"""Test A primary analysis, shared core (AUSTIN_PLAN.md §7 standardisation, §8 shared at-risk rule,
§8A risk sets, §9 features, model, folds and metric, §10 p-value and surrogate file, §11 rule).

Written on 2026-11-10 at checkpoint 1, before any InSAR file was opened, for the planted-signal check
(§14). The decoy run (§13 step 4) and the real run (step 5) import this module unchanged. Its SHA-256 is
recorded in §15 with the planted-signal script. It reads no InSAR file by itself: the InSAR step writes
the field file (`save_field`) and the conditional-null surrogate file (`write_surrogates`) in the
formats fixed here.

Definitions fixed here, where the plan leaves the detail to the scripts:
- Houses: the eligible houses of checkpoint 1 (features_2018.parquet, eligible_grid_folds.parquet), in
  prop_id order. Every row index below is a position in that order.
- Pixels: the sorted unique (pix_i, pix_j) of the eligible houses (pixel edges at multiples of 30 m,
  checkpoint 1). The field file holds the trend velocity on all of them. The null field (§10) is the
  subset holding at least one house with complete Baseline 1 inputs; surrogates exist on it only.
- Standardisation sets (§7, "over all eligible parcels with a value", read literally as the user decided
  on 2026-11-10): per window, each house counted once (a pixel shared by several houses is weighted by them).
  The observed field is standardised over all eligible houses whose pixel has a value in it. A surrogate
  field has values on the null field only, so it is standardised over the eligible houses on null-field
  pixels with a value in it. Every analysis row lies on a null-field pixel, because its house has complete
  inputs.
- Windows: one per study month, 2018-08 to 2025-11 (88), in calendar order; an event takes the window of
  its calendar month (§7).
- Building age at a date: the decimal year of the date, year + (day of year - 1)/365.25, minus year built.
- Cases (§8A): events in order of date, then prop_id. An event is a case if its house is eligible, has
  complete Baseline 1 inputs, is not demolition-censored on or before the event date and has a value in
  the window. Dropped events are counted by reason.
- Controls (§8A): 50 per case, drawn without replacement by one generator, in case order, from the
  eligible houses (prop_id order) that have a value in the case's window and are at risk at the case date
  under the shared rule (§8), the case excluded. Control rows missing a Baseline 1 input are then dropped
  and counted ("draws lost to missing values", §8A; "missing inputs", §9).
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score

FROZEN = Path(__file__).resolve().parents[1] / "freeze" / "scripts"
if str(FROZEN) not in sys.path:
    sys.path.insert(0, str(FROZEN))
import nyc_lib as N  # noqa: E402  (frozen copy)

START, END = pd.Timestamp("2018-08-01"), pd.Timestamp("2025-11-30")
MONTHS = [str(p) for p in pd.period_range("2018-08", "2025-11", freq="M")]
STATIC = ["log_living_area", "log_lot_area", "lep_0_150", "slope_deg", "elevation_m", "log_income", "foundation_slab"]
B1 = ["building_age"] + STATIC + ["x_km", "y_km"]
NULL_COVARIATES = ["building_age"] + STATIC  # pixel means over complete houses, age at START; no coordinates (§10)
CONTROLS, CONTROL_SEED, FOLD_SEED = 50, 2029, 42
NULL_SEED, NULL_DRAWS = 2027, 999
NULL_SETTINGS = dict(kmax=1000, max_lag=16, chunk=8)
PIXEL_M = 30.0
QS = [0.5, 25, 50, 75, 99.5]
KEY = 1_000_000


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 24), b""):
            h.update(b)
    return h.hexdigest()


def decimal_year(t):
    t = pd.DatetimeIndex(np.atleast_1d(np.asarray(t, dtype="datetime64[ns]")))
    return (t.year + (t.dayofyear - 1) / 365.25).to_numpy(dtype=float)


def window_of(dates):
    """Index of each date's calendar month among MONTHS (-1 outside the study months)."""
    pos = {m: k for k, m in enumerate(MONTHS)}
    return np.array([pos.get(m, -1) for m in pd.DatetimeIndex(dates).strftime("%Y-%m")], dtype=np.int64)


