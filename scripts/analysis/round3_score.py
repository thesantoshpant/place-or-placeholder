#!/usr/bin/env python
"""Round-3 post hoc scoring (EXP-A representation variants, EXP-B extra seeds).

Specs (committed before any of these runs was scored): docs/methods/round3_variants.md,
docs/methods/round3_runs.md. Scoring = results kit v3 exactly: estimands_report.load_cell with
the exclusions_v2 unit/week files, rk_compute.apply_unit_weeks (Espirito Santo) and
rk_compute.apply_row_filter("origin_year"), horizons h{1,4} pooled with equal-week weights,
pop.eval.estimands.infer_estimand (DM on the weekly series, EWC long-run variance + HLN, t-CI,
TOST at +-1% of WIS(L3)). Nothing here re-implements a test.

Usage (repo root, after `source env.sh`):
    nice -n 19 python scripts/analysis/round3_score.py --part variants [--items PATTERN ...]
    nice -n 19 python scripts/analysis/round3_score.py --part seeds    [--items PATTERN ...]
    nice -n 19 python scripts/analysis/round3_score.py --part tuning
    nice -n 19 python scripts/analysis/round3_score.py --part sanity

--items: fnmatch patterns on cell ids (CO_S1, TW_S5, ...) or scheduler item names
(r3a_colombia_s1_r3_V1_L3, r3_co_s1_seeds, ...); default = every cell. A cell is scored only
when every scheduler item it needs reports "done" (scripts/run/scheduler.py status) and every
run dir has scores.parquet; other cells are listed as pending. Results of cells not rescored are
kept from the existing CSV; Holm (variant family) is recomputed over all family rows present.

Outputs: docs/results/review/R3_C_variants.csv, R3_C_seeds.csv, R3_C_tuning.csv.
Blinded run dirs (brazil_s4*, brazil_s2_nohist*, brazil_s1_sens_*) are never read.
"""
from __future__ import annotations

import argparse
import fnmatch
import os
import subprocess
import sys
import time
import warnings
from pathlib import Path

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_MAX_THREADS",
           "POLARS_MAX_THREADS"):
    os.environ[_v] = "6"

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "analysis"))
sys.path.insert(0, str(ROOT / "scripts" / "run"))
os.chdir(ROOT)

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import estimands_report as ER  # noqa: E402
import review_sens as RS  # noqa: E402
import rk_cells as C  # noqa: E402
import rk_compute as K  # noqa: E402
from pop.eval.estimands import ESTIMANDS, infer_estimand  # noqa: E402
from pop.eval.stats import holm  # noqa: E402

warnings.filterwarnings("ignore", category=RuntimeWarning)

OUT = ROOT / "docs" / "results" / "review"
T1 = ROOT / "docs" / "results" / "tables" / "T1_primary_family.csv"
XDIR = ROOT / "data" / "processed" / "exclusions_v2"
EXCL = {"exclude_units": str(XDIR / "no_geometry_units.csv"),
        "exclude_weeks": str(XDIR / "incomplete_weeks.csv"), "late_entry": None,
        "week_actions": ("exclude",)}
UNIT_WEEKS = str(XDIR / "unit_week_exclusions.csv")
HP = [1, 4]
ROW_FILTER = "origin_year"
BLINDED = ("brazil_s4", "brazil_s2_nohist", "brazil_s1_sens_")
CC = {"brazil": "BR", "colombia": "CO", "peru": "PE", "taiwan": "TW"}
SPLIT_NAME = {"S1": "new years (S1)", "S2": "held-out states (S2)", "S3": "held-out blocks (S3)",
              "S4": "held-out random units (S4)", "S5": "held-out country (S5)"}
COUNTRY_NAME = {"BR": "Brazil", "CO": "Colombia", "PE": "Peru", "TW": "Taiwan"}

