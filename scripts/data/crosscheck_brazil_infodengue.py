"""Cross-check OpenDengue V1.3.1 Brazil weekly Admin2 rows against InfoDengue (alertcity API).

Question: does an absent OpenDengue municipality-week mean zero cases?
Outputs -> outputs/data_audit/brazil_infodengue_*.csv ; raw API pulls -> data/reference/infodengue/
"""
import hashlib, io, time, datetime, urllib.request, os
import numpy as np, pandas as pd

OD = "data/raw/opendengue/V1.3.1/extracted/Temporal_extract_V1_3_1/Temporal_extract_V1_3_1.csv"
REF = "data/reference/infodengue"; OUT = "outputs/data_audit"
os.makedirs(REF, exist_ok=True); os.makedirs(OUT, exist_ok=True)
API = ("https://info.dengue.mat.br/api/alertcity?geocode={g}&disease=dengue&format=csv"
       "&ew_start=1&ew_end=53&ey_start=2017&ey_end=2023")
rng = np.random.default_rng(20261115)

od = pd.read_csv(OD, usecols=["adm_0_name", "IBGE_code", "calendar_start_date", "dengue_total", "S_res", "T_res"], dtype=str)
od = od[(od.adm_0_name == "BRAZIL") & (od.T_res == "Week") & (od.S_res == "Admin2")].copy()
od["date"] = pd.to_datetime(od.calendar_start_date); od["yr"] = od.date.dt.year
od["od"] = pd.to_numeric(od.dengue_total, errors="coerce"); od["geo"] = od.IBGE_code.astype(int)
od = od.groupby(["geo", "date", "yr"], as_index=False).od.sum(min_count=1)
allgeo = set(od.geo)
present = od.groupby("yr").geo.apply(set)
nweeks22 = od[od.yr == 2022].groupby("geo").size()

abs17 = sorted(allgeo - present[2017]); abs22 = sorted(allgeo - present[2022])
both = sorted(set(abs17) & set(abs22))
pick_a = list(rng.choice(abs17, 8, replace=False)) + list(rng.choice(sorted(set(abs22) - set(abs17)) or abs22, 7, replace=False))
part = nweeks22[(nweeks22 > 3) & (nweeks22 < 45)].index.values
pick_b = list(rng.choice(part, 15, replace=False))
big = {3550308: "Sao Paulo", 3304557: "Rio de Janeiro", 3106200: "Belo Horizonte", 2927408: "Salvador",
       2304400: "Fortaleza", 5300108: "Brasilia", 1302603: "Manaus", 4106902: "Curitiba",
       2611606: "Recife", 5208707: "Goiania"}
groups = {int(g): "a_absent17" for g in pick_a[:8]} | {int(g): "a_absent22" for g in pick_a[8:]} \
    | {int(g): "b_partial22" for g in pick_b} | {g: "c_large" for g in big}
print(f"OD munis={len(allgeo)} absent2017={len(abs17)} absent2022={len(abs22)} absent_both={len(both)} partial2022={len(part)}")

frames, man = [], []
for g, grp in groups.items():
    fn = f"{REF}/alertcity_{g}_2017_2023.csv"
    if not os.path.exists(fn):
        url = API.format(g=g)
        for attempt in range(3):
            try:
                raw = urllib.request.urlopen(url, timeout=60).read(); break
            except Exception as e:
                print("retry", g, e); time.sleep(5)
        open(fn, "wb").write(raw); time.sleep(1.0)
        man.append([os.path.basename(fn), hashlib.sha256(raw).hexdigest(), url, str(datetime.date.today())])
    x = pd.read_csv(fn)
    x = x[["data_iniSE", "SE", "casos", "casprov"]].assign(geo=g, group=grp)
    frames.append(x)
if man:
    with open(f"{REF}/_fetched.tsv", "a") as f:
        for m in man: f.write("\t".join(m) + "\n")

idg = pd.concat(frames)
idg["date"] = pd.to_datetime(idg.data_iniSE); idg["yr"] = idg.date.dt.year
assert (idg.date.dt.dayofweek == 6).all(), "InfoDengue weeks not Sunday-start"
m = idg.merge(od[od.geo.isin(groups)][["geo", "date", "od"]], on=["geo", "date"], how="left")
m["od_present"] = m.od.notna()
m = m[m.yr.isin([2017, 2019, 2022, 2023])]
m.to_csv(f"{OUT}/brazil_infodengue_merged.csv", index=False)

rows = []
for (grp, yr), s in m.groupby(["group", "yr"]):
    a, p = s[~s.od_present], s[s.od_present]
    r = dict(group=grp, year=yr, munis=s.geo.nunique(), weeks_absent=len(a),
             absent_casos_eq0=(a.casos == 0).mean() if len(a) else np.nan,
             absent_casos_sum=a.casos.sum(), absent_casos_max=a.casos.max() if len(a) else np.nan,
             absent_casprov_sum=a.casprov.sum(), weeks_present=len(p))
    if len(p):
        r |= dict(present_od_sum=p.od.sum(), present_casos_sum=p.casos.sum(), present_casprov_sum=p.casprov.sum(),
                  exact_casos=(p.od == p.casos).mean(), exact_casprov=(p.od == p.casprov).mean(),
                  within1_casprov=((p.od - p.casprov).abs() <= 1).mean(),
                  corr_casprov=p.od.corr(p.casprov) if p.casprov.notna().sum() > 2 else np.nan)
    rows.append(r)
summ = pd.DataFrame(rows)
summ.to_csv(f"{OUT}/brazil_infodengue_summary.csv", index=False)
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
print(summ.round(3).to_string())
# gaps: absent OD week but InfoDengue >0
gap = m[(~m.od_present) & (m.casos > 0)]
print("absent-but-positive weeks:", len(gap), "of", (~m.od_present).sum())
print(gap.groupby(["group", "yr"]).agg(n=("casos", "size"), casos=("casos", "sum"), casprov=("casprov", "sum")).to_string())
print(gap.sort_values("casos", ascending=False).head(10)[["geo", "group", "data_iniSE", "casos", "casprov"]].to_string())
# present-week mismatches for large cities in 2022/2023
p = m[m.od_present & (m.group == "c_large")]
p = p.assign(ratio_od_casprov=p.od / p.casprov.replace(0, np.nan), ratio_od_casos=p.od / p.casos.replace(0, np.nan))
print(p.groupby("yr")[["ratio_od_casprov", "ratio_od_casos"]].median().to_string())
# do present weeks in OD 2022+ include any zeros? and are OD-present weeks a subset of casos>0?
print("OD-present weeks with casos==0 by yr:", m[m.od_present & (m.casos == 0)].groupby("yr").size().to_dict())
print("OD-present weeks with casprov==0 by yr:", m[m.od_present & (m.casprov == 0)].groupby("yr").size().to_dict())
print("absent weeks with casprov>0 by yr:", m[(~m.od_present) & (m.casprov > 0)].groupby("yr").size().to_dict())
