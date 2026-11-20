# Changes in draft v1c (round-3 referee reports, 2026-11-19)

Scope: main text and references only (`00_front.md`, `01_introduction.md`, `02_methods.md`, `03_results.md`, `05_discussion.md`, `06_declarations.md`, `refs_v1.bib`). The supplement (`S1_supplement_methods.md`, `S2_supplement_results.md`) is edited by another agent. Binding spec: `audits/final_round/TRIAGE_round3.md` section A, plus two supervisor updates on 2026-11-19 (first round-3 results for R3-A2, R3-A4 and R3-A7; regenerated figures and captions; deviation rows 39–52 in the supplement).

Status words: **Done** = changed in the text. **Pending R3** = the text is written and marked `[pending]` with `<!-- PENDING: ... -->`; it is filled when the round-3 analysis lands. **Authors** = needs an author action, marked `[to be completed]` / `<!-- AUTHORS -->`. **Declined** = not done in the preprint, with a reason. **Other owner** = belongs to a file this agent does not edit.

## Lengths (comments, display equations, tables, table notes, figure captions and headings excluded)

- Abstract: 298 words (limit 300).
- Main text: about 6,960 words (Introduction 829, Methods 2,770, Results 1,761, Discussion 1,601). v1b was 6,010 on the same count. The increase comes from the required additions (co-primary embedding gain, the full post-result change list in 2.12, Section 2.13, the no-history identifier panel, the scope limit). Further cuts are possible in 3.6 and 4.2 if the authors want 6,000.

## Global changes

- **Title:** "Place or placeholder? Satellite embeddings and location controls in weekly district dengue forecasting across four countries" (A.1).
- **Abstract** rewritten (A.1–A.3, A.6, supervisor update): it answers the question explicitly; it leads with Colombia held-out states, the only loss robust to both cautious variance estimators and to the "no control" rule; Taiwan held out is "not robust"; the equivalence count is tied to the variance estimator and anchored to Brazil's covariate stack; the outcome-agnostic sentence "Embeddings raised upper forecast quantiles"; "may worsen transfer"; "inconclusive" without case history; 6,909 scored districts.
- **"Identity gain" → "control gain"** everywhere in the text, equation (3) now uses Δ_ctrl, and a note says code and CSVs keep G_id (A.4).
- **Embedding gain co-primary**: Table 2 has an embedding-gain column; 2.9 and 2.10 explain; Figure 2 caption covers both gains (A.4).
- **Split names** unified: new years (S1), held-out states (S2), held-out regions (S3), held-out districts (S4), held-out country (S5) (A.10).
- **Supervisor update 1 (R3-A2/A4/A7)**: Brazil held out is described as robust to the variance estimators but present only beside the noise control (embedding gain −0.34%, p = 0.44 from T1); under the "no control" rule only BR S1 and CO S5 keep a control, and the Holm-significant losses are CO S1–S4 and TW S5 (exact Holm values `[pending]`); equivalence is stated to depend on the variance estimator (B=4 + Holm count `[pending]`); embedding year-to-year instability is offered as a candidate explanation in 4.2 and described in 3.7 (exact values `[pending]`).
- **Supervisor update 2 (figures)**: Figure 1–4 captions adapted from the regenerated `docs/results/figures/pub/CAPTIONS.md`, checked against Fig 2 by eye; supplementary figure references now S1 = ladder, S2 = per-year, S3 = similarity, S4 = probe; supplementary table references S43–S55 follow the supplement editor's rows 39–52; 2.12 now counts 52 dated changes.

## Referee A (journal referee)

