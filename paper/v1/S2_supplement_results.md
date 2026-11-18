# Supplementary Results

Unless a table states otherwise, the following conventions apply. Forecasts are scored with the weighted interval score (WIS) on log(1 + cases), computed from the median and the deciles 0.1 to 0.9. Rows are district × target week × horizon, with horizons 1 and 4 pooled. Only origin-year rows are scored, that is, forecasts whose origin lies in the target's epidemiological year. Scoring uses the primary exclusions: districts without a boundary polygon, two incomplete Peruvian department-weeks, and Espírito Santo from 29 December 2019. Taiwan includes test year 2021. Gains are percentages of the reference model's WIS on the same rows (L3, or N3 without case history), and positive values mean that the added input improves the forecast. Confidence intervals (CIs) and p values come from Diebold–Mariano (DM) tests on the weekly mean loss difference, with the equal-weighted cosine (EWC) variance and the Harvey–Leybourne–Newbold (HLN) correction. p values are unadjusted unless marked Holm. Percentages have two decimals, p values two significant digits with a floor of <0.001, and WIS four decimals.

Model codes: L0, seasonal naive; L1, case history; L2, adds weekly climate; L3, adds remote sensing and population (the reference model); L4, adds the AlphaEarth embeddings; C\*, the selected location control; N3 and N4, L3 and L4 without any case-derived input. Location controls: C1, historical risk; C2, coordinates; C3, shuffled embedding; C4 and C4s, random smooth fields at the fitted and at a short range; C5, 2023 embedding snapshot; C6, district identifier. Splits: S1, new years; S2, held-out states; S3, held-out regions; S4, held-out districts; S5, held-out country. A cell is one country and split.

The reference WIS and the gains in Table 2 and Tables S21 and S24 to S27 are means over target weeks of within-week means, so each week has equal weight. Tables S17 to S20 and S41 report means over rows, so their WIS values differ slightly (Brazil, new years, L3: 0.1675 as a week mean, 0.1681 as a row mean). <!-- src: T1_primary_family.csv BR_S1 WIS_L3 0.16753; T2_ladder.csv BR_S1 L3 0.1681 -->

## A. Baselines and model ladder

**Table S17. Forecast error of the baseline and ladder models in the new-years split.**

<!-- src: S1_baselines.csv, rows with pooled_over = 1,4; columns wis_log, rel_wis_vs_L0, cov_80, cov_80_nonzero; n_rows per country -->
| Model | Brazil | Colombia | Peru | Taiwan (without 2021) |
|---|---|---|---|---|
| L0, seasonal naive | 0.4695 (1.00) | 0.3272 (1.00) | 0.6596 (1.00) | 0.0922 (1.00) |
| Negative binomial regression (L1 inputs) | 0.2185 (0.47) | 0.1426 (0.44) | 0.3232 (0.49) | 0.0594 (0.64) |
| TimesFM 2.5, zero-shot | 0.1928 (0.41) | not run | not run | not run |
| LightGBM L1, case history | 0.1700 (0.36) | 0.1226 (0.37) | 0.2442 (0.37) | 0.0394 (0.43) |
| LightGBM L2, + climate | 0.1690 (0.36) | 0.1224 (0.37) | 0.2431 (0.37) | tuned separately only (row below) |
| LightGBM L3, + remote sensing and population | 0.1681 (0.36) | 0.1220 (0.37) | 0.2438 (0.37) | 0.0398 (0.43) |
| LightGBM L4, + embeddings | 0.1677 (0.36) | 0.1225 (0.37) | 0.2462 (0.37) | 0.0402 (0.44) |
| LightGBM L3 + C\* | 0.1680 (0.36) | 0.1221 (0.37) | 0.2445 (0.37) | 0.0400 (0.43) |
| LightGBM L4 + C\* | 0.1676 (0.36) | 0.1226 (0.37) | 0.2462 (0.37) | 0.0402 (0.44) |
| LightGBM L2, tuned separately | – | – | – | 0.0477 (0.52) |
| Rows scored | 2,703,183 | 319,930 | 45,754 | 113,430 |

Note: Mean WIS over rows, with the relative WIS against the seasonal naive baseline (L0) in parentheses. Every model is scored on the same rows (last row). TimesFM was run for Brazil only. C\* is historical risk (C1) in all four countries. Brazil averages three seeds for L3, L4, L3 + C\* and L4 + C\*. Taiwan excludes 2021, because the baseline runs have no 2021 forecasts. Taiwan's L2 model was tuned separately and is not comparable with the other Taiwan rows. The step from L0 to L1 changes both the inputs and the method.

**Table S18. Coverage of 80% prediction intervals in the new-years split.**

<!-- src: S1_baselines.csv, rows with pooled_over = 1,4; columns wis_log, rel_wis_vs_L0, cov_80, cov_80_nonzero; n_rows per country -->
| Model | Brazil | Colombia | Peru | Taiwan (without 2021) |
|---|---|---|---|---|
| L0, seasonal naive | 0.77 / 0.40 | 0.81 / 0.53 | 0.73 / 0.47 | 0.94 / 0.00 |
| Negative binomial regression (L1 inputs) | 0.94 / 0.77 | 0.96 / 0.81 | 0.93 / 0.84 | 0.98 / 0.42 |
| TimesFM 2.5, zero-shot | 0.82 / 0.60 | not run | not run | not run |
| LightGBM L1, case history | 0.91 / 0.68 | 0.93 / 0.72 | 0.84 / 0.70 | 0.98 / 0.24 |
| LightGBM L2, + climate | 0.90 / 0.68 | 0.93 / 0.72 | 0.83 / 0.68 | tuned separately only (row below) |
| LightGBM L3, + remote sensing and population | 0.90 / 0.67 | 0.93 / 0.72 | 0.83 / 0.68 | 0.98 / 0.25 |
| LightGBM L4, + embeddings | 0.90 / 0.67 | 0.93 / 0.71 | 0.83 / 0.68 | 0.98 / 0.24 |
| LightGBM L3 + C\* | 0.90 / 0.66 | 0.93 / 0.71 | 0.83 / 0.67 | 0.98 / 0.24 |
| LightGBM L4 + C\* | 0.90 / 0.66 | 0.93 / 0.71 | 0.83 / 0.67 | 0.98 / 0.24 |
| LightGBM L2, tuned separately | – | – | – | 0.97 / 0.03 |

Note: Share of observations inside the 80% interval, over all rows / over rows with at least one case. Models, rows and seeds as in Table S17.

**Table S19. Mean forecast error along the model ladder in each cell.**

<!-- src: T2_ladder.csv, column `WIS pooled h{1,4}` per cell and label; cov_80 and cov_80_nonzero of L4+C*; n_rows -->
| Cell | C\* | L0 | L1 | L2 | L3 | L4 |
|---|---|---|---|---|---|---|
| Brazil, new years | C1 | 0.4695 | 0.1700 | 0.1690 | 0.1681 | 0.1677 |
| Brazil, held-out states | C1 | – | – | – | 0.1689 | 0.1690 |
| Brazil, held-out regions | C1 | – | – | – | 0.1706 | 0.1709 |
| Brazil, held-out districts | pending <!-- PENDING: BR S4 --> |  |  |  |  |  |
| Brazil, held-out country | C3 | – | – | – | 0.1914 | 0.1921 |
| Colombia, new years | C1 | 0.3272 | 0.1226 | 0.1224 | 0.1220 | 0.1225 |
| Colombia, held-out states | C1 | – | – | – | 0.1224 | 0.1232 |
| Colombia, held-out regions | C1 | – | – | – | 0.1244 | 0.1255 |
| Colombia, held-out districts | C1 | – | – | – | 0.1222 | 0.1229 |
| Colombia, held-out country | C2 | – | – | – | 0.1238 | 0.1239 |
| Peru, new years | C1 | 0.6596 | 0.2442 | 0.2431 | 0.2438 | 0.2462 |
| Peru, held-out country | C3 | – | – | – | 0.2383 | 0.2367 |
| Taiwan, new years (ladder without 2021) | C1 | 0.0922 | 0.0394 | 0.0477 (per-level tuned) | 0.0398 | 0.0402 |
| Taiwan, held-out country | C3 | – | – | – | 0.0205 | 0.0250 |
| Brazil, new years, per-level tuning (sensitivity) | C1 | 0.4695 | 0.1700 | 0.1690 | 0.1714 | 0.1710 |
| Taiwan, new years, Brazil parameters (sensitivity) | C1 | – | – | – | 0.0398 | 0.0402 |

Note: Mean WIS over rows (lower is better), on rows common to every model. L0 to L2 were run in the new-years split only. Brazil, new years, averages three seeds. The Taiwan new-years ladder excludes 2021 (its L0 to L2 runs have no 2021 forecasts; Table 2 includes 2021), and its L2 model was tuned separately. Sensitivity rows: Brazil, new years, with each model tuned separately (L3 and L4 at 31 leaves, as in the original protocol, with the earlier control selection); Taiwan, new years, with Brazil's configuration and C\* (without 2021).

**Table S20. Forecast error with the location control, and interval coverage, in each cell.**

<!-- src: T2_ladder.csv, column `WIS pooled h{1,4}` per cell and label; cov_80 and cov_80_nonzero of L4+C*; n_rows -->
| Cell | L3 + C\* | L4 + C\* | 80% coverage of L4 + C\*, all rows / cases > 0 | Rows |
|---|---|---|---|---|
| Brazil, new years | 0.1680 | 0.1676 | 0.90 / 0.66 | 2,703,183 |
| Brazil, held-out states | 0.1690 | 0.1690 | 0.90 / 0.66 | 2,703,183 |
| Brazil, held-out regions | 0.1707 | 0.1710 | 0.90 / 0.66 | 2,703,183 |
| Brazil, held-out districts | pending <!-- PENDING: BR S4 --> |  |  |  |
| Brazil, held-out country | 0.1912 | 0.1924 | 0.88 / 0.64 | 2,703,183 |
| Colombia, new years | 0.1221 | 0.1226 | 0.93 / 0.71 | 319,930 |
| Colombia, held-out states | 0.1225 | 0.1231 | 0.92 / 0.70 | 319,930 |
| Colombia, held-out regions | 0.1246 | 0.1254 | 0.92 / 0.70 | 319,930 |
| Colombia, held-out districts | 0.1224 | 0.1229 | 0.92 / 0.71 | 319,930 |
| Colombia, held-out country | 0.1249 | 0.1246 | 0.94 / 0.75 | 319,930 |
| Peru, new years | 0.2445 | 0.2462 | 0.83 / 0.67 | 45,754 |
| Peru, held-out country | 0.2394 | 0.2371 | 0.84 / 0.67 | 45,754 |
| Taiwan, new years (ladder without 2021) | 0.0400 | 0.0402 | 0.98 / 0.24 | 113,430 |
| Taiwan, held-out country | 0.0212 | 0.0248 | 0.99 / 0.61 | 141,645 |
| Brazil, new years, per-level tuning (sensitivity) | 0.1714 | 0.1710 | 0.90 / 0.68 | 2,703,183 |
| Taiwan, new years, Brazil parameters (sensitivity) | 0.0401 | 0.0403 | 0.98 / 0.24 | 113,430 |

