# Draft v1 — shared brief for all writers (read first)

Target: **medRxiv preprint, Epidemiology**, submit Mon 23 Nov 2026. Agents write and verify; the three authors then review and comment in a shared doc, iterating until sign-off. The posted PDF is exported from that doc.

## Authors (exact)
1. Santosh Pant — Knox College, Galesburg, Illinois, USA
2. Brij Patel — Illinois State University, Normal, Illinois, USA
3. Adithya Asokan — University of Washington, Seattle, Washington, USA

Corresponding author, emails, ORCID: `[[AUTHORS: TBD]]`. Funding, competing interests, CRediT, AI-use statement: `[[AUTHORS: TBD]]` placeholders only. AI use (authors' decision 2026-11-18): the full AI-use statement, naming the tool, is added ONLY in the shared doc and the submitted PDF. In these repo files write `[[AI-USE: full statement in the shared doc]]` in the declarations. Wherever the text describes code, verification, audits or analyses done by agents, say so factually and generically ("automated AI agents; see Use of AI tools"); never imply a person did it.

## Sources of truth (in this order)
1. Numbers: `docs/results/tables/*.csv` (T1–T6, S1–S8) and `docs/results/review/*_summary.md`, `RG_tw2021.md`, `RE_summary.md`. **Never copy a number from draft v0, the reviews or memory.** After every number or number group, put an HTML comment naming its source, e.g. `<!-- src: T1_primary_family.csv BR_S5 pct_of_WIS_ref -->`.
2. Decisions: `../audits/review_round/RESOLUTION_LOG.md` (binding; every "agree" row must be reflected), `docs/plans/deviations_from_protocol.md` (rows 1–34), `docs/results/NOTES_FOR_WRITERS.md`, `docs/results/RESULTS_BRIEF.md`.
3. Criticism to fix: `../audits/review_round/R6_draft_and_medrxiv.md` (brutal review of v0 + medRxiv/EPIFORGE mapping), `R1_timing_leakage.md`, `R2_data_scoring.md`, `R10_fact_check.md`, `R8_literature.md`, plus the raw reviews (`external_review_and_venues_2026-11-17.md`, `gdoc_review_and_preprint_plan_2026-11-17.md`, `friend_comments_gdoc_2026-11-17.md`) and the team guide (`medrxiv_guide_gdoc_2026-11-17.md`).
4. Prose you may reuse after checking: `../audits/review_round/draft_v0_rev114.md`, `paper/main.tex`. v0 is outdated (pre-review numbers, old scoring); rewrite, do not copy numbers.
5. Citations: `paper/refs.bib` + `../audits/review_round/R8_refs_additions.bib`. Cite as `[@key]`. Only keys that exist there. GBD burden numbers are UNVERIFIED: write `[[GBD: authors to pull from IHME]]`, never a number.

## Pending results (mark exactly, do not guess)
`[[PENDING: BR S4]]`, `[[PENDING: BR S2 no-history]]`, `[[PENDING: BR C3/C6 panel]]`, `[[PENDING: sensitivities yref/delay2]]`, `[[PENDING: final Holm m=14]]`. Posting is after BR S4 lands, so the final m = 14 (no m = 13 deviation row needed). The current family has 13 of 14 cells; write Holm values as "(Holm over the 13 available cells; final m = 14)". A fill pass on Thursday replaces every `[[PENDING…]]`.

## Fixed framing and terms
- Question: do AlphaEarth annual satellite embeddings improve weekly district dengue forecasts beyond what location identity already gives? Unit word: "district" (municipalities in Brazil and Colombia, provinces in Peru, townships in Taiwan; say once that we call all of them districts).
- Estimands, always with a one-sentence plain definition before any formula: **embedding gain** (G_emb = WIS(L3) − WIS(L4)), **identity gain** (G_id = WIS(L3) − WIS(L3+C*)), **excess gain** (G_excess = WIS(L3+C*) − WIS(L4+C*)), the primary. Reported as % of WIS(L3), positive = embeddings help, pooled over horizons 1 and 4 weeks, origin-year rows.
- Inference: DM test with EWC long-run variance + HLN; Holm over the 14-cell family; TOST equivalence margin ±1% of WIS(L3) (sensitivity 0.5/2%). Say "pre-specified (commit `bd3ba50`/`fcc3c38` etc. as in the deviations log)", never "pre-registered"; no Jan-15 freeze sentence.
- Taiwan stays in the family. "Stress test" wording only in the Discussion. TW S5 is reported with absolute log-WIS next to the %.
- Headline (current): no cell shows a significant gain; small significant harms in BR S5 and CO S1–S4 after Holm; a large harm in TW S5 (out-of-distribution); others null/equivalent; PE S5 gain fragile. No-history arm (BR S1): coordinates help (+3.3%), embeddings add nothing beyond coordinates — the clearest "placeholder" evidence. Phrase the title answer only as strongly as the CIs allow.
- Scope deferred to follow-up work (say so in Discussion): PDFM (L5), second model class, monthly arm, RQ4 static vs lagged, reporting-delay realism beyond the delay-2 sensitivity.
- Plain, short sentences. Define every abbreviation at first use; a glossary goes in the supplement. No marketing words ("novel", "groundbreaking"). No em dashes in running prose; use commas, colons or parentheses.
- **Never write the product name of any AI assistant in repo files.**

## Figures (current kit outputs in `docs/results/figures/`)
Numbering (accepted 2026-11-18): sections 1 Introduction, 2 Methods, 3 Results, 4 Discussion; Table 1 = Methods data table, Table 2 = primary family. Main: Fig 1 study design and information timing (NEW: give a precise text spec; it will be drawn), Fig 2 forest plot of excess gain `F1_forest_G_excess.png`, Fig 3 three-strata contributions `F2_strata_contributions.png`, Fig 4 no-history ladder `FS2_nohist_ladder.png`. Supplement: `F3_s5_embedding_distance.png`, `F4_per_year_gains.png`, `FS1_ladder_S1.png`. **Ignore the stale files `F2_ladder_S1.png` and `F3_per_year_gains.png`.**

## Length targets
Abstract ≤ 300 words (structured: Background, Methods, Findings, Interpretation). Plain-language summary ~120 words. Main text ~5,500 words: Introduction ~800, Methods ~1,900, Results ~1,500, Discussion ~1,300. Technical detail (extraction, checksums, compute, scheduler, full deviation table) goes to the supplement.

## Files (one owner each; write only your own)
`paper/v1/00_front.md`, `01_introduction.md`, `05_discussion.md`, `06_declarations.md`, `refs_v1.bib` → writer A.
`02_methods.md`, `S1_supplement_methods.md` (info-availability table, data details, full deviations table, EPIFORGE 2020 checklist, glossary) → writer B.
`03_results.md`, `S2_supplement_results.md` (supplementary tables and figure captions) → writer C.
