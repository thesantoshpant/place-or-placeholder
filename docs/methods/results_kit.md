# Results kit (`scripts/analysis/make_results.py`), v3

One command regenerates every paper table, figure and the writers' brief from whatever runs are
finished. It is idempotent and cached, so re-running it after more compute finishes only computes
the new or changed cells. Version 3 (2026-11-18) folds in the post-review decisions (deviation rows
24–33); what changed and the before/after numbers are in `docs/results/review/KIT3_changes.md`.

## How to run

```bash
cd /net/home/spant/0-100/group-research/place-or-placeholder && source env.sh
export OMP_NUM_THREADS=4
nice -n 19 python scripts/analysis/make_results.py                 # everything, cached
nice -n 19 python scripts/analysis/make_results.py --force         # ignore the cache
nice -n 19 python scripts/analysis/make_results.py --only BR_S1 --force   # recompute one cell
nice -n 19 python scripts/analysis/make_results.py --extras none   # fast: no forecast-reading analyses
nice -n 19 python scripts/analysis/make_results.py --n-boot 2000   # add the 52-week bootstrap
```

Long runs go in tmux (`pop_kit3`). Log of the last full run: `runs/kit3_full.log`. Tests:
`pytest tests/test_make_results.py` (synthetic runs, ~40 s).

**Isolation.** Each cell that needs computing runs in its own worker process
(`make_results.py --worker CELL`, internal), so memory goes back to the OS after every cell and
only one cell is in memory at a time. `--in-process` turns this off (tests, debugging).

**Run time.** A cached cell takes about 1 s. With `--extras all`, a Brazil cell takes tens of minutes
(the recalibration, q0.9 and distance analyses read the forecast files); Peru and Taiwan take a few
minutes. BR S4 and the no-history cells are picked up automatically, with the same filters, the
next time the script runs after their runs finish.

## Options

| Option | Meaning |
|---|---|
| `--extras none` | estimand table, ladder, all-rows sensitivity, EWC B=4, delta-method CI, three strata |
| `--extras cheap` | + IAAFT-calibrated p (`--iaaft-reps`, default 2000), case scale, weighting, outbreak, per year, S1 baselines |
| `--extras all` (default) | + causal recalibration, q0.9 mechanism on zero rows, embedding distance (S2–S5) |
| `--exclusions v2` (default) / `v1` | scoring exclusions: v2 = v1 + unit-week exclusions (Espírito Santo, IBGE `^32\d{5}$`, target weeks ≥ 2019-12-29; row 34); with v2 the v1 result is also stored per cell (`exclv1_*` in T1, `strata3_excl_v1`) |
| `--control-panel PATH` | fixed control panel CSV (default `docs/results/review/RE_control_panel.csv`; pending if absent) |

The heavier analyses run on primary cells only; secondary cells get the estimand table, ladder and
the cheap robustness columns.

## Cells

Defined in `scripts/analysis/rk_cells.py` (`build_registry`) from `configs/primary_cells.yaml`.

**Primary family (14 cells).** BR S1–S5, CO S1–S5, PE S1, PE S5, TW S1, TW S5; every manifest cell
carries `family: primary` (Taiwan S1 included; deviation row 25). `family_size: 14` sets the
Holm family size. When a run's `plan.json` marks a stage `reuse:<dir>`, that directory is used.

