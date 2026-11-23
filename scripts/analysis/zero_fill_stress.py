#!/usr/bin/env python
"""R5 zero-fill stress test: what if some zero-filled weeks held a few unreported cases?

Scoring only: no model is refitted. The stored quantile forecasts of the 14 primary comparisons
are rescored against perturbed targets.

Usage (repo root, after `source env.sh`):
    nice -n 19 python scripts/analysis/zero_fill_stress.py [--stage all|precompute|cells|report]
        [--workers-pre 10] [--workers-cells 4] [--R 20] [--grid 0.5,1,2,2.1,5,10] [--ks 1,3]
        [--tmp tmp/r5] [--out docs/results/review]

Method
  1. precompute: for every run dir of the 14 primary comparisons (configs/primary_cells.yaml;
     3-seed manifest), the chunk forecast files at the primary horizons are read (median +
     deciles) and the log-scale WIS (pop.eval.scoring.wis_interval, log1p) is computed at the
     observed count and at y = 0, 1 and 3 cases. Check: WIS at the observed count reproduces the
     stored wis_log on every row. Rows with a zero target are kept in tmp/r5/wis_alt/<run>.parquet.
  2. cells: the primary scored rows are built exactly as the results kit builds them
     (estimands_report.load_cell + exclusions_v2 + origin-year row filter + primary horizons;
     rk_compute helpers). The same pipeline is then run with the y = k scores served in place of
     wis_log, which gives every row's gains (common-seed rule) had its target been k cases.
     Candidates = district-weeks (unit, target week) whose target was zero-filled (absent from the
     source; weeks the source listed as 0 are never touched). For draw r one random permutation of
     a comparison's candidates is drawn (numpy default_rng([20261122, crc32(cell id), r])); share
     s takes its first round(s * N) district-weeks, so the draws are nested across s and identical
     for k = 1 and 3, for all four models, every seed and both horizons of a target week.
  3. Each draw's gain series is the primary one (cross-unit mean per horizon and target week,
     then the unweighted mean over the horizons present in the week: pop.eval.stats.
     pooled_horizon_series) and is tested with the primary test (pop.eval.stats.ewc_inference =
     DM/EWC + HLN). Only the selected rows change, so the per-(horizon, week) means are updated by
     a weighted sum of the row changes. % = 100 * gain / unperturbed WIS(L3) (fixed denominator).
     Holm over the 14 comparisons within each draw index (pop.eval.stats.holm).
  Checks: s = 0 reproduces docs/results/tables/T1_primary_family.csv; the y = 0 rescoring
  reproduces the stored gains on every candidate row; two draws per comparison are recomputed with
  pop.eval.estimands.infer_estimand on an explicitly perturbed frame.
Outputs: docs/results/review/R5_zero_fill_stress.{csv,md}; scratch (draws, checks) in tmp/r5/.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import warnings
import zlib
from concurrent.futures import ProcessPoolExecutor, as_completed
from contextlib import contextmanager
from multiprocessing import get_context
from pathlib import Path

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_MAX_THREADS"):
    os.environ[_v] = "1"

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "analysis"))
sys.path.insert(0, str(ROOT / "scripts" / "run"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import pyarrow.parquet as pq  # noqa: E402

import estimands_report as ER  # noqa: E402
import rk_cells as C  # noqa: E402
import rk_compute as K  # noqa: E402
from review_sens import make_reader  # noqa: E402

from pop.eval import scoring  # noqa: E402
from pop.eval.estimands import infer_estimand  # noqa: E402
from pop.eval.stats import ewc_inference, holm, pooled_horizon_series  # noqa: E402

KEYS = list(ER.KEYS)                     # test_year, unit_id, origin_week, target_week, horizon
QLEVELS = np.asarray(scoring.PRIMARY_QUANTILES, float)
ALT_Y = {0: "w_y0", 1: "w_y1", 3: "w_y3"}
EST = ("G_excess", "G_emb")             # G_excess primary
PREFIX = {"G_excess": "exc", "G_emb": "emb"}
SEED = 20261122
BENCH = 2.1                              # Brazil 2023: 2.1% of filled weeks held a probable case
XDIR = Path("data/processed/exclusions_v2")
EXCL = {"exclude_units": str(XDIR / "no_geometry_units.csv"),
        "exclude_weeks": str(XDIR / "incomplete_weeks.csv"), "late_entry": None,
        "week_actions": ("exclude",), "unit_weeks": str(XDIR / "unit_week_exclusions.csv")}


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def _norm(df: pd.DataFrame) -> pd.DataFrame:
    """Key dtypes used for every merge in this script."""
    df["test_year"] = df.test_year.astype(int)
    df["unit_id"] = df.unit_id.astype(str)
    df["origin_week"] = pd.to_datetime(df.origin_week)      # as estimands_report.read_scores
    df["target_week"] = pd.to_datetime(df.target_week)
    df["horizon"] = df.horizon.astype(int)
    if "seed" in df:
        df["seed"] = df.seed.astype(int)
    return df


# ============================================================================ 1. precompute
def alt_path(tmp, d) -> Path:
    return Path(tmp) / "wis_alt" / f"{Path(d).name}.parquet"


def precompute_dir(job) -> dict:
    d, tmp, horizons = job
    os.chdir(ROOT)
    d = Path(d)
    out = alt_path(tmp, d)
    ckf = out.with_suffix(".check.json")
    sc_path = d / "scores.parquet"
    if out.exists() and ckf.exists() and out.stat().st_mtime > sc_path.stat().st_mtime:
        return json.loads(ckf.read_text())
    t0 = time.time()
    k = len(QLEVELS)
    files = sorted(f for f in (d / "chunks").glob("*.forecasts.parquet")
                   if any(f.name.endswith(f"__h{h}.forecasts.parquet") for h in horizons))
    chk = {"dir": str(d), "n_chunks": len(files), "n_forecasts": 0, "n_zero_target": 0,
           "wis_obs_maxdiff": 0.0, "nan_pattern_mismatch": 0, "n_nan_wis": 0}
    parts = []
    for f in files:
        fc = pd.read_parquet(f, columns=KEYS + ["seed", "quantile", "value"])
        n = len(fc)
        if n % k or not np.allclose(fc["quantile"].to_numpy(float).reshape(-1, k), QLEVELS[None, :]):
            raise ValueError(f"{f}: quantile pattern is not 9 consecutive levels per forecast")
        for c in ("test_year", "origin_week", "target_week", "horizon", "seed"):
            a = fc[c].to_numpy().reshape(-1, k)
            if not (a == a[:, :1]).all():
                raise ValueError(f"{f}: {c} varies within a forecast block")
        u = pd.factorize(fc.unit_id)[0].reshape(-1, k)
        if not (u == u[:, :1]).all():
            raise ValueError(f"{f}: unit_id varies within a forecast block")
        V = fc["value"].to_numpy(float).reshape(-1, k)
        keys = _norm(fc.iloc[::k][KEYS + ["seed"]].reset_index(drop=True))
        del fc
        sf = f.with_name(f.name.replace(".forecasts.", ".scores."))
        sc = _norm(pd.read_parquet(sf, columns=KEYS + ["seed", "cases", "wis_log"]))
        m = keys.merge(sc, on=KEYS + ["seed"], how="left", validate="one_to_one", indicator=True)
        if len(sc) != len(keys) or (m["_merge"] != "both").any():
            raise ValueError(f"{f}: forecast and score rows differ")
        y = m.cases.to_numpy(float)
        wl = m.wis_log.to_numpy(float)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            w_obs = scoring.wis_interval(y, QLEVELS, V, log1p=True)
            keep = y == 0
            Vk = V[keep]
            alt = {c: scoring.wis_interval(np.full(len(Vk), float(yv)), QLEVELS, Vk, log1p=True)
                   for yv, c in ALT_Y.items()}
        nan_s = np.isnan(wl)
        chk["nan_pattern_mismatch"] += int((np.isnan(w_obs) != nan_s).sum())
        chk["n_nan_wis"] += int(nan_s.sum())
        ok = ~nan_s & ~np.isnan(w_obs)
        if ok.any():
            chk["wis_obs_maxdiff"] = max(chk["wis_obs_maxdiff"], float(np.max(np.abs(w_obs[ok] - wl[ok]))))
        rows = m.loc[keep, KEYS + ["seed", "cases"]].reset_index(drop=True)
        for c, v in alt.items():
            rows[c] = np.where(nan_s[keep], np.nan, v)
        chk["n_forecasts"] += len(V)
        chk["n_zero_target"] += int(keep.sum())
        parts.append(rows)
    df = pd.concat(parts, ignore_index=True)
    n_sc = pq.read_table(sc_path, columns=["horizon"],
                         filters=[("horizon", "in", [int(h) for h in horizons])]).num_rows
    chk["n_scores_rows"] = int(n_sc)
    if n_sc != chk["n_forecasts"]:
        raise ValueError(f"{d}: {chk['n_forecasts']} chunk forecasts vs {n_sc} rows in scores.parquet")
    if df.duplicated(KEYS + ["seed"]).any():
        raise ValueError(f"{d}: duplicated (key, seed) rows")
    out.parent.mkdir(parents=True, exist_ok=True)
    tmpf = out.with_suffix(".tmp.parquet")
    df.to_parquet(tmpf, index=False)
    os.replace(tmpf, out)
    chk["seconds"] = round(time.time() - t0, 1)
    ckf.write_text(json.dumps(chk, indent=1))
    return chk


# ============================================================================ 2. cells
@contextmanager
def served_scores(reader):
    orig = ER.read_scores
    ER.read_scores = reader
    try:
        yield
    finally:
        ER.read_scores = orig


def alt_reader(tmp, col, horizons):
    """estimands_report.read_scores replacement serving WIS at y = k (zero-target rows only)."""
    def _read(dirs, cols=("wis_log", "cases")):
        out = []
        for d in map(Path, dirs):
            s = pd.read_parquet(alt_path(tmp, d), columns=KEYS + ["seed", "cases", col],
                                filters=[("horizon", "in", [int(h) for h in horizons])])
            s = s.rename(columns={col: "wis_log"})
            s["label"] = d.name
            s["dir"] = d.name
            out.append(_norm(s))
        return pd.concat(out, ignore_index=True)
    return _read


def kit_rows(cell, reader):
    """Primary scored rows of a cell, as rk_compute.compute_cell builds them."""
    roles = {r: cell["roles"][r]["dirs"] for r in C.ROLES}
    lexcl = {k: v for k, v in EXCL.items() if k != "unit_weeks"}
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        with served_scores(reader):
            g, info = ER.load_cell(roles, panel=cell.get("panel"), **lexcl)
    g, uinfo = K.apply_unit_weeks(g, EXCL["unit_weeks"])
    g, finfo = K.apply_row_filter(g, cell.get("row_filter"))
    hp, _ = K.resolve_horizons(g.horizon.unique(), cell.get("primary_horizons"),
                               cell.get("secondary_horizons"))
    gp = K._sub(g, g.horizon.isin(hp).to_numpy())
    return gp, {"rows_scored": int(len(gp)), "seeds": info.get("seeds"),
                "unit_week_rows_dropped": uinfo.get("unit_week_rows_dropped"),
                "rows_dropped_by_filter": finfo.get("rows_dropped_by_filter"), "horizons": hp}


def run_cell(job) -> dict:
    cell, tmp, grid, ks, R = job
    os.chdir(ROOT)
    t0 = time.time()
    cid = cell["id"]
    hp = [int(h) for h in cell["primary_horizons"]]
    gp, info = kit_rows(cell, make_reader("wis_log", hp))
    gp = gp.reset_index(drop=True)
    cols = list(EST) + ["wis_L3"]
    base = {e: infer_estimand(gp, e, margin_rel=0.01) for e in EST}
    wref = float(base["G_excess"]["wis_ref"])
    hmax = int(gp.horizon.max())

    # candidates: zero-filled targets, as district-weeks
    zf = gp.zero_filled.to_numpy(bool)
    if np.any(gp.cases.to_numpy(float)[zf] != 0):
        raise ValueError(f"{cid}: zero-filled rows with cases > 0")
    cand = np.flatnonzero(zf)
    ck = _norm(gp.loc[cand, KEYS].reset_index(drop=True))
    dw = pd.factorize(pd.MultiIndex.from_arrays([ck.unit_id.to_numpy(), ck.target_week.to_numpy()]))[0]
    N = int(dw.max() + 1) if len(dw) else 0

    # gains on candidate rows if their target had been y cases (same kit pipeline)
    alt = {}
    for yv, col in ALT_Y.items():
        if yv != 0 and yv not in ks:
            continue
        gk, _ = kit_rows(cell, alt_reader(tmp, col, hp))
        gk = _norm(gk[KEYS + cols].copy())
        m = ck.merge(gk, on=KEYS, how="left", validate="one_to_one")
        if m[cols].isna().any().any():
            raise ValueError(f"{cid}: y={yv}: {int(m[cols].isna().any(axis=1).sum())} candidate rows missing")
        alt[yv] = {c: m[c].to_numpy(float) for c in cols}
        del gk, m
    G0 = {c: gp[c].to_numpy(float) for c in cols}
    checks = {f"y0_maxdiff_{c}": float(np.max(np.abs(alt[0][c] - G0[c][cand]))) if len(cand) else 0.0
              for c in cols}

    # per-(horizon, target week) groups: weekly means are sums / counts
    hw = pd.MultiIndex.from_arrays([gp.horizon.to_numpy(), gp.target_week.to_numpy()])
    gid, uniq = pd.factorize(hw)
    nG = len(uniq)
    wk = pd.DataFrame({"horizon": uniq.get_level_values(0), "target_week": uniq.get_level_values(1)})
    n_g = np.bincount(gid, minlength=nG).astype(float)
    sums = {c: np.bincount(gid, weights=G0[c], minlength=nG) for c in cols}
    gid_c = gid[cand]

    def series(c, extra):
        return pooled_horizon_series(wk.assign(v=(sums[c] + extra) / n_g), "v")

    zero = np.zeros(nG)
    for e in EST:
        f0 = ewc_inference(series(e, zero).to_numpy(), h=hmax)
        checks[f"fast_s0_absdiff_est_{e}"] = abs(f0.estimate - base[e]["estimate"])
        checks[f"fast_s0_absdiff_p_{e}"] = abs(f0.p - base[e]["p"])
    delta = {k: {c: alt[k][c] - G0[c][cand] for c in cols} for k in ks}

    # exact expectation under uniform selection (linear in the inclusion share)
    expect = {}
    for k in ks:
        for e in EST:
            all_ = float(series(e, np.bincount(gid_c, weights=delta[k][e], minlength=nG)).mean())
            e0 = float(base[e]["estimate"])
            expect[(e, k)] = {"est_all": all_, "est0": e0,
                              "zero_cross_s_pct": 100 * e0 / (e0 - all_) if (e0 - all_) != 0 and
                              0 < e0 / (e0 - all_) <= 1 else np.nan}

    recs = []
    verify_at = {(0, 10.0, 3), (1, BENCH, 1)}
    vchk = []
    for r in range(R):
        rng = np.random.default_rng([SEED, zlib.crc32(cid.encode()), r])
        perm = rng.permutation(N)
        for s in grid:
            m = int(round(s / 100 * N))
            sel_dw = np.zeros(N, bool)
            sel_dw[perm[:m]] = True
            rows = sel_dw[dw]
            gsel = gid_c[rows]
            for k in ks:
                ex_ref = np.bincount(gsel, weights=delta[k]["wis_L3"][rows], minlength=nG)
                wref_k = float(series("wis_L3", ex_ref).mean())
                for e in EST:
                    ex = np.bincount(gsel, weights=delta[k][e][rows], minlength=nG)
                    inf = ewc_inference(series(e, ex).to_numpy(), h=hmax)
                    recs.append({"cell": cid, "estimand": e, "s_pct": float(s), "k": int(k), "r": r,
                                 "n_dw": m, "n_rows_perturbed": int(rows.sum()),
                                 "estimate": inf.estimate, "se": inf.se, "df": inf.df, "p": inf.p,
                                 "lo95": inf.lo95, "hi95": inf.hi95,
                                 "pct": 100 * inf.estimate / wref, "lo95_pct": 100 * inf.lo95 / wref,
                                 "hi95_pct": 100 * inf.hi95 / wref,
                                 "pct_pert_ref": 100 * inf.estimate / wref_k})
                    if (r, float(s), k) in verify_at:
                        gpert = gp[["horizon", "target_week"]].copy()
                        v = G0[e].copy()
                        v[cand[rows]] = alt[k][e][rows]
                        gpert[e] = v
                        gpert["wis_L3"] = G0["wis_L3"]
                        gpert.attrs = {}
                        q = infer_estimand(gpert, e, margin_rel=0.01)
                        vchk.append({"estimand": e, "r": r, "s_pct": s, "k": k,
                                     "absdiff_est": abs(q["estimate"] - inf.estimate),
                                     "absdiff_p": abs(q["p"] - inf.p),
                                     "absdiff_lo95": abs(q["lo95"] - inf.lo95)})
    checks["verify_draws"] = vchk
    checks["verify_max_absdiff"] = max((max(x["absdiff_est"], x["absdiff_p"], x["absdiff_lo95"])
                                        for x in vchk), default=np.nan)
    base_out = {e: {k: (float(v) if isinstance(v, (int, float, np.floating, np.integer)) else v)
                    for k, v in base[e].items() if k in ("estimate", "se", "df", "p", "lo95", "hi95",
                                                         "wis_ref", "pct_of_ref", "n_rows", "n_weeks")}
                for e in EST}
    res = {"cell": cid, "country": cell["country"], "split": cell["split"], "cstar": cell.get("cstar"),
           "info": info, "base": base_out, "wis_ref": wref, "n_rows": int(len(gp)),
           "n_weeks": int(base["G_excess"]["n_weeks"]), "zero_filled_row_share": float(zf.mean()),
           "n_candidate_rows": int(len(cand)), "n_candidate_dw": N, "checks": checks,
           "expect": {f"{e}|{k}": v for (e, k), v in expect.items()},
           "seconds": round(time.time() - t0, 1)}
    out = Path(tmp) / "cells"
    out.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(recs).to_parquet(out / f"{cid}.draws.parquet", index=False)
    (out / f"{cid}.json").write_text(json.dumps(res, indent=1, default=str))
    return res


# ============================================================================ 3. report
def fmt_s(s: float) -> str:
    return f"{s:g}%"


def summarise(D: pd.DataFrame, cells: list[dict], grid, ks, R) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Holm per draw index over the 14 comparisons; one row per comparison x s x k."""
    ids = [c["cell"] for c in cells]
    meta = {c["cell"]: c for c in cells}
    # s = 0 (unperturbed) rows: the kit's own inference
    base = []
    for e in EST:
        p0 = np.array([meta[i]["base"][e]["p"] for i in ids])
        h0 = holm(p0)
        for i, hp in zip(ids, h0):
            b = meta[i]["base"][e]
            base.append({"cell": i, "estimand": e, "est0": b["estimate"], "pct0": b["pct_of_ref"],
                         "lo95_pct0": 100 * b["lo95"] / b["wis_ref"],
                         "hi95_pct0": 100 * b["hi95"] / b["wis_ref"], "p0": b["p"], "holm0": hp})
    B = pd.DataFrame(base).set_index(["cell", "estimand"])
    D = D.copy()
    D["holm_p"] = np.nan
    for _, grp in D.groupby(["estimand", "s_pct", "k", "r"]):
        if set(grp.cell) != set(ids) or len(grp) != len(ids):
            raise ValueError("a draw index lacks some comparison")
        D.loc[grp.index, "holm_p"] = holm(grp.p.to_numpy())
    D = D.join(B[["est0"]], on=["cell", "estimand"])
    D["sig_loss"] = (D.holm_p < 0.05) & (D.estimate < 0)
    D["sig_gain"] = (D.holm_p < 0.05) & (D.estimate > 0)
    D["gain_p05"] = (D.p < 0.05) & (D.estimate > 0)
    D["loss_p05"] = (D.p < 0.05) & (D.estimate < 0)
    D["flip"] = np.sign(D.estimate) != np.sign(D.est0)

    rows = []
    for i in ids:
        c = meta[i]
        common = {"cell": i, "country": c["country"], "split": c["split"], "C_star": c["cstar"],
                  "n_rows": c["n_rows"], "n_weeks": c["n_weeks"],
                  "zero_filled_row_share": c["zero_filled_row_share"],
                  "n_candidate_dw": c["n_candidate_dw"]}
        r0 = {**common, "s_pct": 0.0, "k": 0, "R": 0, "n_perturbed_dw": 0, "perturbed_row_share": 0.0}
        for e in EST:
            b = B.loc[(i, e)]
            p = PREFIX[e]
            r0.update({f"{p}_pct_s0": b.pct0, f"{p}_pct_median": b.pct0, f"{p}_pct_q025": b.pct0,
                       f"{p}_pct_q975": b.pct0, f"{p}_pct_expected": b.pct0,
                       f"{p}_lo95_pct_median": b.lo95_pct0, f"{p}_hi95_pct_median": b.hi95_pct0,
                       f"{p}_p_median": b.p0, f"{p}_holm_p_median": b.holm0,
                       f"{p}_share_holm_sig_loss": float(b.holm0 < 0.05 and b.est0 < 0),
                       f"{p}_share_holm_sig_gain": float(b.holm0 < 0.05 and b.est0 > 0),
                       f"{p}_share_p05_gain": float(b.p0 < 0.05 and b.est0 > 0),
                       f"{p}_share_p05_loss": float(b.p0 < 0.05 and b.est0 < 0),
                       f"{p}_share_sign_flip": 0.0})
        rows.append(r0)
        for k in ks:
            for s in grid:
                sub = D[(D.cell == i) & (D.s_pct == float(s)) & (D.k == k)]
                x = sub[sub.estimand == "G_excess"]
                r = {**common, "s_pct": float(s), "k": int(k), "R": int(x.r.nunique()),
                     "n_perturbed_dw": int(x.n_dw.iloc[0]),
                     "perturbed_row_share": float(x.n_rows_perturbed.iloc[0] / c["n_rows"])}
                for e in EST:
                    y = sub[sub.estimand == e]
                    p = PREFIX[e]
                    ex = c["expect"][f"{e}|{k}"]
                    frac = r["n_perturbed_dw"] / c["n_candidate_dw"] if c["n_candidate_dw"] else 0.0
                    r.update({f"{p}_pct_s0": B.loc[(i, e)].pct0,
                              f"{p}_pct_median": float(y.pct.median()),
                              f"{p}_pct_q025": float(y.pct.quantile(0.025)),
                              f"{p}_pct_q975": float(y.pct.quantile(0.975)),
                              f"{p}_pct_expected": 100 * (ex["est0"] + frac * (ex["est_all"] - ex["est0"]))
                              / c["wis_ref"],
                              f"{p}_lo95_pct_median": float(y.lo95_pct.median()),
                              f"{p}_hi95_pct_median": float(y.hi95_pct.median()),
                              f"{p}_p_median": float(y.p.median()),
                              f"{p}_holm_p_median": float(y.holm_p.median()),
                              f"{p}_share_holm_sig_loss": float(y.sig_loss.mean()),
                              f"{p}_share_holm_sig_gain": float(y.sig_gain.mean()),
                              f"{p}_share_p05_gain": float(y.gain_p05.mean()),
                              f"{p}_share_p05_loss": float(y.loss_p05.mean()),
                              f"{p}_share_sign_flip": float(y.flip.mean()),
                              f"{p}_pct_pert_ref_median": float(y.pct_pert_ref.median())})
                rows.append(r)
    T = pd.DataFrame(rows)
    # tipping share: smallest s at which the loss is no longer Holm-significant in >= half the draws
    for e in EST:
        p = PREFIX[e]
        T[f"{p}_tipping_s_pct"] = np.nan
        T[f"{p}_tipping_note"] = ""
        T[f"{p}_zero_cross_s_pct"] = np.nan
        T[f"{p}_tipping_unadj_s_pct"] = np.nan
        T[f"{p}_tipping_unadj_note"] = ""
        for i in ids:
            sig0 = B.loc[(i, e)].holm0 < 0.05 and B.loc[(i, e)].est0 < 0
            raw0 = B.loc[(i, e)].p0 < 0.05 and B.loc[(i, e)].est0 < 0
            for k in ks:
                m = (T.cell == i) & (T.k == k)
                T.loc[m, f"{p}_zero_cross_s_pct"] = meta[i]["expect"][f"{e}|{k}"]["zero_cross_s_pct"]
                if raw0:   # same rule without Holm: share of draws with unadjusted p < .05 and a loss
                    t = T[m & (T.s_pct > 0)].sort_values("s_pct")
                    hit = t[t[f"{p}_share_p05_loss"] <= 0.5]
                    T.loc[m, f"{p}_tipping_unadj_s_pct"] = float(hit.s_pct.iloc[0]) if len(hit) else np.nan
                    T.loc[m, f"{p}_tipping_unadj_note"] = (f"tips at {fmt_s(hit.s_pct.iloc[0])}" if len(hit)
                                                           else f"> {fmt_s(max(grid))} (still significant)")
                else:
                    T.loc[m, f"{p}_tipping_unadj_note"] = "no loss with p < .05 at s = 0"
                if not sig0:
                    T.loc[m, f"{p}_tipping_note"] = "no Holm-significant loss at s = 0"
                    continue
                t = T[m & (T.s_pct > 0)].sort_values("s_pct")
                hit = t[t[f"{p}_share_holm_sig_loss"] <= 0.5]
                if len(hit):
                    T.loc[m, f"{p}_tipping_s_pct"] = float(hit.s_pct.iloc[0])
                    T.loc[m, f"{p}_tipping_note"] = f"tips at {fmt_s(hit.s_pct.iloc[0])}"
                else:
                    T.loc[m, f"{p}_tipping_note"] = f"> {fmt_s(max(grid))} (still significant)"
        T.loc[T.k == 0, [f"{p}_tipping_s_pct", f"{p}_zero_cross_s_pct", f"{p}_tipping_unadj_s_pct"]] = np.nan
        T.loc[T.k == 0, [f"{p}_tipping_note", f"{p}_tipping_unadj_note"]] = ""
    return T, D


