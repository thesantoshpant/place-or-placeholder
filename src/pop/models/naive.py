"""Seasonal naive (L0): median = cases in week T-52; quantiles from training errors.

Quantile method: e = log1p(y_T) - log1p(y_{T-52}) over all training rows of this
horizon (target years in the train window, flag_gap targets excluded). The
forecast quantile tau is expm1(log1p(y_{T-52}) + Q_e(tau)), clipped at 0.
"""
from __future__ import annotations

import numpy as np

from .base import QuantileModel, finalize


class SeasonalNaive(QuantileModel):
    name = "naive"
    feature = "sy1_0"

    def fit(self, X, y_log, quantiles=None):
        e = np.asarray(y_log) - X[self.feature].to_numpy()
        self.errors_ = e[np.isfinite(e)]
        return self

    def predict_quantiles(self, X, quantiles):
        qe = np.quantile(self.errors_, np.asarray(quantiles, float))
        base = X[self.feature].to_numpy()[:, None]
        return finalize(np.expm1(base + qe[None, :]))
