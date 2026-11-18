## 2 Methods

<!-- Every number carries a src comment. Technical detail is in S1_supplement_methods.md (Supplementary Methods, sections A to I). The Figure 1 drawing specification is the HTML comment in Section 2.7. -->

### 2.1 Study design

This was a retrospective forecasting study: all forecasts were made after the fact from one snapshot of final, revised data. We followed the EPIFORGE 2020 guideline for epidemic forecasting studies [@pollett2021epiforge] (checklist in Supplementary Methods, section G). Figure 1 summarises the design. Automated AI agents wrote the code and ran the downloads, data checks, model runs and analyses (see Use of AI tools). Codes such as D24 refer to rows of the protocol deviation log (Supplementary Methods, section F).

### 2.2 Data

We used weekly district case counts from the Temporal extract of OpenDengue version 1.3.1 [@clarke2024opendengue; @opendengue131]. Table 1 summarises each country; Tables S1 and S2 give the sources and the panel. Case definitions differ between countries, so all percentages compare models within a country.

**Table 1. Data and evaluation design by country.**

<!-- src: districts, panel dates: docs/data/panel_weekly_v1.md "Counts" and "Frozen rule"; scored districts: S7_embedding_distance.csv n_units BR_S5 5,439, CO_S5 1,070, PE_S5 115, TW_S5 285; test years, rows scored, weeks: T1_primary_family.csv test_years, n_rows, T_weeks for BR_S1, CO_S1, PE_S1, TW_S1; zero weeks: T5_strata.csv row_share (recorded_zero + zero_filled) for BR_S1, CO_S1, PE_S1, TW_S1 and S6_q90_mechanism.csv zero_row_share -->
| Country | Districts (scored) | Weekly data | Test years (weeks) | Splits | Rows scored | Zero weeks, % of rows |
|---|---|---|---|---|---|---|
| Brazil | 5,517 municipalities (5,439) | 2013-12-29 to 2024-12-22 | 2020–2024 (256) | All five | 2,703,183 | 73 |
| Colombia | 1,071 municipalities (1,070) | 2006-12-31 to 2022-12-25 | 2020–2022 (154) | All five | 319,930 | 79 |
| Peru | 115 provinces (115) | 2000-01-02 to 2023-12-24 | 2020–2023 (205) | New years; held-out country | 45,754 | 56 |
| Taiwan | 287 townships (285) | 1997-12-28 to 2024-12-22 | 2020–2024 (256) | New years; held-out country | 141,645 | 98 |

Note: Districts are all districts that ever reported a case. Scored districts exclude three without a boundary polygon and, in Brazil, the 78 municipalities of Espírito Santo. Weekly data give the first and last week of the panel. Rows scored are district × target week × horizon for horizons 1 and 4, counting only forecasts whose origin lies in the target's epidemiological year, after exclusions; the count is the same in every split of a country. Zero weeks are weeks without a reported case, either listed as zero by the source (Brazil 2020–2021 only; 21% of rows) or filled with zero by us. Case definitions: probable cases (Brazil), total cases (Colombia), probable and confirmed cases (Peru), and locally acquired confirmed cases by week of onset (Taiwan). <!-- src: case definitions: docs/data/panel_weekly_v1.md; Taiwan definition: docs/data/zero_fill_crosscheck.md (OpenDengue labels it "Total"); Brazil recorded zeros: T5_strata.csv BR_S1 recorded_zero row_share 21% -->

OpenDengue omits most weeks without cases (Brazil lists zeros only until 2021). We set every missing district-week inside a country's coverage window to zero and flagged it as zero-filled. <!-- src: docs/data/panel_weekly_v1.md "Frozen rule"; R2_data_scoring.md Comment 5 --> In sampled Brazilian municipalities, InfoDengue [@codeco2018infodengue; @infodengue_api] recorded cases in at most 2.1% of filled weeks, Espírito Santo aside. <!-- src: docs/data/zero_fill_crosscheck.md (2017/2019: 0; 2022–23: 1.1–2.1%, max 8); docs/data/zero_fill_crosscheck_2024.md (2024 excl. ES: 1.5%, max 3) --> The Taiwan Centers for Disease Control line list [@taiwancdc_dengue_daily] held no local case in any filled week, Colombian district totals matched national totals, and Peru could be checked only in aggregate (Supplementary Methods, section A4). <!-- src: docs/data/completeness_v1.md "Colombia: the ratio is ≈1 and stable (2020–22 weekly p10 ≥ .79)"; "Peru zero-fill check" -->

