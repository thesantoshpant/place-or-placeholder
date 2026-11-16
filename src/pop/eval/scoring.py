"""Proper scoring of quantile forecasts: WIS, coverage, median AE.

Reference: Bracher J, Ray EL, Gneiting T, Reich NG (2021). Evaluating epidemic
forecasts in an interval format. PLoS Comput Biol 17(2): e1008618.

Long forecast format: unit_id, origin_week, target_week, horizon, quantile, value
(any extra columns, e.g. ``model`` or ``split``, are carried through as keys).
Truth format: unit_id, target_week, cases.
"""
from __future__ import annotations

import warnings
from typing import Iterable, Sequence

import numpy as np
import pandas as pd

PRIMARY_QUANTILES: tuple[float, ...] = (0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9)
CDC_QUANTILES: tuple[float, ...] = (
    0.01, 0.025, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5,
    0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 0.975, 0.99,
)
PRIMARY_COVERAGE: tuple[float, ...] = (0.4, 0.8)
SECONDARY_COVERAGE: tuple[float, ...] = (0.5, 0.9)
_DEC = 6  # rounding used to match quantile levels


def _q(levels: Iterable[float]) -> np.ndarray:
    return np.round(np.asarray(list(levels), dtype=float), _DEC)


def interval_alphas(quantiles: Sequence[float]) -> np.ndarray:
    """Return alphas (ascending) of the central intervals in a symmetric set.

    The set must contain 0.5 and be symmetric (q and 1-q both present).
    """
    q = np.sort(_q(quantiles))
    if not np.any(np.isclose(q, 0.5)):
        raise ValueError("quantile set must contain the median 0.5")
    if not np.allclose(q, np.sort(np.round(1 - q, _DEC))):
        raise ValueError(f"quantile set is not symmetric: {q}")
    lower = q[q < 0.5]
    return np.round(2 * lower, _DEC)  # alpha_k = 2 * lower level


def sort_crossing(values: np.ndarray) -> tuple[np.ndarray, int]:
    """Sort quantile values along the last axis (levels assumed ascending).

    Returns the sorted array and the number of rows that had crossing.
    Rows with NaN are left as-is (their scores become NaN anyway).
    """
    v = np.asarray(values, dtype=float)
    d = np.diff(v, axis=-1)
    crossed = np.any(d < 0, axis=-1)
    n = int(np.sum(crossed))
    if n:
        v = v.copy()
        v[crossed] = np.sort(v[crossed], axis=-1)
    return v, n


def _prep(y, levels, values, log1p, sort):
    lv = _q(levels)
    order = np.argsort(lv)
    lv = lv[order]
    v = np.atleast_2d(np.asarray(values, dtype=float))[:, order]
    y = np.atleast_1d(np.asarray(y, dtype=float))
    if v.shape[0] != y.shape[0]:
        raise ValueError("values must have shape (n, n_quantiles) matching y")
    if log1p:
        y = np.log1p(y)
        v = np.log1p(v)
    n_cross = 0
    if sort:
        v, n_cross = sort_crossing(v)
        if n_cross:
            warnings.warn(f"{n_cross} forecast(s) had quantile crossing; sorted", stacklevel=3)
    return y, lv, v, n_cross


def interval_score(y, lower, upper, alpha):
    """IS_alpha = (u-l) + 2/alpha (l-y)_+ + 2/alpha (y-u)_+."""
    return (upper - lower) + (2.0 / alpha) * np.maximum(lower - y, 0) + (
        2.0 / alpha
    ) * np.maximum(y - upper, 0)


def wis_interval(y, levels, values, *, log1p: bool = False, sort: bool = True) -> np.ndarray:
    """WIS via the interval form (Bracher et al. 2021, eq. 2).

    WIS = 1/(K+0.5) * (0.5|y-m| + sum_k alpha_k/2 * IS_{alpha_k}).
    ``values``: array (n, Q) with columns matching ``levels``. NaN -> NaN.
    """
    y, lv, v, _ = _prep(y, levels, values, log1p, sort)
    alphas = interval_alphas(lv)
    K = len(alphas)
    med = v[:, np.isclose(lv, 0.5)][:, 0]
    tot = 0.5 * np.abs(y - med)
    for a in alphas:
        lo = v[:, np.isclose(lv, a / 2)][:, 0]
        hi = v[:, np.isclose(lv, 1 - a / 2)][:, 0]
        tot = tot + (a / 2) * interval_score(y, lo, hi, a)
    return tot / (K + 0.5)


def pinball_loss(y, q, tau):
    """Quantile (pinball) loss: (1{y<q} - tau)(q - y)."""
    return ((y < q).astype(float) - tau) * (q - y)


