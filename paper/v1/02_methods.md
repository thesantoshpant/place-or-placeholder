## 2 Methods

<!-- Writer B. Every number carries a src comment. Terms follow paper/v1/STYLE.md. The Figure 1 spec is the HTML comment at the end of 2.6. Technical detail is in S1_supplement_methods.md (sections A-H). -->

### 2.1 Study design and reporting

This is a retrospective forecasting study: all forecasts were made after the fact from one snapshot of final, revised data, none in real time. We follow the EPIFORGE 2020 reporting guideline [@pollett2021epiforge] (checklist in Supplement S1, section G). The unit is the second-level administrative unit (Admin2): municipalities in Brazil and Colombia, provinces in Peru, townships in Taiwan. We call them districts. Fig 1 summarises the design. Labels such as D24 are rows of the deviation log (Supplement S1, section E).

### 2.2 Data

We used the Temporal extract of OpenDengue v1.3.1 [@clarke2024opendengue; @opendengue131]: weekly, Sunday-start rows at Admin2 resolution. A country's district universe is every district that ever reported a case (Table 1). Case definitions differ between countries, so all percentages are within-country comparisons. Polygons, sources and licences are in Supplement S1, section B.

*Table 1. Data and evaluation design by country. Scored rows are per seed, horizons 1 and 4, origin-year rows, after exclusions.*

| Country | Districts | Weekly panel | Case definition | Test years | Splits | Scored rows | Weeks (T) |
|---|---|---|---|---|---|---|---|
| Brazil | 5,517 municipalities | 2013-12-29 to 2024-12-22 | Probable | 2020–2024 | S1–S5 | 2,703,183 | 256 |
| Colombia | 1,071 municipalities | 2006-12-31 to 2022-12-25 | Total | 2020–2022 | S1–S5 | 319,930 | 154 |
| Peru | 115 provinces | 2000-01-02 to 2023-12-24 | Probable and confirmed | 2020–2023 | S1, S5 | 45,754 | 205 |
| Taiwan | 287 townships | 1997-12-28 to 2024-12-22 | Local confirmed, by onset week | 2020–2024 | S1, S5 | 141,645 | 256 |

<!-- src: districts, panel dates, case definitions: docs/data/panel_weekly_v1.md "Counts" and "Frozen rule"; Taiwan definition: docs/data/zero_fill_crosscheck.md (OpenDengue labels it "Total"); test years, scored rows, weeks: T1_primary_family.csv test_years, n_rows, T_weeks for BR_S1, CO_S1, PE_S1, TW_S1 -->

**Zero-filling.** OpenDengue omits most weeks without cases, inconsistently (Brazil lists explicit zeros only until 2021). We set every missing district-week inside a country's coverage window to zero and flagged it as zero-filled. <!-- src: docs/data/panel_weekly_v1.md "Frozen rule"; R2_data_scoring.md Comment 5 --> In Brazil, checks against InfoDengue probable counts [@codeco2018infodengue; @infodengue_api] found any case in at most 2.1% of absent weeks (at most 8 cases) in the five years checked, Espírito Santo aside; in Taiwan, every reported township-week matched the Taiwan CDC case file and no absent week held a local case [@taiwancdc_dengue_daily]. Colombia and Peru could be checked only against aggregate totals (Supplement S1, section B). <!-- src: docs/data/zero_fill_crosscheck.md (2017/2019: 0; 2022–23: 1.1–2.1%, max 8); docs/data/zero_fill_crosscheck_2024.md (2024 excl. ES: 1.5%, max 3); docs/data/completeness_v1.md "Peru zero-fill check" -->

**Exclusions.** For all models alike, scoring drops the three districts without a polygon, two Peruvian department-weeks flagged as incomplete by a pre-stated rule, and all 78 Espírito Santo municipalities from 29 December 2019 onward, where OpenDengue holds false zeros while InfoDengue shows cases (1.41% of Brazilian rows; D34). The Espírito Santo false zeros remain in the training targets, because models were not refitted. These are retrospective quality checks; dropping the incomplete-week rule restores only 16 Peruvian rows. <!-- src: docs/results/review/RA_summary.md RA3; docs/data/completeness_v1.md "Flags in the test years", "Other exclusion files"; docs/plans/deviations_from_protocol.md row 34; KIT3_changes.md (38,766 rows = 1.41%) -->

### 2.3 Forecasting task, features and models

