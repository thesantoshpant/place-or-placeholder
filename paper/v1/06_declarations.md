## Declarations

<!-- Writer A. Wording follows the medRxiv submission guide and FAQ as summarised in audits/review_round/R6_draft_and_medrxiv.md section D. Use the same text in the medRxiv form. Every [[AUTHORS: ...]] item must be filled by the authors before posting. -->

### Ethics statement

This study used only openly available human data, originally located at:

- OpenDengue data release V1.3.1 (weekly dengue case counts aggregated by administrative unit): https://github.com/OpenDengue/master-repo/tree/main/data/releases/V1.3.1, doi:10.6084/m9.figshare.24259573 [@opendengue131; @clarke2024opendengue].
- Taiwan Centers for Disease Control, "Dengue fever daily confirmed cases since 1998" (`Dengue_Daily.csv`), a public case-level line list of confirmed cases with onset date and township of residence, published on the Taiwan government open data platform (https://data.gov.tw/dataset/21025) and used through the Internet Archive snapshot of 29 July 2025 [[VERIFY: exact Internet Archive snapshot URL]] [@taiwancdc_dengue_daily].
- InfoDengue public API (weekly municipal dengue counts for Brazil): https://info.dengue.mat.br/services/api/doc [@infodengue_api; @codeco2018infodengue].

We used the Taiwan line list only to build and check weekly township totals, and we report only aggregated weekly counts. No new data were collected from people. [[AUTHORS: confirm that no institutional review or exemption determination was sought or is required; none is claimed here]]

<!-- Do NOT use the earlier wording "no human participants or individual-level data": the Taiwan CDC file is a case-level line list (R6 H6; RESOLUTION_LOG.md section I). -->

Patient and participant consent: not applicable (openly available data only). Clinical trial registration: not applicable.

### Reporting guideline

We followed the EPIFORGE 2020 guidelines for epidemic forecasting and prediction research [@pollett2021epiforge]; the completed checklist is in Supplementary Material S1. This is a retrospective forecasting study: all forecasts were produced after the fact from one snapshot of final, revised data.

### Data availability

All input data are public.

- **Dengue cases:** OpenDengue V1.3.1, Temporal extract (release commit 99b6a3e; figshare version 5), licensed CC BY-SA [@opendengue131; @clarke2024opendengue]. [[VERIFY: CC BY-SA version number]]
- **Embeddings:** AlphaEarth Foundations Satellite Embedding dataset, V1 annual (`GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL`), Google Earth Engine Data Catalog, CC-BY 4.0 [@aef_dataset; @brown2025alphaearth]. The AlphaEarth Foundations Satellite Embedding dataset is produced by Google and Google DeepMind.
- **Covariates (all through Google Earth Engine [@gorelick2017gee]):** ERA5-Land daily aggregates (Copernicus licence; contains modified Copernicus Climate Change Service information) [@era5land_ee]; MODIS Terra vegetation indices (MOD13Q1) and land surface temperature (MOD11A2), Collection 6.1 [@mod13q1_ee; @mod11a2_ee]; VIIRS annual night-time lights [@viirs_ee]; GHSL P2023A population and built-up surface grids [@ghsl_pop; @ghsl_built]. [[AUTHORS: confirm and state the MODIS, VIIRS and GHSL licence terms from the cited catalogue pages]]
- **Boundaries:** IBGE municipal mesh 2022 for Brazil [@ibge2022malha]; geoBoundaries gbOpen for Colombia (DANE MGN 2020, CC BY 4.0), Peru (IGN/OCHA, CC BY 3.0 IGO) and Taiwan (OpenStreetMap 2017, CC BY-SA 2.0) [@geoboundaries_gbopen].
- **Validation sources:** InfoDengue API (accessed November 2026) [@infodengue_api]; Taiwan CDC `Dengue_Daily.csv` (Open Government Data License v1.0) [@taiwancdc_dengue_daily].
- **Derived data:** the zero-filled district-week panel, district features, embeddings by district and year, forecasts, scores and all result tables will be deposited with the code under CC BY-SA 4.0, as required by the share-alike terms of OpenDengue and the Taiwan boundaries: [[AUTHORS: repo public + Zenodo DOI]] [[AUTHORS: confirm licence for derived data]]

### Code availability

The code for the data pipeline, feature extraction, location controls, splits, model runs, scoring, statistical inference and the script that regenerates every table and figure, with unit tests, a locked software environment and data manifests with checksums, will be released under an open licence at [[AUTHORS: repo public + Zenodo DOI]]. The archived snapshot carries a versioned DOI minted on the day of posting. The public history includes the dated commits cited for pre-specification in the Methods and Supplement S1 (`d8c7944`, `fcc3c38`, `bd3ba50`, `e9df1f1`). The protocol, deviation log and analysis code were deposited at [[AUTHORS: deposit DOI]] on 18 November 2026, before the Brazil S4 and no-history Brazil S2 results were read.

<!-- EPIFORGE items 9 (code) and 16 (versioned identifier) depend on the repo and DOI above (R6 section E). The pre-specification claims rest on the git history being public (RESOLUTION_LOG.md, Needs the authors, item 3). -->

### Funding

[[AUTHORS: TBD]]

<!-- medRxiv asks whether any third party provided payment or services for any aspect of the work. Authors to decide whether to declare Google Earth Engine noncommercial (Contributor tier) access and institutional computing (R6 D row 7). If none: "This work received no specific funding." -->

### Competing interests

[[AUTHORS: TBD]]

<!-- medRxiv: cover the past 36 months for every author, including third-party payments or services. -->

### Author contributions (CRediT)

[[AUTHORS: TBD]]

<!-- Roles to assign: conceptualisation, methodology, software, validation, formal analysis, investigation, data curation, writing (original draft), writing (review and editing), visualisation, supervision, project administration. -->

### Use of AI tools

[[AI-USE: full statement in the shared doc]]

<!-- Authors' decision 2026-11-18 (STYLE.md): the full AI-use statement, naming the tool, is added only in the shared doc and the submitted PDF. medRxiv FAQ: tool use "should be detailed in manuscripts", tools cannot be authors, and authors are accountable for all content. Factual list: audits/review_round/RESOLUTION_LOG.md, "Needs the authors" (code, downloads and download-verification scripts, Earth Engine extractions, model runs, scoring, statistics, internal audits, the earlier protocol review, drafting and reference checks were done by AI agents). The statement must also say which checks people carried out. The Methods (2.1) and Supplement S1 point to this section wherever agent work is described. -->

### Acknowledgements

[[AUTHORS: TBD]]

<!-- Suggested: the OpenDengue, InfoDengue and Taiwan CDC data teams; the external reviewers of the earlier draft; the administrators of the computing server. -->

### Preprint licence

[[AUTHORS: TBD]]

<!-- CC BY is recommended (RESOLUTION_LOG.md, Needs the authors, item 4). If a map figure uses the OpenStreetMap-derived Taiwan polygons, check the CC BY-SA 2.0 terms for that figure. -->
