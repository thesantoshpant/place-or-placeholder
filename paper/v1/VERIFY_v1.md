# VERIFY_v1: number and consistency check of draft v1

Date: 2026-11-18. Scope: `00_front`, `01_introduction`, `02_methods`, `03_results`, `05_discussion`, `06_declarations`, `S1_supplement_methods`, `S2_supplement_results`. Sources: `docs/results/tables/*.csv` (kit v3), `docs/results/review/*`, `docs/data/*`, `docs/methods/*`, `../audits/review_round/*`.

## Summary

- **Numbers checked: about 2,750.**
  - About 2,400 table entries were checked by script against the CSVs, cell by cell, covering Table 2 (the primary family) and Tables S2-1 to S2-19.
  - About 350 numbers in prose were checked by script or by hand.
  - About 80 S1 numbers were spot-checked against docs and audits: panel counts, zero-fill tables, R1 timing and buffer, R10, RC, RF, s1_pipeline, climate and remote-sensing docs.
- **Table mismatches: 0.** The only differences were rounding of p values near 1, such as 0.996 shown as "1.0" instead of "1.00", and a 5-significant-figure display in S2-4. Both are acceptable.
- **Numbers fixed: 13.** Wording and consistency fixes: 20 (listed below).
- **Unresolved issues: 16.** They are listed below.

## Changes made (file: old → new; reason)

### 00_front.md
1. Abstract src comment. Old: "(6,987 units with geometry, scored)". New: 6,987 units with geometry = 5,517 + 1,070 + 115 + 285; 6,909 are scored after the Espírito Santo exclusion. Reason: Espírito Santo is not scored in any test year (S7 n_units).
2. Findings. Old: "In 13 of 14 cells … no gain survived correction. For new years…". New: "In the 13 completed cells [[PENDING: BR S4]], no gain survived correction …; for new years…". Reason: the old wording implied one of 14 cells showed a gain.
3. Findings. Old: "Six showed losses surviving correction". New: "Six showed losses after correction". A new sentence follows: "Their direction was consistent, but four (three Colombian, Taiwan) were significant only under some variance estimators." It has a src comment (T1 B4_Holm_p, p_iaaft_Holm). Reason: the T1 robust columns. CO S1, CO S3, CO S4 and TW S5 are not Holm-significant under B = 4.
4. Three wording trims, to stay at or under 300 words:
   - "absolute loss 0.0035 on a baseline error of 0.020" → "absolute 0.0035 of a 0.020 baseline";
   - the Background was shortened;
   - "OpenDengue v1.3.1; … testing from 2020" → "OpenDengue; … testing 2020".
5. "Losses sat in unreported weeks filled as zero" → "Losses sat in zero-filled weeks". Reason: length.
6. Interpretation: "harmed transfer" → "worsened transfer". The word "weekly" was dropped. Reason: length; the strength of the claim is unchanged.
7. Plain-language summary:
   - the Taiwan sentence now adds "though some of these losses were statistically fragile";
   - "the summaries added nothing beyond them" → "added nothing detectable beyond them".

   Reason: match the strength of T1 and the no-history CI (−2.06 to 1.19).
8. The abstract word-count comment now records 298 words (whitespace count including the 4 section labels).

### 01_introduction.md
- No changes. All literature numbers were checked against `docs/research/literature.md` round 2 (5,570 municipalities; 19 of 20; October 2023 snapshot; 2020–2025; −0.0051 at one month; not significant at 3 and 6 months). The 6,987 count was also checked.

### 02_methods.md
1. `[[CITE: Pollett …]]` → `[@pollett2021epiforge]`. `[[CITE: Schreiber and Schmitz …]]` → `[@schreiber1996iaaft]`, with IAAFT spelled out.
2. "Diebold–Mariano test" → "Diebold–Mariano (DM) test". "Harvey–Leybourne–Newbold correction" → "… (HLN) correction". Reason: Results and Table 2 use DM and HLN.
3. "Figure 1 / 1B / 1C" → "Fig 1 / 1B / 1C". Reason: match "Fig 2–4" in Results.
4. Headings "# 2 Methods" and "## 2.x" → "## 2 Methods" and "### 2.x". Reason: the heading levels now match the other sections.
5. Added a src comment for "Peru's 115 provinces … 14 cells".
6. The data table stays **Table 1**. It is cited first, in 2.2 and 2.9. See the numbering note below.

