# RESULTS BRIEF (auto-generated)

Generated 2026-11-16 20:10 by `scripts/analysis/make_results.py`. Do not edit by hand: re-run the script. All numbers are log1p-scale WIS; a gain is positive when the second model has the lower WIS. Percentages are of WIS(L3) (WIS(N3) in the no-history arm). Inference: DM test with EWC long-run variance and HLN correction on the weekly cross-unit mean loss difference; TOST against a ±1% margin (90% CI); MDE at 80% power. See `docs/methods/results_kit.md`.

Key: **G_emb** = WIS(L3) − WIS(L4) (raw AlphaEarth gain); **G_id** = WIS(L3) − WIS(L3+C*) (gain from a pure location/ID control); **G_excess** = WIS(L3+C*) − WIS(L4+C*) (primary: what AlphaEarth adds beyond the best ID control).

## 1. Status of every cell

| cell | group | description | C* | status | what is missing |
|---|---|---|---|---|---|
| BR_S1 | primary/history | Brazil S1, history arm (primary) | C1 | pending | L4C: brazil_s1_shared_L4_Cstar: partial (14 chunks) |
| BR_S2 | primary/history | Brazil S2, history arm (primary) |  | pending | L3: brazil_s2_L3: not started; L4: brazil_s2_L4: not started; L3C: brazil_s2_L3_Cstar: not started; L4C: brazil_s2_L4_Cstar: not started |
| BR_S3 | primary/history | Brazil S3, history arm (primary) |  | pending | L3: brazil_s3_L3: not started; L4: brazil_s3_L4: not started; L3C: brazil_s3_L3_Cstar: not started; L4C: brazil_s3_L4_Cstar: not started |
| BR_S4 | primary/history | Brazil S4, history arm (primary) |  | pending | L3: brazil_s4_L3: not started; L4: brazil_s4_L4: not started; L3C: brazil_s4_L3_Cstar: not started; L4C: brazil_s4_L4_Cstar: not started |
| BR_S5 | primary/history | Brazil S5, history arm (primary) | C4 | pending | L4: brazil_s5_L4: partial (5 chunks); L3C: brazil_s5_L3_Cstar: not started; L4C: brazil_s5_L4_Cstar: not started |
| CO_S1 | primary/history | Colombia S1, history arm (primary) |  | pending | L3: colombia_s1_shared_L3: not started; L4: colombia_s1_shared_L4: not started; L3C: colombia_s1_shared_L3_Cstar: not started; L4C: colombia_s1_shared_L4_Cstar: not started |
| CO_S2 | primary/history | Colombia S2, history arm (primary) |  | pending | L3: colombia_s2_L3: not started; L4: colombia_s2_L4: not started; L3C: colombia_s2_L3_Cstar: not started; L4C: colombia_s2_L4_Cstar: not started |
| CO_S3 | primary/history | Colombia S3, history arm (primary) |  | pending | L3: colombia_s3_L3: not started; L4: colombia_s3_L4: not started; L3C: colombia_s3_L3_Cstar: not started; L4C: colombia_s3_L4_Cstar: not started |
| CO_S4 | primary/history | Colombia S4, history arm (primary) |  | pending | L3: colombia_s4_L3: not started; L4: colombia_s4_L4: not started; L3C: colombia_s4_L3_Cstar: not started; L4C: colombia_s4_L4_Cstar: not started |
| CO_S5 | primary/history | Colombia S5, history arm (primary) | C2 | pending | L3: colombia_s5_L3: not started; L4: colombia_s5_L4: not started; L3C: colombia_s5_L3_Cstar: not started; L4C: colombia_s5_L4_Cstar: not started |
| PE_S1 | primary/history | Peru S1, history arm (primary) | C1 | available |  |
| PE_S5 | primary/history | Peru S5, history arm (primary) |  | pending | L3: peru_s5_L3: not started; L4: peru_s5_L4: not started; L3C: peru_s5_L3_Cstar: not started; L4C: peru_s5_L4_Cstar: not started |
| TW_S1 | primary/history | Taiwan S1, history arm (primary) | C3 | available |  |
| TW_S5 | primary/history | Taiwan S5, history arm (primary) |  | pending | L3: taiwan_s5_L3: not started; L4: taiwan_s5_L4: not started; L3C: taiwan_s5_L3_Cstar: not started; L4C: taiwan_s5_L4_Cstar: not started |
| BR_S1_3seeds | secondary/sensitivity | Brazil S1, primary + 2 extra seeds (seed-averaged; extra seeds h1/h4) | C1 | pending | L3: brazil_s1_sens_seed2_L3: not started; L4: brazil_s1_sens_seed2_L4: not started; L3C: brazil_s1_sens_seed1_L3_Cstar: partial (2 chunks); brazil_s1_sens_seed2_L3_Cstar: not started; L4C: brazil_s1_shared_L4_Cstar: partial (14 chunks); brazil_s1_sens_seed1_L4_Cstar: not started; brazil_s1_sens_seed2_L4_Cstar: not started |
| BR_S1_yref | secondary/sensitivity | Brazil S1 sensitivity: yearly features aligned to the origin year (strictly causal) (G_emb only) |  | pending | L3: brazil_s1_sens_yref_L3: not started; L4: brazil_s1_sens_yref_L4: not started; L3C: brazil_s1_sens_yref_L3: not started; L4C: brazil_s1_sens_yref_L4: not started |
| BR_S1_delay2 | secondary/sensitivity | Brazil S1 sensitivity: 2-week reporting delay (G_emb only) |  | pending | L3: brazil_s1_sens_delay2_L3: not started; L4: brazil_s1_sens_delay2_L4: not started; L3C: brazil_s1_sens_delay2_L3: not started; L4C: brazil_s1_sens_delay2_L4: not started |
| BR_S1_ctrlC3 | secondary/sensitivity | Brazil S1 controls panel: C3 in place of C* (h1, h4) | C3 | pending | L3C: brazil_s1_sens_ctrl_L3_C3: not started; L4C: brazil_s1_sens_ctrl_L4_C3: not started |
| BR_S1_ctrlC6 | secondary/sensitivity | Brazil S1 controls panel: C6 in place of C* (h1, h4) | C6 | pending | L3C: brazil_s1_sens_ctrl_L3_C6: not started; L4C: brazil_s1_sens_ctrl_L4_C6: not started |
| BR_S1_perlevel | secondary/sensitivity | Brazil S1, per-level tuning (L3/L4 31 leaves; superseded primary) | C1 | available |  |
| TW_S1_BRparams | secondary/sensitivity | Taiwan S1 with Brazil's tuned params and C* | C1 | available |  |
| BR_S1_nohist | secondary/no-history | Brazil S1, no-history arm (ref = N3) |  | pending | L3: brazil_s1_nohist_N3: not started; L4: brazil_s1_nohist_N4: not started; L3C: brazil_s1_nohist_N3_Cstar: not started; L4C: brazil_s1_nohist_N4_Cstar: not started |
| BR_S2_nohist | secondary/no-history | Brazil S2, no-history arm (ref = N3) |  | pending | L3: brazil_s2_nohist_N3: not started; L4: brazil_s2_nohist_N4: not started; L3C: brazil_s2_nohist_N3_Cstar: not started; L4C: brazil_s2_nohist_N4_Cstar: not started |

