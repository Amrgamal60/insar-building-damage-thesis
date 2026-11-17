"""Synthetic-only temporal surrogate -> resampling -> CNN null checks.

Four draws per planted/no-signal scenario are an implementation/rank smoke test,
not a type-I error calibration or a 0.05 test (minimum attainable p is 0.2).
"""
import os
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['OMP_NUM_THREADS'] = '1'
import json
from pathlib import Path
import subprocess
import sys
import time
import numpy as np
from sklearn.model_selection import StratifiedGroupKFold

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from deep_model import temporal_null_test, resample_series, series_from_fields


def synthetic(signal, seed, n_cases=400):
    rng = np.random.default_rng(seed)
    # 25 real 2 km blocks, each holding a 20x20 cluster of synthetic 30 m pixels.
    i = np.arange(10000)
    blocks = i//400
    ix = i%400
    xy = np.c_[(blocks%5)*2000+(ix%20)*30+15,
               (blocks//5)*2000+(ix//20)*30+15]
    latent = rng.normal(size=10000)
    t = np.linspace(0,1,62)
    fields = latent[None,:]*t[:,None] + .15*rng.normal(size=(62,10000))
    fields += .2*rng.normal(size=(1,10000))*np.sin(4*np.pi*t[:,None])
    fields[rng.random(fields.shape)<.08] = np.nan
    dates = np.datetime64('2025-01-01')-np.arange(732,-1,-12).astype('timedelta64[D]')
    probability = np.exp(2*latent) if signal else np.ones(10000)
    cases = rng.choice(10000,n_cases,replace=False,p=probability/probability.sum())
    eligible_controls = np.setdiff1d(i,cases)
    risksets = np.stack([np.r_[case,rng.choice(eligible_controls,50,replace=False)] for case in cases])
    row_pixel = risksets.ravel()
    y = np.tile(np.r_[1,np.zeros(50,dtype=int)],n_cases).astype(int)
    holds_event = np.isin(i,cases).astype(int)
    parcel_baseline = rng.normal(size=(10000,9)).astype(np.float32)
    parcel_baseline[:,0] += .7*holds_event
    parcel_fold = np.full(10000,-1)
    for k,(_,test) in enumerate(StratifiedGroupKFold(5,shuffle=True,random_state=42).split(i,holds_event,blocks)):
        parcel_fold[test] = k
    return dict(baseline=parcel_baseline[row_pixel], dates=dates, fields=fields,
                row_pixel=row_pixel, row_event_dates=np.full(len(y),np.datetime64('2025-01-17')),
                y=y, blocks=blocks[row_pixel], fold=parcel_fold[row_pixel], xy=xy)


def main():
    free = subprocess.check_output(['nvidia-smi','--query-gpu=memory.free','--format=csv,noheader,nounits'],text=True).strip()
    if int(free.splitlines()[0]) < 6000:
        result = dict(status='UNVERIFIED',reason='Less than 6000 MiB GPU memory free',nvidia_smi_free_mib=free)
    else:
        result = dict(status='PASS',synthetic_only=True,draws_per_scenario=4,
                      minimum_attainable_p=.2,nvidia_smi_free_mib=free)
        for name,signal,seed in [('planted_signal',True,716),('no_signal',False,717)]:
            data = synthetic(signal,seed)
            # The efficient field resampler must exactly match the single-series code.
            s,m = series_from_fields(data['dates'],data['fields'],np.isfinite(data['fields']),
                                     data['row_pixel'],data['row_event_dates'])
            for row in [0,1,50,51,300,20000]:
                ss,mm = resample_series(data['dates'],data['fields'][:,data['row_pixel'][row]],data['row_event_dates'][row])
                assert np.array_equal(mm,m[row]) and np.array_equal(ss,s[row])
            t0 = time.perf_counter()
            out,_ = temporal_null_test(**data,expected_draws=4,progress=True)
            out['elapsed_total_seconds'] = time.perf_counter()-t0
            out['single_vs_field_resampler_exact'] = True
            assert all(r['real_mask_identical'] for r in out['draws'])
            assert all(r['comparison'].get('reused') for draw in out['draws'] for r in draw['folds'])
            if signal:
                assert out['observed_delta_pr_auc'] > 0
                assert out['exceedances'] <= 1, out['p']
            else:
                assert out['p'] >= .05  # smoke only: four draws cannot test 0.05
            result[name] = out
            print(json.dumps({'scenario':name,'p':out['p'],
                              'observed_delta_pr_auc':out['observed_delta_pr_auc'],
                              'null_deltas':[r['delta_pr_auc'] for r in out['draws']]}),flush=True)
    (Path(__file__).parent/'temporal_null_results.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')


if __name__ == '__main__':
    main()
