#!/usr/bin/env python
"""Paper-1 estimands (G_emb, G_id, G_excess, ID share) for one country x split, inference policy v2.

Usage:
    python scripts/run/estimands_report.py --l3 runs/brazil_s1_L3 --l4 runs/brazil_s1_L4 \
        --l3c runs/brazil_s1_L3_Cstar --l4c runs/brazil_s1_L4_Cstar [--ref-name L3|N3] \
        [--ladder RUN ...] [--pairs A:B ...] [--out DIR] [--prefix estimands] \
        [--n-boot 2000] [--block-len 52] [--boot-seed 0] [--margin-rel 0.01] \
        [--exclude-units FILE | --no-exclude-units] [--exclude-weeks FILE | --no-exclude-weeks] \
        [--exclude-weeks-action exclude|sensitivity|all ...] \
        [--universe-first-year-max [--late-entry FILE]]

Each role accepts one or more run dirs (concatenated; e.g. extra-seed runs). Rows are told apart
by the ``seed`` column of scores.parquet (absent = seed 0); a duplicated (key, seed) is an error.

Definitions (positive = lower log1p WIS for the second model, i.e. an improvement):
  G_emb = WIS(L3) - WIS(L4); G_id = WIS(L3) - WIS(L3+C*); G_excess = WIS(L3+C*) - WIS(L4+C*).
  In the no-history arm pass N3/N4 runs as --l3/--l4 etc. and --ref-name N3.

Inference (deviations rows 9, 11, 12, 16; library code pop.eval.estimands.infer_estimand):
  - Seeds: per row, each role's log-WIS is averaged over its seeds (seed-averaged loss); all
    CIs/tests use these. Per-seed estimands use a role's own seed-s loss where present, else
    its seed-averaged loss; point estimate = mean over seeds (= estimate on seed-averaged
    losses); seed SD over the seeds actually present (NaN with one seed).
  - Weekly series: per (horizon, target week) cross-unit mean gain; pooled-h = per-week mean
    over the horizons present. Primary: DM on that series, EWC long-run variance
    (B = floor(0.4 T^(2/3)), t_B), HLN with the largest horizon; se = se_EWC/HLN;
    CI = dbar -/+ t_B se (95%, and 90% for TOST).
  - TOST margin = 1% of WIS(ref) (ref = L3, or N3); class: equivalent (90% CI inside
    +-margin) / superior (95% CI > 0 and p < .05) / inferior / inconclusive.
    MDE = (t_{B,.975} + t_{B,.80}) se.
  - Sensitivity: states (adm1) x 52-week circular blocks (shared across states) bootstrap,
    2,000 reps, percentile 95% CI of the row-level mean gain.
  - ID share = G_id/G_emb only if the primary 95% CI of G_emb excludes 0 and G_emb >= 1% of
    WIS(L3) (bootstrap ratio CI).
  - No multiplicity correction here: the primary family (pooled-h G_excess, Holm over the 14
    country x split cells) lives in scripts/run/primary_family.py.

Rows: keys (test_year, unit, origin, target, horizon) scored by all four roles; flag_gap target
weeks dropped; then the exclusions (pop.eval.exclusions), in this order: no-geometry units
(default ON, data/processed/exclusions_v1/no_geometry_units.csv), incomplete weeks (default ON,
incomplete_weeks.csv rows with action == "exclude", i.e. the primary k = 0.5 flags; see
docs/data/completeness_v1.md; `--exclude-weeks-action all` adds the sensitivity flags),
late-entry units (only with --universe-first-year-max: first case year > test year). Counts are reported.
Outbreak week: target cases >= max(unit p90 of weekly cases over 2013-2019, 5).
"""
from __future__ import annotations

import argparse
import json
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
from analyze_run import md  # noqa: E402

from pop.eval import exclusions as X  # noqa: E402
from pop.eval.estimands import (ESTIMANDS, ROLES, compute_estimands_v2, infer_estimand,  # noqa: E402
                                seed_gain_frame, weekly_pooled)
from pop.eval.stats import ewc_inference  # noqa: E402

KEYS = ["test_year", "unit_id", "origin_week", "target_week", "horizon"]
EST = list(ESTIMANDS)
EXCL_DIR = Path("data/processed/exclusions_v1")
DEFAULT_UNITS = EXCL_DIR / "no_geometry_units.csv"
DEFAULT_LATE = EXCL_DIR / "late_entry_units.csv"
DEFAULT_WEEKS = EXCL_DIR / "incomplete_weeks.csv"


