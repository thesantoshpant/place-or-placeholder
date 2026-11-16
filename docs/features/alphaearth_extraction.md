# AlphaEarth production extraction (Brazil, Colombia, Peru, Taiwan)

**Code:** `src/pop/features/alphaearth_extract.py`, `scripts/features/extract_alphaearth.py`, `tests/test_alphaearth_extract.py`.
**Outputs:** `data/interim/alphaearth/brazil/`
- `alphaearth_brazil_<year>.parquet`, one per finished year, and `alphaearth_brazil.parquet` with all finished years. Columns:
  - `unit_id`, `year` (image year)
  - `w_A00..w_A63`: population-weighted mean
  - `u_A00..u_A63`: unweighted (area) mean
  - `w_norm`, `u_norm`: norms of the raw means. Means are **not** renormalised; that happens downstream.
  - `w_fallback`: True if the unit has no population; `w_*` then equals `u_*`.
  - `pop_sum`: GHSL people, coverage-weighted
  - `area_km2_covered`: area of valid embedding pixels at 300 m
  - `n_pixels`: the same, as 100 m-equivalent pixels
- `chunks/<year>/<UF>.parquet`: raw sums (`ws_*`, `pop_sum`, `us_*`, `cov_sum`), plus a `.done` marker.
- `ledger.csv`: one row per chunk or verification. Records EECU-s (total and by pass), the source of each EECU figure, request counts, bytes, wall time, units, state km² and fetched km².
- `ghsl/`: cached sparse GHSL rasters per state × epoch.
- `verify_2023_*.json`

**Other countries:** `data/interim/alphaearth/<country>/` for `colombia`, `peru`, `taiwan`, same layout and schema (`alphaearth_<country>_<year>.parquet`, `alphaearth_<country>.parquet`, own `ledger.csv`, `chunks/`, `ghsl/`). The chunk region is the adm1 name, slugged (e.g. `CHANGHUA_COUNTY`). Units without geometry are skipped and logged as `SKIP_NO_GEOMETRY`: `COLOMBIA|CHOCO|BELEN DE BAJIRA`, `TAIWAN|HSINCHU CITY|OTHER`, `TAIWAN|TAINAN CITY|OTHER`.

**Logs:** `runs/alphaearth_multi/extract.log` (from 2026-11-16 08:14 UTC; before that, `runs/alphaearth_brazil/extract.log`). The run is in tmux session `pop_alphaearth`.

## Method
- **Grid:** the GHSL `GHS_POP` native Mollweide grid (origin −18041000, 9000000). Population and embedding pixels coincide exactly.
- **Image:** the annual mosaic of `GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL`, read via the pyramid (MEAN). It is fetched with `ee.data.computePixels` as float32 NPY.
- **Weighted pass (100 m):**
  - The pass runs over 128×128-pixel blocks. A block is fetched only where coverage × population > 0 for some unit of the state, and only the populated bounding rectangle is fetched.
  - **Sparse blocks** (≤3 of the 16 sub-blocks of 32×32 populated) fetch only those sub-blocks. Each request costs at least ~0.4 EECU-s; a full block costs 1–3 EECU-s.
  - **Weight** = exactextract coverage fraction × GHSL people. GHSL values are masked to ≥0 and **linearly interpolated between epochs**: 2017 = 0.6·2015 + 0.4·2020, …, 2023 = 0.4·2020 + 0.6·2025, 2024 = 0.2·2020 + 0.8·2025.
- **Unweighted pass (300 m):** all 256×256 blocks touched by the state's units, cropped to the touched cells. Weight = coverage.
- **Sums:** the run keeps raw sums. Means are derived only in `sums_to_means`. Pixels without an embedding get no weight.
- **Chunks:**
  - A chunk is one state (UF, from the first 2 digits of `unit_id`) × one year.
  - Years run in the order 2023, 2022, 2021, 2020, 2019, 2018, 2017, then 2024. Within a year, states run from smallest to largest.
  - Blocks on state borders are fetched once per state.
  - Queue: Brazil 2023→2017, then 2024; Colombia 2023, 2021→2017; Peru 2023→2017; Taiwan 2023→2017.
- **Parallelism (from 2026-11-16):**
  - `--procs 4` chunk processes (spawned), each with `--workers 8` concurrent `computePixels` threads, so up to 32 requests are in flight. The profile tail at the end of each chunk overlaps with the requests of the other processes. BLAS uses 2 threads per process.
  - Both passes of a chunk are queued at once.
  - EE profiles (EECU) are looked up on a separate 32-thread pool, off the request path, with 3 tries (2 s and 4 s waits). Profiles can lag; one still unavailable after that is estimated from the running EECU/km² rate (`eecu_source`), which is about 6 % of requests in parallel runs.
  - Block results are accumulated **in job order**, so the sums are bitwise independent of the worker count.
- **Retries:**
  - Rate-limit, quota, 5xx and network errors (429, "too many concurrent", RESOURCE_EXHAUSTED, …) are retried up to 10 times with exponential backoff (2 s → 120 s, ±25 % jitter). Other errors are retried up to 6 times.
  - Retries are counted in the ledger (`n_retries`, `n_retries_429`).
  - A block that still fails raises, so the whole chunk fails (`CHUNK_FAILED`) and is requeued at the end, up to 3 attempts. Nothing is dropped silently.
