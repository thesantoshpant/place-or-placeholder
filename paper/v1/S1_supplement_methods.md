# Supplementary Methods

Contents: A. Data sources, processing and verification. B. Features and controls. C. Models and hyperparameters. D. Information available to each model. E. Inference, size simulation, supporting and sensitivity analyses. F. Deviations from the original protocol. G. EPIFORGE 2020 checklist. H. Glossary (Table S16). I. Further limitations.

Automated AI agents (see Use of AI tools) wrote the code and ran the downloads, the verification scripts, the Earth Engine extractions, the model runs, the scoring, the statistical analyses and the internal audits described in this supplement. A check called separate or independent below was written and run by a different automated AI agent from the one that produced the output being checked.

The supplement uses short codes in tables, and the glossary (Supplementary Methods, section H) defines each of them. There are five splits. Future years (S1) forecasts the same districts in later years. The other four hold out states (S2), regions made of compact blocks of districts with a buffer around them (S3), districts assigned at random (S4) and a whole country (S5). One country with one split is a comparison. The models form a ladder of steps, L0 to L4. The reference model (L3) uses case history, climate, remote sensing and population, and the embedding model (L4) adds the satellite embeddings. A location control is an input that tells the model where a district is, which district it is, or how much dengue it usually has, without describing its own environment directly. The six controls are C1 to C6 (Table S7), and C\* is the control selected for a comparison.

We report three measures. The embedding gain compares the reference model with the embedding model. The control gain compares the reference model with the reference model plus the selected control; earlier drafts called it the identity gain, and the code and result files still call it `G_id`. The excess gain compares the reference model with the control against the embedding model with the same control. A positive embedding or excess gain means that the embeddings reduced forecast error, and a positive control gain means that the control reduced it. Tables S17 to S56 and Figures S1 to S4 are in the Supplementary Results.

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

All gridded inputs were downloaded from Google Earth Engine [@gorelick2017gee] and averaged over each district on our own server, weighting each grid cell by the share of it that falls inside the district [@baston_exactextract]. Before use, a separate script checked every downloaded file: it compared checksums with the source, tested archive integrity and parsed the whole file. The OpenDengue archives matched the GitHub blob hashes of release commit 99b6a3e and the figshare v5 MD5 sums and parsed without error. The boundary files and the 2024 InfoDengue downloads were checked in the same way. <!-- src: docs/data/opendengue_v1.3.1_verification.md; docs/data/boundaries_verification.md; docs/data/zero_fill_2024_verification.md section 1 -->

### A2. Weekly district panel

We used the weekly, district-level (Admin2) rows of the OpenDengue Temporal extract. All weekly rows are 7-day spans starting on Sunday, and no district appears twice in the same week. The epidemiological year of a week is the calendar year of its Wednesday. Districts are identified by the 7-digit IBGE code in Brazil and by their state and district names elsewhere. The FAO GAUL codes could not be used because they are not unique: Taiwan's 287 districts share two codes. <!-- src: docs/data/panel_weekly_v1.md; ../audits/review_round/R10_fact_check.md section B (GAUL codes 5,456 / 1,012 / 113 / 2) -->

**Table S2. Weekly district panel after zero-filling.**

<!-- src: docs/data/panel_weekly_v1.md "Counts"; docs/data/opendengue_v1.3.1_audit.md (raw rows with 0 cases); ../audits/review_round/R10_fact_check.md items 5a, 5c, 5d and section B (raw row counts) -->

| Country | Districts | Weeks | Panel rows | Source weekly rows | Source rows reporting 0 cases | Panel rows zero-filled (whole window) |
|---|---|---|---|---|---|---|
| Brazil | 5,517 | 574 | 3,166,758 | 1,895,538 | 63% | 40.1% (2014–2021: 29.3%; 2022 on: 69.2%) |
| Colombia | 1,071 | 835 | 894,285 | 199,458 | 0.4% | 77.7% |
| Peru | 115 | 1,252 | 143,980 | 30,991 | 0% | 78.5% |
| Taiwan | 287 | 1,409 | 404,383 | 7,673 | 0% | 98.1% |

District counts include only districts that ever reported a case. Peru has 115 of about 196 provinces, and Taiwan 287 of about 368 townships, namely those that ever had a locally acquired case. <!-- src: docs/data/zero_fill_crosscheck.md (287 of ~368 townships); docs/data/completeness_v1.md "Peru zero-fill check" (~115 of ~196 provinces ever report) -->

Three district counts appear in the paper. The panel has 6,990 districts (Table S2). Of these, 6,987 have a boundary polygon (Table S3; one Colombian and two Taiwanese districts have none). The scored count, used in the main text, is 6,909. The 78 Espírito Santo municipalities have no scored row, because their exclusion (Supplementary Methods, section A6) covers every test year. Brazil therefore contributes 5,439 scored districts, Colombia 1,070, Peru 115 and Taiwan 285. <!-- src: Table S2 (5,517 + 1,071 + 115 + 287 = 6,990); Table S3 (5,517 + 1,070 + 115 + 285 = 6,987); S7_embedding_distance.csv n_units BR_S5 5,439, CO 1,070, PE 115, TW 285 (sum 6,909); docs/plans/deviations_from_protocol.md row 34 (78 ES municipalities) -->

### A3. Boundaries

Brazil was joined by IBGE code to the 2022 municipal mesh. Colombia, Peru and Taiwan were matched by name within each state, department or county. Matches were tried in this order: manual fixes, then the Taiwan CDC township list, then exact, normalised and finally approximate (fuzzy) name matches. A fuzzy match needed a rapidfuzz similarity score of at least 85, or 90 in Taiwan, and each district could match only one polygon. <!-- src: docs/data/boundaries_join.md "Method" -->

**Table S3. Matching of districts to boundary polygons.**

<!-- src: docs/data/boundaries_join.md "Match rates" -->

| Country | Districts matched | Cases 2014 on matched | Match methods |
|---|---|---|---|
| Brazil | 5,517 / 5,517 | 100.000% | IBGE code |
| Colombia | 1,070 / 1,071 | 99.994% | exact 1,005, normalised 30, fuzzy 28, manual 7 |
| Peru | 115 / 115 | 100.000% | exact 113, manual 2 |
| Taiwan | 285 / 287 | 100.000% | CDC crosswalk 271, manual 6, exact 4, normalised 3, fuzzy 1 |

Three districts have no polygon. Belén de Bajirá in Colombia had 40 cases since 2014, and its municipality status was annulled. Taiwan has two "other" categories that are not places and had no cases since 2014. All three are excluded from scoring. The official Taiwan township file returned HTTP 403, so Taiwan polygons are the 2017 OpenStreetMap-derived geoBoundaries file. <!-- src: docs/data/boundaries_join.md "Unmatched units"; docs/data/completeness_v1.md "Other exclusion files" -->

#### Taiwan crosswalk

We matched OpenDengue townships to Taiwan CDC townships by choosing, within each county, the pairing that best lines up their weekly case counts. Agreement in weekly counts is therefore partly built in and does not validate the match. A check that does not use counts compared the romanised (pinyin) spelling of every Chinese township name with the OpenDengue name. It agreed for 287 of 287 districts: 281 exactly, 5 by close spelling and 1 after an individual check. In addition, 40 rows of the match were reviewed one by one. Automated AI agents made both checks (see Use of AI tools). <!-- src: ../audits/review_round/R1_timing_leakage.md section 4; docs/data/boundaries_verification.md -->

### A4. Zero-fill validation

#### Rule

The district universe is every district in a country's weekly file. A country's coverage runs from its first to its last week with any district row. Within that period, a missing district-week is set to 0 and flagged as zero-filled. <!-- src: docs/data/panel_weekly_v1.md "Frozen rule" -->

#### Brazil vs InfoDengue

OpenDengue matches InfoDengue's count of probable cases (`casprov`) rather than its count of notified cases. <!-- src: docs/data/zero_fill_crosscheck.md; docs/data/zero_fill_crosscheck_2024.md -->

**Table S4. OpenDengue compared with InfoDengue probable cases in samples of Brazilian municipalities.**

| Year | Municipalities sampled | Present weeks: Σ OpenDengue / Σ probable | Absent weeks with ≥ 1 probable case | Maximum in an absent week |
|---|---|---|---|---|
| 2017 | 40 | 1.008 | 0 of 902 | 0 |
| 2019 | 40 | 1.003 | 0 of 573 | 0 |
| 2022 | 40 | 1.020 | 14 of 1,285 (1.1%) | 4 |
| 2023 | 40 | 0.939 | 26 of 1,231 (2.1%) | 8 |
| 2024 (excluding Espírito Santo) | 58 | 0.964 | 25 of 1,658 (1.5%) | 3 |

The weekly correlation was at least 0.97 in every year and group, and 0.999 in 2024. In weeks present in both sources the differences were small, though larger in later years. This fits revisions to the surveillance data made after the OpenDengue snapshot. <!-- src: docs/data/zero_fill_crosscheck.md; docs/data/zero_fill_crosscheck_2024.md (60 municipalities incl. 2 ES) -->

#### Taiwan vs Taiwan CDC

OpenDengue's Taiwan series counts locally acquired confirmed cases by week of onset and township of residence. Imported cases are left out. All 7,673 township-weeks present in OpenDengue match the CDC data exactly, and no absent township-week holds a local case. In 2021 there were no local cases and 12 imported ones. National weekly totals match exactly in 83.7% of weeks. The rest of the difference is 410 early local cases from 1998–2010, 217 of them in 2002, that have no county of residence and so cannot be placed in a township. <!-- src: docs/data/zero_fill_crosscheck.md Taiwan section -->

#### Colombia and Peru

In Colombia, district sums agree with national totals within about 5%. The weekly ratio of the district sum to the national total is about 1 and stable, with a 10th percentile of at least 0.79 in 2020–2022. This leaves little room for unreported cases in filled weeks. <!-- src: docs/data/completeness_v1.md "Colombia: the ratio is ≈1 and stable (2020–22 weekly p10 ≥ .79)" --> In Peru, district sums cover 85–94% of national totals in 2020–2023. With the same case definition, they are 0.84–0.94 of department totals in 2007–2013. Only 0.4–1.6% of the department-level cases fall in department-weeks in which every district was zero-filled. We could not check absent weeks at province level, so Peru's zero-filling is only partly validated. <!-- src: docs/data/completeness_v1.md "Peru zero-fill check", "Recommendation" item 3 -->

### A5. Completeness rule and exclusions

#### Completeness rule

The rule was fixed after the future-years results but before it was applied to the test years. The primary threshold is k = 0.5, with 0.4 and 0.6 as sensitivity values. <!-- src: docs/data/completeness_v1.md "Rule" -->

1. Country-weeks (Brazil, Colombia and Peru, in weeks with at least 20 national cases). A week is flagged when the district total is unusually low compared with the national total. Unusually low means that the ratio of the two is below k times its usual value for that time of year and also below k times the median ratio of the same year. The usual value is the median ratio over the previous three years, within ±2 weeks of the same epidemiological week.
2. State-weeks. A week is flagged when its cases fall below k times the smaller of two means: the mean of the two weeks before and the mean of the two weeks after. That smaller mean must be at least 50. If the national series dips in the same way, the flag is used for sensitivity analyses only.
3. Weeks flagged at k ≤ 0.5 by the primary rule are excluded from scoring. All other flags are used only in sensitivity analyses.

#### Flags in the test years

No test week was flagged in Brazil, Colombia or Taiwan. In Peru, two department-weeks were flagged, Junín 2020-12-27 and Ucayali 2023-07-23; they hold 0.03% of rows and 0.02% of cases. In Brazil, 8–22 December 2024 carries a flag used only in sensitivity analyses (1.1% of Brazilian test rows, 0.4% of cases). Taiwan has no national reference, but the state-week check of rule 2 flagged 0 of 96 evaluable weeks. Removing the incomplete-week exclusions restores 16 Peruvian rows and changes no result. <!-- src: docs/data/completeness_v1.md "Flags in the test years", "Recommendation"; docs/results/review/RA_summary.md RA3 -->

