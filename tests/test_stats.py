import numpy as np
import pandas as pd
import pytest

from pop.eval import stats as ST


def ar1(rng, T, phi, size=()):
    e = rng.normal(size=size + (T,))
    x = np.empty_like(e)
    x[..., 0] = e[..., 0] / np.sqrt(1 - phi**2)
    for t in range(1, T):
        x[..., t] = phi * x[..., t - 1] + e[..., t]
    return x


def test_identical_losses():
    r = ST.dm_test(np.zeros(50), h=2)
    assert r.stat == 0 and r.p_value == 1 and r.mean_d == 0


def test_constant_nonzero_difference():
    r = ST.dm_test(np.full(30, 0.5))
    assert np.isinf(r.stat) and r.p_value == 0


def test_clearly_better_model():
    rng = np.random.default_rng(0)
    d = 1.0 + ar1(rng, 100, 0.3)
    r = ST.dm_test(d, h=1, lag=3)
    assert r.p_value < 1e-4 and r.stat > 0 and r.mean_d == pytest.approx(d.mean())


@pytest.mark.parametrize("T,h", [(50, 1), (50, 4), (104, 3), (10, 2)])
def test_hln_factor(T, h):
    assert ST.hln_factor(T, h) == pytest.approx(np.sqrt((T + 1 - 2 * h + h * (h - 1) / T) / T))
    rng = np.random.default_rng(T + h)
    d = rng.normal(0.2, 1, T)
    r = ST.dm_test(d, h=h, lag="h-1")
    assert r.lag == h - 1
    assert r.stat == pytest.approx(ST.hln_factor(T, h) * r.mean_d / r.se)


def test_lag_rule():
    d = np.random.default_rng(1).normal(size=40)
    assert ST.dm_test(d, h=4, lag=2).lag == 3
    assert ST.dm_test(d, h=1, lag=5).lag == 5
    assert ST.dm_test(d, h=1, lag="nw").lag == ST.nw_auto_lag(40) == 3
    assert ST.dm_test(np.zeros(104) + d.mean(), h=1, lag="nw").lag == 4
    assert ST.dm_test(d, h=6, lag="nw").lag == 5
    assert ST.dm_test(d, h=3, lag="h-1").lag == 2
    r = ST.dm_test(d, h=4)
    assert r.method == "ewc" and r.lag is None and r.df == ST.ewc_n_terms(40) == 4
    with pytest.raises(ValueError):
        ST.dm_test(d, lag="bogus")


def test_ewc_var():
    d = np.random.default_rng(3).normal(size=104)
    v, B = ST.ewc_var(d)
    assert B == 8
    # invariant to the mean; equals mean of squared cosine projections
    t = np.arange(104) + 0.5
    lam = [np.sqrt(2 / 104) * np.cos(np.pi * j * t / 104) @ d for j in range(1, 9)]
    assert v == pytest.approx(np.mean(np.square(lam)))
    assert ST.ewc_var(d + 5.0)[0] == pytest.approx(v)
    r = ST.dm_test(d)
    assert r.se == pytest.approx(np.sqrt(v / 104))
    assert r.stat == pytest.approx(ST.hln_factor(104, 1) * r.mean_d / r.se)


def test_hac_matches_statsmodels():
    sm = pytest.importorskip("statsmodels.api")
    rng = np.random.default_rng(5)
    d = 0.3 + ar1(rng, 80, 0.5)
    for L in (0, 3, 6):
        r = ST.dm_test(d, h=1, lag=L)
        fit = sm.OLS(d, np.ones_like(d)).fit(cov_type="HAC", cov_kwds={"maxlags": L, "use_correction": False})
        assert r.se == pytest.approx(float(fit.bse[0]), rel=1e-10)


def test_nan_dropped():
    d = np.r_[np.random.default_rng(2).normal(size=30), np.nan]
    assert ST.dm_test(d).T == 30


def _rej(D, **kw):
    return np.mean([ST.dm_test(x, h=1, **kw).p_value < 0.05 for x in D])


