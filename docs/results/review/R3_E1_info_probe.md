# R3-E1 information probe: do AlphaEarth embeddings carry district dengue-burden information?

Script: `scripts/analysis/info_probe.py`. Long-format results: `R3_E1_info_probe.csv`. Figure: `docs/results/figures/pub/FigS4_info_probe.png`.

## Design

- One row per district (no-geometry units dropped; exclusions_v2 applied to weeks: primary incomplete weeks and Espírito Santo from 2019-12-29, so ES units have no T2). Targets: **T1** mean log1p weekly cases 2014-2019; **T2** mean log1p weekly cases, test years (2020-last); **T3** share of weeks with >=1 case 2014-2019; **T4** mean log1p weekly incidence per 100k 2014-2019. T1/T3/T4 need ≥104 pre-period weeks.
- Features: **E** = AlphaEarth 2018 pop-weighted district mean, renormalised to unit length (64 dims); variants E1718 (mean of 2017–18) and Epca8 (PCA-8 fitted inside each training fold). **G** = representative-point lat/lon + real spherical harmonics L=8 (C2 features). **S** = 2017–18 means of NDVI, day/night LST, log night lights, log built share, tmean/tmin/tmax, log precip, RH, plus log population 2018.
- Models: ridge (standardised, alpha by efficient leave-one-out inner CV over 1e-3..1e5) and LightGBM (31 leaves, 200 rounds, lr 0.05, feature_fraction 0.8).
- CV: grouped by state into 5 folds with the S2 rule (`group_adm1_folds`; identical to the S2 folds for Brazil and Colombia), random 5-fold, and leave-one-country-out (LOCO) on within-country standardised targets (R² computed inside the held-out country).
- Out-of-fold R² and Spearman ρ; 95% CIs from 1000 state-cluster bootstrap resamples of the OOF predictions (fold models not refitted, so CIs reflect evaluation-sample uncertainty only). ΔR² is paired on the same resamples.

Units: Brazil 5517, Colombia 1070, Peru 115, Taiwan 285.

## T1: mean log1p weekly cases 2014-2019

Out-of-fold R² [95% CI], grouped-state CV (ridge / LightGBM), and ΔR² of adding E.

| Country | Model | G | S | E | G+S | G+S+E | ΔR² E over G | ΔR² E over S | ΔR² E over G+S | ΔR² Epca8 over G+S |
|---|---|---|---|---|---|---|---|---|---|---|
| Brazil | ridge | -0.44 | 0.46 | 0.34 | 0.30 | 0.47 | +0.580 [+0.103, +1.247] | +0.084 [+0.046, +0.146] | +0.169 [-0.050, +0.724] | +0.056 [-0.046, +0.272] |
| Brazil | lgbm | 0.06 | 0.65 | 0.49 | 0.71 | 0.72 | +0.437 [+0.321, +0.545] | +0.058 [+0.015, +0.100] | +0.010 [-0.002, +0.025] | -0.004 [-0.013, +0.005] |
| Colombia | ridge | -0.20 | 0.53 | 0.43 | 0.17 | 0.60 | +0.620 [+0.456, +0.908] | +0.083 [+0.009, +0.156] | +0.423 [+0.015, +1.444] | +0.325 [+0.013, +1.146] |
| Colombia | lgbm | -0.17 | 0.66 | 0.52 | 0.71 | 0.72 | +0.674 [+0.521, +0.894] | +0.042 [+0.005, +0.083] | +0.010 [-0.018, +0.042] | +0.009 [-0.011, +0.034] |
| Peru | ridge | -0.10 | 0.20 | 0.33 | 0.06 | 0.36 | +0.349 [+0.049, +0.649] | +0.238 [+0.050, +0.506] | +0.299 [-0.123, +0.917] | +0.134 [-0.354, +0.651] |
| Peru | lgbm | -0.16 | 0.43 | 0.24 | 0.45 | 0.38 | +0.366 [-0.040, +0.801] | -0.112 [-0.320, +0.033] | -0.071 [-0.267, +0.070] | -0.034 [-0.147, +0.067] |
| Taiwan | ridge | -0.44 | 0.13 | -0.02 | -0.57 | -0.77 | +0.096 [-38.040, +0.350] | -0.409 [-27.731, +0.286] | -0.205 [-20.103, +3.104] | -0.068 [-16.480, +2.875] |
| Taiwan | lgbm | -0.38 | 0.55 | 0.45 | 0.33 | 0.40 | +0.776 [-12.644, +15.458] | -0.015 [-9.922, +0.181] | +0.070 [-8.202, +0.399] | -0.050 [-2.773, +0.043] |

