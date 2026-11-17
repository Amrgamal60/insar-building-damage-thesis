"""Locally referenced interferograms for the Hong Kong MintPy stack (NYC plan §17 step 4), added 2026-10-17 before any order
data were linked to InSAR values.

Why: in the standard run, temporal coherence was high only near the automatic reference point (Shenzhen). Closure-phase
checks showed the errors are mostly whole-cycle offsets of entire unwrapped components relative to that distant point:
in 11 x 11 pixel urban blocks, 13-36% of triplet closures were non-zero against the reference point but 1-15% against the
block's own median (hk_mintpy_checks.py, plan §17 status). Bridging did not remove them.

What: for every interferogram, each valid pixel's unwrapped phase minus the mean phase of the valid pixels of the SAME
connected component within a 25 x 25 pixel (1 km) window. Whole-cycle offsets of a component cancel exactly, as does any
signal smoother than ~1 km (regional subsidence, troposphere, orbit). A pixel is kept only if its window holds at least
MIN_NEIGH valid pixels of its component. Valid = land (waterMask), connectComponent > 0, finite phase. The raw
unwrapPhase is used (bridging adds whole cycles per component, which cancel here anyway). Writes dataset
unwrapPhase_local (NaN = not kept) into hongkong/mintpy/inputs/ifgramStack.h5; MintPy's inversion then skips NaN per pixel.
Run from Alex/:  PROJ_DATA=~/miniforge3/envs/insar/share/proj ~/miniforge3/envs/insar/bin/python -I feasibility/hk_local_reference.py
Then, in hongkong/mintpy with the insar env's PATH, PROJ_DATA and GDAL_DATA set (run 2's smallbaselineApp.cfg and
exclude_date.txt; no tropospheric correction, which the 1 km reference mostly removes):
  ifgram_inversion.py inputs/ifgramStack.h5 -i unwrapPhase_local --skip-ref -m waterMask.h5 -o timeseries_local.h5 \
      temporalCoherence_local.h5 numInvIfgram_local.h5 -c local --num-worker 10
  dem_error.py timeseries_local.h5 -t smallbaselineApp.cfg -g inputs/geometryGeo.h5 -o timeseries_local_demErr.h5 \
      --dem-err-file demErr_local.h5      (it also writes timeseriesResidual.h5 next to -o: rename it to *_local.h5)
  timeseries2velocity.py timeseries_local_demErr.h5 -t smallbaselineApp.cfg -o velocity_local.h5
A pixel gets temporal coherence 0 when any date is left with no valid interferogram (MintPy's min_redundancy 1).
"""
from pathlib import Path

import h5py
import numpy as np
from scipy.ndimage import uniform_filter

MP = Path(__file__).resolve().parent / "hongkong" / "mintpy"
WIN, MIN_NEIGH = 25, 100
OUT = "unwrapPhase_local"


def local(phase, cc, land):
    out = np.full(phase.shape, np.nan, np.float32)
    valid = land & (cc > 0) & np.isfinite(phase)
    for lab in np.unique(cc[valid]):
        m = valid & (cc == lab)
        if m.sum() < MIN_NEIGH:
            continue
        mf = m.astype(np.float64)
        n = uniform_filter(mf, WIN, mode="constant") * WIN * WIN
        s = uniform_filter(np.where(m, phase, 0.0), WIN, mode="constant") * WIN * WIN
        keep = m & (n >= MIN_NEIGH - 0.5)
        out[keep] = (phase[keep] - s[keep] / n[keep]).astype(np.float32)
    return out


def main():
    with h5py.File(MP / "waterMask.h5") as h:
        land = h["waterMask"][:].astype(bool)
    with h5py.File(MP / "inputs" / "ifgramStack.h5", "r+") as f:
        unw, cc = f["unwrapPhase"], f["connectComponent"]
        n = unw.shape[0]
        ds = f[OUT] if OUT in f else f.create_dataset(OUT, unw.shape, np.float32, chunks=(1,) + unw.shape[1:], fillvalue=np.nan)
        kept = []
        for k in range(n):
            ds[k] = local(unw[k].astype(np.float64), cc[k], land)
            kept.append(float(np.isfinite(ds[k]).sum() / land.sum()))
            if k % 50 == 0 or k == n - 1:
                print(f"{k + 1}/{n} done; land share kept in this pair {kept[-1]:.3f}", flush=True)
        ds.attrs["DESCRIPTION"] = f"unwrapPhase minus same-component mean within {WIN} px; min {MIN_NEIGH} neighbours"
    print(f"median land share kept per pair: {np.median(kept):.3f}")


if __name__ == "__main__":
    main()