def test_null_size_ar1():
    # Default EWC/fixed-b DM under AR(1) nulls, 1000 seeded reps (MC SE ~0.7pp).
    # Reference sims (seed 42): phi=0.5,T=104: 6.9%; phi=0,T=104: 5.8%;
    # phi=0.5,T=260: 5.7%. NW-1994 "nw" gives ~11% and "h-1" ~27% at phi=0.5.
    rng = np.random.default_rng(42)
    D = ar1(rng, 104, 0.5, size=(1000,))
    assert 0.03 <= _rej(D) <= 0.08
    assert _rej(D, lag="nw") > _rej(D)  # documents the HAC over-rejection
    D0 = ar1(rng, 104, 0.0, size=(1000,))
    assert 0.03 <= _rej(D0) <= 0.075


def test_power_ar1_shift():
    # 0.3 marginal-SD mean shift, phi=0.5, T=104: EWC power ~0.35
    rng = np.random.default_rng(7)
    D = 0.3 / np.sqrt(0.75) + ar1(rng, 104, 0.5, size=(400,))
    assert 0.2 <= _rej(D) <= 0.55


def test_loss_diff_series():
    sc = pd.DataFrame({
        "model": ["A"] * 4 + ["B"] * 3,
        "unit_id": [1, 2, 1, 2, 1, 2, 1],
        "origin_week": [0, 0, 1, 1, 0, 0, 1],
        "target_week": [1, 1, 2, 2, 1, 1, 2],
        "horizon": 1,
        "wis": [3.0, 5.0, 2.0, 9.0, 1.0, 1.0, 1.0],
    })
    d = ST.loss_diff_series(sc, "A", "B")
    np.testing.assert_allclose(d.to_numpy(), [3.0, 1.0])  # week 2: only unit 1 shared
    assert list(d.index) == [1, 2]


def _panel_df(rng, C=20, T=60, mu=0.5, phi=0.5):
    x = mu + ar1(rng, T, phi, size=(C,))
    return pd.DataFrame({"state": np.repeat(np.arange(C), T), "target_week": np.tile(np.arange(T), C),
                         "d": x.ravel()})


def test_bootstrap_reproducible():
    df = _panel_df(np.random.default_rng(0))
    a = ST.bootstrap_ci_mean(df, "d", n_boot=200, seed=7)
    b = ST.bootstrap_ci_mean(df, "d", n_boot=200, seed=7)
    c = ST.bootstrap_ci_mean(df, "d", n_boot=200, seed=8)
    assert a == b and a != c
    assert a["lo"] < a["estimate"] < a["hi"]
    assert a["estimate"] == pytest.approx(df.d.mean())


def test_bootstrap_coverage():
    rng = np.random.default_rng(11)
    hits = 0
    nsim = 60
    for s in range(nsim):
        df = _panel_df(rng, C=15, T=48, mu=0.5)
        ci = ST.bootstrap_ci_mean(df, "d", n_boot=300, seed=s)
        hits += ci["lo"] <= 0.5 <= ci["hi"]
    assert hits / nsim >= 0.8, hits / nsim


def test_bootstrap_per_cluster_blocks_and_no_cluster():
    df = _panel_df(np.random.default_rng(3))
    a = ST.bootstrap_ci_mean(df, "d", n_boot=200, seed=1, shared_time_blocks=False)
    b = ST.bootstrap_ci_mean(df, "d", n_boot=200, seed=1, cluster_col=None)
    for r in (a, b):
        assert r["lo"] < r["estimate"] < r["hi"]


def test_bootstrap_ratio():
    rng = np.random.default_rng(4)
    df = _panel_df(rng)
    df["num"] = 0.3 * df["d"] + 0.05 * rng.normal(size=len(df))
    r = ST.bootstrap_ci_ratio(df, "num", "d", n_boot=300, seed=0)
    assert r["estimate"] == pytest.approx(df.num.mean() / df.d.mean())
    assert r["lo"] < 0.3 < r["hi"]


def test_block_idx_circular():
    rng = np.random.default_rng(0)
    idx = ST._block_idx(10, 4, rng)
    assert idx.shape == (10,)
    for blk in (idx[0:4], idx[4:8], idx[8:10]):
        assert np.all(np.diff(blk) % 10 == 1)  # consecutive, wrapping


def test_holm():
    p = [0.01, 0.04, 0.03, 0.005, np.nan]
    adj = ST.holm(p)
    np.testing.assert_allclose(adj[:4], [0.03, 0.06, 0.06, 0.02])
    assert np.isnan(adj[4])
    sm = pytest.importorskip("statsmodels.stats.multitest")
    np.testing.assert_allclose(adj[:4], sm.multipletests(p[:4], method="holm")[1])
