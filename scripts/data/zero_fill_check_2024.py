"""Zero-fill cross-check for Brazil epi-year 2024: OpenDengue V1.3.1 panel vs InfoDengue (alertcity API).

Extends scripts/data/crosscheck_brazil_infodengue.py (2017/2019/2022/2023) to the Brazil test year 2024.
Question: is a zero-filled municipality-week in 2024 really a week with 0 probable cases?

Sample (seed 20261118), drawn from the panel's 2024 rows (data/processed/panel_weekly_v1.parquet):
  a_absent24  15 municipalities with no observed OpenDengue week in 2024 (all weeks zero-filled)
  b_partial24 15 municipalities with 4-44 observed weeks in 2024
  c_large     the same 10 large cities as the 2017-2023 check
  d_random    20 municipalities drawn uniformly from all Brazilian panel units (representative of the stratum)
Raw API responses -> data/raw/infodengue/2024_check/ with manifest.tsv (url, utc timestamp, sha256, rows).
Outputs -> outputs/data_audit/brazil_infodengue_2024_{merged,summary}.csv
"""
import datetime, hashlib, io, os, time, urllib.request
import numpy as np, pandas as pd

PANEL = "data/processed/panel_weekly_v1.parquet"
RAW = "data/raw/infodengue/2024_check"; OUT = "outputs/data_audit"
os.makedirs(RAW, exist_ok=True); os.makedirs(OUT, exist_ok=True)
API = ("https://info.dengue.mat.br/api/alertcity?geocode={g}&disease=dengue&format=csv"
       "&ew_start=1&ew_end=53&ey_start=2024&ey_end=2024")
YEAR = 2024
rng = np.random.default_rng(20261118)

p = pd.read_parquet(PANEL, columns=["unit_id", "country", "week_start", "year", "cases", "observed", "zero_filled", "flag_gap"])
p = p[(p.country == "BRAZIL") & (p.year == YEAR)].copy()
p["geo"] = p.unit_id.astype(int); p["date"] = pd.to_datetime(p.week_start)
print(f"panel BR {YEAR}: units={p.geo.nunique()} rows={len(p)} weeks={p.date.nunique()} "
      f"{p.date.min().date()}..{p.date.max().date()} zero_filled={p.zero_filled.mean():.3f}")
nobs = p.groupby("geo")["observed"].sum()
big = {3550308: "Sao Paulo", 3304557: "Rio de Janeiro", 3106200: "Belo Horizonte", 2927408: "Salvador",
       2304400: "Fortaleza", 5300108: "Brasilia", 1302603: "Manaus", 4106902: "Curitiba",
       2611606: "Recife", 5208707: "Goiania"}
absent = sorted(set(nobs[nobs == 0].index) - set(big))
part = sorted(set(nobs[(nobs > 3) & (nobs < 45)].index) - set(big))
pick_a = [int(g) for g in rng.choice(absent, 15, replace=False)]
pick_b = [int(g) for g in rng.choice(sorted(set(part) - set(pick_a)), 15, replace=False)]
rest = sorted(set(nobs.index) - set(pick_a) - set(pick_b) - set(big))
pick_d = [int(g) for g in rng.choice(rest, 20, replace=False)]
groups = {g: "a_absent24" for g in pick_a} | {g: "b_partial24" for g in pick_b} \
    | {g: "c_large" for g in big} | {g: "d_random" for g in pick_d}
print(f"absent24={len(absent)} partial24={len(part)} sampled={len(groups)}")

manifest = f"{RAW}/manifest.tsv"
if not os.path.exists(manifest):
    open(manifest, "w").write("file\turl\tretrieved_utc\tsha256\tbytes\tdata_rows\tgroup\n")
