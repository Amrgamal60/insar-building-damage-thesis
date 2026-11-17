"""Austin temporal model, AUSTIN_PLAN §12.20 (secondary, budget permitting).

FIXED AUTHORS' CHOICES, proposed by the script author; no real-data tuning:
* Information set: §7 event-month anchoring, confirmed by coordinator 2026-11-01.
  T = first day of case's month; every row in that risk set uses the same T.
  Window [T-24 calendar months,T); grid T-[732,720,...,12] days (61 steps).
  Nearest acquisition within 6 days, ties earlier; no interpolation. A step is
  masked if its inclusive +/-6-day neighbourhood crosses the window boundary.
  Reason: same pre-month information as Test A; no fabricated observations.
* Displacement in mm, subtract first valid sampled value per row; missing 0,
  mask 0, valid mask 1. Reason: remove arbitrary displacement datum, keep gaps.
* Baseline 1 columns supplied in checkpoint order (option A/C chosen upstream),
  train-only mean/SD; series divided by one train-only SD across valid values
  after referencing, with no centring; no per-row scaling. Reason: preserve
  relative amplitude and velocity and avoid validation/test leakage.
* Encoder: Conv1d(2,8,k=5,pad=2), ReLU, Conv1d(8,8,k=3,pad=1), ReLU,
  AdaptiveAvgPool1d(4), Flatten, Linear(32,8), ReLU. Value + mask are channels.
  Reason: small local filters and four time bins retain coarse temporal shape.
* Head: Linear(p+8,16), ReLU, Linear(16,1). Comparison removes the encoder and
  its eight inputs, otherwise the identical p->16->1 head and training rules.
  Baseline-input weights and head biases/output weights are initially shared.
  Reason: isolate the series contribution with a small matched baseline head.
* Loss: BCEWithLogitsLoss(pos_weight=Nnegative/Npositive on inner training).
  Reason: sampled Test A risk sets have about 50 controls per case.
* AdamW, lr=.001, weight_decay=.0001, betas=(.9,.999), eps=1e-8; batch=1024;
  cap=16 epochs; no scheduler/dropout/augmentation. Reason: modest fixed budget.
* Early stop: minimum inner-validation weighted BCE, min_delta=.0001,
  patience=3 complete epochs; restore best epoch, no outer-training refit.
  Reason: validation is outcome-separate from held-out blocks.
* Outer fold map INPUT from Test A (SGKF 5/shuffle/42 on eligible parcels), never
  regenerated on repeated risk-set rows. Inner: first SGKF(5,shuffle=True,
  random_state=4242+outer_fold) split of outer-training rows grouped by 2km
  block, with row y for stratification. Reason: spatially separated stopping.
* Seeds: model 2040+outer_fold, batches 3040+outer_fold, same for both models;
  NumPy/Python/torch seeded; CPU only, float32, one torch thread and one interop
  thread; deterministic algorithms and MKLDNN deterministic mode, no CUDA.
  Reason: reproducible scores and no competition with the model-server GPU.
* OOF outputs retain input row order and include both scores, y, block, fold;
  paired comparisons/bootstrap must use those exact rows, pooled across folds.
  Temporal null: LowMemVariogramNull on acquisition-date displacement fields,
  real acquisition/step masks, seed 2037, 99 draws; refit series network only,
  reuse observed comparison scores; upper-tail delta pooled PR AUC statistic.
  Construction registered by coordinator 2026-11-01 (see temporal_null_test).
"""
from __future__ import annotations
import argparse
import copy
import json
import random
import time
from pathlib import Path
import numpy as np
import pandas as pd
import torch
from sklearn.model_selection import StratifiedGroupKFold
from torch import nn

STEPS = 61
BATCH_SIZE = 1024
EPOCHS = 16
PATIENCE = 3
MIN_DELTA = 1e-4
LEARNING_RATE = 1e-3
WEIGHT_DECAY = 1e-4


def configure_cpu():
    torch.set_num_threads(1)
    if torch.get_num_interop_threads() != 1:
        torch.set_num_interop_threads(1)
    torch.use_deterministic_algorithms(True)
    torch.backends.mkldnn.deterministic = True


