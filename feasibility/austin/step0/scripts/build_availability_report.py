"""Build the public aggregate report from private checks and source evidence."""
import argparse
import datetime as dt
import json
from pathlib import Path
import urllib.parse

p=argparse.ArgumentParser()
p.add_argument('--private',type=Path,required=True)
p.add_argument('--outdir',type=Path,required=True)
a=p.parse_args()
manifest=json.loads((a.outdir/'tcad_manifest.json').read_text())
roll=json.loads((a.private/'derived_2026/summary.json').read_text())
static=json.loads((a.private/'static_checks_2026/static_summary.json').read_text())
population=json.loads((a.private/'final_population_2026/population_summary.json').read_text())
ids=json.loads((a.private/'id_match_2026.json').read_text())

def source(part,method=None):
    got=[x for x in manifest if part in x['url'] and x.get('http_status')==200 and not x.get('error') and (method is None or x['method']==method)]
    return got[-1] if got else None

def link(text,url):return '['+text+']('+url+')'
def n(value):return f'{value:,}'
def pct(value):return f'{value:.4f}%'
def evidence(entry,label):
    if entry is None:return f'- {label}: UNVERIFIED.\n'
    return f"- {link(label,entry['url'])}: accessed {entry['access_date_utc']}; HTTP {entry['http_status']}; {n(entry.get('size_bytes',0))} saved bytes; SHA-256 `{entry.get('sha256')}`; private file `{entry.get('local_path')}`.\n"

full=source('2026%20Certified%20Appraisal%20Export%20Supp%200_07182026.zip','GET')
layout=source('Website_Legacy8.0.33-AppraisalExportLayout_06182026.zip','GET')
boundary=source('/resource/vnwj-xmz9.geojson','GET')
permit=source('/resource/3syk-w9eu.csv','GET')
publicinfo='https://traviscad.org/publicinformation'
ears_names={2022:'227EARS092822%20%282%29.zip',2023:'227EARS082923%20%282%29.zip',
            2024:'227EARS082824%20%282%29.zip',2025:'227EARS090425.zip',2026:'227EARS082626.zip'}
years=[]
for year in range(2016,2027):
    entry=source(ears_names[year],'HEAD') if year in ears_names else None
    years.append({'year':year,'full_certified_characteristics_export':
        {'status':'DOWNLOADED_AND_INSPECTED','source':full,'format':'True Prodigy Legacy 8.0.33 fixed-width text ZIP'} if year==2026 else
        {'status':'UNVERIFIED','reason':'No functioning anonymous full certified-characteristics export recovered; EARS availability is listed separately'},
        'ears_submission':{'status':'HEAD_VERIFIED','source':entry,'format':'ZIP; EARS submission layout is comma-delimited quoted text; archive members not opened'} if entry else None})

collections=json.loads(Path(source('collections?search=Land%20Parcels')['local_path']).read_text())['results']
geometry_inventory=[]
for c in sorted(collections,key=lambda x:x['acquisition_date']):
    matching=[]
    for e in manifest:
        if '/api/v1/resources?collection_id='+c['collection_id'] in e['url'] and e.get('http_status')==200 and e.get('local_path'):
            result=json.loads(Path(e['local_path']).read_text())
            matching.extend(x for x in result.get('results',[]) if x.get('area_type_name')=='Travis')
    unique={x['resource']:x for x in matching}
    geometry_inventory.append({'collection_year':int(c['acquisition_date'][:4]),'collection_id':c['collection_id'],
        'collection_acquisition_date':c['acquisition_date'],'publication_date':c['publication_date'],
        'catalog_crs':'EPSG:'+c['spatial_reference'],'license':c['license_name'],'license_url':c['license_url'],
        'travis_resources':list(unique.values()),
        'status':'LISTED; direct file retrieval UNVERIFIED (CloudFront 403 for tested 2019/2026 URLs)' if unique else 'NO_TRAVIS_RESOURCE_RETURNED_BY_API'})

