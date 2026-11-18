#!/usr/bin/env python
"""Exploratory, scoring-only analyses for the external review (RQ5, Comment 10, Section 5.6).

No model is refitted: every number comes from the existing primary-cell scores/forecasts.

Usage (GPU, after `source env.sh`; one process per cell, then combine):
    nice -n 19 python scripts/analysis/review_explore.py {strata,distance,decomp,all,combine} \
        [--cells BR_S1 TW_S5 ...] [--out docs/results/review]

Analyses
1. strata   (RB_strata.csv): G_excess and G_emb within exploratory strata of units:
            (a) population tercile (unit population in the year before the test year; terciles
                within cell x test year), (b) surveillance history = number of years 2014-2017
                with >= 1 reported case (0 / 1-2 / 3-4), (c) urban growth = GHSL built-up share
                change between the 2010 and 2015 epochs (the last epoch before the 2020 test
                window), terciles within cell; a relative-growth variant is also given.
            Inference within a stratum = the primary estimator on that stratum's rows
            (pop.eval.estimands.infer_estimand: equal-week pooling, DM/EWC + HLN). Exploratory:
            no multiplicity adjustment. Additive contributions (analysis 3 identity) are also
            given so the strata sum to the cell total.
2. distance (RB_distance_units.csv, RB_distance_bins.csv, RB_distance_spearman.csv,
            RB_upperq_bins.csv, RB_s5_distance.png): per held-out unit and test year y, max and
            top-5 mean cosine similarity between the unit's AlphaEarth y-1 embedding
            (renormalised) and the TRAINING units' embeddings for y-1 (a training country
            lacking y-1 uses its latest year <= y-1). Related to per-unit G_excess / G_emb.
            On zero-case rows, the per-quantile decomposition of WIS (log1p scale; for y = 0
            and q >= 0, WIS = sum_tau (1 - tau) log1p(q_tau) / (K + 0.5), K = 4) splits the L3+C* vs
            L4+C* difference into upper-quantile (tau >= 0.6), median and lower parts.
3. decomp   (RB_decomp.csv): the week-weighted estimator and its observed / zero-filled strata.
            Identity per (h, t): d_ht = w_ht d^obs_ht + (1 - w_ht) d^zf_ht, w_ht = observed row
            share. Hence total = mean_t mean_h [w_ht d^obs_ht] + mean_t mean_h [(1-w_ht) d^zf_ht]
            exactly (contributions); the two stratum estimates (each equal-week weighted) do
            not combine to the total with any fixed weights. Contributions get EWC CIs.
"""
from __future__ import annotations

import argparse
import gc
import json
import os
import sys
from pathlib import Path

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_MAX_THREADS"):
    os.environ.setdefault(_v, "4")

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent / "run")]

QLEV = np.round(np.arange(1, 10) / 10, 6)       # primary quantile set (median + deciles)
K = 4                                           # central intervals (alpha .2,.4,.6,.8)
EST = ("G_excess", "G_emb")
HIST_YEARS = (2014, 2017)
BUILT_EPOCHS = (2010, 2015)
COUNTRY_UP = {"brazil": "BRAZIL", "colombia": "COLOMBIA", "peru": "PERU", "taiwan": "TAIWAN"}


# ------------------------------------------------------------------------------ pure helpers
def terciles(x: pd.Series) -> pd.Series:
    """'T1' (low) .. 'T3' (high) by rank-based thirds; NaN stays NaN."""
    r = x.rank(method="first")
    n = r.notna().sum()
    if n == 0:
        return pd.Series(pd.NA, index=x.index, dtype="object")
    b = np.ceil(3 * r / n).clip(1, 3)
    return b.map(lambda v: f"T{int(v)}" if pd.notna(v) else pd.NA)


def history_group(nyears) -> pd.Series:
    n = pd.Series(nyears)
    return pd.Series(np.select([n == 0, n <= 2], ["0", "1-2"], "3-4"), index=n.index).where(n.notna())