#### Gap flag in training

A country-week is gap-flagged when the national count is at least 20 and the ratio of the district sum to the national total is below 0.25 times that country-year's ratio of sums. Only one week is flagged, Peru on 2018-08-12, and it is dropped from the training targets. <!-- src: docs/data/panel_weekly_v1.md "flag_gap"; ../audits/review_round/R1_timing_leakage.md section 0 last row -->

### A6. Espírito Santo false zeros (D34)

OpenDengue V1.3.1 has no source data for Espírito Santo after 2020. Its district rows end on 2020-12-27, and 63 of the 78 municipalities have their last row on 2019-12-22. The 15 municipalities with 2020 rows report far fewer cases than InfoDengue (7,562 vs 27,077 probable). In 2024 every Espírito Santo week is zero-filled, while InfoDengue shows probable cases in 2,925 of 4,056 of those weeks (72%), 166,407 cases in total. A scan of every state, department and county in the four countries found no other gap of this kind. <!-- src: docs/data/zero_fill_2024_verification.md sections 2–3; docs/data/zero_fill_crosscheck_2024.md ES table -->

#### Rule

Every Espírito Santo municipality, that is, every district whose IBGE code matches `^32\d{5}$`, is excluded from scoring for target weeks from 2019-12-29 (epidemiological year 2020) onward. The exclusion applies to every Brazilian comparison and every model. It removes 38,766 primary rows per comparison, which is 1.41% of the about 2.74 million Brazilian primary rows before the exclusion; 2,703,183 rows remain. It moves every Brazilian excess gain by at most 0.03 percentage points. The rule does not depend on the outcomes of other states, because it follows from the source no longer reporting this state. Models were not refitted, so their 2020–2023 training targets still contain these false zeros. Espírito Santo makes up 1.9–4.5% of Brazil's zero-filled rows in each year. <!-- src: docs/plans/deviations_from_protocol.md row 34; docs/results/review/KIT3_changes.md ES section; docs/data/zero_fill_crosscheck_2024.md ES table -->

### A7. Covariates

#### Climate (L2)

ERA5-Land daily values were summed or averaged over the panel's Sunday-start weeks. The variables are mean, minimum and maximum temperature at 2 m, total precipitation and relative humidity. Humidity was computed from daily mean temperature and dew point with the Magnus formula and capped at 100%. Each grid cell is weighted by GHSL population from the nearest available year and by the share of the cell inside the district, on a 0.01° grid aligned with ERA5-Land's 0.1° grid. Ocean cells get zero weight. We downloaded the weekly grids from Earth Engine and averaged them on our own server. The result agreed with Earth Engine's own district averages to r > 0.999999995 at about 1/20 of the computing cost (Brazil 1.76 EECU-hours). Twenty-three districts, mostly islands, have no ERA5-Land land cell (Brazil 3, Colombia 2, Taiwan 18); they use the nearest land cell. <!-- src: docs/features/climate_era5land.md "Definitions" and "Method choice"; ../audits/review_round/R10_fact_check.md section B (23 units) -->

#### Remote sensing and population (L3)

<!-- src: docs/features/remote_sensing.md "Sources and conventions", "QA", "Caveats", "v2" -->
- NDVI: MOD13Q1 (16-day, 250 m), keeping pixels with quality flag SummaryQA ≤ 1. Values were read from the coarser, about 1 km, copies that Earth Engine stores for large areas. In a pilot this gave r = 0.998 against the native 250 m data at about a quarter of the cost.
- Land-surface temperature (LST): MOD11A2 day and night (8-day, 1 km), without the satellite's quality mask. A version that used the quality flags (v2) did not remove the cold readings caused by clouds, and it changed Brazil's month-to-month pattern (correlation with v1 about 0.85–0.88), so we did not use it. Instead, for Colombia, Peru, Taiwan and every held-out-country model (S5), an LST value more than 10 °C below the district's median for that calendar month over years ≤ 2017 is set to missing (D7). The share of district-months removed by this screen, day and night, was 0.08% and 0.02% in Brazil, 0.06% and 0.57% in Colombia, 0.06% and 0.18% in Peru, and 0.05% and 0.06% in Taiwan. The screen is off for Brazil's within-country splits (S1–S4). <!-- src: docs/methods/s1_pipeline.md "LST outlier screen" -->
- Month assignment: each composite image is assigned to the month in which it ends, so each month uses only data available by its end. A missing district-month is filled only from the same month of the previous year.
- Night lights: VIIRS annual, from 2013 (missing before). Built-up share: GHSL GHS_BUILT_S, interpolated linearly between the GHSL reference years.
- Population: GHSL GHS_POP, interpolated on a log scale between the GHSL reference years, with no extrapolation beyond them. It exceeds the 2022 Brazilian census by 4–10%, so we use it only as a relative scale.
- Remote-sensing extraction used 8.9 EECU-hours in total.

#### AlphaEarth (L4)

<!-- src: docs/features/alphaearth_extraction.md "Method"; docs/features/alphaearth_verification.md; ../audits/review_round/R10_fact_check.md items 1b, 3, 4b and section B -->
- Image: the annual mosaic of `GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL` (64 bands A00–A63, 10 m, each pixel vector of unit length), read at a coarser resolution that Earth Engine builds by averaging pixels.
- District mean: a population-weighted mean at 100 m on the GHSL population grid. Each pixel is weighted by its share inside the district times its GHSL population. Negative no-data values were set to 0, and population was interpolated linearly between 2015, 2020 and 2025. Only blocks with people were downloaded. An unweighted 300 m mean is stored but not used in the primary models.
- In a 10-municipality subset of the Brazilian pilot, 100 m gave practically the same means as 10 m (mean cosine 0.99994), while simple resampling to 300 m did not (0.993). Downloading blocks and summing them on our own server matched Earth Engine's own district sums exactly at about 40% of the cost.
- Image years extracted: Brazil 2017–2024, Colombia 2017–2021 and 2023, Peru and Taiwan 2017–2023. Target year y uses image year y − 1.
- District means are shorter than unit length. In the median district, the length of the population-weighted mean is 0.87–0.92 by country (range 0.70–0.98). In Brazil the median is 0.92 and the range 0.74–0.98. Each mean is rescaled to unit length. Rescaling removes the length of the mean, which is shorter when a district's land cover is more varied; we did not test that length as a separate input.
- The source data have no AlphaEarth pixels for Fernando de Noronha (Brazil) in 2017–2021. Its embedding inputs are therefore missing for target years 2018–2022, and LightGBM treats them as missing values. The missing values are the same in every model that contains the embeddings (L4 and L4 + C\*), so they do not differ between the two sides of the excess gain.
- Extracting one state-year again with a different number of parallel workers gave exactly the same sums.

**Table S5. Independent recomputation of AlphaEarth district means.**

<!-- src: docs/features/alphaearth_verification.md; ../audits/review_round/R10_fact_check.md items 3, 4b and section B -->

| Country | Districts covered | District-years recomputed | Minimum cosine, weighted | Minimum cosine, unweighted | Median cosine, neighbours vs random pairs |
|---|---|---|---|---|---|
| Brazil | 5,517 / 5,517 | 33 | 0.9999999987 | 0.9999999969 | 0.973 vs 0.710 |
| Colombia | 1,070 / 1,071 | 33 | 0.9999999982 | 0.9999999975 | 0.926 vs 0.644 |
| Peru | 115 / 115 | 32 | 0.99999999975 | 0.9999999996 | 0.91 vs 0.44 |
| Taiwan | 285 / 287 | 33 | 0.99999998 | 0.99999989 | 0.975 vs 0.88 |

Note: The recomputation used a separate script with its own Earth Engine code; it did not reuse the extraction code. Population sums agree within 0.03%. <!-- src: ../audits/review_round/R10_fact_check.md section B (max 0.027%, Taiwan; Brazil max 0.017%) --> Districts not covered are those without a polygon. The agreement shows that the extraction can be reproduced. It says nothing about the quality of the embeddings themselves.

### A8. Computation

LightGBM 4.7.0 ran on CPUs in its deterministic mode with row-wise histograms. Every pair of compared runs used the same number of threads, seed rule and software version. For one model we checked, the predictions were exactly the same with 2, 4, 8 and 16 threads. TimesFM ran on one GPU. <!-- src: docs/methods/compute_plan.md lines on determinism; docs/methods/timesfm.md -->

#### Training and randomness

Every model (booster) is trained for a fixed 400 boosting rounds. There is no early stopping and no validation set inside the test-year fits. The seed of a run sets LightGBM's random number generators. These affect the model only through the rows and columns each tree sees: a random 0.8 share of rows at every round and a random 0.9 share of columns. The seed also sets the random draws of two controls, the source map of the shuffled embeddings (C3) and the smooth random fields (C4 and C4s). Nothing else in a run is random. The features, folds, test years and scoring are fixed. <!-- src: src/pop/models/lgbm.py lines 10-11, 21, 32 (num_boost_round 400, seed, no early stopping); src/pop/features/controls.py SEEDED_CONTROLS, _rng; docs/methods/round3_runs.md section S1 -->

#### Size of each fit

One fit is one model for one quantile, horizon, test year and fold. Each job in the run fits 9 such models, for the median and the 8 other deciles, on the same training rows. Table S5b gives the range of training rows per fit for the full model (L4 + C\*) over test years and folds; the smallest is at the first test year, 2020. Within a comparison, all models have the same inputs apart from the embedding and control columns (Table S6). The tuning and selection fits at the 2019 origin trained on the 2018 targets: Brazil 286,884 rows, Colombia 55,692, Peru 5,865 and Taiwan 14,924 (horizon 1). <!-- src: runs/<country>_s1_shared_controls_2019/chunks/lgbm__L3+C1__s0__2019__h1.done.json n_train -->

**Table S5b. Training rows per fit for the full model (L4 + C\*), horizons 1 and 4.**

