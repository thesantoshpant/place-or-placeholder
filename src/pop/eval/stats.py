"""Inference helpers: Diebold-Mariano (EWC/HAC + HLN), cluster moving-block bootstrap, Holm.

References
- Diebold FX, Mariano RS (1995). Comparing predictive accuracy. JBES 13:253-263.
- Harvey D, Leybourne S, Newbold P (1997). Testing the equality of prediction
  mean squared errors. IJF 13:281-291.
- Newey WK, West KD (1987). Econometrica 55:703-708; (1994) RES 61:631-653.
- Lazarus E, Lewis DJ, Stock JH, Watson MW (2018). HAR inference:
  recommendations for practice. JBES 36:541-559 (EWC estimator).
- Kunsch HR (1989); Politis DN, Romano JP (1992) (circular block bootstrap).
- Holm S (1979). Scand J Stat 6:65-70.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Callable, Sequence

import numpy as np
import pandas as pd
from scipy import stats as _st


# ----------------------------------------------------------------- Diebold-Mariano
@dataclass
class DMResult:
    stat: float      # HLN-corrected statistic
    p_value: float   # two-sided, Student-t with ``df`` degrees of freedom
    mean_d: float
    se: float        # long-run SE of mean_d (uncorrected; HAC or EWC)
    T: int
    lag: int | None  # Bartlett HAC lag (None for method="ewc")
    hln_factor: float
    method: str = "ewc"   # "ewc" or "nw-hac"
    df: float = float("nan")  # t reference df (B for EWC, T-1 for HAC)

    def to_dict(self) -> dict:
        return asdict(self)


def hln_factor(T: int, h: int) -> float:
    """Harvey-Leybourne-Newbold factor sqrt((T+1-2h+h(h-1)/T)/T)."""
    return float(np.sqrt((T + 1 - 2 * h + h * (h - 1) / T) / T))


def newey_west_var(d: np.ndarray, lag: int) -> float:
    """Bartlett-kernel long-run variance of d (autocovariances divided by T)."""
    d = np.asarray(d, float)
    T = d.size
    e = d - d.mean()
    v = e @ e / T
    for k in range(1, min(lag, T - 1) + 1):
        v += 2 * (1 - k / (lag + 1)) * (e[k:] @ e[:-k]) / T
    return float(v)


def nw_auto_lag(T: int) -> int:
    """Newey-West (1994) rule of thumb floor(4*(T/100)**(2/9))."""
    return int(np.floor(4 * (T / 100) ** (2 / 9)))


def ewc_n_terms(T: int) -> int:
    """Lazarus-Lewis-Stock-Watson (2018) rule B = floor(0.4*T**(2/3)), in [1, T-1]."""
    return int(min(max(np.floor(0.4 * T ** (2 / 3)), 1), T - 1))


def ewc_var(d: np.ndarray, B: int | None = None) -> tuple[float, int]:
    """Equal-weighted cosine (EWC) long-run variance of d and its df B.

    omega = mean_j Lambda_j^2, Lambda_j = sqrt(2/T) sum_t cos(pi j (t-1/2)/T) d_t,
    j = 1..B. Under fixed-b asymptotics (B fixed) dbar/sqrt(omega/T) ~ t_B.
    """
    d = np.asarray(d, float)
    T = d.size
    B = ewc_n_terms(T) if B is None else int(B)
    t = np.arange(T) + 0.5
    basis = np.sqrt(2 / T) * np.cos(np.pi * np.outer(np.arange(1, B + 1), t) / T)
    lam = basis @ (d - d.mean())
    return float(lam @ lam / B), B


def dm_test(d, h: int = 1, lag: str | int | None = None) -> DMResult:
    """Diebold-Mariano test on a loss-difference series d_t = L_A - L_B.

    stat = HLN * dbar / se (Harvey-Leybourne-Newbold 1997). ``lag`` selects the
    long-run variance:

    - ``None`` or ``"ewc"`` (default): equal-weighted cosine estimator with
      B = floor(0.4*T**(2/3)) terms and a t_B reference (fixed-b; Lazarus,
      Lewis, Stock & Watson 2018). Near-nominal size for autocorrelated weekly
      d_t (AR(1) phi=0.5, T=104: ~6% at nominal 5%). ``h`` enters only via HLN.
    - ``"nw"``: Newey-West Bartlett HAC, lag max(h-1, floor(4*(T/100)**(2/9)))
      (Newey-West 1994 rule of thumb), t_{T-1} reference. Over-rejects
      (~10%) under phi=0.5, T=104.
    - ``"h-1"``: Bartlett HAC with lag h-1 (classic DM; no correction when h=1).
    - ``int``: Bartlett HAC with lag max(h-1, lag), t_{T-1} reference; ``se``
      then matches statsmodels HAC (no small-sample correction).

    NaNs are dropped (series assumed in time order). mean_d > 0 means model B
    has lower loss. If the variance is 0: stat=0, p=1 when mean_d==0;
    otherwise stat=+-inf, p=0.
    """
    d = np.asarray(d, float)
    d = d[~np.isnan(d)]
    T = d.size
    if T < 2:
        raise ValueError("need at least 2 non-NaN observations")
    dbar = float(d.mean())
    if lag is None or lag == "ewc":
        var, B = ewc_var(d)
        L, method, df = None, "ewc", float(B)
    else:
        if lag == "nw":
            L = max(h - 1, nw_auto_lag(T))
        elif lag == "h-1":
            L = max(h - 1, 0)
        elif isinstance(lag, (int, np.integer)) and not isinstance(lag, bool):
            L = max(h - 1, int(lag))
        else:
            raise ValueError(f"lag must be None, 'ewc', 'nw', 'h-1' or int, got {lag!r}")
        var = newey_west_var(d, L)
        method, df = "nw-hac", float(T - 1)
    se = float(np.sqrt(max(var, 0.0) / T))
    f = hln_factor(T, h)
    if se <= 1e-14 * max(1.0, abs(dbar)):
        stat = 0.0 if abs(dbar) < 1e-14 else np.sign(dbar) * np.inf
        p = 1.0 if stat == 0 else 0.0
        return DMResult(stat, p, dbar, se, T, L, f, method, df)
    stat = f * dbar / se
    p = float(2 * _st.t.sf(abs(stat), df=df))
    return DMResult(float(stat), p, dbar, se, T, L, f, method, df)


def loss_diff_series(
    scores: pd.DataFrame,
    model_a: str,
    model_b: str,
    *,
    metric: str = "wis",
    model_col: str = "model",
    time_col: str = "target_week",
    keys: Sequence[str] = ("unit_id", "origin_week", "target_week", "horizon"),
) -> pd.Series:
    """Per-week mean over units of (metric_A - metric_B), on rows scored for both.

    Filter ``scores`` to one horizon (and split) before calling. Indexed by
    ``time_col`` (sorted).
    """
    keys = [k for k in keys if k in scores.columns]
    a = scores.loc[scores[model_col] == model_a, keys + [metric]]
    b = scores.loc[scores[model_col] == model_b, keys + [metric]]
    m = a.merge(b, on=keys, suffixes=("_a", "_b"), validate="one_to_one")
    m["d"] = m[f"{metric}_a"] - m[f"{metric}_b"]
    m = m.dropna(subset=["d"])
    return m.groupby(time_col)["d"].mean().sort_index()


# ------------------------------------------------------- cluster block bootstrap
def _panel(df, value_cols, cluster_col, time_col):
    clusters = (pd.Index(["_all"] * len(df)) if cluster_col is None else pd.Index(df[cluster_col]))
    cc, cl = pd.factorize(clusters, sort=True)
    tc, tl = pd.factorize(df[time_col], sort=True)
    C, T, V = len(cl), len(tl), len(value_cols)
    S = np.zeros((V, C, T))
    N = np.zeros((V, C, T))
    for j, col in enumerate(value_cols):
        x = df[col].to_numpy(float)
        ok = ~np.isnan(x)
        np.add.at(S[j], (cc[ok], tc[ok]), x[ok])
        np.add.at(N[j], (cc[ok], tc[ok]), 1.0)
    return S, N


def _block_idx(T: int, b: int, rng, size=()):
    nb = -(-T // b)
    starts = rng.integers(0, T, size=size + (nb,))
    idx = (starts[..., None] + np.arange(b)) % T
    return idx.reshape(size + (nb * b,))[..., :T]


def block_bootstrap_means(
    df: pd.DataFrame,
    value_cols: Sequence[str],
    *,
    cluster_col: str | None = "state",
    time_col: str = "target_week",
    block_len: int = 8,
    n_boot: int = 2000,
    seed: int = 0,
    shared_time_blocks: bool = True,
) -> tuple[np.ndarray, np.ndarray]:
    """Bootstrap the row-level means of ``value_cols``.

    Each replicate draws clusters with replacement, then circular blocks of
    ``block_len`` time points (wrapping), truncated to T. With
    ``shared_time_blocks`` one set of week indices is used for all clusters in
    a replicate (preserves common-week shocks); else drawn per cluster.
    Returns (point estimate (V,), replicates (n_boot, V)).
    """
    value_cols = list(value_cols)
    S, N = _panel(df, value_cols, cluster_col, time_col)
    _, C, T = S.shape
    point = S.sum(axis=(1, 2)) / N.sum(axis=(1, 2))
    rng = np.random.default_rng(seed)
    out = np.empty((n_boot, len(value_cols)))
    for r in range(n_boot):
        ci = rng.integers(0, C, size=C)
        if shared_time_blocks:
            ti = _block_idx(T, block_len, rng)
            Ss, Ns = S[:, ci][:, :, ti], N[:, ci][:, :, ti]
        else:
            ti = _block_idx(T, block_len, rng, size=(C,))
            Ss = np.take_along_axis(S[:, ci], ti[None], axis=2)
            Ns = np.take_along_axis(N[:, ci], ti[None], axis=2)
        with np.errstate(invalid="ignore", divide="ignore"):
            out[r] = Ss.sum(axis=(1, 2)) / Ns.sum(axis=(1, 2))
    return point, out


def percentile_ci(reps: np.ndarray, alpha: float = 0.05) -> tuple[float, float]:
    reps = np.asarray(reps, float)
    reps = reps[np.isfinite(reps)]
    lo, hi = np.quantile(reps, [alpha / 2, 1 - alpha / 2])
    return float(lo), float(hi)


def bootstrap_ci_mean(df, col: str, *, alpha: float = 0.05, **kw) -> dict:
    """Percentile CI for the mean of ``col`` (e.g. a per-row loss difference)."""
    pt, reps = block_bootstrap_means(df, [col], **kw)
    lo, hi = percentile_ci(reps[:, 0], alpha)
    return {"estimate": float(pt[0]), "lo": lo, "hi": hi, "se": float(np.nanstd(reps[:, 0], ddof=1))}


def bootstrap_ci_ratio(df, num_col: str, den_col: str, *, alpha: float = 0.05, **kw) -> dict:
    """Percentile CI for mean(num)/mean(den), both from the same resamples."""
    pt, reps = block_bootstrap_means(df, [num_col, den_col], **kw)
    with np.errstate(invalid="ignore", divide="ignore"):
        r = reps[:, 0] / reps[:, 1]
    lo, hi = percentile_ci(r, alpha)
    return {"estimate": float(pt[0] / pt[1]), "lo": lo, "hi": hi}


# ------------------------------------------------------------------------- Holm
def holm(pvals) -> np.ndarray:
    """Holm step-down adjusted p-values (NaNs kept as NaN, excluded from m)."""
    p = np.asarray(pvals, float)
    out = np.full_like(p, np.nan)
    ok = ~np.isnan(p)
    pv = p[ok]
    m = pv.size
    if m == 0:
        return out
    order = np.argsort(pv)
    adj = np.minimum(1.0, np.maximum.accumulate((m - np.arange(m)) * pv[order]))
    res = np.empty(m)
    res[order] = adj
    out[ok] = res
    return out
