# Experiment runner (`pop.runner`)

**Entry point:** `python scripts/run/run_experiment.py configs/<name>.yaml`. The script sets `OMP_NUM_THREADS` and related variables from `threads` before it imports numpy or LightGBM.

## Architecture
1. **Panel to grid.** `features/history.make_grid` turns the panel into a dense unit × week grid of `log1p(cases)`. It checks that the weeks are regular and that the grid is complete.
2. **Split.** The `pop.splits` API (S0–S5, see `docs/methods/splits.md`). For each fold and origin Y, `get_split` gives the unit sets and years (train targets 2018..Y−1, test targets in Y). `row_masks` on the grid rows gives `train`, `test`, `score` and `train_target_ok`, and `runner.split_masks` reshapes them to (U, W) and caches them. Training uses `train` minus NaN targets, and minus `flag_gap` when `exclude_flag_gap` is set; that equals `train_target_ok`. Test rows are `test`, and scoring drops `flag_gap`, which equals `score`. Under S5 the panels of all four countries are loaded and training rows come from the other countries' grids.
3. **Features.** `runner.build` calls `LEVELS[level](grid, idx, h, ctx)` on the target cells of a mask, with origin = target − h. `ctx` is a per-country `levels.Context` that holds the non-case inputs and the current split.
4. **Model.** Models come from the `pop.models.MODELS` registry. Each implements `fit(X, y_log, quantiles)` and `predict_quantiles(X, q)`, which returns case-scale quantiles (n × Q). `finalize` clips them at ≥0 and sorts them, so the quantiles are monotone.
5. **Chunks.** Each chunk is one (model, level, fold, seed, test year, horizon); the name gets `__f<fold>` only when the split has folds. Forecasts and scores carry `split` and `fold` columns. Outputs go to `runs/<exp>/chunks/<chunk>.{forecasts,scores}.parquet` plus a `.done.json` with the timing, n_train and NB α. A chunk that already has a `.done.json` is skipped, so the run can be resumed.
6. **Scoring.** Scores come from `pop.eval.scoring.score_forecasts`: `wis_log` (primary), `wis_case`, `ae_*` and `cov_40`/`cov_80`. Rows whose target is `flag_gap` are dropped. The target's `zero_filled` flag is kept.
7. **Assembly.** The run writes `forecasts.parquet`, `scores.parquet`, `summary.csv` (means by run × horizon × test year, plus `all`), `dm.csv`, `timing.csv`, `config_resolved.yaml` (with frozen params and package versions) and `run.log`.

## Config schema
```yaml
exp_name, country, panel           # country matched case-insensitively
split: {name: S1, folds: all}    # S0..S5; folds: all | [..]; optional split_dir, seed
features: {climate_lag_vars: [tmean, precip, rh], yearly_ref: target,
           alphaearth: {weights: w, normalize: true}, control_kw: {C4: {range_km: ...}}}
test_years: [...]; tune_year: 2019; horizons: [1,2,3,4]
quantiles: [0.1..0.9]; coverage_levels: [0.4, 0.8]
exclude_flag_gap: true; seeds: [0]; threads: 16
runs: - {model, level, params?, tune?: {grid, horizons, quantiles}, name?, seeded?,
        params_from?: runs/<exp>/tuning_<run>.json}   # reuse frozen params; params override
dm_pairs: [[A, B], ...]          # run names, "<model>-<level>"
```

Tuning uses origin `tune_year` (train 2018, validate 2019) of the split's first fold, with the same grid for every level, and is then frozen for all folds and test years.

`params_from` (instead of `tune`) takes the `best` params of another run's tuning file; keys in `params` override them. The L3+Ck control runs use it to share L3's frozen params. `seeded: false` runs only the first seed in `seeds` (used for C1/C2/C5/C6 when C3/C4/C4s run several seeds; 3 at the 2019 selection). A test year of 2019 is allowed (train targets 2018 only), which is what C* selection uses (`configs/brazil_s1_controls_2019.yaml`, then `scripts/run/select_control.py`).

## Adding a feature level
1. Write `fn(grid, idx, h, ctx) -> DataFrame` in `src/pop/features/levels.py`. Read weekly values through `history._take`, which asserts that the source week is ≤ the origin. Read monthly and yearly values through `levels._take_before`, which asserts that the source period is strictly before the limit.
2. Register the function in `levels.LEVELS`.
3. L0, L1 and L2 (`levels.NO_LOCATION_LEVELS`) must pass `history.assert_no_location`, and `runner.build` enforces this. L3 and above carry population and built-up share on purpose.

