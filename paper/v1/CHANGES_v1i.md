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
