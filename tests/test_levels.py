"""Feature levels L2-L4 and L3+C: availability (poisoned future inputs), y-1 rule, renormalisation,
controls replacing the embedding block."""
import numpy as np
import pandas as pd
import pytest

from pop.features import history as H
from pop.features import levels as LV
from pop.splits import splits as SP
from test_history import synth_panel

N_UNITS = 6


def panel():
    p = synth_panel(n_units=N_UNITS, n_weeks=574)
    p["country"] = "BRAZIL"
    p["adm1"] = np.where(p["unit_id"].isin(["U0", "U1", "U2"]), "A", "B")
    return p


def tables(seed=0):
    rng = np.random.default_rng(seed)
    units = [f"U{i}" for i in range(N_UNITS)]
    weeks = pd.date_range("2013-12-29", periods=574, freq="7D")
    cl = pd.DataFrame({"unit_id": np.repeat(units, len(weeks)), "week_start": np.tile(weeks, N_UNITS)})
    for v in LV.CLIMATE_VARS:
        cl[v] = rng.normal(size=len(cl)).astype("float32")
    ym = [(y, m) for y in range(2013, 2025) for m in range(1, 13)]
    mo = pd.DataFrame([(u, y, m) for u in units for y, m in ym], columns=["unit_id", "year", "month"])
    for v in LV.MONTHLY_VARS:
        mo[v] = rng.normal(size=len(mo))
    yrs = range(2013, 2025)
    yr = pd.DataFrame([(u, y) for u in units for y in yrs], columns=["unit_id", "year"])
    yr["ntl_pw"], yr["built_share"] = rng.random(len(yr)), rng.random(len(yr))
    pop = yr[["unit_id", "year"]].assign(pop=rng.integers(1000, 10**6, len(yr)).astype(float))
    W = rng.normal(size=(len(yr), 64)) * 3
    ae = pd.concat([yr[["unit_id", "year"]].reset_index(drop=True),
                    pd.DataFrame(W, columns=[f"w_A{i:02d}" for i in range(64)]),
                    pd.DataFrame(W + 1, columns=[f"u_A{i:02d}" for i in range(64)])], axis=1)
    pts = pd.DataFrame({"unit_id": units, "country": "BRAZIL", "adm1": ["A"] * 3 + ["B"] * 3,
                        "lat": -10 - np.arange(N_UNITS), "lon": -50 + np.arange(N_UNITS) * 0.7})
    return {"climate": cl, "rs_monthly": mo, "rs_yearly": yr, "population": pop,
            "alphaearth": ae, "units": pts}


def ctx(tabs=None, **options):
    return LV.Context(country="BRAZIL", tables=tabs or tables(), options=options)


@pytest.fixture(scope="module")
def grid():
    return H.make_grid(panel())


def rows(grid, h, weeks=range(300, 560, 13)):
    return H.design_index(grid, np.array(list(weeks)), h)


def test_feature_counts(grid):
    idx = rows(grid, 1)
    c = ctx()
    n = {lv: LV.LEVELS[lv](grid, idx, 1, c).shape[1] for lv in ("L0", "L1", "L2", "L3", "L4")}
    assert n == {"L0": 1, "L1": 23, "L2": 74, "L3": 86, "L4": 150}
    H.assert_no_location(LV.LEVELS["L2"](grid, idx, 1, c).columns)


@pytest.mark.parametrize("h", [1, 4])
@pytest.mark.parametrize("level", ["L2", "L3", "L4"])
def test_poisoned_future_inputs_do_not_change_features(grid, level, h):
    idx = rows(grid, h)
    base = LV.LEVELS[level](grid, idx, h, ctx())
    for o in np.unique(idx["o"])[::4]:
        sel = (idx["o"] == o).to_numpy()
        ow = grid.weeks[o]
        tyear = int(grid.year[o + h])
        tb = tables()
        cl = tb["climate"]
        cl.loc[cl.week_start > ow, list(LV.CLIMATE_VARS)] = 1e9
        mo = tb["rs_monthly"]
        mo.loc[mo.year * 12 + mo.month - 1 >= ow.year * 12 + ow.month - 1, list(LV.MONTHLY_VARS)] = 1e9
        for k, cols in (("rs_yearly", ["ntl_pw", "built_share"]), ("population", ["pop"]),
                        ("alphaearth", [c for c in tb["alphaearth"] if c[:2] in ("w_", "u_")])):
            tb[k].loc[tb[k].year >= tyear, cols] = 1e9
        X = LV.LEVELS[level](grid, idx[sel], h, ctx(tb))
        pd.testing.assert_frame_equal(X, base[sel])


