# Supplementary Methods

Contents: A. Data sources, processing and verification. B. Features and controls. C. Models and hyperparameters. D. Information available to each model. E. Inference, size simulation, supporting and sensitivity analyses. F. Deviations from the original protocol. G. EPIFORGE 2020 checklist. H. Glossary (Table S16). I. Further limitations.

Automated AI agents (see Use of AI tools) wrote the code and ran the downloads, the verification scripts, the Earth Engine extractions, the model runs, the scoring, the statistical analyses and the internal audits described in this supplement. Where a check is called separate or independent below, it was written and run by a different automated AI agent from the one that produced the checked output, not by a person.

Split codes used in this supplement: S1, new years; S2, held-out states; S3, held-out regions (compact blocks of districts with a buffer); S4, held-out districts (assigned at random); S5, held-out country. Model codes: L0 to L4 for the ladder (L3 is the reference model), C\* for the selected location control and C1 to C6 for the controls (Table S7). Gains: the embedding gain (L3 to L4), the control gain (L3 to L3 + C\*; called the identity gain in earlier drafts and `G_id` in the code and result files) and the excess gain (L3 + C\* to L4 + C\*). Tables S17 to S55 and Figures S1 to S4 are in the Supplementary Results.

---

## A. Data sources, processing and verification

### A1. Sources and licences

**Table S1. Data sources, versions and licences.**

<!-- src: docs/research/data_and_tools.md (OpenDengue, AlphaEarth, ERA5-Land licence rows); docs/data/boundaries_join.md "Sources and licences"; docs/features/remote_sensing.md "Sources and conventions"; docs/data/zero_fill_crosscheck.md -->

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

All gridded inputs were fetched from Google Earth Engine [@gorelick2017gee] and reduced to polygons locally with exact coverage fractions [@baston_exactextract]. Downloaded source files were re-checked before use by a separate verification script, written and run by an automated AI agent other than the downloading one (see Use of AI tools): checksums against upstream, archive integrity, full parse. The OpenDengue archives matched the GitHub blob hashes of release commit 99b6a3e and the figshare v5 MD5 sums and parsed without error. The boundary files and the 2024 InfoDengue pulls were verified the same way. <!-- src: docs/data/opendengue_v1.3.1_verification.md; docs/data/boundaries_verification.md; docs/data/zero_fill_2024_verification.md section 1 -->

### A2. Weekly district panel