# ------------------------------------------------------------------ cell definitions
# EXP-A: cell id -> (run prefix, variants). V4 = L2+AE (substitution).
VAR_CELLS = {"CO_S1": ("colombia_s1", ["V1", "V2", "V3", "V4"]),
             "CO_S2": ("colombia_s2", ["V1", "V2", "V3", "V4"]),
             "TW_S1": ("taiwan_s1", ["V1", "V2", "V3", "V4"]),
             "PE_S1": ("peru_s1", ["V1", "V2", "V3", "V4"]),
             "BR_S2": ("brazil_s2", ["V1", "V2"])}
# L2 reference runs (country S1 only; seed 0; L2 params = L1 params = shared set). Extra dirs
# are added only when their scheduler item is done (TW 2021 L2 lives in r3_tw_s1_ladder2021).
L2_RUNS = {"CO_S1": (["runs/colombia_s1_L2"], []),
           "PE_S1": (["runs/peru_s1_L2"], []),
           "TW_S1": (["runs/taiwan_s1_shared_L2"],
                     [("runs/taiwan_s1_r3_tw2021_L2", "r3_tw_s1_ladder2021")])}
# Variant family size fixed by the spec (32 tests: G_emb^V, G_excess^V for V1-V3 and the
# substitution S = WIS(L3) - WIS(L2+AE)).
FAMILY_SIZE = 32

# EXP-B: cell id -> (seed item, run prefix, roles with extra seeds)
ALL4 = ("L3", "L4", "L3C", "L4C")
SEED_CELLS = {"CO_S1": ("r3_co_s1_seeds", "colombia_s1", ALL4),
              "CO_S2": ("r3_co_s2_seeds", "colombia_s2", ALL4),
              "BR_S5": ("r3_br_s5_seeds", "brazil_s5", ALL4),
              "TW_S5": ("r3_tw_s5_seeds", "taiwan_s5", ("L3C", "L4C")),
              "PE_S5": ("r3_pe_s5_seeds", "peru_s5", ("L3C", "L4C")),
              "CO_S3": ("r3_co_s3_seeds", "colombia_s3", ALL4),
              "CO_S4": ("r3_co_s4_seeds", "colombia_s4", ALL4),
              "PE_S1": ("r3_pe_s1_seeds", "peru_s1", ALL4),
              "TW_S1": ("r3_tw_s1_seeds", "taiwan_s1", ALL4)}
STAGE = {"L3": "L3", "L4": "L4", "L3C": "L3_Cstar", "L4C": "L4_Cstar"}


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def cell_name(cid):
    c, s = cid.split("_")[:2]
    return f"{COUNTRY_NAME[c]} {SPLIT_NAME[s]}"


# ------------------------------------------------------------------ guards
_STATUS = None


def item_states() -> dict:
    global _STATUS
    if _STATUS is None:
        r = subprocess.run([sys.executable, "scripts/run/scheduler.py", "status"], capture_output=True,
                           text=True, cwd=ROOT, timeout=600)
        _STATUS = {}
        for line in r.stdout.splitlines():
            t = line.split()
            if len(t) >= 3 and t[0].startswith("T") and t[0][1:].isdigit():
                _STATUS[t[1]] = t[2]
    return _STATUS


def item_done(item) -> bool:
    return item_states().get(item) == "done"


def check_dirs(dirs):
    for d in dirs:
        if any(Path(d).name.startswith(b) for b in BLINDED):
            raise SystemExit(f"refusing blinded run dir {d}")
    return all((ROOT / d / "scores.parquet").exists() for d in dirs)


def registry() -> dict:
    return {c["id"]: c for c in C.build_registry(str(ROOT / "configs" / "primary_cells.yaml"))
            if c["group"] == "primary" and c["id"] != "BR_S4"}