def built_2010_from_yearly(s2013: np.ndarray, s2015: np.ndarray) -> np.ndarray:
    """Linear interpolation inverse: s2013 = s2010 + 0.6 (s2015 - s2010) -> s2010."""
    return (np.asarray(s2013, float) - 0.6 * np.asarray(s2015, float)) / 0.4


def renorm(m: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(m, axis=1, keepdims=True)
    with np.errstate(invalid="ignore", divide="ignore"):
        return m / n


def cosine_to_train(test: np.ndarray, train: np.ndarray, k: int = 5) -> tuple[np.ndarray, np.ndarray]:
    """Rows unit-norm. Returns (max cosine, mean of top-k cosines) per test row."""
    train = train[np.isfinite(train).all(axis=1)]
    out_max = np.full(len(test), np.nan)
    out_k = np.full(len(test), np.nan)
    ok = np.isfinite(test).all(axis=1)
    if not ok.any() or len(train) == 0:
        return out_max, out_k
    s = test[ok] @ train.T
    k = min(k, s.shape[1])
    top = -np.partition(-s, k - 1, axis=1)[:, :k]
    out_max[ok] = top.max(axis=1)
    out_k[ok] = top.mean(axis=1)
    return out_max, out_k


def zero_row_parts(vals_log: np.ndarray) -> dict:
    """Per-quantile WIS parts for y = 0 rows. ``vals_log`` (n, 9) = sorted log1p quantiles,
    columns = QLEV. Returns dict of arrays: total, upper (tau >= .6), median, lower (tau <= .4),
    q90 (tau = .9 term only)."""
    v = np.maximum(vals_log, 0.0)
    w = (1 - QLEV)[None, :] / (K + 0.5)
    part = v * w
    up = QLEV >= 0.6 - 1e-9
    lo = QLEV <= 0.4 + 1e-9
    med = np.isclose(QLEV, 0.5)
    return {"total": part.sum(1), "upper": part[:, up].sum(1), "median": part[:, med].sum(1),
            "lower": part[:, lo].sum(1), "q90": part[:, -1]}


def mean_ci(x: np.ndarray, alpha: float = 0.05) -> tuple[float, float, float, int]:
    from scipy import stats
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    n = len(x)
    if n == 0:
        return np.nan, np.nan, np.nan, 0
    m = float(x.mean())
    if n < 2:
        return m, np.nan, np.nan, n
    h = stats.t.ppf(1 - alpha / 2, n - 1) * x.std(ddof=1) / np.sqrt(n)
    return m, m - h, m + h, n


def week_contributions(g: pd.DataFrame, col: str, stratum: str, *, time_col="target_week",
                       horizon_col="horizon") -> tuple[pd.DataFrame, pd.Series]:
    """Exact additive split of the equal-week, pooled-h estimator of ``col`` over the levels of
    ``stratum``. Returns (weekly contributions wide [index=t, columns=levels], weekly total).

    Per (h, t): d_ht = sum_s w_sht dbar_sht with w_sht = n_sht / n_ht. Pooled over the horizons
    present at t with equal weights, then averaged over t: total = sum_s mean_t c_st with
    c_st = mean_h w_sht dbar_sht (0 where stratum s has no rows)."""
    k = [horizon_col, time_col]
    grp = g.groupby(k + [stratum], observed=True, sort=True)[col].agg(["sum", "size"])
    n_ht = g.groupby(k, sort=True).size()
    sums = grp["sum"].unstack(stratum, fill_value=0.0)
    sums = sums.reindex(n_ht.index, fill_value=0.0)
    contrib_ht = sums.div(n_ht, axis=0)                 # w_sht * dbar_sht = sum_s / n_ht
    c_t = contrib_ht.groupby(level=time_col).mean()     # equal horizon weights per week
    total_t = g.groupby(k, sort=True)[col].mean().groupby(level=time_col).mean()
    return c_t, total_t


def decompose(g: pd.DataFrame, col: str, stratum: str, *, ref_col: str = "wis_L3") -> pd.DataFrame:
    """Total, per-stratum equal-week estimates and exact contributions with EWC CIs."""
    from pop.eval.estimands import infer_estimand
    from pop.eval.stats import ewc_inference
    hmax = int(g.horizon.max())
    c_t, tot_t = week_contributions(g, col, stratum)
    tot = infer_estimand(g, col, ref_col=ref_col, margin_rel=0.01)
    wis_ref = tot["wis_ref"]
    share = g[stratum].value_counts(normalize=True)
    rows = [{"stratum": "TOTAL", "row_share": 1.0, "estimate": tot["estimate"],
             "lo95": tot["lo95"], "hi95": tot["hi95"], "p": tot["p"],
             "pct_of_own_ref": tot["pct_of_ref"], "own_wis_ref": wis_ref,
             "contribution": float(tot_t.mean()), "contrib_lo95": tot["lo95"],
             "contrib_hi95": tot["hi95"], "contrib_p": tot["p"],
             "contrib_pct_of_total_ref": 100 * float(tot_t.mean()) / wis_ref,
             "n_rows": len(g), "n_units": g.unit_id.nunique()}]
    for s in c_t.columns:
        sub = g[g[stratum] == s]
        r = infer_estimand(sub, col, ref_col=ref_col, margin_rel=0.01) if len(sub) else {}
        ci = ewc_inference(c_t[s].to_numpy(), h=hmax)
        rows.append({"stratum": str(s), "row_share": float(share.get(s, 0.0)),
                     "estimate": r.get("estimate", np.nan), "lo95": r.get("lo95", np.nan),
                     "hi95": r.get("hi95", np.nan), "p": r.get("p", np.nan),
                     "pct_of_own_ref": r.get("pct_of_ref", np.nan),
                     "own_wis_ref": r.get("wis_ref", np.nan),
                     "contribution": float(c_t[s].mean()), "contrib_lo95": ci.lo95,
                     "contrib_hi95": ci.hi95, "contrib_p": ci.p,
                     "contrib_pct_of_total_ref": 100 * float(c_t[s].mean()) / wis_ref,
                     "n_rows": len(sub), "n_units": sub.unit_id.nunique()})
    out = pd.DataFrame(rows)
    out["identity_residual"] = float(tot_t.mean()) - float(c_t.sum(axis=1).mean())
    return out


# ------------------------------------------------------------------------------ data access
def primary_cells(ids=None) -> list[dict]:
    import rk_cells as R
    cells = [c for c in R.build_registry() if c["group"] == "primary"]
    out = []
    for c in cells:
        if ids and c["id"] not in ids:
            continue
        st, _ = R.cell_status(c)
        c["status"] = st
        out.append(c)
    return out


def load_g(cell: dict) -> tuple[pd.DataFrame, dict]:
    """Primary gain frame (default exclusions) restricted to the primary horizons."""
    import rk_cells as R
    from estimands_report import load_cell
    g, info = load_cell({r: cell["roles"][r]["dirs"] for r in R.ROLES}, panel=cell.get("panel"))
    hp = cell.get("primary_horizons") or [1, 4]
    keep = ["test_year", "unit_id", "origin_week", "target_week", "horizon", "wis_L3", "wis_L4",
            "wis_L3C", "wis_L4C", "G_emb", "G_id", "G_excess", "zero_filled", "cases", "state"]
    keep += [c for c in g.columns if "@" in c and c.split("@")[0] in
             ("G_emb", "G_excess", "has_G_emb", "has_G_excess", "wis_L3")]
    seeds = g.attrs.get("seeds")
    g = g.loc[g.horizon.isin(hp), keep].reset_index(drop=True)
    g.attrs["seeds"] = seeds
    return g, info


def ae_year(country: str, year: int) -> pd.DataFrame | None:
    """Unit-norm AE embeddings (index unit_id). Latest available year <= ``year``."""
    d = Path("data/interim/alphaearth") / country
    for y in range(year, 2016, -1):
        f = d / f"alphaearth_{country}_{y}.parquet"
        if f.exists():
            a = pd.read_parquet(f)
            cols = [f"w_A{i:02d}" for i in range(64)]
            m = renorm(a[cols].to_numpy(float))
            out = pd.DataFrame(m, index=a.unit_id.astype(str), columns=cols)
            out.attrs["year"] = y
            return out
    return None


def unit_attributes(country: str) -> pd.DataFrame:
    """Per unit: surveillance history (years 2014-17 with >= 1 case), built-up 2010/2015."""
    C = COUNTRY_UP[country]
    p = pd.read_parquet("data/processed/panel_weekly_v1.parquet",
                        columns=["unit_id", "country", "year", "cases"],
                        filters=[("year", ">=", HIST_YEARS[0]), ("year", "<=", HIST_YEARS[1])])
    p = p[p.country.astype(str).str.upper() == C]
    p["unit_id"] = p.unit_id.astype(str)
    yrs = p[p.cases > 0].groupby("unit_id").year.nunique()
    units = pd.Index(p.unit_id.unique())
    out = pd.DataFrame(index=units)
    out["hist_years"] = yrs.reindex(units).fillna(0).astype(int)
    rs = pd.read_parquet(f"data/interim/remote_sensing/rs_yearly_{country}_v1.parquet",
                         columns=["unit_id", "year", "built_share"])
    rs["unit_id"] = rs.unit_id.astype(str)
    w = rs.pivot(index="unit_id", columns="year", values="built_share")
    b10 = built_2010_from_yearly(w[2013].to_numpy(), w[2015].to_numpy())
    bu = pd.DataFrame({"built_2010": b10, "built_2015": w[2015].to_numpy()}, index=w.index)
    bu["urban_growth_pp"] = 100 * (bu.built_2015 - bu.built_2010)
    with np.errstate(invalid="ignore", divide="ignore"):
        bu["urban_growth_rel"] = np.where(bu.built_2010 > 0, bu.built_2015 / bu.built_2010 - 1,
                                          np.nan)
    return out.join(bu, how="outer")


def population(units) -> pd.DataFrame:
    p = pd.read_parquet("data/interim/population/unit_population_yearly_v1.parquet")
    p["unit_id"] = p.unit_id.astype(str)
    return p[p.unit_id.isin(set(units))]


# ------------------------------------------------------------------------------ analysis 1
def run_strata(cell: dict, g: pd.DataFrame) -> pd.DataFrame:
    country = cell["country"]
    seeds = g.attrs.get("seeds")
    att = unit_attributes(country)
    pop = population(g.unit_id.unique())
    uy = g[["unit_id", "test_year"]].drop_duplicates()
    uy = uy.merge(pop.assign(test_year=pop.year + 1)[["unit_id", "test_year", "pop"]],
                  on=["unit_id", "test_year"], how="left")
    uy["pop_tercile"] = uy.groupby("test_year", group_keys=False)["pop"].apply(terciles)
    ua = att.reindex(g.unit_id.unique())
    ua["history"] = history_group(ua.hist_years).to_numpy()
    ua["urban_growth_tercile"] = terciles(ua.urban_growth_pp)
    ua["urban_growth_rel_tercile"] = terciles(ua.urban_growth_rel)
    g = g.merge(uy[["unit_id", "test_year", "pop_tercile"]], on=["unit_id", "test_year"],
                how="left")
    g = g.merge(ua[["history", "urban_growth_tercile", "urban_growth_rel_tercile"]],
                left_on="unit_id", right_index=True, how="left")
    g.attrs["seeds"] = seeds
    rows = []
    for dim in ("pop_tercile", "history", "urban_growth_tercile", "urban_growth_rel_tercile"):
        gg = g.assign(**{dim: g[dim].fillna("NA").astype(str)})
        gg.attrs["seeds"] = seeds
        for e in EST:
            d = decompose(gg, e, dim)
            d.insert(0, "estimand", e)
            d.insert(0, "dimension", dim)
            rows.append(d)
    out = pd.concat(rows, ignore_index=True)
    out.insert(0, "cell", cell["id"])
    return out


# ------------------------------------------------------------------------------ analysis 2
def train_units(cell: dict, fold) -> frozenset:
    from pop.splits.splits import get_split
    C = COUNTRY_UP[cell["country"]]
    if cell["split"] == "S5":
        return get_split("S5", C, fold=C).train_units
    return get_split(cell["split"], C, fold=int(fold)).train_units


def unit_fold(cell: dict) -> pd.Series:
    from pop.splits.splits import FOLD_COL, load_unit_folds
    uf = load_unit_folds()
    uf = uf[uf.country == COUNTRY_UP[cell["country"]]]
    return pd.Series(uf[FOLD_COL[cell["split"]]].to_numpy(), index=uf.unit_id.astype(str))


def distances(cell: dict, g: pd.DataFrame) -> pd.DataFrame:
    """Per (held-out unit, test year): max and top-5 mean cosine to the training units."""
    from pop.splits.splits import load_unit_folds
    uf = load_unit_folds()
    cty = uf.set_index(uf.unit_id.astype(str)).country.str.lower()
    folds = unit_fold(cell) if cell["split"] != "S5" else None
    rows = []
    cache = {}

    def emb(c, y):
        if (c, y) not in cache:
            cache[(c, y)] = ae_year(c, y)
        return cache[(c, y)]

    for y in sorted(g.test_year.unique()):
        units = pd.Index(g.loc[g.test_year == y, "unit_id"].unique())
        te = emb(cell["country"], int(y) - 1)
        groups = {None: units} if folds is None else {
            f: units[folds.reindex(units).to_numpy() == f] for f in folds.reindex(units).dropna().unique()}
        for f, us in groups.items():
            tr = train_units(cell, f)
            mats, yrs = [], {}
            for c in sorted(set(cty.reindex(list(tr)).dropna())):
                e = emb(c, int(y) - 1)
                if e is None:
                    continue
                yrs[c] = e.attrs["year"]
                mats.append(e.reindex([u for u in e.index if u in tr]).to_numpy())
            train = np.vstack(mats)
            test = te.reindex(us).to_numpy()
            mx, k5 = cosine_to_train(test, train)
            rows.append(pd.DataFrame({"unit_id": us, "test_year": int(y), "fold": str(f),
                                      "cos_max": mx, "cos_top5": k5,
                                      "train_ae_years": json.dumps(yrs)}))
    return pd.concat(rows, ignore_index=True)


def zero_row_quantiles(cell: dict, g: pd.DataFrame) -> pd.DataFrame:
    """Per zero-case scored row: WIS parts of L3+C* and L4+C* (seed 0, primary horizons)."""
    import pyarrow.parquet as pq
    z = g.loc[g.cases == 0, ["unit_id", "origin_week", "target_week", "horizon", "test_year"]]
    out = []
    for y in sorted(z.test_year.unique()):
        parts = {}
        for role in ("L3C", "L4C"):
            d = Path(cell["roles"][role]["dirs"][0])
            t = pq.read_table(d / "forecasts.parquet",
                              columns=["seed", "unit_id", "origin_week", "target_week", "horizon",
                                       "quantile", "value"],
                              filters=[("test_year", "==", int(y)), ("seed", "==", 0),
                                       ("horizon", "in", sorted(set(g.horizon)))])
            f = t.to_pandas()
            del t
            f["unit_id"] = f.unit_id.astype(str)
            f["quantile"] = np.round(f["quantile"].astype(float), 6)
            f = f[f["quantile"].isin(QLEV)]
            w = f.pivot_table(index=["unit_id", "origin_week", "target_week", "horizon"],
                              columns="quantile", values="value", aggfunc="first")
            del f
            w = w.reindex(columns=QLEV)
            zy = z[z.test_year == y].set_index(["unit_id", "origin_week", "target_week", "horizon"])
            w = w.reindex(zy.index)
            v = np.sort(np.log1p(np.maximum(w.to_numpy(float), 0.0)), axis=1)
            p = zero_row_parts(v)
            p["q90_log"] = v[:, -1]
            parts[role] = p
            idx = zy.index
        df = pd.DataFrame(idx.to_frame(index=False))
        df["test_year"] = int(y)
        for role, p in parts.items():
            for k, a in p.items():
                df[f"{k}_{role}"] = a
        out.append(df)
        gc.collect()
    return pd.concat(out, ignore_index=True)


def run_distance(cell: dict, g: pd.DataFrame) -> dict:
    dist = distances(cell, g)
    uyr = g.groupby(["unit_id", "test_year"]).agg(
        G_excess=("G_excess", "mean"), G_emb=("G_emb", "mean"), wis_L3=("wis_L3", "mean"),
        zero_share=("cases", lambda s: float((s == 0).mean())), n_rows=("G_excess", "size")
    ).reset_index()
    uyr = uyr.merge(dist, on=["unit_id", "test_year"], how="left")
    zq = zero_row_quantiles(cell, g)
    # sanity: reconstructed WIS on zero rows equals the scored wis_log
    chk = zq.merge(g[["unit_id", "origin_week", "target_week", "horizon", "wis_L3C", "wis_L4C"]],
                   on=["unit_id", "origin_week", "target_week", "horizon"], how="left")
    seeds = g.attrs.get("seeds") or [0]
    recon = {"L3C": float(np.nanmax(np.abs(chk.total_L3C - chk.wis_L3C))),
             "L4C": float(np.nanmax(np.abs(chk.total_L4C - chk.wis_L4C)))} if len(seeds) == 1 else {}
    zagg = zq.groupby(["unit_id", "test_year"]).agg(
        **{f"z_{k}_{r}": (f"{k}_{r}", "mean") for k in ("total", "upper", "median", "lower", "q90",
                                                       "q90_log") for r in ("L3C", "L4C")},
        n_zero=("total_L3C", "size")).reset_index()
    uyr = uyr.merge(zagg, on=["unit_id", "test_year"], how="left")
    uyr.insert(0, "cell", cell["id"])
    return {"units": uyr, "recon_maxabs": recon}


def unit_level(uyr: pd.DataFrame) -> pd.DataFrame:
    """Collapse unit x year to unit: row-weighted gains, mean cosines; zero-row parts weighted
    by zero-row counts."""
    def wmean(df, c, w):
        ok = df[c].notna() & (df[w] > 0)
        return float(np.average(df.loc[ok, c], weights=df.loc[ok, w])) if ok.any() else np.nan

    rows = []
    for (cell, u), d in uyr.groupby(["cell", "unit_id"]):
        r = {"cell": cell, "unit_id": u, "cos_max": d.cos_max.mean(), "cos_top5": d.cos_top5.mean(),
             "n_rows": int(d.n_rows.sum()), "n_zero": float(d.n_zero.fillna(0).sum())}
        for c in ("G_excess", "G_emb", "wis_L3", "zero_share"):
            r[c] = wmean(d, c, "n_rows")
        for c in [c for c in d.columns if c.startswith("z_")]:
            r[c] = wmean(d.assign(n_zero=d.n_zero.fillna(0)), c, "n_zero")
        rows.append(r)
    return pd.DataFrame(rows)


def distance_summaries(units: pd.DataFrame, nbins: int = 5) -> tuple[pd.DataFrame, pd.DataFrame,
                                                                      pd.DataFrame]:
    from scipy import stats
    sp, bins, uq = [], [], []
    for cell, d in units.groupby("cell"):
        d = d[d.cos_max.notna()].copy()
        for e in EST:
            for x in ("cos_max", "cos_top5"):
                rho, p = stats.spearmanr(d[x], d[e], nan_policy="omit")
                sp.append({"cell": cell, "estimand": e, "distance": x, "spearman_rho": rho,
                           "p_naive": p, "n_units": len(d)})
        d["bin"] = pd.qcut(d.cos_max.rank(method="first"), nbins, labels=False) + 1
        for b, db in d.groupby("bin"):
            row = {"cell": cell, "bin": int(b), "cos_max_lo": db.cos_max.min(),
                   "cos_max_hi": db.cos_max.max(), "cos_max_mean": db.cos_max.mean(),
                   "n_units": len(db), "zero_share": db.zero_share.mean(), "wis_L3": db.wis_L3.mean()}
            for e in EST:
                m, lo, hi, _ = mean_ci(db[e])
                row.update({e: m, f"{e}_lo95": lo, f"{e}_hi95": hi,
                            f"{e}_share_units_neg": float((db[e] < 0).mean())})
            bins.append(row)
            dz = db[db.n_zero > 0]
            if len(dz) and "z_total_L3C" in dz:
                dtot = dz.z_total_L3C - dz.z_total_L4C       # >0 = L4+C* better; <0 = harm
                dup = dz.z_upper_L3C - dz.z_upper_L4C
                dq9 = dz.z_q90_L3C - dz.z_q90_L4C
                dmed = dz.z_median_L3C - dz.z_median_L4C
                wz = dz.n_zero
                tot = float(np.average(dtot, weights=wz))
                uq.append({"cell": cell, "bin": int(b), "cos_max_mean": db.cos_max.mean(),
                           "n_units": len(dz),
                           "zero_G_excess": tot,
                           "upper_part": float(np.average(dup, weights=wz)),
                           "median_part": float(np.average(dmed, weights=wz)),
                           "q90_part": float(np.average(dq9, weights=wz)),
                           "share_upper": float(np.average(dup, weights=wz)) / tot if tot else np.nan,
                           "share_q90": float(np.average(dq9, weights=wz)) / tot if tot else np.nan,
                           "q90_case_L3C": float(np.expm1(np.average(dz.z_q90_log_L3C, weights=wz))),
                           "q90_case_L4C": float(np.expm1(np.average(dz.z_q90_log_L4C, weights=wz)))})
    return pd.DataFrame(sp), pd.DataFrame(bins), pd.DataFrame(uq)


def plot_distance(units: pd.DataFrame, bins: pd.DataFrame, path: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    s5 = [c for c in ("BR_S5", "CO_S5", "PE_S5", "TW_S5") if c in set(units.cell)]
    colors = {"BR_S5": "#1b6ca8", "CO_S5": "#d97b29", "PE_S5": "#3a9a5b", "TW_S5": "#b8336a"}
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.4))
    for c in s5:
        d = units[units.cell == c]
        ax[0].scatter(d.cos_max, d.G_excess, s=5, alpha=0.25, color=colors[c], lw=0)
        b = bins[bins.cell == c]
        ax[1].errorbar(b.cos_max_mean, b.G_excess,
                       yerr=[b.G_excess - b.G_excess_lo95, b.G_excess_hi95 - b.G_excess],
                       marker="o", ms=4, capsize=2, color=colors[c], label=c.replace("_", " "))
    for a in ax:
        a.axhline(0, color="0.4", lw=0.8)
        a.set_xlabel("Max cosine similarity to training units (AlphaEarth, year y-1)")
    ax[0].set_ylabel("Per-unit excess gain (log-WIS; <0 = embeddings hurt)")
    ax[0].set_title("Units (S5: whole country held out)")
    ax[1].set_title("Quintile bins of similarity, mean and 95% CI")
    ax[1].legend(frameon=False, fontsize=8)
    ax[0].set_ylim(np.nanpercentile(units.loc[units.cell.isin(s5), "G_excess"], [0.5, 99.5]))
    fig.suptitle("Exploratory: embedding similarity to training units vs per-unit excess gain",
                 fontsize=10)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


