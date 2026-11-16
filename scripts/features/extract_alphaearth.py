"""Production AlphaEarth extraction (Brazil, Colombia, Peru, Taiwan): region x year chunks, resumable,
budget-guarded, parallel.

    python scripts/features/extract_alphaearth.py run [--countries brazil colombia ...] [--procs 3 --workers 12]
    python scripts/features/extract_alphaearth.py detcheck --country brazil --year 2023 --region SE
    python scripts/features/extract_alphaearth.py verify --country brazil --year 2023 --states DF SE AL
    python scripts/features/extract_alphaearth.py dtype-test
    python scripts/features/extract_alphaearth.py assemble
    python scripts/features/extract_alphaearth.py status

Outputs per country (data/interim/alphaearth/<country>/): chunks/<year>/<region>.parquet (raw sums) + .done,
ledger.csv (one row per chunk / verification), alphaearth_<country>_<year>.parquet,
alphaearth_<country>.parquet (all completed years). Region = Brazilian UF (first 2 digits of unit_id) or the
adm1 name (slugged) elsewhere. See docs/features/alphaearth_extraction.md.
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import multiprocessing as mp
import os
import re
import shutil
import sys
import time
from collections import deque
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

from pop.features import alphaearth as ae
from pop.features import alphaearth_extract as X

ROOT = Path("data/interim/alphaearth")
UNITS = "data/interim/boundaries/opendengue_units_v1.parquet"
# queue order: countries in this order, years newest first within each (Brazil 2024 last)
COUNTRIES = {
    "brazil": [2023, 2022, 2021, 2020, 2019, 2018, 2017, 2024],
    "colombia": [2023, 2021, 2020, 2019, 2018, 2017],
    "peru": [2023, 2022, 2021, 2020, 2019, 2018, 2017],
    "taiwan": [2023, 2022, 2021, 2020, 2019, 2018, 2017],
}
YEARS = COUNTRIES["brazil"]  # backwards compatibility
CAP_H = 800.0  # EECU-h per calendar month (UTC); Contributor tier = 1,000
OTHER_H = {"2026-11": 25.0}  # EECU-h used by other work this month (not in the ledgers)
LEDGER_COLS = ["chunk", "state", "year", "started", "finished", "eecu_s", "eecu_w_s", "eecu_u_s", "eecu_ghsl_s",
               "eecu_source", "n_req_w", "n_req_u", "n_profile_missing", "bytes", "wall_s", "units",
               "state_km2", "fetched_km2_w", "fetched_km2_u", "dtype", "n_retries", "n_retries_429", "workers"]


def log(msg: str) -> None:
    print(f"{pd.Timestamp.now(tz='UTC'):%Y-%m-%d %H:%M:%S} {msg}", flush=True)


def out_dir(country: str) -> Path:
    return ROOT / country


def slug(s: str) -> str:
    return re.sub(r"[^A-Z0-9]+", "_", str(s).upper()).strip("_")


_UNITS: dict = {}


def units_ll(country: str = "brazil", quiet: bool = True) -> gpd.GeoDataFrame:
    """Units of one country with a ``uf`` (region key) column; units without geometry are dropped (logged)."""
    if country in _UNITS:
        return _UNITS[country]
    g = gpd.read_parquet(UNITS)
    g = g[g.country == country.upper()].reset_index(drop=True)
    g["unit_id"] = g.unit_id.astype(str)
    bad = g.geometry.isna() | g.geometry.is_empty
    if bad.any() and not quiet:
        log(f"SKIP_NO_GEOMETRY {country}: {g.loc[bad, 'unit_id'].tolist()}")
    g = g[~bad].reset_index(drop=True)
    if country == "brazil":
        g["uf"] = g.unit_id.str[:2].map(X.UF)
        assert g.uf.notna().all() and len(g) == 5517, len(g)
    else:
        g["uf"] = g.adm1.map(slug)
        assert g.groupby("uf").adm1.nunique().max() == 1
    _UNITS[country] = g
    return g


def state_order(g) -> list[str]:
    return g.groupby("uf").area_km2.sum().sort_values().index.tolist()  # small regions first


def ledger(country: str = "brazil") -> pd.DataFrame:
    p = out_dir(country) / "ledger.csv"
    return pd.read_csv(p, dtype={"chunk": str, "state": str}) if p.exists() else pd.DataFrame(columns=LEDGER_COLS)


def all_ledgers() -> pd.DataFrame:
    fr = [ledger(c) for c in COUNTRIES if (out_dir(c) / "ledger.csv").exists()]
    return pd.concat(fr, ignore_index=True).reindex(columns=LEDGER_COLS) if fr else pd.DataFrame(columns=LEDGER_COLS)


def ledger_add(rec: dict, country: str = "brazil") -> None:
    p = out_dir(country) / "ledger.csv"
    p.parent.mkdir(parents=True, exist_ok=True)
    if p.exists() and pd.read_csv(p, nrows=0).columns.tolist() != LEDGER_COLS:  # schema upgrade: add columns
        L = pd.read_csv(p, dtype={"chunk": str, "state": str})
        L.reindex(columns=LEDGER_COLS).to_csv(p, index=False)
    pd.DataFrame([rec], columns=LEDGER_COLS).to_csv(p, mode="a", header=not p.exists(), index=False)


def chunks_of(L: pd.DataFrame) -> pd.DataFrame:
    return L[L.chunk.astype(str).str.match(r"^\d{4}_")] if len(L) else L


def rates(L: pd.DataFrame) -> dict:
    c = chunks_of(L)
    r = {"w": 0.01, "u": 0.002, "state": 0.005}
    if len(c) and c.fetched_km2_w.sum() > 0:
        r["w"] = c.eecu_w_s.sum() / c.fetched_km2_w.sum()
    if len(c) and c.fetched_km2_u.sum() > 0:
        r["u"] = c.eecu_u_s.sum() / c.fetched_km2_u.sum()
    if len(c):
        r["state"] = c.eecu_s.sum() / c.state_km2.sum()
    return r


def rates_for(country: str) -> dict:
    L = ledger(country)
    return rates(L if len(chunks_of(L)) else all_ledgers())


def pop_for(uf: str, gm, year: int, block_w: int, out: Path, log=log):
    """Interpolated GHSL people on the region's 100 m window (cached per region x epoch)."""
    win = X.grid_window(gm.total_bounds, X.RES_W, block_w)
    c0, r0, nx, ny = win
    pop = np.zeros((ny, nx), "float32")
    eecu = 0.0
    (out / "ghsl").mkdir(parents=True, exist_ok=True)
    for e, t in X.epoch_weights(year):
        f = out / "ghsl" / f"{uf}_{e}_b{block_w}.npz"
        if f.exists():
            z = np.load(f)
            assert tuple(z["win"]) == win
            a = np.zeros(nx * ny, "float32")
            a[z["idx"]] = z["val"]
            a = a.reshape(ny, nx)
        else:
            a, ee_s, _ = X.fetch_ghsl(e, c0, r0, nx, ny)
            eecu += ee_s
            idx = np.flatnonzero(a)
            tmp = f.with_name(f"{f.stem}.{os.getpid()}.tmp.npz")
            np.savez(tmp, win=np.array(win), idx=idx, val=a.ravel()[idx])
            os.replace(tmp, f)  # atomic (parallel chunks may share a region)
            log(f"  GHSL {uf} {e}: {nx}x{ny} px, {a.sum():,.0f} people, eecu={ee_s:.1f}")
        pop += np.float32(t) * a
    return pop, win, eecu


