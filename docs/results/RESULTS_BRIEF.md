# RESULTS BRIEF (auto-generated)

Generated 2026-11-17 22:13 by `scripts/analysis/make_results.py`. Do not edit by hand: re-run the script. All numbers are log1p-scale WIS; a gain is positive when the second model has the lower WIS. Percentages are of WIS(L3) (WIS(N3) in the no-history arm). **Horizons:** every "pooled" estimate (T1, T3, T5, T6, per-year and strata rows, F1, F3) pools the primary horizons **h{1,4}** (manifest `primary_horizons`, deviation row 21), in every cell; S1 cells also show the secondary pooling over h1-4 (`horizon = pooled_h1-4`), which is never in the Holm family. Inference: DM test with EWC long-run variance and HLN correction on the weekly cross-unit mean loss difference; TOST against a ±1% margin (90% CI); MDE at 80% power. See `docs/methods/results_kit.md`.

Key: **G_emb** = WIS(L3) − WIS(L4) (raw AlphaEarth gain); **G_id** = WIS(L3) − WIS(L3+C*) (gain from a pure location/ID control); **G_excess** = WIS(L3+C*) − WIS(L4+C*) (primary: what AlphaEarth adds beyond the best ID control).

## 1. Status of every cell

| cell | group | description | C* | status | what is missing |
|---|---|---|---|---|---|
| BR_S1 | primary/history | Brazil S1, history arm (primary) | C1 | available |  |
| BR_S2 | primary/history | Brazil S2, history arm (primary) | C1 | available |  |
| BR_S3 | primary/history | Brazil S3, history arm (primary) | C1 | pending | L4C: brazil_s3_L4_Cstar: partial (1 chunks) |
| BR_S4 | primary/history | Brazil S4, history arm (primary) | selection pending (stale) | pending | L3: brazil_s4_L3: not started; L4: brazil_s4_L4: not started; L3C: brazil_s4_L3_Cstar: not started; L4C: brazil_s4_L4_Cstar: not started |
| BR_S5 | primary/history | Brazil S5, history arm (primary) | C3 | available |  |
| CO_S1 | primary/history | Colombia S1, history arm (primary) | C1 | available |  |
| CO_S2 | primary/history | Colombia S2, history arm (primary) | C1 | available |  |
| CO_S3 | primary/history | Colombia S3, history arm (primary) | C1 | available |  |
| CO_S4 | primary/history | Colombia S4, history arm (primary) | C1 | available |  |
| CO_S5 | primary/history | Colombia S5, history arm (primary) | C2 | available |  |
| PE_S1 | primary/history | Peru S1, history arm (primary) | C1 | available |  |
| PE_S5 | primary/history | Peru S5, history arm (primary) | C3 | available |  |
| TW_S1 | primary/history | Taiwan S1, history arm (primary) | C1 | available |  |
| TW_S5 | primary/history | Taiwan S5, history arm (primary) | C3 | available |  |
| BR_S1_3seeds | secondary/sensitivity | Brazil S1, primary + 2 extra seeds (seed-averaged; extra seeds h1/h4) | C1 | available |  |
| BR_S1_yref | secondary/sensitivity | Brazil S1 sensitivity: yearly features aligned to the origin year (strictly causal) (G_emb only) | n/a (no C* run) | pending | L3: brazil_s1_sens_yref_L3: not started; L4: brazil_s1_sens_yref_L4: not started; L3C: brazil_s1_sens_yref_L3: not started; L4C: brazil_s1_sens_yref_L4: not started |
| BR_S1_delay2 | secondary/sensitivity | Brazil S1 sensitivity: 2-week reporting delay (G_emb only) | n/a (no C* run) | pending | L3: brazil_s1_sens_delay2_L3: not started; L4: brazil_s1_sens_delay2_L4: not started; L3C: brazil_s1_sens_delay2_L3: not started; L4C: brazil_s1_sens_delay2_L4: not started |
| BR_S1_ctrlC3 | secondary/sensitivity | Brazil S1 controls panel: C3 in place of C* (h1, h4) | C3 | pending | L3C: brazil_s1_sens_ctrl_L3_C3: not started; L4C: brazil_s1_sens_ctrl_L4_C3: not started |
| BR_S1_ctrlC6 | secondary/sensitivity | Brazil S1 controls panel: C6 in place of C* (h1, h4) | C6 | pending | L3C: brazil_s1_sens_ctrl_L3_C6: not started; L4C: brazil_s1_sens_ctrl_L4_C6: not started |
| BR_S1_perlevel | secondary/sensitivity | Brazil S1, per-level tuning (L3/L4 31 leaves; superseded primary) | C1 | available |  |
| TW_S1_BRparams | secondary/sensitivity | Taiwan S1 with Brazil's tuned params and C* | C1 | available |  |
| BR_S1_nohist | secondary/no-history | Brazil S1, no-history arm (ref = N3) | selection pending (stale) | pending | L3: brazil_s1_nohist_N3: not started; L4: brazil_s1_nohist_N4: not started; L3C: brazil_s1_nohist_N3_Cstar: not started; L4C: brazil_s1_nohist_N4_Cstar: not started |
| BR_S2_nohist | secondary/no-history | Brazil S2, no-history arm (ref = N3) | selection pending (stale) | pending | L3: brazil_s2_nohist_N3: not started; L4: brazil_s2_nohist_N4: not started; L3C: brazil_s2_nohist_N3_Cstar: not started; L4C: brazil_s2_nohist_N4_Cstar: not started |

