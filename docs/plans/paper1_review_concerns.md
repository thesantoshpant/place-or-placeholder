# Paper 1 ("Place or Placeholder?") — concerns from the implementation review

**Date:** 2026-11-15 · **For:** the AI that helped draft the Paper 1 and Paper 2 plans · **From:** the implementation side

**What we checked:** both plans line by line; a literature and scoop scan; data and tool documentation; the team GPU server; Earth Engine access. Items marked *[verified]* were confirmed against the source. *[review]* items are our own methodological reading.

**What we need from you:** for each point, tell us whether the plan already covers it (and where), or how you'd resolve it. The questions at the end matter most.

---

## A. Literature and framing

1. **Muslim et al. is characterized too broadly** *[verified]*. arXiv:2610.05699, "Planetary Geospatial Foundation Models: A New Paradigm for Global Public Health". It has 38 authors, John Brittain among them; v1 was posted 2026-10-05 and v2 on 2026-10-17. Mexico dengue (about 2,457 municipalities, 2020–2025) is one of five case studies.
   - Its main analysis uses the Oct-2023 PDFM snapshot, but it also runs an Oct-2025 snapshot check.
   - The dengue study has no location-only control and no unseen-region test. However, the same paper uses shuffled/random-embedding controls and unseen-state tests in its other case studies.
   - So "neither compared with a district ID / neither tested unseen districts" must be scoped to the dengue analyses.
2. **Muslim's model stack is the same as ours** *[verified]*: TimesFM plus a PDFM residual model, scored with WIS, Diebold–Mariano and block bootstrap. Our novelty therefore cannot rest on the model or the scoring. It has to rest on time alignment, location-only controls, the ID-share metric and spatial/country transfer.
3. **The gain being tested is tiny** *[verified]*. Muslim's 1-month ΔWIS is −0.0051, the median municipality gets slightly worse, and the 3- and 6-month gains are not significant. Their horizons are also monthly, while ours are weekly (1–4 weeks), so results are not directly comparable.
4. **We could not find Brittain et al. on medRxiv.** We found only code (github.com/kraemer-lab/pdfm-dengue-brazil) and a Zenodo record dated 2026-11-05 labelled "Initial manuscript submission" (10.5281/zenodo.23984558). We could not check its design, snapshot, controls or effect size. → **Where did the plan's description of Brittain come from?**
5. **Nazir et al. is only partly static** *[verified]*. arXiv:2605.10949 (Nazir, Cheng, Khalid). Its respiratory-infection analysis is aligned to the survey year; only the malaria analysis uses a static snapshot. Its reported numbers also differ between arXiv versions. "Same gaps" needs scoping.
6. **A close precedent is missing from the plan** *[verified]*. Pradhan, "Benchmarks Are Not Deployments: Geospatial Foundation Models in a City-Scale Dengue Early-Warning System" (NeurIPS 2026, GlobalSouthAI affinity poster). In one Indian city, a satellite-embedding advantage "fell to 0.001 once the open layers were given the cell's own coordinates". That is our core hypothesis at city scale. We must cite it and position against it: multi-country, time-aligned, transfer, ID share.
   - Related: arXiv:2605.01650 finds PDFM gains shrink under geographically structured validation (population estimation, not disease).
   - **Overall scoop risk: low–medium.** Nothing combines all three of our tests for dengue, but the Oxford/Google groups have the code to add controls quickly.

## B. Data

7. **AlphaEarth years: resolved, no action needed** *[verified]*. A direct Earth Engine query of `GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL` returns years 2017–2025, so the plan's range and the year-t−1 design (first forecast year 2018) hold.
8. **L4 has no training rows outside the tuning years** *[review]*. Year t−1 embeddings exist only for forecast years from 2018. The plan says 2018–2019 is tuning only and 2020+ is test. So it is unclear what L4 is trained on in S1.
   - If L0–L3 are trained on 2013–2019 and L4 on 2018+, the embedding gain mixes in a training-window effect.
   - **We need an explicit protocol.** We suggest rolling-origin annual refits (to forecast year Y, train on all data up to Y−1), with every ladder level fit on the same row window. Lag features can still draw on history from 2013.
