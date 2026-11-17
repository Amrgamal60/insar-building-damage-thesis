"""Shared code for the NYC InSAR checks and models (NYC_REPLICATION_PLAN.md §7-§12). Imported by 10_insar_checks.py
and 11_models.py; settings follow the Alexandria scripts 07, 09, 10, 11 and 12, which are named where copied.

- Cells: the eligible cells of checkpoint 2 (features_<res>m.csv), in row-major order; a cell's index is its row there.
- Velocity fields: one row per window, one column per cell (NaN = no value), from out/insar/cells_<res>m.csv.gz.
- Standardisation (§7): per window, over all eligible cells with a value, subtract the landmass-group median, divide
  by the interquartile range, winsorise at the 0.5th and 99.5th percentiles.
- Risk sets (§8): one per (event cell, event date). Rules: "first" (primary), "earlier" (secondary 7: the earlier
  draft's rule, controls exclude only the case cell and cells with another event inside the window [t_e - length, t_e],
  every event is its own risk set, and an earlier event, inside or outside the window, does not stop a case) and
  "never" (secondary 11: controls never hold an event).
- Variogram-matching null (§10, Burt et al. 2020 as in Alexandria's 11_msr_variogram_check.py, burt_surrogates):
  one permutation, one k and one white-noise vector per draw, shared by every window; per-window rescaling.
  Runs on the GPU (CuPy) as a speed-up; the arithmetic is the same as the NumPy version."""
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

LENGTHS = {365: "2017-07-16", 730: "2018-07-16", 1095: "2019-07-16"}  # window length (days): first event date used
STATIC = ["built_share_2015", "old_share_1975", "height_m", "elevation_m", "dist_coast_km"]
B1 = ["built_share_2015", "old_share_1975", "height_m", "log_buildings", "elevation_m", "dist_coast_km", "x_km", "y_km"]
LR, RF = "logistic regression", "random forest"
N_FOLDS, TOP_SHARE, MAX_LAG = 5, 0.10, 16


# ---------------------------------------------------------------- data
def load_cells(cp2, res):
    return pd.read_csv(cp2 / f"features_{res}m.csv")


def load_fields(ins, res, cells, columns=("v", "v_linear", "v_nomask", "n_px")):
    """{column: DataFrame windows x cells} of the raw InSAR cell values (NaN where the cell has no value)."""
    t = pd.read_csv(ins / f"cells_{res}m.csv.gz")
    pos = pd.Series(np.arange(len(cells)), index=pd.MultiIndex.from_arrays([cells.row, cells.col]))
    t["cell"] = pos.reindex(pd.MultiIndex.from_arrays([t.row, t.col])).values
    out = {}
    for c in columns:
        m = t.pivot(index="window", columns="cell", values=c).reindex(columns=np.arange(len(cells)))
        if c == "n_px":
            m = m.where(m > 0)
        out[c] = m
    return out


def standardise(raw, landmass):
    """§7: per window, landmass-group median removed, divided by the IQR, winsorised at 0.5% / 99.5%."""
    out = raw.copy() * np.nan
    lm = np.asarray(landmass)
    for w, row in raw.iterrows():
        v = row.values.astype(float)
        z = np.full_like(v, np.nan)
        for g in np.unique(lm):
            m = (lm == g) & np.isfinite(v)
            z[m] = v[m] - np.median(v[m])
        ok = np.isfinite(z)
        q25, q75 = np.percentile(z[ok], [25, 75])
        z = z / (q75 - q25)
        lo, hi = np.percentile(z[ok], [0.5, 99.5])
        out.loc[w] = np.clip(z, lo, hi)
    return out


def releases(cp2):
    r = pd.read_csv(cp2 / "pluto_releases.csv")
    r = r[r.usable].sort_values("date")
    return r.release.values, pd.to_datetime(r.date).values


def event_release(dates, rel):
    names, rdates = rel
    k = np.searchsorted(rdates, pd.to_datetime(dates).values, side="left") - 1  # latest release dated before the date
    assert (k >= 0).all()
    return names[k]


def pluto_table(cp2, res, cells):
    """{release: (n_bldgs, median_yearbuilt) arrays over the cells}."""
    p = pd.read_csv(cp2 / f"pluto_cells_{res}m.csv")
    out = {}
    for rel, g in p.groupby("release"):
        g = cells[["row", "col"]].merge(g, on=["row", "col"], how="left")
        out[rel] = (g.n_bldgs.fillna(0).values, g.median_yearbuilt.values)
    return out


