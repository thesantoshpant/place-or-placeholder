# Brazil S1: Paper-1 estimands (L3 / L4 / L3+C* / L4+C*)

Runs: `runs/brazil_s1_L3` (L3, 31 leaves), `runs/brazil_s1_L4` (L4, 31 leaves), `runs/brazil_s1_L3_Cstar`
(L3+C1), `runs/brazil_s1_L4_Cstar` (L4+C1); C\* = C1 per `brazil_s1_control_selection.md`. LightGBM,
test years 2020–24, h1–h4.
Command:
`python scripts/run/estimands_report.py --l3 runs/brazil_s1_L3 --l4 runs/brazil_s1_L4 --l3c runs/brazil_s1_L3_Cstar --l4c runs/brazil_s1_L4_Cstar --ladder runs/brazil_s1_baselines runs/brazil_s1_timesfm_zs runs/brazil_s1_L2 runs/brazil_s1_L3_leaves127 --pairs lgbm-L3:lgbm-L2 lgbm-L3:lgbm-L3-leaves127 lgbm-L4:lgbm-L2 lgbm-L2:lgbm-L1 --out runs/brazil_s1_analysis --n-boot 2000`
(13 min; tables in `runs/brazil_s1_analysis/estimands_*.csv` and `estimands_tables.md`).

## Method
- Score: mean log1p WIS (median + deciles). Gains are positive when the second model has lower WIS:
  G_emb = L3 − L4, G_id = L3 − (L3+C1), G_excess = (L3+C1) − (L4+C1) (primary).
- CIs: `pop.eval.estimands.compute_estimands` → `stats.block_bootstrap_means`, 2,000 replicates.
  Each replicate draws the 27 states (adm1) with replacement and one set of circular 8-week blocks of
  target weeks shared by all states; the estimand is the row-level mean of the per-row gain; 95%
  percentile CI. All estimands and WIS(L3) come from the same replicates.
- DM: `stats.dm_test` on the per-target-week mean of the per-row gain (T = 261 weeks), EWC long-run
  variance (B = 16, t_16 reference) × HLN; Holm across the 4 horizons, separately per estimand.
- ID share = G_id / G_emb only if the G_emb CI excludes 0 and G_emb ≥ 1% of WIS(L3).
- Outbreak week: target cases ≥ max(unit p90 of weekly cases 2013–19 (panel; Brazil starts 2014), 5);
  8.0% of rows. zero_filled from the panel.

## Data integrity
All 10 compared models (4 estimand runs + 6 ladder models) have **identical row sets**: 5,759,748
rows each (2020: 1,169,604; 2021–24: 1,147,536 each), the same (unit, origin, target, horizon) keys in
every test year (0 mismatches vs L3), 0 duplicate keys, 0 NaN scores, `scores.parquet` = sum of the
chunk files for every LGBM run, 0 flag_gap weeks, every row matched to the panel with equal case counts.

## Main estimands (pooled 2020–24; log1p WIS; WIS(L3) h1–h4 = 0.1425 / 0.1644 / 0.1830 / 0.2009)

| h | G_emb [95% CI] | G_id [95% CI] | G_excess [95% CI] | G_excess % of WIS(L3) | DM p Holm (emb / id / excess) |
|---|---|---|---|---|---|
| 1 | +0.00009 [−0.00002, +0.00023] | −0.00020 [−0.00041, −0.00002] | +0.00019 [+0.00004, +0.00039] | 0.13% | 0.48 / 0.33 / 0.33 |
| 2 | +0.00031 [−0.00004, +0.00084] | −0.00013 [−0.00042, +0.00007] | +0.00030 [−0.00000, +0.00071] | 0.18% | 0.48 / 0.84 / 0.36 |
| 3 | +0.00056 [−0.00000, +0.00136] | −0.00005 [−0.00050, +0.00032] | +0.00057 [+0.00007, +0.00130] | 0.31% | 0.48 / 1.00 / 0.36 |
| 4 | +0.00072 [+0.00004, +0.00165] | −0.00004 [−0.00072, +0.00052] | +0.00072 [+0.00003, +0.00172] | 0.36% | 0.48 / 1.00 / 0.36 |
| all | +0.00042 [+0.00001, +0.00101] | −0.00011 [−0.00049, +0.00021] | +0.00045 [+0.00004, +0.00102] | 0.26% | – |

