# Split pipeline and queue (S0, S2–S5, S1 shared-params)

`scripts/run/split_pipeline.sh <country> <split>` runs one (country, split) end to end. `scripts/run/queue.sh` runs every job in two tmux lanes. Both were launched on 2026-11-16 at 12:26.

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
