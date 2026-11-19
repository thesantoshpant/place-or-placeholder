# Round-3 embedding-representation variants (EXP-A): pre-specification

**Status.** Post hoc and **exploratory**. Written on 2026-11-19, after external review round 3 (`audits/final_round/TRIAGE_round3.md`, section C, "EXP-A"; referee RB items M2, M6, M11, E2), and **before any variant run has produced output**. No estimand, score or forecast of these runs had been computed when this file was written. Scoring is done later by a separate analysis agent, after this document is committed. None of these runs reads, or is chosen from, the blinded run directories (BR S4, BR S2 no-history, BR S1 `sens_{yref,delay,ctrl}`).

**Question.** The primary analysis gives AlphaEarth to LightGBM as 64 raw, unit-normalised columns of the year y−1 embedding (L4). A reviewer can object that this representation, not the information in the embedding, explains the null. These variants test three other representations and one other ladder position.

## Variants

Code: `src/pop/features/variants.py` (levels registered in `pop.features.levels.LEVELS`; existing levels unchanged, checked bit-for-bit on real data and by `tests/test_variants.py`).

| Code | Name | Columns | Definition |
|---|---|---|---|
| V1 | AE-kNN risk encoding | 1 (`v1_ae_knn`) | Embedding-space analogue of C1. For each unit: the weighted mean, over its **k = 5 most cosine-similar training units of the same country (itself excluded)**, of those units' mean log1p(cases) over the years **before the first training target year** (exactly C1's source rows: training units only, flag_gap weeks dropped; `c1_source_rows(..., 'pre_train')`). Weight = 1 / (1 − cos + 0.001). Similarity uses the causal static embedding of V3. In unseen-unit splits the training units get **C1's matched leave-out** (S2: no neighbour from the unit's own state/department; S3: none within buffer D); held-out units are encoded from the training pool. Static within (split, fold, origin). Replaces the 64 embedding columns. |
| V2 | PCA-8 | 8 (`v2_pc1..8`) | PCA (SVD, centred, sign fixed so each component's largest-magnitude loading is positive) fitted **per (split, fold, origin) on the training units' unit-year vectors** of the embedding years the training targets use (y − 1 for each training target year y). Held-out units and later years never enter the fit. Each row's y − 1 vector (the L4 block) is projected on the 8 components. Replaces the 64 columns. |
| V3 | Causal static | 64 (`v3_A00..A63`) | Mean of the unit's 2017 and 2018 vectors (each pop-weighted and unit-normalised as in L4), renormalised; the same value in every year. Replaces the yearly y − 1 block. Note: training rows of target year 2018 see the 2018 vector (contemporaneous imagery); all test rows (2020+) see only imagery at least one year older than the target. |
| V4 | Substitution (L2 + AE) | 64 (`ae_00..63`) | Level `L2+AE`: the L4 embedding block (y − 1) in place of the L3 remote-sensing / population block. |

Levels: `L3+V1`, `L3+V2`, `L3+V3` (L3 columns, then the variant block); `L3+C1+V1`, `L3+C1+V2`, `L3+C1+V3` (L3+C1 columns, then the variant block); `L2+AE`.

## Cells and runs

All runs: LightGBM, the country's **shared parameter set** (its S1 L1 tuning, via `params_from`, as the seed-0 primary runs), **seed 0**, **h ∈ {1, 4}**, the same features, folds, test years, LST screen and control kwargs as the cell's existing L3+C\* config. C\* = C1 in every cell below (rule v2). Baselines L3 and L3+C\* are the existing runs of the cell (`configs/primary_cells.yaml`); they are not rerun.

| Order | Cell | Test years | New roles | Existing reference runs |
|---|---|---|---|---|
| 1 | CO S1 | 2020–22 | L3+V1/V2/V3, L3+C1+V1/V2/V3, L2+AE | `colombia_s1_shared_{L3,L3_Cstar}` (via its plan.json) |
| 2 | CO S2 | 2020–22, 5 folds | same 7 | `colombia_s2_{L3,L3_Cstar}` |
| 3 | TW S1 | 2020–24 incl. 2021 | same 7 | `taiwan_s1_shared_*` + `taiwan_s1_tw2021_*` |
| 4 | PE S1 | 2020–23 | same 7 | `peru_s1_shared_*` |
| 5 | BR S2 | 2020–24, 5 folds | L3+V1/V2, L3+C1+V1/V2 (no V3, no V4) | `brazil_s2_{L3,L3_Cstar}` |

Configs: `configs/<cell>_r3_<variant>_<role>.yaml` with `<cell>` ∈ {`colombia_s1`, `colombia_s2`, `taiwan_s1`, `peru_s1`, `brazil_s2`}, `<variant>` ∈ {V1, V2, V3, V4} and `<role>` ∈ {`L3`, `L3_Cstar`, `L2`} (V4 has only `L2`); run dirs `runs/<same stem>`. List in priority order: `runs/queue/r3_expA_configs.txt`.

## Estimands (per cell, per variant V)

- **Embedding gain, variant V:** G_emb^V = WIS(L3) − WIS(L3+V).
- **Excess gain, variant V:** G_excess^V = WIS(L3+C\*) − WIS(L3+C\*+V).
- **Substitution:** S = WIS(L3) − WIS(L2+AE) (positive = the embeddings do better than the hand-built remote-sensing/population block).
- Each reported in log-WIS units and as % of WIS(L3); positive = the variant helps.

## Scoring and inference (same as the v3 results kit)

- WIS on log(1 + cases), median + deciles 0.1–0.9; **h ∈ {1, 4} pooled** (equal weight per week, as the primary family).
- Rows: exclusions_v2 (no-geometry units, incomplete weeks, Espírito Santo from 2019-12-29) and the **origin-year row filter** (`row_filter: origin_year`). Only rows present for both roles of an estimand (and the TW S1 test years incl. 2021).
- Inference: Diebold–Mariano on the per-week mean loss difference, **EWC long-run variance + HLN**, 95% t-CI; equivalence classification with the ±1% of WIS(L3) margin (TOST on the 90% CI), as for the primary family.
- **Multiplicity:** exploratory, **not** part of the 14-cell primary family and not Holm-adjusted with it. **Holm within the variant family** (all G_emb^V, G_excess^V and S estimates above: 5 cells; 3 variants × 2 estimands in CO/TW/PE S1 and CO S2, 2 × 2 in BR S2, plus 4 substitution estimates = 32 tests) is reported beside the unadjusted p values.
- No variant replaces the primary L4 result. A variant gain, if any, is reported as "this representation used the embedding better", not as a revision of the primary estimand.

## Pre-declared reading

- V1 is the most direct place-or-placeholder test in held-out places (CO S2, BR S2): it asks whether embedding similarity transfers historical risk better than geographic proximity (C1). Compare G_emb^{V1} with the existing G_id (C1).
- V2 and V3 test whether the raw 64-axis form or the year-to-year variation of the vector hid a gain.
- V4 tests substitution, not added value.
