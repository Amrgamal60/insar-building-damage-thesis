"""NYC models and inference (NYC_REPLICATION_PLAN.md §8-§12) on one outcome:
  --decoy  §13 step 4: each of the 185 events moved to a random eligible cell of the primary population (the domain,
           250 m; seed 99), keeping its date; at 200 m the decoy cell is the one holding that 250 m cell's centre.
  --real   §13 step 5: the real events. Run once, after the decoy; reruns only to fix code errors (logged).
Every analysis compares Baseline 1 (or 2) + x/y with the same + the window field, on identical rows, with 5 fixed
spatial folds (seed 42), logistic regression (StandardScaler + C = 1) or random forest, as Alexandria's 07 and 09.
- Statistic: change in pooled out-of-fold PR AUC; also ROC AUC, pooled top-10% recall and the share of events whose
  cell ranks in the top 10% of its own risk set (§9, §12.10).
- Primary null: variogram-matching surrogates shared across windows (seed 2027; nyc_lib.VariogramNull); the velocity
  model is refitted on each surrogate; p = (1 + draws with a change >= observed) / (1 + draws). Random forest: the
  first 500 surrogates of the same field.
- Interval: refit block bootstrap of 2 km blocks with all their rows (2,000 for logistic regression, 500 for random
  forest; seed = resample number, as Alexandria's 09).
- Direction (§11): per risk set, the event cell's field value minus its controls' median; the label uses the median
  over risk sets (below 0 = concordant). Raw line-of-sight mm/yr beside it; sign of the field's coefficient in a
  logistic regression fitted on all rows.
- Primary extras: secondary 8 (free and within-block permutation 2,000 each, seeds 10,000 + draw as Alexandria's 09;
  MSR and amplitude-adjusted MSR 999 each, seed 2026 as Alexandria's 10, the amplitude-adjusted one ending with a
  remap to each window's observed values on its valid cells; variogram-matching rank-remapped to each
  window's observed values, the primary surrogates) and secondary 9 (fold maps with seeds 0-9, primary null).
  Shared randomness across windows: one random ordering (or sign vector) per draw is applied to every window, over
  each window's cells with a value; a cell without a value in a window takes the window median for MSR only.
Outputs: out/models/<decoy|real>/ (results.csv, per-analysis null and bootstrap draws, event logs, REPORT.md).
Usage (from feasibility/nyc): ../../.venv/bin/python -I scripts/11_models.py raw out --decoy|--real [--only k1,k2]
  [--jobs 16] [--quick N] [--quick-rf N]  (decoy only: N draws and resamples for the secondary analyses 1-7 and
  11-15, and for the random forest; the primary, secondary 8 and secondary 9 keep their full counts; §14 deviation 2)."""
import argparse
import hashlib
import importlib.util
import json
import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from joblib import Parallel, delayed, parallel_config
from pyproj import Transformer
from scipy.linalg import null_space
from scipy.sparse.csgraph import minimum_spanning_tree
from scipy.spatial.distance import cdist

ap = argparse.ArgumentParser()
ap.add_argument("raw"), ap.add_argument("out")
g = ap.add_mutually_exclusive_group(required=True)
g.add_argument("--decoy", action="store_true"), g.add_argument("--real", action="store_true")
ap.add_argument("--only", default=""), ap.add_argument("--jobs", type=int, default=16), ap.add_argument("--quick", type=int, default=0)
ap.add_argument("--test", type=int, default=0, help="smoke test: N draws everywhere, decoy only, written to out/models/test")
ap.add_argument("--quick-rf", type=int, default=16, help="draws and resamples for the random forest when --quick is set")
ap.add_argument("--surrogates-only", action="store_true",
                help="only build the variogram-matching surrogate files of the selected analyses: no model is fitted")
ARGS = ap.parse_args()
if (ARGS.quick or ARGS.test) and not ARGS.decoy:
    ap.error("--quick and --test are for the decoy only")
