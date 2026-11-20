# RESULTS BRIEF (auto-generated, results kit v3)

Generated 2026-11-20 13:29 by `scripts/analysis/make_results.py`. Do not edit by hand: re-run the script. All numbers are log1p-scale WIS unless marked 'case scale'; a gain is positive when the second model has the lower WIS. Percentages are of WIS(L3) (WIS(N3) in the no-history arm).

**Scored rows (deviation row 24).** Every estimate keeps only rows whose forecast origin (target week − h) lies in the same epi-year as the target, which removes the yearly-feature and training-label look-ahead (review R1): at h1 the first epi-week of each test year is dropped (1.9% of rows), at h4 the first four (7.7%). T1 also shows G_excess on all rows ('all rows %').

**Horizons.** Every 'pooled' estimate pools the primary horizons **h{1,4}** in every cell (row 21); S1 cells also show a secondary pooling over h1-4 (`horizon = pooled_h1-4`), which is never in the Holm family and uses only test years scored at all four horizons.

**Inference.** DM test with EWC long-run variance and HLN correction on the weekly cross-unit mean loss difference; TOST against ±1% of WIS(L3); Holm over the 14-cell family (DM p and TOST p separately). Robustness columns: EWC with B = 4 cosine terms, IAAFT-surrogate-calibrated p (review RC), delta-method CI that treats WIS(L3) as estimated, case-scale G_excess. See `docs/methods/results_kit.md`.

**Exclusions (row 34).** Primary scoring uses `data/processed/exclusions_v2/`: v1 (units without geometry, incomplete weeks) plus every Espírito Santo row of every test year (target weeks from 2019-12-29) (the source has false zeros for all 78 municipalities while InfoDengue shows cases). Applied to all four models at scoring only; the models were not refitted, so 2020–23 training targets still contain these false zeros. T1 shows G_excess under the v1 exclusions ('v1 excl %').

**Taiwan (row 25).** Both Taiwan cells use test years 2020–2024 including 2021, a year with no local cases; the pre-review set (without 2021) is the sensitivity cell `TW_*_no2021`. A cell whose 2021 runs are not finished uses its base runs and is flagged '2021 pending'.

**Loss-counting rule.** A cell counts as a **loss** (gain) when its G_excess is negative (positive) and the Holm-adjusted DM p over the 14-cell family is < .05; a loss is **small** when the point estimate is inside ±1% of WIS(L3). Nominal (unadjusted) p < .05 alone is reported as 'nominal', never counted. While a family cell is pending, Holm runs over the available cells and the count is provisional.

Key: **G_emb** = WIS(L3) − WIS(L4) (raw AlphaEarth gain); **G_id** = WIS(L3) − WIS(L3+C*) (gain from a location/ID control); **G_excess** = WIS(L3+C*) − WIS(L4+C*) (primary: what AlphaEarth adds beyond the best ID control).

## 1. Headline table (T1)

Family: **14 of 14 cells available**.

| cell | C* | G_excess % [95% CI] | DM p | Holm p | label (±1%) | B=4 p | IAAFT p | all rows % | v1 excl % | case % |
|---|---|---|---|---|---|---|---|---|---|---|
| BR_S1 | C1 | +0.23 [-0.33, +0.79] | 0.392 | 1.000 | no significant difference; within ±1% (TOST, Holm-adjusted) | 0.447 | 0.507 | +0.26 | +0.23 | -0.03 |
| BR_S2 | C1 | -0.00 [-0.34, +0.34] | 0.996 | 1.000 | no significant difference; within ±1% (TOST, Holm-adjusted) | 0.997 | 0.997 | +0.03 | -0.01 | -0.73 |
| BR_S3 | C1 | -0.16 [-0.34, +0.03] | 0.090 | 0.527 | no significant difference; within ±1% (TOST, Holm-adjusted) | 0.259 | 0.214 | -0.10 | -0.19 | -1.30 |
| BR_S4 | C1 | +0.20 [-0.32, +0.71] | 0.428 | 1.000 | no significant difference; within ±1% (TOST, Holm-adjusted) | 0.472 | 0.522 | +0.23 | +0.19 | -0.37 |
| BR_S5 | C3 | -0.68 [-0.94, -0.42] | 4e-05 | 0.00057 | small negative difference, significant after Holm correction; within ±1% (unadjusted TOST only) | 0.007 | 0.0005 | -0.69 | -0.70 | -0.89 |
| CO_S1 | C1 | -0.42 [-0.64, -0.21] | 0.001 | 0.014 | small negative difference, significant after Holm correction; within ±1% (TOST, Holm-adjusted) | 0.014 | 0.003 | -0.42 | n/a | -0.84 |
| CO_S2 | C1 | -0.52 [-0.74, -0.30] | 0.00026 | 0.003 | small negative difference, significant after Holm correction; within ±1% (TOST, Holm-adjusted) | 0.002 | 0.0005 | -0.53 | n/a | -0.75 |
| CO_S3 | C1 | -0.68 [-1.08, -0.29] | 0.003 | 0.030 | small negative difference, significant after Holm correction; not shown to be within ±1% | 0.009 | 0.0005 | -0.71 | n/a | -0.78 |
| CO_S4 | C1 | -0.45 [-0.68, -0.21] | 0.002 | 0.019 | small negative difference, significant after Holm correction; within ±1% (TOST, Holm-adjusted) | 0.015 | 0.006 | -0.45 | n/a | -1.05 |
| CO_S5 | C2 | +0.22 [-0.19, +0.63] | 0.267 | 1.000 | no significant difference; within ±1% (TOST, Holm-adjusted) | 0.490 | 0.461 | +0.18 | n/a | +0.51 |
| PE_S1 | C1 | -0.82 [-1.49, -0.14] | 0.022 | 0.178 | nominal small negative difference, not significant after Holm correction; not shown to be within ±1% | 0.114 | 0.040 | -0.73 | n/a | -1.35 |
| PE_S5 | C3 | +0.93 [-0.16, +2.02] | 0.088 | 0.527 | no significant difference; not shown to be within ±1% | 0.020 | 0.005 | +0.99 | n/a | -0.61 |
| TW_S1 | C1 | -0.71 [-1.40, -0.03] | 0.042 | 0.294 | nominal small negative difference, not significant after Holm correction; not shown to be within ±1% | 0.037 | 0.007 | -0.66 | n/a | -0.13 |
| TW_S5 | C3 | -18.29 [-29.80, -6.78] | 0.004 | 0.035 | negative difference, significant after Holm correction; not shown to be within ±1% | 0.034 | 0.048 | -18.46 | n/a | -3.66 |

Counts under the loss-counting rule: loss: 1, nominal only: 2, none: 6, small loss: 5.

## 2. Status of every cell

| cell | group | description | C* | status | flags / what is missing |
|---|---|---|---|---|---|
| BR_S1 | primary/history | Brazil S1, history arm (primary) | C1 | available |  |
| BR_S2 | primary/history | Brazil S2, history arm (primary) | C1 | available |  |
| BR_S3 | primary/history | Brazil S3, history arm (primary) | C1 | available |  |
| BR_S4 | primary/history | Brazil S4, history arm (primary) | C1 | available |  |
| BR_S5 | primary/history | Brazil S5, history arm (primary) | C3 | available |  |
| CO_S1 | primary/history | Colombia S1, history arm (primary) | C1 | available |  |
| CO_S2 | primary/history | Colombia S2, history arm (primary) | C1 | available |  |
| CO_S3 | primary/history | Colombia S3, history arm (primary) | C1 | available |  |
| CO_S4 | primary/history | Colombia S4, history arm (primary) | C1 | available |  |
| CO_S5 | primary/history | Colombia S5, history arm (primary) | C2 | available |  |
| PE_S1 | primary/history | Peru S1, history arm (primary) | C1 | available |  |
| PE_S5 | primary/history | Peru S5, history arm (primary) | C3 | available |  |
| TW_S1 | primary/history | Taiwan S1, history arm (primary); test years incl. 2021 | C1 | available |  |
| TW_S5 | primary/history | Taiwan S5, history arm (primary); test years incl. 2021 | C3 | available |  |
| TW_S1_no2021 | secondary/sensitivity | Taiwan S1 without test year(s) 2021 (the pre-review test-year set) | C1 | available |  |
| TW_S5_no2021 | secondary/sensitivity | Taiwan S5 without test year(s) 2021 (the pre-review test-year set) | C3 | available |  |
| BR_S1_3seeds | secondary/sensitivity | Brazil S1, primary + 2 extra seeds (seed-averaged; extra seeds h1/h4) | C1 | available |  |
| BR_S1_yref | secondary/sensitivity | Brazil S1 sensitivity: yearly features aligned to the origin year (strictly causal) (G_emb only) | n/a (no C* run) | available |  |
| BR_S1_delay2 | secondary/sensitivity | Brazil S1 sensitivity: 2-week reporting delay (G_emb only) | n/a (no C* run) | available |  |
| BR_S1_ctrlC3 | secondary/sensitivity | Brazil S1 controls panel: C3 in place of C* (h1, h4) | C3 | available |  |
| BR_S1_ctrlC6 | secondary/sensitivity | Brazil S1 controls panel: C6 in place of C* (h1, h4) | C6 | available |  |
| BR_S1_perlevel | secondary/sensitivity | Brazil S1, per-level tuning (L3/L4 31 leaves; superseded primary) | C1 | available |  |
| TW_S1_BRparams | secondary/sensitivity | Taiwan S1 with Brazil's tuned params and C* | C1 | available |  |
| BR_S1_nohist | secondary/no-history | Brazil S1, no-history arm (ref = N3) | C2 | available |  |
| BR_S2_nohist | secondary/no-history | Brazil S2, no-history arm (ref = N3) | C2 | available |  |

