"""Cross-check OpenDengue V1.3.1 Taiwan weekly Admin2 rows against Taiwan CDC Dengue_Daily.csv
(case-level confirmed cases; Wayback snapshot 2025-07-29 because od.cdc.gov.tw is unreachable from the server).
Outputs -> outputs/data_audit/taiwan_cdc_*.csv
"""
import numpy as np, pandas as pd
from scipy.optimize import linear_sum_assignment

OD = "data/raw/opendengue/V1.3.1/extracted/Temporal_extract_V1_3_1/Temporal_extract_V1_3_1.csv"
CDC = "data/reference/taiwan_cdc/Dengue_Daily_wayback20250729.csv"; OUT = "outputs/data_audit"
COUNTY = {"臺北市": "TAIPEI CITY", "新北市": "NEW TAIPEI CITY", "桃園市": "TAOYUAN CITY", "臺中市": "TAICHUNG CITY",
          "臺南市": "TAINAN CITY", "高雄市": "KAOHSIUNG CITY", "基隆市": "KEELUNG CITY", "新竹市": "HSINCHU CITY",
          "嘉義市": "CHIAYI CITY", "新竹縣": "HSINCHU COUNTY", "苗栗縣": "MIAOLI COUNTY", "彰化縣": "CHANGHUA COUNTY",
          "南投縣": "NANTOU COUNTY", "雲林縣": "YUNLIN COUNTY", "嘉義縣": "CHIAYI COUNTY", "屏東縣": "PINGTUNG COUNTY",
          "宜蘭縣": "YILAN COUNTY", "花蓮縣": "HUALIEN COUNTY", "臺東縣": "TAITUNG COUNTY", "澎湖縣": "PENGHU COUNTY",
          "金門縣": "KINMEN COUNTY", "連江縣": "LIENCHIANG COUNTY"}
wk = lambda d: d - pd.to_timedelta((d.dt.dayofweek + 1) % 7, unit="D")  # Sunday-start week

od = pd.read_csv(OD, usecols=["adm_0_name", "adm_1_name", "adm_2_name", "calendar_start_date", "dengue_total", "S_res", "T_res"], dtype=str)
od = od[(od.adm_0_name == "TAIWAN") & (od.T_res == "Week") & (od.S_res == "Admin2")].copy()
od["week"] = pd.to_datetime(od.calendar_start_date); od["od"] = pd.to_numeric(od.dengue_total)
od["county"] = od.adm_1_name; od["unit"] = od.adm_1_name + "|" + od.adm_2_name
od = od.groupby(["county", "unit", "week"], as_index=False).od.sum()
od["yr"] = od.week.dt.year  # NB: year of Sunday start

c = pd.read_csv(CDC, dtype=str, encoding="utf-8-sig")
c["n"] = pd.to_numeric(c["確定病例數"]).fillna(1)
c["imported"] = c["是否境外移入"].eq("是")
c["county"] = c["居住縣市"].str.replace("台", "臺").map(COUNTY)
c["town_zh"] = c["居住縣市"] + c["居住鄉鎮"]
print("CDC rows", len(c), "unmapped county rows", c.county.isna().sum(), c.loc[c.county.isna(), "居住縣市"].value_counts().head().to_dict())
for col, name in [("發病日", "onset"), ("個案研判日", "confirm"), ("通報日", "notify")]:
    c[name] = wk(pd.to_datetime(c[col], errors="coerce"))
c["onset_yr"] = pd.to_datetime(c["發病日"]).dt.year

# --- 1. national annual totals by definition and date
ann = pd.DataFrame({
    "od": od.groupby(od.week.dt.year).od.sum(),
    "local_onset": c[~c.imported].groupby(c.onset.dt.year).n.sum(),
    "imported_onset": c[c.imported].groupby(c.onset.dt.year).n.sum(),
    "all_onset": c.groupby(c.onset.dt.year).n.sum(),
    "local_notify": c[~c.imported].groupby(c.notify.dt.year).n.sum(),
}).fillna(0).astype(int).loc[1997:2025]
ann.to_csv(f"{OUT}/taiwan_cdc_annual.csv")
print(ann.to_string())