RAW, OUT = Path(ARGS.raw), Path(ARGS.out)
CP2, INS = OUT / "checkpoint2", OUT / "insar"
RUN = OUT / "models" / ("test" if ARGS.test else "decoy" if ARGS.decoy else "real")
RUN.mkdir(parents=True, exist_ok=True)
spec = importlib.util.spec_from_file_location("nyc_lib", Path(__file__).resolve().parent / "nyc_lib.py")
N = importlib.util.module_from_spec(spec)
spec.loader.exec_module(N)
LR, RF = N.LR, N.RF
N_SURR, NULL_SEED, DECOY_SEED, MSR_SEED, AA_ITERS = 999, 2027, 99, 2026, 50
N_BOOT = {LR: 2000, RF: 500}
N_NULL = {LR: 999, RF: 500}
N_PERM = 2000
METRICS = ["pr", "roc", "top10", "top10_rs"]
DIRECTIONAL = {"v", "v_linear", "v_nomask"}


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


def real_events():
    ev = pd.read_csv(OUT / "events_final.csv")
    x, y = Transformer.from_crs("EPSG:4326", "EPSG:32618", always_xy=True).transform(ev.geo_lon.values, ev.geo_lat.values)
    return pd.DataFrame({"event_id": ev.event_id, "date": ev.date, "x": x, "y": y})


def decoy_events(ev, cells):
    dom = cells[cells.domain.astype(bool)].reset_index(drop=True)
    pick = np.random.default_rng(DECOY_SEED).integers(0, len(dom), len(ev))
    return ev.assign(x=dom.x.values[pick], y=dom.y.values[pick])


# ---------------------------------------------------------------- fitting helpers (run in workers)
def metrics_of(X, y, fold, rs, kind):
    s = N.oof(X, y, fold, kind)
    return N.metrics(y, s, rs)


def observed_metrics(X, y, fold, rs, kind):
    return N.metrics(y, oof_par(X, y, fold), rs) if kind == RF else metrics_of(X, y, fold, rs, kind)


def null_rep(path, d, wpos, upos, Xb, y, fold, rs, kind, mb):
    s = np.load(path, mmap_mode="r")[d]
    v = np.asarray(s[wpos, upos], float)
    m = metrics_of(np.c_[Xb, v], y, fold, rs, kind)
    return {k: m[k] - mb[k] for k in METRICS}


def field_rep(v, Xb, y, fold, rs, kind, mb):
    m = metrics_of(np.c_[Xb, v], y, fold, rs, kind)
    return {k: m[k] - mb[k] for k in METRICS}


def boot_rep(seed, blocks, Xb, v, y, fold, kind):
    rng = np.random.default_rng(seed)
    ub, code = np.unique(blocks, return_inverse=True)
    order = np.argsort(code, kind="stable")
    members = np.split(order, np.cumsum(np.bincount(code, minlength=len(ub)))[:-1])
    idx = np.concatenate([members[i] for i in rng.choice(len(ub), len(ub), replace=True)])
    yy, ff = y[idx], fold[idx]
    sb, sv = N.oof(Xb[idx], yy, ff, kind), N.oof(np.c_[Xb[idx], v[idx]], yy, ff, kind)
    ok = np.isfinite(sb) & np.isfinite(sv)
    if not 0 < yy[ok].sum() < ok.sum():
        return None
    from sklearn.metrics import average_precision_score, roc_auc_score
    return {"pr": average_precision_score(yy[ok], sv[ok]) - average_precision_score(yy[ok], sb[ok]),
            "roc": roc_auc_score(yy[ok], sv[ok]) - roc_auc_score(yy[ok], sb[ok]),
            "top10": N.recall_top(yy[ok], sv[ok]) - N.recall_top(yy[ok], sb[ok])}


def par(tasks):
    with parallel_config(backend="loky", inner_max_num_threads=1):
        return Parallel(n_jobs=ARGS.jobs)(tasks)


def array_digest(args):
    h = hashlib.sha256()
    for arg in args:
        if isinstance(arg, np.ndarray):
            a = np.ascontiguousarray(arg)
            h.update(str((a.shape, a.dtype.str)).encode())
            h.update(a.tobytes())
    return h.hexdigest()


