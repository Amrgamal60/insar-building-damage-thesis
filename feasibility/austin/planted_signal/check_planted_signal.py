"""Check of the planted-signal script and the Test A core on synthetic velocity fields only (AUSTIN_PLAN §14:
"written, checked on synthetic data and hashed into §15 before any InSAR file is opened").

No InSAR file is read. The velocity field is synthetic, built on the real pixel geometry of the eligible
houses. Real houses, Baseline 1 features, folds, demolition dates and event dates are used, as in the
planted-signal check itself. Steps:

 1. Equivalence with the frozen calibration: on a frozen synthetic city (calibration/simulation.city_a), the
    core's standardisation equals the frozen standardise_at_rows bit for bit, and the core's statistic
    reproduces the stored calibration record's observed change.
 2. Geometry: the core's fold map with the real labels reproduces the stored checkpoint-1 folds; pixel counts.
 3. Synthetic field (88 windows x all eligible pixels, NaN masks) saved with testa_core.save_field.
 4. Surrogates: the frozen ConditionalVariogramNull (CPU backend of the calibration) on the null field, a few
    draws, written by testa_core.write_surrogates. The neighbour cap is lowered to 200 (max_lag 16, chunk 8)
    to keep the CPU check within the PC's free memory; the production setting (1000) runs on the GPU.
    Surrogates already in the work directory are reused if they were made from the same synthetic field.
 4b. Standardisation sets (§7), recomputed with a separate join of houses to pixels: the observed field over
    all eligible houses with a value, each surrogate field over the houses on null-field pixels.
 5. planted_signal.py event-dates, quantiles, run (cells 1-6, 2 datasets each) and summarise.
 6. Independent checks of two datasets: event counts per date, unique houses, every case a valid candidate,
    every control valid under the shared rule, dropped rows.
 7. Selection frequencies of the weighted draw against exp(eta) at one date (chi-square).
 8. Reproducibility: two jobs rerun in a fresh directory give identical records.
 9. Timing projection for 999 draws and 600 datasets.
"""
import os

for _name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMBA_NUM_THREADS"):
    os.environ[_name] = "1"
import argparse  # noqa: E402
import json  # noqa: E402
import resource  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy.ndimage import gaussian_filter  # noqa: E402
from scipy.stats import chisquare  # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE)]
import testa_core as C  # noqa: E402
import planted_signal as PS  # noqa: E402

CAL = C.FROZEN / "calibration"
sys.path.insert(0, str(CAL))

p = argparse.ArgumentParser()
for k in ("features", "grid", "episodes", "censoring", "events"):
    p.add_argument(f"--{k}", type=Path, required=True)
p.add_argument("--work", type=Path, required=True, help="scratch directory for the synthetic field and surrogates")
p.add_argument("--out", type=Path, default=HERE / "check")
p.add_argument("--draws", type=int, default=20)
p.add_argument("--workers", type=int, default=12)
a = p.parse_args()
a.work.mkdir(parents=True, exist_ok=True)
a.out.mkdir(parents=True, exist_ok=True)
R = dict(sources=PS.source_hashes(), check_sha256=C.sha256(Path(__file__)), draws=a.draws, workers=a.workers)
T0 = time.perf_counter()


def note(msg):
    print(f"[{time.perf_counter() - T0:7.1f} s] {msg}", flush=True)


def save():
    (a.out / "check_results.json").write_text(json.dumps(R, indent=1, default=float) + "\n")


# ---------------------------------------------------------------- 1. equivalence with the frozen calibration
from simulation import city_a, standardise_at_rows  # noqa: E402
import nyc_lib as N  # noqa: E402

config = json.loads((CAL / "design.json").read_text())
rec = json.loads((CAL / "records" / "A_00_0000.json").read_text())
spec = rec["spec"]
data = city_a(config, rec["seed"], spec[3], spec[4], spec[5])
frozen_u = standardise_at_rows(data["fields"], data)
q = C.window_quantiles(data["fields"][:, data["pixel"]])
core_u = C.standardise(data["fields"][data["row_window"], data["row_pixel"]], data["row_window"], q)
A = C.TestA(data["X"], data["y"], data["fold"])
observed = A.delta(core_u)
baseline_frozen = float(N.average_precision_score(data["y"], N.oof(data["X"], data["y"], data["fold"], N.LR)))
R["1_equivalence"] = dict(record="calibration/records/A_00_0000.json", spec=spec,
                          standardisation_bit_identical=bool(np.array_equal(frozen_u, core_u)),
                          baseline_equal=A.baseline == baseline_frozen == rec["baseline_average_precision"],
                          observed_core=observed, observed_record=rec["observed"],
                          observed_equal=observed == rec["observed"])
