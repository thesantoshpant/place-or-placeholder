import warnings

import numpy as np
import pandas as pd
import pytest

from pop.eval import scoring as S

L3 = [0.1, 0.5, 0.9]


def test_hand_examples():
    v = np.array([[2.0, 5.0, 8.0]] * 3)
    y = np.array([10.0, 4.0, 5.0])
    # y=10: (0.5*5 + 0.1*(6 + 10*2))/1.5 = 3.4 ; y=4: (0.5 + 0.6)/1.5 ; y=5: 0.6/1.5
    exp = np.array([3.4, 1.1 / 1.5, 0.6 / 1.5])
    np.testing.assert_allclose(S.wis_interval(y, L3, v), exp)
    np.testing.assert_allclose(S.wis_quantile(y, L3, v), exp)


def test_median_only_is_abs_error():
    np.testing.assert_allclose(S.wis_interval([3.0], [0.5], [[1.0]]), [2.0 * 0.5 / 0.5])


@pytest.mark.parametrize("qs", [S.PRIMARY_QUANTILES, S.CDC_QUANTILES])
def test_forms_agree_random(qs):
    rng = np.random.default_rng(1)
    n = 500
    v = np.sort(rng.gamma(2, 10, size=(n, len(qs))), axis=1)
    y = rng.gamma(2, 10, size=n)
    a = S.wis_interval(y, qs, v)
    b = S.wis_quantile(y, qs, v)
    np.testing.assert_allclose(a, b, rtol=1e-12)
    assert np.all(a >= 0)


@pytest.mark.parametrize("qs", [S.PRIMARY_QUANTILES, S.CDC_QUANTILES])
def test_scoringrules_crosscheck(qs):
    sr = pytest.importorskip("scoringrules")
    rng = np.random.default_rng(2)
    n = 300
    v = np.sort(rng.normal(0, 3, size=(n, len(qs))), axis=1)
    y = rng.normal(0, 3, size=n)
    lv = np.asarray(qs)
    alphas = S.interval_alphas(qs)
    lo = np.stack([v[:, np.isclose(lv, a / 2)][:, 0] for a in alphas], axis=1)
    hi = np.stack([v[:, np.isclose(lv, 1 - a / 2)][:, 0] for a in alphas], axis=1)
    med = v[:, np.isclose(lv, 0.5)][:, 0]
    # Build WIS from scoringrules' interval_score (its weighted_interval_score
    # has differed from the standard definition in some versions; not relied on).
    IS = np.asarray(sr.interval_score(y, lo, hi, alphas))
    ref = (0.5 * np.abs(y - med) + (IS * alphas / 2).sum(axis=1)) / (len(alphas) + 0.5)
    np.testing.assert_allclose(S.wis_interval(y, qs, v), ref, rtol=1e-8)


def test_perfect_forecast_zero():
    y = np.array([0.0, 7.0, 123.0])
    v = np.repeat(y[:, None], 9, axis=1)
    np.testing.assert_allclose(S.wis_interval(y, S.PRIMARY_QUANTILES, v), 0.0)
    np.testing.assert_allclose(S.wis_quantile(y, S.PRIMARY_QUANTILES, v, log1p=True), 0.0)


def test_log1p_option():
    v = np.array([[2.0, 5.0, 8.0]])
    y = np.array([10.0])
    np.testing.assert_allclose(S.wis_interval(y, L3, v, log1p=True),
                               S.wis_interval(np.log1p(y), L3, np.log1p(v)))


def test_nan_propagates():
    v = np.array([[2.0, np.nan, 8.0], [2.0, 5.0, 8.0]])
    y = np.array([4.0, np.nan])
    assert np.all(np.isnan(S.wis_interval(y, L3, v)))
    assert np.all(np.isnan(S.wis_quantile(y, L3, v)))
    np.testing.assert_array_equal(S.coverage(y, L3, v, 0.8), [1.0, np.nan])  # 80% PI intact


