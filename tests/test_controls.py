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


# ---------------------------------------------------------------------------------- C2
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
    # permutation differs across years
    s = a.pivot(index="unit_id", columns="year", values="c3_src_unit")
    assert not (s[2018] == s[2019]).all()


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


# ---------------------------------------------------------------------------------- C4
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
