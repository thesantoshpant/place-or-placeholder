"""Zero-filled weekly Admin2 panel (frozen rule, panel_weekly_v1).

Rule:
  1. unit universe per country = every Admin2 unit ever in its weekly file;
  2. coverage = first..last week with any weekly Admin2 row (Brazil from epi
     week 2014-01, i.e. week starting 2013-12-29); every unit gets every week,
     a missing row = 0 cases (``observed=False, zero_filled=True``);
  3. validation vs the OpenDengue national weekly series; country-weeks whose
     Admin2 sum is far below national are ``flag_gap=True``.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from pop.data.opendengue import ibge7

COUNTRY_START = {"BRAZIL": pd.Timestamp("2013-12-29")}  # epi week 2014-01
# flag_gap: national >= GAP_MIN_NATIONAL and the week's admin2/national ratio is
# < GAP_RATIO x that country-year's ratio of sums (relative, because Brazil's
# Admin2 "Probable" series is systematically ~0.5-0.6 of the national "Total"
# series from 2016 on; an absolute threshold would flag a definitional offset).
GAP_RATIO = 0.25
GAP_MIN_NATIONAL = 20
PANEL_COLS = ["unit_id", "country", "adm1", "adm2", "week_start", "year", "cases",
              "observed", "zero_filled", "flag_gap", "case_definition"]


def epi_year(week_start: pd.Series) -> pd.Series:
    """Epidemiological year = calendar year of the week's Wednesday."""
    return (pd.to_datetime(week_start) + pd.Timedelta(days=3)).dt.year


def make_unit_id(df: pd.DataFrame) -> pd.Series:
    """Brazil: 7-digit IBGE string; others: 'ADM0|ADM1|ADM2' (upper-case)."""
    up = lambda c: df[c].fillna("").astype(str).str.upper()
    uid = up("adm_0_name") + "|" + up("adm_1_name") + "|" + up("adm_2_name")
    bra = df["adm_0_name"] == "BRAZIL"
    if bra.any():
        uid = uid.where(~bra, df.loc[bra, "IBGE_code"].map(ibge7))
    return uid


def admin2_rows(raw: pd.DataFrame) -> pd.DataFrame:
    """Weekly Admin2 rows -> tidy observed frame."""
    a = raw[(raw["T_res"] == "Week") & (raw["S_res"] == "Admin2")].copy()
    a["unit_id"] = make_unit_id(a)
    out = pd.DataFrame({
        "unit_id": a["unit_id"], "country": a["adm_0_name"].astype(str),
        "adm1": a["adm_1_name"].astype(str), "adm2": a["adm_2_name"].astype(str),
        "week_start": pd.to_datetime(a["calendar_start_date"]),
        "cases": a["dengue_total"].astype(float),
        "case_definition": a["case_definition_standardised"].astype(str),
    })
    for c, start in COUNTRY_START.items():
        out = out[~((out["country"] == c) & (out["week_start"] < start))]
    if out.duplicated(["unit_id", "week_start"]).any():
        raise ValueError("duplicate (unit_id, week_start) rows")
    return out.reset_index(drop=True)


def zero_fill(obs: pd.DataFrame) -> pd.DataFrame:
    """Complete unit x week grid per country over its coverage period."""
    parts = []
    for country, g in obs.groupby("country", sort=True):
        weeks = pd.date_range(g["week_start"].min(), g["week_start"].max(), freq="7D")
        units = (g.sort_values("week_start")
                 .drop_duplicates("unit_id", keep="last")[["unit_id", "adm1", "adm2"]]
                 .sort_values("unit_id"))
        grid = pd.MultiIndex.from_product([units["unit_id"], weeks],
                                          names=["unit_id", "week_start"]).to_frame(index=False)
        grid = grid.merge(units, on="unit_id", how="left")
        grid = grid.merge(g[["unit_id", "week_start", "cases", "case_definition"]],
                          on=["unit_id", "week_start"], how="left", indicator=True)
        grid["observed"] = grid.pop("_merge").eq("both")
        if len(grid) != len(units) * len(weeks) or grid["observed"].sum() != len(g):
            raise AssertionError(f"{country}: grid/observed mismatch")
        grid["zero_filled"] = ~grid["observed"]
        grid["cases"] = grid["cases"].fillna(0.0).astype(float)
        cd = g["case_definition"].mode().iat[0]
        grid["case_definition"] = grid["case_definition"].fillna(cd)
        grid["country"] = country
        parts.append(grid)
    p = pd.concat(parts, ignore_index=True)
    p["year"] = epi_year(p["week_start"]).astype("int16")
    p["flag_gap"] = False
    return p