def test_monthly_reads_three_complete_months(grid):
    idx = rows(grid, 2)
    X = LV.rs_block(grid, idx, ctx())
    mo = tables()["rs_monthly"].set_index(["unit_id", "year", "month"])
    for i in [0, 7, 15]:
        r = idx.iloc[i]
        d = grid.weeks[r.o]
        for b in (1, 2, 3):
            p = pd.Period(d, "M") - b
            assert p.end_time < d  # complete before the origin week starts
            exp = mo.loc[(grid.units[r.u], p.year, p.month), "ndvi_pw"]
            assert X["ndvi_pw_m%d" % b].iloc[i] == pytest.approx(exp, rel=1e-6)


def test_embedding_is_year_minus_one_and_renormalised(grid):
    idx = rows(grid, 3, weeks=range(200, 570, 5))
    tb = tables()
    X = LV.alphaearth_block(grid, idx, ctx(tb))
    V = X.to_numpy(float)
    assert np.allclose(np.linalg.norm(V, axis=1), 1, atol=1e-6)
    ae = tb["alphaearth"].set_index(["unit_id", "year"])
    wcols = [f"w_A{i:02d}" for i in range(64)]
    for i in range(0, len(idx), 11):
        r = idx.iloc[i]
        y = int(grid.year[r.t]) - 1
        w = ae.loc[(grid.units[r.u], y), wcols].to_numpy(float)
        assert np.allclose(V[i], w / np.linalg.norm(w), atol=1e-6)
        assert not np.allclose(V[i], ae.loc[(grid.units[r.u], y + 1), wcols].to_numpy(float)
                               / np.linalg.norm(ae.loc[(grid.units[r.u], y + 1), wcols]), atol=1e-3)
    raw = LV.alphaearth_block(grid, idx, ctx(tb, alphaearth={"normalize": False}))
    r = idx.iloc[0]
    assert np.allclose(raw.iloc[0], ae.loc[(grid.units[r.u], int(grid.year[r.t]) - 1), wcols]
                       .to_numpy(float), rtol=1e-5)
    unw = LV.alphaearth_block(grid, idx, ctx(tb, alphaearth={"weights": "u", "normalize": False}))
    assert np.allclose(unw.iloc[0], raw.iloc[0] + 1, rtol=1e-5)


def test_yearly_origin_rule_is_stricter(grid):
    # a target in early January whose origin is in the previous epi-year
    t = next(t for t in range(300, 574) if grid.year[t] != grid.year[t - 4])
    idx = H.design_index(grid, np.array([t]), 4)
    a = LV.alphaearth_block(grid, idx, ctx())
    b = LV.alphaearth_block(grid, idx, ctx(yearly_ref="origin"))
    assert not np.allclose(a, b)


@pytest.fixture()
def split_dir(tmp_path):
    pts = tables()["units"]
    uf = pts.assign(centroid_source="polygon", s2_fold=[0, 0, 0, 1, 1, 1],
                    s3_block=[0, 0, 1, 1, 2, 2], s4_fold=[0, 1, 2, 3, 4, 0])
    for c in ("s2_fold", "s3_block", "s4_fold"):
        uf[c] = uf[c].astype("Int16")
    uf.to_parquet(tmp_path / "unit_folds.parquet")
    pd.DataFrame({"country": pd.Series([], dtype=str), "test_block": pd.Series([], dtype="Int16"),
                  "excluded_unit_id": pd.Series([], dtype=str)}).to_parquet(
        tmp_path / "s3_buffer_exclusions.parquet")
    return str(tmp_path)