def expect_arrays(directory, *args):
    path = directory / "input_arrays.sha256"
    expected = array_digest(args)
    if path.exists():
        assert path.read_text() == expected, f"checkpoint inputs changed: {directory}"
    else:
        path.write_text(expected)


def matching_results(a, b):
    if a is None or b is None:
        return a is None and b is None
    return a.keys() == b.keys() and all(np.isfinite(a[k]) and np.isfinite(b[k]) and
                                       abs(a[k] - b[k]) <= 1e-12 for k in a)


def reproducible_rep(function, args, expected):
    observations, records = [], []
    for attempt in range(6):
        assert array_digest(args) == expected, "calculation input arrays changed"
        try:
            result = function(*args)
        except (IndexError, ValueError) as error:
            known = "out of bounds" in str(error) or "neither increasing nor decreasing" in str(error)
            if not known:
                raise
            records.append({"attempt": attempt, "error": repr(error)})
            continue
        assert array_digest(args) == expected, "calculation input arrays changed during execution"
        records.append({"attempt": attempt, "result": result})
        if any(matching_results(old, result) for old in observations):
            return result, records
        observations.append(result)
    raise RuntimeError(f"seeded calculation did not reproduce in six attempts: {records}")


def checkpoint_rep(directory, seed, function, *args):
    """Persist one unchanged seeded calculation, so interrupted batches can resume."""
    path = directory / f"{seed}.json"
    if path.exists():
        saved = json.loads(path.read_text())
        payload = saved["payload"]
        assert hashlib.sha256(payload.encode()).hexdigest() == saved["sha256"], f"damaged checkpoint: {path}"
        value = json.loads(payload)
        assert value["seed"] == seed
        assert value.get("repeat_checked") is True
        return value["result"]
    pending = directory / f"{seed}.running.json"
    pending.write_text(json.dumps({"seed": seed, "pid": os.getpid()}))
    result, attempts = reproducible_rep(function, args, (directory / "input_arrays.sha256").read_text())
    payload = json.dumps({"seed": seed, "result": result, "repeat_checked": True,
                          "attempts": attempts}, sort_keys=True, allow_nan=False)
    saved = {"payload": payload, "sha256": hashlib.sha256(payload.encode()).hexdigest()}
    tmp = path.with_suffix(f".{os.getpid()}.tmp")
    tmp.write_text(json.dumps(saved))
    tmp.replace(path)
    pending.unlink(missing_ok=True)
    return result


def checkpoint_fingerprint(a, arrays, n_null, n_boot):
    h = hashlib.sha256(N.fingerprint(a).encode())
    h.update(json.dumps({"spec": N.SPEC[a["key"]], "null": n_null, "bootstrap": n_boot,
                         "null_seed": NULL_SEED}, sort_keys=True).encode())
    for filename in (__file__, N.__file__):
        h.update(Path(filename).read_bytes())
    for arr in arrays:
        arr = np.ascontiguousarray(arr)
        h.update(str((arr.shape, arr.dtype.str)).encode())
        h.update(arr.tobytes())
    return h.hexdigest()


# ---------------------------------------------------------------- surrogates
SHARED = {"s3": "primary", "s4": "primary", "s11": "primary"}  # same field, windows and union as the primary