9. **Unit counts** *[superseded by B2.1, where all four counts are confirmed]*. OpenDengue V1.3.1 exists (GitHub `data/releases/V1.3.1`, CC BY-SA). We could not confirm the plan's 5,517 / 1,071 / 115 / 287 units or its year ranges from the documentation.
   - Taiwan's 287 matches neither its 22 counties nor its ~368 townships.
   - Peru's 115 doesn't match its 25 regions, 196 provinces or ~1,890 districts.
   - Weekly coverage for Brazil after 2021 and for Peru is unconfirmed.
   - **Where do these counts come from?** We will re-tally them from the Spatial extract.
10. **The GAUL join may fail, especially for Taiwan** *[verified]*. OpenDengue does not document which GAUL version it uses. `FAO/GAUL/2015/level2` is deprecated in Earth Engine and licensed non-commercial. Its replacement, `FAO/GAUL/2025/level2`, may not share 2015 codes. Taiwan is often coded under China in GAUL. We need to measure join rates per country, with geoBoundaries/GADM as a fallback.
11. **PDFM covers 17 countries, including Brazil but not Colombia, Peru or Taiwan** *[verified]*. So L5 is Brazil-only.
12. **WorldPop has a product break** *[verified]*. The classic EE collection ends in 2020, so 2021–2024 needs `WorldPop/GP/100m/R2025A/v1/pop`, which uses a different method and may create a step change in the population weights. Consider using GHSL population (or a single WorldPop product) for consistency.
13. **Earth Engine cost** *[verified + review]*. The Community tier allows 150 EECU-hours a month, enforced since 2026-04-27; going over throttles jobs rather than stopping them.
    - Population-weighted means of 64 bands at 10 m over ~7,000 districts × 8 years is heavy. Large Amazon municipalities are the worst case.
    - We plan to reduce at a coarser scale (e.g. 100 m) and to time the cost on 100 municipalities first.
    - Downloading the COGs locally is not an option: Brazil alone is several TB per year, and our free disk is about 1.3 TB, shared with others.
14. **OpenDengue's CC BY-SA licence** means any derived district-week tables we release must be share-alike.

## B2. Measured: OpenDengue V1.3.1 audit (downloaded and independently verified 2026-11-15)

The download is verified: all three zips match GitHub's blob SHAs and figshare v5's MD5s, and every CSV parses cleanly. The data runs to 2025-04-30. Numbers below come from the weekly Admin2 rows of the Temporal extract. **Several of the plan's data assumptions don't hold:**

- **B2.1 The unit counts match exactly, but they mean something different.** Brazil 5,517, Colombia 1,071, Peru 115, Taiwan 287 all match the plan. But each count is the set of units that *ever reported a case*, not the full set of districts. Peru's 115 is out of ~196 provinces; Taiwan's 287 is out of ~368 townships.
- **B2.2 Weeks with zero cases are mostly not recorded.**
  - Colombia, Peru (since 2012) and Taiwan list only weeks with at least one case.
  - Brazil records zero weeks explicitly for 2014–2021, but none from 2022: rows drop from ~196k in 2021 to ~77k in 2022.
  - Even in Brazil's zero-recording years, only 3,551–4,521 of ~5,570 municipalities appear each year, so whole unit-years are absent.
  - **The plan needs an explicit zero-filling rule**, e.g. "absent = 0 within the country's reporting window". We're checking this against independent sources (InfoDengue for Brazil, Taiwan CDC). The risk is that some absent rows are reporting gaps, not true zeros.
- **B2.3 The usable windows differ from the plan:**
  - Brazil: weekly 2014–2024 (2013 has a single week).
  - Colombia: weekly Admin2 ends in 2022.
  - Peru: ends in 2023.
  - Taiwan: runs to 2024, but **2021 is absent** and 2017 has only 7 unit-weeks.
- **B2.4 The Taiwan hold-out (S5) is effectively one outbreak.** Unit-weeks with cases in the 2020+ test period are 32 (2020), 0 (2021), 8 (2022), 1,544 (2023) and 96 (2024). So the S5 Taiwan test mostly scores the 2023 southern outbreak. The very low counts in non-outbreak years suggest local cases only, which we're verifying. Options:
  - aggregate Taiwan to Admin1 or to its southern cities;
  - frame S5 as outbreak-season transfer;
  - add another held-out country with dense weekly district data.
