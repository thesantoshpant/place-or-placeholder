"""L3 standard remote-sensing covariates + yearly unit population (GHSL / VIIRS / MODIS).

    python scripts/features/build_remote_sensing.py pilot BRAZIL --adm1 "SAO PAULO" --year 2023
    python scripts/features/build_remote_sensing.py run BRAZIL        # COLOMBIA / PERU / TAIWAN
    python scripts/features/build_remote_sensing.py merge-pop         # all countries -> one file
    python scripts/features/build_remote_sensing.py pilot-lst COLOMBIA --adm1 SANTANDER --year 2013
    python scripts/features/build_remote_sensing.py run-lst-v2 COLOMBIA   # v2 = v1 with QC-masked LST
    python scripts/features/build_remote_sensing.py compare-lst           # v1 vs v2 LST, all countries

Outputs: data/interim/remote_sensing/rs_{monthly,yearly}_<country>_v1.parquet (+ .qa.json),
data/interim/population/unit_population_yearly_v1.parquet, costs in data/interim/remote_sensing/costs.jsonl.
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import ee
import geopandas as gpd
import numpy as np
import pandas as pd

from pop.features import climate as C
from pop.features import ee_utils as U
from pop.features import population as P
from pop.features import remote_sensing as R

OUT = Path("data/interim/remote_sensing")
POP_OUT = Path("data/interim/population")
UNITS = "data/interim/boundaries/opendengue_units_v1.parquet"
# panel range, clipped to MODIS availability (from 2000)
YEARS = {"BRAZIL": (2013, 2024), "COLOMBIA": (2007, 2022), "PERU": (2000, 2023), "TAIWAN": (2000, 2024)}
POP_YEARS = {"BRAZIL": (2013, 2024), "COLOMBIA": (2006, 2022), "PERU": (2000, 2023), "TAIWAN": (1997, 2024)}
MCOLS = ["ndvi_pw", "ndvi_aw", "lst_day_pw", "lst_day_aw", "lst_night_pw", "lst_night_aw"]


LCOLS = ["lst_day_pw", "lst_day_aw", "lst_night_pw", "lst_night_aw"]
KEYS = ["unit_id", "year", "month"]
BUDGET_V2_H = 9.5  # cap on EECU-h logged by the v2 LST stages (stage names ending in "_v2")


BUDGET_H = 26.0  # hard stop on all logged EECU-h (5.9 h used by BR + pilots, +20 h cap for CO/PE/TW)


def total_eecu_h() -> float:
    f = OUT / "costs.jsonl"
    if not f.exists():
        return 0.0
    recs = [json.loads(x) for x in f.read_text().splitlines() if x.strip()]
    return sum(r.get("eecu_s") or 0 for r in recs if r.get("stage") != "run_total") / 3600


def v2_eecu_h() -> float:
    f = OUT / "costs.jsonl"
    recs = [json.loads(x) for x in f.read_text().splitlines() if x.strip()] if f.exists() else []
    return sum(r.get("eecu_s") or 0 for r in recs if str(r.get("stage", "")).endswith("_v2")) / 3600


def log_cost(rec: dict) -> None:
    rec = {**rec, "time": pd.Timestamp.now().isoformat()}
    print(json.dumps(rec), flush=True)
    with (OUT / "costs.jsonl").open("a") as f:
        f.write(json.dumps(rec) + "\n")


class Builder:
    def __init__(self, country: str, adm1: str | None = None):
        g = gpd.read_parquet(UNITS)
        g = g[g.country == country]
        self.no_geom = g[g.geometry.isna()].unit_id.tolist()
        g = g[g.geometry.notna()]
        if adm1:
            g = g[g.adm1 == adm1]
        self.country, self.u = country, g.reset_index(drop=True)
        self.ids = self.u.unit_id.astype(str).values
        self.g = C.snap_bbox(self.u.total_bounds)
        t = time.time()
        self.cov = C.coverage_table(self.u, self.g)
        self.cells = R.Cells(self.cov, self.g)
        self.Wa = R.weight_matrix(self.cov, self.cells, len(self.u), None)
        self.unit_area = np.asarray(self.Wa.sum(1)).ravel()
        self.eecu, self.ghsl = 0.0, {}
        print(f"{country} {adm1 or ''}: {len(self.u)} units, {len(self.cells.cells):,} cells, "
              f"coverage {time.time() - t:.0f}s, no geometry: {self.no_geom}", flush=True)

    def _fetch(self, stage, img, tile, **kw):
        t = time.time()
        X, e, info = R.fetch_cells(img, self.cells, tile=tile)
        self.eecu += e
        log_cost({"stage": stage, "country": self.country, "n_cells": len(self.cells.cells), "bands": X.shape[0],
                  "eecu_s": e, **info, "wall_s": time.time() - t, **kw})
        if stage.endswith("_v2"):
            if v2_eecu_h() > BUDGET_V2_H:
                raise SystemExit(f"EECU budget guard (v2): {v2_eecu_h():.2f} h logged > {BUDGET_V2_H} h")
        elif total_eecu_h() > BUDGET_H:
            raise SystemExit(f"EECU budget guard: {total_eecu_h():.2f} h logged > {BUDGET_H} h")
        return X

    # ---- GHSL
    def fetch_ghsl(self, epochs, built_epochs=None, tile=10, stage="ghsl"):
        built_epochs = list(epochs if built_epochs is None else built_epochs)
        img, names = R.ghsl_image(epochs, built_epochs)
        X = self._fetch(stage, img, tile, epochs=list(epochs), built_epochs=built_epochs)
        X = np.clip(np.nan_to_num(X, nan=0.0), 0, None)
        for n, x in zip(names, X):
            k, e = n.split("_")
            self.ghsl.setdefault(int(e), {})[k] = x

    def Wp(self, year):
        """Population weights (nearest GHSL epoch) plus a negligible area term so units with
        no people fall back to area weighting."""
        e = C.nearest_epoch(year)
        return R.weight_matrix(self.cov, self.cells, len(self.u), self.ghsl[e]["pop"]) + 1e-9 * self.Wa

    def epoch_sums(self, epochs):
        """(units x epochs) people and built-up share of unit area."""
        Wc = R.weight_matrix(self.cov, self.cells, len(self.u), np.ones(len(self.cells.cells)))  # coverage only
        pop = R.zonal_sum(Wc, np.stack([self.ghsl[e]["pop"] for e in epochs])).T
        be = [e for e in epochs if "built" in self.ghsl[e]]
        built = R.zonal_sum(Wc, np.stack([self.ghsl[e]["built"] for e in be])).T / self.unit_area[:, None]
        return pop, built, be

    # ---- VIIRS
    def ntl(self, years):
        ys = [y for y in years if R.viirs_id(y)]
        X = self._fetch("ntl", R.ntl_image(ys), tile=40, years=[ys[0], ys[-1]]) if ys else None
        rows = []
        for y in years:
            d = pd.DataFrame({"unit_id": self.ids, "year": y, "ntl_pw": np.nan, "ntl_aw": np.nan})
            if y in ys:
                x = X[[ys.index(y)]]
                d["ntl_pw"], d["ntl_aw"] = R.zonal_mean(self.Wp(y), x)[0], R.zonal_mean(self.Wa, x)[0]
            rows.append(d)
        return pd.concat(rows, ignore_index=True)

    # ---- MODIS
    def modis(self, year, img=None, stage="modis", tile=20, vars_=R.MONTHLY_VARS):
        X = self._fetch(stage, img if img is not None else R.monthly_image(year), tile, year=year)
        return R.monthly_frame(self.ids, year, R.zonal_mean(self.Wp(year), X), R.zonal_mean(self.Wa, X), vars_)

    def pop_weights_v2(self, years, cache: Path):
        """GHSL population per cell for the nearest epochs of ``years`` (pop only, no built-up);
        cached in ``cache`` so a rerun does not pay EECU again."""
        eps = sorted({C.nearest_epoch(y) for y in years})
        if cache.exists():
            z = np.load(cache)
            if np.array_equal(z["cells"], self.cells.cells) and all(f"pop_{e}" in z for e in eps):
                for e in eps:
                    self.ghsl.setdefault(e, {})["pop"] = z[f"pop_{e}"]
                print(f"GHSL pop cells from cache {cache}", flush=True)
                return eps
        self.fetch_ghsl(eps, [], stage="ghsl_pop_v2")
        np.savez_compressed(cache, cells=self.cells.cells, **{f"pop_{e}": self.ghsl[e]["pop"] for e in eps})
        return eps


def _native_ndvi(year):
    """Pilot comparison: QA-masked NDVI at native 250 m, reduceResolution-averaged to 0.01 deg."""
    m13 = R.composites_by_month(R.MOD13, year)
    proj = ee.Image(ee.ImageCollection(R.MOD13).first()).select("NDVI").projection()
    fine = {"crs": "EPSG:4326", "crsTransform": [R.FRES, 0, C.X0, 0, -R.FRES, C.Y0]}
    b = []
    for m in range(1, 13):
        x = ee.ImageCollection(R.MOD13).filter(ee.Filter.inList("system:index", m13[m])).map(R._ndvi).mean()
        x = x.setDefaultProjection(proj).reduceResolution(ee.Reducer.mean(), maxPixels=1024).reproject(**fine)
        b += [x.rename(f"ndvi_{m:02d}"), ee.Image.constant(0).rename(f"d1_{m:02d}"), ee.Image.constant(0).rename(f"d2_{m:02d}")]
    return ee.Image.cat(b)


def pilot(country, adm1, year, ghsl=True, native=True):
    b = Builder(country, adm1)
    eps = P.epochs_for_years(*POP_YEARS[country])
    if not ghsl:  # cheap re-pilot: population weights from one epoch only
        eps = [C.nearest_epoch(year)]
    b.fetch_ghsl(eps)
    pop, built, _ = b.epoch_sums(eps)
    pe = pd.DataFrame(pop, columns=eps, index=b.ids)
    ntl = b.ntl([year])
    m = b.modis(year, img=R.monthly_image(year, mask_qa="all"), stage="modis_qa_pyramid")
    m0 = b.modis(year, img=R.monthly_image(year, mask_qa="none"), stage="modis_noqa_pyramid")
    m1 = b.modis(year, img=R.monthly_image(year, mask_qa="ndvi"), stage="modis_ndviqa_pyramid")
    mn = b.modis(year, img=_native_ndvi(year), stage="ndvi_qa_native250", tile=20) if native else None
    cmp = {}
    for v in ("lst_day", "lst_night"):
        x, y = m[f"{v}_aw"].values, m1[f"{v}_aw"].values
        ok = ~np.isnan(x) & ~np.isnan(y)
        cmp[f"{v}_aw_qc_vs_noqc"] = {"r": float(np.corrcoef(x[ok], y[ok])[0, 1]), "mad": float(np.median(np.abs(x[ok] - y[ok]))),
                                     "bias": float(np.mean(y[ok] - x[ok])), "nan_qc": float(np.isnan(x).mean()), "nan_noqc": float(np.isnan(y).mean())}
    for name, o in (("noqa", m0), ("native250", mn)):
        if o is None:
            continue
        x, y = m.ndvi_aw.values, o.ndvi_aw.values
        ok = ~np.isnan(x) & ~np.isnan(y)
        cmp[f"ndvi_aw_vs_{name}"] = {"r": float(np.corrcoef(x[ok], y[ok])[0, 1]), "mad": float(np.median(np.abs(x[ok] - y[ok]))),
                                     "bias": float(np.mean(y[ok] - x[ok]))}
    res = {"units": len(b.u), "cells": len(b.cells.cells), "eecu_s": b.eecu, "cmp": cmp,
           "pop_epochs_top": pe.sort_values(eps[-1]).tail(3).round(0).to_dict(),
           "nan_rate": m[MCOLS].isna().mean().round(4).to_dict(),
           "ranges": m[MCOLS].describe().loc[["min", "50%", "max"]].round(3).to_dict(),
           "ntl": ntl[["ntl_pw", "ntl_aw"]].describe().loc[["min", "50%", "max"]].round(2).to_dict(),
           "built_share_last": pd.Series(built[:, -1]).describe().round(4).to_dict()}
    (OUT / f"pilot_{U.ISO3[country]}_{year}.json").write_text(json.dumps(res, indent=1, default=str))
    print(json.dumps(res, indent=1, default=str))


def qa(df, cols, keys) -> dict:
    return {"rows": len(df), "duplicates": int(df.duplicated(keys).sum()),
            "nan_rate": df[cols].isna().mean().round(5).to_dict(),
            "range_min_p001_p50_p999_max": {c: [round(float(v), 4) for v in df[c].quantile([0, .001, .5, .999, 1])] for c in cols}}


def run(country, years=None):
    t = time.time()
    y0, y1 = years or YEARS[country]
    yrs = list(range(y0, y1 + 1))
    b = Builder(country)
    eps = P.epochs_for_years(*POP_YEARS[country])
    beps = P.epochs_for_years(y0, y1)
    b.fetch_ghsl(eps, beps)
    pop, built, beps = b.epoch_sums(eps)
    pyrs = list(range(POP_YEARS[country][0], POP_YEARS[country][1] + 1))
    pl = P.interp_years(pop, eps, pyrs, "loglinear")
    pli = P.interp_years(pop, eps, pyrs, "linear")
    popdf = P.to_long(b.ids, pyrs, pl, "pop")
    POP_OUT.mkdir(parents=True, exist_ok=True)
    popdf.to_parquet(POP_OUT / f"unit_population_yearly_{country.lower()}_v1.parquet", index=False)
    pd.DataFrame(pop, columns=[f"pop_{e}" for e in eps]).assign(unit_id=b.ids).to_parquet(
        POP_OUT / f"unit_population_epochs_{country.lower()}_v1.parquet", index=False)
    yearly = P.to_long(b.ids, yrs, P.interp_years(built, beps, yrs, "linear"), "built_share")
    yearly = b.ntl(yrs).merge(yearly, on=["unit_id", "year"])[["unit_id", "year", "ntl_pw", "ntl_aw", "built_share"]]
    yearly.to_parquet(OUT / f"rs_yearly_{country.lower()}_v1.parquet", index=False)
    parts = []
    for y in yrs:
        parts.append(b.modis(y))
    mon = pd.concat(parts, ignore_index=True)
    raw_nan = mon[MCOLS].isna().mean().round(5).to_dict()
    mon, nfill = R.fill_prev_year(mon, MCOLS)
    for c in MCOLS:
        mon[c] = mon[c].astype("float32")
    mon.to_parquet(OUT / f"rs_monthly_{country.lower()}_v1.parquet", index=False)
    rep = {"country": country, "years": [y0, y1], "units": len(b.ids), "no_geometry_skipped": b.no_geom,
           "eecu_s": b.eecu, "wall_s": time.time() - t, "ghsl_epochs": eps,
           "pop_total_by_epoch": {e: float(pop[:, i].sum()) for i, e in enumerate(eps)},
           "pop_loglin_vs_lin_max_rel_diff": float(np.nanmax(np.abs(pl - pli) / np.maximum(pli, 1))),
           "zero_pop_units": int((pop[:, -1] <= 0).sum()),
           "monthly": {**qa(mon, MCOLS, ["unit_id", "year", "month"]), "nan_rate_before_fill": raw_nan, "filled_from_prev_year": nfill},
           "yearly": qa(yearly, ["ntl_pw", "ntl_aw", "built_share"], ["unit_id", "year"]),
           "population": qa(popdf, ["pop"], ["unit_id", "year"])}
    (OUT / f"rs_{country.lower()}_v1.qa.json").write_text(json.dumps(rep, indent=1, default=str))
    log_cost({"stage": "run_total", "country": country, "eecu_s": b.eecu, "wall_s": rep["wall_s"]})
    print(json.dumps(rep, indent=1, default=str))


# ---------------------------------------------------------------- v2: QC-masked LST
def _same_bits(a: pd.Series, b: pd.Series) -> bool:
    """Numeric: identical bytes (NaN payloads included); other dtypes: equal values and dtype."""
    if a.dtype != b.dtype or len(a) != len(b):
        return False
    if pd.api.types.is_numeric_dtype(a):
        return a.to_numpy().tobytes() == b.to_numpy().tobytes()
    return bool(a.reset_index(drop=True).equals(b.reset_index(drop=True)))


def pilot_lst(country, adm1, year):
    """Slice check: unmasked LST via ``lst_image(qc=False)`` must reproduce v1; compare the QC rule
    with LST error <= 2 K (flag 1) and <= 1 K (flag 0, the v2 default)."""
    b = Builder(country, adm1)
    b.fetch_ghsl([C.nearest_epoch(year)], [], stage="ghsl_pop_pilot_v2")
    m0 = b.modis(year, img=R.lst_image(year, qc=False), stage="lst_noqc_pilot_v2", vars_=R.LST_VARS)
    v1 = pd.read_parquet(OUT / f"rs_monthly_{country.lower()}_v1.parquet")
    med = v1.groupby(["unit_id", "month"])[LCOLS].median()  # v1 unit x calendar-month medians (all years)
    v1 = v1[(v1.year == year) & v1.unit_id.isin(b.ids)].set_index(KEYS)
    m0 = m0.set_index(KEYS).loc[v1.index]
    md = med.reindex(pd.MultiIndex.from_arrays([v1.index.get_level_values(0), v1.index.get_level_values(2)])).to_numpy()
    res = {"country": country, "adm1": adm1, "year": year, "units": len(b.ids)}
    for flag in (1, 0):
        m1 = b.modis(year, img=R.lst_image(year, qc=True, max_err_flag=flag), stage="lst_qc_pilot_v2", vars_=R.LST_VARS)
        m1 = m1.set_index(KEYS).loc[v1.index]
        for k, c in enumerate(LCOLS):
            raw = m0[c].notna()  # v1 values that were not gap-filled
            res.setdefault(c, {"noqc_vs_v1_maxabs": float((m0[c] - v1[c])[raw].abs().max()),
                               "min_v1": float(v1[c].min()), "nan_noqc": float(m0[c].isna().mean()),
                               "cold10_noqc": float((m0[c].to_numpy() < md[:, k] - 10).mean())})
            res[c][f"err_flag{flag}"] = {"minus_v1_mean": float((m1[c] - v1[c]).mean()), "r_v1": float(m1[c].corr(v1[c])),
                                         "min": float(m1[c].min()), "nan": float(m1[c].isna().mean()),
                                         "cold10": float((m1[c].to_numpy() < md[:, k] - 10).mean())}
    res["eecu_s"] = b.eecu
    (OUT / f"pilot_lst_{U.ISO3[country]}_{adm1.replace(' ', '_')}_{year}_v2.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


def run_lst_v2(country):
    """rs_monthly_<c>_v2 = v1 with the four LST columns recomputed with the v2 QC rule (same keys,
    order, dtypes; all other columns copied bit-identical from v1)."""
    t = time.time()
    c = country.lower()
    v1 = pd.read_parquet(OUT / f"rs_monthly_{c}_v1.parquet")
    yrs = sorted(v1.year.unique().tolist())
    b = Builder(country)
    eps = b.pop_weights_v2(yrs, OUT / f"ghsl_pop_cells_{c}_v2.npz")
    parts = []
    for y in yrs:  # per-year cache: a crash or budget stop does not lose paid EECU
        f = OUT / "lst_v2_cache" / f"lst_raw_{c}_{y}_v2.parquet"
        if f.exists():
            parts.append(pd.read_parquet(f))
            continue
        d = b.modis(y, img=R.lst_image(y, qc=True), stage="lst_qc_v2", vars_=R.LST_VARS)
        f.parent.mkdir(exist_ok=True)
        d.to_parquet(f, index=False)
        parts.append(d)
    new = pd.concat(parts, ignore_index=True)
    raw_nan = new[LCOLS].isna().mean().round(5).to_dict()
    new, nfill = R.fill_prev_year(new, LCOLS)
    new = new.set_index(KEYS)
    idx = pd.MultiIndex.from_frame(v1[KEYS])
    missing = (~idx.isin(new.index)).sum()
    if missing or len(new) != len(v1):
        raise RuntimeError(f"key mismatch v1 vs v2: {missing} v1 keys missing, {len(new)} vs {len(v1)} rows")
    new = new.reindex(idx)
    v2 = v1.copy()
    for col in LCOLS:
        v2[col] = new[col].to_numpy().astype(v1[col].dtype)
    assert list(v2.columns) == list(v1.columns) and (v2.dtypes == v1.dtypes).all()
    same = {col: _same_bits(v2[col], v1[col]) for col in v1.columns if col not in LCOLS}
    if not all(same.values()):
        raise RuntimeError(f"non-LST columns changed: {same}")
    v2.to_parquet(OUT / f"rs_monthly_{c}_v2.parquet", index=False)
    rep = {"country": country, "version": "v2", "rule": R.LST_QC_RULE, "years": [yrs[0], yrs[-1]],
           "units": len(b.ids), "no_geometry_skipped": b.no_geom, "ghsl_pop_epochs": eps,
           "eecu_s": b.eecu, "wall_s": time.time() - t, "non_lst_columns_bit_identical_to_v1": same,
           "monthly": {**qa(v2, MCOLS, KEYS), "lst_nan_rate_before_fill": raw_nan, "lst_filled_from_prev_year": nfill}}
    (OUT / f"rs_{c}_v2.qa.json").write_text(json.dumps(rep, indent=1, default=str))
    log_cost({"stage": "run_total_lst_v2_info", "country": country, "eecu_s": 0, "eecu_s_run": b.eecu, "wall_s": rep["wall_s"]})
    print(json.dumps(rep, indent=1, default=str))


def cold_share(df, col, thr=10.0) -> float:
    """Share of non-NaN unit-months more than ``thr`` deg C below the unit's calendar-month median."""
    med = df.groupby(["unit_id", "month"])[col].transform("median")
    ok = df[col].notna()
    return float(((df[col] < med - thr) & ok).sum() / ok.sum())


