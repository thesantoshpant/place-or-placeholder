# Notes for the paper writers: caveats and disclosures

Plain-language list of everything the paper must say honestly. Each item points to its source. "Dn" = row n of `docs/plans/deviations_from_protocol.md` (reproduced in the paper appendix). Last updated 2026-11-16.

## What was fixed when (pre-specification)
1. **The design freeze has not happened.** It is planned for 15 January 2027. Do not write that anything was "frozen" or "pre-specified before the test-year comparisons". Say what was fixed when: the original protocol (15 Nov 2026), then the dated deviations with commit hashes (D1–D10 `d8c7944`; D11–D17 `fcc3c38`; no-history pre-registration `bd3ba50`; D18–D23 not yet committed). Source: deviations doc header; paper section "Pre-specification".
2. **S1 (temporal split) is partly unblinded.** Brazil, Peru and Taiwan S1 test-year results were seen before D2, D8, D9, D11, D12 and D18–D22 were decided. Every S1 statement must carry this caveat. All of these were fixed before any spatial-split (S2–S5) result was read. Source: deviations doc, last column.
3. **The baselines (L0–L2, TimesFM) were looked at on test years** during pipeline development. Source: paper "Pre-specification".

## Design changes the reader must know about
4. **One hyperparameter set per country (D2)** replaced per-level tuning *after* Brazil S1 showed a capacity confound (L3 at 127 leaves beat L3 at 31 leaves by 5–20× the embedding effect). Per-level tuning is a sensitivity analysis. Source: `docs/results/brazil_s1_estimands.md` (superseded), D2.
5. **C1 leak and fix (D1).** The first C1 (mean of the training targets) leaked each training row's target (2019 log-WIS 0.263 vs 0.175 for L3). Now C1 = pre-training-years mean. In S2–S4 C1 uses matched leave-out neighbours from pre-training years (D5, D14). Source: `docs/methods/controls.md`.
6. **C3 was not a stable ID until D13** (new permutation every year). Fixed to one permutation per seed for all years. Source: D13, `docs/methods/controls.md`.
7. **C4/C4s bug (D18).** In Colombia and Taiwan (and every S5 fold that contains them), C4 and C4s were all-NaN because 3 units without geometry broke the field construction. Their forecasts were identical to L3, so they were no-op controls; Colombia S1's chosen C\* ("C4s") was really plain L3. Fixed and rerun. The Colombia S1 2019 selection and Taiwan S1 test results had been seen. Source: `Part 1/audits/audit4_analysis_paper.md` (C1), `docs/methods/controls.md`.
8. **C\* selection rule v2 (D19).** Old rule: lowest 2019 score, no tie rule, so C\* was decided inside seed noise (CO margin 0.00003 vs seed SD 0.00006; TW exact ties broken by sort order). New rule: drop degenerate candidates, tie set within 2·SE of the best, fixed priority C1 > C3 > C2 > C4s > C4 > C5 (no-history: C3 > C2 > C6 > C4), zero seed SD = "uninformative". Adopted after S1 results, before any spatial result. Do not describe C\* as "the lowest seed-averaged score". Source: D19.
9. **C4s range = min(D, fitted) (D20).** In Peru and Taiwan C4s equals C4 and is not a candidate; before the fix it ran at D (longer range) there but never won. Source: D20.
10. **Horizons (D21).** The primary family pools h ∈ {1, 4} in every cell, including S1. S1 pooled over h1–h4 is secondary. Any table that shows S1 over h1–h4 must say so. Source: D21, `configs/primary_cells.yaml`.
11. **Seeds (D22).** Only the Brazil S1 primary cell has 3 seeds (0, 1, 2, at h1/h4); every other cell uses one seed, so its CI conditions on one fit. Seed SD (≈ 0.0001–0.0003 log-WIS) is the same order as the S1 estimates. Source: D16, D22.
12. **Scope cuts (D3, D4, D10).** S2 = 5 grouped leave-states-out folds (not leave-one-state-out); BR S3 = 5 folds; S0 dropped; spatial splits at h {1, 4}; final C\* runs at 1 seed; TimesFM hybrid, monthly arm, PDFM (L5), vintage-based reporting lag and no-history S3 deferred. Source: D3, D4, D10, `docs/methods/nohist_arm.md`.
13. **No-history arm is exploratory (D8)**, added after the S1 nulls; it uses Brazil's L1 parameters, which were tuned on a model *with* case history (audit 3 M-4). Source: `docs/methods/nohist_arm.md`.