## 3. Per-cell detail

### BR_S1: Brazil S1, history arm (primary) (C* = C1)
Rows scored (primary horizons) 2,703,183; row filter origin_year dropped 271,950 rows of 5678316 (all horizons); test years [2020, 2021, 2022, 2023, 2024]; seeds [0, 1, 2]; zero-filled share 0.52; outbreak share 0.082.

- **G_excess** (pooled h{1,4}) +0.23% [-0.33, +0.79]: L4+C* improves on L3+C* by 0.23% of WIS(ref) (95% CI -0.33 to +0.79%; p = 0.392; MDE 0.79%): **equivalent** (unadjusted rule), i.e. the 90% CI lies inside ±1% of WIS(ref): any effect is too small to matter.
- **G_emb** (pooled h{1,4}) +0.26% [-0.31, +0.82]: L4 improves on L3 by 0.26% of WIS(ref) (95% CI -0.31 to +0.82%; p = 0.348; MDE 0.80%): **equivalent** (unadjusted rule), i.e. the 90% CI lies inside ±1% of WIS(ref): any effect is too small to matter.
- **G_id** (pooled h{1,4}) +0.03% [-0.11, +0.18]: L3+C* improves on L3 by 0.03% of WIS(ref) (95% CI -0.11 to +0.18%; p = 0.651; MDE 0.21%): **equivalent** (unadjusted rule), i.e. the 90% CI lies inside ±1% of WIS(ref): any effect is too small to matter.
- *Secondary* G_excess pooled over h1-4 (years [2020, 2021, 2022, 2023, 2024]; not in the Holm family): +0.25% [-0.33, +0.82]; p = 0.381; equivalent.
- G_excess by target type (stratum estimate, % of the stratum's WIS(L3) | additive contribution, % of the cell's WIS(L3)): positive (27% rows) +0.30 | +0.46; recorded_zero (21% rows) -0.27 | -0.02; zero_filled (52% rows) -1.67 | -0.20; identity residual 0.0e+00.
- **ID share**: not estimable: G_emb 95% CI includes 0
- Ladder (pooled h{1,4}, 2,703,183 common rows): L0 0.4695, L1 0.1700, L2 0.1690, L3 0.1681, L4 0.1677, L3+C* 0.1680, L4+C* 0.1676. Best = L4+C*. 80% coverage 0.77–0.91 overall, 0.40–0.68 on non-zero targets.

### BR_S2: Brazil S2, history arm (primary) (C* = C1)
Rows scored (primary horizons) 2,703,183; row filter origin_year dropped 135,975 rows of 2839158 (all horizons); test years [2020, 2021, 2022, 2023, 2024]; seeds [0]; zero-filled share 0.52; outbreak share 0.082.

- **G_excess** (pooled h{1,4}) -0.00% [-0.34, +0.34]: L4+C* is worse than L3+C* by 0.00% of WIS(ref) (95% CI -0.34 to +0.34%; p = 0.996; MDE 0.48%): **equivalent** (unadjusted rule), i.e. the 90% CI lies inside ±1% of WIS(ref): any effect is too small to matter.
- **G_emb** (pooled h{1,4}) -0.02% [-0.34, +0.30]: L4 is worse than L3 by 0.02% of WIS(ref) (95% CI -0.34 to +0.30%; p = 0.881; MDE 0.45%): **equivalent** (unadjusted rule), i.e. the 90% CI lies inside ±1% of WIS(ref): any effect is too small to matter.
- **G_id** (pooled h{1,4}) -0.05% [-0.13, +0.02]: L3+C* is worse than L3 by 0.05% of WIS(ref) (95% CI -0.13 to +0.02%; p = 0.135; MDE 0.10%): **equivalent** (unadjusted rule), i.e. the 90% CI lies inside ±1% of WIS(ref): any effect is too small to matter.
- G_excess by target type (stratum estimate, % of the stratum's WIS(L3) | additive contribution, % of the cell's WIS(L3)): positive (27% rows) -0.00 | +0.14; recorded_zero (21% rows) +0.72 | +0.05; zero_filled (52% rows) -1.48 | -0.18; identity residual 0.0e+00.
- **ID share**: not estimable: G_emb 95% CI includes 0
- Ladder (pooled h{1,4}, 2,703,183 common rows): L3 0.1689, L4 0.1690, L3+C* 0.1690, L4+C* 0.1690. Best = L3. 80% coverage 0.90–0.90 overall, 0.66–0.66 on non-zero targets.

### BR_S3: Brazil S3, history arm (primary) (C* = C1)
Rows scored (primary horizons) 2,703,183; row filter origin_year dropped 135,975 rows of 2839158 (all horizons); test years [2020, 2021, 2022, 2023, 2024]; seeds [0]; zero-filled share 0.52; outbreak share 0.082.

- **G_excess** (pooled h{1,4}) -0.16% [-0.34, +0.03]: L4+C* is worse than L3+C* by 0.16% of WIS(ref) (95% CI -0.34 to +0.03%; p = 0.090; MDE 0.26%): **equivalent** (unadjusted rule), i.e. the 90% CI lies inside ±1% of WIS(ref): any effect is too small to matter.
- **G_emb** (pooled h{1,4}) -0.13% [-0.35, +0.09]: L4 is worse than L3 by 0.13% of WIS(ref) (95% CI -0.35 to +0.09%; p = 0.215; MDE 0.31%): **equivalent** (unadjusted rule), i.e. the 90% CI lies inside ±1% of WIS(ref): any effect is too small to matter.
- **G_id** (pooled h{1,4}) -0.03% [-0.14, +0.08]: L3+C* is worse than L3 by 0.03% of WIS(ref) (95% CI -0.14 to +0.08%; p = 0.592; MDE 0.16%): **equivalent** (unadjusted rule), i.e. the 90% CI lies inside ±1% of WIS(ref): any effect is too small to matter.
- G_excess by target type (stratum estimate, % of the stratum's WIS(L3) | additive contribution, % of the cell's WIS(L3)): positive (27% rows) +0.28 | +0.22; recorded_zero (21% rows) -0.34 | -0.03; zero_filled (52% rows) -2.75 | -0.35; identity residual 0.0e+00.
- **ID share**: not estimable: G_emb 95% CI includes 0
- Ladder (pooled h{1,4}, 2,703,183 common rows): L3 0.1706, L4 0.1709, L3+C* 0.1707, L4+C* 0.1710. Best = L3. 80% coverage 0.90–0.90 overall, 0.66–0.66 on non-zero targets.

### BR_S4: Brazil S4, history arm (primary) (C* = C1)
Rows scored (primary horizons) 2,703,183; row filter origin_year dropped 135,975 rows of 2839158 (all horizons); test years [2020, 2021, 2022, 2023, 2024]; seeds [0]; zero-filled share 0.52; outbreak share 0.082.

- **G_excess** (pooled h{1,4}) +0.20% [-0.32, +0.71]: L4+C* improves on L3+C* by 0.20% of WIS(ref) (95% CI -0.32 to +0.71%; p = 0.428; MDE 0.73%): **equivalent** (unadjusted rule), i.e. the 90% CI lies inside ±1% of WIS(ref): any effect is too small to matter.
- **G_emb** (pooled h{1,4}) +0.22% [-0.32, +0.76]: L4 improves on L3 by 0.22% of WIS(ref) (95% CI -0.32 to +0.76%; p = 0.396; MDE 0.76%): **equivalent** (unadjusted rule), i.e. the 90% CI lies inside ±1% of WIS(ref): any effect is too small to matter.
- **G_id** (pooled h{1,4}) +0.02% [-0.01, +0.05]: L3+C* improves on L3 by 0.02% of WIS(ref) (95% CI -0.01 to +0.05%; p = 0.178; MDE 0.04%): **equivalent** (unadjusted rule), i.e. the 90% CI lies inside ±1% of WIS(ref): any effect is too small to matter.
- G_excess by target type (stratum estimate, % of the stratum's WIS(L3) | additive contribution, % of the cell's WIS(L3)): positive (27% rows) +0.27 | +0.40; recorded_zero (21% rows) +0.07 | +0.00; zero_filled (52% rows) -1.59 | -0.20; identity residual 5.4e-20.
- **ID share**: not estimable: G_emb 95% CI includes 0
- Ladder (pooled h{1,4}, 2,703,183 common rows): L3 0.1683, L4 0.1679, L3+C* 0.1683, L4+C* 0.1680. Best = L4. 80% coverage 0.90–0.90 overall, 0.66–0.66 on non-zero targets.

### BR_S5: Brazil S5, history arm (primary) (C* = C3)
Rows scored (primary horizons) 2,703,183; row filter origin_year dropped 135,975 rows of 2839158 (all horizons); test years [2020, 2021, 2022, 2023, 2024]; seeds [0, 1, 2]; zero-filled share 0.52; outbreak share 0.082.