Primary family: **12 of 14 cells available**. Holm p-values are over the available cells only and are provisional until all 14 are in; `p_bonf14` in T1 is the conservative bound.

## 2. Headline numbers

### BR_S1: Brazil S1, history arm (primary) (C* = C1)
Rows scored 5,759,748; test years [2020, 2021, 2022, 2023, 2024]; horizons scored [1, 2, 3, 4], primary pooled over h{1,4}; seeds [0, 1, 2]; zero-filled share 0.53; outbreak share 0.080.

- **G_excess** (pooled h{1,4}, primary) +0.26% [-0.38, +0.90]: L4+C* improves on L3+C* by 0.26% of WIS(ref) (95% CI -0.38 to +0.90%; p = 0.399; MDE 0.90%): **equivalent**, i.e. the 90% CI lies inside ±1% of WIS(ref): any effect is too small to matter.
- **G_emb** (pooled h{1,4}, primary) +0.29% [-0.35, +0.93]: L4 improves on L3 by 0.29% of WIS(ref) (95% CI -0.35 to +0.93%; p = 0.354; MDE 0.90%): **equivalent**, i.e. the 90% CI lies inside ±1% of WIS(ref): any effect is too small to matter.
- **G_id** (pooled h{1,4}, primary) +0.01% [-0.15, +0.17]: L3+C* improves on L3 by 0.01% of WIS(ref) (95% CI -0.15 to +0.17%; p = 0.878; MDE 0.22%): **equivalent**, i.e. the 90% CI lies inside ±1% of WIS(ref): any effect is too small to matter.
- *Secondary* G_excess pooled over h1-4 (not in the Holm family): +0.27% [-0.37, +0.91]; p = 0.384; equivalent.
- **ID share**: not estimable: G_emb 95% CI includes 0
- Ladder (pooled h{1,4}): L0 0.4645, L1 0.1703, L2 0.1692, L3 0.1684, L4 0.1679, L3+C* 0.1684, L4+C* 0.1679. Best = L4. 80% coverage 0.77–0.91 overall, 0.40–0.68 on non-zero targets.
- G_excess by stratum (pooled h{1,4}): observed +0.57% [-0.08, +1.23]; zero_filled -1.74% [-2.77, -0.71]; outbreak +0.15% [-0.77, +1.07]

### BR_S2: Brazil S2, history arm (primary) (C* = C1)
Rows scored 2,879,874; test years [2020, 2021, 2022, 2023, 2024]; horizons scored [1, 4], primary pooled over h{1,4}; seeds [0]; zero-filled share 0.53; outbreak share 0.080.

- **G_excess** (pooled h{1,4}, primary) +0.02% [-0.37, +0.41]: L4+C* improves on L3+C* by 0.02% of WIS(ref) (95% CI -0.37 to +0.41%; p = 0.928; MDE 0.55%): **equivalent**, i.e. the 90% CI lies inside ±1% of WIS(ref): any effect is too small to matter.
- **G_emb** (pooled h{1,4}, primary) -0.01% [-0.39, +0.37]: L4 is worse than L3 by 0.01% of WIS(ref) (95% CI -0.39 to +0.37%; p = 0.957; MDE 0.53%): **equivalent**, i.e. the 90% CI lies inside ±1% of WIS(ref): any effect is too small to matter.
- **G_id** (pooled h{1,4}, primary) -0.05% [-0.12, +0.01]: L3+C* is worse than L3 by 0.05% of WIS(ref) (95% CI -0.12 to +0.01%; p = 0.116; MDE 0.10%): **equivalent**, i.e. the 90% CI lies inside ±1% of WIS(ref): any effect is too small to matter.
- **ID share**: not estimable: G_emb 95% CI includes 0
- Ladder (pooled h{1,4}): L3 0.1692, L4 0.1693, L3+C* 0.1693, L4+C* 0.1693. Best = L3. 80% coverage 0.90–0.90 overall, 0.65–0.65 on non-zero targets.
- G_excess by stratum (pooled h{1,4}): observed +0.35% [-0.14, +0.84]; zero_filled -1.59% [-2.70, -0.49]; outbreak -0.95% [-1.97, +0.07]

### BR_S5: Brazil S5, history arm (primary) (C* = C3)
Rows scored 2,879,874; test years [2020, 2021, 2022, 2023, 2024]; horizons scored [1, 4], primary pooled over h{1,4}; seeds [0]; zero-filled share 0.53; outbreak share 0.080.

