import numpy as np
import pandas as pd
import pytest

from pop.splits import spatial as sp
from pop.splits import splits as S

pytestmark = pytest.mark.skipif(not (S.SPLIT_DIR / "unit_folds.parquet").exists(),
                                reason="run scripts/splits/build_splits.py first")


@pytest.fixture(scope="module")
def uf():
    return S.load_unit_folds()


@pytest.fixture(scope="module")
def ex():
    return S.load_buffer_exclusions()


@pytest.mark.parametrize("name", S.SPLITS)
def test_years_no_leakage(name):
    for s in S.iter_folds(name, include_tuning=True):
        assert max(s.train_years) < min(s.test_years) == s.origin
        assert min(s.train_years) == S.TRAIN_START
        assert s.origin <= S.LAST_YEAR[s.country]


@pytest.mark.parametrize("name", ["S2", "S2L", "S3", "S3B", "S4", "S5"])
def test_units_disjoint(name):
    for s in S.iter_folds(name):
        assert s.test_units and s.train_units
        assert not (s.train_units & s.test_units)


@pytest.mark.parametrize("name", ["S3", "S3B"])
def test_s3_buffer_excluded(uf, ex, name):
    for s in S.iter_folds(name):
        cu = uf[uf.country == s.country]
        blocks = set(cu.s3_block[cu.unit_id.isin(s.test_units)].astype(int))
        e = set(ex.excluded_unit_id[(ex.country == s.country) & ex.test_block.isin(blocks)])
        assert not (s.train_units & e)
        assert s.train_units | s.test_units | e == set(cu.unit_id)


@pytest.mark.parametrize("name", ["S3", "S3B"])
def test_s3_buffer_complete(uf, name):
    """Buffer = exactly the non-test units within D of some held-out unit of the fold."""
    import json
    D = json.loads((S.SPLIT_DIR / "buffer_distance.json").read_text())
    c = uf.set_index("unit_id")
    for s in S.iter_folds(name):
        if s.origin != S.FIRST_TEST_ORIGIN:
            continue
        cu = set(uf.unit_id[uf.country == s.country])
        buf = sorted(cu - s.train_units - s.test_units)
        te = c.loc[sorted(s.test_units)]
        if buf:
            b = c.loc[buf]
            assert sp.haversine_matrix(te.lon, te.lat, b.lon, b.lat).min(0).max() <= D[s.country]["D_km"]


@pytest.mark.parametrize("name", ["S3", "S3B"])
def test_s3_buffer_distance(uf, ex, name):
    """Every retained training unit is farther than D from every held-out unit of the fold."""
    import json
    D = json.loads((S.SPLIT_DIR / "buffer_distance.json").read_text())
    c = uf.set_index("unit_id")
    for s in S.iter_folds(name):
        if s.origin != S.FIRST_TEST_ORIGIN:
            continue
        te, tr = c.loc[sorted(s.test_units)], c.loc[sorted(s.train_units)]
        d = sp.haversine_matrix(te.lon, te.lat, tr.lon, tr.lat)
        assert d.min() > D[s.country]["D_km"]


@pytest.mark.parametrize("name,col", [("S2", "s2_fold"), ("S2L", "s2l_fold"), ("S4", "s4_fold"),
                                      ("S3", "s3_fold"), ("S3B", "s3_block")])
def test_each_unit_tested_once(uf, name, col):
    for c in S.SPLIT_COUNTRIES[name]:
        cu = uf[uf.country == c]
        assert cu[col].notna().all()
        tested = []
        for f in S.folds(name, c):
            tested += list(S.get_split(name, c, f, 2020).test_units)
        assert len(tested) == len(set(tested)) == len(cu)


def test_s2_grouped_states(uf):
    """S2: 5 folds; every adm1 in exactly one fold; held-out states never in training; balanced."""
    for c in S.SPLIT_COUNTRIES["S2"]:
        cu = uf[uf.country == c]
        assert S.folds("S2", c) == [0, 1, 2, 3, 4]
        assert (cu.groupby("adm1").s2_fold.nunique() == 1).all()
        sizes = cu.s2_fold.value_counts()
        assert sizes.max() - sizes.min() <= cu.adm1.value_counts().max()
        assert sizes.max() / sizes.min() < 1.1  # greedy balance is tight for BR and CO
        for f in S.folds("S2", c):
            s = S.get_split("S2", c, f, 2022)
            te_states = set(cu.adm1[cu.unit_id.isin(s.test_units)])
            tr_states = set(cu.adm1[cu.unit_id.isin(s.train_units)])
            assert not (te_states & tr_states)
            assert s.test_units | s.train_units == set(cu.unit_id)


def test_s2_grouping_deterministic(uf):
    cu = uf[uf.country == "BRAZIL"]
    a, b = S.group_adm1_folds(cu), S.group_adm1_folds(cu)
    assert (a == b).all() and (a.to_numpy() == cu.s2_fold.to_numpy()).all()
    assert S.group_adm1_folds(cu, seed=1).notna().all()
    toy = pd.DataFrame({"adm1": list("AABBC")})
    assert set(S.group_adm1_folds(toy, k=5)) == {0, 1, 2}  # k capped at the number of adm1s