### 03_results.md
1. **Table renumbered: "Table 1" → "Table 2"** (the text reference and the caption). Reason: Methods already has a Table 1 (data and design), and tables must be numbered in order of citation.
2. "## Results" → "## 3 Results".
3. Coverage. Old: "embeddings changed it by at most 0.05". New: "adding embeddings to L3+C\* changed it by at most 0.05 (0.07 from L3 to L4 in Taiwan S5)". Reason: in TW S5, L3 vs L4 coverage on weeks with cases is 0.558 vs 0.632. The src was extended.
4. "No stored forecast had crossing quantiles" → "… after sorting". Reason: S1-D says quantiles are sorted, and crossing before sorting was not logged.
5. **q0.9 shift: "+0.006 (Brazil S1)" → "+0.002 (Taiwan S1)".** Reason: the minimum dq90_log is TW_S1 0.0024 (S6), not Brazil S1. The src was extended.
6. Weighting. Old: "Colombian losses grew (to −1.38% in S3 with population weights)". New: "Colombian losses grew under population weighting (to −1.38% in S3)" and "Peru S5 turned negative under both". Reason: under case weighting, the CO S2 and S3 losses shrank (−0.40%).
7. Strata. Old: "losses were largest in districts with no reported case". New: "where losses occurred they were largest…". Reason: in BR S1 the no-history stratum was +0.55%.
8. 2021 rows. Old: "On the all-zero 2021 rows, WIS was 0.00394 …". New: "On the all-zero 2021 rows of Taiwan S5 … (seed 0; …)". Reason: the cell was not named.
9. **Similarity quintile means: "0.70–0.83" → "0.70–0.82" (Taiwan S5).** Reason: the Q5 mean is 0.8246.
10. **Per-quintile harm: "−32.1 to −42.3" → "−31.6 to −42.3" ×10⁻⁴.** Reason: Q4 is −31.6, which is smaller in magnitude than Q1's −32.1.
11. Robustness paragraph. Added: "The direction of all six losses was therefore consistent, but their significance after Holm correction depended on the variance estimator in Colombia S1, S3 and S4 and Taiwan S5." Reason: the brief and T1.
12. No-history paragraph. Added: "Because the embedding gain's CI included zero, the identity share was not estimable, and the pre-specified identifier pattern (…) was not met." The src now includes T6b ID_share and nohist_arm.md "Interpretation".

### 05_discussion.md
1. Headings: "5 Discussion" and "5.x" → "4 Discussion" and "4.x". Reason: there was no section 4, and Results is section 3.
2. 4.1. Added a sentence on robustness: the direction is consistent, and significance depends on the variance estimator in CO (new years, buffered blocks, random districts) and TW held out. Src: T1.
3. 4.2. "p = .048" → "p = 0.048" (p format).
4. **4.2 capacity: "about seven times … (6 to 20 times per horizon)" → "about eight times the shared-configuration embedding gain pooled over horizons 1 and 4 (6.5 to 14 times per horizon)".**
   - Recomputed from `T2_ladder_long.csv`: (perlevel L3 − shared L3) / (shared L3 − shared L4) = 0.00327 / 0.00043 = 7.7 for h{1,4}.
   - Per horizon: 13.7, 7.7, 7.3 and 6.5.
   - The old figure (R10) came from rows before the origin-year filter.
5. **4.2: "raised its zero-row 0.9 quantile by 0.097" → "0.099".** Reason: S6 TW_S5 dq90_log = 0.0987.
6. 4.2: the src for "every township lost" is now S7b (kit v3, with 2021: 285/285 in every quintile) in place of the pre-v3 RB.
7. 4.2. Old: "Only in Peru held out did gains rise with similarity". New: "… rise clearly … (ρ = 0.47; |ρ| ≤ 0.15 in the other held-out cells)". Reason: BR S5 (+0.10), BR S3 (+0.12) and CO S5 (+0.15) also have positive, weak ρ (S7).
8. 4.2: "vanished after causal recalibration" → "causal (Mondrian) recalibration". Reason: the global shift leaves +0.75% (S5).
9. 4.3. Old: "they added nothing". New: "they added no detectable gain". The sentence now also says the identity share is not estimable. Reason: the brief (consistent with the placeholder pattern, but not a formal pass).
10. **4.3 panel: "shrank the non-significant embedding gain from +0.25% to +0.02%" → "the non-significant embedding gain of +0.29% shrank to +0.02% once coordinates were in the model (+0.25% with historical risk)".** Reason: +0.25% is the C1 excess gain, not the embedding gain. The seed-0 G_emb is +0.29% (S2_control_panel). The src now points to the CSV.
11. 4.5 strengths. Old: "The main result held under …". New: the same, plus a note that two exploratory estimates were nominally positive without adjustment (CO S5 with case weights +0.49%; PE S5 on all rows +1.01%, p = 0.046). Reason: S4_weighted and T1.
12. 4.5. "validation cost 0.1–1.05%" → "0.11–1.05%" (RF, and matches S1-D).
13. **4.5 inference: "up to 22% … in surrogate simulations" → "10–22% … in surrogate simulations of the affected cells, up to 28% under a stress test".** Reason: RC and S1-F3.
14. **4.5 calibration. Old: "covered 61–75% … at every rung; causal recalibration barely helped". New: "intervals of the full model covered 61–75% …, and other rungs were similar (56–75%); causal recalibration raised this mainly in Peru".** Reason: L3 in TW S5 is 0.558; Peru rose from 0.67 to 0.76–0.77 (T2, S5).
15. 4.5 countries. Old: "Taiwan's test years are almost all zeros, so its tuning…". New: "Taiwan's data are almost all zeros (95 non-zero training targets at the 2019 tuning origin)". Reason: tuning used training years, not test years (s1_pipeline.md).
16. 4.5: "About 11 of the first 23" → "Eleven of the first 23". Reason: this matches Methods 2.11.
17. 4.7 Conclusion. Added "the direction of these losses was consistent, but four of them were significant only under some variance estimators".