- **G_excess** (pooled h{1,4}, primary) -0.63% [-0.88, -0.39]: L4+C* is worse than L3+C* by 0.63% of WIS(ref) (95% CI -0.88 to -0.39%; p = 0.000; MDE 0.34%): **equivalent**, i.e. the 90% CI lies inside ±1% of WIS(ref): any effect is too small to matter.
- **G_emb** (pooled h{1,4}, primary) -0.36% [-1.29, +0.57]: L4 is worse than L3 by 0.36% of WIS(ref) (95% CI -1.29 to +0.57%; p = 0.423; MDE 1.30%): **inconclusive**, i.e. the CI crosses 0 and reaches past the ±1% margin: the data cannot tell.
- **G_id** (pooled h{1,4}, primary) +0.09% [-0.79, +0.98]: L3+C* improves on L3 by 0.09% of WIS(ref) (95% CI -0.79 to +0.98%; p = 0.827; MDE 1.25%): **equivalent**, i.e. the 90% CI lies inside ±1% of WIS(ref): any effect is too small to matter.
- **ID share**: not estimable: G_emb 95% CI includes 0
- Ladder (pooled h{1,4}): L3 0.1908, L4 0.1915, L3+C* 0.1906, L4+C* 0.1918. Best = L3+C*. 80% coverage 0.87–0.88 overall, 0.59–0.63 on non-zero targets.
- G_excess by stratum (pooled h{1,4}): observed +0.32% [-0.06, +0.70]; zero_filled -5.48% [-6.43, -4.53]; outbreak +0.80% [+0.15, +1.45]

### CO_S1: Colombia S1, history arm (primary) (C* = C1)
Rows scored 671,960; test years [2020, 2021, 2022]; horizons scored [1, 2, 3, 4], primary pooled over h{1,4}; seeds [0]; zero-filled share 0.78; outbreak share 0.023.

- **G_excess** (pooled h{1,4}, primary) -0.39% [-0.58, -0.20]: L4+C* is worse than L3+C* by 0.39% of WIS(ref) (95% CI -0.58 to -0.20%; p = 0.001; MDE 0.26%): **equivalent**, i.e. the 90% CI lies inside ±1% of WIS(ref): any effect is too small to matter.
- **G_emb** (pooled h{1,4}, primary) -0.35% [-0.57, -0.13]: L4 is worse than L3 by 0.35% of WIS(ref) (95% CI -0.57 to -0.13%; p = 0.005; MDE 0.31%): **equivalent**, i.e. the 90% CI lies inside ±1% of WIS(ref): any effect is too small to matter.
- **G_id** (pooled h{1,4}, primary) -0.06% [-0.34, +0.23]: L3+C* is worse than L3 by 0.06% of WIS(ref) (95% CI -0.34 to +0.23%; p = 0.673; MDE 0.40%): **equivalent**, i.e. the 90% CI lies inside ±1% of WIS(ref): any effect is too small to matter.
- *Secondary* G_excess pooled over h1-4 (not in the Holm family): -0.38% [-0.60, -0.17]; p = 0.002; equivalent.
- **ID share**: not estimable: G_emb < 1% of WIS(L3)
- Ladder (pooled h{1,4}): L0 0.3286, L1 0.1237, L2 0.1235, L3 0.1231, L4 0.1235, L3+C* 0.1232, L4+C* 0.1237. Best = L3. 80% coverage 0.81–0.93 overall, 0.53–0.72 on non-zero targets.
- G_excess by stratum (pooled h{1,4}): observed +0.28% [-0.29, +0.85]; zero_filled -2.12% [-3.51, -0.72]; outbreak -0.64% [-2.21, +0.93]

### CO_S2: Colombia S2, history arm (primary) (C* = C1)
Rows scored 335,980; test years [2020, 2021, 2022]; horizons scored [1, 4], primary pooled over h{1,4}; seeds [0]; zero-filled share 0.78; outbreak share 0.023.

- **G_excess** (pooled h{1,4}, primary) -0.48% [-0.69, -0.27]: L4+C* is worse than L3+C* by 0.48% of WIS(ref) (95% CI -0.69 to -0.27%; p = 0.000; MDE 0.29%): **equivalent**, i.e. the 90% CI lies inside ±1% of WIS(ref): any effect is too small to matter.
- **G_emb** (pooled h{1,4}, primary) -0.59% [-0.79, -0.38]: L4 is worse than L3 by 0.59% of WIS(ref) (95% CI -0.79 to -0.38%; p = 0.000; MDE 0.29%): **equivalent**, i.e. the 90% CI lies inside ±1% of WIS(ref): any effect is too small to matter.
- **G_id** (pooled h{1,4}, primary) -0.07% [-0.12, -0.03]: L3+C* is worse than L3 by 0.07% of WIS(ref) (95% CI -0.12 to -0.03%; p = 0.003; MDE 0.06%): **equivalent**, i.e. the 90% CI lies inside ±1% of WIS(ref): any effect is too small to matter.
- **ID share**: not estimable: G_emb < 1% of WIS(L3)
- Ladder (pooled h{1,4}): L3 0.1235, L4 0.1243, L3+C* 0.1236, L4+C* 0.1242. Best = L3. 80% coverage 0.92–0.92 overall, 0.70–0.71 on non-zero targets.
- G_excess by stratum (pooled h{1,4}): observed +0.26% [-0.32, +0.84]; zero_filled -2.46% [-3.77, -1.16]; outbreak -1.00% [-2.77, +0.78]

