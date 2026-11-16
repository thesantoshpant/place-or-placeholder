"""LightGBM quantile regression on log1p(cases): one booster per quantile (per horizon)."""
from __future__ import annotations

import lightgbm as lgb
import numpy as np

from .base import QuantileModel, finalize

DEFAULTS = dict(learning_rate=0.05, num_leaves=63, min_data_in_leaf=200,
                feature_fraction=0.9, bagging_fraction=0.8, bagging_freq=1,
                lambda_l2=1.0, num_boost_round=400)


class LGBMQuantile(QuantileModel):
    name = "lgbm"

    def _params(self, q):
        p = {**DEFAULTS, **self.params}
        rounds = int(p.pop("num_boost_round"))
        p.update(objective="quantile", alpha=float(q), num_threads=self.threads,
                 seed=self.seed, deterministic=True, force_row_wise=True, verbose=-1)
        return p, rounds

    def fit(self, X, y_log, quantiles=None):
        self.quantiles_ = tuple(float(q) for q in quantiles)
        ds = lgb.Dataset(X.to_numpy(np.float32), label=np.asarray(y_log, np.float32),
                         feature_name=list(X.columns), free_raw_data=False)
        self.boosters_ = {}
        for q in self.quantiles_:
            p, rounds = self._params(q)
            self.boosters_[round(q, 6)] = lgb.train(p, ds, num_boost_round=rounds)
        return self

    def predict_log(self, X, quantiles):
        Xa = X.to_numpy(np.float32)
        return np.column_stack([self.boosters_[round(float(q), 6)].predict(
            Xa, num_threads=self.threads) for q in quantiles])

    def predict_quantiles(self, X, quantiles):
        return finalize(np.expm1(self.predict_log(X, quantiles)))
