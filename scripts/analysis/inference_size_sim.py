#!/usr/bin/env python
"""Size / coverage / power study of the primary inference under realistic dependence (review C8).

The primary test (policy row 11) is a Diebold-Mariano test on the weekly series
d_t = mean over units (pooled over horizons 1 and 4 within week) of the per-row WIS difference,
with the EWC long-run variance (B = floor(0.4 T^(2/3)), t_B reference) and the HLN factor at
h = 4 (``pop.eval.stats.ewc_inference``). This script asks whether that test has the right size
and its 95% CI the right coverage for series that look like OUR d_t, and compares it with
alternatives. All tests are the library functions (``pop.eval.stats``), imported, not re-coded.

Subcommands
  extract   rows of every available primary cell via estimands_report.load_cell (same
            exclusions as the results kit), restricted to the primary horizons {1, 4};
            weekly series d_t (G_excess, G_emb, G_id), weekly WIS(L3); seed-vs-seed placebo
            series (Brazil S1 seeds 0/1/2; controls at the 2019 origin with 3 seeds).
            -> docs/results/review/RC_weekly_series.parquet, RC_cells.json
  simulate  null DGPs calibrated to each cell's centred G_excess series, R reps each:
              iaaft     windowed IAAFT surrogate (spectrum + marginal of the centred series)
              iaaft_lf2 same with 2x power below 2/T (low-frequency stress)
              arx       annual harmonics + AR(p) + resampled standardized residuals x the
                        real time-varying scale (outbreak heteroskedasticity, fixed timing)
              ar1       Gaussian AR(1) phi=.5, T=104 (the earlier benchmark)
            -> docs/results/review/RC_sim_<cell>.parquet (per-rep stats; for calibrated p)
  report    size, coverage, power, placebo rejections, real-cell p under each method,
            surrogate-calibrated p and Holm -> RC_size_table.csv, RC_real_cells.csv,
            RC_placebo.csv, RC_summary.md

Methods: ewc_hln (primary), ewc (no HLN), nw94 (Bartlett, NW94 lag, HLN, t_{T-1}),
hac_h1 (Bartlett lag h-1 = 3, HLN, t_{T-1}), cbb52 / cbb8 (circular block bootstrap of d_t
itself, i.e. the SAME week-weighted estimand, percentile 95% CI; 999 resamples per rep).
"""
from __future__ import annotations