# ---------------------------------------------------------------------------- loading
def read_scores(dirs, cols=("wis_log", "cases", "cov_40", "cov_80")) -> pd.DataFrame:
    """Concatenate scores.parquet of the dirs; adds seed (0 if absent) and run label."""
    out = []
    for d in map(Path, dirs):
        names = pq.ParquetFile(d / "scores.parquet").schema.names
        use = KEYS + [c for c in cols if c in names] + [c for c in ("seed", "run") if c in names]
        s = pd.read_parquet(d / "scores.parquet", columns=use)
        if "seed" not in s:
            s["seed"] = 0
        s["seed"] = s.seed.astype(int)
        s["label"] = s["run"].astype(str) if "run" in s else d.name
        s["dir"] = d.name
        s["test_year"] = s.test_year.astype(int)
        s["unit_id"] = s.unit_id.astype(str)
        s["origin_week"] = pd.to_datetime(s.origin_week)
        s["target_week"] = pd.to_datetime(s.target_week)
        s["horizon"] = s.horizon.astype(int)
        out.append(s.drop(columns=[c for c in ("run",) if c in s]))
    return pd.concat(out, ignore_index=True)


def run_complete(d) -> bool:
    """A run counts as complete when scores.parquet exists (written after all chunks)."""
    return (Path(d) / "scores.parquet").exists()


def load_panel(panel: str, country: str | None) -> pd.DataFrame:
    cols = ["unit_id", "country", "adm1", "week_start", "year", "cases", "zero_filled", "flag_gap"]
    p = pd.read_parquet(panel, columns=cols)
    if country:
        p = p[p.country.astype(str).str.upper() == str(country).upper()]
    p = p.drop(columns="country")
    p["unit_id"] = p.unit_id.astype(str)
    p["week_start"] = pd.to_datetime(p.week_start)
    return p


def outbreak_threshold(p: pd.DataFrame) -> pd.Series:
    base = p[(p.year >= 2013) & (p.year <= 2019) & ~p.flag_gap.fillna(False).astype(bool)]
    return np.maximum(base.groupby("unit_id").cases.quantile(0.9), 5.0)


def load_cell(roles: dict, *, panel: str | None = None, country: str | None = None,
              exclude_units=DEFAULT_UNITS, exclude_weeks=DEFAULT_WEEKS, late_entry=None,
              week_actions=("exclude",)) -> tuple:
    """Load the four role runs of one cell and build the seed-aware gain frame.

    roles: {"L3": [dirs], "L4": [...], "L3C": [...], "L4C": [...]}.
    Returns (g, info): g from ``seed_gain_frame`` with state/zero_filled/outbreak columns,
    info = dict of labels, seeds, row counts and exclusion counts.
    """
    first = Path(roles["L3"][0])
    cfg = yaml.safe_load((first / "config_resolved.yaml").read_text())
    country = country or cfg.get("country")
    pnl = load_panel(panel or cfg["panel"], country)
    info = {"country": country, "roles": {}, "excluded": {}}
    frames = []
    for r in ROLES:
        s = read_scores(roles[r], cols=("wis_log", "cases"))
        info["roles"][r] = {"dirs": [str(d) for d in roles[r]],
                            "labels": sorted(s.label.unique()),
                            "seeds": sorted(int(x) for x in s.seed.unique()),
                            "rows": int(len(s)),
                            "seeds_by_h": {int(h): sorted(int(x) for x in v.unique())
                                           for h, v in s.groupby("horizon").seed},
                            "nan_wis": int(s.wis_log.isna().sum())}
        frames.append(s.assign(model=r))
        if r == "L3":
            cases = s.drop_duplicates(KEYS).set_index(KEYS)["cases"]
    sc = pd.concat(frames, ignore_index=True)
    sc = sc[sc.wis_log.notna()]
    g = seed_gain_frame(sc, {r: r for r in ROLES}, metric="wis_log", keys=KEYS)
    seeds = g.attrs["seeds"]
    n_union = len(sc.drop_duplicates(KEYS))
    info["rows_common"] = int(len(g))
    info["rows_not_common"] = int(n_union - len(g))
    pm = pnl.rename(columns={"week_start": "target_week", "cases": "panel_cases"})[
        ["unit_id", "target_week", "adm1", "panel_cases", "zero_filled", "flag_gap"]]
    g = g.merge(pm, on=["unit_id", "target_week"], how="left", validate="many_to_one")
    g["cases"] = cases.reindex(pd.MultiIndex.from_frame(g[KEYS])).to_numpy()
    info["no_panel_match"] = int(g.adm1.isna().sum())
    info["case_mismatch"] = int((~np.isclose(g.cases, g.panel_cases)).sum())
    gap = g.flag_gap.fillna(False).astype(bool).to_numpy()
    g = g[~gap]
    info["excluded"]["flag_gap"] = int(gap.sum())
    g["state"] = g.adm1.astype(str)
    g["zero_filled"] = g.zero_filled.fillna(False).astype(bool)
    g["outbreak"] = g.cases >= g.unit_id.map(outbreak_threshold(pnl)).fillna(5.0)
    for name, path, fn, kw in (
            ("no_geometry_units", exclude_units, X.exclude_units, {}),
            ("incomplete_weeks", exclude_weeks, X.exclude_weeks,
             {"country": country, "actions": week_actions}),
            ("late_entry_units", late_entry, X.exclude_late_entry, {})):
        if path is None:
            info["excluded"][name] = "off"
        elif not Path(path).exists():
            info["excluded"][name] = f"file missing ({path}); not applied"
        else:
            g, n = fn(g, path, **kw)
            info["excluded"][name] = int(n)
    g = g.reset_index(drop=True)
    g.attrs["seeds"] = seeds
    info["rows_scored"] = int(len(g))
    info["seeds"] = seeds
    return g, info


