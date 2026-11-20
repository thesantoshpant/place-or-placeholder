# Final results brief (2026-11-20)

All 14 primary cells are scored. The blinding was lifted on 2026-11-20 (no pre-read deposit).
Source: `docs/results/tables/T1_primary_family.csv` (results kit v3, `make_results.py --force`,
manifest `configs/primary_cells.yaml` with seeds 0–2 where they exist). Earlier tables are backed up
in `tmp/final/backup_pre_final/`.

Scoring for every number here:
- WIS on log(1 + cases);
- origin-year rows only;
- exclusions v2;
- horizons 1 and 4 pooled, with weeks weighted equally;
- DM test with EWC variance and the HLN correction.

Percentages are of the reference WIS (L3; N3 in the no-history arm). Positive means the embeddings help.

## 1. Primary family (Holm over m = 14)

G_excess = WIS(L3+C*) − WIS(L4+C*) (primary). G_emb = WIS(L3) − WIS(L4) (co-primary).
- The Holm column adjusts the EWC p values; B=4 and IAAFT are the two cautious variance checks, each also Holm-adjusted over 14.
- TOST uses the ±1% margin, Holm-adjusted.
- "Seeds" lists the seeds used for G_excess. For PE S5 and TW S5, G_emb and G_id use seed 0 only (pre-declared cut). Every other cell uses the same seeds for all estimands.

| Cell | C* | Seeds | G_excess % [95% CI] | DM p | Holm p | B=4 Holm p | IAAFT Holm p | TOST (Holm) | G_emb % [95% CI] | G_emb p |
|---|---|---|---|---|---|---|---|---|---|---|
| BR S1 | C1 | 0–2 | +0.23 [−0.33, +0.79] | .39 | 1.0 | 1.0 | 1.0 | equivalent | +0.26 [−0.31, +0.82] | .35 |
| BR S2 | C1 | 0 | −0.00 [−0.34, +0.34] | .996 | 1.0 | 1.0 | 1.0 | equivalent | −0.02 [−0.34, +0.30] | .88 |
| BR S3 | C1 | 0 | −0.16 [−0.34, +0.03] | .090 | .53 | 1.0 | 1.0 | equivalent | −0.13 [−0.35, +0.09] | .21 |
| **BR S4** | C1 | 0 | **+0.20 [−0.32, +0.71]** | .43 | 1.0 | 1.0 | 1.0 | equivalent | +0.22 [−0.32, +0.76] | .40 |
| BR S5 | C3 | 0–2 | −0.68 [−0.94, −0.42] | <.001 | **.0006** | .095 | **.007** | inferior | −0.39 [−1.34, +0.55] | .39 |
| CO S1 | C1 | 0–2 | −0.42 [−0.64, −0.21] | .001 | **.014** | .15 | **.038** | equivalent | −0.38 [−0.61, −0.16] | .003 |
| CO S2 | C1 | 0–2 | −0.52 [−0.74, −0.30] | <.001 | **.003** | **.022** | **.007** | equivalent | −0.60 [−0.81, −0.39] | <.001 |
| CO S3 | C1 | 0–2 | −0.68 [−1.08, −0.29] | .003 | **.030** | .11 | **.007** | inferior | −0.82 [−1.14, −0.49] | <.001 |
| CO S4 | C1 | 0–2 | −0.45 [−0.68, −0.21] | .002 | **.019** | .15 | .054 | equivalent | −0.54 [−0.78, −0.30] | <.001 |
| CO S5 | C2 | 0 | +0.22 [−0.19, +0.63] | .27 | 1.0 | 1.0 | 1.0 | equivalent | −0.04 [−0.37, +0.28] | .77 |
| PE S1 | C1 | 0–2 | −0.82 [−1.49, −0.14] | .022 | .18 | .68 | .28 | inconclusive | −0.91 [−1.62, −0.20] | .016 |
| PE S5 | C3 | 0–2 | +0.93 [−0.16, +2.02] | .088 | .53 | .18 | .0500 (=.04998) | inconclusive | +0.68 [−0.59, +1.96] (seed 0) | .27 |
| TW S1 | C1 | 0–2 | −0.71 [−1.40, −0.03] | .042 | .29 | .27 | .056 | inconclusive | −0.95 [−1.71, −0.18] | .018 |
| TW S5 | C3 | 0–2 | −18.3 [−29.8, −6.8] | .004 | **.035** | .27 | .29 | inferior | −21.6 [−31.8, −11.4] (seed 0) | <.001 |

