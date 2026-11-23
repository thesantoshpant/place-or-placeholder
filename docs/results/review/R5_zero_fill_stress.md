# R5: zero-fill stress test (hidden cases in filled weeks)

Scoring-only sensitivity analysis; no model was refitted. Script: `scripts/analysis/zero_fill_stress.py`; table: `docs/results/review/R5_zero_fill_stress.csv`.

## Question

Outside the source's listed weeks, every district-week was set to 0 cases. If some of these filled weeks really held a few unreported cases, how far would the 14 primary comparisons move?

## Method

- **Rows and scoring** are those of the primary analysis (Table 2; `configs/primary_cells.yaml`, 3-seed means where seeds exist): exclusions v2, origin-year row filter, horizons 1 and 4 pooled, each target week weighted equally, WIS on log(1 + cases) with the median and deciles. The rows are built with the results kit's own code (`estimands_report.load_cell`, `rk_compute`).
- **Candidates** are district-weeks whose target was zero-filled (absent from the source). Weeks the source listed as 0 are never changed.
- **Perturbation.** In each comparison a random share s of the candidate district-weeks is set to k cases (y = log(1 + k)); s in {0.5%, 1%, 2%, 2.1%, 5%, 10%} (2.1% = the Brazil benchmark, added to the grid) and k in {1, 3}. A changed district-week changes at both horizons, for all four models and every seed. R = 20 draws per (s, k) with fixed seeds (`default_rng([20261122, crc32(comparison), r])`); within a draw the selected sets are nested across s and identical for k = 1 and 3.
- **Rescoring.** WIS at y = 0, 1 and 3 cases was recomputed from the stored quantile forecasts (`pop.eval.scoring.wis_interval`) and passed through the same kit pipeline, so each row's gain follows the common-seed rule. Each draw's weekly gain series is tested with the main test (`pop.eval.stats.ewc_inference`, DM with EWC variance and HLN correction); Holm is applied over the 14 comparisons within each draw index (`pop.eval.stats.holm`).
- **Percentages** are 100 x gain / unperturbed WIS(L3), so the denominator is fixed. The CSV also gives the median with the perturbed WIS(L3) (`*_pct_pert_ref_median`).
- **Tipping share** = the smallest s at which the loss is no longer Holm-significant in at least half of the 20 draws. Holm is applied within each draw, so a comparison's adjusted p also rises when the other losses weaken at the same time; the same rule without Holm (unadjusted p < .05) is reported beside it. The CSV also gives the exact share at which the *expected* gain reaches 0 (`*_zero_cross_s_pct`; the estimate is linear in the selection).
- **Scope limits.** Only the scored targets change. Hidden cases would also have entered the case-history inputs and the training targets; this test cannot show that. Placement is uniform within each comparison.

## Sanity check: s = 0 reproduces Table 2 (T1_primary_family.csv)

