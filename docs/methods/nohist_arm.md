# No-case-history arm (secondary, exploratory): pre-specification

**Status.** Secondary / exploratory analysis. This document was written on 2026-11-16, **after** the Brazil S1 nulls (below) were seen and **before** any no-history run was scored. It fixes the levels, splits, control choice, estimands and decision rule in advance (pre-specified in commit `bd3ba50`). It is not part of the 14-cell primary family.

> **Amendments (2026-11-16, project-wide rule changes, not specific to this arm; see `docs/plans/deviations_from_protocol.md`).** (a) Inference: the sensitivity bootstrap uses **52-week** circular blocks, not 8 (row 11); the primary CI is the DM/EWC t-interval. (b) C3 uses **one fixed permutation per seed across all years** (row 13). (c) C\* is chosen with **selection rule v2** (row 19): degenerate candidates are dropped, the tie set is every candidate within 2·SE (pooled seed SD) of the best, and C\* is the first tie-set member in the priority **C3 > C2 > C6 > C4s > C4**. (d) **BR S3 is dropped** for this arm (compute); only S1 and S2 run. (e) Parameters: the N-levels use Brazil's **L1** parameters (127 leaves / min_data 100), which were tuned on a model *with* case history (audit 3 M-4); this follows the one-parameter-set-per-country rule (row 2) and must be disclosed. (f) **C4s** (the random smooth fields at range min(D, fitted) = 225 km for Brazil; row 15) is a C\* candidate in this arm too, as coded in `scripts/run/select_control.py` (`NOHIST = C2, C3, C4, C4s`, + C6 in S1); it was added in `9de7386`, before any no-history result was read. The text below is the original pre-specification (`bd3ba50`); where it conflicts with (a)–(f), the amendments apply.

## Why
In the primary ladder, every level from L1 up contains the unit's own case history: lags 0–11, plus the same week ±1 in each of the previous 1–3 years. With that history in the model, neither AlphaEarth (L4) nor the location-ID controls (L3+C\*) add anything in Brazil S1: G_excess ≈ +0.1–0.4% of WIS, not significant. So the case history already acts as the ID, and the question "real place information or ID fingerprint?" cannot be answered there.

Place descriptors should matter most where a district has little or no surveillance history. This arm removes every feature derived from cases and asks the same question there.

## Levels (`src/pop/features/levels.py`, `NOHIST_LEVELS`; blocks listed in `N_BLOCKS`)
| Level | Blocks | Columns |
|---|---|---|
| **N2** | calendar + climate | 2 + 51 = **53** |
| **N3** | N2 + remote sensing / population | 53 + 12 = **65** |
| **N4** | N3 + AlphaEarth | 65 + 64 = **129** |
| N3+Ck, N4+Ck | N3 / N4 + control block Ck (same construction, seed and kwargs as L3+Ck) | + block |

- **Calendar (2):** `woy_sin`, `woy_cos` of the target week, computed from the grid's epi-week number only. These are the same two columns L1 has. There is no horizon feature, because a separate model is fitted for each horizon.
- **Climate (51), as in L2:** lags 0–11 of tmean, precip and rh (36), plus 4/8/12-week rolling means of tmean, tmin, tmax, precip and rh (15). All are population-weighted and measured relative to the origin week.
- **Remote sensing / population (12), as in L3:** ndvi, lst_day and lst_night (population-weighted) for the 3 latest complete months before the origin (9); night lights and built share for year y−1 (2); log1p(population) for year y−1 (1). The LST screen is off, as in Brazil S1.
- **AlphaEarth (64), as in L4:** the population-weighted mean embedding of year y−1 (`w_A00..A63`), renormalised to unit length.
- **Removed relative to L2/L3/L4 (21 columns):** `lag_0..lag_11` and `sy{1,2,3}_{m1,0,p1}`.

**Tests** (`tests/test_levels.py`):
- Every N-level is unchanged when all case values in the grid are replaced by random values or NaN.
- The N-blocks are not `history.*` functions, and no block's source code reads `grid.y`.
- N4 = N3 ∪ AlphaEarth block, column for column.
- N2/N3/N4 equal L2/L3/L4 with the 21 history columns dropped.
- Availability rules: poisoning future inputs leaves every N-level unchanged.
- N3+C2…C6 do not depend on cases. N3+C1 does.
- C6 holds one code per unit and is categorical in LightGBM. It raises NotApplicable for unseen units.

