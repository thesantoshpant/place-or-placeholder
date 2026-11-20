# Round-3 analyses (R3-A1 to A8): summary

Script: `scripts/analysis/round3_analyses.py`. Scoring follows kit v3: exclusions_v2, the origin-year row filter, horizons h{1,4} pooled, and DM/EWC + HLN inference. The run covers 13 cells; Brazil held-out districts (S4) is excluded because it is still blinded. Unless a table says otherwise, numbers are % of the reference WIS (WIS of L3, or of L3+C\* where stated), with 95% CIs and two-sided p.

**Check:** `tmp/round3_analyses/load_check.csv` shows that the rebuilt G_excess and row counts equal T1 exactly in all 13 cells.

**Caveats that apply to every section:**
- **Post hoc.** All of these analyses were specified after the primary results were read (TRIAGE_round3 section B). They are exploratory, and their p values are not corrected beyond what each table states.
- **COVID.** The test years 2020–21 are COVID-affected: reporting fell and dynamics were unusual. Taiwan had no local cases in 2021.
- **Seeds.** Every cell except Brazil new years (S1, 3 seeds) is a single seed. Seed SD (about 0.0001–0.0003 log-WIS) is of the same order as many of the estimates.
- **Outcome-conditioned subsets.** Strata such as case weeks, zero weeks and "district-years with at least one case" condition on the outcome. They describe where the differences sit, not a forecastable subgroup.
- **Taiwan 2021.** Primary Taiwan cells include 2021. The A1 ladder for Taiwan does not include it (the needed L1/L2 runs do not exist yet). Including 2021 makes Taiwan estimates more negative (new years −0.44 → −0.60; held-out country −11.2 → −17.3).

Cell names: S1 new years, S2 held-out states, S3 held-out regions, S4 held-out districts, S5 held-out country.

---

## A1: covariate ladder as a positive control and margin anchor (`R3_A1_positive_control.csv`)
**What was computed.** For each new-years (S1) cell, the gain from each covariate step was tested with DM/EWC + HLN, using shared-parameter runs and L3/L4 seed-averaged. The steps are L1→L2 (climate), L2→L3 (remote sensing and population), L1→L3, and L3→L4 (embedding, no control).

| Cell | L1→L2 climate | L2→L3 RS + pop | L1→L3 all non-case | L3→L4 embedding | Primary G_excess | ±1% ÷ (L1→L3 gain) |
|---|---|---|---|---|---|---|
| Brazil new years (S1) | **+0.57 [+0.03, +1.12] p .041** | **+0.52 [+0.18, +0.86] p .005** | **+1.09 [+0.44, +1.74] p .003** | +0.26 [−0.31, +0.82] p .35 | +0.23 | 0.92 |
| Colombia new years (S1) | +0.14 [−0.14, +0.42] p .29 | **+0.30 [+0.02, +0.59] p .041** | +0.45 [−0.06, +0.95] p .080 | **−0.36 [−0.58, −0.13] p .005** | −0.39 | 2.25 |
| Peru new years (S1) | +0.44 [−1.48, +2.37] p .63 | −0.27 [−1.04, +0.50] p .46 | +0.17 [−1.84, +2.19] p .86 | **−0.94 [−1.70, −0.18] p .020** | −0.70 | 5.76 |
| Taiwan new years (S1)\* | −0.93 [−2.43, +0.58] p .21 | +0.06 [−0.59, +0.71] p .85 | −0.87 [−2.51, +0.78] p .28 | **−0.94 [−1.85, −0.03] p .043** | −0.60 (−0.44 w/o 2021) | not defined (L1→L3 < 0) |

\*Taiwan ladder without 2021; the primary G_excess includes 2021.