assert R["1_equivalence"]["standardisation_bit_identical"] and R["1_equivalence"]["baseline_equal"]
assert R["1_equivalence"]["observed_equal"]
note("1 equivalence with the frozen calibration: identical")
save()

# ---------------------------------------------------------------- 2. geometry
h = C.load_houses(a.features, a.grid, a.episodes, a.censoring)
geo = C.Geometry(h)
fold_again = C.fold_of_houses(h, h.holds_event.to_numpy(bool))
R["2_geometry"] = dict(houses=len(h), complete=int(h.complete_b1.sum()), pixels=len(geo.pix_i),
                       null_pixels=len(geo.null_pixels), observed_standardisation_houses=len(geo.house_pixel),
                       surrogate_standardisation_houses=len(geo.null_houses),
                       houses_off_null_field=int((geo.house_null < 0).sum()),
                       folds_reproduced=bool(np.array_equal(fold_again, h.fold.to_numpy())))
assert R["2_geometry"]["folds_reproduced"]
cov = C.null_covariates(h, geo)
note(f"2 geometry: {R['2_geometry']}")
save()

# ---------------------------------------------------------------- 3. synthetic field
field_path = a.work / "synthetic_field.npz"
rng = np.random.default_rng(20261111)
W, P = len(C.MONTHS), len(geo.pix_i)
i0, j0 = geo.pix_i.min(), geo.pix_j.min()
shape = (int(geo.pix_j.max() - j0 + 1), int(geo.pix_i.max() - i0 + 1))


def smooth(sigma_px):
    f = gaussian_filter(rng.standard_normal(shape), sigma_px)
    v = f[geo.pix_j - j0, geo.pix_i - i0]
    return (v - v.mean()) / v.std()


def pixel_mean(col):
    x = h[col].to_numpy(float)
    ok = np.isfinite(x)
    s = np.bincount(geo.house_pixel[ok], weights=x[ok], minlength=P)
    n = np.bincount(geo.house_pixel[ok], minlength=P)
    m = np.where(n > 0, s / np.maximum(n, 1), np.nan)
    z = (m - np.nanmean(m)) / np.nanstd(m)
    return np.where(np.isfinite(z), z, 0.0)


g = 0.8 * pixel_mean("lep_0_150") + 0.3 * pixel_mean("elevation_m") + 0.2 * np.maximum(pixel_mean("lep_0_150") - 0.7, 0) ** 2
stat_s, stat_w = smooth(16), rng.standard_normal(P)
monthly_s = np.array([smooth(16) for _ in range(W + 23)])
monthly_w = rng.standard_normal((W + 23, P))
v = np.empty((W, P))
for w in range(W):
    spatial = np.sqrt(.7) * stat_s + np.sqrt(.3) * monthly_s[w:w + 24].sum(0) / np.sqrt(24)
    white = np.sqrt(.7) * stat_w + np.sqrt(.3) * monthly_w[w:w + 24].sum(0) / np.sqrt(24)
    v[w] = -1.0 + 1.5 * (g + 0.9 * (np.sqrt(.8) * spatial + np.sqrt(.2) * white))
always = rng.random(P) < 0.005
v[(rng.random((W, P)) < 0.03) | always[None, :]] = np.nan
C.save_field(field_path, v, geo, meta=dict(synthetic=True, seed=20261111))
v_null = C.load_field(field_path, geo)[:, geo.null_pixels]
fp = C.null_fingerprint(v_null, geo)
R["3_field"] = dict(path=str(field_path), sha256=C.sha256(field_path), fingerprint=fp, valid_share=float(np.isfinite(v).mean()))
note("3 synthetic field saved")
save()

# ---------------------------------------------------------------- 4. surrogates (frozen conditional null, CPU backend)
from conditional_null import ConditionalVariogramNull  # noqa: E402
from cpu_null import CPULowMemVariogramNull  # noqa: E402

CHECK_NULL_SETTINGS = dict(C.NULL_SETTINGS, kmax=200)
store_path = a.work / "surrogates_conditional.npy"
if store_path.exists() and json.loads(Path(str(store_path) + ".json").read_text()).get("fingerprint") == fp:
    meta = json.loads(Path(str(store_path) + ".json").read_text())
    R["4_surrogates"] = dict(reused=True, draws=meta["draws"], sha256=meta["sha256"])