def _sampling_indices(dates, event_date):
    """Shared nearest-date lookup for individual and field-based resampling."""
    month = pd.Timestamp(event_date).to_period('M').start_time
    start = (month - pd.DateOffset(months=24)).to_datetime64()
    end = month.to_datetime64()
    grid = end - np.arange(732, 0, -12).astype('timedelta64[D]')
    available = np.flatnonzero((dates >= start) & (dates < end))
    available = available[np.argsort(dates[available], kind='stable')]
    positions = np.full(STEPS, -1, int)
    radius = np.timedelta64(6, 'D')
    for j, step in enumerate(grid):
        if step-radius < start or step+radius >= end or not len(available):
            continue
        i = available[int(np.argmin(np.abs(dates[available]-step)))]
        if abs(dates[i]-step) <= radius:
            positions[j] = i
    return positions


def resample_series(dates, displacement_mm, event_date):
    """One parcel's acquired series -> referenced values[61], mask[61].

    Input acquisitions already obey §7 masks/re-referencing and connected
    component rules. Nonfinite displacement is missing. Duplicate dates error.
    event_date is the CASE date for every parcel in a risk set, including controls.
    """
    dates = np.asarray(dates, dtype='datetime64[ns]')
    values = np.asarray(displacement_mm, dtype=float)
    if dates.ndim != 1 or values.shape != dates.shape or np.isnat(dates).any():
        raise ValueError('Finite dates and matching one-dimensional values required')
    if len(np.unique(dates)) != len(dates):
        raise ValueError('Duplicate acquisition date')
    ix = _sampling_indices(dates, event_date)
    out, mask = np.zeros(STEPS, np.float32), np.zeros(STEPS, bool)
    keep = ix >= 0
    mask[keep] = np.isfinite(values[ix[keep]])
    out[mask] = values[ix[mask]]
    if mask.any():
        out[mask] -= out[np.flatnonzero(mask)[0]]
    return out, mask


def series_from_fields(dates, fields, real_valid, row_pixel, row_event_dates, real_step_mask=None):
    """Date-by-pixel displacement -> all row series, using the real acquisition mask.

    Date validity and optional additional real row/step masks (e.g. construction
    masks) are imposed before first-valid referencing. Real and surrogate series
    use this SAME function. Rows identify their parcel's pixel by zero-based index
    and their CASE's event date. Months are grouped only for efficient indexing.
    """
    dates = np.asarray(dates, dtype='datetime64[ns]')
    f, valid = np.asarray(fields), np.asarray(real_valid, bool)
    pixels, events = np.asarray(row_pixel, int), np.asarray(row_event_dates, dtype='datetime64[ns]')
    if f.ndim != 2 or f.shape != valid.shape or len(dates) != len(f):
        raise ValueError('Expected (date,pixel) field and real acquisition mask')
    if np.isnat(dates).any() or len(np.unique(dates)) != len(dates) or np.isnat(events).any():
        raise ValueError('Unique finite acquisition dates and finite event dates required')
    if pixels.shape != events.shape or pixels.ndim != 1 or (pixels<0).any() or (pixels>=f.shape[1]).any():
        raise ValueError('Invalid row-pixel/event mapping')
    if not np.isfinite(f[valid]).all():
        raise ValueError('Surrogate missing where real acquisition was valid')
    out, mask = np.zeros((len(pixels), STEPS), np.float32), np.zeros((len(pixels), STEPS), bool)
    months = events.astype('datetime64[M]')
    for month in np.unique(months):
        rows = np.flatnonzero(months==month)
        ix = _sampling_indices(dates, month.astype('datetime64[ns]'))
        good = ix >= 0
        selected = np.where(good, ix, 0)
        m = valid[selected[None,:],pixels[rows,None]] & good[None,:]
        if real_step_mask is not None:
            rm = np.asarray(real_step_mask, bool)
            if rm.shape != out.shape:
                raise ValueError('Additional real step mask shape mismatch')
            m &= rm[rows]
        raw = f[selected[None,:], pixels[rows,None]]
        v = np.where(m, raw, 0.).astype(np.float32)
        first = np.argmax(m, axis=1)
        v = np.where(m, v-v[np.arange(len(rows)),first,None], 0.)
        out[rows], mask[rows] = v, m
    return out, mask


class Network(nn.Module):
    def __init__(self, n_baseline, with_series):
        super().__init__()
        self.with_series = with_series
        if with_series:
            self.encoder = nn.Sequential(nn.Conv1d(2, 8, 5, padding=2), nn.ReLU(),
                                         nn.Conv1d(8, 8, 3, padding=1), nn.ReLU(),
                                         nn.AdaptiveAvgPool1d(4), nn.Flatten(),
                                         nn.Linear(32, 8), nn.ReLU())
        self.head = nn.Sequential(nn.Linear(n_baseline+(8 if with_series else 0), 16),
                                  nn.ReLU(), nn.Linear(16, 1))

    def forward(self, baseline, series_mask):
        x = torch.cat((baseline, self.encoder(series_mask)), dim=1) if self.with_series else baseline
        return self.head(x).squeeze(1)


