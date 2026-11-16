# Data & tools verification: Paper 1 (Place or Placeholder?)

Checked 2026-11-15 using web docs and catalog pages only. **UNVERIFIED** means no primary source confirmed the item, so do not rely on it.

---

## 1. OpenDengue v1.3.1

| Item | Finding |
|---|---|
| Exists? | Yes. GitHub release `v1.3.1`, published **2026-11-03** (GitHub API). It is the latest release. The one before it is v1.3.0 (2025-05-27). |
| Download | Zips are in the repo, not attached as release assets: `data/releases/V1.3.1/{National,Spatial,Temporal}_extract_V1_3_1.zip` (https://github.com/OpenDengue/master-repo/tree/main/data/releases/V1.3.1). The website has a filtered CSV download at https://opendengue.org/data.html. Figshare DOI: 10.6084/m9.figshare.24259573. The repo README still cites "v1.3 (2025)", so it is UNVERIFIED whether figshare has 1.3.1 yet. |
| Extracts | National, Spatial (highest spatial resolution), Temporal (highest temporal resolution). Use the **Temporal** extract for weekly data, but check that it also keeps admin-2 rows. A weekly admin-1 series can outrank a coarser-time admin-2 one. |
| Columns | `adm_0_name`, `adm_1_name`, `adm_2_name`, `FAO_GAUL_code`, `calendar_start_date`, `calendar_end_date`, `dengue_total`, plus `S_res` and `T_res`. The codebook gives no value lists for S_res/T_res. Case definitions are in `sourcedata_V1.3.1.csv`. |
| Licence | **CC BY-SA** per the Sci Data paper (Clarke et al. 2024, https://doi.org/10.1038/s41597-024-03120-7). Website text is CC BY 4.0. Share-alike applies to any redistributed derived dataset. |
| GAUL version | **Not stated anywhere (UNVERIFIED).** Brazil IBGE codes were matched to GAUL admin-2 using geobr and a lookup table (paper). |
| Coverage | The paper names Brazil, Colombia and Taiwan MoHs as sources of **weekly admin-2** counts. **Peru is not mentioned.** The v1.3.1 notes say Peru and Colombia national totals now combine Admin1 and Admin2 sources. v1.3.1 also fixed weekly calendar dates for "several countries". v1.2.0 added Brazil admin-2 2001–2021. Whether weekly admin-2 data exists for Brazil 2022–2024, Peru 2013–2023, Colombia 2013–2022 and Taiwan 2013–2024 is **UNVERIFIED**. Tabulate `T_res`/`S_res` by country-year on day 1. |

Release-note gotchas (v1.3.1): duplicate weekly records were removed for some countries, and monthly/annual rows are no longer dropped when they share a start date with a weekly row. Expect mixed-resolution rows and filter on `T_res == "Week"` (exact token UNVERIFIED).

## 2. AlphaEarth Satellite Embedding V1

| Item | Finding |
|---|---|
| EE ID | `GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL` (https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_SATELLITE_EMBEDDING_V1_ANNUAL) |
| Years | The EE catalog says 2017-01-01 to 2025-01-01, i.e. **2017–2024**. The 2017 layer was regenerated in v1.1. Source Cooperative says **2017–2025**, so 2025 may be out off-EE but is **not confirmed in EE**. |
| Bands | 64 bands, `A00`–`A63`, values in [-1, 1], unit-length vectors. Use all bands together. |
| Resolution | 10 m, tiles in UTM. |
| Licence | CC-BY 4.0. Attribution: "The AlphaEarth Foundations Satellite Embedding dataset is produced by Google and Google DeepMind." |
| Off-EE copies | (a) `gs://alphaearth_foundations`: the catalog says the bucket is **"provider pays" as of July 2026**, but a translated page says requester-pays. Treat cost as UNVERIFIED. README: https://developers.google.com/earth-engine/guides/aef_on_gcs_readme. (b) **Source Cooperative** `tge-labs/aef` (https://source.coop/tge-labs/aef): COGs, 8192², int8. De-quantise as `sign(v)*(v/127.5)^2`, with -128 as NoData. Files are stored bottom-up, so use the provided `.vrt` files. Index: `aef_index.gpkg`/parquet/csv. Not officially Google-supported. Python loader: `aef-loader` (https://aef-loader.readthedocs.io). One Source Coop test page noted a 2017 quality issue. |

Implication: district-mean embeddings for about 7k districts are feasible in EE (`reduceRegions` at 10 m is expensive, so set `scale` around 100–250 m or use tileScale). Source Coop avoids EECU quota but means downloading TBs for Brazil. A practical compromise is to compute in EE at a coarser scale.

## 3. Earth Engine access (Nov 2026)

| Item | Finding |
|---|---|
| Registration | Noncommercial, verified Cloud project. `ee.Initialize(project='...')` is mandatory and the Earth Engine API must be enabled. Reverification is required yearly. |
| Community tier | **150 EECU-hours/month** (confirmed). No billing account needed. This is the default tier. |
| Contributor tier | **1,000 EECU-hours/month** (confirmed). Requires a linked billing account. EE noncommercial use is not charged, but other GCP services are (e.g. GCS export storage). |
| Partner tier | 100,000 EECU-hours. Requires an application and must be climate-related. Not relevant here. |
| Enforcement | Quotas have been rolling out since 2026-04-27. They reset monthly (midnight PT on the 1st). **Over quota means "restricted mode"** (throttled), not a hard stop. |
| Headless auth | `earthengine authenticate --auth_mode=notebook` (paste the code from a local browser), or `auth_mode=gcloud` if gcloud is on both machines. Unattended jobs should use a **service account** with `credentials=` passed to `ee.Initialize`, registered to the project (see the EE service-account guide). Docs: https://developers.google.com/earth-engine/guides/auth |
| xee | An Xarray backend for EE (`pip install xee`). It is useful for pulling ERA5/MODIS stacks as xarray, but counts against the same EECU quota. Not re-verified. |

Source: https://developers.google.com/earth-engine/guides/noncommercial_tiers

## 4. GAUL boundaries

| Asset | ID / notes |
|---|---|
| GAUL 2015 L2 | `FAO/GAUL/2015/level2`. **Deprecated** and superseded by 2025. Properties: `ADM0_CODE, ADM0_NAME, ADM1_CODE, ADM1_NAME, ADM2_CODE, ADM2_NAME, DISP_AREA, STATUS, STR2_YEAR, EXP2_YEAR`. Licence is **non-commercial only** (FAO data licence). The simplified version is `FAO/GAUL_SIMPLIFIED_500m/2015/level2`. |
| GAUL 2024 | **No official EE asset found.** Community-catalog copy: `projects/sat-io/open-datasets/FAO/GAUL/GAUL_2024_L2`, not distributed by FAO. |
| GAUL 2025 L2 | `FAO/GAUL/2025/level2` (official). Properties: `GAUL0_CODE … GAUL2_CODE, GAUL2_NAME, ISO3_CODE, DISP_EN`. CC-BY-4.0. **No statement that codes match GAUL 2015**, so assume they do not. |
| OpenDengue's version | UNVERIFIED. It is most likely GAUL 2015-era codes, given the 2023 build date. Test by joining `FAO_GAUL_code` to `FAO/GAUL/2015/level2.ADM2_CODE` and measuring the match rate per country. |
| Taiwan | How GAUL represents Taiwan (separate ADM0 or a province of China) is **UNVERIFIED**. GAUL 2015 L2 for Taiwan likely reflects pre-2010 county structure. Also check that "287 Taiwan units" in the plan matches OpenDengue's Taiwan adm_2 list, since Taiwan has 22 counties/cities and about 368 townships. |
| Fallbacks | geoBoundaries (CC-BY, `WM/geoLab/geoBoundaries/600/ADM2` in EE, ID UNVERIFIED) or GADM 4.1 (non-commercial). Brazil can use geobr/IBGE codes directly. Taiwan can use MOI/geoBoundaries, joined by name. |

## 5. Covariate datasets on Earth Engine

| Dataset | EE ID | Coverage (catalog) | Notes |
|---|---|---|---|
| ERA5-Land daily | `ECMWF/ERA5_LAND/DAILY_AGGR` | 1950-01-02 to about 3 months behind real time | Bands `temperature_2m`, `dewpoint_temperature_2m`, `total_precipitation_sum`. About 11 km. Copernicus licence. |
| MODIS NDVI | `MODIS/061/MOD13Q1` | 2000-02-18 to 2026-10-16 | 250 m, 16-day. Bands `NDVI`, `EVI`, `SummaryQA`. Watch for Terra orbit drift and end-of-life late in the series. |
| MODIS LST | `MODIS/061/MOD11A2` | (page not fetched, but ID follows the Collection 6.1 pattern) | 1 km, 8-day, `LST_Day_1km`. Coverage UNVERIFIED. |
| VIIRS annual NTL | `NOAA/VIIRS/DNB/ANNUAL_V22` | 2012-04-01 to 2025-01-01 (2012–2024) | Bands `average`, `average_masked`, `median`, … `NOAA/VIIRS/DNB/ANNUAL_V21` holds an older run. |
| GHSL pop | `JRC/GHSL/P2023A/GHS_POP` | Epochs 1975–2020 every 5 years, plus 2025 and 2030 projections | 100 m, `population_count`. Interpolate between epochs. |
| GHSL built-up | `JRC/GHSL/P2023A/GHS_BUILT_S` (from catalog slug) | Same epochs | ID inferred from the slug and not fetched. |
| WorldPop (new) | `WorldPop/GP/100m/R2025A/v1/pop` | **2015–2030 annual** (Global2) | **Covers 2021–2024.** DOI 10.5258/SOTON/WP00839. Band names UNVERIFIED. |
| WorldPop (old) | `WorldPop/GP/100m/pop` | 2000–2020 only | Do not use for 2021+. |

## 6. PDFM / Population Dynamics

- Research repo: https://github.com/google-research/population-dynamics. Request access via form https://forms.gle/ysdp5uUoPrMrhjZQA. Research use is free on approval and data is delivered as a **BigQuery listing**. Contact pdfm-embeddings@google.com.
- Productised as **Population Dynamics Insights** (Google Maps Platform, Preview, announced 2026-04-22). It has 330-dim embeddings on an **S2 level-12 grid**, "updated monthly".
- **Covered countries (17):** AU, BE, **BR**, CA, FR, DE, IN, IT, JP, MX, NL, NG, PT, ES, CH, GB, US (PDI docs, https://developers.google.com/maps/documentation/population-dynamics-insights/about-data).
- **Brazil is covered. Colombia, Peru and Taiwan are NOT.** PDFM can only be a Brazil-only comparator.
- History depth is UNVERIFIED. Embeddings come from Search/Maps activity and are likely recent, which creates a temporal-leakage risk for 2013–2024 backtests. Whether the research tier gives the same S2 grid or US-only counties/ZCTAs is UNVERIFIED.

## 7. TimesFM

| Item | 2.5 | 3.0 (new) |
|---|---|---|
| HF ID | `google/timesfm-2.5-200m-pytorch` | `google/timesfm-3.0-pytorch` (Aug 2026) |
| Params | 200M, plus an optional 30M quantile head | 330M |
| Weights licence | Apache-2.0 | **timesfm-non-commercial-license-v1.0** (research use is OK, but not production) |
| Context | Example uses 1024 context and 256 horizon | Global context 15,360 |
| Quantiles | `use_continuous_quantile_head=True`. Output is mean plus deciles 0.1–0.9 | `return_quantiles=True`, 9 quantiles |
| Covariates | XReg (restored 2025-10-29), needs the `timesfm[xreg]` extra | Native past and future covariates |

- PyPI `timesfm`: latest **3.0.2 (2026-09-09)**, `Requires-Python >=3.10`, so **Py3.12 is OK**. Extras: `torch`, `mlx`, `flax`, `xreg`. 2.5 code is "archived" but still in `src/timesfm`. Which pin loads 2.5 cleanly is UNVERIFIED. The 2.0.x line (Jun–Jul 2026) is likely. Pin and smoke-test it.
- 2.5 API: `timesfm.TimesFM_2p5_200M_torch.from_pretrained(...)`, then `model.compile(timesfm.ForecastConfig(...))` and `model.forecast(horizon, inputs)`.
- GPU memory: not documented. A 200–330M model in fp32 is about 1–1.5 GB of weights, so batch inference fits easily on 48 GB.
- The quantile set lacks the 0.01/0.025/0.05/0.95/0.975/0.99 levels used in the standard 23-quantile WIS. **Restrict WIS to the 0.1–0.9 deciles for every model**, or extrapolate.

## 8. Python tooling

| Need | Option |
|---|---|
| WIS / quantile score | `scoringrules` (https://scoringrules.readthedocs.io) has `interval_score` and `weighted_interval_score` (signature UNVERIFIED). Alternative: `interval-scoring` (adrian-lison). Recommendation: write a 20-line vectorised WIS following Bracher et al. 2021 and unit-test it against scoringrules. |
| LightGBM quantile | `objective="quantile", alpha=q`, one model per quantile. Fix crossing by sorting. Standard; not re-verified. |
| Negative binomial | `statsmodels.discrete.discrete_model.NegativeBinomial` (estimates alpha) or `sm.GLM(..., family=sm.families.NegativeBinomial(alpha=...))` (alpha is fixed). Standard; not re-verified. |
| Diebold–Mariano | PyPI `dieboldmariano` 1.0.0 (pure Python). Whether it applies the HLN correction is UNVERIFIED. `macroforecast.dm_test(correction="hln")` documents HLN. johntwk/Diebold-Mariano-Test is an HLN script. Recommendation: implement DM with HLN plus Newey-West HAC (lag h-1) yourself and check it against R `forecast::dm.test`. |

## Red flags for the plan
1. **PDFM does not cover Colombia, Peru or Taiwan.** It can only be a Brazil-only comparator, and its historical depth is unclear.
2. **OpenDengue's GAUL version is undocumented, and GAUL 2015 (the likely match) is deprecated and licensed non-commercial only.** Join rates, especially for Taiwan, must be measured before committing.
3. **Weekly admin-2 coverage for Peru, and for Brazil after 2021, is unconfirmed** in the docs. The plan's unit counts (5,517 / 1,071 / 115 / 287) need re-deriving from v1.3.1, which was released only 12 days ago.
4. **AlphaEarth in EE only covers 2017–2024.** There is no 2013–2016 data, so embeddings must be treated as static or as lagged annual values. 2025 exists only on Source Coop.
5. **TimesFM 3.0 now exists**, but its weights are non-commercial. The 2.5 install path needs pinning, and both models give only 0.1–0.9 quantiles, which affects WIS comparability.
6. EE quotas are now enforced. Use Contributor tier (billing linked) and coarse `scale` for 10 m embeddings over Brazil.

---
## Supervisor review notes (2026-11-15)
- AlphaEarth years: **resolved**. A direct EE query (2026-11-15) returns 2017–2025 (97,155 tiles). Source Cooperative `tge-labs/aef` also has 2017–2025.
- OpenDengue `data/releases/` on GitHub shows folders V1.0, V1.1, V1.2, V1.2.1, V1.2.2, V1.3, V1.3.1 (spot-checked). Release date 2026-11-03 not independently confirmed.
- Design implications to raise before the Jan 15 freeze:
  1. AlphaEarth starts in 2017, so L4 rows exist only from 2018. Fit L0–L3 on the same 2018+ window as L4 (or report both windows), otherwise Embedding gain mixes in a training-window effect.
  2. TimesFM 2.5 emits only the 0.1–0.9 quantiles. Either score all models' WIS on a common quantile set, or have the LightGBM residual stage produce the full 23-quantile set. Decide and freeze.
  3. Re-derive unit counts (5,517 / 1,071 / 115 / 287) and weekly coverage from the v1.3.1 Spatial extract. Taiwan's 287 matches neither its 22 counties nor its ~368 townships.
