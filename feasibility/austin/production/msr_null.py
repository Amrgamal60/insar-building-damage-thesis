"""MSR null for Test A secondary 8 (AUSTIN_PLAN.md §12 item 8: "MSR (999)"), as NYC's 11_models.msr_draws (Wagner &
Dray 2015, Alexandria's 10), seed 2026, non-amplitude-adjusted, on the Test A null field (88 windows x the null
pixels). The user chose on 2026-11-12 to time it first and then decide within the §13.6 secondary budget (§15).
Outcome-blind: reads the field and pixel positions only.

NYC's arithmetic, kept: threshold t = longest edge of the minimum spanning tree of the pixel centres; weights
w_ij = 1 - (d_ij / 4t)^2 for 0 < d_ij <= t, else 0; q an orthonormal basis of the complement of the constant vector;
(lam, u) = eigh(q' w q) (LAPACK ?syevd, as numpy and cupy); basis = q u; each window filled with its median where it
has no value and centred on its mean; C = basis' Z; per draw one sign vector sgn = rng.choice([-1., 1.], n - 1) for
every window (rng = default_rng(2026), draws in order), S = mean + basis (sgn * C), NaN where the window has no value.

Changes needed at this size (n ~ 107,000: NYC's dense code holds several n x n arrays at once). Each is exact in
arithmetic or in exact mathematics, and the `check` command compares it with NYC's dense code on a subset:
  - t from the minimum spanning tree of the Delaunay edges (a Euclidean minimum spanning tree lies in the Delaunay
    graph, and every minimum spanning tree has the same longest edge); verified on the full set by connectivity:
    pairs closer than t(1 + 1e-9) connect all pixels and pairs closer than t(1 - 1e-9) do not;
  - w built in column blocks with cdist and NYC's expression (identical values);
  - q = columns 2..n of the Householder reflector H = I - 2 v v'/(v'v), v = 1 + sqrt(n) e1, in place of scipy's
    null_space (an SVD of a 1 x n matrix). Any orthonormal q gives the same eigenvalues and the same eigenvectors q u up
    to sign (and to rotation inside a repeated eigenvalue); a sign change flips C's matching row too, so the draws do not
    change. q' w q = (H w H)[1:, 1:] is formed in place; with v[1:] = 1 its entries are
    w_ik - (2/c)(wv_i + wv_k) + 4 v'wv / c^2, c = v'v, wv = w v;
  - eigh by LAPACK dsyevd from numpy's own 64-bit-integer OpenBLAS (numpy.linalg.eigh calls the same routine but copies
    the matrix twice; scipy's 32-bit-integer LAPACK overflows the 2n^2 workspace size), in place, so the matrix
    becomes its eigenvectors; basis = q u is then formed in the same buffer (one row down, the first row added);
  - draws computed 16 at a time by one matrix product (same sign vectors, same order).
Peak memory ~ 3 n^2 doubles during eigh (matrix + 2 n^2 workspace), n^2 after.

Commands
  check   on a random subset of null pixels (default 1,500): NYC's dense code (copied below, numpy for cupy) against
          this class: threshold, weights, eigenvalues, eigenvectors of separated eigenvalues, orthonormality, NaN
          pattern, and the draws' components along separated eigenvectors (whole draws are compared for information
          only: eigenvectors of near-equal eigenvalues are not unique, and no two eigensolvers return the same ones).
  timing  stage times and peak memory on subsets (one process each), projected to the full field (eigh ~ n^3;
          weights, H w H, basis, coefficients and the per-draw product ~ n^2; memory 3 n^2 doubles).
  make    the 999 MSR fields (seed 2026) in the testa_core surrogate format, for planted_signal.py quantiles and
          run_tests.py testa (as null (a)).
Usage: python -I msr_null.py check|timing|make --features F --grid G --episodes E --censoring C --field FIELD.npz
           --out OUT [--threads 32] [--n 1500] [--sizes 10000 20000 30000]
"""
import argparse
import ctypes
import glob
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components, minimum_spanning_tree
from scipy.spatial import Delaunay, cKDTree
from scipy.spatial.distance import cdist