Scoring excluded, for all models, the three districts without a boundary polygon (Table S3), two Peruvian department-weeks flagged as incomplete by a rule fixed before it was applied to the test years, and Espírito Santo's 78 municipalities from 29 December 2019 (D34). There OpenDengue holds false zeros while InfoDengue shows cases (Table S4). This removed 1.41% of Brazilian rows; the models were not refitted. <!-- src: docs/data/completeness_v1.md "Flags in the test years", "Other exclusion files"; docs/plans/deviations_from_protocol.md row 34; KIT3_changes.md (38,766 rows = 1.41%) -->

### 2.3 Forecasting task

At each origin, the end of a week, a model forecasts the cases h weeks ahead (the horizon) as nine quantiles of log(1 + cases): the deciles 0.1 to 0.9, including the median. A quantile is the value below which a given share of the forecast distribution lies. Horizons were 1 to 4 weeks in the new-years split and 1 and 4 weeks elsewhere, bracketing the one to four weeks used by forecast hubs [@cramer2022covidhub]. <!-- src: docs/methods/splits.md "Origins"; docs/methods/runner.md --> For each test year Y, one model per horizon was trained on targets from the epidemiological years 2018 to Y − 1, the same rows for every model. An epidemiological year is the calendar year of a week's Wednesday. Training starts in 2018 because the first AlphaEarth year, 2017, serves 2018 targets. <!-- src: docs/methods/runner.md; docs/plans/deviations_from_protocol.md row 4 -->

### 2.4 Models and inputs

The models form a ladder, each step adding one block of inputs (Figure 1A). The seasonal naive baseline (L0) repeats the cases of the same week a year earlier. The case-history model (L1) uses cases in the 12 weeks up to the origin, cases around the same week in the previous three years, and the week of the year. The climate step (L2) adds population-weighted ERA5-Land temperature, precipitation and humidity, lagged up to 12 weeks [@era5land_ee]. The remote-sensing and population step (L3) adds MODIS vegetation greenness (NDVI) and land-surface temperature for the last three complete months [@mod13q1_ee; @mod11a2_ee], and night-time lights, built-up share and log population for the year before the target year [@viirs_ee; @ghsl_built; @ghsl_pop]. This model, with every input except the embeddings, is the reference model; below it, the only district-specific input is the case history, and its population and built-up share could act as weak identifiers. The embedding step (L4) adds the 64-number AlphaEarth embedding of the year before the target year [@brown2025alphaearth; @aef_dataset], as a population-weighted district mean rescaled to unit length. A separate recomputation reproduced these district means (Table S5), and Table S6 lists every input. <!-- src: docs/methods/runner.md "Features" (Brazil p = 1, 23, 74, 86, 150); docs/features/alphaearth_verification.md -->

The forecasting model was LightGBM quantile regression [@ke2017lightgbm], one gradient-boosted tree ensemble per quantile and horizon. The baselines were the seasonal naive forecast, a negative binomial regression on the case-history inputs and, in Brazil, TimesFM 2.5, a pretrained time-series model used zero-shot (without training on our data) [@das2024timesfm; @timesfm25]. Each country used one LightGBM configuration for every model, control and split (D2). It was tuned once on the case-history model (train 2018, validate 2019): 127 leaves per tree in Brazil and 31 elsewhere, with at least 100 rows per leaf. Models trained across countries used Brazil's configuration, or Colombia's when Brazil was held out. <!-- src: docs/methods/split_pipeline.md "Params"; docs/methods/runner.md "Models and tuning" --> Tuning each model separately, as in the original protocol, is a sensitivity analysis.

### 2.5 Location controls