### 06_declarations.md
- "commits cited for pre-specification in the Methods" → "in the Methods and Supplement S1". Reason: d8c7944 and fcc3c38 are cited only in S1-E.

### S1_supplement_methods.md
1. `[[CITE: Pollett …]]` → `[@pollett2021epiforge]`. Added `[@schreiber1996iaaft]` in F2.
2. **D, per-level tuning: "about seven times … (6–20 times per horizon)" → "about eight times the shared-configuration embedding gain … (6.5–14 times per horizon, primary rows) … before the origin-year filter the figure was about seven".** The src was extended.
3. E row 2: "a capacity effect about seven times the embedding gain" → "several times the embedding gain (about eight times on the primary rows; Section D)".
4. E: **deleted** "If the preprint is posted before Brazil S4 is complete, a row recording Holm over m = 13 cells must be added. [[PENDING: final Holm m=14]]". Reason: STYLE says posting comes after BR S4, so the final m is 14 and no m = 13 row is needed.
5. E row 31: "RQ4 (year-aligned vs static embeddings) deferred" → "The protocol's RQ4 (…) deferred; RQ4 in this paper is the exploratory question on where embeddings help or hurt". Reason: the Introduction renumbered the RQs.
6. F1: "(T1b)" → "(Supplementary Table S2-6)". Reason: kit file names should not appear in the paper.
7. **F3. Old: "Among the Holm-significant losses, only Colombia S4 is not robust (… current values are in T1)". New: this was so in the pre-filter simulation; on the current rows CO S1, S3, S4 and TW S5 lose Holm significance with B = 4, and CO S4 and TW S5 with IAAFT.** Reason: the old text contradicted T1 and the brief.
8. F4: "Strata for RQ5" → "Strata for RQ4 (exploratory)".
9. G item 12: "Results baseline table" → "Results; Supplementary Table S2-1". G item 15: "Pending (writer A)" → "Present".
10. Added a src comment for "Population sums agree within 0.03%" (R10: maximum 0.027%, Taiwan).

### S2_supplement_results.md
1. Five references to the primary table renumbered "Table 1" → "Table 2" (the S2-1, S2-2 and S2-12 captions).
2. The Fig 2, Fig 3 and Fig S2-2 captions said "Brazil S4 is pending." with or without a marker. They now read "Brazil S4: [[PENDING: BR S4]]" (the exact marker form).
3. S2-13, yref/delay2 rows, "Primary cell" column: "+0.26" → "+0.26 (seed 0: +0.29)". Reason: the caption says the comparator is the seed-0 +0.29%.

## Table and figure numbering (after edits)

- **Main tables:**
  - Table 1: data and evaluation design (Methods 2.2, also cited in 2.9).
  - Table 2: the primary family (Results).

  STYLE.md does not number tables, and the brief expected a single "Table 1". If only one main table is wanted, move the Methods data table into S1-B and renumber Table 2 back to Table 1. That means 2 references in Results and 5 in S2.
- **Main figures:** Fig 1 (design, spec in the Methods comment), Fig 2 (forest), Fig 3 (strata), Fig 4 (no-history ladder). The text says "Fig N" and the captions say "Figure N.". This is consistent with STYLE.
- **Supplement:**
  - Tables S1-A1 to S1-F1 and S2-1 to S2-19.
  - Figures S2-1 (similarity), S2-2 (per year) and S2-3 (S1 ladder), matching STYLE's supplement figures.
  - Every "Supplementary Table S2-n" reference in Results points to the right table.
