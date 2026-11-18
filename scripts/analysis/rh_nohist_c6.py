#!/usr/bin/env python
"""RH (exploratory; added after the v1 review on 2026-11-18, before these results were seen).

No-history arm, Brazil S1, district-identifier control C6 (unit-ID categorical) on the test
years 2020-2024, compared on the same scored rows with the arm's C* = C2 (coordinates):
    G_id_k     = WIS(N3)    - WIS(N3+Ck)
    G_excess_k = WIS(N3+Ck) - WIS(N4+Ck)
    G_emb      = WIS(N3)    - WIS(N4)
k in {C6, C2}. Log1p-WIS, pooled over h {1, 4}, seed 0, the v3 primary scored rows
(exclusions_v2 incl. unit-week exclusions; row_filter origin_year), DM with EWC variance, t_B and
HLN; TOST margin 1% of WIS(N3). Loading, filters and inference are the ones used by
scripts/analysis/control_panel.py (estimands_report.load_cell, rk_compute.apply_unit_weeks /
apply_row_filter, pop.eval.estimands.infer_estimand); role names L3/L4/L3C/L4C carry N3/N4/N3+Ck/N4+Ck.

Usage: python scripts/analysis/rh_nohist_c6.py [--out docs/results/review]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_MAX_THREADS"):
    os.environ.setdefault(_v, "4")

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "run"))
sys.path.insert(0, str(ROOT / "scripts" / "analysis"))
from estimands_report import KEYS, load_cell, run_complete  # noqa: E402

from rk_compute import apply_row_filter, apply_unit_weeks  # noqa: E402

from pop.eval.estimands import infer_estimand, weekly_pooled  # noqa: E402

XDIR = ROOT / "data/processed/exclusions_v2"
HORIZONS = [1, 4]
N3, N4 = "runs/brazil_s1_nohist_N3", "runs/brazil_s1_nohist_N4"
CONTROLS = {
    "C6": ("runs/brazil_s1_nohist_panel_N3_C6", "runs/brazil_s1_nohist_panel_N4_C6",
           "unit-ID categorical (exploratory panel run)"),
    "C2": ("runs/brazil_s1_nohist_N3_Cstar", "runs/brazil_s1_nohist_N4_Cstar",
           "coordinates, spherical harmonics (existing no-history C* runs)"),
}
KIT_T6B = ROOT / "docs/results/tables/T6b_nohist_estimands.csv"
HEADER = ("exploratory, added after the v1 review on 2026-11-18, before these results were seen")
MARKER = "<!-- interpretation below is hand-written; the script keeps it -->"
DEFS = {"G_id": "WIS(N3) - WIS(N3+{k})", "G_excess": "WIS(N3+{k}) - WIS(N4+{k})",
        "G_emb": "WIS(N3) - WIS(N4)"}


def load(k: str):
    d3, d4, _ = CONTROLS[k]
    roles = {"L3": [N3], "L4": [N4], "L3C": [d3], "L4C": [d4]}
    miss = [r for r, v in roles.items() if not run_complete(v[0])]
    if miss:
        raise SystemExit(f"{k}: runs not complete: {miss}")
    lexcl = {"exclude_units": str(XDIR / "no_geometry_units.csv"),
             "exclude_weeks": str(XDIR / "incomplete_weeks.csv"), "late_entry": None,
             "week_actions": ("exclude",)}
    g, info = load_cell(roles, **lexcl)
    g, uinfo = apply_unit_weeks(g, str(XDIR / "unit_week_exclusions.csv"))
    g, finfo = apply_row_filter(g, "origin_year")
    if "seed" in g.columns and g["seed"].nunique() > 1:
        g = g[g["seed"] == 0]
    g = g[g.horizon.isin(HORIZONS)].reset_index(drop=True)
    return g, {**info, **uinfo, **finfo}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="docs/results/review")
    a = ap.parse_args()
    os.chdir(ROOT)
    G, INFO = {}, {}
    for k in CONTROLS:
        G[k], INFO[k] = load(k)
        print(f"{k}: {len(G[k])} rows after filters; excluded {INFO[k]['excluded']}; "
              f"unit-week dropped {INFO[k].get('unit_week_rows_dropped')}; "
              f"row filter dropped {INFO[k].get('rows_dropped_by_filter')}", flush=True)
    # same rows for both controls
    idx = {k: pd.MultiIndex.from_frame(G[k][KEYS]) for k in G}
    common = idx["C6"].intersection(idx["C2"])
    for k in G:
        n0 = len(G[k])
        G[k] = G[k][idx[k].isin(common)].reset_index(drop=True)
        INFO[k]["rows_dropped_not_common"] = n0 - len(G[k])
    print(f"common rows: {len(common)}; dropped not-common: "
          f"{ {k: INFO[k]['rows_dropped_not_common'] for k in G} }", flush=True)

    rows, wis = [], {}
    for k, g in G.items():
        for col, lab in (("wis_L3", "N3"), ("wis_L4", "N4"), ("wis_L3C", f"N3+{k}"),
                         ("wis_L4C", f"N4+{k}")):
            wis[lab] = float(weekly_pooled(g, col).mean())
        for e in ("G_id", "G_excess", "G_emb"):
            x = infer_estimand(g, e)
            rows.append({"control": k, "estimand": e, "definition": DEFS[e].format(k=k),
                         "estimate": x["estimate"], "lo95": x["lo95"], "hi95": x["hi95"],
                         "pct_of_wis_N3": x["pct_of_ref"],
                         "pct_lo95": 100 * x["lo95"] / x["wis_ref"],
                         "pct_hi95": 100 * x["hi95"] / x["wis_ref"], "p": x["p"],
                         "tost_p": x["tost_p"], "cls": x["cls"], "mde_pct": x["mde_pct"],
                         "wis_N3": x["wis_ref"], "n_rows": x["n_rows"], "n_weeks": x["n_weeks"],
                         "horizons": "1,4", "seed": 0, "scoring": "v3_excl_v2_origin_year",
                         "runs": f"N3={N3}; N4={N4}; N3+{k}={CONTROLS[k][0]}; N4+{k}={CONTROLS[k][1]}"})
    F = pd.DataFrame(rows)
    ge = F[F.estimand == "G_emb"].set_index("control")["estimate"]
    if not np.isclose(ge["C6"], ge["C2"], rtol=0, atol=1e-12):
        raise SystemExit(f"G_emb differs between the two row sets: {ge.to_dict()}")

    # cross-check: C2 values against the kit's T6b (v3 rows, pooled h {1,4})
    xc = ""
    if KIT_T6B.exists():
        t = pd.read_csv(KIT_T6B)
        t = t[(t.cell == "BR_S1_nohist") & (t.horizon.astype(str) == "pooled")]
        lines = []
        for e in ("G_id", "G_excess", "G_emb"):
            kr = t[t.estimand == e]
            mine = F[(F.control == "C2") & (F.estimand == e)].iloc[0]
            if len(kr):
                kr = kr.iloc[0]
                lines.append(f"{e}: kit {kr.pct_of_ref:+.4f}% (n_rows {int(kr.n_rows)}) vs here "
                             f"{mine.pct_of_wis_N3:+.4f}% (n_rows {int(mine.n_rows)})")
        xc = "; ".join(lines)
        print("cross-check vs kit T6b (C2):", xc, flush=True)

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    F.to_csv(out / "RH_nohist_c6.csv", index=False)

    def fmt(r):
        return (f"{r.pct_of_wis_N3:+.2f} [{r.pct_lo95:+.2f}, {r.pct_hi95:+.2f}] | {r.p:.3f} | "
                f"{r.cls} | {r.mde_pct:.2f}")
    tl = ["| Control | Estimand | Definition | % of WIS(N3) [95% CI] | p (DM) | TOST class | MDE % |",
          "|---|---|---|---|---|---|---|"]
    for _, r in F.iterrows():
        tl.append(f"| {r.control} | {r.estimand} | {r.definition} | {fmt(r)} |")
    wl = ["| Model | pooled log1p-WIS |", "|---|---|"] + [f"| {m} | {v:.5f} |" for m, v in wis.items()]
    head = (f"# RH: no-history arm, Brazil S1, district-identifier control C6\n\n"
            f"**Status: {HEADER}.**\n\n"
            "Generated by `scripts/analysis/rh_nohist_c6.py`. Configs "
            "`configs/brazil_s1_nohist_panel_N3_C6.yaml`, `..._N4_C6.yaml` (copies of the "
            "no-history C* configs with only the level changed; Brazil S1 L1 params, seed 0, "
            "test years 2020-2024, h {1, 4}). Scored rows: v3 primary (exclusions_v2 incl. "
            "Espirito Santo unit-weeks; row_filter origin_year), the same rows for C6 and C2 "
            f"({int(F.n_rows.iloc[0])} rows, {int(F.n_weeks.iloc[0])} target weeks). "
            "Log1p-WIS pooled over h {1, 4}; DM with EWC variance, t_B and HLN; TOST margin 1% "
            "of WIS(N3). Positive = the second model is better. C6 = unit-ID categorical (pure "
            "identifier); C2 = coordinates (the arm's C*, selected at the 2019 origin with tie set "
            "{C2, C6}). No multiplicity correction (descriptive, exploratory).\n\n"
            + "\n".join(tl) + "\n\nPooled log1p-WIS on these rows:\n\n" + "\n".join(wl)
            + (f"\n\nCross-check of the C2 rows against the kit (`T6b_nohist_estimands.csv`, "
               f"BR_S1_nohist, pooled h {{1, 4}}): {xc}.\n" if xc else "\n")
            + f"\nFilter info: {json.dumps({k: {kk: INFO[k].get(kk) for kk in ('excluded', 'unit_week_rows_dropped', 'rows_dropped_by_filter', 'rows_dropped_not_common')} for k in INFO})}\n\n")
    p = out / "RH_nohist_c6.md"
    tail = ""
    if p.exists() and MARKER in p.read_text():
        tail = p.read_text().split(MARKER, 1)[1]
    p.write_text(head + MARKER + (tail or "\n\n## Interpretation\n\n(pending)\n"))
    print(head)


if __name__ == "__main__":
    main()