| Comparison | T1 excess gain % [95% CI] | Recomputed % [95% CI] | T1 Holm p | Recomputed Holm p | Rows T1 / here |
|---|---|---|---|---|---|
| BR S1 | +0.2321 [-0.3275, +0.7917] | +0.2321 [-0.3275, +0.7917] | 1 | 1 | 2,703,183 / 2,703,183 |
| BR S2 | -0.0008 [-0.3392, +0.3377] | -0.0008 [-0.3392, +0.3377] | 1 | 1 | 2,703,183 / 2,703,183 |
| BR S3 | -0.1579 [-0.3434, +0.0276] | -0.1579 [-0.3434, +0.0276] | 0.5273 | 0.5273 | 2,703,183 / 2,703,183 |
| BR S4 | +0.1979 [-0.3176, +0.7134] | +0.1979 [-0.3176, +0.7134] | 1 | 1 | 2,703,183 / 2,703,183 |
| BR S5 | -0.6806 [-0.9385, -0.4226] | -0.6806 [-0.9385, -0.4226] | 0.0005664 | 0.0005664 | 2,703,183 / 2,703,183 |
| CO S1 | -0.4227 [-0.6375, -0.2079] | -0.4227 [-0.6375, -0.2079] | 0.0143 | 0.0143 | 319,930 / 319,930 |
| CO S2 | -0.5223 [-0.7402, -0.3044] | -0.5223 [-0.7402, -0.3044] | 0.003402 | 0.003402 | 319,930 / 319,930 |
| CO S3 | -0.6849 [-1.0836, -0.2863] | -0.6849 [-1.0836, -0.2863] | 0.03038 | 0.03038 | 319,930 / 319,930 |
| CO S4 | -0.4451 [-0.6830, -0.2071] | -0.4451 [-0.6830, -0.2071] | 0.0188 | 0.0188 | 319,930 / 319,930 |
| CO S5 | +0.2174 [-0.1921, +0.6269] | +0.2174 [-0.1921, +0.6269] | 1 | 1 | 319,930 / 319,930 |
| PE S1 | -0.8152 [-1.4939, -0.1365] | -0.8152 [-1.4939, -0.1365] | 0.1777 | 0.1777 | 45,754 / 45,754 |
| PE S5 | +0.9322 [-0.1591, +2.0236] | +0.9322 [-0.1591, +2.0236] | 0.5273 | 0.5273 | 45,754 / 45,754 |
| TW S1 | -0.7145 [-1.3998, -0.0292] | -0.7145 [-1.3998, -0.0292] | 0.294 | 0.294 | 141,645 / 141,645 |
| TW S5 | -18.2896 [-29.7960, -6.7832] | -18.2896 [-29.7960, -6.7832] | 0.03512 | 0.03512 | 141,645 / 141,645 |

Largest absolute difference over the 14 comparisons: excess gain % 0.0e+00, CI bounds 0.0e+00, DM p 0.0e+00, Holm p 0.0e+00; embedding gain % 0.0e+00; row counts equal in 14 of 14. **Result: PASS.**

Other checks:
- WIS recomputed at the observed count from the forecast files matches the stored `wis_log` on all 125,120,432 forecasts of the 136 run directories (largest absolute difference 0.0e+00; NaN pattern mismatches 0).
- Rescoring at y = 0 reproduces the stored gains on every candidate row (largest absolute difference 0.0e+00).
- Two draws per comparison recomputed with `pop.eval.estimands.infer_estimand` on an explicitly perturbed frame agree with the fast path (largest absolute difference in estimate, p or CI bound 1.1e-15).

## Excess gain, k = 1 hidden case per changed week

Cells: median excess gain % over draws [2.5–97.5% range of draws]; share of draws with a Holm-significant loss (sig) and with the sign flipped (flip).