- **Sections:** 1 Introduction, 2 Methods, 3 Results, 4 Discussion (4.1–4.7). Results subsections are unnumbered; numbering them 3.1–3.9 is optional.

## Citations

- Every `[@key]` exists in `refs_v1.bib` (65 entries, no duplicates). No `[[CITE: …]]` markers remain.
- **Unused bib entries (kept, not deleted):** `zhang2026population`, `stanaway2016burden`, `paho2023sitrep1`, `paho2024sitrep48`, `meyer2022global`, `goeman2010threesided`, `worldpop_r2025a`.

## Style checks

- No AI-assistant or product names.
- No "pre-registered".
- No Jan-15 freeze sentence.
- No em dashes in any paper file.
- p values use the "0.0xx" form.

## Unresolved issues

1. **Length** (see the word counts). The main text is about 6,970 words against about 5,500.
2. **Pre-kit-v3 numbers are still quoted.** All are labelled in src comments or captions:
   - RB strata: Table S2-17, the Results strata sentence, and the Discussion 4.2 strata sentence;
   - RB median nearest-neighbour cosine 0.77 vs 0.94–0.98 (Discussion 4.2; computed without Taiwan 2021);
   - RC size simulation (S1-F3, Discussion inference bullet);
   - RA3 "16 Peruvian rows";
   - RA7 "77,187,144 forecasts";
   - the RE control panel, where Taiwan has no 2021.

   Regenerate these in the kit before posting, or keep the labels.
3. **RG_tw2021.md CIs differ from T1 and T6a** (TW S5 [−26.56, −7.43] vs [−27.03, −7.57]). The paper uses T1. Ask the kit owner which CI construction RG used.
4. **T6a `variant_horizons` reads "1,2,3,4"** for BR_S1_perlevel and the Taiwan variants, but T3 and T5 show these are h{1,4} values. This looks like a kit label bug; the paper values are correct.
5. **The seed of the yref and delay2 runs is assumed to be seed 0** (S2-13 comparator +0.29%). Confirm when they land.
6. **A marker outside the STYLE list:** `[[PENDING: BR S1 no-history N4+C1]]` (S2-19). Add it to the Thursday fill list or drop the row.
7. **Taiwan L2 with shared parameters is missing.** S2-1, S2-2 and Fig S2-3 show a per-level L2 labelled "not comparable", with no marker.
8. **Kit figure titles need regenerating:** F1 says "best location control", and FS1/FS2 say "log1p WIS". The captions are already correct.
9. **Methods Table 1 lists universe counts** (Colombia 1,071; Taiwan 287), while 1,070 and 285 are scored (and Brazil 5,439 after Espírito Santo). Consider a footnote.
10. **Discussion 4.5 says "seed variation is the same order as several estimates".** For BR S1, the seed SD of the excess gain is 0.00002 against a SE of 0.00044. The claim rests on per-model seed SD (D16: 0.0001–0.0003). Consider rewording to "seed variation in a single model's WIS is the same order as several estimates".
11. **The headline "six losses" rests on the primary EWC test.** Every section now says that four of the six depend on the variance estimator. The authors should still decide whether the abstract should count six losses or two robust ones (BR S5, CO S2) plus four that are significant only under the primary test.
12. **Author items:**
    - GBD numbers;
    - the Taiwan CDC Internet Archive URL;
    - the OpenDengue CC BY-SA version;
    - licences for MODIS, VIIRS and GHSL;
    - the ethics confirmation;
    - the AI-use statement;
    - the repo and Zenodo DOI;
    - the official EPIFORGE checklist file;
    - the derived-data licence;
    - the Brittain byline ("J.-S." vs "John").
13. **The plain-language summary is 137 words** against about 120.
14. **Repo docs outside paper/v1 are stale** (notes_B): the deviations_from_protocol.md header says "pre-registered" and mentions the freeze; rows 2, 13 and 14; runner.md; control_selection_v2.md. Fix them before the repo goes public.
15. **NOTES_FOR_WRITERS item 32 is stale.** The panel uses v3 rows, and the captions are correct.
16. **Week-mean vs row-mean WIS.** Table 2 and T1 use week means (BR L3 0.1675); T2 and S2-1/S2-2 use row means (0.1681). The captions say so. Confirm that this is intended.

## PENDING markers (exact forms; 55 in total)

