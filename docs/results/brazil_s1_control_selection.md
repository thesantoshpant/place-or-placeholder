> **SUPERSEDED (2026-11-16).** These runs use per-level tuned params (31 leaves), the old per-year C3 permutation and C4 at 8,483 km only, and the old "lowest mean WIS" rule. The primary Brazil S1 cell uses shared L1 params (`runs/brazil_s1_shared_controls_2019`), fixed-permutation C3, C4s, and selection rule v2 (deviations rows 2, 13, 15, 19). This selection is kept only as part of the per-level-tuning sensitivity (audit 3 M-5); it is not rerun.

# Brazil S1: choice of the ID control C* (2019 origin)

Runs: `runs/brazil_s1_controls_2019` (config `configs/brazil_s1_controls_2019.yaml`), 96 chunks, and
the leak-free C1 rerun `runs/brazil_s1_controls_2019_C1fix` (config
`configs/brazil_s1_controls_2019_C1fix.yaml`, only L3+C1, same params_from).
Selection: `python scripts/run/select_control.py runs/brazil_s1_controls_2019
runs/brazil_s1_controls_2019_C1fix --replace lgbm-L3+C1`
(writes `selection.csv`, `selection.json`, `selection.md` in the C1fix run dir; the old C1 row is kept
as "superseded" and is not eligible).

Setup: LightGBM quantile, train targets 2018, test 2019 only; all runs reuse the frozen L3
hyperparameters (`runs/brazil_s1_L3/tuning_lgbm-L3.json`: num_leaves 31, min_data_in_leaf 100), so
the runs differ only in the control block. C3/C4: 10 seeds (seed = control draw and LightGBM seed);
the others seed 0. Score = mean log1p WIS over all 2019 unit-weeks, pooled over h1-h4
(1,147,536 rows per run x seed; identical row sets across runs).

| Run | log-WIS (pooled) | seed SD | h1 | h2 | h3 | h4 | cov 40 | cov 80 | vs L3 |
|---|---|---|---|---|---|---|---|---|---|
| **L3+C1** (target encoding, pre-training years; C1fix) | **0.17462** | - | 0.14281 | 0.16570 | 0.18574 | 0.20423 | 0.779 | 0.888 | −0.00062 |
| L3 (reference) | 0.17524 | - | 0.14283 | 0.16602 | 0.18638 | 0.20572 | 0.781 | 0.889 | 0 |
| L3+C3 (shuffled AE) | 0.17550 | 0.00010 | 0.14298 | 0.16612 | 0.18669 | 0.20621 | 0.781 | 0.887 | +0.00026 |
| L3+C5 (AE 2023 static) | 0.17599 | - | 0.14321 | 0.16655 | 0.18738 | 0.20681 | 0.782 | 0.884 | +0.00075 |
| L3+C2 (spatial basis) | 0.17647 | - | 0.14339 | 0.16699 | 0.18783 | 0.20767 | 0.779 | 0.885 | +0.00123 |
| L3+C4 (random field) | 0.17649 | 0.00017 | 0.14336 | 0.16691 | 0.18790 | 0.20781 | 0.780 | 0.884 | +0.00126 |
| L3+C1 (target encoding, training targets) — *leaky, superseded* | 0.26314 | - | 0.22454 | 0.25507 | 0.27506 | 0.29789 | 0.739 | 0.815 | +0.08791 |

C3 seed range 0.17527-0.17561; C4 seed range 0.17614-0.17675.

## Decision (revised 2026-11-16 after the C1 leakage fix)

**C\* = C1** (leak-free). Its pooled log-WIS 0.17462 is below C3 (0.17550; gap 0.00088 ≈ 9 seed
SDs of C3) and below plain L3 (−0.00062), and it is lowest at h2–h4 (h1 ties L3 and beats C3).
C1 is deterministic given the data, so one run is used; its LightGBM-seed noise is not measured,
but for C3 it is ~0.0001, an order of magnitude below the gap.

C1 rule (`controls.c1_source_rows`, `c1_period="auto"` → `"pre_train"` under S0/S1): unit mean of
log1p(cases) over the panel years before the first training target year (Brazil 2014–2017),
flag_gap weeks dropped; the same value for training and test rows and for every origin.

Main runs (2020-24 x h1-h4, 1 seed): `configs/brazil_s1_L3_Cstar.yaml` -> `runs/brazil_s1_L3_Cstar`
(L3 params, level `L3+C1`) and `configs/brazil_s1_L4_Cstar.yaml` -> `runs/brazil_s1_L4_Cstar`
(L4 params, level `L4+C1`). The earlier C\* = C3 configs are kept as
`configs/brazil_s1_L{3,4}_Cstar_C3.yaml`; their partial 10-seed runs (stopped at relaunch) are in
`runs/brazil_s1_L{3,4}_Cstar_C3_partial`.

Superseded decision: C\* = C3 (lowest among the controls while C1 was leaky).

## Notes

- **Every control except the leak-free C1 is worse than plain L3 at the 2019 origin**: with one training
  year, C2-C5 add nothing beyond L1-L3; the pre-training level C1 helps slightly (−0.0006).
- **Old C1 (leaky, superseded; +0.088).** In S1 every unit is seen, so the old C1 = the unit's own
  mean over the training targets (2018). Each training row's feature contained its own target
  (in-sample target encoding), the model over-relied on it, and it did not transfer to 2019. Fixed
  by computing C1 from the pre-training years (see Decision; `docs/methods/controls.md`). The old
  rule is still available as `c1_period="train"`.
- `select_control.py` logic checked: rejects any test_year other than 2019; averages per (run, seed)
  first, then over seeds; equal row counts per run x seed. Ties are broken by sort order (stable),
  and there is no near-tie rule; with these numbers none is needed.