def do_chunk(country: str, uf: str, year: int, opts: dict, r: dict, out: Path | None = None) -> dict:
    """Run one chunk, write chunks/<year>/<uf>.parquet under ``out``; returns the ledger record
    (the caller appends it to the ledger and writes the .done marker)."""
    out = out or out_dir(country)
    g = units_ll(country)
    gs = g[g.uf == uf].reset_index(drop=True)
    gm = gs.to_crs(X.MOLL)
    name = f"{year}_{uf}"
    clog = lambda m: log(f"[{country} {name}] {m.strip()}")  # noqa: E731
    t0 = time.time()
    started = pd.Timestamp.now(tz="UTC").isoformat()
    pop, win, eecu_g = pop_for(uf, gm, year, opts["block_w"], out, clog)
    sums, st = X.run_chunk(gm[["unit_id", "geometry"]], year, pop, win, opts["block_w"], opts["block_u"],
                           opts["dtype"], opts["workers"], clog, r["w"], r["u"])
    d = out / "chunks" / str(year)
    d.mkdir(parents=True, exist_ok=True)
    tmp = d / f"{uf}.{os.getpid()}.tmp.parquet"
    sums.to_parquet(tmp, index=False)
    os.replace(tmp, d / f"{uf}.parquet")
    eecu = st.eecu_w + st.eecu_u + eecu_g
    return {"chunk": name, "state": uf, "year": year, "started": started,
            "finished": pd.Timestamp.now(tz="UTC").isoformat(), "eecu_s": round(eecu, 2),
            "eecu_w_s": round(st.eecu_w, 2), "eecu_u_s": round(st.eecu_u, 2), "eecu_ghsl_s": round(eecu_g, 2),
            "eecu_source": "profile" if st.prof_missing == 0 else f"profile+estimate({st.est_missing_eecu:.0f}s)",
            "n_req_w": st.req_w, "n_req_u": st.req_u, "n_profile_missing": st.prof_missing, "bytes": st.bytes,
            "wall_s": round(time.time() - t0, 1), "units": len(gs), "state_km2": round(gs.area_km2.sum(), 1),
            "fetched_km2_w": round(st.px_w * 0.01, 1), "fetched_km2_u": round(st.px_u * 0.09, 1),
            "dtype": opts["dtype"], "n_retries": st.retries, "n_retries_429": st.retries_429,
            "workers": opts["workers"]}