Note: Mean WIS over rows. Rows and seeds as in Table S19.

## B. Primary family: secondary gains, control selection and equivalence

**Table S21. Reference error, embedding gain and identity gain in each cell.**

<!-- src: T1_primary_family.csv WIS_L3 per cell (moved from main Table 2) -->
<!-- src: T1_primary_family.csv, one row per cell: test_years; n_rows; n_seeds; WIS_L4C; G_emb_pct, G_emb_lo95_pct, G_emb_hi95_pct; G_id_pct, G_id_lo95_pct, G_id_hi95_pct; DM_p; TOST_p_Holm. Values moved unchanged from draft v1 Table 2, which the number verifier checked cell by cell against T1. -->
| Cell | Reference WIS (L3) | WIS of L4 + C\* | Embedding gain, % (95% CI) | Identity gain, % (95% CI) | DM p, excess gain | Holm TOST p (±1%) |
|---|---|---|---|---|---|---|
| Brazil, new years | 0.1675 | 0.1671 | +0.26 (−0.31 to 0.82) | +0.03 (−0.11 to 0.18) | 0.39 | 0.031 |
| Brazil, held-out states | 0.1683 | 0.1684 | −0.02 (−0.34 to 0.30) | −0.05 (−0.13 to 0.02) | 1.0 | <0.001 |
| Brazil, held-out regions | 0.1701 | 0.1704 | −0.13 (−0.35 to 0.09) | −0.03 (−0.14 to 0.08) | 0.090 | <0.001 |
| Brazil, held-out districts | pending <!-- PENDING: BR S4 --> |  |  |  |  |  |
| Brazil, held-out country | 0.1907 | 0.1917 | −0.34 (−1.24 to 0.56) | +0.10 (−0.75 to 0.96) | <0.001 | 0.010 |
| Colombia, new years | 0.1222 | 0.1227 | −0.36 (−0.58 to −0.13) | −0.07 (−0.34 to 0.20) | 0.0011 | <0.001 |
| Colombia, held-out states | 0.1226 | 0.1233 | −0.59 (−0.80 to −0.37) | −0.08 (−0.13 to −0.04) | <0.001 | 0.0011 |
| Colombia, held-out regions | 0.1245 | 0.1255 | −0.83 (−1.14 to −0.52) | −0.13 (−0.22 to −0.05) | 0.0033 | 0.18 |
| Colombia, held-out districts | 0.1224 | 0.1231 | −0.52 (−0.75 to −0.28) | −0.13 (−0.18 to −0.08) | 0.0028 | 0.0018 |
| Colombia, held-out country | 0.1240 | 0.1247 | −0.04 (−0.37 to 0.28) | −0.81 (−1.16 to −0.46) | 0.27 | 0.0059 |
| Peru, new years | 0.2418 | 0.2441 | −0.94 (−1.70 to −0.18) | −0.26 (−1.05 to 0.53) | 0.056 | 0.57 |
| Peru, held-out country | 0.2362 | 0.2350 | +0.68 (−0.59 to 1.96) | −0.44 (−0.80 to −0.07) | 0.079 | 0.94 |
| Taiwan, new years | 0.0312 | 0.0315 | −1.06 (−1.96 to −0.16) | −0.63 (−1.68 to 0.43) | 0.049 | 0.35 |
| Taiwan, held-out country | 0.0202 | 0.0243 | −21.60 (−31.82 to −11.39) | −3.36 (−6.52 to −0.20) | 0.0017 | 1.0 |

Note: Same rows, tests and C\* as Table 2. The reference WIS is a mean over target weeks of within-week means. The embedding gain compares L3 with L4, and the identity gain compares L3 with L3 + C\*. DM p is the unadjusted p value of the excess gain. The Holm TOST p tests equivalence within ±1% of the reference WIS, Holm-adjusted over the 13 completed cells [pending] <!-- PENDING: final Holm m=14 -->. Brazil, new years, averages three seeds; other cells use one. Test years and rows are in Table 1.

**Table S22. Selection of the location control at the 2019 origin: reference model, historical risk, coordinates and shuffled embedding.**

<!-- src: T4_cstar_selection.csv, column wis_log_2019 per cell and candidate (3-seed mean for C3, C4, C4s), `selected`, C_star -->
| Cell | Reference (L3 or N3) | + C1 | + C2 | + C3 | Selected C\* |
|---|---|---|---|---|---|
| Brazil, new years | 0.17525 | 0.17446 | 0.17715 | 0.17681 | C1 |
| Brazil, held-out states | 0.17542 | 0.17597 | 0.17733 | 0.17757 | C1 |
| Brazil, held-out regions | 0.17715 | 0.17749 | 0.17989 | 0.17916 | C1 |
| Brazil, held-out districts | pending <!-- PENDING: BR S4 --> |  |  |  |  |
| Brazil, held-out country | 0.19102 | – | 0.19168 | 0.19182 | C3 |
| Colombia, new years | 0.17019 | 0.17046 | 0.17045 | 0.17042 | C1 |
| Colombia, held-out states | 0.17169 | 0.17176 | 0.17211 | 0.17219 | C1 |
| Colombia, held-out regions | 0.17311 | 0.17315 | 0.17387 | 0.17381 | C1 |
| Colombia, held-out districts | 0.17158 | 0.17167 | 0.17201 | 0.17225 | C1 |
| Colombia, held-out country | 0.18208 | – | 0.17809 | 0.18352 | C2 |
| Peru, new years | 0.16194 | 0.16258 | 0.16431 | 0.16537 | C1 |
| Peru, held-out country | 0.13892 | – | 0.14227 | 0.13997 | C3 |
| Taiwan, new years | 0.0041143 | 0.0041315 | 0.0043898 | 0.0040175 | C1 |
| Taiwan, held-out country | 0.0065580 | – | 0.0091207 | 0.0078422 | C3 |
| Brazil, new years, without case history | 0.35428 | – | 0.34633 | 0.35963 | C2 |
| Brazil, held-out states, without case history | 0.36193 | – | 0.35921 | 0.36860 | C2 |

Note: Mean WIS at the 2019 validation origin (trained on 2018 targets and scored on 2019 targets; horizons 1 and 4) of the reference model and of the reference model plus each candidate control. C3 is a mean over three seeds; the other columns use one seed. Selection rule v2 (D19): candidates whose forecasts equal the reference model's are excluded; the tie set contains candidates within two seed standard errors of the best score; the first tie-set member in the order C1, C3, C2, C4s, C4, C5 is selected (without case history: C3, C2, C6, C4s, C4). A dash means not a candidate. C1 is not defined across countries. C4s is not a candidate in Peru and Taiwan, where its range equals that of C4. C5 is not a candidate without case history, where C1 forms its own step. C6 is used only in the new-years split without case history. A control scored below L3 only in Brazil (new years), Colombia (held-out country) and Taiwan (new years); in Taiwan the lower-scoring C3 was not selected because of the priority rule. The selection for Brazil, held-out states, without case history is shown; its test-year results are [pending]. <!-- PENDING: BR S2 no-history: delete the last clause after the fill -->

**Table S23. Selection of the location control at the 2019 origin: random smooth fields, snapshot and identifier.**

<!-- src: T4_cstar_selection.csv, column wis_log_2019 per cell and candidate (3-seed mean for C3, C4, C4s), `selected`, C_star -->
| Cell | + C4 | + C4s | + C5 | + C6 |
|---|---|---|---|---|
| Brazil, new years | 0.17782 | 0.17840 | 0.17732 | – |
| Brazil, held-out states | 0.17773 | 0.17900 | 0.17766 | – |
| Brazil, held-out regions | 0.18093 | 0.18162 | 0.18033 | – |
| Brazil, held-out districts | pending <!-- PENDING: BR S4 --> |  |  |  |
| Brazil, held-out country | 0.19235 | 0.19247 | 0.19252 | – |
| Colombia, new years | 0.17096 | 0.17088 | 0.17093 | – |
| Colombia, held-out states | 0.17288 | 0.17279 | 0.17249 | – |
| Colombia, held-out regions | 0.17490 | 0.17453 | 0.17455 | – |
| Colombia, held-out districts | 0.17269 | 0.17269 | 0.17279 | – |
| Colombia, held-out country | 0.18349 | 0.18367 | 0.18290 | – |
| Peru, new years | 0.16684 | 0.16664 | 0.16372 | – |
| Peru, held-out country | 0.14111 | – | 0.14149 | – |
| Taiwan, new years | 0.0043931 | – | 0.0044552 | – |
| Taiwan, held-out country | 0.0078206 | – | 0.011081 | – |
| Brazil, new years, without case history | 0.34895 | 0.35076 | – | 0.34722 |
| Brazil, held-out states, without case history | 0.35977 | 0.36747 | – | – |

Note: As Table S22. C4 and C4s are means over three seeds.

**Table S24. Equivalence of the excess gain at margins of ±0.5%, ±1% and ±2% of the reference WIS.**