Primary family: **2 of 14 cells available**. Holm p-values are over the available cells only and are provisional until all 14 are in; `p_bonf14` in T1 is the conservative bound.

## 2. Headline numbers

### PE_S1: Peru S1, history arm (primary) (C* = C1)
Rows scored 96,108; test years [2020, 2021, 2022, 2023]; horizons [1, 2, 3, 4]; seeds [0]; zero-filled share 0.56; outbreak share 0.228.

- **G_excess** -0.57% [-1.29, +0.15]: L4+C* is worse than L3+C* by 0.57% of WIS(ref) (95% CI -1.29 to +0.15%; p = 0.112; MDE 1.01%): **inconclusive**, i.e. the CI crosses 0 and reaches past the ±1% margin: the data cannot tell.
- **G_emb** -0.76% [-1.50, -0.02]: L4 is worse than L3 by 0.76% of WIS(ref) (95% CI -1.50 to -0.02%; p = 0.046; MDE 1.04%): **inferior**, i.e. the 95% CI excludes 0 on the harm side: the second model is worse.
- **G_id** -0.28% [-1.02, +0.45]: L3+C* is worse than L3 by 0.28% of WIS(ref) (95% CI -1.02 to +0.45%; p = 0.422; MDE 1.03%): **equivalent**, i.e. the 90% CI lies inside ±1% of WIS(ref): any effect is too small to matter.
- **ID share**: not estimable: G_emb < 1% of WIS(L3)
- Ladder (pooled h): L0 0.6541, L1 0.2469, L2 0.2457, L3 0.2460, L4 0.2479, L3+C* 0.2467, L4+C* 0.2481. Best = L2. 80% coverage 0.73–0.84 overall, 0.47–0.69 on non-zero targets.
- G_excess by stratum: observed +0.01% [-0.85, +0.88]; zero_filled -5.69% [-8.09, -3.29]; outbreak -1.00% [-2.56, +0.55]