| Comment | Status | What changed (file, section) |
|---|---|---|
| M1 Title and framing | Done | New title (00); Abstract Interpretation answers the question; 4.1 ¶2 and 4.7 say the identity question did not arise with case history and use "consistent with, but does not establish" (05). |
| M2 Harmful controls; no "no control" option | Done + Pending R3-A2 | Table 2 flags † (control beat L3 at 2019) and ‡ (control-gain CI below zero) and \* (noise control in S5) (03 Table 2); 2.5 justifies the priority order, states no control was not a candidate and adds the "no control" sensitivity rule (02); 3.3 reports that only BR S1 and CO S5 kept a control and which losses survive (03); embedding gain co-primary. |
| M3 Per-year trend | Done + Pending R3-A3 | Per-year Brazil series in 3.5 with the COVID caveat and the trend test placeholder; 4.5 states the rise and that longer histories are untested (03, 05). The optional static-embedding run is V3 in R3-C. |
| M4 Loss claims and "worsened transfer" | Done | Abstract leads with the robust loss; TW S5 "not robust"; "may worsen transfer" (00, 05 4.7); 3.2 and 3.4 give the robustness pattern; drift caveat on equivalence (03 3.3). Size-simulation rerun is R3-A8 (optional, analysis agent). |
| M5 Post hoc, weakly anchored margin | Done + Pending R3-A1, R3-A4 | 2.10 states the margin was chosen after the BR and PE new-years results and adds the ladder anchor and ±0.5% (02); 3.1 and 3.3 give the Brazil/Colombia covariate-stack sizes from T2 (row means) and the ±0.5% result (03); Table 2 adds absolute differences; abstract wording anchored. |
| M6 Positive control | Pending R3-A1 | 3.1 and 4.1 ¶3 frame it; 4.1 makes task insensitivity the key scope limit (03, 05). |
| M7 Pre-specification | Done + Pending R3-A5 + Authors | 2.12 rewritten: exact timing split of all 52 rows, all seven post-result changes that alter primary numbers incl. D21, D22 and D25 (with the TW numbers); Intro ¶6 says family membership was fixed before held-out results while rows and Taiwan's years changed after review; deposit sentence conditional with an AUTHORS note; Table S43 referenced (01, 02, 06). |
| M8 Outcome-conditioned strata | Done + Pending R3-A6 | Lerch et al. 2017 cited (2.8, 3.5, 4.2); strata labelled descriptive (2.8, 3.5 heading sentence, Fig 3 title); outcome-agnostic abstract sentence; 4.2 discusses possible calibration gain on case weeks and false zeros in Colombia (02, 03, 05). |
| M9 Single seeds | Pending R3-C (EXP-B seeds) | 2.13 states the three-seed rule; Table 2 note and 3.4 placeholders; 4.5 keeps the seed caveat (02, 03, 05). |
| M10 Splits do not remove the identifier route | Done | Intro ¶4 and ¶6, 2.6 ¶2 and 4.1 ¶2 say what S2–S4 remove and what they do not (01, 02, 05). |
| M11 Row sets and WIS values | Done + Pending R3-C (TW ladder with 2021) | 2.9 defines week weighting and says row means are labelled; 3.8 uses week-weighted 0.1675 / 0.3520 and labels the row means; 3.1 and 3.6 say "Taiwan without 2021"; Table 1 says Taiwan includes 2021 (02, 03). |
| M12 Captions vs figures | Done | Figure 1–4 captions replaced from the regenerated CAPTIONS.md; file comments point to `pub/` (02, 03). |
| minor 1 District counts | Done | 6,909 in Abstract and Intro; Table 1 note explains 6,990 / 6,987 / 6,909 (00, 01, 02). |
| minor 2 Signed zero | Done | Table 2 BR S2 "0.00", Holm "1.00". The figure prints "1.0" (figure owner). |
| minor 3 Ambiguous loss range | Done | Losses now named by cell (00, 03 3.2). |
| minor 4 Two Brazil values | Done | Table 2 uses the 3-seed values; 3.6 and 4.4 label the panel value "seed 0". |
| minor 5 Contribution vs stratum CI | Done | 3.5 drops the p = 0.048 stratum claim and reports the additive contribution (−0.22, CI −0.46 to 0.02). |
| minor 6 2.12 vs deviation log | Done | 2.12 gives the exact split (D1–D23, 11 with S1 results in view; D24–D34; D35–D38; D39–D52). |
| minor 7 TW 2019 selection noisy | Done | 3.6 last sentence. |
| minor 8 Holm worst case for BR S4 | Done | 2.10: every loss keeps Holm p < 0.05 for any 14th p (largest 0.029), computed from T1 DM_p. |
| minor 9 TW without 2021 in Table 2 | Done | Table 2 note gives both no-2021 estimates. |
| minor 10 Shared tuning | Pending R3-C (EXP-B S4) | 4.2 ¶3. |
| minor 11 Dimensionality vs content | Pending R3-C (V2 PCA-8) | 4.2 ¶2, 3.9. |
| minor 12 Jargon | Done | "Cell" and "origin" defined in 2.1; glossary pointer; one split name set; EWC and HLN glossed; "origin-year rows" replaced by plain wording in the main text. C\* and L-codes kept where tied to equations and figures. |
| minor 13 Eq. (1) normalisation | Done | 2.8: median plus K = 4 intervals; not comparable with 23-quantile hub WIS. |
| minor 14 Inference population | Done | 2.10 and 4.5. |
| minor 15 Reporting-delay sentence | Done | Sentence removed from Limitations (the delay sensitivity is still pending); delays kept as future work. |
| minor 16 Literature | Done (partly) | Added Lerch 2017, Rolf 2021 (MOSAIKS), Wadoux 2021, Gneiting & Raftery 2007 (all DOI-verified). Lowe et al.: the existing `lowe2016elife` (Brazil) stays in the Introduction; no separate climate-lag paper was added because none was verified in this round. Brittain's different target scale stated in 4.4. |
| minor 17 Reporting statements | Authors | AUTHORS notes in 06 (deposit, public repo, human checks in the AI-use statement). EPIFORGE items are in the supplement (other owner). |
| minor 18 Ethics | Authors | AUTHORS note in 06 asks for an exemption statement or determination. |
| minor 19 Units in 3.7 | Done | "× 10⁻⁴ log-WIS". |
| minor 20 Denominator of 1.41% | Done | 2.2: 38,766 of 2,741,949 rows. |
| minor 21 Soften 4.4 | Done | 4.4: "though neither differed from zero". |