# ------------------------------------------------------------------ loading = kit v3 rows
def load_v3(roles: dict, seeds=None):
    """estimands_report.load_cell (kit exclusions) -> unit-week exclusions -> origin-year row
    filter -> h{1,4}. ``seeds``: keep only these seeds (None = all)."""
    for ds in roles.values():
        check_dirs(ds)
    base = RS.make_reader("wis_log", HP)

    def rd(dirs, cols=("wis_log", "cases", "cov_40", "cov_80")):
        s = base(dirs, cols)
        if seeds is not None:
            s = s[s.seed.isin(list(seeds))].reset_index(drop=True)
        return s
    orig = ER.read_scores
    ER.read_scores = rd
    try:
        g, info = ER.load_cell(roles, **EXCL)
    finally:
        ER.read_scores = orig
    g, ui = K.apply_unit_weeks(g, UNIT_WEEKS)
    g, fi = K.apply_row_filter(g, ROW_FILTER)
    g = K._sub(g, g.horizon.isin(HP).to_numpy()).reset_index(drop=True)
    return g, {**info, **ui, **fi}


def est_fields(q: dict, prefix="") -> dict:
    w = q["wis_ref"]
    return {f"{prefix}estimate": q["estimate"], f"{prefix}pct": 100 * q["estimate"] / w,
            f"{prefix}lo95_pct": 100 * q["lo95"] / w, f"{prefix}hi95_pct": 100 * q["hi95"] / w,
            f"{prefix}lo95": q["lo95"], f"{prefix}hi95": q["hi95"], f"{prefix}se": q["se"],
            f"{prefix}df": q["df"], f"{prefix}p": q["p"], f"{prefix}tost_p": q["tost_p"],
            f"{prefix}cls": q["cls"], f"{prefix}mde_pct": q["mde_pct"],
            f"{prefix}wis_ref": w, f"{prefix}n_rows": q["n_rows"], f"{prefix}n_weeks": q["n_weeks"]}


def infer_col(g, col, ref="wis_L3"):
    """infer_estimand on an arbitrary gain column (no per-seed spread)."""
    a = dict(g.attrs)
    g.attrs = {**a, "seeds": []}
    try:
        return infer_estimand(g, col, ref_col=ref)
    finally:
        g.attrs = a


def t1() -> pd.DataFrame:
    return pd.read_csv(T1).set_index("cell")


# ------------------------------------------------------------------ sanity
def sanity(reg) -> pd.DataFrame:
    """Recompute T1's CO S1 values (L3, L4, L3+C*, L4+C*) and compare."""
    t = t1()
    rows = []
    for cid in ("CO_S1",):
        # seed 0 only: T1 is the seed-0 table; the manifest may list extra seeds (round 3)
        g, info = load_v3({r: reg[cid]["roles"][r]["dirs"] for r in ALL4}, seeds=[0])
        ref = t.loc[cid]
        for e, tcol, pcol in (("G_emb", "G_emb", "G_emb_p"), ("G_id", "G_id", "G_id_p"),
                              ("G_excess", "G_excess", "DM_p")):
            q = infer_estimand(g, e)
            rows.append({"cell": cid, "estimand": e, "ours": q["estimate"], "T1": ref[tcol],
                         "diff": q["estimate"] - ref[tcol], "p_ours": q["p"], "p_T1": ref[pcol],
                         "n_rows_ours": len(g), "n_rows_T1": ref["n_rows"]})
        q = infer_estimand(g, "G_excess")
        rows.append({"cell": cid, "estimand": "G_excess lo95_pct", "ours": 100 * q["lo95"] / q["wis_ref"],
                     "T1": ref["lo95_pct"], "diff": 100 * q["lo95"] / q["wis_ref"] - ref["lo95_pct"]})
    df = pd.DataFrame(rows)
    ok = (df["diff"].abs() < 1e-10).all() and (df.dropna(subset=["n_rows_T1"]).eval(
        "n_rows_ours == n_rows_T1")).all()
    log("sanity:\n" + df.to_string())
    log(f"sanity {'PASS' if ok else 'FAIL'}")
    if not ok:
        raise SystemExit("sanity check failed: kit numbers not reproduced")
    return df


