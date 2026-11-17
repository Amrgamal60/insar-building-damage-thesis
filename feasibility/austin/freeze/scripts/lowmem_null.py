"""Memory-lean variant of nyc_lib.VariogramNull with identical arithmetic (Austin step 0, timing gate).

The NYC class stores the per-window valid-pair mask as a dense float64 (W, P) array and multiplies it in one
call. At Austin's size (88 windows x 15.3 M pairs) that is 10.8 GB, plus a 10.8 GB Fortran-order copy inside
cupyx's sparse matmul, which does not fit in 24 GB. This variant:
- keeps the mask as bool (1 byte per entry) and casts it to float64 inside each window chunk;
- computes the pair counts and the semivariances in chunks of `chunk` windows.
Each window's numbers are computed by the same operations on the same values, so draws are identical.
Everything else (permutation, k grid, smoothing matrices, fitting) is inherited unchanged.
"""
import numpy as np
from scipy.spatial import cKDTree

import nyc_lib as N


class LowMemVariogramNull(N.VariogramNull):
    def __init__(self, fields, xy, res, kmax=1000, max_lag=N.MAX_LAG, chunk=8):
        import cupy as cp
        import cupyx.scipy.sparse as csp
        self.cp, self.chunk = cp, chunk
        self.valid = np.isfinite(fields)
        n = fields.shape[1]
        self.n, self.W = n, len(fields)
        self.mean = np.array([f[v].mean() for f, v in zip(fields, self.valid)])
        med = np.array([np.median(f[v]) for f, v in zip(fields, self.valid)])
        filled = np.where(self.valid, fields, med[:, None])
        self.z = cp.asarray(filled - self.mean[:, None])
        self.lags = N.Lags(xy, res, max_lag)
        self.target = self.lags.vario(fields, self.valid)
        self.ks = np.unique(np.geomspace(2, min(0.9 * n, kmax), 15).astype(int))
        dist, nbr = cKDTree(xy).query(xy, k=int(self.ks.max()) + 1)
        self.W_k = []
        for k in self.ks:
            dk, nk = dist[:, :k + 1], nbr[:, :k + 1]
            w = np.exp(-dk / dk.max(1, keepdims=True))
            w = w / w.sum(1, keepdims=True)
            self.W_k.append(csp.csr_matrix((cp.asarray(w.ravel()), (cp.asarray(np.repeat(np.arange(n), k + 1)),
                                                                     cp.asarray(nk.ravel()))), shape=(n, n)))
        del dist, nbr
        L = self.lags
        self.gi, self.gj = cp.asarray(L.i), cp.asarray(L.j)
        self.H = csp.csr_matrix((cp.ones(len(L.k)), (cp.arange(len(L.k)), cp.asarray(L.k - 1))), shape=(len(L.k), max_lag))
        self.vpb = cp.asarray(self.valid[:, L.i] & self.valid[:, L.j])  # (W, P) bool
        self.cnt = cp.concatenate([(self.H.T @ self.vpb[a:a + chunk].astype(cp.float64).T).T
                                   for a in range(0, self.W, chunk)])

    def _vario(self, S):
        cp, c = self.cp, self.chunk
        out = []
        for a in range(0, self.W, c):
            d = S[a:a + c][:, self.gi] - S[a:a + c][:, self.gj]
            out.append((self.H.T @ (0.5 * d * d * self.vpb[a:a + c].astype(cp.float64)).T).T / self.cnt[a:a + c])
        return cp.concatenate(out)
