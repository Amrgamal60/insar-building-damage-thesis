"""Apply a newer official boundary to the already validated parcel polygons."""
import argparse
import hashlib
import json
from pathlib import Path
import geopandas as gpd
import numpy as np
import shapely

p=argparse.ArgumentParser()
p.add_argument('--polygons',type=Path,required=True)
p.add_argument('--prior-summary',type=Path,required=True)
p.add_argument('--boundary',type=Path,required=True)
p.add_argument('--output',type=Path,required=True)
a=p.parse_args()
a.output.mkdir(parents=True,exist_ok=False)
frame=gpd.read_parquet(a.polygons)
boundary=gpd.read_file(a.boundary).to_crs(32614)
assert set(boundary.city_name)=={'CITY OF AUSTIN'} and set(boundary.jurisdiction_type)=={'FULL'}
city=shapely.union_all(boundary.geometry.to_numpy())
if not shapely.is_valid(city):city=shapely.make_valid(city)
shapely.prepare(city)
points=frame.geometry.centroid
frame['inside_full_purpose']=shapely.contains(city,points.to_numpy())
frame['on_full_purpose_boundary']=shapely.touches(points.to_numpy(),city)
eligible=frame[frame.inside_full_purpose&frame.year_built.between(1,2015)].copy()
centroids=eligible.geometry.centroid
eligible['cell_x']=np.floor(centroids.x/30).astype('int64')
eligible['cell_y']=np.floor(centroids.y/30).astype('int64')
eligible.to_parquet(a.output/'eligible_2026_diagnostic.parquet',index=False)

def coverage(df):
    result={}
    for col in ['year_built','living_area','size_acres','size_square_feet','polygon_area_m2']:
        result[col]={'nonblank':int(df[col].notna().sum()),'positive':int(df[col].gt(0).sum()),
                     'denominator':len(df),'nonblank_percent':100*df[col].notna().mean(),
                     'positive_percent':100*df[col].gt(0).mean()}
    result['main_dwelling_foundation']={'nonblank':int(df.foundation.ne('').sum()),'denominator':len(df),
        'nonblank_percent':100*df.foundation.ne('').mean(),'parcel_categories':df.foundation.value_counts(dropna=False).to_dict()}
    return result

summary=json.loads(a.prior_summary.read_text())
summary.update(a1_all_ages_inside_full_purpose=int(frame.inside_full_purpose.sum()),
    a1_centroids_on_city_boundary=int(frame.on_full_purpose_boundary.sum()),
    a1_built_2015_or_earlier_inside_full_purpose=len(eligible),
    unique_30m_cells_epsg32614=len(eligible[['cell_x','cell_y']].drop_duplicates()),
    strict_type01_inside_full_purpose=int(eligible.imprv_type_cd.eq('01').sum()),
    strict_type01_unique_30m_cells=len(eligible.loc[eligible.imprv_type_cd.eq('01'),['cell_x','cell_y']].drop_duplicates()),
    a1_main_dwelling_type_counts_inside=eligible.imprv_type_cd.value_counts().to_dict(),
    eligible_2026_coverage=coverage(eligible),a1_inside_all_ages_coverage=coverage(frame[frame.inside_full_purpose]),
    boundary_path=str(a.boundary),boundary_sha256=hashlib.sha256(a.boundary.read_bytes()).hexdigest(),
    boundary_feature_count=len(boundary),boundary_area_km2=city.area/1e6,
    boundary_dataset='vnwj-xmz9',boundary_rows_updated_utc='2026-10-27T23:33:00Z',
    boundary_vintage_comparison={'is88_7234_updated_2025_06_02':{
        'parcels':146989,'cells':112195,'status':'superseded diagnostic'},
        'official_hosted_full_purpose_updated_2026_05_06':{
        'parcels':150488,'cells':115486,'status':'comparison only'}})
(a.output/'population_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps({k:summary[k] for k in ['a1_built_2015_or_earlier_inside_full_purpose','unique_30m_cells_epsg32614',
    'strict_type01_inside_full_purpose','strict_type01_unique_30m_cells','boundary_sha256','eligible_2026_coverage']},indent=2))
