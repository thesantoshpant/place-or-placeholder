# Location-only controls C1–C5

Each control replaces the AlphaEarth block in L4 ("L3 + C"). Everything is rebuilt per split instance and origin.

```python
make_controls(control, units_df, train_units, test_units, origin_year,
              train_rows=None, emb_df=None, seed=0, **kw) -> DataFrame
make_controls_for_split(control, split, units_df, panel=None, emb_df=None, seed=0, **kw)
```

`units_df` holds `unit_id, country, lat, lon`. `load_unit_points()` uses polygon `representative_point()`, which handles the 3 offshore centroids. `emb_df` holds `unit_id, year, A00..A63`. The output covers `train_units ∪ test_units`.

| Control | Output columns | Definition |
|---|---|---|
| C1 | `unit_id, c1_te` | Mean log1p(cases) per unit, or log1p(incidence per 100k) when `population=` is given. Training units only. **Seen** (S0/S1): the unit's own mean over the **pre-training years** (see below). **Unseen** (S2–S4): inverse-distance (1/(d+1 km)) mean of the 5 nearest training units in the same country. Training units get a *matched leave-out* kNN value (`train_mode="matched"`, default; see below). **S5**: raises `ControlNotApplicable`. |
| C2 | `unit_id, c2_lat, c2_lon, c2_sh_l{l}_m{m}` (`mn` = negative m) | Orthonormal real spherical harmonics, 1 ≤ l ≤ L (default 8 → 80 columns). |
| C3 | `unit_id, year, c3_A00..c3_A63` | S0/S1/S5: permute across units within each country × embedding year (S5: the target country among its own units). S2–S4: permute training units within country-year; each held-out unit gets a random training unit's embedding from the same country-year. Seeds 0–9; never the identity. |
| C4 | `unit_id, c4_f00..c4_f63` | 64 independent Gaussian random fields per country with exponential covariance exp(−d/`range_km`) (great-circle d). `range_km` is a float or a per-country dict. Exact Cholesky for n ≤ 8000 (Brazil ≈4 s, cached), else random Fourier features. Each field is standardised within its country. Seeds 0–9. |
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
- S2–S4: `train_mode="loo_knn"` reproduces the pre-2026-11-16 output; the default `"matched"` equals it in S4 (tested).

## C1 source rows (`c1_source_rows`, fixed 2026-11-16)

`make_controls_for_split(..., c1_period=...)` picks the rows C1 is computed from:

| `c1_period` | Rows | Used by |
|---|---|---|
| `"auto"` (default) | `"pre_train"` if every test unit is a training unit (S0/S1), else `"train"` | all splits |
| `"pre_train"` | Training units, panel years strictly before the first training target year (`min(split.train_years)`; 2014–2017 for Brazil, the panel's first year onward in general), `flag_gap` weeks dropped as for training targets | S0/S1 |
| `"train"` (legacy) | `row_masks(...)["train_target_ok"]`, years < origin | S2–S4; explicit opt-in for S0/S1 only to reproduce the old run |

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
