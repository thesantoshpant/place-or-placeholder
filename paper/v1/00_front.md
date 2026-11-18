# Place or placeholder? A four-country evaluation of satellite embeddings in weekly district dengue forecasting

<!-- Title alternatives are in notes_A.md. Keep the title a question unless the Brazil held-out-states cell without case history is decisive. -->

Santosh Pant^1^, Brij Patel^2^, Adithya Asokan^3^

^1^ Knox College, Galesburg, Illinois, USA\
^2^ Illinois State University, Normal, Illinois, USA\
^3^ University of Washington, Seattle, Washington, USA

Corresponding author: [to be completed] <!-- AUTHORS: corresponding author name and email -->

ORCID iDs: [to be completed] <!-- AUTHORS: ORCID iDs of all three authors -->

## Abstract

**Background.** Satellite foundation-model embeddings, numeric summaries of places, are entering disease forecasts. A model can use a place's embedding to recognise the district rather than to learn about its environment. We tested whether AlphaEarth embeddings improve weekly dengue forecasts beyond surveillance history and location.

**Methods.** We retrospectively forecast weekly dengue cases one and four weeks ahead in 6,987 districts of Brazil, Colombia, Peru and Taiwan (OpenDengue; training from 2018, testing from 2020), using gradient-boosted quantile regression with case history, climate, remote sensing and population. <!-- src: docs/data/boundaries_join.md (6,987 units with geometry = 5,517 + 1,070 + 115 + 285); 6,909 are scored after the Espírito Santo exclusion (S7_embedding_distance.csv n_units 5,439 + 1,070 + 115 + 285); T1_primary_family.csv test_years; docs/plans/deviations_from_protocol.md (training targets 2018..Y−1) --> The primary measure, the excess gain, is the reduction in forecast error (weighted interval score on log(1 + cases)) from adding the previous year's embeddings to a model with a location control. We estimated it in 14 country-by-split cells (new years or held-out places) with Diebold–Mariano tests, Holm correction and a ±1% equivalence margin. An exploratory analysis omitted case history.

**Results.** In the 13 completed cells, no gain survived correction [pending]. <!-- PENDING: BR S4 (14th cell), final Holm m=14 and BR S2 no-history: recheck every count in this abstract --> In Brazil (new years), the excess gain was +0.23% (95% confidence interval [CI] −0.33 to 0.79). <!-- src: T1_primary_family.csv BR_S1 pct_of_WIS_ref, lo95_pct, hi95_pct --> Differences beyond ±1% were excluded in 8 of 13 cells. <!-- src: T1b_margin_sensitivity.csv margin_pct 1.0 within_Holm True in 8/13 (BR_S1, BR_S2, BR_S3, BR_S5, CO_S1, CO_S2, CO_S4, CO_S5); T1_primary_family.csv TOST_p_Holm --> Six cells showed losses after correction. Five were small (−0.39% to −0.65%), two of them robust to more cautious tests. <!-- src: T1_primary_family.csv BR_S5, CO_S1..CO_S4 pct_of_WIS_ref, Holm_p_available, loss_or_gain; B4_Holm_p and p_iaaft_Holm both < 0.05 only for BR_S5 (0.027, 0.0065) and CO_S2 (0.028, 0.0065) --> One was large relative to a low baseline (Taiwan held out: −17.3%, CI −27.0 to −7.6; absolute 0.0035 of a 0.020 baseline). <!-- src: T1_primary_family.csv TW_S5 pct_of_WIS_ref, lo95_pct, hi95_pct, G_excess (−0.00349), WIS_L3 (0.0202) --> Losses arose mainly in weeks without reported cases. <!-- src: T5_strata.csv G_excess zero_filled contrib_pct (negative in 13/13) --> Without case history (Brazil, new years), coordinates reduced error by 3.3% (CI 1.7 to 4.9), and embeddings added no detectable skill beyond them (−0.43%, CI −2.06 to 1.19). <!-- src: T6b_nohist_estimands.csv BR_S1_nohist pooled G_id, G_excess pct_of_ref, lo95_pct, hi95_pct -->

**Conclusions.** For one forecasting model at one- and four-week horizons, district-mean AlphaEarth embeddings showed no evidence of improving dengue forecasts beyond surveillance history and location, and worsened transfer to a dissimilar country. Such features need location-only controls and equivalence tests.

<!-- Abstract word count (four labels included, comments and markers excluded) is checked at build; must stay ≤ 300. -->

Keywords: dengue; probabilistic forecasting; satellite embeddings; geospatial foundation models; location confounding; spatial validation; equivalence testing
