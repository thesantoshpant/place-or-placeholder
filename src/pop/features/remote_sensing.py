"""Standard remote-sensing covariates per unit (L3): GHSL population/built-up, VIIRS night
lights, MODIS NDVI and LST.

Everything is fetched with ``ee.data.computePixels`` on one 0.01 deg EPSG:4326 grid aligned
to the ERA5-Land grid of ``pop.features.climate`` (edges at -180.05 + k*0.01), then reduced
locally with exactextract coverage fractions:
  * GHSL (100 m Mollweide): density is averaged into 0.01 deg cells with ``reduceResolution``
    (exact sums; negative nodata masked to 0) and multiplied by the cell area.
  * VIIRS (15", ~460 m) and MODIS (250 m / 1 km): read from EE pyramids at 0.01 deg.
Unit values are coverage x weight averages over valid (non-NaN) cells only, so cloud gaps
re-normalise the weights; a unit whose cells are all invalid gets NaN.

Month alignment (leakage-safe): a MODIS composite belongs to the month that contains its
*last* day (MOD13Q1: start + 15 d; MOD11A2: start + 7 d capped at 31 Dec, as the last
composite of a year is short). Month m therefore only contains information up to the end
of month m.
"""
from __future__ import annotations

import concurrent.futures as cf

import ee
import numpy as np
import pandas as pd
import scipy.sparse as sp

from pop.features import climate as C
from pop.features.ee_utils import profile_eecu

GHS_POP = "JRC/GHSL/P2023A/GHS_POP"
GHS_BUILT = "JRC/GHSL/P2023A/GHS_BUILT_S"
VIIRS = {"NOAA/VIIRS/DNB/ANNUAL_V21": range(2013, 2022), "NOAA/VIIRS/DNB/ANNUAL_V22": range(2022, 2026)}
NTL_BAND = "average_masked"
MOD13 = "MODIS/061/MOD13Q1"
MOD11 = "MODIS/061/MOD11A2"
COMPOSITE_DAYS = {MOD13: 16, MOD11: 8}
MONTHLY_VARS = ["ndvi", "lst_day", "lst_night"]
FINE = C.FINE  # fine cells per ERA5 cell -> 0.01 deg
FRES = C.RES / FINE
R_EARTH = 6371008.8


# ---------------------------------------------------------------- month alignment (pure)
def composite_month(start, product: str) -> pd.Series:
    """(year, month) period each composite is assigned to: the month of its last day."""
    s = pd.to_datetime(pd.Series(start))
    end = s + pd.Timedelta(days=COMPOSITE_DAYS[product] - 1)
    if product == MOD11:  # the last 8-day period of a year stops on 31 Dec
        end = end.where(end.dt.year == s.dt.year, pd.to_datetime(s.dt.year.astype(str) + "-12-31"))
    return end.dt.to_period("M")


def composites_by_month(product: str, year: int) -> dict[int, list[str]]:
    """{month: [system:index, ...]} of composites whose last day falls in ``year``-month."""
    ic = ee.ImageCollection(product).filterDate(f"{year - 1}-12-01", f"{year + 1}-01-01")
    d = ee.Dictionary({"i": ic.aggregate_array("system:index"), "t": ic.aggregate_array("system:time_start")}).getInfo()
    per = composite_month(pd.to_datetime(d["t"], unit="ms"), product)
    out = {m: [] for m in range(1, 13)}
    for i, p in zip(d["i"], per):
        if p.year == year:
            out[p.month].append(i)
    return out


# ---------------------------------------------------------------- EE images
def _ndvi(img):
    q = img.select("SummaryQA")
    return img.select("NDVI").multiply(1e-4).updateMask(q.lte(1))  # 0 good, 1 marginal


def _lst(img, which):
    qc = img.select(f"QC_{which}")
    ok = qc.bitwiseAnd(3).lte(1).And(qc.rightShift(6).bitwiseAnd(3).lte(1))  # produced, LST error <= 2 K
    return img.select(f"LST_{which}_1km").multiply(0.02).subtract(273.15).updateMask(ok)