At a forecast origin (the end of a week), each model forecasts cases h weeks ahead on the log(1 + cases) scale as nine quantiles (deciles 0.1–0.9, including the median; the native output of the TimesFM baseline). Horizons are 1–4 weeks in S1 and 1 and 4 weeks in S2–S5 (D4); one to four weeks is the range used by forecast hubs [@cramer2022covidhub], and 1 and 4 bracket it. One model per horizon is refitted once per test year Y on targets from epidemiological years 2018 to Y − 1, the same rows for every level, since the first AlphaEarth year (2017) serves 2018 targets. <!-- src: docs/methods/splits.md "Origins"; docs/methods/runner.md; docs/plans/deviations_from_protocol.md row 4 -->

**Feature ladder.** Each level adds one block of inputs (Supplement S1, sections B and C):

- **L0, seasonal naive:** cases in the same week a year earlier.
- **L1, case history:** cases in the 12 weeks up to the origin and around the same week in each of the previous three years; week of the year.
- **L2, + weekly climate:** population-weighted ERA5-Land temperature, precipitation and humidity, lagged up to 12 weeks [@era5land_ee].
- **L3, + remote sensing and population:** MODIS NDVI and land-surface temperature for the last three complete months [@mod13q1_ee; @mod11a2_ee]; night lights, built-up share and log population for the year before the target year [@viirs_ee; @ghsl_built; @ghsl_pop].
- **L4, + AlphaEarth:** the 64-dimensional annual embedding [@brown2025alphaearth; @aef_dataset] of the year before the target year, averaged over the district with population weights and renormalised to unit length.

<!-- src: docs/methods/runner.md "Features" (Brazil p = 1, 23, 74, 86, 150) -->

L0–L2 contain no district-specific inputs; L3 adds population and built-up share, which could act as weak identifiers.

**Models.** The main model is LightGBM quantile regression [@ke2017lightgbm], one booster per quantile and horizon (crossed quantiles sorted). Baselines are L0, a negative binomial regression on L1 inputs and, in Brazil, zero-shot TimesFM 2.5 [@das2024timesfm; @timesfm25]. Each country uses one LightGBM configuration for every level, control and split (D2), tuned once on L1 at the 2019 origin (train 2018, validate 2019): 127 leaves and 100 minimum rows per leaf in Brazil, 31 and 100 elsewhere. Cross-country models use Brazil's configuration, or Colombia's when Brazil is held out. <!-- src: docs/methods/split_pipeline.md "Params"; docs/methods/runner.md "Models and tuning" --> The primary question is therefore the value of each block under a shared configuration; per-level tuning, as in the original protocol, is a sensitivity analysis.

### 2.4 Location controls and the validation-selected control

A location control tells the model where a district is without describing what is on the ground. It replaces the AlphaEarth block (L3 + Ck) or sits beside it (L4 + Ck). <!-- src: docs/methods/controls.md -->

- **Historical risk.** C1: the district's mean log(1 + cases) in the years before 2018 (Brazil 2014–2017); held-out districts in S2–S4 get the distance-weighted mean of their five nearest training districts; undefined across countries. <!-- src: src/pop/features/controls.py c1_source_rows; docs/methods/controls.md -->
- **Geographic.** C2: latitude, longitude and 80 spherical harmonics [@russwurm2024location]. C4: 64 random smooth spatial fields at the AlphaEarth spatial range (Brazil 8,483 km); C4s: the same at range D (Brazil 225 km, Colombia 130 km). <!-- src: docs/methods/controls.md table and C4s rule -->
- **Identifier.** C3: the real AlphaEarth series of a fixed, randomly chosen other district. C6: the district ID as one categorical input (S1 only).
- **Snapshot.** C5: the 2023 embedding for every year (a candidate never selected).

In each country × split, the **validation-selected control (C\*)** is chosen at the 2019 origin by rule v2 (D19): candidates with constant features or forecasts identical to L3 are excluded; candidates within two seed standard errors of the best 2019 WIS form a tie set; C\* is the first of them in the fixed priority C1 > C3 > C2 > C4s > C4 > C5 (C1 is not available in S5). <!-- src: scripts/run/select_control.py docstring --> Because C\* is selected, we also report a fixed control panel with C1, C2, C3 and C6 each in place of C\* in S1 (D29); the Brazil C3 and C6 rows are [[PENDING: BR C3/C6 panel]].

### 2.5 Evaluation splits

Each split asks a different "where" question (Fig 1B):

- **S1 new years:** all districts, later years.
- **S2 held-out states:** whole Admin1 units held out, in five folds.
- **S3 held-out buffered blocks:** k-means blocks of districts held out; training districts within a buffer D dropped (Brazil 225 km, Colombia 130 km, from 2014–2019 case correlograms) [@roberts2017cv; @ploton2020spatial].
- **S4 held-out random districts:** five folds of districts, stratified by Admin1.
- **S5 held-out country:** train on three countries, test on the fourth.

