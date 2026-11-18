#!/usr/bin/env python
"""Scoring-only analyses for the reviewer round (RD_*). No model is refitted.

Every number comes from existing scores.parquet / forecasts.parquet of completed runs.

Usage (GPU, after `source env.sh`; one process per cell, then combine):
    nice -n 19 python scripts/analysis/review_more.py run [--cells BR_S1 ...] [--only A ...]
    nice -n 19 python scripts/analysis/review_more.py combine

Analyses (per available primary cell; rows = default exclusions, primary horizons {1,4}):
  baselines (S1 only) RD_baselines.csv: mean log1p-WIS at h1, h4 and pooled h{1,4} (row mean
            over the keys scored by every listed model), relative WIS = mean WIS / mean WIS(L0)
            (L0 = seasonal naive, same week last year; Cramer et al. 2022 style ratio of means),
            80% coverage overall and on positive weeks. Missing models are listed explicitly.
  weighted  RD_weighted.csv: G_excess (and G_emb, G_id) with unit weights inside each
            (horizon, week) mean: (a) population of the unit in the target year, (b) unit's
            mean weekly cases over 2013-2017 (before the first training target year 2018) + 1.
            Same estimator otherwise (equal-week pooling over h{1,4}, DM/EWC + HLN, margin 1%
            of the weighted WIS(L3)).
  outbreak  RD_outbreak.csv: G_excess on outbreak vs non-outbreak rows (outbreak = cases >=
            max(unit p90 of 2013-2019, 5), estimands_report.outbreak_threshold) + a test of the
            difference (weekly series d_out - d_non on weeks with both).
  recal     RD_recal.csv / RD_recal_shifts.csv: causal quantile recalibration of L3+C* and
            L4+C* separately (log1p scale, per cell x model x horizon x seed): for test year Y,
            additive per-quantile shifts delta_tau = tau-quantile ('inverted_cdf') of
            log1p(y) - q_tau over that model's scored rows of test years < Y; the first test
            year is left unadjusted (no 2019-origin run exists for L3+C*/L4+C*). Variant
            'global' (one shift per tau) and 'mondrian' (shifts per bin of the raw forecast
            median, log1p edges 0.1/1/2; bins with < 200 calibration rows use the global
            shift). Quantiles are clipped at 0 and re-sorted. G_excess is recomputed with the
            primary estimator, on all years and on years >= the 2nd test year.
  mech      RD_mechanism.csv: on y = 0 rows, mean q0.9 (log1p and case scale) of L4+C* minus
            L3+C* (EWC CI on the weekly series) and the additive split of the y = 0 rows'
            contribution to G_excess into quantile levels (tau >= 0.6, tau = 0.9).
  peryear   RD_peryear.csv: G_excess per test year, with context flags.
"""
from __future__ import annotations

import argparse
import gc
import json
import os
import sys
import warnings
from pathlib import Path

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_MAX_THREADS"):
    os.environ.setdefault(_v, "4")

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent / "run")]

from pop.eval.estimands import ESTIMANDS, infer_estimand  # noqa: E402
from pop.eval.stats import classify_effect, ewc_inference, pooled_horizon_series, tost_p  # noqa: E402

QLEV = np.round(np.arange(1, 10) / 10, 6)
K = 4
KEYS = ["test_year", "unit_id", "origin_week", "target_week", "horizon"]
FKEYS = ["test_year", "unit_id", "origin_week", "horizon"]
OUT = Path("docs/results/review")
CDIR = OUT / "RD_cells"
POP_FILE = Path("data/interim/population/unit_population_yearly_v1.parquet")
PRE_YEARS = (2013, 2017)
MED_EDGES = (0.1, 1.0, 2.0)
MIN_BIN = 200
COUNTRY_UP = {"brazil": "BRAZIL", "colombia": "COLOMBIA", "peru": "PERU", "taiwan": "TAIWAN"}
ROLE_LABEL = {"L3": "L3", "L4": "L4", "L3C": "L3+C*", "L4C": "L4+C*"}


