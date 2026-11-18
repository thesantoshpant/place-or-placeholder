"""Tests for the review sensitivity filters (scripts/analysis/review_sens.py)."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "analysis"))
sys.path.insert(0, str(ROOT / "scripts" / "run"))

import review_sens as RS  # noqa: E402
from pop.data.panel import epi_year  # noqa: E402
from pop.eval.estimands import weekly_pooled  # noqa: E402


@pytest.mark.parametrize("Y,expect", [(2020, "2019-12-22"), (2021, "2020-12-27"),
                                      (2022, "2021-12-26"), (2023, "2022-12-25"),
                                      (2024, "2023-12-24"), (2025, "2024-12-22")])
def test_last_train_week(Y, expect):
    w = RS.last_train_week(Y)
    assert w == pd.Timestamp(expect)
    assert w.weekday() == 6
    assert epi_year(pd.Series([w])).iloc[0] == Y - 1
    assert epi_year(pd.Series([w + pd.Timedelta(days=7)])).iloc[0] == Y


def _rows():
    # test year 2023: first target week 2023-01-01; last training label week 2022-12-25
    tw = pd.to_datetime(["2023-01-01", "2023-01-08", "2023-01-15", "2023-01-22", "2023-01-01",
                         "2023-02-05"])
    h = np.array([1, 4, 4, 4, 4, 4])
    return pd.DataFrame({"test_year": 2023, "target_week": tw, "horizon": h,
                         "origin_week": tw - pd.to_timedelta(7 * h, unit="D")})


def test_admissible_mask():
    g = _rows()
    m = RS.admissible_mask(g)
    # h1 first week: origin = 2022-12-25 = last label week -> kept;
    # h4 targets Jan 1/8/15 have origins before it -> dropped; Jan 22 origin = Dec 25 -> kept
    assert m.tolist() == [True, False, False, True, False, True]


def test_admissible_never_drops_h1():
    weeks = pd.date_range("2019-12-29", "2024-12-22", freq="7D")
    g = pd.DataFrame({"target_week": weeks, "horizon": 1})
    g["origin_week"] = g.target_week - pd.Timedelta(days=7)
    g["test_year"] = epi_year(g.target_week).to_numpy()
    assert RS.admissible_mask(g).all()
    g4 = g.assign(horizon=4, origin_week=g.target_week - pd.Timedelta(days=28))
    m = RS.admissible_mask(g4)
    assert (~m).sum() == 3 * g4.test_year.nunique()


def test_strata3():
    g = pd.DataFrame({"cases": [0, 0, 3, 0, 7], "zero_filled": [True, False, False, True, False]})
    s = RS.strata3(g)
    assert s["positive"].tolist() == [False, False, True, False, True]
    assert s["recorded_zero"].tolist() == [False, True, False, False, False]
    assert s["zero_filled"].tolist() == [True, False, False, True, False]
    tot = s["positive"].astype(int) + s["recorded_zero"] + s["zero_filled"]
    assert (tot == 1).all()
    with pytest.raises(ValueError):
        RS.strata3(pd.DataFrame({"cases": [2], "zero_filled": [True]}))


def _panel(T=156, U=5, seed=1):
    rng = np.random.default_rng(seed)
    weeks = pd.date_range("2020-01-05", periods=T, freq="7D")
    rows = []
    for h in (1, 4):
        for u in range(U):
            l3 = rng.gamma(2, 0.1, T)
            rows.append(pd.DataFrame({"unit_id": f"u{u}", "target_week": weeks, "horizon": h,
                                      "wis_L3": l3, "G_emb": rng.normal(0.002, 0.01, T),
                                      "G_id": rng.normal(0, 0.01, T),
                                      "G_excess": rng.normal(-0.001, 0.01, T)}))
    return pd.concat(rows, ignore_index=True).iloc[:-7]   # unbalanced on purpose


def test_week_bootstrap_matches_primary_point():
    g = _panel()
    b = RS.week_bootstrap(g, n_boot=200)
    for e in ("G_emb", "G_id", "G_excess"):
        assert np.isclose(b[e]["point"], weekly_pooled(g, e).mean())
        assert b[e]["boot_lo"] <= b[e]["point"] <= b[e]["boot_hi"]
    # differs from the row-level mean on an unbalanced panel
    assert not np.isclose(b["G_excess"]["point"], g.G_excess.mean())


def test_delta_ratio_ci():
    rng = np.random.default_rng(0)
    w = 0.2 + rng.normal(0, 0.02, 300)
    d = 0.001 + rng.normal(0, 0.002, 300)
    r = RS.delta_ratio_ci(d, w, h=4)
    assert np.isclose(r["ratio"], d.mean() / w.mean())
    assert r["lo95"] < r["lo90"] < r["ratio"] < r["hi90"] < r["hi95"]
    # constant denominator -> same as fixed-denominator inference of d / mean(w)
    from pop.eval.stats import ewc_inference
    rc = RS.delta_ratio_ci(d, np.full(300, 0.2), h=4)
    assert np.isclose(rc["se"], ewc_inference(d, h=4).se / 0.2)


def test_equivalence_label_and_near_margin():
    lab = RS.equivalence_label(-0.4, -0.6, -0.2, 0.001, 0.01, 0.001, 1)
    assert lab.startswith("small negative difference, significant after Holm")
    assert "within ±1% (TOST, Holm-adjusted)" in lab
    lab = RS.equivalence_label(1.0, 0.1, 1.9, 0.04, 0.3, 0.9, 1)
    assert lab.startswith("nominal positive difference, not significant after Holm")
    assert "not shown to be within ±1%" in lab
    lab = RS.equivalence_label(0.1, -0.5, 0.9, 0.5, 1.0, 0.2, 1)
    assert lab == "no significant difference; within ±1% (unadjusted TOST only)"
    assert RS.near_margin(-1.04, -0.3, 1)
    assert not RS.near_margin(-0.9, 0.5, 1)


def test_reader_filters_horizons_and_metric(tmp_path):
    d = tmp_path / "run"
    d.mkdir()
    s = pd.DataFrame({"run": "x", "seed": 0, "test_year": 2023, "unit_id": "a",
                      "origin_week": pd.to_datetime(["2023-01-01"] * 4),
                      "target_week": pd.to_datetime(["2023-01-08"] * 4), "horizon": [1, 2, 3, 4],
                      "cases": 1.0, "wis_log": [1., 2, 3, 4], "wis_case": [10., 20, 30, 40]})
    s.to_parquet(d / "scores.parquet", index=False)
    out = RS.make_reader("wis_case", [1, 4])([d], cols=("wis_log", "cases"))
    assert sorted(out.horizon) == [1, 4]
    assert sorted(out.wis_log) == [10., 40.]
    assert "wis_case" not in out
