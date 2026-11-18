# Review comment 8: size and coverage of the primary inference under realistic dependence

Script: `scripts/analysis/inference_size_sim.py` (`extract` → `simulate` → `report`). Seed 20261118, 2,000 replications per cell × DGP, 999 bootstrap resamples per replication.
Outputs: `RC_size_table.csv` (size, 95% CI coverage, power, CI half-width per cell × DGP × method), `RC_real_cells.csv` (real-cell p/CI under every method, surrogate-calibrated p, Holm), `RC_placebo.csv`, `RC_weekly_series.parquet`, `RC_cells.json`, `RC_sim_<cell>.parquet` (per-replication statistics, about 29 MB in total, so do not commit them).

## What was tested

- **Series.** We used d_t, the weekly cross-unit mean of the G_excess row gain, pooled over h = 1 and 4 within each week. It was rebuilt with `estimands_report.load_cell` using the kit's exclusions. For all 13 available primary cells (BR S4 is pending), the mean of d_t equals the results-kit estimate to machine precision. The DGPs are calibrated to each cell's own centred d_t, so pooled horizons, annual refits, seasonality and outbreak bursts are inherited from the real series.
- **Null DGPs (true mean 0).**
  - `iaaft`: windowed IAAFT. We built a circular surrogate of length 8T with the real marginal and the real span-3-smoothed spectrum, then took a random length-T window. A plain length-T IAAFT always reproduces the sample mean, so it cannot be used to measure size. Below frequency 1/T the spectrum is held flat at its lowest smoothed ordinate. This DGP treats the observed multi-year swings in d_t as stationary noise.
  - `iaaft_lf2`: the same, with twice the power below frequency 2/T. This is a stress test.
  - `arx`: two fitted annual harmonics (held fixed, de-meaned), plus AR(p) with p chosen by AIC (p = 1 in every cell). The innovations are resampled standardized residuals multiplied by the real 13-week rolling scale, so the heavy tails and the timing of outbreak volatility are kept.
  - `ar1`: the earlier benchmark, Gaussian φ = .5, T = 104.
  - **Real placebo.** (a) Brazil S1 seed-vs-seed differences of the same model: 21 series, T = 261 (L3, L4, L3+C1, L4+C1 losses and the three estimands; seed pairs 0/1, 0/2, 1/2). (b) The 2019-origin controls C3, C4 and C4s with 3 seeds in BR, CO, PE and TW: 33 series, T = 52. By exchangeability of seeds, every placebo series has true mean 0.
- **Methods.**
  - `ewc_hln` is the primary method (EWC with B = ⌊0.4T^(2/3)⌋, t_B, HLN at h = 4).
  - `ewc` is the same without the HLN factor.
  - `ewc_hln_B8` and `ewc_hln_B4` use fewer cosine terms.
  - `nw94` is Bartlett with the NW94 lag rule.
  - `hac_h1` is Bartlett with lag h−1 = 3.
  - `season_t` is a t-test over consecutive 52-week block means, with (number of seasons − 1) df.
  - `cbb52` and `cbb8` are circular block bootstraps of d_t itself. They estimate the same week-weighted quantity as the primary estimator, use a percentile 95% CI, and use the library's `_block_idx`.
  - All DM variants call `pop.eval.stats` directly. The `ewc_hln` CI is asserted equal to `ewc_inference`.
- 95% CI coverage = 1 − size for every method here (CI and test coincide, and the CIs are shift-equivariant). Power is the rejection rate when d_t is shifted by 0.5% or 1% of WIS(L3).

## Empirical size at nominal 5% (2,000 reps; Monte-Carlo SE ≈ 0.5 pp)

