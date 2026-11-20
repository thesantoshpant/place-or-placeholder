"""R3-E1 information probe: cross-sectional prediction of district dengue burden.

Separates (a) "AlphaEarth embeddings carry no transferable burden information" from
(b) "they carry it, but it is redundant with case history at h <= 4 weeks".

One row per district. Targets (T1..T4), feature sets (G, S, E and combinations),
ridge + small LightGBM, grouped-state / random / leave-one-country-out CV,
out-of-fold R^2 and Spearman with state-cluster bootstrap CIs.

Usage:  nice -n 19 python scripts/analysis/info_probe.py [--boot 1000] [--threads 8]
Outputs: docs/results/review/R3_E1_info_probe.{csv,md}, docs/results/figures/pub/FigS4_info_probe.png
Data only: reads data/processed and data/interim; no runs/ directory is touched.
"""
from __future__ import annotations

import argparse
import zlib
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[2]
import sys
sys.path.insert(0, str(ROOT / "src"))
from pop.features.controls import coordinate_harmonics  # noqa: E402
from pop.features.levels import renormalize  # noqa: E402

COUNTRIES = ("BRAZIL", "COLOMBIA", "PERU", "TAIWAN")
LAST_YEAR = {"BRAZIL": 2024, "COLOMBIA": 2022, "PERU": 2023, "TAIWAN": 2024}
PRE = (2014, 2019)
BANDS = [f"A{i:02d}" for i in range(64)]
TARGETS = {
    "T1": "mean log1p weekly cases 2014-2019",
    "T2": "mean log1p weekly cases, test years (2020-last)",
    "T3": "share of weeks with >=1 case 2014-2019",
    "T4": "mean log1p weekly incidence per 100k 2014-2019",
}
OUT_CSV = ROOT / "docs/results/review/R3_E1_info_probe.csv"
OUT_MD = ROOT / "docs/results/review/R3_E1_info_probe.md"
OUT_FIG = ROOT / "docs/results/figures/pub/FigS4_info_probe.png"


# ----------------------------------------------------------------------------- data
def load_targets() -> pd.DataFrame:
    p = pd.read_parquet(ROOT / "data/processed/panel_weekly_v1.parquet",
                        columns=["unit_id", "country", "adm1", "week_start", "year", "cases"])
    p["unit_id"] = p.unit_id.astype(str)
    p["week_start"] = pd.to_datetime(p.week_start)
    ex = ROOT / "data/processed/exclusions_v2"
    nogeo = set(pd.read_csv(ex / "no_geometry_units.csv").unit_id.astype(str))
    p = p[~p.unit_id.isin(nogeo)]
    # incomplete weeks (primary "exclude" flags only)
    iw = pd.read_csv(ex / "incomplete_weeks.csv")
    iw = iw[iw.action.str.strip().str.lower() == "exclude"]
    iw["week_start"] = pd.to_datetime(iw.week_start)
    drop = np.zeros(len(p), bool)
    for r in iw.itertuples():
        m = (p.country.to_numpy() == r.country) & (p.week_start.to_numpy() == np.datetime64(r.week_start))
        if r.scope == "adm1":
            m &= p.adm1.to_numpy() == r.adm1
        drop |= m
    # unit-week exclusions (Espirito Santo from 2019-12-29)
    uw = pd.read_csv(ex / "unit_week_exclusions.csv", dtype={"unit_id": str})
    uw = uw[uw.action.str.lower() == "exclude"]
    uw["from_week"] = pd.to_datetime(uw.from_week)
    uw["to_week"] = pd.to_datetime(uw.to_week)
    q = p[["unit_id", "week_start"]].merge(uw[["unit_id", "from_week", "to_week"]], on="unit_id", how="left")
    m = q.from_week.notna() & (q.week_start >= q.from_week) & (q.to_week.isna() | (q.week_start <= q.to_week))
    drop |= m.to_numpy()
    n_drop = int(drop.sum())
    p = p[~drop].copy()

    pop = pd.read_parquet(ROOT / "data/interim/population/unit_population_yearly_v1.parquet")
    pop["unit_id"] = pop.unit_id.astype(str)
    p = p.merge(pop, on=["unit_id", "year"], how="left")
    p["lc"] = np.log1p(p.cases)
    p["linc"] = np.log1p(p.cases / p["pop"] * 1e5)
    p["pos"] = (p.cases >= 1).astype(float)
    pre = p[p.year.between(*PRE)]
    g = pre.groupby("unit_id")
    T = pd.DataFrame({"T1": g.lc.mean(), "T3": g.pos.mean(), "T4": g.linc.mean(), "n_pre": g.size()})
    lasty = p.country.map(LAST_YEAR)
    test = p[(p.year >= 2020) & (p.year <= lasty)]
    T["T2"] = test.groupby("unit_id").lc.mean()
    meta = p.groupby("unit_id")[["country", "adm1"]].first()
    T = meta.join(T)
    # require a decent pre-period (>= 2 years of weeks) for T1/T3/T4
    for t in ("T1", "T3", "T4"):
        T.loc[T.n_pre < 104, t] = np.nan
    print(f"targets: {len(T)} units; dropped {n_drop} excluded unit-weeks", flush=True)
    return T.reset_index()


