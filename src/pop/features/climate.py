"""Weekly district climate from ERA5-Land (ECMWF/ERA5_LAND/DAILY_AGGR).

Variables per Sunday-start week [week_start, week_start + 7 d), UTC days:
  tmean  mean of daily mean 2 m temperature (deg C)
  tmin   mean of daily minimum 2 m temperature (deg C)
  tmax   mean of daily maximum 2 m temperature (deg C)
  precip weekly total precipitation (mm)
  rh     mean of daily relative humidity (%) from daily mean T and dewpoint (Magnus)

District means are population-weighted (GHSL GHS_POP, epoch nearest the week's year);
``*_area`` columns are area-weighted. Both are exact polygon/grid intersections.

Method "grid" (chosen; see docs/features/climate_era5land.md):
  1. EE composites weekly images and the result is downloaded in ERA5-Land's native
     0.1 deg grid with ``ee.data.computePixels`` (cheap: no zonal work in EE).
  2. GHSL people per cell on an aligned 0.01 deg grid is downloaded once per epoch.
  3. exactextract gives polygon x 0.01-deg-cell coverage fractions once; they are
     folded into sparse unit x ERA5-cell weight matrices (coverage*pop, coverage*area)
     so every week is a sparse mat-vec. Ocean (masked) ERA5 cells get zero weight;
     units with no land cell use the nearest land cell to their centroid.
Method "ee" (pilot comparison): ``reduceRegions`` sum over a stacked year image.
"""
from __future__ import annotations

import concurrent.futures as cf
import io
import math

import ee
import numpy as np
import pandas as pd
import scipy.sparse as sp

from pop.features.ee_utils import profiled

ERA5 = "ECMWF/ERA5_LAND/DAILY_AGGR"
GHSL_POP = "JRC/GHSL/P2023A/GHS_POP"
GHSL_EPOCHS = list(range(1975, 2031, 5))
VARS = ["tmean", "tmin", "tmax", "precip", "rh"]
# native ERA5-Land grid: cell edges at -180.05 + k*0.1 (lon), 90.05 - k*0.1 (lat)
X0, Y0, RES = -180.05, 90.05, 0.1
FINE = 10  # weight grid = RES / FINE = 0.01 deg, aligned to the ERA5 grid
MAGNUS_A, MAGNUS_B = 17.625, 243.04  # Alduchov & Eskridge (1996)


# ---------------------------------------------------------------- pure helpers
def rh_magnus(t_c, td_c):
    """Relative humidity (%) from temperature and dewpoint (deg C), capped at 100."""
    t_c, td_c = np.asarray(t_c, float), np.asarray(td_c, float)
    rh = 100 * np.exp(MAGNUS_A * td_c / (MAGNUS_B + td_c) - MAGNUS_A * t_c / (MAGNUS_B + t_c))
    return np.minimum(rh, 100.0)


def nearest_epoch(year: int) -> int:
    return min(GHSL_EPOCHS, key=lambda e: (abs(e - year), e))


def week_starts(panel_path: str, country: str) -> pd.DatetimeIndex:
    p = pd.read_parquet(panel_path, columns=["country", "week_start"], filters=[("country", "==", country)])
    ws = pd.DatetimeIndex(sorted(pd.to_datetime(p.week_start.unique())))
    assert (ws.dayofweek == 6).all(), "panel weeks must start on Sunday"
    return ws


def snap_bbox(bounds, pad: float = 0.2):
    """Expand (minx, miny, maxx, maxy) to whole ERA5 cells; returns grid origin + shape."""
    minx, miny, maxx, maxy = bounds
    c0 = math.floor((minx - pad - X0) / RES)
    c1 = math.ceil((maxx + pad - X0) / RES)
    r0 = math.floor((Y0 - (maxy + pad)) / RES)
    r1 = math.ceil((Y0 - (miny - pad)) / RES)
    return {"x0": X0 + c0 * RES, "y0": Y0 - r0 * RES, "nx": c1 - c0, "ny": r1 - r0}


