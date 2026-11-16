import numpy as np
import pandas as pd
import pytest

from pop.features import history as H


def synth_panel(n_units=3, start="2013-12-29", n_weeks=320, seed=0):
    rng = np.random.default_rng(seed)
    weeks = pd.date_range(start, periods=n_weeks, freq="7D")
    rows = []
    for u in range(n_units):
        lam = 5 + 4 * np.sin(2 * np.pi * np.arange(n_weeks) / 52.18 + u)
        rows.append(pd.DataFrame({"unit_id": f"U{u}", "country": "X", "adm1": "A",
                                  "adm2": f"B{u}", "week_start": weeks,
                                  "cases": rng.poisson(lam).astype(float),
                                  "observed": True, "zero_filled": False, "flag_gap": False}))
    p = pd.concat(rows, ignore_index=True)
    p["year"] = (p["week_start"] + pd.Timedelta(days=3)).dt.year
    return p


@pytest.mark.parametrize("h", [1, 2, 3, 4])
@pytest.mark.parametrize("level", ["l0_features", "l1_features"])
def test_no_future_leakage(h, level):
    g = H.make_grid(synth_panel())
    target = np.arange(200, 260)
    idx = H.design_index(g, target, h)
    X = getattr(H, level)(g, idx, h)
    # poison every week after each origin, recompute: features must not change
    for o in np.unique(idx["o"])[::7]:
        gp = H.make_grid(synth_panel())
        gp.y[:, o + 1:] = 1e9
        rows = idx["o"] == o
        Xp = getattr(H, level)(gp, idx[rows], h)
        pd.testing.assert_frame_equal(X[rows], Xp)
        assert (Xp.abs() < 1e8).all().all()


def test_lag_values_and_guard():
    g = H.make_grid(synth_panel())
    idx = H.design_index(g, np.array([250]), 2)
    X = H.l1_features(g, idx, 2)
    assert np.allclose(X["lag_0"], g.y[:, 248])
    assert np.allclose(X["lag_11"], g.y[:, 237])
    assert np.allclose(X["sy1_0"], g.y[:, 250 - 52])
    assert np.allclose(X["sy3_p1"], g.y[:, 250 - 156 + 1])
    with pytest.raises(AssertionError):
        H._take(g.y, np.array([0]), np.array([10]), np.array([9]))


def test_l1_has_no_location_columns():
    g = H.make_grid(synth_panel())
    X = H.l1_features(g, H.design_index(g, np.arange(200, 210), 1), 1)
    H.assert_no_location(X.columns)
    assert len(X.columns) == 12 + 9 + 2
    for bad in ["unit_id", "adm2", "lat", "lon", "country"]:
        assert bad not in X.columns
    # identical history -> identical features regardless of unit label
    p = synth_panel()
    p2 = p.copy()
    p2["unit_id"] = p2["unit_id"].map({"U0": "Z9", "U1": "Z8", "U2": "Z7"})
    X2 = H.l1_features(H.make_grid(p2), H.design_index(H.make_grid(p2), np.arange(200, 210), 1), 1)
    assert sorted(map(tuple, X.round(9).to_numpy())) == sorted(map(tuple, X2.round(9).to_numpy()))
    with pytest.raises(AssertionError):
        H.assert_no_location(["lag_0", "unit_id"])