else:
    t = time.perf_counter()
    engine = ConditionalVariogramNull(v_null, geo.null_xy(), C.PIXEL_M, cov, feature_names=C.NULL_COVARIATES,
                                      null_factory=CPULowMemVariogramNull, **CHECK_NULL_SETTINGS)
    setup = time.perf_counter() - t
    t = time.perf_counter()
    meta = C.write_surrogates(store_path, engine, a.draws, C.NULL_SEED, fp, v_null.shape)
    R["4_surrogates"] = dict(reused=False, draws=a.draws, settings=CHECK_NULL_SETTINGS, setup_seconds=setup, seconds_per_draw=(time.perf_counter() - t) / a.draws,
                             explained_variance_mean=float(np.mean(engine.explained_variance)), chosen_k=meta["chosen_k"],
                             sha256=meta["sha256"], peak_rss_gb=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6)
    del engine
store = C.SurrogateStore(store_path, fp)
S0 = store.draw(0)
R["4_surrogates"]["nan_pattern_preserved"] = bool(np.array_equal(np.isfinite(S0), np.isfinite(v_null)))
assert R["4_surrogates"]["nan_pattern_preserved"]
note(f"4 surrogates: {R['4_surrogates']}")
save()

# ---------------------------------------------------------------- 4b. standardisation sets (§7), recomputed separately
# Observed field: all eligible houses with a value. Surrogate field: the houses on null-field pixels, the only
# ones with a value in it. Houses are joined to pixels by their (pix_i, pix_j) key, not by the core's indices.
vf = C.load_field(field_path, geo)
pix_tab = pd.DataFrame({"pix_i": geo.pix_i, "pix_j": geo.pix_j, "col": np.arange(P)})
hp = h[["pix_i", "pix_j"]].merge(pix_tab, on=["pix_i", "pix_j"], how="left", validate="many_to_one")
assert hp.col.notna().all()
house_col = hp.col.to_numpy(np.int64)
null_keys = sorted(set(map(tuple, h.loc[h.complete_b1.astype(bool), ["pix_i", "pix_j"]].to_numpy().tolist())))
null_col = {k: n for n, k in enumerate(null_keys)}
house_keys = list(map(tuple, h[["pix_i", "pix_j"]].to_numpy().tolist()))
on_null = np.array([k in null_col for k in house_keys])
null_house_col = np.array([null_col[k] for k, o in zip(house_keys, on_null) if o], dtype=np.int64)
q_obs_sep = np.nanpercentile(vf[:, house_col], C.QS, axis=1)
q_sur_sep = np.nanpercentile(S0[:, null_house_col], C.QS, axis=1)
q_obs_core, q_sur_core = C.observed_quantiles(vf, geo), C.surrogate_quantiles(S0, geo)
q_obs_null_set = np.nanpercentile(vf[:, house_col[on_null]], C.QS, axis=1)
R["4b_standardisation_sets"] = dict(
    observed_set_houses=int(len(house_col)), surrogate_set_houses=int(on_null.sum()),
    observed_max_abs_diff=float(np.abs(q_obs_core - q_obs_sep).max()),
    surrogate_max_abs_diff=float(np.abs(q_sur_core - q_sur_sep).max()),
    observed_set_differs_from_null_set_windows=int((np.abs(q_obs_core - q_obs_null_set) > 0).any(axis=0).sum()))
assert len(null_keys) == len(geo.null_pixels) and on_null.sum() == len(geo.null_houses)
assert R["4b_standardisation_sets"]["observed_max_abs_diff"] < 1e-12
assert R["4b_standardisation_sets"]["surrogate_max_abs_diff"] < 1e-12
assert R["4b_standardisation_sets"]["observed_set_differs_from_null_set_windows"] > 0
note(f"4b standardisation sets: {R['4b_standardisation_sets']}")
save()

# ---------------------------------------------------------------- 5. the planted-signal script
common = ["--features", str(a.features), "--grid", str(a.grid), "--episodes", str(a.episodes),
          "--censoring", str(a.censoring), "--field", str(field_path)]
dates_path, q_path, run_dir = a.work / "event_dates.csv", a.work / "surrogate_quantiles.npy", a.work / "run"
PS.main(["event-dates"] + common + ["--events", str(a.events), "--out", str(dates_path)])
PS.main(["quantiles"] + common + ["--surrogates", str(store_path), "--out", str(q_path), "--workers", str(a.workers)])
run_args = common + ["--surrogates", str(store_path), "--quantiles", str(q_path), "--event-dates", str(dates_path),
                     "--workers", str(a.workers), "--datasets", "2", "--projection-hours", "72"]
