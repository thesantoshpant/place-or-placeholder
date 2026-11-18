# RD: scoring-only reviewer analyses (no refits)

Script: `scripts/analysis/review_more.py` (tests `tests/test_review_more.py`, 10 pass). Run per cell:
`nice -n 19 python scripts/analysis/review_more.py run --cells <ID>` then `... combine`. Per-cell files are in `RD_cells/`.
Scope: the 13 available primary cells (BR S4 is still pending; rerun with `--cells BR_S4` when it lands). Rows are the primary rows: default exclusions, horizons {1,4} pooled, seed-averaged (BR S1 = 3 seeds). Inference is the primary estimator (equal-week pooling, DM/EWC + HLN, margin 1% of WIS(L3)). Values are % of WIS(L3) with 95% CI. Classes: equiv/infer/super/incon.
Integrity: WIS recomputed from forecasts.parquet equals scores.parquet to ≤2e-15 in every cell, and no forecast row is missing (`RD_forecast_check.csv`). Each cell's primary G_excess reproduces the kit value (`RD_cells/*_info.json`).

## 1. S1 baselines (`RD_baselines.csv`)
Pooled h{1,4} mean log-WIS (relative WIS vs L0, the seasonal naive = same week last year), then 80% coverage overall/positive weeks. Rows = keys scored by every model listed.

| model | BR_S1 | CO_S1 | PE_S1 | TW_S1 |
|---|---|---|---|---|
| L0 (seasonal naive) | 0.4645 (1.000); 0.77/0.40 | 0.3286 (1.000); 0.81/0.53 | 0.6541 (1.000); 0.73/0.47 | 0.0885 (1.000); 0.95/0.00 |
| NB GLM (L1) | 0.2174 (0.468); 0.94/0.76 | 0.1439 (0.438); 0.96/0.81 | 0.3245 (0.496); 0.93/0.84 | 0.0571 (0.645); 0.98/0.42 |
| TimesFM 2.5 zero-shot | 0.1923 (0.414); 0.82/0.59 | missing | missing | missing |
| LightGBM L1 | 0.1703 (0.367); 0.91/0.68 | 0.1237 (0.376); 0.93/0.72 | 0.2454 (0.375); 0.84/0.69 | 0.0380 (0.429); 0.98/0.25 |
| LightGBM L2 | 0.1692 (0.364); 0.90/0.67 | 0.1235 (0.376); 0.93/0.72 | 0.2442 (0.373); 0.83/0.68 | missing |
| LightGBM L2 (per-level tuned) | missing | missing | missing | 0.0465 (0.526); 0.97/0.05 |
| LightGBM L3 | 0.1684 (0.363); 0.90/0.66 | 0.1231 (0.375); 0.93/0.71 | 0.2448 (0.374); 0.83/0.67 | 0.0383 (0.433); 0.98/0.26 |
| LightGBM L4 | 0.1679 (0.362); 0.90/0.66 | 0.1235 (0.376); 0.93/0.71 | 0.2469 (0.377); 0.83/0.67 | 0.0387 (0.437); 0.98/0.25 |
| LightGBM L3+C* | 0.1684 (0.363); 0.90/0.66 | 0.1232 (0.375); 0.92/0.71 | 0.2454 (0.375); 0.83/0.66 | 0.0386 (0.436); 0.98/0.25 |
| LightGBM L4+C* | 0.1679 (0.362); 0.90/0.66 | 0.1237 (0.376); 0.93/0.71 | 0.2470 (0.378); 0.83/0.67 | 0.0387 (0.438); 0.98/0.25 |

- **Missing:** TimesFM zero-shot exists for Brazil only. Taiwan has no shared-params L2 (`taiwan_s1_l2shared` has not run), so its L2 row is the per-level-tuned run and is not comparable.
- LightGBM L1 cuts WIS by 57–63% vs L0 (relative WIS 0.37–0.43) and beats NB (0.44–0.65) and TimesFM (BR 0.41).
- L1→L4+C* moves relative WIS by ≤0.01 in every country. This is the paper's point: the main model is competitive, and the location layers are second-order.
- NB has the best positive-week coverage (0.76–0.84) but much worse WIS.

