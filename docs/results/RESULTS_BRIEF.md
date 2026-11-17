# RESULTS BRIEF (auto-generated)

Generated 2026-11-16 21:05 by `scripts/analysis/make_results.py`. Do not edit by hand: re-run the script. All numbers are log1p-scale WIS; a gain is positive when the second model has the lower WIS. Percentages are of WIS(L3) (WIS(N3) in the no-history arm). **Horizons:** every "pooled" estimate (T1, T3, T5, T6, per-year and strata rows, F1, F3) pools the primary horizons **h{1,4}** (manifest `primary_horizons`, deviation row 21), in every cell; S1 cells also show the secondary pooling over h1-4 (`horizon = pooled_h1-4`), which is never in the Holm family. Inference: DM test with EWC long-run variance and HLN correction on the weekly cross-unit mean loss difference; TOST against a ±1% margin (90% CI); MDE at 80% power. See `docs/methods/results_kit.md`.

Key: **G_emb** = WIS(L3) − WIS(L4) (raw AlphaEarth gain); **G_id** = WIS(L3) − WIS(L3+C*) (gain from a pure location/ID control); **G_excess** = WIS(L3+C*) − WIS(L4+C*) (primary: what AlphaEarth adds beyond the best ID control).

## 1. Status of every cell

| cell | group | description | C* | status | what is missing |
|---|---|---|---|---|---|
| BR_S1 | primary/history | Brazil S1, history arm (primary) | C1 | pending | L3: brazil_s1_sens_seed2_L3: not started; L4: brazil_s1_sens_seed2_L4: not started; L3C: brazil_s1_sens_seed2_L3_Cstar: not started; L4C: brazil_s1_sens_seed1_L4_Cstar: not started; brazil_s1_sens_seed2_L4_Cstar: not started |
| BR_S2 | primary/history | Brazil S2, history arm (primary) | selection pending (stale) | pending | L3: brazil_s2_L3: not started; L4: brazil_s2_L4: not started; L3C: brazil_s2_L3_Cstar: not started; L4C: brazil_s2_L4_Cstar: not started |
| BR_S3 | primary/history | Brazil S3, history arm (primary) | selection pending (stale) | pending | L3: brazil_s3_L3: not started; L4: brazil_s3_L4: not started; L3C: brazil_s3_L3_Cstar: not started; L4C: brazil_s3_L4_Cstar: not started |
| BR_S4 | primary/history | Brazil S4, history arm (primary) | selection pending (stale) | pending | L3: brazil_s4_L3: not started; L4: brazil_s4_L4: not started; L3C: brazil_s4_L3_Cstar: not started; L4C: brazil_s4_L4_Cstar: not started |
| BR_S5 | primary/history | Brazil S5, history arm (primary) | selection pending (stale) | pending | L4: brazil_s5_L4: partial (5 chunks); L3C: brazil_s5_L3_Cstar: not started; L4C: brazil_s5_L4_Cstar: not started |
| CO_S1 | primary/history | Colombia S1, history arm (primary) | C1 | pending | L4C: colombia_s1_shared_L4_Cstar: not started |
| CO_S2 | primary/history | Colombia S2, history arm (primary) | selection pending (stale) | pending | L3: colombia_s2_L3: not started; L4: colombia_s2_L4: not started; L3C: colombia_s2_L3_Cstar: not started; L4C: colombia_s2_L4_Cstar: not started |
| CO_S3 | primary/history | Colombia S3, history arm (primary) | selection pending (stale) | pending | L3: colombia_s3_L3: not started; L4: colombia_s3_L4: not started; L3C: colombia_s3_L3_Cstar: not started; L4C: colombia_s3_L4_Cstar: not started |
| CO_S4 | primary/history | Colombia S4, history arm (primary) | selection pending (stale) | pending | L3: colombia_s4_L3: not started; L4: colombia_s4_L4: not started; L3C: colombia_s4_L3_Cstar: not started; L4C: colombia_s4_L4_Cstar: not started |
| CO_S5 | primary/history | Colombia S5, history arm (primary) | selection pending (stale) | pending | L3: colombia_s5_L3: not started; L4: colombia_s5_L4: not started; L3C: colombia_s5_L3_Cstar: not started; L4C: colombia_s5_L4_Cstar: not started |
| PE_S1 | primary/history | Peru S1, history arm (primary) | C1 | available |  |
| PE_S5 | primary/history | Peru S5, history arm (primary) | selection pending (stale) | pending | L3: peru_s5_L3: not started; L4: peru_s5_L4: not started; L3C: peru_s5_L3_Cstar: not started; L4C: peru_s5_L4_Cstar: not started |
| TW_S1 | primary/history | Taiwan S1, history arm (primary) | C1 | available |  |
| TW_S5 | primary/history | Taiwan S5, history arm (primary) | selection pending (stale) | pending | L3: taiwan_s5_L3: not started; L4: taiwan_s5_L4: not started; L3C: taiwan_s5_L3_Cstar: not started; L4C: taiwan_s5_L4_Cstar: not started |
| BR_S1_3seeds | secondary/sensitivity | Brazil S1, primary + 2 extra seeds (seed-averaged; extra seeds h1/h4) | C1 | pending | L3: brazil_s1_sens_seed2_L3: not started; L4: brazil_s1_sens_seed2_L4: not started; L3C: brazil_s1_sens_seed2_L3_Cstar: not started; L4C: brazil_s1_sens_seed1_L4_Cstar: not started; brazil_s1_sens_seed2_L4_Cstar: not started |
| BR_S1_yref | secondary/sensitivity | Brazil S1 sensitivity: yearly features aligned to the origin year (strictly causal) (G_emb only) | n/a (no C* run) | pending | L3: brazil_s1_sens_yref_L3: not started; L4: brazil_s1_sens_yref_L4: not started; L3C: brazil_s1_sens_yref_L3: not started; L4C: brazil_s1_sens_yref_L4: not started |
| BR_S1_delay2 | secondary/sensitivity | Brazil S1 sensitivity: 2-week reporting delay (G_emb only) | n/a (no C* run) | pending | L3: brazil_s1_sens_delay2_L3: not started; L4: brazil_s1_sens_delay2_L4: not started; L3C: brazil_s1_sens_delay2_L3: not started; L4C: brazil_s1_sens_delay2_L4: not started |
| BR_S1_ctrlC3 | secondary/sensitivity | Brazil S1 controls panel: C3 in place of C* (h1, h4) | C3 | pending | L3: brazil_s1_sens_seed2_L3: not started; L4: brazil_s1_sens_seed2_L4: not started; L3C: brazil_s1_sens_ctrl_L3_C3: not started; L4C: brazil_s1_sens_ctrl_L4_C3: not started |
| BR_S1_ctrlC6 | secondary/sensitivity | Brazil S1 controls panel: C6 in place of C* (h1, h4) | C6 | pending | L3: brazil_s1_sens_seed2_L3: not started; L4: brazil_s1_sens_seed2_L4: not started; L3C: brazil_s1_sens_ctrl_L3_C6: not started; L4C: brazil_s1_sens_ctrl_L4_C6: not started |
| BR_S1_perlevel | secondary/sensitivity | Brazil S1, per-level tuning (L3/L4 31 leaves; superseded primary) | C1 | available |  |
| TW_S1_BRparams | secondary/sensitivity | Taiwan S1 with Brazil's tuned params and C* | C1 | available |  |
| BR_S1_nohist | secondary/no-history | Brazil S1, no-history arm (ref = N3) | selection pending (stale) | pending | L3: brazil_s1_nohist_N3: not started; L4: brazil_s1_nohist_N4: not started; L3C: brazil_s1_nohist_N3_Cstar: not started; L4C: brazil_s1_nohist_N4_Cstar: not started |
| BR_S2_nohist | secondary/no-history | Brazil S2, no-history arm (ref = N3) | selection pending (stale) | pending | L3: brazil_s2_nohist_N3: not started; L4: brazil_s2_nohist_N4: not started; L3C: brazil_s2_nohist_N3_Cstar: not started; L4C: brazil_s2_nohist_N4_Cstar: not started |

