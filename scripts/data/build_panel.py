#!/usr/bin/env python
"""Build the zero-filled weekly Admin2 panel (panel_weekly_v1) from OpenDengue V1.3.1.

Usage (from the project root, after `source env.sh`):
  python scripts/data/build_panel.py
Outputs:
  data/processed/panel_weekly_v1.parquet, data/processed/unit_universe_v1.csv,
  outputs/data_audit/panel_national_check.csv, outputs/data_audit/panel_national_weekly.csv,
  outputs/data_audit/panel_summary.csv
"""
import argparse
from pathlib import Path

from pop.data.opendengue import TEMPORAL_CSV, load_temporal
from pop.data.panel import build_panel

ap = argparse.ArgumentParser()
ap.add_argument("--src", default=str(TEMPORAL_CSV))
ap.add_argument("--processed", default="data/processed")
ap.add_argument("--audit", default="outputs/data_audit")
a = ap.parse_args()
proc, aud = Path(a.processed), Path(a.audit)
proc.mkdir(parents=True, exist_ok=True)
aud.mkdir(parents=True, exist_ok=True)

raw = load_temporal(a.src, s_res=["Admin0", "Admin2"])
panel, universe, weekly, yearly = build_panel(raw)

out = panel.copy()
out["week_start"] = out["week_start"].dt.date
for c in ["unit_id", "country", "adm1", "adm2", "case_definition"]:
    out[c] = out[c].astype("string")
out.to_parquet(proc / "panel_weekly_v1.parquet", index=False)
u = universe.copy()
u["first_week"] = u["first_week"].dt.date
u["last_week"] = u["last_week"].dt.date
u.to_csv(proc / "unit_universe_v1.csv", index=False)
yearly.to_csv(aud / "panel_national_check.csv", index=False, float_format="%.4f")
weekly.to_csv(aud / "panel_national_weekly.csv", index=False, float_format="%.4f")

summ = panel.groupby("country").agg(
    n_units=("unit_id", "nunique"), n_weeks=("week_start", "nunique"),
    first_week=("week_start", "min"), last_week=("week_start", "max"),
    n_rows=("cases", "size"), pct_zero_filled=("zero_filled", "mean"),
    n_weeks_flagged=("flag_gap", lambda s: panel.loc[s.index[s], "week_start"].nunique()),
    total_cases=("cases", "sum")).reset_index()
summ["pct_zero_filled"] = (100 * summ["pct_zero_filled"]).round(2)
summ.to_csv(aud / "panel_summary.csv", index=False)
print(summ.to_string(index=False))
print(yearly.to_string(index=False))
