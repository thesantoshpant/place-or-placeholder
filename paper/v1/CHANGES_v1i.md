# Changes in draft v1i (co-author comments on draft v1.3; zero-fill stress test)

Date: 2026-11-22. Base: commit 40d7faf (paper text as in c25257c). Plan: `audits/final_round/C5_final_plan.md` (105 edits, each matched exactly once). Word counts (project counter): abstract 300, main text 7,519 (limit 7,520). The text of every changed paragraph is in `audits/final_round/changed_text_v1i.md`.

## By comment

- **C01** New title: "Place or placeholder? AlphaEarth satellite embeddings did not detectably improve weekly dengue forecasts in four countries" (front matter; also `paper/README.md`, `paper/main.tex` and STYLE_DECISIONS section 1, which keeps the earlier title). The authors must approve it.
- **C02–C08, C29** Abstract: "district recognition"; 14 comparisons across future years and held-out places; a plain gloss for "location control"; "two stricter checks"; equivalence sentence with "the stricter checks"; probe result as "added little", labelled exploratory.
- **C09–C14** Introduction: the identity confound explained with an example; what case history and held-out places do and do not remove; the Indian-city study named.
- **C15–C22** Methods: forecast origin with an example; the ladder in one sentence; purpose of the location controls; spherical harmonics glossed; why the rule always picks a control; held-out districts "unseen but not information-free"; the sign rule ("loss") stated once; the excess gain in plain words.
- **C05, C35** Methods 2.10: one plain clause for the Diebold–Mariano test; the drift weakness flagged; Results 3.3 says the surrogate check was not Holm-adjusted; Discussion 4.5 sets out the inflated size; the conclusion leads with the comparisons that pass every check.
- **C23** Zero-filling: validation numbers in 2.2 (Brazil 2.1% maximum, Taiwan exact, Colombia and Peru totals only); stress test in 2.10, 3.5, 4.5, Table S13, Table S14 row 54, Table S56 and deviation row 54 (see R5 below).
- **C25–C27** Results 3.2: direct opening; "meaning that the embeddings increased forecast error"; Table 2 reordered (conclusion second, selected control last; no value changed) with a note that a comparison can be both a small loss and within ±1%.
- **C28** Figure 2: bold "embeddings help" / "embeddings hurt" labels either side of the zero line; axis title "Gain from embeddings (% of the reference model's WIS)" (see Figure below).
- **C30, C31** 4.1: what earlier dengue evaluations lacked and what this study adds; why non-case inputs have little room at 1–4 weeks.
- **C32–C34** 4.2 and 4.3: hedged mechanisms; Taiwan held out as a stress test; the no-history result "may have worked partly as a placeholder".
- **C36, C24** 4.6 in three paragraphs: scale in case terms against case history, plain advice for programmes, interval coverage for preparedness.
- **C37–C41** 4.7: plain conclusion, equivalence counts (8 under the main test, 5 of these under both stricter checks), test advice.
- **D1–D14** The direct Doc edits (D9 is a Doc revert with no source change).
- **Cuts** (word budget; every number cut stays in a table or another section): see C5_final_plan.md section 4.

## R5 zero-fill stress test (fill-in; docs/results/review/R5_zero_fill_stress.md and .csv, commit 40d7faf)

