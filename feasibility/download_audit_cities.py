#!/usr/bin/env python3
"""Download city source files and audit actual bytes. Never marks metadata as data.
Run with the project .venv. Network failures are logged and return nonzero.
"""
import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import zipfile
import requests

ROOT = Path(__file__).resolve().parent

def digest(path, algorithm='sha256'):
    h = hashlib.new(algorithm)
    with path.open('rb') as f:
        for block in iter(lambda: f.read(8 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

def save_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, default=str, allow_nan=False) + '\n')

def download(url, path, size=None, md5=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        valid = (size is not None and path.stat().st_size == size)
        if valid and (not md5 or digest(path, 'md5') == md5):
            return {'status': 'verified_existing', 'bytes': path.stat().st_size}
        raise ValueError(f'Unverified existing file retained without overwrite: {path}')
    partial = path.with_name(path.name + '.part')
    try:
        with requests.get(url, stream=True, timeout=(15, 90)) as response:
            response.raise_for_status()
            content_type = response.headers.get('Content-Type', '')
            with partial.open('wb') as f:
                for block in response.iter_content(1024 * 1024):
                    if block:
                        f.write(block)
        n = partial.stat().st_size
        if size is not None and n != size:
            raise ValueError(f'Expected {size} bytes, got {n}')
        with partial.open('rb') as f:
            magic = f.read(512).lstrip()
        if path.suffix.lower() == '.pdf' and not magic.startswith(b'%PDF-'):
            raise ValueError('Response is not a PDF')
        if path.suffix.lower() in {'.zip', '.xlsx'}:
            if not zipfile.is_zipfile(partial):
                raise ValueError('Response is not a ZIP container')
            with zipfile.ZipFile(partial) as archive:
                bad = archive.testzip()
                if bad:
                    raise ValueError(f'ZIP CRC failure: {bad}')
        if path.suffix.lower() in {'.tif', '.tiff'} and magic[:4] not in (b'II*\x00', b'MM\x00*', b'II+\x00', b'MM\x00+'):
            raise ValueError('Response is not TIFF')
        if path.suffix.lower() in {'.csv', '.gz'} and (b'<html' in magic.lower() or b'<!doctype html' in magic.lower()):
            raise ValueError('HTML response masquerading as data')
        if md5 and digest(partial, 'md5') != md5:
            raise ValueError('Publisher MD5 mismatch')
        sha = digest(partial)
        partial.rename(path)
        return {'status': 'downloaded', 'bytes': n, 'sha256': sha, 'content_type': content_type}
    except Exception:
        partial.unlink(missing_ok=True)
        raise

def attempt(log, city, dataset, url, path, **kwargs):
    item = dict(city=city, dataset=dataset, url=url, path=str(path.relative_to(ROOT)), attempted_utc=datetime.now(timezone.utc).isoformat())
    try:
        item.update(download(url, path, **kwargs))
    except Exception as e:
        item.update(status='failed', error=str(e))
    log.append(item)
    print(f'{city}: {dataset}: {item["status"]}', flush=True)

def figshare(log, city, article_id, version=None):
    url = f'https://api.figshare.com/v2/articles/{article_id}' + (f'/versions/{version}' if version else '')
    try:
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        metadata = r.json()
        save_json(ROOT / city / 'metadata/figshare_article.json', metadata)
        files = metadata['files']
        if not files:
            raise ValueError('No files advertised by publisher')
        selected = [f for f in files if city == 'lagos' or 'mumbai' in f['name'].lower() or 'collapse' in f['name'].lower() or 'readme' in f['name'].lower()]
        if not selected:
            raise ValueError('No Mumbai/incident/README files found; inspect inventory')
        for f in selected:
            name = f['name']
            if Path(name).name != name:
                raise ValueError('Unsafe publisher filename')
            attempt(log, city, 'figshare', f['download_url'], ROOT / city / 'downloads/figshare' / name, size=f.get('size'), md5=f.get('computed_md5'))
        save_json(ROOT / city / 'audit/figshare_completeness.json', {
            'article_id': article_id, 'version': metadata.get('version'), 'advertised_files': len(files),
            'selected_files': len(selected), 'scope': 'all advertised files' if city == 'lagos' else 'Mumbai files plus collapse catalog and README',
            'complete': all(any(x['path'].endswith('/'+f['name']) and x['status'] in ('downloaded','verified_existing') for x in log) for f in selected)})
    except Exception as e:
        log.append(dict(city=city, dataset='figshare_inventory', url=url, status='failed', error=str(e)))
        print(f'{city}: Figshare inventory failed: {type(e).__name__}', flush=True)

def audit_table(frame):
    import numpy as np
    result = {'rows': len(frame), 'columns': [str(c) for c in frame.columns],
              'null_counts': {str(k): int(v) for k,v in frame.isna().sum().items()},
              'empty_or_whitespace_counts': {}, 'nonfinite_numeric_counts': {},
              'duplicate_full_rows': int(frame.duplicated().sum())}
    for c in frame.columns:
        s = frame[c]
        if s.dtype.kind in 'biufc':
            result['nonfinite_numeric_counts'][str(c)] = int((~np.isfinite(s.to_numpy(dtype=float))).sum())
        else:
            result['empty_or_whitespace_counts'][str(c)] = int(s.fillna('').astype(str).str.strip().eq('').sum())
    result['note'] = 'Default pandas NA recognition; undocumented numeric sentinel codes are not inferred. Spreadsheet rows include headers/notes unless cleaned separately.'
    return result

def inspect_file(path):
    result = {'path': str(path.relative_to(ROOT)), 'size_bytes': path.stat().st_size, 'sha256': digest(path)}
    try:
        suffix = path.suffix.lower()
        if suffix in ('.tif', '.tiff'):
            import numpy as np
            import rasterio
            with rasterio.open(path) as src:
                result.update(format='GeoTIFF', width=src.width, height=src.height, bands=src.count,
                              crs=str(src.crs), resolution=list(src.res), bounds=list(src.bounds), dtypes=list(src.dtypes),
                              nodata=[str(x) if x is not None else None for x in src.nodatavals], tags=src.tags(), band_descriptions=list(src.descriptions))
                stats=[]
                for b in range(1,src.count+1):
                    masked = nonfinite = pixels = 0
                    for _, window in src.block_windows(b):
                        a=src.read(b,window=window,masked=True)
                        mask=np.ma.getmaskarray(a)
                        masked += int(mask.sum()); nonfinite += int((~np.isfinite(a.data) & ~mask).sum()); pixels += a.size
                    stats.append(dict(band=b,total_pixels=pixels,masked_pixels=masked,unmasked_nonfinite_pixels=nonfinite))
                result['missing_values']=stats
        elif suffix == '.csv' or path.name.endswith('.csv.gz'):
            import pandas as pd
            import gzip
            import numpy as np
            opener = gzip.open if path.name.endswith('.gz') else open
            with opener(path, 'rt', encoding='utf-8-sig', newline='') as f:
                first = next(csv.reader(f), [])
            def numeric_or_empty(value):
                try:
                    float(value)
                    return True
                except ValueError:
                    return not value.strip()
            headerless = bool(first) and all(numeric_or_empty(v) for v in first)
            total=0; nulls={}; nonfinite={}; empty={}; columns=None
            for frame in pd.read_csv(path,chunksize=100000,header=None if headerless else 0):
                total+=len(frame); columns=list(frame.columns)
                for k,v in frame.isna().sum().items(): nulls[str(k)]=nulls.get(str(k),0)+int(v)
                for k in frame.columns:
                    s=frame[k]
                    if s.dtype.kind in 'biufc':
                        count=int((~np.isfinite(s.to_numpy(dtype=float))).sum())
                        nonfinite[str(k)]=nonfinite.get(str(k),0)+count
                    else:
                        count=int(s.fillna('').astype(str).str.strip().eq('').sum())
                        empty[str(k)]=empty.get(str(k),0)+count
            result.update(format='CSV',rows=total,columns=columns,null_counts=nulls,
                          headerless_numeric_detected=headerless,nonfinite_numeric_counts=nonfinite,empty_or_whitespace_counts=empty,
                          note='Numeric first rows trigger header=None; other headers require manual review. Unknown sentinel codes are not inferred. CRS/time are not inferred from names.')
        elif suffix == '.xlsx':
            import pandas as pd
            result.update(format='XLSX',sheets={})
            with pd.ExcelFile(path) as workbook:
                for sheet in workbook.sheet_names:
                    result['sheets'][sheet]=audit_table(pd.read_excel(workbook,sheet_name=sheet))
        elif suffix == '.pdf':
            from pypdf import PdfReader
            reader=PdfReader(path); pages=[]
            target=ROOT/'mumbai/audit/pdf_text'/path.stem
            for i,page in enumerate(reader.pages,1):
                text=page.extract_text(extraction_mode='layout') or ''
                pages.append(dict(page=i,characters=len(text),needs_ocr=len(text.strip())<50))
                target.mkdir(parents=True,exist_ok=True)
                (target/f'page_{i:03d}.txt').write_text(text)
            result.update(format='PDF',pages=pages,note='Text extraction only: row/column alignment and OCR require review before entity matching.')
        elif suffix == '.zip':
            with zipfile.ZipFile(path) as archive:
                result.update(format='ZIP',crc_failure=archive.testzip(),members=[dict(name=i.filename,bytes=i.file_size,compressed_bytes=i.compress_size) for i in archive.infolist()])
                # Read shapefile directly through GDAL without extracting untrusted archive paths.
                shapefiles=[i.filename for i in archive.infolist() if i.filename.lower().endswith('.shp')]
            if shapefiles:
                import geopandas as gpd
                result['vector_layers']=[]
                for layer in shapefiles:
                    g=gpd.read_file(f'/vsizip/{path}/{layer}')
                    attrs=g.drop(columns=g.geometry.name)
                    result['vector_layers'].append(dict(layer=layer,crs=str(g.crs),bounds=[float(x) for x in g.total_bounds],
                        missing_geometry=int(g.geometry.isna().sum()),invalid_geometry=int((~g.geometry.is_valid).sum()),**audit_table(attrs)))
        else:
            result['format']='Uninspected format; retain for manual review'
        result['audit_status']='inspected'
    except Exception as e:
        result.update(audit_status='inspection_failed',error=str(e))
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--download',action='store_true')
    p.add_argument('--download-extra',action='store_true',help='Also attempt WSF and public GLO-30 mirror candidates')
    p.add_argument('--audit-only',action='store_true')
    args=p.parse_args()
    if args.audit_only and (args.download or args.download_extra): p.error('--audit-only cannot be combined with downloads')
    log=[]
    if args.download or args.download_extra:
        figshare(log,'mumbai',25856260,2)
        figshare(log,'lagos',19738957)
        sources=json.loads((ROOT/'mumbai/metadata/c1_sources.json').read_text())
        for s in sources:
            attempt(log,'mumbai','c1',s['url'],ROOT/'mumbai/downloads/c1'/s['filename'])
    if args.download_extra:
        for city,lon,lat,dem_cells in [('mumbai',72,18,[(18,72),(19,72),(18,73),(19,73)]),('lagos',2,6,[(6,3)])]:
            # Candidate names follow product convention. Successful retrieval and header audit are required to validate.
            name=f'WSFevolution_v1_{lon}_{lat}.tif'
            attempt(log,city,'wsf',f'https://download.geoservice.dlr.de/WSF_EVO/files/{name}',ROOT/city/'downloads/wsf'/name)
            for la,lo in dem_cells:
                name=f'Copernicus_DSM_COG_10_N{la:02d}_00_E{lo:03d}_00_DEM'
                attempt(log,city,'dem',f'https://copernicus-dem-30m.s3.amazonaws.com/{name}/{name}.tif',ROOT/city/'downloads/dem'/f'{name}.tif')
    for city in ['mumbai','lagos']:
        if log:
            citylog=[x for x in log if x['city']==city]
            save_json(ROOT/city/'audit/download_attempts.json',citylog)
        actual=[inspect_file(f) for f in sorted((ROOT/city/'downloads').rglob('*')) if f.is_file() and not f.name.endswith('.part')]
        save_json(ROOT/city/'audit/file_content_audit.json',actual)
        save_json(ROOT/city/'audit/local_inventory_summary.json',dict(files_present=len(actual),bytes_present=sum(x['size_bytes'] for x in actual),successfully_inspected=sum(x['audit_status']=='inspected' for x in actual),note='Content presence is separate from verified publisher completeness; report/catalog contains source metadata from the original audit date.'))
        print(f'{city}: {len(actual)} local source files, {sum(x["size_bytes"] for x in actual)} bytes',flush=True)
    return 1 if any(x['status']=='failed' for x in log) else 0

if __name__=='__main__':
    raise SystemExit(main())
