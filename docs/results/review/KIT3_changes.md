# Results kit v3: what changed (2026-11-18)

Command: `nice -n 19 python scripts/analysis/make_results.py` (tmux `pop_kit3`, log `runs/kit3_full.log`, exit 0,
18 cells computed, no supporting-analysis errors). Before = the v2 kit's `T1_primary_family.csv`
(saved in `runs/kit3_before/`); after = `docs/results/tables/T1_primary_family.csv`. Full comparison:
`runs/kit3_compare.csv`, `runs/kit3_es_effect.csv` (script `runs/kit3_compare.py`).
Tests: `tests/test_make_results.py`, 12 pass.

## What changed

| Decision | Implementation | Deviation row |
|---|---|---|
| Primary rows = origin-year rows | `row_filter: origin_year` in `configs/primary_cells.yaml`; applied in the kit after `load_cell` (library defaults untouched). Drops 1.91% of h1 rows and 7.66% of h4 rows in every cell. All-rows G_excess = T1 `unfiltered_*` | 24 |
| Taiwan 2021 | `add_test_years` for TW S1 (complete: 2020–2024) and TW S5 (**2021 runs still running** in `pop_tw2021s5`, so TW S5 falls back to the old years and is flagged "2021 pending"; it is picked up automatically on the next kit run). Old sets = `TW_S1_no2021`, `TW_S5_no2021`. TW S1 is now explicitly `family: primary`; the old `secondary: true` key (it only switched on h1–h4 pooling) is renamed `secondary_pooling` | 25 |
| Three strata | T5 / F2: cases > 0, zero listed by the source, zero filled; stratum estimate + exact additive contribution. Identity residual = 0.0 in every cell | 26 |
| T1 | Absolute WIS of L3/L4/L3+C\*/L4+C\*, G_emb, G_id, unadjusted and Holm-adjusted TOST class, plain label, `loss_or_gain`, DM p, Holm p (13 of 14 available, marked provisional), EWC B=4 p/CI/Holm, IAAFT p (2,000 surrogates)/Holm, delta-method CI, case scale, all rows, v1 exclusions. T1b = margins 0.5/1/2% | 27, 28 |
| Supporting tables | S1 baselines, S2 control panel (**pending**: `docs/results/review/RE_control_panel.csv` not present yet), S3 outbreak, S4 weighting, S5 recalibration, S6 q0.9 mechanism, S7 embedding distance, S8 per year with context flags | 29, 33 |
| Figures | F1 forest (Taiwan S5 in its own panel), F2 strata contributions, F3 S5 distance vs gain, F4 per-year; FS1/FS2 ladders. The superseded v2 files `F2_ladder_S1.*` and `F3_per_year_gains.*` were deleted | – |
| Espírito Santo (coordinator, mid-task) | `data/processed/exclusions_v2/` (built by `scripts/analysis/build_exclusions_v2.py`; v1 untouched): v1 + all 78 units matching `^32\d{5}$`, target weeks ≥ 2019-12-29, dropped at scoring for all four models in every Brazil cell. v1 result kept as T1 `exclv1_*` | 34 |
| Bug fix | T1 `T_weeks` was `r.T` (the pandas transpose of the row, so a Series repr); now the integer week count | – |
| Docs | Deviation rows 24–34 added; the stale "D18–D23 not committed" header fixed (`e9df1f1`); NOTES_FOR_WRITERS items 1, 2, 17, 18, 20, 26 updated and 29–35 added (incl. the ES training-target limitation and the outbreak-threshold wording); `docs/methods/results_kit.md` rewritten | – |

## Before → after, G_excess (% of WIS(L3), pooled h{1,4})

| Cell | v2 % (DM p, class) | v3 % [95% CI] | DM p | Holm p (13) | v3 label (±1%) / loss rule |
|---|---|---|---|---|---|
| BR S1 | +0.26 (.40, equiv.) | +0.23 [−0.33, +0.79] | .39 | .80 | no sig. difference; within ±1% (Holm TOST) |
| BR S2 | +0.02 (.93, equiv.) | −0.00 [−0.34, +0.34] | .996 | .996 | no sig. difference; within ±1% (Holm TOST) |
| BR S3 | −0.13 (.28, equiv.) | −0.16 [−0.34, +0.03] | .090 | .39 | no sig. difference; within ±1% (Holm TOST) |
| BR S4 | pending | pending | | | |
| BR S5 | −0.63 (<.001, equiv.) | −0.60 [−0.84, −0.36] | <.001 | .001 | small loss (Holm), within ±1% |
| CO S1 | −0.39 (.001, equiv.) | −0.39 [−0.58, −0.19] | .001 | .011 | small loss, within ±1% |
| CO S2 | −0.48 (<.001, equiv.) | −0.47 [−0.69, −0.25] | <.001 | .006 | small loss, within ±1% |
| CO S3 | −0.68 (.003, inferior) | −0.65 [−1.04, −0.27] | .003 | .026 | small loss; within ±1% only unadjusted (Holm class: inferior) |
| CO S4 | −0.44 (.002, equiv.) | −0.43 [−0.68, −0.18] | .003 | .025 | small loss, within ±1% |
| CO S5 | +0.18 (.33, equiv.) | +0.22 [−0.19, +0.63] | .27 | .80 | no sig. difference; within ±1% |
| PE S1 | −0.62 (.094, inconcl.) | −0.70 [−1.41, +0.02] | .056 | .34 | no sig. difference; not shown within ±1% |
| PE S5 | **+1.01 (.046, superior)** | +0.96 [−0.13, +2.05] | .079 | .39 | **no longer nominally significant**; not within ±1% |
| TW S1 | −0.39 (.19, equiv.) | −0.60 [−1.20, −0.00] | .049 | .34 | nominal small negative, not sig. after Holm; not within ±1% |
| TW S5 | −11.53 (<.001, inferior) | −11.16 [−15.66, −6.65] | <.001 | .002 | loss (2021 pending) |

