<!-- Writer C. Draft v1, 2026-11-18. Supplementary results: tables S2-1 to S2-19 and captions for every main and supplementary figure. Numbers are generated from docs/results/tables/*.csv (results kit v3, 2026-11-18 11:53) and docs/results/review/*; each table carries its source in an HTML comment. Rounding: percentages to 2 decimals, p to 2 significant digits with a floor of <0.001, WIS to 4 decimals. Cell names: country and split (S1 new years; S2 held-out states; S3 held-out buffered blocks; S4 held-out random districts; S5 held-out country). We call all second-level units districts (municipalities in Brazil and Colombia, provinces in Peru, townships in Taiwan). -->

# Supplement S2: Supplementary results

WIS(L3) and the gains in Table 2 and in the tables built from the same estimator (Table S2-3, S2-5, S2-6) are means over target weeks of within-week means, so each week has equal weight. Tables S2-1, S2-2 and S2-19 report means over rows, so their WIS values differ slightly (Brazil S1 L3: 0.1675 as a week mean, 0.1681 as a row mean). <!-- src: T1_primary_family.csv BR_S1 WIS_L3 0.16753; T2_ladder.csv BR_S1 L3 0.1681 --> Cells are named by country and split: S1 new years, S2 held-out states, S3 held-out buffered blocks, S4 held-out random districts, S5 held-out country.

## S2-A. Baselines, ladder and control selection

**Table S2-1. Baseline comparison in the temporal split (S1).** Each entry gives mean WIS over scored rows, relative WIS against the seasonal naive baseline L0 in parentheses, then 80% interval coverage over all rows / over rows with at least one case. Horizons 1 and 4 pooled; origin-year rows; v2 exclusions; every model is scored on the same rows (bottom row). L0 forecasts the same week of the previous year. NB GLM is a negative binomial GLM on the L1 inputs. TimesFM 2.5 zero-shot was run for Brazil only. C\* is C1 in all four countries; Brazil averages three seeds for L3, L4, L3+C\* and L4+C\*. Taiwan rows exclude 2021 because the baseline runs have no 2021 forecasts. The Taiwan L2 row was tuned separately (per-level) and is not comparable with the other Taiwan rows; a shared-parameter Taiwan L2 was not available. The step from L0 to L1 changes both inputs and method. These are means over rows, so they differ slightly from the week-weighted WIS in Table 2.

<!-- src: S1_baselines.csv, rows with pooled_over = 1,4; columns wis_log, rel_wis_vs_L0, cov_80, cov_80_nonzero; n_rows per country -->
| Model | Brazil S1 | Colombia S1 | Peru S1 | Taiwan S1 (without 2021) |
|---|---|---|---|---|
| L0 (seasonal naive) | 0.4695 (1.00); 0.77 / 0.40 | 0.3272 (1.00); 0.81 / 0.53 | 0.6596 (1.00); 0.73 / 0.47 | 0.0922 (1.00); 0.94 / 0.00 |
| NB GLM (L1) | 0.2185 (0.47); 0.94 / 0.77 | 0.1426 (0.44); 0.96 / 0.81 | 0.3232 (0.49); 0.93 / 0.84 | 0.0594 (0.64); 0.98 / 0.42 |
| TimesFM 2.5 zero-shot | 0.1928 (0.41); 0.82 / 0.60 | not run | not run | not run |
| LightGBM L1 | 0.1700 (0.36); 0.91 / 0.68 | 0.1226 (0.37); 0.93 / 0.72 | 0.2442 (0.37); 0.84 / 0.70 | 0.0394 (0.43); 0.98 / 0.24 |
| LightGBM L2 | 0.1690 (0.36); 0.90 / 0.68 | 0.1224 (0.37); 0.93 / 0.72 | 0.2431 (0.37); 0.83 / 0.68 | per-level run only (row below) |
| LightGBM L3 | 0.1681 (0.36); 0.90 / 0.67 | 0.1220 (0.37); 0.93 / 0.72 | 0.2438 (0.37); 0.83 / 0.68 | 0.0398 (0.43); 0.98 / 0.25 |
| LightGBM L4 | 0.1677 (0.36); 0.90 / 0.67 | 0.1225 (0.37); 0.93 / 0.71 | 0.2462 (0.37); 0.83 / 0.68 | 0.0402 (0.44); 0.98 / 0.24 |
| LightGBM L3+C\* | 0.1680 (0.36); 0.90 / 0.66 | 0.1221 (0.37); 0.93 / 0.71 | 0.2445 (0.37); 0.83 / 0.67 | 0.0400 (0.43); 0.98 / 0.24 |
| LightGBM L4+C\* | 0.1676 (0.36); 0.90 / 0.66 | 0.1226 (0.37); 0.93 / 0.71 | 0.2462 (0.37); 0.83 / 0.67 | 0.0402 (0.44); 0.98 / 0.24 |
| LightGBM L2 (per-level tuned) | – | – | – | 0.0477 (0.52); 0.97 / 0.03 |
| Rows scored | 2,703,183 | 319,930 | 45,754 | 113,430 |


**Table S2-2. Feature ladder per primary cell.** Mean WIS on log(1 + cases) over rows (lower is better), horizons 1 and 4 pooled, origin-year rows common to every rung, v2 exclusions. L0–L2 were run in S1 only. The last two columns give the 80% interval coverage of L4+C\* over all rows / rows with cases, and the number of rows. Brazil S1 averages three seeds. The Taiwan S1 ladder excludes 2021 (its L0–L2 runs have no 2021 forecasts; Table 2 includes 2021) and its L2 rung is per-level tuned. Sensitivity rows: Brazil S1 with per-level tuning (L3 and L4 at 31 leaves, the original protocol, with pre-fix control selection) and Taiwan S1 with Brazil's hyperparameters and C\* (without 2021). Brazil S4 (held-out random districts): [[PENDING: BR S4]].

<!-- src: T2_ladder.csv, column `WIS pooled h{1,4}` per cell and label; cov_80 and cov_80_nonzero of L4+C*; n_rows -->
| Cell | C\* | L0 | L1 | L2 | L3 | L4 | L3+C\* | L4+C\* | L4+C\* 80% coverage, all / cases > 0 | Rows |
|---|---|---|---|---|---|---|---|---|---|---|
| Brazil S1 (new years) | C1 | 0.4695 | 0.1700 | 0.1690 | 0.1681 | 0.1677 | 0.1680 | 0.1676 | 0.90 / 0.66 | 2,703,183 |
| Brazil S2 (held-out states) | C1 | – | – | – | 0.1689 | 0.1690 | 0.1690 | 0.1690 | 0.90 / 0.66 | 2,703,183 |
| Brazil S3 (held-out buffered blocks) | C1 | – | – | – | 0.1706 | 0.1709 | 0.1707 | 0.1710 | 0.90 / 0.66 | 2,703,183 |
| Brazil S5 (held-out country) | C3 | – | – | – | 0.1914 | 0.1921 | 0.1912 | 0.1924 | 0.88 / 0.64 | 2,703,183 |
| Colombia S1 (new years) | C1 | 0.3272 | 0.1226 | 0.1224 | 0.1220 | 0.1225 | 0.1221 | 0.1226 | 0.93 / 0.71 | 319,930 |
| Colombia S2 (held-out states) | C1 | – | – | – | 0.1224 | 0.1232 | 0.1225 | 0.1231 | 0.92 / 0.70 | 319,930 |
| Colombia S3 (held-out buffered blocks) | C1 | – | – | – | 0.1244 | 0.1255 | 0.1246 | 0.1254 | 0.92 / 0.70 | 319,930 |
| Colombia S4 (held-out random districts) | C1 | – | – | – | 0.1222 | 0.1229 | 0.1224 | 0.1229 | 0.92 / 0.71 | 319,930 |
| Colombia S5 (held-out country) | C2 | – | – | – | 0.1238 | 0.1239 | 0.1249 | 0.1246 | 0.94 / 0.75 | 319,930 |
| Peru S1 (new years) | C1 | 0.6596 | 0.2442 | 0.2431 | 0.2438 | 0.2462 | 0.2445 | 0.2462 | 0.83 / 0.67 | 45,754 |
| Peru S5 (held-out country) | C3 | – | – | – | 0.2383 | 0.2367 | 0.2394 | 0.2371 | 0.84 / 0.67 | 45,754 |
| Taiwan S1 (new years) (ladder without 2021) | C1 | 0.0922 | 0.0394 | 0.0477 (per-level tuned) | 0.0398 | 0.0402 | 0.0400 | 0.0402 | 0.98 / 0.24 | 113,430 |
| Taiwan S5 (held-out country) | C3 | – | – | – | 0.0205 | 0.0250 | 0.0212 | 0.0248 | 0.99 / 0.61 | 141,645 |
| Brazil S1, per-level tuning (sensitivity) | C1 | 0.4695 | 0.1700 | 0.1690 | 0.1714 | 0.1710 | 0.1714 | 0.1710 | 0.90 / 0.68 | 2,703,183 |
| Taiwan S1, Brazil parameters (sensitivity) | C1 | – | – | – | 0.0398 | 0.0402 | 0.0401 | 0.0403 | 0.98 / 0.24 | 113,430 |


**Table S2-3. Excess gain by horizon (Part A) and the remaining columns of the primary family (Part B).** WIS is the weighted interval score on log(1 + cases), computed from the median and the 0.1–0.9 deciles. Rows are district × target week × horizon, origin-year rows only (forecast origin in the target's epidemiological year), after the v2 exclusions (districts without geometry, incomplete weeks, and Espírito Santo test-year weeks in Brazil). Taiwan includes test year 2021 unless stated. Gains are percentages of WIS(L3) on the same rows; positive values mean the added input improves the forecast. 95% confidence intervals (CIs) and p values come from the Diebold–Mariano (DM) test with the equal-weighted cosine (EWC) long-run variance and the Harvey–Leybourne–Newbold (HLN) correction, applied to the weekly mean loss difference; p values are unadjusted unless marked Holm. Horizons 1 and 4 are shown separately. S1 cells also show the secondary pooling over horizons 1–4, which is not in the Holm family and uses only test years scored at all four horizons; for Taiwan S1 it therefore excludes 2021, whose runs cover horizons 1 and 4 only. Brazil S4 (held-out random districts): [[PENDING: BR S4]].

*Part A.*

<!-- src: T3_estimands.csv rows test_year = pooled, estimand = G_excess, horizon 1 / 4 (pct_of_ref, lo95_pct, hi95_pct, p); S1 secondary pooling from T1_primary_family.csv sec_pct, sec_lo95_pct, sec_hi95_pct, sec_DM_p, sec_years -->
| Cell | h = 1: % [95% CI], p | h = 4: % [95% CI], p | S1 only, pooled h1–4 (secondary): % [95% CI], p; years |
|---|---|---|---|
| Brazil S1 (new years) | +0.11 [−0.14, +0.36], 0.36 | +0.32 [−0.48, +1.13], 0.40 | +0.25 [−0.33, +0.82], 0.38; 2020–24 |
| Brazil S2 (held-out states) | −0.01 [−0.19, +0.18], 0.95 | −0.00 [−0.47, +0.47], 0.99 | – |
| Brazil S3 (held-out buffered blocks) | −0.13 [−0.24, −0.02], 0.022 | −0.18 [−0.43, +0.07], 0.14 | – |
| Brazil S5 (held-out country) | −0.42 [−0.63, −0.20], <0.001 | −0.75 [−1.10, −0.41], <0.001 | – |
| Colombia S1 (new years) | −0.29 [−0.42, −0.15], <0.001 | −0.50 [−0.78, −0.21], 0.0026 | −0.39 [−0.61, −0.17], 0.0023; 2020–22 |
| Colombia S2 (held-out states) | −0.41 [−0.56, −0.26], <0.001 | −0.54 [−0.87, −0.22], 0.0037 | – |
| Colombia S3 (held-out buffered blocks) | −0.66 [−0.90, −0.41], <0.001 | −0.66 [−1.24, −0.09], 0.028 | – |
| Colombia S4 (held-out random districts) | −0.30 [−0.49, −0.12], 0.0039 | −0.57 [−0.91, −0.23], 0.0034 | – |
| Colombia S5 (held-out country) | −0.07 [−0.29, +0.15], 0.49 | +0.51 [−0.13, +1.15], 0.11 | – |
| Peru S1 (new years) | −0.10 [−0.47, +0.27], 0.58 | −1.15 [−2.17, −0.13], 0.030 | −0.63 [−1.35, +0.08], 0.077; 2020–23 |
| Peru S5 (held-out country) | +0.38 [−0.07, +0.83], 0.089 | +1.36 [−0.19, +2.91], 0.080 | – |
| Taiwan S1 (new years) | +0.07 [−0.97, +1.12], 0.89 | −1.18 [−2.31, −0.05], 0.042 | −0.38 [−0.92, +0.15], 0.14; 2020–24 (no 2021) |
| Taiwan S5 (held-out country) | −14.83 [−22.46, −7.21], <0.001 | −18.87 [−30.84, −6.90], 0.0043 | – |

*Part B. Embedding and identity gains and further columns of the primary family (moved from Table 2 of the main text).* Horizons 1 and 4 pooled, as in Table 2; same rows, tests and C\* as Table 2. DM p is the unadjusted p of the excess gain. The Holm-adjusted TOST p tests equivalence within ±1% of WIS(L3), Holm over the 13 available cells (final m = 14). Brazil S1 averages three seeds; all other cells use one.

<!-- src: T1_primary_family.csv, one row per cell: test_years; n_rows; n_seeds; WIS_L4C; G_emb_pct, G_emb_lo95_pct, G_emb_hi95_pct; G_id_pct, G_id_lo95_pct, G_id_hi95_pct; DM_p; TOST_p_Holm. Values moved unchanged from draft v1 Table 2, which the number verifier checked cell by cell against T1. -->
| Cell | Test years; rows; seeds | WIS(L4+C\*) | Embedding gain, % [95% CI] | Identity gain, % [95% CI] | DM p (excess gain) | Holm-adjusted TOST p (±1%) |
|---|---|---|---|---|---|---|
| Brazil S1 (new years) | 2020–24; 2,703,183; 3 | 0.1671 | +0.26 [−0.31, +0.82] | +0.03 [−0.11, +0.18] | 0.39 | 0.031 |
| Brazil S2 (held-out states) | 2020–24; 2,703,183; 1 | 0.1684 | −0.02 [−0.34, +0.30] | −0.05 [−0.13, +0.02] | 1.0 | <0.001 |
| Brazil S3 (held-out buffered blocks) | 2020–24; 2,703,183; 1 | 0.1704 | −0.13 [−0.35, +0.09] | −0.03 [−0.14, +0.08] | 0.090 | <0.001 |
| Brazil S4 (held-out random districts) | [[PENDING: BR S4]] | | | | | |
| Brazil S5 (held-out country) | 2020–24; 2,703,183; 1 | 0.1917 | −0.34 [−1.24, +0.56] | +0.10 [−0.75, +0.96] | <0.001 | 0.010 |
| Colombia S1 (new years) | 2020–22; 319,930; 1 | 0.1227 | −0.36 [−0.58, −0.13] | −0.07 [−0.34, +0.20] | 0.0011 | <0.001 |
| Colombia S2 (held-out states) | 2020–22; 319,930; 1 | 0.1233 | −0.59 [−0.80, −0.37] | −0.08 [−0.13, −0.04] | <0.001 | 0.0011 |
| Colombia S3 (held-out buffered blocks) | 2020–22; 319,930; 1 | 0.1255 | −0.83 [−1.14, −0.52] | −0.13 [−0.22, −0.05] | 0.0033 | 0.18 |
| Colombia S4 (held-out random districts) | 2020–22; 319,930; 1 | 0.1231 | −0.52 [−0.75, −0.28] | −0.13 [−0.18, −0.08] | 0.0028 | 0.0018 |
| Colombia S5 (held-out country) | 2020–22; 319,930; 1 | 0.1247 | −0.04 [−0.37, +0.28] | −0.81 [−1.16, −0.46] | 0.27 | 0.0059 |
| Peru S1 (new years) | 2020–23; 45,754; 1 | 0.2441 | −0.94 [−1.70, −0.18] | −0.26 [−1.05, +0.53] | 0.056 | 0.57 |
| Peru S5 (held-out country) | 2020–23; 45,754; 1 | 0.2350 | +0.68 [−0.59, +1.96] | −0.44 [−0.80, −0.07] | 0.079 | 0.94 |
| Taiwan S1 (new years) | 2020–24; 141,645; 1 | 0.0315 | −1.06 [−1.96, −0.16] | −0.63 [−1.68, +0.43] | 0.049 | 0.35 |
| Taiwan S5 (held-out country) | 2020–24; 141,645; 1 | 0.0243 | −21.60 [−31.82, −11.39] | −3.36 [−6.52, −0.20] | 0.0017 | 1.0 |


**Table S2-4. Selection of the location control C\* at the 2019 origin.** Mean WIS on log(1 + cases) at the 2019 validation origin (models trained on 2018 targets and scored on 2019 targets; horizons 1 and 4) for the reference model (L3, or N3 in the no-history arm) and for the reference plus each candidate control. Bold marks the selected C\*. C3, C4 and C4s are means over 3 seeds; the others use one seed. Selection rule v2 (deviation D19): exclude degenerate candidates, form a tie set within two seed standard errors of the best score, then take the first by priority C1 > C3 > C2 > C4s > C4 > C5 (no-history arm: C3 > C2 > C6 > C4s > C4). C1 is not defined across countries (S5); C4s is not a candidate in Peru and Taiwan, where its range equals that of C4; C5 is not a candidate in the no-history arm, where C1 forms its own rung; C6 is used only in the no-history S1 cell. A dash means not a candidate. A control scored below L3 only in Brazil S1, Colombia S5 and Taiwan S1; in Taiwan S1 the lower-scoring C3 was not selected because of the priority rule. The Brazil S2 no-history selection is shown although its test-year runs are still pending. Brazil S4 (held-out random districts): [[PENDING: BR S4]].

<!-- src: T4_cstar_selection.csv, column wis_log_2019 per cell and candidate (3-seed mean for C3, C4, C4s), `selected`, C_star -->
| Cell | Reference (L3 or N3) | +C1 | +C2 | +C3 | +C4 | +C4s | +C5 | +C6 | Selected C\* |
|---|---|---|---|---|---|---|---|---|---|
| Brazil S1 (new years) | 0.17525 | **0.17446** | 0.17715 | 0.17681 | 0.17782 | 0.17840 | 0.17732 | – | C1 |
| Brazil S2 (held-out states) | 0.17542 | **0.17597** | 0.17733 | 0.17757 | 0.17773 | 0.17900 | 0.17766 | – | C1 |
| Brazil S3 (held-out buffered blocks) | 0.17715 | **0.17749** | 0.17989 | 0.17916 | 0.18093 | 0.18162 | 0.18033 | – | C1 |
| Brazil S5 (held-out country) | 0.19102 | – | 0.19168 | **0.19182** | 0.19235 | 0.19247 | 0.19252 | – | C3 |
| Colombia S1 (new years) | 0.17019 | **0.17046** | 0.17045 | 0.17042 | 0.17096 | 0.17088 | 0.17093 | – | C1 |
| Colombia S2 (held-out states) | 0.17169 | **0.17176** | 0.17211 | 0.17219 | 0.17288 | 0.17279 | 0.17249 | – | C1 |
| Colombia S3 (held-out buffered blocks) | 0.17311 | **0.17315** | 0.17387 | 0.17381 | 0.17490 | 0.17453 | 0.17455 | – | C1 |
| Colombia S4 (held-out random districts) | 0.17158 | **0.17167** | 0.17201 | 0.17225 | 0.17269 | 0.17269 | 0.17279 | – | C1 |
| Colombia S5 (held-out country) | 0.18208 | – | **0.17809** | 0.18352 | 0.18349 | 0.18367 | 0.18290 | – | C2 |
| Peru S1 (new years) | 0.16194 | **0.16258** | 0.16431 | 0.16537 | 0.16684 | 0.16664 | 0.16372 | – | C1 |
| Peru S5 (held-out country) | 0.13892 | – | 0.14227 | **0.13997** | 0.14111 | – | 0.14149 | – | C3 |
| Taiwan S1 (new years) | 0.0041143 | **0.0041315** | 0.0043898 | 0.0040175 | 0.0043931 | – | 0.0044552 | – | C1 |
| Taiwan S5 (held-out country) | 0.0065580 | – | 0.0091207 | **0.0078422** | 0.0078206 | – | 0.011081 | – | C3 |
| Brazil S1, no history | 0.35428 | – | **0.34633** | 0.35963 | 0.34895 | 0.35076 | – | 0.34722 | C2 |
| Brazil S2, no history | 0.36193 | – | **0.35921** | 0.36860 | 0.35977 | 0.36747 | – | – | C2 |


## S2-B. Robustness of the primary family

**Table S2-5. Robustness of the excess gain to inference, scale, rows and exclusions.** WIS is the weighted interval score on log(1 + cases), computed from the median and the 0.1–0.9 deciles. Rows are district × target week × horizon, origin-year rows only (forecast origin in the target's epidemiological year), after the v2 exclusions (districts without geometry, incomplete weeks, and Espírito Santo test-year weeks in Brazil). Taiwan includes test year 2021 unless stated. Primary: DM test with EWC and HLN; Holm p over the 13 available cells, final m = 14 [[PENDING: final Holm m=14]]. EWC B = 4: the same test with 4 cosine terms (more robust to slow drift across seasons). IAAFT-calibrated p: the observed statistic compared with 2,000 iterative amplitude-adjusted Fourier transform (IAAFT) surrogates of the cell's own weekly loss-difference series. Delta-method CI: the 95% CI of the percentage when WIS(L3) is treated as estimated. Case scale (secondary): excess gain on WIS of raw case counts, as a percentage of case-scale WIS(L3). All rows: without the origin-year filter. Exclusions v1: Brazil scored without the Espírito Santo exclusion. In Brazil S1 (three seeds) the seed standard deviation of the excess gain is 0.00002 against a standard error of 0.00044. <!-- src: T1_primary_family.csv BR_S1 seed_sd, se --> Brazil S4 (held-out random districts): [[PENDING: BR S4]].

<!-- src: T1_primary_family.csv per cell: pct_of_WIS_ref, lo95_pct, hi95_pct, DM_p, Holm_p_available; B4_lo95_pct, B4_hi95_pct, B4_p, B4_Holm_p; p_iaaft, p_iaaft_Holm; delta_lo95_pct, delta_hi95_pct; case_pct, case_p; all rows = unfiltered_pct, unfiltered_p; v1 exclusions = exclv1_pct, exclv1_p for Brazil -->
| Cell | Primary: % [95% CI]; p (Holm) | EWC B = 4: 95% CI; p (Holm) | IAAFT-calibrated p (Holm) | Delta-method 95% CI | Case scale: %; p | All rows: %; p | Exclusions v1 (Brazil): %; p |
|---|---|---|---|---|---|---|---|
| Brazil S1 | +0.23 [−0.33, +0.79]; 0.39 (0.80) | [−0.53, +1.00]; 0.45 (1.0) | 0.51 (1.0) | [−0.28, +0.75] | −0.03; 0.92 | +0.26; 0.39 | +0.23; 0.40 |
| Brazil S2 | −0.00 [−0.34, +0.34]; 1.0 (1.0) | [−0.57, +0.56]; 1.0 (1.0) | 1.0 (1.0) | [−0.34, +0.34] | −0.73; 0.025 | +0.03; 0.89 | −0.01; 0.94 |
| Brazil S3 | −0.16 [−0.34, +0.03]; 0.090 (0.39) | [−0.49, +0.18]; 0.26 (1.0) | 0.21 (0.86) | [−0.36, +0.05] | −1.30; 0.065 | −0.10; 0.40 | −0.19; 0.045 |
| Brazil S5 | −0.60 [−0.84, −0.36]; <0.001 (<0.001) | [−0.84, −0.37]; 0.0021 (0.027) | <0.001 (0.0065) | [−0.94, −0.26] | −0.86; 0.20 | −0.62; <0.001 | −0.61; <0.001 |
| Colombia S1 | −0.39 [−0.58, −0.19]; 0.0011 (0.012) | [−0.60, −0.17]; 0.0072 (0.079) | <0.001 (0.010) | [−0.59, −0.19] | −0.81; 0.038 | −0.39; <0.001 | – |
| Colombia S2 | −0.47 [−0.69, −0.25]; <0.001 (0.0068) | [−0.66, −0.28]; 0.0023 (0.028) | <0.001 (0.0065) | [−0.71, −0.24] | −0.64; 0.18 | −0.48; <0.001 | – |
| Colombia S3 | −0.65 [−1.04, −0.27]; 0.0033 (0.026) | [−1.03, −0.28]; 0.0084 (0.084) | <0.001 (0.0065) | [−1.08, −0.23] | −0.70; 0.23 | −0.68; 0.0027 | – |
| Colombia S4 | −0.43 [−0.68, −0.18]; 0.0028 (0.025) | [−0.73, −0.13]; 0.016 (0.14) | 0.0065 (0.054) | [−0.69, −0.18] | −0.88; 0.10 | −0.44; 0.0018 | – |
| Colombia S5 | +0.22 [−0.19, +0.63]; 0.27 (0.80) | [−0.58, +1.01]; 0.49 (1.0) | 0.46 (1.0) | [−0.17, +0.60] | +0.51; 0.068 | +0.18; 0.33 | – |
| Peru S1 | −0.70 [−1.41, +0.02]; 0.056 (0.34) | [−1.82, +0.42]; 0.16 (0.80) | 0.083 (0.47) | [−1.47, +0.08] | −1.14; 0.095 | −0.62; 0.094 | – |
| Peru S5 | +0.96 [−0.13, +2.05]; 0.079 (0.39) | [+0.22, +1.70]; 0.023 (0.16) | 0.0060 (0.054) | [−0.17, +2.09] | −0.59; 0.56 | +1.01; 0.046 | – |
| Taiwan S1 | −0.60 [−1.20, −0.00]; 0.049 (0.34) | [−1.40, +0.20]; 0.10 (0.63) | 0.078 (0.47) | [−1.72, +0.52] | −0.00; 0.95 | −0.55; 0.076 | – |
| Taiwan S5 | −17.30 [−27.03, −7.57]; 0.0017 (0.017) | [−29.31, −5.28]; 0.016 (0.14) | 0.020 (0.14) | [−40.57, +5.97] | −4.02; 0.0086 | −17.62; 0.0011 | – |


Peru S5 was nominally positive under both more cautious checks (B = 4 p = 0.023; IAAFT-calibrated p = 0.0060) but not after Holm correction (0.16 and 0.054). <!-- src: T1_primary_family.csv PE_S5 B4_p, p_iaaft, B4_Holm_p, p_iaaft_Holm -->

**Table S2-6. Equivalence at margins of ±0.5%, ±1% and ±2% of WIS(L3).** WIS is the weighted interval score on log(1 + cases), computed from the median and the 0.1–0.9 deciles. Rows are district × target week × horizon, origin-year rows only (forecast origin in the target's epidemiological year), after the v2 exclusions (districts without geometry, incomplete weeks, and Espírito Santo test-year weeks in Brazil). Taiwan includes test year 2021 unless stated. The excess gain is shown with its 90% CI (DM test with EWC and HLN). A cell is within the margin when the two one-sided tests (TOST) reject at 5%, unadjusted or with TOST p values Holm-adjusted over the 13 available cells (final m = 14). "Near margin" marks a CI bound within 0.05 percentage points of the margin. The ±1% margin was chosen after the Brazil and Peru S1 results had been seen. Equivalence for Brazil S1, Brazil S2 and Colombia S5 assumes no multi-season drift in the weekly loss difference. Brazil S4 (held-out random districts): [[PENDING: BR S4]].

<!-- src: T1b_margin_sensitivity.csv per cell and margin_pct: G_excess_pct, lo90_pct, hi90_pct, within_unadjusted, within_Holm, near_margin -->
| Cell | Excess gain, % [90% CI] | ±0.5%: unadjusted / Holm | ±1%: unadjusted / Holm | ±2%: unadjusted / Holm |
|---|---|---|---|---|
| Brazil S1 | +0.23 [−0.23, +0.69] | no / no | yes / yes | yes / yes |
| Brazil S2 | −0.00 [−0.28, +0.28] | yes / yes | yes / yes | yes / yes |
| Brazil S3 | −0.16 [−0.31, −0.01] | yes / yes | yes / yes | yes / yes |
| Brazil S5 | −0.60 [−0.80, −0.40] | no / no | yes / yes | yes / yes |
| Colombia S1 | −0.39 [−0.55, −0.23] | no / no (near margin) | yes / yes | yes / yes |
| Colombia S2 | −0.47 [−0.65, −0.29] | no / no | yes / yes | yes / yes |
| Colombia S3 | −0.65 [−0.97, −0.34] | no / no | yes / no (near margin) | yes / yes |
| Colombia S4 | −0.43 [−0.64, −0.23] | no / no | yes / yes | yes / yes |
| Colombia S5 | +0.22 [−0.12, +0.55] | no / no | yes / yes | yes / yes |
| Peru S1 | −0.70 [−1.29, −0.11] | no / no | no / no | yes / yes |
| Peru S5 | +0.96 [+0.07, +1.85] | no / no | no / no | yes / no |
| Taiwan S1 | −0.60 [−1.09, −0.11] | no / no | no / no | yes / yes |
| Taiwan S5 | −17.30 [−25.31, −9.28] | no / no | no / no | no / no |
| Cells within the margin (of 13) | | 2 / 2 | 9 / 8 | 12 / 11 |


## S2-C. Where the difference arises

**Table S2-7. Excess gain by type of target week.** WIS is the weighted interval score on log(1 + cases), computed from the median and the 0.1–0.9 deciles. Rows are district × target week × horizon, origin-year rows only (forecast origin in the target's epidemiological year), after the v2 exclusions (districts without geometry, incomplete weeks, and Espírito Santo test-year weeks in Brazil). Taiwan includes test year 2021 unless stated. Strata: weeks with at least one case; zero weeks listed by the source (Brazil 2020–2021 test years only); zero weeks filled by us. For each stratum: share of rows; the stratum estimate as a percentage of the stratum's own WIS(L3), with 95% CI; and the stratum's additive contribution to the cell total as a percentage of the cell's WIS(L3), with 95% CI. Contributions add up exactly to the total (residual 0). Stratum estimates weight weeks equally and are not shares of the total. DM test with EWC and HLN, unadjusted. Extra rows: Brazil S1 with per-level tuning (31 leaves); Taiwan without 2021; the Brazil S1 no-history arm (N4+C2 vs N3+C2, percentages of WIS(N3)). Brazil S4 (held-out random districts): [[PENDING: BR S4]].

<!-- src: T5_strata.csv, estimand = G_excess, per cell and stratum: row_share; pct_of_ref, lo95_pct, hi95_pct (stratum estimate, % of the stratum's own WIS(L3)); contrib_pct, contrib_lo95_pct, contrib_hi95_pct, contrib_p (additive contribution, % of the cell's WIS(L3)); total_pct -->
| Cell | Total, % | Cases > 0: share; own % [95% CI]; contribution % [95% CI] | Recorded zero (Brazil 2020–21): share; own % [95% CI]; contribution % [95% CI] | Zero-filled: share; own % [95% CI]; contribution % [95% CI] |
|---|---|---|---|---|
| Brazil S1 (new years) | +0.23 | 27%; +0.30 [−0.16, +0.76]; +0.46 [−0.16, +1.07] | 21%; −0.27 [−2.74, +2.20]; −0.02 [−0.16, +0.12] | 52%; −1.67 [−2.65, −0.69]; −0.20 [−0.33, −0.08] |
| Brazil S2 (held-out states) | −0.00 | 27%; −0.00 [−0.42, +0.42]; +0.14 [−0.27, +0.54] | 21%; +0.72 [−1.33, +2.78]; +0.05 [−0.07, +0.16] | 52%; −1.48 [−2.58, −0.38]; −0.18 [−0.30, −0.06] |
| Brazil S3 (held-out buffered blocks) | −0.16 | 27%; +0.28 [−0.01, +0.58]; +0.22 [−0.02, +0.47] | 21%; −0.34 [−2.71, +2.03]; −0.03 [−0.17, +0.11] | 52%; −2.75 [−4.39, −1.11]; −0.35 [−0.52, −0.18] |
| Brazil S5 (held-out country) | −0.60 | 27%; +0.55 [+0.15, +0.95]; +0.28 [+0.05, +0.50] | 21%; −2.69 [−5.35, −0.03]; −0.22 [−0.46, +0.02] | 52%; −5.22 [−6.17, −4.27]; −0.66 [−0.85, −0.47] |
| Colombia S1 (new years) | −0.39 | 21%; +0.28 [−0.30, +0.86]; +0.21 [−0.20, +0.61] | none | 79%; −2.11 [−3.52, −0.69]; −0.59 [−1.00, −0.19] |
| Colombia S2 (held-out states) | −0.47 | 21%; +0.26 [−0.32, +0.84]; +0.22 [−0.18, +0.61] | none | 79%; −2.46 [−3.78, −1.13]; −0.69 [−1.07, −0.31] |
| Colombia S3 (held-out buffered blocks) | −0.65 | 21%; +0.15 [−0.31, +0.60]; +0.10 [−0.19, +0.40] | none | 79%; −2.55 [−4.13, −0.98]; −0.76 [−1.23, −0.29] |
| Colombia S4 (held-out random districts) | −0.43 | 21%; +0.31 [−0.32, +0.94]; +0.26 [−0.16, +0.68] | none | 79%; −2.48 [−4.00, −0.97]; −0.69 [−1.13, −0.25] |
| Colombia S5 (held-out country) | +0.22 | 21%; +0.37 [+0.07, +0.66]; +0.27 [+0.06, +0.49] | none | 79%; −0.13 [−2.25, +1.98]; −0.05 [−0.51, +0.41] |
| Peru S1 (new years) | −0.70 | 44%; −0.08 [−0.94, +0.77]; +0.04 [−0.74, +0.83] | none | 56%; −6.14 [−8.64, −3.65]; −0.74 [−0.99, −0.49] |
| Peru S5 (held-out country) | +0.96 | 44%; +1.61 [+0.26, +2.95]; +1.28 [+0.22, +2.33] | none | 56%; −2.97 [−4.73, −1.22]; −0.32 [−0.51, −0.12] |
| Taiwan S1 (new years) | −0.60 | 2%; −0.15 [−1.21, +0.91]; −0.07 [−0.34, +0.20] | none | 98%; −9.46 [−22.14, +3.23]; −0.53 [−1.22, +0.17] |
| Taiwan S5 (held-out country) | −17.30 | 2%; +2.16 [+0.27, +4.04]; +1.28 [−1.06, +3.61] | none | 98%; −48.47 [−72.97, −23.97]; −18.57 [−28.18, −8.97] |
| Brazil S1, per-level tuning, 31 leaves (sensitivity) | +0.25 | 27%; +0.22 [−0.03, +0.46]; +0.27 [−0.04, +0.59] | 21%; +0.30 [−1.54, +2.14]; +0.01 [−0.08, +0.11] | 52%; −0.06 [−0.65, +0.54]; −0.03 [−0.09, +0.02] |
| Taiwan S1 (new years), without 2021 | −0.44 | 3%; −0.15 [−1.21, +0.91]; −0.07 [−0.35, +0.20] | none | 97%; −6.74 [−19.50, +6.02]; −0.36 [−1.04, +0.31] |
| Taiwan S5 (held-out country), without 2021 | −11.16 | 3%; +2.16 [+0.27, +4.04]; +1.33 [−1.12, +3.77] | none | 97%; −35.22 [−48.16, −22.27]; −12.48 [−16.99, −7.97] |
| Brazil S1, no-history arm (N3+C2 vs N4+C2) | −0.43 | 27%; +0.58 [−1.16, +2.31]; +0.77 [−1.27, +2.80] | 21%; −6.09 [−17.44, +5.25]; −0.29 [−0.78, +0.20] | 52%; −15.77 [−24.77, −6.76]; −0.91 [−1.46, −0.35] |


**Table S2-8. Upper quantiles on zero-case rows.** WIS is the weighted interval score on log(1 + cases), computed from the median and the 0.1–0.9 deciles. Rows are district × target week × horizon, origin-year rows only (forecast origin in the target's epidemiological year), after the v2 exclusions (districts without geometry, incomplete weeks, and Espírito Santo test-year weeks in Brazil). Taiwan includes test year 2021 unless stated. Δq0.9 is the mean 0.9 quantile of L4+C\* minus that of L3+C\* on rows with zero cases, on the log(1 + cases) and case scales, with a 95% CI from the weekly series (DM test with EWC). The zero-row contribution is the additive contribution of all zero-case rows (listed and filled) to the absolute excess gain, in units of 10⁻⁴ WIS. The last two columns give the share of that contribution coming from quantile levels above the median (0.6–0.9) and from the 0.9 quantile alone; values above 1 mean the lower quantiles offset part of the loss. Colombia S5 shares are unstable because its zero-row contribution is close to zero. Brazil S4 (held-out random districts): [[PENDING: BR S4]].

<!-- src: S6_q90_mechanism.csv per cell: zero_row_share; dq90_log, dq90_log_lo95, dq90_log_hi95, dq90_log_p; dq90_case, dq90_case_lo95, dq90_case_hi95; G_zero_contrib, G_zero_contrib_lo95, G_zero_contrib_hi95 (×10^4); upper_share_of_zero; q90_share_of_zero -->
| Cell | Zero-case row share | Δq0.9, log(1+cases) [95% CI]; p | Δq0.9, cases [95% CI] | Zero-row contribution to excess gain, WIS ×10⁻⁴ [95% CI] | Share of zero-row loss from quantiles above the median | Share from q0.9 alone |
|---|---|---|---|---|---|---|
| Brazil S1 | 73% | +0.006 [+0.001, +0.011]; 0.029 | +0.003 [−0.008, +0.014] | −3.8 [−7.3, −0.2] | 0.77 | 0.24 |
| Brazil S2 | 73% | +0.009 [+0.004, +0.015]; 0.0013 | +0.001 [−0.007, +0.009] | −2.3 [−5.5, +0.9] | 1.27 | 0.63 |
| Brazil S3 | 73% | +0.027 [+0.019, +0.035]; <0.001 | +0.031 [+0.020, +0.042] | −6.5 [−10.6, −2.3] | 1.19 | 0.65 |
| Brazil S5 | 73% | +0.043 [+0.028, +0.058]; <0.001 | +0.058 [+0.027, +0.088] | −16.8 [−21.9, −11.7] | 1.04 | 0.44 |
| Colombia S1 | 79% | +0.017 [+0.010, +0.025]; <0.001 | +0.020 [+0.004, +0.036] | −7.2 [−12.2, −2.3] | 1.00 | 0.42 |
| Colombia S2 | 79% | +0.019 [+0.012, +0.027]; <0.001 | +0.018 [+0.003, +0.032] | −8.4 [−13.1, −3.8] | 1.04 | 0.40 |
| Colombia S3 | 79% | +0.025 [+0.018, +0.033]; <0.001 | +0.018 [−0.001, +0.036] | −9.4 [−15.3, −3.6] | 1.12 | 0.47 |
| Colombia S4 | 79% | +0.017 [+0.010, +0.025]; <0.001 | +0.018 [+0.003, +0.033] | −8.5 [−13.8, −3.1] | 1.05 | 0.36 |
| Colombia S5 | 79% | +0.007 [+0.000, +0.014]; 0.041 | +0.007 [−0.009, +0.022] | −0.7 [−6.4, +5.0] | 2.94 | 1.98 |
| Peru S1 | 56% | +0.037 [+0.020, +0.053]; <0.001 | +0.057 [+0.031, +0.083] | −17.9 [−23.9, −11.9] | 0.74 | 0.23 |
| Peru S5 | 56% | +0.017 [+0.010, +0.025]; <0.001 | +0.040 [+0.022, +0.058] | −7.5 [−12.1, −2.9] | 0.66 | 0.30 |
| Taiwan S1 | 98% | +0.002 [−0.001, +0.006]; 0.15 | +0.003 [−0.002, +0.007] | −1.6 [−3.8, +0.5] | 1.12 | 0.33 |
| Taiwan S5 | 98% | +0.099 [+0.067, +0.130]; <0.001 | +0.137 [+0.089, +0.185] | −37.5 [−56.8, −18.1] | 0.96 | 0.57 |


## S2-D. Supporting analyses (exploratory, no multiplicity adjustment)

These analyses are exploratory and unadjusted for multiplicity (detail moved from the main Results). Outbreak weeks made up 0.7–22.9% of rows. On them, the excess gain had a CI above zero in Brazil S5 and Peru S5 (+3.66%) and below zero in Brazil S2, Brazil S3 and Colombia S3 (Table S2-9). <!-- src: S3_outbreak.csv outbreak row_share, pct_of_ref, lo95_pct, hi95_pct --> Under population or past-case weighting, only Colombia S5 had a CI above zero (+0.49% with case weights); Colombian losses grew under population weighting (to −1.38% in S3) and Peru S5 turned negative under both (Table S2-10). <!-- src: S4_weighted.csv pct_of_ref, lo95_pct, hi95_pct (PE_S5 −1.19 population, −0.73 case) --> Causal quantile recalibration changed the excess gain by 0.16 points or less, except in Peru S5 (to −0.05% with Mondrian shifts) and Taiwan S5 (to −15.01%); it raised coverage on weeks with cases mainly in Peru (Table S2-11). <!-- src: S5_recalibration.csv all_years raw vs global/mondrian pct_of_ref; cov80pos_L4+C* --> In strata computed before the origin-year filter and the Espírito Santo exclusion, no population, surveillance-history or urban-growth stratum gained significantly outside Peru S5, and where losses occurred they were largest in districts with no reported case in 2014–2017 (Table S2-17). <!-- src: docs/results/review/RB_summary.md section 1; RB_strata.csv -->

**Table S2-9. Excess gain on outbreak and non-outbreak weeks.** WIS is the weighted interval score on log(1 + cases), computed from the median and the 0.1–0.9 deciles. Rows are district × target week × horizon, origin-year rows only (forecast origin in the target's epidemiological year), after the v2 exclusions (districts without geometry, incomplete weeks, and Espírito Santo test-year weeks in Brazil). Taiwan includes test year 2021 unless stated. Gains are percentages of WIS(L3) on the same rows; positive values mean the added input improves the forecast. 95% confidence intervals (CIs) and p values come from the Diebold–Mariano (DM) test with the equal-weighted cosine (EWC) long-run variance and the Harvey–Leybourne–Newbold (HLN) correction, applied to the weekly mean loss difference; p values are unadjusted unless marked Holm. An outbreak week has cases at least max(the district's 90th percentile of weekly cases over 2013–2019, 5); the window includes the training years 2018–2019 but no test year. Each stratum estimate is a percentage of that stratum's own WIS(L3). The last column tests the outbreak minus non-outbreak weekly series. Brazil S4 (held-out random districts): [[PENDING: BR S4]].

<!-- src: S3_outbreak.csv per cell: stratum outbreak / non_outbreak (row_share, pct_of_ref, lo95_pct, hi95_pct, p, n_weeks) and outbreak_minus_non (p) -->
| Cell | Outbreak row share | Outbreak weeks: % [95% CI]; p | Non-outbreak weeks: % [95% CI]; p | Difference, p |
|---|---|---|---|---|
| Brazil S1 | 8.2% | +0.08 [−0.77, +0.92]; 0.85 | +0.01 [−0.19, +0.20]; 0.94 | 0.85 |
| Brazil S2 | 8.2% | −0.98 [−1.96, −0.01]; 0.048 | +0.15 [−0.06, +0.36]; 0.16 | 0.041 |
| Brazil S3 | 8.2% | −0.98 [−1.73, −0.23]; 0.013 | +0.13 [−0.19, +0.44]; 0.41 | 0.011 |
| Brazil S5 | 8.2% | +0.87 [+0.20, +1.54]; 0.014 | −0.86 [−1.14, −0.58]; <0.001 | 0.0047 |
| Colombia S1 | 2.3% | −0.62 [−2.21, +0.97]; 0.41 | −0.39 [−0.59, −0.18]; 0.0015 | 0.48 |
| Colombia S2 | 2.3% | −0.96 [−2.76, +0.84]; 0.26 | −0.43 [−0.65, −0.22]; 0.0010 | 0.31 |
| Colombia S3 | 2.3% | −1.72 [−3.29, −0.15]; 0.035 | −0.52 [−0.98, −0.05]; 0.033 | 0.047 |
| Colombia S4 | 2.3% | −0.92 [−2.80, +0.96]; 0.30 | −0.41 [−0.66, −0.17]; 0.0030 | 0.36 |
| Colombia S5 | 2.3% | −0.34 [−1.47, +0.79]; 0.52 | +0.30 [−0.17, +0.77]; 0.19 | 0.46 |
| Peru S1 | 22.9% | −1.26 [−2.90, +0.37]; 0.12 | −0.75 [−1.33, −0.18]; 0.014 | 0.20 |
| Peru S5 | 22.9% | +3.66 [+1.46, +5.86]; 0.0033 | −0.98 [−1.61, −0.36]; 0.0048 | 0.0012 |
| Taiwan S1 | 0.7% | −0.19 [−1.15, +0.77]; 0.61 | −1.33 [−2.58, −0.08]; 0.039 | 0.64 |
| Taiwan S5 | 0.7% | +1.31 [−0.07, +2.69]; 0.058 | −21.21 [−32.87, −9.54]; 0.0014 | 0.039 |


**Table S2-10. Population- and case-weighted excess gain.** WIS is the weighted interval score on log(1 + cases), computed from the median and the 0.1–0.9 deciles. Rows are district × target week × horizon, origin-year rows only (forecast origin in the target's epidemiological year), after the v2 exclusions (districts without geometry, incomplete weeks, and Espírito Santo test-year weeks in Brazil). Taiwan includes test year 2021 unless stated. Gains are percentages of WIS(L3) on the same rows; positive values mean the added input improves the forecast. 95% confidence intervals (CIs) and p values come from the Diebold–Mariano (DM) test with the equal-weighted cosine (EWC) long-run variance and the Harvey–Leybourne–Newbold (HLN) correction, applied to the weekly mean loss difference; p values are unadjusted unless marked Holm. Within each horizon and week, rows are weighted by the district's population in the target year, or by its mean weekly cases in 2013–2017 plus 1; weeks are then averaged as in the primary estimator. Brazil S4 (held-out random districts): [[PENDING: BR S4]].

<!-- src: S4_weighted.csv, estimand G_excess, per cell and weights (unweighted, population, pre_cases_plus1): pct_of_ref, lo95_pct, hi95_pct, p -->
| Cell | Unweighted: % [95% CI]; p | Population-weighted: % [95% CI]; p | Weighted by 2013–17 mean weekly cases + 1: % [95% CI]; p |
|---|---|---|---|
| Brazil S1 | +0.23 [−0.33, +0.79]; 0.39 | +0.03 [−0.40, +0.46]; 0.88 | −0.13 [−0.53, +0.27]; 0.51 |
| Brazil S2 | −0.00 [−0.34, +0.34]; 1.0 | −0.15 [−0.53, +0.22]; 0.40 | −0.21 [−0.64, +0.22]; 0.32 |
| Brazil S3 | −0.16 [−0.34, +0.03]; 0.090 | −0.42 [−0.90, +0.07]; 0.086 | −0.58 [−0.99, −0.16]; 0.010 |
| Brazil S5 | −0.60 [−0.84, −0.36]; <0.001 | −0.53 [−1.08, +0.01]; 0.054 | −0.44 [−1.00, +0.12]; 0.11 |
| Colombia S1 | −0.39 [−0.58, −0.19]; 0.0011 | −1.03 [−1.53, −0.52]; <0.001 | −0.72 [−1.19, −0.26]; 0.0053 |
| Colombia S2 | −0.47 [−0.69, −0.25]; <0.001 | −0.54 [−1.13, +0.06]; 0.072 | −0.40 [−0.88, +0.09]; 0.099 |
| Colombia S3 | −0.65 [−1.04, −0.27]; 0.0033 | −1.38 [−2.18, −0.57]; 0.0032 | −0.40 [−0.83, +0.02]; 0.060 |
| Colombia S4 | −0.43 [−0.68, −0.18]; 0.0028 | −0.67 [−1.33, −0.01]; 0.047 | −0.52 [−1.10, +0.06]; 0.074 |
| Colombia S5 | +0.22 [−0.19, +0.63]; 0.27 | +0.51 [−0.02, +1.04]; 0.058 | +0.49 [+0.07, +0.92]; 0.026 |
| Peru S1 | −0.70 [−1.41, +0.02]; 0.056 | −1.18 [−3.11, +0.74]; 0.21 | −3.90 [−6.39, −1.40]; 0.0050 |
| Peru S5 | +0.96 [−0.13, +2.05]; 0.079 | −1.19 [−2.96, +0.58]; 0.17 | −0.73 [−1.91, +0.46]; 0.21 |
| Taiwan S1 | −0.60 [−1.20, −0.00]; 0.049 | −0.89 [−1.82, +0.04]; 0.060 | −0.80 [−1.63, +0.02]; 0.056 |
| Taiwan S5 | −17.30 [−27.03, −7.57]; 0.0017 | −13.78 [−21.93, −5.63]; 0.0025 | −8.72 [−14.20, −3.25]; 0.0038 |


**Table S2-11. Excess gain after causal quantile recalibration.** WIS is the weighted interval score on log(1 + cases), computed from the median and the 0.1–0.9 deciles. Rows are district × target week × horizon, origin-year rows only (forecast origin in the target's epidemiological year), after the v2 exclusions (districts without geometry, incomplete weeks, and Espírito Santo test-year weeks in Brazil). Taiwan includes test year 2021 unless stated. Separately for L3+C\* and L4+C\*, per horizon and seed, additive per-quantile shifts on the log(1 + cases) scale are fitted only on earlier test years: one shift per quantile (global) or one per bin of the forecast median (Mondrian). The first test year has no earlier year and is left unadjusted in the first three columns; the fourth column drops it. The last column gives the 80% coverage of L4+C\* on rows with cases, raw and after Mondrian shifts. DM test with EWC and HLN; unadjusted p. Brazil S4 (held-out random districts): [[PENDING: BR S4]].

<!-- src: S5_recalibration.csv per cell, years and calibration: pct_of_ref, p; cov80pos_L4+C* -->
| Cell | Raw: %; p | Global shift: %; p | Mondrian shift: %; p | Mondrian, from 2nd test year: %; p | L4+C\* 80% coverage on cases > 0, raw → Mondrian |
|---|---|---|---|---|---|
| Brazil S1 | +0.23; 0.39 | +0.23; 0.39 | +0.24; 0.36 | +0.33; 0.29 | 0.66 → 0.69 |
| Brazil S2 | −0.00; 1.0 | −0.00; 1.0 | +0.06; 0.76 | +0.15; 0.51 | 0.66 → 0.69 |
| Brazil S3 | −0.16; 0.090 | −0.16; 0.090 | −0.08; 0.51 | −0.06; 0.69 | 0.66 → 0.69 |
| Brazil S5 | −0.60; <0.001 | −0.54; <0.001 | −0.44; <0.001 | −0.42; <0.001 | 0.64 → 0.67 |
| Colombia S1 | −0.39; 0.0011 | −0.39; 0.0011 | −0.40; 0.0089 | −0.29; 0.13 | 0.71 → 0.70 |
| Colombia S2 | −0.47; <0.001 | −0.47; <0.001 | −0.48; 0.0038 | −0.42; 0.045 | 0.70 → 0.70 |
| Colombia S3 | −0.65; 0.0033 | −0.65; 0.0033 | −0.61; 0.0041 | −0.57; 0.0046 | 0.70 → 0.70 |
| Colombia S4 | −0.43; 0.0028 | −0.43; 0.0028 | −0.45; 0.012 | −0.31; 0.15 | 0.71 → 0.70 |
| Colombia S5 | +0.22; 0.27 | +0.22; 0.27 | +0.25; 0.20 | −0.10; 0.26 | 0.75 → 0.73 |
| Peru S1 | −0.70; 0.056 | −0.69; 0.047 | −0.64; 0.11 | −0.42; 0.37 | 0.67 → 0.76 |
| Peru S5 | +0.96; 0.079 | +0.75; 0.16 | −0.05; 0.91 | −0.38; 0.30 | 0.67 → 0.77 |
| Taiwan S1 | −0.60; 0.049 | −0.60; 0.049 | −0.60; 0.049 | −0.35; 0.15 | 0.24 → 0.24 |
| Taiwan S5 | −17.30; 0.0017 | −15.02; 0.0026 | −15.01; 0.0027 | −12.01; 0.018 | 0.61 → 0.60 |


**Table S2-12. Fixed control panel in the temporal split (S1).** WIS is the weighted interval score on log(1 + cases), computed from the median and the 0.1–0.9 deciles. Rows are district × target week × horizon, origin-year rows only (forecast origin in the target's epidemiological year), after the v2 exclusions (districts without geometry, incomplete weeks, and Espírito Santo test-year weeks in Brazil). Gains are percentages of WIS(L3) on the same rows; positive values mean the added input improves the forecast. 95% confidence intervals (CIs) and p values come from the Diebold–Mariano (DM) test with the equal-weighted cosine (EWC) long-run variance and the Harvey–Leybourne–Newbold (HLN) correction, applied to the weekly mean loss difference; p values are unadjusted unless marked Holm. Each row replaces C\* by one fixed control: C1 historical risk (district mean log(1 + cases) in the years before 2018), C2 coordinates (spherical harmonics), C3 a fixed other district's AlphaEarth series, C6 district identifier (categorical). Identity gain = L3 vs L3+Ck; excess gain = L3+Ck vs L4+Ck; the bottom rows give the embedding gain without a control. Seed 0 only (so Brazil C1 differs slightly from the three-seed Table 2 value); no multiplicity adjustment. The panel is scored on the same primary rows as Table 2 (v2 exclusions and origin-year filter), but the Taiwan rows exclude 2021 because the panel reuses runs made before 2021 was added; Taiwan values are comparable within the panel, not with Table 2. <!-- src: S2_control_panel.csv scoring = v3_excl_v2_origin_year; RE_summary.md caveats -->

<!-- src: S2_control_panel.csv per country and control: G_id_pct, G_id_pct_lo95, G_id_pct_hi95, G_id_p; G_excess_pct, G_excess_pct_lo95, G_excess_pct_hi95, G_excess_p; G_emb_pct, G_emb_pct_lo95, G_emb_pct_hi95, G_emb_p; status -->
| Country (S1) | Control | Identity gain with this control, % [95% CI]; p | Excess gain with this control, % [95% CI]; p |
|---|---|---|---|
| Brazil | C1 | +0.02 [−0.15, +0.20]; 0.77 | +0.25 [−0.32, +0.81]; 0.37 |
| Brazil | C2 | +0.14 [−0.16, +0.43]; 0.34 | +0.02 [−0.25, +0.29]; 0.88 |
| Brazil | C3 | [[PENDING: BR C3/C6 panel]] | [[PENDING: BR C3/C6 panel]] |
| Brazil | C6 | [[PENDING: BR C3/C6 panel]] | [[PENDING: BR C3/C6 panel]] |
| Colombia | C1 | −0.07 [−0.34, +0.20]; 0.60 | −0.39 [−0.58, −0.19]; 0.0011 |
| Colombia | C2 | −0.12 [−0.21, −0.03]; 0.016 | −0.34 [−0.59, −0.10]; 0.010 |
| Colombia | C3 | −0.12 [−0.20, −0.04]; 0.0053 | −0.33 [−0.49, −0.16]; 0.0011 |
| Colombia | C6 | −2.37 [−2.80, −1.94]; <0.001 | −0.13 [−0.37, +0.12]; 0.27 |
| Peru | C1 | −0.26 [−1.05, +0.53]; 0.49 | −0.70 [−1.41, +0.02]; 0.056 |
| Peru | C2 | −0.31 [−0.73, +0.11]; 0.13 | −0.86 [−1.57, −0.14]; 0.022 |
| Peru | C3 | −0.76 [−1.48, −0.04]; 0.040 | −0.37 [−0.80, +0.05]; 0.081 |
| Peru | C6 | −6.28 [−9.87, −2.69]; 0.0023 | −0.29 [−1.53, +0.96]; 0.63 |
| Taiwan | C1 | −0.63 [−1.69, +0.44]; 0.23 | −0.44 [−1.01, +0.14]; 0.12 |
| Taiwan | C2 | −0.35 [−0.75, +0.04]; 0.075 | −0.77 [−1.88, +0.34]; 0.16 |
| Taiwan | C3 | −0.59 [−1.30, +0.12]; 0.094 | −0.54 [−1.31, +0.23]; 0.15 |
| Taiwan | C6 | −2.20 [−5.54, +1.15]; 0.18 | −0.42 [−1.08, +0.23]; 0.18 |
| Brazil | none (embedding gain, L3 vs L4) | – | +0.29 [−0.27, +0.84]; 0.29 |
| Colombia | none (embedding gain, L3 vs L4) | – | −0.36 [−0.58, −0.13]; 0.0052 |
| Peru | none (embedding gain, L3 vs L4) | – | −0.94 [−1.70, −0.18]; 0.020 |
| Taiwan | none (embedding gain, L3 vs L4) | – | −0.94 [−1.85, −0.03]; 0.043 |


**Table S2-13. Sensitivity cells.** WIS is the weighted interval score on log(1 + cases), computed from the median and the 0.1–0.9 deciles. Rows are district × target week × horizon, origin-year rows only (forecast origin in the target's epidemiological year), after the v2 exclusions (districts without geometry, incomplete weeks, and Espírito Santo test-year weeks in Brazil). Taiwan includes test year 2021 unless stated. Gains are percentages of WIS(L3) on the same rows; positive values mean the added input improves the forecast. 95% confidence intervals (CIs) and p values come from the Diebold–Mariano (DM) test with the equal-weighted cosine (EWC) long-run variance and the Harvey–Leybourne–Newbold (HLN) correction, applied to the weekly mean loss difference; p values are unadjusted unless marked Holm. The last column repeats the matching primary cell. Per-level tuning: L3 and L4 tuned separately on the 2019 grid (31 leaves; the original protocol), with the pre-fix control selection. Taiwan S1 with Brazil's parameters and C\* excludes 2021. Taiwan without 2021 is the pre-review test-year set. The strictly causal yearly-input and two-week reporting-delay runs refit L3 and L4 only, so they estimate the embedding gain only; because they use seed 0, their comparator is the seed-0 Brazil S1 embedding gain, +0.29% [−0.27, +0.84] (Table S2-12), not the three-seed +0.26%. <!-- src: S2_control_panel.csv brazil G_emb_pct, G_emb_pct_lo95, G_emb_pct_hi95 --> No-history rows use N3 as reference and C\* = C2.

<!-- src: T6a_sensitivities.csv per variant and estimand: variant_pct, variant_lo95_pct, variant_hi95_pct, variant_p, variant_status; primary_pct; variant_years -->
| Variant | Gain | Variant: % [95% CI]; p | Primary cell, % |
|---|---|---|---|
| Brazil S1, yearly inputs keyed to the origin year (strictly causal) | embedding | [[PENDING: sensitivities yref/delay2]] | +0.26 (seed 0: +0.29) |
| Brazil S1, 2-week reporting delay | embedding | [[PENDING: sensitivities yref/delay2]] | +0.26 (seed 0: +0.29) |
| Brazil S1, C3 in place of C\* | embedding | [[PENDING: BR C3/C6 panel]] | +0.26 |
| Brazil S1, C3 in place of C\* | identity | [[PENDING: BR C3/C6 panel]] | +0.03 |
| Brazil S1, C3 in place of C\* | excess | [[PENDING: BR C3/C6 panel]] | +0.23 |
| Brazil S1, C6 in place of C\* | embedding | [[PENDING: BR C3/C6 panel]] | +0.26 |
| Brazil S1, C6 in place of C\* | identity | [[PENDING: BR C3/C6 panel]] | +0.03 |
| Brazil S1, C6 in place of C\* | excess | [[PENDING: BR C3/C6 panel]] | +0.23 |
| Brazil S1, per-level tuning (31 leaves; original protocol) | embedding | +0.21 [−0.05, +0.47]; 0.10 | +0.26 |
| Brazil S1, per-level tuning (31 leaves; original protocol) | identity | −0.06 [−0.30, +0.18]; 0.62 | +0.03 |
| Brazil S1, per-level tuning (31 leaves; original protocol) | excess | +0.25 [−0.07, +0.56]; 0.11 | +0.23 |
| Taiwan S1, Brazil's parameters and C\* (no 2021) | embedding | −0.87 [−1.78, +0.03]; 0.057 | −1.06 |
| Taiwan S1, Brazil's parameters and C\* (no 2021) | identity | −0.71 [−1.67, +0.26]; 0.14 | −0.63 |
| Taiwan S1, Brazil's parameters and C\* (no 2021) | excess | −0.33 [−0.89, +0.23]; 0.22 | −0.60 |
| Taiwan S1 without 2021 | embedding | −0.94 [−1.85, −0.03]; 0.043 | −1.06 |
| Taiwan S1 without 2021 | identity | −0.63 [−1.69, +0.44]; 0.23 | −0.63 |
| Taiwan S1 without 2021 | excess | −0.44 [−1.01, +0.14]; 0.12 | −0.60 |
| Taiwan S5 without 2021 | embedding | −14.68 [−20.24, −9.11]; <0.001 | −21.60 |
| Taiwan S5 without 2021 | identity | −2.31 [−5.52, +0.90]; 0.14 | −3.36 |
| Taiwan S5 without 2021 | excess | −11.16 [−15.66, −6.65]; <0.001 | −17.30 |
| Brazil S1, no-history arm (reference N3; C\* = C2) | embedding | +2.54 [−0.82, +5.89]; 0.13 | +0.26 |
| Brazil S1, no-history arm (reference N3; C\* = C2) | identity | +3.30 [+1.68, +4.93]; <0.001 | +0.03 |
| Brazil S1, no-history arm (reference N3; C\* = C2) | excess | −0.43 [−2.06, +1.19]; 0.58 | +0.23 |
| Brazil S2, no-history arm | embedding | [[PENDING: BR S2 no-history]] | −0.02 |
| Brazil S2, no-history arm | identity | [[PENDING: BR S2 no-history]] | −0.05 |
| Brazil S2, no-history arm | excess | [[PENDING: BR S2 no-history]] | −0.00 |


**Table S2-14. Taiwan test year 2021 on its own.** Mean WIS on log(1 + cases) on the 2021 rows (all targets zero; Taiwan had no local cases in 2021), horizons 1 and 4 pooled, origin-year rows, v2 exclusions, seed 0. The last columns give the absolute excess gain and its unadjusted DM p (EWC and HLN). Percentages are not shown because WIS(L3) is close to zero.

<!-- src: docs/results/review/RG_tw2021.md, table "2021 rows on their own (v3, mean log-WIS, h {1, 4})" -->
| Cell | L3 | L4 | L3+C\* | L4+C\* | Excess gain (absolute) | p |
|---|---|---|---|---|---|---|
| Taiwan S1 | 0.00031 | 0.00050 | 0.00031 | 0.00058 | −0.00026 | 0.077 |
| Taiwan S5 | 0.00394 | 0.01171 | 0.00512 | 0.01193 | −0.00665 | 0.091 |

**Table S2-15. Embedding similarity of held-out districts and their excess gain.** Similarity is the maximum cosine similarity between a held-out district's renormalised AlphaEarth vector for year y − 1 and those of the training districts. Part A: Spearman correlation between district gain and similarity, with naive p values (districts are not independent). Part B: similarity quintiles in the held-out-country cells (S5), with the absolute excess gain in units of 10⁻⁴ WIS on log(1 + cases), its 95% CI, the quintile's WIS(L3) and the share of districts with a negative excess gain. Horizons 1 and 4 pooled, origin-year rows, v2 exclusions; Taiwan includes 2021. Exploratory, unadjusted. For comparison, quintile means of similarity are 0.95–0.99 in Brazil S2 and 0.93–0.98 in Colombia S2. <!-- src: S7b_embedding_distance_bins.csv cos_max_mean BR_S2, CO_S2 -->

*Part A.*

<!-- src: S7_embedding_distance.csv, distance = cos_max: spearman_rho, p_naive, n_units per cell and estimand -->
| Cell | Districts | Spearman ρ, district excess gain vs similarity (naive p) | Spearman ρ, district embedding gain vs similarity (naive p) |
|---|---|---|---|
| Brazil S2 | 5,439 | +0.04 (0.0018) | +0.07 (<0.001) |
| Brazil S3 | 5,439 | +0.12 (<0.001) | +0.07 (<0.001) |
| Brazil S5 | 5,439 | +0.10 (<0.001) | +0.20 (<0.001) |
| Colombia S2 | 1,070 | +0.03 (0.36) | +0.01 (0.82) |
| Colombia S3 | 1,070 | −0.04 (0.16) | −0.01 (0.64) |
| Colombia S4 | 1,070 | +0.07 (0.015) | +0.08 (0.0068) |
| Colombia S5 | 1,070 | +0.15 (<0.001) | +0.02 (0.50) |
| Peru S5 | 115 | +0.47 (<0.001) | +0.48 (<0.001) |
| Taiwan S5 | 285 | −0.13 (0.024) | −0.22 (<0.001) |

*Part B.*

<!-- src: S7b_embedding_distance_bins.csv, cells BR_S5, CO_S5, PE_S5, TW_S5, per bin: cos_max_lo, cos_max_hi, n_units, zero_share, wis_L3, G_excess, G_excess_lo95, G_excess_hi95 (×10^4), G_excess_share_units_neg -->
| Cell | Similarity quintile (max cosine range) | Districts | WIS(L3) | Excess gain, WIS ×10⁻⁴ [95% CI] | Districts harmed |
|---|---|---|---|---|---|
| Brazil S5 | Q1 (0.43–0.67) | 1088 | 0.1035 | −14.0 [−14.8, −13.2] | 90% |
| Brazil S5 | Q2 (0.67–0.72) | 1088 | 0.1522 | −12.6 [−13.5, −11.7] | 82% |
| Brazil S5 | Q3 (0.72–0.76) | 1087 | 0.1781 | −12.6 [−13.5, −11.6] | 81% |
| Brazil S5 | Q4 (0.76–0.80) | 1088 | 0.2429 | −9.4 [−10.4, −8.4] | 71% |
| Brazil S5 | Q5 (0.80–0.99) | 1088 | 0.2802 | −10.0 [−11.2, −8.9] | 71% |
| Colombia S5 | Q1 (0.53–0.78) | 214 | 0.1015 | −1.6 [−3.6, +0.5] | 73% |
| Colombia S5 | Q2 (0.78–0.81) | 214 | 0.1307 | +1.7 [−0.4, +3.8] | 58% |
| Colombia S5 | Q3 (0.81–0.84) | 214 | 0.1305 | +4.1 [+2.1, +6.1] | 50% |
| Colombia S5 | Q4 (0.84–0.86) | 214 | 0.1363 | +6.6 [+4.2, +9.1] | 47% |
| Colombia S5 | Q5 (0.86–0.99) | 214 | 0.1201 | +3.4 [+1.4, +5.4] | 57% |
| Peru S5 | Q1 (0.62–0.76) | 23 | 0.2211 | −30.4 [−48.0, −12.8] | 78% |
| Peru S5 | Q2 (0.76–0.84) | 23 | 0.2562 | +2.0 [−34.6, +38.7] | 70% |
| Peru S5 | Q3 (0.85–0.88) | 23 | 0.2336 | +41.8 [+5.5, +78.2] | 57% |
| Peru S5 | Q4 (0.88–0.92) | 23 | 0.1768 | +37.8 [+7.0, +68.7] | 43% |
| Peru S5 | Q5 (0.93–0.99) | 23 | 0.3040 | +64.7 [+31.6, +97.7] | 22% |
| Taiwan S5 | Q1 (0.49–0.74) | 57 | 0.0054 | −32.1 [−35.7, −28.5] | 100% |
| Taiwan S5 | Q2 (0.74–0.76) | 57 | 0.0147 | −39.3 [−44.2, −34.5] | 100% |
| Taiwan S5 | Q3 (0.76–0.78) | 57 | 0.0171 | −32.7 [−35.9, −29.5] | 100% |
| Taiwan S5 | Q4 (0.78–0.80) | 57 | 0.0182 | −31.6 [−34.2, −29.0] | 100% |
| Taiwan S5 | Q5 (0.80–0.88) | 57 | 0.0473 | −42.3 [−45.8, −38.8] | 100% |


Taiwan S5 harm did not shrink with similarity (−31.6 to −42.3 × 10⁻⁴ per quintile; all 285 districts harmed), while Peru S5 showed a gradient, from −30.4 × 10⁻⁴ in the least similar quintile to +64.7 × 10⁻⁴ in the most similar (ρ = +0.47). <!-- src: S7b_embedding_distance_bins.csv TW_S5, PE_S5 G_excess, G_excess_share_units_neg; S7_embedding_distance.csv PE_S5 spearman_rho -->

**Table S2-16. Excess gain by test year.** WIS is the weighted interval score on log(1 + cases), computed from the median and the 0.1–0.9 deciles. Rows are district × target week × horizon, origin-year rows only (forecast origin in the target's epidemiological year), after the v2 exclusions (districts without geometry, incomplete weeks, and Espírito Santo test-year weeks in Brazil). Taiwan includes test year 2021 unless stated. Values are percentages of that year's WIS(L3), horizons 1 and 4 pooled; * marks unadjusted p < 0.05 (DM test with EWC and HLN; CIs are in the source file). For Taiwan the absolute excess gain (×10⁻⁴ WIS) is given in brackets, because WIS(L3) is close to zero outside the 2023 outbreak and the percentages are unstable (2021 had no local cases). Context: 2020–2021 COVID-19 era; Peru 2023 record season; Taiwan 2023 outbreak; Brazil 2024 record epidemic. Brazil S4 (held-out random districts): [[PENDING: BR S4]].

<!-- src: S8_per_year.csv, estimand = G_excess, per cell and test_year: pct_of_ref, lo95_pct, hi95_pct, p (* = p < 0.05, unadjusted); estimate (absolute, shown ×10^-4 in brackets) for Taiwan -->
| Cell | 2020 | 2021 | 2022 | 2023 | 2024 |
|---|---|---|---|---|---|
| Brazil S1 | −0.22 | −0.67* | +0.12 | +0.42 | +0.88 |
| Brazil S2 | −0.38 | −0.77* | −0.07* | +0.32 | +0.41 |
| Brazil S3 | −0.19* | −0.97* | −0.05 | +0.05 | +0.02 |
| Brazil S5 | −0.56 | −1.67* | −0.65* | −0.48 | −0.23 |
| Colombia S1 | −0.56* | −0.34 | −0.22 | – | – |
| Colombia S2 | −0.56* | −0.57 | −0.29* | – | – |
| Colombia S3 | −0.68 | −0.76* | −0.54* | – | – |
| Colombia S4 | −0.66* | −0.43 | −0.16 | – | – |
| Colombia S5 | +0.80* | −0.31 | −0.02 | – | – |
| Peru S1 | −1.38 | −1.24 | −0.51 | +0.06 | – |
| Peru S5 | +1.11 | +1.37 | +1.43* | +0.17 | – |
| Taiwan S1 | −15.69 (−3.9) | −85.74 (−2.6) | −0.23 (−0.0) | −0.04 (−0.5) | −3.06 (−2.3) |
| Taiwan S5 | −47.64* (−39.8) | −173.45 (−66.4) | −86.19* (−28.9) | −1.90 (−14.0) | −21.23* (−25.1) |


In all four Brazilian cells the excess gain was lowest in 2021 (−0.67% to −1.67%; each unadjusted p < 0.05), a COVID-19-era year [@chen2022covid; @roster2024covidbrazil], and highest in 2023–2024; the largest yearly estimate was Brazil S1 in 2024, Brazil's largest recorded epidemic (+0.88% [−0.93, +2.69]) [@gurgelgoncalves2024brazil]. Colombia S1–S4 were negative in every year; Peru S1 was negative in 2020–2022 and +0.06% in its 2023 record season [@munayco2024peru]. Taiwan's yearly percentages are unstable because WIS(L3) is near zero outside its 2023 outbreak (2023: S1 −0.04%, S5 −1.90%). <!-- src: S8_per_year.csv G_excess pct_of_ref, lo95_pct, hi95_pct, p, context (moved from the main Results, per-year view) -->

**Table S2-17. Exploratory strata by surveillance history and population (computed before the origin-year filter and the Espírito Santo exclusion).** Excess gain as a percentage of the stratum's own WIS(L3); * marks unadjusted p < 0.05. History = number of years in 2014–2017 with at least one reported case (n = districts with none). Population terciles are formed within each cell and test year from population in the year before the test year. These strata were computed before the review changes and were not regenerated in results kit v3: they use all rows (no origin-year filter), the v1 exclusions (Espírito Santo included) and Taiwan without 2021, so they differ slightly from the primary estimates. Urban-growth terciles (change in built-up share, 2010–2015) are in the source file and show no consistent pattern. Exploratory, no multiplicity adjustment.

<!-- src: docs/results/review/RB_strata.csv, estimand = G_excess, dimension history (0, 1-2, 3-4) and pop_tercile (T1-T3): pct_of_own_ref, p, n_units (pre-review scoring: all rows, exclusions v1, Taiwan without 2021) -->
| Cell | No case 2014–17 | 1–2 years | 3–4 years | Population T1 (smallest) | T2 | T3 (largest) |
|---|---|---|---|---|---|---|
| Brazil S1 | +0.55 (n = 507) | +0.58 | +0.21 | +0.27 | +0.33 | +0.21 |
| Brazil S2 | +0.04 (n = 507) | +0.15 | −0.00 | +0.02 | +0.05 | −0.01 |
| Brazil S3 | −1.76* (n = 507) | −0.45* | −0.03 | −0.17 | −0.08 | −0.14 |
| Brazil S5 | −2.47* (n = 507) | −1.29* | −0.47* | −0.77* | −0.61* | −0.58* |
| Colombia S1 | −1.14* (n = 65) | −0.66* | −0.38* | −0.82* | −0.42* | −0.28* |
| Colombia S2 | −19.74* (n = 65) | −2.74* | −0.39* | −1.27* | −0.52* | −0.27 |
| Colombia S3 | −40.70* (n = 65) | −5.52* | −0.49* | −2.36* | −0.84* | −0.21 |
| Colombia S4 | −7.14* (n = 65) | −2.31* | −0.38* | −1.19* | −0.50* | −0.24 |
| Colombia S5 | −11.63* (n = 65) | −0.81 | +0.22 | −0.63* | +0.15 | +0.39 |
| Peru S1 | −0.31 (n = 34) | +0.50 | −0.81* | −0.00 | −0.49 | −1.13* |
| Peru S5 | −0.75 (n = 34) | −0.35 | +1.35* | +0.75 | +2.18* | −0.09 |
| Taiwan S1 | −0.50 (n = 42) | −0.56 | −0.24 | +0.12 | −0.09 | −0.66 |
| Taiwan S5 | −28.83* (n = 42) | −13.79* | −5.88* | −16.71* | −11.99* | −9.66* |


## S2-E. No-history arm

**Table S2-18. No-history arm, Brazil S1: embedding, identity and excess gains.** WIS is the weighted interval score on log(1 + cases), computed from the median and the 0.1–0.9 deciles. Rows are district × target week × horizon, origin-year rows only (forecast origin in the target's epidemiological year), after the v2 exclusions (districts without geometry, incomplete weeks, and Espírito Santo test-year weeks in Brazil). All 21 case-derived inputs are removed; N3 is L3 without them and N4 is L4 without them. The validation-selected control is coordinates (C2). Gains are percentages of WIS(N3); positive values mean the added input improves the forecast. DM test with EWC and HLN, unadjusted; MDE is the minimum detectable effect at 80% power. Seed 0. The identity share is not estimable because the embedding gain's CI includes zero.

<!-- src: T6b_nohist_estimands.csv, cell BR_S1_nohist, per horizon (1, 4, pooled) and estimand: pct_of_ref, lo95_pct, hi95_pct, p, mde_pct, wis_ref -->
| Horizon | WIS(N3) | Embedding gain, % [95% CI]; p | Identity gain (C2), % [95% CI]; p | Excess gain, % [95% CI]; p | MDE of excess gain, % |
|---|---|---|---|---|---|
| h = 1 | 0.3520 | +2.35 [−0.83, +5.53]; 0.14 | +3.28 [+1.60, +4.96]; <0.001 | −0.53 [−1.99, +0.94]; 0.46 | 2.07 |
| h = 4 | 0.3533 | +2.72 [−0.92, +6.37]; 0.13 | +3.22 [+1.61, +4.84]; <0.001 | −0.29 [−2.13, +1.55]; 0.74 | 2.59 |
| Pooled h{1,4} | 0.3520 | +2.54 [−0.82, +5.89]; 0.13 | +3.30 [+1.68, +4.93]; <0.001 | −0.43 [−2.06, +1.19]; 0.58 | 2.29 |
| Brazil S2, no history | [[PENDING: BR S2 no-history]] | | | | |


**Table S2-19. No-history arm, Brazil S1: ladder.** Mean WIS on log(1 + cases) over rows (lower is better) by horizon and pooled over horizons 1 and 4, with 80% interval coverage over all rows / rows with cases. Origin-year rows, v2 exclusions, seed 0. C1 (static history) is a separate rung, not a candidate for C\*. The last rows give the history-arm L3 and L4 on the same rows for comparison (Brazil S1, three seeds). The N4 + C1 rung was still running.

<!-- src: T6c_nohist_ladder.csv, cell BR_S1_nohist, per label and horizon: wis_log, cov_80, cov_80_nonzero; history-arm comparison from T2_ladder.csv BR_S1 `WIS pooled h{1,4}` -->
| Rung | h = 1 | h = 4 | Pooled h{1,4} | 80% coverage, all / cases > 0 (pooled) |
|---|---|---|---|---|
| N3 (season, climate, remote sensing, population) | 0.3520 | 0.3533 | 0.3526 | 0.85 / 0.43 |
| N3 + C1 (static history: mean log(1+cases) 2014–17) | 0.3473 | 0.3483 | 0.3478 | 0.84 / 0.43 |
| N4 = N3 + AlphaEarth | 0.3437 | 0.3437 | 0.3437 | 0.83 / 0.41 |
| N3 + C2 (coordinates; C\*) | 0.3404 | 0.3419 | 0.3411 | 0.84 / 0.43 |
| N4 + C2 | 0.3423 | 0.3429 | 0.3426 | 0.84 / 0.42 |
| For comparison, history arm L3 / L4 (Brazil S1, same rows) | 0.1419 / 0.1418 | 0.1959 / 0.1952 | 0.1681 / 0.1677 | 0.90 / 0.67 (L4) |
| N4 + C1 | [[PENDING: BR S1 no-history N4+C1]] | | | |


## S2-F. Figure captions

**Figure 1. Study design and information timing.** (A) What is compared. Feature levels add inputs in turn: L0 seasonal naive (same week of the previous year), L1 lagged cases, L2 weekly climate, L3 monthly remote sensing and yearly population, L4 the district's AlphaEarth embedding for the previous year. From L3, four LightGBM models form a 2 × 2 grid (with or without embeddings; with or without the validation-selected location control C\*). The three arrows define the embedding gain (L3 to L4), the identity gain (L3 to L3+C\*) and the excess gain (L3+C\* to L4+C\*, the primary estimand). C\* is chosen at the 2019 origin from C1 historical risk, C2 coordinates, C3 shuffled embedding, C4/C4s random smooth fields and C5 a 2023 embedding snapshot. (B) Where models are tested. S1 new years (train on target years 2018 to Y − 1, test year Y); S2 held-out groups of states; S3 held-out spatial blocks with a buffer of excluded districts (D = 225 km in Brazil, 130 km in Colombia); S4 held-out random districts; S5 held-out country. S2–S4 are run in Brazil and Colombia, S1 and S5 in all four countries; held-out districts keep their own lagged cases. (C) Information timing for one forecast. Case and climate inputs end at the forecast origin; remote sensing uses the last complete months before the origin month; yearly inputs (AlphaEarth, population, night lights, built-up share) come from the year before the target's epidemiological year; training targets run to the last week of Y − 1. Targets in the first h weeks of Y, whose origin lies in Y − 1, are dropped from primary scoring (origin-year rows only). Horizons h = 1 to 4 weeks; primary estimates pool h = 1 and 4. <!-- spec: 02_methods.md, FIGURE 1 SPEC (writer B) -->

**Figure 2. Excess gain from AlphaEarth embeddings in each primary cell** (`docs/results/figures/F1_forest_G_excess.png`). Points show the excess gain (L3+C\* vs L4+C\*) as a percentage of WIS(L3), horizons 1 and 4 pooled, on origin-year rows after the v2 exclusions; positive values mean the embeddings improve the forecast. Thick bars are 90% CIs and thin bars 95% CIs (DM test with EWC and HLN). The shaded band is the ±1% equivalence margin. Filled markers have a Holm-adjusted p < 0.05 over the 13 available cells (final m = 14). Taiwan S5 (−17.30% [−27.03, −7.57]; an absolute −0.0035 in WIS on log(1 + cases)) is drawn in its own panel on its own scale. Brazil S4: [[PENDING: BR S4]] <!-- src: T1_primary_family.csv; figure F1_forest_G_excess.png, results kit v3. The figure title still says "best location control"; it should read "validation-selected location control" (see notes_C.md). -->

**Figure 3. Contributions of three types of target week to the excess gain** (`docs/results/figures/F2_strata_contributions.png`). For each primary cell, bars give the additive contribution to the excess gain of weeks with cases, of zero weeks listed by the source (Brazil 2020–2021 only) and of zero weeks filled by us, each as a percentage of the cell's WIS(L3), with 95% CIs (DM test with EWC and HLN, unadjusted). The diamond is the total; the bars add up to it exactly. Horizons 1 and 4 pooled, origin-year rows, v2 exclusions; negative values mean the embeddings hurt. One panel per country; the Taiwan panel has its own scale and includes 2021. Brazil S4: [[PENDING: BR S4]] <!-- src: T5_strata.csv contribution columns -->

**Figure 4. No-history arm ladder, Brazil S1** (`docs/results/figures/FS2_nohist_ladder.png`). Mean WIS on log(1 + cases) over rows (lower is better) at horizon 1, horizon 4 and pooled over both, for N3 (season, climate, remote sensing and population, without any case-derived input), N4 (N3 plus AlphaEarth), N3+C1 (static history: district mean log(1 + cases), 2014–2017), N3+C2 (coordinates, the validation-selected control) and N4+C2. Origin-year rows, v2 exclusions, seed 0, 2,703,183 rows. No CIs are drawn; the gains and their 95% CIs are in Table S2-18. For scale, the history-arm L3 on the same rows scores 0.1681. [[PENDING: BR S2 no-history]] <!-- src: T6c_nohist_ladder.csv n_rows; T2_ladder.csv BR_S1 L3 -->

**Figure S2-1. Similarity to the training districts and excess gain in the held-out-country split (S5)** (`docs/results/figures/F3_s5_embedding_distance.png`). One panel per held-out country. The x axis is a district's maximum cosine similarity between its renormalised AlphaEarth vector (year y − 1) and those of the training districts; the y axis is the district's excess gain as a percentage of the cell's WIS(L3) (negative means the embeddings hurt). Grey points are districts (those outside the 1st–99th percentile are not shown); blue points are quintile means with 95% CIs. Horizons 1 and 4 pooled, origin-year rows, v2 exclusions; Taiwan includes 2021. Exploratory. <!-- src: S7b_embedding_distance_bins.csv G_excess_pct_cell -->

**Figure S2-2. Excess gain by test year** (`docs/results/figures/F4_per_year_gains.png`). Excess gain as a percentage of that year's WIS(L3), horizons 1 and 4 pooled, with 95% CIs (DM test with EWC and HLN, unadjusted), for every primary cell, coloured by split; the shaded band is ±1%. Each country panel has its own scale. Taiwan's percentages in 2020–2022 and 2024 are large because WIS(L3) is close to zero in those years (2021 had no local cases); absolute values are in Table S2-16. Origin-year rows, v2 exclusions. Brazil S4: [[PENDING: BR S4]] <!-- src: S8_per_year.csv -->

**Figure S2-3. Feature ladder in the temporal split (S1) by country** (`docs/results/figures/FS1_ladder_S1.png`). Mean WIS on log(1 + cases) over rows (lower is better) for L1, L2, L3, L4, L3+C1 and L4+C1 at horizons 1–4 (thin lines) and pooled over horizons 1 and 4 (black squares). C\* is C1 in every country. The seasonal naive L0 is off scale; its pooled value is printed above each panel. Origin-year rows, v2 exclusions. The Taiwan panel excludes 2021, and its L2 point was tuned separately (per-level) and is not comparable with the other Taiwan rungs. <!-- src: T2_ladder.csv; S1_baselines.csv -->