# ------------------------------------------------------------------ EXP-A variants
def variant_items(prefix, v):
    roles = ["L2"] if v == "V4" else ["L3", "L3_Cstar"]
    return [f"r3a_{prefix}_r3_{v}_{r}" for r in roles]


def pair_est(a_dirs, b_dirs, l3_dirs, label: dict, *, ref_from_frame=None) -> dict:
    """Estimate WIS(a) - WIS(b), % of WIS(L3), on rows scored by L3, a and b (seed 0).
    Frame roles: L3 = L3, L4 = b, L3C = a, L4C = b -> column G_excess = a - b."""
    g, info = load_v3({"L3": l3_dirs, "L4": b_dirs, "L3C": a_dirs, "L4C": b_dirs}, seeds=[0])
    q = infer_estimand(g, "G_excess")
    return {**label, **est_fields(q), "rows_not_common": info.get("rows_not_common"),
            "test_years": ",".join(str(y) for y in sorted(g.test_year.unique())),
            "a_runs": ";".join(a_dirs), "b_runs": ";".join(b_dirs)}


def score_variants(reg, pats) -> tuple[pd.DataFrame, list]:
    rows, pending = [], []
    t = t1()
    for cid, (prefix, vs) in VAR_CELLS.items():
        items = [it for v in vs for it in variant_items(prefix, v)]
        if pats and not any(fnmatch.fnmatch(x, p) for p in pats for x in [cid] + items):
            continue
        cell = reg[cid]
        l3 = list(cell["roles"]["L3"]["dirs"])
        l3c = list(cell["roles"]["L3C"]["dirs"])
        orig = t.loc[cid]
        base = {"cell": cid, "cell_name": cell_name(cid), "C_star": orig["C_star"],
                "orig_G_emb_pct": orig["G_emb_pct"], "orig_G_emb_lo95_pct": orig["G_emb_lo95_pct"],
                "orig_G_emb_hi95_pct": orig["G_emb_hi95_pct"], "orig_G_emb_p": orig["G_emb_p"],
                "orig_G_excess_pct": orig["pct_of_WIS_ref"], "orig_G_excess_lo95_pct": orig["lo95_pct"],
                "orig_G_excess_hi95_pct": orig["hi95_pct"], "orig_G_excess_p": orig["DM_p"],
                "orig_G_id_pct": orig["G_id_pct"], "orig_G_id_p": orig["G_id_p"]}
        for v in vs:
            its = variant_items(prefix, v)
            if not all(item_done(i) for i in its):
                pending.append(f"{cid} {v} (items not done: {[i for i in its if not item_done(i)]})")
                continue
            log(f"{cid} {v} ...")
            if v != "V4":
                dv, dvc = [f"runs/{prefix}_r3_{v}_L3"], [f"runs/{prefix}_r3_{v}_L3_Cstar"]
                if not check_dirs(dv + dvc):
                    pending.append(f"{cid} {v} (scores.parquet missing)")
                    continue
                rows.append(pair_est(l3, dv, l3, {**base, "variant": v, "estimand": "G_emb_V",
                                                  "contrast": f"L3 - L3+{v}", "in_family": True}))
                rows.append(pair_est(l3c, dvc, l3, {**base, "variant": v, "estimand": "G_excess_V",
                                                   "contrast": f"L3+C* - L3+C*+{v}", "in_family": True}))
                if v == "V1":   # direct: does embedding-similarity risk beat geographic C1?
                    rows.append(pair_est(l3c, dv, l3, {**base, "variant": v, "estimand": "V1_vs_Cstar",
                                                      "contrast": "L3+C* - L3+V1", "in_family": False}))
            else:
                dae = [f"runs/{prefix}_r3_V4_L2"]
                if not check_dirs(dae):
                    pending.append(f"{cid} V4 (scores.parquet missing)")
                    continue
                rows.append(pair_est(l3, dae, l3, {**base, "variant": v, "estimand": "S_L3_vs_L2AE",
                                                  "contrast": "L3 - L2+AE", "in_family": True}))
                if cid in L2_RUNS:
                    l2, extra = L2_RUNS[cid]
                    l2 = list(l2) + [d for d, it in extra if item_done(it) and check_dirs([d])]
                    note = "" if len(l2) == 1 + len(L2_RUNS[cid][1]) else "L2 test year 2021 pending; rows without 2021"
                    if check_dirs(l2):
                        r = pair_est(l2, dae, l3, {**base, "variant": v, "estimand": "S_L2_vs_L2AE",
                                                   "contrast": "L2 - L2+AE", "in_family": False})
                        r["note"] = note
                        rows.append(r)
                else:
                    pending.append(f"{cid} V4: no L2 run for this split (L2 - L2+AE not estimable)")
    return pd.DataFrame(rows), pending


