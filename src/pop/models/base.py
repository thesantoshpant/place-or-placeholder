"""Model interface: fit on log1p targets, predict case-scale quantiles (n, Q), sorted."""
from __future__ import annotations

import numpy as np
import pandas as pd


class QuantileModel:
    name = "base"

    def __init__(self, seed: int = 0, threads: int = 16, **params):
        self.seed, self.threads, self.params = seed, threads, params

    def fit(self, X: pd.DataFrame, y_log: np.ndarray, quantiles=None) -> "QuantileModel":
        raise NotImplementedError

    def predict_quantiles(self, X: pd.DataFrame, quantiles) -> np.ndarray:
        raise NotImplementedError


def finalize(q_case: np.ndarray) -> np.ndarray:
    """Clip to >= 0 and enforce monotone quantiles by sorting each row."""
    return np.sort(np.clip(np.nan_to_num(q_case, nan=0.0), 0.0, None), axis=1)
