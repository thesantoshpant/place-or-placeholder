# CHANGES v1f: plain-language edit of the main text (2026-11-20)

Files edited: 00_front.md, 01_introduction.md, 02_methods.md, 03_results.md, 05_discussion.md, 06_declarations.md. Supplement files were not touched. Binding brief: audits/final_round/STYLE_DECISIONS.md; inputs: the four STYLE_*.md reviews.

## Word counts

Method as in v1d (HTML comments, equations, tables, captions, table notes and headings excluded; the Table 2 note is now split into labelled paragraphs "Seeds:", "Taiwan:", "Symbols:", "Labels:", which are table notes and were excluded).

| Part | v1e | v1f |
|---|---|---|
| Abstract (labels included) | 300 | 300 |
| Introduction | 775 | 860 |
| Methods | 2,528 | 2,589 |
| Results | 1,814 | 1,727 |
| Discussion | 1,190 | 1,162 |
| Main text | 6,307 | 6,338 |

Counts exclude in-text citation keys. Counting citation keys as words gives 6,339 (v1e) and 6,368 (v1f). Either way the main text is under 6,400.

## Main kinds of change

- Title set to STYLE_DECISIONS section 1. "Placeholder" is defined once in the Introduction (paragraph 3).
- Fixed terms applied in all six files:
  - "new years" → "future years";
  - "cell" → "comparison" (the Table 2 header now says "Comparison");
  - "co-primary" → "both main measures";
  - the tests are "the main test", "the strict-variance check" and "the surrogate-series check" (together "the two stricter checks"); EWC, HLN-type wording and IAAFT are named once, in Methods 2.10 only;
  - controls are named "average past cases", "coordinates", "shuffled embeddings", "smooth spatial noise" and "district label" (this replaces "historical risk", "static history", "random fields" and "identifier" in prose and in the Table 2 control column).
- "Location control" is defined once, in the Introduction, with the STYLE_DECISIONS wording. Methods 2.5 now lists the five controls as a short list.
- Codes:
  - D-codes, "rule v2", commit hashes and file names were removed from main-text prose and from the Table 1 note; changes now point to "Table S14";
  - L/C/N/S codes appear only in parentheses after the plain name at first use, in tables, in table notes and in figure captions;
  - Table 2 has a code key line;
  - the commit hashes remain in the Code availability statement only.
- Sign rule: "changed WIS by +x%" / "−x%" was replaced by "gain of", "control gain", "made forecasts worse" or "lowered accuracy" (Results 3.6, 3.8). The probe sentence now uses one unit per quantity.
- Removed signposting and verdict-plus-colon openers: "This is our answer to the title's question", "The embeddings are not empty:", "Transfer itself worked:", "Model capacity matters:", "Three results were fragile:", "Outcome-agnostic measures agree", "Part of the loss is generic", "The key limit on scope", "Recent seasons ... were exceptional:", "Geospatial foundation models offer a shortcut:", "Dengue adds a complication:".
- Overstated wording fixed:
  - "can only favour" → "if anything, favours";
  - "did not improve" → "did not detectably improve";
  - "cannot separate" → "makes ... hard to separate";
  - "year-to-year noise is not the explanation" → "not the whole explanation";
  - "harmed/protect" → "had a negative excess gain / higher similarity did not reduce it";
  - "of the order of its climate gain" → "smaller than its climate gain";
  - "improved it by 2.54%" (CI spans zero) → "was 2.54%, but its CI included zero";
  - "Brazil's held-out districts showed no difference" → "no significant difference".
- Mechanisms in Discussion 4.2 are hedged ("probably", "seems to", "one possible explanation"). The heading is now "Why the embeddings can make forecasts worse".
- Long sentences:
  - long sentences were split, and number-stacked sentences were thinned (see removals below);
  - nested parentheses were removed;
  - Methods 2.12 lists the post-result changes as bullets.