| Comparison | s = 0: % (Holm p) | s = 1% | s = 2.1% | s = 5% | s = 10% |
|---|---|---|---|---|---|
| BR S1 | +0.23 (1.000) | +0.24 [+0.24, +0.24]; sig 0.00, flip 0.00 | +0.25 [+0.25, +0.25]; sig 0.00, flip 0.00 | +0.28 [+0.27, +0.28]; sig 0.00, flip 0.00 | +0.32 [+0.32, +0.32]; sig 0.00, flip 0.00 |
| BR S2 | -0.00 (1.000) | +0.01 [+0.01, +0.01]; sig 0.00, flip 1.00 | +0.03 [+0.03, +0.03]; sig 0.00, flip 1.00 | +0.07 [+0.06, +0.07]; sig 0.00, flip 1.00 | +0.13 [+0.13, +0.14]; sig 0.00, flip 1.00 |
| BR S3 | -0.16 (0.527) | -0.13 [-0.13, -0.13]; sig 0.00, flip 0.00 | -0.11 [-0.11, -0.10]; sig 0.00, flip 0.00 | -0.03 [-0.04, -0.03]; sig 0.00, flip 0.00 | +0.10 [+0.09, +0.10]; sig 0.00, flip 1.00 |
| BR S4 | +0.20 (1.000) | +0.21 [+0.21, +0.21]; sig 0.00, flip 0.00 | +0.22 [+0.22, +0.22]; sig 0.00, flip 0.00 | +0.25 [+0.25, +0.26]; sig 0.00, flip 0.00 | +0.31 [+0.30, +0.31]; sig 0.00, flip 0.00 |
| BR S5 | -0.68 (0.001) | -0.64 [-0.64, -0.64]; sig 1.00, flip 0.00 | -0.60 [-0.60, -0.59]; sig 1.00, flip 0.00 | -0.48 [-0.48, -0.47]; sig 1.00, flip 0.00 | -0.27 [-0.28, -0.27]; sig 0.00, flip 0.00 |
| CO S1 | -0.42 (0.014) | -0.38 [-0.39, -0.38]; sig 1.00, flip 0.00 | -0.34 [-0.34, -0.33]; sig 0.80, flip 0.00 | -0.22 [-0.23, -0.20]; sig 0.00, flip 0.00 | -0.01 [-0.03, +0.00]; sig 0.00, flip 0.05 |
| CO S2 | -0.52 (0.003) | -0.47 [-0.48, -0.47]; sig 1.00, flip 0.00 | -0.42 [-0.42, -0.41]; sig 1.00, flip 0.00 | -0.27 [-0.28, -0.26]; sig 0.00, flip 0.00 | -0.02 [-0.03, -0.00]; sig 0.00, flip 0.05 |
| CO S3 | -0.68 (0.030) | -0.61 [-0.62, -0.61]; sig 0.90, flip 0.00 | -0.53 [-0.55, -0.53]; sig 0.00, flip 0.00 | -0.33 [-0.36, -0.32]; sig 0.00, flip 0.00 | +0.01 [-0.02, +0.04]; sig 0.00, flip 0.75 |
| CO S4 | -0.45 (0.019) | -0.40 [-0.40, -0.39]; sig 1.00, flip 0.00 | -0.35 [-0.36, -0.34]; sig 0.30, flip 0.00 | -0.22 [-0.23, -0.21]; sig 0.00, flip 0.00 | +0.01 [-0.00, +0.02]; sig 0.00, flip 0.85 |
| CO S5 | +0.22 (1.000) | +0.23 [+0.23, +0.24]; sig 0.00, flip 0.00 | +0.25 [+0.25, +0.26]; sig 0.00, flip 0.00 | +0.30 [+0.29, +0.31]; sig 0.00, flip 0.00 | +0.39 [+0.38, +0.40]; sig 0.00, flip 0.00 |
| PE S1 | -0.82 (0.178) | -0.79 [-0.80, -0.77]; sig 0.00, flip 0.00 | -0.75 [-0.77, -0.73]; sig 0.00, flip 0.00 | -0.67 [-0.70, -0.64]; sig 0.00, flip 0.00 | -0.53 [-0.58, -0.49]; sig 0.00, flip 0.00 |
| PE S5 | +0.93 (0.527) | +0.94 [+0.94, +0.94]; sig 0.00, flip 0.00 | +0.95 [+0.94, +0.95]; sig 0.00, flip 0.00 | +0.98 [+0.97, +0.99]; sig 0.00, flip 0.00 | +1.02 [+1.01, +1.03]; sig 0.00, flip 0.00 |
| TW S1 | -0.71 (0.294) | -0.69 [-0.73, -0.64]; sig 0.00, flip 0.00 | -0.65 [-0.69, -0.58]; sig 0.00, flip 0.00 | -0.54 [-0.59, -0.47]; sig 0.00, flip 0.00 | -0.37 [-0.47, -0.30]; sig 0.00, flip 0.00 |
| TW S5 | -18.29 (0.035) | -16.98 [-17.07, -16.88]; sig 1.00, flip 0.00 | -15.54 [-15.65, -15.37]; sig 0.00, flip 0.00 | -11.78 [-11.98, -11.58]; sig 0.00, flip 0.00 | -5.19 [-5.50, -4.97]; sig 0.00, flip 0.00 |

## Excess gain, k = 3 hidden cases per changed week

Cells: median excess gain % over draws [2.5–97.5% range of draws]; share of draws with a Holm-significant loss (sig) and with the sign flipped (flip).