def load_embeddings() -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    for c in COUNTRIES:
        for y in (2017, 2018):
            d = pd.read_parquet(ROOT / f"data/interim/alphaearth/{c.lower()}/alphaearth_{c.lower()}_{y}.parquet")
            d["unit_id"] = d.unit_id.astype(str)
            rows.append(d[["unit_id", "year"] + [f"w_{b}" for b in BANDS]])
    a = pd.concat(rows)
    def mk(df):
        V = renormalize(df[[f"w_{b}" for b in BANDS]].to_numpy(float))
        return pd.DataFrame(V, columns=[f"e_{b}" for b in BANDS], index=df.unit_id.to_numpy())
    e18 = mk(a[a.year == 2018])
    m = a.groupby("unit_id")[[f"w_{b}" for b in BANDS]].mean().reset_index()
    em = mk(m)
    em.columns = [f"em_{b}" for b in BANDS]
    return e18, em


def load_geo(units: pd.Series) -> pd.DataFrame:
    f = pd.read_parquet(ROOT / "data/processed/splits_v1/unit_folds.parquet")
    f["unit_id"] = f.unit_id.astype(str)
    pts = f[["unit_id", "country", "lat", "lon"]]
    h = coordinate_harmonics(pts, list(units), L=8).set_index("unit_id")
    h.index = h.index.astype(str)
    return h, f.set_index("unit_id")[["s2_fold"]]


def load_statics() -> pd.DataFrame:
    out = []
    for c in COUNTRIES:
        cl = c.lower()
        rm = pd.read_parquet(ROOT / f"data/interim/remote_sensing/rs_monthly_{cl}_v1.parquet")
        rm = rm[rm.year.isin([2017, 2018])]
        a = rm.groupby("unit_id")[["ndvi_pw", "lst_day_pw", "lst_night_pw"]].mean()
        ry = pd.read_parquet(ROOT / f"data/interim/remote_sensing/rs_yearly_{cl}_v1.parquet")
        ry = ry[ry.year.isin([2017, 2018])]
        b = ry.groupby("unit_id")[["ntl_pw", "built_share"]].mean()
        b["ntl_pw"] = np.log1p(b.ntl_pw.clip(lower=0))
        b["built_share"] = np.log(b.built_share.clip(lower=0) + 1e-5)
        cw = pd.read_parquet(ROOT / f"data/interim/climate/climate_weekly_{cl}_v1.parquet",
                             columns=["unit_id", "week_start", "tmean", "tmin", "tmax", "precip", "rh"])
        yr = (pd.to_datetime(cw.week_start) + pd.Timedelta(days=3)).dt.year
        cw = cw[yr.isin([2017, 2018]).to_numpy()]
        cc = cw.groupby("unit_id")[["tmean", "tmin", "tmax", "precip", "rh"]].mean()
        cc["precip"] = np.log1p(cc.precip)
        s = a.join(b, how="outer").join(cc, how="outer")
        s.index = s.index.astype(str)
        out.append(s)
    s = pd.concat(out)
    pop = pd.read_parquet(ROOT / "data/interim/population/unit_population_yearly_v1.parquet")
    pop["unit_id"] = pop.unit_id.astype(str)
    s["log_pop"] = np.log(pop[pop.year == 2018].set_index("unit_id")["pop"].clip(lower=1))
    return s


