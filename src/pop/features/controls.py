"""Location-only control features C1-C5 (Paper 1, "Place or Placeholder?").

Each control replaces the AlphaEarth block in L4 ("L3 + C"). Everything is computed at fit time
for one split instance (train_units, test_units, origin_year). C1 uses outcome rows of training
units only: pre-training years under S0/S1, training target rows under S2-S4 (c1_source_rows).

Column contracts (all outputs carry ``unit_id``; C3 also ``year``):
    C1  target_encoding         -> unit_id, c1_te                     (static within an origin)
    C2  coordinate_harmonics    -> unit_id, c2_lat, c2_lon, c2_sh_l{l}_m{m}   (m<0 written 'mn')
    C3  shuffle_embeddings      -> unit_id, year, c3_A00..c3_A63        (year = embedding year)
    C4  random_smooth_fields    -> unit_id, c4_f00..c4_f63            (static)
    C5  static_embedding        -> unit_id, c5_A00..c5_A63            (static; AlphaEarth 2023)
    C6  unit_id_categorical     -> unit_id, c6_unit_cat               (pure ID; LightGBM categorical,
                                   columns ending in '_cat'; seen-unit splits only, else NotApplicable)

Inputs:
    units_df  unit_id, country, and either (lat, lon) or (centroid_lat, centroid_lon) in degrees.
              Use ``load_unit_points()`` for representative points (3 units have offshore centroids).
    train_rows panel rows (unit_id, year, cases[, week_start]); filtered again here to
              unit in train_units and year < origin_year, so passing the whole panel is safe.
    emb_df    unit_id, year, A00..A63.
"""
from __future__ import annotations

import zlib
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
from scipy.special import gammaln, lpmv

R_EARTH_KM = 6371.0088
BANDS = [f"A{i:02d}" for i in range(64)]
CONTROLS = ("C1", "C2", "C3", "C4", "C5", "C6")
N_SEEDS = 10  # C3 / C4 draws
STATIC_YEAR = 2023
ROOT = Path(__file__).resolve().parents[3]
BOUNDARIES = ROOT / "data/interim/boundaries/opendengue_units_v1.parquet"


class ControlNotApplicable(ValueError):
    """Raised when a control is undefined for a split (C1 under S5; C6 with unseen test units)."""


# ------------------------------------------------------------------------------------ geometry
def load_unit_points(path=BOUNDARIES) -> pd.DataFrame:
    """unit_id, country, adm1, lat, lon from polygon representative points (always on land)."""
    import geopandas as gpd
    g = gpd.read_parquet(path)
    rp = g.geometry.representative_point()
    return pd.DataFrame({"unit_id": g.unit_id.to_numpy(), "country": g.country.to_numpy(),
                         "adm1": g.adm1.to_numpy(), "lat": rp.y.to_numpy(), "lon": rp.x.to_numpy()})


def _latlon(df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    if {"lat", "lon"} <= set(df.columns):
        return df["lat"].to_numpy(float), df["lon"].to_numpy(float)
    return df["centroid_lat"].to_numpy(float), df["centroid_lon"].to_numpy(float)


def _xyz(lat, lon) -> np.ndarray:
    la, lo = np.radians(lat), np.radians(lon)
    return np.column_stack([np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo), np.sin(la)])


def great_circle_km(lat1, lon1, lat2, lon2) -> np.ndarray:
    la1, lo1, la2, lo2 = map(np.radians, (lat1, lon1, lat2, lon2))
    a = np.sin((la2 - la1) / 2) ** 2 + np.cos(la1) * np.cos(la2) * np.sin((lo2 - lo1) / 2) ** 2
    return 2 * R_EARTH_KM * np.arcsin(np.sqrt(np.clip(a, 0, 1)))


def _gc_matrix(xyz_a, xyz_b) -> np.ndarray:
    return R_EARTH_KM * np.arccos(np.clip(xyz_a @ xyz_b.T, -1.0, 1.0))


def _rng(seed: int, *keys) -> np.random.Generator:
    return np.random.default_rng([int(seed)] + [zlib.crc32(str(k).encode()) for k in keys])


def _subset(units_df, units) -> pd.DataFrame:
    u = units_df[units_df.unit_id.isin(set(units))]
    return u.drop_duplicates("unit_id").reset_index(drop=True)


