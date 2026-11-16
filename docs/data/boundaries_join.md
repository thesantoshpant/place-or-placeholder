# OpenDengue weekly Admin2 units: boundary join

Build: `scripts/data/download_boundaries.sh`, then `scripts/data/build_unit_boundaries.py`. Output: `data/interim/boundaries/opendengue_units_v1.parquet` (GeoParquet, EPSG:4326, 6,990 rows). Audits: `outputs/data_audit/boundary_join_<country>.csv`. Manifest: `manifests/boundaries.tsv`. Fixes: `configs/boundary_name_fixes.csv`.

Units: Temporal extract, weekly Admin2 rows. `unit_id` is the IBGE code (Brazil) or `COUNTRY|ADM1|ADM2`. FAO_GAUL_code is not used.

## Sources and licences
| Country | Source | Licence |
|---|---|---|
| Brazil | IBGE malha municipal 2022, `BR_Municipios_2022` (`CD_MUN`) | IBGE open data, attribution |
| Colombia | geoBoundaries gbOpen COL ADM2 (DANE MGN, 2020), ADM1 for departments | CC BY 4.0 (ADM1: ODbL 1.0) |
| Peru | geoBoundaries gbOpen PER ADM2 (IGN/OCHA, provinces) | CC BY 3.0 IGO (ADM1: public domain) |
| Taiwan | geoBoundaries gbOpen TWN ADM2 (OpenStreetMap/Wambacher, 2017, 368 townships) | **CC BY-SA 2.0** (ADM1: ODbL 1.0) |

The official MOI township file (data.gov.tw 7441) returned **HTTP 403** from the server, and GADM 4.1 TWN stops at county level. No provider publishes checksums. geoBoundaries ADM2 polygons get their ADM1 from the ADM1 polygon containing their representative point.

## Method
- **Brazil:** code join (`IBGE_code` is 7 digits for every row).
- **Other countries:** matching runs within the ADM1 pool, which is set by a crosswalk in the code (e.g. VALLE→Valle del Cauca, LIMA→Lima + Municipalidad Metropolitana de Lima, KAOHSIUNG CITY→Kaohsiung). The steps run in this order:
  1. manual fix;
  2. Taiwan only: `cdc_crosswalk`;
  3. exact match (uppercase, accents stripped);
  4. normalised match (punctuation, Spanish stopwords, `(CD)` and Taiwan suffixes removed; parenthetical variants; Tongyong→Hanyu folding such as SI→XI, IOU→IU, UEI→UI);
  5. fuzzy match (rapidfuzz, ≥85, or ≥90 for Taiwan, assigned one-to-one greedily).
- **Taiwan `cdc_crosswalk`:** the unit is mapped to its Chinese CDC township name via the read-only `outputs/data_audit/taiwan_township_crosswalk_inferred.csv`. That name is matched to the polygon either directly (some OSM names are Chinese) or through pypinyin with folding.

## Match rates (cases = weekly Admin2 cases, 2014+)
| Country | Units | Matched | Unit % | Cases 2014+ | Case % |
|---|---|---|---|---|---|
| Brazil | 5,517 | 5,517 | 100.00 | 16,708,965 | 100.000 |
| Colombia | 1,071 | 1,070 | 99.91 | 687,419 | 99.994 |
| Peru | 115 | 115 | 100.00 | 578,638 | 100.000 |
| Taiwan | 287 | 285 | 99.30 | 86,360 | 100.000 |

Methods used:
- Colombia: exact 1,005, normalised 30, fuzzy 28, manual 7.
- Peru: exact 113, manual 2.
- Taiwan: cdc_crosswalk 271, manual 6, exact 4, normalised 3, fuzzy 1.

There are 15 manual fixes (7 COL, 2 PER, 6 TWN), plus one documented `NONE` row.

## Unmatched units and many-to-one
- COLOMBIA|CHOCO|BELEN DE BAJIRA: 40 cases 2014+. Its municipality status was annulled, so it is not in DANE MGN 2020; the area lies within Riosucio/Carmen del Darién. It is left unmatched rather than double-assigned.
- TAIWAN|TAINAN CITY|OTHER and TAIWAN|HSINCHU CITY|OTHER: 0 cases 2014+ (16 and 1 in all years). These are non-spatial "other" buckets.

**Many-to-one:** none. No polygon is matched to more than one OpenDengue unit.

## Checks
- All 6,987 non-empty geometries are valid. The raw files contained no invalid geometries; `make_valid` is applied if any appear.
- Unmatched units have empty geometry and NaN area and centroid.
- `area_km2` and the centroid are computed in EPSG:6933 (equal-area). The centroid is then reprojected to 4326.

## Caveats
- **Taiwan geometry is OSM 2017, not the official MOI file, and is CC BY-SA 2.0 (share-alike).** If the MOI file can be fetched (e.g. from a Taiwan network), swap it in; it would also allow a direct Chinese-name join.
  - OSM mislabels Tainan 新營 Xinying as "Xiaying", and the real 下營 is "Siaying". Both are fixed manually and confirmed by location.
- The Taiwan crosswalk was inferred from case counts. It reproduces all OpenDengue totals, but it is not an official code list.
- Boundary vintages differ from the reporting periods: Brazil 2022, Colombia 2020, Peru 2020, Taiwan 2017. Pre-2014 Taiwan county mergers are handled implicitly, because OpenDengue already uses post-2014 municipality names.
