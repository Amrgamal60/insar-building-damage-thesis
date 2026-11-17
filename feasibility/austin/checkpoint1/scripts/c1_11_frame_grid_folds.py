"""Checkpoint 1 (AUSTIN_PLAN §5 frame clip and eligibility; §7 parcel pixel and Test B cells; §9 folds).

No InSAR file is opened. The frame's footprint and grid come from the public OPERA burst
database (github.com/opera-adt/burst_db, release v0.18.0, downloaded 2026-11-10):
- frame-geometries-simple: the footprint polygon of frame 28482 (longitude/latitude);
- frame-to-burst: the frame's EPSG code and its bounding box, snapped to 30 m.

Grid: the bounding box is snapped to multiples of 30 m, so pixel edges are taken at multiples
of 30 m in the frame's UTM zone and pixel centres at 30 k + 15 m. The pixel whose centre is
nearest a parcel point is then the pixel that contains it. THIS IS CHECKED AGAINST THE
COORDINATES OF THE FIRST GRANULE AT THE InSAR STEP; if the product grid differs, the pixel,
block and fold columns are rebuilt and the change is logged.

Eligible (§5): a population house whose parcel point lies inside the study area (already
applied in c1_03) and inside the frame footprint.
Block (§9): the 2 km block (UTM grid, edges at multiples of 2,000 m) of the pixel centre.
Cell (§7): the 250 m cell (edges at multiples of 250 m) of the parcel point.
Folds (§9): the frozen nyc_lib.fold_map (StratifiedGroupKFold, 5 folds, shuffle, seed 42) on
all eligible houses in prop_id order, label "house holds an event" (§4), groups = blocks.
"""
import argparse
import hashlib
import json
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import pyproj
import shapely
from shapely.ops import transform

p = argparse.ArgumentParser()
p.add_argument("--frame-dir", type=Path, required=True)
p.add_argument("--reference", type=Path, required=True)
p.add_argument("--events-private", type=Path, required=True)
p.add_argument("--frozen-scripts", type=Path, required=True)
p.add_argument("--out-private", type=Path, required=True)
p.add_argument("--out-json", type=Path, required=True)
a = p.parse_args()
a.out_private.mkdir(parents=True, exist_ok=False)
sys.path.insert(0, str(a.frozen_scripts))
import nyc_lib  # noqa: E402  (frozen copy)

FRAME = 28482
REL = "https://github.com/opera-adt/burst_db/releases/download/v0.18.0/"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


S = dict(frame=FRAME, source=REL, files={})
tables = {}
for name in ("opera-s1-disp-0.18.0-frame-to-burst.json.zip", "frame-geometries-simple-0.18.0.geojson.zip"):
    f = a.frame_dir / name
    S["files"][name] = dict(bytes=f.stat().st_size, sha256=sha(f))
    z = zipfile.ZipFile(f)
    tables[name] = json.load(z.open(z.namelist()[0]))
fb = tables["opera-s1-disp-0.18.0-frame-to-burst.json.zip"]
fr = fb["data"][str(FRAME)]
assert fr["epsg"] == 32614 and fb["metadata"]["snap"] == 30.0
for k in ("xmin", "ymin", "xmax", "ymax"):
    assert fr[k] % 30 == 0
S["frame_grid"] = dict(epsg=fr["epsg"], snap_m=fb["metadata"]["snap"], xmin=fr["xmin"], ymin=fr["ymin"], xmax=fr["xmax"], ymax=fr["ymax"],
                       bursts=len(fr["burst_ids"]), database_version=fb["metadata"]["version"])
feat = [x for x in tables["frame-geometries-simple-0.18.0.geojson.zip"]["features"] if x.get("id") == FRAME]
assert len(feat) == 1
to_utm = pyproj.Transformer.from_crs(4326, 32614, always_xy=True).transform
foot = transform(to_utm, shapely.geometry.shape(feat[0]["geometry"]))
S["frame_footprint"] = dict(orbit_pass=feat[0]["properties"]["orbit_pass"], area_km2=round(foot.area / 1e6, 1))