## 2. Weighted WIS (`RD_weighted.csv`)
Two weightings inside each (h, week) mean: unit population in the target year, and the unit's mean weekly cases in 2013–17 + 1.

| cell | unweighted | population | pre_cases_plus1 |
|---|---|---|---|
| BR_S1 | +0.26 [-0.38, +0.90] equiv | +0.06 [-0.45, +0.58] equiv | -0.10 [-0.57, +0.37] equiv |
| BR_S2 | +0.02 [-0.37, +0.41] equiv | -0.15 [-0.58, +0.28] equiv | -0.21 [-0.67, +0.25] equiv |
| BR_S3 | -0.13 [-0.38, +0.12] equiv | -0.39 [-0.91, +0.13] equiv | -0.56 [-1.04, -0.08] equiv |
| BR_S5 | -0.63 [-0.88, -0.39] equiv | -0.54 [-1.09, +0.00] equiv | -0.45 [-1.01, +0.10] equiv |
| CO_S1 | -0.39 [-0.58, -0.20] equiv | -1.02 [-1.53, -0.51] infer | -0.72 [-1.20, -0.25] infer |
| CO_S2 | -0.48 [-0.69, -0.27] equiv | -0.53 [-1.13, +0.06] incon | -0.40 [-0.89, +0.10] equiv |
| CO_S3 | -0.68 [-1.07, -0.29] infer | -1.41 [-2.23, -0.59] infer | -0.44 [-0.93, +0.05] equiv |
| CO_S4 | -0.44 [-0.68, -0.20] equiv | -0.69 [-1.39, +0.01] incon | -0.56 [-1.22, +0.11] incon |
| CO_S5 | +0.18 [-0.21, +0.58] equiv | +0.47 [-0.05, +0.98] equiv | +0.43 [+0.02, +0.85] equiv |
| PE_S1 | -0.62 [-1.35, +0.12] incon | -1.07 [-2.89, +0.75] incon | -3.82 [-6.26, -1.38] infer |
| PE_S5 | +1.01 [+0.02, +2.00] super | -1.12 [-2.78, +0.54] incon | -0.72 [-1.85, +0.42] incon |
| TW_S1 | -0.39 [-1.00, +0.22] equiv | -0.64 [-1.55, +0.27] incon | -0.55 [-1.38, +0.28] incon |
| TW_S5 | -11.53 [-15.83, -7.23] infer | -9.37 [-13.61, -5.13] infer | -6.34 [-10.36, -2.31] infer |

**Conclusion unchanged:** no cell shows a gain under either weighting.
- Weighting makes the Colombia and Peru harm *larger*: CO S1 −1.02% population-weighted and PE S1 −3.8% case-weighted, both inferior.
- PE S5's unweighted "superior" (+1.0%) does not survive either weighting (−1.1%, −0.7%).
- Brazil stays inside ±1% under both weightings.
- Some class labels flip, equivalent ↔ inconclusive/inferior. The ±1% equivalence verdicts in CO S1–S4 depend on the equal-unit weighting.

## 3. Outbreak weeks (`RD_outbreak.csv`)
Outbreak = cases ≥ max(unit p90 over 2013–2019, 5), the code's definition (`estimands_report.outbreak_threshold`). Note: this window includes the training years 2018–19, while the draft says "pre-training years". Align the text. `p_diff` tests the outbreak minus non-outbreak weekly series.