def monthly_image(year: int, months=range(1, 13), mask_qa: str = "ndvi") -> ee.Image:
    """Bands ``<var>_<mm>`` for ndvi (unitless), lst_day, lst_night (deg C).
    mask_qa: "all" (NDVI SummaryQA + LST QC), "ndvi" (NDVI only; LST is already only produced
    for clear-sky pixels) or "none"."""
    m13, m11 = composites_by_month(MOD13, year), composites_by_month(MOD11, year)
    bands = []
    for m in months:
        a = ee.ImageCollection(MOD13).filter(ee.Filter.inList("system:index", m13[m]))
        b = ee.ImageCollection(MOD11).filter(ee.Filter.inList("system:index", m11[m]))
        nd = a.map(_ndvi) if mask_qa in ("all", "ndvi") else a.map(lambda i: i.select("NDVI").multiply(1e-4))
        if mask_qa == "all":
            ld, ln = b.map(lambda i: _lst(i, "Day")), b.map(lambda i: _lst(i, "Night"))
        else:
            ld = b.map(lambda i: i.select("LST_Day_1km").multiply(0.02).subtract(273.15))
            ln = b.map(lambda i: i.select("LST_Night_1km").multiply(0.02).subtract(273.15))
        bands += [nd.mean().rename(f"ndvi_{m:02d}"), ld.mean().rename(f"lst_day_{m:02d}"), ln.mean().rename(f"lst_night_{m:02d}")]
    return ee.Image.cat(bands)


def viirs_id(year: int) -> str | None:
    for cid, yrs in VIIRS.items():
        if year in yrs:
            return cid
    return None


def ntl_image(years) -> ee.Image:
    """Annual VIIRS VNL ``average_masked`` radiance (nW/cm2/sr); background-masked pixels = 0."""
    out = []
    for y in years:
        img = ee.ImageCollection(viirs_id(y)).filterDate(f"{y}-01-01", f"{y + 1}-01-01").first()
        out.append(ee.Image(img).select(NTL_BAND).unmask(0).rename(f"ntl_{y}"))
    return ee.Image.cat(out)


def _per_cell(img, band: str, name: str) -> ee.Image:
    """Exact 100 m -> 0.01 deg aggregate of a per-pixel GHSL quantity (nodata < 0 -> 0)."""
    x = img.select(band)
    dens = x.updateMask(x.gte(0)).divide(1e4).unmask(0)  # per m2 (100 m pixels)
    fine = {"crs": "EPSG:4326", "crsTransform": [FRES, 0, C.X0, 0, -FRES, C.Y0]}
    dens = dens.setDefaultProjection(x.projection()).reduceResolution(ee.Reducer.mean(), maxPixels=2048).reproject(**fine)
    return dens.multiply(ee.Image.pixelArea()).rename(name)


def ghsl_image(pop_epochs, built_epochs=()) -> tuple[ee.Image, list[str]]:
    """People and built-up m2 per 0.01 deg cell: bands pop_<e>, built_<e> (and their names)."""
    b, names = [], []
    for e in pop_epochs:
        b.append(_per_cell(ee.Image(f"{GHS_POP}/{e}"), "population_count", f"pop_{e}"))
        names.append(f"pop_{e}")
    for e in built_epochs:
        b.append(_per_cell(ee.Image(f"{GHS_BUILT}/{e}"), "built_surface", f"built_{e}"))
        names.append(f"built_{e}")
    return ee.Image.cat(b), names


# ---------------------------------------------------------------- EECU accounting
def profiled(fn, tries: int = 6):
    """Like ``ee_utils.profiled`` but with longer back-off; returns (result, EECU-s, n_missing)."""
    import time
    ids: list[str] = []
    with ee.data.profiling(ids.append):
        res = fn()
    get = ee.ApiFunction.lookup("Profile.getProfiles").call
    eecu, miss = 0.0, 0
    for pid in ids:
        for k in range(tries):
            try:
                eecu += profile_eecu(get(ids=[pid]).getInfo())
                break
            except ee.EEException:
                if k == tries - 1:
                    miss += 1
                time.sleep(2 * 2 ** k)
    return res, eecu, miss


