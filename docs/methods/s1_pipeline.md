# S1 pipeline for Colombia, Peru and Taiwan

> **Scope note (2026-11-16).** This is the **per-level** S1 pipeline (per-level tuning), now a sensitivity analysis (deviations row 2). The 10-seed C3/C4 rule below applies only here. The primary S1 cells use `split_pipeline.sh <country> s1_shared` (one parameter set per country; 3 seeds for C3/C4 at selection; **final C\* runs use 1 seed**, except the Brazil S1 primary cell, which uses seeds 0–2 at h {1, 4}, row 22). C\* is chosen by selection rule v2 (row 19); C4/C4s were no-ops in Colombia and Taiwan before the fix of row 18.

`scripts/run/s1_pipeline.sh <colombia|peru|taiwan> [--workers N] [--threads T]` runs the whole
S1 (temporal) ladder for one country in tmux session `pop_s1_<country>`. It copies the Brazil
protocol (configs `brazil_s1_*.yaml`), with one change: the LST outlier screen is on.

## Stages
Stages run in order. A stage is skipped if `runs/<country>_s1/stage_<name>.done` exists, and
`run_experiment.py` resumes at chunk level, so you can kill the session and relaunch it safely.

1. `gen_configs` writes `configs/<country>_s1_{baselines,L2,L3,L4,controls_2019}.yaml`.
2. `baselines`: naive-L0, NB-L1 and LGBM-L1.
3. `L2`.
4. `L3`.
5. `L4`.
6. `controls_2019`: L3 + C1..C5 on the 2019 origin only, with the L3 tuning frozen. C3 and C4 run 10 seeds. C4 `range_km` comes from `fit_embedding_range` on that country's renormalised 2017–18 embeddings, cached in `runs/<country>_s1/c4_range_km.json`: CO 705 km, PE 148 km, TW 27 km.
7. `select_control` runs `scripts/run/select_control.py runs/<country>_s1_controls_2019`.
8. `gen_cstar` writes `configs/<country>_s1_{L3,L4}_Cstar.yaml` from `selection.json`. A C\* of C3 or C4 gets 10 seeds; any other control gets 1 seed.
9. `L3_Cstar` and `L4_Cstar`, with `params_from` the L3 and L4 tunings respectively.

The LightGBM grid, budget and tuning origin (2019) are the same as Brazil's. Test years: CO 2020–22, PE 2020–23, TW 2020 and 2022–24. TW 2021 has no local cases, so it is not a test year. It stays in training for later origins as true zeros.

## Run files
- **Outputs:** each run writes to `runs/<country>_s1_<stage>/`, with stdout in `stdout.log` inside that folder.
- **Pipeline log:** `runs/<country>_s1/pipeline.log`.
- **Markers:** `runs/<country>_s1/PIPELINE_DONE`, or `PIPELINE_FAILED`, which names the failing stage.
- **Changing workers or threads:** put `WORKERS=N` (and optionally `THREADS=T`) in `runs/<country>_s1/override.env`. The pipeline reads it at the start of each stage. Keep THREADS fixed within a country.
- **Pre-flight results:** `runs/<country>_s1/preflight.json`, written by `tmp/s1_preflight/preflight.py`.

## LST outlier screen (`features.remote_sensing.lst_screen: true`)
MODIS LST has cloud-contaminated cold values. `levels.screen_lst` sets `lst_day_pw` and `lst_night_pw` to NaN where a value is more than 10 °C below the unit's calendar-month median. The median uses years ≤ 2017 only, i.e. before the first training target year. That keeps the screen causal and makes it identical at every origin. The option defaults to off, so the Brazil configs are unchanged.

Flagged share of finite unit-months (v1 table, all years):

| country | lst_day | lst_night | night min before → after |
|---|---|---|---|
| Brazil | 0.08% | 0.02% | 0.0 → 1.0 °C |
| Colombia | 0.06% | 0.57% | −42.4 → −3.7 °C |
| Peru | 0.06% | 0.18% | −16.5 → −5.9 °C |
| Taiwan | 0.05% | 0.06% | −2.1 → 3.4 °C |

## Pre-flight findings
- **Unit coverage:** the climate, RS, population and AlphaEarth tables cover every unit that has a polygon: CO 1,070/1,071 and TW 285/287. The units without a polygon get NaN features, which LightGBM handles. They are ~0.1% of the CO design and 0.7% of the TW design. LST NaN after the screen is ≤ 0.9%.
- **Non-zero targets at the 2019 tuning origin (h1, train 2018 → validate 2019):** CO 9,655 → 17,513 (fine). PE 825 → 1,237, from 62–72 of 115 units (thin, but workable). TW 95 → 56, from 33 and 26 of 287 units, out of about 14.9k rows each. For TW, the tuning and the C\* choice are therefore nearly uninformative: they are dominated by zero targets.