<!-- src: T1b_margin_sensitivity.csv per cell and margin_pct: G_excess_pct, lo90_pct, hi90_pct, within_unadjusted, within_Holm, near_margin -->
| Cell | Excess gain, % (90% CI) | ±0.5%: unadjusted / Holm | ±1%: unadjusted / Holm | ±2%: unadjusted / Holm |
|---|---|---|---|---|
| Brazil, new years | +0.23 (−0.23 to 0.69) | no / no | yes / yes | yes / yes |
| Brazil, held-out states | −0.00 (−0.28 to 0.28) | yes / yes | yes / yes | yes / yes |
| Brazil, held-out regions | −0.16 (−0.31 to −0.01) | yes / yes | yes / yes | yes / yes |
| Brazil, held-out districts | pending <!-- PENDING: BR S4 --> |  |  |  |
| Brazil, held-out country | −0.60 (−0.80 to −0.40) | no / no | yes / yes | yes / yes |
| Colombia, new years | −0.39 (−0.55 to −0.23) | no / no (near margin) | yes / yes | yes / yes |
| Colombia, held-out states | −0.47 (−0.65 to −0.29) | no / no | yes / yes | yes / yes |
| Colombia, held-out regions | −0.65 (−0.97 to −0.34) | no / no | yes / no (near margin) | yes / yes |
| Colombia, held-out districts | −0.43 (−0.64 to −0.23) | no / no | yes / yes | yes / yes |
| Colombia, held-out country | +0.22 (−0.12 to 0.55) | no / no | yes / yes | yes / yes |
| Peru, new years | −0.70 (−1.29 to −0.11) | no / no | no / no | yes / yes |
| Peru, held-out country | +0.96 (0.07 to 1.85) | no / no | no / no | yes / no |
| Taiwan, new years | −0.60 (−1.09 to −0.11) | no / no | no / no | yes / yes |
| Taiwan, held-out country | −17.30 (−25.31 to −9.28) | no / no | no / no | no / no |
| Cells within the margin (of 13) <!-- PENDING: final Holm m=14 and BR S4: recount --> |  | 2 / 2 | 9 / 8 | 12 / 11 |

Note: The excess gain is shown with its 90% CI. A cell lies within the margin when both one-sided tests (TOST) reject at 5%, unadjusted or with the TOST p values Holm-adjusted over the 13 completed cells [pending] <!-- PENDING: final Holm m=14 -->. Near margin: a CI bound lies within 0.05 percentage points of the margin. The ±1% margin was chosen after the Brazil and Peru new-years results had been seen. Equivalence for Brazil (new years and held-out states) and Colombia (held-out country) assumes no drift in the weekly loss difference across seasons.

## C. Robustness of the primary family

**Table S25. Excess gain at horizons 1 and 4 separately.**

<!-- src: T3_estimands.csv rows test_year = pooled, estimand = G_excess, horizon 1 / 4 (pct_of_ref, lo95_pct, hi95_pct, p); S1 secondary pooling from T1_primary_family.csv sec_pct, sec_lo95_pct, sec_hi95_pct, sec_DM_p, sec_years -->
| Cell | Horizon 1: % (95% CI); p | Horizon 4: % (95% CI); p | Horizons 1 to 4, new years only: % (95% CI); p; years |
|---|---|---|---|
| Brazil, new years | +0.11 (−0.14 to 0.36), 0.36 | +0.32 (−0.48 to 1.13), 0.40 | +0.25 (−0.33 to 0.82), 0.38; 2020–24 |
| Brazil, held-out states | −0.01 (−0.19 to 0.18), 0.95 | −0.00 (−0.47 to 0.47), 0.99 | – |
| Brazil, held-out regions | −0.13 (−0.24 to −0.02), 0.022 | −0.18 (−0.43 to 0.07), 0.14 | – |
| Brazil, held-out districts | pending <!-- PENDING: BR S4 --> |  |  |
| Brazil, held-out country | −0.42 (−0.63 to −0.20), <0.001 | −0.75 (−1.10 to −0.41), <0.001 | – |
| Colombia, new years | −0.29 (−0.42 to −0.15), <0.001 | −0.50 (−0.78 to −0.21), 0.0026 | −0.39 (−0.61 to −0.17), 0.0023; 2020–22 |
| Colombia, held-out states | −0.41 (−0.56 to −0.26), <0.001 | −0.54 (−0.87 to −0.22), 0.0037 | – |
| Colombia, held-out regions | −0.66 (−0.90 to −0.41), <0.001 | −0.66 (−1.24 to −0.09), 0.028 | – |
| Colombia, held-out districts | −0.30 (−0.49 to −0.12), 0.0039 | −0.57 (−0.91 to −0.23), 0.0034 | – |
| Colombia, held-out country | −0.07 (−0.29 to 0.15), 0.49 | +0.51 (−0.13 to 1.15), 0.11 | – |
| Peru, new years | −0.10 (−0.47 to 0.27), 0.58 | −1.15 (−2.17 to −0.13), 0.030 | −0.63 (−1.35 to 0.08), 0.077; 2020–23 |
| Peru, held-out country | +0.38 (−0.07 to 0.83), 0.089 | +1.36 (−0.19 to 2.91), 0.080 | – |
| Taiwan, new years | +0.07 (−0.97 to 1.12), 0.89 | −1.18 (−2.31 to −0.05), 0.042 | −0.38 (−0.92 to 0.15), 0.14; 2020–24 (no 2021) |
| Taiwan, held-out country | −14.83 (−22.46 to −7.21), <0.001 | −18.87 (−30.84 to −6.90), 0.0043 | – |

Note: The new-years cells also show the secondary pooling over horizons 1 to 4, which is not in the Holm family and uses only test years scored at all four horizons. For Taiwan it therefore excludes 2021, whose runs cover horizons 1 and 4 only.

**Table S26. Excess gain under more cautious statistical tests.**

<!-- src: T1_primary_family.csv per cell: pct_of_WIS_ref, lo95_pct, hi95_pct, DM_p, Holm_p_available; B4_lo95_pct, B4_hi95_pct, B4_p, B4_Holm_p; p_iaaft, p_iaaft_Holm; delta_lo95_pct, delta_hi95_pct; case_pct, case_p; all rows = unfiltered_pct, unfiltered_p; v1 exclusions = exclv1_pct, exclv1_p for Brazil -->
| Cell | Excess gain, % (95% CI) | p / Holm p | B = 4: 95% CI | B = 4: p / Holm p | Surrogate-calibrated p / Holm p | 95% CI, reference WIS estimated |
|---|---|---|---|---|---|---|
| Brazil, new years | +0.23 (−0.33 to 0.79) | 0.39 / 0.80 | −0.53 to 1.00 | 0.45 / 1.0 | 0.51 / 1.0 | −0.28 to 0.75 |
| Brazil, held-out states | −0.00 (−0.34 to 0.34) | 1.0 / 1.0 | −0.57 to 0.56 | 1.0 / 1.0 | 1.0 / 1.0 | −0.34 to 0.34 |
| Brazil, held-out regions | −0.16 (−0.34 to 0.03) | 0.090 / 0.39 | −0.49 to 0.18 | 0.26 / 1.0 | 0.21 / 0.86 | −0.36 to 0.05 |
| Brazil, held-out districts | pending <!-- PENDING: BR S4 --> |  |  |  |  |  |
| Brazil, held-out country | −0.60 (−0.84 to −0.36) | <0.001 / <0.001 | −0.84 to −0.37 | 0.0021 / 0.027 | <0.001 / 0.0065 | −0.94 to −0.26 |
| Colombia, new years | −0.39 (−0.58 to −0.19) | 0.0011 / 0.012 | −0.60 to −0.17 | 0.0072 / 0.079 | <0.001 / 0.010 | −0.59 to −0.19 |
| Colombia, held-out states | −0.47 (−0.69 to −0.25) | <0.001 / 0.0068 | −0.66 to −0.28 | 0.0023 / 0.028 | <0.001 / 0.0065 | −0.71 to −0.24 |
| Colombia, held-out regions | −0.65 (−1.04 to −0.27) | 0.0033 / 0.026 | −1.03 to −0.28 | 0.0084 / 0.084 | <0.001 / 0.0065 | −1.08 to −0.23 |
| Colombia, held-out districts | −0.43 (−0.68 to −0.18) | 0.0028 / 0.025 | −0.73 to −0.13 | 0.016 / 0.14 | 0.0065 / 0.054 | −0.69 to −0.18 |
| Colombia, held-out country | +0.22 (−0.19 to 0.63) | 0.27 / 0.80 | −0.58 to 1.01 | 0.49 / 1.0 | 0.46 / 1.0 | −0.17 to 0.60 |
| Peru, new years | −0.70 (−1.41 to 0.02) | 0.056 / 0.34 | −1.82 to 0.42 | 0.16 / 0.80 | 0.083 / 0.47 | −1.47 to 0.08 |
| Peru, held-out country | +0.96 (−0.13 to 2.05) | 0.079 / 0.39 | 0.22 to 1.70 | 0.023 / 0.16 | 0.0060 / 0.054 | −0.17 to 2.09 |
| Taiwan, new years | −0.60 (−1.20 to −0.00) | 0.049 / 0.34 | −1.40 to 0.20 | 0.10 / 0.63 | 0.078 / 0.47 | −1.72 to 0.52 |
| Taiwan, held-out country | −17.30 (−27.03 to −7.57) | 0.0017 / 0.017 | −29.31 to −5.28 | 0.016 / 0.14 | 0.020 / 0.14 | −40.57 to 5.97 |

Note: Primary test as in Table 2, with Holm adjustment over the 13 completed cells [pending] <!-- PENDING: final Holm m=14 -->. B = 4: the same test with 4 cosine terms in the variance, which is more robust to slow drift across seasons. Surrogate-calibrated p: the observed statistic compared with 2,000 iterative amplitude-adjusted Fourier transform (IAAFT) surrogates of the cell's own weekly loss-difference series. Last column: delta-method 95% CI of the percentage when the reference WIS is treated as estimated. In Brazil, new years (three seeds), the seed standard deviation of the excess gain is 0.00002, against a standard error of 0.00044. <!-- src: T1_primary_family.csv BR_S1 seed_sd, se --> With Peru held out, the excess gain was nominally positive under both cautious tests (B = 4 p = 0.023; surrogate-calibrated p = 0.0060) but not after Holm correction (0.16 and 0.054). <!-- src: T1_primary_family.csv PE_S5 B4_p, p_iaaft, B4_Holm_p, p_iaaft_Holm -->

**Table S27. Excess gain on the case scale, on all rows and without the Espírito Santo exclusion.**

