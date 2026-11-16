# Paper 1 ("Place or Placeholder?"): response to the implementation review

**Date:** 2026-11-15 · **From:** the AI that drafted the Paper 1 and Paper 2 plans · **To:** the implementation side and the team
**Responds to:** "Paper 1 — concerns from the implementation review" (23 points, 6 questions)

**Status tags used below:**

| Tag | Meaning |
| --- | --- |
| **[re-verified]** | I re-checked it today against the source (web page, or the OpenDengue file itself) |
| **[reviewer]** | I accept your verification but did not re-check it myself |
| **[decision]** | A protocol choice I am proposing to freeze on Jan 15 |
| **[my error]** | The plan was wrong or overstated |

---

## 0. Summary: what changes

The review is right on almost every point. One point is mistaken: Brittain et al. does exist on medRxiv. Re-tallying OpenDengue also turned up a bigger problem the review did not catch: **missing zeros**. The headline changes are:

1. **Brittain et al. exists** (medRxiv, posted 2026-11-06, DOI prefix `10.64898`). My description of its design was partly unverified, and the plan's wording has to change (§2, Q2).
2. **OpenDengue drops zero-case weeks.** Brazil 2013–2021 records explicit zeros. Brazil 2022–2024, Colombia, Peru and Taiwan contain *no zero rows at all*. The unit counts (5,517 / 1,071 / 115 / 287) are units that **ever reported a case**, which is why they match no administrative count. A zero-filling rule is now a required, frozen step (§1).
3. **Taiwan's 287 units carry only 2 GAUL codes.** The GAUL join is unusable for Taiwan; use name matching. Brazil should join on `IBGE_code`, not GAUL (§1, #10).
4. **I missed Pradhan (NeurIPS 2026).** Novelty is reframed: not "first test that does all three", but the multi-country, time-aligned, transfer-tested version of a result Pradhan saw in one city (§2, Q3).
5. **Training protocol:** rolling-origin annual refits, with every ladder level fit on the same 2018+ row window (§2, Q1).
6. **Scoring:** primary WIS on the **log(1+cases) scale**, using the **9-decile set** that every model can produce. 23-quantile WIS becomes secondary (§2, Q4).
7. **Primary estimand changes** from the ID-share ratio to a difference: *excess gain = WIS(L3 + best location control) − WIS(L4 + best location control)*. ID share is reported only when the embedding gain's CI excludes 0 (§2, Q5).
8. **Controls for unseen units** and an **outbreak floor** are defined (§2, Q6).

---

## 1. New data facts from re-tallying OpenDengue V1.3.1 [re-verified]

**Method:** I downloaded `Spatial_extract_V1_3_1.zip` (CSV, 502 MB) from the repo's `data/releases/V1.3.1` folder in a browser and parsed it there. A *unit* is a distinct `full_name` with `S_res = Admin2` and `T_res = Week`. These are the same definitions behind the plan's numbers, so the counts reproduce exactly.

### 1a. Unit counts and what they actually are

| Country | Weekly Admin2 units | Distinct GAUL codes | What Admin2 means here | Real admin total | Weekly years |
| --- | --- | --- | --- | --- | --- |
| Brazil | 5,517 | 5,456 | Municipality (also has `IBGE_code`: 5,517 distinct, 0 missing) | ~5,570 | 2013–2024 |
| Colombia | 1,071 | 1,012 | Municipality | ~1,120 | 2006–2022 |
| Peru | 115 | 113 | **Province** (e.g., Loreto / Maynas, Loreto / Alto Amazonas) | 196 provinces | 2000–2023 |
| Taiwan | 287 | **2** (13276, 13277) | Township / district (e.g., Kaohsiung City / Lingya Dist.) | ~368 | 1997–2024 |

**Answer to #9:** the counts are right as counts of units that *ever appear* in the weekly file. They are not administrative totals. The gaps (Peru 115 of 196, Taiwan 287 of ~368) are units that never reported a case, because zero weeks are omitted (§1b).

### 1b. Zero weeks are missing, inconsistently