Other CV schemes (best of ridge/LightGBM by point R²): R² of E alone; ΔR² of E over G+S (same model).

| Country | random: E | random: ΔR² E/G+S | LOCO: E | LOCO: G+S | LOCO: ΔR² E/G+S |
|---|---|---|---|---|---|
| Brazil | 0.61 (lgbm) | +0.006 [-0.000, +0.015] | -0.34 (lgbm) | 0.41 | -0.012 [-0.047, +0.012] |
| Colombia | 0.58 (lgbm) | +0.002 [-0.021, +0.023] | 0.28 (lgbm) | 0.58 | -0.055 [-0.110, +0.011] |
| Peru | 0.37 (ridge) | -0.069 [-0.167, +0.035] | 0.27 (lgbm) | -2.86 | -0.072 [-0.780, +0.256] |
| Taiwan | 0.70 (lgbm) | -0.086 [-2.871, +0.007] | -1.98 (ridge) | -1.81 | -0.547 [-71.607, -0.089] |

## T2: mean log1p weekly cases, test years (2020-last)

Out-of-fold R² [95% CI], grouped-state CV (ridge / LightGBM), and ΔR² of adding E.

| Country | Model | G | S | E | G+S | G+S+E | ΔR² E over G | ΔR² E over S | ΔR² E over G+S | ΔR² Epca8 over G+S |
|---|---|---|---|---|---|---|---|---|---|---|
| Brazil | ridge | -0.74 | 0.49 | 0.42 | 0.56 | 0.56 | +0.667 [-0.120, +1.746] | +0.118 [+0.075, +0.188] | +0.001 [-0.091, +0.107] | +0.015 [-0.010, +0.071] |
| Brazil | lgbm | 0.06 | 0.67 | 0.54 | 0.71 | 0.72 | +0.463 [+0.329, +0.638] | +0.052 [+0.021, +0.098] | +0.009 [-0.010, +0.046] | -0.002 [-0.010, +0.010] |
| Colombia | ridge | -0.98 | 0.52 | 0.42 | -0.43 | 0.32 | +0.924 [+0.239, +2.536] | +0.034 [-0.048, +0.106] | +0.755 [+0.036, +2.898] | +0.313 [-0.014, +1.189] |
| Colombia | lgbm | -0.38 | 0.70 | 0.52 | 0.66 | 0.65 | +0.768 [+0.447, +1.275] | +0.009 [-0.017, +0.040] | -0.006 [-0.024, +0.019] | +0.000 [-0.019, +0.017] |
| Peru | ridge | -0.55 | 0.56 | 0.44 | 0.46 | 0.59 | +0.895 [+0.317, +1.685] | +0.011 [-0.203, +0.199] | +0.125 [-0.118, +0.420] | +0.055 [-0.201, +0.358] |
| Peru | lgbm | -0.02 | 0.52 | 0.45 | 0.63 | 0.62 | +0.475 [+0.219, +0.722] | +0.083 [-0.032, +0.228] | -0.015 [-0.140, +0.097] | -0.005 [-0.077, +0.068] |
| Taiwan | ridge | -0.74 | 0.04 | -0.09 | -0.55 | -0.49 | +0.465 [-1.505, +3.556] | -0.188 [-4.657, +0.089] | +0.056 [-4.115, +0.853] | -0.210 [-4.793, +0.140] |
| Taiwan | lgbm | 0.06 | -0.15 | 0.14 | 0.09 | -0.01 | +0.012 [-1.334, +0.345] | +0.095 [-0.473, +0.973] | -0.104 [-1.021, +0.047] | -0.151 [-1.087, -0.079] |