# ------------------------------------------------------------------------- C1 target encoding
def unit_level(train_rows, train_units, origin_year, population=None) -> pd.Series:
    """Mean log1p(cases) (or log1p incidence/100k if `population` given) per training unit,
    from rows with unit in train_units and year < origin_year only."""
    r = train_rows[train_rows.unit_id.isin(set(train_units)) & (train_rows.year < origin_year)]
    r = r[["unit_id", "year", "cases"]].dropna(subset=["cases"])
    if population is not None:
        keys = ["unit_id", "year"] if "year" in population.columns else ["unit_id"]
        r = r.merge(population[keys + ["population"]], on=keys, how="inner")
        v = np.log1p(r.cases / r.population * 1e5)
    else:
        v = np.log1p(r.cases.clip(lower=0))
    return v.groupby(r.unit_id).mean()


def knn_encode(query: pd.DataFrame, ref: pd.DataFrame, ref_values: pd.Series, k=5, eps_km=1.0,
               exclude_self=False, return_neighbours=False, exclude_group=None,
               exclude_within_km=None):
    """Inverse-distance (1/(d+eps)) weighted mean of the k nearest `ref` units in the same country.
    `ref` must contain only training units; `exclude_self` drops a query unit from its own pool.
    Matched leave-out (C1 train_mode='matched'): `exclude_group` (a column, e.g. 'adm1') drops
    ref units sharing the query unit's value; `exclude_within_km` drops ref units with
    great-circle distance <= that many km (this also drops the unit itself). A query unit with
    fewer than k admissible neighbours uses those it has (NaN if none)."""
    out, nbrs = pd.Series(np.nan, index=query.unit_id.to_numpy(), dtype=float), {}
    ref = ref[ref.unit_id.isin(ref_values.index)]
    for c, q in query.groupby("country"):
        rc = ref[ref.country == c]
        if rc.empty:
            continue
        D = _gc_matrix(_xyz(*_latlon(q)), _xyz(*_latlon(rc)))
        rid = rc.unit_id.to_numpy()
        if exclude_self:
            D[q.unit_id.to_numpy()[:, None] == rid[None, :]] = np.inf
        if exclude_group is not None:
            D[q[exclude_group].to_numpy()[:, None] == rc[exclude_group].to_numpy()[None, :]] = np.inf
        if exclude_within_km is not None:
            D[D <= float(exclude_within_km)] = np.inf
        vals = ref_values.reindex(rid).to_numpy()
        kk = min(k, D.shape[1])
        if kk < 1:
            continue
        idx = np.argpartition(D, kk - 1, axis=1)[:, :kk]
        d = np.take_along_axis(D, idx, 1)
        ok = np.isfinite(d)
        w = np.where(ok, 1.0 / (np.where(ok, d, 0.0) + eps_km), 0.0)
        num = np.where(ok, w * vals[idx], 0.0).sum(1)
        den = w.sum(1)
        with np.errstate(invalid="ignore", divide="ignore"):
            out.loc[q.unit_id.to_numpy()] = np.where(den > 0, num / np.where(den > 0, den, 1.0), np.nan)
        nbrs.update({u: list(rid[i][o]) for u, i, o in zip(q.unit_id, idx, ok)})
    return (out, nbrs) if return_neighbours else out


C1_TRAIN_MODES = ("matched", "auto", "loo_knn", "own")


