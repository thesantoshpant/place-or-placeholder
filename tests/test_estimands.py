import numpy as np
import pandas as pd
import pytest

from pop.eval import estimands as E

MODELS = {"L3": "l3", "L4": "l4", "L3C": "l3c", "L4C": "l4c"}


def _scores(rng, eff, C=10, U=3, T=40):
    """eff: per-model mean WIS offsets (lower = better)."""
    rows = []
    base = rng.gamma(4, 0.25, size=(C, U, T))
    for name, off in eff.items():
        noise = 0.02 * rng.normal(size=(C, U, T))
        w = base + off + noise
        for c in range(C):
            for u in range(U):
                for t in range(T):
                    rows.append((name, c * U + u, c, t, t + 1, 1, w[c, u, t]))
    return pd.DataFrame(rows, columns=["model", "unit_id", "state", "origin_week",
                                       "target_week", "horizon", "wis"])


def test_gain_frame_signs():
    rng = np.random.default_rng(0)
    sc = _scores(rng, {"l3": 0.5, "l4": 0.3, "l3c": 0.35, "l4c": 0.33}, C=3, T=5)
    g = E.gain_frame(sc, MODELS, extra_cols=["state"])
    assert len(g) == 3 * 3 * 5
    assert g.G_emb.mean() == pytest.approx(0.2, abs=0.02)
    assert g.G_id.mean() == pytest.approx(0.15, abs=0.02)
    assert g.G_excess.mean() == pytest.approx(0.02, abs=0.02)
    np.testing.assert_allclose(g.G_emb, g.wis_L3 - g.wis_L4)


def test_gain_frame_inner_join_drops_missing():
    rng = np.random.default_rng(1)
    sc = _scores(rng, {"l3": 0.5, "l4": 0.3, "l3c": 0.35, "l4c": 0.33}, C=2, T=4)
    sc = sc.drop(sc[(sc.model == "l4c") & (sc.unit_id == 0)].index)
    g = E.gain_frame(sc, MODELS, extra_cols=["state"])
    assert 0 not in set(g.unit_id) and len(g) == (2 * 3 - 1) * 4


def test_select_best_control():
    rng = np.random.default_rng(2)
    sc = _scores(rng, {"a": 0.4, "b": 0.2, "c": 0.3}, C=2, T=4)
    assert E.select_best_control(sc, ["a", "b", "c"]) == "b"


@pytest.mark.parametrize("g,lo,hi,w,ok", [
    (0.2, 0.1, 0.3, 1.0, True),
    (0.2, -0.1, 0.3, 1.0, False),    # CI includes 0
    (0.005, 0.001, 0.009, 1.0, False),  # < 1% of WIS(L3)
    (-0.2, -0.3, -0.1, 1.0, False),  # significant worsening
    (0.01, 0.005, 0.02, 1.0, True),  # exactly 1%
])
def test_id_share_gate(g, lo, hi, w, ok):
    res, reason = E.id_share_gate(g, lo, hi, w)
    assert res is ok
    assert (reason == "") is ok
    if not ok:
        assert reason.startswith("not estimable")


def test_compute_estimands_reported():
    rng = np.random.default_rng(3)
    sc = _scores(rng, {"l3": 0.5, "l4": 0.3, "l3c": 0.35, "l4c": 0.33})
    g = E.gain_frame(sc, MODELS, extra_cols=["state"])
    r = E.compute_estimands(g, n_boot=200, seed=0)
    assert r["G_emb"]["lo"] > 0
    assert r["ID_share"]["reason"] == ""
    assert r["ID_share"]["estimate"] == pytest.approx(g.G_id.mean() / g.G_emb.mean())
    assert r["ID_share"]["lo"] < 0.75 < r["ID_share"]["hi"]
    assert r == E.compute_estimands(g, n_boot=200, seed=0)


def test_compute_estimands_not_estimable():
    rng = np.random.default_rng(4)
    sc = _scores(rng, {"l3": 0.5, "l4": 0.5, "l3c": 0.4, "l4c": 0.4})  # G_emb ~ 0
    g = E.gain_frame(sc, MODELS, extra_cols=["state"])
    r = E.compute_estimands(g, n_boot=200, seed=0)
    assert np.isnan(r["ID_share"]["estimate"])
    assert r["ID_share"]["reason"].startswith("not estimable")
    assert np.isfinite(r["G_excess"]["estimate"])
