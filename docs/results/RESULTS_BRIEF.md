# RESULTS BRIEF (auto-generated, results kit v3)

Generated 2026-11-18 02:14 by `scripts/analysis/make_results.py`. Do not edit by hand: re-run the script. All numbers are log1p-scale WIS unless marked 'case scale'; a gain is positive when the second model has the lower WIS. Percentages are of WIS(L3) (WIS(N3) in the no-history arm).

**Scored rows (deviation row 24).** Every estimate keeps only rows whose forecast origin (target week − h) lies in the same epi-year as the target, which removes the yearly-feature and training-label look-ahead (review R1): at h1 the first epi-week of each test year is dropped (1.9% of rows), at h4 the first four (7.7%). T1 also shows G_excess on all rows ('all rows %').

**Horizons.** Every 'pooled' estimate pools the primary horizons **h{1,4}** in every cell (row 21); S1 cells also show a secondary pooling over h1-4 (`horizon = pooled_h1-4`), which is never in the Holm family and uses only test years scored at all four horizons.

**Inference.** DM test with EWC long-run variance and HLN correction on the weekly cross-unit mean loss difference; TOST against ±1% of WIS(L3); Holm over the 14-cell family (DM p and TOST p separately). Robustness columns: EWC with B = 4 cosine terms, IAAFT-surrogate-calibrated p (review RC), delta-method CI that treats WIS(L3) as estimated, case-scale G_excess. See `docs/methods/results_kit.md`.

**Exclusions (row 34).** Primary scoring uses `data/processed/exclusions_v2/`: v1 (units without geometry, incomplete weeks) plus every Espírito Santo row of every test year (target weeks from 2019-12-29) (the source has false zeros for all 78 municipalities while InfoDengue shows cases). Applied to all four models at scoring only; the models were not refitted, so 2020–23 training targets still contain these false zeros. T1 shows G_excess under the v1 exclusions ('v1 excl %').

**Taiwan (row 25).** Both Taiwan cells use test years 2020–2024 including 2021, a year with no local cases; the pre-review set (without 2021) is the sensitivity cell `TW_*_no2021`. A cell whose 2021 runs are not finished uses its base runs and is flagged '2021 pending'.

**Loss-counting rule.** A cell counts as a **loss** (gain) when its G_excess is negative (positive) and the Holm-adjusted DM p over the 14-cell family is < .05; a loss is **small** when the point estimate is inside ±1% of WIS(L3). Nominal (unadjusted) p < .05 alone is reported as 'nominal', never counted. While a family cell is pending, Holm runs over the available cells and the count is provisional.

Key: **G_emb** = WIS(L3) − WIS(L4) (raw AlphaEarth gain); **G_id** = WIS(L3) − WIS(L3+C*) (gain from a location/ID control); **G_excess** = WIS(L3+C*) − WIS(L4+C*) (primary: what AlphaEarth adds beyond the best ID control).

## 1. Headline table (T1)

Family: **13 of 14 cells available** — Holm p values are over the available cells and are **provisional**.

| cell | C* | G_excess % [95% CI] | DM p | Holm p | label (±1%) | B=4 p | IAAFT p | all rows % | v1 excl % | case % |
|---|---|---|---|---|---|---|---|---|---|---|
| BR_S1 | C1 | +0.23 [-0.33, +0.79] | 0.392 | 0.802 | no significant difference; within ±1% (TOST, Holm-adjusted) | 0.447 | 0.507 | +0.26 | +0.23 | -0.03 |
| BR_S2 | C1 | -0.00 [-0.34, +0.34] | 0.996 | 0.996 | no significant difference; within ±1% (TOST, Holm-adjusted) | 0.997 | 0.997 | +0.03 | -0.01 | -0.73 |
| BR_S3 | C1 | -0.16 [-0.34, +0.03] | 0.090 | 0.395 | no significant difference; within ±1% (TOST, Holm-adjusted) | 0.259 | 0.214 | -0.10 | -0.19 | -1.30 |
| BR_S4 | selection pending (stale) | pending | | | | | | | | |
| BR_S5 | C3 | -0.60 [-0.84, -0.36] | 7.5e-05 | 0.00097 | small negative difference, significant after Holm correction; within ±1% (TOST, Holm-adjusted) | 0.002 | 0.0005 | -0.62 | -0.61 | -0.86 |
| CO_S1 | C1 | -0.39 [-0.58, -0.19] | 0.001 | 0.011 | small negative difference, significant after Holm correction; within ±1% (TOST, Holm-adjusted) | 0.007 | 0.001 | -0.39 | n/a | -0.81 |
| CO_S2 | C1 | -0.47 [-0.69, -0.25] | 0.00056 | 0.006 | small negative difference, significant after Holm correction; within ±1% (TOST, Holm-adjusted) | 0.002 | 0.0005 | -0.48 | n/a | -0.64 |
| CO_S3 | C1 | -0.65 [-1.04, -0.27] | 0.003 | 0.026 | small negative difference, significant after Holm correction; within ±1% (unadjusted TOST only) | 0.008 | 0.0005 | -0.68 | n/a | -0.70 |
| CO_S4 | C1 | -0.43 [-0.68, -0.18] | 0.003 | 0.025 | small negative difference, significant after Holm correction; within ±1% (TOST, Holm-adjusted) | 0.016 | 0.006 | -0.44 | n/a | -0.88 |
| CO_S5 | C2 | +0.22 [-0.19, +0.63] | 0.267 | 0.802 | no significant difference; within ±1% (TOST, Holm-adjusted) | 0.490 | 0.461 | +0.18 | n/a | +0.51 |
| PE_S1 | C1 | -0.70 [-1.41, +0.02] | 0.056 | 0.342 | no significant difference; not shown to be within ±1% | 0.159 | 0.083 | -0.62 | n/a | -1.14 |
| PE_S5 | C3 | +0.96 [-0.13, +2.05] | 0.079 | 0.395 | no significant difference; not shown to be within ±1% | 0.023 | 0.006 | +1.01 | n/a | -0.59 |
| TW_S1 | C1 | -0.60 [-1.20, -0.00] | 0.049 | 0.342 | nominal small negative difference, not significant after Holm correction; not shown to be within ±1% | 0.104 | 0.078 | -0.55 | n/a | -0.00 |
| TW_S5 (2021 pending (base test years only)) | C3 | -11.16 [-15.66, -6.65] | 0.00013 | 0.002 | negative difference, significant after Holm correction; not shown to be within ±1% | 0.004 | 0.001 | -11.53 | n/a | -2.93 |