| Comparison | s = 0: % (Holm p) | s = 1% | s = 2.1% | s = 5% | s = 10% |
|---|---|---|---|---|---|
| BR S1 | +0.23 (1.000) | +0.24 [+0.24, +0.24]; sig 0.00, flip 0.00 | +0.25 [+0.25, +0.25]; sig 0.00, flip 0.00 | +0.28 [+0.28, +0.28]; sig 0.00, flip 0.00 | +0.33 [+0.33, +0.34]; sig 0.00, flip 0.00 |
| BR S2 | -0.00 (1.000) | +0.01 [+0.01, +0.01]; sig 0.00, flip 1.00 | +0.03 [+0.02, +0.03]; sig 0.00, flip 1.00 | +0.06 [+0.06, +0.07]; sig 0.00, flip 1.00 | +0.13 [+0.12, +0.13]; sig 0.00, flip 1.00 |
| BR S3 | -0.16 (0.527) | -0.13 [-0.13, -0.13]; sig 0.00, flip 0.00 | -0.10 [-0.10, -0.10]; sig 0.00, flip 0.00 | -0.02 [-0.03, -0.02]; sig 0.00, flip 0.00 | +0.11 [+0.10, +0.11]; sig 0.00, flip 1.00 |
| BR S4 | +0.20 (1.000) | +0.21 [+0.21, +0.21]; sig 0.00, flip 0.00 | +0.22 [+0.22, +0.23]; sig 0.00, flip 0.00 | +0.26 [+0.26, +0.26]; sig 0.00, flip 0.00 | +0.32 [+0.32, +0.32]; sig 0.00, flip 0.00 |
| BR S5 | -0.68 (0.001) | -0.64 [-0.64, -0.64]; sig 1.00, flip 0.00 | -0.59 [-0.60, -0.59]; sig 1.00, flip 0.00 | -0.47 [-0.48, -0.47]; sig 1.00, flip 0.00 | -0.27 [-0.27, -0.26]; sig 0.00, flip 0.00 |
| CO S1 | -0.42 (0.014) | -0.38 [-0.39, -0.38]; sig 1.00, flip 0.00 | -0.34 [-0.35, -0.33]; sig 0.50, flip 0.00 | -0.22 [-0.23, -0.20]; sig 0.00, flip 0.00 | -0.01 [-0.04, -0.00]; sig 0.00, flip 0.05 |
| CO S2 | -0.52 (0.003) | -0.48 [-0.48, -0.47]; sig 1.00, flip 0.00 | -0.42 [-0.43, -0.41]; sig 1.00, flip 0.00 | -0.29 [-0.31, -0.28]; sig 0.00, flip 0.00 | -0.06 [-0.09, -0.04]; sig 0.00, flip 0.00 |
| CO S3 | -0.68 (0.030) | -0.63 [-0.63, -0.62]; sig 1.00, flip 0.00 | -0.56 [-0.57, -0.55]; sig 0.00, flip 0.00 | -0.39 [-0.41, -0.37]; sig 0.00, flip 0.00 | -0.09 [-0.12, -0.06]; sig 0.00, flip 0.00 |
| CO S4 | -0.45 (0.019) | -0.40 [-0.41, -0.39]; sig 1.00, flip 0.00 | -0.35 [-0.36, -0.34]; sig 0.00, flip 0.00 | -0.23 [-0.24, -0.21]; sig 0.00, flip 0.00 | -0.02 [-0.03, +0.00]; sig 0.00, flip 0.10 |
| CO S5 | +0.22 (1.000) | +0.23 [+0.22, +0.24]; sig 0.00, flip 0.00 | +0.24 [+0.23, +0.25]; sig 0.00, flip 0.00 | +0.28 [+0.27, +0.30]; sig 0.00, flip 0.00 | +0.35 [+0.33, +0.36]; sig 0.00, flip 0.00 |
| PE S1 | -0.82 (0.178) | -0.78 [-0.80, -0.76]; sig 0.00, flip 0.00 | -0.75 [-0.77, -0.72]; sig 0.00, flip 0.00 | -0.65 [-0.69, -0.61]; sig 0.00, flip 0.00 | -0.50 [-0.56, -0.45]; sig 0.00, flip 0.00 |
| PE S5 | +0.93 (0.527) | +0.94 [+0.94, +0.95]; sig 0.00, flip 0.00 | +0.96 [+0.95, +0.96]; sig 0.00, flip 0.00 | +0.99 [+0.98, +1.00]; sig 0.00, flip 0.00 | +1.05 [+1.03, +1.07]; sig 0.00, flip 0.00 |
| TW S1 | -0.71 (0.294) | -0.69 [-0.73, -0.64]; sig 0.00, flip 0.00 | -0.65 [-0.70, -0.58]; sig 0.00, flip 0.00 | -0.54 [-0.60, -0.47]; sig 0.00, flip 0.00 | -0.38 [-0.49, -0.30]; sig 0.00, flip 0.00 |
| TW S5 | -18.29 (0.035) | -16.91 [-17.01, -16.80]; sig 1.00, flip 0.00 | -15.39 [-15.52, -15.19]; sig 0.00, flip 0.00 | -11.43 [-11.65, -11.21]; sig 0.00, flip 0.00 | -4.46 [-4.84, -4.25]; sig 0.00, flip 0.00 |

