# RF: fold-internal re-tuning check (S2-S4, Brazil and Colombia)

**Question (reviewer):** S2-S4 reuse the S1 LightGBM tuning (origin 2019, all units). That tuning saw the held-out units' 2018 (train) and 2019 (validation) outcomes. Would tuning on each fold's training units alone have picked the same parameters?

**Method.** `scripts/analysis/tuning_fold_check.py` reruns the same search as `runner.tune`. It uses the same grid (num_leaves {31,127} x min_data_in_leaf {100,1000}; lr 0.05, 400 rounds, other params fixed), level L1, horizons {1,4}, quantiles {0.1,0.5,0.9}, metric (mean pinball loss on log1p) and seed 0. Each fold uses only its training units: it trains on their 2018 targets and validates on their 2019 targets. Held-out units and S3 buffer units contribute no rows. No test-year forecasts were made. Fits ran single-threaded; the forest is deterministic across thread counts.

**Reproduction check.** The S1 reruns over all units reproduce the stored `runs/<c>_s1_baselines/tuning_lgbm-L1.csv` to every printed digit (BR 127/100 = 0.0740640; CO 31/100 = 0.0703860).

Raw results (4 grid rows per fold): `RF_tuning_fold_check.csv`. In the table below, "gap" is the validation loss of the S1 parameters minus the fold's own best, as a % of the fold's best. "margin" is the fold's best vs its runner-up.

| Country | Split | Fold | Train units | Fold best | S1 choice | Same? | Best val | S1-param val | Gap % | Margin to 2nd % |
|---|---|---|---|---|---|---|---|---|---|---|
| CO | S2 | 0-4 | 856-857 | 31/100 | 31/100 | yes (5/5) | .0671-.0780 | same | 0 | 1.14-1.60 |
| CO | S3 | 0-5 | 528-1038 | 31/100 | 31/100 | yes (6/6) | .0593-.0780 | same | 0 | 0.63-1.75 |
| CO | S4 | 0-4 | 856-857 | 31/100 | 31/100 | yes (5/5) | .0687-.0715 | same | 0 | 1.07-2.01 |
| BR | S2 | 0 | 4414 | 31/100 | 127/100 | no | .07187 | .07227 | 0.56 | 0.56 |
| BR | S2 | 1 | 4416 | 127/100 | 127/100 | yes | .06590 | .06590 | 0 | 0.04 |
| BR | S2 | 2 | 4427 | 31/100 | 127/100 | no | .08433 | .08448 | 0.17 | 0.17 |
| BR | S2 | 3 | 4393 | 31/100 | 127/100 | no | .07292 | .07317 | 0.34 | 0.34 |
| BR | S2 | 4 | 4418 | 31/100 | 127/100 | no | .07727 | .07746 | 0.24 | 0.24 |
| BR | S3 | 0 | 3771 | 31/100 | 127/100 | no | .06481 | .06505 | 0.37 | 0.37 |
| BR | S3 | 1 | 4124 | 31/100 | 127/100 | no | .08605 | .08630 | 0.29 | 0.29 |
| BR | S3 | 2 | 3648 | 31/100 | 127/100 | no | .06699 | .06728 | 0.43 | 0.43 |
| BR | S3 | 3 | 3631 | 31/100 | 127/100 | no | .06733 | .06804 | 1.05 | 1.05 |
| BR | S3 | 4 | 3891 | 31/100 | 127/100 | no | .07582 | .07610 | 0.37 | 0.37 |
| BR | S4 | 0 | 4413 | 127/100 | 127/100 | yes | .07405 | .07405 | 0 | 0.01 |
| BR | S4 | 1 | 4413 | 31/100 | 127/100 | no | .07393 | .07409 | 0.21 | 0.21 |
| BR | S4 | 2 | 4414 | 127/100 | 127/100 | yes | .07464 | .07464 | 0 | 0.07 |
| BR | S4 | 3 | 4414 | 31/100 | 127/100 | no | .07498 | .07506 | 0.11 | 0.11 |
| BR | S4 | 4 | 4414 | 31/100 | 127/100 | no | .07436 | .07455 | 0.26 | 0.26 |

(Colombia per-fold values are in the CSV. min_data_in_leaf = 100 is chosen in every fold of both countries.)

**Verdict.**

*Colombia:* every fold (16/16) picks the S1 parameters 31/100, with a 0.6-2.0% margin, so the exposure is inert there.

*Brazil:* 12/15 folds would have picked num_leaves 31 instead of the S1 choice of 127. S1 itself separated the two settings by only 0.29% (.07406 vs .07428), so the choice sits on a nearly flat ridge. The S1 parameters are 0.11-1.05% worse in fold-internal validation (median 0.32%; 1.05% only in S3 fold 3). That bounds the tuning-exposure effect on absolute WIS at about 1%, typically 0.3%.

For the L3-vs-L4 contrasts, the effect is likely smaller still. Both rungs share the parameters, and in BR S1 the estimand barely moved between 31 and 127 leaves (G_excess +0.26% at 31/100 per-level vs +0.27% at 127/100 shared, both pooled h1-4). That comparison is from S1, not S2-S4. If certainty is wanted for BR S2-S4, rerun them with 31/100.