HERE = Path(__file__).resolve().parent
PS_DIR = HERE.parent / "planted_signal"
sys.path[:0] = [str(HERE), str(PS_DIR)]
import testa_core as C  # noqa: E402
import planted_signal as PS  # noqa: E402  (checkpoint-1 input hash check)

MSR_SEED, MSR_DRAWS, BLOCK, DRAW_BATCH = 2026, 999, 2048, 16


def _status(field):
    with open("/proc/self/status") as f:
        for line in f:
            if line.startswith(field + ":"):
                return int(line.split()[1]) / 1e6


def peak_gb():
    return _status("VmHWM")


def now_gb():
    return _status("VmRSS")


# ---------------------------------------------------------------- LAPACK dsyevd, 64-bit integers, numpy's OpenBLAS
def _openblas64():
    libs = glob.glob(str(Path(np.__file__).resolve().parent.parent / "numpy.libs" / "libscipy_openblas64_*.so"))
    assert len(libs) == 1, libs
    return ctypes.CDLL(libs[0])


def dsyevd_inplace(a, n, lda):
    """Eigen-decomposition of the symmetric n x n matrix in the leading part of the Fortran-ordered buffer `a`
    (leading dimension lda); `a` is overwritten by the eigenvectors (columns). Returns the eigenvalues, ascending."""
    assert a.dtype == np.float64 and a.flags.f_contiguous and a.shape[0] == lda and a.shape[1] >= n
    f = _openblas64().scipy_dsyevd_64_
    i64, P = ctypes.c_int64, ctypes.POINTER
    f.argtypes = [ctypes.c_char_p, ctypes.c_char_p, P(i64), P(ctypes.c_double), P(i64), P(ctypes.c_double),
                  P(ctypes.c_double), P(i64), P(i64), P(i64), P(i64), ctypes.c_size_t, ctypes.c_size_t]
    f.restype = None
    w = np.empty(n)
    lwork, liwork = 1 + 6 * n + 2 * n * n, 3 + 5 * n
    work = np.empty(lwork)
    iwork = np.empty(liwork, dtype=np.int64)
    info = i64(0)
    dp = lambda x: x.ctypes.data_as(P(ctypes.c_double))  # noqa: E731
    f(b"V", b"L", ctypes.byref(i64(n)), dp(a), ctypes.byref(i64(lda)), dp(w), dp(work), ctypes.byref(i64(lwork)),
      iwork.ctypes.data_as(P(i64)), ctypes.byref(i64(liwork)), ctypes.byref(info), 1, 1)
    del work, iwork
    assert info.value == 0, f"dsyevd info={info.value}"
    return w


# ---------------------------------------------------------------- threshold
def emst_threshold(xy):
    """Longest edge of a minimum spanning tree of the points, from their Delaunay edges, measured as cdist does."""
    s = Delaunay(xy).simplices
    e = np.unique(np.sort(np.r_[s[:, [0, 1]], s[:, [1, 2]], s[:, [0, 2]]], axis=1), axis=0)
    d = np.sqrt(((xy[e[:, 0]] - xy[e[:, 1]]) ** 2).sum(1))
    g = coo_matrix((d, (e[:, 0], e[:, 1])), shape=(len(xy), len(xy))).tocsr()
    m = minimum_spanning_tree(g).tocoo()
    assert m.nnz == len(xy) - 1, "the points do not form one connected tree"
    k = int(np.argmax(m.data))
    return float(cdist(xy[[m.row[k]]], xy[[m.col[k]]])[0, 0])


def threshold_verified(xy, t):
    """Pairs closer than t(1+1e-9) connect all points; pairs closer than t(1-1e-9) do not."""
    tree, n = cKDTree(xy), len(xy)

    def parts(r):
        p = tree.query_pairs(r, output_type="ndarray")
        g = coo_matrix((np.ones(len(p)), (p[:, 0], p[:, 1])), shape=(n, n))
        return connected_components(g, directed=False)[0]

    return bool(parts(t * (1 + 1e-9)) == 1 and parts(t * (1 - 1e-9)) > 1)


