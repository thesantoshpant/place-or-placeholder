# Brazil S1: L2 (+ climate) vs L1, LightGBM

Run: `runs/brazil_s1_L2` (config `configs/brazil_s1_L2.yaml`, 20 chunks, 3.1 h, n_train up to 1.73M, p = 74).
Analysis: `python scripts/run/analyze_run.py --runs runs/brazil_s1_baselines runs/brazil_s1_L2 --out runs/brazil_s1_L2/analysis --pairs lgbm-L2:lgbm-L1` (tables in `runs/brazil_s1_L2/analysis/`).
Every model is scored on the same 1,439,937 rows per horizon (5,517 units, test years 2020–24). No NaN scores and no flag_gap weeks in Brazil.
L2 tuning on the 2019 origin chose the same params as L1 (num_leaves 127, min_data_in_leaf 100).

## Headline
Adding ERA5-Land climate lowers log-WIS by only 0.3–0.8% (−0.0004 at h1 to −0.0016 at h4). None of the four DM tests is significant after Holm. Climate barely helps once 12 weeks of case lags and 3 seasons of seasonal lags are in the model.

## Mean log1p WIS, pooled 2020–24

| model | h1 | h2 | h3 | h4 | mean |
|---|---|---|---|---|---|
| L0 naive | 0.4645 | 0.4645 | 0.4645 | 0.4645 | 0.4645 |
| L1 NB | 0.1894 | 0.2102 | 0.2279 | 0.2454 | 0.2182 |
| L1 LightGBM | 0.1414 | 0.1628 | 0.1813 | 0.1992 | 0.1711 |
| **L2 LightGBM** | **0.1410** | **0.1621** | **0.1801** | **0.1975** | **0.1702** |

## Per test year (LightGBM)

| h | level | 2020 | 2021 | 2022 | 2023 | 2024 |
|---|---|---|---|---|---|---|
| 1 | L1 | 0.1237 | 0.0971 | 0.1484 | 0.1416 | 0.1963 |
| 1 | L2 | 0.1240 | 0.0970 | 0.1477 | 0.1413 | 0.1951 |
| 4 | L1 | 0.1671 | 0.1278 | 0.2101 | 0.1917 | 0.2996 |
| 4 | L2 | 0.1661 | 0.1276 | 0.2065 | 0.1914 | 0.2967 |

L2 is better in every year at h4. At h1 it is better in every year except 2020 (+0.0003). The largest gains are in 2022 and 2024.

## DM test, L2 − L1 (EWC + HLN; d = per-week mean log-WIS difference, T = 261 weeks)

| h | mean d | t | p | p Holm (12 tests in the table) | p Holm (4 L2-vs-L1 tests) |
|---|---|---|---|---|---|
| 1 | −0.0004 | −1.86 | 0.082 | 0.109 | 0.109 |
| 2 | −0.0007 | −2.43 | 0.027 | 0.109 | 0.109 |
| 3 | −0.0012 | −2.41 | 0.028 | 0.109 | 0.109 |
| 4 | −0.0016 | −2.25 | 0.039 | 0.109 | 0.109 |

The raw p-values are < 0.05 at h2–h4, but none survives Holm under either family. (`--pairs` was added to `analyze_run.py` for this table.)

## Coverage (nominal 0.40 / 0.80)

| model | 40% all | 80% all | 40% cases>0 | 80% cases>0 |
|---|---|---|---|---|
| L1 LightGBM | 0.781 | 0.907 | 0.312 | 0.677 |
| L2 LightGBM | 0.774 | 0.904 | 0.306 | 0.667 |

Only 26.2% of targets are non-zero. Both levels over-cover zero targets and under-cover non-zero targets, and climate does not fix this. 80% coverage on cases>0 by year for L2 is 0.665 / 0.629 / 0.655 / 0.669 / 0.691 (2020–24).

## zero_filled vs observed targets (mean log1p WIS, all horizons)

| model | observed | zero_filled |
|---|---|---|
| L1 LightGBM | 0.3181 | 0.0407 |
| L2 LightGBM | 0.3159 | 0.0408 |

The whole gain comes from observed (reported) weeks. On zero-filled weeks L2 is equal to L1 or slightly worse (by year: 2020 0.0022 vs 0.0016, 2024 0.0676 vs 0.0659). The zero-filled share is 0.26 / 0.32 / 0.73 / 0.74 / 0.61 for 2020–24. NB is still the best model on zero-filled rows (0.026).

Case-scale WIS (h1–h4): L1 2.320 / 2.892 / 3.376 / 3.865, L2 2.309 / 2.887 / 3.359 / 3.845.
