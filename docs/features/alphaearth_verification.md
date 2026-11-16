# AlphaEarth extraction: independent verification

**Script:** `scripts/features/verify_alphaearth.py --country <name> [--years 2017-2023] [--n-sample 30] [--seed 0]`.
It reads only the final per-year parquet files and the unit polygons, and recomputes sampled unit-years with its own
EE `reduceRegion` code. It does not use the extractor code or its `verify_*`/`detcheck_*` files.
Output: `data/interim/alphaearth/<country>/verification_v1.json` (+ `verification_v1_sample.csv`); log `runs/verify_alphaearth/<country>.log`.

Definitions reproduced:
- image = mosaic of `GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL` for the year, bands A00..A63;
- weights = GHSL `JRC/GHSL/P2023A/GHS_POP`, values < 0 set to 0, linear interpolation between 2015/2020/2025;
- grid = GHS_POP native Mollweide grid (transform read from EE); weighted pass 100 m, unweighted 300 m;
- polygons projected locally to Mollweide (ESRI:54009) and passed as planar EE geometries;
- `w_` = sum(pop·A)/sum(pop) and `u_` = coverage-weighted mean, both over valid embedding pixels.

Thresholds: cos(w) > 0.9999; cos(u) > 0.9995. The recompute uses the same 300 m grid and pyramid as the stored values,
so only the polygon-coverage implementation differs (exactextract vs EE). The looser bound allows for that in small units.
pop_sum must agree within 0.1 %.

## Brazil (2026-11-16, years 2017-2023) — PASS

| check | result |
|---|---|
| completeness | 5,517/5,517 units every year (= universe, all have geometry); 0 missing, 0 extra, 0 duplicate ids |
| finite values | all 128 columns finite, except **2605459 Fernando de Noronha in 2017–2021**: NaN, pop_sum 0, no coverage, `w_fallback`=True |
| coverage gap check | EE has **0 valid AlphaEarth pixels** over Noronha in 2017–2021 and 210 (300 m) in 2022–23. This is an upstream gap, not an extraction bug |
| norms | stored = recomputed (max diff 0). `w_norm` range 0.74–0.98, median 0.92; `u_norm` 0.71–0.99; none > 1 |
| copy bug | 0 identical or near-identical (cos > 1−1e-12) vectors between distinct units in any year |
| year-to-year (w) | median cos 0.98 for every consecutive pair; no unit identical across years. The low tail is 2017→18 (min 0.74; 114 units < 0.9, mostly PE/AL/SE coast) and 2021→22 (39 < 0.9, RS/SP/PR) |
| spatial | 2023 adjacent pairs: median cos 0.973 (n = 16,323) vs random pairs 0.710 |
| EE recompute | 33 unit-years: 6 each small/medium/large/coastal/Amazon (≤25,000 km²) + the 3 lowest year-to-year-cos units (2017, PE/AL). All 7 years are covered. **min cos_w 0.9999999987, min cos_u 0.9999999969**, max abs diff 1.5e-5 (w), 2.9e-5 (u) |
| pop_sum | stored/EE ratio 0.99995–1.00017 |
| EECU | 0.40 EECU-h (1 profile unresolved) |

Notes for downstream:
- Fernando de Noronha has no embedding for target years built from AE 2017–2021. Impute it (e.g. from AE 2022) or drop it, and say so in the methods.
- The low-cos 2017 units recompute exactly, so the 2017 shift on the NE coast is in AlphaEarth itself, not an extraction error.