Other CV schemes (best of ridge/LightGBM by point R²): R² of E alone; ΔR² of E over G+S (same model).

| Country | random: E | random: ΔR² E/G+S | LOCO: E | LOCO: G+S | LOCO: ΔR² E/G+S |
|---|---|---|---|---|---|
| Brazil | 0.66 (lgbm) | -0.000 [-0.008, +0.008] | -0.34 (lgbm) | 0.40 | -0.131 [-0.296, -0.052] |
| Colombia | 0.59 (lgbm) | -0.013 [-0.030, +0.006] | 0.23 (lgbm) | 0.52 | -0.056 [-0.113, +0.007] |
| Peru | 0.60 (ridge) | +0.111 [+0.036, +0.213] | 0.41 (lgbm) | -2.07 | +0.052 [-0.218, +0.309] |
| Taiwan | 0.47 (lgbm) | -0.084 [-0.462, -0.008] | -2.44 (ridge) | -1.84 | -1.080 [-16.870, -0.281] |

## T3: share of weeks with >=1 case 2014-2019

Out-of-fold R² [95% CI], grouped-state CV (ridge / LightGBM), and ΔR² of adding E.

| Country | Model | G | S | E | G+S | G+S+E | ΔR² E over G | ΔR² E over S | ΔR² E over G+S | ΔR² Epca8 over G+S |
|---|---|---|---|---|---|---|---|---|---|---|
| Brazil | ridge | -1.13 | 0.51 | 0.41 | 0.25 | 0.32 | +1.428 [+0.335, +3.306] | +0.097 [+0.041, +0.161] | +0.069 [-0.135, +0.364] | +0.040 [-0.015, +0.123] |
| Brazil | lgbm | 0.08 | 0.65 | 0.51 | 0.71 | 0.71 | +0.437 [+0.299, +0.564] | +0.044 [-0.003, +0.082] | -0.001 [-0.015, +0.011] | +0.005 [-0.004, +0.012] |
| Colombia | ridge | -0.34 | 0.61 | 0.53 | 0.33 | 0.59 | +0.849 [+0.566, +1.403] | +0.072 [+0.000, +0.141] | +0.259 [+0.051, +0.733] | +0.126 [+0.020, +0.344] |
| Colombia | lgbm | -0.07 | 0.67 | 0.56 | 0.72 | 0.72 | +0.584 [+0.412, +0.796] | +0.034 [-0.011, +0.079] | -0.002 [-0.027, +0.023] | +0.002 [-0.013, +0.016] |
| Peru | ridge | -0.22 | 0.40 | 0.23 | -0.64 | 0.46 | -0.005 [-1.010, +0.778] | +0.171 [+0.019, +0.348] | +1.102 [-0.206, +3.219] | +0.911 [-0.399, +2.887] |
| Peru | lgbm | -0.04 | 0.52 | 0.33 | 0.51 | 0.49 | +0.423 [+0.072, +0.837] | +0.002 [-0.149, +0.139] | -0.024 [-0.197, +0.181] | +0.035 [-0.068, +0.153] |
| Taiwan | ridge | -0.80 | 0.25 | 0.24 | -0.46 | -0.27 | +0.700 [-0.099, +8.526] | -0.162 [-3.462, +0.504] | +0.197 [-0.178, +3.983] | +0.115 [-0.556, +2.489] |
| Taiwan | lgbm | 0.09 | 0.67 | 0.53 | 0.55 | 0.53 | +0.324 [-1.326, +1.065] | -0.023 [-1.150, +0.063] | -0.018 [-1.319, +0.206] | -0.028 [-0.326, +0.010] |