body_bytes=sum(e.get('size_bytes',0) for e in manifest if e['method']=='GET')
header_bytes=sum(e.get('size_bytes',0) for e in manifest if e['method']=='HEAD')
summary={'access_date_utc':'2026-10-28','status':'COMPLETED_WITH_HISTORICAL_ITEMS_UNVERIFIED_AS_DIRECTED_BY_COORDINATOR',
    'scope':{'complete_rolls_downloaded_and_inspected':[2026],
        'other_roll_bodies_opened':False,'2018_mirror_header_and_layout_only':True,
        'permit_join':'500-row uniform random ID check only; no outcome filters',
        'insar_opera_sentinel_data_or_metadata_opened':False,'models_fitted':False,'events_built':False},
    'roll_availability':years,'earlier_rolls':{'status':'UNVERIFIED','reference_roll_at_or_before_2016':None,
        'historical_lead':'Open Austin 2017 README said electronic records dated back to 2007; current downloadable availability and price unverified'},
    'txgio_geometry_inventory':geometry_inventory,
    'geometry_verified':[
        {'label':'Legacy TCAD_Parcels published 2012-04-11','source':source('/items/5b315f0617c84b42a4b2992af8796d81/data'),
         'features':326095,'crs':'EPSG:2277','ground_vintage':'UNVERIFIED; metadata modified 2009-07-23, ground-date placeholder'},
        {'label':'Parcels_Travis_2016 NON-OFFICIAL research mirror','metadata':source('Parcels_Travis_2016_f_ao/FeatureServer/0?'),
         'sample':source('Parcels_Travis_2016_f_ao/FeatureServer/0/query?where=1%3D1&outFields='),
         'features':342776,'sample_features':10,'service_crs':'EPSG:3857','original_shapefile_crs':'EPSG:2277',
         'certified_status':'UNVERIFIED','license':'UNVERIFIED; no explicit layer licence'},
        {'label':'TNRIS September 2019 mirror','source':source('/items/4061b026210d40bfb25a559281cba008/data'),
         'features':353920,'crs':'EPSG:3857','format':'ZIP shapefile'},
        {'label':'TCAD Parcels Dec 2025 hosted layer, updated 2026-10-02','features':386682,'unique_property_ids':373524,
         'native_crs':'EPSG:2277','download_crs':'EPSG:32614','pages':39,
         'vintage':'Exact geometry observation date UNVERIFIED; named Dec 2025 but updated monthly'}],
    'roll_2026_inspection':roll,'static_2026_checks':static,'permit_id_check_2026':ids,
    'population_2026_diagnostic':population,
    'earliest_population_check':{'status':'UNVERIFIED','reason':'No qualifying pre-2017 certified roll obtained; no 2016 count inferred from 2026'},
    'consequences':{'section4_sale_split':'NOT RUN as written: only one inspected certified characteristics roll; consecutive annual deed dates unavailable',
        'section5_reference_roll':'Pre-2017 certified reference UNVERIFIED; supervisor must choose fallback; A1 is the house code, not broad PTD A',
        'section9_foundation_rule_2026_diagnostic':population['eligible_2026_coverage']['main_dwelling_foundation']['nonblank_percent']>=90,
        'section9_reference_roll_rule':'UNVERIFIED for an actual historical reference population; 2026 attributes may be post-event',
        'gpu_unique_30m_cells_diagnostic':population['unique_30m_cells_epsg32614']},
    'download_accounting':{'get_response_body_bytes':body_bytes,'saved_head_response_header_bytes':header_bytes,
        'total_saved_download_evidence_bytes':body_bytes+header_bytes,'limit_bytes':20_000_000_000,
        'compressed_or_wire_sizes_not_uncompressed_sizes':True,'failed_response_bodies_and_retries_included':True},
    'terms':{'tcad':{'free_public_bulk_export':True,'export_specific_license':'UNVERIFIED; no export-specific licence found',
        'general_public_domain_statement':'All information contained herein is considered in the public domain and is distributed without warranty of any kind, implied, expressed or statutory.',
        'source':'https://traviscad.org/propertysearch','free_access_source':'https://traviscad.org/faqs'},
        'txgio':{'license':'CC0-1.0','source':'https://creativecommons.org/publicdomain/zero/1.0/'},
        'non_official_mirrors':'Data-specific licence UNVERIFIED; software licence not assumed to cover data'},
    'routes_user_action_required':[
        {'route':'TCAD countywide GIS copy','published_cost_usd':4,'historical_vintages_and_accompanying_tables':'UNVERIFIED','source':'https://traviscad.org/faqs'},
        {'route':'TCAD records request','requested_roll_years':list(range(2016,2026)),
         'published_predefined_pdf_roll_cost_usd':5,'historical_electronic_export_cost':'UNVERIFIED',
         'historical_2017_claim_usd_per_year':80,'historical_records_claim_begin_year':2007,
         'source':publicinfo,'portal':'https://traviscad.govqa.us/WEBAPP/_rs/SupportHome.aspx','agency_email':'recmgr@tcadcentral.org'},
        {'route':'TxGIO browser/source follow-up','listed_travis_years':[2019,2024,2025,2026],'tested_direct_download_http_status':403},
        {'route':'NON-OFFICIAL TXHousing mirror','roll_year':2018,'certification':'PRELIMINARY',
         'export_run_date':'2018-04-10T07:56','export_layout_version':'8.0.0.20','repository_readme_commit_date':'2018-08-20',
         'data_license':'UNVERIFIED','property_and_improvement_bodies_opened':False,
         'header':source('export=download&id=1_RFxw6aoNNblsGRxlCQVLRDUMkeDuNTc'),
         'layout':source('export=download&id=1YRrDHgCJBviFxPCe24wYSswKpudunpzf'),
         'source':'https://github.com/amspector100/TXHousing'}],
    'verification':{'saved_file_hashes_and_sizes_verified':147,'aggregate_count_and_cell_checks':'PASSED',
        'privacy_grep_owner_mailing_contractor_field_patterns':'NO MATCHES in feasibility/austin/step0',
        'source_body_files_outside_private_tree':False},
    'manifest':'feasibility/austin/step0/tcad_manifest.json'}
(a.outdir/'tcad_availability.json').write_text(json.dumps(summary,indent=2)+'\n')