def _child_init() -> None:
    ae.init()


def _child(country, uf, year, opts, r):
    return do_chunk(country, uf, year, opts, r)


def assemble_year(year: int, ufs, country: str = "brazil") -> bool:
    out = out_dir(country)
    d = out / "chunks" / str(year)
    if not all((d / f"{u}.done").exists() for u in ufs):
        return False
    s = pd.concat([pd.read_parquet(d / f"{u}.parquet") for u in ufs], ignore_index=True)
    m = X.sums_to_means(s)
    m.to_parquet(out / f"alphaearth_{country}_{year}.parquet", index=False)
    log(f"ASSEMBLED {country} {year}: {len(m)} units, nonfinite rows="
        f"{int((~np.isfinite(m[X.WCOLS + X.UCOLS])).any(axis=1).sum())}")
    return True


def assemble_all(country: str = "brazil") -> None:
    ufs = state_order(units_ll(country))
    fr = []
    for y in sorted(COUNTRIES[country]):
        if assemble_year(y, ufs, country):
            fr.append(pd.read_parquet(out_dir(country) / f"alphaearth_{country}_{y}.parquet"))
    if fr:
        pd.concat(fr, ignore_index=True).to_parquet(out_dir(country) / f"alphaearth_{country}.parquet", index=False)
        log(f"COMBINED {country} years={[int(f.year.iloc[0]) for f in fr]}")


def month_used_h(month: str) -> float:
    return X.budget_state(all_ledgers(), month, CAP_H, OTHER_H)["used_h"]


