"""Scoring-exclusion filters applied to test rows before any estimand (data audit, 2026-11-16).

Files (data/processed/exclusions_v1/):
- incomplete_weeks.csv: country, week_start, scope ("country" | "adm1"), adm1. A row is dropped
  when its target week equals week_start in its country and, for scope "adm1", its adm1 matches.
  An optional ``action`` column (e.g. "exclude" | "sensitivity") can be filtered with ``actions``.
- no_geometry_units.csv: unit_id. Rows of these units are dropped.
- late_entry_units.csv: unit_id plus a first-case-year column (the first column whose name
  contains both "first" and "year"). Sensitivity: drop rows whose unit's first case year is
  after the origin year, i.e. the rolling-origin test year (``test_year``; the year of
  ``origin_week`` when there is no test_year column).
Every function returns (kept frame, number of rows removed).
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def _norm(s: pd.Series) -> pd.Series:
    return s.astype(str).str.strip().str.upper()


def exclude_units(df: pd.DataFrame, units_csv, *, unit_col: str = "unit_id"):
    u = pd.read_csv(units_csv, dtype=str)
    if "unit_id" not in u.columns:
        raise ValueError(f"{units_csv}: needs a unit_id column")
    drop = df[unit_col].astype(str).isin(set(u.unit_id.astype(str).str.strip()))
    return df[~drop], int(drop.sum())


def exclude_weeks(df: pd.DataFrame, weeks_csv, *, country: str, time_col: str = "target_week",
                  adm1_col: str = "state", actions=None):
    w = pd.read_csv(weeks_csv, dtype=str)
    miss = {"country", "week_start", "scope"} - set(w.columns)
    if miss:
        raise ValueError(f"{weeks_csv}: missing columns {sorted(miss)}")
    w = w[_norm(w.country) == str(country).strip().upper()].copy()
    if actions is not None:
        if "action" not in w.columns:
            raise ValueError(f"{weeks_csv}: no action column to filter on")
        w = w[w.action.str.strip().str.lower().isin({a.lower() for a in actions})]
    if w.empty:
        return df, 0
    w["week_start"] = pd.to_datetime(w.week_start)
    scope = w.scope.str.strip().str.lower()
    bad = set(scope) - {"country", "adm1"}
    if bad:
        raise ValueError(f"{weeks_csv}: unknown scope {sorted(bad)}")
    tw = pd.to_datetime(df[time_col])
    drop = tw.isin(set(w.loc[scope == "country", "week_start"]))
    wa = w[scope == "adm1"]
    if len(wa):
        if "adm1" not in wa.columns:
            raise ValueError(f"{weeks_csv}: scope adm1 rows need an adm1 column")
        pairs = pd.MultiIndex.from_arrays([wa.week_start, _norm(wa.adm1)])
        drop |= pd.MultiIndex.from_arrays([tw, _norm(df[adm1_col])]).isin(pairs)
    drop = np.asarray(drop, bool)
    return df[~drop], int(drop.sum())


def first_year_col(cols) -> str:
    c = [x for x in cols if "first" in x.lower() and "year" in x.lower()]
    if not c:
        raise ValueError("late-entry file needs a column naming the first case year")
    return c[0]


def exclude_late_entry(df: pd.DataFrame, late_csv, *, unit_col: str = "unit_id",
                       year_col: str = "test_year", origin_col: str = "origin_week"):
    u = pd.read_csv(late_csv, dtype={"unit_id": str})
    fy = u.set_index(u.unit_id.astype(str).str.strip())[first_year_col(u.columns)].astype(float)
    first = df[unit_col].astype(str).map(fy)
    yr = (df[year_col].astype(int) if year_col in df.columns
          else pd.to_datetime(df[origin_col]).dt.year)
    drop = (first > yr).to_numpy()
    return df[~drop], int(drop.sum())
