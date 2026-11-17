#!/usr/bin/env python
"""One-command results kit for Paper 1 ("Place or Placeholder?").

Usage (repo root, after `source env.sh`):
    nice -n 19 python scripts/analysis/make_results.py [--only CELL ...] [--force]
        [--n-boot 0] [--no-scheduler] [--out-tables docs/results/tables]
        [--out-figures docs/results/figures] [--brief docs/results/RESULTS_BRIEF.md]
        [--cache runs/analysis_cache]

What it does (idempotent; safe to run while production runs are going):
  1. Builds the cell registry (rk_cells.build_registry): the 14 primary cells of
     configs/primary_cells.yaml (plan.json reuse applied) + secondary arms (BR S1 extra seeds,
     yearly_ref, report_delay, controls panel, per-level tuning; TW S1 with BR params;
     no-history BR S1/S2). Cells with any incomplete role are "pending" and never read.
  2. For every available cell: rows/exclusions via scripts/run/estimands_report.load_cell,
     estimands via pop.eval.estimands.compute_estimands_v2 (DM/EWC + HLN, TOST 1%, MDE,
     seeds), ladder (mean log1p WIS, 40/80% coverage) on the cell's common keys. Cached under
     runs/analysis_cache/<cell>/ keyed on the scores.parquet size/mtime of every run used,
     exclusion files and options; a re-run recomputes only new or changed cells.
  3. Writes tables T1-T6 (CSV + LaTeX booktabs), figures F1-F4 (PDF + PNG) and
     docs/results/RESULTS_BRIEF.md.
Default exclusions are those of estimands_report.py (no-geometry units, primary incomplete
weeks). The 52-week bootstrap sensitivity is off by default (--n-boot 2000 to add it).
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
import sys
import traceback
from pathlib import Path

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_MAX_THREADS"):
    os.environ.setdefault(_v, "2")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(ROOT / "scripts" / "run"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import rk_cells as C  # noqa: E402
import rk_compute as K  # noqa: E402
import rk_render as R  # noqa: E402
from estimands_report import DEFAULT_UNITS, DEFAULT_WEEKS  # noqa: E402
from pop.eval.stats import holm  # noqa: E402

N_FAMILY = 14
CLS_TEXT = {
    "equivalent": "the 90% CI lies inside ±1% of WIS(ref): any effect is too small to matter",
    "superior": "the 95% CI excludes 0 on the improvement side: the second model is better",
    "inferior": "the 95% CI excludes 0 on the harm side: the second model is worse",
    "inconclusive": "the CI crosses 0 and reaches past the ±1% margin: the data cannot tell",
}


# ------------------------------------------------------------------ helpers
def pct_cols(d: pd.DataFrame) -> pd.DataFrame:
    d = d.copy()
    w = d.wis_ref.astype(float)
    for c in ("lo95", "hi95", "lo90", "hi90"):
        d[f"{c}_pct"] = 100 * d[c].astype(float) / w
    return d


def pick(est: pd.DataFrame, cell: str, estimand: str, horizon="pooled", year="pooled",
         stratum="all"):
    x = est[(est.cell == cell) & (est.estimand == estimand) & (est.horizon == horizon)
            & (est.test_year == year) & (est.stratum == stratum)]
    return None if x.empty else x.iloc[0]


def ci_txt(r, nd=2) -> str:
    return f"{r.pct_of_ref:+.{nd}f}% [{r.lo95_pct:+.{nd}f}, {r.hi95_pct:+.{nd}f}]"


def scheduler_status() -> str:
    try:
        p = subprocess.run([sys.executable, "scripts/run/scheduler.py", "status"],
                           capture_output=True, text=True, timeout=120)
        return (p.stdout or p.stderr).strip()
    except Exception as e:  # noqa: BLE001
        return f"(scheduler status unavailable: {e!r})"


# ------------------------------------------------------------------ main
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--manifest", default="configs/primary_cells.yaml")
    ap.add_argument("--only", nargs="*", default=None, help="compute only these cell ids")
    ap.add_argument("--force", action="store_true", help="ignore the cache")
    ap.add_argument("--n-boot", type=int, default=0)
    ap.add_argument("--block-len", type=int, default=52)
    ap.add_argument("--margin-rel", type=float, default=0.01)
    ap.add_argument("--no-scheduler", action="store_true")
    ap.add_argument("--no-exclusions", action="store_true")
    ap.add_argument("--cache", default="runs/analysis_cache")
    ap.add_argument("--out-tables", default="docs/results/tables")
    ap.add_argument("--out-figures", default="docs/results/figures")
    ap.add_argument("--brief", default="docs/results/RESULTS_BRIEF.md")
    ap.add_argument("--root", default=str(ROOT), help="repo root (tests pass a temp dir)")
    ap.add_argument("--registry", default=None, help="JSON cell list instead of the built-in registry (tests)")
    a = ap.parse_args(argv)
    os.chdir(a.root)
    log = lambda m: print(m, flush=True)  # noqa: E731

    cells = (json.loads(Path(a.registry).read_text()) if a.registry
             else C.build_registry(a.manifest))
    excl = ({"exclude_units": None, "exclude_weeks": None, "late_entry": None, "week_actions": ("exclude",)}
            if a.no_exclusions else
            {"exclude_units": str(DEFAULT_UNITS), "exclude_weeks": str(DEFAULT_WEEKS),
             "late_entry": None, "week_actions": ("exclude",)})
    status, ests, lads, infos = {}, [], [], {}
    for c in cells:
        st, roles = C.cell_status(c)
        status[c["id"]] = {"status": st, "roles": roles}
        if st != "available" or (a.only and c["id"] not in a.only and not (Path(a.cache) / c["id"]).exists()):
            log(f"{c['id']}: {st}" + ("" if st == "available" else
                f" ({'; '.join(f'{r}: {v}' for r, v in roles.items() if v != 'complete')})"))
            if st == "available":
                status[c["id"]]["status"] = "available (not computed: --only)"
            continue
        try:
            force = a.force and (not a.only or c["id"] in a.only)
            res = K.compute_cell(c, cache_root=Path(a.cache), excl=excl, margin_rel=a.margin_rel,
                                 n_boot=a.n_boot, block_len=a.block_len, force=force, log=log)
            ests.append(res["est"])
            lads.append(res["ladder"])
            infos[c["id"]] = res["info"]
        except Exception as e:  # noqa: BLE001
            status[c["id"]]["status"] = "error"
            status[c["id"]]["error"] = repr(e)[:300]
            log(f"{c['id']}: ERROR {e!r}\n{traceback.format_exc()}")
    est = pd.concat(ests, ignore_index=True) if ests else pd.DataFrame(
        columns=["cell", "horizon", "test_year", "stratum", "estimand"] + K.FIELDS)
    for col in ("horizon", "test_year", "stratum", "estimand"):
        est[col] = est[col].astype(str)
    est = est[est.estimand != "error"].copy() if "estimand" in est else est
    est = pct_cols(est[est.estimand != "ID_share"]).pipe(
        lambda d: pd.concat([d, est[est.estimand == "ID_share"]], ignore_index=True))
    lad = pd.concat(lads, ignore_index=True) if lads else pd.DataFrame(
        columns=["cell", "label", "horizon", "n_rows", "wis_log", "cov_40", "cov_80", "cov_80_nonzero"])
    byid = {c["id"]: c for c in cells}
    cstars = {c["id"]: c.get("cstar") for c in cells}
    T, F = Path(a.out_tables), Path(a.out_figures)
    made = {}

    # ---------------- T1 primary family
    prim = [c for c in cells if c["group"] == "primary"]
    rows = []
    for c in prim:
        r = pick(est, c["id"], "G_excess")
        base = {"cell": c["id"], "country": c["country"], "split": c["split"],
                "C_star": cstars.get(c["id"]) or "", "status": status[c["id"]]["status"]}
        if r is None:
            rows.append({**base, "missing": "; ".join(f"{k}: {v}" for k, v in
                                                       status[c["id"]]["roles"].items() if v != "complete")})
            continue
        rows.append({**base, "G_excess": r.estimate, "pct_of_WIS_ref": r.pct_of_ref,
                     "lo95": r.lo95, "hi95": r.hi95, "lo90": r.lo90, "hi90": r.hi90,
                     "lo95_pct": r.lo95_pct, "hi95_pct": r.hi95_pct, "lo90_pct": r.lo90_pct,
                     "hi90_pct": r.hi90_pct, "DM_p": r.p, "TOST_p": r.tost_p, "TOST_class": r.cls,
                     "MDE": r.mde, "MDE_pct": r.mde_pct, "WIS_ref": r.wis_ref, "n_seeds": r.n_seeds,
                     "seed_sd": r.seed_sd, "T_weeks": r.T, "n_rows": r.n_rows, "missing": ""})
    t1 = pd.DataFrame(rows)
    av = t1.status == "available"
    t1["Holm_p_available"] = np.nan
    t1["p_bonf14"] = np.nan
    if av.any():
        t1.loc[av, "Holm_p_available"] = holm(t1.loc[av, "DM_p"].astype(float).to_numpy())
        t1.loc[av, "p_bonf14"] = np.minimum(1.0, N_FAMILY * t1.loc[av, "DM_p"].astype(float))
    for c in ("G_excess", "pct_of_WIS_ref", "lo95_pct", "hi95_pct", "lo90_pct", "hi90_pct",
              "DM_p", "MDE_pct", "TOST_class"):
        if c not in t1:
            t1[c] = np.nan
    t1x = t1.copy()
    t1x["CI95 (%)"] = [f"[{l:+.2f}, {h:+.2f}]" if np.isfinite(l) else "" for l, h in
                       zip(t1x.lo95_pct.astype(float), t1x.hi95_pct.astype(float))]
    t1x["CI90 (%)"] = [f"[{l:+.2f}, {h:+.2f}]" if np.isfinite(l) else "" for l, h in
                       zip(t1x.lo90_pct.astype(float), t1x.hi90_pct.astype(float))]
    t1x["Holm p"] = t1x.Holm_p_available
    t1x["G_excess (%)"] = t1x.pct_of_WIS_ref
    t1x["DM p"] = t1x.DM_p
    t1x["TOST"] = t1x.TOST_class.fillna("pending")
    t1x["MDE (%)"] = t1x.MDE_pct
    T.mkdir(parents=True, exist_ok=True)
    t1.to_csv(T / "T1_primary_family.csv", index=False)
    (T / "T1_primary_family.tex").write_text(R.to_booktabs(
        t1x[["country", "split", "C_star", "G_excess", "G_excess (%)", "CI95 (%)", "CI90 (%)",
             "DM p", "Holm p", "TOST", "MDE (%)"]],
        "T1. Primary family: pooled-h G_excess = WIS(L3+C*) - WIS(L4+C*), log1p WIS; % of WIS(L3); "
        "DM/EWC+HLN; Holm over available cells (provisional while cells are pending)", "tab:T1", 4))
    made["T1"] = "T1_primary_family"

    # ---------------- T2 ladder
    if not lad.empty:
        lw = lad.pivot_table(index=["cell", "label"], columns="horizon", values="wis_log", sort=False)
        lw.columns = [f"WIS h{c}" if c != "pooled" else "WIS pooled" for c in lw.columns]
        lp = lad[lad.horizon == "pooled"].set_index(["cell", "label"])[["cov_40", "cov_80", "cov_80_nonzero", "n_rows"]]
        t2w = lw.join(lp).reset_index()
        t2w.insert(2, "C_star", t2w.cell.map(cstars).fillna(""))
        lad.to_csv(T / "T2_ladder_long.csv", index=False)
        hcols = sorted([c for c in t2w.columns if c.startswith("WIS h")]) + ["WIS pooled"]
        R.write_table(t2w, T, "T2_ladder",
                      "T2. Ladder: mean log1p WIS per horizon and pooled; 40%/80% interval coverage "
                      "(pooled; cov_80_nonzero = rows with cases > 0); common rows of each cell",
                      4, tex_cols=["cell", "label"] + hcols + ["cov_40", "cov_80", "cov_80_nonzero"])
        made["T2"] = "T2_ladder"

    # ---------------- T3 estimands
    keep = ["cell", "horizon", "test_year", "estimand", "estimate", "pct_of_ref", "lo95", "hi95",
            "lo95_pct", "hi95_pct", "lo90_pct", "hi90_pct", "p", "tost_p", "cls", "mde_pct",
            "wis_ref", "n_seeds", "seed_sd", "boot_lo", "boot_hi", "n_rows", "n_weeks", "reason"]
    if not est.empty:
        t3 = est[est.stratum == "all"]
        t3 = t3[[c for c in keep if c in t3]]
        t3x = t3[(t3.test_year == "pooled") & (t3.estimand != "ID_share")].copy()
        t3x["CI95 (%)"] = [f"[{l:+.2f}, {h:+.2f}]" for l, h in zip(t3x.lo95_pct, t3x.hi95_pct)]
        t3.to_csv(T / "T3_estimands.csv", index=False)
        (T / "T3_estimands.tex").write_text(R.to_booktabs(
            t3x[["cell", "estimand", "horizon", "estimate", "pct_of_ref", "CI95 (%)", "p", "cls"]],
            "T3. G_emb, G_id, G_excess per cell and horizon (pooled test years); per-year rows in the CSV",
            "tab:T3", 4))
        made["T3"] = "T3_estimands"

    # ---------------- T4 C* selection
    sel_rows = []
    for c in cells:
        s = c.get("selection")
        if not s:
            continue
        f = Path(s["dir"]) / "selection.csv"
        mk = s.get("marker")
        ok = f.exists() and (mk is None or not Path(mk).parent.exists() or Path(mk).exists())
        if not ok:
            sel_rows.append({"cell": c["id"], "candidate": "", "status": "pending"})
            continue
        x = pd.read_csv(f)
        js = json.loads((Path(s["dir"]) / "selection.json").read_text())
        for r in x.itertuples():
            sel_rows.append({"cell": c["id"], "candidate": r.run, "status": "done",
                             "wis_log_2019": r.wis_log, "seed_sd": getattr(r, "wis_log_sd_seeds", np.nan),
                             "n_seeds": getattr(r, "n_seeds", np.nan),
                             "delta_vs_ref": getattr(r, "delta_vs_ref", np.nan),
                             "selected": r.run == js.get("run"), "C_star": js.get("c_star")})
    if sel_rows:
        t4 = pd.DataFrame(sel_rows)
        t4x = t4[t4.status == "done"].copy()
        t4x["mean ± SD"] = [f"{m:.5f} ± {s:.5f}" if np.isfinite(s) else f"{m:.5f}"
                            for m, s in zip(t4x.wis_log_2019.astype(float), t4x.seed_sd.astype(float))]
        t4x["selected"] = t4x.selected.map({True: "C*", False: ""})
        t4.to_csv(T / "T4_cstar_selection.csv", index=False)
        (T / "T4_cstar_selection.tex").write_text(R.to_booktabs(
            t4x[["cell", "candidate", "mean ± SD", "n_seeds", "delta_vs_ref", "selected"]],
            "T4. C* selection at the 2019 origin: mean log1p WIS (pooled h) over seeds", "tab:T4", 5))
        made["T4"] = "T4_cstar_selection"

    # ---------------- T5 strata
    if not est.empty:
        t5 = est[(est.stratum != "all")]
        t5 = t5[[c for c in ["cell", "stratum"] + keep[2:] if c in t5]]
        t5x = t5[(t5.test_year == "pooled") & (t5.estimand != "ID_share")].copy()
        t5x["CI95 (%)"] = [f"[{l:+.2f}, {h:+.2f}]" for l, h in zip(t5x.lo95_pct, t5x.hi95_pct)]
        t5.to_csv(T / "T5_strata.csv", index=False)
        (T / "T5_strata.tex").write_text(R.to_booktabs(
            t5x[["cell", "stratum", "estimand", "estimate", "pct_of_ref", "CI95 (%)", "p", "n_rows"]],
            "T5. Estimands by stratum (observed vs zero-filled targets; outbreak vs not), pooled h and "
            "years; per-year strata in the CSV", "tab:T5", 4))
        made["T5"] = "T5_strata"

    # ---------------- T6 secondary arms
    pairs = [("BR_S1_3seeds", "BR_S1"), ("BR_S1_yref", "BR_S1"), ("BR_S1_delay2", "BR_S1"),
             ("BR_S1_ctrlC3", "BR_S1"), ("BR_S1_ctrlC6", "BR_S1"), ("BR_S1_perlevel", "BR_S1"),
             ("TW_S1_BRparams", "TW_S1")]
    t6 = []
    for v, p in pairs:
        for e in ("G_emb", "G_id", "G_excess"):
            if byid.get(v, {}).get("estimands") and e not in byid[v]["estimands"]:
                continue
            rv, rp = pick(est, v, e), pick(est, p, e)
            t6.append({"variant": v, "vs": p, "estimand": e,
                       "variant_desc": byid.get(v, {}).get("desc", ""),
                       "variant_status": status.get(v, {}).get("status", "n/a"),
                       "primary_status": status.get(p, {}).get("status", "n/a"),
                       "variant_pct": rv.pct_of_ref if rv is not None else np.nan,
                       "variant_lo95_pct": rv.lo95_pct if rv is not None else np.nan,
                       "variant_hi95_pct": rv.hi95_pct if rv is not None else np.nan,
                       "variant_p": rv.p if rv is not None else np.nan,
                       "variant_cls": rv.cls if rv is not None else "pending",
                       "primary_pct": rp.pct_of_ref if rp is not None else np.nan,
                       "primary_cls": rp.cls if rp is not None else "pending",
                       "variant_horizons": ",".join(map(str, infos.get(v, {}).get("horizons", [])))})
    t6 = pd.DataFrame(t6)
    R.write_table(t6, T, "T6a_sensitivities",
                  "T6a. Sensitivity variants vs the primary cell (estimate as % of WIS(L3), 95% CI)", 3,
                  tex_cols=["variant", "vs", "estimand", "variant_pct", "variant_lo95_pct",
                            "variant_hi95_pct", "variant_cls", "primary_pct", "primary_cls"])
    nh = [c["id"] for c in cells if c["arm"] == "no-history"]
    t6b = est[est.cell.isin(nh) & (est.stratum == "all") & (est.test_year == "pooled")]
    t6b = t6b[[c for c in keep if c in t6b]]
    nhl = lad[lad.cell.isin(nh)]
    t6b.to_csv(T / "T6b_nohist_estimands.csv", index=False)
    nhl.to_csv(T / "T6c_nohist_ladder.csv", index=False)
    if not nhl.empty:
        (T / "T6c_nohist_ladder.tex").write_text(R.to_booktabs(
            nhl[nhl.horizon == "pooled"][["cell", "label", "wis_log", "cov_40", "cov_80"]],
            "T6c. No-history arm ladder (pooled h, mean log1p WIS)", "tab:T6c", 4))
    made["T6"] = "T6a_sensitivities, T6b_nohist_estimands, T6c_nohist_ladder"

    # ---------------- figures
    fr = t1.rename(columns={"pct_of_WIS_ref": "pct"})[["cell", "status", "pct", "lo95_pct", "hi95_pct",
                                                      "lo90_pct", "hi90_pct"]]
    secs = []
    for c in cells:
        if c["group"] != "primary":
            r = pick(est, c["id"], "G_excess")
            if r is not None and not c.get("estimands"):
                secs.append({"cell": c["id"], "status": "available", "pct": r.pct_of_ref,
                             "lo95_pct": r.lo95_pct, "hi95_pct": r.hi95_pct,
                             "lo90_pct": r.lo90_pct, "hi90_pct": r.hi90_pct})
    figs = {}
    try:
        figs["F1"] = R.fig_forest(fr.astype({c: float for c in fr.columns[2:]}),
                                  pd.DataFrame(secs, columns=fr.columns), F)
        br = "BR_S1" if "BR_S1" in set(lad.cell) else "BR_S1_perlevel"
        figs["F2"] = R.fig_ladder(lad, [br, "CO_S1", "PE_S1", "TW_S1"], F, "F2_ladder_S1",
                                  "F2. S1 ladder per country (mean log1p WIS; C* = selected control)",
                                  R.LADDER_ORDER, cstars)
        figs["F3"] = R.fig_per_year(est, [br, "CO_S1", "PE_S1", "TW_S1", "TW_S1_BRparams"], F)
        figs["F4"] = R.fig_ladder(lad, nh, F, "F4_nohist_ladder",
                                  "F4. No-history arm ladder (mean log1p WIS)",
                                  ["N2", "N3", "N4", "N3+C1", "N4+C1", "N3+C*", "N4+C*"], cstars)
    except Exception as e:  # noqa: BLE001
        log(f"figure error: {e!r}\n{traceback.format_exc()}")

    # ---------------- brief
    write_brief(Path(a.brief), cells, status, est, t1, t6, lad, made, figs, infos,
                "" if a.no_scheduler else scheduler_status(), T, F)
    log(f"done: {sum(s['status'] == 'available' for s in status.values())} cells available, "
        f"brief at {a.brief}")
    return 0


def _interp(r, a_name, b_name) -> str:
    d = "improves on" if r.estimate > 0 else "is worse than"
    return (f"{b_name} {d} {a_name} by {abs(r.pct_of_ref):.2f}% of WIS(ref) "
            f"(95% CI {r.lo95_pct:+.2f} to {r.hi95_pct:+.2f}%; p = {r.p:.3f}; MDE {r.mde_pct:.2f}%): "
            f"**{r.cls}**, i.e. {CLS_TEXT.get(r.cls, r.cls)}.")


def write_brief(path, cells, status, est, t1, t6, lad, made, figs, infos, sched, T, F):
    L = ["# RESULTS BRIEF (auto-generated)", "",
         f"Generated {dt.datetime.now():%Y-%m-%d %H:%M} by `scripts/analysis/make_results.py`. "
         "Do not edit by hand: re-run the script. All numbers are log1p-scale WIS; a gain is "
         "positive when the second model has the lower WIS. Percentages are of WIS(L3) "
         "(WIS(N3) in the no-history arm). Inference: DM test with EWC long-run variance and "
         "HLN correction on the weekly cross-unit mean loss difference; TOST against a ±1% margin "
         "(90% CI); MDE at 80% power. See `docs/methods/results_kit.md`.", "",
         "Key: **G_emb** = WIS(L3) − WIS(L4) (raw AlphaEarth gain); **G_id** = WIS(L3) − WIS(L3+C*) "
         "(gain from a pure location/ID control); **G_excess** = WIS(L3+C*) − WIS(L4+C*) (primary: "
         "what AlphaEarth adds beyond the best ID control).", "",
         "## 1. Status of every cell", "",
         "| cell | group | description | C* | status | what is missing |", "|---|---|---|---|---|---|"]
    for c in cells:
        s = status[c["id"]]
        miss = "; ".join(f"{r}: {v}" for r, v in s["roles"].items() if v != "complete")
        if s.get("error"):
            miss = "ERROR " + s["error"]
        L.append(f"| {c['id']} | {c['group']}/{c['arm']} | {c['desc']} | {c.get('cstar') or ''} | "
                 f"{s['status']} | {miss} |")
    n_av = int((t1.status == "available").sum())
    L += ["", f"Primary family: **{n_av} of {len(t1)} cells available**. Holm p-values are over the "
          f"available cells only and are provisional until all {len(t1)} are in; `p_bonf14` in T1 is "
          "the conservative bound.", "", "## 2. Headline numbers", ""]
    for c in cells:
        cid = c["id"]
        if not str(status[cid]["status"]).startswith("available") or est.empty:
            continue
        rows = est[(est.cell == cid)]
        if rows.empty:
            continue
        a3 = "N3" if c.get("ref") == "N3" else "L3"
        a4 = a3.replace("3", "4")
        L.append(f"### {cid}: {c['desc']} (C* = {c.get('cstar') or 'n/a'})")
        info = infos.get(cid, {})
        L.append(f"Rows scored {info.get('rows_scored', '?'):,}; test years {info.get('test_years')}; "
                 f"horizons {info.get('horizons')}; seeds {info.get('seeds')}; zero-filled share "
                 f"{info.get('zero_filled_share', np.nan):.2f}; outbreak share {info.get('outbreak_share', np.nan):.3f}.")
        L.append("")
        for e, (x, y) in {"G_excess": (f"{a3}+C*", f"{a4}+C*"), "G_emb": (a3, a4),
                          "G_id": (a3, f"{a3}+C*")}.items():
            r = pick(est, cid, e)
            if r is not None:
                L.append(f"- **{e}** {ci_txt(r)}: {_interp(r, x, y)}")
        ids = pick(est, cid, "ID_share")
        if ids is not None:
            v = ids.estimate
            L.append(f"- **ID share**: " + (f"{float(v):.2f}" if pd.notna(v) and str(v) != "nan"
                                             else str(ids.reason)))
        lp = lad[(lad.cell == cid) & (lad.horizon == "pooled")]
        if not lp.empty:
            best = lp.sort_values("wis_log").iloc[0]
            L.append(f"- Ladder (pooled h): " + ", ".join(f"{r.label} {r.wis_log:.4f}" for r in lp.itertuples())
                     + f". Best = {best.label}. 80% coverage {lp.cov_80.min():.2f}–{lp.cov_80.max():.2f} "
                     f"overall, {lp.cov_80_nonzero.min():.2f}–{lp.cov_80_nonzero.max():.2f} on non-zero targets.")
        st = est[(est.cell == cid) & (est.estimand == "G_excess") & (est.test_year == "pooled")
                 & (est.stratum.isin(["observed", "zero_filled", "outbreak"]))]
        if not st.empty and not c.get("estimands"):
            L.append("- G_excess by stratum: " + "; ".join(
                f"{r.stratum} {r.pct_of_ref:+.2f}% [{r.lo95_pct:+.2f}, {r.hi95_pct:+.2f}]" for r in st.itertuples()))
        if info.get("ladder_skipped"):
            L.append(f"- Ladder rungs not yet available: {'; '.join(info['ladder_skipped'])}")
        L.append("")
    if not t6.empty:
        L += ["## 3. Secondary comparisons (T6a)", "",
              "| variant | vs | estimand | variant % [95% CI] | class | primary % | primary class |",
              "|---|---|---|---|---|---|---|"]
        for r in t6.itertuples():
            v = (f"{r.variant_pct:+.2f} [{r.variant_lo95_pct:+.2f}, {r.variant_hi95_pct:+.2f}]"
                 if np.isfinite(r.variant_pct) else "pending")
            p = f"{r.primary_pct:+.2f}" if np.isfinite(r.primary_pct) else "pending"
            L.append(f"| {r.variant} | {r.vs} | {r.estimand} | {v} | {r.variant_cls} | {p} | {r.primary_cls} |")
        L += ["", "Note: the controls panel and extra-seed variants are scored on h1/h4 rows only "
              "(spatial-split horizons), so they are not row-identical to the h1–h4 primary.", ""]
    L += ["## 4. Where everything is", "",
          f"Tables (`{T}/`, each as .csv and a LaTeX booktabs fragment .tex):", "",
          "- `T1_primary_family` — 14 primary cells: G_excess, % of WIS(L3), 95%/90% CI, DM p, Holm p "
          "(available cells), p_bonf14, TOST class, MDE.",
          "- `T2_ladder` (+ `T2_ladder_long.csv`) — L0–L4, L3+C*, L4+C* per cell: WIS per horizon and "
          "pooled; 40/80% coverage, overall and on non-zero targets.",
          "- `T3_estimands` — G_emb / G_id / G_excess / ID share per cell × horizon and per test year (CSV).",
          "- `T4_cstar_selection` — every control candidate at the 2019 origin, mean ± SD over seeds, chosen C*.",
          "- `T5_strata` — estimands for observed vs zero-filled targets and outbreak vs non-outbreak weeks, "
          "pooled and per year (CSV).",
          "- `T6a_sensitivities` — extra seeds, yearly_ref: origin, report delay 2, controls panel C3/C6, "
          "per-level tuning, TW with BR params; `T6b_nohist_estimands`, `T6c_nohist_ladder` — no-history arm.",
          "", f"Figures (`{F}/`, PDF + PNG):", ""]
    fdesc = {"F1": "forest plot of G_excess (% of WIS(L3)), 95% and 90% CI, ±1% band; all cells",
             "F2": "S1 ladder per country", "F3": "per-test-year G_emb and G_excess, S1 cells",
             "F4": "no-history arm ladder"}
    for k, d in fdesc.items():
        L.append(f"- `{figs.get(k) or k}` — {d}" + ("" if figs.get(k) else " (**pending: no data yet**)"))
    L += ["", "Per-cell intermediate results: `runs/analysis_cache/<cell>/` (est.parquet, ladder.parquet, "
          "info.json with row counts, exclusions and seeds).", ""]
    if sched:
        L += ["## 5. Compute status (scheduler snapshot)", "", "```", sched, "```", ""]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(L))


if __name__ == "__main__":
    sys.exit(main())
