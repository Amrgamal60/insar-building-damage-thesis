"""Outcome-blind InSAR checks (NYC_REPLICATION_PLAN.md §7 "Before outcomes are joined", §10, §13 step 3).
No model is fitted and no InSAR value is compared with events.
1. Sign check: the full-period line-of-sight velocity of the 250 m cells crossed by the LaGuardia runways must be
   below the median of the eligible 250 m cells (motion away from the satellite); else work stops.
2. Coverage: per window, the eligible cells (and domain cells) with a value at 250 m and 200 m, the pixel losses by
   rule, and the raw velocity's median and IQR (which the standardisation removes); a coverage map.
3. Variogram check: the primary analysis's 999 variogram-matching surrogates (seed 2027, the ones the primary test will
   use; saved to out/models/real/surr_primary.npy) against the observed standardised field, for 20 of its windows
   chosen with seed 7: semivariance at lags 1-16 cell widths and in 1 km bins from 4 to 20 km. The windows of the primary
   analysis are its risk sets' event dates, which need the event dates and cells but no InSAR value at events.
Outputs: out/insar/INSAR_CHECKS.md, sign_check_result.csv, coverage_cells.csv, variogram_check.csv, insar_checks.png.
Usage (from feasibility/nyc): ../../.venv/bin/python -I scripts/10_insar_checks.py raw out"""
import importlib.util
import sys
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd
from pyproj import Transformer

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

RAW, OUT = Path(sys.argv[1]), Path(sys.argv[2])
CP2, INS, MOD = OUT / "checkpoint2", OUT / "insar", OUT / "models/real"
spec = importlib.util.spec_from_file_location("nyc_lib", Path(__file__).resolve().parent / "nyc_lib.py")
N = importlib.util.module_from_spec(spec)
spec.loader.exec_module(N)
N_SURR, NULL_SEED, CHECK_SEED, N_CHECK = 999, 2027, 7, 20
LONG_BINS_KM = np.arange(4, 21)  # 1 km bins (4, 5], ..., (19, 20]


def md(df):
    cols = list(df.columns)
    return "\n".join(["| " + " | ".join(map(str, cols)) + " |", "|" + "|".join("---" for _ in cols) + "|"] +
                     ["| " + " | ".join("" if (isinstance(v, float) and np.isnan(v)) else str(v) for v in r) + " |"
                      for r in df.itertuples(index=False)])


def events():
    ev = pd.read_csv(OUT / "events_final.csv")
    x, y = Transformer.from_crs("EPSG:4326", "EPSG:32618", always_xy=True).transform(ev.geo_lon.values, ev.geo_lat.values)
    return pd.DataFrame({"event_id": ev.event_id, "date": ev.date, "x": x, "y": y})


def sign_check(ctx):
    rw = pd.read_csv(INS / "sign_check.csv")
    full = ctx.raw.loc["full"].values
    city = float(np.nanmedian(full))
    lm = ctx.cells.landmass.values
    bq = float(np.nanmedian(full[lm == "Brooklyn+Queens"]))
    rv = rw.v.dropna()
    res = pd.DataFrame([{"Runway cells with a value": f"{len(rv)} of {len(rw)}",
                         "Runway cells: median LOS velocity (mm/yr)": f"{rv.median():+.2f}",
                         "Eligible cells: median (mm/yr)": f"{city:+.2f}",
                         "Brooklyn+Queens eligible cells: median (mm/yr)": f"{bq:+.2f}",
                         "Runway cells below the city median": f"{int((rv < city).sum())} of {len(rv)}",
                         "Result": "pass" if rv.median() < city else "FAIL"}])
    res.to_csv(INS / "sign_check_result.csv", index=False)
    return res, rv.median() < city


def coverage(ctx250, ctx200):
    cov = pd.read_csv(INS / "coverage.csv")
    rows = []
    for ctx in (ctx250, ctx200):
        f = ctx.fields["v"]
        dom = ctx.cells.domain.values
        has = np.isfinite(f.values)
        raw = ctx.raw.reindex(f.index).values
        for w, h, rv in zip(f.index, has, raw):
            rows.append({"window": w, "res": ctx.res, "eligible cells": len(h), "with a value": int(h.sum()),
                         "domain cells": int(dom.sum()), "domain with a value": int((h & dom).sum()),
                         "raw median": np.nanmedian(rv), "raw IQR": np.subtract(*np.nanpercentile(rv, [75, 25]))})
    t = pd.DataFrame(rows)
    t["length"] = t.window.str.split("d_").str[0]
    return t, cov