NAMES = {"S1": "future years", "S2": "held-out states", "S3": "held-out blocks",
         "S4": "held-out districts", "S5": "country held out"}


def label(cid: str) -> str:
    c, s = cid.split("_")
    return f"{c} {s}"


def md_table(header, rows) -> list[str]:
    out = ["| " + " | ".join(header) + " |", "|" + "|".join("---" for _ in header) + "|"]
    out += ["| " + " | ".join(str(x) for x in r) + " |" for r in rows]
    return out


def write_report(T, D, cells, sanity, pre, grid, ks, R, runtime, out_md):
    ids = [c["cell"] for c in cells]
    L = ["# R5: zero-fill stress test (hidden cases in filled weeks)", "",
         "Scoring-only sensitivity analysis; no model was refitted. Script: "
         "`scripts/analysis/zero_fill_stress.py`; table: `docs/results/review/R5_zero_fill_stress.csv`.", "",
         "## Question", "",
         "Outside the source's listed weeks, every district-week was set to 0 cases. If some of these "
         "filled weeks really held a few unreported cases, how far would the 14 primary comparisons move?", "",
         "## Method", "",
         "- **Rows and scoring** are those of the primary analysis (Table 2; `configs/primary_cells.yaml`, "
         "3-seed means where seeds exist): exclusions v2, origin-year row filter, horizons 1 and 4 pooled, "
         "each target week weighted equally, WIS on log(1 + cases) with the median and deciles. The rows "
         "are built with the results kit's own code (`estimands_report.load_cell`, `rk_compute`).",
         "- **Candidates** are district-weeks whose target was zero-filled (absent from the source). Weeks "
         "the source listed as 0 are never changed.",
         f"- **Perturbation.** In each comparison a random share s of the candidate district-weeks is set "
         f"to k cases (y = log(1 + k)); s in {{{', '.join(fmt_s(x) for x in grid)}}} "
         f"({fmt_s(BENCH)} = the Brazil benchmark, added to the grid) and k in {{{', '.join(map(str, ks))}}}. "
         "A changed district-week changes at both horizons, for all four models and every seed. "
         f"R = {R} draws per (s, k) with fixed seeds (`default_rng([20261122, crc32(comparison), r])`); "
         "within a draw the selected sets are nested across s and identical for k = 1 and 3.",
         "- **Rescoring.** WIS at y = 0, 1 and 3 cases was recomputed from the stored quantile forecasts "
         "(`pop.eval.scoring.wis_interval`) and passed through the same kit pipeline, so each row's gain "
         "follows the common-seed rule. Each draw's weekly gain series is tested with the main test "
         "(`pop.eval.stats.ewc_inference`, DM with EWC variance and HLN correction); Holm is applied over "
         "the 14 comparisons within each draw index (`pop.eval.stats.holm`).",
         "- **Percentages** are 100 x gain / unperturbed WIS(L3), so the denominator is fixed. "
         "The CSV also gives the median with the perturbed WIS(L3) (`*_pct_pert_ref_median`).",
         "- **Tipping share** = the smallest s at which the loss is no longer Holm-significant in at least "
         f"half of the {R} draws. Holm is applied within each draw, so a comparison's adjusted p also rises "
         "when the other losses weaken at the same time; the same rule without Holm (unadjusted p < .05) is "
         "reported beside it. The CSV also gives the exact share at which the *expected* gain reaches 0 "
         "(`*_zero_cross_s_pct`; the estimate is linear in the selection).",
         "- **Scope limits.** Only the scored targets change. Hidden cases would also have entered the "
         "case-history inputs and the training targets; this test cannot show that. Placement is uniform "
         "within each comparison.", ""]

    # ---------------- sanity
    L += ["## Sanity check: s = 0 reproduces Table 2 (T1_primary_family.csv)", ""]
    hdr = ["Comparison", "T1 excess gain % [95% CI]", "Recomputed % [95% CI]", "T1 Holm p",
           "Recomputed Holm p", "Rows T1 / here"]
    rows = []
    for _, r in sanity.iterrows():
        rows.append([label(r.cell), f"{r.t1_pct:+.4f} [{r.t1_lo:+.4f}, {r.t1_hi:+.4f}]",
                     f"{r.pct:+.4f} [{r.lo:+.4f}, {r.hi:+.4f}]", f"{r.t1_holm:.4g}", f"{r.holm:.4g}",
                     f"{int(r.t1_n):,} / {int(r.n):,}"])
    L += md_table(hdr, rows)
    mx = sanity[["d_pct", "d_lo", "d_hi", "d_p", "d_holm"]].abs().max()
    L += ["", f"Largest absolute difference over the 14 comparisons: excess gain % {mx.d_pct:.1e}, "
          f"CI bounds {max(mx.d_lo, mx.d_hi):.1e}, DM p {mx.d_p:.1e}, Holm p {mx.d_holm:.1e}; "
          f"embedding gain % {sanity.d_emb_pct.abs().max():.1e}; row counts equal in "
          f"{int((sanity.n == sanity.t1_n).sum())} of 14. **Result: {'PASS' if sanity.ok.all() else 'FAIL'}.**", ""]
    ck = [c["checks"] for c in cells]
    L += ["Other checks:",
          f"- WIS recomputed at the observed count from the forecast files matches the stored `wis_log` on "
          f"all {int(pre.n_forecasts.sum()):,} forecasts of the {len(pre)} run directories (largest absolute "
          f"difference {pre.wis_obs_maxdiff.max():.1e}; NaN pattern mismatches {int(pre.nan_pattern_mismatch.sum())}).",
          "- Rescoring at y = 0 reproduces the stored gains on every candidate row (largest absolute "
          f"difference {max(max(v for kk, v in c.items() if kk.startswith('y0_maxdiff')) for c in ck):.1e}).",
          "- Two draws per comparison recomputed with `pop.eval.estimands.infer_estimand` on an explicitly "
          f"perturbed frame agree with the fast path (largest absolute difference in estimate, p or CI bound "
          f"{max(c['verify_max_absdiff'] for c in ck):.1e}).", ""]

    # ---------------- results
    X = T[T.k > 0]
    show = [s for s in (1.0, BENCH, 5.0, 10.0) if s in set(X.s_pct)]
    for k in ks:
        L += [f"## Excess gain, k = {k} hidden case{'s' if k > 1 else ''} per changed week", "",
              "Cells: median excess gain % over draws [2.5–97.5% range of draws]; share of draws with a "
              "Holm-significant loss (sig) and with the sign flipped (flip).", ""]
        hdr = ["Comparison", "s = 0: % (Holm p)"] + [f"s = {fmt_s(s)}" for s in show]
        rows = []
        for i in ids:
            r0 = T[(T.cell == i) & (T.k == 0)].iloc[0]
            row = [label(i), f"{r0.exc_pct_s0:+.2f} ({r0.exc_holm_p_median:.3f})"]
            for s in show:
                r = X[(X.cell == i) & (X.k == k) & (X.s_pct == s)].iloc[0]
                row.append(f"{r.exc_pct_median:+.2f} [{r.exc_pct_q025:+.2f}, {r.exc_pct_q975:+.2f}]; "
                           f"sig {r.exc_share_holm_sig_loss:.2f}, flip {r.exc_share_sign_flip:.2f}")
            rows.append(row)
        L += md_table(hdr, rows) + [""]

    # ---------------- tipping
    L += ["## Tipping shares (excess gain)", "",
          "For the comparisons with a Holm-significant loss in Table 2. Tipping share = smallest s at which "
          "the loss is no longer significant in at least half the draws, with Holm over the 14 comparisons "
          "and without it (unadjusted p < .05); the last two columns give the share at which the expected "
          "excess gain reaches 0.", ""]
    sig0 = [i for i in ids if T[(T.cell == i) & (T.k == 0)].iloc[0].exc_share_holm_sig_loss == 1.0]
    hdr = ["Comparison", "s = 0: % (Holm p)"] + [f"Holm tipping, k = {k}" for k in ks] + \
        [f"Unadjusted tipping, k = {k}" for k in ks] + [f"Expected gain = 0 at s, k = {k}" for k in ks]
    rows = []
    for i in sig0:
        r0 = T[(T.cell == i) & (T.k == 0)].iloc[0]
        row = [label(i), f"{r0.exc_pct_s0:+.2f} ({r0.exc_holm_p_median:.4f})"]
        for k in ks:
            row.append(T[(T.cell == i) & (T.k == k)].iloc[0].exc_tipping_note)
        for k in ks:
            row.append(T[(T.cell == i) & (T.k == k)].iloc[0].exc_tipping_unadj_note)
        for k in ks:
            z = T[(T.cell == i) & (T.k == k)].iloc[0].exc_zero_cross_s_pct
            row.append(f"{z:.2f}%" if np.isfinite(z) else "> 100%")
        rows.append(row)
    L += md_table(hdr, rows) + [""]

    # ---------------- embedding gain (secondary)
    L += ["## Embedding gain (secondary)", "",
          "Same draws; Holm over the 14 comparisons as for the excess gain.", ""]
    hdr = ["Comparison", "s = 0: % (Holm p)"] + [f"k = {k}, s = {fmt_s(s)}" for k in ks for s in (BENCH, 10.0)]
    rows = []
    for i in ids:
        r0 = T[(T.cell == i) & (T.k == 0)].iloc[0]
        row = [label(i), f"{r0.emb_pct_s0:+.2f} ({r0.emb_holm_p_median:.3f})"]
        for k in ks:
            for s in (BENCH, 10.0):
                r = X[(X.cell == i) & (X.k == k) & (X.s_pct == s)].iloc[0]
                row.append(f"{r.emb_pct_median:+.2f}; sig loss {r.emb_share_holm_sig_loss:.2f}, "
                           f"sig gain {r.emb_share_holm_sig_gain:.2f}")
        rows.append(row)
    L += md_table(hdr, rows) + [""]
    L += ["## Interpretation", "", "INTERPRETATION_PLACEHOLDER", "",
          f"Runtime: {runtime}."]
    Path(out_md).write_text("\n".join(L) + "\n")


