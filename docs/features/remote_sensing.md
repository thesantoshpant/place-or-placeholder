# L3 remote-sensing covariates and yearly unit population

Code: `src/pop/features/remote_sensing.py`, `src/pop/features/population.py`, driver
`scripts/features/build_remote_sensing.py run <COUNTRY>` / `merge-pop`. Tests: `tests/test_remote_sensing.py`.

## Outputs (`data/interim/`)
| File | Key | Columns |
|---|---|---|
| `remote_sensing/rs_monthly_<c>_v1.parquet` | unit_id, year, month | `ndvi_{pw,aw}` (unitless), `lst_day_{pw,aw}`, `lst_night_{pw,aw}` (deg C) |
| `remote_sensing/rs_yearly_<c>_v1.parquet` | unit_id, year | `ntl_{pw,aw}` (VIIRS nW/cm2/sr), `built_share` (built-up m2 / unit area) |
| `population/unit_population_yearly_<c>_v1.parquet` | unit_id, year | `pop` (people) |
| `population/unit_population_epochs_<c>_v1.parquet` | unit_id | `pop_<epoch>` (GHSL epoch sums) |
| `population/unit_population_yearly_v1.parquet` | unit_id, year | all 4 countries concatenated (`merge-pop`; read-only on the per-country files) |
| `remote_sensing/rs_<c>_v1.qa.json`, `costs.jsonl`, `run_<c>.log` | | QA summary, EECU ledger, logs |
| `remote_sensing/rs_monthly_<c>_v2.parquet` (+ `rs_<c>_v2.qa.json`, `run_lst_<c>_v2.log`) | unit_id, year, month | v1 with the 4 LST columns recomputed with the QC mask (see "v2: QC-masked LST") |
| `remote_sensing/rs_lst_compare_v1_v2.json`, `pilot_lst_*_v2.json`, `ghsl_pop_cells_<c>_v2.npz`, `lst_v2_cache/lst_raw_<c>_<year>_v2.parquet` | | v1-vs-v2 comparison, QC-rule pilots, cached GHSL population per 0.01 deg cell, per-year raw (pre-fill) v2 LST (resume cache) |