**Answers.**
- **Did any non-case covariate step improve skill significantly?** Yes, but only in Brazil, plus one step in Colombia. In Brazil, climate (+0.57%, p .041), RS + pop (+0.52%, p .005) and their sum (+1.09%, p .003) all helped. In Colombia only RS + pop did (+0.30%, p .041). Peru and Taiwan showed no significant step, and Taiwan's point estimates were negative. None of these p values is multiplicity-adjusted, and the two p = .04 results would not survive a correction across 16 tests. The design can detect a covariate block of about 0.5–1% in Brazil, but not reliably elsewhere.
- **How big is ±1% against the L1→L3 gain?** The margin is 0.92× Brazil's whole non-case covariate gain, 2.25× Colombia's and 5.8× Peru's. Taiwan's L1→L3 step is a loss, so it gives no anchor. A ±1% margin is therefore as large as, or larger than, everything that climate, remote sensing and population together add to case history.
- **Is G_excess smaller than, or comparable to, the climate gain?** Comparable in size. In Brazil, G_excess (+0.23) is about 40% of the climate gain (+0.57), or 0.21× the L1→L3 gain. In Colombia, G_excess (−0.39) is larger in magnitude than the climate gain (+0.14, ns) and of opposite sign. In Peru and Taiwan the climate step itself is not distinguishable from zero.

**Interpretation.** Climate and remote sensing produce gains of the same order (0.1–1%) as the embedding effects, so "equivalent within ±1%" does not rule out an embedding effect as large as an established covariate block. The positive control works in Brazil, which shows the test has some power there. Elsewhere the covariate steps are themselves unresolved, so a null embedding result in Peru or Taiwan says little.

---

## A2: "no control" rule (`R3_A2_nocontrol_rule.csv`)
**What was computed.** Under this rule, C\* = none unless a control beat plain L3 at the 2019 origin by more than 2 SE (seed-noise SE from selection.json). Cells without a control use G_emb instead of G_excess. Holm correction is over 13 cells.

Only Brazil new years (C1) and Colombia held-out country (C2) keep a control.

| Cell | Estimand under rule | Estimate [95% CI] | p | Holm p | Primary G_excess (Holm p) |
|---|---|---|---|---|---|
| Brazil new years (S1) | G_excess (C1) | +0.23 [−0.33, +0.79] | .39 | 1.0 | +0.23 (.80) |
| Brazil held-out states (S2) | G_emb | −0.02 [−0.34, +0.30] | .88 | 1.0 | −0.00 (1.0) |
| Brazil held-out regions (S3) | G_emb | −0.13 [−0.35, +0.09] | .22 | 1.0 | −0.16 (.40) |
| Brazil held-out country (S5) | G_emb | −0.34 [−1.24, +0.56] | .44 | 1.0 | **−0.60 (.001)** |
| Colombia new years (S1) | G_emb | **−0.36 [−0.58, −0.13]** | .005 | **.046** | −0.39 (.012) |
| Colombia held-out states (S2) | G_emb | **−0.59 [−0.80, −0.37]** | <.001 | **.001** | −0.47 (.007) |
| Colombia held-out regions (S3) | G_emb | **−0.83 [−1.14, −0.52]** | <.001 | **.001** | −0.65 (.026) |
| Colombia held-out districts (S4) | G_emb | **−0.52 [−0.75, −0.28]** | .001 | **.005** | −0.43 (.025) |
| Colombia held-out country (S5) | G_excess (C2) | +0.22 [−0.19, +0.63] | .27 | 1.0 | +0.22 (.80) |
| Peru new years (S1) | G_emb | −0.94 [−1.70, −0.18] | .020 | .16 | −0.70 (.34) |
| Peru held-out country (S5) | G_emb | +0.68 [−0.59, +1.96] | .27 | 1.0 | +0.96 (.40) |
| Taiwan new years (S1) | G_emb | −1.06 [−1.96, −0.16] | .024 | .17 | −0.60 (.34) |
| Taiwan held-out country (S5) | G_emb | **−21.6 [−31.8, −11.4]** | <.001 | **.004** | −17.3 (.017) |