- **G_excess** (pooled h{1,4}) -0.68% [-0.94, -0.42]: L4+C* is worse than L3+C* by 0.68% of WIS(ref) (95% CI -0.94 to -0.42%; p = 0.000; MDE 0.36%): **equivalent** (unadjusted rule), i.e. the 90% CI lies inside ±1% of WIS(ref): any effect is too small to matter.
- **G_emb** (pooled h{1,4}) -0.39% [-1.34, +0.55]: L4 is worse than L3 by 0.39% of WIS(ref) (95% CI -1.34 to +0.55%; p = 0.390; MDE 1.33%): **inconclusive** (unadjusted rule), i.e. the CI crosses 0 and reaches past the ±1% margin: the data cannot tell.
- **G_id** (pooled h{1,4}) +0.15% [-0.89, +1.18]: L3+C* improves on L3 by 0.15% of WIS(ref) (95% CI -0.89 to +1.18%; p = 0.769; MDE 1.46%): **equivalent** (unadjusted rule), i.e. the 90% CI lies inside ±1% of WIS(ref): any effect is too small to matter.
- G_excess by target type (stratum estimate, % of the stratum's WIS(L3) | additive contribution, % of the cell's WIS(L3)): positive (27% rows) +0.44 | +0.16; recorded_zero (21% rows) -1.89 | -0.16; zero_filled (52% rows) -5.18 | -0.68; identity residual 0.0e+00.
- **ID share**: not estimable: G_emb 95% CI includes 0
- Ladder (pooled h{1,4}, 2,703,183 common rows): L3 0.1914, L4 0.1921, L3+C* 0.1911, L4+C* 0.1924. Best = L3+C*. 80% coverage 0.87–0.88 overall, 0.60–0.64 on non-zero targets.

### CO_S1: Colombia S1, history arm (primary) (C* = C1)
Rows scored (primary horizons) 319,930; row filter origin_year dropped 32,100 rows of 671960 (all horizons); test years [2020, 2021, 2022]; seeds [0, 1, 2]; zero-filled share 0.79; outbreak share 0.023.

- **G_excess** (pooled h{1,4}) -0.42% [-0.64, -0.21]: L4+C* is worse than L3+C* by 0.42% of WIS(ref) (95% CI -0.64 to -0.21%; p = 0.001; MDE 0.30%): **equivalent** (unadjusted rule), i.e. the 90% CI lies inside ±1% of WIS(ref): any effect is too small to matter.
- **G_emb** (pooled h{1,4}) -0.38% [-0.61, -0.16]: L4 is worse than L3 by 0.38% of WIS(ref) (95% CI -0.61 to -0.16%; p = 0.003; MDE 0.32%): **equivalent** (unadjusted rule), i.e. the 90% CI lies inside ±1% of WIS(ref): any effect is too small to matter.
- **G_id** (pooled h{1,4}) -0.06% [-0.32, +0.19]: L3+C* is worse than L3 by 0.06% of WIS(ref) (95% CI -0.32 to +0.19%; p = 0.600; MDE 0.36%): **equivalent** (unadjusted rule), i.e. the 90% CI lies inside ±1% of WIS(ref): any effect is too small to matter.
- *Secondary* G_excess pooled over h1-4 (years [2020, 2021, 2022]; not in the Holm family): -0.41% [-0.64, -0.18]; p = 0.002; equivalent.
- G_excess by target type (stratum estimate, % of the stratum's WIS(L3) | additive contribution, % of the cell's WIS(L3)): positive (21% rows) +0.24 | +0.18; recorded_zero (0% rows) n/a | +0.00; zero_filled (79% rows) -2.17 | -0.60; identity residual 0.0e+00.
- **ID share**: not estimable: G_emb significantly negative (embeddings hurt)
- Ladder (pooled h{1,4}, 319,930 common rows): L0 0.3272, L1 0.1226, L2 0.1224, L3 0.1220, L4 0.1225, L3+C* 0.1221, L4+C* 0.1226. Best = L3. 80% coverage 0.81–0.93 overall, 0.53–0.72 on non-zero targets.

### CO_S2: Colombia S2, history arm (primary) (C* = C1)
Rows scored (primary horizons) 319,930; row filter origin_year dropped 16,050 rows of 335980 (all horizons); test years [2020, 2021, 2022]; seeds [0, 1, 2]; zero-filled share 0.79; outbreak share 0.023.

- **G_excess** (pooled h{1,4}) -0.52% [-0.74, -0.30]: L4+C* is worse than L3+C* by 0.52% of WIS(ref) (95% CI -0.74 to -0.30%; p = 0.000; MDE 0.30%): **equivalent** (unadjusted rule), i.e. the 90% CI lies inside ±1% of WIS(ref): any effect is too small to matter.
- **G_emb** (pooled h{1,4}) -0.60% [-0.81, -0.39]: L4 is worse than L3 by 0.60% of WIS(ref) (95% CI -0.81 to -0.39%; p = 0.000; MDE 0.30%): **equivalent** (unadjusted rule), i.e. the 90% CI lies inside ±1% of WIS(ref): any effect is too small to matter.
- **G_id** (pooled h{1,4}) -0.06% [-0.09, -0.03]: L3+C* is worse than L3 by 0.06% of WIS(ref) (95% CI -0.09 to -0.03%; p = 0.002; MDE 0.04%): **equivalent** (unadjusted rule), i.e. the 90% CI lies inside ±1% of WIS(ref): any effect is too small to matter.
- G_excess by target type (stratum estimate, % of the stratum's WIS(L3) | additive contribution, % of the cell's WIS(L3)): positive (21% rows) +0.19 | +0.16; recorded_zero (0% rows) n/a | +0.00; zero_filled (79% rows) -2.45 | -0.68; identity residual 0.0e+00.
- **ID share**: not estimable: G_emb significantly negative (embeddings hurt)
- Ladder (pooled h{1,4}, 319,930 common rows): L3 0.1225, L4 0.1232, L3+C* 0.1225, L4+C* 0.1232. Best = L3. 80% coverage 0.92–0.93 overall, 0.70–0.71 on non-zero targets.

### CO_S3: Colombia S3, history arm (primary) (C* = C1)
Rows scored (primary horizons) 319,930; row filter origin_year dropped 16,050 rows of 335980 (all horizons); test years [2020, 2021, 2022]; seeds [0, 1, 2]; zero-filled share 0.79; outbreak share 0.023.

- **G_excess** (pooled h{1,4}) -0.68% [-1.08, -0.29]: L4+C* is worse than L3+C* by 0.68% of WIS(ref) (95% CI -1.08 to -0.29%; p = 0.003; MDE 0.56%): **inferior** (unadjusted rule), i.e. the 95% CI excludes 0 on the harm side: the second model is worse.
- **G_emb** (pooled h{1,4}) -0.82% [-1.14, -0.49]: L4 is worse than L3 by 0.82% of WIS(ref) (95% CI -1.14 to -0.49%; p = 0.000; MDE 0.45%): **inferior** (unadjusted rule), i.e. the 95% CI excludes 0 on the harm side: the second model is worse.
- **G_id** (pooled h{1,4}) -0.08% [-0.14, -0.02]: L3+C* is worse than L3 by 0.08% of WIS(ref) (95% CI -0.14 to -0.02%; p = 0.011; MDE 0.08%): **equivalent** (unadjusted rule), i.e. the 90% CI lies inside ±1% of WIS(ref): any effect is too small to matter.
- G_excess by target type (stratum estimate, % of the stratum's WIS(L3) | additive contribution, % of the cell's WIS(L3)): positive (21% rows) +0.09 | +0.07; recorded_zero (0% rows) n/a | +0.00; zero_filled (79% rows) -2.55 | -0.76; identity residual 2.2e-19.
- **ID share**: not estimable: G_emb significantly negative (embeddings hurt)
- Ladder (pooled h{1,4}, 319,930 common rows): L3 0.1245, L4 0.1255, L3+C* 0.1246, L4+C* 0.1254. Best = L3. 80% coverage 0.92–0.92 overall, 0.70–0.71 on non-zero targets.

### CO_S4: Colombia S4, history arm (primary) (C* = C1)
Rows scored (primary horizons) 319,930; row filter origin_year dropped 16,050 rows of 335980 (all horizons); test years [2020, 2021, 2022]; seeds [0, 1, 2]; zero-filled share 0.79; outbreak share 0.023.

- **G_excess** (pooled h{1,4}) -0.45% [-0.68, -0.21]: L4+C* is worse than L3+C* by 0.45% of WIS(ref) (95% CI -0.68 to -0.21%; p = 0.002; MDE 0.33%): **equivalent** (unadjusted rule), i.e. the 90% CI lies inside ±1% of WIS(ref): any effect is too small to matter.
- **G_emb** (pooled h{1,4}) -0.54% [-0.78, -0.30]: L4 is worse than L3 by 0.54% of WIS(ref) (95% CI -0.78 to -0.30%; p = 0.000; MDE 0.34%): **equivalent** (unadjusted rule), i.e. the 90% CI lies inside ±1% of WIS(ref): any effect is too small to matter.
- **G_id** (pooled h{1,4}) -0.10% [-0.12, -0.08]: L3+C* is worse than L3 by 0.10% of WIS(ref) (95% CI -0.12 to -0.08%; p = 0.000; MDE 0.03%): **equivalent** (unadjusted rule), i.e. the 90% CI lies inside ±1% of WIS(ref): any effect is too small to matter.
- G_excess by target type (stratum estimate, % of the stratum's WIS(L3) | additive contribution, % of the cell's WIS(L3)): positive (21% rows) +0.26 | +0.22; recorded_zero (0% rows) n/a | +0.00; zero_filled (79% rows) -2.40 | -0.66; identity residual 0.0e+00.
- **ID share**: not estimable: G_emb significantly negative (embeddings hurt)
- Ladder (pooled h{1,4}, 319,930 common rows): L3 0.1223, L4 0.1229, L3+C* 0.1224, L4+C* 0.1229. Best = L3. 80% coverage 0.92–0.93 overall, 0.71–0.71 on non-zero targets.