def finish_variants(new: pd.DataFrame) -> pd.DataFrame:
    f = OUT / "R3_C_variants.csv"
    if f.exists() and len(new):
        old = pd.read_csv(f)
        key = set(zip(new.cell, new.variant))
        old = old[[(c, v) not in key for c, v in zip(old.cell, old.variant)]]
        df = pd.concat([old, new], ignore_index=True)
    else:
        df = new if len(new) else pd.read_csv(f)
    fam = df.in_family.astype(bool)
    df["holm_p_family"] = np.nan
    df.loc[fam, "holm_p_family"] = holm(df.loc[fam, "p"].to_numpy())
    df["family_tests_available"] = int(fam.sum())
    df["family_size_spec"] = FAMILY_SIZE
    order = {"G_emb_V": 0, "G_excess_V": 1, "V1_vs_Cstar": 2, "S_L3_vs_L2AE": 3, "S_L2_vs_L2AE": 4}
    df = df.assign(_o=df.estimand.map(order)).sort_values(["cell", "variant", "_o"]).drop(columns="_o")
    df.to_csv(f, index=False)
    log(f"wrote {f} ({len(df)} rows; family tests {int(fam.sum())}/{FAMILY_SIZE})")
    return df


# ------------------------------------------------------------------ EXP-B seeds
def seed_roles(cell, prefix, extra_roles):
    roles = {}
    for r in ALL4:
        ds = list(cell["roles"][r]["dirs"])
        if r in extra_roles:
            ds += [d for d in (f"runs/{prefix}_r3_seed{s}_{STAGE[r]}" for s in (1, 2)) if d not in ds]
        roles[r] = ds
    return roles


def score_seeds(reg, pats) -> tuple[pd.DataFrame, list]:
    rows, pending = [], []
    t = t1()
    for cid, (item, prefix, extra) in SEED_CELLS.items():
        if pats and not any(fnmatch.fnmatch(x, p) for p in pats for x in (cid, item)):
            continue
        if not item_done(item):
            pending.append(f"{cid} ({item}: {item_states().get(item, 'unknown')})")
            continue
        roles = seed_roles(reg[cid], prefix, extra)
        if not all(check_dirs(ds) for ds in roles.values()):
            pending.append(f"{cid} (scores.parquet missing)")
            continue
        log(f"{cid} seeds ...")
        g, info = load_v3(roles)
        orig = t.loc[cid]
        for e in ("G_excess", "G_emb", "G_id"):
            q = infer_estimand(g, e)       # kit multi-seed estimator (common seeds per row)
            base = {"cell": cid, "cell_name": cell_name(cid), "C_star": orig["C_star"], "estimand": e,
                    "n_seeds": q["n_seeds"], "seed_sd": q["seed_sd"],
                    "seed_sd_pct": 100 * q["seed_sd"] / q["wis_ref"] if q["n_seeds"] > 1 else np.nan,
                    "T1_seed0_pct": orig["pct_of_WIS_ref"] if e == "G_excess" else orig[f"{e}_pct"],
                    "T1_seed0_p": orig["DM_p"] if e == "G_excess" else orig[f"{e}_p"]}
            rows.append({**base, "seed": "mean", **est_fields(q)})
            for s in sorted(q["seed_estimates"]) if q["n_seeds"] > 1 else [0]:
                m = g[f"has_{e}@{s}"].to_numpy(bool)
                sub = K._sub(g, m)
                qs = infer_col(sub, f"{e}@{s}", ref=f"wis_L3@{s}" if sub[f"wis_L3@{s}"].notna().all()
                               else "wis_L3")
                rows.append({**base, "seed": str(s), **est_fields(qs)})
    return pd.DataFrame(rows), pending