def surrogates(a, name, n):
    """The first n variogram-matching surrogates (seed 2027) of a field, cached as float32 .npy with its window ids and
    union cells. Returns (path, row index of each of a's windows in the file, column index of each cell, -1 if absent)."""
    path, meta = RUN / f"surr_{name}.npy", RUN / f"surr_{name}_meta.npz"

    def index():
        m = np.load(meta, allow_pickle=False)
        wpos = pd.Series(np.arange(len(m["wins"])), index=m["wins"]).reindex(a["wins"]).values
        assert not np.isnan(wpos).any(), f"{name} surrogates lack some of {a['key']}'s windows"
        upos = np.full(len(a["upos"]), -1)
        upos[m["U"]] = np.arange(len(m["U"]))
        return path, wpos.astype(int), upos

    if path.exists() and meta.exists():
        s = np.load(path, mmap_mode="r")
        same = name != a["key"] or str(np.load(meta)["fp"]) == N.fingerprint(a)
        if s.shape[0] >= n and same:
            return index()
        log(f"  surrogates {name}: cached file does not match (draws {s.shape[0]}, fingerprint {'same' if same else 'differs'}); regenerating")
    assert name == a["key"], f"{name} surrogates must be made by their own analysis first"
    null = N.VariogramNull(a["null_fields"], a["xy"], a["res"])
    out = np.lib.format.open_memmap(path.with_suffix(".tmp.npy"), mode="w+", dtype=np.float32, shape=(n,) + a["null_fields"].shape)
    ks = []
    for d, (s, k) in enumerate(null.draws(n, np.random.default_rng(NULL_SEED))):
        out[d] = s
        ks.append(k)
        if d % 200 == 0:
            log(f"  surrogates {name}: {d}/{n} (k = {k})")
    out.flush()
    del out
    path.with_suffix(".tmp.npy").rename(path)
    pd.DataFrame({"draw": np.arange(n), "k": ks}).to_csv(RUN / f"surr_{name}_k.csv", index=False)
    N.save_surrogate_meta(meta, a)
    return index()


def perm_fields(F, keys, blocks=None):
    """Shared permutation: per window, its valid cells ordered by key (within block) receive its values in index order."""
    out = np.full_like(F, np.nan)
    for w in range(len(F)):
        v = np.flatnonzero(np.isfinite(F[w]))
        if blocks is None:
            dst = v[np.argsort(keys[v], kind="stable")]
        else:
            src = v[np.lexsort((v, blocks[v]))]
            dst = v[np.lexsort((keys[v], blocks[v]))]
            out[w, dst] = F[w, src]
            continue
        out[w, dst] = F[w, v]
    return out


def msr_draws(F, xy, n, rng, aa=False):
    """MSR (Wagner & Dray 2015, Alexandria's 10) over the union cells, one sign vector per draw for every window."""
    import cupy as cp
    d = cdist(xy, xy)
    t = minimum_spanning_tree(d).toarray().max()
    w = np.where((d > 0) & (d <= t), 1 - (d / (4 * t)) ** 2, 0.0)
    q = null_space(np.ones((1, len(w))))
    lam, u = np.linalg.eigh(q.T @ w @ q)
    basis = cp.asarray(q @ u)
    valid = np.isfinite(F)
    med = np.array([np.median(f[v]) for f, v in zip(F, valid)])
    filled = np.where(valid, F, med[:, None])
    mean = filled.mean(1)
    Z = cp.asarray((filled - mean[:, None]).T)  # (n, W)
    C = basis.T @ Z
    absC = cp.abs(C)
    ordered = cp.sort(cp.asarray(filled.T), axis=0)
    mu = cp.asarray(mean)[None, :]
    for _ in range(n):
        sgn = cp.asarray(rng.choice([-1.0, 1.0], C.shape[0]))
        S = mu + basis @ (sgn[:, None] * C)
        if aa:
            for _ in range(AA_ITERS):
                S = cp.take_along_axis(ordered, cp.argsort(cp.argsort(S, axis=0), axis=0), axis=0)
                cs = basis.T @ (S - mu)
                S = mu + basis @ (cp.sign(cs) * absC)
            yield N.remap(cp.asnumpy(S.T), np.where(valid, F, np.nan))  # last remap: each window's observed values
            continue
        yield np.where(valid, cp.asnumpy(S.T), np.nan)


# ---------------------------------------------------------------- one analysis
def p_value(null, obs):
    null = np.asarray(null)
    return (1 + (null >= obs - 1e-12).sum()) / (1 + len(null))