def event_cells(events, cells, res):
    """Index of the eligible cell holding each event point (x, y in UTM 18N), -1 if none."""
    x0 = float((cells.x - (cells.col + 0.5) * res).iloc[0])
    y0 = float((cells.y + (cells.row + 0.5) * res).iloc[0])
    r = np.floor((y0 - events.y.values) / res).astype(int)
    c = np.floor((events.x.values - x0) / res).astype(int)
    pos = pd.Series(np.arange(len(cells)), index=pd.MultiIndex.from_arrays([cells.row, cells.col]))
    return pos.reindex(pd.MultiIndex.from_arrays([r, c])).fillna(-1).to_numpy(dtype=int)


# ---------------------------------------------------------------- risk sets
def risk_sets(ev, cell_of, population, length, rule, has_value, base_ok):
    """List of dicts (window, date, pos, controls) and a dropped-event log.
    ev: events (event_id, date) for all 185 events; cell_of: their cell index (-1 = not an eligible cell).
    population: bool over cells; has_value(window) -> bool over cells; base_ok: bool over cells (static inputs)."""
    dates = pd.to_datetime(ev.date).values
    n = len(population)
    first = np.full(n, np.datetime64("NaT"), "datetime64[ns]")
    for c, d in sorted(zip(cell_of, dates), key=lambda t: t[1], reverse=True):
        if c >= 0:
            first[c] = d
    ever = ~np.isnat(first)
    start = np.datetime64(LENGTHS[length])
    sets, log, seen = [], [], set()
    for i in np.argsort(dates, kind="stable"):
        c, d, eid = cell_of[i], dates[i], ev.event_id.values[i]
        if d < start:
            continue
        w = f"{length}d_{pd.Timestamp(d).date()}"
        reason = None
        if c < 0:
            reason = "cell not eligible"
        elif not population[c]:
            reason = "cell not in the population"
        elif rule != "earlier" and first[c] < d:
            reason = "earlier event in the cell"
        elif rule != "earlier" and (c, d) in seen:
            reason = "same cell and date as another event (one risk set)"
        elif not has_value(w)[c]:
            reason = "no window value"
        elif not base_ok[c]:
            reason = "missing baseline input"
        log.append({"event_id": eid, "date": pd.Timestamp(d).date(), "cell": c, "window": w, "dropped": reason or ""})
        if reason:
            continue
        seen.add((c, d))
        ok = population & has_value(w) & base_ok
        if rule == "first":
            ok &= np.isnat(first) | (first > d)
        elif rule == "never":
            ok &= ~ever
        else:  # earlier draft: exclude cells with another event inside the window [t_e - length, t_e]
            lo = d - np.timedelta64(length, "D")
            inside = np.zeros(n, bool)
            m = (cell_of >= 0) & (dates >= lo) & (dates <= d)
            inside[cell_of[m]] = True
            ok &= ~inside
        ok[c] = False
        sets.append({"window": w, "date": d, "pos": c, "controls": np.flatnonzero(ok), "event_id": eid})
    return sets, pd.DataFrame(log)


def rows(sets, cells, pluto, rel, field, age=False):
    """Pooled (risk set, cell) rows: X (B1 [+ age]), velocity, y, cell, risk-set id, window id."""
    win_ids = {w: k for k, w in enumerate(sorted({s["window"] for s in sets}))}
    parts = []
    names = event_release([s["date"] for s in sets], rel)
    for k, (s, relname) in enumerate(zip(sets, names)):
        cc = np.r_[s["pos"], s["controls"]]
        nb, myb = pluto[relname]
        d = {"rs": k, "cell": cc, "y": np.r_[1, np.zeros(len(s["controls"]), int)], "win": win_ids[s["window"]],
             "log_buildings": np.log1p(nb[cc])}
        if age:
            d["age"] = pd.Timestamp(s["date"]).year - myb[cc]
        parts.append(pd.DataFrame(d))
    r = pd.concat(parts, ignore_index=True)
    for f in STATIC + ["x_km", "y_km"]:
        r[f] = cells[f].values[r.cell.values]
    wins = sorted(win_ids, key=win_ids.get)
    r["vel"] = field.loc[wins].values[r.win.values, r.cell.values]
    return r, wins


# ---------------------------------------------------------------- models and metrics (Alexandria 07 and 09)
def model(kind):
    if kind == LR:
        return make_pipeline(StandardScaler(), LogisticRegression(C=1.0, max_iter=5000))
    return RandomForestClassifier(n_estimators=500, min_samples_leaf=5, max_features="sqrt",
                                  class_weight="balanced_subsample", n_jobs=1, random_state=0)