- **Significant after Holm (EWC, m = 14):** six losses, BR S5, CO S1, CO S2, CO S3, CO S4 and TW S5. No gain is significant.
- **Also significant under B=4 + Holm:** CO S2 only.
- **Also significant under IAAFT + Holm:** BR S5, CO S1, CO S2 and CO S3. PE S5 (a gain) sits exactly at the threshold (.04998).
- **Significant under all three:** CO S2 only.
- **Equivalent within ±1% after Holm:** 8 cells (BR S1–S4, CO S1, CO S2, CO S4, CO S5). The count is 9 unadjusted and 5 under B=4 + Holm. At ±0.5%, 2 are equivalent with EWC (unadjusted and Holm) and 0 under B=4 + Holm (R3 A4).

## 2. Verification of this run

- **14 cells.** `n_family_available = 14` and `family_complete = True`. Recomputing Holm from DM_p matches the table exactly.
- **3-seed cells.** The 9 cells in `R3_C_seeds.csv` reproduce it exactly: 27 estimand rows, max |diff| = 0 in % and both CI ends, p, n_seeds, n_rows and class.
- **Cells without new seeds.**
  - BR S2, BR S3 and CO S5 have point estimates, CIs, DM p, B=4 p, IAAFT p, G_emb and G_id identical to the 13-cell backup. Only the Holm values change (m 13 → 14).
  - BR S4 is new.
  - BR S1 is also unchanged (it already had 3 seeds).
- **Taiwan rows.** Every Taiwan table has 141,645 pooled rows: T1, T2 ladder, T3, S1 baselines, S2 control panel, S3, S4, S5 and T5 strata (138,362 + 3,283).
  - The TW S1 ladder and baselines now use the 2021 runs through the new additive manifest key `ladder_runs`, read by `rk_cells`, `rk_compute` and `review_more.run_baselines`.
  - L2 is now the shared-parameter run, which replaces the per-level tuned L2 in T2.
  - The ladder values match `R3_C_tw2021_ladder.csv`: L0 .0743, NB .0475, L1 .0316, L2 .0319. L3/L4 differ by ≤.0005 because the kit averages seeds 0–2 and round 3 used seed 0.
  - Only the secondary cells TW_S1_BRparams, TW_S1_no2021 and TW_S5_no2021 have 113,430 rows, by design.
- **BR S4 sanity.**
  - Rows: 2,879,874 per role before filtering → 2,703,183 scored, the same as the other BR cells. 1.41% of rows are removed by the ES exclusion.
  - C* = C1 is read from `runs/brazil_s4_controls_2019/selection.json` (rule v2; tie set {C1}; 2019 WIS L3 .17500 vs L3+C1 .17517, so C1 did not beat L3).
  - Ladder WIS (pooled h{1,4}): L3 .1683, L4 .1679, L3+C1 .1683, L4+C1 .1680. For comparison, BR S2 L3 is .1689 and BR S3 L3 is .1706. 80% coverage is .90; on case weeks it is .66.

## 3. BR S4 (held-out districts)

G_excess is +0.20% [−0.32, +0.71], p .43, Holm 1.0. TOST is equivalent at ±1% (Holm), MDE 0.73%. G_emb is +0.22% [−0.32, +0.76], p .40, and G_id is +0.02%, p .18.

By target type (contribution to the total, in pp of WIS(L3)):
- case weeks +0.40 [−0.16, +0.96];
- recorded zeros 0.00;
- zero-filled weeks −0.17 [−0.31, −0.04], p .015.

