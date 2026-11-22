# CHANGES v1g (main text, 00–06): round-4 reviewer fixes

Binding source: `audits/final_round/TRIAGE_R4.md` ("FIX: main text" and "FIX: ML referee items"). Supplement files were not touched.

## Word counts (method as in v1d/v1f: HTML comments, equations, tables, captions, table notes, headings and citation keys excluded)

- Abstract (Background to Interpretation, labels included, keywords excluded): 300 before, 300 after.
- Main text (Introduction + Methods + Results + Discussion): 6,339 before, **7,019 after** (Intro 860→826, Methods 2,592→2,682, Results 1,725→1,853, Discussion 1,162→1,658).
- The ~6,600 target was NOT met. The triage additions came to about 950 words; trimming removed about 270. Further cuts would remove content (Results 3.8/3.9 detail, 4.2 mechanism, 2.12 disclosures), so they were left to the supervisor/authors.
- Trims made: Intro location-encoder sentence (refs still cited in 4.5) and the "Models added one block…" sentence (repeats Methods 2.4); Methods 2.13 list of variants (now points to 3.9); Results Brazil held-out-districts sentence (Table 2 row), "Brazil's excess gain smaller than its climate gain" (Table S44), duplicate "labelling pattern" sentence (merged into one in 3.8), baseline ratios for NB/TimesFM (Table S17); Discussion "Peru and Taiwan R² too uncertain", case-week coverage clause in 4.2, Colombia no-history sentence in 4.3 (in 3.8), MOSAIKS clause in 4.4, "no gain whose source needed explaining" in 4.7, Peru clause in 4.2 tree-size paragraph (kept in 4.5).

## Items

Abstract (00_front)
- E5/P3: done ("comparison(s)" everywhere; Methods sentence as specified).
- P4: done ("5 under the strict-variance check").
- P5: abstract "under the main test" skipped (word budget); 3.2 now prints 0.050 (2,000 surrogates; within Monte Carlo error of 0.05). 0.04998 removed from main text.
- E6/M5: adapted. Used M5's short form "With Taiwan held out, embeddings increased error, but not robustly." (E6's longer form did not fit 300 words; checked T1 TW_S5 B4_Holm_p 0.27, p_iaaft_Holm 0.29.)
- E21: done.
- E20/P18: skipped (word budget); "test years" and the WIS gloss did not fit.
- M1: done, adapted to "climate, remote-sensing and population covariates already carried most of it".
- M8: done ("known covariates were detectable only in Brazil and, partly, Colombia"; verified Table S44: Colombia RS/pop step only, p = 0.034).
- M17: done (held-out states, the main design, first; verified 2.11 calls it the main design).
- Trims to fit: Colombia held-out-states CI (−0.74 to −0.30) removed from abstract (in Table 2); R² range 0.24–0.52 removed (in Table S50 and 3.9); "leaving no gain to attribute" and "Exploratory analyses omitted case history" removed ("(exploratory)" added to the no-history sentence).

Introduction
- E12: done (lowe2016elife; colongonzalez2021vietnam for climate/environment; harish2024movement for movement).
- E2: left (author decision; `[to be completed]` slots unchanged).
- M9: done (location-control definition). It is defined only in the Introduction; Methods 2.5 refers to it.
- M18 (replaces P27): done in Intro ("For two other outcomes, malaria and respiratory infection…"; "We found no control … and no spatial hold-out") and 4.4 ("malaria and respiratory infection").

Methods
- E3: done (2.2: "OpenDengue has almost no rows for this state after 2019, so our zero-filling would create false zeros there…"; matches Supplementary Methods A6; 4.5: "The zeros we filled for Espírito Santo remain in the training targets.").
- E4: done in 3.2 (rough guide, anchors Peru future years 0.0020 and Taiwan held out 0.0037, about 60% cut from case history).
- E9: done ("Districts that never reported a case are not forecast, and 565 districts first reported in 2018 or later"; Supplementary Methods, section I). No province/township totals added.
- E16: done. Table 1 note: probable cases (Brazil); all reported cases, as labelled by OpenDengue (Colombia); probable and confirmed cases (Peru); locally acquired confirmed cases by week of onset (Taiwan). Colombia wording follows the coordinator's instruction.
- E22/P25: done ("(Table S38; change to the plan in Table S14)").
- E24: done (2.3).
- P6/M21: done. "five kinds of location control … plus a 2023 embedding snapshot as a sixth candidate (Table S7). We call the control selected for a comparison C\*." Consistent with Table S7 (C1–C6 + C4s variant) and the Figure 1 caption.
- P7: done.
- P17/M20: done, adapted to match Table 2's Labels note. Text: equivalent when both one-sided tests reject after Holm adjustment over 14 comparisons; "Without adjustment, this is the same as the 90% CI … inside ±1%"; Table 2 marks before-adjustment-only. (M20's "that is" would have equated the Holm test with the unadjusted CI, which is not exact.)
- P24: done ("results in Table S26; their calibration in Table S12"; both verified).
- M3: done in 2.5, in the Table 2 \* note and in 4.2.
- M16: done (verified Supplementary Methods C).
- E8 (2.2 part): done ("supported this at district level in Brazil and Taiwan. In Colombia and Peru, only national or department totals could be checked"; verified A4).
- P26: checked; all lettered cross-references in 00–06 already read "Supplementary Methods, section X".
- M6 wording also applied to 2.8 and 2.13 ("measures computed from the forecasts alone").
- Figure 1 caption: "primary scores/scoring/estimates" changed to neutral wording; checked for "historical risk", "district identifier", "new years", "co-primary", "recorded zeros", "cell" (none in 00–06 captions).