### CO_S5: Colombia S5, history arm (primary) (C* = C2)
Rows scored (primary horizons) 319,930; row filter origin_year dropped 16,050 rows of 335980 (all horizons); test years [2020, 2021, 2022]; seeds [0]; zero-filled share 0.79; outbreak share 0.023.

- **G_excess** (pooled h{1,4}) +0.22% [-0.19, +0.63]: L4+C* improves on L3+C* by 0.22% of WIS(ref) (95% CI -0.19 to +0.63%; p = 0.267; MDE 0.57%): **equivalent** (unadjusted rule), i.e. the 90% CI lies inside ±1% of WIS(ref): any effect is too small to matter.
- **G_emb** (pooled h{1,4}) -0.04% [-0.37, +0.28]: L4 is worse than L3 by 0.04% of WIS(ref) (95% CI -0.37 to +0.28%; p = 0.774; MDE 0.46%): **equivalent** (unadjusted rule), i.e. the 90% CI lies inside ±1% of WIS(ref): any effect is too small to matter.
- **G_id** (pooled h{1,4}) -0.81% [-1.16, -0.46]: L3+C* is worse than L3 by 0.81% of WIS(ref) (95% CI -1.16 to -0.46%; p = 0.000; MDE 0.49%): **inferior** (unadjusted rule), i.e. the 95% CI excludes 0 on the harm side: the second model is worse.
- G_excess by target type (stratum estimate, % of the stratum's WIS(L3) | additive contribution, % of the cell's WIS(L3)): positive (21% rows) +0.37 | +0.27; recorded_zero (0% rows) n/a | +0.00; zero_filled (79% rows) -0.13 | -0.05; identity residual 0.0e+00.
- **ID share**: not estimable: G_emb 95% CI includes 0
- Ladder (pooled h{1,4}, 319,930 common rows): L3 0.1238, L4 0.1239, L3+C* 0.1249, L4+C* 0.1246. Best = L3. 80% coverage 0.93–0.94 overall, 0.68–0.75 on non-zero targets.

### PE_S1: Peru S1, history arm (primary) (C* = C1)
Rows scored (primary horizons) 45,754; row filter origin_year dropped 4,600 rows of 96108 (all horizons); test years [2020, 2021, 2022, 2023]; seeds [0, 1, 2]; zero-filled share 0.56; outbreak share 0.229.

- **G_excess** (pooled h{1,4}) -0.82% [-1.49, -0.14]: L4+C* is worse than L3+C* by 0.82% of WIS(ref) (95% CI -1.49 to -0.14%; p = 0.022; MDE 0.95%): **inferior** (unadjusted rule), i.e. the 95% CI excludes 0 on the harm side: the second model is worse.
- **G_emb** (pooled h{1,4}) -0.91% [-1.62, -0.20]: L4 is worse than L3 by 0.91% of WIS(ref) (95% CI -1.62 to -0.20%; p = 0.016; MDE 1.00%): **inferior** (unadjusted rule), i.e. the 95% CI excludes 0 on the harm side: the second model is worse.
- **G_id** (pooled h{1,4}) -0.20% [-0.92, +0.52]: L3+C* is worse than L3 by 0.20% of WIS(ref) (95% CI -0.92 to +0.52%; p = 0.558; MDE 1.01%): **equivalent** (unadjusted rule), i.e. the 90% CI lies inside ±1% of WIS(ref): any effect is too small to matter.
- *Secondary* G_excess pooled over h1-4 (years [2020, 2021, 2022, 2023]; not in the Holm family): -0.69% [-1.38, -0.01]; p = 0.047; inferior.
- G_excess by target type (stratum estimate, % of the stratum's WIS(L3) | additive contribution, % of the cell's WIS(L3)): positive (44% rows) -0.27 | -0.14; recorded_zero (0% rows) n/a | +0.00; zero_filled (56% rows) -5.64 | -0.67; identity residual 0.0e+00.
- **ID share**: not estimable: G_emb significantly negative (embeddings hurt)
- Ladder (pooled h{1,4}, 45,754 common rows): L0 0.6596, L1 0.2442, L2 0.2431, L3 0.2438, L4 0.2460, L3+C* 0.2443, L4+C* 0.2463. Best = L2. 80% coverage 0.73–0.84 overall, 0.47–0.70 on non-zero targets.

### PE_S5: Peru S5, history arm (primary) (C* = C3)
Rows scored (primary horizons) 45,754; row filter origin_year dropped 2,300 rows of 48054 (all horizons); test years [2020, 2021, 2022, 2023]; seeds [0, 1, 2]; zero-filled share 0.56; outbreak share 0.229.

- **G_excess** (pooled h{1,4}) +0.93% [-0.16, +2.02]: L4+C* improves on L3+C* by 0.93% of WIS(ref) (95% CI -0.16 to +2.02%; p = 0.088; MDE 1.53%): **inconclusive** (unadjusted rule), i.e. the CI crosses 0 and reaches past the ±1% margin: the data cannot tell.
- **G_emb** (pooled h{1,4}) +0.68% [-0.59, +1.96]: L4 improves on L3 by 0.68% of WIS(ref) (95% CI -0.59 to +1.96%; p = 0.268; MDE 1.79%): **inconclusive** (unadjusted rule), i.e. the CI crosses 0 and reaches past the ±1% margin: the data cannot tell.
- **G_id** (pooled h{1,4}) -0.44% [-0.80, -0.07]: L3+C* is worse than L3 by 0.44% of WIS(ref) (95% CI -0.80 to -0.07%; p = 0.022; MDE 0.51%): **equivalent** (unadjusted rule), i.e. the 90% CI lies inside ±1% of WIS(ref): any effect is too small to matter.
- G_excess by target type (stratum estimate, % of the stratum's WIS(L3) | additive contribution, % of the cell's WIS(L3)): positive (44% rows) +1.52 | +1.20; recorded_zero (0% rows) n/a | +0.00; zero_filled (56% rows) -2.69 | -0.27; identity residual 0.0e+00.
- **ID share**: not estimable: G_emb 95% CI includes 0
- Ladder (pooled h{1,4}, 45,754 common rows): L3 0.2383, L4 0.2367, L3+C* 0.2392, L4+C* 0.2369. Best = L4. 80% coverage 0.83–0.84 overall, 0.65–0.68 on non-zero targets.

### TW_S1: Taiwan S1, history arm (primary); test years incl. 2021 (C* = C1)
Rows scored (primary horizons) 141,645; row filter origin_year dropped 12,825 rows of 267900 (all horizons); test years [2020, 2021, 2022, 2023, 2024]; seeds [0, 1, 2]; zero-filled share 0.97; outbreak share 0.008.

- **G_excess** (pooled h{1,4}) -0.71% [-1.40, -0.03]: L4+C* is worse than L3+C* by 0.71% of WIS(ref) (95% CI -1.40 to -0.03%; p = 0.042; MDE 0.96%): **inferior** (unadjusted rule), i.e. the 95% CI excludes 0 on the harm side: the second model is worse.
- **G_emb** (pooled h{1,4}) -0.95% [-1.71, -0.18]: L4 is worse than L3 by 0.95% of WIS(ref) (95% CI -1.71 to -0.18%; p = 0.018; MDE 1.08%): **inferior** (unadjusted rule), i.e. the 95% CI excludes 0 on the harm side: the second model is worse.
- **G_id** (pooled h{1,4}) -0.41% [-0.97, +0.16]: L3+C* is worse than L3 by 0.41% of WIS(ref) (95% CI -0.97 to +0.16%; p = 0.145; MDE 0.79%): **equivalent** (unadjusted rule), i.e. the 90% CI lies inside ±1% of WIS(ref): any effect is too small to matter.
- *Secondary* G_excess pooled over h1-4 (years [2020, 2022, 2023, 2024]; not in the Holm family): -0.46% [-1.09, +0.17]; p = 0.136; equivalent.
- G_excess by target type (stratum estimate, % of the stratum's WIS(L3) | additive contribution, % of the cell's WIS(L3)): positive (2% rows) -0.10 | -0.24; recorded_zero (0% rows) n/a | +0.00; zero_filled (98% rows) -8.59 | -0.47; identity residual 0.0e+00.
- **ID share**: not estimable: G_emb significantly negative (embeddings hurt)
- Ladder (pooled h{1,4}, 141,645 common rows): L0 0.0743, L1 0.0316, L2 0.0319, L3 0.0320, L4 0.0323, L3+C* 0.0321, L4+C* 0.0323. Best = L1. 80% coverage 0.95–0.98 overall, 0.00–0.25 on non-zero targets.

### TW_S5: Taiwan S5, history arm (primary); test years incl. 2021 (C* = C3)
Rows scored (primary horizons) 141,645; row filter origin_year dropped 7,125 rows of 148770 (all horizons); test years [2020, 2021, 2022, 2023, 2024]; seeds [0, 1, 2]; zero-filled share 0.98; outbreak share 0.007.

