"""Synthetic-signal test of the Hong Kong locally referenced product (NYC plan §17 step 4), added 2026-10-17 after the GPT
review, before any order data were linked to InSAR values. No order data are read.

Question: how much of a known ground-motion pattern survives the processing steps after HyP3, as a function of its width?
Where the signal enters: the clipped HyP3 unwrapped interferograms (`unwrapPhase` in inputs/ifgramStack.h5), i.e. AFTER
HyP3's 10x2-look multilooking, filtering and unwrapping, which this test therefore does not cover. It tests the steps that
follow: local referencing (hk_local_reference.local), the network inversion with its per-pixel gaps, the DEM-error
correction and the velocity fit, all with the same commands and masks as the real local product.

Signal: Gaussian bowls of line-of-sight velocity A = -5 mm/yr (away from the satellite), linear in time, with widths
sigma = 40 ... 2,560 m, placed (seeded, greedy, largest first) at centres where the real local product has temporal
coherence >= 0.7, far enough apart that responses do not overlap. Pair phase = -4*pi/wavelength * (D(t2) - D(t1)), MintPy's
convention (displacement positive toward the satellite).
Every step after injection is linear in the phase for fixed masks and weights, so the recovered signal is
velocity_synth - velocity_local exactly (up to float rounding); the real product's noise is reported beside it.

  inject:    writes unwrapPhase_synth_local into inputs/ifgramStack.h5 and synth/truth.h5, synth/placements.json
  (then run the inversion, dem_error and timeseries2velocity into synth/, see SHELL below)
  evaluate:  writes synth/SYNTH_TEST.json (per width: amplitude recovered, correlation, halo, noise; ideal-filter value)
Run from Alex/:  PROJ_DATA=~/miniforge3/envs/insar/share/proj ~/miniforge3/envs/insar/bin/python -I feasibility/hk_synthetic_test.py inject|evaluate
"""
import importlib.util
import json
import sys
from pathlib import Path

import h5py
import numpy as np
from scipy.ndimage import uniform_filter

HERE = Path(__file__).resolve().parent
MP = HERE / "hongkong" / "mintpy"
OUT = MP / "synth"
spec = importlib.util.spec_from_file_location("hk_local_reference", HERE / "hk_local_reference.py")
LR = importlib.util.module_from_spec(spec)
spec.loader.exec_module(LR)
PIX = 40.0
SIGMAS = [2560, 1280, 640, 320, 160, 80, 40]  # m, placed largest first
PER_SIGMA = 6
AMP = -5.0  # mm/yr LOS
SEED = 20261017
DS = "unwrapPhase_synth_local"
SHELL = """cd feasibility/hongkong/mintpy; ln -sf ../temporalCoherence.h5 synth/temporalCoherence.h5  # dem_error's mask, as in the local run
ifgram_inversion.py inputs/ifgramStack.h5 -i unwrapPhase_synth_local --skip-ref -m waterMask.h5 -o synth/timeseries_synth.h5 \\
    synth/temporalCoherence_synth.h5 synth/numInvIfgram_synth.h5 -c local --num-worker 10
dem_error.py synth/timeseries_synth.h5 -t smallbaselineApp.cfg -g inputs/geometryGeo.h5 -o synth/timeseries_synth_demErr.h5 --dem-err-file synth/demErr_synth.h5
timeseries2velocity.py synth/timeseries_synth_demErr.h5 -t smallbaselineApp.cfg -o synth/velocity_synth.h5"""


def read(name, key):
    with h5py.File(MP / name) as h:
        return h[key][:]


def bowl(shape, r0, c0, sigma):
    yy, xx = np.ogrid[:shape[0], :shape[1]]
    return np.exp(-((yy - r0) ** 2 + (xx - c0) ** 2) * PIX ** 2 / (2.0 * sigma ** 2))


def place(good):
    """Greedy seeded placement: centre on a good pixel, >= 30% good pixels within max(sigma, 80 m), and centres apart by
    3*sigma_i + 3*sigma_j + 2 km so that no bowl's response (bowl + the 0.5 km half-window) reaches another's."""
    rng = np.random.default_rng(SEED)
    frac = {}
    cand = np.flatnonzero(good.ravel())
    rng.shuffle(cand)
    placed = []
    for s in SIGMAS:
        rad = max(s, 80) / PIX
        k = int(2 * np.ceil(rad) + 1)
        frac[s] = uniform_filter(good.astype(float), k, mode="constant")
        n = 0
        for idx in cand:
            r, c = divmod(int(idx), good.shape[1])
            if frac[s][r, c] < 0.3:
                continue
            if all(np.hypot(r - p["row"], c - p["col"]) * PIX >= 3 * s + 3 * p["sigma_m"] + 2000 for p in placed):
                placed.append({"sigma_m": s, "row": r, "col": c})
                n += 1
                if n == PER_SIGMA:
                    break
    return placed


