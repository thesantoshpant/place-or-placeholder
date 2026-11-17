# Results kit (`scripts/analysis/make_results.py`)

One command regenerates every paper table, figure and the writers' brief from whatever runs are
finished. It is idempotent and cached, so re-running it after more compute finishes only computes
the new cells.

## How to run

```bash
cd /net/home/spant/0-100/group-research/place-or-placeholder && source env.sh
nice -n 19 python scripts/analysis/make_results.py            # everything, cached
nice -n 19 python scripts/analysis/make_results.py --force    # ignore the cache
nice -n 19 python scripts/analysis/make_results.py --only BR_S1 --force   # recompute one cell
nice -n 19 python scripts/analysis/make_results.py --n-boot 2000          # add the 52-week bootstrap
```

Log of the last full run: `runs/analysis_cache/make_results.log`. Test: `pytest tests/test_make_results.py`
(synthetic runs, ~25 s).

Run time: a cached cell takes about 1 s. A new Brazil S1 cell (5.8M rows per role) takes several
minutes. Peru and Taiwan take seconds. The default is `OMP_NUM_THREADS=2`.

## Cells

The cells are defined in `scripts/analysis/rk_cells.py` (`build_registry`).

**Primary cells (14).** These come from `configs/primary_cells.yaml`. When a run's `plan.json` marks a stage `reuse:<dir>`, that directory is used for the role.

**C\*.** A cell's C\* is read only from `<prefix>_controls_2019/selection.json` (prefix = the first L3 run dir minus `_L3`), and only when that file has `rule_version: 2` (the rule of `scripts/run/select_control.py`). A missing file, an older rule (e.g. a pre-fix `runs/brazil_s5_controls_2019/selection.json` saying C4) or a `c_star` in `plan.json` is never used: the cell then shows **"selection pending (stale)"** in T1, T2, the brief and T4. Sensitivity cells with no C\* run (`BR_S1_yref`, `BR_S1_delay2`) show "n/a (no C\* run)".

**Secondary cells:**

| Cell | What it is |
|---|---|
| `BR_S1_3seeds` | Primary runs plus `brazil_s1_sens_seed{1,2}_*`, averaged over seeds. The extra seeds cover h1 and h4 only. |
| `BR_S1_yref`, `BR_S1_delay2` | Sensitivity runs for `yearly_ref: origin` and `report_delay: 2`. Only G_emb is reported, because these runs have no C\* run. |
| `BR_S1_ctrlC3`, `BR_S1_ctrlC6` | Controls panel: the control is used in place of C\* on the test years. |
| `BR_S1_perlevel` | The old per-level-tuned runs `brazil_s1_{L3,L4,L3_Cstar,L4_Cstar}`. |
| `TW_S1_BRparams` | `taiwan_s1brp_*`, i.e. Taiwan run with Brazil's params and C\*. |
| `BR_S1_nohist`, `BR_S2_nohist` | No-history arm: N3, N4, N3+C\*, N4+C\*, with reference N3. The ladder adds N3+C1 and N4+C1, and N2 if that run exists. |

**Completeness.** A role is complete only when all three conditions hold:
- `scores.parquet` exists;
- no chunk file is newer than `scores.parquet`;
- its pipeline stage marker (`runs/<pipeline>/stage_<stage>.done`) exists, whenever the pipeline directory exists.

A cell is computed only when all four of its roles are complete. Otherwise it shows as **pending**, with the reason for each role. Partial runs are never read.

## Horizons

Every **primary pooled** estimate pools only the manifest's `primary_horizons` (h{1,4}, deviation row 21), in every cell. This applies to the rows labelled `horizon = "pooled"` of T1, T3, T5 and T6, the per-test-year and strata rows, the ladder's pooled column (T2, F2), and F1/F3. These are the same rows and the same estimator as `scripts/run/primary_family.py`, so T1 matches its `estimate`, `lo95`/`hi95` and `p` exactly (checked on PE S1 and TW S1: differences 0).

For S1 cells (manifest `secondary: true`; secondary-arm S1 cells too), the kit also emits the **secondary** pooling over `secondary_horizons` (h1–h4) as `horizon = "pooled_h1-4"` (overall only, not per year or stratum). In T1 this is in the `sec_*` columns and in the last LaTeX column. It is never in the Holm family. The secondary row is emitted only when the cell actually has more horizons than the primary set (cells scored on h1/h4 only get none).

