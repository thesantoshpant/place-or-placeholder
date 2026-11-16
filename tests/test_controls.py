import numpy as np
import pandas as pd
import pytest

from pop.features import controls as C


def synth_units(n=60, countries=("X", "Y"), seed=0):
    rng = np.random.default_rng(seed)
    rows = []
    for k, c in enumerate(countries):
        for i in range(n):
            rows.append({"unit_id": f"{c}{i:03d}", "country": c,
                         "lat": rng.uniform(-5, 5) + 20 * k, "lon": rng.uniform(-5, 5)})
    return pd.DataFrame(rows)


def synth_rows(units, years=range(2018, 2022), seed=1):
    rng = np.random.default_rng(seed)
    r = [{"unit_id": u, "year": y, "cases": float(rng.poisson(5 + i % 7))}
         for i, u in enumerate(units.unit_id) for y in years for _ in range(4)]
    return pd.DataFrame(r)


def synth_emb(units, years=range(2017, 2025), seed=2):
    rng = np.random.default_rng(seed)
    e = pd.DataFrame([(u, y) for u in units.unit_id for y in years], columns=["unit_id", "year"])
    return pd.concat([e, pd.DataFrame(rng.normal(size=(len(e), 64)), columns=C.BANDS)], axis=1)


# ---------------------------------------------------------------------------------- C1
@pytest.mark.parametrize("seen", [True, False])
def test_c1_poisoned_values_unused(seen):
    u = synth_units()
    rows = synth_rows(u)
    allu = set(u.unit_id[u.country == "X"])
    test = set(sorted(allu)[:15])
    train = allu if seen else allu - test
    origin = 2021
    clean = rows[rows.unit_id.isin(train) & (rows.year < origin)]
    poisoned = rows.copy()
    bad = (poisoned.year >= origin) | (~poisoned.unit_id.isin(train))
    poisoned.loc[bad, "cases"] = 1e12
    a = C.make_controls("C1", u, train, test, origin, train_rows=clean)
    b = C.make_controls("C1", u, train, test, origin, train_rows=poisoned)
    pd.testing.assert_frame_equal(a, b)
    assert np.isfinite(a.c1_te).all() and a.c1_te.max() < 10
    assert set(a.unit_id) == allu


def test_c1_knn_excludes_heldout_and_matches_manual():
    u = synth_units()
    rows = synth_rows(u)
    allu = set(u.unit_id[u.country == "X"])
    test = set(sorted(allu)[::3])
    train = allu - test
    own = C.unit_level(rows, train, 2021)
    q, ref = u[u.unit_id.isin(test)], u[u.unit_id.isin(train)]
    enc, nb = C.knn_encode(q, ref, own, k=5, return_neighbours=True)
    for t, ids in nb.items():
        assert len(ids) == 5 and not set(ids) & test
        r = ref.set_index("unit_id").loc[ids]
        tt = u.set_index("unit_id").loc[t]
        d = C.great_circle_km(tt.lat, tt.lon, r.lat.to_numpy(), r.lon.to_numpy())
        rest = ref[~ref.unit_id.isin(ids)]
        assert d.max() <= C.great_circle_km(tt.lat, tt.lon, rest.lat.to_numpy(), rest.lon.to_numpy()).min()
        w = 1 / (d + 1.0)
        assert np.isclose(enc[t], (w * own.loc[ids].to_numpy()).sum() / w.sum())
    out = C.make_controls("C1", u, train, test, 2021, train_rows=rows).set_index("unit_id").c1_te
    assert np.allclose(out.loc[sorted(test)], enc.loc[sorted(test)])


def test_c1_dropped_for_unseen_country():
    u = synth_units()
    with pytest.raises(C.ControlNotApplicable):
        C.make_controls("C1", u, set(u.unit_id[u.country == "X"]), set(u.unit_id[u.country == "Y"]),
                        2021, train_rows=synth_rows(u))


