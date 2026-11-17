"""Assemble reviewed settlement records and descriptive counts; never read InSAR.

Requires every blind batch and every adjudication requested by compare.json.
--private-root permits sandbox staging before installing files in Alex_private.
Engineer confirmation is deliberately left pending, never inferred from AI agreement.
"""
import argparse
import collections
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
AUDIT = ROOT / 'miami/audit/settlement'
DOS = ROOT.parent.parent / 'Alex_private/miami_dossiers_full'


def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / (name + '.py'))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def read_jsonl(p):
    return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--private-root', type=Path, default=ROOT.parent.parent / 'Alex_private/miami_settlement')
    args = ap.parse_args()
    priv = args.private_root
    check = module('miami_settlement_check')
    check.PRIV = priv
    batches = json.loads((priv / 'review_batches.json').read_text())
    errors = [e for rd in ('A', 'B') for i in range(len(batches[rd])) for e in check.check_batch(rd, i, batches)]
    if errors:
        raise ValueError(errors)
    compare = module('miami_settlement_compare')
    compare.PRIV = priv
    compare.main()
    compared = json.loads((priv / 'compare.json').read_text())
    needed = {r['case'] for r in compared['settle'] + compared['verify']}
    decisions = {}
    for p in sorted((priv / 'adjudication').glob('decisions_*.jsonl')):
        for r in read_jsonl(p):
            assert r['case'] not in decisions, ('duplicate adjudication', r['case'])
            assert r.get('adjudication_reason'), ('missing reason', r['case'])
            errors = check.check_record(r, r['case'])
            for ex in r.get('engineer_excerpts', []):
                errors += check.check_passage(ex, check.lines(r['case']), 'engineer_excerpt')
            assert not errors, (r['case'], errors)
            decisions[r['case']] = r
    assert set(decisions) == needed, ('adjudication coverage', sorted(needed - set(decisions)), sorted(set(decisions) - needed))
    A, B = compare.load('A'), compare.load('B')
    assert set(A) == set(B) == {c for batch in batches['A'] for c in batch}
    finals = [decisions.get(c, A[c]) for c in sorted(A)]
    # Keep historical blind batches intact; apply reviewed name-only trims to finals.
    corrections_file = priv / 'name_corrections.json'
    if corrections_file.exists():
        corrections = json.loads(corrections_file.read_text())
        if isinstance(corrections, dict):
            corrections = corrections['corrections']
        bycase = {r['case']: r for r in finals}
        for edit in corrections:
            parts = edit['field_path'].split('.')
            assert parts[0] in {'passage', 'doc_passage', 'engineer_excerpts', 'cause_stated',
                                'note', 'adjudication_reason'}, 'Name correction cannot alter classification or dates'
            target = bycase[edit['case']]
            for part in parts[:-1]:
                target = target[int(part)] if isinstance(target, list) else target[part]
            key = int(parts[-1]) if isinstance(target, list) else parts[-1]
            assert target[key] == edit['original_value'], ('stale correction', edit['case'], edit['field_path'])
            target[key] = edit['replacement']
        for r in finals:
            errors = check.check_record(r, r['case'])
            for ex in r.get('engineer_excerpts', []):
                errors += check.check_passage(ex, check.lines(r['case']), 'engineer_excerpt')
            assert not errors, (r['case'], errors)
    (priv / 'final.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in finals))
    # Building and episode counts are descriptive identities recorded by reviewers.
    # Same folio alone is never an episode merge.
    parent = {r['case']: r['case'] for r in finals}
    def find(c):
        if parent[c] != c:
            parent[c] = find(parent[c])
        return parent[c]
    for r in finals:
        for c in r.get('episode_cases', []):
            if c in parent:
                parent[find(c)] = find(r['case'])
    def identity(r):
        b = r['building']
        return (b.get('folio', '').strip(), b.get('label', '').strip().lower())
    byclass = {}
    for cls in sorted(check.CLASSES):
        rs = [r for r in finals if r['class'] == cls]
        byclass[cls] = {'cases': len(rs), 'recorded_building_identities': len({identity(r) for r in rs}),
                        'episodes_in_reviewed_cases': len({find(r['case']) for r in rs}),
                        'folios': len({r['building']['folio'] for r in rs}),
                        'building_types': dict(collections.Counter(r['building']['type'] for r in rs)),
                        'sources': dict(collections.Counter(r['source'] for r in rs)),
                        'missing_doc_date': sum(not r.get('doc_date') for r in rs)}
    screen = json.loads((AUDIT / 'screen.json').read_text())
    # Clopper-Pearson bounds for each stratum, as fixed in protocol section 4.
    from scipy.stats import beta
    misses = {}
    for k, sample in screen['sample'].items():
        N, n = screen['strata']['D_plumb_dropped_only' if k == 'D' else k], len(sample)
        x = sum(r['class'] in ('GFM', 'GEOM_UNRESOLVED') for r in finals if r['case'] in sample)
        lo = float(beta.ppf(.025, x, n - x + 1)) if x else 0.0
        hi = float(beta.ppf(.975, x + 1, n - x)) if x < n else 1.0
        if n == N:
            lo = hi = x / n
        misses[k] = {'population': N, 'reviewed': n, 'retained_AI_cases': x, 'estimated_missed_cases': N*x/n,
                     'bounds_95_per_stratum': [N*lo, N*hi]}
    # Existing, preserved v3 assessments are candidate controls, not new labels.
    v3 = read_jsonl(ROOT.parent.parent / 'Alex_private/miami_labels_full/reports/stage0_final.jsonl')
    controls = [r for r in v3 if r['assessment'] in ('ENG_PASS_FIRST', 'INSP_NO_DEFECT_EXPLICIT')]
    controls_table = collections.Counter((r['assessment'], r['pathway'], r['building']['type'],
                                         r.get('assessment_date', '')[:4]) for r in controls)
    summary = {'status': 'AI adjudication complete; independent structural/geotechnical review pending',
               'reviewed_cases': len(finals), 'by_class': byclass, 'agreement': compared['summary'],
               'engineer_confirmed_buildings': None, 'screen_misses': misses,
               'estimated_nonmatch_cases_GFM_or_GEOM': sum(r['estimated_missed_cases'] for r in misses.values()),
               'control_candidates_preserved_v3': [dict(assessment=k[0], pathway=k[1], building_type=k[2],
                                                       assessment_year=k[3], cases=n) for k,n in sorted(controls_table.items())],
               'controls_limitation': 'Candidate assessments only; temporal/building comparability and absence of ground distress require engineering/cohort review. No new control labels inferred.',
               'identity_limitation': 'Recorded folio plus building label; unresolved multi-building identities require engineering review. Episode counts merge explicit links only within reviewed cases.',
               'screen_misses_limitation': 'Per-stratum exact binomial bounds; their sum is not a joint 95% confidence interval. D is a census.',
               'training_started': False, 'InSAR_movement_values_inspected': False}
    candidate_file = priv / 'control_candidates.json'
    if candidate_file.exists():
        candidate_review = json.loads(candidate_file.read_text())
        for r in candidate_review['candidates']:
            assert not check.check_passage(r['passage'], check.lines(r['case']), 'control_assessment'), r['case']
        summary['retained_pathway_counts'] = candidate_review['retained_pathway_counts']
        summary['control_candidates_reviewed_nonmatches'] = {
            'cases': candidate_review['candidate_case_count'],
            'assessment_counts': candidate_review['candidate_assessment_counts'],
            'building_type_counts': candidate_review['candidate_building_type_counts'],
            'pathway_counts': candidate_review['candidate_pathway_counts'],
            'scope': candidate_review['search_scope'],
            'limitations': candidate_review['comparability_limitations']}
        summary['combined_control_candidate_cases_deduplicated'] = len(
            {r['case'] for r in controls} | {r['case'] for r in candidate_review['candidates']})
    (AUDIT / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    required = {r['case'] for r in finals if r['class'] in ('GFM', 'GEOM_UNRESOLVED') or
                (r['class'] == 'UNRELATED' and r.get('crack_pattern'))}
    required |= {r['case'] for r in compared['settle'] if
                 (r['A']['class'] in ('GFM', 'GEOM_UNRESOLVED')) != (r['B']['class'] in ('GFM', 'GEOM_UNRESOLVED')) or
                 {r['A']['class'], r['B']['class']} == {'GFM', 'GEOM_UNRESOLVED'}}
    import numpy as np
    negatives = sorted(r['case'] for r in finals if r['class'] == 'UNRELATED' and r['case'] not in required)
    rng = np.random.default_rng(20261025)
    chosen = list(rng.choice(negatives, size=min(10,len(negatives)), replace=False))
    selected = sorted(required | set(chosen))
    rng.shuffle(selected)
    # Private selection map: do not reveal random-negative status in engineer material.
    (priv / 'engineer_selection.json').write_text(json.dumps({'cases_in_packet_order': selected,
                'random_unrelated_cases': chosen, 'required_cases': sorted(required)}, indent=2) + '\n')
    print(json.dumps({'final_cases': len(finals), 'adjudicated': len(decisions),
                      'class_counts': {k:v['cases'] for k,v in byclass.items()},
                      'engineer_review_cases': len(selected)}, indent=2))


if __name__ == '__main__':
    main()
