# Round 3, part C: representation variants and extra seeds (scored 2026-11-19)

Post hoc and exploratory. The specifications were written and committed before any of these runs were scored: `docs/methods/round3_variants.md` (EXP-A) and `docs/methods/round3_runs.md` (EXP-B).

Script: `scripts/analysis/round3_score.py` (`--part variants|seeds|tuning|sanity`, `--items PATTERN`). Data: `R3_C_variants.csv`, `R3_C_seeds.csv` (this folder).

**Scoring.** Same as the v3 results kit, using the kit's own functions:
- rows: exclusions_v2, the Espírito Santo unit-week exclusion and the origin-year row filter;
- horizons h ∈ {1, 4}, pooled with equal weight per week;
- inference: DM test with EWC long-run variance + HLN, 95% t-CI, and TOST at ±1% of WIS(L3).

Every percentage is a share of WIS(L3) on log(1 + cases). A positive value means the variant helps.

**Sanity check: PASS.** Recomputing Colombia S1 (L3, L4, L3+C\*, L4+C\*) reproduces T1 exactly (difference 0.0) for G_emb, G_id, G_excess, the p-values, the CI and n_rows (319,930). In the seed table, seed 0 likewise reproduces T1 for CO S1 and CO S2.

## 1. Representation variants (EXP-A)

The four variants:
- **V1** = embedding-similarity risk encoding (1 column).
- **V2** = PCA-8.
- **V3** = causal static embedding, the mean of 2017 and 2018.
- **V4** = L2 + embedding in place of the remote-sensing/population block (substitution).

Every variant uses C\* = C1 and seed 0.

**Holm.** Holm is applied within the 32-test variant family named in the spec. The V1-vs-C1 and L2-vs-L2+AE contrasts are extra and are not in the family.

### Embedding gain, % of WIS(L3) [95% CI], DM p (Holm p)

Each variant replaces the 64 raw columns.

| Cell | Original L4 (64 cols) | V1 kNN risk | V2 PCA-8 | V3 static |
|---|---|---|---|---|
| Colombia new years (S1) | −0.36 (p .005) | −0.07 [−0.13, −0.01] p .023 (1.0) | −0.07 [−0.17, +0.02] p .12 (1.0) | −0.14 [−0.25, −0.03] p .017 (1.0) |
| Colombia held-out states (S2) | −0.59 (p <.001) | −0.04 [−0.11, +0.03] p .19 (1.0) | −0.14 [−0.22, −0.07] p .001 (.027) | −0.30 [−0.40, −0.20] p <.001 (.001) |
| Peru new years (S1) | −0.94 (p .020) | −0.01 [−0.13, +0.10] p .81 (1.0) | −0.15 [−0.64, +0.35] p .53 (1.0) | −0.66 [−1.19, −0.13] p .018 (1.0) |
| Taiwan new years (S1, incl. 2021) | −1.06 (p .024) | −0.66 [−1.76, +0.45] p .23 (1.0) | −0.46 [−1.71, +0.78] p .44 (1.0) | −0.60 [−1.58, +0.37] p .21 (1.0) |
| Brazil held-out states (S2) | −0.02 (p .88) | −0.05 [−0.11, +0.01] p .10 (1.0) | −0.02 [−0.17, +0.12] p .75 (1.0) | not run |

### Excess gain beyond C1, % of WIS(L3) [95% CI], DM p (Holm p)

| Cell | Original L4+C\* | V1 | V2 | V3 |
|---|---|---|---|---|
| Colombia S1 | −0.39 (p .001) | −0.05 [−0.09, −0.01] p .014 (1.0) | −0.13 [−0.24, −0.02] p .025 (1.0) | −0.08 [−0.19, +0.03] p .12 (1.0) |
| Colombia S2 | −0.47 (p <.001) | −0.01 [−0.05, +0.03] p .68 (1.0) | −0.11 [−0.18, −0.05] p .003 (.085) | −0.21 [−0.31, −0.12] p <.001 (.015) |
| Peru S1 | −0.70 (p .056) | +0.04 [−0.10, +0.19] p .53 (1.0) | +0.06 [−0.41, +0.54] p .77 (1.0) | **−0.87 [−1.32, −0.42] p .001 (.032)** |
| Taiwan S1 | −0.60 (p .049) | −0.11 [−0.29, +0.07] p .20 (1.0) | +0.15 [−0.53, +0.83] p .65 (1.0) | −0.12 [−0.32, +0.08] p .22 (1.0) |
| Brazil S2 | −0.00 (p 1.0) | −0.02 [−0.06, +0.02] p .31 (1.0) | +0.05 [−0.12, +0.21] p .56 (1.0) | not run |