def target_encoding(units_df, train_units, test_units, origin_year, train_rows, population=None,
                    k=5, eps_km=1.0, train_mode="matched", exclude_group=None,
                    exclude_within_km=None) -> pd.DataFrame:
    """C1. Seen units (S0/S1): own mean of `train_rows` (via make_controls_for_split these are the
    pre-training years, see c1_source_rows). Unseen units (S2-S4): kNN of training units.
    train_mode for training units when test units are unseen:
      'matched' (default, 2026-11-16): kNN with the held-out unit's leave-out rule applied to each
        training unit, i.e. its own unit plus `exclude_group` (S2: same adm1) / everything within
        `exclude_within_km` (S3: buffer D); with neither given this is plain leave-one-out (S4).
      'loo_knn' / 'auto' (legacy): plain leave-one-out kNN.  'own': the unit's own mean.
    Test units are always encoded from the training pool, excluding themselves only.
    S5 -> ControlNotApplicable."""
    if train_mode not in C1_TRAIN_MODES:
        raise ValueError(f"C1 train_mode must be one of {C1_TRAIN_MODES}, got {train_mode!r}")
    train_units, test_units = set(train_units), set(test_units)
    allu = _subset(units_df, train_units | test_units)
    tr = allu[allu.unit_id.isin(train_units)]
    if not set(allu.country[allu.unit_id.isin(test_units)]) <= set(tr.country):
        raise ControlNotApplicable("C1 is dropped when the test country has no training units (S5)")
    own = unit_level(train_rows, train_units, origin_year, population)
    seen = test_units <= train_units
    if seen or train_mode == "own":
        mode = "own" if train_mode in ("auto", "matched", "own") else train_mode
    else:
        mode = train_mode if train_mode == "matched" else "loo_knn"
    mkw = {}
    if mode == "matched":
        if exclude_group is not None and exclude_group not in allu.columns:
            raise ValueError(f"C1 matched mode needs column {exclude_group!r} in units_df")
        mkw = {"exclude_group": exclude_group, "exclude_within_km": exclude_within_km}
    te = pd.Series(np.nan, index=allu.unit_id.to_numpy(), dtype=float)
    if mode == "own":
        te.update(own.reindex(tr.unit_id).dropna())
    else:
        te.loc[tr.unit_id.to_numpy()] = knn_encode(tr, tr, own, k, eps_km, exclude_self=True,
                                                   **mkw).to_numpy()
    unseen = allu.unit_id.isin(test_units - train_units).to_numpy()
    miss_tr = allu[te.reindex(allu.unit_id).isna().to_numpy() & ~unseen]
    if len(miss_tr) and mode == "own":  # training units with no usable rows
        te.loc[miss_tr.unit_id.to_numpy()] = knn_encode(miss_tr, tr, own, k, eps_km,
                                                        exclude_self=True).to_numpy()
    miss = allu[unseen]
    if len(miss):  # unseen test units
        te.loc[miss.unit_id.to_numpy()] = knn_encode(miss, tr, own, k, eps_km, exclude_self=True).to_numpy()
    return pd.DataFrame({"unit_id": te.index, "c1_te": te.to_numpy()})


# ------------------------------------------------------------- C2 coordinates + harmonics
def real_sph_harm(lat, lon, L=8, include_constant=False) -> pd.DataFrame:
    """Orthonormal real spherical harmonics Y_lm, l<=L (integral of Y^2 over the sphere = 1)."""
    th, ph = np.radians(90.0 - np.asarray(lat, float)), np.radians(np.asarray(lon, float))
    x, cols = np.cos(th), {}
    for l in range(0 if include_constant else 1, L + 1):
        for m in range(-l, l + 1):
            am = abs(m)
            logn = 0.5 * (np.log(2 * l + 1) - np.log(4 * np.pi) + gammaln(l - am + 1) - gammaln(l + am + 1))
            p = np.exp(logn) * lpmv(am, l, x)
            y = p if m == 0 else np.sqrt(2) * p * (np.cos(m * ph) if m > 0 else np.sin(am * ph))
            cols[f"c2_sh_l{l}_m{m}".replace("-", "n")] = y
    return pd.DataFrame(cols)


def coordinate_harmonics(units_df, units, L=8) -> pd.DataFrame:
    u = _subset(units_df, units)
    lat, lon = _latlon(u)
    sh = real_sph_harm(lat, lon, L)
    return pd.concat([pd.DataFrame({"unit_id": u.unit_id, "c2_lat": lat, "c2_lon": lon}), sh], axis=1)


# --------------------------------------------------------------- C3 shuffled embeddings
def _perm(n, rng) -> np.ndarray:
    p = rng.permutation(n)
    while n > 1 and np.array_equal(p, np.arange(n)):
        p = rng.permutation(n)
    return p