A location control tells the model where a district is, or how much dengue it had before, without describing what is on the ground (Table S7). <!-- src: docs/methods/controls.md --> Historical risk (C1) is the district's mean log(1 + cases) in the years before 2018 (2014–2017 in Brazil). A district held out within its country receives the distance-weighted mean of its five nearest training districts; across countries the control is undefined. <!-- src: src/pop/features/controls.py c1_source_rows; docs/methods/controls.md --> Coordinates (C2) are latitude, longitude and 80 spherical harmonics, smooth functions of position on the globe [@russwurm2024location]. Random fields are 64 random smooth spatial maps at the spatial range of the embeddings (C4; 8,483 km in Brazil, close to smooth national trends) or at the buffer distance of the held-out-regions split (C4s; 225 km in Brazil, 130 km in Colombia). <!-- src: docs/methods/controls.md table and C4s rule; docs/plans/deviations_from_protocol.md row 15 (at 8,483 km C4 is close to a planar trend) --> The shuffled embedding (C3) gives each district the real AlphaEarth series of a fixed, randomly chosen other district. The identifier (C6) is the district ID as one categorical input, in the new-years split only. A 2023 snapshot embedding (C5) was never selected.

In the new-years split a control can act as an identifier. Elsewhere, held-out districts were never trained on, so a control acts as a geographic or historical-risk prior; there the embedding gain is the more direct measure, and the excess gain checks robustness to the control.

One control per cell, the selected control, was chosen on 2019 data (selection rule v2, D19). Controls whose forecasts equalled those of the reference model were dropped. Among the controls within two seed standard errors of the best score, we took the first in the order historical risk, shuffled embedding, coordinates, short-range random fields, random fields and snapshot. <!-- src: scripts/run/select_control.py docstring --> A fixed panel in the new-years split replaces it with each of four controls in turn.

### 2.6 Evaluation splits

Five splits define the training and test sets (Figure 1B). New years (S1) uses all districts and tests on later years. Held-out states (S2) holds out whole states (departments in Colombia) in five folds. Held-out regions (S3) holds out compact blocks of neighbouring districts and drops training districts within a buffer distance, at which correlations between 2014–2019 case series first fell below 0.1 (225 km in Brazil, 130 km in Colombia) [@roberts2017cv; @ploton2020spatial]. Held-out districts (S4) assigns districts at random to five folds, stratified by state. Held-out country (S5) trains on three countries and tests on the fourth. <!-- src: docs/methods/splits.md "Splits" (k-means blocks on centroids) and "Buffer distance D" (first 0.1 crossing of the 2014–2019 residual correlogram) -->

The state, region and district splits were run in Brazil and Colombia only, because Peru's 115 provinces are too few for state or block splits. This gives 14 combinations of country and split, which we call cells. <!-- src: docs/data/panel_weekly_v1.md (Peru 115 units); T1_primary_family.csv (14 cells: BR S1–S5, CO S1–S5, PE S1/S5, TW S1/S5) --> Held-out districts were never in a training fit but kept their own lagged cases as inputs, so unseen means never trained on, not without surveillance history.

### 2.7 Information timing

Inputs were limited to information available at the origin (Figure 1C). Weekly inputs ended at the origin week, monthly inputs used complete months before it, and yearly inputs came from the year before the target's epidemiological year. Two small leaks occur around New Year. A late-December forecast for a January target would use yearly inputs for an unfinished year, and a model trained on cases up to the end of that year, after the forecast date. <!-- src: R1_timing_leakage.md sections 1a, 1b --> Both leaks affect only the first one to four weeks of a year. After external review, we therefore restricted every primary estimate to origin-year rows, whose origin lies in the target's epidemiological year (D24). This removes both leaks without refitting and drops 4.8% of rows; all rows form a sensitivity analysis. <!-- src: R1_timing_leakage.md section 1a table (4.79% pooled h{1,4}); docs/plans/deviations_from_protocol.md row 24 -->

No test-year outcome of a held-out district entered any fit, but earlier outcomes informed tuning and control selection (Table S8). Tables S9 to S11 give the rows affected by the New Year leaks, other later-dated information (affecting all models alike or favouring the embeddings) and tuning repeated within folds. <!-- src: R8_literature.md section 4; R1_timing_leakage.md sections 0 and 1c; RF_summary.md -->

<!--
FIGURE 1 SPEC (to be drawn). Title: "Study design and information timing". Three panels: A top-left, B top-right, C full-width bottom. Colour-blind-safe palette. No country maps (generic shapes only; this also avoids the CC BY-SA 2.0 Taiwan polygons).