def _loss(model, b, s, y, criterion, rows):
    total = 0.
    model.eval()
    with torch.no_grad():
        for chunk in np.array_split(rows, max(1, int(np.ceil(len(rows)/BATCH_SIZE)))):
            total += criterion(model(b[chunk], s[chunk]), y[chunk]).item()*len(chunk)
    return total/len(rows)


def _train(model, b, s, y, train, val, fold):
    criterion = nn.BCEWithLogitsLoss(pos_weight=torch.tensor(float((y[train]==0).sum()/(y[train]==1).sum())))
    optimizer = torch.optim.AdamW(model.parameters(), lr=LEARNING_RATE, weight_decay=WEIGHT_DECAY,
                                  betas=(.9, .999), eps=1e-8)
    rng = np.random.default_rng(3040+fold)
    best, best_state, stale, history = np.inf, None, 0, []
    for epoch in range(EPOCHS):
        model.train()
        order = rng.permutation(train)
        for a in range(0, len(order), BATCH_SIZE):
            ix = order[a:a+BATCH_SIZE]
            optimizer.zero_grad(set_to_none=True)
            loss = criterion(model(b[ix], s[ix]), y[ix])
            if not torch.isfinite(loss):
                raise RuntimeError('Nonfinite training loss')
            loss.backward()
            optimizer.step()
        vl = _loss(model, b, s, y, criterion, val)
        history.append(vl)
        if vl < best-MIN_DELTA:
            best, best_state, stale = vl, copy.deepcopy(model.state_dict()), 0
            best_epoch = epoch+1
        else:
            stale += 1
        if stale >= PATIENCE:
            break
    model.load_state_dict(best_state)
    return dict(epochs_run=len(history), best_epoch=best_epoch, validation_loss=best,
                validation_history=history, rows_train=len(train), rows_validation=len(val),
                pos_weight=float(criterion.pos_weight))


def _predict(model, b, s, rows):
    out = []
    model.eval()
    with torch.no_grad():
        for a in range(0, len(rows), BATCH_SIZE):
            ix = rows[a:a+BATCH_SIZE]
            out.append(torch.sigmoid(model(b[ix], s[ix])).numpy())
    return np.concatenate(out)


