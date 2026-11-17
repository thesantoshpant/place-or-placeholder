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
  policy (deviations rows 9, 11, 12, 16, 22): DM/EWC primary CIs, TOST against a 1% margin,
  MDE, 52-week circular bootstrap sensitivity and multi-seed handling (seeds common to both
  roles of each estimand; seed SD only where all of them exist).
"""
from __future__ import annotations

import warnings
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
                    keys: Sequence[str] = KEYS, extra: pd.DataFrame | None = None,
                    seed_policy: str = "common", on_mismatch: str = "warn") -> pd.DataFrame:
    """Row-level gain frame with seed handling (policy rows 16 and 22; audit4 M2).

    Rows are the keys scored (with a non-NaN loss for at least one seed) by all four roles
    (L3, L4, L3C, L4C -> model name in ``models``).

    Always present:
    - ``wis_<role>`` = the role's per-row loss averaged over the seeds it has on that row
      (used for WIS(ref) margins and ladders);
    - ``wis_L3@s`` = L3's seed-s loss; ``has@s`` = some role has seed s on the row.

    ``seed_policy="common"`` (default; deviations row 22): for estimand e = (a, b) and each
    row, only the seeds present for BOTH roles a and b are used:
    - ``G_<e>`` = mean over those common seeds of (loss_a,s - loss_b,s);
    - ``G_<e>@s`` = loss_a,s - loss_b,s where both roles have seed s, else NaN;
    - ``has_<e>@s`` = both roles have seed s on the row.
    ``wis_L3@s`` is NaN where L3 lacks seed s. When the two roles of an estimand have different
    seed sets on some rows, ``on_mismatch`` decides: "warn" (default; RuntimeWarning),
    "error" (ValueError) or "ignore". A row with no common seed is always an error. With equal
    seed sets on every row this gives the same G_<e> as ``wis_a - wis_b``.

    ``seed_policy="fill"`` (legacy, superseded): a role lacking seed s on a row contributes its
    seed-averaged loss; ``G_<e> = wis_a - wis_b``. Kept to reproduce earlier reports.

    ``extra`` (indexed by ``keys``) is joined on (e.g. state, test_year, strata flags).
    ``g.attrs["seeds"]`` = the union of seeds; ``g.attrs["seed_policy"]``;
    ``g.attrs["seed_mismatch"]`` = {estimand: number of rows whose role seed sets differ}.
    """
    if seed_policy not in ("common", "fill"):
        raise ValueError(f"seed_policy must be 'common' or 'fill', got {seed_policy!r}")
    if on_mismatch not in ("warn", "error", "ignore"):
        raise ValueError(f"on_mismatch must be 'warn', 'error' or 'ignore', got {on_mismatch!r}")
    keys = [k for k in keys if k in scores.columns]
    wides = {r: seed_wide(scores, models[r], metric=metric, model_col=model_col,
                          seed_col=seed_col, keys=keys) for r in ROLES}
    idx = None
    for w in wides.values():
        ok = w.index[w.notna().any(axis=1)]
        idx = ok if idx is None else idx.intersection(ok)
    seeds = sorted(set().union(*[set(w.columns) for w in wides.values()]))
    W = {r: w.reindex(index=idx, columns=seeds) for r, w in wides.items()}
    g = pd.DataFrame(index=idx)
    has = {s: np.zeros(len(idx), bool) for s in seeds}
    for r in ROLES:
        g[f"wis_{r}"] = W[r].mean(axis=1).to_numpy()
        for s in seeds:
            has[s] |= W[r][s].notna().to_numpy()
    mismatch = {}
    if seed_policy == "fill":
        per_seed = {(r, s): W[r][s].fillna(W[r].mean(axis=1)).to_numpy()
                    for r in ROLES for s in seeds}
        for e, (a, b) in ESTIMANDS.items():
            g[e] = g[f"wis_{a}"] - g[f"wis_{b}"]
        for s in seeds:
            for e, (a, b) in ESTIMANDS.items():
                g[f"{e}@{s}"] = per_seed[(a, s)] - per_seed[(b, s)]
            g[f"wis_L3@{s}"] = per_seed[("L3", s)]
            g[f"has@{s}"] = has[s]
    else:
        for e, (a, b) in ESTIMANDS.items():
            pa, pb = W[a].notna().to_numpy(), W[b].notna().to_numpy()
            both = pa & pb
            if (both.sum(axis=1) == 0).any():
                n0 = int((both.sum(axis=1) == 0).sum())
                raise ValueError(f"{e}: {n0} rows have no seed common to {a} and {b}")
            n_mis = int((pa != pb).any(axis=1).sum())
            mismatch[e] = n_mis
            if n_mis and on_mismatch != "ignore":
                msg = (f"{e}: roles {a}/{b} have different seed sets on {n_mis} of {len(idx)} "
                       f"rows; using only the seeds common to both on each row")
                if on_mismatch == "error":
                    raise ValueError(msg)
                warnings.warn(msg, RuntimeWarning, stacklevel=2)
            diff = np.where(both, W[a].to_numpy() - W[b].to_numpy(), np.nan)
            g[e] = np.nanmean(diff, axis=1)
            for j, s in enumerate(seeds):
                g[f"{e}@{s}"] = diff[:, j]
                g[f"has_{e}@{s}"] = both[:, j]
        for s in seeds:
            g[f"wis_L3@{s}"] = W["L3"][s].to_numpy()
            g[f"has@{s}"] = has[s]
    g = g.reset_index()
    if extra is not None:
        g = g.merge(extra, left_on=keys, right_index=True, how="left", validate="one_to_one")
    g.attrs["seeds"] = seeds
    g.attrs["seed_policy"] = seed_policy
    g.attrs["seed_mismatch"] = mismatch
    return g


def seed_spread(g: pd.DataFrame, estimand: str, *, time_col: str = "target_week",
                horizon_col: str = "horizon") -> dict:
    """Per-seed estimates and seed SD of ``estimand`` (audit4 M2).

    Common-seed frames (``has_<e>@s`` columns): the seeds used are those present for both
    roles somewhere; per-seed estimates are computed only on the rows where ALL of them are
    present (so horizons with fewer seeds, e.g. h2/h3 when extra seeds exist only at h1/h4,
    do not enter the seed SD). Legacy frames: seeds with ``has@s`` on any row, all rows.
    Returns {n_seeds, seed_estimates, seed_mean, seed_sd, seed_rows, seed_horizons}.
    """
    seeds = list(g.attrs.get("seeds", []))
    if seeds and f"has_{estimand}@{seeds[0]}" in g:
        seeds = [s for s in seeds if g[f"has_{estimand}@{s}"].any()]
        full = (np.logical_and.reduce([g[f"has_{estimand}@{s}"].to_numpy() for s in seeds])
                if seeds else np.zeros(len(g), bool))
        sub = g[full]
    else:
        seeds = [s for s in seeds if f"has@{s}" in g and g[f"has@{s}"].any()]
        sub = g
    ests = {}
    if len(sub):
        ests = {s: float(weekly_pooled(sub, f"{estimand}@{s}", time_col=time_col,
                                       horizon_col=horizon_col).mean()) for s in seeds}
    vals = list(ests.values())
    return {"n_seeds": len(ests), "seed_estimates": ests,
            "seed_mean": float(np.mean(vals)) if vals else np.nan,
            "seed_sd": float(np.std(vals, ddof=1)) if len(vals) > 1 else np.nan,
            "seed_rows": int(len(sub)),
            "seed_horizons": sorted(int(h) for h in sub[horizon_col].unique()) if len(sub) else []}


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
    Seeds: see ``seed_spread`` (per-seed estimates on the rows where all seeds common to the
    two roles exist; seed_sd NaN with one seed). With the common-seed policy the point estimate
    uses each row's common seeds, so seed_mean can differ from it when seed sets vary by row.

    Strata: when ``g`` is a subset (e.g. outbreak rows), every target week still gets equal
    weight in the mean, however many stratum rows it has (equal-week weighting; audit4 M3);
    this is the same estimator as the primary, applied to the stratum's rows.
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
    out.update(seed_spread(g, estimand, time_col=time_col, horizon_col=horizon_col))
    return out


def compute_estimands_v2(g: pd.DataFrame, *, cluster_col: str | None = "state",
                         time_col: str = "target_week", horizon_col: str = "horizon",
                         block_len: int = 52, n_boot: int = 2000, seed: int = 0,
                         margin_rel: float = 0.01, min_rel: float = 0.01,
                         bootstrap: bool = True) -> dict:
    """All estimands under the v2 policy on the rows of ``g`` (from ``seed_gain_frame``).

    Returns {estimand: infer_estimand(...) + boot_lo/boot_hi} for G_emb, G_id, G_excess and
    'ID_share'. Bootstrap (sensitivity only): ``block_bootstrap_means`` on the row gains
    ``G_<e>`` (common-seed averaged), states x ``block_len``-week circular blocks shared
    across states, percentile 95% CI of the ROW-LEVEL mean (``boot_point``; this differs from
    the primary week-pooled estimate unless the panel is balanced with one horizon). ID share = G_id / G_emb only if the primary (EWC) 95% CI of
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
