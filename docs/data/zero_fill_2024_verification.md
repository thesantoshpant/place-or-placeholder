# Independent verification of `zero_fill_crosscheck_2024.md` (2026-11-18)

Verifier script: `scripts/data/verify_zero_fill_2024.py` (`download`, `es`, `scan`). It was written independently and does not reuse `zero_fill_check_2024.py`. Re-downloads and analysis outputs are in `data/raw/infodengue/2024_check_verify/` (logs and CSVs under `analysis/`; new downloads are listed in `manifest_verify.tsv`, with the sha256 of each). A few extra checks were run inline; their outputs are `analysis/es_2020_od_vs_infodengue.csv`, `admin2_vs_national_by_year.csv`, `admin1_year_posunit_flags.csv` and `admin1_zero_week_runs.csv`.

## Verdicts

| Task | Verdict |
|---|---|
| 1. Download integrity | **PASS** |
| 2. Espírito Santo (ES) defect | **CONFIRMED, and it is larger than reported.** The gap starts at epi-year 2020, not after 2020-12-20. |
| 3. Scan for similar defects | **PASS.** ES is the only structural defect. Every other flag is a genuine low year or a true zero. |
| 4. Exclusion rule | Given below. |

## 1. Download integrity: PASS
- **Sample:** a stratified 20% re-download, rounding up within each group. That gave 28 of 138 files: a 3, b 3, c 2, d 4, e 16. The four named ES cities were forced into group e. Seed 990101. Requests were sequential with a 1.5 s pause.
- **Results:** for all 28 files, the manifest sha256 matches the original file on disk, **and the re-downloaded file is byte-identical** (sha256 equal).
  - Row counts are equal and match the manifest.
  - There are 0 week mismatches in `casprov`, `casos` and `casconf`.
  - No data revisions were seen between the two pulls on the same day.
- **Caveat:** the `cols_differing` column in `download_compare.csv` is a comparison artifact and should be ignored. The sha256 values are identical.

## 2. Espírito Santo: CONFIRMED, with a correction
**OpenDengue V1.3.1 raw data** (Temporal and Spatial extracts give identical results):
- ES Admin2/Week rows run from 2013-12-29 to **2020-12-27**. The last week with a positive count is 2020-12-20.
- After that date, ES has no rows at any resolution. There is also no ES Admin1 series after 2005, and the National extract has no ES rows. **OpenDengue therefore has no source of ES data for 2021–2024.**
- **The gap starts a year earlier than reported.** 63 of the 78 municipalities have their last row on **2019-12-22**. Only 15 municipalities have 2020 rows: 780 rows, all explicit, with 732 of them equal to 0.
- In those 15 municipalities the 2020 values are not credible apart from Vitória. Examples, OpenDengue vs InfoDengue `casprov` for 2020:

| Municipality | OpenDengue 2020 | InfoDengue `casprov` 2020 |
|---|---|---|
| Cariacica | 4 | 1,929 |
| Serra | 71 | 4,472 |
| Vitória | 7,370 | 10,751 |

- Totals over the 78 ES files for 2020:
  - the 15 municipalities with rows: OpenDengue 7,562 vs `casprov` 27,077;
  - the other 63: OpenDengue 0 vs `casprov` 7,650.

**Panel (`panel_weekly_v1.parquet`):**
- In 2020 ES has 795 observed and 3,339 zero-filled rows.
- In 2021–2024 every one of its 4,056 rows per year is zero-filled, with 0 cases.
- The state-year case total for 2020 (7,562) looks normal only because Vitória carries it. The positive-unit count collapses from a median of 67 to 15.

**InfoDengue re-query** (16 ES municipalities, including Vitória, Vila Velha, Serra and Cariacica; epi-years 2020–2024): there are real cases in every year except 2021. Examples of `casprov` for 2024:

| Municipality | `casprov` 2024 |
|---|---|
| Vitória | 20,905 |
| Serra | 20,095 |
| Vila Velha | 17,000 |
| Cariacica | 11,148 |

The 2023 values are similar. In 2021–22, `casprov` is about 0 while `casos` is not (Vitória 2022: 96 vs 2,540). So the original doc is right that neither source is complete for ES in those years.

**The other claims in the original doc are consistent** with the re-downloaded files, which are byte-identical: outside ES, present weeks give ΣOD/Σ`casprov` = 0.964 with r = 0.999, and 1.5% of zero-filled weeks hold 1–3 cases. I did not recompute the per-group table.

## 3. Admin1-year scan (panel, 2014–2024 within each country's window)
**Rules:**
- **A:** cases are below 5% of the unit's own median over its other years, with that median ≥ 20.
- **B:** there are 0 observed rows, with a median ≥ 100.
- **C:** the unit's share of the country total is below 5% of its usual share, with a median ≥ 100.
- **D** (extra): the number of municipalities with any positive count is below 25% of its median over the other years.
- **E** (extra): a run of ≥ 4 weeks in which the whole state reports 0, in a state-year with ≥ 500 cases.