- **G_excess** (pooled h{1,4}) -18.29% [-29.80, -6.78]: L4+C* is worse than L3+C* by 18.29% of WIS(ref) (95% CI -29.80 to -6.78%; p = 0.004; MDE 16.20%): **inferior** (unadjusted rule), i.e. the 95% CI excludes 0 on the harm side: the second model is worse.
- **G_emb** (pooled h{1,4}) -21.60% [-31.82, -11.39]: L4 is worse than L3 by 21.60% of WIS(ref) (95% CI -31.82 to -11.39%; p = 0.000; MDE 14.38%): **inferior** (unadjusted rule), i.e. the 95% CI excludes 0 on the harm side: the second model is worse.
- **G_id** (pooled h{1,4}) -3.36% [-6.52, -0.20]: L3+C* is worse than L3 by 3.36% of WIS(ref) (95% CI -6.52 to -0.20%; p = 0.039; MDE 4.45%): **inferior** (unadjusted rule), i.e. the 95% CI excludes 0 on the harm side: the second model is worse.
- G_excess by target type (stratum estimate, % of the stratum's WIS(L3) | additive contribution, % of the cell's WIS(L3)): positive (2% rows) +2.41 | +1.33; recorded_zero (0% rows) n/a | +0.00; zero_filled (98% rows) -51.00 | -19.62; identity residual 0.0e+00.
- **ID share**: not estimable: G_emb significantly negative (embeddings hurt)
- Ladder (pooled h{1,4}, 141,645 common rows): L3 0.0205, L4 0.0250, L3+C* 0.0216, L4+C* 0.0253. Best = L3. 80% coverage 0.99–0.99 overall, 0.56–0.63 on non-zero targets.

### TW_S1_no2021: Taiwan S1 without test year(s) 2021 (the pre-review test-year set) (C* = C1)
Rows scored (primary horizons) 113,430; row filter origin_year dropped 11,400 rows of 238260 (all horizons); test years [2020, 2022, 2023, 2024]; seeds [0]; zero-filled share 0.97; outbreak share 0.009.

- **G_excess** (pooled h{1,4}) -0.44% [-1.01, +0.14]: L4+C* is worse than L3+C* by 0.44% of WIS(ref) (95% CI -1.01 to +0.14%; p = 0.123; MDE 0.80%): **equivalent** (unadjusted rule), i.e. the 90% CI lies inside ±1% of WIS(ref): any effect is too small to matter.
- **G_emb** (pooled h{1,4}) -0.94% [-1.85, -0.03]: L4 is worse than L3 by 0.94% of WIS(ref) (95% CI -1.85 to -0.03%; p = 0.043; MDE 1.27%): **inferior** (unadjusted rule), i.e. the 95% CI excludes 0 on the harm side: the second model is worse.
- **G_id** (pooled h{1,4}) -0.63% [-1.69, +0.44]: L3+C* is worse than L3 by 0.63% of WIS(ref) (95% CI -1.69 to +0.44%; p = 0.228; MDE 1.50%): **inconclusive** (unadjusted rule), i.e. the CI crosses 0 and reaches past the ±1% margin: the data cannot tell.
- *Secondary* G_excess pooled over h1-4 (years [2020, 2022, 2023, 2024]; not in the Holm family): -0.38% [-0.92, +0.15]; p = 0.145; equivalent.
- G_excess by target type (stratum estimate, % of the stratum's WIS(L3) | additive contribution, % of the cell's WIS(L3)): positive (3% rows) -0.15 | -0.07; recorded_zero (0% rows) n/a | +0.00; zero_filled (97% rows) -6.74 | -0.36; identity residual 0.0e+00.
- **ID share**: not estimable: G_emb significantly negative (embeddings hurt)
- Ladder (pooled h{1,4}, 113,430 common rows): L3 0.0398, L4 0.0402, L3+C* 0.0400, L4+C* 0.0402. Best = L3. 80% coverage 0.98–0.98 overall, 0.24–0.25 on non-zero targets.

### TW_S5_no2021: Taiwan S5 without test year(s) 2021 (the pre-review test-year set) (C* = C3)
Rows scored (primary horizons) 113,430; row filter origin_year dropped 5,700 rows of 119130 (all horizons); test years [2020, 2022, 2023, 2024]; seeds [0]; zero-filled share 0.97; outbreak share 0.009.

- **G_excess** (pooled h{1,4}) -11.16% [-15.66, -6.65]: L4+C* is worse than L3+C* by 11.16% of WIS(ref) (95% CI -15.66 to -6.65%; p = 0.000; MDE 6.32%): **inferior** (unadjusted rule), i.e. the 95% CI excludes 0 on the harm side: the second model is worse.
- **G_emb** (pooled h{1,4}) -14.68% [-20.24, -9.11]: L4 is worse than L3 by 14.68% of WIS(ref) (95% CI -20.24 to -9.11%; p = 0.000; MDE 7.81%): **inferior** (unadjusted rule), i.e. the 95% CI excludes 0 on the harm side: the second model is worse.
- **G_id** (pooled h{1,4}) -2.31% [-5.52, +0.90]: L3+C* is worse than L3 by 2.31% of WIS(ref) (95% CI -5.52 to +0.90%; p = 0.145; MDE 4.51%): **inconclusive** (unadjusted rule), i.e. the CI crosses 0 and reaches past the ±1% margin: the data cannot tell.
- G_excess by target type (stratum estimate, % of the stratum's WIS(L3) | additive contribution, % of the cell's WIS(L3)): positive (3% rows) +2.16 | +1.33; recorded_zero (0% rows) n/a | +0.00; zero_filled (97% rows) -35.22 | -12.48; identity residual 0.0e+00.
- **ID share**: not estimable: G_emb significantly negative (embeddings hurt)
- Ladder (pooled h{1,4}, 113,430 common rows): L3 0.0246, L4 0.0283, L3+C* 0.0252, L4+C* 0.0280. Best = L3. 80% coverage 0.99–0.99 overall, 0.56–0.63 on non-zero targets.

### BR_S1_3seeds: Brazil S1, primary + 2 extra seeds (seed-averaged; extra seeds h1/h4) (C* = C1)
Rows scored (primary horizons) 2,703,183; row filter origin_year dropped 271,950 rows of 5678316 (all horizons); test years [2020, 2021, 2022, 2023, 2024]; seeds [0, 1, 2]; zero-filled share 0.52; outbreak share 0.082.

- **G_excess** (pooled h{1,4}) +0.23% [-0.33, +0.79]: L4+C* improves on L3+C* by 0.23% of WIS(ref) (95% CI -0.33 to +0.79%; p = 0.392; MDE 0.79%): **equivalent** (unadjusted rule), i.e. the 90% CI lies inside ±1% of WIS(ref): any effect is too small to matter.
- **G_emb** (pooled h{1,4}) +0.26% [-0.31, +0.82]: L4 improves on L3 by 0.26% of WIS(ref) (95% CI -0.31 to +0.82%; p = 0.348; MDE 0.80%): **equivalent** (unadjusted rule), i.e. the 90% CI lies inside ±1% of WIS(ref): any effect is too small to matter.
- **G_id** (pooled h{1,4}) +0.03% [-0.11, +0.18]: L3+C* improves on L3 by 0.03% of WIS(ref) (95% CI -0.11 to +0.18%; p = 0.651; MDE 0.21%): **equivalent** (unadjusted rule), i.e. the 90% CI lies inside ±1% of WIS(ref): any effect is too small to matter.
- *Secondary* G_excess pooled over h1-4 (years [2020, 2021, 2022, 2023, 2024]; not in the Holm family): +0.25% [-0.33, +0.82]; p = 0.381; equivalent.
- G_excess by target type (stratum estimate, % of the stratum's WIS(L3) | additive contribution, % of the cell's WIS(L3)): positive (27% rows) +0.30 | +0.46; recorded_zero (21% rows) -0.27 | -0.02; zero_filled (52% rows) -1.67 | -0.20; identity residual 0.0e+00.
- **ID share**: not estimable: G_emb 95% CI includes 0
- Ladder (pooled h{1,4}, 2,703,183 common rows): L3 0.1681, L4 0.1677, L3+C* 0.1680, L4+C* 0.1676. Best = L4+C*. 80% coverage 0.90–0.90 overall, 0.66–0.67 on non-zero targets.

### BR_S1_yref: Brazil S1 sensitivity: yearly features aligned to the origin year (strictly causal) (G_emb only) (C* = n/a (no C* run))
Rows scored (primary horizons) 2,703,183; row filter origin_year dropped 135,975 rows of 2839158 (all horizons); test years [2020, 2021, 2022, 2023, 2024]; seeds [0]; zero-filled share 0.52; outbreak share 0.082.

- **G_emb** (pooled h{1,4}) +0.26% [-0.29, +0.82]: L4 improves on L3 by 0.26% of WIS(ref) (95% CI -0.29 to +0.82%; p = 0.330; MDE 0.79%): **equivalent** (unadjusted rule), i.e. the 90% CI lies inside ±1% of WIS(ref): any effect is too small to matter.
- Ladder (pooled h{1,4}, 2,703,183 common rows): L3 0.1681, L4 0.1676. Best = L4. 80% coverage 0.90–0.90 overall, 0.67–0.67 on non-zero targets.

