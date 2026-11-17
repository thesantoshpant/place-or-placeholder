# Evaluation library (`pop.eval`)

## `scoring.py`
- `PRIMARY_QUANTILES` (0.1–0.9, i.e. 20/40/60/80% PIs plus the median) and `CDC_QUANTILES` (23 levels).
- `wis_interval(y, levels, values, log1p=False)`: WIS from Bracher et al. (2021, PLoS Comput Biol 17:e1008618):
  `WIS = [0.5|y−m| + Σ_k (α_k/2)·IS_αk] / (K+0.5)`, where `IS_α = (u−l) + (2/α)(l−y)+ + (2/α)(y−u)+`.
- `wis_quantile(...)`: the equivalent pinball form, `Σ_q (1{y<q}−τ)(q−y) / (K+0.5)`.
- Any symmetric level set that contains 0.5 works. A set that is not symmetric raises `ValueError`.
- NaN in the truth or in any quantile used gives a NaN score.
- Quantile crossing: values are sorted, and a `UserWarning` gives the count (`sort_crossing`).
- `log1p=True` transforms both the truth and the quantiles before scoring.
- `coverage(y, levels, values, level)`: closed interval [l,u].
- `score_forecasts(fc_long, truth, quantiles=PRIMARY_QUANTILES, scale="log"|"case", coverage_levels=(0.4,0.8))`:
  - Returns one row per forecast with columns `wis`, `ae_median` (on the chosen scale) and `cov_XX`.
  - Keys are all forecast columns except `quantile` and `value`, so `model` and `split` pass through.
  - Levels outside the requested set are ignored.
- `aggregate_scores(scores, by=("split","horizon","model"))` returns mean metrics plus `n` (the number of non-NaN WIS rows).

## `stats.py`
- `dm_test(d, h, lag=None)` runs the Diebold–Mariano test (1995) on `d_t = L_A − L_B`; `stat = HLN · d̄/se`, with `HLN = sqrt((T+1−2h+h(h−1)/T)/T)` (Harvey, Leybourne & Newbold 1997). Long-run variance via `lag`:
  - `None`/`"ewc"` (default): equal-weighted cosine estimator, `B = floor(0.4·T^(2/3))` terms (8 at T=104), p-value from t with B df (fixed-b; Lazarus, Lewis, Stock & Watson 2018).
  - `"nw"`: Newey–West Bartlett HAC, lag `max(h−1, floor(4(T/100)^(2/9)))` (NW 1994), t with T−1 df.
  - `"h-1"` or an int `L`: Bartlett HAC with lag `max(h−1, L)`, t with T−1 df; `se` then matches statsmodels HAC.
  - Returns a `DMResult(stat, p_value, mean_d, se, T, lag, hln_factor, method, df)`; `se` is uncorrected, `lag` is None for EWC.
  - Zero variance: stat=0 and p=1 if d̄=0; otherwise stat=±inf and p=0.
- `loss_diff_series(scores, A, B, metric="wis")`: per-week mean over units of `A−B` on common rows; filter to one horizon/split first.
- `block_bootstrap_means(df, cols, cluster_col="state", time_col="target_week", block_len=52, n_boot, seed, shared_time_blocks=True)`:
  - Draws clusters with replacement, then **circular** blocks of **52 weeks** (wrapping modulo T; Politis & Romano 1992; moving blocks: Künsch 1989). The default was 8 until 2026-11-16 (deviations row 11). With T = 209–261 weeks there are only 4–5 blocks, so percentile CIs are coarse. It is a sensitivity analysis only; the primary CI is the DM/EWC t-interval.
  - The statistic is the row-level mean; it equals the primary week-pooled mean only for a balanced panel with one horizon.
- `bootstrap_ci_mean` and `bootstrap_ci_ratio` (mean(num)/mean(den), using the same resamples) return percentile CIs.
- `holm(pvals)` gives Holm (1979) adjusted p-values and ignores NaN.

## `estimands.py` (positive = lower WIS)
- `select_best_control(val_scores, candidates)` picks C* as the candidate with the lowest mean WIS on common rows. Pass it validation data only.
- `gain_frame(scores, {"L3","L4","L3C","L4C"→model})`: inner join, then
  - `G_emb = L3−L4`
  - `G_id = L3−L3C`
  - `G_excess = L3C−L4C` (primary)
- `compute_estimands(g, ...)` returns joint bootstrap CIs for all gains and `WIS_L3`.
- `ID_share = G_id/G_emb` is reported only if:
  - the G_emb CI excludes 0, **and**
  - G_emb ≥ 1% of mean WIS(L3).
  
  Otherwise it is NaN with `reason="not estimable: …"` (logic in `id_share_gate`).
- **v2 (primary):** `seed_gain_frame(scores, models, seed_policy="common", on_mismatch="warn")` builds the row frame; `infer_estimand` / `compute_estimands_v2` give DM/EWC + HLN t-CIs, TOST (1% margin), MDE and the 52-week bootstrap sensitivity.
  - **Seeds (deviations row 22):** each estimand uses, per row, only the seeds present for both of its roles; a mismatch warns (or errors with `on_mismatch="error"`). `seed_spread` computes per-seed estimates and the seed SD only on rows where all those seeds exist (so h2/h3 rows with seed 0 only do not shrink it). The legacy rule (`seed_policy="fill"`) is kept for old reports.
  - **Strata (audit 4 M3):** stratum estimates (observed, zero-filled, outbreak, …) use the same week-pooled estimator on the stratum's rows, so every week has equal weight whatever its number of stratum rows. They are not row-weighted and are not shares of the overall gain.

Note: null size at nominal 5% (1000 seeded AR(1) reps, h=1): φ=0.5, T=104 — EWC 6.9%, `"nw"` 10.8%, `"h-1"` 27.5%; φ=0, T=104 — EWC 5.8%; φ=0.5, T=260 — EWC 5.7%. Power for a 0.3-SD shift (φ=0.5, T=104): EWC 35% (size-adjusted 31% vs 36% for NW). Weekly WIS differences are autocorrelated, so keep the EWC default.