def run_analysis(key, ctx, events, n_null, n_boot, fold=None, tag=None):
    tag = tag or key
    done = RUN / f"result_{tag}.json"
    if done.exists():
        return json.loads(done.read_text())
    t0 = time.time()
    a = N.prepare(key, ctx, events)
    if ARGS.surrogates_only:
        if SHARED.get(key, key) == key:
            surrogates(a, key, n_null)
            log(f"{tag}: surrogates ready")
        return None
    kind = a["kind"]
    r = a["rows"]
    Xb, v, y, rs = r[a["feats"]].values, r.vel.values, r.y.values.astype(int), r.rs.values
    fold = ctx.fold[r.cell.values] if fold is None else fold[r.cell.values]
    a["log"].to_csv(RUN / f"events_{tag}.csv", index=False)
    # Confirm observed fits before using their statistics in the null comparisons.
    observed_args = (Xb, y, fold, rs, kind)
    mb, _ = reproducible_rep(observed_metrics, observed_args, array_digest(observed_args))
    observed_velocity_args = (np.c_[Xb, v], y, fold, rs, kind)
    mv, _ = reproducible_rep(observed_metrics, observed_velocity_args, array_digest(observed_velocity_args))
    obs = {k: mv[k] - mb[k] for k in METRICS}
    log(f"{tag}: {len(a['sets'])} risk sets, {len(r):,} rows; PR AUC {mb['pr']:.4f} -> {mv['pr']:.4f} ({obs['pr']:+.4f})")
    res = {"key": key, "tag": tag, "label": a["label"], "res": a["res"], "model": kind, "risk_sets": len(a["sets"]),
           "cells_missing_static": a["cells_missing_static"], "rows_missing_age": a["rows_missing_age"],
           "windows": len(a["wins"]), "rows": len(r), "cells": int(r.cell.nunique()), "union_cells": len(a["U"]),
           **{f"{k}_base": mb[k] for k in METRICS}, **{f"{k}_vel": mv[k] for k in METRICS}, **{f"{k}_delta": obs[k] for k in METRICS}}
    fname = N.SPEC[key][6]
    if fname in DIRECTIONAL:
        diff = r.groupby("rs").apply(lambda g_: g_.vel[g_.y == 1].iloc[0] - np.median(g_.vel[g_.y == 0]), include_groups=False)
        res["direction_median"] = float(np.median(diff))
        res["direction_label"] = "concordant" if res["direction_median"] < 0 else "opposite" if res["direction_median"] > 0 else "none"
        res["direction_share_below_0"] = float((diff < 0).mean())
        if a["raw"] is not None:
            raw = a["raw"][r.win.values, r.cell.values]
            rd = pd.DataFrame({"rs": r.rs, "y": r.y, "raw": raw}).groupby("rs").apply(
                lambda g_: g_.raw[g_.y == 1].iloc[0] - np.median(g_.raw[g_.y == 0]), include_groups=False)
            res["direction_raw_mm_yr_median"] = float(np.median(rd))
            res["event_raw_mm_yr_median"] = float(np.median(raw[r.y.values == 1]))
            res["control_raw_mm_yr_median"] = float(np.median(raw[r.y.values == 0]))
        m = N.model(LR).fit(np.c_[Xb, v], y)
        res["coef_field_all_rows"] = float(m[-1].coef_[0, -1])
    # primary null
    path, fw, fu = surrogates(a, SHARED.get(key, key), n_null)
    wpos, upos = fw[r.win.values], fu[r.cell.values]
    assert (upos >= 0).all()
    blocks = np.unique(np.asarray(ctx.cells.block.values, dtype=object), return_inverse=True)[1][r.cell.values]
    fp = checkpoint_fingerprint(a, [Xb, v, y, fold, rs, blocks], n_null, n_boot)
    checkpoint = RUN / "checkpoints" / tag / fp
    null_dir, boot_dir = checkpoint / "null", checkpoint / "bootstrap"
    null_dir.mkdir(parents=True, exist_ok=True)
    boot_dir.mkdir(parents=True, exist_ok=True)
    expect_arrays(null_dir, wpos, upos, Xb, y, fold, rs)
    expect_arrays(boot_dir, blocks, Xb, v, y, fold)
    null_csv, null_meta = RUN / f"null_{tag}.csv", checkpoint / "null_complete.json"
    if null_csv.exists():
        old_null = pd.read_csv(null_csv, float_precision="round_trip")
        valid = len(old_null) == n_null and set(METRICS).issubset(old_null.columns)
        valid = valid and np.isfinite(old_null[METRICS].values).all()
        assert valid, f"incomplete or invalid saved null table: {null_csv}"
        digest = hashlib.sha256(null_csv.read_bytes()).hexdigest()
        checked = json.loads(null_meta.read_text()) if null_meta.exists() else {}
        if checked.get("fingerprint") != fp or checked.get("sha256") != digest:
            draws = np.unique(np.linspace(0, n_null - 1, min(16, n_null), dtype=int)).tolist()
            fresh = pd.DataFrame(par(delayed(checkpoint_rep)(null_dir, d, null_rep, path, d,
                                                             wpos, upos, Xb, y, fold, rs, kind, mb) for d in draws))
            np.testing.assert_allclose(fresh[METRICS].values, old_null.iloc[draws][METRICS].values, rtol=0, atol=1e-12)
            null_meta.write_text(json.dumps({"fingerprint": fp, "sha256": digest, "verified_draws": draws,
                                            "draws": n_null, "absolute_tolerance": 1e-12}, indent=2))
        nd = old_null[METRICS].to_dict("records")
        log(f"{tag}: reused {n_null} saved null draws after integrity/metric checks")
    else:
        nd = par(delayed(checkpoint_rep)(null_dir, d, null_rep, path, d, wpos, upos, Xb, y, fold, rs, kind, mb)
                 for d in range(n_null))
        pd.DataFrame(nd).to_csv(null_csv, index=False)
        null_meta.write_text(json.dumps({"fingerprint": fp, "sha256": hashlib.sha256(null_csv.read_bytes()).hexdigest(),
                                        "generated_draws": n_null}, indent=2))
    for k in METRICS:
        res[f"{k}_p"] = p_value([x[k] for x in nd], obs[k])
        res[f"{k}_null_median"] = float(np.median([x[k] for x in nd]))
    res["null_draws"] = n_null
    # refit block bootstrap
    if n_boot:
        # integer codes in label order (same resamples as the labels): pandas' pyarrow strings arrive corrupted in workers
        bt = [b for b in par(delayed(checkpoint_rep)(boot_dir, s, boot_rep, s, blocks, Xb, v, y, fold, kind)
                            for s in range(n_boot)) if b is not None]
        pd.DataFrame(bt).to_csv(RUN / f"boot_{tag}.csv", index=False)
        for k in ("pr", "roc", "top10"):
            res[f"{k}_ci_lo"], res[f"{k}_ci_hi"] = (float(np.percentile([b[k] for b in bt], q)) for q in (2.5, 97.5))
        res["boot_resamples"] = len(bt)
    res["seconds"] = round(time.time() - t0)
    done.write_text(json.dumps(res, default=float, indent=1))
    log(f"{tag}: p = {res['pr_p']:.3f}; done in {res['seconds']} s")
    return res


