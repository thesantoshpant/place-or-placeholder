#!/usr/bin/env python
"""Primary hypothesis family: pooled-over-horizons G_excess across country x split cells, Holm.

Usage:
    python scripts/run/primary_family.py [--manifest configs/primary_cells.yaml] \
        [--out runs/primary_family] [exclusion flags as in estimands_report.py]

Family (deviations_from_protocol.md row 12): history arm, one cell per country x split
(BR S1-S5, CO S1-S5, PE S1/S5, TW S1/S5 = 14 cells). For each available cell the pooled-h
G_excess = WIS(L3+C*) - WIS(L4+C*) is computed exactly as in estimands_report.py
(pop.eval.estimands.infer_estimand: seed-averaged per-row log1p WIS, weekly cross-unit mean,
per-week mean over horizons, DM with EWC variance, t_B and HLN; TOST margin 1% of WIS(L3)).
Holm (step-down) is applied over the available cells only; the number of pending cells is
reported. Because Holm with m_avail < 14 is less strict than with all 14, adjusted p-values
are provisional until no cell is pending; the column p_bonf14 = min(1, 14 p) gives the
conservative bound for the full family.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_MAX_THREADS"):
    os.environ.setdefault(_v, "8")

import json

import numpy as np
import pandas as pd
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyze_run import md  # noqa: E402
from estimands_report import add_exclusion_args, exclusion_kw, load_cell, run_complete  # noqa: E402

from pop.eval.estimands import ROLES, infer_estimand  # noqa: E402
from pop.eval.stats import holm  # noqa: E402

STAGE = {"L3": "L3", "L4": "L4", "L3C": "L3_Cstar", "L4C": "L4_Cstar"}


def resolve_cell(cell: dict) -> tuple[dict, list[str]]:
    """Role -> list of run dirs (plan.json reuse applied) and the list of missing roles."""
    plan = {}
    if cell.get("plan") and Path(cell["plan"]).exists():
        plan = json.loads(Path(cell["plan"]).read_text())
    roles, missing = {}, []
    for r in ROLES:
        v = cell["runs"][r]
        dirs = [v] if isinstance(v, str) else list(v)
        p = plan.get(STAGE[r])
        if isinstance(p, str) and p.startswith("reuse:"):
            dirs = [p[len("reuse:"):]] + dirs[1:]
        roles[r] = dirs
        if not all(run_complete(d) for d in dirs):
            missing.append(r)
    return roles, missing


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", default="configs/primary_cells.yaml")
    ap.add_argument("--out", default="runs/primary_family")
    ap.add_argument("--margin-rel", type=float, default=0.01)
    add_exclusion_args(ap)
    a = ap.parse_args()
    cells = yaml.safe_load(Path(a.manifest).read_text())["cells"]
    rows = []
    for c in cells:
        roles, missing = resolve_cell(c)
        base = {"country": c["country"], "split": c["split"], "arm": c.get("arm", "history"),
                "note": c.get("note", "")}
        if missing:
            rows.append({**base, "status": "pending", "missing": ",".join(missing)})
            print(f"{c['country']} {c['split']}: pending ({','.join(missing)})", flush=True)
            continue
        g, info = load_cell(roles, **exclusion_kw(a))
        r = infer_estimand(g, "G_excess", margin_rel=a.margin_rel)
        rows.append({**base, "status": "available", "missing": "",
                     "runs": "; ".join(f"{k}={','.join(v)}" for k, v in roles.items()),
                     "estimate": r["estimate"], "lo95": r["lo95"], "hi95": r["hi95"],
                     "p": r["p"], "pct_of_ref": r["pct_of_ref"], "cls": r["cls"],
                     "mde_pct": r["mde_pct"], "n_seeds": r["n_seeds"], "seed_sd": r["seed_sd"],
                     "T": r["T"], "df": r["df"], "n_rows": r["n_rows"],
                     "excluded": json.dumps(info["excluded"])})
        print(f"{c['country']} {c['split']}: G_excess {r['estimate']:+.5f} p={r['p']:.3f}", flush=True)
    F = pd.DataFrame(rows)
    av = F.status == "available"
    F["p_holm_avail"] = np.nan
    if av.any():
        F.loc[av, "p_holm_avail"] = holm(F.loc[av, "p"].to_numpy())
        F.loc[av, "p_bonf14"] = np.minimum(1.0, len(F) * F.loc[av, "p"])
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    F.to_csv(out / "primary_family.csv", index=False)
    n_av, n_pend = int(av.sum()), int((~av).sum())
    cols = [c for c in ["country", "split", "status", "estimate", "lo95", "hi95", "p",
                        "p_holm_avail", "p_bonf14", "cls", "mde_pct", "n_seeds", "seed_sd",
                        "missing", "note"] if c in F]
    txt = (f"# Primary family: pooled-h G_excess (history arm)\n\n{n_av} of {len(F)} cells "
           f"available, {n_pend} pending. Holm over the {n_av} available cells "
           f"(provisional while cells are pending; p_bonf14 = min(1, {len(F)} p)).\n\n"
           + md(F[cols], 5, index=False) + "\n")
    (out / "primary_family.md").write_text(txt)
    print(txt)


if __name__ == "__main__":
    main()
