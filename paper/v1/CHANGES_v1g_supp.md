# Changes v1g, supplement (S1, S2): round-4 reviewer fixes

Binding list: `audits/final_round/TRIAGE_R4.md` (EDIT-supp items). Text edits only; no result number changed.

| Item | Status | Where / what |
|---|---|---|
| P8 | done | "historical risk" → "average past cases" in S1 Table S7 (C1 type), B1 text, Table S13 and row 38 ("district-label panel"); S2 code list, Table S17 note, Table S22 title, Table S36 note, S51 text (3 places), Table S53 row, Figure S1 caption. C6 type in Table S7 "Identifier" → "District label". No "district identifier" was left in either file. |
| P16 | done | Table S42 note: "Horizon rows give the mean over rows; pooled rows weight target weeks equally, as in the gains." Verified: horizon-1 WIS of N3 0.35196 equals the T6c row mean; the pooled row mean would be 0.3526, so the printed pooled 0.3520 is week-weighted. |
| P20 | done | Sentence deleted from the S1 opening; the preceding sentence reads on its own. |
| P21 | done | S2 G8: "close to the static covariates" → "less than the static covariates explained" (holds in all four countries). |
| P26 | done | All 19 lettered cross-references in S1 now read "Supplementary Methods, section X" (18 by pattern outside comments, plus "Supplementary Methods, section D, lists…"). S2 had one, already prefixed. |
| E13 | done | S1 E3 Conclusions: 10–22% now labelled "this earlier simulation, run before the origin-year filter"; the Table S47 sentence says it replaces the earlier simulation for the final results. S1 I (Inference): "earlier size simulations", plus one sentence giving the final-row size 14% to 18% in five comparisons (Supplementary Results, Table S47). |
| E16 | done | S1 I: "probable cases in Brazil, all reported cases as labelled by OpenDengue ("Total") in Colombia, probable and confirmed cases in Peru, and locally acquired confirmed cases by week of onset in Taiwan". `panel_weekly_v1.md` gives CO only as "Total", so the triage fallback was used. **The main-text editor should use the same wording** (02_methods still said "total cases (Colombia)" when this was written). |
| M6 | done | Heading G6 → "District-years with cases, and forecast width and coverage"; Table S48 title → "District-years with cases, and forecast width and coverage on weeks with and without cases"; closing paragraph → "On measures computed from the forecasts alone, rather than from their scores, and reported separately for weeks with and without cases, …". |
| M13 | adapted | The suggested S50 note was partly wrong. Peru's G + S (0.45) is above S (0.43), and "E over S alone was not computed" is false: the probe CSV has dR2 S+E over S. New note: Taiwan's coordinates lowered R² below S alone (0.33 vs 0.55); in Peru they raised it only slightly (0.45 vs 0.43); E over S alone also added nothing (Peru −0.11, 95% CI −0.32 to 0.03; Taiwan −0.01, −9.92 to 0.18). Also added to the G8 text: coordinates "in a tree model cannot extrapolate to states not used for fitting". |
| M22 | done | S1 A7: "Rescaling removes the length of the mean, which is shorter when a district's land cover is more varied; we did not test that length as a separate input." |
| M23 | done | Table S10, AlphaEarth row: "Could favour the embeddings". |
| M9 (consistency) | adapted | The location-control definition is repeated in the S1 opening and the glossary, so both now use the M9 wording to match the main text. |
| Caption/term sweep | done | See counts below. |
| Extra | done | E3: raw "d_t" → `$d_t$`. Row 38: "identifier gain" → "control gain". |

## Term-sweep counts (prose, captions and table notes; HTML comments untouched)
- "historical risk" → "average past cases": S1 2 (Table S7, B1), S2 10. Plus 3 "identifier" labels → "district label" (S1 Table S7 C6, Table S13, row 38).
- "district identifier": 0 found.
- "new years": 0 in visible text. Three src comments in S2 still say "new years"; they quote file labels and were left alone.
- "co-primary": 0 found.
- "cell" → "comparison": 0 in S2 visible text. S1 keeps 4 "grid cell" uses (a raster cell, a different meaning) and the glossary entry "Comparison (cell)", which defines the old name used in code and file names.
- "recorded zeros" → "zeros listed by the source": S1 2 (row 26, glossary label), S2 6 (Table S28 header and note, Table S29 header ×2, S29 note ×2).

## New numbers and their sources
- S1 I: "14% to 18%" in five comparisons. `<!-- src: R3_A8_iaaft_equivalence.csv size_nominal5 (BR_S1 .184, BR_S2 .14, BR_S3 .152, BR_S4 .149, CO_S5 .158) -->`. The same range was already in S1 E3.
- S2 Table S50 note: 0.33, 0.55, 0.45, 0.43 (from Table S50 itself); Peru −0.11 (−0.32 to 0.03) and Taiwan −0.01 (−9.92 to 0.18). `<!-- src: docs/results/review/R3_E1_info_probe.csv, T1, grouped_state, lgbm, dR2, fset S+E, base S -->`.
- Number check (visible text, before vs after): the only additions are the numbers above and "47" (the Table S47 reference). Nothing was removed or changed.
