"""Independent verification of docs/data/zero_fill_crosscheck_2024.md.

Subcommands (run from the repo root after `source env.sh`):
  download  re-download a stratified 20% sample of data/raw/infodengue/2024_check/manifest.tsv
            into data/raw/infodengue/2024_check_verify/ and compare with the originals
  es        Espirito Santo checks on the OpenDengue raw extracts and the panel
  scan      Admin1-year collapse scan on the panel (all four countries), with a
            Brazil cross-check against the OpenDengue Admin1 / Admin0 series

Written independently of scripts/data/zero_fill_check_2024.py.
"""
import hashlib
import io
import json
import sys
import time
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(".")
ORIG = ROOT / "data/raw/infodengue/2024_check"
VER = ROOT / "data/raw/infodengue/2024_check_verify"
OUT = VER / "analysis"
OD = ROOT / "data/raw/opendengue/V1.3.1/extracted"
PANEL = ROOT / "data/processed/panel_weekly_v1.parquet"
ES_FORCE = ["3205309", "3205200", "3205002", "3201308"]  # Vitoria, Vila Velha, Serra, Cariacica
SEED = 990101


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def fetch(url, tries=5):
    for k in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "research-data-verifier/1.0"})
            with urllib.request.urlopen(req, timeout=120) as r:
                return r.read()
        except Exception as e:  # noqa: BLE001
            wait = 3 * 2 ** k
            print(f"retry {k+1} after {e!r}; sleep {wait}s", flush=True)
            time.sleep(wait)
    raise RuntimeError(f"failed: {url}")