# ------------------------------------------------------------------------------ analysis 3
def run_decomp(cell: dict, g: pd.DataFrame) -> pd.DataFrame:
    gg = g.assign(report=np.where(g.zero_filled, "zero_filled", "observed"))
    gg.attrs["seeds"] = g.attrs.get("seeds")
    rows = []
    for e in ("G_excess", "G_emb"):
        d = decompose(gg, e, "report")
        tot = d[d.stratum == "TOTAL"].iloc[0]
        st = d[d.stratum != "TOTAL"].set_index("stratum")
        naive = float((st.row_share * st.estimate).sum())
        d["naive_rowshare_combo"] = naive
        d["naive_minus_total"] = naive - tot.estimate
        d.insert(0, "estimand", e)
        rows.append(d)
    out = pd.concat(rows, ignore_index=True)
    out.insert(0, "cell", cell["id"])
    return out


# ------------------------------------------------------------------------------ main
def run_cell(c: dict, todo: set, cdir: Path) -> None:
    """One cell -> per-cell CSVs in ``cdir`` (one process per cell keeps memory bounded)."""
    cdir.mkdir(parents=True, exist_ok=True)
    g, info = load_g(c)
    if "strata" in todo:
        run_strata(c, g).assign(cstar=c["cstar"]).to_csv(cdir / "strata.csv", index=False)
    if "decomp" in todo:
        run_decomp(c, g).assign(cstar=c["cstar"]).to_csv(cdir / "decomp.csv", index=False)
    if "distance" in todo and c["split"] in ("S2", "S3", "S4", "S5"):
        r = run_distance(c, g)
        r["units"].to_csv(cdir / "distance_unit_years.csv", index=False)
        (cdir / "recon.json").write_text(json.dumps(r["recon_maxabs"]))