Other CV schemes (best of ridge/LightGBM by point R²): R² of E alone; ΔR² of E over G+S (same model).

| Country | random: E | random: ΔR² E/G+S | LOCO: E | LOCO: G+S | LOCO: ΔR² E/G+S |
|---|---|---|---|---|---|
| Brazil | 0.65 (lgbm) | -0.003 [-0.009, +0.003] | 0.07 (lgbm) | 0.45 | +0.021 [-0.013, +0.053] |
| Colombia | 0.66 (lgbm) | -0.006 [-0.019, +0.003] | 0.33 (lgbm) | 0.57 | -0.003 [-0.045, +0.033] |
| Peru | 0.56 (ridge) | -0.007 [-0.093, +0.081] | 0.30 (lgbm) | -0.66 | +0.241 [-0.014, +0.539] |
| Taiwan | 0.76 (ridge) | -0.049 [-0.295, -0.005] | -0.76 (lgbm) | -1.14 | -0.479 [-9.982, -0.140] |

## T4: mean log1p weekly incidence per 100k 2014-2019

Out-of-fold R² [95% CI], grouped-state CV (ridge / LightGBM), and ΔR² of adding E.

| Country | Model | G | S | E | G+S | G+S+E | ΔR² E over G | ΔR² E over S | ΔR² E over G+S | ΔR² Epca8 over G+S |
|---|---|---|---|---|---|---|---|---|---|---|
| Brazil | ridge | -0.04 | 0.29 | 0.37 | 0.16 | 0.18 | +0.379 [+0.153, +0.757] | +0.139 [+0.067, +0.239] | +0.017 [-0.270, +0.367] | -0.058 [-0.139, -0.011] |
| Brazil | lgbm | 0.29 | 0.43 | 0.44 | 0.55 | 0.55 | +0.147 [+0.061, +0.226] | +0.087 [+0.034, +0.146] | -0.008 [-0.025, +0.008] | -0.004 [-0.013, +0.005] |
| Colombia | ridge | -0.97 | 0.46 | 0.46 | 0.25 | 0.49 | +1.405 [+0.621, +2.911] | +0.055 [-0.058, +0.157] | +0.238 [+0.068, +0.596] | +0.100 [+0.009, +0.271] |
| Colombia | lgbm | 0.01 | 0.45 | 0.46 | 0.56 | 0.53 | +0.441 [+0.304, +0.629] | +0.081 [+0.018, +0.179] | -0.034 [-0.079, -0.002] | -0.009 [-0.043, +0.013] |
| Peru | ridge | -0.31 | 0.16 | 0.35 | 0.26 | 0.32 | +0.578 [+0.028, +1.259] | +0.219 [+0.080, +0.461] | +0.059 [-0.214, +0.439] | +0.000 [-0.446, +0.393] |
| Peru | lgbm | -0.21 | -0.02 | 0.22 | 0.02 | 0.10 | +0.497 [+0.109, +0.896] | +0.175 [-0.251, +0.773] | +0.077 [-0.121, +0.248] | +0.090 [-0.037, +0.192] |
| Taiwan | ridge | -1.48 | 0.18 | 0.06 | -0.46 | -0.54 | +1.215 [-0.833, +37.126] | -0.173 [-11.654, +0.352] | -0.086 [-13.217, +0.139] | -0.037 [-32.482, +1.867] |
| Taiwan | lgbm | 0.15 | 0.54 | 0.48 | 0.43 | 0.42 | +0.193 [-14.765, +0.355] | +0.005 [-6.376, +0.205] | -0.007 [-9.965, +0.065] | -0.043 [-2.434, +0.035] |

Other CV schemes (best of ridge/LightGBM by point R²): R² of E alone; ΔR² of E over G+S (same model).