def sanity_table(cells, t1_path) -> pd.DataFrame:
    t1 = pd.read_csv(t1_path).set_index("cell")
    meta = {c["cell"]: c for c in cells}
    ids = [c["cell"] for c in cells]
    p = np.array([meta[i]["base"]["G_excess"]["p"] for i in ids])
    hp = dict(zip(ids, holm(p)))
    rows = []
    for i in ids:
        b = meta[i]["base"]["G_excess"]
        e = meta[i]["base"]["G_emb"]
        t = t1.loc[i]
        r = {"cell": i, "pct": b["pct_of_ref"], "lo": 100 * b["lo95"] / b["wis_ref"],
             "hi": 100 * b["hi95"] / b["wis_ref"], "p": b["p"], "holm": hp[i], "n": meta[i]["n_rows"],
             "t1_pct": t.pct_of_WIS_ref, "t1_lo": t.lo95_pct, "t1_hi": t.hi95_pct, "t1_p": t.DM_p,
             "t1_holm": t.Holm_p, "t1_n": t.n_rows, "emb_pct": e["pct_of_ref"], "t1_emb_pct": t.G_emb_pct}
        r.update(d_pct=r["pct"] - r["t1_pct"], d_lo=r["lo"] - r["t1_lo"], d_hi=r["hi"] - r["t1_hi"],
                 d_p=r["p"] - r["t1_p"], d_holm=r["holm"] - r["t1_holm"],
                 d_emb_pct=r["emb_pct"] - r["t1_emb_pct"])
        r["ok"] = bool(max(abs(r["d_pct"]), abs(r["d_lo"]), abs(r["d_hi"]), abs(r["d_p"]),
                           abs(r["d_holm"]), abs(r["d_emb_pct"])) < 1e-8 and r["n"] == r["t1_n"])
        rows.append(r)
    return pd.DataFrame(rows)