<!-- src: docs/methods/splits.md "Splits" and "Buffer distance D" -->

S2–S4 run in Brazil and Colombia; Peru's 115 provinces are too few for state or block splits. This gives 14 country × split cells. <!-- src: docs/data/panel_weekly_v1.md (Peru 115 units); T1_primary_family.csv (14 cells: BR S1–S5, CO S1–S5, PE S1/S5, TW S1/S5) --> Held-out districts are never in a training fit but keep their own lagged cases as inputs: "unseen" means never trained on, not without surveillance history. Taiwan 2021, which had no local cases, is a test year (D25).

### 2.6 Information timing

Weekly case and climate inputs end at the origin week, monthly inputs use months that ended before it, and yearly inputs come from the year before the target's epidemiological year (Fig 1C). Two look-aheads remain at year boundaries: targets in the first h weeks of year Y (origin in Y − 1) receive the annual product of the unfinished year Y − 1, and each annual model trains on labels up to the end of Y − 1, after the origin of targets in the first h − 1 weeks. <!-- src: R1_timing_leakage.md sections 1a, 1b --> After external review we therefore restricted every primary estimate to **origin-year rows**, whose origin lies in the target's epidemiological year (D24). This scoring filter removes both for all four models without refitting; it drops 4.8% of rows, and all rows form a sensitivity analysis. <!-- src: R1_timing_leakage.md section 1a table (4.79% pooled h{1,4}); docs/plans/deviations_from_protocol.md row 24 -->

Final revised counts, GHSL population up to a 2025 projection and a district universe defined with hindsight affect all four models alike; the AlphaEarth model was trained on imagery that includes our test years (layers released July 2025), which can only favour the embeddings. <!-- src: R8_literature.md section 4; R1_timing_leakage.md section 1c --> Held-out districts' 2018–2019 outcomes informed tuning in S2–S4 and their 2019 outcomes informed C\* selection in S2–S5, but no test-year outcome of a held-out district entered any fit. Supplement S1 lists what each model sees under each split (section A) and a fold-internal tuning check (section D). <!-- src: R1_timing_leakage.md section 0; RF_summary.md -->

<!--
FIGURE 1 SPEC (to be drawn). Title: "Study design and information timing". Three panels: A top-left, B top-right, C full-width bottom. Colour-blind-safe palette. No country maps (generic shapes only; this also avoids the CC BY-SA 2.0 Taiwan polygons).

Panel A, "What is compared".
- Left strip: a vertical ladder of five stacked boxes, bottom to top: "L0 seasonal naive", "L1 + case history", "L2 + weekly climate", "L3 + remote sensing and population", "L4 + AlphaEarth embedding". An arrow from the L3 box leads into the grid.
- Grid of four model boxes: rows "without embedding" (top) / "with embedding" (bottom); columns "no location control" (left) / "with location control C*" (right). Cells: top-left "L3", bottom-left "L4", top-right "L3 + C*", bottom-right "L4 + C*".
- Three labelled arrows: L3 -> L4 "embedding gain"; L3 -> L3 + C* "identity gain"; L3 + C* -> L4 + C* "excess gain (primary)", drawn thicker.
- Legend under the grid: "C* chosen at the 2019 origin from C1 historical risk, C2 coordinates, C3 shuffled embedding, C4/C4s random smooth fields, C5 2023 snapshot".

Panel B, "Where models are tested". Five small schematics in one row; each is a cluster of about 30 hexagons standing for districts (training = light grey, test = dark, dropped = white with dashed outline).
- "S1 new years": two stacked copies of the same cluster, all grey labelled "2018 to Y-1" and all dark labelled "year Y".
- "S2 held-out states": hexagons outlined in 5 state groups; one whole group dark.
- "S3 held-out buffered blocks": one compact block dark; a ring of white dashed hexagons around it labelled "buffer D (BR 225 km, CO 130 km)".
- "S4 held-out random districts": about 1 in 5 hexagons dark, scattered.
- "S5 held-out country": four separate clusters labelled BR, CO, PE, TW; one cluster dark.
- Note under the row: "S2-S4 in Brazil and Colombia; S1 and S5 in all four countries. Held-out districts keep their own lagged cases."