def shuffle_embeddings(emb_df, units_df, train_units, test_units, seed=0, return_source=False):
    """C3. Seen units or unseen country (S0/S1/S5): permute embeddings across units within each
    country-year (S5: the target country is permuted among its own units). Unseen units in a
    seen country (S2-S4): training units permuted within country-year; each held-out unit gets
    the embedding of a training unit of the same country-year drawn at random (with replacement)."""
    train_units, test_units = set(train_units), set(test_units)
    cty = _subset(units_df, train_units | test_units)[["unit_id", "country"]]
    e = emb_df.merge(cty, on="unit_id", how="inner")
    train_c = set(cty.country[cty.unit_id.isin(train_units)])
    test_c = set(cty.country[cty.unit_id.isin(test_units)])
    within = test_units <= train_units or not (test_c & train_c)
    src = pd.Series(index=e.index, dtype=object)
    for (c, y), g in e.groupby(["country", "year"], sort=True):
        rng, ids = _rng(seed, "C3", c, y), g.unit_id.to_numpy()
        if within:
            src.loc[g.index] = ids[_perm(len(ids), rng)]
            continue
        is_tr = np.isin(ids, list(train_units))
        tr_ids = ids[is_tr]
        src.loc[g.index[is_tr]] = tr_ids[_perm(len(tr_ids), rng)]
        if (~is_tr).any():
            src.loc[g.index[~is_tr]] = tr_ids[rng.integers(0, len(tr_ids), (~is_tr).sum())]
    lookup = e.set_index(["unit_id", "year"])[BANDS]
    vals = lookup.loc[list(zip(src, e.year))].to_numpy()
    out = pd.DataFrame(vals, columns=[f"c3_{b}" for b in BANDS])
    out.insert(0, "year", e.year.to_numpy())
    out.insert(0, "unit_id", e.unit_id.to_numpy())
    if return_source:
        out["c3_src_unit"] = src.to_numpy()
    return out


# ---------------------------------------------------------------- C4 random smooth fields
_CHOL: dict = {}


def _chol_factor(xyz, range_km, jitter=1e-8):
    key = (zlib.crc32(xyz.tobytes()), len(xyz), float(range_km))
    if key not in _CHOL:
        if len(_CHOL) > 8:
            _CHOL.clear()
        C = np.exp(-_gc_matrix(xyz, xyz) / range_km)
        C[np.diag_indices_from(C)] += jitter
        _CHOL[key] = np.linalg.cholesky(C)
    return _CHOL[key]


def gaussian_random_fields(lat, lon, range_km, n_fields=64, rng=None, method="auto",
                           n_features=4096) -> np.ndarray:
    """(n, n_fields) zero-mean unit-variance GRF with exponential covariance exp(-d/range_km)
    (d great-circle km). 'cholesky' is exact (default for n <= 8000); 'rff' = random Fourier
    features of the exponential kernel in R^3 (chord distance; multivariate-Cauchy frequencies)."""
    rng = rng or np.random.default_rng(0)
    xyz = _xyz(lat, lon)
    if method == "auto":
        method = "cholesky" if len(xyz) <= 8000 else "rff"
    if method == "cholesky":
        return _chol_factor(xyz, range_km) @ rng.standard_normal((len(xyz), n_fields))
    X, out = xyz * R_EARTH_KM, np.empty((len(xyz), n_fields))
    for f in range(n_fields):
        w = rng.standard_normal((3, n_features)) / (range_km * np.abs(rng.standard_normal(n_features)))
        b = rng.uniform(0, 2 * np.pi, n_features)
        out[:, f] = np.sqrt(2.0 / n_features) * np.cos(X @ w + b).sum(1)
    return out


def random_smooth_fields(units_df, units, range_km, seed=0, n_fields=64, method="auto",
                         standardize=True) -> pd.DataFrame:
    """C4. Independent fields per country; range_km is a float or {country: float}.
    Depends only on geography and seed (no target), so no refit leakage is possible."""
    u = _subset(units_df, units)
    parts = []
    for c, g in u.groupby("country", sort=True):
        r = range_km[c] if isinstance(range_km, dict) else range_km
        F = gaussian_random_fields(*_latlon(g), r, n_fields, _rng(seed, "C4", c), method)
        if standardize:
            F = (F - F.mean(0)) / np.where(F.std(0) > 0, F.std(0), 1.0)
        parts.append(pd.DataFrame(F, columns=[f"c4_f{i:02d}" for i in range(n_fields)]).assign(
            unit_id=g.unit_id.to_numpy()))
    out = pd.concat(parts, ignore_index=True)
    return out[["unit_id"] + [c for c in out.columns if c != "unit_id"]]


def empirical_variogram(values, lat, lon, max_pairs=2_000_000, seed=0):
    """Pair distances (km) and semivariances 0.5 * ||v_i - v_j||^2 / p (all or sampled pairs)."""
    n = len(values)
    rng = np.random.default_rng(seed)
    if n * (n - 1) // 2 <= max_pairs:
        i, j = np.triu_indices(n, 1)
    else:
        i, j = rng.integers(0, n, max_pairs), rng.integers(0, n, max_pairs)
        keep = i != j
        i, j = i[keep], j[keep]
    d = great_circle_km(lat[i], lon[i], lat[j], lon[j])
    g = 0.5 * ((values[i] - values[j]) ** 2).mean(1)
    return d, g