Counts under the loss-counting rule: loss: 1, nominal only: 1, none: 6, pending: 1, small loss: 5.

## 2. Status of every cell

| cell | group | description | C* | status | flags / what is missing |
|---|---|---|---|---|---|
| BR_S1 | primary/history | Brazil S1, history arm (primary) | C1 | available |  |
| BR_S2 | primary/history | Brazil S2, history arm (primary) | C1 | available |  |
| BR_S3 | primary/history | Brazil S3, history arm (primary) | C1 | available |  |
| BR_S4 | primary/history | Brazil S4, history arm (primary) | selection pending (stale) | pending | L3: brazil_s4_L3: not started; L4: brazil_s4_L4: not started; L3C: brazil_s4_L3_Cstar: not started; L4C: brazil_s4_L4_Cstar: not started |
| BR_S5 | primary/history | Brazil S5, history arm (primary) | C3 | available |  |
| CO_S1 | primary/history | Colombia S1, history arm (primary) | C1 | available |  |
| CO_S2 | primary/history | Colombia S2, history arm (primary) | C1 | available |  |
| CO_S3 | primary/history | Colombia S3, history arm (primary) | C1 | available |  |
| CO_S4 | primary/history | Colombia S4, history arm (primary) | C1 | available |  |
| CO_S5 | primary/history | Colombia S5, history arm (primary) | C2 | available |  |
| PE_S1 | primary/history | Peru S1, history arm (primary) | C1 | available |  |
| PE_S5 | primary/history | Peru S5, history arm (primary) | C3 | available |  |
| TW_S1 | primary/history | Taiwan S1, history arm (primary); test years incl. 2021 | C1 | available |  |
| TW_S5 | primary/history | Taiwan S5, history arm (primary) | C3 | available | 2021 pending (base test years only) |
| TW_S1_no2021 | secondary/sensitivity | Taiwan S1 without test year(s) 2021 (the pre-review test-year set) | C1 | available |  |
| TW_S5_no2021 | secondary/sensitivity | Taiwan S5 without test year(s) 2021 (the pre-review test-year set) | C3 | available |  |
| BR_S1_3seeds | secondary/sensitivity | Brazil S1, primary + 2 extra seeds (seed-averaged; extra seeds h1/h4) | C1 | available |  |
| BR_S1_yref | secondary/sensitivity | Brazil S1 sensitivity: yearly features aligned to the origin year (strictly causal) (G_emb only) | n/a (no C* run) | pending | L3: brazil_s1_sens_yref_L3: not started; L4: brazil_s1_sens_yref_L4: not started; L3C: brazil_s1_sens_yref_L3: not started; L4C: brazil_s1_sens_yref_L4: not started |
| BR_S1_delay2 | secondary/sensitivity | Brazil S1 sensitivity: 2-week reporting delay (G_emb only) | n/a (no C* run) | pending | L3: brazil_s1_sens_delay2_L3: not started; L4: brazil_s1_sens_delay2_L4: not started; L3C: brazil_s1_sens_delay2_L3: not started; L4C: brazil_s1_sens_delay2_L4: not started |
| BR_S1_ctrlC3 | secondary/sensitivity | Brazil S1 controls panel: C3 in place of C* (h1, h4) | C3 | pending | L3C: brazil_s1_sens_ctrl_L3_C3: not started; L4C: brazil_s1_sens_ctrl_L4_C3: not started |
| BR_S1_ctrlC6 | secondary/sensitivity | Brazil S1 controls panel: C6 in place of C* (h1, h4) | C6 | pending | L3C: brazil_s1_sens_ctrl_L3_C6: not started; L4C: brazil_s1_sens_ctrl_L4_C6: not started |
| BR_S1_perlevel | secondary/sensitivity | Brazil S1, per-level tuning (L3/L4 31 leaves; superseded primary) | C1 | available |  |
| TW_S1_BRparams | secondary/sensitivity | Taiwan S1 with Brazil's tuned params and C* | C1 | available |  |
| BR_S1_nohist | secondary/no-history | Brazil S1, no-history arm (ref = N3) | C2 | pending | L3: brazil_s1_nohist_N3: partial (2 chunks); L4: brazil_s1_nohist_N4: not started; L3C: brazil_s1_nohist_N3_Cstar: not started; L4C: brazil_s1_nohist_N4_Cstar: not started |
| BR_S2_nohist | secondary/no-history | Brazil S2, no-history arm (ref = N3) | selection pending (stale) | pending | L3: brazil_s2_nohist_N3: not started; L4: brazil_s2_nohist_N4: not started; L3C: brazil_s2_nohist_N3_Cstar: not started; L4C: brazil_s2_nohist_N4_Cstar: not started |

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

