# Brazil S1: Paper-1 estimands under the fixed inference policy (v2)

Supersedes `brazil_s1_estimands.md` (8-week bootstrap CIs). Policy: `docs/plans/deviations_from_protocol.md`
rows 9, 11, 12, 16.

## Which runs (read this first)
The shared-params runs this report is meant for (`brazil_s1_shared_L4`, `brazil_s1_shared_L3_Cstar`,
`brazil_s1_shared_L4_Cstar`; L1 params, 127 leaves) **do not exist yet**: `runs/brazil_s1_shared` has
finished only `gen_configs`, and `controls_2019` is still running. Only the L3 run with those params
(`brazil_s1_L3_leaves127`) is complete, and it can't form any estimand by itself.

So this report uses the only complete quadruple: `runs/brazil_s1_L3`, `brazil_s1_L4`,
`brazil_s1_L3_Cstar` (L3+C1) and `brazil_s1_L4_Cstar` (L4+C1). All four have identical frozen LightGBM
params (31 leaves, min_data_in_leaf 100, lr 0.05, 400 rounds, bagging 0.8, feature_fraction 0.9). So within
the quadruple the comparison is like for like, but these are **not** the shared L1 params (127 leaves),
and L3/L4 ran at 16 threads while the C\* runs ran at 4 (audit M8). There is one seed per run (seed 0),
so **no seed SD is available**. The noise floor from the audit (H3) is a per-horizon seed SD of
0.0001–0.0003 for single-run differences. **Re-run this report when the shared runs and the extra seeds
(row 16) are complete:**

```
python scripts/run/estimands_report.py --l3 runs/brazil_s1_L3_leaves127 [extra-seed dirs] \
  --l4 runs/brazil_s1_shared_L4 [..] --l3c runs/brazil_s1_shared_L3_Cstar [..] \
  --l4c runs/brazil_s1_shared_L4_Cstar [..] --out runs/brazil_s1_analysis --prefix estimands_v2_shared
```

Command used here (a few minutes, ≤8 threads):
`python scripts/run/estimands_report.py --l3 runs/brazil_s1_L3 --l4 runs/brazil_s1_L4 --l3c runs/brazil_s1_L3_Cstar --l4c runs/brazil_s1_L4_Cstar --out runs/brazil_s1_analysis --prefix estimands_v2`
Full tables: `runs/brazil_s1_analysis/estimands_v2_tables.md` and `estimands_v2_{main,info,primary}.*`.

## Method (v2)
- **Loss.** Mean log1p WIS (median + deciles). Gains are positive when the second model is better:
  G_emb = L3 − L4, G_id = L3 − (L3+C1), G_excess = (L3+C1) − (L4+C1) (primary).
- **Primary inference** (`pop.eval.estimands.infer_estimand`, `pop.eval.stats.ewc_inference`):
  1. d_{h,t} = cross-unit mean of the seed-averaged per-row gain at horizon h, target week t.
  2. Pooled-h: d_t = mean over horizons of d_{h,t} for each week. One horizon uses d_{h,t} directly.
  3. DM on d_t (T = 261 weeks): EWC long-run variance (B = floor(0.4 T^(2/3)) = 16, t_16 reference) ×
     HLN (pooled-h uses h = 4, the widest). se = se_EWC / HLN; CI = d̄ ± t_B·se at 95%, and at 90% for TOST.
     The 95% CI excludes 0 exactly when the DM p < 0.05.
- **TOST.** Margin = 1% of WIS(L3), the same weekly-pooled mean. Classes: *equivalent* (90% CI inside
  ±margin; checked first), *superior* (95% CI > 0 and p < .05), *inferior*, else *inconclusive*.
  MDE = (t_{B,.975} + t_{B,.80})·se.
- **Sensitivity.** States × 52-week circular blocks bootstrap (shared across states), 2,000 replicates,
  percentile CI of the row-level mean. It is not run per year or per stratum.
- **Multiplicity.** None here. The primary family (pooled-h G_excess, Holm over the 14 country × split
  cells) is in `scripts/run/primary_family.py` → `runs/primary_family/`.
