"""NB2 regression (statsmodels discrete NegativeBinomial, log link) on case counts.

Features enter as-is (log1p history + week-of-year sin/cos) plus an intercept.
Predictive quantiles are NB(mu, alpha) quantiles, alpha estimated by MLE.
Training rows with any NaN feature are dropped; NaN at prediction is set to 0.
"""
from __future__ import annotations

import numpy as np
import statsmodels.api as sm
from scipy import stats

from .base import QuantileModel, finalize


class NBGLM(QuantileModel):
    name = "nb"

    def fit(self, X, y_log, quantiles=None):
        y = np.round(np.expm1(np.asarray(y_log)))
        Xc = sm.add_constant(X.to_numpy(float), has_constant="add")
        ok = np.isfinite(Xc).all(1) & np.isfinite(y)
        Xc, y = Xc[ok], y[ok]
        pois = sm.GLM(y, Xc, family=sm.families.Poisson()).fit()
        start = np.append(pois.params, 1.0)
        maxiter = int(self.params.get("maxiter", 300))
        # lbfgs optimises log(alpha) internally (statsmodels transparams), which is
        # stable when the data are near-Poisson; newton on raw alpha can overflow.
        res = sm.NegativeBinomial(y, Xc).fit(start_params=start, method="lbfgs",
                                             maxiter=maxiter, disp=0)
        self.beta_, self.alpha_ = res.params[:-1], float(res.params[-1])
        self.converged_ = bool(res.mle_retvals.get("converged", False))
        return self

    def mean(self, X):
        Xc = sm.add_constant(np.nan_to_num(X.to_numpy(float)), has_constant="add")
        return np.exp(np.clip(Xc @ self.beta_, -30, 25))

    def predict_quantiles(self, X, quantiles):
        mu = self.mean(X)[:, None]
        n = 1.0 / max(self.alpha_, 1e-8)
        p = n / (n + mu)
        q = stats.nbinom.ppf(np.asarray(quantiles, float)[None, :], n, p)
        return finalize(q)
