# CHANGES v1e: final fill pass (2026-11-20)

Files edited: 00_front.md, 02_methods.md, 03_results.md, 05_discussion.md. 01_introduction.md and 06_declarations.md needed no change (no markers, no result-dependent wording). Supplement files were not touched.

Sources: docs/results/FINAL_RESULTS_BRIEF.md (binding), docs/results/tables/*.csv (final kit, 3-seed means, Holm m = 14), docs/results/review/R3_*.csv (rerun on 14 cells), RE_control_panel.csv, FINAL_br_nohist_C1_rung.csv, T6b/T6c, pub/CAPTIONS.md (2026-11-20), paper/v1/_compute_total.txt. Every new number has a `<!-- src: -->` comment.

Word counts (same method as v1d: HTML comments, equations, tables, captions, table notes and headings excluded): abstract 300 (labels included); main text 6,328 (Introduction 785, Methods 2,542, Results 1,808, Discussion 1,193), against 6,299 in v1d.

Markers left: none (`[pending]`, `PENDING`, `REVISIT` all removed). `[to be completed]` + `<!-- AUTHORS -->` and the `<!-- AI-USE -->` slot are untouched.

## 00_front.md (Abstract, Findings)
- "In 13 completed combinations, no gain survived correction [pending]" → "No gain survived correction in 14 combinations." (T1 Holm_p, m = 14)
- New: six losses, five small (−0.42% to −0.68%) and Taiwan held out −18.3% (absolute −0.0037). Old: Taiwan −17.3%, absolute −0.0035. (T1 pct_of_WIS_ref, G_excess)
- CO S2: −0.47% (−0.69 to −0.25) → −0.52% (−0.74 to −0.30); "robust to cautious variance estimators, dropping the control and seed choice" → "Only Colombia's held-out states ... survived both cautious variance estimators" (it is the only cell significant under B=4 + Holm; case-scale CO S2 is p .15, so "every robustness check" was avoided). (T1 B4_Holm_p .022, p_iaaft_Holm .007)
- Equivalence: "8 of 13, 6 with cautious variances" → "8 combinations (5 with cautious variances)". (T1b; R3_A4)
- q90 src 13/13 → 14/14.
- No-history sentence: added Brazil held-out states ("nothing was detected"); BR new-years wording kept. (T6b BR_S2_nohist)
- Abstract count comment now points to this file.

## 02_methods.md
- 2.4: "[pending] core-hours" → "about 4,700 core-hours" (src `_compute_total.txt`, 4,662.1 exact).
- 2.10: removed "Until Brazil held-out districts is released, Holm values are over the 13 completed cells [pending]" (family complete, m = 14).
- 2.12: D25 effect labelled "seed-0" (−11.2% → −17.3%; −0.44% → −0.60%); src changed to R3_C_seeds.csv T1_seed0_pct, because T1 now holds three-seed values (−18.29, −0.71).

## 03_results.md
- Header comment: final kit, three-seed means, m = 14; REVISIT note removed.
- 3.1: Colombia RS/pop CI 0.01–0.59 → 0.03–0.57 (p .034) (R3_A1); Taiwan case-week coverage 24% → 23% (T2_ladder TW_S1 L4+C*, with 2021); case-week range low end TW S5 0.614 → 0.609 (still "61%"); src now S1_baselines/T2 (TW includes 2021). Cut "Design sensitivity is thus shown only in Brazil and partly in Colombia" (repeated in 4.1).
- 3.2: "No completed cell ... [pending]" → "No cell ... over the 14 cells". "six of the 13 completed cells" → "six of the 14 cells". CO S2 → −0.52% (−0.74 to −0.30), now "the only loss that stayed significant under both cautious variance estimators" (old text said Brazil held out was also robust to both; FALSE now, B=4 Holm .095). BR S5 −0.60% (−0.84 to −0.36) → −0.68% (−0.94 to −0.42); no-control G_emb −0.34% (−1.24 to 0.56; p .44) → −0.39% (−1.34 to 0.55; p .39). TW S5 −17.30% (−27.03 to −7.57), absolute −0.0035 → −18.29%, absolute −0.0037 (CI in Table 2). New sentence on BR S4 (+0.20%, −0.32 to 0.71; Holm 1.00; equivalent). PE S5 +0.96% (−0.13 to 2.05; p .079; Holm .39) → +0.93% (−0.16 to 2.02; p .088; Holm .53), plus a plain statement: IAAFT Holm p 0.04998, B=4 Holm 0.18.
- Table 2: every row from final T1. BR S4 row filled (C1; +0.20 (−0.32 to 0.71); +3.3; 1.00; +0.22 (−0.32 to 0.76); no significant difference, within ±1%). Holm values over m = 14 (BR S1 0.80 → 1.00; BR S3 0.39 → 0.53; CO S5 0.80 → 1.00; etc.). Conclusion changes: BR S5 "within ±1%" → "within ±1% unadjusted only" (TOST_class_Holm inferior); CO S3 "within ±1% unadjusted only" → "not shown within ±1%" (TOST inferior both ways). § mark added: PE S5 and TW S5 embedding gains are seed 0.
- Table 2 note: Holm over 14 cells; seeds 0–2 where they exist (all cells except BR S2–S4 and CO S5; Table S52); Taiwan-without-2021 values labelled seed 0; added definition of "not shown within ±1%".
- Figure 2 caption: "over the 13 completed cells" → "over all 14 cells"; −17.3% (−0.0035) → −18.3% (−0.0037); "Brazil held-out districts is pending" removed (CAPTIONS.md 2026-11-20).
- 3.3: equivalence 9/13 and 8/13 → 9/14 and 8/14; B=4 + Holm 6 → 5 cells; "Four of those six (BR S5; CO S1, S2, S4)" → "Three of those five (CO S1, S2, S4)". Margin ratio Peru 5.8 → 5.0 (R3_A1 margin1_over_L1L3_gain 5.03). No-control rule: Holm 0.001–0.046 → <0.001–0.035; TW S5 0.004 → 0.005; BR S5 value added (−0.39%, p .39).
- 3.4: "two stayed significant under both tests (BR S5; CO S2), two under one, two under neither" → "one under both (CO S2), three under the surrogate test only (BR S5, CO S1, CO S3), two under neither (CO S4, TW S5)". Case scale negative 12/13 → 13/14. Seed paragraph rewritten (three-seed means are now primary; seed SD 0.03–0.12%, TW S5 1.1%). Planned-settings paragraph: PE S1 per-level −0.70 → −0.82 to +0.65; PE S5 B=4 +0.96 (0.22–1.70) → +0.93 (0.25–1.62); PE S5 all rows "p < 0.05 (+1.01%)" → "p = 0.051 (+0.99%)" (R3_A5 all rows p .0505: no longer below 0.05). Cut the BR S3 exclusions-v1 sentence (in Table S43).
- 3.5: zero-filled negative 13/13, CI 11 → 14/14, CI 12; case weeks positive 12/13 → 12/14 (PE S1 and TW S1 negative); CI above zero "three held-out-country cells other than Taiwan" → "only with Colombia or Peru held out" (BR S5 lower bound now −0.08). q90: 13 cells, CI 12, +0.002 to +0.099, ≥65% → 14 cells, CI 13, +0.002 to +0.093, ≥63%. Zero-week widening 12/13 (2–14%; TW S5 61%) → 14/14 (2–12%; TW S5 55%; significant in 13). PE S5 case-week coverage +2.4 → +2.0 pp. Colombian case district-years −0.28 to −0.30 (p ≤ .016) → −0.29 to −0.33 (p ≤ .008), "half to two-thirds" → "about half to four-fifths"; TW S5 −17.3 → −3.4 became −18.3 → −3.3. 2023–24 src now R3_A3_per_year.csv (BR S4 +0.61, p .20 added to src).
- 3.6: "[pending]" for Brazil C3/C6 filled; paragraph rewritten: no excess gain in 16 panel cells has a CI above zero; Brazil +0.02% (C2) and +0.25% to +0.30% (C1, C3, C6; p ≥ 0.15) vs +0.29% without a control; identifier hurts in all four countries (−2.11% to −6.28%; TW n.s.).
- 3.7: Taiwan Spearman −0.13 → −0.25 ("regardless of similarity" → "similarity did not protect them: the most similar fifth lost most"; S7/S7b). Cut the own-next-year-match sentence (Table S49 keeps it).
- 3.8: "[pending]" filled with a Brazil held-out-states paragraph (T6b BR_S2_nohist: C2 +0.88 [−0.48, 2.23] p .19; G_emb +1.52 [−1.27, 4.32] p .27; G_excess −0.01 [−1.28, 1.27], MDE 1.80; static history −0.24, beyond it +1.85; pattern not met). Colombia paragraph moved after it.
- 3.9: CO S1 variant baseline −0.36% and tuning −0.39% labelled seed 0; cut the similarity-vs-historical-risk clause and the V4 parenthetical (both in Table S51).
- Figure 4 caption: now covers both splits (CAPTIONS.md 2026-11-20); "Brazil held-out states will be added" removed.

## 05_discussion.md
- Header comment: m = 14, three-seed means; REVISIT note removed.
- 4.1: "[pending]" removed; "in any of the 14 cells". Loss sentence rewritten: only CO S2 survived both cautious variance estimators and the no-control rule (old text implied BR S5 survived one but needed a noise control; still true but folded into "the others depended on the control or the estimator"). Taiwan absolute 0.0035 → 0.0037. Equivalence "6 to 8 of 13" → "5 to 8 of 14".
- 4.2: "widened zero-week intervals in 12 of 13" → "in all 14"; PE S5 +2.4 → +2.0 pp (src); CO case district-years p ≤ 0.016 → 0.008 (src); TW S5 q90 0.099 → 0.093; "regardless of" → "whatever its embedding distance" (Spearman now −0.25); src −17.3/−3.36 → −18.3/−3.28.
- 4.3: rewritten with BR S2 without case history: no detectable gain from coordinates or embeddings in held-out states, wide intervals (MDE 1.8%); "consistent with" location-label wording kept (TRIAGE A.1: never "fits"); pre-specified criterion met in neither split. "[pending]" removed.
- 4.5: size inflation "in four cells, though conservative in the cells with losses" → "in five cells (adds BR S4 14.9%) and near nominal (1% to 9%) in the loss cells that were checked" (R3_A8: CO S1 8.7%, CO S4 7.35% with three-seed series, so "conservative" no longer holds). COVID/training-length limitation shortened.
- 4.6: upper bounds +0.79% (BR S1) and +2.05% → +2.02% (PE S5); added BR S4 +0.71%.
- 4.7: "8 of 13 cells, or 6" → "8 of 14 cells, or 5"; no-history sentence → "results differed between splits and countries; they are consistent with, but do not establish, a location proxy".

## Claims weakened
- Brazil held out is no longer described as robust to the variance estimators (only IAAFT + Holm).
- Colombia held-out regions is no longer "within ±1% unadjusted".
- Peru held out on all rows is no longer p < 0.05 (p = 0.051).
- The primary test is no longer called "conservative in the loss cells" (near nominal, 1% to 9%).
- Taiwan held-out harm: similarity did not protect districts (most similar fifth lost most), rather than "regardless".

## Unresolved / for the supervisor
- FINAL_RESULTS_BRIEF lists the PE S5 IAAFT Holm p as ".0500 (=.04998)" and says "BR S5 survives IAAFT + Holm (.007)"; the text reports 0.04998 plainly, without calling it significant or not.
- Table S numbers for Brazil held-out states without case history: no supplementary table existed when this pass ran (Tables S41/S42 are Brazil new years only), so the text cites Figure 4 and T6b via src comments only. If the supplement agent adds a table, add its number to Results 3.8.
- Main text is 6,328 words, 28 over the ~6,300 target.