def gpu_vario(S, valid, i, j, k, nbins):
    import cupy as cp
    out = np.full((len(S), nbins), np.nan)
    for w in range(len(S)):
        vp = valid[w, i] & valid[w, j]
        num = cp.bincount(k[vp], weights=0.5 * (S[w, i[vp]] - S[w, j[vp]]) ** 2, minlength=nbins)
        cnt = cp.bincount(k[vp], minlength=nbins)
        out[w] = cp.asnumpy(num / cp.where(cnt > 0, cnt, cp.nan))
    return out


def variogram_check(ctx, ev):
    import cupy as cp
    from scipy.spatial import cKDTree
    a = N.prepare("primary", ctx, ev)
    fields, xy, res = a["null_fields"], a["xy"], ctx.res
    MOD.mkdir(parents=True, exist_ok=True)
    path = MOD / "surr_primary.npy"
    null = N.VariogramNull(fields, xy, res)
    if path.exists():
        surr = np.load(path)
        ks = pd.read_csv(MOD / "surr_primary_k.csv").k.values
    else:
        rng = np.random.default_rng(NULL_SEED)
        surr = np.empty((N_SURR,) + fields.shape, np.float32)
        ks = np.empty(N_SURR, int)
        for d, (s, k) in enumerate(null.draws(N_SURR, rng)):
            surr[d], ks[d] = s, k
            if d % 100 == 0:
                print("surrogate", d, "k", k, flush=True)
        np.save(path, surr)
        pd.DataFrame({"draw": np.arange(N_SURR), "k": ks}).to_csv(MOD / "surr_primary_k.csv", index=False)
    N.save_surrogate_meta(MOD / "surr_primary_meta.npz", a)
    pick = np.sort(np.random.default_rng(CHECK_SEED).choice(len(a["wins"]), N_CHECK, replace=False))
    # lag bins: 1..16 cell widths, then 1 km bins from 4 to 20 km
    p = cKDTree(xy).query_pairs(r=20_000, output_type="ndarray")
    dist = np.hypot(*(xy[p[:, 0]] - xy[p[:, 1]]).T)
    lag = np.rint(dist / res).astype(int)
    short = (lag >= 1) & (lag <= N.MAX_LAG)
    longb = np.searchsorted(LONG_BINS_KM * 1000, dist, side="left")  # (b-1, b] km -> bin index b - 4
    bins = np.where(short, lag - 1, np.where((dist > 4000) & (dist <= 20000), N.MAX_LAG + longb - 1, -1))
    keep = bins >= 0
    i, j, k = (cp.asarray(x[keep]) for x in (p[:, 0], p[:, 1], bins))
    nb = N.MAX_LAG + len(LONG_BINS_KM) - 1
    valid = cp.asarray(np.isfinite(fields[pick]))
    obs = gpu_vario(cp.asarray(np.nan_to_num(fields[pick])), valid, i, j, k, nb)
    sv = np.stack([gpu_vario(cp.asarray(np.nan_to_num(surr[d][pick].astype(float))), valid, i, j, k, nb) for d in range(N_SURR)])
    lo, hi, med = np.percentile(sv, 2.5, 0), np.percentile(sv, 97.5, 0), np.median(sv, 0)
    first = (N.MAX_LAG + 0.5) * res / 1000  # lag 16 takes the pairs up to 16.5 cell widths
    labels = [f"{(h + 1) * res / 1000:.2f} km" for h in range(N.MAX_LAG)] + [f"{max(b - 1, first):g}–{b} km" for b in LONG_BINS_KM[1:]]
    rows = []
    for wi, w in enumerate(pick):
        for b in range(nb):
            rows.append({"window": a["wins"][w], "bin": labels[b], "observed": obs[wi, b], "median": med[wi, b],
                         "2.5%": lo[wi, b], "97.5%": hi[wi, b], "inside": lo[wi, b] <= obs[wi, b] <= hi[wi, b]})
    t = pd.DataFrame(rows)
    t.to_csv(INS / "variogram_check.csv", index=False)
    return a, t, labels, ks, null.ks