- 3.5: at Brazil's 2.1%, the six losses shrank by 13% to 22% (exact 12.5% to 22.0%); after Holm correction only the losses with Brazil held out and in Colombia's held-out states stayed significant in every draw; at 10% none did; no comparison became a significant gain. Version (b) and the PENDING-ALT note removed.
- 4.5: "probably overstated" became "may be overstated", with the two-of-six result (scored weeks only).
- 4.1: one sentence: the losses may partly reflect cases hidden by zero-filling (Table S56).
- Abstract: only Colombia's held-out-states loss stayed significant under two stricter checks "and a test for missed cases"; five small cuts keep the abstract at 300 words, and no number changed.
- 2.10: design confirmed against the R5 report; the PENDING note became a source comment.
- Table S56 built (six loss comparisons; excess gain as reported, medians at 2.1% and 10%, Holm-significant draws at 2.1%, tipping shares), with a design note checked against the R5 report, a reading paragraph and a pointer to the CSV.
- Table S13 status "Done"; Table S14 row 54 and the deviations log row 54 carry commit 40d7faf (specification and results in one commit, so not "specified before scoring"); "Tables S17 to S56" in the Supplementary Methods introduction.
- Word budget: Section 3.5 trimmed (shorter lead sentence, CIs in parentheses, "with cases", the "half to four-fifths" aside dropped; its numbers remain in the sentence and Table S48), plus one shorter clause in 4.5.

## Figure

`scripts/paper/make_pub_figures.py`: `x_cues()` gains `color`, `weight` and `at_zero` (defaults leave Figures 3, 4 and S1 unchanged); `fig2()` uses one bold call anchored at zero, the new axis title and slightly larger bottom margins. Only Fig2.png and Fig2.pdf changed; all other figure PNGs are bit-identical.

## Checks

- Number check against c25257c: every new number is an R5 value, a Table 2 value repeated in Table S56, an R5 design value, the commit 40d7faf and its date, or a number from the C5 plan (section references, ±1%, 60%, 0.2%, row 54).
- No `[pending` or `PENDING` markers remain except the three EPIFORGE "Pending:" cells; author markers unchanged.
- PDFs: main 26 pages, supplement 66 pages; no overfull boxes, missing glyphs or undefined references. Word build: 64 tables, 8 figures, 63 references.

## Tone pass

Base: 99cec1a. Inputs: `audits/final_round/TONE_{opus,fable,sonnet,haiku}_v1i.md` (O, F, S, H plus issue number below), STYLE_DECISIONS.md, TRIAGE_R4.md "Do not break" (all kept: ‡ and \* markers, 2.12 bullets, Tables S43, S44 and S48A, absolute values next to −18%, "the null results in Peru and Taiwan say little"). Word counts (project counter): abstract 300 (was 300), main text 7,517 (was 7,519; limit 7,520). No em dashes in main prose.

### Naming: the hidden-case check
- The R5 zero-fill analysis is now called "the hidden-case check" everywhere it is named: Methods 2.10, Results 3.5 (own paragraph, with a plain definition and "a draw is one random choice of which weeks hide cases"), Discussion 4.5 (one clause), S1 Table S13 row, S1 row-54 bullet and Table S14 row 54, S2 section G14 heading and text (draw defined), Table S56 title. "Stress test" now refers only to Taiwan held out (4.2) and, in the supplement, to the IAAFT simulation.
- Abstract: "a test for missed cases" became "a check for cases hidden in zero-filled weeks" (O3, F1, S18).