def test_c1_population_incidence():
    u = synth_units(5, ("X",))
    rows = synth_rows(u)
    pop = pd.DataFrame({"unit_id": u.unit_id, "population": 1e5})
    lv = C.unit_level(rows, set(u.unit_id), 2021, population=pop)
    assert np.allclose(lv, C.unit_level(rows, set(u.unit_id), 2021))


def _panel_and_split(name="S1", origin=2021, seed=3):
    from pop.splits.splits import Split
    u = synth_units()
    rng = np.random.default_rng(seed)
    xs = sorted(u.unit_id[u.country == "X"])
    rows = [{"unit_id": x, "year": y, "cases": float(rng.poisson(3 + i % 5)), "flag_gap": False}
            for i, x in enumerate(xs) for y in range(2014, origin + 1) for _ in range(4)]
    panel = pd.DataFrame(rows)
    allu = frozenset(xs)
    test = frozenset(xs[:15]) if name != "S1" else allu
    train = allu if name == "S1" else allu - test
    sp = Split(name, "X", None if name == "S1" else 0, origin, train, test,
               tuple(range(2018, origin)), (origin,))
    return u, panel, sp


@pytest.mark.parametrize("origin", [2019, 2021])
def test_c1_s1_ignores_training_target_years(origin):
    u, panel, sp = _panel_and_split("S1", origin)
    a = C.make_controls_for_split("C1", sp, u, panel=panel)
    poisoned = panel.copy()
    poisoned.loc[poisoned.year >= min(sp.train_years), "cases"] = 1e12
    b = C.make_controls_for_split("C1", sp, u, panel=poisoned)
    pd.testing.assert_frame_equal(a, b)
    # equals the own mean of log1p(cases) over 2014-2017, gap weeks excluded
    pre = panel[panel.year < 2018]
    exp = np.log1p(pre.cases).groupby(pre.unit_id).mean()
    got = a.set_index("unit_id").c1_te
    assert np.allclose(got.loc[exp.index], exp)
    gapped = panel.copy()
    gapped["flag_gap"] = gapped.year < 2018
    gapped.loc[gapped.flag_gap, "cases"] = 1e12
    first = gapped.groupby("unit_id").head(1).index
    gapped.loc[first, ["flag_gap", "cases"]] = [False, 0.0]
    g = C.make_controls_for_split("C1", sp, u, panel=gapped).set_index("unit_id").c1_te
    assert np.allclose(g.dropna(), 0.0) and g.notna().all()


def test_c1_s1_identical_across_origins_and_train_test():
    u, p21, s21 = _panel_and_split("S1", 2021)
    _, _, s19 = _panel_and_split("S1", 2019)
    p19 = p21[p21.year <= 2019]
    a = C.make_controls_for_split("C1", s19, u, panel=p19)
    b = C.make_controls_for_split("C1", s21, u, panel=p21)
    pd.testing.assert_frame_equal(a, b)
    # one value per unit; training and test rows of a unit read the same row of this table
    assert a.unit_id.is_unique and set(a.unit_id) == set(s19.train_units) == set(s19.test_units)


def test_c1_s1_legacy_train_period_available():
    u, panel, sp = _panel_and_split("S1", 2021)
    leg = C.make_controls_for_split("C1", sp, u, panel=panel, c1_period="train").set_index("unit_id").c1_te
    r = panel[panel.year.between(2018, 2020)]
    exp = np.log1p(r.cases).groupby(r.unit_id).mean()
    assert np.allclose(leg.loc[exp.index], exp)
    with pytest.raises(ValueError):
        C.make_controls_for_split("C1", sp, u, panel=panel, c1_period="bogus")