def cmd_run(args) -> int:
    ae.init()
    opts = {k: getattr(args, k) for k in ("block_w", "block_u", "dtype", "workers")}
    queue = deque()
    for country in args.countries:
        g = units_ll(country, quiet=False)
        ufs = args.states or state_order(g)
        km2 = g.groupby("uf").area_km2.sum()
        for y in (args.years or COUNTRIES[country]):
            for uf in ufs:
                if not (out_dir(country) / "chunks" / str(y) / f"{uf}.done").exists():
                    queue.append((country, uf, y, float(km2[uf])))
    log(f"RUN procs={args.procs} workers={args.workers} cap={args.cap_h}h/month queue={len(queue)} chunks")
    attempts: dict = {}
    failed: list = []
    inflight: dict = {}
    paused = False
    ctx = mp.get_context("spawn")
    with cf.ProcessPoolExecutor(args.procs, mp_context=ctx, initializer=_child_init) as pool:
        while queue or inflight:
            while queue and len(inflight) < args.procs and not paused:
                country, uf, y, km2 = queue[0]
                r = rates_for(country)
                month = pd.Timestamp.now(tz="UTC").strftime("%Y-%m")
                used = month_used_h(month)
                pending_h = sum(t[4] for t in inflight.values())
                est_h = km2 * r["state"] / 3600
                if used + pending_h + est_h > args.cap_h:
                    log(f"BUDGET_PAUSE month={month} used={used:.2f}h inflight_est={pending_h:.2f}h "
                        f"next={country} {y}_{uf} est={est_h:.2f}h cap={args.cap_h}h")
                    paused = True
                    break
                queue.popleft()
                log(f"START {country} {y}_{uf} (month used {used:.2f}/{args.cap_h}h, est {est_h:.2f}h)")
                fut = pool.submit(_child, country, uf, y, opts, r)
                inflight[fut] = (country, uf, y, km2, est_h)
            if not inflight:
                break
            done, _ = cf.wait(list(inflight), return_when=cf.FIRST_COMPLETED)
            for fut in done:
                country, uf, y, km2, est_h = inflight.pop(fut)
                try:
                    rec = fut.result()
                except Exception as e:
                    k = (country, uf, y)
                    attempts[k] = attempts.get(k, 0) + 1
                    log(f"CHUNK_FAILED {country} {y}_{uf} attempt {attempts[k]}: {str(e)[:300]}")
                    if attempts[k] < args.max_attempts:
                        queue.append((country, uf, y, km2))  # retry at the end of the queue
                    else:
                        failed.append(f"{country} {y}_{uf}")
                    continue
                ledger_add(rec, country)
                d = out_dir(country) / "chunks" / str(y)
                (d / f"{uf}.done").write_text(json.dumps(rec))
                log(f"DONE {country} {rec['chunk']} eecu={rec['eecu_s']:.0f}s "
                    f"({rec['eecu_s'] / max(rec['state_km2'], 1e-9):.4f}/km2) w={rec['eecu_w_s']:.0f} "
                    f"u={rec['eecu_u_s']:.0f} ghsl={rec['eecu_ghsl_s']:.0f} req={rec['n_req_w']}+{rec['n_req_u']} "
                    f"retries={rec['n_retries']} (429-like {rec['n_retries_429']}) {rec['bytes'] / 2**20:.0f}MB "
                    f"{rec['wall_s']:.0f}s units={rec['units']}")
                if args.states is None:
                    ufs = state_order(units_ll(country))
                    if assemble_year(y, ufs, country) and all(
                            (out_dir(country) / "chunks" / str(yy) / f"{u}.done").exists()
                            for yy in COUNTRIES[country] for u in ufs):
                        assemble_all(country)
    if args.states is None:
        for country in args.countries:
            assemble_all(country)
    if failed:
        log(f"FAILED_CHUNKS {failed}")
        return 1
    if paused:
        return 3
    log("ALL_DONE")
    return 0


