# Mumbai dataset feasibility audit

Audit date: 2026-10-10. **No requested source dataset has been downloaded into this city folder.** Shell networking is disabled (`CODEX_SANDBOX_NETWORK_DISABLED=1`) and host DNS lookups failed. Browser metadata is evidence of availability, not a local download or byte-level audit. Unknown sizes and missing-value counts remain unknown. Existing Alexandria files are not city downloads.

## Dataset findings

### Processed Mumbai VLM and building risk, requested v2

- **Download Status:** BLOCKED_NETWORK
- **File Names:** Mumbai_VLM_data.csv; Mumbai_Buildings_Damage_Risk.zip; Building_Collapse_Incidents.xlsx (publisher names; v2 inventory unverified)
- **Size Note:** Unknown: file not retrieved
- **Format:** CSV; zipped shapefile; XLSX
- **Spatial Resolution:** Irregular VLM points and individual polygons; empirical spacing not measured
- **Temporal Coverage:** Mumbai InSAR 2015-2023 (paper); 10/30/50-year scenarios are projections
- **Coordinate System:** VLM reference IGS14; lat/lon columns; polygon .prj unverified
- **Relevant Fields Bands:** longitude; latitude; vlm cm/year; Risk_InSAR/Risk_10yrs/Risk_30yrs/Risk_50yrs (0-4)
- **Missing Values:** Publisher risk fields may be NaN; actual null/sentinel counts unknown
- **License:** CC0 1.0
- **Model Use:** VLM: DL input/baseline; risk: derived baseline or weak target; incidents: potential independent labels/validation
- **Notes:** Pin https://doi.org/10.7294/25856260.v2 . Current landing page is v3 (2025-10-29); exact v2 sizes and file equality unknown. Risk is derived from InSAR and footprints: not independent validation. Shared incident workbook needs Mumbai filtering.
- **Source:** [Processed Mumbai VLM and building risk, requested v2](https://data.lib.vt.edu/articles/dataset/Data_for_Vertical_Land_Motion_and_Building_Damage_Risk_for_the_Indian_Megacities/25856260)

### Mumbai C-1 dangerous/dilapidated building lists

- **Download Status:** BLOCKED_NETWORK
- **File Names:** 7 candidate PDFs: see audit/c1_year_coverage.csv
- **Size Note:** Unknown: file not retrieved
- **Format:** PDF; extracted tables pending
- **Spatial Resolution:** Building-address records, not georeferenced raster
- **Temporal Coverage:** Candidates 2018-2020 and 2023-2026; gaps 2017/2021/2022
- **Coordinate System:** None in PDF; addresses require geocoding
- **Relevant Fields Bands:** Ward; serial; building name/address; ownership in older lists; beat in newer lists
- **Missing Values:** Unknown: file not retrieved
- **License:** No explicit reuse license verified
- **Model Use:** Potential C-1 target/validation after matching; C-1 is not observed collapse
- **Notes:** No full annual panel downloaded or matched. First appearance remains uncomputed, and earliest observed listing is not the date deterioration began.
- **Source:** [Mumbai C-1 dangerous/dilapidated building lists](https://portal.mcgm.gov.in/irj/portal/anonymous/qlrelatedlinkspage)

### Raw Sentinel-1 (InSAR requires SLC)

- **Download Status:** BLOCKED_NETWORK
- **File Names:** Not selected: scene inventory unavailable
- **Size Note:** Unknown: file not retrieved
- **Format:** SAFE ZIP; complex measurement TIFF and XML
- **Spatial Resolution:** Product-dependent; SLC slant-range sampling differs from ground resolution
- **Temporal Coverage:** Scene dates unverified; mission archive begins 2014
- **Coordinate System:** Slant-range radar geometry; geolocation XML, no ordinary map-grid EPSG
- **Relevant Fields Bands:** Complex amplitude/phase; available polarizations; orbit and burst timing
- **Missing Values:** Unknown: file not retrieved
- **License:** Copernicus Sentinel data terms; ASF access agreement applies
- **Model Use:** DL input after coregistration/calibration; derive interferograms/coherence/displacement; not collapse label
- **Notes:** Catalog: https://search.asf.alaska.edu/#/ . Earthdata authentication needed for archive downloads. Missing bursts, temporal gaps and decorrelation require inspection.
- **Source:** [Raw Sentinel-1 (InSAR requires SLC)](https://docs.asf.alaska.edu/datasets/using_ASF_data/)

### Google Open Buildings v3

- **Download Status:** BLOCKED_NETWORK
- **File Names:** S2 level-4 polygon shards not yet selected
- **Size Note:** Unknown: file not retrieved
- **Format:** gzip CSV with WKT polygon geometry
- **Spatial Resolution:** Building polygons; no raster pixel resolution
- **Temporal Coverage:** Inference May 2023; per-building imagery dates absent
- **Coordinate System:** Longitude/latitude; verify geographic CRS before spatial joins
- **Relevant Fields Bands:** latitude; longitude; area_in_meters; confidence; geometry; full_plus_code
- **Missing Values:** Unknown: file not retrieved
- **License:** Choose CC BY 4.0 or ODbL 1.0
- **Model Use:** DL input after rasterization; baseline footprint/area/density; weak segmentation label; no structural safety label
- **Notes:** Confidence >=0.65 in released detections. Download tile index and select intersecting shards. Detection omissions are not measured null values.
- **Source:** [Google Open Buildings v3](https://sites.research.google/gr/open-buildings/)

### WSF Evolution

- **Download Status:** BLOCKED_NETWORK
- **File Names:** Tile not retrieved; see acquisition_plan.json
- **Size Note:** Unknown: file not retrieved
- **Format:** GeoTIFF
- **Spatial Resolution:** 30 m nominal
- **Temporal Coverage:** 1985-2015 annual settlement detection
- **Coordinate System:** EPSG:4326
- **Relevant Fields Bands:** Settlement detection year 1985-2015; companion annual IDC score 1-6
- **Missing Values:** Publisher: 0 is no data; actual pixel counts unknown
- **License:** CC BY 4.0
- **Model Use:** DL input/baseline settlement history; validation only for settlement detection
- **Notes:** Settlement detection year is not the construction year of an individual building. 1985 is left censored; newer/replaced buildings require separate evidence.
- **Source:** [WSF Evolution](https://web.geoservice.dlr.de/web/datasets/wsf_evo)

### GHSL: selected candidate GHS-BUILT-S R2023A

- **Download Status:** BLOCKED_NETWORK
- **File Names:** Product/epoch/CRS tiles pending selection
- **Size Note:** Unknown: file not retrieved
- **Format:** GeoTIFF, typically ZIP
- **Spatial Resolution:** 100 m or 1 km; 2018 anchor also 10 m
- **Temporal Coverage:** 1975-2030 every 5 years; interpolated/extrapolated; 2018 anchor
- **Coordinate System:** ESRI:54009 Mollweide or EPSG:4326, product dependent
- **Relevant Fields Bands:** Built-up surface m²; optional non-residential surface
- **Missing Values:** Product-specific nodata; actual counts unknown
- **License:** EU reuse with source acknowledgment; confirm selected product terms
- **Model Use:** DL input/baseline built-up intensity/history; no collapse target
- **Notes:** User linked a product portal, not a single dataset. GHS-POP/SMOD/AGE are distinct products; record release and epoch for each acquired file.
- **Source:** [GHSL: selected candidate GHS-BUILT-S R2023A](https://human-settlement.emergency.copernicus.eu/ghs_buS2023.php)

### Copernicus DEM: GLO-30 candidate

- **Download Status:** BLOCKED_NETWORK
- **File Names:** Geocells pending selection
- **Size Note:** Unknown: file not retrieved
- **Format:** GeoTIFF DGED; DTED alternative
- **Spatial Resolution:** 1 arcsecond (~30 m), geographic grid
- **Temporal Coverage:** Main acquisitions 2011-2015; older gap fills
- **Coordinate System:** EPSG:4326 horizontal; EGM2008 vertical (EPSG:3855)
- **Relevant Fields Bands:** Elevation metres; optional editing/filling/water/error masks
- **Missing Values:** Unknown: file not retrieved
- **License:** Copernicus DEM free license with attribution; not assumed CC BY
- **Model Use:** DL input and baseline elevation/slope; terrain validation only with independent reference
- **Notes:** Digital surface model includes vegetation and buildings. Auxiliary quality masks are not guaranteed in every mirror. Zero elevation is not automatically missing.
- **Source:** [Copernicus DEM: GLO-30 candidate](https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM)

### WorldPop India population counts

- **Download Status:** BLOCKED_NETWORK
- **File Names:** India raster filename not verified from listing
- **Size Note:** Unknown: file not retrieved
- **Format:** GeoTIFF candidate
- **Spatial Resolution:** Select 100 m or 1 km series; linked listing does not fix a product
- **Temporal Coverage:** Candidate Global1 2000-2020 annual; constrained 2020 separate; exact product pending
- **Coordinate System:** Geographic CRS expected; verify file
- **Relevant Fields Bands:** Population count per grid cell; UN adjustment/constrained status must be recorded
- **Missing Values:** Unknown: file not retrieved
- **License:** CC BY 4.0
- **Model Use:** DL input/baseline exposure; not individual collapse label or independent outcome validation
- **Notes:** Listing is dynamic and does not expose a specific India asset. Country selection, year and constrained/UN-adjusted status unresolved.
- **Source:** [WorldPop India population counts](https://hub.worldpop.org/geodata/listing?id=78)

### India-WRIS groundwater

- **Download Status:** BLOCKED_NETWORK
- **File Names:** No station export or API asset recovered
- **Size Note:** Unknown: file not retrieved
- **Format:** Portal tables/export format unverified
- **Spatial Resolution:** Observation-well points; no regular raster resolution
- **Temporal Coverage:** Station-specific seasons/dates; Mumbai coverage unverified
- **Coordinate System:** Station-coordinate datum unverified
- **Relevant Fields Bands:** Required: station ID, location, date, depth below ground/water level, units and quality; actual schema unknown
- **Missing Values:** Unknown: file not retrieved
- **License:** No explicit export license verified
- **Model Use:** Potential temporal DL input/baseline groundwater trend; no collapse label
- **Notes:** Do not interpret depth below ground as hydraulic head or assign unsupported interpolation. Basin documentation describes seasonal monitoring, not verified Mumbai station data.
- **Source:** [India-WRIS groundwater](https://indiawris.gov.in/wris/#/)

## Feasibility decisions

These model-use judgments are analysis, not publisher claims. Keep measured collapse events separate from official danger classifications and from subsidence-derived risk. Predicting the latter from their own VLM inputs tests reproduction of the risk rule, not independent collapse prediction.

Use spatially separated evaluation and time cutoffs. A 2015-2023 average VLM rate includes measurements after earlier events and cannot be treated as a pre-event predictor for those events. Match footprint acquisition dates to events, distinguish missing outcomes from confirmed safe buildings, and retain geocoding uncertainty.

No sample size, null count, CRS, risk-class distribution, checksum, or download completeness has been verified from the requested files. A deep-learning-ready training set cannot yet be certified.

## Rerun

From the project root:

```bash
.venv/bin/python feasibility/download_audit_cities.py --download
```

This attempts pinned Mumbai Figshare v2, the full current Lagos Figshare inventory, and every recovered official C-1 PDF. `--download-extra` also attempts candidate city WSF/DEM files. `--audit-only` inspects files already placed in each downloads folder. GHSL, Open Buildings shards, WorldPop and groundwater still need product/asset selection; raw SLC needs scene selection and authenticated access. See acquisition_plan.json.

## C-1 yearly recovery

Official PDF links found for 2018-19, 2019-20, 2020-21, 2024 and 2026-27. The user supplied 2023 and 2025-26 candidates. The generic C1 Buildings.pdf contains the date 23-Apr-2024; the 2026 portal link leads to a PDF dated 30-Apr-2026. No yearly list recovered for 2017, 2021 or 2022. A missing search result does not prove that a list was never published.

First-appearance computation is blocked by missing local PDFs and unreviewed table extraction. Do not use serial numbers as persistent IDs. Match ward, plot/CTS identifiers, full address and building/wing name; retain OCR spelling variants and source page. Grouped building ranges must be split only when the underlying addresses identify separate buildings.

Report first_seen_year as the minimum matched observed year, with left_censored=true when earlier lists are missing. A disappearance can indicate demolition, evacuation, repair, delisting or a changed spelling; it does not establish safety. The first_appearance_template.csv is header-only and contains no fabricated matches.

## Additional source evidence

[Indian megacities paper](https://www.nature.com/articles/s41893-025-01663-0) documents Mumbai’s 2015–2023 descending-orbit observations. This temporal coverage is paper metadata; it has not been verified against the requested v2 files.

[Official 2025 PDF](https://portal.mcgm.gov.in/irj/go/km/docs/documents/HomePage%20Data/Whats%20New/List%20of%20C-1%20Catagory%20Dilapilated%20Buildings%202025-26%20%281%29.pdf) is dated 30-Apr-2025. Its browser text includes trailing serials without corresponding attributes, illustrating why serial totals and complete rows must be reconciled against rendered pages before matching.