frames = []
for g, grp in groups.items():
    fn = f"{RAW}/alertcity_{g}_{YEAR}.csv"
    if not os.path.exists(fn):
        url = API.format(g=g); raw = None
        for attempt in range(5):
            try:
                raw = urllib.request.urlopen(url, timeout=90).read()
                pd.read_csv(io.BytesIO(raw), usecols=["data_iniSE", "SE", "casos", "casprov"]); break
            except Exception as e:
                raw = None; print("retry", g, attempt, e); time.sleep(5 * 2 ** attempt)
        if raw is None:
            raise RuntimeError(f"failed {g}")
        open(fn, "wb").write(raw)
        nrows = len(pd.read_csv(io.BytesIO(raw)))
        ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        with open(manifest, "a") as f:
            f.write(f"{os.path.basename(fn)}\t{url}\t{ts}\t{hashlib.sha256(raw).hexdigest()}\t{len(raw)}\t{nrows}\t{grp}\n")
        time.sleep(1.5)
    x = pd.read_csv(fn)[["data_iniSE", "SE", "casos", "casprov"]].assign(geo=g, group=grp)
    frames.append(x)

idg = pd.concat(frames)
idg["date"] = pd.to_datetime(idg.data_iniSE)
assert (idg.date.dt.day_of_week == 6).all(), "InfoDengue weeks not Sunday-start"
assert (idg.SE // 100 == YEAR).all()
assert not idg.duplicated(["geo", "date"]).any()
m = p[p.geo.isin(groups)][["geo", "date", "cases", "observed", "zero_filled", "flag_gap"]].merge(
    idg[["geo", "date", "SE", "casos", "casprov", "group"]], on=["geo", "date"], how="left", indicator=True)
print("panel rows without an InfoDengue week:", (m._merge == "left_only").sum(),
      "| InfoDengue weeks not in panel:", len(idg) - (m._merge == "both").sum())
m = m[m._merge == "both"].drop(columns="_merge")
m.to_csv(f"{OUT}/brazil_infodengue_2024_merged.csv", index=False)

def summ(s, label):
    a, pr = s[s["zero_filled"]], s[s["observed"]]
    r = dict(group=label, munis=s.geo.nunique(), weeks_absent=len(a),
             absent_casprov_gt0=int((a.casprov > 0).sum()), absent_share_gt0=(a.casprov > 0).mean() if len(a) else np.nan,
             absent_casprov_max=a.casprov.max() if len(a) else np.nan, absent_casprov_sum=a.casprov.sum(),
             absent_casos_sum=a.casos.sum(), share_casprov_in_absent=a.casprov.sum() / s.casprov.sum() if s.casprov.sum() else np.nan,
             weeks_present=len(pr))
    if len(pr):
        r |= dict(present_od_sum=pr.cases.sum(), present_casprov_sum=pr.casprov.sum(),
                  ratio_od_casprov=pr.cases.sum() / pr.casprov.sum(), median_diff=(pr.cases - pr.casprov).median(),
                  exact_casprov=(pr.cases == pr.casprov).mean(), within1_casprov=((pr.cases - pr.casprov).abs() <= 1).mean(),
                  exact_casos=(pr.cases == pr.casos).mean(), corr_casprov=pr.cases.corr(pr.casprov))
    return r

rows = [summ(s, g) for g, s in m.groupby("group")] + [summ(m, "all")]
S = pd.DataFrame(rows); S.to_csv(f"{OUT}/brazil_infodengue_2024_summary.csv", index=False)
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
print(S.round(4).to_string())
a = m[m["zero_filled"] & (m.casprov > 0)]
print("absent weeks with casprov>0, distribution of casprov:", a.casprov.value_counts().sort_index().to_dict())
print(a.groupby("group").agg(n=("casprov", "size"), munis=("geo", "nunique"), casprov=("casprov", "sum")).to_string())
print(a.sort_values("casprov", ascending=False).head(10)[["geo", "group", "date", "casos", "casprov"]].to_string())
# by quarter (late-2024 revisions are most likely)
m["q"] = m.date.dt.quarter.where(m.date.dt.year == YEAR, 1)
print(m[m["zero_filled"]].groupby("q").agg(weeks=("casprov", "size"), gt0=("casprov", lambda v: (v > 0).mean()), s=("casprov", "sum")).to_string())
# observed weeks that are zero in OD
print("observed weeks with OD==0:", int((m["observed"] & (m.cases == 0)).sum()), "| observed with casprov==0:", int((m["observed"] & (m.casprov == 0)).sum()))

# ---------------------------------------------------------------------------
# Supplement: Espirito Santo. OpenDengue V1.3.1 has 0 ES cases after 2020-12-20 (all 78 municipalities
# zero-filled 2021-2024), and the 2024 sample above found Marataizes (ES) with 562 probable cases.
# Pull every ES panel municipality for epi-years 2020-2024 to size the gap.
# ---------------------------------------------------------------------------
API_ES = ("https://info.dengue.mat.br/api/alertcity?geocode={g}&disease=dengue&format=csv"
          "&ew_start=1&ew_end=53&ey_start=2020&ey_end=2024")
pall = pd.read_parquet(PANEL, columns=["unit_id", "country", "adm1", "week_start", "year", "cases", "observed", "zero_filled"])
es = pall[(pall.country == "BRAZIL") & (pall.adm1 == "ESPIRITO SANTO") & (pall.year >= 2020)].copy()
es["geo"] = es.unit_id.astype(int); es["date"] = pd.to_datetime(es.week_start)
fr = []
for g in sorted(es.geo.unique()):
    fn = f"{RAW}/alertcity_{g}_2020_2024.csv"
    if not os.path.exists(fn):
        url = API_ES.format(g=g); raw = None
        for attempt in range(5):
            try:
                raw = urllib.request.urlopen(url, timeout=90).read()
                pd.read_csv(io.BytesIO(raw), usecols=["data_iniSE", "SE", "casos", "casprov"]); break
            except Exception as e:
                raw = None; print("retry", g, attempt, e); time.sleep(5 * 2 ** attempt)
        if raw is None:
            raise RuntimeError(f"failed {g}")
        open(fn, "wb").write(raw)
        ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        with open(manifest, "a") as f:
            f.write(f"{os.path.basename(fn)}\t{url}\t{ts}\t{hashlib.sha256(raw).hexdigest()}\t{len(raw)}\t"
                    f"{len(pd.read_csv(io.BytesIO(raw)))}\te_espirito_santo\n")
        time.sleep(1.5)
    fr.append(pd.read_csv(fn)[["data_iniSE", "SE", "casos", "casprov"]].assign(geo=g))
ie = pd.concat(fr); ie["date"] = pd.to_datetime(ie.data_iniSE)
me = es.merge(ie, on=["geo", "date"], how="left")
print("ES panel weeks without InfoDengue row:", int(me.casprov.isna().sum()))
me.to_csv(f"{OUT}/brazil_infodengue_es_2020_2024_merged.csv", index=False)
E = me.groupby("year").agg(munis=("geo", "nunique"), weeks=("geo", "size"), zero_filled_share=("zero_filled", "mean"),
                           od_cases=("cases", "sum"), casprov=("casprov", "sum"), casos=("casos", "sum"),
                           zf_weeks_casprov_gt0=("casprov", lambda v: int((v[me.loc[v.index, "zero_filled"]] > 0).sum())),
                           zf_casprov=("casprov", lambda v: v[me.loc[v.index, "zero_filled"]].sum())).reset_index()
br = pall[(pall.country == "BRAZIL") & (pall.year >= 2020)]
E = E.merge(br.groupby("year").agg(br_od_cases=("cases", "sum"), br_rows=("cases", "size"),
                                   br_zf_rows=("zero_filled", "sum")).reset_index(), on="year")
E["es_share_of_br_rows"] = E.weeks / E.br_rows
E["es_share_of_br_zf_rows"] = (E.weeks * E.zero_filled_share) / E.br_zf_rows
E["casprov_vs_br_od"] = E.casprov / E.br_od_cases
E.to_csv(f"{OUT}/brazil_infodengue_es_2020_2024_summary.csv", index=False)
print(E.round(4).to_string())
z = me[me["zero_filled"] & (me.year == 2024)]
print("ES 2024 zero-filled unit-weeks:", len(z), "with casprov>0:", int((z.casprov > 0).sum()),
      "share:", round((z.casprov > 0).mean(), 3), "munis with any:", z[z.casprov > 0].geo.nunique(), "/", z.geo.nunique())
# 2024 random-sample estimate excluding ES
mx = m[(m.geo // 100000 != 32) & m["zero_filled"]]
print("2024 sample excl. ES: absent weeks", len(mx), "casprov>0", int((mx.casprov > 0).sum()),
      "share", round((mx.casprov > 0).mean(), 4), "max", mx.casprov.max(), "sum", mx.casprov.sum())