Primary family: **2 of 14 cells available**. Holm p-values are over the available cells only and are provisional until all 14 are in; `p_bonf14` in T1 is the conservative bound.

## 2. Headline numbers

### PE_S1: Peru S1, history arm (primary) (C* = C1)
Rows scored 96,108; test years [2020, 2021, 2022, 2023]; horizons scored [1, 2, 3, 4], primary pooled over h{1,4}; seeds [0]; zero-filled share 0.56; outbreak share 0.228.

- **G_excess** (pooled h{1,4}, primary) -0.62% [-1.35, +0.12]: L4+C* is worse than L3+C* by 0.62% of WIS(ref) (95% CI -1.35 to +0.12%; p = 0.094; MDE 1.03%): **inconclusive**, i.e. the CI crosses 0 and reaches past the ±1% margin: the data cannot tell.
- **G_emb** (pooled h{1,4}, primary) -0.89% [-1.64, -0.13]: L4 is worse than L3 by 0.89% of WIS(ref) (95% CI -1.64 to -0.13%; p = 0.025; MDE 1.06%): **inferior**, i.e. the 95% CI excludes 0 on the harm side: the second model is worse.
- **G_id** (pooled h{1,4}, primary) -0.28% [-1.02, +0.46]: L3+C* is worse than L3 by 0.28% of WIS(ref) (95% CI -1.02 to +0.46%; p = 0.427; MDE 1.04%): **equivalent**, i.e. the 90% CI lies inside ±1% of WIS(ref): any effect is too small to matter.
- *Secondary* G_excess pooled over h1-4 (not in the Holm family): -0.57% [-1.29, +0.15]; p = 0.112; inconclusive.
- **ID share**: not estimable: G_emb < 1% of WIS(L3)
- Ladder (pooled h{1,4}): L0 0.6541, L1 0.2454, L2 0.2442, L3 0.2448, L4 0.2469, L3+C* 0.2454, L4+C* 0.2470. Best = L2. 80% coverage 0.73–0.84 overall, 0.47–0.69 on non-zero targets.
- G_excess by stratum (pooled h{1,4}): observed +0.03% [-0.83, +0.89]; zero_filled -6.40% [-8.90, -3.90]; outbreak -1.05% [-2.65, +0.54]

