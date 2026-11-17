"""Sanity-check map of the located events (data/inventory/geocoded_events_map.png): whole city and the
historic core, over a 25% sample of Google Open Buildings v3 centroids and the ADM2 district outlines."""
from pathlib import Path

import duckdb
import geopandas as gpd
import matplotlib
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
CRS = 32636
DISTRICTS = ["Al Attarin", "Mina Al-Basal", "Muharam Bik", "Sidi Gabir", "Al Dikhila", "Muntazah", "Al Raml",
             "Kesm than Al Raml", "Al Gumruk", "A L Labban", "Karmuz", "Bab Sharqi", "Al Manshiyya", "Al Amreia"]
STYLE = [("A_street", "tab:blue"), ("A_intersection", "navy"), ("B_street_review", "tab:orange"),
         ("B_street_overture", "tab:red"), ("C_landmark", "tab:green"), ("C_neighbourhood", "tab:green")]
VIEWS = [((185000, 230000), (3432000, 3470000)), ((201000, 212000), (3450500, 3459500))]


def main():
    adm = gpd.read_file(ROOT / "data/raw/admin_geoboundaries/geoBoundaries-EGY-ADM2.geojson").to_crs(CRS)
    a = adm[adm.shapeName.isin(DISTRICTS)]
    b = duckdb.sql("select longitude, latitude from read_csv_auto('" + str(ROOT / "data/interim/google_buildings_v3_alex.csv") +
                   "') using sample 25% (bernoulli, 1)").df()
    bp = gpd.GeoSeries(gpd.points_from_xy(b.longitude, b.latitude), crs=4326).to_crs(CRS)
    ev = pd.read_csv(ROOT / "data/inventory/events.csv")
    ev = ev[ev.x_utm36.notna()]
    fig, axs = plt.subplots(1, 2, figsize=(16, 8))
    for ax, (xl, yl) in zip(axs, VIEWS):
        ax.scatter(bp.x, bp.y, s=0.05, c="0.8", rasterized=True)
        a.boundary.plot(ax=ax, color="0.4", lw=0.6)
        for cat, c in STYLE:
            e = ev[ev.loc_category == cat]
            ax.scatter(e.x_utm36, e.y_utm36, s=14, c=c, label=f"{cat} ({len(e)})", edgecolor="k", lw=0.3)
        ax.set_xlim(xl)
        ax.set_ylim(yl)
        ax.set_aspect("equal")
    axs[1].legend(loc="lower right", fontsize=8)
    for _, r in a.iterrows():
        p = r.geometry.representative_point()
        axs[0].text(p.x, p.y, r.shapeName, fontsize=6)
    plt.tight_layout()
    plt.savefig(ROOT / "data/inventory/geocoded_events_map.png", dpi=110)


if __name__ == "__main__":
    main()