def wis_quantile(y, levels, values, *, log1p: bool = False, sort: bool = True) -> np.ndarray:
    """WIS via the quantile form: 1/(K+0.5) * sum_q pinball_q (equal to interval form)."""
    y, lv, v, _ = _prep(y, levels, values, log1p, sort)
    K = len(interval_alphas(lv))
    pl = pinball_loss(y[:, None], v, lv[None, :])
    return pl.sum(axis=1) / (K + 0.5)


def coverage(y, levels, values, level: float, *, sort: bool = True) -> np.ndarray:
    """1.0 if y in the central ``level`` interval [l, u] (inclusive), else 0.0; NaN if missing.

    Monotone transform invariant, so no log1p option is needed.
    """
    lv = _q(levels)
    order = np.argsort(lv)
    lv, v = lv[order], np.atleast_2d(np.asarray(values, float))[:, order]
    if sort:
        v, _ = sort_crossing(v)
    y = np.atleast_1d(np.asarray(y, float))
    a = round((1 - level) / 2, _DEC)
    il, iu = np.isclose(lv, a), np.isclose(lv, 1 - a)
    if not (il.any() and iu.any()):
        raise ValueError(f"levels lack quantiles {a} and {1 - a} for {level:.0%} coverage")
    lo, hi = v[:, il][:, 0], v[:, iu][:, 0]
    out = ((y >= lo) & (y <= hi)).astype(float)
    out[np.isnan(y) | np.isnan(lo) | np.isnan(hi)] = np.nan
    return out


def score_forecasts(
    forecasts: pd.DataFrame,
    truth: pd.DataFrame,
    *,
    quantiles: Sequence[float] = PRIMARY_QUANTILES,
    scale: str = "log",
    coverage_levels: Sequence[float] = PRIMARY_COVERAGE,
) -> pd.DataFrame:
    """Score long-format forecasts against truth; one row per forecast.

    Keys are all forecast columns except ``quantile``/``value``. Only the
    requested ``quantiles`` are used (extra levels are ignored); a forecast
    missing any requested level, or with no truth, gets NaN scores.
    ``scale``: "log" (log1p of truth and quantiles; primary) or "case".
    Output columns: keys, cases, wis, ae_median, cov_<pct> ..., n_crossing attr.
    """
    if scale not in ("log", "case"):
        raise ValueError("scale must be 'log' or 'case'")
    lv = np.sort(_q(quantiles))
    interval_alphas(lv)
    keys = [c for c in forecasts.columns if c not in ("quantile", "value")]
    fc = forecasts.assign(quantile=np.round(forecasts["quantile"].astype(float), _DEC))
    fc = fc[fc["quantile"].isin(lv)]
    if fc.duplicated(keys + ["quantile"]).any():
        raise ValueError("duplicate (forecast, quantile) rows")
    wide = fc.set_index(keys + ["quantile"])["value"].unstack("quantile")
    wide = wide.reindex(columns=lv)
    wide = wide.reset_index()
    tr = truth[["unit_id", "target_week", "cases"]]
    out = wide[keys].merge(tr, on=["unit_id", "target_week"], how="left", validate="many_to_one")
    v = wide[list(lv)].to_numpy(float)
    y = out["cases"].to_numpy(float)
    vs, n_cross = sort_crossing(v)
    if n_cross:
        warnings.warn(f"{n_cross} forecast(s) had quantile crossing; sorted", stacklevel=2)
    log1p = scale == "log"
    out["wis"] = wis_interval(y, lv, vs, log1p=log1p, sort=False)
    med = vs[:, np.isclose(lv, 0.5)][:, 0]
    out["ae_median"] = np.abs(np.log1p(y) - np.log1p(med)) if log1p else np.abs(y - med)
    for lev in coverage_levels:
        out[f"cov_{int(round(lev * 100))}"] = coverage(y, lv, vs, lev, sort=False)
    out.attrs["n_crossing"] = n_cross
    out.attrs["scale"] = scale
    return out


def aggregate_scores(
    scores: pd.DataFrame,
    by: Sequence[str] = ("split", "horizon", "model"),
    metrics: Sequence[str] | None = None,
) -> pd.DataFrame:
    """Mean of score columns by any grouping (missing ``by`` columns are skipped).

    NaN scores are excluded from means; ``n`` counts non-NaN WIS rows.
    """
    by = [b for b in by if b in scores.columns]
    if metrics is None:
        metrics = [c for c in scores.columns if c in ("wis", "ae_median") or c.startswith("cov_")]
    metrics = list(metrics)
    if not by:
        res = scores[metrics].mean().to_frame().T
        res["n"] = int(scores["wis"].notna().sum()) if "wis" in scores else len(scores)
        return res
    g = scores.groupby(by, dropna=False, observed=True)
    res = g[metrics].mean()
    res["n"] = g["wis"].count() if "wis" in scores else g.size()
    return res.reset_index()
