#!/usr/bin/env python
"""Weekly completeness check of the zero-filled Admin2 panel (completeness_v1).

Compares the panel's Admin2 sums with OpenDengue reference series that are
already on disk (no new downloads):
  * country x week: Admin2 sum / national weekly (Temporal, S_res=Admin0, Total,
    WHO/PAHO; 2014+). Taiwan's national weekly is all zero -> not usable.
  * Admin1 x week, direct: Admin2 sum / Admin1 weekly (Temporal, S_res=Admin1).
    Only Peru 2007-2013 (Probable and confirmed) is usable; the Colombia Admin1
    weekly series (2007-2019) is sparse and far below the Admin2 sums.
  * Peru, same case definition: National extract Admin0 weekly
    "Probable and confirmed" 2000-2013.
  * Admin1 x week, internal (all countries, all years): a "dip" test against the
    two weeks on each side, because no Admin1 reference exists in test years.

Incomplete-week rules (pre-stated; primary k = 0.5, sensitivity 0.4 / 0.6):
  country-week (BR, CO, PE; national >= 20):
    ref = median ratio over the previous 3 epi-years, epi-weeks within +-2 of the
          week (seasonal reference; needs >= 5 values, else no test);
    flag if ratio < k * ref  AND  ratio < k * median ratio of the same epi-year
    (the second condition stops a whole-year definitional level shift, e.g.
    Brazil 2016, from being flagged week by week). The seasonal-only variant is
    written as rule country_seasonal_only (sensitivity).
  adm1-week (all countries): x_t < k * min(mean(x_{t-2..t-1}), mean(x_{t+1..t+2}))
    with that minimum >= DIP_FLOOR cases. Not evaluable in the last/first 2 weeks.
    If the national reference dips in the same week (national_t < k * its own
    neighbour minimum), the flag is labelled adm1_dip_reference_also_dips: a
    surveillance-wide dip (year-end holiday week), not an Admin2 gap.
  Peru adm1-week 2007-2013 (pe_adm1_direct): Admin1 ref >= 20 and ratio <
    k * that department-year's median ratio.
  action = exclude for primary rules flagged at k <= 0.5, else sensitivity.

Usage: python scripts/data/completeness_check.py
Outputs: data/processed/exclusions_v1/*.csv (exclusion lists + diagnostics).
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from pop.data.opendengue import TEMPORAL_CSV

NATIONAL_CSV = Path("data/raw/opendengue/V1.3.1/extracted/National_extract_V1_3_1/"
                    "National_extract_V1_3_1.csv")
COUNTRIES = ["BRAZIL", "COLOMBIA", "PERU", "TAIWAN"]
TEST_YEARS = {"BRAZIL": [2020, 2021, 2022, 2023, 2024], "COLOMBIA": [2020, 2021, 2022],
              "PERU": [2020, 2021, 2022, 2023], "TAIWAN": [2020, 2022, 2023, 2024]}
TRAIN_YEARS = range(2018, 2024)  # target years used by any origin (2018..Y-1)
KS = [0.4, 0.5, 0.6]
K_PRIMARY = 0.5
MIN_NAT = 20
PRIOR_YEARS = 3
WEEK_WIN = 2
MIN_REF_N = 5
DIP_FLOOR = 50
LATE_ENTRY_FROM = 2018


def epi_year(s):
    return (pd.to_datetime(s) + pd.Timedelta(days=3)).dt.year


def epi_week(s):
    d = pd.to_datetime(s) + pd.Timedelta(days=3)
    return (d.dt.day_of_year - 1) // 7 + 1


def load_refs():
    cols = ["adm_0_name", "adm_1_name", "calendar_start_date", "dengue_total", "T_res",
            "S_res", "case_definition_standardised"]
    t = pd.read_csv(TEMPORAL_CSV, usecols=cols, low_memory=False)
    t = t[t["adm_0_name"].isin(COUNTRIES) & (t["T_res"] == "Week")
          & t["S_res"].isin(["Admin0", "Admin1"])].copy()
    t["dengue_total"] = pd.to_numeric(t["dengue_total"], errors="coerce")
    t["week_start"] = pd.to_datetime(t["calendar_start_date"])
    nat = (t[t["S_res"] == "Admin0"].groupby(["adm_0_name", "week_start"])["dengue_total"]
           .sum().rename("national").reset_index().rename(columns={"adm_0_name": "country"}))
    a1 = (t[t["S_res"] == "Admin1"].groupby(["adm_0_name", "adm_1_name", "week_start"])
          ["dengue_total"].sum().rename("ref").reset_index()
          .rename(columns={"adm_0_name": "country", "adm_1_name": "adm1"}))
    n = pd.read_csv(NATIONAL_CSV, low_memory=False)
    n = n[(n["adm_0_name"] == "PERU") & (n["T_res"] == "Week")
          & (n["case_definition_standardised"] == "Probable and confirmed")].copy()
    n["week_start"] = pd.to_datetime(n["calendar_start_date"])
    n["dengue_total"] = pd.to_numeric(n["dengue_total"], errors="coerce")
    pe_pc = n.groupby("week_start")["dengue_total"].sum().rename("ref").reset_index()
    return nat, a1, pe_pc


def country_week(panel, nat):
    a2 = panel.groupby(["country", "week_start"])["cases"].sum().rename("admin2").reset_index()
    w = a2.merge(nat, on=["country", "week_start"], how="left")
    w["year"], w["epiweek"] = epi_year(w["week_start"]), epi_week(w["week_start"])
    w["ratio"] = w["admin2"] / w["national"].where(w["national"] > 0)
    ok = (w["national"] >= MIN_NAT) & w["ratio"].notna() & (w["country"] != "TAIWAN")
    w["evaluable"] = ok
    ym = w[ok].groupby(["country", "year"])["ratio"].median().rename("year_median")
    w = w.merge(ym.reset_index(), on=["country", "year"], how="left")
    refs, ns = [], []
    pool = w[ok]
    for r in w.itertuples():
        p = pool[(pool["country"] == r.country) & (pool["year"] < r.year)
                 & (pool["year"] >= r.year - PRIOR_YEARS)
                 & ((pool["epiweek"] - r.epiweek).abs() <= WEEK_WIN)]["ratio"]
        ns.append(len(p))
        refs.append(p.median() if len(p) >= MIN_REF_N else np.nan)
    w["seasonal_ref"], w["seasonal_n"] = refs, ns
    for k in KS:
        w[f"flag_k{int(k * 100)}"] = (ok & (w["ratio"] < k * w["seasonal_ref"])
                                     & (w["ratio"] < k * w["year_median"]))
    w["rel_seasonal"] = w["ratio"] / w["seasonal_ref"]
    return w


def adm1_direct(panel, a1, pe_pc):
    a2 = (panel.groupby(["country", "adm1", "week_start"])["cases"].sum()
          .rename("admin2").reset_index())
    d = a1.merge(a2, on=["country", "adm1", "week_start"], how="inner")
    d["year"] = epi_year(d["week_start"])
    d["ratio"] = d["admin2"] / d["ref"].where(d["ref"] > 0)
    # Peru national, same case definition (2000-2013)
    pn = panel[panel["country"] == "PERU"].groupby("week_start")["cases"].sum() \
        .rename("admin2").reset_index().merge(pe_pc, on="week_start", how="inner")
    pn["year"] = epi_year(pn["week_start"])
    pn["ratio"] = pn["admin2"] / pn["ref"].where(pn["ref"] > 0)
    return d, pn


def _dip_ratio(df, keys, col):
    g = df.groupby(keys)[col]
    prev = (g.shift(1) + g.shift(2)) / 2
    nxt = (g.shift(-1) + g.shift(-2)) / 2
    nmin = np.minimum(prev, nxt)
    return nmin, df[col] / nmin


def adm1_dip(panel, w):
    a = (panel.groupby(["country", "adm1", "week_start"])["cases"].sum()
         .rename("x").reset_index().sort_values(["country", "adm1", "week_start"]))
    a["neighbour_min"], a["ratio"] = _dip_ratio(a, ["country", "adm1"], "x")
    a["evaluable"] = a["neighbour_min"] >= DIP_FLOOR
    for k in KS:
        a[f"flag_k{int(k * 100)}"] = a["evaluable"] & (a["ratio"] < k)
    a["year"] = epi_year(a["week_start"])
    # does the national reference dip in the same week? (surveillance-wide dip,
    # e.g. the Christmas/New-Year week, not an Admin2 completeness problem)
    n = w[["country", "week_start", "national"]].sort_values(["country", "week_start"]).copy()
    _, n["national_dip"] = _dip_ratio(n, ["country"], "national")
    a = a.merge(n[["country", "week_start", "national_dip"]], on=["country", "week_start"],
                how="left")
    return a


def strictest_k(df, prefix="flag_k"):
    """Smallest k in KS at which the row is flagged (NaN if never)."""
    out = pd.Series(np.nan, index=df.index)
    for k in sorted(KS, reverse=True):
        out = out.where(~df[f"{prefix}{int(k * 100)}"], k)
    return out


def shares(panel, flags, scope):
    """Share of test rows / test cases covered by flags (country or adm1 scope)."""
    out = []
    for c, yrs in TEST_YEARS.items():
        p = panel[(panel["country"] == c) & panel["year"].isin(yrs)]
        f = flags[flags["country"] == c]
        keys = ["country", "week_start"] + (["adm1"] if scope == "adm1" else [])
        m = p.merge(f[keys].drop_duplicates().assign(_f=True), on=keys, how="left")
        hit = m["_f"].fillna(False).astype(bool)
        out.append(dict(country=c, scope=scope, test_years="/".join(map(str, yrs)),
                        n_weeks=int(f[f["year"].isin(yrs)]["week_start"].nunique()),
                        n_flag_units_weeks=int(len(f[f["year"].isin(yrs)])),
                        row_share=hit.mean(), case_share=m.loc[hit, "cases"].sum() / m["cases"].sum()))
    return pd.DataFrame(out)


def shares_union(panel, flags):
    """Union of country-scope and adm1-scope flags -> test row / case shares."""
    out = []
    for c, yrs in TEST_YEARS.items():
        p = panel[(panel["country"] == c) & panel["year"].isin(yrs)]
        f = flags[(flags["country"] == c)]
        cw = f[f["scope"] == "country"][["week_start"]].drop_duplicates().assign(_c=True)
        aw = f[f["scope"] == "adm1"][["adm1", "week_start"]].drop_duplicates().assign(_a=True)
        m = p.merge(cw, on="week_start", how="left").merge(aw, on=["adm1", "week_start"], how="left")
        hit = m["_c"].fillna(False).astype(bool) | m["_a"].fillna(False).astype(bool)
        out.append(dict(country=c, scope="union", test_years="/".join(map(str, yrs)),
                        n_weeks=int(f[f["year"].isin(yrs)]["week_start"].nunique()),
                        n_flag_units_weeks=int(len(f[f["year"].isin(yrs)])),
                        row_share=hit.mean(), case_share=m.loc[hit, "cases"].sum() / m["cases"].sum()))
    return pd.DataFrame(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--panel", default="data/processed/panel_weekly_v1.parquet")
    ap.add_argument("--out", default="data/processed/exclusions_v1")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    panel = pd.read_parquet(a.panel, columns=["unit_id", "country", "adm1", "adm2",
                                              "week_start", "year", "cases", "observed"])
    panel["week_start"] = pd.to_datetime(panel["week_start"])
    for c in ["country", "adm1", "unit_id", "adm2"]:
        panel[c] = panel[c].astype(str)
    panel["year"] = panel["year"].astype(int)
    nat, a1, pe_pc = load_refs()

    # 1. country x week
    w = country_week(panel, nat)
    w.to_csv(out / "diag_country_week.csv", index=False, float_format="%.4f")
    ev = w[w["evaluable"]]
    yr = ev.groupby(["country", "year"]).agg(
        weeks=("ratio", "size"), admin2=("admin2", "sum"), national=("national", "sum"),
        median=("ratio", "median"), p10=("ratio", lambda s: s.quantile(.1)),
        p90=("ratio", lambda s: s.quantile(.9)),
        cv=("ratio", lambda s: s.std() / s.mean()),
        min_rel_seasonal=("rel_seasonal", "min"),
        **{f"flag_k{int(k * 100)}": (f"flag_k{int(k * 100)}", "sum") for k in KS}).reset_index()
    yr["sum_ratio"] = yr["admin2"] / yr["national"]
    yr.to_csv(out / "diag_country_year.csv", index=False, float_format="%.4f")

    # 2. Admin1 x week
    d, pn = adm1_direct(panel, a1, pe_pc)
    d.to_csv(out / "diag_adm1_week_direct.csv", index=False, float_format="%.4f")
    pn.to_csv(out / "diag_peru_national_same_definition.csv", index=False, float_format="%.4f")
    dy = d[d["ref"] > 0].groupby(["country", "year"]).agg(
        adm1_weeks=("ratio", "size"), admin2=("admin2", "sum"), ref=("ref", "sum"),
        median=("ratio", "median"),
        share_ref_ge20_ratio_lt05=("ratio", lambda s: ((s < .5) & (d.loc[s.index, "ref"] >= 20)).mean()),
        ref_cases_in_zero_admin2=("ref", lambda s: s[d.loc[s.index, "admin2"] == 0].sum()),
    ).reset_index()
    dy["sum_ratio"] = dy["admin2"] / dy["ref"]
    dy["share_ref_cases_in_zero_admin2"] = dy["ref_cases_in_zero_admin2"] / dy["ref"]
    dy.to_csv(out / "diag_adm1_year_direct.csv", index=False, float_format="%.4f")
    py = pn.groupby("year").agg(weeks=("ratio", "size"), admin2=("admin2", "sum"),
                                ref=("ref", "sum"), median=("ratio", "median"),
                                p10=("ratio", lambda s: s.quantile(.1)),
                                p90=("ratio", lambda s: s.quantile(.9))).reset_index()
    py["sum_ratio"] = py["admin2"] / py["ref"]
    py.to_csv(out / "diag_peru_national_same_definition_year.csv", index=False,
              float_format="%.4f")
    dip = adm1_dip(panel, w)
    dip_f = dip[dip[[f"flag_k{int(k * 100)}" for k in KS]].any(axis=1)]
    dip_f.to_csv(out / "diag_adm1_week_dip_flags.csv", index=False, float_format="%.4f")
    dip_sum = dip[dip["evaluable"]].groupby(["country", "year"]).agg(
        evaluable=("x", "size"),
        **{f"flag_k{int(k * 100)}": (f"flag_k{int(k * 100)}", "sum") for k in KS}).reset_index()
    dip_sum.to_csv(out / "diag_adm1_dip_year.csv", index=False)
    # Peru Admin1 direct (same case definition, 2007-2013): ratio < k x dept-year median
    pd1 = d[(d["country"] == "PERU") & (d["ref"] >= MIN_NAT)].copy()
    pd1["dept_year_median"] = pd1.groupby(["adm1", "year"])["ratio"].transform("median")
    for k in KS:
        pd1[f"flag_k{int(k * 100)}"] = pd1["ratio"] < k * pd1["dept_year_median"]

    # 3. exclusion file: one row per flagged (week, scope, adm1, rule) at any k;
    #    strictest_k = smallest k flagging it; action = exclude for primary rules at k<=0.5.
    cols = ["country", "week_start", "scope", "adm1", "ratio", "rule", "strictest_k", "action", "year"]
    parts = []
    c1 = w.copy()
    c1["strictest_k"] = strictest_k(c1)
    c1 = c1[c1["strictest_k"].notna()].assign(
        scope="country", adm1="", rule="country_seasonal_and_year_median")
    parts.append(c1)
    c2 = w.copy()  # sensitivity: seasonal reference only (no same-year guard)
    for k in KS:
        c2[f"s_k{int(k * 100)}"] = c2["evaluable"] & (c2["ratio"] < k * c2["seasonal_ref"])
    c2["strictest_k"] = strictest_k(c2, "s_k")
    c2 = c2[c2["strictest_k"].notna()].assign(scope="country", adm1="", rule="country_seasonal_only")
    parts.append(c2)
    a1f = dip.copy()
    a1f["strictest_k"] = strictest_k(a1f)
    a1f = a1f[a1f["strictest_k"].notna()].assign(scope="adm1")
    ref_dips = a1f["national_dip"] < a1f["strictest_k"].clip(lower=K_PRIMARY)
    a1f["rule"] = np.where(ref_dips, "adm1_dip_reference_also_dips", "adm1_dip")
    parts.append(a1f)
    p1 = pd1.copy()
    p1["strictest_k"] = strictest_k(p1)
    p1 = p1[p1["strictest_k"].notna()].assign(scope="adm1", rule="pe_adm1_direct")
    parts.append(p1)
    inc = pd.concat([p.reindex(columns=cols) for p in parts], ignore_index=True)
    primary = inc["rule"].isin(["country_seasonal_and_year_median", "adm1_dip", "pe_adm1_direct"])
    inc["action"] = np.where(primary & (inc["strictest_k"] <= K_PRIMARY), "exclude", "sensitivity")
    inc = inc.sort_values(["country", "week_start", "scope", "adm1", "rule"])
    w_out = inc.drop(columns="year").copy()
    w_out["week_start"] = w_out["week_start"].dt.date
    w_out.to_csv(out / "incomplete_weeks.csv", index=False, float_format="%.4f")

    # shares of test rows / cases
    sh = []
    for label, sel in [("exclude", inc["action"] == "exclude"),
                       ("exclude+sensitivity", inc["action"].notna()),
                       ("k0.4_primary", primary & (inc["strictest_k"] <= 0.4)),
                       ("k0.6_primary", primary & (inc["strictest_k"] <= 0.6))]:
        f = inc[sel]
        for scope in ["country", "adm1"]:
            s = shares(panel, f[f["scope"] == scope], scope)
            s["set"] = label
            sh.append(s)
        both = shares_union(panel, f)
        both["set"] = label
        sh.append(both)
    sh = pd.concat(sh)
    sh.to_csv(out / "diag_test_shares.csv", index=False, float_format="%.5f")
    tr = inc[(inc["action"] == "exclude") & inc["year"].isin(TRAIN_YEARS)]

    # 4. no-geometry units
    u = pd.read_parquet("data/interim/boundaries/opendengue_units_v1.parquet",
                        columns=["unit_id", "country", "adm1", "adm2", "match_method", "geometry"])
    ng = u[u["geometry"].isna()].drop(columns="geometry")
    tot = panel.groupby("unit_id").agg(total_cases=("cases", "sum"),
                                       cases_2018_on=("cases", lambda s: s[panel.loc[s.index, "year"] >= 2018].sum()))
    ng = ng.merge(tot.reset_index(), on="unit_id", how="left")
    ng["reason"] = np.where(ng["adm2"].eq("OTHER"), "non-spatial OTHER bucket",
                            "no polygon in boundary source")
    ng.to_csv(out / "no_geometry_units.csv", index=False)

    # 5. late-entry units (first week with cases > 0)
    pos = panel[panel["cases"] > 0].groupby("unit_id")["week_start"].min().rename("first_case_week")
    obs = panel[panel["observed"]].groupby("unit_id")["week_start"].min().rename("first_row_week")
    le = panel.drop_duplicates("unit_id")[["unit_id", "country", "adm1", "adm2"]] \
        .merge(pos.reset_index(), on="unit_id", how="left") \
        .merge(obs.reset_index(), on="unit_id", how="left") \
        .merge(tot["total_cases"].reset_index(), on="unit_id", how="left")
    le["first_year"] = epi_year(le["first_case_week"]).astype("Int64")
    le = le[le["first_year"].isna() | (le["first_year"] >= LATE_ENTRY_FROM)]
    for c in ["first_case_week", "first_row_week"]:
        le[c] = le[c].dt.date
    le.sort_values(["country", "first_year", "unit_id"]).to_csv(out / "late_entry_units.csv",
                                                                 index=False)

    pd.set_option("display.width", 250)
    print("== country-year ratio ==\n", yr.round(3).to_string(index=False))
    print("== adm1 direct ==\n", dy.round(3).to_string(index=False))
    print("== peru same-definition national ==\n", py.round(3).to_string(index=False))
    print("== dip per year (evaluable / flags) ==\n",
          dip_sum[dip_sum["year"] >= 2014].to_string(index=False))
    print("== test shares ==\n", sh.round(4).to_string(index=False))
    print("== incomplete_weeks (year>=2013) ==\n",
          inc[inc["year"] >= 2013].round(3).to_string(index=False))
    print("== primary flags in training years 2018-2023 ==\n",
          tr.groupby(["country", "scope", "rule", "year"]).size().to_string())
    print("== no geometry ==\n", ng.to_string(index=False))
    print("== late entry by country x first_year ==\n",
          le.groupby(["country", "first_year"], dropna=False).size().unstack(0).to_string())


if __name__ == "__main__":
    main()