def finish_simple(new: pd.DataFrame, name: str) -> pd.DataFrame:
    f = OUT / name
    if f.exists() and len(new):
        old = pd.read_csv(f)
        old = old[~old.cell.isin(set(new.cell))]
        df = pd.concat([old, new], ignore_index=True)[list(new.columns)]
    else:
        df = new if len(new) else (pd.read_csv(f) if f.exists() else new)
    df.to_csv(f, index=False)
    log(f"wrote {f} ({len(df)} rows)")
    return df


# ------------------------------------------------------------------ EXP-B S4 tuning (CO S1)
def score_tuning(reg, pats) -> tuple[pd.DataFrame, list]:
    """G_excess best-for-each = WIS(tuned L3+C1) - WIS(tuned L4+C1), beside the shared one."""
    item, cid = "r3_co_s1_tuning", "CO_S1"
    if pats and not any(fnmatch.fnmatch(x, p) for p in pats for x in (cid, item)):
        return pd.DataFrame(), []
    if not item_done(item):
        return pd.DataFrame(), [f"{cid} tuning ({item}: {item_states().get(item, 'unknown')})"]
    cell = reg[cid]
    tl3, tl4 = ["runs/colombia_s1_r3_tuned_L3_Cstar"], ["runs/colombia_s1_r3_tuned_L4_Cstar"]
    if not check_dirs(tl3 + tl4):
        return pd.DataFrame(), [f"{cid} tuning (scores.parquet missing)"]
    l3 = list(cell["roles"]["L3"]["dirs"])
    base = {"cell": cid, "cell_name": cell_name(cid)}
    rows = [pair_est(tl3, tl4, l3, {**base, "estimand": "G_excess_tuned",
                                    "contrast": "tuned L3+C1 - tuned L4+C1"}),
            pair_est(list(cell["roles"]["L3C"]["dirs"]), list(cell["roles"]["L4C"]["dirs"]), l3,
                     {**base, "estimand": "G_excess_shared", "contrast": "L3+C1 - L4+C1 (shared)"}),
            pair_est(list(cell["roles"]["L3C"]["dirs"]), tl3, l3,
                     {**base, "estimand": "tuning_gain_L3C", "contrast": "shared - tuned L3+C1"}),
            pair_est(list(cell["roles"]["L4C"]["dirs"]), tl4, l3,
                     {**base, "estimand": "tuning_gain_L4C", "contrast": "shared - tuned L4+C1"})]
    return pd.DataFrame(rows), []


# ------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--part", required=True, choices=["variants", "seeds", "tuning", "sanity"])
    ap.add_argument("--items", nargs="*", default=[], help="fnmatch patterns on cell ids / item names")
    ap.add_argument("--no-sanity", action="store_true")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    reg = registry()
    if a.part == "sanity" or not a.no_sanity:
        sanity(reg)
        if a.part == "sanity":
            return
    fn = {"variants": score_variants, "seeds": score_seeds, "tuning": score_tuning}[a.part]
    new, pending = fn(reg, a.items)
    if a.part == "variants":
        finish_variants(new)
    else:
        finish_simple(new, f"R3_C_{a.part}.csv")
    if pending:
        log("pending / skipped:\n  " + "\n  ".join(pending))


if __name__ == "__main__":
    main()
