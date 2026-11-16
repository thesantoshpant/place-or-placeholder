# AlphaEarth district-mean pilot (Brazil, 100 municipalities, 2022)

Code: `src/pop/features/alphaearth.py` and `scripts/features/pilot_alphaearth.py`. Outputs are in `data/interim/alphaearth/`.

## Method
- **Boundaries:** IBGE 2022 polygons (`opendengue_units_v1.parquet`), simplified at 5e-4° (~50 m).
- **Sample:** 10 largest municipalities in AC/AM/AP/PA/RO/RR (68k–160k km²), plus 10 per cell of area tercile × GHSL-2020 population tercile.
- **Image:** the AlphaEarth annual collection, filtered to the year and mosaicked.
- **Weights:** GHSL `GHS_POP/2020` converted to density × `pixelArea()`. GHS_POP has unmasked negative nodata, so values are masked to `>= 0`; Brazil's total is then 210.4 M.
- **One pass:** a single `Reducer.sum()` over `[A·w, A, w, valid]` gives both the population-weighted and the unweighted mean. Boundary pixels count by the fraction covered.
- **Output columns:** `unit_id, year, A00..A63` (unit length), `pop_sum, n_pixels, weighting, raw_norm, scale`. `year` is the image year; `lag_to_target_year()` adds year+1.

## Scale error (cosine vs 10 m, 10 units of 97–375 km²)
| scale | unweighted mean / min | pop-weighted mean / min |
|---|---|---|
| 30 m | 1.000000 / 1.000000 | 0.999995 / 0.999991 |
| 100 m | 0.999998 / 0.999992 | 0.999944 / 0.999785 |
| 300 m | 0.999978 / 0.999862 | 0.992961 / 0.986666 |

At 100 m, `pop_sum` is within 0.008% of the 10 m value, so 100 m is effectively exact. The loss at 300 m (pop-weighted) comes from nearest-neighbour resampling of the population grid.

## Unit length
- **Pixels:** 1,000 pixels at 10 m have norm 1.0000 ± 0.0020 (range 0.9945–1.0058).
- **District means before renormalising** (median [5–95%], min):
  - pop-weighted: 0.929 [0.877–0.962], min 0.806
  - unweighted: 0.913 [0.839–0.964], min 0.751
- The shrinkage varies by unit, so renormalising matters. `raw_norm` is kept for the sensitivity check.

## Cost (batch `Export.table.toAsset`)
| job | km² | EECU-s | wall |
|---|---|---|---|
| 100 units, 100 m, pop | 1,055,045 | 22,716 | 91 s |
| 90 non-Amazon, 100 m, pop | 99,902 | 2,498 | 117 s |
| 90 non-Amazon, 100 m, both | 99,902 | 2,693 | 154 s |
| 90 non-Amazon, 300 m, both | 99,902 | 516 | 111 s |

- **The first 100-unit export failed after computing**, because table exports reject null geometries. The code now keeps each unit's centroid. The cached re-run cost 0.02 EECU-s and matched the interactive results (cos > 0.9999999).
- **Unit cost:** 0.023–0.027 EECU-s per km²·year. Adding the unweighted mean to the same pass costs +8%.
- **Full run** (6,990 units, 10.62 M km² × 9 years, both weightings, 100 m):
  - **620–720 EECU-h**, which is **4–5 months of the 150 EECU-h/month quota**.
  - Brazil alone: 490–570 EECU-h.
  - At 300 m: about 130 EECU-h.
- **Spent on this pilot:** about 8 EECU-h batch, plus the interactive runs.

## Recommendation
1. **Scale:** 100 m, both weightings in one pass. 30 m and 10 m add nothing.
2. **Budget is the blocker.** Decide before running all 9 years:
   - (a) spread the run over about 5 months;
   - (b) get a higher EE tier; or
   - (c) use 300 m with population aggregated by `reduceResolution(sum)`. This is about 5× cheaper but must first be validated on these 10 units.
3. **Boundaries:** upload once as table assets under `projects/ee-spant-scaleshift/assets/pop/` (pilot: `br_pilot100_units`).
4. **Export:**
   - One `toAsset` task per state × year, about 250 tasks.
   - Export raw sums and finish the means locally with `sums_to_frame`.
   - Use `tileScale=4`. No geometry tiling was needed: Altamira (160k km²) ran in batch with `tileScale=4`.
   - Log `batchEecuUsageSeconds` for each task and stop at a monthly budget.
5. **GHSL epoch:** use the epoch nearest each image year (2015/2020/2025).