def test_s3_grouped_blocks(uf):
    """S3: BR 10 blocks -> 5 folds of exactly 2 blocks; CO keeps 6 single-block folds."""
    br = uf[uf.country == "BRAZIL"]
    assert br.s3_block.nunique() == 10 and S.folds("S3", "BRAZIL") == [0, 1, 2, 3, 4]
    assert (br.groupby("s3_fold").s3_block.nunique() == 2).all()
    assert (br.groupby("s3_block").s3_fold.nunique() == 1).all()
    co = uf[uf.country == "COLOMBIA"]
    assert S.folds("S3", "COLOMBIA") == list(range(6))
    assert (co.s3_fold.astype(int) == co.s3_block.astype(int)).all()
    assert S.folds("S3B", "BRAZIL") == list(range(10))
    g = S.group_blocks(pd.Series([0] * 5 + [1] * 1 + [2] * 3 + [3] * 2), 2)
    assert g == {0: 0, 1: 0, 2: 1, 3: 1}  # largest with smallest


def test_s4_stratified(uf):
    for c in S.SPLIT_COUNTRIES["S4"]:
        cu = uf[uf.country == c]
        sizes = cu.s4_fold.value_counts()
        assert sizes.max() - sizes.min() <= 1
        per = cu.groupby("adm1").s4_fold.agg(lambda f: (lambda v: v.max() - v.min())(f.value_counts().reindex(range(5), fill_value=0)))
        assert (per <= 1).all()


def test_s5_country_partition(uf):
    assert S.folds("S5", None)[0] == "TAIWAN"
    for s in S.iter_folds("S5"):
        assert set(uf.country[uf.unit_id.isin(s.test_units)]) == {s.country}
        assert s.country not in set(uf.country[uf.unit_id.isin(s.train_units)])


def test_peru_only_s1_s5():
    for n in ("S0", "S2", "S3", "S4"):
        assert "PERU" not in S.SPLIT_COUNTRIES[n]
        with pytest.raises(ValueError):
            S.get_split(n, "PERU", 0, 2020)


def test_origins():
    assert S.origins("COLOMBIA") == [2020, 2021, 2022]
    assert S.origins("BRAZIL", include_tuning=True)[0] == 2019
    s = S.get_split("S1", "BRAZIL", None, 2019)
    assert s.train_years == (2018,) and s.test_years == (2019,)


def _toy_panel(uf):
    units = uf.unit_id[uf.country == "TAIWAN"].to_numpy()[:20]
    weeks = pd.date_range("2017-01-01", "2021-12-31", freq="7D")
    p = pd.MultiIndex.from_product([units, weeks], names=["unit_id", "week_start"]).to_frame(index=False)
    p["year"] = p.week_start.dt.year
    p["flag_gap"] = np.random.default_rng(0).random(len(p)) < 0.05
    return p


def test_row_masks_s0_deterministic_and_disjoint(uf):
    p = _toy_panel(uf)
    s = S.get_split("S0", "TAIWAN", None, 2020)
    m1, m2 = S.row_masks(p, s), S.row_masks(p.sample(frac=1, random_state=1).sort_index(), s)
    for k in m1:
        assert (m1[k] == m2[k]).all()
    assert not (m1["train"] & m1["test"]).any()
    assert set(p.year[m1["test"]]) == {2020} and set(p.year[m1["train"]]) <= {2018, 2019, 2020}
    frac = m1["test"].sum() / (p.year == 2020).sum()
    assert 0.1 < frac < 0.3
    other = S.row_masks(p, S.get_split("S0", "TAIWAN", None, 2020, seed=7))
    assert (other["test"] != m1["test"]).any()


def test_score_mask_excludes_gaps(uf):
    p = _toy_panel(uf)
    m = S.row_masks(p, S.get_split("S1", "TAIWAN", None, 2021))
    assert not (m["score"] & p.flag_gap.to_numpy()).any()
    assert (m["score"] | (m["test"] & p.flag_gap.to_numpy()) == m["test"]).all()
    assert set(p.year[m["train"]]) == {2018, 2019, 2020}


def test_build_determinism(uf):
    from importlib import util
    spec = util.spec_from_file_location("bs", S.ROOT / "scripts/splits/build_splits.py")
    bs = util.module_from_spec(spec)
    spec.loader.exec_module(bs)
    cu = uf[uf.country == "COLOMBIA"].reset_index(drop=True)
    a, b = bs.s4_folds(cu, 5, S.DEFAULT_SEED), bs.s4_folds(cu, 5, S.DEFAULT_SEED)
    assert (a == b).all() and (a == cu.s4_fold.to_numpy()).all()
    assert (bs.s4_folds(cu, 5, 1) != a).any()
    blk = sp.kmeans_blocks(cu, bs.N_BLOCKS["COLOMBIA"], seed=S.DEFAULT_SEED)
    assert (blk == cu.s3_block.to_numpy()).all()