## Referee B (ML referee)

| Comment | Status | What changed |
|---|---|---|
| M1 Positive control / scope | Done + Pending R3-A1, R3-E1 | 4.1 ¶3 names task insensitivity as the key scope limit, with REVISIT wording for either probe outcome; 2.13 and 3.9 describe the probe. |
| M2 One representation | Pending R3-C (V1–V3) | 2.13, 3.9, 4.2. **Declined for the preprint:** unweighted-mean and raw-mean-plus-norm variants (not in the triage); the norm limitation stays in 4.5. |
| M3 Tuning/capacity | Pending R3-C (EXP-B S4, Colombia) | 4.2 ¶3; per-level Brazil result already in 3.5. **Declined for the preprint:** Brazil equal-budget tuning (triage D; named as future work in 4.6). |
| M4 One model class | Declined (triage D) | Stated as a limitation (4.5) and future work, including the TimesFM residual design (4.6). |
| M5 Margin too wide | Done + Pending R3-A1, R3-A4 | As RA M5; ±0.5% reported alongside (2.10, 3.3); abstract wording anchored. |
| M6 Year-to-year variation | Done (text) + Pending R3-A7, V3 | 3.7 and 4.2 (candidate explanation per supervisor update). |
| M7 Estimand vs splits; control roles | Done | Co-primary embedding gain; "control gain"; 2.5 ¶2 says no control tests identity with case history; C3 within-country and noise-control role; C2 degree-8 resolution stated (2.5). |
| M8 Taiwan harm as country/regime transfer | Done (text, partly) | 4.2 ¶4 offers country case definition and reporting level as the explanation; absolute values beside the % in Table 2, 3.2 and Fig 2. **Declined:** making the absolute effect the primary measure for one cell (would break the common family scale); country-centred embeddings deferred (triage D, 4.6). |
| M9 Small losses near seed noise | Done (text) + Pending seeds | Abstract and 3.2 lead with the robust loss; seeds placeholders. |
| M10 Title question; no-history arm | Done + Pending R3-C (CO S2 no-history) | New title; 2.11, 3.8, 4.3. **Declined for the preprint:** N3-specific tuning (triage D; 4.6). |
| M11 Substitution L2+AE | Pending R3-C (V4) | 2.13, 3.9. |
| M12 Positioning | Done | Pradhan novelty stated (01 ¶5, 04 4.4); MOSAIKS, GeoCLIP, GEO-Bench cited (01, 05); PDFM named as the main external-validity gap (4.5). |
| M13 Reproducibility | Done + Pending (core-hours) + Authors | 2.4: no early stopping, 400 rounds, what the seed controls, training-set size example; 06: derived district-year embedding table to be released with the code; core-hours `[pending]`. Tuning-criterion data size is in Supplementary Methods C (other owner). |
| minor 1 Split naming | Done | One name set. |
| minor 2 Fig 2 caption | Done | Rewritten for the regenerated figure. |
| minor 3 Fig 3 caption | Done | Totals printed as text; off-scale arrow described. |
| minor 4 Fig 4 caption | Done | Pooled only, CIs in panel B, row-mean vs week-weighted denominators explained; "control gain". |
| minor 5 Broken sentence in 3.2 | Done | Paragraph rewritten. |
| minor 6 −0.00 and absolute column | Done | Table 2. |
| minor 7 Fig 1A legend C6 | Done (caption) / Other owner (drawing) | Caption mentions C6; drawing handled by the figure agent. |
| minor 8 Jargon | Done | As RA minor 12. |
| minor 9 Coverage on case weeks | Pending R3-A6(b) | 3.5, 4.2. |
| minor 10 Quantile crossing not logged | Declined | Needs refitting to log pre-sort crossing; the supplement states that crossing before sorting was not logged. |
| minor 11 Embedding missingness (Noronha) | Other owner | Stated in Supplementary Methods A7; removed from the main text for length. |
| minor 12 District counts | Done | 6,909 throughout. |
| minor 13 Absolute values | Done | Table 2 absolute column. |
| minor 14 TW S5 used 127 leaves | Done | 4.2 ¶3. |
| minor 15 AlphaEarth training overlap | Done | 4.5: training imagery "2017 to present" (Brown et al. §S15), favours the embeddings, strengthens the null. |
| minor 16 Strata descriptive | Done | 2.8, 3.5, 4.2, Fig 3 title. |