def cmd_download():
    VER.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    man = pd.read_csv(ORIG / "manifest.tsv", sep="\t", dtype=str)
    rng = np.random.default_rng(SEED)
    picks = []
    for g, d in man.groupby("group"):
        n = int(np.ceil(0.2 * len(d)))
        forced = d[d.file.str.contains("|".join(ES_FORCE))] if g == "e_espirito_santo" else d.iloc[:0]
        rest = d.drop(forced.index)
        k = max(n - len(forced), 0)
        picks.append(forced)
        picks.append(rest.iloc[rng.choice(len(rest), size=k, replace=False)])
    sample = pd.concat(picks)
    rows = []
    vman = []
    for _, r in sample.iterrows():
        dest = VER / r.file
        if not dest.exists():
            body = fetch(r.url)
            dest.write_bytes(body)
            vman.append({"file": r.file, "url": r.url,
                         "retrieved_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                         "sha256": hashlib.sha256(body).hexdigest(), "bytes": len(body)})
            time.sleep(1.5)
        o = pd.read_csv(ORIG / r.file)
        v = pd.read_csv(dest)
        orig_sha_file = sha(ORIG / r.file)
        m = o.merge(v, on="data_iniSE", how="outer", suffixes=("_o", "_v"), indicator=True)
        both = m[m._merge == "both"]
        rec = {
            "file": r.file, "group": r.group,
            "sha_manifest_eq_file": orig_sha_file == r.sha256,
            "sha_eq": orig_sha_file == sha(dest),
            "rows_manifest": int(r.data_rows), "rows_orig": len(o), "rows_new": len(v),
            "weeks_only_one_side": int((m._merge != "both").sum()),
        }
        for c in ["casprov", "casos", "casconf"]:
            a = pd.to_numeric(both[c + "_o"], errors="coerce").fillna(-1)
            b = pd.to_numeric(both[c + "_v"], errors="coerce").fillna(-1)
            rec[f"{c}_weeks_diff"] = int((a != b).sum())
            rec[f"{c}_sum_orig"] = float(a.clip(lower=0).sum())
            rec[f"{c}_sum_new"] = float(b.clip(lower=0).sum())
        # which columns differ at all
        diffcols = []
        for c in o.columns:
            if c == "data_iniSE" or c + "_o" not in both:
                continue
            a, b = both[c + "_o"].astype(str), both[c + "_v"].astype(str)
            if (a != b).any():
                diffcols.append(c)
        rec["cols_differing"] = ";".join(diffcols)
        rows.append(rec)
        print(rec, flush=True)
    res = pd.DataFrame(rows)
    res.to_csv(OUT / "download_compare.csv", index=False)
    if vman:
        mp = VER / "manifest_verify.tsv"
        pd.DataFrame(vman).to_csv(mp, sep="\t", index=False, mode="a", header=not mp.exists())
    print(res[["sha_manifest_eq_file", "sha_eq"]].value_counts())
    print("rows equal:", (res.rows_orig == res.rows_new).all(),
          "casprov diffs:", res.casprov_weeks_diff.sum(), "casos diffs:", res.casos_weeks_diff.sum())


def read_od(name, cols=None):
    p = OD / f"{name}_extract_V1_3_1" / f"{name}_extract_V1_3_1.csv"
    df = pd.read_csv(p, usecols=cols, dtype=str, keep_default_na=False)
    return df


ODCOLS = ["adm_0_name", "adm_1_name", "adm_2_name", "IBGE_code", "calendar_start_date",
          "calendar_end_date", "Year", "dengue_total", "S_res", "T_res"]


def cmd_es():
    OUT.mkdir(parents=True, exist_ok=True)
    rep = {}
    for name in ["Temporal", "Spatial", "National"]:
        df = read_od(name, ODCOLS)
        br = df[df.adm_0_name == "BRAZIL"].copy()
        br["cases"] = pd.to_numeric(br.dengue_total, errors="coerce")
        br["y"] = br.calendar_start_date.str[:4].astype(int)
        es = br[br.adm_1_name.str.upper().str.contains("ESP.RITO SANTO", regex=True)
                | br.IBGE_code.str.startswith("32")]
        g = es.groupby(["S_res", "T_res", "y"]).agg(rows=("cases", "size"), cases=("cases", "sum"),
                                                     zero_rows=("cases", lambda s: int((s == 0).sum())),
                                                     last_start=("calendar_start_date", "max")).reset_index()
        g.to_csv(OUT / f"es_od_{name.lower()}_by_year.csv", index=False)
        print(f"== {name} ES rows by S_res/T_res/year\n{g.to_string()}", flush=True)
        a2 = es[(es.S_res == "Admin2") & (es.T_res == "Week")]
        rep[name] = {
            "es_admin2_week_rows": len(a2),
            "es_admin2_week_last_start": a2.calendar_start_date.max() if len(a2) else None,
            "es_admin2_week_last_positive_start": a2[a2.cases > 0].calendar_start_date.max() if len(a2) else None,
            "es_admin2_units": int(a2.IBGE_code.nunique()),
            "es_rows_after_2020-12-20_any_res": int((es.calendar_start_date > "2020-12-20").sum()),
            "es_res_after_2020": sorted(es[es.calendar_start_date > "2020-12-20"].S_res.unique().tolist()),
        }
        # Brazil Admin0 / Admin1 yearly series for the scan cross-check
        allc = df[df.adm_0_name.isin(["BRAZIL", "PERU", "COLOMBIA", "TAIWAN"])].copy()
        allc["cases"] = pd.to_numeric(allc.dengue_total, errors="coerce")
        allc["y"] = allc.calendar_start_date.str[:4].astype(int)
        lvl = allc[allc.S_res.isin(["Admin0", "Admin1"])]
        if len(lvl):
            gg = lvl.groupby(["adm_0_name", "S_res", "T_res", "adm_1_name", "y"]).cases.sum().reset_index()
            gg.to_csv(OUT / f"od_{name.lower()}_admin01_by_year.csv", index=False)
            rep[name]["admin01_series"] = gg.groupby(["adm_0_name", "S_res", "T_res"]).y.agg(["min", "max"]).reset_index().to_dict("records")
        # weekly last date of ES admin2 by municipality
        if name == "Temporal" and len(a2):
            last = a2.groupby("IBGE_code").calendar_start_date.max()
            rep[name]["es_unit_last_week_distribution"] = last.value_counts().head(10).to_dict()
    # panel
    p = pd.read_parquet(PANEL, columns=["unit_id", "country", "adm1", "week_start", "year", "cases",
                                        "observed", "zero_filled", "flag_gap"])
    es = p[(p.country == "BRAZIL") & p.unit_id.str.startswith("32")]
    pg = es.groupby("year").agg(units=("unit_id", "nunique"), rows=("cases", "size"),
                                observed=("observed", "sum"), zero_filled=("zero_filled", "sum"),
                                cases=("cases", "sum"), pos_rows=("cases", lambda s: int((s > 0).sum()))).reset_index()
    pg.to_csv(OUT / "es_panel_by_year.csv", index=False)
    print(pg.to_string())
    ws = pd.to_datetime(es.week_start.astype(str))
    rep["panel"] = {"es_units": int(es.unit_id.nunique()),
                    "last_observed_week": str(ws[es.observed].max().date()),
                    "last_positive_week": str(ws[es.cases > 0].max().date()),
                    "rows_after_2020-12-20": int((ws > "2020-12-20").sum()),
                    "observed_after_2020-12-20": int(es.observed[ws > "2020-12-20"].sum()),
                    "adm1_label": es.adm1.unique().tolist()}
    # InfoDengue: verify-folder files for the four named cities (2020-2024)
    idrows = []
    for f in sorted(VER.glob("alertcity_32*_2020_2024.csv")):
        d = pd.read_csv(f)
        d["ey"] = d.SE // 100
        for ey, dd in d.groupby("ey"):
            idrows.append({"file": f.name, "geocode": f.name.split("_")[1], "municipio": dd.municipio_nome.iloc[0],
                           "epi_year": int(ey), "weeks": len(dd), "casprov": float(dd.casprov.sum()),
                           "casos": float(dd.casos.sum()), "weeks_casprov_pos": int((dd.casprov > 0).sum())})
    idf = pd.DataFrame(idrows)
    idf.to_csv(OUT / "es_infodengue_verify_by_year.csv", index=False)
    print(idf.to_string())
    (OUT / "es_report.json").write_text(json.dumps(rep, indent=2, default=str))
    print(json.dumps(rep, indent=2, default=str))


WINDOWS = {"BRAZIL": (2014, 2024), "COLOMBIA": (2014, 2022), "PERU": (2014, 2023), "TAIWAN": (2014, 2024)}


def cmd_scan():
    OUT.mkdir(parents=True, exist_ok=True)
    p = pd.read_parquet(PANEL, columns=["unit_id", "country", "adm1", "year", "cases", "observed"])
    rows = []
    for c, (y0, y1) in WINDOWS.items():
        d = p[(p.country == c) & p.year.between(y0, y1)]
        g = d.groupby(["adm1", "year"]).agg(cases=("cases", "sum"), observed_rows=("observed", "sum"),
                                            units_obs=("unit_id", lambda s: 0)).reset_index()
        # units with any observed row per adm1-year
        uo = d[d.observed].groupby(["adm1", "year"]).unit_id.nunique().rename("units_observed")
        g = g.drop(columns="units_obs").merge(uo, on=["adm1", "year"], how="left").fillna({"units_observed": 0})
        nat = d.groupby("year").cases.sum().rename("country_cases")
        g = g.merge(nat, on="year")
        g["country"] = c
        rows.append(g)
    t = pd.concat(rows)
    out = []
    for (c, a), d in t.groupby(["country", "adm1"]):
        d = d.sort_values("year")
        for i, r in d.iterrows():
            others = d[d.year != r.year].cases
            med = float(others.median())
            share_other = (d[d.year != r.year].cases / d[d.year != r.year].country_cases).median()
            ratio = r.cases / med if med > 0 else np.nan
            share = r.cases / r.country_cases if r.country_cases > 0 else np.nan
            out.append({"country": c, "adm1": a, "year": int(r.year), "cases": float(r.cases),
                        "observed_rows": int(r.observed_rows), "units_observed": int(r.units_observed),
                        "median_other_years": med, "ratio_to_median": ratio,
                        "share_of_country": share, "median_share_other_years": share_other,
                        "share_ratio": share / share_other if share_other and share_other > 0 else np.nan})
    s = pd.DataFrame(out)
    # flag A: cases < 5% of own median of other years (median >= 20 to avoid tiny-count noise)
    s["flag_lt5pct_median"] = (s.median_other_years >= 20) & (s.ratio_to_median < 0.05)
    # flag B: zero observed rows while median of other years is large (>= 100)
    s["flag_zero_rows"] = (s.observed_rows == 0) & (s.median_other_years >= 100)
    # flag C: share of country collapses to < 5% of its usual share (median other-year cases >= 100)
    s["flag_share_collapse"] = (s.median_other_years >= 100) & (s.share_ratio < 0.05)
    s["flagged"] = s.flag_lt5pct_median | s.flag_zero_rows | s.flag_share_collapse
    s.to_csv(OUT / "admin1_year_scan.csv", index=False)
    f = s[s.flagged].sort_values(["country", "adm1", "year"])
    f.to_csv(OUT / "admin1_year_flags.csv", index=False)
    pd.set_option("display.width", 250)
    print(f.to_string())
    print("n flags", len(f), "by country", f.country.value_counts().to_dict())


if __name__ == "__main__":
    {"download": cmd_download, "es": cmd_es, "scan": cmd_scan}[sys.argv[1]]()