Per-horizon rows (`horizon = "1"`, …) are unchanged. Every estimand row has a `pooled_over` column listing its horizons. With a JSON `--registry` (tests), the horizons come from `configs/primary_cells.yaml` when present, else h{1,4} and h1–h4.

**Seeds.** Rows come from `load_cell`, which uses `seed_gain_frame(seed_policy="common")`: each estimand uses, per row, only the seeds both of its roles have. If the two roles of an estimand have different seed sets at a primary horizon, the kit records it in `info.json` (`seed_set_mismatch_primary`) and in the brief; unlike `primary_family.py` it does not stop. Holm (T1) runs over the primary pooled DM p-values of the available primary cells only.

## Computation

The kit reuses the existing code and does not reimplement any statistics. It calls:
- `scripts/run/estimands_report.load_cell` for the rows, the default exclusions (no-geometry units and the primary incomplete weeks), the strata flags and the seeds;
- `pop.eval.estimands.compute_estimands_v2` for DM/EWC + HLN, the 95% and 90% t-CIs, TOST at 1% of WIS(L3), the MDE, the seed SD and the ID-share gate;
- `pop.eval.stats.holm` for the primary family.

The ladder is the seed-averaged mean of log1p WIS and the 40/80% coverage. It uses only the keys that every rung scores within the cell's estimand rows.

**Cache.** Results go to `runs/analysis_cache/<cell>/{est,ladder}.parquet` and `info.json`. The cache key covers:
- the size and mtime of every `scores.parquet` used;
- the exclusion files;
- the options and the cell's primary/secondary horizons (and `KIT_VERSION`, now 2).

## Outputs

**Tables.** These are written to `docs/results/tables/`, each as CSV plus a LaTeX booktabs `tabular` fragment that can be `\input`.

| File | Contents |
|---|---|
| `T1_primary_family` | The 14 cells, with: G_excess (pooled over h{1,4}); % of WIS(L3); 95% and 90% CIs (absolute and %); DM p; Holm p over the available cells (provisional while cells are pending); `p_bonf14`; TOST p and class; MDE; seeds and seed SD; `sec_*` = S1 secondary pooling over h1–h4. |
| `T2_ladder` (+ `T2_ladder_long.csv`) | WIS for L0–L4, L3+C\* and L4+C\*, per horizon, pooled over h{1,4}, and (S1) pooled over h1–h4 as a secondary column. Coverage at 40/80%, both overall and on rows with cases > 0. L0–L2 appear for S1 cells only. |
| `T3_estimands` | G_emb, G_id, G_excess and the ID share, per cell × horizon (`1`…`4`, `pooled` = h{1,4}, `pooled_h1-4` = S1 secondary) and per test year (primary horizons). |
| `T4_cstar_selection` | All candidates at the 2019 origin, as mean ± SD over seeds, with the selected C\*. Selections without `rule_version: 2` are listed as "selection pending (stale)". |
| `T5_strata` | Observed vs zero-filled targets, and outbreak vs non-outbreak weeks. Given pooled, and per year in the CSV. |
| `T6a_sensitivities` | Each variant vs its primary cell. |
| `T6b_nohist_estimands`, `T6c_nohist_ladder` | No-history arm. |

**Figures.** These are written to `docs/results/figures/` as PDF + PNG, using the Okabe–Ito colour-blind-safe palette.

| Figure | Contents |
|---|---|
| F1 | Forest plot of G_excess (pooled over h{1,4}) as % of WIS(L3), with 95% (thin) and 90% (thick) CIs and the ±1% band. Primary cells are blue, secondary cells grey, and pending cells are labelled. |
| F2 | S1 ladder per country. L0 is given in the panel title because its scale differs. When BR S1 is pending, the panel shows `BR_S1_perlevel`. |
| F3 | G_emb and G_excess per test year (pooled over h{1,4}) for the S1 cells. |
| F4 | No-history ladder. |

**Brief.** `docs/results/RESULTS_BRIEF.md` contains:
- the status of every cell;
- the headline numbers for each available cell, each with a one-line plain-language reading;
- the secondary comparisons;
- pointers to all outputs;
- a scheduler snapshot.

## Conventions

- **Gains.** A gain is positive when the second model has lower WIS. Percentages are of WIS(L3), or WIS(N3) in the no-history arm.
- **TOST classes.** *equivalent* means the 90% CI lies inside ±1%. *superior* and *inferior* mean the 95% CI excludes 0 and p < .05. *inconclusive* covers everything else.
- **Bootstrap.** The 52-week state-block bootstrap is a sensitivity analysis and is off by default.
