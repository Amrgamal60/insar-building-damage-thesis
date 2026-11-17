"""Outcome-blind 2019 -> 2026 TCAD parcel-account audit, version 3.

Usage (offline, Python -I): id_crosswalk.py PRIVATE_AUSTIN OUT_JSON PRIVATE_PARQUET TCAD_MANIFEST
Only the named parcel, roll, boundary, and public-metadata inputs are read. No
permit, remote-sensing, or outcome inputs are accepted. All row-level products
and content-addressed caches stay beside PRIVATE_PARQUET, below crosswalk/.

Stages 1/2/3 retain v1's order and 0.9 overlap thresholds. Stage 2 requires keys
unique in both years and reciprocal >=0.9 geometric corroboration. This rejects
v1's two misleading geographic matches; stage 3 finds their actual lot matches.
Split coverage uses the geometric union and requires >=2 successors. No inferred parent-ID, nearest-neighbour,
textual, or locally shifted spatial match becomes an accepted crosswalk edge.
A parcel/account successor is not proof of continuity of the physical dwelling.
"""
import argparse
import hashlib
import json
from pathlib import Path
import urllib.parse
import warnings
import zipfile

import geopandas as gpd
import numpy as np
import pandas as pd
import pyogrio
import shapely
from scipy.spatial import cKDTree
from shapely.affinity import translate

VERSION = 3


def counts(s):
    return {str(k): int(v) for k, v in s.value_counts(dropna=False).sort_index().items()}


def norm_geo(s):
    # Preserve strings/leading zeros in outputs; strip numeric padding only for comparisons.
    s = s.astype('string').str.strip()
    return s.mask(s.eq('')).str.lstrip('0').mask(lambda v: v.eq(''))


def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def describe(s):
    d = pd.Series(s).replace([np.inf, -np.inf], np.nan).describe(percentiles=[.1, .5, .9, .95, .99])
    return {k: None if pd.isna(v) else float(v) for k, v in d.items()}


def dump(path, obj):
    Path(path).write_text(json.dumps(obj, indent=2, sort_keys=True, allow_nan=False) + '\n')


def cached(path, signature, build, geo=False):
    meta = path.with_suffix('.cache.json')
    if path.exists() and meta.exists() and json.loads(meta.read_text()) == signature:
        return (gpd.read_parquet if geo else pd.read_parquet)(path)
    frame = build()
    frame.to_parquet(path, index=False)
    dump(meta, signature)
    return frame


def raw_fields(roll, layouts, filename, table, fields):
    specs = {f['field']: (f['start'] - 1, f['end']) for f in layouts[table]}
    spans = [specs[f] for f in fields]
    # Stream fixed-width bytes; never extract or execute archive members.
    with zipfile.ZipFile(roll) as z, z.open(filename) as source:
        records = [tuple(line[a:b].decode('cp1252', errors='replace').strip() for a, b in spans)
                   for line in source]
    result = pd.DataFrame.from_records(records, columns=fields)
    result['pid'] = pd.to_numeric(result.prop_id, errors='coerce')
    return result


