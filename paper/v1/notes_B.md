# Notes from writer B (Methods + Supplement S1)

## Status
- `02_methods.md`: about 2,250 words of prose (tables, formulas and HTML comments excluded), above the ~1,900 target. Easiest cuts if needed (about 200 words): the zero-fill validation sentence in 2.2, the second paragraph of 2.6 and the robustness paragraph of 2.9 can move to S1 (sections A, B4 and F2 already hold the detail).
- `S1_supplement_methods.md`: about 8,900 words, sections A–H; the full 34-row deviation table is in E.
- Figure 1 spec: HTML comment at the end of Methods 2.6.

## Open questions for the supervisor
1. **Peru unit word.** STYLE.md says "district in Peru", but Peru's Admin2 units are provinces (115 of ~196; `docs/data/completeness_v1.md`). I wrote "provinces in Peru; we call them districts" and also used the review's "second-level administrative unit" once. Please fix STYLE and tell writers A and C.
2. **Two citation keys are missing from both bib files.** I used `[[CITE: …]]` markers: Pollett et al. 2021 (EPIFORGE, doi:10.1371/journal.pmed.1003793) and Schreiber & Schmitz 1996 (IAAFT surrogates). Writer A should add them to `refs_v1.bib` (suggested keys `pollett2021epiforge` and `schreiber1996iaaft`).
3. **Posting before BR S4.** S1-E ends with a note that a deviation row 35 (Holm over m = 13) is needed if the preprint is posted before Brazil S4 lands.

## Code and docs disagree (I followed the code or the newest evidence)
- **C1 period:** the code uses all panel years before 2018 (Colombia from 2007, Peru from 2000, Taiwan from 1998). RESOLUTION_LOG says "2014–2017", which is true for Brazil only. I wrote "years before 2018 (Brazil 2014–2017)".
- **No-history C\* candidates:** `select_control.py` uses C2, C3, C4 and C4s (plus C6 in S1), with priority C3 > C2 > C6 > C4s > C4. `nohist_arm.md` amendment (c) and deviation row 19 leave out C4s. I followed the code.
- **Training-target drops:** `completeness_v1.md` recommends dropping 5 primary-flagged weeks from training targets. Per R1, the code drops only the `flag_gap` week (Peru 2018-08-12). I described the code.
- **Control panel rows:** `RE_summary.md` says it uses the v3 primary rows (origin-year filter, exclusions v2). `NOTES_FOR_WRITERS` item 32 says it uses all rows. Writer C should confirm before quoting it next to T1.
- **Stale repo docs to fix before the repo goes public:**
  - `deviations_from_protocol.md` header still says "pre-registered" and "planner's response" and mentions the 15 Jan freeze. Row 2 says "≤0.07%"; the true range is 0.03–1.4% (R10). Row 14 says "log incidence"; the code uses log(1 + cases). Row 13 says "2019 origin only", but R6 says the issue was found after Brazil S1 test results. S1-E uses the corrected wording; please confirm row 13.
  - `runner.md` feature table still describes the old C1 (training-target mean) and the per-year C3.
  - `control_selection_v2.md` says Brazil and Colombia S5 were "not re-selected", but T4 shows rule-v2 picks (C3 and C2).
- **Peru exclusion rows:** R10 and RESOLUTION_LOG say 32 of 48,054 rows (0.07%); RA3 says 16 rows (h{1,4}). I used "two department-weeks" in the text and "16 rows" from RA3. Please recheck against the v3 primary rows.
- **RC (size simulation) and RA analyses predate kit v3**, so they have no origin-year filter and no Espírito Santo exclusion. I flagged this in S1-F3. Current B = 4 and IAAFT p values are in T1 (for example, CO S4 B = 4 Holm p is .126 in T1 and .10 in RC).
- **TW S1 secondary h1–h4 pooling** (`T1 sec_years`) leaves out 2021 because the 2021 runs are h{1,4} only. Writer C should say so wherever S1 h1–h4 is quoted.

## For the authors
- **Licences:** licences for MODIS, VIIRS, GHSL, InfoDengue and the Taiwan CDC file are not recorded in the repo docs (S1-B1 says "provider terms"). The "Peru ~196 provinces" figure comes from `completeness_v1.md` (approximate).
- **EPIFORGE (S1-G):** this is a paraphrase. Replace it with the official checklist file. Items 6, 9 and 16 need the public repo URL and the Zenodo DOI.
- **AI-use statement:** S1 refers to "a separate verification script" and to audits. Per RESOLUTION_LOG, the AI-use statement must say these were AI-agent work and what people checked.
- **AlphaEarth compute total** (EECU-hours) is not in any repo doc, so it was left out. Only the per-area rates and the climate and remote-sensing totals are given.
