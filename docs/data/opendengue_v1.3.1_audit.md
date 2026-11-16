# OpenDengue V1.3.1 — weekly sub-national audit (Paper 1)

Script: `scripts/data/audit_opendengue.py` · Outputs: `outputs/data_audit/*.csv` · Run 2026-11-15.

## Plan vs measured (best weekly sub-national level)

| Country | Plan units | Measured units (level) | Plan years | Weekly years present | Grid completeness* | Flag |
|---|---|---|---|---|---|---|
| Brazil | 5,517 | 5,517 (Admin2) | 2013–2024 | 2013–2024 (2013 = 1 week only) | 59.9% | OK; 2013 unusable, 2022–23 rows drop to ~27% |
| Colombia | 1,071 | 1,071 (Admin2) | 2013–2022 | 2006–2022 | 22.3% | OK; zero weeks not reported |
| Peru | 115 | 115 (Admin2) | 2013–2023 | 2000–2023 | 21.3% (Spatial) / 21.5% (Temporal) | Count matches, but only ~115 of ~196 provinces; zeros not reported |
| Taiwan | 287 | 287 (Admin2 townships) | 2013–2024 | 1997–2024, **2021 missing** | 3.7% | **Mismatch on usability**: very sparse |
| Mexico (fallback) | – | 32 (**Admin1 only**) | – | 2002–07, 2012–13, 2017–22 | 90.7% | No Admin2; gaps 2008–11, 2014–16 |
| Thailand (fallback) | – | **no weekly data** (Admin1 Month only, 78 units, 1993–2022) | – | none | – | Not usable for weekly |

*unique unit-weeks / (units × distinct weeks). All weekly rows are 7-day spans starting Sunday (100%); no duplicate (unit, week) keys in any country/extract.

## S_res × T_res (Spatial extract; Temporal identical unless noted)

| Country | Combinations (units, years) |
|---|---|
| Brazil | Admin2 Week (5,517; 2013–24); Admin2 Month (5,054; 2001–13); Admin1 Month (3; 1993–2000); Admin0 Year |
| Colombia | Admin2 Week (1,071; 2006–22); Admin1 Week (37; 2001–19); Admin2/Admin1 Year (2003–12); Admin0 Week 2023–24 |
| Peru | Admin2 Week (115; 2000–23); **Temporal only:** Admin1 Week (25; 2006–13); Admin0 Week 2023–24 (Spatial) / 2013–24 (Temporal) |
| Taiwan | Admin2 Week (287; 1997–2024); Admin0 Week/Month/Year |
| Mexico | Admin1 Week (32; 2002–22); Admin0 Week/Year |
| Thailand | Admin1 Month (78; 1993–2022); Admin0 Month/Year |

Full table: `crosstab_sres_tres.csv`; per-year breakdown: `years_by_sres_tres.csv`.

## Missingness: absent row ≈ zero cases (except Brazil)

| Country | Share of weekly rows with 0 cases | Interpretation |
|---|---|---|
| Brazil | 63% | Zeros reported explicitly 2014–2021; 2022–2024 row coverage falls to 27–40% → zeros (or units) likely dropped; must zero-fill and verify |
| Colombia | 0.4% | Rows only for case-positive weeks → zero-fill needed |
| Peru | 0% (min 1) | Case-positive only; 115 = provinces that ever reported a case |
| Taiwan | 0% (min 1) | Case-positive only; units appear/vanish year to year |
| Mexico | 34% | Zeros reported |

Per-year units, weeks, drop-outs and new entrants: `weekly_per_year.csv`. Units entering/leaving each year are large (e.g. Brazil −905 in 2017, +1,055 in 2022; Taiwan 234 units in 2015 vs 4 in 2017), consistent with case-only reporting rather than true admin changes.

## Taiwan

