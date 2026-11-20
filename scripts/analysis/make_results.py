#!/usr/bin/env python
"""One-command results kit for Paper 1 ("Place or Placeholder?").

Usage (repo root, after `source env.sh`):
    nice -n 19 python scripts/analysis/make_results.py [--only CELL ...] [--force]
        [--n-boot 0] [--no-scheduler] [--out-tables docs/results/tables]
        [--out-figures docs/results/figures] [--brief docs/results/RESULTS_BRIEF.md]
        [--cache runs/analysis_cache]

v3 (2026-11-18, post-review; deviations rows 24-32): primary scored rows = manifest `row_filter`
(origin_year), Taiwan 2021 via `add_test_years`, three strata with additive contributions,
T1 with G_emb/G_id/absolute WIS/Holm-adjusted TOST/plain labels/robustness columns (EWC B=4,
IAAFT-calibrated p, delta-method CI, case scale, unfiltered rows), margin table, supporting tables
S1-S8 and figures F1-F4. Each cell is computed in its own worker subprocess (memory is returned
to the OS after every cell); --in-process turns that off.

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
from pop.eval.stats import holm, tost_p  # noqa: E402

N_FAMILY = 14       # overwritten by the manifest's family_size
MARGINS = (0.5, 1.0, 2.0)
LOSS_RULE = ("A cell counts as a **loss** (gain) when its G_excess is negative (positive) and the "
             "Holm-adjusted DM p over the 14-cell family is < .05; a loss is **small** when the point "
             "estimate is inside ±1% of WIS(L3). Nominal (unadjusted) p < .05 alone is reported as "
             "'nominal', never counted. While a family cell is pending, Holm runs over the available "
             "cells and the count is provisional.")
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


# ------------------------------------------------------------------ v3 helpers
def plain_label(est_pct, lo90_pct, hi90_pct, p_raw, p_holm, tost_holm, m=1.0) -> str:
    """Plain-language label (review RA4 vocabulary; review_sens.equivalence_label)."""
    from review_sens import equivalence_label
    return equivalence_label(est_pct, lo90_pct, hi90_pct, p_raw, p_holm, tost_holm, m)


def holm_class(est, lo95, hi95, p_holm, tost_holm) -> str:
    """Holm-adjusted class: 'equivalent' if the Holm-adjusted TOST p < .05 (±1%); else
    'inferior'/'superior' if the Holm-adjusted DM p < .05 (95% CI excludes 0); else
    'inconclusive'."""
    if tost_holm < 0.05:
        return "equivalent"
    if p_holm < 0.05 and hi95 < 0:
        return "inferior"
    if p_holm < 0.05 and lo95 > 0:
        return "superior"
    return "inconclusive"


def holm_avail(p: pd.Series) -> pd.Series:
    out = pd.Series(np.nan, index=p.index)
    ok = p.notna()
    if ok.any():
        out[ok] = holm(p[ok].astype(float).to_numpy())
    return out


def xrow(extras: dict, cid: str, name: str, estimand: str | None = "G_excess"):
    d = extras.get(cid, {}).get(name)
    if d is None or d.empty:
        return None
    if estimand is not None and "estimand" in d:
        d = d[d.estimand == estimand]
    return None if d.empty else d.iloc[0]


def _f(r, k):
    try:
        v = r[k]
        return float(v) if v is not None else np.nan
    except (KeyError, TypeError, ValueError):
        return np.nan


def cat_extra(extras: dict, name: str, cells=None) -> pd.DataFrame:
    fs = [x[name] for c, x in extras.items() if name in x and (cells is None or c in cells)]
    return pd.concat(fs, ignore_index=True) if fs else pd.DataFrame()


def cell_label(cid: str) -> str:
    """'BR_S1' -> 'Brazil, S1 new years' (plain label with the split code kept)."""
    cc, _, rest = cid.partition("_")
    sp, _, tail = rest.partition("_")
    lab = f"{R.COUNTRY_NAME.get(cc, cc)}, {sp} {R.SPLIT_NAME.get(sp, '')}".strip()
    return lab + (f" ({tail})" if tail else "")


def run_worker(a, cid: str) -> None:
    """Compute one cell in a fresh interpreter (`make_results.py --worker CELL`): all memory is
    returned to the OS afterwards and no forked thread state is inherited."""
    cmd = [sys.executable, str(Path(__file__).resolve()), "--worker", cid, "--root", str(a.root),
           "--manifest", a.manifest, "--cache", a.cache, "--n-boot", str(a.n_boot),
           "--block-len", str(a.block_len), "--margin-rel", str(a.margin_rel), "--extras", a.extras,
           "--iaaft-reps", str(a.iaaft_reps)]
    if a.registry:
        cmd += ["--registry", a.registry]
    if a.no_exclusions:
        cmd.append("--no-exclusions")
    cmd += ["--exclusions", a.exclusions]
    r = subprocess.run(cmd)
    if r.returncode != 0:
        raise RuntimeError(f"cell worker for {cid} exited with code {r.returncode}")


# ------------------------------------------------------------------ main
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--manifest", default="configs/primary_cells.yaml")
    ap.add_argument("--only", nargs="*", default=None, help="compute only these cell ids")
    ap.add_argument("--force", action="store_true", help="ignore the cache")
    ap.add_argument("--n-boot", type=int, default=0)
    ap.add_argument("--block-len", type=int, default=52)
    ap.add_argument("--margin-rel", type=float, default=0.01)
    ap.add_argument("--extras", choices=K.EXTRAS_LEVELS, default="all",
                    help="none: estimands, ladder, unfiltered rows, B=4, delta CI, strata; cheap: + "
                         "IAAFT p, case scale, weighting, outbreak, per-year, baselines; all: + "
                         "recalibration, q0.9 mechanism, embedding distance (reads forecasts)")
    ap.add_argument("--iaaft-reps", type=int, default=2000)
    ap.add_argument("--in-process", action="store_true", help="no worker subprocess per cell")
    ap.add_argument("--worker", default=None, help=argparse.SUPPRESS)
    ap.add_argument("--no-scheduler", action="store_true")
    ap.add_argument("--no-exclusions", action="store_true")
    ap.add_argument("--exclusions", choices=["v1", "v2"], default="v2",
                    help="v2 (primary since row 34) = v1 + unit-week exclusions (Espirito Santo "
                         "false zeros, target weeks >= 2019-12-29); v1 is also reported as a sensitivity column")
    ap.add_argument("--cache", default="runs/analysis_cache")
    ap.add_argument("--out-tables", default="docs/results/tables")
    ap.add_argument("--out-figures", default="docs/results/figures")
    ap.add_argument("--brief", default="docs/results/RESULTS_BRIEF.md")
    ap.add_argument("--control-panel", default="docs/results/review/RE_control_panel.csv")
    ap.add_argument("--root", default=str(ROOT), help="repo root (tests pass a temp dir)")
    ap.add_argument("--registry", default=None, help="JSON cell list instead of the built-in registry (tests)")
    a = ap.parse_args(argv)
    if a.registry:
        a.registry = str(Path(a.registry).resolve())
    a.root = str(Path(a.root).resolve())
    os.chdir(a.root)
    log = lambda m: print(m, flush=True)  # noqa: E731
    global N_FAMILY

    if a.registry:
        cells = json.loads(Path(a.registry).read_text())
        if Path(a.manifest).exists():   # horizons/filter from the manifest even for a JSON registry
            import yaml
            man = yaml.safe_load(Path(a.manifest).read_text())
            C.PRIMARY_HORIZONS = sorted(int(h) for h in man.get("primary_horizons", [1, 4]))
            C.SECONDARY_HORIZONS = sorted(int(h) for h in man.get("secondary_horizons", [1, 2, 3, 4]))
            C.ROW_FILTER = man.get("row_filter")
            C.FAMILY_SIZE = int(man.get("family_size", N_FAMILY))
        for c in cells:
            c.setdefault("primary_horizons", list(C.PRIMARY_HORIZONS))
            c.setdefault("secondary_horizons", list(C.SECONDARY_HORIZONS) if c.get("split") == "S1"
                         else None)
            c.setdefault("row_filter", C.ROW_FILTER)
            c.setdefault("flags", [])
    else:
        cells = C.build_registry(a.manifest)
    N_FAMILY = int(getattr(C, "FAMILY_SIZE", N_FAMILY) or N_FAMILY)
    hlab = K.hlabel(C.PRIMARY_HORIZONS)
    slab = K.sec_label(C.SECONDARY_HORIZONS)
    xdir = Path(f"data/processed/exclusions_{a.exclusions}")
    if a.no_exclusions:
        excl = {"exclude_units": None, "exclude_weeks": None, "late_entry": None,
                "week_actions": ("exclude",)}
    elif a.exclusions == "v1":
        excl = {"exclude_units": str(DEFAULT_UNITS), "exclude_weeks": str(DEFAULT_WEEKS),
                "late_entry": None, "week_actions": ("exclude",)}
    else:
        if not (xdir / "unit_week_exclusions.csv").exists():
            raise SystemExit(f"{xdir} missing: run scripts/analysis/build_exclusions_v2.py first")
        excl = {"exclude_units": str(xdir / "no_geometry_units.csv"),
                "exclude_weeks": str(xdir / "incomplete_weeks.csv"), "late_entry": None,
                "week_actions": ("exclude",), "unit_weeks": str(xdir / "unit_week_exclusions.csv")}
    kw = dict(margin_rel=a.margin_rel, n_boot=a.n_boot, block_len=a.block_len, extras=a.extras,
              iaaft_reps=a.iaaft_reps)
    if a.worker:     # child mode: compute one cell, write its cache, exit
        c = {x["id"]: x for x in cells}[a.worker]
        K.compute_cell(c, cache_root=Path(a.cache), excl=excl, force=True, log=log, **kw)
        return 0
    status, ests, lads, infos, extras = {}, [], [], {}, {}
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
            cdir = Path(a.cache) / c["id"]
            key = K.cell_key(c, excl, K.cell_opts(c, **{k: v for k, v in kw.items()}))
            force = a.force and (not a.only or c["id"] in a.only)
            if not force and K.cache_valid(cdir, key):
                log(f"  {c['id']}: cache hit ({key})")
            elif a.only and c["id"] not in a.only:
                log(f"  {c['id']}: cache stale, not recomputed (--only); using the old cache")
                status[c["id"]]["status"] = "available (stale cache: --only)"
            else:
                job = dict(cell=c, cache_root=Path(a.cache), excl=excl, force=True, log=log, **kw)
                if a.in_process:
                    K.compute_cell(**job)
                else:
                    run_worker(a, c["id"])
            res = K.load_cached(cdir)
            ests.append(res["est"])
            lads.append(res["ladder"])
            infos[c["id"]] = res["info"]
            extras[c["id"]] = res["extras"]
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
    cstars = {c["id"]: c.get("cstar") for c in cells}             # raw (None = no valid C*)
    cstar_txt = {c["id"]: C.cstar_label(c) for c in cells}          # display
    T, F = Path(a.out_tables), Path(a.out_figures)
    T.mkdir(parents=True, exist_ok=True)
    made = {}

    # ---------------- T1 primary family (v3)
    prim = [c for c in cells if c["group"] == "primary"]
    rows = []
    for c in prim:
        cid = c["id"]
        r = pick(est, cid, "G_excess")
        av = str(status[cid]["status"]).startswith("available") and r is not None
        base = {"cell": cid, "cell_name": cell_label(cid), "country": c["country"], "split": c["split"],
                "C_star": cstar_txt[cid], "status": status[cid]["status"] if av else "pending",
                "flags": "; ".join(c.get("flags", [])), "horizons": hlab,
                "row_filter": c.get("row_filter") or "none"}
        if not av:
            rows.append({**base, "missing": "; ".join(f"{k}: {v}" for k, v in
                                                       status[cid]["roles"].items() if v != "complete")})
            continue
        info = infos.get(cid, {})
        re_, ri = pick(est, cid, "G_emb"), pick(est, cid, "G_id")
        w3 = float(r["wis_ref"])
        row = {**base, "test_years": ",".join(map(str, info.get("test_years", []))),
               "n_rows": int(r["n_rows"]), "T_weeks": int(r["T"]), "n_seeds": r["n_seeds"],
               "seed_sd": r["seed_sd"], "WIS_L3": w3}
        if re_ is not None and ri is not None:
            row.update(WIS_L4=w3 - float(re_["estimate"]), WIS_L3C=w3 - float(ri["estimate"]))
            row["WIS_L4C"] = row["WIS_L3C"] - float(r["estimate"])
        for e, q in (("G_emb", re_), ("G_id", ri)):
            if q is not None:
                row.update({e: q["estimate"], f"{e}_pct": q["pct_of_ref"], f"{e}_lo95_pct": q["lo95_pct"],
                            f"{e}_hi95_pct": q["hi95_pct"], f"{e}_p": q["p"], f"{e}_class": q["cls"]})
        row.update({"G_excess": r["estimate"], "pct_of_WIS_ref": r["pct_of_ref"], "se": r["se"],
                    "df": r["df"], "lo95": r["lo95"], "hi95": r["hi95"], "lo90": r["lo90"],
                    "hi90": r["hi90"], "lo95_pct": r["lo95_pct"], "hi95_pct": r["hi95_pct"],
                    "lo90_pct": r["lo90_pct"], "hi90_pct": r["hi90_pct"], "DM_p": r["p"],
                    "TOST_p": r["tost_p"], "TOST_class": r["cls"], "MDE": r["mde"],
                    "MDE_pct": r["mde_pct"], "WIS_ref": w3, "missing": ""})
        rb = xrow(extras, cid, "robust")
        if rb is not None:
            row.update(B4_p=_f(rb, "B4_p"), B4_lo95_pct=_f(rb, "B4_lo95_pct"),
                       B4_hi95_pct=_f(rb, "B4_hi95_pct"), p_iaaft=_f(rb, "p_iaaft"),
                       iaaft_reps=_f(rb, "iaaft_reps"), delta_lo95_pct=_f(rb, "delta_lo95_pct"),
                       delta_hi95_pct=_f(rb, "delta_hi95_pct"), delta_lo90_pct=_f(rb, "delta_lo90_pct"),
                       delta_hi90_pct=_f(rb, "delta_hi90_pct"))
        cs = xrow(extras, cid, "casescale")
        if cs is not None:
            row.update(case_pct=_f(cs, "pct_of_ref"), case_lo95_pct=_f(cs, "lo95_pct"),
                       case_hi95_pct=_f(cs, "hi95_pct"), case_p=_f(cs, "p"), case_WIS_L3=_f(cs, "wis_ref"))
        e1 = xrow(extras, cid, "excl_v1")
        if e1 is not None:
            row.update(exclv1_pct=_f(e1, "pct_of_ref"), exclv1_lo95_pct=_f(e1, "lo95_pct"),
                       exclv1_hi95_pct=_f(e1, "hi95_pct"), exclv1_p=_f(e1, "p"),
                       exclv1_class=e1["cls"], exclv1_n_rows=_f(e1, "n_rows"),
                       unit_week_share_dropped=info.get("unit_week_share_dropped_primary", 0.0))
        uf = xrow(extras, cid, "unfiltered")
        if uf is not None:
            row.update(unfiltered_pct=_f(uf, "pct_of_ref"), unfiltered_lo95_pct=_f(uf, "lo95_pct"),
                       unfiltered_hi95_pct=_f(uf, "hi95_pct"), unfiltered_p=_f(uf, "p"),
                       unfiltered_class=uf["cls"], unfiltered_n_rows=_f(uf, "n_rows"))
        rs = est[(est.cell == cid) & (est.estimand == "G_excess") & (est.test_year == "pooled")
                 & (est.stratum == "all") & est.horizon.str.startswith("pooled_h")]
        if len(rs):   # secondary (S1): pooled over the secondary horizons; NOT in the Holm family
            q = rs.iloc[0]
            row.update({"sec_horizons": q.horizon, "sec_years": ",".join(
                map(str, info.get("secondary_years") or [])), "sec_G_excess": q.estimate,
                "sec_pct": q.pct_of_ref, "sec_lo95_pct": q.lo95_pct, "sec_hi95_pct": q.hi95_pct,
                "sec_DM_p": q.p, "sec_TOST_class": q.cls})
        rows.append(row)
    t1 = pd.DataFrame(rows)
    for col in ("G_excess", "pct_of_WIS_ref", "lo95_pct", "hi95_pct", "lo90_pct", "hi90_pct", "DM_p",
                "MDE_pct", "TOST_class", "B4_p", "p_iaaft", "se", "df", "WIS_ref", "lo95", "hi95",
                "G_emb_pct", "G_id_pct", "case_pct", "unfiltered_pct", "delta_lo95_pct", "exclv1_pct"):
        if col not in t1:
            t1[col] = np.nan
    av = t1.status.astype(str).str.startswith("available")
    n_av = int(av.sum())
    complete = n_av == N_FAMILY and len(t1) == N_FAMILY
    t1["n_family_available"] = n_av
    t1["family_complete"] = complete
    t1["Holm_p"] = holm_avail(t1.DM_p.where(av))
    t1["Holm_p_available"] = t1.Holm_p          # v2 column name kept
    t1["p_bonf14"] = np.where(av, np.minimum(1.0, N_FAMILY * t1.DM_p.astype(float)), np.nan)
    t1["B4_Holm_p"] = holm_avail(t1.B4_p.where(av))
    t1["p_iaaft_Holm"] = holm_avail(t1.p_iaaft.where(av))
    margin_rows = []
    for m in MARGINS:
        tag = f"{m:g}".replace(".", "p")
        tp = pd.Series([tost_p(e, s, d, m / 100 * w) if ok else np.nan
                        for e, s, d, w, ok in zip(t1.G_excess, t1.se, t1.df, t1.WIS_ref, av)], index=t1.index)
        th = holm_avail(tp)
        within = (t1.lo90_pct.astype(float) > -m) & (t1.hi90_pct.astype(float) < m)
        lab = [plain_label(e, lo, hi, p, ph, t, m) if ok else "pending" for e, lo, hi, p, ph, t, ok in
               zip(t1.pct_of_WIS_ref, t1.lo90_pct, t1.hi90_pct, t1.DM_p, t1.Holm_p, th, av)]
        if m == 1.0:
            t1["TOST_p_Holm"] = th
            t1["TOST_class_Holm"] = [holm_class(e, lo, hi, ph, t) if ok else "pending" for e, lo, hi, ph, t, ok in
                                     zip(t1.G_excess, t1.lo95, t1.hi95, t1.Holm_p, th, av)]
            t1["plain_label"] = lab
        from review_sens import near_margin
        for i in t1.index[av]:
            margin_rows.append({"cell": t1.cell[i], "cell_name": t1.cell_name[i],
                                "margin_pct": m, "G_excess_pct": t1.pct_of_WIS_ref[i],
                                "lo90_pct": t1.lo90_pct[i], "hi90_pct": t1.hi90_pct[i],
                                "TOST_p": tp[i], "TOST_p_Holm": th[i], "within_unadjusted": bool(within[i]),
                                "within_Holm": bool(th[i] < 0.05),
                                "near_margin": near_margin(t1.lo90_pct[i], t1.hi90_pct[i], m),
                                "plain_label": lab[list(t1.index).index(i)],
                                "n_family_available": n_av})
    t1["loss_or_gain"] = [
        ("pending" if not ok else
         ("small loss" if (e < 0 and ph < 0.05 and abs(pc) < 1) else
          "loss" if (e < 0 and ph < 0.05) else
          "small gain" if (e > 0 and ph < 0.05 and abs(pc) < 1) else
          "gain" if (e > 0 and ph < 0.05) else
          "nominal only" if p < 0.05 else "none"))
        for e, pc, p, ph, ok in zip(t1.G_excess, t1.pct_of_WIS_ref, t1.DM_p, t1.Holm_p, av)]
    t1.to_csv(T / "T1_primary_family.csv", index=False)
    t1x = t1.copy()
    fmt_ci = lambda v, l, h: f"{v:+.2f} [{l:+.2f}, {h:+.2f}]" if np.isfinite(v) else ""  # noqa: E731
    t1x["G_excess % [95% CI]"] = [fmt_ci(*x) for x in zip(t1x.pct_of_WIS_ref.astype(float),
                                                          t1x.lo95_pct.astype(float), t1x.hi95_pct.astype(float))]
    t1x["G_emb %"] = t1x.G_emb_pct
    t1x["G_id %"] = t1x.G_id_pct
    t1x["WIS L3+C*"] = t1x.get("WIS_L3C", np.nan)
    t1x["WIS L4+C*"] = t1x.get("WIS_L4C", np.nan)
    t1x["DM p"], t1x["Holm p"] = t1x.DM_p, t1x.Holm_p
    t1x["Holm TOST"] = t1x.TOST_class_Holm
    t1x["B=4 p"], t1x["IAAFT p"] = t1x.B4_p, t1x.p_iaaft
    t1x["case %"] = t1x.case_pct
    t1x["all rows %"] = t1x.unfiltered_pct
    t1x["v1 excl %"] = t1x.exclv1_pct
    pend = "" if complete else f" PROVISIONAL: Holm over the {n_av} available of {N_FAMILY} cells."
    (T / "T1_primary_family.tex").write_text(R.to_booktabs(
        t1x[["cell_name", "C_star", "WIS L3+C*", "WIS L4+C*", "G_excess % [95% CI]", "G_emb %", "G_id %",
             "DM p", "Holm p", "Holm TOST", "B=4 p", "IAAFT p", "case %", "all rows %", "v1 excl %"]],
        f"T1. Primary family (rows: forecast origin in the target's epi-year). G_excess = "
        f"WIS(L3+C*) - WIS(L4+C*), log1p WIS pooled over {hlab}, % of WIS(L3); DM/EWC+HLN; Holm "
        f"over the family; Holm TOST = class from the Holm-adjusted TOST at ±1%; B=4 p = EWC with "
        f"4 cosine terms; IAAFT p = surrogate-calibrated; case % = G_excess on the case scale; all "
        f"rows % = without the origin-year filter; v1 excl % = without the Espirito Santo unit-week "
        f"exclusion (Brazil cells).{pend}", "tab:T1", 4))
    tm = pd.DataFrame(margin_rows)
    R.write_table(tm, T, "T1b_margin_sensitivity",
                  f"T1b. Equivalence margin sensitivity (0.5/1/2% of WIS(L3)): unadjusted and "
                  f"Holm-adjusted TOST over the available family cells ({n_av} of {N_FAMILY})", 4,
                  tex_cols=["cell", "margin_pct", "G_excess_pct", "lo90_pct", "hi90_pct", "TOST_p",
                            "TOST_p_Holm", "within_unadjusted", "within_Holm", "near_margin"]
                  if len(tm) else None)
    made["T1"] = "T1_primary_family, T1b_margin_sensitivity"

    # ---------------- T2 ladder
    if not lad.empty:
        lw = lad.pivot_table(index=["cell", "label"], columns="horizon", values="wis_log", sort=False)
        lw.columns = [f"WIS h{c}" if str(c).isdigit() else
                      (f"WIS pooled {hlab}" if c == "pooled" else f"WIS {c} (secondary)")
                      for c in lw.columns]
        lp = lad[lad.horizon == "pooled"].set_index(["cell", "label"])[["cov_40", "cov_80", "cov_80_nonzero", "n_rows"]]
        t2w = lw.join(lp).reset_index()
        t2w.insert(2, "C_star", t2w.cell.map(cstar_txt).fillna(""))
        lad.to_csv(T / "T2_ladder_long.csv", index=False)
        hcols = sorted([c for c in t2w.columns if c.startswith("WIS h")]) + [f"WIS pooled {hlab}"] \
            + [c for c in t2w.columns if c.endswith("(secondary)")]
        R.write_table(t2w, T, "T2_ladder",
                      f"T2. Ladder: mean log1p WIS per horizon, pooled over the primary horizons "
                      f"{hlab} and (S1, secondary) over {slab.replace('pooled_', '')}; 40%/80% "
                      f"interval coverage (pooled {hlab}; cov_80_nonzero = rows with cases > 0); "
                      "rows scored by every rung of the cell (origin-year rows; the TW S1 L0-L2 rungs "
                      "include the 2021 runs via the manifest key ladder_runs, L2 = shared parameters)",
                      4, tex_cols=["cell", "label"] + hcols + ["cov_40", "cov_80", "cov_80_nonzero"])
        made["T2"] = "T2_ladder"

    # ---------------- T3 estimands
    keep = ["cell", "horizon", "pooled_over", "test_year", "estimand", "estimate", "pct_of_ref", "lo95", "hi95",
            "lo95_pct", "hi95_pct", "lo90_pct", "hi90_pct", "p", "tost_p", "cls", "mde_pct",
            "wis_ref", "n_seeds", "seed_sd", "boot_lo", "boot_hi", "n_rows", "n_weeks", "reason"]
    if not est.empty:
        t3 = est[est.stratum == "all"]
        t3 = t3[[c for c in keep if c in t3]]
        t3x = t3[(t3.test_year == "pooled") & (t3.estimand != "ID_share")].copy()
        t3x["CI95 (%)"] = [f"[{l:+.2f}, {h:+.2f}]" for l, h in zip(t3x.lo95_pct, t3x.hi95_pct)]
        t3.to_csv(T / "T3_estimands.csv", index=False)
        (T / "T3_estimands.tex").write_text(R.to_booktabs(
            t3x[["cell", "estimand", "horizon", "pooled_over", "estimate", "pct_of_ref", "CI95 (%)",
                 "p", "cls"]],
            f"T3. G_emb, G_id, G_excess per cell and horizon (pooled test years; origin-year rows). "
            f"'pooled' = primary horizons {hlab}; '{slab}' = secondary S1 pooling; pooled_over lists "
            "the horizons. Per-year rows (primary horizons) in the CSV", "tab:T3", 4))
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
        if not ok or not C.selection_ok(s["dir"]):
            sel_rows.append({"cell": c["id"], "candidate": "",
                             "status": "pending" if not ok else C.CSTAR_PENDING})
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
        t4 = pd.DataFrame(sel_rows).drop_duplicates(["cell", "candidate"])
        t4x = t4[t4.status == "done"].copy()
        t4x["mean ± SD"] = [f"{m:.5f} ± {s:.5f}" if np.isfinite(s) else f"{m:.5f}"
                            for m, s in zip(t4x.wis_log_2019.astype(float), t4x.seed_sd.astype(float))]
        t4x["selected"] = t4x.selected.map({True: "C*", False: ""})
        t4.to_csv(T / "T4_cstar_selection.csv", index=False)
        (T / "T4_cstar_selection.tex").write_text(R.to_booktabs(
            t4x[["cell", "candidate", "mean ± SD", "n_seeds", "delta_vs_ref", "selected"]],
            "T4. C* selection at the 2019 origin: mean log1p WIS (pooled h) over seeds; only "
            "selections under rule_version 2 are shown", "tab:T4", 5))
        made["T4"] = "T4_cstar_selection"

    # ---------------- T5 three strata (estimates + additive contributions)
    s3 = cat_extra(extras, "strata3")
    if not s3.empty:
        s3 = s3[s3.cell.isin([c["id"] for c in cells])]
        s3.to_csv(T / "T5_strata.csv", index=False)
        x = s3[(s3.estimand == "G_excess")].copy()
        x["stratum estimate % [95% CI]"] = [fmt_ci(v, l, h) if np.isfinite(v) else "too few weeks/rows"
                                             for v, l, h in zip(x.get("pct_of_ref", np.nan).astype(float),
                                                                x.get("lo95_pct", np.nan).astype(float),
                                                                x.get("hi95_pct", np.nan).astype(float))]
        x["contribution % [95% CI]"] = [fmt_ci(v, l, h) if np.isfinite(l) else f"{v:+.2f}"
                                        for v, l, h in zip(x.contrib_pct, x.contrib_lo95_pct, x.contrib_hi95_pct)]
        x = x[x.cell.isin([c["id"] for c in prim])]
        (T / "T5_strata.tex").write_text(R.to_booktabs(
            x[["cell", "stratum", "row_share", "stratum estimate % [95% CI]", "contribution % [95% CI]",
               "total_pct", "identity_residual"]],
            "T5. G_excess by target type: cases > 0 / zero listed by the source / zero filled by us. "
            "Stratum estimate = the primary estimator on the stratum's rows, % of the stratum's own "
            "WIS(L3); contribution = the stratum's exact additive share of the cell total, % of the "
            "cell's WIS(L3) (contributions sum to the total; residual shown). G_emb and G_id in the CSV",
            "tab:T5", 3))
        made["T5"] = "T5_strata"

    # ---------------- T6 secondary arms
    pairs = [("BR_S1_3seeds", "BR_S1"), ("BR_S1_yref", "BR_S1"), ("BR_S1_delay2", "BR_S1"),
             ("BR_S1_ctrlC3", "BR_S1"), ("BR_S1_ctrlC6", "BR_S1"), ("BR_S1_perlevel", "BR_S1"),
             ("TW_S1_BRparams", "TW_S1")]
    pairs += [(c["id"], c["id"].split("_no")[0]) for c in cells if "_no" in c["id"]]
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
                       "variant_years": ",".join(map(str, infos.get(v, {}).get("test_years", []))),
                       "variant_horizons": ",".join(map(str, infos.get(v, {}).get("horizons", [])))})
    t6 = pd.DataFrame(t6)
    R.write_table(t6, T, "T6a_sensitivities",
                  f"T6a. Sensitivity variants vs the primary cell (estimate as % of WIS(L3), 95% CI; "
                  f"both pooled over the primary horizons {hlab}; origin-year rows)", 3,
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

    # ---------------- supporting tables S1-S8
    pids = [c["id"] for c in prim]
    sup = supporting_tables(extras, est, pids, byid, T, a.control_panel, hlab)
    made.update(sup["made"])

    # ---------------- figures
    figs = {}
    for k, fn in (("F1", lambda: R.fig_forest_v3(t1, F, hlab)),
                  ("F2", lambda: R.fig_strata_contrib(s3[s3.cell.isin(pids)] if not s3.empty else s3, F)),
                  ("F3", lambda: R.fig_distance(sup.get("dist_units"), sup.get("dist_bins"), F)),
                  ("F4", lambda: R.fig_per_year_v3(sup.get("peryear"), F, hlab)),
                  ("FS1", lambda: R.fig_ladder(lad, ["BR_S1", "CO_S1", "PE_S1", "TW_S1"], F, "FS1_ladder_S1",
                                               "Ladder by country, new-years split (S1): mean WIS on log(1 + cases) "
                                               "(C* = the selected control)", R.LADDER_ORDER, cstars)),
                  ("FS2", lambda: R.fig_ladder(lad, nh, F, "FS2_nohist_ladder",
                                               "No-history arm ladder (mean WIS on log(1 + cases))",
                                               ["N2", "N3", "N4", "N3+C1", "N4+C1", "N3+C*", "N4+C*"], cstars))):
        try:
            figs[k] = fn()
        except Exception as e:  # noqa: BLE001
            log(f"figure {k} error: {e!r}\n{traceback.format_exc()}")

    # ---------------- brief
    write_brief(Path(a.brief), cells, status, est, t1, t6, lad, made, figs, infos, extras,
                "" if a.no_scheduler else scheduler_status(), T, F, hlab, slab, sup)
    log(f"done: {sum(str(s['status']).startswith('available') for s in status.values())} cells available, "
        f"brief at {a.brief}")
    return 0


def supporting_tables(extras, est, pids, byid, T, control_panel, hlab) -> dict:
    """S1 baselines, S2 fixed control panel, S3 outbreak, S4 weighting, S5 recalibration,
    S6 q0.9 mechanism, S7 embedding distance, S8 per year (with context flags)."""
    import review_more as RM
    out = {"made": {}}

    def w(df, name, caption, tex_cols=None, nd=4):
        if df is None or df.empty:
            return
        R.write_table(df, T, name, caption, nd, tex_cols=[c for c in (tex_cols or []) if c in df] or None)
        out["made"][name.split("_")[0]] = name

    b = cat_extra(extras, "baselines", pids)
    if not b.empty:
        b = b[b.horizon.isin(["1", "4", "pooled"])]
    w(b, "S1_baselines", f"S1. Baselines and ladder, new-years split: mean log1p WIS (h1, h4, pooled "
      f"{hlab}), relative WIS vs the seasonal naive (L0) and vs LightGBM L1, coverage; rows scored by "
      "every listed model (origin-year rows)",
      ["cell", "label", "horizon", "wis_log", "rel_wis_vs_L0", "cov_80", "cov_80_nonzero"])
    cp = Path(control_panel)
    if cp.exists():
        x = pd.read_csv(cp)
        if "panel_file" not in x.columns:
            x.insert(0, "panel_file", str(cp))
        scoring = (", ".join(sorted(map(str, x["scoring"].dropna().unique())))
                   if "scoring" in x.columns else "see panel file")
        w(x, "S2_control_panel", "S2. Fixed control panel (S1): each control k in place of C*; "
          f"read from {cp} (computed by scripts/analysis/control_panel.py; scoring: {scoring})")
    else:
        out["made"]["S2"] = "S2_control_panel (pending: control panel file not found)"
    o = cat_extra(extras, "outbreak", pids)
    w(o, "S3_outbreak", "S3. G_excess on outbreak vs other weeks (outbreak = cases >= max(unit p90 "
      "of 2013-2019, 5); exploratory, no multiplicity adjustment); outbreak_minus_non = weekly "
      "difference test; outbreak_contribution = additive share of the cell total",
      ["cell", "stratum", "row_share", "pct_of_ref", "lo95_pct", "hi95_pct", "p", "estimate",
       "share_of_total"])
    wt = cat_extra(extras, "weighted", pids)
    w(wt[wt.estimand == "G_excess"] if not wt.empty else wt, "S4_weighted",
      "S4. G_excess with unit weights inside each week: none, population (target year), mean "
      "weekly cases 2013-2017 + 1", ["cell", "weights", "pct_of_ref", "lo95_pct", "hi95_pct", "p", "cls"])
    rc = cat_extra(extras, "recal", pids)
    w(rc, "S5_recalibration", "S5. Causal quantile recalibration of L3+C* and L4+C* (shifts fitted "
      "on earlier test years only; global and median-binned); G_excess and 80% coverage",
      ["cell", "years", "calibration", "pct_of_ref", "lo95_pct", "hi95_pct", "p", "cls",
       "cov80pos_L3+C*", "cov80pos_L4+C*"])
    mc = cat_extra(extras, "mech", pids)
    w(mc, "S6_q90_mechanism", "S6. Zero-case rows: change in the 0.9 quantile (L4+C* minus L3+C*) "
      "and the share of the zero rows' contribution to G_excess that comes from the upper quantiles",
      ["cell", "zero_row_share", "dq90_log", "dq90_log_lo95", "dq90_log_hi95", "dq90_case",
       "G_zero_contrib", "upper_share_of_zero", "q90_share_of_zero"])
    du = cat_extra(extras, "distance_unit_years", pids)
    if not du.empty:
        import review_explore as RX
        units = RX.unit_level(du)
        sp, bins, uq = RX.distance_summaries(units)
        wref = {c: float(pick(est, c, "G_excess")["wis_ref"]) for c in units.cell.unique()
                if pick(est, c, "G_excess") is not None}
        units["G_excess_pct_cell"] = 100 * units.G_excess / units.cell.map(wref)
        bins["G_excess_pct_cell"] = 100 * bins.G_excess / bins.cell.map(wref)
        bins["G_excess_lo95_pct_cell"] = 100 * bins.G_excess_lo95 / bins.cell.map(wref)
        bins["G_excess_hi95_pct_cell"] = 100 * bins.G_excess_hi95 / bins.cell.map(wref)
        w(sp, "S7_embedding_distance", "S7. Held-out districts: Spearman correlation between the "
          "AlphaEarth similarity to the training districts (max / top-5 mean cosine, year y-1) and "
          "the district's gain (exploratory; naive p ignores spatial dependence)",
          ["cell", "estimand", "distance", "spearman_rho", "p_naive", "n_units"])
        bins.to_csv(T / "S7b_embedding_distance_bins.csv", index=False)
        out["dist_units"], out["dist_bins"] = units, bins
    # per year (all three estimands) + context flags
    py = est[(est.stratum == "all") & (est.horizon == "pooled") & (est.test_year != "pooled")
             & est.estimand.isin(["G_emb", "G_id", "G_excess"]) & est.cell.isin(pids)].copy()
    if not py.empty:
        py["country"] = py.cell.map(lambda c: byid[c]["country"])
        py["context"] = [RM.context_flags(c, int(y)) for c, y in zip(py.country, py.test_year)]
        pe = cat_extra(extras, "peryear", pids)
        if not pe.empty:
            pe = pe.assign(test_year=pe.test_year.astype(str))[["cell", "test_year", "positive_share",
                                                                 "mean_log1p_cases"]]
            py = py.merge(pe, on=["cell", "test_year"], how="left")
        if "taiwan" in set(py.country):
            py.loc[(py.country == "taiwan") & (py.test_year == "2021"), "context"] = \
                "Taiwan 2021: no local cases (all-zero year)"
        py = py[["cell", "country", "test_year", "estimand", "estimate", "pct_of_ref", "lo95_pct",
                 "hi95_pct", "p", "cls", "n_rows", "n_weeks", "context"]
                + [c for c in ("positive_share", "mean_log1p_cases") if c in py]]
        w(py, "S8_per_year", f"S8. Gains per test year (pooled {hlab}; % of the year's WIS(L3)) with "
          "context flags", ["cell", "test_year", "estimand", "pct_of_ref", "lo95_pct", "hi95_pct", "p",
                            "context"])
        out["peryear"] = py
    return out


def _interp(r, a_name, b_name) -> str:
    d = "improves on" if r.estimate > 0 else "is worse than"
    return (f"{b_name} {d} {a_name} by {abs(r.pct_of_ref):.2f}% of WIS(ref) "
            f"(95% CI {r.lo95_pct:+.2f} to {r.hi95_pct:+.2f}%; p = {r.p:.3f}; MDE {r.mde_pct:.2f}%): "
            f"**{r.cls}** (unadjusted rule), i.e. {CLS_TEXT.get(r.cls, r.cls)}.")


def _fmt(v, nd=2, sign=True):
    try:
        v = float(v)
    except (TypeError, ValueError):
        return "n/a"
    if not np.isfinite(v):
        return "n/a"
    return f"{v:+.{nd}f}" if sign else f"{v:.{nd}f}"


def _p(v):
    try:
        v = float(v)
    except (TypeError, ValueError):
        return "n/a"
    return "n/a" if not np.isfinite(v) else (f"{v:.2g}" if v < 0.001 else f"{v:.3f}")


def write_brief(path, cells, status, est, t1, t6, lad, made, figs, infos, extras, sched, T, F,
                hlab="h{1,4}", slab="pooled_h1-4", sup=None):
    n_av = int(t1.status.astype(str).str.startswith("available").sum())
    L = ["# RESULTS BRIEF (auto-generated, results kit v3)", "",
         f"Generated {dt.datetime.now():%Y-%m-%d %H:%M} by `scripts/analysis/make_results.py`. "
         "Do not edit by hand: re-run the script. All numbers are log1p-scale WIS unless marked "
         "'case scale'; a gain is positive when the second model has the lower WIS. Percentages are "
         "of WIS(L3) (WIS(N3) in the no-history arm).", "",
         "**Scored rows (deviation row 24).** Every estimate keeps only rows whose forecast origin "
         "(target week − h) lies in the same epi-year as the target, which removes the yearly-feature "
         "and training-label look-ahead (review R1): at h1 the first epi-week of each test year is "
         "dropped (1.9% of rows), at h4 the first four (7.7%). T1 also shows G_excess on all rows "
         "('all rows %').", "",
         f"**Horizons.** Every 'pooled' estimate pools the primary horizons **{hlab}** in every cell "
         f"(row 21); S1 cells also show a secondary pooling over {slab.replace('pooled_', '')} "
         f"(`horizon = {slab}`), which "
         "is never in the Holm family and uses only test years scored at all four horizons.", "",
         "**Inference.** DM test with EWC long-run variance and HLN correction on the weekly "
         "cross-unit mean loss difference; TOST against ±1% of WIS(L3); Holm over the 14-cell "
         "family (DM p and TOST p separately). Robustness columns: EWC with B = 4 cosine terms, "
         "IAAFT-surrogate-calibrated p (review RC), delta-method CI that treats WIS(L3) as estimated, "
         "case-scale G_excess. See `docs/methods/results_kit.md`.", "",
         "**Exclusions (row 34).** Primary scoring uses `data/processed/exclusions_v2/`: v1 (units "
         "without geometry, incomplete weeks) plus every Espírito Santo row of every test year (target weeks from 2019-12-29) "
         "(the source has false zeros for all 78 municipalities while InfoDengue shows cases). "
         "Applied to all four models at scoring only; the models were not refitted, so 2020–23 "
         "training targets still contain these false zeros. T1 shows G_excess under the v1 "
         "exclusions ('v1 excl %').", "",
         "**Taiwan (row 25).** Both Taiwan cells use test years 2020–2024 including 2021, a year with "
         "no local cases; the pre-review set (without 2021) is the sensitivity cell `TW_*_no2021`. "
         "A cell whose 2021 runs are not finished uses its base runs and is flagged '2021 pending'.", "",
         "**Loss-counting rule.** " + LOSS_RULE, "",
         "Key: **G_emb** = WIS(L3) − WIS(L4) (raw AlphaEarth gain); **G_id** = WIS(L3) − WIS(L3+C*) "
         "(gain from a location/ID control); **G_excess** = WIS(L3+C*) − WIS(L4+C*) (primary: what "
         "AlphaEarth adds beyond the best ID control).", "",
         "## 1. Headline table (T1)", "",
         f"Family: **{n_av} of {len(t1)} cells available**" + ("" if n_av == len(t1) else
             " — Holm p values are over the available cells and are **provisional**") + ".", "",
         "| cell | C* | G_excess % [95% CI] | DM p | Holm p | label (±1%) | B=4 p | IAAFT p | all rows % | v1 excl % | case % |",
         "|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in t1.itertuples():
        if not str(r.status).startswith("available"):
            L.append(f"| {r.cell} | {r.C_star} | pending | | | | | | | | |")
            continue
        fl = f" ({r.flags})" if isinstance(r.flags, str) and r.flags else ""
        L.append(f"| {r.cell}{fl} | {r.C_star} | {_fmt(r.pct_of_WIS_ref)} [{_fmt(r.lo95_pct)}, "
                 f"{_fmt(r.hi95_pct)}] | {_p(r.DM_p)} | {_p(r.Holm_p)} | {r.plain_label} | {_p(r.B4_p)} | "
                 f"{_p(r.p_iaaft)} | {_fmt(getattr(r, 'unfiltered_pct', np.nan))} | "
                 f"{_fmt(getattr(r, 'exclv1_pct', np.nan))} | "
                 f"{_fmt(getattr(r, 'case_pct', np.nan))} |")
    cnt = t1.loss_or_gain.value_counts().to_dict() if "loss_or_gain" in t1 else {}
    L += ["", "Counts under the loss-counting rule: " + ", ".join(f"{k}: {v}" for k, v in sorted(cnt.items()))
          + ".", "", "## 2. Status of every cell", "",
          "| cell | group | description | C* | status | flags / what is missing |", "|---|---|---|---|---|---|"]
    for c in cells:
        s = status[c["id"]]
        miss = "; ".join(f"{r}: {v}" for r, v in s["roles"].items() if v != "complete")
        if s.get("error"):
            miss = "ERROR " + s["error"]
        fl = "; ".join(c.get("flags", []))
        L.append(f"| {c['id']} | {c['group']}/{c['arm']} | {c['desc']} | {C.cstar_label(c)} | "
                 f"{s['status']} | {'; '.join(x for x in (fl, miss) if x)} |")
    L += ["", "## 3. Per-cell detail", ""]
    for c in cells:
        cid = c["id"]
        if not str(status[cid]["status"]).startswith("available") or est.empty:
            continue
        if est[est.cell == cid].empty:
            continue
        a3 = "N3" if c.get("ref") == "N3" else "L3"
        a4 = a3.replace("3", "4")
        L.append(f"### {cid}: {c['desc']} (C* = {C.cstar_label(c)})")
        info = infos.get(cid, {})
        L.append(f"Rows scored (primary horizons) {info.get('rows_scored_primary', '?'):,}; row filter "
                 f"{info.get('row_filter')} dropped {info.get('rows_dropped_by_filter', 0):,} rows of "
                 f"{info.get('rows_before_filter', '?')} (all horizons); test years {info.get('test_years')}; "
                 f"seeds {info.get('seeds')}; zero-filled share {info.get('zero_filled_share', np.nan):.2f}; "
                 f"outbreak share {info.get('outbreak_share', np.nan):.3f}."
                 + (f" Flags: {'; '.join(info.get('flags'))}." if info.get("flags") else ""))
        L.append("")
        for e, (x, y) in {"G_excess": (f"{a3}+C*", f"{a4}+C*"), "G_emb": (a3, a4),
                          "G_id": (a3, f"{a3}+C*")}.items():
            r = pick(est, cid, e)
            if r is not None:
                L.append(f"- **{e}** (pooled {hlab}) {ci_txt(r)}: {_interp(r, x, y)}")
        rs = est[(est.cell == cid) & (est.estimand == "G_excess") & (est.test_year == "pooled")
                 & (est.stratum == "all") & est.horizon.str.startswith("pooled_h")]
        for q in rs.itertuples():
            L.append(f"- *Secondary* G_excess pooled over {q.horizon.replace('pooled_', '')} "
                     f"(years {info.get('secondary_years')}; not in the Holm family): {ci_txt(q)}; "
                     f"p = {q.p:.3f}; {q.cls}.")
        s3 = extras.get(cid, {}).get("strata3")
        if s3 is not None and not c.get("estimands"):
            x = s3[s3.estimand == "G_excess"]
            L.append("- G_excess by target type (stratum estimate, % of the stratum's WIS(L3) | additive "
                     "contribution, % of the cell's WIS(L3)): " + "; ".join(
                         f"{r.stratum} ({100 * r.row_share:.0f}% rows) {_fmt(getattr(r, 'pct_of_ref', np.nan))} | "
                         f"{_fmt(r.contrib_pct)}" for r in x.itertuples())
                     + f"; identity residual {x.identity_residual.abs().max():.1e}.")
        ids = pick(est, cid, "ID_share")
        if ids is not None:
            v = ids.estimate
            L.append("- **ID share**: " + (f"{float(v):.2f}" if pd.notna(v) and str(v) != "nan"
                                            else str(ids.reason)))
        lp = lad[(lad.cell == cid) & (lad.horizon == "pooled")]
        if not lp.empty:
            best = lp.sort_values("wis_log").iloc[0]
            L.append(f"- Ladder (pooled {hlab}, {int(lp.n_rows.max()):,} common rows): " + ", ".join(
                f"{r.label} {r.wis_log:.4f}" for r in lp.itertuples())
                + f". Best = {best.label}. 80% coverage {lp.cov_80.min():.2f}–{lp.cov_80.max():.2f} "
                f"overall, {lp.cov_80_nonzero.min():.2f}–{lp.cov_80_nonzero.max():.2f} on non-zero targets.")
        if info.get("extras_errors"):
            L.append(f"- Supporting analyses that failed: {info['extras_errors']}")
        if info.get("ladder_skipped"):
            L.append(f"- Ladder rungs not yet available: {'; '.join(info['ladder_skipped'])}")
        L.append("")
    if not t6.empty:
        L += ["## 4. Sensitivity cells (T6a)", "",
              "| variant | vs | estimand | variant % [95% CI] | class | primary % | primary class |",
              "|---|---|---|---|---|---|---|"]
        for r in t6.itertuples():
            v = (f"{r.variant_pct:+.2f} [{r.variant_lo95_pct:+.2f}, {r.variant_hi95_pct:+.2f}]"
                 if np.isfinite(r.variant_pct) else "pending")
            p = f"{r.primary_pct:+.2f}" if np.isfinite(r.primary_pct) else "pending"
            L.append(f"| {r.variant} | {r.vs} | {r.estimand} | {v} | {r.variant_cls} | {p} | {r.primary_cls} |")
        L += ["", f"Both columns pool the primary horizons {hlab} on origin-year rows.", ""]
    L += ["## 5. Where everything is", "",
          f"Tables (`{T}/`, each as .csv and a LaTeX booktabs fragment .tex):", "",
          "- `T1_primary_family` — the 14 family cells: absolute WIS of L3/L4/L3+C*/L4+C*, G_emb, G_id, "
          "G_excess (% of WIS(L3), 95%/90% CI), DM p, Holm p, p_bonf14, unadjusted TOST class and the "
          "Holm-adjusted TOST class, plain label, loss_or_gain, EWC B=4 p/CI (+Holm), IAAFT p (+Holm), "
          "delta-method CI, case-scale G_excess, all-rows G_excess, S1 secondary pooling (`sec_*`).",
          "- `T1b_margin_sensitivity` — TOST at ±0.5/1/2% (unadjusted, Holm), near-margin flags, labels.",
          "- `T2_ladder` (+ `T2_ladder_long.csv`) — ladder per cell and horizon, coverage.",
          "- `T3_estimands` — G_emb / G_id / G_excess / ID share per cell × horizon and per test year (CSV).",
          "- `T4_cstar_selection` — control candidates at the 2019 origin and the chosen C*.",
          "- `T5_strata` — three target types (cases > 0 / recorded zero / zero-filled): stratum "
          "estimates and additive contributions (G_emb, G_id, G_excess in the CSV).",
          "- `T6a_sensitivities` (incl. TW without 2021), `T6b_nohist_estimands`, `T6c_nohist_ladder`.",
          "- Supporting: `S1_baselines`, `S2_control_panel`, `S3_outbreak`, `S4_weighted`, "
          "`S5_recalibration`, `S6_q90_mechanism`, `S7_embedding_distance` (+ `S7b_..._bins.csv`), "
          "`S8_per_year` (with context flags).", "",
          "Made: " + "; ".join(f"{k}: {v}" for k, v in made.items()), "",
          f"Figures (`{F}/`, PDF + PNG):", ""]
    fdesc = {"F1": f"forest plot of G_excess per family cell (pooled {hlab}, % of WIS(L3), 95%/90% CI, ±1% "
                   "band); Taiwan S5 in its own panel",
             "F2": "three target types: additive contributions to G_excess per cell",
             "F3": "held-out country (S5): AlphaEarth similarity to the training districts vs district gain",
             "F4": "G_excess per test year and cell",
             "FS1": "ladder per country, S1", "FS2": "no-history arm ladder"}
    for k, d in fdesc.items():
        L.append(f"- `{figs.get(k) or k}` — {d}" + ("" if figs.get(k) else " (**pending: no data yet**)"))
    L += ["", "Per-cell intermediate results: `runs/analysis_cache/<cell>/` (est.parquet, ladder.parquet, "
          "extras/*.parquet, info.json with row counts, filter, exclusions and seeds).", ""]
    if sched:
        L += ["## 6. Compute status (scheduler snapshot)", "", "```", sched, "```", ""]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(L))


if __name__ == "__main__":
    sys.exit(main())
