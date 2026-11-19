"""Round-3 representation variants (pop.features.variants): additivity, no target leakage, held-out
units never used, matched leave-out, V2/V3/L2+AE construction."""
import numpy as np
import pandas as pd
import pytest

from pop.features import levels as LV
from pop.features import variants as VA
from pop.splits import splits as SP
from test_levels import ctx, grid, panel, rows, split_dir, tables  # noqa: F401 (fixtures)

ORIGINAL = ({"L0", "L1", "L2", "L3", "L4"} | {f"L3+{c}" for c in LV.CONTROLS}
            | {f"L4+{c}" for c in LV.CONTROLS} | set(LV.NOHIST_LEVELS))


def mk(sp, pan=None, tabs=None, **opt):
    c = ctx(tabs, **opt)
    c.panel, c.split = (panel() if pan is None else pan), sp
    return c


def test_existing_levels_untouched():
    assert VA._CONTROLS == LV.CONTROLS
    assert ORIGINAL <= set(LV.LEVELS)
    assert not ORIGINAL & set(VA.VARIANT_LEVELS)
    for name in ORIGINAL:  # registry entries are still the levels module's own functions
        assert LV.LEVELS[name].__module__ == "pop.features.levels"
    assert set(LV.LEVELS) == ORIGINAL | set(VA.VARIANT_LEVELS)


@pytest.mark.parametrize("variant,ncol,prefix", [("V1", 1, "v1_"), ("V2", 8, "v2_pc"), ("V3", 64, "v3_A")])
@pytest.mark.parametrize("control", [None, "C1"])
def test_variant_levels_extend_l3_and_l3c(grid, split_dir, variant, ncol, prefix, control):
    idx = rows(grid, 1)
    sp = SP.get_split("S1", "BRAZIL", None, 2022, split_dir=split_dir)
    base = LV.LEVELS["L3" if control is None else f"L3+{control}"](grid, idx, 1, mk(sp))
    name = f"L3+{variant}" if control is None else f"L3+{control}+{variant}"
    X = LV.LEVELS[name](grid, idx, 1, mk(sp))
    extra = list(X.columns[base.shape[1]:])
    assert len(extra) == ncol and all(k.startswith(prefix) for k in extra)
    pd.testing.assert_frame_equal(X[list(base.columns)], base)
    assert not any(k.startswith("ae_") for k in X.columns)
    assert X[extra].notna().all().all()


def test_l2_ae_is_l2_plus_l4_embedding_block(grid):
    idx = rows(grid, 2)
    l2 = LV.LEVELS["L2"](grid, idx, 2, ctx())
    l4 = LV.LEVELS["L4"](grid, idx, 2, ctx())
    X = LV.LEVELS["L2+AE"](grid, idx, 2, ctx())
    ae = [f"ae_{i:02d}" for i in range(64)]
    assert list(X.columns) == list(l2.columns) + ae
    pd.testing.assert_frame_equal(X[list(l2.columns)], l2)
    pd.testing.assert_frame_equal(X[ae], l4[ae])


@pytest.mark.parametrize("split,fold", [("S1", None), ("S4", 0), ("S2", 0)])
def test_v1_ignores_post_pretrain_and_heldout_targets(grid, split_dir, split, fold):
    idx = rows(grid, 1)
    sp = SP.get_split(split, "BRAZIL", fold, 2022, split_dir=split_dir)
    a = VA.v1_block(grid, idx, mk(sp))
    p = panel()
    bad = (p.year >= 2018) | p.unit_id.isin(sp.test_units - sp.train_units)
    p.loc[bad, "cases"] = 1e12
    b = VA.v1_block(grid, idx, mk(sp, pan=p))
    pd.testing.assert_frame_equal(a, b)
    # and pre-2018 training outcomes do matter (the feature is not constant noise)
    p2 = panel()
    p2.loc[p2.year < 2018, "cases"] *= 50
    assert not VA.v1_block(grid, idx, mk(sp, pan=p2)).equals(a)