### BR_S5: Brazil S5, history arm (primary) (C* = C3)
Rows scored (primary horizons) 2,703,183; row filter origin_year dropped 135,975 rows of 2839158 (all horizons); test years [2020, 2021, 2022, 2023, 2024]; seeds [0]; zero-filled share 0.52; outbreak share 0.082.

- **G_excess** (pooled h{1,4}) -0.60% [-0.84, -0.36]: L4+C* is worse than L3+C* by 0.60% of WIS(ref) (95% CI -0.84 to -0.36%; p = 0.000; MDE 0.34%): **equivalent** (unadjusted rule), i.e. the 90% CI lies inside ±1% of WIS(ref): any effect is too small to matter.
- **G_emb** (pooled h{1,4}) -0.34% [-1.24, +0.56]: L4 is worse than L3 by 0.34% of WIS(ref) (95% CI -1.24 to +0.56%; p = 0.439; MDE 1.27%): **inconclusive** (unadjusted rule), i.e. the CI crosses 0 and reaches past the ±1% margin: the data cannot tell.
- **G_id** (pooled h{1,4}) +0.10% [-0.75, +0.96]: L3+C* improves on L3 by 0.10% of WIS(ref) (95% CI -0.75 to +0.96%; p = 0.797; MDE 1.20%): **equivalent** (unadjusted rule), i.e. the 90% CI lies inside ±1% of WIS(ref): any effect is too small to matter.
- G_excess by target type (stratum estimate, % of the stratum's WIS(L3) | additive contribution, % of the cell's WIS(L3)): positive (27% rows) +0.55 | +0.28; recorded_zero (21% rows) -2.69 | -0.22; zero_filled (52% rows) -5.22 | -0.66; identity residual 0.0e+00.
- **ID share**: not estimable: G_emb 95% CI includes 0
- Ladder (pooled h{1,4}, 2,703,183 common rows): L3 0.1914, L4 0.1921, L3+C* 0.1912, L4+C* 0.1924. Best = L3+C*. 80% coverage 0.87–0.88 overall, 0.60–0.64 on non-zero targets.

### CO_S1: Colombia S1, history arm (primary) (C* = C1)
Rows scored (primary horizons) 319,930; row filter origin_year dropped 32,100 rows of 671960 (all horizons); test years [2020, 2021, 2022]; seeds [0]; zero-filled share 0.79; outbreak share 0.023.

