"""Study-area figure for the supervisor report. (a) The analysed built-up cells at 250 m, the 63 pilot collapses and
the historic core. (b) Shirzaei velocity in the core cells at 250 m, with the collapse cells outlined. Reads 06's
events, 07's cells and 09's core cells; no model fits. Output: data/report/fig_study_area.png."""
import importlib.util
from pathlib import Path

import geopandas as gpd
import matplotlib
import numpy as np
import pandas as pd
import shapely
from matplotlib.collections import PatchCollection
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Rectangle

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("stats09", ROOT / "scripts/09_core_statistics.py")
S = importlib.util.module_from_spec(spec)
spec.loader.exec_module(S)
P = S.P
OUT = ROOT / "data/report"
RES = 250
NAMES = dict(zip(S.C8.CORE, ["Karmouz", "Moharam Bek", "El Gomrok", "El Labban", "Attarin", "Manshiya", "Mina El-Basal"]))


def squares(xy, **kw):
    return PatchCollection([Rectangle((x - RES / 2, y - RES / 2), RES, RES) for x, y in xy], **kw)


def scalebar(ax, km):
    x0, x1 = ax.get_xlim()
    y0, y1 = ax.get_ylim()
    xs, ys = x0 + 0.05 * (x1 - x0), y0 + 0.05 * (y1 - y0)
    ax.plot([xs, xs + km * 1000], [ys, ys], color="k", lw=3, solid_capstyle="butt")
    ax.text(xs + km * 500, ys + 0.015 * (y1 - y0), f"{km} km", ha="center", va="bottom", fontsize=11)


def main():
    OUT.mkdir(exist_ok=True)
    adm = gpd.read_file(P.RAW / "admin_geoboundaries/geoBoundaries-EGY-ADM2.geojson").to_crs(P.CRS)
    study = adm[adm.shapeName.isin(P.DISTRICTS)]
    core = adm[adm.shapeName.isin(S.C8.CORE)]
    core_union = core.union_all()
    shore = gpd.read_file(P.RAW / "collapse_osf/Figures 4 and 5/2021.shp").to_crs(P.CRS)
    ev = pd.read_csv(P.PILOT / "target_events.csv")
    cells = pd.read_csv(P.PILOT / f"cells_{RES}m.csv")
    cc = S.core_cells(RES, adm)
    in_core = shapely.contains_xy(core_union, ev.x_utm36.values, ev.y_utm36.values)

    fig, ax = plt.subplots(2, 1, figsize=(10, 12.5), gridspec_kw={"height_ratios": [1.15, 1]})
    a = ax[0]
    a.add_collection(squares(cells[["x", "y"]].values, facecolor="0.86", edgecolor="none"))
    study.boundary.plot(ax=a, color="0.6", lw=0.5)
    gpd.GeoSeries([core_union], crs=P.CRS).boundary.plot(ax=a, color="k", lw=1.6)
    shore.plot(ax=a, color="tab:blue", lw=0.9)
    a.scatter(ev.x_utm36, ev.y_utm36, s=16, c="tab:red", edgecolor="white", linewidth=0.4, zorder=5)
    a.set_xlim(cells.x.min() - 1500, cells.x.max() + 1500)
    a.set_ylim(cells.y.min() - 1500, cells.y.max() + 1500)
    a.set_aspect("equal")
    a.set_axis_off()
    scalebar(a, 5)
    a.set_title(f"(a) {len(ev)} pilot collapses, 2014–2016: {int(in_core.sum())} in the historic core", fontsize=14, loc="left")
    a.legend(handles=[Line2D([], [], marker="o", ls="", color="tab:red", label="Pilot collapse"),
                      Line2D([], [], color="k", lw=1.6, label="Historic core (7 districts)"),
                      Patch(facecolor="0.86", label=f"Built-up cells settled by 2015 ({RES} m)"),
                      Line2D([], [], color="0.6", lw=0.8, label="District boundary"),
                      Line2D([], [], color="tab:blue", lw=0.9, label="Shoreline, 2021")],
             loc="lower right", fontsize=11, frameon=False)

    b = ax[1]
    pc = squares(cc[["x", "y"]].values, cmap="magma", edgecolor=np.where(cc.positive, "k", "none").tolist(), linewidth=1.4)
    pc.set_array(cc.shz_vlm.values)
    pc.set_clim(-8, cc.shz_vlm.max())
    b.add_collection(pc)
    core.boundary.plot(ax=b, color="0.45", lw=0.6)
    gpd.GeoSeries([core_union], crs=P.CRS).boundary.plot(ax=b, color="k", lw=1.2)
    for name, geom in zip(core.shapeName, core.geometry):
        p = geom.representative_point()
        b.text(p.x, p.y, NAMES[name], fontsize=10, ha="center", va="center", color="0.15",
               bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.55))
    x0, y0, x1, y1 = core_union.bounds
    b.set_xlim(x0 - 300, x1 + 300)
    b.set_ylim(y0 - 300, y1 + 300)
    b.set_aspect("equal")
    b.set_axis_off()
    scalebar(b, 1)
    b.set_title(f"(b) Historic core: {RES} m cells with InSAR points\nblack outline = cell with a pilot collapse", fontsize=14, loc="left")
    cb = fig.colorbar(pc, ax=b, extend="min", shrink=0.8)
    cb.set_label("Shirzaei vertical land motion (mm/yr), clipped at −8", fontsize=11)
    fig.tight_layout()
    fig.savefig(OUT / "fig_study_area.png", dpi=200)
    plt.close(fig)
    print(f"{len(ev)} events, {int(in_core.sum())} in the core; {len(cc)} core cells, {int(cc.positive.sum())} collapse cells")


if __name__ == "__main__":
    main()
