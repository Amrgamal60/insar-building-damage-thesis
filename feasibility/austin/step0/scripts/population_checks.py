"""Diagnostic population/cell counts from a roll and public parcel polygons.

No permit data is accepted. Centroids are computed on EPSG:32614 polygons.
"""
import argparse
import hashlib
import json
from pathlib import Path
import urllib.parse
import geopandas as gpd
import numpy as np
import pandas as pd
import shapely
from shapely.geometry import shape

p=argparse.ArgumentParser()
p.add_argument('--manifest',type=Path,required=True)
p.add_argument('--parcel-fields',type=Path,required=True)
p.add_argument('--boundary',type=Path,required=True)
p.add_argument('--output',type=Path,required=True)
a=p.parse_args()
a.output.mkdir(parents=True,exist_ok=False)
manifest=json.loads(a.manifest.read_text())
prefix='https://services1.arcgis.com/HGcSYZ5bvjRswoCb/arcgis/rest/services/TCAD_Parcels_Dec_2025/FeatureServer/0/query?'
pages={}
for entry in manifest:
    if entry['url'].startswith(prefix) and entry.get('http_status')==200 and not entry.get('error') and entry.get('local_path'):
        params=urllib.parse.parse_qs(urllib.parse.urlsplit(entry['url']).query)
        if params.get('outFields')==['OBJECTID,PROP_ID,geo_id'] and params.get('resultRecordCount')==['10000']:
            path=Path(entry['local_path'])
            try:
                j=json.loads(path.read_text())
            except json.JSONDecodeError:
                continue
            if 'features' in j:
                assert j.get('crs',{}).get('properties',{}).get('name')=='EPSG:32614'
                pages[int(params['resultOffset'][0])]=(path,j)
expected=set(range(0,386682,10000))
assert set(pages)==expected, f'Missing pages: {sorted(expected-set(pages))}'
records=[]
for offset,(path,j) in sorted(pages.items()):
    for f in j['features']:
        props=f['properties']
        records.append((props['OBJECTID'],props['PROP_ID'],props['geo_id'],shape(f['geometry']) if f['geometry'] else None))
    print(json.dumps({'offset':offset,'features':len(j['features'])}),flush=True)
frame=gpd.GeoDataFrame(records,columns=['object_id','prop_id_numeric','geo_id','geometry'],crs=32614)
assert len(frame)==386682 and frame.object_id.nunique()==386682
frame['prop_id']=frame.prop_id_numeric.astype('Int64').astype(str).str.zfill(12)
sf=pd.read_parquet(a.parcel_fields)
matched=frame.merge(sf,on='prop_id',how='inner',suffixes=('_polygon','_roll'),validate='many_to_one')
invalid_before=int((~matched.geometry.is_valid).sum())
missing=int(matched.geometry.isna().sum())
matched=matched[matched.geometry.notna()&~matched.geometry.is_empty].copy()
duplicate_property_geometry_rows=int(matched.prop_id.duplicated().sum())
if duplicate_property_geometry_rows:
    matched.geometry=shapely.make_valid(matched.geometry.to_numpy())
    matched=matched.dissolve(by='prop_id',as_index=False,aggfunc='first')
matched['point']=matched.geometry.centroid
matched['polygon_area_m2']=matched.geometry.area
boundary=gpd.read_file(a.boundary).to_crs(32614)
assert set(boundary.jurisdiction_type)=={'FULL'}
assert set(boundary.city_name)=={'CITY OF AUSTIN'}
city=shapely.union_all(boundary.geometry.to_numpy())
if not shapely.is_valid(city):
    city=shapely.make_valid(city)
matched['inside_full_purpose']=shapely.within(matched['point'].to_numpy(),city)
matched['on_full_purpose_boundary']=shapely.touches(matched['point'].to_numpy(),city)
matched['age_eligible']=matched.year_built.between(1,2015)
eligible=matched[matched.inside_full_purpose&matched.age_eligible].copy()
eligible['cell_x']=np.floor(eligible['point'].map(lambda p:p.x).to_numpy()/30).astype('int64')
eligible['cell_y']=np.floor(eligible['point'].map(lambda p:p.y).to_numpy()/30).astype('int64')
matched.drop(columns=['point']).to_parquet(a.output/'a1_parcel_polygons.parquet',index=False)
eligible.drop(columns=['point']).to_parquet(a.output/'eligible_2026_diagnostic.parquet',index=False)