def oof_par(X, y, fold):
    """Random forest out-of-fold scores with every core per fit (same result as n_jobs = 1)."""
    from sklearn.ensemble import RandomForestClassifier
    s = np.full(len(y), np.nan)
    for k in range(N.N_FOLDS):
        tr, te = fold != k, fold == k
        if te.any() and y[tr].sum() > 0:
            m = RandomForestClassifier(n_estimators=500, min_samples_leaf=5, max_features="sqrt",
                                       class_weight="balanced_subsample", n_jobs=ARGS.jobs, random_state=0)
            s[te] = m.fit(X[tr], y[tr]).predict_proba(X[te])[:, 1]
    return s


def other_nulls(ctx, events):
    """Secondary 8 on the primary analysis."""
    done = RUN / "result_s8.json"
    if done.exists():
        return json.loads(done.read_text())
    a = N.prepare("primary", ctx, events)
    r = a["rows"]
    Xb, v, y, rs = r[a["feats"]].values, r.vel.values, r.y.values.astype(int), r.rs.values
    fold = ctx.fold[r.cell.values]
    mb = metrics_of(Xb, y, fold, rs, LR)
    obs = metrics_of(np.c_[Xb, v], y, fold, rs, LR)
    obs = {k: obs[k] - mb[k] for k in METRICS}
    F = a["null_fields"]
    wpos, upos = r.win.values, a["upos"][r.cell.values]
    blocks = ctx.cells.block.values[a["U"]]
    out = {}
    n_perm = ARGS.test or N_PERM
    for name, blk in (("Free permutation", None), ("Within-block permutation", blocks)):
        fields = (perm_fields(F, np.random.default_rng(10_000 + d).random(F.shape[1]), blk)[wpos, upos] for d in range(n_perm))
        out[name] = par(delayed(field_rep)(f, Xb, y, fold, rs, LR, mb) for f in fields)
        log(f"s8: {name} done")
    rng = np.random.default_rng(MSR_SEED)
    n_msr = ARGS.test or N_SURR
    for name, aa in (("MSR", False), ("MSR, amplitude-adjusted", True)):
        fields = [s[wpos, upos] for s in msr_draws(F, a["xy"], n_msr, rng, aa=aa)]
        out[name] = par(delayed(field_rep)(f, Xb, y, fold, rs, LR, mb) for f in fields)
        log(f"s8: {name} done")
    path, fw, fu = surrogates(a, "primary", n_msr)
    assert (fw == np.arange(len(fw))).all() and (fu[a["U"]] == np.arange(len(a["U"]))).all()
    S = np.load(path, mmap_mode="r")
    fields = (N.remap(np.asarray(S[d], float), F)[wpos, upos] for d in range(n_msr))
    out["Variogram-matching, observed values"] = par(delayed(field_rep)(f, Xb, y, fold, rs, LR, mb) for f in fields)
    res = {"observed": obs}
    for name, nd in out.items():
        pd.DataFrame(nd).to_csv(RUN / f"null_s8_{name.split(',')[0].replace(' ', '_').lower()}{'_aa' if 'amplitude' in name else ''}{'_remapped' if 'observed' in name else ''}.csv", index=False)
        res[name] = {"draws": len(nd), **{f"{k}_p": p_value([x[k] for x in nd], obs[k]) for k in METRICS},
                     "pr_null_median": float(np.median([x["pr"] for x in nd]))}
    done.write_text(json.dumps(res, default=float, indent=1))
    return res


