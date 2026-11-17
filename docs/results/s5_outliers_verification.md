# Verification of the two S5 outlier cells (TW_S5, PE_S5)

Date: 2026-11-17. Read-only check. Scratch scripts and outputs are on the GPU in `tmp/verify_s5/` (`a1_scores.py`, `a2_fc.py`, `a3_feat.py`, `a4_nn.py`, the logs, and `{taiwan,peru}_merged.parquet`). No runs, configs or results were changed.

## Verdicts

| Cell | Verdict | One line |
|---|---|---|
| **TW_S5** (−11.5%) | **Real model behaviour, no bug.** It is a covariate-shift (out-of-distribution) effect, and the small denominator inflates the percentage. | Taiwan's AE vectors lie far outside the training countries' embedding cloud. Their nearest training units are hyper-endemic Colombian cities, so L4 roughly doubles the upper quantiles on Taiwan's ~97% zero-case rows. Feature construction is correct. |
| **PE_S5** (+1.0%) | **Fragile and borderline. Do not cite it as a positive finding.** | Holm-adjusted p = 0.23 over the 11 available cells (≥0.37 once all 14 are in; Bonferroni 0.65). The gain sits in about 10 Amazonian units and is negative during the 2023 coastal outbreak. |

No bug was found in feature construction, alignment, normalisation or C3 sourcing. One cosmetic issue is listed in section 5.

---

## 1. Ladders (log-WIS, primary scoring: no-geometry units excluded)

T2 numbers reproduce exactly from `runs/*_s5_*/scores.parquet`. L1 and L2 were not run for S5.

**TW_S5** (n = 119,130 rows; WIS(L3) = 0.0245)

| level | h1 | h4 | pooled |
|---|---|---|---|
| L3 | .01839 | .03069 | .02454 |
| L4 | .02121 | .03538 | .02829 |
| L3+C3 | .01878 | .03155 | .02516 |
| L4+C3 | .02069 | .03529 | .02799 |

- G_emb (pooled) = −0.00375 (−15.3%, p < .001).
- G_id = −0.00062 (−2.5%, p = .11).
- G_excess = −0.00283 (−11.5%).

**The harm comes from L4, that is, from the real embeddings.** Adding C3 to L3 costs little; adding AE costs a lot.

**PE_S5** (n = 48,054)

| level | h1 | h4 | pooled |
|---|---|---|---|
| L3 | .18333 | .29662 | .23998 |
| L4 | .18265 | .29379 | .23822 |
| L3+C3 | .18370 | .29841 | .24106 |
| L4+C3 | .18300 | .29428 | .23864 |

- G_emb = +0.00176 (+0.73%, p = .19).
- G_id = −0.00108 (−0.45%, p = .014). C3 *hurts* L3.
- G_excess = +0.00242 (+1.01%, p = .046).
- By horizon: h1 +0.38% (p = .07), h4 +1.40% (p = .047).

So the "superior" G_excess is partly G_emb, which is not significant, plus the fact that C3 degrades the reference model.

## 2. Where the TW effect sits

It is **spread over almost everything, and it lives on zero-case rows.**

**Observed vs zero rows.** Zero-target rows are 115,770 of 119,130 (97.2%). All of them are zero-filled; in Taiwan, positive equals observed.

| rows | WIS L3 | WIS L4 | G_emb | G_excess |
|---|---|---|---|---|
| zero rows | .00858 | .01295 | −.00437 | −.00320 |
| positive rows (3,360) | .5744 | .5569 | **+.0175** | **+.0099** |

On case weeks, the embeddings actually **help** (+1.7% of L3 on those rows).