def resolve_roles(a) -> dict:
    return {"L3": a.l3, "L4": a.l4, "L3C": a.l3c, "L4C": a.l4c}


def add_exclusion_args(ap: argparse.ArgumentParser) -> None:
    ap.add_argument("--exclude-units", default=str(DEFAULT_UNITS),
                    help="unit_id CSV dropped from scoring (default: no-geometry units)")
    ap.add_argument("--no-exclude-units", action="store_true")
    ap.add_argument("--exclude-weeks", default=str(DEFAULT_WEEKS),
                    help="incomplete-weeks CSV (country, week_start, scope, adm1, action); "
                         "default ON with the primary rows (action == exclude, k = 0.5)")
    ap.add_argument("--no-exclude-weeks", action="store_true")
    ap.add_argument("--exclude-weeks-action", nargs="+", default=["exclude"],
                    help="action values of incomplete_weeks.csv to drop (default: exclude = "
                         "primary k=0.5 flags); 'all' = every row incl. sensitivity flags")
    ap.add_argument("--universe-first-year-max", action="store_true",
                    help="sensitivity: drop units whose first case year is after the origin year")
    ap.add_argument("--late-entry", default=str(DEFAULT_LATE))


def exclusion_kw(a) -> dict:
    return {"exclude_units": None if a.no_exclude_units else a.exclude_units,
            "exclude_weeks": None if a.no_exclude_weeks else a.exclude_weeks,
            "late_entry": a.late_entry if a.universe_first_year_max else None,
            "week_actions": (None if [x.lower() for x in a.exclude_weeks_action] == ["all"]
                             else a.exclude_weeks_action)}


# ---------------------------------------------------------------------------- tables
FIELDS = ["estimate", "se", "df", "T", "stat", "p", "lo95", "hi95", "lo90", "hi90", "wis_ref",
          "margin", "pct_of_ref", "tost_p", "cls", "mde", "mde_pct", "n_seeds", "seed_mean",
          "seed_sd", "boot_lo", "boot_hi", "n_rows", "n_weeks"]


def est_rows(g, label, kw, bootstrap=True):
    r = compute_estimands_v2(g, bootstrap=bootstrap, **kw)
    rows = []
    for e in EST:
        row = {**label, "estimand": e, **{f: r[e].get(f, np.nan) for f in FIELDS}}
        row["seed_estimates"] = json.dumps({str(k): v for k, v in r[e]["seed_estimates"].items()})
        rows.append(row)
    rows.append({**label, "estimand": "ID_share", "estimate": r["ID_share"]["estimate"],
                 "boot_lo": r["ID_share"].get("boot_lo", np.nan),
                 "boot_hi": r["ID_share"].get("boot_hi", np.nan),
                 "reason": r["ID_share"]["reason"]})
    return rows


def fmt_table(t: pd.DataFrame, lead: list[str]) -> str:
    t = t[t.estimand.isin(EST)].copy()
    t["CI95"] = [f"[{a:+.5f}, {b:+.5f}]" for a, b in zip(t.lo95, t.hi95)]
    t["CI90"] = [f"[{a:+.5f}, {b:+.5f}]" for a, b in zip(t.lo90, t.hi90)]
    t["boot95_52wk"] = [f"[{a:+.5f}, {b:+.5f}]" if np.isfinite(a) else "-"
                        for a, b in zip(t.boot_lo.astype(float), t.boot_hi.astype(float))]
    t["margin"] = t.margin.map(lambda v: f"{v:.5f}")
    t["MDE (% ref)"] = [f"{m:.5f} ({p:.2f}%)" for m, p in zip(t.mde, t.mde_pct)]
    t["n_seeds"] = t.n_seeds.astype(int)
    t["seed SD"] = [f"{v:.5f}" if np.isfinite(v) else "-" for v in t.seed_sd.astype(float)]
    cols = lead + ["estimand", "estimate", "pct_of_ref", "CI95", "CI90", "p", "margin", "tost_p",
                   "cls", "MDE (% ref)", "n_seeds", "seed SD", "boot95_52wk"]
    return md(t[cols], 5, index=False)


