# Location-only controls C1–C6 (+ C4s)

Each control replaces the AlphaEarth block in L4 ("L3 + C"). Everything is rebuilt per split instance and origin.

```python
make_controls(control, units_df, train_units, test_units, origin_year,
              train_rows=None, emb_df=None, seed=0, **kw) -> DataFrame
make_controls_for_split(control, split, units_df, panel=None, emb_df=None, seed=0, **kw)
```

`units_df` holds `unit_id, country, lat, lon`. `load_unit_points()` uses polygon `representative_point()`, which handles the 3 offshore centroids. `emb_df` holds `unit_id, year, A00..A63`. The output covers `train_units ∪ test_units`.

| Control | Output columns | Definition |
|---|---|---|
| C1 | `unit_id, c1_te` | Mean log1p(cases) per unit, or log1p(incidence per 100k) when `population=` is given. Training units only, **pre-training years only in every split** (see below). **Seen** (S0/S1): the unit's own mean. **Unseen** (S2–S4): inverse-distance (1/(d+1 km)) mean of the 5 nearest training units in the same country, from those units' pre-training means. Training units get a *matched leave-out* kNN value (`train_mode="matched"`, default; see below). **S5**: raises `ControlNotApplicable`. |
| C2 | `unit_id, c2_lat, c2_lon, c2_sh_l{l}_m{m}` (`mn` = negative m) | Orthonormal real spherical harmonics, 1 ≤ l ≤ L (default 8 → 80 columns). |
| C3 | `unit_id, year, c3_A00..c3_A63` | One fixed source map π per seed and country, used for **every** year: unit i gets the real year-y embedding of π(i) (`c3_source_map`). S0/S1/S5: π permutes the country's units (S5: the target country among its own units). S2–S4: π permutes training units; each held-out unit gets one random training unit (with replacement). Never the identity. A source with no embedding in year y gives NaN. |
| C4 | `unit_id, c4_f00..c4_f63` | 64 independent Gaussian random fields per country with exponential covariance exp(−d/`range_km`) (great-circle d). `range_km` is a float or a per-country dict. Exact Cholesky for n ≤ 8000 (Brazil ≈4 s, cached), else random Fourier features. Each field is standardised within its country. Seeds 0–9. |
| C4s | `unit_id, c4s_f00..c4s_f63` | C4 with `range_km` = the country's S3 buffer D (`c4s_range()`, file `data/processed/splits_v1/c4s_range_km.json`): BR 225, CO 130, PE 275, TW 170 km. Same white noise per seed and country as C4. |
| C5 | `unit_id, c5_A00..c5_A63` | The AlphaEarth 2023 embedding, used for every target year. |

Seeds are deterministic: `default_rng([seed, crc32(tag), crc32(country)(, year)])`.

## Matching C4 to AlphaEarth

`fit_embedding_range(emb_df, points, year=None, per_country=False)` builds the within-country semivariogram 0.5·‖e_i − e_j‖²/64 of the district means (averaged over years unless `year` is given), in 25 bins up to half the maximum pair distance.

It fits nugget + psill·(1 − exp(−h/r)) and returns `r`, which is C4's `range_km`. A simulated r = 150 km is recovered within ±40% (tested).

## Leakage guarantees (tested)

- C1 does not change when test-unit rows or rows with year ≥ origin are set to 1e12.
- kNN neighbours are training units only.
- C2–C5 use no target data.

- S0/S1: C1 does not change when every row with year ≥ the first training target year is set to 1e12; it is identical across origins and for training and test rows (`tests/test_controls.py`).
- S2–S4: `c1_period="train", train_mode="loo_knn"` reproduces the pre-2026-11-16 output (tested).
- S1–S4: C1 does not change when every row with year ≥ 2018 is set to 1e12 (tested, origins 2019 and 2021).

## C1 source rows (`c1_source_rows`, fixed 2026-11-16)

`make_controls_for_split(..., c1_period=...)` picks the rows C1 is computed from:

