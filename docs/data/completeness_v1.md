# Weekly completeness check v1 (zero-filled Admin2 panel)

Script: `scripts/data/completeness_check.py` (about 1 min; reads `panel_weekly_v1.parquet` and the OpenDengue V1.3.1 Temporal and National extracts already on disk; no new downloads). Outputs are in `data/processed/exclusions_v1/`: the three exclusion files plus `diag_*.csv` (all weekly ratios, yearly summaries and test-row shares).

## References available
| country | reference series (OpenDengue V1.3.1) | usable for |
|---|---|---|
| BR | Admin0 weekly, "Total" (WHO/PAHO), 2014–24 | country × week |
| CO | Admin0 weekly, "Total" (PAHO), 2014–24 | country × week. The Admin1 weekly series (2007–19) has only 3–39 matched department-weeks per year, and its sums are 6–112× *below* Admin2, so it is not a reference. |
| PE | Admin0 weekly, "Total" (PAHO), 2014–24. Admin0 weekly "Probable and confirmed" (National extract), 2000–13. Admin1 weekly "Probable and confirmed", 2007–13 | country × week; same-definition check; department × week (pre-2014 only) |
| TW | Admin0 weekly is 0 in every week, so it is unusable | none here. The Taiwan CDC cross-check (`zero_fill_crosscheck.md`) already matches all 7,673 township-weeks exactly, with 0 cases in absent weeks. |

No Admin1 weekly reference exists in any test year. Admin1 × week therefore uses an internal test (below).

## Coverage ratio = Σ Admin2 / national, by year (weeks with national ≥ 20)
| year | BR sum (wk median; p10–p90) | CO sum (median) | PE sum (median; p10–p90) |
|---|---|---|---|
| 2014 | 1.00 (1.00) | .99 (.99) | .91 (.86; .63–2.28) |
| 2015 | 1.03 (1.01) | .99 (.99) | .86 (.88) |
| 2016 | .68 (.58; .42–.72) | .99 (.99) | .79 (.77) |
| 2017 | .48 (.47) | .99 (.99) | .90 (.81) |
| 2018 | .57 (.55) | .97 (.95) | .54 (.54; .30–2.06) |
| 2019 | .69 (.65) | .97 (.97) | .89 (.77) |
| 2020 | .65 (.57; .39–.71) | .98 (.96) | .85 (.91; .76–.98) |
| 2021 | .56 (.52; .43–.61) | .94 (.94) | .91 (.94; .86–.96) |
| 2022 | .59 (.49; .36–.69) | .96 (.93) | .87 (.86; .74–.97) |
| 2023 | .49 (.43; .29–.55) | – | .94 (.92; .84–.96) |
| 2024 | .63 (.49; .29–.68) | – | – |

- **Brazil:** there is a definitional break in 2016. In 2014–15 the national weekly series equals the Admin2 "Probable" sum; from 2016 on it behaves like notified cases ("Total"). After the break the ratio is **strongly seasonal in every year**: about 0.6–0.7 in the epidemic peak (epi-weeks 1–24) and 0.29–0.44 in epi-weeks 33–48. The late-2024 values (0.28–0.40) match 2022–23 for the same weeks (2023: 0.29 in weeks 33–44). The audit's "drop from 0.63 to 0.33–0.40" compares off-season weeks with an annual ratio that the peak dominates, so it is not evidence of truncation. Admin2 counts in Dec 2024 rise in step with national (6.7k → 16.8k/week). The one residual signal: 2024 weeks 50–52 (0.39–0.40) sit below 2021–23 for those weeks (0.53–1.16), at 0.41–0.56 of the seasonal reference. These are flagged for *sensitivity* only.
- **Colombia:** the ratio is ≈1 and stable (2020–22 weekly p10 ≥ .79).
- **Peru:** the ratio is noisy before 2020 (timing shifts; 2018 has a PAHO-side anomaly with ratios up to 54). In the test years 2020–23 it is stable at 0.85–0.94 (weekly CV 0.06–0.15).

## Rule (pre-stated; primary k = 0.5, sensitivity k = 0.4 / 0.6)
1. **Country × week** (BR, CO, PE; national ≥ 20). The seasonal reference is the median ratio over the previous 3 epi-years, epi-weeks ±2 (≥ 5 values). A week is flagged when **ratio < k × seasonal reference AND ratio < k × the same epi-year's median ratio**.
   - *Why seasonal:* a "first 40 weeks" or annual median would flag every Brazilian off-season week, because the offset is seasonal.
   - *Why the AND:* the seasonal-only variant (written as `country_seasonal_only`, sensitivity) flags all of Brazil 2016–17 after the definition break, plus Peru 2020-04 weeks with a ratio of 0.96, so it is too fragile to be primary.