| cell | row_share | non_outbreak | outbreak | p_diff |
|---|---|---|---|---|
| BR_S1 | 0.08 | +0.01 [-0.22, +0.24] equiv | +0.15 [-0.77, +1.07] equiv | 0.734 |
| BR_S2 | 0.08 | +0.15 [-0.07, +0.37] equiv | -0.95 [-1.97, +0.07] incon | 0.056 |
| BR_S3 | 0.08 | +0.11 [-0.21, +0.43] equiv | -0.89 [-1.66, -0.12] infer | 0.023 |
| BR_S5 | 0.08 | -0.89 [-1.17, -0.61] infer | +0.80 [+0.15, +1.45] super | 0.006 |
| CO_S1 | 0.023 | -0.39 [-0.59, -0.19] equiv | -0.64 [-2.21, +0.93] incon | 0.458 |
| CO_S2 | 0.023 | -0.43 [-0.64, -0.22] equiv | -1.00 [-2.77, +0.78] incon | 0.29 |
| CO_S3 | 0.023 | -0.53 [-0.98, -0.08] equiv | -1.80 [-3.37, -0.22] infer | 0.04 |
| CO_S4 | 0.023 | -0.42 [-0.65, -0.19] equiv | -0.92 [-2.77, +0.94] incon | 0.351 |
| CO_S5 | 0.023 | +0.30 [-0.18, +0.77] equiv | -0.41 [-1.59, +0.76] incon | 0.407 |
| PE_S1 | 0.228 | -0.78 [-1.37, -0.20] infer | -1.05 [-2.65, +0.54] incon | 0.295 |
| PE_S5 | 0.228 | -1.08 [-1.71, -0.46] infer | +3.76 [+1.76, +5.75] super | 0.0 |
| TW_S1 | 0.008 | -0.89 [-2.18, +0.40] incon | -0.13 [-0.87, +0.62] equiv | 0.694 |
| TW_S5 | 0.008 | -14.26 [-19.31, -9.21] infer | +1.09 [-0.33, +2.51] incon | 0.049 |

- There is no consistent outbreak-week gain.
- In the **within-country spatial** cells (BR S2/S3, CO S3), AlphaEarth is worse on outbreak weeks: −0.9% to −1.8%, with BR S3 and CO S3 inferior.
- In the **cross-country** S5 cells (BR, PE, TW), the outbreak-week effect is positive (BR S5 +0.8%, PE S5 +3.8%, both superior) while the non-outbreak rows carry the harm. The PE S5 headline gain is entirely outbreak rows.
- BR S1: +0.15% on outbreak weeks, ns.
- These are exploratory per-stratum tests, with no multiplicity adjustment.

## 4. Causal recalibration (`RD_recal.csv`, `RD_recal_shifts.csv`)
Method:
- Separately for L3+C* and L4+C*, per horizon and seed, additive per-quantile shifts on the log1p scale are fitted only on earlier test years. Shift for level τ = τ-quantile of y − q_τ. The first test year is unadjusted, because no 2019-origin run exists for these models.
- Two variants: 'global', and 'mondrian' (shifts per bin of the forecast median).
- The table shows all years. `from_2nd_test_year` rows in the CSV drop the unadjusted year and give the same picture.

| cell | raw | global | mondrian |
|---|---|---|---|
| BR_S1 | +0.26 (equiv); pos-cov 0.66/0.66 | +0.26 (equiv); pos-cov 0.66/0.66 | +0.26 (equiv); pos-cov 0.68/0.68 |
| BR_S2 | +0.02 (equiv); pos-cov 0.65/0.65 | +0.02 (equiv); pos-cov 0.65/0.65 | +0.08 (equiv); pos-cov 0.68/0.68 |
| BR_S3 | -0.13 (equiv); pos-cov 0.65/0.65 | -0.13 (equiv); pos-cov 0.65/0.65 | -0.06 (equiv); pos-cov 0.68/0.68 |
| BR_S5 | -0.63 (equiv); pos-cov 0.62/0.63 | -0.57 (equiv); pos-cov 0.62/0.61 | -0.47 (equiv); pos-cov 0.67/0.66 |
| CO_S1 | -0.39 (equiv); pos-cov 0.71/0.71 | -0.39 (equiv); pos-cov 0.71/0.71 | -0.40 (equiv); pos-cov 0.70/0.71 |
| CO_S2 | -0.48 (equiv); pos-cov 0.71/0.70 | -0.48 (equiv); pos-cov 0.71/0.70 | -0.49 (equiv); pos-cov 0.70/0.70 |
| CO_S3 | -0.68 (infer); pos-cov 0.71/0.70 | -0.68 (infer); pos-cov 0.71/0.70 | -0.66 (equiv); pos-cov 0.70/0.70 |
| CO_S4 | -0.44 (equiv); pos-cov 0.71/0.70 | -0.44 (equiv); pos-cov 0.71/0.70 | -0.46 (equiv); pos-cov 0.70/0.70 |
| CO_S5 | +0.18 (equiv); pos-cov 0.75/0.75 | +0.18 (equiv); pos-cov 0.75/0.75 | +0.19 (equiv); pos-cov 0.73/0.73 |
| PE_S1 | -0.62 (incon); pos-cov 0.66/0.67 | -0.61 (incon); pos-cov 0.71/0.72 | -0.60 (incon); pos-cov 0.76/0.76 |
| PE_S5 | +1.01 (super); pos-cov 0.65/0.67 | +0.81 (incon); pos-cov 0.70/0.71 | -0.11 (equiv); pos-cov 0.76/0.76 |
| TW_S1 | -0.39 (equiv); pos-cov 0.25/0.25 | -0.39 (equiv); pos-cov 0.25/0.25 | -0.39 (equiv); pos-cov 0.25/0.25 |
| TW_S5 | -11.53 (infer); pos-cov 0.57/0.62 | -9.73 (infer); pos-cov 0.57/0.60 | -9.64 (infer); pos-cov 0.57/0.60 |