| Cell (T) | EWC+HLN ar/iaaft/lf2 | EWC+HLN B=4 | season-t | NW94 | CBB-52 |
|---|---|---|---|---|---|
| AR(1) φ=.5 (104) | 0.054 | 0.046 | 0.051 | 0.110 | 0.294 |
| BR S1 (261) | 0.069 / **0.218** / **0.280** | 0.034 / 0.149 / 0.150 | 0.03 / 0.16 / 0.17 | 0.36 / 0.42 / 0.49 | 0.21–0.31 |
| BR S2 (261) | 0.060 / **0.146** / **0.244** | 0.049 / 0.080 / 0.070 | ≤0.09 | 0.24–0.50 | 0.18–0.27 |
| BR S3 (261) | 0.026 / 0.118 / 0.195 | ≤0.054 | ≤0.07 | 0.19–0.39 | 0.15–0.23 |
| BR S5 (261) | 0.069 / 0.012 / 0.042 | ≤0.048 | ≤0.05 | 0.11–0.24 | 0.11–0.16 |
| CO S1 (157) | 0.001 / 0.048 / 0.093 | ≤0.034 | ≤0.06 | 0.02–0.30 | 0.18–0.20 |
| CO S2 (157) | 0.001 / 0.011 / 0.038 | ≤0.032 | ≤0.06 | 0.02–0.20 | 0.15–0.20 |
| CO S3 (157) | 0.001 / 0.002 / 0.007 | ≤0.022 | ≤0.06 | 0.02–0.08 | 0.06–0.22 |
| CO S4 (157) | 0.004 / 0.073 / 0.122 | ≤0.042 | ≤0.05 | 0.03–0.35 | 0.20–0.22 |
| CO S5 (157) | 0.079 / **0.159** / **0.226** | 0.044 / 0.067 / 0.090 | ≤0.06 | 0.25–0.46 | 0.24–0.27 |
| PE S1 (209) | 0.031 / 0.102 / 0.163 | ≤0.058 | ≤0.06 | 0.10–0.36 | 0.16–0.21 |
| PE S5 (209) | 0.013 / 0.004 / 0.008 | ≤0.046 | ≤0.05 | 0.02–0.10 | 0.09–0.16 |
| TW S1 (209) | 0.012 / 0.047 / 0.120 | ≤0.056 | ≤0.05 | 0.09–0.25 | 0.16–0.23 |
| TW S5 (209) | 0.043 / 0.011 / 0.050 | ≤0.048 | ≤0.07 | 0.11–0.22 | 0.13–0.17 |
| **Median across cells** | 0.026 / 0.048 / 0.120 | 0.034 / 0.036 / 0.048 | 0.05 | 0.10 / 0.20 / 0.30 | 0.18–0.21 |

The 8-week bootstrap and `hac_h1` are worse than NW94 (maximum size 0.36–0.54).

**Real placebo (seed differences, true mean 0; seed placebo uses the kit exclusions for BR S1, none for the 2019 controls):**
- BR S1, T = 261, 21 series: EWC+HLN rejects 2 of 21 (10%), B4 1, B8 3, season-t 0, NW94 4, CBB-52 3, CBB-8 3.
- 2019 controls, T = 52, 33 series: EWC+HLN 4 of 33 (12%), B4 5, NW94 13, h−1 HAC 13, CBB-8 16. Season-t and CBB-52 are undefined at T = 52.
- The series within each set are correlated, so these rates are imprecise. They agree with the ARX picture, not the IAAFT one.

**Power** (`RC_size_table.csv`, ARX DGP, EWC+HLN, at 0.5% / 1% of WIS(L3)):

| Cells | 0.5% | 1% |
|---|---|---|
| BR S2/S3/S5, CO S1–S4 | 0.84–1.00 | ≈ 1.00 |
| BR S1 | 0.53 | 0.88 |
| CO S5 | 0.78 | 1.00 |
| TW S1 | 0.43 | 0.83 |
| PE S1 | 0.31 | 0.88 |
| PE S5 | 0.09 | 0.53 |
| TW S5 | 0.06 | 0.08 |

TW S5 is so low because its d_t is very noisy relative to WIS(L3). B = 4 loses about 0.1–0.3 of power at 0.5% in the BR cells. Power for the oversized methods (NW94, bootstraps) is not size-adjusted, so it should not be compared directly.

## Do the primary-family conclusions change?

Holm-adjusted p for G_excess over the 13 available cells:

