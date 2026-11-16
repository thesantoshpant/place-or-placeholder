# Experiment runner (`pop.runner`)

**Entry point:** `python scripts/run/run_experiment.py configs/<name>.yaml`. The script sets `OMP_NUM_THREADS` and related variables from `threads` before it imports numpy or LightGBM.

## Architecture
1. **Panel to grid.** `features/history.make_grid` turns the panel into a dense unit × week grid of `log1p(cases)`. It checks that the weeks are regular and that the grid is complete.
2. **Split.** `runner.select_split(grid, split, Y)` handles S1. Train rows are those whose **target** week falls in `[train_start_year, Y−1]`. Test rows are those whose target falls in `Y`. This function is the hook that the `pop.splits` API will replace.
3. **Features.** `runner.build` calls `LEVELS[level](grid, idx, h)` for all units × target weeks, with origin = target − h. When building training rows, it drops targets that are `flag_gap` or NaN.
4. **Model.** Models come from the `pop.models.MODELS` registry. Each implements `fit(X, y_log, quantiles)` and `predict_quantiles(X, q)`, which returns case-scale quantiles (n × Q). `finalize` clips them at ≥0 and sorts them, so the quantiles are monotone.
5. **Chunks.** Each chunk is one (model, level, seed, test year, horizon). Outputs go to `runs/<exp>/chunks/<chunk>.{forecasts,scores}.parquet` plus a `.done.json` with the timing, n_train and NB α. A chunk that already has a `.done.json` is skipped, so the run can be resumed.
6. **Scoring.** Scores come from `pop.eval.scoring.score_forecasts`: `wis_log` (primary), `wis_case`, `ae_*` and `cov_40`/`cov_80`. Rows whose target is `flag_gap` are dropped. The target's `zero_filled` flag is kept.
7. **Assembly.** The run writes `forecasts.parquet`, `scores.parquet`, `summary.csv` (means by run × horizon × test year, plus `all`), `dm.csv`, `timing.csv`, `config_resolved.yaml` (with frozen params and package versions) and `run.log`.

## Config schema
```yaml
exp_name, country, panel           # country matched case-insensitively
split: {name: S1, train_start_year: 2018}
test_years: [...]; tune_year: 2019; horizons: [1,2,3,4]
quantiles: [0.1..0.9]; coverage_levels: [0.4, 0.8]
exclude_flag_gap: true; seeds: [0]; threads: 16
runs: - {model, level, params?, tune?: {grid, horizons, quantiles}, name?}
dm_pairs: [[A, B], ...]          # run names, "<model>-<level>"
```

## Adding a feature level
1. Write `fn(grid, idx, h) -> DataFrame`. Read every grid value through `history._take`, which asserts that the source week is ≤ the origin week.
2. Register the function in `runner.LEVELS`.
3. Levels other than the controls must pass `history.assert_no_location`. History levels enforce this automatically.

Time-invariant covariates (such as embeddings) can be merged on `idx.u`, but only in the levels meant to carry them.

## Features
- **L0:** `sy1_0`, which is the log1p cases in target week − 52.
- **L1** (23 columns):
  - `lag_0..11` relative to the origin;
  - `sy{1,2,3}_{m1,0,p1}`, the target week minus 52j, and ±1 week around it;
  - `woy_sin/cos` of the target's epi week (period 52.18).
- Each horizon gets its own model.

## L0 quantile method
For each horizon and test year, we compute the errors `e = log1p(y_T) − log1p(y_{T−52})` on all training rows. The quantile τ is then `expm1(log1p(y_{T−52}) + Q_e(τ))`, clipped at 0.

## Models and tuning
- **NB:**
  - Model: statsmodels `NegativeBinomial` (NB2), with L1 features plus an intercept, on the raw counts.
  - Fitting: L-BFGS, which uses log α internally, starting from a Poisson GLM.
  - Quantiles: NB(μ, α) PPF.
  - No tuning.
- **LightGBM:**
  - Model: quantile objective on log1p, one booster per quantile and horizon.
  - Fixed settings: lr 0.05, 400 rounds, feature_fraction 0.9, bagging 0.8/1, λ₂ 1, 16 threads, deterministic, seed 0.
  - Tuning grid: `num_leaves ∈ {31,127}` × `min_data_in_leaf ∈ {100,1000}`. Configurations are compared on mean log-scale pinball loss at τ ∈ {0.1, 0.5, 0.9} and h ∈ {1, 4}, training on 2018 and validating on 2019.
  - Chosen: **127 / 100** (val pinball 0.0741, against 0.0743 for 31/100). These values are frozen for every test year.

## Results: Brazil S1 (`runs/brazil_s1_baselines`)
Analysis: `python scripts/run/analyze_run.py --runs runs/brazil_s1_baselines runs/brazil_s1_timesfm_zs`. Full write-up: `docs/results/brazil_s1_baselines.md`. Every model is scored on the same 1,439,937 rows per horizon with the same nine deciles. No scores are NaN and Brazil has no flag_gap weeks.

Mean log1p WIS, pooled 2020–24:

| model | h1 | h2 | h3 | h4 |
|---|---|---|---|---|
| L0 naive | 0.4645 | 0.4645 | 0.4645 | 0.4645 |
| L1 NB | 0.1894 | 0.2102 | 0.2279 | 0.2454 |
| **L1 LightGBM** | **0.1414** | **0.1628** | **0.1813** | **0.1992** |
| TimesFM 2.5 ZS | 0.1594 | 0.1829 | 0.2051 | 0.2252 |

- **DM tests** (EWC + HLN, Holm over 16 tests): LightGBM beats L0, NB and TimesFM at every horizon (p_holm ≤ 0.0015), and TimesFM beats L0.
- **Coverage on non-zero targets** (40%/80%): LGBM 0.31/0.68, NB 0.36/0.76, TimesFM 0.27/0.59. All models under-cover.
- **Case-scale WIS:** NB blows up (327–475), driven by a few units at epidemic peaks.
- **Zero fill:** the share of zero-filled targets rises to about 0.6–0.74 in 2022–24.