def coverage(frame):
    n=len(frame)
    cols={}
    for col in ['year_built','living_area','size_acres','size_square_feet','polygon_area_m2']:
        cols[col]={'nonblank':int(frame[col].notna().sum()),'positive':int(frame[col].gt(0).sum()),
                   'denominator':n,'nonblank_percent':100*frame[col].notna().mean(),
                   'positive_percent':100*frame[col].gt(0).mean()}
    cols['main_dwelling_foundation']={'nonblank':int(frame.foundation.ne('').sum()),'denominator':n,
        'nonblank_percent':100*frame.foundation.ne('').mean(),
        'parcel_categories':frame.foundation.value_counts(dropna=False).to_dict()}
    return cols

summary={'label':'DIAGNOSTIC FROM 2026 CERTIFIED ROLL; not a pre-2017 reference population',
    'roll_year':2026,'polygon_layer_name':'TCAD Parcels Dec 2025',
    'polygon_last_edit_date_utc':'2026-10-02','polygon_vintage_caveat':'layer named Dec 2025 is maintained monthly and last edited 2026-10-02; exact geometry observation date unverified',
    'polygon_download_pages':len(pages),'polygon_features':len(frame),'polygon_unique_property_ids':frame.prop_id.nunique(),
    'a1_roll_unique_parcels':len(sf),'a1_parcels_matching_polygon':matched.prop_id.nunique(),
    'a1_parcels_without_polygon':int((~sf.prop_id.isin(matched.prop_id)).sum()),
    'a1_geo_id_disagree_with_geometry':int(matched.geo_id_polygon.fillna('').ne(matched.geo_id_roll.fillna('')).sum()),
    'invalid_a1_polygon_features_before_repair':invalid_before,'missing_geometry_a1_features':missing,
    'duplicate_property_geometry_rows_dissolved':duplicate_property_geometry_rows,
    'a1_all_ages_inside_full_purpose':int(matched.inside_full_purpose.sum()),
    'a1_centroids_on_city_boundary':int(matched.on_full_purpose_boundary.sum()),
    'a1_built_2015_or_earlier_countywide':int(sf.year_built.between(1,2015).sum()),
    'a1_built_2015_or_earlier_with_polygon':int(matched.age_eligible.sum()),
    'a1_built_2015_or_earlier_inside_full_purpose':len(eligible),
    'unique_30m_cells_epsg32614':len(eligible[['cell_x','cell_y']].drop_duplicates()),
    'cell_rule':'(floor(centroid_easting/30), floor(centroid_northing/30)); lower-inclusive and upper-exclusive edges at integer multiples of 30 metres',
    'strict_type01_inside_full_purpose':int(eligible.imprv_type_cd.eq('01').sum()),
    'strict_type01_unique_30m_cells':len(eligible.loc[eligible.imprv_type_cd.eq('01'),['cell_x','cell_y']].drop_duplicates()),
    'a1_main_dwelling_type_counts_inside':eligible.imprv_type_cd.value_counts().to_dict(),
    'eligible_2026_coverage':coverage(eligible),
    'a1_inside_all_ages_coverage':coverage(matched[matched.inside_full_purpose]),
    'boundary_path':str(a.boundary),'boundary_sha256':hashlib.sha256(a.boundary.read_bytes()).hexdigest(),
    'boundary_feature_count':len(boundary),'boundary_geometry_crs':'EPSG:4326 reprojected to EPSG:32614',
    'boundary_filter':'jurisdiction_type=FULL; CITY OF AUSTIN only',
    'frame_clip':'not applied; no OPERA/InSAR data or metadata opened in this task'}
(a.output/'population_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))