def test_c1_unseen_splits_legacy_available():
    """c1_period='train' + train_mode='loo_knn' reproduces the pre-2026-11-16 output in S2-S4;
    with pre-training rows, the default 'matched' mode equals plain leave-one-out in S4."""
    from pop.splits.splits import row_masks
    for name in ("S2", "S3", "S4"):
        u, panel, sp = _panel_and_split(name, 2021)
        leg = C.make_controls_for_split("C1", sp, u, panel=panel, c1_period="train", train_mode="loo_knn")
        tr = panel[row_masks(panel, sp)["train_target_ok"]]
        old = C.make_controls("C1", u, sp.train_units, sp.test_units, sp.origin, train_rows=tr,
                              train_mode="auto")
        pd.testing.assert_frame_equal(leg, old)
        if name == "S4":
            pd.testing.assert_frame_equal(
                C.make_controls_for_split("C1", sp, u, panel=panel, train_mode="loo_knn"),
                C.make_controls_for_split("C1", sp, u, panel=panel))


@pytest.mark.parametrize("name", ["S1", "S2", "S3", "S4"])
@pytest.mark.parametrize("origin", [2019, 2021])
def test_c1_no_2018plus_target_enters_any_split(name, origin):
    """Fix 2026-11-16: C1 reads only pre-training years (< first training target year 2018) in
    every split, including the matched kNN encodings of S2-S4."""
    u = _states(synth_units(n=150))
    rng = np.random.default_rng(7)
    xs = sorted(u.unit_id[u.country == "X"])
    panel = pd.DataFrame([{"unit_id": x, "year": y, "cases": float(rng.poisson(1 + i % 9)),
                           "flag_gap": False}
                          for i, x in enumerate(xs) for y in range(2014, origin + 1) for _ in range(3)])
    if name == "S1":
        from pop.splits.splits import Split
        sp = Split("S1", "X", None, origin, frozenset(xs), frozenset(xs), tuple(range(2018, origin)),
                   (origin,))
    else:
        sp = _matched_split(name, u, origin=origin)
    a = C.make_controls_for_split("C1", sp, u, panel=panel, c1_buffer_km=150.0).set_index("unit_id").c1_te
    poisoned = panel.copy()
    poisoned.loc[poisoned.year >= 2018, "cases"] = 1e12
    b = C.make_controls_for_split("C1", sp, u, panel=poisoned, c1_buffer_km=150.0).set_index("unit_id").c1_te
    pd.testing.assert_series_equal(a, b)
    assert a.notna().all() and a.max() < 10
    # and the kNN pool is the neighbours' 2014-2017 means (training units only)
    pre = panel[(panel.year < 2018) & panel.unit_id.isin(sp.train_units)]
    own = np.log1p(pre.cases).groupby(pre.unit_id).mean()
    te = u[u.unit_id.isin(sp.test_units - sp.train_units)]
    if len(te):
        tr = u[u.unit_id.isin(sp.train_units)]
        assert np.allclose(a.loc[te.unit_id], C.knn_encode(te, tr, own, exclude_self=True))
    else:
        assert np.allclose(a.loc[own.index], own)


# ---------------------------------------------------- C1 matched leave-out (2026-11-16)
def _states(u, n_lon=4, n_lat=3):
    u = u.copy()
    bx = np.clip(((u.lon + 5) / 10 * n_lon).astype(int), 0, n_lon - 1)
    by = np.clip(((u.lat - u.lat.groupby(u.country).transform("min")) / 10 * n_lat).astype(int), 0, n_lat - 1)
    u["adm1"] = u.country + "_" + by.astype(str) + bx.astype(str)
    return u


def _matched_split(name, u, origin=2021, d_km=150.0):
    from pop.splits.splits import Split
    xs = u[u.country == "X"]
    if name == "S2":
        test = set(xs.unit_id[xs.adm1 == sorted(xs.adm1.unique())[0]])
        train = set(xs.unit_id) - test
    elif name == "S3":
        test = set(xs.unit_id[xs.lon < -2.5])
        tq, rest = xs[xs.unit_id.isin(test)], xs[~xs.unit_id.isin(test)]
        D = C.great_circle_km(tq.lat.to_numpy()[:, None], tq.lon.to_numpy()[:, None],
                              rest.lat.to_numpy()[None, :], rest.lon.to_numpy()[None, :])
        train = set(rest.unit_id[(D > d_km).all(0)])
    else:
        test = set(sorted(xs.unit_id)[::5])
        train = set(xs.unit_id) - test
    assert test and len(train) > 10
    return Split(name, "X", 0, origin, frozenset(train), frozenset(test),
                 tuple(range(2018, origin)), (origin,))