PS.main(["run"] + run_args + ["--out", str(run_dir)])
PS.main(["summarise", "--out", str(run_dir)])
dinfo = json.loads(Path(str(dates_path) + ".json").read_text())
summary = json.loads((run_dir / "planted_signal_summary.json").read_text())
recs = {(r["cell"], r["dataset"]): r for r in (json.loads(f.read_text()) for f in sorted((run_dir / "records").glob("*.json")))}
R["5_run"] = dict(event_dates=dinfo, projection=summary["projection"],
                  per_dataset={f"cell{c}_ds{d}": dict(observed=r["observed"], p=r["p"], meets_rule=r["meets_rule"],
                                                     baseline=r["baseline_average_precision"], rows=r["rows"],
                                                     dropped=r["control_rows_dropped_missing_inputs"],
                                                     case_minus_candidate_term=r["diagnostics"]["case_term"] - r["diagnostics"]["candidate_term"],
                                                     case_minus_candidate_u=r["diagnostics"]["case_u"] - r["diagnostics"]["candidate_u"],
                                                     elapsed_seconds=r["elapsed_seconds"], null_seconds=r["null_seconds"])
                               for (c, d), r in sorted(recs.items())})
assert len(recs) == 12 and all(r["synthetic_events"] == dinfo["cases"] for r in recs.values())
# the planted term moves the draws in the planted direction
for d in (0, 1):
    assert recs[(2, d)]["diagnostics"]["case_term"] > recs[(2, d)]["diagnostics"]["candidate_term"]
    assert recs[(3, d)]["diagnostics"]["case_term"] > recs[(3, d)]["diagnostics"]["candidate_term"]
    # velocity tracks soil in the synthetic field, so compare the cases' mean velocity across cells:
    # it falls as the planted beta becomes more negative
    cu = [recs[(c, d)]["diagnostics"]["case_u"] for c in (1, 4, 5, 6)]
    assert cu[0] > cu[1] > cu[2] > cu[3], cu
    # the strongest planted effect reaches the minimum p and meets the rule
    assert recs[(6, d)]["observed"] > 0 and recs[(6, d)]["p"] == 1 / (1 + a.draws) and recs[(6, d)]["meets_rule"]
note("5 planted-signal script ran; planted directions and cell 6 detection as expected")
save()

# ---------------------------------------------------------------- 6. independent checks of two datasets
pa = argparse.Namespace(**{k: getattr(a, k) for k in ("features", "grid", "episodes", "censoring")},
                        field=field_path, coefficients=HERE / "generating_coefficients.json", event_dates=dates_path)
CTX = PS.build_context(pa, need_null=False)
# the planted model's u and the observed statistic use the observed field standardised over all eligible houses
U_sep = C.standardise(vf[:, house_col], np.arange(W)[:, None], q_obs_sep)
assert np.allclose(CTX["U"], U_sep, rtol=0, atol=1e-12, equal_nan=True)
dates = pd.read_csv(dates_path).t_e
first_ep = h.t_episode.to_numpy("datetime64[ns]")
dem = h.t_demolition.to_numpy("datetime64[ns]")
complete = h.complete_b1.to_numpy(bool)
HV = CTX["HV"]
checks6 = {}
for cell, ds in ((4, 0), (3, 1)):
    house, t_ep, _ = PS.synthetic_events(cell, ds)
    ev_dates = CTX["dates"]
    win = CTX["windows"]
    ok = dict(count_per_date=bool((pd.Series(ev_dates).value_counts().sort_index().values
                                   == pd.to_datetime(dates).value_counts().sort_index().values).all()),
              unique_houses=bool(len(np.unique(house)) == len(house)))
    # each case: complete, value in its window, no real episode before START, not demolished on/before t,
    # no synthetic event at an earlier position
    pos = {hh: k for k, hh in enumerate(house)}
    case_ok = []
    for k, (hh, t, w) in enumerate(zip(house, ev_dates, win)):
        pre = first_ep[hh] < np.datetime64("2018-08-01")
        case_ok.append(complete[hh] and HV[w, hh] and not pre and not (dem[hh] <= t) and pos[hh] == k)
    ok["cases_valid"] = bool(all(case_ok))
    # synthetic episode dates: real pre-study episodes plus the synthetic events, nothing else
    expect = np.where(first_ep < np.datetime64("2018-08-01", "ns"), first_ep, np.datetime64("NaT", "ns"))
    expect[house] = ev_dates
    ok["episode_dates"] = bool(np.array_equal(expect, t_ep, equal_nan=True))
    crng = np.random.default_rng(np.random.SeedSequence([PS.MASTER, cell, ds, C.CONTROL_SEED]))
    rows = C.risk_sets(house, ev_dates, win, t_ep, CTX["t_dem"], HV, crng)
    rh, rs, ry, rw, rd = rows["house"], rows["set"], rows["y"], rows["window"], rows["date"]
    ctrl = ry == 0
    case_of_set = house[rs]
    ok["set_sizes_51"] = bool((np.bincount(rs) == 51).all())
    ok["controls_not_case"] = bool((rh[ctrl] != case_of_set[ctrl]).all())
    ok["controls_unique_within_set"] = bool(pd.DataFrame({"s": rs, "h": rh}).duplicated().sum() == 0)
    ok["controls_have_value"] = bool(HV[rw[ctrl], rh[ctrl]].all())
    ok["controls_not_demolished"] = bool((~(dem[rh[ctrl]] <= rd[ctrl])).all())
    ok["controls_no_episode_on_or_before"] = bool((~(t_ep[rh[ctrl]] <= rd[ctrl])).all())
    later = ctrl & np.isin(rh, house)
    ok["some_controls_hold_a_later_synthetic_event"] = bool(later.any())
    kept, lost = C.drop_incomplete(rows, h)
    ok["dropped_equals_incomplete_controls"] = bool(lost == int((~complete[rh[ctrl]]).sum()))
    rec6 = recs[(cell, ds)]
    ok["rows_match_record"] = bool(len(kept["y"]) == rec6["rows"] and lost == rec6["control_rows_dropped_missing_inputs"])
    checks6[f"cell{cell}_ds{ds}"] = ok
    assert all(ok.values()), ok
