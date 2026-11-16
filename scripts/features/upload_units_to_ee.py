"""Simplify district polygons and upload them to Earth Engine (one asset per country).

Re-runnable per country: re-reads opendengue_units_v1.parquet each time, replaces that
country's rows in units_simplified_v1.parquet and overwrites its EE asset.

    python scripts/features/upload_units_to_ee.py BRAZIL [--tol 0.001] [--dry-run] [--no-overwrite]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import geopandas as gpd
import pandas as pd
import shapely

from pop.features import ee_utils

SRC = Path("data/interim/boundaries/opendengue_units_v1.parquet")
DST = Path("data/interim/boundaries/units_simplified_v1.parquet")
LOG = Path("data/interim/boundaries/units_simplified_v1.log.jsonl")
EQ = "EPSG:6933"  # equal-area for area checks


def simplify(gdf: gpd.GeoDataFrame, tol: float) -> gpd.GeoDataFrame:
    """Coverage simplification (shared edges stay shared, no new gaps/overlaps).

    Falls back to per-polygon topology-preserving simplify for any result that
    is empty or invalid (coverage_simplify assumes a clean coverage).
    """
    geoms = gdf.geometry.values
    try:
        out = shapely.coverage_simplify(geoms, tol, simplify_boundary=True)
    except ValueError:  # unclean coverage (e.g. GeometryCollections) -> per-polygon
        out = shapely.simplify(geoms, tol, preserve_topology=True)
    bad = shapely.is_empty(out) | ~shapely.is_valid(out)
    if bad.any():
        out[bad] = shapely.simplify(geoms[bad], tol, preserve_topology=True)
    bad = ~shapely.is_valid(out)
    out[bad] = shapely.make_valid(out[bad])
    g = gdf.copy()
    g["geometry"] = out
    return g, int(bad.sum())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("countries", nargs="+")
    ap.add_argument("--tol", type=float, default=0.001, help="degrees (~110 m)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-overwrite", action="store_true")
    a = ap.parse_args()
    allu = gpd.read_parquet(SRC)
    for c in [c.upper() for c in a.countries]:
        g = allu[allu.country == c][["unit_id", "country", "adm1", "adm2", "geometry"]].reset_index(drop=True)
        nogeom = g.geometry.isna() | g.geometry.is_empty
        if nogeom.any():  # units without a polygon cannot be uploaded or extracted; report and skip
            print(json.dumps({"country": c, "skipped_no_geometry": g.unit_id[nogeom].tolist()}))
            g = g[~nogeom].reset_index(drop=True)
        s, nfix = simplify(g, a.tol)
        a0, a1 = g.to_crs(EQ).area.values, s.to_crs(EQ).area.values
        rel = (a1 - a0) / a0
        nv0 = shapely.get_num_coordinates(g.geometry.values).sum()
        nv1 = shapely.get_num_coordinates(s.geometry.values).sum()
        rep = {"country": c, "n": len(g), "tol_deg": a.tol, "vertices": [int(nv0), int(nv1)],
               "area_total_rel_change": float(pd.Series(a1).sum() / pd.Series(a0).sum() - 1),
               "area_unit_abs_rel_change_median": float(pd.Series(abs(rel)).median()),
               "area_unit_abs_rel_change_p99": float(pd.Series(abs(rel)).quantile(0.99)),
               "area_unit_abs_rel_change_max": float(pd.Series(abs(rel)).max()), "n_null_or_zero_area": int((~(a0 > 0)).sum()), "n_make_valid": nfix,
               "n_empty": int(s.geometry.is_empty.sum())}
        print(json.dumps(rep))
        if a.dry_run:
            continue
        old = gpd.read_parquet(DST) if DST.exists() else None
        out = s if old is None else pd.concat([old[old.country != c], s], ignore_index=True)
        gpd.GeoDataFrame(out, geometry="geometry", crs="EPSG:4326").to_parquet(DST)
        ee_utils.init()
        res = ee_utils.upload_units(s, c, overwrite=not a.no_overwrite)
        rep.update(res)
        print(json.dumps(res))
        with LOG.open("a") as f:
            f.write(json.dumps({**rep, "time": pd.Timestamp.now().isoformat()}) + "\n")


if __name__ == "__main__":
    main()