### CO_S3: Colombia S3, history arm (primary) (C* = C1)
Rows scored 335,980; test years [2020, 2021, 2022]; horizons scored [1, 4], primary pooled over h{1,4}; seeds [0]; zero-filled share 0.78; outbreak share 0.023.

- **G_excess** (pooled h{1,4}, primary) -0.68% [-1.07, -0.29]: L4+C* is worse than L3+C* by 0.68% of WIS(ref) (95% CI -1.07 to -0.29%; p = 0.003; MDE 0.55%): **inferior**, i.e. the 95% CI excludes 0 on the harm side: the second model is worse.
- **G_emb** (pooled h{1,4}, primary) -0.86% [-1.18, -0.53]: L4 is worse than L3 by 0.86% of WIS(ref) (95% CI -1.18 to -0.53%; p = 0.000; MDE 0.45%): **inferior**, i.e. the 95% CI excludes 0 on the harm side: the second model is worse.
- **G_id** (pooled h{1,4}, primary) -0.12% [-0.21, -0.04]: L3+C* is worse than L3 by 0.12% of WIS(ref) (95% CI -0.21 to -0.04%; p = 0.009; MDE 0.12%): **equivalent**, i.e. the 90% CI lies inside ±1% of WIS(ref): any effect is too small to matter.
- **ID share**: not estimable: G_emb < 1% of WIS(L3)
- Ladder (pooled h{1,4}): L3 0.1255, L4 0.1265, L3+C* 0.1256, L4+C* 0.1265. Best = L3. 80% coverage 0.92–0.92 overall, 0.70–0.71 on non-zero targets.
- G_excess by stratum (pooled h{1,4}): observed +0.13% [-0.32, +0.59]; zero_filled -2.59% [-4.14, -1.03]; outbreak -1.80% [-3.37, -0.22]

### CO_S4: Colombia S4, history arm (primary) (C* = C1)
Rows scored 335,980; test years [2020, 2021, 2022]; horizons scored [1, 4], primary pooled over h{1,4}; seeds [0]; zero-filled share 0.78; outbreak share 0.023.

- **G_excess** (pooled h{1,4}, primary) -0.44% [-0.68, -0.20]: L4+C* is worse than L3+C* by 0.44% of WIS(ref) (95% CI -0.68 to -0.20%; p = 0.002; MDE 0.33%): **equivalent**, i.e. the 90% CI lies inside ±1% of WIS(ref): any effect is too small to matter.
- **G_emb** (pooled h{1,4}, primary) -0.51% [-0.74, -0.28]: L4 is worse than L3 by 0.51% of WIS(ref) (95% CI -0.74 to -0.28%; p = 0.000; MDE 0.32%): **equivalent**, i.e. the 90% CI lies inside ±1% of WIS(ref): any effect is too small to matter.
- **G_id** (pooled h{1,4}, primary) -0.12% [-0.17, -0.07]: L3+C* is worse than L3 by 0.12% of WIS(ref) (95% CI -0.17 to -0.07%; p = 0.000; MDE 0.07%): **equivalent**, i.e. the 90% CI lies inside ±1% of WIS(ref): any effect is too small to matter.
- **ID share**: not estimable: G_emb < 1% of WIS(L3)
- Ladder (pooled h{1,4}): L3 0.1233, L4 0.1240, L3+C* 0.1235, L4+C* 0.1240. Best = L3. 80% coverage 0.92–0.92 overall, 0.70–0.71 on non-zero targets.
- G_excess by stratum (pooled h{1,4}): observed +0.31% [-0.31, +0.94]; zero_filled -2.53% [-4.03, -1.02]; outbreak -0.92% [-2.77, +0.94]

### CO_S5: Colombia S5, history arm (primary) (C* = C2)
Rows scored 335,980; test years [2020, 2021, 2022]; horizons scored [1, 4], primary pooled over h{1,4}; seeds [0]; zero-filled share 0.78; outbreak share 0.023.

- **G_excess** (pooled h{1,4}, primary) +0.18% [-0.21, +0.58]: L4+C* improves on L3+C* by 0.18% of WIS(ref) (95% CI -0.21 to +0.58%; p = 0.326; MDE 0.55%): **equivalent**, i.e. the 90% CI lies inside ±1% of WIS(ref): any effect is too small to matter.
- **G_emb** (pooled h{1,4}, primary) -0.06% [-0.38, +0.26]: L4 is worse than L3 by 0.06% of WIS(ref) (95% CI -0.38 to +0.26%; p = 0.683; MDE 0.45%): **equivalent**, i.e. the 90% CI lies inside ±1% of WIS(ref): any effect is too small to matter.
- **G_id** (pooled h{1,4}, primary) -0.84% [-1.28, -0.39]: L3+C* is worse than L3 by 0.84% of WIS(ref) (95% CI -1.28 to -0.39%; p = 0.002; MDE 0.62%): **inferior**, i.e. the 95% CI excludes 0 on the harm side: the second model is worse.
- **ID share**: not estimable: G_emb 95% CI includes 0
- Ladder (pooled h{1,4}): L3 0.1251, L4 0.1252, L3+C* 0.1261, L4+C* 0.1259. Best = L3. 80% coverage 0.93–0.94 overall, 0.68–0.75 on non-zero targets.
- G_excess by stratum (pooled h{1,4}): observed +0.34% [+0.03, +0.64]; zero_filled -0.08% [-2.25, +2.09]; outbreak -0.41% [-1.59, +0.76]