Panel C, "Information timing for one forecast". Horizontal axis in epidemiological weeks covering the last ~16 weeks of year Y-1 and the first ~10 weeks of year Y; a vertical line labelled "epidemiological year boundary".
- Origin o: vertical solid line labelled "forecast origin (end of week o)". Target t = o + h: a filled diamond; bracket "h = 1 to 4 weeks".
- Above the axis, bars ending at o: "case history, weeks o-11 to o"; "climate, weeks o-11 to o". Small marks one, two and three years back labelled "same week +/- 1, previous 3 years".
- A bar "remote sensing: last 3 complete months before the month of o".
- A box at the far left: "yearly inputs from year y-1 (AlphaEarth, population, night lights, built-up share); y = target's epidemiological year".
- Below the axis: a long bar "training targets: 2018 to last week of Y-1" ending at the year boundary.
- Shade the first h target weeks of Y light red, labelled "dropped from primary scoring: origin in Y-1 (yearly inputs or training labels after the origin)"; shade the rest of Y light green, labelled "origin-year rows (primary)".
- Inset, top-right of panel C: a year axis 2018 | 2019 | 2020 | ... | last test year, annotated "2019: tuning and C* selection (train 2018, validate 2019)" and "2020 to last: one refit per test year".
Caption, first sentence = takeaway: "Each comparison changes one block of inputs while the model, rows and configuration stay fixed; primary scores use only forecasts whose inputs and training labels end at the origin."
-->

### 2.7 Scoring

The primary score is the weighted interval score (WIS) [@bracher2021wis] on log(1 + cases) [@bosse2023transformed]. WIS rewards intervals that are narrow yet contain the observed value; for a point forecast it reduces to the absolute error. With median m and the K = 4 central intervals (20%, 40%, 60%, 80%) formed by the deciles,

```latex
\mathrm{WIS}(F, y) = \frac{1}{K + 1/2}\left(\frac{1}{2}\lvert y - m\rvert + \sum_{k=1}^{K}\frac{\alpha_k}{2}\,\mathrm{IS}_{\alpha_k}(F, y)\right),
\qquad
\mathrm{IS}_{\alpha}(F, y) = (u - l) + \frac{2}{\alpha}(l - y)_{+} + \frac{2}{\alpha}(y - u)_{+}
```

where l and u bound the central (1 − α) interval; lower is better. The four models in a comparison are scored on identical rows. Secondary measures are WIS on the case scale and coverage of the 40% and 80% intervals. Rows fall into three strata by target status (D26): weeks with cases, recorded zeros (listed by the source; Brazil 2020–2021 only) and zero-filled weeks. Strata depend on the outcome and are descriptive.

### 2.8 Estimands

Gains are differences in mean WIS, positive when the second model forecasts better, reported as a percentage of WIS(L3); because WIS(L3) differs widely between countries, absolute differences are reported beside them. The **embedding gain** is how much adding AlphaEarth improves L3:

```latex
G_{\mathrm{emb}} = \mathrm{WIS}(L3) - \mathrm{WIS}(L4)
```

The **identity gain** is how much the validation-selected location control alone improves L3:

```latex
G_{\mathrm{id}} = \mathrm{WIS}(L3) - \mathrm{WIS}(L3 + C^{*})
```

The **excess gain**, the primary estimand, is what the embeddings add when the model already knows where the district is:

```latex
G_{\mathrm{excess}} = \mathrm{WIS}(L3 + C^{*}) - \mathrm{WIS}(L4 + C^{*})
```

The ratio G_id / G_emb is reported only if G_emb's 95% interval excludes zero and G_emb is at least 1% of WIS(L3); it is descriptive, because in a nonlinear model the control and the embedding can interact. <!-- src: docs/methods/eval_library.md estimands.py; RESOLUTION_LOG.md section B -->

### 2.9 Statistical inference

For each target week we averaged the WIS difference over districts at each horizon, then over horizons 1 and 4, giving a weekly series d_t of length T (Table 1) whose mean is the estimate. <!-- src: src/pop/eval/estimands.py infer_estimand --> We applied the Diebold–Mariano (DM) test [@diebold1995comparing] to d_t with the equal-weighted cosine (EWC) long-run variance, fixed-b t critical values on B = ⌊0.4 T^(2/3)⌋ degrees of freedom [@lazarus2018har] and the Harvey–Leybourne–Newbold (HLN) correction at h = 4 [@harvey1997testing]. Intervals use the same standard error, so a 95% interval excludes zero exactly when p < 0.05. <!-- src: src/pop/eval/stats.py ewc_inference; T1_primary_family.csv df (BR 16, CO 11, PE 13, TW 16) --> Weeks are the sampling unit: inference concerns these districts, pipelines and seasons, not others.

