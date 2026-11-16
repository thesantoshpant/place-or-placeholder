"""Paper-1 estimands. Positive gain = improvement (lower WIS).

G_emb    = WIS(L3)    - WIS(L4)
G_id     = WIS(L3)    - WIS(L3+C*)
G_excess = WIS(L3+C*) - WIS(L4+C*)          (primary)
ID share = G_id / G_emb, reported only if the 95% bootstrap CI of G_emb
           excludes 0 AND G_emb >= min_rel * WIS(L3); otherwise NaN, "not estimable".
"""
from __future__ import annotations

from typing import Sequence

import numpy as np
import pandas as pd

from .stats import block_bootstrap_means, percentile_ci

ROLES = ("L3", "L4", "L3C", "L4C")
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