def main():
    only = set(ARGS.only.split(",")) - {""}
    ctx = {res: N.Context(CP2, INS, RAW, res) for res in (250, 200)}
    events = real_events()
    if ARGS.decoy:
        events = decoy_events(events, ctx[250].cells)
        events.to_csv(RUN / "decoy_events.csv", index=False)
    quick = ARGS.test or ARGS.quick
    order = ["primary", "s8", "s9"] + [k for k in N.SPEC if k not in ("primary", "s3")] + ["s3"]
    for key in order:
        if only and key not in only:
            continue
        if key == "s8" and ARGS.surrogates_only:
            continue
        if key == "s8":
            other_nulls(ctx[250], events)
        elif key == "s9":
            if ARGS.surrogates_only:
                continue
            for sd in range(10):
                fm = N.fold_map(ctx[250].cells, sd)
                run_analysis("primary", ctx[250], events, ARGS.test or N_SURR, 0,
                             fold=ctx[250].cells.block.map(fm).values, tag=f"s9_seed{sd}")
        else:
            kind = N.SPEC[key][7]
            q = (ARGS.test or ARGS.quick_rf) if kind == RF and quick else quick
            n_null = N_NULL[kind] if (key == "primary" and not ARGS.test) or not quick else q
            n_boot = N_BOOT[kind] if (key == "primary" and not ARGS.test) or not quick else q
            run_analysis(key, ctx[N.SPEC[key][2]], events, n_null, n_boot)
    log("ALLDONE")


if __name__ == "__main__":
    main()