city_n=population['a1_built_2015_or_earlier_inside_full_purpose']
cells=population['unique_30m_cells_epsg32614']
foundation=population['eligible_2026_coverage']['main_dwelling_foundation']
lines=[f'''# TCAD availability check — Austin pre-freeze step 0

Access date: **2026-10-28 UTC**. This audit opens one complete certified roll, **2026**, and no InSAR, OPERA or Sentinel data or metadata. No events, outcome counts or models were built. The only permit–roll join is the authorized random sample of 500 permits from the full nonblank-ID population. Raw responses and row-level derivatives are under `/mnt/data/Master-projects/Alex_private/austin/tcad/`.

**Decision-relevant result:** a certified roll dated 2016 or earlier is **UNVERIFIED**, so its field coverage, identifier match rate and population count are also UNVERIFIED. From the **2026 certified roll**, the diagnostic population is **{n(city_n)} parcels in {n(cells)} unique 30 m cells**, using the official full-purpose boundary updated **2026-10-27**. Main-dwelling foundation coverage in that population is **{n(foundation['nonblank'])}/{n(city_n)} = {pct(foundation['nonblank_percent'])}**. These are 2026 diagnostics, not a historical population reconstructed for the study.

The coordinator explicitly directed completion with historical items marked UNVERIFIED after the archive/access failures described below. No purchase, account creation, records request or verification-gate workaround was attempted.

## 1. Certified appraisal rolls available today

The [TCAD Public Information page]({publicinfo}) currently links the 2026 certified full-characteristics export, a certified JSON alternative, supplements, and EARS submissions for 2022–2026. EARS is a distinct Comptroller submission product; it is not assumed to contain the improvement-detail/attribute tables needed here. HEAD checks establish anonymous availability and compressed size; they do **not** establish the contents of an unopened ZIP. Full-roll certification claims for years other than 2026 remain UNVERIFIED.

| Year | Verified retrieval / source | Format and compressed bytes | What remains unverified |
|---|---|---|---|
''']
for year in range(2016,2027):
    if year==2026:
        lines.append(f"| 2026 | {link('Certified July export; downloaded',full['url'])} | True Prodigy Legacy 8.0.33 fixed-width text ZIP; {n(full['size_bytes'])} | Inspected and internally confirmed year 2026 and supplement 0 |\n")
    elif year in ears_names:
        e=source(ears_names[year],'HEAD')
        lines.append(f"| {year} | {link('TCAD EARS submission; HEAD 200',e['url'])} | ZIP, {n(e['remote_size_bytes'])}; EARS manual specifies quoted comma-delimited text | Members, certification snapshot and characteristics completeness UNVERIFIED; body not opened |\n")
    else:
        lead={2016:'[2017 Open Data Census](https://us-city.census.okfn.org/entry/austin/assessment.html) said a 2016 certified export was then downloadable; current direct retrieval fails TLS validation and is UNVERIFIED',
              2017:'No functioning certified download recovered; WordPress media search yielded no roll',
              2018:'Public TXHousing tables are 2018 PRELIMINARY, not certified; header/layout only inspected',
              2019:'No functioning certified characteristics export recovered',
              2020:'No functioning certified characteristics export recovered',
              2021:'No functioning certified characteristics export recovered'}[year]
        lines.append(f'| {year} | UNVERIFIED | Format / compressed size UNVERIFIED | {lead} |\n')