- Repetition cut:
  - the "case history identifies the district" point now appears once in the Introduction and once in Methods 2.11;
  - the location-control definition appears once;
  - the "redundant with coordinates and covariates" point appears in Abstract, 4.1 and 4.7 only.
- Process voice:
  - "after a third review" → "after a further review";
  - Methods 2.12 states once that changes followed "external and internal reviews of earlier drafts".
- Declarations:
  - the Taiwan data sentence was split;
  - the consent wording was simplified;
  - the data-deposit sentence was split;
  - Code availability says "will receive a DOI on the day of posting";
  - the duplicate sentence "No separate third-party deposit..." was removed (it is in Methods 2.12);
  - the `[to be completed]` + `<!-- AUTHORS -->` markers and the `<!-- AI-USE -->` slot are untouched.
- AI-use statement (GPU only, `tmp/ai_use_statement.md`):
  - backup saved as `tmp/ai_use_statement.v1.md`;
  - rewritten in first-person plural with short sentences;
  - every factual claim kept (the tool and maker; agents; code for download, processing and verification; Earth Engine extractions; model runs; scoring; statistics; internal checks and audits; drafting; reference checks; the independent-check rule; author direction, review and responsibility).

## The three content fixes

1. **Added R² beyond coordinates and static covariates.** The claim is restricted to Brazil and Colombia. In Peru and Taiwan, the text now says the added R² was too uncertain to judge, or had wide intervals that included zero. This is applied in the Abstract (Findings and Interpretation), Discussion 4.1 and Conclusions 4.7. Results 3.9 already restricted it.
2. **"About as well as standard covariates" → "less well than".** This is applied in the Abstract ("less well than covariates"), Discussion 4.1 ("less well than standard covariates but far better than coordinates") and Results 3.9 ("That is less than the static covariates explained (43% to 66%)"; was "close to"). Each country's embedding R² is below its static-covariate R² (0.49/0.65, 0.52/0.66, 0.24/0.43, 0.45/0.55).
3. **Methods 2.12 seed row and count.**
   - The list has seven items, so the text now says "Seven changes made after results were seen". These are the shared settings, the control-selection rule, pooling horizons 1 and 4, seed averaging, origin-year rows, Taiwan 2021 and the Espírito Santo exclusion.
   - The seed item covers deviation rows 22 (Brazil, future years) and 53 (all other comparisons). Row 49 is the extra seed runs themselves. The src comment records this mapping.
   - No D-codes remain in the prose. The text cites Table S14 (the deviations table in S1).

## Numbers removed from prose (each still in a table)

Each entry gives where the number was and where it still lives.

**Abstract**
- "log(1 + cases)" as the scale of the weighted interval score. It is in the Table 2 note and Methods 2.8.
- The sentence on upper forecast quantiles (no number). It is in Results 3.5 and Table S31.

**Methods**
- 2.2: InfoDengue "2.1%" is in Table S4.
- 2.2 and Table 1 note: D25 → Table S14.
- 2.12/2.13: all deviation codes (D1–D53, rows 11, 12, 21 and so on) → Table S14.
- 2.12: the parenthetical naming the last results read (Brazil held-out districts, Brazil held-out states without case history) → Supplementary Methods section F.
- 2.11: commit bd3ba50 is in Supplementary Methods section F and Code availability.
- 2.10: the "too many false positives in simulations" sentence is in Discussion 4.5 (14% to 18%) and Table S12.

**Results 3.1**
- Climate +0.57% (0.03 to 1.12), remote sensing and population +0.52% (0.18 to 0.86), and Colombia +0.30% (0.03 to 0.57) → Table S44.

**Results 3.2**
- Brazil held out: CI −0.94 to −0.42 → Table 2.
- Brazil held out, embedding-gain CI −1.34 to 0.55 → Table 2.
- Brazil held-out districts +0.20% (−0.32 to 0.71), Holm p 1.00 → Table 2.
- Peru held out, unadjusted p 0.088 → Tables S21 and S26.

