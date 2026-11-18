# CHANGES v1b: revision of draft v1 after the V2 brutal review and the number verifier

Date: 2026-11-18. Inputs: `../audits/review_round/V2_brutal_review_v1.md` (V2), `VERIFY_v1.md`, supervisor decisions of 2026-11-18, `STYLE.md` (read-only). Files changed: `00_front.md`, `01_introduction.md`, `02_methods.md`, `03_results.md`, `05_discussion.md`, `06_declarations.md`, `S1_supplement_methods.md`, `S2_supplement_results.md`. Not changed: `STYLE.md`, `refs_v1.bib`, `notes_A/B/C.md`, `VERIFY_v1.md`.

Every new number carries a `<!-- src: … -->` comment read from `docs/results/tables/*.csv`, `docs/results/review/*`, `docs/data/*` or `docs/plans/deviations_from_protocol.md`. One new literature fact (AlphaEarth inputs vs training targets) was read from Brown et al., arXiv:2507.22291v2, Table S1 and section S15; it is flagged in its src comment for the human reference check.

## Word counts

Counter: prose only; HTML comments, `[[…]]` markers, `[@…]` keys, LaTeX blocks, table rows and table captions excluded. "Incl. headings" also counts section headings (closest to the verifier's method).

| Part | Before (v1) | After (v1b) | Target |
|---|---|---|---|
| Abstract (incl. 4 labels) | 294 | 300 | ≤ 300 |
| Plain-language summary | 137 | 140 (V2's text) | ~120 |
| 1 Introduction | 890 | 830 | ~800 |
| 2 Methods | 2,071 | 2,042 | ~1,900 |
| 3 Results | 1,764 | 1,484 | ~1,500 |
| 4 Discussion | 1,887 | 1,532 | ~1,300 |
| **Main text, sections 1–4** | **6,612** | **5,888** | ≤ 6,000 |
| Main text incl. headings | 6,734 | 5,986 | ≤ 6,000 |
| Table 2 caption (excluded) | 222 | 158 | – |

Moved to the supplement: Table 2 columns (to S2-3 Part B), Results supporting-analysis and per-year detail (to S2-D and after S2-16), Peru similarity gradient (after S2-15), Peru S5 robustness note (after S2-5), Discussion bullets Calibration, Countries, Covariates and geometry, later-dated detail, Taiwan crosswalk and the inference detail (new S1 section I), Methods robustness paragraph and margin anchors (S1-F1, F2), Colombia completeness percentile (S1-B4), Holm-adjusted MDE factor and the HLN note (S1-F1).

## V2 issues

### CRITICAL

| ID | Status | Where | Note |
|---|---|---|---|
| C1 AI use | done (per supervisor rule) | 06 "Use of AI tools" = `[[AI-USE: full statement in the shared doc]]`; 02 §2.1 new sentence; S1 new paragraph "Who did the work described here"; S1-B1 verification script, S1-B3 pinyin and crosswalk review (was "by hand"), S1-B7 table title, S1-D fold check, S1-E rows 13 and 17 ("automated AI-agent audit"); 05 §4.5 "independent checks" → "district-level checks of filled zeros against independent sources" | STYLE rule kept (not V2's "replace the STYLE rule"); no product named. |
| C2 pending results | done (markers kept) | all files | No result invented. New marker `[[PENDING: no-history C6 test years (RH)]]` (H3). Abstract, plain summary, 4.1, 4.3, 4.7 must be reread as prose after the fill. |
| C3 production blockers | partly | 06 Data availability: Copernicus attribution added; licence marker for MODIS/VIIRS/GHSL; deposit sentence | Skipped (author input or outside my files): corresponding author, ORCID, funding, COI, CRediT, consent, licence, Internet Archive URL, CC BY-SA version, GBD numbers, public repo/DOI, Figure 1 drawing, compiled PDF, official EPIFORGE file, kit figure titles (F1 "best location control", FS1/FS2 "log1p WIS"; regenerate in the kit). |

### HIGH

| ID | Status | Where | Note |
|---|---|---|---|
| H1 harm claims | done | Abstract Findings; plain summary; 4.1; 4.7 | Six losses after Holm: five small, one large relative to a low baseline (Taiwan S5, absolute 0.0035); two (BR S5, CO S2) significant under both cautious checks (T1 B4_Holm_p, p_iaaft_Holm). "Clearly"/"substantially" removed everywhere. |
| H2 null and equivalence claims | done | Abstract (8 of 13 cells, Holm-adjusted TOST, T1b); plain summary (V2 text verbatim); 4.1; 4.7 | 4.7 no-history sentence reworded from V2's "at least as much as" to "coordinates improved forecasts while embeddings alone did not detectably": coordinates vs embeddings was never formally compared. No "nothing"/"no meaningful" left (one "nothing" in 2.4 removed). |
| H3 no-history reading | done | 03 No-history arm (T4 2019: C6 0.3472, C2 0.3463, C4 0.3490, C3 0.3596 vs N3 0.3543); 05 §4.3 V2 paragraph; "location proxy" in 4.3, 4.7 and glossary; marker in 03, 05, S1-E row 38, S1-F5; 02 §2.10 discloses D38 | Title unchanged. "Placeholder" now appears only for the history arm in 4.1 ("place versus placeholder cannot be settled"). |
| H4 generic dimensionality | done | 03 Fixed control panel (S2_control_panel C3 G_id −0.12/−0.76/−0.59 vs G_emb −0.36/−0.94/−0.94; T4 2019: C4 and C5 worse than L3 in 13/13, C4s 9/9, C3 12/13); 05 §4.2 | Taiwan panel rows are without 2021 (stated). |
| H5 null not specific | done | 05 §4.1 new paragraph (S1_baselines rel WIS, ≤ 0.01); §4.6 longer horizons; S1-G item 13 | |
| H6 undeclared deviations | done | 02 §2.11 ("all 38", D24–D38, three commitments not carried out); S1 contents, E title, E intro, rows 35–38 added; S1-F5 rows; 05 §4.5 new "Short training window" bullet | Rows 35–38 copied from `docs/plans/deviations_from_protocol.md`. |
| H7 third-party timestamp | done (text); deposit itself needs authors | 02 §2.11 and 06 Code availability: "deposited at [[AUTHORS: deposit DOI]] on 18 November 2026, before the Brazil S4 and no-history Brazil S2 results were read"; 05 §4.5; S1-G items 9 and 16 | "Pre-specified (commit X)" wording kept. |

### MEDIUM

| ID | Status | Where |
|---|---|---|
| M1 excess-gain definition | done | 02 §2.8 ("once the model also has the validation-selected location control"); §2.4 new S1 vs S2–S5 paragraph |
| M2 "no district-specific inputs" | done | 02 §2.3 |
| M3 Colombia filled weeks | done | 02 §2.2 (ratio about 1), S1-B4 (10th percentile ≥ 0.79), 05 §4.5 "Filled zeros" |
| M4 recorded zeros vs year | done | 03 "Where the difference arises" (2021 lowest in every Brazilian cell, S8); 05 §4.2 old claim removed |
| M5 margin justification | done | 02 §2.9 (protocol origin of 1%, 0.0017 ≈ 0.2% ratio, TimesFM 13%); S1-F1 Margin (scale mismatch of the hub anchor) |
| M6 secondary estimands unadjusted | done | 03 "Secondary estimands, unadjusted" |
| M7 L3 transfers well | done | 03 Taiwan section (WIS_L3 PE 0.2362 vs 0.2418, TW 0.0202 vs 0.0312); 05 §4.2 |
| M8 capacity caveats | done | 03 (earlier control selection); 05 §4.2 (five of six loss cells use 31 leaves); ratio stays the v3 value in S1-D |
| M9 seed noise | done | 05 §4.5 Inference (T1 seed_sd 2.03e-5 vs 3.89e-4; row 16; C3 cells) |
| M10 "satellite-only" | done | 01 ¶2 and ¶4; 05 §4.2 redundancy sentence | Inputs are Sentinel-2, Landsat 8/9, Sentinel-1; ERA5-Land, DEM and others are training targets only (arXiv:2507.22291v2 Table S1). Needs the human reference check. |
| M11 RQ answers | done | 05 §4.1 first paragraph |
| M12 length and structure | partly | Main text 5,888; Table 2 cut to Cell, C\*, WIS(L3), excess gain, Holm p, label (rest in S2-3 Part B); inline D labels in Methods limited to D2, D19, D24, D34 plus D38; robustness paragraph to S1-F; plain split names in Results prose; per-year and supporting detail to S2; three Discussion bullets to S1-I. Not done: Table 1 (data table) left as is; Table 2 keeps the T1 label text, shortened only by dropping the repeated "(TOST, Holm-adjusted)". |
| M13 EPIFORGE | partly | S1-G items 6, 9, 13, 16, 17 updated; `[[CITE]]` markers were already replaced. Skipped: the official checklist file (authors must download and fill it). |
| M14 plain summary uncertainty | done | Plain summary ("in most settings we could rule out improvements larger than 1%") |

### LOW

| # | Status | Where / note |
|---|---|---|
| 1 district counts | done | 01 ¶5 "(6,909 scored in the test years)"; Table 1 caption. Abstract keeps 6,987 (word limit; src comment gives 6,909). |
| 2 wrong estimand name | done | Already fixed by the verifier; panel paragraph removed from 4.3; 4.4 uses +0.29% → +0.02% |
| 3 Pradhan pattern | done | 05 §4.4 |
| 4 Taiwan similarity statistic | done | 03 uses S7b only; 05 §4.2 refers to Results; RB 0.77 and ρ −0.10 removed |
| 5 "can only favour" | done | 02 §2.6, 05 §4.5 ("expected to favour"); S1-I |
| 6 "pre-stated rule" | done | 02 §2.2; S1-B5 |
| 7 HLN on pooled horizons | done | 02 §2.9; S1-F1 |
| 8 renormalisation | done | 05 §4.5 "One representation" |
| 9 licences | partly | Copernicus attribution added; MODIS/VIIRS/GHSL need authors (marker in 06) |
| 10 Intro ¶3 two threats | done | 01 ¶3 |
| 11 counts and "pre-specified" family | done | "Eleven" in 02 and 05; Intro item 3 "fixed before any spatial-split result was seen" (no D12 label, to keep inline labels thin) |
| 12 strengths claim | done | 05 §4.5 |
| 13 WIS(L3) week vs row means | done | Table 2 caption; new S2 preamble |
| 14 glossary gaps | done | S1-H: 16 rows added (embedding, cosine similarity, quantile, location control, location proxy, Mondrian recalibration, delta method, zero-shot, spherical harmonics, booster/leaves, fixed-b, outbreak week, identity confound, k-means, correlogram, area of applicability) |
| 15 "small" by point estimate | done | Table 2 caption; 03 text |
| 16 C4 at 8,483 km | done | 02 §2.4 |

### Readability section (V2 §3) and resolution-log gaps (V2 §5)

- Passages 1–5 and the C\* rule: rewritten as proposed (abstract, 2.9, 2.6, Results robustness, Results secondary estimands, 2.4).
- Jargon: booster/leaves, zero-shot, spherical harmonics and "rescaled to unit length" explained in 2.3–2.4; fixed-b, cosine terms, IAAFT, delta method, Mondrian and "quintile means of maximum cosine" removed from or rephrased in the main text; k-means and correlogram replaced by plain wording.
- EXT-C10 (other Taiwan explanations): done, 4.2. EXT-C11 (equal-budget per-level tuning): done, 4.6. F-C3 (lay test explanation): done, 2.9. F-C8 (internal margin anchor): done, 2.9.
- Skipped, need new analyses: EXT-C5 false-zero scenarios; EXT-C12 sharpness reporting; V2 optional long-window L0–L3 run (logged as D35 instead).

### Pre-kit-v3 numbers

- Replaced by v3 tables: Taiwan similarity in 4.2 (RB → S7b/Results); RB "harm largest in districts with no case" removed from 4.2.
- Kept and labelled "(computed before the origin-year filter and the Espírito Santo exclusion)": RB strata (03 Supporting analyses, S2-D, S2-17 title); RC size simulation (05 §4.5 Inference, S1-F1 table caption, S1-I).
- RE panel (S2_control_panel.csv) is a v3 table but Taiwan lacks 2021; stated wherever used.
- RG: main text uses T1/T6a; only S2-14 (2021 rows on their own, v3) still cites RG.

## Remaining markers (all files)

| Marker | Count | Locations (file:line) |
|---|---|---|
| `[[PENDING: BR S4]]` | 20 | 00:20; 03:15, 25 (×2); 05:9; S2:27, 49, 78, 91, 115, 137, 160, 184, 208, 228, 248, 382, 455, 457, 463 |
| `[[PENDING: BR C3/C6 panel]]` | 13 | 02:57; 03:61; S1:383; S2:275 (×2), 276 (×2), 302–307 |
| `[[PENDING: BR S2 no-history]]` | 8 | 00:20; 03:71; 05:25; S2:323, 324, 325, 434, 459 |
| `[[PENDING: sensitivities yref/delay2]]` | 7 | 02:147; 03:57; 05:35; S1:384, 385; S2:300, 301 |
| `[[PENDING: final Holm m=14]]` | 6 | 00:20; 02:145; 03:15, 17; 05:9; S2:115 |
| `[[PENDING: no-history C6 test years (RH)]]` (new) | 4 | 03:71; 05:25; S1:304, 393 |
| `[[PENDING: BR S1 no-history N4+C1]]` (not in STYLE list) | 1 | S2:448 |
| `[[AUTHORS: TBD]]` | 7 | 00:11, 12; 06:42, 48, 54, 66, 72 |
| `[[AUTHORS: repo public + Zenodo DOI]]` | 5 | 06:32, 36; S1:412, 415, 422 |
| `[[AUTHORS: deposit DOI]]` (new) | 4 | 02:155; 06:36; S1:415, 422 |
| `[[AI-USE: full statement in the shared doc]]` (new) | 1 | 06:60 |
| `[[AUTHORS: confirm and state the MODIS, VIIRS and GHSL licence terms …]]` (new) | 1 | 06:29 |
| `[[AUTHORS: confirm licence for derived data]]` | 1 | 06:32 |
| `[[AUTHORS: confirm that no institutional review …]]` | 1 | 06:13 |
| `[[AUTHORS: ...]]` (inside a comment) | 1 | 06:3 |
| `[[VERIFY: exact Internet Archive snapshot URL]]` | 1 | 06:10 |
| `[[VERIFY: CC BY-SA version number]]` | 1 | 06:27 |
| `[[GBD: authors to pull from IHME]]` | 1 | 01:3 |

## Open points for the supervisor

1. The deposit sentence states a date (18 November 2026). It is true only if the authors actually deposit today, before Brazil S4 and no-history S2 are read; otherwise use V2's fallback wording ("recorded in commit X, dated …").
2. `[[PENDING: BR S1 no-history N4+C1]]` (S2-19) is outside the STYLE marker list: add it to the Thursday fill or drop the row.
3. The plain summary is 140 words (V2's text applied verbatim against a ~120 target); dropping its first sentence would save 13.
4. Kit figure titles (F1, FS1, FS2) still need regenerating outside `paper/v1/`.
