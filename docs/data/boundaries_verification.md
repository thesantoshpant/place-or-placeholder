# Boundaries verification (independent, 2026-11-16)

Everything below was re-derived on epyc2 from the provider APIs, the raw files and the parquet. I did not use the manifest's values as evidence.

## Provenance

| File | Source of URL | Re-download sha256 = raw? | Provider count vs file |
|---|---|---|---|
| BR_Municipios_2022.zip | IBGE geoftp `municipio_2022/Brasil/BR/` index (Last-Modified 2023-03-28, 203,627,589 B) | PASS (`9c904fa1…`) | 5,572 features = 5,570 municipalities + Lagoa Mirim (4300001) + Lagoa dos Patos (4300002). PASS |
| COL ADM1 / ADM2 | gB API gjDownloadURL @9469f09, build 2023-12-12 | PASS / PASS | 33/33; 1,122/1,122. PASS |
| PER ADM1 / ADM2 | API: ADM1 @90a1d52 (build 2024-02-21), ADM2 @9469f09 | PASS / PASS | 26/26; 196/196. PASS |
| TWN ADM1 / ADM2 | API @9469f09 | PASS / PASS | 22/22; **API says 369, file has 368** (368 unique shapeIDs). Minor upstream discrepancy; the file is the one the API serves |

All 5,517 OpenDengue Brazil codes are present in `CD_MUN`, and boundary_id = unit_id for every one of them.

## Parquet integrity

| Check | BR | CO | PE | TW |
|---|---|---|---|---|
| Rows = universe (6,990; no set differences, adm names identical) | 5,517 PASS | 1,071 PASS | 115 PASS | 287 PASS |
| Matched / unmatched | 5,517/0 | 1,070/1 (Belén de Bajirá) | 115/0 | 285/2 (Hsinchu City/OTHER, Tainan City/OTHER) |
| EPSG:4326, 0 invalid geometries, no reused boundary_id, every ID in source | PASS | PASS | PASS | PASS |
| Stored area and centroid recomputed (EPSG:6933): max diff 0 | PASS | PASS | PASS | PASS |
| Summed area, km² | 8,445,785 (≈8.5 M) PASS | 1,117,258 (country ≈1.14 M) PASS | 1,040,116 (115 of 196 provinces) PASS | 20,453 (285 of 368 townships) PASS |
| Centroid in polygon or bbox | PASS (6,897 of 6,987 lie inside their polygon; all are inside their bbox) | | | |
| Centroid inside country | WARN: Vitória (3205309), pulled about 120 km offshore by the Trindade islands | PASS | WARN: Putumayo (centroid falls outside its own polygon, at the border) | WARN: Qijin, at 119.51E, pulled off-island by its outlying islands |

Use `representative_point()` rather than the stored centroid for distance work involving these three units.

## Join correctness

I reviewed all 29 fuzzy rows, all 15 manual rows, and a random sample of 40 of the 271 cdc_crosswalk rows (seed 1).

- **Spatial adm1 check (all 6,987 matched units):** each polygon's representative point was placed in an ADM1 (Brazil: IBGE UF). 0 true mismatches. The only flag is PERU/LIMA/LIMA, which falls in gB's separate "Municipalidad Metropolitana de Lima" ADM1. That is OK.
- **Taiwan county:** for every reviewed row, the polygon's ADM1 equals the OpenDengue county. The Xinying/Xiaying swap in `boundary_name_fixes.csv` is correct. The polygon gB labels "Xiaying" is at 23.30N 120.30E, which is Xinying (新營). "Siaying" is at 23.23N 120.25E, which is Xiaying (下營).
- **Name review:** all OK. Examples: Itsmina→Istmina; Santa Martha→Santa Marta; Villarica→Villarrica; Darién (Valle)→Calima; Tiquisio→"Tiquiso"; Puerto Santander (CD)→Santander (Araracuara); Nazca→Nasca; MARAЀON→Marañón; Shuili→Shueli; Zhushan→Chushang; Liuqiu→Xiaoliuqiu; Ludao→Green Island; Donggang→Dongang. Crosswalk rows that carry Chinese names also check out (社頭鄉 Shetou, 員林市 Yuanlin, 新豐鄉 Xinfeng, 田尾鄉 Tianwei, 芳苑鄉 Fangyuan, 苗栗市 Miaoli, 永靖鄉 Yongjing, 和美鎮 Hemei, 大埤鄉 Dapi), as does Namaxia→Namasia.

**SUSPECT matches: none.**

## Maps

`outputs/data_audit/maps/{brazil,colombia,peru,taiwan}_units.png` (1200×1200 px). Polygons are coloured by log10(total cases 2014+ + 1), ADM1 areas with no OpenDengue unit are shown in grey, and unmatched units are listed in a red box.

**Overall verdict: PASS.** The three warnings are about centroids only and do not affect the join.