# ---------------------------------------------------------------- the engine
class MSR:
    """draws(n_draws, rng) -> (W x n field, 0), the testa_core engine interface."""

    def __init__(self, F, xy):
        T = {}
        n = len(xy)
        self.n = n
        v = np.ones(n)
        v[0] += np.sqrt(n)
        t0 = time.perf_counter()
        self.t = emst_threshold(xy)
        self.t_verified = threshold_verified(xy, self.t)
        T["threshold"] = time.perf_counter() - t0
        # weights: buf (n x n-1, Fortran order); its first n-1 rows hold w[1:, 1:], column k = pixel k+1
        t0 = time.perf_counter()
        wfun = lambda d: np.where((d > 0) & (d <= self.t), 1 - (d / (4 * self.t)) ** 2, 0.0)  # noqa: E731
        buf = np.empty((n, n - 1), order="F")
        wv = np.empty(n)
        wv[0] = wfun(cdist(xy[:1], xy))[0] @ v
        for a in range(1, n, BLOCK):
            wb = wfun(cdist(xy[a:a + BLOCK], xy))
            wv[a:a + BLOCK] = wb @ v
            buf[:n - 1, a - 1:a - 1 + BLOCK] = wb[:, 1:].T
        del wb
        T["weights"] = time.perf_counter() - t0
        # q' w q = (H w H)[1:, 1:] in place
        t0 = time.perf_counter()
        c = float(v @ v)
        vwv = float(v @ wv)
        wv1 = wv[1:]
        for a in range(0, n - 1, BLOCK):
            buf[:n - 1, a:a + BLOCK] += -(2 / c) * (wv1[:, None] + wv1[None, a:a + BLOCK]) + 4 * vwv / c ** 2
        T["householder"] = time.perf_counter() - t0
        # eigh in place: buf[:n-1] becomes u (columns)
        t0 = time.perf_counter()
        self.lam = dsyevd_inplace(buf, n - 1, n)
        T["eigh"] = time.perf_counter() - t0
        T["peak_gb_after_eigh"] = peak_gb()
        # basis = H[:, 1:] u: row 0 = -(2/c) v0 r', rows 1.. = u - (2/c) r' (v[1:] = 1), r = u' v[1:]
        t0 = time.perf_counter()
        for a in range(0, n - 1, BLOCK):
            blk = buf[:n - 1, a:a + BLOCK]
            r = blk.sum(0)
            col = np.empty((n, blk.shape[1]))
            col[0] = -(2 / c) * v[0] * r
            col[1:] = blk - (2 / c) * r[None, :]
            buf[:, a:a + BLOCK] = col
        del col
        self.basis = buf
        T["basis"] = time.perf_counter() - t0
        # coefficients
        t0 = time.perf_counter()
        self.valid = np.isfinite(F)
        med = np.array([np.median(f[m]) for f, m in zip(F, self.valid)])
        filled = np.where(self.valid, F, med[:, None])
        self.mean = filled.mean(1)
        self.C = self.basis.T @ (filled - self.mean[:, None]).T
        T["coefficients"] = time.perf_counter() - t0
        self.times = T

    def verify(self, xy, k=200, seed=0):
        """Eigen-residual and orthonormality on k random basis columns, with w rebuilt in row blocks (the matrix
        itself was overwritten): P w b_j = lam_j b_j (P = I - 11'/n, as b_j is orthogonal to the constant), b'b = I."""
        n = self.n
        cols = np.sort(np.random.default_rng(seed).choice(n - 1, min(k, n - 1), replace=False))
        B = np.ascontiguousarray(self.basis[:, cols])
        WB = np.empty((n, len(cols)))
        for a in range(0, n, BLOCK):
            d = cdist(xy[a:a + BLOCK], xy)
            WB[a:a + BLOCK] = np.where((d > 0) & (d <= self.t), 1 - (d / (4 * self.t)) ** 2, 0.0) @ B
        res = np.abs((WB - WB.mean(0)) - B * self.lam[cols]).max() / np.abs(self.lam).max()
        G = self.basis.T @ B
        G[cols, np.arange(len(cols))] -= 1.0
        return dict(columns=len(cols), eigen_residual_rel=float(res), orthonormal_max_err=float(np.abs(G).max()),
                    orthogonal_to_constant_max=float(np.abs(B.sum(0)).max()))

    def draws(self, n_draws, rng):
        mu = self.mean[None, :]
        m, W = self.C.shape
        done = 0
        while done < n_draws:
            k = min(DRAW_BATCH, n_draws - done)
            sg = [rng.choice([-1.0, 1.0], m) for _ in range(k)]
            S = self.basis @ np.concatenate([s[:, None] * self.C for s in sg], axis=1)
            for j in range(k):
                yield np.where(self.valid, (mu + S[:, j * W:(j + 1) * W]).T, np.nan), 0
            done += k