Rows with weekly time resolution and Admin2 spatial resolution were taken from the Temporal extract. All weekly rows are 7-day spans starting on Sunday, and no (district, week) pair is duplicated. The epidemiological year of a week is the calendar year of its Wednesday. Districts are identified by the 7-digit IBGE code in Brazil and by Admin1|Admin2 name elsewhere; FAO GAUL codes are not unique (Taiwan's 287 districts share two codes). <!-- src: docs/data/panel_weekly_v1.md; ../audits/review_round/R10_fact_check.md section B (GAUL codes 5,456 / 1,012 / 113 / 2) -->

**Table S2. Weekly district panel after zero-filling.**

<!-- src: docs/data/panel_weekly_v1.md "Counts"; docs/data/opendengue_v1.3.1_audit.md (raw rows with 0 cases); ../audits/review_round/R10_fact_check.md items 5a, 5c, 5d and section B (raw row counts) -->

| Country | Districts | Weeks | Panel rows | Source weekly rows | Source rows reporting 0 cases | Panel rows zero-filled (whole window) |
|---|---|---|---|---|---|---|
| Brazil | 5,517 | 574 | 3,166,758 | 1,895,538 | 63% | 40.1% (2014–2021: 29.3%; 2022 on: 69.2%) |
| Colombia | 1,071 | 835 | 894,285 | 199,458 | 0.4% | 77.7% |
| Peru | 115 | 1,252 | 143,980 | 30,991 | 0% | 78.5% |
| Taiwan | 287 | 1,409 | 404,383 | 7,673 | 0% | 98.1% |

District counts are districts that ever reported a case, not administrative totals: Peru's 115 of about 196 provinces and Taiwan's 287 of about 368 townships (those that ever had a locally acquired case). <!-- src: docs/data/zero_fill_crosscheck.md (287 of ~368 townships); docs/data/completeness_v1.md "Peru zero-fill check" (~115 of ~196 provinces ever report) -->

Three district counts appear in the paper. The panel has 6,990 districts (Table S2). Of these, 6,987 have a boundary polygon (Table S3; one Colombian and two Taiwanese districts have none). The scored count is 6,909: the 78 Espírito Santo municipalities have no scored row, because their exclusion (Section A6) covers every test year, so Brazil contributes 5,439, Colombia 1,070, Peru 115 and Taiwan 285. The headline count in the main text is the scored count, 6,909. <!-- src: Table S2 (5,517 + 1,071 + 115 + 287 = 6,990); Table S3 (5,517 + 1,070 + 115 + 285 = 6,987); S7_embedding_distance.csv n_units BR_S5 5,439, CO 1,070, PE 115, TW 285 (sum 6,909); docs/plans/deviations_from_protocol.md row 34 (78 ES municipalities) -->

### A3. Boundaries

Brazil was joined by IBGE code to the 2022 municipal mesh. Colombia, Peru and Taiwan were joined by name within Admin1, in the order manual fix, Taiwan CDC crosswalk, exact, normalised and fuzzy match (rapidfuzz ≥ 85, ≥ 90 for Taiwan, one-to-one). <!-- src: docs/data/boundaries_join.md "Method" -->

**Table S3. Matching of districts to boundary polygons.**

<!-- src: docs/data/boundaries_join.md "Match rates" -->

| Country | Districts matched | Cases 2014 on matched | Match methods |
|---|---|---|---|
| Brazil | 5,517 / 5,517 | 100.000% | IBGE code |
| Colombia | 1,070 / 1,071 | 99.994% | exact 1,005, normalised 30, fuzzy 28, manual 7 |
| Peru | 115 / 115 | 100.000% | exact 113, manual 2 |
| Taiwan | 285 / 287 | 100.000% | CDC crosswalk 271, manual 6, exact 4, normalised 3, fuzzy 1 |

The unmatched districts are Belén de Bajirá (Colombia; 40 cases since 2014; its municipality status was annulled) and two non-spatial "other" buckets in Taiwan (no cases since 2014). They are excluded from scoring. The official Taiwan township file returned HTTP 403, so Taiwan polygons are the 2017 OpenStreetMap-derived geoBoundaries file. <!-- src: docs/data/boundaries_join.md "Unmatched units"; docs/data/completeness_v1.md "Other exclusion files" -->

#### Taiwan crosswalk

The OpenDengue-to-CDC township crosswalk was inferred by an assignment that maximises shared weekly cases within each county, so agreement in weekly counts is partly built in and is not an independent validation. Independently of counts, the pinyin of every Chinese township name matches the OpenDengue romanised name for 287 of 287 districts (281 exactly, 5 by close string similarity, 1 checked individually), and 40 crosswalk rows were reviewed one by one; both checks were made by automated AI agents (see Use of AI tools). <!-- src: ../audits/review_round/R1_timing_leakage.md section 4; docs/data/boundaries_verification.md -->

### A4. Zero-fill validation

#### Rule

The district universe is every Admin2 unit in a country's weekly file. Coverage runs from the country's first to last week with any Admin2 row, and a missing district-week is set to 0 and flagged zero-filled. <!-- src: docs/data/panel_weekly_v1.md "Frozen rule" -->

#### Brazil vs InfoDengue

OpenDengue matches InfoDengue's probable count (`casprov`), not its notified count. <!-- src: docs/data/zero_fill_crosscheck.md; docs/data/zero_fill_crosscheck_2024.md -->

**Table S4. OpenDengue compared with InfoDengue probable cases in samples of Brazilian municipalities.**

| Year | Municipalities sampled | Present weeks: Σ OpenDengue / Σ probable | Absent weeks with ≥ 1 probable case | Maximum in an absent week |
|---|---|---|---|---|
| 2017 | 40 | 1.008 | 0 of 902 | 0 |
| 2019 | 40 | 1.003 | 0 of 573 | 0 |
| 2022 | 40 | 1.020 | 14 of 1,285 (1.1%) | 4 |
| 2023 | 40 | 0.939 | 26 of 1,231 (2.1%) | 8 |
| 2024 (excluding Espírito Santo) | 58 | 0.964 | 25 of 1,658 (1.5%) | 3 |

Weekly correlation was ≥ 0.97 in every year and group (0.999 in 2024). The small present-week differences, larger in later years, are consistent with surveillance revisions after the OpenDengue snapshot. <!-- src: docs/data/zero_fill_crosscheck.md; docs/data/zero_fill_crosscheck_2024.md (60 municipalities incl. 2 ES) -->

#### Taiwan vs Taiwan CDC

OpenDengue's Taiwan series equals locally acquired confirmed cases by onset week and residence township; imported cases are excluded. All 7,673 present township-weeks match exactly, no absent township-week holds a local case, and 2021 had no local cases (12 imported). National weekly totals match exactly in 83.7% of weeks; the rest of the gap is 410 early local cases (1998–2010, 217 of them in 2002) with no residence county, which cannot be assigned to a township. <!-- src: docs/data/zero_fill_crosscheck.md Taiwan section -->

#### Colombia and Peru

Admin2 sums agree with national totals within about 5% in Colombia; the weekly Admin2/national ratio is about 1 and stable (10th percentile at least 0.79 in 2020–2022), leaving little room for unreported cases in filled weeks. <!-- src: docs/data/completeness_v1.md "Colombia: the ratio is ≈1 and stable (2020–22 weekly p10 ≥ .79)" --> In Peru they cover 85–94% of national totals in 2020–2023; with the same case definition, district sums are 0.84–0.94 of department totals (2007–2013) and only 0.4–1.6% of reference cases fall in fully zero-filled department-weeks. Province-level absent weeks could not be checked; Peru is "partially validated". <!-- src: docs/data/completeness_v1.md "Peru zero-fill check", "Recommendation" item 3 -->

### A5. Completeness rule and exclusions

#### Completeness rule

The rule was fixed after the new-years results but before it was applied to the test years. The primary threshold is k = 0.5, with 0.4 and 0.6 as sensitivity values. <!-- src: docs/data/completeness_v1.md "Rule" -->

1. Country × week (Brazil, Colombia, Peru; national count ≥ 20): flagged when the Admin2/national ratio is below k × its seasonal reference (median ratio of the previous three years at epidemiological weeks ±2) and below k × the same year's median ratio.
2. Admin1 × week: flagged when cases fall below k × the smaller of the mean of the two weeks before and the two weeks after (that minimum ≥ 50). If the national series dips the same way, the flag is for sensitivity only.
3. Primary flags at k ≤ 0.5 are excluded from scoring; all others feed sensitivity analyses.

#### Flags in the test years

Brazil, Colombia and Taiwan: none. Peru: Junín 2020-12-27 and Ucayali 2023-07-23 (0.03% of rows, 0.02% of cases). Brazil 8–22 December 2024 carries a sensitivity-only flag (1.1% of Brazilian test rows, 0.4% of cases). Taiwan had no national reference, but its rule-2 check gave 0 flags in 96 evaluable state-weeks. Removing the incomplete-week exclusions restores 16 Peruvian rows and changes no result. <!-- src: docs/data/completeness_v1.md "Flags in the test years", "Recommendation"; docs/results/review/RA_summary.md RA3 -->

#### Gap flag in training

A country-week is gap-flagged when the national count is ≥ 20 and the Admin2/national ratio is below 0.25 × that country-year's ratio of sums. Only one week is flagged (Peru, 2018-08-12); it is dropped from training targets. <!-- src: docs/data/panel_weekly_v1.md "flag_gap"; ../audits/review_round/R1_timing_leakage.md section 0 last row -->

### A6. Espírito Santo false zeros (D34)

OpenDengue V1.3.1 has no source data for Espírito Santo after 2020: Admin2 rows end on 2020-12-27, 63 of the 78 municipalities have their last row on 2019-12-22, and the 15 with 2020 rows report far fewer cases than InfoDengue (7,562 vs 27,077 probable). In 2024 every Espírito Santo week is zero-filled, while InfoDengue shows probable cases in 2,925 of 4,056 of those weeks (72%), 166,407 cases in total. A scan of every Admin1 unit in the four countries found no other structural defect. <!-- src: docs/data/zero_fill_2024_verification.md sections 2–3; docs/data/zero_fill_crosscheck_2024.md ES table -->

#### Rule

Every district whose IBGE code matches `^32\d{5}$` is excluded from scoring for target weeks from 2019-12-29 (epidemiological year 2020) onward, in every Brazilian cell and for all models. This removes 38,766 primary rows per cell (1.41% of the about 2.74 million Brazilian primary rows before this exclusion; 2,703,183 remain) and moves every Brazilian excess gain by at most 0.03 percentage points. The exclusion does not depend on outcomes of other states: the source stopped reporting this state. Models were not refitted, so their 2020–2023 training targets still contain these false zeros (Espírito Santo is 1.9–4.5% of Brazil's zero-filled rows per year). <!-- src: docs/plans/deviations_from_protocol.md row 34; docs/results/review/KIT3_changes.md ES section; docs/data/zero_fill_crosscheck_2024.md ES table -->

### A7. Covariates

#### Climate (L2)

ERA5-Land daily aggregates were summed or averaged to the panel's Sunday-start weeks: mean, minimum and maximum 2 m temperature, total precipitation and relative humidity from daily mean temperature and dew point (Magnus formula, capped at 100%). Weights are GHSL population of the nearest epoch, with exact polygon coverage on a 0.01° grid aligned to ERA5-Land's 0.1° grid; ocean cells get zero weight. Weekly grids were fetched with `computePixels` and reduced locally, which agreed with Earth Engine `reduceRegions` to r > 0.999999995 at about 1/20 of the compute (Brazil 1.76 EECU-hours). Twenty-three districts with no ERA5-Land land cell (Brazil 3, Colombia 2, Taiwan 18, mostly islands) use the nearest land cell. <!-- src: docs/features/climate_era5land.md "Definitions" and "Method choice"; ../audits/review_round/R10_fact_check.md section B (23 units) -->

#### Remote sensing and population (L3)

<!-- src: docs/features/remote_sensing.md "Sources and conventions", "QA", "Caveats", "v2" -->
- NDVI: MOD13Q1 (16-day, 250 m), SummaryQA ≤ 1, read from about 1 km pyramids (r = 0.998 against native 250 m in a pilot, at about a quarter of the cost).
- Land-surface temperature: MOD11A2 day and night (8-day, 1 km), without the QC mask. A QC-masked version (v2) did not remove the cloud-contaminated cold values and changed Brazilian anomalies (correlation with v1 about 0.85–0.88), so it was rejected. Instead, for Colombia, Peru, Taiwan and every S5 model, an LST value more than 10 °C below the district's calendar-month median over years ≤ 2017 is set to missing (D7). The screen flags day/night: Brazil 0.08%/0.02%, Colombia 0.06%/0.57%, Peru 0.06%/0.18%, Taiwan 0.05%/0.06% of district-months; it is off for Brazil S1–S4. <!-- src: docs/methods/s1_pipeline.md "LST outlier screen" -->
- Month assignment: a composite belongs to the month of its last day, so month m contains no information after month m. Missing district-months are filled from the same month of the previous year only.
- Night lights: VIIRS annual, from 2013 (missing before). Built-up share: GHSL GHS_BUILT_S, interpolated linearly between epochs.
- Population: GHSL GHS_POP, log-linear between epochs, no extrapolation. It exceeds the 2022 Brazilian census by 4–10%, so it is used as a relative scale.
- Remote-sensing extraction used 8.9 EECU-hours in total.

#### AlphaEarth (L4)

<!-- src: docs/features/alphaearth_extraction.md "Method"; docs/features/alphaearth_verification.md; ../audits/review_round/R10_fact_check.md items 1b, 3, 4b and section B -->
- Image: the annual mosaic of `GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL` (64 bands A00–A63, 10 m, unit-length pixel vectors), read through the mean pyramid.
- Population-weighted mean at 100 m on the native GHS_POP Mollweide grid, with weight = coverage fraction × GHSL population (negative no-data set to 0, linear interpolation between the 2015, 2020 and 2025 epochs). Only populated blocks are fetched. An unweighted 300 m mean is stored but not used in the primary models.
- In a 10-municipality subset of the Brazilian pilot, 100 m was effectively exact against 10 m (mean cosine 0.99994), while naive 300 m resampling was not (0.993). Fetching blocks with `computePixels` and summing locally matched `reduceRegions` exactly at about 40% of its cost.
- Image years extracted: Brazil 2017–2024, Colombia 2017–2021 and 2023, Peru and Taiwan 2017–2023. Target year y uses image year y − 1.
- District means are not unit-length: the median population-weighted norm is 0.87–0.92 by country (range 0.70–0.98; Brazil median 0.92, range 0.74–0.98). Each mean is renormalised to unit length.
- Fernando de Noronha (Brazil) has no AlphaEarth pixels in 2017–2021 upstream; its embedding inputs are missing for target years 2018–2022 and LightGBM routes them as missing. The missing values are the same in every model that contains the embeddings (L4 and L4 + C\*), so they do not differ between the two sides of the excess gain.
- Re-extracting one state-year with a different number of workers gave bitwise-identical sums.

**Table S5. Independent recomputation of AlphaEarth district means.**

<!-- src: docs/features/alphaearth_verification.md; ../audits/review_round/R10_fact_check.md items 3, 4b and section B -->

| Country | Districts covered | District-years recomputed | Minimum cosine, weighted | Minimum cosine, unweighted | Median cosine, neighbours vs random pairs |
|---|---|---|---|---|---|
| Brazil | 5,517 / 5,517 | 33 | 0.9999999987 | 0.9999999969 | 0.973 vs 0.710 |
| Colombia | 1,070 / 1,071 | 33 | 0.9999999982 | 0.9999999975 | 0.926 vs 0.644 |
| Peru | 115 / 115 | 32 | 0.99999999975 | 0.9999999996 | 0.91 vs 0.44 |
| Taiwan | 285 / 287 | 33 | 0.99999998 | 0.99999989 | 0.975 vs 0.88 |

Note: The recomputation used a separate script, written and run by an automated AI agent other than the extracting one (see Use of AI tools), with its own Earth Engine code; it did not reuse the extraction code. Population sums agree within 0.03%. <!-- src: ../audits/review_round/R10_fact_check.md section B (max 0.027%, Taiwan; Brazil max 0.017%) --> Districts not covered are those without a polygon. Agreement shows that the extraction is reproducible, not that the product is valid.

### A8. Computation

LightGBM 4.7.0 ran on CPU in deterministic mode with row-wise histograms; every pair of compared runs uses the same thread count, seed rule and version. On a checked booster, predictions were bit-identical across 2, 4, 8 and 16 threads. TimesFM ran on one GPU. <!-- src: docs/methods/compute_plan.md lines on determinism; docs/methods/timesfm.md -->

#### Training and randomness

Every booster is trained for a fixed 400 rounds; there is no early stopping and no validation set inside the test-year fits. The `seed` of a run sets LightGBM's random number generators, which act only through row subsampling (bagging fraction 0.8 at every iteration) and column subsampling (feature fraction 0.9), and it sets the random draws of the controls C3 (the source map of shuffled embeddings) and C4/C4s (the random fields). Nothing else in a run is random: the features, folds, test years and scoring are fixed. <!-- src: src/pop/models/lgbm.py lines 10-11, 21, 32 (num_boost_round 400, seed, no early stopping); src/pop/features/controls.py SEEDED_CONTROLS, _rng; docs/methods/round3_runs.md section S1 -->

#### Size of each fit

One fit is one booster for one quantile, horizon, test year and fold; each chunk fits 9 boosters (the median and the 8 other deciles) on the same training rows. Table S5b gives the range of training rows per fit for the full model L4 + C\* over test years and folds (the smallest at the first test year, 2020); the number of inputs is the same across models of a cell except for the embedding and control blocks (Table S6). The tuning and selection fits at the 2019 origin trained on the 2018 targets: Brazil 286,884 rows, Colombia 55,692, Peru 5,865 and Taiwan 14,924 (horizon 1). <!-- src: runs/<country>_s1_shared_controls_2019/chunks/lgbm__L3+C1__s0__2019__h1.done.json n_train -->

**Table S5b. Training rows per fit for the full model (L4 + C\*), horizons 1 and 4.**

<!-- src: runs/<run>/chunks/*.done.json n_train and n_features for test years >= 2020; run directories brazil_s1_shared_L4_Cstar, brazil_s2_L4_Cstar, brazil_s3_L4_Cstar, brazil_s5_L4_Cstar, colombia_s1_shared_L4_Cstar, colombia_s{2,3,4,5}_L4_Cstar, peru_s1_L4_Cstar, peru_s5_L4_Cstar, taiwan_s1_shared_L4_Cstar, taiwan_s5_L4_Cstar plus taiwan_s5_tw2021_L4_Cstar; brazil_s1_nohist_N4_Cstar; brazil_s4_L4_Cstar and brazil_s2_nohist_N4_Cstar (read 2026-11-20) -->

| Cell | Training rows per fit (range over test years and folds) | Input columns |
|---|---|---|
| Brazil, new years | 573,768 – 1,726,821 | 151 |
| Brazil, held-out states | 456,872 – 1,385,651 | 151 |
| Brazil, held-out regions | 377,624 – 1,290,812 | 151 |
| Brazil, held-out districts | 458,952 – 1,381,582 | 151 |
| Brazil, held-out country | 153,077 – 405,242 | 214 |
| Colombia, new years | 111,384 – 223,839 | 151 |
| Colombia, held-out states | 89,024 – 179,113 | 151 |
| Colombia, held-out regions | 54,912 – 216,942 | 151 |
| Colombia, held-out districts | 89,024 – 179,113 | 151 |
| Colombia, held-out country | 615,461 – 1,236,956 | 232 |
| Peru, new years | 11,845 – 29,900 | 151 |
| Peru, held-out country | 715,000 – 1,794,375 | 214 |
| Taiwan, new years | 29,848 – 89,831 | 151 |
| Taiwan, held-out country | 696,997 – 2,042,232 | 214 |
| Brazil, new years, without case history | 573,768 – 1,726,821 | 211 |
| Brazil, held-out states, without case history | 456,872 – 1,385,651 | 211 |

Note: Input columns of L4 + C\* as recorded by the runner (the 150 columns of L4 in Table S6 plus the control: 1 for C1, 64 for C3, 82 for C2). Held-out-country fits pool the three other countries.

#### Total compute

All LightGBM and negative binomial runs took about 4,700 core-hours (wall time × threads, summed over the 6,180 completed chunks stored in the run directories). This total includes the 2019 tuning and control-selection runs, the sensitivity analyses, the round-3 runs and some superseded runs kept for the record, but not chunks invalidated and moved aside under rows 13–15 and 18. By part: the primary and secondary runs with case history about 2,400 core-hours (3,326 chunks), the analysis without case history about 900 (804), the round-3 runs about 810 (1,722) and the review sensitivities and fixed control panels about 510 (328). TimesFM used 32 minutes of one GPU. Earth Engine extraction used about 182 EECU-hours for AlphaEarth and 8.9 for remote sensing. All runs used one server (AMD EPYC 7551P, 32 cores, 125 GiB RAM). <!-- src: paper/v1/_compute_total.txt (runs/*/chunks/*.done.json seconds × threads over all runs, 4,662 core-hours, 6,180 chunks; threads from config_resolved.yaml for the 146 early chunks without a threads field; computed 2026-11-20); docs/methods/timesfm.md (32 min); project notes (AE 182 EECU-h); docs/features/remote_sensing.md (8.9 EECU-h) -->

#### Derived data to be released

The district-year AlphaEarth table (population-weighted and unweighted means, before and after renormalisation, with population sums and norms), the weekly district panel, the covariate tables, the split and fold definitions, all stored forecasts and the scoring code will be released with the code deposit [to be completed: deposit DOI]. The embedding table is derived from a CC BY 4.0 product; the case panel is derived from OpenDengue (CC BY-SA). <!-- AUTHORS: deposit DOI and repository URL -->

---

## B. Features and controls

**Table S6. Inputs added at each step of the model ladder.**

<!-- src: docs/methods/runner.md "Features"; docs/methods/nohist_arm.md -->

| Level | Block added | Columns | Time alignment |
|---|---|---|---|
| L0 | log(1 + cases) in target week − 52 | 1 | Year before the target |
| L1 | log(1 + cases) at lags 0–11 from the origin (12); target week − 52j and ±1 week, j = 1, 2, 3 (9); sine and cosine of the target's epidemiological week (2) | 23 | Lags end at the origin week |
| L2 | ERA5-Land lags 0–11 of mean temperature, precipitation and humidity (36); 4-, 8- and 12-week rolling means of mean, minimum and maximum temperature, precipitation and humidity (15); population-weighted | 74 | Ends at the origin week |
| L3 | NDVI, day LST and night LST, population-weighted, for the 3 latest complete months (9); night lights and built-up share (2) and log(1 + population) (1) for year y − 1 | 86 | Months ending before the origin month; year before the target's epidemiological year |
| L4 | AlphaEarth population-weighted mean for year y − 1, renormalised (64) | 150 | Year before the target's epidemiological year |
| N3 | L3 without the 21 case-derived columns | 65 | As L3 |
| N4 | L4 without the 21 case-derived columns | 129 | As L4 |

Note: Column counts are cumulative and are given for Brazil.

L0–L2 pass a code assertion that they contain no district-specific input. Weekly inputs are read through a function that asserts the source week is at or before the origin; monthly and yearly inputs through one that asserts the source period ends before the limit. <!-- src: docs/methods/runner.md "Adding a feature level" -->

**Table S7. Location controls.**

<!-- src: docs/methods/controls.md; src/pop/features/controls.py; docs/methods/nohist_arm.md (C6) -->

| Control | Type | Columns | Definition | Where defined |
|---|---|---|---|---|
| C1 | Historical risk | 1 | Mean log(1 + cases) over panel years before 2018 (Brazil 2014–2017), gap-flagged weeks dropped. S1: the district's own value, identical for training and test rows and at every origin. S2–S4: inverse-distance (1/(d + 1 km)) mean of the 5 nearest training districts' values; training districts get a matched leave-out value (S2 excludes their own state, S3 neighbours within D, S4 only themselves) | S1–S4 |
| C2 | Geographic | 82 | Latitude, longitude and 80 orthonormal real spherical harmonics of degree 1–8, no constant term [@russwurm2024location; @klemmer2025satclip] | All |
| C3 | Identifier (S1–S4); dimension-matched noise (S5) | 64 | One fixed source map per seed and country, used in every year: district i gets the real year y − 1 AlphaEarth vector of its source district. S1 and S5: a random permutation of the country's districts; the identity permutation is rejected, but the permutation is not a derangement, so occasionally a district keeps its own vector (about one per country and seed). S2–S4: training districts are permuted among themselves, and each held-out district gets a training district drawn at random (with replacement), never itself | All |
| C4 | Geographic | 64 | 64 Gaussian random fields per country, exponential covariance exp(−d/r) in great-circle distance, standardised within country; r fitted to the AlphaEarth semivariogram (Brazil 8,483 km, Colombia 705 km, Peru 148 km, Taiwan 27 km); drawn only on districts with coordinates | All |
| C4s | Geographic | 64 | C4 with r = min(D, fitted range): Brazil 225 km, Colombia 130 km; equal to C4 in Peru and Taiwan, so not a separate candidate there | Brazil, Colombia, S5 |
| C5 | Snapshot | 64 | AlphaEarth 2023 for every target year | All |
| C6 | Identifier | 1 | District ID as one LightGBM categorical input | S1 only |

Note: Each control replaces the AlphaEarth block (L3 + Ck) or is added beside it (L4 + Ck). In the held-out-country split, C3 gives each district the embedding of another district of the same unseen country, so it tests the cost of 64 extra columns of realistic values rather than district identity; we call it a dimension-matched noise control there. Districts without a polygon or point (Belén de Bajirá in Colombia; two non-spatial "other" buckets in Taiwan) get missing (NaN) values for C1, C2, C4 and C4s, which LightGBM routes as missing; they are excluded from scoring. <!-- src: src/pop/features/controls.py _perm (rejects only the identity permutation), c3_source_map docstring; ../audits/final_round/RC_repro_audit.md M3, L6 -->

<!-- src: C4 ranges: ../audits/review_round/R1_timing_leakage.md section 0 (BR 8483, CO 705, PE 148 km); docs/methods/controls.md (C4s rule; PE/TW fitted 148/27 km). Taiwan's fitted range (27 km) is from docs/methods/controls.md. -->

Controls are rebuilt for every split, fold, origin and seed. Districts are located by a polygon representative point. C1 does not change when every row from 2018 on, or every test-district row, is replaced by an extreme value (tested). <!-- src: docs/methods/controls.md "Leakage guarantees" -->

### B1. Selection of the location control (rule v2)

For each cell, every candidate control k is added to the reference model and scored at the 2019 origin (trained on 2018 targets, scored on 2019 targets, horizons 1 and 4). The score $\mathrm{Score}_k$ is the mean WIS on log(1 + cases) over rows (not week-weighted), averaged over seeds; C3, C4 and C4s use three seeds and the other candidates one. Candidates whose forecasts are bitwise equal to the reference model's are dropped as degenerate. With $\sigma_{\mathrm{seed}}$ the within-candidate seed standard deviation pooled over the multi-seed candidates of the cell and $n_k$ the number of seeds of candidate k,

$$\mathrm{SE}_k = \frac{\sigma_{\mathrm{seed}}}{\sqrt{n_k}}, \qquad \mathcal{T} = \left\{k : \mathrm{Score}_k - \mathrm{Score}_{\mathrm{best}} \le 2\sqrt{\mathrm{SE}_{\mathrm{best}}^2 + \mathrm{SE}_k^2}\right\},$$

so single-seed candidates (C1, C2, C5, C6) have $\mathrm{SE}_k = \sigma_{\mathrm{seed}}$. C\* is the first member of the tie set $\mathcal{T}$ in the priority order C1 > C3 > C2 > C4s > C4 > C5 (without case history: C3 > C2 > C6 > C4s > C4). If $\sigma_{\mathrm{seed}}$ is zero or undefined the cell is marked uninformative and C\* is the first non-degenerate candidate in priority order. <!-- src: scripts/run/select_control.py docstring (lines 20-30) and selection function (lines 125-151) -->

The priority order puts the controls that most directly encode a district's own dengue history or identity first (C1, then the shuffled embedding C3, which keeps the embedding's dimension and distribution), then smooth geographic controls from the most flexible (coordinates with harmonics) to the least, and the 2023 snapshot last because it uses later imagery. The plain reference model was not a candidate, so a control was always selected, even where every candidate scored worse than L3 at 2019 (11 of 14 cells; Table S22). A "no control" rule is reported as a sensitivity analysis (Supplementary Results, Table S45). <!-- src: T4_cstar_selection.csv wis_log_2019 (a candidate below L3 only in BR_S1 C1, CO_S5 C2, TW_S1 C3; 11 of 14 cells with every candidate worse); ../audits/final_round/RC_repro_audit.md M4 -->

---

## C. Models and hyperparameters

#### LightGBM

Quantile objective on log(1 + cases), one booster per quantile (9) and horizon; learning rate 0.05; 400 rounds; feature fraction 0.9; bagging fraction 0.8 every iteration; L2 penalty 1; deterministic, row-wise histograms. Quantiles are back-transformed, clipped at 0 and sorted; a scan of the 77,187,144 stored forecasts found no crossed or missing quantiles (crossing before sorting was not logged). <!-- src: docs/methods/runner.md "Models and tuning"; docs/results/review/RA_summary.md RA7 -->

#### Tuning

Grid: leaves {31, 127} × minimum rows per leaf {100, 1,000}. Criterion: mean pinball loss on log(1 + cases) at quantiles 0.1, 0.5, 0.9 and horizons 1 and 4; train 2018, validate 2019; level L1; seed 0. Choice: Brazil 127/100 (validation 0.07406 vs 0.07428 for 31/100); Colombia, Peru and Taiwan 31/100. One configuration per country is used for every level, control and split. S5 uses Brazil's configuration (127 leaves; so Taiwan held out, the cell with the largest loss, used 127 leaves), or Colombia's (31 leaves) when Brazil is held out. The no-history arm uses Brazil's L1 configuration, which was tuned on a model with case history. <!-- src: docs/results/review/RF_summary.md (0.07406/0.07428); docs/methods/split_pipeline.md "Params"; docs/plans/deviations_from_protocol.md "No-history parameters" -->

#### Per-level tuning (sensitivity)

Tuning each level separately in Brazil gave L1 and L2 127/100 and L3 and L4 31/100. The gap between the best and second-best validation loss was 0.29% for L1, 0.03% for L2, 0.06% for L3 and 1.36% for L4. On the Brazil S1 test years, the difference between L3 at 31 and at 127 leaves was about eight times the shared-configuration embedding gain pooled over horizons 1 and 4 (6.5–14 times per horizon, primary rows), which motivated one shared configuration (D2); before the origin-year filter the figure was about seven. <!-- src: ../audits/review_round/R10_fact_check.md section B (tuning gaps) and items 6a, 6b (pre-filter, about 7x); primary rows computed from T2_ladder_long.csv BR_S1_perlevel vs BR_S1 L3 and BR_S1 L3 vs L4 (7.7 pooled h{1,4}; 13.7, 7.7, 7.3, 6.5 by horizon) -->

#### Taiwan

At the 2019 tuning origin Taiwan had 95 non-zero training targets (33 townships) and 56 non-zero validation targets (26 townships), so its tuning and C\* choice are nearly uninformative. Taiwan S1 is therefore also run with Brazil's configuration and C\* as a sensitivity analysis. <!-- src: docs/methods/s1_pipeline.md "Pre-flight findings" -->

#### Baselines

L0: the quantile τ is expm1(log1p(y at t − 52) + the τ-quantile of the training errors log1p(y_t) − log1p(y_{t−52})), clipped at 0. Negative binomial: an NB2 regression on raw counts with the L1 inputs and an intercept, fitted by L-BFGS from a Poisson start, with quantiles from the fitted distribution; not tuned. TimesFM 2.5 (checkpoint `google/timesfm-2.5-200m-pytorch`), zero-shot on each Brazilian district's log(1 + cases) history up to the origin (at most 573 weeks), deciles sorted and clipped at 0; Brazil S1 only. <!-- src: docs/methods/runner.md "L0 quantile method", "Models and tuning"; docs/methods/timesfm.md -->

---

## D. Information available to each model

"Outcomes" means case counts. "Held-out" means the districts scored in a split's test fold. For test year Y the training targets are epidemiological years 2018 to Y − 1.

**Table S8. Information used at each step of the analysis, by split.**

<!-- src: ../audits/review_round/R1_timing_leakage.md section 0 (code references there) -->

| Step | New years (S1) | Held-out states (S2) | Held-out regions (S3) | Held-out districts (S4) | Held-out country (S5) |
|---|---|---|---|---|---|
| Final model fit | All districts, targets 2018 to Y − 1 | Training districts only | Training districts minus the buffer | Training districts | The other three countries |
| Hyperparameters | Country L1 tuning at 2019 (train 2018, validate 2019), all districts | The same S1 tuning, so held-out districts' 2018–2019 outcomes informed the choice | As S2 | As S2 | Brazil's (Colombia's when Brazil is held out); no held-out-country outcome used |
| C\* selection | All districts, 2019 outcomes | Train on training districts (2018), score held-out districts' 2019 outcomes | As S2, held-out blocks | As S2, held-out districts | Held-out country's 2019 outcomes |
| C1 value | Own mean log(1 + cases) before 2018 | Held-out: distance-weighted mean of the 5 nearest training districts' pre-2018 means. Training: the same, excluding their own state | As S2; training districts exclude neighbours within D | As S2; training districts exclude only themselves | Not defined |
| C3 value | Fixed random permutation of the country's districts (a district can occasionally keep its own vector) | Held-out district gets a random training district's series (never its own) | As S2 | As S2 | Fixed permutation within the held-out country (a district can occasionally keep its own vector) |
| C4/C4s range | Fitted on AlphaEarth 2017–2018 of all districts (covariates only, no outcomes) | As S1 | As S1 | As S1 | Per country, as S1 |
| Buffer D | – | – | Correlograms of deseasonalised 2014–2019 case series of all districts, held-out included (pre-test; Section D3) | – | – |
| Fold construction | – | Admin1 units assigned greedily by district count | k-means on centroids | Random, stratified by Admin1 | – |
| District universe | Districts that ever reported a case, through the end of the data (hindsight) | Same | Same | Same | Same |
| LST screen | Per district and calendar month, median of its own LST over years ≤ 2017 (off in Brazil S1–S4) | Same | Same | Same | Same (on for all countries) |
| Test-time inputs of held-out districts | Own lagged cases, climate, remote sensing, population, AlphaEarth y − 1 | Same (own lagged cases are used) | Same | Same | Same |
| Scoring exclusions | No-polygon districts, incomplete weeks (rule uses ±2 weeks and the same year, i.e. later weeks), Espírito Santo from 2019-12-29 | Same | Same | Same | Same |

### D1. Where held-out outcomes enter

Held-out districts' outcomes enter in three places, all before the test years: hyperparameter choice in S2–S4 (2018–2019 outcomes), C\* selection in S2–S5 (2019 outcomes) and the S3 buffer distance (2014–2019 outcomes). The district universe uses outcomes from every year. No test-year (≥ 2020) outcome of a held-out district enters any fit. <!-- src: ../audits/review_round/R1_timing_leakage.md section 0 -->

### D2. Look-ahead removed by the origin-year filter (D24)

Yearly inputs are keyed to the target's epidemiological year, and each annual model is trained on labels up to the last week of Y − 1. Rows whose origin falls in Y − 1 therefore saw later information.

**Table S9. Share of scored rows affected by each New Year look-ahead.**

<!-- src: ../audits/review_round/R1_timing_leakage.md section 1a table -->

| Horizon | Yearly-input look-ahead (first h target weeks of Y) | Training-label look-ahead (first h − 1 weeks) | Maximum weeks of labels after the origin |
|---|---|---|---|
| 1 | 1.91% | 0 | 0 |
| 2 | 3.83% | 1.91% | 1 |
| 3 | 5.74% | 3.83% | 2 |
| 4 | 7.66% | 5.74% | 3 |
| Pooled h 1 and 4 (primary) | 4.79% | 2.87% | |

Note: h is the forecast horizon in weeks. The shares are identical in every cell.

The filter keeps a row only if the epidemiological year of its origin week (the calendar year of the week's Wednesday) equals the test year. On kept rows, target-keyed and origin-keyed yearly inputs coincide and every training label is dated at or before the origin. In the three within-country Brazilian cells the dropped rows favoured L4 slightly, so the look-ahead did not cancel between models. <!-- src: ../audits/review_round/R1_timing_leakage.md section 1a/1b and "Resolution" -->

**Table S10. Information dated after the origin that the origin-year filter does not remove.**

<!-- src: ../audits/review_round/R1_timing_leakage.md section 1c; ../audits/review_round/R8_literature.md section 4; docs/research/data_and_tools.md ERA5-Land row -->

| Item | Why it is later than the origin | Models affected | Direction |
|---|---|---|---|
| Case counts | One snapshot of final revised counts; no reporting delay except the delay-2 sensitivity | All | Unknown; flatters all models |
| ERA5-Land | Reaches Earth Engine about 3 months after real time | L2 and above | Shared |
| GHSL population and weights | Product released 2023; epochs 2015, 2020, 2025 (2025 a projection); climate weights use the nearest epoch, so 2023+ weeks use 2025 | L2 and above | Shared |
| AlphaEarth model | Trained on imagery "covering 2017 to present", production model with labels through 2023–2024; annual layers released 30 July 2025. The imagery period overlaps every test year (2020–2024) | L4, C3, C5 | Favours embeddings, so it makes the observed lack of gain more, not less, convincing |
| C5 (2023 static embedding) | 2023 imagery used for 2020–2022 targets | C5 only (never selected) | Favours the control |
| District universe | Districts that ever reported a case; 565 enter in 2018 or later (Brazil 507, 111 first in 2024; Peru 28; Taiwan 18, all in 2023; Colombia 12) | All | Shared |
| Incomplete-week exclusion | Rule uses later weeks of the same year | Scoring only | Shared; test-year effect 2 Peruvian department-weeks |

<!-- src for late-entry counts: docs/data/completeness_v1.md "Other exclusion files"; ../audits/review_round/R10_fact_check.md item 2 -->

A late-entry sensitivity (restricting the universe at origin Y to districts first seen before Y) is supported by the code but was not run. <!-- src: ../audits/review_round/R1_timing_leakage.md section 1c last row -->

### D3. Buffer geometry of the held-out-regions split

The buffer distance D was estimated on 2014–2019 only (no test year), from districts with at least 10 weeks with cases (Brazil 4,249; Colombia 806). For each distance bin we computed the mean pairwise correlation between districts' weekly log(1 + cases) residuals under two definitions: the protocol residuals (district mean and week-of-year effects removed) and residuals that also remove each calendar week's national mean. D is the larger of the two distances at which these correlograms first fall below 0.1. In Brazil the protocol correlogram levels off at about 0.11 out to 2,000 km (national co-movement that no buffer can remove), so only the second crossing exists there: D = 225 km. In Colombia the crossings are 130 km and 80 km, so D = 130 km. Every training district within D of any held-out district of the fold is dropped from training. <!-- src: docs/methods/splits.md "Buffer distance D" -->

The buffer uses polygon centroids, while C1, C2 and C4 use representative points. Under representative-point distances, 44 Brazilian and 13 Colombian training district-folds (about 0.23% and 0.38% of training memberships) lie within D of a held-out district; the minimum train–test distance in a fold is 161–218 km in Brazil (D = 225 km) and 122–146 km in Colombia (D = 130 km). <!-- src: ../audits/review_round/R1_timing_leakage.md section 3 -->

### D4. Tuning within folds

S2–S4 reuse the country's S1 tuning, which saw held-out districts' 2018–2019 outcomes. An automated AI agent reran the same search within each fold's training districts only (no held-out or buffer district contributes). The reruns over all districts reproduce the stored S1 tuning to every printed digit. <!-- src: docs/results/review/RF_summary.md -->

**Table S11. Tuning repeated within each fold's training districts.**

<!-- src: docs/results/review/RF_summary.md table and verdict -->

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

## E. Inference, size simulation, supporting and sensitivity analyses

### E1. Primary estimator and test

For a gain and a cell, let $g$ be the seed-averaged WIS difference of one row. The weekly value $d_{h,t}$ is the mean of $g$ over districts at horizon $h$ and target week $t$, and $d_t$ is the mean of $d_{h,t}$ over the horizons present (1 and 4). The estimate $\bar d$ is the mean of $d_t$ over the $T$ test weeks. The Diebold–Mariano (DM) statistic uses the EWC long-run variance with $B$ cosine terms and a $t$ reference distribution with $B$ degrees of freedom ($B$ = 16 in Brazil and Taiwan, 11 in Colombia and 13 in Peru), together with the HLN factor at $h = 4$. Ten cells average seeds 0 to 2 (Brazil S1 and S5, Colombia S1 to S4, Peru S1 and S5, Taiwan S1 and S5; with Peru and Taiwan held out only for the excess gain, row 53); the other cells use one seed, so their intervals condition on one fit. <!-- src: T1_primary_family.csv n_seeds; docs/results/FINAL_RESULTS_BRIEF.md section 1 --> The statistic and its parts are <!-- src: docs/results/review/RC_summary.md "What population the inference refers to" (1.34) --> <!-- src: src/pop/eval/estimands.py infer_estimand; src/pop/eval/stats.py; T1_primary_family.csv df -->

$$\begin{aligned}
\mathrm{DM} &= \frac{\bar d}{\mathrm{SE}}, & \mathrm{SE} &= \frac{\mathrm{SE}_{\mathrm{EWC}}}{c_{\mathrm{HLN}}},\\
B &= \left\lfloor 0.4\,T^{2/3}\right\rfloor, & c_{\mathrm{HLN}} &= \sqrt{\frac{T + 1 - 2h + h(h-1)/T}{T}}.
\end{aligned}$$

The 95% and 90% intervals are $\bar d \pm t_B\,\mathrm{SE}$, so a 95% interval excludes zero exactly when $p < 0.05$. The HLN factor at $h = 4$ is applied to the series pooled over horizons 1 and 4; because the correction grows with $h$, this is the conservative choice. TOST rejects both one-sided null hypotheses when the 90% interval lies inside ±1% of WIS(L3), where WIS(L3) uses the same week-pooled mean. The minimum detectable effect is $(t_{B,0.975} + t_{B,0.80})\,\mathrm{SE}$, unadjusted; Holm-adjusted thresholds are about 1.34 times larger.

The WIS uses the median and the nine deciles, that is K = 4 central intervals (20%, 40%, 60% and 80%) plus the median, normalised by K + ½. It is therefore not on the same scale as the 23-quantile WIS of the forecast hubs (row 36). Unless a table says "row mean", a mean WIS in this paper is week-weighted: the mean over target weeks of the within-week mean over districts and horizons.

#### Labels and counting

Each cell's label in Table 2 combines the Holm-adjusted DM test with the Holm-adjusted TOST, for example "Small loss; within ±1%" or "Inconclusive" (neither a significant difference nor shown equivalence). A loss (gain) is an excess gain below (above) zero with Holm-adjusted p < 0.05; it is "small" when inside ±1%. A nominal p < 0.05 alone is never counted. <!-- src: docs/plans/deviations_from_protocol.md row 27; T1_primary_family.csv plain_label -->

#### Margin

The 1% value was the original protocol's threshold for a material embedding gain (the identity-share gate; row 9); its use as an equivalence margin was decided after the Brazil and Peru S1 results. On the log scale, WIS differences behave roughly like relative errors, so 1% of Brazil's WIS(L3) (about 0.0017) is roughly a 0.2% change in the typical ratio of forecast to observed (1 + cases). <!-- src: T1_primary_family.csv BR_S1 WIS_ref 0.1675; exp(0.00168) − 1 = 0.17% --> Internal anchor: zero-shot TimesFM had 13% higher WIS than LightGBM L1 in Brazil S1 (relative WIS against L0 0.411 vs 0.362). <!-- src: S1_baselines.csv BR_S1 pooled 1,4 wis_log 0.19284 vs 0.16996; rel_wis_vs_L0 0.411 vs 0.362 --> External anchor: in the US COVID-19 Forecast Hub, adjacent leading models differed by 0.01–0.02 relative WIS, about 1.6–3.3% of the leader's WIS [@cramer2022covidhub]. That comparison is on the case scale, while our margin is a share of WIS on log(1 + cases), so it is indicative only. Margins of ±0.5% and ±2% are reported (Table S24). <!-- src: ../audits/review_round/R8_literature.md section 2 -->

#### Inference population

Weeks are the sampling unit, for this fixed set of districts, fitted pipelines and test seasons. Spatial-split folds are partitions, not samples. Inference about new seasons would need the between-season variance, which a season-level t-test with 2–4 degrees of freedom can barely estimate. <!-- src: docs/results/review/RC_summary.md "What population the inference refers to" -->

### E2. Robustness checks

- EWC with B = 4 cosine terms (fewer terms, more robust to low-frequency variation, less power).
- IAAFT-calibrated p. 2,000 windowed IAAFT surrogates [@schreiber1996iaaft] of d_t: a circular surrogate of length 8T with the real marginal distribution and the real span-3-smoothed spectrum (held flat below frequency 1/T), centred at zero, from which a random length-T window is taken. The p-value is (1 + k)/(1 + 2,000), where k counts surrogates whose |DM statistic| is at least the observed one.
- Delta-method interval for 100 × G / WIS(L3), with WIS(L3) estimated (EWC + HLN on the linearised weekly series).
- Case scale: the excess gain with WIS on raw counts (expm1 of the log-scale quantiles, clipped at 0).
- All rows: without the origin-year filter.
- Old exclusions: without the Espírito Santo exclusion.
- Circular block bootstrap of d_t with 52-week blocks; descriptive only, because T = 154–256 weeks gives three to five blocks.

<!-- src: docs/plans/deviations_from_protocol.md row 28; scripts/analysis/rk_compute.py iaaft_pvalue, robust_table; docs/results/review/RC_summary.md "What was tested"; docs/results/review/RA_summary.md RA6 -->

### E3. Size simulation

We measured the size of the primary test and its alternatives on null series calibrated to each cell's own centred d_t (2,000 replications per cell and generating process). Generating processes: windowed IAAFT (multi-year swings treated as stationary noise), IAAFT with doubled power below frequency 2/T (stress test), annual harmonics plus AR(1) with resampled heavy-tailed residuals (ARX), and Gaussian AR(1) with φ = 0.5 and T = 104. Real placebos were seed-vs-seed differences of the same model: 21 Brazil S1 series (T = 261) and 33 series from the 2019 control runs (T = 52). <!-- src: docs/results/review/RC_summary.md "What was tested" -->

**Table S12. Empirical size of the tests at a nominal 5% level.**

<!-- src: docs/results/review/RC_summary.md size table -->

| Generating process | EWC + HLN (primary) | EWC + HLN, B = 4 | Newey–West (NW94) | 52-week block bootstrap |
|---|---|---|---|---|
| AR(1), φ = 0.5, T = 104 | 0.054 | 0.046 | 0.110 | 0.294 |
| ARX, median over cells | 0.026 | 0.034 | 0.10 | 0.18–0.21 |
| IAAFT, median over cells | 0.048 | 0.036 | 0.20 | 0.18–0.21 |
| IAAFT low-frequency stress, median over cells | 0.120 | 0.048 | 0.30 | 0.18–0.21 |
| IAAFT, worst cells (BR S1, BR S2, BR S3, CO S5, PE S1) | 0.10–0.22 | ≤ 0.15 | 0.10–0.50 (any process) | 0.15–0.31 (any process) |
| Seed placebo, Brazil S1 (21 series) | 2 of 21 rejected | 1 of 21 | 4 of 21 | 3 of 21 |
| Seed placebo, 2019 controls (33 series, T = 52) | 4 of 33 | 5 of 33 | 13 of 33 | undefined |

Note: Monte Carlo standard error about 0.5 percentage points. Computed before the origin-year filter and the Espírito Santo exclusion.

#### Conclusions

The primary test is acceptably calibrated when d_t is short-memory around a fixed mean, as in most cells (size ≤ 8% under ARX), and HLN changes size by at most 1 point. It is oversized (10–22%, up to 28% under the stress test) in cells whose gain drifts across seasons, if that drift is treated as noise: Brazil S1, S2, S3, Colombia S5 and Peru S1. Equivalence statements for Brazil S1, Brazil S2 and Colombia S5 therefore hold "assuming no multi-season drift". Newey–West, the h − 1 HAC and both block bootstraps are badly oversized. In this simulation analysis, which preceded the origin-year filter and the Taiwan 2021 runs, only Colombia S4 lost Holm significance with B = 4 (Holm-adjusted p 0.10). On the final primary rows (Table 2 and Table S26; Holm over 14 cells), Brazil S5, Colombia S1, S3 and S4 and Taiwan S5 lose Holm significance with B = 4, so only Colombia S2 keeps it, and Colombia S4 and Taiwan S5 lose it with IAAFT calibration; the direction of all six losses is unchanged. <!-- src: T1_primary_family.csv B4_Holm_p, p_iaaft_Holm --> In the final IAAFT calibration of the primary rows (Table S47), the size of the nominal 5% test was 14% to 18% in Brazil S1, S2, S3 and S4 and Colombia S5, so equivalence statements for these cells also assume no multi-season drift. <!-- src: R3_A8_iaaft_equivalence.csv size_nominal5 (BR_S4 0.149) --> Power to detect a gain of 1% of WIS(L3) is about 1.00 in Brazil S2/S3/S5 and Colombia S1–S4, 1.00 in Colombia S5, 0.83–0.88 in Brazil S1, Taiwan S1 and Peru S1, 0.53 in Peru S5 and 0.08 in Taiwan S5. <!-- src: docs/results/review/RC_summary.md "Power", "Do the primary-family conclusions change?", "Verdict" -->

<!-- Note: RC_summary.md was computed before kit v3 (all rows, before the origin-year filter and the ES exclusion); current robustness p-values are in T1 (B4_Holm_p, p_iaaft_Holm). -->

### E4. Supporting analyses (exploratory, no multiplicity adjustment; D33)

<!-- src: docs/results/review/RD_summary.md sections 1–6; docs/results/review/RB_summary.md sections 1–3; docs/results/review/RA_summary.md RA1, RA7; docs/plans/deviations_from_protocol.md row 33 -->

- S1 baselines: WIS on log(1 + cases) of L0, negative binomial, LightGBM L1–L4 and L3/L4 + C\*, and TimesFM (Brazil), with relative WIS against L0 on rows scored by every model.
- Additive stratum contributions: per horizon and week, d = Σ_s w_s d_s with w_s the stratum's row share, so the contributions (as % of the cell's WIS(L3)) sum exactly to the total. Stratum estimates on their own rows are also reported as % of the stratum's own WIS(L3); they are not shares of the total.
- Outbreak weeks: cases ≥ max(5, the district's 90th percentile of weekly cases over 2013–2019).
- Weighted means: inside each (horizon, week) mean, weights equal to district population in the target year, or to the district's mean weekly cases over 2013–2017 plus 1.
- Causal recalibration: separately for L3 + C\* and L4 + C\*, additive per-quantile shifts on the log scale fitted only on earlier test years (the first test year unadjusted), either one shift per quantile ("global") or per bin of the forecast median ("Mondrian").
- Mechanism: the change in the mean 0.9 quantile between L4 + C\* and L3 + C\* on rows with zero cases, and the share of the zero-row loss from quantiles above the median.
- Embedding similarity (S2–S5): the maximum (and top-5 mean) cosine similarity between a held-out district's renormalised year y − 1 embedding and the training districts' vectors [@meyer2021aoa], against the district's gain.
- Per-year gains with context flags (COVID-19 years 2020–2021, Peru 2023, Brazil 2024).
- Strata for RQ4 (exploratory): population tercile (year before the test year), number of years 2014–2017 with at least one case (0, 1–2, 3–4) and change in GHSL built-up share 2010–2015 (tercile).
- Coverage of the 40% and 80% intervals overall and on weeks with cases.

### E5. Sensitivity analyses

**Table S13. Sensitivity analyses and their status.**

| Analysis | Cells | Estimands | Status |
|---|---|---|---|
| Three seeds (primary) vs seed 0 | Brazil S1 | All three | Done |
| Per-level tuning (original protocol) | Brazil S1 | All three | Done |
| Fixed control panel C1, C2, C3, C6 | S1, all countries | Control and excess gains | Done (Table S36; Brazil C3 and C6 also in Table S37) |
| Yearly inputs keyed to the origin year (strictly causal) | Brazil S1 | Embedding gain only | Done (Table S37) |
| Two-week reporting delay in case inputs | Brazil S1 | Embedding gain only | Done (Table S37) |
| Taiwan with Brazil's configuration and C\* | Taiwan S1 | All three | Done |
| Taiwan without 2021 | Taiwan S1, S5 | All three | Done |
| Margins ±0.5% and ±2% | All cells | Excess gain | Done |
| All rows; old exclusions; case scale; B = 4; IAAFT; delta method | All cells | Excess gain | Done |
| Late-entry district universe | All cells | Excess gain | Not run |
| Long training window for L0–L3 (2013 to Y − 1; protocol) | Brazil S1 | Ladder | Not run (row 35) |
| 23-quantile WIS (protocol secondary score) | All cells | All | Not computed (row 36) |
| As planned vs as reported (Table S43) | All cells | Excess and embedding gains | Done (row 44; Table S43) |
| Positive-control ladder gains, margin anchor (Table S44) | S1, all countries | Ladder gains | Done (row 41; Table S44) |
| "No control" selection rule (Table S45) | All cells | Embedding or excess gain | Done (row 40; Table S45) |
| Per-year trend test (Table S46) | All cells | Excess and embedding gains | Done (row 42; Table S46) |
| Equivalence at ±0.5/1/2% with EWC and B = 4 SEs (Table S47) | All cells | Excess gain | Done (row 43; Table S47) |
| Outcome-agnostic checks (Table S48) | All cells; Colombia district-years | Excess gain, coverage, width | Done (row 45; Table S48) |
| Embedding stability (Table S49) | All countries | Cosine similarity | Done (row 46; Table S49) |
| Information probe (Table S50, Figure S4) | All countries | Cross-validated skill | Done (row 47; Table S50) |
| Representation variants V1–V4 (Table S51) | CO S1, CO S2, PE S1, TW S1, BR S2 | Variant gains | Done (row 48; Table S51) |
| Seeds 0–2 (Table S52) | Colombia, Peru, Taiwan cells; Brazil S5 | All three | Done (rows 49 and 53; Table S52) |
| Taiwan new-years ladder and panel with 2021 (Table S53) | Taiwan S1 | Ladder, control panel | Done (row 50; Table S53) |
| No case history, Colombia held-out states (Table S54) | Colombia S2 | All three | Done (row 51; Table S54) |
| Equal-budget tuning (Table S55) | Colombia S1 | Excess gain | Done (row 52; Table S55) |
| No-history identifier panel N3 + C6, N4 + C6 (exploratory) | Brazil S1 no-history | Control and excess gains | Done (row 38; results below) |

<!-- src: T6a_sensitivities.csv variant and variant_status (all available, final kit 2026-11-20); RE_summary.md; RE_control_panel.csv; docs/results/review/RH_nohist_c6.md; T1_primary_family.csv robustness columns; ../audits/review_round/R1_timing_leakage.md section 1c (late entry not run). Note: RE_summary.md says the control panel uses the v3 primary rows (origin-year filter, exclusions v2), while NOTES_FOR_WRITERS item 32 says all rows; see notes_B. -->

The reporting-delay sensitivity shifts only the case-history inputs two weeks back; it is not an evaluation on data vintages. The origin-keyed and delay runs cover L3 and L4 only, so they are compared with the embedding gain, not the excess gain. None of the Brazilian sensitivity analyses gave a significant gain: the embedding gain was +0.26% (95% CI −0.29 to 0.82) with strictly causal yearly inputs and +0.60% (−0.56 to 1.76) with a two-week reporting delay, against +0.29% for seed 0 of the primary runs; the excess gain was +0.28% (−0.27 to 0.82) with C3 and +0.30% (−0.12 to 0.71) with C6 in place of C\*. <!-- src: T6a_sensitivities.csv BR_S1_yref, BR_S1_delay2, BR_S1_ctrlC3, BR_S1_ctrlC6; S2_control_panel.csv brazil G_emb_pct --> In the exploratory identifier panel without case history (row 38; Brazil S1, seed 0), the district identifier C6 improved N3 by +1.98% (95% CI 0.76 to 3.21; p = 0.003), less than coordinates (+3.30%), and with C6 in the model the embeddings changed WIS by −0.04% (−1.24 to 1.16). <!-- src: docs/results/review/RH_nohist_c6.md table (C6 G_id +1.98 [+0.76, +3.21] p 0.003; C6 G_excess −0.04 [−1.24, +1.16]; C2 G_id +3.30) --> <!-- src: ../audits/review_round/R1_timing_leakage.md sections 1a, 1c; ../audits/review_round/RESOLUTION_LOG.md section C -->

---

## F. Deviations from the original protocol

The original protocol is the evaluation plan and its design review of 15 November 2026. Rows 1–10 were committed in d8c7944, the no-history arm was pre-specified in bd3ba50, rows 11–17 were recorded in fcc3c38 and the control fixes of rows 13–15 implemented in 9de7386, all on 16 November 2026 before any spatial-split result had been read. Rows 18–23 were committed in e9df1f1 (16 November, 20:29 CST), about three hours before the first spatial-split result (3ca02d7, 23:21 CST). Rows 24–34 were committed in f107238 (18 November, 02:16 CST) after external review, when the S1, S2, S3 and S5 results and Colombia S4 had been seen; only Brazil S4 and the no-history cells were still running. Rows 35–38 were added on 18 November 2026 after review of the full draft and recorded in the deposit commit, after the Brazil S1 no-history result had been read but before the Brazil S4 and no-history Brazil S2 results were read; rows 35–37 record protocol commitments that were not carried out. Rows 39–53 were added on 19 November 2026 after the third review round, when all 13 completed cells had been read (Brazil held-out districts was still blinded); each was specified, and recorded in commit 8001a92, before it was scored, and row 53 before any new seed was seen. <!-- src: ../audits/final_round/RC_repro_audit.md L4; ../audits/final_round/TRIAGE_round3.md sections B, C --> <!-- src: docs/plans/deviations_from_protocol.md rows 35–38 (commit column "2026-11-18 deposit commit") --> Brazil, Peru and Taiwan S1 test-year results were seen before rows 2, 8, 9, 11, 13, 16 and 18–22, so S1 is partly unblinded; the baselines (L0–L2, TimesFM) were also looked at on test years during pipeline development.

Timing of all 53 rows: rows 1–23 (23 rows) were decided after some new-years test results but before any held-out-place result; rows 24–34 (11 rows) after every completed cell except Brazil held-out districts and the analyses without case history; rows 35–38 (4 rows) after the Brazil new-years result without case history; rows 39–53 (15 rows) after all 13 completed cells. Four rows changed the primary estimand after results it affects had been read: row 2 (one shared configuration), row 21 (horizons 1 and 4 pooled in the new-years cells), row 24 (origin-year rows) and row 25 (Taiwan 2021 included, decided after both Taiwan cells had been read; it moved the seed-0 Taiwan held-out excess gain from −11.16% to −17.30% and the Taiwan new-years gain from −0.44% to −0.60%; with seeds 0 to 2 the final values are −18.29% and −0.71%). Row 53 (seed averaging) changes the primary estimates of the cells that gained seeds (Table S52); it changed no conclusion after Holm adjustment over 14 cells, although Brazil held out no longer survives the B = 4 variance with Holm adjustment (Table S26). <!-- src: commit times in the paragraph above; T6a_sensitivities.csv / Table S37 (TW without 2021: S5 −11.16, S1 −0.44); R3_C_seeds.csv T1_seed0_pct TW_S5 −17.30, TW_S1 −0.60; T1_primary_family.csv (final) TW_S5 −18.29, TW_S1 −0.71 --> <!-- src: docs/plans/deviations_from_protocol.md header; docs/results/NOTES_FOR_WRITERS.md items 1–3; git log (commit times) -->

**Table S14. Deviations from the original protocol.**

| # | Change | Reason | Decided after seeing | Commit |
|---|---|---|---|---|
| 1 | C1 under the temporal split = the district's mean log(1 + cases) over the years before the first training target year (Brazil 2014–2017), identical for training and test rows | The first definition (mean of the training targets) leaked each training row's own target: 2019 WIS 0.263 vs 0.175 for plain L3 | 2019 selection-origin results only | d8c7944 |
| 2 | One LightGBM configuration per country, tuned once on L1 at the 2019 origin, for all levels and controls; per-level tuning becomes a sensitivity analysis | Per-level tuning on a nearly flat grid (validation differences 0.03–1.4%) gave L1/L2 127 leaves and L3/L4 31 leaves; on Brazil S1 test years L3 with 127 leaves beat L3 with 31 at every horizon (Holm p ≤ 0.012), a capacity effect several times the embedding gain (about eight times on the primary rows; Section C) | Brazil S1 test years | d8c7944 |
| 3 | S2 = grouped leave-states-out in 5 folds (was one state per fold: 27 in Brazil, 33 in Colombia); Brazil's S3 groups 10 blocks into 5 folds; old versions kept in the code, not run | Compute (the 27-fold S2 was 54% of the total); held-out districts are still in states unseen in training | No | d8c7944 |
| 4 | Spatial splits score horizons 1 and 4 only (S1 keeps 1–4); the random district-week split S0 is dropped; final C\* runs use 1 seed (selection uses 3 seeds for random controls; the protocol said 10); no re-tuning per split | Compute; Brazil S1 selection seed SD about 0.0001 WIS | No | d8c7944 |
| 5 | C1 in S2/S3: training districts get a matched leave-out value (exclude own state in S2, neighbours within D in S3) | With plain leave-one-out, training districts' neighbours were far closer than held-out districts' (median 23 km vs 105–394 km), so training and test values differed in distribution | No | d8c7944 |
| 6 | S5 configuration = the L1 configuration of the largest training country (Brazil; Colombia when Brazil is held out) | No S5-specific tuning origin exists | No | d8c7944 |
| 7 | LST outlier screen for Colombia, Peru and Taiwan (value > 10 °C below the district's calendar-month median from years ≤ 2017 set to missing); off for Brazil S1–S4 | Cloud-contaminated cold MODIS LST (Colombia minimum −42 °C); a QC-bit mask did not remove it | No | d8c7944 |
| 8 | Secondary no-case-history arm added, pre-specified in `docs/methods/nohist_arm.md` before it ran | With case history neither embeddings nor controls helped (Brazil and Peru S1), so identity and place information could not be told apart | Yes (S1 nulls); labelled exploratory | d8c7944; bd3ba50 |
| 9 | Smallest effect of interest = 1% of WIS(L3) (the protocol's ID-share gate); TOST on 90% intervals; minimum-detectable-effect table | A null result needs an explicit margin | Partly (Brazil and Peru S1 seen) | d8c7944 |
| 10 | Deferred: TimesFM + LightGBM residual hybrid, monthly replication arm, PDFM (L5), reporting-lag analysis on data vintages | Time and scope | No | d8c7944 |
| 11 | Inference: DM test on the weekly cross-district mean loss difference with EWC variance, fixed-b t and HLN; interval d̄ ± t_B · SE; TOST on the 90% version; the bootstrap becomes a sensitivity analysis with 52-week (not 8-week) blocks | Weekly loss differences stay autocorrelated at lags 8 and 52 (about 0.42–0.43); the 8-week bootstrap excluded 0 where DM p was 0.3–0.5 | Yes (Brazil S1); before any spatial result | fcc3c38 |
| 12 | Primary family = pooled-horizon excess gain, history arm, 14 country × split cells, Holm; embedding and control gains, per-horizon and per-year results secondary (the embedding gain is co-primary since row 39) | The family had not been fixed | Yes (S1); before any spatial result | fcc3c38 |
| 13 | C3 uses one fixed source map per seed across all years | A new permutation each year meant C3 was not a stable identifier (0–0.05% of districts kept their source) | Found by an automated AI-agent audit (see Use of AI tools) after Brazil S1 test results; C3 had been scored at the 2019 origin only | fcc3c38; code 9de7386 |
| 14 | C1 in S2–S4 = matched neighbour mean of the neighbours' pre-training-year mean log(1 + cases) (was their 2018 to Y − 1 targets) | In-period neighbour targets are contemporaneous with training targets (a diluted leak) and differ from the S1 definition | No spatial result read | fcc3c38; code 9de7386 |
| 15 | C4 at two ranges: the fitted range (Brazil 8,483 km) and a short range (C4s) | At 8,483 km C4 is close to a planar trend, not an identifier | No | fcc3c38; code 9de7386 |
| 16 | Brazil S1 primary runs get 2 extra seeds at horizons 1 and 4; seed SD reported | Per-horizon seed SD (about 0.0001–0.0003 WIS) is of the same order as the excess gain | Yes (Brazil S1) | fcc3c38 |
| 17 | Documented, not changed: yearly inputs keyed to the target year; annual refits train through the end of Y − 1; an origin-keyed sensitivity planned (superseded by row 24) | Automated AI-agent audit | – | fcc3c38 |
| 18 | C4/C4s fields fitted only on districts with coordinates; affected Colombia, Taiwan and S5 runs and the Colombia S1 and Brazil S5 C\* runs were discarded and rerun | Three districts without polygons made every field missing in Colombia and Taiwan, so C4/C4s forecasts equalled L3 (Colombia S1 C\* had in effect been plain L3) | Yes (Colombia S1 2019 selection, Taiwan S1 test results); no spatial result | e9df1f1 |
| 19 | C\* selection rule v2: drop degenerate candidates; tie set within 2 seed SEs of the best; first tie-set member in priority C1 > C3 > C2 > C4s > C4 > C5 (no-history C3 > C2 > C6 > C4s > C4); zero seed SD = "uninformative" | C\* was being decided inside seed noise (Colombia margin 0.00003 vs seed SD 0.00006; Taiwan exact ties broken by sort order) | Yes (Brazil, Peru, Taiwan S1); before any spatial result | e9df1f1 |
| 20 | C4s range = min(D, fitted range); in Peru and Taiwan C4s equals C4 and is not a candidate | C4s had run at a longer range than C4 there; it never won, so no C\* changed | Yes (Peru, Taiwan S1) | e9df1f1 |
| 21 | The primary family pools horizons 1 and 4 in every cell; S1 pooled over 1–4 is secondary | The S1 estimand differed from S2–S5 | Yes (S1); before any spatial result | e9df1f1 |
| 22 | Brazil S1 primary cell uses seeds 0, 1 and 2 at horizons 1 and 4; each estimand uses the seeds common to both its models; seed SD computed where all seeds exist | The manifest listed one seed, and the old fill rule halved the seed SD | Yes (Brazil S1) | e9df1f1 |
| 23 | Scheduler thread budget counts other jobs on the server | Operations | No effect on results | e9df1f1 |
| 24 | Primary scored rows = origin-year rows (drops the first h epidemiological weeks of each test year); all rows reported as a sensitivity | Yearly inputs and annual training labels could postdate the origin (Section D) | Yes (after review) | f107238 |
| 25 | Taiwan 2021 is a test year in TW S1 and TW S5; Taiwan S1 explicitly in the 14-cell family; the old test-year set reported as a sensitivity | Excluding a year because it had no cases is an outcome-based exclusion | Yes | f107238 |
| 26 | Three target strata (weeks with cases, recorded zeros, zero-filled), each with its own estimate and an exact additive contribution to the cell total | "Observed" mixed weeks with cases and zeros listed by the source; stratum estimates do not add up under equal-week weighting | Yes | f107238 |
| 27 | Holm-adjusted TOST, plain labels, margin table at ±0.5/1/2%, and a loss-counting rule (Holm-adjusted p < 0.05; "small" inside ±1%) | Equivalence claims over 14 cells need the same multiplicity control; earlier class words were misleading | Yes | f107238 |
| 28 | Robustness columns: EWC with B = 4, IAAFT-calibrated p, delta-method interval, case scale, all rows | The primary test is oversized under multi-season drift in some cells; the percentage ignored denominator uncertainty | Yes | f107238 |
| 29 | Fixed control panel (S1: C1, C2, C3, C6 each in place of C\*) | The conclusion should not rest on the selected C\* alone | Yes | f107238 |
| 30 | WIS on incidence dropped (never computed); case-scale WIS is the secondary scale | The protocol listed a metric that no code computed | Yes | f107238 |
| 31 | The protocol's RQ4 (year-aligned vs static embeddings) deferred; RQ4 in this paper is the exploratory question on where embeddings help or hurt | Time and scope | Yes | f107238 |
| 32 | N2 (no-history climate-only level) not run | Compute; not needed for any no-history estimand | Yes | f107238 |
| 33 | Supporting analyses added on the primary rows (Section E), all exploratory | Review | Yes | f107238 |
| 34 | Espírito Santo excluded from scoring from 2019-12-29 (Section A6); old exclusions reported as a sensitivity | OpenDengue holds false zeros for the state while InfoDengue shows cases | Yes (found in review) | f107238 |
| 35 | Long-window secondary analysis (L0–L3 trained on 2013 to Y − 1) not run | Compute before the preprint; it does not involve the embeddings (AlphaEarth starts in 2017). Limitation: at the 2020 origin every rung trains on two target years | Yes (after review of the full draft) | Deposit commit, 18 November 2026 |
| 36 | 23-quantile WIS (secondary score) not computed; all scores use the median and the 0.1–0.9 deciles | The fitted models output only the median and deciles, so a 23-quantile WIS would need refitting | Yes (after review of the full draft) | Deposit commit, 18 November 2026 |
| 37 | Taiwan per-outbreak and county-level reporting replaced by per-year results (Table S30) and Taiwan's two cells in the 14-cell family | Taiwan's test years are almost all zeros, so per-outbreak estimates would rest on a handful of weeks | Yes (after review) | Deposit commit, 18 November 2026 |
| 38 | Exploratory no-history identifier panel: N3 + C6 and N4 + C6 on Brazil S1 test years, seed 0, horizons 1 and 4, primary rows (results in Section E5: identifier gain +1.98%, excess gain −0.04%) | Coordinates (the selected C\*) also carry environmental gradients, so a pure identifier is needed to read the no-history result | Yes for other cells; no for these runs (added before they produced any result) | Deposit commit, 18 November 2026 |
| 39 | The embedding gain (L3 → L4) becomes co-primary beside the excess gain and is shown in Table 2 and Figure 2; the "identity gain" is renamed the "control gain" (wording only; code and file names unchanged) | The selected control often scored worse than L3, so the excess gain alone can understate or overstate the embeddings' contribution | Post hoc, after all 13 cells were read; specified before scoring | 8001a92 |
| 40 | Sensitivity selection rule allowing "no control": C\* = none when no candidate beat L3 at 2019 by more than 2 SE; such cells then use the embedding gain (Table S45) | Rule v2 always selected a control, even when all candidates were worse than L3 (11 of 13 cells) | Post hoc, after all 13 cells were read; specified before scoring | 8001a92 |
| 41 | Positive-control ladder gains (L1 → L2, L2 → L3, L1 → L3, L3 → L4) with CIs in every new-years cell, used to anchor the ±1% margin; ±0.5% reported alongside (Table S44) | The ±1% margin was set after the S1 results and needs an empirical anchor | Post hoc, after all 13 cells were read; specified before scoring | 8001a92 |
| 42 | Per-year gains with a weighted trend test on training-window length, and a DM test on 2023–2024 for Brazil (Table S46) | Referees asked whether the null is specific to short training windows | Post hoc, after all 13 cells were read; specified before scoring | 8001a92 |
| 43 | Equivalence at ±0.5/1/2% with both the EWC and the B = 4 standard errors (Table S47) | Equivalence claims should survive the more cautious variance estimator | Post hoc, after all 13 cells were read; specified before scoring | 8001a92 |
| 44 | Supplementary "as planned vs as reported" table (Table S43) | One place to see the effect of every post-result choice on the primary family | Post hoc, after all 13 cells were read; specified before scoring | 8001a92 |
| 45 | Outcome-agnostic checks: Colombian district-years with at least one case; change in 80% coverage and interval width on case and zero weeks (Table S48) | Outcome-defined strata can reward biased forecasts (forecaster's dilemma) | Post hoc, after all 13 cells were read; specified before scoring | 8001a92 |
| 46 | Embedding stability: within-district year-to-year cosine against between-district cosine (Table S49) | Shows how far the yearly embedding acts as a fixed district signature | Post hoc, after all 13 cells were read; specified before scoring | 8001a92 |
| 47 | Information probe: cross-sectional prediction of district burden from embeddings, coordinates and L3 statics (Table S50, Figure S4) | Separates "no dengue information in the embeddings" from "information redundant with case history at 1–4 weeks" | Post hoc, after all 13 cells were read; specified before scoring | 8001a92 |
| 48 | Representation variants V1–V4 (embedding-space risk encoding, PCA-8, causal static 2017–2018 mean, substitution for the L3 block) in five cells; Holm within the variant family only (Table S51) | Referees asked whether a different use of the embeddings would show a gain | Post hoc, after all 13 cells were read; specified before scoring | 8001a92 |
| 49 | Seeds 1–2 for L3, L4, L3 + C\* and L4 + C\* in Colombia (new years, held-out states, regions and districts), Peru and Taiwan (new years) and Brazil held out, and for L3 + C\* and L4 + C\* only in Peru and Taiwan held out (Table S52) | Seed SD is of the same order as several estimates | Post hoc, after all 13 cells were read; specified before any new seed was seen | 8001a92 |
| 50 | Taiwan new-years ladder (seasonal naive, negative binomial, L1, shared-configuration L2) and fixed control panel rerun with 2021 (Table S53) | Removes the 113,430 vs 141,645 row-set split between Taiwan tables | Post hoc, after all 13 cells were read; specified before scoring | 8001a92 |
| 51 | Analysis without case history repeated for Colombia held-out states, exploratory (Table S54) | Checks whether the Brazilian no-history pattern holds in a second country | Post hoc, after all 13 cells were read; specified before scoring | 8001a92 |
| 52 | Equal-budget per-level tuning of L3 + C\* and L4 + C\* in Colombia S1 (Table S55) | Checks whether one shared configuration favoured or penalised the embedding model | Post hoc, after all 13 cells were read; specified before scoring | 8001a92 |
| 53 | A cell's primary estimate becomes the mean over seeds 0–2 wherever all three seeds exist for both models of an estimand; seed 0 alone becomes a sensitivity analysis (Table S43, Table S52) | Brings every cell with extra seeds to the estimator already used for Brazil, new years (row 22) | Post hoc, after all 13 cells were read; decided 19 November 2026 before any new seed was seen | 8001a92 |

<!-- src: docs/plans/deviations_from_protocol.md rows 1–38; rows 39–53 from ../audits/final_round/TRIAGE_round3.md sections A.4, B and C and docs/methods/round3_runs.md, also recorded in docs/plans/deviations_from_protocol.md rows 39–53 (row 2 validation range corrected per ../audits/review_round/R10_fact_check.md section B; row 13 timing per ../audits/review_round/R6_draft_and_medrxiv.md B MEDIUM 7; row 14 "log incidence" corrected to log(1 + cases) per RESOLUTION_LOG.md section B) -->

#### Documented, not changed

(a) The S3 buffer uses centroids; C1, C2 and C4 use representative points (Section D). (b) The no-history arm uses Brazil's L1 configuration. (c) Brazil's per-level control selection ranks the pre-fix C3 and C4 and is used only within the per-level sensitivity. (d) Brazilian rows in S5 use the LST screen, while Brazil S1–S4 do not (the screen flags 0.08%/0.02% of Brazilian district-months). (e) The outbreak threshold window 2013–2019 includes the training years 2018–2019 but no test year. <!-- src: docs/plans/deviations_from_protocol.md "Documented, not changed" -->

---

## G. EPIFORGE 2020 checklist

Table S15 maps each item of the EPIFORGE 2020 checklist [@pollett2021epiforge] to the manuscript; items are paraphrased. <!-- AUTHORS: replace this table with the official EPIFORGE checklist file before submission --> <!-- src: ../audits/review_round/R6_draft_and_medrxiv.md section E -->

**Table S15. EPIFORGE 2020 checklist.**

| # | Item | Where | Status |
|---|---|---|---|
| 1 | Identify the study as forecasting research in the title or abstract | Title; Abstract | Present |
| 2 | Purpose and forecast targets | Introduction; Methods 2.3 (target: weekly cases per district, 1–4 weeks ahead) | Present |
| 3 | Methods in reproducible detail, including fitting and assumptions | Methods 2.2–2.12; Supplementary Methods, A–F | Present; code link in item 9 |
| 4 | Prospective, real-time or retrospective | Methods 2.1: retrospective, from one snapshot of final revised data | Present |
| 5 | Origin of input data, with references | Methods 2.2–2.4; Supplementary Methods, A1 | Present |
| 6 | Source data available, or why not | Data availability statement (OpenDengue and all covariate sources are public; derived panels to be deposited) | Pending: [to be completed] <!-- AUTHORS: public repository URL and Zenodo DOI --> |
| 7 | Data processing | Methods 2.2; Supplementary Methods, A2–A7 | Present |
| 8 | Model type and assumptions, with references | Methods 2.4; Supplementary Methods, B and C | Present |
| 9 | Code available, or why not | Code availability statement; protocol, deviation log and code, with the full commit history, released at [to be completed] <!-- AUTHORS: deposit DOI --> at posting (no separate pre-results deposit was made) | Pending: public repository URL [to be completed] <!-- AUTHORS: public repository URL and Zenodo DOI --> |
| 10 | Validation approach, described and justified | Methods 2.6–2.7; Supplementary Methods, D | Present |
| 11 | Accuracy evaluation, described and justified | Methods 2.8–2.10; Supplementary Methods, E | Present |
| 12 | Comparison with benchmark models, justified | Methods 2.4 (seasonal naive, negative binomial, TimesFM in Brazil); Results 3.1; Tables S17 and S18 | Present |
| 13 | Forecast horizon, described and justified | Methods 2.3: 1–4 weeks, the range used by forecast hubs; horizons 1 and 4 bracket it and are used in S2–S5 to halve compute. Lead times for vector control can be longer; Discussion 4.1 limits the conclusion to one- and four-week forecasts and 4.6 names longer horizons as future work | Present (scope stated) |
| 14 | Forecast uncertainty presented and explained | Quantile forecasts, WIS and interval coverage (Methods 2.8; Results 3.1) | Present |
| 15 | Non-technical summary of results and uncertainty | Abstract; Discussion 4.1 | Partly present (no separate lay summary) |
| 16 | Time-stamped, versioned identifier for forecasts and data | Protocol and code with the full commit history [to be completed] <!-- AUTHORS: deposit DOI --> at posting; Zenodo deposit of code, forecasts and derived data at posting | Pending: [to be completed] <!-- AUTHORS: public repository URL and Zenodo DOI --> |
| 17 | Weaknesses, including data quality and methods | Discussion 4.5; Supplementary Methods, section I | Present |
| 18 | Implications for public-health action | Discussion 4.6 (scoped: no recommendation about operational use) | Present |
| 19 | Generalisability across populations | Discussion 4.2 and 4.5; four-country design and the held-out-country split | Present |

---

## H. Glossary

**Table S16. Glossary of terms and abbreviations.**

| Term | Meaning |
|---|---|
| Admin1, Admin2 | First- and second-level administrative units. Admin1: states (Brazil), departments (Colombia, Peru), counties and cities (Taiwan). Admin2: municipalities (Brazil, Colombia), provinces (Peru), townships (Taiwan) |
| AlphaEarth | AlphaEarth Foundations Satellite Embedding V1: annual 64-dimensional embeddings of satellite imagery at 10 m [@brown2025alphaearth] |
| Area of applicability | The part of feature space where training data are close enough for predictions to be trusted [@meyer2021aoa] |
| B | Number of cosine terms in the EWC variance; also the degrees of freedom of the t reference |
| Booster, leaves | A booster is one gradient-boosted ensemble of decision trees (here one per quantile and horizon); leaves are the end nodes of each tree, and more leaves allow more complex trees |
| C1–C6, C4s | Location controls (Table S7) |
| C\*, selected control | The location control chosen at the 2019 origin by selection rule v2 |
| Cell | One combination of country and split |
| Case scale | WIS computed on raw counts instead of log(1 + cases) |
| Correlogram | Mean correlation between districts' deseasonalised case series as a function of the distance between them; used to set the S3 buffer D (Section D3) |
| Cosine similarity | Similarity of the directions of two vectors, from −1 to 1; 1 means the same direction |
| Coverage | Share of observed values inside a central prediction interval (40% or 80%) |
| D | Buffer distance of the held-out-regions split (Brazil 225 km, Colombia 130 km; Section D3) |
| Dimension-matched noise control | C3 in the held-out-country split: 64 columns of real embeddings of other districts of the unseen country, which match the embedding block's size and distribution but carry no district identity the model could have learned |
| Delta method | An approximation for the uncertainty of a ratio (here a gain as a percentage of WIS(L3)) when numerator and denominator are both estimated |
| District | Our word for an Admin2 unit |
| DM test | Diebold–Mariano test of equal forecast accuracy [@diebold1995comparing] |
| EE, EECU | Google Earth Engine; Earth Engine compute units (a quota meter) |
| Embedding | A fixed-length numeric vector summarising an object; here, a place's satellite observations in one year |
| Embedding gain, $\Delta_{\text{emb}}$ | WIS(L3) − WIS(L4); co-primary |
| Epidemiological week, year | Sunday-start week; its year is the calendar year of its Wednesday |
| EPIFORGE | Reporting guideline for epidemic forecasting studies (2020) |
| EWC | Equal-weighted cosine long-run variance estimator [@lazarus2018har] |
| Excess gain, $\Delta_{\text{excess}}$ | WIS(L3 + C\*) − WIS(L4 + C\*); co-primary (the protocol's primary measure) |
| Fixed-b | Critical values that treat the number of variance terms B as fixed, which keeps tests closer to their nominal size in short series [@lazarus2018har] |
| GHSL | Global Human Settlement Layer (population and built-up surfaces) |
| h | Forecast horizon in weeks (target week minus origin week) |
| HLN | Harvey–Leybourne–Newbold small-sample correction [@harvey1997testing] |
| Holm | Holm's step-down multiplicity correction [@holm1979simple] |
| IAAFT | Iterative amplitude-adjusted Fourier transform surrogates: random series with a given distribution and spectrum |
| Identity confound | The possibility that an embedding improves forecasts because it identifies the district, not because of what it says about the environment |
| Control gain, $\Delta_{\text{ctrl}}$ | WIS(L3) − WIS(L3 + C\*); called the identity gain in earlier drafts (`G_id` in code and result files) |
| k-means | A clustering method that splits points into k compact groups; used on district centroids to form the S3 blocks |
| L0–L4 | Steps of the model ladder (Table S6) |
| LightGBM | Gradient-boosted decision trees [@ke2017lightgbm]; here with a quantile loss |
| Location control | An input that tells the model where a district is without describing its land surface (C1–C6) |
| Location proxy | A feature that improves forecasts mainly by standing in for where a district is |
| LST | Land-surface temperature (MODIS) |
| MDE | Minimum detectable effect at 80% power and 5% two-sided level |
| MODIS | Moderate Resolution Imaging Spectroradiometer |
| Mondrian recalibration | Recalibration with a separate quantile shift for each bin of the forecast median |
| N3, N4 | No-history levels: L3 and L4 without case-derived inputs |
| NB | Negative binomial regression |
| NDVI | Normalised difference vegetation index |
| Origin | The last week whose data a forecast may use; forecasts are made at its end |
| Origin-year rows | Scored rows whose origin lies in the same epidemiological year as the target (primary) |
| Outbreak week | A district-week with cases at least max(5, the district's 90th percentile of weekly cases over 2013–2019) |
| q0.9 | The 0.9 quantile of a forecast |
| Quantile | The value below which a given share of the forecast distribution lies; the 0.9 quantile is exceeded with probability 0.1 |
| Recorded zero | A week the source lists with 0 cases (Brazil 2020–2021 in the test years) |
| Reference model | L3: the model with case history, climate, remote sensing and population, but without embeddings |
| Row mean | A mean WIS over all scored rows, so weeks with more rows weigh more; used only where a table says so |
| S1–S5 | Evaluation splits: new years (S1), held-out states (S2), held-out regions, that is, compact blocks of districts with a buffer (S3), held-out districts, assigned at random (S4), and held-out country (S5) |
| SE | Standard error |
| Static history | The historical-risk control (C1) used as a separate step in the analysis without case history |
| Spherical harmonics | Smooth functions of position on the globe, used as flexible coordinate features (C2) [@russwurm2024location] |
| T | Number of target weeks in a cell's weekly series |
| TimesFM | A pretrained time-series foundation model, used zero-shot as a baseline [@das2024timesfm] |
| TOST | Two one-sided tests for equivalence [@lakens2017equivalence] |
| VIIRS | Visible Infrared Imaging Radiometer Suite (night lights) |
| WIS | Weighted interval score [@bracher2021wis]; lower is better. Here from the median and nine deciles (K = 4 intervals), normalised by K + ½ |
| Week-weighted | A mean over target weeks of the within-week mean over districts and horizons, so each week has equal weight (the default in this paper) |
| WIS(L3), reference WIS | Mean WIS of the reference model in the cell; the denominator of every percentage |
| y − 1 | The year before the target year, the source year of yearly inputs |
| y, Y | y: the target's epidemiological year; Y: the test year of an annual refit |
| Zero-filled week | A district-week missing from the source and set to 0 |
| Zero-shot | Used as released, without training or fine-tuning on our data (TimesFM) |

---

## I. Further limitations

- Calibration. Eighty per cent intervals of the full model (L4 + C\*) covered 61–75% of weeks with cases (23% in Taiwan, new years; 24% without 2021), and other rungs were similar (56–75%); causal recalibration raised this mainly in Peru. <!-- src: T2_ladder.csv cov_80_nonzero for L4+C* (range 0.609–0.752; TW_S1 0.231 with 2021, 0.241 without); L1–L4+C* outside TW_S1 0.558–0.752; S5_recalibration.csv cov80pos_L4+C* (PE 0.67 → 0.76–0.77; others ≤ 0.03 change) -->
- Countries. Peru (115 provinces) did not show equivalence at ±1% (minimum detectable effects 0.95% for new years and 1.53% held out). Taiwan's data are almost all zeros (95 non-zero training targets at the 2019 tuning origin), so its tuning and control selection are nearly uninformative. Case definitions differ (probable in Brazil, total in Colombia, probable and confirmed in Peru, local confirmed in Taiwan), so percentages compare models within a country. <!-- src: T1_primary_family.csv PE_S1 MDE_pct (0.95, three seeds), PE_S5 (1.53); docs/methods/s1_pipeline.md "Pre-flight findings" (Taiwan 95 non-zero training targets); R2_data_scoring.md (case definitions) -->
- Covariates and geometry. The land-surface-temperature screen was off in Brazil's within-country runs; population grids exceed Brazil's 2022 census by 4–10%; the S3 buffer uses centroids (0.2–0.4% of training district-folds fall inside it by representative points); quality exclusions use adjacent weeks, though dropping them changes no result. <!-- src: NOTES_FOR_WRITERS.md item 23; docs/features/remote_sensing.md (GHSL +4–10% vs 2022 census); RESOLUTION_LOG.md section C (S3 buffer: 44 BR and 13 CO unit-folds; RA3 no-exclusion) -->
- Later-dated information. The AlphaEarth annual layers were released on 30 July 2025 by a model trained on data that extend into our test years [@brown2025alphaearth]; population is interpolated towards a 2025 projection; and the district universe ("ever reported a case") uses hindsight, with 565 districts first reporting in 2018 or later (111 Brazilian municipalities first in 2024). Section D lists every such item. <!-- src: R8_literature.md section 4; R10_fact_check.md row 2; docs/data/completeness_v1.md "Other exclusion files" -->
- Filled zeros. In Brazil 2024, 1.5% of absent weeks held one to three probable cases (Espírito Santo excluded). Taiwan's crosswalk was inferred from counts, so count agreement is not independent; a name check matched all 287 townships (Section A3). <!-- src: docs/data/zero_fill_crosscheck_2024.md (excluding Espírito Santo); R1_timing_leakage.md section 4 -->
- Inference. In size simulations computed before the origin-year filter and the Espírito Santo exclusion, the primary test rejected 10–22% of true nulls at nominal 5% in the cells with multi-season drift, up to 28% under a stress test, and 10–12% in seed placebos (Section E3). On the current rows, with the B = 4 and IAAFT checks and Holm correction, the loss in Colombia's held-out states stays significant under both checks, those with Brazil held out and in Colombia's new years and buffered blocks under one (IAAFT), and those for Colombia's random districts and Taiwan held out under neither (Table S26). <!-- src: RC_summary.md size table and real placebo; T1_primary_family.csv B4_Holm_p, p_iaaft_Holm -->