<!-- src: T1_primary_family.csv per cell: pct_of_WIS_ref, lo95_pct, hi95_pct, DM_p, Holm_p_available; B4_lo95_pct, B4_hi95_pct, B4_p, B4_Holm_p; p_iaaft, p_iaaft_Holm; delta_lo95_pct, delta_hi95_pct; case_pct, case_p; all rows = unfiltered_pct, unfiltered_p; v1 exclusions = exclv1_pct, exclv1_p for Brazil -->
| Cell | Case scale, % | Case scale, p | All rows, % | All rows, p | Earlier exclusions, % | Earlier exclusions, p |
|---|---|---|---|---|---|---|
| Brazil, new years | −0.03 | 0.92 | +0.26 | 0.39 | +0.23 | 0.40 |
| Brazil, held-out states | −0.73 | 0.025 | +0.03 | 0.89 | −0.01 | 0.94 |
| Brazil, held-out regions | −1.30 | 0.065 | −0.10 | 0.40 | −0.19 | 0.045 |
| Brazil, held-out districts | pending <!-- PENDING: BR S4 --> |  |  |  |  |  |
| Brazil, held-out country | −0.86 | 0.20 | −0.62 | <0.001 | −0.61 | <0.001 |
| Colombia, new years | −0.81 | 0.038 | −0.39 | <0.001 | – | – |
| Colombia, held-out states | −0.64 | 0.18 | −0.48 | <0.001 | – | – |
| Colombia, held-out regions | −0.70 | 0.23 | −0.68 | 0.0027 | – | – |
| Colombia, held-out districts | −0.88 | 0.10 | −0.44 | 0.0018 | – | – |
| Colombia, held-out country | +0.51 | 0.068 | +0.18 | 0.33 | – | – |
| Peru, new years | −1.14 | 0.095 | −0.62 | 0.094 | – | – |
| Peru, held-out country | −0.59 | 0.56 | +1.01 | 0.046 | – | – |
| Taiwan, new years | −0.00 | 0.95 | −0.55 | 0.076 | – | – |
| Taiwan, held-out country | −4.02 | 0.0086 | −17.62 | 0.0011 | – | – |

Note: Case scale: excess gain in the WIS of raw case counts, as a percentage of the case-scale reference WIS (secondary scale). All rows: without the origin-year filter. Earlier exclusions: Brazil scored without the Espírito Santo exclusion. A dash means not applicable.

## D. Where the difference arises

**Table S28. Additive contributions of three types of target week to the excess gain.**

<!-- src: T5_strata.csv, estimand = G_excess, per cell and stratum: row_share; pct_of_ref, lo95_pct, hi95_pct (stratum estimate, % of the stratum's own WIS(L3)); contrib_pct, contrib_lo95_pct, contrib_hi95_pct, contrib_p (additive contribution, % of the cell's WIS(L3)); total_pct -->
| Cell | Total, % | Weeks with cases, % (95% CI) | Recorded zeros, % (95% CI) | Zero-filled weeks, % (95% CI) |
|---|---|---|---|---|
| Brazil, new years | +0.23 | +0.46 (−0.16 to 1.07) | −0.02 (−0.16 to 0.12) | −0.20 (−0.33 to −0.08) |
| Brazil, held-out states | −0.00 | +0.14 (−0.27 to 0.54) | +0.05 (−0.07 to 0.16) | −0.18 (−0.30 to −0.06) |
| Brazil, held-out regions | −0.16 | +0.22 (−0.02 to 0.47) | −0.03 (−0.17 to 0.11) | −0.35 (−0.52 to −0.18) |
| Brazil, held-out districts | pending <!-- PENDING: BR S4 --> |  |  |  |
| Brazil, held-out country | −0.60 | +0.28 (0.05 to 0.50) | −0.22 (−0.46 to 0.02) | −0.66 (−0.85 to −0.47) |
| Colombia, new years | −0.39 | +0.21 (−0.20 to 0.61) | – | −0.59 (−1.00 to −0.19) |
| Colombia, held-out states | −0.47 | +0.22 (−0.18 to 0.61) | – | −0.69 (−1.07 to −0.31) |
| Colombia, held-out regions | −0.65 | +0.10 (−0.19 to 0.40) | – | −0.76 (−1.23 to −0.29) |
| Colombia, held-out districts | −0.43 | +0.26 (−0.16 to 0.68) | – | −0.69 (−1.13 to −0.25) |
| Colombia, held-out country | +0.22 | +0.27 (0.06 to 0.49) | – | −0.05 (−0.51 to 0.41) |
| Peru, new years | −0.70 | +0.04 (−0.74 to 0.83) | – | −0.74 (−0.99 to −0.49) |
| Peru, held-out country | +0.96 | +1.28 (0.22 to 2.33) | – | −0.32 (−0.51 to −0.12) |
| Taiwan, new years | −0.60 | −0.07 (−0.34 to 0.20) | – | −0.53 (−1.22 to 0.17) |
| Taiwan, held-out country | −17.30 | +1.28 (−1.06 to 3.61) | – | −18.57 (−28.18 to −8.97) |
| Brazil, new years, per-level tuning, 31 leaves (sensitivity) | +0.25 | +0.27 (−0.04 to 0.59) | +0.01 (−0.08 to 0.11) | −0.03 (−0.09 to 0.02) |
| Taiwan, new years, without 2021 | −0.44 | −0.07 (−0.35 to 0.20) | – | −0.36 (−1.04 to 0.31) |
| Taiwan, held-out country, without 2021 | −11.16 | +1.33 (−1.12 to 3.77) | – | −12.48 (−16.99 to −7.97) |
| Brazil, new years, without case history (N3 + C2 vs N4 + C2) | −0.43 | +0.77 (−1.27 to 2.80) | −0.29 (−0.78 to 0.20) | −0.91 (−1.46 to −0.35) |

Note: Each contribution is a percentage of the cell's reference WIS, and the three contributions add up exactly to the total. Recorded zeros are zero weeks listed by the source (Brazil 2020 to 2021 test years only); zero-filled weeks are weeks missing from the source and set to zero. A dash means that the cell has no rows of this type. Extra rows: Brazil, new years, with each model tuned separately (31 leaves); Taiwan without 2021; Brazil, new years, without case history (N4 + C2 vs N3 + C2, as percentages of the WIS of N3).

**Table S29. Excess gain within each type of target week.**

<!-- src: T5_strata.csv, estimand = G_excess, per cell and stratum: row_share; pct_of_ref, lo95_pct, hi95_pct (stratum estimate, % of the stratum's own WIS(L3)); contrib_pct, contrib_lo95_pct, contrib_hi95_pct, contrib_p (additive contribution, % of the cell's WIS(L3)); total_pct -->
| Cell | Cases > 0: share | Cases > 0: % (95% CI) | Recorded zeros: share | Recorded zeros: % (95% CI) | Zero-filled: share | Zero-filled: % (95% CI) |
|---|---|---|---|---|---|---|
| Brazil, new years | 27% | +0.30 (−0.16 to 0.76) | 21% | −0.27 (−2.74 to 2.20) | 52% | −1.67 (−2.65 to −0.69) |
| Brazil, held-out states | 27% | −0.00 (−0.42 to 0.42) | 21% | +0.72 (−1.33 to 2.78) | 52% | −1.48 (−2.58 to −0.38) |
| Brazil, held-out regions | 27% | +0.28 (−0.01 to 0.58) | 21% | −0.34 (−2.71 to 2.03) | 52% | −2.75 (−4.39 to −1.11) |
| Brazil, held-out districts | pending <!-- PENDING: BR S4 --> |  |  |  |  |  |
| Brazil, held-out country | 27% | +0.55 (0.15 to 0.95) | 21% | −2.69 (−5.35 to −0.03) | 52% | −5.22 (−6.17 to −4.27) |
| Colombia, new years | 21% | +0.28 (−0.30 to 0.86) | – | – | 79% | −2.11 (−3.52 to −0.69) |
| Colombia, held-out states | 21% | +0.26 (−0.32 to 0.84) | – | – | 79% | −2.46 (−3.78 to −1.13) |
| Colombia, held-out regions | 21% | +0.15 (−0.31 to 0.60) | – | – | 79% | −2.55 (−4.13 to −0.98) |
| Colombia, held-out districts | 21% | +0.31 (−0.32 to 0.94) | – | – | 79% | −2.48 (−4.00 to −0.97) |
| Colombia, held-out country | 21% | +0.37 (0.07 to 0.66) | – | – | 79% | −0.13 (−2.25 to 1.98) |
| Peru, new years | 44% | −0.08 (−0.94 to 0.77) | – | – | 56% | −6.14 (−8.64 to −3.65) |
| Peru, held-out country | 44% | +1.61 (0.26 to 2.95) | – | – | 56% | −2.97 (−4.73 to −1.22) |
| Taiwan, new years | 2% | −0.15 (−1.21 to 0.91) | – | – | 98% | −9.46 (−22.14 to 3.23) |
| Taiwan, held-out country | 2% | +2.16 (0.27 to 4.04) | – | – | 98% | −48.47 (−72.97 to −23.97) |
| Brazil, new years, per-level tuning, 31 leaves (sensitivity) | 27% | +0.22 (−0.03 to 0.46) | 21% | +0.30 (−1.54 to 2.14) | 52% | −0.06 (−0.65 to 0.54) |
| Taiwan, new years, without 2021 | 3% | −0.15 (−1.21 to 0.91) | – | – | 97% | −6.74 (−19.50 to 6.02) |
| Taiwan, held-out country, without 2021 | 3% | +2.16 (0.27 to 4.04) | – | – | 97% | −35.22 (−48.16 to −22.27) |
| Brazil, new years, without case history (N3 + C2 vs N4 + C2) | 27% | +0.58 (−1.16 to 2.31) | 21% | −6.09 (−17.44 to 5.25) | 52% | −15.77 (−24.77 to −6.76) |

Note: Share is the share of rows. Each estimate is a percentage of that stratum's own reference WIS, with weeks weighted equally; these estimates are not shares of the total (Table S28). Rows as in Table S28.

**Table S30. Excess gain by test year.**

