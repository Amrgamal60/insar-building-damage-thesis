# Alexandria collapse-risk data

AOI (clip bbox): 29.75–30.15 E, 31.05–31.38 N. Python env: `../.venv` (rebuilt 2026-10-07 on the new PC with uv, Python 3.12.7; versions in `../requirements.txt`).

## Downloaded (`raw/`)

| Folder | Layer | Source | Notes |
|---|---|---|---|
| collapse_osf | Collapse records, DSAS shorelines 1887/1959/2001/2021, susceptible-collapse polygons | https://osf.io/98pyu (Fouad et al. 2025, doi:10.1029/2024EF004883) | Collapse records are district-level, not GPS points |
| buildings_google_v3 | Building footprints (S2 tile 14f, raw) | Google Open Buildings v3 | Clipped: `interim/google_buildings_v3_alex.csv` (518,291 buildings) |
| dem_fabdem | Bare-earth DEM 30 m (N31E029, N31E030) | FABDEM v1-2, Univ. Bristol | |
| soilgrids | clay, sand, silt, bdod, soc, phh2o, cfvo, nitrogen, cec × 6 depths | ISRIC SoilGrids 2.0 (files.isric.org) | Resampled to EPSG:4326 at 0.0025° |
| insar_vlm_shirzaei | Vertical land motion (IGS14, InSAR points) | VT Figshare 25864435 | `LLIVS_IGS14_Alexandria.csv` |
| insar_licsar | LiCSAR frame metadata (E/N/U, hgt, vlos_eur, baselines) | COMET LiCSAR, frames 065D_05935_131108, 131A_05957_110910 | Interferograms not downloaded (1153 + 2199, Oct 2014–Sep 2023). They moved to CEDA (`data.ceda.ac.uk/neodc/comet/data/licsar_products/<track>/<frame>/<pair>/`, open); the GeoTIFFs are striped, so a city window reads remotely in about 2 s. Check of 2026-09-30 (4 sample pairs, 2015–2016): 351–354 of 416 historic-core cells at 250 m have valid unwrapped pixels, including all 241 Shirzaei-covered cells and all 34 core collapse cells; median coherence 0.40–0.61 |
| sealevel_psmsl | Alexandria tide gauge, metric monthly (1944–) | PSMSL station 503 | No RLR series available |
| weather_openmeteo | Daily weather 1980–2026 at 3 points | Open-Meteo archive (ERA5-based) | Stand-in until ERA5 via CDS |
| seismic | Earthquakes M≥2.5, 27.5–32.5E / 29.5–33.5N | USGS FDSN | |
| ghsl_age | Built-up age epochs 1975–2020, 100 m, global zip | GHS-AGE R2025A | Needs clip (Mollweide 54009) |
| ghsl_obat | Building attributes (height, age, use), Egypt GPKG | GHS-OBAT R2024A | Needs clip |
| wsf_evolution | Settlement year 1985–2015, 30 m | DLR WSF Evolution | |
| worldcover | Land cover 2021, 10 m | ESA WorldCover v200 | |
| osm | OSM Egypt extract (2026-09-28) | Geofabrik | building:levels, historic tags; street gazetteer for geocoding |
| insar_deltas_ohenhen2025 | Vertical land motion grids, 40 deltas (use `nile_vlm.tif`), ~0.0083° (~900 m), Sentinel-1 2014–2023 | Ohenhen et al. 2025 Nature, Zenodo 10.5281/zenodo.15015923 (CC-BY-4.0) | Covers ~54% of the city window; coarse but has a documented period |
| overture_places | 31,797 places in the city window, 29,735 with free-form address | Overture Maps places, release 2026-09-23.0 (CDLA-Permissive-2.0) | Fallback gazetteer in `scripts/02` (only where OSM fails): placed 2 records at street level |
| ghsl_built_s | Built-up surface 1975, 2000, 2015, 2020, 100 m (tile R6_C21) | GHS-BUILT-S R2023A (JRC FTP tiles) | Mollweide 54009 |
| ghsl_built_h | Building height 2018: ANBH (net) and AGBH (gross), 100 m (tile R6_C21) | GHS-BUILT-H R2023A (JRC FTP tiles, no GEE needed) | |
| wsf_evolution/idcscore | Input Data Consistency score for WSF Evolution | DLR | 6 (very good) across the city |
| gsw | Surface water occurrence, change, transitions 1984–2021 (tiles 20E_40N, 30E_40N) | JRC Global Surface Water v1.4 (GCS direct) | Yearly 1984–2021 history is Earth Engine only |
| admin_geoboundaries | Egypt ADM2 (kism/markaz) polygons | geoBoundaries gbOpen EGY ADM2 (CAPMAS/OCHA 2020) | Police-district constraint for geocoding |
| literature | Mohamadi, Balz & Younes 2020, Remote Sens 12:3307 (PDF, CC BY) | MDPI (mdpi-res.com CDN link) | Closest prior work; its GPS-located inventory (255 collapses 2001–2019) is not public, requested from the authors 2026-09-29 |

