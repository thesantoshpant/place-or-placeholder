"""Pilot: AlphaEarth district means for 100 Brazilian municipalities (year 2022).

Usage: python scripts/features/pilot_alphaearth.py STAGE
  pop      GHSL-2020 population for all Brazil units at 1 km (for stratification)
  sample   draw 100 units (10 largest Amazon + 90 area x pop strata)
  extract  100 m, weighted + unweighted, -> pilot_brazil_100_2022.parquet
  scale    10 small/medium units at 10/30/100 m -> cosine vs 10 m
  norms    ~1000 pixel norms + district-mean norms
  units    export the 100 boundaries to an EE table asset
  export   batch export (100 m, pop-weighted) of the 100 units -> asset
  costsub  uncached cost check on the 90 non-Amazon units (pop vs both)
  coarse   300 m accuracy (vs 10 m) and batch cost on the 90 units
  cost     read EECU usage / wall time of the export task
"""
import json
import sys
import time
from pathlib import Path

import ee
import geopandas as gpd
import numpy as np
import pandas as pd
import shapely

from pop.features import alphaearth as ae

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data/interim/alphaearth"
OUT.mkdir(parents=True, exist_ok=True)
YEAR = 2022
AMAZON = {"ACRE", "AMAZONAS", "AMAPA", "PARA", "RONDONIA", "RORAIMA"}


def brazil():
    d = pd.read_parquet(ROOT / "data/interim/boundaries/opendengue_units_v1.parquet")
    d = d[d.country == "BRAZIL"].copy()
    return gpd.GeoDataFrame(d, geometry=shapely.from_wkb(d.geometry.values), crs="EPSG:4326")


def stage_pop():
    g = brazil()
    rows = []
    for i in range(0, len(g), 400):
        fc = ae.units_to_fc(g.iloc[i:i + 400], simplify_deg=0.01)
        r = ae.pop_per_pixel(2020).unmask(0).reduceRegions(fc, ee.Reducer.sum(), scale=1000, tileScale=2)
        rows += [f["properties"] for f in r.getInfo()["features"]]
    p = pd.DataFrame(rows).rename(columns={"sum": "pop_ghsl2020_1km"})
    p.to_parquet(OUT / "brazil_pop_ghsl2020_1km.parquet")
    print(p.describe())


def stage_sample(seed=42):
    g = brazil().merge(pd.read_parquet(OUT / "brazil_pop_ghsl2020_1km.parquet"), on="unit_id")
    amz = g[g.adm1.isin(AMAZON)].nlargest(10, "area_km2").assign(stratum="amazon_largest")
    rest = g.drop(amz.index)
    rest = rest.assign(a=pd.qcut(rest.area_km2, 3, labels=["aS", "aM", "aL"]),
                       p=pd.qcut(rest.pop_ghsl2020_1km, 3, labels=["pS", "pM", "pL"]))
    picks = [grp.sample(10, random_state=seed).assign(stratum=f"{a}_{p}")
             for (a, p), grp in rest.groupby(["a", "p"], observed=True)]
    s = pd.concat([amz, *picks])[["unit_id", "adm1", "adm2", "area_km2", "pop_ghsl2020_1km", "stratum"]]
    s.to_csv(OUT / "pilot_sample_100.csv", index=False)
    print(s.stratum.value_counts().to_string(), "\n", s.area_km2.sum())


def sample_gdf():
    s = pd.read_csv(OUT / "pilot_sample_100.csv", dtype={"unit_id": str})
    g = brazil()[["unit_id", "geometry"]]
    return gpd.GeoDataFrame(s.merge(g, on="unit_id"), geometry="geometry", crs="EPSG:4326")


def stage_extract():
    g = sample_gdf().sort_values("area_km2")
    t = time.time()
    small, big = g[g.area_km2 < 20000], g[g.area_km2 >= 20000]
    df = pd.concat([ae.extract(small, YEAR, 100, "both", chunk=15, tile_scale=4),
                    ae.extract(big, YEAR, 100, "both", chunk=2, tile_scale=8)], ignore_index=True)
    df.to_parquet(OUT / f"pilot_brazil_100_{YEAR}.parquet", index=False)
    print(f"interactive extract {time.time() - t:.0f}s, rows={len(df)}")
    print(df.groupby("weighting").raw_norm.describe())


