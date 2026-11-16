# Train/test splits S0–S5 (splits_v1)

Code: `src/pop/splits/{splits,spatial}.py`. The grouped S2/S3 fold columns (`s2_fold`, `s3_fold`) are derived in `load_unit_folds()` from the stored table (whose adm1 index is exposed as `s2l_fold`, blocks as `s3_block`), so `splits_v1` was not rebuilt. Tests: `tests/test_splits.py` (coverage, disjointness, one fold per state, buffer distance and completeness). Build: `scripts/splits/build_splits.py` (re-runnable, seed 20240101). Outputs: `data/processed/splits_v1/`.

**Origins.** Origin Y trains on target years 2018..Y−1 (lags may use earlier years) and tests on all target weeks of Y, horizons 1–4. Tuning origin 2019 trains on 2018 only. Test origins run from 2020 to the last year of each country: BR 2024, CO 2022, PE 2023, TW 2024. `row_masks()` returns `train`, `test`, `score = test & ~flag_gap` and `train_target_ok`. Gap weeks stay available as inputs.

**Splits.**
- **S0** (BR/CO/TW, leaky): a hash of (unit, week, seed) sends 20% of 2018..Y rows to test. Train uses the other 80%, including rows from Y. Test is the 20% that falls in Y.
- **S1** (all countries): purely temporal; every unit is in both train and test.
- **S2** (BR/CO): **grouped leave-states-out, 5 folds** (changed 2026-11-16). Each adm1 is in exactly one fold; held-out units are always in states never seen in training. Folds are balanced by unit count with a seeded greedy rule (`splits.group_adm1_folds`: adm1s in a seeded random order, stable-sorted by size descending, each to the currently smallest fold). The old leave-one-adm1-out split is kept as **S2L** (not run).
- **S3** (BR/CO): k-means blocks on centroids (k = 10 for BR, 6 for CO). **BR's 10 blocks are grouped into 5 folds of 2** (largest block paired with smallest, `splits.group_blocks`); CO keeps 6 folds = 6 blocks. Units within D of *any* held-out unit of the fold are dropped from training (union of the per-block buffers). The old one-block-per-fold split is kept as **S3B** (not run).
- **S4** (BR/CO): 5-fold unit hold-out stratified by adm1. Fold sizes differ by at most one unit, both overall and within each adm1.
- **S5**: leave one country out, in the order TW, BR, CO, PE.

## Buffer distance D
Data: years 2014–2019 only, so test years are excluded. Units need ≥10 non-zero weeks (BR 4,249, CO 806). Method: mean pairwise correlation of de-seasonalised log1p(cases), by centroid-distance bin. Residual versions:
- *additive* (protocol): remove the unit mean and week-of-year effects.
- *week_fe*: also removes each calendar week's national mean, including epidemic years.
- *unit_woy*: sensitivity check.

**D = max(first 0.1 crossing of additive, first 0.1 crossing of week_fe).** Brazil's additive curve levels off at about 0.11 out to 2,000 km. This is a national co-movement that no buffer can remove, so only the week_fe crossing is defined there.

| | additive | week_fe | 3a (week_fe) | **D** |
|---|---|---|---|---|
| Brazil | none | 225 km | 789 km | **225 km** |
| Colombia | 130 km | 80 km | 501 km | **130 km** |

The exponential ranges come from long, weak tails and are not used. Plots: `outputs/splits/correlogram_*.png/csv`.

## Fold sizes (origin 2020)
| Split | Country | folds | test units | train units | buffer-excluded |
|---|---|---|---|---|---|
| S2 | BR | 5 (4–6 states each) | 1090–1124 | 4393–4427 | – |
| S2 | CO | 5 (6–7 depts each) | 214–215 | 856–857 | – |
| S3 | BR | 5 (blocks 0+3, 1+2, 4+9, 5+6, 7+8) | 966–1219 | 3631–4124 | 340–678 |
| S3 | CO | 6 | 30–246 | 528–1038 | 3–297 |
| S2L (legacy) | BR / CO | 27 / 33 | 1–853 / 1–125 | | – |
| S3B (legacy) | BR | 10 | 107–961 | 3910–5378 | 32–646 |
| S4 | BR | 5 | 1103–1104 | 4413–4414 | – |
| S4 | CO | 5 | 214–215 | 856–857 | – |
| S5 | TW/BR/CO/PE | 1 each | 287/5517/1071/115 | 6703/1473/5919/6875 | – |

S0/S1 use all units: BR 5517, CO 1071, TW 287, and PE 115 (S1 only). Under S2L, Distrito Federal and Bogotá each form a single-unit fold. CO S3 block 5 has 30 units (Amazon/Orinoquía).

## Flagged units (no geometry → adm1-mean centroid)
- `COLOMBIA|CHOCO|BELEN DE BAJIRA`: its S3 buffer membership is approximate.
- `TAIWAN|HSINCHU CITY|OTHER` and `TAIWAN|TAINAN CITY|OTHER`: no spatial split uses them.

Re-run the build after the boundaries are refined.
