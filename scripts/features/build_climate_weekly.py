"""Weekly district ERA5-Land climate (pop- and area-weighted).

    python scripts/features/build_climate_weekly.py pilot BRAZIL --year 2023   # grid vs EE reduceRegions
    python scripts/features/build_climate_weekly.py run BRAZIL                 # full panel weeks, grid method

Outputs in data/interim/climate/: climate_weekly_<country>_v1.parquet, cost log (costs.jsonl),
pilot files pilot_<iso3>_<year>_{grid,ee}.parquet and pilot_<iso3>_<year>_compare.json.
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

OUT = Path("data/interim/climate")
PANEL = "data/processed/panel_weekly_v1.parquet"
UNITS = "data/interim/boundaries/units_simplified_v1.parquet"
COLS = C.VARS + [f"{v}_area" for v in C.VARS]


def log_cost(rec: dict) -> None:
    rec = {**rec, "time": pd.Timestamp.now().isoformat()}
    print(json.dumps(rec))
    with (OUT / "costs.jsonl").open("a") as f:
        f.write(json.dumps(rec) + "\n")


def units(country: str) -> gpd.GeoDataFrame:
    g = gpd.read_parquet(UNITS)
    g = g[g.country == country].reset_index(drop=True)
    c = g.geometry.representative_point()
    return g.assign(lon=c.x, lat=c.y)


class GridMethod:
    """Local zonal stats on downloaded ERA5-Land weekly grids (see pop.features.climate)."""

    def __init__(self, country: str):
        self.country, self.g = country, None
        self.u = units(country)
        self.g = C.snap_bbox(self.u.total_bounds)
        self.eecu, self.W = 0.0, {}
        t = time.time()
        self.cov = C.coverage_table(self.u, self.g)
        self.need = np.zeros((self.g["ny"], self.g["nx"]), bool)
        self.need[self.cov.r.values // C.FINE, self.cov.c.values // C.FINE] = True
        print(f"cells needed {self.need.mean():.2f} of bbox; coverage table {len(self.cov):,} rows in {time.time() - t:.0f}s; grid {self.g}")

    def _land(self):
        if not hasattr(self, "land"):
            land, e = U.profiled(lambda: C.compute_pixels(C.weekly_image(pd.Timestamp("2020-01-05")).select("tmean"), self.g))
            self.eecu += e
            self.land = ~np.isnan(land[0])
            self.Wa_raw = C.weight_matrix(self.cov, self.g, len(self.u), None, self.land)
            self.nearest = C.nearest_land_cell(self.u.lon.values, self.u.lat.values, self.g, self.land)
            self.Wa, self.src_area = C.finalize_weights(self.Wa_raw, self.Wa_raw, self.nearest)
        return self.land

    def weights(self, epoch: int):
        land = self._land()
        if epoch not in self.W:
            t = time.time()
            pop, e = C.download_pop(epoch, self.g, need=self.need)
            self.eecu += e
            Wp = C.weight_matrix(self.cov, self.g, len(self.u), pop, land)
            self.W[epoch] = C.finalize_weights(Wp, self.Wa_raw, self.nearest)
            src = pd.Series(self.W[epoch][1]).value_counts().to_dict()
            log_cost({"stage": "pop", "country": self.country, "epoch": epoch, "eecu_s": e,
                      "wall_s": time.time() - t, "people": float(pop.sum()), "weight_source": src})
        return self.W[epoch][0]

    def extract(self, weeks) -> pd.DataFrame:
        weeks = pd.DatetimeIndex(weeks)
        frames = []
        for ep in sorted({C.nearest_epoch(w.year) for w in weeks}):
            ws = weeks[[C.nearest_epoch(w.year) == ep for w in weeks]]
            Wp = self.weights(ep)
            t = time.time()
            grids, e = C.download_weeks(ws, self.g)
            self.eecu += e
            log_cost({"stage": "weeks", "country": self.country, "epoch": ep, "first": f"{ws[0]:%Y-%m-%d}",
                      "n_weeks": len(ws), "eecu_s": e, "wall_s": time.time() - t})
            vp, va = C.apply_weights(Wp, grids), C.apply_weights(self.Wa, grids)
            for i, w in enumerate(ws):
                d = pd.DataFrame({"unit_id": self.u.unit_id.astype(str).values, "week_start": w})
                for j, v in enumerate(C.VARS):
                    d[v], d[f"{v}_area"] = vp[i, j], va[i, j]
                frames.append(d)
        return pd.concat(frames, ignore_index=True)


def qa(df: pd.DataFrame, weeks, unit_ids) -> dict:
    full = pd.MultiIndex.from_product([sorted(unit_ids), pd.DatetimeIndex(weeks)])
    got = pd.MultiIndex.from_frame(df[["unit_id", "week_start"]])
    rng = {c: [float(df[c].min()), float(df[c].quantile(0.001)), float(df[c].quantile(0.999)), float(df[c].max())] for c in COLS}
    return {"rows": len(df), "expected_rows": len(full), "missing_pairs": int(len(full.difference(got))),
            "nan_cells": int(df[COLS].isna().sum().sum()), "duplicates": int(got.duplicated().sum()),
            "tmin_le_tmean_le_tmax_violations": int(((df.tmin > df.tmean + 1e-6) | (df.tmean > df.tmax + 1e-6)).sum()),
            "range_min_p001_p999_max": rng}


def pilot(country: str, year: int):
    iso = U.ISO3[country]
    weeks = [w for w in C.week_starts(PANEL, country) if w.year == year]
    assert C.ndays(weeks) == [7] * len(weeks)
    # (b) grid
    t = time.time()
    gm = GridMethod(country)
    b = gm.extract(weeks)
    wall_b = time.time() - t
    b.to_parquet(OUT / f"pilot_{iso}_{year}_grid.parquet")
    log_cost({"stage": "pilot_grid_total", "country": country, "year": year, "eecu_s": gm.eecu, "wall_s": wall_b})
    # (a) EE reduceRegions -> table asset
    asset = f"{U.ASSET_ROOT}/climate_pilot_{iso}_{year}_ee"
    U.delete_asset(asset)
    while not U.asset_exists(U.units_asset_id(country)):  # upload may still be running
        time.sleep(60)
    fc = ee.FeatureCollection(U.units_asset_id(country))
    t = time.time()
    task = ee.batch.Export.table.toAsset(collection=C.ee_reduce(fc, weeks, C.nearest_epoch(year)),
                                         description=f"climate_pilot_{iso}_{year}_ee", assetId=asset)
    task.start()
    ca = U.wait(task.id, poll=30)
    sums = ee.data.computeFeatures({"expression": ee.FeatureCollection(asset), "fileFormat": "PANDAS_DATAFRAME"})
    a = C.ee_sums_to_long(sums, weeks)
    a.to_parquet(OUT / f"pilot_{iso}_{year}_ee.parquet")
    log_cost({"stage": "pilot_ee_total", "country": country, "year": year, "eecu_s": ca["eecu_s"],
              "task_wall_s": ca["wall_s"], "wall_s": time.time() - t, "task": task.id})
    m = a.merge(b, on=["unit_id", "week_start"], suffixes=("_ee", "_grid"))
    cmp = {"n": len(m), "eecu_s": {"ee": ca["eecu_s"], "grid": gm.eecu},
           "wall_s": {"ee_task": ca["wall_s"], "grid_total": wall_b}}
    for c in COLS:
        x, y = m[f"{c}_ee"], m[f"{c}_grid"]
        ok = x.notna() & y.notna()
        cmp[c] = {"r": float(np.corrcoef(x[ok], y[ok])[0, 1]), "mad": float((x[ok] - y[ok]).abs().median()),
                  "p99_ad": float((x[ok] - y[ok]).abs().quantile(0.99)), "nan_ee": int(x.isna().sum()), "nan_grid": int(y.isna().sum())}
    (OUT / f"pilot_{iso}_{year}_compare.json").write_text(json.dumps(cmp, indent=1))
    print(json.dumps(cmp, indent=1))


def run(country: str):
    weeks = C.week_starts(PANEL, country)
    nd = C.ndays(list(weeks))
    assert nd == [7] * len(weeks), f"incomplete ERA5 weeks: {[w for w, n in zip(weeks, nd) if n != 7]}"
    t = time.time()
    gm = GridMethod(country)
    parts = []
    for y in sorted({w.year for w in weeks}):
        parts.append(gm.extract([w for w in weeks if w.year == y]))
    df = pd.concat(parts, ignore_index=True).sort_values(["unit_id", "week_start"], ignore_index=True)
    for c in COLS:
        df[c] = df[c].astype("float32")
    path = OUT / f"climate_weekly_{country.lower()}_v1.parquet"
    df.to_parquet(path, index=False)
    panel_units = pd.read_parquet(PANEL, columns=["unit_id", "country"], filters=[("country", "==", country)]).unit_id.astype(str).unique()
    rep = {"country": country, "eecu_s": gm.eecu, "wall_s": time.time() - t,
           "weight_source_area": pd.Series(gm.src_area).value_counts().to_dict(),
           "panel_units_missing_polygons": sorted(set(panel_units) - set(gm.u.unit_id.astype(str)))[:20],
           **qa(df, weeks, panel_units)}
    (OUT / f"climate_weekly_{country.lower()}_v1.qa.json").write_text(json.dumps(rep, indent=1, default=str))
    log_cost({"stage": "run_total", "country": country, "eecu_s": gm.eecu, "wall_s": rep["wall_s"]})
    print(json.dumps(rep, indent=1, default=str))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=["pilot", "run"])
    ap.add_argument("country")
    ap.add_argument("--year", type=int, default=2023)
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    U.init()
    pilot(a.country.upper(), a.year) if a.stage == "pilot" else run(a.country.upper())