Units are Admin2 townships/districts (e.g. `KAOHSIUNG CITY|ZIGUAN DIST.`, `PINGTUNG COUNTY|JIURU TOWNSHIP`) across 22 Admin1 cities/counties (Kaohsiung 38, Tainan 37, Pingtung 33…). Taiwan has ~368 townships; **287 = townships with ≥1 reported case in any week 1997–2024**. Only 7,673 unit-weeks exist (3.7% of the grid); outside outbreak years (2002, 2014–15, 2023) most years have <100 unit-weeks, and 2021 has none. List: `taiwan_units.csv`.

## Identifiers (weekly sub-national rows)

| Country | units | adm_2 name alone unique | FAO_GAUL unique codes | GAUL codes shared by >1 unit | IBGE | RNE_iso_code |
|---|---|---|---|---|---|---|
| Brazil | 5,517 | 5,239 (no) | 5,456 | 54 | **5,517, 1:1, 100% non-null** | Admin1-level (27) |
| Colombia | 1,071 | 989 (no) | 1,012 | 53 | – | Admin1-level (32) |
| Peru | 115 | 115 | 113 | 2 | – | Admin1-level (22) |
| Taiwan | 287 | 274 (no) | **2** | 2 (city vs county placeholder) | – | Admin1-level (22) |
| Mexico | 32 | n/a | 32 | 0 | – | 32 |

All codes 100% non-null where present; no unit maps to >1 code. `full_name` (= adm_0, adm_1, adm_2) is 1:1 with units everywhere. **Recommended key:** `IBGE_code` for Brazil; `adm_1_name|adm_2_name` (or `full_name`) elsewhere. GAUL is not a safe key (shared codes; Taiwan's are not township codes). Joining to covariates/shapefiles will need a name crosswalk outside Brazil.

## Spatial vs Temporal extract

| Country | Weekly sub-national unit-weeks Spatial / Temporal | Only in Temporal | Value conflicts |
|---|---|---|---|
| Brazil | 1,895,538 / 1,895,538 | 0 | 0 |
| Colombia | 199,458 / 199,458 | 0 | 0 |
| Peru | 30,685 / 30,991 | 306 (+ Admin1 Week 2006–13) | 0 |
| Taiwan | 7,673 / 7,673 | 0 | 0 |
| Mexico | 17,492 / 17,492 | 0 | 0 |

**Use the Temporal extract**: for weekly district data it is a strict superset of Spatial (adds 306 Peru unit-weeks and Peru Admin1 weekly), with no conflicting values. It also carries national weekly series (2013–24) usable for aggregation checks. Combining the two adds nothing.

## Risks for Paper 1

1. Zero-fill assumption: absent unit-weeks must be treated as 0 for COL/PER/TWN (and Brazil 2022–24) — this is an inference, not documented in the data; confirm against OpenDengue docs.
2. Taiwan is too sparse for a 287-unit weekly panel (3.7% non-zero, 2021 missing); consider aggregating to Admin1 or restricting to the southern cities.
3. Brazil 2013 has one week; effective window 2014–2024.
4. Fallbacks: Mexico is Admin1-only with 7 missing years; Thailand has no weekly data. Neither replaces a district-level country.
5. Mixed case definitions (Brazil Probable, Colombia/Taiwan Total, Peru Probable+confirmed).

## Reproduce

```bash
ssh -o BatchMode=yes -J jumper@math.knox.edu -l spant epyc2.knoxds.org
cd /net/home/spant/0-100/group-research/place-or-placeholder && source env.sh
X=data/raw/opendengue/V1.3.1/extracted
python scripts/data/audit_opendengue.py \
  --spatial  $X/Spatial_extract_V1_3_1/Spatial_extract_V1_3_1.csv \
  --temporal $X/Temporal_extract_V1_3_1/Temporal_extract_V1_3_1.csv \
  --out outputs/data_audit
```
Outputs: `crosstab_sres_tres.csv`, `years_by_sres_tres.csv`, `weekly_summary.csv`, `weekly_per_year.csv`, `identifiers.csv`, `duplicate_examples.csv` (empty), `taiwan_units.csv`, `spatial_vs_temporal.csv`, `plan_vs_measured.csv`. Zero-share figures came from a one-off check (`dengue_total == 0` on weekly Admin1/2 rows).