43 state-years were flagged under rules A–C (`analysis/admin1_year_flags.csv`). Colombia had none.

| Country | Admin1 | Year(s) | Cases (median of other years) | Verdict |
|---|---|---|---|---|
| BR | **Espírito Santo** | **2020** (rule D: 15 vs 67 positive units; rule E: 16-week zero run) | 7,562 (8,914) | **DEFECT** (see section 2) |
| BR | **Espírito Santo** | **2021, 2022, 2023, 2024** | 0 each (8,914) | **DEFECT**: no source data |
| BR | Amapá | 2020 | 69 (1,079) | Genuine. Macapá: OpenDengue 37 vs InfoDengue `casprov` 29 (re-queried). |
| BR | Paraná | 2017 / 2018 | 2,227 / 1,424 (54,373) | Genuine low years. Brazil's own totals fell in 2017–18, and the state's share of the national total is 0.10–0.17 of usual, not near 0. |
| BR | Rio Grande do Sul | 2014 / 2018 | 151 / 128 (3,587) | Same as Paraná. RS has historically had little dengue. |
| BR | Santa Catarina | 2014 / 2017 / 2018 | 138 / 191 / 185 (8,519) | Same. Its epidemics began only after 2015. |
| BR | São Paulo | 2017 | 9,459 (282,332) | National low year, so genuine. |
| PE | Áncash | 2014, 2020 | 0, 0 (118) | Plausible true zeros. The 2000–13 history has years with 0–8 cases. |
| PE | Ayacucho | 2014 | 0 (782) | Plausible. Dengue there began in 2015; 2000–13 is all 0. |
| PE | Ica | 2014 / 2015 / 2018 / 2019 | 0 / 3 / 127 / 51 (4,208) | Plausible. Ica had no dengue before 2016. |
| PE | Piura | 2019 / 2020 | 70 / 125 (7,610) | Probably genuine. Piura swings widely (2004: 37, 2018: 525). **Not independently sourced.** The 2020 national-minus-Admin2 gap is 7.8k, so a partial Piura gap cannot be excluded. |
| PE | Cajamarca 2018; Cusco 2019; Huánuco 2018–19; La Libertad 2018; Lambayeque 2018; Lima 2014, 2015, 2018; San Martín 2018; Tumbes 2018; Puno 2015–18 (median 20) | | Small counts | 2018 was a national low year (Peru Admin0: 6.9k). Treated as genuine. |
| TW | Kaohsiung 2017, 2020–21; Tainan 2017–18, 2020–22; New Taipei 2016, 2021–22 | | 0–18 | Genuine. Taiwan was validated exactly against CDC local cases (`zero_fill_crosscheck.md`), and 2021 had 0 local cases. |

**Cross-check against national totals.** OpenDengue has no Brazil Admin1 series after 2005, so states can only be checked through the national Admin0 total. The Admin2/national ratio for Brazil is about 1.0 in 2014–15 and 0.47–0.69 in 2016–24, with no step in 2020–21. This is a case-definition gap that `completeness_v1.md` already covers. ES is about 2.5% of Brazil's cases, so it is invisible at national level, which is why only the state-level scan finds it.

Peru's ratio is 0.68–1.00 in every year, and Colombia's is 0.94–1.02. Taiwan has no national series for 2020 onward.

**Rule E outside ES:** the zero-week runs in Peru (Áncash, Callao, Huánuco, Lambayeque, Lima, Tumbes; 4–10 weeks) and Taiwan (16–24 weeks) are off-season gaps in coastal or seasonal regions. Taiwan's are CDC-validated.

## 4. Recommended exclusion rule
- **Units:** all 78 Brazilian municipalities with `unit_id` matching `^32\d{5}$` (Espírito Santo).
- **Dates:** `week_start >= 2019-12-29`, which is epi-year 2020 onward, through the end of the panel.
- **Scope:**
  - Drop these rows from scoring and from training targets in every split, setting them like `flag_gap`.
  - Also mask them as lag and history inputs. Their lagged cases are false zeros, so set them to NaN rather than 0.
  - Leave ES 2014–2019 in.
  - C1's pre-2018 means are unaffected.
- **Do not back-fill from InfoDengue.** `casprov` for ES is about 0 in 2021–22 even though `casos` is not, so there is no consistent replacement series.
- **Why the start date is 2019-12-29 and not 2020-12-20:** 63 of 78 units have no 2020 rows at all. The other 14 units with rows, leaving out Vitória, report 192 cases against 16,326 InfoDengue `casprov` (about 1%); Vitória reports 69%. Excluding only 2021+ would leave 2020 (a test year) with false zeros.
- **Sensitivity option:** keep Vitória 2020 (3205309). This is not recommended.
- No other exclusions are needed. Piura 2019–20 could be checked against a MINSA/CDC-Perú source if a reviewer asks.