# ---------------------------------------------------------------- EE images
def _daily(img: ee.Image) -> ee.Image:
    t = img.select("temperature_2m").subtract(273.15)
    td = img.select("dewpoint_temperature_2m").subtract(273.15)
    rh = (td.multiply(MAGNUS_A).divide(td.add(MAGNUS_B))
          .subtract(t.multiply(MAGNUS_A).divide(t.add(MAGNUS_B))).exp().multiply(100).min(100))
    return ee.Image.cat([
        t.rename("tmean"),
        img.select("temperature_2m_min").subtract(273.15).rename("tmin"),
        img.select("temperature_2m_max").subtract(273.15).rename("tmax"),
        img.select("total_precipitation_sum").multiply(1000).rename("precip"),
        rh.rename("rh"),
    ])


def weekly_image(ws: pd.Timestamp) -> ee.Image:
    """5-band weekly composite for the week starting ``ws`` (Sunday)."""
    a = ws.strftime("%Y-%m-%d")
    b = (ws + pd.Timedelta(days=7)).strftime("%Y-%m-%d")
    d = ee.ImageCollection(ERA5).filterDate(a, b).map(_daily)
    mean = d.select(["tmean", "tmin", "tmax", "rh"]).mean()
    return ee.Image.cat([mean.select(["tmean", "tmin", "tmax"]), d.select("precip").sum(), mean.select("rh")]).select(VARS)


def stack_weeks(weeks) -> ee.Image:
    imgs = [weekly_image(w).rename([f"{v}_{w:%Y%m%d}" for v in VARS]) for w in weeks]
    return ee.Image.cat(imgs)


def ndays(weeks) -> list[int]:
    a, b = weeks[0].strftime("%Y-%m-%d"), (weeks[-1] + pd.Timedelta(days=7)).strftime("%Y-%m-%d")
    t = ee.ImageCollection(ERA5).filterDate(a, b).aggregate_array("system:time_start").getInfo()
    d = pd.to_datetime(t, unit="ms")
    return [int(((d >= w) & (d < w + pd.Timedelta(days=7))).sum()) for w in weeks]


def pop_per_cell(epoch: int) -> ee.Image:
    """GHSL people per 0.01-deg cell (density averaged then x cell area)."""
    pop = ee.Image(f"{GHSL_POP}/{epoch}").select("population_count")
    dens = pop.updateMask(pop.gte(0)).divide(1e4).unmask(0)  # people / m^2 (100 m Mollweide pixels)
    fine = {"crs": "EPSG:4326", "crsTransform": [RES / FINE, 0, X0, 0, -RES / FINE, Y0]}
    dens = dens.setDefaultProjection(pop.projection()).reduceResolution(ee.Reducer.mean(), maxPixels=2048).reproject(**fine)
    return dens.multiply(ee.Image.pixelArea()).rename("pop")


# ---------------------------------------------------------------- downloads
def compute_pixels(img: ee.Image, g: dict, fine: int = 1, nodata: float = -9999.0) -> np.ndarray:
    """Download ``img`` on the (sub)grid ``g`` -> float32 array (bands, ny, nx); nodata -> NaN."""
    res = RES / fine
    req = {"expression": img.unmask(nodata, False).toFloat(), "fileFormat": "NPY",
           "grid": {"dimensions": {"width": g["nx"] * fine, "height": g["ny"] * fine},
                    "affineTransform": {"scaleX": res, "shearX": 0, "translateX": g["x0"],
                                        "shearY": 0, "scaleY": -res, "translateY": g["y0"]},
                    "crsCode": "EPSG:4326"}}
    raw = ee.data.computePixels(req)
    arr = np.load(io.BytesIO(raw)) if isinstance(raw, (bytes, bytearray)) else raw
    out = np.stack([arr[n].astype("float32") for n in arr.dtype.names])
    out[out == nodata] = np.nan
    return out


