# Place or placeholder? Satellite embeddings and location controls in weekly district dengue forecasting across four countries

<!-- Title set by the supervisor in round-3 triage (TRIAGE_round3.md A.1, answering RA M1 and RB M10); the authors may revert. Earlier alternatives are in notes_A.md. -->

Santosh Pant^1^, Brij Patel^2^, Adithya Asokan^3^

^1^ Knox College, Galesburg, Illinois, USA\
^2^ Illinois State University, Normal, Illinois, USA\
^3^ University of Washington, Seattle, Washington, USA

Corresponding author: [to be completed] <!-- AUTHORS: corresponding author name and email -->

ORCID iDs: [to be completed] <!-- AUTHORS: ORCID iDs of all three authors -->

## Abstract

**Background.** Satellite embeddings, numeric summaries of places, are entering disease forecasts. A model may use them to recognise a district, not its environment. We asked whether AlphaEarth embeddings improve weekly district dengue forecasts and whether any gain reflects place or identity.

**Methods.** We retrospectively forecast weekly cases one and four weeks ahead in 6,909 districts of Brazil, Colombia, Peru and Taiwan (OpenDengue; testing 2020–2024) with gradient boosting on case history and environmental inputs. <!-- src: S7_embedding_distance.csv n_units BR_S5 5,439 + CO_S5 1,070 + PE_S5 115 + TW_S5 285 = 6,909 scored; T1_primary_family.csv test_years --> In 14 combinations of country and evaluation split (new years; held-out states, regions, districts or country), we measured how the previous year's embeddings changed forecast error (weighted interval score on log(1 + cases)), without and with a location control. We used Diebold–Mariano tests, Holm correction and a ±1% equivalence margin set after the first results. Exploratory analyses omitted case history.

**Findings.** In 13 completed combinations, no gain survived correction [pending]. <!-- PENDING: BR S4 (14th cell), final Holm m=14: recheck every count and value in this abstract --> The clearest loss, in Colombia's held-out states (−0.47%, 95% CI −0.69 to −0.25), was robust to cautious variance estimators, dropping the control and seed choice. <!-- src: T1_primary_family.csv CO_S2 pct_of_WIS_ref, lo95_pct, hi95_pct, B4_Holm_p 0.028, p_iaaft_Holm 0.0065; R3_A2_nocontrol_rule.csv CO_S2 Holm_p 0.001; R3_C_seeds.csv CO_S2 G_excess 3-seed −0.52 --> <!-- REVISIT final kit (3-seed, m=14) --> Taiwan held out gave a large point estimate (−17.3%; absolute −0.0035) that was not robust. <!-- src: T1_primary_family.csv TW_S5 pct_of_WIS_ref, G_excess (−0.00349), B4_Holm_p 0.14, p_iaaft_Holm 0.14 --> <!-- REVISIT final kit (3-seed, m=14) --> Effects beyond ±1% (about Brazil's gain from all non-case inputs) were excluded in 8 of 13 combinations, 6 with cautious variances. <!-- src: T1b_margin_sensitivity.csv within_Holm True at margin 1.0 in 8/13; R3_A4_equivalence.csv G_excess ±1% B=4 Holm 6/13; R3_A1_positive_control.csv BR_S1 L1->L3 +1.09%, margin1_over_L1L3_gain 0.92 --> <!-- REVISIT final kit (3-seed, m=14) --> Embeddings raised upper forecast quantiles. <!-- src: S6_q90_mechanism.csv dq90_log > 0 in 13/13 --> Alone, embeddings predicted district burden in unseen states (R² 0.24 to 0.52) but added about 0.01 to coordinates and static covariates. <!-- src: R3_E1_info_probe.md T1 grouped-state CV, LightGBM: E alone 0.49/0.52/0.24/0.45; ΔR² E over G+S BR +0.010, CO +0.010 --> Without case history, coordinates cut error by 3.3% (1.7 to 4.9) in Brazil, and embeddings added nothing detectable; in Colombia both hurt. <!-- src: T6b_nohist_estimands.csv BR_S1_nohist pooled G_id 3.30 [1.68, 4.93]; R3_C_co_s2_nohist.csv G_id −2.08, G_emb −5.30 --> <!-- PENDING: BR S2 no-history -->

**Interpretation.** The embeddings carry dengue-relevant environmental information, but it duplicates coordinates and standard covariates. With case history they added no detectable skill, so place versus identity never arose; without it, exploratory evidence was inconclusive. Embeddings may worsen transfer between countries. Such features need location controls and held-out places.

<!-- Abstract word count (four labels included, comments and markers excluded): see CHANGES_v1c.md "v1d fill pass" (limit 300). -->

Keywords: dengue; probabilistic forecasting; satellite embeddings; geospatial foundation models; location confounding; spatial validation; equivalence testing
