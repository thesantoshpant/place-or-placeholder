# Weekly district panel v1 (OpenDengue V1.3.1)

**Source:** Temporal extract, `T_res=="Week"`, `S_res=="Admin2"`; Brazil, Colombia, Peru, Taiwan. Weeks start on Sunday. `year` is the epidemiological year, meaning the calendar year of the week's Wednesday.

## Frozen rule
1. The unit universe is every Admin2 unit that appears in a country's weekly file.
2. Coverage runs from the country's first to its last week with any Admin2 row. Brazil starts at epi-week 2014-01, the week starting 2013-12-29; this is OpenDengue's "2013" week. Every unit gets every week, and a missing row means 0 cases (`observed=False`, `zero_filled=True`).
3. Validation compares the Admin2 sum with OpenDengue's national weekly series (`S_res=="Admin0"`).

`unit_id`: for Brazil, the 7-digit IBGE code exactly as OpenDengue gives it (all codes have 7 digits). The IBGE check digit matches for 5,508 of 5,517 codes. The other 9 are IBGE's official exceptions (e.g. 2201919, 5203939), so codes are never recomputed. For other countries, `unit_id` is `ADM0|ADM1|ADM2` (OpenDengue names). The case definition is constant per country: BR Probable, CO Total, PE Probable and confirmed, TW Total.

## Counts
| country | units | weeks | period | rows | % zero-filled |
|---|---|---|---|---|---|
| Brazil | 5,517 | 574 | 2013-12-29 to 2024-12-22 | 3,166,758 | 40.1 (2014–21: 29.3; 2022+: 69.2) |
| Colombia | 1,071 | 835 | 2006-12-31 to 2022-12-25 | 894,285 | 77.7 |
| Peru | 115 | 1,252 | 2000-01-02 to 2023-12-24 | 143,980 | 78.5 |
| Taiwan | 287 | 1,409 | 1997-12-28 to 2024-12-22 | 404,383 | 98.1 |

## National check
Ratio = Admin2 sum ÷ national (`S_res=="Admin0"`) sum. National weekly data start in 2014. Full table, including the share of weeks within ±10%: `outputs/data_audit/panel_national_check.csv`.

| year | 14 | 15 | 16 | 17 | 18 | 19 | 20 | 21 | 22 | 23 | 24 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| BR | 1.00 | 1.03 | .68 | .48 | .57 | .69 | .65 | .56 | .59 | .49 | .63 |
| CO | .99 | .99 | .99 | .99 | .97 | .97 | .98 | .94 | .96 | – | – |
| PE | .91 | .91 | .79 | .90 | .68 | .89 | .85 | .91 | .87 | .94 | – |

- **Brazil:** from 2016 on, Admin2 ("Probable") is a smooth, seasonal 0.3–0.7 of national ("Total"), with ≈0% of weeks within ±10%. This is a case-definition offset, not missing weeks. 2022+ (no explicit zeros) looks like 2016–21 (explicit zeros), so zero-filling it looks safe.
- **Colombia:** agrees closely; 46–100% of weeks are within ±10%.
- **Peru:** yearly totals agree; weekly values are noisy because of timing shifts.
- **Taiwan:** national weekly is **0 in every week** of 1998–2024, including 2015 (43k Admin2 cases), so it is unusable. National 2021 = 0 is consistent with the zero-filled 2021 but proves nothing; see the Taiwan CDC cross-check.
- Colombia and Peru before 2014 are unvalidated.

## flag_gap
`flag_gap=True` for every unit in a country-week where national ≥ 20 cases **and** (Admin2/national) < 0.25 × that country-year's ratio of sums. The threshold is relative to the year's ratio so that Brazil's definitional offset is not flagged. Only **1 week** is flagged: Peru 2018-08-12 (21 vs 156 cases; relative ratio 0.20). Exclude flagged weeks from scoring.

## Rebuild
```
cd $P && source env.sh
python scripts/data/build_panel.py   # ~40 s
python -m pytest -q tests/test_panel.py
```
Code: `src/pop/data/opendengue.py`, `src/pop/data/panel.py`.