### PE_S1: Peru S1, history arm (primary) (C* = C1)
Rows scored 96,108; test years [2020, 2021, 2022, 2023]; horizons scored [1, 2, 3, 4], primary pooled over h{1,4}; seeds [0]; zero-filled share 0.56; outbreak share 0.228.

- **G_excess** (pooled h{1,4}, primary) -0.62% [-1.35, +0.12]: L4+C* is worse than L3+C* by 0.62% of WIS(ref) (95% CI -1.35 to +0.12%; p = 0.094; MDE 1.03%): **inconclusive**, i.e. the CI crosses 0 and reaches past the ±1% margin: the data cannot tell.
- **G_emb** (pooled h{1,4}, primary) -0.89% [-1.64, -0.13]: L4 is worse than L3 by 0.89% of WIS(ref) (95% CI -1.64 to -0.13%; p = 0.025; MDE 1.06%): **inferior**, i.e. the 95% CI excludes 0 on the harm side: the second model is worse.
- **G_id** (pooled h{1,4}, primary) -0.28% [-1.02, +0.46]: L3+C* is worse than L3 by 0.28% of WIS(ref) (95% CI -1.02 to +0.46%; p = 0.427; MDE 1.04%): **equivalent**, i.e. the 90% CI lies inside ±1% of WIS(ref): any effect is too small to matter.
- *Secondary* G_excess pooled over h1-4 (not in the Holm family): -0.57% [-1.29, +0.15]; p = 0.112; inconclusive.
- **ID share**: not estimable: G_emb < 1% of WIS(L3)
- Ladder (pooled h{1,4}): L0 0.6541, L1 0.2454, L2 0.2442, L3 0.2448, L4 0.2469, L3+C* 0.2454, L4+C* 0.2470. Best = L2. 80% coverage 0.73–0.84 overall, 0.47–0.69 on non-zero targets.
- G_excess by stratum (pooled h{1,4}): observed +0.03% [-0.83, +0.89]; zero_filled -6.40% [-8.90, -3.90]; outbreak -1.05% [-2.65, +0.54]

### PE_S5: Peru S5, history arm (primary) (C* = C3)
Rows scored 48,054; test years [2020, 2021, 2022, 2023]; horizons scored [1, 4], primary pooled over h{1,4}; seeds [0]; zero-filled share 0.56; outbreak share 0.228.

- **G_excess** (pooled h{1,4}, primary) +1.01% [+0.02, +2.00]: L4+C* improves on L3+C* by 1.01% of WIS(ref) (95% CI +0.02 to +2.00%; p = 0.046; MDE 1.39%): **superior**, i.e. the 95% CI excludes 0 on the improvement side: the second model is better.
- **G_emb** (pooled h{1,4}, primary) +0.73% [-0.42, +1.89]: L4 improves on L3 by 0.73% of WIS(ref) (95% CI -0.42 to +1.89%; p = 0.195; MDE 1.62%): **inconclusive**, i.e. the CI crosses 0 and reaches past the ±1% margin: the data cannot tell.
- **G_id** (pooled h{1,4}, primary) -0.45% [-0.79, -0.11]: L3+C* is worse than L3 by 0.45% of WIS(ref) (95% CI -0.79 to -0.11%; p = 0.014; MDE 0.48%): **equivalent**, i.e. the 90% CI lies inside ±1% of WIS(ref): any effect is too small to matter.
- **ID share**: not estimable: G_emb 95% CI includes 0
- Ladder (pooled h{1,4}): L3 0.2400, L4 0.2382, L3+C* 0.2411, L4+C* 0.2386. Best = L4. 80% coverage 0.83–0.84 overall, 0.65–0.68 on non-zero targets.
- G_excess by stratum (pooled h{1,4}): observed +1.66% [+0.45, +2.87]; zero_filled -3.16% [-4.86, -1.47]; outbreak +3.76% [+1.76, +5.75]

### TW_S1: Taiwan S1, history arm (primary) (C* = C1)
Rows scored 238,260; test years [2020, 2022, 2023, 2024]; horizons scored [1, 2, 3, 4], primary pooled over h{1,4}; seeds [0]; zero-filled share 0.97; outbreak share 0.008.