## Collapse inventory (`inventory/`)

The audited, geocoded collapse inventory is in `inventory/`, built by `scripts/01–03`. `inventory/AUDIT_REPORT.md` has the numbers and the open decisions.

## Pilot (`pilot/`)

The restricted pilot (target rule, 250 m cells, urban/coastal baseline with and without velocity) is built by `scripts/06_pilot_sample.py` and `scripts/07_pilot_models.py`. `pilot/PILOT_REPORT.md` has the sample, the review decisions and the results.

LiCSAR replication (2026-09-30), following the pre-registered `pilot/LICSAR_TEST_PLAN.md`:
- `licsbas/<frame>/`: the LiCSBAS run per frame (`GEOCml1`, `TS_GEOCml1`, `log`) and `velocity/` (P1 = first epoch to 2016-12-31, P2 = full period, line of sight, mm/yr, with the E/N unit vectors); `licsbas/decomposed/`: vertical (UD) and east–west (EW) velocity from both frames. Made by `scripts/15_licsbas_run.sh`.
- `pilot/licsar_cells_<res>m.csv` and `LICSAR_CELLS.md` (`scripts/16_licsar_cells.py`): velocity per cell, coverage and agreement with Shirzaei.
- `pilot/LICSAR_VARIOGRAM_CHECK.md` (`scripts/17_licsar_test.py --check`), then `pilot/LICSAR_TEST.md`, `licsar_test*.csv` and `licsar_test.png` (`scripts/17_licsar_test.py`): the decision and secondary tests 1–5.
- `pilot/LICSAR_LOCATION_CHECKS.md` and `location_checks_licsar_<res>m.csv` (`scripts/18_licsar_location_checks.py`): secondary test 6.

## Tools (`../tools/`)

- **LiCSBAS** (InSAR time series): `tools/LiCSBAS`, cloned from github.com/comet-licsar/LiCSBAS at commit a145e6c4217b29eb7348ea95630454a099809098 (2026-07-17). It runs in its own conda env `licsbas` (conda-forge only: Python 3.11.16, GDAL 3.12.3, numpy 2.3.5, astropy 6.1.7; created 2026-09-30, recreated 2026-10-07 on the new PC with Miniforge at `~/miniforge3`, exact versions in `tools/licsbas_env.yml`; `LiCSBAS_check_install.py` OK; the optional pygmt and usgs-libcomcat are not installed), not in `.venv` (no GDAL Python bindings there) and not in base. numpy was downgraded from 2.4.6 on 2026-09-30 because astropy 6.1.7, which LiCSBAS imports, needs `np.in1d`, removed in numpy 2.4; the first run stopped on this (`data/licsbas/run_attempt1_failed_numpy.log`). The full run is `scripts/15_licsbas_run.sh`, into `data/licsbas/`. Use: `PATH=tools/LiCSBAS/bin:$PATH PYTHONPATH=tools/LiCSBAS/LiCSBAS_lib ~/miniforge3/envs/licsbas/bin/python tools/LiCSBAS/bin/<step>.py`.

## Needs an account (not yet downloaded)

- Sentinel-1 SLC / Sentinel-2 L2A: Copernicus Data Space (dataspace.copernicus.eu)
- Landsat C2: USGS EarthExplorer (or Planetary Computer STAC, no login)
- ERA5 / ERA5-Land: Copernicus CDS (`~/.cdsapirc`)
- CMEMS MEDSEA_MULTIYEAR_PHY_006_004, MEDSEA_MULTIYEAR_WAV_006_012, SEALEVEL_EUR_PHY_L4_MY_008_068: Copernicus Marine
- Google Open Buildings 2.5D Temporal: Google Earth Engine only
- GRACE-FO mascons, SMAP L4: NASA Earthdata