| Country | Weekly rows | Rows with 0 cases | Median weeks per unit-year present | Case definition |
| --- | --- | --- | --- | --- |
| Brazil | 1,895,538 | 1,196,480 (63%) | 52 | Probable |
| Colombia | 199,458 | **0** | 9 | Total |
| Peru | 30,685 | **0** | 17 | Probable and confirmed |
| Taiwan | 7,673 | **0** | 2 | Total |

In Brazil, the share of zero rows is 68–82% each year in 2013–2021 and **0% in 2022, 2023 and 2024**. **The format changes inside the test period.** Without a fix, the model would see Brazil's districts suddenly stop having quiet weeks in 2022.

**Units present per year** (each year's count of units with at least one weekly row):

- Brazil: 3,690 (2013) up to 5,214 (2024). Explicit zeros exist, but whole unit-years are still absent.
- Colombia: 714–897 per year since 2010.
- Peru: 48 (2010) up to 94 (2023). Reporting is expanding.
- Taiwan: 4–63 in normal years; 137 (2014), 234 (2015), 216 (2023). These are the outbreak years.

**[decision] Zero-fill rule, frozen Jan 15:**

1. Define each country's *unit universe*: every Admin2 unit that ever appears in its weekly file. Units that never appear are excluded and listed in the appendix.
2. For every unit in the universe, set every week in that country's weekly coverage period without a row to **0 cases**.
3. **Validation, done in December:**
   - Brazil: compare zero-filled OpenDengue against the InfoDengue API (`casos`) for 50 random municipalities in 2022–2024, and for 50 municipality-years that are absent in 2013–2021.
   - All countries: compare the weekly sum of zero-filled Admin2 against OpenDengue's national weekly series (National/Temporal extracts). A large gap in a week means real missingness, not zeros. Flag those weeks and exclude them from scoring.
4. Sensitivity analysis: score on unit-weeks that were actually reported only.

**Consequences:**

- **Taiwan is extremely sparse** (median 2 non-zero weeks per unit-year). Taiwan WIS will be dominated by zeros plus three outbreaks. This supports #21; see §3.
- **Peru is province-level with 115 units.** It is too small and coarse for within-country spatial splits. Use it for S5 (cross-country) and S1 only.
- **Case definitions differ by country.** Cross-country transfer must be scored on log incidence per 100,000, with per-country scaling, not raw counts.

---

## 2. Answers to the six priority questions

### Q1. Train/validation/test protocol, given L4 starts in 2018 (#8) [decision]

You are right: as written, L4 had no training rows outside the tuning years. This is the protocol.

**Rolling-origin annual refits.** Test origin years are Y ∈ {2020, …, last year} (Brazil 2024, Colombia 2022, Peru 2023, Taiwan 2024).

| Element | Rule |
| --- | --- |
| Training rows (all ladder levels L0–L5) | Target weeks in years 2018 to Y−1. **The same row window for every level**, so the embedding gain is not confounded by window length. |
| Lag features | May use history back to 2013 (or the country's first weekly year). |
| Embedding for a row in year y | AlphaEarth year y−1, so 2018 rows use 2017 embeddings. |
| Hyperparameter tuning | Once, on the 2019 origin (train on 2018 rows, validate on 2019). Frozen for all test origins. Same tuning budget per level. |
| Forecasts | Every week of year Y; horizons 1–4 weeks; issued from data available that week. |
| Refit frequency | Once per origin year. Weekly refits are not needed for LightGBM. |

**Secondary analysis:** L0–L3 trained on a long window (2013 to Y−1), to show what the short window costs. It is reported, not used for the embedding comparison.

**Caveat to state in the paper:** embeddings are annual, so each unit contributes only 2–6 distinct embedding values across the test origins. The embedding can only explain differences *between* units and slow change *across* years, never within-season timing. That is the hypothesis, not a flaw, but it should be said.

**Spatial splits on top of rolling origins:**

- S2–S4: the training rows above, restricted to training units.
- S5: training rows from the other countries.
- Held-out units still receive **their own lagged cases as inputs** at forecast time. "Cold start" means the model never trained on that unit's rows, not that the unit has no history.
- An optional strict cold-start variant drops own-unit lags. It is not primary.

### Q2. Where the Brittain description and the unit counts came from (#4, #9)

**Brittain:** I read the medRxiv full-text page in the earlier session and re-fetched it today [re-verified].

- Title: *Foundation models capture human and environmental context to improve dengue forecasting*.
- Authors: J.-S. Brittain … M.U.G. Kraemer; 24 authors from Oxford, Fiocruz, FGV, Google Research and others.
- Posted **2026-11-06**, DOI **10.64898/2026.11.05.26367335**. The new medRxiv DOI prefix is probably why a search under `10.1101` failed. The Zenodo record and the `kraemer-lab/pdfm-dengue-brazil` code fit an initial submission on Nov 5.
- Design:
  - Brazil, 5,570 municipalities, **monthly** cases from InfoDengue.
  - Backtest Jan 2020–Aug 2025; horizons 1, 3, 6 and 12 months.
  - Five model families, including TimesFM, N-BEATS and XGBoost.
  - PDFM used as a **post-hoc residual adjustment**; WIS with Diebold–Mariano tests.
- Effect: improved mean WIS in **19 of 20** model-horizon combinations. The largest gain was N-BEATS at 6 months, ΔWIS 1.13 (95% CI 0.84–1.48).
- **[my error]:** the plan said Brittain "used one embedding snapshot from October 2023" and "did not compare with a district ID or test unseen districts". The page I read does not state the PDFM snapshot date. Controls and unseen-region tests are not mentioned on that page, which is not the same as absent. **Implementation side: please check the methods and supplement in the full text** and record what they say.

**Unit counts:** from my tally of the Spatial extract (method in §1). They reproduce exactly. §1 explains why they differ from administrative counts.

### Q3. Pradhan (NeurIPS 2026) and novelty framing (#6)

**No, I missed it [my error].** Facts [re-verified]:

- Raunaq Pradhan, single author.
- Poster at the NeurIPS 2026 GlobalSouthAI affinity event; full paper on OpenReview (`2M8rnwfdj7`).
- One large Indian metropolitan authority. Two evaluations:
  1. **Forecasting:** adding embedding features to statistical and ML forecasters left error metrics *largely unchanged* across four horizons.
  2. **Small-area grid:** embeddings were indistinguishable from five open map layers or a satellite embedding on 11 small-area targets. **The 0.001 difference belongs to this second evaluation**, after the open layers got each cell's coordinates. It is not a forecasting gain.
- The author frames these as failures to detect a difference, and blames the **small number of independent spatial units** at city scale.

**Positioning.** Pradhan is the closest precedent and helps us. It shows the coordinate-control effect in one city and names its own limit (too few independent units). Paper 1 tests the same question:

- across 4 countries and about 7,000 units, about 200× more independent units
- with embeddings time-aligned to the year before each forecast
- under spatial and cross-country transfer
- with a quantified estimand (excess gain, ID share), not a single comparison

**Revised novelty sentence:**

> Two recent dengue studies report forecast gains from place embeddings without location-only controls or unseen-region tests (Brittain et al.; the Mexico analysis in Muslim et al.). A city-scale study found the advantage disappears once coordinates are added, but had few independent units (Pradhan). We provide the first multi-country test, with time-aligned embeddings, location-only controls and spatial and cross-country transfer.

Also cite arXiv:2605.01650 (Zhang et al., Southampton): PDFM gains for population estimation are uneven and break down under spatial-scale mismatch [re-verified].

**Scoop risk:** I agree, low to medium. The Oxford/Google groups could add controls fast. The defence is speed: a Brazil-only S1–S4 preprint by mid-March, as already planned.

### Q4. WIS quantile set and scale (#15, #16) [decision]

TimesFM 2.5 (`google/timesfm-2.5-200m-pytorch`) returns the mean plus the 0.1–0.9 deciles by default [re-verified in the docs]. The optional continuous quantile head *may* allow other quantile levels. The implementation side should test that, but we will not depend on it.

| Choice | Decision |
| --- | --- |
| **Primary quantile set** | Median plus the 0.1–0.9 deciles, which form the 20/40/60/80% central intervals. Every model is scored on this set (your option a). |
| Secondary | 23-quantile WIS for models that produce it natively (LightGBM, negative binomial) and for the TimesFM hybrid, where the LightGBM residual stage outputs all 23 (your option b). No tail extrapolation (option c is rejected). |
| Coverage | 40% and 80% intervals on the primary set; 50% and 90% on the secondary set. |
| **Primary scale** | **log(1 + cases)**, following Bosse et al. 2023 (*PLOS Comput Biol*) for epidemic forecasts. This stops the largest cities dominating. |
| Secondary scales | Case scale, and incidence per 100,000. |
| Aggregation | Mean over unit-weeks within each split × horizon. Also report the share of units improved and the median per-unit difference, since Muslim's median municipality got slightly worse. |

### Q5. ID-share reporting rule (#17) [decision]

A ratio with a near-zero denominator is unusable as a primary result. With C* as the **best location-only control**, chosen on the 2019 tuning origin and not on test data, define three differences:

```
G_emb    = WIS(L3)      − WIS(L4)        embedding gain
G_id     = WIS(L3)      − WIS(L3 + C*)   location-control gain
G_excess = WIS(L3 + C*) − WIS(L4 + C*)   what embeddings add beyond location
```

- **Primary estimand: G_excess**, with a 95% block-bootstrap CI and a DM test. It answers the paper's question directly and stays stable near zero.
- Report G_emb and G_id with CIs.
- **ID share = G_id / G_emb**, reported only when G_emb's 95% CI excludes 0 and G_emb is at least 1% of WIS(L3). The CI comes from the bootstrap distribution of the ratio. Otherwise it is reported as "not estimable (no embedding gain)".

### Q6. Controls for unseen units, and the outbreak floor (#18, #19) [decision]

| Control | S1 (seen units) | S2–S4 (unseen units, same country) | S5 (unseen country) |
| --- | --- | --- | --- |
| C1 target encoding | Own-unit mean log incidence, from training rows only | **kNN encoding:** distance-weighted mean of the 5 nearest training units (still location-only) | kNN unavailable across borders, so **C1 is dropped**; C2 and C4 carry the comparison |
| C2 coordinates + spherical harmonics | Defined everywhere | Defined | Defined |
| C3 shuffled embeddings | Embeddings permuted across units within country-year; 10 fixed seeds | Held-out units get a training unit's embedding drawn at random; 10 seeds | Embeddings permuted within the target country; 10 seeds |
| C4 random smooth fields | 64 Gaussian random fields per country, range matched to the AlphaEarth variogram, evaluated at unit centroids; 10 draws | Defined everywhere | Defined everywhere |
| C5 static embedding | AlphaEarth 2023 for all years (mirrors the PDFM snapshot timing) | Same | Same |

All target encodings use training rows only, refit at each origin.

**Outbreak definition** (computed after zero-filling):

- A week is an outbreak week if cases ≥ max(the unit's baseline 90th percentile, **5 cases**).
- Baseline: 2013–2019, or the country's available pre-2020 weekly years.
- Units with no outbreak weeks in the test period count toward false alarms only, not sensitivity.
- Sensitivity check: the PAHO-style endemic channel (baseline mean + 2 SD), with the same 5-case floor.

---

## 3. Point-by-point (all 23)

| # | Verdict | Resolution |
| --- | --- | --- |
| 1 Muslim scope | **Agree** [reviewer] | Restrict claims to "the Mexico dengue analysis". Note that Muslim uses shuffled-embedding controls and unseen-state tests in other case studies. That supports our design, so cite it. Note the Oct-2025 snapshot check. |
| 2 Same model stack as Muslim | **Agree** | Novelty rests on time alignment, location controls, G_excess/ID share, transfer and multi-country scale (Q3). Reusing their stack is a plus: our S1 + L5 + monthly arm is a **replication anchor**. |
| 3 Tiny gain; monthly vs weekly | **Agree** [reviewer] | Add a **monthly arm**: aggregate weeks to months; horizons 1 and 3 months; Brazil, S1, L3/L4/L5. That gives a direct comparison with Brittain and Muslim at low cost. The literature is mixed: Muslim's gain is tiny, Brittain's is larger. That is itself motivation. |
| 4 Brittain not found | **Disagree on existence; agree the description was overstated** | §2 Q2. Fix the plan's wording; check the full-text methods. |
| 5 Nazir partly static | **Agree** [reviewer] | Say "the malaria analysis uses a static snapshot". Cite a specific arXiv version, since numbers differ between versions. |
| 6 Pradhan missing | **Agree** [re-verified] | §2 Q3. Add Zhang et al. (2605.01650). |
| 7 AlphaEarth 2017–2025 | **Agree** | No action. |
| 8 L4 training rows | **Agree** | §2 Q1. |
| 9 Unit counts | **Counts confirmed; meaning corrected** [re-verified] | §1. Re-tally on your side is still welcome; it should match exactly. |
| 10 GAUL join | **Agree, and worse than stated** [re-verified] | Brazil: join on `IBGE_code` to IBGE 2022 municipal boundaries. Colombia: 1,071 units share 1,012 GAUL codes, so name-match to geoBoundaries/GADM ADM2 with a manual fix list. Peru: name-match provinces (ADM2). Taiwan: 2 GAUL codes, so name-match county + township to Taiwan's official township boundaries or GADM (check which level holds townships). Report join rate by units and by cases; target ≥ 98% of cases. |
| 11 PDFM 17 countries | **Agree** [re-verified] | L5 is Brazil-only. Note: Google's commercial Population Dynamics Insights (built on PDFM) is **updated monthly** across 17 countries at S2 level-12 cells. A time-aligned PDFM therefore exists, but it is paid and out of scope; mention it as a limitation and future work. |
| 12 WorldPop break | **Agree** | Use **GHSL GHS-POP** for all population weights, interpolated linearly between its 2015, 2020 and 2025 epochs. WorldPop only in a sensitivity check. |
| 13 Earth Engine cost | **Agree** | Reduce at 100 m with population-weighted `reduceRegions`. Time 100 municipalities first. Tile the large Amazon municipalities. Export per state. Also: AlphaEarth vectors are designed to be unit-length (verify), so a mean shrinks toward the origin; **renormalise district means to unit length**, with the unnormalised version as a sensitivity check. |
| 14 CC BY-SA | **Agree** | Derived district-week tables released under CC BY-SA 4.0; code under MIT. Credit AlphaEarth under its licence (check the catalog terms). |
| 15 TimesFM quantiles | **Agree** [re-verified] | §2 Q4. |
| 16 WIS scale | **Agree** | Log scale primary (§2 Q4). |
| 17 ID share unstable | **Agree** | G_excess primary; ID share conditional (§2 Q5). |
| 18 Controls undefined | **Agree** | §2 Q6 table. |
| 19 Outbreak threshold | **Agree** | 5-case floor; endemic-channel sensitivity (§2 Q6). |
| 20 What DM tests | **Clarify** [decision] | Per split × horizon: average the WIS difference across units for each forecast week, giving one weekly series, then run DM with Newey–West (HAC) variance, lag ≥ h−1, plus Harvey's correction. Averaging first handles spatial dependence in the test statistic. Unit-level uncertainty comes from the block bootstrap, resampling state clusters × 8-week blocks. |
| 21 Taiwan dynamics | **Agree, and the data confirm it** [re-verified] | Units per year jump to 137 (2014), 234 (2015) and 216 (2023). Report Taiwan per outbreak: 2014 Kaohsiung, 2015 Tainan/Kaohsiung, 2023 Tainan, and non-outbreak years. Also score at county level (22 units). Treat Taiwan as a stress test, not the headline. Note that OpenDengue's "Total" may include imported cases. |
| 22 Shared server storage | **Agree** | The SSD becomes **required before Jan 4** (Paper 2 imagery start). Paper 1 (< 50 GB) can use `/net/home` meanwhile. |
| 23 Earth Engine project | **Noted** | Use a dedicated Cloud project for this paper; record its ID in the repo config. |

---

## 4. Additions to the frozen protocol (Jan 15)

The Jan 15 freeze document should include, in addition to the original plan:

1. The zero-fill rule plus its validation results (§1b).
2. Join keys per country and achieved join rates (#10).
3. The rolling-origin training windows (Q1).
4. The quantile set, scoring scale and aggregation (Q4).
5. The estimands G_excess, G_emb and G_id, and the ID-share condition (Q5).
6. Control definitions per split, and how C* is selected (Q6).
7. The outbreak definition and floor (Q6).
8. The DM and bootstrap specification (#20).
9. The monthly replication arm (#3).
10. GHSL population weights and embedding renormalisation (#12, #13).
11. The Taiwan per-outbreak reporting plan (#21).

**Timeline impact:** add a **data audit, Dec 1–19** (zero-fill validation and join rates) inside the existing Dec 1–Jan 15 data build. The Jan 15 freeze and the Apr 30 submission hold.

## 5. Changes needed in the two plan docs

**Paper 1 doc:**

- Summary "Why now": rewrite with the scoped claims and the Q3 novelty sentence; add Pradhan and Zhang. Remove "both used one Oct-2023 snapshot".
- Data: re-label the unit table "units that ever reported a case". Mark Peru as provinces; note Taiwan's GAUL problem and the zero-fill rule; switch population weights to GHSL.
- Study design: rolling-origin protocol, decile WIS on the log scale, G_excess, the controls table, the outbreak floor, the DM specification, the monthly arm.
- Risks: add "missing zeros / format break in 2022" and "join failures".

**Paper 2 doc:**

- Unit counts as above.
- Stage A target uses zero-filled annual incidence.
- Taiwan joined by name.
- Peru province-level (fewer, larger chip sets).
- SSD required.
- Same WIS scale and quantile set as Paper 1.

## 6. Still unverified (owner: implementation side)

- Brittain full-text methods: PDFM snapshot date, any controls, any spatial holdout.
- Muslim v2 details (I could not open the PDF today because of rate limits): the dengue ΔWIS values, and the controls used in the other case studies.
- Nazir: which analyses are static, and the version differences.
- Whether TimesFM 2.5's continuous quantile head returns arbitrary quantile levels (e.g., 0.025, 0.975).
- AlphaEarth unit-length vectors and the dataset licence.
- Which Taiwan boundary source holds all 287 townships under matching names.

## Sources

- [Brittain et al., medRxiv 2026, DOI 10.64898/2026.11.05.26367335](https://www.medrxiv.org/content/10.64898/2026.11.05.26367335v1.full)
- [Pradhan, "Benchmarks Are Not Deployments", NeurIPS 2026 GlobalSouthAI](https://neurips.cc/virtual/2026/162773)
- [Muslim et al., arXiv:2610.05699](https://arxiv.org/abs/2610.05699)
- [Google Research blog on PDFM public-health case studies (Oct 6, 2026)](https://research.google/blog/earth-ais-planetary-geospatial-foundation-models-for-global-public-health/)
- [Population Dynamics Insights announcement (17 countries, monthly updates, S2 level-12)](https://mapsplatform.google.com/intl/fr_fr/resources/blog/from-static-maps-to-geospatial-ai-announcing-population-dynamics-insights/)
- [Zhang et al., arXiv:2605.01650 (PDFM, population estimation)](https://www.emergentmind.com/papers/2605.01650)
- [TimesFM repository (2.5 quantile head)](https://github.com/google-research/timesfm)
- [TimesFM 2.5 in Hugging Face Transformers (default quantiles 0.1–0.9)](https://huggingface.co/docs/transformers/model_doc/timesfm2_5)
- OpenDengue V1.3.1 Spatial extract: `github.com/OpenDengue/master-repo/data/releases/V1.3.1/Spatial_extract_V1_3_1.zip` (tallied directly)
- Bosse N.I. et al., "Scoring epidemiological forecasts on transformed scales", *PLOS Computational Biology* 2023, 19(8): e1011393 (from memory; confirm the citation)
