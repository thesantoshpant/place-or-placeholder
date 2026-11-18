# Place or Placeholder? A four-country evaluation of satellite embeddings in weekly district dengue forecasting

<!-- Title alternatives are in notes_A.md. Final choice after the no-history Brazil S2 cell lands (resolution log A, F-C1). V2 review: keep the title a question unless no-history S2 is decisive. -->

**Santosh Pant**^1^, **Brij Patel**^2^, **Adithya Asokan**^3^

^1^ Knox College, Galesburg, Illinois, USA
^2^ Illinois State University, Normal, Illinois, USA
^3^ University of Washington, Seattle, Washington, USA

Corresponding author: [[AUTHORS: TBD]] (name, email)
ORCID iDs: [[AUTHORS: TBD]]

## Abstract

**Background.** Satellite foundation-model embeddings, numeric summaries of places, are entering disease forecasts. Because each is unique, a model can use it as a district identifier rather than as environmental information. We tested whether AlphaEarth embeddings add skill beyond surveillance history and location.

**Methods.** We retrospectively forecast weekly dengue cases one and four weeks ahead in 6,987 districts of Brazil, Colombia, Peru and Taiwan <!-- src: docs/data/boundaries_join.md (6,987 units with geometry = 5,517 + 1,070 + 115 + 285); 6,909 are scored after the Espírito Santo exclusion (S7_embedding_distance.csv n_units 5,439 + 1,070 + 115 + 285) --> (OpenDengue; training from 2018, testing from 2020 <!-- src: T1_primary_family.csv test_years (last test year 2022–2024 by country); docs/plans/deviations_from_protocol.md (training targets 2018..Y−1) -->) with gradient-boosted quantile regression on case history, climate, remote sensing and population. The primary estimand, the excess gain, is the error reduction (weighted interval score on log(1 + cases)) from adding prior-year embeddings to a model with a location control. We estimated it in 14 country-by-split cells (new years or held-out places) with Diebold–Mariano tests, Holm correction and a ±1% equivalence margin. An exploratory arm omitted case history.

**Findings.** In the 13 completed cells [[PENDING: BR S4]], no gain survived correction [[PENDING: final Holm m=14]]; for new years in Brazil the excess gain was +0.23% (95% confidence interval [CI] −0.33 to 0.79). <!-- src: T1_primary_family.csv BR_S1 pct_of_WIS_ref, lo95_pct, hi95_pct --> In 8 of 13 cells, differences beyond ±1% were excluded after adjustment. <!-- src: T1b_margin_sensitivity.csv margin_pct 1.0 within_Holm True in 8/13 (BR_S1, BR_S2, BR_S3, BR_S5, CO_S1, CO_S2, CO_S4, CO_S5); T1_primary_family.csv TOST_p_Holm --> Six showed losses after correction: five small (−0.39% to −0.65%; Brazil held out, four Colombian splits; two robust to more cautious tests) <!-- src: T1_primary_family.csv BR_S5, CO_S1..CO_S4 pct_of_WIS_ref, Holm_p_available, loss_or_gain; B4_Holm_p and p_iaaft_Holm both < 0.05 only for BR_S5 (0.027, 0.0065) and CO_S2 (0.028, 0.0065) --> and one large relative to a low baseline (Taiwan held out: −17.3%, CI −27.0 to −7.6; absolute 0.0035 of a 0.020 baseline). <!-- src: T1_primary_family.csv TW_S5 pct_of_WIS_ref, lo95_pct, hi95_pct, G_excess (−0.00349), WIS_L3 (0.0202) --> Losses concentrated in weeks without reported cases, where embedding models predicted higher upper ranges. <!-- src: T5_strata.csv G_excess zero_filled contrib_pct (negative in 13/13); S6_q90_mechanism.csv dq90_log (positive in 13/13) --> Without case history (Brazil, new years), coordinates reduced error by 3.3% (CI 1.7 to 4.9); embeddings added no detectable skill beyond them (−0.43%, CI −2.06 to 1.19). <!-- src: T6b_nohist_estimands.csv BR_S1_nohist pooled G_id, G_excess pct_of_ref, lo95_pct, hi95_pct --> [[PENDING: BR S2 no-history]]

**Interpretation.** For one learner at one- and four-week horizons, district-mean AlphaEarth embeddings showed no evidence of improving dengue forecasts beyond surveillance history and location, and worsened transfer to a dissimilar country. Such features need location-only controls and equivalence tests.

<!-- Abstract word count (Background to Interpretation, excluding comments and markers, including the four section labels): 300 (v1b counter, 2026-11-18). Must stay ≤ 300. -->

## Plain-language summary

Health departments use dengue forecasts to plan mosquito control and hospital care. Artificial-intelligence models can now summarise each place from satellite images as a list of 64 numbers, <!-- src: docs/research/data_and_tools.md AlphaEarth row (bands A00–A63) --> and some studies report that these summaries improve forecasts. But each summary is unique to its place, so a model could improve just by recognising which place it is. We tested this in nearly 7,000 districts in Brazil, Colombia, Peru and Taiwan. <!-- src: docs/data/boundaries_join.md (6,987 units with geometry) --> When the model already knew each district's recent dengue cases, the summaries gave no detectable improvement, and in most settings we could rule out improvements larger than 1%. <!-- src: T1_primary_family.csv (no Holm-significant gain); T1b_margin_sensitivity.csv within_Holm 8/13 at ±1% --> They made forecasts slightly worse in several settings, and worse in relative terms when a model was moved to Taiwan, where cases are rare. Without recent case data, in Brazil, map coordinates helped and the summaries added no detectable benefit beyond them. <!-- src: T6b_nohist_estimands.csv BR_S1_nohist pooled G_id (+3.30, CI 1.68 to 4.93), G_excess (−0.43, CI −2.06 to 1.19) -->

## Keywords

dengue; probabilistic forecasting; satellite embeddings; geospatial foundation models; location confounding; spatial validation; equivalence testing