lines.append(f'''
The 2026 certified JSON alternative is also HEAD 200: {link('2026 Certified JSON SUPP 0',source('2026%20Certified%20JSON%20SUPP%200%2007182026.zip','HEAD')['url'])}, **3,554,021,795 bytes**. It was not downloaded. The 2026 EARS ZIP is HEAD 200, **103,303,062 bytes**, and was not opened.

A separate [public academic repository](https://github.com/intelligent-environments-lab/tcad) advertises parsed **2023 certified-export** tables. Its `PROP.parquet` (**42,898,692 bytes**), `IMP_INFO.parquet` (**5,698,970**), `IMP_DET.parquet` (**40,296,862**) and `IMP_ATR.parquet` (**25,651,660**) all return HEAD 200. These are **NON-OFFICIAL processed subsets**, not a recovered full original roll; bodies, internal year, field completeness, certification fidelity and data-specific licence are UNVERIFIED. The original export URL preserved in the repository's downloader returns **404**. These four tables were not downloaded or read, preserving the roll-inspection limit.

**Earlier than 2016:** [Open Austin's historical project README](https://github.com/open-austin/liberate-appraisal-data) says electronic records extended back to **2007** and describes a historical **$80 per appraisal year** MS Access delivery route. That is a **2017 statement**, not today's price or proof of today's downloads. No earlier certified body was obtained.

**Search/access evidence:** TCAD's current page and anonymous WordPress media searches did not expose a legacy certified archive. The [Travis County portal](https://www.traviscountytx.gov/open-data-portal) points to tax-office data and GIS; no qualifying historical certified-characteristics download was recovered. Austin's `kk8y-6cmt` “Land Database 2021” has a stale description mentioning October 2016, but an outcome-blind aggregate query shows **269,681 rows with `propval_yr=2021` and 1,887 missing-year rows**: it was not substituted for a 2016 roll. The [Texas Comptroller reports portal](https://comptroller.texas.gov/taxes/property-tax/reports/index.php) supplied reports/layout guidance, not a recovered pre-2017 TCAD account-level roll. Archive.org's CDX requests timed out and the availability endpoint returned **429**; Common Crawl returned **504**. These failures establish an unresolved access route, not that the historical records do not exist.

### Cost and terms

TCAD's [FAQ](https://traviscad.org/faqs) says an electronic roll is available free: “an electronic copy of the entire appraisal roll data is made available free of charge on the appraisal district website.” Its [general property-information statement](https://traviscad.org/propertysearch) says: “All information contained herein is considered in the public domain and is distributed without warranty of any kind, implied, expressed or statutory.” The bulk ZIP is linked expressly from Public Information. **No export-specific licence file was found**; whether the general statement applies identically to each export is UNVERIFIED. This audit did not bulk-scrape the property-search or map-search sites.

TxGIO's collection metadata identifies **Creative Commons Zero v1.0 Universal (CC0-1.0)**. The [CC0 deed](https://creativecommons.org/publicdomain/zero/1.0/) states: “You can copy, modify, distribute and perform the work, even for commercial purposes, all without asking permission.” Research mirrors without an explicit data licence are marked UNVERIFIED rather than assuming the repository's software licence licenses the data.

## 2. Parcel geometry and vintages

**Yes: a publicly queryable layer explicitly dated 2016 exists.** The NON-OFFICIAL [Parcels_Travis_2016 mirror](https://services.arcgis.com/8vL8ZFWfQxhb4uIP/arcgis/rest/services/Parcels_Travis_2016_f_ao/FeatureServer/0) has **342,776 polygon features**, service CRS **EPSG:3857**, and public item creation/modification in March 2018. Its original public [research-folder shapefile](https://drive.google.com/drive/folders/1WzyFvm_8quAanIyYPv7Y2qVEbXyuStza) has an independently downloaded `.prj` identifying **EPSG:2277**. A 10-polygon query selecting only IDs and geometry succeeded. Full 2016 geometry was not needed for the unavailable 2016-roll count; the exact acquisition date, certification tie and data licence remain UNVERIFIED. Its attributes include `PROP_ID`, `PID_10`, `geo_id`, `deed_date` and `tcad_acres`, but **no state code or year-built field**, so it cannot supply the missing historical eligibility by itself.

| Geometry product | Accessible evidence | Format / CRS / size | Vintage limitation |
|---|---|---|---|
| Legacy `TCAD_Parcels`, published 2012-04-11 | {link('Public ArcGIS ZIP; downloaded','https://www.arcgis.com/sharing/rest/content/items/5b315f0617c84b42a4b2992af8796d81/data')} | Shapefile; EPSG:2277; 326,095 polygons; 80,836,234 compressed bytes | Public file existed by 2012; XML modification date 2009-07-23; ground-date field is a placeholder, so exact ground vintage UNVERIFIED |
| `Parcels_Travis_2016` | Public service count, schema, 10 polygons and original `.prj` | Polygon service EPSG:3857; original shapefile EPSG:2277 | Explicit 2016 label; NON-OFFICIAL copy and exact date/licence UNVERIFIED |
| September 2019 Travis / TNRIS | {link('Public ArcGIS shapefile mirror; downloaded','https://www.arcgis.com/sharing/rest/content/items/4061b026210d40bfb25a559281cba008/data')} | `stratmap19-landparcels_48453_travis_201909.shp`; EPSG:3857; 353,920 polygons; 117,067,408 compressed bytes | Mirror metadata identifies September 2019 and TNRIS conversion; geometry source is TCAD |
| `TCAD Parcels Dec 2025`, maintained monthly | {link('Public hosted TCAD/TNR layer','https://services1.arcgis.com/HGcSYZ5bvjRswoCb/arcgis/rest/services/TCAD_Parcels_Dec_2025/FeatureServer/0')} | Native EPSG:2277; 386,682 polygon features, 373,524 unique property IDs; all 39 pages downloaded in EPSG:32614 | Last edit 2026-10-02; its name is not proof of a frozen December 2025 observation date; this is the diagnostic-count geometry |

The TxGIO anonymous collection/resource API lists the following. CRS below is **collection-level metadata**, not a verified `.prj` for inaccessible files. Tested **2019 and 2026 direct file URLs return generic CloudFront 403**; these were not worked around. The working 2019 ArcGIS mirror is a separate public source, not a bypass. No Travis resource is returned for the 2021–2023 collections despite Travis appearing in collection-level county lists. No 2016, 2017, 2018 or 2020 land-parcel collection was returned by the `Land Parcels` collection search.

| TxGIO collection | Travis filename / compressed bytes advertised | Catalog CRS | Verification |
|---|---|---|---|
''')
for g in geometry_inventory:
    if g['travis_resources']:
        r=g['travis_resources'][0]
        text=link(Path(urllib.parse.urlsplit(r['resource']).path).name,r['resource'])+' / '+n(r['filesize'])
        status='Catalog-listed; file retrieval UNVERIFIED (tested 2019/2026: 403)'
    else:text='No Travis resource returned';status='Not a verified Travis download'
    lines.append(f"| {g['collection_year']} | {text} | {g['catalog_crs']} | {status} |\n")