# --- 2. national weekly agreement by definition x date
odw = od.groupby("week").od.sum()
res = []
for imp_lab, sub in [("local", c[~c.imported]), ("imported", c[c.imported]), ("all", c)]:
    for d in ["onset", "notify", "confirm"]:
        cw = sub.groupby(d).n.sum()
        j = pd.concat([odw.rename("od"), cw.rename("cdc")], axis=1).fillna(0)
        j = j[(j.index >= "1998-01-01") & (j.index < "2024-12-29")]
        res.append(dict(series=imp_lab, date=d, weeks=len(j), exact=(j.od == j.cdc).mean(),
                        corr=j.od.corr(j.cdc), od_sum=j.od.sum(), cdc_sum=j.cdc.sum()))
res = pd.DataFrame(res); print(res.round(4).to_string())
best = res.sort_values("exact").iloc[-1]; print("BEST:", best.series, best.date)

# --- 3. township crosswalk by data-driven assignment within county (best definition)
sub = c[~c.imported] if best.series == "local" else (c if best.series == "all" else c[c.imported])
cw = sub.groupby(["county", "town_zh", best.date]).n.sum().rename("cdc").reset_index().rename(columns={best.date: "week"})
xw = []
for cty, o in od.groupby("county"):
    cc = cw[cw.county == cty]
    A = o.pivot_table(index="unit", columns="week", values="od", fill_value=0)
    B = cc.pivot_table(index="town_zh", columns="week", values="cdc", fill_value=0)
    cols = A.columns.union(B.columns); A = A.reindex(columns=cols, fill_value=0); B = B.reindex(columns=cols, fill_value=0)
    S = np.minimum(A.values[:, None, :], B.values[None, :, :]).sum(-1)  # shared cases
    r, k = linear_sum_assignment(-S)
    for i, j in zip(r, k):
        xw.append(dict(county=cty, unit=A.index[i], town_zh=B.index[j], shared=S[i, j], od_tot=A.values[i].sum(), cdc_tot=B.values[j].sum()))
xw = pd.DataFrame(xw); xw.to_csv(f"{OUT}/taiwan_township_crosswalk_inferred.csv", index=False)
print("OD units", od.unit.nunique(), "matched", len(xw), "shared/od_tot", xw.shared.sum() / xw.od_tot.sum())

cwu = cw.merge(xw[["town_zh", "unit"]], on="town_zh", how="left")
print("CDC cases in towns not matched to an OD unit:", cwu[cwu.unit.isna()].cdc.sum(),
      cwu[cwu.unit.isna()].groupby(cwu.week.dt.year).cdc.sum().to_dict())
j = od.merge(cwu.dropna(subset=["unit"])[["unit", "week", "cdc"]], on=["unit", "week"], how="outer")
j["od_present"] = j.od.notna(); j["cdc"] = j.cdc.fillna(0); j["yr"] = j.week.dt.year
j = j[j.week < "2024-12-29"]
j.to_csv(f"{OUT}/taiwan_cdc_unitweek_merged.csv", index=False)
pres = j[j.od_present]
print("unit-week present: n", len(pres), "exact", (pres.od == pres.cdc).mean().round(4), "within1", ((pres.od - pres.cdc).abs() <= 1).mean().round(4))
ab = j[~j.od_present]
print("unit-weeks absent in OD but CDC>0:", len(ab), "cases", ab.cdc.sum())
print(ab.groupby("yr").cdc.agg(["size", "sum"]).to_string())
print("by-year unit-week exact:", pres.groupby("yr").apply(lambda s: round((s.od == s.cdc).mean(), 3)).to_dict())

# --- 4. 2021 and township counts
loc = c[~c.imported]
print("2021 onset local:", loc[loc.onset_yr == 2021].n.sum(), "imported:", c[c.imported & (c.onset_yr == 2021)].n.sum())
print("CDC distinct townships with >=1 local case (1998-2025):", loc.town_zh.nunique(), "| any case:", c.town_zh.nunique())
print("OD units:", od.unit.nunique())
print("local cases by yr 2016-2025:", loc.groupby("onset_yr").n.sum().loc[2016:].to_dict())
print("imported by yr 2016-2025:", c[c.imported].groupby("onset_yr").n.sum().loc[2016:].to_dict())
