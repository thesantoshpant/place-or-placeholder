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
| C1 | `unit_id, c1_te` | Mean log1p(cases) per unit, or log1p(incidence per 100k) when `population=` is given. Training units, years < origin only. **Seen** (S0/S1): the unit's own mean. **Unseen** (S2–S4): inverse-distance (1/(d+1 km)) mean of the 5 nearest training units in the same country. Training units get a *leave-one-out* kNN value (`train_mode="auto"`, or `"own"`); this matches the train and test distributions. **S5**: raises `ControlNotApplicable`. |
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

Under S0, C1 conservatively leaves out the origin-year training rows.
