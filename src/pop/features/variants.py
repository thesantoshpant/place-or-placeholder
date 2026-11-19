"""Round-3 embedding-representation variants (post hoc, exploratory; docs/methods/round3_variants.md).

Purely additive: new level names only; every existing level in ``levels.LEVELS`` is untouched.

    V1  AE-kNN risk encoding (1 col, v1_ae_knn). Embedding-space analogue of C1: for each unit, the
        inverse-dissimilarity weighted mean, over its k = 5 most cosine-similar TRAINING units of the
        same country (self excluded), of the training units' mean log1p(cases) over the years before
        the first training target year (exactly C1's source rows: c1_source_rows 'pre_train', i.e.
        training units only, flag_gap weeks dropped). Weight 1 / (1 - cos + eps), eps = 1e-3.
        Similarity uses the causal static embedding of V3 (mean of 2017 and 2018, renormalised).
        Unseen-unit splits (S2-S4) use C1's matched leave-out for training-unit queries
        (S2: no neighbour from the unit's own adm1; S3: none within the buffer D); held-out units
        are encoded from the training pool. Static within (split, fold, origin).
    V2  PCA-8 (8 cols, v2_pc1..v2_pc8). PCA of the y-1 embedding (the L4 block), fitted per
        (split, fold, origin) on the training units' unit-year vectors of the embedding years the
        training targets use (y - 1 for y in split.train_years); held-out units never enter the
        fit. Components sign-fixed (largest |loading| positive). Every row's y-1 vector is projected.
    V3  Causal static embedding (64 cols, v3_A00..v3_A63): mean of the unit's 2017 and 2018 vectors
        (each as in L4: pop-weighted, renormalised), renormalised again; the same for all years.
    AE  "L2+AE": the L4 AlphaEarth block (y-1) in place of the L3 remote-sensing / population block.

Levels:  L3+V{1,2,3};  L3+C{k}+V{1,2,3} (columns = L3+Ck columns, then the variant block);  L2+AE.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

VARIANTS = ("V1", "V2", "V3")
V1_K = 5
V1_EPS = 1e-3
V2_NCOMP = 8
V3_YEARS = (2017, 2018)


# ------------------------------------------------------------------ pure helpers (testable)
def static_embedding_mean(emb: pd.DataFrame, years=V3_YEARS) -> pd.DataFrame:
    """unit_id -> mean of the unit's (already renormalised) vectors over `years`, renormalised.
    Years with a non-finite vector are skipped; units with none -> all NaN (kept out)."""
    from pop.features.levels import AE_BANDS, renormalize
    e = emb[emb.year.isin(years)]
    V = e[AE_BANDS].to_numpy(float)
    ok = np.isfinite(V).all(axis=1)
    g = pd.DataFrame(V[ok], columns=AE_BANDS).groupby(e.unit_id.to_numpy()[ok]).mean()
    out = pd.DataFrame(renormalize(g.to_numpy(float)), index=g.index.astype(str), columns=AE_BANDS)
    return out


def ae_knn_encode(query_units, pool_values: pd.Series, static: pd.DataFrame, units_df: pd.DataFrame,
                  k=V1_K, eps=V1_EPS, matched_queries=(), exclude_group=None,
                  exclude_within_km=None) -> pd.Series:
    """Cosine-kNN encoding. pool_values: training unit -> value (only these units can be
    neighbours). Each query excludes itself; queries in `matched_queries` also exclude pool units
    sharing their `exclude_group` value or within `exclude_within_km` km. Same country only.
    Weight 1 / (1 - cos + eps). Fewer than k admissible neighbours -> those available; none -> NaN."""
    from pop.features.controls import _gc_matrix, _latlon, _xyz
    q_ids = pd.Index(pd.unique(np.asarray(list(query_units), dtype=str)))
    out = pd.Series(np.nan, index=q_ids, dtype=float)
    pv = pool_values.copy()
    pv.index = pv.index.astype(str)
    pv = pv[np.isfinite(pv.to_numpy(float))]
    ud = units_df.assign(unit_id=units_df.unit_id.astype(str)).drop_duplicates("unit_id").set_index("unit_id")
    st = static[np.isfinite(static.to_numpy(float)).all(axis=1)]
    pool = pv.index[pv.index.isin(st.index) & pv.index.isin(ud.index)]
    qs = q_ids[q_ids.isin(st.index) & q_ids.isin(ud.index)]
    matched = set(map(str, matched_queries))
    for c in sorted(set(ud.loc[qs, "country"].astype(str))):
        qc = qs[(ud.loc[qs, "country"].astype(str) == c).to_numpy()]
        pc = pool[(ud.loc[pool, "country"].astype(str) == c).to_numpy()]
        if len(pc) == 0 or len(qc) == 0:
            continue
        S = st.loc[qc].to_numpy(float) @ st.loc[pc].to_numpy(float).T
        D = np.clip(1.0 - S, 0.0, None)
        D[qc.to_numpy()[:, None] == pc.to_numpy()[None, :]] = np.inf
        m = np.isin(qc.to_numpy(), list(matched))
        if m.any() and exclude_group is not None:
            same = ud.loc[qc, exclude_group].to_numpy()[:, None] == ud.loc[pc, exclude_group].to_numpy()[None, :]
            D[m[:, None] & same] = np.inf
        if m.any() and exclude_within_km is not None:
            G = _gc_matrix(_xyz(*_latlon(ud.loc[qc])), _xyz(*_latlon(ud.loc[pc])))
            D[m[:, None] & (G <= float(exclude_within_km))] = np.inf
        vals = pv.reindex(pc).to_numpy(float)
        kk = min(k, D.shape[1])
        idx = np.argsort(D, axis=1, kind="stable")[:, :kk]  # stable: deterministic ties
        d = np.take_along_axis(D, idx, 1)
        ok = np.isfinite(d)
        w = np.where(ok, 1.0 / (np.where(ok, d, 0.0) + eps), 0.0)
        num = np.where(ok, w * vals[idx], 0.0).sum(1)
        den = w.sum(1)
        with np.errstate(invalid="ignore", divide="ignore"):
            out.loc[qc] = np.where(den > 0, num / np.where(den > 0, den, 1.0), np.nan)
    return out


def fit_pca(X: np.ndarray, n=V2_NCOMP):
    """(mean, components (n, p)) of the rows of X by SVD; each component's largest-|loading|
    entry made positive (deterministic sign)."""
    mu = X.mean(axis=0)
    _, _, Vt = np.linalg.svd(X - mu, full_matrices=False)
    C = Vt[:n].copy()
    j = np.abs(C).argmax(axis=1)
    C *= np.sign(C[np.arange(len(C)), j])[:, None]
    return mu, C


# ------------------------------------------------------------------ blocks (grid-aligned)
def _split_key(ctx, name):
    sp = ctx.split
    if sp is None:
        raise ValueError(f"variant {name} needs ctx.split")
    return ("split", "variant", name, sp.name, str(sp.fold), sp.origin)


def _static(grid, ctx):
    return ctx._cached(grid, ("v3_static",), lambda: static_embedding_mean(ctx.embeddings()))


def v1_block(grid, idx, ctx) -> pd.DataFrame:
    from pop.features.controls import c1_matched_rule, c1_source_rows, unit_level
    key = _split_key(ctx, "V1")
    if key not in ctx._cache:
        sp = ctx.split
        rows, cutoff = c1_source_rows(ctx.panel, sp, "pre_train")
        vals = unit_level(rows, sp.train_units, cutoff)
        vals = vals[vals.index.astype(str).isin({str(u) for u in sp.train_units})]
        unseen = not set(sp.test_units) <= set(sp.train_units)
        rule = c1_matched_rule(sp) if unseen else {}
        q = sorted({str(u) for u in set(sp.train_units) | set(sp.test_units)})
        ctx._cache[key] = ae_knn_encode(
            q, vals, static_embedding_mean(ctx.embeddings()), ctx.table("units"),
            matched_queries=[str(u) for u in sp.train_units] if rule else (), **rule)
    s = ctx._cache[key]
    v = s.reindex(grid.units[idx["u"].to_numpy()].astype(str)).to_numpy(float)
    return pd.DataFrame({"v1_ae_knn": v.astype(np.float32)}, index=idx.index)


def v2_block(grid, idx, ctx) -> pd.DataFrame:
    from pop.features.levels import AE_BANDS, alphaearth_block
    key = _split_key(ctx, "V2")
    if key not in ctx._cache:
        sp = ctx.split
        e = ctx.embeddings()
        fit_years = {int(y) - 1 for y in sp.train_years}
        tr = e[e.unit_id.astype(str).isin({str(u) for u in sp.train_units}) & e.year.isin(fit_years)]
        X = tr[AE_BANDS].to_numpy(float)
        X = X[np.isfinite(X).all(axis=1)]
        ctx._cache[key] = fit_pca(X)
    mu, C = ctx._cache[key]
    A = alphaearth_block(grid, idx, ctx).to_numpy(np.float64)
    Z = (A - mu) @ C.T
    return pd.DataFrame(Z.astype(np.float32), columns=[f"v2_pc{i + 1}" for i in range(C.shape[0])],
                        index=idx.index)


def v3_block(grid, idx, ctx) -> pd.DataFrame:
    from pop.features.levels import AE_BANDS
    st = _static(grid, ctx)
    X = st.reindex(grid.units[idx["u"].to_numpy()].astype(str)).to_numpy(float)
    return pd.DataFrame(X.astype(np.float32), columns=[f"v3_{b}" for b in AE_BANDS], index=idx.index)


VARIANT_BLOCKS = {"V1": v1_block, "V2": v2_block, "V3": v3_block}


# ------------------------------------------------------------------ levels
def _l3v(variant, control=None):
    def fn(grid, idx, h, ctx):
        from pop.features import levels as L
        parts = [L._l3(grid, idx, h, ctx)]
        if control is not None:
            parts.append(L.control_block(control, grid, idx, ctx))
        parts.append(VARIANT_BLOCKS[variant](grid, idx, ctx))
        return pd.concat(parts, axis=1)
    fn.__name__ = "l3_" + (f"{control.lower()}_" if control else "") + variant.lower()
    return fn


def _l2ae(grid, idx, h, ctx):
    from pop.features import levels as L
    return pd.concat([L._l2(grid, idx, h, ctx), L.alphaearth_block(grid, idx, ctx)], axis=1)


def variant_levels(controls) -> dict:
    out = {f"L3+{v}": _l3v(v) for v in VARIANTS}
    out.update({f"L3+{c}+{v}": _l3v(v, c) for c in controls for v in VARIANTS})
    out["L2+AE"] = _l2ae
    return out


_CONTROLS = ("C1", "C2", "C3", "C4", "C4s", "C5", "C6")  # == levels.CONTROLS (checked in tests)
VARIANT_LEVELS = variant_levels(_CONTROLS)
