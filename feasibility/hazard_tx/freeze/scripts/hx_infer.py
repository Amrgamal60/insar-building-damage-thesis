"""Inference for HAZARD_TX models whose nuisance part is block-diagonal by city (HAZARD_TX_PLAN.md §7, §10).

Model: log E[y] = offset + Z_c a_c (+ fixed effects of city c) + beta * x, for every city c; one common beta.
With beta fixed, the model separates by city, so every restricted fit is a set of per-city fits. This module computes
the values of oa_core.infer (r1-r4: estimate, one-sided p, 90%/95% intervals by inverting the wild cluster score test
over oa_core.GRID with oa_core.webb_weights drawn as infer draws them) using that structure:
- restricted fits per city, warm-started from the previous grid point (the fits converge to the same maximum; values
  agree with oa_core.infer to the convergence tolerance, checked by `check_against_oa` in run_ht.py; a p-value can
  differ by one draw only at an exact tie of a bootstrap statistic with the observed one, which needs a constant
  weight vector: probability 6 / 6^G per draw, negligible for the 33 blocks of r4);
- the full fit by Newton on beta over the profile (per-city restricted fits at each beta);
- optional per-city fixed effects (secondary 6) concentrated out of each city's fit (profile Newton; the efficient
  residual of x is taken within groups), equal to the dummy-variable fit (checked in `selftest`).
r1 (CR1 Wald, 2 km) uses oa_core.cr1 on the full design (fixed effects not supported for r1).
Clusters never cross cities (blocks are city-specific), so cluster sums of the efficient score are the same whether
computed per city or pooled.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ht_core as H  # noqa: E402

C = H.C


def _fit_fe(Z, g, y, off, b_init=None, tol=1e-10, maxit=100):
    """Poisson with group fixed effects g (codes 0..G-1, each group with y > 0) concentrated out.
    Returns b, mu, Hp (profile Hessian: within-group, mu-weighted) and the group-mean function."""
    G = int(g.max()) + 1
    Yg = np.bincount(g, weights=y, minlength=G)
    assert (Yg > 0).all(), "a fixed-effect group without events"
    b = np.zeros(Z.shape[1]) if b_init is None else np.array(b_init, float)

    def state(bb):
        e0 = off + Z @ bb
        m = e0.max()
        S = np.bincount(g, weights=np.exp(e0 - m), minlength=G)
        alpha = np.log(Yg) - np.log(S) - m
        eta = e0 + alpha[g]
        return eta, float(np.sum(y * eta - np.exp(eta)))

    def within(mu):
        w = np.bincount(g, weights=mu, minlength=G)
        return lambda A: A - (np.stack([np.bincount(g, weights=mu * A[:, j], minlength=G) for j in range(A.shape[1])], 1) / w[:, None])[g] \
            if A.ndim == 2 else A - (np.bincount(g, weights=mu * A, minlength=G) / w)[g]

    eta, cur = state(b)
    for _ in range(maxit):
        mu = np.exp(eta)
        Zd = within(mu)(Z)
        Hp = (Zd * mu[:, None]).T @ Zd
        step = C.solve(Hp, Z.T @ (y - mu))
        t = 1.0
        eta_n, new = state(b + step)
        while not (np.isfinite(new) and new >= cur - 1e-9 * (1 + abs(cur))) and t > 1e-10:
            t /= 2
            eta_n, new = state(b + t * step)
        b, eta, cur = b + t * step, eta_n, new
        if np.max(np.abs(t * step)) < tol:
            break
    mu = np.exp(eta)
    wf = within(mu)
    Zd = wf(Z)
    return b, mu, (Zd * mu[:, None]).T @ Zd, wf


class BlockModel:
    """blocks: list of (rows: int index array, Z: per-city nuisance design, fe: per-row group codes or None).
    Z includes the city's own intercept when fe is None (and must not when fe is given). x: the tested column."""

    def __init__(self, blocks, x, y, offset, groups):
        self.blocks = blocks
        self.x, self.y, self.off = np.asarray(x, float), np.asarray(y, float), np.asarray(offset, float)
        self.groups = groups
        self.n = len(self.y)
        rows = np.concatenate([r for r, _, _ in blocks])
        assert len(rows) == self.n and len(np.unique(rows)) == self.n, "blocks must partition the rows"
        self._warm = {}

    def restricted(self, b0, key="grid"):
        """Per-city fits at beta = b0. Returns mu, xt (efficient residual of x), coefficients per city."""
        mu, xt = np.empty(self.n), np.empty(self.n)
        coefs = []
        warm = self._warm.get(key)
        for i, (r, Z, fe) in enumerate(self.blocks):
            off = self.off[r] + b0 * self.x[r]
            bi = None if warm is None else warm[i]
            if fe is None:
                b, m, Hz = C.poisson_fit(Z, self.y[r], off, b_init=bi)
                xt[r] = self.x[r] - Z @ C.solve(Hz, (Z * m[:, None]).T @ self.x[r])
            else:
                b, m, Hp, wf = _fit_fe(Z, fe, self.y[r], off, b_init=bi)
                xd, Zd = wf(self.x[r]), wf(Z)
                xt[r] = xd - Zd @ C.solve(Hp, (Zd * m[:, None]).T @ xd)
            mu[r] = m
            coefs.append(b)
        self._warm[key] = coefs
        return mu, xt, coefs

    def scores(self, b0, gidx, G, key="grid"):
        mu, xt, _ = self.restricted(b0, key)
        return np.bincount(gidx, weights=xt * (self.y - mu), minlength=G)

    def estimate(self, tol=1e-10, maxit=100):
        """Full fit: Newton on beta over the profile; score sum(x (y - mu)), information sum(mu x xt)."""
        beta = 0.0
        for _ in range(maxit):
            mu, xt, coefs = self.restricted(beta, key="fit")
            s, info = float(np.sum(self.x * (self.y - mu))), float(np.sum(mu * self.x * xt))
            step = s / info
            beta += step
            if abs(step) < tol:
                break
        mu, xt, coefs = self.restricted(beta, key="fit")
        self.beta, self.mu_full, self.coefs, self.info = beta, mu, coefs, float(np.sum(mu * self.x * xt))
        return beta

    def full_design(self):
        """The pooled design [city blocks..., x] (no fixed effects), as oa_core would fit it."""
        assert all(fe is None for _, _, fe in self.blocks)
        X = np.zeros((self.n, sum(Z.shape[1] for _, Z, _ in self.blocks) + 1))
        j = 0
        for r, Z, _ in self.blocks:
            X[np.ix_(r, np.arange(j, j + Z.shape[1]))] = Z
            j += Z.shape[1]
        X[:, -1] = self.x
        return X

    def infer(self, method, seed, interval=True):
        """Values of oa_core.infer(full design, ..., method, seed, interval) for this model."""
        if not hasattr(self, "beta"):
            self.estimate()
        est = float(self.beta)
        gidx, G = C.group_index(self.groups[C.BLOCK_OF[method]])
        out = dict(method=method, clusters=G, log_irr=est, irr=float(np.exp(est)))
        if method == "r1":
            X = self.full_design()
            b = np.r_[np.concatenate(self.coefs), est]
            mu = np.exp(self.off + X @ b)
            Hf = (X * mu[:, None]).T @ X
            r = C.infer(X, self.y, self.off, self.groups, "r1", seed, interval=interval, fit=(b, mu, Hf))
            return {k: r[k] for k in r}
        W = C.webb_weights(np.random.default_rng(seed), C.N_WILD, G)
        p_up, _ = C.wild_p(self.scores(0.0, gidx, G, key="p"), W)
        out["p_one_sided"] = float(p_up)
        if interval:
            pu, pl = np.empty(len(C.GRID)), np.empty(len(C.GRID))
            self._warm.pop("grid", None)
            for i, b0 in enumerate(C.GRID):
                pu[i], pl[i] = C.wild_p(self.scores(b0, gidx, G, key="grid"), W)
            for lev, a in ((90, 0.05), (95, 0.025)):
                keep = (pu >= a) & (pl >= a)
                if keep.any():
                    i0, i1 = np.flatnonzero(keep)[[0, -1]]
                    out[f"lo{lev}"] = None if i0 == 0 else float(np.exp(C.GRID[i0]))
                    out[f"hi{lev}"] = None if i1 == len(C.GRID) - 1 else float(np.exp(C.GRID[i1]))
                else:
                    out[f"lo{lev}"] = out[f"hi{lev}"] = None
        return out