def main() -> None:
    ap = argparse.ArgumentParser()
    for r in ("l3", "l4", "l3c", "l4c"):
        ap.add_argument(f"--{r}", required=True, nargs="+")
    ap.add_argument("--ref-name", default="L3", help="label of the reference level (L3 or N3)")
    ap.add_argument("--ladder", nargs="*", default=[], help="extra run dirs for the ladder table")
    ap.add_argument("--pairs", nargs="*", default=[], metavar="A:B",
                    help="extra EWC pairs on ladder labels; d = WIS(A) - WIS(B)")
    ap.add_argument("--out", default=None)
    ap.add_argument("--prefix", default="estimands_v2")
    ap.add_argument("--panel", default=None)
    ap.add_argument("--country", default=None)
    ap.add_argument("--n-boot", type=int, default=2000)
    ap.add_argument("--block-len", type=int, default=52)
    ap.add_argument("--boot-seed", type=int, default=0)
    ap.add_argument("--margin-rel", type=float, default=0.01)
    add_exclusion_args(ap)
    a = ap.parse_args()

    roles = resolve_roles(a)
    l3 = Path(roles["L3"][0])
    out = Path(a.out) if a.out else l3.parent / (l3.name + "_analysis")
    out.mkdir(parents=True, exist_ok=True)
    pre = out / a.prefix
    lines: list[str] = []

    def emit(title, body):
        print(f"\n## {title}\n{body}", flush=True)
        lines.extend([f"## {title}", "", body, ""])

    g, info = load_cell(roles, panel=a.panel, country=a.country, **exclusion_kw(a))
    rt = pd.DataFrame([{"role": r, "dirs": " ".join(Path(d).name for d in v["dirs"]),
                        "labels": ",".join(v["labels"]), "rows": v["rows"],
                        "seeds": ",".join(map(str, v["seeds"])), "nan_wis": v["nan_wis"],
                        "seeds_by_h": "; ".join(f"h{h}:{','.join(map(str, s))}"
                                                for h, s in v["seeds_by_h"].items())}
                       for r, v in info["roles"].items()])
    emit("Rows, seeds and exclusions", md(rt, 0, index=False) + "\n\n"
         + f"Keys scored by all four roles: {info['rows_common']} (keys missing from at least one "
           f"role: {info['rows_not_common']}); no panel match: {info['no_panel_match']}; score "
           f"cases != panel cases: {info['case_mismatch']}. Removed: "
         + "; ".join(f"{k}: {v}" for k, v in info["excluded"].items())
         + f". Rows scored: {info['rows_scored']}; states: {g.state.nunique()}; "
           f"outbreak share: {g.outbreak.mean():.4f}.")
    (Path(f"{pre}_info.json")).write_text(json.dumps(info, indent=1, default=str))

    kw = dict(cluster_col="state", time_col="target_week", block_len=a.block_len,
              n_boot=a.n_boot, seed=a.boot_seed, margin_rel=a.margin_rel)
    rows = []
    for h, gh in g.groupby("horizon"):
        gh.attrs = dict(g.attrs)
        rows += est_rows(gh, {"horizon": h, "test_year": "pooled", "stratum": "all"}, kw)
    rows += est_rows(g, {"horizon": "pooled", "test_year": "pooled", "stratum": "all"}, kw)
    for y, gy in g.groupby("test_year"):
        gy.attrs = dict(g.attrs)
        rows += est_rows(gy, {"horizon": "pooled", "test_year": y, "stratum": "all"}, kw,
                         bootstrap=False)
    strata = {"observed": ~g.zero_filled, "zero_filled": g.zero_filled,
              "outbreak": g.outbreak, "non_outbreak": ~g.outbreak}
    for name, msk in strata.items():
        gs = g[msk]
        gs.attrs = dict(g.attrs)
        rows += est_rows(gs, {"horizon": "pooled", "test_year": "pooled", "stratum": name}, kw,
                         bootstrap=False)
    E = pd.DataFrame(rows)
    E.to_csv(f"{pre}_main.csv", index=False)
    pooled = E[(E.test_year.astype(str) == "pooled") & (E.stratum == "all")]
    ref = a.ref_name
    emit(f"Main estimands, pooled test years (log1p WIS; + = improvement; ref = {ref})",
         fmt_table(pooled.sort_values(["estimand", "horizon"], key=lambda s: s.astype(str)),
                   ["horizon"])
         + f"\n\nWIS({ref}) (pooled weekly mean): " + ", ".join(
             f"h{r.horizon}={r.wis_ref:.5f}" for r in pooled[pooled.estimand == "G_excess"].itertuples()))
    py = E[(E.test_year.astype(str) != "pooled")]
    emit("Per test year (pooled over h; secondary; EWC with T = 52-53 weeks, B = 5)",
         fmt_table(py, ["test_year"]))
    st = E[(E.stratum != "all")]
    emit("Strata (pooled over h and years; secondary; weeks with no stratum rows dropped)",
         fmt_table(st, ["stratum"]))
    ids = E[E.estimand == "ID_share"][["horizon", "test_year", "stratum", "estimate", "boot_lo",
                                       "boot_hi", "reason"]]
    emit("ID share rule (gate on the primary EWC 95% CI of G_emb)",
         md(ids[ids.stratum == "all"], 4, index=False))
    pr = pooled[(pooled.estimand == "G_excess") & (pooled.horizon.astype(str) == "pooled")].iloc[0]
    (Path(f"{pre}_primary.json")).write_text(json.dumps(
        {k: (v.item() if hasattr(v, "item") else v) for k, v in pr.items()}, indent=1, default=str))

    # ---------------------------------------------------------------- ladder (optional)
    if a.ladder:
        lad_sc = read_scores(a.ladder)
        keyset = pd.MultiIndex.from_frame(g[KEYS])
        lad_sc = lad_sc[pd.MultiIndex.from_frame(lad_sc[KEYS]).isin(keyset) & lad_sc.wis_log.notna()]
        avg = lad_sc.groupby(["label"] + KEYS, sort=False)[["wis_log", "cov_40", "cov_80", "cases"]].mean()
        avg = avg.reset_index()
        cnt = avg.groupby(KEYS).label.transform("size")
        nl = avg.label.nunique()
        avg = avg[cnt == nl]
        tb = avg.pivot_table(index="label", columns="horizon", values="wis_log", aggfunc="mean")
        tb["mean"] = tb.mean(axis=1)
        nz = avg.cases > 0
        tb["cov80_all"] = avg.groupby("label").cov_80.mean()
        tb["cov80_nonzero"] = avg[nz].groupby("label").cov_80.mean()
        tb.to_csv(f"{pre}_ladder.csv")
        emit(f"Ladder (seed-averaged; keys common to all ladder runs within the estimand rows: "
             f"{len(avg) // max(nl, 1)})", md(tb, 4))
        dl = []
        for p in a.pairs:
            x, y = p.split(":", 1)
            if x not in tb.index or y not in tb.index:
                continue
            w = avg[avg.label.isin([x, y])].pivot_table(index=KEYS, columns="label",
                                                        values="wis_log").reset_index()
            w["d"] = w[x] - w[y]
            for h in sorted(w.horizon.unique()) + ["pooled"]:
                wh = w if h == "pooled" else w[w.horizon == h]
                r = ewc_inference(weekly_pooled(wh, "d").to_numpy(), h=int(wh.horizon.max()))
                dl.append({"A": x, "B": y, "horizon": h, "mean_d": r.estimate, "lo95": r.lo95,
                           "hi95": r.hi95, "p": r.p, "df": r.df, "T": r.T})
        if dl:
            dl = pd.DataFrame(dl)
            dl.to_csv(f"{pre}_ladder_ewc.csv", index=False)
            emit("Ladder pairs (d = WIS(A) - WIS(B); EWC + HLN; no multiplicity correction)",
                 md(dl, 5, index=False))

    Path(f"{pre}_tables.md").write_text(
        "# Estimands report (inference policy v2)\n\nRoles: " + ", ".join(
            f"{k}={' '.join(map(str, v))}" for k, v in roles.items())
        + f"\n\nPrimary: DM/EWC + HLN on the weekly cross-unit mean gain (pooled-h = per-week "
          f"mean over horizons); TOST margin {a.margin_rel:.0%} of WIS({ref}). Sensitivity "
          f"bootstrap: {a.n_boot} reps, states x {a.block_len}-week circular blocks, seed "
          f"{a.boot_seed}.\n\n" + "\n".join(lines))
    print(f"\nwrote {pre}_*", flush=True)


if __name__ == "__main__":
    main()