- **G_excess** (pooled h{1,4}, primary) -0.39% [-1.00, +0.22]: L4+C* is worse than L3+C* by 0.39% of WIS(ref) (95% CI -1.00 to +0.22%; p = 0.192; MDE 0.86%): **equivalent**, i.e. the 90% CI lies inside ±1% of WIS(ref): any effect is too small to matter.
- **G_emb** (pooled h{1,4}, primary) -0.93% [-1.84, -0.02]: L4 is worse than L3 by 0.93% of WIS(ref) (95% CI -1.84 to -0.02%; p = 0.045; MDE 1.28%): **inferior**, i.e. the 95% CI excludes 0 on the harm side: the second model is worse.
- **G_id** (pooled h{1,4}, primary) -0.65% [-1.70, +0.40]: L3+C* is worse than L3 by 0.65% of WIS(ref) (95% CI -1.70 to +0.40%; p = 0.203; MDE 1.47%): **inconclusive**, i.e. the CI crosses 0 and reaches past the ±1% margin: the data cannot tell.
- *Secondary* G_excess pooled over h1-4 (not in the Holm family): -0.35% [-0.93, +0.23]; p = 0.215; equivalent.
- **ID share**: not estimable: G_emb < 1% of WIS(L3)
- Ladder (pooled h{1,4}): L0 0.0885, L1 0.0380, L2 0.0465, L3 0.0383, L4 0.0387, L3+C* 0.0386, L4+C* 0.0387. Best = L1. 80% coverage 0.95–0.98 overall, 0.00–0.26 on non-zero targets.
- G_excess by stratum (pooled h{1,4}): observed -0.14% [-1.19, +0.91]; zero_filled -5.46% [-18.26, +7.35]; outbreak -0.13% [-0.87, +0.62]

### TW_S5: Taiwan S5, history arm (primary) (C* = C3)
Rows scored 119,130; test years [2020, 2022, 2023, 2024]; horizons scored [1, 4], primary pooled over h{1,4}; seeds [0]; zero-filled share 0.97; outbreak share 0.008.

- **G_excess** (pooled h{1,4}, primary) -11.53% [-15.83, -7.23]: L4+C* is worse than L3+C* by 11.53% of WIS(ref) (95% CI -15.83 to -7.23%; p = 0.000; MDE 6.04%): **inferior**, i.e. the 95% CI excludes 0 on the harm side: the second model is worse.
- **G_emb** (pooled h{1,4}, primary) -15.29% [-20.87, -9.72]: L4 is worse than L3 by 15.29% of WIS(ref) (95% CI -20.87 to -9.72%; p = 0.000; MDE 7.83%): **inferior**, i.e. the 95% CI excludes 0 on the harm side: the second model is worse.
- **G_id** (pooled h{1,4}, primary) -2.53% [-5.71, +0.66]: L3+C* is worse than L3 by 2.53% of WIS(ref) (95% CI -5.71 to +0.66%; p = 0.111; MDE 4.47%): **inconclusive**, i.e. the CI crosses 0 and reaches past the ±1% margin: the data cannot tell.
- **ID share**: not estimable: G_emb < 1% of WIS(L3)
- Ladder (pooled h{1,4}): L3 0.0245, L4 0.0283, L3+C* 0.0252, L4+C* 0.0280. Best = L3. 80% coverage 0.99–0.99 overall, 0.56–0.63 on non-zero targets.
- G_excess by stratum (pooled h{1,4}): observed +1.90% [-0.35, +4.16]; zero_filled -34.56% [-46.23, -22.89]; outbreak +1.09% [-0.33, +2.51]

### BR_S1_3seeds: Brazil S1, primary + 2 extra seeds (seed-averaged; extra seeds h1/h4) (C* = C1)
Rows scored 5,759,748; test years [2020, 2021, 2022, 2023, 2024]; horizons scored [1, 2, 3, 4], primary pooled over h{1,4}; seeds [0, 1, 2]; zero-filled share 0.53; outbreak share 0.080.

- **G_excess** (pooled h{1,4}, primary) +0.26% [-0.38, +0.90]: L4+C* improves on L3+C* by 0.26% of WIS(ref) (95% CI -0.38 to +0.90%; p = 0.399; MDE 0.90%): **equivalent**, i.e. the 90% CI lies inside ±1% of WIS(ref): any effect is too small to matter.
- **G_emb** (pooled h{1,4}, primary) +0.29% [-0.35, +0.93]: L4 improves on L3 by 0.29% of WIS(ref) (95% CI -0.35 to +0.93%; p = 0.354; MDE 0.90%): **equivalent**, i.e. the 90% CI lies inside ±1% of WIS(ref): any effect is too small to matter.
- **G_id** (pooled h{1,4}, primary) +0.01% [-0.15, +0.17]: L3+C* improves on L3 by 0.01% of WIS(ref) (95% CI -0.15 to +0.17%; p = 0.878; MDE 0.22%): **equivalent**, i.e. the 90% CI lies inside ±1% of WIS(ref): any effect is too small to matter.
- *Secondary* G_excess pooled over h1-4 (not in the Holm family): +0.27% [-0.37, +0.91]; p = 0.384; equivalent.
- **ID share**: not estimable: G_emb 95% CI includes 0
- Ladder (pooled h{1,4}): L3 0.1684, L4 0.1679, L3+C* 0.1684, L4+C* 0.1679. Best = L4. 80% coverage 0.90–0.90 overall, 0.66–0.66 on non-zero targets.
- G_excess by stratum (pooled h{1,4}): observed +0.57% [-0.08, +1.23]; zero_filled -1.74% [-2.77, -0.71]; outbreak +0.15% [-0.77, +1.07]