### V1 against geography directly

The contrast is WIS(L3+C1) − WIS(L3+V1); positive means V1 is better. It is not in the Holm family.

| Cell | % [95% CI] | p |
|---|---|---|
| Colombia S1 | −0.01 [−0.23, +0.21] | .94 |
| Colombia S2 | +0.04 [−0.00, +0.08] | .064 |
| Peru S1 | +0.24 [−0.48, +0.97] | .48 |
| Taiwan S1 | −0.03 [−0.20, +0.15] | .74 |
| Brazil S2 | +0.00 [−0.07, +0.07] | .91 |

### Substitution (V4)

Positive means the embedding does better than the comparison.

| Cell | L3 − (L2+AE) | L2 − (L2+AE), not in family |
|---|---|---|
| Colombia S1 | **−0.79 [−1.15, −0.42] p <.001 (Holm .018)** | −0.48 [−0.80, −0.17] p .006 |
| Colombia S2 | **−0.93 [−1.27, −0.59] p <.001 (Holm .003)** | no Colombia S2 L2 run; not estimable |
| Peru S1 | −0.84 [−1.66, −0.01] p .047 (Holm .93) | −1.10 [−1.90, −0.31] p .010 |
| Taiwan S1 | −0.79 [−1.77, +0.20] p .11 (Holm 1.0) | −0.74 [−1.37, −0.11] p .024 |

The Taiwan L2 − (L2+AE) contrast now includes 2021 (141,645 rows; rescored 2026-11-20). Without 2021 it was −0.64 [−1.27, −0.02] p .044.

### Reading

- **No representation turns the embeddings into a significant gain.** Across all 28 G_emb/G_excess tests, none has a positive point estimate with a CI above 0. The largest positive estimate is +0.15% (V2, Taiwan excess, p .65).
- **Compact forms mostly shrink the loss rather than reverse it.** V1 (1 column) and V2 (8 columns) are much closer to zero than the 64 raw columns, for example Colombia S1 −0.07% vs −0.36%. Fewer noisy columns means less to overfit, not more signal.
- **V1 does not beat C1-like geography.** It is indistinguishable from C1 in every cell: within ±0.05% in Colombia and Brazil held-out states, with the largest edge +0.04% (Colombia S2, p .064). Embedding similarity transfers historical risk about as well as geographic neighbours do, and no better. This fits the "placeholder" reading.
- **V3 (static) does not remove the loss.** It halves it in Colombia S2 (−0.30% vs −0.59%), but the loss stays significant after Holm. It leaves the Peru excess loss as large as before (−0.87%, Holm .032). Year-to-year changes in the vector are not what hurts.
- **V4: the embedding does not substitute for the remote-sensing/population block.** L2+AE is worse than L3 in all four cells (significant after Holm in Colombia S1 and S2). It is also worse than L2 without any place block (Colombia S1, Peru S1, Taiwan without 2021).
- Every Holm-significant variant result is negative: CO S2 V2 G_emb, CO S2 V3 G_emb and G_excess, PE S1 V3 G_excess, and the CO S1/S2 substitution. All sit within or near the ±1% margin.

## 2. Extra seeds (EXP-B): Colombia S1 and S2

The kit's multi-seed estimator is used, as for Brazil S1: `seed_gain_frame` with `seed_policy="common"`, the seed-averaged per-row loss and the same DM/EWC + HLN. Per-seed rows are single-seed estimates on the same rows. The seed SD is the SD of the three per-seed estimates.

