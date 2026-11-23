# Supplementary Results

Most WIS values in this supplement are week-weighted: we average over districts and horizons within each target week, then average over weeks. Tables marked "row mean" instead average over all rows, so their values differ slightly from the week-weighted ones (details below). Unless a table states otherwise, the following conventions apply.

- Score: the weighted interval score (WIS) on log(1 + cases), computed from the median and the deciles 0.1 to 0.9.
- Rows: one row is one district, target week and horizon, with horizons 1 and 4 pooled. Only origin-year rows are scored, that is, forecasts whose origin lies in the target's epidemiological year.
- Exclusions: districts without a boundary polygon, two incomplete Peruvian department-weeks, and Espírito Santo from 29 December 2019. Taiwan includes test year 2021 unless a row or table says "without 2021".
- Gains: percentages of the reference model's WIS on the same rows (L3, or N3 without case history). A positive value means that the added input reduced forecast error.
- Tests: confidence intervals (CIs) and p values come from the main test, a Diebold–Mariano (DM) test on the weekly mean loss difference with the equal-weighted cosine (EWC) variance and the Harvey–Leybourne–Newbold (HLN) correction. p values are unadjusted unless marked Holm.
- Rounding: percentages have two decimals, p values two significant digits (smallest shown <0.001) and WIS four decimals. A value that rounds to zero is written 0.00, without a sign. An interval bound that rounds to zero is given to one more decimal so that its side of zero stays visible (for example −0.003).

The codes are defined in the glossary of the Supplementary Methods. Model codes: L0, seasonal naive; L1, case history; L2, adds weekly climate; L3, the reference model, adds remote sensing and population; L4, the embedding model, adds the AlphaEarth embeddings; C\*, the selected location control; N3 and N4, L3 and L4 without any case-derived input. Location controls: C1, average past cases; C2, coordinates; C3, shuffled embeddings, which in the held-out-country split act as a noise control of matching size rather than a location control; C4 and C4s, smooth random fields at the fitted range and at a short range; C5, the 2023 embedding snapshot; C6, a district label. Splits: S1, future years; S2, held-out states; S3, held-out regions; S4, held-out districts; S5, held-out country. A comparison is one country with one split. The embedding gain compares L3 with L4, and the control gain compares L3 with L3 + C\*; earlier drafts called the control gain the identity gain, and the code and result files call it `G_id`. The excess gain compares L3 + C\* with L4 + C\*.

The reference WIS and every gain (Table 2 and Tables S21, S24 to S34, S36, S37 and S42) are week-weighted. Tables S17 to S20, S22, S23 and S41 report row means, marked in their titles, so their WIS values differ slightly from the week-weighted ones. For example, the reference model in Brazil's future-years comparison has a WIS of 0.1675 week-weighted and 0.1681 as a row mean. <!-- src: T1_primary_family.csv BR_S1 WIS_L3 0.16753; T2_ladder.csv BR_S1 L3 0.1681 -->

## A. Baselines and model ladder

**Table S17. Forecast error of the baseline and ladder models in the future-years split (row mean).**

<!-- src: S1_baselines.csv, rows with pooled_over = 1,4; columns wis_log, rel_wis_vs_L0, cov_80, cov_80_nonzero; n_rows per country (final kit; Taiwan includes 2021, 141,645 rows; equals R3_C_tw2021_ladder.csv for L0 to L2) -->
| Model | Brazil | Colombia | Peru | Taiwan |
|---|---|---|---|---|
| L0, seasonal naive | 0.4695 (1.00) | 0.3272 (1.00) | 0.6596 (1.00) | 0.0743 (1.00) |
| Negative binomial regression (L1 inputs) | 0.2185 (0.47) | 0.1426 (0.44) | 0.3232 (0.49) | 0.0475 (0.64) |
| TimesFM 2.5, zero-shot | 0.1928 (0.41) | not run | not run | not run |
| LightGBM L1, case history | 0.1700 (0.36) | 0.1226 (0.37) | 0.2442 (0.37) | 0.0316 (0.43) |
| LightGBM L2, + climate | 0.1690 (0.36) | 0.1224 (0.37) | 0.2431 (0.37) | 0.0319 (0.43) |
| LightGBM L3, + remote sensing and population | 0.1681 (0.36) | 0.1220 (0.37) | 0.2438 (0.37) | 0.0320 (0.43) |
| LightGBM L4, + embeddings | 0.1677 (0.36) | 0.1225 (0.37) | 0.2460 (0.37) | 0.0323 (0.43) |
| LightGBM L3 + C\* | 0.1680 (0.36) | 0.1221 (0.37) | 0.2443 (0.37) | 0.0321 (0.43) |
| LightGBM L4 + C\* | 0.1676 (0.36) | 0.1226 (0.37) | 0.2463 (0.37) | 0.0323 (0.44) |
| Rows scored | 2,703,183 | 319,930 | 45,754 | 141,645 |

Note: Mean WIS over rows, with the WIS relative to the seasonal naive baseline (L0) in parentheses. Every model is scored on the same rows, whose number is given in the last row. TimesFM was run for Brazil only. The selected control (C\*) is average past cases (C1) in all four countries. L3, L4, L3 + C\* and L4 + C\* average seeds 0 to 2 in all four countries; the other models use one run. Taiwan includes test year 2021, and its L2 uses the shared configuration (Table S53). The earlier Taiwan values without 2021 used a separately tuned L2. The step from L0 to L1 changes both the inputs and the method.

**Table S18. Coverage of 80% prediction intervals in the future-years split.**

<!-- src: S1_baselines.csv, rows with pooled_over = 1,4; columns wis_log, rel_wis_vs_L0, cov_80, cov_80_nonzero; n_rows per country (final kit; Taiwan includes 2021, 141,645 rows; equals R3_C_tw2021_ladder.csv for L0 to L2) -->
| Model | Brazil | Colombia | Peru | Taiwan |
|---|---|---|---|---|
| L0, seasonal naive | 0.77 / 0.40 | 0.81 / 0.53 | 0.73 / 0.47 | 0.95 / 0.00 |
| Negative binomial regression (L1 inputs) | 0.94 / 0.77 | 0.96 / 0.81 | 0.93 / 0.84 | 0.99 / 0.42 |
| TimesFM 2.5, zero-shot | 0.82 / 0.60 | not run | not run | not run |
| LightGBM L1, case history | 0.91 / 0.68 | 0.93 / 0.72 | 0.84 / 0.70 | 0.98 / 0.24 |
| LightGBM L2, + climate | 0.90 / 0.68 | 0.93 / 0.72 | 0.83 / 0.68 | 0.98 / 0.23 |
| LightGBM L3, + remote sensing and population | 0.90 / 0.67 | 0.93 / 0.72 | 0.83 / 0.68 | 0.98 / 0.25 |
| LightGBM L4, + embeddings | 0.90 / 0.67 | 0.93 / 0.71 | 0.83 / 0.68 | 0.98 / 0.24 |
| LightGBM L3 + C\* | 0.90 / 0.66 | 0.93 / 0.71 | 0.83 / 0.67 | 0.98 / 0.24 |
| LightGBM L4 + C\* | 0.90 / 0.66 | 0.93 / 0.71 | 0.83 / 0.67 | 0.98 / 0.23 |

Note: Share of observations inside the 80% interval, first over all rows and then over rows with at least one case. Models, rows and seeds as in Table S17.

**Table S19. Mean forecast error along the model ladder in each comparison (row mean).**

<!-- src: T2_ladder.csv, column `WIS pooled h{1,4}` per cell and label; cov_80 and cov_80_nonzero of L4+C*; n_rows (final kit; seeds 0–2 averaged where they exist; Taiwan new years includes 2021 and the shared-configuration L2) -->
| Comparison | C\* | L0 | L1 | L2 | L3 | L4 |
|---|---|---|---|---|---|---|
| Brazil, future years | C1 | 0.4695 | 0.1700 | 0.1690 | 0.1681 | 0.1677 |
| Brazil, held-out states | C1 | – | – | – | 0.1689 | 0.1690 |
| Brazil, held-out regions | C1 | – | – | – | 0.1706 | 0.1709 |
| Brazil, held-out districts | C1 | – | – | – | 0.1683 | 0.1679 |
| Brazil, held-out country | C3 | – | – | – | 0.1914 | 0.1921 |
| Colombia, future years | C1 | 0.3272 | 0.1226 | 0.1224 | 0.1220 | 0.1225 |
| Colombia, held-out states | C1 | – | – | – | 0.1225 | 0.1232 |
| Colombia, held-out regions | C1 | – | – | – | 0.1245 | 0.1255 |
| Colombia, held-out districts | C1 | – | – | – | 0.1223 | 0.1229 |
| Colombia, held-out country | C2 | – | – | – | 0.1238 | 0.1239 |
| Peru, future years | C1 | 0.6596 | 0.2442 | 0.2431 | 0.2438 | 0.2460 |
| Peru, held-out country | C3 | – | – | – | 0.2383 | 0.2367 |
| Taiwan, future years | C1 | 0.0743 | 0.0316 | 0.0319 | 0.0320 | 0.0323 |
| Taiwan, held-out country | C3 | – | – | – | 0.0205 | 0.0250 |
| Brazil, future years, per-level tuning (sensitivity) | C1 | 0.4695 | 0.1700 | 0.1690 | 0.1714 | 0.1710 |
| Taiwan, future years, Brazil parameters (sensitivity, without 2021) | C1 | – | – | – | 0.0398 | 0.0402 |

Note: Mean WIS over rows (lower is better), on rows common to every model. L0 to L2 were run in the future-years split only. L3, L4, L3 + C\* and L4 + C\* average seeds 0 to 2 where three seeds exist. That is the case in all future-years comparisons, with Brazil held out and in Colombia's four within-country splits. With Peru or Taiwan held out, only L3 + C\* and L4 + C\* have three seeds. Other comparisons use seed 0. Taiwan, future years, includes 2021 and uses the shared configuration for L2 (Table S53). There are two sensitivity rows. In Brazil, future years, each model was tuned separately, giving L3 and L4 with 31 leaves as in the original protocol, with the earlier control selection. In Taiwan, future years, without 2021, the models used Brazil's configuration and selected control.

**Table S20. Forecast error with the location control, and interval coverage, in each comparison (row mean).**

<!-- src: T2_ladder.csv, column `WIS pooled h{1,4}` per cell and label; cov_80 and cov_80_nonzero of L4+C*; n_rows (final kit; seeds 0–2 averaged where they exist; Taiwan new years includes 2021 and the shared-configuration L2) -->
| Comparison | L3 + C\* | L4 + C\* | 80% coverage of L4 + C\*, all rows / cases > 0 | Rows |
|---|---|---|---|---|
| Brazil, future years | 0.1680 | 0.1676 | 0.90 / 0.66 | 2,703,183 |
| Brazil, held-out states | 0.1690 | 0.1690 | 0.90 / 0.66 | 2,703,183 |
| Brazil, held-out regions | 0.1707 | 0.1710 | 0.90 / 0.66 | 2,703,183 |
| Brazil, held-out districts | 0.1683 | 0.1680 | 0.90 / 0.66 | 2,703,183 |
| Brazil, held-out country | 0.1911 | 0.1924 | 0.88 / 0.64 | 2,703,183 |
| Colombia, future years | 0.1221 | 0.1226 | 0.93 / 0.71 | 319,930 |
| Colombia, held-out states | 0.1225 | 0.1232 | 0.92 / 0.70 | 319,930 |
| Colombia, held-out regions | 0.1246 | 0.1254 | 0.92 / 0.70 | 319,930 |
| Colombia, held-out districts | 0.1224 | 0.1229 | 0.92 / 0.71 | 319,930 |
| Colombia, held-out country | 0.1249 | 0.1246 | 0.94 / 0.75 | 319,930 |
| Peru, future years | 0.2443 | 0.2463 | 0.83 / 0.67 | 45,754 |
| Peru, held-out country | 0.2392 | 0.2369 | 0.84 / 0.67 | 45,754 |
| Taiwan, future years | 0.0321 | 0.0323 | 0.98 / 0.23 | 141,645 |
| Taiwan, held-out country | 0.0216 | 0.0253 | 0.99 / 0.61 | 141,645 |
| Brazil, future years, per-level tuning (sensitivity) | 0.1714 | 0.1710 | 0.90 / 0.68 | 2,703,183 |
| Taiwan, future years, Brazil parameters (sensitivity, without 2021) | 0.0401 | 0.0403 | 0.98 / 0.24 | 113,430 |

Note: Mean WIS over rows. Rows and seeds as in Table S19.

## B. Primary family: secondary gains, control selection and equivalence

**Table S21. Reference error, embedding gain and control gain in each comparison.**

<!-- src: T1_primary_family.csv WIS_L3 per cell (final kit, 14 cells) -->
<!-- src: T1_primary_family.csv, one row per cell: test_years; n_rows; n_seeds; WIS_L4C; G_emb_pct, G_emb_lo95_pct, G_emb_hi95_pct; G_id_pct, G_id_lo95_pct, G_id_hi95_pct; DM_p; TOST_p_Holm. Regenerated from the final kit (14 cells, seeds 0–2 where they exist). -->
| Comparison | Reference WIS (L3) | WIS of L4 + C\* | Embedding gain, % (95% CI) | Control gain, % (95% CI) | DM p, excess gain | Holm TOST p (±1%) |
|---|---|---|---|---|---|---|
| Brazil, future years | 0.1675 | 0.1671 | +0.26 (−0.31 to 0.82) | +0.03 (−0.11 to 0.18) | 0.39 | 0.036 |
| Brazil, held-out states | 0.1683 | 0.1684 | −0.02 (−0.34 to 0.30) | −0.05 (−0.13 to 0.02) | 1.0 | <0.001 |
| Brazil, held-out regions | 0.1701 | 0.1704 | −0.13 (−0.35 to 0.09) | −0.03 (−0.14 to 0.08) | 0.090 | <0.001 |
| Brazil, held-out districts | 0.1678 | 0.1674 | +0.22 (−0.32 to 0.76) | +0.02 (−0.01 to 0.05) | 0.43 | 0.018 |
| Brazil, held-out country | 0.1907 | 0.1917 | −0.39 (−1.34 to 0.55) | +0.15 (−0.89 to 1.18) | <0.001 | 0.055 |
| Colombia, future years | 0.1222 | 0.1228 | −0.38 (−0.61 to −0.16) | −0.06 (−0.32 to 0.19) | 0.0012 | <0.001 |
| Colombia, held-out states | 0.1226 | 0.1233 | −0.60 (−0.81 to −0.39) | −0.06 (−0.09 to −0.03) | <0.001 | 0.0027 |
| Colombia, held-out regions | 0.1246 | 0.1255 | −0.82 (−1.14 to −0.49) | −0.08 (−0.14 to −0.02) | 0.0030 | 0.27 |
| Colombia, held-out districts | 0.1224 | 0.1231 | −0.54 (−0.78 to −0.30) | −0.10 (−0.12 to −0.08) | 0.0017 | 0.0018 |
| Colombia, held-out country | 0.1240 | 0.1247 | −0.04 (−0.37 to 0.28) | −0.81 (−1.16 to −0.46) | 0.27 | 0.0066 |
| Peru, future years | 0.2417 | 0.2442 | −0.91 (−1.62 to −0.20) | −0.20 (−0.92 to 0.52) | 0.022 | 0.85 |
| Peru, held-out country | 0.2362 | 0.2351 | +0.68 (−0.59 to 1.96) | −0.44 (−0.80 to −0.07) | 0.088 | 0.90 |
| Taiwan, future years | 0.0312 | 0.0316 | −0.95 (−1.71 to −0.18) | −0.41 (−0.97 to 0.16) | 0.042 | 0.78 |
| Taiwan, held-out country | 0.0202 | 0.0245 | −21.60 (−31.82 to −11.39) | −3.36 (−6.52 to −0.20) | 0.0039 | 1.0 |

Note: Same rows, tests and selected controls as Table 2. The reference WIS is week-weighted. The embedding gain compares L3 with L4, and the control gain compares L3 with L3 + C\*. DM p is the unadjusted p value of the excess gain. The Holm TOST p tests equivalence within ±1% of the reference WIS, with Holm adjustment over the 14 comparisons. As in Table 2, estimates average seeds 0 to 2 where three seeds exist. With Peru or Taiwan held out, the embedding and control gains use seed 0. Test years and rows are in Table 1.

**Table S22. Selection of the location control at the 2019 origin: reference model, average past cases, coordinates and shuffled embedding (row mean).**

<!-- src: T4_cstar_selection.csv, column wis_log_2019 per cell and candidate (3-seed mean for C3, C4, C4s), `selected`, C_star -->
| Comparison | Reference (L3 or N3) | + C1 | + C2 | + C3 | Selected C\* |
|---|---|---|---|---|---|
| Brazil, future years | 0.17525 | 0.17446 | 0.17715 | 0.17681 | C1 |
| Brazil, held-out states | 0.17542 | 0.17597 | 0.17733 | 0.17757 | C1 |
| Brazil, held-out regions | 0.17715 | 0.17749 | 0.17989 | 0.17916 | C1 |
| Brazil, held-out districts | 0.17500 | 0.17517 | 0.17716 | 0.17684 | C1 |
| Brazil, held-out country | 0.19102 | – | 0.19168 | 0.19182 | C3 |
| Colombia, future years | 0.17019 | 0.17046 | 0.17045 | 0.17042 | C1 |
| Colombia, held-out states | 0.17169 | 0.17176 | 0.17211 | 0.17219 | C1 |
| Colombia, held-out regions | 0.17311 | 0.17315 | 0.17387 | 0.17381 | C1 |
| Colombia, held-out districts | 0.17158 | 0.17167 | 0.17201 | 0.17225 | C1 |
| Colombia, held-out country | 0.18208 | – | 0.17809 | 0.18352 | C2 |
| Peru, future years | 0.16194 | 0.16258 | 0.16431 | 0.16537 | C1 |
| Peru, held-out country | 0.13892 | – | 0.14227 | 0.13997 | C3 |
| Taiwan, future years | 0.00411 | 0.00413 | 0.00439 | 0.00402 | C1 |
| Taiwan, held-out country | 0.00656 | – | 0.00912 | 0.00784 | C3 |
| Brazil, future years, without case history | 0.35428 | – | 0.34633 | 0.35963 | C2 |
| Brazil, held-out states, without case history | 0.36193 | – | 0.35921 | 0.36860 | C2 |

Note: Mean WIS over rows (not week-weighted) at the 2019 validation origin (trained on 2018 targets and scored on 2019 targets; horizons 1 and 4) of the reference model and of the reference model plus each candidate control. C3 is a mean over three seeds; the other columns use one seed. The selection rule (D19) is given in full in Supplementary Methods, section B. In short, candidates whose forecasts equal the reference model's are excluded. Each remaining candidate has a standard error $\mathrm{SE}_k = \sigma_{\mathrm{seed}}/\sqrt{n_k}$, where $\sigma_{\mathrm{seed}}$ is the seed SD pooled over the multi-seed candidates (C3, C4, C4s) and $n_k$ is the number of seeds; single-seed candidates therefore get $\mathrm{SE}_k = \sigma_{\mathrm{seed}}$. The tie set is every candidate with $\mathrm{Score}_k - \mathrm{Score}_{\mathrm{best}} \le 2\sqrt{\mathrm{SE}_{\mathrm{best}}^2 + \mathrm{SE}_k^2}$, and its first member in the order C1, C3, C2, C4s, C4, C5 is selected. Without case history the order is C3, C2, C6, C4s, C4. The plain reference model was not a candidate, so a control was selected even where every candidate scored worse than the reference model. A rule that allows "no control" is a sensitivity analysis (Table S45). <!-- src: scripts/run/select_control.py docstring lines 23-25 and lines 130-148 --> A dash means not a candidate. C1 is not defined across countries. C4s is not a candidate in Peru and Taiwan, where its range equals that of C4. C5 is not a candidate without case history, where C1 forms its own step. C6 is used only in the future-years split without case history. A control scored below L3 only in Brazil (future years), Colombia (held-out country) and Taiwan (future years). In Taiwan the lower-scoring C3 was not selected because of the order of preference. Taiwan's 2019 validation WIS (about 0.004) rests on 56 non-zero validation targets, so its choice of control is effectively arbitrary. <!-- src: T4_cstar_selection.csv TW_S1 wis_log_2019; docs/methods/s1_pipeline.md "Pre-flight findings" (56 non-zero validation targets) --> The test-year results of the two comparisons without case history are in Tables S41 and S42.