R["6_independent"] = checks6
note(f"6 independent checks passed: {checks6}")
save()

# ---------------------------------------------------------------- 7. selection frequencies at one date
e = len(CTX["dates"]) // 2
t, w, dy = CTX["dates"][e], CTX["windows"][e], CTX["dec_dates"][e]
t_ep = CTX["t_ep_pre"]
idx = np.flatnonzero(complete & HV[w] & C.at_risk(t, t_ep, CTX["t_dem"]))
eta = CTX["eta_static"][idx] + CTX["age_coef"] * (dy - CTX["year_built"][idx] - CTX["age_mean"]) / CTX["age_scale"] - 0.4 * CTX["U"][w, idx]
prob = np.exp(eta - eta.max())
prob /= prob.sum()
r7 = np.random.default_rng(7)
n_draw = 400_000
picks = r7.choice(len(idx), size=n_draw, p=prob)
dec = pd.qcut(eta, 10, labels=False)
obs = np.bincount(dec[picks], minlength=10)
exp_ = np.array([prob[dec == k].sum() for k in range(10)]) * n_draw
chi = chisquare(obs, exp_)
R["7_selection"] = dict(date=str(pd.Timestamp(t).date()), candidates=len(idx), draws=n_draw, observed_by_eta_decile=obs.tolist(),
                        expected_by_eta_decile=exp_.round(1).tolist(), chi2=float(chi.statistic), p=float(chi.pvalue))
assert chi.pvalue > 0.001
note(f"7 selection frequencies: chi2 {chi.statistic:.1f}, p {chi.pvalue:.3f}")
save()

# ---------------------------------------------------------------- 8. reproducibility
rerun_dir = a.work / "rerun"
PS.main(["run"] + [x if x != str(a.workers) else "2" for x in run_args[:-4]] + ["--datasets", "1", "--projection-hours", "72",
        "--cells", "3", "4", "--out", str(rerun_dir)])
same = {}
for c in (3, 4):
    r1 = json.loads((run_dir / "records" / f"cell{c}_ds000.json").read_text())
    r2 = json.loads((rerun_dir / "records" / f"cell{c}_ds000.json").read_text())
    for r in (r1, r2):
        for k in ("elapsed_seconds", "null_seconds"):
            r.pop(k)
    same[f"cell{c}_ds0"] = r1 == r2
R["8_reproducible"] = same
assert all(same.values())
note(f"8 reruns identical: {same}")

# ---------------------------------------------------------------- 9. timing projection
per_stat = np.mean([r["null_seconds"] / r["draws"] for r in recs.values()])
overhead = np.mean([r["elapsed_seconds"] - r["null_seconds"] for r in recs.values()])
job = overhead + per_stat * 999
R["9_timing"] = dict(seconds_per_null_statistic=per_stat, seconds_outside_null=overhead, projected_job_seconds_999=job,
                     projected_hours_600_jobs={str(k): job * 600 / k / 3600 for k in (12, 16, 48, 96)},
                     note=f"measured with {a.workers} concurrent workers on this machine")
note(f"9 timing: {R['9_timing']}")
R["all_passed"] = True
R["seconds"] = time.perf_counter() - T0
save()
print(json.dumps(R, indent=1, default=float))