### BR_S1_delay2: Brazil S1 sensitivity: 2-week reporting delay (G_emb only) (C* = n/a (no C* run))
Rows scored (primary horizons) 2,703,183; row filter origin_year dropped 135,975 rows of 2839158 (all horizons); test years [2020, 2021, 2022, 2023, 2024]; seeds [0]; zero-filled share 0.52; outbreak share 0.082.

- **G_emb** (pooled h{1,4}) +0.60% [-0.56, +1.76]: L4 improves on L3 by 0.60% of WIS(ref) (95% CI -0.56 to +1.76%; p = 0.291; MDE 1.64%): **inconclusive** (unadjusted rule), i.e. the CI crosses 0 and reaches past the ±1% margin: the data cannot tell.
- Ladder (pooled h{1,4}, 2,703,183 common rows): L3 0.2038, L4 0.2026. Best = L4. 80% coverage 0.89–0.89 overall, 0.63–0.63 on non-zero targets.

### BR_S1_ctrlC3: Brazil S1 controls panel: C3 in place of C* (h1, h4) (C* = C3)
Rows scored (primary horizons) 2,703,183; row filter origin_year dropped 135,975 rows of 2839158 (all horizons); test years [2020, 2021, 2022, 2023, 2024]; seeds [0, 1, 2]; zero-filled share 0.52; outbreak share 0.082.

- **G_excess** (pooled h{1,4}) +0.28% [-0.27, +0.82]: L4+C* improves on L3+C* by 0.28% of WIS(ref) (95% CI -0.27 to +0.82%; p = 0.296; MDE 0.77%): **equivalent** (unadjusted rule), i.e. the 90% CI lies inside ±1% of WIS(ref): any effect is too small to matter.
- **G_emb** (pooled h{1,4}) +0.26% [-0.31, +0.82]: L4 improves on L3 by 0.26% of WIS(ref) (95% CI -0.31 to +0.82%; p = 0.348; MDE 0.80%): **equivalent** (unadjusted rule), i.e. the 90% CI lies inside ±1% of WIS(ref): any effect is too small to matter.
- **G_id** (pooled h{1,4}) -0.04% [-0.08, -0.00]: L3+C* is worse than L3 by 0.04% of WIS(ref) (95% CI -0.08 to -0.00%; p = 0.038; MDE 0.06%): **equivalent** (unadjusted rule), i.e. the 90% CI lies inside ±1% of WIS(ref): any effect is too small to matter.
- G_excess by target type (stratum estimate, % of the stratum's WIS(L3) | additive contribution, % of the cell's WIS(L3)): positive (27% rows) +0.30 | +0.44; recorded_zero (21% rows) +0.14 | +0.01; zero_filled (52% rows) -1.23 | -0.17; identity residual 5.4e-20.
- **ID share**: not estimable: G_emb 95% CI includes 0
- Ladder (pooled h{1,4}, 2,703,183 common rows): L3 0.1681, L4 0.1677, L3+C* 0.1682, L4+C* 0.1677. Best = L4. 80% coverage 0.90–0.90 overall, 0.66–0.67 on non-zero targets.

### BR_S1_ctrlC6: Brazil S1 controls panel: C6 in place of C* (h1, h4) (C* = C6)
Rows scored (primary horizons) 2,703,183; row filter origin_year dropped 135,975 rows of 2839158 (all horizons); test years [2020, 2021, 2022, 2023, 2024]; seeds [0, 1, 2]; zero-filled share 0.52; outbreak share 0.082.

- **G_excess** (pooled h{1,4}) +0.30% [-0.12, +0.71]: L4+C* improves on L3+C* by 0.30% of WIS(ref) (95% CI -0.12 to +0.71%; p = 0.150; MDE 0.58%): **equivalent** (unadjusted rule), i.e. the 90% CI lies inside ±1% of WIS(ref): any effect is too small to matter.
- **G_emb** (pooled h{1,4}) +0.26% [-0.31, +0.82]: L4 improves on L3 by 0.26% of WIS(ref) (95% CI -0.31 to +0.82%; p = 0.348; MDE 0.80%): **equivalent** (unadjusted rule), i.e. the 90% CI lies inside ±1% of WIS(ref): any effect is too small to matter.
- **G_id** (pooled h{1,4}) -2.11% [-2.68, -1.54]: L3+C* is worse than L3 by 2.11% of WIS(ref) (95% CI -2.68 to -1.54%; p = 0.000; MDE 0.81%): **inferior** (unadjusted rule), i.e. the 95% CI excludes 0 on the harm side: the second model is worse.
- G_excess by target type (stratum estimate, % of the stratum's WIS(L3) | additive contribution, % of the cell's WIS(L3)): positive (27% rows) +0.23 | +0.34; recorded_zero (21% rows) +0.34 | +0.02; zero_filled (52% rows) -0.40 | -0.06; identity residual 0.0e+00.
- **ID share**: not estimable: G_emb 95% CI includes 0
- Ladder (pooled h{1,4}, 2,703,183 common rows): L3 0.1681, L4 0.1677, L3+C* 0.1717, L4+C* 0.1712. Best = L4. 80% coverage 0.89–0.90 overall, 0.63–0.67 on non-zero targets.

### BR_S1_perlevel: Brazil S1, per-level tuning (L3/L4 31 leaves; superseded primary) (C* = C1)
Rows scored (primary horizons) 2,703,183; row filter origin_year dropped 271,950 rows of 5678316 (all horizons); test years [2020, 2021, 2022, 2023, 2024]; seeds [0]; zero-filled share 0.52; outbreak share 0.082.

- **G_excess** (pooled h{1,4}) +0.25% [-0.07, +0.56]: L4+C* improves on L3+C* by 0.25% of WIS(ref) (95% CI -0.07 to +0.56%; p = 0.113; MDE 0.44%): **equivalent** (unadjusted rule), i.e. the 90% CI lies inside ±1% of WIS(ref): any effect is too small to matter.
- **G_emb** (pooled h{1,4}) +0.21% [-0.05, +0.47]: L4 improves on L3 by 0.21% of WIS(ref) (95% CI -0.05 to +0.47%; p = 0.105; MDE 0.37%): **equivalent** (unadjusted rule), i.e. the 90% CI lies inside ±1% of WIS(ref): any effect is too small to matter.
- **G_id** (pooled h{1,4}) -0.06% [-0.30, +0.18]: L3+C* is worse than L3 by 0.06% of WIS(ref) (95% CI -0.30 to +0.18%; p = 0.615; MDE 0.33%): **equivalent** (unadjusted rule), i.e. the 90% CI lies inside ±1% of WIS(ref): any effect is too small to matter.
- *Secondary* G_excess pooled over h1-4 (years [2020, 2021, 2022, 2023, 2024]; not in the Holm family): +0.25% [-0.06, +0.57]; p = 0.108; equivalent.
- G_excess by target type (stratum estimate, % of the stratum's WIS(L3) | additive contribution, % of the cell's WIS(L3)): positive (27% rows) +0.22 | +0.27; recorded_zero (21% rows) +0.30 | +0.01; zero_filled (52% rows) -0.06 | -0.03; identity residual 5.4e-20.
- **ID share**: not estimable: G_emb 95% CI includes 0
- Ladder (pooled h{1,4}, 2,703,183 common rows): L0 0.4695, L1 0.1700, L2 0.1690, L3 0.1714, L4 0.1710, L3+C* 0.1714, L4+C* 0.1710. Best = L2. 80% coverage 0.77–0.91 overall, 0.40–0.68 on non-zero targets.

### TW_S1_BRparams: Taiwan S1 with Brazil's tuned params and C* (C* = C1)
Rows scored (primary horizons) 113,430; row filter origin_year dropped 11,400 rows of 238260 (all horizons); test years [2020, 2022, 2023, 2024]; seeds [0]; zero-filled share 0.97; outbreak share 0.009.

- **G_excess** (pooled h{1,4}) -0.33% [-0.89, +0.23]: L4+C* is worse than L3+C* by 0.33% of WIS(ref) (95% CI -0.89 to +0.23%; p = 0.220; MDE 0.79%): **equivalent** (unadjusted rule), i.e. the 90% CI lies inside ±1% of WIS(ref): any effect is too small to matter.
- **G_emb** (pooled h{1,4}) -0.87% [-1.78, +0.03]: L4 is worse than L3 by 0.87% of WIS(ref) (95% CI -1.78 to +0.03%; p = 0.057; MDE 1.27%): **inconclusive** (unadjusted rule), i.e. the CI crosses 0 and reaches past the ±1% margin: the data cannot tell.
- **G_id** (pooled h{1,4}) -0.71% [-1.67, +0.26]: L3+C* is worse than L3 by 0.71% of WIS(ref) (95% CI -1.67 to +0.26%; p = 0.140; MDE 1.36%): **inconclusive** (unadjusted rule), i.e. the CI crosses 0 and reaches past the ±1% margin: the data cannot tell.
- *Secondary* G_excess pooled over h1-4 (years [2020, 2022, 2023, 2024]; not in the Holm family): -0.33% [-0.86, +0.21]; p = 0.213; equivalent.
- G_excess by target type (stratum estimate, % of the stratum's WIS(L3) | additive contribution, % of the cell's WIS(L3)): positive (3% rows) +0.02 | -0.11; recorded_zero (0% rows) n/a | +0.00; zero_filled (97% rows) -4.10 | -0.23; identity residual 2.7e-20.
- **ID share**: not estimable: G_emb 95% CI includes 0
- Ladder (pooled h{1,4}, 113,430 common rows): L3 0.0398, L4 0.0402, L3+C* 0.0401, L4+C* 0.0403. Best = L3. 80% coverage 0.98–0.98 overall, 0.24–0.25 on non-zero targets.

