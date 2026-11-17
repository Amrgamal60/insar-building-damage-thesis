"""Only authorized permit-roll join: uniform 500 permits from ALL nonblank IDs."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd

p=argparse.ArgumentParser()
p.add_argument('--permits',type=Path,required=True)
p.add_argument('--roll-properties',type=Path,required=True)
p.add_argument('--summary',type=Path,required=True)
p.add_argument('--sample',type=Path,required=True)
a=p.parse_args()
d=pd.read_csv(a.permits,dtype=str,keep_default_na=False)
d=d[d.tcad_id.str.strip().ne('')].reset_index(drop=True)
s=d.iloc[np.random.default_rng(2032).choice(len(d),500,replace=False)].copy()
prop=pd.read_parquet(a.roll_properties)
v=s.tcad_id.str.strip()
geo=prop.geo_id.str.strip()
pid=prop.prop_id.str.strip()
def numeric(series):
    return series.str.replace(r'[^0-9]','',regex=True).str.lstrip('0').replace('','0')
result={'seed':2032,'generator':'numpy.random.default_rng PCG64',
    'sampling_frame':'all records with a nonblank tcad_id; ordered by Socrata :id',
    'nonblank_permit_rows':len(d),'sample_size':len(s),
    'snapshot_sha256':hashlib.sha256(a.permits.read_bytes()).hexdigest(),
    'sample_tcad_id_length_counts':v.str.len().value_counts().to_dict(),
    'sample_digits_only_count':int(v.str.fullmatch(r'[0-9]+').sum()),
    'sample_dash_count':int(v.str.contains('-',regex=False).sum()),
    'sample_prop_id_exact':int(v.isin(set(pid)).sum()),
    'sample_geo_id_exact':int(v.isin(set(geo)).sum()),
    'sample_prop_id_numeric':int(numeric(v).isin(set(numeric(pid))).sum()),
    'sample_geo_id_numeric':int(numeric(v).isin(set(numeric(geo))).sum()),
    'sample_geo_id_zfill10':int(v.str.zfill(10).isin(set(geo)).sum()),
    'roll_prop_id_length_counts':pid.str.len().value_counts().to_dict(),
    'roll_geo_id_length_counts':geo.str.len().value_counts().to_dict(),
    'warning':'Numeric prop_id coincidences are not valid alternative identifier mappings.'}
a.summary.write_text(json.dumps(result,indent=2)+'\n')
s.to_csv(a.sample,index=False)
print(json.dumps({k:result[k] for k in ['sample_size','sample_geo_id_exact','nonblank_permit_rows']}))