| Cell | Estimand | Seed 0 | Seed 1 | Seed 2 | Mean of seeds 0–2 [95% CI], p | Seed SD |
|---|---|---|---|---|---|---|
| Colombia S1 | G_excess | −0.39 (p .001) | −0.48 (p <.001) | −0.40 (p .005) | **−0.42 [−0.64, −0.21], p .001** | 0.00006 (0.05%) |
| Colombia S1 | G_emb | −0.36 | −0.42 | −0.37 | −0.38 [−0.61, −0.16], p .003 | 0.00004 (0.04%) |
| Colombia S1 | G_id | −0.07 | −0.01 | −0.11 | −0.06 [−0.32, +0.19], p .60 | 0.00006 |
| Colombia S2 | G_excess | −0.47 (p <.001) | −0.58 (p <.001) | −0.52 (p <.001) | **−0.52 [−0.74, −0.30], p <.001** | 0.00006 (0.05%) |
| Colombia S2 | G_emb | −0.59 | −0.59 | −0.62 | −0.60 [−0.81, −0.39], p <.001 | 0.00002 (0.02%) |
| Colombia S2 | G_id | −0.08 | +0.01 | −0.10 | −0.06 [−0.09, −0.03], p .002 | 0.00008 |

- **The Colombia losses survive seed averaging, and grow a little.** Every seed is negative and significant on its own. The seed SD of G_excess (≈0.00006 log-WIS, 0.05% of WIS) is roughly a tenth of the effect, so seed noise does not explain the Colombia result. The TOST label stays "equivalent", because the effect lies inside ±1%.
- G_id (C1) is the seed-sensitive quantity, not G_excess. In Colombia S2 seed 1 flips its sign (+0.01%).

## 3. Extra seeds (EXP-B): the other seven cells (scored 2026-11-20)

The estimator is the same as in section 2 (common seeds per estimand; seed SD = SD of the three per-seed estimates). The seed-0 values reproduce T1 exactly in every cell.

**TW S5 and PE S5 (pre-declared compute cut).** Only L3+C\* and L4+C\* have seeds 1–2. So in these two cells G_excess is the 3-seed mean, but G_emb and G_id stay **seed 0 only**. For G_id this happens because L3 (seed 0) and L3+C\* (seeds 0–2) have only seed 0 in common.

### G_excess, % of WIS(L3) on log(1 + cases), h{1,4}

| Cell | C\* | Seed 0 (T1) | Seed 1 | Seed 2 | Mean of seeds 0–2 [95% CI], p | Seed SD (% of WIS) |
|---|---|---|---|---|---|---|
| BR S5 | C3 | −0.60 (p <.001) | −0.62 | −0.82 | **−0.68 [−0.94, −0.42], p <.001** | 0.12 |
| CO S3 | C1 | −0.65 (p .003) | −0.70 | −0.70 | **−0.68 [−1.08, −0.29], p .003** | 0.03 |
| CO S4 | C1 | −0.43 (p .003) | −0.48 | −0.42 | **−0.45 [−0.68, −0.21], p .002** | 0.03 |
| PE S1 | C1 | −0.70 (p .056) | −0.88 | −0.87 | **−0.82 [−1.49, −0.14], p .022** | 0.10 |
| PE S5 | C3 | +0.96 (p .079) | +0.96 | +0.88 | +0.93 [−0.16, +2.02], p .088 | 0.04 |
| TW S1 (incl. 2021) | C1 | −0.60 (p .049) | −0.87 | −0.67 | **−0.71 [−1.40, −0.03], p .042** | 0.14 |
| TW S5 (incl. 2021) | C3 | −17.30 (p .002) | −18.06 | −19.51 | **−18.29 [−29.80, −6.78], p .004** | 1.12 |

### G_emb and G_id (3-seed mean; seed 0 only where marked)

| Cell | G_emb [95% CI], p | G_id [95% CI], p |
|---|---|---|
| BR S5 | −0.39 [−1.34, +0.55], p .39 | +0.15 [−0.89, +1.18], p .77 |
| CO S3 | −0.82 [−1.14, −0.49], p <.001 | −0.08 [−0.14, −0.02], p .011 |
| CO S4 | −0.54 [−0.78, −0.30], p <.001 | −0.10 [−0.12, −0.08], p <.001 |
| PE S1 | −0.91 [−1.62, −0.20], p .016 | −0.20 [−0.92, +0.52], p .56 |
| PE S5 | +0.68 [−0.59, +1.96], p .27 (seed 0) | −0.44 [−0.80, −0.07], p .022 (seed 0) |
| TW S1 | −0.95 [−1.71, −0.18], p .018 | −0.41 [−0.97, +0.16], p .15 |
| TW S5 | −21.60 [−31.82, −11.39], p <.001 (seed 0) | −3.36 [−6.52, −0.20], p .039 (seed 0) |