Panel A, "What is compared".
- Left strip: a vertical ladder of five stacked boxes, bottom to top: "L0 seasonal naive", "L1 + case history", "L2 + weekly climate", "L3 + remote sensing and population (reference model)", "L4 + AlphaEarth embedding". An arrow from the L3 box leads into the grid.
- Grid of four model boxes: rows "without embedding" (top) / "with embedding" (bottom); columns "no location control" (left) / "with selected location control C*" (right). Cells: top-left "L3", bottom-left "L4", top-right "L3 + C*", bottom-right "L4 + C*".
- Three labelled arrows: L3 -> L4 "embedding gain"; L3 -> L3 + C* "identity gain"; L3 + C* -> L4 + C* "excess gain (primary)", drawn thicker.
- Legend under the grid: "C* chosen at the 2019 origin from C1 historical risk, C2 coordinates, C3 shuffled embedding, C4/C4s random smooth fields, C5 2023 snapshot".

Panel B, "Where models are tested". Five small schematics in one row; each is a cluster of about 30 hexagons standing for districts (training = light grey, test = dark, dropped = white with dashed outline).
- "New years (S1)": two stacked copies of the same cluster, all grey labelled "2018 to Y-1" and all dark labelled "year Y".
- "Held-out states (S2)": hexagons outlined in 5 state groups; one whole group dark.
- "Held-out regions (S3)": one compact block dark; a ring of white dashed hexagons around it labelled "buffer (BR 225 km, CO 130 km)".
- "Held-out districts (S4)": about 1 in 5 hexagons dark, scattered.
- "Held-out country (S5)": four separate clusters labelled BR, CO, PE, TW; one cluster dark.
- Note under the row: "S2-S4 in Brazil and Colombia; S1 and S5 in all four countries. Held-out districts keep their own lagged cases."

Panel C, "Information timing for one forecast". Horizontal axis in epidemiological weeks covering the last ~16 weeks of year Y-1 and the first ~10 weeks of year Y; a vertical line labelled "epidemiological year boundary".
- Origin o: vertical solid line labelled "forecast origin (end of week o)". Target t = o + h: a filled diamond; bracket "h = 1 to 4 weeks".
- Above the axis, bars ending at o: "case history, weeks o-11 to o"; "climate, weeks o-11 to o". Small marks one, two and three years back labelled "same week +/- 1, previous 3 years".
- A bar "remote sensing: last 3 complete months before the month of o".
- A box at the far left: "yearly inputs from year y-1 (AlphaEarth, population, night lights, built-up share); y = target's epidemiological year".
- Below the axis: a long bar "training targets: 2018 to last week of Y-1" ending at the year boundary.
- Shade the first h target weeks of Y light red, labelled "dropped from primary scoring: origin in Y-1 (yearly inputs or training labels after the origin)"; shade the rest of Y light green, labelled "origin-year rows (primary)".
- Inset, top-right of panel C: a year axis 2018 | 2019 | 2020 | ... | last test year, annotated "2019: tuning and C* selection (train 2018, validate 2019)" and "2020 to last: one refit per test year".
Caption: see the Figure 1 caption below.
-->

**Figure 1. Study design and information timing.** Each comparison changes one block of inputs while the model type, scored rows and configuration stay fixed, and primary scores use only forecasts whose inputs and training labels end at the origin. (A) What is compared. Models add inputs in turn: seasonal naive (L0), case history (L1), weekly climate (L2), remote sensing and population (L3, the reference model) and the previous year's AlphaEarth embedding (L4). From the reference model, four models form a 2 × 2 grid, with or without the embeddings and with or without the selected location control (C\*). Arrows mark the embedding gain (L3 to L4), the identity gain (L3 to L3 + C\*) and the excess gain (L3 + C\* to L4 + C\*), which is the primary measure. The control is selected at the 2019 origin from historical risk (C1), coordinates (C2), a shuffled embedding (C3), random smooth fields (C4, C4s) and a 2023 embedding snapshot (C5). (B) Where models are tested: new years (S1; training targets 2018 to Y − 1, test year Y), held-out states (S2), held-out regions with a buffer of excluded districts (S3; 225 km in Brazil, 130 km in Colombia), held-out districts (S4) and held-out country (S5). S2 to S4 were run in Brazil and Colombia, and S1 and S5 in all four countries. Held-out districts keep their own lagged cases. (C) Information timing for one forecast. Case and climate inputs end at the origin; remote sensing uses the last complete months before the origin month; yearly inputs come from the year before the target's epidemiological year; training targets end in the last week of Y − 1. Targets in the first h weeks of Y, whose origin lies in Y − 1, are dropped from primary scoring. Horizons are 1 to 4 weeks; primary estimates pool horizons 1 and 4.

