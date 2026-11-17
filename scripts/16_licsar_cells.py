"""LiCSAR velocity per grid cell, for the test in data/pilot/LICSAR_TEST_PLAN.md. No models.

Inputs: 15's vertical velocity (data/licsbas/decomposed/{P1,P2}_UD.geo.tif) and each frame's line-of-sight velocity
(data/licsbas/<frame>/velocity/P1.vel.geo.tif), in mm/yr, positive = up / towards the satellite; 07's cells.
Cell value = the mean of the valid pixels whose centres fall in the cell, on 07's grid; cells without one stay empty.
Also reported: the LiCSBAS processing per frame (from its info files), the coverage of the cells the test uses, and
the agreement of LiCSAR with Shirzaei velocity on the cells that have both (Spearman; the plan's secondary check 7,
descriptive).
Outputs: data/pilot/licsar_cells_<res>m.csv and LICSAR_CELLS.md."""
import importlib.util
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
import shapely
from pyproj import Transformer
from rasterio.transform import from_origin
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("stats09", ROOT / "scripts/09_core_statistics.py")
S = importlib.util.module_from_spec(spec)
spec.loader.exec_module(S)
P = S.P
LB = ROOT / "data/licsbas"
FRAMES = {"065D_05935_131108": "065D", "131A_05957_110910": "131A"}
LAYERS = {  # cell column: (GeoTIFF, label)
    "lic_ud_p1": (LB / "decomposed/P1_UD.geo.tif", "Vertical, P1 (primary)"),
    "lic_ud_p2": (LB / "decomposed/P2_UD.geo.tif", "Vertical, P2"),
    **{f"lic_los_{s}_p1": (LB / f / "velocity/P1.vel.geo.tif", f"{s} line of sight, P1") for f, s in FRAMES.items()},
}
READING = [  # written after the 2026-09-30 run
    "## Result",
    "",
    "- **Coverage is complete for the primary test.** All 241 of the Shirzaei test's core cells at 250 m, and all 32 of "
    "their collapse cells, have a LiCSAR vertical velocity, so no cell is dropped. 341 of the 416 core cells have one "
    "(all 34 collapse cells), as do 2,872 of the 3,300 eligible cells city-wide (all 50) and 345 of the Shirzaei test's "
    "347 cells at 200 m.",
    "- **Processing:** LiCSBAS kept 822 of 1,153 interferograms (065D) and 1,621 of 2,199 (131A). Step 15 kept 38–39% "
    "of the pixels with a time series; 20,575 pixels are valid in both frames. Both networks have gaps in 2015 (065D: "
    "October–November; 131A: June–September and October–November), which LiCSBAS bridges with its default linear "
    "constraint, so P1 (64 and 57 epochs) rests mainly on the connected stretch from November 2015 to December 2016.",
    "- **Agreement with Shirzaei (secondary check 7):** Spearman ρ = 0.81 city-wide (1,763 shared cells) and 0.77 in the "
    "core (241) for P1; 0.75 and 0.89 for P2. The medians differ (LiCSAR +0.5 and +2.5 mm/yr, Shirzaei −3.1) because "
    "LiCSAR is relative to each frame's reference point and Shirzaei is in IGS14; the tests use only differences "
    "between cells.",
    "",
]


def pixels(path):
    """Centres (UTM 36N) and values of the valid pixels."""
    with rasterio.open(path) as src:
        a, t = src.read(1), src.transform
        assert src.crs.is_geographic and t.b == t.d == 0
    r, c = np.nonzero(np.isfinite(a))
    x, y = Transformer.from_crs("EPSG:4326", P.CRS, always_xy=True).transform(t.c + (c + 0.5) * t.a, t.f + (r + 0.5) * t.e)
    return x, y, a[r, c].astype(float)


def aggregate(cells, res, x, y, v):
    """Mean and count of the pixel values per cell, using 07's grid (recovered from the cells' row, col and centre)."""
    x0 = np.unique(np.round(cells.x - (cells.col + 0.5) * res, 3))
    y0 = np.unique(np.round(cells.y + (cells.row + 0.5) * res, 3))
    assert len(x0) == len(y0) == 1, "cells are not on one grid"
    r, c = P.rowcol(from_origin(x0[0], y0[0], res, res), res, x, y)
    g = pd.DataFrame({"row": r, "col": c, "v": v}).groupby(["row", "col"]).v.agg(["mean", "count"])
    m = cells[["row", "col"]].merge(g, left_on=["row", "col"], right_index=True, how="left")
    return m["mean"].values, m["count"].fillna(0).astype(int).values


def read_list(path):
    return path.read_text().split() if path.exists() else []