## Referee C (reproducibility audit)

| Comment | Status | What changed |
|---|---|---|
| H1 Figure–caption mismatch | Done (main text) / Other owner (supplement captions) | Main captions replaced; S-figure references renumbered to the `pub/` files. |
| H2 D25 and D21 omitted | Done | 2.12 lists both with the TW numbers; Intro ¶6 rewritten. |
| H3 Deposit claim, declarations | Authors | Deposit sentence conditional (AUTHORS notes in 02 and 06); GBD numbers and declarations still `[to be completed]`. |
| M1 Two definitions of mean WIS | Done | 2.9, 3.8, Fig 4 caption. |
| M2 TW numbers without 2021 | Done | 3.1, 3.6. |
| M3 C3 description | Done | 2.5: "a few districts keep their own". |
| M4 Selection rule wording | Done | 2.5: two standard errors of the difference, pooled seed SD; no control was not a candidate. |
| M5 Failing test | Other owner | Code fix, not a manuscript file. |
| M6 Buffer wording | Done | 2.6: deseasonalised residuals; pointer to section D3. |
| L1 "about 0.1" | Done | 3.4. |
| L2 District counts | Done | As RA minor 1. |
| L3 "at most 0.01" | Done | 3.1: L4 + C\* vs L1. |
| L4 D35–D38 timing | Done | 2.12. |
| L5 E3 power sentence | Other owner | Supplement. |
| L6 NaN C1 note in Table S7 | Other owner | Supplement. |
| L7 Unverified numbers | Authors | Human reference/number check before posting. |

