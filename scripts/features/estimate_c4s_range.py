#!/usr/bin/env python
"""C4s range per country (control fixes 2026-11-16): the S3 buffer D, by the same rule as
scripts/splits/build_splits.py.

  BRAZIL, COLOMBIA: copied from data/processed/splits_v1/buffer_distance.json (D_km).
  PERU, TAIWAN (no S3 split): the same rule on de-seasonalised log1p(cases), 2014-2019:
      D = max of the first 0.1-crossings of the 'additive' and 'week_fe' correlograms (>= 30 pairs
      per bin). If neither curve crosses 0.1 (or < 30 usable units), fallback D = median
      great-circle distance from a unit to its 10th-nearest unit (all units of the country).
Writes data/processed/splits_v1/c4s_range_km.json ({COUNTRY: {range_km, method, ...}}); does not
touch the split files. Usage: python scripts/features/estimate_c4s_range.py
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from pop.splits import spatial as sp

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data/processed/splits_v1/c4s_range_km.json"
CG_YEARS, THRESH, MIN_UNITS = (2014, 2019), 0.1, 30
BIN_KM = {"PERU": 25.0, "TAIWAN": 5.0}
MAX_KM = {"PERU": 1500.0, "TAIWAN": 300.0}


def knn10_median(cent: pd.DataFrame) -> float:
    c = cent.dropna(subset=["lon", "lat"])
    D = sp.haversine_matrix(c.lon.to_numpy(), c.lat.to_numpy())
    np.fill_diagonal(D, np.inf)
    return float(np.median(np.sort(D, axis=1)[:, 9]))


def main() -> None:
    panel = pd.read_parquet(ROOT / "data/processed/panel_weekly_v1.parquet",
                            columns=["unit_id", "country", "adm1", "week_start", "year", "cases", "flag_gap"])
    bnd = pd.read_parquet(ROOT / "data/interim/boundaries/opendengue_units_v1.parquet",
                          columns=["unit_id", "centroid_lon", "centroid_lat"])
    cent = sp.unit_centroids(panel, bnd)
    bd = json.loads((ROOT / "data/processed/splits_v1/buffer_distance.json").read_text())
    out = {}
    for c in ("BRAZIL", "COLOMBIA", "PERU", "TAIWAN"):
        cc = cent[cent.country == c]
        k10 = knn10_median(cc)
        if c in bd:
            out[c] = {"range_km": float(bd[c]["D_km"]), "method": "s3_buffer_D (buffer_distance.json)",
                      "knn10_median_km": round(k10, 2)}
            continue
        q = panel[(panel.country == c) & panel.year.between(*CG_YEARS)]
        res = {}
        for mode in ("additive", "week_fe"):
            r = sp.deseasonalised_residuals(q, mode)
            cg = sp.correlogram(r, cc, BIN_KM[c], MAX_KM[c])
            res[mode] = {"n_units": int(r.shape[1]), "first_crossing_km": sp.first_crossing(cg, THRESH),
                         "curve": cg[["dist_mid", "mean", "count"]].round(4).to_dict("list")}
        xs = [v["first_crossing_km"] for v in res.values() if np.isfinite(v["first_crossing_km"])]
        n_units = min(v["n_units"] for v in res.values())
        if xs and n_units >= MIN_UNITS:
            D, method = float(max(xs)), "correlogram rule as S3 D (max first 0.1-crossing, additive/week_fe)"
        else:
            D, method = round(k10, 2), "fallback: median distance to the 10th-nearest unit"
        out[c] = {"range_km": D, "method": method, "years": list(CG_YEARS), "bin_km": BIN_KM[c],
                  "knn10_median_km": round(k10, 2),
                  **{m: {"n_units": v["n_units"], "first_crossing_km": v["first_crossing_km"]}
                     for m, v in res.items()},
                  "curves": {m: v["curve"] for m, v in res.items()}}
    OUT.write_text(json.dumps(out, indent=1))
    for c, v in out.items():
        print(c, v["range_km"], v["method"], "knn10", v["knn10_median_km"],
              {m: v[m] for m in ("additive", "week_fe") if m in v})


if __name__ == "__main__":
    main()