This is the same pattern as the other Brazil cells: a small, non-significant gain on case weeks offset by a loss on zero-filled weeks. Brazil's spatial splits S2–S4 are all within ±0.25% of zero.

## 4. BR S2 without case history (pre-specified headline split of the no-history arm)

C* = C2 (coordinates; rule v2 at the 2019 origin). n = 2,703,183 rows, seed 0, % of WIS(N3).

| Estimand | % [95% CI] | p | class |
|---|---|---|---|
| G_emb (N3 → N4) | +1.52 [−1.27, +4.32] | .27 | inconclusive |
| G_id, coordinates (N3 → N3+C2) | +0.88 [−0.48, +2.23] | .19 | inconclusive |
| G_excess (N3+C2 → N4+C2) | −0.01 [−1.28, +1.27] | .99 | inconclusive (MDE 1.80%) |
| G_C1 (N3 → N3+C1) | −0.24 [−0.82, +0.34] | .39 | equivalent |
| G_excess beyond C1 (N3+C1 → N4+C1) | +1.85 [−1.09, +4.79] | .20 | inconclusive |

The last two rows are the static-history rung, computed with `round3_extra.score_nohist` and saved in `docs/results/review/FINAL_br_nohist_C1_rung.csv`. The same code reproduces T6b for both BR cells exactly. ID share is not estimable because G_emb's CI includes 0.

Ladder (WIS): N3 .3613, N3+C1 .3622, N3+C2 .3582, N4 .3557, N4+C2 .3581, N4+C1 .3555.

**Reading.** In held-out Brazilian states nothing is significant. The embedding point gain (+1.5%) is of the same order as the coordinate gain (+0.9%), and beyond coordinates it is exactly zero. Compared with the other no-history cells:
- **BR S1:** the coordinate gain was significant, G_id +3.30 [+1.68, +4.93], p .0005.
- **CO S2:** every estimand was significantly negative.

The pre-specified decision rule ("ID fingerprint" = G_emb > 0 and G_excess equivalent to 0) is not met in BR S2: G_emb is not significant and G_excess is inconclusive, not equivalent. The no-history BR S1 N4+C1 rung is present (T6c; N4+C1 .3409 vs N3+C1 .3478).

## 5. Sensitivities (Brazil S1, T6a; % of WIS(L3); h{1,4})

| Variant | Estimand | % [95% CI] | p | Primary |
|---|---|---|---|---|
| `yearly_ref: origin` (strictly causal yearly alignment) | G_emb | +0.26 [−0.29, +0.82] | .33 | +0.26 |
| `report_delay: 2` (2-week reporting delay) | G_emb | +0.60 [−0.56, +1.76] | .29 (inconclusive) | +0.26 |
| C3 (shuffled embedding) in place of C* | G_excess | +0.28 [−0.27, +0.82] | .30 | +0.23 |
| C3 in place of C* | G_id | −0.04 [−0.08, −0.00] | .038 | +0.03 |
| C6 (unit-ID categorical) in place of C* | G_excess | +0.30 [−0.12, +0.71] | .15 | +0.23 |
| C6 in place of C* | G_id | −2.11 [−2.68, −1.54] | <.001 | +0.03 |

No sensitivity variant turns Brazil S1 into a significant gain. The reporting delay doubles the point estimate but also the CI width. The other sensitivity cells (per-level tuning, TW with BR parameters, TW without 2021) are in T6a.

## 6. Final S1 fixed control panel (seed 0; `docs/results/review/RE_control_panel.csv`)

G_excess_k, % of WIS(L3):

| | C1 | C2 | C3 | C6 |
|---|---|---|---|---|
| Brazil | +0.25 (p .37) | +0.02 (p .88) | +0.28 (p .30) | +0.30 (p .15) |
| Colombia | −0.39 (.001) | −0.34 (.010) | −0.33 (.001) | −0.13 (.27) |
| Peru | −0.70 (.056) | −0.86 (.022) | −0.37 (.081) | −0.29 (.63) |
| Taiwan (incl. 2021) | −0.60 (.049) | −0.94 (.087) | −0.68 (.079) | −0.52 (.11) |