def nyc_msr_draws(F, xy, n, rng):
    """NYC 11_models.msr_draws (aa=False), unchanged except numpy in place of cupy."""
    from scipy.linalg import null_space
    d = cdist(xy, xy)
    t = minimum_spanning_tree(d).toarray().max()
    w = np.where((d > 0) & (d <= t), 1 - (d / (4 * t)) ** 2, 0.0)
    q = null_space(np.ones((1, len(w))))
    lam, u = np.linalg.eigh(q.T @ w @ q)
    basis = q @ u
    valid = np.isfinite(F)
    med = np.array([np.median(f[v]) for f, v in zip(F, valid)])
    filled = np.where(valid, F, med[:, None])
    mean = filled.mean(1)
    Z = filled - mean[:, None]
    Z = Z.T
    Cc = basis.T @ Z
    mu = mean[None, :]
    out = []
    for _ in range(n):
        sgn = rng.choice([-1.0, 1.0], Cc.shape[0])
        S = mu + basis @ (sgn[:, None] * Cc)
        out.append(np.where(valid, S.T, np.nan))
    return dict(t=t, w=w, lam=lam, basis=basis, draws=out)


# ---------------------------------------------------------------- commands
def load(a):
    inputs = PS.checkpoint1_inputs(a)
    h = C.load_houses(a.features, a.grid, a.episodes, a.censoring)
    geo = C.Geometry(h)
    v_null = C.load_field(a.field, geo)[:, geo.null_pixels]
    return inputs, geo, v_null, geo.null_xy()


def subset(v_null, xy, n, seed=0):
    k = np.sort(np.random.default_rng(seed).choice(xy.shape[0], n, replace=False))
    return v_null[:, k], xy[k]