The G_id 95% CI lies entirely below 0 in Colombia S2, S3, S4 and S5, Peru S5 and Taiwan S5; there, the control alone hurts.

**Interpretation.** No cell shows a gain under either rule. The Brazil held-out-country loss exists only beside the shuffled-embedding control (C3): without a control it is −0.34% (p .44). The Colombian losses get larger and stay Holm-significant without a control, so they are not an artefact of the control choice.

---

## A3: gains by test year and trend with training length (`R3_A3_per_year.csv`, `R3_A3_trend.csv`)
**What was computed.** G_excess and G_emb were estimated per test year. Each cell's per-year estimates were then regressed on the number of training years (WLS, weights 1/SE², 3–5 points per cell), and a DM test was run on 2023–24 rows only for the Brazil cells.

**Per-year G_excess, Brazil** (% [95% CI]):

| Cell | 2020 | 2021 | 2022 | 2023 | 2024 |
|---|---|---|---|---|---|
| Brazil new years (S1) | −0.22 [−0.66, 0.23] | **−0.67 [−1.33, −0.02]** | +0.12 [−0.06, 0.29] | +0.42 [−0.38, 1.21] | +0.88 [−0.93, 2.69] |
| Brazil held-out states (S2) | −0.38 [−0.89, 0.14] | **−0.77 [−1.25, −0.29]** | **−0.07 [−0.13, −0.01]** | +0.32 [−0.38, 1.02] | +0.41 [−0.51, 1.32] |
| Brazil held-out regions (S3) | **−0.19 [−0.34, −0.04]** | **−0.97 [−1.58, −0.35]** | −0.05 [−0.26, 0.16] | +0.05 [−0.37, 0.47] | +0.02 [−0.34, 0.38] |
| Brazil held-out country (S5) | −0.56 [−1.19, 0.08] | **−1.67 [−2.24, −1.09]** | **−0.65 [−1.20, −0.11]** | −0.48 [−1.20, 0.24] | −0.23 [−0.66, 0.21] |

Colombia (2020–22) is negative in almost every cell-year and shrinks toward 0 by 2022. Taiwan's per-year percentages are unstable (e.g. new years 2021 −86%) because the reference WIS is tiny in low-incidence years.

**Trend in pp per extra training year (G_excess).** "Known-SE" uses the per-year SEs as given. "Scaled" inflates them by the residual over-dispersion.

| Cell | Slope | p (known SE) | p (scaled) | Slope excl. 2020–21 | p (scaled) |
|---|---|---|---|---|---|
| Brazil new years (S1) | +0.24 | .003 | .12 | +0.34 | .39 |
| Brazil held-out states (S2) | +0.28 | <.001 | .096 | +0.28 | .31 |
| Brazil held-out regions (S3) | +0.06 | .037 | .37 | +0.04 | .69 |
| Brazil held-out country (S5) | +0.22 | .001 | .26 | +0.21 | .36 |
| Colombia new years (S1) | +0.17 | .024 | .26 | – | – |
| Colombia held-out states (S2) | +0.14 | .065 | .32 | – | – |
| Colombia held-out regions (S3) | +0.10 | .54 | .65 | – | – |
| Colombia held-out districts (S4) | +0.25 | .002 | .20 | – | – |
| Colombia held-out country (S5) | −0.12 | .26 | .79 | – | – |
| Peru new years (S1) | +0.52 | .096 | .24 | – | – |
| Peru held-out country (S5) | −0.28 | .54 | .60 | – | – |
| Taiwan new years (S1) | +3.10 | .12 | .39 | −1.70 | .70 |
| Taiwan held-out country (S5) | +5.81 | .081 | .63 | −15.5 | .57 |
| Pooled, 12 cells (excl. TW S5) | +0.13 | <.0001 | n/a | | |

G_emb behaves the same way: the pooled slope is +0.16 (known-SE p <.0001), and no single cell is significant with the scaled SE.