def compare_ref(g, m: pd.DataFrame, ids: list, year: int) -> dict:
    gl = g.set_index("unit_id").loc[ids]
    ref, eecu = X.ee_reference(gl.geometry.values, ids, year, X.epoch_weights(year))
    ref = ref.set_index("unit_id").loc[ids]
    loc = m.set_index("unit_id").loc[ids]
    W = ref[[f"ws_{b}" for b in ae.BANDS]].to_numpy(float) / ref.pop_sum.to_numpy(float)[:, None]
    U = ref[[f"us_{b}" for b in ae.BANDS]].to_numpy(float) / ref.cnt.to_numpy(float)[:, None]
    return {"units": ids, "cos_w": ae.cosine(W, loc[X.WCOLS].to_numpy(float)).round(8).tolist(),
            "cos_u_300m_vs_100m": ae.cosine(U, loc[X.UCOLS].to_numpy(float)).round(8).tolist(),
            "pop_ratio": (loc.pop_sum / ref.pop_sum).round(5).tolist(), "eecu_s": round(eecu, 1)}


def cmd_detcheck(args) -> None:
    """Re-extract a finished chunk into a temp dir with the current (parallel) code from scratch (fresh
    GHSL too) and compare with the stored chunk; plus 3 units vs a fresh EE reduceRegions at 100 m."""
    ae.init()
    c, uf, y = args.country, args.region, args.year
    tmp = ROOT / "_detcheck" / f"{c}_{y}_{uf}_w{args.workers}"
    shutil.rmtree(tmp, ignore_errors=True)
    opts = {k: getattr(args, k) for k in ("block_w", "block_u", "dtype", "workers")}
    rec = do_chunk(c, uf, y, opts, rates_for(c), out=tmp)
    old = pd.read_parquet(out_dir(c) / "chunks" / str(y) / f"{uf}.parquet")
    new = pd.read_parquet(tmp / "chunks" / str(y) / f"{uf}.parquet")
    mo, mn = X.sums_to_means(old).set_index("unit_id"), X.sums_to_means(new).set_index("unit_id")
    mn = mn.loc[mo.index]
    cols = X.WCOLS + X.UCOLS + ["pop_sum"]
    diff = np.abs(mo[cols].to_numpy(float) - mn[cols].to_numpy(float))
    rawd = np.abs(old.drop(columns=["unit_id", "year"]).to_numpy(float)
                  - new.set_index("unit_id").loc[old.unit_id].reset_index().drop(columns=["unit_id", "year"]).to_numpy(float))
    rep = {"chunk": f"{c} {y}_{uf}", "units": len(mo), "workers": args.workers,
           "max_abs_diff_w_u": float(np.nanmax(diff[:, :-1])), "max_abs_diff_pop_sum": float(np.nanmax(diff[:, -1])),
           "max_abs_diff_raw_sums": float(np.nanmax(rawd)), "bitwise_equal_raw": float(np.nanmax(rawd)) == 0.0,
           "wall_s": rec["wall_s"], "req": rec["n_req_w"] + rec["n_req_u"], "retries": rec["n_retries"],
           "eecu_s": rec["eecu_s"]}
    rep["pass"] = rep["max_abs_diff_w_u"] <= 1e-6 and rep["max_abs_diff_pop_sum"] <= 1e-6
    ids = mn.sample(3, random_state=1).index.tolist()
    rep["ee_ref"] = compare_ref(units_ll(c), mn.reset_index(), ids, y)
    rep["ee_ref_pass"] = min(rep["ee_ref"]["cos_w"]) > 0.9999
    ledger_add({"chunk": f"detcheck_{y}_{uf}", "state": "", "year": y, "started": rec["started"],
                "finished": pd.Timestamp.now(tz="UTC").isoformat(),
                "eecu_s": round(rec["eecu_s"] + rep["ee_ref"]["eecu_s"], 2), "eecu_source": "profile",
                "units": rec["units"], "workers": args.workers}, c)
    print(json.dumps(rep, indent=1))
    (out_dir(c) / f"detcheck_{y}_{uf}.json").write_text(json.dumps(rep, indent=1))


