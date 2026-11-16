# Split pipeline and queue (S0, S2–S5, S1 shared-params)

`scripts/run/split_pipeline.sh <country> <split>` runs one (country, split) end to end. Since 2026-11-16 14:36 every job runs under ONE global priority scheduler (`scripts/run/scheduler.py`, section "Global scheduler" at the end); the lane sections below are history.

## Pipeline (`split_pipeline.sh`)
- **Splits.** `s0`, `s2`, `s3`, `s4`, `s5` (the country argument is the held-out country), `s1brp` (Taiwan S1 with Brazil's params and C\* = C1), and `s1_shared` (S1 under the shared-params rule).
- **Configs** go to `configs/<c>_<s>_{controls_2019,L3,L4,L3_Cstar,L4_Cstar}.yaml`. **Runs** go to `runs/<c>_<s>_<stage>/`. **Pipeline state** goes to `runs/<c>_<s>/`: `pipeline.log`, `stage_*.done`, `PIPELINE_DONE`/`PIPELINE_FAILED`.
- **Stages:**
  1. `gen_configs`
  2. `controls_2019`: the 2019 origin with L3 plus C1 (dropped in S5), C2, C5, C3 ×3 seeds and C4 ×3 seeds
  3. `select_control`
  4. `gen_cstar`: if C\* ∈ {C3, C4}, the C\* runs use 3 seeds
  5. `L3`, `L4`, `L3_Cstar`, `L4_Cstar`: all test years, h1–h4

  A stage is skipped once its `.done` file exists, and chunks resume through flock claims, so you can kill and relaunch at any point.
- **Params (shared-params rule, no re-tuning).** Each country uses ONE set for every level and control: its S1 **L1** tuning (`runs/<c>_s1_baselines/tuning_lgbm-L1.json`). TW S0, all S5 jobs and `s1brp` use Brazil's L1 (127 leaves / min_data 100). CO and PE L1 = 31/100. TW L1 = 31/100.
- **`s1_shared` reuse.** A stage whose per-level S1 params already equal L1 reuses the existing S1 run; see `runs/<c>_s1_shared/plan.json` and `stage_*.reuse`.
  - BR: L3 reuses `runs/brazil_s1_L3_leaves127`.
  - CO: every stage is reused.
  - PE: L4 is reused. L4+C\* is reused if C\* is unchanged.
  - TW: everything reruns.
- **LST screen:** on for CO/PE/TW and for every S5 job (mixed countries). Off for Brazil S0–S4, as in Brazil S1.
- **C4 `range_km`:** each country's S1 value (BR 8483, CO 705, PE 148, TW 27 km). S5 uses a per-country dict. C1 uses `c1_period: auto`: pre-training years in S0/S1, and LOO-kNN over training rows in S2–S4.
- **Threads** are always 4 per worker.

## Queue (`queue.sh launch | status | budget | workers <L> | lane <L> | reap`)
- **Lanes since 2026-11-16 13:12** (see "Throughput 2026-11-16" below):
  - **A (`pop_qA`):** BR S1-shared → BR S4.
  - **C (`pop_qC`):** BR S3 → S5 (BR held out).
  - **D (`pop_qD`):** BR S2.
  - **B (`pop_qB`):** PE S1-shared → TW S1-shared → CO S4 → S2 → S3 → S5 (CO, PE, TW held out) → TW S1-BRparams → CO S1-shared. CO S1-shared waits until `pop_s1_colombia` has ended.
- **Workers** (4 threads each) are re-evaluated at every stage start and every 20 s within a stage. When the number rises, an extra `run_experiment.py` process joins the same config (if MemAvailable ≥ 12 GiB), and one final pass (leftover chunks + assembly) runs at the end of the stage. Counts never drop mid-stage.
  - **Budget** = 60 threads, or 52 while other users' CPU is > 4 cores (back to 60 below 3 cores; 2-s `top` sample, cached 60 s in `runs/queue/others_cpu`), minus 4 × `WORKERS` of each live `pop_s1_<c>` session.
  - budget/4 workers are split over the unfinished lanes by weight (remaining worker-h: A 135, B 95, C 93, D 98), largest remainder, ≥ 1 each. A finished lane's workers go to the others.
- **Manual pins:** `<L>_WORKERS=`, `W_<L>=` (weight) and `BUDGET=` (threads) in `runs/queue/override.env`.
- **Logs:** `runs/queue/lane_{A,B,C,D}.log`. A failed job is logged and the lane moves on to the next job. A lane never starts a job while another `split_pipeline.sh` runs it.
- **Scheduling:** `runner.submit_order` submits the latest test years first, which shortens the tail at the end of each stage.

## Measured chunk times and ETA (4 threads, server load ~55–60) — superseded by the scope cuts below
- **Measured chunk times:**
  - BR 2019 controls (n_train 0.29 M, 127 leaves): 490–520 s.
  - BR S1 L3 at 127 leaves: 730 s at 0.57 M rows, up to 1,810 s at 1.73 M rows, i.e. t ≈ 200 + 950·n[M] s.
  - PE: 20–45 s per chunk.
- **Model:** L4 ≈ 1.35× L3, L3+C ≈ 1.35×, L4+C ≈ 1.7×. Worker-hours are computed from the real fold sizes.
- **Estimated worker-hours** (C\* single-seed – C\* in {C3, C4} with 3 seeds):
  - Lane A: S1-shared 38–82, S4 191–374, S3 171–333, S2 191–374, S0 48–92, S5 18–34. Total **≈ 660–1,290**.
  - Lane B: **≈ 300–540**.
- **Wall clock:**
  - Lane A at 9 workers takes ≈ 3–6 days. Lane B at 4 workers takes ≈ 3–5.5 days.
  - Pooled at 13 workers: ≈ **74–140 h**. Add ~10–20% while `pop_s1_colombia` holds the budget at 28 threads.
  - Each BR spatial split's main cost is L3/L4/L3+C\*/L4+C\* over 5 folds × 5 years × 4 horizons at 127 leaves.

## Scope cuts 2026-11-16 (cut wall clock from ~3–6 days to ~1.5–2)
- **S0 dropped** (BR, CO, TW); removed from both lanes. `split_pipeline.sh` still accepts `s0` but nothing queues it.
- **Horizons.** Spatial splits S2–S5 use **h ∈ {1, 4}** in every stage (the 2019 `controls_2019` selection and the test-year runs). S1 (`s1_shared`, `s1brp`) keeps h1–h4. All test years are kept.
- **Seeds.** Final `L3_Cstar` / `L4_Cstar` runs use **1 seed** (seed 0) even when C\* ∈ {C3, C4}. The 2019 selection still uses 3 seeds for C3/C4.
- **S5 params** = the L1 tuning of the largest training country: Brazil's (127/100), or Colombia's (31/100) when Brazil is held out.
- **C1 matched leave-out** is the default (`train_mode="matched"`, see `docs/methods/controls.md`): training units in S2 exclude same-state neighbours, in S3 neighbours within D (BR 225 km, CO 130 km); S4 is plain LOO.
- **Lane B order:** CO S4 now runs before CO S2/S3. No S2/S3 stage had started, so no C1 chunks needed deleting.
- **Restart (12:42).** Both lanes were relaunched with the new lists. The two running S1-shared stages (BR `controls_2019`, PE `L3_Cstar`) lost only their in-flight chunks; 5 BR and 7 PE completed chunks were kept and resumed. `run_cfg` now waits for any leftover `run_experiment.py` on the same config before starting. BR and PE S1-shared configs that existed already were not regenerated; BR's `gen_cstar` (not yet run) will write 1-seed C\* configs.
- **ETA** (greedy simulation over real fold sizes; t = a + b·n per chunk from `runs/*/timing.csv`: BR L3 at 127 leaves 177 + 993·n[M] s, CO 52 + 813·n; multipliers vs L3: C1 1.0, C2 1.55, C5 1.35, C3 2.35, C4 2.3, L4 1.55; script `tmp/eta.py`, not versioned):

  | | C\* = C1 (as in BR/PE S1) | C\* = C3/C4 |
  |---|---|---|
  | Lane A worker-h (BR S1-shared rest, S4, S3, S2, S5) | 39 + 98 + 88 + 98 + 5 ≈ 330 | ≈ 470 |
  | Lane B worker-h (CO S4/S2/S3/S5, PE S5, TW S5; S1 jobs < 2) | 11 + 11 + 13 + 14 + 21 + 24 ≈ 95 | ≈ 130 |
  | Lane B wall at 4 workers | ≈ 25 h | ≈ 34 h |
  | Lane A wall (9 workers, 13 after lane B ends) | ≈ 33 h | ≈ 47 h |

  Add a few hours while `pop_s1_colombia` holds the budget at 5 + 2 workers. Chunk times rise if the server load climbs.


## Throughput 2026-11-16
- **Measured inefficiency (13:04).** Tails and setup were small: 13 parallel runs today (`runs/*/run.log`) kept their workers 89–100% busy, BR data load is ~10 s per stage and `select_control` takes 2 s. The real losses were:
  - **Unused budget.** While `pop_s1_colombia` ran, the queue held 28 threads (A 5 + B 2), so 40 of 64 hardware threads were busy (load ~50) and 24 sat idle.
  - **Lane imbalance.** Lane B (~95 worker-h) would end ~9 h before lane A (~330 worker-h), and all of Brazil was serial inside one lane.
- **Change.**
  - Brazil is split over three lanes (A: S1-shared → S4; C: S3 → S5; D: S2), with work-weighted shares of one budget of 60 threads.
  - `run_cfg` counts `run_experiment.py` processes already running on a config as workers instead of waiting them out.
  - Chunk definitions, params, seeds and threads (4) are unchanged, so results are identical.
  - Concurrent stages within a split (option a) were not built. They would recover only the ~3% tail loss and would need a stage-DAG rewrite.
- **Handover 13:11.**
  - New scripts were installed by atomic `mv`, so running bash processes kept the old file.
  - Killing the old lane loops also ended their process groups, even though remain-on-exit was set and the sessions were renamed. The in-flight chunks were lost: BR S1-shared `controls_2019` (≤ 5 chunks of ~8 min) and TW S1-shared `L3_Cstar` (2 short chunks). Every `.done.json` chunk was kept (16/40 BR).
  - **Next time:** change the scripts with `mv` only. The lanes pick up the new `queue.sh workers` at once and the new `split_pipeline.sh` at their next job. Do not kill lane loops.
- **Layout now.** 4 lanes; A 4, B 3, C 2, D 3 workers + `pop_s1_colombia` 3 = 60 threads. After `pop_s1_colombia` ends: A 5, B 3, C 3, D 4 = 60 threads.
- **ETA** (event simulation of the lanes with the dynamic split, `tmp/eta3.py`, CO S1 ending ~5.7 h after 13:12):

  | | C\* = C1 | C\* = C3/C4 |
  |---|---|---|
  | Lane D (BR S2) | 26.5 h | 37 h |
  | Lane A (BR S1-shared, S4) | 28 h | 40 h |
  | Lane B (CO/PE/TW) | 30 h | 42 h |
  | Lane C (BR S3, S5) | 30 h | 42.5 h |
  | **All done** | **≈ 30 h** (Nov 17 ~19:00) | ≈ 42.5 h (Nov 18 ~08:00) |
  | Old 2-lane layout | 36.5 h | 51 h |
  | New layout at the 52-thread fallback | 34 h | 48 h |

  The floor is total work ÷ threads: 421 worker-h needs ≈ 29 h at 15 workers (12 while CO S1 runs). Finishing in ≤ 24 h would take ~70 threads, which is more than the 64 on the machine.

## Control fixes 2026-11-16
- C3 (fixed source per unit), C1 in S2–S4 (pre-training years) and the new C4s (C4 at range D) are described in `docs/methods/controls.md`, section "Control fixes 2026-11-16". controls_2019 now has C4s ×3 seeds as a seventh candidate.
- Lanes were stopped at 13:40–13:48 (lanes A/B at once; C, D and `pop_nohist` after their in-flight chunks of unaffected runs had finished), the affected chunks were moved aside (`runs/queue/invalidation_2026-11-16.md`, `scripts/run/invalidate_control_fixes.py`), and everything was relaunched at 13:49 with `queue.sh launch`, `nohist_pipeline.sh launch s1 s2 s3` and `s1_pipeline.sh peru|taiwan` (per-level selection rerun). `pop_s1_colombia` finishes its superseded L3+C4 stage, skips L4_Cstar (PAUSE marker), and `tmp/fix/colombia_watch.sh` (tmux `pop_fixwatch`) then invalidates and relaunches it.
- `gen_cstar` now resets the final stages when C\* changes (`scripts/run/supersede.py guard_final`), so a rerun selection that picks a different C\* regenerates the C\* configs and reruns L3_Cstar/L4_Cstar; an unchanged, unaffected C\* final run is kept.


## Global scheduler 2026-11-16 (replaces the lanes above)
- **What.** `scripts/run/scheduler.py run` (tmux `pop_sched`; `queue.sh launch | status | eta | stop`) is the only process that starts `run_experiment.py` workers for the queue. Each item is one pipeline in tmux `pop_q_<item>` (`split_pipeline.sh` / `nohist_pipeline.sh` with `POP_SCHED=1`). The pipelines keep their stage order. On entering a run stage, a pipeline writes `runs/<item>/current_cfg`, waits until every chunk of that config has a `.done.json`, then runs one assembly pass (`--workers 1`). Log `runs/queue/scheduler.log`; snapshot `runs/queue/state/snapshot.json`; chunk lists `runs/queue/state/tasks/`; exit codes of scheduler-started workers `runs/queue/state/exits.log` (3 non-signal failures on a config → `state/failed_<config>` → that stage fails).
- **Priority** (tier, then list order):
  - **T1:** BR S1-shared; PE/TW S1-shared; CO S1 per-level (`pop_s1_colombia`, external); CO S1-shared (waits for `pop_s1_colombia`); TW S1-BRparams.
  - **T2:** BR S1 extra seeds (`sens_seeds`, waits for the BR S1-shared `gen_cstar`); S5 BR/CO/PE/TW; CO S2/S3/S4; BR S2; BR S3.
  - **T3:** no-history BR S1, then BR S2 (queue items now; `pop_nohist` retired; **no-history S3 dropped**).
  - **T4:** BR S1 sensitivity `sens_yref`, `sens_delay`, `sens_ctrl`.
  - **T5:** BR S4.
- **Allocation (every 20 s).** Budget = 60 threads, or 52 while other users use > 4 cores (`BUDGET=` in `runs/queue/override.env` pins it) → 15 workers × 4 threads. Every `run_experiment.py` of this user counts against it, including external sessions and leftovers. A worker is "held" while its tree has a chunk in flight (a live `.lock` file). A process younger than 5 min holds its full `--workers`, to cover data loading. Free workers go to items in priority order, each up to the unclaimed chunks of its current stage; one new process per item per tick (MemAvailable ≥ 12 GiB). Pipelines of pending items start one per tick, since their config and selection stages cost nothing.
- **Flow to higher tiers (lossless).** If a stage has unmet demand for 2 ticks and no worker is free, the scheduler takes the flocks of the unclaimed chunks of the lowest-priority running stage(s) of a strictly lower tier. This is the same `chunks/<name>.lock` claim a worker makes. Those processes finish their in-flight chunks and then cannot claim more. A process tree with no chunk in flight for 2 ticks is stopped, and the reservation is released once the stage has no process left. No running chunk is ever killed. Within a tier there is no preemption.
- **External.** `pop_s1_colombia` keeps its own processes. The scheduler writes its `runs/colombia_s1/override.env` `WORKERS`, which `s1_pipeline.sh` reads at each stage start.
- **Safety.**
  - Chunks are claimed by flock and skipped once `.done.json` exists, so nothing completed is recomputed. The scheduler takes reservations only on chunks that are neither done nor locked.
  - `--inside` takes `runs/<item>/.pipeline.lock` (flock, fd closed for child processes), so a second pipeline on the same item exits at once. The scheduler also refuses to start an item while a pipeline process for it exists (bracket `pgrep`).
  - A second scheduler exits (`runs/queue/.scheduler.lock`). Stopping `pop_sched` leaves items and workers running; reservations are released with the process.
  - Unchanged: chunk definitions, params, seeds and threads (4), so results are unchanged.
- **Sensitivity items (Brazil S1; horizons {1, 4}; shared params `runs/brazil_s1_baselines/tuning_lgbm-L1.json`; 4 threads; 2020–24).** Configs are copies of `configs/brazil_s1_shared_*.yaml`; run dirs `runs/brazil_s1_sens_<stage>/`; pipeline state `runs/brazil_s1_sens_{seeds,yref,delay,ctrl}/`.
  - (a) `seed{1,2}_{L3,L4,L3_Cstar,L4_Cstar}`: same run names as the shared runs (`lgbm-L3`, …), seed 1 or 2, so they pool as extra seeds. The shared seed-0 L3 is `runs/brazil_s1_L3_leaves127` (run name `lgbm-L3-leaves127`).
  - (b) `yref_{L3,L4}`: `yearly_ref: origin`.
  - (c) `delay2_{L3,L4}`: `report_delay: 2` (levels.py: L0/L1 lags and seasonal terms read only weeks ≤ origin − 2, lags taken relative to origin − 2; calendar, climate, RS, embeddings, controls unchanged; tests `test_report_delay_*`).
  - (d) `ctrl_{L3,L4}_{C3,C6}`: controls panel, seed 0.
- **Handover 14:36.** The lane loops were ended, the scheduler started, and every completed chunk was kept. Freezing the lane sessions' pane shells (SIGSTOP) did not protect their workers: tmux sends SIGCONT to a stopped pane process, so the shells exited and the hang-up killed the lanes' in-flight chunks (≈ 45–75 worker-min; `runs/queue/handover_2026-11-16_scheduler.md`). **Next time:** stop the scheduler (`queue.sh stop`) and replace files with `mv`. Item pipelines read their scripts at start, and workers are in their own sessions (`setsid`), so neither needs killing.
- **ETA** (`queue.sh eta`: chunk-level event simulation at 15 workers in priority order. Per-chunk seconds come from the stage's own finished chunks, else the country's S1 L3 median × level multipliers; C\* assumed C1. Run at 14:45):

  | Tier | worker-h | complete |
  |---|---|---|
  | T1 (BR S1-shared 49, CO S1 39, CO S1-shared 6, TW < 1) | ≈ 95 | +7.7 h, Mon Nov 16 ~22:30 |
  | T2 (sens seeds 40, S5 77, CO S2–S4 37, BR S2 106, BR S3 106) | ≈ 365 | +32.5 h, Tue Nov 17 ~23:00 |
  | T3 (nohist S1 36, S2 109) | ≈ 145 | +44 h, Wed Nov 18 ~11:00 |
  | T4 (yref 10, delay 10, ctrl 31) | ≈ 51 | +44.5 h, Wed Nov 18 ~11:00 |
  | T5 (BR S4) | ≈ 108 | +52 h, Wed Nov 18 ~19:00 |

  The simulation assumes perfect chunk-level flow. Real flow waits up to one chunk (≤ 30 min for BR) at each preemption, and CO S1 per-level gets new workers only at its stage starts.