**DM test on 2023–24 only, Brazil:**

| Cell | G_excess 2023–24 | p (B=4 p) | G_emb 2023–24 | p |
|---|---|---|---|---|
| Brazil new years (S1) | +0.69 [−0.40, +1.78] | .18 (.23) | +0.68 [−0.45, +1.81] | .20 |
| Brazil held-out states (S2) | +0.37 [−0.20, +0.94] | .17 (.23) | +0.31 [−0.28, +0.90] | .26 |
| Brazil held-out regions (S3) | +0.03 [−0.18, +0.24] | .74 (.74) | +0.11 [−0.23, +0.44] | .48 |
| Brazil held-out country (S5) | **−0.33 [−0.64, −0.01]** | .043 (.049) | +0.04 [−1.68, +1.77] | .95 |

**Answers.**
- **Is there a significant upward trend?** Not once over-dispersion is allowed for. With the per-year SEs taken at face value, 6 of 13 cells (and the pooled slope) have a significant positive slope. With the scaled SE, no cell does (smallest p .096). After dropping 2020–21, no cell does either, and Taiwan's slopes turn negative. The pooled p ignores the fact that cells in a country share test years and data, so it is anti-conservative.
- **2023–24 DM test in Brazil:** no significant gain in any cell; the largest is new years, +0.69% (p .18). With Brazil held out, the loss persists (−0.33%, p .043), although G_emb there is ~0.

**Interpretation.** The positive slopes come mainly from losses in 2021 (and 2020), the COVID-affected years with the shortest training windows. Training length and COVID are fully confounded, with 3–5 points per cell. The data are consistent with "the harm fades after 2021" but do not support "embeddings improve as the training window grows".

---

## A4: equivalence under different margins and variances (`R3_A4_equivalence.csv`)
**What was computed.** TOST at ±0.5, ±1 and ±2% of WIS(ref) on 90% CIs, with the primary EWC variance and with the cautious EWC B=4 variance, unadjusted and Holm over 13 cells.

**Number of cells (of 13) that are equivalent:**

| Estimand | Margin | EWC unadj. | EWC Holm | B=4 unadj. | B=4 Holm |
|---|---|---|---|---|---|
| G_excess | ±0.5% | 2 | 2 | 2 | **0** |
| G_excess | ±1% | 9 | 8 | 9 | **6** |
| G_excess | ±2% | 12 | 11 | 12 | 12 |
| G_emb | ±0.5% | 3 | 2 | 3 | 0 |
| G_emb | ±1% | 7 | 7 | 8 | 6 |
| G_emb | ±2% | 12 | 10 | 11 | 10 |

At ±1%, G_excess:
- **Equivalent under all four variants:** Brazil S2, S3 and S5, and Colombia S1, S2 and S4.
- **Lose equivalence under B=4 + Holm:** Brazil S1 and Colombia S5. Colombia S3 already loses it under EWC + Holm.
- **Never equivalent:** Peru S1, Peru S5, Taiwan S1 and Taiwan S5.

At ±0.5%, only Brazil S2 and S3 are equivalent (EWC), and none survives B=4 + Holm.

**Interpretation.** "Equivalent" depends on both the margin and the variance estimator. At ±1%, the robust core is six cells. Four of these six are significantly *negative* (Brazil S5, Colombia S1, S2, S4), so "equivalent" here means "a loss smaller than 1%", not "no effect". Equivalence within ±0.5% cannot be claimed for any cell under the cautious variance.

---

## A5: "as planned" versus "as reported" (`R3_A5_planned_vs_reported.csv`)
**What was computed.** The reported primary G_excess was set beside variants that restore planned settings: per-level tuning, all rows (no origin-year filter), exclusions v1, the rule-v1 C\* (where recorded or runnable), h1–h4 pooled, single seed, Taiwan without 2021, and the B=4 variance.