- **G_excess is essentially unchanged** in 11/13 cells (|Δ| ≤ 0.1 pp).
- Exceptions:
  - **PE S5 +1.01% (superior) → +0.81% (inconclusive, global) → −0.11% (equivalent, mondrian)**. Its one significant gain does not survive recalibration.
  - **TW S5 −11.5% → −9.6%**, still inferior.
- Recalibration barely helps positive-week coverage (BR 0.66→0.68, PE 0.66→0.76, CO none, TW none).
  - Global shifts are ~0 because *overall* 80% coverage is already ≥0.80 (0.83–0.98).
  - The positive-week shortfall is conditional on the outcome, and forecast-side bins cannot remove it. In Taiwan almost every forecast median is ~0.
- This is a limitation to state, not something cheap recalibration fixes.

## 5. Mechanism: upper quantiles on y = 0 rows (`RD_mechanism.csv`)
Columns:
- Δq0.9 = mean q0.9 of L4+C* minus L3+C* on y = 0 rows (weekly-series EWC CI).
- The zero-row contribution to G_excess is additive: per (h, week), zero rows' sum over all rows.
- "upper share" = the part of that contribution from τ ≥ 0.6; "q0.9 share" = from τ = 0.9.

| cell | zero_row_share | dq90_log_ci | dq90_case_ci | G_pct | zero_contrib_pct | upper_share_of_zero | q90_share_of_zero |
|---|---|---|---|---|---|---|---|
| BR_S1 | 0.738 | +0.006 [+0.001, +0.010] | +0.003 [-0.008, +0.014] | 0.261 | -0.243 | 0.76 | 0.218 |
| BR_S2 | 0.738 | +0.010 [+0.005, +0.016] | +0.002 [-0.006, +0.009] | 0.017 | -0.145 | 1.271 | 0.64 |
| BR_S3 | 0.738 | +0.029 [+0.020, +0.037] | +0.034 [+0.022, +0.045] | -0.13 | -0.42 | 1.176 | 0.624 |
| BR_S5 | 0.738 | +0.044 [+0.029, +0.059] | +0.061 [+0.030, +0.091] | -0.633 | -0.903 | 1.044 | 0.447 |
| CO_S1 | 0.785 | +0.018 [+0.010, +0.025] | +0.020 [+0.004, +0.036] | -0.391 | -0.595 | 1.002 | 0.418 |
| CO_S2 | 0.785 | +0.020 [+0.012, +0.027] | +0.018 [+0.003, +0.033] | -0.478 | -0.691 | 1.036 | 0.396 |
| CO_S3 | 0.785 | +0.026 [+0.018, +0.033] | +0.018 [-0.000, +0.036] | -0.683 | -0.766 | 1.109 | 0.466 |
| CO_S4 | 0.785 | +0.017 [+0.010, +0.025] | +0.018 [+0.004, +0.033] | -0.441 | -0.701 | 1.04 | 0.348 |
| CO_S5 | 0.785 | +0.007 [+0.001, +0.014] | +0.007 [-0.008, +0.022] | 0.185 | -0.046 | 3.393 | 2.283 |
| PE_S1 | 0.559 | +0.037 [+0.021, +0.053] | +0.057 [+0.031, +0.083] | -0.616 | -0.76 | 0.743 | 0.228 |
| PE_S5 | 0.559 | +0.018 [+0.011, +0.026] | +0.043 [+0.026, +0.060] | 1.008 | -0.333 | 0.663 | 0.309 |
| TW_S1 | 0.972 | +0.001 [-0.002, +0.005] | +0.001 [-0.003, +0.006] | -0.392 | -0.314 | 1.362 | 0.251 |
| TW_S5 | 0.972 | +0.097 [+0.070, +0.125] | +0.134 [+0.093, +0.174] | -11.53 | -12.671 | 0.975 | 0.673 |

