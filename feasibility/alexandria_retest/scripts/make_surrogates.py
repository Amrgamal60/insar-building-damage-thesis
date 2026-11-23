"""Surrogates and the variogram check of ALEX_RETEST_PLAN.md §6 (outcome-blind: no label is read).

For each pixel null (c1 linear conditional on the baseline, c2 linear conditional on baseline + x/y, a
unconditional; plan draft 3): 999 draws, seed 2043, on the pixels of the 241 primary cells, averaged into cells. The original plain variogram-matching null at cell
level (241 cells, scripts/17_licsar_test.py surrogates, seed 2027) is saved beside them. The variogram check
compares surrogates and the observed field at pixel level (lags 1-16 x 100 m) and at cell level on the 241
primary cells (lags 1-6 x 250 m), with pair counts.

Outputs (feasibility/alexandria_retest/step0/): surrogates.npz, variogram_check.json, VARIOGRAM_CHECK.md.
The first version (341-cell field, HistGradientBoosting fits) is kept as *_v1.
"""
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import retest_core as R  # noqa: E402

OUT = R.RETEST / "step0"
N_DRAWS = 999


def summary(obs, sims):
    lo, med, hi = np.nanpercentile(sims, [2.5, 50, 97.5], axis=0)
    return dict(observed=obs.tolist(), median=med.tolist(), lo95=lo.tolist(), hi95=hi.tolist(),
                inside=((obs >= lo) & (obs <= hi)).tolist(), ratio_median_to_observed=(med / obs).tolist())


def main():
    OUT.mkdir(exist_ok=True)
    c, _, _ = R.load_cells()  # labels are not used below
    px = R.PixelField(c)
    idx241 = np.arange(len(c))
    xy241 = c[["x", "y"]].to_numpy(float)
    v241 = c[R.COL].to_numpy(float)
    pix_lags = R.N.Lags(px.xy, R.PIXEL_LAG_M, R.MAX_LAG)
    cell_lags, obs_cell = R.cell_variogram(v241, xy241)
    obs_pix = pix_lags.vario(px.v)[0]
    pairs_pix = np.bincount(pix_lags.k, minlength=R.MAX_LAG + 1)[1:].tolist()
    pairs_cell = np.bincount(cell_lags.k, minlength=R.CELL_CHECK_LAGS + 1)[1:].tolist()
    arrays, check = {}, dict(pixel_pairs_per_lag=pairs_pix, cell_pairs_per_lag=pairs_cell, nulls={})
    for kind in ("c1", "c2", "a"):
        t0 = time.perf_counter()
        S_pix, ks, explained = R.pixel_surrogates(kind, px, N_DRAWS)
        cells = px.to_cells(S_pix)  # (999, 241)
        arrays[f"{kind}_cells241"] = cells
        check["nulls"][kind] = dict(seconds=time.perf_counter() - t0, explained_variance=explained,
                                    neighbour_k=dict(min=min(ks), median=float(np.median(ks)), max=max(ks)),
                                    pixel=summary(obs_pix, pix_lags.vario(S_pix)),
                                    cell=summary(obs_cell[0], cell_lags.vario(cells[:, idx241])))
        print(kind, f"{check['nulls'][kind]['seconds']:.0f} s, explained {explained:.3f}", flush=True)
    surr, _ = R.T17.surrogates(v241, xy241, R.RES, N_DRAWS)
    arrays["plain_cells241"] = surr["Variogram-matching"]
    check["nulls"]["plain"] = dict(cell=summary(obs_cell[0], cell_lags.vario(arrays["plain_cells241"])))
    np.savez(OUT / "surrogates.npz", **arrays)
    rec = dict(draws=N_DRAWS, seed=R.SEED_NULL, pixels=int(len(px.v)), field_cells=int(len(c)),
               surrogates_sha256=R.sha256(OUT / "surrogates.npz"), check=check, **R.hashes())
    (OUT / "variogram_check.json").write_text(json.dumps(rec, indent=1) + "\n")
    names = dict(c1="c1 linear conditional, baseline", c2="c2 linear conditional, baseline + x/y",
                 a="a unconditional pixel null", plain="original plain variogram-matching (cell level)")
    lines = ["# Variogram check of the retest nulls (outcome-blind; read before any planted or real p-value)", "",
             f"{N_DRAWS} draws per null; pixel field {len(px.v)} pixels in the {len(c)} primary cells; cell level on the same cells.",
             "Cells give the surrogates' median as a multiple of the observed semivariance; * = observed outside the surrogates' 95% range.", ""]
    for level, nl, pairs, width in (("pixel", R.MAX_LAG, pairs_pix, 100), ("cell", R.CELL_CHECK_LAGS, pairs_cell, 250)):
        lines += [f"## {level.capitalize()} level (lag unit {width} m)", "",
                  "| Null | explained variance | " + " | ".join(f"lag {k}" for k in range(1, nl + 1)) + " |",
                  "|---|---|" + "---|" * nl,
                  "| pairs | | " + " | ".join(str(p) for p in pairs) + " |"]
        for k, d in check["nulls"].items():
            if level not in d:
                continue
            s = d[level]
            ev = f"{d['explained_variance']:.3f}" if "explained_variance" in d else ""
            lines.append(f"| {names[k]} | {ev} | " + " | ".join(
                f"{r:.2f}{'' if ins else '*'}" for r, ins in zip(s["ratio_median_to_observed"], s["inside"])) + " |")
        lines.append("")
    (OUT / "VARIOGRAM_CHECK.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
