"""Synthetic resampling timing and transparent full temporal-null cost projection.

No real geometry is read. The historic setup/draw times and P are the registered
synthetic-value timing in the plan, not a new 254-date GPU verification.
"""
import os
os.environ['OPENBLAS_NUM_THREADS'] = '1'
import json
from pathlib import Path
import sys
import time
import numpy as np
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from deep_model import series_from_fields


def main():
    n, dates_n, rows = 111039,254,300000
    rng = np.random.default_rng(808)
    dates = np.datetime64('2016-07-10')+np.linspace(0,3418,dates_n).astype('timedelta64[D]')
    fields = rng.normal(size=(dates_n,n)).astype(np.float32)
    valid = rng.random(fields.shape)>=.1
    fields[~valid] = np.nan
    pixel = rng.integers(n,size=rows)
    months = np.arange(np.datetime64('2018-08','M'),np.datetime64('2025-12','M'))
    events = months[rng.integers(len(months),size=rows)].astype('datetime64[D]')+np.timedelta64(15,'D')
    start = time.perf_counter()
    values, mask = series_from_fields(dates,fields,valid,pixel,events)
    preparation = time.perf_counter()-start
    deep = json.loads((Path(__file__).parent/'deep_realistic_results.json').read_text())
    folds = deep['folds']
    comparison = sum(f['comparison']['elapsed_seconds'] for f in folds)
    series = sum(f['series']['elapsed_seconds'] for f in folds)
    overhead = deep['elapsed_seconds']-comparison-series
    series_refit = series+max(overhead,0)
    # Linear window-count extrapolation of the registered identical-size benchmark.
    historic_windows, historic_setup, historic_draw, pairs = 88,77.7,6.9,15338069
    setup = historic_setup*dates_n/historic_windows
    draw = historic_draw*dates_n/historic_windows
    generation_99 = setup+99*draw
    refit_99 = 99*(series_refit+preparation)
    cap_fit = sum(f['series']['elapsed_seconds']*16/f['series']['epochs_run'] for f in folds)+max(overhead,0)
    result = dict(synthetic_only=True, pixels=n, acquisition_dates=dates_n, rows=rows, steps=61,
                  synthetic_unique_event_months=len(months), resampling_seconds=preparation,
                  paired_five_fold_seconds=deep['elapsed_seconds'],
                  measured_series_training_prediction_seconds=series,
                  shared_preprocessing_seconds=overhead,
                  estimated_series_only_full_refit_seconds=series_refit,
                  date_field_generation_projected_setup_seconds=setup,
                  date_field_generation_projected_draw_seconds=draw,
                  date_field_generation_projected_99_seconds=generation_99,
                  series_refits_and_resampling_projected_99_seconds=refit_99,
                  total_projected_99_seconds=generation_99+refit_99,
                  total_projected_99_hours=(generation_99+refit_99)/3600,
                  total_projected_99_all_16_epochs_hours=(generation_99+99*(cap_fit+preparation))/3600,
                  historical_benchmark='plan §10 / step0/timing/timing_k1000_lowmem.json, 111039 pixels, 88 windows, kmax1000',
                  assumptions=['generation time scales linearly with date count; setup scaling deliberately conservative',
                               'same spatial pair density and hardware as prior benchmark',
                               'series-only refit = measured series model time plus all measured shared preprocessing',
                               'surrogates can early-stop at different epochs; cap projection scales measured per-fold time',
                               'stream date fields; do not materialise all 99 draws'],
                  boolean_valid_pair_mask_gb=dates_n*pairs/1e9,
                  float64_source_date_field_gb=dates_n*n*8/1e9,
                  all_99_float32_date_fields_gb=99*dates_n*n*4/1e9,
                  full_date_gpu_memory='UNVERIFIED: historic 88-window transient pool was 22.01 GB; 254-date setup may exceed free VRAM',
                  full_99_draw_run='UNVERIFIED: projected, not executed')
    (Path(__file__).parent/'temporal_budget_results.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps(result,indent=2))


if __name__ == '__main__':
    main()