| Cell | Primary EWC+HLN | B4 | IAAFT-calibrated / lf2 / ARX-calibrated |
|---|---|---|---|
| BR S5 | .0006 | .022 | .007 / .007 / .007 |
| CO S1 | .007 | .039 | .007 / .023 / .007 |
| CO S2 | .004 | .022 | .009 / .007 / .007 |
| CO S3 | .022 | .023 | .007 / .007 / .007 |
| TW S5 | .0006 | .022 | .007 / .007 / .007 |
| **CO S4** | .017 | **.10** | .028 / **.088** / .007 |
| PE S5 (+1.0%) | .33 | .13 | .028 / .060 / .070 |
| BR S1, BR S2, BR S3, CO S5, PE S1, TW S1 | ≥ .47 | ≥ .47 | ≥ .44 |

- **BR S5, CO S1, CO S2, CO S3 and TW S5:** the significant small harms survive every calibrated and robust variant.
- **CO S4:** this is the one primary conclusion that is not robust. It is Holm-significant under the primary test but borderline under B4 and lf2 calibration.
- **PE S5:** the gain stays not Holm-significant, except under IAAFT calibration (.028).
- **Non-significant cells:** BR S1, BR S2, BR S3, CO S5, PE S1 and TW S1 are non-significant under every method.
- **Equivalence (TOST) classes:** recomputed with the B4 or B8 CIs, every class is unchanged except CO S3, which moves from "inferior" to "equivalent" under B4.
- **Season-level t-test:** it has only 2–4 df, and under it only BR S5 (p = .006), CO S2, CO S3, PE S5 and TW S5 reject unadjusted. After Holm, none remains significant (Holm p ≥ .074; BR S5 .074 is the smallest). This is the "new seasons" view, which has very little power.

## Verdict

- **The primary EWC+HLN test is acceptably calibrated when d_t is short-memory around a fixed mean, which it is in most cells.**
  - Size is ≤ 8% in every cell under the ARX DGP, 5.4% for AR(1), and the real seed placebo rejects 10–12%. HLN changes almost nothing (≤ 1 pp).
  - **It is not calibrated when the multi-year drift in d_t is treated as stationary noise (IAAFT).**
    - Size is 10–22% in BR S1, BR S2, BR S3, CO S5 and PE S1, and up to 28% under the low-frequency stress.
    - These are cells whose gain trends across seasons. For example, BR S1's yearly mean of d_t rises from −0.0004 log-WIS in 2020 to +0.0024 in 2024, and its lowest periodogram ordinate is about 3.5× the mean of the 16 that EWC uses.
- **Newey–West (NW94), the h−1 HAC and both block bootstraps are badly oversized** (typically 10–50%). They should not be primary, and the 52-week bootstrap is unusable at these T (only 3–5 blocks).
- **Recommendation.**
  - Keep EWC+HLN as the primary test. This avoids a post-hoc change of method, and no significant conclusion depends on it except CO S4.
  - Report two robustness columns:
    - (i) EWC with B = 4. Its size is ≤ 9% in 12 of 13 cells under every DGP, and it is 15% only for BR S1 under IAAFT.
    - (ii) IAAFT-calibrated p-values.
  - Flag CO S4 as fragile.
  - If the planner prefers one primary method that is robust to multi-year drift, use B = 4. The family conclusions are then the same except CO S4 (Holm .10).
  - Equivalence statements for BR S1, BR S2 and CO S5 rest on the short-memory view. Under IAAFT their CIs are too narrow by roughly a factor of 1.3–1.6, so call them "equivalent assuming no multi-season drift".

## What population the inference refers to

The test treats **weeks as the sampling unit**, for this fixed set of units, these fitted model pipelines and these test seasons. It asks whether a mean loss difference this large could arise from week-to-week noise around a fixed average. It is not inference about other districts, other countries, or a new set of seasons. Generalizing to new seasons would require the between-season variance (`season_t`, 2–4 df), which these data can barely estimate. Spatial-split cells (S2–S5) average over held-out units, but those units are still a fixed set: the S2–S5 folds are partitions, not samples. MDEs (`mde_pct`) are approximate unadjusted thresholds at 80% power. For Holm over 14 cells, the multiplicity-adjusted threshold is about 1.34× larger ((z_{1−.05/28} + z_{.80}) / (z_{.975} + z_{.80}) = (2.91 + 0.84) / (1.96 + 0.84)).
