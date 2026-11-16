#!/usr/bin/env python
"""Attach one polygon to every OpenDengue V1.3.1 weekly Admin2 unit (BRA, COL, PER, TWN).

Units: Temporal extract rows with T_res == "Week" and S_res == "Admin2".
  BRA: joined on 7-digit IBGE code -> IBGE malha municipal 2022 (CD_MUN).
  COL/PER/TWN: name match within ADM1 against geoBoundaries gbOpen ADM2. geoBoundaries
  ADM2 files carry no ADM1 name, so each ADM2 polygon gets its ADM1 from the gbOpen
  ADM1 polygon containing its representative point.
Match cascade (per country, within ADM1): manual (configs/boundary_name_fixes.csv) ->
exact (uppercase, accent-stripped) -> normalised (punctuation, suffixes, romanisation) ->
fuzzy (rapidfuzz on normalised names, >= --fuzzy-min, one-to-one greedy).
FAO_GAUL_code is never used (not unique per unit).

Outputs:
  <out-parquet>  GeoParquet EPSG:4326, one row per OpenDengue unit (unmatched -> empty geometry)
  <audit-dir>/boundary_join_<country>.csv  all units incl. unmatched, with 2014+ weekly cases

Usage (from project root, env sourced):
  python scripts/data/build_unit_boundaries.py \
    --temporal data/raw/opendengue/V1.3.1/extracted/Temporal_extract_V1_3_1/Temporal_extract_V1_3_1.csv \
    --boundaries data/raw/boundaries --fixes configs/boundary_name_fixes.csv \
    --out-parquet data/interim/boundaries/opendengue_units_v1.parquet --audit-dir outputs/data_audit
"""
import argparse
import re
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from rapidfuzz import fuzz
from shapely.validation import make_valid
from unidecode import unidecode

COUNTRIES = ["BRAZIL", "COLOMBIA", "PERU", "TAIWAN"]
ISO = {"COLOMBIA": "COL", "PERU": "PER", "TAIWAN": "TWN"}
EQUAL_AREA = "EPSG:6933"

# OpenDengue ADM1 name -> geoBoundaries ADM1 shapeName(s) (pool of candidate ADM2 polygons).
# Only entries that differ after accent stripping are listed.
ADM1_XWALK = {
    "COLOMBIA": {
        "BOGOTA": ["Bogota Capital District", "Cundinamarca"],
        "GUAJIRA": ["La Guajira"],
        "NORTE SANTANDER": ["Norte de Santander"],
        "SAN ANDRES": ["Archipiélago de San Andrés, Providencia y Santa Catalina"],
        "VALLE": ["Valle del Cauca"],
    },
    "PERU": {
        "LIMA": ["Lima", "Municipalidad Metropolitana de Lima"],
        "CALLAO": ["El Callao"],
    },
    "TAIWAN": {  # OD "<NAME> CITY|COUNTY" -> gb names
        "KINMEN COUNTY": ["Kinmen"], "LIENCHIANG COUNTY": ["Matsu Islands"],
        "PENGHU COUNTY": ["Penghu"], "CHIAYI CITY": ["Chiayi"], "HSINCHU CITY": ["Hsinchu"],
        "KEELUNG CITY": ["Keelung"], "TAICHUNG CITY": ["Taichung"], "TAOYUAN CITY": ["Taoyuan"],
        "NEW TAIPEI CITY": ["New Taipei"], "TAINAN CITY": ["Tainan"], "TAIPEI CITY": ["Taipei"],
        "KAOHSIUNG CITY": ["Kaohsiung"],
    },
}

TW_SUFFIX = r"\b(DIST|DISTRICT|TOWNSHIP|TOWN|CITY|AREA)\b"
# Tongyong/Wade-Giles -> Hanyu-ish phonetic folding, applied to both sides (Taiwan only).
TW_FOLD = [("EASTERN", "EAST"), ("WESTERN", "WEST"), ("IOU", "IU"), ("UEI", "UI"), ("JH", "ZH"), ("SI", "XI"), ("CI", "QI"), ("FONG", "FENG"), ("WUN", "WEN"),
           ("JYU", "JU"), ("SYU", "XU"), ("CYU", "QU"), ("ZIH", "ZI")]
ES_STOP = r"\b(DE|DEL|LA|LAS|LOS|EL|Y)\b"
CJK = re.compile(r"[\u4e00-\u9fff]")
ZH_DIR = {"東": "EAST", "西": "WEST", "南": "SOUTH", "北": "NORTH", "中": "CENTRAL", "中西": "WEST CENTRAL"}