def oof(X, y, fold, kind):
    s = np.full(len(y), np.nan)
    for k in range(N_FOLDS):
        tr, te = fold != k, fold == k
        if te.any() and y[tr].sum() > 0:
            s[te] = model(kind).fit(X[tr], y[tr]).predict_proba(X[te])[:, 1]
    return s


def recall_top(y, s, share=TOP_SHARE):
    k = max(1, int(round(share * len(s))))
    return y[np.argsort(-s, kind="stable")[:k]].sum() / y.sum()


def within_top(y, s, rs, share=TOP_SHARE):
    """Share of events whose cell ranks in the top 10% of its own risk set (ties count half)."""
    d = pd.DataFrame({"y": y, "s": s, "rs": rs})
    hits = []
    for _, g in d.groupby("rs"):
        sp = g.s.values[g.y.values == 1][0]
        rank = 1 + (g.s.values > sp).sum() + 0.5 * ((g.s.values == sp).sum() - 1)
        hits.append(rank <= max(1, int(round(share * len(g)))))
    return float(np.mean(hits))


def metrics(y, s, rs):
    return {"pr": average_precision_score(y, s), "roc": roc_auc_score(y, s), "top10": recall_top(y, s),
            "top10_rs": within_top(y, s, rs)}


def fold_map(cells, seed):
    """Alexandria's fold_map on all eligible cells: 2 km blocks, StratifiedGroupKFold(5, shuffle, seed)."""
    fold = np.full(len(cells), -1)
    for k, (_, te) in enumerate(StratifiedGroupKFold(n_splits=N_FOLDS, shuffle=True, random_state=seed)
                                .split(cells, cells.holds_event.values.astype(int), cells.block)):
        fold[te] = k
    return dict(zip(cells.block, fold))


# ---------------------------------------------------------------- variogram-matching null (GPU)
class Lags:
    """Cell pairs at lags 1..max_lag cell widths (lag = distance / cell size, rounded), as Alexandria's Lags."""

    def __init__(self, xy, res, max_lag=MAX_LAG):
        tree = cKDTree(xy)
        p = tree.query_pairs(r=(max_lag + 0.5) * res, output_type="ndarray")
        lag = np.rint(np.hypot(*(xy[p[:, 0]] - xy[p[:, 1]]).T) / res).astype(int)
        keep = (lag >= 1) & (lag <= max_lag)
        self.i, self.j, self.k, self.max_lag = p[keep, 0], p[keep, 1], lag[keep], max_lag

    def vario(self, s, valid=None):
        """Semivariance by lag of field s (n,) or fields (W, n); pairs need both cells valid."""
        s = np.atleast_2d(s)
        valid = np.ones_like(s, bool) if valid is None else np.atleast_2d(valid)
        out = np.full((len(s), self.max_lag), np.nan)
        for w in range(len(s)):
            vp = valid[w, self.i] & valid[w, self.j]
            num = np.bincount(self.k[vp], 0.5 * (s[w, self.i[vp]] - s[w, self.j[vp]]) ** 2, minlength=self.max_lag + 1)[1:]
            cnt = np.bincount(self.k[vp], minlength=self.max_lag + 1)[1:]
            out[w] = num / np.where(cnt > 0, cnt, np.nan)
        return out