def _panel(u, origin=2021, seed=4):
    rng = np.random.default_rng(seed)
    xs = sorted(u.unit_id[u.country == "X"])
    return pd.DataFrame([{"unit_id": x, "year": y, "cases": float(rng.poisson(1 + i % 9)),
                          "flag_gap": False}
                         for i, x in enumerate(xs) for y in range(2016, origin + 1) for _ in range(3)])


@pytest.mark.parametrize("name", ["S2", "S3"])
def test_c1_matched_training_neighbours_follow_heldout_rule(name):
    d_km = 150.0
    u = _states(synth_units(n=150))
    panel = _panel(u)
    sp = _matched_split(name, u, d_km=d_km)
    got = C.make_controls_for_split("C1", sp, u, panel=panel, c1_buffer_km=d_km).set_index("unit_id").c1_te
    own = C.unit_level(panel, sp.train_units, min(sp.train_years))  # pre-training years (fix 2026-11-16)
    tr = u[u.unit_id.isin(sp.train_units)]
    rule = {"exclude_group": "adm1"} if name == "S2" else {"exclude_within_km": d_km}
    exp, nb = C.knn_encode(tr, tr, own, exclude_self=True, return_neighbours=True, **rule)
    assert np.allclose(got.loc[exp.index], exp, equal_nan=True)
    pts = u.set_index("unit_id")
    for t, ids in nb.items():
        assert t not in ids and len(ids) > 0
        if name == "S2":  # no training unit is encoded from a unit of its own state
            assert (pts.loc[ids, "adm1"] != pts.at[t, "adm1"]).all()
        else:  # nor from a unit within the buffer D
            d = C.great_circle_km(pts.at[t, "lat"], pts.at[t, "lon"], pts.loc[ids, "lat"].to_numpy(),
                                  pts.loc[ids, "lon"].to_numpy())
            assert (d > d_km).all()
    # held-out units: unchanged (kNN over all training units)
    te = u[u.unit_id.isin(sp.test_units)]
    assert np.allclose(got.loc[te.unit_id], C.knn_encode(te, tr, own, exclude_self=True), equal_nan=True)
    # the matched training encodings differ from the legacy plain leave-one-out ones
    leg = C.make_controls_for_split("C1", sp, u, panel=panel, train_mode="loo_knn").set_index("unit_id").c1_te
    assert not np.allclose(leg.loc[tr.unit_id], got.loc[tr.unit_id])
    # and matched training neighbours are at least as far away as plain-LOO ones, on average
    _, nb_loo = C.knn_encode(tr, tr, own, exclude_self=True, return_neighbours=True)

    def mean_d(nbs):
        return np.mean([C.great_circle_km(pts.at[t, "lat"], pts.at[t, "lon"], pts.loc[i, "lat"].to_numpy(),
                                          pts.loc[i, "lon"].to_numpy()).mean() for t, i in nbs.items()])
    assert mean_d(nb) > mean_d(nb_loo)


def test_c1_matched_rule_defaults_and_errors():
    from pop.splits.splits import Split
    s = lambda n, c="BRAZIL": Split(n, c, 0, 2021, frozenset({"a"}), frozenset({"b"}), (2018,), (2021,))  # noqa: E731
    assert C.c1_matched_rule(s("S2")) == {"exclude_group": "adm1"}
    assert C.c1_matched_rule(s("S3")) == {"exclude_within_km": 225.0}
    assert C.c1_matched_rule(s("S3", "COLOMBIA")) == {"exclude_within_km": 130.0}
    assert C.c1_matched_rule(s("S4")) == {}
    u = synth_units()  # no adm1 column
    rows = synth_rows(u)
    allu = set(u.unit_id[u.country == "X"])
    test = set(sorted(allu)[:10])
    with pytest.raises(ValueError):
        C.make_controls("C1", u, allu - test, test, 2021, train_rows=rows, exclude_group="adm1")
    with pytest.raises(ValueError):
        C.make_controls("C1", u, allu - test, test, 2021, train_rows=rows, train_mode="bogus")
    # seen units (S0/S1) ignore the matched rule: own mean
    a = C.make_controls("C1", u, allu, allu, 2021, train_rows=rows)
    b = C.make_controls("C1", u, allu, allu, 2021, train_rows=rows, train_mode="own")
    pd.testing.assert_frame_equal(a, b)