- **G_excess** (pooled h{1,4}) -0.39% [-0.58, -0.19]: L4+C* is worse than L3+C* by 0.39% of WIS(ref) (95% CI -0.58 to -0.19%; p = 0.001; MDE 0.27%): **equivalent** (unadjusted rule), i.e. the 90% CI lies inside ±1% of WIS(ref): any effect is too small to matter.
- **G_emb** (pooled h{1,4}) -0.36% [-0.58, -0.13]: L4 is worse than L3 by 0.36% of WIS(ref) (95% CI -0.58 to -0.13%; p = 0.005; MDE 0.31%): **equivalent** (unadjusted rule), i.e. the 90% CI lies inside ±1% of WIS(ref): any effect is too small to matter.
- **G_id** (pooled h{1,4}) -0.07% [-0.34, +0.20]: L3+C* is worse than L3 by 0.07% of WIS(ref) (95% CI -0.34 to +0.20%; p = 0.602; MDE 0.38%): **equivalent** (unadjusted rule), i.e. the 90% CI lies inside ±1% of WIS(ref): any effect is too small to matter.
- *Secondary* G_excess pooled over h1-4 (years [2020, 2021, 2022]; not in the Holm family): -0.39% [-0.61, -0.17]; p = 0.002; equivalent.
- G_excess by target type (stratum estimate, % of the stratum's WIS(L3) | additive contribution, % of the cell's WIS(L3)): positive (21% rows) +0.28 | +0.21; recorded_zero (0% rows) n/a | +0.00; zero_filled (79% rows) -2.11 | -0.59; identity residual 0.0e+00.
- **ID share**: not estimable: G_emb significantly negative (embeddings hurt)
- Ladder (pooled h{1,4}, 319,930 common rows): L0 0.3272, L1 0.1226, L2 0.1224, L3 0.1220, L4 0.1225, L3+C* 0.1221, L4+C* 0.1226. Best = L3. 80% coverage 0.81–0.93 overall, 0.53–0.72 on non-zero targets.

### CO_S2: Colombia S2, history arm (primary) (C* = C1)
Rows scored (primary horizons) 319,930; row filter origin_year dropped 16,050 rows of 335980 (all horizons); test years [2020, 2021, 2022]; seeds [0]; zero-filled share 0.79; outbreak share 0.023.

- **G_excess** (pooled h{1,4}) -0.47% [-0.69, -0.25]: L4+C* is worse than L3+C* by 0.47% of WIS(ref) (95% CI -0.69 to -0.25%; p = 0.001; MDE 0.30%): **equivalent** (unadjusted rule), i.e. the 90% CI lies inside ±1% of WIS(ref): any effect is too small to matter.
- **G_emb** (pooled h{1,4}) -0.59% [-0.80, -0.37]: L4 is worse than L3 by 0.59% of WIS(ref) (95% CI -0.80 to -0.37%; p = 0.000; MDE 0.30%): **equivalent** (unadjusted rule), i.e. the 90% CI lies inside ±1% of WIS(ref): any effect is too small to matter.
- **G_id** (pooled h{1,4}) -0.08% [-0.13, -0.04]: L3+C* is worse than L3 by 0.08% of WIS(ref) (95% CI -0.13 to -0.04%; p = 0.002; MDE 0.06%): **equivalent** (unadjusted rule), i.e. the 90% CI lies inside ±1% of WIS(ref): any effect is too small to matter.
- G_excess by target type (stratum estimate, % of the stratum's WIS(L3) | additive contribution, % of the cell's WIS(L3)): positive (21% rows) +0.26 | +0.22; recorded_zero (0% rows) n/a | +0.00; zero_filled (79% rows) -2.46 | -0.69; identity residual 0.0e+00.
- **ID share**: not estimable: G_emb significantly negative (embeddings hurt)
- Ladder (pooled h{1,4}, 319,930 common rows): L3 0.1224, L4 0.1232, L3+C* 0.1225, L4+C* 0.1231. Best = L3. 80% coverage 0.92–0.92 overall, 0.70–0.71 on non-zero targets.

### CO_S3: Colombia S3, history arm (primary) (C* = C1)
Rows scored (primary horizons) 319,930; row filter origin_year dropped 16,050 rows of 335980 (all horizons); test years [2020, 2021, 2022]; seeds [0]; zero-filled share 0.79; outbreak share 0.023.

- **G_excess** (pooled h{1,4}) -0.65% [-1.04, -0.27]: L4+C* is worse than L3+C* by 0.65% of WIS(ref) (95% CI -1.04 to -0.27%; p = 0.003; MDE 0.54%): **equivalent** (unadjusted rule), i.e. the 90% CI lies inside ±1% of WIS(ref): any effect is too small to matter.
- **G_emb** (pooled h{1,4}) -0.83% [-1.14, -0.52]: L4 is worse than L3 by 0.83% of WIS(ref) (95% CI -1.14 to -0.52%; p = 0.000; MDE 0.44%): **inferior** (unadjusted rule), i.e. the 95% CI excludes 0 on the harm side: the second model is worse.
- **G_id** (pooled h{1,4}) -0.13% [-0.22, -0.05]: L3+C* is worse than L3 by 0.13% of WIS(ref) (95% CI -0.22 to -0.05%; p = 0.007; MDE 0.12%): **equivalent** (unadjusted rule), i.e. the 90% CI lies inside ±1% of WIS(ref): any effect is too small to matter.
- G_excess by target type (stratum estimate, % of the stratum's WIS(L3) | additive contribution, % of the cell's WIS(L3)): positive (21% rows) +0.15 | +0.10; recorded_zero (0% rows) n/a | +0.00; zero_filled (79% rows) -2.55 | -0.76; identity residual 0.0e+00.
- **ID share**: not estimable: G_emb significantly negative (embeddings hurt)
- Ladder (pooled h{1,4}, 319,930 common rows): L3 0.1244, L4 0.1255, L3+C* 0.1246, L4+C* 0.1254. Best = L3. 80% coverage 0.92–0.92 overall, 0.70–0.71 on non-zero targets.