## Sources and conventions
- **NDVI**: MODIS/061/MOD13Q1 (16-day, 250 m), SummaryQA <= 1 (good/marginal), scale 1e-4.
- **LST day/night**: MODIS/061/MOD11A2 (8-day, 1 km), x0.02 - 273.15 -> deg C. **No QC mask** (see caveats).
- **Night lights**: VIIRS VNL annual V2.1 (2013-21) / V2.2 (2022-24), `average_masked`, masked background = 0. Not available before 2013 (NaN).
- **Built-up / population**: GHSL P2023A GHS_BUILT_S and GHS_POP (100 m), 5-year epochs; negative nodata masked to 0.
- **Grid**: everything is fetched with EE `computePixels` on a 0.01 deg EPSG:4326 grid aligned to the ERA5-Land grid (edges at -180.05 + k*0.01) and reduced locally with exactextract coverage fractions. MODIS/VIIRS are read from EE pyramids at 0.01 deg; GHSL is aggregated exactly with `reduceResolution` (mean density x cell area).
- **Weights**: `_aw` = coverage x cell area; `_pw` = coverage x GHSL population of the nearest epoch to the year (plus 1e-9 x area so empty units fall back to area weighting). Means are over valid (non-NaN) cells only, so cloud gaps renormalise the weights; a unit with no valid cell is NaN.
- **Month assignment (leakage-safe)**: a composite belongs to the month of its **last day** (MOD13Q1 start + 15 d; MOD11A2 start + 7 d, the year's last 8-day composite capped at 31 Dec). Month m only contains information up to the end of month m.
- **Gap-fill**: a NaN unit-month is filled from the **same month of the previous year** (only if that year exists and is non-NaN); never from the future. Remaining NaN stays NaN.
- **Population**: yearly values interpolated between GHSL epochs **log-linearly** (constant growth; linear if an endpoint is 0), clamped outside the epoch range (no extrapolation). `built_share` is interpolated linearly.
- **Years**: BR 2013-24, CO 2007-22 (pop 2006-22), PE 2000-23, TW 2000-24 (pop 1997-24): the panel windows, clipped at MODIS start (2000), so 2012/2013 lags are always covered.

## Fix 2026-11-16: Taiwan crash (MODIS start)
`run TAIWAN` crashed with `IndexError: index 32 ... size 32` in `Builder.modis`. Root cause: MODIS Terra starts in Feb 2000; for 2000 no MOD13Q1 composite ends in Jan/Feb and no MOD11A2 composite ends in Jan (checked with `composites_by_month` for 2000-24: only 2000 has empty months). `ImageCollection.mean()` of an empty collection has zero bands, so `monthly_image(2000)` returned 32 bands instead of 36 and positional indexing `3*(m-1)+j` overflowed (a mid-year gap would have silently shifted months). Fix: empty months now emit a fully masked band with the right name (-> NaN), and `R.monthly_frame` refuses stacks that are not 12 x 3 bands. Brazil is unaffected: the serialized EE graph of `monthly_image(y)` is identical to the old code for every year 2013-24, and a recompute of Sergipe 2023 (73 units x 12 months, 6 variables) matched the existing Brazil file exactly (max abs diff 0.0). Brazil files were not rewritten.

## QA (all 4 countries)
| | BR | CO | PE | TW |
|---|---|---|---|---|
| units built / universe | 5,517 / 5,517 | 1,070 / 1,071 (Belen de Bajira, no polygon) | 115 / 115 | 285 / 287 (Hsinchu City and Tainan City "OTHER", no polygon) |
| monthly years | 2013-24 | 2007-22 | 2000-23 | 2000-24 |
| duplicates (mon/yr/pop) | 0 | 0 | 0 | 0 |
| NaN after fill: ndvi / lst_day / lst_night | 0.001% / 0 / 0.08% | 0.009% / 0.006% / 0.24% | 0.70% / 0.69% / 0.60% | 1.24% / 0.67% / 0.68% |
| of which year 2000 Jan-Feb (no MODIS) | - | - | all but 1 row | ~all of lst; ndvi see below |
| NDVI pw range | 0.06-0.90 | 0.07-0.93 | 0.06-0.83 | -0.06-0.87 |
| LST day pw range (deg C) | 9.3-49.3 | -0.5-47.2 | 6.9-44.5 | -3.1-43.2 |
| LST night pw range (deg C) | 0.0-29.0 | **-42.4**-28.8 | -16.6-26.2 | -2.1-28.5 |
| NTL NaN years | none | 2007-12 (pre-VIIRS) | 2000-12 | 2000-12 |
| pop min / units <= 0 | 805 / 0 | 290 / 0 | 3,633 / 0 | 913 / 0 |
| pop total 2013 / 2020 (M) | 199.4 / 210.9 | 45.3 / 50.0 | 24.7 / 27.5 | 21.9 / 22.4 |
| loglin vs linear pop, max rel diff | 3.4% | 16.0% | 0.9% | 0.3% |
| EECU-h (run) | 5.51 | 1.08 | 1.63 | 0.26 (+0.10 crashed run) |

All NDVI values lie in [-0.2, 1]. Remaining NaN outside 2000 Jan-Feb: TW NDVI ~0.4-0.8%/yr, concentrated in tiny dense urban districts where SummaryQA masks most pixels (Taichung Central Dist., 0.94 km2, NaN in 71% of months; Taichung South 24%; Kaohsiung Xinxing 15%); PE one unit-month (Callao, 2008-08); BR/CO scattered night-LST months. Downstream should impute (e.g. unit-calendar-month mean from training years) or use `_aw`/neighbour values.

EECU: CO/PE/TW runs plus the Brazil slice check used ~3.1 EECU-h; all logged RS work (pilots, BR, CO, PE, TW) totals 8.9 EECU-h. Budget guard `BUDGET_H` = 26 h of logged EECU.

## Caveats
- **NDVI from ~1 km pyramids**, not native 250 m: r = 0.998 vs QA-masked native 250 m in the SP 2023 pilot, at about 1/4 of the cost.
- **LST without QC mask (v1 only; fixed in v2, see below)**: in the SP pilot the QC mask changed unit means by only -0.02 deg C (r >= 0.998). In cloudier terrain it lets cloud-contaminated cold pixels through: CO night LST is > 10 deg C below the unit's calendar-month median in 0.56% of unit-months (1,153; Andes/Pacific, minimum -42 deg C, e.g. Contratacion 2013-05), PE 0.18%, TW/BR <= 0.06% (e.g. Keelung Feb 2008 day LST ~ -3 deg C). Consider winsorising LST at the unit-calendar-month level or re-running CO with `mask_qa="all"` if LST matters for the models.
- **GHSL log-linear between epochs is +4-10% vs the 2022 BR census** (GHSL 2025 epoch is a projection). Use population as a relative weight/scale feature, not as a census count.
- VIIRS night lights start in 2013; CO/PE/TW years before that are NaN (no DMSP splice).
- Population weights use the nearest GHSL epoch, not the interpolated year.

## v2: QC-masked LST
`python scripts/features/build_remote_sensing.py run-lst-v2 <COUNTRY>` (then `compare-lst`). `rs_monthly_<c>_v2.parquet`
has exactly the v1 keys, row order, columns and dtypes; only `lst_{day,night}_{pw,aw}` are recomputed. All other
columns are copied from v1 and checked to be bit-identical (`non_lst_columns_bit_identical_to_v1` in the QA json,
`tests/test_remote_sensing.py::test_v2_matches_v1_except_lst`). v1 files are untouched. Models choose the version
with `options={"remote_sensing": {"version": "v2"}}` in `pop.features.levels.Context` (default `v1`).

**QC rule (v2).** MOD11A2 `QC_Day` / `QC_Night` bit fields from the MOD11 Collection 6 user guide (Wan 2013,
*MODIS Land Surface Temperature Products Users' Guide*, Table "QC bit flags"; the same bits are listed in the
EE catalog for `MODIS/061/MOD11A2`): bits 0-1 mandatory QA (00 = LST produced, good quality; 01 = produced,
other quality, check the other bits; 10/11 = not produced), bits 6-7 average LST error (00 <= 1 K, 01 <= 2 K,
10 <= 3 K, 11 > 3 K). **A pixel is kept if bits 0-1 = 00, or bits 0-1 = 01 and bits 6-7 = 00 (LST error <= 1 K).**
Day and night are masked separately, each with its own QC band, on each 8-day composite before the monthly mean
(`R.lst_qc_ok`, `R.LST_MAX_ERR_FLAG = 0`). Masking happens on the native 1 km pixels: at the 0.01 deg request
scale EE reads pyramid level 0 (926 m). Everything else (grid, weights, month assignment, valid-cell
renormalisation, previous-year gap-fill) is as in v1. Population weights use the same nearest-GHSL-epoch
rule, refetched (pop only) and cached in `ghsl_pop_cells_<c>_v2.npz`.

**Why <= 1 K and not <= 2 K.** The looser, commonly suggested rule (keep 01 when LST error <= 2 K) was piloted
first and does nothing to the artifacts: the cold pixels are themselves flagged `01` with error <= 2 K and
data-quality and emissivity bits at 00. Example: Contratacion (CO) 2013-05 night = one composite (2013-05-09), 2 pixels,
both QC 01/err<=2K at -42.4 deg C. Chipata 2022-06: 1 pixel, QC 01/err<=2K, -40.9 deg C. Balboa 2018-11: 8
pixels, all 01/err<=2K, median -5.9 deg C. Pilots (`pilot-lst <COUNTRY> --adm1 <STATE> --year <Y>`, one year,
unit-months, cold = > 10 deg C below the v1 unit x calendar-month median):

| slice | variable | v1 min | <= 2 K: min / cold / r vs v1 | <= 1 K (v2): min / cold / r vs v1 / mean shift / NaN before fill |
|---|---|---|---|---|
| CO Santander 2013 | night pw | -42.4 | -42.4 / 0.86% / 0.996 | -1.0 / 0.57% / 0.880 / +0.64 / 10.0% (v1 0.8%) |
| CO Santander 2013 | day pw | 15.7 | 15.7 / 0 / 1.000 | 17.5 / 0 / 0.944 / +0.78 / 0% |
| CO Cauca 2018 | night pw | -30.2 | -30.2 / 2.85% / 1.000 | -10.4 / 1.22% / 0.879 / +0.32 / 6.7% (v1 0.8%) |
| CO Cauca 2018 | day pw | 14.0 | 14.0 / 0 / 1.000 | 6.1 / 0.41% / 0.893 / +1.05 / 0.2% |
| BR Sergipe 2023 | night pw | 15.9 | 15.9 / 0 / 1.000 | 15.6 / 0 / 0.938 / +0.40 / 0% |
| BR Sergipe 2023 | day pw | 22.5 | 22.5 / 0 / 1.000 | 18.3 / 0 / 0.931 / +1.31 / 2.4% |
| BR Amazonas 2019 | night pw | 12.5 | 14.3 / 0 / 0.992 | 19.9 / 0 / 0.814 / +0.35 / 3.1% (v1 1.4%) |
| BR Amazonas 2019 | day pw | 23.1 | 23.1 / 0 / 0.997 | 24.3 / 0 / 0.824 / +0.27 / 0% |

The <= 2 K rule reproduces v1 (r >= 0.992, mean shift <= 0.03 deg C). The <= 1 K rule removes the extreme cold values and
halves the cold share, but it also drops many "other quality" pixels everywhere, so LST rises (+0.3 to +1.3 deg C,
the usual clear-sky / cloud-edge effect) and more night unit-months are NaN before gap-fill. The unmasked path of
the v2 code (`lst_image(qc=False)`) reproduces v1 to <= 2e-6 deg C on the pilot slices.

**Full-run comparison, v1 vs v2** (`compare-lst` -> `rs_lst_compare_v1_v2.json`). Cold = unit-month more than 10 deg C below
that version's own unit x calendar-month median (all years); mean/abs diff/r over rows non-NaN in both;
"NaN before fill" = raw share before the previous-year gap-fill.

| | variable | cold >10 C v1 -> v2 | min v1 -> v2 | max v1 -> v2 | mean v1 -> v2 | mean diff | mean abs diff | p99 abs diff | r | NaN before fill v1 -> v2 | NaN after fill v1 -> v2 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| BR | lst_day_pw | 0.010% -> 0.021% | 9.3 -> 7.5 | 49.3 -> 53.0 | 30.15 -> 30.59 | +0.44 | 0.74 | 4.3 | 0.979 | 0.01% -> 1.23% | 0.000% -> 0.334% |
| BR | lst_day_aw | 0.006% -> 0.013% | 8.7 -> 7.3 | 48.5 -> 52.8 | 29.29 -> 29.80 | +0.51 | 0.62 | 3.7 | 0.987 | 0.01% -> 1.23% | 0.000% -> 0.334% |
| BR | lst_night_pw | 0.020% -> 0.008% | 0.0 -> -0.1 | 29.0 -> 29.6 | 19.34 -> 19.53 | +0.19 | 0.39 | 3.0 | 0.983 | 0.47% -> 1.18% | 0.081% -> 0.306% |
| BR | lst_night_aw | 0.010% -> 0.004% | 0.1 -> 0.9 | 28.2 -> 28.6 | 18.98 -> 19.18 | +0.20 | 0.30 | 2.4 | 0.990 | 0.47% -> 1.18% | 0.081% -> 0.306% |
| CO | lst_day_pw | 0.055% -> 0.191% | -0.5 -> 2.4 | 47.2 -> 47.9 | 27.67 -> 28.48 | +0.81 | 1.25 | 6.5 | 0.929 | 0.09% -> 3.18% | 0.006% -> 0.864% |
| CO | lst_day_aw | 0.012% -> 0.090% | -0.9 -> 2.4 | 45.4 -> 46.3 | 25.92 -> 27.27 | +1.35 | 1.51 | 7.2 | 0.941 | 0.09% -> 3.18% | 0.006% -> 0.864% |
| CO | lst_night_pw | 0.563% -> 0.688% | -42.4 -> -22.1 | 28.8 -> 29.2 | 17.06 -> 17.48 | +0.42 | 1.04 | 8.7 | 0.943 | 1.16% -> 6.02% | 0.241% -> 1.985% |
| CO | lst_night_aw | 0.309% -> 0.273% | -42.4 -> -12.4 | 28.3 -> 28.6 | 16.05 -> 16.46 | +0.41 | 0.86 | 6.3 | 0.970 | 1.16% -> 6.02% | 0.241% -> 1.985% |
| PE | lst_day_pw | 0.064% -> 0.027% | 6.9 -> -1.8 | 44.5 -> 50.6 | 28.64 -> 29.63 | +0.99 | 1.35 | 7.5 | 0.938 | 0.69% -> 0.84% | 0.691% -> 0.722% |
| PE | lst_day_aw | 0.040% -> 0.021% | 6.8 -> -0.9 | 48.1 -> 50.4 | 27.16 -> 28.67 | +1.51 | 1.57 | 7.6 | 0.970 | 0.69% -> 0.84% | 0.691% -> 0.722% |
| PE | lst_night_pw | 0.182% -> 0.314% | -16.5 -> -16.0 | 26.2 -> 26.5 | 13.89 -> 13.99 | +0.10 | 0.98 | 7.3 | 0.961 | 0.61% -> 1.66% | 0.595% -> 1.048% |
| PE | lst_night_aw | 0.052% -> 0.095% | -16.5 -> -12.1 | 25.7 -> 26.4 | 12.71 -> 12.74 | +0.03 | 0.74 | 4.7 | 0.983 | 0.61% -> 1.66% | 0.595% -> 1.048% |
| TW | lst_day_pw | 0.049% -> 0.031% | -3.1 -> 7.5 | 43.2 -> 44.7 | 30.07 -> 30.39 | +0.32 | 1.02 | 5.3 | 0.951 | 0.85% -> 6.84% | 0.665% -> 2.771% |
| TW | lst_day_aw | 0.040% -> 0.017% | -2.8 -> 7.4 | 43.2 -> 44.8 | 29.02 -> 29.44 | +0.42 | 0.92 | 4.9 | 0.963 | 0.85% -> 6.84% | 0.665% -> 2.771% |
| TW | lst_night_pw | 0.059% -> 0.042% | -2.1 -> 2.2 | 28.5 -> 29.5 | 20.18 -> 20.65 | +0.47 | 0.90 | 5.3 | 0.951 | 1.08% -> 6.35% | 0.680% -> 2.716% |
| TW | lst_night_aw | 0.048% -> 0.024% | -2.1 -> 2.7 | 28.4 -> 29.6 | 19.80 -> 20.29 | +0.48 | 0.83 | 4.9 | 0.960 | 1.08% -> 6.35% | 0.680% -> 2.716% |

Brazil (v2 vs v1): the shift is a near-constant offset. The mean day-pw difference is +0.40 to +0.51 deg C in every year 2013-24, and
night is +0.15 to +0.22 deg C. But the unit x calendar-month anomalies (the part that carries the signal) correlate only
0.875 (day pw) and 0.851 (night pw) between versions, so **Brazil v2 is not ~ v1**. EECU for the v2 runs and pilots: 8.65 EECU-h logged
(including about 1.2 h lost to a crash in the first launch and then recomputed; BR 4.66 h of it).

**Where the v2 cold months come from.** v2 removes most of the v1 cold months, but it creates about as many new ones.
CO night pw: 1,153 cold in v1, 1,386 in v2, only 229 in both. PE night pw: 60 / 103 / 13. TW night pw: 50 / 35 / 3.
The new ones cluster in units with a large elevation range (Meta and Putumayo piedmont, Andean slopes: Villagarzon,
Guamal, Acacias, El Castillo). There the strict mask leaves only a few, often high and cold, valid pixels in a
cloudy month. The unit mean over valid cells is then not representative (spatial selection), and the drop
relative to the v1 value has a median of 8.7 deg C. The same mechanism drives the mean shift: dropping "other quality" pixels
removes cloud-cooled values, but it also changes which pixels are averaged.

**Verdict.** No MOD11A2 QC-bit rule gives a clean fix. The <= 2 K rule reproduces v1. The <= 1 K rule (v2) removes
the extreme minima (CO -42 -> -22 deg C, TW -3 -> +7.5 deg C) but does not lower the cold-outlier share in CO/PE (and creates new
day outliers: PE day min 6.9 -> -1.8 deg C). It also moves every country by +0.2 to +1.5 deg C (r 0.93-0.99), changes Brazil's
anomalies (r 0.85-0.88), and raises raw NaN up to ~100x (BR day: 0.01% -> 1.2%; CO/TW to ~6%). v1 stays the default (`levels` option
`remote_sensing.version = "v1"`); v2 is kept as a sensitivity variant. A better fix for cloudy, mountainous units
is a post-hoc robust filter on the unit series, e.g. set unit-months more than 10 deg C below the unit x
calendar-month median of the *training* years to NaN and impute. A pixel-level alternative is to average per-pixel anomalies from a
pixel climatology, so that partially masked months do not change the pixel mix. The first needs no new EE extraction
(it must use training years only to stay leakage-safe); the second needs a new per-pixel extraction.