def test_c2_harmonics_orthonormal_and_finite():
    rng = np.random.default_rng(0)
    n = 200_000
    lat = np.degrees(np.arcsin(rng.uniform(-1, 1, n)))
    lon = rng.uniform(-180, 180, n)
    Y = C.real_sph_harm(lat, lon, L=8, include_constant=True).to_numpy()
    assert Y.shape[1] == 81 and np.isfinite(Y).all()
    G = 4 * np.pi * Y.T @ Y / n
    assert np.abs(G - np.eye(81)).max() < 0.08


def test_c2_columns():
    u = synth_units()
    f = C.make_controls("C2", u, set(u.unit_id), set(u.unit_id), 2021, L=4)
    assert f.shape == (len(u), 1 + 2 + 24) and np.isfinite(f.drop(columns="unit_id").to_numpy()).all()


# ---------------------------------------------------------------------------------- C3
def test_c3_permutation_within_country_year():
    u = synth_units()
    e = synth_emb(u)
    allu = set(u.unit_id)
    a = C.shuffle_embeddings(e, u, allu, allu, seed=3, return_source=True)
    b = C.shuffle_embeddings(e, u, allu, allu, seed=3, return_source=True)
    c = C.shuffle_embeddings(e, u, allu, allu, seed=4, return_source=True)
    pd.testing.assert_frame_equal(a, b)
    assert not a.c3_src_unit.equals(c.c3_src_unit)
    a = a.merge(u[["unit_id", "country"]], on="unit_id")
    for _, g in a.groupby(["country", "year"]):
        assert sorted(g.c3_src_unit) == sorted(g.unit_id)
        assert (g.c3_src_unit != g.unit_id).mean() > 0.5
    src = e.set_index(["unit_id", "year"]).loc[list(zip(a.c3_src_unit, a.year)), C.BANDS].to_numpy()
    assert np.array_equal(a[[f"c3_{x}" for x in C.BANDS]].to_numpy(), src)
    # fix 2026-11-16: one source per unit across all years
    s = a.pivot(index="unit_id", columns="year", values="c3_src_unit")
    assert s.nunique(axis=1).eq(1).all()


def test_c3_unseen_units_draw_from_training():
    u = synth_units()
    e = synth_emb(u)
    allu = set(u.unit_id[u.country == "X"])
    test = set(sorted(allu)[:10])
    train = allu - test
    a = C.shuffle_embeddings(e, u, train, test, seed=0, return_source=True)
    assert a.c3_src_unit.isin(train).all()
    for _, g in a[a.unit_id.isin(train)].groupby("year"):
        assert sorted(g.c3_src_unit) == sorted(g.unit_id)
    # S5: target country permuted within itself
    tx, ty = set(u.unit_id[u.country == "X"]), set(u.unit_id[u.country == "Y"])
    s5 = C.shuffle_embeddings(e, u, tx, ty, seed=0, return_source=True)
    t = s5[s5.unit_id.isin(ty)]
    assert t.c3_src_unit.isin(ty).all()
    for _, g in t.groupby("year"):
        assert sorted(g.c3_src_unit) == sorted(g.unit_id)


