"""Pilot of cheaper AlphaEarth district-mean estimators (Brazil, 100 units, 2022).

  points   fetch GHSL 100 m rasters per unit, draw point sets -> cheap_pilot/points.parquet
  footprint  area share of populated blocks per unit -> cheap_pilot/footprint.csv
  local <res> <n> <float|int8> <block>  computePixels + local zonal means on n units
  submit   start batch exports: <variant> [<variant> ...]
           point variants: pop_N, area_N, popsys_N (N points/unit)
           coarse variants: coarse_<scale>_<pyramid|rr>[_<subset>]
  wait     block until all logged tasks finish
  collect  download finished exports, log EECU, compute metrics -> cheap_pilot/metrics.csv
"""
from __future__ import annotations

import json
import zlib
import sys
import time
from pathlib import Path

import ee
import geopandas as gpd
import numpy as np
import pandas as pd

from pop.features import alphaearth as ae
from pop.features import alphaearth_sampling as aes

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "data/interim/alphaearth"
OUT = SRC / "cheap_pilot"
YEAR, NMAX, CHUNK = 2022, 4000, 25
TASKS = OUT / "tasks.json"


def units() -> gpd.GeoDataFrame:
    s = pd.read_csv(SRC / "pilot_sample_100.csv", dtype={"unit_id": str})
    g = gpd.read_parquet(ROOT / "data/interim/boundaries/opendengue_units_v1.parquet")[["unit_id", "geometry"]]
    g = gpd.GeoDataFrame(s.merge(g, on="unit_id"), geometry="geometry", crs="EPSG:4326")
    g["geometry"] = g.geometry.simplify(5e-4, preserve_topology=True)  # as the reference
    return g


def cmd_points():
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    for k, r in units().iterrows():
        t = time.time()
        pop, mask, c0, r0 = aes.pop_raster(r.geometry)
        for how in ("pop", "area", "pop_sys"):
            for n in (250, 1000, 4000):
                if how == "pop_sys" and n != 1000:
                    continue
                xy = aes.draw_points(pop, mask, c0, r0, n, how, np.random.default_rng(zlib.crc32(f"{r.unit_id}{how}{n}".encode())))
                rows.append(pd.DataFrame({"unit_id": r.unit_id, "how": how, "n": n, "lon": xy[:, 0], "lat": xy[:, 1]}))
        print(k, r.unit_id, pop.shape, f"pop={pop.sum():.0f} px={mask.sum()} {time.time() - t:.1f}s", flush=True)
    pd.concat(rows).to_parquet(OUT / "points.parquet")