## Features
- **L0:** `sy1_0`, which is the log1p cases in target week − 52.
- **L1** (23 columns):
  - `lag_0..11` relative to the origin;
  - `sy{1,2,3}_{m1,0,p1}`, the target week minus 52j, and ±1 week around it;
  - `woy_sin/cos` of the target's epi week (period 52.18).
- **L2** (74 = 23 + 51): L1 plus pop-weighted ERA5-Land climate (`climate_weekly_<c>_v1`), relative to the origin week.
  - Lags 0–11 of `tmean`, `precip`, `rh` (36): `<v>_l<k>`.
  - 4-, 8- and 12-week rolling means of `tmean`, `tmin`, `tmax`, `precip`, `rh` (15): `<v>_r<k>`, the mean of lags 0..k−1.
  - Why: tmin and tmax are highly collinear with tmean at weekly lags, so they enter only as rolling means. All 5 × 12 lags would give 98 columns. `features.climate_lag_vars` changes this.
- **L3** (86 = 74 + 12):
  - `ndvi_pw`, `lst_day_pw`, `lst_night_pw` for the 3 latest complete months, `_m1.._m3` (9). A month counts only if it ended before the origin week starts (month < month of the origin week). MODIS composites are assigned to the month that holds their last day.
  - `ntl_pw_y1` and `built_share_y1` from `rs_yearly`, year y−1 (2).
  - `log_pop_y1` = log1p of GHSL-interpolated population, year y−1 (1).
- **L4** (150 = 86 + 64): `ae_00..ae_63`, the AlphaEarth `w_A*` vector (pop-weighted) for year y−1, renormalised to unit L2 length. Options: `alphaearth.normalize: false` and `alphaearth.weights: u`. Files: `data/interim/alphaearth/<c>/alphaearth_<c>_<year>.parquet`.
- **Feature summary per level** (Brazil column counts):

| level | adds | p |
|---|---|---|
| L0 | `sy1_0` | 1 |
| L1 | `lag_0..11`, `sy{1,2,3}_{m1,0,p1}`, `woy_sin/cos` | 23 |
| L2 | L1 + climate lags/rolling means | 74 |
| L3 | L2 + `ndvi/lst_day/lst_night_pw_m1..m3`, `ntl_pw_y1`, `built_share_y1`, `log_pop_y1` | 86 |
| L4 | L3 + `ae_00..ae_63` (AlphaEarth y−1, unit length) | 150 |
| L3+C1 | L3 + `c1_te`: mean log1p(cases) over the **pre-training years** (panel years before the first training target year 2018; Brazil 2014–17; flag_gap weeks dropped), the same value at every origin. S0/S1: the unit's own pre-training mean, identical for training and test rows. S2–S4: inverse-distance kNN (k = 5, same country) of training units' pre-2018 means; held-out units use the training pool, and training units get a **matched leave-out** value (S2: neighbours in their own state excluded; S3: neighbours within the buffer D excluded; S4: plain leave-one-out). S5: not applicable (`ControlNotApplicable`) | 87 |
| L3+C2 | L3 + `c2_lat`, `c2_lon` + 80 real spherical harmonics l=1..8 (no constant) | 168 |
| L3+C3 | L3 + `c3_A00..A63`: the real AlphaEarth y−1 vector of a **fixed source unit**, drawn once per country and seed and used in every year (a stable fake district ID). S0/S1/S5: a permutation of each country's units within that country (never the identity); S2–S4: training units permuted among themselves, each held-out unit gets one random training unit of its country | 150 |
| L3+C4 | L3 + `c4_f00..f63`: 64 Gaussian random fields, exp(−d/range_km), standardised (seeded); fitted range (Brazil 8,483 km) | 150 |
| L3+C4s | L3 + `c4s_f00..f63`: as C4 at range min(D, fitted) (Brazil 225 km, Colombia 130 km; equal to C4 in Peru and Taiwan, so not a candidate there) | 150 |
| L3+C5 | L3 + `c5_A00..A63`: AlphaEarth 2023 for every year | 150 |
| L3+C6 | L3 + `c6_unit_cat`: the unit ID as one LightGBM categorical feature; S0/S1 only (`ControlNotApplicable` when test units are unseen) | 87 |