lines.append('''
The [TxGIO program page](https://geographic.texas.gov/stratmap/land-parcels) explains annual refreshes and that county acquisition months appear in filenames. Its free public statewide layer is a standardized subset of CAD data, not a replacement for the full improvement tables. No ground vintage was inferred from a portal upload date alone.

## 3. Inspected roll fields and fill rates

The inspected 2026 ZIP contains **493,324 property rows and 493,246 unique `prop_id` values**. Every row records tax year `02026` and supplement `000000000000` (certified supplement 0). There are 78 repeated property rows; all parcel counts deduplicate `prop_id`. The single-family denominator is **289,879 unique real-property parcels** (`prop_type_cd=R`, `imprv_state_cd=A1`).

Main dwelling: choose the largest summed living-floor area among improvement type **01 = 1 FAM DWELLING** and **16 = TOWNHOMES**, breaking an area tie by improvement ID. This retains A1's townhouses rather than broadening to condominiums or manufactured housing. Living-floor codes are `1/2`, `1ST`, `2ND`, `3RD`, `4TH`, `5TH`, `ADDL`. Year built is the minimum positive year on the selected main dwelling's `1ST` details; zero is missing. Foundation is read only from `Foundation` attributes linked to those main-dwelling `1ST` detail rows. Mixed foundation values are retained explicitly. Main types among all A1 parcels: **285,126 type 01**, **4,382 type 16**, **371 without a usable selected main dwelling**. This is a transparent diagnostic extraction rule for the coordinator to review before freeze.

| Required field | Exact source / positions, 1-based inclusive | Nonblank over all 289,879 A1 parcels | Additional validity information |
|---|---|---|---|
| Property ID | `PROP.TXT.prop_id`, 1–12 | 289,879 / 100% | Twelve-character zero-padded numeric text in this fixed-width export |
| Geographic ID | `PROP.TXT.geo_id`, 547–596 | 289,879 / 100% | Usually a 10-digit ID, preserving initial zeros |
| Deed date | `PROP.TXT.deed_dt`, 2034–2058 | 288,409 / 99.4929% | All nonblank values parse; 5 dates have year ≤1900 and need a historical-date rule before sale analysis |
| Single-family state code | `PROP.TXT.imprv_state_cd`, 2732–2741; `IMP_INFO.TXT.imprv_state_cd`, 64–68 | 289,879 / 100% by definition | A1 explicitly means SINGLE FAMILY RESIDENCE; broad PTD A includes other dwelling types |
| Main year built | `IMP_DET.TXT.yr_built`, 86–89, linked through `imprv_id` and `imprv_det_id` | 289,253 / 99.7840% have a nonblank raw first-floor year | 289,229 / 99.7758% have a positive usable year; zero is missing |
| Main living area | `IMP_DET.TXT.imprv_det_area`, 94–108, summed over the living-floor codes above | 289,508 / 99.8720% | 289,507 / 99.8717% positive; total improvement-detail area would wrongly include porches, HVAC and garages |
| Land acres | `LAND_DET.TXT.size_acres`, 70–83 | 289,763 / 99.9600% | Four implied decimal places; 289,526 / 99.8782% positive |
| Land square feet | `LAND_DET.TXT.size_square_feet`, 84–97 | 289,763 / 99.9600% | 289,526 / 99.8782% positive; polygon area is the plan's lot-area source |
| Main foundation | `IMP_ATR.TXT.imprv_attr_desc`, 53–77 = `Foundation`; `imprv_attr_cd`, 78–87 | 262,595 / 90.5878% | Restricted to selected main dwelling's first-floor details |

The main-improvement table is `IMP_INFO.TXT`; its `imprv_type_cd` occupies 29–38. Detail and attribute tables join on `(prop_id, prop_val_yr, imprv_id, imprv_det_id)`. The layout also permits the property `udi_group` link; five A1 parcels have nonzero UDI groups, but there were no additional attribute rows for those group IDs in the inspected data. No owner or mailing field was needed for analysis.

### All state codes, with unique-property counts

Counts below refer to `PROP.TXT.imprv_state_cd` after deduplicating property ID, not to land codes or owner rows. Zero-count codes are still present in `STATE_CD.TXT`. Blank improvement state code: **91,967**. Restricting to A1 selects houses; A2 identifies manufactured homes, A4 condominiums and A3/A5 detail-only records.

| CAD code | Exact CAD description | Unique properties |
|---|---|---:|
''')
for row in roll['state_dictionary']:
    code=row['state_cd']
    lines.append(f"| {code} | {row['state_cd_description']} | {n(roll['property_state_codes'].get(code,0))} |\n")
lines.append('''
### Every improvement-attribute type in A1 parcels

These are raw attribute-row counts and distinct parcel counts across **all improvements** belonging to A1 parcels. They are descriptive inventory counts; the main-dwelling restriction below is the relevant foundation check.

| `imprv_attr_desc` | Attribute rows | Distinct A1 properties |
|---|---:|---:|
''')
for row in roll['sf_attribute_types']:
    lines.append(f"| {row['description']} | {n(row['rows'])} | {n(row['distinct_properties'])} |\n")