### BR_S1_perlevel: Brazil S1, per-level tuning (L3/L4 31 leaves; superseded primary) (C* = C1)
Rows scored 5,759,748; test years [2020, 2021, 2022, 2023, 2024]; horizons scored [1, 2, 3, 4], primary pooled over h{1,4}; seeds [0]; zero-filled share 0.53; outbreak share 0.080.

- **G_excess** (pooled h{1,4}, primary) +0.26% [-0.10, +0.63]: L4+C* improves on L3+C* by 0.26% of WIS(ref) (95% CI -0.10 to +0.63%; p = 0.143; MDE 0.51%): **equivalent**, i.e. the 90% CI lies inside ±1% of WIS(ref): any effect is too small to matter.
- **G_emb** (pooled h{1,4}, primary) +0.24% [-0.08, +0.55]: L4 improves on L3 by 0.24% of WIS(ref) (95% CI -0.08 to +0.55%; p = 0.130; MDE 0.44%): **equivalent**, i.e. the 90% CI lies inside ±1% of WIS(ref): any effect is too small to matter.
- **G_id** (pooled h{1,4}, primary) -0.07% [-0.31, +0.18]: L3+C* is worse than L3 by 0.07% of WIS(ref) (95% CI -0.31 to +0.18%; p = 0.557; MDE 0.34%): **equivalent**, i.e. the 90% CI lies inside ±1% of WIS(ref): any effect is too small to matter.
- *Secondary* G_excess pooled over h1-4 (not in the Holm family): +0.26% [-0.09, +0.60]; p = 0.133; equivalent.
- **ID share**: not estimable: G_emb 95% CI includes 0
- Ladder (pooled h{1,4}): L0 0.4645, L1 0.1703, L2 0.1692, L3 0.1717, L4 0.1713, L3+C* 0.1718, L4+C* 0.1713. Best = L2. 80% coverage 0.77–0.91 overall, 0.40–0.68 on non-zero targets.
- G_excess by stratum (pooled h{1,4}): observed +0.36% [+0.00, +0.72]; zero_filled -0.09% [-0.70, +0.53]; outbreak +0.24% [-0.26, +0.73]

### TW_S1_BRparams: Taiwan S1 with Brazil's tuned params and C* (C* = C1)
Rows scored 238,260; test years [2020, 2022, 2023, 2024]; horizons scored [1, 2, 3, 4], primary pooled over h{1,4}; seeds [0]; zero-filled share 0.97; outbreak share 0.008.

- **G_excess** (pooled h{1,4}, primary) -0.27% [-0.91, +0.37]: L4+C* is worse than L3+C* by 0.27% of WIS(ref) (95% CI -0.91 to +0.37%; p = 0.380; MDE 0.90%): **equivalent**, i.e. the 90% CI lies inside ±1% of WIS(ref): any effect is too small to matter.
- **G_emb** (pooled h{1,4}, primary) -0.86% [-1.77, +0.04]: L4 is worse than L3 by 0.86% of WIS(ref) (95% CI -1.77 to +0.04%; p = 0.060; MDE 1.27%): **inconclusive**, i.e. the CI crosses 0 and reaches past the ±1% margin: the data cannot tell.
- **G_id** (pooled h{1,4}, primary) -0.76% [-1.73, +0.21]: L3+C* is worse than L3 by 0.76% of WIS(ref) (95% CI -1.73 to +0.21%; p = 0.117; MDE 1.36%): **inconclusive**, i.e. the CI crosses 0 and reaches past the ±1% margin: the data cannot tell.
- *Secondary* G_excess pooled over h1-4 (not in the Holm family): -0.29% [-0.89, +0.31]; p = 0.318; equivalent.
- **ID share**: not estimable: G_emb 95% CI includes 0
- Ladder (pooled h{1,4}): L3 0.0384, L4 0.0387, L3+C* 0.0387, L4+C* 0.0388. Best = L3. 80% coverage 0.98–0.98 overall, 0.25–0.26 on non-zero targets.
- G_excess by stratum (pooled h{1,4}): observed -0.00% [-1.18, +1.18]; zero_filled -2.50% [-15.54, +10.54]; outbreak -0.15% [-0.71, +0.41]

## 3. Secondary comparisons (T6a)

