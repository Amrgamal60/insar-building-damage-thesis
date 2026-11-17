"""Acquisition-date displacement field for the temporal deep model (AUSTIN_PLAN.md §12 item 20; §15 "Item 20").

Input: i08's house_series.npz (each OPERA DISP product's displacement in mm, validity and connected-component flag at
the eligible house pixels, testa_core.Geometry order). Outcome-blind: no event, outcome, fold or block is read.

One chain from the first reference date, as opera-utils' rebase_timeseries (used by i08 per window): a product with
reference r and secondary date s gives cum(s) = cum(r) + displacement, where cum(r) is the chained value at the
product whose secondary date is r, and cum(first reference) = 0.
Authors' choice (registered in §15 before any outcome): where a pixel is invalid at a link product (the product
whose secondary date is a later reference date), rebase_timeseries would leave NaN for every later date. Here the
pixel's last finite chained value at or before that date is carried instead (0 if none). Within any §7 window that
has a value, i08 requires the pixel valid at every link inside the window's chain, so a carried value only shifts
that window's series by a constant, which the deep model's first-valid referencing removes; real rows are
unchanged. It keeps each date's field continuous for the registered temporal null, whose surrogates mix pixels.
Validity of a date at a pixel: the product's valid flag (recommended and water masks) and its connected-component
flag (§7 step 3). Rows: the 254 secondary dates in order; the first reference date (all zeros) is not a row.
"""
import hashlib

import numpy as np


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 24), b""):
            h.update(b)
    return h.hexdigest()


def build_field(series_path, pix_i, pix_j):
    """-> dates (datetime64[ns], 254), field (254, pixels) float64 with NaN where not valid, info dict."""
    with np.load(series_path, allow_pickle=False) as z:
        assert np.array_equal(z["pix_i"], pix_i) and np.array_equal(z["pix_j"], pix_j), "pixel order differs"
        ref = z["reference"].astype("datetime64[D]")
        sec = z["secondary"].astype("datetime64[D]")
        D = z["displacement_mm"].astype(np.float64)
        V, L = z["valid"].astype(bool), z["label_ok"].astype(bool)
    T, P = D.shape
    assert (np.diff(sec.astype(np.int64)) > 0).all(), "secondary dates not unique and increasing"
    assert (ref < sec).all() and np.isfinite(D[V]).all()
    root = ref.min()
    links = np.unique(ref[ref != root])
    link_product = {}
    for r in links:
        q = np.flatnonzero(sec == r)
        assert len(q) == 1, f"no single product ends at reference date {r}"
        link_product[r] = int(q[0])
    offset = {root: np.zeros(P)}
    carried = {}
    cum = np.full((T, P), np.nan)
    last = np.zeros(P)  # last finite chained value at or before the current product's date
    for p in range(T):
        r = ref[p]
        assert r in offset, f"reference {r} used before its link product"
        cum[p] = np.where(V[p], offset[r] + D[p], np.nan)
        last = np.where(np.isfinite(cum[p]), cum[p], last)
        if sec[p] in link_product:  # this product is a link: its chained value is the next reference's offset
            ok = np.isfinite(cum[p])
            offset[sec[p]] = np.where(ok, cum[p], last)
            carried[str(sec[p])] = int((~ok).sum())
    field = np.where(V & L, cum, np.nan)
    info = dict(source=str(series_path), source_sha256=sha256(series_path), dates=int(T), pixels=int(P),
                first_reference=str(root), reference_dates=int(len(links) + 1),
                pixels_carried_per_link=carried, pixels_carried_at_any_link=int((~V[list(link_product.values())]).any(0).sum()),
                valid_share=float(np.isfinite(field).mean()), dates_without_valid_pixel=int((~np.isfinite(field).any(1)).sum()))
    return sec.astype("datetime64[ns]"), field, info