**Results 3.3**
- 18% size at a nominal 5% → Table S12 (and the 14% to 18% range in Discussion 4.5).
- The list of six comparisons where the control made forecasts worse → Table 2 (‡).
- The sentence "At 2019, the selected control beat the reference model only in ..." → Table 2 (†) and Tables S22–S23.
- "No control" rule: Holm p < 0.001 to 0.035 and 0.005, and Brazil held out −0.39% (p = 0.39) → Table S45.

**Results 3.4**
- Seed SD 0.03% to 0.12% and 1.1% → Table S52.
- Peru held out, strict-variance check +0.93% (0.25 to 1.62), and all rows +0.99% → Tables S43 and S26.

**Results 3.5**
- Zero-row 0.9-quantile range +0.002 to +0.093 → Table S31.
- Zero-week interval widening 2% to 12%, 55% with Taiwan held out, significant in 13, and +2.1 percentage points → Table S48.
- Brazil 2020 value −0.22% → Tables S46 and S30.
- "None without 2020–2021" and "no Brazilian comparison gained in 2023–2024" → Table S46.

**Results 3.6**
- −0.13% to −0.94%, CI −0.25 to 0.29, p ≥ 0.15, and −2.11% to −6.28% → Table S36.

**Results 3.7**
- Similarity 0.70–0.82 and 0.95–0.99 → Table S40.
- Year-to-year cosine 0.98 vs 0.97 (sentence cut) → Table S49.

**Results 3.8**
- Brazil held-out states p = 0.19 and 0.27 → Table S42.
- Average past cases −0.24% and +1.85% beyond it → Table S42.
- Colombia −4.17% (−6.45 to −1.90) and −1.46% (−2.90 to −0.03) → Table S54.

**Results 3.9**
- Peru and Taiwan added R² −0.07 and +0.07 → Table S50.
- Variants −0.36% → −0.07%, −0.21%, −0.87% and Holm p 0.032 → Table S51.
- Tuning −0.39% → Table S55.

**Discussion**
- 4.1: "5 to 8 of 14" → Results 3.3 and Conclusions 4.7.
- 4.2: Taiwan zero-row 0.9 quantile +0.093 → Table S31.
- 4.3: 3.3% and 2.0% → Results 3.8 (3.30%, 1.98%) and Table S42.
- 4.3: minimum detectable effect 1.8% → Results 3.8 (1.80%) and Table S42.
- 4.5: the "COVID-19 years" sentence → Results 3.5.

Numbers added: none. The number-diff script finds only new table references (Table S14, Table S44, Table 2, Section 3.9), code letters in the new Table 2 key line, and punctuation changes (for example "2017," for "2017").

## Reviewer issues not applied, and why

- Glosses that would add numbers were not used: "10th to 90th percentile", "R², a 0 to 1 measure", "(1 means identical)", "just under 0.05", and "64 columns" in Results.
- "Identity confound" → "identity problem" (Haiku only) was not applied. The term is defined in plain words right before it.
- A gloss for gradient boosting in the abstract, and keeping "log(1 + cases)" there, were left out because of the 300-word limit.
- The Figure 1 caption was tightened and the control list was replaced by a pointer, but it was not cut to one sentence per panel. Panel C carries timing numbers that would otherwise disappear.
- The empty "Use of AI tools" heading was left as is, by design. The build inserts the statement at `<!-- AI-USE -->`.
- The rule-of-three sentence about the order of the selection rule was deleted rather than reworded.

## Checks run

- Grep of main-text prose (comments excluded) found:
  - no D-codes, "rule v2", "round 3", "blind", "cautious variance", "new years", "co-primary", "Notably", "Importantly" or "Taken together";
  - no em dashes;
  - "cell" only inside the Pradhan quotation.
- Number comparison against the v1e copies: no number added, and every removal is listed above.
