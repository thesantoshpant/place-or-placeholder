# Compute plan (Paper 1 runner)

> **SUPERSEDED (2026-11-16).** The scope below (S0, S2 with 27/33 leave-one-state-out folds, 10 seeds for C3/C4 everywhere, controls on every test year) was cut: S0 dropped, S2 = 5 grouped folds, BR S3 = 5 folds, spatial splits at h {1, 4}, controls only at the 2019 origin with 3 seeds, final C\* runs with 1 seed. See `docs/plans/deviations_from_protocol.md` rows 3–4 and `docs/methods/split_pipeline.md` (global scheduler). The timing measurements and the determinism checks remain valid.

Measured 2026-11-16 on epyc2 (64 threads, shared; load ~40–50 from three live 16-thread runs, so
all timings are pessimistic). Scratch: `tmp/bench_parallel/` (scripts `build_design.py`, `fit.py`,
`compare.py`, `compute_model.py`; raw results `results.jsonl`, `compute_model.csv`).

## 1. Benchmark: one real chunk
Brazil S1, L3 (p = 86), test year 2023, h1: n_train = 1,439,937, n_test = 286,884. L3's frozen
params (31 leaves / min_data 100, 400 rounds). The design is built once and cached as npy, and
each fit is one quantile booster (τ = 0.5). A chunk = 9 boosters + ~20 s of features and scoring.

| threads | s / booster | core-s / booster | core efficiency vs 16 | chunk wall (≈9×) |
|---|---|---|---|---|
| 16 | 54 | 866 | 1.00 | ~490 s (prod: 511 s) |
| 8 | 89 | 710 | 0.82 | ~800 s |
| 4 | 141 | 562 | 0.65 | ~1,270 s |
| 2 | 255 | 510 | 0.59 | ~2,300 s |

- Feature build for the chunk takes 12 s and data load 7 s; peak RSS is 2.6 GB (data + design), and the LightGBM fit adds ~1.2 GB.
- `deterministic` off: 80 s vs 89 s at 8 threads, within noise. `force_col_wise` gives 83 s, also no real gain. Keep the current `deterministic=True, force_row_wise=True`.
- The 9 quantile boosters are independent and share one `Dataset`, so they can be fitted in parallel inside one chunk (thread pool, T/k threads each). This is just another way of splitting the cores, though: chunk-level workers give the same throughput with less code, so it is not implemented. A naive attempt (several `lgb.train` calls in a thread pool on one shared, not-yet-constructed `Dataset`) **segfaulted** (2 of 2 runs), so doing this would need one Dataset per thread or processes.

## 2. Determinism
- The same thread count gives **bit-identical** predictions (16/16, 8/8, 4/4).
- **Across thread counts the predictions were also bit-identical**: 16 = 8 = 4 = 2 threads (max |Δ| = 0 in log1p quantiles). The same holds with `deterministic=False` and with `force_col_wise`. With row-wise histograms, LightGBM's per-thread histogram reduction is exact enough here that the trees do not change.
- A full 9-booster fit at 16 threads took 459 s (51 s per booster), and its tau=0.5 column is identical to the single-booster fit, so fitting the boosters sequentially doesn't change anything. With `force_row_wise` dropped (auto) a booster takes 78 s at 8 threads, with identical output.
- Caveat: this was checked on one booster/chunk. The executor still records `threads` in every `.done.json` and `timing.csv`, and **all levels/controls that are compared (L3 vs L4, L3+C\* vs L4+C\*) must use the same `threads`, `deterministic=True`, `force_row_wise=True`, seed rule and LightGBM version** (4.7.0). Don't mix thread counts inside a comparison unless a check like the one above has been rerun for that configuration.

## 3. Recommended layout
- Throughput is proportional to core efficiency, so the best layout is **many workers × 4 threads**. Compared with the serial path (1 × 16), the speedups are:
  - 1 × 16 → **12 × 4** (48 threads, leaves 16 for other users): ~3 × 1/0.65 ≈ **4.6× per run**;
  - **16 × 4** (all 64 threads) ≈ 6.2×, but only when the server is otherwise idle;
  - 6 × 8 ≈ 3.7×; 3 × 16 = 3×.