| Country | random: E | random: ΔR² E/G+S | LOCO: E | LOCO: G+S | LOCO: ΔR² E/G+S |
|---|---|---|---|---|---|
| Brazil | 0.60 (lgbm) | -0.008 [-0.015, -0.001] | -0.17 (lgbm) | 0.08 | +0.209 [+0.094, +0.409] |
| Colombia | 0.60 (lgbm) | -0.002 [-0.027, +0.023] | 0.27 (ridge) | 0.41 | +0.039 [+0.012, +0.062] |
| Peru | 0.51 (ridge) | -0.076 [-0.232, +0.036] | 0.19 (lgbm) | -0.52 | +0.501 [+0.166, +1.391] |
| Taiwan | 0.73 (ridge) | -0.017 [-3.705, +0.128] | -0.44 (lgbm) | -1.34 | +0.827 [+0.201, +124.517] |

## Interpretation

**Read LightGBM as the primary model.** Ridge on the 82 coordinate/harmonic columns extrapolates badly to held-out states. G alone gives R² from −0.2 to −1.1 under grouped CV, so ridge ΔR² "E over G+S" (e.g. CO T1 +0.42) mostly shows ridge G+S failing, not E adding information. LightGBM does not have this problem.

1. **The embeddings do carry district burden information.** With grouped-state CV, so the predictions are for unseen states, AlphaEarth alone (LightGBM) explains R² ≈ 0.49 (Brazil), 0.52 (Colombia), 0.24 (Peru) and 0.45 (Taiwan) of the between-district variance in pre-period mean log cases (T1). Results are similar for test-period burden (T2: 0.54, 0.52, 0.45, 0.14), the share of case weeks (T3) and incidence (T4). Coordinates alone transfer poorly to unseen states (R² ≈ −0.4 to 0.1). On its own, then, E is far more informative than location, so explanation (a), "no transferable information", is rejected.
2. **That information is almost entirely redundant with cheap static covariates plus coordinates.** In Brazil and Colombia, E is slightly weaker than the 11 static covariates (S ≈ 0.65). It adds a small, significant amount over S alone (ΔR² +0.04 to +0.06 in BR/CO for T1 and T2). It adds essentially nothing over G+S: ΔR² is +0.010 [−0.002, +0.025] (BR T1), +0.010 [−0.018, +0.042] (CO T1), +0.009 [−0.010, +0.046] (BR T2) and −0.006 [−0.024, +0.019] (CO T2). The PCA-8 variant gives the same result. In Peru (115 units) and Taiwan (285 units, burden concentrated in a few southern districts) the point estimates over G+S are negative or near zero, and the CIs are wide. Taiwan's state-cluster bootstrap is unstable because resamples without Kaohsiung/Tainan have almost no variance.
3. **Leave-one-country-out:** E transfers weakly or not at all across countries (T1 R² −0.34 BR, 0.28 CO, 0.27 PE, < 0 TW). It improves on G+S in a consistent way only for incidence (T4). There it fixes G+S, which is close to useless across countries; for T1/T2 it does not improve on G+S.
4. **Random 5-fold CV** gives the same picture: E alone has R² 0.4–0.7, and its increment over G+S is ≤ 0.01 (BR/CO).

**Bottom line for the paper.** The embeddings are not empty. They predict which districts carry high dengue burden about as well as standard environmental covariates do, and much better than coordinates for unseen states. Once statics and coordinates are included, they add < 0.01–0.02 R². The forecasting null is therefore not "AlphaEarth has no dengue signal". It is that the signal duplicates information other inputs already supply: statics and coordinates here, and case history in the forecasting ladder. This supports explanation (b), with a sharper wording: the redundancy holds even cross-sectionally, before case history is added.

**Caveats.** These are cross-sectional associations, not causal. The CIs come from state-cluster bootstraps of fixed out-of-fold predictions, so they ignore refit variability. S uses 2017–18 means, which overlap the T1 period; E uses 2018, which also lies inside the T1 window. T2 has no such overlap. LightGBM has no tuning beyond the fixed small configuration.

Runtime: 28.2 min (nice 19, ≤8 threads).