lines.append('''
`Foundation` is the foundation type. Its exact category strings are truncated by the source's 10-character field; no guessed label expansion was applied.

| `imprv_attr_cd` | Foundation rows, all A1 improvements | Foundation rows, main dwelling first floor |
|---|---:|---:|
''')
raw_foundation={x['code']:x['rows'] for x in roll['sf_attribute_values'] if x['description']=='Foundation'}
for code,count in sorted(raw_foundation.items()):
    lines.append(f"| {code} | {n(count)} | {n(static['foundation_attribute_values_main_first_floor'].get(code,0))} |\n")
lines.append(f'''
Across all improvements, foundation attributes reach **263,462 / 289,879 = {pct(100*263462/289879)}** parcels. Restricting to the main dwelling gives **262,595 / 289,879 = 90.5878%**; among countywide main dwellings built by 2015 it is **224,378 / 235,113 = 95.4341%**. For the final Austin diagnostic population the rate is **{pct(foundation['nonblank_percent'])}**. Thus the **2026 diagnostic** clears the plan's ≥90% threshold. Coverage in an actual pre-2017 reference roll remains **UNVERIFIED**; this audit does not decide a historical baseline using a later roll.

| Main-dwelling foundation category, one row per eligible 2026 parcel | Parcels inside Austin full purpose |
|---|---:|
''')
for code,count in foundation['parcel_categories'].items():
    lines.append(f"| {code.replace('|',' + ') if code else '(missing)'} | {n(count)} |\n")