def oof_scores(baseline, series, mask, y, blocks, fold, progress=False, comparison_scores=None):
    """Fit fixed paired networks and return score arrays plus fold audit metadata.

    series: referenced sampled mm values, [row,61]; mask [row,61] is boolean.
    baseline: numeric finite design matrix, including pre-encoded foundation
    indicators when required; upstream performs the identical-row missing rule.
    Inputs are copied, never altered. Fold map must keep each block in one fold.
    """
    configure_cpu()
    base, values = np.asarray(baseline, dtype=np.float32), np.asarray(series, dtype=np.float32)
    mask, yy, blocks, fold = np.asarray(mask), np.asarray(y), np.asarray(blocks), np.asarray(fold)
    n = len(yy)
    if base.ndim != 2 or base.shape[0] != n or values.shape != (n, STEPS) or mask.shape != values.shape:
        raise ValueError('Input shapes do not match')
    if any(a.shape != (n,) for a in [yy, blocks, fold]):
        raise ValueError('One y/block/fold per row required')
    if not np.isin(mask, [0, 1]).all() or not np.isin(yy, [0, 1]).all():
        raise ValueError('Binary y and mask required')
    mask = mask.astype(bool)
    if not np.isfinite(base).all() or not np.isfinite(values[mask]).all():
        raise ValueError('Missing baseline or unmasked series value')
    if not np.array_equal(np.unique(fold), np.arange(5)):
        raise ValueError('Expected input fold labels 0..4')
    if pd.DataFrame({'block':blocks, 'fold':fold}).groupby('block').fold.nunique().max() != 1:
        raise ValueError('Outer fold map splits a spatial block')
    scores = {name: np.full(n, np.nan, np.float32) for name in ['comparison', 'series']}
    if comparison_scores is not None:
        cached = np.asarray(comparison_scores, np.float32)
        if cached.shape != (n,) or not np.isfinite(cached).all():
            raise ValueError('Invalid cached comparison OOF scores')
        scores['comparison'][:] = cached
    audit = []
    for k in range(5):
        begin = time.perf_counter()
        outer_train, test = np.flatnonzero(fold!=k), np.flatnonzero(fold==k)
        splitter = StratifiedGroupKFold(5, shuffle=True, random_state=4242+k)
        it, iv = next(splitter.split(base[outer_train], yy[outer_train], blocks[outer_train]))
        train, val = outer_train[it], outer_train[iv]
        if any(len(np.unique(yy[ix])) != 2 for ix in [train, val]):
            raise ValueError('Inner training and validation must each contain both classes')
        mean = base[train].mean(0, dtype=np.float64)
        sd = base[train].std(0, dtype=np.float64)
        sd[sd == 0] = 1.
        b = torch.from_numpy(((base-mean)/sd).astype(np.float32))
        observed_train = values[train][mask[train]]
        scale = float(np.std(observed_train, dtype=np.float64)) if observed_train.size else 1.
        if scale == 0:
            scale = 1.
        x = np.stack([np.where(mask, values/scale, 0.), mask.astype(np.float32)], axis=1)
        s, yt = torch.from_numpy(x.astype(np.float32)), torch.from_numpy(yy.astype(np.float32))
        seed = 2040+k
        random.seed(seed)
        np.random.seed(seed)
        torch.manual_seed(seed)
        comparison = Network(base.shape[1], False)
        torch.manual_seed(seed)
        full = Network(base.shape[1], True)
        with torch.no_grad():
            full.head[0].weight[:, :base.shape[1]].copy_(comparison.head[0].weight)
            full.head[0].bias.copy_(comparison.head[0].bias)
            full.head[2].load_state_dict(comparison.head[2].state_dict())
        info = dict(fold=k, series_scale=scale, baseline_mean=mean.tolist(), baseline_sd=sd.tolist(),
                    training_blocks=np.unique(blocks[train]).tolist(),
                    validation_blocks=np.unique(blocks[val]).tolist(), test_blocks=np.unique(blocks[test]).tolist())
        for name, net in [('comparison', comparison), ('series', full)]:
            if name == 'comparison' and comparison_scores is not None:
                info[name] = {'reused': True}
                continue
            model_begin = time.perf_counter()
            info[name] = _train(net, b, s, yt, train, val, k)
            scores[name][test] = _predict(net, b, s, test)
            info[name]['elapsed_seconds'] = time.perf_counter()-model_begin
        info['elapsed_seconds'] = time.perf_counter()-begin
        audit.append(info)
        if progress:
            print(json.dumps({'fold':k, 'elapsed_seconds':info['elapsed_seconds'],
                              'comparison_epoch':info['comparison'].get('best_epoch', 'reused'),
                              'series_epoch':info['series']['best_epoch']}), flush=True)
    if not all(np.isfinite(s).all() for s in scores.values()):
        raise RuntimeError('Missing OOF score')
    return scores, audit


def series_diagnostics(series, mask):
    """Descriptive only: raw scale, marginal shape and lag-one temporal behavior."""
    from scipy.stats import skew, kurtosis
    v, m = np.asarray(series, float), np.asarray(mask, bool)
    x = v[m]
    pair = m[:, 1:] & m[:, :-1]
    a, b = v[:, :-1][pair], v[:, 1:][pair]
    var = float(np.var(x))
    return dict(mean=float(np.mean(x)), sd=float(np.std(x)),
                skewness=float(skew(x)), excess_kurtosis=float(kurtosis(x)),
                pooled_lag1_correlation=float(np.corrcoef(a,b)[0,1]),
                mean_squared_step_over_variance=float(np.mean((b-a)**2)/max(var,1e-12)),
                valid_share=float(m.mean()))


