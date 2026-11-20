# v1f plain-language edit of the supplement (S1, S2)

Scope: `S1_supplement_methods.md` and `S2_supplement_results.md`. I edited prose, captions, table notes and some word-only table label cells. I changed no table number, and I added, deleted or renumbered no table, figure or section. All 98 (S1) and 106 (S2) HTML comments are byte-identical to the input, including every `<!-- src -->`. The `[to be completed]` and `<!-- AUTHORS -->` markers are untouched.

## Kinds of change

- **Fixed terms.** Prose, captions, notes and table label cells now use:
  - "future years" (was "new years"/"new-years");
  - "comparison" (was "cell"); grid, land and ocean cells are kept;
  - "reference model" and "embedding model";
  - "the main test", "the strict-variance check" (B = 4), "the surrogate-series check" (IAAFT) and "the two stricter checks". These replace "cautious tests", "B = 4 variance" and "IAAFT calibration" in prose.
  - "Without case history" replaces "no-history".
  - "District label" replaces "district identifier" for C6 in prose, the S23 caption and one S36 label cell.
  - "Reviewers" replaces "referees".
- **Process and draft voice removed.**
  - "round 3", "round-3 runs", "blinded/unblinded", "still blinded", "rule v2" in prose and headings (B1 and the G heading), and "pre-declared compute cut";
  - "now share one row set" and "These values replace...";
  - "chunks", "moved aside", "invalidated", "routes as missing", "bitwise/bit-identical", "upstream", "mean pyramid", "Mollweide", "computePixels/reduceRegions" in prose. Code identifiers stay in Table S1 and the regex in A6.
  - "Rule v1/v2" remain only in Table S43/S45 cells, and the S43 note now explains them.
- **Sentence structure.**
  - Number-packed sentences are split (A2 to A7, C, D3, E3, F, I; S2 conventions, G1, G2, G4, G5, G6, G8, G9, G10).
  - Verdict-colon openers and habitual "X, not Y" closers are rewritten. Examples: "The broad conclusions survive every switch:", "Internal anchor:/External anchor:", "Agreement shows ... not that the product is valid", "more, not less, convincing".
  - "Outcome-agnostically" is replaced, and "In Colombia the exposure is inert" is stated plainly.
  - No nested parentheses or em dashes remain in prose.
- **Lists instead of long sentences.**
  - S1-F timing is now a 5-item bullet list. I did not add a table, because the table count is fixed.
  - The E3 generating processes and the S2 opening conventions are now bullet lists. The conventions list opens with the week-weighted versus row-mean rule.
  - The four G9 representation variants (V1 to V4) are now a bullet list.
- **Plain-language glosses added:**
  - size and power (E3);
  - pinball loss, zero-shot, MDE and TOST (E1);
  - the purpose of the IAAFT check (E2);
  - a one-sentence plain summary of the control-selection rule (B1);
  - the completeness rule (A5);
  - the Taiwan crosswalk (A3);
  - the buffer correlograms (D3);
  - over-dispersion (S46 note).
- **Repetition cut.**
  - The AI-agent disclaimer is now stated once, in the S1 header; A1, A3 and the S5 note no longer repeat it in full.
  - The repeated closing sentence of S2 G8 ("So the embeddings encode ... duplicates ...") is deleted.
- **Sign wording.** "Changed WIS by −0.04%" is now "the excess gain ... was −0.04%". "Improved N3 by +1.98%" is now "gave a control gain of +1.98% over N3".
- **Captions.**
  - Headings: D2, "Information dated after the forecast origin..."; G2, G5, G6.
  - Table captions: S9, S10, S23, S26, S44, S47.
  - Figure captions S1 to S4 are rewritten with a plain first sentence. Drawing conventions are shortened.
  - "RQ4" is now "research question 4, where embeddings help or hurt".

## Glossary rows (Table S16)

- **Added:**
  - Comparison (cell);
  - Embedding model;
  - Equivalent within the margin;
  - Future years;
  - Main test;
  - Strict-variance check;
  - Surrogate-series check;
  - Two stricter checks;
  - With a location control.
- **Rewritten:**
  - Booster, leaves;
  - C\*;
  - Embedding gain, Control gain and Excess gain, each now with a plain definition and "one of the two main measures" instead of "co-primary";
  - IAAFT;
  - Location control, now with the binding definition;
  - Noise control of matching size;
  - N3, N4;
  - S1–S5, now with "future years".

## Number-check notes for the supervisor

- The only numeric differences are reorderings within the same sentence and the cases listed below.
- **Digits inside codes.** Some removed codes contain digits: Admin1/Admin2, "round-3", "rule v2", L3/L4/S5 in prose replaced by plain names. Some glossary rows add L4/L3/S1/B1 codes.
- **One deletion.** The redundant second "6,909" in S1-A2 is deleted, as the reviewers asked. The same value stays in the preceding sentence of the same paragraph.
- **One word-to-digit change.** "Eighty per cent" became "80%" in S1-I, for consistency with the rest of the text. The value is unchanged.

## Skipped or not applicable

- **Paper title.** The supplement does not repeat the title, so there was nothing to update.
- **No new timeline table** for S1-F, as the reviewers suggested, because tables may not be added. A bullet list is used instead.
- **Deviations table (S14).** The codes and commit hashes are kept, as allowed. Only "rule v2", "co-primary", "referees", "cautious variance estimator" and the row-set wording were changed.
- **Not re-read:** table cells, apart from word-only label cells.