### Priority edits
- Dense paragraphs split. 3.2 (O8, F17, S9, H5): robustness breakdown kept only in 3.4; the Colombia sentence now points to 3.4; the Brazil-held-out sentence names the estimate ("the embedding gain in this comparison ... Table 2"); "Monte Carlo error" became "too close to 0.05 to call given simulation error"; Peru held out is its own paragraph. 3.5 (O4, O5, F3, F4, S1, S2, H9): signpost opener deleted; "They" became "The embeddings"; "case-week coverage" rewritten; the Colombia and Taiwan district-years sentences moved to the strata paragraph; the hidden-case check has its own paragraph ("two stayed significant in every draw: the loss with Brazil held out and the loss in Colombia's held-out states"). 3.9 (O15, F16, S20, H16): split in two; negative R² explained; "cannot extrapolate" became "cannot carry coordinates over to states it has not seen"; "transferred weakly" became "predicted burden poorly across countries". 4.2 Taiwan (O6, F8, S7, H4): split at "One possible explanation"; "township" became "district"; the shuffled-embedding sentence simplified. 4.5 (O16, F15, S6, H3): reporting and zero-fill limitations are now separate paragraphs; "These were checked" has a subject; Espírito Santo sentence says the false zeros from our zero-filling were removed from scoring but remain in training targets.
- Repetition cut (supervisor item 3): the hidden-case result now appears in full in 3.5, in one clause in the abstract and in one clause in 4.5 (the 4.1 sentence was deleted). The robustness breakdown is told once (3.4). The triple "we found no location-only control" in the Introduction is one sentence (O9). "The Colombian loss persisted in district-years with cases" now appears in 3.5 and 4.2 only. The 4.2 and 4.5 tuning remarks no longer repeat each other.
- 4.6: "control decisions" became "vector-control or clinical decisions" (O7, H); second "roughly" became "about"; "upper 95% bounds" became "the upper ends of the 95% CIs"; "in case terms" rephrased here and in 3.2 (F).
- Abstract: circular "That is roughly Brazil's gain ... which helped detectably only in Brazil" became "roughly the combined gain from all non-case inputs in Brazil, the only country where all of them helped detectably" (O2, H1); losses sentence uses a colon (F2); "numbers summarising places" in parentheses (O20, F20); "Such features" became "Embeddings" (F20, H12); interpretation sentence shortened.

### Item-5 checks
- 02:118 vs S1:530 (O1, F12, S13, H8). The deviations log (`docs/plans/deviations_from_protocol.md`, column "After seeing test results?") marks rows 2, 8, 9 (partly), 11, 13, 16 and 18–22 as decided after relevant results: 11 rows. All 23 were committed after some Brazil future-years results existed. Methods now says each change "was recorded after at least some test results had been seen. The first 23 were recorded before any held-out-place result, and future-years results bore on 11 of them." S1 says the same (rows 1–23 recorded after some future-years results; those results bore on rows 2, 8, 9, 11, 13, 16 and 18–22); the stray sentence in the rows 39–53 bullet was moved there. Table S14 row 12 said "Yes (S1); before any spatial result", which contradicted the log ("Fixed before any spatial result") and the count of 11 (VERIFY_v1e.md had already ruled that row 12 was not decided after results); its cell now matches the log.
- 05:13 now reads "in 8 comparisons under the main test, and in 5 of these under both stricter checks" (T1b within_Holm 8/14; R3_A4 the five are a subset; src comment extended).
- 05:31 "+0.29%" = S2_control_panel.csv brazil G_emb_pct 0.2858 (seed 0), the row "none (embedding gain, L3 vs L4)" of Table S36; the text now cites "(seed 0; Table S36)".
- 03:17 "−0.39% (p = 0.39)" = Brazil held out, embedding gain (L3 to L4, no control), three-seed mean (T1 G_emb_pct, G_emb_p; Table 2 column "Embedding gain"); the sentence now says so.
- Abstract "both hurt in Colombia's" is supported in 3.8 (control gain −2.08%, 95% CI −3.47 to −0.69; embeddings alone −5.30%, −8.19 to −2.41; Table S54; both CIs exclude zero).
- 05:27 "the labelling pattern we had specified in advance" now points to Section 3.8, where it is defined (O12, F9).

