# OpenDengue V1.3.1 verification

Independent verification, 2026-11-15 (server epyc2). Everything was re-derived from upstream. The downloader manifest was compared only at the end.

**Overall: PASS** (see the notes for points the analysis team must handle)

| Check | National | Spatial | Temporal |
|---|---|---|---|
| 1 GitHub size + git blob sha | PASS | PASS | PASS |
| 1 Release commit 99b6a3e, no later change | PASS | PASS | PASS |
| 2 figshare v5 size + md5 | PASS | PASS | PASS |
| 3 `unzip -t` + CSV == zip member (sha256) | PASS | PASS | PASS |
| 4 Full pandas parse / content checks | PASS | PASS* | PASS* |
| 5 Version sanity | PASS | PASS | PASS |
| Manifest consistency (bytes, sha256, md5) | PASS | PASS | PASS |

## Evidence
**1 GitHub.** The API at `contents/data/releases/V1.3.1` matches `git hash-object` exactly for every file:
National 330958 B `a2b21417...`, Spatial 55045735 B `c1bdaff5...`, Temporal 55205724 B `73b73795...`.
The commit history page in Chrome shows a single commit, "V1.3.1 release" 99b6a3e (ahyoung-lim, 2026-11-03), and "End of commit history". No later commit changed these files.

**2 figshare.** Article 24259573 has versions [1..5], and v5 (posted 2026-11-03 15:46Z) is the latest. Chromes unversioned page shows Version 5. The page does not print the string V1.3.1, but v5s files are named `*_V1_3_1.zip`. For all three zips, size and computed_md5 = supplied_md5 = local md5: `5b5ea930...`, `d215278e...`, `4f88cec8...`.

**3 Archives.** Each zip holds 1 member and "No errors detected". Extracted CSV sha256 equals the `unzip -p` sha256: `b9381e3f...`, `402f0a62...`, `fec937de...`.

**4 Parse.** All three use 16 columns, the same in each file. Every check reports 0 for: parse errors, NaT start/end dates, start>end, non-numeric/NaN/negative/non-integer dengue_total, null UUID, `Year`≠start-year, full-duplicate rows, and duplicate rows ignoring UUID. The last row in each file is a complete YEMEN 2024-07-28..08-03 row with a trailing CRLF (no truncation).

| | National | Spatial | Temporal |
|---|---|---|---|
| rows | 29,540 | 2,823,035 | 2,834,996 |
| `wc -l` − 1 | 29,540 | 2,823,043 | 2,835,004 |
| unique UUID | 943 | 1,401 | 1,414 |
| S_res | Admin0 29,540 | Admin2 2,642,502 / Admin1 143,977 / Admin0 36,556 | Admin2 2,642,808 / Admin1 151,794 / Admin0 40,394 |
| T_res | Week 22,883 / Year 3,491 / Month 3,166 | Week 2,239,818 / Month 575,981 / Year 7,236 | Week 2,249,062 / Month 578,504 / Year 7,430 |
| lowercase `confirmed` | 103 | 3,296 | 3,296 |

\*The 8-line gap in Spatial/Temporal comes from 4 rows (INDIA, `LITERATURE-IND-19972012-Y01-01`) whose `adm_1_name` and `full_name` contain an embedded `\r\n` ("ARUNACHAL\r\nPRADESH"). These rows are valid quoted CSV.

case_definition_standardised values: Total, Suspected, Confirmed, Probable, Probable and confirmed, Suspected and confirmed, **confirmed** (lowercase).

**5 Version.** No version column. Date range in all files: start ≥ 1924-01-20, max calendar_end_date **2025-04-30**. Rows ending in 2025: 104 / 132 / 135. CSV timestamps inside the zips are 2026-07-31. This is plausible for a Nov-2026 release with reporting lag, and nothing points to another version.

## Notes for analysis
- `UUID` identifies the *source document*, not the row (per figshare codebook), so it is heavily repeated. Do not use it as a row key. Rows are unique with or without UUID.
- Merge `confirmed` into `Confirmed`.
- Strip `\r\n` from "ARUNACHAL\r\nPRADESH" (4 rows each in Spatial/Temporal).
- Missing admin names/codes are the literal string `NA`. Read with `keep_default_na`, or map them explicitly.
- `Year` = year of start date. 319 / 38,393 / 38,523 rows end in the following year.
- Data stops at 2025-04-30. Recent 2024–25 coverage is sparse.
