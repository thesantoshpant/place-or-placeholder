import numpy as np
import pandas as pd

from pop.features import history as H
from pop.models import make_model
from test_history import synth_panel

Q = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]


def _data(level="l1_features", h=1):
    g = H.make_grid(synth_panel(n_units=4))
    tr = H.design_index(g, np.arange(170, 280), h)
    te = H.design_index(g, np.arange(280, 320), h)
    f = getattr(H, level)
    return (f(g, tr, h), g.y[tr.u, tr.t], f(g, te, h))


def test_quantiles_monotone_nonnegative():
    for name, level in [("naive", "l0_features"), ("nb", "l1_features"), ("lgbm", "l1_features")]:
        Xtr, ytr, Xte = _data(level)
        kw = {"num_boost_round": 30, "min_data_in_leaf": 10} if name == "lgbm" else {}
        m = make_model(name, seed=0, threads=2, **kw).fit(Xtr, ytr, quantiles=Q)
        P = m.predict_quantiles(Xte, Q)
        assert P.shape == (len(Xte), len(Q))
        assert np.all(np.diff(P, axis=1) >= 0) and np.all(P >= 0), name


def test_naive_median_is_last_year_when_errors_symmetric():
    X = pd.DataFrame({"sy1_0": np.log1p([0.0, 10.0, 100.0])})
    m = make_model("naive").fit(pd.DataFrame({"sy1_0": np.zeros(5)}), np.array([-1, -.5, 0, .5, 1.]))
    P = m.predict_quantiles(X, Q)
    assert np.allclose(P[:, 4], [0, 10, 100])


def test_lgbm_finalize_sorts_crossing():
    from pop.models import finalize
    P = finalize(np.array([[3.0, 1.0, 2.0], [-1.0, 0.5, 0.2]]))
    assert np.array_equal(P, [[1, 2, 3], [0, 0.2, 0.5]])
