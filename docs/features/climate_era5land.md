# Weekly district climate from ERA5-Land

**Output:** `data/interim/climate/climate_weekly_<country>_v1.parquet` with columns `unit_id`, `week_start`, `tmean`, `tmin`, `tmax`, `precip`, `rh`, plus an `*_area` version of each variable.
**Code:** `src/pop/features/{climate,ee_utils}.py`, `scripts/features/{upload_units_to_ee,build_climate_weekly}.py`, `tests/test_climate.py`.

## Definitions
- **Weeks** are the panel's Sunday-start weeks, `[week_start, +7 d)`, built from `ECMWF/ERA5_LAND/DAILY_AGGR` UTC days. Every Brazil week has exactly 7 days (asserted).
- **Variables:**
  - `tmean`: weekly mean of daily mean T2m.
  - `tmin` / `tmax`: weekly means of the daily minimum and maximum (°C).
  - `precip`: weekly sum (mm).
  - `rh`: weekly mean of daily RH from daily mean T and dewpoint, using Magnus/Alduchov–Eskridge (a=17.625, b=243.04 °C) and capped at 100 %.
- **Weights:**
  - Population: GHSL `GHS_POP`, epoch nearest the week's year (2015 / 2020 / 2025 for Brazil). Negative nodata is masked in EE (`updateMask(pop.gte(0))`) and clamped to ≥0 again locally.
  - Area: `*_area`, coverage × cos(lat).
  - Both use exact polygon × 0.01° coverage fractions (exactextract) on a grid aligned to ERA5-Land's native 0.1° grid.
  - Ocean cells (masked in ERA5-Land) get zero weight.
  - 3 units have no land cell: Fernando de Noronha, Itaparica and Madre de Deus. They use the nearest land cell to their representative point.

## Polygons
- **Simplification:** `shapely.coverage_simplify` at 0.001° (~110 m), which keeps shared edges and leaves no gaps or overlaps. Brazil vertices fall from 16.7 M to 2.0 M.
- **Area change:** total −5×10⁻⁷. Per unit, median |Δ| is 0.008 %, p99 0.10 % and max 0.40 %.
- **Other countries (dry run):** Colombia and Taiwan contain unclean geometries, so they fall back to per-polygon topology-preserving simplify. Their p99 area change is 0.6 % and 2.9 %. Re-check once their matches are final.
- **Asset:** `projects/ee-spant-scaleshift/assets/pop/units_v1_bra` (5,517 features). Uploaded in 27 chunks plus a merge export for 0.35 EECU-s in total.

## Method choice (pilot: Brazil 2023, 53 weeks × 5517 units)
| | (a) EE `reduceRegions` → table asset | (b) download grids + local zonal stats |
|---|---|---|
| EECU | **12,572 s (3.5 h)** per year | ~1,690 s (weeks 186 s + GHSL 2025 ≈1,500 s) |
| Wall time | 360 s task (plus queueing) | 223 s |
| Full Brazil (projected) | ~38 EECU-h | measured **1.76 EECU-h** |

- **Agreement (a vs b, 292k unit-weeks):** r > 0.999999995 for all 10 columns. Median absolute difference is ≤2×10⁻⁴; p99 is ≤0.001 °C and ≤0.01 mm.
- **Missing values:** (a) is NaN for the 3 units without a land cell; (b) fills them.
- **Choice: (b).** It is about 20× cheaper with the same results.
  - Weekly composites (5 variables) are built in EE and fetched on the native 0.1° grid with `computePixels` (8 weeks per request).
  - GHSL is aggregated in EE to 0.01° (`reduceResolution`, 25×25-cell tiles) only where polygons need it. This is ~1,450 EECU-s per epoch and dominates the cost.
  - Locally, sparse unit × cell weight matrices are built once, so each week is a mat-vec.
- **Interactive EECU** comes from EE profiles (`ee_utils.profiled`). 49 profiles were unavailable, so the 1.76 h is a slight lower bound (likely ≤2 h).

## EECU used / projected
- **Used:** Brazil full run 6,340 s. Pilot (a) 12,572 s; pilot (b) ~1,690 s. Upload ~0. **Total ≈ 5.8 EECU-h.**
- **Projected with (b)**, scaled by bbox × weeks and populated area × epochs:
  - Colombia ≈ 0.4 h
  - Peru ≈ 0.5 h
  - Taiwan ≈ 0.05 h
  - All four countries ≈ 2.8 EECU-h, including Brazil.
- **Possible saving:** caching the GHSL grids per epoch would cut repeat runs to ~0.6 h for Brazil.

## QA (Brazil, `climate_weekly_brazil_v1.qa.json`)
- **Completeness:** 3,166,758 rows = 5,517 units × 574 weeks (2013-12-29 → 2024-12-22). 0 missing pairs, 0 NaN, 0 duplicates. Every panel unit has a polygon.
- **Consistency:** 0 violations of tmin ≤ tmean ≤ tmax.
- **Ranges (min / p0.1 / p99.9 / max):**
  - tmean: 4.3 / 9.1 / 32.1 / 36.3 °C
  - tmin: 0.4 / 4.7 / 26.9 / 31.9 °C
  - tmax: 7.6 / 13.5 / 38.1 / 41.4 °C
  - precip: 0 / 0.002 / 221 / 486 mm/week
  - rh: 17.9 / 25.9 / 93.5 / 97.3 %