def classify(o, threshold=.9, union=True):
    full = o[o.a >= threshold]
    if len(full) == 1:
        return ('renumbered' if full.b.iloc[0] >= threshold else 'merged',
                [int(full.pid26.iloc[0])])
    if len(full) > 1 and union:
        return 'unresolved', []
    parts = o[o.b >= threshold]
    if len(parts):
        coverage = (shapely.area(shapely.union_all(parts.geometry)) / o.area19.iloc[0]
                    if union else parts.a.sum())
        if coverage >= threshold and (len(parts) >= 2 or not union):
            return 'split', sorted(parts.pid26.astype(int).unique().tolist())
    return 'unresolved', []


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('private_austin', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('crosswalk', type=Path)
    parser.add_argument('manifest', type=Path)
    args = parser.parse_args()
    root, out, xwpath = args.private_austin.resolve(), args.output, args.crosswalk.resolve()
    private = root / 'crosswalk'
    if not xwpath.is_relative_to(private):
        raise ValueError('Row-level output must be below PRIVATE_AUSTIN/crosswalk/')
    xwpath.parent.mkdir(parents=True, exist_ok=True)
    cache = xwpath.parent
    tcad = root / 'tcad'
    manifest = json.loads(args.manifest.read_text())
    layouts = json.loads((tcad / 'derived_2026/layouts.json').read_text())
    roll = tcad / 'raw/traviscad.org_569b31953c8c/2026 Certified Appraisal Export Supp 0_07182026.zip'
    rollsha = sha(roll)
    oldzip = tcad / 'raw/www.arcgis.com_e41c24899f71/data'
    shp = ('/vsizip/{' + str(oldzip) + '}/stratmap19-landparcels_48453_vector_shp/'
           'stratmap19-landparcels_48453_travis_201909.shp')
    old = cached(cache / 'source_2019.parquet', {'sha256': sha(oldzip), 'version': VERSION},
                 lambda: pyogrio.read_dataframe(shp, columns=['PROP_ID', 'GEO_ID', 'STAT_LAND_',
                                                              'YEAR_BUILT']).to_crs(32614), geo=True)
    old['pid'] = pd.to_numeric(old.PROP_ID, errors='coerce')
    old['geo19'] = norm_geo(old.GEO_ID)
    boundarypath = tcad / 'raw/data.austintexas.gov_27339cbf4a36/vnwj-xmz9.geojson'
    boundary = gpd.read_file(boundarypath).to_crs(32614).union_all()
    g = old[old.STAT_LAND_.astype(str).str.strip().str.upper().str.startswith('A1') &
            old.YEAR_BUILT.between(1, 2015) & old.geometry.notna() &
            ~old.geometry.is_empty & old.pid.notna()].copy()
    g = g[g.geometry.centroid.within(boundary)].drop_duplicates('pid').reset_index(drop=True)
    assert len(g) == 151944, 'Historical denominator changed; audit the inputs.'
    g['geometry'] = g.geometry.make_valid()
    prop = pd.read_parquet(tcad / 'derived_2026/PROP.TXT.parquet')
    prop['pid'] = pd.to_numeric(prop.prop_id, errors='coerce')
    prop = prop.dropna(subset=['pid']).drop_duplicates('pid')
    prop['geo26'] = norm_geo(prop.geo_id)
    st = prop.set_index('pid')
    # All A1 roll parcels, including accounts without hosted geometry; pre-existing outcome-blind derivative.
    mainfields = pd.read_parquet(tcad / 'static_checks_2026/parcel_fields.parquet',
                                columns=['prop_id', 'imprv_type_cd', 'year_built'])
    mainfields['pid'] = pd.to_numeric(mainfields.prop_id, errors='coerce')
    a1 = mainfields.drop_duplicates('pid').set_index('pid')
    pop = pd.read_parquet(tcad / 'final_population_2026/eligible_2026_diagnostic.parquet',
                          columns=['prop_id_numeric', 'imprv_type_cd'])
    detached = set(pop.loc[pop.imprv_type_cd.eq('01'), 'prop_id_numeric'])

    pages, skipped = {}, {'invalid_json': 0, 'error_or_not_geojson': 0}
    for e in manifest:
        url = e.get('url', '')
        if 'TCAD_Parcels_Dec_2025' not in url or 'resultOffset' not in url or not e.get('local_path'):
            continue
        params = urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)
        try:
            d = json.loads(Path(e['local_path']).read_text())
        except (ValueError, OSError):
            skipped['invalid_json'] += 1
            continue
        if 'features' not in d:
            skipped['error_or_not_geojson'] += 1
            continue
        assert sha(e['local_path']) == e['sha256'], 'Geometry page does not match its source manifest.'
        assert d.get('crs', {}).get('properties', {}).get('name') == 'EPSG:32614'
        if params.get('outFields') != ['OBJECTID,PROP_ID,geo_id']:
            continue
        offset = int(params['resultOffset'][0])
        pages[offset] = (e, d)
    assert set(pages) == set(range(0, 386682, 10000))
    geometry_signature = {str(k): v[0]['sha256'] for k, v in sorted(pages.items())}
    def build_polygons():
        parts = [gpd.GeoDataFrame.from_features(d['features'], crs=32614)[
            ['OBJECTID', 'PROP_ID', 'geo_id', 'geometry']] for e, d in pages.values()]
        p = pd.concat(parts, ignore_index=True)
        assert len(p) == 386682 and p.OBJECTID.nunique() == 386682
        return p
    features = cached(cache / 'source_2026_features.parquet', geometry_signature, build_polygons, geo=True)
    del pages
    features['pid26'] = pd.to_numeric(features.PROP_ID, errors='coerce')
    features['geo26'] = norm_geo(features.geo_id)
    def dissolve():
        p = features[features.geometry.notna() & ~features.geometry.is_empty].dissolve(by='pid26', as_index=False)
        p.geometry = p.geometry.make_valid()
        return p
    p26 = cached(cache / 'source_2026_parcels.parquet', geometry_signature, dissolve, geo=True)
    polyids = set(p26.pid26)

    rows, left, geo_candidate_audit = [], [], []
    v1_geo_matched_old = set()
    old_geo_count = g.groupby('geo19').pid.nunique()
    polygon_index = p26.set_index('pid26')
    geogroups = prop[prop.geo26.notna()].groupby('geo26').pid.agg(lambda s: sorted(set(s.astype(int))))
    for r in g.itertuples():
        if r.pid in st.index:
            rows.append((r.pid, '1 prop_id', 'same', [int(r.pid)]))
        else:
            accepted = False
            if pd.notna(r.geo19) and r.geo19 in geogroups:
                ids = geogroups[r.geo19]
                aa = bb = None
                reason = 'current key ambiguous'
                if len(ids) == 1:
                    v1_geo_matched_old.add(r.pid)
                    successor = ids[0]
                    if successor in polygon_index.index:
                        polygon = polygon_index.geometry[successor]
                        intersection = r.geometry.intersection(polygon).area
                        aa, bb = intersection / r.geometry.area, intersection / polygon.area
                    if old_geo_count[r.geo19] != 1:
                        reason = 'historical key ambiguous'
                    elif aa is None:
                        reason = 'no hosted geometry corroboration'
                    elif aa >= .9 and bb >= .9:
                        rows.append((r.pid, '2 geo_id', 'same geo_id', ids))
                        reason, accepted = 'accepted', True
                    else:
                        reason = 'geographic key conflicts with geometry'
                geo_candidate_audit.append({'reason': reason, 'old_key_multiplicity': int(old_geo_count[r.geo19]),
                                            'share_old': aa, 'share_new': bb})
            if not accepted:
                left.append(r.Index)
    unmatched = g.loc[left, ['pid', 'geometry']].copy()
    unmatched['area19'] = unmatched.area
    newer = p26[['pid26', 'geometry']].assign(area26=p26.area)
    overlap = gpd.overlay(unmatched, newer, how='intersection', keep_geom_type=True)
    overlap['a'] = overlap.area / overlap.area19
    overlap['b'] = overlap.area / overlap.area26
    groups = {pid: f for pid, f in overlap.groupby('pid')}
    empty = overlap.iloc[:0]
    sensitivity, legacy_sensitivity = {}, {}
    for threshold in [.9, .8, .5]:
        result, legacy = [], []
        for pid in unmatched.pid:
            o = groups.get(pid, empty)
            kind, successors = classify(o, threshold)
            result.append(kind)
            if pid not in v1_geo_matched_old:
                legacy.append(classify(o, threshold, union=False)[0])
            if threshold == .9:
                rows.append((pid, '3 spatial', kind, successors))
        sensitivity[str(threshold)] = counts(pd.Series(result))
        legacy_sensitivity[str(threshold)] = counts(pd.Series(legacy))
    xw = pd.DataFrame(rows, columns=['pid19', 'stage', 'kind', 'successors']).sort_values('pid19').reset_index(drop=True)
    assert len(xw) == len(g) and xw.pid19.is_unique
    oldidx = g.set_index('pid')
    xw['geo_id_2019'] = oldidx.GEO_ID.reindex(xw.pid19).str.strip().to_numpy()
    xw['year_built_2019'] = oldidx.YEAR_BUILT.reindex(xw.pid19).to_numpy()
    xw['successor_geo_ids'] = [sorted({str(st.geo_id.get(p, '')).strip() for p in ids
                                      if p in st.index and str(st.geo_id[p]).strip()}) for ids in xw.successors]
    xw['geo_same'] = [bool(len(ids) == 1 and ids[0] in st.index and
                           st.geo26[ids[0]] == oldidx.geo19[pid]) for pid, ids in zip(xw.pid19, xw.successors)]
    def status(pid, y19):
        if pid not in st.index:
            return 'successor absent from certified roll'
        if st.imprv_state_cd[pid] != 'A1':
            return '2026 non-A1 (codes ' + (st.imprv_state_cd[pid] or '-') + '/' + (st.land_state_cd[pid] or '-') + ')'
        if pid not in a1.index or pd.isna(a1.imprv_type_cd[pid]):
            return '2026 A1, selected main dwelling missing'
        typ, year = a1.imprv_type_cd[pid], pd.to_numeric(a1.year_built[pid], errors='coerce')
        if year > 2015:
            return '2026 A1, recorded year after 2015 (rebuild/update proxy)'
        if typ == '16':
            return '2026 A1 townhouse, ' + ('same recorded year' if year == y19 else 'different/missing recorded year')
        if pd.isna(year) or year <= 0:
            return '2026 A1 type 01, recorded year missing'
        if pid in detached:
            return '2026 detached diagnostic population'
        return '2026 A1 type 01 pre-2016, outside diagnostic geometry/boundary'
    xw['status'] = ['; '.join(sorted({status(p, y) for p in ids})) if ids else '2026 successor unknown'
                    for ids, y in zip(xw.successors, xw.year_built_2019)]
    unresolved_ids = set(xw.loc[xw.kind.eq('unresolved'), 'pid19'])
    u = g[g.pid.isin(unresolved_ids)].copy()
    point = u[['pid', 'geometry']].set_geometry(u.geometry.representative_point())
    nearest = gpd.sjoin_nearest(point, p26[['pid26', 'geometry']], how='left', distance_col='nearest_m')
    nearest_min = nearest.groupby('pid').nearest_m.min()
    covered = set(nearest_min[nearest_min.eq(0)].index)
    xw['final_category'] = [
        ('unresolved: point in hosted gap' if p not in covered else 'unresolved: partial/ambiguous hosted overlap')
        if k == 'unresolved' else ('parcel ' + k + ': physical continuity unverified')
        if k in ['merged', 'split'] else '2026 non-A1' if s.startswith('2026 non-A1') else s
        for p, k, s in zip(xw.pid19, xw.kind, xw.status)]
    xw['rule'] = xw.stage + ' | ' + xw.kind

    rawprop = cached(cache / 'raw_property_audit.parquet', {'roll_sha256': rollsha, 'version': VERSION},
                     lambda: raw_fields(roll, layouts, 'PROP.TXT', 'Property', [
                         'prop_id', 'geo_id', 'ref_id1', 'ref_id2', 'udi_group',
                         'sup_action', 'sup_cd', 'sup_desc',
                         'py_confidential_flag', 'jan1_confidential_flag', 'appr_confidential_flag']))
    rawimp = cached(cache / 'raw_improvement_audit.parquet', {'roll_sha256': rollsha, 'version': VERSION},
                    lambda: raw_fields(roll, layouts, 'IMP_INFO.TXT', 'Improvement',
                                       ['prop_id', 'imprv_type_cd', 'imprv_state_cd']))
    raw_unique = rawprop.drop_duplicates('pid')
    impids = set(rawimp.pid)
    xw['successors_with_raw_improvements'] = [sum(p in impids for p in ids) for ids in xw.successors]
    derived_imp = pd.read_parquet(tcad / 'derived_2026/IMP_INFO.TXT.parquet', columns=['prop_id'])
    derived_imp_ids = set(pd.to_numeric(derived_imp.prop_id, errors='coerce'))

    # Aggregate reference-field diagnostics. Neither numeric coincidence nor an undocumented
    # string prefix is treated as a crosswalk rule.
    refs = {}
    for field in ['ref_id1', 'ref_id2', 'udi_group']:
        value = raw_unique[field]
        normalized = norm_geo(value)
        refs[field] = {'nonblank': int(value.ne('').sum()),
                       'nonzero': int((value.ne('') & value.str.strip('0').ne('')).sum()),
                       'exact_missing_old_pid_hits': int(pd.to_numeric(value, errors='coerce').isin(unresolved_ids).sum()),
                       'exact_missing_old_geo_hits': int(normalized.isin(u.geo19).sum())}
    # Same-ID geometry controls and a local translation diagnostic, never accepted links.
    stable = g[g.pid.isin(xw.loc[xw.stage.eq('1 prop_id'), 'pid19'])].merge(
        p26[['pid26', 'geometry']], left_on='pid', right_on='pid26', suffixes=('19', '26'))
    ga, gb = gpd.GeoSeries(stable.geometry19, crs=32614), gpd.GeoSeries(stable.geometry26, crs=32614)
    dx, dy = gb.centroid.x - ga.centroid.x, gb.centroid.y - ga.centroid.y
    iou = shapely.area(shapely.intersection(ga.array, gb.array)) / shapely.area(shapely.union(ga.array, gb.array))
    tree = cKDTree(np.column_stack([ga.centroid.x, ga.centroid.y]))
    distance, indices = tree.query(np.column_stack([u.centroid.x, u.centroid.y]), k=20, distance_upper_bound=200)
    valid = indices < len(stable)
    safe = np.minimum(indices, len(stable) - 1)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', RuntimeWarning)
        localx = np.nanmedian(np.where(valid, dx.to_numpy()[safe], np.nan), axis=1)
        localy = np.nanmedian(np.where(valid, dy.to_numpy()[safe], np.nan), axis=1)
    localshift = np.hypot(localx, localy)
    translated = u[['pid', 'geometry']].copy()
    translated.geometry = [translate(z, xoff=float(x), yoff=float(y)) if np.isfinite(x + y) else z
                           for z, x, y in zip(u.geometry, localx, localy)]
    translated['area19'] = translated.area
    shifted = gpd.overlay(translated, newer, how='intersection', keep_geom_type=True)
    shifted['a'] = shifted.area / shifted.area19

    # Reverse reconciliation; preserve every distinct predecessor edge, not just one.
    m1 = xw[xw.stage.eq('1 prop_id')]
    missing = sorted(detached - set(m1.pid19))
    allold = old.dropna(subset=['pid']).drop_duplicates('pid').set_index('pid')
    reverse = []
    for pid in missing:
        parents = xw[xw.successors.map(lambda ids: pid in ids)]
        if len(parents):
            reason = 'successor of 2019 house(s), stages 2/3'
        elif pid not in allold.index:
            reason = 'not in 2019 layer'
        elif not str(allold.STAT_LAND_[pid]).strip().upper().startswith('A1'):
            reason = '2019 state code ' + (str(allold.STAT_LAND_[pid]).strip() if pd.notna(allold.STAT_LAND_[pid]) else 'missing')
        elif not 1 <= allold.YEAR_BUILT[pid] <= 2015:
            reason = '2019 year built missing or after 2015'
        else:
            reason = '2019 A1 age eligible, centroid outside boundary'
        reverse.append((pid, reason, parents.pid19.astype(int).tolist(), sorted(set(parents.kind))))
    reverse = pd.DataFrame(reverse, columns=['pid26', 'reason', 'predecessors', 'kinds'])
    reverse.assign(predecessors=reverse.predecessors.map(lambda a: ','.join(map(str, a))),
                   kinds=reverse.kinds.map(lambda a: ','.join(a))).to_parquet(cache / 'reverse_2026_2019.parquet', index=False)

    # Geographic alias evidence: original keys plus one-to-one IDs only. Ambiguous
    # aliases remain flagged and cannot silently allocate a permit to several houses.
    aliases = [(int(r.pid19), str(r.geo_id_2019).strip(), '2019 reference') for r in xw.itertuples()]
    for r in xw.itertuples():
        if r.kind in ['same', 'same geo_id', 'renumbered'] and len(r.successors) == 1:
            aliases.extend((int(r.pid19), geo, r.rule) for geo in r.successor_geo_ids)
    aliases = pd.DataFrame(aliases, columns=['pid19', 'geo_id', 'source']).drop_duplicates(['pid19', 'geo_id'])
    aliases['ambiguous'] = aliases.geo_id.map(aliases.groupby('geo_id').pid19.nunique()).gt(1)
    aliases.to_parquet(cache / 'geographic_aliases_2019_2026.parquet', index=False)
    xw.assign(successors=xw.successors.map(lambda a: ','.join(map(str, a))),
              successor_geo_ids=xw.successor_geo_ids.map(lambda a: ','.join(a))).to_parquet(xwpath, index=False)
    overlap.to_parquet(cache / 'overlap_evidence.parquet', index=False)
    nearest.drop(columns='geometry').to_parquet(cache / 'nearest_evidence.parquet', index=False)

    non_a1 = m1[m1.pid19.map(st.imprv_state_cd).ne('A1')]
    polygon_by_code = {}
    for code, frame in prop.groupby('imprv_state_cd', dropna=False):
        polygon_by_code[str(code) or '(blank)'] = {'roll': len(frame), 'with_polygon': int(frame.pid.isin(polyids).sum()),
                                                'without_polygon': int((~frame.pid.isin(polyids)).sum())}
    public_metadata = cache / 'raw/tcad_arcgis_metadata/layer.json'
    md = json.loads(public_metadata.read_text()) if public_metadata.exists() else {}
    stage_counts = {f'{s} | {k}': int(v) for (s, k), v in xw.groupby(['stage', 'kind']).size().items()}
    stage_counts.setdefault('2 geo_id | same geo_id', 0)
    report = {
        'version': VERSION, 'scope': 'parcel-account continuity; physical-house continuity is not inferred',
        'houses_2019': len(g), 'prop_id_matches': len(m1),
        'prop_id_matches_with_same_geo_id': int(m1.geo_same.sum()),
        'by_stage_and_kind': stage_counts,
        'final_categories': counts(xw.final_category),
        'status_by_stage': {stage: counts(f.status) for stage, f in xw.groupby('stage')},
        'stage2_geographic_candidates': {
            'count': len(geo_candidate_audit),
            'reason_counts': counts(pd.Series([a['reason'] for a in geo_candidate_audit], dtype='string')),
            'zero_overlap_both_directions': sum(a['share_old'] == 0 and a['share_new'] == 0 for a in geo_candidate_audit),
            'historical_key_ambiguous': sum(a['old_key_multiplicity'] > 1 for a in geo_candidate_audit)},
        'v1_stage_counts_for_comparison': {'1 prop_id | same': 149857, '2 geo_id | same geo_id': 2,
            '3 spatial | renumbered': 19, '3 spatial | merged': 126, '3 spatial | split': 49, '3 spatial | unresolved': 1891},
        'threshold_sensitivity_union': sensitivity, 'threshold_sensitivity_original_v1': legacy_sensitivity,
        'geometry_source': {'valid_pages': 39, 'features': len(features), 'unique_property_ids': len(p26),
                            'skipped_manifest_bodies': skipped,
                            'hosted_definition_expression': md.get('definitionExpression'),
                            'hosted_relationship_count': len(md.get('relationships', [])),
                            'hosted_parent_or_reference_fields': [f['name'] for f in md.get('fields', [])
                                                                 if any(w in f['name'].lower() for w in ['parent', 'prev', 'ref_', 'udi'])],
                            'roll_polygon_coverage_by_improvement_state': polygon_by_code},
        'unresolved_diagnostics': {
            'count': len(u), 'representative_point_in_any_polygon': len(covered),
            'representative_point_in_hosted_gap': len(u) - len(covered),
            'nearest_polygon_distance_m': describe(nearest_min),
            'with_any_positive_area_overlap': int(overlap.loc[overlap.pid.isin(unresolved_ids), 'pid'].nunique()),
            'same_id_geometry_control_count': len(stable), 'same_id_iou': describe(iou),
            'same_id_dx_m': describe(dx), 'same_id_dy_m': describe(dy),
            'local_controls_200m_count': describe(valid.sum(axis=1)),
            'local_median_shift_m': describe(localshift),
            'local_shift_under_1m': int((localshift < 1).sum()),
            'no_controls_within_200m': int((valid.sum(axis=1) == 0).sum()),
            'nearest_local_control_m': describe(distance[:, 0]),
            'local_translation_max_overlap_ge_0_9': int((shifted.groupby('pid').a.max() >= .9).sum()),
            'reference_field_checks': refs,
            'unverified_cause': 'Hosted gaps verified; suppression, conversion and resubdivision cannot be assigned to missing accounts without an authoritative history.'},
        'improvement_flag_audit': {
            'raw_rows': len(rawimp), 'raw_unique_property_ids': len(impids),
            'derived_improvement_property_ids': len(derived_imp_ids),
            'derived_non_A1_property_ids': int(prop.loc[prop.pid.isin(derived_imp_ids), 'imprv_state_cd'].ne('A1').sum()),
            'stage1_non_A1_accounts': len(non_a1),
            'stage1_non_A1_with_raw_improvements': int(non_a1.pid19.isin(impids).sum()),
            'stage1_non_A1_without_raw_improvements': int((~non_a1.pid19.isin(impids)).sum()),
            'conclusion': 'v1 no-improvement labels were invalid: derived IMP_INFO was A1-filtered; raw absence is not demolition evidence'},
        'raw_property_audit': {'rows': len(rawprop), 'unique_property_ids': rawprop.pid.nunique(),
                               'supplement_field_nonblank': {f: int(rawprop[f].ne('').sum()) for f in ['sup_action', 'sup_cd', 'sup_desc']},
                               'confidential_flag_counts': {f: counts(rawprop[f]) for f in ['py_confidential_flag', 'jan1_confidential_flag', 'appr_confidential_flag']}},
        'reverse_2026_detached_not_matched_by_prop_id': {'count': len(reverse), 'reasons': counts(reverse.reason),
            'linked_successors_by_kind': {k: int(reverse.kinds.map(lambda a: k in a).sum()) for k in ['same geo_id', 'renumbered', 'merged', 'split']},
            'linked_successors_with_multiple_2019_predecessors': int(reverse.predecessors.map(len).gt(1).sum())},
        'aliases': {'distinct_house_geo_pairs': len(aliases), 'distinct_geo_ids': aliases.geo_id.nunique(),
                    'ambiguous_geo_ids': aliases.loc[aliases.ambiguous, 'geo_id'].nunique(),
                    'distinct_2019_geo_ids': xw.geo_id_2019.nunique(),
                    'ambiguous_2019_geo_ids': int(xw.groupby('geo_id_2019').pid19.nunique().gt(1).sum()),
                    'houses_with_ambiguous_2019_geo': int(xw.geo_id_2019.map(xw.groupby('geo_id_2019').pid19.nunique()).gt(1).sum()),
                    'note': 'Evidence only; safe permit use also requires the registered house-continuity and event-date rule.'},
        'inputs': {'roll_sha256': rollsha, 'old_geometry_sha256': sha(oldzip), 'boundary_sha256': sha(boundarypath),
                   'tcad_manifest_sha256': sha(args.manifest),
                   'all_A1_main_fields_sha256': sha(tcad / 'static_checks_2026/parcel_fields.parquet'),
                   'derived_property_sha256': sha(tcad / 'derived_2026/PROP.TXT.parquet'),
                   'roll_layout_sha256': sha(tcad / 'derived_2026/layouts.json')},
        'invariants': {'all_2019_houses_have_one_final_category': len(xw) == xw.pid19.nunique() == len(g),
                       'stage_counts_sum_to_population': sum(xw.groupby(['stage', 'kind']).size()) == len(g),
                       'reverse_counts_sum_to_417': len(reverse) == 417,
                       'no_outcome_inputs_read': True},
        'changes_from_v1': ['Stage 2 requires unique keys in both years and >=0.9 reciprocal spatial corroboration: two false geographic candidates move to stage-3 renumberings.',
                            'Split coverage uses the geometric union and >=2 successors; no accepted splits change.',
                            'Statuses use all A1 roll accounts, including those missing polygons; recorded year >2015 is a rebuild/update proxy.',
                            'Removed A1-filtered IMP_INFO absence as a no-improvement flag; full raw improvement audit added.',
                            'Added final gap/partial-overlap categories, ambiguity flags, reverse edges, sensitivity, local controls and raw-field diagnostics.']}
    # Convert numpy scalar booleans/integers without changing numeric precision.
    report = json.loads(json.dumps(report, default=lambda x: x.item() if hasattr(x, 'item') else str(x)))
    dump(out, report)
    print(json.dumps({'houses_2019': len(g), 'stages': report['by_stage_and_kind'],
                      'unresolved': len(u), 'reverse': len(reverse)}, sort_keys=True))


if __name__ == '__main__':
    main()