### BR_S1_nohist: Brazil S1, no-history arm (ref = N3) (C* = C2)
Rows scored (primary horizons) 2,703,183; row filter origin_year dropped 135,975 rows of 2839158 (all horizons); test years [2020, 2021, 2022, 2023, 2024]; seeds [0]; zero-filled share 0.52; outbreak share 0.082.

- **G_excess** (pooled h{1,4}) -0.43% [-2.06, +1.19]: N4+C* is worse than N3+C* by 0.43% of WIS(ref) (95% CI -2.06 to +1.19%; p = 0.580; MDE 2.29%): **inconclusive** (unadjusted rule), i.e. the CI crosses 0 and reaches past the ±1% margin: the data cannot tell.
- **G_emb** (pooled h{1,4}) +2.54% [-0.82, +5.89]: N4 improves on N3 by 2.54% of WIS(ref) (95% CI -0.82 to +5.89%; p = 0.129; MDE 4.72%): **inconclusive** (unadjusted rule), i.e. the CI crosses 0 and reaches past the ±1% margin: the data cannot tell.
- **G_id** (pooled h{1,4}) +3.30% [+1.68, +4.93]: N3+C* improves on N3 by 3.30% of WIS(ref) (95% CI +1.68 to +4.93%; p = 0.001; MDE 2.29%): **superior** (unadjusted rule), i.e. the 95% CI excludes 0 on the improvement side: the second model is better.
- G_excess by target type (stratum estimate, % of the stratum's WIS(L3) | additive contribution, % of the cell's WIS(L3)): positive (27% rows) +0.58 | +0.77; recorded_zero (21% rows) -6.09 | -0.29; zero_filled (52% rows) -15.77 | -0.91; identity residual 0.0e+00.
- **ID share**: not estimable: G_emb 95% CI includes 0
- Ladder (pooled h{1,4}, 2,703,183 common rows): N3+C1 0.3478, N4+C1 0.3409, N3 0.3526, N4 0.3437, N3+C* 0.3411, N4+C* 0.3426. Best = N4+C1. 80% coverage 0.83–0.85 overall, 0.41–0.43 on non-zero targets.

### BR_S2_nohist: Brazil S2, no-history arm (ref = N3) (C* = C2)
Rows scored (primary horizons) 2,703,183; row filter origin_year dropped 135,975 rows of 2839158 (all horizons); test years [2020, 2021, 2022, 2023, 2024]; seeds [0]; zero-filled share 0.52; outbreak share 0.082.

- **G_excess** (pooled h{1,4}) -0.01% [-1.28, +1.27]: N4+C* is worse than N3+C* by 0.01% of WIS(ref) (95% CI -1.28 to +1.27%; p = 0.989; MDE 1.80%): **inconclusive** (unadjusted rule), i.e. the CI crosses 0 and reaches past the ±1% margin: the data cannot tell.
- **G_emb** (pooled h{1,4}) +1.52% [-1.27, +4.32]: N4 improves on N3 by 1.52% of WIS(ref) (95% CI -1.27 to +4.32%; p = 0.265; MDE 3.93%): **inconclusive** (unadjusted rule), i.e. the CI crosses 0 and reaches past the ±1% margin: the data cannot tell.
- **G_id** (pooled h{1,4}) +0.88% [-0.48, +2.23]: N3+C* improves on N3 by 0.88% of WIS(ref) (95% CI -0.48 to +2.23%; p = 0.189; MDE 1.91%): **inconclusive** (unadjusted rule), i.e. the CI crosses 0 and reaches past the ±1% margin: the data cannot tell.
- G_excess by target type (stratum estimate, % of the stratum's WIS(L3) | additive contribution, % of the cell's WIS(L3)): positive (27% rows) +1.04 | +0.99; recorded_zero (21% rows) -5.38 | -0.27; zero_filled (52% rows) -11.40 | -0.73; identity residual 4.3e-19.
- **ID share**: not estimable: G_emb 95% CI includes 0
- Ladder (pooled h{1,4}, 2,703,183 common rows): N3+C1 0.3622, N4+C1 0.3555, N3 0.3613, N4 0.3557, N3+C* 0.3582, N4+C* 0.3581. Best = N4+C1. 80% coverage 0.82–0.84 overall, 0.40–0.42 on non-zero targets.

## 4. Sensitivity cells (T6a)

| variant | vs | estimand | variant % [95% CI] | class | primary % | primary class |
|---|---|---|---|---|---|---|
| BR_S1_3seeds | BR_S1 | G_emb | +0.26 [-0.31, +0.82] | equivalent | +0.26 | equivalent |
| BR_S1_3seeds | BR_S1 | G_id | +0.03 [-0.11, +0.18] | equivalent | +0.03 | equivalent |
| BR_S1_3seeds | BR_S1 | G_excess | +0.23 [-0.33, +0.79] | equivalent | +0.23 | equivalent |
| BR_S1_yref | BR_S1 | G_emb | +0.26 [-0.29, +0.82] | equivalent | +0.26 | equivalent |
| BR_S1_delay2 | BR_S1 | G_emb | +0.60 [-0.56, +1.76] | inconclusive | +0.26 | equivalent |
| BR_S1_ctrlC3 | BR_S1 | G_emb | +0.26 [-0.31, +0.82] | equivalent | +0.26 | equivalent |
| BR_S1_ctrlC3 | BR_S1 | G_id | -0.04 [-0.08, -0.00] | equivalent | +0.03 | equivalent |
| BR_S1_ctrlC3 | BR_S1 | G_excess | +0.28 [-0.27, +0.82] | equivalent | +0.23 | equivalent |
| BR_S1_ctrlC6 | BR_S1 | G_emb | +0.26 [-0.31, +0.82] | equivalent | +0.26 | equivalent |
| BR_S1_ctrlC6 | BR_S1 | G_id | -2.11 [-2.68, -1.54] | inferior | +0.03 | equivalent |
| BR_S1_ctrlC6 | BR_S1 | G_excess | +0.30 [-0.12, +0.71] | equivalent | +0.23 | equivalent |
| BR_S1_perlevel | BR_S1 | G_emb | +0.21 [-0.05, +0.47] | equivalent | +0.26 | equivalent |
| BR_S1_perlevel | BR_S1 | G_id | -0.06 [-0.30, +0.18] | equivalent | +0.03 | equivalent |
| BR_S1_perlevel | BR_S1 | G_excess | +0.25 [-0.07, +0.56] | equivalent | +0.23 | equivalent |
| TW_S1_BRparams | TW_S1 | G_emb | -0.87 [-1.78, +0.03] | inconclusive | -0.95 | inferior |
| TW_S1_BRparams | TW_S1 | G_id | -0.71 [-1.67, +0.26] | inconclusive | -0.41 | equivalent |
| TW_S1_BRparams | TW_S1 | G_excess | -0.33 [-0.89, +0.23] | equivalent | -0.71 | inferior |
| TW_S1_no2021 | TW_S1 | G_emb | -0.94 [-1.85, -0.03] | inferior | -0.95 | inferior |
| TW_S1_no2021 | TW_S1 | G_id | -0.63 [-1.69, +0.44] | inconclusive | -0.41 | equivalent |
| TW_S1_no2021 | TW_S1 | G_excess | -0.44 [-1.01, +0.14] | equivalent | -0.71 | inferior |
| TW_S5_no2021 | TW_S5 | G_emb | -14.68 [-20.24, -9.11] | inferior | -21.60 | inferior |
| TW_S5_no2021 | TW_S5 | G_id | -2.31 [-5.52, +0.90] | inconclusive | -3.36 | inferior |
| TW_S5_no2021 | TW_S5 | G_excess | -11.16 [-15.66, -6.65] | inferior | -18.29 | inferior |
| BR_S1_nohist | BR_S1 | G_emb | +2.54 [-0.82, +5.89] | inconclusive | +0.26 | equivalent |
| BR_S1_nohist | BR_S1 | G_id | +3.30 [+1.68, +4.93] | superior | +0.03 | equivalent |
| BR_S1_nohist | BR_S1 | G_excess | -0.43 [-2.06, +1.19] | inconclusive | +0.23 | equivalent |
| BR_S2_nohist | BR_S2 | G_emb | +1.52 [-1.27, +4.32] | inconclusive | -0.02 | equivalent |
| BR_S2_nohist | BR_S2 | G_id | +0.88 [-0.48, +2.23] | inconclusive | -0.05 | equivalent |
| BR_S2_nohist | BR_S2 | G_excess | -0.01 [-1.28, +1.27] | inconclusive | -0.00 | equivalent |

Both columns pool the primary horizons h{1,4} on origin-year rows.

## 5. Where everything is

Tables (`docs/results/tables/`, each as .csv and a LaTeX booktabs fragment .tex):