def download_weeks(weeks, g: dict, chunk: int = 8, workers: int = 4, log=print) -> np.ndarray:
    """((n_weeks, 5, ny, nx) weekly grids, EECU-s), fetched in chunks of ``chunk`` weeks."""
    weeks = list(weeks)
    parts = [weeks[i:i + chunk] for i in range(0, len(weeks), chunk)]

    def one(ws):
        for k in range(4):
            try:
                return profiled(lambda: compute_pixels(stack_weeks(ws), g))
            except Exception as e:  # transient 429/5xx
                if k == 3:
                    raise
                log(f"  retry {ws[0]:%Y-%m-%d}: {e}")
    out, eecu = [], 0.0
    with cf.ThreadPoolExecutor(workers) as ex:
        for i, (a, e) in enumerate(ex.map(one, parts)):
            out.append(a.reshape(len(parts[i]), len(VARS), g["ny"], g["nx"]))
            eecu += e
    return np.concatenate(out), eecu


def download_pop(epoch: int, g: dict, need: np.ndarray | None = None, tile: int = 25, workers: int = 6):
    """((ny*FINE, nx*FINE) people per 0.01-deg cell, EECU-s), in tiles of ``tile`` x ``tile`` ERA5 cells
    (reduceResolution from 100 m caps the per-request input size). Tiles with no ``need``
    ERA5 cell (bool (ny, nx), e.g. cells touched by any polygon) are skipped (cost ~ input pixels)."""
    img = pop_per_cell(epoch)
    out = np.zeros((g["ny"] * FINE, g["nx"] * FINE), "float32")
    jobs = [(r, c) for r in range(0, g["ny"], tile) for c in range(0, g["nx"], tile)
            if need is None or need[r:r + tile, c:c + tile].any()]

    def one(rc):
        r, c = rc
        sub = {"x0": g["x0"] + c * RES, "y0": g["y0"] - r * RES,
               "nx": min(tile, g["nx"] - c), "ny": min(tile, g["ny"] - r)}
        for k in range(4):
            try:
                a, e = profiled(lambda: compute_pixels(img, sub, fine=FINE)[0])
                return rc, sub, a, e
            except Exception:
                if k == 3:
                    raise
    with cf.ThreadPoolExecutor(workers) as ex:
        eecu = 0.0
        for (r, c), sub, a, e in ex.map(one, jobs):
            out[r * FINE:(r + sub["ny"]) * FINE, c * FINE:(c + sub["nx"]) * FINE] = a
            eecu += e
    # GHS_POP has unmasked negative nodata (e.g. -200): masked in EE (pop_per_cell); clamp again locally
    return np.clip(np.nan_to_num(out, nan=0.0), 0, None), eecu


