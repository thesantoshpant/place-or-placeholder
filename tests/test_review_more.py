"""Tests of the weighting and recalibration helpers of scripts/analysis/review_more.py."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path[:0] = [str(Path(__file__).resolve().parents[1] / "scripts" / "analysis"),
                str(Path(__file__).resolve().parents[1] / "scripts" / "run")]
import review_more as RM  # noqa: E402
from pop.eval.estimands import infer_estimand, weekly_pooled  # noqa: E402


def _frame(seed=0, n_units=20, n_weeks=60):
    rng = np.random.default_rng(seed)
    wk = pd.date_range("2020-01-05", periods=n_weeks, freq="7D")
    rows = []
    for h in (1, 4):
        for t in wk:
            for u in range(n_units):
                rows.append((h, t, str(u)))
    g = pd.DataFrame(rows, columns=["horizon", "target_week", "unit_id"])
    g["wis_L3"] = rng.gamma(2.0, 0.1, len(g))
    g["G_excess"] = rng.normal(0.001, 0.01, len(g))
    for c in ("G_emb", "G_id"):
        g[c] = rng.normal(0, 0.01, len(g))
    return g


def test_weighted_weekly_none_equals_weekly_pooled():
    g = _frame()
    a = RM.weighted_weekly(g, "G_excess")
    b = weekly_pooled(g, "G_excess")
    pd.testing.assert_series_equal(a, b, check_names=False)


def test_weighted_weekly_constant_weights_and_known_value():
    g = _frame(n_units=2, n_weeks=12)
    w1 = np.full(len(g), 7.0)
    pd.testing.assert_series_equal(RM.weighted_weekly(g, "G_excess", w1),
                                   RM.weighted_weekly(g, "G_excess"))
    # weight only unit "0" -> weekly series = unit 0's value (mean over horizons)
    w = (g.unit_id == "0").astype(float).to_numpy()
    s = RM.weighted_weekly(g, "G_excess", w)
    exp = g[g.unit_id == "0"].groupby("target_week").G_excess.mean()
    np.testing.assert_allclose(s.to_numpy(), exp.to_numpy())


def test_weighted_weekly_ignores_nan_weights():
    g = _frame(n_units=3, n_weeks=12)
    w = np.ones(len(g))
    w[g.unit_id.to_numpy() == "2"] = np.nan
    s = RM.weighted_weekly(g, "G_excess", w)
    exp = weekly_pooled(g[g.unit_id != "2"], "G_excess")
    np.testing.assert_allclose(s.to_numpy(), exp.to_numpy())


def test_infer_weighted_unweighted_matches_primary():
    g = _frame()
    a = RM.infer_weighted(g, "G_excess")
    b = infer_estimand(g, "G_excess")
    for k in ("estimate", "se", "p", "lo95", "hi95", "wis_ref", "cls"):
        assert a[k] == pytest.approx(b[k]) if k != "cls" else a[k] == b[k]


def test_fit_shifts_gives_nominal_coverage():
    rng = np.random.default_rng(1)
    y = rng.normal(0, 1, 5000)
    q = np.tile(np.linspace(-0.2, 0.2, 9), (5000, 1))   # far too narrow
    s = RM.fit_shifts(y, q)
    qn = q + s
    cov = (y[:, None] <= qn).mean(axis=0)
    assert np.all(cov >= RM.QLEV - 1e-9)
    assert np.all(cov <= RM.QLEV + 0.01)


def test_apply_shifts_clips_and_sorts():
    q = np.array([[0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]])
    s = np.array([-1, 0.5, 0, 0, 0, 0, 0, 0, -0.5])
    out = RM.apply_shifts(q, s)
    assert out.min() >= 0
    assert np.all(np.diff(out, axis=1) >= 0)


def test_causal_recalibrate_first_year_unchanged_and_no_lookahead():
    rng = np.random.default_rng(2)
    n = 3000
    year = np.repeat([2020, 2021, 2022], n)
    h = np.tile([1, 4], 3 * n // 2)
    y = np.abs(rng.normal(1, 1, 3 * n))
    q = np.sort(np.abs(rng.normal(1, 0.3, (3 * n, 9))), axis=1)
    out, rows = RM.causal_recalibrate(year, h, y, q, mode="global")
    np.testing.assert_array_equal(out[year == 2020], q[year == 2020])
    # changing the truth of 2022 must not change the 2021 or 2022 adjustments
    y2 = y.copy()
    y2[year == 2022] += 100
    out2, _ = RM.causal_recalibrate(year, h, y2, q, mode="global")
    np.testing.assert_array_equal(out[year <= 2022], out2[year <= 2022])
    # 2022 shifts use 2020 and 2021 rows of the same horizon
    r = [x for x in rows if x["year"] == 2022 and x["horizon"] == 1][0]
    assert r["n_fit"] == int(((year < 2022) & (h == 1)).sum())


def test_causal_recalibrate_mondrian_fallback():
    rng = np.random.default_rng(3)
    n = 1000
    year = np.repeat([2020, 2021], n)
    h = np.ones(2 * n, int)
    y = np.abs(rng.normal(0, 1, 2 * n))
    q = np.sort(np.abs(rng.normal(0, 0.05, (2 * n, 9))), axis=1)   # medians in bin 0
    q[-5:] += 3.0                                                     # few rows in bin 3
    _, rows = RM.causal_recalibrate(year, h, y, q, mode="mondrian", min_bin=200)
    by_bin = {r["bin"]: r for r in rows}
    assert by_bin[3]["fallback_global"] is True
    assert by_bin[0]["fallback_global"] is False


def test_pinball_parts_sum_to_wis():
    from pop.eval.scoring import wis_interval
    rng = np.random.default_rng(4)
    y = np.abs(rng.normal(1, 1, 200))
    q = np.sort(np.abs(rng.normal(1, 1, (200, 9))), axis=1)
    np.testing.assert_allclose(RM.pinball_parts(y, q).sum(axis=1),
                               wis_interval(y, RM.QLEV, q, log1p=False))


def test_contribution_series_is_additive():
    g = _frame(n_units=5, n_weeks=15)
    m = g.unit_id.isin(["0", "1"]).to_numpy()
    a = RM.contribution_series(g, "G_excess", m)
    b = RM.contribution_series(g, "G_excess", ~m)
    np.testing.assert_allclose((a + b).to_numpy(), weekly_pooled(g, "G_excess").to_numpy())