# ---------------------------------------------------------------- cells / downloads
class Cells:
    """Fine (0.01 deg) cells touched by the unit polygons on bbox grid ``g`` (0.1 deg units)."""

    def __init__(self, cov: pd.DataFrame, g: dict):
        self.g, self.NX = g, g["nx"] * FINE
        flat = cov.r.values.astype(np.int64) * self.NX + cov.c.values
        self.cells, self.col = np.unique(flat, return_inverse=True)  # col: coverage row -> cell index
        self.r, self.c = self.cells // self.NX, self.cells % self.NX
        self.lat = g["y0"] - (self.r + 0.5) * FRES
        self.area = cell_area_m2(self.lat)

    def tiles(self, tile: int):
        """[(sub-grid dict, cell idx, local row, local col)] for tiles of ``tile`` ERA5 cells."""
        T = tile * FINE
        key = (self.r // T) * (self.NX // T + 1) + self.c // T
        order = np.argsort(key, kind="stable")
        ks, starts = np.unique(key[order], return_index=True)
        out = []
        for k, idx in zip(ks, np.split(order, starts[1:])):
            tr, tc = int(self.r[idx[0]] // T), int(self.c[idx[0]] // T)
            sub = {"x0": float(self.g["x0"] + tc * tile * C.RES), "y0": float(self.g["y0"] - tr * tile * C.RES),
                   "nx": int(min(tile, self.g["nx"] - tc * tile)), "ny": int(min(tile, self.g["ny"] - tr * tile))}
            out.append((sub, idx, self.r[idx] - tr * T, self.c[idx] - tc * T))
        return out


def cell_area_m2(lat):
    """Spherical area (m2) of 0.01 deg cells centred at ``lat``."""
    h = np.deg2rad(FRES / 2)
    return R_EARTH ** 2 * np.deg2rad(FRES) * (np.sin(np.deg2rad(lat) + h) - np.sin(np.deg2rad(lat) - h))


def fetch_cells(img: ee.Image, cells: Cells, tile: int, workers: int = 6, log=print):
    """Download ``img`` at the needed cells -> ((bands, n_cells) float32 with NaN nodata, EECU-s, info).
    EECU of requests whose profile never became available is imputed with the mean of the others."""
    jobs = cells.tiles(tile)
    out = None

    def one(job):
        sub = job[0]
        for k in range(5):
            try:
                return profiled(lambda: C.compute_pixels(img, sub, fine=FINE))
            except Exception as e:  # transient 429 / 5xx
                if k == 4:
                    raise
                log(f"  retry tile {sub['x0']:.2f},{sub['y0']:.2f}: {str(e)[:120]}")
    eecu, miss = 0.0, 0
    with cf.ThreadPoolExecutor(workers) as ex:
        for (sub, idx, lr, lc), (a, e, m) in zip(jobs, ex.map(one, jobs)):
            if out is None:
                out = np.full((a.shape[0], len(cells.cells)), np.nan, "float32")
            out[:, idx] = a[:, lr, lc]
            eecu += e
            miss += m
    n = len(jobs)
    est = eecu * n / (n - miss) if miss < n else float("nan")
    return out, est, {"eecu_measured_s": eecu, "profiles_missing": miss, "requests": n}


# ---------------------------------------------------------------- zonal reduction
def weight_matrix(cov: pd.DataFrame, cells: Cells, n_units: int, cell_w: np.ndarray | None) -> sp.csr_matrix:
    """(units x cells) coverage x (cell_w, or cell area if None)."""
    w = cov.f.values * (cells.area[cells.col] if cell_w is None else cell_w[cells.col])
    W = sp.csr_matrix((w, (cov.uix.values, cells.col)), shape=(n_units, len(cells.cells)))
    W.sum_duplicates()
    return W


def zonal_sum(W: sp.csr_matrix, X: np.ndarray) -> np.ndarray:
    """X (bands, cells) -> (bands, units) weighted sums (NaN treated as 0)."""
    return np.asarray(W @ np.nan_to_num(X, nan=0.0).T).T


def zonal_mean(W: sp.csr_matrix, X: np.ndarray) -> np.ndarray:
    """Weighted mean over valid cells; NaN where a unit has no valid weight."""
    num = W @ np.nan_to_num(X, nan=0.0).T
    den = W @ (~np.isnan(X)).T.astype("float64")
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.asarray(np.where(den > 0, num / den, np.nan)).T


def fill_prev_year(df: pd.DataFrame, cols) -> tuple[pd.DataFrame, dict]:
    """Fill NaN unit-months from the same month of the previous year (leakage-safe)."""
    df = df.sort_values(["unit_id", "month", "year"]).copy()
    n = {}
    for c in cols:
        prev = df.groupby(["unit_id", "month"])[c].shift(1)
        prev_year = df.groupby(["unit_id", "month"])["year"].shift(1)
        m = df[c].isna() & prev.notna() & (prev_year == df.year - 1)
        df.loc[m, c] = prev[m]
        n[c] = int(m.sum())
    return df.sort_values(["unit_id", "year", "month"], ignore_index=True), n