def processing(frame):
    """What LiCSBAS did to one frame, from its info files."""
    ts = LB / frame / "TS_GEOCml1"
    pairs = read_list(ROOT / f"data/raw/insar_licsar/{frame}/interferograms.txt")
    bad11, bad12 = read_list(ts / "info/11bad_ifg.txt"), read_list(ts / "info/12bad_ifg.txt")
    used = read_list(ts / "info/13used_image.txt")
    par = dict(line.split(":", 1) for line in (ts / "info/EQA.dem_par").read_text().splitlines() if ":" in line)
    width, length = int(par["width"].split()[0]), int(par["nlines"].split()[0])
    kept = int((np.fromfile(ts / "results/mask", "float32") == 1).sum())
    inverted = int(np.isfinite(np.fromfile(ts / "results/vel", "float32")).sum())  # pixels with a step 13 time series
    with rasterio.open(LB / frame / "velocity/P1.vel.geo.tif") as s:
        p1 = np.isfinite(s.read(1)).sum()
    assert inverted <= width * length
    return {"Frame": frame, "Interferograms": len(pairs), "Dropped in step 11": len(bad11), "Dropped in step 12": len(bad12),
            "Epochs used": f"{len(used)} ({used[0]}–{used[-1]})" if used else "",
            "Epochs in P1": sum(int(d) <= 20161231 for d in used),
            "Pixels kept by step 15": f"{kept:,} of {inverted:,} with a time series ({kept / inverted:.0%}; box {width * length:,})",
            "Pixels with a P1 velocity": f"{p1:,}",
            "Reference (step 16)": (ts / "info/16ref.txt").read_text().strip() if (ts / "info/16ref.txt").exists() else ""}


def main():
    adm = gpd.read_file(P.RAW / "admin_geoboundaries/geoBoundaries-EGY-ADM2.geojson").to_crs(P.CRS)
    core = adm[adm.shapeName.isin(S.C8.CORE)].union_all()
    px = {k: pixels(p) for k, (p, _) in LAYERS.items()}
    cov, agree = [], []
    for res in P.RESOLUTIONS:
        cells = pd.read_csv(P.PILOT / f"cells_{res}m.csv")
        out = cells[["row", "col", "x", "y"]].copy()
        for k in LAYERS:
            out[k], out[f"{k}_n"] = aggregate(cells, res, *px[k])
        out.to_csv(P.PILOT / f"licsar_cells_{res}m.csv", index=False)
        c = cells.merge(out.drop(columns=["x", "y"]), on=["row", "col"])
        in_core = shapely.contains_xy(core, c.x.values, c.y.values)
        base = np.isfinite(c[P.BASELINE]).all(axis=1).values
        shz = (c.shz_n > 0).values & np.isfinite(c.shz_vlm).values
        for name, m in (("All eligible cells", np.ones(len(c), bool)), ("Historic core, cells with baseline inputs", in_core & base),
                        ("Historic core, Shirzaei-covered (Shirzaei test's cells)", in_core & base & shz)):
            y = c.positive.values[m]
            row = {"Cell size": f"{res} m", "Cells": name, "Count (collapse cells)": f"{m.sum():,} ({int(y.sum())})"}
            for k, (_, label) in LAYERS.items():
                ok = np.isfinite(c[k].values[m])
                row[label] = f"{ok.sum():,} ({int(y[ok].sum())})"
            row["Pixels per covered cell, vertical P1 (median)"] = f"{np.median(c.lic_ud_p1_n.values[m][c.lic_ud_p1_n.values[m] > 0]):.0f}"
            cov.append(row)
        for region, m in (("All eligible cells", np.ones(len(c), bool)), ("Historic core", in_core)):
            for k in ("lic_ud_p1", "lic_ud_p2"):
                ok = m & shz & np.isfinite(c[k].values)
                rho = spearmanr(c[k].values[ok], c.shz_vlm.values[ok]).statistic
                agree.append({"Cell size": f"{res} m", "Cells": region, "LiCSAR": LAYERS[k][1], "Shared cells": f"{ok.sum():,}",
                              "Spearman ρ with Shirzaei VLM": f"{rho:.2f}",
                              "Median, LiCSAR / Shirzaei (mm/yr)": f"{np.median(c[k].values[ok]):.1f} / {np.median(c.shz_vlm.values[ok]):.1f}"})
    proc, cov, agree = pd.DataFrame([processing(f) for f in FRAMES]), pd.DataFrame(cov), pd.DataFrame(agree)
    for t in (proc, cov, agree):
        print(t.to_string(index=False))
    lines = [
        "# LiCSAR velocity per cell",
        "",
        "**Plan:** `LICSAR_TEST_PLAN.md`. **Processing:** `scripts/15_licsbas_run.sh` (LiCSBAS steps 02 and 11–16, then P1/P2 "
        "velocity and the vertical decomposition). **Reproduce:** `.venv/bin/python scripts/16_licsar_cells.py` (after 07 and 15).",
        "",
        "- **P1** = first epoch to 2016-12-31 (primary); **P2** = full period. Linear fits to LiCSBAS's filtered cumulative "
        "displacement, masked by step 15. Vertical = both frames decomposed with their LOS unit vectors, assuming no "
        "north–south motion; mm/yr, positive up. The reference is each frame's own stable point, so absolute levels are "
        "arbitrary; the tests only use differences between cells.",
        "- **Cell value** = mean of the valid pixels (0.001°, about 95 × 111 m) whose centres fall in the cell, on the pilot's grid.",
        "",
        *READING,
        "## LiCSBAS processing",
        "",
        P.md_table(proc),
        "",
        "## Coverage (cells with a value; collapse cells in brackets)",
        "",
        P.md_table(cov),
        "",
        "## Agreement with Shirzaei velocity (secondary check 7, descriptive)",
        "",
        P.md_table(agree),
        "",
    ]
    (P.PILOT / "LICSAR_CELLS.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
