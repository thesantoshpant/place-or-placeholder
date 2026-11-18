# RB: exploratory strata, embedding distance, additive decomposition (scoring only)

Script: `scripts/analysis/review_explore.py` (strata / distance / decomp; no refits). Cells: the 13 available primary cells (BR S4 pending). Rows = primary rows (default exclusions, h{1,4} pooled, seed-averaged; rule-v2 C\*). Inference = primary estimator (equal-week pooling, DM/EWC + HLN). All subgroup tests are **exploratory, with no multiplicity adjustment**. Gains are positive when embeddings help. Integrity: per-row WIS rebuilt from forecasts matches the stored scores to <= 1.4e-15 (`RB_wis_reconstruction_check.json`).

## 1. Exploratory strata for RQ5 (`RB_strata.csv`)

Strata: (a) population tercile (unit population in the year before the test year; terciles within cell x test year); (b) surveillance history = number of years 2014-2017 with >= 1 reported case (0 / 1-2 / 3-4); (c) urban growth = GHSL built-up share change 2010 -> 2015, terciles within cell (a relative-growth variant is also in the file). Values are G_excess as % of the stratum's own WIS(L3); the file also gives additive contributions (% of the cell's total WIS(L3)), which sum to the cell total.

- **No stratum shows a gain in any Brazil, Colombia or Taiwan cell.** Brazil S1 strata are all +0.06% to +0.58%, every CI including 0; Brazil S2 strata are within +/-0.15%, all ns.
- **Harm is largest where surveillance history is shortest** in spatial and transfer cells. Units with no case in 2014-17 lose -1.8% (BR S3), -2.5% (BR S5), -7% to -41% (CO S2-S5; 65 units, 6% of rows; their own WIS is tiny, so the additive contribution is <= 0.05 pp) and -28.8% (TW S5). Units with 3-4 history years lose least (BR S5 -0.47%, CO S2-S4 about -0.4%, TW S5 -5.9%).
- **Population:** in Colombia the least-populated tercile is harmed most (CO S2 -1.27% vs -0.27% in the top tercile; CO S3 -2.36% vs -0.21%). Brazil S5 is uniform (-0.58% to -0.77%).
- **Urban growth:** no consistent pattern. Colombia's lowest-growth tercile is harmed most (CO S3 -1.39% vs -0.28%), which co-varies with population. Brazil S1 point estimates rise with growth (+0.06% -> +0.41%), none significant.
- **The only significant stratum gains are in Peru S5** (population middle tercile +2.18%, p = .001; history 3-4 +1.35%, p = .019; growth terciles 1-2 +2.13% and +1.45%). That cell is already known to be fragile (RD: the gain vanishes under weighting and recalibration).
- Reading for RQ5: embeddings do not help in fast-urbanising, small or low-history units; where they hurt, they hurt most in units with little pre-2018 surveillance history.

## 2. Embedding distance vs unit gain (`RB_distance_units.csv`, `RB_distance_bins.csv`, `RB_distance_spearman.csv`, `RB_upperq_bins.csv`, `RB_s5_distance.png`)

Distance = max (and top-5 mean) cosine similarity between a held-out unit's renormalised AlphaEarth y-1 vector and the training units' vectors for y-1. Spearman rho of per-unit gain vs cos_max (naive p; units are not independent):

| cell | rho G_excess | rho G_emb | units harmed (G_excess < 0) | median cos_max |
|---|---|---|---|---|
| TW S5 | -0.10 (p .09) | -0.23 | 285/285 (100%) | 0.77 |
| BR S5 | +0.11 | +0.22 | 80% | 0.75 |
| PE S5 | +0.48 | +0.49 | 54% | 0.86 |
| CO S5 | +0.15 | +0.02 | 59% | 0.82 |
| BR S2 / S3 | +0.05 / +0.15 | +0.07 / +0.11 | 48% / 57% | 0.98 / 0.95 |
| CO S2 / S3 / S4 | +0.02 / -0.05 / +0.07 | +0.01 / -0.02 / +0.08 | 71% / 68% / 71% | 0.97 / 0.94 / 0.98 |

- **Taiwan S5: the harm is not monotone in distance.** All 285 units are harmed, in every similarity quintile. In absolute log-WIS the harm per quintile is -0.0026, -0.0032, -0.0025, -0.0025, -0.0034 (least to most similar): flat, with a slightly negative rank correlation. The %-of-WIS(L3) values per quintile (-34.7% -> -6.0%) fall with similarity only because the quintile's WIS(L3) rises from 0.0075 to 0.057. There is no within-Taiwan dose-response; the harm is country-wide. Covariate shift stays a consistent explanation (Taiwan's median nearest-training cosine 0.77 vs 0.94-0.98 within countries) but is not demonstrated.
- **Peru S5 is the one cell with a clear gradient:** the least-similar quintile loses (-0.0030 log-WIS) and the most-similar quintile gains (+0.0068). Consistent with the embeddings helping only where Peruvian units resemble training units.
- **Brazil S5** loses slightly more in the least-similar quintiles (-0.0014 vs -0.0010 log-WIS); 80% of units are harmed. Within-country splits show weak or no relation (|rho| <= 0.15).
- **Upper quantiles on zero rows:** in TW S5, quantiles above the median account for 94-100% of the zero-row loss in every quintile and q0.9 alone for 61-75%; mean q0.9 (cases) rises 0.10 -> 0.21 in the least-similar quintile and 0.29 -> 0.44 in the most similar. The same upper-quantile share (about 95-110%) holds in BR S5 and CO S2-S4.

Wording consequence: "Taiwan's loss is consistent with a shift in embedding space away from the training countries; within Taiwan it does not grow with distance." Do not write that the harm occurs because Taiwan's nearest neighbours are high-incidence cities.

## 3. Additive contribution identity (`RB_decomp.csv`)

Per (h, week), d = w d_obs + (1 - w) d_zf, with w the observed row share, so stratum contributions (as % of the cell's total WIS(L3)) add exactly to the total (max residual 4e-19). Two strata here (observed / zero-filled); the three-way split (positive / recorded zero / zero-filled) is in `RA_strata3.csv`.

| cell | observed | zero-filled | total |
|---|---|---|---|
| BR S1 | +0.47 | -0.21 | +0.26 |
| BR S2 | +0.21 | -0.19 | +0.02 |
| BR S3 | +0.26 | -0.39 | -0.13 |
| BR S5 | +0.05 | -0.68 | -0.63 |
| CO S1 | +0.20 | -0.59 | -0.39 |
| CO S2 | +0.21 | -0.69 | -0.48 |
| CO S3 | +0.08 | -0.77 | -0.68 |
| CO S4 | +0.26 | -0.70 | -0.44 |
| CO S5 | +0.23 | -0.05 | +0.18 |
| PE S1 | +0.14 | -0.76 | -0.62 |
| PE S5 | +1.34 | -0.33 | +1.01 |
| TW S1 | -0.08 | -0.31 | -0.39 |
| TW S5 | +1.14 | -12.67 | -11.53 |

- The zero-filled contribution is negative in all 13 cells and significant (p < .05) in 11 (not CO S5, p .83; TW S1, p .36). The observed contribution is significant only in PE S5 (p .009) and CO S5 (p .048).
- Combining the stratum's own-WIS percentages by row share misses the total by up to 0.0005 log-WIS (BR S3, BR S5), because strata differ in week composition. Use contributions, not own-WIS percentages, whenever the text says the strata "explain" the total.
