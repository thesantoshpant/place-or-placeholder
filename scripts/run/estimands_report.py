#!/usr/bin/env python
"""Paper-1 estimands (G_emb, G_id, G_excess, ID share) for one country x split.

Usage:
    python scripts/run/estimands_report.py --l3 runs/brazil_s1_L3 --l4 runs/brazil_s1_L4 \
        --l3c runs/brazil_s1_L3_Cstar --l4c runs/brazil_s1_L4_Cstar \
        [--ladder runs/brazil_s1_baselines runs/brazil_s1_timesfm_zs runs/brazil_s1_L2 ...] \
        [--pairs lgbm-L3:lgbm-L2 ...] [--out runs/brazil_s1_analysis] [--prefix estimands]
        [--n-boot 2000] [--block-len 8] [--seed 0]

Definitions (positive = lower log-WIS for the second model, i.e. an improvement):
  G_emb = WIS(L3) - WIS(L4); G_id = WIS(L3) - WIS(L3+C*); G_excess = WIS(L3+C*) - WIS(L4+C*).
  ID share = G_id / G_emb, only if the 95% CI of G_emb excludes 0 and G_emb >= 1% of WIS(L3)
  (pop.eval.estimands.compute_estimands).

Inference (library code only):
  - CIs: pop.eval.stats.block_bootstrap_means: each replicate resamples states (adm1) with
    replacement and, shared across states, circular 8-week blocks of target weeks; row-level
    means of the per-row gains; percentile 95% CI; all estimands from the same replicates.
  - DM: pop.eval.stats.dm_test on the per-target-week mean of the per-row gain (= mean WIS
    difference), EWC long-run variance (B = floor(0.4 T^(2/3)), t_B reference) x HLN factor.
    Holm across the 4 horizons, separately for each estimand (and each extra pair).

Rows: all runs are restricted to the common (test_year, unit_id, origin_week, target_week,
horizon) keys with non-NaN log-WIS; flag_gap target weeks are dropped. The row-set check is
written to <prefix>_rowcheck.csv and must show zero mismatches for the estimand runs.
Outbreak week: target cases >= max(unit p90 of weekly cases over 2013-2019, 5) (panel weeks,
flag_gap excluded). Strata use the panel's zero_filled flag.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_MAX_THREADS"):
    os.environ.setdefault(_v, "8")

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyze_run import load_run, md  # noqa: E402

from pop.eval.estimands import compute_estimands, gain_frame  # noqa: E402
from pop.eval.stats import dm_test, holm, loss_diff_series  # noqa: E402

KEYS = ["test_year", "unit_id", "origin_week", "target_week", "horizon"]
EST = ["G_emb", "G_id", "G_excess"]


def run_label(d: Path) -> str:
    return str(load_run(d).model.iloc[0])


def chunk_rows(d: Path) -> int | None:
    ch = sorted((d / "chunks").glob("*.scores.parquet")) if (d / "chunks").exists() else []
    return sum(pq.ParquetFile(c).metadata.num_rows for c in ch) if ch else None


def load_panel(panel: str, country: str | None) -> pd.DataFrame:
    cols = ["unit_id", "country", "adm1", "week_start", "year", "cases", "zero_filled", "flag_gap"]
    p = pd.read_parquet(panel, columns=cols)
    if country:
        p = p[p.country == country]
    p = p.drop(columns="country")
    p["unit_id"] = p.unit_id.astype(str)
    p["week_start"] = pd.to_datetime(p.week_start)
    return p


def outbreak_threshold(p: pd.DataFrame) -> pd.Series:
    base = p[(p.year >= 2013) & (p.year <= 2019) & ~p.flag_gap.fillna(False).astype(bool)]
    q = base.groupby("unit_id").cases.quantile(0.9)
    return np.maximum(q, 5.0)


def est_rows(g: pd.DataFrame, label: dict, kw: dict) -> list[dict]:
    r = compute_estimands(g, **kw)
    out = []
    w = r["WIS_L3"]["estimate"]
    for k in EST + ["WIS_L3", "ID_share"]:
        e = r[k]
        row = {**label, "estimand": k, "estimate": e["estimate"], "lo": e["lo"], "hi": e["hi"],
               "pct_of_wis_l3": 100 * e["estimate"] / w if k in EST else np.nan,
               "n_rows": len(g), "n_weeks": g.target_week.nunique()}
        if k == "ID_share":
            row["reason"] = e["reason"]
        out.append(row)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    for r in ("l3", "l4", "l3c", "l4c"):
        ap.add_argument(f"--{r}", required=True)
    ap.add_argument("--ladder", nargs="*", default=[], help="extra run dirs for the ladder table")
    ap.add_argument("--pairs", nargs="*", default=[], metavar="A:B",
                    help="extra DM pairs (labels) on the ladder rows; d = WIS(A) - WIS(B)")
    ap.add_argument("--out", default=None)
    ap.add_argument("--prefix", default="estimands")
    ap.add_argument("--panel", default=None)
    ap.add_argument("--country", default=None)
    ap.add_argument("--n-boot", type=int, default=2000)
    ap.add_argument("--block-len", type=int, default=8)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()

    roles = {"L3": Path(a.l3), "L4": Path(a.l4), "L3C": Path(a.l3c), "L4C": Path(a.l4c)}
    ladder = [Path(x) for x in a.ladder]
    out = Path(a.out) if a.out else roles["L3"].parent / (roles["L3"].name + "_analysis")
    out.mkdir(parents=True, exist_ok=True)
    pre = out / a.prefix
    cfg = yaml.safe_load((roles["L3"] / "config_resolved.yaml").read_text())
    panel = load_panel(a.panel or cfg["panel"], a.country or cfg.get("country"))
    lines: list[str] = []

    def emit(title, body):
        print(f"\n## {title}\n{body}", flush=True)
        lines.extend([f"## {title}", "", body, ""])

    # ---------------------------------------------------------------- load + row check
    dirs = list(roles.values()) + [d for d in ladder if d not in roles.values()]
    frames, rc = [], []
    for d in dirs:
        s = load_run(d)
        for m, sm in s.groupby("model", sort=False):
            dup = int(sm.duplicated(KEYS).sum())
            rc.append({"run": d.name, "model": m, "rows": len(sm), "dup_keys": dup,
                       "nan_wis_log": int(sm.wis_log.isna().sum()),
                       "chunk_rows": chunk_rows(d) if s.model.nunique() == 1 else None})
        frames.append(s)
    sc = pd.concat(frames, ignore_index=True)
    lab = {r: run_label(d) for r, d in roles.items()}
    models = list(dict.fromkeys(sc.model))

    # per-test-year key-set comparison vs L3 (all models)
    ref = sc[sc.model == lab["L3"]]
    def hk(df):
        return np.unique(pd.util.hash_pandas_object(df[KEYS[1:]], index=False).to_numpy())
    refk = {y: hk(g) for y, g in ref.groupby("test_year")}
    yr = []
    for m in models:
        sm = sc[sc.model == m]
        for y, g in sm.groupby("test_year"):
            k = hk(g)
            r0 = refk.get(y, np.array([], dtype=np.uint64))
            yr.append({"model": m, "test_year": y, "rows": len(g),
                       "only_here": len(np.setdiff1d(k, r0, assume_unique=True)),
                       "only_in_L3": len(np.setdiff1d(r0, k, assume_unique=True))})
    yr = pd.DataFrame(yr)
    rc = pd.DataFrame(rc)
    rc.to_csv(f"{pre}_rowcheck_runs.csv", index=False)
    yr.to_csv(f"{pre}_rowcheck.csv", index=False)
    est_ok = yr[yr.model.isin(lab.values())][["only_here", "only_in_L3"]].to_numpy().sum() == 0
    all_ok = yr[["only_here", "only_in_L3"]].to_numpy().sum() == 0
    emit("Row-set check", md(rc, 0, index=False) + "\n\n"
         + md(yr.pivot_table(index="model", columns="test_year", values="rows").reindex(models), 0)
         + f"\n\nKey sets (unit, origin, target, horizon) identical to L3 per test year: "
           f"estimand runs {est_ok}; all runs {all_ok} (mismatch counts in {pre.name}_rowcheck.csv).")

    # ---------------------------------------------------------------- panel merge
    thr = outbreak_threshold(panel)
    pm = panel.rename(columns={"week_start": "target_week", "cases": "panel_cases",
                               "zero_filled": "zf_panel"})[
        ["unit_id", "target_week", "adm1", "panel_cases", "zf_panel", "flag_gap"]]
    sc = sc.merge(pm, on=["unit_id", "target_week"], how="left", validate="many_to_one")
    miss = int(sc.adm1.isna().sum())
    cmis = int((~np.isclose(sc.cases, sc.panel_cases)).sum())
    gap = sc.flag_gap.fillna(False).astype(bool)
    sc = sc[~gap & sc.wis_log.notna()]
    cnt = sc.groupby(KEYS, sort=False).model.transform("size")
    n_before = len(sc)
    sc = sc[cnt == len(models)].reset_index(drop=True)
    sc["state"] = sc.adm1.astype(str)
    sc["zero_filled"] = sc.zf_panel.fillna(False).astype(bool)
    sc["thr"] = sc.unit_id.map(thr).fillna(5.0)
    sc["outbreak"] = sc.cases >= sc.thr
    emit("Panel join", f"rows without panel match: {miss}; score cases != panel cases: {cmis}; "
         f"zero_filled taken from the panel; flag_gap rows dropped: {int(gap.sum())}; rows dropped "
         f"as not common to all {len(models)} models: {n_before - len(sc)}; states: "
         f"{sc.state.nunique()}; outbreak share of rows: {sc[sc.model == lab['L3']].outbreak.mean():.4f}")

    # ---------------------------------------------------------------- estimands
    g = gain_frame(sc[sc.model.isin(lab.values())], lab, metric="wis_log",
                   keys=KEYS[1:], extra_cols=["test_year", "state", "zero_filled", "outbreak"])
    kw = dict(cluster_col="state", time_col="target_week", block_len=a.block_len,
              n_boot=a.n_boot, seed=a.seed)
    rows = []
    for h, gh in g.groupby("horizon"):
        rows += est_rows(gh, {"horizon": h, "test_year": "pooled", "stratum": "all"}, kw)
    rows += est_rows(g, {"horizon": "pooled", "test_year": "pooled", "stratum": "all"}, kw)
    for y, gy in g.groupby("test_year"):
        rows += est_rows(gy, {"horizon": "pooled", "test_year": y, "stratum": "all"}, kw)
    E = pd.DataFrame(rows)

    # DM per horizon per estimand, Holm across horizons
    dm = []
    for h, gh in g.groupby("horizon"):
        for e in EST:
            d = gh.groupby("target_week")[e].mean().sort_index()
            r = dm_test(d.to_numpy(), h=int(h))
            dm.append({"horizon": h, "estimand": e, "mean_d": r.mean_d, "stat": r.stat, "df": r.df,
                       "p": r.p_value, "T": r.T})
    dm = pd.DataFrame(dm)
    dm["p_holm"] = dm.groupby("estimand").p.transform(lambda p: holm(p.to_numpy()))
    E = E.merge(dm[["horizon", "estimand", "stat", "p", "p_holm"]], on=["horizon", "estimand"],
                how="left")
    E.to_csv(f"{pre}_main.csv", index=False)
    dm.to_csv(f"{pre}_dm.csv", index=False)

    def tab(sub):
        t = sub[sub.estimand.isin(EST)].copy()
        t["CI95"] = t.apply(lambda r: f"[{r.lo:+.5f}, {r.hi:+.5f}]", axis=1)
        cols = ["estimand", "estimate", "CI95", "pct_of_wis_l3"] + \
               [c for c in ["p", "p_holm"] if c in t and t[c].notna().any()]
        return t, cols

    t, cols = tab(E[E.test_year.astype(str) == "pooled"])
    t = t.sort_values(["estimand", "horizon"], key=lambda s: s.astype(str))
    emit("Main estimands, pooled test years (log1p WIS; + = improvement)",
         md(t[["horizon"] + cols], 5, index=False)
         + "\n\nWIS(L3): " + ", ".join(f"h{r.horizon}={r.estimate:.5f}" for r in
                                      E[(E.estimand == "WIS_L3") & (E.test_year.astype(str) == "pooled")]
                                      .itertuples()))
    t, cols = tab(E[E.test_year.astype(str) != "pooled"])
    emit("Per test year (pooled over h)", md(t[["test_year"] + cols], 5, index=False))
    ids = E[E.estimand == "ID_share"][["horizon", "test_year", "estimate", "lo", "hi", "reason"]]
    emit("ID share rule", md(ids, 4, index=False))

    # ---------------------------------------------------------------- strata
    srows = []
    strata = {"observed": ~g.zero_filled, "zero_filled": g.zero_filled,
              "outbreak": g.outbreak, "non_outbreak": ~g.outbreak,
              "observed_non_outbreak": ~g.zero_filled & ~g.outbreak}
    for name, msk in strata.items():
        srows += est_rows(g[msk], {"horizon": "pooled", "test_year": "pooled", "stratum": name}, kw)
    last = int(g.test_year.max())
    gl = g[g.test_year == last]
    for name, msk in {"all": slice(None), "observed": ~gl.zero_filled, "zero_filled": gl.zero_filled,
                      "outbreak": gl.outbreak, "non_outbreak": ~gl.outbreak}.items():
        srows += est_rows(gl[msk], {"horizon": "pooled", "test_year": last, "stratum": name}, kw)
    for h, gh in gl.groupby("horizon"):
        srows += est_rows(gh, {"horizon": h, "test_year": last, "stratum": "all"}, kw)
    S = pd.DataFrame(srows)
    S.to_csv(f"{pre}_strata.csv", index=False)
    t, cols = tab(S)
    emit("Strata (pooled over h unless stated)",
         md(t[["test_year", "horizon", "stratum", "n_rows"] + cols], 5, index=False)
         + "\n\nWIS(L3) by stratum: " + ", ".join(
             f"{r.stratum}/{r.test_year}/h{r.horizon}={r.estimate:.4f}"
             for r in S[S.estimand == "WIS_L3"].itertuples()))
    # share of the total G (sum over rows) contributed by each stratum
    tot = g[EST].sum()
    shares = pd.DataFrame({n: g.loc[m, EST].sum() / tot for n, m in strata.items()}).T
    shares["row_share"] = [m.mean() for m in strata.values()]
    shares.to_csv(f"{pre}_strata_contrib.csv")
    emit("Share of the pooled total gain contributed by each stratum (sum of row gains / total)",
         md(shares, 3))

    # ---------------------------------------------------------------- ladder
    lad = sc.pivot_table(index="model", columns="horizon", values="wis_log", aggfunc="mean").reindex(models)
    lad["mean"] = lad.mean(axis=1)
    nz = sc.cases > 0
    lad["cov80_all"] = sc.groupby("model").cov_80.mean()
    lad["cov80_nonzero"] = sc[nz].groupby("model").cov_80.mean()
    lad["cov40_all"] = sc.groupby("model").cov_40.mean()
    lad["cov40_nonzero"] = sc[nz].groupby("model").cov_40.mean()
    lad.to_csv(f"{pre}_ladder.csv")
    emit("Ladder: mean log1p WIS by horizon (pooled test years) and coverage", md(lad, 4))

    pr = [tuple(p.split(":", 1)) for p in a.pairs]
    pr = [(x, y) for x, y in pr if x in models and y in models]
    if pr:
        dl = []
        for x, y in pr:
            for h in sorted(sc.horizon.unique()):
                d = loss_diff_series(sc[sc.horizon == h], x, y, metric="wis_log",
                                     keys=KEYS[1:])
                r = dm_test(d.to_numpy(), h=int(h))
                dl.append({"A": x, "B": y, "horizon": h, "mean_d": r.mean_d, "stat": r.stat,
                           "df": r.df, "p": r.p_value, "T": r.T})
        dl = pd.DataFrame(dl)
        dl["p_holm"] = dl.groupby(["A", "B"]).p.transform(lambda p: holm(p.to_numpy()))
        dl.to_csv(f"{pre}_ladder_dm.csv", index=False)
        emit("Ladder DM tests (d = WIS(A) - WIS(B); Holm across horizons within each pair)",
             md(dl, 5, index=False))

    (Path(f"{pre}_tables.md")).write_text(
        "# Estimands report\n\nRoles: " + ", ".join(f"{k}={v} ({roles[k]})" for k, v in lab.items())
        + f"\n\nBootstrap: {a.n_boot} reps, states x {a.block_len}-week circular blocks (shared "
          f"across states), seed {a.seed}.\n\n" + "\n".join(lines))
    print(f"\nwrote {pre}_*", flush=True)


if __name__ == "__main__":
    main()