def test_v1_excludes_self_in_seen_split():
    st = pd.DataFrame(np.eye(3, 64), index=["a", "b", "c"], columns=LV.AE_BANDS)
    ud = pd.DataFrame({"unit_id": list("abc"), "country": "X", "adm1": "A", "lat": 0.0, "lon": 0.0})
    vals = pd.Series({"a": 1.0, "b": 2.0, "c": 4.0})
    s = VA.ae_knn_encode(list("abc"), vals, st, ud, k=5)
    assert s["a"] == pytest.approx(3.0) and s["b"] == pytest.approx(2.5)  # equidistant others


def test_v1_matched_group_and_heldout_pool():
    rng = np.random.default_rng(0)
    V = rng.normal(size=(6, 64))
    st = pd.DataFrame(V / np.linalg.norm(V, axis=1, keepdims=True), index=list("abcdef"), columns=LV.AE_BANDS)
    ud = pd.DataFrame({"unit_id": list("abcdef"), "country": "X", "adm1": list("AABBCC"),
                       "lat": 0.0, "lon": np.arange(6.0)})
    vals = pd.Series({"a": 1.0, "b": 2.0, "c": 3.0, "d": 4.0})  # e, f held out (not in pool)
    s = VA.ae_knn_encode(list("abcdef"), vals, st, ud, k=1, matched_queries=list("abcd"),
                         exclude_group="adm1")
    for u, allowed in {"a": "cd", "b": "cd", "c": "ab", "d": "ab"}.items():
        assert s[u] in {vals[x] for x in allowed}  # never self, never own adm1
    assert s["e"] in set(vals) and s["f"] in set(vals)
    s2 = VA.ae_knn_encode(list("ab"), vals, st, ud, k=5, matched_queries=list("ab"),
                          exclude_within_km=1e5)
    assert s2.isna().all()


def test_v2_pca_fit_on_training_units_and_years_only(grid, split_dir):
    idx = rows(grid, 1)
    sp = SP.get_split("S4", "BRAZIL", 0, 2022, split_dir=split_dir)
    tr_rows = np.isin(grid.units[idx["u"].to_numpy()], list(sp.train_units))
    a = VA.v2_block(grid, idx, mk(sp))
    tabs = tables()
    ae = tabs["alphaearth"]
    held = ae.unit_id.isin(sp.test_units - sp.train_units) | (ae.year >= 2021)  # not in the fit
    cols = [c for c in ae.columns if c.startswith("w_")]
    ae.loc[held, cols] = ae.loc[held, cols].to_numpy() * 7 + 3
    b = VA.v2_block(grid, idx, mk(sp, tabs=tabs))
    # rows of training units whose y-1 vector was not altered keep identical PCs
    yrs = grid.year[idx["t"].to_numpy()] - 1
    keep = tr_rows & (yrs < 2021)
    assert keep.any()
    np.testing.assert_array_equal(a.to_numpy()[keep], b.to_numpy()[keep])
    mu, C = VA.fit_pca(np.random.default_rng(1).normal(size=(50, 64)))
    np.testing.assert_allclose(C @ C.T, np.eye(8), atol=1e-10)


def test_v3_static_mean_2017_2018_renormalised(grid, split_dir):
    idx = rows(grid, 1)
    sp = SP.get_split("S1", "BRAZIL", None, 2022, split_dir=split_dir)
    X = VA.v3_block(grid, idx, mk(sp)).to_numpy(float)
    np.testing.assert_allclose(np.linalg.norm(X, axis=1), 1.0, rtol=1e-5)
    e = ctx().embeddings()
    for i in range(0, len(idx), 5):
        u = grid.units[idx.u.iloc[i]]
        v = e[(e.unit_id == u) & e.year.isin([2017, 2018])][LV.AE_BANDS].to_numpy().mean(0)
        np.testing.assert_allclose(X[i], v / np.linalg.norm(v), rtol=1e-5)
    # poisoning embeddings of years >= 2019 changes nothing
    tabs = tables()
    ae = tabs["alphaearth"]
    cols = [c for c in ae.columns if c.startswith(("w_", "u_"))]
    ae.loc[ae.year >= 2019, cols] = 1e6
    np.testing.assert_array_equal(X, VA.v3_block(grid, idx, mk(sp, tabs=tabs)).to_numpy(float))