Results
- P10: done (3.1 now cites Table S20 for both ranges, "Across all comparisons, the 80% intervals of the full model…"; values 0.83–0.99 and 0.61–0.75, TW S1 0.23 verified in Table S20).
- P12: done in 3.6 and 4.4 ("(seed 0)").
- P13: done (Peru and Taiwan only; Brazil and Colombia worse, Table S21).
- P15: done ("target weeks weighted equally; Figure 4B; Tables S41 and S42").
- P19: adapted (gives 2020 −0.22% and 2021 −0.67%, cites Table S30).
- P21: already "less than" in 3.9; no change needed.
- M6: done (3.5).
- M10: done, adapted ("usually": C1 is selected in 10 of 14 comparisons).
- M13: done (3.9; R² −0.38 to 0.06 verified in Table S50).
- 3.6 real vs shuffled (M experiment item 2): done (Brazil +0.29% vs −0.04%, Table S36; existing Colombia/Peru/Taiwan sentence kept; "We did not test these differences.").

Discussion
- E7: done, adapted (4.5; delay sensitivity +0.60%, 95% CI −0.56 to 1.76, Table S37). The parenthetical about Brazilian notification lags was not added (no source in the repo).
- E8: done (4.5).
- E10: done (4.5; 61–75%, 23%).
- E11: done, UNCITED. No Taiwan dengue-epidemiology reference exists in refs_v1.bib. **Authors to confirm or cite.**
- E13/P14: done (4.5: 14–18% on final rows, Table S47; earlier simulation 10–22%, Table S12).
- E15: done (4.5).
- E18: done (4.6, exact triage text).
- E23/P22: done.
- P11: done ("(Supplementary Methods, section C)").
- M1: done in 4.1 and 4.7.
- M2: done (4.3 counter-evidence: Tables S36, S22, S49, all verified; 4.7 sentence replaced).
- M4: done, condensed (4.5). Adapted "Only Colombia's future years were checked with separate tuning of both models" to "Only Colombia's future years were tuned on a wider grid for both models", because per-level tuning also exists for Brazil, Peru and Taiwan (Table S43).
- M7: done (two sentences).
- M11: done.
- M12: done.
- M14: done (4.5; kNN-risk and PCA-8 results are in Section 3.9).
- M15: done (4.2 now opens with the zero-filled / Colombian district-years fact, Table S48).
- M24: done, merged with E24 (4.5).
- 4.3 limitation "no shuffled-embedding run in the test years": done. 4.2 "We did not test embeddings centred within each country…": done.
- Consistency (beyond triage): 4.7 "Embeddings may worsen forecasts for a country whose surveillance differs…" changed to "With Taiwan held out, whose case definition differs from that of the training countries, embeddings worsened forecasts, though not robustly." This matches the abstract (M5/E6).

Declarations
- E17: done ("The Taiwan CDC file is a public open-government dataset without names or other direct identifiers."). Kept "build and check" (existing). **Authors to confirm** (AUTHORS comment added).
- E1/P2: left; `[to be completed]`, AUTHORS comments and `<!-- AI-USE -->` unchanged.

## New numbers in main-text prose (all with src comments)

- 02 Table 1 note: 565 districts first reported in 2018 or later (S1_supplement_methods.md section I).
- 02 2.4: 127 leaves for held-out-country models (S1_supplement_methods.md section C "Tuning").
- 03 3.2: 0.002 and 0.2% (illustrative conversion given in TRIAGE_R4 E4; exp(0.002) − 1); 0.0020 (T1 G_excess PE_S1 −0.00197; Table 2 −19.7 × 10⁻⁴); roughly 60% (TRIAGE E4; from 3.1 ratios 0.36–0.43, S1_baselines.csv); 0.050, 2,000 surrogates, 0.05 (TRIAGE P5; T1 PE_S5 p_iaaft_Holm 0.04998).
- 03 3.5: −0.22% in 2020 (Table S30; S8_per_year.csv BR_S1).
- 03 3.6: −0.04% (Table S36; S2_control_panel.csv brazil C3 G_id_pct).
- 03 3.7: 0.1907 vs 0.1675, 0.1240 vs 0.1222 (Table S21; T1 WIS_ref BR_S5, BR_S1, CO_S5, CO_S1).
- 05 4.5: +0.60% (95% CI −0.56 to 1.76) (Table S37; T6a_sensitivities.csv); 10% to 22% (Table S12); 61% to 75% and 23% (Table S20; repeated from 3.1).

## Numbers removed from main-text prose (all remain in a table)

- Abstract: Colombia held-out-states CI −0.74 to −0.30 (Table 2); R² 0.24 to 0.52 (Table S50; range still in 3.9).
- 3.1: NB 0.44 to 0.64 and TimesFM 0.41 (Table S17).
- 3.2: 0.04998 replaced by 0.050 (per triage).
- 3.3: Brazil excess gain +0.23% beside climate gain (Table 2, Table S44).
- 3.9: individual R² 49%, 52%, 24%, 45% replaced by "24% to 52%" (Table S50).