## Tipping shares (excess gain)

For the comparisons with a Holm-significant loss in Table 2. Tipping share = smallest s at which the loss is no longer significant in at least half the draws, with Holm over the 14 comparisons and without it (unadjusted p < .05); the last two columns give the share at which the expected excess gain reaches 0.

| Comparison | s = 0: % (Holm p) | Holm tipping, k = 1 | Holm tipping, k = 3 | Unadjusted tipping, k = 1 | Unadjusted tipping, k = 3 | Expected gain = 0 at s, k = 1 | Expected gain = 0 at s, k = 3 |
|---|---|---|---|---|---|---|---|
| BR S5 | -0.68 (0.0006) | tips at 10% | tips at 10% | > 10% (still significant) | > 10% (still significant) | 16.71% | 16.47% |
| CO S1 | -0.42 (0.0143) | tips at 5% | tips at 2.1% | tips at 10% | tips at 10% | 10.32% | 10.46% |
| CO S2 | -0.52 (0.0034) | tips at 5% | tips at 5% | tips at 10% | tips at 10% | 10.31% | 11.32% |
| CO S3 | -0.68 (0.0304) | tips at 2% | tips at 2% | tips at 5% | tips at 10% | 9.77% | 11.53% |
| CO S4 | -0.45 (0.0188) | tips at 2% | tips at 2% | tips at 10% | tips at 10% | 9.81% | 10.33% |
| TW S5 | -18.29 (0.0351) | tips at 2% | tips at 2% | tips at 10% | tips at 10% | 13.97% | 13.26% |

## Embedding gain (secondary)

Same draws; Holm over the 14 comparisons as for the excess gain.

