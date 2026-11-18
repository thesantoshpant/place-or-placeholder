# Zero-fill cross-check, Brazil epi-year 2024 (extends `zero_fill_crosscheck.md`)

Script: `scripts/data/zero_fill_check_2024.py`. Log and outputs: `outputs/data_audit/brazil_infodengue_2024{.log,_merged.csv,_summary.csv}` and `outputs/data_audit/brazil_infodengue_es_2020_2024_{merged,summary}.csv`. Raw API responses are in `data/raw/infodengue/2024_check/`. Each of the 138 files is listed in `manifest.tsv` with its URL, UTC retrieval time, sha256, byte size, data rows and sample group, so a verifier can re-download and compare. The pulls ran on 2026-11-18.

## Method (same as the 2017–2023 check)
- **Reference:** the InfoDengue `alertcity` API, dengue, epi-weeks 1–53 of 2024, one sequential request per municipality with a 1.5 s pause and exponential-backoff retries. The comparison column is **`casprov` (probable)**, which is the series OpenDengue matches (see the earlier doc). `casos` (notified) is reported for context only.
- **OpenDengue side:** the zero-filled panel `data/processed/panel_weekly_v1.parquet`, Brazil, `year == 2024`. That is 52 Sunday-start weeks, 2023-12-31 to 2024-12-22, for 5,517 units; 60.6% of the rows are `zero_filled`. **Present** = `observed`. **Absent** = `zero_filled`. The InfoDengue `data_iniSE` value is a Sunday and joins 1:1 on (geocode, week start). Every InfoDengue `SE` is in 2024, and all panel rows matched.
- **Sample** (seed 20261118; the same groups as before plus a random group):
  - (a) 15 municipalities with no observed week in 2024 (301 such units exist).
  - (b) 15 municipalities with 4–44 observed weeks.
  - (c) the same 10 large cities.
  - (d) **20 municipalities drawn uniformly** from all 5,517. This group is new; it gives a representative estimate for the stratum.
- **Supplement:** all 78 Espírito Santo (ES) municipalities for 2020–2024. This was triggered by the result in group (a).
- OpenDengue V1.3.1 ends 2025-04-30. The panel and the test design stop at epi-year 2024, so 2025 was not checked.

## Results, 2024 sample (60 municipalities)

**Present weeks** (OpenDengue vs `casprov`):

| Group | Present weeks | ΣOD / Σcasprov | Median OD−casprov | Exact | Within ±1 | r |
|---|---|---|---|---|---|---|
| b partial | 336 | 0.993 | 0 | 83% | 94% | 0.999 |
| c large cities | 520 | 0.964 | −8 | 5% | 14% | 0.999 |
| d random | 502 | 0.940 | 0 | 73% | 86% | 0.999 |
| all | 1,358 | 0.964 | 0 | 49% | 60% | 0.999 |

These match the pattern for 2023. Small municipalities agree exactly or nearly so. In large cities OpenDengue is about 4% lower, consistent with *inferred* SINAN revisions after the snapshot. No present week has OD = 0.

**Absent (zero-filled) weeks:**

| Group | Absent unit-weeks | casprov > 0 | Max | Σcasprov | Σcasos |
|---|---|---|---|---|---|
| a absent all year | 780 | 70 (9.0%) | 48 | 653 | 2,456 |
| of which ES (2 municipalities) | 104 | 64 | 48 | 647 | 2,309 |
| a, excluding ES (13) | 676 | 6 (0.9%) | 1 | 6 | 147 |
| b partial | 444 | 7 (1.6%) | 3 | 11 | 454 |
| c large cities | 0 | – | – | – | – |
| d random | 538 | 12 (2.2%) | 3 | 17 | 423 |
| **all, excluding ES** | **1,658** | **25 (1.5%)** | **3** | **34** | 1,024 |

Outside ES, absent weeks in 2024 look like 2022–23: 1.5% of them have 1–3 probable cases, against 1.6% with 1–8 cases in 2022–23. Those weeks hold 34 cases, which is 0.002% of the sample's 1.50 M probable cases.

## Finding: Espírito Santo is missing from OpenDengue after 2020
OpenDengue V1.3.1 has **0 cases for all 78 ES municipalities after 2020-12-20**, so in the panel every ES week of 2021–2024 is zero-filled. InfoDengue `casprov` for the same units:

| Epi-year | ES zero-filled share | Zero-filled weeks with casprov > 0 | Σcasprov in zero-filled weeks | As share of BR OD total | ES share of BR zero-filled rows |
|---|---|---|---|---|---|
| 2020 | 81% | 853 | 7,650 | 0.8% | 4.4% |
| 2021 | 100% | 0 | 0 (casos 144) | 0 | 4.5% |
| 2022 | 100% | 73 | 481 (casos 21,583) | 0.03% | 1.9% |
| 2023 | 100% | 2,908 | 139,511 | 9.2% | 1.9% |
| **2024** | **100%** | **2,925 of 4,056 (72%)** | **166,407** | 2.6% | **2.3%** |

All 78 ES municipalities have probable cases in 2024 weeks that the panel scores as 0. *Inferred:* this matches ES's move off SINAN dengue reporting. InfoDengue's own `casprov` for ES is also near zero in 2021–22 even though `casos` is not, so neither source is complete for ES in those two years. The completeness rules in `completeness_v1.md` do not flag this gap, because they look for week-to-week dips and ES has been zero for 4 straight years. 2023 is a training year for the 2024 origin, so ES false zeros also enter the training targets.

## What it means for the Brazil 2024 zero-filled stratum
Outside Espírito Santo, a zero-filled 2024 week is a true zero about 98.5% of the time (otherwise it holds at most 3 probable cases). But the 78 ES municipalities (2.3% of 2024 zero-filled rows) are false zeros in 72% of their weeks, with 166k probable cases missing. So ES 2021–2024 should be excluded from scoring (and ideally from training targets), or rerun as a sensitivity analysis, before the zero-filled-week embedding harm is interpreted.