2. **Admin1 × week** (all countries, all years). A week is flagged when x_t < k × min(mean of the 2 weeks before, mean of the 2 weeks after), and that minimum is ≥ 50 cases. The first and last 2 weeks of data cannot be evaluated. If the national series dips the same way that week, the flag becomes `adm1_dip_reference_also_dips`, i.e. sensitivity only.
   - Of the Brazil dips, 68 are this kind. They all fall in the Christmas/New Year week, where PAHO dips too (to 0.05–0.42 of its neighbours). They reflect surveillance as a whole, not a gap in Admin2.
   - Taiwan acts as a specificity check (CDC-verified, no true gaps): 0 flags in 96 evaluable state-weeks.
3. **Peru department × week, 2007–13** (`pe_adm1_direct`). A week is flagged when the Admin1 reference is ≥ 20 and the ratio is < k × that department-year's median ratio.

`action = exclude` for primary rules flagged at k ≤ 0.5; everything else is `sensitivity`. `strictest_k` gives the smallest k that flags the row.

## Flags in the test years
| country (test years) | exclude (k=0.5) | rows / cases | k=0.4 | k=0.6 primary | + all sensitivity flags: rows / cases |
|---|---|---|---|---|---|
| BR 2020–24 | none | 0 / 0 | none | 2 state-weeks (0.02% / <0.01%) | 1.67% / 0.45% (2024-12-08..22 country, plus year-end holiday dips) |
| CO 2020–22 | none | 0 / 0 | none | 2021-06-20 country + Córdoba 2022-01-16 (0.65% / 0.32%) | same |
| PE 2020–23 | Junín 2020-12-27, Ucayali 2023-07-23 | 0.03% / 0.02% | none | + Ucayali 2023-10-22 (0.05% / 0.03%) | 1.96% / 1.19% |
| TW 2020, 22–24 | none (no national reference; CDC-verified) | 0 / 0 | – | – | 0 / 0 |

Country-level primary flags since 2014: **only Peru 2018-07-01 and 2018-08-12** (ratio 0.18 and 0.14), plus Peru 2017-07-16, 09-03 and 09-10. The old `flag_gap` caught only 2018-08-12.

## Peru zero-fill check
- **Same definition, national, 2000–13:** Σ Admin2 / Σ national "Probable and confirmed" = 1.00 (2000, 2001, 2009); 0.87–0.97 (2007, 2008, 2011–13).
- **Same definition, department × week, 2007–13:** Σ Admin2 / Σ Admin1 = 0.84–0.94. Only **0.4–1.6% of the reference cases fall in department-weeks where every Admin2 row is absent** (zero-filled), so whole-department false zeros are rare. The 6–16% shortfall comes from cases not in the 115 provinces (only ~115 of ~196 provinces ever report) or with unknown province, and from timing shifts.
- **2014–23 vs PAHO "Total":** stable at 0.85–0.94 in 2020–23. No country-level flags in the test years.
- **Not checkable with data on disk:** province-level absent weeks, and whether the ~81 never-reporting provinces are true zeros. Units with positive cases per year rise from 52 (2014) to 94 (2023), so in the early years many zero-filled rows may belong to provinces that did not report, rather than to provinces with true zeros. Label Peru as "partially validated (national/department level)".

## Training-year contamination
Training for test year Y uses targets ≤ Y−1 from 2018. Primary (`exclude`) flags in 2018–2023 are:
- Peru 2018-07-01 and 2018-08-12 (country-wide);
- Brazil Rondônia 2019-12-22;
- Peru Junín 2020-12-27 and Ucayali 2023-07-23 (training targets for later origins).

That is 5 weeks in total, all small. Drop them from training targets as is already done for `flag_gap`. Brazil and Colombia have no country-level flags in any training year.

## Other exclusion files
- `no_geometry_units.csv` lists 3 units. The 2 Taiwan "OTHER" buckets are non-spatial (1 and 16 cases, none since 2018). Colombia's Belén de Bajirá has 42 cases, 39 of them from 2018 on. **Recommendation:** drop all 3 from training and scoring (they have NaN covariates).
- `late_entry_units.csv` lists the 565 units whose first week with cases > 0 falls in epi-year ≥ 2018: BR 507 (111 first seen in 2024), CO 12, PE 28, TW 18 (all in 2023). For the sensitivity run at origin year Y, restrict the universe to units with `first_year < Y` (i.e. seen by the origin).

## Recommendation
1. **Scoring:** drop the (country, week) rows and (country, adm1, week) rows with `action == "exclude"` from the score tables before aggregating; the forecasts themselves are kept. Join on `country`, `week_start`, and on `adm1` when `scope == "adm1"`. Their effect on the test years is tiny (Peru: 2 province-weeks, 0.03% of rows). Report one sensitivity run that also drops the `sensitivity` rows, notably Brazil 2024-12-08..12-22 (1.1% of BR test rows, 0.4% of cases) and the year-end holiday state-weeks.
2. **Brazil 2024 is not truncated** at country level. The late-year ratio is the usual off-season Probable/Total offset. A unit-level InfoDengue check of 2024 (audit H2) is still the only way to validate absent municipality-weeks; the files already on disk can't do it.
3. Peru remains partially validated; Taiwan is fully validated; Colombia matches national within ~5%.
4. Exclude the 3 no-geometry units. Run the late-entry universe restriction as a sensitivity analysis.
