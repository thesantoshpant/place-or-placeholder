# Peru S1: Paper-1 estimands (shared params, inference policy v2)

Runs (shared-params rule, `runs/peru_s1_shared/plan.json`):
- L3 = `runs/peru_s1_shared_L3`;
- L4 = `runs/peru_s1_L4` (reused: its params equal L1's);
- L3+C\* = `runs/peru_s1_shared_L3_Cstar`;
- L4+C\* = `runs/peru_s1_L4_Cstar` (reused).

C\* = C1, from the 2019-origin selection in `runs/peru_s1_shared_controls_2019/selection.json`. All four runs
use one params set: Peru L1 (31 leaves, min_data_in_leaf 100, lr 0.05, 400 rounds), at 4 threads, with
seed 0. LightGBM; test years 2020–23; h1–h4.

There is one seed per run, so **no seed SD**. Use the Brazil 2019-origin noise floor (audit H3) as a guide.

Command (15 s):
`python scripts/run/estimands_report.py --l3 runs/peru_s1_shared_L3 --l4 runs/peru_s1_L4 --l3c runs/peru_s1_shared_L3_Cstar --l4c runs/peru_s1_L4_Cstar --out runs/peru_s1_analysis --prefix estimands_v2`
Full tables: `runs/peru_s1_analysis/estimands_v2_tables.md`. Sensitivity variants use the same directory
with prefixes `estimands_v2_noexcl`, `_exclwkall` and `_late`.

## Method
The method is the same as `brazil_s1_estimands_v2.md`:
- DM/EWC + HLN on the weekly cross-unit mean gain; pooled-h = the per-week mean over horizons;
- T = 209 weeks, B = 14, t_14;
- TOST margin = 1% of WIS(L3);
- 52-week state-cluster bootstrap as a sensitivity analysis.

Peru has 22 adm1 clusters.

## Rows and exclusions
- **Keys.** 96,140 keys, identical in all four runs. 0 NaN, 0 flag_gap, and every key matches the panel.
- **No-geometry units** (default): 0 rows removed (none are in Peru).
- **Incomplete weeks**, primary flags (`action == exclude`, k = 0.5; default): **32 rows removed (0.03%)**.
  Rows scored: 96,108.
- **Sensitivity: all incomplete-week flags** (`--exclude-weeks-action all`): 1,888 rows removed. Pooled
  G_excess −0.00127 [−0.00303, +0.00048], p = 0.14.
- **Sensitivity: late-entry universe** (`--universe-first-year-max`): 5,680 rows removed (units whose first
  case comes after the test year). Pooled G_excess −0.00154 [−0.00341, +0.00034], p = 0.10.
- **No exclusions at all:** G_excess −0.00141 [−0.00319, +0.00037], p = 0.11.

The conclusion is the same in every variant.

## Main result (pooled 2020–23; WIS(L3) h1–h4 = 0.1949 / 0.2314 / 0.2632 / 0.2946, pooled 0.2460; margin pooled = 0.00246)

| h | G_excess | 95% CI | DM p | class | MDE (% WIS L3) | 52-wk bootstrap 95% |
|---|---|---|---|---|---|---|
| 1 | −0.00013 | [−0.00088, +0.00063] | 0.725 | equivalent | 0.00106 (0.54%) | [−0.00105, +0.00081] |
| 2 | −0.00093 | [−0.00241, +0.00055] | 0.197 | equivalent | 0.00208 (0.90%) | [−0.00276, +0.00080] |
| 3 | −0.00167 | [−0.00407, +0.00074] | 0.159 | inconclusive | 0.00337 (1.28%) | [−0.00464, +0.00140] |
| 4 | −0.00289 | [−0.00596, +0.00017] | 0.063 | inconclusive | 0.00430 (1.46%) | [−0.00767, +0.00193] |
| **pooled** | **−0.00140** (−0.57%) | **[−0.00318, +0.00037]** | **0.112** | **inconclusive** | **0.00250 (1.01%)** | [−0.00387, +0.00110] |

| estimand (pooled h) | estimate | 95% CI | p | class | MDE |
|---|---|---|---|---|---|
| G_emb | −0.00186 (−0.76%) | [−0.00368, −0.00004] | 0.046 | **inferior** | 0.00256 (1.04%) |
| G_id | −0.00070 (−0.28%) | [−0.00250, +0.00111] | 0.422 | equivalent | 0.00254 (1.03%) |

**Reading.**
- **Embeddings do not help in Peru S1. If anything they hurt.**
  - G_emb is negative at every horizon, and significant at h1 (−0.00072, p = 0.039) and h4 (−0.00361,
    p = 0.034; *inferior*).
  - G_excess is negative too, but not significant (p = 0.11 pooled). Pooled, it is *inconclusive*: the
    90% CI [−0.00286, +0.00006] reaches past −1%, and the MDE (1.01%) sits right at the margin. So Peru
    alone can't establish equivalence at 1%.
- The 52-week bootstrap is wider than EWC here. With 4 test years, 52-week blocks leave only about 4
  independent blocks, but it agrees on the sign and that the result is not significant.
- **ID share: not estimable.** G_emb ≤ 0, or its CI includes 0.

## Per test year (G_excess, pooled over h; secondary; B = 5)

| year | G_excess | 95% CI | p | class |
|---|---|---|---|---|
| 2020 | −0.00275 | [−0.00735, +0.00184] | 0.18 | inconclusive |
| 2021 | −0.00228 | [−0.00575, +0.00120] | 0.15 | inconclusive |
| 2022 | −0.00116 | [−0.00321, +0.00089] | 0.21 | inconclusive |
| 2023 | +0.00060 | [−0.00563, +0.00682] | 0.82 | inconclusive |

## Strata (G_excess, pooled; secondary)
- **Observed:** +0.00006, equivalent.
- **Zero-filled:** −0.00318 [−0.00452, −0.00183], p = 0.0002, inferior. The harm from embeddings is in
  zero-case weeks: adding the embedding raises WIS when nothing happens.
- **Outbreak:** −0.00558, not significant.
- **Non-outbreak:** −0.00118, p = 0.020, inferior.