## Tally

78 referee comments (RA 12 major + 21 minor; RB 13 major + 16 minor; RC 16):

| Status | RA | RB | RC | Total |
|---|---|---|---|---|
| Done in the main text | 21 | 16 | 11 | 48 |
| Text done, numbers pending R3 | 6 | 6 | 0 | 12 |
| Pending R3 only | 4 | 4 | 0 | 8 |
| Needs the authors | 2 | 0 | 2 | 4 |
| Other owner (supplement or code) | 0 | 1 | 3 | 4 |
| Declined | 0 | 2 | 0 | 2 |

Declined in full: RB M4 (second model class; triage D, stated as limitation and future work) and RB minor 10 (pre-sort quantile crossing cannot be logged without refitting). Declined in part: RB M2 (unweighted and raw-plus-norm variants), RB M3 (Brazil equal-budget tuning; triage D), RB M8 (absolute effect as the primary measure for one cell; country-centred embeddings deferred, triage D) and RB M10 (N3-specific tuning; triage D).

## References

Added to `refs_v1.bib` after checking the Crossref record of each DOI and, for the NeurIPS papers, the proceedings.neurips.cc abstract page (2026-11-19):

- `lerch2017dilemma`: Lerch, Thorarinsdottir, Ravazzolo, Gneiting. Statistical Science 32(1):106–127, 2017. doi:10.1214/16-STS588.
- `rolf2021mosaiks`: Rolf, Proctor, Carleton, Bolliger, Shankar, Ishihara, Recht, Hsiang. Nature Communications 12:4392, 2021. doi:10.1038/s41467-021-24638-z.
- `vivanco2023geoclip`: Vivanco Cepeda, Nayak, Shah. NeurIPS 36 (Main Conference Track), pp. 8690–8701, 2023. doi:10.52202/075280-0379.
- `lacoste2023geobench`: Lacoste et al. (17 authors). NeurIPS 36, Datasets and Benchmarks Track, pp. 51080–51093, 2023. doi:10.52202/075280-2223.
- `gneiting2007proper`: Gneiting, Raftery. JASA 102(477):359–378, 2007. doi:10.1198/016214506000001437 (RA minor 16).
- `wadoux2021spatialcv`: Wadoux, Heuvelink, de Bruin, Brus. Ecological Modelling 457:109692, 2021. doi:10.1016/j.ecolmodel.2021.109692 (RA minor 16).

None was rejected. No separate Lowe et al. climate-lag paper was added (the existing Brazil reference `lowe2016elife` is kept).

## For the fill pass

- Search for `PENDING` and `REVISIT` in the six files. The abstract, 3.2–3.4, Table 2 and 4.1 change if seed-averaged estimates replace seed-0 values (D49).
- Recount the abstract after the fill (limit 300).

## v1d fill pass (2026-11-20)

Files: 00_front.md, 01_introduction.md, 02_methods.md, 03_results.md, 05_discussion.md (06_declarations.md unchanged). Word counts (comments, equations, tables, captions, table notes and headings excluded): abstract 300 (labels included); main text 6,299 (Introduction 785, Methods 2,553, Results 1,782, Discussion 1,179), down from 6,961.

