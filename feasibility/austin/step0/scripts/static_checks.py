"""Outcome-blind 2026 roll field checks. Row-level output remains private."""
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd

p=argparse.ArgumentParser()
p.add_argument('--derived',type=Path,required=True)
p.add_argument('--output',type=Path,required=True)
a=p.parse_args()
a.output.mkdir(parents=True,exist_ok=False)
prop=pd.read_parquet(a.derived/'PROP.TXT.parquet')
sf=prop[(prop.imprv_state_cd=='A1')&(prop.prop_type_cd=='R')].drop_duplicates('prop_id').copy()
info=pd.read_parquet(a.derived/'IMP_INFO.TXT.parquet')
det=pd.read_parquet(a.derived/'IMP_DET.TXT.parquet')
attr=pd.read_parquet(a.derived/'IMP_ATR.TXT.parquet')
land=pd.read_parquet(a.derived/'LAND_DET.TXT.parquet')
for col in ['yr_built','imprv_det_area','imprv_det_val']:
    det[col+'_number']=pd.to_numeric(det[col],errors='coerce')
floors=det[det.Imprv_det_type_cd.isin(['1/2','1ST','2ND','3RD','4TH','5TH','ADDL'])]
groups=floors.groupby(['prop_id','imprv_id'],as_index=False).agg(
    living_area=('imprv_det_area_number','sum'),floor_rows=('prop_id','size'))
first=floors[floors.Imprv_det_type_cd.eq('1ST')].copy()
first['valid_year']=first.yr_built_number.where(first.yr_built_number.between(1,2026))
years=first.groupby(['prop_id','imprv_id'],as_index=False).agg(year_built=('valid_year','min'))
groups=groups.merge(years,on=['prop_id','imprv_id'],how='left',validate='one_to_one')
groups=groups.merge(info[['prop_id','imprv_id','imprv_type_cd','imprv_state_cd']],
                    on=['prop_id','imprv_id'],how='left',validate='one_to_one')
main=groups[groups.imprv_type_cd.isin(['01','16'])].sort_values(
    ['prop_id','living_area','imprv_id'],ascending=[True,False,True]).drop_duplicates('prop_id')
mainkeys=main[['prop_id','imprv_id']]
first_main=first.merge(mainkeys,on=['prop_id','imprv_id'],how='inner',validate='many_to_one')
foundation=attr[(attr.imprv_attr_desc=='Foundation')&attr.imprv_attr_cd.ne('')].merge(
    first_main[['prop_id','imprv_id','imprv_det_id']],
    on=['prop_id','imprv_id','imprv_det_id'],how='inner',validate='many_to_one')
foundation_values=foundation.groupby('prop_id').imprv_attr_cd.agg(lambda s:' | '.join(sorted(set(s))))
sf=sf.merge(main[['prop_id','imprv_id','imprv_type_cd','year_built','living_area']],on='prop_id',how='left',validate='one_to_one')
sf['foundation']=sf.prop_id.map(foundation_values).fillna('')
for col in ['size_acres','size_square_feet']:
    land[col+'_number']=pd.to_numeric(land[col],errors='coerce')
    grouped=land.groupby('prop_id')[col+'_number'].sum(min_count=1)
    sf[col]=sf.prop_id.map(grouped)
sf.to_parquet(a.output/'parcel_fields.parquet',index=False)

def coverage(frame):
    n=len(frame)
    fields={}
    for col in ['year_built','living_area','size_acres','size_square_feet']:
        fields[col]={'nonblank':int(frame[col].notna().sum()),'positive':int(frame[col].gt(0).sum()),
                     'denominator':n,'nonblank_percent':100*frame[col].notna().mean(),
                     'positive_percent':100*frame[col].gt(0).mean()}
    fields['main_dwelling_foundation']={'nonblank':int(frame.foundation.ne('').sum()),'denominator':n,
        'nonblank_percent':100*frame.foundation.ne('').mean(),
        'parcel_categories':frame.foundation.value_counts(dropna=False).to_dict()}
    return fields

summary={'definition':{'single_family':'unique PROP.TXT prop_id with prop_type_cd R and imprv_state_cd A1',
    'main_dwelling':'largest summed living-floor area among IMP_INFO types 01 (1 FAM DWELLING) and 16 (TOWNHOMES), tie by imprv_id',
    'living_area':'sum IMP_DET area on codes 1/2,1ST,2ND,3RD,4TH,5TH,ADDL for the selected improvement',
    'year_built':'minimum positive yr_built among 1ST detail rows of selected main dwelling; zero is missing',
    'foundation':'Foundation attribute linked to 1ST detail rows of selected main dwelling; multiple codes retained as a mixed category',
    'land_area':'sum LAND_DET sizes by prop_id; size_acres uses four implied decimal places; all values used only for coverage',
    'geometry':'not used in this stage'},
    'a1_unique_parcels':len(sf),'main_dwelling_type_counts':sf.imprv_type_cd.fillna('MISSING').value_counts().to_dict(),
    'a1_coverage':coverage(sf),'age_eligible_parcels_countywide':int(sf.year_built.between(1,2015).sum()),
    'age_eligible_coverage_countywide':coverage(sf[sf.year_built.between(1,2015)]),
    'foundation_attribute_rows_main_first_floor':len(foundation),
    'foundation_attribute_values_main_first_floor':foundation.imprv_attr_cd.value_counts().to_dict(),
    'strict_type01_age_eligible_countywide':int((sf.year_built.between(1,2015)&sf.imprv_type_cd.eq('01')).sum())}
raw_year=int(first_main.loc[first_main.yr_built.ne(''),'prop_id'].nunique())
summary['raw_main_first_floor_year_nonblank']={'nonblank':raw_year,'denominator':len(sf),'nonblank_percent':100*raw_year/len(sf)}
dates=pd.to_datetime(sf.deed_dt,format='mixed',errors='coerce')
summary['deed_date_parseable']={'count':int(dates.notna().sum()),'percent':100*dates.notna().mean(),
                                'year_at_or_before_1900':int(dates.dt.year.le(1900).sum())}
(a.output/'static_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))