lines.append(f'''
**Earliest inspected qualifying roll:** none obtained. Its layout, fields, full state-code counts, attribute types and fill rates are **UNVERIFIED because a certified pre-2017 roll could not be retrieved**. The 2018 preliminary header is not passed off as that roll.

## 4. Permit identifier test — random 500, seed 2032

The anonymous permit download selects **only Socrata `:id` and `tcad_id`**, where `tcad_id is not null`, sorted by `:id`, with a limit of 3,000,000. After local whitespace-only blanks are excluded, the sampling frame has **2,319,386 permit rows**. It contains every permit type and work class and uses no keywords, permit outcome rules, date restrictions or residential filters. Draw **500 rows without replacement** using `numpy.random.default_rng(2032)` (PCG64); the sampled row IDs and parcel IDs remain private. The full frame is hashed, so live-table changes do not alter the recorded draw.

Against the **2026 roll**, **436/500 = 87.2%** match `geo_id` exactly after surrounding whitespace is stripped. The sample contains **483 ten-character digit-only IDs** and **17 seven-character nonnumeric entries**; no sampled ID has a dash. Of the 483 numeric ten-character IDs, **436/483 = 90.2692%** match; the specified headline denominator remains **500**, not 483.

`tcad_id` therefore corresponds to **TCAD geographic ID**, not internal property ID. Preserve the 10-digit geographic string and initial zeros; join to stripped `geo_id`. There are **0/500 exact `prop_id` matches** against the export's twelve-character padded property-ID strings. Removing numeric padding creates **5 incidental internal-ID coincidences**; those are not evidence that `prop_id` is an alternative mapping. Stripping geographic padding or applying `zfill(10)` does not improve the **436** geographic matches. No dashes needed removal in this draw. The remaining **64 IDs** were left unmatched; no outcomes were examined to explain them.

The identifier match rate against a qualifying pre-2017 roll is **UNVERIFIED**. It was not estimated from the 2016 geometry or the 2018 preliminary mirror.

## 5. Diagnostic population and 30 m grid — from 2026 roll

Final official boundary: Austin Technology Services (GIS), daily dataset **`vnwj-xmz9`**, rows updated **2026-10-27T23:33:00Z**. The query selects only `CITY OF AUSTIN` and `jurisdiction_type=FULL`; the downloaded GeoJSON contains **26 full-purpose polygons**, in EPSG:4326. It is transformed to **EPSG:32614** before the spatial check.

The TCAD/TNR parcel service has **386,682 polygon features and 373,524 unique property IDs**. All 39 pages were checked for expected row count and unique object IDs. **289,465 of 289,879 A1 parcels** have geometry; **414** do not, including **197** otherwise eligible by age. The geographic IDs agree for every matched A1 parcel. There are **7 repeated A1 property-geometry rows**; they are unioned by property before centroids are computed. **5** A1 polygon features are initially invalid; validity repair is recorded before union. Centroids are calculated on complete parcel polygons in EPSG:32614, then tested strictly inside the official full-purpose boundary; there are **0 centroids exactly on its boundary**.

| Count | From 2026 certified roll |
|---|---:|
| A1 parcels, all Travis County, all ages | 289,879 |
| A1 with usable main-dwelling year built ≤2015, countywide | 235,113 |
| Age-eligible A1 with a parcel polygon | 234,916 |
| All-age A1 centroids inside Austin full purpose | {n(population['a1_all_ages_inside_full_purpose'])} |
| **Age-eligible A1 centroids inside Austin full purpose** | **{n(city_n)}** |
| **Unique 30 m cells, EPSG:32614** | **{n(cells)}** |
| Strict main type 01 only, excluding A1 main townhouses | {n(population['strict_type01_inside_full_purpose'])} |
| Unique cells under that stricter type-01 definition | {n(population['strict_type01_unique_30m_cells'])} |

The grid index is **`(floor(x/30), floor(y/30))`**, where x/y are UTM easting/northing in metres. Cell edges lie at integer multiples of 30 m, with lower-inclusive / upper-exclusive membership. Count distinct index pairs, not rounded point coordinates. The A1 count includes **{n(population['a1_main_dwelling_type_counts_inside'].get('16',0))} main townhouses** (TCAD type 16), classified by TCAD as A1. The stricter type-01 alternative is disclosed for the coordinator's pre-freeze decision.

Year built, living area and polygon lot area are all present and positive for **100%** of this age-selected city population. Roll land acres/square feet are nonblank for **100%**, with **{n(population['eligible_2026_coverage']['size_square_feet']['positive'])}/{n(city_n)} = {pct(population['eligible_2026_coverage']['size_square_feet']['positive_percent'])}** positive; polygon area avoids those zero roll-lot values. Main foundation is nonblank for **{n(foundation['nonblank'])}/{n(city_n)} = {pct(foundation['nonblank_percent'])}**.

These are boundary-version-specific diagnostics. The older official `is88-7234` copy, updated 2025-06-02, would give **146,989 parcels / 112,195 cells**; an official hosted full-purpose layer updated 2026-05-06 gives **150,488 / 115,486**. Those are **superseded comparisons**, not the final count above. The newest official daily dataset was chosen and hashed. No satellite-frame clip was applied, because no OPERA/InSAR source was opened; any later frame-intersection requirement remains to be checked at its authorized stage.

**Pre-2017 reference population and cell count: UNVERIFIED**, because no qualifying certified roll was recovered. The 2026 estimate does not recover parcels rebuilt, reclassified, split, combined or removed since 2016.

## Routes to a 2016-or-earlier roll — user's action required

1. **TCAD direct GIS copy — user's action required.** The [FAQ](https://traviscad.org/faqs) offers a countywide GIS shapefile for **$4**, through the records department, delivered on CD or FTP. It does not state which historical vintages are supplied or whether improvement/deed tables accompany it. Before paying, the user should ask specifically for 2016-or-earlier geometry, its date/CRS, the join identifiers and any accompanying certified tables. A GIS copy alone may not supply year built, living area or foundation. The $4 figure is the published GIS-copy price, not a verified quote for historical certified rolls.

2. **Texas Public Information Act request to TCAD — user's action required.** [TCAD Public Information]({publicinfo}) directs requests to its [online records portal](https://traviscad.govqa.us/WEBAPP/_rs/SupportHome.aspx) or `recmgr@tcadcentral.org`. The user could request certified supplement-0 appraisal rolls **2016–2025**, and the earliest available pre-2016 roll, with `PROP`, `IMP_INFO`, `IMP_DET`, `IMP_ATR`, `LAND_DET`, state-code dictionaries, layouts and same-vintage polygon files. Ask for the original electronic exports, date/certification metadata, licence/terms and a fee estimate. The FAQ lists **$5** for predefined PDF roll copies and possible programming/manipulation charges for extra criteria; **no current quote for historical electronic rolls was verified**. The 2017 project’s $80/year statement is historical only. No request was submitted by this worker.

3. **TxGIO/TNRIS vintages — user's action required.** The direct file links and exact filenames/advertised sizes for **2019, 2024, 2025 and 2026** are in §2 and the manifest. The user may try them in a normal browser or contact TxGIO about the CloudFront errors and historical geometry availability. The collection API returned no Travis resource for **2021, 2022 or 2023**, and no 2016-or-earlier collection. TxGIO polygons are a route to geometry; they do not establish availability of a full historical appraisal roll. No gate was bypassed.

4. **2018 PRELIMINARY research mirror — user's action required before adoption.** The [TXHousing repository](https://github.com/amspector100/TXHousing) links a public [raw TCAD folder](https://drive.google.com/drive/folders/1kz4bZzOM5TBnK1hhPp0yaA45cvJdBGcy). Its README commit is dated **2018-08-20**. Only `APPR_HDR.TXT` and `travis_parcel_metadata.xlsx` were downloaded: the header records **2018**, run **2018-04-10 07:56**, description **EXPORT R&P ALLJUR AS OF 2018 PRELIM**, export version **8.0.0.20**. The folder lists `PROP.TXT`, `IMP_INFO.TXT`, `IMP_DET.TXT`, `IMP_ATR.TXT`, `LAND_DET.TXT`, `STATE_CD.TXT`, `UDI.TXT` and other tables. The project separately hosts a 2016 polygon shapefile. This is **NON-OFFICIAL**; original official download provenance, completeness, certification fidelity and **data licence are UNVERIFIED**. No licence file appeared in the repository tree. No property/improvement body was opened, no fill rate or 2026 overlap was inferred, and no header operator name is reproduced. The user/supervisor must decide whether a preliminary 2018 fallback is acceptable and obtain/clarify permission and provenance.

## Consequences for the plan

- **§4 — sale split:** `deed_dt` exists and is 99.4929% nonblank in 2026, but **secondary 14 is NOT RUN as written** with present evidence. One roll supplies the latest recorded transfer, not changes between consecutive 2016–2025 rolls. EARS downloads were not assumed to supply the missing history.
- **§5 — reference population:** the preferred certified pre-2017 reference roll is UNVERIFIED. Use the plan's stated fallback only after the supervisor chooses the earliest acceptable roll and records the limitation. A1 is the house state code; broad PTD A would incorrectly combine houses with manufactured homes, condos and detail-only records. The A1 townhouse/main-improvement extraction rule is disclosed above.
- **§9 — baseline:** the 2026 diagnostic main-foundation rate is **{pct(foundation['nonblank_percent'])}**, above 90%; year built, main living area and polygon lot area have 100% valid coverage in its age-selected city population. This does not establish the ≥90% rule for an unavailable historical reference roll. Foundation categories may be mixed, and some raw category labels are truncated.
- **GPU timing input:** use **{n(cells)} unique 30 m cells** for the explicitly labelled **2026 diagnostic**, with the daily full-purpose boundary updated 2026-10-27. The count for an actual pre-2017 reference population remains UNVERIFIED.

**Consequences if only the 2026 roll is used:** foundation type and living area may have been recorded or changed after a repair, and year built after a rebuild may likewise be post-event. A single `deed_dt` gives only the latest recorded transfer, so the consecutive-year sale split in §4 cannot be constructed as written. Parcels demolished and rebuilt after 2016 can drop out of the year-built ≤2015 filter. The later roll also cannot reconstruct former parcel identifiers or boundaries by itself.

## Evidence, hashes and reproducibility

Every anonymous download/probe, including failed responses and retries, is recorded in `tcad_manifest.json` with UTC access date, HTTP status, byte count, SHA-256 when a file was saved, and private path. **HEAD paths contain HTTP headers, not ZIP/Parquet bodies; their SHA-256 values hash those saved headers.** No SHA-256 is asserted for an undownloaded remote body. Transient signed redirect parameters were removed from the public manifest; canonical public source URLs remain.

''')
lines.append(evidence(full,'2026 certified full roll'))
lines.append(evidence(layout,'2026 PDF/XLSX layout package'))
lines.append(evidence(boundary,'Final official full-purpose boundary'))
lines.append(evidence(permit,'All-permit non-null-ID sampling frame'))
for part,label in [('/items/5b315f0617c84b42a4b2992af8796d81/data','Legacy parcel shapefile ZIP'),
                   ('/items/4061b026210d40bfb25a559281cba008/data','September 2019 parcel shapefile ZIP'),
                   ('export=download&id=1_RFxw6aoNNblsGRxlCQVLRDUMkeDuNTc','2018 preliminary export header'),
                   ('export=download&id=1YRrDHgCJBviFxPCe24wYSswKpudunpzf','2018 mirror layout workbook'),
                   ('export=download&id=1M-7ezCtoJvBJGbysSx_9C5w1j0W1okWM','Original 2016 shapefile CRS file'),
                   ('Parcels_Travis_2016_f_ao/FeatureServer/0/query?where=1%3D1&outFields=','2016 public geometry ten-polygon sample')]:
    lines.append(evidence(source(part),label))