## Controls in this arm
- **C1 is "static history", not an ID control.** C1 is a unit's mean (log) cases before training, i.e. a target encoding; for unseen units it is a kNN value from training units. It brings a time-invariant piece of case history back in. It therefore gets its own rung, **N3+C1 vs N4+C1**, and is **excluded from the C\* choice**.
- **C5 (AlphaEarth 2023, static) is excluded from C\***, because it is an embedding, not an ID control.
- **C6 (new) = the unit ID as one LightGBM categorical feature** (`controls.unit_id_categorical`, column `c6_unit_cat`; LightGBM treats columns ending in `_cat` as categorical). It is the purest ID. It is defined only when every test unit is a training unit (S1); it raises `ControlNotApplicable` in S2–S5.
- **C\* candidates (target-free):** C2 (coordinates + spherical harmonics, L = 8), C3 (embeddings from a fixed random source unit, the same in every year; amendment b), C4 (random smooth fields, range 8,483 km), C4s (random smooth fields, range 225 km; amendment f), and **C6 in S1 only**.
- **C\* choice:** the 2019 origin only, separately for each split. C\* was originally the lowest seed-averaged mean log-WIS pooled over h1 and h4; it is now chosen by rule v2 (amendment c). C3, C4 and C4s use 3 seeds (0–2). Script: `scripts/run/select_control.py --ref lgbm-N3`.

## Splits, horizons, years, model
- **Brazil only.**
  - **BR S2** (grouped leave-states-out, 5 folds; the same split definition as the live queue) is the **headline** for this arm, because IDs cannot transfer to held-out states.
  - **BR S1** (temporal; all units are seen) is the contrast.
  - ~~**BR S3** (spatial blocks + 225 km buffer, 5 folds) is added after S2 if time allows (cheap).~~ **Dropped** (amendment d).
- **Horizons:** {1, 4}. **Test years:** 2020–2024 (rolling-origin annual refits, training targets 2018..Y−1). **Selection origin:** 2019.
- **Model:** LightGBM quantile, deciles 0.1–0.9. ONE params set = Brazil S1 L1 tuning (`runs/brazil_s1_baselines/tuning_lgbm-L1.json`, 127 leaves / min_data 100), with no re-tuning. 4 threads. Test-year runs use 1 seed (seed 0), including when C\* is C3 or C4.
- **Runs:** `N3`, `N4`, `N3+C*`, `N4+C*`, `N3+C1` and `N4+C1` on the test years, for each split. N2 is defined but not run.

## Estimands (per split; WIS on log1p cases, median + deciles, pooled over test years and h ∈ {1, 4}; also per horizon)
- **G_emb^N** = WIS(N3) − WIS(N4)
- **G_id^N** = WIS(N3) − WIS(N3+C\*)
- **G_excess^N** = WIS(N3+C\*) − WIS(N4+C\*): the primary estimand of this arm, and the headline in S2.
- **Static-history rung:** G_emb^{N,C1} = WIS(N3+C1) − WIS(N4+C1).
- **Inference:** the same machinery as the main paper. A DM test with EWC variance and HLN correction on the per-week mean WIS difference, with t-CIs from the same EWC variance; a bootstrap over state clusters × 52-week circular blocks is a sensitivity analysis (amendment a).
- **Equivalence margin:** ±1% of WIS(N3) for that split, tested with **TOST** using **90% CIs**:
  - The CI inside (−1%, +1%) of WIS(N3) means **equivalent / negligible**.
  - The CI excluding 0 and its point estimate ≥ 1% means a **gain**.
  - Anything else is **inconclusive**.
- **Interpretation:**
  - **Place information beyond ID:** G_excess^N > 0 (a gain by the rule above) in S2.
  - **ID fingerprint:** G_emb^N > 0, but G_excess^N is equivalent to 0.
  - The ID share G_id^N / G_emb^N is reported only under the main paper's rule: G_emb's CI excludes 0 and G_emb ≥ 1% of WIS(N3).

## Execution
- **Command:** `bash scripts/run/nohist_pipeline.sh launch s1 s2 [s3]`. This starts tmux `pop_nohist` (≤ 2 workers × 4 threads), running S1 then S2 (S3 dropped, amendment d; the arm is now run by the global scheduler, tier T3).
- **Configs:** `configs/brazil_{s1,s2,s3}_nohist_*.yaml`.
- **Outputs:** `runs/brazil_{s}_nohist_<stage>/`.
- **Pipeline state:** `runs/brazil_{s}_nohist/` (`pipeline.log`, `stage_*.done`, `PIPELINE_DONE`).
- **Stages:** gen_configs → controls_2019 → select_control → gen_cstar → N3 → N4 → N3_Cstar → N4_Cstar → N3_C1 → N4_C1.

## Changes to shared code
- `controls.py` gains C6.
- `lgbm.py` passes `categorical_feature` = the columns ending in `_cat`. No existing level produces such a column, so earlier runs are unaffected.
- `levels.py` `CONTROLS` now includes C6 (L3+C6, L4+C6, N3+C6, N4+C6).