### CO_S4: Colombia S4, history arm (primary) (C* = C1)
Rows scored (primary horizons) 319,930; row filter origin_year dropped 16,050 rows of 335980 (all horizons); test years [2020, 2021, 2022]; seeds [0]; zero-filled share 0.79; outbreak share 0.023.

- **G_excess** (pooled h{1,4}) -0.43% [-0.68, -0.18]: L4+C* is worse than L3+C* by 0.43% of WIS(ref) (95% CI -0.68 to -0.18%; p = 0.003; MDE 0.35%): **equivalent** (unadjusted rule), i.e. the 90% CI lies inside ±1% of WIS(ref): any effect is too small to matter.
- **G_emb** (pooled h{1,4}) -0.52% [-0.75, -0.28]: L4 is worse than L3 by 0.52% of WIS(ref) (95% CI -0.75 to -0.28%; p = 0.001; MDE 0.33%): **equivalent** (unadjusted rule), i.e. the 90% CI lies inside ±1% of WIS(ref): any effect is too small to matter.
- **G_id** (pooled h{1,4}) -0.13% [-0.18, -0.08]: L3+C* is worse than L3 by 0.13% of WIS(ref) (95% CI -0.18 to -0.08%; p = 0.000; MDE 0.07%): **equivalent** (unadjusted rule), i.e. the 90% CI lies inside ±1% of WIS(ref): any effect is too small to matter.
- G_excess by target type (stratum estimate, % of the stratum's WIS(L3) | additive contribution, % of the cell's WIS(L3)): positive (21% rows) +0.31 | +0.26; recorded_zero (0% rows) n/a | +0.00; zero_filled (79% rows) -2.48 | -0.69; identity residual 0.0e+00.
- **ID share**: not estimable: G_emb significantly negative (embeddings hurt)
- Ladder (pooled h{1,4}, 319,930 common rows): L3 0.1222, L4 0.1229, L3+C* 0.1224, L4+C* 0.1229. Best = L3. 80% coverage 0.92–0.93 overall, 0.71–0.71 on non-zero targets.

### CO_S5: Colombia S5, history arm (primary) (C* = C2)
Rows scored (primary horizons) 319,930; row filter origin_year dropped 16,050 rows of 335980 (all horizons); test years [2020, 2021, 2022]; seeds [0]; zero-filled share 0.79; outbreak share 0.023.

- **G_excess** (pooled h{1,4}) +0.22% [-0.19, +0.63]: L4+C* improves on L3+C* by 0.22% of WIS(ref) (95% CI -0.19 to +0.63%; p = 0.267; MDE 0.57%): **equivalent** (unadjusted rule), i.e. the 90% CI lies inside ±1% of WIS(ref): any effect is too small to matter.
- **G_emb** (pooled h{1,4}) -0.04% [-0.37, +0.28]: L4 is worse than L3 by 0.04% of WIS(ref) (95% CI -0.37 to +0.28%; p = 0.774; MDE 0.46%): **equivalent** (unadjusted rule), i.e. the 90% CI lies inside ±1% of WIS(ref): any effect is too small to matter.
- **G_id** (pooled h{1,4}) -0.81% [-1.16, -0.46]: L3+C* is worse than L3 by 0.81% of WIS(ref) (95% CI -1.16 to -0.46%; p = 0.000; MDE 0.49%): **inferior** (unadjusted rule), i.e. the 95% CI excludes 0 on the harm side: the second model is worse.
- G_excess by target type (stratum estimate, % of the stratum's WIS(L3) | additive contribution, % of the cell's WIS(L3)): positive (21% rows) +0.37 | +0.27; recorded_zero (0% rows) n/a | +0.00; zero_filled (79% rows) -0.13 | -0.05; identity residual 0.0e+00.
- **ID share**: not estimable: G_emb 95% CI includes 0
- Ladder (pooled h{1,4}, 319,930 common rows): L3 0.1238, L4 0.1239, L3+C* 0.1249, L4+C* 0.1246. Best = L3. 80% coverage 0.93–0.94 overall, 0.68–0.75 on non-zero targets.

### PE_S1: Peru S1, history arm (primary) (C* = C1)
Rows scored (primary horizons) 45,754; row filter origin_year dropped 4,600 rows of 96108 (all horizons); test years [2020, 2021, 2022, 2023]; seeds [0]; zero-filled share 0.56; outbreak share 0.229.

