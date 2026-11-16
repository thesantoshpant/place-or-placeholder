"""Paper-1 estimands. Positive gain = improvement (lower WIS).

G_emb    = WIS(L3)    - WIS(L4)
G_id     = WIS(L3)    - WIS(L3+C*)
G_excess = WIS(L3+C*) - WIS(L4+C*)          (primary)
ID share = G_id / G_emb, reported only if the 95% CI of G_emb
           excludes 0 AND G_emb >= min_rel * WIS(L3); otherwise NaN, "not estimable".

Two layers:
- ``gain_frame`` / ``compute_estimands``: the original row-level frame and the 8-week
  cluster-block bootstrap CI (superseded; kept to reproduce the first Brazil S1 report).
- ``seed_gain_frame`` / ``infer_estimand`` / ``compute_estimands_v2``: the fixed inference
  policy (deviations rows 9, 11, 12, 16): DM/EWC primary CIs, TOST against a 1% margin, MDE,
  52-week bootstrap sensitivity and multi-seed handling.
"""
from __future__ import annotations

from typing import Sequence

import numpy as np
import pandas as pd

from .stats import (block_bootstrap_means, classify_effect, ewc_inference, percentile_ci,
                    pooled_horizon_series, tost_p)

ROLES = ("L3", "L4", "L3C", "L4C")
ESTIMANDS = {"G_emb": ("L3", "L4"), "G_id": ("L3", "L3C"), "G_excess": ("L3C", "L4C")}
KEYS = ("unit_id", "origin_week", "target_week", "horizon")


def select_best_control(
    scores: pd.DataFrame, candidates: Sequence[str], *, metric: str = "wis",
    model_col: str = "model", keys: Sequence[str] = KEYS,
) -> str:
    """C* = candidate (e.g. L3+control model) with lowest mean metric on rows
    scored for all candidates. Pass validation-period scores only."""
    keys = [k for k in keys if k in scores.columns]
    sub = scores[scores[model_col].isin(candidates)]
    w = sub.pivot_table(index=keys, columns=model_col, values=metric, aggfunc="first")
    w = w.reindex(columns=list(candidates)).dropna()
    if w.empty:
        raise ValueError("no rows scored for all candidates")
    return str(w.mean().idxmin())


def gain_frame(
    scores: pd.DataFrame, models: dict, *, metric: str = "wis", model_col: str = "model",
    keys: Sequence[str] = KEYS, extra_cols: Sequence[str] = (),
) -> pd.DataFrame:
    """Wide frame with wis_<role> for roles L3, L4, L3C, L4C and per-row gains.

    ``models`` maps role -> model name. Only rows scored by all four are kept.
    ``extra_cols`` (e.g. 'state') are carried along (must be constant per key).
    """
    keys = [k for k in keys if k in scores.columns]
    parts = None
    for role in ROLES:
        s = scores.loc[scores[model_col] == models[role], keys + list(extra_cols) + [metric]]
        s = s.rename(columns={metric: f"wis_{role}"})
        parts = s if parts is None else parts.merge(
            s.drop(columns=list(extra_cols)), on=keys, how="inner", validate="one_to_one")
    g = parts.dropna(subset=[f"wis_{r}" for r in ROLES]).copy()
    g["G_emb"] = g["wis_L3"] - g["wis_L4"]
    g["G_id"] = g["wis_L3"] - g["wis_L3C"]
    g["G_excess"] = g["wis_L3C"] - g["wis_L4C"]
    return g.reset_index(drop=True)


def id_share_gate(g_emb: float, lo: float, hi: float, wis_l3: float, min_rel: float = 0.01):
    """Return (estimable, reason)."""
    if not (lo > 0 or hi < 0):
        return False, "not estimable: G_emb 95% CI includes 0"
    if not g_emb >= min_rel * wis_l3:
        return False, f"not estimable: G_emb < {min_rel:.0%} of WIS(L3)"
    return True, ""


def compute_estimands(
    g: pd.DataFrame, *, cluster_col: str | None = "state", time_col: str = "target_week",
    block_len: int = 8, n_boot: int = 2000, seed: int = 0, alpha: float = 0.05,
    min_rel: float = 0.01, shared_time_blocks: bool = True,
) -> dict:
    """Point estimates + joint cluster block-bootstrap percentile CIs.

    Returns {name: {estimate, lo, hi}} for G_emb, G_id, G_excess, WIS_L3 and
    'ID_share' with an extra 'reason' ('' when reported).
    """
    cols = ["G_emb", "G_id", "G_excess", "wis_L3"]
    pt, reps = block_bootstrap_means(
        g, cols, cluster_col=cluster_col, time_col=time_col, block_len=block_len,
        n_boot=n_boot, seed=seed, shared_time_blocks=shared_time_blocks)
    res = {}
    for j, c in enumerate(cols):
        lo, hi = percentile_ci(reps[:, j], alpha)
        res[c if c != "wis_L3" else "WIS_L3"] = {"estimate": float(pt[j]), "lo": lo, "hi": hi}
    e = res["G_emb"]
    ok, reason = id_share_gate(e["estimate"], e["lo"], e["hi"], res["WIS_L3"]["estimate"], min_rel)
    if ok:
        with np.errstate(invalid="ignore", divide="ignore"):
            r = reps[:, 1] / reps[:, 0]
        lo, hi = percentile_ci(r, alpha)
        res["ID_share"] = {"estimate": float(pt[1] / pt[0]), "lo": lo, "hi": hi, "reason": ""}
    else:
        res["ID_share"] = {"estimate": np.nan, "lo": np.nan, "hi": np.nan, "reason": reason}
    return res