<!-- src: runs/<run>/chunks/*.done.json n_train and n_features for test years >= 2020; run directories brazil_s1_shared_L4_Cstar, brazil_s2_L4_Cstar, brazil_s3_L4_Cstar, brazil_s5_L4_Cstar, colombia_s1_shared_L4_Cstar, colombia_s{2,3,4,5}_L4_Cstar, peru_s1_L4_Cstar, peru_s5_L4_Cstar, taiwan_s1_shared_L4_Cstar, taiwan_s5_L4_Cstar plus taiwan_s5_tw2021_L4_Cstar; brazil_s1_nohist_N4_Cstar; brazil_s4_L4_Cstar and brazil_s2_nohist_N4_Cstar (read 2026-11-20) -->

| Comparison | Training rows per fit (range over test years and folds) | Input columns |
|---|---|---|
| Brazil, future years | 573,768 – 1,726,821 | 151 |
| Brazil, held-out states | 456,872 – 1,385,651 | 151 |
| Brazil, held-out regions | 377,624 – 1,290,812 | 151 |
| Brazil, held-out districts | 458,952 – 1,381,582 | 151 |
| Brazil, held-out country | 153,077 – 405,242 | 214 |
| Colombia, future years | 111,384 – 223,839 | 151 |
| Colombia, held-out states | 89,024 – 179,113 | 151 |
| Colombia, held-out regions | 54,912 – 216,942 | 151 |
| Colombia, held-out districts | 89,024 – 179,113 | 151 |
| Colombia, held-out country | 615,461 – 1,236,956 | 232 |
| Peru, future years | 11,845 – 29,900 | 151 |
| Peru, held-out country | 715,000 – 1,794,375 | 214 |
| Taiwan, future years | 29,848 – 89,831 | 151 |
| Taiwan, held-out country | 696,997 – 2,042,232 | 214 |
| Brazil, future years, without case history | 573,768 – 1,726,821 | 211 |
| Brazil, held-out states, without case history | 456,872 – 1,385,651 | 211 |

Note: Input columns of the full model (L4 + C\*) as recorded during the runs. They are the 150 columns of L4 in Table S6 plus the control: 1 column for C1, 64 for C3 and 82 for C2. Held-out-country fits pool the three other countries.

#### Total compute

All LightGBM and negative binomial runs took about 4,700 core-hours, counted as wall time times threads and summed over the 6,180 completed jobs that were stored. This total includes the 2019 tuning and control-selection runs, the sensitivity analyses, the runs added after the third review and some superseded runs kept for the record. It does not include runs discarded after the control fixes (rows 13–15 and 18). The primary and secondary runs with case history took about 2,400 core-hours (3,326 jobs). The analysis without case history took about 900 (804 jobs), the runs added after the third review about 810 (1,722) and the review sensitivity analyses and fixed control panels about 510 (328). TimesFM used 32 minutes of one GPU. Earth Engine extraction used about 182 EECU-hours for AlphaEarth and 8.9 for remote sensing. All runs used one server (AMD EPYC 7551P, 32 cores, 125 GiB RAM). <!-- src: paper/v1/_compute_total.txt (runs/*/chunks/*.done.json seconds × threads over all runs, 4,662 core-hours, 6,180 chunks; threads from config_resolved.yaml for the 146 early chunks without a threads field; computed 2026-11-20); docs/methods/timesfm.md (32 min); project notes (AE 182 EECU-h); docs/features/remote_sensing.md (8.9 EECU-h) -->

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

A software check confirms that L0 to L2 contain no district-specific input. Weekly inputs are read through a function that checks that the source week is at or before the forecast origin. Monthly and yearly inputs are read through a function that checks that the source period ends before the allowed limit. <!-- src: docs/methods/runner.md "Adding a feature level" -->

**Table S7. Location controls.**

<!-- src: docs/methods/controls.md; src/pop/features/controls.py; docs/methods/nohist_arm.md (C6) -->

| Control | Type | Columns | Definition | Where defined |
|---|---|---|---|---|
| C1 | Average past cases | 1 | Mean log(1 + cases) over panel years before 2018 (Brazil 2014–2017), gap-flagged weeks dropped. S1: the district's own value, identical for training and test rows and at every origin. S2–S4: inverse-distance (1/(d + 1 km)) mean of the 5 nearest training districts' values; training districts get a matched leave-out value (S2 excludes their own state, S3 neighbours within D, S4 only themselves) | S1–S4 |
| C2 | Geographic | 82 | Latitude, longitude and 80 orthonormal real spherical harmonics of degree 1–8, no constant term [@russwurm2024location; @klemmer2025satclip] | All |
| C3 | Identifier (S1–S4); noise of matching size (S5) | 64 | One fixed source map per seed and country, used in every year: district i gets the real year y − 1 AlphaEarth vector of its source district. S1 and S5: a random permutation of the country's districts; the identity permutation is rejected, but the permutation is not a derangement, so occasionally a district keeps its own vector (about one per country and seed). S2–S4: training districts are permuted among themselves, and each held-out district gets a training district drawn at random (with replacement), never itself | All |
| C4 | Geographic | 64 | 64 Gaussian random fields per country, exponential covariance exp(−d/r) in great-circle distance, standardised within country; r fitted to the AlphaEarth semivariogram (Brazil 8,483 km, Colombia 705 km, Peru 148 km, Taiwan 27 km); drawn only on districts with coordinates | All |
| C4s | Geographic | 64 | C4 with r = min(D, fitted range): Brazil 225 km, Colombia 130 km; equal to C4 in Peru and Taiwan, so not a separate candidate there | Brazil, Colombia, S5 |
| C5 | Snapshot | 64 | AlphaEarth 2023 for every target year | All |
| C6 | District label | 1 | District ID as one LightGBM categorical input | S1 only |

Note: Each control takes the place of the AlphaEarth columns (L3 + Ck) or is added to them (L4 + Ck). In the held-out-country split, C3 gives each district the embedding of another district of the same unseen country. It therefore measures the cost of 64 extra columns of realistic values rather than district identity, and we call it a noise control of matching size there. Districts without a polygon or point get missing values for C1, C2, C4 and C4s, which LightGBM treats as missing. These are Belén de Bajirá in Colombia and two "other" categories in Taiwan, and they are excluded from scoring. <!-- src: src/pop/features/controls.py _perm (rejects only the identity permutation), c3_source_map docstring; ../audits/final_round/RC_repro_audit.md M3, L6 -->

<!-- src: C4 ranges: ../audits/review_round/R1_timing_leakage.md section 0 (BR 8483, CO 705, PE 148 km); docs/methods/controls.md (C4s rule; PE/TW fitted 148/27 km). Taiwan's fitted range (27 km) is from docs/methods/controls.md. -->

Controls are rebuilt for every split, fold, origin and seed. Each district is located by a point guaranteed to lie inside its polygon. We tested that C1 does not change when every row from 2018 on, or every row of a test district, is replaced by an extreme value. <!-- src: docs/methods/controls.md "Leakage guarantees" -->

### B1. Selection of the location control

In plain terms, we keep every control whose selection score is within about two standard errors of the best one, and then take the first of these in a fixed order of preference. In detail, for each comparison every candidate control k is added to the reference model and scored at the 2019 origin: trained on 2018 targets, scored on 2019 targets, at horizons 1 and 4. The score $\mathrm{Score}_k$ is the mean WIS on log(1 + cases) over rows (not week-weighted), averaged over seeds. C3, C4 and C4s use three seeds and the other candidates one. A candidate whose forecasts exactly match the reference model's adds nothing and is dropped. With $\sigma_{\mathrm{seed}}$ the within-candidate seed standard deviation pooled over the multi-seed candidates of the comparison and $n_k$ the number of seeds of candidate k,

$$\mathrm{SE}_k = \frac{\sigma_{\mathrm{seed}}}{\sqrt{n_k}}, \qquad \mathcal{T} = \left\{k : \mathrm{Score}_k - \mathrm{Score}_{\mathrm{best}} \le 2\sqrt{\mathrm{SE}_{\mathrm{best}}^2 + \mathrm{SE}_k^2}\right\},$$

so single-seed candidates (C1, C2, C5, C6) have $\mathrm{SE}_k = \sigma_{\mathrm{seed}}$. C\* is the first member of the tie set $\mathcal{T}$ in the priority order C1 > C3 > C2 > C4s > C4 > C5. Without case history the order is C3 > C2 > C6 > C4s > C4. If $\sigma_{\mathrm{seed}}$ is zero or undefined, the comparison is marked uninformative and C\* is the first remaining candidate in priority order. <!-- src: scripts/run/select_control.py docstring (lines 20-30) and selection function (lines 125-151) -->

The priority order puts first the controls that most directly encode a district's own dengue history or identity. These are average past cases (C1) and then the shuffled embeddings (C3), which keep the size and distribution of the real embeddings. Next come the smooth geographic controls, from the most flexible (coordinates with harmonics) to the least. The 2023 snapshot comes last because it uses later imagery. The plain reference model was not a candidate, so a control was always selected, even where every candidate scored worse than the reference model at 2019. This happened in 11 of 14 comparisons (Table S22). A rule that allows "no control" is reported as a sensitivity analysis (Supplementary Results, Table S45). <!-- src: T4_cstar_selection.csv wis_log_2019 (a candidate below L3 only in BR_S1 C1, CO_S5 C2, TW_S1 C3; 11 of 14 cells with every candidate worse); ../audits/final_round/RC_repro_audit.md M4 -->

---

## C. Models and hyperparameters

#### LightGBM

LightGBM was fitted with a quantile loss on log(1 + cases), with one model (booster) per quantile (9) and horizon. Settings: learning rate 0.05; 400 rounds; feature fraction 0.9; bagging fraction 0.8 at every iteration; L2 penalty 1; deterministic mode with row-wise histograms. The forecast quantiles were converted back to case counts, set to at least 0 and put in order. A scan of the 77,187,144 stored forecasts found no quantiles out of order and none missing. We did not log how often quantiles were out of order before sorting. <!-- src: docs/methods/runner.md "Models and tuning"; docs/results/review/RA_summary.md RA7 -->

#### Tuning

The search grid was leaves per tree {31, 127} × minimum rows per leaf {100, 1,000}. The criterion was the mean pinball loss, a standard score for quantile forecasts, on log(1 + cases) at quantiles 0.1, 0.5 and 0.9 and horizons 1 and 4. We trained on 2018 and validated on 2019, using level L1 and seed 0. Brazil chose 127/100 (validation 0.07406 vs 0.07428 for 31/100), and Colombia, Peru and Taiwan chose 31/100. One configuration per country is used for every level, control and split. The held-out-country split (S5) uses Brazil's configuration (127 leaves), or Colombia's (31 leaves) when Brazil is held out. Taiwan held out, the comparison with the largest loss, therefore used 127 leaves. The analysis without case history uses Brazil's L1 configuration, which was tuned on a model with case history. <!-- src: docs/results/review/RF_summary.md (0.07406/0.07428); docs/methods/split_pipeline.md "Params"; docs/plans/deviations_from_protocol.md "No-history parameters" -->

#### Per-level tuning (sensitivity)

Tuning each level separately in Brazil gave 127/100 for L1 and L2 and 31/100 for L3 and L4. The gap between the best and second-best validation loss was 0.29% for L1, 0.03% for L2, 0.06% for L3 and 1.36% for L4. In the Brazilian future-years test years (S1), the reference model with 31 leaves differed from the same model with 127 leaves by about eight times the embedding gain under the shared configuration, pooled over horizons 1 and 4. Per horizon the ratio was 6.5–14 times on the primary rows. This difference motivated one shared configuration (D2). Before the origin-year filter the ratio was about seven. <!-- src: ../audits/review_round/R10_fact_check.md section B (tuning gaps) and items 6a, 6b (pre-filter, about 7x); primary rows computed from T2_ladder_long.csv BR_S1_perlevel vs BR_S1 L3 and BR_S1 L3 vs L4 (7.7 pooled h{1,4}; 13.7, 7.7, 7.3, 6.5 by horizon) -->

#### Taiwan

At the 2019 tuning origin Taiwan had 95 non-zero training targets in 33 townships and 56 non-zero validation targets in 26 townships. Its tuning and its choice of control therefore carry almost no information. As a sensitivity analysis, we also ran Taiwan's future-years comparison (S1) with Brazil's configuration and Brazil's selected control. <!-- src: docs/methods/s1_pipeline.md "Pre-flight findings" -->

#### Baselines

Seasonal naive model (L0): the quantile τ is expm1(log1p(y at t − 52) + the τ-quantile of the training errors log1p(y_t) − log1p(y_{t−52})), set to at least 0. Negative binomial: an NB2 regression on raw counts with the L1 inputs and an intercept, fitted by L-BFGS from a Poisson start, with quantiles taken from the fitted distribution; it was not tuned. TimesFM 2.5 (checkpoint `google/timesfm-2.5-200m-pytorch`) was used as released, without training on our data (zero-shot). It received each Brazilian district's log(1 + cases) history up to the origin, at most 573 weeks, and its deciles were sorted and set to at least 0. It was run for Brazil's future-years comparison (S1) only. <!-- src: docs/methods/runner.md "L0 quantile method", "Models and tuning"; docs/methods/timesfm.md -->

---

## D. Information available to each model

"Outcomes" means case counts. "Held-out" means the districts scored in a split's test fold. For test year Y the training targets are epidemiological years 2018 to Y − 1.

**Table S8. Information used at each step of the analysis, by split.**

<!-- src: ../audits/review_round/R1_timing_leakage.md section 0 (code references there) -->

| Step | Future years (S1) | Held-out states (S2) | Held-out regions (S3) | Held-out districts (S4) | Held-out country (S5) |
|---|---|---|---|---|---|
| Final model fit | All districts, targets 2018 to Y − 1 | Training districts only | Training districts minus the buffer | Training districts | The other three countries |
| Hyperparameters | Country L1 tuning at 2019 (train 2018, validate 2019), all districts | The same S1 tuning, so held-out districts' 2018–2019 outcomes informed the choice | As S2 | As S2 | Brazil's (Colombia's when Brazil is held out); no held-out-country outcome used |
| C\* selection | All districts, 2019 outcomes | Train on training districts (2018), score held-out districts' 2019 outcomes | As S2, held-out blocks | As S2, held-out districts | Held-out country's 2019 outcomes |
| C1 value | Own mean log(1 + cases) before 2018 | Held-out: distance-weighted mean of the 5 nearest training districts' pre-2018 means. Training: the same, excluding their own state | As S2; training districts exclude neighbours within D | As S2; training districts exclude only themselves | Not defined |
| C3 value | Fixed random permutation of the country's districts (a district can occasionally keep its own vector) | Held-out district gets a random training district's series (never its own) | As S2 | As S2 | Fixed permutation within the held-out country (a district can occasionally keep its own vector) |
| C4/C4s range | Fitted on AlphaEarth 2017–2018 of all districts (covariates only, no outcomes) | As S1 | As S1 | As S1 | Per country, as S1 |
| Buffer D | – | – | Correlograms of deseasonalised 2014–2019 case series of all districts, held-out included (pre-test; Supplementary Methods, section D3) | – | – |
| Fold construction | – | Admin1 units assigned greedily by district count | k-means on centroids | Random, stratified by Admin1 | – |
| District universe | Districts that ever reported a case, through the end of the data (hindsight) | Same | Same | Same | Same |
| LST screen | Per district and calendar month, median of its own LST over years ≤ 2017 (off in Brazil S1–S4) | Same | Same | Same | Same (on for all countries) |
| Test-time inputs of held-out districts | Own lagged cases, climate, remote sensing, population, AlphaEarth y − 1 | Same (own lagged cases are used) | Same | Same | Same |
| Scoring exclusions | No-polygon districts, incomplete weeks (rule uses ±2 weeks and the same year, i.e. later weeks), Espírito Santo from 2019-12-29 | Same | Same | Same | Same |

### D1. Where held-out outcomes enter

Outcomes of held-out districts enter in three places, all before the test years. They informed the choice of model settings in S2–S4 (2018–2019 outcomes), the selection of the control in S2–S5 (2019 outcomes) and the buffer distance of the held-out-regions split, S3 (2014–2019 outcomes). The district universe uses outcomes from every year. No outcome of a held-out district from a test year (≥ 2020) enters any fit. <!-- src: ../audits/review_round/R1_timing_leakage.md section 0 -->

### D2. Information dated after the forecast origin, removed by the origin-year filter (D24)

Yearly inputs are linked to the target's epidemiological year, and each annual model is trained on labels up to the last week of Y − 1. Rows whose origin falls in Y − 1 could therefore use information from after the origin.

**Table S9. Share of scored rows that could use information from after the origin, around the turn of the year.**

<!-- src: ../audits/review_round/R1_timing_leakage.md section 1a table -->

| Horizon | Yearly inputs after the origin (first h target weeks of Y) | Training labels after the origin (first h − 1 weeks) | Maximum weeks of labels after the origin |
|---|---|---|---|
| 1 | 1.91% | 0 | 0 |
| 2 | 3.83% | 1.91% | 1 |
| 3 | 5.74% | 3.83% | 2 |
| 4 | 7.66% | 5.74% | 3 |
| Pooled h 1 and 4 (primary) | 4.79% | 2.87% | |

Note: h is the forecast horizon in weeks. The shares are identical in every comparison.

The filter keeps a row only if the epidemiological year of its origin week (the calendar year of the week's Wednesday) equals the test year. On the rows kept, yearly inputs are the same whether they are linked to the target or to the origin, and every training label is dated at or before the origin. In the three within-country Brazilian comparisons the dropped rows slightly favoured the embedding model (L4), so the later information did not cancel out between models. <!-- src: ../audits/review_round/R1_timing_leakage.md section 1a/1b and "Resolution" -->

**Table S10. Information dated after the forecast origin that the origin-year filter does not remove.**

<!-- src: ../audits/review_round/R1_timing_leakage.md section 1c; ../audits/review_round/R8_literature.md section 4; docs/research/data_and_tools.md ERA5-Land row -->

| Item | Why it is later than the origin | Models affected | Direction |
|---|---|---|---|
| Case counts | One snapshot of final revised counts; no reporting delay except the delay-2 sensitivity | All | Unknown; flatters all models |
| ERA5-Land | Reaches Earth Engine about 3 months after real time | L2 and above | Shared |
| GHSL population and weights | Product released 2023; epochs 2015, 2020, 2025 (2025 a projection); climate weights use the nearest epoch, so 2023+ weeks use 2025 | L2 and above | Shared |
| AlphaEarth model | Trained on imagery "covering 2017 to present", production model with labels through 2023–2024; annual layers released 30 July 2025. The imagery period overlaps every test year (2020–2024) | L4, C3, C5 | Could favour the embeddings |
| C5 (2023 static embedding) | 2023 imagery used for 2020–2022 targets | C5 only (never selected) | Favours the control |
| District universe | Districts that ever reported a case; 565 enter in 2018 or later (Brazil 507, 111 first in 2024; Peru 28; Taiwan 18, all in 2023; Colombia 12) | All | Shared |
| Incomplete-week exclusion | Rule uses later weeks of the same year | Scoring only | Shared; test-year effect 2 Peruvian department-weeks |

<!-- src for late-entry counts: docs/data/completeness_v1.md "Other exclusion files"; ../audits/review_round/R10_fact_check.md item 2 -->

A sensitivity analysis for late entry, which would restrict the universe at origin Y to districts first seen before Y, is supported by the code but was not run. <!-- src: ../audits/review_round/R1_timing_leakage.md section 1c last row -->

### D3. Buffer geometry of the held-out-regions split

The buffer distance D was estimated on 2014–2019 only, with no test year, from districts with at least 10 weeks with cases (Brazil 4,249; Colombia 806). For each distance band we computed the mean correlation between pairs of districts' weekly log(1 + cases) residuals. We used two kinds of residual. The protocol residuals remove the district mean and week-of-year effects. The second kind also removes each calendar week's national mean. D is the larger of the two distances at which these correlation curves (correlograms) first fall below 0.1. In Brazil the protocol curve levels off at about 0.11 out to 2,000 km. This reflects national co-movement that no buffer can remove, so in Brazil only the second curve drops below that level, giving D = 225 km. In Colombia the two curves drop below it at 130 km and 80 km, so D = 130 km. Every training district within D of any held-out district of the fold is dropped from training. <!-- src: docs/methods/splits.md "Buffer distance D" -->

The buffer is measured from polygon centres (centroids), while C1, C2 and C4 use a point inside each district. Measured between these inside points, 44 Brazilian and 13 Colombian training districts in a fold lie within D of a held-out district; these are about 0.23% and 0.38% of training memberships. The minimum distance between training and test districts in a fold is 161–218 km in Brazil (D = 225 km) and 122–146 km in Colombia (D = 130 km). <!-- src: ../audits/review_round/R1_timing_leakage.md section 3 -->

### D4. Tuning within folds

The held-out states, regions and districts splits (S2–S4) reuse the country's future-years tuning (S1), which saw the held-out districts' 2018–2019 outcomes. An automated AI agent repeated the same search within each fold's training districts only, so no held-out or buffer district contributed. Repeating the search over all districts reproduced the stored S1 tuning to every printed digit. <!-- src: docs/results/review/RF_summary.md -->

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

In Colombia every fold chose the same settings, so the use of held-out outcomes made no difference. In Brazil, 12 of 15 folds would have chosen 31 leaves. The S1 configuration raised the fold validation loss by 0.11–1.05% (median 0.32%), and in S1 itself the two settings differed by only 0.29%. The Brazilian S2–S4 comparisons were not rerun. <!-- src: docs/results/review/RF_summary.md verdict -->

---

## E. Inference, size simulation, supporting and sensitivity analyses

### E1. Primary estimator and test

For a gain and a comparison, let $g$ be the seed-averaged WIS difference of one row. The weekly value $d_{h,t}$ is the mean of $g$ over districts at horizon $h$ and target week $t$, and $d_t$ is the mean of $d_{h,t}$ over the horizons present (1 and 4). The estimate $\bar d$ is the mean of $d_t$ over the $T$ test weeks. The main test is a Diebold–Mariano (DM) test. It uses the equal-weighted cosine (EWC) estimate of the long-run variance with $B$ cosine terms and a $t$ reference distribution with $B$ degrees of freedom. $B$ is 16 in Brazil and Taiwan, 11 in Colombia and 13 in Peru. The test also applies the Harvey–Leybourne–Newbold (HLN) small-sample factor at $h = 4$, and Holm correction across the comparisons of the primary family. Ten comparisons average seeds 0 to 2: Brazil S1 and S5, Colombia S1 to S4, Peru S1 and S5, and Taiwan S1 and S5. For Peru and Taiwan held out, the seed average applies only to the excess gain (row 53). The other comparisons use one seed, so their intervals are conditional on one fit. <!-- src: T1_primary_family.csv n_seeds; docs/results/FINAL_RESULTS_BRIEF.md section 1 --> The statistic and its parts are <!-- src: docs/results/review/RC_summary.md "What population the inference refers to" (1.34) --> <!-- src: src/pop/eval/estimands.py infer_estimand; src/pop/eval/stats.py; T1_primary_family.csv df -->

$$\begin{aligned}
\mathrm{DM} &= \frac{\bar d}{\mathrm{SE}}, & \mathrm{SE} &= \frac{\mathrm{SE}_{\mathrm{EWC}}}{c_{\mathrm{HLN}}},\\
B &= \left\lfloor 0.4\,T^{2/3}\right\rfloor, & c_{\mathrm{HLN}} &= \sqrt{\frac{T + 1 - 2h + h(h-1)/T}{T}}.
\end{aligned}$$

The 95% and 90% intervals are $\bar d \pm t_B\,\mathrm{SE}$, so a 95% interval excludes zero exactly when $p < 0.05$. The HLN factor at $h = 4$ is applied to the series pooled over horizons 1 and 4. Because the correction grows with $h$, this is the conservative choice. Equivalence is tested with two one-sided tests (TOST). They show equivalence when the 90% interval lies inside ±1% of WIS(L3), where WIS(L3) uses the same week-pooled mean. The minimum detectable effect (MDE), the smallest effect the test could reliably detect, is $(t_{B,0.975} + t_{B,0.80})\,\mathrm{SE}$ without adjustment. Holm-adjusted thresholds are about 1.34 times larger.

The WIS uses the median and the nine deciles, that is K = 4 central intervals (20%, 40%, 60% and 80%) plus the median, normalised by K + ½. It is therefore not on the same scale as the 23-quantile WIS of the forecast hubs (row 36). Unless a table says "row mean", a mean WIS in this paper is week-weighted. That is, we first average over districts and horizons within each target week and then average over weeks.

#### Labels and counting

The label of each comparison in Table 2 combines the main test with the Holm-adjusted TOST. Examples are "Small loss; within ±1%" and "Inconclusive", which means neither a significant difference nor shown equivalence. A loss is an excess gain below zero with Holm-adjusted p < 0.05, and a gain is one above zero with the same condition. A loss or gain is called small when it lies inside ±1%. A p < 0.05 without Holm adjustment is never counted. <!-- src: docs/plans/deviations_from_protocol.md row 27; T1_primary_family.csv plain_label -->

#### Margin

The original protocol used 1% as the smallest embedding gain worth reporting, before any share of it could be attributed to identity (row 9). We decided to use it as an equivalence margin after seeing the Brazil and Peru future-years results (S1). On the log scale, a WIS difference behaves roughly like a relative error. So 1% of Brazil's WIS(L3), about 0.0017, corresponds to a change of roughly 0.2% in the typical ratio of forecast to observed (1 + cases). <!-- src: T1_primary_family.csv BR_S1 WIS_ref 0.1675; exp(0.00168) − 1 = 0.17% --> Two comparisons give a sense of scale. Within our own study, TimesFM used without training on our data had 13% higher WIS than LightGBM L1 in Brazil's future-years comparison (S1). Their WIS relative to the seasonal naive model (L0) was 0.411 and 0.362. <!-- src: S1_baselines.csv BR_S1 pooled 1,4 wis_log 0.19284 vs 0.16996; rel_wis_vs_L0 0.411 vs 0.362 --> In the US COVID-19 Forecast Hub, neighbouring leading models differed by 0.01–0.02 in relative WIS, about 1.6–3.3% of the leader's WIS [@cramer2022covidhub]. That comparison is on the case scale, while our margin is a share of WIS on log(1 + cases), so it is only a rough guide. Margins of ±0.5% and ±2% are also reported (Table S24). <!-- src: ../audits/review_round/R8_literature.md section 2 -->

#### Inference population

Weeks are the sampling unit, for this fixed set of districts, fitted models and test seasons. The folds of the spatial splits divide the districts into groups; they are not random samples. Inference about future seasons would need the variance between seasons. A test at the level of seasons would have only 2–4 degrees of freedom and could barely estimate it. <!-- src: docs/results/review/RC_summary.md "What population the inference refers to" -->

### E2. Robustness checks

- The strict-variance check: the main test with only B = 4 cosine terms. With fewer terms the test is less affected by slow drift in the weekly differences, at the cost of power.
- The surrogate-series check. We simulated 2,000 series that have the same distribution of values and the same pattern of ups and downs as the observed weekly differences $d_t$, but a true mean of zero, and asked how often they give a test statistic as large as the observed one. Technically, these are windowed iterative amplitude-adjusted Fourier transform (IAAFT) surrogates [@schreiber1996iaaft]. Each is a circular series of length 8T with the real distribution of values and the real spectrum smoothed over a span of 3 (held flat below frequency 1/T), centred at zero, from which a random window of length T is taken. The p value is (1 + k)/(1 + 2,000), where k counts surrogates whose |DM statistic| is at least the observed one.
- Together these are the two stricter checks.
- Delta-method interval for 100 × G / WIS(L3), which allows for the uncertainty in WIS(L3) (EWC + HLN on the linearised weekly series).
- Case scale: the excess gain with WIS on raw counts (expm1 of the log-scale quantiles, set to at least 0).
- All rows: without the origin-year filter.
- Old exclusions: without the Espírito Santo exclusion.
- Resampling of the weekly differences $d_t$ in 52-week blocks (circular block bootstrap). This is descriptive only, because T = 154–256 weeks gives only three to five blocks.

<!-- src: docs/plans/deviations_from_protocol.md row 28; scripts/analysis/rk_compute.py iaaft_pvalue, robust_table; docs/results/review/RC_summary.md "What was tested"; docs/results/review/RA_summary.md RA6 -->

### E3. Size simulation

The size of a test is how often it finds an effect when there is none; it should match the nominal level. We measured the size of the main test and its alternatives on simulated series with no effect, built to resemble each comparison's own centred weekly differences $d_t$ (2,000 replications per comparison and generating process). We used four ways of generating the series:

- surrogate series with the real pattern of ups and downs, which treats swings over several years as random noise (windowed IAAFT);
- the same with extra slow swings, as a stress test (IAAFT with doubled power below frequency 2/T);
- yearly seasonal cycles plus noise that carries over from week to week, with heavy-tailed residuals resampled from the data (annual harmonics plus AR(1), called ARX);
- a simple Gaussian AR(1) series with φ = 0.5 and T = 104.

As real placebos we used differences between two seeds of the same model: 21 series from Brazil's future-years comparison (S1; T = 261) and 33 series from the 2019 control runs (T = 52). <!-- src: docs/results/review/RC_summary.md "What was tested" -->

**Table S12. Empirical size of the tests at a nominal 5% level.**

<!-- src: docs/results/review/RC_summary.md size table -->

| Generating process | Main test (EWC + HLN) | Strict-variance check (EWC + HLN, B = 4) | Newey–West (NW94) | 52-week block bootstrap |
|---|---|---|---|---|
| AR(1), φ = 0.5, T = 104 | 0.054 | 0.046 | 0.110 | 0.294 |
| ARX, median over comparisons | 0.026 | 0.034 | 0.10 | 0.18–0.21 |
| IAAFT, median over comparisons | 0.048 | 0.036 | 0.20 | 0.18–0.21 |
| IAAFT low-frequency stress, median over comparisons | 0.120 | 0.048 | 0.30 | 0.18–0.21 |
| IAAFT, worst comparisons (BR S1, BR S2, BR S3, CO S5, PE S1) | 0.10–0.22 | ≤ 0.15 | 0.10–0.50 (any process) | 0.15–0.31 (any process) |
| Seed placebo, Brazil S1 (21 series) | 2 of 21 rejected | 1 of 21 | 4 of 21 | 3 of 21 |
| Seed placebo, 2019 controls (33 series, T = 52) | 4 of 33 | 5 of 33 | 13 of 33 | undefined |

Note: Size is the share of simulated series with no effect in which the test found one. The Monte Carlo standard error is about 0.5 percentage points. Computed before the origin-year filter and the Espírito Santo exclusion. BR, Brazil; CO, Colombia; PE, Peru.

#### Conclusions

The main test is acceptably calibrated when the weekly differences $d_t$ have short memory around a steady mean, as in most comparisons (size ≤ 8% under ARX). The HLN correction changes the size by at most 1 point. In this earlier simulation, run before the origin-year filter, the test finds effects too often (size 10–22%, up to 28% under the stress test) in comparisons whose gain drifts across seasons, if that drift is treated as noise. These are Brazil S1, S2 and S3, Colombia S5 and Peru S1. Equivalence statements for Brazil S1, Brazil S2 and Colombia S5 therefore hold only if there is no drift across several seasons. The Newey–West and h − 1 variance estimators and both block bootstraps found effects far too often.

In this simulation analysis, which came before the origin-year filter and the Taiwan 2021 runs, only Colombia S4 lost Holm significance under the strict-variance check (B = 4; Holm-adjusted p 0.10). On the final primary rows (Table 2 and Table S26; Holm over 14 comparisons), Brazil S5, Colombia S1, S3 and S4 and Taiwan S5 lose Holm significance under the strict-variance check (B = 4), so only Colombia S2 keeps it. Under the surrogate-series check, Colombia S4 and Taiwan S5 lose it. The direction of all six losses is unchanged. <!-- src: T1_primary_family.csv B4_Holm_p, p_iaaft_Holm --> In the final surrogate-series calibration of the primary rows (Supplementary Results, Table S47), which replaces the earlier simulation for the final results, the size of the nominal 5% test was 14% to 18% in Brazil S1, S2, S3 and S4 and Colombia S5. Equivalence statements for these comparisons also assume no drift across several seasons. <!-- src: R3_A8_iaaft_equivalence.csv size_nominal5 (BR_S4 0.149) --> The chance of detecting a gain of 1% of WIS(L3) (the power) is 1.00 in Colombia S5 and about 1.00 in Brazil S2, S3 and S5 and Colombia S1–S4. It is 0.83–0.88 in Brazil S1, Taiwan S1 and Peru S1, 0.53 in Peru S5 and 0.08 in Taiwan S5. <!-- src: docs/results/review/RC_summary.md "Power", "Do the primary-family conclusions change?", "Verdict" -->

<!-- Note: RC_summary.md was computed before kit v3 (all rows, before the origin-year filter and the ES exclusion); current robustness p-values are in T1 (B4_Holm_p, p_iaaft_Holm). -->

### E4. Supporting analyses (exploratory, no multiplicity adjustment; D33)

<!-- src: docs/results/review/RD_summary.md sections 1–6; docs/results/review/RB_summary.md sections 1–3; docs/results/review/RA_summary.md RA1, RA7; docs/plans/deviations_from_protocol.md row 33 -->

- Baselines in the future-years split (S1): WIS on log(1 + cases) of the seasonal naive model (L0), negative binomial regression, LightGBM L1–L4 and L3/L4 + C\*, and TimesFM (Brazil only). WIS relative to L0 is computed on rows scored by every model.
- Additive stratum contributions: for each horizon and week, d = Σ_s w_s d_s, where w_s is the stratum's share of rows. The contributions, as % of the comparison's WIS(L3), therefore add up exactly to the total. We also report each stratum's estimate on its own rows as % of that stratum's own WIS(L3); these are not shares of the total.
- Outbreak weeks: cases ≥ max(5, the district's 90th percentile of weekly cases over 2013–2019).
- Weighted means: within each mean over a horizon and week, districts are weighted by their population in the target year, or by their mean weekly cases over 2013–2017 plus 1.
- Causal recalibration: the forecast ranges are adjusted using only earlier test years, separately for L3 + C\* and L4 + C\*. Each quantile is shifted by a fixed amount on the log scale, fitted on the earlier test years; the first test year is left unadjusted. There is either one shift per quantile (global) or one shift per group of forecasts with a similar median (called Mondrian).
- Mechanism: the change in the mean 0.9 quantile between L4 + C\* and L3 + C\* on rows with zero cases, and the share of the loss on those rows that comes from quantiles above the median.
- Embedding similarity (S2–S5): for each held-out district, the cosine similarity between its rescaled year y − 1 embedding and the most similar training district's vector, and the mean over the 5 most similar [@meyer2021aoa], set against the district's gain.
- Per-year gains with context flags (COVID-19 years 2020–2021, Peru 2023, Brazil 2024).
- Exploratory subgroups (research question 4, where embeddings help or hurt): population tercile in the year before the test year; number of years in 2014–2017 with at least one case (0, 1–2, 3–4); and tercile of the change in GHSL built-up share over 2010–2015.
- Coverage of the 40% and 80% intervals overall and on weeks with cases.

### E5. Sensitivity analyses

**Table S13. Sensitivity analyses and their status.**

| Analysis | Comparisons | Estimands | Status |
|---|---|---|---|
| Three seeds (primary) vs seed 0 | Brazil S1 | All three | Done |
| Per-level tuning (original protocol) | Brazil S1 | All three | Done |
| Fixed control panel C1, C2, C3, C6 | S1, all countries | Control and excess gains | Done (Table S36; Brazil C3 and C6 also in Table S37) |
| Yearly inputs keyed to the origin year (strictly causal) | Brazil S1 | Embedding gain only | Done (Table S37) |
| Two-week reporting delay in case inputs | Brazil S1 | Embedding gain only | Done (Table S37) |
| Taiwan with Brazil's configuration and C\* | Taiwan S1 | All three | Done |
| Taiwan without 2021 | Taiwan S1, S5 | All three | Done |
| Margins ±0.5% and ±2% | All comparisons | Excess gain | Done |
| All rows; old exclusions; case scale; B = 4; IAAFT; delta method | All comparisons | Excess gain | Done |
| Late-entry district universe | All comparisons | Excess gain | Not run |
| Long training window for L0–L3 (2013 to Y − 1; protocol) | Brazil S1 | Ladder | Not run (row 35) |
| 23-quantile WIS (protocol secondary score) | All comparisons | All | Not computed (row 36) |
| As planned vs as reported (Table S43) | All comparisons | Excess and embedding gains | Done (row 44; Table S43) |
| Gains from known predictors along the ladder, as a scale for the margin (Table S44) | S1, all countries | Ladder gains | Done (row 41; Table S44) |
| "No control" selection rule (Table S45) | All comparisons | Embedding or excess gain | Done (row 40; Table S45) |
| Per-year trend test (Table S46) | All comparisons | Excess and embedding gains | Done (row 42; Table S46) |
| Equivalence at ±0.5/1/2% with EWC and B = 4 SEs (Table S47) | All comparisons | Excess gain | Done (row 43; Table S47) |
| Checks that do not select rows by outcome (Table S48) | All comparisons; Colombia district-years | Excess gain, coverage, width | Done (row 45; Table S48) |
| Embedding stability (Table S49) | All countries | Cosine similarity | Done (row 46; Table S49) |
| Information probe (Table S50, Figure S4) | All countries | Cross-validated skill | Done (row 47; Table S50) |
| Representation variants V1–V4 (Table S51) | CO S1, CO S2, PE S1, TW S1, BR S2 | Variant gains | Done (row 48; Table S51) |
| Seeds 0–2 (Table S52) | Colombia, Peru, Taiwan comparisons; Brazil S5 | All three | Done (rows 49 and 53; Table S52) |
| Taiwan future-years ladder and panel with 2021 (Table S53) | Taiwan S1 | Ladder, control panel | Done (row 50; Table S53) |
| No case history, Colombia held-out states (Table S54) | Colombia S2 | All three | Done (row 51; Table S54) |
| Equal-budget tuning (Table S55) | Colombia S1 | Excess gain | Done (row 52; Table S55) |
| District-label panel without case history, N3 + C6, N4 + C6 (exploratory) | Brazil S1 without case history | Control and excess gains | Done (row 38; results below) |
| Zero-fill stress test: a share of zero-filled test weeks changed to 1 or 3 cases, stored forecasts rescored (Table S56) | All comparisons | Excess gain | Done (row 54; Table S56) <!-- src: docs/results/review/R5_zero_fill_stress.md (commit 40d7faf) --> |

<!-- src: T6a_sensitivities.csv variant and variant_status (all available, final kit 2026-11-20); RE_summary.md; RE_control_panel.csv; docs/results/review/RH_nohist_c6.md; T1_primary_family.csv robustness columns; ../audits/review_round/R1_timing_leakage.md section 1c (late entry not run). Note: RE_summary.md says the control panel uses the v3 primary rows (origin-year filter, exclusions v2), while NOTES_FOR_WRITERS item 32 says all rows; see notes_B. -->

The reporting-delay sensitivity analysis only shifts the case-history inputs two weeks back. It does not use real data on reporting delays. The runs with origin-linked yearly inputs and with a delay cover L3 and L4 only, so they are compared with the embedding gain rather than the excess gain. None of the Brazilian sensitivity analyses gave a significant gain. The embedding gain was +0.26% (95% CI −0.29 to 0.82) with strictly causal yearly inputs. It was +0.60% (−0.56 to 1.76) with a two-week reporting delay, against +0.29% for seed 0 of the primary runs. The excess gain was +0.28% (−0.27 to 0.82) with shuffled embeddings (C3) in place of the selected control, and +0.30% (−0.12 to 0.71) with the district label (C6). <!-- src: T6a_sensitivities.csv BR_S1_yref, BR_S1_delay2, BR_S1_ctrlC3, BR_S1_ctrlC6; S2_control_panel.csv brazil G_emb_pct --> Row 38 added an exploratory comparison without case history, in Brazil's future-years split (S1) with seed 0. There, the district label (C6) gave a control gain of +1.98% over N3 (95% CI 0.76 to 3.21; p = 0.003). This is less than the gain from coordinates (+3.30%). With the district label in the model, the excess gain from the embeddings was −0.04% (−1.24 to 1.16). <!-- src: docs/results/review/RH_nohist_c6.md table (C6 G_id +1.98 [+0.76, +3.21] p 0.003; C6 G_excess −0.04 [−1.24, +1.16]; C2 G_id +3.30) --> <!-- src: ../audits/review_round/R1_timing_leakage.md sections 1a, 1c; ../audits/review_round/RESOLUTION_LOG.md section C -->

---

## F. Deviations from the original protocol

We logged each change to the protocol with the date it was recorded and the results that had already been seen. The original protocol is the evaluation plan and its design review of 15 November 2026. The changes were recorded as follows.

- Rows 1–10 were committed in d8c7944. The analysis without case history was pre-specified in bd3ba50. Rows 11–17 were recorded in fcc3c38, and the control fixes of rows 13–15 were implemented in 9de7386. All of this happened on 16 November 2026, before any result of a spatial split had been read.
- Rows 18–23 were committed in e9df1f1 (16 November, 20:29 CST), about three hours before the first spatial-split result (3ca02d7, 23:21 CST).
- Rows 24–34 were committed in f107238 (18 November, 02:16 CST) after external review. By then the S1, S2, S3 and S5 results and Colombia S4 had been seen. Only Brazil S4 and the comparisons without case history were still running.
- Rows 35–38 were added on 18 November 2026 after review of the full draft and recorded in the deposit commit. The Brazil S1 result without case history had been read, but the Brazil S4 result and the Brazil S2 result without case history had not. Rows 35–37 record protocol commitments that were not carried out.
- Rows 39–53 were added on 19 November 2026 after the third review, when all 13 completed comparisons had been read; the result for Brazil's held-out districts had not yet been seen. Each was specified, and recorded in commit 8001a92, before it was scored, and row 53 before any new seed was seen. <!-- src: ../audits/final_round/RC_repro_audit.md L4; ../audits/final_round/TRIAGE_round3.md sections B, C --> <!-- src: docs/plans/deviations_from_protocol.md rows 35–38 (commit column "2026-11-18 deposit commit") --> The future-years test results (S1) for Brazil, Peru and Taiwan were seen before rows 2, 8, 9, 11, 13, 16 and 18–22 were decided, so some S1 test results were known when those decisions were made. The baselines (L0–L2, TimesFM) were also looked at on test years while the analysis code was being developed.
- Row 54 was added on 22 November 2026, during the authors' review of the full draft, when all 14 comparisons had been read. It rescores stored forecasts against changed targets; nothing was refitted and no primary number changes. Its specification and its results were recorded together in commit 40d7faf (22 November, 19:01 CST). <!-- src: git log 40d7faf (2026-11-22 19:01 −0600; script, CSV and report in one commit, so not "specified before scoring") -->

All 54 rows can be grouped by what had been seen when they were decided. Rows 1–23 (23 rows) came after some future-years test results but before any held-out-place result. Rows 24–34 (11 rows) came after every completed comparison except Brazil's held-out districts and the analyses without case history. Rows 35–38 (4 rows) came after the Brazilian future-years result without case history, rows 39–53 (15 rows) after all 13 completed comparisons, and row 54 after all 14.

Four rows changed the quantity being estimated after results it affects had been read. Row 2 introduced one shared configuration, row 21 pooled horizons 1 and 4 in the future-years comparisons, and row 24 restricted scoring to origin-year rows. Row 25 included Taiwan 2021 and was decided after both Taiwan comparisons had been read. It moved the seed-0 excess gain with Taiwan held out from −11.16% to −17.30%, and the Taiwan future-years gain from −0.44% to −0.60%. With seeds 0 to 2 the final values are −18.29% and −0.71%. Row 53 (seed averaging) changes the primary estimates of the comparisons that gained seeds (Table S52). It changed no conclusion after Holm adjustment over 14 comparisons, although the loss with Brazil held out is no longer significant under the strict-variance check (B = 4) with Holm adjustment (Table S26). <!-- src: commit times in the paragraph above; T6a_sensitivities.csv / Table S37 (TW without 2021: S5 −11.16, S1 −0.44); R3_C_seeds.csv T1_seed0_pct TW_S5 −17.30, TW_S1 −0.60; T1_primary_family.csv (final) TW_S5 −18.29, TW_S1 −0.71 --> <!-- src: docs/plans/deviations_from_protocol.md header; docs/results/NOTES_FOR_WRITERS.md items 1–3; git log (commit times) -->

**Table S14. Deviations from the original protocol.**

| # | Change | Reason | Decided after seeing | Commit |
|---|---|---|---|---|
| 1 | C1 under the temporal split = the district's mean log(1 + cases) over the years before the first training target year (Brazil 2014–2017), identical for training and test rows | The first definition (mean of the training targets) leaked each training row's own target: 2019 WIS 0.263 vs 0.175 for plain L3 | 2019 selection-origin results only | d8c7944 |
| 2 | One LightGBM configuration per country, tuned once on L1 at the 2019 origin, for all levels and controls; per-level tuning becomes a sensitivity analysis | Per-level tuning on a nearly flat grid (validation differences 0.03–1.4%) gave L1/L2 127 leaves and L3/L4 31 leaves; on Brazil S1 test years L3 with 127 leaves beat L3 with 31 at every horizon (Holm p ≤ 0.012), a capacity effect several times the embedding gain (about eight times on the primary rows; Supplementary Methods, section C) | Brazil S1 test years | d8c7944 |
| 3 | S2 = grouped leave-states-out in 5 folds (was one state per fold: 27 in Brazil, 33 in Colombia); Brazil's S3 groups 10 blocks into 5 folds; old versions kept in the code, not run | Compute (the 27-fold S2 was 54% of the total); held-out districts are still in states unseen in training | No | d8c7944 |
| 4 | Spatial splits score horizons 1 and 4 only (S1 keeps 1–4); the random district-week split S0 is dropped; final C\* runs use 1 seed (selection uses 3 seeds for random controls; the protocol said 10); no re-tuning per split | Compute; Brazil S1 selection seed SD about 0.0001 WIS | No | d8c7944 |
| 5 | C1 in S2/S3: training districts get a matched leave-out value (exclude own state in S2, neighbours within D in S3) | With plain leave-one-out, training districts' neighbours were far closer than held-out districts' (median 23 km vs 105–394 km), so training and test values differed in distribution | No | d8c7944 |
| 6 | S5 configuration = the L1 configuration of the largest training country (Brazil; Colombia when Brazil is held out) | No S5-specific tuning origin exists | No | d8c7944 |
| 7 | LST outlier screen for Colombia, Peru and Taiwan (value > 10 °C below the district's calendar-month median from years ≤ 2017 set to missing); off for Brazil S1–S4 | Cloud-contaminated cold MODIS LST (Colombia minimum −42 °C); a QC-bit mask did not remove it | No | d8c7944 |
| 8 | Secondary no-case-history arm added, pre-specified in `docs/methods/nohist_arm.md` before it ran | With case history neither embeddings nor controls helped (Brazil and Peru S1), so identity and place information could not be told apart | Yes (S1 nulls); labelled exploratory | d8c7944; bd3ba50 |
| 9 | Smallest effect of interest = 1% of WIS(L3) (the protocol's ID-share gate); TOST on 90% intervals; minimum-detectable-effect table | A null result needs an explicit margin | Partly (Brazil and Peru S1 seen) | d8c7944 |
| 10 | Deferred: TimesFM + LightGBM residual hybrid, monthly replication arm, PDFM (L5), reporting-lag analysis on data vintages | Time and scope | No | d8c7944 |
| 11 | Inference: DM test on the weekly cross-district mean loss difference with EWC variance, fixed-b t and HLN; interval d̄ ± t_B · SE; TOST on the 90% version; the bootstrap becomes a sensitivity analysis with 52-week (not 8-week) blocks | Weekly loss differences stay autocorrelated at lags 8 and 52 (about 0.42–0.43); the 8-week bootstrap excluded 0 where DM p was 0.3–0.5 | Yes (Brazil S1); before any spatial result | fcc3c38 |
| 12 | Primary family = pooled-horizon excess gain, with case history, 14 country × split comparisons, Holm; embedding and control gains, per-horizon and per-year results secondary (since row 39 the embedding gain is also a main measure) | The family had not been fixed | Yes (S1); before any spatial result | fcc3c38 |
| 13 | C3 uses one fixed source map per seed across all years | A new permutation each year meant C3 was not a stable identifier (0–0.05% of districts kept their source) | Found by an automated AI-agent audit (see Use of AI tools) after Brazil S1 test results; C3 had been scored at the 2019 origin only | fcc3c38; code 9de7386 |
| 14 | C1 in S2–S4 = matched neighbour mean of the neighbours' pre-training-year mean log(1 + cases) (was their 2018 to Y − 1 targets) | In-period neighbour targets are contemporaneous with training targets (a diluted leak) and differ from the S1 definition | No spatial result read | fcc3c38; code 9de7386 |
| 15 | C4 at two ranges: the fitted range (Brazil 8,483 km) and a short range (C4s) | At 8,483 km C4 is close to a planar trend, not an identifier | No | fcc3c38; code 9de7386 |
| 16 | Brazil S1 primary runs get 2 extra seeds at horizons 1 and 4; seed SD reported | Per-horizon seed SD (about 0.0001–0.0003 WIS) is of the same order as the excess gain | Yes (Brazil S1) | fcc3c38 |
| 17 | Documented, not changed: yearly inputs keyed to the target year; annual refits train through the end of Y − 1; an origin-keyed sensitivity planned (superseded by row 24) | Automated AI-agent audit | – | fcc3c38 |
| 18 | C4/C4s fields fitted only on districts with coordinates; affected Colombia, Taiwan and S5 runs and the Colombia S1 and Brazil S5 C\* runs were discarded and rerun | Three districts without polygons made every field missing in Colombia and Taiwan, so C4/C4s forecasts equalled L3 (Colombia S1 C\* had in effect been plain L3) | Yes (Colombia S1 2019 selection, Taiwan S1 test results); no spatial result | e9df1f1 |
| 19 | New C\* selection rule: drop candidates whose forecasts equal L3's; tie set within 2 seed SEs of the best; first tie-set member in priority C1 > C3 > C2 > C4s > C4 > C5 (without case history: C3 > C2 > C6 > C4s > C4); zero seed SD = "uninformative" | C\* was being decided inside seed noise (Colombia margin 0.00003 vs seed SD 0.00006; Taiwan exact ties broken by sort order) | Yes (Brazil, Peru, Taiwan S1); before any spatial result | e9df1f1 |
| 20 | C4s range = min(D, fitted range); in Peru and Taiwan C4s equals C4 and is not a candidate | C4s had run at a longer range than C4 there; it never won, so no C\* changed | Yes (Peru, Taiwan S1) | e9df1f1 |
| 21 | The primary family pools horizons 1 and 4 in every comparison; S1 pooled over 1–4 is secondary | The S1 estimand differed from S2–S5 | Yes (S1); before any spatial result | e9df1f1 |
| 22 | Brazil S1 primary comparison uses seeds 0, 1 and 2 at horizons 1 and 4; each estimand uses the seeds common to both its models; seed SD computed where all seeds exist | The manifest listed one seed, and the old fill rule halved the seed SD | Yes (Brazil S1) | e9df1f1 |
| 23 | Scheduler thread budget counts other jobs on the server | Operations | No effect on results | e9df1f1 |
| 24 | Primary scored rows = origin-year rows (drops the first h epidemiological weeks of each test year); all rows reported as a sensitivity | Yearly inputs and annual training labels could postdate the origin (Supplementary Methods, section D) | Yes (after review) | f107238 |
| 25 | Taiwan 2021 is a test year in TW S1 and TW S5; Taiwan S1 explicitly in the family of 14 comparisons; the old test-year set reported as a sensitivity | Excluding a year because it had no cases is an outcome-based exclusion | Yes | f107238 |
| 26 | Three target strata (weeks with cases, zeros listed by the source, zero-filled), each with its own estimate and an exact additive contribution to the comparison total | "Observed" mixed weeks with cases and zeros listed by the source; stratum estimates do not add up under equal-week weighting | Yes | f107238 |
| 27 | Holm-adjusted TOST, plain labels, margin table at ±0.5/1/2%, and a loss-counting rule (Holm-adjusted p < 0.05; "small" inside ±1%) | Equivalence claims over 14 comparisons need the same multiplicity control; earlier class words were misleading | Yes | f107238 |
| 28 | Robustness columns: EWC with B = 4, IAAFT-calibrated p, delta-method interval, case scale, all rows | The primary test is oversized under multi-season drift in some comparisons; the percentage ignored denominator uncertainty | Yes | f107238 |
| 29 | Fixed control panel (S1: C1, C2, C3, C6 each in place of C\*) | The conclusion should not rest on the selected C\* alone | Yes | f107238 |
| 30 | WIS on incidence dropped (never computed); case-scale WIS is the secondary scale | The protocol listed a metric that no code computed | Yes | f107238 |
| 31 | The protocol's RQ4 (year-aligned vs static embeddings) deferred; RQ4 in this paper is the exploratory question on where embeddings help or hurt | Time and scope | Yes | f107238 |
| 32 | N2 (climate-only level without case history) not run | Compute; not needed for any estimand without case history | Yes | f107238 |
| 33 | Supporting analyses added on the primary rows (Supplementary Methods, section E), all exploratory | Review | Yes | f107238 |
| 34 | Espírito Santo excluded from scoring from 2019-12-29 (Supplementary Methods, section A6); old exclusions reported as a sensitivity | OpenDengue holds false zeros for the state while InfoDengue shows cases | Yes (found in review) | f107238 |
| 35 | Long-window secondary analysis (L0–L3 trained on 2013 to Y − 1) not run | Compute before the preprint; it does not involve the embeddings (AlphaEarth starts in 2017). Limitation: at the 2020 origin every rung trains on two target years | Yes (after review of the full draft) | Deposit commit, 18 November 2026 |
| 36 | 23-quantile WIS (secondary score) not computed; all scores use the median and the 0.1–0.9 deciles | The fitted models output only the median and deciles, so a 23-quantile WIS would need refitting | Yes (after review of the full draft) | Deposit commit, 18 November 2026 |
| 37 | Taiwan per-outbreak and county-level reporting replaced by per-year results (Table S30) and Taiwan's two comparisons in the family of 14 comparisons | Taiwan's test years are almost all zeros, so per-outbreak estimates would rest on a handful of weeks | Yes (after review) | Deposit commit, 18 November 2026 |
| 38 | Exploratory district-label panel without case history: N3 + C6 and N4 + C6 on Brazil S1 test years, seed 0, horizons 1 and 4, primary rows (results in Supplementary Methods, section E5: control gain +1.98%, excess gain −0.04%) | Coordinates (the selected C\*) also carry environmental gradients, so a pure identifier is needed to read the result without case history | Yes for other comparisons; no for these runs (added before they produced any result) | Deposit commit, 18 November 2026 |
| 39 | The embedding gain (L3 → L4) becomes a main measure alongside the excess gain and is shown in Table 2 and Figure 2; the "identity gain" is renamed the "control gain" (wording only; code and file names unchanged) | The selected control often scored worse than L3, so the excess gain alone can understate or overstate the embeddings' contribution | Post hoc, after all 13 comparisons were read; specified before scoring | 8001a92 |
| 40 | Sensitivity selection rule allowing "no control": C\* = none when no candidate beat L3 at 2019 by more than 2 SE; such comparisons then use the embedding gain (Table S45) | The selection rule always selected a control, even when all candidates were worse than L3 (11 of 13 comparisons) | Post hoc, after all 13 comparisons were read; specified before scoring | 8001a92 |
| 41 | Gains from known predictors along the ladder (L1 → L2, L2 → L3, L1 → L3, L3 → L4) with CIs in every future-years comparison, used to anchor the ±1% margin; ±0.5% reported alongside (Table S44) | The ±1% margin was set after the S1 results and needs an empirical anchor | Post hoc, after all 13 comparisons were read; specified before scoring | 8001a92 |
| 42 | Per-year gains with a weighted trend test on training-window length, and a DM test on 2023–2024 for Brazil (Table S46) | Reviewers asked whether the null result is specific to short training windows | Post hoc, after all 13 comparisons were read; specified before scoring | 8001a92 |
| 43 | Equivalence at ±0.5/1/2% with both the EWC and the B = 4 standard errors (Table S47) | Equivalence claims should also hold under the strict-variance check | Post hoc, after all 13 comparisons were read; specified before scoring | 8001a92 |
| 44 | Supplementary "as planned vs as reported" table (Table S43) | One place to see the effect of every post-result choice on the primary family | Post hoc, after all 13 comparisons were read; specified before scoring | 8001a92 |
| 45 | Checks that do not select rows by outcome: Colombian district-years with at least one case; change in 80% coverage and interval width on case and zero weeks (Table S48) | Outcome-defined strata can reward biased forecasts (forecaster's dilemma) | Post hoc, after all 13 comparisons were read; specified before scoring | 8001a92 |
| 46 | Embedding stability: within-district year-to-year cosine against between-district cosine (Table S49) | Shows how far the yearly embedding acts as a fixed district signature | Post hoc, after all 13 comparisons were read; specified before scoring | 8001a92 |
| 47 | Information probe: cross-sectional prediction of district burden from embeddings, coordinates and L3 statics (Table S50, Figure S4) | Separates "no dengue information in the embeddings" from "information redundant with case history at 1–4 weeks" | Post hoc, after all 13 comparisons were read; specified before scoring | 8001a92 |
| 48 | Representation variants V1–V4 (embedding-space risk encoding, PCA-8, causal static 2017–2018 mean, substitution for the L3 block) in five comparisons; Holm within the variant family only (Table S51) | Reviewers asked whether a different use of the embeddings would show a gain | Post hoc, after all 13 comparisons were read; specified before scoring | 8001a92 |
| 49 | Seeds 1–2 for L3, L4, L3 + C\* and L4 + C\* in Colombia (future years, held-out states, regions and districts), Peru and Taiwan (future years) and Brazil held out, and for L3 + C\* and L4 + C\* only in Peru and Taiwan held out (Table S52) | Seed SD is of the same order as several estimates | Post hoc, after all 13 comparisons were read; specified before any new seed was seen | 8001a92 |
| 50 | Taiwan future-years ladder (seasonal naive, negative binomial, L1, shared-configuration L2) and fixed control panel rerun with 2021 (Table S53) | Makes all Taiwan tables use the same rows (141,645 rather than 113,430 in some) | Post hoc, after all 13 comparisons were read; specified before scoring | 8001a92 |
| 51 | Analysis without case history repeated for Colombia held-out states, exploratory (Table S54) | Checks whether the Brazilian pattern without case history holds in a second country | Post hoc, after all 13 comparisons were read; specified before scoring | 8001a92 |
| 52 | Equal-budget per-level tuning of L3 + C\* and L4 + C\* in Colombia S1 (Table S55) | Checks whether one shared configuration favoured or penalised the embedding model | Post hoc, after all 13 comparisons were read; specified before scoring | 8001a92 |
| 53 | A comparison's primary estimate becomes the mean over seeds 0–2 wherever all three seeds exist for both models of an estimand; seed 0 alone becomes a sensitivity analysis (Table S43, Table S52) | Brings every comparison with extra seeds to the estimator already used for Brazil, future years (row 22) | Post hoc, after all 13 comparisons were read; decided 19 November 2026 before any new seed was seen | 8001a92 |
| 54 | Zero-fill stress test (Table S56): in each comparison, a share of zero-filled test weeks is changed to 1 or 3 cases, the stored forecasts of both models are rescored, and the main test is rerun; the share at which each loss stops being significant is compared with the 2.1% of filled weeks that held a probable case in Brazil's 2023 check (Table S4) | A co-author asked how sensitive the losses are to cases hidden by zero-filling, since most scored rows are zero-filled and the losses arise there | Post hoc, after all 14 comparisons were read; scoring only, no model refitted | 40d7faf |

<!-- src: docs/plans/deviations_from_protocol.md rows 1–38; rows 39–53 from ../audits/final_round/TRIAGE_round3.md sections A.4, B and C and docs/methods/round3_runs.md, also recorded in docs/plans/deviations_from_protocol.md rows 39–53 (row 2 validation range corrected per ../audits/review_round/R10_fact_check.md section B; row 13 timing per ../audits/review_round/R6_draft_and_medrxiv.md B MEDIUM 7; row 14 "log incidence" corrected to log(1 + cases) per RESOLUTION_LOG.md section B) -->

#### Documented, not changed

(a) The buffer of the held-out-regions split (S3) is measured from district centres (centroids), while C1, C2 and C4 use a point inside each district (Supplementary Methods, section D). (b) The analysis without case history uses Brazil's L1 configuration. (c) Brazil's control selection under per-level tuning ranks the C3 and C4 controls as they were before their later fixes, and it is used only within the per-level sensitivity analysis. (d) Brazilian rows in the held-out-country split (S5) use the LST screen, while Brazil's S1–S4 runs do not. The screen removes 0.08% of daytime and 0.02% of night-time Brazilian district-months. (e) The window for the outbreak threshold, 2013–2019, includes the training years 2018–2019 but no test year. <!-- src: docs/plans/deviations_from_protocol.md "Documented, not changed" -->

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
| Booster, leaves | A booster is one fitted gradient-boosted model, an ensemble of decision trees; here there is one per quantile and horizon. Leaves are the end nodes of each tree, and more leaves allow more complex trees |
| C1–C6, C4s | Location controls (Table S7) |
| C\*, selected control | The location control chosen for a comparison at the 2019 origin by the selection rule of Supplementary Methods, section B1 |
| Comparison (cell) | One country with one split. "Cell" is the older name and is used only in some code and file names |
| Case scale | WIS computed on raw counts instead of log(1 + cases) |
| Correlogram | Mean correlation between districts' deseasonalised case series as a function of the distance between them; used to set the S3 buffer D (Supplementary Methods, section D3) |
| Cosine similarity | Similarity of the directions of two vectors, from −1 to 1; 1 means the same direction |
| Coverage | Share of observed values inside a central prediction interval (40% or 80%) |
| D | Buffer distance of the held-out-regions split (Brazil 225 km, Colombia 130 km; Supplementary Methods, section D3) |
| Noise control of matching size (dimension-matched) | C3 in the held-out-country split: 64 columns of real embeddings of other districts of the unseen country, which match the embedding block's size and distribution but carry no district identity the model could have learned |
| Delta method | An approximation for the uncertainty of a ratio (here a gain as a percentage of WIS(L3)) when numerator and denominator are both estimated |
| District | Our word for an Admin2 unit |
| DM test | Diebold–Mariano test of equal forecast accuracy [@diebold1995comparing] |
| EE, EECU | Google Earth Engine; Earth Engine compute units (a quota meter) |
| Embedding | A fixed-length numeric vector summarising an object; here, a place's satellite observations in one year |
| Embedding gain, $\Delta_{\text{emb}}$ | WIS(L3) − WIS(L4): how much adding the embeddings to the reference model reduced forecast error. One of the two main measures |
| Embedding model | L4: the reference model plus the satellite embeddings |
| Epidemiological week, year | Sunday-start week; its year is the calendar year of its Wednesday |
| EPIFORGE | Reporting guideline for epidemic forecasting studies (2020) |
| EWC | Equal-weighted cosine long-run variance estimator [@lazarus2018har] |
| Equivalent within the margin | The interval used for equivalence testing lies inside the equivalence margin, so effects larger than the margin are ruled out (Supplementary Methods, section E) |
| Excess gain, $\Delta_{\text{excess}}$ | WIS(L3 + C\*) − WIS(L4 + C\*): how much the embeddings reduced error when the model already had the selected location control. One of the two main measures, and the primary measure of the protocol |
| Future years | The split that forecasts the same districts in years after the training years (S1) |
| Fixed-b | Critical values that treat the number of variance terms B as fixed, which keeps tests closer to their nominal size in short series [@lazarus2018har] |
| GHSL | Global Human Settlement Layer (population and built-up surfaces) |
| h | Forecast horizon in weeks (target week minus origin week) |
| HLN | Harvey–Leybourne–Newbold small-sample correction [@harvey1997testing] |
| Holm | Holm's step-down multiplicity correction [@holm1979simple] |
| IAAFT | Iterative amplitude-adjusted Fourier transform surrogates: random series with a given distribution of values and a given pattern of ups and downs (spectrum); used in the surrogate-series check |
| Identity confound | The possibility that an embedding improves forecasts because it identifies the district, not because of what it says about the environment |
| Control gain, $\Delta_{\text{ctrl}}$ | WIS(L3) − WIS(L3 + C\*): how much adding the selected location control to the reference model reduced error. Earlier drafts called it the identity gain, and code and result files call it `G_id` |
| k-means | A clustering method that splits points into k compact groups; used on district centroids to form the S3 blocks |
| L0–L4 | Steps of the model ladder (Table S6) |
| LightGBM | Gradient-boosted decision trees [@ke2017lightgbm]; here with a quantile loss |
| Location control | An input that tells the model where a district is, which district it is, or how much dengue it usually has, without describing its own environment directly (C1–C6). The controls include the district's average past cases, its coordinates, shuffled embeddings, smooth spatial noise and a district label |
| Main test | The Diebold–Mariano test with the EWC variance estimate and the HLN small-sample correction, with Holm correction across the comparisons of the primary family (Supplementary Methods, section E) |
| Location proxy | A feature that improves forecasts mainly by standing in for where a district is |
| LST | Land-surface temperature (MODIS) |
| MDE | Minimum detectable effect at 80% power and 5% two-sided level |
| MODIS | Moderate Resolution Imaging Spectroradiometer |
| Mondrian recalibration | Recalibration with a separate quantile shift for each bin of the forecast median |
| N3, N4 | Levels without case history: L3 and L4 without case-derived inputs |
| NB | Negative binomial regression |
| NDVI | Normalised difference vegetation index |
| Origin | The last week whose data a forecast may use; forecasts are made at its end |
| Origin-year rows | Scored rows whose origin lies in the same epidemiological year as the target (primary) |
| Outbreak week | A district-week with cases at least max(5, the district's 90th percentile of weekly cases over 2013–2019) |
| q0.9 | The 0.9 quantile of a forecast |
| Quantile | The value below which a given share of the forecast distribution lies; the 0.9 quantile is exceeded with probability 0.1 |
| Zero listed by the source | A week the source lists with 0 cases (Brazil 2020–2021 in the test years) |
| Reference model | L3: the model with case history, climate, remote sensing and population, but without embeddings |
| Strict-variance check | The main test repeated with fewer variance terms (a smaller B), which is less affected by slow drift (Supplementary Methods, section E) |
| Surrogate-series check | P values calibrated on simulated IAAFT series that share the data's distribution and pattern of ups and downs but have no true effect (Supplementary Methods, section E) |
| Row mean | A mean WIS over all scored rows, so weeks with more rows weigh more; used only where a table says so |
| S1–S5 | Evaluation splits: future years (S1), the same districts forecast in later years; held-out states (S2); held-out regions, compact blocks of districts with a buffer around them (S3); held-out districts, assigned at random (S4); and held-out country (S5) |
| SE | Standard error |
| Static history | The historical-risk control (C1) used as a separate step in the analysis without case history |
| Two stricter checks | The strict-variance check and the surrogate-series check together |
| With a location control | A model with the selected control added (+ C\*), as in L3 + C\* and L4 + C\* |
| Spherical harmonics | Smooth functions of position on the globe, used as flexible coordinate features (C2) [@russwurm2024location] |
| T | Number of target weeks in a comparison's weekly series |
| TimesFM | A pretrained time-series foundation model, used zero-shot as a baseline [@das2024timesfm] |
| TOST | Two one-sided tests for equivalence [@lakens2017equivalence] |
| VIIRS | Visible Infrared Imaging Radiometer Suite (night lights) |
| WIS | Weighted interval score [@bracher2021wis]; lower is better. Here from the median and nine deciles (K = 4 intervals), normalised by K + ½ |
| Week-weighted | A mean over target weeks of the within-week mean over districts and horizons, so each week has equal weight (the default in this paper) |
| WIS(L3), reference WIS | Mean WIS of the reference model in the comparison; the denominator of every percentage |
| y − 1 | The year before the target year, the source year of yearly inputs |
| y, Y | y: the target's epidemiological year; Y: the test year of an annual refit |
| Zero-filled week | A district-week missing from the source and set to 0 |
| Zero-shot | Used as released, without training or fine-tuning on our data (TimesFM) |

---

## I. Further limitations

- Calibration. The 80% intervals of the full model (L4 + C\*) covered 61–75% of weeks with cases. In Taiwan's future-years comparison they covered 23%, or 24% without 2021. The other steps of the ladder were similar (56–75%). Adjusting the forecast ranges with earlier test years (causal recalibration) raised coverage mainly in Peru. <!-- src: T2_ladder.csv cov_80_nonzero for L4+C* (range 0.609–0.752; TW_S1 0.231 with 2021, 0.241 without); L1–L4+C* outside TW_S1 0.558–0.752; S5_recalibration.csv cov80pos_L4+C* (PE 0.67 → 0.76–0.77; others ≤ 0.03 change) -->
- Countries. Peru (115 provinces) was not shown to be equivalent within ±1%. The smallest effect the test could reliably detect was 0.95% for future years and 1.53% with Peru held out. Taiwan's data are almost all zeros, with 95 non-zero training targets at the 2019 tuning origin, so its tuning and control selection carry almost no information. Case definitions differ: probable cases in Brazil, all reported cases as labelled by OpenDengue ("Total") in Colombia, probable and confirmed cases in Peru, and locally acquired confirmed cases by week of onset in Taiwan. Percentages therefore compare models within a country. <!-- src: T1_primary_family.csv PE_S1 MDE_pct (0.95, three seeds), PE_S5 (1.53); docs/methods/s1_pipeline.md "Pre-flight findings" (Taiwan 95 non-zero training targets); R2_data_scoring.md (case definitions) -->
- Covariates and geometry. The land-surface-temperature screen was off in Brazil's within-country runs. Population grids exceed Brazil's 2022 census by 4–10%. The buffer of the held-out-regions split is measured from district centres, and 0.2–0.4% of training districts in a fold fall inside it when distances are measured from points inside each district. The quality exclusions use neighbouring weeks, though dropping them changes no result. <!-- src: NOTES_FOR_WRITERS.md item 23; docs/features/remote_sensing.md (GHSL +4–10% vs 2022 census); RESOLUTION_LOG.md section C (S3 buffer: 44 BR and 13 CO unit-folds; RA3 no-exclusion) -->
- Information dated after the forecast. The AlphaEarth annual layers were released on 30 July 2025 by a model trained on data that extend into our test years [@brown2025alphaearth]. Population is interpolated towards a 2025 projection. The district universe, districts that ever reported a case, uses hindsight: 565 districts first reported in 2018 or later, including 111 Brazilian municipalities first in 2024. Supplementary Methods, section D, lists every such item. <!-- src: R8_literature.md section 4; R10_fact_check.md row 2; docs/data/completeness_v1.md "Other exclusion files" -->
- Filled zeros. In Brazil in 2024, 1.5% of absent weeks held one to three probable cases, with Espírito Santo excluded. Taiwan's township match was inferred from counts, so agreement in counts does not validate it; a check of names matched all 287 townships (Supplementary Methods, section A3). <!-- src: docs/data/zero_fill_crosscheck_2024.md (excluding Espírito Santo); R1_timing_leakage.md section 4 -->
- Inference. The earlier size simulations were computed before the origin-year filter and the Espírito Santo exclusion. In them, the main test wrongly found an effect in 10–22% of simulated series with no real effect, against a nominal 5%, in the comparisons with drift across several seasons. The rate reached 28% under a stress test and 10–12% in seed placebos (Supplementary Methods, section E3). On the final rows, the surrogate-series calibration gave a size of 14% to 18% in five comparisons: Brazil's future years, held-out states, held-out regions and held-out districts, and Colombia held out (Supplementary Results, Table S47). <!-- src: R3_A8_iaaft_equivalence.csv size_nominal5 (BR_S1–S4, CO_S5) --> On the current rows, with Holm correction, the two stricter checks give the following picture (Table S26). The loss in Colombia's held-out states stays significant under both checks. The losses with Brazil held out and in Colombia's future years and held-out regions stay significant under one of them, the surrogate-series check. The losses in Colombia's held-out districts and with Taiwan held out stay significant under neither. <!-- src: RC_summary.md size table and real placebo; T1_primary_family.csv B4_Holm_p, p_iaaft_Holm -->
