# Literature notes: Paper 1 "Place or Placeholder?"

Compiled 2026-11-15 from web research only. Items marked **UNVERIFIED** could not be confirmed from a primary source.

## 1. The three target papers

### 1a. Muslim et al. 2026 (arXiv) — VERIFIED
- **Title:** "Planetary Geospatial Foundation Models: A New Paradigm for Global Public Health". arXiv:2610.05699 (cs.LG). https://arxiv.org/abs/2610.05699 (HTML: https://arxiv.org/html/2610.05699v2)
- **Authors:** Arbaaz Muslim, Aviv Slobodkin, ..., John Brittain, ..., Moritz U. G. Kraemer, ..., Gautam Prasad (38 authors; Google Research, Oxford, Tec de Monterrey, NYU and others).
- **Posted:** v1 2026-10-05; v2 2026-10-17. Google blog post, 2026-10-06: https://research.google/blog/earth-ais-planetary-geospatial-foundation-models-for-global-public-health/
- **Scope:** an umbrella paper with five PDFM case studies: US–Canada MMR vaccination, US CVD nowcasting, **Mexico municipal dengue (Case Study 3)**, DRC cholera hotspots, and US postpartum depression.
- **Dengue data:** Mexican Ministry of Health surveillance, Jan 2020–Aug 2025 (68 months, monthly), about 2,457 GADM-2 municipalities. This is not OpenDengue.
- **Embedding:** PDFM. "The primary analysis used the static October 2023 snapshot throughout." The paper also reports a sensitivity analysis with an **October 2025 snapshot**, but we could not find its result.
- **Models:** TimesFM 2.0 zero-shot baseline, compared with TimesFM plus PDFM-conditioned residual models (one per horizon and quantile).
- **Split:** 24-month sliding window, which reads as temporal rolling-origin. All municipalities were evaluated, and none was held out.
- **Location-only controls (dengue):** none reported. There is no municipality ID, coordinates or fixed effects, and no shuffled or random embedding in the dengue study. Random and shuffled embedding controls appear only in Case Study 5 (postpartum depression), which is also the only case study that tests on **unseen states**.
- **Gain:** mean ΔWIS at 1 month = −0.0051 (95% block-bootstrap CI −0.0081 to −0.0027; DM p<0.001). Only 47.6% of municipalities improved, and the median municipality change was +0.0013, i.e. slightly worse. At 3 months: +0.0028 (p=0.14). At 6 months: +0.0039 (p=0.074, sensitive to block length). The blog's "up to 72% of active-transmission municipalities improved" is a subset claim.
- **Methodological overlap with us:** they already use TimesFM, a residual-correction model, WIS, Diebold–Mariano and block bootstrap. Our model stack is therefore not novel. Our novelty must come from the controls, time alignment and spatial transfer.

### 1b. Brittain et al. 2026 (Brazil) — PARTLY VERIFIED
- **Manuscript title** (from the code archive): "Foundation models capture human and environmental context to improve dengue forecasting". Authors: Brittain, J.-S., et al. (Kraemer lab, Oxford).
- **Code:** https://github.com/kraemer-lab/pdfm-dengue-brazil and Zenodo https://zenodo.org/records/23984558 (v1.0.0, 2026-11-05, "Initial manuscript submission"). It uses the "Thucia" forecasting framework.
- A ResearchGate listing attached to the wrong title describes a Brazil study comparing **five forecasting architectures with PDFM residual adjustment**. It says the share of forecasts improved by PDFM grew with local case counts, and that TimesFM was stable at longer horizons. This is a secondary source.
- **UNVERIFIED:** the medRxiv posting, DOI/URL and date (the README says "link to be added upon availability"; the medRxiv search page returned 403). Also unverified: the PDFM snapshot date, data years, spatial unit, split, controls and effect size. Brittain also co-authored 1a.