| Marker | Count | Locations (file: line) |
|---|---|---|
| `[[PENDING: BR S4]]` | 19 | 00_front 20; 03_results 15, 25 (×2); 05_discussion 7; S2 25, 47, 67, 91, 111, 134, 158, 180, 200, 220, 352, 423, 425, 431 |
| `[[PENDING: final Holm m=14]]` | 6 | 00_front 20; 02_methods 143; 03_results 15, 17; 05_discussion 7; S2 91 |
| `[[PENDING: BR S2 no-history]]` | 8 | 00_front 20; 03_results 69; 05_discussion 19; S2 295, 296, 297, 402, 427 |
| `[[PENDING: BR C3/C6 panel]]` | 14 | 02_methods 55; 03_results 59; 05_discussion 21; S1 377; S2 247 (×2), 248 (×2), 274–279 |
| `[[PENDING: sensitivities yref/delay2]]` | 7 | 02_methods 147; 03_results 55; 05_discussion 31; S1 378, 379; S2 272, 273 |
| `[[PENDING: BR S1 no-history N4+C1]]` (not in STYLE) | 1 | S2 416 |

Other markers for the authors:

| Marker | Locations |
|---|---|
| `[[AUTHORS: TBD]]` | 00_front 11, 12; 06_declarations 42, 48, 54, 60, 66, 72 |
| `[[AUTHORS: repo public + Zenodo DOI]]` | 05_discussion 37; 06_declarations 32, 36 |
| `[[AUTHORS: confirm licence for derived data]]` | 06_declarations 32 |
| `[[AUTHORS: confirm that no institutional review …]]` | 06_declarations 13 |
| `[[AUTHORS: ...]]` | 06_declarations 3 (inside a comment) |
| `[[VERIFY: exact Internet Archive snapshot URL]]` | 06_declarations 10 |
| `[[VERIFY: CC BY-SA version number]]` | 06_declarations 27 |
| `[[GBD: authors to pull from IHME]]` | 01_introduction 3 |

## Word counts

Prose only, excluding HTML comments, markers, citation keys, LaTeX blocks and table rows.

| Section | Words | Target | Difference |
|---|---|---|---|
| Abstract | 298 (by whitespace, including 4 labels; 290 alphanumeric words) | ≤ 300 | OK |
| Plain-language summary | 137 | ~120 | +17 |
| 1 Introduction | 892 | ~800 | +92 |
| 2 Methods | 2,138 (including the Table 1 caption; excluding the Fig 1 spec comment) | ~1,900 | +238 |
| 3 Results | 2,036 (1,812 prose + 224 Table 2 caption) | ~1,500 | +312 prose (+536 with the caption) |
| 4 Discussion | 1,920 (4.5 limitations about 720) | ~1,300 | +620 |
| **Main text** | **about 6,986** (about 6,760 without the Table 2 caption) | ~5,500 | **about +1,260** |
| Declarations | 435 | – | – |
| Supplement S1 | 3,909 prose + 3,702 in tables | – | – |
| Supplement S2 | 3,918 prose + 3,667 in tables | – | – |

## Proposed cuts (not applied)

These total about 1,250 words.

- **Discussion (−600):**
  - Move the "Calibration", "Countries" and "Covariates and geometry" limitation bullets to S1, leaving one sentence (about −200).
  - Shorten the "Later-dated information" and "Decisions after results" bullets, which repeat Methods 2.6 and 2.11 (about −150).
  - Drop the 4.3 second paragraph (the control panel), which repeats Results (about −70).
  - Drop the last sentence of 4.4 (per-year), which repeats Results (about −50).
  - In 4.2, cut the Peru S5 fragility sentence to one clause (about −50).
  - Tighten 4.1, which repeats Results numbers (about −80).
- **Results (−320):**
  - Move the "Per-year view" paragraph to S2 and keep one sentence (about −70).
  - Reduce "Supporting and sensitivity analyses" to two sentences pointing to S2-9 to S2-11 and S2-17 (about −110).
  - Cut the Table 2 caption to the essentials and point to Methods 2.7–2.9 for the definitions (about −120 of its 224 words).
  - Shorten the paragraph on Taiwan with 2021 (about −30).
- **Methods (−240):** writer B's proposal.
  - Move the zero-fill validation sentence (2.2) to S1-B4.
  - Move the second paragraph of 2.6 to S1-A.
  - Move the robustness paragraph of 2.9 to S1-F2, leaving one sentence.
- **Introduction (−90):** compress the prior-work paragraph, the Muslim and Nazir details in particular. They belong in the Discussion or are already in R8.
- **Plain summary (−17):** drop or merge the first sentence ("Health departments use dengue forecasts…").
