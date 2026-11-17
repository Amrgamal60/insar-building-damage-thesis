"""Checkpoint 2, first part (NYC_REPLICATION_PLAN.md §5, §6, §8). Builds the 250 m and 200 m grids, the landmass groups,
eligibility and the older-building domain from PLUTO 15v1, the borough boundaries and WSF Evolution. Then makes the
§6 event count that fixes the primary population. No InSAR is read.
Cells follow the Alexandria pilot (scripts/07_pilot_models.py): a grid aligned to multiples of the cell size, and
only lots whose point lies inside the study area count. Each landmass group is taken from the borough polygon holding the
cell centre, or the nearest borough polygon when the centre falls on water.
Usage (from feasibility/nyc): ../../.venv/bin/python -I scripts/04_grid_domain.py raw out"""
import math
import sys
import zipfile
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
import shapely
from pyproj import Transformer
from rasterio.transform import from_origin
from rasterio.transform import xy as pixel_xy
from rasterio.windows import from_bounds

RAW, OUT = Path(sys.argv[1]), Path(sys.argv[2]) / "checkpoint2"
CRS = "EPSG:32618"
RESOLUTIONS = [250, 200]  # primary first
START, MIN_EVENTS, PRE_WAR, MIN_LOTS = "2017-07-16", 30, 1940, 5
LANDMASS = {"Manhattan": "Manhattan", "Bronx": "Bronx", "Brooklyn": "Brooklyn+Queens", "Queens": "Brooklyn+Queens",
            "Staten Island": "Staten Island"}


def grid(area, res):
    minx, miny, maxx, maxy = area.bounds
    x0, y0 = math.floor(minx / res) * res, math.ceil(maxy / res) * res
    return from_origin(x0, y0, res, res), (math.ceil((y0 - miny) / res), math.ceil((maxx - x0) / res))


def rowcol(tr, res, x, y):
    return np.floor((tr.f - y) / res).astype(int), np.floor((x - tr.c) / res).astype(int)


def bincount(tr, shape, res, x, y, w=None):
    r, c = rowcol(tr, res, x, y)
    ok = (r >= 0) & (r < shape[0]) & (c >= 0) & (c < shape[1])
    flat = r[ok] * shape[1] + c[ok]
    return np.bincount(flat, weights=None if w is None else w[ok], minlength=shape[0] * shape[1]).reshape(shape)


def load_lots(area):
    """PLUTO 15v1 lots with a lot point inside the study area, in UTM 18N."""
    with zipfile.ZipFile(RAW / "pluto_15v1/nyc_pluto_15v1.zip") as z:
        lots = pd.concat([pd.read_csv(z.open(n), usecols=["Borough", "BBL", "NumBldgs", "YearBuilt", "XCoord", "YCoord"],
                                      low_memory=False) for n in ["Mn.csv", "BX.csv", "BK.csv", "QN.csv", "SI.csv"]])
    n_all = len(lots)
    num = ["NumBldgs", "YearBuilt", "XCoord", "YCoord"]  # 15v1 leaves missing values blank
    lots[num] = lots[num].apply(lambda s: pd.to_numeric(s.astype(str).str.strip(), errors="coerce"))
    lots = lots[(lots.XCoord > 0) & (lots.YCoord > 0)]
    x, y = Transformer.from_crs("EPSG:2263", CRS, always_xy=True).transform(lots.XCoord.values, lots.YCoord.values)
    lots = lots.assign(x=x, y=y)
    inside = shapely.contains_xy(area, lots.x.values, lots.y.values)
    info = {"lots": n_all, "with_point": len(lots), "in_area": int(inside.sum())}
    return lots[inside].reset_index(drop=True), info


def load_settled():
    """Centres of WSF Evolution pixels first mapped as settlement in 1985-2015, around NYC, in UTM 18N."""
    xs, ys = [], []
    for p in sorted((RAW / "wsf_evolution").glob("WSFevolution_v1_*.tif")):
        with rasterio.open(p) as s:
            w = from_bounds(-74.30, 40.45, -73.65, 40.95, s.transform).intersection(
                rasterio.windows.Window(0, 0, s.width, s.height)).round_offsets().round_lengths()
            yr = s.read(1, window=w)
            r_, c_ = np.nonzero((yr >= 1985) & (yr <= 2015))
            wx, wy = pixel_xy(s.window_transform(w), r_, c_)
            xs.append(np.asarray(wx)), ys.append(np.asarray(wy))
    x, y = Transformer.from_crs("EPSG:4326", CRS, always_xy=True).transform(np.concatenate(xs), np.concatenate(ys))
    return np.asarray(x), np.asarray(y)


