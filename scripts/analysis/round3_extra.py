#!/usr/bin/env python
"""Round-3 post hoc scoring, part 2: Taiwan S1 ladder/panel with 2021 and Colombia S2 no-history.

Specs (committed before scoring): docs/methods/round3_runs.md (EXP-B S2, S3).
Scoring = the v3 results kit rows (round3_score.load_v3: exclusions_v2, unit-week exclusions,
origin-year row filter, h{1,4}); ladders via rk_compute.ladder_table, estimands via
rk_compute.estimand_table / pop.eval.estimands.infer_estimand. Nothing re-implements a test.

Usage (repo root, after `source env.sh`):
    nice -n 19 python scripts/analysis/round3_extra.py tw2021      # ladder + baselines + panel
    nice -n 19 python scripts/analysis/round3_extra.py nohist      # CO S2 no-history (+ BR S1 check)

Outputs (docs/results/review/): R3_C_tw2021_ladder.csv, R3_C_tw2021_panel.csv,
R3_C_co_s2_nohist.csv, R3_C_co_s2_nohist_ladder.csv.
Blinded run dirs (brazil_s4*, brazil_s2_nohist*, brazil_s1_sens_{yref,delay,ctrl}*) are never read.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "analysis"))
sys.path.insert(0, str(ROOT / "scripts" / "run"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import round3_score as R3  # noqa: E402  (sets threads, chdir ROOT, kit imports)
import rk_cells as C  # noqa: E402
import rk_compute as K  # noqa: E402
from pop.eval.estimands import infer_estimand  # noqa: E402

OUT = R3.OUT
HP = [1, 4]
TW_ROWS = 141_645
BLINDED = ("brazil_s4", "brazil_s2_nohist", "brazil_s1_sens_yref", "brazil_s1_sens_delay",
           "brazil_s1_sens_ctrl")
log = R3.log


def guard(dirs):
    for d in dirs:
        if any(Path(d).name.startswith(b) for b in BLINDED):
            raise SystemExit(f"refusing blinded run dir {d}")
        if not (ROOT / d / "scores.parquet").exists():
            raise SystemExit(f"missing scores.parquet: {d}")


def load(roles, seeds=None):
    for v in roles.values():
        guard(v)
    return R3.load_v3(roles, seeds=seeds)


def est_cols(prefix, q):
    w = q["wis_ref"]
    return {f"{prefix}_est": q["estimate"], f"{prefix}_lo95": q["lo95"], f"{prefix}_hi95": q["hi95"],
            f"{prefix}_p": q["p"], f"{prefix}_pct": 100 * q["estimate"] / w,
            f"{prefix}_pct_lo95": 100 * q["lo95"] / w, f"{prefix}_pct_hi95": 100 * q["hi95"] / w,
            f"{prefix}_cls": q["cls"], f"{prefix}_mde_pct": q["mde_pct"]}


# ====================================================================== Taiwan S1 with 2021
TW_BASE = ["runs/taiwan_s1_baselines", "runs/taiwan_s1_r3_tw2021_baselines"]
TW_L2 = ["runs/taiwan_s1_shared_L2", "runs/taiwan_s1_r3_tw2021_L2"]


def tw_cell():
    cell = R3.registry()["TW_S1"]
    if cell.get("add_test_years", {}).get("state") != "complete":
        raise SystemExit("TW_S1 2021 runs not complete in the registry")
    return cell


def tw_ladder(cell) -> pd.DataFrame:
    roles = {r: list(cell["roles"][r]["dirs"]) for r in C.ROLES}
    g, info = load(roles, seeds=[0])
    log(f"TW S1 primary rows (h1,4): {len(g):,}; years {sorted(g.test_year.unique())}")
    rungs = [("L0 (seasonal naive)", TW_BASE, "naive-L0"), ("NB GLM (L1)", TW_BASE, "nb-L1"),
             ("LightGBM L1", TW_BASE, "lgbm-L1"), ("LightGBM L2", TW_L2, "lgbm-L2")]
    for r in C.ROLES:
        rungs.append((f"LightGBM {R3.STAGE[r].replace('_Cstar', '+C*')}", roles[r], None))
    for _, d, _ in rungs:
        guard(d)
    lad = K.ladder_table(g, rungs, primary_horizons=HP, secondary_horizons=None)
    l0 = lad[lad.label.str.startswith("L0")].set_index("horizon").wis_log
    l1 = lad[lad.label == "LightGBM L1"].set_index("horizon").wis_log
    lad["rel_wis_vs_L0"] = lad.wis_log / lad.horizon.map(l0)
    lad["rel_wis_vs_L1"] = lad.wis_log / lad.horizon.map(l1)
    lad.insert(0, "cell", "TW_S1")
    lad["test_years"] = ",".join(str(int(y)) for y in sorted(g.test_year.unique()))
    lad["seeds"] = "0"
    lad["missing_models"] = "TimesFM 2.5 zero-shot (no Taiwan run)"
    lad["rows_primary_frame"] = len(g)
    # old (without 2021) values for comparison, from the kit table
    old = pd.read_csv(ROOT / "docs/results/tables/S1_baselines.csv", dtype={"horizon": str})
    old = old[old.cell == "TW_S1"].copy()
    old["label"] = old.label.str.replace(" (per-level tuned)", " (per-level tuned, superseded)",
                                         regex=False)
    m = old.set_index(["label", "horizon"])
    for c in ("wis_log", "rel_wis_vs_L0", "cov_80", "cov_80_nonzero", "n_rows"):
        lad[f"no2021_{c}"] = [m[c].get((lb, h), np.nan) for lb, h in zip(lad.label, lad.horizon)]
    return lad, len(g)


def tw_panel(cell) -> pd.DataFrame:
    base = {r: list(cell["roles"][r]["dirs"]) for r in C.ROLES}
    rows = []
    for k in ("C1", "C2", "C3", "C6"):
        if k == "C1":
            d3, d4, src = base["L3C"], base["L4C"], "existing C* (C1) runs incl. 2021"
        else:
            d3 = [f"runs/taiwan_s1_panel_L3_{k}", f"runs/taiwan_s1_r3_tw2021_panel_L3_{k}"]
            d4 = [f"runs/taiwan_s1_panel_L4_{k}", f"runs/taiwan_s1_r3_tw2021_panel_L4_{k}"]
            src = "panel run + 2021 panel run (round-3 EXP-B S2)"
        roles = {"L3": base["L3"], "L4": base["L4"], "L3C": d3, "L4C": d4}
        g, info = load(roles, seeds=[0])
        r = {"country": "taiwan", "split": "S1", "control": k, "source": src,
             "runs": "; ".join(f"{a}={'+'.join(v)}" for a, v in roles.items()), "status": "available",
             "horizons": "1,4", "n_rows": len(g), "scoring": "v3_excl_v2_origin_year",
             "test_years": ",".join(str(int(y)) for y in sorted(g.test_year.unique())), "seed": 0}
        for e in ("G_id", "G_excess", "G_emb"):
            q = infer_estimand(g, e)
            r.update(est_cols(e, q))
        r["wis_L3"] = q["wis_ref"]
        rows.append(r)
        log(f"TW panel {k}: n={len(g):,} G_id {r['G_id_pct']:+.2f}% (p={r['G_id_p']:.3f}) "
            f"G_excess {r['G_excess_pct']:+.2f}% (p={r['G_excess_p']:.3f})")
    df = pd.DataFrame(rows)
    old = pd.read_csv(OUT / "RE_control_panel.csv")
    old = old[old.country == "taiwan"].set_index("control")
    for c in ("G_id_pct", "G_id_p", "G_excess_pct", "G_excess_p", "n_rows"):
        df[f"no2021_{c}"] = df.control.map(old[c])
    return df


def run_tw2021():
    cell = tw_cell()
    lad, n = tw_ladder(cell)
    pan = tw_panel(cell)
    a1 = OUT / "R3_A1_positive_control.csv"
    checks = {"primary_frame": n, "ladder_pooled": int(lad[lad.horizon == "pooled"].n_rows.max()),
              "ladder_pooled_min": int(lad[lad.horizon == "pooled"].n_rows.min()),
              "panel_min": int(pan.n_rows.min()), "panel_max": int(pan.n_rows.max())}
    if a1.exists():
        x = pd.read_csv(a1)
        x = x[x.cell == "TW_S1"]
        checks["A1_TW"] = sorted(set(int(v) for v in x.n_rows))
    ok = all(v == TW_ROWS for k, v in checks.items() if k != "A1_TW") and \
        checks.get("A1_TW", [TW_ROWS]) == [TW_ROWS]
    log(f"row-count check vs {TW_ROWS:,}: {checks} -> {'PASS' if ok else 'FAIL'}")
    lad["rowcount_check"] = "PASS" if ok else f"FAIL {json.dumps(checks)}"
    pan["rowcount_check"] = lad["rowcount_check"].iloc[0]
    lad.to_csv(OUT / "R3_C_tw2021_ladder.csv", index=False)
    pan.to_csv(OUT / "R3_C_tw2021_panel.csv", index=False)
    log("wrote R3_C_tw2021_ladder.csv, R3_C_tw2021_panel.csv")
    pd.set_option("display.width", 250)
    print(lad[lad.horizon == "pooled"][["label", "n_rows", "wis_log", "rel_wis_vs_L0", "cov_40", "cov_80",
                                         "cov_80_nonzero", "no2021_wis_log", "no2021_rel_wis_vs_L0"]]
          .round(4).to_string())
    print(pan[["control", "n_rows", "G_id_pct", "G_id_pct_lo95", "G_id_pct_hi95", "G_id_p", "G_excess_pct",
               "G_excess_pct_lo95", "G_excess_pct_hi95", "G_excess_p", "G_emb_pct", "G_emb_p",
               "no2021_G_excess_pct"]].round(4).to_string())


# ====================================================================== no-history
def nohist_cell(country, split):
    c, s = country, split.lower()
    pref = f"runs/{c}_{s}_nohist"
    cell = C._pipeline_cell(f"{C.COUNTRY_CODE[c]}_{split}_nohist", "secondary", "no-history", c, split,
                            f"{c.title()} {split}, no-history arm (ref = N3)", pref, pref, ref="N3",
                            plan_roles=False)
    cell["ladder"] = [{"label": "N2", "dir": f"{pref}_N2", "run": None, "optional": True}] + [
        {"label": f"{lv}+C1", "dir": f"{pref}_{lv}_C1", "run": None,
         "marker": f"{pref}/stage_{lv}_C1.done"} for lv in ("N3", "N4")]
    cell["role_labels"] = {"L3": "N3", "L4": "N4", "L3C": "N3+C*", "L4C": "N4+C*"}
    return cell


def score_nohist(cell):
    roles = {r: list(cell["roles"][r]["dirs"]) for r in C.ROLES}
    g, info = load(roles)
    log(f"{cell['id']}: {len(g):,} rows, years {sorted(g.test_year.unique())}, C* {cell['cstar']}")
    est = K.estimand_table(g, primary_horizons=HP, secondary_horizons=None)
    est = est[(est.stratum == "all") & (est.test_year == "pooled")].copy()
    est.insert(0, "cell", cell["id"])
    est["C_star"] = cell["cstar"]
    rungs, notes = K.ladder_rungs(cell)
    for _, d, _ in rungs:
        guard(d)
    lad = K.ladder_table(g, rungs, primary_horizons=HP, secondary_horizons=None)
    lad.insert(0, "cell", cell["id"])
    lad["skipped_rungs"] = "; ".join(notes) + ("; N2 not run" if not any(r[0] == "N2" for r in rungs) else "")
    # C1 static-history rung: G_C1 = WIS(N3) - WIS(N3+C1); excess beyond C1 = WIS(N3+C1) - WIS(N4+C1)
    pref = f"runs/{cell['country']}_{cell['split'].lower()}_nohist"
    rc = {"L3": roles["L3"], "L4": roles["L4"], "L3C": [f"{pref}_N3_C1"], "L4C": [f"{pref}_N4_C1"]}
    g1, _ = load(rc)
    extra = []
    for e, name in (("G_id", "G_C1 (N3 - N3+C1)"), ("G_excess", "G_excess_C1 (N3+C1 - N4+C1)")):
        q = infer_estimand(g1, e)
        extra.append({"cell": cell["id"], "horizon": "pooled", "pooled_over": "1,4", "test_year": "pooled",
                      "estimand": name, "estimate": q["estimate"], "pct_of_ref": q["pct_of_ref"],
                      "lo95": q["lo95"], "hi95": q["hi95"], "lo95_pct": 100 * q["lo95"] / q["wis_ref"],
                      "hi95_pct": 100 * q["hi95"] / q["wis_ref"], "p": q["p"], "tost_p": q["tost_p"],
                      "cls": q["cls"], "mde_pct": q["mde_pct"], "wis_ref": q["wis_ref"],
                      "n_rows": q["n_rows"], "n_weeks": q["n_weeks"], "C_star": "C1 (rung)"})
    return est, pd.DataFrame(extra), lad, len(g), len(g1)


def run_nohist(check_br=True):
    t6b = pd.read_csv(ROOT / "docs/results/tables/T6b_nohist_estimands.csv", dtype={"horizon": str})
    cols = [c for c in t6b.columns]
    if check_br:   # reproduce T6b for BR S1 no-history (not blinded) with this code path
        est, _, lad, _, _ = score_nohist(nohist_cell("brazil", "S1"))
        a = est[est.horizon == "pooled"].set_index("estimand")
        b = t6b[(t6b.cell == "BR_S1_nohist") & (t6b.horizon == "pooled")].set_index("estimand")
        d = (a.loc[b.index, "estimate"] - b.estimate).abs().max()
        dp = (a.loc[b.index, "p"] - b.p).abs().max()
        log(f"BR S1 no-history check vs T6b: max |diff| estimate {d:.3g}, p {dp:.3g} -> "
            f"{'PASS' if d < 1e-10 and dp < 1e-10 else 'FAIL'}")
        if not (d < 1e-10 and dp < 1e-10):
            raise SystemExit("T6b not reproduced")
    cell = nohist_cell("colombia", "S2")
    if cell["cstar"] is None:
        raise SystemExit("CO S2 no-history: no rule-v2 selection.json")
    est, extra, lad, n, n1 = score_nohist(cell)
    est = est[[c for c in cols if c in est.columns] + ["C_star"]]
    out = pd.concat([est, extra], ignore_index=True)
    sel = json.loads((ROOT / "runs/colombia_s2_nohist_controls_2019/selection.json").read_text())
    out["selection_tie_set"] = ",".join(sel.get("tie_set", []))
    out["selection_ref_wis"] = sel.get("ref_wis_log")
    out["selection_cstar_wis"] = sel.get("wis_log")
    out["n_rows_primary"] = n
    out["n_rows_C1_frame"] = n1
    out.to_csv(OUT / "R3_C_co_s2_nohist.csv", index=False)
    lad.to_csv(OUT / "R3_C_co_s2_nohist_ladder.csv", index=False)
    log("wrote R3_C_co_s2_nohist.csv, R3_C_co_s2_nohist_ladder.csv")
    pd.set_option("display.width", 250)
    print(out[out.horizon == "pooled"][["estimand", "pct_of_ref", "lo95_pct", "hi95_pct", "p", "cls",
                                         "mde_pct", "n_rows"]].round(4).to_string())
    print(out[out.horizon != "pooled"][["horizon", "estimand", "pct_of_ref", "p"]].round(4).to_string())
    print(lad[lad.horizon == "pooled"].round(5).to_string())


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("part", choices=["tw2021", "nohist"])
    ap.add_argument("--no-br-check", action="store_true")
    a = ap.parse_args()
    if a.part == "tw2021":
        run_tw2021()
    else:
        run_nohist(not a.no_br_check)


if __name__ == "__main__":
    main()
