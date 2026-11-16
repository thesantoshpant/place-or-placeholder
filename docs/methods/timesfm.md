# TimesFM 2.5 zero-shot (model 4 base)

Code: `src/pop/models/timesfm_zs.py`, `scripts/run/run_timesfm_zs.py`, `tests/test_timesfm_zs.py`. Outputs: `runs/brazil_s1_timesfm_zs/` (the Y=2023 pilot is in `pilot_2023/`).

**Versions.** Checkpoint `google/timesfm-2.5-200m-pytorch` (Apache-2.0). Package `timesfm==2.0.2`, which provides the 2.5 API; we avoid 3.x because the 3.0 weights are non-commercial. Also `torch==2.14.1+cu130` on an RTX A6000 (driver 595, CUDA 13.2). torch.compile is off because the server has no Python headers, so we run in eager mode. We did not use the HF Transformers `timesfm2_5` port.

**Input.** Each series is log1p(cases) for one unit, using every week from 2013-12-29 up to and including the origin (at most 573 weeks, max_context = 576). Config: `normalize_inputs`, continuous quantile head, flip invariance, `infer_is_positive` and `fix_quantile_crossing`. We keep the deciles 0.1–0.9 for h = 1–4, sort them and clip at ≥ 0. `value` is expm1 of the log1p decile (case scale, as in the other models) and `value_log` is kept. Origins are every week whose h = 1..4 targets fall in test year Y (S1: all 5,517 units, purely temporal), and each target year is forecast once. Flag_gap targets are excluded from scoring. A test confirms that values after the origin have no effect.

**Runtime.** 1.52 M series (5 × ~303k), batch 1024: about 1,170 series/s, about 260 s per year and about 22 min in total including scoring. Peak GPU memory is 8.1 GB.

**Results** (mean log1p WIS):

| Year | h1 | h2 | h3 | h4 |
|---|---|---|---|---|
| 2020 | 0.139 | 0.156 | 0.172 | 0.186 |
| 2021 | 0.107 | 0.118 | 0.129 | 0.137 |
| 2022 | 0.167 | 0.193 | 0.216 | 0.238 |
| 2023 | 0.158 | 0.176 | 0.194 | 0.211 |
| 2024 | 0.227 | 0.272 | 0.315 | 0.356 |
| **Pooled** | **0.159** | **0.183** | **0.205** | **0.225** |

Pooled 40%/80% coverage by horizon: 0.61/0.83, 0.68/0.83, 0.54/0.76 and 0.64/0.82. Exact-zero targets (74% of rows) cover easily because the clipped intervals include 0. Non-zero targets are under-covered (about 0.26/0.59), so the intervals are too narrow during epidemics. Coverage on zero targets swings from one horizon to the next, which comes from the model's quantile head near zero. 2024, Brazil's record epidemic, is the hardest year.