@pytest.mark.parametrize("control", ["C1", "C2", "C3", "C4", "C5"])
def test_control_replaces_embedding_block(grid, split_dir, control):
    idx = rows(grid, 1)
    c = ctx(control_kw={"C4": {"range_km": 300.0}})
    c.panel = panel()
    c.split = SP.get_split("S4", "BRAZIL", 0, 2022, split_dir=split_dir)
    l3 = LV.LEVELS["L3"](grid, idx, 1, c)
    l4 = LV.LEVELS["L4"](grid, idx, 1, c)
    X = LV.LEVELS[f"L3+{control}"](grid, idx, 1, c)
    extra = [k for k in X.columns if k not in l3.columns]
    assert list(X.columns[: l3.shape[1]]) == list(l3.columns)
    assert extra and all(k.startswith(control.lower() + "_") for k in extra)
    assert not any(k.startswith("ae_") for k in X.columns)
    assert [k for k in l4.columns if k not in l3.columns] == [f"ae_{i:02d}" for i in range(64)]
    assert X[extra].notna().all().all()


@pytest.mark.parametrize("seed", [0, 3])
@pytest.mark.parametrize("control", ["C1", "C2", "C3", "C4", "C5"])
def test_l4_control_is_l4_plus_same_control_block(grid, split_dir, control, seed):
    idx = rows(grid, 1)
    sp = SP.get_split("S4", "BRAZIL", 0, 2022, split_dir=split_dir)

    def mk():  # fresh context per level: no shared control cache between L3+Ck and L4+Ck
        c = ctx(control_kw={"C4": {"range_km": 300.0}})
        c.panel, c.split, c.seed = panel(), sp, seed
        return c
    l4 = LV.LEVELS["L4"](grid, idx, 1, mk())
    l3c = LV.LEVELS[f"L3+{control}"](grid, idx, 1, mk())
    X = LV.LEVELS[f"L4+{control}"](grid, idx, 1, mk())
    ctrl = [k for k in l3c.columns if k.startswith(control.lower() + "_")]
    assert ctrl
    assert list(X.columns) == list(l4.columns) + ctrl
    pd.testing.assert_frame_equal(X[list(l4.columns)], l4)
    pd.testing.assert_frame_equal(X[ctrl], l3c[ctrl])


def test_c1_uses_training_rows_only(grid, split_dir):
    idx = rows(grid, 1)
    sp = SP.get_split("S4", "BRAZIL", 0, 2022, split_dir=split_dir)
    c = ctx()
    c.panel, c.split = panel(), sp
    a = LV.control_block("C1", grid, idx, c)
    p = panel()
    bad = p.unit_id.isin(sp.test_units) | (p.year >= 2022)
    p.loc[bad, "cases"] = 1e12
    c2 = ctx()
    c2.panel, c2.split = p, sp
    pd.testing.assert_frame_equal(a, LV.control_block("C1", grid, idx, c2))


def test_c3_uses_embedding_year_minus_one(grid, split_dir):
    idx = rows(grid, 1, weeks=range(300, 560, 40))
    c = ctx(alphaearth={"normalize": False})
    c.split = SP.get_split("S1", "BRAZIL", None, 2022, split_dir=split_dir)
    X = LV.control_block("C3", grid, idx, c).to_numpy(float)
    ae = tables()["alphaearth"]
    for i in range(len(idx)):
        y = int(grid.year[idx.t.iloc[i]]) - 1
        cand = ae[ae.year == y][[f"w_A{j:02d}" for j in range(64)]].to_numpy(float)
        assert np.isclose(cand, X[i], rtol=1e-5).all(axis=1).any()  # some unit's y-1 vector


def test_missing_input_raises(grid):
    tb = tables()
    del tb["rs_monthly"]
    c = LV.Context(country="BRAZIL", tables=tb, root="/nonexistent")
    with pytest.raises(LV.MissingInput):
        LV.LEVELS["L3"](grid, rows(grid, 1), 1, c)


