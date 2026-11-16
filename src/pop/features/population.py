"""Yearly unit population (and other epoch quantities) interpolated from GHSL 5-year epochs.

GHSL P2023A epochs are 1975, 1980, ..., 2030 (2025/2030 are projections). Values between
two epochs are interpolated log-linearly (constant growth rate) when both endpoints are
positive and linearly otherwise; years outside the epoch range are clamped to the nearest
epoch (never extrapolated).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

EPOCH_STEP = 5


def epochs_for_years(y0: int, y1: int) -> list[int]:
    """Smallest set of 5-year epochs whose range brackets [y0, y1]."""
    a = (y0 // EPOCH_STEP) * EPOCH_STEP
    b = -(-y1 // EPOCH_STEP) * EPOCH_STEP
    return list(range(a, b + 1, EPOCH_STEP))


def interp_years(values: np.ndarray, epochs, years, method: str = "loglinear") -> np.ndarray:
    """values (n_units, n_epochs) at sorted ``epochs`` -> (n_units, n_years).

    method: "linear" or "loglinear" (falls back to linear where an endpoint is <= 0)."""
    v = np.asarray(values, float)
    ep = np.asarray(epochs, float)
    out = np.empty((v.shape[0], len(years)))
    for j, y in enumerate(years):
        y = float(np.clip(y, ep[0], ep[-1]))
        k = min(int(np.searchsorted(ep, y, side="right")) - 1, len(ep) - 2)
        t = (y - ep[k]) / (ep[k + 1] - ep[k])
        a, b = v[:, k], v[:, k + 1]
        lin = a + t * (b - a)
        if method == "loglinear":
            pos = (a > 0) & (b > 0)
            with np.errstate(divide="ignore", invalid="ignore"):
                lg = np.exp(np.log(a) + t * (np.log(b) - np.log(a)))
            out[:, j] = np.where(pos, lg, lin)
        elif method == "linear":
            out[:, j] = lin
        else:
            raise ValueError(method)
    return out


def to_long(unit_ids, years, arr: np.ndarray, name: str) -> pd.DataFrame:
    return pd.DataFrame({"unit_id": np.repeat(np.asarray(unit_ids, str), len(years)),
                         "year": np.tile(np.asarray(years, "int16"), len(unit_ids)),
                         name: arr.ravel()})
