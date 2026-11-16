#!/usr/bin/env python
"""Pool the scores of one or more run directories and write the results tables.

Usage:
    python scripts/run/analyze_run.py --runs runs/brazil_s1_baselines runs/brazil_s1_timesfm_zs \
        [--out runs/brazil_s1_baselines/analysis] [--ref lgbm-L1] [--naive naive-L0]

Each run dir must hold scores.parquet (one row per forecast; wis_log, wis_case, cov_40, cov_80,
cases). Model label = ``run`` column if present, else ``model`` from summary.csv, else the dir
name. All models are restricted to the common (test_year, unit_id, origin_week, target_week,
horizon) keys with non-NaN log-WIS, so every model is scored on the same rows. Target weeks
flagged ``flag_gap`` in the panel are excluded; ``zero_filled`` comes from the panel.

Outputs (in --out): tables.md plus one CSV per table.
  a  mean log-WIS, model x horizon (pooled test years)
  b  mean log-WIS, model x test year at h=1 and h=4
  c  mean case-scale WIS, model x horizon
  d  40/80% coverage, all targets and non-zero targets (cases > 0)
  e  mean log-WIS by zero_filled target vs observed
  f  DM tests (EWC + HLN) per horizon on per-week mean log-WIS differences, Holm over all tests
  g  per-unit mean log-WIS, ref vs naive: share of units where ref is better, median difference
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from pop.eval.stats import dm_test, holm, loss_diff_series

KEYS = ["test_year", "unit_id", "origin_week", "target_week", "horizon"]
COLS = KEYS + ["cases", "wis_log", "wis_case", "cov_40", "cov_80"]


def load_run(d: Path) -> pd.DataFrame:
    sc = pd.read_parquet(d / "scores.parquet")
    if "run" in sc.columns:
        lab = sc["run"].astype(str)
    else:
        name = d.name
        sp = d / "summary.csv"
        if sp.exists():
            m = pd.read_csv(sp)
            if "model" in m.columns and m["model"].nunique() == 1:
                name = str(m["model"].iloc[0])
        lab = pd.Series(name, index=sc.index)
    sc = sc[COLS].copy()
    sc["model"] = lab.to_numpy()
    sc["test_year"] = sc.test_year.astype(int)
    sc["unit_id"] = sc.unit_id.astype(str)
    sc["origin_week"] = pd.to_datetime(sc.origin_week)
    sc["target_week"] = pd.to_datetime(sc.target_week)
    sc["horizon"] = sc.horizon.astype(int)
    return sc


def md(df: pd.DataFrame, nd: int = 4, index: bool = True) -> str:
    """Pipe-table markdown without the optional tabulate dependency."""
    df = df.copy()
    if index:
        names = [n if n is not None else "" for n in df.index.names]
        df = df.reset_index()
        df.columns = names + [str(c) for c in df.columns[len(names):]]
    def f(v):
        if isinstance(v, (float, np.floating)):
            return "" if np.isnan(v) else (f"{v:.{nd}f}" if abs(v) >= 10 ** -nd or v == 0 else f"{v:.2e}")
        return str(v)
    hdr = [" / ".join(map(str, c)) if isinstance(c, tuple) else str(c) for c in df.columns]
    out = ["| " + " | ".join(hdr) + " |", "|" + "---|" * len(hdr)]
    out += ["| " + " | ".join(f(v) for v in row) + " |" for row in df.itertuples(index=False)]
    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", nargs="+", required=True)
    ap.add_argument("--out", default=None)
    ap.add_argument("--ref", default="lgbm-L1")
    ap.add_argument("--naive", default="naive-L0")
    ap.add_argument("--panel", default=None, help="default: panel in first run's config_resolved.yaml")
    ap.add_argument("--country", default=None)
    a = ap.parse_args()
    runs = [Path(r) for r in a.runs]
    out = Path(a.out) if a.out else runs[0] / "analysis"
    out.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []

    def emit(title: str, body: str) -> None:
        print(f"\n## {title}\n{body}")
        lines.extend([f"## {title}", "", body, ""])

    cfg = {}
    cp = runs[0] / "config_resolved.yaml"
    if cp.exists():
        cfg = yaml.safe_load(cp.read_text())
    panel = a.panel or cfg.get("panel")
    country = a.country or cfg.get("country")

    sc = pd.concat([load_run(r) for r in runs], ignore_index=True)
    models = list(dict.fromkeys(sc.model))
    sizes = {str(r / "forecasts.parquet"): (r / "forecasts.parquet").stat().st_size / 2**20
             for r in runs if (r / "forecasts.parquet").exists()}

    # sanity: raw counts, NaNs
    raw = sc.groupby(["model", "horizon"]).size().unstack()
    nan = sc.groupby("model").wis_log.apply(lambda s: int(s.isna().sum()))
    sanity = [f"forecasts.parquet size (MiB): " + ", ".join(f"{k}={v:.0f}" for k, v in sizes.items()),
              f"NaN log-WIS rows per model: {nan.to_dict()}"]

    # panel flags
    if panel:
        pcols = ["unit_id", "week_start", "flag_gap", "zero_filled"]
        import pyarrow.parquet as pq
        avail = set(pq.ParquetFile(panel).schema_arrow.names)
        p = pd.read_parquet(panel, columns=[c for c in pcols + ["country"] if c in avail])
        if country and "country" in p.columns:
            p = p[p.country == country]
        p = p.rename(columns={"week_start": "target_week"}).drop(columns=["country"], errors="ignore")
        p["unit_id"] = p.unit_id.astype(str)
        p["target_week"] = pd.to_datetime(p.target_week)
        sc = sc.merge(p, on=["unit_id", "target_week"], how="left")
        if "flag_gap" in sc.columns:
            g = sc.flag_gap.fillna(False).astype(bool)
            sanity.append(f"flag_gap rows excluded: {int(g.sum())} (panel gap weeks: {int(p.flag_gap.sum())})")
            sc = sc[~g]
    if "zero_filled" not in sc.columns:
        sc["zero_filled"] = False
    sc["zero_filled"] = sc.zero_filled.fillna(False).astype(bool)

    # common rows across all models
    sc = sc[sc.wis_log.notna()]
    cnt = sc.groupby(KEYS, sort=False).model.transform("size")
    sc = sc[cnt == len(models)].reset_index(drop=True)
    common = sc.groupby(["model", "horizon"]).size().unstack()
    sanity.append(f"rows per model x horizon, raw:\n\n{md(raw, 0)}\n")
    sanity.append(f"rows per model x horizon, common set used below (all equal: "
                  f"{bool(common.nunique().max() == 1 and (common.values == common.values[0, 0]).all())}):"
                  f"\n\n{md(common, 0)}\n")
    emit("Sanity", "\n\n".join(sanity))

    # a, b, c
    ta = sc.pivot_table(index="model", columns="horizon", values="wis_log", aggfunc="mean").reindex(models)
    ta["mean"] = ta.mean(axis=1)
    emit("(a) Mean log1p WIS, model x horizon, pooled test years", md(ta))
    tb = sc[sc.horizon.isin([1, 4])].pivot_table(index=["horizon", "model"], columns="test_year",
                                                values="wis_log", aggfunc="mean")
    emit("(b) Mean log1p WIS, model x test year, h=1 and h=4", md(tb))
    tc = sc.pivot_table(index="model", columns="horizon", values="wis_case", aggfunc="mean").reindex(models)
    emit("(c) Mean case-scale WIS, model x horizon", md(tc, 3))

    # d coverage
    nz = sc.cases > 0
    td = pd.concat({"all": sc.groupby("model")[["cov_40", "cov_80"]].mean(),
                    "cases>0": sc[nz].groupby("model")[["cov_40", "cov_80"]].mean()}, axis=1).reindex(models)
    td.columns = [f"{c[1]} ({c[0]})" for c in td.columns]
    emit(f"(d) Interval coverage (nominal 0.40/0.80); non-zero share of targets = {nz.mean():.3f}", md(td, 3))
    tdy = sc[nz].pivot_table(index="model", columns="test_year", values="cov_80", aggfunc="mean").reindex(models)
    emit("(d2) 80% coverage on non-zero targets by test year", md(tdy, 3))

    # e zero-filled
    te = sc.pivot_table(index="model", columns="zero_filled", values="wis_log", aggfunc="mean").reindex(models)
    te.columns = [f"zero_filled={c}" for c in te.columns]
    zf = sc[sc.model == models[0]].groupby("test_year").zero_filled.mean()
    emit("(e) Mean log1p WIS by target type (zero_filled vs observed)", md(te)
         + "\n\nShare of zero_filled targets by test year: "
         + ", ".join(f"{y}: {v:.3f}" for y, v in zf.items()))
    tey = sc[sc.zero_filled].pivot_table(index="model", columns="test_year", values="wis_log",
                                         aggfunc="mean").reindex(models)
    if len(tey.columns):
        emit("(e2) Mean log1p WIS on zero_filled targets by test year", md(tey))

    # f DM
    tfm = next((m for m in models if "timesfm" in m.lower()), None)
    nb = next((m for m in models if m.lower().startswith("nb")), None)
    pairs = [(a.ref, a.naive), (a.ref, nb), (a.ref, tfm), (tfm, a.naive)]
    pairs = [(x, y) for x, y in pairs if x in models and y in models]
    rows = []
    for h in sorted(sc.horizon.unique()):
        sh = sc[sc.horizon == h]
        for x, y in pairs:
            d = loss_diff_series(sh, x, y, metric="wis_log", model_col="model")
            r = dm_test(d.to_numpy(), h=int(h))
            rows.append({"A": x, "B": y, "horizon": h, "mean_d": r.mean_d, "stat": r.stat,
                         "df": r.df, "p": r.p_value, "T": r.T})
    tf = pd.DataFrame(rows)
    tf["p_holm"] = holm(tf.p.to_numpy())
    tf["better"] = np.where(tf.p_holm < 0.05, np.where(tf.mean_d < 0, tf.A, tf.B), "n.s.")
    emit("(f) DM tests (EWC + HLN), d = log-WIS(A) - log-WIS(B) per target week; Holm over all "
         f"{len(tf)} tests", md(tf, 4, index=False))

    # g per-unit
    pu = sc[sc.model.isin([a.ref, a.naive])].pivot_table(index=["unit_id", "horizon"], columns="model",
                                                         values="wis_log", aggfunc="mean")
    pu["d"] = pu[a.ref] - pu[a.naive]
    tg = pu.groupby("horizon").d.agg(share_ref_better=lambda s: (s < 0).mean(), median_diff="median",
                                     n_units="size")
    allh = (sc[sc.model.isin([a.ref, a.naive])].pivot_table(index="unit_id", columns="model",
                                                          values="wis_log", aggfunc="mean"))
    dall = allh[a.ref] - allh[a.naive]
    tg.loc["all"] = [(dall < 0).mean(), dall.median(), len(dall)]
    emit(f"(g) Per-unit mean log-WIS, {a.ref} - {a.naive}", md(tg))

    for k, t in {"a_wis_log_h": ta, "b_wis_log_year": tb, "c_wis_case_h": tc, "d_coverage": td,
                 "e_zero_filled": te, "g_per_unit": tg}.items():
        t.to_csv(out / f"{k}.csv")
    tf.to_csv(out / "f_dm.csv", index=False)
    (out / "tables.md").write_text(f"# Analysis of {', '.join(map(str, runs))}\n\n" + "\n".join(lines))
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
