#!/usr/bin/env python
"""Audit weekly sub-national coverage in OpenDengue V1.3.1 for Paper 1.

Paper 1 ("Place or Placeholder?") forecasts weekly district-level dengue cases
1-4 weeks ahead in Brazil, Colombia, Peru and Taiwan (fallbacks: Mexico,
Thailand). This script measures, for both the Spatial and Temporal extracts:

  1. S_res x T_res crosstab (rows, unique units, min/max year)
  2. best weekly sub-national level: units overall/per year, completeness vs a
     full unit x week grid, duplicates, week convention, gaps/drop-outs
  3. identifier quality (FAO_GAUL_code, IBGE_code, RNE_iso_code, names)
  4. Taiwan unit samples
  5. plan vs measured table
  6. Spatial vs Temporal overlap of weekly sub-national unit-weeks

Read-only on the raw data. Outputs are CSVs in --out.

Usage:
  python scripts/data/audit_opendengue.py \
      --spatial data/raw/opendengue/V1.3.1/extracted/Spatial_extract_V1_3_1/Spatial_extract_V1_3_1.csv \
      --temporal data/raw/opendengue/V1.3.1/extracted/Temporal_extract_V1_3_1/Temporal_extract_V1_3_1.csv \
      --out outputs/data_audit
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

COUNTRIES = {"BRA": "Brazil", "COL": "Colombia", "PER": "Peru", "TWN": "Taiwan",
             "MEX": "Mexico", "THA": "Thailand"}
PLAN = {"BRA": (5517, 2013, 2024), "COL": (1071, 2013, 2022),
        "PER": (115, 2013, 2023), "TWN": (287, 2013, 2024)}
CODE_COLS = ["FAO_GAUL_code", "RNE_iso_code", "IBGE_code"]


def load(path):
    df = pd.read_csv(path, dtype=str, keep_default_na=True, na_values=["NA"])
    df = df[df["ISO_A0"].isin(COUNTRIES)].copy()
    df["Year"] = df["Year"].astype(int)
    df["start"] = pd.to_datetime(df["calendar_start_date"])
    df["end"] = pd.to_datetime(df["calendar_end_date"])
    df["unit"] = np.where(df["S_res"] == "Admin2",
                          df["adm_1_name"].fillna("") + "|" + df["adm_2_name"].fillna(""),
                          np.where(df["S_res"] == "Admin1", df["adm_1_name"].fillna(""), df["adm_0_name"]))
    return df


def best_level(d):
    w = d[d["T_res"] == "Week"]
    for lvl in ("Admin2", "Admin1"):
        if (w["S_res"] == lvl).any():
            return lvl, w[w["S_res"] == lvl]
    return None, w.iloc[0:0]


def audit(df, ext):
    xt, summ, peryear, ids, dups_out = [], [], [], [], []
    xt = (df.groupby(["ISO_A0", "S_res", "T_res"])
          .agg(rows=("UUID", "size"), units=("unit", "nunique"),
               year_min=("Year", "min"), year_max=("Year", "max")).reset_index())
    xt.insert(0, "extract", ext)
    # years per S/T combination (for gap detection)
    yrs = (df.groupby(["ISO_A0", "Year", "S_res", "T_res"]).size()
           .rename("rows").reset_index())
    yrs.insert(0, "extract", ext)
    weekly = {}
    for iso in COUNTRIES:
        d = df[df["ISO_A0"] == iso]
        lvl, w = best_level(d)
        if lvl is None:
            summ.append(dict(extract=ext, iso=iso, level=None)); continue
        weekly[iso] = w
        units = w["unit"].nunique()
        weeks = w["start"].nunique()
        uw = w.drop_duplicates(["unit", "start"])
        dup = w.duplicated(["unit", "start"], keep=False)
        span = (w["end"] - w["start"]).dt.days + 1
        wd = w["start"].dt.day_name().value_counts(normalize=True)
        # per-year
        py = w.groupby("Year").agg(units=("unit", "nunique"), weeks=("start", "nunique"),
                                   unit_weeks=("start", "size"), cases=("dengue_total",
                                   lambda s: pd.to_numeric(s, errors="coerce").sum()))
        uw_py = uw.groupby("Year").size()
        py["unit_weeks_unique"] = uw_py
        py["completeness_vs_all_units_pct"] = 100 * uw_py / (units * py["weeks"])
        py["completeness_vs_year_units_pct"] = 100 * uw_py / (py["units"] * py["weeks"])
        # drop-outs relative to previous year
        sets = w.groupby("Year")["unit"].apply(set)
        prev = None; drop, new = [], []
        for y, s in sets.items():
            drop.append(len(prev - s) if prev is not None else 0)
            new.append(len(s - prev) if prev is not None else len(s))
            prev = s
        py["units_dropped_vs_prev"] = drop; py["units_new_vs_prev"] = new
        # zero vs missing: units with zero weeks reported in-year among all units
        py = py.reset_index(); py.insert(0, "iso", iso); py.insert(0, "extract", ext)
        py.insert(2, "level", lvl)
        peryear.append(py)
        # years with only coarser data
        all_years = set(d["Year"]); wk_years = set(w["Year"])
        other = sorted(all_years - wk_years)
        # identifiers per unit (unique combos)
        u = w.drop_duplicates(["unit"] + CODE_COLS + ["full_name"])
        rec = dict(extract=ext, iso=iso, level=lvl, units=units, units_by_full_name=w["full_name"].nunique(),
                   adm2_name_alone_unique=w["adm_2_name"].nunique() if lvl == "Admin2" else np.nan)
        for c in CODE_COLS:
            nn = w[c].notna().mean()
            pairs = w[["unit", c]].dropna().drop_duplicates()
            rec[f"{c}_nonnull_pct"] = round(100 * nn, 2)
            rec[f"{c}_nunique"] = pairs[c].nunique()
            rec[f"{c}_codes_with_multi_names"] = int((pairs.groupby(c)["unit"].nunique() > 1).sum())
            rec[f"units_with_multi_{c}"] = int((pairs.groupby("unit")[c].nunique() > 1).sum())
        ids.append(rec)
        if dup.any():
            dd = w[dup].sort_values(["unit", "start"]).head(200)
            dd.insert(0, "extract", ext); dups_out.append(dd)
        summ.append(dict(
            extract=ext, iso=iso, country=COUNTRIES[iso], level=lvl, units=units,
            year_min=w["Year"].min(), year_max=w["Year"].max(), n_years=w["Year"].nunique(),
            distinct_weeks=weeks, rows=len(w), unit_weeks_unique=len(uw),
            completeness_full_grid_pct=round(100 * len(uw) / (units * weeks), 2),
            dup_unitweek_rows=int(dup.sum()), dup_unitweek_keys=int(w[dup].drop_duplicates(["unit", "start"]).shape[0]),
            pct_7day_span=round(100 * (span == 7).mean(), 2),
            span_values=";".join(f"{k}:{v}" for k, v in span.value_counts().head(5).items()),
            start_weekday=";".join(f"{k}:{v:.3f}" for k, v in wd.head(3).items()),
            years_without_weekly_at_level=";".join(map(str, other)),
            missing_years_in_range=";".join(map(str, sorted(set(range(w["Year"].min(), w["Year"].max() + 1)) - wk_years))),
            case_def=";".join(w["case_definition_standardised"].fillna("NA").unique()),
        ))
    return (xt, yrs, pd.DataFrame(summ), pd.concat(peryear), pd.DataFrame(ids),
            pd.concat(dups_out) if dups_out else pd.DataFrame(), weekly)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--spatial", required=True)
    ap.add_argument("--temporal", required=True)
    ap.add_argument("--out", default="outputs/data_audit")
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    res, weekly = {}, {}
    for ext, p in (("Spatial", a.spatial), ("Temporal", a.temporal)):
        df = load(p)
        *r, weekly[ext] = audit(df, ext)
        res[ext] = r
    names = ["crosstab_sres_tres", "years_by_sres_tres", "weekly_summary", "weekly_per_year",
             "identifiers", "duplicate_examples"]
    for i, n in enumerate(names):
        pd.concat([res[e][i] for e in res]).to_csv(out / f"{n}.csv", index=False)
    # Taiwan unit samples
    tw = weekly["Spatial"].get("TWN")
    if tw is not None:
        (tw.groupby(["adm_1_name", "adm_2_name"], dropna=False)
         .agg(rows=("UUID", "size"), year_min=("Year", "min"), year_max=("Year", "max"),
              gaul=("FAO_GAUL_code", "first"), full_name=("full_name", "first"))
         .reset_index().to_csv(out / "taiwan_units.csv", index=False))
    # Spatial vs Temporal overlap
    ov = []
    for iso in COUNTRIES:
        s, t = weekly["Spatial"].get(iso), weekly["Temporal"].get(iso)
        if s is None or t is None:
            continue
        ks = set(zip(s["S_res"], s["unit"], s["start"])); kt = set(zip(t["S_res"], t["unit"], t["start"]))
        m = s.merge(t, on=["S_res", "unit", "start"], suffixes=("_s", "_t"))
        ov.append(dict(iso=iso, spatial_keys=len(ks), temporal_keys=len(kt), both=len(ks & kt),
                       only_spatial=len(ks - kt), only_temporal=len(kt - ks),
                       value_mismatch_in_both=int((m["dengue_total_s"] != m["dengue_total_t"]).sum()),
                       spatial_units=s["unit"].nunique(), temporal_units=t["unit"].nunique()))
    pd.DataFrame(ov).to_csv(out / "spatial_vs_temporal.csv", index=False)
    # plan vs measured
    sm = pd.concat([res[e][2] for e in res])
    rows = []
    for iso, (pu, py0, py1) in PLAN.items():
        for ext in res:
            r = sm[(sm.extract == ext) & (sm.iso == iso)].iloc[0]
            rows.append(dict(iso=iso, extract=ext, plan_units=pu, measured_units=r["units"],
                             measured_level=r["level"], plan_years=f"{py0}-{py1}",
                             measured_years=f"{r['year_min']}-{r['year_max']}",
                             missing_years=r["missing_years_in_range"],
                             completeness_pct=r["completeness_full_grid_pct"],
                             units_match=pu == r["units"],
                             years_match=(py0 >= r["year_min"]) and (py1 <= r["year_max"])))
    pv = pd.DataFrame(rows); pv.to_csv(out / "plan_vs_measured.csv", index=False)
    with pd.option_context("display.width", 250, "display.max_columns", 40, "display.max_rows", 400):
        for n in ("crosstab_sres_tres", "weekly_summary", "identifiers", "spatial_vs_temporal", "plan_vs_measured"):
            print(f"\n== {n}\n", pd.read_csv(out / f"{n}.csv").to_string(index=False))


if __name__ == "__main__":
    main()