# ---------------------------------------------------------------- local zonal weights
def coverage_table(gdf, g: dict) -> pd.DataFrame:
    """Polygon x fine-cell coverage fractions (unit index, fine row, fine col, frac)."""
    from exactextract import exact_extract
    from exactextract.raster import NumPyRasterSource
    ny, nx = g["ny"] * FINE, g["nx"] * FINE
    src = NumPyRasterSource(np.zeros((ny, nx), "float32"), xmin=g["x0"], ymin=g["y0"] - g["ny"] * RES,
                            xmax=g["x0"] + g["nx"] * RES, ymax=g["y0"], name="z")
    vec = gdf[["geometry"]].reset_index(drop=True).assign(uix=np.arange(len(gdf)))
    df = exact_extract(src, vec, ["cell_id", "coverage"], include_cols=["uix"], output="pandas")
    rows = []
    for uix, cid, cov in zip(df.uix, df.z_cell_id if "z_cell_id" in df else df.cell_id,
                             df.z_coverage if "z_coverage" in df else df.coverage):
        cid = np.asarray(cid, dtype=np.int64)
        rows.append(pd.DataFrame({"uix": uix, "r": cid // nx, "c": cid % nx, "f": np.asarray(cov, float)}))
    return pd.concat(rows, ignore_index=True)


def weight_matrix(cov: pd.DataFrame, g: dict, n_units: int, pop: np.ndarray | None, land: np.ndarray) -> sp.csr_matrix:
    """Sparse (units x ERA5 cells) weights: coverage * (pop or cell area), zero on ocean cells."""
    if pop is None:
        lat = g["y0"] - (cov.r.values + 0.5) * RES / FINE
        w = cov.f.values * np.cos(np.deg2rad(lat))
    else:
        w = cov.f.values * pop[cov.r.values, cov.c.values]
    cell = (cov.r.values // FINE) * g["nx"] + cov.c.values // FINE
    w = np.where(land.ravel()[cell], w, 0.0)
    W = sp.csr_matrix((w, (cov.uix.values, cell)), shape=(n_units, g["ny"] * g["nx"]))
    W.sum_duplicates()
    W.eliminate_zeros()
    return W


def nearest_land_cell(lon, lat, g: dict, land: np.ndarray) -> np.ndarray:
    rr, cc = np.nonzero(land)
    clat, clon = g["y0"] - (rr + 0.5) * RES, g["x0"] + (cc + 0.5) * RES
    out = []
    for x, y in zip(lon, lat):
        k = np.argmin((clon - x) ** 2 * np.cos(np.deg2rad(y)) ** 2 + (clat - y) ** 2)
        out.append(rr[k] * g["nx"] + cc[k])
    return np.array(out)


def finalize_weights(W: sp.csr_matrix, fallback: sp.csr_matrix, nearest: np.ndarray) -> tuple[sp.csr_matrix, np.ndarray]:
    """Row-normalise; rows with zero total use ``fallback`` row, else nearest land cell."""
    tot = np.asarray(W.sum(1)).ravel()
    W = W.tolil()
    ftot = np.asarray(fallback.sum(1)).ravel()
    src = np.where(tot > 0, "own", np.where(ftot > 0, "fallback", "nearest"))
    for i in np.nonzero(tot <= 0)[0]:
        if ftot[i] > 0:
            W[i] = fallback[i]
        else:
            W[i, nearest[i]] = 1.0
    W = W.tocsr()
    W = sp.diags(1.0 / np.asarray(W.sum(1)).ravel()) @ W
    return W, src


def apply_weights(W: sp.csr_matrix, grids: np.ndarray) -> np.ndarray:
    """grids (n_weeks, n_vars, ny, nx) -> (n_weeks, n_vars, n_units). NaN cells must have zero weight."""
    nw, nv = grids.shape[:2]
    X = np.nan_to_num(grids.reshape(nw * nv, -1), nan=0.0).T  # cells x (weeks*vars)
    return np.asarray(W @ X).T.reshape(nw, nv, W.shape[0])


# ---------------------------------------------------------------- EE reduceRegions method (pilot)
def ee_year_stack(weeks, epoch: int) -> ee.Image:
    vals = stack_weeks(weeks)
    valid = vals.select(0).mask().gt(0)
    w = pop_per_cell(epoch).unmask(0).updateMask(valid)
    names = vals.bandNames()
    return ee.Image.cat([vals.multiply(w).rename(names.map(lambda n: ee.String("w_").cat(n))),
                         vals, w.rename("pop_sum"), valid.selfMask().rename("n_cells")])


def ee_reduce(fc: ee.FeatureCollection, weeks, epoch: int, tile_scale: int = 4) -> ee.FeatureCollection:
    img = ee_year_stack(weeks, epoch)
    return img.reduceRegions(collection=fc.select(["unit_id"]), reducer=ee.Reducer.sum(),
                             crs="EPSG:4326", crsTransform=[RES / FINE, 0, X0, 0, -RES / FINE, Y0], tileScale=tile_scale)


def ee_sums_to_long(df: pd.DataFrame, weeks) -> pd.DataFrame:
    out = []
    for w in weeks:
        s = f"{w:%Y%m%d}"
        d = pd.DataFrame({"unit_id": df.unit_id.astype(str), "week_start": w})
        for v in VARS:
            d[v] = df[f"w_{v}_{s}"] / df["pop_sum"]
            d[f"{v}_area"] = df[f"{v}_{s}"] / df["n_cells"]
        out.append(d)
    return pd.concat(out, ignore_index=True)