def main():
    ev = events()
    ctx = {res: N.Context(CP2, INS, RAW, res) for res in (250, 200)}
    sres, ok = sign_check(ctx[250])
    print(sres.T.to_string())
    if not ok:
        sys.exit("Sign check failed: work stops (§7).")
    cov_t, cov_px = coverage(ctx[250], ctx[200])
    a, vt, labels, ks, offered = variogram_check(ctx[250], ev)

    # coverage summaries
    cs = cov_t.groupby(["res", "length"]).agg(windows=("window", "size"), eligible=("eligible cells", "first"),
                                               val_min=("with a value", "min"), val_med=("with a value", "median"),
                                               dom=("domain cells", "first"), dom_min=("domain with a value", "min"),
                                               dom_med=("domain with a value", "median"),
                                               raw_med_lo=("raw median", "min"), raw_med_hi=("raw median", "max"),
                                               iqr_lo=("raw IQR", "min"), iqr_hi=("raw IQR", "max")).reset_index()
    cs = cs[cs.length != "full"]
    cs_tab = pd.DataFrame({"Cell size": cs.res.map(lambda r: f"{r} m"), "Window (days)": cs.length, "Windows": cs.windows,
                           "Eligible cells with a value: min / median": [f"{a_:,.0f} / {b_:,.0f} of {c_:,}" for a_, b_, c_ in zip(cs.val_min, cs.val_med, cs.eligible)],
                           "Domain cells with a value: min / median": [f"{a_:,.0f} / {b_:,.0f} of {c_:,}" for a_, b_, c_ in zip(cs.dom_min, cs.dom_med, cs.dom)],
                           "Raw window median (mm/yr): range": [f"{a_:+.1f} to {b_:+.1f}" for a_, b_ in zip(cs.raw_med_lo, cs.raw_med_hi)],
                           "Raw IQR (mm/yr): range": [f"{a_:.1f} to {b_:.1f}" for a_, b_ in zip(cs.iqr_lo, cs.iqr_hi)]})
    cov_px = cov_px[cov_px.window != "full"].copy()
    cov_px["length"] = cov_px.window.str.split("d_").str[0]
    px = cov_px.groupby("length").agg(**{c: (c, "median") for c in cov_px.columns if c not in ("window", "length")}).reset_index()
    tot = px.pixels_in_eligible_250m_cells
    px_tab = pd.DataFrame({"Window (days)": px.length, "Pixels in eligible 250 m cells": tot.map(lambda v: f"{v:,.0f}"),
                           **{lab: (100 * px[c] / tot).map(lambda v: f"{v:.1f}%") for lab, c in
                              (("Masked at a reference change", "masked_at_reference_change"),
                               ("Component rule", "component_label_rule"), ("Completeness rule", "completeness_rule"),
                               ("Construction mask", "construction_mask"), ("Valid", "valid"))}})
    one = cov_t[(cov_t.res == 250) & (cov_t.length == "365")]
    f1 = ctx[250].fields["v"].loc[one.window.values]
    share = np.isfinite(f1.values).mean(0)
    pd.DataFrame({"row": ctx[250].cells.row, "col": ctx[250].cells.col, "share_of_1y_windows_with_value": share}).to_csv(INS / "coverage_cells.csv", index=False)

    # variogram check summaries
    vt["short"] = vt.bin.str.endswith("km") & ~vt.bin.str.contains("–")
    per_w = vt.groupby("window").apply(lambda g: pd.Series({
        "Lags 1–16 inside": f"{int(g.inside[g.short].sum())} of {int(g.short.sum())}",
        "1 km bins 4–20 km inside": f"{int(g.inside[~g.short].sum())} of {int((~g.short).sum())}",
        "Median / observed, lags 1–4": " · ".join(f"{x:.2f}" for x in (g.loc[g.short, "median"] / g.loc[g.short, "observed"]).values[:4]),
        "Median / observed, lags 5–16 (range)": f"{(g.loc[g.short, 'median'] / g.loc[g.short, 'observed']).values[4:].min():.2f}–{(g.loc[g.short, 'median'] / g.loc[g.short, 'observed']).values[4:].max():.2f}",
        "Outside, below the range": int((g.observed < g["2.5%"]).sum()), "Outside, above the range": int((g.observed > g["97.5%"]).sum())}),
        include_groups=False).reset_index()
    by_bin = vt.groupby("bin", sort=False).agg(inside=("inside", "mean"), ratio=("median", "median")).reset_index()
    ratio_obs = vt.groupby("bin", sort=False).apply(lambda g: np.median(g["median"] / g.observed), include_groups=False).values
    bin_tab = pd.DataFrame({"Lag": by_bin.bin, "Windows inside the 95% range": (by_bin.inside * N_CHECK).round().astype(int).map(lambda v: f"{v} of {N_CHECK}"),
                            "Surrogate median / observed (median over windows)": [f"{x:.2f}" for x in ratio_obs]})
    n_in_short = int(vt.inside[vt.short].sum()); n_short = int(vt.short.sum())
    n_in_long = int(vt.inside[~vt.short].sum()); n_long = int((~vt.short).sum())

    # figure
    fig, ax = plt.subplots(1, 3, figsize=(17, 5))
    cells = ctx[250].cells
    sc = ax[0].scatter(cells.x / 1000, cells.y / 1000, c=share, s=2.2, marker="s", cmap="viridis", vmin=0, vmax=1)
    fig.colorbar(sc, ax=ax[0], label="Share of 1-year windows with a value")
    ax[0].set(title="Coverage, eligible 250 m cells", xlabel="km east (UTM 18N)", ylabel="km north")
    ax[0].set_aspect("equal")
    full = ctx[250].raw.loc["full"].values
    lim = np.nanpercentile(np.abs(full - np.nanmedian(full)), 98)
    sc = ax[1].scatter(cells.x / 1000, cells.y / 1000, c=full, s=2.2, marker="s", cmap="RdBu_r",
                       vmin=np.nanmedian(full) - lim, vmax=np.nanmedian(full) + lim)
    rw = pd.read_csv(INS / "sign_check.csv")
    ax[1].plot(rw.x / 1000, rw.y / 1000, "k.", ms=3)
    fig.colorbar(sc, ax=ax[1], label="Full-period LOS velocity (mm/yr; + toward the satellite)")
    ax[1].set(title="Full period 2016-07 to 2022-08 (black dots: LaGuardia runway cells)", xlabel="km east")
    ax[1].set_aspect("equal")
    g = vt[vt.window == vt.window.iloc[0]]
    xs = np.arange(len(g))
    ax[2].fill_between(xs, g["2.5%"], g["97.5%"], color="tab:orange", alpha=0.3, label="surrogates 95% range")
    ax[2].plot(xs, g["median"], color="tab:orange", label="surrogates median")
    ax[2].plot(xs, g.observed, "o-", ms=3, color="tab:blue", label="observed")
    ax[2].set_xticks(xs[::4], g.bin.values[::4], rotation=45, fontsize=7)
    ax[2].set(ylabel="Semivariance (standardised units²)", title=f"Variogram check, window {g.window.iloc[0]}")
    ax[2].legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(INS / "insar_checks.png", dpi=120)
    plt.close(fig)

    lines = [
        "# InSAR checks before outcomes are joined",
        "",
        "**Plan:** `NYC_REPLICATION_PLAN.md` §7 (\"Before outcomes are joined\"), §10, §13 step 3. "
        "**Reproduce:** `~/miniforge3/envs/opera/bin/python -I scripts/09_insar_velocities.py raw out`, then "
        "`../../.venv/bin/python -I scripts/10_insar_checks.py raw out`. No model is fitted and no InSAR value is compared with events.",
        "",
        "## 1. Sign check (LaGuardia runways, full period, line of sight)",
        "",
        md(sres),
        "",
        "The runway cells are the 250 m cells crossed by the OSM centre lines of runways 13/31 and 04/22. Positive line of sight = toward the satellite.",
        "",
        "## 2. Coverage",
        "",
        "**Pixels** (median over windows; share of the pixels whose centre is in an eligible 250 m cell; each pixel is counted under the first rule it fails):",
        "",
        md(px_tab),
        "",
        "**Cells** with a value per window, and the raw (unstandardised) velocity's window median and IQR over eligible cells:",
        "",
        md(cs_tab),
        "",
        "The raw window velocities carry large offsets and spreads that change from window to window (no correction layers are "
        "applied, §7). The window standardisation of §7 removes each window's landmass medians and scales by its IQR, as planned.",
        "",
        f"## 3. Variogram check of the primary null ({N_SURR} surrogates, seed {NULL_SEED}; {N_CHECK} windows, seed {CHECK_SEED})",
        "",
        f"- **Primary analysis structure:** {len(a['wins'])} windows; {len(a['U']):,} domain cells with a value in any window "
        "(the null's union). Event counts and losses are reported with the results, not here.",
        f"- **Chosen neighbourhood k:** median {int(np.median(ks))} (2.5–97.5%: {int(np.percentile(ks, 2.5))}–{int(np.percentile(ks, 97.5))}); "
        f"offered {', '.join(map(str, offered))}.",
        f"- **Lags 1–16 cell widths:** observed inside the surrogates' 95% range at {n_in_short} of {n_short} window-lags; "
        f"**1 km bins from 4 to 20 km:** {n_in_long} of {n_long}.",
        "- Whatever this shows, the primary null is not changed (§10).",
        "",
        md(per_w),
        "",
        "**By lag, over the 20 windows:**",
        "",
        md(bin_tab),
        "",
        "Figure: `insar_checks.png` (coverage map, full-period velocity with the runway cells, one window's variogram check).",
        "",
    ]
    (INS / "INSAR_CHECKS.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
