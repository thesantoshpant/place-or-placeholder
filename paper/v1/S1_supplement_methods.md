# Supplement S1: Methods details

<!-- Writer B. Sections A-H. Every number carries a src comment. Paths in src comments are repo-relative unless they start with ../audits (laptop, outside the repo). -->

Contents: A. Information available to each model. B. Data sources, processing and verification. C. Features and controls. D. Models, hyperparameters and the fold-internal tuning check. E. Deviations from the original protocol (rows 1–34). F. Inference details, size simulation, supporting and sensitivity analyses. G. EPIFORGE 2020 checklist. H. Glossary.

---

## A. Information available to each model

"Outcomes" means case counts. "Held-out" means the districts scored in a split's test fold. For test year Y the training targets are epidemiological years 2018 to Y − 1.

*Table S1-A1. What each step uses, by split.* <!-- src: ../audits/review_round/R1_timing_leakage.md section 0 (code references there) -->

| Step | S1 new years | S2 held-out states | S3 held-out buffered blocks | S4 held-out random districts | S5 held-out country |
|---|---|---|---|---|---|
| Final model fit | All districts, targets 2018 to Y − 1 | Training districts only | Training districts minus the buffer | Training districts | The other three countries |
| Hyperparameters | Country L1 tuning at 2019 (train 2018, validate 2019), all districts | The same S1 tuning, so held-out districts' 2018–2019 outcomes informed the choice | As S2 | As S2 | Brazil's (Colombia's when Brazil is held out); no held-out-country outcome used |
| C\* selection | All districts, 2019 outcomes | Train on training districts (2018), score held-out districts' 2019 outcomes | As S2, held-out blocks | As S2, held-out districts | Held-out country's 2019 outcomes |
| C1 value | Own mean log(1 + cases) before 2018 | Held-out: distance-weighted mean of the 5 nearest training districts' pre-2018 means. Training: the same, excluding their own state | As S2; training districts exclude neighbours within D | As S2; training districts exclude only themselves | Not defined |
| C3 value | Fixed random other district of the country | Held-out district gets a random training district's series | As S2 | As S2 | Fixed permutation within the held-out country |
| C4/C4s range | Fitted on AlphaEarth 2017–2018 of all districts (covariates only, no outcomes) | As S1 | As S1 | As S1 | Per country, as S1 |
| Buffer D | – | – | Correlogram of 2014–2019 outcomes of all districts, held-out included (pre-test) | – | – |
| Fold construction | – | Admin1 units assigned greedily by district count | k-means on centroids | Random, stratified by Admin1 | – |
| District universe | Districts that ever reported a case, through the end of the data (hindsight) | Same | Same | Same | Same |
| LST screen | Per district and calendar month, median of its own LST over years ≤ 2017 (off in Brazil S1–S4) | Same | Same | Same | Same (on for all countries) |
| Test-time inputs of held-out districts | Own lagged cases, climate, remote sensing, population, AlphaEarth y − 1 | Same (own lagged cases are used) | Same | Same | Same |
| Scoring exclusions | No-polygon districts, incomplete weeks (rule uses ±2 weeks and the same year, i.e. later weeks), Espírito Santo from 2019-12-29 | Same | Same | Same | Same |

**Where held-out outcomes enter.** Held-out districts' outcomes enter in three places, all before the test years: hyperparameter choice in S2–S4 (2018–2019 outcomes), C\* selection in S2–S5 (2019 outcomes) and the S3 buffer distance (2014–2019 outcomes). The district universe uses outcomes from every year. No test-year (≥ 2020) outcome of a held-out district enters any fit. <!-- src: ../audits/review_round/R1_timing_leakage.md section 0 -->

**Look-ahead removed by the origin-year filter (D24).** Yearly inputs are keyed to the target's epidemiological year, and each annual model is trained on labels up to the last week of Y − 1. Rows whose origin falls in Y − 1 therefore saw later information.

*Table S1-A2. Share of scored rows with each look-ahead, identical in every cell.* <!-- src: ../audits/review_round/R1_timing_leakage.md section 1a table -->

| Horizon | Yearly-input look-ahead (first h target weeks of Y) | Training-label look-ahead (first h − 1 weeks) | Maximum weeks of labels after the origin |
|---|---|---|---|
| 1 | 1.91% | 0 | 0 |
| 2 | 3.83% | 1.91% | 1 |
| 3 | 5.74% | 3.83% | 2 |
| 4 | 7.66% | 5.74% | 3 |
| Pooled h 1 and 4 (primary) | 4.79% | 2.87% | |

The filter keeps a row only if the epidemiological year of its origin week (the calendar year of the week's Wednesday) equals the test year. On kept rows, target-keyed and origin-keyed yearly inputs coincide and every training label is dated at or before the origin. In the three within-country Brazilian cells the dropped rows favoured L4 slightly, so the look-ahead did not cancel between models. <!-- src: ../audits/review_round/R1_timing_leakage.md section 1a/1b and "Resolution" -->

*Table S1-A3. Information dated after the origin that the filter does not remove.* <!-- src: ../audits/review_round/R1_timing_leakage.md section 1c; ../audits/review_round/R8_literature.md section 4; docs/research/data_and_tools.md ERA5-Land row -->

| Item | Why it is later than the origin | Models affected | Direction |
|---|---|---|---|
| Case counts | One snapshot of final revised counts; no reporting delay except the delay-2 sensitivity | All | Unknown; flatters all models |
| ERA5-Land | Reaches Earth Engine about 3 months after real time | L2 and above | Shared |
| GHSL population and weights | Product released 2023; epochs 2015, 2020, 2025 (2025 a projection); climate weights use the nearest epoch, so 2023+ weeks use 2025 | L2 and above | Shared |
| AlphaEarth model | Trained on imagery "covering 2017 to present", production model with labels through 2023–2024; annual layers released 30 July 2025 | L4, C3, C5 | Favours embeddings |
| C5 (2023 static embedding) | 2023 imagery used for 2020–2022 targets | C5 only (never selected) | Favours the control |
| District universe | Districts that ever reported a case; 565 enter in 2018 or later (Brazil 507, 111 first in 2024; Peru 28; Taiwan 18, all in 2023; Colombia 12) | All | Shared |
| Incomplete-week exclusion | Rule uses later weeks of the same year | Scoring only | Shared; test-year effect 2 Peruvian department-weeks |

<!-- src for late-entry counts: docs/data/completeness_v1.md "Other exclusion files"; ../audits/review_round/R10_fact_check.md item 2 -->

A late-entry sensitivity (restricting the universe at origin Y to districts first seen before Y) is supported by the code but was not run. <!-- src: ../audits/review_round/R1_timing_leakage.md section 1c last row -->

**S3 buffer geometry.** The buffer uses polygon centroids, while C1, C2 and C4 use representative points. Under representative-point distances, 44 Brazilian and 13 Colombian training district-folds (about 0.23% and 0.38% of training memberships) lie within D of a held-out district; the minimum train–test distance in a fold is 161–218 km in Brazil (D = 225 km) and 122–146 km in Colombia (D = 130 km). <!-- src: ../audits/review_round/R1_timing_leakage.md section 3 -->

---

## B. Data sources, processing and verification

### B1. Sources and licences

*Table S1-B1.* <!-- src: docs/research/data_and_tools.md (OpenDengue, AlphaEarth, ERA5-Land licence rows); docs/data/boundaries_join.md "Sources and licences"; docs/features/remote_sensing.md "Sources and conventions"; docs/data/zero_fill_crosscheck.md -->

| Source | Use | Version / product | Licence as recorded |
|---|---|---|---|
| OpenDengue [@clarke2024opendengue; @opendengue131] | Weekly Admin2 cases | V1.3.1, Temporal extract (release commit 99b6a3e; figshare v5) | CC BY-SA (share-alike applies to redistributed derived data) |
| InfoDengue API [@codeco2018infodengue; @infodengue_api] | Brazil zero-fill validation | `alertcity`, column `casprov` (probable) | Public API |
| Taiwan CDC `Dengue_Daily.csv` [@taiwancdc_dengue_daily] | Taiwan validation and crosswalk | Internet Archive snapshot of 2025-07-29 | Open government data |
| IBGE municipal mesh [@ibge2022malha] | Brazil polygons | 2022 | IBGE open data |
| geoBoundaries gbOpen [@geoboundaries_gbopen] | Colombia, Peru, Taiwan polygons | COL ADM2 (DANE 2020); PER ADM2; TWN ADM2 (OpenStreetMap 2017) | CC BY 4.0; CC BY 3.0 IGO; CC BY-SA 2.0 |
| ERA5-Land daily aggregates [@era5land_ee] | Weekly climate | `ECMWF/ERA5_LAND/DAILY_AGGR` | Copernicus licence |
| MODIS [@mod13q1_ee; @mod11a2_ee] | NDVI; land-surface temperature | MOD13Q1 and MOD11A2, collection 6.1 | Provider terms |
| VIIRS night lights [@viirs_ee] | Night lights | VNL annual V2.1 (2013–2021), V2.2 (2022–2024) | Provider terms |
| GHSL [@ghsl_pop; @ghsl_built] | Population, weights, built-up share | P2023A GHS_POP and GHS_BUILT_S, 100 m | Provider terms |
| AlphaEarth Foundations [@brown2025alphaearth; @aef_dataset] | Embeddings | `GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL`, 64 bands, 10 m | CC BY 4.0 |

<!-- Licences for MODIS, VIIRS and GHSL are not recorded in the repo docs; authors to confirm from the cited catalogue pages. -->

All gridded inputs were fetched from Google Earth Engine [@gorelick2017gee] and reduced to polygons locally with exact coverage fractions [@baston_exactextract]. Downloaded source files were re-checked by a separate verification script before use (checksums against upstream, archive integrity, full parse). The OpenDengue archives matched the GitHub blob hashes of release commit 99b6a3e and the figshare v5 MD5 sums and parsed without error. The boundary files and the 2024 InfoDengue pulls were verified the same way. <!-- src: docs/data/opendengue_v1.3.1_verification.md; docs/data/boundaries_verification.md; docs/data/zero_fill_2024_verification.md section 1 -->

### B2. Weekly district panel

Rows with weekly time resolution and Admin2 spatial resolution were taken from the Temporal extract. All weekly rows are 7-day spans starting on Sunday, and no (district, week) pair is duplicated. The epidemiological year of a week is the calendar year of its Wednesday. Districts are identified by the 7-digit IBGE code in Brazil and by Admin1|Admin2 name elsewhere; FAO GAUL codes are not unique (Taiwan's 287 districts share two codes). <!-- src: docs/data/panel_weekly_v1.md; ../audits/review_round/R10_fact_check.md section B (GAUL codes 5,456 / 1,012 / 113 / 2) -->

*Table S1-B2. Panel after zero-filling.* <!-- src: docs/data/panel_weekly_v1.md "Counts"; docs/data/opendengue_v1.3.1_audit.md (raw rows with 0 cases); ../audits/review_round/R10_fact_check.md items 5a, 5c, 5d and section B (raw row counts) -->

| Country | Districts | Weeks | Panel rows | Source weekly rows | Source rows reporting 0 cases | Panel rows zero-filled (whole window) |
|---|---|---|---|---|---|---|
| Brazil | 5,517 | 574 | 3,166,758 | 1,895,538 | 63% | 40.1% (2014–2021: 29.3%; 2022 on: 69.2%) |
| Colombia | 1,071 | 835 | 894,285 | 199,458 | 0.4% | 77.7% |
| Peru | 115 | 1,252 | 143,980 | 30,991 | 0% | 78.5% |
| Taiwan | 287 | 1,409 | 404,383 | 7,673 | 0% | 98.1% |

District counts are districts that ever reported a case, not administrative totals: Peru's 115 of about 196 provinces and Taiwan's 287 of about 368 townships (those that ever had a locally acquired case). <!-- src: docs/data/zero_fill_crosscheck.md (287 of ~368 townships); docs/data/completeness_v1.md "Peru zero-fill check" (~115 of ~196 provinces ever report) -->

### B3. Boundaries

Brazil was joined by IBGE code to the 2022 municipal mesh. Colombia, Peru and Taiwan were joined by name within Admin1, in the order manual fix, Taiwan CDC crosswalk, exact, normalised and fuzzy match (rapidfuzz ≥ 85, ≥ 90 for Taiwan, one-to-one). <!-- src: docs/data/boundaries_join.md "Method" -->

*Table S1-B3. Boundary join.* <!-- src: docs/data/boundaries_join.md "Match rates" -->

| Country | Districts matched | Cases 2014 on matched | Match methods |
|---|---|---|---|
| Brazil | 5,517 / 5,517 | 100.000% | IBGE code |
| Colombia | 1,070 / 1,071 | 99.994% | exact 1,005, normalised 30, fuzzy 28, manual 7 |
| Peru | 115 / 115 | 100.000% | exact 113, manual 2 |
| Taiwan | 285 / 287 | 100.000% | CDC crosswalk 271, manual 6, exact 4, normalised 3, fuzzy 1 |

The unmatched districts are Belén de Bajirá (Colombia; 40 cases since 2014; its municipality status was annulled) and two non-spatial "other" buckets in Taiwan (no cases since 2014). They are excluded from scoring. The official Taiwan township file returned HTTP 403, so Taiwan polygons are the 2017 OpenStreetMap-derived geoBoundaries file. <!-- src: docs/data/boundaries_join.md "Unmatched units"; docs/data/completeness_v1.md "Other exclusion files" -->

**Taiwan crosswalk.** The OpenDengue-to-CDC township crosswalk was inferred by an assignment that maximises shared weekly cases within each county, so agreement in weekly counts is partly built in and is not an independent validation. Independently of counts, the pinyin of every Chinese township name matches the OpenDengue romanised name for 287 of 287 districts (281 exactly, 5 by close string similarity, 1 checked by hand), and 40 crosswalk rows were reviewed by hand. <!-- src: ../audits/review_round/R1_timing_leakage.md section 4; docs/data/boundaries_verification.md -->

### B4. Zero-fill validation

**Rule.** The district universe is every Admin2 unit in a country's weekly file. Coverage runs from the country's first to last week with any Admin2 row, and a missing district-week is set to 0 and flagged zero-filled. <!-- src: docs/data/panel_weekly_v1.md "Frozen rule" -->

**Brazil vs InfoDengue.** OpenDengue matches InfoDengue's probable count (`casprov`), not its notified count. <!-- src: docs/data/zero_fill_crosscheck.md; docs/data/zero_fill_crosscheck_2024.md -->

| Year | Municipalities sampled | Present weeks: Σ OpenDengue / Σ probable | Absent weeks with ≥ 1 probable case | Maximum in an absent week |
|---|---|---|---|---|
| 2017 | 40 | 1.008 | 0 of 902 | 0 |
| 2019 | 40 | 1.003 | 0 of 573 | 0 |
| 2022 | 40 | 1.020 | 14 of 1,285 (1.1%) | 4 |
| 2023 | 40 | 0.939 | 26 of 1,231 (2.1%) | 8 |
| 2024 (excluding Espírito Santo) | 58 | 0.964 | 25 of 1,658 (1.5%) | 3 |

Weekly correlation was ≥ 0.97 in every year and group (0.999 in 2024). The small present-week differences, larger in later years, are consistent with surveillance revisions after the OpenDengue snapshot. <!-- src: docs/data/zero_fill_crosscheck.md; docs/data/zero_fill_crosscheck_2024.md (60 municipalities incl. 2 ES) -->

**Taiwan vs Taiwan CDC.** OpenDengue's Taiwan series equals locally acquired confirmed cases by onset week and residence township; imported cases are excluded. All 7,673 present township-weeks match exactly, no absent township-week holds a local case, and 2021 had no local cases (12 imported). National weekly totals match exactly in 83.7% of weeks; the rest of the gap is 410 early local cases (1998–2010, 217 of them in 2002) with no residence county, which cannot be assigned to a township. <!-- src: docs/data/zero_fill_crosscheck.md Taiwan section -->

**Colombia and Peru.** Admin2 sums agree with national totals within about 5% in Colombia. In Peru they cover 85–94% of national totals in 2020–2023; with the same case definition, district sums are 0.84–0.94 of department totals (2007–2013) and only 0.4–1.6% of reference cases fall in fully zero-filled department-weeks. Province-level absent weeks could not be checked; Peru is "partially validated". <!-- src: docs/data/completeness_v1.md "Peru zero-fill check", "Recommendation" item 3 -->

### B5. Completeness rule and exclusions

**Rule (pre-stated; primary k = 0.5, sensitivity 0.4 and 0.6).** <!-- src: docs/data/completeness_v1.md "Rule" -->
1. *Country × week* (Brazil, Colombia, Peru; national count ≥ 20): flagged when the Admin2/national ratio is below k × its seasonal reference (median ratio of the previous three years at epidemiological weeks ±2) *and* below k × the same year's median ratio.
2. *Admin1 × week*: flagged when cases fall below k × the smaller of the mean of the two weeks before and the two weeks after (that minimum ≥ 50). If the national series dips the same way, the flag is for sensitivity only.
3. Primary flags at k ≤ 0.5 are excluded from scoring; all others feed sensitivity analyses.

**Flags in the test years.** Brazil, Colombia and Taiwan: none. Peru: Junín 2020-12-27 and Ucayali 2023-07-23 (0.03% of rows, 0.02% of cases). Brazil 8–22 December 2024 carries a sensitivity-only flag (1.1% of Brazilian test rows, 0.4% of cases). Taiwan had no national reference, but its rule-2 check gave 0 flags in 96 evaluable state-weeks. Removing the incomplete-week exclusions restores 16 Peruvian rows and changes no result. <!-- src: docs/data/completeness_v1.md "Flags in the test years", "Recommendation"; docs/results/review/RA_summary.md RA3 -->

**Gap flag in training.** A country-week is gap-flagged when the national count is ≥ 20 and the Admin2/national ratio is below 0.25 × that country-year's ratio of sums. Only one week is flagged (Peru, 2018-08-12); it is dropped from training targets. <!-- src: docs/data/panel_weekly_v1.md "flag_gap"; ../audits/review_round/R1_timing_leakage.md section 0 last row -->

### B6. Espírito Santo false zeros (D34)

OpenDengue V1.3.1 has no source data for Espírito Santo after 2020: Admin2 rows end on 2020-12-27, 63 of the 78 municipalities have their last row on 2019-12-22, and the 15 with 2020 rows report far fewer cases than InfoDengue (7,562 vs 27,077 probable). In 2024 every Espírito Santo week is zero-filled, while InfoDengue shows probable cases in 2,925 of 4,056 of those weeks (72%), 166,407 cases in total. A scan of every Admin1 unit in the four countries found no other structural defect. <!-- src: docs/data/zero_fill_2024_verification.md sections 2–3; docs/data/zero_fill_crosscheck_2024.md ES table -->

**Rule.** Every district whose IBGE code matches `^32\d{5}$` is excluded from scoring for target weeks from 2019-12-29 (epidemiological year 2020) onward, in every Brazilian cell and for all models. This removes 38,766 primary rows per cell (1.41% of Brazilian primary rows) and moves every Brazilian excess gain by at most 0.03 percentage points. The exclusion does not depend on outcomes of other states: the source stopped reporting this state. Models were not refitted, so their 2020–2023 training targets still contain these false zeros (Espírito Santo is 1.9–4.5% of Brazil's zero-filled rows per year). <!-- src: docs/plans/deviations_from_protocol.md row 34; docs/results/review/KIT3_changes.md ES section; docs/data/zero_fill_crosscheck_2024.md ES table -->

### B7. Covariates

**Climate (L2).** ERA5-Land daily aggregates were summed or averaged to the panel's Sunday-start weeks: mean, minimum and maximum 2 m temperature, total precipitation and relative humidity from daily mean temperature and dew point (Magnus formula, capped at 100%). Weights are GHSL population of the nearest epoch, with exact polygon coverage on a 0.01° grid aligned to ERA5-Land's 0.1° grid; ocean cells get zero weight. Weekly grids were fetched with `computePixels` and reduced locally, which agreed with Earth Engine `reduceRegions` to r > 0.999999995 at about 1/20 of the compute (Brazil 1.76 EECU-hours). Twenty-three districts with no ERA5-Land land cell (Brazil 3, Colombia 2, Taiwan 18, mostly islands) use the nearest land cell. <!-- src: docs/features/climate_era5land.md "Definitions" and "Method choice"; ../audits/review_round/R10_fact_check.md section B (23 units) -->

**Remote sensing and population (L3).** <!-- src: docs/features/remote_sensing.md "Sources and conventions", "QA", "Caveats", "v2" -->
- NDVI: MOD13Q1 (16-day, 250 m), SummaryQA ≤ 1, read from about 1 km pyramids (r = 0.998 against native 250 m in a pilot, at about a quarter of the cost).
- Land-surface temperature: MOD11A2 day and night (8-day, 1 km), without the QC mask. A QC-masked version (v2) did not remove the cloud-contaminated cold values and changed Brazilian anomalies (correlation with v1 about 0.85–0.88), so it was rejected. Instead, for Colombia, Peru, Taiwan and every S5 model, an LST value more than 10 °C below the district's calendar-month median over years ≤ 2017 is set to missing (D7). The screen flags day/night: Brazil 0.08%/0.02%, Colombia 0.06%/0.57%, Peru 0.06%/0.18%, Taiwan 0.05%/0.06% of district-months; it is off for Brazil S1–S4. <!-- src: docs/methods/s1_pipeline.md "LST outlier screen" -->
- Month assignment: a composite belongs to the month of its last day, so month m contains no information after month m. Missing district-months are filled from the same month of the previous year only.
- Night lights: VIIRS annual, from 2013 (missing before). Built-up share: GHSL GHS_BUILT_S, interpolated linearly between epochs.
- Population: GHSL GHS_POP, log-linear between epochs, no extrapolation. It exceeds the 2022 Brazilian census by 4–10%, so it is used as a relative scale.
- Remote-sensing extraction used 8.9 EECU-hours in total.

**AlphaEarth (L4).** <!-- src: docs/features/alphaearth_extraction.md "Method"; docs/features/alphaearth_verification.md; ../audits/review_round/R10_fact_check.md items 1b, 3, 4b and section B -->
- Image: the annual mosaic of `GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL` (64 bands A00–A63, 10 m, unit-length pixel vectors), read through the mean pyramid.
- Population-weighted mean at 100 m on the native GHS_POP Mollweide grid, with weight = coverage fraction × GHSL population (negative no-data set to 0, linear interpolation between the 2015, 2020 and 2025 epochs). Only populated blocks are fetched. An unweighted 300 m mean is stored but not used in the primary models.
- In a 10-municipality subset of the Brazilian pilot, 100 m was effectively exact against 10 m (mean cosine 0.99994), while naive 300 m resampling was not (0.993). Fetching blocks with `computePixels` and summing locally matched `reduceRegions` exactly at about 40% of its cost.
- Image years extracted: Brazil 2017–2024, Colombia 2017–2021 and 2023, Peru and Taiwan 2017–2023. Target year y uses image year y − 1.
- District means are not unit-length: the median population-weighted norm is 0.87–0.92 by country (range 0.70–0.98; Brazil median 0.92, range 0.74–0.98). Each mean is renormalised to unit length.
- Fernando de Noronha (Brazil) has no AlphaEarth pixels in 2017–2021 upstream; its embedding inputs are missing for target years 2018–2022 and LightGBM routes them as missing.
- Re-extracting one state-year with a different number of workers gave bitwise-identical sums.

*Table S1-B7. Verification of AlphaEarth district means by a separate script that recomputed sampled district-years with its own Earth Engine code (it did not reuse the extraction code).* <!-- src: docs/features/alphaearth_verification.md; ../audits/review_round/R10_fact_check.md items 3, 4b and section B -->

| Country | Districts covered | District-years recomputed | Minimum cosine, weighted | Minimum cosine, unweighted | Median cosine, neighbours vs random pairs |
|---|---|---|---|---|---|
| Brazil | 5,517 / 5,517 | 33 | 0.9999999987 | 0.9999999969 | 0.973 vs 0.710 |
| Colombia | 1,070 / 1,071 | 33 | 0.9999999982 | 0.9999999975 | 0.926 vs 0.644 |
| Peru | 115 / 115 | 32 | 0.99999999975 | 0.9999999996 | 0.91 vs 0.44 |
| Taiwan | 285 / 287 | 33 | 0.99999998 | 0.99999989 | 0.975 vs 0.88 |

Population sums agree within 0.03%. <!-- src: ../audits/review_round/R10_fact_check.md section B (max 0.027%, Taiwan; Brazil max 0.017%) --> Districts not covered are those without a polygon. Agreement shows that the extraction is reproducible, not that the product is valid.

### B8. Computation

LightGBM 4.7.0 ran on CPU in deterministic mode with row-wise histograms; every pair of compared runs uses the same thread count, seed rule and version. On a checked booster, predictions were bit-identical across 2, 4, 8 and 16 threads. TimesFM ran on one GPU. <!-- src: docs/methods/compute_plan.md lines on determinism; docs/methods/timesfm.md -->

---

## C. Features and controls

*Table S1-C1. Inputs by level (column counts for Brazil).* <!-- src: docs/methods/runner.md "Features"; docs/methods/nohist_arm.md -->

| Level | Block added | Columns | Time alignment |
|---|---|---|---|
| L0 | log(1 + cases) in target week − 52 | 1 | Year before the target |
| L1 | log(1 + cases) at lags 0–11 from the origin (12); target week − 52j and ±1 week, j = 1, 2, 3 (9); sine and cosine of the target's epidemiological week (2) | 23 | Lags end at the origin week |
| L2 | ERA5-Land lags 0–11 of mean temperature, precipitation and humidity (36); 4-, 8- and 12-week rolling means of mean, minimum and maximum temperature, precipitation and humidity (15); population-weighted | 74 | Ends at the origin week |
| L3 | NDVI, day LST and night LST, population-weighted, for the 3 latest complete months (9); night lights and built-up share (2) and log(1 + population) (1) for year y − 1 | 86 | Months ending before the origin month; year before the target's epidemiological year |
| L4 | AlphaEarth population-weighted mean for year y − 1, renormalised (64) | 150 | Year before the target's epidemiological year |
| N3 | L3 without the 21 case-derived columns | 65 | As L3 |
| N4 | L4 without the 21 case-derived columns | 129 | As L4 |

L0–L2 pass a code assertion that they contain no district-specific input. Weekly inputs are read through a function that asserts the source week is at or before the origin; monthly and yearly inputs through one that asserts the source period ends before the limit. <!-- src: docs/methods/runner.md "Adding a feature level" -->

*Table S1-C2. Location controls. Each replaces the AlphaEarth block (L3 + Ck) or is added beside it (L4 + Ck).* <!-- src: docs/methods/controls.md; src/pop/features/controls.py; docs/methods/nohist_arm.md (C6) -->

| Control | Type | Columns | Definition | Where defined |
|---|---|---|---|---|
| C1 | Historical risk | 1 | Mean log(1 + cases) over panel years before 2018 (Brazil 2014–2017), gap-flagged weeks dropped. S1: the district's own value, identical for training and test rows and at every origin. S2–S4: inverse-distance (1/(d + 1 km)) mean of the 5 nearest training districts' values; training districts get a matched leave-out value (S2 excludes their own state, S3 neighbours within D, S4 only themselves) | S1–S4 |
| C2 | Geographic | 82 | Latitude, longitude and 80 orthonormal real spherical harmonics of degree 1–8, no constant term [@russwurm2024location; @klemmer2025satclip] | All |
| C3 | Identifier | 64 | One fixed source map per seed and country, used in every year: district i gets the real year y − 1 AlphaEarth vector of its source district (never itself). S2–S4: each held-out district gets one random training district | All |
| C4 | Geographic | 64 | 64 Gaussian random fields per country, exponential covariance exp(−d/r) in great-circle distance, standardised within country; r fitted to the AlphaEarth semivariogram (Brazil 8,483 km, Colombia 705 km, Peru 148 km, Taiwan 27 km); drawn only on districts with coordinates | All |
| C4s | Geographic | 64 | C4 with r = min(D, fitted range): Brazil 225 km, Colombia 130 km; equal to C4 in Peru and Taiwan, so not a separate candidate there | Brazil, Colombia, S5 |
| C5 | Snapshot | 64 | AlphaEarth 2023 for every target year | All |
| C6 | Identifier | 1 | District ID as one LightGBM categorical input | S1 only |

<!-- src: C4 ranges: ../audits/review_round/R1_timing_leakage.md section 0 (BR 8483, CO 705, PE 148 km); docs/methods/controls.md (C4s rule; PE/TW fitted 148/27 km). Taiwan's fitted range (27 km) is from docs/methods/controls.md. -->

Controls are rebuilt for every split, fold, origin and seed. Districts are located by a polygon representative point. C1 does not change when every row from 2018 on, or every test-district row, is replaced by an extreme value (tested). <!-- src: docs/methods/controls.md "Leakage guarantees" -->

---

## D. Models, hyperparameters and the fold-internal tuning check

**LightGBM.** Quantile objective on log(1 + cases), one booster per quantile (9) and horizon; learning rate 0.05; 400 rounds; feature fraction 0.9; bagging fraction 0.8 every iteration; L2 penalty 1; deterministic, row-wise histograms. Quantiles are back-transformed, clipped at 0 and sorted; a scan of the 77,187,144 stored forecasts found no crossed or missing quantiles (crossing before sorting was not logged). <!-- src: docs/methods/runner.md "Models and tuning"; docs/results/review/RA_summary.md RA7 -->

**Tuning.** Grid: leaves {31, 127} × minimum rows per leaf {100, 1,000}. Criterion: mean pinball loss on log(1 + cases) at quantiles 0.1, 0.5, 0.9 and horizons 1 and 4; train 2018, validate 2019; level L1; seed 0. Choice: Brazil 127/100 (validation 0.07406 vs 0.07428 for 31/100); Colombia, Peru and Taiwan 31/100. One configuration per country is used for every level, control and split. S5 uses Brazil's configuration, or Colombia's when Brazil is held out. The no-history arm uses Brazil's L1 configuration, which was tuned on a model with case history. <!-- src: docs/results/review/RF_summary.md (0.07406/0.07428); docs/methods/split_pipeline.md "Params"; docs/plans/deviations_from_protocol.md "No-history parameters" -->

**Per-level tuning (sensitivity).** Tuning each level separately in Brazil gave L1 and L2 127/100 and L3 and L4 31/100. The gap between the best and second-best validation loss was 0.29% for L1, 0.03% for L2, 0.06% for L3 and 1.36% for L4. On the Brazil S1 test years, the difference between L3 at 31 and at 127 leaves was about eight times the shared-configuration embedding gain pooled over horizons 1 and 4 (6.5–14 times per horizon, primary rows), which motivated one shared configuration (D2); before the origin-year filter the figure was about seven. <!-- src: ../audits/review_round/R10_fact_check.md section B (tuning gaps) and items 6a, 6b (pre-filter, about 7x); primary rows computed from T2_ladder_long.csv BR_S1_perlevel vs BR_S1 L3 and BR_S1 L3 vs L4 (7.7 pooled h{1,4}; 13.7, 7.7, 7.3, 6.5 by horizon) -->

**Taiwan.** At the 2019 tuning origin Taiwan had 95 non-zero training targets (33 townships) and 56 non-zero validation targets (26 townships), so its tuning and C\* choice are nearly uninformative. Taiwan S1 is therefore also run with Brazil's configuration and C\* as a sensitivity analysis. <!-- src: docs/methods/s1_pipeline.md "Pre-flight findings" -->

**Baselines.** L0: the quantile τ is expm1(log1p(y at t − 52) + the τ-quantile of the training errors log1p(y_t) − log1p(y_{t−52})), clipped at 0. Negative binomial: an NB2 regression on raw counts with the L1 inputs and an intercept, fitted by L-BFGS from a Poisson start, with quantiles from the fitted distribution; not tuned. TimesFM 2.5 (checkpoint `google/timesfm-2.5-200m-pytorch`), zero-shot on each Brazilian district's log(1 + cases) history up to the origin (at most 573 weeks), deciles sorted and clipped at 0; Brazil S1 only. <!-- src: docs/methods/runner.md "L0 quantile method", "Models and tuning"; docs/methods/timesfm.md -->

**Fold-internal tuning check.** S2–S4 reuse the country's S1 tuning, which saw held-out districts' 2018–2019 outcomes. We reran the same search within each fold's training districts only (no held-out or buffer district contributes). The reruns over all districts reproduce the stored S1 tuning to every printed digit. <!-- src: docs/results/review/RF_summary.md -->

*Table S1-D1. Fold-internal tuning.* <!-- src: docs/results/review/RF_summary.md table and verdict -->

| Country | Split | Folds choosing the S1 configuration | Validation cost of the S1 configuration vs the fold's best |
|---|---|---|---|
| Colombia | S2 | 5 of 5 | 0 |
| Colombia | S3 | 6 of 6 | 0 |
| Colombia | S4 | 5 of 5 | 0 |
| Brazil | S2 | 1 of 5 | 0.17–0.56% |
| Brazil | S3 | 0 of 5 | 0.29–1.05% |
| Brazil | S4 | 2 of 5 | 0.11–0.26% |

In Colombia the exposure is inert. In Brazil, 12 of 15 folds would have chosen 31 leaves; the S1 configuration costs 0.11–1.05% of fold validation loss (median 0.32%). S1 itself separated the two settings by only 0.29%. The S2–S4 Brazilian cells were not rerun. <!-- src: docs/results/review/RF_summary.md verdict -->

---

## E. Deviations from the original protocol (rows 1–34)

The original protocol is the evaluation plan and its design review of 15 November 2026. Rows 1–10 were committed in d8c7944, the no-history arm was pre-specified in bd3ba50, rows 11–17 were recorded in fcc3c38 and the control fixes of rows 13–15 implemented in 9de7386, all on 16 November 2026 before any spatial-split result had been read. Rows 18–23 were committed in e9df1f1 (16 November, 20:29 CST), about three hours before the first spatial-split result (3ca02d7, 23:21 CST). Rows 24–34 were committed in f107238 (18 November, 02:16 CST) after external review, when the S1, S2, S3 and S5 results and Colombia S4 had been seen; only Brazil S4 and the no-history cells were still running. Brazil, Peru and Taiwan S1 test-year results were seen before rows 2, 8, 9, 11, 12, 16 and 18–22, so S1 is partly unblinded; the baselines (L0–L2, TimesFM) were also looked at on test years during pipeline development. <!-- src: docs/plans/deviations_from_protocol.md header; docs/results/NOTES_FOR_WRITERS.md items 1–3; git log (commit times) -->

| # | Change | Reason | Decided after seeing | Commit |
|---|---|---|---|---|
| 1 | C1 under the temporal split = the district's mean log(1 + cases) over the years before the first training target year (Brazil 2014–2017), identical for training and test rows | The first definition (mean of the training targets) leaked each training row's own target: 2019 WIS 0.263 vs 0.175 for plain L3 | 2019 selection-origin results only | d8c7944 |
| 2 | One LightGBM configuration per country, tuned once on L1 at the 2019 origin, for all levels and controls; per-level tuning becomes a sensitivity analysis | Per-level tuning on a nearly flat grid (validation differences 0.03–1.4%) gave L1/L2 127 leaves and L3/L4 31 leaves; on Brazil S1 test years L3 with 127 leaves beat L3 with 31 at every horizon (Holm p ≤ 0.012), a capacity effect several times the embedding gain (about eight times on the primary rows; Section D) | **Brazil S1 test years** | d8c7944 |
| 3 | S2 = grouped leave-states-out in 5 folds (was one state per fold: 27 in Brazil, 33 in Colombia); Brazil's S3 groups 10 blocks into 5 folds; old versions kept in the code, not run | Compute (the 27-fold S2 was 54% of the total); held-out districts are still in states unseen in training | No | d8c7944 |
| 4 | Spatial splits score horizons 1 and 4 only (S1 keeps 1–4); the random district-week split S0 is dropped; final C\* runs use 1 seed (selection uses 3 seeds for random controls; the protocol said 10); no re-tuning per split | Compute; Brazil S1 selection seed SD about 0.0001 WIS | No | d8c7944 |
| 5 | C1 in S2/S3: training districts get a matched leave-out value (exclude own state in S2, neighbours within D in S3) | With plain leave-one-out, training districts' neighbours were far closer than held-out districts' (median 23 km vs 105–394 km), so training and test values differed in distribution | No | d8c7944 |
| 6 | S5 configuration = the L1 configuration of the largest training country (Brazil; Colombia when Brazil is held out) | No S5-specific tuning origin exists | No | d8c7944 |
| 7 | LST outlier screen for Colombia, Peru and Taiwan (value > 10 °C below the district's calendar-month median from years ≤ 2017 set to missing); off for Brazil S1–S4 | Cloud-contaminated cold MODIS LST (Colombia minimum −42 °C); a QC-bit mask did not remove it | No | d8c7944 |
| 8 | Secondary no-case-history arm added, pre-specified in `docs/methods/nohist_arm.md` before it ran | With case history neither embeddings nor controls helped (Brazil and Peru S1), so identity and place information could not be told apart | **Yes** (S1 nulls); labelled exploratory | d8c7944; bd3ba50 |
| 9 | Smallest effect of interest = 1% of WIS(L3) (the protocol's ID-share gate); TOST on 90% intervals; minimum-detectable-effect table | A null result needs an explicit margin | **Partly** (Brazil and Peru S1 seen) | d8c7944 |
| 10 | Deferred: TimesFM + LightGBM residual hybrid, monthly replication arm, PDFM (L5), reporting-lag analysis on data vintages | Time and scope | No | d8c7944 |
| 11 | Inference: DM test on the weekly cross-district mean loss difference with EWC variance, fixed-b t and HLN; interval d̄ ± t_B · SE; TOST on the 90% version; the bootstrap becomes a sensitivity analysis with 52-week (not 8-week) blocks | Weekly loss differences stay autocorrelated at lags 8 and 52 (about 0.42–0.43); the 8-week bootstrap excluded 0 where DM p was 0.3–0.5 | **Yes** (Brazil S1); before any spatial result | fcc3c38 |
| 12 | Primary family = pooled-horizon excess gain, history arm, 14 country × split cells, Holm; embedding and identity gains, per-horizon and per-year results secondary | The family had not been fixed | **Yes** (S1); before any spatial result | fcc3c38 |
| 13 | C3 uses one fixed source map per seed across all years | A new permutation each year meant C3 was not a stable identifier (0–0.05% of districts kept their source) | Found by an audit after Brazil S1 test results; C3 had been scored at the 2019 origin only | fcc3c38; code 9de7386 |
| 14 | C1 in S2–S4 = matched neighbour mean of the neighbours' pre-training-year mean log(1 + cases) (was their 2018 to Y − 1 targets) | In-period neighbour targets are contemporaneous with training targets (a diluted leak) and differ from the S1 definition | No spatial result read | fcc3c38; code 9de7386 |
| 15 | C4 at two ranges: the fitted range (Brazil 8,483 km) and a short range (C4s) | At 8,483 km C4 is close to a planar trend, not an identifier | No | fcc3c38; code 9de7386 |
| 16 | Brazil S1 primary runs get 2 extra seeds at horizons 1 and 4; seed SD reported | Per-horizon seed SD (about 0.0001–0.0003 WIS) is of the same order as the excess gain | **Yes** (Brazil S1) | fcc3c38 |
| 17 | Documented, not changed: yearly inputs keyed to the target year; annual refits train through the end of Y − 1; an origin-keyed sensitivity planned (superseded by row 24) | Audit | – | fcc3c38 |
| 18 | C4/C4s fields fitted only on districts with coordinates; affected Colombia, Taiwan and S5 runs and the Colombia S1 and Brazil S5 C\* runs were discarded and rerun | Three districts without polygons made every field missing in Colombia and Taiwan, so C4/C4s forecasts equalled L3 (Colombia S1 C\* had in effect been plain L3) | **Yes** (Colombia S1 2019 selection, Taiwan S1 test results); no spatial result | e9df1f1 |
| 19 | C\* selection rule v2: drop degenerate candidates; tie set within 2 seed SEs of the best; first tie-set member in priority C1 > C3 > C2 > C4s > C4 > C5 (no-history C3 > C2 > C6 > C4s > C4); zero seed SD = "uninformative" | C\* was being decided inside seed noise (Colombia margin 0.00003 vs seed SD 0.00006; Taiwan exact ties broken by sort order) | **Yes** (Brazil, Peru, Taiwan S1); before any spatial result | e9df1f1 |
| 20 | C4s range = min(D, fitted range); in Peru and Taiwan C4s equals C4 and is not a candidate | C4s had run at a longer range than C4 there; it never won, so no C\* changed | **Yes** (Peru, Taiwan S1) | e9df1f1 |
| 21 | The primary family pools horizons 1 and 4 in every cell; S1 pooled over 1–4 is secondary | The S1 estimand differed from S2–S5 | **Yes** (S1); before any spatial result | e9df1f1 |
| 22 | Brazil S1 primary cell uses seeds 0, 1 and 2 at horizons 1 and 4; each estimand uses the seeds common to both its models; seed SD computed where all seeds exist | The manifest listed one seed, and the old fill rule halved the seed SD | **Yes** (Brazil S1) | e9df1f1 |
| 23 | Scheduler thread budget counts other jobs on the server | Operations | No effect on results | e9df1f1 |
| 24 | Primary scored rows = origin-year rows (drops the first h epidemiological weeks of each test year); all rows reported as a sensitivity | Yearly inputs and annual training labels could postdate the origin (Section A) | **Yes** (after review) | f107238 |
| 25 | Taiwan 2021 is a test year in TW S1 and TW S5; Taiwan S1 explicitly in the 14-cell family; the old test-year set reported as a sensitivity | Excluding a year because it had no cases is an outcome-based exclusion | **Yes** | f107238 |
| 26 | Three target strata (weeks with cases, recorded zeros, zero-filled), each with its own estimate and an exact additive contribution to the cell total | "Observed" mixed weeks with cases and zeros listed by the source; stratum estimates do not add up under equal-week weighting | **Yes** | f107238 |
| 27 | Holm-adjusted TOST, plain labels, margin table at ±0.5/1/2%, and a loss-counting rule (Holm-adjusted p < 0.05; "small" inside ±1%) | Equivalence claims over 14 cells need the same multiplicity control; earlier class words were misleading | **Yes** | f107238 |
| 28 | Robustness columns: EWC with B = 4, IAAFT-calibrated p, delta-method interval, case scale, all rows | The primary test is oversized under multi-season drift in some cells; the percentage ignored denominator uncertainty | **Yes** | f107238 |
| 29 | Fixed control panel (S1: C1, C2, C3, C6 each in place of C\*) | The conclusion should not rest on the selected C\* alone | **Yes** | f107238 |
| 30 | WIS on incidence dropped (never computed); case-scale WIS is the secondary scale | The protocol listed a metric that no code computed | **Yes** | f107238 |
| 31 | The protocol's RQ4 (year-aligned vs static embeddings) deferred; RQ4 in this paper is the exploratory question on where embeddings help or hurt | Time and scope | **Yes** | f107238 |
| 32 | N2 (no-history climate-only level) not run | Compute; not needed for any no-history estimand | Yes | f107238 |
| 33 | Supporting analyses added on the primary rows (Section F), all exploratory | Review | **Yes** | f107238 |
| 34 | Espírito Santo excluded from scoring from 2019-12-29 (Section B6); old exclusions reported as a sensitivity | OpenDengue holds false zeros for the state while InfoDengue shows cases | **Yes** (found in review) | f107238 |

<!-- src: docs/plans/deviations_from_protocol.md rows 1–34 (row 2 validation range corrected per ../audits/review_round/R10_fact_check.md section B; row 13 timing per ../audits/review_round/R6_draft_and_medrxiv.md B MEDIUM 7; row 14 "log incidence" corrected to log(1 + cases) per RESOLUTION_LOG.md section B) -->

**Documented, not changed.** (a) The S3 buffer uses centroids; C1, C2 and C4 use representative points (Section A). (b) The no-history arm uses Brazil's L1 configuration. (c) Brazil's per-level control selection ranks the pre-fix C3 and C4 and is used only within the per-level sensitivity. (d) Brazilian rows in S5 use the LST screen, while Brazil S1–S4 do not (the screen flags 0.08%/0.02% of Brazilian district-months). (e) The outbreak threshold window 2013–2019 includes the training years 2018–2019 but no test year. <!-- src: docs/plans/deviations_from_protocol.md "Documented, not changed" -->

---

## F. Inference details, size simulation, supporting and sensitivity analyses

### F1. Primary estimator and test

For estimand G and cell c, let g be the seed-averaged per-row WIS difference. Then d_{h,t} is the mean of g over districts at horizon h and target week t; d_t is the mean of d_{h,t} over the horizons present (1 and 4); the estimate is the mean of d_t over the T weeks. The DM statistic uses the EWC long-run variance with B = ⌊0.4 T^(2/3)⌋ cosine terms and a t_B reference (B = 16 in Brazil and Taiwan, 11 in Colombia, 13 in Peru) and the HLN factor at h = 4; SE = SE_EWC / HLN. The 95% and 90% intervals are d̄ ± t_B · SE. TOST rejects both one-sided nulls when the 90% interval lies inside ±1% of WIS(L3), where WIS(L3) uses the same week-pooled mean. The minimum detectable effect is (t_{B,0.975} + t_{B,0.80}) · SE. <!-- src: src/pop/eval/estimands.py infer_estimand; src/pop/eval/stats.py; T1_primary_family.csv df -->

```latex
\mathrm{DM} = \frac{\bar d}{\mathrm{SE}},\quad \mathrm{SE} = \frac{\mathrm{SE}_{\mathrm{EWC}}}{c_{\mathrm{HLN}}},\quad
B = \left\lfloor 0.4\,T^{2/3}\right\rfloor,\quad
c_{\mathrm{HLN}} = \sqrt{\frac{T + 1 - 2h + h(h-1)/T}{T}}
```

**Labels and counting.** Each cell's plain label combines the Holm-adjusted DM test with TOST, for example "small negative difference, significant after Holm correction; within ±1% (TOST, Holm-adjusted)" or "no significant difference; not shown to be within ±1%". A loss (gain) is an excess gain below (above) zero with Holm-adjusted p < 0.05; it is "small" when inside ±1%. A nominal p < 0.05 alone is never counted. <!-- src: docs/plans/deviations_from_protocol.md row 27; T1_primary_family.csv plain_label -->

**Margin.** ±1% was chosen after the Brazil and Peru S1 results. In the US COVID-19 Forecast Hub, adjacent leading models differed by 0.01–0.02 relative WIS, about 1.6–3.3% of the leader's WIS [@cramer2022covidhub]; ±1% is stricter than that. Margins of ±0.5% and ±2% are reported (Supplementary Table S2-6). <!-- src: ../audits/review_round/R8_literature.md section 2 -->

**Inference population.** Weeks are the sampling unit, for this fixed set of districts, fitted pipelines and test seasons. Spatial-split folds are partitions, not samples. Inference about new seasons would need the between-season variance, which a season-level t-test with 2–4 degrees of freedom can barely estimate. <!-- src: docs/results/review/RC_summary.md "What population the inference refers to" -->

### F2. Robustness columns

- **EWC with B = 4** cosine terms (fewer terms, more robust to low-frequency variation, less power).
- **IAAFT-calibrated p.** 2,000 windowed IAAFT surrogates [@schreiber1996iaaft] of d_t: a circular surrogate of length 8T with the real marginal distribution and the real span-3-smoothed spectrum (held flat below frequency 1/T), centred at zero, from which a random length-T window is taken. The p-value is (1 + k)/(1 + 2,000), where k counts surrogates whose |DM statistic| is at least the observed one.
- **Delta-method interval** for 100 × G / WIS(L3), with WIS(L3) estimated (EWC + HLN on the linearised weekly series).
- **Case scale:** the excess gain with WIS on raw counts (expm1 of the log-scale quantiles, clipped at 0).
- **All rows:** without the origin-year filter.
- **Old exclusions:** without the Espírito Santo exclusion.
- **Circular block bootstrap** of d_t with 52-week blocks; descriptive only, because T = 154–256 weeks gives three to five blocks.

<!-- src: docs/plans/deviations_from_protocol.md row 28; scripts/analysis/rk_compute.py iaaft_pvalue, robust_table; docs/results/review/RC_summary.md "What was tested"; docs/results/review/RA_summary.md RA6 -->

### F3. Size simulation

We measured the size of the primary test and its alternatives on null series calibrated to each cell's own centred d_t (2,000 replications per cell and generating process). Generating processes: windowed IAAFT (multi-year swings treated as stationary noise), IAAFT with doubled power below frequency 2/T (stress test), annual harmonics plus AR(1) with resampled heavy-tailed residuals (ARX), and Gaussian AR(1) with φ = 0.5 and T = 104. Real placebos were seed-vs-seed differences of the same model: 21 Brazil S1 series (T = 261) and 33 series from the 2019 control runs (T = 52). <!-- src: docs/results/review/RC_summary.md "What was tested" -->

*Table S1-F1. Empirical size at nominal 5% (Monte Carlo SE about 0.5 percentage points).* <!-- src: docs/results/review/RC_summary.md size table -->

| Generating process | EWC + HLN (primary) | EWC + HLN, B = 4 | Newey–West (NW94) | 52-week block bootstrap |
|---|---|---|---|---|
| AR(1), φ = 0.5, T = 104 | 0.054 | 0.046 | 0.110 | 0.294 |
| ARX, median over cells | 0.026 | 0.034 | 0.10 | 0.18–0.21 |
| IAAFT, median over cells | 0.048 | 0.036 | 0.20 | 0.18–0.21 |
| IAAFT low-frequency stress, median over cells | 0.120 | 0.048 | 0.30 | 0.18–0.21 |
| IAAFT, worst cells (BR S1, BR S2, BR S3, CO S5, PE S1) | 0.10–0.22 | ≤ 0.15 | 0.10–0.50 (any process) | 0.15–0.31 (any process) |
| Seed placebo, Brazil S1 (21 series) | 2 of 21 rejected | 1 of 21 | 4 of 21 | 3 of 21 |
| Seed placebo, 2019 controls (33 series, T = 52) | 4 of 33 | 5 of 33 | 13 of 33 | undefined |

**Conclusions.** The primary test is acceptably calibrated when d_t is short-memory around a fixed mean, as in most cells (size ≤ 8% under ARX), and HLN changes size by at most 1 point. It is oversized (10–22%, up to 28% under the stress test) in cells whose gain drifts across seasons, if that drift is treated as noise: Brazil S1, S2, S3, Colombia S5 and Peru S1. Equivalence statements for Brazil S1, Brazil S2 and Colombia S5 therefore hold "assuming no multi-season drift". Newey–West, the h − 1 HAC and both block bootstraps are badly oversized. In this simulation analysis, which preceded the origin-year filter and the Taiwan 2021 runs, only Colombia S4 lost Holm significance with B = 4 (Holm-adjusted p 0.10). On the current primary rows (Table 2, Supplementary Table S2-5), Colombia S1, S3 and S4 and Taiwan S5 lose Holm significance with B = 4, and Colombia S4 and Taiwan S5 with IAAFT calibration; the direction of all six losses is unchanged. Power to detect a gain of 1% of WIS(L3) is about 1.00 in Brazil S2/S3/S5 and Colombia S1–S4, 1.00 in Colombia S5, 0.83–0.88 in Brazil S1, Taiwan S1 and Peru S1, 0.53 in Peru S5 and 0.08 in Taiwan S5. <!-- src: docs/results/review/RC_summary.md "Power", "Do the primary-family conclusions change?", "Verdict" -->

<!-- Note: RC_summary.md was computed before kit v3 (all rows, before the origin-year filter and the ES exclusion); current robustness p-values are in T1 (B4_Holm_p, p_iaaft_Holm). -->

### F4. Supporting analyses (exploratory, no multiplicity adjustment; D33)

<!-- src: docs/results/review/RD_summary.md sections 1–6; docs/results/review/RB_summary.md sections 1–3; docs/results/review/RA_summary.md RA1, RA7; docs/plans/deviations_from_protocol.md row 33 -->

- **S1 baselines:** WIS on log(1 + cases) of L0, negative binomial, LightGBM L1–L4 and L3/L4 + C\*, and TimesFM (Brazil), with relative WIS against L0 on rows scored by every model.
- **Additive stratum contributions:** per horizon and week, d = Σ_s w_s d_s with w_s the stratum's row share, so the contributions (as % of the cell's WIS(L3)) sum exactly to the total. Stratum estimates on their own rows are also reported as % of the stratum's own WIS(L3); they are not shares of the total.
- **Outbreak weeks:** cases ≥ max(5, the district's 90th percentile of weekly cases over 2013–2019).
- **Weighted means:** inside each (horizon, week) mean, weights equal to district population in the target year, or to the district's mean weekly cases over 2013–2017 plus 1.
- **Causal recalibration:** separately for L3 + C\* and L4 + C\*, additive per-quantile shifts on the log scale fitted only on earlier test years (the first test year unadjusted), either one shift per quantile ("global") or per bin of the forecast median ("Mondrian").
- **Mechanism:** the change in the mean 0.9 quantile between L4 + C\* and L3 + C\* on rows with zero cases, and the share of the zero-row loss from quantiles above the median.
- **Embedding similarity (S2–S5):** the maximum (and top-5 mean) cosine similarity between a held-out district's renormalised year y − 1 embedding and the training districts' vectors [@meyer2021aoa], against the district's gain.
- **Per-year gains** with context flags (COVID-19 years 2020–2021, Peru 2023, Brazil 2024).
- **Strata for RQ4 (exploratory):** population tercile (year before the test year), number of years 2014–2017 with at least one case (0, 1–2, 3–4) and change in GHSL built-up share 2010–2015 (tercile).
- **Coverage** of the 40% and 80% intervals overall and on weeks with cases.

### F5. Sensitivity analyses

| Analysis | Cells | Estimands | Status |
|---|---|---|---|
| Three seeds (primary) vs seed 0 | Brazil S1 | All three | Done |
| Per-level tuning (original protocol) | Brazil S1 | All three | Done |
| Fixed control panel C1, C2, C3, C6 | S1, all countries | Identity and excess gains | Colombia, Peru, Taiwan, Brazil C1/C2 done; [[PENDING: BR C3/C6 panel]] |
| Yearly inputs keyed to the origin year (strictly causal) | Brazil S1 | Embedding gain only | [[PENDING: sensitivities yref/delay2]] |
| Two-week reporting delay in case inputs | Brazil S1 | Embedding gain only | [[PENDING: sensitivities yref/delay2]] |
| Taiwan with Brazil's configuration and C\* | Taiwan S1 | All three | Done |
| Taiwan without 2021 | Taiwan S1, S5 | All three | Done |
| Margins ±0.5% and ±2% | All cells | Excess gain | Done |
| All rows; old exclusions; case scale; B = 4; IAAFT; delta method | All cells | Excess gain | Done |
| Late-entry district universe | All cells | Excess gain | Not run |

<!-- src: T6a_sensitivities.csv variant and variant_status; RE_summary.md; T1_primary_family.csv robustness columns; ../audits/review_round/R1_timing_leakage.md section 1c (late entry not run). Note: RE_summary.md says the control panel uses the v3 primary rows (origin-year filter, exclusions v2), while NOTES_FOR_WRITERS item 32 says all rows; see notes_B. -->

The reporting-delay sensitivity shifts only the case-history inputs two weeks back; it is not an evaluation on data vintages. The origin-keyed and delay runs cover L3 and L4 only, so they are compared with the embedding gain, not the excess gain. <!-- src: ../audits/review_round/R1_timing_leakage.md sections 1a, 1c; ../audits/review_round/RESOLUTION_LOG.md section C -->

---

## G. EPIFORGE 2020 checklist

Items are paraphrased from Pollett et al. 2021 [@pollett2021epiforge]; the official checklist file should replace this table in the final supplement. Section numbers refer to draft v1. <!-- src: ../audits/review_round/R6_draft_and_medrxiv.md section E -->

| # | Item | Where | Status |
|---|---|---|---|
| 1 | Identify the study as forecasting research in the title or abstract | Title; Abstract | Present |
| 2 | Purpose and forecast targets | Introduction; Methods 2.3 (target: weekly cases per district, 1–4 weeks ahead) | Present |
| 3 | Methods in reproducible detail, including fitting and assumptions | Methods 2.2–2.10; Supplement S1, A–F | Present; code link in item 9 |
| 4 | Prospective, real-time or retrospective | Methods 2.1: retrospective, from one snapshot of final revised data | Present |
| 5 | Origin of input data, with references | Methods 2.2–2.3; Supplement S1, B1 | Present |
| 6 | Source data available, or why not | Data availability statement (OpenDengue and all covariate sources are public; derived panels to be deposited) | Needs the deposit DOI from the authors |
| 7 | Data processing | Methods 2.2; Supplement S1, B2–B7 | Present |
| 8 | Model type and assumptions, with references | Methods 2.3; Supplement S1, C and D | Present |
| 9 | Code available, or why not | Code availability statement | **Missing:** public repository URL and Zenodo DOI (authors) |
| 10 | Validation approach, described and justified | Methods 2.5–2.6; Supplement S1, A | Present |
| 11 | Accuracy evaluation, described and justified | Methods 2.7–2.9; Supplement S1, F | Present |
| 12 | Comparison with benchmark models, justified | Methods 2.3 (seasonal naive, negative binomial, TimesFM in Brazil); Results; Supplementary Table S2-1 | Present |
| 13 | Forecast horizon, described and justified | Methods 2.3: 1–4 weeks, the range used by forecast hubs; horizons 1 and 4 bracket it and are used in S2–S5 to halve compute | Present |
| 14 | Forecast uncertainty presented and explained | Quantile forecasts, WIS and interval coverage (Methods 2.7; Results) | Present |
| 15 | Non-technical summary of results and uncertainty | Plain-language summary (front matter) | Present |
| 16 | Time-stamped, versioned identifier for forecasts and data | Zenodo deposit of code, forecasts and derived data | **Missing** (authors) |
| 17 | Weaknesses, including data quality and methods | Discussion, Limitations | Present |
| 18 | Implications for public-health action | Discussion (scoped: no deployment recommendation) | Present |
| 19 | Generalisability across populations | Discussion; four-country design and S5 | Present |

---

## H. Glossary

| Term | Meaning |
|---|---|
| Admin1, Admin2 | First- and second-level administrative units. Admin1: states (Brazil), departments (Colombia, Peru), counties and cities (Taiwan). Admin2: municipalities (Brazil, Colombia), provinces (Peru), townships (Taiwan) |
| AlphaEarth | AlphaEarth Foundations Satellite Embedding V1: annual 64-dimensional embeddings of satellite imagery at 10 m [@brown2025alphaearth] |
| B | Number of cosine terms in the EWC variance; also the degrees of freedom of the t reference |
| C1–C6, C4s | Location controls (Table S1-C2) |
| C\* | Validation-selected control: the control chosen at the 2019 origin by selection rule v2 |
| Case scale | WIS computed on raw counts instead of log(1 + cases) |
| Coverage | Share of observed values inside a central prediction interval (40% or 80%) |
| D | S3 buffer distance (Brazil 225 km, Colombia 130 km) |
| DM test | Diebold–Mariano test of equal forecast accuracy [@diebold1995comparing] |
| District | Our word for an Admin2 unit |
| EE, EECU | Google Earth Engine; Earth Engine compute units (a quota meter) |
| Embedding gain, G_emb | WIS(L3) − WIS(L4) |
| Epidemiological week, year | Sunday-start week; its year is the calendar year of its Wednesday |
| EPIFORGE | Reporting guideline for epidemic forecasting studies (2020) |
| EWC | Equal-weighted cosine long-run variance estimator [@lazarus2018har] |
| Excess gain, G_excess | WIS(L3 + C\*) − WIS(L4 + C\*); the primary estimand |
| GHSL | Global Human Settlement Layer (population and built-up surfaces) |
| h | Forecast horizon in weeks (target week minus origin week) |
| HLN | Harvey–Leybourne–Newbold small-sample correction [@harvey1997testing] |
| Holm | Holm's step-down multiplicity correction [@holm1979simple] |
| IAAFT | Iterative amplitude-adjusted Fourier transform surrogates: random series with a given distribution and spectrum |
| Identity gain, G_id | WIS(L3) − WIS(L3 + C\*) |
| L0–L4 | Feature ladder levels (Table S1-C1) |
| LightGBM | Gradient-boosted decision trees [@ke2017lightgbm]; here with a quantile loss |
| LST | Land-surface temperature (MODIS) |
| MDE | Minimum detectable effect at 80% power and 5% two-sided level |
| MODIS | Moderate Resolution Imaging Spectroradiometer |
| N3, N4 | No-history levels: L3 and L4 without case-derived inputs |
| NB | Negative binomial regression |
| NDVI | Normalised difference vegetation index |
| Origin | The last week whose data a forecast may use; forecasts are made at its end |
| Origin-year rows | Scored rows whose origin lies in the same epidemiological year as the target (primary) |
| q0.9 | The 0.9 quantile of a forecast |
| Recorded zero | A week the source lists with 0 cases (Brazil 2020–2021 in the test years) |
| S1–S5 | Evaluation splits: new years, held-out states, held-out buffered blocks, held-out random districts, held-out country |
| SE | Standard error |
| T | Number of target weeks in a cell's weekly series |
| TimesFM | A pretrained time-series foundation model, used zero-shot as a baseline [@das2024timesfm] |
| TOST | Two one-sided tests for equivalence [@lakens2017equivalence] |
| VIIRS | Visible Infrared Imaging Radiometer Suite (night lights) |
| WIS | Weighted interval score [@bracher2021wis]; lower is better |
| WIS(L3) | Mean WIS of model L3 in the cell; the denominator of every percentage |
| y, Y | y: the target's epidemiological year; Y: the test year of an annual refit |
| y − 1 | The year before the target year, the source year of yearly inputs |
| Zero-filled week | A district-week missing from the source and set to 0 |