Raw DM p for G_excess: 0.083 / 0.135 / 0.119 / 0.161; for G_emb: 0.23 / 0.24 / 0.15 / 0.12.

**Per test year (pooled over h)**

| year | G_emb [CI] | G_id [CI] | G_excess [CI] | G_excess % |
|---|---|---|---|---|
| 2020 | +0.00011 [−0.00008, +0.00038] | +0.00036 [−0.00011, +0.00097] | +0.00004 [−0.00017, +0.00032] | 0.02% |
| 2021 | −0.00023 [−0.00052, +0.00000] | +0.00007 [−0.00024, +0.00037] | −0.00020 [−0.00054, +0.00000] | −0.18% |
| 2022 | +0.00024 [−0.00003, +0.00068] | −0.00009 [−0.00099, +0.00078] | +0.00025 [+0.00004, +0.00068] | 0.14% |
| 2023 | +0.00044 [−0.00008, +0.00121] | −0.00033 [−0.00098, +0.00010] | +0.00055 [+0.00003, +0.00130] | 0.32% |
| 2024 | +0.00155 [+0.00001, +0.00386] | −0.00055 [−0.00146, +0.00023] | +0.00161 [+0.00010, +0.00383] | 0.63% |

**ID share: not estimable anywhere.** h1–h3 and 2020–23: the G_emb CI includes 0; h4, pooled, and
2024: the CI excludes 0 but G_emb < 1% of WIS(L3) (0.36%, 0.24%, 0.61%).

## Strata (pooled over h and years unless stated)

| stratum | row share | WIS(L3) | G_emb [CI] | G_id [CI] | G_excess [CI] | share of total G_excess |
|---|---|---|---|---|---|---|
| observed | 0.47 | 0.323 | +0.00094 [−0.00009, +0.00233] | −0.00126 [−0.00281, −0.00027] | +0.00108 [+0.00006, +0.00242] | 1.14 |
| zero-filled | 0.53 | 0.040 | −0.00004 [−0.00037, +0.00039] | +0.00092 [+0.00027, +0.00161] | −0.00011 [−0.00042, +0.00024] | −0.14 |
| outbreak | 0.08 | 0.627 | +0.00378 [−0.00299, +0.00911] | −0.00608 [−0.00904, −0.00391] | +0.00396 [−0.00236, +0.00890] | 0.71 |
| non-outbreak | 0.92 | 0.133 | +0.00013 [−0.00006, +0.00037] | +0.00041 [+0.00013, +0.00070] | +0.00014 [−0.00006, +0.00037] | 0.29 |
| observed non-outbreak | 0.39 | 0.260 | +0.00036 [−0.00002, +0.00080] | −0.00027 [−0.00144, +0.00044] | +0.00048 [+0.00012, +0.00096] | 0.42 |
| 2024 all | – | 0.255 | +0.00155 [+0.00001, +0.00386] | −0.00055 [−0.00146, +0.00023] | +0.00161 [+0.00010, +0.00383] | – |
| 2024 observed | – | 0.545 | +0.00370 [−0.00065, +0.00900] | −0.00392 [−0.00599, −0.00222] | +0.00432 [+0.00031, +0.00893] | – |
| 2024 outbreak | – | 0.599 | +0.00750 [−0.00159, +0.01711] | −0.00575 [−0.00947, −0.00390] | +0.00816 [−0.00025, +0.01703] | – |

2024 by horizon (G_excess): +0.00063 / +0.00101 / +0.00200 / +0.00278 (h1–h4; all CIs exclude 0;
`estimands_strata.csv`).

## Ladder (pooled 2020–24, identical rows)

