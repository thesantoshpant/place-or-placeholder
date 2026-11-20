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

**Findings.** No gain survived correction in 14 combinations. <!-- src: T1_primary_family.csv Holm_p (m = 14), loss_or_gain (no gain in any cell); G_emb_lo95_pct ≤ 0 in every cell --> Six showed losses: five small (−0.42% to −0.68%) and one with Taiwan held out (−18.3%; absolute −0.0037). <!-- src: T1_primary_family.csv loss_or_gain, pct_of_WIS_ref (BR_S5 −0.68, CO_S1 −0.42, CO_S2 −0.52, CO_S3 −0.68, CO_S4 −0.45; TW_S5 −18.29, G_excess −0.00369), Holm_p < 0.05 --> Only Colombia's held-out states (−0.52%, 95% CI −0.74 to −0.30) survived both cautious variance estimators. <!-- src: T1_primary_family.csv CO_S2 pct_of_WIS_ref, lo95_pct, hi95_pct, B4_Holm_p 0.022, p_iaaft_Holm 0.007 (only cell with both < 0.05); R3_A2_nocontrol_rule.csv CO_S2 Holm_p 0.0009; R3_C_seeds.csv CO_S2 seeds 0–2 all negative --> Effects beyond ±1% (about Brazil's gain from all non-case inputs) were excluded in 8 combinations (5 with cautious variances). <!-- src: T1b_margin_sensitivity.csv within_Holm True at margin 1.0 in 8/14; R3_A4_equivalence.csv G_excess ±1% B=4 Holm 5/14; R3_A1_positive_control.csv BR_S1 L1->L3 +1.09%, margin1_over_L1L3_gain 0.92 --> Embeddings raised upper forecast quantiles. <!-- src: S6_q90_mechanism.csv dq90_log > 0 in 14/14 --> Alone, they predicted district burden in unseen states (R² 0.24 to 0.52) but added about 0.01 to coordinates and static covariates. <!-- src: R3_E1_info_probe.md T1 grouped-state CV, LightGBM: E alone 0.49/0.52/0.24/0.45; ΔR² E over G+S BR +0.010, CO +0.010 --> Without case history, coordinates cut error by 3.3% (1.7 to 4.9) in Brazil's new years, with no detectable embedding gain beyond them; in Brazil's held-out states nothing was detected, and in Colombia's both hurt. <!-- src: T6b_nohist_estimands.csv BR_S1_nohist pooled G_id 3.30 [1.68, 4.93], G_excess −0.43 [−2.06, 1.19]; BR_S2_nohist pooled G_id +0.88 [−0.48, 2.23], G_emb +1.52 [−1.27, 4.32], G_excess −0.01 [−1.28, 1.27]; R3_C_co_s2_nohist.csv G_id −2.08, G_emb −5.30 -->

**Interpretation.** The embeddings carry dengue-relevant environmental information, but it duplicates coordinates and standard covariates. With case history they added no detectable skill, so place versus identity never arose; without it, exploratory evidence was inconclusive. Embeddings may worsen transfer between countries. Such features need location controls and held-out places.

<!-- Abstract word count (four labels included, comments and markers excluded): see CHANGES_v1e.md (limit 300). -->

Keywords: dengue; probabilistic forecasting; satellite embeddings; geospatial foundation models; location confounding; spatial validation; equivalence testing