<!-- src: S8_per_year.csv, estimand = G_excess, per cell and test_year: pct_of_ref, lo95_pct, hi95_pct, p (* = p < 0.05, unadjusted); estimate (absolute, shown ×10^-4 in brackets) for Taiwan -->
| Cell | 2020 | 2021 | 2022 | 2023 | 2024 |
|---|---|---|---|---|---|
| Brazil, new years | −0.22 | −0.67* | +0.12 | +0.42 | +0.88 |
| Brazil, held-out states | −0.38 | −0.77* | −0.07* | +0.32 | +0.41 |
| Brazil, held-out regions | −0.19* | −0.97* | −0.05 | +0.05 | +0.02 |
| Brazil, held-out districts | pending <!-- PENDING: BR S4 --> |  |  |  |  |
| Brazil, held-out country | −0.56 | −1.67* | −0.65* | −0.48 | −0.23 |
| Colombia, new years | −0.56* | −0.34 | −0.22 | – | – |
| Colombia, held-out states | −0.56* | −0.57 | −0.29* | – | – |
| Colombia, held-out regions | −0.68 | −0.76* | −0.54* | – | – |
| Colombia, held-out districts | −0.66* | −0.43 | −0.16 | – | – |
| Colombia, held-out country | +0.80* | −0.31 | −0.02 | – | – |
| Peru, new years | −1.38 | −1.24 | −0.51 | +0.06 | – |
| Peru, held-out country | +1.11 | +1.37 | +1.43* | +0.17 | – |
| Taiwan, new years | −15.69 (−3.9) | −85.74 (−2.6) | −0.23 (−0.0) | −0.04 (−0.5) | −3.06 (−2.3) |
| Taiwan, held-out country | −47.64* (−39.8) | −173.45 (−66.4) | −86.19* (−28.9) | −1.90 (−14.0) | −21.23* (−25.1) |

Note: Percentage of that year's reference WIS. An asterisk marks unadjusted p < 0.05; CIs are in the source file. For Taiwan the absolute excess gain (× 10⁻⁴ WIS) is given in parentheses, because the reference WIS is close to zero outside the 2023 outbreak and the percentages are unstable (2021 had no local cases). Context: 2020 to 2021, COVID-19 pandemic; Peru 2023, record season; Taiwan 2023, outbreak; Brazil 2024, record epidemic.

In all four completed Brazilian cells the excess gain was lowest in 2021 (−0.67% to −1.67%; each unadjusted p < 0.05), a year of the COVID-19 pandemic [@chen2022covid; @roster2024covidbrazil], and highest in 2023 or 2024. The largest yearly estimate was Brazil, new years, in 2024, Brazil's largest recorded epidemic (+0.88%, 95% CI −0.93 to 2.69) [@gurgelgoncalves2024brazil]. Colombia's four within-country cells were negative in every year. Peru (new years) was negative in 2020 to 2022 and +0.06% in its 2023 record season [@munayco2024peru]. Taiwan's yearly percentages are unstable because its reference WIS is near zero outside the 2023 outbreak (2023: new years −0.04%, held out −1.90%). <!-- src: S8_per_year.csv G_excess pct_of_ref, lo95_pct, hi95_pct, p, context -->

**Table S31. Upper quantiles of the forecasts on rows with zero cases.**

<!-- src: S6_q90_mechanism.csv per cell: zero_row_share; dq90_log, dq90_log_lo95, dq90_log_hi95, dq90_log_p; dq90_case, dq90_case_lo95, dq90_case_hi95; G_zero_contrib, G_zero_contrib_lo95, G_zero_contrib_hi95 (×10^4); upper_share_of_zero; q90_share_of_zero -->
| Cell | Zero-case share of rows | Δq0.9, log(1 + cases) (95% CI); p | Δq0.9, cases (95% CI) | Zero-row contribution, WIS × 10⁻⁴ (95% CI) | Share from quantiles above the median | Share from q0.9 alone |
|---|---|---|---|---|---|---|
| Brazil, new years | 73% | +0.006 (0.001 to 0.011); 0.029 | +0.003 (−0.008 to 0.014) | −3.8 (−7.3 to −0.2) | 0.77 | 0.24 |
| Brazil, held-out states | 73% | +0.009 (0.004 to 0.015); 0.0013 | +0.001 (−0.007 to 0.009) | −2.3 (−5.5 to 0.9) | 1.27 | 0.63 |
| Brazil, held-out regions | 73% | +0.027 (0.019 to 0.035); <0.001 | +0.031 (0.020 to 0.042) | −6.5 (−10.6 to −2.3) | 1.19 | 0.65 |
| Brazil, held-out districts | pending <!-- PENDING: BR S4 --> |  |  |  |  |  |
| Brazil, held-out country | 73% | +0.043 (0.028 to 0.058); <0.001 | +0.058 (0.027 to 0.088) | −16.8 (−21.9 to −11.7) | 1.04 | 0.44 |
| Colombia, new years | 79% | +0.017 (0.010 to 0.025); <0.001 | +0.020 (0.004 to 0.036) | −7.2 (−12.2 to −2.3) | 1.00 | 0.42 |
| Colombia, held-out states | 79% | +0.019 (0.012 to 0.027); <0.001 | +0.018 (0.003 to 0.032) | −8.4 (−13.1 to −3.8) | 1.04 | 0.40 |
| Colombia, held-out regions | 79% | +0.025 (0.018 to 0.033); <0.001 | +0.018 (−0.001 to 0.036) | −9.4 (−15.3 to −3.6) | 1.12 | 0.47 |
| Colombia, held-out districts | 79% | +0.017 (0.010 to 0.025); <0.001 | +0.018 (0.003 to 0.033) | −8.5 (−13.8 to −3.1) | 1.05 | 0.36 |
| Colombia, held-out country | 79% | +0.007 (0.000 to 0.014); 0.041 | +0.007 (−0.009 to 0.022) | −0.7 (−6.4 to 5.0) | 2.94 | 1.98 |
| Peru, new years | 56% | +0.037 (0.020 to 0.053); <0.001 | +0.057 (0.031 to 0.083) | −17.9 (−23.9 to −11.9) | 0.74 | 0.23 |
| Peru, held-out country | 56% | +0.017 (0.010 to 0.025); <0.001 | +0.040 (0.022 to 0.058) | −7.5 (−12.1 to −2.9) | 0.66 | 0.30 |
| Taiwan, new years | 98% | +0.002 (−0.001 to 0.006); 0.15 | +0.003 (−0.002 to 0.007) | −1.6 (−3.8 to 0.5) | 1.12 | 0.33 |
| Taiwan, held-out country | 98% | +0.099 (0.067 to 0.130); <0.001 | +0.137 (0.089 to 0.185) | −37.5 (−56.8 to −18.1) | 0.96 | 0.57 |

Note: Δq0.9 is the mean 0.9 quantile of L4 + C\* minus that of L3 + C\* on rows with zero cases, on the log(1 + cases) scale and on the case scale, with a 95% CI from the weekly series. The zero-row contribution is the additive contribution of all zero-case rows (recorded and filled) to the absolute excess gain. The last two columns give the share of that contribution from the quantile levels above the median (0.6 to 0.9) and from the 0.9 quantile alone; values above 1 mean that the lower quantiles offset part of the loss. Colombia's held-out-country shares are unstable because its zero-row contribution is close to zero.

### Supporting analyses

The analyses in Tables S32 to S35 are exploratory and unadjusted for multiplicity. Outbreak weeks made up 0.7% to 22.9% of rows. On them, the excess gain had a CI above zero with Brazil and Peru held out (+3.66% for Peru) and below zero in Brazil (held-out states and held-out regions) and Colombia (held-out regions) (Table S32). <!-- src: S3_outbreak.csv outbreak row_share, pct_of_ref, lo95_pct, hi95_pct --> Under weighting by population or by past cases, only Colombia held out had a CI above zero (+0.49% with case weights). Colombian losses grew under population weighting (to −1.38% with held-out regions), and Peru held out turned negative under both weightings (Table S33). <!-- src: S4_weighted.csv pct_of_ref, lo95_pct, hi95_pct (PE_S5 −1.19 population, −0.73 case) --> Causal recalibration of the quantiles changed the excess gain by 0.16 percentage points or less, except with Peru held out (to −0.05% with Mondrian shifts) and Taiwan held out (to −15.01%). It raised coverage on weeks with cases mainly in Peru (Table S34). <!-- src: S5_recalibration.csv all_years raw vs global/mondrian pct_of_ref; cov80pos_L4+C* --> In strata computed before the origin-year filter and the Espírito Santo exclusion, no population, surveillance-history or urban-growth stratum gained significantly outside Peru held out. Where losses occurred, they were largest in districts with no reported case in 2014 to 2017 (Table S35). <!-- src: docs/results/review/RB_summary.md section 1; RB_strata.csv -->

**Table S32. Excess gain on outbreak and non-outbreak weeks.**

<!-- src: S3_outbreak.csv per cell: stratum outbreak / non_outbreak (row_share, pct_of_ref, lo95_pct, hi95_pct, p, n_weeks) and outbreak_minus_non (p) -->
| Cell | Outbreak share of rows | Outbreak weeks: % (95% CI); p | Other weeks: % (95% CI); p | Difference, p |
|---|---|---|---|---|
| Brazil, new years | 8.2% | +0.08 (−0.77 to 0.92); 0.85 | +0.01 (−0.19 to 0.20); 0.94 | 0.85 |
| Brazil, held-out states | 8.2% | −0.98 (−1.96 to −0.01); 0.048 | +0.15 (−0.06 to 0.36); 0.16 | 0.041 |
| Brazil, held-out regions | 8.2% | −0.98 (−1.73 to −0.23); 0.013 | +0.13 (−0.19 to 0.44); 0.41 | 0.011 |
| Brazil, held-out districts | pending <!-- PENDING: BR S4 --> |  |  |  |
| Brazil, held-out country | 8.2% | +0.87 (0.20 to 1.54); 0.014 | −0.86 (−1.14 to −0.58); <0.001 | 0.0047 |
| Colombia, new years | 2.3% | −0.62 (−2.21 to 0.97); 0.41 | −0.39 (−0.59 to −0.18); 0.0015 | 0.48 |
| Colombia, held-out states | 2.3% | −0.96 (−2.76 to 0.84); 0.26 | −0.43 (−0.65 to −0.22); 0.0010 | 0.31 |
| Colombia, held-out regions | 2.3% | −1.72 (−3.29 to −0.15); 0.035 | −0.52 (−0.98 to −0.05); 0.033 | 0.047 |
| Colombia, held-out districts | 2.3% | −0.92 (−2.80 to 0.96); 0.30 | −0.41 (−0.66 to −0.17); 0.0030 | 0.36 |
| Colombia, held-out country | 2.3% | −0.34 (−1.47 to 0.79); 0.52 | +0.30 (−0.17 to 0.77); 0.19 | 0.46 |
| Peru, new years | 22.9% | −1.26 (−2.90 to 0.37); 0.12 | −0.75 (−1.33 to −0.18); 0.014 | 0.20 |
| Peru, held-out country | 22.9% | +3.66 (1.46 to 5.86); 0.0033 | −0.98 (−1.61 to −0.36); 0.0048 | 0.0012 |
| Taiwan, new years | 0.7% | −0.19 (−1.15 to 0.77); 0.61 | −1.33 (−2.58 to −0.08); 0.039 | 0.64 |
| Taiwan, held-out country | 0.7% | +1.31 (−0.07 to 2.69); 0.058 | −21.21 (−32.87 to −9.54); 0.0014 | 0.039 |