# =========================================================================== helpers (tested)
def weighted_weekly(g: pd.DataFrame, col: str, w=None, *, time_col="target_week",
                    horizon_col="horizon") -> pd.Series:
    """Per (horizon, week): sum(w x) / sum(w) over rows (plain mean if w is None); then the
    unweighted mean over the horizons present in each week (as estimands.weekly_pooled)."""
    x = g[col].to_numpy(float)
    ww = np.ones(len(g)) if w is None else np.asarray(w, float)
    ok = np.isfinite(x) & np.isfinite(ww)
    df = pd.DataFrame({"h": g[horizon_col].to_numpy()[ok], "t": g[time_col].to_numpy()[ok],
                       "wx": (ww * x)[ok], "w": ww[ok]})
    s = df.groupby(["h", "t"], sort=True)[["wx", "w"]].sum()
    wk = (s.wx / s.w).rename(col).reset_index().rename(columns={"h": horizon_col, "t": time_col})
    return pooled_horizon_series(wk, col, time_col=time_col, horizon_col=horizon_col)


def infer_weighted(g: pd.DataFrame, col: str, *, ref_col="wis_L3", w=None, margin_rel=0.01,
                   alpha=0.05) -> dict:
    """Primary estimator (DM/EWC + HLN, h = max horizon) on the (weighted) weekly series."""
    hmax = int(g.horizon.max())
    d = weighted_weekly(g, col, w)
    inf = ewc_inference(d.to_numpy(), h=hmax)
    ref = float(weighted_weekly(g, ref_col, w).mean())
    m = margin_rel * ref
    out = inf.to_dict()
    out.update(wis_ref=ref, margin=m, pct_of_ref=100 * inf.estimate / ref,
               lo95_pct=100 * inf.lo95 / ref, hi95_pct=100 * inf.hi95 / ref,
               tost_p=tost_p(inf.estimate, inf.se, inf.df, m),
               cls=classify_effect(inf.lo95, inf.hi95, inf.lo90, inf.hi90, inf.p, m, alpha),
               n_rows=int(len(g)), n_weeks=int(d.size))
    return out


def fit_shifts(y: np.ndarray, q: np.ndarray, levels=QLEV) -> np.ndarray:
    """Additive per-level shifts: delta_j = levels[j]-quantile (inverted CDF) of y - q[:, j],
    so that the shifted quantile covers y with empirical frequency >= levels[j]."""
    r = np.asarray(y, float)[:, None] - np.asarray(q, float)
    return np.array([np.quantile(r[:, j], levels[j], method="inverted_cdf")
                     for j in range(r.shape[1])])


def apply_shifts(q: np.ndarray, s: np.ndarray) -> np.ndarray:
    """q + s, clipped at 0 (log1p of a count) and re-sorted along the quantile axis."""
    return np.sort(np.maximum(np.asarray(q, float) + np.asarray(s, float), 0.0), axis=1)