def inject():
    land = read("waterMask.h5", "waterMask").astype(bool)
    good = land & (np.nan_to_num(read("temporalCoherence_local.h5", "temporalCoherence")) >= 0.7)
    placed = place(good)
    vel = np.zeros(land.shape)  # mm/yr
    for p in placed:
        vel += AMP * bowl(land.shape, p["row"], p["col"], p["sigma_m"])
    OUT.mkdir(exist_ok=True)
    with h5py.File(OUT / "truth.h5", "w") as h:
        h["velocity_mm_yr"] = vel.astype(np.float32)
    (OUT / "placements.json").write_text(json.dumps({"amplitude_mm_yr": AMP, "seed": SEED, "bowls": placed}, indent=1) + "\n")
    print({s: sum(p["sigma_m"] == s for p in placed) for s in SIGMAS}, flush=True)
    with h5py.File(MP / "inputs" / "ifgramStack.h5", "r+") as f:
        unw, cc = f["unwrapPhase"], f["connectComponent"]
        wl = float(f.attrs["WAVELENGTH"])
        t = np.array([[np.datetime64(f"{d[:4]}-{d[4:6]}-{d[6:]}") for d in (p[0].decode(), p[1].decode())] for p in f["date"][:]])
        t0 = t.min()
        yrs = (t - t0).astype("timedelta64[D]").astype(float) / 365.25
        ds = f[DS] if DS in f else f.create_dataset(DS, unw.shape, np.float32, chunks=(1,) + unw.shape[1:], fillvalue=np.nan)
        for k in range(unw.shape[0]):
            dphase = -4 * np.pi / wl * (vel / 1000.0) * (yrs[k, 1] - yrs[k, 0])
            ds[k] = LR.local(unw[k].astype(np.float64) + dphase, cc[k], land)
            if k % 100 == 0 or k == unw.shape[0] - 1:
                print(f"{k + 1}/{unw.shape[0]}", flush=True)
        ds.attrs["DESCRIPTION"] = "unwrapPhase + synthetic bowls (hk_synthetic_test.py), then hk_local_reference.local"


def evaluate():
    land = read("waterMask.h5", "waterMask").astype(bool)
    tcoh = np.nan_to_num(read("temporalCoherence_local.h5", "temporalCoherence"))
    good = land & (tcoh >= 0.7)
    vloc = read("velocity_local.h5", "velocity") * 1000
    with h5py.File(OUT / "velocity_synth.h5") as h:
        vsyn = h["velocity"][:] * 1000
    with h5py.File(OUT / "truth.h5") as h:
        truth = h["velocity_mm_yr"][:]
    rec = vsyn - vloc
    pl = json.loads((OUT / "placements.json").read_text())
    half = 12  # the 25 x 25 window of hk_local_reference
    rows = []
    for p in pl["bowls"]:
        s, r0, c0 = p["sigma_m"], p["row"], p["col"]
        b = AMP * bowl(land.shape, r0, c0, s)
        dist = np.hypot(*np.ogrid[-r0:land.shape[0] - r0, -c0:land.shape[1] - c0]) * PIX
        core = good & (dist <= max(2 * s, 60))
        area = good & (dist <= 3 * s + 500)
        ring = good & (dist > 3 * s) & (dist <= 3 * s + 500)
        # the same bowl through the bare 25 x 25 mean subtraction on a fully valid grid (no masks, no inversion)
        ideal = b - uniform_filter(b, 2 * half + 1, mode="constant")
        rows.append({"sigma_m": s, "row": r0, "col": c0, "centre_valid": bool(good[r0, c0]),
                     "centre_recovered_over_injected": round(float(rec[r0, c0] / AMP), 3) if good[r0, c0] else None,
                     "centre_ideal_filter_over_injected": round(float(ideal[r0, c0] / AMP), 3),
                     "core_pixels": int(core.sum()),
                     "core_amplitude_ratio": round(float((rec[core] * b[core]).sum() / (b[core] ** 2).sum()), 3) if core.any() else None,
                     "area_corr_recovered_vs_injected": round(float(np.corrcoef(rec[area], b[area])[0, 1]), 3) if area.sum() > 2 else None,
                     "ring_mean_recovered_mm_yr": round(float(rec[ring].mean()), 3) if ring.any() else None,
                     "noise_std_real_product_in_area_mm_yr": round(float(vloc[area].std()), 3) if area.any() else None,
                     "area_corr_full_product_vs_injected": round(float(np.corrcoef(vsyn[area], b[area])[0, 1]), 3) if area.sum() > 2 else None})
    by = {}
    for s in SIGMAS:
        rr = [x for x in rows if x["sigma_m"] == s]
        med = lambda k: (round(float(np.median([x[k] for x in rr if x[k] is not None])), 3) if any(x[k] is not None for x in rr) else None)
        by[s] = {"bowls": len(rr), **{k: med(k) for k in ["centre_recovered_over_injected", "centre_ideal_filter_over_injected",
                                                         "core_amplitude_ratio", "area_corr_recovered_vs_injected",
                                                         "ring_mean_recovered_mm_yr", "noise_std_real_product_in_area_mm_yr",
                                                         "area_corr_full_product_vs_injected"]}}
    far = good & (np.abs(truth) < 1e-6 * abs(AMP))  # linearity check: nothing should appear away from the bowls
    out = {"amplitude_mm_yr": AMP, "injection_point": "clipped HyP3 unwrapPhase, before local referencing",
           "max_abs_recovered_far_from_bowls_mm_yr": round(float(np.abs(rec[far]).max()), 6),
           "by_sigma_median": by, "bowls": rows}
    (OUT / "SYNTH_TEST.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps({k: out[k] for k in ["max_abs_recovered_far_from_bowls_mm_yr", "by_sigma_median"]}, indent=1))


if __name__ == "__main__":
    {"inject": inject, "evaluate": evaluate}[sys.argv[1]]()