- `T1_primary_family` — the 14 family cells: absolute WIS of L3/L4/L3+C*/L4+C*, G_emb, G_id, G_excess (% of WIS(L3), 95%/90% CI), DM p, Holm p, p_bonf14, unadjusted TOST class and the Holm-adjusted TOST class, plain label, loss_or_gain, EWC B=4 p/CI (+Holm), IAAFT p (+Holm), delta-method CI, case-scale G_excess, all-rows G_excess, S1 secondary pooling (`sec_*`).
- `T1b_margin_sensitivity` — TOST at ±0.5/1/2% (unadjusted, Holm), near-margin flags, labels.
- `T2_ladder` (+ `T2_ladder_long.csv`) — ladder per cell and horizon, coverage.
- `T3_estimands` — G_emb / G_id / G_excess / ID share per cell × horizon and per test year (CSV).
- `T4_cstar_selection` — control candidates at the 2019 origin and the chosen C*.
- `T5_strata` — three target types (cases > 0 / recorded zero / zero-filled): stratum estimates and additive contributions (G_emb, G_id, G_excess in the CSV).
- `T6a_sensitivities` (incl. TW without 2021), `T6b_nohist_estimands`, `T6c_nohist_ladder`.
- Supporting: `S1_baselines`, `S2_control_panel`, `S3_outbreak`, `S4_weighted`, `S5_recalibration`, `S6_q90_mechanism`, `S7_embedding_distance` (+ `S7b_..._bins.csv`), `S8_per_year` (with context flags).

Made: T1: T1_primary_family, T1b_margin_sensitivity; T2: T2_ladder; T3: T3_estimands; T4: T4_cstar_selection; T5: T5_strata; T6: T6a_sensitivities, T6b_nohist_estimands, T6c_nohist_ladder; S1: S1_baselines; S2: S2_control_panel; S3: S3_outbreak; S4: S4_weighted; S5: S5_recalibration; S6: S6_q90_mechanism; S7: S7_embedding_distance; S8: S8_per_year

Figures (`docs/results/figures/`, PDF + PNG):

- `F1_forest_G_excess` — forest plot of G_excess per family cell (pooled h{1,4}, % of WIS(L3), 95%/90% CI, ±1% band); Taiwan S5 in its own panel
- `F2_strata_contributions` — three target types: additive contributions to G_excess per cell
- `F3_s5_embedding_distance` — held-out country (S5): AlphaEarth similarity to the training districts vs district gain
- `F4_per_year_gains` — G_excess per test year and cell
- `FS1_ladder_S1` — ladder per country, S1
- `FS2_nohist_ladder` — no-history arm ladder

Per-cell intermediate results: `runs/analysis_cache/<cell>/` (est.parquet, ladder.parquet, extras/*.parquet, info.json with row counts, filter, exclusions and seeds).

## 6. Compute status (scheduler snapshot)

```
snapshot 2026-11-20 13:29:37 (2 s old); budget 60 threads (others 112% CPU (incl. own non-pipeline jobs)) = 15 workers; held 0; free 15
  T1 brazil_s1_shared             done                                     -                                  held  0 unclaimed   0
  T1 peru_s1_shared               done                                     -                                  held  0 unclaimed   0
  T1 taiwan_s1_shared             done                                     -                                  held  0 unclaimed   0
  T1 colombia_s1_shared           done                                     -                                  held  0 unclaimed   0
  T1 taiwan_s1brp                 done                                     -                                  held  0 unclaimed   0
  T2 brazil_s1_sens_seeds         done                                     -                                  held  0 unclaimed   0
  T2 brazil_s5                    done                                     -                                  held  0 unclaimed   0
  T2 colombia_s5                  done                                     -                                  held  0 unclaimed   0
  T2 peru_s5                      done                                     -                                  held  0 unclaimed   0
  T2 taiwan_s5                    done                                     -                                  held  0 unclaimed   0
  T2 colombia_s2                  done                                     -                                  held  0 unclaimed   0
  T2 colombia_s3                  done                                     -                                  held  0 unclaimed   0
  T2 colombia_s4                  done                                     -                                  held  0 unclaimed   0
  T2 brazil_s2                    done                                     -                                  held  0 unclaimed   0
  T2 brazil_s3                    done                                     -                                  held  0 unclaimed   0
  T3 brazil_s1_nohist             done                                     -                                  held  0 unclaimed   0
  T3 brazil_s2_nohist             done                                     -                                  held  0 unclaimed   0
  T4 brazil_s1_sens_yref          done                                     -                                  held  0 unclaimed   0
  T4 brazil_s1_sens_delay         done                                     -                                  held  0 unclaimed   0
  T4 brazil_s1_sens_ctrl          done                                     -                                  held  0 unclaimed   0
  T4 taiwan_s1_l2shared           done                                     -                                  held  0 unclaimed   0
  T5 brazil_s4                    done                                     -                                  held  0 unclaimed   0
  T6 r3_co_s1_seeds               done                                     -                                  held  0 unclaimed   0
  T6 r3_co_s2_seeds               done                                     -                                  held  0 unclaimed   0
  T6 r3a_colombia_s1_r3_V1_L3     done                                     -                                  held  0 unclaimed   0
  T6 r3a_colombia_s1_r3_V1_L3_Cstar done                                     -                                  held  0 unclaimed   0
  T6 r3a_colombia_s1_r3_V2_L3     done                                     -                                  held  0 unclaimed   0
  T6 r3a_colombia_s1_r3_V2_L3_Cstar done                                     -                                  held  0 unclaimed   0
  T6 r3a_colombia_s1_r3_V3_L3     done                                     -                                  held  0 unclaimed   0
  T6 r3a_colombia_s1_r3_V3_L3_Cstar done                                     -                                  held  0 unclaimed   0
  T6 r3a_colombia_s1_r3_V4_L2     done                                     -                                  held  0 unclaimed   0
  T6 r3a_colombia_s2_r3_V1_L3     done                                     -                                  held  0 unclaimed   0
  T6 r3a_colombia_s2_r3_V1_L3_Cstar done                                     -                                  held  0 unclaimed   0
  T6 r3a_colombia_s2_r3_V2_L3     done                                     -                                  held  0 unclaimed   0
  T6 r3a_colombia_s2_r3_V2_L3_Cstar done                                     -                                  held  0 unclaimed   0
  T6 r3a_colombia_s2_r3_V3_L3     done                                     -                                  held  0 unclaimed   0
  T6 r3a_colombia_s2_r3_V3_L3_Cstar done                                     -                                  held  0 unclaimed   0
  T6 r3a_colombia_s2_r3_V4_L2     done                                     -                                  held  0 unclaimed   0
  T6 r3a_taiwan_s1_r3_V1_L3       done                                     -                                  held  0 unclaimed   0
  T6 r3a_taiwan_s1_r3_V1_L3_Cstar done                                     -                                  held  0 unclaimed   0
  T6 r3a_taiwan_s1_r3_V2_L3       done                                     -                                  held  0 unclaimed   0
  T6 r3a_taiwan_s1_r3_V2_L3_Cstar done                                     -                                  held  0 unclaimed   0
  T6 r3a_taiwan_s1_r3_V3_L3       done                                     -                                  held  0 unclaimed   0
  T6 r3a_taiwan_s1_r3_V3_L3_Cstar done                                     -                                  held  0 unclaimed   0
  T6 r3a_taiwan_s1_r3_V4_L2       done                                     -                                  held  0 unclaimed   0
  T6 r3a_peru_s1_r3_V1_L3         done                                     -                                  held  0 unclaimed   0
  T6 r3a_peru_s1_r3_V1_L3_Cstar   done                                     -                                  held  0 unclaimed   0
  T6 r3a_peru_s1_r3_V2_L3         done                                     -                                  held  0 unclaimed   0
  T6 r3a_peru_s1_r3_V2_L3_Cstar   done                                     -                                  held  0 unclaimed   0
  T6 r3a_peru_s1_r3_V3_L3         done                                     -                                  held  0 unclaimed   0
  T6 r3a_peru_s1_r3_V3_L3_Cstar   done                                     -                                  held  0 unclaimed   0
  T6 r3a_peru_s1_r3_V4_L2         done                                     -                                  held  0 unclaimed   0
  T6 r3a_brazil_s2_r3_V1_L3       done                                     -                                  held  0 unclaimed   0
  T6 r3a_brazil_s2_r3_V1_L3_Cstar done                                     -                                  held  0 unclaimed   0
  T6 r3a_brazil_s2_r3_V2_L3       done                                     -                                  held  0 unclaimed   0
  T6 r3a_brazil_s2_r3_V2_L3_Cstar done                                     -                                  held  0 unclaimed   0
  T6 r3_br_s5_seeds               done                                     -                                  held  0 unclaimed   0
  T6 r3_tw_s1_ladder2021          done                                     -                                  held  0 unclaimed   0
  T6 r3_tw_s5_seeds               done                                     -                                  held  0 unclaimed   0
  T6 r3_pe_s5_seeds               done                                     -                                  held  0 unclaimed   0
  T6 r3_co_s1_tuning              done                                     -                                  held  0 unclaimed   0
  T6 r3_co_s2_nohist              done                                     -                                  held  0 unclaimed   0
  T6 r3_co_s3_seeds               done                                     -                                  held  0 unclaimed   0
  T6 r3_co_s4_seeds               done                                     -                                  held  0 unclaimed   0
  T6 r3_pe_s1_seeds               done                                     -                                  held  0 unclaimed   0
  T6 r3_tw_s1_seeds               done                                     -                                  held  0 unclaimed   0
```