### 2.8 Scoring

The primary score was the weighted interval score (WIS) [@bracher2021wis] on log(1 + cases) [@bosse2023transformed]. The WIS rewards prediction intervals that are narrow yet contain the observation; lower is better, and for a single-value forecast it equals the absolute error. For an observation $y$ and a central interval from $l$ to $u$ with coverage $1-\alpha$, the interval score and the WIS are

$$\begin{aligned}
\mathrm{IS}_{\alpha}(l, u; y) &= (u - l) + \tfrac{2}{\alpha}\,(l - y)_{+} + \tfrac{2}{\alpha}\,(y - u)_{+},\\
\mathrm{WIS}(F, y) &= \frac{1}{K + 1/2}\Big(\tfrac{1}{2}\,\lvert y - m\rvert + \sum_{k=1}^{K} \tfrac{\alpha_k}{2}\,\mathrm{IS}_{\alpha_k}(l_k, u_k; y)\Big),
\end{aligned} \qquad (1)$$

where $F$ is the forecast, $y$ is the observed log(1 + cases), $m$ is the forecast median, and $(x)_{+}$ equals $x$ when $x$ is positive and 0 otherwise. Our deciles give $K = 4$ central intervals, with bounds $l_k$ and $u_k$ and $\alpha_k$ = 0.8, 0.6, 0.4 and 0.2 for coverage 20%, 40%, 60% and 80%. The interval score penalises wide intervals and observations outside them.

Secondary measures were the WIS on the case scale and the coverage of the 40% and 80% intervals (the share of observations inside them). Rows fall into three types of target week: weeks with at least one case, zeros listed by the source (Brazil 2020–2021 only) and zero-filled weeks. These strata depend on the outcome and are descriptive.

### 2.9 Gains

We write $\overline{W}_M$ for the mean WIS of model $M$ on the shared rows, with each target week weighted equally (Section 2.10). A gain is positive when the second model forecasts better. The embedding gain is how much the embeddings improve the reference model:

$$\Delta_{\text{emb}} = \overline{W}_{R} - \overline{W}_{R+E} \qquad (2)$$

where $R$ is the reference model (L3) and $R+E$ is the same model with the embeddings added (L4). The identity gain is how much the selected location control alone improves the reference model:

$$\Delta_{\text{id}} = \overline{W}_{R} - \overline{W}_{R+C} \qquad (3)$$

where $R+C$ is the reference model with the selected control (L3 + C\*). The excess gain, our primary measure, is what the embeddings add once the model already has the selected control:

$$\Delta_{\text{excess}} = \overline{W}_{R+C} - \overline{W}_{R+C+E} \qquad (4)$$

where $R+C+E$ has both the control and the embeddings (L4 + C\*).

We report each gain as a percentage of the reference model's WIS, $\overline{W}_R$, and also as an absolute difference, because $\overline{W}_R$ differs widely between countries. The identity share, $\Delta_{\text{id}}/\Delta_{\text{emb}}$, was to be reported only if the embedding gain's 95% confidence interval (CI) excluded zero and the gain was at least 1% of $\overline{W}_R$; it is descriptive, because control and embedding effects can interact. <!-- src: docs/methods/eval_library.md estimands.py; RESOLUTION_LOG.md section B -->

### 2.10 Statistical analysis