# ======================================================== inference policy v2 (2026-11-16)
def seed_wide(scores: pd.DataFrame, model: str, *, metric: str = "wis",
              model_col: str = "model", seed_col: str = "seed",
              keys: Sequence[str] = KEYS) -> pd.DataFrame:
    """Per-row losses of one model, one column per seed (index = keys).

    Raises if a (key, seed) pair occurs twice. Without ``seed_col`` the run counts as seed 0.
    Missing (row, seed) cells stay NaN here (see ``seed_gain_frame`` for the fill rule).
    """
    keys = [k for k in keys if k in scores.columns]
    s = scores.loc[scores[model_col] == model]
    if s.empty:
        raise ValueError(f"no rows for model {model!r}")
    seed = s[seed_col].astype(int) if seed_col in s.columns else pd.Series(0, index=s.index)
    s = s[keys + [metric]].assign(_seed=seed.to_numpy())
    dup = s.duplicated(keys + ["_seed"])
    if dup.any():
        raise ValueError(f"model {model!r}: {int(dup.sum())} duplicate (key, seed) rows")
    w = s.pivot(index=keys, columns="_seed", values=metric)
    w.columns = [int(c) for c in w.columns]
    return w


def seed_gain_frame(scores: pd.DataFrame, models: dict, *, metric: str = "wis",
                    model_col: str = "model", seed_col: str = "seed",
                    keys: Sequence[str] = KEYS, extra: pd.DataFrame | None = None) -> pd.DataFrame:
    """Row-level gain frame with seed handling (policy row 16; audit H3, M7).

    For each role (L3, L4, L3C, L4C -> model name in ``models``):
    - ``wis_<role>`` = the per-row loss averaged over the seeds present for that row
      (seed-averaged per-row loss); all primary inference uses these;
    - the per-seed loss for seed s is the role's own seed-s loss where it exists, otherwise
      that row's seed-averaged loss. This handles runs whose seed sets differ from their
      comparison run's (e.g. extra seeds only at h1/h4, or a single-seed reused run).
    Rows are the keys scored (with a non-NaN seed-averaged loss) by all four roles.
    Columns ``G_<e>`` (seed-averaged) and ``G_<e>@s`` / ``wis_L3@s`` for every seed s in the
    union of seeds, plus ``has@s`` = some role actually has seed s on the row.
    ``extra`` (indexed by ``keys``) is joined on (e.g. state, test_year, strata flags).
    """
    keys = [k for k in keys if k in scores.columns]
    wides = {r: seed_wide(scores, models[r], metric=metric, model_col=model_col,
                          seed_col=seed_col, keys=keys) for r in ROLES}
    idx = None
    for w in wides.values():
        ok = w.index[w.notna().any(axis=1)]
        idx = ok if idx is None else idx.intersection(ok)
    seeds = sorted(set().union(*[set(w.columns) for w in wides.values()]))
    g = pd.DataFrame(index=idx)
    per_seed = {}
    has = {s: np.zeros(len(idx), bool) for s in seeds}
    for r, w in wides.items():
        w = w.reindex(idx)
        mean = w.mean(axis=1)
        g[f"wis_{r}"] = mean.to_numpy()
        for s in seeds:
            if s in w.columns:
                has[s] |= w[s].notna().to_numpy()
                per_seed[(r, s)] = w[s].fillna(mean).to_numpy()
            else:
                per_seed[(r, s)] = mean.to_numpy()
    for e, (a, b) in ESTIMANDS.items():
        g[e] = g[f"wis_{a}"] - g[f"wis_{b}"]
    for s in seeds:
        for e, (a, b) in ESTIMANDS.items():
            g[f"{e}@{s}"] = per_seed[(a, s)] - per_seed[(b, s)]
        g[f"wis_L3@{s}"] = per_seed[("L3", s)]
        g[f"has@{s}"] = has[s]
    g = g.reset_index()
    if extra is not None:
        g = g.merge(extra, left_on=keys, right_index=True, how="left", validate="one_to_one")
    g.attrs["seeds"] = seeds
    return g


def weekly_pooled(g: pd.DataFrame, col: str, *, time_col: str = "target_week",
                  horizon_col: str = "horizon") -> pd.Series:
    """Weekly series behind every v2 estimate: per (horizon, target week) the cross-unit
    mean of ``col``; then, per week, the unweighted mean over the horizons present
    (one horizon -> the per-horizon weekly mean)."""
    wk = g.groupby([horizon_col, time_col], sort=True)[col].mean().rename(col).reset_index()
    return pooled_horizon_series(wk, col, time_col=time_col, horizon_col=horizon_col)