| variant | vs | estimand | variant % [95% CI] | class | primary % | primary class |
|---|---|---|---|---|---|---|
| BR_S1_3seeds | BR_S1 | G_emb | +0.29 [-0.35, +0.93] | equivalent | +0.29 | equivalent |
| BR_S1_3seeds | BR_S1 | G_id | +0.01 [-0.15, +0.17] | equivalent | +0.01 | equivalent |
| BR_S1_3seeds | BR_S1 | G_excess | +0.26 [-0.38, +0.90] | equivalent | +0.26 | equivalent |
| BR_S1_yref | BR_S1 | G_emb | pending | pending | +0.29 | equivalent |
| BR_S1_delay2 | BR_S1 | G_emb | pending | pending | +0.29 | equivalent |
| BR_S1_ctrlC3 | BR_S1 | G_emb | pending | pending | +0.29 | equivalent |
| BR_S1_ctrlC3 | BR_S1 | G_id | pending | pending | +0.01 | equivalent |
| BR_S1_ctrlC3 | BR_S1 | G_excess | pending | pending | +0.26 | equivalent |
| BR_S1_ctrlC6 | BR_S1 | G_emb | pending | pending | +0.29 | equivalent |
| BR_S1_ctrlC6 | BR_S1 | G_id | pending | pending | +0.01 | equivalent |
| BR_S1_ctrlC6 | BR_S1 | G_excess | pending | pending | +0.26 | equivalent |
| BR_S1_perlevel | BR_S1 | G_emb | +0.24 [-0.08, +0.55] | equivalent | +0.29 | equivalent |
| BR_S1_perlevel | BR_S1 | G_id | -0.07 [-0.31, +0.18] | equivalent | +0.01 | equivalent |
| BR_S1_perlevel | BR_S1 | G_excess | +0.26 [-0.10, +0.63] | equivalent | +0.26 | equivalent |
| TW_S1_BRparams | TW_S1 | G_emb | -0.86 [-1.77, +0.04] | inconclusive | -0.93 | inferior |
| TW_S1_BRparams | TW_S1 | G_id | -0.76 [-1.73, +0.21] | inconclusive | -0.65 | inconclusive |
| TW_S1_BRparams | TW_S1 | G_excess | -0.27 [-0.91, +0.37] | equivalent | -0.39 | equivalent |

Both columns pool the primary horizons h{1,4}. Variants scored on h1/h4 only (controls panel, extra seeds) are therefore on the same horizons as the primary.

## 4. Where everything is

Tables (`docs/results/tables/`, each as .csv and a LaTeX booktabs fragment .tex):

- `T1_primary_family` — 14 primary cells: G_excess pooled over h{1,4}, % of WIS(L3), 95%/90% CI, DM p, Holm p (available cells, primary values only), p_bonf14, TOST class, MDE; `sec_*` = S1 secondary pooling over h1-4.
- `T2_ladder` (+ `T2_ladder_long.csv`) — L0–L4, L3+C*, L4+C* per cell: WIS per horizon and pooled; 40/80% coverage, overall and on non-zero targets.
- `T3_estimands` — G_emb / G_id / G_excess / ID share per cell × horizon and per test year (CSV).
- `T4_cstar_selection` — every control candidate at the 2019 origin, mean ± SD over seeds, chosen C*.
- `T5_strata` — estimands for observed vs zero-filled targets and outbreak vs non-outbreak weeks, pooled and per year (CSV).
- `T6a_sensitivities` — extra seeds, yearly_ref: origin, report delay 2, controls panel C3/C6, per-level tuning, TW with BR params; `T6b_nohist_estimands`, `T6c_nohist_ladder` — no-history arm.

Figures (`docs/results/figures/`, PDF + PNG):

- `F1_forest_G_excess` — forest plot of G_excess pooled over h{1,4} (% of WIS(L3)), 95% and 90% CI, ±1% band; all cells
- `F2_ladder_S1` — S1 ladder per country
- `F3_per_year_gains` — per-test-year G_emb and G_excess pooled over h{1,4}, S1 cells
- `F4` — no-history arm ladder (**pending: no data yet**)

Per-cell intermediate results: `runs/analysis_cache/<cell>/` (est.parquet, ladder.parquet, info.json with row counts, exclusions and seeds).

## 5. Compute status (scheduler snapshot)

```
snapshot 2026-11-17 22:13:19 (16 s old); budget 48 threads (others 1284% CPU (incl. own non-pipeline jobs)) = 12 workers; held 15; free -3
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
  T2 brazil_s3                    running                                  brazil_s3_L4_Cstar                 held 15 unclaimed  34
  T3 brazil_s1_nohist             running                                  brazil_s1_nohist_controls_2019     held  0 unclaimed  12
  T3 brazil_s2_nohist             running                                  brazil_s2_nohist_controls_2019     held  0 unclaimed 110
  T4 brazil_s1_sens_yref          running                                  brazil_s1_sens_yref_L3             held  0 unclaimed  10
  T4 brazil_s1_sens_delay         running                                  brazil_s1_sens_delay2_L3           held  0 unclaimed  10
  T4 brazil_s1_sens_ctrl          running                                  brazil_s1_sens_ctrl_L3_C3          held  0 unclaimed  10
  T4 taiwan_s1_l2shared           running                                  taiwan_s1_shared_L2                held  0 unclaimed  16
  T5 brazil_s4                    running                                  brazil_s4_controls_2019            held  0 unclaimed 130
```