**Table S23. Selection of the location control at the 2019 origin: random smooth fields, snapshot and district label (row mean).**

<!-- src: T4_cstar_selection.csv, column wis_log_2019 per cell and candidate (3-seed mean for C3, C4, C4s), `selected`, C_star -->
| Comparison | + C4 | + C4s | + C5 | + C6 |
|---|---|---|---|---|
| Brazil, future years | 0.17782 | 0.17840 | 0.17732 | – |
| Brazil, held-out states | 0.17773 | 0.17900 | 0.17766 | – |
| Brazil, held-out regions | 0.18093 | 0.18162 | 0.18033 | – |
| Brazil, held-out districts | 0.17799 | 0.17855 | 0.17731 | – |
| Brazil, held-out country | 0.19235 | 0.19247 | 0.19252 | – |
| Colombia, future years | 0.17096 | 0.17088 | 0.17093 | – |
| Colombia, held-out states | 0.17288 | 0.17279 | 0.17249 | – |
| Colombia, held-out regions | 0.17490 | 0.17453 | 0.17455 | – |
| Colombia, held-out districts | 0.17269 | 0.17269 | 0.17279 | – |
| Colombia, held-out country | 0.18349 | 0.18367 | 0.18290 | – |
| Peru, future years | 0.16684 | 0.16664 | 0.16372 | – |
| Peru, held-out country | 0.14111 | – | 0.14149 | – |
| Taiwan, future years | 0.00439 | – | 0.00446 | – |
| Taiwan, held-out country | 0.00782 | – | 0.01108 | – |
| Brazil, future years, without case history | 0.34895 | 0.35076 | – | 0.34722 |
| Brazil, held-out states, without case history | 0.35977 | 0.36747 | – | – |

Note: As Table S22. C4 and C4s are means over three seeds.

**Table S24. Equivalence of the excess gain at margins of ±0.5%, ±1% and ±2% of the reference WIS.**

<!-- src: T1b_margin_sensitivity.csv per cell and margin_pct: G_excess_pct, lo90_pct, hi90_pct, within_unadjusted, within_Holm, near_margin -->
| Comparison | Excess gain, % (90% CI) | ±0.5%: unadjusted / Holm | ±1%: unadjusted / Holm | ±2%: unadjusted / Holm |
|---|---|---|---|---|
| Brazil, future years | +0.23 (−0.23 to 0.69) | no / no | yes / yes | yes / yes |
| Brazil, held-out states | 0.00 (−0.28 to 0.28) | yes / yes | yes / yes | yes / yes |
| Brazil, held-out regions | −0.16 (−0.31 to −0.01) | yes / yes | yes / yes | yes / yes |
| Brazil, held-out districts | +0.20 (−0.23 to 0.62) | no / no | yes / yes | yes / yes |
| Brazil, held-out country | −0.68 (−0.89 to −0.47) | no / no | yes / no | yes / yes |
| Colombia, future years | −0.42 (−0.60 to −0.25) | no / no | yes / yes | yes / yes |
| Colombia, held-out states | −0.52 (−0.70 to −0.34) | no / no | yes / yes | yes / yes |
| Colombia, held-out regions | −0.68 (−1.01 to −0.36) | no / no | no / no (near margin) | yes / yes |
| Colombia, held-out districts | −0.45 (−0.64 to −0.25) | no / no | yes / yes | yes / yes |
| Colombia, held-out country | +0.22 (−0.12 to 0.55) | no / no | yes / yes | yes / yes |
| Peru, future years | −0.82 (−1.37 to −0.26) | no / no | no / no | yes / yes |
| Peru, held-out country | +0.93 (0.04 to 1.83) | no / no | no / no | yes / no |
| Taiwan, future years | −0.71 (−1.28 to −0.15) | no / no | no / no | yes / yes |
| Taiwan, held-out country | −18.29 (−27.77 to −8.81) | no / no | no / no | no / no |
| Comparisons within the margin (of 14) |  | 2 / 2 | 9 / 8 | 13 / 12 |

Note: The excess gain is shown with its 90% CI. A comparison is equivalent within the margin when both one-sided tests (TOST) reject at 5%, either unadjusted or with the TOST p values Holm-adjusted over the 14 comparisons. "Near margin" means that a CI bound lies within 0.05 percentage points of the margin. The ±1% margin was chosen after the Brazil and Peru future-years results had been seen. Equivalence for Brazil (future years, held-out states, regions and districts) and Colombia (held-out country) assumes that the weekly loss difference does not drift across seasons. In these five comparisons the surrogate-series check shows that the main test finds effects too often (Table S47).

## C. Robustness of the primary family

**Table S25. Excess gain at horizons 1 and 4 separately.**

<!-- src: T3_estimands.csv rows test_year = pooled, estimand = G_excess, horizon 1 / 4 (pct_of_ref, lo95_pct, hi95_pct, p); S1 secondary pooling from T1_primary_family.csv sec_pct, sec_lo95_pct, sec_hi95_pct, sec_DM_p, sec_years -->
| Comparison | Horizon 1: % (95% CI); p | Horizon 4: % (95% CI); p | Horizons 1 to 4, future years only: % (95% CI); p; years |
|---|---|---|---|
| Brazil, future years | +0.11 (−0.14 to 0.36), 0.36 | +0.32 (−0.48 to 1.13), 0.40 | +0.25 (−0.33 to 0.82), 0.38; 2020–24 |
| Brazil, held-out states | −0.01 (−0.19 to 0.18), 0.95 | 0.00 (−0.47 to 0.47), 0.99 | – |
| Brazil, held-out regions | −0.13 (−0.24 to −0.02), 0.022 | −0.18 (−0.43 to 0.07), 0.14 | – |
| Brazil, held-out districts | +0.11 (−0.14 to 0.35), 0.37 | +0.26 (−0.46 to 0.98), 0.46 | – |
| Brazil, held-out country | −0.59 (−0.80 to −0.38), <0.001 | −0.77 (−1.17 to −0.36), 0.0010 | – |
| Colombia, future years | −0.29 (−0.43 to −0.15), <0.001 | −0.56 (−0.87 to −0.25), 0.0021 | −0.41 (−0.64 to −0.18), 0.0024; 2020–22 |
| Colombia, held-out states | −0.42 (−0.56 to −0.27), <0.001 | −0.64 (−0.96 to −0.32), 0.0010 | – |
| Colombia, held-out regions | −0.67 (−0.90 to −0.45), <0.001 | −0.71 (−1.31 to −0.11), 0.025 | – |
| Colombia, held-out districts | −0.35 (−0.53 to −0.17), 0.0015 | −0.55 (−0.88 to −0.23), 0.0032 | – |
| Colombia, held-out country | −0.07 (−0.29 to 0.15), 0.49 | +0.51 (−0.13 to 1.15), 0.11 | – |
| Peru, future years | −0.22 (−0.51 to 0.07), 0.13 | −1.25 (−2.24 to −0.26), 0.017 | −0.69 (−1.38 to −0.01), 0.047; 2020–23 |
| Peru, held-out country | +0.34 (−0.09 to 0.78), 0.11 | +1.34 (−0.19 to 2.87), 0.081 | – |
| Taiwan, future years | −0.38 (−0.76 to 0.01), 0.054 | −1.01 (−2.07 to 0.04), 0.059 | −0.46 (−1.09 to 0.17), 0.14; 2020–24 (no 2021) |
| Taiwan, held-out country | −14.63 (−22.48 to −6.78), 0.0011 | −20.65 (−35.08 to −6.22), 0.0081 | – |

Note: The future-years comparisons also show a secondary estimate pooled over horizons 1 to 4. It is not part of the Holm family and uses only test years scored at all four horizons. For Taiwan it therefore leaves out 2021, whose runs cover horizons 1 and 4 only.

**Table S26. Excess gain under the two stricter checks.**

<!-- src: T1_primary_family.csv per cell: pct_of_WIS_ref, lo95_pct, hi95_pct, DM_p, Holm_p_available; B4_lo95_pct, B4_hi95_pct, B4_p, B4_Holm_p; p_iaaft, p_iaaft_Holm; delta_lo95_pct, delta_hi95_pct; case_pct, case_p; all rows = unfiltered_pct, unfiltered_p; v1 exclusions = exclv1_pct, exclv1_p for Brazil -->
| Comparison | Excess gain, % (95% CI) | p / Holm p | B = 4: 95% CI | B = 4: p / Holm p | Surrogate-calibrated p / Holm p | 95% CI, reference WIS estimated |
|---|---|---|---|---|---|---|
| Brazil, future years | +0.23 (−0.33 to 0.79) | 0.39 / 1.0 | −0.53 to 1.00 | 0.45 / 1.0 | 0.51 / 1.0 | −0.28 to 0.75 |
| Brazil, held-out states | 0.00 (−0.34 to 0.34) | 1.0 / 1.0 | −0.57 to 0.56 | 1.0 / 1.0 | 1.0 / 1.0 | −0.34 to 0.34 |
| Brazil, held-out regions | −0.16 (−0.34 to 0.03) | 0.090 / 0.53 | −0.49 to 0.18 | 0.26 / 1.0 | 0.21 / 1.0 | −0.36 to 0.05 |
| Brazil, held-out districts | +0.20 (−0.32 to 0.71) | 0.43 / 1.0 | −0.49 to 0.89 | 0.47 / 1.0 | 0.52 / 1.0 | −0.28 to 0.68 |
| Brazil, held-out country | −0.68 (−0.94 to −0.42) | <0.001 / <0.001 | −1.06 to −0.31 | 0.0073 / 0.095 | <0.001 / 0.0070 | −1.01 to −0.35 |
| Colombia, future years | −0.42 (−0.64 to −0.21) | 0.0012 / 0.014 | −0.70 to −0.14 | 0.014 / 0.15 | 0.0035 / 0.038 | −0.64 to −0.21 |
| Colombia, held-out states | −0.52 (−0.74 to −0.30) | <0.001 / 0.0034 | −0.71 to −0.33 | 0.0016 / 0.022 | <0.001 / 0.0070 | −0.76 to −0.29 |
| Colombia, held-out regions | −0.68 (−1.08 to −0.29) | 0.0030 / 0.030 | −1.09 to −0.28 | 0.0093 / 0.11 | <0.001 / 0.0070 | −1.13 to −0.24 |
| Colombia, held-out districts | −0.45 (−0.68 to −0.21) | 0.0017 / 0.019 | −0.75 to −0.14 | 0.015 / 0.15 | 0.0060 / 0.054 | −0.68 to −0.21 |
| Colombia, held-out country | +0.22 (−0.19 to 0.63) | 0.27 / 1.0 | −0.58 to 1.01 | 0.49 / 1.0 | 0.46 / 1.0 | −0.17 to 0.60 |
| Peru, future years | −0.82 (−1.49 to −0.14) | 0.022 / 0.18 | −1.94 to 0.31 | 0.11 / 0.68 | 0.040 / 0.28 | −1.55 to −0.08 |
| Peru, held-out country | +0.93 (−0.16 to 2.02) | 0.088 / 0.53 | 0.25 to 1.62 | 0.020 / 0.18 | 0.0050 / 0.050 | −0.20 to 2.06 |
| Taiwan, future years | −0.71 (−1.40 to −0.03) | 0.042 / 0.29 | −1.36 to −0.07 | 0.037 / 0.27 | 0.0070 / 0.056 | −1.65 to 0.22 |
| Taiwan, held-out country | −18.29 (−29.80 to −6.78) | 0.0039 / 0.035 | −34.29 to −2.29 | 0.034 / 0.27 | 0.048 / 0.29 | −43.79 to 7.21 |

Note: Main test as in Table 2, with Holm adjustment over the 14 comparisons. B = 4: the strict-variance check, the same test with 4 cosine terms in the variance, which is less affected by slow drift across seasons. Surrogate-calibrated p: the surrogate-series check, which compares the observed statistic with 2,000 iterative amplitude-adjusted Fourier transform (IAAFT) surrogates of the comparison's own weekly loss-difference series. Last column: delta-method 95% CI of the percentage, which allows for uncertainty in the reference WIS. In Brazil, future years (three seeds), the seed standard deviation of the excess gain is 0.00002, against a standard error of 0.00044. <!-- src: T1_primary_family.csv BR_S1 seed_sd, se --> The standard errors of the three-seed comparisons average over seeds. In each of them the seed standard deviation of the excess gain is at most about the size of its standard error (Brazil held out 0.00024 against 0.00023). <!-- src: T1_primary_family.csv seed_sd, se --> With Peru held out, the excess gain was positive before adjustment under both stricter checks (B = 4 p = 0.020; surrogate-calibrated p = 0.0050). After Holm correction the B = 4 p was 0.18, and the surrogate-calibrated p sat exactly at the threshold (0.04998). This is the only gain in the family that reaches the threshold under any of the tests. <!-- src: T1_primary_family.csv PE_S5 B4_p, p_iaaft, B4_Holm_p, p_iaaft_Holm -->

**Table S27. Excess gain on the case scale, on all rows and without the Espírito Santo exclusion.**

<!-- src: T1_primary_family.csv per cell: pct_of_WIS_ref, lo95_pct, hi95_pct, DM_p, Holm_p_available; B4_lo95_pct, B4_hi95_pct, B4_p, B4_Holm_p; p_iaaft, p_iaaft_Holm; delta_lo95_pct, delta_hi95_pct; case_pct, case_p; all rows = unfiltered_pct, unfiltered_p; v1 exclusions = exclv1_pct, exclv1_p for Brazil -->
| Comparison | Case scale, % | Case scale, p | All rows, % | All rows, p | Earlier exclusions, % | Earlier exclusions, p |
|---|---|---|---|---|---|---|
| Brazil, future years | −0.03 | 0.92 | +0.26 | 0.39 | +0.23 | 0.40 |
| Brazil, held-out states | −0.73 | 0.025 | +0.03 | 0.89 | −0.01 | 0.94 |
| Brazil, held-out regions | −1.30 | 0.065 | −0.10 | 0.40 | −0.19 | 0.045 |
| Brazil, held-out districts | −0.37 | 0.13 | +0.23 | 0.42 | +0.19 | 0.44 |
| Brazil, held-out country | −0.89 | 0.18 | −0.69 | <0.001 | −0.70 | <0.001 |
| Colombia, future years | −0.84 | 0.052 | −0.42 | <0.001 | – | – |
| Colombia, held-out states | −0.75 | 0.15 | −0.53 | <0.001 | – | – |
| Colombia, held-out regions | −0.78 | 0.20 | −0.71 | 0.0025 | – | – |
| Colombia, held-out districts | −1.05 | 0.074 | −0.45 | 0.0011 | – | – |
| Colombia, held-out country | +0.51 | 0.068 | +0.18 | 0.33 | – | – |
| Peru, future years | −1.35 | 0.077 | −0.73 | 0.046 | – | – |
| Peru, held-out country | −0.61 | 0.58 | +0.99 | 0.051 | – | – |
| Taiwan, future years | −0.13 | 0.12 | −0.66 | 0.062 | – | – |
| Taiwan, held-out country | −3.66 | 0.0033 | −18.46 | 0.0029 | – | – |

Note: Case scale: excess gain in the WIS of raw case counts, as a percentage of the case-scale reference WIS (secondary scale). All rows: without the origin-year filter. Earlier exclusions: Brazil scored without the Espírito Santo exclusion. A dash means not applicable.

## D. Where the difference arises

**Table S28. Additive contributions of three types of target week to the excess gain.**

<!-- src: T5_strata.csv, estimand = G_excess, per cell and stratum: row_share; pct_of_ref, lo95_pct, hi95_pct (stratum estimate, % of the stratum's own WIS(L3)); contrib_pct, contrib_lo95_pct, contrib_hi95_pct, contrib_p (additive contribution, % of the cell's WIS(L3)); total_pct -->
| Comparison | Total, % | Weeks with cases, % (95% CI) | Zeros listed by the source, % (95% CI) | Zero-filled weeks, % (95% CI) |
|---|---|---|---|---|
| Brazil, future years | +0.23 | +0.46 (−0.16 to 1.07) | −0.02 (−0.16 to 0.12) | −0.20 (−0.33 to −0.08) |
| Brazil, held-out states | 0.00 | +0.14 (−0.27 to 0.54) | +0.05 (−0.07 to 0.16) | −0.18 (−0.30 to −0.06) |
| Brazil, held-out regions | −0.16 | +0.22 (−0.02 to 0.47) | −0.03 (−0.17 to 0.11) | −0.35 (−0.52 to −0.18) |
| Brazil, held-out districts | +0.20 | +0.40 (−0.16 to 0.96) | 0.00 (−0.12 to 0.12) | −0.20 (−0.34 to −0.07) |
| Brazil, held-out country | −0.68 | +0.16 (−0.08 to 0.40) | −0.16 (−0.44 to 0.11) | −0.68 (−0.88 to −0.48) |
| Colombia, future years | −0.42 | +0.18 (−0.19 to 0.56) | – | −0.60 (−0.99 to −0.21) |
| Colombia, held-out states | −0.52 | +0.16 (−0.23 to 0.55) | – | −0.68 (−1.05 to −0.32) |
| Colombia, held-out regions | −0.68 | +0.07 (−0.20 to 0.35) | – | −0.76 (−1.21 to −0.30) |
| Colombia, held-out districts | −0.45 | +0.22 (−0.20 to 0.64) | – | −0.66 (−1.10 to −0.23) |
| Colombia, held-out country | +0.22 | +0.27 (0.06 to 0.49) | – | −0.05 (−0.51 to 0.41) |
| Peru, future years | −0.82 | −0.14 (−0.89 to 0.61) | – | −0.67 (−0.92 to −0.43) |
| Peru, held-out country | +0.93 | +1.20 (0.11 to 2.29) | – | −0.27 (−0.42 to −0.13) |
| Taiwan, future years (with 2021) | −0.71 | −0.24 (−0.73 to 0.25) | – | −0.47 (−1.12 to 0.18) |
| Taiwan, held-out country (with 2021) | −18.29 | +1.33 (−1.01 to 3.67) | – | −19.62 (−30.92 to −8.32) |
| Brazil, future years, per-level tuning, 31 leaves (sensitivity) | +0.25 | +0.27 (−0.04 to 0.59) | +0.01 (−0.08 to 0.11) | −0.03 (−0.09 to 0.02) |
| Taiwan, future years, without 2021 | −0.44 | −0.07 (−0.35 to 0.20) | – | −0.36 (−1.04 to 0.31) |
| Taiwan, held-out country, without 2021 | −11.16 | +1.33 (−1.12 to 3.77) | – | −12.48 (−16.99 to −7.97) |
| Brazil, future years, without case history (N3 + C2 vs N4 + C2) | −0.43 | +0.77 (−1.27 to 2.80) | −0.29 (−0.78 to 0.20) | −0.91 (−1.46 to −0.35) |
| Brazil, held-out states, without case history (N3 + C2 vs N4 + C2) | −0.01 | +0.99 (−0.54 to 2.51) | −0.27 (−0.72 to 0.18) | −0.73 (−1.17 to −0.29) |

Note: Each contribution is a percentage of the comparison's reference WIS, and the three contributions add up exactly to the total. Zeros listed by the source are zero weeks that the source itself reports (Brazil 2020 to 2021 test years only); zero-filled weeks are weeks missing from the source and set to zero. A dash means that the comparison has no rows of this type. The extra rows are Brazil, future years, with each model tuned separately (31 leaves); Taiwan without 2021; and Brazil, future years and held-out states, without case history. The rows without case history compare N4 + C2 with N3 + C2, as percentages of the WIS of N3. Estimates average seeds 0 to 2 where three seeds exist, as in Table 2.