def national_weekly(raw: pd.DataFrame) -> pd.DataFrame:
    n = raw[(raw["T_res"] == "Week") & (raw["S_res"] == "Admin0")]
    return (n.groupby(["adm_0_name", "calendar_start_date"])["dengue_total"].sum()
            .rename("national").reset_index()
            .rename(columns={"adm_0_name": "country", "calendar_start_date": "week_start"}))


def national_check(panel: pd.DataFrame, nat: pd.DataFrame,
                   gap_ratio: float = GAP_RATIO, min_nat: float = GAP_MIN_NATIONAL):
    """Return (weekly comparison, per country-year table); weekly has flag_gap."""
    a2 = panel.groupby(["country", "week_start"])["cases"].sum().rename("admin2").reset_index()
    w = a2.merge(nat, on=["country", "week_start"], how="left")
    w["ratio"] = w["admin2"] / w["national"]
    w["within10"] = (w["ratio"] - 1).abs() <= 0.10
    w["year"] = epi_year(w["week_start"])
    has = w["national"].notna()
    cy = w[has].groupby(["country", "year"])[["admin2", "national"]].sum()
    cy_ratio = (cy["admin2"] / cy["national"].replace(0, np.nan)).rename("year_ratio")
    w = w.merge(cy_ratio.reset_index(), on=["country", "year"], how="left")
    w["rel_ratio"] = w["ratio"] / w["year_ratio"]
    w["flag_gap"] = (w["national"] >= min_nat) & (w["rel_ratio"] < gap_ratio)
    yr = w.groupby(["country", "year"]).agg(
        n_weeks=("admin2", "size"),
        n_weeks_national=("national", "count"),
        admin2_sum=("admin2", "sum"),
        national_sum=("national", lambda s: s.sum(min_count=1)),
        n_weeks_flagged=("flag_gap", "sum")).reset_index()
    a2_on_nat = w[has].groupby(["country", "year"])["admin2"].sum().rename("admin2_sum_matched")
    within = w[has & (w["national"] > 0)].groupby(["country", "year"])["within10"].mean() \
        .rename("share_weeks_within10")
    yr = yr.merge(a2_on_nat.reset_index(), on=["country", "year"], how="left") \
           .merge(within.reset_index(), on=["country", "year"], how="left")
    yr["ratio"] = yr["admin2_sum_matched"] / yr["national_sum"].replace(0, np.nan)
    yr = yr[["country", "year", "n_weeks", "n_weeks_national", "admin2_sum", "national_sum",
             "ratio", "share_weeks_within10", "n_weeks_flagged"]]
    return w, yr


def build_panel(raw: pd.DataFrame):
    """raw Temporal rows (weekly, panel countries) -> (panel, universe, weekly, yearly)."""
    obs = admin2_rows(raw)
    panel = zero_fill(obs)
    w, yr = national_check(panel, national_weekly(raw))
    gap = w.loc[w["flag_gap"], ["country", "week_start"]].assign(_g=True)
    panel = panel.drop(columns="flag_gap").merge(gap, on=["country", "week_start"], how="left")
    panel["flag_gap"] = panel.pop("_g").fillna(False).astype(bool)
    panel = panel[PANEL_COLS].sort_values(["country", "unit_id", "week_start"]) \
        .reset_index(drop=True)
    universe = unit_universe(panel)
    return panel, universe, w, yr


def unit_universe(panel: pd.DataFrame) -> pd.DataFrame:
    o = panel[panel["observed"]]
    u = o.groupby("unit_id").agg(country=("country", "first"), adm1=("adm1", "first"),
                                 adm2=("adm2", "first"), first_week=("week_start", "min"),
                                 last_week=("week_start", "max"),
                                 n_observed_weeks=("week_start", "size")).reset_index()
    tot = panel.groupby("unit_id")["cases"].sum().rename("total_cases")
    u = u.merge(tot.reset_index(), on="unit_id")
    return u[["unit_id", "country", "adm1", "adm2", "first_week", "last_week",
              "n_observed_weeks", "total_cases"]].sort_values(["country", "unit_id"])