def demojibake(s):
    s = str(s)
    if "Ã" in s:
        try:
            s = s.encode("latin1").decode("utf8")
        except UnicodeError:
            pass
    return s


def zh_key(s):
    """Chinese township name (e.g. 北斗鎮, 東區, '大埤鄉 (Dapi)') -> folded pinyin key comparable with norm()."""
    from pypinyin import lazy_pinyin
    s = re.sub(r"\s*\(.*\)", "", str(s)).strip()
    s = re.sub(r"[市鎮鄉區]$", "", s)
    s = ZH_DIR.get(s, s)
    if CJK.search(s):
        s = "".join(lazy_pinyin(s)).replace("v", "u")
    return norm(s, "TAIWAN")


def basic(s):
    s = unidecode(demojibake(s)).upper()
    s = re.sub(r"\((CD|COR\.? ?DEPARTAMENTAL)\)", " ", s)
    return re.sub(r"\s+", " ", re.sub(r"[^A-Z0-9 ]", " ", s)).strip()


def norm(s, country):
    if country == "TAIWAN" and CJK.search(str(s)):
        return zh_key(s)
    s = basic(s)
    if country == "TAIWAN":
        s = re.sub(TW_SUFFIX, " ", s)
        s = re.sub(r"\s+", "", s)  # "WEST CENTRAL" == "WESTCENTRAL"
        for a, b in TW_FOLD:
            s = s.replace(a, b)
    else:
        s = re.sub(ES_STOP, " ", s)
        s = re.sub(r"\b(DC|D C|DISTRITO CAPITAL|CAPITAL DISTRICT)\b", " ", s)
        s = re.sub(r"\s+", "", s)
    return s


def load_units(path):
    d = pd.read_csv(path, keep_default_na=False, dtype=str,
                    usecols=["adm_0_name", "adm_1_name", "adm_2_name", "IBGE_code",
                             "Year", "dengue_total", "T_res", "S_res"])
    d = d[(d.T_res == "Week") & (d.S_res == "Admin2") & d.adm_0_name.isin(COUNTRIES)].copy()
    d["cases"] = pd.to_numeric(d.dengue_total.replace("NA", np.nan))
    d["y"] = pd.to_numeric(d.Year, errors="coerce")
    d["unit_id"] = np.where(d.adm_0_name == "BRAZIL", d.IBGE_code,
                            d.adm_0_name + "|" + d.adm_1_name + "|" + d.adm_2_name)
    g = d.groupby("unit_id")
    u = g.agg(country=("adm_0_name", "first"), adm1=("adm_1_name", "first"),
              adm2=("adm_2_name", "first"), ibge=("IBGE_code", "first")).reset_index()
    u["cases_2014plus"] = d[d.y >= 2014].groupby("unit_id").cases.sum().reindex(u.unit_id).fillna(0).values
    u["cases_all"] = g.cases.sum().reindex(u.unit_id).values
    return u


def fix_geoms(gdf):
    bad = ~gdf.geometry.is_valid
    if bad.any():
        gdf.loc[bad, "geometry"] = gdf.loc[bad, "geometry"].apply(make_valid)
    # keep polygonal parts only
    gdf["geometry"] = gdf.geometry.apply(
        lambda g: g if g.geom_type in ("Polygon", "MultiPolygon")
        else gpd.GeoSeries([g]).explode().pipe(lambda s: s[s.geom_type.isin(["Polygon", "MultiPolygon"])]).union_all())
    return gdf, int(bad.sum())


def load_brazil(bdir):
    z = next((bdir / "ibge").glob("BR_Municipios_2022*.zip"))
    g = gpd.read_file(f"/vsizip/{z}").to_crs(4326)
    g["boundary_id"] = g.CD_MUN.astype(str)
    g["tname"] = g.NM_MUN
    g["tadm1"] = g.SIGLA_UF
    g["boundary_source"] = "IBGE malha municipal 2022"
    return g[["boundary_id", "tname", "tadm1", "boundary_source", "geometry"]]