**Table S29. Excess gain within each type of target week.**

<!-- src: T5_strata.csv, estimand = G_excess, per cell and stratum: row_share; pct_of_ref, lo95_pct, hi95_pct (stratum estimate, % of the stratum's own WIS(L3)); contrib_pct, contrib_lo95_pct, contrib_hi95_pct, contrib_p (additive contribution, % of the cell's WIS(L3)); total_pct -->
| Comparison | Cases > 0: share | Cases > 0: % (95% CI) | Zeros listed by the source: share | Zeros listed by the source: % (95% CI) | Zero-filled: share | Zero-filled: % (95% CI) |
|---|---|---|---|---|---|---|
| Brazil, future years | 27% | +0.30 (−0.16 to 0.76) | 21% | −0.27 (−2.74 to 2.20) | 52% | −1.67 (−2.65 to −0.69) |
| Brazil, held-out states | 27% | 0.00 (−0.42 to 0.42) | 21% | +0.72 (−1.33 to 2.78) | 52% | −1.48 (−2.58 to −0.38) |
| Brazil, held-out regions | 27% | +0.28 (−0.01 to 0.58) | 21% | −0.34 (−2.71 to 2.03) | 52% | −2.75 (−4.39 to −1.11) |
| Brazil, held-out districts | 27% | +0.27 (−0.18 to 0.72) | 21% | +0.07 (−2.14 to 2.29) | 52% | −1.59 (−2.65 to −0.54) |
| Brazil, held-out country | 27% | +0.44 (0.03 to 0.85) | 21% | −1.89 (−5.43 to 1.64) | 52% | −5.18 (−6.39 to −3.97) |
| Colombia, future years | 21% | +0.24 (−0.31 to 0.79) | – | – | 79% | −2.17 (−3.52 to −0.81) |
| Colombia, held-out states | 21% | +0.19 (−0.40 to 0.77) | – | – | 79% | −2.45 (−3.73 to −1.16) |
| Colombia, held-out regions | 21% | +0.09 (−0.33 to 0.52) | – | – | 79% | −2.55 (−4.06 to −1.03) |
| Colombia, held-out districts | 21% | +0.26 (−0.37 to 0.89) | – | – | 79% | −2.40 (−3.92 to −0.89) |
| Colombia, held-out country | 21% | +0.37 (0.07 to 0.66) | – | – | 79% | −0.13 (−2.25 to 1.98) |
| Peru, future years | 44% | −0.27 (−1.11 to 0.57) | – | – | 56% | −5.64 (−8.10 to −3.19) |
| Peru, held-out country | 44% | +1.52 (0.14 to 2.90) | – | – | 56% | −2.69 (−4.31 to −1.08) |
| Taiwan, future years (with 2021) | 2% | −0.10 (−1.15 to 0.95) | – | – | 98% | −8.59 (−20.34 to 3.16) |
| Taiwan, held-out country (with 2021) | 2% | +2.41 (0.56 to 4.26) | – | – | 98% | −51.00 (−79.68 to −22.33) |
| Brazil, future years, per-level tuning, 31 leaves (sensitivity) | 27% | +0.22 (−0.03 to 0.46) | 21% | +0.30 (−1.54 to 2.14) | 52% | −0.06 (−0.65 to 0.54) |
| Taiwan, future years, without 2021 | 3% | −0.15 (−1.21 to 0.91) | – | – | 97% | −6.74 (−19.50 to 6.02) |
| Taiwan, held-out country, without 2021 | 3% | +2.16 (0.27 to 4.04) | – | – | 97% | −35.22 (−48.16 to −22.27) |
| Brazil, future years, without case history (N3 + C2 vs N4 + C2) | 27% | +0.58 (−1.16 to 2.31) | 21% | −6.09 (−17.44 to 5.25) | 52% | −15.77 (−24.77 to −6.76) |
| Brazil, held-out states, without case history (N3 + C2 vs N4 + C2) | 27% | +1.04 (−0.24 to 2.32) | 21% | −5.38 (−14.67 to 3.91) | 52% | −11.40 (−17.98 to −4.81) |

Note: Share is the share of rows. Each estimate is a percentage of that stratum's own reference WIS, with weeks weighted equally; these estimates are not shares of the total (Table S28). Rows as in Table S28. All strata are defined by the outcome and are descriptive. With Brazil held out, the estimate in the stratum of zeros listed by the source was −1.89% (95% CI −5.43 to 1.64). The additive contribution of the same rows to the total was −0.16 (Table S28; −0.44 to 0.11). Both 95% CIs include zero, and all zeros listed by the source fall in 2020 to 2021. <!-- src: T5_strata.csv BR_S5 recorded_zero pct_of_ref, lo95_pct, hi95_pct; contrib_pct, contrib_lo95_pct, contrib_hi95_pct -->

**Table S30. Excess gain by test year.**

<!-- src: S8_per_year.csv, estimand = G_excess, per cell and test_year: pct_of_ref, lo95_pct, hi95_pct, p (* = p < 0.05, unadjusted); estimate (absolute, shown ×10^-4 in brackets) for Taiwan -->
| Comparison | 2020 | 2021 | 2022 | 2023 | 2024 |
|---|---|---|---|---|---|
| Brazil, future years | −0.22 | −0.67* | +0.12 | +0.42 | +0.88 |
| Brazil, held-out states | −0.38 | −0.77* | −0.07* | +0.32 | +0.41 |
| Brazil, held-out regions | −0.19* | −0.97* | −0.05 | +0.05 | +0.02 |
| Brazil, held-out districts | −0.15 | −0.66* | +0.07 | +0.37 | +0.78 |
| Brazil, held-out country | −0.17 | −1.94* | −0.68* | −0.67* | −0.46* |
| Colombia, future years | −0.65* | −0.36 | −0.21 | – | – |
| Colombia, held-out states | −0.62* | −0.64 | −0.31* | – | – |
| Colombia, held-out regions | −0.64 | −0.87* | −0.59* | – | – |
| Colombia, held-out districts | −0.69* | −0.42 | −0.18 | – | – |
| Colombia, held-out country | +0.80* | −0.31 | −0.02 | – | – |
| Peru, future years | −1.50 | −1.35 | −0.58 | −0.09 | – |
| Peru, held-out country | +1.31 | +1.40 | +1.11 | +0.16 | – |
| Taiwan, future years | −13.76 (−3.4) | −65.39 (−2.0) | +2.76 (+0.2) | −0.28 (−4.0) | −2.57 (−1.9) |
| Taiwan, held-out country | −38.01* (−31.8) | −209.94 (−80.4) | −88.10* (−29.5) | −1.50 (−11.0) | −26.83* (−31.8) |

Note: Percentage of that year's reference WIS. An asterisk marks unadjusted p < 0.05; CIs are in the source file. For Taiwan the absolute excess gain (× 10⁻⁴ log-WIS) is given in parentheses, because the reference WIS is close to zero outside the 2023 outbreak and the percentages are unstable (2021 had no local cases). Context: 2020 to 2021, COVID-19 pandemic; Peru 2023, record season; Taiwan 2023, outbreak; Brazil 2024, record epidemic.

In all five Brazilian comparisons the excess gain was lowest in 2021, a year of the COVID-19 pandemic (−0.66% to −1.94%; each unadjusted p < 0.05) [@chen2022covid; @roster2024covidbrazil]. In the four within-Brazil comparisons it was highest in 2023 or 2024. The largest yearly estimate in Brazil was in the future-years comparison in 2024, the year of Brazil's largest recorded epidemic (+0.88%, 95% CI −0.93 to 2.69) [@gurgelgoncalves2024brazil]. Colombia's four within-country comparisons were negative in every year. Peru (future years) was negative in every year and closest to zero in its 2023 record season (−0.09%) [@munayco2024peru]. Taiwan's yearly percentages are unstable because its reference WIS is near zero outside the 2023 outbreak. In 2023 the excess gain was −0.28% for future years and −1.50% with Taiwan held out. <!-- src: S8_per_year.csv G_excess pct_of_ref, lo95_pct, hi95_pct, p, context -->

**Table S31. Upper quantiles of the forecasts on rows with zero cases.**

<!-- src: S6_q90_mechanism.csv per cell: zero_row_share; dq90_log, dq90_log_lo95, dq90_log_hi95, dq90_log_p; dq90_case, dq90_case_lo95, dq90_case_hi95; G_zero_contrib, G_zero_contrib_lo95, G_zero_contrib_hi95 (×10^4); upper_share_of_zero; q90_share_of_zero -->
| Comparison | Zero-case share of rows | Δq0.9, log(1 + cases) (95% CI); p | Δq0.9, cases (95% CI) | Zero-row contribution, log-WIS × 10⁻⁴ (95% CI) | Share from quantiles above the median | Share from q0.9 alone |
|---|---|---|---|---|---|---|
| Brazil, future years | 73% | +0.006 (0.001 to 0.011); 0.029 | +0.003 (−0.008 to 0.014) | −3.8 (−7.3 to −0.2) | 0.77 | 0.24 |
| Brazil, held-out states | 73% | +0.009 (0.004 to 0.015); 0.0013 | +0.001 (−0.007 to 0.009) | −2.3 (−5.5 to 0.9) | 1.27 | 0.63 |
| Brazil, held-out regions | 73% | +0.027 (0.019 to 0.035); <0.001 | +0.031 (0.020 to 0.042) | −6.5 (−10.6 to −2.3) | 1.19 | 0.65 |
| Brazil, held-out districts | 73% | +0.009 (0.004 to 0.015); 0.0011 | +0.009 (−0.0004 to 0.019) | −3.4 (−6.8 to −0.02) | 1.00 | 0.43 |
| Brazil, held-out country | 73% | +0.042 (0.027 to 0.056); <0.001 | +0.045 (0.011 to 0.078) | −16.1 (−22.8 to −9.4) | 0.99 | 0.45 |
| Colombia, future years | 79% | +0.017 (0.010 to 0.025); <0.001 | +0.020 (0.004 to 0.036) | −7.4 (−12.1 to −2.6) | 0.97 | 0.40 |
| Colombia, held-out states | 79% | +0.019 (0.013 to 0.026); <0.001 | +0.018 (0.004 to 0.032) | −8.4 (−12.9 to −3.9) | 1.04 | 0.40 |
| Colombia, held-out regions | 79% | +0.025 (0.018 to 0.032); <0.001 | +0.017 (−0.002 to 0.036) | −9.4 (−15.1 to −3.8) | 1.11 | 0.47 |
| Colombia, held-out districts | 79% | +0.017 (0.010 to 0.025); <0.001 | +0.018 (0.003 to 0.033) | −8.1 (−13.4 to −2.8) | 1.06 | 0.36 |
| Colombia, held-out country | 79% | +0.007 (0.0004 to 0.014); 0.041 | +0.007 (−0.009 to 0.022) | −0.7 (−6.4 to 5.0) | 2.94 | 1.98 |
| Peru, future years | 56% | +0.036 (0.019 to 0.053); <0.001 | +0.054 (0.026 to 0.081) | −16.3 (−22.2 to −10.4) | 0.78 | 0.25 |
| Peru, held-out country | 56% | +0.017 (0.011 to 0.023); <0.001 | +0.035 (0.018 to 0.052) | −6.4 (−9.8 to −3.0) | 0.63 | 0.34 |
| Taiwan, future years | 98% | +0.002 (−0.002 to 0.005); 0.33 | +0.001 (−0.004 to 0.006) | −1.5 (−3.5 to 0.6) | 1.14 | 0.26 |
| Taiwan, held-out country | 98% | +0.093 (0.061 to 0.125); <0.001 | +0.132 (0.082 to 0.181) | −39.6 (−62.3 to −16.8) | 0.95 | 0.51 |

Note: Δq0.9 is the mean 0.9 quantile of L4 + C\* minus that of L3 + C\* on rows with zero cases, on the log(1 + cases) scale and on the case scale, with a 95% CI from the weekly series. The zero-row contribution is the additive contribution of all zero-case rows (recorded and filled) to the absolute excess gain. The last two columns give the share of that contribution from the quantile levels above the median (0.6 to 0.9) and from the 0.9 quantile alone; values above 1 mean that the lower quantiles offset part of the loss. Colombia's held-out-country shares are unstable because its contribution from zero-case rows is close to zero.

### Supporting analyses

The analyses in Tables S32 to S35 are exploratory and not adjusted for multiplicity. Outbreak weeks made up 0.7% to 22.9% of rows. On outbreak weeks, the excess gain had a CI above zero with Peru and Taiwan held out (+3.62% and +1.32%). It had a CI below zero in Brazil's held-out states and held-out regions and in Colombia's held-out regions (Table S32). <!-- src: S3_outbreak.csv outbreak row_share, pct_of_ref, lo95_pct, hi95_pct --> When districts were weighted by population or by past cases, only Colombia held out had a CI above zero (+0.49% with case weights). Colombian losses grew under population weighting, to −1.34% with held-out regions. With Peru held out the gain turned negative under both weightings (Table S33). <!-- src: S4_weighted.csv pct_of_ref, lo95_pct, hi95_pct (CO_S3 population −1.34; PE_S5 −1.37 population, −0.89 case) --> Adjusting the forecast quantiles with earlier test years only (causal recalibration) changed the excess gain by 0.08 percentage points or less in most comparisons. The exceptions were Brazil held out (−0.68% to −0.47% with Mondrian shifts), Peru, future years (−0.82% to −0.61%), Peru held out (+0.93% to 0.00%) and Taiwan held out (−18.29% to −16.71%). Recalibration raised coverage on weeks with cases mainly in Peru (Table S34). <!-- src: S5_recalibration.csv all_years raw vs global/mondrian pct_of_ref; cov80pos_L4+C* --> Some subgroups were computed before the origin-year filter and the Espírito Santo exclusion. In them, no subgroup defined by population, surveillance history or urban growth showed a significant gain, except with Peru held out. Where losses occurred, they were largest in districts with no reported case in 2014 to 2017 (Table S35). <!-- src: docs/results/review/RB_summary.md section 1; RB_strata.csv -->

**Table S32. Excess gain on outbreak and non-outbreak weeks.**

<!-- src: S3_outbreak.csv per cell: stratum outbreak / non_outbreak (row_share, pct_of_ref, lo95_pct, hi95_pct, p, n_weeks) and outbreak_minus_non (p) -->
| Comparison | Outbreak share of rows | Outbreak weeks: % (95% CI); p | Other weeks: % (95% CI); p | Difference, p |
|---|---|---|---|---|
| Brazil, future years | 8.2% | +0.08 (−0.77 to 0.92); 0.85 | +0.01 (−0.19 to 0.20); 0.94 | 0.85 |
| Brazil, held-out states | 8.2% | −0.98 (−1.96 to −0.01); 0.048 | +0.15 (−0.06 to 0.36); 0.16 | 0.041 |
| Brazil, held-out regions | 8.2% | −0.98 (−1.73 to −0.23); 0.013 | +0.13 (−0.19 to 0.44); 0.41 | 0.011 |
| Brazil, held-out districts | 8.2% | +0.01 (−0.83 to 0.86); 0.97 | +0.03 (−0.16 to 0.23); 0.73 | 0.99 |
| Brazil, held-out country | 8.2% | +0.50 (−0.07 to 1.08); 0.081 | −0.81 (−1.18 to −0.45); <0.001 | 0.030 |
| Colombia, future years | 2.3% | −0.70 (−2.33 to 0.94); 0.37 | −0.42 (−0.63 to −0.21); 0.0012 | 0.44 |
| Colombia, held-out states | 2.3% | −1.12 (−2.88 to 0.64); 0.19 | −0.48 (−0.68 to −0.28); <0.001 | 0.23 |
| Colombia, held-out regions | 2.3% | −1.86 (−3.31 to −0.42); 0.016 | −0.54 (−1.02 to −0.07); 0.028 | 0.023 |
| Colombia, held-out districts | 2.3% | −0.96 (−2.80 to 0.88); 0.27 | −0.42 (−0.65 to −0.19); 0.0018 | 0.32 |
| Colombia, held-out country | 2.3% | −0.34 (−1.47 to 0.79); 0.52 | +0.30 (−0.17 to 0.77); 0.19 | 0.46 |
| Peru, future years | 22.9% | −1.64 (−3.30 to 0.03); 0.053 | −0.69 (−1.23 to −0.14); 0.017 | 0.089 |
| Peru, held-out country | 22.9% | +3.62 (1.36 to 5.89); 0.0043 | −0.96 (−1.57 to −0.36); 0.0045 | 0.0017 |
| Taiwan, future years | 0.7% | −0.46 (−1.16 to 0.24); 0.14 | −1.05 (−2.25 to 0.16); 0.084 | 0.15 |
| Taiwan, held-out country | 0.7% | +1.32 (0.21 to 2.44); 0.030 | −22.45 (−36.24 to −8.67); 0.0033 | 0.024 |