# ---------------------------------------------------------------- houses and pixels
def load_houses(features, grid, episodes, censoring):
    """Eligible houses in prop_id order with Baseline 1 inputs, pixel, block, fold and the dates of the
    shared at-risk rule: first matched foundation episode (§4 rules 1-4 and 6, any date from 1980) and
    first total-demolition permit on or after 2018-08-01 (§5). NaT means none."""
    f, g = pd.read_parquet(features), pd.read_parquet(grid)
    assert f.prop_id.is_unique and f.prop_id.is_monotonic_increasing
    assert (f.prop_id.to_numpy() == g.prop_id.to_numpy()).all()
    assert (f.block.to_numpy() == g.block.to_numpy()).all() and (f.fold.to_numpy() == g.fold.to_numpy()).all()
    h = f[["prop_id", "year_built"] + STATIC + ["x_km", "y_km", "complete_b1", "block", "fold", "holds_event"]].copy()
    h["pix_i"], h["pix_j"] = g.pix_i.to_numpy(np.int64), g.pix_j.to_numpy(np.int64)
    complete = h[["year_built"] + STATIC + ["x_km", "y_km"]].notna().all(axis=1)
    assert (complete.to_numpy() == h.complete_b1.to_numpy()).all()
    ep, cens = pd.read_parquet(episodes), pd.read_parquet(censoring)
    assert ep.prop_id.is_unique and cens.prop_id.is_unique
    assert ep.prop_id.isin(set(h.prop_id)).all() and cens.prop_id.isin(set(h.prop_id)).all()
    h["t_episode"] = h.prop_id.map(ep.set_index("prop_id").t_first).astype("datetime64[ns]")
    h["t_demolition"] = h.prop_id.map(cens.set_index("prop_id").t_demolition).astype("datetime64[ns]")
    return h.reset_index(drop=True)


class Geometry:
    """Houses to pixels. pixel: index in the sorted unique pixels; null: index in the null field (-1 off)."""

    def __init__(self, h):
        i, j = h.pix_i.to_numpy(np.int64), h.pix_j.to_numpy(np.int64)
        assert (i >= 0).all() and (j >= 0).all() and (j < KEY).all()
        ukey, self.house_pixel = np.unique(i * KEY + j, return_inverse=True)
        self.pix_i, self.pix_j = ukey // KEY, ukey % KEY
        complete = h.complete_b1.to_numpy(bool)
        self.in_null = np.bincount(self.house_pixel, weights=complete, minlength=len(ukey)) > 0
        self.null_pixels = np.flatnonzero(self.in_null)
        pos = np.full(len(ukey), -1, dtype=np.int64)
        pos[self.null_pixels] = np.arange(len(self.null_pixels))
        self.house_null = pos[self.house_pixel]
        self.null_houses = np.flatnonzero(self.house_null >= 0)  # surrogate standardisation set before validity
        self.null_houses_pixel = self.house_null[self.null_houses]
        assert (self.house_null[complete] >= 0).all()

    def null_xy(self):
        return np.column_stack([self.pix_i[self.null_pixels] * PIXEL_M + PIXEL_M / 2,
                                self.pix_j[self.null_pixels] * PIXEL_M + PIXEL_M / 2])


def null_covariates(h, geo):
    """Pixel means of the Baseline 1 features without x/y over complete houses (§10), age at START."""
    c = h.complete_b1.to_numpy(bool)
    X = h.loc[c, STATIC].to_numpy(float)
    age = (decimal_year(START)[0] - h.loc[c, "year_built"].to_numpy(float))[:, None]
    X = np.column_stack([age, X])
    pix = geo.house_null[c]
    n = np.bincount(pix, minlength=len(geo.null_pixels))
    out = np.column_stack([np.bincount(pix, weights=X[:, k], minlength=len(geo.null_pixels)) / n for k in range(X.shape[1])])
    assert np.isfinite(out).all()
    return out


# ---------------------------------------------------------------- field and surrogate files
def save_field(path, v, geo, meta=None):
    """v: (88 windows, all eligible pixels) trend velocity, mm/yr, NaN where no value."""
    v = np.ascontiguousarray(v, dtype=np.float64)
    assert v.shape == (len(MONTHS), len(geo.pix_i))
    np.savez(path, months=np.array(MONTHS), pix_i=geo.pix_i, pix_j=geo.pix_j, v=v,
             meta=np.array(json.dumps(meta or {})))


def load_field(path, geo):
    with np.load(path, allow_pickle=False) as z:
        assert list(z["months"]) == MONTHS
        assert np.array_equal(z["pix_i"], geo.pix_i) and np.array_equal(z["pix_j"], geo.pix_j)
        v = np.asarray(z["v"], dtype=np.float64)
    assert v.shape == (len(MONTHS), len(geo.pix_i))
    return v