- **Profiling (2026-11-16):**
  - Raw `computePixels` latency is 0.7–1 s median at 12–24 concurrent requests. Throughput peaks at about 16 req/s per project around 24 in flight; at 32 and 48 it falls to 13 and 11 req/s.
  - Local zonal math (exactextract) takes about 8 ms per block, which is negligible.
  - The old serial profile lookup inside each request thread (2–12 s sleeps when a profile lagged) plus one chunk at a time held production at about 3 req/s.
- **int16 vs float32:** checked on 3 blocks.
  - int16 (×32767) has a max error of 1.5e-5 and halves the bytes (4.2 → 2.1 MB).
  - It costs **more** EECU (1.2–2.6 vs 1.1 EECU-s), so float32 is used.
- **EECU accounting:**
  - EECU comes from the EE profile of each `computePixels` and GHSL `getPixels` call.
  - A few profiles (≈5–10 %) are unavailable. For those, cost is estimated as fetched km² × the running EECU/km² rate, and the ledger's `eecu_source` column says so.

## Budget guard
- Before each chunk, the script computes this month's usage: ledger EECU for the month (UTC) plus other work (25 EECU-h for 2026-11, set in `OTHER_H`).
- Usage is summed over **all country ledgers** plus `OTHER_H`. Chunks in flight count at their estimate.
- If usage plus the chunk's estimate (state km² × observed rate) would exceed **800 EECU-h per calendar month**, the script logs `BUDGET_PAUSE`, lets in-flight chunks finish and exits with code 3. This is a safety stop: the project moved to the Contributor tier (1,000 EECU-h/month) on 2026-11-16, and `getProjectConfig` reports only `registrationState: REGISTERED_NOT_COMMERCIALLY`, not the tier.
- The wait-for-next-month behaviour was removed. A rerun skips chunks that have a `.done` marker.

## Verification (2023; `verify_2023_DF-SE-AL.json`, `verify_2023_AP.json`)
| check | result |
|---|---|
| (a) completeness | DF + SE + AL: 176/176 units; AP: 16/16. All 64 `w_` and 64 `u_` values are finite; 0 fall back to unweighted. |
| (b) norms (raw means) | DF/SE/AL: `w_norm` 0.867–0.947 (median 0.912), `u_norm` 0.777–0.968. AP: `w_norm` 0.850–0.943. All within the pilot range. |
| (c) cosine vs fresh EE `reduceRegions` at 100 m (same grid, same interpolated weights) | 5 units in AL/SE: `cos_w` = 1.0000000 at 8 dp for all 5. 5 units in AP (sparse sub-block path): also 1.0000000. `pop_sum` ratio is 0.99992–1.00006. Unweighted 300 m vs 100 m: cos ≥ 0.99997. |
| (d) cost | Weighted pass: 0.0119 EECU-s per fetched km², against 0.010 in the pilot. Unweighted 300 m pass: 0.00136 per km². Per state km²: dense states 0.013–0.015; AP 0.0042, so populated-only fetching is ~3.4× cheaper in the Amazon. |
| (e) projection | About 21 EECU-h per year (range 18–25). This assumes the 8 Amazon/Cerrado-frontier states (4.7 M km²) cost ~0.005 per km² and the rest (3.7 M km²) ~0.0137. The 7 years 2017–23 come to ≈145 EECU-h, ≈166 EECU-h with 2024. Throughput is ~15–18 EECU-h per wall hour. |

**Timeline under the guard:**
- The November cap (75 EECU-h left after other work) covers about 3.5 years, 2023 → part of 2020. It is reached in the evening of 2026-11-16 (UTC).
- The run then logs `BUDGET_PAUSE` and resumes on 2026-12-01 at 00:10 UTC. It should finish all 8 years within a few hours that day, using ~90 EECU-h of December.
- Other December work is not in `OTHER_H`. Add it if needed.

**Verification cost:** 18 EECU-s (DF/SE/AL), 1,175 EECU-s (AP, which has very large units) and 8 EECU-s (dtype test). All are in the ledger.

## Commands
```
cd $P && source env.sh
python scripts/features/extract_alphaearth.py status          # progress + budget
tail -f runs/alphaearth_brazil/extract.log                     # or: tmux attach -t pop_alphaearth
python scripts/features/extract_alphaearth.py run --procs 4 --workers 8   # (re)start all countries; resumes from .done markers
python scripts/features/extract_alphaearth.py detcheck --country brazil --year 2023 --region SE --workers 16
python scripts/features/extract_alphaearth.py verify --year 2023 --states DF SE AL
python scripts/features/extract_alphaearth.py assemble        # rebuild per-year + combined files (all countries)
python -m pytest -q tests/test_alphaearth_extract.py
```

## Determinism check (2026-11-16, `brazil/detcheck_2023_SE.json`)
- `2023_SE` was re-extracted from scratch (fresh GHSL) with the parallel code at 16 workers into `_detcheck/`.
- The raw sums are **bitwise identical** to the stored chunk. Max abs diff is 0 on all `w_`, `u_` and `pop_sum`.
- 3 units vs a fresh EE `reduceRegions` at 100 m: `cos_w` = 1.0 (8 dp), `pop_sum` ratio 1.00000–1.00001.