def cmd_verify(args) -> None:
    ae.init()
    c = args.country
    g = units_ll(c)
    rep = {}
    s = pd.concat([pd.read_parquet(out_dir(c) / "chunks" / str(args.year) / f"{u}.parquet") for u in args.states])
    m = X.sums_to_means(s)
    vals = m[X.WCOLS + X.UCOLS].to_numpy()
    n_exp = int(g.uf.isin(args.states).sum())
    rep["a_units"] = {"expected": n_exp, "rows": len(m), "all_finite_64x2": bool(np.isfinite(vals).all()),
                      "w_fallback": int(m.w_fallback.sum())}
    rep["b_norms"] = {k: {"min": float(m[k].min()), "median": float(m[k].median()), "max": float(m[k].max())}
                      for k in ("w_norm", "u_norm")}
    rng = np.random.default_rng(1)
    pick = rng.choice(len(m), size=min(5, len(m)), replace=False)
    ids = m.unit_id.iloc[pick].tolist()
    rep["c_cosine_vs_ee100m"] = compare_ref(g, m, ids, args.year)
    eecu = rep["c_cosine_vs_ee100m"]["eecu_s"]
    tag = f"verify_{args.year}_{'-'.join(args.states)}"
    ledger_add({"chunk": tag, "state": "", "year": args.year,
                "started": pd.Timestamp.now(tz="UTC").isoformat(), "finished": pd.Timestamp.now(tz="UTC").isoformat(),
                "eecu_s": round(eecu, 2), "eecu_source": "profile", "units": len(ids)}, c)
    ch = chunks_of(ledger(c))
    rate = ch.eecu_s.sum() / ch.state_km2.sum()
    rep["d_cost"] = {"eecu_per_state_km2": round(rate, 5),
                     "w_per_fetched_km2": round(ch.eecu_w_s.sum() / max(ch.fetched_km2_w.sum(), 1), 5),
                     "u_per_fetched_km2": round(ch.eecu_u_s.sum() / max(ch.fetched_km2_u.sum(), 1), 5)}
    per_year_h = g.area_km2.sum() * rate / 3600
    rep["e_projection"] = {"km2": round(g.area_km2.sum()), "per_year_eecu_h": round(per_year_h, 1)}
    print(json.dumps(rep, indent=1))
    (out_dir(c) / f"{tag}.json").write_text(json.dumps(rep, indent=1))