### Holm over the 13 non-blinded cells (BR S4 still blinded), G_excess

This is computed with the 3-seed p-values wherever three seeds exist (BR S1 already had them; BR S2, BR S3 and CO S5 have seed 0 only). File: GPU `tmp/score4/holm13_3seed.csv`. Holm over 14 will be recomputed by the final kit once BR S4 is unblinded.

| Cell | Holm p, seed 0 (T1) | Holm p, 3 seeds |
|---|---|---|
| BR S5 | .001 | .0005 |
| CO S1 | .012 | .013 |
| CO S2 | .007 | .003 |
| CO S3 | .026 | .027 |
| CO S4 | .025 | .017 |
| TW S5 | .017 | .031 |
| PE S1 | .34 | .16 |
| TW S1 | .34 | .25 |
| PE S5 | .39 | .44 |
| BR S1 / BR S2 / CO S5 | .80 / 1.0 / .80 | .80 / 1.0 / .80 (same p; Holm rank unchanged) |
| BR S3 | .39 | .44 (same p; Holm rank shifts) |

**Reading.**
- **No significance call changes after Holm.** The same six cells are Holm-significant losses as at seed 0: BR S5, CO S1–S4 and TW S5. Every loss gets slightly larger with seed averaging (by 0.01–0.12 pp, TW S5 by 1 pp). No seed reverses a sign.
- **Unadjusted changes:**
  - PE S1 goes from p .056 to **p .022**, and its CI now excludes 0, so the TOST class changes from inconclusive to "inferior" at ±1%. It is not Holm-significant (.16).
  - CO S3's 3-seed CI crosses −1%, so its unadjusted TOST class changes from equivalent to "inferior". This matches T1's existing Holm-TOST reading for CO S3.
  - TW S1 stays nominal (p .042; Holm .25).
- **PE S5 gain:** it stays non-significant (+0.93%, p .088), and every seed is positive.
- **Seed noise:**
  - The seed SD is small next to the effects (0.03–0.14% of WIS; TW S5 1.1%).
  - BR S5 has the largest relative seed spread (SD 0.12% against a −0.68% effect), because C\* = C3 redraws its permutation by seed. Even so, all three seeds are significant on their own.
  - G_id is again the seed-sensitive estimand: seed 1 makes it ≈0 in CO S3, CO S4 and TW S1.

## 4. Equal-budget tuning, Colombia S1 (EXP-B S4)

File: `R3_C_tuning.csv`.

**Chosen configurations.** Separate tuning (train 2018 → validate 2019, 18-point grid) picked the **same configuration for both levels**: num_leaves 31, min_data_in_leaf 100, feature_fraction 0.9. That is exactly the shared Colombia set; the LightGBM default feature_fraction is 0.9.
- Best validation pinball loss: L3+C1 .07114, L4+C1 .07174.
- Runners-up:
  - L3+C1: 15/100/0.9 (+0.6%);
  - L4+C1: 15/100/0.9 (+0.4%).

**Result.** Because the configurations are identical, the tuned test-year forecasts are bit-identical to the shared ones (max |Δ| = 0 on 3.03M forecast rows).
- G_excess best-for-each = G_excess shared = **−0.39% [−0.58, −0.19], p .001** (seed 0).
- The tuning gain is 0 for both levels.

**Reading.** In Colombia the loss is not an artefact of one shared parameter set: each level, tuned on its own, picks the same configuration. min_data 1000/5000 and feature_fraction 0.3 were worse for both levels.

## 5. Taiwan S1 with 2021 (EXP-B S2)

The 2021 test-year runs (`runs/taiwan_s1_r3_tw2021_*`) are concatenated with the existing 2020 and 2022–24 runs. Scoring is v3 rows, seed 0. Files: `R3_C_tw2021_ladder.csv` and `R3_C_tw2021_panel.csv`. The script is `scripts/analysis/round3_extra.py tw2021`, which replicates the `control_panel.py` logic; that script was not run. A1 is from `round3_analyses.py --only A1 --a1-tw2021` (a new flag that appends the 2021 L1/L2 runs).

