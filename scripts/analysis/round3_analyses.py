#!/usr/bin/env python
"""Round-3 review analyses R3-A1..A8 from EXISTING scores/forecasts (no model is refitted).

Spec: audits/final_round/TRIAGE_round3.md section B. Scoring = results kit v3 exactly
(rk_compute: exclusions_v2 incl. unit-week exclusions + origin-year row filter, primary
horizons h{1,4} pooled with equal-week weights, DM/EWC + HLN via pop.eval).

Usage (repo root, after `source env.sh`):
    nice -n 19 python scripts/analysis/round3_analyses.py [--only A1,A2,...] [--exclude BR_S4]
        [--force] [--reps 2000]

--exclude defaults to the blinded cell BR_S4; cells whose runs are incomplete are skipped and
listed. Rerun with `--exclude ""` after unblinding to cover all 14 cells. Per-cell intermediate
results are cached under tmp/round3_analyses/<cell>/ (keyed by the run fingerprints).

Outputs (docs/results/review/): R3_A1_positive_control.csv, R3_A2_nocontrol_rule.csv,
R3_A3_per_year.csv (+ R3_A3_trend.csv), R3_A4_equivalence.csv, R3_A5_planned_vs_reported.csv,
R3_A6_outcome_agnostic.csv, R3_A7_embedding_stability.csv, R3_A8_iaaft_equivalence.csv.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
import warnings
from pathlib import Path

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_MAX_THREADS",
           "POLARS_MAX_THREADS"):
    os.environ.setdefault(_v, "8")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "analysis"))
sys.path.insert(0, str(ROOT / "scripts" / "run"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy import stats as st  # noqa: E402

import estimands_report as ER  # noqa: E402
import review_sens as RS  # noqa: E402
import rk_cells as C  # noqa: E402
import rk_compute as K  # noqa: E402
from pop.eval.estimands import infer_estimand, weekly_pooled  # noqa: E402
from pop.eval.stats import dm_test, ewc_inference, holm, tost_p  # noqa: E402

warnings.filterwarnings("ignore", category=RuntimeWarning)

OUT = ROOT / "docs" / "results" / "review"
TAB = ROOT / "docs" / "results" / "tables"
CACHE = ROOT / "tmp" / "round3_analyses"
XDIR = ROOT / "data" / "processed" / "exclusions_v2"
EXCL = {"exclude_units": str(XDIR / "no_geometry_units.csv"),
        "exclude_weeks": str(XDIR / "incomplete_weeks.csv"), "late_entry": None,
        "week_actions": ("exclude",)}
UNIT_WEEKS = str(XDIR / "unit_week_exclusions.csv")
HP = [1, 4]
MARGINS = (0.5, 1.0, 2.0)
BLINDED = ["BR_S4"]
FIRST_TRAIN_YEAR = 2018
ALL = ["A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8"]
L2_DIR = {"brazil": "runs/brazil_s1_L2", "colombia": "runs/colombia_s1_L2",
          "peru": "runs/peru_s1_L2", "taiwan": "runs/taiwan_s1_shared_L2"}
L2_NOTE = {"brazil": "L2 params = L1 (127/100)", "colombia": "L2 per-level params = L1 params",
           "peru": "L2 per-level params = L1 params", "taiwan": "shared-param L2 run (taiwan_s1_shared_L2)"}
PERLEVEL = {"PE_S1": {"L3": ["runs/peru_s1_L3"], "L4": ["runs/peru_s1_L4"],
                      "L3C": ["runs/peru_s1_L3_Cstar"], "L4C": ["runs/peru_s1_L4_Cstar"]},
            "TW_S1": {"L3": ["runs/taiwan_s1_L3"], "L4": ["runs/taiwan_s1_L4"],
                      "L3C": ["runs/taiwan_s1_L3_Cstar"], "L4C": ["runs/taiwan_s1_L4_Cstar"]}}


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


# ============================================================== loading (kit v3 rows)
LABEL_FILTER: dict[str, str] = {}    # run dir name -> run label to keep (baselines dirs)


def _reader(horizons):
    base = RS.make_reader("wis_log", horizons)

    def rd(dirs, cols=("wis_log", "cases", "cov_40", "cov_80")):
        s = base(dirs, cols)
        if LABEL_FILTER:
            keep = s.dir.map(LABEL_FILTER)
            s = s[keep.isna() | (s.label == keep)].reset_index(drop=True)
        return s
    return rd


def load_v3(roles: dict, horizons=HP) -> tuple[pd.DataFrame, dict]:
    """The kit v3 primary rows (rk_compute.compute_cell): load_cell with the v2 exclusions,
    unit-week exclusions, origin-year row filter, primary horizons."""
    orig = ER.read_scores
    ER.read_scores = _reader(horizons)
    try:
        g, info = ER.load_cell(roles, **EXCL)
    finally:
        ER.read_scores = orig
    g, ui = K.apply_unit_weeks(g, UNIT_WEEKS)
    g, fi = K.apply_row_filter(g, "origin_year")
    g = K._sub(g, g.horizon.isin(horizons).to_numpy()).reset_index(drop=True)
    return g, {**info, **ui, **fi}


def infer_col(g, col, ref="wis_L3"):
    """Primary inference on an arbitrary row-gain column (no per-seed columns)."""
    a = dict(g.attrs)
    g.attrs = {**a, "seeds": []}
    try:
        return infer_estimand(g, col, ref_col=ref)
    finally:
        g.attrs = a


def est_dict(q: dict, prefix="") -> dict:
    keys = ("estimate", "se", "df", "p", "lo95", "hi95", "lo90", "hi90", "wis_ref", "pct_of_ref",
            "cls", "mde_pct", "n_rows", "n_weeks")
    d = {f"{prefix}{k}": q.get(k, np.nan) for k in keys}
    w = q.get("wis_ref", np.nan)
    d[f"{prefix}lo95_pct"] = 100 * q["lo95"] / w
    d[f"{prefix}hi95_pct"] = 100 * q["hi95"] / w
    return d


def fp(dirs) -> str:
    parts = []
    for d in dirs:
        p = Path(d) / "scores.parquet"
        parts.append([str(d), p.stat().st_size, p.stat().st_mtime_ns] if p.exists() else [str(d)])
    return hashlib.sha1(json.dumps(parts).encode()).hexdigest()[:12]


def cached(cell_id, name, key, fn, force=False):
    d = CACHE / cell_id
    f, kf = d / f"{name}.parquet", d / f"{name}.key"
    if not force and f.exists() and kf.exists() and kf.read_text() == key:
        return pd.read_parquet(f)
    df = fn()
    d.mkdir(parents=True, exist_ok=True)
    df.to_parquet(f, index=False)
    kf.write_text(key)
    return df


def registry(exclude):
    cells, skipped = [], []
    for c in C.build_registry(str(ROOT / "configs" / "primary_cells.yaml")):
        if c["group"] != "primary":
            continue
        if c["id"] in exclude:
            skipped.append(f"{c['id']} (excluded: blinded)")
            continue
        stt, roles = C.cell_status(c)
        if stt != "available":
            skipped.append(f"{c['id']} (runs incomplete)")
            continue
        cells.append(c)
    return cells, skipped


def roles_of(cell):
    return {r: list(cell["roles"][r]["dirs"]) for r in C.ROLES}


def t1():
    return pd.read_csv(TAB / "T1_primary_family.csv").set_index("cell")


def kit_est(cid):
    f = ROOT / "runs" / "analysis_cache" / cid / "est.parquet"
    return pd.read_parquet(f) if f.exists() else None


def kit_extra(cid, name):
    f = ROOT / "runs" / "analysis_cache" / cid / "extras" / f"{name}.parquet"
    return pd.read_parquet(f) if f.exists() else None


# ============================================================== A1 positive control / anchor
def a1_cell(cell):
    country = cell["country"]
    base = f"runs/{country}_s1_baselines"
    LABEL_FILTER.clear()
    LABEL_FILTER[Path(base).name] = "lgbm-L1"
    roles = {"L3": [base], "L4": [L2_DIR[country]],
             "L3C": roles_of(cell)["L3"], "L4C": roles_of(cell)["L4"]}
    try:
        g, info = load_v3(roles)
    finally:
        LABEL_FILTER.clear()
    # wis_L3 = L1, wis_L4 = L2, wis_L3C = L3, wis_L4C = L4 (seed-averaged losses, as in T2 ladder)
    g["d_L1_L2"] = g.wis_L3 - g.wis_L4
    g["d_L2_L3"] = g.wis_L4 - g.wis_L3C
    g["d_L1_L3"] = g.wis_L3 - g.wis_L3C
    g["d_L3_L4"] = g.wis_L3C - g.wis_L4C
    g["d_L1_L4"] = g.wis_L3 - g.wis_L4C
    rows = []
    years = sorted(int(y) for y in g.test_year.unique())
    for col, lab in (("d_L1_L2", "L1->L2 (climate)"), ("d_L2_L3", "L2->L3 (RS + pop)"),
                     ("d_L1_L3", "L1->L3 (all non-case covariates)"), ("d_L3_L4", "L3->L4 (embedding, no control)"),
                     ("d_L1_L4", "L1->L4")):
        q = infer_col(g, col, ref="wis_L3C")
        r = {"cell": cell["id"], "increment": lab, **est_dict(q)}
        r["pct_of_WIS_L3"] = r.pop("pct_of_ref")
        r["wis_L1"] = float(weekly_pooled(g, "wis_L3").mean())
        r["test_years"] = ",".join(map(str, years))
        rows.append(r)
    return pd.DataFrame(rows)


def run_a1(cells, force):
    T1 = t1()
    out = []
    for c in cells:
        if c["split"] != "S1":
            continue
        dirs = sum(roles_of(c).values(), []) + [f"runs/{c['country']}_s1_baselines", L2_DIR[c["country"]]]
        log(f"A1 {c['id']}")
        df = cached(c["id"], "A1", fp(dirs), lambda: a1_cell(c), force)
        gx = T1.loc[c["id"]]
        tot = df.set_index("increment").loc["L1->L3 (all non-case covariates)"]
        df["G_excess_primary_pct"] = gx.pct_of_WIS_ref
        df["G_emb_primary_pct"] = gx.G_emb_pct
        df["G_excess_over_L1L3_gain"] = gx.pct_of_WIS_ref / tot.pct_of_WIS_L3
        df["margin1_over_L1L3_gain"] = 1.0 / tot.pct_of_WIS_L3
        df["margin05_over_L1L3_gain"] = 0.5 / tot.pct_of_WIS_L3
        note = f"L1 = runs/{c['country']}_s1_baselines (lgbm-L1); {L2_NOTE[c['country']]}; L3/L4 = primary runs, seed-averaged"
        if c["country"] == "taiwan":
            note += ("; Taiwan 2021 NOT included (L1/L2 with 2021 do not exist yet; EXP-B runs pending); "
                     "the primary G_excess columns include 2021")
            nx = t1_no2021("TW_S1")
            if nx is not None:
                df["G_excess_no2021_pct"] = nx
        df["note"] = note
        out.append(df)
    res = pd.concat(out, ignore_index=True)
    res.to_csv(OUT / "R3_A1_positive_control.csv", index=False)
    return res


def t1_no2021(cid):
    e = kit_est(f"{cid}_no2021")
    if e is None:
        return None
    r = e[(e.horizon == "pooled") & (e.test_year == "pooled") & (e.stratum == "all") & (e.estimand == "G_excess")]
    return float(r.pct_of_ref.iloc[0]) if len(r) else None


# ============================================================== A2 no-control rule
def run_a2(cells):
    T1 = t1()
    rows = []
    for c in cells:
        f = Path(c["selection"]["dir"]) / "selection.json"
        j = json.loads(f.read_text())
        ref = j["ref_wis_log"]
        sig = j.get("sigma_seed") or 0.0
        best = None
        for k, v in j["candidates"].items():
            if v.get("wis_log") is None:
                continue
            se_d = float(np.hypot(v.get("se") or 0.0, sig))
            delta = v["wis_log"] - ref
            if best is None or delta < best[1]:
                best = (k, delta, se_d)
        sel = j["candidates"].get(j["c_star"], {})
        sel_delta = sel.get("wis_log", np.nan) - ref
        beats_2se = [k for k, v in j["candidates"].items() if v.get("wis_log") is not None
                     and v["wis_log"] - ref < -2 * float(np.hypot(v.get("se") or 0.0, sig))]
        x = T1.loc[c["id"]]
        none = len(beats_2se) == 0
        e = "G_emb" if none else "G_excess"
        pre = "G_emb_" if none else ""
        est_pct = x.G_emb_pct if none else x.pct_of_WIS_ref
        rows.append({
            "cell": c["id"], "C_star_v2": j["c_star"], "ref_wis_2019": ref, "sigma_seed": sig,
            "Cstar_delta_vs_L3_2019": sel_delta, "Cstar_beat_L3_2019": bool(sel_delta < 0),
            "best_control_2019": best[0], "best_delta_vs_L3_2019": best[1], "best_se_diff": best[2],
            "controls_beating_L3_by_2SE": ",".join(beats_2se),
            "rule_noctrl_Cstar": "none" if none else j["c_star"], "estimand_used": e,
            "est_pct": est_pct,
            "lo95_pct": x[f"{pre}lo95_pct"] if not none else x.G_emb_lo95_pct,
            "hi95_pct": x[f"{pre}hi95_pct"] if not none else x.G_emb_hi95_pct,
            "p": x.G_emb_p if none else x.DM_p,
            "class_1pct": x.G_emb_class if none else x.TOST_class,
            "G_excess_pct_primary": x.pct_of_WIS_ref, "G_excess_p_primary": x.DM_p,
            "G_emb_pct": x.G_emb_pct, "G_emb_p": x.G_emb_p,
            "G_id_pct": x.G_id_pct, "G_id_lo95_pct": x.G_id_lo95_pct, "G_id_hi95_pct": x.G_id_hi95_pct,
            "G_id_CI_below_0": bool(x.G_id_hi95_pct < 0), "G_id_CI_above_0": bool(x.G_id_lo95_pct > 0)})
    df = pd.DataFrame(rows)
    df["Holm_p"] = holm(df.p.to_numpy())
    df["Holm_p_primary"] = holm(df.G_excess_p_primary.to_numpy())
    df["n_cells_holm"] = len(df)
    df["se_rule"] = ("beat = control 2019 WIS < L3 2019 WIS - 2*sqrt(se_cand^2 + sigma_seed^2) "
                     "(se_cand, sigma_seed from selection.json; seed-noise SE only)")
    df.to_csv(OUT / "R3_A2_nocontrol_rule.csv", index=False)
    return df


# ============================================================== A3 per-year + trend
def wls_slope(x, y, se):
    x, y, se = map(lambda a: np.asarray(a, float), (x, y, se))
    ok = np.isfinite(x) & np.isfinite(y) & np.isfinite(se) & (se > 0)
    x, y, w = x[ok], y[ok], 1 / se[ok] ** 2
    n = len(x)
    if n < 3 or np.ptp(x) == 0:
        return {"n_years": n, "slope": np.nan}
    X = np.column_stack([np.ones(n), x])
    XtW = X.T * w
    cov = np.linalg.inv(XtW @ X)
    b = cov @ XtW @ y
    res = y - X @ b
    s2 = float((w * res ** 2).sum() / (n - 2))
    se_known = float(np.sqrt(cov[1, 1]))
    se_scaled = float(np.sqrt(cov[1, 1] * max(s2, 1.0)))   # never narrower than the known-variance SE
    return {"n_years": n, "slope": float(b[1]), "slope_se_known": se_known,
            "p_known_z": float(2 * st.norm.sf(abs(b[1] / se_known))),
            "slope_se_scaled": se_scaled, "p_scaled_t": float(2 * st.t.sf(abs(b[1] / se_scaled), n - 2)),
            "residual_dispersion": s2}


def fe_slope(df):
    """Common slope with cell intercepts (WLS, weights 1/se^2, known variance)."""
    cells = sorted(df.cell.unique())
    X = np.column_stack([(df.cell == c).to_numpy(float) for c in cells] + [df.n_train_years.to_numpy(float)])
    w = 1 / df.se_pct.to_numpy() ** 2
    cov = np.linalg.inv((X.T * w) @ X)
    b = cov @ (X.T * w) @ df.pct.to_numpy()
    se = float(np.sqrt(cov[-1, -1]))
    return {"slope": float(b[-1]), "slope_se_known": se, "p_known_z": float(2 * st.norm.sf(abs(b[-1] / se))),
            "n_years": len(df), "n_cells": len(cells)}


def a3_dm(cell, g):
    rows = []
    s = K._sub(g, g.test_year.isin([2023, 2024]).to_numpy())
    for est in ("G_excess", "G_emb"):
        q = infer_estimand(s, est)
        d = weekly_pooled(s, est).to_numpy()
        b4 = K.ewc_fixed_B(d, 4, 4)
        rows.append({"cell": cell["id"], "estimand": est, "test_year": "2023-2024",
                     "n_train_years": np.nan, "estimate": q["estimate"], "pct": q["pct_of_ref"],
                     "se_pct": 100 * q["se"] / q["wis_ref"], "df": q["df"],
                     "lo95_pct": 100 * q["lo95"] / q["wis_ref"], "hi95_pct": 100 * q["hi95"] / q["wis_ref"],
                     "p": q["p"], "B4_p": b4["p"], "wis_ref": q["wis_ref"], "n_weeks": q["n_weeks"],
                     "covid_year": False, "source": "DM/EWC+HLN on 2023-24 rows only (post hoc)"})
    return pd.DataFrame(rows)


def run_a3(cells, dm_parts):
    rows = []
    for c in cells:
        e = kit_est(c["id"])
        e = e[(e.horizon == "pooled") & (e.stratum == "all") & (e.test_year != "pooled")
              & e.estimand.isin(["G_excess", "G_emb"])]
        for _, r in e.iterrows():
            y = int(r.test_year)
            rows.append({"cell": c["id"], "estimand": r.estimand, "test_year": str(y),
                         "n_train_years": y - FIRST_TRAIN_YEAR, "estimate": r.estimate,
                         "pct": r.pct_of_ref, "se_pct": 100 * r.se / r.wis_ref, "df": r.df,
                         "lo95_pct": 100 * r.lo95 / r.wis_ref, "hi95_pct": 100 * r.hi95 / r.wis_ref,
                         "p": r.p, "wis_ref": r.wis_ref, "n_weeks": r.n_weeks,
                         "covid_year": y in (2020, 2021), "source": "kit v3 cache (est.parquet)"})
    per = pd.concat([pd.DataFrame(rows)] + list(dm_parts), ignore_index=True)
    per.to_csv(OUT / "R3_A3_per_year.csv", index=False)
    yr = per[per.test_year != "2023-2024"]
    tr = []
    for (cid, est), s in yr.groupby(["cell", "estimand"]):
        for lab, m in (("all test years", np.ones(len(s), bool)), ("excl. 2020-21 (COVID)", ~s.covid_year.to_numpy())):
            tr.append({"cell": cid, "estimand": est, "years": lab,
                       **wls_slope(s.n_train_years[m], s.pct[m], s.se_pct[m])})
    for est in ("G_excess", "G_emb"):
        for grp, pref in (("all cells", ""), ("Brazil cells", "BR_"), ("Colombia cells", "CO_")):
            s = yr[(yr.estimand == est) & yr.cell.str.startswith(pref) & ~yr.cell.str.startswith("TW_S5")]
            if len(s) >= 4:
                tr.append({"cell": f"pooled: {grp} (excl. TW S5)", "estimand": est, "years": "all test years",
                           **fe_slope(s)})
    trd = pd.DataFrame(tr)
    trd["note"] = ("post hoc; slope = change in % of WIS(L3) per extra training year; WLS weights 1/se^2; "
                   "3-5 points per cell; 2020-21 COVID-affected; pooled slopes ignore cross-cell dependence")
    trd.to_csv(OUT / "R3_A3_trend.csv", index=False)
    return per, trd


# ============================================================== A4 equivalence variants
def run_a4(cells):
    rows = []
    t4 = st.t.ppf(0.975, 4)
    for c in cells:
        e = kit_est(c["id"])
        e = e[(e.horizon == "pooled") & (e.test_year == "pooled") & (e.stratum == "all")].set_index("estimand")
        rb = kit_extra(c["id"], "robust").set_index("estimand")
        for est in ("G_excess", "G_emb"):
            r = e.loc[est]
            w = r.wis_ref
            b = rb.loc[est]
            se_b4 = (b.B4_hi95_pct - b.B4_lo95_pct) / 100 * w / (2 * t4)
            for sev, se, df in (("EWC (primary)", r.se, r.df), ("EWC B=4", se_b4, 4.0)):
                for m in MARGINS:
                    mg = m / 100 * w
                    tq = st.t.ppf(0.95, df)
                    rows.append({"cell": c["id"], "estimand": est, "se_variant": sev, "margin_pct": m,
                                 "pct": 100 * r.estimate / w, "se_pct": 100 * se / w, "df": df,
                                 "lo90_pct": 100 * (r.estimate - tq * se) / w,
                                 "hi90_pct": 100 * (r.estimate + tq * se) / w,
                                 "TOST_p": tost_p(r.estimate, se, df, mg)})
    df = pd.DataFrame(rows)
    df["TOST_p_Holm"] = np.nan
    for _, idx in df.groupby(["estimand", "se_variant", "margin_pct"]).groups.items():
        df.loc[idx, "TOST_p_Holm"] = holm(df.loc[idx, "TOST_p"].to_numpy())
    df["equivalent_unadj"] = df.TOST_p < 0.05
    df["equivalent_Holm"] = df.TOST_p_Holm < 0.05
    df["n_cells_holm"] = df.groupby(["estimand", "se_variant", "margin_pct"]).cell.transform("size")
    df.to_csv(OUT / "R3_A4_equivalence.csv", index=False)
    return df


# ============================================================== per-cell loaded analyses
def a6_cell(cell, g):
    """(a) unit-years with >= 1 case; (b) coverage / width on case vs zero weeks."""
    rows = []
    uy = g.groupby(["unit_id", "test_year"]).cases.transform("max").to_numpy() > 0
    s = K._sub(g, uy)
    for est in ("G_excess", "G_emb"):
        q = infer_estimand(s, est)
        rows.append({"cell": cell["id"], "analysis": "a: unit-years with >=1 case", "estimand": est,
                     "row_share": float(uy.mean()), **est_dict(q)})
    km = RS.KeyMap(g)
    pos = g.cases.to_numpy(float) > 0
    vals = {}
    for r in ("L3C", "L4C"):
        cv = RS.role_coverage(km, cell["roles"][r]["dirs"], HP)
        wd, _ = RS.scan_forecasts(km, cell["roles"][r]["dirs"], HP, check_wis=False)
        vals[r] = {"cov_80": cv["cov_80"], "cov_40": cv["cov_40"], "w80_log": wd["w80_log"],
                   "w80_case": wd["w80_case"]}
    for metric in ("cov_80", "cov_40", "w80_log", "w80_case"):
        for lab, m in (("case weeks (y>0)", pos), ("zero weeks (y=0)", ~pos)):
            a, b = vals["L3C"][metric], vals["L4C"][metric]
            ok = m & np.isfinite(a) & np.isfinite(b)
            tmp = pd.DataFrame({"target_week": g.target_week[ok].to_numpy(), "horizon": g.horizon[ok].to_numpy(),
                                "d": (b - a)[ok]})
            d = weekly_pooled(tmp, "d").to_numpy()
            inf = ewc_inference(d, h=4)
            nominal = {"cov_80": 0.8, "cov_40": 0.4}.get(metric)
            ra, rb_ = float(np.mean(a[ok])), float(np.mean(b[ok]))
            rows.append({"cell": cell["id"], "analysis": "b: coverage/width L4+C* minus L3+C*",
                         "metric": metric, "stratum": lab, "n_rows": int(ok.sum()),
                         "L3C_mean": ra, "L4C_mean": rb_, "diff_row_mean": rb_ - ra,
                         "diff_week_mean": inf.estimate, "diff_lo95": inf.lo95, "diff_hi95": inf.hi95,
                         "diff_p": inf.p,
                         "toward_nominal": (abs(rb_ - nominal) < abs(ra - nominal)) if nominal else np.nan})
    return pd.DataFrame(rows)


def a8_cell(cell, g, reps, seed=20261119):
    from inference_size_sim import IAAFT
    import zlib
    d = weekly_pooled(g, "G_excess").to_numpy()
    d = d[np.isfinite(d)]
    w = float(weekly_pooled(g, "wis_L3").mean())
    obs = ewc_inference(d, h=4)
    gen = IAAFT(d)
    rng = np.random.default_rng([seed, zlib.crc32(cell["id"].encode())])
    t_p, t_b4 = np.empty(reps), np.empty(reps)
    for i in range(reps):
        x = gen.draw(rng)
        t_p[i] = abs(dm_test(x, h=4, lag="ewc").stat)
        b = K.ewc_fixed_B(x, 4, 4)
        t_b4[i] = abs(b["estimate"] / b["se"]) if b["se"] > 0 else 0.0
    rows = []
    b4o = K.ewc_fixed_B(d, 4, 4)
    for meth, tt, df, se in (("ewc_hln (primary)", t_p, obs.df, obs.se), ("ewc_hln_B4", t_b4, 4.0, b4o["se"])):
        size = float((tt > st.t.ppf(0.975, df)).mean())
        q90 = float(np.quantile(tt, 0.90))      # calibrated two-sided 10% critical value -> 90% CI
        f90 = q90 / st.t.ppf(0.95, df)
        lo, hi = obs.estimate - q90 * se, obs.estimate + q90 * se
        rows.append({"cell": cell["id"], "method": meth, "T": len(d), "reps": reps,
                     "size_nominal5": size, "calibrated_crit90": q90, "ci_widen_factor_90": f90,
                     "pct": 100 * obs.estimate / w, "cal_lo90_pct": 100 * lo / w, "cal_hi90_pct": 100 * hi / w,
                     "equivalent_1pct_calibrated": bool(lo > -0.01 * w and hi < 0.01 * w),
                     "equivalent_05pct_calibrated": bool(lo > -0.005 * w and hi < 0.005 * w)})
    return pd.DataFrame(rows)


def seed0_cell(cell, g):
    if "G_excess@0" not in g:
        return pd.DataFrame()
    out = []
    for est in ("G_excess", "G_emb"):
        m = g[f"has_{est}@0"].to_numpy(bool)
        s = K._sub(g, m)
        s = s.assign(_x=s[f"{est}@0"].to_numpy())
        s.attrs = dict(g.attrs)
        q = infer_col(s, "_x")
        out.append({"cell": cell["id"], "variant": "single seed (seed 0)", "estimand": est, **est_dict(q)})
    return pd.DataFrame(out)


def run_loaded(cells, which, force, reps):
    """Load each cell once; compute the per-cell parts of A3 (BR 2023-24), A5 (seed 0,
    per-level), A6 and A8. Returns {part: DataFrame}."""
    T1 = t1()
    parts = {"A6": [], "A8": [], "A3_dm": [], "A5_seed0": [], "A5_perlevel": [], "check": []}
    eq_cells = set(T1.index[T1.TOST_class == "equivalent"])
    for c in cells:
        need6 = "A6" in which
        need8 = "A8" in which and c["id"] in eq_cells
        need3 = "A3" in which and c["country"] == "brazil"
        need5 = "A5" in which and c["id"] == "BR_S1"
        if not (need6 or need8 or need3 or need5):
            continue
        key = fp(sum(roles_of(c).values(), []))
        names = ((["A6"] if need6 else []) + (["A8"] if need8 else []) + (["A5_seed0"] if need5 else [])
                 + (["A3_dm"] if need3 else []))
        hit = all((CACHE / c["id"] / f"{n}.key").exists() and (CACHE / c["id"] / f"{n}.key").read_text() == key
                  for n in names) and not force
        g = None
        if not hit:
            log(f"load {c['id']}")
            g, info = load_v3(roles_of(c))
            q = infer_estimand(g, "G_excess")
            parts["check"].append({"cell": c["id"], "G_excess_pct_here": q["pct_of_ref"],
                                   "G_excess_pct_T1": T1.loc[c["id"]].pct_of_WIS_ref,
                                   "n_rows_here": len(g), "n_rows_T1": T1.loc[c["id"]].n_rows})
        if need3:
            parts["A3_dm"].append(cached(c["id"], "A3_dm", key, lambda: a3_dm(c, g), force))
        if need6:
            log(f"A6 {c['id']}")
            parts["A6"].append(cached(c["id"], "A6", key, lambda: a6_cell(c, g), force))
        if need8:
            log(f"A8 {c['id']}")
            parts["A8"].append(cached(c["id"], "A8", key, lambda: a8_cell(c, g, reps), force))
        if need5:
            parts["A5_seed0"].append(cached(c["id"], "A5_seed0", key, lambda: seed0_cell(c, g), force))
        del g
    if "A5" in which:
        for cid, roles in PERLEVEL.items():
            if cid not in {c["id"] for c in cells}:
                continue
            if any(C.run_state(d) != "complete" for v in roles.values() for d in v):
                continue
            key = fp(sum(roles.values(), []))

            def f(roles=roles, cid=cid):
                log(f"load per-level {cid}")
                g, _ = load_v3(roles)
                return pd.DataFrame([{"cell": cid, "variant": "per-level tuning (pre-shared-params runs)",
                                      "estimand": e, **est_dict(infer_estimand(g, e))}
                                     for e in ("G_excess", "G_emb")])
            parts["A5_perlevel"].append(cached(cid, "A5_perlevel", key, f, force))
    return parts


# ============================================================== A5 planned vs reported
def run_a5(cells, parts):
    T1 = t1()
    rows = []
    sel_v1 = {}
    for c in cells:
        j = json.loads((Path(c["selection"]["dir"]) / "selection.json").read_text())
        sel_v1[c["id"]] = (j.get("c_star"), j.get("c_star_v1"))
    panel = pd.read_csv(OUT / "RE_control_panel.csv")
    cc = {"brazil": "BR", "colombia": "CO", "peru": "PE", "taiwan": "TW"}
    panel["cell"] = panel.country.map(cc) + "_" + panel.split

    def add(cid, variant, pct, lo, hi, p, note=""):
        rows.append({"cell": cid, "variant": variant, "G_excess_pct": pct, "lo95_pct": lo, "hi95_pct": hi,
                     "p": p, "note": note})
    for c in cells:
        cid = c["id"]
        x = T1.loc[cid]
        add(cid, "reported primary (v3: excl v2, origin-year filter, h{1,4}, rule-v2 C*)",
            x.pct_of_WIS_ref, x.lo95_pct, x.hi95_pct, x.DM_p, f"C*={x.C_star}")
        if isinstance(x.sec_horizons, str) and x.sec_horizons:
            add(cid, "planned horizons h1-h4 pooled", x.sec_pct, x.sec_lo95_pct, x.sec_hi95_pct, x.sec_DM_p,
                f"years {x.sec_years}")
        add(cid, "all rows (no origin-year filter)", x.unfiltered_pct, x.unfiltered_lo95_pct,
            x.unfiltered_hi95_pct, x.unfiltered_p)
        if np.isfinite(x.exclv1_pct):
            add(cid, "exclusions v1 (no Espirito Santo unit-week exclusion)", x.exclv1_pct, x.exclv1_lo95_pct,
                x.exclv1_hi95_pct, x.exclv1_p)
        else:
            add(cid, "exclusions v1", x.pct_of_WIS_ref, x.lo95_pct, x.hi95_pct, x.DM_p,
                "identical to primary (no unit-week exclusion applies)")
        add(cid, "EWC B=4 variance (robustness)", x.pct_of_WIS_ref, x.B4_lo95_pct, x.B4_hi95_pct, x.B4_p)
        v2, v1 = sel_v1[cid]
        if v1 and v1 != v2:
            pr = panel[(panel.cell == cid) & (panel.control == v1) & (panel.status == "available")]
            if len(pr):
                r = pr.iloc[0]
                add(cid, f"rule-v1 C* ({v1})", r.G_excess_pct, r.G_excess_pct_lo95, r.G_excess_pct_hi95,
                    r.G_excess_p, "fixed-control panel run (RE); Taiwan panel excludes 2021" if c["country"] == "taiwan"
                    else "fixed-control panel run (RE)")
            else:
                add(cid, f"rule-v1 C* ({v1})", np.nan, np.nan, np.nan, np.nan,
                    "no valid run (pre-fix C4 runs were invalidated)" if v1.startswith("C4") else "no run")
        elif v1:
            add(cid, f"rule-v1 C* ({v1})", x.pct_of_WIS_ref, x.lo95_pct, x.hi95_pct, x.DM_p, "same control as rule v2")
        else:
            add(cid, "rule-v1 C*", np.nan, np.nan, np.nan, np.nan, "rule-v1 choice not recorded")
        if cid in ("TW_S1", "TW_S5"):
            e = kit_est(f"{cid}_no2021")
            if e is not None:
                r = e[(e.horizon == "pooled") & (e.test_year == "pooled") & (e.stratum == "all")
                      & (e.estimand == "G_excess")].iloc[0]
                add(cid, "Taiwan 2021 not included (planned test years)", r.pct_of_ref,
                    100 * r.lo95 / r.wis_ref, 100 * r.hi95 / r.wis_ref, r.p)
        if cid == "BR_S1":
            e = kit_est("BR_S1_perlevel")
            if e is not None:
                r = e[(e.horizon == "pooled") & (e.test_year == "pooled") & (e.stratum == "all")
                      & (e.estimand == "G_excess")].iloc[0]
                add(cid, "per-level tuning (31 leaves; superseded)", r.pct_of_ref, 100 * r.lo95 / r.wis_ref,
                    100 * r.hi95 / r.wis_ref, r.p, "kit cache BR_S1_perlevel")
    for df in parts.get("A5_seed0", []) + parts.get("A5_perlevel", []):
        for _, r in df[df.estimand == "G_excess"].iterrows():
            add(r.cell, r.variant, r.pct_of_ref, r.lo95_pct, r.hi95_pct, r.p)
    out = pd.DataFrame(rows).sort_values(["cell"], kind="stable")
    out.to_csv(OUT / "R3_A5_planned_vs_reported.csv", index=False)
    return out


# ============================================================== A7 embedding stability
def run_a7():
    from pop.features.controls import load_unit_points, _xyz
    from pop.features.levels import renormalize
    from scipy.spatial import cKDTree
    pts = load_unit_points()
    pts["unit_id"] = pts.unit_id.astype(str)
    rows = []
    rng = np.random.default_rng(20261119)
    for country in ("brazil", "colombia", "peru", "taiwan"):
        files = sorted(Path(f"data/interim/alphaearth/{country}").glob(f"alphaearth_{country}_20??.parquet"))
        E = {}
        for f in files:
            d = pd.read_parquet(f)
            y = int(f.stem.rsplit("_", 1)[1])
            V = renormalize(d[[c for c in d.columns if c.startswith("w_A")]].to_numpy(float))
            E[y] = pd.DataFrame(V, index=d.unit_id.astype(str))
        years = sorted(E)
        units = sorted(set.intersection(*[set(E[y].index[np.isfinite(E[y].to_numpy()).all(1)]) for y in years]))
        P = pts.set_index("unit_id").reindex(units)
        okp = P.lat.notna().to_numpy()
        units = list(np.array(units)[okp])
        P = P.loc[units]
        M = {y: E[y].loc[units].to_numpy() for y in years}
        xyz = _xyz(P.lat.to_numpy(), P.lon.to_numpy())
        _, nn = cKDTree(xyz).query(xyz, k=6)
        nn = nn[:, 1:]
        n = len(units)

        def summ(v, metric, ypair):
            v = np.asarray(v, float)
            rows.append({"country": country, "metric": metric, "years": ypair, "n": int(v.size),
                         "mean": float(v.mean()), "p05": float(np.quantile(v, .05)),
                         "p25": float(np.quantile(v, .25)), "median": float(np.median(v)),
                         "p75": float(np.quantile(v, .75)), "min": float(v.min())})
        allw, allnn, allr, ret, ret_nn = [], [], [], [], []
        for y0, y1 in zip(years[:-1], years[1:]):
            A, B = M[y0], M[y1]
            w = (A * B).sum(1)
            allw.append(w)
            summ(w, "within-district, consecutive years", f"{y0}-{y1}")
            S = B @ A.T                      # cos(unit i at y1, unit j at y0)
            best = S.argmax(1)
            ret.append(best == np.arange(n))
            nnc = np.take_along_axis(S, nn, 1).max(1)      # max cos to the 5 spatial neighbours (y0)
            ret_nn.append(w > nnc)
        for y in years:
            A = M[y]
            allnn.append((A[:, None, :] * A[nn]).sum(-1).ravel())
            i, j = rng.integers(0, n, 20000), rng.integers(0, n, 20000)
            k = i != j
            allr.append((A[i[k]] * A[j[k]]).sum(1))
        summ(np.concatenate(allw), "within-district, consecutive years", "all pairs")
        w_first_last = (M[years[0]] * M[years[-1]]).sum(1)
        summ(w_first_last, "within-district, first vs last year", f"{years[0]}-{years[-1]}")
        summ(np.concatenate(allnn), "between-district, 5 nearest spatial neighbours (same year)", "all years")
        summ(np.concatenate(allr), "between-district, random pairs (same year)", "all years")
        r = np.concatenate(ret)
        rows.append({"country": country, "metric": "self-retrieval: unit's y+1 vector is closest to its own y vector "
                     "among all units", "years": "all consecutive pairs", "n": int(r.size), "mean": float(r.mean())})
        r2 = np.concatenate(ret_nn)
        rows.append({"country": country, "metric": "within-unit cos(y,y+1) > max cos to its 5 spatial neighbours",
                     "years": "all consecutive pairs", "n": int(r2.size), "mean": float(r2.mean())})
        rows.append({"country": country, "metric": "units used", "years": f"{years[0]}-{years[-1]}", "n": n,
                     "mean": np.nan})
    df = pd.DataFrame(rows)
    df["note"] = "pop-weighted (w_) district means, renormalised to unit length as in L4; cosine = dot product"
    df.to_csv(OUT / "R3_A7_embedding_stability.csv", index=False)
    return df


# ============================================================== main
def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default=",".join(ALL))
    ap.add_argument("--exclude", default=",".join(BLINDED))
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--reps", type=int, default=2000, help="IAAFT replications (A8)")
    a = ap.parse_args(argv)
    os.chdir(ROOT)
    which = [w.strip() for w in a.only.split(",") if w.strip()]
    excl = [w.strip() for w in a.exclude.split(",") if w.strip()]
    cells, skipped = registry(excl)
    log(f"cells: {[c['id'] for c in cells]}; skipped: {skipped}")
    meta = {"cells": [c["id"] for c in cells], "skipped": skipped, "which": which,
            "generated": time.strftime("%Y-%m-%d %H:%M:%S %Z")}
    if "A1" in which:
        run_a1(cells, a.force)
    if "A2" in which:
        run_a2(cells)
    parts = run_loaded(cells, which, a.force, a.reps)
    if parts["check"]:
        pd.DataFrame(parts["check"]).to_csv(CACHE / "load_check.csv", index=False)
        meta["load_check"] = parts["check"]
    if "A3" in which:
        run_a3(cells, parts["A3_dm"])
    if "A4" in which:
        run_a4(cells)
    if "A5" in which:
        run_a5(cells, parts)
    if "A6" in which and parts["A6"]:
        pd.concat(parts["A6"], ignore_index=True).to_csv(OUT / "R3_A6_outcome_agnostic.csv", index=False)
    if "A7" in which:
        run_a7()
    if "A8" in which and parts["A8"]:
        pd.concat(parts["A8"], ignore_index=True).to_csv(OUT / "R3_A8_iaaft_equivalence.csv", index=False)
    CACHE.mkdir(parents=True, exist_ok=True)
    (CACHE / "last_run.json").write_text(json.dumps(meta, indent=1, default=str))
    log("done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