def cmd_check(a):
    from threadpoolctl import threadpool_limits
    _, geo, v_null, xy = load(a)
    F, P = subset(v_null, xy, a.n)
    Ff = np.where(np.isfinite(F), F, np.nanmedian(F, axis=1)[:, None])  # no NaN: whole draws comparable
    nd = 5
    with threadpool_limits(a.threads):
        ref = nyc_msr_draws(F, P, nd, np.random.default_rng(MSR_SEED))
        ref_f = nyc_msr_draws(Ff, P, nd, np.random.default_rng(MSR_SEED))
        m = MSR(F, P)
        ours = [s for s, _ in m.draws(nd, np.random.default_rng(MSR_SEED))]
        m_f = MSR(Ff, P)
        ours_f = [s for s, _ in m_f.draws(nd, np.random.default_rng(MSR_SEED))]
    n = len(P)
    w = np.empty((n, n))
    for i in range(0, n, BLOCK):
        d = cdist(P[i:i + BLOCK], P)
        w[i:i + BLOCK] = np.where((d > 0) & (d <= m.t), 1 - (d / (4 * m.t)) ** 2, 0.0)
    lam_scale = float(np.max(np.abs(ref["lam"])))
    gap = np.diff(ref["lam"]) / lam_scale
    iso = np.r_[gap[0] >= 1e-6, (gap[:-1] >= 1e-6) & (gap[1:] >= 1e-6), gap[-1] >= 1e-6]
    cos = np.abs(np.sum(ref["basis"] * m.basis, axis=0))
    G = m.basis.T @ m.basis
    B = ref["basis"][:, iso]
    sep = [float(np.max(np.abs((x - y) @ B))) for x, y in zip(ref_f["draws"], ours_f)]
    sd = float(np.nanstd(F))
    R = dict(n=n, threshold_nyc=float(ref["t"]), threshold_ours=m.t, threshold_equal=bool(ref["t"] == m.t),
             threshold_verified=m.t_verified, weights_equal=bool(np.array_equal(ref["w"], w)),
             eigenvalues_max_abs_diff_rel=float(np.max(np.abs(ref["lam"] - m.lam)) / lam_scale),
             separated_eigenvalues=int(iso.sum()), separated_min_abs_cos=float(cos[iso].min()),
             basis_orthonormal_max_err=float(np.max(np.abs(G - np.eye(n - 1)))),
             basis_orthogonal_to_constant_max=float(np.max(np.abs(m.basis.sum(0)))),
             draws_nan_pattern_equal_nyc=all(bool(np.array_equal(np.isnan(x), np.isnan(y))) for x, y in zip(ref["draws"], ours)),
             draws_separated_components_max_diff=max(sep), field_sd=sd, verify=m.verify(P),
             draws_max_abs_diff_vs_nyc_information=[float(np.nanmax(np.abs(x - y))) for x, y in zip(ref["draws"], ours)],
             draws_window_mean_diff_information=[float(np.max(np.abs(np.nanmean(x, 1) - np.nanmean(y, 1)))) for x, y in zip(ref["draws"], ours)])
    R["pass"] = bool(R["threshold_equal"] and R["threshold_verified"] and R["weights_equal"]
                     and R["eigenvalues_max_abs_diff_rel"] <= 1e-10 and R["separated_min_abs_cos"] >= 1 - 1e-8
                     and R["basis_orthonormal_max_err"] <= 1e-10 and R["basis_orthogonal_to_constant_max"] <= 1e-10
                     and R["draws_nan_pattern_equal_nyc"] and R["draws_separated_components_max_diff"] <= 1e-6 * max(1.0, sd)
                     and R["verify"]["eigen_residual_rel"] <= 1e-8 and R["verify"]["orthonormal_max_err"] <= 1e-8)
    Path(a.out).write_text(json.dumps(R, indent=1) + "\n")
    print(json.dumps(R, indent=1))


def cmd_timing_one(a):
    from threadpoolctl import threadpool_limits
    _, geo, v_null, xy = load(a)
    F, P = subset(v_null, xy, a.n)
    base = now_gb()
    with threadpool_limits(a.threads):
        t0 = time.perf_counter()
        m = MSR(F, P)
        build = time.perf_counter() - t0
        t0 = time.perf_counter()
        for _ in m.draws(DRAW_BATCH, np.random.default_rng(MSR_SEED)):
            pass
        per_draw = (time.perf_counter() - t0) / DRAW_BATCH
    print(json.dumps(dict(n=a.n, threads=a.threads, threshold_m=m.t, threshold_verified=m.t_verified, stages=m.times,
                          build_seconds=build, seconds_per_draw=per_draw, peak_gb=peak_gb(), rss_gb_before=base,
                          load_average=os.getloadavg())))