**Cells where a conclusion changes** (G_excess % [95% CI], p):

| Cell | Reported primary | Variant | Value under variant |
|---|---|---|---|
| Peru new years (S1) | −0.70 [−1.41, +0.02] p .056 | per-level tuning | **+0.65 [−0.49, +1.79] p .24** (sign flips) |
| Taiwan new years (S1) | −0.60 [−1.20, −0.00] p .049 | per-level tuning | −0.14 [−0.38, +0.10] p .23 |
| | | B=4 / all rows / h1–h4 / no 2021 | p .10 / .076 / .15 / .12 (nominal loss lost) |
| Peru held-out country (S5) | +0.96 [−0.13, +2.05] p .079 | B=4 variance | **+0.96 [+0.22, +1.70] p .023** |
| | | all rows | **+1.01 [+0.02, +2.00] p .046** |
| Brazil held-out regions (S3) | −0.16 [−0.34, +0.03] p .09 | exclusions v1 (Espírito Santo kept) | **−0.19 [−0.37, −0.01] p .045** |
| Taiwan held-out country (S5) | −17.3 [−27.0, −7.6] | without 2021 | −11.2 [−15.7, −6.7] (still significant loss) |

**Stable across every variant:**
- Brazil new years stays at +0.23 to +0.26 and non-significant (single seed +0.25, p .37; per-level +0.25, p .11; h1–h4 +0.25, p .38).
- Brazil held-out states stays at ~0.
- The losses in Brazil S5 and Colombia S1–S4 stay negative with p ≤ .016 in every variant, B=4 included.
- Colombia S5 stays at +0.18 to +0.22, non-significant.

Exclusions v1 is identical to the primary outside Brazil. The rule-v1 C\* was the same control as rule v2 where recorded, and was not recorded for most spatial cells. Brazil S5's rule-v1 control (C4) has no valid run. Taiwan S1 under rule-v1 C3 gives −0.54 (fixed-control panel, without 2021). The no-control rule (A2) is a further variant that removes the Brazil S5 loss.

**Interpretation.** The headline conclusions survive: no gain in Brazil new years, and small losses in Colombia. Three things are fragile:
- The **sign of the Peru new-years estimate depends on the tuning choice**, the same capacity confound first seen in Brazil.
- The nominal Taiwan new-years loss disappears under almost any planned setting.
- Peru held-out country moves between "inconclusive" and a nominally significant gain (still not Holm-significant) depending on the variance estimator or row filter.

---

## A6: outcome-agnostic checks (`R3_A6_outcome_agnostic.csv`)
### (a) District-years with at least one reported case
**What was computed.** G_excess and G_emb restricted to district-years with at least one case in that test year. This drops always-zero district-years. Rows kept: Brazil 81%, Colombia 71%, Peru 76%, Taiwan 19%.

| Cell | G_excess, case years | p | Primary G_excess | G_emb, case years | p |
|---|---|---|---|---|---|
| Colombia new years (S1) | **−0.30 [−0.48, −0.12]** | .004 | −0.39 | **−0.25 [−0.46, −0.04]** | .023 |
| Colombia held-out states (S2) | **−0.28 [−0.48, −0.08]** | .010 | −0.47 | **−0.39 [−0.57, −0.20]** | .001 |
| Colombia held-out regions (S3) | −0.30 [−0.66, +0.06] | .092 | −0.65 | **−0.47 [−0.76, −0.17]** | .005 |
| Colombia held-out districts (S4) | **−0.28 [−0.49, −0.06]** | .016 | −0.43 | **−0.37 [−0.58, −0.17]** | .002 |
| Colombia held-out country (S5) | +0.28 [−0.08, +0.65] | .12 | +0.22 | −0.00 [−0.31, +0.31] | .99 |
| Brazil held-out country (S5) | **−0.37 [−0.61, −0.13]** | .005 | −0.60 | −0.07 [−0.90, +0.75] | .85 |
| Taiwan held-out country (S5) | **−3.36 [−4.70, −2.02]** | <.001 | −17.3 | **−5.11 [−7.17, −3.05]** | <.001 |
| Peru held-out country (S5) | +1.04 [−0.09, +2.17] | .068 | +0.96 | +0.78 [−0.51, +2.08] | .21 |