### TW_S1: Taiwan S1, history arm (primary) (C* = C3)
Rows scored 238,260; test years [2020, 2022, 2023, 2024]; horizons [1, 2, 3, 4]; seeds [0]; zero-filled share 0.97; outbreak share 0.008.

- **G_excess** -0.36% [-1.01, +0.30]: L4+C* is worse than L3+C* by 0.36% of WIS(ref) (95% CI -1.01 to +0.30%; p = 0.264; MDE 0.92%): **equivalent**, i.e. the 90% CI lies inside ±1% of WIS(ref): any effect is too small to matter.
- **G_emb** -0.70% [-1.55, +0.15]: L4 is worse than L3 by 0.70% of WIS(ref) (95% CI -1.55 to +0.15%; p = 0.100; MDE 1.20%): **inconclusive**, i.e. the CI crosses 0 and reaches past the ±1% margin: the data cannot tell.
- **G_id** -0.54% [-1.23, +0.15]: L3+C* is worse than L3 by 0.54% of WIS(ref) (95% CI -1.23 to +0.15%; p = 0.118; MDE 0.97%): **inconclusive**, i.e. the CI crosses 0 and reaches past the ±1% margin: the data cannot tell.
- **ID share**: not estimable: G_emb 95% CI includes 0
- Ladder (pooled h): L0 0.0885, L1 0.0382, L2 0.0465, L3 0.0386, L4 0.0388, L3+C* 0.0388, L4+C* 0.0389. Best = L1. 80% coverage 0.95–0.98 overall, 0.00–0.26 on non-zero targets.
- G_excess by stratum: observed +0.47% [-0.64, +1.58]; zero_filled -2.81% [-10.08, +4.45]; outbreak -0.28% [-0.69, +0.14]

### BR_S1_perlevel: Brazil S1, per-level tuning (L3/L4 31 leaves; superseded primary) (C* = C1)
Rows scored 5,759,748; test years [2020, 2021, 2022, 2023, 2024]; horizons [1, 2, 3, 4]; seeds [0]; zero-filled share 0.53; outbreak share 0.080.

- **G_excess** +0.26% [-0.09, +0.60]: L4+C* improves on L3+C* by 0.26% of WIS(ref) (95% CI -0.09 to +0.60%; p = 0.133; MDE 0.49%): **equivalent**, i.e. the 90% CI lies inside ±1% of WIS(ref): any effect is too small to matter.
- **G_emb** +0.24% [-0.10, +0.59]: L4 improves on L3 by 0.24% of WIS(ref) (95% CI -0.10 to +0.59%; p = 0.155; MDE 0.49%): **equivalent**, i.e. the 90% CI lies inside ±1% of WIS(ref): any effect is too small to matter.
- **G_id** -0.06% [-0.27, +0.15]: L3+C* is worse than L3 by 0.06% of WIS(ref) (95% CI -0.27 to +0.15%; p = 0.553; MDE 0.30%): **equivalent**, i.e. the 90% CI lies inside ±1% of WIS(ref): any effect is too small to matter.
- **ID share**: not estimable: G_emb 95% CI includes 0
- Ladder (pooled h): L0 0.4645, L1 0.1711, L2 0.1702, L3 0.1727, L4 0.1723, L3+C* 0.1728, L4+C* 0.1724. Best = L2. 80% coverage 0.77–0.91 overall, 0.40–0.68 on non-zero targets.
- G_excess by stratum: observed +0.33% [-0.01, +0.68]; zero_filled -0.11% [-0.66, +0.45]; outbreak +0.18% [-0.27, +0.62]