class VariogramNull:
    """Shared variogram-matching surrogates for W windows over the union of cells U (§10).
    fields: (W, n) observed values on U, NaN where a window has no value. Draws are generated in order from one
    numpy Generator: per draw a permutation of U, then one standard-normal vector (Alexandria's order)."""

    def __init__(self, fields, xy, res, kmax=1000, max_lag=MAX_LAG):
        import cupy as cp
        import cupyx.scipy.sparse as csp
        self.cp = cp
        self.valid = np.isfinite(fields)
        n = fields.shape[1]
        self.n, self.W = n, len(fields)
        self.mean = np.array([f[v].mean() for f, v in zip(fields, self.valid)])
        med = np.array([np.median(f[v]) for f, v in zip(fields, self.valid)])
        filled = np.where(self.valid, fields, med[:, None])  # the window median, for the smoothing only
        self.z = cp.asarray(filled - self.mean[:, None])
        self.lags = Lags(xy, res, max_lag)
        self.target = self.lags.vario(fields, self.valid)  # (W, max_lag)
        self.ks = np.unique(np.geomspace(2, min(0.9 * n, kmax), 15).astype(int))
        dist, nbr = cKDTree(xy).query(xy, k=int(self.ks.max()) + 1)
        self.W_k = []
        for k in self.ks:
            dk, nk = dist[:, :k + 1], nbr[:, :k + 1]  # the cell itself and its k nearest cells
            w = np.exp(-dk / dk.max(1, keepdims=True))
            w = w / w.sum(1, keepdims=True)
            self.W_k.append(csp.csr_matrix((cp.asarray(w.ravel()), (cp.asarray(np.repeat(np.arange(n), k + 1)),
                                                                     cp.asarray(nk.ravel()))), shape=(n, n)))
        L = self.lags
        self.gi, self.gj = cp.asarray(L.i), cp.asarray(L.j)
        self.H = csp.csr_matrix((cp.ones(len(L.k)), (cp.arange(len(L.k)), cp.asarray(L.k - 1))), shape=(len(L.k), max_lag))
        vp = cp.asarray(self.valid[:, L.i] & self.valid[:, L.j]).astype(cp.float64)  # (W, P)
        self.vp = vp
        self.cnt = (self.H.T @ vp.T).T  # (W, max_lag)

    def _vario(self, S):
        """S: (W, n) cupy fields -> (W, max_lag) semivariance over each window's valid pairs."""
        cp = self.cp
        out = []
        for a in range(0, self.W, 16):
            d = S[a:a + 16][:, self.gi] - S[a:a + 16][:, self.gj]
            out.append((self.H.T @ (0.5 * d * d * self.vp[a:a + 16]).T).T / self.cnt[a:a + 16])
        return cp.concatenate(out)

    def draws(self, n_draws, rng):
        """Yields (surrogate fields (W, n) numpy with NaN where the window has no value, chosen k)."""
        cp = self.cp
        tgt, tbar = self.target, np.nanmean(self.target, 0)
        for _ in range(n_draws):
            perm = rng.permutation(self.n)
            x0 = self.z[:, cp.asarray(perm)]
            best = None
            for k, Wk in zip(self.ks, self.W_k):
                xs = (Wk @ x0.T).T
                g = cp.asnumpy(self._vario(xs))
                beta, alpha = np.polyfit(np.nanmean(g, 0), tbar, 1)
                sse = np.sum((tbar - alpha - beta * np.nanmean(g, 0)) ** 2)
                if best is None or sse < best[0]:
                    best = (sse, k, xs, g)
            _, k, xs, g = best
            eps = rng.standard_normal(self.n)
            xs = cp.asnumpy(xs)
            out = np.empty((self.W, self.n))
            for w in range(self.W):
                ok = np.isfinite(g[w]) & np.isfinite(tgt[w])
                beta, alpha = np.polyfit(g[w, ok], tgt[w, ok], 1)
                out[w] = self.mean[w] + np.sqrt(abs(beta)) * xs[w] + np.sqrt(abs(alpha)) * eps
            yield np.where(self.valid, out, np.nan), k


def fingerprint(a):
    """SHA-256 of an analysis's null fields, windows and union cells: a cached surrogate file is reused only if it matches."""
    import hashlib
    h = hashlib.sha256(np.ascontiguousarray(a["null_fields"], np.float64).tobytes())
    h.update("|".join(a["wins"]).encode())
    h.update(np.asarray(a["U"], np.int64).tobytes())
    return h.hexdigest()


def save_surrogate_meta(path, a):
    np.savez(path, wins=np.array(a["wins"]), U=np.asarray(a["U"]), fp=np.array(fingerprint(a)))


def remap(surr, fields):
    """Rank-remap each window's surrogate to that window's observed values (its valid cells only)."""
    out = np.full_like(surr, np.nan)
    for w in range(len(fields)):
        v = np.isfinite(fields[w])
        r = np.argsort(np.argsort(surr[w, v], kind="stable"), kind="stable")
        out[w, v] = np.sort(fields[w, v])[r]
    return out


# ---------------------------------------------------------------- analyses (§11, §12)
# key, label, cell size, population, window length, control rule, field, model, Baseline 2
ANALYSES = [
    ("primary", "Primary: domain, 250 m, logistic regression, Baseline 1, 1-year window", 250, "domain", 365, "first", "v", LR, False),
    ("s1", "1. Whole NYC (generalization)", 250, "whole", 365, "first", "v", LR, False),
    ("s2", "2. 200 m cells", 200, "domain", 365, "first", "v", LR, False),
    ("s3", "3. Random forest", 250, "domain", 365, "first", "v", RF, False),
    ("s4", "4. Baseline 2 (adds building age)", 250, "domain", 365, "first", "v", LR, True),
    ("s5", "5. 2-year window", 250, "domain", 730, "first", "v", LR, False),
    ("s6", "6. 3-year window", 250, "domain", 1095, "first", "v", LR, False),
    ("s7", "7. Earlier control rule", 250, "domain", 365, "earlier", "v", LR, False),
    ("s11", "11. Never-case control rule", 250, "domain", 365, "never", "v", LR, False),
    ("s12", "12. Linear-only velocity", 250, "domain", 365, "first", "v_linear", LR, False),
    ("s13", "13. No construction mask", 250, "domain", 365, "first", "v_nomask", LR, False),
    ("s14", "14. Availability only: log(1 + valid pixels)", 250, "domain", 365, "first", "n_px", LR, False),
    ("s15", "15. Ohenhen et al. 2025 VLM, static (exploratory)", 250, "domain", 365, "first", "ohenhen", LR, False),
]
SPEC = {a[0]: a for a in ANALYSES}