- **G_excess** (pooled h{1,4}) -0.70% [-1.41, +0.02]: L4+C* is worse than L3+C* by 0.70% of WIS(ref) (95% CI -1.41 to +0.02%; p = 0.056; MDE 1.01%): **inconclusive** (unadjusted rule), i.e. the CI crosses 0 and reaches past the ±1% margin: the data cannot tell.
- **G_emb** (pooled h{1,4}) -0.94% [-1.70, -0.18]: L4 is worse than L3 by 0.94% of WIS(ref) (95% CI -1.70 to -0.18%; p = 0.020; MDE 1.07%): **inferior** (unadjusted rule), i.e. the 95% CI excludes 0 on the harm side: the second model is worse.
- **G_id** (pooled h{1,4}) -0.26% [-1.05, +0.53]: L3+C* is worse than L3 by 0.26% of WIS(ref) (95% CI -1.05 to +0.53%; p = 0.493; MDE 1.11%): **equivalent** (unadjusted rule), i.e. the 90% CI lies inside ±1% of WIS(ref): any effect is too small to matter.
- *Secondary* G_excess pooled over h1-4 (years [2020, 2021, 2022, 2023]; not in the Holm family): -0.63% [-1.35, +0.08]; p = 0.077; inconclusive.
- G_excess by target type (stratum estimate, % of the stratum's WIS(L3) | additive contribution, % of the cell's WIS(L3)): positive (44% rows) -0.08 | +0.04; recorded_zero (0% rows) n/a | +0.00; zero_filled (56% rows) -6.14 | -0.74; identity residual 2.2e-19.
- **ID share**: not estimable: G_emb significantly negative (embeddings hurt)
- Ladder (pooled h{1,4}, 45,754 common rows): L0 0.6596, L1 0.2442, L2 0.2431, L3 0.2438, L4 0.2462, L3+C* 0.2445, L4+C* 0.2462. Best = L2. 80% coverage 0.73–0.84 overall, 0.47–0.70 on non-zero targets.

### PE_S5: Peru S5, history arm (primary) (C* = C3)
Rows scored (primary horizons) 45,754; row filter origin_year dropped 2,300 rows of 48054 (all horizons); test years [2020, 2021, 2022, 2023]; seeds [0]; zero-filled share 0.56; outbreak share 0.229.

- **G_excess** (pooled h{1,4}) +0.96% [-0.13, +2.05]: L4+C* improves on L3+C* by 0.96% of WIS(ref) (95% CI -0.13 to +2.05%; p = 0.079; MDE 1.53%): **inconclusive** (unadjusted rule), i.e. the CI crosses 0 and reaches past the ±1% margin: the data cannot tell.
- **G_emb** (pooled h{1,4}) +0.68% [-0.59, +1.96]: L4 improves on L3 by 0.68% of WIS(ref) (95% CI -0.59 to +1.96%; p = 0.268; MDE 1.79%): **inconclusive** (unadjusted rule), i.e. the CI crosses 0 and reaches past the ±1% margin: the data cannot tell.
- **G_id** (pooled h{1,4}) -0.44% [-0.80, -0.07]: L3+C* is worse than L3 by 0.44% of WIS(ref) (95% CI -0.80 to -0.07%; p = 0.022; MDE 0.51%): **equivalent** (unadjusted rule), i.e. the 90% CI lies inside ±1% of WIS(ref): any effect is too small to matter.
- G_excess by target type (stratum estimate, % of the stratum's WIS(L3) | additive contribution, % of the cell's WIS(L3)): positive (44% rows) +1.61 | +1.28; recorded_zero (0% rows) n/a | +0.00; zero_filled (56% rows) -2.97 | -0.32; identity residual 0.0e+00.
- **ID share**: not estimable: G_emb 95% CI includes 0
- Ladder (pooled h{1,4}, 45,754 common rows): L3 0.2383, L4 0.2367, L3+C* 0.2394, L4+C* 0.2371. Best = L4. 80% coverage 0.83–0.84 overall, 0.65–0.68 on non-zero targets.

### TW_S1: Taiwan S1, history arm (primary); test years incl. 2021 (C* = C1)
Rows scored (primary horizons) 141,645; row filter origin_year dropped 12,825 rows of 267900 (all horizons); test years [2020, 2021, 2022, 2023, 2024]; seeds [0]; zero-filled share 0.97; outbreak share 0.008.

