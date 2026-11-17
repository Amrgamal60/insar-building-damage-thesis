"""Coordinator-requested synthetic calibration: 10 null datasets + 1 planted.

Seeds fixed before this calibration: no-signal 1717..1726, planted 1716.
100 independent case parcels + 50 controls/case => 5100 rows; otherwise the same
10000-pixel/25-block/62-date generator as the four-draw temporal smoke check.
All 19 surrogate draws use the registered seed 2037; model hyperparameters and
fold/stopping seeds are unchanged. No seed or result is discarded.
"""
import os
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['OMP_NUM_THREADS'] = '1'
import gc
import hashlib
import argparse
import json
from pathlib import Path
import subprocess
import sys
import time
import numpy as np
from scipy.stats import t as student_t

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(Path(__file__).resolve().parent))
from deep_model import temporal_null_test, series_from_fields
from check_temporal_null import synthetic


def baseline_associations(data):
    s,m = series_from_fields(data['dates'],data['fields'],np.isfinite(data['fields']),
                             data['row_pixel'],data['row_event_dates'])
    # First row per pixel avoids artificial weighting from repeated controls.
    _, ix = np.unique(data['row_pixel'],return_index=True)
    mask = m[ix]
    last = 60-np.argmax(mask[:,::-1],axis=1)
    endpoint = s[ix,last]
    corrs = [float(np.corrcoef(endpoint,data['baseline'][ix,j])[0,1]) for j in range(9)]
    return dict(endpoint_baseline_correlations=corrs,
                max_abs_endpoint_baseline_correlation=max(abs(x) for x in corrs),
                unique_sampled_pixels=len(ix))


def main():
    ap = argparse.ArgumentParser()
    group = ap.add_mutually_exclusive_group()
    group.add_argument('--late-batch', action='store_true', help='Run only 1725,1726,1716; no aggregation')
    group.add_argument('--middle-batch', action='store_true', help='Run only 1723,1724; no aggregation')
    args = ap.parse_args()
    outdir = Path(__file__).parent/'calibration'
    outdir.mkdir(exist_ok=True)
    before = subprocess.check_output(['nvidia-smi','--query-gpu=memory.free','--format=csv,noheader,nounits'],text=True).strip()
    if int(before.splitlines()[0]) < 6000:
        raise RuntimeError('Calibration requires 6000 MiB free VRAM; no process will be stopped')
    cases = [('no_signal',seed) for seed in range(1717,1727)]+[('planted_signal',1716)]
    if args.late_batch:
        cases = [('no_signal',1725),('no_signal',1726),('planted_signal',1716)]
    elif args.middle_batch:
        cases = [('no_signal',1723),('no_signal',1724)]
    source_files = [ROOT/'deep_model.py', ROOT/'lowmem_null.py', ROOT/'nyc_lib.py',
                    ROOT/'requirements_austin.txt', Path(__file__).with_name('check_temporal_null.py')]
    provenance = {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in source_files}
    prior_summary = Path(__file__).with_name('temporal_calibration_results.json')
    prior = json.loads(prior_summary.read_text()) if prior_summary.exists() else {}
    original_wall = prior.get('initial_wall_seconds', prior.get('elapsed_this_invocation_seconds'))
    results = []
    start = time.perf_counter()
    for label,seed in cases:
        # Persist completed replicates so an interrupted diagnostic can resume.
        path = outdir/f'{label}_{seed}.json'
        if path.exists():
            result = json.loads(path.read_text())
            assert result['seed_dataset'] == seed and len(result['draws']) == 19
            assert result['source_sha256'] == provenance, 'Cached model/generator sources changed'
            assert result['p'] == (1+result['exceedances'])/20
            print(json.dumps({'resumed':str(path.name),'p':result['p']}),flush=True)
        else:
            data = synthetic(label=='planted_signal',seed,n_cases=100)
            begin = time.perf_counter()
            result,_ = temporal_null_test(**data,expected_draws=19,diagnostics=True)
            result.update(seed_dataset=seed,scenario=label,rows=5100,source_sha256=provenance,
                          baseline_associations=baseline_associations(data),
                          elapsed_seconds=time.perf_counter()-begin)
            path.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
            print(json.dumps({'scenario':label,'seed_dataset':seed,'p':result['p'],
                              'observed_delta':result['observed_delta_pr_auc'],
                              'mean_null_delta':float(np.mean([d['delta_pr_auc'] for d in result['draws']])),
                              'elapsed_seconds':result['elapsed_seconds']}),flush=True)
            del data
            gc.collect()
            import cupy as cp
            cp.get_default_memory_pool().free_all_blocks()  # this process's pool only
        results.append(result)
    if args.late_batch or args.middle_batch:
        return
    ns = [r for r in results if r['scenario']=='no_signal']
    observed = np.array([r['observed_delta_pr_auc'] for r in ns])
    null = np.array([[d['delta_pr_auc'] for d in r['draws']] for r in ns])
    ps = np.array([r['p'] for r in ns])
    fields = list(ns[0]['observed_series_diagnostics'])
    diagnostic_summary = {}
    for field in fields:
        real = np.array([r['observed_series_diagnostics'][field] for r in ns])
        fake = np.array([[d['series_diagnostics'][field] for d in r['draws']] for r in ns])
        diagnostic_summary[field] = dict(real_mean=float(real.mean()), real_sd=float(real.std(ddof=1)),
                                         null_mean=float(fake.mean()),null_sd=float(fake.std(ddof=1)))
    summary = dict(synthetic_only=True,status='COMPLETED',rows_per_dataset=5100,
                   no_signal_dataset_seeds=list(range(1717,1727)),planted_dataset_seed=1716,
                   surrogate_seed=2037,draws_per_dataset=19,minimum_attainable_p=.05,
                   no_signal_p_values=ps.tolist(),no_signal_mean_p=float(ps.mean()),
                   no_signal_count_p_equals_005=int(np.sum(ps==.05)),
                   expected_discrete_uniform_mean_p=.525,
                   paired_gain_difference_ci95=(np.mean(observed-null.mean(axis=1))+
                       np.array([-1,1])*student_t.ppf(.975,9)*np.std(observed-null.mean(axis=1),ddof=1)/np.sqrt(10)).tolist(),
                   observed_gains=observed.tolist(),
                   observed_gain_mean=float(observed.mean()),observed_gain_sd=float(observed.std(ddof=1)),
                   null_gain_mean=float(null.mean()),null_gain_sd_pooled=float(null.std(ddof=1)),
                   null_mean_gain_per_dataset=null.mean(axis=1).tolist(),
                   paired_observed_minus_mean_null_mean=float((observed-null.mean(axis=1)).mean()),
                   paired_observed_minus_mean_null_sd=float((observed-null.mean(axis=1)).std(ddof=1)),
                   observed_series_diagnostics_vs_null=diagnostic_summary,
                   planted_p=results[-1]['p'],planted_observed_gain=results[-1]['observed_delta_pr_auc'],
                   planted_null_gains=[d['delta_pr_auc'] for d in results[-1]['draws']],
                   elapsed_this_invocation_seconds=time.perf_counter()-start,
                   initial_wall_seconds=original_wall if original_wall is not None else time.perf_counter()-start,
                   summed_replicate_seconds=sum(r['elapsed_seconds'] for r in results),
                   nvidia_smi_free_mib_before=before,
                   replicate_files=[str(Path('calibration')/f'{label}_{seed}.json') for label,seed in cases])
    (Path(__file__).parent/'temporal_calibration_results.json').write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n')
    print(json.dumps(summary,indent=2),flush=True)


if __name__ == '__main__':
    main()