- **L4+C* raises q0.9 on zero rows in 12/13 cells**, with the CI excluding 0. TW S1 is the exception, +0.001, ns.
- The size tracks the harm: TW S5 +0.10 log (+0.13 cases), BR S5 +0.044, PE S1 +0.037, BR S3 +0.029, CO +0.017–0.026, BR S1 +0.006.
- Zero rows carry the loss in every harmed cell: their contribution is −0.3% to −0.9% of WIS(L3), and −12.7% in TW S5.
- Quantiles above the median account for ~75–135% of that zero-row loss, so lower quantiles slightly offset it. q0.9 alone accounts for 22–67%.
- In BR S1 the net +0.26% comes from positive rows; zero rows still contribute −0.24%.
- CO S5's shares are unstable because its zero-row contribution is ~0. TW S1's are unstable because nothing is significant there.
- **Upshot:** the "inflated upper quantiles on zero weeks" mechanism is a measured finding in every country except TW S1, not only in TW S5.

## 6. Per test year (`RD_peryear.csv`)
G_excess, % of WIS(L3); * = p < .05 (per-year, unadjusted). Context flags are in the CSV.

| cell | 2020 | 2021 | 2022 | 2023 | 2024 |
|---|---|---|---|---|---|
| BR_S1 | -0.26 | -0.75 | +0.14 | +0.39 | +1.04 |
| BR_S2 | -0.43 | -0.75* | -0.07 | +0.29 | +0.51 |
| BR_S3 | -0.16* | -0.95* | -0.07 | -0.03 | +0.15 |
| BR_S5 | -0.64 | -1.76* | -0.67* | -0.47 | -0.25 |
| CO_S1 | -0.55* | -0.33 | -0.26 |  |  |
| CO_S2 | -0.57* | -0.56 | -0.31* |  |  |
| CO_S3 | -0.73 | -0.77* | -0.55* |  |  |
| CO_S4 | -0.66* | -0.43 | -0.19 |  |  |
| CO_S5 | +0.72 | -0.29 | -0.05 |  |  |
| PE_S1 | -1.39 | -1.10 | -0.54 | +0.24 |  |
| PE_S5 | +1.06 | +1.45 | +1.35* | +0.38 |  |
| TW_S1 | -15.71 |  | -0.23 | -0.04 | -1.94 |
| TW_S5 | -48.63* |  | -86.64* | -2.10 | -19.73* |

- **Brazil shows a clear trend:** AlphaEarth does worst in 2021 (COVID-era reporting; −0.75 to −1.76%, significant in S2/S3/S5) and best in the 2024 record epidemic (S1 +1.04%, S2 +0.51%; both ns).
- **Colombia** is uniformly slightly negative and largest in 2020–21.
- **Peru:** the 2023 record season is the only S1 year above 0 (+0.24, ns).
- **Taiwan's** large per-year % values come from tiny WIS(L3) denominators in the near-zero years 2020/2022/2024. 2023 (the outbreak year, nearly all test cases) is −0.04% (S1) and −2.1% (S5).
- No single year reverses a cell's sign in a way that changes the headline.

## Does any primary conclusion change?
No. "No genuine gain from AlphaEarth" holds under population/case weighting, on outbreak weeks, after causal recalibration and in every year. Points the writers should note:
- (a) The lone positive cell, PE S5, is fragile: it disappears under weighting and under mondrian recalibration, and comes only from outbreak rows.
- (b) Several "equivalent" labels in CO depend on equal-unit weighting. Population weighting makes CO S1/S3 inferior at about −1.0 to −1.4%.
- (c) The upper-quantile mechanism is now shown per cell (C13).
- (d) Positive-week under-coverage is not fixed by causal recalibration (C12). Report it as a limitation.
- (e) Fix the outbreak-definition wording (2013–2019 window).