def null_fingerprint(v_null, geo):
    h = hashlib.sha256(np.ascontiguousarray(v_null, np.float64).tobytes())
    h.update("|".join(MONTHS).encode())
    h.update(np.ascontiguousarray(geo.pix_i[geo.null_pixels] * KEY + geo.pix_j[geo.null_pixels], np.int64).tobytes())
    return h.hexdigest()


def write_surrogates(path, engine, draws, seed, fingerprint, shape):
    """Draws of a null engine (draws(n, rng) -> (field, k)) written to float32 .npy (draws, W, P_null)
    with a meta JSON beside it. seed: the §10 seed (default_rng(seed)), as NYC."""
    path = Path(path)
    tmp = path.with_suffix(".tmp.npy")
    out = np.lib.format.open_memmap(tmp, mode="w+", dtype=np.float32, shape=(draws,) + tuple(shape))
    ks = []
    for d, (s, k) in enumerate(engine.draws(draws, np.random.default_rng(seed))):
        assert s.shape == tuple(shape)
        out[d] = s
        ks.append(int(k))
    assert len(ks) == draws
    out.flush()
    del out
    tmp.rename(path)
    meta = dict(fingerprint=fingerprint, draws=draws, seed=seed, months=MONTHS, shape=[draws] + list(shape),
                dtype="float32", chosen_k=ks, sha256=sha256(path))
    Path(str(path) + ".json").write_text(json.dumps(meta) + "\n")
    return meta


class SurrogateStore:
    def __init__(self, path, fingerprint, check_hash=True):
        self.path = Path(path)
        self.meta = json.loads(Path(str(path) + ".json").read_text())
        assert self.meta["fingerprint"] == fingerprint, "surrogates were not made from this field"
        assert self.meta["months"] == MONTHS
        if check_hash:
            assert sha256(self.path) == self.meta["sha256"]
        self.S = np.load(self.path, mmap_mode="r")
        assert list(self.S.shape) == self.meta["shape"] and self.S.dtype == np.float32
        self.draws = self.S.shape[0]

    def draw(self, d):
        return np.asarray(self.S[d], dtype=np.float64)


# ---------------------------------------------------------------- standardisation (§7)
def window_quantiles(values):
    """values: (W, n) field values of the standardisation set, NaN = no value. Percentiles QS per window."""
    q = np.empty((len(QS), values.shape[0]))
    for w, x in enumerate(values):
        x = x[np.isfinite(x)]
        q[:, w] = np.percentile(x, QS)
    return q


def observed_quantiles(v_all, geo):
    """v_all: (W, all eligible pixels) observed field; quantiles over all eligible houses with a value (§7)."""
    return window_quantiles(v_all[:, geo.house_pixel])


def surrogate_quantiles(S_null, geo):
    """S_null: (W, P_null) surrogate field, with values on the null field only; quantiles over the eligible
    houses with a value in it, which are the houses on null-field pixels (§7)."""
    return window_quantiles(S_null[:, geo.null_houses_pixel])


def standardise(raw, window, q):
    """Frozen arithmetic (calibration standardise_at_rows): (x - median) / IQR, clipped at the
    standardised 0.5th and 99.5th percentiles of the window."""
    iqr = q[3] - q[1]
    lo, hi = (q[0] - q[2]) / iqr, (q[4] - q[2]) / iqr
    return np.clip((raw - q[2][window]) / iqr[window], lo[window], hi[window])


# ---------------------------------------------------------------- shared at-risk rule (§8) and risk sets (§8A)
def at_risk(t, t_episode, t_demolition):
    """§8 at date t for eligible houses: not demolition-censored on or before t and no matched foundation
    episode on or before t. NaT = never. One function for Tests A and B."""
    t = np.datetime64(pd.Timestamp(t).to_datetime64(), "ns")
    return ~(t_demolition <= t) & ~(t_episode <= t)


def has_value_matrix(v_all, geo):
    """(W, houses) bool: the house's pixel has a value in the window."""
    return np.isfinite(v_all[:, geo.house_pixel])


