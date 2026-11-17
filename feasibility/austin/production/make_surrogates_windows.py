"""Conditional-null surrogates, and their per-draw window quantiles, for a field whose first windows hold no values
(AUSTIN_PLAN.md §12 items 3 and 9; §15, 2026-11-15). These are the 36-month velocity (no value in the first 12
windows) and the lags 1, 3, 6 and 12 (no value in the first 1, 3, 6 and 12 windows). Those windows hold no study
events: §12 item 3 uses events from 2019-08, and item 9 uses "the events whose window starts on or after the first
granule".

make_surrogates.py stops on these fields, because ConditionalVariogramNull requires that "Every window needs at least
three finite velocities". This script runs the same engine (§10 settings, seed 2027, CPU engine of §14 or frozen GPU
path) on the windows that have values. Each draw is then written at full shape (draws, 88, P_null), with NaN in the
empty windows, under the fingerprint of the full field, so SurrogateStore and run_tests.py read the file like any
other.

Why the windows that have values get the same arithmetic as before:
  - the frozen generator makes exactly two calls per draw, rng.permutation(n) and rng.standard_normal(n), where n is
    the number of null pixels (parallel_draws.py), so leaving windows out does not change the random stream;
  - the conditional fits are made window by window (conditional_null.py), on covariates that are the same in every
    window (§10).
Checked by check_surr_windows.py: the first 12 windows of the primary field are blanked, and draws 0-2 must equal the
primary file's draws in windows 12-87 in every draw whose neighbour count is unchanged.

  make       arguments as make_surrogates.py (plus --draws for checks)
  quantiles  arguments as planted_signal.py quantiles. testa_core.surrogate_quantiles is applied to the windows that
             have values, and the empty windows get NaN (a percentile has no value there).
"""
import os

for _name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMBA_NUM_THREADS"):
    os.environ[_name] = "1"
import argparse  # noqa: E402
import json  # noqa: E402
import multiprocessing as mp  # noqa: E402
import platform  # noqa: E402
import resource  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402
from concurrent.futures import ProcessPoolExecutor  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import make_surrogates as MS  # noqa: E402  (puts planted_signal/ and the frozen scripts on the path)
from make_surrogates import C, PS, ParallelDraws  # noqa: E402

CTX = {}


def kept_windows(v_null):
    """Windows with at least one value. The empty ones must be the leading windows, as in the fields of §12.3/§12.9."""
    keep = np.isfinite(v_null).any(axis=1)
    first = int(np.argmax(keep))
    assert keep.any() and keep[first:].all() and not keep[:first].any(), "empty windows are not all leading"
    return keep


class FullWindows:
    """draws(n, rng) -> (field, k) of an engine run on the kept windows, returned at full window shape."""

    def __init__(self, runner, keep):
        self.runner, self.keep = runner, keep

    def draws(self, n_draws, rng):
        for s, k in self.runner.draws(n_draws, rng):
            full = np.full((len(self.keep), s.shape[1]), np.nan)
            full[self.keep] = s
            yield full, k


def source_hashes():
    out = MS.source_hashes()
    out["production/make_surrogates_windows.py"] = C.sha256(HERE / "make_surrogates_windows.py")
    return out


def cmd_make(a):
    t0 = time.perf_counter()
    inputs = PS.checkpoint1_inputs(a)
    h = C.load_houses(a.features, a.grid, a.episodes, a.censoring)
    geo = C.Geometry(h)
    v_null = C.load_field(a.field, geo)[:, geo.null_pixels]
    fp = C.null_fingerprint(v_null, geo)
    keep = kept_windows(v_null)
    cov = C.null_covariates(h, geo)
    engine = MS.build_engine(v_null[keep], geo, cov, a.backend, C.NULL_SETTINGS)
    setup = time.perf_counter() - t0
    runner = ParallelDraws(engine, a.workers) if a.backend == "cpu" and a.workers > 1 else engine
    t1 = time.perf_counter()
    meta = C.write_surrogates(a.out, FullWindows(runner, keep), a.draws, C.NULL_SEED, fp, v_null.shape)
    info = dict(backend=a.backend, workers=a.workers, draws=a.draws, seed=C.NULL_SEED, settings=C.NULL_SETTINGS,
                field_sha256=C.sha256(a.field), fingerprint=fp, inputs=inputs, surrogates_sha256=meta["sha256"],
                empty_windows=int((~keep).sum()), first_window_with_values=C.MONTHS[int(np.argmax(keep))],
                chosen_k=meta["chosen_k"], explained_variance=[float(x) for x in engine.explained_variance],
                setup_seconds=setup, draw_seconds=time.perf_counter() - t1,
                peak_rss_gb_parent=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6,
                peak_rss_gb_largest_worker=resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss / 1e6,
                host=platform.node(), python=platform.python_version(), numpy=np.__version__,
                sources=source_hashes(), finished=time.strftime("%Y-%m-%d %H:%M:%S %Z"))
    Path(str(a.out) + ".run.json").write_text(json.dumps(info, indent=1) + "\n")
    print(json.dumps({k: v for k, v in info.items() if k != "chosen_k"}, indent=1))


def _quantiles_of(d):
    S = CTX["store"].draw(d)
    keep = CTX["keep"]
    q = np.full((len(C.QS), S.shape[0]), np.nan)
    q[:, keep] = C.surrogate_quantiles(S[keep], CTX["geo"])
    return d, q


def cmd_quantiles(a):
    PS.checkpoint1_inputs(a)
    h = C.load_houses(a.features, a.grid, a.episodes, a.censoring)
    geo = C.Geometry(h)
    v_null = C.load_field(a.field, geo)[:, geo.null_pixels]
    store = C.SurrogateStore(a.surrogates, C.null_fingerprint(v_null, geo), check_hash=True)
    CTX.update(store=store, geo=geo, keep=kept_windows(v_null))
    q = np.empty((store.draws, len(C.QS), len(C.MONTHS)))
    with ProcessPoolExecutor(a.workers, mp_context=mp.get_context("fork")) as ex:
        for d, qd in ex.map(_quantiles_of, range(store.draws), chunksize=4):
            q[d] = qd
    np.save(a.out, q)
    meta = dict(sha256=C.sha256(a.out), surrogates_sha256=store.meta["sha256"], fingerprint=store.meta["fingerprint"],
                shape=list(q.shape), percentiles=C.QS, empty_windows=int((~CTX["keep"]).sum()),
                sources=source_hashes())
    Path(str(a.out) + ".json").write_text(json.dumps(meta, indent=1) + "\n")
    print(json.dumps(meta, indent=1))


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="command", required=True)
    for name in ("make", "quantiles"):
        s = sub.add_parser(name)
        for k in ("features", "grid", "episodes", "censoring", "field", "out"):
            s.add_argument(f"--{k}", type=Path, required=True)
        s.add_argument("--workers", type=int, default=1)
        if name == "make":
            s.add_argument("--backend", choices=("cpu", "gpu"), required=True)
            s.add_argument("--draws", type=int, default=C.NULL_DRAWS, help="999 (frozen); fewer only for checks")
        else:
            s.add_argument("--surrogates", type=Path, required=True)
    a = p.parse_args(argv)
    {"make": cmd_make, "quantiles": cmd_quantiles}[a.command](a)


if __name__ == "__main__":
    main()