def temporal_null_test(baseline, dates, fields, row_pixel, row_event_dates, y, blocks, fold,
                       expected_draws=99, xy=None, res=30., surrogate_fields=None,
                       real_step_mask=None, progress=False, diagnostics=False):
    """Registered temporal null: acquisition-date fields -> series -> OOF refits.

    Default fields are in acquisition-date rows over all Test A eligible pixels;
    validity is frozen from real fields. A single LowMemVariogramNull (kmax=1000,
    chunk=8, NYC max_lag=16) shares permutation/k/noise across every date per draw.
    Default seed=2037 and 99 draws. Streaming injected surrogate_fields supports
    reproducible checks; each item is an array or NYC (array,k) tuple. For
    production use the default generator, not an independently seeded sequence.
    Comparison OOF scores are computed once, then reused unchanged. Any failed
    fit, changed step mask or wrong draw count fails the entire run.
    """
    from sklearn.metrics import average_precision_score
    real_valid = np.isfinite(fields)
    series, mask = series_from_fields(dates, fields, real_valid, row_pixel, row_event_dates, real_step_mask)
    t0 = time.perf_counter()
    observed, audit = oof_scores(baseline, series, mask, y, blocks, fold, progress=progress)
    observed_seconds = time.perf_counter()-t0
    comparison_pr = float(average_precision_score(y, observed['comparison']))
    statistic = float(average_precision_score(y, observed['series'])-comparison_pr)
    setup_seconds = 0.
    null = None
    if surrogate_fields is None:
        if xy is None:
            raise ValueError('Pixel coordinates required for default temporal null')
        # Imports are local so ordinary CPU model fits do not initialise CUDA.
        import sys
        root = Path(__file__).resolve().parent
        # Explicit path supports isolated Python (-I); all sources are frozen here.
        if str(root) not in sys.path:
            sys.path.insert(0, str(root))
        from lowmem_null import LowMemVariogramNull
        t0 = time.perf_counter()
        null = LowMemVariogramNull(np.asarray(fields), np.asarray(xy), res, kmax=1000, chunk=8)
        null.cp.cuda.Device().synchronize()
        setup_seconds = time.perf_counter()-t0
        surrogate_fields = null.draws(expected_draws, np.random.default_rng(2037))
    records = []
    iterator = iter(surrogate_fields)
    while True:
        t0 = time.perf_counter()
        try:
            draw = next(iterator)
        except StopIteration:
            break
        generation_seconds = time.perf_counter()-t0
        field, k = draw if isinstance(draw, tuple) else (draw, None)
        t0 = time.perf_counter()
        values, smask = series_from_fields(dates, field, real_valid, row_pixel, row_event_dates, real_step_mask)
        preparation_seconds = time.perf_counter()-t0
        if not np.array_equal(mask, smask):
            raise RuntimeError('Surrogate changed the real row/step mask')
        t0 = time.perf_counter()
        fitted, fit_audit = oof_scores(baseline, values, smask, y, blocks, fold,
                                      comparison_scores=observed['comparison'], progress=progress)
        refit_seconds = time.perf_counter()-t0
        change = float(average_precision_score(y, fitted['series'])-comparison_pr)
        record = dict(draw=len(records), k=int(k) if k is not None else None,
                      delta_pr_auc=change, real_mask_identical=True,
                      generation_seconds=generation_seconds, preparation_seconds=preparation_seconds,
                      series_only_refit_seconds=refit_seconds, folds=fit_audit)
        if null is not None:
            # Same per-date lag bins/targets as the inherited variogram fitter.
            sv = null.lags.vario(field, real_valid)
            err = np.sqrt(np.nanmean((sv-null.target)**2, axis=1))
            denom = np.nanmean(null.target, axis=1)
            record['variogram_relative_rmse_per_date'] = (err/np.maximum(denom, 1e-12)).tolist()
            record['variogram_relative_rmse_median'] = float(np.nanmedian(err/np.maximum(denom, 1e-12)))
        if diagnostics:
            record['series_diagnostics'] = series_diagnostics(values, smask)
        records.append(record)
    if len(records) != expected_draws or expected_draws < 1:
        raise ValueError(f'Expected {expected_draws} successful temporal draws, got {len(records)}')
    exceedances = sum(r['delta_pr_auc'] >= statistic for r in records)
    result = dict(observed_delta_pr_auc=statistic, comparison_pr_auc=comparison_pr,
                  observed_series_pr_auc=comparison_pr+statistic, draws=records,
                  seed=2037, exceedances=exceedances, p=(1+exceedances)/(1+len(records)),
                  null_setup_seconds=setup_seconds, observed_fit_seconds=observed_seconds,
                  observed_fold_audit=audit)
    if diagnostics:
        result['observed_series_diagnostics'] = series_diagnostics(series, mask)
    return result, observed


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('input', type=Path, help='NPZ: baseline, series, mask, y, block, fold; optional row_id')
    ap.add_argument('output', type=Path, help='OOF NPZ; audit JSON written alongside')
    args = ap.parse_args()
    with np.load(args.input, allow_pickle=False) as a:
        scores, audit = oof_scores(a['baseline'], a['series'], a['mask'], a['y'], a['block'], a['fold'], progress=True)
        np.savez_compressed(args.output, **scores, y=a['y'], block=a['block'], fold=a['fold'],
                            row_id=a['row_id'] if 'row_id' in a.files else np.arange(len(a['y'])))
    args.output.with_suffix('.audit.json').write_text(json.dumps(audit, indent=2, allow_nan=False)+'\n')


if __name__ == '__main__':
    main()