- **ID share** is computed only if the primary 95% CI of G_emb excludes 0 and G_emb ≥ 1% of WIS(L3).
- **Rows.** 5,759,748 keys, identical across the four runs. Exclusions (defaults): no-geometry units
  removed **0** rows (none are in Brazil) and incomplete weeks (`action == exclude`, k = 0.5) removed **0**.
  There are 0 flag_gap rows.

## Main result (pooled 2020–24; WIS(L3) h1–h4 = 0.1425 / 0.1644 / 0.1830 / 0.2009, pooled 0.1727; margin pooled = 0.00173)

| h | G_excess | 95% CI | DM p | class | MDE (% WIS L3) | 52-wk bootstrap 95% |
|---|---|---|---|---|---|---|
| 1 | +0.00019 | [−0.00003, +0.00041] | 0.083 | equivalent | 0.00031 (0.22%) | [+0.00002, +0.00045] |
| 2 | +0.00030 | [−0.00010, +0.00070] | 0.135 | equivalent | 0.00057 (0.34%) | [−0.00001, +0.00076] |
| 3 | +0.00057 | [−0.00016, +0.00131] | 0.119 | equivalent | 0.00104 (0.57%) | [+0.00002, +0.00146] |
| 4 | +0.00072 | [−0.00032, +0.00175] | 0.161 | equivalent | 0.00146 (0.73%) | [−0.00010, +0.00201] |
| **pooled** | **+0.00045** (0.26%) | **[−0.00015, +0.00104]** | **0.133** | **equivalent** | **0.00084 (0.49%)** | [−0.00001, +0.00117] |

| estimand (pooled h) | estimate | 95% CI | p | class | MDE |
|---|---|---|---|---|---|
| G_emb | +0.00042 (0.24%) | [−0.00018, +0.00102] | 0.155 | equivalent | 0.00084 (0.49%) |
| G_id | −0.00011 (−0.06%) | [−0.00047, +0.00026] | 0.553 | equivalent | 0.00052 (0.30%) |

**Reading.**
- No estimand differs from 0 at any horizon. Each one is *equivalent* to 0 within ±1% of WIS(L3).
- Pooled G_excess is +0.26% of WIS(L3), and its 90% CI upper bound is 0.54%.
- The design could detect 0.49% of WIS(L3) pooled. 1% is detectable at every horizon.
- The 52-week bootstrap agrees closely with EWC. The old "CI excludes 0" claims (8-week blocks) do not
  survive.
- **ID share: not estimable anywhere** (the G_emb CI includes 0; in 2021 G_emb < 0).

## Per test year (pooled over h; secondary; T = 52–53, B = 5)

| year | G_excess | 95% CI | p | class |
|---|---|---|---|---|
| 2020 | +0.00004 | [−0.00028, +0.00035] | 0.78 | equivalent |
| 2021 | −0.00020 | [−0.00055, +0.00014] | 0.19 | equivalent |
| 2022 | +0.00025 | [−0.00016, +0.00066] | 0.18 | equivalent |
| 2023 | +0.00055 | [−0.00045, +0.00154] | 0.22 | equivalent |
| 2024 | +0.00161 | [−0.00107, +0.00428] | 0.18 | inconclusive (MDE 1.43%) |

G_emb is significantly negative in 2021 (−0.00023, p = 0.019), but that is within the margin.

## Strata (secondary; G_excess pooled)
- Observed: +0.00132 [−0.00003, +0.00267], p = 0.055, equivalent at the stratum's own 1% margin.
- Zero-filled: −0.00004, equivalent.
- Outbreak: +0.00128 [−0.00192, +0.00448], equivalent.
- G_id is clearly negative in outbreak weeks (−0.00976, p < 1e-5): C1 hurts there. It is clearly positive
  in zero-filled weeks.

## What changed from the superseded report
- **Primary CI.** It is now DM/EWC (it was the 8-week state × block bootstrap). The point estimates are
  unchanged, and the DM p-values match the earlier raw DM p.
- **Bootstrap.** It is now a sensitivity analysis with 52-week blocks.
- **Classification.** TOST, the MDE and the equivalence classes are new.
- **ID-share gate.** It now uses the EWC CI.
- **Holm.** It moved to the primary family; the per-estimand Holm over horizons is gone.