def median_bin(q: np.ndarray, edges=MED_EDGES) -> np.ndarray:
    return np.searchsorted(np.asarray(edges), np.asarray(q, float)[:, QLEV.size // 2], side="right")


def causal_recalibrate(year, h, y, q, *, mode="global", edges=MED_EDGES, min_bin=MIN_BIN):
    """Recalibrated quantiles (n, 9) for every row; rows of year Y use shifts fitted only on
    rows with year < Y and the same horizon (first year unchanged). Returns (q_new, shifts)
    where shifts is a list of dicts (year, horizon, bin, n_fit, delta_0.1..delta_0.9)."""
    year, h = np.asarray(year), np.asarray(h)
    y, q = np.asarray(y, float), np.asarray(q, float)
    out = q.copy()
    bins = median_bin(q, edges) if mode == "mondrian" else np.zeros(len(q), int)
    rows = []
    for Y in np.unique(year):
        past = year < Y
        if not past.any():
            continue
        for hh in np.unique(h[year == Y]):
            fit = past & (h == hh)
            if not fit.any():
                continue
            sg = fit_shifts(y[fit], q[fit])
            cur = (year == Y) & (h == hh)
            for b in np.unique(bins[cur]):
                fb = fit & (bins == b)
                use_global = mode != "mondrian" or fb.sum() < min_bin
                s = sg if use_global else fit_shifts(y[fb], q[fb])
                m = cur & (bins == b)
                out[m] = apply_shifts(q[m], s)
                rows.append({"year": int(Y), "horizon": int(hh), "bin": int(b),
                             "n_fit": int(fit.sum() if use_global else fb.sum()),
                             "fallback_global": bool(mode == "mondrian" and use_global),
                             **{f"delta_{lv:.1f}": float(v) for lv, v in zip(QLEV, s)}})
    return out, rows


def pinball_parts(ylog: np.ndarray, qlog: np.ndarray) -> np.ndarray:
    """Per-level WIS parts (n, 9): pinball_tau / (K + 0.5); they sum to WIS (log scale)."""
    ylog = np.asarray(ylog, float)[:, None]
    return ((ylog < qlog).astype(float) - QLEV[None, :]) * (qlog - ylog) / (K + 0.5)


def cov80(ylog, qlog) -> np.ndarray:
    return ((ylog >= qlog[:, 0]) & (ylog <= qlog[:, -1])).astype(float)


def contribution_series(g: pd.DataFrame, col: str, mask) -> pd.Series:
    """Additive contribution of the rows in ``mask`` to the equal-week pooled mean of ``col``:
    per (h, t) sum over masked rows / all rows, then mean over horizons."""
    x = np.where(np.asarray(mask, bool), g[col].to_numpy(float), 0.0)
    df = pd.DataFrame({"horizon": g.horizon.to_numpy(), "target_week": g.target_week.to_numpy(),
                       "c": x})
    wk = df.groupby(["horizon", "target_week"], sort=True).c.mean().reset_index()
    return pooled_horizon_series(wk, "c")


def context_flags(country: str, year: int) -> str:
    f = []
    if year in (2020, 2021):
        f.append("COVID-era reporting")
    if country == "peru" and year == 2023:
        f.append("Peru record season")
    if country == "brazil" and year == 2024:
        f.append("Brazil record epidemic")
    if country == "taiwan" and year == 2023:
        f.append("Taiwan 2023 outbreak")
    return "; ".join(f)


# =========================================================================== cell loading
def primary_cells(ids=None) -> list[dict]:
    import rk_cells as R
    out = []
    for c in R.build_registry():
        if c["group"] != "primary" or (ids and c["id"] not in ids):
            continue
        c["status"] = R.cell_status(c)[0]
        out.append(c)
    return out


def load_g(cell: dict, horizons=None) -> tuple[pd.DataFrame, dict]:
    import rk_cells as R
    import estimands_report as ER
    hp = horizons or cell.get("primary_horizons") or [1, 4]
    orig = ER.read_scores

    def read_h(dirs, cols=("wis_log", "cases", "cov_40", "cov_80")):
        # memory: read only the primary horizons (BR S1 has 3 seeds x h1-h4 otherwise)
        import pyarrow.parquet as pq
        out = []
        for d in map(Path, dirs):
            names = pq.ParquetFile(d / "scores.parquet").schema.names
            use = KEYS + [c for c in cols if c in names] + [c for c in ("seed", "run") if c in names]
            s = pd.read_parquet(d / "scores.parquet", columns=use,
                                filters=[("horizon", "in", [int(h) for h in hp])])
            s["seed"] = s.seed.astype(int) if "seed" in s else 0
            s["label"] = s["run"].astype(str) if "run" in s else d.name
            s["dir"] = d.name
            s["test_year"] = s.test_year.astype(int)
            s["unit_id"] = s.unit_id.astype(str)
            s["origin_week"] = pd.to_datetime(s.origin_week)
            s["target_week"] = pd.to_datetime(s.target_week)
            s["horizon"] = s.horizon.astype(int)
            out.append(s.drop(columns=[c for c in ("run",) if c in s]))
        return pd.concat(out, ignore_index=True)

    ER.read_scores = read_h
    try:
        g, info = ER.load_cell({r: cell["roles"][r]["dirs"] for r in R.ROLES},
                               panel=cell.get("panel"))
    finally:
        ER.read_scores = orig
    keep = KEYS + ["wis_L3", "wis_L4", "wis_L3C", "wis_L4C", "G_emb", "G_id", "G_excess",
                   "zero_filled", "outbreak", "cases", "state"]
    g = g.loc[g.horizon.isin(hp), keep].reset_index(drop=True)
    return g, info


def est_row(label: dict, r: dict) -> dict:
    f = ["estimate", "se", "df", "p", "lo95", "hi95", "pct_of_ref", "lo95_pct", "hi95_pct",
         "wis_ref", "tost_p", "cls", "n_rows", "n_weeks"]
    return {**label, **{k: r.get(k, np.nan) for k in f}}


def primary_check(g):
    return {e: infer_estimand(g, e)["estimate"] for e in ESTIMANDS}


# =========================================================================== analyses
def run_weighted(cell, g) -> pd.DataFrame:
    import estimands_report as ER
    country = cell["country"]
    pop = pd.read_parquet(POP_FILE)
    pop["unit_id"] = pop.unit_id.astype(str)
    years = np.sort(pop.year.unique())
    ty = g.target_week.dt.year.to_numpy()
    ty_c = np.clip(ty, years.min(), years.max())
    pk = pd.MultiIndex.from_arrays([pop.unit_id, pop.year])
    pv = pd.Series(pop["pop"].to_numpy(float), index=pk)
    w_pop = pv.reindex(pd.MultiIndex.from_arrays([g.unit_id, ty_c])).to_numpy()
    pnl = ER.load_panel(cell.get("panel") or _panel_path(cell), COUNTRY_UP[country])
    base = pnl[(pnl.year >= PRE_YEARS[0]) & (pnl.year <= PRE_YEARS[1])
               & ~pnl.flag_gap.fillna(False).astype(bool)]
    mc = base.groupby("unit_id").cases.mean()
    w_case = g.unit_id.map(mc).fillna(0.0).to_numpy() + 1.0
    rows = []
    for name, w in (("unweighted", None), ("population", w_pop), ("pre_cases_plus1", w_case)):
        n_miss = 0 if w is None else int((~np.isfinite(w)).sum())
        for e in ESTIMANDS:
            r = infer_weighted(g, e, w=w)
            rows.append(est_row({"cell": cell["id"], "weights": name, "estimand": e,
                                 "rows_no_weight": n_miss}, r))
    return pd.DataFrame(rows)


def _panel_path(cell):
    import yaml
    d = Path(cell["roles"]["L3"]["dirs"][0])
    return yaml.safe_load((d / "config_resolved.yaml").read_text())["panel"]


def run_outbreak(cell, g) -> pd.DataFrame:
    rows = []
    sub = {"all": g, "outbreak": g[g.outbreak], "non_outbreak": g[~g.outbreak]}
    for name, s in sub.items():
        if s.target_week.nunique() < 10:
            continue
        r = infer_estimand(s, "G_excess")
        r["lo95_pct"], r["hi95_pct"] = 100 * r["lo95"] / r["wis_ref"], 100 * r["hi95"] / r["wis_ref"]
        rows.append(est_row({"cell": cell["id"], "stratum": name,
                             "row_share": len(s) / len(g)}, r))
    # difference outbreak - non-outbreak on weeks with both
    if g.outbreak.any():
        a = weighted_weekly(g[g.outbreak], "G_excess")
        b = weighted_weekly(g[~g.outbreak], "G_excess")
        d = (a - b).dropna()
        if d.size >= 10:
            inf = ewc_inference(d.to_numpy(), h=int(g.horizon.max()))
            rows.append({"cell": cell["id"], "stratum": "outbreak_minus_non", "estimate": inf.estimate,
                         "se": inf.se, "df": inf.df, "p": inf.p, "lo95": inf.lo95, "hi95": inf.hi95,
                         "n_weeks": int(d.size)})
    # additive contribution of outbreak rows to the cell total
    c = contribution_series(g, "G_excess", g.outbreak.to_numpy())
    tot = weighted_weekly(g, "G_excess").mean()
    rows.append({"cell": cell["id"], "stratum": "outbreak_contribution", "estimate": float(c.mean()),
                 "share_of_total": float(c.mean() / tot) if tot else np.nan})
    return pd.DataFrame(rows)


def run_peryear(cell, g) -> pd.DataFrame:
    rows = []
    for y in sorted(g.test_year.unique()):
        s = g[g.test_year == y]
        if s.target_week.nunique() < 10:
            continue
        r = infer_estimand(s, "G_excess")
        r["lo95_pct"], r["hi95_pct"] = 100 * r["lo95"] / r["wis_ref"], 100 * r["hi95"] / r["wis_ref"]
        rows.append(est_row({"cell": cell["id"], "test_year": int(y),
                             "context": context_flags(cell["country"], int(y)),
                             "positive_share": float((s.cases > 0).mean()),
                             "mean_log1p_cases": float(np.log1p(s.cases).mean())}, r))
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ forecasts
def read_wide(d: Path, horizons, keys: pd.DataFrame) -> pd.DataFrame:
    """Wide raw forecasts (case scale) of run dir d at the given horizons, restricted to the
    keys of ``keys`` (FKEYS); one row per (seed, key); columns q0..q8."""
    import pyarrow.parquet as pq
    names = pq.ParquetFile(d / "forecasts.parquet").schema.names
    cols = [c for c in ("seed",) if c in names] + FKEYS + ["quantile", "value"]
    out = []
    kidx = pd.MultiIndex.from_frame(keys[FKEYS])
    for y in sorted(keys.test_year.unique()):
        t = pq.read_table(d / "forecasts.parquet", columns=cols,
                          filters=[("test_year", "==", int(y)), ("horizon", "in", list(horizons))])
        f = t.to_pandas()
        del t
        if "seed" not in f:
            f["seed"] = 0
        f["unit_id"] = f.unit_id.astype(str)
        f["origin_week"] = pd.to_datetime(f.origin_week)
        f["test_year"] = f.test_year.astype(int)
        f["horizon"] = f.horizon.astype(int)
        f["quantile"] = np.round(f["quantile"].astype(float), 6)
        f = f[f["quantile"].isin(QLEV)]
        f = f.sort_values(["seed"] + FKEYS + ["quantile"], kind="stable")
        n = len(f) // QLEV.size
        qv = f["quantile"].to_numpy().reshape(n, QLEV.size)
        if len(f) % QLEV.size or not np.allclose(qv, QLEV[None, :]):
            raise ValueError(f"{d}: quantile rows are not complete 9-sets for year {y}")
        w = f.iloc[::QLEV.size][["seed"] + FKEYS].reset_index(drop=True)
        v = f["value"].to_numpy(float).reshape(n, QLEV.size)
        for j in range(QLEV.size):
            w[f"q{j}"] = v[:, j]
        del f
        w = w[pd.MultiIndex.from_frame(w[FKEYS]).isin(kidx)]
        out.append(w)
        gc.collect()
    return pd.concat(out, ignore_index=True)


def role_forecasts(cell, role, g) -> dict:
    """Per-row (keys of g) seed-averaged metrics of one role: raw / global / mondrian WIS and
    80% coverage, q0.9 (log, case), per-level WIS parts; plus the shift table and a WIS check."""
    hs = sorted(int(h) for h in g.horizon.unique())
    keys = g[KEYS + ["cases"]].drop_duplicates(FKEYS)
    frames, shifts, chk = [], [], []
    for d in cell["roles"][role]["dirs"]:
        w = read_wide(Path(d), hs, keys)
        frames.append(w)
    w = pd.concat(frames, ignore_index=True)
    del frames
    w = w.drop_duplicates(["seed"] + FKEYS)
    w = w.merge(keys, on=FKEYS, how="inner")
    w = w.sort_values(["seed", "test_year", "horizon"] + FKEYS[1:2], kind="stable").reset_index(drop=True)
    qcols = [f"q{j}" for j in range(QLEV.size)]
    res = []
    for s, ws in w.groupby("seed", sort=True):
        q_case = np.maximum(ws[qcols].to_numpy(float), 0.0)
        q = np.sort(np.log1p(q_case), axis=1)
        y = np.log1p(ws.cases.to_numpy(float))
        yr, h = ws.test_year.to_numpy(), ws.horizon.to_numpy()
        out = ws[FKEYS + ["target_week"]].copy()
        out["seed"] = s
        parts = pinball_parts(y, q)
        out["wis_raw"] = parts.sum(axis=1)
        out["cov_raw"] = cov80(y, q)
        out["q90_log"] = q[:, -1]
        out["q90_case"] = np.sort(q_case, axis=1)[:, -1]
        for j in range(QLEV.size):
            out[f"part{j}"] = parts[:, j]
        for mode in ("global", "mondrian"):
            qn, sh = causal_recalibrate(yr, h, y, q, mode=mode)
            out[f"wis_{mode}"] = pinball_parts(y, qn).sum(axis=1)
            out[f"cov_{mode}"] = cov80(y, qn)
            shifts += [{"cell": cell["id"], "role": ROLE_LABEL[role], "seed": int(s), "mode": mode,
                        **r} for r in sh]
        res.append(out)
    del w
    r = pd.concat(res, ignore_index=True)
    num = [c for c in r.columns if c not in FKEYS + ["target_week", "seed"]]
    r = r.groupby(FKEYS, sort=False)[num].mean().reset_index()   # seed average
    return {"rows": r, "shifts": shifts}


def run_forecast_analyses(cell, g, todo) -> dict:
    out = {}
    rf = {}
    for role in ("L3C", "L4C"):
        rf[role] = role_forecasts(cell, role, g)
        gc.collect()
    a = rf["L3C"]["rows"].set_index(FKEYS)
    b = rf["L4C"]["rows"].set_index(FKEYS)
    idx = pd.MultiIndex.from_frame(g[FKEYS])
    A, B = a.reindex(idx), b.reindex(idx)
    gg = g[KEYS + ["cases", "wis_L3", "wis_L3C", "wis_L4C", "G_excess", "state"]].copy()
    miss = int(A.wis_raw.isna().sum() + B.wis_raw.isna().sum())
    chk = {"cell": cell["id"], "rows": len(gg), "rows_missing_forecast": miss,
           "max_abs_wis_diff_L3C": float(np.nanmax(np.abs(A.wis_raw.to_numpy() - gg.wis_L3C.to_numpy()))),
           "max_abs_wis_diff_L4C": float(np.nanmax(np.abs(B.wis_raw.to_numpy() - gg.wis_L4C.to_numpy())))}
    out["check"] = pd.DataFrame([chk])
    pos = gg.cases.to_numpy() > 0
    years = np.sort(gg.test_year.unique())
    if "recal" in todo:
        rows = []
        for mode in ("raw", "global", "mondrian"):
            gg[f"wL3C_{mode}"] = A[f"wis_{mode}"].to_numpy()
            gg[f"wL4C_{mode}"] = B[f"wis_{mode}"].to_numpy()
            gg[f"G_{mode}"] = gg[f"wL3C_{mode}"] - gg[f"wL4C_{mode}"]
        for span, m in (("all_years", np.ones(len(gg), bool)),
                        ("from_2nd_test_year", gg.test_year.to_numpy() > years[0])):
            s = gg[m]
            for mode in ("raw", "global", "mondrian"):
                r = infer_weighted(s, f"G_{mode}", ref_col="wis_L3")   # % of WIS(L3), as the primary
                lab = {"cell": cell["id"], "years": span, "calibration": mode}
                for role, F in (("L3C", A), ("L4C", B)):
                    cv = F[f"cov_{mode}"].to_numpy()[m]
                    lab[f"cov80_{ROLE_LABEL[role]}"] = float(np.nanmean(cv))
                    lab[f"cov80pos_{ROLE_LABEL[role]}"] = float(np.nanmean(cv[pos[m]]))
                    lab[f"wis_{ROLE_LABEL[role]}"] = float(weighted_weekly(s, f"w{role}_{mode}").mean())
                rows.append(est_row(lab, r))
        out["recal"] = pd.DataFrame(rows)
        out["shifts"] = pd.DataFrame(rf["L3C"]["shifts"] + rf["L4C"]["shifts"])
    if "mech" in todo:
        z = gg.cases.to_numpy() == 0
        gz = gg[z].copy()
        gz["dq90_log"] = B.q90_log.to_numpy()[z] - A.q90_log.to_numpy()[z]
        gz["dq90_case"] = B.q90_case.to_numpy()[z] - A.q90_case.to_numpy()[z]
        gz["q90L3C_log"] = A.q90_log.to_numpy()[z]
        gz["q90L3C_case"] = A.q90_case.to_numpy()[z]
        row = {"cell": cell["id"], "zero_row_share": float(z.mean())}
        for c in ("dq90_log", "dq90_case"):
            inf = ewc_inference(weighted_weekly(gz, c).to_numpy(), h=int(gg.horizon.max()))
            row.update({f"{c}": inf.estimate, f"{c}_lo95": inf.lo95, f"{c}_hi95": inf.hi95,
                        f"{c}_p": inf.p})
        row["q90_L3C_log_mean"] = float(weighted_weekly(gz, "q90L3C_log").mean())
        row["q90_L3C_case_mean"] = float(weighted_weekly(gz, "q90L3C_case").mean())
        # additive split of G_excess (raw, recomputed) into zero rows and per-level parts
        gg["G_raw"] = A.wis_raw.to_numpy() - B.wis_raw.to_numpy()
        tot = float(weighted_weekly(gg, "G_raw").mean())
        cz = float(contribution_series(gg, "G_raw", z).mean())
        row.update(G_excess=tot, G_zero_contrib=cz,
                   zero_share_of_G=cz / tot if tot else np.nan)
        parts = []
        for j in range(QLEV.size):
            gg[f"dp{j}"] = A[f"part{j}"].to_numpy() - B[f"part{j}"].to_numpy()
            parts.append(float(contribution_series(gg, f"dp{j}", z).mean()))
        parts = np.array(parts)
        row.update(zero_contrib_upper=float(parts[5:].sum()), zero_contrib_q90=float(parts[8]),
                   zero_contrib_median_lower=float(parts[:5].sum()),
                   upper_share_of_zero=float(parts[5:].sum() / cz) if cz else np.nan,
                   q90_share_of_zero=float(parts[8] / cz) if cz else np.nan)
        cz_series = contribution_series(gg, "G_raw", z)
        inf = ewc_inference(cz_series.to_numpy(), h=int(gg.horizon.max()))
        row.update(G_zero_contrib_lo95=inf.lo95, G_zero_contrib_hi95=inf.hi95,
                   wis_L3_ref=float(weighted_weekly(g, "wis_L3").mean()))
        out["mech"] = pd.DataFrame([row])
    return out


# ------------------------------------------------------------------ baselines
def run_baselines(cell, g) -> pd.DataFrame:
    import pyarrow.parquet as pq
    from rk_compute import ladder_table
    c = cell["country"]
    rungs, missing = [], []

    def has_label(d, lab):
        p = Path(d) / "scores.parquet"
        if not p.exists():
            return False
        if lab is None:
            return True
        return lab in set(pq.ParquetFile(p).read(columns=["run"]).column(0).unique().to_pylist())

    cand = [("L0 (seasonal naive)", f"runs/{c}_s1_baselines", "naive-L0"),
            ("NB GLM (L1)", f"runs/{c}_s1_baselines", "nb-L1"),
            ("TimesFM 2.5 zero-shot", f"runs/{c}_s1_timesfm_zs", None),
            ("LightGBM L1", f"runs/{c}_s1_baselines", "lgbm-L1")]
    l2 = f"runs/{c}_s1_L2"
    l2_lab = "LightGBM L2" if c != "taiwan" else "LightGBM L2 (per-level tuned)"
    if c == "taiwan" and Path("runs/taiwan_s1_shared_L2/scores.parquet").exists():
        l2, l2_lab = "runs/taiwan_s1_shared_L2", "LightGBM L2"
    cand.append((l2_lab, l2, "lgbm-L2"))
    for lab, d, run in cand:
        if has_label(d, run):
            rungs.append((lab, [d], run))
        else:
            missing.append(lab)
    for r in ("L3", "L4", "L3C", "L4C"):
        rungs.append((f"LightGBM {ROLE_LABEL[r]}", list(cell["roles"][r]["dirs"]), None))
    lad = ladder_table(g, rungs, primary_horizons=[1, 4], secondary_horizons=None)
    l0 = lad[lad.label.str.startswith("L0")].set_index("horizon").wis_log
    l1 = lad[lad.label == "LightGBM L1"].set_index("horizon").wis_log
    lad["rel_wis_vs_L0"] = lad.wis_log / lad.horizon.map(l0)
    lad["rel_wis_vs_L1"] = lad.wis_log / lad.horizon.map(l1)
    lad.insert(0, "cell", cell["id"])
    lad["missing_models"] = "; ".join(missing) if missing else ""
    return lad


# =========================================================================== driver
def run_cell(cell, todo, cdir: Path, log=print) -> None:
    cid = cell["id"]
    g, info = load_g(cell)
    log(f"{cid}: {len(g):,} rows, years {sorted(g.test_year.unique())}")
    pc = primary_check(g)
    (cdir / f"{cid}_info.json").write_text(json.dumps(
        {"primary_estimates": pc, "rows": len(g), "cstar": cell.get("cstar"),
         "seeds": info.get("seeds"), "excluded": info.get("excluded")}, indent=1, default=str))
    if "baselines" in todo and cell["split"] == "S1":
        run_baselines(cell, g).to_csv(cdir / f"{cid}_baselines.csv", index=False)
        log(f"{cid}: baselines done")
    if "weighted" in todo:
        run_weighted(cell, g).to_csv(cdir / f"{cid}_weighted.csv", index=False)
        log(f"{cid}: weighted done")
    if "outbreak" in todo:
        run_outbreak(cell, g).to_csv(cdir / f"{cid}_outbreak.csv", index=False)
    if "peryear" in todo:
        run_peryear(cell, g).to_csv(cdir / f"{cid}_peryear.csv", index=False)
    if todo & {"recal", "mech"}:
        o = run_forecast_analyses(cell, g, todo)
        for k, df in o.items():
            df.to_csv(cdir / f"{cid}_{k}.csv", index=False)
        log(f"{cid}: forecast analyses done")
    del g
    gc.collect()


def combine(out: Path) -> None:
    cdir = out / "RD_cells"
    names = {"baselines": "RD_baselines.csv", "weighted": "RD_weighted.csv",
             "outbreak": "RD_outbreak.csv", "peryear": "RD_peryear.csv", "recal": "RD_recal.csv",
             "shifts": "RD_recal_shifts.csv", "mech": "RD_mechanism.csv",
             "check": "RD_forecast_check.csv"}
    for k, fn in names.items():
        fs = sorted(cdir.glob(f"*_{k}.csv"))
        if fs:
            pd.concat([pd.read_csv(f) for f in fs], ignore_index=True).to_csv(out / fn, index=False)
            print(f"{fn}: {len(fs)} cells")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["run", "combine"])
    ap.add_argument("--cells", nargs="*")
    ap.add_argument("--only", nargs="*", default=["baselines", "weighted", "outbreak", "peryear",
                                                    "recal", "mech"])
    ap.add_argument("--out", default=str(OUT))
    a = ap.parse_args()
    out = Path(a.out)
    cdir = out / "RD_cells"
    cdir.mkdir(parents=True, exist_ok=True)
    if a.cmd == "combine":
        combine(out)
        return
    warnings.filterwarnings("ignore", category=RuntimeWarning)
    for c in primary_cells(a.cells):
        if c["status"] != "available":
            print(f"{c['id']}: {c['status']}, skipped")
            continue
        run_cell(c, set(a.only), cdir)


if __name__ == "__main__":
    main()
