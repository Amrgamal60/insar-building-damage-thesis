"""Variogram checks of the nulls (AUSTIN_PLAN.md §10: "as NYC, for 20 windows (seed 7), reported first, and never used
to change the null"; Test B "as Test A, for 5 quarters (seed 8)"). Outcome-blind: reads fields and surrogates only.
Whatever this shows, no null is changed.

As NYC (nyc/scripts/10_insar_checks.py, variogram_check): for the chosen windows, the observed semivariance at each lag
bin is compared with the 2.5th-97.5th percentile range of the 999 surrogates' semivariances; pairs count when both
ends have a value in the window (the surrogates keep the missing pattern); semivariance = sum over unordered pairs of
0.5 (z_i - z_j)^2 / pairs. Lag bins: lags 1-16 cell widths (lag = distance / cell size, rounded, as nyc_lib.Lags),
then longer lags up to 20 km in 1 km bins (b - 1, b] km; a pair at lag <= 16 stays in its lag bin.
  Test A  the conditional-null field (testa_core: the v field on the null pixels, raw mm/yr, the field the null was
          built on and the surrogate file holds) at 30 m. Windows: np.sort(default_rng(7).choice(88, 20, replace=False))
          of the 88 study months. Lag 16 ends at 0.495 km, so the 1 km bins run (0.495, 1], (1, 2], ..., (19, 20] km
          (20 bins; NYC's 250 m cells began them at 4.125 km). Authors' choice for the 30 m grid: the bins from 0.495 to
          4 km are included, so no distance up to 20 km is left out.
          Computation: NYC's pair list does not scale (107,244 pixels give about 5e9 pairs within 20 km). The same
          sums are formed exactly with masked FFT correlations on the 30 m pixel grid (zero-padded, no wrap-around for
          lags up to 20 km): for a displacement d, sum over pixels x with both x and x + d valid of
          (z(x) - z(x + d))^2 = C[m z^2, m](d) + C[m, m z^2](d) - 2 C[m z, m z](d), and the pair count is C[m, m](d)
          (m the valid mask, C[a, b](d) = sum_x a(x) b(x + d)). Each displacement is binned by its length, as pairs are.
          z is centred by the window's valid mean first (semivariance does not change). Checked before use against the
          frozen nyc_lib.Lags.vario (lags 1-16) and against direct pair sums on a pixel sample (all bins).
  Test B  the Test B null field (cells with a value in any quarter) at 250 m, with NYC's direct pair method (bins as
          NYC: lags 1-16, then (4.125, 5], (5, 6], ..., (19, 20] km). Quarters: np.sort(default_rng(8).choice(28, 5,
          replace=False)).
Writes OUT_DIR/variogram_check_{a,b}.csv (window, bin, pairs, observed, median, 2.5%, 97.5%, inside) and .json.
Usage:
  python -I check_variogram.py validate-a FEATURES GRID FIELD_V OUT_JSON
  python -I check_variogram.py a FEATURES GRID FIELD_V SURROGATES OUT_DIR [--workers N]
  python -I check_variogram.py b CELLS_NPZ TESTB_SURROGATES_NPZ OUT_DIR
"""
import os

for _name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[_name] = "1"
import argparse  # noqa: E402
import hashlib  # noqa: E402
import json  # noqa: E402
import multiprocessing as mp  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy import fft as sfft  # noqa: E402
from scipy.spatial import cKDTree  # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent / "planted_signal")]
import testa_core as C  # noqa: E402
import nyc_lib as N  # noqa: E402  (frozen copy, via testa_core's path)

MAX_LAG, MAX_KM = 16, 20
SEED_A, N_A, SEED_B, N_B = 7, 20, 8, 5


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 24), b""):
            h.update(b)
    return h.hexdigest()


def bin_of_distance(dist, res, first_km):
    """Bin index of pair distances (m): lags 1..16 -> 0..15; 1 km bins (b-1, b] km for b = first_km..20 -> 16..; -1 off."""
    lag = np.rint(dist / res).astype(np.int64)
    km = np.ceil(dist / 1000.0 - 1e-12).astype(np.int64)  # (b-1, b] km -> b (distance exactly b km -> b)
    long_ok = (lag > MAX_LAG) & (dist <= MAX_KM * 1000.0) & (km >= first_km)
    return np.where((lag >= 1) & (lag <= MAX_LAG), lag - 1, np.where(long_ok, MAX_LAG + km - first_km, -1))


def labels(res, first_km):
    end16 = (MAX_LAG + 0.5) * res / 1000
    return ([f"{(h + 1) * res / 1000:.3g} km (lag {h + 1})" for h in range(MAX_LAG)] +
            [f"{max(b - 1, end16):g}-{b} km" for b in range(first_km, MAX_KM + 1)])