## Inference caveats
14. **Primary inference = DM test with EWC variance + HLN; CI = d̄ ± t·SE_EWC/HLN (D11).** The 8-week bootstrap of the first Brazil report was anti-conservative; any "CI excludes 0" from it is wrong. Source: D11, `docs/results/brazil_s1_estimands.md` banner.
15. **The 52-week bootstrap is coarse.** It is a circular block bootstrap (Politis & Romano 1992) with only 4–5 blocks over 209–261 weeks, and its point estimate is the row-level mean, not the primary week-pooled mean. Treat it as a rough check only. Source: `docs/methods/eval_library.md`.
16. **"Equivalent" can coexist with "significant".** The classifier checks equivalence first, so a small but significant effect is labelled equivalent (e.g. Brazil G_emb 2021, p = .019). Always print the DM p next to the class. Source: audit 4 L1.
17. **Holm family = 14 cells**, provisional while cells are pending; `p_bonf14` is the conservative bound. Source: `scripts/run/primary_family.py`.
18. **Strata weight weeks equally.** Stratum estimates (observed / zero-filled / outbreak) give each week the same weight however many stratum rows it has; they are not shares of the overall gain (the old "~71% of the gain in outbreak weeks" is a row-level figure from a superseded report). Source: D-notes "Strata weighting", audit 4 M3.
19. **ID share is reported only if G_emb's CI excludes 0 and G_emb ≥ 1% of WIS(L3).** So far it is "not estimable" everywhere. Source: `docs/results/brazil_s1_estimands_v2.md`.

## Data and country caveats
20. **Taiwan is a thin-data stress test**, not a headline: few non-zero targets, 2021 skipped (the weekly series has a 371-day gap that EWC treats as contiguous), test years ≈ the 2023 outbreak, WIS(L3) ≈ 0.039 so the 1% margin is ≈ 0.0004. Tuning and C\* selection there are nearly uninformative. Source: `docs/data/opendengue_v1.3.1_audit.md`, audit 3 M-2, audit 4 L2.
21. **Peru is small** (115 units, 4 test years); MDE ≈ 1% of WIS, so it cannot show equivalence alone. In Peru G_emb is "inferior" (AlphaEarth slightly hurts, p = .046). Source: `docs/results/peru_s1_estimands.md`.
22. **Final revised counts, no reporting delay** (only a `report_delay: 2` sensitivity). Zero-fill is validated for Brazil and Taiwan, only at national/department level for Peru. Source: `docs/data/zero_fill_crosscheck.md`, `docs/data/completeness_v1.md`.
23. **LST:** outlier screen on for CO/PE/TW and all S5 runs, off for Brazil S1–S4, so Brazilian rows in S5 use a different LST definition than in S1–S4. Source: D7, deviations "Documented, not changed".
24. **C5 (AlphaEarth 2023 static) sees later imagery** for 2020–22 targets; this favours the control (conservative for the embedding claim). Source: audit 3 L-3.
25. **S3 buffer is on polygon centroids**, while C1/C4 use representative points; by representative points a few training units are closer than D (BR 161 vs 225 km; CO 122 vs 130 km). Source: audit 3 M-1.
26. **Yearly alignment and annual refits** (D17): small, symmetric look-ahead for January origins; `yearly_ref: origin` sensitivity. Source: D17.
27. **Units without geometry** (CO 1, TW 2; Belén de Bajirá has no polygon) are excluded from scoring by default. Source: `docs/data/completeness_v1.md`.
28. **Per-level Brazil control selection** (`runs/brazil_s1_controls_2019`) ranks pre-fix C3/C4; use it only as part of the per-level sensitivity. Source: `docs/results/brazil_s1_control_selection.md` banner.

## Cross-country (S5) outliers, verified 2026-11-17 (`docs/results/s5_outliers_verification.md`)
- **TW_S5 (−11.5% of WIS) is real, not a bug. Cause: covariate shift.** Taiwan's AlphaEarth vectors are far from every training unit (nearest-unit cosine 0.76, vs 0.98–0.99 within a country). Their nearest neighbours are hyper-endemic Colombian cities. So L4 roughly doubles the upper quantiles on Taiwan's zero-case rows (97% of its rows), and the harm appears in all 285 units. On case weeks, L4 slightly helps (+1.7%). In absolute terms the effect is −0.0028 log-WIS, about 2.3× BR_S5; the percentage looks large because WIS(ref) is small (≈0.025). Frame it as: "embeddings transfer place-specific risk levels across countries and can mislead badly out of distribution".
- **PE_S5 (+1.0%, p = .046) is fragile; do not present it as a positive finding.** It does not survive Holm. Ten Amazonian units give 76% of the gain, it comes mostly from h4, and it is partly an artefact of C3 making L3 worse (G_id −0.45%, p = .014).