def infer_estimand(g: pd.DataFrame, estimand: str, *, ref_col: str = "wis_L3",
                   time_col: str = "target_week", horizon_col: str = "horizon",
                   margin_rel: float = 0.01, alpha: float = 0.05) -> dict:
    """Primary inference for one estimand on the rows of ``g`` (policy rows 9, 11, 16).

    Construction (identical for one horizon and for the pooled-over-horizons estimate):
    1. d_{h,t} = mean over units of the seed-averaged per-row gain at horizon h, week t;
    2. d_t = mean over the horizons present of d_{h,t} (pooled-h; equal horizon weights);
    3. DM on d_t: EWC long-run variance (B = floor(0.4 T^(2/3)), t_B reference) x HLN with
       h = the largest horizon in ``g``; se = se_EWC / HLN; CI95/CI90 = dbar -/+ t_B * se.
    Margin = margin_rel * WIS(ref), WIS(ref) = mean over weeks of the same pooled weekly mean
    of ``ref_col`` (the L3 / N3 loss). TOST p and class from ``stats.tost_p`` and
    ``stats.classify_effect``; MDE = (t_{B,.975} + t_{B,.80}) * se.
    Seeds: estimate_seed_<s> uses ``<estimand>@s``; seed_mean / seed_sd over the seeds that
    are actually present (``has@s``) on these rows; seed_sd is NaN with one seed.
    """
    hmax = int(g[horizon_col].max())
    d = weekly_pooled(g, estimand, time_col=time_col, horizon_col=horizon_col)
    inf = ewc_inference(d.to_numpy(), h=hmax)
    wis_ref = float(weekly_pooled(g, ref_col, time_col=time_col, horizon_col=horizon_col).mean())
    margin = margin_rel * wis_ref
    out = inf.to_dict()
    out.update(wis_ref=wis_ref, margin=margin, tost_p=tost_p(inf.estimate, inf.se, inf.df, margin),
               cls=classify_effect(inf.lo95, inf.hi95, inf.lo90, inf.hi90, inf.p, margin, alpha),
               pct_of_ref=100 * inf.estimate / wis_ref, mde_pct=100 * inf.mde / wis_ref,
               n_rows=len(g), n_weeks=int(d.size))
    seeds = [s for s in g.attrs.get("seeds", []) if f"has@{s}" in g and g[f"has@{s}"].any()]
    ests = {s: float(weekly_pooled(g, f"{estimand}@{s}", time_col=time_col,
                                   horizon_col=horizon_col).mean()) for s in seeds}
    out["n_seeds"] = len(ests)
    out["seed_estimates"] = ests
    out["seed_mean"] = float(np.mean(list(ests.values()))) if ests else np.nan
    out["seed_sd"] = float(np.std(list(ests.values()), ddof=1)) if len(ests) > 1 else np.nan
    return out


def compute_estimands_v2(g: pd.DataFrame, *, cluster_col: str | None = "state",
                         time_col: str = "target_week", horizon_col: str = "horizon",
                         block_len: int = 52, n_boot: int = 2000, seed: int = 0,
                         margin_rel: float = 0.01, min_rel: float = 0.01,
                         bootstrap: bool = True) -> dict:
    """All estimands under the v2 policy on the rows of ``g`` (from ``seed_gain_frame``).

    Returns {estimand: infer_estimand(...) + boot_lo/boot_hi} for G_emb, G_id, G_excess and
    'ID_share'. Bootstrap (sensitivity only): ``block_bootstrap_means`` on the seed-averaged
    row gains, states x ``block_len``-week circular blocks shared across states, percentile
    95% CI of the row-level mean. ID share = G_id / G_emb only if the primary (EWC) 95% CI of
    G_emb excludes 0 and G_emb >= min_rel * WIS(L3); its CI is the bootstrap ratio CI.
    """
    gc = g
    res = {e: infer_estimand(gc, e, time_col=time_col, horizon_col=horizon_col,
                             margin_rel=margin_rel) for e in ESTIMANDS}
    reps = None
    if bootstrap:
        pt, reps = block_bootstrap_means(gc, list(ESTIMANDS), cluster_col=cluster_col,
                                         time_col=time_col, block_len=block_len, n_boot=n_boot,
                                         seed=seed)
        for j, e in enumerate(ESTIMANDS):
            lo, hi = percentile_ci(reps[:, j])
            res[e].update(boot_lo=lo, boot_hi=hi, boot_point=float(pt[j]), block_len=block_len)
    e = res["G_emb"]
    ok, reason = id_share_gate(e["estimate"], e["lo95"], e["hi95"], e["wis_ref"], min_rel)
    if ok:
        sh = {"estimate": res["G_id"]["estimate"] / e["estimate"], "reason": ""}
        if reps is not None:
            with np.errstate(invalid="ignore", divide="ignore"):
                sh["boot_lo"], sh["boot_hi"] = percentile_ci(reps[:, 1] / reps[:, 0])
    else:
        sh = {"estimate": np.nan, "reason": reason}
    res["ID_share"] = sh
    return res
