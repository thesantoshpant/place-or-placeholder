# Train/test splits S0–S5 (splits_v1)

Code: `src/pop/splits/{splits,spatial}.py`. Build: `scripts/splits/build_splits.py` (re-runnable, seed 20240101). Outputs: `data/processed/splits_v1/`.

**Origins.** Origin Y trains on target years 2018..Y−1 (lags may use earlier years) and tests on all target weeks of Y, horizons 1–4. Tuning origin 2019 trains on 2018 only. Test origins run from 2020 to the last year of each country: BR 2024, CO 2022, PE 2023, TW 2024. `row_masks()` returns `train`, `test`, `score = test & ~flag_gap` and `train_target_ok`. Gap weeks stay available as inputs.

**Splits.**
- **S0** (BR/CO/TW, leaky): a hash of (unit, week, seed) sends 20% of 2018..Y rows to test. Train uses the other 80%, including rows from Y. Test is the 20% that falls in Y.
- **S1** (all countries): purely temporal; every unit is in both train and test.
- **S2** (BR/CO): leave one adm1 out.
- **S3** (BR/CO): k-means blocks on centroids (k = 10 for BR, 6 for CO). Units within D of the test block are dropped from training.
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
| S2 | BR | 27 | 1–853 | 4664–5516 | – |
| S2 | CO | 33 | 1–125 | 946–1070 | – |
| S3 | BR | 10 | 107–961 | 3910–5378 | 32–646 |
| S3 | CO | 6 | 30–246 | 528–1038 | 3–297 |
| S4 | BR | 5 | 1103–1104 | 4413–4414 | – |
| S4 | CO | 5 | 214–215 | 856–857 | – |
| S5 | TW/BR/CO/PE | 1 each | 287/5517/1071/115 | 6703/1473/5919/6875 | – |

S0/S1 use all units: BR 5517, CO 1071, TW 287, and PE 115 (S1 only). Distrito Federal and Bogotá each form a single-unit S2 fold. CO S3 block 5 has 30 units (Amazon/Orinoquía).

## Flagged units (no geometry → adm1-mean centroid)
- `COLOMBIA|CHOCO|BELEN DE BAJIRA`: its S3 buffer membership is approximate.
- `TAIWAN|HSINCHU CITY|OTHER` and `TAIWAN|TAINAN CITY|OTHER`: no spatial split uses them.

Re-run the build after the boundaries are refined.
