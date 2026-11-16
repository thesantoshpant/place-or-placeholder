# AlphaEarth cheap-estimator pilot (Brazil, 2022)

Code: `src/pop/features/alphaearth_sampling.py` and `scripts/features/pilot_alphaearth_cheap.py`. Outputs: `data/interim/alphaearth/cheap_pilot/`.
Each estimate is compared with the 100 m `reduceRegions` reference. AlphaEarth's pyramiding policy is **MEAN**.

## Results
**Columns:**
- **cos**: pop-weighted cosine vs reference, mean / min.
- **MSE/var**: error ÷ between-unit variance.
- **retr**: nearest-reference retrieval.
- **ρ**: Spearman correlation of pairwise distances.
- **uw min**: minimum unweighted cosine.
- **EECU-h**: 7 years × ~6,990 units (10.62 M km²); Brazil in brackets. Scale ×9/7 for 2024–25.

| candidate | n | cos | MSE/var | retr | ρ | uw min | EECU-s/km² | EECU-s/unit-yr | EECU-h |
|---|---|---|---|---|---|---|---|---|---|
| 100 m reduceRegions (ref) | 100 | 1 | 0 | 1 | 1 | 1 | 0.025 | 38 | 516 [414] |
| PPS points N=250 | 100 | .99947/.9972 | .0028 | 1 | .9995 | – | – | 288 | 3,900 |
| 300 m pyramid, pop sum | 90 | .9921/.9516 | .044 | .99 | .9967 | .99988 | .0039 | 6 | 81 [65] |
| 300 m naive (prev.) | 90 | .9925/.9459 | .042 | .99 | .9968 | .99988 | .0052 | 8 | 107 |
| 300 m reduceResolution | 10 | .9955/.9920 | .027 | 1 | .991 | .99996 | 2.53 | – | ~52,000 |
| 200 m pyramid, pop sum | 90 | .9981/.9888 | .010 | 1 | .9991 | .99995 | .0075 | 11 | 154 [123] |
| populated 1 km footprint, 100 m | 1 | .99999997 | 0 | – | – | – | .0044* | – | – |
| **computePixels 100 m f32 + local** | 10 | **.9999998/.9999989** | 1e-6 | 1 | 1 | .9999997 | **.0100**† | 15 | **207 [166]** |
| computePixels 100 m int8 | 10 | .999996/.999994 | 2e-5 | 1 | 1 | .999996 | .0130† | 20 | 268 |
| computePixels 50 m int8 | 4 | .99981/.99944 | .001 | 1 | 1 | .999995 | .0355† | 54 | 733 |

\* Per km² of the unit (Amazon unit, 6% of it populated). The footprint run gives the pop-weighted mean only.
† Per km² of bbox, from profiled interactive requests on 150–1,500 km² units. The largest unit cost 0.0077 per km².

## Findings
- **Points are the most expensive option.** Each 10 m point costs ~1.2 EECU-s, because EE computes a whole tile for it.
- **Coarse grids lose accuracy for pop-weighted means.** The cause is within-cell covariance of population and land cover; summing population does not help. Unweighted means are exact at 300 m.
- **The footprint method is exact and 5.7× cheaper in the Amazon.** Elsewhere the median unit is 57% populated, so the saving is small.
- **computePixels with local zonal stats is exact and ~2.5× cheaper than reduceRegions.**
  - float32 beats int8 on both cost and accuracy.
  - Brazil transfer at 100 m is ~54 GB/year as int8 and ~218 GB/year as float32. Reducing each block on the fly with sparse weights means nothing needs storing.

## Recommendation
- **Method:** computePixels at 100 m (float32), with block-wise local zonal sums as in the climate pipeline.
  - It is exact.
  - Projected cost is **~165–210 EECU-h** for all countries over 2017–23, about 1.1–1.4 months of quota.
  - With 2024–25 added: ~270 EECU-h.
- **Follow-up:** fetch only populated blocks at 100 m, and the rest at 300 m for the unweighted mean.
- **Fallback:** 200 m reduceRegions (154 EECU-h). It loses ~1% of between-unit variance.
- **Avoid:** point sampling and reduceResolution.

## EECU used
- **Batch:** points 28,773; reduceResolution 2,006; 300 m and 200 m coarse runs 1,143; footprint 301.
- **Interactive computePixels:** 380.
- **Total:** **≈32,600 EECU-s (9.1 EECU-h)**. GHSL getPixels was not profiled.