| Comparison | s = 0: % (Holm p) | k = 1, s = 2.1% | k = 1, s = 10% | k = 3, s = 2.1% | k = 3, s = 10% |
|---|---|---|---|---|---|
| BR S1 | +0.26 (1.000) | +0.28; sig loss 0.00, sig gain 0.00 | +0.35; sig loss 0.00, sig gain 0.00 | +0.28; sig loss 0.00, sig gain 0.00 | +0.36; sig loss 0.00, sig gain 0.00 |
| BR S2 | -0.02 (1.000) | +0.00; sig loss 0.00, sig gain 0.00 | +0.11; sig loss 0.00, sig gain 0.00 | +0.00; sig loss 0.00, sig gain 0.00 | +0.11; sig loss 0.00, sig gain 0.00 |
| BR S3 | -0.13 (1.000) | -0.08; sig loss 0.00, sig gain 0.00 | +0.11; sig loss 0.00, sig gain 0.00 | -0.08; sig loss 0.00, sig gain 0.00 | +0.12; sig loss 0.00, sig gain 0.00 |
| BR S4 | +0.22 (1.000) | +0.24; sig loss 0.00, sig gain 0.00 | +0.33; sig loss 0.00, sig gain 0.00 | +0.25; sig loss 0.00, sig gain 0.00 | +0.34; sig loss 0.00, sig gain 0.00 |
| BR S5 | -0.39 (1.000) | -0.25; sig loss 0.00, sig gain 0.00 | +0.28; sig loss 0.00, sig gain 0.00 | -0.23; sig loss 0.00, sig gain 0.00 | +0.40; sig loss 0.00, sig gain 0.00 |
| CO S1 | -0.38 (0.035) | -0.30; sig loss 0.00, sig gain 0.00 | +0.02; sig loss 0.00, sig gain 0.00 | -0.30; sig loss 0.00, sig gain 0.00 | -0.00; sig loss 0.00, sig gain 0.00 |
| CO S2 | -0.60 (0.001) | -0.49; sig loss 1.00, sig gain 0.00 | -0.07; sig loss 0.00, sig gain 0.00 | -0.50; sig loss 1.00, sig gain 0.00 | -0.11; sig loss 0.00, sig gain 0.00 |
| CO S3 | -0.82 (0.002) | -0.66; sig loss 1.00, sig gain 0.00 | -0.08; sig loss 0.00, sig gain 0.00 | -0.68; sig loss 1.00, sig gain 0.00 | -0.19; sig loss 0.00, sig gain 0.00 |
| CO S4 | -0.54 (0.005) | -0.44; sig loss 1.00, sig gain 0.00 | -0.07; sig loss 0.00, sig gain 0.00 | -0.44; sig loss 1.00, sig gain 0.00 | -0.09; sig loss 0.00, sig gain 0.00 |
| CO S5 | -0.04 (1.000) | -0.03; sig loss 0.00, sig gain 0.00 | +0.02; sig loss 0.00, sig gain 0.00 | -0.05; sig loss 0.00, sig gain 0.00 | -0.04; sig loss 0.00, sig gain 0.00 |
| PE S1 | -0.91 (0.143) | -0.86; sig loss 0.00, sig gain 0.00 | -0.67; sig loss 0.00, sig gain 0.00 | -0.85; sig loss 0.00, sig gain 0.00 | -0.65; sig loss 0.00, sig gain 0.00 |
| PE S5 | +0.68 (1.000) | +0.73; sig loss 0.00, sig gain 0.00 | +0.90; sig loss 0.00, sig gain 0.00 | +0.74; sig loss 0.00, sig gain 0.00 | +0.94; sig loss 0.00, sig gain 0.00 |
| TW S1 | -0.95 (0.147) | -0.86; sig loss 0.00, sig gain 0.00 | -0.53; sig loss 0.00, sig gain 0.00 | -0.86; sig loss 0.00, sig gain 0.00 | -0.52; sig loss 0.00, sig gain 0.00 |
| TW S5 | -21.60 (0.005) | -18.10; sig loss 1.00, sig gain 0.00 | -4.84; sig loss 0.00, sig gain 0.00 | -17.89; sig loss 1.00, sig gain 0.00 | -3.90; sig loss 0.00, sig gain 0.00 |

## Interpretation

Hidden cases moved the excess gain toward the embedding model in all 14 comparisons at every share, as expected, and no comparison became a Holm-significant gain; the only nominal gain was Colombia held out at 10% (+0.39%, unadjusted p = .02, Holm p = .22). At Brazil's benchmark of 2.1% of filled weeks, the losses with Brazil held out and in Colombia S2 stayed Holm-significant in every draw for both k, and Colombia S1 in 80% (k = 1) and 50% (k = 3) of draws; Colombia S3, Colombia S4 and Taiwan held out lost Holm significance from 2%, although their estimates shrank by only 15–22% and kept unadjusted p < .05 in every draw (part of this tipping comes from Holm itself, because all the losses weaken together). At 5% only the loss with Brazil held out stayed Holm-significant (about −0.48%), and at 10% none did: the within-Colombia estimates (S1–S4) were near zero (−0.09% to +0.01%), while Brazil held out (−0.27%) and Taiwan held out (−4.5% to −5.2%) stayed negative; the expected excess gain reaches zero at about 10–12% of filled weeks in Colombia, 13–14% with Taiwan held out and 16–17% with Brazil held out. One or three hidden cases per week gave almost the same numbers (k = 8, the 2023 maximum, was not run), so the share of filled weeks that hide cases matters more than how many cases they hide; because Colombia's filled weeks were checked only in aggregate, the within-Colombia losses stay Holm-significant only if fewer than about 2–5% of its filled weeks hid a case. The embedding gain (secondary) moved the same way in 13 of 14 comparisons (Colombia held out at k = 3 stayed at −0.04%) and never became a significant gain; its Holm-significant losses in Colombia S2–S4 and with Taiwan held out survived at 2.1% (Colombia S1 did not), and none survived at 10%.

Runtime: 9.2 min wall-clock in total (precompute 1.8 min, comparisons 7.4 min, report 0.0 min).