def load_gb(bdir, iso):
    a2 = gpd.read_file(bdir / "geoboundaries" / f"geoBoundaries-{iso}-ADM2.geojson").to_crs(4326)
    a1 = gpd.read_file(bdir / "geoboundaries" / f"geoBoundaries-{iso}-ADM1.geojson").to_crs(4326)
    a2, _ = fix_geoms(a2)
    a1, _ = fix_geoms(a1)
    rp = gpd.GeoDataFrame(a2[["shapeID"]], geometry=a2.representative_point(), crs=4326)
    j = gpd.sjoin(rp, a1[["shapeName", "geometry"]], how="left", predicate="within")
    j = j[~j.index.duplicated()]
    miss = j.shapeName.isna()
    if miss.any():  # coastal slivers: nearest ADM1
        nn = gpd.sjoin_nearest(rp[miss].to_crs(EQUAL_AREA), a1[["shapeName", "geometry"]].to_crs(EQUAL_AREA))
        j.loc[miss, "shapeName"] = nn[~nn.index.duplicated()].shapeName
    a2["tadm1"] = j.shapeName.values
    a2["boundary_id"] = a2.shapeID
    a2["tname"] = a2.shapeName
    a2["boundary_source"] = f"geoBoundaries gbOpen {iso} ADM2"
    return a2[["boundary_id", "tname", "tadm1", "boundary_source", "geometry"]]


def variants(s, country):
    s = str(s)
    v = {norm(s, country), norm(re.sub(r"\(.*?\)", " ", s), country)}
    v |= {norm(x, country) for x in re.findall(r"\((.*?)\)", s)}
    return {x for x in v if len(x) >= 3}