- **G_id of C6 (the identifier):** BR −2.11, CO −2.37, PE −6.28, TW −2.29 (TW n.s.). It hurts L3 everywhere.
- **Taiwan:** the panel now includes 2021, with base + 2021 runs and 141,645 rows (`control_panel.py --no-tw2021` gives the old panel). The values equal R3_C_tw2021_panel.
- **Interpretation:** rewritten in `RE_summary.md`. No CI lies above 0 in any of the 16 cells. Brazil is positive under every control but never significant; coordinates absorb the Brazil gain (C2 +0.02).

## 7. Round-3 analyses rerun on all 14 cells (`round3_analyses.py --exclude "" --a1-tw2021`)

The load check matches T1 exactly for all 14 cells (BR S4 included).
- **A2 (no-control rule):** the C* beat L3 at 2019 only in BR S1 and CO S5. Under the rule, the Holm-significant losses are CO S1 (.035), CO S2 (.0009), CO S3 (.002), CO S4 (.005) and TW S5 (.0045). BR S5 under the rule (G_emb) is −0.39%, p .39.
- **A4 (equivalence counts):** see Section 1.
- **A6 (outcome-agnostic checks):**
  - **District-years with ≥1 case (G_excess):** CO S1 −0.33 (p .004), CO S2 −0.33 (.004), CO S4 −0.29 (.008), CO S3 −0.33 (.083), BR S5 −0.46 (.001), PE S1 −0.77 (.029), TW S5 −3.28 (<.001), BR S4 +0.20 (.36).
  - **80% interval width on zero weeks:** L4+C* is wider than L3+C* in **14/14 cells** (+1.6% to +12.3%; TW S5 +55%), significant in 13.
  - **Case-week 80% coverage:** PE S5 +2.0 pp (p .0001). CO S3 is −1.0 pp (p .003).
- **A8 (IAAFT):** ±1% equivalence holds in 8 of 9 cells; BR S1 drops out. The real size of the nominal-5% test is 14–18% in BR S1, S2, S3 and S4 and in CO S5.

## 8. What changed vs the earlier 13-cell, seed-0 table

- **BR S4 added:** +0.20% (null, equivalent). Holm now uses m = 14.
- **Seven cells moved to 3 seeds:** BR S5, CO S1–S4, PE S1 and TW S1. PE S5 and TW S5 use 3 seeds for G_excess only.
  - BR S5 −0.60 → −0.68
  - CO S1 −0.39 → −0.42
  - CO S2 −0.47 → −0.52
  - CO S3 −0.65 → −0.68
  - CO S4 −0.43 → −0.45
  - PE S1 −0.70 → −0.82 (DM p .056 → .022, Holm .34 → .18)
  - PE S5 +0.96 → +0.93
  - TW S1 −0.60 → −0.71
  - TW S5 −17.3 → −18.3
- **Holm (EWC):** the same six significant losses as before.
- **B=4 + Holm:** BR S5 is no longer significant (.027 → .095), so **only CO S2 now survives B=4**.
- **IAAFT + Holm:**
  - the set is unchanged (BR S5, CO S1, CO S2, CO S3);
  - TW S5 .14 → .29;
  - PE S5 .054 → .04998, which is at the threshold and in the gain direction.
- **TOST, Holm-adjusted:**
  - BR S5 equivalent → inferior;
  - TW S1 stays inconclusive;
  - PE S1 stays inconclusive (unadjusted class: inferior).
- **Taiwan ladder and panel:** now include 2021 everywhere (141,645 rows). The T2 TW L2 is the shared-parameter run.

## 9. TRIAGE_round3 Addenda 1–5: what still holds