- **Spot check (2023 means):** São Paulo 20.0 °C, Manaus 27.6 °C, Brasília 22.3 °C.
- **Tests:** `tests/test_climate.py` covers RH known values and cap, epoch choice, grid alignment, and alignment of panel weeks with climate weeks. 4 pass.

## Commands
```
cd $P && source env.sh
python scripts/features/upload_units_to_ee.py BRAZIL            # re-runnable per country; --dry-run for area report
python scripts/features/build_climate_weekly.py pilot BRAZIL --year 2023
python scripts/features/build_climate_weekly.py run BRAZIL      # COLOMBIA / PERU / TAIWAN once boundaries final
python -m pytest -q tests/test_climate.py
```
Costs are appended to `data/interim/climate/costs.jsonl`. Method (a) also left `pop/climate_pilot_bra_2023_ee` (a table asset; it can be deleted).

## Results: Colombia, Peru, Taiwan (method (b), full panel week range)
- **Week ranges:** each country covers its full panel range; ERA5-Land runs back to 1950, so no truncation at 2010.
  - Colombia: 2006-12-31 to 2022-12-25 (835 weeks).
  - Peru: 2000-01-02 to 2023-12-24 (1,252 weeks).
  - Taiwan: 1997-12-28 to 2024-12-22 (1,409 weeks).
  - All weeks have 7 ERA5 days.
- **Units without geometry are skipped** (`upload_units_to_ee.py` now drops null or empty geometries and logs them):
  - Colombia: `COLOMBIA|CHOCO|BELEN DE BAJIRA`
  - Taiwan: `TAIWAN|HSINCHU CITY|OTHER` and `TAIWAN|TAINAN CITY|OTHER`
  - After the drop, `coverage_simplify` succeeds for both countries, so the per-polygon fallback is not needed.
- **Simplification (0.001°), area change (total; median / p99 / max per unit):**
  - Colombia: 4.90 M → 0.40 M vertices; +5×10⁻⁷; 0.015 % / 0.16 % / 0.31 %.
  - Peru: 0.45 M → 0.12 M vertices; +2×10⁻⁶; 0.002 % / 0.02 % / 0.06 %.
  - Taiwan: 0.27 M → 0.03 M vertices; −2×10⁻⁵; 0.06 % / 0.90 % / 2.9 %. The largest changes are small islets.
- **Assets:** `projects/ee-spant-scaleshift/assets/pop/units_v1_{col,per,twn}`, with 1,070 / 115 / 285 features. Upload cost is ≤0.05 EECU-s each.
- **Completeness (`climate_weekly_<country>_v1.qa.json`):** no NaN, no duplicates, and 0 violations of tmin ≤ tmean ≤ tmax in all three countries.
  - Colombia: 893,450 rows = 1,070 × 835. The 835 missing pairs are Belén de Bajirá only.
  - Peru: 143,980 rows = 115 × 1,252. Complete.
  - Taiwan: 401,565 rows = 285 × 1,409. The 2,818 missing pairs are the two "OTHER" units only.
- **Nearest land cell:** units with no ERA5 land cell use the nearest one (2 in Colombia, 18 in Taiwan, mostly islets).
- **Ranges (min / p0.1 / p99.9 / max):**
  - Colombia:
    - tmean: 7.0 / 9.3 / 31.0 / 33.6 °C
    - tmin: 1.3 / 5.5 / 26.9 / 28.4 °C
    - tmax: 11.3 / 13.2 / 37.0 / 40.5 °C
    - precip: 0 / 0.007 / 558 / 1,010 mm/week
    - rh: 27 / 41 / 96 / 98 %
  - Peru:
    - tmean: 1.3 / 3.4 / 28.1 / 30.8 °C
    - tmin: −3.9 / −1.5 / 24.6 / 26.2 °C
    - tmax: 5.7 / 8.6 / 34.4 / 37.0 °C
    - precip: 0 / 0.006 / 197 / 457 mm/week
    - rh: 16 / 27 / 94 / 97 %
  - Taiwan:
    - tmean: 5.0 / 10.2 / 29.6 / 31.1 °C
    - tmin: 1.4 / 7.2 / 27.2 / 28.1 °C
    - tmax: 7.9 / 12.2 / 33.1 / 35.6 °C
    - precip: 0 / 0.015 / 575 / 1,160 mm/week (typhoon weeks)
    - rh: 47 / 61 / 94 / 98 %
- **Spot check (mean tmean, mean precip per week):**
  - Colombia: Barranquilla 27.2 °C; Bogotá 13.2 °C; Medellín 16.0 °C.
  - Peru, coast against the Andes: Lima/Barranca 19.6 °C and 3.4 mm; Cusco 8.1 °C; Puno/Carabaya 5.8 °C. Peru, Amazon: Loreto/Alto Amazonas 25.4 °C.
  - Taiwan: Banqiao 21.6 °C; Kaohsiung/Daliao 23.7 °C; Hualien 20.8 °C and 74 mm.
- **EECU (run, from `costs.jsonl`):**
  - Colombia: 2,350 s (0.65 h)
  - Peru: 3,431 s (0.95 h)
  - Taiwan: 885 s (0.25 h)
  - These are above the projections because the panels start earlier (more weeks and GHSL epochs). Some profiles were unavailable, so these are slight lower bounds.
- **Tests:** `pytest tests/test_climate.py`: 4 passed.