| `c1_period` | Rows | Used by |
|---|---|---|
| `"auto"` (default) | `"pre_train"` in every split (since the control fixes of 2026-11-16; before, S2–S4 used `"train"`) | all splits |
| `"pre_train"` | Training units, panel years strictly before the first training target year (`min(split.train_years)`; 2014–2017 for Brazil, the panel's first year onward in general), `flag_gap` weeks dropped as for training targets | S0–S4 |
| `"train"` (legacy) | `row_masks(...)["train_target_ok"]`, years < origin | explicit opt-in only, to reproduce the old runs |

Why: under S1 the old rule set C1 to the unit's own mean over its *training targets*, so each training row's feature contained its own target (and the targets of its neighbours in time). LightGBM learned to lean on it and it did not transfer to the test year (2019-origin pooled log-WIS 0.263 vs 0.175 for L3). The pre-training mean is fully causal, takes the same value for a unit's training and test rows and does not move with the origin, matching the S2–S4 design in which no training row sees its own target. It can be set from YAML via `features.control_kw.C1.c1_period`.

## C1 matched leave-out (`train_mode="matched"`, default since 2026-11-16)

Under plain leave-one-out (LOO) a training unit's 5 nearest training neighbours are its immediate neighbours, but a held-out unit's nearest training units lie beyond its whole held-out state (S2) or beyond the buffer D (S3). The training encodings were therefore smoother and more local than the test encodings: a train/test distribution mismatch. On BR fold 0 (2020 origin), the median mean distance to the 5 neighbours is:

| Split | Test units | Training units, LOO | Training units, matched |
|---|---|---|---|
| S2 | 105 km | 23 km | 129 km |
| S3 (D = 225 km) | 394 km | 23 km | 227 km |

The matched mode encodes each training unit as if it were held out under the same rule:

| Split | Neighbours excluded for a training unit (`c1_matched_rule`) |
|---|---|
| S2 (grouped leave-states-out) | itself and every unit of its own ADM1 state (`exclude_group="adm1"`) |
| S3 (blocks + buffer) | every unit within D km great-circle, D from `splits_v1/buffer_distance.json` (BR 225, CO 130; `c1_buffer_km=` overrides) (`exclude_within_km=D`) |
| S4 | itself only (plain LOO) |

Held-out units are encoded as before (kNN over all training units). Seen-unit splits (S0/S1) are unaffected (own pre-training mean). A unit with fewer than 5 admissible neighbours uses those it has. Other modes: `"loo_knn"` (the old rule; `"auto"` is an alias for it), and `"own"`. Set from YAML via `features.control_kw.C1.train_mode`.

Tests (`tests/test_controls.py`): no training-unit encoding uses a same-state neighbour in S2 or one within D in S3; the matched output equals a manual kNN with the rule; held-out encodings are unchanged; matched training neighbours are farther than LOO ones; S4 matched = LOO; bad modes and a missing `adm1` column raise errors.

## Control fixes 2026-11-16

Deviations rows 13–15 (`docs/plans/deviations_from_protocol.md`). Tests in `tests/test_controls.py`; invalidated outputs listed in `runs/queue/invalidation_2026-11-16.md`.

1. **C3: fixed source per unit.** Before, `shuffle_embeddings` drew a new permutation for each country × year, so a unit's fake embedding came from a different unit every year (0–0.05% of units kept their source) and C3 was not a stable district ID. Now `c3_source_map(units, train, test, seed)` draws one map π per seed and country, and unit i takes the real year-y embedding of π(i) in every year. Tests: the map is identical across years, matches `c3_source_map`, differs across seeds, never maps most units to themselves, and the values follow the source's real per-year embedding (S1, S2–S4 and S5 layouts).
2. **C1 in S2–S4: pre-training years.** `c1_period="auto"` is now `"pre_train"` in every split. The matched kNN rule is unchanged (S2: own state excluded; S3: neighbours within D excluded; S4: leave-one-out), but the pool values are the neighbours' mean log1p(cases) over the years before the first training target year (Brazil 2014–17), the same quantity and period as S1's C1. Before, the pool used the neighbours' in-period 2018..Y−1 targets, which are contemporaneous with the training targets. Test: setting every row with year ≥ 2018 to 1e12 leaves C1 unchanged in S1, S2, S3 and S4. S1's C1 is unchanged.
3. **C4s: C4 at a short range.** At the fitted range (Brazil 8,483 km) C4 is close to a planar trend, not an ID. `C4s` is C4 with `range_km` = the country's S3 buffer D. For Peru and Taiwan (no S3 split), `scripts/features/estimate_c4s_range.py` applies the S3 rule (max of the first 0.1-crossings of the additive and week-FE correlograms of de-seasonalised log1p cases, 2014–19, ≥ 30 pairs per bin), with the fallback D = median distance to the 10th-nearest unit if neither curve crosses:

   | Country | D (km) | Source | additive / week-FE crossing | 10th-NN median |
   |---|---|---|---|---|
   | Brazil | 225 | S3 buffer | — / 225 | 40 km |
   | Colombia | 130 | S3 buffer | 130 / 80 | 34 km |
   | Peru | 275 | S3 rule (69 units, 25-km bins) | 275 / 225 | 168 km |
   | Taiwan | 170 | S3 rule (80 units, 5-km bins) | 170 / 20 | 15 km |

   Taiwan's additive curve stays above 0.1 out to 170 km because the 2014–15 southern outbreak moves many townships together; the week-FE crossing (20 km) and the 10th-NN distance (15 km) are much shorter. The rule is applied as for Brazil and Colombia (the larger crossing), and the short-range alternatives are recorded in the JSON.

   **Rule (2026-11-16): C4s range = min(D, fitted C4 range).** C4s is meant to be the *shorter* field. Brazil min(225, 8,483) = 225 km and Colombia min(130, 705) = 130 km are unchanged. For Peru (D 275 > fitted 148 km) and Taiwan (D 170 > fitted 27 km) the minimum is the fitted range, so C4s would be identical to C4 (same white noise per seed and country). There it is **not a separate C\* candidate**: `split_pipeline.sh` leaves L3+C4s out of their `controls_2019` (`c4s_is_c4()`). In S5, C4s uses the per-country minimum (BR 225, CO 130, PE 147.55, TW 27.12 km), and stays a candidate because it differs from C4 for the Brazil and Colombia rows. Selections made before the rule with C4s at 275/170 km (PE S1-shared C1, PE S1 per-level C1, TW S1-shared C3, TW S1 per-level C1) never picked C4s, so their C\* is what the rule gives; their C4s rows stay in `selection.csv` for information only.

   C4s is wired as `L3+C4s`, `L4+C4s`, `N3+C4s`, `N4+C4s` and is a C\* candidate in every 2019 selection, seeded like C4 (3 seeds in the split and no-history pipelines, 10 in the per-level S1 pipeline). `select_control.py` handles the name unchanged.

**Pipelines.** `split_pipeline.sh`, `nohist_pipeline.sh` and `s1_pipeline.sh` gained `--gen-controls` (rewrite only the controls_2019 config). Their `gen_cstar` step now calls `scripts/run/supersede.py:guard_final` before writing the final configs: if C\* (or, in `s1_shared`, the reuse decision) differs from the existing final config, the final-stage markers are removed and old-C\* chunks are moved to `chunks_superseded_<date>/`. A final run with an unchanged C\* is kept. `s1_shared` now reuses a per-level S1 C\* run only if that run's config really is `<level>+C*` and its stage finished. Invalidation script: `scripts/run/invalidate_control_fixes.py`.