Count under the loss rule (13 cells): **6 Holm-significant losses** (5 small: BR S5, CO S1–S4; 1 large: TW S5),
1 nominal only (TW S1), 6 none, BR S4 pending. No gain anywhere.

## Espírito Santo exclusion (Brazil cells)

All ES rows of every test year go: 38,766 primary rows per cell = **1.41%** of Brazil's primary rows (81,432 rows
over all horizons in S1).

| Cell | G_excess v1 → v2 | zero-filled contribution v1 → v2 | zero-filled row share v1 → v2 |
|---|---|---|---|
| BR S1 | +0.230 → +0.232 | −0.204 → −0.204 | 52.8% → 52.2% |
| BR S2 | −0.013 → −0.001 | −0.194 → −0.182 | 52.8% → 52.2% |
| BR S3 | −0.188 → −0.158 | −0.381 → −0.350 | 52.8% → 52.2% |
| BR S5 | −0.614 → −0.601 | −0.673 → −0.662 | 52.8% → 52.2% |

(% of WIS(L3).) The exclusion moves every Brazil estimate by ≤ 0.03 pp; no conclusion changes. BR S3's DM p is
.045 under v1 and .090 under v2, so its nominal significance depended on the ES false zeros (not Holm-significant either way).

## Taiwan 2021

TW S1: −0.44% [−1.01, +0.14], p = .12 without 2021 → **−0.60% [−1.20, −0.00], p = .049 with 2021** (both on
origin-year rows). The 2021 all-zero year adds harm (embeddings put spurious upper-quantile mass on zeros), so TW S1
becomes "nominal small negative, not significant after Holm". TW S5 still shows the old years (2021 pending).

## Surprises and things to watch

1. **PE S5 loses its nominal gain** (+1.01%, p = .046 → +0.96%, p = .079), mainly from the origin-year filter. But under
   the robustness tests it looks *stronger*: B=4 p = .023 and IAAFT p = .006 (Holm .048). This is the one cell where the
   robust tests disagree with the primary test in the "more significant" direction. It is also the cell R-D found
   fragile under weighting and recalibration. Report it as unresolved, not as a gain.
2. **CO S4 is fragile**, as RC predicted: Holm p .025 (primary) but B=4 Holm p = .126; also CO S1 (.072) and CO S3
   (.075) under B=4 Holm. Under the IAAFT calibration all 6 losses stay Holm-significant (≤ .048).
3. **CO S3** is a Holm-significant small loss whose ±1% equivalence holds only unadjusted (the 90% CI reaches −1.0%);
   its Holm class is "inferior".
4. The **delta-method CI** (denominator estimated) is much wider for TW S5 ([−26.0, +3.6]) than the fixed-denominator
   CI, because WIS(L3) in Taiwan is tiny and very noisy. Elsewhere it changes bounds by < 0.2 pp.
5. **Case scale** tells a different story for BR S2/S3 (−0.73% p = .025; −1.30% p = .065), where log-scale G_excess is
   ≈ 0, and for TW S1 (−0.00%). Secondary scale only (row 30), but worth a sentence.
6. Every family cell's harm sits in the **zero-filled stratum** (e.g. CO S1 contribution −0.59 of −0.39 total; TW S5
   −12.5 of −11.2); positive-case weeks contribute small positive amounts everywhere (+0.1 to +1.3).
7. The **TW S1 ladder** (T2, FS1) drops the 2021 rows, because the L0–L2 baselines have no 2021 runs; T1 is not affected.

## Pending (picked up automatically on the next run, same filters and exclusions)

- BR S4 (scheduler; C\* selection not done yet), BR S1/S2 no-history, the BR S1 sensitivities (yref, delay2,
  controls panel C3/C6): `make_results.py` recomputes only these cells.
- TW S5 2021 runs (`runs/taiwan_s5_tw2021_*`, tmux `pop_tw2021s5`): when all four are complete, TW S5 switches to
  2020–2024 and the flag disappears.
- S2 control panel: appears as soon as `docs/results/review/RE_control_panel.csv` exists.
- Holm p values are over 13 cells until BR S4 lands.