### Other edits (two or more readers, or one clearly right)
- 02:31 "each embedding is used for the next year" (F). 02:53 "no control" rule rewritten (S5). 02:57 buffer "fell below 0.1" (H13). 02:59 14 comparisons spelled out; "unseen but not information-free" became "only partly unseen" (O10, F5). 02:98 "beyond the district's location or identity" (O11, F9). 02:100 identity-share sentence shortened. 02:104 averaging order matches `estimands.py` (districts, then horizons, then weeks); EWC parenthesis removed; "taken as fixed" became "the models as fitted" (O13, F11, S4, H7). 02:108 "Without the adjustment, a comparison is equivalent when ..." (F13, S3). 02:138 probe rewritten without the stacked list and the "X, not Y" closer (O14, F6, H18). 2.4: repeated codes after first use removed.
- 03:11 Taiwan coverage clause shortened. 03:55 "For them, equivalence means only ..." (F14, S11). 03:59 "can exceed the embedding gain, because the embeddings may partly offset the harm" (S10). 03:75 "trend in the gain" (H17). 03:89 transfer sentence without the ambiguous "it did" (H14). 03:91 "a loss", "more similar districts did not lose less" (S19, H15). 03:99 Colombia list rewritten.
- 05:17 "whether or not it helps overall" (O17, F10, S8). 05:19 "to choose between" (S15). 05:27 "where a district was or which district it was"; last sentence made parallel (O11, O12). 05:35 "its four countries" (F19, partly). 05:37 split; "the intended level" (F7, H). 05:39 shortened; only Colombia re-tuned (O18). 05:43 active voice (H19). 05:45 seasons and seeds in separate sentences (O19, H). 05:57 conclusion: equivalence sentence split from the margin; recommendation rewritten without "should not be taken as evidence" (F18, H20, S17).
- S2:987 "the losses with Brazil and Taiwan held out"; "applies most directly" (H).

### Not applied
- H6 (split the ladder paragraph into three), H10 and H11 (more glosses in the abstract), S12 (rephrase the strict-variance check): word limits, or the term is fixed in STYLE_DECISIONS.
- O6 "extreme test": the supervisor kept "stress test" for Taiwan held out.
- H2 ("Only ... conflicts with Table S56"): no conflict. The abstract requires both stricter checks and the hidden-case check; the loss with Brazil held out fails the strict-variance check (Holm p 0.095), so only Colombia's held-out states pass all three.
- H checks not in scope: the Nazir "settings without weekly case histories" sentence (4.4) is unchanged and unverified here.

### Deletions log (no result number lost)
1. 3.2 "It was the only loss that stayed significant under both stricter checks." (no number; in 3.4, Table S26).
2. 3.2 "It was significant after Holm correction but not under either stricter check." (Taiwan; in 3.4, Table 2).
3. 3.2 "The embedding gain was never significantly positive." (repeats the opening sentence).
4. 3.3 "The fixed control panel (Section 3.6) tests the identity confound more directly." (cross-reference 3.6 removed).
5. 4.1 "These losses may partly reflect cases hidden by zero-filling (Table S56)." and its src comment (told in 3.5 and 4.5).
6. 4.1 "(added R² about 0.01, with CIs that include zero; ...)": 0.010 and the CIs remain in 3.9 and Table S50.
7. 4.5 "because the embeddings begin in 2017": 2017 remains in 2.3 and the Introduction.
8. 4.5 "although the Colombian loss persisted in district-years with cases" (in 3.5 and 4.2) and "Losses arose mainly on zero-filled weeks." (in 4.2).
9. 4.5 "(Brazil's settings ... Colombia's when Brazil was held out)" detail (in 2.4); "In a sensitivity analysis, only Colombia's future years were tuned on a wider grid" shortened (result in 3.9 and 4.2).
10. 2.13 "The probe is cross-sectional, not a forecasting task."
11. Introduction: "and we found no location-only control in the study" and "That case study had no location-only control or held-out region, although ..." merged into one sentence with a combined src comment.
12. Abstract: "partly, Colombia" (the Colombian positive-control result remains in 3.1).

### Number check
`numcheck.py 99cec1a`: 7 NEW, all explained, and 3 removed.
- 03_results.md: "2" (the "Table 2" cross-reference for the Brazil-held-out embedding gain), "3.4" and "2.2" (section cross-references), "20" (draws per share in the hidden-case check; R5 design value, already in Table S56 note and the 3.5 src comment).
- 05_discussion.md: "8" and "5" (equivalence counts in 4.1, item 5; same values as 3.3, 4.7 and the abstract), "3.8" (section cross-reference in 4.3).
- Removed: 03 "3.6" (cross-reference); 05 "0.01" (deletion 6), "2017" (deletion 7). S1 and S2: no number added or removed (the S1 timing sentence moved within the file).