The primary family is the excess gain in the 14 cells, with Holm's correction [@holm1979simple] (Holm over the 13 available cells; final m = 14 [[PENDING: final Holm m=14]]). Equivalence uses two one-sided tests (TOST) [@lakens2017equivalence] on the 90% interval with a margin of ±1% of WIS(L3), unadjusted and Holm-adjusted. On this scale the margin is about 0.0017–0.0019 in Brazil and 0.0002–0.0003 in Taiwan. <!-- src: T1_primary_family.csv WIS_ref (BR_S1 0.1675, BR_S5 0.1907; TW_S1 0.0312, TW_S5 0.0202) --> It was chosen after the Brazil and Peru S1 results (D9); it is below the smallest between-model WIS differences resolved in forecast-hub evaluations (about 1.6%) [@cramer2022covidhub], and margins of 0.5% and 2% are sensitivities. <!-- src: R8_literature.md section 2 --> Each cell gets a plain label combining both tests [@isager2026tst]. A loss (gain) is counted only when the excess gain is negative (positive) with Holm-adjusted p < 0.05, and called small inside ±1% (D27). Minimum detectable effects (80% power) are unadjusted; Holm-adjusted ones are about 1.34 times larger. <!-- src: src/pop/eval/stats.py ewc_inference; RC_summary.md "What population the inference refers to" --> Brazil S1 averages three seeds at horizons 1 and 4; other cells use one seed, so their intervals condition on one fit (D22).

**Robustness (D28).** Each cell also reports EWC with B = 4, a p-value calibrated on 2,000 zero-mean surrogates of d_t (windowed iterative amplitude-adjusted Fourier transform, IAAFT [@schreiber1996iaaft]), a delta-method interval treating WIS(L3) as estimated, the case scale, all rows, and the exclusions without Espírito Santo. <!-- src: docs/plans/deviations_from_protocol.md rows 28 and 34; scripts/analysis/rk_compute.py iaaft_pvalue --> In simulations calibrated to each cell, the primary test kept near-nominal size when d_t varies around a fixed mean but was oversized (10–22%) when multi-season drift is treated as noise (Supplement S1, section F). <!-- src: RC_summary.md verdict --> A 52-week block bootstrap [@kunsch1989jackknife; @politis1992circular] is descriptive only.

Exploratory supporting analyses (no multiplicity adjustment; D33) and Brazil S1 sensitivity analyses, including per-level tuning, origin-keyed yearly inputs and a two-week reporting delay ([[PENDING: sensitivities yref/delay2]]), are defined in Supplement S1, section F. <!-- src: docs/plans/deviations_from_protocol.md row 33; T6a_sensitivities.csv -->

### 2.10 No-case-history arm

With case history in the model, identity and place information cannot be told apart, so a secondary, exploratory arm in Brazil drops all 21 case-derived inputs (N3 and N4 are L3 and L4 without them). <!-- src: docs/methods/nohist_arm.md levels table (65 and 129 inputs) --> It runs S2 (its headline, because identifiers cannot transfer to unseen states) and S1, at horizons 1 and 4. C\* is chosen from target-free controls (C2, C3, C4, C4s, and C6 in S1; priority C3 > C2 > C6 > C4s > C4); C1 forms a separate "static history" rung. <!-- src: scripts/run/select_control.py PRIORITY_NOHIST --> The arm was pre-specified at commit bd3ba50, after the history-arm S1 results and before any of its runs was scored. It tests whether place descriptors add skill without case history; it does not identify an environmental mechanism or simulate partial or delayed surveillance.

### 2.11 Deviations from the original protocol

The original protocol (15 November 2026) fixed the ladder, splits, estimands, quantile set and log scale; all 34 later changes are dated in Supplement S1, section E. Eleven followed some S1 test-year results but preceded every spatial-split result (the last committed in e9df1f1, about three hours before the first). Eleven (D24–D34) followed external review, when every cell except Brazil S4 and the no-history arm had been seen. <!-- src: docs/plans/deviations_from_protocol.md header and last column (rows 2, 8, 9, 11, 12, 16, 18–22); git log: e9df1f1 2026-11-16 20:29 CST, 3ca02d7 2026-11-16 23:21 CST, f107238 2026-11-18 02:16 CST --> Four touch the headline: one configuration per country (D2), adopted after Brazil S1 showed a capacity effect several times the embedding effect; C\* rule v2 (D19); origin-year rows (D24); and the Espírito Santo exclusion (D34). The S1 cells are partly unblinded.