@pytest.mark.parametrize("mode", ["seen", "unseen", "s5"])
def test_c3_fixed_source_across_years_and_differs_across_seeds(mode):
    """Fix 2026-11-16: unit i takes its embedding from the same source unit pi(i) in every year;
    the values change with the source's real per-year embedding; the map differs across seeds."""
    u = synth_units()
    e = synth_emb(u)
    xs, ys = set(u.unit_id[u.country == "X"]), set(u.unit_id[u.country == "Y"])
    train, test = {"seen": (xs | ys, xs | ys), "unseen": (xs - set(sorted(xs)[:10]), set(sorted(xs)[:10])),
                   "s5": (xs, ys)}[mode]
    maps = []
    for seed in (0, 1, 2):
        a = C.shuffle_embeddings(e, u, train, test, seed=seed, return_source=True)
        s = a.pivot(index="unit_id", columns="year", values="c3_src_unit")
        assert s.notna().all().all() and s.nunique(axis=1).eq(1).all()  # same source every year
        m = s.iloc[:, 0]
        pd.testing.assert_series_equal(
            m.astype(object), C.c3_source_map(u, train, test, seed).reindex(m.index), check_names=False,
            check_index_type=False)
        assert (m != m.index).mean() > 0.5
        # values = the source's real embedding of that year, so they change across years
        ref = e.set_index(["unit_id", "year"])[C.BANDS]
        got = a.set_index(["unit_id", "year"])[[f"c3_{b}" for b in C.BANDS]]
        exp = ref.loc[list(zip(a.c3_src_unit, a.year))].to_numpy()
        assert np.array_equal(got.to_numpy(), exp)
        v = a[a.unit_id == a.unit_id.iloc[0]].c3_A00
        assert v.nunique() > 1
        maps.append(m)
    assert not maps[0].equals(maps[1]) and not maps[1].equals(maps[2])
    if mode != "seen":
        tst = maps[0][maps[0].index.isin(test)]
        assert tst.isin(train if mode == "unseen" else test).all()


def test_c3_missing_source_year_is_nan():
    u = synth_units(20, countries=("X",))
    e = synth_emb(u)
    allu = set(u.unit_id)
    m = C.c3_source_map(u, allu, allu, seed=0)
    victim = m.iloc[0]  # the source of the first unit loses its 2020 embedding
    e2 = e[~((e.unit_id == victim) & (e.year == 2020))]
    a = C.shuffle_embeddings(e2, u, allu, allu, seed=0, return_source=True)
    row = a[(a.unit_id == m.index[0]) & (a.year == 2020)]
    assert row.c3_src_unit.iloc[0] == victim and row.c3_A00.isna().all()


# ---------------------------------------------------------------------------------- C4
def test_c4s_is_c4_at_buffer_range(tmp_path):
    import json
    rng = np.random.default_rng(0)
    n = 300
    pts = pd.DataFrame({"unit_id": [f"U{i}" for i in range(n)], "country": "BRAZIL",
                        "lat": rng.uniform(-5, 5, n), "lon": rng.uniform(-5, 5, n)})
    allu = set(pts.unit_id)
    a = C.make_controls("C4s", pts, allu, set(), 2021, seed=1, range_km=225.0)
    b = C.make_controls("C4", pts, allu, set(), 2021, seed=1, range_km=225.0)
    assert list(a.columns) == ["unit_id"] + [f"c4s_f{i:02d}" for i in range(64)]
    assert np.array_equal(a.drop(columns="unit_id").to_numpy(), b.drop(columns="unit_id").to_numpy())
    far = C.make_controls("C4", pts, allu, set(), 2021, seed=1, range_km=8483.0)
    assert not np.allclose(a.drop(columns="unit_id").to_numpy(), far.drop(columns="unit_id").to_numpy())
    # default range comes from the C4s range file, per country
    f = tmp_path / "r.json"
    f.write_text(json.dumps({"BRAZIL": {"range_km": 225.0, "method": "s3_buffer_D"},
                             "TAIWAN": {"range_km": 12.5, "method": "x"}}))
    assert C.c4s_range("brazil", path=f) == 225.0 and C.c4s_range(path=f)["TAIWAN"] == 12.5
    assert "C4s" in C.CONTROLS and "C4s" in C.SEEDED_CONTROLS
    from pop.features import levels as LV
    assert {"L3+C4s", "L4+C4s", "N3+C4s", "N4+C4s"} <= set(LV.LEVELS)