def test_crossing_sorted_with_warning():
    v = np.array([[8.0, 5.0, 2.0], [2.0, 5.0, 8.0]])
    with pytest.warns(UserWarning, match="1 forecast"):
        a = S.wis_interval([10.0, 10.0], L3, v)
    assert a[0] == pytest.approx(a[1])
    _, n = S.sort_crossing(v)
    assert n == 1


def test_asymmetric_set_rejected():
    with pytest.raises(ValueError):
        S.interval_alphas([0.1, 0.5, 0.8])
    with pytest.raises(ValueError):
        S.interval_alphas([0.1, 0.9])


def test_coverage():
    v = np.tile(np.arange(1, 10, dtype=float), (4, 1))  # q0.1..0.9 = 1..9
    y = np.array([5.0, 3.0, 2.0, 9.5])
    np.testing.assert_array_equal(S.coverage(y, S.PRIMARY_QUANTILES, v, 0.4), [1, 1, 0, 0])
    np.testing.assert_array_equal(S.coverage(y, S.PRIMARY_QUANTILES, v, 0.8), [1, 1, 1, 0])
    with pytest.raises(ValueError):
        S.coverage(y, S.PRIMARY_QUANTILES, v, 0.5)


def _long(rng, models=("A", "B"), n_units=3, n_weeks=5, qs=S.CDC_QUANTILES):
    rows = []
    for m in models:
        for u in range(n_units):
            for w in range(n_weeks):
                for h in (1, 2):
                    vals = np.sort(rng.gamma(2, 10, size=len(qs)))
                    for q, val in zip(qs, vals):
                        rows.append((m, u, w, w + h, h, q, val))
    fc = pd.DataFrame(rows, columns=["model", "unit_id", "origin_week", "target_week",
                                     "horizon", "quantile", "value"])
    truth = pd.DataFrame([(u, w, rng.poisson(20)) for u in range(n_units)
                          for w in range(n_weeks + 3)], columns=["unit_id", "target_week", "cases"])
    return fc, truth


def test_score_forecasts_and_aggregate():
    rng = np.random.default_rng(3)
    fc, truth = _long(rng)
    sc = S.score_forecasts(fc, truth)  # primary deciles subset of the 23
    assert len(sc) == 2 * 3 * 5 * 2
    assert {"wis", "ae_median", "cov_40", "cov_80"} <= set(sc.columns)
    # matches direct computation
    r = sc.iloc[0]
    sub = fc[(fc.model == r.model) & (fc.unit_id == r.unit_id) & (fc.origin_week == r.origin_week)
             & (fc.horizon == r.horizon)]
    sub = sub[sub["quantile"].round(6).isin(np.round(S.PRIMARY_QUANTILES, 6))].sort_values("quantile")
    exp = S.wis_interval([r.cases], S.PRIMARY_QUANTILES, [sub.value.to_numpy()], log1p=True)
    assert r.wis == pytest.approx(exp[0])
    sc2 = S.score_forecasts(fc, truth, quantiles=S.CDC_QUANTILES, scale="case",
                            coverage_levels=S.SECONDARY_COVERAGE)
    assert {"cov_50", "cov_90"} <= set(sc2.columns)
    agg = S.aggregate_scores(sc, by=["split", "horizon", "model"])
    assert len(agg) == 4 and agg["n"].sum() == len(sc)
    np.testing.assert_allclose(agg.wis.mean(), sc.wis.mean())


def test_score_forecasts_missing_quantile_and_truth():
    rng = np.random.default_rng(4)
    fc, truth = _long(rng, models=("A",), n_units=1, n_weeks=2, qs=S.PRIMARY_QUANTILES)
    fc = fc[~((fc.origin_week == 0) & (fc.horizon == 1) & np.isclose(fc["quantile"], 0.3))]
    truth = truth[truth.target_week != 3]
    sc = S.score_forecasts(fc, truth).set_index(["origin_week", "horizon"])
    assert np.isnan(sc.loc[(0, 1), "wis"])       # missing quantile
    assert np.isnan(sc.loc[(1, 2), "wis"])       # missing truth (target week 3)
    assert np.isfinite(sc.loc[(0, 2), "wis"])
    agg = S.aggregate_scores(sc.reset_index(), by=["model"])
    assert agg["n"].iloc[0] == 2