**Per test year** (G_excess as % of that year's WIS(L3)):

| year | % | p |
|---|---|---|
| 2020 | −48.6 | |
| 2022 | −86.6 | |
| 2023 (outbreak) | −2.1 | .11, ns |
| 2024 | −19.7 | |

The absolute per-row harm is roughly constant (−0.0015 to −0.0040). The percentages explode in years where WIS(L3) is near zero (2022: 0.0034).

**Per week.** G_excess < 0 in 96.7% of weeks: 98% of weeks in 2020, 100% in 2022, 88% in 2023 and 100% in 2024. The ten worst weeks hold only 14% of the total.

**Per unit.**
- **All 285 units** have G_excess < 0. The ten worst hold 7.7% of the total and the worst 30 hold 19.7%.
- The 66 units with zero test-period cases carry 19% of the harm.
- The worst units are dense urban districts of Tainan, Kaohsiung and Taipei.

**Conclusion.** The effect is diffuse and systematic, not driven by a few units or the outbreak.

## 3. Feature checks (TW held out, test year 2023, h1, level L4+C3; rebuilt with the runner's own `build_train`/`build_test`)

**AE features.**
- They are finite for all scored units. The 0.7% NaN rows are exactly the 2 no-geometry "OTHER" units, which are excluded from scoring.
- Norm min/median/max = 0.99999998 / 1.0000000 / 1.00000001, so they are renormalised.

**Alignment.** For 2,000 sampled test rows, the AE vector equals the embedding table at (unit, target epi-year − 1); max abs diff = 1.5e−8.
- The missing 2021 Taiwan case data has no effect, because AE is indexed by calendar year and the grid is dense from 1997 to 2024.
- Test years 2020/22/23/24 read AE 2019/21/22/23, and all of those exist.
- Same result for PE (2022 → AE 2021).

**C3 sourcing.** In 285 of 287 units, the C3 vector equals some *Taiwan* unit's AE for year y−1; the other 2 are the no-geometry NaN units. There are 0 identity matches. So C3 permutes within the held-out country, as designed in `controls.py:226–246` and confirmed for PE (115/115). C3 does not draw from pooled units.

**Other features.**
- No column has a Taiwan-test NaN rate more than 5 points above training, and none is above 20%.
- Shares of TW test rows outside the training 0.5–99.5% range:

| feature | share out of range |
|---|---|
| built_share_y1 | 22% |
| ntl_pw_y1 | 8% |
| lst_night / tmin rolling | ≈6–7% |
| ndvi | ≈5% |

- These shifts are covariate shift, not breakage. L3 already contains them, and TW_S5 L3 (.0245) is better than TW_S1-shared L3 (.0383).
- The LST screen is applied uniformly; it is part of L3 and does not differ between L3 and L4.

**Out-of-distribution check** (AE 2019, unit-normalised `w_` vectors; `a4_nn.py`):

| held-out set | NN cosine to training units: q10 / median / q90 |
|---|---|
| **Taiwan → BR+CO+PE** | **0.70 / 0.76 / 0.81** |
| Peru → BR+CO+TW | 0.71 / 0.87 / 0.96 |
| Colombia → others | 0.74 / 0.82 / 0.91 |
| Brazil → others | 0.59 / 0.70 / 0.78 |
| within-country NN (any country) | median 0.977–0.992 |

- Cosine between the Taiwan centroid and the training centroid is 0.35; for Peru it is 0.72.
- In 2019, 98–100% of Taiwan units fall outside the training 0.5–99.5% range on dimension A01. On AE 2022 the figure is 100%, with A12, A48 and A45 also above 85%.
- **Taiwan's nearest training units are hyper-endemic Colombian cities.** In 2019, 283 of 285 nearest neighbours are Colombian: Barranquilla (53), Santa Marta (51), Bucaramanga (31), Honda (28), Cali (23) and others.
- Those neighbour units had cases in **81%** of 2018–22 weeks. The average training unit had cases in 21%; Taiwan's own units had cases in **0.3%**.
- On AE 2022, Colombia has no AE year (data ends in 2022, by design), so the neighbours become Peru and Brazil. The share of case-weeks is still 81%.

## 4. Mechanism for TW (tested on the forecasts)

The table compares quantile forecasts on Taiwan zero-target rows (n = 115,770):

| level | mean log1p q0.5 | mean log1p q0.9 | share with q0.9 ≥ 0.5 case | 10–90 width |
|---|---|---|---|---|
| L3 | .0049 | .146 | 12.7% | .146 |
| L4 | .0054 | **.272** | **26.2%** | **.272** |
| L3+C3 | .0051 | .166 | 14.1% | .166 |
| L4+C3 | .0052 | .263 | 23.5% | .263 |

- The median does not move. **L4 roughly doubles the upper tail on zero rows in every year** (q0.9 ≥ 0.5 case: 2020 .13→.26, 2022 .08→.22, 2023 .15→.28, 2024 .16→.29).
- On positive rows, L4 also lifts the upper tail (80% coverage on non-zero rows .56 → .63), and that helps.
- Because 97% of Taiwan rows are zero and WIS(L3) is only 0.0245, the tail inflation dominates.

**Mechanism.** The trees learned in BR/CO/PE that "dense, hot, urban-looking" embeddings mean hyper-endemic units, where non-zero weeks are the norm. Taiwan's districts look most like those units but have near-zero local transmission (imports are excluded from the data). So L4 assigns them an endemic-level upper tail.

C3 does not offset this. C3 columns are permuted within each training country, so the model learns to rely on them far less than on the real `ae_` columns. L3+C3's tail rises only .146 → .166. This also explains why G_id is small while G_emb is large.

**Magnitude in context.**
- Absolute G_excess is −0.0028 log-WIS. That is about 2.3× BR_S5 (−0.0012), not 20× the other cells.
- The −11.5% is mostly a denominator effect: WIS_ref = 0.0245 versus 0.12–0.24 elsewhere.
- **Recommendation for the writers:** report the absolute value next to the percentage, and the zero/positive split. On positive rows the sign is the opposite (+1.7%).
- Phrase the finding as "embeddings transfer location-type priors across countries; under strong covariate shift into a low-transmission country, they inflate upper quantiles". That is a legitimate, interesting result. It is not a pipeline error.

## 5. PE_S5 +1.0%: robustness

**Per year** (G_excess % of WIS(L3)):

| year | % | p |
|---|---|---|
| 2020 | +1.06 | .44 |
| 2021 | +1.45 | .10 |
| 2022 | +1.35 | .03 |
| 2023 | +0.38 | .71 |

**Horizon.** It is driven by h4 (+1.40%, p = .047). At h1 it is +0.38% (p = .07).

**Units.**
- 54 units are positive and 61 negative. The positive sum is +183 and the negative sum is −67, giving a net of +116.
- The **top 10 units (all Amazonian/selva)** account for 76% of the net: Tocache, Oxapampa, Bagua, Leoncio Prado, Padre Abad, Rioja, Ucayali, Atalaya, Condorcanqui and Alto Amazonas.
- Dropping the top 5 leaves +0.0014 per row, about 0.6%. Dropping the top 10 leaves +0.0006, about 0.26%.
- The big **coastal outbreak units are all negative**: Piura, Ica, Lima, Chiclayo, Tumbes, Sullana and Morropón.

**2023 outbreak.** G_excess was negative during Feb–Jun 2023 (−0.0020 per row over 4,830 rows); the rest of the period was +0.0029.

**Rows.**
- Positive rows: +0.0073.
- Zero rows: −0.0014. This is the same upper-tail inflation as in Taiwan, but here 44% of rows are positive.

**Plausible reading.** AE carries useful transfer for Peruvian Amazon units, which resemble Brazilian and Colombian Amazon units in training (NN cosine up to 0.96). It does not help the coastal desert units, which have no analogue in training. That is geographically sensible, but it rests on about 10 units.

**Multiplicity.** p = .046 → Holm over the 11 available cells = **0.232** (T1 `Holm_p_available`). With all 14 cells it is at least 0.37 (rank 7 of 14, ×8). Bonferroni-14 = 0.65. **It does not survive.**

Other points:
- The lower 95% CI limit is +0.02%. TOST is not equivalent (p = .51) and the MDE is 1.39%, so the cell is effectively inconclusive.
- **"Superior" here partly reflects C3 hurting L3** (G_id = −0.45%, p = .014). G_excess is larger than G_emb, which itself is not significant.
- Single seed. Seed SD in other cells is about 0.0001–0.0005, small next to 0.0024, but untested here.

## 6. Minor findings (not affecting the numbers)

1. `src/pop/eval/estimands.py:76`: when G_emb is strongly *negative* (TW_S5, −15%), ID_share is reported as "not estimable: G_emb < 1% of WIS(L3)". The rule is correct, but the message is misleading. Suggested wording: "G_emb not ≥ +1% of WIS(L3)".
2. PE_S5 has 48,070 scored rows versus 48,054 in T1/T2. The difference is the primary incomplete-week exclusion (2 department-weeks), as expected.
3. Colombia has no AE 2022 (CO data ends in 2022; the AE years extracted are 2017–21 and 2023). This is correct by design. For Taiwan's 2023 test year, it means the nearest neighbours come from BR/PE rather than CO.
4. TW_S5 C\* was chosen at a 2019 origin with WIS 0.0066 (C3 and C4 tied; best by score was C4). That selection is noise-level for Taiwan, as noted before for TW S1. It does not drive the result, because G_emb (no control) is even larger than G_excess.

## 7. Suggested handling in the paper

- **TW_S5:** keep it, labelled as a covariate-shift failure. Report it as −0.0028 absolute (−11.5%). Add the zero/positive decomposition and the NN-cosine/endemicity evidence. Optionally add a sensitivity check that scores positive rows only, or that rescales WIS by country-level zero share. Do not average it naively with the other cells as a "typical" effect size.
- **PE_S5:** report it as "nominally positive (p = .046), not significant after Holm (p_adj ≥ .23), concentrated in ~10 Amazonian units, negative in the 2023 coastal outbreak". Do not cite it as evidence that the embeddings help.
