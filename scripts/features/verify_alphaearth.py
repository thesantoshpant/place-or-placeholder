#!/usr/bin/env python
"""Independent verification of the AlphaEarth unit-year extraction.

Usage:
    python scripts/features/verify_alphaearth.py --country brazil [--years 2017-2023]
           [--n-sample 30] [--seed 0] [--max-eecu-h 2.7] [--no-ee]

Written independently of the extractor: it reads only the final per-year
parquet files and the unit polygons, and recomputes sampled unit-years with
EE ``reduceRegion`` (own image construction, own weights).

Definitions reproduced (docs/features/alphaearth_extraction.md):
  * image   = mosaic of GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL for the year, bands A00..A63
  * weights = GHSL JRC/GHSL/P2023A/GHS_POP, values < 0 (and masked) set to 0, linear
              interpolation between the 2015/2020/2025 epochs (clamped)
  * grid    = GHS_POP native Mollweide grid; weighted pass at 100 m, unweighted at 300 m
  * w_ mean = sum(cov*pop*A) / sum(cov*pop) over pixels with a valid embedding
  * u_ mean = sum(cov*A) / sum(cov) over valid pixels (300 m)
Checks: completeness/integrity, EE recompute, temporal + duplicate + spatial sanity.
Output: data/interim/alphaearth/<country>/verification_v1.json
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import datetime as dt
import json
import os
import sys
import threading
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
UNITS = ROOT / "data/interim/boundaries/opendengue_units_v1.parquet"
UNIVERSE = ROOT / "data/processed/unit_universe_v1.csv"
COLL = "GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL"
POP = "JRC/GHSL/P2023A/GHS_POP"
BANDS = [f"A{i:02d}" for i in range(64)]
WC = [f"w_{b}" for b in BANDS]
UC = [f"u_{b}" for b in BANDS]
MOLL = "ESRI:54009"
AMAZON_UF = {"11", "12", "13", "14", "15", "16", "17"}  # Brazil North region

COS_W_MIN = 0.9999
COS_U_MIN = 0.9995  # same 300 m grid; only the polygon-coverage implementation differs
POP_RATIO_TOL = 1e-3


def parse_years(s):
    if "-" in s:
        a, b = s.split("-")
        return list(range(int(a), int(b) + 1))
    return [int(x) for x in s.split(",")]


def cos_rows(a, b):
    return (a * b).sum(1) / (np.linalg.norm(a, axis=1) * np.linalg.norm(b, axis=1))


def epoch_mix(year):
    y = min(max(year, 2015), 2025)
    e0 = 2015 if y < 2020 else (2020 if y < 2025 else 2025)
    if e0 == y:
        return [(e0, 1.0)]
    t = (y - e0) / 5.0
    return [(e0, 1.0 - t), (e0 + 5, t)]


# --------------------------------------------------------------------- local checks
def load(country, years):
    d = ROOT / "data/interim/alphaearth" / country
    fr = {}
    for y in years:
        f = d / f"alphaearth_{country}_{y}.parquet"
        if not f.exists():
            raise SystemExit(f"missing {f}")
        fr[y] = pd.read_parquet(f)
    return d, fr


def local_checks(country, fr, units):
    out = {"per_year": {}}
    exp = set(units.unit_id)
    ok = True
    for y, df in fr.items():
        ids = df.unit_id.astype(str)
        W, U = df[WC].to_numpy(float), df[UC].to_numpy(float)
        fin = np.isfinite(W).all(1) & np.isfinite(U).all(1)
        # rows with no valid embedding pixel at all (empty coverage) are an upstream gap, not a copy/NaN bug
        gap = ~fin & (df.area_km2_covered.to_numpy() == 0) & (df.pop_sum.to_numpy() == 0)
        wn, un = np.linalg.norm(W, axis=1), np.linalg.norm(U, axis=1)
        r = {
            "n_rows": len(df),
            "n_expected": len(exp),
            "n_missing": len(exp - set(ids)),
            "n_extra": len(set(ids) - exp),
            "n_dup_ids": int(ids.duplicated().sum()),
            "year_col_ok": bool((df.year.astype(int) == y).all()),
            "n_nonfinite_rows": int((~fin).sum()),
            "nonfinite_units_no_coverage": sorted(ids[gap].tolist()),
            "n_nonfinite_unexplained": int((~fin & ~gap).sum()),
            "n_pop_le0": int((df.pop_sum <= 0).sum()),
            "n_pop_le0_with_coverage": int(((df.pop_sum <= 0) & fin).sum()),
            "n_fallback": int(df.w_fallback.sum()) if "w_fallback" in df else None,
            "max_abs_norm_diff_w": float(np.nanmax(np.abs(wn - df.w_norm))),
            "max_abs_norm_diff_u": float(np.nanmax(np.abs(un - df.u_norm))),
            "w_norm_q": [float(x) for x in np.nanquantile(wn, [0, .01, .5, .99, 1])],
            "u_norm_q": [float(x) for x in np.nanquantile(un, [0, .01, .5, .99, 1])],
            "n_norm_gt1": int((wn > 1 + 1e-6).sum() + (un > 1 + 1e-6).sum()),
            "n_w_norm_lt_0_7": int((wn < 0.7).sum()),
        }
        # copy bug: identical vectors for distinct units
        W, U, wn = W[fin], U[fin], wn[fin]
        r["n_dup_w_vectors"] = int(pd.Series([w.tobytes() for w in W.astype("float32")]).duplicated().sum())
        r["n_dup_u_vectors"] = int(pd.Series([u.tobytes() for u in U.astype("float32")]).duplicated().sum())
        # near-duplicates: nearest other unit cosine > 0.999999 (via kd-tree on unit vectors)
        from scipy.spatial import cKDTree
        Wn = W / wn[:, None]
        dd, ii = cKDTree(Wn).query(Wn, k=2)
        r["n_near_dup_w"] = int((dd[:, 1] < 1e-6).sum())
        r["cos_w_u_q"] = [float(x) for x in np.quantile(cos_rows(W, U), [0, .01, .5])]
        good = (r["n_missing"] == 0 and r["n_extra"] == 0 and r["n_dup_ids"] == 0 and r["year_col_ok"]
                and r["n_nonfinite_unexplained"] == 0 and r["n_pop_le0_with_coverage"] == 0 and r["max_abs_norm_diff_w"] < 1e-6
                and r["max_abs_norm_diff_u"] < 1e-6 and r["n_norm_gt1"] == 0
                and r["n_dup_w_vectors"] == 0 and r["n_dup_u_vectors"] == 0 and r["n_near_dup_w"] == 0)
        r["pass"] = bool(good)
        ok &= good
        out["per_year"][str(y)] = r
    out["pass"] = bool(ok)
    return out


def temporal_checks(fr):
    ys = sorted(fr)
    res, ok = {}, True
    for a, b in zip(ys[:-1], ys[1:]):
        A = fr[a].set_index("unit_id").sort_index()
        B = fr[b].set_index("unit_id").reindex(A.index)
        for p, cols in (("w", WC), ("u", UC)):
            x, z = A[cols].to_numpy(float), B[cols].to_numpy(float)
            k = np.isfinite(x).all(1) & np.isfinite(z).all(1)
            x, z = x[k], z[k]
            c = cos_rows(x, z)
            ident = int((np.abs(x - z).max(1) == 0).sum())
            res[f"{a}-{b}_{p}"] = {"n_units": int(k.sum()),
                                   "cos_q": [float(v) for v in np.quantile(c, [0, .01, .5, .99, 1])],
                                   "n_identical": ident, "n_cos_lt_0_9": int((c < 0.9).sum())}
            ok &= ident == 0
    return {"pairs": res, "pass": bool(ok)}


def spatial_check(fr, units_ll, seed):
    import geopandas as gpd
    y = max(fr)
    df = fr[y].set_index("unit_id")
    df = df[np.isfinite(df[WC].to_numpy(float)).all(1)]
    g = units_ll[units_ll.unit_id.isin(df.index)].reset_index(drop=True)
    g = gpd.GeoDataFrame(g, geometry="geometry", crs=4326)
    gs = g.copy()
    gs["geometry"] = gs.geometry.buffer(0.001)  # ~100 m: bridge tiny boundary gaps
    pairs = gpd.sjoin(gs[["unit_id", "geometry"]], g[["unit_id", "geometry"]], predicate="intersects")
    pairs = pairs[pairs.unit_id_left < pairs.unit_id_right]
    W = df.loc[:, WC]
    a = W.loc[pairs.unit_id_left.values].to_numpy(float)
    b = W.loc[pairs.unit_id_right.values].to_numpy(float)
    cn = cos_rows(a, b)
    rng = np.random.default_rng(seed)
    n = len(cn)
    i, j = rng.integers(0, len(W), n), rng.integers(0, len(W), n)
    k = i != j
    cr = cos_rows(W.to_numpy(float)[i[k]], W.to_numpy(float)[j[k]])
    return {"year": int(y), "n_neighbour_pairs": int(n),
            "cos_neighbour_mean": float(cn.mean()), "cos_neighbour_median": float(np.median(cn)),
            "cos_random_mean": float(cr.mean()), "cos_random_median": float(np.median(cr)),
            "pass": bool(np.median(cn) > np.median(cr))}


# --------------------------------------------------------------------- sampling
def draw_sample(country, units_ll, years, n, seed):
    import geopandas as gpd
    rng = np.random.default_rng(seed)
    g = units_ll.copy()
    outline = gpd.GeoSeries([g.geometry.union_all()], crs=4326).boundary.iloc[0]
    g["coastal"] = g.geometry.intersects(outline.buffer(0.005))
    if country == "brazil":  # drop land borders (west of the coast's westernmost point)
        g["coastal"] &= g.centroid_lon > -53.3
        g["amazon"] = g.unit_id.str[:2].isin(AMAZON_UF) & (g.area_km2 > g.area_km2.median())
    else:
        g["amazon"] = False
    q1, q2 = g.area_km2.quantile([1 / 3, 2 / 3])
    cap = 25000.0  # km2: EE cost guard for the 100 m reduceRegion
    strata = {
        "small": g[g.area_km2 <= q1],
        "medium": g[(g.area_km2 > q1) & (g.area_km2 <= q2) & ~g.coastal],
        "large": g[(g.area_km2 > q2) & (g.area_km2 <= cap) & ~g.amazon & ~g.coastal],
        "coastal": g[g.coastal & (g.area_km2 <= cap)],
    }
    if country == "brazil":
        strata["amazon"] = g[g.amazon & (g.area_km2 <= cap)]
    names = list(strata)
    per = [n // len(names) + (1 if k < n % len(names) else 0) for k in range(len(names))]
    rows, used = [], set()
    yr = list(rng.permutation(years))
    t = 0
    for name, m in zip(names, per):
        cand = strata[name][~strata[name].unit_id.isin(used)]
        pick = cand.sample(n=min(m, len(cand)), random_state=int(rng.integers(1 << 31)))
        for uid in pick.unit_id:
            used.add(uid)
            rows.append({"unit_id": uid, "stratum": name, "year": int(yr[t % len(yr)])})
            t += 1
    s = pd.DataFrame(rows).merge(g[["unit_id", "area_km2", "adm1", "adm2", "geometry"]], on="unit_id")
    return s


def low_cos_units(fr, n):
    """(unit, year) of the n lowest consecutive-year w_ cosines (earlier year of the pair)."""
    if n <= 0:
        return []
    ys, rows = sorted(fr), []
    for a, b in zip(ys[:-1], ys[1:]):
        A = fr[a].set_index("unit_id").sort_index()
        B = fr[b].set_index("unit_id").reindex(A.index)
        c = pd.Series(cos_rows(A[WC].to_numpy(float), B[WC].to_numpy(float)), A.index).dropna()
        rows += [(uid, a, v) for uid, v in c.items()]
    rows.sort(key=lambda r: r[2])
    out, seen = [], set()
    for uid, y, _ in rows:
        if uid not in seen:
            seen.add(uid)
            out.append((uid, y))
        if len(out) == n:
            break
    return out


def coverage_gap_check(units_ll, gap_ids, years, meter):
    """Count valid AlphaEarth pixels (A00 unmasked, 300 m) per year for units with no stored coverage."""
    import ee
    ee.Initialize(project=os.environ["EE_PROJECT"])
    out = {}
    for uid in gap_ids:
        g = units_ll[units_ll.unit_id == uid].geometry.iloc[0]
        geom = ee.Geometry(json.loads(json.dumps(__import__("shapely.geometry").geometry.mapping(g))), None, False)
        cnt = {}
        for y in years:
            ids = []
            with ee.data.profiling(ids.append):
                v = ee.ImageCollection(COLL).filterDate(f"{y}-01-01", f"{y + 1}-01-01").mosaic().select("A00") \
                    .reduceRegion(ee.Reducer.count(), geom, scale=300, maxPixels=1e9).get("A00").getInfo()
            e, _ = eecu_of(ids)
            meter.eecu += e
            cnt[str(y)] = v
        out[uid] = cnt
    return out


# --------------------------------------------------------------------- EE recompute
class Meter:
    def __init__(self, cap_h):
        self.lock, self.eecu, self.cap = threading.Lock(), 0.0, cap_h * 3600
        self.n_unresolved = 0


def eecu_of(ids):
    import ee
    from pop.features.ee_utils import profile_eecu
    get = ee.ApiFunction.lookup("Profile.getProfiles").call
    tot, ok = 0.0, True
    for pid in ids:
        for k in range(5):
            try:
                tot += profile_eecu(get(ids=[pid]).getInfo())
                break
            except Exception:
                if k == 4:
                    ok = False
                time.sleep(2 + 2 * k)
    return tot, ok


def ee_recompute(sample, meter, workers=6):
    import ee
    import geopandas as gpd
    import shapely.geometry
    ee.Initialize(project=os.environ["EE_PROJECT"])
    p20 = ee.Image(f"{POP}/2020")
    proj_info = p20.select("population_count").projection().getInfo()
    wkt, tr = proj_info["wkt"], proj_info["transform"]
    assert abs(tr[0] - 100) < 1e-9 and abs(tr[4] + 100) < 1e-9, tr
    x0, y0 = tr[2], tr[5]
    proj = ee.Projection(wkt)
    gm = gpd.GeoSeries(sample.geometry.values, crs=4326).to_crs(MOLL)

    def pop_img(year):
        img = None
        for e, t in epoch_mix(year):
            p = ee.Image(f"{POP}/{e}").select("population_count")
            p = p.where(p.lt(0), 0).unmask(0).multiply(t)
            img = p if img is None else img.add(p)
        return img

    def one(k):
        r = sample.iloc[k]
        if meter.eecu > meter.cap:
            return {"unit_id": r.unit_id, "year": int(r.year), "skipped": "budget"}
        geo = json.loads(json.dumps(shapely.geometry.mapping(gm.iloc[k])))
        geom = ee.Geometry(geo, proj, False)
        emb = ee.ImageCollection(COLL).filterDate(f"{r.year}-01-01", f"{r.year + 1}-01-01").mosaic().select(BANDS)
        valid = emb.select("A00").mask().gt(0)
        pop = pop_img(int(r.year))
        wimg = emb.multiply(pop).rename([f"ws_{b}" for b in BANDS]) \
            .addBands(pop.updateMask(valid).rename("p")).addBands(pop.rename("p_all"))
        ids = []

        def call():
            with ee.data.profiling(ids.append):
                a = wimg.reduceRegion(ee.Reducer.sum(), geom, crs=proj, crsTransform=[100, 0, x0, 0, -100, y0],
                                      maxPixels=1e13, tileScale=4).getInfo()
                b = emb.reduceRegion(ee.Reducer.mean(), geom, crs=proj, crsTransform=[300, 0, x0, 0, -300, y0],
                                     maxPixels=1e13, tileScale=4).getInfo()
            return a, b
        for att in range(6):
            try:
                a, b = call()
                break
            except Exception as ex:  # noqa: BLE001
                if att == 5:
                    return {"unit_id": r.unit_id, "year": int(r.year), "error": str(ex)[:300]}
                time.sleep(5 * (att + 1))
        e, okp = eecu_of(ids)
        with meter.lock:
            meter.eecu += e
            meter.n_unresolved += (not okp)
        p = a["p"] or 0.0
        wv = np.array([a[f"ws_{x}"] if a[f"ws_{x}"] is not None else np.nan for x in BANDS], float) / p
        uv = np.array([b[x] if b[x] is not None else np.nan for x in BANDS], float)
        return {"unit_id": r.unit_id, "year": int(r.year), "pop_ee": p, "pop_ee_all": a["p_all"],
                "w_ee": wv, "u_ee": uv, "eecu_s": e}

    with cf.ThreadPoolExecutor(workers) as ex:
        res = list(ex.map(one, range(len(sample))))
    return res


def compare(sample, res, fr):
    rows = []
    for r, s in zip(res, sample.itertuples()):
        base = {"unit_id": s.unit_id, "year": int(s.year), "stratum": s.stratum, "area_km2": float(s.area_km2),
                "name": f"{s.adm1}|{s.adm2}"}
        if "w_ee" not in r:
            rows.append({**base, "status": r.get("error") or r.get("skipped")})
            continue
        st = fr[int(s.year)].set_index("unit_id").loc[s.unit_id]
        w, u = st[WC].to_numpy(float), st[UC].to_numpy(float)
        rows.append({**base, "status": "ok",
                     "cos_w": float(w @ r["w_ee"] / np.linalg.norm(w) / np.linalg.norm(r["w_ee"])),
                     "maxabs_w": float(np.abs(w - r["w_ee"]).max()),
                     "cos_u": float(u @ r["u_ee"] / np.linalg.norm(u) / np.linalg.norm(r["u_ee"])),
                     "maxabs_u": float(np.abs(u - r["u_ee"]).max()),
                     "pop_stored": float(st.pop_sum), "pop_ee": float(r["pop_ee"]),
                     "pop_ratio": float(st.pop_sum / r["pop_ee"]),
                     "pop_ee_all_ratio": float(r["pop_ee"] / r["pop_ee_all"]) if r["pop_ee_all"] else None,
                     "eecu_s": r["eecu_s"]})
    return pd.DataFrame(rows)


# --------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", required=True)
    ap.add_argument("--years", default=None, help="e.g. 2017-2023 or 2017,2019 (default: all per-year files)")
    ap.add_argument("--n-sample", type=int, default=30)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--max-eecu-h", type=float, default=2.7)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--no-ee", action="store_true")
    ap.add_argument("--extra", default="", help="extra targeted unit:year pairs, comma-separated")
    ap.add_argument("--low-cos-extra", type=int, default=3,
                    help="also recompute the N unit-years with the lowest consecutive-year cos (w_)")
    a = ap.parse_args()
    import geopandas as gpd
    c = a.country.lower()
    d = ROOT / "data/interim/alphaearth" / c
    if a.years:
        years = parse_years(a.years)
    else:
        years = sorted(int(p.stem.rsplit("_", 1)[1]) for p in d.glob(f"alphaearth_{c}_[0-9]*.parquet"))
    d, fr = load(c, years)
    u = gpd.read_parquet(UNITS)
    u = u[(u.country == c.upper()) & u.geometry.notna() & ~u.geometry.is_empty].copy()
    u["unit_id"] = u.unit_id.astype(str)
    for y in fr:
        fr[y]["unit_id"] = fr[y].unit_id.astype(str)
    univ = pd.read_csv(UNIVERSE, dtype={"unit_id": str})
    univ = univ[univ.country == c.upper()]
    t0 = time.time()
    out = {"country": c, "years": years, "timestamp_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
           "script": "scripts/features/verify_alphaearth.py", "seed": a.seed,
           "n_units_with_geometry": len(u), "n_universe": len(univ),
           "universe_without_geometry": sorted(set(univ.unit_id) - set(u.unit_id))}
    print("local checks ...", flush=True)
    out["completeness_integrity"] = local_checks(c, fr, u)
    out["temporal"] = temporal_checks(fr)
    print("spatial ...", flush=True)
    out["spatial"] = spatial_check(fr, u, a.seed)
    print(json.dumps({k: out[k]["pass"] for k in ("completeness_integrity", "temporal", "spatial")}), flush=True)
    status = out["completeness_integrity"]["pass"] and out["temporal"]["pass"] and out["spatial"]["pass"]
    if not a.no_ee:
        sample = draw_sample(c, u, years, a.n_sample, a.seed)
        ext = [tuple(x.split(":")) for x in a.extra.split(",") if x]
        ext += low_cos_units(fr, a.low_cos_extra)
        if ext:
            e = pd.DataFrame([{"unit_id": uid, "year": int(y), "stratum": "targeted"} for uid, y in ext])
            e = e.merge(u[["unit_id", "area_km2", "adm1", "adm2", "geometry"]], on="unit_id")
            sample = pd.concat([sample, e], ignore_index=True)
        print(f"EE recompute of {len(sample)} unit-years, {sample.area_km2.sum():.0f} km2 ...", flush=True)
        meter = Meter(a.max_eecu_h)
        gaps = sorted({x for r in out["completeness_integrity"]["per_year"].values()
                       for x in r["nonfinite_units_no_coverage"]})
        if gaps:
            gc = coverage_gap_check(u, gaps, years, meter)
            stored_gap = {uid: [y for y, r in out["completeness_integrity"]["per_year"].items()
                                if uid in r["nonfinite_units_no_coverage"]] for uid in gaps}
            # consistent iff EE has 0 valid pixels in exactly the years stored as empty
            cons = all((gc[uid][y] or 0) == 0 for uid in gaps for y in stored_gap[uid]) and \
                all((gc[uid][str(y)] or 0) > 0 for uid in gaps for y in years if str(y) not in stored_gap[uid])
            out["coverage_gaps"] = {"ee_valid_pixel_count_300m": gc, "stored_empty_years": stored_gap,
                                    "consistent_with_ee": bool(cons), "pass": bool(cons)}
            status = status and cons
            print(json.dumps(out["coverage_gaps"]), flush=True)
        res = ee_recompute(sample, meter, a.workers)
        cmp_ = compare(sample, res, fr)
        cmp_.to_csv(d / "verification_v1_sample.csv", index=False)
        okr = cmp_[cmp_.status == "ok"]
        rec = {"n_sample": len(cmp_), "n_ok": len(okr), "strata": cmp_.stratum.value_counts().to_dict(),
               "years": sorted(cmp_.year.unique().tolist()),
               "min_cos_w": float(okr.cos_w.min()), "median_cos_w": float(okr.cos_w.median()),
               "max_maxabs_w": float(okr.maxabs_w.max()),
               "min_cos_u": float(okr.cos_u.min()), "median_cos_u": float(okr.cos_u.median()),
               "max_maxabs_u": float(okr.maxabs_u.max()),
               "pop_ratio_min": float(okr.pop_ratio.min()), "pop_ratio_max": float(okr.pop_ratio.max()),
               "max_abs_pop_rel_diff": float((okr.pop_ratio - 1).abs().max()),
               "thresholds": {"cos_w_min": COS_W_MIN, "cos_u_min": COS_U_MIN, "pop_ratio_tol": POP_RATIO_TOL},
               "n_eecu_unresolved": meter.n_unresolved,
               "detail_csv": str((d / "verification_v1_sample.csv").relative_to(ROOT))}
        rec["pass"] = bool(len(okr) == len(cmp_) and rec["min_cos_w"] > COS_W_MIN and rec["min_cos_u"] > COS_U_MIN
                           and rec["max_abs_pop_rel_diff"] < POP_RATIO_TOL)
        out["ee_recompute"] = rec
        out["eecu_s"] = meter.eecu
        out["eecu_h"] = meter.eecu / 3600
        status = status and rec["pass"]
        print(cmp_.drop(columns=["name"]).to_string(), flush=True)
    out["status"] = "PASS" if status else "FAIL"
    out["wall_s"] = time.time() - t0
    (d / "verification_v1.json").write_text(json.dumps(out, indent=2, default=float))
    print(json.dumps({k: v for k, v in out.items() if k not in ("completeness_integrity", "temporal")},
                     indent=1, default=float)[:4000])


if __name__ == "__main__":
    sys.exit(main())