def compare_lst(countries=("brazil", "colombia", "peru", "taiwan")):
    out = {}
    for c in countries:
        f2 = OUT / f"rs_monthly_{c}_v2.parquet"
        if not f2.exists():
            print(f"skip {c}: no v2")
            continue
        a, b = pd.read_parquet(OUT / f"rs_monthly_{c}_v1.parquet"), pd.read_parquet(f2)
        assert a[KEYS].equals(b[KEYS])
        q1 = json.loads((OUT / f"rs_{c}_v1.qa.json").read_text())["monthly"]["nan_rate_before_fill"]
        q2 = json.loads((OUT / f"rs_{c}_v2.qa.json").read_text())["monthly"]["lst_nan_rate_before_fill"]
        r = {}
        for col in LCOLS:
            x, y = a[col].astype("float64"), b[col].astype("float64")
            ok = x.notna() & y.notna()
            d = (y - x)[ok]
            r[col] = {"cold10_v1": cold_share(a, col), "cold10_v2": cold_share(b, col),
                      "min_v1": float(x.min()), "min_v2": float(y.min()), "max_v1": float(x.max()), "max_v2": float(y.max()),
                      "mean_v1": float(x[ok].mean()), "mean_v2": float(y[ok].mean()), "mean_diff": float(d.mean()),
                      "mean_abs_diff": float(d.abs().mean()), "p99_abs_diff": float(d.abs().quantile(.99)),
                      "r": float(np.corrcoef(x[ok], y[ok])[0, 1]),
                      "nan_before_fill_v1": q1[col], "nan_before_fill_v2": q2[col],
                      "nan_after_fill_v1": float(x.isna().mean()), "nan_after_fill_v2": float(y.isna().mean())}
        out[c] = r
    (OUT / "rs_lst_compare_v1_v2.json").write_text(json.dumps(out, indent=1))
    rows = [{"country": c, "col": k, **v} for c, r in out.items() for k, v in r.items()]
    print(pd.DataFrame(rows).to_string(float_format=lambda v: f"{v:.4g}"))


def merge_pop():
    fs = sorted(POP_OUT.glob("unit_population_yearly_*_v1.parquet"))
    df = pd.concat([pd.read_parquet(f) for f in fs], ignore_index=True)
    df.to_parquet(POP_OUT / "unit_population_yearly_v1.parquet", index=False)
    print(len(df), [f.name for f in fs])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=["pilot", "run", "merge-pop", "pilot-lst", "run-lst-v2", "compare-lst"])
    ap.add_argument("country", nargs="?")
    ap.add_argument("--adm1")
    ap.add_argument("--year", type=int, default=2023)
    ap.add_argument("--skip-native", action="store_true")
    ap.add_argument("--one-epoch", action="store_true")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    if a.stage == "merge-pop":
        merge_pop()
    elif a.stage == "compare-lst":
        compare_lst()
    elif a.stage in ("pilot-lst", "run-lst-v2"):
        U.init()
        pilot_lst(a.country.upper(), a.adm1, a.year) if a.stage == "pilot-lst" else run_lst_v2(a.country.upper())
    else:
        U.init()
        pilot(a.country.upper(), a.adm1, a.year, not a.one_epoch, not a.skip_native) if a.stage == "pilot" else run(a.country.upper())