Note: An outbreak week has cases at least max(5, the district's 90th percentile of weekly cases over 2013 to 2019); this window includes the training years 2018 to 2019 but no test year. Each estimate is a percentage of that stratum's own reference WIS. The last column tests the weekly series of the difference between outbreak and non-outbreak weeks.

**Table S33. Excess gain weighted by population or by past cases.**

<!-- src: S4_weighted.csv, estimand G_excess, per cell and weights (unweighted, population, pre_cases_plus1): pct_of_ref, lo95_pct, hi95_pct, p -->
| Comparison | Unweighted: % (95% CI); p | Population-weighted: % (95% CI); p | Weighted by 2013 to 2017 mean weekly cases + 1: % (95% CI); p |
|---|---|---|---|
| Brazil, future years | +0.23 (−0.33 to 0.79); 0.39 | +0.03 (−0.40 to 0.46); 0.88 | −0.13 (−0.53 to 0.27); 0.51 |
| Brazil, held-out states | 0.00 (−0.34 to 0.34); 1.0 | −0.15 (−0.53 to 0.22); 0.40 | −0.21 (−0.64 to 0.22); 0.32 |
| Brazil, held-out regions | −0.16 (−0.34 to 0.03); 0.090 | −0.42 (−0.90 to 0.07); 0.086 | −0.58 (−0.99 to −0.16); 0.010 |
| Brazil, held-out districts | +0.20 (−0.32 to 0.71); 0.43 | −0.16 (−0.58 to 0.25); 0.42 | −0.11 (−0.51 to 0.28); 0.55 |
| Brazil, held-out country | −0.68 (−0.94 to −0.42); <0.001 | −0.68 (−1.18 to −0.18); 0.011 | −0.65 (−1.15 to −0.14); 0.015 |
| Colombia, future years | −0.42 (−0.64 to −0.21); 0.0012 | −1.02 (−1.52 to −0.52); <0.001 | −0.72 (−1.14 to −0.30); 0.0032 |
| Colombia, held-out states | −0.52 (−0.74 to −0.30); <0.001 | −0.68 (−1.34 to −0.02); 0.043 | −0.52 (−1.04 to −0.001); 0.050 |
| Colombia, held-out regions | −0.68 (−1.08 to −0.29); 0.0030 | −1.34 (−2.20 to −0.48); 0.0056 | −0.48 (−0.90 to −0.06); 0.028 |
| Colombia, held-out districts | −0.45 (−0.68 to −0.21); 0.0017 | −0.86 (−1.59 to −0.13); 0.025 | −0.75 (−1.46 to −0.03); 0.042 |
| Colombia, held-out country | +0.22 (−0.19 to 0.63); 0.27 | +0.51 (−0.02 to 1.04); 0.058 | +0.49 (0.07 to 0.92); 0.026 |
| Peru, future years | −0.82 (−1.49 to −0.14); 0.022 | −1.41 (−3.50 to 0.69); 0.17 | −4.19 (−6.83 to −1.55); 0.0045 |
| Peru, held-out country | +0.93 (−0.16 to 2.02); 0.088 | −1.37 (−3.32 to 0.58); 0.15 | −0.89 (−2.36 to 0.59); 0.22 |
| Taiwan, future years | −0.71 (−1.40 to −0.03); 0.042 | −0.92 (−1.80 to −0.03); 0.044 | −1.07 (−1.98 to −0.16); 0.025 |
| Taiwan, held-out country | −18.29 (−29.80 to −6.78); 0.0039 | −15.19 (−25.04 to −5.34); 0.0048 | −9.43 (−15.65 to −3.21); 0.0054 |

Note: Within each horizon and week, rows are weighted by the district's population in the target year, or by its mean weekly cases in 2013 to 2017 plus 1. Weeks are then averaged as in the primary estimator.

**Table S34. Excess gain after causal recalibration of the quantiles.**

<!-- src: S5_recalibration.csv per cell, years and calibration: pct_of_ref, p; cov80pos_L4+C* -->
| Comparison | Raw: %; p | Global shift: %; p | Mondrian shift: %; p | Mondrian, from second test year: %; p | 80% coverage of L4 + C\*, cases > 0: raw → Mondrian |
|---|---|---|---|---|---|
| Brazil, future years | +0.23; 0.39 | +0.23; 0.39 | +0.24; 0.36 | +0.33; 0.29 | 0.66 → 0.69 |
| Brazil, held-out states | 0.00; 1.0 | 0.00; 1.0 | +0.06; 0.76 | +0.15; 0.51 | 0.66 → 0.69 |
| Brazil, held-out regions | −0.16; 0.090 | −0.16; 0.090 | −0.08; 0.51 | −0.06; 0.69 | 0.66 → 0.69 |
| Brazil, held-out districts | +0.20; 0.43 | +0.20; 0.43 | +0.22; 0.39 | +0.29; 0.33 | 0.66 → 0.69 |
| Brazil, held-out country | −0.68; <0.001 | −0.60; <0.001 | −0.47; <0.001 | −0.53; <0.001 | 0.64 → 0.67 |
| Colombia, future years | −0.42; 0.0012 | −0.42; 0.0012 | −0.43; 0.0056 | −0.29; 0.11 | 0.71 → 0.70 |
| Colombia, held-out states | −0.52; <0.001 | −0.52; <0.001 | −0.53; 0.0018 | −0.47; 0.032 | 0.70 → 0.70 |
| Colombia, held-out regions | −0.68; 0.0030 | −0.68; 0.0031 | −0.64; 0.0037 | −0.64; 0.0026 | 0.70 → 0.70 |
| Colombia, held-out districts | −0.45; 0.0017 | −0.45; 0.0017 | −0.46; 0.0070 | −0.32; 0.12 | 0.71 → 0.70 |
| Colombia, held-out country | +0.22; 0.27 | +0.22; 0.27 | +0.25; 0.20 | −0.10; 0.26 | 0.75 → 0.73 |
| Peru, future years | −0.82; 0.022 | −0.79; 0.021 | −0.61; 0.12 | −0.33; 0.45 | 0.67 → 0.76 |
| Peru, held-out country | +0.93; 0.088 | +0.76; 0.16 | 0.00; 0.99 | −0.36; 0.35 | 0.67 → 0.76 |
| Taiwan, future years | −0.71; 0.042 | −0.71; 0.042 | −0.71; 0.042 | −0.50; 0.13 | 0.23 → 0.23 |
| Taiwan, held-out country | −18.29; 0.0039 | −16.74; 0.0052 | −16.71; 0.0052 | −14.76; 0.019 | 0.61 → 0.59 |

Note: Separately for L3 + C\* and L4 + C\*, and per horizon and seed, additive shifts of each quantile on the log(1 + cases) scale are fitted only on earlier test years. A global shift uses one shift per quantile; a Mondrian shift uses one shift per group of forecasts with a similar median. The first test year has no earlier year and is left unadjusted in the first three result columns; the fourth drops it.

**Table S35. Excess gain by surveillance history and population (exploratory; earlier scoring).**

<!-- src: docs/results/review/RB_strata.csv, estimand = G_excess, dimension history (0, 1-2, 3-4) and pop_tercile (T1-T3): pct_of_own_ref, p, n_units (pre-review scoring: all rows, exclusions v1, Taiwan without 2021) -->
| Comparison | No case 2014 to 2017 | Cases in 1 to 2 years | Cases in 3 to 4 years | Population, lowest third | Middle third | Highest third |
|---|---|---|---|---|---|---|
| Brazil, future years | +0.55 (n = 507) | +0.58 | +0.21 | +0.27 | +0.33 | +0.21 |
| Brazil, held-out states | +0.04 (n = 507) | +0.15 | 0.00 | +0.02 | +0.05 | −0.01 |
| Brazil, held-out regions | −1.76* (n = 507) | −0.45* | −0.03 | −0.17 | −0.08 | −0.14 |
| Brazil, held-out country | −2.47* (n = 507) | −1.29* | −0.47* | −0.77* | −0.61* | −0.58* |
| Colombia, future years | −1.14* (n = 65) | −0.66* | −0.38* | −0.82* | −0.42* | −0.28* |
| Colombia, held-out states | −19.74* (n = 65) | −2.74* | −0.39* | −1.27* | −0.52* | −0.27 |
| Colombia, held-out regions | −40.70* (n = 65) | −5.52* | −0.49* | −2.36* | −0.84* | −0.21 |
| Colombia, held-out districts | −7.14* (n = 65) | −2.31* | −0.38* | −1.19* | −0.50* | −0.24 |
| Colombia, held-out country | −11.63* (n = 65) | −0.81 | +0.22 | −0.63* | +0.15 | +0.39 |
| Peru, future years | −0.31 (n = 34) | +0.50 | −0.81* | 0.00 | −0.49 | −1.13* |
| Peru, held-out country | −0.75 (n = 34) | −0.35 | +1.35* | +0.75 | +2.18* | −0.09 |
| Taiwan, future years | −0.50 (n = 42) | −0.56 | −0.24 | +0.12 | −0.09 | −0.66 |
| Taiwan, held-out country | −28.83* (n = 42) | −13.79* | −5.88* | −16.71* | −11.99* | −9.66* |

Note: Excess gain as a percentage of the stratum's own reference WIS; an asterisk marks unadjusted p < 0.05; n is the number of districts with no reported case in 2014 to 2017. History is the number of years in 2014 to 2017 with at least one reported case. Population thirds are formed within each comparison and test year from the population in the year before the test year. These strata were computed before the changes made after review and were not recomputed. They use all rows without the origin-year filter, the earlier exclusions with Espírito Santo included, and Taiwan without 2021, so they differ slightly from the primary estimates. Brazil's held-out-districts comparison had not been run when they were computed and is not shown. Thirds of urban growth (change in built-up share, 2010 to 2015) are in the source file and show no consistent pattern.

## E. Location controls, sensitivity analyses and transfer to Taiwan

**Table S36. Control and excess gains with each fixed location control in the future-years split.**

<!-- src: Taiwan rows from docs/results/review/R3_C_tw2021_panel.csv (G_id_pct, G_id_pct_lo95, G_id_pct_hi95, G_id_p, G_excess_pct, G_excess_pct_lo95, G_excess_pct_hi95, G_excess_p, G_emb_pct, G_emb_p); other rows S2_control_panel.csv per country and control: G_id_pct, G_id_pct_lo95, G_id_pct_hi95, G_id_p; G_excess_pct, G_excess_pct_lo95, G_excess_pct_hi95, G_excess_p; G_emb_pct, G_emb_pct_lo95, G_emb_pct_hi95, G_emb_p; status -->
| Country | Control | Control gain with this control, % (95% CI); p | Excess gain with this control, % (95% CI); p |
|---|---|---|---|
| Brazil | C1 | +0.02 (−0.15 to 0.20); 0.77 | +0.25 (−0.32 to 0.81); 0.37 |
| Brazil | C2 | +0.14 (−0.16 to 0.43); 0.34 | +0.02 (−0.25 to 0.29); 0.88 |
| Brazil | C3 | −0.04 (−0.08 to −0.003); 0.038 | +0.28 (−0.27 to 0.82); 0.30 |
| Brazil | C6 | −2.11 (−2.68 to −1.54); <0.001 | +0.30 (−0.12 to 0.71); 0.15 |
| Colombia | C1 | −0.07 (−0.34 to 0.20); 0.60 | −0.39 (−0.58 to −0.19); 0.0011 |
| Colombia | C2 | −0.12 (−0.21 to −0.03); 0.016 | −0.34 (−0.59 to −0.10); 0.010 |
| Colombia | C3 | −0.12 (−0.20 to −0.04); 0.0053 | −0.33 (−0.49 to −0.16); 0.0011 |
| Colombia | C6 | −2.37 (−2.80 to −1.94); <0.001 | −0.13 (−0.37 to 0.12); 0.27 |
| Peru | C1 | −0.26 (−1.05 to 0.53); 0.49 | −0.70 (−1.41 to 0.02); 0.056 |
| Peru | C2 | −0.31 (−0.73 to 0.11); 0.13 | −0.86 (−1.57 to −0.14); 0.022 |
| Peru | C3 | −0.76 (−1.48 to −0.04); 0.040 | −0.37 (−0.80 to 0.05); 0.081 |
| Peru | C6 | −6.28 (−9.87 to −2.69); 0.0023 | −0.29 (−1.53 to 0.96); 0.63 |
| Taiwan | C1 | −0.63 (−1.68 to 0.43); 0.22 | −0.60 (−1.20 to −0.003); 0.049 |
| Taiwan | C2 | −0.36 (−0.76 to 0.03); 0.070 | −0.94 (−2.03 to 0.15); 0.087 |
| Taiwan | C3 | −0.58 (−1.29 to 0.12); 0.097 | −0.68 (−1.45 to 0.09); 0.079 |
| Taiwan | C6 | −2.29 (−5.59 to 1.02); 0.16 | −0.52 (−1.16 to 0.13); 0.11 |
| Brazil | none (embedding gain, L3 vs L4) | – | +0.29 (−0.27 to 0.84); 0.29 |
| Colombia | none (embedding gain, L3 vs L4) | – | −0.36 (−0.58 to −0.13); 0.0052 |
| Peru | none (embedding gain, L3 vs L4) | – | −0.94 (−1.70 to −0.18); 0.020 |
| Taiwan | none (embedding gain, L3 vs L4) | – | −1.06 (−1.96 to −0.16); 0.024 |

Note: Each row replaces the selected control by one fixed control. C1 is average past cases, the district's mean log(1 + cases) in the years before 2018. C2 is coordinates with spherical harmonics. C3 is the AlphaEarth series of a fixed other district. C6 is a district label, entered as a categorical input. The control gain compares L3 with L3 + Ck, and the excess gain compares L3 + Ck with L4 + Ck. The last four rows give the embedding gain without a control. Seed 0 only, so the C1 rows differ slightly from the three-seed values in Table 2. The panel is scored on the same primary rows as Table 2. Taiwan includes 2021, giving 141,645 rows; the values without 2021 are in Table S53. No adjustment for multiplicity. <!-- src: S2_control_panel.csv scoring = v3_excl_v2_origin_year; RE_summary.md caveats -->

None of the fixed controls turned the embeddings into a gain, and none of the 16 excess-gain CIs lies above zero. In Brazil the excess gain was positive with every control (+0.02% to +0.30%) but never significant. With coordinates (C2) almost none of it remained (+0.02%). The district label (C6) made the reference model worse in every country. Its control gain was −2.11% in Brazil, −2.37% in Colombia, −6.28% in Peru and −2.29% in Taiwan, the last not significant. <!-- src: S2_control_panel.csv G_excess_pct, G_excess_pct_lo95, G_id_pct, G_id_p; docs/results/review/RE_summary.md -->

**Table S37. Sensitivity analyses of the embedding, control and excess gains.**

<!-- src: T6a_sensitivities.csv per variant and estimand: variant_pct, variant_lo95_pct, variant_hi95_pct, variant_p, variant_status; primary_pct; variant_years -->
| Variant | Gain | Variant: % (95% CI); p | Primary comparison, % |
|---|---|---|---|
| Brazil, future years, yearly inputs keyed to the origin year (strictly causal) | embedding | +0.26 (−0.29 to 0.82); 0.33 | +0.26 (seed 0: +0.29) |
| Brazil, future years, 2-week reporting delay | embedding | +0.60 (−0.56 to 1.76); 0.29 | +0.26 (seed 0: +0.29) |
| Brazil, future years, C3 in place of C\* | embedding | +0.26 (−0.31 to 0.82); 0.35 | +0.26 |
| Brazil, future years, C3 in place of C\* | control | −0.04 (−0.08 to −0.003); 0.038 | +0.03 (seed 0: +0.02) |
| Brazil, future years, C3 in place of C\* | excess | +0.28 (−0.27 to 0.82); 0.30 | +0.23 (seed 0: +0.25) |
| Brazil, future years, C6 in place of C\* | embedding | +0.26 (−0.31 to 0.82); 0.35 | +0.26 |
| Brazil, future years, C6 in place of C\* | control | −2.11 (−2.68 to −1.54); <0.001 | +0.03 (seed 0: +0.02) |
| Brazil, future years, C6 in place of C\* | excess | +0.30 (−0.12 to 0.71); 0.15 | +0.23 (seed 0: +0.25) |
| Brazil, future years, per-level tuning (31 leaves; original protocol) | embedding | +0.21 (−0.05 to 0.47); 0.10 | +0.26 |
| Brazil, future years, per-level tuning (31 leaves; original protocol) | control | −0.06 (−0.30 to 0.18); 0.62 | +0.03 |
| Brazil, future years, per-level tuning (31 leaves; original protocol) | excess | +0.25 (−0.07 to 0.56); 0.11 | +0.23 |
| Taiwan, future years, Brazil's parameters and C\* (no 2021) | embedding | −0.87 (−1.78 to 0.03); 0.057 | −0.95 |
| Taiwan, future years, Brazil's parameters and C\* (no 2021) | control | −0.71 (−1.67 to 0.26); 0.14 | −0.41 |
| Taiwan, future years, Brazil's parameters and C\* (no 2021) | excess | −0.33 (−0.89 to 0.23); 0.22 | −0.71 |
| Taiwan, future years without 2021 | embedding | −0.94 (−1.85 to −0.03); 0.043 | −0.95 |
| Taiwan, future years without 2021 | control | −0.63 (−1.69 to 0.44); 0.23 | −0.41 |
| Taiwan, future years without 2021 | excess | −0.44 (−1.01 to 0.14); 0.12 | −0.71 |
| Taiwan, held-out country without 2021 | embedding | −14.68 (−20.24 to −9.11); <0.001 | −21.60 |
| Taiwan, held-out country without 2021 | control | −2.31 (−5.52 to 0.90); 0.14 | −3.36 |
| Taiwan, held-out country without 2021 | excess | −11.16 (−15.66 to −6.65); <0.001 | −18.29 |
| Brazil, future years, without case history (reference N3; C\* = C2) | embedding | +2.54 (−0.82 to 5.89); 0.13 | +0.26 |
| Brazil, future years, without case history (reference N3; C\* = C2) | control | +3.30 (1.68 to 4.93); <0.001 | +0.03 |
| Brazil, future years, without case history (reference N3; C\* = C2) | excess | −0.43 (−2.06 to 1.19); 0.58 | +0.23 |
| Brazil, held-out states, without case history (reference N3; C\* = C2) | embedding | +1.52 (−1.27 to 4.32); 0.27 | −0.02 |
| Brazil, held-out states, without case history (reference N3; C\* = C2) | control | +0.88 (−0.48 to 2.23); 0.19 | −0.05 |
| Brazil, held-out states, without case history (reference N3; C\* = C2) | excess | −0.01 (−1.28 to 1.27); 0.99 | 0.00 |

Note: The last column repeats the matching primary comparison. Per-level tuning: L3 and L4 tuned separately on the 2019 grid, giving 31 leaves as in the original protocol, with the earlier control selection. Taiwan, future years, with Brazil's configuration and selected control excludes 2021. Taiwan without 2021 is the set of test years used before review. The runs with strictly causal yearly inputs and with a two-week reporting delay refit L3 and L4 only, so they estimate only the embedding gain. Because they use seed 0, they are compared with the seed-0 embedding gain of Brazil, future years, +0.29% (95% CI −0.27 to 0.84; Table S36), rather than with the three-seed +0.26%. <!-- src: S2_control_panel.csv brazil G_emb_pct, G_emb_pct_lo95, G_emb_pct_hi95 --> Rows without case history use N3 as the reference and coordinates (C2) as the selected control. The C3 and C6 rows replace the selected control by that fixed control (seed 0). Their embedding gain equals the primary one by construction, and their control and excess gains are compared with the seed-0 values given in brackets.

**Table S38. Forecast error in Taiwan's 2021 test year.**

<!-- src: docs/results/review/RG_tw2021.md, table "2021 rows on their own (v3, mean log-WIS, h {1, 4})" -->
| Comparison | L3 | L4 | L3 + C\* | L4 + C\* | Excess gain (absolute) | p |
|---|---|---|---|---|---|---|
| Taiwan, future years | 0.00031 | 0.00050 | 0.00031 | 0.00058 | −0.00026 | 0.077 |
| Taiwan, held-out country | 0.00394 | 0.01171 | 0.00512 | 0.01193 | −0.00665 | 0.091 |

Note: Mean WIS on log(1 + cases) on the 2021 rows, where every target is zero because Taiwan had no local cases in 2021. Seed 0. The last two columns give the absolute excess gain and its unadjusted p value. Percentages are not shown, because the reference WIS is close to zero.

**Table S39. Correlation between a held-out district's gain and its embedding similarity to the training districts.**

<!-- src: S7_embedding_distance.csv, distance = cos_max: spearman_rho, p_naive, n_units per cell and estimand -->
| Comparison | Districts | Spearman ρ, excess gain vs similarity (naive p) | Spearman ρ, embedding gain vs similarity (naive p) |
|---|---|---|---|
| Brazil, held-out states | 5,439 | +0.04 (0.0018) | +0.07 (<0.001) |
| Brazil, held-out regions | 5,439 | +0.12 (<0.001) | +0.07 (<0.001) |
| Brazil, held-out districts | 5,439 | +0.09 (<0.001) | +0.10 (<0.001) |
| Brazil, held-out country | 5,439 | +0.09 (<0.001) | +0.24 (<0.001) |
| Colombia, held-out states | 1,070 | +0.01 (0.70) | −0.01 (0.86) |
| Colombia, held-out regions | 1,070 | −0.04 (0.17) | −0.02 (0.49) |
| Colombia, held-out districts | 1,070 | +0.10 (0.0010) | +0.07 (0.022) |
| Colombia, held-out country | 1,070 | +0.15 (<0.001) | +0.02 (0.50) |
| Peru, held-out country | 115 | +0.52 (<0.001) | +0.48 (<0.001) |
| Taiwan, held-out country | 285 | −0.25 (<0.001) | −0.22 (<0.001) |

Note: Similarity is the cosine similarity between a held-out district's rescaled AlphaEarth vector for year y − 1 and that of the most similar training district. The p values treat districts as independent, which they are not, so they are too small. Exploratory, unadjusted.

**Table S40. Excess gain by similarity quintile in the held-out-country split.**

<!-- src: S7b_embedding_distance_bins.csv, cells BR_S5, CO_S5, PE_S5, TW_S5, per bin: cos_max_lo, cos_max_hi, n_units, zero_share, wis_L3, G_excess, G_excess_lo95, G_excess_hi95 (×10^4), G_excess_share_units_neg -->
| Comparison | Similarity quintile (maximum cosine) | Districts | Reference WIS (L3) | Excess gain, log-WIS × 10⁻⁴ (95% CI) | Districts harmed |
|---|---|---|---|---|---|
| Brazil, held-out country | Q1 (0.43–0.67) | 1088 | 0.1035 | −15.6 (−16.4 to −14.8) | 92% |
| Brazil, held-out country | Q2 (0.67–0.72) | 1088 | 0.1521 | −13.2 (−14.0 to −12.3) | 84% |
| Brazil, held-out country | Q3 (0.72–0.76) | 1087 | 0.1781 | −13.6 (−14.4 to −12.7) | 84% |
| Brazil, held-out country | Q4 (0.76–0.80) | 1088 | 0.2429 | −12.2 (−13.1 to −11.2) | 81% |
| Brazil, held-out country | Q5 (0.80–0.99) | 1088 | 0.2802 | −11.7 (−12.8 to −10.6) | 77% |
| Colombia, held-out country | Q1 (0.53–0.78) | 214 | 0.1015 | −1.6 (−3.6 to 0.5) | 73% |
| Colombia, held-out country | Q2 (0.78–0.81) | 214 | 0.1307 | +1.7 (−0.4 to 3.8) | 58% |
| Colombia, held-out country | Q3 (0.81–0.84) | 214 | 0.1305 | +4.1 (2.1 to 6.1) | 50% |
| Colombia, held-out country | Q4 (0.84–0.86) | 214 | 0.1363 | +6.6 (4.2 to 9.1) | 47% |
| Colombia, held-out country | Q5 (0.86–0.99) | 214 | 0.1201 | +3.4 (1.4 to 5.4) | 57% |
| Peru, held-out country | Q1 (0.62–0.76) | 23 | 0.2211 | −33.1 (−53.0 to −13.2) | 83% |
| Peru, held-out country | Q2 (0.76–0.84) | 23 | 0.2562 | +7.1 (−28.0 to 42.3) | 61% |
| Peru, held-out country | Q3 (0.85–0.88) | 23 | 0.2336 | +38.1 (2.4 to 73.9) | 48% |
| Peru, held-out country | Q4 (0.88–0.92) | 23 | 0.1768 | +36.6 (9.0 to 64.2) | 39% |
| Peru, held-out country | Q5 (0.93–0.99) | 23 | 0.3040 | +64.3 (33.0 to 95.6) | 17% |
| Taiwan, held-out country | Q1 (0.49–0.74) | 57 | 0.0054 | −30.8 (−34.7 to −26.9) | 100% |
| Taiwan, held-out country | Q2 (0.74–0.76) | 57 | 0.0147 | −40.8 (−46.0 to −35.6) | 100% |
| Taiwan, held-out country | Q3 (0.76–0.78) | 57 | 0.0171 | −35.5 (−39.4 to −31.6) | 100% |
| Taiwan, held-out country | Q4 (0.78–0.80) | 57 | 0.0182 | −35.3 (−38.4 to −32.1) | 100% |
| Taiwan, held-out country | Q5 (0.80–0.88) | 57 | 0.0473 | −46.2 (−50.0 to −42.3) | 100% |

Note: Similarity as in Table S39. The excess gain is absolute (log-WIS), and the reference WIS of each quintile is week-weighted. "Districts harmed" is the share of districts with a negative excess gain. For comparison, the quintile means of similarity are 0.95 to 0.99 in Brazil's and 0.93 to 0.98 in Colombia's held-out-states splits. <!-- src: S7b_embedding_distance_bins.csv cos_max_mean BR_S2, CO_S2 --> Exploratory, unadjusted.

With Taiwan held out, the loss did not shrink as similarity rose (−30.8 to −46.2 × 10⁻⁴ log-WIS per quintile), and all 285 districts had a loss. With Peru held out the gain rose with similarity, from −33.1 × 10⁻⁴ log-WIS in the least similar quintile to +64.3 × 10⁻⁴ in the most similar (ρ = +0.52). <!-- src: S7b_embedding_distance_bins.csv TW_S5, PE_S5 G_excess, G_excess_share_units_neg; S7_embedding_distance.csv PE_S5 spearman_rho -->

## F. Forecasts without case history

**Table S41. Forecast error without case history, Brazil, future years and held-out states (row mean).**

<!-- src: T6c_nohist_ladder.csv, cells BR_S1_nohist and BR_S2_nohist, per label and horizon: wis_log, cov_80, cov_80_nonzero; history-arm comparison from T2_ladder.csv BR_S1 `WIS pooled h{1,4}` -->
| Model | Future years: horizon 1 | Future years: horizon 4 | Future years: horizons 1 and 4 | Future years: 80% coverage, all rows / cases > 0 (pooled) | Held-out states: horizons 1 and 4 | Held-out states: 80% coverage, all rows / cases > 0 |
|---|---|---|---|---|---|---|
| N3: season, climate, remote sensing and population | 0.3520 | 0.3533 | 0.3526 | 0.85 / 0.43 | 0.3613 | 0.84 / 0.42 |
| N3 + C1: static history (mean log(1 + cases), 2014 to 2017) | 0.3473 | 0.3483 | 0.3478 | 0.84 / 0.43 | 0.3622 | 0.84 / 0.42 |
| N4: N3 + AlphaEarth | 0.3437 | 0.3437 | 0.3437 | 0.83 / 0.41 | 0.3557 | 0.82 / 0.40 |
| N4 + C1 | 0.3404 | 0.3413 | 0.3409 | 0.83 / 0.41 | 0.3555 | 0.82 / 0.40 |
| N3 + C2: coordinates (C\*) | 0.3404 | 0.3419 | 0.3411 | 0.84 / 0.43 | 0.3582 | 0.82 / 0.42 |
| N4 + C2 | 0.3423 | 0.3429 | 0.3426 | 0.84 / 0.42 | 0.3581 | 0.82 / 0.41 |
| With case history, L3 / L4 (same rows) | 0.1419 / 0.1418 | 0.1959 / 0.1952 | 0.1681 / 0.1677 | 0.90 / 0.67 (L4) | 0.1689 / 0.1690 | 0.90 / 0.66 (L4 + C\*) |

<!-- src: T6c_nohist_ladder.csv BR_S1_nohist N4+C1 wis_log 0.340442 / 0.341331 / 0.340873, cov_80 0.834177, cov_80_nonzero 0.407918; BR_S2_nohist pooled N3 0.36129, N3+C1 0.36219, N4 0.35573, N4+C1 0.35546, N3+C* 0.35821, N4+C* 0.35809; T2_ladder.csv BR_S2 L3 0.1689, L4 0.1690 -->

Note: Mean WIS over rows (lower is better). Seed 0. All 21 case-derived inputs are removed. Static history (C1) is a separate step and not a candidate for the selected control, which is coordinates (C2) in both comparisons. The row with case history gives L3 and L4 on the same rows for reference. For Brazil, future years, it uses three seeds and the coverage of L4; for held-out states it uses seed 0 and the coverage of L4 + C\*.

**Table S42. Embedding, control and excess gains without case history, Brazil, future years and held-out states.**

<!-- src: T6b_nohist_estimands.csv, cells BR_S1_nohist and BR_S2_nohist, per horizon (1, 4, pooled) and estimand: pct_of_ref, lo95_pct, hi95_pct, p, mde_pct, wis_ref -->
| Comparison and horizon | Reference WIS (N3) | Embedding gain, % (95% CI); p | Control gain (C2), % (95% CI); p | Excess gain, % (95% CI); p | Minimum detectable excess gain, % |
|---|---|---|---|---|---|
| Future years, horizon 1 | 0.3520 | +2.35 (−0.83 to 5.53); 0.14 | +3.28 (1.60 to 4.96); <0.001 | −0.53 (−1.99 to 0.94); 0.46 | 2.07 |
| Future years, horizon 4 | 0.3533 | +2.72 (−0.92 to 6.37); 0.13 | +3.22 (1.61 to 4.84); <0.001 | −0.29 (−2.13 to 1.55); 0.74 | 2.59 |
| Future years, horizons 1 and 4 | 0.3520 | +2.54 (−0.82 to 5.89); 0.13 | +3.30 (1.68 to 4.93); <0.001 | −0.43 (−2.06 to 1.19); 0.58 | 2.29 |
| Held-out states, horizon 1 | 0.3607 | +1.36 (−1.36 to 4.07); 0.31 | +0.88 (−0.62 to 2.39); 0.23 | −0.06 (−1.18 to 1.06); 0.91 | 1.58 |
| Held-out states, horizon 4 | 0.3619 | +1.73 (−1.23 to 4.69); 0.23 | +0.82 (−0.34 to 1.97); 0.15 | +0.13 (−1.40 to 1.65); 0.86 | 2.14 |
| Held-out states, horizons 1 and 4 | 0.3606 | +1.52 (−1.27 to 4.32); 0.27 | +0.88 (−0.48 to 2.23); 0.19 | −0.01 (−1.28 to 1.27); 0.99 | 1.80 |

<!-- src: T6b_nohist_estimands.csv BR_S2_nohist rows horizon 1, 4, pooled -->

Note: N3 is L3 and N4 is L4 without the 21 case-derived inputs. The selected control is coordinates (C2) in both comparisons. Gains are percentages of the WIS of N3. Horizon rows give the mean over rows; pooled rows weight target weeks equally, as in the gains. The minimum detectable effect is at 80% power. Seed 0. The identity share, the control gain as a share of the embedding gain, cannot be estimated in either comparison, because the CI of the embedding gain includes zero. Static-history step (C1, pooled horizons): for future years, the gain from N3 to N3 + C1 was +1.38% (95% CI −0.09 to 2.85; p = 0.064) and from N3 + C1 to N4 + C1 +1.95% (−1.77 to 5.66; p = 0.28). For held-out states the same gains were −0.24% (−0.82 to 0.34; p = 0.39) and +1.85% (−1.09 to 4.79; p = 0.20). <!-- src: docs/results/review/FINAL_br_nohist_C1_rung.csv pct_of_ref, lo95_pct, hi95_pct, p -->

In held-out Brazilian states, no estimate without case history was significant. The embedding gain (+1.52%) was of the same order as the gain from coordinates (+0.88%). Beyond coordinates the embeddings added nothing (−0.01%, 95% CI −1.28 to 1.27). The significant gain from coordinates in the future-years comparison (+3.30%) was therefore not detected in states that were not used for fitting. We had pre-specified the pattern that would point to identity: an embedding gain above zero together with an excess gain equivalent to zero. It was not met in either comparison, because neither embedding gain was significant and neither excess gain was equivalent within ±1%. <!-- src: T6b_nohist_estimands.csv BR_S1_nohist, BR_S2_nohist pooled; docs/results/FINAL_RESULTS_BRIEF.md section 4 -->

## G. Post hoc analyses added after the third review

The analyses in this section were specified in response to reviewers' reports. By then 13 of the 14 comparisons of the primary family had been read, but not the result for Brazil's held-out districts. Each analysis was specified before any of it was scored (deviation rows 39 to 53, Supplementary Methods Table S14; specification commit 8001a92). Unless stated otherwise, they reuse the primary scoring: week-weighted, origin-year rows, primary exclusions, horizons 1 and 4. The final run repeated Tables S43 to S48 on all 14 comparisons. It used the primary estimates of Table 2 as reference values, which are the mean of seeds 0 to 2 where three seeds exist (row 53), with Holm adjustment over 14 comparisons. Tables S49 to S51 and S53 to S55 use seed 0. None of these analyses enters the Holm family of Table 2, and all are exploratory. <!-- src: docs/results/FINAL_RESULTS_BRIEF.md section 7 (round3_analyses.py rerun on 14 cells; load check exact vs T1); R3_A2_nocontrol_rule.csv n_cells_holm 14; R3_C_summary.md header (specification commits) -->

### G1. As planned and as reported

**Table S43. Excess gain under the protocol as planned and as reported.**

Each column changes one reporting choice back to its planned or earlier form and keeps the others at their reported values. Entries are the excess gain as % of the reference WIS, followed by p.

<!-- src: R3_A5_planned_vs_reported.csv (G_excess_pct, p per cell and variant; "reported primary" = Table 2, seeds 0–2 where available); seed-0 column from R3_C_seeds.csv rows seed = 0 (pct, p) and R3_A5 "single seed (seed 0)" for Brazil, new years; R3_C_tw2021_panel.csv C3 row (Taiwan rule-v1 C3 with 2021) -->
| Comparison | C\* | Reported (Table 2) | All rows (row 24) | Exclusions v1 (row 34) | B = 4 variance | Seed 0 only (before row 53) | Other planned settings |
|---|---|---|---|---|---|---|---|
| Brazil, future years (S1) | C1 | +0.23; 0.39 | +0.26; 0.39 | +0.23; 0.40 | +0.23; 0.45 | +0.25; 0.37 | Horizons 1 to 4 +0.25; 0.38. Per-level tuning +0.25; 0.11 |
| Brazil, held-out states (S2) | C1 | 0.00; 1.0 | +0.03; 0.89 | −0.01; 0.94 | 0.00; 1.0 | = reported | – |
| Brazil, held-out regions (S3) | C1 | −0.16; 0.090 | −0.10; 0.40 | **−0.19; 0.045** | −0.16; 0.26 | = reported | – |
| Brazil, held-out districts (S4) | C1 | +0.20; 0.43 | +0.23; 0.42 | +0.19; 0.44 | +0.20; 0.47 | = reported | – |
| Brazil, held-out country (S5) | C3 | −0.68; <0.001 | −0.69; <0.001 | −0.70; <0.001 | −0.68; 0.0073 | −0.60; <0.001 | rule v1 (C4): no valid run |
| Colombia, future years (S1) | C1 | −0.42; 0.0012 | −0.42; <0.001 | = reported | −0.42; 0.014 | −0.39; 0.0011 | Horizons 1 to 4 −0.41; 0.0024 |
| Colombia, held-out states (S2) | C1 | −0.52; <0.001 | −0.53; <0.001 | = reported | −0.52; 0.0016 | −0.47; <0.001 | – |
| Colombia, held-out regions (S3) | C1 | −0.68; 0.0030 | −0.71; 0.0025 | = reported | −0.68; 0.0093 | −0.65; 0.0033 | – |
| Colombia, held-out districts (S4) | C1 | −0.45; 0.0017 | −0.45; 0.0011 | = reported | −0.45; 0.015 | −0.43; 0.0028 | – |
| Colombia, held-out country (S5) | C2 | +0.22; 0.27 | +0.18; 0.33 | = reported | +0.22; 0.49 | = reported | rule v1: same control |
| Peru, future years (S1) | C1 | −0.82; 0.022 | −0.73; 0.046 | = reported | −0.82; 0.11 | −0.70; 0.056 | Horizons 1 to 4 −0.69; 0.047. **Per-level tuning +0.65; 0.24** |
| Peru, held-out country (S5) | C3 | +0.93; 0.088 | +0.99; 0.051 | = reported | **+0.93; 0.020** | +0.96; 0.079 | – |
| Taiwan, future years (S1) | C1 | −0.71; 0.042 | −0.66; 0.062 | = reported | −0.71; 0.037 | −0.60; 0.049 | Without 2021 −0.44; 0.12. Horizons 1 to 4 −0.46; 0.14. Per-level tuning −0.14; 0.23. Rule v1 (C3) −0.68; 0.079 |
| Taiwan, held-out country (S5) | C3 | −18.29; 0.0039 | −18.46; 0.0029 | = reported | −18.29; 0.034 | −17.30; 0.0017 | Without 2021 −11.16; <0.001 |

Note: "Reported" is the primary estimate of Table 2, the mean of seeds 0 to 2 where three seeds exist (row 53). The seed-0 column gives the estimate before seed averaging, which is the version the reviewers saw; "= reported" marks comparisons with seed 0 only. Bold marks an entry whose conclusion differs from the reported one at the unadjusted 5% level. The unadjusted Taiwan future-years loss is discussed below. In the exclusions column, "= reported" means the estimate is identical, because the earlier exclusions differ from the primary ones only in Brazil (Espírito Santo). The control chosen by the first selection rule (rule v1) was the same as the one chosen by the final rule (rule v2) wherever it was recorded: Brazil and Peru, future years, and Colombia, held-out country. Those rule-v1 entries are therefore identical to the reported ones. It was not recorded for most held-out-place comparisons. Brazil held out chose C4 under rule v1, and those runs were discarded after the C4 fix (row 18). Taiwan's rule-v1 value with C3 is from the fixed control panel with 2021 (Table S36), seed 0. <!-- src: R3_A5_planned_vs_reported.csv notes ("identical to primary", "same control as rule v2", "rule-v1 choice not recorded", "no valid run (pre-fix C4 runs were invalidated)"); R3_C_tw2021_panel.csv C3 G_excess_pct −0.68, p 0.079 -->

The main conclusions hold under every planned setting. Brazil, future years, stays between +0.23% and +0.26%, and Brazil's held-out districts between +0.19% and +0.23%; neither is significant. Brazil's held-out states stay at zero. The losses with Brazil held out and in Colombia's four splits stay negative with p ≤ 0.015 under every planned setting, including the strict-variance check and seed 0 alone. <!-- src: R3_A5_planned_vs_reported.csv BR_S1, BR_S4, BR_S2 rows; max p among BR_S5/CO_S1–S4 rows 0.0148 (CO_S4 B=4); R3_C_seeds.csv seed-0 p --> The interpretation changes for a few estimates. In Peru, future years, the sign reverses under per-level tuning, from −0.82% to +0.65% (95% CI −0.49 to 1.79). This is the same effect of model size that first appeared in Brazil. <!-- src: R3_A5_planned_vs_reported.csv PE_S1 per-level tuning 0.654, lo −0.486, hi 1.794, p 0.237 --> With Peru held out, the gain becomes significant before adjustment under the strict-variance check (B = 4; +0.93%, 95% CI 0.25 to 1.62; p = 0.020). On all rows it is +0.99% (−0.003 to 1.98; p = 0.051). Neither is significant after Holm adjustment. <!-- src: R3_A5_planned_vs_reported.csv PE_S5 B=4 lo 0.2455 hi 1.6190 p 0.0196; all rows 0.9865 lo −0.0027 hi 1.9758 p 0.0505 --> Brazil's held-out regions show a loss that is significant before adjustment under the earlier exclusions, which keep Espírito Santo's false zeros (−0.19%, 95% CI −0.37 to −0.005; p = 0.045). <!-- src: R3_A5_planned_vs_reported.csv BR_S3 exclusions v1 −0.188, lo −0.371, hi −0.0051, p 0.0446 --> The loss in Taiwan, future years, is significant only before adjustment (p = 0.042) and not after Holm adjustment. It loses even that significance under per-level tuning (−0.14%, p = 0.23), on all rows (p = 0.062), with horizons 1 to 4 (p = 0.14), without 2021 (p = 0.12) and with the rule-v1 control (p = 0.079). It keeps it only under the strict-variance check (B = 4; p = 0.037). <!-- src: R3_A5_planned_vs_reported.csv TW_S1 rows --> Two further changes are covered elsewhere. Including Taiwan's 2021 (row 25) moved the estimate with Taiwan held out from −11.16% to −18.29%. The rule that allows "no control" removes the loss with Brazil held out (Table S45).

### G2. Gains from known predictors along the ladder, as a scale for the margin

**Table S44. Gains from adding climate, remote sensing and population, and both, compared with the embedding gain, in the future-years split.**

<!-- src: R3_A1_positive_control.csv (pct_of_WIS_L3, lo95_pct, hi95_pct, p per cell and increment; G_excess_primary_pct; margin1_over_L1L3_gain, margin05_over_L1L3_gain); Taiwan with 2021 (141,645 rows) -->
| Comparison | Climate, L1 → L2 | Remote sensing and population, L2 → L3 | All non-case covariates, L1 → L3 | Embeddings, L3 → L4 | Excess gain | ±1% (±0.5%) as a multiple of the L1 → L3 gain |
|---|---|---|---|---|---|---|
| Brazil | **+0.57 (0.03 to 1.12); 0.041** | **+0.52 (0.18 to 0.86); 0.0053** | **+1.09 (0.44 to 1.74); 0.0026** | +0.26 (−0.31 to 0.82); 0.35 | +0.23 | 0.92 (0.46) |
| Colombia | +0.14 (−0.14 to 0.42); 0.29 | **+0.30 (0.03 to 0.57); 0.034** | +0.44 (−0.05 to 0.93); 0.072 | −0.38 (−0.61 to −0.16); 0.0035 | −0.42 | 2.26 (1.13) |
| Peru | +0.44 (−1.48 to 2.37); 0.63 | −0.24 (−0.99 to 0.51); 0.50 | +0.20 (−1.84 to 2.24); 0.84 | −0.91 (−1.62 to −0.20); 0.016 | −0.82 | 5.03 (2.51) |
| Taiwan (with 2021) | −1.10 (−2.60 to 0.40); 0.14 | −0.17 (−0.53 to 0.19); 0.34 | −1.27 (−2.92 to 0.38); 0.12 | −0.95 (−1.71 to −0.18); 0.018 | −0.71 | not defined (L1 → L3 gain negative) |

Note: Gains in % of WIS(L3) with 95% CI, and unadjusted p. All runs use one shared configuration per country. L3 and L4 average seeds 0 to 2 in every country. Bold marks a covariate step whose CI excludes zero. The excess gain is the primary estimate (Table 2). Without 2021 (seed 0), Taiwan's gains for the four steps were −0.93% (p = 0.21), +0.06% (p = 0.85), −0.87% (p = 0.28) and −0.94% (p = 0.043). <!-- src: R3_A1_positive_control.csv note "L3/L4 = primary runs, seed-averaged"; R3_A1_positive_control_no2021.csv TW_S1 -->

The design can detect a known set of predictors, but only in Brazil and, for one step, in Colombia. In Brazil, climate (+0.57%), remote sensing and population (+0.52%) and both together (+1.09%) each improved the forecast. In Colombia only remote sensing and population did (+0.30%, p = 0.034). In Peru and Taiwan no step was detectable. Taiwan's point estimates were negative, with −1.27% for all inputs other than case history (p = 0.12). The null embedding results in Peru and Taiwan therefore say little about whether useful information would have been detected. None of these p values is adjusted, and the two results with p between 0.03 and 0.05 would not stay significant after adjustment over the 16 tests. The ±1% margin equals 0.92 times the whole gain from Brazil's inputs other than case history, 2.26 times Colombia's and 5.03 times Peru's. A difference within ±1% therefore leaves room for an embedding effect as large as everything that climate, remote sensing and population add to case history. Brazil's excess gain (+0.23%) is about the size of its gain from climate. <!-- src: R3_A1_positive_control.csv -->

### G3. "No control" selection rule

**Table S45. Primary family when "no control" is allowed at the 2019 selection.**

<!-- src: R3_A2_nocontrol_rule.csv (rule_noctrl_Cstar, estimand_used, est_pct, lo95_pct, hi95_pct, p, Holm_p, G_excess_pct_primary, Holm_p_primary, G_id_CI_below_0; n_cells_holm 14) -->
| Comparison | C\* under rule v2 → this rule | Estimand under this rule | % (95% CI) | p | Holm p (14 comparisons) | Primary excess gain (Holm p) | Control-gain CI below 0 |
|---|---|---|---|---|---|---|---|
| Brazil, future years (S1) | C1 → C1 | excess | +0.23 (−0.33 to 0.79) | 0.39 | 1.0 | +0.23 (1.0) | no |
| Brazil, held-out states (S2) | C1 → none | embedding | −0.02 (−0.34 to 0.30) | 0.88 | 1.0 | 0.00 (1.0) | no |
| Brazil, held-out regions (S3) | C1 → none | embedding | −0.13 (−0.35 to 0.09) | 0.21 | 1.0 | −0.16 (0.53) | no |
| Brazil, held-out districts (S4) | C1 → none | embedding | +0.22 (−0.32 to 0.76) | 0.40 | 1.0 | +0.20 (1.0) | no |
| Brazil, held-out country (S5) | C3 → none | embedding | −0.39 (−1.34 to 0.55) | 0.39 | 1.0 | **−0.68 (<0.001)** | no |
| Colombia, future years (S1) | C1 → none | embedding | **−0.38 (−0.61 to −0.16)** | 0.0035 | **0.035** | −0.42 (0.014) | no |
| Colombia, held-out states (S2) | C1 → none | embedding | **−0.60 (−0.81 to −0.39)** | <0.001 | **<0.001** | −0.52 (0.0034) | yes |
| Colombia, held-out regions (S3) | C1 → none | embedding | **−0.82 (−1.14 to −0.49)** | <0.001 | **0.0022** | −0.68 (0.030) | yes |
| Colombia, held-out districts (S4) | C1 → none | embedding | **−0.54 (−0.78 to −0.30)** | <0.001 | **0.0050** | −0.45 (0.019) | yes |
| Colombia, held-out country (S5) | C2 → C2 | excess | +0.22 (−0.19 to 0.63) | 0.27 | 1.0 | +0.22 (1.0) | yes |
| Peru, future years (S1) | C1 → none | embedding | −0.91 (−1.62 to −0.20) | 0.016 | 0.14 | −0.82 (0.18) | no |
| Peru, held-out country (S5) | C3 → none | embedding | +0.68 (−0.59 to 1.96) | 0.27 | 1.0 | +0.93 (0.53) | yes |
| Taiwan, future years (S1) | C1 → none | embedding | −0.95 (−1.71 to −0.18) | 0.018 | 0.15 | −0.71 (0.29) | no |
| Taiwan, held-out country (S5) | C3 → none | embedding | **−21.60 (−31.82 to −11.39)** | <0.001 | **0.0045** | −18.29 (0.035) | yes |

Note: Under this rule the selected control is "none" unless a candidate beat L3 at the 2019 origin by more than two standard errors, using the seed-noise standard error of the main selection rule. Comparisons without a control then contribute the embedding gain (L3 → L4). Only Brazil, future years (C1), and Colombia held out (C2) keep a control. Holm adjustment over the 14 comparisons. Bold marks Holm p < 0.05; in the primary column it is used only where the interpretation differs. The last column marks comparisons where the selected control on its own made L3 worse, that is, where the 95% CI of the control gain lies below zero. Estimates as in Table 2: seeds 0 to 2 where three seeds exist; the embedding gains of Peru and Taiwan held out use seed 0.

No comparison shows a gain under either rule. With Brazil held out, the loss appears only when the noise control of matching size (C3) is in the model. Without a control the embedding gain there is −0.39% (p = 0.39). The Colombian losses are of similar size or larger without a control and remain significant after Holm adjustment, so they do not depend on the choice of control. Under this rule the Holm-significant losses are Colombia's four within-country splits and Taiwan held out. In six comparisons the selected control itself made the reference model worse: Colombia's held-out states, regions, districts and country, Peru held out and Taiwan held out. <!-- src: R3_A2_nocontrol_rule.csv; docs/results/FINAL_RESULTS_BRIEF.md section 7 A2 and section 9 -->

### G4. Trend over test years

**Table S46. Trend of the excess gain with the length of the training window, and Brazil's 2023 to 2024 test years.**

<!-- src: R3_A3_trend.csv (estimand G_excess: slope, p_known_z, p_scaled_t; years "all test years" and "excl. 2020-21 (COVID)") -->
| Comparison | Slope, percentage points per extra training year | p, per-year SEs as given | p, SEs scaled for over-dispersion | Slope without 2020 and 2021 (scaled p) |
|---|---|---|---|---|
| Brazil, future years (S1) | +0.24 | 0.0034 | 0.12 | +0.34 (0.39) |
| Brazil, held-out states (S2) | +0.28 | <0.001 | 0.096 | +0.28 (0.31) |
| Brazil, held-out regions (S3) | +0.06 | 0.037 | 0.37 | +0.04 (0.69) |
| Brazil, held-out districts (S4) | +0.18 | 0.0080 | 0.20 | +0.32 (0.38) |
| Brazil, held-out country (S5) | +0.10 | 0.15 | 0.63 | +0.10 (0.48) |
| Colombia, future years (S1) | +0.22 | <0.001 | 0.18 | – |
| Colombia, held-out states (S2) | +0.16 | 0.019 | 0.26 | – |
| Colombia, held-out regions (S3) | +0.08 | 0.64 | 0.72 | – |
| Colombia, held-out districts (S4) | +0.26 | <0.001 | 0.16 | – |
| Colombia, held-out country (S5) | −0.12 | 0.26 | 0.79 | – |
| Peru, future years (S1) | +0.53 | 0.091 | 0.23 | – |
| Peru, held-out country (S5) | −0.39 | 0.38 | 0.47 | – |
| Taiwan, future years (S1) | +3.21 | 0.078 | 0.32 | −2.55 (0.62) |
| Taiwan, held-out country (S5) | +3.48 | 0.37 | 0.79 | −20.19 (0.54) |

<!-- src: R3_A3_per_year.csv rows test_year = 2023-2024 (pct, lo95_pct, hi95_pct, p, B4_p) -->
| Brazil comparison, test years 2023 and 2024 only | Excess gain, % (95% CI); p (B = 4 p) | Embedding gain, % (95% CI); p |
|---|---|---|
| Future years (S1) | +0.69 (−0.40 to 1.78); 0.18 (0.23) | +0.68 (−0.45 to 1.81); 0.20 |
| Held-out states (S2) | +0.37 (−0.20 to 0.94); 0.17 (0.23) | +0.31 (−0.28 to 0.90); 0.26 |
| Held-out regions (S3) | +0.03 (−0.18 to 0.24); 0.74 (0.74) | +0.11 (−0.23 to 0.44); 0.48 |
| Held-out districts (S4) | +0.61 (−0.39 to 1.61); 0.20 (0.25) | +0.63 (−0.44 to 1.70); 0.21 |
| Held-out country (S5) | −0.54 (−0.81 to −0.28); 0.0015 (0.0089) | +0.12 (−1.63 to 1.87); 0.87 |

Note: Weighted least-squares regression of each comparison's yearly excess gain (Table S30) on the number of training years, with weights equal to the inverse squared standard error and 3 to 5 points per comparison. "Scaled" enlarges the standard errors to allow for year-to-year noise larger than the formula assumes (over-dispersion). The length of the training window cannot be separated from the COVID-19 years 2020 and 2021. Taiwan's yearly percentages are unstable, because the reference WIS is tiny in years with few cases. Post hoc. The yearly embedding gains behave in the same way. <!-- src: R3_summary.md A3 "What was computed" and "G_emb behaves the same way"; R3_A3_trend.csv estimand G_emb -->

With the yearly standard errors taken at face value, 7 of 14 comparisons had a positive slope with p < 0.05. Once the standard errors were scaled for over-dispersion, none did (smallest p = 0.096), and none did when 2020 and 2021 were dropped. The positive point estimates come mainly from losses in 2021, the COVID-affected year with the second-shortest training window. In Brazil's two most recent test years no comparison showed a significant gain (largest +0.69%, p = 0.18), and the loss with Brazil held out persisted (−0.54%, p = 0.0015). The training windows are short and COVID-affected, so the data cannot show whether the embeddings would help with longer training histories. <!-- src: R3_A3_trend.csv; R3_A3_per_year.csv 2023-2024 rows -->

### G5. Equivalence under other margins and stricter checks

**Table S47. Equivalence of the excess gain at ±0.5%, ±1% and ±2% under the main test, the strict-variance check (B = 4) and the surrogate-series check.**

<!-- src: R3_A4_equivalence.csv (estimand G_excess; lo90_pct, hi90_pct per se_variant; equivalent_unadj, equivalent_Holm per margin; n_cells_holm 14); R3_A8_iaaft_equivalence.csv (size_nominal5 EWC/B=4, cal_lo90_pct, cal_hi90_pct, equivalent_1pct_calibrated) -->
| Comparison | 90% CI, EWC | 90% CI, B = 4 | Equivalent at ±0.5% | at ±1% | at ±2% | IAAFT size of the 5% test, EWC / B = 4 | IAAFT-calibrated 90% CI; equivalent at ±1% |
|---|---|---|---|---|---|---|---|
| Brazil, future years (S1) | −0.23 to 0.69 | −0.36 to 0.82 | – | a b c | a b c d | 18.4% / 12.5% | −0.62 to 1.08; no |
| Brazil, held-out states (S2) | −0.28 to 0.28 | −0.43 to 0.43 | a b c | a b c d | a b c d | 14.0% / 5.0% | −0.38 to 0.38; yes |
| Brazil, held-out regions (S3) | −0.31 to −0.01 | −0.41 to 0.10 | a b c | a b c d | a b c d | 15.2% / 5.0% | −0.37 to 0.05; yes |
| Brazil, held-out districts (S4) | −0.23 to 0.62 | −0.33 to 0.73 | – | a b c | a b c d | 14.9% / 9.9% | −0.48 to 0.88; yes |
| Brazil, held-out country (S5) | −0.89 to −0.47 | −0.97 to −0.39 | – | a c | a b c d | 6.5% / 3.5% | −0.91 to −0.45; yes |
| Colombia, future years (S1) | −0.60 to −0.25 | −0.64 to −0.21 | – | a b c d | a b c d | 8.7% / 4.1% | −0.63 to −0.22; yes |
| Colombia, held-out states (S2) | −0.70 to −0.34 | −0.67 to −0.38 | – | a b c d | a b c d | 1.1% / 2.0% | −0.66 to −0.39; yes |
| Colombia, held-out regions (S3) | −1.01 to −0.36 | −1.00 to −0.37 | – | c | a b c d | not run | – |
| Colombia, held-out districts (S4) | −0.64 to −0.25 | −0.68 to −0.21 | – | a b c d | a b c d | 7.4% / 3.6% | −0.66 to −0.23; yes |
| Colombia, held-out country (S5) | −0.12 to 0.55 | −0.39 to 0.83 | – | a b c | a b c d | 15.8% / 6.8% | −0.27 to 0.70; yes |
| Peru, future years (S1) | −1.37 to −0.26 | −1.68 to 0.05 | – | – | a b c d | not run | – |
| Peru, held-out country (S5) | 0.04 to 1.83 | 0.40 to 1.46 | – | – | a c d | not run | – |
| Taiwan, future years (S1) | −1.28 to −0.15 | −1.21 to −0.22 | – | – | a b c d | not run | – |
| Taiwan, held-out country (S5) | −27.77 to −8.81 | −30.57 to −6.01 | – | – | – | not run | – |
| Comparisons equivalent (a / b / c / d) | | | 2 / 2 / 2 / 0 | 9 / 8 / 10 / 5 | 13 / 12 / 13 / 13 | | 8 of 9 at ±1% |

Note: TOST on 90% CIs, % of reference WIS. Letters list the versions under which a comparison is equivalent: a, main test (EWC), unadjusted; b, EWC with Holm adjustment over 14 comparisons; c, strict-variance check (B = 4), unadjusted; d, B = 4 with Holm adjustment. The IAAFT columns come from the surrogate-series check, with 2,000 surrogates of each comparison's weekly loss-difference series under no effect. They were run only for the nine comparisons equivalent at ±1% under a, without Holm adjustment. Estimates as in Table 2 (seeds 0 to 2 where three seeds exist). <!-- src: R3_A4_equivalence.csv counts; R3_A8_iaaft_equivalence.csv; docs/results/FINAL_RESULTS_BRIEF.md section 1 equivalence counts -->

Equivalence depends on both the margin and the test. At ±1%, nine comparisons are equivalent under the main test without adjustment, and eight after Holm adjustment. Five are equivalent under the strict-variance check with Holm adjustment: Brazil's held-out states and regions, and Colombia's future years, held-out states and held-out districts. Three of these five are significantly negative, so "equivalent" there means a loss smaller than 1% rather than no effect. At ±0.5%, two comparisons are equivalent under the main test, with or without Holm adjustment, and none under the strict-variance check with Holm adjustment.

The surrogate-series check shows that the main test finds effects too often in five comparisons: Brazil's future years, held-out states, held-out regions and held-out districts, and Colombia held out. There, a nominal 5% test rejected 14% to 18% of the time. After this calibration, Brazil, future years, the comparison with the largest positive point estimate, is no longer equivalent at ±1% (calibrated 90% CI −0.62 to 1.08), so neither a gain nor equivalence is established there. In the comparisons with clear losses the rate is close to nominal or below it (1.1% to 8.7%). <!-- src: R3_A4_equivalence.csv; R3_A8_iaaft_equivalence.csv size_nominal5, cal_lo90_pct, cal_hi90_pct -->

### G6. District-years with cases, and forecast width and coverage

**Table S48. District-years with cases, and forecast width and coverage on weeks with and without cases.**

Panel A. Excess and embedding gains on district-years with at least one reported case in that test year. The condition applies to the whole district-year, so weeks without cases in those years are kept.

<!-- src: R3_A6_outcome_agnostic.csv analysis "a: unit-years with >=1 case" (row_share, pct_of_ref, lo95_pct, hi95_pct, p per cell and estimand) -->
| Comparison | Rows kept | Excess gain, % (95% CI); p | Primary excess gain | Embedding gain, % (95% CI); p |
|---|---|---|---|---|
| Colombia, future years (S1) | 71% | **−0.33 (−0.53 to −0.13); 0.0038** | −0.42 | **−0.28 (−0.49 to −0.07); 0.014** |
| Colombia, held-out states (S2) | 71% | **−0.33 (−0.52 to −0.13); 0.0040** | −0.52 | **−0.40 (−0.58 to −0.22); <0.001** |
| Colombia, held-out regions (S3) | 71% | −0.33 (−0.71 to 0.05); 0.083 | −0.68 | **−0.45 (−0.75 to −0.15); 0.0071** |
| Colombia, held-out districts (S4) | 71% | **−0.29 (−0.49 to −0.09); 0.0084** | −0.45 | **−0.40 (−0.61 to −0.19); 0.0015** |
| Colombia, held-out country (S5) | 71% | +0.28 (−0.08 to 0.65); 0.12 | +0.22 | 0.00 (−0.31 to 0.31); 0.99 |
| Brazil, held-out districts (S4) | 81% | +0.20 (−0.26 to 0.66); 0.36 | +0.20 | +0.22 (−0.26 to 0.70); 0.34 |
| Brazil, held-out country (S5) | 81% | **−0.46 (−0.71 to −0.21); 0.0013** | −0.68 | −0.08 (−0.93 to 0.78); 0.85 |
| Peru, held-out country (S5) | 76% | +1.01 (−0.12 to 2.14); 0.075 | +0.93 | +0.78 (−0.51 to 2.08); 0.21 |
| Taiwan, held-out country (S5) | 19% | **−3.28 (−4.77 to −1.79); <0.001** | −18.29 | **−5.11 (−7.17 to −3.05); <0.001** |

Note: % of the reference WIS on the kept rows. Brazil's future years, held-out states and held-out regions stay within ±0.25% and are not significant. Peru, future years, is −0.77% (95% CI −1.45 to −0.09; p = 0.029), and Taiwan, future years, −0.51% (p = 0.32). Rows kept are shares of each country's primary rows. Bold: CI excludes zero. <!-- src: R3_A6_outcome_agnostic.csv analysis a: BR_S1 +0.22, BR_S2 +0.03, BR_S3 −0.05; PE_S1 −0.772 (−1.451 to −0.093) p 0.029; TW_S1 −0.515 p 0.32 -->

Panel B. Change from L3 + C\* to L4 + C\* in 80% interval coverage on weeks with cases, and in mean 80% interval width (log(1 + cases) scale) on weeks with and without cases.

<!-- src: R3_A6_outcome_agnostic.csv analysis "b: coverage/width L4+C* minus L3+C*": metric cov_80 and w80_log, stratum case/zero weeks (L3C_mean, L4C_mean, diff_week_mean, diff_lo95, diff_hi95, diff_p) -->
| Comparison | Coverage on case weeks, L3 + C\* | Change in coverage on case weeks, pp (p) | Change in width, zero weeks | Change in width, case weeks |
|---|---|---|---|---|
| Brazil, future years (S1) | 0.66 | −0.2 (0.31) | **+0.006 (+1.6%)** | −0.004 |
| Brazil, held-out states (S2) | 0.66 | **−0.5 (0.011)** | **+0.009 (+2.6%)** | **−0.008** |
| Brazil, held-out regions (S3) | 0.66 | +0.2 (0.088) | **+0.027 (+7.5%)** | +0.002 |
| Brazil, held-out districts (S4) | 0.66 | −0.2 (0.35) | **+0.009 (+2.7%)** | −0.003 |
| Brazil, held-out country (S5) | 0.64 | +0.4 (0.27) | **+0.042 (+9.8%)** | **+0.017** |
| Colombia, future years (S1) | 0.71 | 0.0 (0.94) | **+0.017 (+5.3%)** | +0.001 |
| Colombia, held-out states (S2) | 0.71 | −0.8 (0.15) | **+0.019 (+5.8%)** | −0.010 |
| Colombia, held-out regions (S3) | 0.71 | **−1.0 (0.0028)** | **+0.025 (+7.1%)** | **−0.014** |
| Colombia, held-out districts (S4) | 0.71 | −0.4 (0.41) | **+0.017 (+5.2%)** | −0.004 |
| Colombia, held-out country (S5) | 0.75 | +0.2 (0.29) | **+0.007 (+2.1%)** | −0.007 |
| Peru, future years (S1) | 0.67 | +0.5 (0.076) | **+0.036 (+12.3%)** | **+0.021** |
| Peru, held-out country (S5) | 0.65 | **+2.1 (<0.001)** | **+0.016 (+6.9%)** | **+0.041** |
| Taiwan, future years (S1) | 0.24 | −0.9 (0.25) | +0.002 (+6.4%) | −0.021 |
| Taiwan, held-out country (S5) | 0.57 | +3.7 (0.070) | **+0.093 (+55%)** | **+0.071** |

Note: Absolute changes are week-weighted differences, L4 + C\* minus L3 + C\*, with p values from the main test. Percentages in brackets are the relative change in the mean interval width on zero weeks, as a row mean (L4 + C\* against L3 + C\*). Bold: 95% CI excludes zero. Intervals on zero weeks already contain the observation more often than intended (about 96% to 100%). Estimates as in Table 2 (seeds 0 to 2 where three seeds exist). <!-- src: R3_A6_outcome_agnostic.csv analysis b; zero-week width ratio = L4C_mean / L3C_mean − 1 (w80_log, zero weeks) -->

The Colombian losses do not come only from zero weeks. On district-years with at least one case, the excess gain is still about −0.3% and significant in the future-years, held-out-states and held-out-districts splits. The embedding gain is significantly negative in all four within-country splits. The loss shrinks by a fifth to a half on these rows, so part of it lies in district-years without cases. With Taiwan held out, the loss falls from −18.29% to −3.28% on district-years with cases, so most of it lies in district-years with no local case. Brazil's held-out districts stay at +0.20% (p = 0.36). <!-- src: Panel A; R3_A6_outcome_agnostic.csv analysis a --> We also examined the forecasts themselves, without scoring them, separately for weeks with and without cases. On zero weeks, the embeddings widened the 80% intervals in all 14 comparisons. The increase was 1.6% to 12.3%, and 55% with Taiwan held out. The CI was above zero in 13 of them, although those intervals already contained the observation more often than intended. The embeddings moved coverage on weeks with cases significantly towards the nominal 80% in only one comparison (Peru held out, +2.1 percentage points). They moved it significantly away in two (Brazil's held-out states and Colombia's held-out regions). The embeddings therefore raised the upper forecast quantiles in weeks without cases and did not correct the under-coverage in epidemic weeks. <!-- src: Panel B; R3_A6_outcome_agnostic.csv analysis b; docs/results/FINAL_RESULTS_BRIEF.md section 7 A6 -->

### G7. Stability of the embeddings

**Table S49. Year-to-year similarity of a district's embedding compared with similarity between districts.**

<!-- src: R3_A7_embedding_stability.csv (median per country and metric); R3_summary.md A7 table -->
| Country | Same district, consecutive years | Same district, first vs last year | Five nearest neighbouring districts, same year | Random district pairs | Next-year vector is the district's own nearest match | Next-year similarity above all five neighbours |
|---|---|---|---|---|---|---|
| Brazil | 0.982 | 0.958 | 0.974 | 0.70 | 57% | 87% |
| Colombia | 0.976 | 0.940 | 0.931 | 0.64 | 84% | 95% |
| Peru | 0.985 | 0.973 | 0.912 | 0.49 | 94% | 98% |
| Taiwan | 0.978 | 0.972 | 0.971 | 0.88 | 69% | 89% |

Note: Median cosine similarity of the rescaled, population-weighted district means of the AlphaEarth embeddings, from 2017 to the last extracted year. The last two columns are shares of district-year pairs. <!-- src: R3_A7_embedding_stability.csv -->

In Brazil and Taiwan a district's embedding changes from year to year by about as much as it differs from its neighbours. The median similarities were 0.982 vs 0.974 in Brazil and 0.978 vs 0.971 in Taiwan. The next year's vector is the district's own nearest match only 57% and 69% of the time. In Colombia and Peru the embedding picks out each district well (84% and 94%). Year-to-year drift was therefore a possible explanation for small losses in Brazil and Taiwan. It does not explain Colombia, where the embedding picks out each district well and the losses are clearest. The fixed embedding built only from early years (V3, Table S51) did not remove the losses either. <!-- src: R3_summary.md A7 interpretation; R3_C_summary.md section 1 V3 reading -->

### G8. Information probe

**Table S50. Cross-sectional prediction of district dengue burden from embeddings, coordinates and static covariates.**

<!-- src: docs/results/review/R3_E1_info_probe.md, sections T1 and T2 (grouped-state CV; LightGBM and ridge rows); R3_E1_info_probe.csv -->
| Country (districts) | G | S | E | G + S | G + S + E | Added by E over G + S, T1 (95% CI) | Added by E over G + S, T2 (95% CI) | Ridge: added by E over G + S, T1 (95% CI) |
|---|---|---|---|---|---|---|---|---|
| Brazil (5,517) | 0.06 | 0.65 | 0.49 | 0.71 | 0.72 | +0.010 (−0.002 to 0.025) | +0.009 (−0.010 to 0.046) | +0.169 (−0.050 to 0.724) |
| Colombia (1,070) | −0.17 | 0.66 | 0.52 | 0.71 | 0.72 | +0.010 (−0.018 to 0.042) | −0.006 (−0.024 to 0.019) | +0.423 (0.015 to 1.444) |
| Peru (115) | −0.16 | 0.43 | 0.24 | 0.45 | 0.38 | −0.071 (−0.267 to 0.070) | −0.015 (−0.140 to 0.097) | +0.299 (−0.123 to 0.917) |
| Taiwan (285) | −0.38 | 0.55 | 0.45 | 0.33 | 0.40 | +0.070 (−8.20 to 0.399) | −0.104 (−1.02 to 0.047) | −0.205 (−20.1 to 3.10) |

Note: Out-of-fold R² of a small LightGBM (31 leaves, 200 rounds) predicting T1, the mean log(1 + weekly cases) of 2014 to 2019. Cross-validation holds out whole states, with five folds built as in the held-out-states split. G, coordinates with spherical harmonics (the C2 inputs); S, 2017 to 2018 means of the L3 static covariates and log population in 2018; E, the 2018 AlphaEarth embedding (64 dimensions, rescaled). T2 is the mean log(1 + weekly cases) over the test years. The 95% CIs come from 1,000 bootstrap resamples of states, applied to the fixed out-of-fold predictions, so they ignore variation from refitting. Taiwan's CIs are unstable because resamples without Kaohsiung and Tainan have almost no variance. The ridge column is shown for completeness only. Ridge regression on the 82 coordinate columns extrapolates badly to held-out states (R² of G alone −0.20 to −0.44 for T1), so its added R² mostly reflects ridge failing on G + S rather than information in E. In Taiwan, adding coordinates lowered R² below that of S alone (0.33 against 0.55), and in Peru it raised it only slightly (0.45 against 0.43), so there the increment over G + S is measured against a weak baseline. Measured over S alone, E also added nothing in either country (Peru −0.11, 95% CI −0.32 to 0.03; Taiwan −0.01, −9.92 to 0.18). <!-- src: docs/results/review/R3_E1_info_probe.csv, target T1, grouped_state, lgbm, quantity dR2, fset S+E, base S: PERU −0.11211 (−0.32028, 0.03279), TAIWAN −0.01499 (−9.92212, 0.18099) --> These are cross-sectional associations. S and E overlap the T1 period; T2 does not. <!-- src: R3_E1_info_probe.md Design, Interpretation and Caveats sections; ridge G R² T1 BR −0.44, CO −0.20, PE −0.10, TW −0.44 -->

The embeddings carry information about district dengue burden. On their own they explained 0.49, 0.52, 0.24 and 0.45 of the between-district variance of T1 in held-out states of Brazil, Colombia, Peru and Taiwan. This is less than the static covariates explained (0.43 to 0.66) and far above coordinates alone (−0.38 to 0.06), which in a tree model cannot extrapolate to states not used for fitting. Added to coordinates and static covariates, however, the embeddings raised R² by at most about 0.01 in Brazil and Colombia, with CIs that include zero. The reduction to 8 principal components gave the same result. In Peru and Taiwan the added R² was negative or near zero, with wide CIs. When a whole country was left out, the embeddings predicted its burden weakly or not at all. The T1 R² was −0.34, 0.28 and 0.27 with Brazil, Colombia and Peru held out, and below zero with Taiwan held out. <!-- src: R3_E1_info_probe.md T1 LightGBM rows, T1 LOCO column, Interpretation items 1–3 -->

### G9. Representation variants

**Table S51. Embedding and excess gains with alternative representations of the embeddings.**

We tried four other ways of using the embeddings in place of the 64 columns. They were added after review and are exploratory.

- V1, similarity risk, a single column: the average past dengue level of the k = 5 training districts with the most similar embeddings. Similarity is cosine similarity, and closer districts get more weight (inverse-dissimilarity weights). Past dengue level is the mean log(1 + cases) over the years before training. The district itself is excluded, and in held-out states and regions the same matched leave-out as for average past cases (C1) is used. V1 is the embedding counterpart of C1.
- V2, the first 8 principal components of the embeddings, fitted on training districts for each origin and fold.
- V3, a fixed embedding built only from early years: the rescaled mean of the 2017 and 2018 vectors, the same in every year.
- V4, substitution: the embeddings in place of the remote-sensing and population inputs of L3, that is, L2 plus embeddings.

All variants use average past cases (C1) as the selected control, the shared configurations, seed 0 and horizons 1 and 4.

<!-- src: R3_C_variants.csv; R3_C_summary.md section 1 tables (embedding gain; excess gain beyond C1; V1 against geography; substitution) -->
| Comparison | Original 64 columns | V1, risk encoding | V2, PCA-8 | V3, causal static |
|---|---|---|---|---|
| *Embedding gain, % (95% CI); p (Holm p)* | | | | |
| Colombia, future years (S1) | −0.36; 0.0052 | −0.07 (−0.13 to −0.01); 0.023 (1.0) | −0.07 (−0.17 to 0.02); 0.12 (1.0) | −0.14 (−0.25 to −0.03); 0.017 (1.0) |
| Colombia, held-out states (S2) | −0.59; <0.001 | −0.04 (−0.11 to 0.03); 0.19 (1.0) | **−0.14 (−0.22 to −0.07); <0.001 (0.027)** | **−0.30 (−0.40 to −0.20); <0.001 (0.001)** |
| Peru, future years (S1) | −0.94; 0.020 | −0.01 (−0.13 to 0.10); 0.81 (1.0) | −0.15 (−0.64 to 0.35); 0.53 (1.0) | −0.66 (−1.19 to −0.13); 0.018 (1.0) |
| Taiwan, future years (S1, with 2021) | −1.06; 0.024 | −0.66 (−1.76 to 0.45); 0.23 (1.0) | −0.46 (−1.71 to 0.78); 0.44 (1.0) | −0.60 (−1.58 to 0.37); 0.21 (1.0) |
| Brazil, held-out states (S2) | −0.02; 0.88 | −0.05 (−0.11 to 0.01); 0.10 (1.0) | −0.02 (−0.17 to 0.12); 0.75 (1.0) | not run |
| *Excess gain beyond C1, % (95% CI); p (Holm p)* | | | | |
| Colombia, future years (S1) | −0.39; 0.0011 | −0.05 (−0.09 to −0.01); 0.014 (1.0) | −0.13 (−0.24 to −0.02); 0.025 (1.0) | −0.08 (−0.19 to 0.03); 0.12 (1.0) |
| Colombia, held-out states (S2) | −0.47; <0.001 | −0.01 (−0.05 to 0.03); 0.68 (1.0) | −0.11 (−0.18 to −0.05); 0.0033 (0.085) | **−0.21 (−0.31 to −0.12); <0.001 (0.015)** |
| Peru, future years (S1) | −0.70; 0.056 | +0.04 (−0.10 to 0.19); 0.53 (1.0) | +0.06 (−0.41 to 0.54); 0.77 (1.0) | **−0.87 (−1.32 to −0.42); 0.0012 (0.032)** |
| Taiwan, future years (S1, with 2021) | −0.60; 0.049 | −0.11 (−0.29 to 0.07); 0.20 (1.0) | +0.15 (−0.53 to 0.83); 0.65 (1.0) | −0.12 (−0.32 to 0.08); 0.22 (1.0) |
| Brazil, held-out states (S2) | 0.00; 1.0 | −0.02 (−0.06 to 0.02); 0.31 (1.0) | +0.05 (−0.12 to 0.21); 0.56 (1.0) | not run |

<!-- src: R3_C_summary.md section 1 "V1 against geography directly" and "Substitution (V4)" tables -->
| Comparison | V1 vs C1: WIS(L3 + C1) − WIS(L3 + V1), % (95% CI); p | V4 substitution: WIS(L3) − WIS(L2 + embeddings), % (95% CI); p (Holm p) | WIS(L2) − WIS(L2 + embeddings), % (95% CI); p |
|---|---|---|---|
| Colombia, future years (S1) | −0.01 (−0.23 to 0.21); 0.94 | **−0.79 (−1.15 to −0.42); <0.001 (0.018)** | −0.48 (−0.80 to −0.17); 0.0062 |
| Colombia, held-out states (S2) | +0.04 (−0.004 to 0.08); 0.064 | **−0.93 (−1.27 to −0.59); <0.001 (0.003)** | no L2 run |
| Peru, future years (S1) | +0.24 (−0.48 to 0.97); 0.48 | −0.84 (−1.66 to −0.01); 0.047 (0.93) | −1.10 (−1.90 to −0.31); 0.010 |
| Taiwan, future years (S1, with 2021) | −0.03 (−0.20 to 0.15); 0.74 | −0.79 (−1.77 to 0.20); 0.11 (1.0) | −0.74 (−1.37 to −0.11); 0.024 |
| Brazil, held-out states (S2) | 0.00 (−0.07 to 0.07); 0.91 | not run | not run |

Note: % of WIS(L3); a positive value means that the variant reduced error. Holm adjustment is within the family of 32 variant tests named in the specification: the embedding and excess gains of V1 to V3 and the substitution contrast. The contrasts of V1 with C1 and with L2 are outside that family. Bold: Holm p < 0.05. The first column repeats the primary seed-0 values. <!-- src: R3_C_summary.md section 1 "Holm" paragraph -->

No variant turned the embeddings into a significant gain. None of the 28 tests of embedding and excess gains had a CI above zero, and the largest point estimate was +0.15%. The compact forms V1 (one column) and V2 (eight columns) shrank the loss towards zero. In Colombia, future years, the embedding gain was −0.07% for both, against −0.36% with the full embedding. Part of the loss with 64 columns is therefore a cost of having many inputs, but the compact forms did not reverse it. V1 could not be told apart from average past cases in any comparison (largest difference +0.04%, p = 0.064). Similarity in embedding space thus carried risk from neighbours about as well as geographic closeness did, and no better. The fixed early-years embedding V3 did not remove the loss. Its excess gain was −0.21% in Colombia's held-out states and −0.87% in Peru's future years (Holm p = 0.032), so year-to-year changes in the vector do not explain the whole loss. Used in place of the remote-sensing and population inputs, the embeddings were worse than L3 in all four comparisons (Colombia −0.79% and −0.93%, both Holm-significant). In Colombia, Peru and Taiwan they were also worse than L2, which has no place inputs at all, so in this model they did not replace the hand-built covariates. Every Holm-significant variant result is a loss, and all lie within or near ±1%. <!-- src: R3_C_summary.md section 1 Reading; TRIAGE_round3.md Addendum 4 -->

### G10. Seeds

**Table S52. Excess, embedding and control gains averaged over seeds 0 to 2, and seed 0 alone.**

<!-- src: R3_C_seeds.csv; R3_C_summary.md sections 2 and 3 (per-seed G_excess, 3-seed mean with CI and p, seed SD; G_emb and G_id 3-seed; seed-0 Holm over 13 from the earlier primary table); T1_primary_family.csv Holm_p_available (14 cells, seeds 0–2) -->
| Comparison | C\* | Excess gain, seeds 0 / 1 / 2 | Excess gain, mean of seeds 0–2 (95% CI); p | Seed SD | Holm p, seed 0 (13 comparisons) → seeds 0–2 (14 comparisons) | Embedding gain, seeds 0–2 (95% CI); p | Control gain, seeds 0–2 (95% CI); p |
|---|---|---|---|---|---|---|---|
| Brazil, held-out country (S5) | C3 | −0.60 / −0.62 / −0.82 | −0.68 (−0.94 to −0.42); <0.001 | 0.12 | <0.001 → <0.001 | −0.39 (−1.34 to 0.55); 0.39 | +0.15 (−0.89 to 1.18); 0.77 |
| Colombia, future years (S1) | C1 | −0.39 / −0.48 / −0.40 | −0.42 (−0.64 to −0.21); 0.0012 | 0.05 | 0.012 → 0.014 | −0.38 (−0.61 to −0.16); 0.0035 | −0.06 (−0.32 to 0.19); 0.60 |
| Colombia, held-out states (S2) | C1 | −0.47 / −0.58 / −0.52 | −0.52 (−0.74 to −0.30); <0.001 | 0.05 | 0.0068 → 0.0034 | −0.60 (−0.81 to −0.39); <0.001 | −0.06 (−0.09 to −0.03); 0.0019 |
| Colombia, held-out regions (S3) | C1 | −0.65 / −0.70 / −0.70 | −0.68 (−1.08 to −0.29); 0.0030 | 0.03 | 0.026 → 0.030 | −0.82 (−1.14 to −0.49); <0.001 | −0.08 (−0.14 to −0.02); 0.011 |
| Colombia, held-out districts (S4) | C1 | −0.43 / −0.48 / −0.42 | −0.45 (−0.68 to −0.21); 0.0017 | 0.03 | 0.025 → 0.019 | −0.54 (−0.78 to −0.30); <0.001 | −0.10 (−0.12 to −0.08); <0.001 |
| Peru, future years (S1) | C1 | −0.70 / −0.88 / −0.87 | −0.82 (−1.49 to −0.14); 0.022 | 0.10 | 0.34 → 0.18 | −0.91 (−1.62 to −0.20); 0.016 | −0.20 (−0.92 to 0.52); 0.56 |
| Peru, held-out country (S5) | C3 | +0.96 / +0.96 / +0.88 | +0.93 (−0.16 to 2.02); 0.088 | 0.04 | 0.39 → 0.53 | +0.68 (−0.59 to 1.96); 0.27 (seed 0) | −0.44 (−0.80 to −0.07); 0.022 (seed 0) |
| Taiwan, future years (S1, with 2021) | C1 | −0.60 / −0.87 / −0.67 | −0.71 (−1.40 to −0.03); 0.042 | 0.14 | 0.34 → 0.29 | −0.95 (−1.71 to −0.18); 0.018 | −0.41 (−0.97 to 0.16); 0.15 |
| Taiwan, held-out country (S5, with 2021) | C3 | −17.30 / −18.06 / −19.51 | −18.29 (−29.80 to −6.78); 0.0039 | 1.12 | 0.017 → 0.035 | −21.60 (−31.82 to −11.39); <0.001 (seed 0) | −3.36 (−6.52 to −0.20); 0.039 (seed 0) |

Note: % of WIS(L3), horizons 1 and 4. Where three seeds exist, we averaged the per-row loss over the seeds that both models of a gain share and then applied the main test. Seed SD is the standard deviation of the three per-seed estimates, % of WIS. With Peru or Taiwan held out, only L3 + C\* and L4 + C\* have seeds 1 and 2, because of a limit on computing time set in advance, so their embedding and control gains stay at seed 0. Brazil's future-years comparison already used three seeds (Table 2). Brazil's held-out states, regions and districts and Colombia held out have seed 0 only. Holm adjustment for seed 0 is over the 13 comparisons available before the result for Brazil's held-out districts had been seen; for seeds 0 to 2 it is over all 14 comparisons, as in Table 2. The three-seed values are the primary estimates of Table 2 (row 53). <!-- src: R3_C_summary.md section 3 TW S5 / PE S5 paragraph; section 7 -->

Averaging over three seeds changed no conclusion after Holm adjustment. The same six comparisons remain significant losses: Brazil held out, Colombia's four within-country splits and Taiwan held out. Every loss grew slightly, by 0.01 to 0.12 percentage points and by 1.0 with Taiwan held out, and no seed reversed a sign. Under the strict-variance check (B = 4) with Holm adjustment, however, the loss with Brazil held out is no longer significant (p = 0.095). Only Colombia, held-out states, is therefore significant under the main test and both stricter checks (Table S26). The seed SD of the excess gain (0.03% to 0.14% of WIS; 1.1% with Taiwan held out) is small next to these effects. In Colombia every seed was negative and significant on its own, so the Colombian losses are not seed noise. Before adjustment, Peru, future years, moved from p = 0.056 to p = 0.022, and its CI now excludes zero; it is not significant after Holm adjustment (p = 0.18). With Peru held out the gain stays positive but not significant (+0.93%, p = 0.088), with every seed positive. The control gain is the quantity most sensitive to the seed. Seed 1 brought it to about zero in Colombia's held-out regions and districts and in Taiwan, future years. <!-- src: R3_C_summary.md sections 2 and 3 Reading -->

### G11. Taiwan future-years ladder including 2021

**Table S53. Baselines, ladder and fixed control panel for Taiwan, future years, with test year 2021.**

Panel A. Ladder and baselines (row mean; 141,645 rows).

<!-- src: R3_C_tw2021_ladder.csv rows pooled_over "1,4": wis_log, rel_wis_vs_L0, cov_80, cov_80_nonzero, no2021_rel_wis_vs_L0 -->
| Model | WIS | Relative WIS vs L0 | 80% coverage, all rows / cases > 0 | Relative WIS vs L0 without 2021 |
|---|---|---|---|---|
| L0, seasonal naive | 0.0743 | 1.00 | 0.95 / 0.00 | 1.00 |
| Negative binomial regression (L1 inputs) | 0.0475 | 0.64 | 0.99 / 0.42 | 0.64 |
| LightGBM L1, case history | 0.0316 | 0.43 | 0.98 / 0.24 | 0.43 |
| LightGBM L2, + climate (shared configuration) | 0.0319 | 0.43 | 0.98 / 0.23 | not run (the earlier L2 was tuned separately, 0.52) |
| LightGBM L3, + remote sensing and population | 0.0319 | 0.43 | 0.98 / 0.25 | 0.43 |
| LightGBM L4, + embeddings | 0.0323 | 0.43 | 0.98 / 0.24 | 0.44 |
| LightGBM L3 + C\* (C1) | 0.0321 | 0.43 | 0.98 / 0.24 | 0.43 |
| LightGBM L4 + C\* (C1) | 0.0323 | 0.43 | 0.98 / 0.24 | 0.44 |

Panel B. Fixed control panel (seed 0; no multiplicity adjustment).

<!-- src: R3_C_tw2021_panel.csv G_id_pct, G_id_pct_lo95, G_id_pct_hi95, G_id_p, G_excess_pct, G_excess_pct_lo95, G_excess_pct_hi95, G_excess_p, no2021_G_excess_pct, no2021_G_excess_p -->
| Control | Control gain, % (95% CI); p | Excess gain, % (95% CI); p | Excess gain without 2021; p |
|---|---|---|---|
| C1, average past cases | −0.63 (−1.68 to 0.43); 0.22 | −0.60 (−1.20 to −0.003); 0.049 | −0.44; 0.12 |
| C2, coordinates | −0.36 (−0.76 to 0.03); 0.070 | −0.94 (−2.03 to 0.15); 0.087 | −0.77; 0.16 |
| C3, shuffled embedding | −0.58 (−1.29 to 0.12); 0.097 | −0.68 (−1.45 to 0.09); 0.079 | −0.54; 0.15 |
| C6, district label | −2.29 (−5.59 to 1.02); 0.16 | −0.52 (−1.16 to 0.13); 0.11 | −0.42; 0.18 |
| none (embedding gain) | – | −1.06 (−1.96 to −0.16); 0.024 | −0.94; 0.043 |

Note: Every step of the ladder, control in the panel and gain from added predictors is scored on the same 141,645 rows as Table 2. TimesFM was not run for Taiwan. The 2021 targets are all zero, so adding 2021 lowers every absolute WIS but leaves the ordering and the relative WIS almost unchanged. Seed 0; Table S17 averages seeds 0 to 2 for L3, L4, L3 + C\* and L4 + C\*, so its values differ by up to 0.0001. <!-- src: R3_C_summary.md section 5 row-count check and ladder note -->

With 2021 included, all Taiwan tables use the same rows. Every LightGBM model forecast Taiwan about 57% better than the seasonal naive baseline, and nothing added to case history helped. L1 had the lowest WIS of the LightGBM ladder, and the steps adding inputs other than case history had no detectable effect (Table S44). All four fixed controls gave a negative excess gain, significant before adjustment only with C1 (p = 0.049), and none of them improved L3. Tables S17 to S20 and S36 use these values with 2021 included. <!-- src: R3_C_tw2021_ladder.csv rel_wis_vs_L0 L1 0.425; R3_C_tw2021_panel.csv; R3_C_summary.md section 5 Reading -->

### G12. Colombia held-out states without case history

**Table S54. Embedding, control and excess gains without case history, Colombia, held-out states.**

<!-- src: R3_C_co_s2_nohist.csv pooled rows (pct_of_ref, lo95_pct, hi95_pct, p, mde_pct, wis_ref, C_star, selection_ref_wis, selection_cstar_wis); R3_C_co_s2_nohist_ladder.csv pooled wis_log, cov_80, cov_80_nonzero; Brazil comparison from T6b_nohist_estimands.csv / Table S42 -->
| Estimand | Colombia, held-out states: % (95% CI); p | Brazil, future years (Table S42) |
|---|---|---|
| Embedding gain, N3 → N4 | **−5.30 (−8.19 to −2.41); 0.0020** | +2.54; 0.13 |
| Control gain, N3 → N3 + C2 (coordinates, C\*) | **−2.08 (−3.47 to −0.69); 0.0072** | +3.30; <0.001 |
| Excess gain, N3 + C2 → N4 + C2 | **−4.17 (−6.45 to −1.90); 0.0019** | −0.43; 0.58 |
| Static history, N3 → N3 + C1 | **−1.46 (−2.90 to −0.03); 0.047** | – |
| Excess gain beyond C1, N3 + C1 → N4 + C1 | **−3.46 (−6.13 to −0.79); 0.016** | – |

<!-- src: R3_C_co_s2_nohist_ladder.csv -->
| Model (row mean, 319,930 rows) | N3 | N3 + C1 | N3 + C2 | N4 | N4 + C1 | N4 + C2 |
|---|---|---|---|---|---|---|
| WIS | 0.1989 | 0.2019 | 0.2030 | 0.2096 | 0.2089 | 0.2115 |
| 80% coverage, all rows / cases > 0 | 0.91 / 0.64 | 0.90 / 0.64 | 0.89 / 0.62 | 0.88 / 0.63 | 0.87 / 0.62 | 0.88 / 0.63 |

Note: % of the WIS of N3 (week-weighted 0.1997), horizons 1 and 4, test years 2020 to 2022, seed 0, Colombia's shared configuration. The control was selected at 2019 by the main selection rule among C2, C3, C4 and C4s. Coordinates (C2) were the only member of the tie set (0.33733 vs 0.34366 for C4 and 0.34467 for C3), although they did not beat N3 (0.33728). The minimum detectable excess gain is 3.18%. The control share cannot be estimated, because the embedding gain is negative. Exploratory, outside the primary family. Bold: CI excludes zero. <!-- src: R3_C_co_s2_nohist.csv mde_pct 3.177, wis_ref 0.19966; R3_C_summary.md section 6 Selection -->

The Brazilian pattern without case history did not appear in Colombia. In Colombia's held-out states without case history, the embeddings made forecasts clearly worse (about −4% to −5%), with or without a location control, and neither coordinates nor static history helped N3. In both countries the embeddings added nothing beyond a location control. There are only three test years and five folds, and place inputs generally reduced accuracy in held-out Colombian states. The results without case history therefore differ between countries, are exploratory and say little about mechanism. <!-- src: R3_C_summary.md section 6 Reading; TRIAGE_round3.md Addendum 5 -->

### G13. Equal-budget tuning

**Table S55. Excess gain in Colombia, future years, with each model tuned separately on an equal grid.**

<!-- src: R3_C_tuning.csv (G_excess_tuned, G_excess_shared, tuning_gain_L3C, tuning_gain_L4C); R3_C_summary.md section 4 (chosen configurations, validation losses) -->
| Model | Configuration chosen (leaves / minimum rows per leaf / feature fraction) | Validation pinball loss, 2019 | Excess gain, % (95% CI); p |
|---|---|---|---|
| L3 + C1, tuned separately | 31 / 100 / 0.9 | 0.07114 | – |
| L4 + C1, tuned separately | 31 / 100 / 0.9 | 0.07174 | – |
| Best for each | – | – | −0.39 (−0.58 to −0.19); 0.0011 |
| Shared configuration (primary, seed 0) | 31 / 100 / 0.9 | – | −0.39 (−0.58 to −0.19); 0.0011 |

Note: Grid of 18 configurations (leaves 15, 31, 127; minimum rows per leaf 100, 1,000, 5,000; feature fraction 0.3, 0.9; 400 rounds), trained on 2018 and validated on 2019. The second-best setting was 15 / 100 / 0.9 for both models (+0.6% and +0.4% validation loss). Seed 0. <!-- src: R3_C_summary.md section 4 -->

Tuned separately on the same grid, each model chose the shared configuration. The test-year forecasts were therefore exactly the same as the shared ones, and the excess gain was unchanged (−0.39%). In Colombia the loss does not come from using one shared configuration. <!-- src: R3_C_tuning.csv tuning_gain_L3C 0, tuning_gain_L4C 0; R3_C_summary.md section 4 Result -->

### G14. Zero-fill stress test (added during the final author review)

Unlike the other analyses in this section, this one was added after all 14 comparisons had been read, at a co-author's request (row 54 of Table S14 in the Supplementary Methods). It asks how many cases hidden by zero-filling it would take to remove each loss. Nothing was refitted: the stored forecasts of both models were rescored against changed targets.

**Table S56. Zero-fill stress test: excess gain when a share of zero-filled test weeks is changed to 1 or 3 cases.**

<!-- src: docs/results/review/R5_zero_fill_stress.csv (commit 40d7faf), rows BR_S5, CO_S1, CO_S2, CO_S3, CO_S4, TW_S5. Column 2: exc_pct_s0 (= T1_primary_family.csv pct_of_WIS_ref) and T1 Holm_p. Columns 3 and 4: exc_pct_median at s_pct 2.1 and 10.0, k 1. Column 5: exc_share_holm_sig_loss × R (R = 20) at s_pct 2.1, k 1 / k 3. Column 6: exc_tipping_s_pct, k 1 / k 3. Design: R5_zero_fill_stress.md, Method and Tipping shares. -->
| Comparison | Excess gain as reported, % (Holm p) | Median excess gain (%), 2.1% of filled weeks changed, 1 case | Median excess gain (%), 10% changed, 1 case | Draws with a Holm-significant loss at 2.1% (of 20), 1 / 3 cases | Tipping share, %, 1 / 3 cases |
|---|---|---|---|---|---|
| Brazil, held-out country | −0.68 (<0.001) | −0.60 | −0.27 | 20 / 20 | 10 / 10 |
| Colombia, future years | −0.42 (0.014) | −0.34 | −0.01 | 16 / 10 | 5 / 2.1 |
| Colombia, held-out states | −0.52 (0.003) | −0.42 | −0.02 | 20 / 20 | 5 / 5 |
| Colombia, held-out regions | −0.68 (0.030) | −0.53 | +0.01 | 0 / 0 | 2 / 2 |
| Colombia, held-out districts | −0.45 (0.019) | −0.35 | +0.01 | 6 / 0 | 2 / 2 |
| Taiwan, held-out country | −18.29 (0.035) | −15.54 | −5.19 | 0 / 0 | 2 / 2 |

Note: The six comparisons with a loss in Table 2. Rows, exclusions, seeds and tests as in Table 2 (horizons 1 and 4 pooled; forecasts whose origin lies in the target's epidemiological year; Holm adjustment over the 14 comparisons). In each draw, a share of the zero-filled district-weeks in the test years is changed from 0 to 1 or 3 cases; weeks the source listed as 0 are never changed. A changed week changes at both horizons, for all four models and every seed, and the stored forecasts are rescored; no model is refitted. The shares were 0.5%, 1%, 2%, 2.1%, 5% and 10%, with 20 draws for each share and case count. Weeks were drawn uniformly at random within each comparison. Within a draw, the weeks changed at a smaller share are also changed at every larger share, and the same weeks are used for 1 and 3 cases. Percentages use the unperturbed reference WIS as the denominator, and gains are medians over draws. Each draw is tested with the main test, with Holm adjustment over the 14 comparisons within that draw. The tipping share is the smallest share tested at which the loss is no longer Holm-significant in at least half of the draws; because Holm is applied within each draw, a loss can also tip when the other losses weaken at the same time. The benchmark is Brazil's check against InfoDengue, in which at most 2.1% of filled weeks in a sampled year held a probable case and none held more than 8 (Table S4); 8 cases per week was not tested. The test changes only the scored targets. Hidden cases would also have entered the case-history inputs and the training targets of both models, which are not changed, and district-level rates of hidden cases in Colombia and Peru remain unknown. <!-- src: R5_zero_fill_stress.md, Method (candidates = zero-filled targets; s in {0.5, 1, 2, 2.1, 5, 10}%; k in {1, 3}; R = 20; nested selection; denominator = unperturbed WIS(L3); ewc_inference + Holm within draw index; tipping rule); "k = 8 ... was not run" (Interpretation) -->

At Brazil's highest observed rate of 2.1%, all six losses shrank by 13% to 22%, and each stayed significant before adjustment in every draw. After Holm adjustment, only the losses with Brazil held out and in Colombia's held-out states stayed significant in every draw; at 10%, no loss did, and the four Colombian losses were close to zero while those with Brazil and Taiwan held out stayed negative. Brazil's benchmark applies directly to the comparison with Brazil held out, Taiwan's filled weeks held no local case in the surveillance data (Supplementary Methods, section A4), and Colombia's rate is unknown. <!-- src: R5_zero_fill_stress.csv s_pct 2.1: 1 − exc_pct_median / exc_pct_s0 from 12.5% (BR_S5, k 1) to 22.0% (CO_S4, k 1); exc_share_p05_loss = 1 for all six, k 1 and 3; exc_share_holm_sig_loss as in column 5; s_pct 10: exc_share_holm_sig_loss = 0, exc_pct_median CO_S1–CO_S4 −0.09 to +0.01 (k 1 and 3), BR_S5 −0.27 / −0.27, TW_S5 −5.19 / −4.46; S1_supplement_methods.md A4, Taiwan vs Taiwan CDC ("no absent township-week holds a local case") -->

The other eight comparisons, the other shares, every result for 3 cases and the embedding gain are in the results file docs/results/review/R5_zero_fill_stress.csv. No comparison became a Holm-significant gain at any share, for the excess gain or the embedding gain. <!-- src: R5_zero_fill_stress.csv exc_share_holm_sig_gain = 0 and emb_share_holm_sig_gain = 0 in all 182 rows; the only gain significant before adjustment is CO_S5 at 10% (exc_pct_median +0.39 / +0.35, exc_p_median 0.015 / 0.017, exc_holm_p_median 0.22 / 0.23) -->

## H. Supplementary figures

**Figure S1. Forecast error along the model ladder in the future-years split (S1), by country.** <!-- figure file: docs/results/figures/pub/FigS1.png --> The figure shows how much each model reduces mean WIS over rows compared with L1, the model with case history only (open marker at 0), with horizons 1 and 4 pooled. Models are L0 to L4 and L3 and L4 with the selected location control, which is average past cases (C1) in every country. Values beyond a panel are drawn as an arrow with their value; this applies to the seasonal naive model L0 everywhere. Panels have their own scales. <!-- src: T2_ladder.csv `WIS pooled h{1,4}`, n_rows (Taiwan includes 2021, 141,645 rows); caption text from docs/results/figures/pub/CAPTIONS.md (regenerated 2026-11-20) -->

**Figure S2. Excess gain by test year.** <!-- figure file: docs/results/figures/pub/FigS2.png --> Each point is one comparison in one test year, shown as a percentage of that year's reference WIS (weeks weighted equally) with horizons 1 and 4 pooled. Bars are unadjusted 95% confidence intervals; a filled marker means the interval excludes 0, and the marker shape gives the split. Shading marks the COVID-19 pandemic years 2020–2021. In the Taiwan panel only 2020 is shaded, and 2021 is labelled "no local cases". Intervals running past a panel are cut with an arrowhead. Taiwan includes 2021, when there were no local cases, so its reference WIS is tiny and its percentages are very large (absolute values in Table S30). Panels have their own scales. <!-- src: S8_per_year.csv; caption text from docs/results/figures/pub/CAPTIONS.md (regenerated 2026-11-20) -->

**Figure S3. Excess gain by embedding similarity when a whole country is held out (S5).** <!-- figure file: docs/results/figures/pub/FigS3.png --> The districts of the held-out country are split into fifths by how similar their rescaled AlphaEarth embedding for year y − 1 is to that of the most similar training district (cosine similarity). Points show each fifth's mean similarity and its excess gain as a percentage of the comparison's overall reference WIS, with 95% confidence intervals. ρ is the Spearman correlation between similarity and excess gain across districts; its p values, which treat districts as independent, are in Table S39. Panels have their own vertical scales. Exploratory. <!-- src: S7b_embedding_distance_bins.csv cos_max_mean, G_excess_pct_cell, G_excess_lo95_pct_cell, G_excess_hi95_pct_cell; S7_embedding_distance.csv spearman_rho, n_units; caption text from docs/results/figures/pub/CAPTIONS.md (regenerated 2026-11-20) -->

**Figure S4. How well district dengue burden can be predicted from embeddings, coordinates and static covariates in states not used for fitting.** <!-- figure file: docs/results/figures/pub/FigS4_info_probe.png --> Bars show the out-of-fold R² of a small LightGBM predicting each district's mean log(1 + weekly cases) over 2014 to 2019, under five-fold cross-validation that holds out whole states. Whiskers are 95% CIs from 1,000 bootstrap resamples of states. Grey bars use no embeddings: coordinates with spherical harmonics (G, light grey), the static covariates of L3 (S, mid grey) and both (G + S, dark grey). Purple bars use the 2018 AlphaEarth embeddings, alone (E, solid) or added to coordinates and static covariates (G + S + E, hatched). The axis is cut at −0.5, and whiskers that run below it end in an arrowhead. This affects Peru G and all of Taiwan, whose bootstrap is unstable because resamples without Kaohsiung and Tainan have almost no variance. Exploratory and cross-sectional; ridge regression results and the added R² with CIs are in Table S50. <!-- src: docs/results/review/R3_E1_info_probe.csv (target T1, scheme grouped_state, model lgbm, quantity R2, fsets G, S, G+S, E, G+S+E); caption text from docs/results/figures/pub/CAPTIONS.md (regenerated 2026-11-20) -->

