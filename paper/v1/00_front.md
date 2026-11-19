# Place or placeholder? Satellite embeddings and location controls in weekly district dengue forecasting across four countries

<!-- Title set by the supervisor in round-3 triage (TRIAGE_round3.md A.1, answering RA M1 and RB M10); the authors may revert. Earlier alternatives are in notes_A.md. -->

Santosh Pant^1^, Brij Patel^2^, Adithya Asokan^3^

^1^ Knox College, Galesburg, Illinois, USA\
^2^ Illinois State University, Normal, Illinois, USA\
^3^ University of Washington, Seattle, Washington, USA

Corresponding author: [to be completed] <!-- AUTHORS: corresponding author name and email -->

ORCID iDs: [to be completed] <!-- AUTHORS: ORCID iDs of all three authors -->

## Abstract

**Background.** Satellite embeddings, numeric summaries of places, are entering disease forecasts. A model can use an embedding to recognise a district rather than learn about its environment. We asked whether AlphaEarth embeddings improve weekly district dengue forecasts and whether any gain reflects place or identity.

**Methods.** We retrospectively forecast weekly dengue one and four weeks ahead in 6,909 districts of Brazil, Colombia, Peru and Taiwan (OpenDengue; testing 2020–2024) with gradient-boosted quantile regression on case history, climate, remote sensing and population. <!-- src: S7_embedding_distance.csv n_units BR_S5 5,439 + CO_S5 1,070 + PE_S5 115 + TW_S5 285 = 6,909 scored; T1_primary_family.csv test_years --> In 14 combinations of country and evaluation split (new years, or held-out states, regions, districts or country), we estimated the change in forecast error (weighted interval score on log(1 + cases)) from adding the previous year's embeddings, without and with a location control. We used Diebold–Mariano tests, Holm correction and a ±1% equivalence margin chosen after the first results. An exploratory analysis omitted case history.

**Findings.** In 13 completed combinations, no gain survived correction [pending]. <!-- PENDING: BR S4 (14th cell), final Holm m=14, seed-averaged estimates (R3-C): recheck every count and value in this abstract --> <!-- REVISIT after R3 --> The clearest loss, in Colombia's held-out states (−0.47%, 95% CI −0.69 to −0.25), was robust to cautious variance estimators and to dropping the control. <!-- src: T1_primary_family.csv CO_S2 pct_of_WIS_ref, lo95_pct, hi95_pct, B4_Holm_p 0.028, p_iaaft_Holm 0.0065; G_emb_pct −0.59, G_emb_p 0.0001 --> <!-- PENDING: R3-A2 (CO S2 significant under the no-control rule) --> With Taiwan held out, a large point estimate (−17.3%; absolute −0.0035) was not robust. <!-- src: T1_primary_family.csv TW_S5 pct_of_WIS_ref, G_excess (−0.00349), B4_Holm_p 0.14, p_iaaft_Holm 0.14 --> Effects beyond ±1%, about Brazil's combined benefit of climate, remote sensing and population, were excluded in 8 of 13 combinations with the primary variance estimator, [pending] with a cautious one. <!-- src: T1b_margin_sensitivity.csv within_Holm True at margin 1.0 in 8/13; T2_ladder.csv BR_S1 L1 0.16996 vs L3 0.16809 pooled h{1,4} (1.1%, row means) --> <!-- PENDING: R3-A4 (B=4 + Holm count at ±1%), R3-A1 (anchor with CIs) --> Embeddings raised upper forecast quantiles. <!-- src: S6_q90_mechanism.csv dq90_log > 0 in 13/13 --> Without case history (Brazil, new years), coordinates reduced error by 3.3% (1.7 to 4.9), and embeddings added −0.43% (−2.06 to 1.19) beyond them. <!-- src: T6b_nohist_estimands.csv BR_S1_nohist pooled G_id, G_excess pct_of_ref, lo95_pct, hi95_pct --> <!-- PENDING: BR S2 no-history; CO S2 no-history (R3-C) -->

**Interpretation.** With case history, AlphaEarth embeddings added no detectable skill at one and four weeks, so place versus identity did not arise. Without case history, the exploratory single-country evidence was inconclusive. Embeddings may worsen transfer between countries. Such features need location controls, held-out places and equivalence margins.

<!-- Abstract word count (four labels included, comments and markers excluded): see CHANGES_v1c.md for the count on 2026-11-19 (limit 300). Recount after the fill pass. -->

Keywords: dengue; probabilistic forecasting; satellite embeddings; geospatial foundation models; location confounding; spatial validation; equivalence testing