def match_names(units, tgt, country, fixes, fuzzy_min, zh_xwalk=None):
    xw = ADM1_XWALK.get(country, {})
    tgt = tgt.copy()
    tgt["b1"] = tgt.tadm1.map(basic)
    tgt["b2"] = tgt.tname.map(basic)
    tgt["n2"] = tgt.tname.map(lambda s: norm(s, country))
    if zh_xwalk is not None:
        tgt["zk"] = tgt.tname.map(zh_key)
    out = {}
    used = set()
    pools = {}
    for a1 in units.adm1.unique():
        names = [basic(x) for x in xw.get(a1, [a1])]
        pools[a1] = tgt[tgt.b1.isin(names)]
    # manual
    for _, f in fixes[fixes.country == country].iterrows():
        uid = f"{country}|{f.od_adm1}|{f.od_adm2}"
        if uid in set(units.unit_id) and str(f.target_id) not in ("", "nan", "NONE"):
            out[uid] = (f.target_id, "manual", 100.0)
            used.add(f.target_id)
    # Taiwan: OpenDengue unit -> CDC Chinese township (inferred crosswalk) -> polygon, matching the
    # Chinese name directly (geoBoundaries names some townships in Chinese) or its folded pinyin.
    if zh_xwalk is not None:
        for _, u in units.iterrows():
            zh = zh_xwalk.get(u.unit_id)
            if u.unit_id in out or not zh:
                continue
            twn = zh[3:]  # strip 3-char county prefix (台南市, 彰化縣, ...)
            p = pools[u.adm1]
            p = p[~p.boundary_id.isin(used)]
            hit = p[p.tname.str.strip() == twn]
            if len(hit) != 1:
                hit = p[p.zk == zh_key(twn)]
            if len(hit) == 1:
                out[u.unit_id] = (hit.boundary_id.iloc[0], "cdc_crosswalk", 100.0)
                used.add(hit.boundary_id.iloc[0])
    # exact, then normalised
    for method, key, col in [("exact", basic, "b2"), ("normalised", lambda s: norm(s, country), "n2")]:
        for _, u in units.iterrows():
            if u.unit_id in out:
                continue
            p = pools[u.adm1]
            p = p[~p.boundary_id.isin(used)]
            hit = p[p[col] == key(u.adm2)]
            if len(hit) != 1 and method == "normalised":
                hit = p[p[col].isin(variants(u.adm2, country))]
            if len(hit) == 1:
                out[u.unit_id] = (hit.boundary_id.iloc[0], method, 100.0)
                used.add(hit.boundary_id.iloc[0])
    # fuzzy: greedy one-to-one by descending score within ADM1 pool
    cands = []
    for _, u in units.iterrows():
        if u.unit_id in out:
            continue
        vu = variants(u.adm2, country)
        for _, t in pools[u.adm1].iterrows():
            if t.boundary_id in used:
                continue
            sc = max(fuzz.ratio(x, y) for x in vu for y in variants(t.tname, country) | {t.n2})
            if country != "TAIWAN":  # token_set is too permissive for short romanised names
                sc = max(sc, fuzz.token_set_ratio(basic(u.adm2), t.b2))
            if sc >= fuzzy_min:
                cands.append((sc, u.unit_id, t.boundary_id))
    for sc, uid, bid in sorted(cands, reverse=True):
        if uid in out or bid in used:
            continue
        out[uid] = (bid, "fuzzy", round(sc, 1))
        used.add(bid)
    res = units.copy()
    res["boundary_id"] = res.unit_id.map(lambda x: out.get(x, (None,))[0])
    res["match_method"] = res.unit_id.map(lambda x: out.get(x, (None, "unmatched"))[1])
    res["match_score"] = res.unit_id.map(lambda x: out.get(x, (None, None, np.nan))[2])
    return res


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--temporal", required=True)
    ap.add_argument("--boundaries", default="data/raw/boundaries")
    ap.add_argument("--fixes", default="configs/boundary_name_fixes.csv")
    ap.add_argument("--out-parquet", default="data/interim/boundaries/opendengue_units_v1.parquet")
    ap.add_argument("--audit-dir", default="outputs/data_audit")
    ap.add_argument("--fuzzy-min", type=float, default=85.0)
    ap.add_argument("--fuzzy-min-taiwan", type=float, default=90.0)
    ap.add_argument("--tw-crosswalk", default="outputs/data_audit/taiwan_township_crosswalk_inferred.csv",
                    help="OpenDengue unit -> Taiwan CDC Chinese township name (columns unit, town_zh); read-only")
    a = ap.parse_args()
    bdir = Path(a.boundaries)
    units = load_units(a.temporal)
    fixes = pd.read_csv(a.fixes, dtype=str, keep_default_na=False) if Path(a.fixes).exists() else \
        pd.DataFrame(columns=["country", "od_adm1", "od_adm2", "target_id", "note"])
    Path(a.audit_dir).mkdir(parents=True, exist_ok=True)
    parts, summary = [], []
    for c in COUNTRIES:
        u = units[units.country == c].copy()
        if c == "BRAZIL":
            tgt = load_brazil(bdir)
            tgt, nfix = fix_geoms(tgt)
            u["boundary_id"] = u.unit_id.where(u.unit_id.isin(set(tgt.boundary_id)))
            u["match_method"] = np.where(u.boundary_id.notna(), "code", "unmatched")
            u["match_score"] = np.where(u.boundary_id.notna(), 100.0, np.nan)
        else:
            tgt = load_gb(bdir, ISO[c])
            zx = None
            if c == "TAIWAN" and Path(a.tw_crosswalk).exists():
                x = pd.read_csv(a.tw_crosswalk, dtype=str)
                zx = dict(zip("TAIWAN|" + x.unit, x.town_zh))
            u = match_names(u, tgt, c, fixes, a.fuzzy_min_taiwan if c == "TAIWAN" else a.fuzzy_min, zx)
        m = u.merge(tgt.rename(columns={"tname": "boundary_name", "tadm1": "boundary_adm1"}),
                    on="boundary_id", how="left")
        m["n_od_units_on_polygon"] = m.groupby("boundary_id").unit_id.transform("size").where(m.boundary_id.notna())
        audit = m.drop(columns="geometry").sort_values(["match_method", "cases_2014plus"], ascending=[True, False])
        audit.to_csv(Path(a.audit_dir) / f"boundary_join_{c.lower()}.csv", index=False)
        ok = m.boundary_id.notna()
        summary.append(dict(country=c, units=len(m), matched=int(ok.sum()),
                            unit_rate=round(100 * ok.mean(), 2),
                            cases_2014plus=m.cases_2014plus.sum(),
                            case_rate=round(100 * m.loc[ok, "cases_2014plus"].sum() / max(m.cases_2014plus.sum(), 1), 3),
                            many_to_one=int((m.n_od_units_on_polygon > 1).sum()),
                            methods=m.match_method.value_counts().to_dict()))
        parts.append(gpd.GeoDataFrame(m, geometry="geometry", crs=4326))
    g = pd.concat(parts, ignore_index=True)
    g = gpd.GeoDataFrame(g, geometry="geometry", crs=4326)
    ea = g.geometry.to_crs(EQUAL_AREA)
    g["area_km2"] = ea.area / 1e6
    cen = ea.centroid.to_crs(4326)
    g["centroid_lon"], g["centroid_lat"] = cen.x, cen.y
    g.loc[g.boundary_id.isna(), ["area_km2", "centroid_lon", "centroid_lat"]] = np.nan
    cols = ["unit_id", "country", "adm1", "adm2", "boundary_source", "boundary_id", "match_method",
            "match_score", "area_km2", "centroid_lon", "centroid_lat", "geometry"]
    Path(a.out_parquet).parent.mkdir(parents=True, exist_ok=True)
    g[cols].to_parquet(a.out_parquet, index=False)
    s = pd.DataFrame(summary)
    s.to_csv(Path(a.audit_dir) / "boundary_join_summary.csv", index=False)
    print(s.to_string(index=False))


if __name__ == "__main__":
    main()
