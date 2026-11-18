#!/usr/bin/env python
"""Scoring-only sensitivity analyses for the external review of Paper 1 (no model refits).

Usage (repo root, after `source env.sh`):
    nice -n 19 python scripts/analysis/review_sens.py [--only CELL ...] [--force] [--n-boot 2000]
        [--out docs/results/review] [--no-forecast-scan]

Every available primary cell of configs/primary_cells.yaml (rk_cells.build_registry; pending
cells are skipped and listed) is analysed from the existing scores/forecast files:
  RA1 strata3        positive cases / explicitly recorded zeros / zero-filled zeros; G_emb,
                     G_id, G_excess with the primary inference (DM/EWC + HLN, equal-week weights)
  RA2 lookahead      drop rows whose origin week precedes the last training-label week of the
                     annual model that scored them (= last week of epi-year test_year - 1); all
                     four roles on identical admissible rows; % rows dropped
  RA3 noqual         primary G_excess without the incomplete-week flags (no-geometry units
                     stay excluded; flag_gap weeks are never scored by the runner)
  RA4 equivalence    unrounded 90% CIs at margins 0.5/1/2%; per-cell TOST p, Holm-adjusted TOST
                     and Holm-adjusted DM p over the available family; near-margin flags; labels
  RA5 denominator    CI of the percent gain 100*G/WIS(L3) with WIS(L3) estimated (delta method:
                     EWC + HLN on the linearised weekly series (d_t - R w_t)/mean(w)) vs fixed
  RA6 bootstrap      52-week circular block bootstrap of the SAME week-weighted quantity as the
                     primary (bootstrap over the pooled weekly series; no state clusters)
  RA7 casescale      the three gains on case-scale WIS (scores' wis_case: WIS of the expm1
                     back-transformed, clipped-at-0, sorted quantiles = the forecast files);
                     coverage 40/80% on positive-case weeks; mean 40/80% interval width; quantile
                     crossing / zero-floor counts and a WIS recomputation check on the forecasts
  RA8 absolute       WIS(L3), WIS(L4), WIS(L3+C*), WIS(L4+C*) (log1p and case scale) beside each
                     gain with n rows, n weeks, horizons, years, seeds, C*
Rows, exclusions and seeds come from scripts/run/estimands_report.load_cell; estimands from
pop.eval.estimands.compute_estimands_v2; WIS from pop.eval.scoring. Only the primary horizons
(manifest primary_horizons) are read. Per-cell results are cached in <out>/RA_cells/<cell>/
keyed on the scores files used, so a rerun only computes new or changed cells.
"""
from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import hashlib
import json
import os
import sys
import time
import traceback
from pathlib import Path

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_MAX_THREADS",
           "POLARS_MAX_THREADS"):
    os.environ.setdefault(_v, "4")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "analysis"))