def fit_embedding_range(emb_df, points, year=None, per_country=False, n_bins=25, max_dist_km=None,
                        max_pairs=2_000_000, return_details=False):
    """Fit gamma(h) = nugget + psill * (1 - exp(-h/range)) to the within-country empirical
    variogram of the 64-d district-mean embeddings (averaged over years unless `year` given).
    Returns range_km (exponential scale, the parameter C4 takes): a float, or {country: float}
    if per_country. Default max distance = 1/2 of the largest within-country pair distance."""
    e = emb_df if year is None or "year" not in emb_df.columns else emb_df[emb_df.year == year]
    bands = [b for b in BANDS if b in e.columns]
    e = e.groupby("unit_id")[bands].mean().dropna().reset_index()  # units without pixels
    pts = points[["unit_id", "country"]].assign(lat=_latlon(points)[0], lon=_latlon(points)[1])
    e = e.merge(pts, on="unit_id", how="inner")
    D, G, C = [], [], []
    for c, g in e.groupby("country"):
        lat, lon = g.lat.to_numpy(), g.lon.to_numpy()
        d, gg = empirical_variogram(g[bands].to_numpy(float), lat, lon, max_pairs=max_pairs)
        D.append(d), G.append(gg), C.append(np.full(len(d), c, object))
    D, G, C = map(np.concatenate, (D, G, C))

    def fit(d, gg):
        hmax = max_dist_km or 0.5 * d.max()
        edges = np.linspace(0, hmax, n_bins + 1)
        b = np.digitize(d, edges) - 1
        ok = (b >= 0) & (b < n_bins)
        cnt = np.bincount(b[ok], minlength=n_bins)
        gam = np.bincount(b[ok], gg[ok], minlength=n_bins) / np.maximum(cnt, 1)
        h = np.bincount(b[ok], d[ok], minlength=n_bins) / np.maximum(cnt, 1)
        m = cnt >= 30
        f = lambda x, c0, c1, r: c0 + c1 * (1 - np.exp(-x / r))
        p0 = [gam[m][0] * 0.5, max(gam[m].max() - gam[m][0] * 0.5, 1e-9), hmax / 3]
        p, _ = curve_fit(f, h[m], gam[m], p0=p0, sigma=1 / np.sqrt(cnt[m]),
                         bounds=([0, 0, 1e-3], [np.inf, np.inf, 20 * hmax]), maxfev=20000)
        return float(p[2]), {"h": h[m], "gamma": gam[m], "n": cnt[m], "nugget": p[0], "psill": p[1]}

    if per_country:
        res = {c: fit(D[C == c], G[C == c]) for c in np.unique(C)}
        rng_ = {c: r[0] for c, r in res.items()}
        return (rng_, {c: r[1] for c, r in res.items()}) if return_details else rng_
    r, det = fit(D, G)
    return (r, det) if return_details else r


# -------------------------------------------------------------------- C5 static embedding
def static_embedding(emb_df, units=None, year=STATIC_YEAR) -> pd.DataFrame:
    """C5. AlphaEarth `year` (2023) for every unit, used for all target years."""
    e = emb_df[emb_df.year == year]
    if units is not None:
        e = e[e.unit_id.isin(set(units))]
    if e.unit_id.duplicated().any():
        raise ValueError("duplicate unit_id in static embedding year")
    out = e[["unit_id"] + BANDS].rename(columns={b: f"c5_{b}" for b in BANDS})
    return out.reset_index(drop=True)


def unit_id_categorical(units_df, train_units, test_units) -> pd.DataFrame:
    """C6. The unit identity itself as one categorical code (rank of unit_id among the sorted
    train | test units). Only defined when every test unit is a training unit (S0/S1): for
    held-out units the category was never seen in training, so ControlNotApplicable."""
    train_units, test_units = set(map(str, train_units)), set(map(str, test_units))
    if not test_units <= train_units:
        raise ControlNotApplicable("C6 (unit ID) is undefined when test units are unseen (S2-S5)")
    allu = sorted(train_units | test_units)
    known = set(units_df.unit_id.astype(str)) if units_df is not None else set(allu)
    allu = [u for u in allu if u in known]
    return pd.DataFrame({"unit_id": allu, "c6_unit_cat": np.arange(len(allu), dtype=np.int32)})