def selftest(seed=7):
    """Small synthetic checks against oa_core on explicit designs: (1) two cities, no fixed effects: estimate, p and
    interval equal oa_core.infer; (2) fixed effects concentrated out equal the dummy-variable fit."""
    rng = np.random.default_rng(seed)
    n1, n2 = 3000, 4000
    city = np.r_[np.zeros(n1, int), np.ones(n2, int)]
    Z1, Z2 = rng.normal(size=(n1, 3)), rng.normal(size=(n2, 2))
    x = (rng.random(n1 + n2) < 0.1).astype(float)
    eta = np.r_[-3 + Z1 @ [0.3, -0.2, 0.1], -2.5 + Z2 @ [0.2, 0.4]] + 0.3 * x
    y = rng.poisson(np.exp(eta)).astype(float)
    off = np.zeros(n1 + n2)
    # enough clusters that a constant Webb weight vector (the only exact tie of the bootstrap statistic with the
    # observed one; probability 6 / 6^G per draw) does not occur: G(r4) = 10 + 13
    blk = np.r_[rng.integers(0, 60, n1), 120 + rng.integers(0, 78, n2)]
    groups = {"b2": blk, "b6": blk // 3, "b12": blk // 6}
    r1, r2 = np.flatnonzero(city == 0), np.flatnonzero(city == 1)
    M = BlockModel([(r1, np.c_[np.ones(n1), Z1], None), (r2, np.c_[np.ones(n2), Z2], None)], x, y, off, groups)
    X = M.full_design()
    for m in ("r1", "r3", "r4"):
        a, b = M.infer(m, [2071, 0], interval=True), C.infer(X, y, off, groups, m, [2071, 0], interval=True)
        assert abs(a["log_irr"] - b["log_irr"]) < 1e-8, (m, a["log_irr"], b["log_irr"])
        for k in ("p_one_sided", "lo90", "hi90", "lo95", "hi95"):
            assert (a[k] is None and b[k] is None) or abs(a[k] - b[k]) < 1e-8, (m, k, a[k], b[k])
    # fixed effects: groups within city (all with events), no intercept in Z
    fe1 = np.unique(blk[r1] // 3, return_inverse=True)[1]  # fixed effects on the 6 km blocks (all hold events)
    fe2 = np.unique(blk[r2] // 3, return_inverse=True)[1]
    assert np.bincount(fe1, weights=y[r1]).min() > 0 and np.bincount(fe2, weights=y[r2]).min() > 0
    MF = BlockModel([(r1, Z1, fe1), (r2, Z2, fe2)], x, y, off, groups)
    D1 = np.c_[np.eye(fe1.max() + 1)[fe1], Z1]
    D2 = np.c_[np.eye(fe2.max() + 1)[fe2], Z2]
    MD = BlockModel([(r1, D1, None), (r2, D2, None)], x, y, off, groups)
    for m in ("r3", "r4"):
        a, b = MF.infer(m, [2071, 1], interval=True), MD.infer(m, [2071, 1], interval=True)
        assert abs(a["log_irr"] - b["log_irr"]) < 1e-8, (m, a["log_irr"], b["log_irr"])
        for k in ("p_one_sided", "lo90", "hi90", "lo95", "hi95"):
            assert (a[k] is None and b[k] is None) or abs(a[k] - b[k]) < 1e-8, ("fe", m, k, a[k], b[k])
    bD = C.infer(MD.full_design(), y, off, groups, "r4", [2071, 1], interval=False)
    assert abs(bD["log_irr"] - MF.beta) < 1e-8
    return "hx_infer self-test passed: block model = oa_core.infer (r1, r3, r4; estimate, p, 90/95% intervals); " \
           "fixed effects concentrated = dummy variables (r3, r4)"


if __name__ == "__main__":
    print(selftest())
