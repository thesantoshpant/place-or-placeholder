# Place or Placeholder? A four-country evaluation of satellite embeddings in weekly district dengue forecasting

<!-- Title alternatives are in notes_A.md. Final choice after the no-history Brazil S2 cell lands (resolution log A, F-C1). -->

**Santosh Pant**^1^, **Brij Patel**^2^, **Adithya Asokan**^3^

^1^ Knox College, Galesburg, Illinois, USA
^2^ Illinois State University, Normal, Illinois, USA
^3^ University of Washington, Seattle, Washington, USA

Corresponding author: [[AUTHORS: TBD]] (name, email)
ORCID iDs: [[AUTHORS: TBD]]

## Abstract

**Background.** Satellite foundation-model embeddings, numeric summaries of places, are entering disease forecasts. Because each embedding is unique, a model can use it as a district identifier rather than as environmental information. We tested whether AlphaEarth embeddings improve weekly dengue forecasts beyond surveillance history and location.

**Methods.** We retrospectively forecast weekly dengue cases one and four weeks ahead in 6,987 districts of Brazil, Colombia, Peru and Taiwan <!-- src: docs/data/boundaries_join.md (6,987 units with geometry = 5,517 + 1,070 + 115 + 285); 6,909 are scored after the Espírito Santo exclusion (S7_embedding_distance.csv n_units 5,439 + 1,070 + 115 + 285) --> (OpenDengue; training from 2018, testing 2020 to 2022–2024 <!-- src: T1_primary_family.csv test_years; docs/plans/deviations_from_protocol.md (training targets 2018..Y−1) -->) with gradient-boosted quantile regression on case history, climate, remote sensing and population. The primary estimand, the excess gain, is the reduction in forecast error (weighted interval score on log(1 + cases)) from adding the previous year's embeddings to a model already containing a location control. We estimated it in 14 country-by-split cells (new years, held-out states, spatial blocks, random districts or countries) with Diebold–Mariano tests, Holm correction and a ±1% equivalence margin. An exploratory arm omitted case history.

**Findings.** In the 13 completed cells [[PENDING: BR S4]], no gain survived correction [[PENDING: final Holm m=14]]; for new years in Brazil the excess gain was +0.23% (95% confidence interval [CI] −0.33 to 0.79). <!-- src: T1_primary_family.csv BR_S1 pct_of_WIS_ref, lo95_pct, hi95_pct --> Six showed losses after correction: five small (−0.39% to −0.65%; Brazil held out, four Colombian splits) <!-- src: T1_primary_family.csv BR_S5, CO_S1..CO_S4 pct_of_WIS_ref, Holm_p_available, loss_or_gain --> and one large (Taiwan held out: −17.3%, CI −27.0 to −7.6; absolute 0.0035 of a 0.020 baseline). <!-- src: T1_primary_family.csv TW_S5 pct_of_WIS_ref, lo95_pct, hi95_pct, G_excess, WIS_L3 --> Their direction was consistent, but four (three Colombian, Taiwan) were significant only under some variance estimators. <!-- src: T1_primary_family.csv B4_Holm_p (CO_S1 0.079, CO_S3 0.084, CO_S4 0.14, TW_S5 0.14), p_iaaft_Holm (CO_S4 0.054, TW_S5 0.14); BR_S5 and CO_S2 < 0.05 under both --> Losses sat in zero-filled weeks, where embeddings raised upper quantiles. <!-- src: T5_strata.csv G_excess zero_filled contrib_pct (negative in 13/13); S6_q90_mechanism.csv dq90_log --> Without case history (Brazil, new years), coordinates reduced error by 3.3% (CI 1.7 to 4.9); embeddings added −0.43% (CI −2.06 to 1.19) beyond them. <!-- src: T6b_nohist_estimands.csv BR_S1_nohist pooled G_id, G_excess pct_of_ref, lo95_pct, hi95_pct --> [[PENDING: BR S2 no-history]]

**Interpretation.** District-mean AlphaEarth embeddings showed no evidence of improving dengue forecasts beyond surveillance history and location, and worsened transfer to a dissimilar country. Evaluations of such features need location-only controls and equivalence tests.

<!-- Abstract word count (Background to Interpretation, excluding comments and markers): 298 by whitespace count including the four section labels (verifier, 2026-11-18). -->

## Plain-language summary

Health departments use dengue forecasts to plan mosquito control and hospital care. Artificial-intelligence models can now summarise each place from satellite images as a short list of numbers, and some studies report that these summaries improve forecasts. But each summary is unique to its place, so a model could improve just by recognising which place it is. We tested this in nearly 7,000 districts in Brazil, Colombia, Peru and Taiwan. <!-- src: docs/data/boundaries_join.md (6,987 units with geometry) --> Once the model knew each district's recent dengue cases, the satellite summaries brought no meaningful improvement anywhere. They made forecasts slightly worse in several settings and much worse when the model was moved to Taiwan, though some of these losses were statistically fragile. Without recent case data, map coordinates helped, and the summaries added nothing detectable beyond them. Such tools should be tested against simple location-only alternatives.

## Keywords

dengue; probabilistic forecasting; satellite embeddings; geospatial foundation models; location confounding; spatial validation; equivalence testing