- **G_excess** (pooled h{1,4}) -0.60% [-1.20, -0.00]: L4+C* is worse than L3+C* by 0.60% of WIS(ref) (95% CI -1.20 to -0.00%; p = 0.049; MDE 0.84%): **inferior** (unadjusted rule), i.e. the 95% CI excludes 0 on the harm side: the second model is worse.
- **G_emb** (pooled h{1,4}) -1.06% [-1.96, -0.16]: L4 is worse than L3 by 1.06% of WIS(ref) (95% CI -1.96 to -0.16%; p = 0.024; MDE 1.27%): **inferior** (unadjusted rule), i.e. the 95% CI excludes 0 on the harm side: the second model is worse.
- **G_id** (pooled h{1,4}) -0.63% [-1.68, +0.43]: L3+C* is worse than L3 by 0.63% of WIS(ref) (95% CI -1.68 to +0.43%; p = 0.225; MDE 1.48%): **inconclusive** (unadjusted rule), i.e. the CI crosses 0 and reaches past the ±1% margin: the data cannot tell.
- *Secondary* G_excess pooled over h1-4 (years [2020, 2022, 2023, 2024]; not in the Holm family): -0.38% [-0.92, +0.15]; p = 0.145; equivalent.
- G_excess by target type (stratum estimate, % of the stratum's WIS(L3) | additive contribution, % of the cell's WIS(L3)): positive (2% rows) -0.15 | -0.07; recorded_zero (0% rows) n/a | +0.00; zero_filled (98% rows) -9.46 | -0.53; identity residual 0.0e+00.
- **ID share**: not estimable: G_emb significantly negative (embeddings hurt)
- Ladder (pooled h{1,4}, 113,430 common rows): L0 0.0922, L1 0.0394, L2 0.0477, L3 0.0398, L4 0.0402, L3+C* 0.0400, L4+C* 0.0402. Best = L1. 80% coverage 0.94–0.98 overall, 0.00–0.25 on non-zero targets.

### TW_S5: Taiwan S5, history arm (primary) (C* = C3)
Rows scored (primary horizons) 113,430; row filter origin_year dropped 5,700 rows of 119130 (all horizons); test years [2020, 2022, 2023, 2024]; seeds [0]; zero-filled share 0.97; outbreak share 0.009. Flags: 2021 pending (base test years only).

- **G_excess** (pooled h{1,4}) -11.16% [-15.66, -6.65]: L4+C* is worse than L3+C* by 11.16% of WIS(ref) (95% CI -15.66 to -6.65%; p = 0.000; MDE 6.32%): **inferior** (unadjusted rule), i.e. the 95% CI excludes 0 on the harm side: the second model is worse.
- **G_emb** (pooled h{1,4}) -14.68% [-20.24, -9.11]: L4 is worse than L3 by 14.68% of WIS(ref) (95% CI -20.24 to -9.11%; p = 0.000; MDE 7.81%): **inferior** (unadjusted rule), i.e. the 95% CI excludes 0 on the harm side: the second model is worse.
- **G_id** (pooled h{1,4}) -2.31% [-5.52, +0.90]: L3+C* is worse than L3 by 2.31% of WIS(ref) (95% CI -5.52 to +0.90%; p = 0.145; MDE 4.51%): **inconclusive** (unadjusted rule), i.e. the CI crosses 0 and reaches past the ±1% margin: the data cannot tell.
- G_excess by target type (stratum estimate, % of the stratum's WIS(L3) | additive contribution, % of the cell's WIS(L3)): positive (3% rows) +2.16 | +1.33; recorded_zero (0% rows) n/a | +0.00; zero_filled (97% rows) -35.22 | -12.48; identity residual 0.0e+00.
- **ID share**: not estimable: G_emb significantly negative (embeddings hurt)
- Ladder (pooled h{1,4}, 113,430 common rows): L3 0.0246, L4 0.0283, L3+C* 0.0252, L4+C* 0.0280. Best = L3. 80% coverage 0.99–0.99 overall, 0.56–0.63 on non-zero targets.

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

## 4. Sensitivity cells (T6a)