### Filled (round 3; sources in `<!-- src: -->` comments)
- R3-A1 positive control: Results 3.1 (Brazil climate +0.57%, RS/pop +0.52%, all non-case +1.09%; Colombia RS/pop only; Peru and Taiwan none, Taiwan with 2021); margin anchor in 3.3 (±1% = 0.92× Brazil's L1→L3 gain, 2.3× Colombia, 5.8× Peru); Discussion 4.1 scope limit; abstract.
- R3-A2 "no control" rule: 3.2 (CO S2 Holm p 0.001) and 3.3 (Colombia within-country Holm p 0.001–0.046, TW S5 0.004, BR S5 not significant).
- R3-A3: 3.5 per-year paragraph rewritten to "no detectable trend" (smallest scaled p 0.096; none excluding 2020–2021; COVID caveat); 4.5 limitation rewritten.
- R3-A4: 3.3, 4.1, 4.7 and abstract (B = 4 + Holm: 6 at ±1%, 0 at ±0.5%; four of the six are also losses).
- R3-A5: Methods 2.12 (Table S43 no longer pending) and a new Results 3.4 paragraph (PE S1 sign flip under per-level tuning; TW S1 nominal loss fragile; PE S5 nominal with B = 4 or all rows; BR S3 nominal under exclusions v1).
- R3-A6: 3.5 (zero-week widening 12/13; case-week coverage toward nominal only PE S5; Colombian loss persists in case district-years; TW S5 −17.3% → −3.4%); 4.2.
- R3-A7: 3.7 (stability; own next-year match 57/84/94/69%).
- R3-A8: 3.3 (BR S1 drops out of ±1% after IAAFT calibration) and 4.5 (size 14–18% in four cells; conservative in loss cells).
- R3-E1 information probe: new 3.9 paragraph; Methods 2.13 design sentence; Abstract Findings and Interpretation; Discussion 4.1 ("real place information, but redundant") and 4.7; MOSAIKS link in 4.4.
- R3-C variants: 3.9 and 4.2 (no representation helps; V1/V2 shrink the loss, a dimensionality cost; V3 static does not remove it; V4 does not substitute).
- R3-C seeds: 3.4 (three-seed means, same six Holm-significant losses, seed SD, PE S1 nominal); abstract "seed choice"; 2.12 adds D49 to the post-result changes that alter primary numbers (now eight).
- R3-C tuning: 3.9 and 4.2 ("separate tuning chose the shared configuration").
- R3-C Taiwan 2021: 3.1 baselines and coverage, 3.6 control panel (all Taiwan values now with 2021; "without 2021" caveats removed).
- R3-C Colombia S2 without case history: 3.8, 4.3, abstract, conclusions ("results differ between countries; exploratory"); Methods 2.11 (D51).

### Left pending (blinded until the final kit)
BR S4; BR S2 without case history; BR S1 C3/C6 panel; final Holm over 14; Table 2 and Figure 2 values (every Table 2 row, the Figure 2 caption, abstract T1 values and seed-0 T1 values in 3.2–3.4, 4.1, 4.6 and 4.7 carry `<!-- REVISIT final kit (3-seed, m=14) -->`). Also still pending: total core-hours (Methods 2.4; no total in the round-3 docs). The BR S1 yref/delay sensitivities are not cited in the main text.

### Cut
- Methods: 2.5 condensed; the worst-case 14th-cell Holm sentence in 2.10 removed (it used seed-0 p values); 2.11–2.13 rewritten and shortened; small cuts throughout.
- Results: zero-share sentence (duplicated Table 1); coverage-change sentence (now covered by R3-A6); Tables S21–S23 pointer; per-model zero-stratum paragraph; 2019 control-selection sentences in 3.6; Taiwan 2021 denominator sentence moved into the Table 2 note; repeated robustness wording in 3.2.
- Discussion: 4.1 compressed; 4.2 rewritten around the new mechanism evidence (larger-tree paragraph and Peru similarity correlation dropped); 4.4–4.7 shortened; unit-length rescaling limitation dropped (remains in Supplementary Methods, section I).
- Introduction: pre-specification sentence moved out (it is in 2.12); four research questions condensed.

### Claims changed by the new results
- Brazil new years is no longer described as equivalent without qualification: after IAAFT calibration its CI crosses +1%.
- "Year-to-year noise may add to this" (4.2) was replaced: the static variant did not remove the loss, so noise is not the explanation.
- "The excess gain rose with each added training year" (4.5) became "no detectable trend".
- The no-history conclusion now says the two countries disagreed; the Brazilian coordinate pattern did not replicate in Colombia.
- Peru new years becomes a nominal (not Holm-significant) loss under three seeds, and changes sign under per-level tuning.
