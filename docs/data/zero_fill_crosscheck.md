# Zero-fill cross-check: does a missing OpenDengue V1.3.1 Admin2 week mean zero cases?

Scripts: `scripts/data/crosscheck_brazil_infodengue.py` and `scripts/data/crosscheck_taiwan_cdc.py`. Outputs and logs are in `outputs/data_audit/`. Reference files are in `data/reference/{infodengue,taiwan_cdc}/` and listed in `manifests/reference_files.tsv`.

## Brazil vs InfoDengue (`alertcity`, 40 municipalities, 2017/2019/2022/2023)

- OpenDengue `IBGE_code` uses the **7-digit** geocode, the same code the API expects (5,517 municipalities).
- InfoDengue `data_iniSE` is the Sunday that starts the epi week, so it lines up 1:1 with `calendar_start_date` (checked with an assert).
- Sample (seed 20261115): (a) 8 municipalities absent for all of 2017 and 7 absent for all of 2022; (b) 15 present in 2022 with 4–44 weeks; (c) 10 capitals.

**Which InfoDengue column matches?** OpenDengue matches `casprov` (**probable**), not `casos` (notified). In capitals, exact agreement with `casos` is 0–0.4% of weeks, and the OD/`casos` ratio is about 0.43–0.63.

| Year | Present weeks | Median OD−casprov | ΣOD / Σcasprov | Exact (capitals) |
|---|---|---|---|---|
| 2017 | 1,218 | 0 | 1.008 | 58% (78% within ±1) |
| 2019 | 1,507 | 0 | 1.003 | 52% (70%) |
| 2022 | 795 | 0 | 1.020 | 22% (37%) |
| 2023 | 849 | −1 | 0.939 | 8% (19%) |

Weekly correlation is ≥0.97 in every group. For the small municipalities, exact agreement is 79–100%. *Inferred:* the small differences, which are larger in 2023, come from SINAN revisions after the OpenDengue snapshot.

**Absent weeks (InfoDengue probable counts):**

| Year | Absent unit-weeks | casprov>0 | max | Σcasprov | Σcasos (notified) |
|---|---|---|---|---|---|
| 2017 | 902 | 0 | 0 | 0 | 9 |
| 2019 | 573 | 0 | 0 | 0 | 3 |
| 2022 | 1,285 | 14 (1.1%) | 4 | 26 | 544 |
| 2023 | 1,231 | 26 (2.1%) | 8 | 58 | 579 |

Municipalities absent for a whole year (group a) have 0 probable cases in 2017 and 2022. Notified cases can be non-zero in absent weeks (Curitiba 2023: up to 27 notified, at most 1 probable). This is expected, because the series counts probable cases.

**Verdict, Brazil:** within 2014–2023 (measured for 2017, 2019, 2022 and 2023), an absent row means **0 probable cases**. Rows were dropped for municipality-years with zero cases (≤2021) and for zero weeks (≥2022). The 40 absent weeks in 2022–23 with 1–8 probable cases are close to zero. *Inferred:* they are later revisions, not reporting gaps. 2024 was not checked.

## Taiwan vs Taiwan CDC `Dengue_Daily.csv`

`od.cdc.gov.tw` cannot be reached from epyc2 (the connection times out), so I used the Wayback snapshot of 2025-07-29: 107,387 confirmed cases, 1998 to 2025-07, sha256 `8eaebe6b…e6ad5d`.

| Series × date | Weekly national exact | Σ 1998–2024 |
|---|---|---|
| **local, onset** | **83.7%**, r = 1.0000 | 102,302 vs OD 101,892 |
| local, notification | 10.3% | 102,303 |
| local, confirmation | 6.2% | 96,287 |
| local + imported, onset | 8.2% | 107,271 |

- OpenDengue Taiwan = **locally acquired confirmed cases, by onset date, by residence township**. Imported cases are excluded.
- The 410-case gap is entirely local cases with a blank residence county in the CDC file: 1998–2010, of which 217 are in 2002. OpenDengue drops them. They cannot be assigned to a township.
- The OD↔CDC township crosswalk was **inferred** by assignment within each county that maximises shared cases. It is not a verified name match. It reproduces 100% of OD cases.
- Unit-weeks: **7,673/7,673 present unit-weeks match exactly**. **0** unit-weeks absent from OD have CDC local cases > 0.
- **2021: 0 local cases** (12 imported), so OD's missing year is a true zero. 2017 = 10 local, 2022 = 20, 2025 (to July) = 0.
- **287 townships ever had a local case**, exactly the 287 OD units. 338 had any case including imported ones. *Inferred:* the other ~81 of ~368 townships (total not measured here) are structural zeros for local cases.

| Year | OD | CDC local (onset week) | CDC imported |
|---|---|---|---|
| 2014 | 15,506 | 15,506 | 239 |
| 2015 | 43,467 | 43,467 | 365 |
| 2021 | 0 | 0 | 12 |
| 2023 | 26,462 | 26,462 | 278 |
| 2024 | 222 | 222 | 269 |

**Verdict, Taiwan:** zero-filling is exact for 1998–2024 at township × Sunday-week, for all ~368 townships. The only non-zero "absent" mass is the 410 early local cases with no residence location. These are national-level only, and 2002 is the main year affected (217 of 5,330 local cases, 4%).