| model | h1 | h2 | h3 | h4 | mean | cov80 all | cov80 cases>0 | cov40 cases>0 |
|---|---|---|---|---|---|---|---|---|
| L0 naive | 0.4645 | 0.4645 | 0.4645 | 0.4645 | 0.4645 | 0.773 | 0.400 | 0.043 |
| L1 NB | 0.1894 | 0.2102 | 0.2279 | 0.2454 | 0.2182 | 0.938 | 0.762 | 0.355 |
| TimesFM 2.5 zero-shot | 0.1594 | 0.1829 | 0.2051 | 0.2252 | 0.1932 | 0.810 | 0.593 | 0.267 |
| L1 LGBM | 0.1414 | 0.1628 | 0.1813 | 0.1992 | 0.1711 | 0.907 | 0.677 | 0.312 |
| L2 LGBM | 0.1410 | 0.1621 | 0.1801 | 0.1975 | 0.1702 | 0.904 | 0.667 | 0.306 |
| L3 LGBM (31 leaves) | 0.1425 | 0.1644 | 0.1830 | 0.2009 | 0.1727 | 0.903 | 0.668 | 0.300 |
| L3 LGBM (127 leaves) | **0.1407** | **0.1615** | **0.1792** | **0.1962** | **0.1694** | 0.902 | 0.658 | 0.298 |
| L4 LGBM (31 leaves) | 0.1424 | 0.1641 | 0.1825 | 0.2001 | 0.1723 | 0.904 | 0.669 | 0.302 |
| L3+C1 | 0.1427 | 0.1645 | 0.1831 | 0.2009 | 0.1728 | 0.902 | 0.667 | 0.299 |
| L4+C1 | 0.1425 | 0.1642 | 0.1825 | 0.2002 | 0.1724 | 0.902 | 0.667 | 0.302 |

DM (d = WIS(A) − WIS(B), EWC + HLN, Holm over h within each pair), h1 / h2 / h3 / h4:

| A − B | mean d | p Holm |
|---|---|---|
| L3(31) − L2 | +0.0016 / +0.0023 / +0.0030 / +0.0033 | 0.039 / 0.059 / 0.077 / 0.077 |
| L3(31) − L3(127) | +0.0018 / +0.0029 / +0.0039 / +0.0047 | 0.010 / 0.011 / 0.012 / 0.012 |
| L4(31) − L2 | +0.0015 / +0.0020 / +0.0024 / +0.0026 | 0.030 / 0.030 / 0.053 / 0.053 |
| L2 − L1 | −0.0004 / −0.0007 / −0.0012 / −0.0016 | 0.109 (all h) |

## Takeaways (cautious)
- The primary estimand G_excess is positive at every horizon (+0.0002 to +0.0007 log-WIS, 0.13–0.36% of
  WIS(L3)), and the bootstrap CI excludes 0 at h1, h3, h4 and pooled, but **no DM test is significant**
  (Holm p ≥ 0.33; raw p 0.08–0.16). Read it as a very small, possibly real gain, not an established one.
- **The ID control does not explain the embedding gain:** G_id ≈ 0 (slightly negative; C1 makes L3 a
  little worse out of sample), so G_excess ≈ G_emb. The **ID share is not estimable** (G_emb < 1% of WIS(L3)
  where its CI excludes 0).
- **Where the gain lives:** observed (reported) weeks and outbreaks. Observed rows carry >100% of the
  total G_excess; zero-filled rows carry slightly negative gain. Outbreak weeks (8% of rows) carry ~71%;
  2024 (the epidemic year) gives the largest per-year gain (0.63% of WIS(L3), growing with h), and
  2021 (a quiet year) is slightly negative. Stratum CIs are wide (outbreak CIs include 0).
- C1 behaves as a level/ID feature: it helps on zero-filled and non-outbreak rows and hurts on observed
  and outbreak rows (G_id −0.006 on outbreaks), cancelling out overall.
- **Capacity confound:** the frozen 31-leaf L3/L4 are worse than L2 (127 leaves) and than L3 refit with
  127 leaves; the capacity effect (0.0018–0.0047) is ~5–20× G_emb and is significant at every h (Holm
  p ≤ 0.012). L4(31) is still worse than L2 (significant at h1–h2). So the RS layer plus the embedding
  do not beat climate-only L2 under the 2019-origin tuning. The estimands compare like with like (same
  params within each pair), but a sensitivity with 127 leaves for all four roles is advisable before
  the headline is fixed.
- The 2019-origin tuning chose 31 leaves for L3/L4 by a small margin on one year (L3 val pinball
  0.07369 vs 0.07374), and that choice reverses over 2020–24.
- Coverage is unchanged by any layer: all LGBM levels over-cover overall (~0.90 at 80%) and under-cover
  non-zero targets (0.66–0.68).
- Bootstrap CIs (state × 8-week blocks) are narrower than the DM tests imply (EWC with t_16 is
  conservative); where the two disagree we report both and lean on the DM result.
