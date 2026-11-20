# VERIFY v1e: final numeric and claim check (2026-11-20)

Scope: main text 00 to 06 (every number), supplement tables and paragraphs changed in v1e (CHANGES_v1e_supp.md) in full, and a spot-check of the rest. Sources: docs/results/tables/*.csv, docs/results/review/*.csv|md, FINAL_RESULTS_BRIEF.md, _compute_total.txt, deviations_from_protocol.md, figures/pub/CAPTIONS.md and Fig4.png. CSVs were read on the GPU with a read-only viewer (tmp/final/verify_v1e/show.py).

About 1,100 numbers checked: about 450 in the main text (incl. Tables 1 and 2, all four captions) and about 650 in the supplement (S17 to S34, S36, S37, S39 to S48, S52 to S55 in full; S5b, S12 to S14 and section I in part).

## Known source conflicts

| # | Item | Resolution |
|---|---|---|
| C1 | BR S4 zero-filled contribution: T5 −0.20 [−0.34, −0.07] vs brief −0.17 | T5 used everywhere. The only place it appears is Table S28 (already −0.20, −0.34 to −0.07; sums to +0.20). The main text does not cite it. No change needed. |
| C2 | PE S5 case-week coverage change: week-weighted +2.1 pp vs row mean +2.0 pp | Week-weighted +2.1 pp is now used everywhere (Results 3.5 text and src; Discussion 4.2 src). Table S48 and its text already said +2.1. |

## Fixes: numbers and rounding

| Location | Old → new | Source |
|---|---|---|
| Results 3.5, coverage sentence | "+2.0 percentage points" → "+2.1 percentage points"; src now diff_week_mean +2.10 (row mean +2.03 noted) | R3_A6_outcome_agnostic.csv PE_S5 cov_80 case weeks |
| Discussion 4.2 src | "PE_S5 +2.0 pp" → "+2.1 pp (week-weighted, Table S48)" | same |
| Results 3.5, Colombian district-years | "p ≤ 0.008 in three cells" → "p < 0.01 in three cells" (CO S4 p = 0.0084 > 0.008) | R3_A6 analysis a: CO_S1 .0038, CO_S2 .0040, CO_S4 .0084 |
| Discussion 4.2 src | "p ≤ 0.008" → "p < 0.01 (max 0.0084)" | same |
| Results 3.7 | Peru in-country reference WIS 0.2418 → 0.2417 (0.2418 was the seed-0 value; T1 now holds the three-seed mean); src TW_S1 0.03117 → 0.03124 | T1 WIS_L3 PE_S1 0.24171, TW_S1 0.03124 |
| S1 section E1 | "Nine cells average seeds 0 to 2" → "Ten cells" (the list itself names ten; T1 n_seeds = 3 in ten cells; Table 2 note agrees) | T1 n_seeds |
| S1 section F, first paragraph | "seen before rows 2, 8, 9, 11, 12, 16 and 18–22" → "rows 2, 8, 9, 11, 13, 16 and 18–22" (row 12 was not after results; row 13 was; Methods 2.12 already lists D13) | deviations_from_protocol.md "After seeing test results?" column |
| S1 section B1 (line 267) | "every candidate scored worse than L3 at 2019 (11 of 13 cells" → "(11 of 14 cells"; src corrected (TW S1 C3 also scored below L3) | T4_cstar_selection.csv wis_log_2019 |
| S1 section I, Calibration | "(24% in Taiwan, new years, with or without 2021)" → "(23% in Taiwan, new years; 24% without 2021)"; src range 0.614 → 0.609, TW_S1 0.231 with 2021 | T2_ladder.csv cov_80_nonzero L4+C* (TW_S1 0.231; TW_S1_no2021 0.241; TW_S5 0.609) |
| S1 section I, Countries | MDE "1.01% for new years" → "0.95%" (three seeds); src updated | T1 PE_S1 MDE_pct 0.952 |
| S1 section I, Inference | "the losses with Brazil held out and Colombia's held-out states stay significant under both checks, those for Colombia's new years and buffered blocks under one" → "the loss in Colombia's held-out states stays significant under both checks, those with Brazil held out and in Colombia's new years and buffered blocks under one (IAAFT)" (BR S5 B4 Holm p = 0.095) | T1 B4_Holm_p, p_iaaft_Holm |
| S2 Table S54 | Bold added to static history (−1.46, CI −2.90 to −0.03) and excess beyond C1 (−3.46, CI −6.13 to −0.79), per the note "Bold: CI excludes zero" | R3_C_co_s2_nohist.csv |

## Fixes: cross-references and src comments

| Location | Change | Reason |
|---|---|---|
| Results 3.8, both Brazil paragraphs | Added "Tables S41 and S42" / "Table S42" | Supplement now holds the Brazil held-out-states no-history results in S41/S42 (flagged as open in CHANGES_v1e.md) |
| Results 3.5, outbreak src | "CI above zero: BR_S5, PE_S5" → "outbreak CI above zero: PE_S5, TW_S5" | S3_outbreak.csv (BR_S5 outbreak CI −0.07 to 1.08; TW_S5 0.21 to 2.44). Text unaffected. |

## Claim-strength changes (smallest wording change)

| Location | Old → new | Evidence |
|---|---|---|
| Results 3.9 | "in Peru and Taiwan the added R² was negative or near zero with wide intervals" → "in Peru and Taiwan the added R² (−0.07 and +0.07) had wide intervals that included zero" | Taiwan +0.070 is seven times Brazil's +0.010; not "near zero" (R3_E1 T1 LightGBM) |
| Discussion 4.1 | "(added R² about 0.01; Section 3.9)" → "(added R² about 0.01 in Brazil and Colombia; Section 3.9)" | same |
| S2 text after Table S30 | "The largest yearly estimate was Brazil, new years, in 2024" → "The largest yearly estimate in Brazil was new years in 2024" | PE S5 was +1.31, +1.40, +1.11 in 2020 to 2022 (R3_A3_per_year.csv) |
| S2 text after Table S53 | "Every model forecast Taiwan about 57% better than the seasonal naive" → "Every LightGBM model ..." | NB relative WIS 0.64 |
| S2 text after Table S53 | "All four fixed controls gave a negative excess gain, none significant" → "..., nominally significant only with C1 (p = 0.049)" | Panel B C1 −0.60 (−1.20 to −0.003); p 0.049 |
| S2 text after Table S42 | "The significant coordinate gain of the new-years cell (+3.30%) therefore did not carry over to states ..." → "... was therefore not detected in states ..." | BR S2 no-history G_id +0.88 (−0.48 to 2.23): an undetected effect, not shown absent |
| S1 section I, Countries | "Peru ... cannot show equivalence at ±1%" → "did not show equivalence" | With three seeds PE S1 MDE is 0.95% < 1% |

## Checked and correct (selected)

- Abstract and Results: six Holm losses (BR S5, CO S1 to S4, TW S5); five small −0.42% to −0.68%; TW S5 −18.29% (abs −0.00369); only CO S2 below 0.05 under both B4 Holm (0.022) and IAAFT Holm (0.007); IAAFT Holm significant: BR S5, CO S1, CO S2, CO S3; PE S5 IAAFT Holm 0.04998, B4 Holm 0.18; equivalence ±1% 9 / 8 / 5 (B4 + Holm); ±0.5% 2 / 2, none under B4 + Holm; BR S2 no-history all inconclusive.
- Table 2: every row (C\*, %, CI, absolute ×10⁻⁴, Holm p, G_emb, conclusion), † (BR S1, CO S5) and ‡ (CO S2 to S5, PE S5, TW S5) flags.
- Table 1: districts, scored districts (5,439 + 1,070 + 115 + 285 = 6,909), rows, weeks, zero shares 73/79/56/98.
- Sections 3.3 to 3.9: margins 0.92 / 2.26 / 5.03; no-control rule Holm values; per-horizon CIs; delta-method CIs; seed SDs 0.03% to 0.12% (TW S5 1.12%); planned-settings values; strata counts (zero-filled 14/14, CI 12; case weeks 12/14, CI above zero CO S5 and PE S5); q90 14/14 (CI 13), 0.002 to 0.093, ≥63%; width +1.6% to +12.3%, TW S5 +55%, 13 significant; trend smallest scaled p 0.096; 2023 to 2024 values; control panel (16 cells, C6 −2.11 to −6.28); C3 vs real embedding costs 0.12 to 0.76 vs 0.36 to 1.06; similarity quintiles 0.70 to 0.82 vs 0.95 to 0.99; Spearman −0.25; stability 0.982/0.978 vs 0.974/0.971; all no-history numbers (T6b, FINAL C1 rung, RH, R3_C_co_s2_nohist); info probe R²; variants (28 tests, max +0.15%; V3 Holm 0.032); tuning −0.39%.
- Discussion: "one-third to four-fifths" (0.34 / 0.81 / 0.55); per-level tuning ratio 7.6 (0.00327/0.00043); size 14% to 18% in five cells, 1% to 9% in loss cells; upper bounds +0.79, +0.71, +2.02.
- Methods: compute 4,662.1 → "about 4,700"; df 16/11/13/16; D-code counts in 2.12 (11 of D1 to D23 after new-years results; matches the deviation log).
- Supplement S17 to S27, S30, S31, S33, S34, S36, S37, S40 to S48, S52, S53, S55: every regenerated value checked against its CSV; S21 and S26 every cell.
- Figure captions match CAPTIONS.md in substance; Fig 4 (PNG viewed) shows S1 and S2, as the caption says. All cited Tables S1 to S55 and Figures S1 to S4 exist; section cross-references (2.7, 2.10 to 2.13, 3.1 to 3.9, S1 sections A4, B, C, D3, E to I) point to the right content.

## Open judgment items (not edited)

1. Abstract: "added about 0.01 to coordinates and static covariates" holds for Brazil and Colombia only (Peru −0.07, Taiwan +0.07, wide CIs). A fix ("about 0.01 in Brazil and Colombia") adds four words to a 300-word abstract. Same issue in Discussion 4.1 "in these four countries it is redundant" and Interpretation "it duplicates coordinates and standard covariates".
2. Discussion 4.1 "predicted ... about as well as standard covariates": E vs S R² is 0.49 vs 0.65 (BR), 0.52 vs 0.66, 0.24 vs 0.43, 0.45 vs 0.55. Results 3.9 says "close to". Consider "somewhat less well than".
3. Methods 2.12 "Eight post-result changes ... three seeds ... where they exist, in other cells (D49)": the change that made the seed mean primary is D53, not D49. Citing D53 would change the count of eight.
4. Results 3.4 "Restoring the planned settings left the Brazilian and Colombian conclusions unchanged": BR S3 becomes nominally significant (p = 0.045) under exclusions v1; true only for Holm-based conclusions.
5. Results 3.9 "Embeddings in place of the remote-sensing and population block were worse than that block in all four cells": Taiwan's difference is not significant (−0.79, p = 0.11).
6. Results 3.8 / S42: "Static history changed WIS by −0.24%" uses the gain sign convention (negative = worse). It is correct but easy to misread as an improvement.
7. Results 3.1 "The full model changed this ratio by at most 0.01": Taiwan moves 0.425 → 0.4355 (0.0105), which rounds to 0.01.
8. Table S19/S20 four-decimal rounding of half-way values (e.g. BR S4 L4 0.16795 shown 0.1679 in S19 and 0.1680 in S20 for L4 + C\*) is within float noise; not changed.
9. Deviation row 40 (S14) still says "11 of 13 cells": left as the record at specification time.