def cmd_dtype_test(args) -> None:
    """Same blocks fetched as float32 and int16: EECU, bytes, max abs error."""
    ae.init()
    res = []
    from pyproj import Transformer
    tf = Transformer.from_crs("EPSG:4326", X.MOLL, always_xy=True)
    for lon, lat in [(-47.9, -15.8), (-37.1, -10.9), (-60.0, -3.1)]:  # Brasilia, Aracaju, Manaus
        x, y = tf.transform(lon, lat)
        c0, r0, nx, ny = int((x - X.X0) // 100), int((X.Y0 - y) // 100), 128, 128
        A, e1, b1, _ = X.fetch_block(X.emb_image(2023, "float32"), c0, r0, nx, ny, 100, "float32")
        B, e2, b2, _ = X.fetch_block(X.emb_image(2023, "int16"), c0, r0, nx, ny, 100, "int16")
        ok = np.isfinite(A) & np.isfinite(B)
        res.append({"block": [c0, r0], "eecu_f32": e1, "eecu_i16": e2, "bytes_f32": b1, "bytes_i16": b2,
                    "max_abs_err": float(np.abs(A - B)[ok].max()) if ok.any() else None,
                    "valid_frac": float(ok[0].mean())})
    print(json.dumps(res, indent=1))
    ledger_add({"chunk": "dtype_test", "year": 2023, "started": pd.Timestamp.now(tz="UTC").isoformat(),
                "finished": pd.Timestamp.now(tz="UTC").isoformat(),
                "eecu_s": round(sum(r["eecu_f32"] + r["eecu_i16"] for r in res), 2), "eecu_source": "profile"})


def cmd_status(args) -> None:
    month = pd.Timestamp.now(tz="UTC").strftime("%Y-%m")
    LA = all_ledgers()
    print(f"month {month}: {month_used_h(month):.2f}/{CAP_H} EECU-h (incl. {OTHER_H.get(month, 0)} h other work); "
          f"all ledgers {LA.eecu_s.sum() / 3600:.2f} h")
    allc = chunks_of(LA)
    now = pd.Timestamp.now(tz="UTC")
    rem_km2 = 0.0
    for c in COUNTRIES:
        g = units_ll(c)
        km2 = g.groupby("uf").area_km2.sum()
        done = [(y, u) for y in COUNTRIES[c] for u in km2.index
                if (out_dir(c) / "chunks" / str(y) / f"{u}.done").exists()]
        tot = len(km2) * len(COUNTRIES[c])
        left = km2.sum() * len(COUNTRIES[c]) - sum(km2[u] for _, u in done)
        rem_km2 += left
        yrs = [y for y in COUNTRIES[c] if (out_dir(c) / f"alphaearth_{c}_{y}.parquet").exists()]
        print(f"{c:9s} chunks {len(done):4d}/{tot:4d}  years assembled {sorted(yrs)}  remaining {left / 1e6:.2f} M km2")
    if len(allc):
        fin = pd.to_datetime(allc.finished, utc=True, format="ISO8601")
        rec = allc[fin > now - pd.Timedelta(hours=1)]
        rate = allc.eecu_s.sum() / allc.state_km2.sum()
        print(f"rate {rate:.5f} EECU-s/state-km2; remaining est {rem_km2 * rate / 3600:.1f} EECU-h")
        if len(rec):
            kph = rec.state_km2.sum()  # km2 finished in the last hour
            eta = now + pd.Timedelta(hours=rem_km2 / kph)
            print(f"last hour: {len(rec)} chunks, {kph / 1e6:.2f} M km2/h, {rec.eecu_s.sum() / 3600:.1f} EECU-h/h, "
                  f"retries {int(rec.n_retries.fillna(0).sum())}; naive ETA {eta:%Y-%m-%d %H:%M} UTC")
        cols = ["chunk", "eecu_s", "wall_s", "units", "n_retries", "finished"]
        print(allc.tail(6).reindex(columns=cols).to_string(index=False))


def main() -> int:
    global CAP_H
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["run", "detcheck", "verify", "dtype-test", "assemble", "status"])
    ap.add_argument("--countries", nargs="+", default=list(COUNTRIES), choices=list(COUNTRIES))
    ap.add_argument("--country", default="brazil", choices=list(COUNTRIES))
    ap.add_argument("--years", type=int, nargs="+", default=None)
    ap.add_argument("--year", type=int, default=2023)
    ap.add_argument("--states", nargs="+", default=None)
    ap.add_argument("--region", default="SE")
    ap.add_argument("--dtype", default="float32", choices=["float32", "int16"])
    ap.add_argument("--block-w", type=int, default=128)
    ap.add_argument("--block-u", type=int, default=256)
    ap.add_argument("--workers", type=int, default=16, help="concurrent computePixels requests per chunk")
    ap.add_argument("--procs", type=int, default=3, help="chunks in parallel (processes)")
    ap.add_argument("--max-attempts", type=int, default=3)
    ap.add_argument("--cap-h", type=float, default=CAP_H)
    a = ap.parse_args()
    CAP_H = a.cap_h
    if a.cmd == "run":
        return cmd_run(a)
    if a.cmd == "detcheck":
        cmd_detcheck(a)
    elif a.cmd == "verify":
        cmd_verify(a)
    elif a.cmd == "dtype-test":
        cmd_dtype_test(a)
    elif a.cmd == "assemble":
        ae.init()
        for c in a.countries:
            assemble_all(c)
    else:
        cmd_status(a)
    return 0


if __name__ == "__main__":
    sys.exit(main())
