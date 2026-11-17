"""Inspect only allowlisted non-personal fields from a TCAD ZIP, never execute it.

All row-level outputs, including IDs, must be in the private directory passed in.
"""
import argparse
import collections
import io
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import zipfile
import pandas as pd

p=argparse.ArgumentParser()
p.add_argument('--roll',type=Path,required=True)
p.add_argument('--layout',type=Path,required=True)
p.add_argument('--output',type=Path,required=True)
a=p.parse_args()
a.output.mkdir(parents=True,exist_ok=False)
ns={'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
with zipfile.ZipFile(a.layout) as outer:
    x=zipfile.ZipFile(io.BytesIO(outer.read(next(n for n in outer.namelist() if n.endswith('.xlsx')))))
    strings=[''.join(t.itertext()) for t in ET.fromstring(x.read('xl/sharedStrings.xml')).findall('m:si',ns)]
    sheets=ET.fromstring(x.read('xl/workbook.xml')).findall('m:sheets/m:sheet',ns)
    layouts={}
    for i,sheet in enumerate(sheets,1):
        rows=[]
        for row in ET.fromstring(x.read(f'xl/worksheets/sheet{i}.xml')).findall('m:sheetData/m:row',ns):
            cells={}
            for cell in row.findall('m:c',ns):
                value=cell.find('m:v',ns)
                if value is not None:
                    cells[re.sub(r'\d','',cell.attrib['r'])]=strings[int(value.text)] if cell.get('t')=='s' else value.text
            if all(k in cells for k in ['A','C','D']) and str(cells['C']).isdigit() and str(cells['D']).isdigit():
                rows.append({'field':cells['A'],'start':int(cells['C']),'end':int(cells['D']),
                             'description':cells.get('F','')})
        layouts[sheet.attrib['name']]=rows
(a.output/'layouts.json').write_text(json.dumps(layouts,indent=2)+'\n')

def read_allowed(z,filename,sheet,fields,allowed=None):
    specs={r['field']:(r['start']-1,r['end']) for r in layouts[sheet]}
    spans=[specs[f] for f in fields]
    result=[]
    rows=0
    with z.open(filename) as source:
        for line in source:
            rows+=1
            pid=line[:12].strip().decode('ascii')
            if allowed is None or pid in allowed:
                result.append(tuple(line[start:end].strip().decode('cp1252',errors='replace') for start,end in spans))
    table=pd.DataFrame.from_records(result,columns=fields)
    table.to_parquet(a.output/(filename+'.parquet'),index=False)
    print(json.dumps({'file':filename,'source_rows':rows,'retained_rows':len(table)}),flush=True)
    return table,rows

summary={'roll_path':str(a.roll),'layout_path':str(a.layout)}
with zipfile.ZipFile(a.roll) as z:
    prop,n=read_allowed(z,'PROP.TXT','Property',[
        'prop_id','prop_type_cd','prop_val_yr','sup_num','geo_id','udi_group',
        'deed_dt','imprv_state_cd','land_state_cd'])
    summary['property_rows']=n
    summary['unique_property_ids']=prop.prop_id.nunique()
    summary['property_duplicate_rows']=int(prop.prop_id.duplicated().sum())
    summary['year_counts']=prop.prop_val_yr.value_counts(dropna=False).to_dict()
    summary['supplement_counts']=prop.sup_num.value_counts(dropna=False).to_dict()
    summary['property_state_codes']=prop.drop_duplicates('prop_id').imprv_state_cd.value_counts(dropna=False).to_dict()
    sf=prop[(prop.imprv_state_cd=='A1')&(prop.prop_type_cd=='R')].drop_duplicates('prop_id')
    summary['single_family_real_A1']=len(sf)
    summary['single_family_field_fill']={f:{'nonblank':int(sf[f].ne('').sum()),'denominator':len(sf),
        'percent':float(100*sf[f].ne('').mean())} for f in ['prop_id','geo_id','deed_dt','imprv_state_cd']}
    sf_ids=set(sf.prop_id)
    udi=set(sf.udi_group)-{'','0'}
    allowed=sf_ids|udi
    summary['sf_nonzero_udi_groups']=len(udi)
    state,_=read_allowed(z,'STATE_CD.TXT','StateCode',[r['field'] for r in layouts['StateCode']])
    summary['state_dictionary']=state.to_dict('records')
    info,_=read_allowed(z,'IMP_INFO.TXT','Improvement',[
        'prop_id','prop_val_yr','imprv_id','imprv_type_cd','imprv_type_desc','imprv_state_cd','imprv_val'],allowed)
    summary['sf_improvement_type_counts']=info.groupby(['imprv_type_cd','imprv_type_desc']).size().to_dict()
    summary['sf_improvement_type_counts']=[{'code':k[0],'description':k[1],'count':int(v)} for k,v in summary['sf_improvement_type_counts'].items()]
    det,_=read_allowed(z,'IMP_DET.TXT','ImprovementDetail',[
        'prop_id','prop_val_yr','imprv_id','imprv_det_id','Imprv_det_type_cd',
        'Imprv_det_type_desc','Imprv_det_class_cd','yr_built','imprv_det_area','imprv_det_val'],allowed)
    summary['sf_detail_type_counts']=[{'code':k[0],'description':k[1],'count':int(v)} for k,v in
        det.groupby(['Imprv_det_type_cd','Imprv_det_type_desc']).size().items()]
    attr,_=read_allowed(z,'IMP_ATR.TXT','ImprovementDetailAttributes',[
        'prop_id','prop_val_yr','imprv_id','imprv_det_id','imprv_attr_id','imprv_attr_desc','imprv_attr_cd'],allowed)
    summary['sf_attribute_types']=[{'description':k,'rows':int(v),'distinct_properties':int(attr.loc[attr.imprv_attr_desc.eq(k),'prop_id'].nunique())}
                                  for k,v in attr.imprv_attr_desc.value_counts(dropna=False).items()]
    summary['sf_attribute_values']=[{'description':k[0],'code':k[1],'rows':int(v)} for k,v in
                                   attr.groupby(['imprv_attr_desc','imprv_attr_cd']).size().items()]
    land,_=read_allowed(z,'LAND_DET.TXT','LandDetail',[
        'prop_id','prop_val_yr','land_seg_id','land_type_cd','land_type_desc','state_cd','size_acres','size_square_feet'],allowed)
    for col in ['size_acres','size_square_feet']:
        got=set(land.loc[land[col].ne(''),'prop_id'])
        summary['single_family_field_fill'][col]={'nonblank':len(sf_ids&got),'denominator':len(sf_ids),
                                                'percent':100*len(sf_ids&got)/len(sf_ids)}
(a.output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps({k:v for k,v in summary.items() if k not in ['sf_attribute_values','state_dictionary','sf_detail_type_counts']},indent=2))