Brazil S1, S2 and S3 stay within ±0.25% and non-significant. Peru new years: −0.65 (p .069). Taiwan new years: −0.63 (p .23).

**Answer.** Yes, Colombia still loses in district-years with cases. G_excess is about −0.3% (significant in S1, S2 and S4), and G_emb is significant in S1–S4. The loss shrinks by roughly a third to a half, so part of it, but not all, sits in always-zero district-years. Taiwan held-out country falls from −17% to −3.4%: most of that loss is in district-years without cases.

### (b) 80% coverage and interval width, L4+C\* minus L3+C\*
**What was computed.** Week-weighted differences in 80% coverage and in mean 80% interval width (log1p scale), separately on case weeks (y>0) and zero weeks (y=0).

| Cell | Case-week cov80, L3+C\* | Δ cov80, case weeks (pp) | Δ width, zero weeks (log) | Δ width, case weeks (log) |
|---|---|---|---|---|
| Brazil new years (S1) | .663 | −0.2 (p .31) | **+0.006** (+1.8%) | −0.004 |
| Brazil held-out states (S2) | .662 | **−0.5 (p .011)** | **+0.010** (+2.9%) | **−0.008** |
| Brazil held-out regions (S3) | .656 | +0.2 (p .088) | **+0.027** (+7.9%) | +0.003 |
| Brazil held-out country (S5) | .634 | +0.7 (p .11) | **+0.043** (+9.7%) | **+0.023** |
| Colombia new years (S1) | .713 | −0.0 (p .95) | **+0.017** (+5.3%) | +0.000 |
| Colombia held-out states (S2) | .710 | −0.8 (p .15) | **+0.019** (+5.9%) | −0.014 |
| Colombia held-out regions (S3) | .708 | **−0.9 (p .013)** | **+0.025** (+7.2%) | **−0.011** |
| Colombia held-out districts (S4) | .710 | −0.5 (p .33) | **+0.017** (+5.3%) | −0.006 |
| Colombia held-out country (S5) | .751 | +0.2 (p .29) | **+0.007** (+2.2%) | −0.007 |
| Peru new years (S1) | .669 | +0.6 (p .082) | **+0.036** (+14%) | **+0.016** |
| Peru held-out country (S5) | .652 | **+2.4 (p <.001)** | **+0.017** (+6.6%) | **+0.053** |
| Taiwan new years (S1) | .241 | −1.6 (p .43) | +0.002 (p .15) | −0.007 |
| Taiwan held-out country (S5) | .566 | +3.0 (p .21) | **+0.099** (+61%) | **+0.077** |

Bold = 95% CI excludes 0. Percentages are relative to the L3+C\* zero-week width.

**Answer.** On case weeks, every model under-covers (24–75% against a nominal 80%). The embedding moves case-week coverage toward nominal significantly in only one cell, Peru held-out country (+2.4 pp). It moves coverage away from nominal significantly in two cells (Brazil S2 and Colombia S3, about −0.5 to −0.9 pp), and in the rest the change is ≤ ±3 pp and not significant. The cost is consistent: zero-week intervals widen in 12 of 13 cells (all but Taiwan new years) by about +2% to +14%, and by +61% in Taiwan held-out country. Zero weeks are already over-covered (about 96–100%), so this widening adds no useful coverage. On case weeks, the intervals mostly get narrower or stay the same.

**Interpretation.** The embedding does not fix the under-coverage in epidemic weeks. Its main effect on the intervals is extra upper-tail width where nothing happens, which matches the mechanism found earlier (q0.9 on zero rows rises in 12/13 cells). The Peru held-out-country gain coincides with a real coverage gain on case weeks, bought with wider intervals on both case and zero weeks.