def combine(out: Path) -> None:
    cd = out / "cells"
    def cat(name):
        fs = sorted(cd.glob(f"*/{name}"))
        return pd.concat([pd.read_csv(f) for f in fs], ignore_index=True) if fs else None
    for name, dst in (("strata.csv", "RB_strata.csv"), ("decomp.csv", "RB_decomp.csv")):
        d = cat(name)
        if d is not None:
            d.to_csv(out / dst, index=False)
    uyr = cat("distance_unit_years.csv")
    if uyr is not None:
        uyr.to_csv(out / "RB_distance_unit_years.csv", index=False)
        units = unit_level(uyr)
        units.to_csv(out / "RB_distance_units.csv", index=False)
        sp, bins, uq = distance_summaries(units)
        sp.to_csv(out / "RB_distance_spearman.csv", index=False)
        bins.to_csv(out / "RB_distance_bins.csv", index=False)
        uq.to_csv(out / "RB_upperq_bins.csv", index=False)
        recon = {f.parent.name: json.loads(f.read_text()) for f in sorted(cd.glob("*/recon.json"))}
        (out / "RB_wis_reconstruction_check.json").write_text(json.dumps(recon, indent=1))
        plot_distance(units, bins, out / "RB_s5_distance.png")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["strata", "distance", "decomp", "all", "combine"])
    ap.add_argument("--cells", nargs="*", default=None)
    ap.add_argument("--out", default="docs/results/review")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    if a.what == "combine":
        combine(out)
        print("combined", flush=True)
        return
    todo = {"strata", "distance", "decomp"} if a.what == "all" else {a.what}
    cells = [c for c in primary_cells(a.cells) if c["status"] == "available"]
    print("cells:", [c["id"] for c in cells], flush=True)
    for c in cells:
        print(f"== {c['id']} (C*={c['cstar']})", flush=True)
        run_cell(c, todo, out / "cells" / c["id"])
        gc.collect()
    print("done", flush=True)


if __name__ == "__main__":
    main()