# ---------------------------------------------------------------- Test A: exact FFT sums on the pixel grid
class GridVario:
    def __init__(self, pix_i, pix_j, res=C.PIXEL_M):
        self.res = res
        self.first_km = 1
        self.nb = MAX_LAG + MAX_KM - self.first_km + 1
        L = int(np.ceil(MAX_KM * 1000.0 / res)) + 1
        self.i0, self.j0 = pix_i - pix_i.min(), pix_j - pix_j.min()
        n1, n2 = int(self.i0.max()) + 1, int(self.j0.max()) + 1
        self.shape = (sfft.next_fast_len(n1 + L, real=True), sfft.next_fast_len(n2 + L, real=True))
        a = np.arange(self.shape[0]); a = np.where(a < self.shape[0] // 2, a, a - self.shape[0])  # noqa: E702
        b = np.arange(self.shape[1]); b = np.where(b < self.shape[1] // 2, b, b - self.shape[1])  # noqa: E702
        assert self.shape[0] // 2 > L and self.shape[1] // 2 > L
        dist = res * np.hypot(a[:, None], b[None, :])
        self.bin = bin_of_distance(dist, res, self.first_km).ravel()
        self.use = self.bin >= 0
        self.bin_use = self.bin[self.use]

    def grid(self, values):
        g = np.zeros(self.shape)
        g[self.i0, self.j0] = values
        return g

    def window(self, valid):
        """Per-window constants: the mask's transform and the pair counts per bin (exact integers)."""
        Mh = sfft.rfft2(self.grid(valid.astype(np.float64)))
        cnt = np.rint(sfft.irfft2(Mh * Mh.conj(), s=self.shape).ravel()[self.use])
        return Mh, np.bincount(self.bin_use, weights=cnt, minlength=self.nb)

    def vario(self, z, valid, Mh, cnt):
        z = np.where(valid, z - z[valid].mean(), 0.0)
        Ah, Zh = sfft.rfft2(self.grid(z * z)), sfft.rfft2(self.grid(z))
        S = sfft.irfft2(Ah.conj() * Mh + Mh.conj() * Ah - 2.0 * (Zh * Zh.conj()), s=self.shape).ravel()[self.use]
        num = np.bincount(self.bin_use, weights=S, minlength=self.nb)
        return 0.5 * num / np.where(cnt > 0, cnt, np.nan)


def load_a(features, grid, field):
    f = pd.read_parquet(features, columns=["prop_id", "complete_b1"])
    g = pd.read_parquet(grid, columns=["prop_id", "pix_i", "pix_j"])
    assert (f.prop_id.to_numpy() == g.prop_id.to_numpy()).all()
    geo = C.Geometry(pd.DataFrame({"pix_i": g.pix_i, "pix_j": g.pix_j, "complete_b1": f.complete_b1}))
    v_null = C.load_field(field, geo)[:, geo.null_pixels]
    return geo, v_null


def direct_pairs(xy, z, valid, res, first_km):
    """NYC's route on a small set: all pairs within 20 km, bincount by bin."""
    p = cKDTree(xy).query_pairs(r=MAX_KM * 1000.0, output_type="ndarray")
    k = bin_of_distance(np.hypot(*(xy[p[:, 0]] - xy[p[:, 1]]).T), res, first_km)
    nb = MAX_LAG + MAX_KM - first_km + 1
    out = np.full((len(z), nb), np.nan)
    for w in range(len(z)):
        vp = valid[w, p[:, 0]] & valid[w, p[:, 1]] & (k >= 0)
        num = np.bincount(k[vp], 0.5 * (z[w, p[vp, 0]] - z[w, p[vp, 1]]) ** 2, minlength=nb)
        cnt = np.bincount(k[vp], minlength=nb)
        out[w] = num / np.where(cnt > 0, cnt, np.nan)
    return out


def validate_a(a):
    geo, v = load_a(a.features, a.grid, a.field)
    pick = np.sort(np.random.default_rng(SEED_A).choice(len(C.MONTHS), N_A, replace=False))
    G = GridVario(geo.pix_i[geo.null_pixels], geo.pix_j[geo.null_pixels])
    xy = geo.null_xy()
    R = dict(field_sha256=sha256(a.field), windows=[C.MONTHS[w] for w in pick], grid_shape=list(G.shape))
    # 1. lags 1-16 on the full field: FFT against the frozen nyc_lib.Lags.vario
    t0 = time.perf_counter()
    lag = N.Lags(xy, C.PIXEL_M, MAX_LAG)
    w3 = pick[:3]
    ref = lag.vario(v[w3], np.isfinite(v[w3]))
    fftv = np.array([G.vario(v[w], np.isfinite(v[w]), *G.window(np.isfinite(v[w]))) for w in w3])
    R["lags_1_16_vs_frozen_Lags"] = dict(windows=[C.MONTHS[w] for w in w3],
                                         max_rel_diff=float(np.max(np.abs(fftv[:, :MAX_LAG] / ref - 1))),
                                         seconds=time.perf_counter() - t0)
    # 2. every bin on a pixel sample: FFT (mask = the sample) against direct pair sums
    rng = np.random.default_rng(0)
    s = np.sort(rng.choice(v.shape[1], 6000, replace=False))
    Gs = GridVario(geo.pix_i[geo.null_pixels][s], geo.pix_j[geo.null_pixels][s])
    vs = v[w3][:, s]
    ok = np.isfinite(vs)
    direct = direct_pairs(xy[s], vs, ok, C.PIXEL_M, 1)
    fs = np.array([Gs.vario(vs[k], ok[k], *Gs.window(ok[k])) for k in range(len(w3))])
    both = np.isfinite(direct) & np.isfinite(fs)
    R["all_bins_vs_direct_pairs_on_6000_pixels"] = dict(bins=int(both.shape[1]), finite_equal=bool((np.isfinite(direct) == np.isfinite(fs)).all()),
                                                        max_rel_diff=float(np.max(np.abs(fs[both] / direct[both] - 1))))
    R["pass"] = bool(R["lags_1_16_vs_frozen_Lags"]["max_rel_diff"] < 1e-9 and R["all_bins_vs_direct_pairs_on_6000_pixels"]["finite_equal"]
                     and R["all_bins_vs_direct_pairs_on_6000_pixels"]["max_rel_diff"] < 1e-9)
    Path(a.out).write_text(json.dumps(R, indent=1) + "\n")
    print(json.dumps(R, indent=1))


_W = {}


def _draw_a(d):
    S = np.asarray(_W["store"].S[d, _W["pick"]], dtype=np.float64)  # the chosen windows of draw d
    return d, np.array([_W["G"].vario(S[k], _W["valid"][k], *_W["win"][k]) for k in range(len(_W["pick"]))])


def k_summary(ks):
    ks = np.asarray(ks)
    return dict(median=float(np.median(ks)), p2_5=float(np.percentile(ks, 2.5)), p97_5=float(np.percentile(ks, 97.5)),
                counts={str(int(k)): int((ks == k).sum()) for k in np.unique(ks)})


def summarise(obs, sv, cnt, names, win_labels, out_dir, tag, extra):
    lo, hi, med = np.percentile(sv, 2.5, 0), np.percentile(sv, 97.5, 0), np.median(sv, 0)
    rows = []
    for k, wl in enumerate(win_labels):
        for b, name in enumerate(names):
            rows.append({"window": wl, "bin": name, "pairs": int(cnt[k, b]), "observed": obs[k, b], "median": med[k, b],
                         "2.5%": lo[k, b], "97.5%": hi[k, b], "inside": bool(lo[k, b] <= obs[k, b] <= hi[k, b]),
                         "below": bool(obs[k, b] < lo[k, b]), "above": bool(obs[k, b] > hi[k, b])})
    t = pd.DataFrame(rows)
    t.to_csv(out_dir / f"variogram_check_{tag}.csv", index=False)
    short = t.bin.str.contains("lag")
    ratio = (t["median"] / t.observed)
    per_window = {wl: dict(lags_1_16_inside=int(g.inside[short[g.index]].sum()), long_bins_inside=int(g.inside[~short[g.index]].sum()),
                           ratio_lags_1_4=[round(float(x), 3) for x in ratio[g.index][short[g.index]].values[:4]],
                           ratio_lags_5_16_range=[round(float(ratio[g.index][short[g.index]].values[4:].min()), 3),
                                                  round(float(ratio[g.index][short[g.index]].values[4:].max()), 3)],
                           below=int(g.below.sum()), above=int(g.above.sum()))
                  for wl, g in t.groupby("window", sort=False)}
    per_bin = {name: dict(windows_inside=int(g.inside.sum()), median_ratio=round(float(np.median(ratio[g.index])), 3))
               for name, g in t.groupby("bin", sort=False)}
    R = dict(**extra, windows=list(win_labels), bins=names,
             lags_1_16_inside=[int(t.inside[short].sum()), int(short.sum())],
             long_bins_inside=[int(t.inside[~short].sum()), int((~short).sum())],
             below=int(t.below.sum()), above=int(t.above.sum()), per_window=per_window, per_bin=per_bin)
    (out_dir / f"variogram_check_{tag}.json").write_text(json.dumps(R, indent=1) + "\n")
    print(json.dumps({k: R[k] for k in ("windows", "lags_1_16_inside", "long_bins_inside", "below", "above")}, indent=1))


def run_a(a):
    t0 = time.perf_counter()
    geo, v = load_a(a.features, a.grid, a.field)
    store = C.SurrogateStore(a.surrogates, C.null_fingerprint(v, geo))
    pick = np.sort(np.random.default_rng(SEED_A).choice(len(C.MONTHS), N_A, replace=False))
    G = GridVario(geo.pix_i[geo.null_pixels], geo.pix_j[geo.null_pixels])
    valid = np.isfinite(v[pick])
    first = store.draw(0)[pick]
    assert np.array_equal(np.isfinite(first), valid), "surrogates do not keep the missing pattern"
    win = [G.window(valid[k]) for k in range(len(pick))]
    cnt = np.array([c for _, c in win])
    obs = np.array([G.vario(v[w], valid[k], *win[k]) for k, w in enumerate(pick)])
    _W.update(store=store, G=G, valid=valid, win=win, pick=pick)
    sv = np.empty((store.draws,) + obs.shape)
    with mp.get_context("fork").Pool(a.workers) as pool:
        for d, g in pool.imap_unordered(_draw_a, range(store.draws), chunksize=4):
            sv[d] = g
    np.save(Path(a.out) / "variogram_check_a_draws.npy", sv)
    summarise(obs, sv, cnt, labels(C.PIXEL_M, 1), [C.MONTHS[w] for w in pick], Path(a.out), "a",
              dict(test="A", field_sha256=sha256(a.field), surrogates_sha256=store.meta["sha256"], draws=store.draws,
                   seed=SEED_A, chosen_k=k_summary(store.meta["chosen_k"]), method="masked FFT sums on the 30 m pixel grid (exact; validated by validate-a)",
                   grid_shape=list(G.shape), seconds=time.perf_counter() - t0))


def run_b(a):
    t0 = time.perf_counter()
    c = np.load(a.cells, allow_pickle=False)
    s = np.load(a.surrogates, allow_pickle=False)
    use = np.isfinite(c["v"]).any(0)
    assert np.array_equal(c["cells"][use], s["cells"]) and np.array_equal(c["quarters"], s["quarters"])
    f, xy = c["v"][:, use], c["xy"][use]
    pick = np.sort(np.random.default_rng(SEED_B).choice(len(c["quarters"]), N_B, replace=False))
    first_km = 5  # 250 m cells: lag 16 ends at 4.125 km, so the 1 km bins are (4.125, 5], (5, 6], ..., (19, 20], as NYC
    p = cKDTree(xy).query_pairs(r=MAX_KM * 1000.0, output_type="ndarray")
    k = bin_of_distance(np.hypot(*(xy[p[:, 0]] - xy[p[:, 1]]).T), 250.0, first_km)
    nb = MAX_LAG + MAX_KM - first_km + 1
    valid = np.isfinite(f[pick])

    def vario(z):
        out, cnt = np.full((len(pick), nb), np.nan), np.zeros((len(pick), nb))
        for w in range(len(pick)):
            vp = valid[w, p[:, 0]] & valid[w, p[:, 1]] & (k >= 0)
            num = np.bincount(k[vp], 0.5 * (z[w, p[vp, 0]] - z[w, p[vp, 1]]) ** 2, minlength=nb)
            cnt[w] = np.bincount(k[vp], minlength=nb)
            out[w] = num / np.where(cnt[w] > 0, cnt[w], np.nan)
        return out, cnt

    obs, cnt = vario(f[pick])
    S = s["fields"]
    assert np.array_equal(np.isfinite(S[0][pick]), valid)
    sv = np.array([vario(S[d][pick])[0] for d in range(len(S))])
    summarise(obs, sv, cnt, labels(250.0, first_km), [str(q) for q in c["quarters"][pick]], Path(a.out), "b",
              dict(test="B", cells_npz_sha256=sha256(a.cells), surrogates_sha256=sha256(a.surrogates), draws=int(len(S)),
                   seed=SEED_B, chosen_k=k_summary(s["k"]), method="direct pair sums (NYC)", seconds=time.perf_counter() - t0))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    v = sub.add_parser("validate-a")
    for k in ("features", "grid", "field", "out"):
        v.add_argument(k, type=Path)
    q = sub.add_parser("a")
    for k in ("features", "grid", "field", "surrogates", "out"):
        q.add_argument(k, type=Path)
    q.add_argument("--workers", type=int, default=16)
    b = sub.add_parser("b")
    for k in ("cells", "surrogates", "out"):
        b.add_argument(k, type=Path)
    a = p.parse_args()
    if a.cmd != "validate-a":
        a.out.mkdir(parents=True, exist_ok=True)
    {"validate-a": validate_a, "a": run_a, "b": run_b}[a.cmd](a)


if __name__ == "__main__":
    main()