# ============================================================================ main
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--stage", choices=["all", "precompute", "cells", "report"], default="all")
    ap.add_argument("--manifest", default="configs/primary_cells.yaml")
    ap.add_argument("--workers-pre", type=int, default=10)
    ap.add_argument("--workers-cells", type=int, default=4)
    ap.add_argument("--R", type=int, default=20)
    ap.add_argument("--grid", default=f"0.5,1,2,{BENCH},5,10")
    ap.add_argument("--ks", default="1,3")
    ap.add_argument("--only", nargs="*", default=None, help="cells stage: only these comparison ids")
    ap.add_argument("--tmp", default="tmp/r5")
    ap.add_argument("--out", default="docs/results/review")
    ap.add_argument("--t1", default="docs/results/tables/T1_primary_family.csv")
    a = ap.parse_args(argv)
    os.chdir(ROOT)
    grid = sorted(float(x) for x in a.grid.split(","))
    ks = [int(x) for x in a.ks.split(",")]
    if any(k not in ALT_Y for k in ks):
        raise SystemExit(f"k must be one of {sorted(ALT_Y)}")
    cells = [c for c in C.build_registry(a.manifest) if c["group"] == "primary"]
    if len(cells) != C.FAMILY_SIZE:
        raise SystemExit(f"{len(cells)} primary cells, family size {C.FAMILY_SIZE}")
    for c in cells:
        st, roles = C.cell_status(c)
        if st != "available":
            raise SystemExit(f"{c['id']}: {st} {roles}")
    tmp = Path(a.tmp)
    tmp.mkdir(parents=True, exist_ok=True)
    t_start = time.time()
    timing = json.loads((tmp / "timing.json").read_text()) if (tmp / "timing.json").exists() else {}
    ctx = get_context("spawn")

    if a.stage in ("all", "precompute"):
        t0 = time.time()
        dirs = sorted({d for c in cells for r in C.ROLES for d in c["roles"][r]["dirs"]})
        hp = sorted({int(h) for c in cells for h in c["primary_horizons"]})
        log(f"precompute: {len(dirs)} run dirs, horizons {hp}, {a.workers_pre} workers")
        res = []
        with ProcessPoolExecutor(a.workers_pre, mp_context=ctx) as ex:
            futs = {ex.submit(precompute_dir, (d, str(tmp), hp)): d for d in dirs}
            for f in as_completed(futs):
                r = f.result()
                res.append(r)
                log(f"  {Path(r['dir']).name}: {r['n_forecasts']:,} forecasts, max|dWIS| "
                    f"{r['wis_obs_maxdiff']:.1e} ({len(res)}/{len(dirs)})")
        pd.DataFrame(res).to_csv(tmp / "precompute_checks.csv", index=False)
        timing["precompute_s"] = round(time.time() - t0, 1)

    if a.stage in ("all", "cells"):
        t0 = time.time()
        todo = [c for c in cells if not a.only or c["id"] in a.only]
        todo.sort(key=lambda c: -sum(len(c["roles"][r]["dirs"]) for r in C.ROLES)
                  * (5 if c["country"] == "brazil" else 1))
        log(f"cells: {len(todo)} comparisons, R = {a.R}, grid {grid}, k {ks}, {a.workers_cells} workers")
        with ProcessPoolExecutor(a.workers_cells, mp_context=ctx) as ex:
            futs = {ex.submit(run_cell, (c, str(tmp), grid, ks, a.R)): c["id"] for c in todo}
            for f in as_completed(futs):
                r = f.result()
                ck = r["checks"]
                log(f"  {r['cell']}: {r['n_rows']:,} rows, {r['n_candidate_dw']:,} candidate district-weeks, "
                    f"base excess {r['base']['G_excess']['pct_of_ref']:+.3f}%, y0 check "
                    f"{max(v for k, v in ck.items() if k.startswith('y0_maxdiff')):.1e}, verify "
                    f"{ck['verify_max_absdiff']:.1e}, {r['seconds']} s")
        timing["cells_s"] = round(time.time() - t0, 1)

    if a.stage in ("all", "report"):
        t0 = time.time()
        meta = [json.loads((tmp / "cells" / f"{c['id']}.json").read_text()) for c in cells]
        D = pd.concat([pd.read_parquet(tmp / "cells" / f"{c['id']}.draws.parquet") for c in cells],
                      ignore_index=True)
        T, D = summarise(D, meta, grid, ks, a.R)
        D.to_parquet(tmp / "draws_with_holm.parquet", index=False)
        sanity = sanity_table(meta, a.t1)
        sanity.to_csv(tmp / "sanity_check.csv", index=False)
        pre = pd.read_csv(tmp / "precompute_checks.csv")
        out = Path(a.out)
        T.to_csv(out / "R5_zero_fill_stress.csv", index=False)
        timing["report_s"] = round(time.time() - t0, 1)
        tot = sum(v for k, v in timing.items() if k.endswith("_s"))
        runtime = (f"{tot / 60:.1f} min wall-clock in total (precompute {timing.get('precompute_s', 0) / 60:.1f} "
                   f"min, comparisons {timing.get('cells_s', 0) / 60:.1f} min, report "
                   f"{timing.get('report_s', 0) / 60:.1f} min)")
        md = out / "R5_zero_fill_stress.md"
        if md.exists() and "INTERPRETATION_PLACEHOLDER" not in md.read_text():
            md = tmp / "R5_zero_fill_stress.regenerated.md"   # never overwrite a hand-written interpretation
        write_report(T, D, meta, sanity, pre, grid, ks, a.R, runtime, md)
        log(f"report: sanity {'PASS' if sanity.ok.all() else 'FAIL'}; wrote {md} and R5_zero_fill_stress.csv")
    (tmp / "timing.json").write_text(json.dumps(timing, indent=1))
    log(f"done in {(time.time() - t_start) / 60:.1f} min")
    return 0


if __name__ == "__main__":
    sys.exit(main())
