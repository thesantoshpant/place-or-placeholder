#!/usr/bin/env python
"""S1 fixed control panel (review response, external Comment 2 / C15).

For every S1 cell (BR, CO, PE, TW) and every fixed control k in {C1, C2, C3, C6}:
    G_id_k     = WIS(L3)    - WIS(L3+Ck)     (does the control alone help?)
    G_excess_k = WIS(L3+Ck) - WIS(L4+Ck)     (does AlphaEarth add skill beyond control k?)
plus G_emb = WIS(L3) - WIS(L4) (the same for every k). Log1p-WIS, pooled over h in {1, 4},
seed 0, the v3 primary scored rows (exclusions_v2 incl. unit-week exclusions, row_filter
origin_year; --legacy = v1 exclusions, no row filter) and the primary inference (DM with EWC variance, t_B, HLN;
TOST margin 1% of WIS(L3)) via scripts/run/estimands_report.load_cell and
pop.eval.estimands.infer_estimand, exactly as scripts/run/primary_family.py.
L3/L4 dirs follow runs/<c>_s1_shared/plan.json (reuse entries). C1 = the existing C* runs.
Pending runs (no scores.parquet) are listed as pending; rerun the script when they finish.

Usage: python scripts/analysis/control_panel.py [--out docs/results/review]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_MAX_THREADS"):
    os.environ.setdefault(_v, "4")

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "run"))
sys.path.insert(0, str(ROOT / "scripts" / "analysis"))
from estimands_report import add_exclusion_args, exclusion_kw, load_cell, run_complete  # noqa: E402

from rk_compute import apply_row_filter, apply_unit_weeks  # noqa: E402

from pop.eval.estimands import infer_estimand  # noqa: E402

XDIR = ROOT / "data/processed/exclusions_v2"

HORIZONS = [1, 4]
COUNTRIES = ["brazil", "colombia", "peru", "taiwan"]
CONTROLS = ["C1", "C2", "C3", "C6"]
MARKER = "<!-- interpretation below is hand-written; the script keeps it -->"


def base_dirs(c: str) -> dict:
    plan = json.loads((ROOT / f"runs/{c}_s1_shared/plan.json").read_text())
    out = {}
    for stage in ("L3", "L4", "L3_Cstar", "L4_Cstar"):
        p = plan.get(stage)
        out[stage] = (p[len("reuse:"):] if isinstance(p, str) and p.startswith("reuse:")
                      else f"runs/{c}_s1_shared_{stage}")
    if plan.get("c_star") != "C1":
        raise SystemExit(f"{c}: S1 C* is {plan.get('c_star')}, expected C1")
    return out


def control_dirs(c: str, k: str, b: dict) -> tuple[str, str, str]:
    if k == "C1":
        return b["L3_Cstar"], b["L4_Cstar"], "existing C* (C1) runs"
    if c == "brazil" and k in ("C3", "C6"):
        return (f"runs/brazil_s1_sens_ctrl_L3_{k}", f"runs/brazil_s1_sens_ctrl_L4_{k}",
                "scheduler item brazil_s1_sens_ctrl")
    return f"runs/{c}_s1_panel_L3_{k}", f"runs/{c}_s1_panel_L4_{k}", "panel run"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="docs/results/review")
    ap.add_argument("--legacy", action="store_true",
                    help="v1 exclusions and no row filter (pre-kit-v3 primary)")
    add_exclusion_args(ap)
    a = ap.parse_args()
    if a.legacy:
        lexcl, uw, rf = exclusion_kw(a), None, None
    else:
        lexcl = {"exclude_units": str(XDIR / "no_geometry_units.csv"),
                 "exclude_weeks": str(XDIR / "incomplete_weeks.csv"), "late_entry": None,
                 "week_actions": ("exclude",)}
        uw, rf = str(XDIR / "unit_week_exclusions.csv"), "origin_year"
    os.chdir(ROOT)
    rows = []
    for c in COUNTRIES:
        b = base_dirs(c)
        for k in CONTROLS:
            d3, d4, src = control_dirs(c, k, b)
            roles = {"L3": [b["L3"]], "L4": [b["L4"]], "L3C": [d3], "L4C": [d4]}
            base = {"country": c, "split": "S1", "control": k, "source": src,
                    "runs": "; ".join(f"{r}={v[0]}" for r, v in roles.items())}
            miss = [r for r, v in roles.items() if not run_complete(v[0])]
            if miss:
                rows.append({**base, "status": "pending", "missing": ",".join(miss)})
                print(f"{c} {k}: pending ({','.join(miss)})", flush=True)
                continue
            g, info = load_cell(roles, **lexcl)
            if uw:
                g, _ = apply_unit_weeks(g, uw)
            g, finfo = apply_row_filter(g, rf)
            if "seed" in g.columns and g["seed"].nunique() > 1:  # seed 0 only in this panel
                g = g[g["seed"] == 0]
            g = g[g.horizon.isin(HORIZONS)].reset_index(drop=True)
            r = {**base, "status": "available", "missing": "", "horizons": "1,4",
                 "n_rows": len(g), "excluded": json.dumps(info["excluded"]),
                 "scoring": "legacy_v1" if a.legacy else "v3_excl_v2_origin_year",
                 "rows_dropped_by_filter": finfo.get("rows_dropped_by_filter", 0)}
            for e in ("G_id", "G_excess", "G_emb"):
                x = infer_estimand(g, e)
                r.update({f"{e}_est": x["estimate"], f"{e}_lo95": x["lo95"],
                          f"{e}_hi95": x["hi95"], f"{e}_p": x["p"],
                          f"{e}_pct": x["pct_of_ref"], f"{e}_pct_lo95": 100 * x["lo95"] / x["wis_ref"],
                          f"{e}_pct_hi95": 100 * x["hi95"] / x["wis_ref"], f"{e}_cls": x["cls"],
                          f"{e}_mde_pct": x["mde_pct"]})
            r["wis_L3"] = x["wis_ref"]
            rows.append(r)
            print(f"{c} {k}: G_id {r['G_id_pct']:+.2f}% (p={r['G_id_p']:.3f})  "
                  f"G_excess {r['G_excess_pct']:+.2f}% (p={r['G_excess_p']:.3f})", flush=True)
    F = pd.DataFrame(rows)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    F.to_csv(out / "RE_control_panel.csv", index=False)

    def fmt(r, e):
        if r.status != "available":
            return "pending"
        return (f"{r[e + '_pct']:+.2f} [{r[e + '_pct_lo95']:+.2f}, {r[e + '_pct_hi95']:+.2f}]"
                f" p={r[e + '_p']:.3f} ({r[e + '_cls']})")
    lines = ["| Country | Control | G_id_k, % of WIS(L3) [95% CI] | G_excess_k, % of WIS(L3) [95% CI] |",
             "|---|---|---|---|"]
    for _, r in F.iterrows():
        lines.append(f"| {r.country} | {r.control} | {fmt(r, 'G_id')} | {fmt(r, 'G_excess')} |")
    emb = F[F.status == "available"].drop_duplicates("country")
    elines = [f"- {r.country}: G_emb {fmt(r, 'G_emb')}" for _, r in emb.iterrows()]
    head = ("# S1 fixed control panel (review response)\n\n"
            "Generated by `scripts/analysis/control_panel.py` (rerunnable; pending cells fill in "
            "when their runs finish). S1, LightGBM with one shared hyperparameter set per country, "
            "seed 0, log1p-WIS pooled over h {1, 4}, "
            + ("v1 exclusions, no row filter (legacy), " if a.legacy else
               "v3 primary scored rows (exclusions_v2 incl. Espirito Santo unit-weeks; "
               "row_filter origin_year), ")
            + "DM/EWC + HLN inference, "
            "TOST margin 1% of WIS(L3). Positive = the second model is better. "
            "G_id_k = WIS(L3) - WIS(L3+Ck); G_excess_k = WIS(L3+Ck) - WIS(L4+Ck). "
            "C1 = pre-training mean log cases (C* in every S1 cell), C2 = coordinates "
            "(spherical harmonics), C3 = shuffled embedding (fixed permutation, seed 0), "
            "C6 = unit-ID categorical. No multiplicity correction (descriptive panel).\n\n"
            + "\n".join(lines) + "\n\nEmbedding gain without controls (G_emb = WIS(L3) - WIS(L4)):\n\n"
            + "\n".join(elines) + "\n\n")
    p = out / "RE_summary.md"
    tail = ""
    if p.exists() and MARKER in p.read_text():
        tail = p.read_text().split(MARKER, 1)[1]
    p.write_text(head + MARKER + (tail or "\n\n## Interpretation\n\n(pending)\n"))
    print(head)


if __name__ == "__main__":
    main()
