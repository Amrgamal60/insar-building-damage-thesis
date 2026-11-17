"""CPU initialization of LowMemVariogramNull, preserving its draw/_vario code.

Only device/CSR allocation differs: NumPy and SciPy replace CuPy and cupyx. The
unchanged LowMemVariogramNull._vario and VariogramNull.draws are inherited.
Arithmetic equality is verified against the actual GPU implementation before
calibration. This adapter is local to synthetic calibration, not a source edit.
"""
from types import SimpleNamespace
import numpy as np
import scipy.sparse as csp
from scipy.spatial import cKDTree
import nyc_lib as N
from lowmem_null import LowMemVariogramNull


class CPULowMemVariogramNull(LowMemVariogramNull):
    def __init__(self, fields, xy, res, kmax=1000, max_lag=N.MAX_LAG, chunk=8):
        cp = SimpleNamespace(asarray=np.asarray, asnumpy=np.asarray, ones=np.ones,
                             arange=np.arange, concatenate=np.concatenate, float64=np.float64)
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
        self.ks = np.unique(np.geomspace(2, min(0.9*n, kmax), 15).astype(int))
        dist, nbr = cKDTree(xy).query(xy, k=int(self.ks.max())+1)
        self.W_k = []
        for k in self.ks:
            dk, nk = dist[:, :k+1], nbr[:, :k+1]
            w = np.exp(-dk / dk.max(1, keepdims=True))
            w = w / w.sum(1, keepdims=True)
            self.W_k.append(csp.csr_matrix((cp.asarray(w.ravel()),
                (cp.asarray(np.repeat(np.arange(n), k+1)), cp.asarray(nk.ravel()))), shape=(n, n)))
        L = self.lags
        self.gi, self.gj = cp.asarray(L.i), cp.asarray(L.j)
        self.H = csp.csr_matrix((cp.ones(len(L.k)),
            (cp.arange(len(L.k)), cp.asarray(L.k-1))), shape=(len(L.k), max_lag))
        self.vpb = cp.asarray(self.valid[:, L.i] & self.valid[:, L.j])
        self.cnt = cp.concatenate([(self.H.T @ self.vpb[a:a+chunk].astype(cp.float64).T).T
                                  for a in range(0, self.W, chunk)])