### TW_S1_BRparams: Taiwan S1 with Brazil's tuned params and C* (C* = C1)
Rows scored 238,260; test years [2020, 2022, 2023, 2024]; horizons [1, 2, 3, 4]; seeds [0]; zero-filled share 0.97; outbreak share 0.008.

- **G_excess** -0.29% [-0.89, +0.31]: L4+C* is worse than L3+C* by 0.29% of WIS(ref) (95% CI -0.89 to +0.31%; p = 0.318; MDE 0.84%): **equivalent**, i.e. the 90% CI lies inside ±1% of WIS(ref): any effect is too small to matter.
- **G_emb** -0.61% [-1.40, +0.18]: L4 is worse than L3 by 0.61% of WIS(ref) (95% CI -1.40 to +0.18%; p = 0.122; MDE 1.11%): **inconclusive**, i.e. the CI crosses 0 and reaches past the ±1% margin: the data cannot tell.
- **G_id** -0.55% [-1.38, +0.28]: L3+C* is worse than L3 by 0.55% of WIS(ref) (95% CI -1.38 to +0.28%; p = 0.175; MDE 1.17%): **inconclusive**, i.e. the CI crosses 0 and reaches past the ±1% margin: the data cannot tell.
- **ID share**: not estimable: G_emb 95% CI includes 0
- Ladder (pooled h): L3 0.0386, L4 0.0389, L3+C* 0.0389, L4+C* 0.0390. Best = L3. 80% coverage 0.98–0.98 overall, 0.24–0.25 on non-zero targets.
- G_excess by stratum: observed -0.03% [-1.08, +1.01]; zero_filled -1.31% [-12.96, +10.33]; outbreak -0.33% [-0.97, +0.32]

## 3. Secondary comparisons (T6a)

| variant | vs | estimand | variant % [95% CI] | class | primary % | primary class |
|---|---|---|---|---|---|---|
| BR_S1_3seeds | BR_S1 | G_emb | pending | pending | pending | pending |
| BR_S1_3seeds | BR_S1 | G_id | pending | pending | pending | pending |
| BR_S1_3seeds | BR_S1 | G_excess | pending | pending | pending | pending |
| BR_S1_yref | BR_S1 | G_emb | pending | pending | pending | pending |
| BR_S1_delay2 | BR_S1 | G_emb | pending | pending | pending | pending |
| BR_S1_ctrlC3 | BR_S1 | G_emb | pending | pending | pending | pending |
| BR_S1_ctrlC3 | BR_S1 | G_id | pending | pending | pending | pending |
| BR_S1_ctrlC3 | BR_S1 | G_excess | pending | pending | pending | pending |
| BR_S1_ctrlC6 | BR_S1 | G_emb | pending | pending | pending | pending |
| BR_S1_ctrlC6 | BR_S1 | G_id | pending | pending | pending | pending |
| BR_S1_ctrlC6 | BR_S1 | G_excess | pending | pending | pending | pending |
| BR_S1_perlevel | BR_S1 | G_emb | +0.24 [-0.10, +0.59] | equivalent | pending | pending |
| BR_S1_perlevel | BR_S1 | G_id | -0.06 [-0.27, +0.15] | equivalent | pending | pending |
| BR_S1_perlevel | BR_S1 | G_excess | +0.26 [-0.09, +0.60] | equivalent | pending | pending |
| TW_S1_BRparams | TW_S1 | G_emb | -0.61 [-1.40, +0.18] | inconclusive | -0.70 | inconclusive |
| TW_S1_BRparams | TW_S1 | G_id | -0.55 [-1.38, +0.28] | inconclusive | -0.54 | inconclusive |
| TW_S1_BRparams | TW_S1 | G_excess | -0.29 [-0.89, +0.31] | equivalent | -0.36 | equivalent |

Note: the controls panel and extra-seed variants are scored on h1/h4 rows only (spatial-split horizons), so they are not row-identical to the h1–h4 primary.

## 4. Where everything is