For each target week, we averaged the WIS difference between two models over districts at each horizon and then over horizons 1 and 4. The mean of this weekly series, over the test weeks in Table 1, is the estimate. <!-- src: src/pop/eval/estimands.py infer_estimand --> Errors in neighbouring weeks are correlated, which makes ordinary tests overconfident, so we used the Diebold–Mariano test [@diebold1995comparing] with a variance estimator designed for correlated series, the equal-weighted cosine (EWC) estimator [@lazarus2018har], and the Harvey–Leybourne–Newbold small-sample correction [@harvey1997testing]. <!-- src: src/pop/eval/stats.py ewc_inference; T1_primary_family.csv df (BR 16, CO 11, PE 13, TW 16) --> Weeks are the sampling unit, so inference concerns these districts, fitted models and seasons, not others.

The primary family was the excess gain in the 14 cells, with Holm's correction for multiple testing [@holm1979simple]. We also tested equivalence with two one-sided tests (TOST) [@lakens2017equivalence]: a cell was equivalent when its 90% CI lay inside ±1% of the reference model's WIS, unadjusted or Holm-adjusted. The 1% value was the original protocol's threshold for a material embedding gain; its use as an equivalence margin was decided after the Brazil and Peru new-years results. <!-- src: docs/plans/deviations_from_protocol.md row 9 ("the protocol's ID-share gate"); docs/plans/paper1_review_response.md (ID share only if G_emb ≥ 1% of WIS(L3)) --> Supplementary Methods, section E1, interprets this margin. Margins of 0.5% and 2% are sensitivity analyses. Each cell's label combines the two tests [@isager2026tst]. We counted a loss or a gain only when the excess gain was negative or positive with a Holm-adjusted p below 0.05, and called it small when the estimate lay inside ±1%.

Robustness checks were two more cautious tests (one with fewer variance terms, one calibrated on surrogate series; Table S12 gives their size), an interval treating the reference WIS as estimated, the case scale and all rows. These, the exploratory analyses and the sensitivity analyses (Table S13) are not adjusted for multiplicity (Supplementary Methods, section E). <!-- src: docs/plans/deviations_from_protocol.md rows 28 and 33; RC_summary.md verdict; T6a_sensitivities.csv -->

### 2.11 Forecasts without case history

Because case history already identifies districts, a secondary, exploratory analysis in Brazil dropped all 21 case-derived inputs, giving a reference model without case history (N3) and its embedding counterpart (N4). <!-- src: docs/methods/nohist_arm.md levels table (65 and 129 inputs) --> Its main design is the held-out-states split, where an identifier cannot transfer; it also uses the new-years split (horizons 1 and 4). The control was selected from controls that use no case data, in the order shuffled embedding, coordinates, identifier (new-years split only), short-range random fields and random fields. Historical risk forms a separate step, which we call static history. <!-- src: scripts/run/select_control.py PRIORITY_NOHIST --> It was pre-specified at commit bd3ba50, after the new-years results with case history and before any of its own runs were scored. An exploratory identifier panel (N3 and N4 with the identifier, new years) was added after review of the full draft, before those runs produced any result (D38). <!-- src: docs/plans/deviations_from_protocol.md row 38 -->

### 2.12 Changes to the protocol

The original protocol (15 November 2026) fixed the ladder, splits, gains and scoring; all 38 later changes are dated in Table S14. Eleven followed some new-years test results but preceded every held-out-place result. Fifteen (D24 to D38) followed external review, when every cell except Brazil held-out districts and the analysis without case history had been seen. Three record protocol commitments not carried out: a long training window, a 23-quantile WIS and per-outbreak reporting for Taiwan. <!-- src: docs/plans/deviations_from_protocol.md header, last column and rows 35–37 (rows 2, 8, 9, 11, 12, 16, 18–22 after S1 results); git log: e9df1f1 2026-11-16 20:29 CST, 3ca02d7 2026-11-16 23:21 CST, f107238 2026-11-18 02:16 CST --> Four changes affect the main result, and the new-years cells are therefore partly unblinded: one configuration per country (D2), adopted after the Brazil new-years results showed a capacity effect several times the embedding effect; selection rule v2 (D19); origin-year rows (D24); and the Espírito Santo exclusion (D34). The protocol, deviation log and analysis code were deposited at [to be completed] <!-- AUTHORS: deposit DOI --> on 18 November 2026, before the results for Brazil held-out districts and for Brazil held-out states without case history were read.