Note: An outbreak week has cases at least max(5, the district's 90th percentile of weekly cases over 2013 to 2019); this window includes the training years 2018 to 2019 but no test year. Each estimate is a percentage of that stratum's own reference WIS. The last column tests the weekly series of the outbreak minus non-outbreak difference.

**Table S33. Excess gain weighted by population or by past cases.**

<!-- src: S4_weighted.csv, estimand G_excess, per cell and weights (unweighted, population, pre_cases_plus1): pct_of_ref, lo95_pct, hi95_pct, p -->
| Cell | Unweighted: % (95% CI); p | Population-weighted: % (95% CI); p | Weighted by 2013 to 2017 mean weekly cases + 1: % (95% CI); p |
|---|---|---|---|
| Brazil, new years | +0.23 (−0.33 to 0.79); 0.39 | +0.03 (−0.40 to 0.46); 0.88 | −0.13 (−0.53 to 0.27); 0.51 |
| Brazil, held-out states | −0.00 (−0.34 to 0.34); 1.0 | −0.15 (−0.53 to 0.22); 0.40 | −0.21 (−0.64 to 0.22); 0.32 |
| Brazil, held-out regions | −0.16 (−0.34 to 0.03); 0.090 | −0.42 (−0.90 to 0.07); 0.086 | −0.58 (−0.99 to −0.16); 0.010 |
| Brazil, held-out districts | pending <!-- PENDING: BR S4 --> |  |  |
| Brazil, held-out country | −0.60 (−0.84 to −0.36); <0.001 | −0.53 (−1.08 to 0.01); 0.054 | −0.44 (−1.00 to 0.12); 0.11 |
| Colombia, new years | −0.39 (−0.58 to −0.19); 0.0011 | −1.03 (−1.53 to −0.52); <0.001 | −0.72 (−1.19 to −0.26); 0.0053 |
| Colombia, held-out states | −0.47 (−0.69 to −0.25); <0.001 | −0.54 (−1.13 to 0.06); 0.072 | −0.40 (−0.88 to 0.09); 0.099 |
| Colombia, held-out regions | −0.65 (−1.04 to −0.27); 0.0033 | −1.38 (−2.18 to −0.57); 0.0032 | −0.40 (−0.83 to 0.02); 0.060 |
| Colombia, held-out districts | −0.43 (−0.68 to −0.18); 0.0028 | −0.67 (−1.33 to −0.01); 0.047 | −0.52 (−1.10 to 0.06); 0.074 |
| Colombia, held-out country | +0.22 (−0.19 to 0.63); 0.27 | +0.51 (−0.02 to 1.04); 0.058 | +0.49 (0.07 to 0.92); 0.026 |
| Peru, new years | −0.70 (−1.41 to 0.02); 0.056 | −1.18 (−3.11 to 0.74); 0.21 | −3.90 (−6.39 to −1.40); 0.0050 |
| Peru, held-out country | +0.96 (−0.13 to 2.05); 0.079 | −1.19 (−2.96 to 0.58); 0.17 | −0.73 (−1.91 to 0.46); 0.21 |
| Taiwan, new years | −0.60 (−1.20 to −0.00); 0.049 | −0.89 (−1.82 to 0.04); 0.060 | −0.80 (−1.63 to 0.02); 0.056 |
| Taiwan, held-out country | −17.30 (−27.03 to −7.57); 0.0017 | −13.78 (−21.93 to −5.63); 0.0025 | −8.72 (−14.20 to −3.25); 0.0038 |

Note: Within each horizon and week, rows are weighted by the district's population in the target year, or by its mean weekly cases in 2013 to 2017 plus 1. Weeks are then averaged as in the primary estimator.

**Table S34. Excess gain after causal recalibration of the quantiles.**

<!-- src: S5_recalibration.csv per cell, years and calibration: pct_of_ref, p; cov80pos_L4+C* -->
| Cell | Raw: %; p | Global shift: %; p | Mondrian shift: %; p | Mondrian, from second test year: %; p | 80% coverage of L4 + C\*, cases > 0: raw → Mondrian |
|---|---|---|---|---|---|
| Brazil, new years | +0.23; 0.39 | +0.23; 0.39 | +0.24; 0.36 | +0.33; 0.29 | 0.66 → 0.69 |
| Brazil, held-out states | −0.00; 1.0 | −0.00; 1.0 | +0.06; 0.76 | +0.15; 0.51 | 0.66 → 0.69 |
| Brazil, held-out regions | −0.16; 0.090 | −0.16; 0.090 | −0.08; 0.51 | −0.06; 0.69 | 0.66 → 0.69 |
| Brazil, held-out districts | pending <!-- PENDING: BR S4 --> |  |  |  |  |
| Brazil, held-out country | −0.60; <0.001 | −0.54; <0.001 | −0.44; <0.001 | −0.42; <0.001 | 0.64 → 0.67 |
| Colombia, new years | −0.39; 0.0011 | −0.39; 0.0011 | −0.40; 0.0089 | −0.29; 0.13 | 0.71 → 0.70 |
| Colombia, held-out states | −0.47; <0.001 | −0.47; <0.001 | −0.48; 0.0038 | −0.42; 0.045 | 0.70 → 0.70 |
| Colombia, held-out regions | −0.65; 0.0033 | −0.65; 0.0033 | −0.61; 0.0041 | −0.57; 0.0046 | 0.70 → 0.70 |
| Colombia, held-out districts | −0.43; 0.0028 | −0.43; 0.0028 | −0.45; 0.012 | −0.31; 0.15 | 0.71 → 0.70 |
| Colombia, held-out country | +0.22; 0.27 | +0.22; 0.27 | +0.25; 0.20 | −0.10; 0.26 | 0.75 → 0.73 |
| Peru, new years | −0.70; 0.056 | −0.69; 0.047 | −0.64; 0.11 | −0.42; 0.37 | 0.67 → 0.76 |
| Peru, held-out country | +0.96; 0.079 | +0.75; 0.16 | −0.05; 0.91 | −0.38; 0.30 | 0.67 → 0.77 |
| Taiwan, new years | −0.60; 0.049 | −0.60; 0.049 | −0.60; 0.049 | −0.35; 0.15 | 0.24 → 0.24 |
| Taiwan, held-out country | −17.30; 0.0017 | −15.02; 0.0026 | −15.01; 0.0027 | −12.01; 0.018 | 0.61 → 0.60 |

Note: Separately for L3 + C\* and L4 + C\*, and per horizon and seed, additive shifts of each quantile on the log(1 + cases) scale are fitted only on earlier test years. A global shift uses one shift per quantile; a Mondrian shift uses one per bin of the forecast median. The first test year has no earlier year and is left unadjusted in the first three result columns; the fourth drops it.

**Table S35. Excess gain by surveillance history and population (exploratory; earlier scoring).**

<!-- src: docs/results/review/RB_strata.csv, estimand = G_excess, dimension history (0, 1-2, 3-4) and pop_tercile (T1-T3): pct_of_own_ref, p, n_units (pre-review scoring: all rows, exclusions v1, Taiwan without 2021) -->
| Cell | No case 2014 to 2017 | Cases in 1 to 2 years | Cases in 3 to 4 years | Population, lowest third | Middle third | Highest third |
|---|---|---|---|---|---|---|
| Brazil, new years | +0.55 (n = 507) | +0.58 | +0.21 | +0.27 | +0.33 | +0.21 |
| Brazil, held-out states | +0.04 (n = 507) | +0.15 | −0.00 | +0.02 | +0.05 | −0.01 |
| Brazil, held-out regions | −1.76* (n = 507) | −0.45* | −0.03 | −0.17 | −0.08 | −0.14 |
| Brazil, held-out country | −2.47* (n = 507) | −1.29* | −0.47* | −0.77* | −0.61* | −0.58* |
| Colombia, new years | −1.14* (n = 65) | −0.66* | −0.38* | −0.82* | −0.42* | −0.28* |
| Colombia, held-out states | −19.74* (n = 65) | −2.74* | −0.39* | −1.27* | −0.52* | −0.27 |
| Colombia, held-out regions | −40.70* (n = 65) | −5.52* | −0.49* | −2.36* | −0.84* | −0.21 |
| Colombia, held-out districts | −7.14* (n = 65) | −2.31* | −0.38* | −1.19* | −0.50* | −0.24 |
| Colombia, held-out country | −11.63* (n = 65) | −0.81 | +0.22 | −0.63* | +0.15 | +0.39 |
| Peru, new years | −0.31 (n = 34) | +0.50 | −0.81* | −0.00 | −0.49 | −1.13* |
| Peru, held-out country | −0.75 (n = 34) | −0.35 | +1.35* | +0.75 | +2.18* | −0.09 |
| Taiwan, new years | −0.50 (n = 42) | −0.56 | −0.24 | +0.12 | −0.09 | −0.66 |
| Taiwan, held-out country | −28.83* (n = 42) | −13.79* | −5.88* | −16.71* | −11.99* | −9.66* |

Note: Excess gain as a percentage of the stratum's own reference WIS; an asterisk marks unadjusted p < 0.05; n is the number of districts with no reported case in 2014 to 2017. History is the number of years in 2014 to 2017 with at least one reported case. Population thirds are formed within each cell and test year from the population in the year before the test year. These strata were computed before the review changes and were not regenerated: they use all rows (no origin-year filter), the earlier exclusions (Espírito Santo included) and Taiwan without 2021, so they differ slightly from the primary estimates. Thirds of urban growth (change in built-up share, 2010 to 2015) are in the source file and show no consistent pattern.

## E. Location controls, sensitivity analyses and transfer to Taiwan

**Table S36. Identity and excess gains with each fixed location control in the new-years split.**

<!-- src: S2_control_panel.csv per country and control: G_id_pct, G_id_pct_lo95, G_id_pct_hi95, G_id_p; G_excess_pct, G_excess_pct_lo95, G_excess_pct_hi95, G_excess_p; G_emb_pct, G_emb_pct_lo95, G_emb_pct_hi95, G_emb_p; status -->
| Country | Control | Identity gain with this control, % (95% CI); p | Excess gain with this control, % (95% CI); p |
|---|---|---|---|
| Brazil | C1 | +0.02 (−0.15 to 0.20); 0.77 | +0.25 (−0.32 to 0.81); 0.37 |
| Brazil | C2 | +0.14 (−0.16 to 0.43); 0.34 | +0.02 (−0.25 to 0.29); 0.88 |
| Brazil | C3 | pending <!-- PENDING: BR C3/C6 panel --> | pending <!-- PENDING: BR C3/C6 panel --> |
| Brazil | C6 | pending <!-- PENDING: BR C3/C6 panel --> | pending <!-- PENDING: BR C3/C6 panel --> |
| Colombia | C1 | −0.07 (−0.34 to 0.20); 0.60 | −0.39 (−0.58 to −0.19); 0.0011 |
| Colombia | C2 | −0.12 (−0.21 to −0.03); 0.016 | −0.34 (−0.59 to −0.10); 0.010 |
| Colombia | C3 | −0.12 (−0.20 to −0.04); 0.0053 | −0.33 (−0.49 to −0.16); 0.0011 |
| Colombia | C6 | −2.37 (−2.80 to −1.94); <0.001 | −0.13 (−0.37 to 0.12); 0.27 |
| Peru | C1 | −0.26 (−1.05 to 0.53); 0.49 | −0.70 (−1.41 to 0.02); 0.056 |
| Peru | C2 | −0.31 (−0.73 to 0.11); 0.13 | −0.86 (−1.57 to −0.14); 0.022 |
| Peru | C3 | −0.76 (−1.48 to −0.04); 0.040 | −0.37 (−0.80 to 0.05); 0.081 |
| Peru | C6 | −6.28 (−9.87 to −2.69); 0.0023 | −0.29 (−1.53 to 0.96); 0.63 |
| Taiwan | C1 | −0.63 (−1.69 to 0.44); 0.23 | −0.44 (−1.01 to 0.14); 0.12 |
| Taiwan | C2 | −0.35 (−0.75 to 0.04); 0.075 | −0.77 (−1.88 to 0.34); 0.16 |
| Taiwan | C3 | −0.59 (−1.30 to 0.12); 0.094 | −0.54 (−1.31 to 0.23); 0.15 |
| Taiwan | C6 | −2.20 (−5.54 to 1.15); 0.18 | −0.42 (−1.08 to 0.23); 0.18 |
| Brazil | none (embedding gain, L3 vs L4) | – | +0.29 (−0.27 to 0.84); 0.29 |
| Colombia | none (embedding gain, L3 vs L4) | – | −0.36 (−0.58 to −0.13); 0.0052 |
| Peru | none (embedding gain, L3 vs L4) | – | −0.94 (−1.70 to −0.18); 0.020 |
| Taiwan | none (embedding gain, L3 vs L4) | – | −0.94 (−1.85 to −0.03); 0.043 |

Note: Each row replaces C\* by one fixed control: C1, historical risk (district mean log(1 + cases) in the years before 2018); C2, coordinates (spherical harmonics); C3, a fixed other district's AlphaEarth series; C6, district identifier (categorical). The identity gain compares L3 with L3 + Ck, and the excess gain compares L3 + Ck with L4 + Ck. The last four rows give the embedding gain without a control. Seed 0 only, so Brazil's C1 row differs slightly from the three-seed value in Table 2. The panel is scored on the same primary rows as Table 2, but the Taiwan rows exclude 2021, because the panel reuses runs made before 2021 was added; Taiwan values are comparable within the panel, not with Table 2. No adjustment for multiplicity. <!-- src: S2_control_panel.csv scoring = v3_excl_v2_origin_year; RE_summary.md caveats -->

**Table S37. Sensitivity analyses of the embedding, identity and excess gains.**

<!-- src: T6a_sensitivities.csv per variant and estimand: variant_pct, variant_lo95_pct, variant_hi95_pct, variant_p, variant_status; primary_pct; variant_years -->
| Variant | Gain | Variant: % (95% CI); p | Primary cell, % |
|---|---|---|---|
| Brazil, new years, yearly inputs keyed to the origin year (strictly causal) | embedding | pending <!-- PENDING: sensitivities yref/delay2 --> | +0.26 (seed 0: +0.29) |
| Brazil, new years, 2-week reporting delay | embedding | pending <!-- PENDING: sensitivities yref/delay2 --> | +0.26 (seed 0: +0.29) |
| Brazil, new years, C3 in place of C\* | embedding | pending <!-- PENDING: BR C3/C6 panel --> | +0.26 |
| Brazil, new years, C3 in place of C\* | identity | pending <!-- PENDING: BR C3/C6 panel --> | +0.03 |
| Brazil, new years, C3 in place of C\* | excess | pending <!-- PENDING: BR C3/C6 panel --> | +0.23 |
| Brazil, new years, C6 in place of C\* | embedding | pending <!-- PENDING: BR C3/C6 panel --> | +0.26 |
| Brazil, new years, C6 in place of C\* | identity | pending <!-- PENDING: BR C3/C6 panel --> | +0.03 |
| Brazil, new years, C6 in place of C\* | excess | pending <!-- PENDING: BR C3/C6 panel --> | +0.23 |
| Brazil, new years, per-level tuning (31 leaves; original protocol) | embedding | +0.21 (−0.05 to 0.47); 0.10 | +0.26 |
| Brazil, new years, per-level tuning (31 leaves; original protocol) | identity | −0.06 (−0.30 to 0.18); 0.62 | +0.03 |
| Brazil, new years, per-level tuning (31 leaves; original protocol) | excess | +0.25 (−0.07 to 0.56); 0.11 | +0.23 |
| Taiwan, new years, Brazil's parameters and C\* (no 2021) | embedding | −0.87 (−1.78 to 0.03); 0.057 | −1.06 |
| Taiwan, new years, Brazil's parameters and C\* (no 2021) | identity | −0.71 (−1.67 to 0.26); 0.14 | −0.63 |
| Taiwan, new years, Brazil's parameters and C\* (no 2021) | excess | −0.33 (−0.89 to 0.23); 0.22 | −0.60 |
| Taiwan, new years without 2021 | embedding | −0.94 (−1.85 to −0.03); 0.043 | −1.06 |
| Taiwan, new years without 2021 | identity | −0.63 (−1.69 to 0.44); 0.23 | −0.63 |
| Taiwan, new years without 2021 | excess | −0.44 (−1.01 to 0.14); 0.12 | −0.60 |
| Taiwan, held-out country without 2021 | embedding | −14.68 (−20.24 to −9.11); <0.001 | −21.60 |
| Taiwan, held-out country without 2021 | identity | −2.31 (−5.52 to 0.90); 0.14 | −3.36 |
| Taiwan, held-out country without 2021 | excess | −11.16 (−15.66 to −6.65); <0.001 | −17.30 |
| Brazil, new years, without case history (reference N3; C\* = C2) | embedding | +2.54 (−0.82 to 5.89); 0.13 | +0.26 |
| Brazil, new years, without case history (reference N3; C\* = C2) | identity | +3.30 (1.68 to 4.93); <0.001 | +0.03 |
| Brazil, new years, without case history (reference N3; C\* = C2) | excess | −0.43 (−2.06 to 1.19); 0.58 | +0.23 |
| Brazil, held-out states, without case history | embedding | pending <!-- PENDING: BR S2 no-history --> | −0.02 |
| Brazil, held-out states, without case history | identity | pending <!-- PENDING: BR S2 no-history --> | −0.05 |
| Brazil, held-out states, without case history | excess | pending <!-- PENDING: BR S2 no-history --> | −0.00 |

Note: The last column repeats the matching primary cell. Per-level tuning: L3 and L4 tuned separately on the 2019 grid (31 leaves, as in the original protocol), with the earlier control selection. Taiwan, new years, with Brazil's configuration and C\* excludes 2021. Taiwan without 2021 is the test-year set used before review. The strictly causal yearly-input and two-week reporting-delay runs refit L3 and L4 only, so they estimate the embedding gain only. Because they use seed 0, their comparator is the seed-0 embedding gain of Brazil, new years, +0.29% (95% CI −0.27 to 0.84; Table S36), not the three-seed +0.26%. <!-- src: S2_control_panel.csv brazil G_emb_pct, G_emb_pct_lo95, G_emb_pct_hi95 --> Rows without case history use N3 as the reference and C2 as C\*.

**Table S38. Forecast error in Taiwan's 2021 test year.**

<!-- src: docs/results/review/RG_tw2021.md, table "2021 rows on their own (v3, mean log-WIS, h {1, 4})" -->
| Cell | L3 | L4 | L3 + C\* | L4 + C\* | Excess gain (absolute) | p |
|---|---|---|---|---|---|---|
| Taiwan, new years | 0.00031 | 0.00050 | 0.00031 | 0.00058 | −0.00026 | 0.077 |
| Taiwan, held-out country | 0.00394 | 0.01171 | 0.00512 | 0.01193 | −0.00665 | 0.091 |

Note: Mean WIS on log(1 + cases) on the 2021 rows, where every target is zero (Taiwan had no local cases in 2021). Seed 0. The last two columns give the absolute excess gain and its unadjusted p value. Percentages are not shown, because the reference WIS is close to zero.

**Table S39. Correlation between a held-out district's gain and its embedding similarity to the training districts.**

<!-- src: S7_embedding_distance.csv, distance = cos_max: spearman_rho, p_naive, n_units per cell and estimand -->
| Cell | Districts | Spearman ρ, excess gain vs similarity (naive p) | Spearman ρ, embedding gain vs similarity (naive p) |
|---|---|---|---|
| Brazil, held-out states | 5,439 | +0.04 (0.0018) | +0.07 (<0.001) |
| Brazil, held-out regions | 5,439 | +0.12 (<0.001) | +0.07 (<0.001) |
| Brazil, held-out country | 5,439 | +0.10 (<0.001) | +0.20 (<0.001) |
| Colombia, held-out states | 1,070 | +0.03 (0.36) | +0.01 (0.82) |
| Colombia, held-out regions | 1,070 | −0.04 (0.16) | −0.01 (0.64) |
| Colombia, held-out districts | 1,070 | +0.07 (0.015) | +0.08 (0.0068) |
| Colombia, held-out country | 1,070 | +0.15 (<0.001) | +0.02 (0.50) |
| Peru, held-out country | 115 | +0.47 (<0.001) | +0.48 (<0.001) |
| Taiwan, held-out country | 285 | −0.13 (0.024) | −0.22 (<0.001) |

Note: Similarity is the maximum cosine similarity between a held-out district's renormalised AlphaEarth vector for year y − 1 and those of the training districts. The p values are naive, because districts are not independent. Exploratory, unadjusted.

**Table S40. Excess gain by similarity quintile in the held-out-country split.**

<!-- src: S7b_embedding_distance_bins.csv, cells BR_S5, CO_S5, PE_S5, TW_S5, per bin: cos_max_lo, cos_max_hi, n_units, zero_share, wis_L3, G_excess, G_excess_lo95, G_excess_hi95 (×10^4), G_excess_share_units_neg -->
| Cell | Similarity quintile (maximum cosine) | Districts | Reference WIS (L3) | Excess gain, WIS × 10⁻⁴ (95% CI) | Districts harmed |
|---|---|---|---|---|---|
| Brazil, held-out country | Q1 (0.43–0.67) | 1088 | 0.1035 | −14.0 (−14.8 to −13.2) | 90% |
| Brazil, held-out country | Q2 (0.67–0.72) | 1088 | 0.1522 | −12.6 (−13.5 to −11.7) | 82% |
| Brazil, held-out country | Q3 (0.72–0.76) | 1087 | 0.1781 | −12.6 (−13.5 to −11.6) | 81% |
| Brazil, held-out country | Q4 (0.76–0.80) | 1088 | 0.2429 | −9.4 (−10.4 to −8.4) | 71% |
| Brazil, held-out country | Q5 (0.80–0.99) | 1088 | 0.2802 | −10.0 (−11.2 to −8.9) | 71% |
| Colombia, held-out country | Q1 (0.53–0.78) | 214 | 0.1015 | −1.6 (−3.6 to 0.5) | 73% |
| Colombia, held-out country | Q2 (0.78–0.81) | 214 | 0.1307 | +1.7 (−0.4 to 3.8) | 58% |
| Colombia, held-out country | Q3 (0.81–0.84) | 214 | 0.1305 | +4.1 (2.1 to 6.1) | 50% |
| Colombia, held-out country | Q4 (0.84–0.86) | 214 | 0.1363 | +6.6 (4.2 to 9.1) | 47% |
| Colombia, held-out country | Q5 (0.86–0.99) | 214 | 0.1201 | +3.4 (1.4 to 5.4) | 57% |
| Peru, held-out country | Q1 (0.62–0.76) | 23 | 0.2211 | −30.4 (−48.0 to −12.8) | 78% |
| Peru, held-out country | Q2 (0.76–0.84) | 23 | 0.2562 | +2.0 (−34.6 to 38.7) | 70% |
| Peru, held-out country | Q3 (0.85–0.88) | 23 | 0.2336 | +41.8 (5.5 to 78.2) | 57% |
| Peru, held-out country | Q4 (0.88–0.92) | 23 | 0.1768 | +37.8 (7.0 to 68.7) | 43% |
| Peru, held-out country | Q5 (0.93–0.99) | 23 | 0.3040 | +64.7 (31.6 to 97.7) | 22% |
| Taiwan, held-out country | Q1 (0.49–0.74) | 57 | 0.0054 | −32.1 (−35.7 to −28.5) | 100% |
| Taiwan, held-out country | Q2 (0.74–0.76) | 57 | 0.0147 | −39.3 (−44.2 to −34.5) | 100% |
| Taiwan, held-out country | Q3 (0.76–0.78) | 57 | 0.0171 | −32.7 (−35.9 to −29.5) | 100% |
| Taiwan, held-out country | Q4 (0.78–0.80) | 57 | 0.0182 | −31.6 (−34.2 to −29.0) | 100% |
| Taiwan, held-out country | Q5 (0.80–0.88) | 57 | 0.0473 | −42.3 (−45.8 to −38.8) | 100% |

Note: Similarity as in Table S39. The excess gain is absolute. Districts harmed is the share of districts with a negative excess gain. For comparison, the quintile means of similarity are 0.95 to 0.99 in Brazil's and 0.93 to 0.98 in Colombia's held-out-states splits. <!-- src: S7b_embedding_distance_bins.csv cos_max_mean BR_S2, CO_S2 --> Exploratory, unadjusted.

With Taiwan held out, the harm did not shrink with similarity (−31.6 to −42.3 × 10⁻⁴ per quintile), and all 285 districts were harmed. With Peru held out there was a gradient, from −30.4 × 10⁻⁴ in the least similar quintile to +64.7 × 10⁻⁴ in the most similar (ρ = +0.47). <!-- src: S7b_embedding_distance_bins.csv TW_S5, PE_S5 G_excess, G_excess_share_units_neg; S7_embedding_distance.csv PE_S5 spearman_rho -->

## F. Forecasts without case history

**Table S41. Forecast error without case history, Brazil, new years.**

<!-- src: T6c_nohist_ladder.csv, cell BR_S1_nohist, per label and horizon: wis_log, cov_80, cov_80_nonzero; history-arm comparison from T2_ladder.csv BR_S1 `WIS pooled h{1,4}` -->
| Model | Horizon 1 | Horizon 4 | Horizons 1 and 4 | 80% coverage, all rows / cases > 0 (pooled) |
|---|---|---|---|---|
| N3: season, climate, remote sensing and population | 0.3520 | 0.3533 | 0.3526 | 0.85 / 0.43 |
| N3 + C1: static history (mean log(1 + cases), 2014 to 2017) | 0.3473 | 0.3483 | 0.3478 | 0.84 / 0.43 |
| N4: N3 + AlphaEarth | 0.3437 | 0.3437 | 0.3437 | 0.83 / 0.41 |
| N3 + C2: coordinates (C\*) | 0.3404 | 0.3419 | 0.3411 | 0.84 / 0.43 |
| N4 + C2 | 0.3423 | 0.3429 | 0.3426 | 0.84 / 0.42 |
| With case history, L3 / L4 (same rows) | 0.1419 / 0.1418 | 0.1959 / 0.1952 | 0.1681 / 0.1677 | 0.90 / 0.67 (L4) |
| N4 + C1 | pending <!-- PENDING: BR S1 no-history N4 + C1 --> |  |  |  |

Note: Mean WIS over rows (lower is better). Seed 0. All 21 case-derived inputs are removed. C1 (static history) is a separate step, not a candidate for C\*. The row with case history gives L3 and L4 on the same rows for comparison (three seeds; coverage of L4).

**Table S42. Embedding, identity and excess gains without case history, Brazil, new years.**

<!-- src: T6b_nohist_estimands.csv, cell BR_S1_nohist, per horizon (1, 4, pooled) and estimand: pct_of_ref, lo95_pct, hi95_pct, p, mde_pct, wis_ref -->
| Horizon | Reference WIS (N3) | Embedding gain, % (95% CI); p | Identity gain (C2), % (95% CI); p | Excess gain, % (95% CI); p | Minimum detectable excess gain, % |
|---|---|---|---|---|---|
| Horizon 1 | 0.3520 | +2.35 (−0.83 to 5.53); 0.14 | +3.28 (1.60 to 4.96); <0.001 | −0.53 (−1.99 to 0.94); 0.46 | 2.07 |
| Horizon 4 | 0.3533 | +2.72 (−0.92 to 6.37); 0.13 | +3.22 (1.61 to 4.84); <0.001 | −0.29 (−2.13 to 1.55); 0.74 | 2.59 |
| Horizons 1 and 4 | 0.3520 | +2.54 (−0.82 to 5.89); 0.13 | +3.30 (1.68 to 4.93); <0.001 | −0.43 (−2.06 to 1.19); 0.58 | 2.29 |
| Brazil, held-out states, without case history | pending <!-- PENDING: BR S2 no-history --> |  |  |  |  |

Note: N3 is L3 and N4 is L4 without the 21 case-derived inputs. The selected control is coordinates (C2). Gains are percentages of the WIS of N3. The minimum detectable effect is at 80% power. Seed 0. The identity share is not estimable, because the embedding gain's CI includes zero.

## G. Supplementary figures

**Figure S1. Model ladder in the new-years split, by country.** <!-- figure file: docs/results/figures/FS1_ladder_S1.png --> Mean WIS on log(1 + cases) over rows (lower is better) for L1, L2, L3, L4, L3 + C1 and L4 + C1, at horizons 1 to 4 (thin lines) and pooled over horizons 1 and 4 (black squares). C\* is historical risk (C1) in every country. The seasonal naive baseline L0 is off scale; its pooled value is printed above each panel. The Taiwan panel excludes 2021, and its L2 point was tuned separately and is not comparable with the other Taiwan models. <!-- src: T2_ladder.csv; S1_baselines.csv -->

**Figure S2. Excess gain by test year.** <!-- figure file: docs/results/figures/F4_per_year_gains.png --> Excess gain as a percentage of that year's reference WIS, horizons 1 and 4 pooled, with 95% CIs (unadjusted), for every cell, coloured by split. The shaded band is ±1%. Each country panel has its own scale. Taiwan's percentages in 2020 to 2022 and 2024 are large because the reference WIS is close to zero in those years (2021 had no local cases); absolute values are in Table S30. <!-- src: S8_per_year.csv -->

**Figure S3. Similarity to the training districts and excess gain in the held-out-country split.** <!-- figure file: docs/results/figures/F3_s5_embedding_distance.png --> One panel per held-out country. The horizontal axis is a district's maximum cosine similarity between its renormalised AlphaEarth vector (year y − 1) and those of the training districts. The vertical axis is the district's excess gain as a percentage of the cell's reference WIS (negative means that the embeddings hurt). Grey points are districts (those outside the 1st to 99th percentile are not shown); blue points are quintile means with 95% CIs. Exploratory. <!-- src: S7b_embedding_distance_bins.csv G_excess_pct_cell -->
