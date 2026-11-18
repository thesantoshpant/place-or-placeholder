import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "analysis"))
import review_explore as RE  # noqa: E402

from pop.eval.scoring import wis_interval  # noqa: E402


def test_terciles_balanced_and_nan():
    x = pd.Series([5, 1, 3, 2, 4, 6, np.nan])
    t = RE.terciles(x)
    assert t.iloc[-1] is pd.NA or pd.isna(t.iloc[-1])
    assert t.iloc[:6].value_counts().to_dict() == {"T1": 2, "T2": 2, "T3": 2}
    assert t[1] == "T1" and t[5] == "T3"


def test_history_group():
    assert list(RE.history_group([0, 1, 2, 3, 4])) == ["0", "1-2", "1-2", "3-4", "3-4"]


def test_built_inverse():
    s10, s15 = np.array([0.1, 0.2]), np.array([0.2, 0.25])
    s13 = s10 + 0.6 * (s15 - s10)
    assert np.allclose(RE.built_2010_from_yearly(s13, s15), s10)


def test_cosine_to_train():
    rng = np.random.default_rng(0)
    tr = RE.renorm(rng.normal(size=(20, 8)))
    te = np.vstack([tr[3], RE.renorm(rng.normal(size=(1, 8)))[0], np.full(8, np.nan)])
    mx, k5 = RE.cosine_to_train(te, tr, k=5)
    assert np.isclose(mx[0], 1.0) and mx[1] < 1 and np.isnan(mx[2])
    assert k5[0] <= mx[0]
    s = te[1] @ tr.T
    assert np.isclose(k5[1], np.sort(s)[-5:].mean())


def test_zero_row_parts_match_wis():
    rng = np.random.default_rng(1)
    v = np.sort(np.abs(rng.gamma(1.0, 3.0, size=(50, 9))), axis=1)
    ref = wis_interval(np.zeros(50), RE.QLEV, v, log1p=True)
    p = RE.zero_row_parts(np.log1p(v))
    assert np.allclose(p["total"], ref)
    assert np.allclose(p["upper"] + p["median"] + p["lower"], p["total"])


def _toy(seed=0):
    rng = np.random.default_rng(seed)
    n = 3000
    g = pd.DataFrame({"unit_id": rng.integers(0, 60, n).astype(str),
                      "target_week": pd.to_datetime("2020-01-05")
                      + pd.to_timedelta(7 * rng.integers(0, 80, n), "D"),
                      "horizon": rng.choice([1, 4], n),
                      "s": rng.choice(["a", "b", "c"], n, p=[.6, .3, .1])})
    g["G_excess"] = rng.normal(0.01 * (g.s == "a") - 0.02 * (g.s == "b"), 0.05)
    g["wis_L3"] = rng.gamma(2, 0.1, n)
    return g


def test_week_contributions_identity():
    g = _toy()
    c, tot = RE.week_contributions(g, "G_excess", "s")
    assert np.allclose(c.sum(axis=1), tot)
    assert np.isclose(c.sum(axis=1).mean(), tot.mean())


def test_decompose_identity_and_naive_gap():
    g = _toy(2)
    d = RE.decompose(g, "G_excess", "s")
    assert abs(d.identity_residual.iloc[0]) < 1e-12
    st = d[d.stratum != "TOTAL"]
    tot = d[d.stratum == "TOTAL"].estimate.iloc[0]
    assert np.isclose(st.contribution.sum(), tot)
    assert np.isclose(d[d.stratum == "TOTAL"].contribution.iloc[0], tot)