import argparse
import json
import os
import zlib
import sys
from pathlib import Path

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_MAX_THREADS"):
    os.environ.setdefault(_v, "2")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(ROOT / "scripts" / "run"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy import stats as st  # noqa: E402

from pop.eval import stats as S  # noqa: E402
from pop.eval.estimands import infer_estimand, weekly_pooled  # noqa: E402

OUT = ROOT / "docs" / "results" / "review"
PRIMARY = ["BR_S1", "BR_S2", "BR_S3", "BR_S4", "BR_S5", "CO_S1", "CO_S2", "CO_S3", "CO_S4",
           "CO_S5", "PE_S1", "PE_S5", "TW_S1", "TW_S5"]
HP = [1, 4]
H_HLN = 4
METHODS = ["ewc_hln", "ewc", "ewc_hln_B8", "ewc_hln_B4", "nw94", "hac_h1", "season_t", "cbb52", "cbb8"]
EFFECTS = [0.005, 0.01]
N_BOOT = 999
ESTS = ("G_excess", "G_emb", "G_id")


# =============================================================== extract
def _patch_read_scores(ER):
    orig = ER.read_scores

    def rs(dirs, cols=("wis_log", "cases", "cov_40", "cov_80")):
        s = orig(dirs, cols=cols)
        return s[s.horizon.isin(HP)].reset_index(drop=True)
    ER.read_scores = rs


def extract(a):
    import rk_cells as C
    import estimands_report as ER
    _patch_read_scores(ER)
    excl = {"exclude_units": str(ER.DEFAULT_UNITS), "exclude_weeks": str(ER.DEFAULT_WEEKS),
            "late_entry": None, "week_actions": ("exclude",)}
    cells = {c["id"]: c for c in C.build_registry("configs/primary_cells.yaml")}
    series, meta = [], {}
    if (OUT / "RC_cells.json").exists():
        meta = json.loads((OUT / "RC_cells.json").read_text())
    if (OUT / "RC_weekly_series.parquet").exists():
        old = pd.read_parquet(OUT / "RC_weekly_series.parquet")
        series.append(old)
    ids = a.cells or PRIMARY
    for cid in ids:
        c = cells[cid]
        stt, _ = C.cell_status(c)
        if stt != "available":
            print(cid, stt, flush=True)
            continue
        if series:
            series = [s[s.cell != cid] for s in series]
        ndir = len(c["roles"]["L3"]["dirs"])
        if ndir == 1:
            roles = {r: c["roles"][r]["dirs"] for r in C.ROLES}
            g, info = ER.load_cell(roles, panel=c.get("panel"), **excl)
            rec = {"rows": int(len(g)), "seeds": [int(x) for x in g.attrs["seeds"]],
                   "units": int(g.unit_id.nunique())}
            for e in ESTS:
                _add(series, cid, e, weekly_pooled(g, e))
                rec[e] = _inf(g, e)
            _add(series, cid, "wis_L3", weekly_pooled(g, "wis_L3"))
            del g
        else:
            # several seed runs per role (Brazil S1, row 22): load ONE seed at a time (memory);
            # d_t = mean over seeds of the per-seed weekly series. This equals the kit's
            # common-seed estimator when every seed has the same rows (asserted per (h, week)).
            per, counts = {}, None
            for i in range(ndir):
                roles = {r: [c["roles"][r]["dirs"][i]] for r in C.ROLES}
                g, info = ER.load_cell(roles, panel=c.get("panel"), **excl)
                sd = int(g.attrs["seeds"][0])
                assert len(g.attrs["seeds"]) == 1, g.attrs["seeds"]
                cnt = g.groupby(["horizon", "target_week"]).size()
                if counts is None:
                    counts = cnt
                else:
                    assert cnt.equals(counts), f"seed {sd}: rows differ from seed 0"
                L3 = g["wis_L3"]
                g["L3"], g["L4"] = L3, L3 - g["G_emb"]
                g["L3C"] = L3 - g["G_id"]
                g["L4C"] = g["L3C"] - g["G_excess"]
                per[sd] = {k: weekly_pooled(g, k) for k in ESTS + ("wis_L3", "L3", "L4", "L3C", "L4C")}
                rows = int(len(g))
                del g
            seeds = sorted(per)
            rec = {"rows": rows, "seeds": seeds, "rows_per_seed_equal": True}
            avg = {k: sum(per[s][k] for s in seeds) / len(seeds) for k in per[seeds[0]]}
            for e in ESTS:
                _add(series, cid, e, avg[e])
                inf = S.ewc_inference(avg[e].to_numpy(), h=H_HLN)
                wis = float(avg["wis_L3"].mean())
                rec[e] = {"estimate": inf.estimate, "se": inf.se, "df": inf.df, "T": inf.T,
                          "p": inf.p, "lo95": inf.lo95, "hi95": inf.hi95, "wis_ref": wis,
                          "pct_of_ref": 100 * inf.estimate / wis, "mde_pct": 100 * inf.mde / wis}
            _add(series, cid, "wis_L3", avg["wis_L3"])
            for i in range(len(seeds)):
                for j in range(i + 1, len(seeds)):
                    x, y = seeds[i], seeds[j]
                    for k in ("L3", "L4", "L3C", "L4C") + ESTS:
                        _add(series, cid, f"placebo:{k}:s{x}-s{y}", per[x][k] - per[y][k])
        rec["T"] = int(rec["G_excess"]["T"])
        kc = ROOT / "runs" / "analysis_cache" / cid / "est.parquet"
        if kc.exists():
            k = pd.read_parquet(kc)
            k = k[(k.horizon == "pooled") & (k.test_year == "pooled") & (k.stratum == "all")
                  & (k.estimand == "G_excess")]
            if len(k):
                rec["kit_estimate"] = float(k.estimate.iloc[0])
                rec["kit_p"] = float(k.p.iloc[0])
        meta[cid] = rec
        print(cid, json.dumps({k: rec[k] for k in ("T", "rows", "seeds")}),
              "G_excess", rec["G_excess"]["estimate"], "kit", rec.get("kit_estimate"), flush=True)
    # controls at the 2019 origin with 3 seeds (C3, C4, C4s): placebo seed pairs, T = 52
    if not a.cells:
        for country in ("brazil", "colombia", "peru", "taiwan"):
            f = ROOT / "runs" / f"{country}_s1_shared_controls_2019" / "scores.parquet"
            if not f.exists():
                continue
            sc = pd.read_parquet(f, columns=["run", "seed", "unit_id", "origin_week", "target_week",
                                              "horizon", "wis_log"],
                                 filters=[("horizon", "in", HP),
                                          ("run", "in", ["lgbm-L3+C3", "lgbm-L3+C4", "lgbm-L3+C4s"])])
            for run, grp in sc.groupby("run"):
                sd = sorted(grp.seed.unique())
                if len(sd) < 2:
                    continue
                wide = grp.pivot_table(index=["unit_id", "origin_week", "target_week", "horizon"],
                                       columns="seed", values="wis_log", aggfunc="first").dropna()
                wide = wide.reset_index()
                for i in range(len(sd)):
                    for j in range(i + 1, len(sd)):
                        wide["_d"] = wide[sd[i]] - wide[sd[j]]
                        _add_placebo(series, f"ctrl2019_{country[:2].upper()}",
                                     f"placebo:{run.replace('lgbm-', '')}:s{sd[i]}-s{sd[j]}", wide)
            print("controls", country, flush=True)
    out = pd.concat(series, ignore_index=True).drop_duplicates(["cell", "series", "target_week"])
    OUT.mkdir(parents=True, exist_ok=True)
    out.to_parquet(OUT / "RC_weekly_series.parquet", index=False)
    (OUT / "RC_cells.json").write_text(json.dumps(meta, indent=1, default=str))


def _add(series, cid, name, d):
    series.append(pd.DataFrame({"cell": cid, "series": name, "target_week": d.index,
                                "value": d.to_numpy()}))


def _inf(g, e):
    inf = infer_estimand(g, e)
    return {k: inf[k] for k in ("estimate", "se", "df", "T", "p", "lo95", "hi95", "wis_ref",
                                "pct_of_ref", "cls", "mde_pct")}


def _add_placebo(series, cid, name, sub):
    d = weekly_pooled(sub, "_d")
    series.append(pd.DataFrame({"cell": cid, "series": name, "target_week": d.index,
                                "value": d.to_numpy()}))


# =============================================================== tests on one series
def run_methods(d: np.ndarray, rng, n_boot=N_BOOT) -> dict:
    """Per method: estimate, effective se (None for bootstrap), critical value, CI and stat.
    Everything that power needs: for DM methods the test of mean = -delta is
    |dbar + delta| / se_eff > crit; for the bootstrap the percentile CI shifts by delta."""
    T = d.size
    dbar = float(d.mean())
    out = {}
    r = S.dm_test(d, h=H_HLN, lag="ewc")
    out["ewc_hln"] = (dbar, r.se / r.hln_factor, st.t.ppf(0.975, r.df))
    var, B = S.ewc_var(d)
    out["ewc"] = (dbar, np.sqrt(var / T), st.t.ppf(0.975, B))
    f = S.hln_factor(T, H_HLN)
    for Bk in (8, 4):    # fewer cosine terms: robust to a non-flat spectrum near 0, wider t_B
        vb, _ = S.ewc_var(d, B=Bk)
        out[f"ewc_hln_B{Bk}"] = (dbar, np.sqrt(vb / T) / f, st.t.ppf(0.975, Bk))
    # between-season reference: consecutive 52-week blocks (a last block < 26 weeks merged),
    # t-test over the block means with n_blocks - 1 df (generalizes to new seasons)
    if T >= 104:
        nb = T // 52
        blk = np.minimum(np.arange(T) // 52, nb - 1)
        bm = np.bincount(blk, weights=d) / np.bincount(blk)
        out["season_t"] = (float(bm.mean()), float(bm.std(ddof=1) / np.sqrt(nb)), st.t.ppf(0.975, nb - 1))
    else:   # fewer than 2 seasons: not defined
        out["season_t"] = (dbar, np.nan, np.nan)
    r = S.dm_test(d, h=H_HLN, lag="nw")
    out["nw94"] = (dbar, r.se / r.hln_factor, st.t.ppf(0.975, r.df))
    r = S.dm_test(d, h=H_HLN, lag="h-1")
    out["hac_h1"] = (dbar, r.se / r.hln_factor, st.t.ppf(0.975, r.df))
    res = {}
    for m, (est, se, crit) in out.items():
        res[m] = {"est": est, "se": se, "crit": crit, "lo": est - crit * se, "hi": est + crit * se,
                  "t": est / se if se > 0 else np.nan}
    for m, b in (("cbb52", 52), ("cbb8", 8)):
        idx = S._block_idx(T, b, rng, size=(n_boot,))
        reps = d[idx].mean(axis=1)
        lo, hi = S.percentile_ci(reps)
        res[m] = {"est": dbar, "se": float(reps.std(ddof=1)), "crit": np.nan, "lo": lo, "hi": hi,
                  "t": np.nan}
    return res


def _check_against_library(d):
    """The CI of ewc_hln must equal ewc_inference's CI exactly."""
    inf = S.ewc_inference(d, h=H_HLN)
    r = run_methods(d, np.random.default_rng(0), n_boot=50)["ewc_hln"]
    assert np.isclose(r["lo"], inf.lo95) and np.isclose(r["hi"], inf.hi95), (r, inf)


# =============================================================== DGPs
def _smoothed_periodogram(x):
    T = x.size
    I = np.abs(np.fft.rfft(x)) ** 2 / T          # j = 0..T//2
    Ij = I[1:]
    pad = np.r_[Ij[0], Ij, Ij[-1]]
    Sj = (pad[:-2] + pad[1:-1] + pad[2:]) / 3       # Daniell span 3
    f = np.arange(1, Ij.size + 1) / T
    return f, Sj


class IAAFT:
    """Windowed IAAFT: a circular surrogate of length M = k*T whose amplitude spectrum is the
    span-3 smoothed periodogram of the centred real series (interpolated; flat below 1/T) and
    whose marginal is the real marginal (quantile-expanded, mean exactly 0); a random window of
    length T is returned. (A length-T IAAFT reproduces the sample mean exactly, so it cannot
    be used for size; windows of a longer surrogate have a non-degenerate mean whose variance
    comes from the low-frequency power of the real series.)"""

    def __init__(self, x, k=8, lf_mult=1.0, n_iter=40):
        x = np.asarray(x, float) - np.mean(x)
        self.T = T = x.size
        self.M = M = k * T
        f, Sj = _smoothed_periodogram(x)
        fl = np.arange(M // 2 + 1) / M
        Sl = np.interp(fl, f, Sj, left=Sj[0], right=Sj[-1])
        if lf_mult != 1.0:
            Sl[fl < 2.0 / T] *= lf_mult
        self.amp = np.sqrt(Sl * M)
        q = np.quantile(x, (np.arange(M) + 0.5) / M)
        self.sorted = np.sort(q - q.mean())
        self.n_iter = n_iter

    def draw(self, rng):
        s = rng.permutation(self.sorted)
        for _ in range(self.n_iter):
            X = np.fft.rfft(s)
            s = np.fft.irfft(self.amp * np.exp(1j * np.angle(X)), n=self.M)
            s = self.sorted[np.argsort(np.argsort(s))]
        start = rng.integers(0, self.M)
        return s[(start + np.arange(self.T)) % self.M]


class ARX:
    """d_t = s_t + u_t: s_t = 2 annual harmonics (fitted, de-meaned over the sample, held fixed);
    u_t = AR(p) (p <= 8 by AIC, OLS) driven by sigma_t * z_t, sigma_t = the real residuals'
    centred 13-week RMS (outbreak-period volatility at its real timing), z_t resampled i.i.d.
    from the real standardized residuals (heavy tails). True mean of d_t is 0."""

    def __init__(self, x, pmax=8):
        x = np.asarray(x, float) - np.mean(x)
        T = self.T = x.size
        t = np.arange(T)
        Xh = np.column_stack([f(2 * np.pi * k * t / 52.1775) for k in (1, 2) for f in (np.sin, np.cos)])
        beta, *_ = np.linalg.lstsq(Xh, x, rcond=None)
        s = Xh @ beta
        self.s = s - s.mean()
        u = x - Xh @ beta
        best = None
        for p in range(1, pmax + 1):
            Y = u[p:]
            Z = np.column_stack([u[p - i:T - i] for i in range(1, p + 1)])
            ph, *_ = np.linalg.lstsq(Z, Y, rcond=None)
            e = Y - Z @ ph
            aic = (T - p) * np.log(e @ e / (T - p)) + 2 * p
            if best is None or aic < best[0]:
                best = (aic, p, ph, e)
        _, self.p, self.phi, e = best
        roots = np.abs(np.roots(np.r_[1, -self.phi]))
        if roots.size and roots.max() >= 0.99:          # keep stationary
            self.phi = self.phi * 0.98 / roots.max() ** self.p
        rms = pd.Series(e).pow(2).rolling(13, center=True, min_periods=4).mean().pow(0.5).to_numpy()
        rms = np.maximum(rms, 0.2 * np.nanmedian(rms))
        self.sig = np.r_[np.full(self.p, rms[0]), rms]
        z = e / rms
        self.z = (z - z.mean()) / z.std()
        self.sig_burn = float(np.median(rms))
        self.harm_share = float(np.var(self.s) / np.var(x))

    def draw(self, rng, burn=200):
        p, T = self.p, self.T
        n = burn + T
        sig = np.r_[np.full(burn, self.sig_burn), self.sig]
        eps = sig * rng.choice(self.z, size=n)
        u = np.zeros(n)
        for i in range(p, n):
            u[i] = self.phi @ u[i - p:i][::-1] + eps[i]
        return self.s + u[burn:]


class AR1:
    def __init__(self, T=104, phi=0.5):
        self.T, self.phi = T, phi

    def draw(self, rng, burn=100):
        e = rng.standard_normal(self.T + burn)
        u = np.zeros_like(e)
        for i in range(1, e.size):
            u[i] = self.phi * u[i - 1] + e[i]
        return u[burn:]


# =============================================================== simulate
def simulate(a):
    ser = pd.read_parquet(OUT / "RC_weekly_series.parquet")
    meta = json.loads((OUT / "RC_cells.json").read_text())
    jobs = []
    for cid in (a.cells or [c for c in PRIMARY if c in meta] + ["AR1_T104"]):
        if cid == "AR1_T104":
            jobs.append((cid, {"ar1": AR1()}))
            continue
        x = ser[(ser.cell == cid) & (ser.series == "G_excess")].sort_values("target_week").value.to_numpy()
        _check_against_library(x)
        jobs.append((cid, {"iaaft": IAAFT(x), "iaaft_lf2": IAAFT(x, lf_mult=2.0), "arx": ARX(x)}))
    for cid, dgps in jobs:
        rows = []
        for k, (name, g) in enumerate(dgps.items()):
            rng = np.random.default_rng([a.seed, zlib.crc32(cid.encode()), k])
            for rep in range(a.reps):
                d = g.draw(rng)
                res = run_methods(d, rng)
                for m, v in res.items():
                    rows.append((cid, name, rep, m, v["est"], v["se"], v["crit"], v["lo"], v["hi"], v["t"]))
            extra = f" p={g.p} harm_share={g.harm_share:.2f}" if isinstance(g, ARX) else ""
            print(cid, name, "done", extra, flush=True)
        df = pd.DataFrame(rows, columns=["cell", "dgp", "rep", "method", "est", "se", "crit", "lo", "hi", "t"])
        df.to_parquet(OUT / f"RC_sim_{cid}.parquet", index=False)


# =============================================================== report
def _wilson(k, n):
    if n == 0:
        return (np.nan, np.nan)
    z = 1.96
    ph = k / n
    c = (ph + z * z / (2 * n)) / (1 + z * z / n)
    w = z * np.sqrt(ph * (1 - ph) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return c - w, c + w


def report(a):
    meta = json.loads((OUT / "RC_cells.json").read_text())
    ser = pd.read_parquet(OUT / "RC_weekly_series.parquet")
    sims = pd.concat([pd.read_parquet(f) for f in sorted(OUT.glob("RC_sim_*.parquet"))], ignore_index=True)
    rows = []
    for (cid, dgp, m), g in sims.groupby(["cell", "dgp", "method"], sort=False):
        R = len(g)
        rej = ((g.lo > 0) | (g.hi < 0)).to_numpy()
        lo, hi = _wilson(rej.sum(), R)
        rec = {"cell": cid, "dgp": dgp, "method": m, "T": int(meta.get(cid, {}).get("T") or
                                                              (104 if cid == "AR1_T104" else 0)),
               "reps": R, "size": rej.mean(), "size_lo95": lo, "size_hi95": hi,
               "coverage95": 1 - rej.mean(),
               "mean_ci_halfwidth": float(((g.hi - g.lo) / 2).mean())}
        wis = meta.get(cid, {}).get("G_excess", {}).get("wis_ref")
        for eff in EFFECTS:
            if wis:
                dl = eff * wis
                pw = ((g.lo + dl > 0) | (g.hi + dl < 0)).mean()
            else:
                pw = np.nan
            rec[f"power_{eff * 100:g}pct"] = pw
        rows.append(rec)
    tab = pd.DataFrame(rows)
    tab.to_csv(OUT / "RC_size_table.csv", index=False, float_format="%.4f")

    # real cells: p / CI under every method + surrogate-calibrated p of the primary statistic
    real = []
    for cid, rec in meta.items():
        x = ser[(ser.cell == cid) & (ser.series == "G_excess")].sort_values("target_week").value.to_numpy()
        res = run_methods(x, np.random.default_rng(1), n_boot=9999)
        wis = rec["G_excess"]["wis_ref"]
        r = {"cell": cid, "T": x.size, "estimate_pct": 100 * x.mean() / wis,
             "primary_p": rec["G_excess"]["p"], "kit_estimate": rec.get("kit_estimate"),
             "series_mean": x.mean()}
        for m, v in res.items():
            r[f"{m}_lo_pct"] = 100 * v["lo"] / wis
            r[f"{m}_hi_pct"] = 100 * v["hi"] / wis
            if np.isfinite(v["t"]):
                r[f"{m}_p"] = 2 * st.t.sf(abs(v["t"]), df=_df(m, x.size))
            r[f"{m}_excl0"] = bool(v["lo"] > 0 or v["hi"] < 0)
            if m.startswith("ewc_hln") and np.isfinite(v["se"]):
                dfm = _df(m, x.size)
                h90 = st.t.ppf(0.95, dfm) * v["se"]
                r[f"{m}_cls"] = S.classify_effect(v["lo"], v["hi"], v["est"] - h90, v["est"] + h90,
                                                  r.get(f"{m}_p", 1.0), 0.01 * wis)
        tobs = abs(res["ewc_hln"]["t"])
        sc = sims[(sims.cell == cid) & (sims.method == "ewc_hln")]
        for dgp, g in sc.groupby("dgp"):
            r[f"pcal_{dgp}"] = (1 + (g.t.abs() >= tobs).sum()) / (1 + len(g))
        real.append(r)
    real = pd.DataFrame(real)
    fam = real[real.cell.isin(PRIMARY)].copy()
    for col in ["ewc_hln_p", "ewc_hln_B8_p", "ewc_hln_B4_p", "season_t_p", "nw94_p", "pcal_iaaft", "pcal_iaaft_lf2", "pcal_arx"]:
        if col in fam:
            fam[f"holm_{col}"] = S.holm(fam[col].to_numpy())
    fam.to_csv(OUT / "RC_real_cells.csv", index=False, float_format="%.5g")

    # placebo
    pl = []
    for (cid, name), g in ser[ser.series.str.startswith("placebo:")].groupby(["cell", "series"]):
        x = g.sort_values("target_week").value.to_numpy()
        res = run_methods(x, np.random.default_rng(2), n_boot=1999)
        r = {"cell": cid, "series": name, "T": x.size, "mean": x.mean()}
        for m, v in res.items():
            ok = np.isfinite(v["lo"]) and np.isfinite(v["hi"]) and not (m == "cbb52" and x.size < 104)
            r[f"rej_{m}"] = (bool(v["lo"] > 0 or v["hi"] < 0)) if ok else np.nan
        pl.append(r)
    pl = pd.DataFrame(pl)
    pl.to_csv(OUT / "RC_placebo.csv", index=False, float_format="%.5g")
    print(tab.pivot_table(index=["cell", "dgp"], columns="method", values="size").round(3).to_string())
    print(fam.round(4).to_string())
    print(pl.groupby(pl.cell.str.startswith("ctrl"))[[f"rej_{m}" for m in METHODS]].agg(["sum", "count"]).to_string())
    print(fam[["cell"] + [c for c in fam if c.endswith("_cls")]].to_string())


def _df(m, T):
    if m.startswith("ewc_hln_B"):
        return int(m[len("ewc_hln_B"):])
    if m in ("ewc_hln", "ewc"):
        return S.ewc_n_terms(T)
    if m == "season_t":
        return max(T // 52, 2) - 1
    return T - 1


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["extract", "simulate", "report"])
    ap.add_argument("--cells", nargs="*")
    ap.add_argument("--reps", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=20261118)
    a = ap.parse_args(argv)
    os.chdir(ROOT)
    {"extract": extract, "simulate": simulate, "report": report}[a.cmd](a)


if __name__ == "__main__":
    main()