- 2 threads would be ~10% more efficient per core but doubles memory per core and chunk latency, so it isn't worth it.
- Memory: workers are forked after the data are loaded and the level caches are warmed, so the grid and the climate/RS/AE arrays are shared copy-on-write. Each worker adds its design matrices plus LightGBM (~2–4 GB for BR L4 2024), so 12 workers come to ≈ 30–50 GB. That fits in the ~105 GB available; still, check `maxrss_gb` in `.done.json` on the first run.
- `python scripts/run/run_experiment.py <cfg> --workers 12 --threads 4`. Several configs can run at once if workers × threads summed over them stays ≤ ~48.

## 4. Full-protocol chunk counts and core-hours
- Model: chunk wall at 16 threads = a + b·n_train, fitted on the BR S1 production chunks (L3: 76 s + 302 s per M rows; L4: 206 + 351; L2: 199 + 285; L1: 66 + 145). Controls are scaled from the L3 timings on the 2019 controls run (C1 .91, C2 1.54, C3/C4 1.25, C5 1.34, L4+C\* 1.4). Core-h at 4 threads = 16 · wall · 0.65.
- Rows: units × 52.18 × (training years 2018..Y−1, capped at the country's last year). Spatial folds use the real `train_units` of each fold; S5 trains on the other three countries.
- Origins: BR 2020–24, CO 2020–22, PE 2020–23 (S1/S5 only), TW 2020, 2022–24 (2021 skipped, no local cases).
- Runs per split: naive-L0, NB-L1, LGBM L1–L4, L3+C1 (not S5), L3+C2, L3+C3 ×10 seeds, L3+C4 ×10 seeds, L3+C5, L4+C\*. 4 horizons each.

| split | country | chunks | core-h @4 thr |
|---|---|---|---|
| S0 | BR / CO / TW | 600 / 360 / 480 | 709 / 74 / 37 |
| S1 | BR / CO / PE / TW | 600 / 360 / 480 / 480 | 849 / 93 / 15 / 47 |
| S2 | BR (27 folds) / CO (33) | 16,200 / 11,880 | **22,239** / 2,963 |
| S3 | BR (10) / CO (6) | 6,000 / 2,160 | 7,394 / 383 |
| S4 | BR (5) / CO (5) | 3,000 / 1,800 | 3,546 / 370 |
| S5 | held out BR / CO / PE / TW | 580 / 348 / 464 / 464 | 265 / 418 / 710 / 811 |
| **total** | | **46,256** | **≈ 40,900** (62,960 at 16 thr) |

- By run: C3 + C4 × 10 seeds = 29,500 core-h (72%). Everything else = 11,400 core-h.
- **Wall clock, 12 × 4 on 48 cores:** full protocol ≈ 850 h ≈ **35 days**. Without the C3/C4 seed replicates it is ≈ 240 h ≈ **10 days**. Brazil S1 complete (all runs) ≈ 18 h; one BR S1 LGBM level (20 chunks, ~25 core-h) ≈ 0.5 h (vs ~2.4 h serial at 16 threads).
- These timings were taken under load, so an idle server may be ~1.2–1.4× faster. The NB/L0 costs are negligible.

## 5. Critical path
1. **S2 Brazil** (27 state folds × 5 origins) is 54% of all compute: 22k core-h, ≈ 19 days on 48 cores, and ≈ 5 days without the C3/C4 seeds.
2. **C3/C4 × 10 seeds on every spatial split.** Options to decide before the Jan 15 freeze:
   - 10 seeds only on S1 + S4, and 3 seeds on S2/S3, which cuts the total to ≈ 20k core-h (~17 days);
   - or run seeds only for C\* if C\* ∈ {C3, C4}, since C\* is chosen on the 2019 origin. Then C3/C4 seeds cost ~1/2 or nothing outside S1;
   - or score S2 only on G_excess runs (L3+C\*, L4+C\*, L3, L4).
3. **Order:** BR S1 (all), then BR S4 and S3, then CO all splits and S5, then BR S2. That way the headline Brazil temporal and coarse spatial results land first.
4. The upstream inputs (AlphaEarth for CO/PE/TW, RS for all countries) must be complete before the CO/PE/TW/S5 runs.

## Follow-ups (not done)
- A real end-to-end parallel run (e.g. BR L3 2023, 4 × 4 threads) to measure actual per-worker RSS with CoW sharing and to confirm the 9-quantile WIS against the 16-thread production chunk.
- Measure on an idle server to tighten the a + b·n model; also time S5 and the controls on 2020+ rows.
- The `L4+C*` level does not exist yet in `levels.LEVELS` (it is costed here as 1.4 × L3).