class Context:
    """Everything an analysis needs that does not depend on the outcome, loaded once per cell size."""

    def __init__(self, cp2, ins, raw, res):
        self.res = res
        self.cells = load_cells(cp2, res)
        self.cells["holds_event"] = self.cells.holds_event.astype(bool)
        raw_f = load_fields(ins, res, self.cells)
        lm = self.cells.landmass.values
        self.raw = raw_f["v"]
        self.fields = {"v": standardise(raw_f["v"], lm), "v_linear": standardise(raw_f["v_linear"], lm),
                       "v_nomask": standardise(raw_f["v_nomask"], lm), "n_px": np.log1p(raw_f["n_px"])}
        self.fields["ohenhen"] = self._ohenhen(raw)
        self.pluto = pluto_table(cp2, res, self.cells)
        self.rel = releases(cp2)
        self.base_ok = np.isfinite(self.cells[STATIC].values).all(1)
        self.fold = self.cells.block.map(dict(zip(self.cells.block, self.cells.fold))).values

    def _ohenhen(self, raw):
        """Mean of the Ohenhen et al. 2025 points in each cell, the same for every window (mm/yr, not standardised)."""
        from pyproj import Transformer
        o = pd.read_csv(raw / "ohenhen2025/newYork_VLM.csv")
        x, y = Transformer.from_crs("EPSG:4326", "EPSG:32618", always_xy=True).transform(o.longitude_deg.values, o.latitude_deg.values)
        c = event_cells(pd.DataFrame({"x": x, "y": y}), self.cells, self.res)
        ok = c >= 0
        cnt = np.bincount(c[ok], minlength=len(self.cells))
        v = np.where(cnt > 0, np.bincount(c[ok], o.VLM_mmPerYr.values[ok], minlength=len(self.cells)) / np.maximum(cnt, 1), np.nan)
        w = self.fields["v"].index
        return pd.DataFrame(np.tile(v, (len(w), 1)), index=w)


def prepare(key, ctx, events):
    """Risk sets and pooled rows of analysis `key` for an outcome (events: event_id, date, x, y for all 185)."""
    _, label, res, pop, length, rule, fname, kind, age = SPEC[key]
    cells, field = ctx.cells, ctx.fields[fname]
    population = cells.domain.values.astype(bool) if pop == "domain" else np.ones(len(cells), bool)
    windows = set(field.index)
    has = lambda w: (np.isfinite(field.loc[w].values) if w in windows else np.zeros(len(cells), bool))
    cell_of = event_cells(events, cells, res)
    sets, log = risk_sets(events, cell_of, population, length, rule, has, ctx.base_ok)
    r, wins = rows(sets, cells, ctx.pluto, ctx.rel, field, age=age)
    feats = B1 + (["age"] if age else [])
    missing_age_rows = 0
    if age:  # rows without a recorded year built in the event PLUTO are left out; so is a risk set that loses its event cell
        ok = np.isfinite(r.age.values)
        missing_age_rows = int((~ok).sum())
        lost = set(r.rs[(r.y == 1) & ~ok])
        r = r[ok & ~r.rs.isin(lost)].reset_index(drop=True)
        for k in lost:
            log.loc[log.event_id == sets[k]["event_id"], "dropped"] = "no building age at the event cell (Baseline 2)"
        sets = [s_ for k, s_ in enumerate(sets) if k not in lost]
    U = np.flatnonzero(population & np.isfinite(field.loc[wins].values).any(0))
    upos = np.full(len(cells), -1)
    upos[U] = np.arange(len(U))
    with_value = population & np.isfinite(field.loc[wins].values).any(0)
    return dict(key=key, label=label, res=res, kind=kind, sets=sets, log=log, rows=r, wins=wins, feats=feats,
                cells_missing_static=int((with_value & ~ctx.base_ok).sum()), rows_missing_age=missing_age_rows,
                U=U, upos=upos, null_fields=field.loc[wins].values[:, U], xy=cells[["x", "y"]].values[U],
                raw=ctx.raw.reindex(wins).values if fname == "v" else None)