**Row-count check: PASS.** Each of these has exactly **141,645** rows (2021 has all-zero targets):
- the primary frame;
- every ladder rung (L0, NB, L1, L2, L3, L4, L3+C\*, L4+C\*);
- every panel control;
- every A1 increment.

### Ladder and baselines, pooled h{1,4}

| Model | WIS log | Rel. WIS vs L0 | Cov 40 | Cov 80 | Cov 80 on case weeks | Rel. vs L0 without 2021 |
|---|---|---|---|---|---|---|
| L0 seasonal naive | .0743 | 1.000 | .954 | .954 | .001 | 1.000 |
| NB GLM (L1) | .0475 | .640 | .979 | .986 | .417 | .644 |
| LightGBM L1 | .0316 | .425 | .977 | .982 | .245 | .428 |
| LightGBM L2 (shared params) | .0319 | .430 | .977 | .982 | .232 | (old table: per-level-tuned L2, .517) |
| LightGBM L3 | .0319 | .430 | .977 | .982 | .250 | .432 |
| LightGBM L4 | .0323 | .434 | .977 | .982 | .242 | .436 |
| LightGBM L3+C\* | .0321 | .432 | .977 | .982 | .241 | .434 |
| LightGBM L4+C\* | .0323 | .435 | .977 | .982 | .241 | .436 |

There is no TimesFM run for Taiwan. Adding 2021 lowers every absolute WIS, because the all-zero year is easy, but it leaves the ordering and relative WIS almost unchanged.

**Coverage.** Coverage is mostly zero weeks. LightGBM's 80% coverage on case weeks is only .23–.25.

### R3-A1 positive control (increments, % of WIS(L3))

| Increment | With 2021 | Without 2021 |
|---|---|---|
| L1→L2 (climate) | −1.10 [−2.60, +0.40], p .14 | −0.93, p .21 |
| L2→L3 (RS + pop) | +0.05 [−0.58, +0.68], p .88 | +0.06, p .85 |
| L1→L3 (all non-case covariates) | −1.06 [−2.69, +0.58], p .19 | −0.87, p .28 |
| L3→L4 (embedding) | −1.06 [−1.96, −0.16], p .024 | −0.94, p .043 |

**Reading.** As before, no covariate step is detectable in Taiwan; climate is, if anything, harmful. The positive-control conclusion is unchanged: the Taiwan null says little about design sensitivity.

The other cells' A1 rows are identical. The pre-2021 file was copied to `R3_A1_positive_control_no2021.csv`.

### Fixed control panel with 2021 (seed 0; no multiplicity correction)

| Control | G_id_k [95% CI], p | G_excess_k [95% CI], p | G_excess_k without 2021 |
|---|---|---|---|
| C1 | −0.63 [−1.68, +0.43], p .23 | −0.60 [−1.20, −0.00], p .049 | −0.44 (p .12) |
| C2 | −0.36 [−0.76, +0.03], p .070 | −0.94 [−2.03, +0.15], p .087 | −0.77 (p .16) |
| C3 | −0.58 [−1.29, +0.12], p .097 | −0.68 [−1.45, +0.09], p .079 | −0.54 (p .15) |
| C6 | −2.29 [−5.59, +1.02], p .16 | −0.52 [−1.16, +0.13], p .11 | −0.42 (p .18) |

G_emb with 2021 = −1.06% [−1.96, −0.16], p .024.

**Reading.**
- With 2021, every G_excess_k becomes slightly more negative.
- No control turns the embedding into a gain.
- No control helps L3 (every G_id_k is negative).
- The Taiwan row set is now a single 141,645-row set everywhere.

## 6. Colombia S2 without case history (EXP-B S3; exploratory)

File: `R3_C_co_s2_nohist.csv` (estimands) and `R3_C_co_s2_nohist_ladder.csv`. The script is `scripts/analysis/round3_extra.py nohist`.

**Code check.** The same code path reproduces T6b for Brazil S1 no-history exactly (max |Δ| = 0 for estimates and p-values).

**Selection.**
- C\* = **C2 (coordinates)** under rule v2 at the 2019 origin. C2 was the tie set's only member: N3+C2 .33733 vs C4 .34366 and C3 .34467.
- At 2019, N3+C2 did not beat N3 (.33728).
- Folds, years and seeds:
  - Colombia grouped S2 folds;
  - test years 2020–22;
  - 319,930 rows;
  - seed 0;
  - N2 was not run (not in the spec).