### 1c. Nazir et al. 2026 (arXiv) — VERIFIED
- **Title:** "AlphaEarth Satellite Embeddings for Modelling Climate Sensitive Diseases Towards Global Health Resilience". Authors: Usman Nazir, I-Han Cheng, Sara Khalid (Oxford). arXiv:2605.10949, https://arxiv.org/html/2605.10949. The arXiv header is dated 29 Apr 2026, and some listings show 13 May 2026. Oxford ORA lists it as a CVPR 2026 item. Venue is unconfirmed.
- **Three studies, using AlphaEarth 64-d embeddings:**
  - **Malaria, Nigeria:** NMEP data, 28k locations, 2000–2024. Random forest, temporal holdout (train 2000–2023, test 2024). The embedding is a static per-location "fingerprint" with no stated year.
  - **Childhood ARI:** 11 DHS countries, 2017–2022. The embedding **is time-aligned** to the survey year. 5-fold×2 CV with the split type unstated, and countries are pooled. This is cross-sectional mapping, not forecasting.
  - **Stunting:** 35 DHS countries. The embedding is broadcast at country level and is absorbed by country fixed effects. Gain ≤ +0.02 R².
- **Controls:** no coordinates-only, ID or shuffled-embedding control. There is no unseen-country or region holdout.
- **Gains:** **the reported numbers differ between versions.** The HTML gives malaria R² 0.201→0.245 and ARI 0.157→0.206. The abstract and NeurIPS pages give Nigeria malaria 0.623→0.777, India 0.867→0.881 and ARI 0.098→0.164. Cite the version you read.
- **Related, same group:** "Learned geospatial priors for malaria forecasting" / "AlphaEarth Embeddings Improve Malaria Forecasting in Low-Resource Settings" (NeurIPS 2026, https://neurips.cc/virtual/2026/174475). It combines negative binomial, LSTM/Transformer and AlphaEarth for India and Nigeria with a one-year-ahead holdout. "Improving Childhood Respiratory Infection Risk Mapping with AlphaEarth Embeddings" (https://neurips.cc/virtual/2026/174721).

### Discrepancies vs our plan
1. "Both used one Oct 2023 snapshot for forecasts back to 2020": **true for Muslim (primary analysis)**, but they also ran an Oct 2025 snapshot sensitivity. **Unverified for Brittain.**
2. "Neither compared against district ID/coordinates": **true for the Muslim dengue study.** The same paper does use random and shuffled embedding controls elsewhere (Case 5), so reviewers will expect us to acknowledge that. Unverified for Brittain.
3. "Neither tested on unseen districts": **true for the Muslim dengue study.** But Muslim Case 5 and the CVD and MMR cases do test held-out units, so we should not say "the paper never tests transfer". Unverified for Brittain.
4. "Brittain et al. 2026 (medRxiv)": the medRxiv posting is **unverified**. Cite as "manuscript; code at Zenodo 10.5281/zenodo.23984558" until a DOI appears.
5. "Nazir has the same gaps": **mostly true** (no location controls, no spatial or country holdout). **But the ARI study is time-aligned.** So "static snapshot" applies only to malaria (and stunting is country-broadcast).
6. The Muslim dengue gain is tiny (ΔWIS −0.005, median municipality worse) and only significant at 1 month. Our framing should read "small, horizon-limited gains, not yet shown to beat a location-only control", not "large gains".

## 2. Scoop-risk scan (2025 → Nov 2026)
- **Pradhan, "Benchmarks Are Not Deployments: Geospatial Foundation Models in a City-Scale Dengue Early-Warning System"** (NeurIPS 2026 GlobalSouthAI poster, https://neurips.cc/virtual/2026/162773). One Indian city grid. It reports that a satellite-embedding advantage over open map layers "fell to 0.001 once the open layers were given the cell's own coordinates". This is the **closest conceptual precedent** (embedding ≈ location) and we must cite it. Differences: a single city, no multi-country, no spatial transfer, no time-aligned AlphaEarth, no WIS/DM framework.
- **arXiv:2605.01650**, "Geospatial foundation-model embeddings improve population estimation unevenly across space and scale". PDFM under geographically structured validation, with gains shrinking across scales. Not about disease. https://arxiv.org/abs/2605.01650
- **arXiv:2609.11689**, "Geospatial Foundation Models Capture Health-Relevant Dimensions of Place Beyond Conventional Social Risk Indices". Not forecasting. Not checked in detail.
- **AlphaEarth Foundations paper** (Brown et al. 2025, arXiv:2507.22291) itself reports controls for "purely geographic information". Useful precedent.
- No paper found that combines time-aligned satellite embeddings, location-only controls, spatial or held-out-country validation and dengue/infectious-disease forecasting.
- **Rating: LOW–MEDIUM.** Low for the full design. Medium because (a) Pradhan already makes the "coordinates absorb the embedding gain" point for dengue, and (b) the Oxford/Google groups (Kraemer, Khalid) are active and have the data and code (Thucia) to add these controls in revisions of Brittain/Muslim. Speed matters.

## 3. Methodological anchors
1. Roberts DR et al. 2017, "Cross-validation strategies for data with temporal, spatial, hierarchical, or phylogenetic structure", *Ecography* 40:913–929. Grounds block or spatial CV.
2. Ploton P et al. 2020, "Spatial validation reveals poor predictive performance of large-scale ecological mapping models", *Nature Communications* 11:4540. Random CV inflates skill, and spatial CV reveals it. This parallels our "unseen districts" test.
3. Meyer H & Pebesma E 2021, "Predicting into unknown space? Estimating the area of applicability of spatial prediction models", *Methods Ecol Evol* 12:1620; and 2022, "Machine learning-based global maps of ecological variables and the challenge of assessing them", *Nat Commun* 13:2208. Covers area of applicability and transfer.
4. Klemmer K et al. 2025, "SatCLIP: Global, general-purpose location embeddings with satellite imagery", AAAI 2025 (arXiv:2311.17179); and Rußwurm M et al. 2024, "Geographic location encoding with spherical harmonics and sinusoidal representation networks", ICLR 2024 (arXiv:2310.06743). Source for our lat/lon + spherical-harmonics control. (Citations from prior knowledge; not re-fetched.)
5. Brown CF et al. 2025, "AlphaEarth Foundations: An embedding field model for accurate and efficient global mapping from sparse label data", arXiv:2507.22291. The source for the Satellite Embedding V1 (annual, 2017+), which is what makes time alignment possible.
6. Agarwal M et al. 2024, "General Geospatial Inference with a Population Dynamics Foundation Model", arXiv:2411.07207. The PDFM source.
7. Bracher J, Ray EL, Gneiting T, Reich NG 2021, "Evaluating epidemic forecasts in an interval format", *PLOS Comput Biol* 17:e1008618. Defines WIS (23 quantiles = CDC hub standard).
8. Diebold FX & Mariano RS 1995, *J Bus Econ Stat* 13:253; Harvey D, Leybourne S, Newbold P 1997, "Testing the equality of prediction mean squared errors", *Int J Forecast* 13:281–291. DM test with small-sample correction. Muslim et al. already use DM, so match their setup for comparability.
9. Clarke J et al. 2024, "A global dataset of publicly available dengue case count data", *Scientific Data* 11:296 (OpenDengue). Our data source.
10. Araujo EC et al. 2025, "Leveraging probabilistic forecasts for dengue preparedness and control: the 2024 Dengue Forecasting Sprint in Brazil", medRxiv 10.1101/2025.05.12.25327419 (https://www.medrxiv.org/content/10.1101/2025.05.12.25327419.full.pdf). Mosqlimate/InfoDengue benchmark scored with WIS. Use its baselines and protocol for comparability. (First-author name from prior knowledge; check before citing.)
11. Das A et al. 2024, "A decoder-only foundation model for time-series forecasting", ICML 2024 (TimesFM). **No peer-reviewed WIS evaluation of TimesFM 2.5 on infectious disease was found.** The closest are a TimesFM/Moirai study on HFMD (Frontiers Public Health 2025, 10.3389/fpubh.2025.1634138, non-WIS metrics) and EpiCastBench (arXiv:2605.11598, MASE/RMSE). This gap gives us a small secondary contribution.

## Verification round 2 (2026-11-15)

1. **Brittain et al., medRxiv 10.64898/2026.11.05.26367335. VERIFIED** (https://www.medrxiv.org/content/10.64898/2026.11.05.26367335v1.full). Assets are dated 2026-11-06. 5,570 Brazilian municipalities, monthly cases, horizons of 1/3/6/12 months. SARIMA, XGBoost, TCN and N-BEATS trained Jan 2010–Dec 2019; TimesFM zero-shot. Targets Jan 2020–Aug 2025. WIS on log(1+cases).
   - **PDFM:** one 330-d Oct 2023 snapshot: "a single October 2023 embedding snapshot was used throughout the evaluation period".
   - **Location controls:** none found in a full-text keyword search (shuffle, permutation, placebo, fixed effect, coordinates, one-hot, identifier). The ERA analysis uses the static embeddings to parameterise "municipality-specific climate sensitivities", which is close to ID use.
   - **Spatial hold-out:** none. Hold-outs are temporal only.
   - **Headline:** improvement in 19 of 20 model-horizons. N-BEATS at 6 months: ΔWIS −1.13 (95% CI 0.84–1.48; DM p<0.0001). Also −1.13 at 12 months, reported in Results without a CI. TCN at 12 months: p=0.14.
2. **Muslim et al., arXiv:2610.05699 v2 (17 Oct 2026; v1 5 Oct). VERIFIED** (https://arxiv.org/html/2610.05699v2).
   - **Dengue (Mexico):** about 2,450 municipalities. ΔWIS is PDFM minus TimesFM; negative means PDFM is better.
     - 1 month: −0.0051 (bootstrap CI −0.0081 to −0.0027; DM p<0.001)
     - 3 months: +0.0028 (p=0.14)
     - 6 months: +0.0039 (p=0.074, sensitive to block length)
     - The gain is significant only at 1 month.
     - **Oct-2025 snapshot check:** −0.00505 vs −0.00514 (2023 snapshot) at 1 month; stable.
     - No shuffled or unseen-region control for dengue.
   - **Controls in other case studies:**
     - MMR: Canadian embeddings randomly reassigned (permutation); 10-fold CV.
     - CVD: spatial random effects; county hold-out.
     - Cholera: permutation test on Precision@5.
     - PRAMS: random- and shuffled-embedding controls. Real embeddings beat random by +0.0047 AUC; no shuffled result was found. Label permutation is also used. Whole jurisdictions are held out (S2), where PDFM *replacing state* gives ΔAUC +0.0038.
3. **Nazir, Cheng, Khalid, arXiv:2605.10949. VERIFIED. Only v1 exists** (29 Apr 2026), so there is no version difference (https://arxiv.org/abs/2605.10949).
   - Malaria (Nigeria): *static* "fingerprint per location"; R² 0.201 → 0.245.
   - ARI (11 countries): *year-aligned*, "sampled at each cluster's survey year"; R² 0.157 → 0.206.
   - Stunting: country-level average, year unstated; R² 0.036 → 0.036, with no gain due to collinearity with fixed effects.
4. **AlphaEarth V1 ANNUAL. VERIFIED** (https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_SATELLITE_EMBEDDING_V1_ANNUAL).
   - "The embeddings are unit-length, meaning they have a magnitude of 1".
   - CC-BY 4.0. Required attribution: "The AlphaEarth Foundations Satellite Embedding dataset is produced by Google and Google DeepMind."
   - Cite Brown CF et al. 2025, arXiv:2507.22291.
5. **TimesFM 2.5: deciles only. VERIFIED.** `src/timesfm/configs.py` (https://github.com/google-research/timesfm) sets `DEFAULT_QUANTILES = (0.1,…,0.9)`, "the 9 quantiles that the TimesFM 2.5 model was trained to output". `output_quantiles` "must be a subset of DEFAULT_QUANTILES". The continuous head only avoids "quantile collapsing". HF card output is the mean plus the 10th–90th percentiles. **It cannot produce 0.025 or 0.975.** Score WIS on the 0.1–0.9 levels.
6. **Bosse NI, Abbott S, Cori A, van Leeuwen E, Bracher J, Funk S. 2023. *PLOS Comput Biol* 19(8):e1011393. VERIFIED** (https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1011393).

**Framing:** Neither Brittain nor Muslim's dengue study has a location-only control or a spatial hold-out, and both use a static 2023 snapshot. Our "place or placeholder" test is unoccupied.