def test_c4s_range_file_matches_buffer_D():
    """BR/CO C4s range = the S3 buffer D in splits_v1/buffer_distance.json (when built)."""
    import json
    if not C.C4S_RANGE_FILE.exists():
        pytest.skip("c4s range file not built")
    D = json.loads((C.C4S_RANGE_FILE.parent / "buffer_distance.json").read_text())
    r = C.c4s_range()
    for c in ("BRAZIL", "COLOMBIA"):
        assert r[c] == D[c]["D_km"]
    assert set(r) >= {"BRAZIL", "COLOMBIA", "PERU", "TAIWAN"} and all(v > 0 for v in r.values())


def test_c4_unit_variance_range_and_determinism():
    rng = np.random.default_rng(0)
    n, r = 1500, 150.0
    pts = pd.DataFrame({"unit_id": [f"U{i}" for i in range(n)], "country": "X",
                        "lat": rng.uniform(-5, 5, n), "lon": rng.uniform(-5, 5, n)})
    F = C.gaussian_random_fields(pts.lat.to_numpy(), pts.lon.to_numpy(), r, 64, np.random.default_rng(1))
    assert abs((F ** 2).mean() - 1) < 0.1
    emb = pd.DataFrame(F, columns=C.BANDS).assign(unit_id=pts.unit_id)
    r_hat = C.fit_embedding_range(emb, pts, max_dist_km=600)
    assert 0.6 * r < r_hat < 1.6 * r
    a = C.make_controls("C4", pts, set(pts.unit_id), set(), 2021, seed=2, range_km=r)
    b = C.make_controls("C4", pts, set(pts.unit_id), set(), 2021, seed=2, range_km=r)
    c = C.make_controls("C4", pts, set(pts.unit_id), set(), 2021, seed=3, range_km=r)
    pd.testing.assert_frame_equal(a, b)
    X = a.drop(columns="unit_id").to_numpy()
    assert X.shape == (n, 64) and np.allclose(X.std(0), 1) and np.allclose(X.mean(0), 0, atol=1e-9)
    assert not np.allclose(X, c.drop(columns="unit_id").to_numpy())


def test_c4_rff_variance():
    rng = np.random.default_rng(0)
    lat, lon = rng.uniform(-5, 5, 400), rng.uniform(-5, 5, 400)
    F = C.gaussian_random_fields(lat, lon, 150.0, 64, np.random.default_rng(1), method="rff")
    assert abs((F ** 2).mean() - 1) < 0.15


# ---------------------------------------------------------------------------------- C5
def test_c5_picks_2023():
    u = synth_units(10)
    e = synth_emb(u)
    e["A00"] = e.year.astype(float)
    f = C.make_controls("C5", u, set(u.unit_id), set(u.unit_id), 2021, emb_df=e)
    assert len(f) == len(u) and (f.c5_A00 == 2023).all()
    ref = e[e.year == 2023].set_index("unit_id")[C.BANDS]
    assert np.array_equal(f.set_index("unit_id").loc[ref.index].to_numpy(), ref.to_numpy())


def test_fit_embedding_range_ignores_units_without_embedding():
    rng = np.random.default_rng(3)
    n = 400
    lat, lon = rng.uniform(-20, -10, n), rng.uniform(-50, -40, n)
    pts = pd.DataFrame({"unit_id": [f"u{i}" for i in range(n)], "country": "BRAZIL",
                        "lat": lat, "lon": lon})
    F = C.gaussian_random_fields(lat, lon, 300.0, n_fields=64, rng=rng)
    emb = pd.DataFrame(F, columns=C.BANDS).assign(unit_id=pts.unit_id, year=2018)
    r0 = C.fit_embedding_range(emb, pts)
    emb.loc[5, C.BANDS] = np.nan  # e.g. an island unit with no pixels
    r1 = C.fit_embedding_range(emb, pts)
    assert np.isfinite(r1) and abs(r1 - r0) / r0 < 0.05