def cmd_timing(a):
    rows = []
    for n in a.sizes:
        cmd = [sys.executable, "-I", str(Path(__file__).resolve()), "timing-one", "--n", str(n), "--threads", str(a.threads)]
        for k in ("features", "grid", "episodes", "censoring", "field"):
            cmd += [f"--{k}", str(getattr(a, k))]
        out = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout.strip().splitlines()[-1]
        rows.append(json.loads(out))
        print(out, flush=True)
    N = len(load(a)[3])
    big = rows[-1]
    s = big["stages"]
    f3, f2 = (N / big["n"]) ** 3, (N / big["n"]) ** 2
    proj = dict(full_pixels=N, from_n=big["n"], threads=a.threads,
                eigh_hours=s["eigh"] * f3 / 3600,
                other_build_hours=(s["householder"] + s["basis"] + s["weights"] + s["coefficients"]) * f2 / 3600
                + s["threshold"] / 3600,
                draws_hours=big["seconds_per_draw"] * f2 * MSR_DRAWS / 3600,
                peak_memory_gb=3 * N * N * 8 / 1e9 + max(0.0, big["peak_gb"] - 3 * big["n"] ** 2 * 8 / 1e9),
                surrogate_file_gb=MSR_DRAWS * 88 * N * 4 / 1e9,
                scaling="eigh ~ n^3; weights, H w H, basis, coefficients and the per-draw product ~ n^2; "
                        "memory 3 n^2 doubles during eigh; threshold time not scaled (full-set threshold differs)")
    proj["total_hours"] = proj["eigh_hours"] + proj["other_build_hours"] + proj["draws_hours"]
    R = dict(rows=rows, projection=proj, host=platform.node(), finished=time.strftime("%Y-%m-%d %H:%M:%S %Z"))
    Path(a.out).write_text(json.dumps(R, indent=1) + "\n")
    print(json.dumps(proj, indent=1))


def cmd_make(a):
    from threadpoolctl import threadpool_limits
    inputs, geo, v_null, xy = load(a)
    fp = C.null_fingerprint(v_null, geo)
    t0 = time.perf_counter()
    with threadpool_limits(a.threads):
        m = MSR(v_null, xy)
        assert m.t_verified
        build = time.perf_counter() - t0
        ver = m.verify(xy)
        print(json.dumps(dict(threshold_m=m.t, stages=m.times, verify=ver)), flush=True)
        assert ver["eigen_residual_rel"] <= 1e-8 and ver["orthonormal_max_err"] <= 1e-8 \
            and ver["orthogonal_to_constant_max"] <= 1e-8, ver
        meta = C.write_surrogates(a.out, m, MSR_DRAWS, MSR_SEED, fp, v_null.shape)
    info = dict(null="MSR (secondary 8)", seed=MSR_SEED, draws=MSR_DRAWS, threshold_m=m.t, stages=m.times, verify=ver,
                build_seconds=build, total_seconds=time.perf_counter() - t0, peak_gb=peak_gb(), threads=a.threads,
                fingerprint=fp, inputs=inputs, field_sha256=C.sha256(a.field), surrogates_sha256=meta["sha256"],
                source_sha256=C.sha256(Path(__file__).resolve()), host=platform.node(),
                finished=time.strftime("%Y-%m-%d %H:%M:%S %Z"))
    Path(str(a.out) + ".run.json").write_text(json.dumps(info, indent=1) + "\n")
    print(json.dumps(info, indent=1))


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    for name in ("check", "timing", "timing-one", "make"):
        s = sub.add_parser(name)
        for k in ("features", "grid", "episodes", "censoring", "field"):
            s.add_argument(f"--{k}", type=Path, required=True)
        s.add_argument("--threads", type=int, default=32)
        if name != "timing-one":
            s.add_argument("--out", type=Path, required=True)
        if name in ("check", "timing-one"):
            s.add_argument("--n", type=int, default=1500)
        if name == "timing":
            s.add_argument("--sizes", type=int, nargs="+", default=[10000, 20000, 30000])
    a = p.parse_args(argv)
    {"check": cmd_check, "timing": cmd_timing, "timing-one": cmd_timing_one, "make": cmd_make}[a.cmd](a)


if __name__ == "__main__":
    main()