**Row filter (row 24).** Manifest `row_filter: origin_year`: every estimate, ladder and supporting
table uses only rows whose forecast origin (target week − h) lies in the target's epi-year
(epi-year = calendar year of the week's Wednesday). The filter is applied inside the kit, after
`load_cell`, identically for all four roles; library defaults (`load_cell`, `infer_estimand`,
`ewc_inference`) are unchanged. G_excess on all rows is kept as the `unfiltered_*` columns of T1.

**Extra test years (row 25).** A manifest cell may list `add_test_years: {years, runs}`. When all
four of those runs are complete they are appended to the cell's roles; otherwise the cell uses its
base runs and is flagged "<years> pending (base test years only)" in T1, F1 and the brief. The
base-runs-only set is always registered as a sensitivity cell `<id>_no<years>`
(`TW_S1_no2021`, `TW_S5_no2021`), shown in T6a.

**C\*.** Read only from `<prefix>_controls_2019/selection.json` with `rule_version: 2`; otherwise
"selection pending (stale)".

**Secondary cells:** `BR_S1_3seeds` (duplicate of BR_S1 since row 22), `BR_S1_yref`,
`BR_S1_delay2` (G_emb only), `BR_S1_ctrlC3`, `BR_S1_ctrlC6`, `BR_S1_perlevel`, `TW_S1_BRparams`,
`TW_*_no2021`, `BR_S1_nohist`, `BR_S2_nohist`.

**Completeness.** A role is complete only when `scores.parquet` exists, no chunk file is newer and
its stage marker exists (when the pipeline dir exists). Pending cells are never read.

## Horizons and seeds

Primary pooled estimates pool `primary_horizons` = h{1,4} in every cell (row 21). S1 cells
(`secondary_pooling: true`, old key `secondary`) also get a secondary h1–h4 pooled row, computed
only on test years scored at all four horizons (so Taiwan 2021, scored at h1/h4 only, is left out
of it). Seeds: `seed_gain_frame(seed_policy="common")` as before.

## Computation (all reused, nothing re-implemented)

- Rows: `scripts/run/estimands_report.load_cell` (v2 unit and incomplete-week files), then the unit-week exclusions of `exclusions_v2/unit_week_exclusions.csv` (kit-side, all four roles), then the row filter. Build v2 once with `python scripts/analysis/build_exclusions_v2.py`.
- Estimands: `pop.eval.estimands.compute_estimands_v2` / `infer_estimand` (DM/EWC + HLN, TOST 1%, MDE).
- Three strata and additive contributions: `review_explore.week_contributions` (exact identity;
  the residual is stored and tested to be 0).
- EWC B=4: the `ewc_hln_B4` construction of `inference_size_sim.run_methods` (tested equal).
- IAAFT-calibrated p: `inference_size_sim.IAAFT` surrogates of the cell's own weekly G_excess
  series, p = (1 + #|t*| ≥ |t|) / (1 + R), seed fixed per cell.
- Delta-method CI: `review_sens.delta_ratio_ci`; plain labels: `review_sens.equivalence_label`.
- Case scale: `load_cell` with `wis_case` served through `review_sens.patched_reader`.
- Weighting, outbreak, per year, baselines, recalibration, q0.9 mechanism:
  `review_more.run_*`; embedding distance: `review_explore.run_distance` / `distance_summaries`.

**Cache.** `runs/analysis_cache/<cell>/{est,ladder}.parquet`, `extras/*.parquet`, `info.json`
(rows before/after the filter, % dropped per horizon, seeds, exclusions, extras errors). The key
covers every `scores.parquet` used, the exclusion files, the options (row filter, extras level,
IAAFT reps), C\*, flags, horizons and `KIT_VERSION` (3).

## Outputs

Tables in `docs/results/tables/` (CSV + LaTeX booktabs fragment):

| File | Contents |
|---|---|
| `T1_primary_family` | Per family cell: absolute week-mean WIS of L3, L4, L3+C\*, L4+C\*; G_emb, G_id, G_excess (% of WIS(L3), 95/90% CI, p); DM p; Holm p over the available cells (`n_family_available`, `family_complete`); `p_bonf14`; unadjusted TOST class and the Holm-adjusted TOST p/class; `plain_label`; `loss_or_gain` (rule below); EWC B=4 p, CI and Holm p; IAAFT p and Holm p; delta-method CI; case-scale G_excess; all-rows G_excess; S1 `sec_*`; `flags`; `T_weeks` (integer; the v2 file held a pandas repr). |
| `T1b_margin_sensitivity` | TOST at ±0.5/1/2%: unadjusted and Holm-adjusted p, within flags, near-margin flag, label. |
| `T2_ladder` | Ladder per cell and horizon, coverage (origin-year rows common to every rung). |
| `T3_estimands` | All estimands per cell × horizon and per test year. |
| `T4_cstar_selection` | 2019-origin candidates and the chosen C\*. |
| `T5_strata` | Three target types (cases > 0 / zero listed by the source / zero filled): stratum estimate (% of the stratum's WIS(L3)) and additive contribution (% of the cell's WIS(L3)), per estimand; contributions sum to the total. |
| `T6a_sensitivities`, `T6b_nohist_estimands`, `T6c_nohist_ladder` | Sensitivity cells and the no-history arm. |
| `S1_baselines` … `S8_per_year` | Supporting: baselines (relative WIS vs seasonal naive), fixed control panel (read from file), outbreak weeks, weighting, causal recalibration, q0.9 mechanism, embedding distance (Spearman; bins in `S7b_*.csv`), per year with context flags. |

Figures in `docs/results/figures/` (PDF + PNG, Okabe–Ito palette, plain labels):

| Figure | Contents |
|---|---|
| F1 `F1_forest_G_excess` | G_excess per family cell, 95% and 90% CI, ±1% band; filled dot = Holm-adjusted p < .05; Taiwan S5 in its own panel (own scale). |
| F2 `F2_strata_contributions` | Additive contribution of each target type to G_excess, per cell, one panel per country; diamond = total. |
| F3 `F3_s5_embedding_distance` | Held-out country: district similarity to training districts vs district G_excess, quintile means with 95% CI. |
| F4 `F4_per_year_gains` | G_excess per test year, one panel per country, splits by colour. |
| FS1, FS2 | S1 ladder per country; no-history ladder. |

**Brief.** `docs/results/RESULTS_BRIEF.md`: scored-row rule, Taiwan rule, loss-counting rule, the
headline T1 table, cell status, per-cell detail, sensitivities, file pointers, scheduler snapshot.

## Conventions

- A gain is positive when the second model has lower WIS; % of WIS(L3) (WIS(N3) no-history).
- **Unadjusted class** (`TOST_class`): equivalent = 90% CI inside ±1%; superior/inferior = 95% CI
  excludes 0 and p < .05; else inconclusive. **Holm class** (`TOST_class_Holm`): equivalent =
  Holm-adjusted TOST p < .05; else inferior/superior = Holm-adjusted DM p < .05; else inconclusive.
- **Loss-counting rule:** a loss (gain) = G_excess < 0 (> 0) with Holm-adjusted DM p < .05; "small"
  if the estimate is inside ±1%; nominal p < .05 alone is "nominal only", never counted.
- `scripts/run/primary_family.py` reads the same manifest but not `row_filter` / `add_test_years`;
  it reproduces only the v2 (pre-review) numbers.
