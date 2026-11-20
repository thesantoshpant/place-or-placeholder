# v1e supplement fill pass (2026-11-20)

Sources: final results kit (`docs/results/tables/*.csv`, 14 cells, Holm m = 14, seeds 0–2 where they exist), `docs/results/FINAL_RESULTS_BRIEF.md`, `docs/results/review/R3_*.csv` (rerun on 14 cells), `RE_control_panel.csv` / `S2_control_panel.csv`, `FINAL_br_nohist_C1_rung.csv`, `RH_nohist_c6.md`, `docs/results/figures/pub/CAPTIONS.md`. Table rows were regenerated from the CSVs by a read-only script on the GPU (`tmp/final/supp_fill/gen.py`, `fmt.py`, `splice.py`) with the supplement's rounding rules, then diffed against the previous text.

## Compute total (task 1)
- `paper/v1/_compute_total.txt`: about 4,700 core-hours (4,662.1), wall seconds × threads over all 6,180 completed chunks in `runs/*/chunks/*.done.json` (GPU script `tmp/final/compute_total/compute.py`). Breakdown: history arm 2,446.5 (3,326 chunks), no-history arm 895.0 (804), round 3 809.5 (1,722), review sensitivities and panels 511.2 (328).
- The earlier 2,374 core-hours / 3,202 chunks figure skipped the 146 early serial chunks whose `.done.json` lacks a `threads` field; these now take threads from `config_resolved.yaml` (16).
- S1 "Total compute" paragraph rewritten with the total and breakdown (consistent with the main text's "about 4,700 core-hours").

## S2_supplement_results.md
- **Regenerated from the final kit** (all rows, Brazil held-out districts added where the table is per cell): Tables S17–S34, S36 (Brazil C3/C6 rows), S37, S39 (Brazil S4 row added), S40.
  - Notes updated: seeds (L3 to L4 + C\* now seed-averaged in all new-years cells and in Brazil S5, Colombia S1–S4; Peru/Taiwan S5 G_emb/G_id seed 0), Holm over 14 cells, Taiwan 141,645 rows.
  - S24 count row: of 14 cells, 2/2, 9/8, 13/12.
  - S26 note: PE S5 surrogate Holm p 0.04998 (at the threshold); seed SD vs SE sentence for three-seed cells.
  - S28/S29: extra row "Brazil, held-out states, without case history"; S29 note rewritten (Brazil S5 recorded-zero stratum now −1.89%, CI includes zero).
  - S30 paragraph: five Brazilian cells lowest in 2021 (−0.66% to −1.94%); Brazil S5 not highest in 2023/24; Peru negative every year; Taiwan 2023 −0.28 / −1.50.
  - Supporting-analyses paragraph (S32–S35): outbreak CI above zero now Peru and Taiwan held out; weighting and recalibration numbers updated. S35 note: Brazil S4 not in the pre-review strata.
  - S36: Brazil C3 (control −0.04, p 0.038; excess +0.28, p 0.30) and C6 (control −2.11, p < 0.001; excess +0.30, p 0.15) filled; new interpretation paragraph (no CI above zero in 16 cells; C2 absorbs Brazil's gain; C6 hurts L3 in every country).
  - S37: yref +0.26 (p 0.33), delay2 +0.60 (−0.56 to 1.76), C3/C6 rows, Brazil S2 no-history rows; Taiwan primary column now three-seed; seed-0 comparators kept in brackets.
  - S39/S40 text: Taiwan quintiles −30.8 to −46.2, Peru −33.1 to +64.3, ρ +0.52.
- **BR S2 without case history (coordinator request): option 1 used.** Tables S41 and S42 now take a "Brazil, held-out states" block: S41 gets two held-out-states columns (N-ladder WIS incl. N4 + C1, coverage); S42 gets three held-out-states rows (horizons 1, 4, pooled; G_emb +1.52, G_id +0.88, G_excess −0.01, MDE 1.80) plus a note with the C1 rung of both cells and an interpretation paragraph. No new table S56. The S41 N4 + C1 marker is filled (0.3409 pooled).
- S22 note: "pending" clause deleted as instructed; Brazil S4 rows in S22/S23.
- **Section G (S43–S48) rewritten for the 14-cell rerun**:
  - S43: "Reported" is now the Table 2 (three-seed) value; the former seeds column became "Seed 0 only (before row 53)"; Brazil S4 row added. Readings: PE S5 all rows now p 0.051 (no longer bold), B = 4 p 0.020 (bold); TW S1 nominal loss kept only under B = 4.
  - S44: R3_A1 rerun values (CO RS/pop +0.30, p 0.034; PE and TW steps changed; TW all non-case −1.27, p 0.12; margins 0.92 / 2.26 / 5.03).
  - S45: Holm over 14; Brazil S4 row; BR S5 under the rule −0.39% (p 0.39).
  - S46: trend rerun incl. Brazil S4 (7 of 14 nominal, none scaled); 2023–24 table adds Brazil S4 and new Brazil S5 (−0.54%, p 0.0015).
  - S47: counts 2/2/2/0, 9/8/10/5, 13/12/13/13; IAAFT adds Brazil S4 (size 14.9%); Colombia S3 no longer equivalent under (a), so its IAAFT cells read "not run"; 8 of 9 calibrated.
  - S48: Panel A adds Brazil S4; values per rerun (TW S5 −3.28%; PE S1 −0.77, p 0.029 in note); Panel B zero-week width percentages now the ratio of row means (+1.6% to +12.3%, TW S5 +55%), significant in 13 of 14.
- S52: Holm column now "seed 0 (13 cells) → seeds 0–2 (14 cells)" from T1; text adds that Brazil S5 loses significance under B = 4 + Holm (only Colombia S2 survives all three).
- Figure S1–S4 captions replaced by the regenerated `CAPTIONS.md` text (Fig S1 no "without 2021"; Fig S4 LightGBM only).
- All `REVISIT final kit` tags and `PENDING` markers removed.

## S1_supplement_methods.md
- Table S5b: Brazil held-out districts 458,952 – 1,381,582 rows, 151 inputs; new row Brazil held-out states without case history (456,872 – 1,385,651; 211).
- Total compute paragraph (see above).
- E1: nine cells average three seeds. E3 conclusions: final B = 4 + Holm (only Colombia S2 survives), IAAFT + Holm (Colombia S4, Taiwan S5 lose); final IAAFT size 14–18% in Brazil S1–S4 and Colombia S5.
- Table S13: fixed panel, yref, delay2 and the no-history C6 panel marked Done; results paragraph added (sensitivities and RH values).
- Deviation row 38: results filled (identifier gain +1.98%, excess −0.04%). Timing paragraph: row 25 now states seed-0 and final three-seed Taiwan values; "13 completed cells" qualified (Brazil S4 still blinded).
- EPIFORGE items 9 and 16: removed the claim of an 18 November deposit (the user skipped the deposit); AUTHORS markers unchanged.
- Deviations table S14 cross-checked against `docs/plans/deviations_from_protocol.md` rows 1–53: commit refs and all numbers match (differences are only section cross-references).

## Source conflicts (flagged, not resolved by guessing)
1. FINAL_RESULTS_BRIEF §3 gives the Brazil S4 zero-filled contribution as −0.17 [−0.31, −0.04], p .015; `T5_strata.csv` gives −0.20 [−0.34, −0.07] (and +0.40 + 0.00 − 0.20 = +0.20 = total). Tables use T5.
2. Peru S5 case-week coverage change: brief "+2.0 pp" equals the difference of row means; the week-weighted difference (the table's convention) is +2.1 pp (p < 0.001). S48 and its text use +2.1.
3. Zero-week width percentages in S48 follow the brief (ratio of row means); the absolute changes in the same table are week-weighted.