lines.append(f'''
The 39 diagnostic polygon response files have individual hashes in the manifest; total successful geometry-body bytes are counted there. The aggregate JSON `tcad_availability.json` preserves the tables, counts, definitions, source records and UNVERIFIED flags in machine-readable form.

**Total downloaded GET response bodies: {n(body_bytes)} bytes.** Saved HEAD response headers: **{n(header_bytes)} bytes**; total saved download evidence **{n(body_bytes+header_bytes)} bytes**, below the **20,000,000,000-byte** cap. This includes failed-response bodies, duplicate/retried downloads and metadata. Uncompressed tables were streamed; the roll's **17,989,848,588 uncompressed bytes** were not unpacked wholesale.

Scripts under `feasibility/austin/step0/scripts/` take data paths as arguments and run with `/mnt/data/Master-projects/Alex/.venv/bin/python -I`. `inspect_roll.py` reads allowlisted fields only; `static_checks.py` builds dwelling coverage; `id_match_check.py` performs the sole permitted 500-row ID check; `population_checks.py` verifies all polygon pages and original boundary diagnostics; `final_boundary_counts.py` applies the newer official boundary; this builder writes the public aggregate deliverables. All row-level outputs stay private. No existing plan, readiness file or other worker's literature file was changed.

Final verification: **147 saved response/header files** match their manifest SHA-256 values and byte sizes. Parcel uniqueness, age eligibility, EPSG:32614 grid indices, distinct-cell count, foundation counts, all 45 state-code definitions and the 500-row ID-test totals pass aggregate checks. A recursive grep for owner-name, mailing-address, contractor-name and applicant-name field patterns returned **no matches** in `feasibility/austin/step0/`.
''')
(a.outdir/'TCAD_AVAILABILITY.md').write_text(''.join(lines))
print(json.dumps({'report':str(a.outdir/'TCAD_AVAILABILITY.md'),'bytes_downloaded':body_bytes+header_bytes,
                  'parcels':city_n,'cells':cells,'foundation_coverage_percent':foundation['nonblank_percent']}))