### Estimands, % of WIS(N3), pooled h{1,4}

| Estimand | Estimate [95% CI] | p | Brazil S1 no-history (T6b) |
|---|---|---|---|
| G_emb = N3 − N4 | **−5.30 [−8.19, −2.41]** | .002 | +2.54 (p .13) |
| G_id = N3 − N3+C2 | **−2.08 [−3.47, −0.69]** | .007 | +3.30 (p <.001) |
| G_excess = N3+C2 − N4+C2 | **−4.17 [−6.45, −1.90]** | .002 | −0.43 (p .58) |
| C1 rung: N3 − N3+C1 | −1.46 [−2.90, −0.03] | .047 | |
| Excess beyond C1: N3+C1 − N4+C1 | −3.46 [−6.13, −0.79] | .016 | |

The ID share is not estimable, because G_emb is negative. The per-horizon values are the same at h1 and h4.

**Ladder (WIS on log(1 + cases)):**

| Level | WIS |
|---|---|
| N3 | .1989 |
| N3+C1 | .2019 |
| N3+C\* | .2030 |
| N4+C1 | .2089 |
| N4 | .2096 |
| N4+C\* | .2115 |

80% coverage on case weeks: N3 .642, N4 .626.

**Reading (exploratory).**
- In Colombia's held-out states without case history, the embeddings make forecasts clearly worse (≈ −4 to −5%), with or without a location control.
- Neither coordinates (C2) nor static history (C1) help N3 either.
- So the Brazil no-history pattern does **not** replicate in Colombia: there, coordinates carried a gain and the embedding added nothing beyond them.
- What does replicate is that the embedding adds nothing beyond a location control, here with a significant loss.
- With only 3 test years and 5 folds, and with place features generally hurting in held-out Colombian states, this is weak evidence about mechanism. Report it as exploratory.

## 7. Manifest switched to 3 seeds (for the final kit)

- `configs/primary_cells_v3_seed0.yaml` is a byte copy of the seed-0 manifest (sensitivity).
- `configs/primary_cells.yaml` now lists seeds 0–2 for:
  - BR S5, CO S1–S4 and PE S1 (all four roles, in the `runs` lists);
  - PE S5 (L3C, L4C only).
- **Taiwan S1 and S5 use a new additive manifest key, `extra_seed_runs`.** It is read by a new helper `rk_cells._apply_extra_seed_runs`, called once in `build_registry`. The helper appends the seed runs to the primary cell only, after the `add_test_years` (2021) runs. The reason: the seed runs already contain 2021, so adding them to the `runs` lists would leak 2021 rows (seeds 1–2) into the `<id>_no2021` sensitivity cells. Those cells stay seed 0 with the old test years.
- No other kit change. The kit already handles unequal seed sets per estimand (common-seed rule). It records them in `info.seed_set_mismatch_primary` (PE/TW S5: "G_id h1; G_id h4") and does not fail.
- The "fails on unequal seeds" guard lives only in `scripts/run/primary_family.py` (the v2 tool). That tool knows neither `row_filter` nor `add_test_years`, has no cell filter (so it would read BR S4), and would stop on PE/TW S5. **It was therefore not run.**
- **Validation instead:** the kit's own `rk_compute.compute_cell` (`tmp/score4/validate_kit.py`, separate cache `tmp/score4/kitcache`, BR S4 excluded, `make_results.py` not run) on the nine changed cells, using the new manifest. G_excess, G_emb and G_id estimates, p-values, seed counts and row counts equal `R3_C_seeds.csv` exactly (max |Δ| = 0). See `tmp/score4/validate_kit.csv`.
- `round3_score.py --part sanity` now loads seed 0 only. This was needed: with the 3-seed manifest it would otherwise compare a 3-seed CO S1 against T1's seed-0 values.

**Caveats.**
- The extra seeds are post hoc (specified in `round3_runs.md` before scoring; a deviation row is still to be added).
- The secondary h1–h4 pooling of the S1 cells mixes 3 seeds (h1, h4) with seed 0 (h2, h3), as BR S1 already does.
- Downstream analyses that read the registry (`round3_analyses.py` A1–A8, `round3_score.py --part variants`) will see seed-averaged L3/L4 if rerun. The variant contrasts are pinned to seed 0.