| variant | vs | estimand | variant % [95% CI] | class | primary % | primary class |
|---|---|---|---|---|---|---|
| BR_S1_3seeds | BR_S1 | G_emb | +0.26 [-0.31, +0.82] | equivalent | +0.26 | equivalent |
| BR_S1_3seeds | BR_S1 | G_id | +0.03 [-0.11, +0.18] | equivalent | +0.03 | equivalent |
| BR_S1_3seeds | BR_S1 | G_excess | +0.23 [-0.33, +0.79] | equivalent | +0.23 | equivalent |
| BR_S1_yref | BR_S1 | G_emb | pending | pending | +0.26 | equivalent |
| BR_S1_delay2 | BR_S1 | G_emb | pending | pending | +0.26 | equivalent |
| BR_S1_ctrlC3 | BR_S1 | G_emb | pending | pending | +0.26 | equivalent |
| BR_S1_ctrlC3 | BR_S1 | G_id | pending | pending | +0.03 | equivalent |
| BR_S1_ctrlC3 | BR_S1 | G_excess | pending | pending | +0.23 | equivalent |
| BR_S1_ctrlC6 | BR_S1 | G_emb | pending | pending | +0.26 | equivalent |
| BR_S1_ctrlC6 | BR_S1 | G_id | pending | pending | +0.03 | equivalent |
| BR_S1_ctrlC6 | BR_S1 | G_excess | pending | pending | +0.23 | equivalent |
| BR_S1_perlevel | BR_S1 | G_emb | +0.21 [-0.05, +0.47] | equivalent | +0.26 | equivalent |
| BR_S1_perlevel | BR_S1 | G_id | -0.06 [-0.30, +0.18] | equivalent | +0.03 | equivalent |
| BR_S1_perlevel | BR_S1 | G_excess | +0.25 [-0.07, +0.56] | equivalent | +0.23 | equivalent |
| TW_S1_BRparams | TW_S1 | G_emb | -0.87 [-1.78, +0.03] | inconclusive | -1.06 | inferior |
| TW_S1_BRparams | TW_S1 | G_id | -0.71 [-1.67, +0.26] | inconclusive | -0.63 | inconclusive |
| TW_S1_BRparams | TW_S1 | G_excess | -0.33 [-0.89, +0.23] | equivalent | -0.60 | inferior |
| TW_S1_no2021 | TW_S1 | G_emb | -0.94 [-1.85, -0.03] | inferior | -1.06 | inferior |
| TW_S1_no2021 | TW_S1 | G_id | -0.63 [-1.69, +0.44] | inconclusive | -0.63 | inconclusive |
| TW_S1_no2021 | TW_S1 | G_excess | -0.44 [-1.01, +0.14] | equivalent | -0.60 | inferior |
| TW_S5_no2021 | TW_S5 | G_emb | -14.68 [-20.24, -9.11] | inferior | -14.68 | inferior |
| TW_S5_no2021 | TW_S5 | G_id | -2.31 [-5.52, +0.90] | inconclusive | -2.31 | inconclusive |
| TW_S5_no2021 | TW_S5 | G_excess | -11.16 [-15.66, -6.65] | inferior | -11.16 | inferior |
| BR_S1_nohist | BR_S1 | G_emb | pending | pending | +0.26 | equivalent |
| BR_S1_nohist | BR_S1 | G_id | pending | pending | +0.03 | equivalent |
| BR_S1_nohist | BR_S1 | G_excess | pending | pending | +0.23 | equivalent |
| BR_S2_nohist | BR_S2 | G_emb | pending | pending | -0.02 | equivalent |
| BR_S2_nohist | BR_S2 | G_id | pending | pending | -0.05 | equivalent |
| BR_S2_nohist | BR_S2 | G_excess | pending | pending | -0.00 | equivalent |

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

Made: T1: T1_primary_family, T1b_margin_sensitivity; T2: T2_ladder; T3: T3_estimands; T4: T4_cstar_selection; T5: T5_strata; T6: T6a_sensitivities, T6b_nohist_estimands, T6c_nohist_ladder; S1: S1_baselines; S2: S2_control_panel (pending: control panel file not found); S3: S3_outbreak; S4: S4_weighted; S5: S5_recalibration; S6: S6_q90_mechanism; S7: S7_embedding_distance; S8: S8_per_year

Figures (`docs/results/figures/`, PDF + PNG):

- `F1_forest_G_excess` — forest plot of G_excess per family cell (pooled h{1,4}, % of WIS(L3), 95%/90% CI, ±1% band); Taiwan S5 in its own panel
- `F2_strata_contributions` — three target types: additive contributions to G_excess per cell
- `F3_s5_embedding_distance` — held-out country (S5): AlphaEarth similarity to the training districts vs district gain
- `F4_per_year_gains` — G_excess per test year and cell
- `FS1_ladder_S1` — ladder per country, S1
- `FS2` — no-history arm ladder (**pending: no data yet**)

Per-cell intermediate results: `runs/analysis_cache/<cell>/` (est.parquet, ladder.parquet, extras/*.parquet, info.json with row counts, filter, exclusions and seeds).

## 6. Compute status (scheduler snapshot)

```
snapshot 2026-11-18 02:13:58 (7 s old); budget 44 threads (others 1587% CPU (incl. own non-pipeline jobs)) = 11 workers; held 12; free -1
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
  T3 brazil_s1_nohist             running                                  brazil_s1_nohist_N3                held  5 unclaimed   0
  T3 brazil_s2_nohist             running                                  brazil_s2_nohist_N3                held  3 unclaimed  47
  T4 brazil_s1_sens_yref          running                                  brazil_s1_sens_yref_L3             held  0 unclaimed  10
  T4 brazil_s1_sens_delay         running                                  brazil_s1_sens_delay2_L3           held  0 unclaimed  10
  T4 brazil_s1_sens_ctrl          running                                  brazil_s1_sens_ctrl_L3_C3          held  0 unclaimed  10
  T4 taiwan_s1_l2shared           running                                  taiwan_s1_shared_L2                held  0 unclaimed  16
  T5 brazil_s4                    running                                  brazil_s4_controls_2019            held  0 unclaimed 130
  other run_experiment configs (counted in the budget): {'configs/colombia_s1_panel_L4_C2.yaml': 2, 'configs/taiwan_s5_tw2021_L4_Cstar.yaml': 2}
```