def cmd_footprint():
    """Share of each unit's area in populated 1 km / 2.56 km blocks (free: local GHSL)."""
    rows = []
    for k, r in units().iterrows():
        pop, mask, c0, r0 = aes.pop_raster(r.geometry)
        rec = {"unit_id": r.unit_id, "area_px": int(mask.sum())}
        for b in (10, 26):
            H, W = (np.array(pop.shape) // b + 1) * b
            P = np.zeros((H, W)); M = np.zeros((H, W))
            P[:pop.shape[0], :pop.shape[1]] = pop; M[:pop.shape[0], :pop.shape[1]] = mask
            Pb = P.reshape(H // b, b, W // b, b).sum((1, 3)).ravel()
            Mb = M.reshape(H // b, b, W // b, b).sum((1, 3)).ravel()
            o = np.argsort(-Pb); cp = np.cumsum(Pb[o]) / Pb.sum(); ca = np.cumsum(Mb[o]) / Mb.sum()
            rec[f"area_pop>0_b{b}"] = Mb[Pb > 0].sum() / Mb.sum()
            for q in (0.99, 0.999):
                rec[f"area_q{q}_b{b}"] = ca[np.searchsorted(cp, q)]
        rows.append(rec)
    d = pd.DataFrame(rows)
    d.to_csv(OUT / "footprint.csv", index=False)
    w = d.area_px / d.area_px.sum()
    print(d.drop(columns=["unit_id", "area_px"]).mul(w, axis=0).sum().round(4))


def cmd_local(res: float, n: int = 10, int8: bool = False, block: int = 256):
    """computePixels + local zonal stats on n mid-sized non-Amazon units (interactive, profiled)."""
    s = pd.read_csv(SRC / "pilot_sample_100.csv", dtype={"unit_id": str})
    s = s[(s.stratum != "amazon_largest") & s.area_km2.between(150, 1500)].sort_values("area_km2")
    ids = s.unit_id.iloc[np.linspace(0, len(s) - 1, n).astype(int)].tolist()
    g = units().set_index("unit_id").geometry
    rows, est = [], []
    for uid in ids:
        t = time.time()
        r = aes.local_means(g[uid], YEAR, res, int8=int8, block=block)
        rows.append({"unit_id": uid, "res": res, "eecu_s": r["eecu_s"], "bbox_km2": r["bbox_km2"],
                     "area_km2": s.set_index("unit_id").area_km2[uid], "mb": r["mb"], "wall_s": time.time() - t})
        for w in ("pop", "none"):
            est.append({"unit_id": uid, "weighting": w, **dict(zip(ae.BANDS, r[w]))})
        print(rows[-1], flush=True)
    tag = f"local_{int(res)}" + ("_int8" if int8 else "") + (f"_b{block}" if block != 256 else "")
    pd.DataFrame(rows).to_csv(OUT / f"{tag}_cost.csv", index=False)
    e = pd.DataFrame(est); e.to_parquet(OUT / f"{tag}_est.parquet")
    ref = pd.read_parquet(SRC / f"pilot_brazil_100_{YEAR}.parquet")
    for w in ("pop", "none"):
        print(tag, w, aes.compare(e[e.weighting == w].set_index("unit_id"), ref[ref.weighting == w].set_index("unit_id")))
    c = pd.DataFrame(rows)
    print(tag, "EECU-s", c.eecu_s.sum(), "per bbox km2", c.eecu_s.sum() / c.bbox_km2.sum())


def load_tasks() -> dict:
    return json.loads(TASKS.read_text()) if TASKS.exists() else {}


def cmd_submit(variants):
    tasks = load_tasks()
    pts = pd.read_parquet(OUT / "points.parquet") if any(not v.startswith("coarse") for v in variants) else None
    for v in variants:
        if v.startswith("fp"):
            _, b, uid = v.split("_")
            g = units().set_index("unit_id").geometry[uid]
            fp, km2 = aes.footprint_geometry(g, int(b))
            print(v, f"footprint {fp.area / g.area:.3f} of unit (deg^2), {len(fp.wkt)} chars", flush=True)
            fc = ae.units_to_fc(gpd.GeoDataFrame({"unit_id": [uid]}, geometry=[fp]), simplify_deg=0)
            sel = ["unit_id", "year", "scale", "pop_sum", "n_pixels", *ae.WBANDS]
            jobs = [(v, ae.reduce_units(fc, YEAR, 100, "pop", centroid=True).select(sel, None, True))]
        elif v.startswith("coarse"):
            _, sc, mode, *sub = v.split("_")
            fc = ee.FeatureCollection(f"{ae.ASSET_ROOT}/br_pilot100_units")
            if sub:  # subset: 'na' = 90 non-Amazon units, 'small' = 10 smallest
                s = pd.read_csv(SRC / "pilot_sample_100.csv", dtype={"unit_id": str})
                s = s[s.stratum != "amazon_largest"] if sub[0] == "na" else s.nsmallest(10, "area_km2")
                fc = fc.filter(ee.Filter.inList("unit_id", s.unit_id.tolist()))
            sel = ["unit_id", "year", "scale", "pop_sum", "n_pixels", *ae.WBANDS, *ae.BANDS]
            coll = aes.coarse_reduce(fc, YEAR, float(sc), mode).select(sel, None, True)
            jobs = [(v, coll)]
        else:
            how, n = v.split("_")
            how = {"popsys": "pop_sys"}.get(how, how)
            p = pts[(pts.how == how) & (pts.n == int(n))]
            ids = p.unit_id.unique()
            step = CHUNK if int(n) >= 4000 else len(ids)
            jobs = []
            for i in range(0, len(ids), step):
                sub = p[p.unit_id.isin(ids[i:i + step])]
                fc = aes.points_fc({u: g[["lon", "lat"]].to_numpy() for u, g in sub.groupby("unit_id")})
                jobs.append((f"{v}_{i // step}" if step < len(ids) else v, aes.point_means(fc, YEAR)))
        for name, coll in jobs:
            name = f"cheap_{name}"
            aid = f"{ae.ASSET_ROOT}/{name}"
            try:
                ee.data.deleteAsset(aid)
            except ee.EEException:
                pass
            t = ee.batch.Export.table.toAsset(collection=coll, description=name, assetId=aid)
            t.start()
            tasks[name] = {"id": t.id, "variant": v}
            print(name, t.id, flush=True)
    TASKS.write_text(json.dumps(tasks, indent=1))


def cmd_wait():
    ids = [t["id"] for t in load_tasks().values()]
    while True:
        st = [ae.task_cost(i)["state"] for i in ids]
        if all(s in ("SUCCEEDED", "FAILED", "CANCELLED") for s in st):
            return
        time.sleep(15)


def cmd_collect():
    tasks = load_tasks()
    for name, t in tasks.items():
        if t.get("eecu_s") is None or t.get("state") != "SUCCEEDED":
            c = ae.task_cost(t["id"])
            t.update(state=c["state"], eecu_s=c["eecu_s"], wall_s=c["wall_s"])
        print(name, t["state"], t["eecu_s"], t["wall_s"], ae.task_cost(t["id"])["metadata"].get("error", "") if t["state"] == "FAILED" else "")
    TASKS.write_text(json.dumps(tasks, indent=1))
    ref = pd.read_parquet(SRC / f"pilot_brazil_100_{YEAR}.parquet")
    area = pd.read_csv(SRC / "pilot_sample_100.csv", dtype={"unit_id": str}).set_index("unit_id").area_km2
    est_rows, metrics = [], []
    by_var: dict[str, list] = {}
    # previous pilot's naive 300 m export (NN-resampled pop), reused without recomputation
    by_var["naive_300_pyramid_na"] = [("@br_pilot90_2022_300m_both", {"state": "SUCCEEDED", "eecu_s": 516.0})]
    for name, t in tasks.items():
        by_var.setdefault(t["variant"], []).append((name, t))
    for v, lst in by_var.items():
        if any(t["state"] != "SUCCEEDED" for _, t in lst):
            continue
        feats = []
        for name, _ in lst:
            fc = ee.FeatureCollection(f"{ae.ASSET_ROOT}/{name.lstrip('@')}")
            feats += [f["properties"] for f in fc.getInfo()["features"]]
        eecu = sum(t["eecu_s"] or 0 for _, t in lst)
        if v.startswith(("coarse", "naive", "fp")):
            df = ae.sums_to_frame(feats)
            pairs = [(w, df[df.weighting == w]) for w in ("pop", "none") if (df.weighting == w).any()]
        else:
            df = pd.DataFrame(feats).rename(columns=lambda c: c.replace("_mean", ""))
            df["unit_id"] = df.unit_id.astype(str)
            pairs = [("none" if v.startswith("area") else "pop", df)]
        for w, d in pairs:
            d = d.set_index("unit_id")
            est_rows.append(d[ae.BANDS].assign(variant=v, weighting=w).reset_index())
            r = ref[ref.weighting == w].set_index("unit_id")
            m = aes.compare(d, r)
            n_units = len(d)
            metrics.append({"variant": v, "weighting": w, **m, "eecu_s": eecu,
                            "eecu_s_per_unit": eecu / n_units, "eecu_s_per_km2": eecu / area.loc[d.index].sum()})
    if not est_rows:
        return
    pd.concat(est_rows).to_parquet(OUT / "estimates.parquet")
    m = pd.DataFrame(metrics)
    m.to_csv(OUT / "metrics.csv", index=False)
    with pd.option_context("display.width", 200, "display.max_columns", 20):
        print(m.round(5))


if __name__ == "__main__":
    ae.init()
    {"points": lambda: cmd_points(), "submit": lambda: cmd_submit(sys.argv[2:]),
     "collect": lambda: cmd_collect(), "wait": lambda: cmd_wait(), "footprint": lambda: cmd_footprint(),
     "local": lambda: cmd_local(float(sys.argv[2]), int(sys.argv[3]), sys.argv[4] == "int8", int(sys.argv[5]))}[sys.argv[1]]()