Tables (`docs/results/tables/`, each as .csv and a LaTeX booktabs fragment .tex):

- `T1_primary_family` — 14 primary cells: G_excess, % of WIS(L3), 95%/90% CI, DM p, Holm p (available cells), p_bonf14, TOST class, MDE.
- `T2_ladder` (+ `T2_ladder_long.csv`) — L0–L4, L3+C*, L4+C* per cell: WIS per horizon and pooled; 40/80% coverage, overall and on non-zero targets.
- `T3_estimands` — G_emb / G_id / G_excess / ID share per cell × horizon and per test year (CSV).
- `T4_cstar_selection` — every control candidate at the 2019 origin, mean ± SD over seeds, chosen C*.
- `T5_strata` — estimands for observed vs zero-filled targets and outbreak vs non-outbreak weeks, pooled and per year (CSV).
- `T6a_sensitivities` — extra seeds, yearly_ref: origin, report delay 2, controls panel C3/C6, per-level tuning, TW with BR params; `T6b_nohist_estimands`, `T6c_nohist_ladder` — no-history arm.

Figures (`docs/results/figures/`, PDF + PNG):

- `F1_forest_G_excess` — forest plot of G_excess (% of WIS(L3)), 95% and 90% CI, ±1% band; all cells
- `F2_ladder_S1` — S1 ladder per country
- `F3_per_year_gains` — per-test-year G_emb and G_excess, S1 cells
- `F4` — no-history arm ladder (**pending: no data yet**)

Per-cell intermediate results: `runs/analysis_cache/<cell>/` (est.parquet, ladder.parquet, info.json with row counts, exclusions and seeds).

## 5. Compute status (scheduler snapshot)

```
snapshot 2026-11-16 20:08:50 (112 s old); budget 60 threads (others 15% CPU) = 15 workers; held 15; free 0
  T1 brazil_s1_shared             running                                  brazil_s1_shared_L4_Cstar          held  6 unclaimed   0
  T1 peru_s1_shared               done                                     -                                  held  0 unclaimed   0
  T1 taiwan_s1_shared             done                                     -                                  held  0 unclaimed   0
  T1 colombia_s1                  running                                  colombia_s1_L3_Cstar               held  1 unclaimed  31
  T1 colombia_s1_shared           blocked: waits for pop_s1_colombia       -                                  held  0 unclaimed   0
  T1 taiwan_s1brp                 done                                     -                                  held  0 unclaimed   0
  T2 brazil_s1_sens_seeds         running                                  brazil_s1_sens_seed1_L3_Cstar      held  8 unclaimed   0
  T2 brazil_s5                    running                                  brazil_s5_L4                       held  0 unclaimed   5
  T2 colombia_s5                  running                                  colombia_s5_L3                     held  0 unclaimed   6
  T2 peru_s5                      running                                  peru_s5_controls_2019              held  0 unclaimed  24
  T2 taiwan_s5                    running                                  taiwan_s5_controls_2019            held  0 unclaimed  24
  T2 colombia_s2                  running                                  colombia_s2_controls_2019          held  0 unclaimed 130
  T2 colombia_s3                  running                                  colombia_s3_controls_2019          held  0 unclaimed 156
  T2 colombia_s4                  running                                  colombia_s4_controls_2019          held  0 unclaimed 124
  T2 brazil_s2                    running                                  brazil_s2_controls_2019            held  0 unclaimed 109
  T2 brazil_s3                    running                                  brazil_s3_controls_2019            held  0 unclaimed 109
  T3 brazil_s1_nohist             running                                  brazil_s1_nohist_controls_2019     held  0 unclaimed  12
  T3 brazil_s2_nohist             running                                  brazil_s2_nohist_controls_2019     held  0 unclaimed 110
  T4 brazil_s1_sens_yref          running                                  brazil_s1_sens_yref_L3             held  0 unclaimed  10
  T4 brazil_s1_sens_delay         running                                  brazil_s1_sens_delay2_L3           held  0 unclaimed  10
  T4 brazil_s1_sens_ctrl          running                                  brazil_s1_sens_ctrl_L3_C3          held  0 unclaimed  10
  T5 brazil_s4                    running                                  brazil_s4_controls_2019            held  0 unclaimed 130
```
