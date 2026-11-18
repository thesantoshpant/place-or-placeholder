#!/usr/bin/env python
r"""Build data/processed/exclusions_v2/ (primary scoring exclusions from 2026-11-18; v1 is kept).

v2 = v1 (no-geometry units, incomplete weeks, late-entry list; copied unchanged)
   + unit_week_exclusions.csv: unit-weeks whose zero targets are false zeros because the source
     stopped reporting a whole state/department. Applied at scoring to every model (results kit),
     never to training (models are not refitted).

Current entries (deviation row 34):
  Espirito Santo (Brazil, IBGE codes ^32\d{5}$, all 78 municipalities): OpenDengue V1.3.1 has false
  zeros there (docs/data/zero_fill_crosscheck_2024.md; independent verification
  docs/data/zero_fill_2024_verification.md: the defect starts earlier than first thought).
  Excluded: target weeks >= 2019-12-29, i.e. every ES row of every Brazil test year 2020-2024.
  The verifier's scan found no other structural defect in any Admin1 unit of the four countries.

Usage: python scripts/analysis/build_exclusions_v2.py [--panel data/processed/panel_weekly_v1.parquet]
"""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

import pandas as pd

V1 = Path("data/processed/exclusions_v1")
V2 = Path("data/processed/exclusions_v2")
RULES = [  # (country, unit_id regex, from_week, to_week or None, reason)
    ("BRAZIL", r"^32\d{5}$", "2019-12-29", None,
     "Espirito Santo (IBGE 32xxxxx): false zeros in the source in every test year 2020-2024; "
     "InfoDengue shows cases (docs/data/zero_fill_crosscheck_2024.md, "
     "docs/data/zero_fill_2024_verification.md)"),
]


def build(panel: str) -> pd.DataFrame:
    p = pd.read_parquet(panel, columns=["unit_id", "country"]).drop_duplicates()
    p["unit_id"] = p.unit_id.astype(str)
    rows = []
    for country, prefix, w0, w1, why in RULES:
        u = p[(p.country.astype(str).str.upper() == country) & p.unit_id.str.fullmatch(prefix.strip("^$"))]
        rows += [{"unit_id": x, "country": country, "from_week": w0, "to_week": w1 or "",
                  "rule": f"{country}:{prefix}", "reason": why, "action": "exclude"}
                 for x in sorted(u.unit_id)]
    return pd.DataFrame(rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--panel", default="data/processed/panel_weekly_v1.parquet")
    a = ap.parse_args()
    V2.mkdir(parents=True, exist_ok=True)
    for f in ("no_geometry_units.csv", "incomplete_weeks.csv", "late_entry_units.csv"):
        shutil.copy2(V1 / f, V2 / f)
    t = build(a.panel)
    t.to_csv(V2 / "unit_week_exclusions.csv", index=False)
    (V2 / "README.md").write_text(
        "# Scoring exclusions v2 (2026-11-18)\n\nBuilt by `scripts/analysis/build_exclusions_v2.py`. "
        "Same as `exclusions_v1/` (files copied unchanged) plus `unit_week_exclusions.csv`: "
        "unit-weeks dropped at scoring for all models (target_week >= from_week and, if set, "
        "<= to_week). Rules:\n\n" + "\n".join(f"- {c} units matching {p}: target weeks >= {w0}: {why}"
                                             for c, p, w0, _, why in RULES) + "\n")
    print(t.groupby("rule").size().to_string())


if __name__ == "__main__":
    main()