pop = pd.read_parquet(a.reference / "population_2018.parquet")
pts = shapely.points(pop.x.to_numpy(), pop.y.to_numpy())
shapely.prepare(foot)
pop["in_frame"] = shapely.within(pts, foot)
inbox = (pop.x >= fr["xmin"]) & (pop.x < fr["xmax"]) & (pop.y >= fr["ymin"]) & (pop.y < fr["ymax"])
S["frame_clip"] = dict(population_houses=len(pop), inside_frame_footprint=int(pop.in_frame.sum()),
                       outside_frame_footprint=int((~pop.in_frame).sum()), inside_frame_bounding_box=int(inbox.sum()),
                       nearest_distance_to_footprint_edge_km=round(float(shapely.distance(pts, foot.exterior).min()) / 1000, 2))
g = pop[pop.in_frame].sort_values("prop_id").reset_index(drop=True)
g["pix_i"] = np.floor(g.x / 30).astype("int64")
g["pix_j"] = np.floor(g.y / 30).astype("int64")
assert (g.pix_i == g.cell_x).all() and (g.pix_j == g.cell_y).all()
g["pix_cx"], g["pix_cy"] = 30.0 * g.pix_i + 15.0, 30.0 * g.pix_j + 15.0
g["block_x"] = np.floor(g.pix_cx / 2000).astype("int64")
g["block_y"] = np.floor(g.pix_cy / 2000).astype("int64")
g["block"] = g.block_x.astype(str) + "_" + g.block_y.astype(str)
g["cell250_x"] = np.floor(g.x / 250).astype("int64")
g["cell250_y"] = np.floor(g.y / 250).astype("int64")
g["cell250"] = g.cell250_x.astype(str) + "_" + g.cell250_y.astype(str)
point_block = np.floor(g.x / 2000).astype("int64").astype(str) + "_" + np.floor(g.y / 2000).astype("int64").astype(str)
per_pixel = g.groupby(["pix_i", "pix_j"]).size()
per_cell = g.groupby("cell250").size()
S["eligible"] = dict(houses=len(g), unique_pixels=int(len(per_pixel)), houses_sharing_a_pixel=int((per_pixel[per_pixel > 1]).sum()),
                     max_houses_in_a_pixel=int(per_pixel.max()), blocks_2km=int(g.block.nunique()),
                     houses_whose_point_block_differs_from_pixel_block=int((point_block != g.block).sum()),
                     cells_250m=int(len(per_cell)), cells_250m_with_3_or_more_houses=int((per_cell >= 3).sum()),
                     houses_per_250m_cell_median=float(per_cell.median()))

ev = pd.read_parquet(a.events_private / "foundation_events.parquet")
g["holds_event"] = g.prop_id.isin(set(ev.prop_id))
assert int(g.holds_event.sum()) == len(ev) - int((~ev.prop_id.isin(set(g.prop_id))).sum())
fmap = nyc_lib.fold_map(g, 42)
g["fold"] = g.block.map(fmap).astype("int64")
assert g.groupby("block").fold.nunique().max() == 1 and set(g.fold) == set(range(5))
again = nyc_lib.fold_map(g, 42)
assert again == fmap
S["folds"] = dict(function="nyc_lib.fold_map (frozen copy)", nyc_lib_sha256=sha(a.frozen_scripts / "nyc_lib.py"), seed=42, order="prop_id ascending",
                  events_at_eligible_houses=int(g.holds_event.sum()),
                  by_fold=[dict(fold=int(k), houses=int(len(x)), events=int(x.holds_event.sum()), blocks=int(x.block.nunique()))
                           for k, x in g.groupby("fold")])
cols = ["prop_id", "geo", "x", "y", "pix_i", "pix_j", "pix_cx", "pix_cy", "block_x", "block_y", "block", "cell250_x", "cell250_y", "cell250", "holds_event", "fold"]
g[cols].to_parquet(a.out_private / "eligible_grid_folds.parquet", index=False)
S["private_outputs_sha256"] = {"eligible_grid_folds.parquet": sha(a.out_private / "eligible_grid_folds.parquet")}
a.out_json.write_text(json.dumps(S, indent=1, default=int) + "\n")
print(json.dumps(S, indent=1, default=int))