sys.path.insert(0, str(ROOT / "scripts" / "run"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import pyarrow.parquet as pq  # noqa: E402
from scipy import stats as _st  # noqa: E402

import estimands_report as ER  # noqa: E402
import rk_cells as C  # noqa: E402
from rk_compute import _int_keys  # noqa: E402
from pop.eval import scoring  # noqa: E402
from pop.eval.estimands import ESTIMANDS, compute_estimands_v2, weekly_pooled  # noqa: E402
from pop.eval.stats import (block_bootstrap_means, classify_effect, ewc_inference, holm,  # noqa: E402
                            percentile_ci, tost_p)

VERSION = "1"
ROLE_LABEL = {"L3": "L3", "L4": "L4", "L3C": "L3+C*", "L4C": "L4+C*"}
FIELDS = ["estimate", "se", "df", "T", "p", "lo95", "hi95", "lo90", "hi90", "wis_ref",
          "margin", "pct_of_ref", "tost_p", "cls", "mde_pct", "n_rows", "n_weeks"]
MARGINS = (0.5, 1.0, 2.0)          # percent of WIS(L3)
NEAR_PP = 0.05                     # near-margin flag, percentage points
QLEVELS = np.array(scoring.PRIMARY_QUANTILES)


# ======================================================================== filters (tested)
def epi_year(d) -> pd.Series:
    """Epidemiological year of a week = calendar year of its Wednesday (pop.data.panel)."""
    return (pd.to_datetime(pd.Series(d)) + pd.Timedelta(days=3)).dt.year


def last_train_week(test_year: int, weekday: int = 6) -> pd.Timestamp:
    """Start of the last training-label week of the annual model for ``test_year``.

    Origin Y trains on target weeks of epi-years 2018..Y-1 (pop.splits.year_window +
    row_masks on the panel's epi-year), so its last label is the last week (start day
    ``weekday``, 6 = Sunday) whose epi-year is Y-1."""
    d = pd.Timestamp(f"{int(test_year)}-01-04")   # in epi-year Y whatever the weekday
    d = d - pd.Timedelta(days=(d.weekday() - weekday) % 7)  # week start containing/near it
    while (d + pd.Timedelta(days=3)).year >= int(test_year):
        d -= pd.Timedelta(days=7)
    return d


def admissible_mask(g: pd.DataFrame) -> np.ndarray:
    """True where the forecast origin is on/after the last training-label week of the model
    that scored the row (origin_week >= last_train_week(test_year)); the origin week's data
    are available at the origin, so origin == last label week is admissible."""
    wd = int(pd.to_datetime(g.target_week.iloc[0]).weekday()) if len(g) else 6
    lw = {y: last_train_week(y, wd) for y in pd.unique(g.test_year)}
    cut = g.test_year.map(lw)
    return (pd.to_datetime(g.origin_week) >= pd.to_datetime(cut)).to_numpy()


def strata3(g: pd.DataFrame) -> dict[str, np.ndarray]:
    """Three-way reporting/case status of each target row: cases > 0; recorded zero
    (cases == 0 and not zero-filled); zero-filled zero. Raises if a zero-filled row has cases."""
    zf = g.zero_filled.astype(bool).to_numpy()
    cases = g.cases.to_numpy(float)
    if np.any(zf & (cases > 0)):
        raise ValueError("zero-filled rows with positive cases")
    pos = cases > 0
    return {"positive": pos, "recorded_zero": (~pos) & (~zf), "zero_filled": zf}


def delta_ratio_ci(d, w, h: int) -> dict:
    """CI of R = mean(d)/mean(w) treating both as estimated: EWC + HLN inference on the
    linearised weekly series z_t = (d_t - R w_t) / mean(w) (delta method)."""
    d, w = np.asarray(d, float), np.asarray(w, float)
    ok = np.isfinite(d) & np.isfinite(w)
    d, w = d[ok], w[ok]
    R = d.mean() / w.mean()
    inf = ewc_inference((d - R * w) / w.mean(), h=h)
    t975, t95 = _st.t.ppf(0.975, inf.df), _st.t.ppf(0.95, inf.df)
    return {"ratio": R, "se": inf.se, "df": inf.df, "lo95": R - t975 * inf.se,
            "hi95": R + t975 * inf.se, "lo90": R - t95 * inf.se, "hi90": R + t95 * inf.se}


def weekly_frame(g: pd.DataFrame, cols) -> pd.DataFrame:
    """Primary weekly series (weekly_pooled) of each column, aligned on target week."""
    return pd.concat({c: weekly_pooled(g, c) for c in cols}, axis=1).dropna().rename_axis(
        "target_week").reset_index()


def week_bootstrap(g: pd.DataFrame, *, n_boot=2000, block_len=52, seed=0) -> dict:
    """52-week circular block bootstrap of the primary week-weighted estimates: resamples the
    pooled weekly series (one row per week), so the point estimate equals the primary one."""
    cols = list(ESTIMANDS) + ["wis_L3"]
    W = weekly_frame(g, cols)
    pt, reps = block_bootstrap_means(W, cols, cluster_col=None, time_col="target_week",
                                     block_len=block_len, n_boot=n_boot, seed=seed)
    out = {}
    for j, e in enumerate(ESTIMANDS):
        lo, hi = percentile_ci(reps[:, j])
        with np.errstate(invalid="ignore", divide="ignore"):
            plo, phi = percentile_ci(100 * reps[:, j] / reps[:, -1])
        out[e] = {"point": float(pt[j]), "pct": float(100 * pt[j] / pt[-1]), "boot_lo": lo,
                  "boot_hi": hi, "boot_lo_pct": plo, "boot_hi_pct": phi,
                  "boot_p2": float(2 * min((reps[:, j] <= 0).mean(), (reps[:, j] >= 0).mean())),
                  "n_weeks": int(len(W))}
    return out


def equivalence_label(est_pct, lo90_pct, hi90_pct, p_raw, p_holm, tost_holm, m) -> str:
    """Plain-language label (review comment 7). Positive gain = embeddings improve WIS."""
    sign = "positive" if est_pct > 0 else "negative"
    small = "small " if abs(est_pct) < m else ""
    if p_holm < 0.05:
        a = f"{small}{sign} difference, significant after Holm correction"
    elif p_raw < 0.05:
        a = f"nominal {small}{sign} difference, not significant after Holm correction"
    else:
        a = "no significant difference"
    inside = (lo90_pct > -m) and (hi90_pct < m)
    if inside and tost_holm < 0.05:
        b = f"within ±{m:g}% (TOST, Holm-adjusted)"
    elif inside:
        b = f"within ±{m:g}% (unadjusted TOST only)"
    else:
        b = f"not shown to be within ±{m:g}%"
    return f"{a}; {b}"


def near_margin(lo90_pct, hi90_pct, m, tol=NEAR_PP) -> bool:
    return bool(min(abs(lo90_pct + m), abs(hi90_pct - m)) < tol)


# ======================================================================== loading
def make_reader(metric: str = "wis_log", horizons=None):
    """Replacement for estimands_report.read_scores: same output, reads only ``horizons``
    and serves ``metric`` (e.g. wis_case) under the name wis_log."""
    def _read(dirs, cols=("wis_log", "cases", "cov_40", "cov_80")):
        out = []
        for d in map(Path, dirs):
            names = pq.ParquetFile(d / "scores.parquet").schema.names
            want = [metric if c == "wis_log" else c for c in cols]
            use = ER.KEYS + [c for c in dict.fromkeys(want) if c in names] + \
                [c for c in ("seed", "run") if c in names]
            filt = [("horizon", "in", [int(h) for h in horizons])] if horizons else None
            s = pd.read_parquet(d / "scores.parquet", columns=use, filters=filt)
            if metric != "wis_log" and "wis_log" in cols:
                s = s.rename(columns={metric: "wis_log"})
            if "seed" not in s:
                s["seed"] = 0
            s["seed"] = s.seed.astype(int)
            s["label"] = s["run"].astype(str) if "run" in s else d.name
            s["dir"] = d.name
            s["test_year"] = s.test_year.astype(int)
            s["unit_id"] = s.unit_id.astype(str)
            s["origin_week"] = pd.to_datetime(s.origin_week)
            s["target_week"] = pd.to_datetime(s.target_week)
            s["horizon"] = s.horizon.astype(int)
            out.append(s.drop(columns=[c for c in ("run",) if c in s]))
        return pd.concat(out, ignore_index=True)
    return _read


@contextlib.contextmanager
def patched_reader(metric, horizons):
    orig = ER.read_scores
    ER.read_scores = make_reader(metric, horizons)
    try:
        yield
    finally:
        ER.read_scores = orig


def load(cell, metric="wis_log", horizons=None, exclude_weeks=ER.DEFAULT_WEEKS):
    roles = {r: cell["roles"][r]["dirs"] for r in C.ROLES}
    with patched_reader(metric, horizons):
        return ER.load_cell(roles, exclude_weeks=exclude_weeks)


def est_all(g) -> dict:
    r = compute_estimands_v2(g, bootstrap=False)
    return {e: {f: r[e].get(f, np.nan) for f in FIELDS} for e in ESTIMANDS}


def flat(prefix: dict, res: dict) -> list[dict]:
    return [{**prefix, "estimand": e, **v} for e, v in res.items()]


# ======================================================================== per-row joins
class KeyMap:
    """Map rows of another frame onto the rows of g by (unit, origin, test_year, horizon)."""

    def __init__(self, g):
        self.units = pd.Index(sorted(g.unit_id.astype(str).unique()))
        k = _int_keys(g, self.units)
        self.order = np.argsort(k)
        self.ks = k[self.order]
        self.n = len(g)

    def pos(self, df):
        k = _int_keys(df, self.units)
        p = np.clip(np.searchsorted(self.ks, k), 0, self.n - 1)
        ok = (k >= 0) & (self.ks[p] == k)
        return self.order[p[ok]], ok

    def seed_mean(self, idx_vals: list[tuple[np.ndarray, np.ndarray]]) -> np.ndarray:
        """Average of the values mapped to each g row (seed-averaged); NaN if none."""
        s = np.zeros(self.n)
        c = np.zeros(self.n)
        for idx, v in idx_vals:
            np.add.at(s, idx, v)
            np.add.at(c, idx, 1.0)
        with np.errstate(invalid="ignore", divide="ignore"):
            return s / c


def role_coverage(km: KeyMap, dirs, horizons) -> dict:
    s = make_reader("wis_log", horizons)(dirs, cols=("cov_40", "cov_80"))
    idx, ok = km.pos(s)
    return {c: km.seed_mean([(idx, s[c].to_numpy(float)[ok])]) for c in ("cov_40", "cov_80")}


def scan_forecasts(km: KeyMap, dirs, horizons, check_wis=True) -> tuple[dict, dict]:
    """Interval widths per g row (seed-averaged) + quantile checks from the chunk forecast
    files of the primary horizons. Returns (row arrays, counts)."""
    cnt = {"n_forecasts": 0, "n_crossing": 0, "n_nan": 0, "n_q_at_zero": 0, "n_all_zero": 0,
           "n_q10_zero": 0, "pattern_ok": True, "chunk_rows_match": True, "n_chunks": 0,
           "wis_check_rows": 0, "wis_log_maxdiff": 0.0, "wis_case_maxdiff": 0.0}
    acc = {c: [] for c in ("w80_case", "w40_case", "w80_log", "w40_log")}
    i10, i30, i70, i90 = (int(np.argmin(abs(QLEVELS - q))) for q in (0.1, 0.3, 0.7, 0.9))
    for d in map(Path, dirs):
        files = sorted((d / "chunks").glob("*.forecasts.parquet"))
        tot = sum(pq.ParquetFile(f).metadata.num_rows for f in files)
        if tot != pq.ParquetFile(d / "forecasts.parquet").metadata.num_rows:
            cnt["chunk_rows_match"] = False
        checked = False
        for f in files:
            if not any(f.name.endswith(f"__h{h}.forecasts.parquet") for h in horizons):
                continue
            fc = pd.read_parquet(f, columns=["unit_id", "origin_week", "target_week", "test_year",
                                             "horizon", "quantile", "value"])
            k = len(QLEVELS)
            if len(fc) % k or not np.allclose(fc["quantile"].to_numpy().reshape(-1, k),
                                              QLEVELS[None, :]):
                cnt["pattern_ok"] = False
                continue
            V = fc["value"].to_numpy(float).reshape(-1, k)
            keys = fc.iloc[::k][["unit_id", "origin_week", "target_week", "test_year",
                                 "horizon"]].reset_index(drop=True)
            cnt["n_chunks"] += 1
            cnt["n_forecasts"] += len(V)
            cnt["n_crossing"] += int(np.any(np.diff(V, axis=1) < 0, axis=1).sum())
            cnt["n_nan"] += int(np.isnan(V).any(axis=1).sum())
            cnt["n_q_at_zero"] += int((V == 0).sum())
            cnt["n_all_zero"] += int((V == 0).all(axis=1).sum())
            cnt["n_q10_zero"] += int((V[:, i10] == 0).sum())
            idx, ok = km.pos(keys)
            L = np.log1p(V)
            for c, val in (("w80_case", V[:, i90] - V[:, i10]), ("w40_case", V[:, i70] - V[:, i30]),
                           ("w80_log", L[:, i90] - L[:, i10]), ("w40_log", L[:, i70] - L[:, i30])):
                acc[c].append((idx, val[ok]))
            if check_wis and not checked:
                sf = f.with_name(f.name.replace(".forecasts.", ".scores."))
                if sf.exists():
                    sc = pd.read_parquet(sf, columns=["unit_id", "origin_week", "target_week",
                                                      "horizon", "cases", "wis_log", "wis_case"])
                    m = keys.reset_index().merge(sc, on=["unit_id", "origin_week", "target_week",
                                                        "horizon"], how="inner")
                    Vm = V[m["index"].to_numpy()]
                    y = m.cases.to_numpy(float)
                    wl = scoring.wis_interval(y, QLEVELS, Vm, log1p=True)
                    wc = scoring.wis_interval(y, QLEVELS, Vm, log1p=False)
                    cnt["wis_check_rows"] += len(m)
                    cnt["wis_log_maxdiff"] = max(cnt["wis_log_maxdiff"],
                                                 float(np.nanmax(abs(wl - m.wis_log.to_numpy()))))
                    cnt["wis_case_maxdiff"] = max(cnt["wis_case_maxdiff"],
                                                  float(np.nanmax(abs(wc - m.wis_case.to_numpy()))))
                    checked = True
            del fc, V, L, keys
    return {c: km.seed_mean(v) for c, v in acc.items()}, cnt


# ======================================================================== one cell
def cell_key(cell, opts) -> str:
    parts = {"v": VERSION, "opts": opts, "cstar": cell.get("cstar"),
             "roles": {r: [C.run_fingerprint(d) for d in cell["roles"][r]["dirs"]] for r in C.ROLES},
             "excl": [str(p) for p in (ER.DEFAULT_UNITS, ER.DEFAULT_WEEKS)]
             + [Path(p).stat().st_mtime_ns for p in (ER.DEFAULT_UNITS, ER.DEFAULT_WEEKS)]}
    return hashlib.sha1(json.dumps(parts, sort_keys=True, default=str).encode()).hexdigest()[:16]


def wis_abs(g, cols=("wis_L3", "wis_L4", "wis_L3C", "wis_L4C")) -> dict:
    return {c: float(weekly_pooled(g, c).mean()) for c in cols}


def compute_cell(cell, *, n_boot=2000, scan=True, log=print) -> dict:
    cid = cell["id"]
    hp = list(cell["primary_horizons"])
    hmax = max(hp)
    t0 = time.time()
    lab = {"cell": cid, "cstar": cell.get("cstar")}
    out = {}

    # ---- primary rows (log1p WIS, default exclusions)
    g, info = load(cell, "wis_log", hp)
    log(f"  {cid}: loaded {len(g):,} rows ({time.time() - t0:.0f}s)")
    prim = est_all(g)
    out["primary"] = flat({**lab, "analysis": "primary"}, prim)
    yrs = sorted(int(y) for y in g.test_year.unique())
    seeds = [int(s) for s in g.attrs.get("seeds", [])]

    # RA8 absolute WIS (log)
    ab = wis_abs(g)
    out["absolute"] = [{**lab, "scale": "log1p", **{f"WIS_{ROLE_LABEL[r]}": ab[f"wis_{r}"] for r in C.ROLES},
                        **{f"{e}": prim[e]["estimate"] for e in ESTIMANDS},
                        **{f"{e}_pct": prim[e]["pct_of_ref"] for e in ESTIMANDS},
                        **{f"{e}_lo95": prim[e]["lo95"] for e in ESTIMANDS},
                        **{f"{e}_hi95": prim[e]["hi95"] for e in ESTIMANDS},
                        "n_rows": len(g), "n_weeks": prim["G_excess"]["n_weeks"],
                        "n_units": int(g.unit_id.nunique()),
                        "horizons": ",".join(map(str, hp)), "years": f"{yrs[0]}-{yrs[-1]}" if yrs else "",
                        "n_years": len(yrs), "seeds": ",".join(map(str, seeds))}]

    # RA1 three-way strata
    rows = []
    for name, m in strata3(g).items():
        sub = g[m]
        base = {**lab, "stratum": name, "share_rows": float(m.mean()), "rows": int(m.sum()),
                "weeks": int(sub.target_week.nunique())}
        if m.sum() == 0 or sub.target_week.nunique() < 10:
            rows += [{**base, "estimand": e, "note": "too few rows/weeks"} for e in ESTIMANDS]
            continue
        r = est_all(sub)
        absr = wis_abs(sub)
        rows += [{**base, "estimand": e, **v, **{f"WIS_{ROLE_LABEL[k]}": absr[f"wis_{k}"]
                                                for k in C.ROLES}} for e, v in r.items()]
    out["strata3"] = rows

    # RA2 look-ahead (training-label cutoff)
    adm = admissible_mask(g)
    drop_h = {int(h): float(1 - adm[g.horizon.to_numpy() == h].mean()) for h in hp}
    r = est_all(g[adm])
    out["lookahead"] = [{**lab, "pct_rows_dropped": 100 * float(1 - adm.mean()),
                         **{f"pct_dropped_h{h}": 100 * v for h, v in drop_h.items()},
                         "rows_kept": int(adm.sum()), "estimand": e, **v} for e, v in r.items()]

    # RA5 denominator uncertainty, RA6 week bootstrap
    W = weekly_frame(g, list(ESTIMANDS) + ["wis_L3"])
    rows = []
    for e in ESTIMANDS:
        p = prim[e]
        dr = delta_ratio_ci(W[e], W["wis_L3"], hmax)
        rows.append({**lab, "estimand": e, "pct": 100 * dr["ratio"],
                     "fixed_lo95_pct": 100 * p["lo95"] / p["wis_ref"],
                     "fixed_hi95_pct": 100 * p["hi95"] / p["wis_ref"],
                     "fixed_lo90_pct": 100 * p["lo90"] / p["wis_ref"],
                     "fixed_hi90_pct": 100 * p["hi90"] / p["wis_ref"],
                     "delta_lo95_pct": 100 * dr["lo95"], "delta_hi95_pct": 100 * dr["hi95"],
                     "delta_lo90_pct": 100 * dr["lo90"], "delta_hi90_pct": 100 * dr["hi90"],
                     "fixed_se_pct": 100 * p["se"] / p["wis_ref"], "delta_se_pct": 100 * dr["se"],
                     "se_ratio_delta_over_fixed": dr["se"] / (p["se"] / p["wis_ref"]),
                     "wis_ref": p["wis_ref"],
                     "wis_ref_se_rel": float(ewc_inference(W["wis_L3"].to_numpy(), h=hmax).se
                                             / p["wis_ref"])})
    out["denominator"] = rows
    if n_boot:
        bs = week_bootstrap(g, n_boot=n_boot)
        out["bootstrap"] = [{**lab, "estimand": e, **v, "primary": prim[e]["estimate"],
                             "primary_lo95": prim[e]["lo95"], "primary_hi95": prim[e]["hi95"],
                             "primary_p": prim[e]["p"], "n_boot": n_boot, "block_len": 52}
                            for e, v in bs.items()]
        for e in ESTIMANDS:
            assert np.isclose(bs[e]["point"], prim[e]["estimate"], rtol=1e-9, atol=1e-12), e

    # RA7 coverage / widths / forecast checks
    km = KeyMap(g)
    pos = g.cases.to_numpy(float) > 0
    outb = g.outbreak.to_numpy(bool)
    cov_rows, chk_rows = [], []
    for r in C.ROLES:
        dirs = cell["roles"][r]["dirs"]
        cv = role_coverage(km, dirs, hp)
        row = {**lab, "model": ROLE_LABEL[r], "rows": len(g), "rows_positive": int(pos.sum()),
               "rows_outbreak": int(outb.sum())}
        for c in ("cov_40", "cov_80"):
            row[f"{c}_all"] = float(np.nanmean(cv[c]))
            row[f"{c}_positive"] = float(np.nanmean(cv[c][pos])) if pos.any() else np.nan
            row[f"{c}_outbreak"] = float(np.nanmean(cv[c][outb])) if outb.any() else np.nan
        if scan:
            wd, ck = scan_forecasts(km, dirs, hp)
            for c, v in wd.items():
                row[f"mean_{c}_all"] = float(np.nanmean(v))
                row[f"mean_{c}_positive"] = float(np.nanmean(v[pos])) if pos.any() else np.nan
                row[f"rows_missing_width"] = int(np.isnan(v).sum())
            chk_rows.append({**lab, "model": ROLE_LABEL[r], **ck})
            del wd
        cov_rows.append(row)
        log(f"  {cid}: coverage/widths {r} ({time.time() - t0:.0f}s)")
    out["coverage"] = cov_rows
    out["forecast_checks"] = chk_rows
    excl_weeks = info["excluded"].get("incomplete_weeks")
    out["info"] = {"rows": len(g), "excluded": info["excluded"], "seeds": seeds, "years": yrs,
                   "horizons": hp}
    del g, km, W

    # RA3 no quality exclusions (only reloaded when the flags removed rows)
    if isinstance(excl_weeks, int) and excl_weeks > 0:
        g2, info2 = load(cell, "wis_log", hp, exclude_weeks=None)
        r = est_all(g2)
        n2 = len(g2)
        del g2
    else:
        r, n2 = prim, out["info"]["rows"]
    out["noqual"] = [{**lab, "incomplete_week_rows_restored": excl_weeks, "rows": n2,
                      "estimand": e, **v} for e, v in r.items()]

    # RA7 case scale
    gc, _ = load(cell, "wis_case", hp)
    rc = est_all(gc)
    abc = wis_abs(gc)
    out["casescale"] = [{**lab, "estimand": e, **v} for e, v in rc.items()]
    out["absolute"].append({**lab, "scale": "case", **{f"WIS_{ROLE_LABEL[r]}": abc[f"wis_{r}"]
                                                      for r in C.ROLES},
                            **{e: rc[e]["estimate"] for e in ESTIMANDS},
                            **{f"{e}_pct": rc[e]["pct_of_ref"] for e in ESTIMANDS},
                            **{f"{e}_lo95": rc[e]["lo95"] for e in ESTIMANDS},
                            **{f"{e}_hi95": rc[e]["hi95"] for e in ESTIMANDS},
                            "n_rows": len(gc), "n_weeks": rc["G_excess"]["n_weeks"],
                            "n_units": int(gc.unit_id.nunique()),
                            "horizons": ",".join(map(str, hp)),
                            "years": f"{yrs[0]}-{yrs[-1]}" if yrs else "", "n_years": len(yrs),
                            "seeds": ",".join(map(str, seeds))})
    del gc
    out["info"]["seconds"] = round(time.time() - t0, 1)
    log(f"  {cid}: done in {time.time() - t0:.0f}s")
    return out


# ======================================================================== family level
def equivalence_table(prim: pd.DataFrame) -> pd.DataFrame:
    """RA4 from the primary G_excess rows (one per available cell)."""
    p = prim[prim.estimand == "G_excess"].copy().reset_index(drop=True)
    w = p.wis_ref.astype(float)
    for c in ("lo95", "hi95", "lo90", "hi90"):
        p[f"{c}_pct"] = 100 * p[c].astype(float) / w
    p["p_holm_dm"] = holm(p.p.astype(float).to_numpy())
    p["n_family_available"] = len(p)
    p["class_1pct_primary_rule"] = [
        classify_effect(a, b, c, d, pp, 0.01 * ww)
        for a, b, c, d, pp, ww in zip(p.lo95, p.hi95, p.lo90, p.hi90, p.p, w)]
    for m in MARGINS:
        tag = f"{m:g}".replace(".", "p")
        tp = [tost_p(e, s, df, m / 100 * ww) for e, s, df, ww in zip(p.estimate, p.se, p.df, w)]
        p[f"tost_p_{tag}_unadj"] = tp
        p[f"tost_p_{tag}_holm"] = holm(np.asarray(tp))
        p[f"within_{tag}_unadj"] = (p.lo90_pct > -m) & (p.hi90_pct < m)
        p[f"within_{tag}_holm"] = p[f"tost_p_{tag}_holm"] < 0.05
        p[f"near_margin_{tag}"] = [near_margin(a, b, m) for a, b in zip(p.lo90_pct, p.hi90_pct)]
        p[f"label_{tag}"] = [equivalence_label(e, a, b, pr, ph, th, m) for e, a, b, pr, ph, th in
                             zip(p.pct_of_ref, p.lo90_pct, p.hi90_pct, p.p, p.p_holm_dm,
                                 p[f"tost_p_{tag}_holm"])]
    keep = ["cell", "cstar", "estimate", "pct_of_ref", "se", "df", "p", "p_holm_dm", "lo95_pct",
            "hi95_pct", "lo90_pct", "hi90_pct", "class_1pct_primary_rule", "n_family_available"]
    keep += [c for c in p.columns if c.startswith(("tost_p_", "within_", "near_margin_", "label_"))]
    return p[keep]


def change_flags(prim: pd.DataFrame, alt: pd.DataFrame, estimand="G_excess") -> list[str]:
    """Cells whose sign, DM significance (p < .05) or 1%-rule class differs from the primary."""
    a = prim[prim.estimand == estimand].set_index("cell")
    b = alt[alt.estimand == estimand].set_index("cell")
    out = []
    for c in a.index.intersection(b.index):
        x, y = a.loc[c], b.loc[c]
        diffs = []
        if np.sign(x.estimate) != np.sign(y.estimate):
            diffs.append("sign")
        if (x.p < .05) != (y.p < .05):
            diffs.append(f"DM p {x.p:.3f}->{y.p:.3f}")
        if x.cls != y.cls:
            diffs.append(f"class {x.cls}->{y.cls}")
        if diffs:
            out.append(f"{c} ({', '.join(diffs)})")
    return out


def fmt_pct(v, nd=2):
    return "nan" if not np.isfinite(v) else f"{v:+.{nd}f}%"


def write_summary(T: dict, out: Path, pending: list[str], cells: list[str]) -> None:
    P = T["primary"]
    pe = P[P.estimand == "G_excess"].set_index("cell")
    L = [f"# Review sensitivity analyses (RA1-RA8), scoring only",
         "",
         f"Generated {dt.datetime.now():%Y-%m-%d %H:%M} by `scripts/analysis/review_sens.py` from the "
         f"existing forecast/score files; no model was refitted. Cells analysed ({len(cells)}): "
         f"{', '.join(cells)}. Pending (skipped): {', '.join(pending) or 'none'}. Primary horizons "
         "h{1,4} pooled; gains are % of WIS(L3) with WIS computed on log(1+cases) unless stated; "
         "positive = embeddings improve. Primary G_excess (95% CI, DM p): "
         + "; ".join(f"{c} {fmt_pct(r.pct_of_ref)} [{fmt_pct(100*r.lo95/r.wis_ref)}, "
                     f"{fmt_pct(100*r.hi95/r.wis_ref)}] p={r.p:.3g}" for c, r in pe.iterrows()) + ".",
         ""]

    # RA1
    S = T["strata3"]
    s = S[S.estimand == "G_excess"]
    L += ["## RA1 Three-way strata (`RA_strata3.csv`)", ""]
    parts = []
    for c in cells:
        x = s[s.cell == c].set_index("stratum")
        parts.append(f"{c}: " + ", ".join(
            f"{k} {100*x.loc[k,'share_rows']:.0f}% rows {fmt_pct(x.loc[k,'pct_of_ref']) if 'pct_of_ref' in x and np.isfinite(x.loc[k,'pct_of_ref']) else 'n/a'}"
            + (f" (p={x.loc[k,'p']:.2g})" if 'p' in x and np.isfinite(x.loc[k, 'p']) else "")
            for k in ("positive", "recorded_zero", "zero_filled") if k in x.index))
    L += ["G_excess by stratum (stratum gain as % of the stratum's own WIS(L3); share of rows): "
          + "; ".join(parts) + ". Recorded zeros exist only where the source lists zero weeks "
          "(Brazil 2020-21 test years); elsewhere the zero stratum is entirely zero-filled.", ""]

    # RA2
    la = T["lookahead"]
    lg = la[la.estimand == "G_excess"].set_index("cell")
    L += ["## RA2 Training-label look-ahead exclusion (`RA_lookahead.csv`)", "",
          "Each annual model for test year Y is trained on target weeks of epi-years 2018..Y-1, so "
          "its last training label is the last week of epi-year Y-1. Rows whose origin week "
          "precedes that week (h4 targets in the first three weeks of each test year; no h1 row) "
          f"were dropped for all four models. Rows dropped: {lg.pct_rows_dropped.min():.2f}-"
          f"{lg.pct_rows_dropped.max():.2f}%. G_excess: "
          + "; ".join(f"{c} {fmt_pct(r.pct_of_ref)} (p={r.p:.3g}, primary {fmt_pct(pe.loc[c,'pct_of_ref'])})"
                      for c, r in lg.iterrows()) + ". Conclusion changes: "
          + (", ".join(change_flags(P, la)) or "none") + ". The annual-feature cutoff "
          "(yearly_ref: origin) is a separate refit sensitivity (BR S1, G_emb only) and is not "
          "covered here.", ""]

    # RA3
    nq = T["noqual"]
    ng = nq[nq.estimand == "G_excess"].set_index("cell")
    restored = ng.incomplete_week_rows_restored
    L += ["## RA3 No quality exclusions (`RA_noqual.csv`)", "",
          "Incomplete-week flags removed (no-geometry units still excluded; flag_gap weeks are "
          "dropped by the runner at scoring and cannot be restored). Rows restored per cell: "
          + ", ".join(f"{c} {v}" for c, v in restored.items()) + ". G_excess changes only where "
          "rows were restored: " + "; ".join(
              f"{c} {fmt_pct(r.pct_of_ref)} (p={r.p:.3g})" for c, r in ng.iterrows()
              if isinstance(restored[c], (int, np.integer)) and restored[c] > 0)
          + ". Conclusion changes: " + (", ".join(change_flags(P, nq)) or "none") + ".", ""]

    # RA4
    E = T["equivalence"]
    L += ["## RA4 Equivalence and multiplicity (`RA_equivalence.csv`)", "",
          f"From unrounded 90% CIs over the {len(E)} available cells (Holm m = {len(E)}; the "
          "predeclared family has 14). "]
    for m in MARGINS:
        tag = f"{m:g}".replace(".", "p")
        L[-1] += (f"±{m:g}%: {int(E[f'within_{tag}_unadj'].sum())} cells within unadjusted, "
                  f"{int(E[f'within_{tag}_holm'].sum())} after Holm-adjusted TOST"
                  + (f"; near the margin (<{NEAR_PP} pp): "
                     + ", ".join(E.cell[E[f'near_margin_{tag}']]) if E[f'near_margin_{tag}'].any() else "")
                  + ". ")
    L[-1] += ("DM p < .05 unadjusted: " + (", ".join(E.cell[E.p < .05]) or "none") + "; after Holm: "
              + (", ".join(E.cell[E.p_holm_dm < .05]) or "none") + ". Labels at ±1%: "
              + "; ".join(f"{c}: {l}" for c, l in zip(E.cell, E.label_1)) + ".")
    L += [""]

    # RA5
    D = T["denominator"]
    dg = D[D.estimand == "G_excess"].set_index("cell")
    L += ["## RA5 Denominator uncertainty (`RA_denominator.csv`)", "",
          "Delta-method CI of 100*G_excess/WIS(L3) with WIS(L3) estimated (EWC + HLN on the "
          "linearised weekly series) vs the fixed-denominator CI. SE ratio delta/fixed: "
          f"{dg.se_ratio_delta_over_fixed.min():.3f}-{dg.se_ratio_delta_over_fixed.max():.3f}. "
          "Largest change in a 95% bound: "
          f"{np.nanmax(np.abs(np.r_[dg.delta_lo95_pct - dg.fixed_lo95_pct, dg.delta_hi95_pct - dg.fixed_hi95_pct])):.3f} pp. "
          "Cells whose ±1% 90% classification differs: "
          + (", ".join(c for c, r in dg.iterrows()
                       if ((r.fixed_lo90_pct > -1) & (r.fixed_hi90_pct < 1))
                       != ((r.delta_lo90_pct > -1) & (r.delta_hi90_pct < 1))) or "none") + ".", ""]

    # RA6
    if "bootstrap" in T:
        B = T["bootstrap"]
        bg = B[B.estimand == "G_excess"].set_index("cell")
        disagree = [c for c, r in bg.iterrows()
                    if (r.boot_lo > 0 or r.boot_hi < 0) != (r.primary_lo95 > 0 or r.primary_hi95 < 0)]
        L += ["## RA6 Week-weighted 52-week block bootstrap (`RA_bootstrap.csv`)", "",
              "Circular 52-week blocks over the pooled weekly series, so the bootstrap estimates "
              "exactly the primary week-weighted quantity (point estimates equal the primary, "
              "checked). G_excess 95% percentile CIs (% WIS(L3), ratio resampled jointly): "
              + "; ".join(f"{c} [{fmt_pct(r.boot_lo_pct)}, {fmt_pct(r.boot_hi_pct)}]"
                          for c, r in bg.iterrows())
              + ". Cells where bootstrap and DM/EWC disagree on whether 0 is excluded: "
              + (", ".join(disagree) or "none") + ".", ""]

    # RA7
    K = T["casescale"]
    kg = K[K.estimand == "G_excess"].set_index("cell")
    ke = K[K.estimand == "G_emb"].set_index("cell")
    CV = T["coverage"]
    ck = T.get("forecast_checks")
    L += ["## RA7 Case-scale WIS, coverage on positive weeks, interval checks "
          "(`RA_casescale.csv`, `RA_coverage_width.csv`, `RA_forecast_checks.csv`)", "",
          "Case-scale G_excess (% of case-scale WIS(L3), p): "
          + "; ".join(f"{c} {fmt_pct(r.pct_of_ref)} (p={r.p:.2g})" for c, r in kg.iterrows())
          + ". Case-scale G_emb: " + "; ".join(f"{c} {fmt_pct(r.pct_of_ref)} (p={r.p:.2g})"
                                              for c, r in ke.iterrows()) + ". "]
    l4 = CV[CV.model == "L4+C*"].set_index("cell")
    L[-1] += ("80% coverage of L4+C* overall vs positive-case weeks: "
              + "; ".join(f"{c} {r.cov_80_all:.2f} vs {r.cov_80_positive:.2f} (40%: "
                          f"{r.cov_40_all:.2f} vs {r.cov_40_positive:.2f})" for c, r in l4.iterrows()) + ". ")
    if "mean_w80_case_positive" in l4:
        L[-1] += ("Mean 80% interval width on positive weeks (cases; log1p): "
                  + "; ".join(f"{c} {r.mean_w80_case_positive:.1f}; {r.mean_w80_log_positive:.2f}"
                              for c, r in l4.iterrows()) + ". ")
    if ck is not None and len(ck):
        L[-1] += (f"Forecast files: {int(ck.n_forecasts.sum()):,} forecasts scanned, "
                  f"{int(ck.n_crossing.sum())} with quantile crossing, {int(ck.n_nan.sum())} with NaN; "
                  f"{100*ck.n_all_zero.sum()/max(ck.n_forecasts.sum(),1):.1f}% have all nine quantiles at the "
                  f"zero floor and {100*ck.n_q10_zero.sum()/max(ck.n_forecasts.sum(),1):.1f}% a zero 10% "
                  "quantile (models predict log1p; expm1 values below 0 are clipped to 0, then sorted). "
                  f"WIS recomputed from the forecast files matches the stored scores to "
                  f"{max(ck.wis_log_maxdiff.max(), 0):.1e} (log1p) / {ck.wis_case_maxdiff.max():.1e} "
                  f"(case) over {int(ck.wis_check_rows.sum()):,} rows; quantile-level pattern OK: "
                  f"{bool(ck.pattern_ok.all())}; chunk files = forecasts.parquet rows: "
                  f"{bool(ck.chunk_rows_match.all())}.")
    L += [""]

    # RA8
    A = T["absolute"]
    al = A[A.scale == "log1p"].set_index("cell")
    L += ["## RA8 Absolute WIS (`RA_absolute_wis.csv`)", "",
          "Week-weighted mean WIS on log(1+cases), L3 / L4 / L3+C* / L4+C*: "
          + "; ".join(f"{c} ({r.cstar}) {r['WIS_L3']:.4f}/{r['WIS_L4']:.4f}/{r['WIS_L3+C*']:.4f}/"
                      f"{r['WIS_L4+C*']:.4f}, n={int(r.n_rows):,} rows, {int(r.n_weeks)} wk, "
                      f"{r.years}, seeds {r.seeds}" for c, r in al.iterrows())
          + ". The case-scale rows of the same file give the raw-count WIS.", ""]
    (out / "RA_summary.md").write_text("\n".join(L))


# ======================================================================== main
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", default=None)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--n-boot", type=int, default=2000)
    ap.add_argument("--no-forecast-scan", action="store_true")
    ap.add_argument("--out", default="docs/results/review")
    ap.add_argument("--manifest", default="configs/primary_cells.yaml")
    a = ap.parse_args()
    os.chdir(ROOT)
    out = Path(a.out)
    cache = out / "RA_cells"
    cache.mkdir(parents=True, exist_ok=True)
    reg = [c for c in C.build_registry(a.manifest) if c["group"] == "primary"]
    opts = {"n_boot": a.n_boot, "scan": not a.no_forecast_scan}
    avail, pending = [], []
    for c in reg:
        st, _ = C.cell_status(c)
        if st == "available" and c.get("cstar"):
            avail.append(c)
        else:
            pending.append(c["id"])
    print(f"available: {[c['id'] for c in avail]}; pending: {pending}", flush=True)
    results = {}
    for c in avail:
        cdir = cache / c["id"]
        key = cell_key(c, opts)
        kf = cdir / "key.txt"
        if c["id"] in (a.only or [c["id"]]) and (a.force or not kf.exists()
                                                 or kf.read_text().strip() != key):
            try:
                res = compute_cell(c, n_boot=a.n_boot, scan=not a.no_forecast_scan,
                                   log=lambda m: print(m, flush=True))
            except Exception:  # noqa: BLE001 - one bad cell must not stop the rest
                traceback.print_exc()
                continue
            cdir.mkdir(exist_ok=True)
            (cdir / "result.json").write_text(json.dumps(res, default=lambda o: o.item()
                                                         if hasattr(o, "item") else str(o)))
            kf.write_text(key)
        if (cdir / "result.json").exists() and kf.exists() and kf.read_text().strip() == key:
            results[c["id"]] = json.loads((cdir / "result.json").read_text())
    cells = [c["id"] for c in avail if c["id"] in results]
    if not cells:
        print("no results")
        return
    T = {}
    for name in ("primary", "strata3", "lookahead", "noqual", "denominator", "bootstrap",
                 "casescale", "coverage", "forecast_checks", "absolute"):
        rows = [r for c in cells for r in results[c].get(name, [])]
        if rows:
            T[name] = pd.DataFrame(rows)
    T["equivalence"] = equivalence_table(T["primary"])
    files = {"strata3": "RA_strata3.csv", "lookahead": "RA_lookahead.csv",
             "noqual": "RA_noqual.csv", "equivalence": "RA_equivalence.csv",
             "denominator": "RA_denominator.csv", "bootstrap": "RA_bootstrap.csv",
             "casescale": "RA_casescale.csv", "coverage": "RA_coverage_width.csv",
             "forecast_checks": "RA_forecast_checks.csv", "absolute": "RA_absolute_wis.csv",
             "primary": "RA_primary_check.csv"}
    for k, f in files.items():
        if k in T:
            T[k].to_csv(out / f, index=False)
    # cross-check against the results kit cache (primary pooled G_excess)
    chk = []
    for c in cells:
        f = ROOT / "runs/analysis_cache" / c / "est.parquet"
        if f.exists():
            e = pd.read_parquet(f)
            e = e[(e.estimand == "G_excess") & (e.horizon == "pooled") & (e.test_year == "pooled")
                  & (e.stratum == "all")]
            mine = T["primary"].query("cell == @c and estimand == 'G_excess'").estimate.iloc[0]
            if len(e):
                chk.append((c, float(e.estimate.iloc[0]), float(mine)))
    pd.DataFrame(chk, columns=["cell", "kit_estimate", "review_estimate"]).to_csv(
        out / "RA_kit_crosscheck.csv", index=False)
    write_summary(T, out, pending, cells)
    print(f"wrote {out}/RA_*.csv and RA_summary.md for {cells}")


if __name__ == "__main__":
    main()
