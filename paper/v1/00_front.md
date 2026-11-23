# Place or placeholder? AlphaEarth satellite embeddings did not detectably improve weekly dengue forecasts in four countries

<!-- Title changed in response to co-author comment C01 (states the finding); it needs the authors' approval. The earlier title is in STYLE_DECISIONS.md section 1; other alternatives are in notes_A.md. -->

Santosh Pant^1^, Brij Patel^2^, Adithya Asokan^3^

^1^ Knox College, Galesburg, Illinois, USA\
^2^ Illinois State University, Normal, Illinois, USA\
^3^ University of Washington, Seattle, Washington, USA

Corresponding author: [to be completed] <!-- AUTHORS: corresponding author name and email -->

ORCID iDs: [to be completed] <!-- AUTHORS: ORCID iDs of all three authors -->

## Abstract

**Background.** Some recent disease forecasts use satellite embeddings (numbers summarising places). A model may use them only as a placeholder, recognising districts and their usual dengue levels without learning about the environment. We asked whether AlphaEarth embeddings improve weekly district dengue forecasts and whether gains go beyond such recognition.

**Methods.** We retrospectively forecast cases one and four weeks ahead in 6,909 districts of Brazil, Colombia, Peru and Taiwan (OpenDengue, 2020–2024) with gradient boosting. <!-- src: S7_embedding_distance.csv n_units BR_S5 5,439 + CO_S5 1,070 + PE_S5 115 + TW_S5 285 = 6,909 scored; T1_primary_family.csv test_years --> In 14 comparisons across future years and held-out places, we measured how embeddings changed the weighted interval score, with and without a location control (an input that only identifies a district), to test whether location alone explains gains. We used Diebold–Mariano tests, the Holm correction and a ±1% equivalence margin set after the first Brazil and Peru results.

**Findings.** No comparison showed a significant gain after correction. <!-- src: T1_primary_family.csv Holm_p (m = 14), loss_or_gain (no gain in any cell); G_emb_lo95_pct ≤ 0 in every cell --> Six showed losses: five small (−0.42% to −0.68%) and one with Taiwan held out (−18.3%; absolute −0.0037). <!-- src: T1_primary_family.csv loss_or_gain, pct_of_WIS_ref (BR_S5 −0.68, CO_S1 −0.42, CO_S2 −0.52, CO_S3 −0.68, CO_S4 −0.45; TW_S5 −18.29, G_excess −0.00369), Holm_p < 0.05 --> Only Colombia's held-out-states loss (−0.52%) stayed significant under two stricter checks and a check for cases hidden in zero-filled weeks. <!-- src: T1_primary_family.csv CO_S2 pct_of_WIS_ref, lo95_pct, hi95_pct, B4_Holm_p 0.022, p_iaaft_Holm 0.007 (only cell with both < 0.05); R5_zero_fill_stress.csv s_pct 2.1, exc_share_holm_sig_loss = 1 for CO_S2 and BR_S5 only (BR_S5 fails B4_Holm_p 0.095); R3_A2_nocontrol_rule.csv CO_S2 Holm_p 0.0009; R3_C_seeds.csv CO_S2 seeds 0–2 all negative --> In 8 comparisons (5 under the stricter checks), any gain or loss was shown to be smaller than 1% of forecast error. This margin is roughly Brazil's gain from all non-case inputs combined. <!-- src: T1b_margin_sensitivity.csv within_Holm True at margin 1.0 in 8/14; R3_A4_equivalence.csv G_excess ±1% B=4 Holm 5/14; R3_A1_positive_control.csv BR_S1 L1->L3 +1.09%, margin1_over_L1L3_gain 0.92; every non-case step detectable only in BR_S1 (L1->L2 p .041, L2->L3 p .005); CO_S1 only L2->L3 (p .034); PE_S1, TW_S1 none --> In exploratory analyses, embeddings alone predicted district burden in unseen states. <!-- src: R3_E1_info_probe.md T1 grouped-state CV, LightGBM: E alone 0.49/0.52/0.24/0.45; S 0.65/0.66/0.43/0.55; ΔR² E over G+S BR +0.010, CO +0.010 (PE −0.071 and TW +0.070, CIs include zero); S6_q90_mechanism.csv dq90_log > 0 in 14/14 (upper-quantile sentence cut from the abstract; in Results 3.5) --> Without case history, neither coordinates nor embeddings helped detectably in Brazil's held-out states; both hurt in Colombia's. In Brazil's future years, coordinates cut error by 3.3% (1.7 to 4.9); embeddings added nothing detectable. <!-- src: T6b_nohist_estimands.csv BR_S1_nohist pooled G_id 3.30 [1.68, 4.93], G_excess −0.43 [−2.06, 1.19]; BR_S2_nohist pooled G_id +0.88 [−0.48, 2.23], G_emb +1.52 [−1.27, 4.32], G_excess −0.01 [−1.28, 1.27]; R3_C_co_s2_nohist.csv G_id −2.08, G_emb −5.30 -->

**Interpretation.** Embeddings partly showed which districts usually have more dengue, but in Brazil and Colombia other non-case inputs already held most of it. With case history they added no detectable accuracy; without it, evidence was inconclusive. Embeddings should be tested against location-only controls in held-out places.

<!-- Abstract word count (four labels included, comments and markers excluded): see CHANGES_v1f_style.md (limit 300). -->

Keywords: dengue; probabilistic forecasting; satellite embeddings; geospatial foundation models; location confounding; spatial validation; equivalence testing