# ----------------------------------------------------------------------------------- dispatch
def make_controls(control, units_df, train_units, test_units, origin_year, train_rows=None,
                  emb_df=None, seed=0, **kw) -> pd.DataFrame:
    """Features for units in train_units | test_units. kw: C1 population/k/eps_km/train_mode/exclude_group/exclude_within_km;
    C2 L; C3 return_source; C4 range_km (required), n_fields, method; C5 year."""
    allu = set(train_units) | set(test_units)
    if control == "C1":
        if train_rows is None:
            raise ValueError("C1 needs train_rows")
        return target_encoding(units_df, train_units, test_units, origin_year, train_rows, **kw)
    if control == "C2":
        return coordinate_harmonics(units_df, allu, **kw)
    if control == "C3":
        return shuffle_embeddings(emb_df, units_df, train_units, test_units, seed=seed, **kw)
    if control == "C4":
        return random_smooth_fields(units_df, allu, seed=seed, **kw)
    if control == "C5":
        return static_embedding(emb_df, allu, **kw)
    if control == "C6":
        return unit_id_categorical(units_df, train_units, test_units)
    raise ValueError(f"unknown control {control}")


C1_PERIODS = ("auto", "pre_train", "train")


def c1_source_rows(panel, split, period="auto"):
    """Rows and cutoff year C1 is computed from, as (rows, cutoff); unit_level uses year < cutoff.

    pre_train: training units, panel years strictly before the first training target year
    (Brazil 2014-2017 for every origin), flag_gap weeks dropped like training targets. Fully
    causal, identical for training and test rows and across origins.
    train (legacy): the training target rows (row_masks train_target_ok), years < origin. Under
    seen-unit splits (S0/S1) this leaks each training row's own target into its feature.
    auto: pre_train when every test unit is a training unit (S0/S1), else train (S2-S4,
    where training units get leave-one-out kNN values and test units are not in the pool)."""
    from pop.splits.splits import row_masks
    if period not in C1_PERIODS:
        raise ValueError(f"c1 period must be one of {C1_PERIODS}, got {period!r}")
    if period == "auto":
        period = "pre_train" if set(split.test_units) <= set(split.train_units) else "train"
    if period == "train":
        return panel[row_masks(panel, split)["train_target_ok"]], split.origin
    first = min(split.train_years)
    gap = panel["flag_gap"].fillna(False).to_numpy(bool) if "flag_gap" in panel else False
    keep = panel.unit_id.isin(split.train_units).to_numpy() & (panel.year < first).to_numpy() & ~gap
    return panel[keep], first


def c1_matched_rule(split, country=None, buffer_km=None) -> dict:
    """Leave-out rule held-out units face, for C1 train_mode='matched' (S2: same adm1; S3: within
    D km, D from splits_v1/buffer_distance.json unless `buffer_km` is given; others: plain LOO)."""
    if split.name in ("S2", "S2L"):
        return {"exclude_group": "adm1"}
    if split.name in ("S3", "S3B"):
        if buffer_km is None:
            import json
            from pop.splits.splits import SPLIT_DIR
            buffer_km = json.loads((SPLIT_DIR / "buffer_distance.json").read_text())[
                country or split.country]["D_km"]
        return {"exclude_within_km": float(buffer_km)}
    return {}


def make_controls_for_split(control, split, units_df, panel=None, emb_df=None, seed=0,
                            c1_period="auto", c1_buffer_km=None, **kw):
    """Convenience wrapper. C1 source rows come from c1_source_rows(panel, split, c1_period):
    by default pre-training years for S0/S1 and training target rows for S2-S4. C1's default
    train_mode 'matched' takes its leave-out rule from c1_matched_rule(split) (c1_buffer_km
    overrides the S3 buffer D)."""
    train_rows, origin = None, split.origin
    if control == "C1":
        train_rows, origin = c1_source_rows(panel, split, c1_period)
        if kw.get("train_mode", "matched") == "matched" and not set(split.test_units) <= set(split.train_units):
            for key, v in c1_matched_rule(split, buffer_km=c1_buffer_km).items():
                kw.setdefault(key, v)
    return make_controls(control, units_df, split.train_units, split.test_units, origin,
                         train_rows, emb_df, seed, **kw)