def real_cases(events, h, HV):
    """§8A cases from real events (prop_id, t_first). Returns (cases: house, date, window; drop counts)."""
    ev = events[["prop_id", "t_first"]].sort_values(["t_first", "prop_id"], kind="stable").reset_index(drop=True)
    pos = pd.Series(np.arange(len(h)), index=h.prop_id)
    house = ev.prop_id.map(pos).fillna(-1).to_numpy(np.int64)
    date = ev.t_first.to_numpy("datetime64[ns]")
    win = window_of(date)
    assert (win >= 0).all(), "event outside the study months"
    reason = np.full(len(ev), "", dtype=object)
    ok = house >= 0
    reason[~ok] = "house not eligible"
    hh = np.where(ok, house, 0)
    assert (h.t_episode.to_numpy()[hh][ok] == date[ok]).all(), "event is not its house's first matched episode"
    m = ok & ~h.complete_b1.to_numpy(bool)[hh]
    reason[m & (reason == "")] = "missing Baseline 1 input"
    m = ok & (h.t_demolition.to_numpy()[hh] <= date)
    reason[m & (reason == "")] = "demolition-censored on or before the event date"
    m = ok & ~HV[win, hh]
    reason[m & (reason == "")] = "no value in the window"
    keep = reason == ""
    cases = pd.DataFrame({"house": house[keep], "date": date[keep], "window": win[keep]})
    return cases, pd.Series(reason[~keep]).value_counts().to_dict()


def risk_sets(case_house, case_date, case_window, t_episode, t_demolition, HV, rng, n_controls=CONTROLS):
    """§8A: per case, the case row and n_controls controls drawn without replacement from the houses with a
    value in the case's window that are at risk at the case date, the case excluded. Cases in the given
    order, one generator. Returns arrays (house, set, y, window, date) over rows."""
    houses, sets = [], []
    for k, (c, t, w) in enumerate(zip(case_house, case_date, case_window)):
        ok = HV[w] & at_risk(t, t_episode, t_demolition)
        ok[c] = False
        pool = np.flatnonzero(ok)
        controls = rng.choice(pool, n_controls, replace=False)
        houses.append(np.r_[c, controls])
        sets.append(np.full(n_controls + 1, k))
    house, rs = np.concatenate(houses), np.concatenate(sets)
    y = np.tile(np.r_[1, np.zeros(n_controls, dtype=np.int64)], len(case_house))
    return dict(house=house, set=rs, y=y, window=np.asarray(case_window)[rs], date=np.asarray(case_date)[rs])


def drop_incomplete(rows, h):
    """Rows missing a Baseline 1 input are left out (§9); a case row never is (cases are complete)."""
    ok = h.complete_b1.to_numpy(bool)[rows["house"]]
    assert ok[rows["y"] == 1].all()
    out = {k: v[ok] for k, v in rows.items()}
    return out, int((~ok).sum())


def design(h, house, date):
    """Baseline 1 + x/y (§9) at the rows, building age at the row's (case's) date. Column order B1."""
    age = decimal_year(date) - h.year_built.to_numpy(float)[house]
    X = np.column_stack([age, h[STATIC + ["x_km", "y_km"]].to_numpy(float)[house]])
    assert np.isfinite(X).all()
    return X


def fold_of_houses(h, holds_event, seed=FOLD_SEED):
    """§9 fold map: frozen nyc_lib.fold_map on all eligible houses in prop_id order, label 'house holds an
    event', groups = 2 km blocks of the pixel centre."""
    cells = pd.DataFrame({"block": h.block.to_numpy(), "holds_event": np.asarray(holds_event, dtype=bool)})
    fmap = N.fold_map(cells, seed)
    return h.block.map(fmap).to_numpy(np.int64)


# ---------------------------------------------------------------- statistic, p-value and rule (§9-§11)
def oof_ap(X, y, fold):
    s = N.oof(X, y, fold, N.LR)
    assert np.isfinite(s).all()
    return float(average_precision_score(y, s))


class TestA:
    """Change in pooled out-of-fold PR AUC (average precision) from Baseline 1 + x/y to Baseline 1 + x/y +
    standardised velocity, logistic regression (frozen nyc_lib.model), as the calibration's a_stat."""

    def __init__(self, X, y, fold):
        self.X, self.y, self.fold = X, y, fold
        self.baseline = oof_ap(X, y, fold)

    def delta(self, u):
        assert np.isfinite(u).all()
        return oof_ap(np.column_stack([self.X, u]), self.y, self.fold) - self.baseline


def p_value(observed, null):
    null = np.asarray(null, dtype=float)
    return (1 + int(np.sum(null >= observed))) / (1 + len(null))


def demonstrated(observed, p):
    """§11: a positive change and p < 0.05."""
    return bool(observed > 0 and p < 0.05)
