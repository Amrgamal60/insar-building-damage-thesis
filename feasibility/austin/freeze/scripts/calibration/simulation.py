"""Fixed, synthetic-only Austin nuisance calibration generators (no file input)."""
import numpy as np
import pandas as pd
from scipy.ndimage import gaussian_filter
from scipy.optimize import brentq
from scipy.special import expit

import nyc_lib as N

FEATURES = ["age", "log_living_area", "log_lot_area", "soil", "slope", "elevation", "log_income"]


def z(a):
    a = np.asarray(a, dtype=float)
    return (a - a.mean()) / a.std()


def smooth(rng, shape, sigma):
    return z(gaussian_filter(rng.standard_normal(shape), sigma=sigma, mode="wrap"))


def city_a(config, seed, scenario, link, effect=0.):
    c = config["a"]
    rng = np.random.default_rng(seed)
    side = c["side_m"] // c["pixel_m"]
    shape = (side, side)
    chosen = np.sort(rng.choice(side*side, c["occupied_pixels"], replace=False))
    iy, ix = np.unravel_index(chosen, shape)
    xy = (np.column_stack([ix, iy]) + .5) * c["pixel_m"]
    def sf(sigma):
        return smooth(rng, shape, sigma / c["pixel_m"])[iy, ix]
    soil = 1 + 9 * expit(1.2 * sf(c["soil_gaussian_sigma_m"]))
    elevation = 180 + 35*sf(c["terrain_gaussian_sigma_m"])
    slope = np.exp(0.6*sf(450))
    bg = xy.astype(int) // c["income_polygon_side_m"]
    nbg = c["side_m"] // c["income_polygon_side_m"]
    income_grid = rng.normal(0, .3, (nbg, nbg))
    bg_id = bg[:, 0] + nbg*bg[:, 1]
    bg_soil = np.bincount(bg_id, weights=soil, minlength=nbg**2)/np.bincount(bg_id, minlength=nbg**2)
    income_grid += .15*z(bg_soil).reshape(nbg, nbg)
    log_income = np.log(65000) + income_grid[bg[:, 1], bg[:, 0]]
    age = np.clip(45 + 15*sf(c["age_gaussian_sigma_m"]), 5, 110)
    living = np.log(1800) + .2*z(log_income) + .2*rng.standard_normal(len(xy))
    lot = np.log(7500) + .15*z(age) + .3*rng.standard_normal(len(xy))
    pixel = np.r_[np.arange(len(xy)), rng.choice(len(xy), c["houses"]-len(xy), replace=True)]
    rng.shuffle(pixel)
    parcel_base = np.column_stack([age, living, lot, soil, slope, elevation, log_income])[pixel].copy()
    # Houses sharing a pixel can differ in building/lot characteristics.
    parcel_base[:, :3] += rng.normal(size=(len(pixel), 3))*np.array([3, .06, .08])
    counts = np.bincount(pixel, minlength=len(xy))
    pixel_cov = np.column_stack([np.bincount(pixel, weights=parcel_base[:, j], minlength=len(xy))/counts
                                 for j in range(parcel_base.shape[1])])
    zs = z(soil)
    tail_pixel = z(np.maximum(zs-.7, 0)**2)
    g = z(.85*zs + .6*tail_pixel + .2*z(slope) + .1*z(elevation) + .15*z(log_income))
    corr_g_soil = np.corrcoef(g, zs)[0, 1]
    rho = c["target_soil_correlations"][link]
    residual_scale = np.sqrt((corr_g_soil/rho)**2-1)
    W = c["windows"]
    monthly_s = np.array([sf(c["velocity_residual_sigma_m"]) for _ in range(W+23)])
    monthly_w = rng.standard_normal((W+23, len(xy)))
    stat_s = sf(c["velocity_residual_sigma_m"])
    stat_w = rng.standard_normal(len(xy))
    residual = []
    for w in range(W):
        rolling_s = monthly_s[w:w+24].sum(axis=0)/np.sqrt(24)
        rolling_w = monthly_w[w:w+24].sum(axis=0)/np.sqrt(24)
        spatial = np.sqrt(.7)*stat_s + np.sqrt(.3)*rolling_s
        white = np.sqrt(.7)*stat_w + np.sqrt(.3)*rolling_w
        residual.append(np.sqrt(.8)*spatial + np.sqrt(.2)*white)
    residual = np.asarray(residual)
    fields = g[None, :] + residual_scale*residual
    base_z = np.column_stack([z(col) for col in parcel_base.T])
    eta = base_z @ np.asarray(c["baseline_logit_coefficients"])
    if scenario in ("N2", "N4"):
        eta += c["nonlinear_tail_coefficient"]*tail_pixel[pixel]
    if scenario in ("N3", "N4"):
        eta += c["hidden_field_coefficient"]*sf(c["hidden_sigma_m"])[pixel]
    eta = np.broadcast_to(eta, (W, len(pixel))).copy()
    # Age is evaluated at each event month; other baseline inputs are time invariant.
    eta += .2*np.arange(W)[:, None]/(12*parcel_base[:, 0].std())
    if effect:
        eta += effect*residual[:, pixel]
    def cumulative(intercept):
        return (-np.expm1(np.log1p(-expit(intercept+eta)).sum(axis=0))).mean()
    intercept = brentq(lambda b: cumulative(b)-c["cumulative_event_probability"], -30, 5)
    # A 12-month stress experiment preserves the SIX-YEAR 4% cumulative rate.
    # Its monthly hazard is deliberately accelerated, not an Austin monthly rate.
    draws = rng.random(eta.shape) < expit(intercept+eta)
    first = np.where(draws.any(axis=0), draws.argmax(axis=0), W)
    day = rng.uniform(size=len(pixel))
    event_time = first + day
    cases = np.flatnonzero(first < W)
    cases = cases[np.argsort(event_time[cases], kind="stable")]
    eligible = pd.DataFrame({"block": (xy[pixel, 0]//2000).astype(int)
        + (c["side_m"]//2000)*(xy[pixel, 1]//2000).astype(int), "holds_event": first < W})
    fmap = N.fold_map(eligible, seed % (2**32-1))
    parcel_fold = eligible.block.map(fmap).to_numpy(dtype=int)
    controls_rng = np.random.default_rng(np.random.SeedSequence([seed, 2029]))
    houses, windows = [], []
    for case in cases:
        at_risk = np.flatnonzero(event_time > event_time[case])
        controls = controls_rng.choice(at_risk, c["controls"], replace=False)
        houses.extend(np.r_[case, controls].tolist())
        windows.extend([int(first[case])]*(1+c["controls"]))
    houses, windows = np.asarray(houses), np.asarray(windows)
    y = np.tile(np.r_[1, np.zeros(c["controls"], dtype=int)], len(cases))
    X = np.column_stack([parcel_base[houses], xy[pixel[houses]]/1000])
    X[:, 0] += windows/12
    fold = parcel_fold[houses]
    if len(np.unique(fold)) != 5 or any(y[fold != k].sum() == 0 for k in range(5)):
        raise RuntimeError("Unusable generated fold; do not discard/regenerate this seed")
    diagnostics = dict(events=int(len(cases)), houses=len(pixel), occupied_pixels=len(xy),
        rows=len(y), blocks=int(eligible.block.nunique()), intercept=float(intercept),
        soil_velocity_correlations=[float(np.corrcoef(f, soil)[0, 1]) for f in fields],
        adjacent_window_correlations=[float(np.corrcoef(fields[w], fields[w+1])[0, 1]) for w in range(W-1)],
        corr_g_soil=float(corr_g_soil), residual_scale=float(residual_scale),
        fold_events=[int(y[fold == k].sum()) for k in range(5)],
        shared_pixel_share=float((counts > 1).mean()), no_missing_inputs=True,
        risk_set_audit=True)
    assert all(np.all(event_time[houses[j+1:j+51]] > event_time[houses[j]]) for j in range(0, len(y), 51))
    return dict(fields=fields, xy=xy, pixel_cov=pixel_cov, pixel=pixel,
                X=X, y=y, fold=fold, row_pixel=pixel[houses], row_window=windows,
                rs=np.repeat(np.arange(len(cases)), 51), diagnostics=diagnostics)


def standardise_at_rows(fields, data):
    # Eligible PARCEL distribution, including multiplicity for shared pixels.
    eligible = fields[:, data["pixel"]]
    q = np.percentile(eligible, [.5, 25, 50, 75, 99.5], axis=1)
    scaled = (fields-q[2, :, None])/(q[3]-q[1])[:, None]
    lo = (q[0]-q[2])/(q[3]-q[1])
    hi = (q[4]-q[2])/(q[3]-q[1])
    scaled = np.clip(scaled, lo[:, None], hi[:, None])
    return scaled[data["row_window"], data["row_pixel"]]


def city_b(config, seed):
    c = config["b"]
    rng = np.random.default_rng(seed)
    shape = tuple(c["grid_shape"])
    iy, ix = np.indices(shape)
    xy = np.column_stack([ix.ravel(), iy.ravel()])*c["cell_m"] + c["cell_m"]/2
    ncell, Q = len(xy), c["quarters"]
    soil = smooth(rng, shape, 3).ravel()
    alpha = .35*soil + rng.normal(0, .25, ncell)
    exposure = rng.integers(c["initial_houses_low"], c["initial_houses_high"], ncell)
    initial = exposure.copy()
    hidden = smooth(rng, shape, c["hidden_field_sigma_cells"]).ravel()
    monthly = np.array([smooth(rng, shape, c["velocity_spatial_sigma_cells"]).ravel()
                        for _ in range(Q+3)])
    white = rng.normal(size=(Q+3, ncell))
    fields, rows = [], []
    for q in range(Q):
        hidden = .6*hidden + np.sqrt(1-.6**2)*smooth(rng, shape, c["hidden_field_sigma_cells"]).ravel()
        velocity = .6*soil + .8*(np.sqrt(.8)*monthly[q:q+4].sum(axis=0)/2
                                + np.sqrt(.2)*white[q:q+4].sum(axis=0)/2)
        fields.append(velocity)
        mu = exposure*np.exp(c["intercept"] + alpha + .25*np.sin(2*np.pi*q/8) + .5*hidden)
        y = np.minimum(exposure, rng.poisson(mu*rng.gamma(c["gamma_shape"], 1/c["gamma_shape"], ncell)))
        rows.append(pd.DataFrame(dict(cell=np.arange(ncell), quarter=q, y=y, n=exposure.copy(), v=velocity,
            block=(xy[:, 0]//2000).astype(int)+8*(xy[:, 1]//2000).astype(int))))
        exposure -= y
    panel = pd.concat(rows, ignore_index=True)
    if (panel.n <= 0).any():
        raise RuntimeError("Synthetic exposure exhausted; do not discard/regenerate seed")
    return dict(panel=panel, fields=np.asarray(fields), xy=xy,
                diagnostics=dict(cells=ncell, quarters=Q, events=int(panel.y.sum()),
                    initial_exposure=int(initial.sum()), final_exposure=int(exposure.sum()),
                    gamma_shape=c["gamma_shape"], velocity_effect=0))
