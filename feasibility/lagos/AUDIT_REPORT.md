# Lagos dataset feasibility audit

Audit date: 2026-10-10. **No requested source dataset has been downloaded into this city folder.** Shell networking is disabled (`CODEX_SANDBOX_NETWORK_DISABLED=1`) and host DNS lookups failed. Browser metadata is evidence of availability, not a local download or byte-level audit. Unknown sizes and missing-value counts remain unknown. Existing Alexandria files are not city downloads.

## Dataset findings

### Complete Lagos collapse + InSAR/risk dataset

- **Download Status:** BLOCKED_NETWORK
- **File Names:** BuildingCollapseTable.xlsx; InSAR_data.csv; Longitude.csv; Latitude.csv; 4 risk GeoTIFF and 4 risk CSV names not verified
- **Size Note:** Unknown: file not retrieved
- **Format:** XLSX; CSV; GeoTIFF
- **Spatial Resolution:** Point and raster resolution unverified
- **Temporal Coverage:** InSAR 2018-2021 (paper); collapse catalog dates pending; risk 4/10/35/75 years
- **Coordinate System:** Unverified until CSV coordinates, README and TIFF CRS inspected
- **Relevant Fields Bands:** VLM/east-west cm/year; collapse records; risk classes; coordinate matrices; exact schema pending
- **Missing Values:** Unknown: file not retrieved
- **License:** CC0 1.0 (catalog record)
- **Model Use:** VLM DL input/baseline; collapse catalog target/validation after deduplication/geocoding; risk maps derived baseline/weak targets
- **Notes:** Catalog describes 12 files and 106 incidents. Paper maps 43 geolocated incidents in 2000-2022; do not assume all 106 have coordinates. Request every file returned by Figshare API, not only known filenames. Primary landing failed browser 403.
- **Source:** [Complete Lagos collapse + InSAR/risk dataset](https://data.lib.vt.edu/articles/dataset/Data_for_Hotspot_for_Building_Collapse_due_to_Land_Subsidence_in_the_Coastal_City_of_Lagos_West_Africa/19738957)

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

## Supporting evidence

[Original Lagos study](https://agupubs.onlinelibrary.wiley.com/doi/10.1029/2022EF003219) gives ascending path 1/frame 1200 and descending path 95/frame 571. [Repository catalog record](https://datasetcatalog.nlm.nih.gov/dataset?q=0002727202) supplies the advertised inventory and CC0 license; file-level verification is still pending.

## Additional source evidence

[DLR collection](https://geoservice.dlr.de/eoc/ogc/stac/v1/collections/WSF_Evolution?f=html) confirms CC BY 4.0. [ASF download documentation](https://docs.asf.alaska.edu/api/basics/) requires Earthdata login. Neither confirms local acquisition.