---

## A7: embedding stability (`R3_A7_embedding_stability.csv`)
**What was computed.** Cosine similarity of the renormalised, population-weighted district means. It was compared across three pairings: the same district in consecutive years, the 5 nearest spatial neighbours (same year), and random district pairs.

| Country | Within district, consecutive years (median) | Within district, first vs last year (median) | 5 nearest neighbours (median) | Random pairs (median) | Own next-year vector is nearest of all districts | Own next-year cos > all 5 neighbours |
|---|---|---|---|---|---|---|
| Brazil | 0.982 | 0.958 | 0.974 | 0.70 | 57% | 87% |
| Colombia | 0.976 | 0.940 | 0.931 | 0.64 | 84% | 95% |
| Peru | 0.985 | 0.973 | 0.912 | 0.49 | 94% | 98% |
| Taiwan | 0.978 | 0.972 | 0.971 | 0.88 | 69% | 89% |

**Interpretation.** In Brazil and Taiwan, a district's vector changes from year to year by about as much as the gap to its neighbours. Its next-year vector is its own nearest match only 57% and 69% of the time, so the y−1 embedding is a noisy identifier there. In Colombia and Peru the embeddings identify districts well (84–94%). Year-to-year drift is a candidate explanation for small harms in Brazil and Taiwan: the model may learn district-specific splits that shift with noise. It does not explain Colombia, where identification is strong and losses are clearest. Variant V3 (causal static embedding) tests this directly.

---

## A8: IAAFT-calibrated equivalence (`R3_A8_iaaft_equivalence.csv`)
**What was computed.** The 9 cells that were equivalent at ±1% (EWC, unadjusted) were re-checked. For each, 2,000 null surrogates of its weekly loss-difference series were drawn by IAAFT. These gave the empirical size of the nominal 5% test and a calibrated 90% CI, which was then compared with ±1% and ±0.5%. No Holm adjustment.

| Cell | Size at nominal 5% (EWC / B=4) | Calibrated 90% CI (EWC) | ±1% | ±0.5% |
|---|---|---|---|---|
| Brazil new years (S1) | **18.4% / 12.5%** | [−0.62, +1.08] | **No** | No |
| Brazil held-out states (S2) | 14.0% / 5.0% | [−0.38, +0.38] | Yes | Yes |
| Brazil held-out regions (S3) | 15.2% / 5.0% | [−0.37, +0.05] | Yes | Yes |
| Brazil held-out country (S5) | 0.9% / 3.7% | [−0.75, −0.45] | Yes | No |
| Colombia new years (S1) | 5.7% / 3.4% | [−0.55, −0.22] | Yes | No |
| Colombia held-out states (S2) | 1.1% / 2.0% | [−0.60, −0.34] | Yes | No |
| Colombia held-out regions (S3) | 0.6% / 1.5% | [−0.85, −0.45] | Yes | No |
| Colombia held-out districts (S4) | 6.8% / 3.3% | [−0.66, −0.21] | Yes | No |
| Colombia held-out country (S5) | 15.8% / 6.8% | [−0.27, +0.71] | Yes | No |

**Answer.** Under IAAFT calibration, equivalence at ±1% drops from 9 to 8 cells: Brazil new years drops out, because its calibrated CI reaches +1.08%. At ±0.5% the count stays at 2 (Brazil S2, S3).

**Interpretation.** The primary EWC + HLN test is oversized (14–18%) in four cells: Brazil S1, S2, S3 and Colombia S5. In those cells the CIs should be about 1.35–1.85× wider. In the cells with clear losses, the test is conservative (size ≤ 7%), so those losses are not an artefact of an oversized test. Brazil new years, the one cell with a positive point estimate, can therefore not be called equivalent within ±1%: neither a gain nor equivalence is established.