def stage_scale():
    g = sample_gdf()
    sub = g[g.area_km2 < 1500].groupby("stratum", group_keys=False).head(2).sort_values("area_km2").head(10)
    res = []
    for sc in (10, 30, 100):
        t = time.time()
        df = ae.extract(sub, YEAR, sc, "both", chunk=1 if sc == 10 else 5, tile_scale=16 if sc == 10 else 4,
                        renormalise=False)
        print(f"scale {sc}: {time.time() - t:.0f}s", flush=True)
        res.append(df)
    df = pd.concat(res, ignore_index=True)
    df.to_parquet(OUT / f"pilot_scale_test_{YEAR}.parquet", index=False)
    ref = df[df.scale == 10].set_index(["unit_id", "weighting"])
    out = []
    for sc in (30, 100):
        x = df[df.scale == sc].set_index(["unit_id", "weighting"]).loc[ref.index]
        cs = ae.cosine(x[ae.BANDS].values, ref[ae.BANDS].values)
        out.append(pd.DataFrame({"scale": sc, "cos": cs, "pop_rel_err": (x.pop_sum / ref.pop_sum - 1).values},
                                index=ref.index))
    out = pd.concat(out).reset_index().merge(sub[["unit_id", "area_km2"]], on="unit_id")
    out.to_csv(OUT / "pilot_scale_cosine.csv", index=False)
    print(out.groupby(["scale", "weighting"]).cos.describe().to_string())
    print(out.groupby(["scale", "weighting"]).pop_rel_err.describe().to_string())


def stage_norms():
    g = sample_gdf()
    region = ae.units_to_fc(g[g.area_km2 < 20000], simplify_deg=0.005).geometry()
    n = ae.sample_pixel_norms(region, YEAR, n=1000, scale=10)
    np.save(OUT / "pilot_pixel_norms.npy", n)
    print("pixel norms n=%d" % len(n), pd.Series(n).describe(percentiles=[.01, .05, .5, .95, .99]).to_string())
    df = pd.read_parquet(OUT / f"pilot_brazil_100_{YEAR}.parquet")
    print(df.groupby("weighting").raw_norm.describe(percentiles=[.05, .5, .95]).to_string())


def stage_units():
    ae.ensure_asset_folder()
    t = ae.export_units_asset(ae.units_to_fc(sample_gdf(), simplify_deg=5e-4), "br_pilot100_units")
    print(t.id)


def stage_export():
    fc = ee.FeatureCollection(f"{ae.ASSET_ROOT}/br_pilot100_units")
    t = ae.export_extract(fc, YEAR, f"br_pilot100_{YEAR}_100m_pop", 100, "pop", tile_scale=4)
    (OUT / "export_task.json").write_text(json.dumps({"task_id": t.id}))
    print(t.id)


def stage_costsub():
    """Uncached cost check: non-Amazon units, pop-only vs both, tileScale 2."""
    g = sample_gdf()
    sub = g[g.stratum != "amazon_largest"]
    fc = ee.FeatureCollection(f"{ae.ASSET_ROOT}/br_pilot100_units").filter(
        ee.Filter.inList("unit_id", sub.unit_id.tolist()))
    ids = {w: ae.export_extract(fc, YEAR, f"br_pilot90_{YEAR}_100m_{w}", 100, w, tile_scale=2).id
           for w in ("pop", "both")}
    (OUT / "export_task_sub.json").write_text(json.dumps({**ids, "area_km2": float(sub.area_km2.sum())}))
    print(ids)


def stage_coarse(sc=300):
    """Accuracy (vs 10 m) and uncached batch cost at a coarser scale."""
    ref = pd.read_parquet(OUT / f"pilot_scale_test_{YEAR}.parquet").query("scale == 10")
    g = sample_gdf()
    x = ae.extract(g[g.unit_id.isin(ref.unit_id)], YEAR, sc, "both", chunk=5, renormalise=False)
    m = x.merge(ref, on=["unit_id", "weighting"], suffixes=("", "_r"))
    m["cos"] = ae.cosine(m[ae.BANDS].values, m[[b + "_r" for b in ae.BANDS]].values)
    print(m.groupby("weighting").cos.describe().to_string())
    sub = g[g.stratum != "amazon_largest"]
    fc = ee.FeatureCollection(f"{ae.ASSET_ROOT}/br_pilot100_units").filter(
        ee.Filter.inList("unit_id", sub.unit_id.tolist()))
    t = ae.export_extract(fc, YEAR, f"br_pilot90_{YEAR}_{sc}m_both", sc, "both", tile_scale=2)
    while ee.data.getTaskStatus(t.id)[0]["state"] in ("READY", "RUNNING"):
        time.sleep(15)
    c = ae.task_cost(t.id)
    print(sc, "m both:", c["state"], c["eecu_s"], c["wall_s"])


def stage_cost():
    tid = json.loads((OUT / "export_task.json").read_text())["task_id"]
    c = ae.task_cost(tid)
    print(json.dumps(c, indent=1, default=str))


if __name__ == "__main__":
    ae.init()
    globals()[f"stage_{sys.argv[1]}"]()
