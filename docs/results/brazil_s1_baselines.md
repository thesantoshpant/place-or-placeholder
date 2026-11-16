# Brazil S1 baselines + TimesFM 2.5 zero-shot

Runs: `runs/brazil_s1_baselines` (L0 seasonal naive, L1 NB GLM, L1 LightGBM quantile) and `runs/brazil_s1_timesfm_zs`. Test years 2020–2024, origins within each year, h = 1..4, 5,517 municipalities.
Reproduce: `python scripts/run/analyze_run.py --runs runs/brazil_s1_baselines runs/brazil_s1_timesfm_zs`. The full tables and CSVs are in `runs/brazil_s1_baselines/analysis/`.

**Scoring.** All four models go through `pop.eval.scoring.score_forecasts` with the same nine deciles (0.1..0.9). TimesFM is scored from its case-scale `value`. The primary metric is mean WIS on log1p. Every model is restricted to the common key set (test_year, unit, origin, target, horizon): 1,439,937 rows per model and horizon, identical for all four. No scores are NaN and no flag_gap weeks are excluded (Brazil has none). On disk, forecasts.parquet is 165 MiB for the baselines and 399 MiB for TimesFM (the TimesFM file also stores `value_log`).

## (a) Mean log1p WIS, pooled 2020–24

| model | h1 | h2 | h3 | h4 |
|---|---|---|---|---|
| L0 naive | 0.4645 | 0.4645 | 0.4645 | 0.4645 |
| L1 NB | 0.1894 | 0.2102 | 0.2279 | 0.2454 |
| **L1 LightGBM** | **0.1414** | **0.1628** | **0.1813** | **0.1992** |
| TimesFM 2.5 ZS | 0.1594 | 0.1829 | 0.2051 | 0.2252 |

## (b) By test year (h=1 / h=4)

| model | 2020 | 2021 | 2022 | 2023 | 2024 |
|---|---|---|---|---|---|
| L0 | .439/.439 | .350/.350 | .415/.415 | .466/.466 | .654/.654 |
| NB | .160/.203 | .121/.151 | .195/.253 | .186/.237 | .286/.383 |
| LGBM | .124/.167 | .097/.128 | .148/.210 | .142/.192 | .196/.300 |
| TimesFM | .139/.186 | .107/.137 | .167/.238 | .158/.211 | .227/.356 |

LightGBM is best in every year and at every horizon, and L0 never beats it. 2024, the record epidemic, is the hardest year for every model.

## (c) Case-scale WIS

| model | h1 | h2 | h3 | h4 |
|---|---|---|---|---|
| L0 | 8.41 | 8.41 | 8.41 | 8.41 |
| NB | 327 | 434 | 475 | 458 |
| LGBM | 2.32 | 2.89 | 3.38 | 3.87 |
| TimesFM | **1.85** | **2.50** | **3.08** | **3.68** |

On the case scale, TimesFM edges out LightGBM. NB's case-scale WIS is broken by a few mean explosions: one unit (3550308, São Paulo city, 2024) reaches WIS ≈ 3×10⁷, and the 100 worst rows account for 56% of NB's case-scale total. The log-link GLM extrapolates badly at epidemic peaks.

## (d) Coverage (nominal 0.40 / 0.80)

| model | all targets | cases > 0 (26.2% of targets) |
|---|---|---|
| L0 | 0.643 / 0.773 | 0.043 / 0.400 |
| NB | 0.829 / 0.937 | 0.355 / 0.762 |
| LGBM | 0.781 / 0.907 | 0.312 / 0.677 |
| TimesFM | 0.617 / 0.810 | 0.267 / 0.593 |

Coverage over all targets looks good only because of the zeros. On non-zero targets every model under-covers. LightGBM's 80% coverage on these targets sits between 0.64 and 0.69 in every year.

## (e) Zero-filled vs observed targets (log-WIS)

| model | observed | zero_filled |
|---|---|---|
| L0 | 0.820 | 0.149 |
| NB | 0.435 | **0.026** |
| LGBM | **0.318** | 0.041 |
| TimesFM | 0.355 | 0.050 |

The share of zero-filled targets jumps from 0.26–0.32 in 2020–21 to 0.73, 0.74 and 0.61 in 2022–24. On zero-filled targets, LightGBM's log-WIS rises from about 0.002 (2020–21) to 0.044–0.066 (2022–24), and in 2022+ it is worse there than NB. These rows dilute the pooled means, so year-to-year comparisons partly reflect the zero-fill share.

## (f) DM tests (EWC + HLN, T = 261 weeks, Holm over 16 tests)

| A vs B | mean d (h1 → h4) | max p_holm | verdict |
|---|---|---|---|
| LGBM − L0 | −0.323 → −0.265 | 3e-4 | LGBM better at all h |
| LGBM − NB | −0.048 → −0.046 | 1.5e-3 | LGBM better at all h |
| LGBM − TimesFM | −0.018 → −0.026 | 1.5e-3 | LGBM better at all h |
| TimesFM − L0 | −0.305 → −0.239 | 3e-4 | TimesFM better at all h |

## (g) Per-unit LGBM vs L0

LightGBM has the lower mean log-WIS in 99.98% of units (5,516 of 5,517, all horizons pooled; 100% at h1 and 99.7% at h4). The median per-unit difference is −0.215 (from −0.241 at h1 to −0.190 at h4).
