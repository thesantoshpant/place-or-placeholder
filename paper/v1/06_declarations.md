## Declarations

<!-- Wording follows the medRxiv submission guide and FAQ as summarised in audits/review_round/R6_draft_and_medrxiv.md section D. Use the same text in the medRxiv form. Every AUTHORS item must be completed by the authors before posting. -->

### Ethics statement

This study used only openly available human data. Weekly dengue case counts aggregated by administrative unit came from the OpenDengue data release V1.3.1 (https://github.com/OpenDengue/master-repo/tree/main/data/releases/V1.3.1; doi:10.6084/m9.figshare.24259573) [@opendengue131; @clarke2024opendengue]. We also used Taiwan's public line list of confirmed cases, which gives onset date and township of residence ("Dengue fever daily confirmed cases since 1998", `Dengue_Daily.csv`) [@taiwancdc_dengue_daily]. It comes from the Taiwan Centers for Disease Control through the Taiwan government open data platform (https://data.gov.tw/dataset/21025); we used the Internet Archive snapshot of 29 July 2025 at [to be completed]. <!-- AUTHORS: exact Internet Archive snapshot URL --> Weekly municipal dengue counts for Brazil came from the InfoDengue public API (https://info.dengue.mat.br/services/api/doc) [@infodengue_api; @codeco2018infodengue].

The Taiwan CDC file is a public open-government dataset without names or other direct identifiers. We used it only to build and check weekly township totals, and we report only aggregated weekly counts. <!-- AUTHORS: confirm that Dengue_Daily.csv contains no names or other direct identifiers (added in v1g, reviewer E17) --> No new data were collected from people. <!-- AUTHORS: confirm that no institutional review or exemption determination was sought or is required; none is claimed here. Referee RA (round 3, minor 18) asks for an explicit exemption statement or institutional determination because the Taiwan file is a case-level line list; obtain one or state why none is needed before posting. --> Consent was not needed, because only openly available data were used. The study is not a clinical trial and was not registered.

<!-- Do NOT use the earlier wording "no human participants or individual-level data": the Taiwan CDC file is a case-level line list (R6 H6; RESOLUTION_LOG.md section I). -->

### Reporting guideline

We followed the EPIFORGE 2020 guidelines for epidemic forecasting and prediction research [@pollett2021epiforge]; the completed checklist is in Supplementary Methods, section G. This is a retrospective forecasting study: all forecasts were produced after the fact from one snapshot of final, revised data.

### Data availability

All input data are public. Dengue cases are from the OpenDengue V1.3.1 Temporal extract (release commit 99b6a3e; figshare version 5), licensed CC BY-SA [@opendengue131; @clarke2024opendengue]. <!-- AUTHORS: confirm the CC BY-SA version number --> The embeddings are the AlphaEarth Foundations Satellite Embedding dataset, V1 annual (`GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL`), from the Google Earth Engine Data Catalog under CC-BY 4.0 [@aef_dataset; @brown2025alphaearth]; this dataset is produced by Google and Google DeepMind.

All covariates were obtained through Google Earth Engine [@gorelick2017gee]: ERA5-Land daily aggregates (Copernicus licence; contains modified Copernicus Climate Change Service information) [@era5land_ee]; MODIS Terra vegetation indices (MOD13Q1) and land surface temperature (MOD11A2), Collection 6.1 [@mod13q1_ee; @mod11a2_ee]; VIIRS annual night-time lights [@viirs_ee]; and the GHSL P2023A population and built-up surface grids [@ghsl_pop; @ghsl_built]. <!-- AUTHORS: confirm and state the MODIS, VIIRS and GHSL licence terms from the cited catalogue pages --> Boundaries are the 2022 IBGE municipal mesh for Brazil [@ibge2022malha] and geoBoundaries gbOpen for Colombia (DANE MGN 2020, CC BY 4.0), Peru (IGN/OCHA, CC BY 3.0 IGO) and Taiwan (OpenStreetMap 2017, CC BY-SA 2.0) [@geoboundaries_gbopen]. Validation sources were the InfoDengue API (accessed November 2026) [@infodengue_api] and the Taiwan CDC file `Dengue_Daily.csv` (Open Government Data License v1.0) [@taiwancdc_dengue_daily].

We will deposit the following with the code at [to be completed]: the weekly district panel with zero-filled weeks; the district features; the population-weighted AlphaEarth embeddings for every district and extracted year from 2017 (64 values each, before and after rescaling to unit length, with the population sums); and all forecasts, scores and result tables. They will be released under CC BY-SA 4.0, as the share-alike terms of OpenDengue and the Taiwan boundaries require. <!-- AUTHORS: public repository URL and Zenodo DOI; confirm the licence for derived data -->

### Code availability

The code will be released under an open licence at [to be completed]. <!-- AUTHORS: public repository URL and Zenodo DOI --> It reproduces the whole study, from data download to every table and figure, and comes with unit tests, a locked software environment and data manifests with checksums. The archived version will receive a DOI on the day of posting. The public history includes the dated commits cited for pre-specification in the Supplementary Methods (`d8c7944`, `fcc3c38`, `bd3ba50`, `e9df1f1`). <!-- AUTHORS 2026-11-20: deposit skipped (decision of the authors); the repository must be public at posting, because the pre-specification claims rest on its dated history (RA M7) -->

<!-- EPIFORGE items 9 (code) and 16 (versioned identifier) depend on the repository and DOI above (R6 section E). The pre-specification claims rest on the git history being public (RESOLUTION_LOG.md, Needs the authors, item 3). -->

### Funding

[to be completed] <!-- AUTHORS: funding statement. medRxiv asks whether any third party provided payment or services for any aspect of the work. Decide whether to declare Google Earth Engine noncommercial (Contributor tier) access and institutional computing (R6 D row 7). If none: "This work received no specific funding." -->

### Competing interests

[to be completed] <!-- AUTHORS: competing interests for every author over the past 36 months, including third-party payments or services -->

### Author contributions

[to be completed] <!-- AUTHORS: CRediT roles to assign: conceptualisation, methodology, software, validation, formal analysis, investigation, data curation, writing (original draft), writing (review and editing), visualisation, supervision, project administration -->

### Use of AI tools

<!-- AI-USE -->

<!-- Authors' decision 2026-11-18 (STYLE.md): the full AI-use statement, naming the tool, is added only in the shared doc and the submitted PDF; the build inserts it at the AI-USE marker above. medRxiv FAQ: tool use "should be detailed in manuscripts", tools cannot be authors, and authors are accountable for all content. Factual list: audits/review_round/RESOLUTION_LOG.md, "Needs the authors" (code, downloads and download-verification scripts, Earth Engine extractions, model runs, scoring, statistics, internal audits, the earlier protocol review, drafting and reference checks were done by AI agents). The statement must also say which checks people carried out. Methods 2.1 and the Supplementary Methods point to this section wherever agent work is described. Round 3 (RA minor 17): the statement must list which checks people carried out independently (for example, which numbers, figures, references and code paths an author verified by hand), because agents wrote the code and ran the analyses. -->

### Acknowledgements

[to be completed] <!-- AUTHORS: acknowledgements. Suggested: the OpenDengue, InfoDengue and Taiwan CDC data teams; the external reviewers of the earlier draft; the administrators of the computing server. -->

### Preprint licence

[to be completed] <!-- AUTHORS: preprint licence. CC BY is recommended (RESOLUTION_LOG.md, Needs the authors, item 4). If a map figure uses the OpenStreetMap-derived Taiwan polygons, check the CC BY-SA 2.0 terms for that figure. -->