- **B2.5 The plan's fallback countries don't work.** Mexico has weekly data only at Admin1 (32 states), with gaps in 2008–11 and 2014–16. Thailand has no weekly data, only monthly Admin1.
- **B2.6 The data can't be joined on GAUL codes as the plan states.** `FAO_GAUL_code` is not unique: 54 codes are shared by several Brazilian municipalities, 53 in Colombia, and Taiwan's 287 units have only 2 distinct codes. Use `IBGE_code` for Brazil and admin names elsewhere. That means district polygons from another source (IBGE, geoBoundaries/GADM or national) and a name-matching step with a reported match rate.
- **B2.7 Case definitions differ by country:** Brazil probable, Colombia and Taiwan total, Peru probable+confirmed. Cross-country transfer (S5) must handle the level differences, e.g. log incidence or per-district normalization.
- **B2.8 Data quirks (handled in code):** missing values are the literal string `NA`; the case-definition column has `confirmed` vs `Confirmed`; a few India rows contain an embedded line break; `UUID` is the source-document ID, not a row ID.

## C. Methods (to settle before the Jan 15 design freeze)

15. **TimesFM 2.5 only gives quantiles 0.1–0.9** *[verified]*. Model `google/timesfm-2.5-200m-pytorch`, Apache-2.0; TimesFM 3.0 weights are non-commercial. It cannot produce the 23-quantile set (0.01–0.99) directly. Options:
    - (a) score every model's WIS on the common 9 quantiles plus the median;
    - (b) have the LightGBM residual stage output all 23 quantiles;
    - (c) extrapolate the tails.
    Choose one and freeze it.
16. **Which scale is WIS on?** *[review]* The target is log(1+cases) and results are "reported on case scale". Case-scale WIS is dominated by big cities. Do we report log-scale WIS too (as recommended for epidemic forecasts on transformed scales), and which one is primary?
17. **ID share is unstable when the gain is near zero** *[review]*. The ratio's denominator is the embedding gain, so a ~0 gain (as in Muslim) makes ID share blow up or flip sign. We need a reporting rule. For example, report it only when the gain's CI excludes 0, and otherwise report the two WIS differences with bootstrap CIs.
18. **Some controls are undefined in some splits** *[review]*.
    - C1 (target-encoded ID) does not exist for an unseen district in S4 or S5. Fall back to the state mean, or drop C1 there?
    - The C1 encoding must use training rows only.
    - C3 and C4 also need a definition for held-out units.
19. **The outbreak threshold breaks on zero-heavy districts** *[review]*. With mostly-zero history (common in Taiwan, Peru and small municipalities), the 90th percentile is 0, so every week with a case counts as an outbreak. This needs a floor, such as a minimum count or a rate threshold.
20. **What does the DM test actually test?** *[review]* DM assumes one loss-difference time series. Is the test run on the WIS difference averaged over districts per week, or per district with pooling? Spatial dependence between districts needs handling; the moving-block bootstrap covers part of it.
21. **Taiwan's dynamics differ** *[review]*. Its dengue is outbreak-driven (mostly Kaohsiung and Tainan, 2014–15 and 2023) and partly imported, with many zero weeks. That makes S5 Taiwan WIS dominated by one or two outbreaks, so a per-outbreak breakdown is worth adding.

## D. Infrastructure (affects Paper 2 more than Paper 1)

22. **The team server is shared.** It has one RTX A6000 (48 GB), 64 threads, 125 GB RAM and Python 3.12. `/net/home` has **about 1.3 TB free and is 95% full, shared with other users**. The system disk is 99% full. Paper 1 (under 50 GB) fits. Paper 2's 0.25–1 TB of imagery would take most of the shared free space, so the plan's 2–4 TB SSD is a hard requirement, not optional.
23. **Earth Engine access:** Earth Engine works from the team server: existing credentials initialize and queries run. It is currently tied to an older default Cloud project, and we will pass a new project ID explicitly for this paper. No problem here; included for completeness.

---

## Questions for you (priority order)
1. What is the train/validation/test protocol per split, given that L4 only exists from 2018 (#8)? Also given the real windows: Brazil 2014–24, Colombia to 2022, Peru to 2023 (B2.3).
2. Do you accept the zero-filling rule (B2.2)? How should S5/Taiwan be redesigned, given it is essentially the 2023 outbreak (B2.4)? Should a different held-out country replace it?
3. Joining on GAUL isn't viable (B2.6). Is IBGE + name-matched polygons acceptable?
4. Where did the Brittain description come from (#4)?
5. Were you aware of Pradhan (NeurIPS 2026)? How should novelty be framed against it (#6)?
6. Which WIS quantile set and which scale (#15, #16)?
7. What is the ID-share reporting rule when the gain is near zero (#17)?
8. How should controls work for unseen units, and what is the outbreak floor (#18, #19)?
