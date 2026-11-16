import numpy as np
import pandas as pd
import pytest

from pop.eval import estimands as E
from pop.eval import stats as ST

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


# ======================================================== inference policy v2
def _seed_scores(rng, eff, seeds_by_model, C=6, U=3, T=60, H=(1, 4), seed_sd=0.01):
    rows = []
    base = rng.gamma(4, 0.25, size=(C, U, T))
    for name, off in eff.items():
        for h in H:
            for s in seeds_by_model[name].get(h, []):
                w = base + off + 0.02 * rng.normal(size=base.shape) + seed_sd * rng.normal()
                for c in range(C):
                    for u in range(U):
                        for t in range(T):
                            rows.append((name, s, c * U + u, c, t, t + h, h, w[c, u, t]))
    return pd.DataFrame(rows, columns=["model", "seed", "unit_id", "state", "origin_week",
                                       "target_week", "horizon", "wis"])


def test_seed_gain_frame_single_seed_matches_gain_frame():
    rng = np.random.default_rng(5)
    one = {m: {1: [0], 4: [0]} for m in MODELS.values()}
    sc = _seed_scores(rng, {"l3": .5, "l4": .4, "l3c": .45, "l4c": .41}, one, T=10)
    g2 = E.seed_gain_frame(sc, MODELS)
    g1 = E.gain_frame(sc, MODELS)
    m = g1.merge(g2, on=list(E.KEYS))
    for e in E.ESTIMANDS:
        np.testing.assert_allclose(m[f"{e}_x"], m[f"{e}_y"])
        np.testing.assert_allclose(m[f"{e}@0"], m[f"{e}_y"])
    assert g2.attrs["seeds"] == [0]


def test_seed_gain_frame_mixed_seeds_and_fill_rule():
    rng = np.random.default_rng(6)
    sb = {"l3": {1: [0, 1, 2], 4: [0, 1, 2]}, "l4": {1: [0, 1, 2], 4: [0]},
          "l3c": {1: [0], 4: [0]}, "l4c": {1: [0, 2], 4: [0, 2]}}
    sc = _seed_scores(rng, {"l3": .5, "l4": .4, "l3c": .45, "l4c": .41}, sb, T=8)
    g = E.seed_gain_frame(sc, MODELS)
    assert g.attrs["seeds"] == [0, 1, 2]
    r = g.iloc[0]
    k = sc[(sc.unit_id == r.unit_id) & (sc.origin_week == r.origin_week) & (sc.horizon == r.horizon)]
    l3 = k[k.model == "l3"].set_index("seed").wis
    l4c = k[k.model == "l4c"].set_index("seed").wis
    l3c = k[k.model == "l3c"].set_index("seed").wis
    assert r.wis_L3 == pytest.approx(l3.mean())
    # seed 1: l3c and l4c lack it -> their seed-averaged losses
    assert r["G_excess@1"] == pytest.approx(l3c.mean() - l4c.mean())
    assert r["G_excess@2"] == pytest.approx(l3c.loc[0] - l4c.loc[2])
    assert r["G_id@1"] == pytest.approx(l3.loc[1] - l3c.loc[0])
    # h4 rows: L4 has only seed 0, so seed 1 is present only via L3
    h4 = g[g.horizon == 4]
    assert h4["has@1"].all()
    # seed mean of per-seed estimands == estimate on seed-averaged losses (linear)
    res = E.infer_estimand(g, "G_emb")
    assert res["n_seeds"] == 3 and np.isfinite(res["seed_sd"])
    with pytest.raises(ValueError):
        E.seed_gain_frame(pd.concat([sc, sc[sc.model == "l3"].head(3)]), MODELS)


def test_seed_mean_equals_estimate_when_complete():
    rng = np.random.default_rng(7)
    sb = {m: {1: [0, 1, 2], 4: [0, 1, 2]} for m in MODELS.values()}
    sc = _seed_scores(rng, {"l3": .5, "l4": .4, "l3c": .45, "l4c": .41}, sb, T=12)
    g = E.seed_gain_frame(sc, MODELS)
    r = E.infer_estimand(g, "G_excess")
    assert r["seed_mean"] == pytest.approx(r["estimate"])
    sds = list(r["seed_estimates"].values())
    assert r["seed_sd"] == pytest.approx(np.std(sds, ddof=1))


def test_infer_estimand_pooled_construction():
    rng = np.random.default_rng(8)
    one = {m: {1: [0], 4: [0]} for m in MODELS.values()}
    sc = _seed_scores(rng, {"l3": .5, "l4": .4, "l3c": .45, "l4c": .41}, one)
    g = E.seed_gain_frame(sc, MODELS)
    r = E.infer_estimand(g, "G_excess")
    wk = g.groupby(["horizon", "target_week"]).G_excess.mean().groupby("target_week").mean()
    ref = ST.ewc_inference(wk.to_numpy(), h=4)
    assert r["estimate"] == pytest.approx(ref.estimate) and r["p"] == pytest.approx(ref.p)
    assert r["lo95"] == pytest.approx(ref.lo95) and r["T"] == wk.size
    wref = g.groupby(["horizon", "target_week"]).wis_L3.mean().groupby("target_week").mean().mean()
    assert r["margin"] == pytest.approx(0.01 * wref)
    r1 = E.infer_estimand(g[g.horizon == 1], "G_excess")
    w1 = g[g.horizon == 1].groupby("target_week").G_excess.mean()
    assert r1["estimate"] == pytest.approx(w1.mean()) and r1["h"] == 1


def test_compute_estimands_v2_classes():
    rng = np.random.default_rng(9)
    one = {m: {1: [0], 4: [0]} for m in MODELS.values()}
    # G_emb large (superior), G_excess ~ 0 with tiny noise (equivalent at 1% margin)
    sc = _seed_scores(rng, {"l3": .5, "l4": .3, "l3c": .45, "l4c": .45}, one, T=80, seed_sd=0.0)
    ex = sc.drop_duplicates(list(E.KEYS)).set_index(list(E.KEYS))[["state"]]
    g = E.seed_gain_frame(sc, MODELS, extra=ex)
    assert g.state.notna().all()
    r = E.compute_estimands_v2(g, n_boot=200, seed=0)
    assert r["G_emb"]["cls"] == "superior"
    assert r["G_excess"]["cls"] == "equivalent"
    assert r["G_emb"]["boot_lo"] < r["G_emb"]["estimate"] < r["G_emb"]["boot_hi"]
    assert r["ID_share"]["reason"] == ""
    assert r["ID_share"]["estimate"] == pytest.approx(r["G_id"]["estimate"] / r["G_emb"]["estimate"])
    sc2 = _seed_scores(rng, {"l3": .5, "l4": .5, "l3c": .45, "l4c": .45}, one, T=80, seed_sd=0.0)
    r2 = E.compute_estimands_v2(E.seed_gain_frame(sc2, MODELS), bootstrap=False, cluster_col=None)
    assert np.isnan(r2["ID_share"]["estimate"])