- **L3+C1..C6** (and L4+Ck): L3 plus `controls.make_controls_for_split(...)`, which **replaces** the AlphaEarth block. The control is refit per (split, fold, origin, seed). C1 uses training units' pre-training-year rows only (`controls.c1_source_rows`; the legacy training-target definition is `c1_period="train"`). C3 is merged on the embedding year y−1. C3 and C5 take their embeddings from the same processed AlphaEarth table as L4. C4 needs `control_kw.C4.range_km`. Points come from `controls.load_unit_points()`.
- **y−1 alignment (L3 yearly columns, L4, C3):** for a forecast row (unit u, origin week o, target week t = o + h), y = epi-year of t (`grid.year[t]`, the year of the target week's Wednesday). Yearly inputs (`ntl_pw_y1`, `built_share_y1`, `log_pop_y1`, `ae_*`, `c3_*`) are read from year y−1 through `_take_before`, which asserts source year < y. So 2020 targets use AlphaEarth 2019, ..., 2024 targets use 2023; training targets 2018 use 2017. Monthly inputs are aligned to the origin, not the target. Checked on the L3 design (2020 and 2024 origins, h1/h4): hand-computed `ndvi_pw_m1` and `ntl_pw_y1` match the source tables; NaN share of the 12 new L3 columns is 0 except `lst_night_pw_m*` (0.07–0.17%, cloud gaps).
- **Units without an embedding:** Fernando de Noronha (IBGE 2605459) has no AlphaEarth pixels in 2017–2021 (all-NaN vector, pop_sum 0); it is valid from 2022. `renormalize` maps a non-finite or zero norm to an all-NaN row, so only that unit's rows get NaN `ae_*` (LightGBM routes NaN natively; target years 2018–2022 for this unit). C3 hands that NaN vector (years 2017–2021) to the unit whose fixed source is Fernando de Noronha (also NaN-safe). C5 uses 2023, which is valid. `fit_embedding_range` drops units with NaN embeddings before the variogram.
- **C4 range_km (Brazil):** 8,483 km, the exponential scale fitted by `controls.fit_embedding_range` on the renormalised 2017–2018 embeddings (the years available at the 2019 selection origin), default binning. The within-Brazil variogram of the embeddings rises almost linearly out to ~2,100 km with no sill, so the scale is weakly identified (2017 alone 11,398 km; 2018 alone 6,105 km; ≤500 km only 913 km). The launch script re-fits it and stops if it moved by >1%.
- **Yearly rule:** y is the target's epi-year, so yearly data come from y−1. This matches the protocol's "embeddings y−1 for target year y". For the ≤4 targets each January whose origin falls in the previous epi-year, y−1 equals the origin's year. `features.yearly_ref: origin` uses (origin year − 1) instead, which is strictly causal.
- **Missing inputs:** if an input has not been built, the level raises `levels.MissingInput`.
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
  - Per level (same grid): L1 127/100, L2 127/100, **L3 31/100** (val pinball 0.07369 vs 0.07374 for 127/100; the grid is almost flat). L4 is tuned the same way. L3+Ck reuse L3's params. Per-level tuning is now a sensitivity analysis: since deviation D2 the primary runs use one shared parameter set per country (tuned on L1 at the 2019 origin) for all levels and controls.

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

## Parallel executor
- `python scripts/run/run_experiment.py <cfg> --workers N --threads T [--start-method fork|spawn]`. The default is `--workers 1`, the serial path. `--threads` overrides the config's `threads` and is recorded in `config_resolved.yaml`, in each `.done.json` and in `timing.csv`. Layout and costs are in `docs/methods/compute_plan.md`; the recommended layout is 12 × 4.
- **Claiming:** a chunk is claimed with a non-blocking `flock` on `chunks/<chunk>.lock`, and `.done.json` is re-checked once the lock is held. The kernel releases the lock when the holder exits or is killed, so there are no stale claims (checked on the MooseFS mount). Several invocations on the same run dir, serial or parallel, never compute the same chunk. A chunk held by another process is skipped and waited for at the end (`WAIT_SECONDS` poll); if its holder died, the chunk is computed then.
- **Crash safety:** forecasts, scores and `.done.json` are written via `*.tmp.<pid>` + `os.replace`, with `.done.json` last, so a chunk without `.done.json` is redone. A failed chunk doesn't stop the others; the run raises at the end, and a rerun resumes it.
- **Tuning** runs once, before the workers start: in a forked helper process for the fork path, because the parent must never run OpenMP. GNU libgomp, which LightGBM uses, hangs in forked children after the parent has used it; this was reproduced. If this interpreter has already fitted a model (e.g. tests), the pool falls back to `spawn`, where each worker reloads the data.
- **Memory:** with fork, the parent loads the data and warms each level's grid-aligned caches (climate/RS/AE arrays) before forking, so workers share them copy-on-write. `maxrss_gb` per chunk is in `.done.json`.
- Chunk compute (`run_chunk`) is unchanged. At equal `threads`, parallel output is bit-identical to serial output (`tests/test_runner.py`).