# ----------------------------------------------------------------------------- models
def fit_predict(model, Xtr, ytr, Xte, threads, pca=0, seed=0):
    from sklearn.impute import SimpleImputer
    from sklearn.preprocessing import StandardScaler
    from sklearn.linear_model import RidgeCV
    from sklearn.decomposition import PCA
    import lightgbm as lgb
    imp = SimpleImputer(strategy="median").fit(Xtr)
    Xtr, Xte = imp.transform(Xtr), imp.transform(Xte)
    if pca:
        sc0 = StandardScaler(with_std=False).fit(Xtr)
        pc = PCA(n_components=pca, random_state=seed).fit(sc0.transform(Xtr))
        Xtr, Xte = pc.transform(sc0.transform(Xtr)), pc.transform(sc0.transform(Xte))
    if model == "ridge":
        sc = StandardScaler().fit(Xtr)
        r = RidgeCV(alphas=np.logspace(-3, 5, 33)).fit(sc.transform(Xtr), ytr)  # efficient LOO inner CV
        return r.predict(sc.transform(Xte))
    m = lgb.LGBMRegressor(num_leaves=31, n_estimators=200, learning_rate=0.05, feature_fraction=0.8,
                          min_child_samples=min(20, max(5, len(ytr) // 20)), n_jobs=threads,
                          random_state=seed, verbose=-1)
    m.fit(Xtr, ytr)
    return m.predict(Xte)


def fast_rho(y, p):
    from scipy.stats import rankdata
    return np.corrcoef(rankdata(y), rankdata(p))[0, 1]


def r2(y, p):
    return 1 - np.sum((y - p) ** 2) / np.sum((y - y.mean()) ** 2)


def boot_idx(groups, B, rng):
    """State-cluster bootstrap: list of row-index arrays."""
    ug, inv = np.unique(groups, return_inverse=True)
    members = [np.flatnonzero(inv == k) for k in range(len(ug))]
    out = []
    for _ in range(B):
        pick = rng.integers(0, len(ug), len(ug))
        out.append(np.concatenate([members[k] for k in pick]))
    return out


# ----------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--boot", type=int, default=1000)
    ap.add_argument("--threads", type=int, default=8)
    ap.add_argument("--replot", action="store_true", help="redraw the figure from the existing CSV only")
    a = ap.parse_args()
    if a.replot:
        make_figure(pd.read_csv(OUT_CSV, keep_default_na=False, na_values=[""]).assign(
            base=lambda d: d.base.fillna("")))
        return
    t0 = time.time()

    T = load_targets()
    e18, em = load_embeddings()
    geo, folds = load_geo(T.unit_id)
    S = load_statics()
    D = T.set_index("unit_id").join(e18).join(em).join(geo).join(S).join(folds)
    Ec = [f"e_{b}" for b in BANDS]
    Emc = [f"em_{b}" for b in BANDS]
    Gc = [c for c in geo.columns]
    Sc = list(S.columns)
    print(f"design: {len(D)} units; G {len(Gc)}, S {len(Sc)}, E {len(Ec)} cols", flush=True)
    FS = {
        "G": (Gc, 0), "S": (Sc, 0), "E": (Ec, 0), "E1718": (Emc, 0), "Epca8": (Ec, 8),
        "G+E": (Gc + Ec, 0), "S+E": (Sc + Ec, 0), "G+S": (Gc + Sc, 0), "G+S+E": (Gc + Sc + Ec, 0),
        "G+S+Epca8": None,  # special: PCA only on E block
    }
    rng0 = np.random.default_rng(20261119)

    # fold assignment per country
    # grouped-state folds: the S2 rule (pop.splits.group_adm1_folds) on each country's unit universe;
    # identical to the S2 fold map for Brazil and Colombia, same rule for Peru and Taiwan.
    from pop.splits.splits import group_adm1_folds
    uf = pd.read_parquet(ROOT / "data/processed/splits_v1/unit_folds.parquet")
    uf["unit_id"] = uf.unit_id.astype(str)
    smap = pd.concat([pd.Series(group_adm1_folds(g).to_numpy(), index=g.unit_id.to_numpy())
                      for _, g in uf.groupby("country")])

    def state_folds(df, c):
        f = df.unit_id.map(smap)
        assert f.notna().all(), c
        return f.astype(int).to_numpy()

    def run_cv(Xdf, y, fold, model, cols, pca, eblock_pca=False):
        pred = np.full(len(y), np.nan)
        for k in np.unique(fold):
            tr, te = fold != k, fold == k
            if eblock_pca:
                from sklearn.decomposition import PCA
                from sklearn.impute import SimpleImputer
                imp = SimpleImputer(strategy="median").fit(Xdf.loc[tr, Ec])
                Et, Ev = imp.transform(Xdf.loc[tr, Ec]), imp.transform(Xdf.loc[te, Ec])
                mu = Et.mean(0)
                pc = PCA(8, random_state=0).fit(Et - mu)
                Xtr = np.hstack([Xdf.loc[tr, Gc + Sc].to_numpy(float), pc.transform(Et - mu)])
                Xte = np.hstack([Xdf.loc[te, Gc + Sc].to_numpy(float), pc.transform(Ev - mu)])
                pred[te] = fit_predict(model, Xtr, y[tr], Xte, a.threads, 0)
            else:
                pred[te] = fit_predict(model, Xdf.loc[tr, cols].to_numpy(float), y[tr],
                                       Xdf.loc[te, cols].to_numpy(float), a.threads, pca)
        return pred

    preds = []  # (country, target, scheme, model, fset) -> oof pred with y, group
    for c in COUNTRIES:
        Dc = D[D.country == c].copy()
        for t in TARGETS:
            sub = Dc[Dc[t].notna()].copy()
            sub = sub.reset_index()
            y = sub[t].to_numpy(float)
            sf = state_folds(sub, c)
            rf = np.random.default_rng(7).permutation(len(sub)) % 5
            for scheme, fold in (("grouped_state", sf), ("random", rf)):
                for model in ("ridge", "lgbm"):
                    for fs, spec in FS.items():
                        if spec is None:
                            p = run_cv(sub, y, fold, model, None, 0, eblock_pca=True)
                        else:
                            p = run_cv(sub, y, fold, model, spec[0], spec[1])
                        preds.append(dict(country=c, target=t, scheme=scheme, model=model, fset=fs,
                                          unit_id=sub.unit_id.to_numpy(), y=y, p=p,
                                          group=sub.adm1.to_numpy()))
            print(f"  {c} {t} n={len(sub)} done  [{time.time()-t0:.0f}s]", flush=True)

    # leave-one-country-out on country-standardised targets
    for t in TARGETS:
        sub = D[D[t].notna()].reset_index()
        z = sub.groupby("country")[t].transform(lambda v: (v - v.mean()) / v.std()).to_numpy(float)
        fold = sub.country.map({c: i for i, c in enumerate(COUNTRIES)}).to_numpy()
        for model in ("ridge", "lgbm"):
            for fs, spec in FS.items():
                if spec is None:
                    p = run_cv(sub, z, fold, model, None, 0, eblock_pca=True)
                else:
                    p = run_cv(sub, z, fold, model, spec[0], spec[1])
                for c in COUNTRIES:
                    m = (sub.country == c).to_numpy()
                    preds.append(dict(country=c, target=t, scheme="loco", model=model, fset=fs,
                                      unit_id=sub.unit_id.to_numpy()[m], y=z[m], p=p[m],
                                      group=sub.adm1.to_numpy()[m]))
        print(f"  LOCO {t} done  [{time.time()-t0:.0f}s]", flush=True)

    # ------------------------------------------------------------- metrics + bootstrap
    idx = {(d["country"], d["target"], d["scheme"], d["model"], d["fset"]): d for d in preds}
    comps = [("E", "G"), ("E", "S"), ("E", "G+S")]
    rec = []
    bcache = {}
    for key, d in idx.items():
        c, t, sch, mod, fs = key
        y, p, g = d["y"], d["p"], d["group"]
        bk = (c, t, sch)
        if bk not in bcache:
            bcache[bk] = boot_idx(g, a.boot, np.random.default_rng(zlib.crc32("|".join(bk).encode())))
        bs = bcache[bk]
        r2b = np.array([r2(y[i], p[i]) for i in bs])
        rhob = np.array([fast_rho(y[i], p[i]) for i in bs])
        rec.append(dict(country=c, target=t, scheme=sch, model=mod, quantity="R2", fset=fs, base="",
                        estimate=r2(y, p), lo=np.nanpercentile(r2b, 2.5), hi=np.nanpercentile(r2b, 97.5),
                        n_units=len(y), n_states=len(np.unique(g))))
        rec.append(dict(country=c, target=t, scheme=sch, model=mod, quantity="spearman", fset=fs, base="",
                        estimate=spearmanr(y, p)[0], lo=np.nanpercentile(rhob, 2.5),
                        hi=np.nanpercentile(rhob, 97.5), n_units=len(y), n_states=len(np.unique(g))))
    for (c, t, sch, mod) in {k[:4] for k in idx}:
        bs = bcache[(c, t, sch)]
        for add, base in comps:
            full = base + "+E" if base != "G+S" else "G+S+E"
            A, B0 = idx[(c, t, sch, mod, full)], idx[(c, t, sch, mod, base)]
            y = A["y"]
            dlt = np.array([r2(y[i], A["p"][i]) - r2(y[i], B0["p"][i]) for i in bs])
            rec.append(dict(country=c, target=t, scheme=sch, model=mod, quantity="dR2", fset=full, base=base,
                            estimate=r2(y, A["p"]) - r2(y, B0["p"]), lo=np.nanpercentile(dlt, 2.5),
                            hi=np.nanpercentile(dlt, 97.5), n_units=len(y), n_states=len(np.unique(A["group"]))))
        # PCA-8 variant of E over G+S
        A, B0 = idx[(c, t, sch, mod, "G+S+Epca8")], idx[(c, t, sch, mod, "G+S")]
        y = A["y"]
        dlt = np.array([r2(y[i], A["p"][i]) - r2(y[i], B0["p"][i]) for i in bs])
        rec.append(dict(country=c, target=t, scheme=sch, model=mod, quantity="dR2", fset="G+S+Epca8", base="G+S",
                        estimate=r2(y, A["p"]) - r2(y, B0["p"]), lo=np.nanpercentile(dlt, 2.5),
                        hi=np.nanpercentile(dlt, 97.5), n_units=len(y), n_states=len(np.unique(A["group"]))))
    R = pd.DataFrame(rec).sort_values(["target", "scheme", "country", "model", "quantity", "fset"])
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    R.to_csv(OUT_CSV, index=False, float_format="%.5f")
    print(f"wrote {OUT_CSV} ({len(R)} rows) [{time.time()-t0:.0f}s]", flush=True)

    # best-model view: per (country, target, scheme, fset) take the model with higher point R2
    make_figure(R)
    make_md(R, D, time.time() - t0, a.boot)
    print(f"total {time.time()-t0:.0f}s", flush=True)


def best_model(R):
    r = R[R.quantity == "R2"]
    return r.loc[r.groupby(["country", "target", "scheme", "fset"]).estimate.idxmax()]


def make_figure(R):
    """Fig S4: LightGBM only, T1, grouped-state CV. Greys for the non-embedding sets,
    one accent for the sets that contain AlphaEarth; CIs clipped at the axis limits are
    drawn to the limit and marked with an arrowhead. No title inside the image."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    sets = ["G", "S", "G+S", "E", "G+S+E"]
    labels = {"G": "Coordinates (G)", "S": "Static covariates (S)", "G+S": "G + S",
              "E": "AlphaEarth embeddings (E)", "G+S+E": "G + S + E"}
    ACC = "#6a3d9a"  # accent (not used for any country in Figs 2-3)
    face = {"G": "#d4d3cd", "S": "#9c9b95", "G+S": "#5b5a55", "E": ACC, "G+S+E": "white"}
    edge = {"G": "#d4d3cd", "S": "#9c9b95", "G+S": "#5b5a55", "E": ACC, "G+S+E": ACC}
    hatch = {"G+S+E": "////"}
    YLO, YHI = -0.5, 1.0
    plt.rcParams.update({"font.family": "DejaVu Sans", "hatch.color": ACC, "hatch.linewidth": 0.6})
    r = R[(R.quantity == "R2") & (R.target == "T1") & (R.scheme == "grouped_state") & (R.model == "lgbm")]
    fig, ax = plt.subplots(figsize=(7.2, 3.6), dpi=300)
    w = 0.16
    for j, s in enumerate(sets):
        q = r[r.fset == s].set_index("country").reindex(COUNTRIES)
        x = np.arange(4) + (j - 2) * w
        est = q.estimate.to_numpy(float)
        ax.bar(x, np.clip(est, YLO, YHI), w * 0.86, color=face[s], edgecolor=edge[s], lw=0.8,
               hatch=hatch.get(s), label=labels[s], zorder=2)
        for xi, e, lo, hi in zip(x, est, q.lo.to_numpy(float), q.hi.to_numpy(float)):
            lo_c, hi_c = max(lo, YLO), min(hi, YHI)
            ax.plot([xi, xi], [lo_c, hi_c], color="#2b2a27", lw=0.8, zorder=3)
            if lo < YLO:
                ax.plot(xi, YLO + 0.012, marker="v", ms=3.6, color="#2b2a27", zorder=4, clip_on=False)
            else:
                ax.plot([xi - 0.025, xi + 0.025], [lo, lo], color="#2b2a27", lw=0.8, zorder=3)
            if hi > YHI:
                ax.plot(xi, YHI - 0.012, marker="^", ms=3.6, color="#2b2a27", zorder=4, clip_on=False)
            else:
                ax.plot([xi - 0.025, xi + 0.025], [hi, hi], color="#2b2a27", lw=0.8, zorder=3)
    ax.axhline(0, color="#0b0b0b", lw=0.6, zorder=1)
    ax.set_ylim(YLO, YHI)
    ax.set_yticks(np.arange(-0.5, 1.01, 0.25))
    ax.yaxis.grid(True, color="#e1e0d9", lw=0.5, zorder=0)
    ax.set_axisbelow(True)
    ax.set_xticks(np.arange(4), [c.title() for c in COUNTRIES], fontsize=9)
    ax.set_ylabel("Out-of-fold $R^2$, held-out states", fontsize=9)
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(labelsize=8.5)
    h, l = ax.get_legend_handles_labels()
    fig.legend(h, l, fontsize=8, frameon=False, loc="lower center", ncol=5, bbox_to_anchor=(0.5, -0.01),
               handlelength=1.4, columnspacing=1.2)
    fig.tight_layout(rect=(0, 0.08, 1, 1))
    OUT_FIG.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT_FIG, dpi=300, bbox_inches="tight")
    fig.savefig(OUT_FIG.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)


def fmt(e, lo, hi, nd=2):
    return f"{e:+.{nd}f} [{lo:+.{nd}f}, {hi:+.{nd}f}]" if e < 0 or True else ""


def make_md(R, D, secs, B):
    L = ["# R3-E1 information probe: do AlphaEarth embeddings carry district dengue-burden information?", "",
         "Script: `scripts/analysis/info_probe.py`. Long-format results: `R3_E1_info_probe.csv`. "
         "Figure: `docs/results/figures/pub/FigS4_info_probe.png`.", "",
         "## Design", "",
         "- One row per district (no-geometry units dropped; exclusions_v2 applied to weeks: primary incomplete "
         "weeks and Espírito Santo from 2019-12-29, so ES units have no T2). Targets: "
         + "; ".join(f"**{k}** {v}" for k, v in TARGETS.items())
         + ". T1/T3/T4 need ≥104 pre-period weeks.",
         "- Features: **E** = AlphaEarth 2018 pop-weighted district mean, renormalised to unit length (64 dims); "
         "variants E1718 (mean of 2017–18) and Epca8 (PCA-8 fitted inside each training fold). "
         "**G** = representative-point lat/lon + real spherical harmonics L=8 (C2 features). "
         "**S** = 2017–18 means of NDVI, day/night LST, log night lights, log built share, tmean/tmin/tmax, "
         "log precip, RH, plus log population 2018.",
         "- Models: ridge (standardised, alpha by efficient leave-one-out inner CV over 1e-3..1e5) and LightGBM "
         "(31 leaves, 200 rounds, lr 0.05, feature_fraction 0.8).",
         "- CV: grouped by state into 5 folds with the S2 rule (`group_adm1_folds`; identical to the S2 folds "
         "for Brazil and Colombia), "
         "random 5-fold, and leave-one-country-out (LOCO) on within-country standardised targets "
         "(R² computed inside the held-out country).",
         f"- Out-of-fold R² and Spearman ρ; 95% CIs from {B} state-cluster bootstrap resamples of the OOF "
         "predictions (fold models not refitted, so CIs reflect evaluation-sample uncertainty only). "
         "ΔR² is paired on the same resamples.", ""]
    n = D.groupby("country").size()
    L.append("Units: " + ", ".join(f"{c.title()} {n.get(c, 0)}" for c in COUNTRIES) + ".")
    L.append("")
    bm = best_model(R)
    for t, desc in TARGETS.items():
        L += [f"## {t}: {desc}", "",
              "Out-of-fold R² [95% CI], grouped-state CV (ridge / LightGBM), and ΔR² of adding E.", "",
              "| Country | Model | G | S | E | G+S | G+S+E | ΔR² E over G | ΔR² E over S | ΔR² E over G+S | ΔR² Epca8 over G+S |",
              "|---|---|---|---|---|---|---|---|---|---|---|"]
        for c in COUNTRIES:
            for mod in ("ridge", "lgbm"):
                q = R[(R.target == t) & (R.scheme == "grouped_state") & (R.country == c) & (R.model == mod)]
                def g(fs, quant="R2", base=""):
                    x = q[(q.quantity == quant) & (q.fset == fs) & (q.base == base)]
                    if x.empty:
                        return "–"
                    x = x.iloc[0]
                    return f"{x.estimate:.2f}" if quant == "R2" else f"{x.estimate:+.3f} [{x.lo:+.3f}, {x.hi:+.3f}]"
                L.append(f"| {c.title()} | {mod} | {g('G')} | {g('S')} | {g('E')} | {g('G+S')} | {g('G+S+E')} | "
                         f"{g('G+E','dR2','G')} | {g('S+E','dR2','S')} | {g('G+S+E','dR2','G+S')} | "
                         f"{g('G+S+Epca8','dR2','G+S')} |")
        # random + LOCO short lines: E alone and dR2 over G+S (best model)
        L += ["", "Other CV schemes (best of ridge/LightGBM by point R²): R² of E alone; ΔR² of E over G+S (same model).", "",
              "| Country | random: E | random: ΔR² E/G+S | LOCO: E | LOCO: G+S | LOCO: ΔR² E/G+S |", "|---|---|---|---|---|---|"]
        for c in COUNTRIES:
            cells = []
            for sch in ("random", "loco"):
                b = bm[(bm.target == t) & (bm.scheme == sch) & (bm.country == c)].set_index("fset")
                mE = b.loc["E"]
                cells.append(f"{mE.estimate:.2f} ({mE.model})")
                if sch == "loco":
                    cells.append(f"{b.loc['G+S'].estimate:.2f}")
                d = R[(R.target == t) & (R.scheme == sch) & (R.country == c) & (R.quantity == "dR2")
                      & (R.fset == "G+S+E") & (R.model == b.loc["G+S+E"].model)].iloc[0]
                cells.append(f"{d.estimate:+.3f} [{d.lo:+.3f}, {d.hi:+.3f}]")
            L.append(f"| {c.title()} | " + " | ".join(cells) + " |")
        L.append("")
    L += ["## Interpretation", "", "[[INTERPRETATION]]", "", f"Runtime: {secs/60:.1f} min (nice 19, ≤8 threads)."]
    OUT_MD.write_text("\n".join(L) + "\n")


if __name__ == "__main__":
    main()