def build_cells(res, area, boros, lots, settled_xy):
    tr, shape = grid(area, res)
    x, y = lots.x.values, lots.y.values
    yb = lots.YearBuilt.fillna(0).values
    nb = bincount(tr, shape, res, x, y, lots.NumBldgs.fillna(0).values.astype(float))
    n_lots = bincount(tr, shape, res, x, y)
    n_yb = bincount(tr, shape, res, x[yb > 0], y[yb > 0])
    n_pre = bincount(tr, shape, res, x[(yb > 0) & (yb < PRE_WAR)], y[(yb > 0) & (yb < PRE_WAR)])
    settled = bincount(tr, shape, res, *settled_xy) > 0
    rows, cols = np.nonzero(n_lots > 0)
    xc, yc = tr.c + (cols + 0.5) * res, tr.f - (rows + 0.5) * res
    centres = gpd.GeoDataFrame(geometry=gpd.points_from_xy(xc, yc), crs=CRS)
    near = gpd.sjoin_nearest(centres, boros[["boroname", "geometry"]], how="left")
    near = near[~near.index.duplicated()]  # a centre equidistant from two polygons keeps the first
    on_land = shapely.contains_xy(area, xc, yc)
    cells = pd.DataFrame({"row": rows, "col": cols, "x": xc, "y": yc,
                          "borough": near.boroname.values, "centre_on_land": on_land,
                          "n_lots": n_lots[rows, cols], "n_bldgs": nb[rows, cols].astype(int),
                          "n_lots_yearbuilt": n_yb[rows, cols], "n_lots_pre1940": n_pre[rows, cols],
                          "settled": settled[rows, cols]})
    cells["landmass"] = cells.borough.map(LANDMASS)
    cells["built_up"] = cells.n_bldgs >= 1
    cells["eligible"] = cells.built_up & cells.settled
    cells["domain"] = (cells.n_lots_yearbuilt >= MIN_LOTS) & (cells.n_lots_pre1940 > 0.5 * cells.n_lots_yearbuilt)
    return cells, tr


def event_flags(ev, cells, tr, res):
    r, c = rowcol(tr, res, ev.x.values, ev.y.values)
    e = pd.DataFrame({"event_id": ev.event_id, "date": ev.date, "row": r, "col": c})
    e = e.merge(cells[["row", "col", "eligible", "domain"]], on=["row", "col"], how="left")
    e[["eligible", "domain"]] = e[["eligible", "domain"]].fillna(False).astype(bool)
    first = e.groupby(["row", "col"]).date.transform("min")
    e["no_earlier_event"] = e.date == first
    e["shares_first_date"] = e.no_earlier_event & e.duplicated(["row", "col", "date"], keep=False)
    return e


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    boros = gpd.read_file(RAW / "boroughs/borough_boundaries.geojson").to_crs(CRS)
    area = boros.union_all()
    lots, linfo = load_lots(area)
    settled_xy = load_settled()
    ev = pd.read_csv(OUT.parent / "events_final.csv", dtype={"bbl": str, "bin": str})
    ex, ey = Transformer.from_crs("EPSG:4326", CRS, always_xy=True).transform(ev.geo_lon.values, ev.geo_lat.values)
    ev = ev.assign(x=ex, y=ey)

    yb = lots.YearBuilt.fillna(0)
    lines = ["# Checkpoint 2, part 1: grid, eligibility, domain and the §6 event count", "",
             "**Reproduce:** from `feasibility/nyc/`, `../../.venv/bin/python -I scripts/04_grid_domain.py raw out`. "
             "No InSAR value is read.", "",
             f"- **PLUTO 15v1 lots:** {linfo['lots']:,}; with a lot point {linfo['with_point']:,}; "
             f"point inside the study area {linfo['in_area']:,}.",
             f"- **Year built recorded (> 0):** {(yb > 0).sum():,} lots in the study area, of which "
             f"{((yb > 0) & (yb < PRE_WAR)).sum():,} were built before 1940. "
             f"Recorded values range from {int(yb[yb > 0].min())} to {int(yb.max())}.",
             f"- **WSF settled pixels (1985–2015) around NYC:** {len(settled_xy[0]):,}.", ""]
    rows, counts = [], {}
    for res in RESOLUTIONS:
        cells, tr = build_cells(res, area, boros, lots, settled_xy)
        cells.to_csv(OUT / f"cells_{res}m.csv", index=False)
        e = event_flags(ev, cells, tr, res)
        e.to_csv(OUT / f"event_cells_{res}m.csv", index=False)
        late = e.date >= START
        k_dom = int((late & e.eligible & e.domain & e.no_earlier_event).sum())
        k_all = int((late & e.eligible & e.no_earlier_event).sum())
        counts[res] = k_dom
        rows.append({"Cell size": f"{res} m", "Cells with a lot point": len(cells), "Built-up": int(cells.built_up.sum()),
                     "Eligible (built-up and settled)": int(cells.eligible.sum()),
                     "Eligible and in the domain": int((cells.eligible & cells.domain).sum()),
                     "Eligible cells with centre on water": int((cells.eligible & ~cells.centre_on_land).sum()),
                     "Events from 2017-07-16": int(late.sum()),
                     "… cell eligible": int((late & e.eligible).sum()),
                     "… and no earlier event in the cell (whole NYC)": k_all,
                     "… and in the domain (§6 count)": k_dom,
                     "First events sharing a cell and date": int((late & e.shares_first_date).sum())})
        if res == RESOLUTIONS[0]:
            land = cells[cells.eligible].groupby("landmass").agg(cells=("row", "size"), domain=("domain", "sum"))
    t = pd.DataFrame(rows).set_index("Cell size").T.reset_index().rename(columns={"index": ""})
    lines += ["| " + " | ".join(t.columns) + " |", "|" + "---|" * len(t.columns)]
    lines += ["| " + " | ".join(str(v) for v in r) + " |" for r in t.itertuples(index=False)]
    k = counts[RESOLUTIONS[0]]
    primary = "the older-building domain" if k >= MIN_EVENTS else "the whole of NYC (switch applied)"
    lines += ["", "**Eligible 250 m cells by landmass group:** " +
              "; ".join(f"{g} {int(r.cells):,} ({int(r.domain):,} in the domain)" for g, r in land.iterrows()) + ".", "",
              f"**§6 decision (250 m):** {k} events, so the primary population is **{primary}**. "
              f"The 200 m count ({counts[200]}) is reported only; the decision is made once, at 250 m.", ""]
    (OUT / "CHECKPOINT2_COUNT.md").write_text("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