def test_remote_sensing_version_option(tmp_path):
    d = tmp_path / "data/interim/remote_sensing"
    d.mkdir(parents=True)
    base = pd.DataFrame({"unit_id": ["U0"], "year": [2020], "month": [1], "ndvi_pw": [0.5],
                         "lst_day_pw": [30.0], "lst_night_pw": [20.0]})
    base.to_parquet(d / "rs_monthly_brazil_v1.parquet")
    base.assign(lst_night_pw=21.0).to_parquet(d / "rs_monthly_brazil_v2.parquet")
    load = lambda **o: LV.Context(country="BRAZIL", root=tmp_path, options=o).table("rs_monthly")
    assert load().lst_night_pw.iloc[0] == 20.0  # default stays v1
    assert load(remote_sensing={"version": "v1"}).lst_night_pw.iloc[0] == 20.0
    assert load(remote_sensing={"version": "v2"}).lst_night_pw.iloc[0] == 21.0
    with pytest.raises(ValueError):
        load(remote_sensing={"version": "v3"})
    (d / "rs_monthly_brazil_v2.parquet").unlink()
    with pytest.raises(LV.MissingInput):
        load(remote_sensing={"version": "v2"})


# ------------------------------------------------------------------ LST outlier screen (lst_screen)
def test_lst_screen_flags_cold_outliers_against_pre_2018_median():
    p0 = 2013 * 12  # Jan 2013
    A = np.full((2, 12 * 8), 25.0)  # 2013..2020
    A[0, (2019 - 2013) * 12 + 3] = 14.0   # 11 below the April median -> flagged
    A[0, (2019 - 2013) * 12 + 4] = 16.0   # 9 below -> kept
    A[1, :] = np.nan                       # no reference data -> never flagged
    A[1, -1] = -40.0
    f = LV.lst_screen_flags(A, p0)
    assert f.sum() == 1 and f[0, (2019 - 2013) * 12 + 3]


def test_lst_screen_median_uses_years_up_to_2017_only():
    p0 = 2013 * 12
    A = np.full((1, 12 * 8), 25.0)
    A[0, (2018 - 2013) * 12:] = 0.0        # 2018+ shift must not move the reference median
    f = LV.lst_screen_flags(A, p0)
    assert f[0, (2018 - 2013) * 12:].all() and not f[0, :(2018 - 2013) * 12].any()
    # and appending later data (a later origin) leaves earlier flags unchanged
    B = np.concatenate([A, np.full((1, 24), -50.0)], axis=1)
    assert (LV.lst_screen_flags(B, p0)[:, :A.shape[1]] == f).all()


def test_lst_screen_option_default_off_and_only_lst(grid):
    tb = tables()
    mo = tb["rs_monthly"]
    sel = (mo.unit_id == "U2") & (mo.year == 2019) & (mo.month == 5)
    mo.loc[sel, ["lst_day_pw", "lst_night_pw", "ndvi_pw"]] = -40.0
    idx = rows(grid, 1, weeks=range(260, 300))  # origins ~Jan-Sep 2019
    off = LV.rs_block(grid, idx, ctx(tb))
    on = LV.rs_block(grid, idx, ctx(tb, remote_sensing={"lst_screen": True}))
    assert np.allclose(off.to_numpy(), LV.rs_block(grid, idx, ctx(tb, remote_sensing={})).to_numpy(),
                       equal_nan=True)
    o_m = LV.month_index(pd.DatetimeIndex(grid.weeks[idx["o"].to_numpy()]))
    u2 = grid.units[idx["u"].to_numpy()] == "U2"
    for b in LV.MONTHS_BACK:
        hit = u2 & (o_m - b == 2019 * 12 + 4)
        assert hit.any()
        for v in ("lst_day_pw", "lst_night_pw"):
            c = f"{v}_m{b}"
            assert np.isnan(on.loc[hit, c]).all() and (off.loc[hit, c] == -40.0).all()
        c = f"ndvi_pw_m{b}"
        assert (on.loc[hit, c] == -40.0).all()
    diff = ~np.isclose(on.to_numpy(), off.to_numpy(), equal_nan=True)
    assert diff.any()
    changed_cols = set(on.columns[diff.any(axis=0)])
    assert changed_cols <= {f"{v}_m{b}" for v in ("lst_day_pw", "lst_night_pw") for b in LV.MONTHS_BACK}
