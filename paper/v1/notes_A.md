# Writer A notes (for the supervisor)

## Files and lengths (words, excluding HTML comments, markers and citation keys)
- `00_front.md`: abstract 299 (limit 300), plain-language summary 129 (target ~120), 7 keywords.
- `01_introduction.md`: ~905 (target ~800). The excess is the prior-work paragraph, which keeps the exact wording constraints from R8 and the literature notes.
- `05_discussion.md`: ~1,810 (target ~1,300). The limitations list alone is ~660 words because it carries every limitation the resolution log assigns to text. If length matters, move the "Calibration" and "Covariates and geometry" bullets to the supplement (about 120 words).
- `06_declarations.md`: placeholders for all author-only items.
- `refs_v1.bib`: 65 entries, no duplicate keys; every key of `paper/refs.bib` and `R8_refs_additions.bib` is present except `araujo2025sprint`.

## Title alternatives
1. Place or Placeholder? Satellite embeddings add no detectable skill to weekly dengue forecasts beyond surveillance history and location (use only if Brazil S4 and Brazil S2 without history do not change the picture).
2. Place or Placeholder? Do satellite embeddings improve short-term dengue forecasts beyond surveillance history and location controls? (question form; safe whatever the pending cells show).

## Open issues (most important first)
1. **Robustness of the losses changed with kit v3 (Taiwan 2021 included).** In T1, Taiwan S5 is no longer significant after Holm under EWC B = 4 (B4_Holm_p .14) or IAAFT calibration (p_iaaft_Holm .14), although its unadjusted p values stay below .05 (.016, .020). Colombia S1 and S3 lose Holm significance under B = 4 (.079, .084) but keep it under IAAFT. Colombia S4 is fragile under both (.14, .054). The resolution log ("TW S5 survives every check") is out of date. I wrote the limitations bullet from T1; writer C's Results must say the same.
2. **Equivalence counts differ from the resolution log.** T1b (kit v3) gives 9 of 13 cells within ±1% unadjusted and 8 after Holm-adjusted TOST. Brazil S1 is now within ±1% after Holm, and Colombia S3 (knife-edge) is the one that drops out; Taiwan S1 is not within ±1% even unadjusted. The log's "7/13, BR S1 and TW S1 lose it" predates kit v3. I used T1b.
3. **The no-history result is suggestive, not decisive.** Brazil S1 without history shows the placeholder pattern (coordinates +3.3% [1.7, 4.9]; embeddings beyond coordinates −0.43% [−2.06, 1.19]), but it does not meet the pre-specified identifier criterion: both intervals are too wide (MDE 2.3%). The arm's pre-specified headline is Brazil S2. The title and abstract should be fixed only after that cell lands.

## Other points to resolve
- **Citation keys.** `araujo2025sprint` is replaced by `araujo2026sprint` (PNAS 2026). I added `pollett2021epiforge` (EPIFORGE 2020) and `schreiber1996iaaft` (Phys Rev Lett 77(4):635–638, doi:10.1103/PhysRevLett.77.635), both checked on Crossref; writer B's `[[CITE: ...]]` markers are left for the verifier. Fixed in the merge: Diebold–Mariano issue and pages, Bracher issue, TimesFM (PMLR 235, 10148–10167), Ploton and Meyer 2022 DOIs, first names of Brown and Agarwal.
- **RQ numbering.** The Introduction uses RQ1–RQ4: the old RQ5 (strata) is now RQ4 (exploratory) and the old RQ4 (lagged vs static embeddings) is deferred. Writers B and C should use the same numbering.
- **Numbers from pre-kit-v3 sources** (recheck in the Thursday fill pass): the "about seven times" capacity ratio (R10, computed before the origin-year row filter); RB strata, median nearest-neighbour cosine 0.77 and "285/285 townships harmed" (computed without Taiwan 2021); the RE control panel (Taiwan without 2021). Kit v3 changed two numbers quoted in the log: Brazil S1 upper bound is now +0.79% (log: +0.9%) and Brazil S1 2024 is +0.88% (log: +1.04%). The Taiwan S5 Spearman ρ is −0.13 in S7 (kit v3) vs −0.10 in RB; I used S7.
- **Ethics.** Authors must confirm that no institutional review or exemption determination is held or needed (none is claimed). Add the exact Internet Archive snapshot URL of the Taiwan CDC file. I described that file as a "case-level line list with onset date and township of residence" without claiming it has no identifiers; someone should check its columns before posting.
- **Licences.** The OpenDengue CC BY-SA version is not recorded in our docs (`[[VERIFY]]` in the declarations). The derived-data licence (CC BY-SA 4.0) needs the authors' confirmation.
- **References to check by a person:** `gbd2023diseases` (group author name), `ihme2023gbdresults` (access date), `taiwancdc_dengue_daily` (snapshot URL); `brittain2026foundation` lists "J.-S. Brittain" while Muslim et al. list "John Brittain"; confirm the medRxiv byline.
- **GBD burden numbers** are left as `[[GBD: authors to pull from IHME]]` in the first paragraph of the Introduction.
- **Holm family.** Posting waits for BR S4, so the final Holm m = 14; every `[[PENDING: final Holm m=14]]` marker is filled from the frozen T1.
- **Pending markers used:** `[[PENDING: BR S4]]`, `[[PENDING: final Holm m=14]]`, `[[PENDING: BR S2 no-history]]`, `[[PENDING: BR C3/C6 panel]]`, `[[PENDING: sensitivities yref/delay2]]`. If BR S4 or the no-history S2 cell changes a headline, the abstract Findings, 5.1, 5.3 and 5.7 need edits.