| Statement | Status |
|---|---|
| A1: BR S5 under the no-control rule ≈ −0.34% (p .44) | **Reword:** −0.39% (p .39) |
| A1: under that rule the Holm-significant losses are CO S1–S4 and TW S5 | Holds (m = 14) |
| A1: "BR S5 robust to the variance estimators" | **Reword:** BR S5 survives IAAFT + Holm (.007) but NOT B=4 + Holm (.095). Only CO S2 survives both. The Abstract lead on CO S2 still holds. |
| A1: equivalence at ±1%: 9 / 8 Holm / 6 Holm B=4; none at ±0.5% after B=4 + Holm | **Reword:** 9 / 8 / **5**. The ±0.5% statement holds. |
| A1: embedding stability (A7) | Unchanged (not rerun on new cells; A7 does not depend on BR S4) |
| A2: positive control A1 (BR climate +0.57, RS/pop +0.52, all +1.09; CO RS/pop +0.30; none in PE/TW) | Holds in substance: BR is unchanged; CO RS/pop is +0.30 (p .034, was .041). The values moved slightly because L3/L4 are now seed-averaged in CO/PE/TW. TW (with 2021) all non-case covariates: −1.27% (p .12). Addendum 5's "−1.06%, p .19" needs updating. |
| A2: A3 trend, "no detectable trend" | Holds (A3 rerun; unchanged inputs except seeds) |
| A2: A5, PE S1 sign flips under per-level tuning; BR S3 significant under exclusions v1; PE S5 p<.05 under B=4 or all rows | Holds per A5 rows. The PE S1 primary is now −0.82 (3 seeds). |
| A2: A6, CO loss persists in case-ever district-years (~−0.3%, p ≤ .016, S1/S2/S4) | Holds (−0.29 to −0.33, p ≤ .008) |
| A2: TW S5 −17% → −3.4% | **Reword:** −18.3% → −3.3% |
| A2: "embeddings widen zero-week intervals in 12/13 cells (+2 to +14%; +61% TW S5)" | **Reword:** 14/14 cells (+1.6 to +12.3%; TW S5 +55%) |
| A2: "case-week coverage moves toward nominal only in PE S5 (+2.4 pp)" | **Reword:** +2.0 pp |
| A2: A8, IAAFT equivalence 9 → 8 (BR S1 drops out) | Holds (BR S4 is equivalent under IAAFT) |
| A2: true size 14–18% in BR S1/S2/S3 and CO S5 | Holds; **add BR S4 (14.9%)** |
| A3: information probe | Unaffected |
| A4: variants, CO seeds | Hold |
| A5: seed values | Hold exactly (verified) |
| A5: "Holm over 13: same six losses" | Holds with **m = 14** |
| A5: TW S1 with 2021 (ladder L1 .425, L3 .430, L4 .434 vs L0) | Hold in seed-0 terms. The kit's 3-seed ladder gives L3 .4306 and L4 .4347. |
| A5: TW panel values | Hold; the kit's S2 table now also uses them |
| A5: CO S2 no-history | Holds. **Add:** BR S2 no-history is null everywhere (Section 4), so "Brazil coordinates help without history" is true only in S1, not in held-out states. |

## 10. Tests

The full suite gives 352 passed, 8 skipped and 1 failed. The failure is the known order-dependent test `tests/test_remote_sensing.py::test_monthly_output_grid_complete`, which uses a relative path; it passes when run alone, together with `tests/test_make_results.py` (13 passed).

## 11. Code changes in this run

All changes are additive. Originals are in `tmp/final/backup_code/`.
- **`configs/primary_cells.yaml`:** new TW S1 key `ladder_runs`.
- **`rk_cells.py`:** `_apply_ladder_runs`.
- **`rk_compute.ladder_rungs`:** multi-dir rungs.
- **`review_more.run_baselines`:** honours `ladder_runs`.
- **`make_results.py`:** T2 caption.
- **`control_panel.py`:**
  - Taiwan now includes the 2021 runs;
  - `--no-tw2021` restores the old panel;
  - the runs column lists all dirs.
- **`round3_analyses.py`:** the A5 note now reads the panel source.
- **`make_pub_figures.py`:**
  - the Fig S4 caption is kept as a constant;
  - the Fig S1 "(without 2021)" label shows only when the rows differ;
  - the Fig 4 title names both splits.