### TW_S1: Taiwan S1, history arm (primary) (C* = C1)
Rows scored 238,260; test years [2020, 2022, 2023, 2024]; horizons scored [1, 2, 3, 4], primary pooled over h{1,4}; seeds [0]; zero-filled share 0.97; outbreak share 0.008.

- **G_excess** (pooled h{1,4}, primary) -0.39% [-1.00, +0.22]: L4+C* is worse than L3+C* by 0.39% of WIS(ref) (95% CI -1.00 to +0.22%; p = 0.192; MDE 0.86%): **equivalent**, i.e. the 90% CI lies inside ±1% of WIS(ref): any effect is too small to matter.
- **G_emb** (pooled h{1,4}, primary) -0.93% [-1.84, -0.02]: L4 is worse than L3 by 0.93% of WIS(ref) (95% CI -1.84 to -0.02%; p = 0.045; MDE 1.28%): **inferior**, i.e. the 95% CI excludes 0 on the harm side: the second model is worse.
- **G_id** (pooled h{1,4}, primary) -0.65% [-1.70, +0.40]: L3+C* is worse than L3 by 0.65% of WIS(ref) (95% CI -1.70 to +0.40%; p = 0.203; MDE 1.47%): **inconclusive**, i.e. the CI crosses 0 and reaches past the ±1% margin: the data cannot tell.
- *Secondary* G_excess pooled over h1-4 (not in the Holm family): -0.35% [-0.93, +0.23]; p = 0.215; equivalent.
- **ID share**: not estimable: G_emb < 1% of WIS(L3)
- Ladder (pooled h{1,4}): L0 0.0885, L1 0.0380, L2 0.0465, L3 0.0383, L4 0.0387, L3+C* 0.0386, L4+C* 0.0387. Best = L1. 80% coverage 0.95–0.98 overall, 0.00–0.26 on non-zero targets.
- G_excess by stratum (pooled h{1,4}): observed -0.14% [-1.19, +0.91]; zero_filled -5.46% [-18.26, +7.35]; outbreak -0.13% [-0.87, +0.62]

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
| BR_S1_perlevel | BR_S1 | G_emb | +0.24 [-0.08, +0.55] | equivalent | pending | pending |
| BR_S1_perlevel | BR_S1 | G_id | -0.07 [-0.31, +0.18] | equivalent | pending | pending |
| BR_S1_perlevel | BR_S1 | G_excess | +0.26 [-0.10, +0.63] | equivalent | pending | pending |
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
snapshot 2026-11-16 21:04:55 (10 s old); budget 48 threads (others 1300% CPU (incl. own non-pipeline jobs)) = 12 workers; held 15; free -3
  T1 brazil_s1_shared             done                                     -                                  held  0 unclaimed   0
  T1 peru_s1_shared               done                                     -                                  held  0 unclaimed   0
  T1 taiwan_s1_shared             done                                     -                                  held  0 unclaimed   0
  T1 colombia_s1_shared           running                                  colombia_s1_shared_L4_Cstar        held  5 unclaimed   6
  T1 taiwan_s1brp                 done                                     -                                  held  0 unclaimed   0
  T2 brazil_s1_sens_seeds         running                                  brazil_s1_sens_seed1_L4_Cstar      held 10 unclaimed   0 RESERVED
  T2 brazil_s5                    running                                  brazil_s5_controls_2019            held  0 unclaimed   8
  T2 colombia_s5                  running                                  colombia_s5_controls_2019          held  0 unclaimed  12
  T2 peru_s5                      running                                  peru_s5_controls_2019              held  0 unclaimed  18
  T2 taiwan_s5                    running                                  taiwan_s5_controls_2019            held  0 unclaimed  18
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
  T4 taiwan_s1_l2shared           running                                  taiwan_s1_shared_L2                held  0 unclaimed  16
  T5 brazil_s4                    running                                  brazil_s4_controls_2019            held  0 unclaimed 130
```
