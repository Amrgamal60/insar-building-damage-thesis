"""Secondary check 6 of data/pilot/LICSAR_TEST_PLAN.md: 08's location checks (feature sets A-D) with LiCSAR vertical
velocity P1 in place of Shirzaei velocity. Reported; no decision is attached.

Cells: 07's eligible cells with all baseline inputs and a LiCSAR value (no Shirzaei condition). Regions: the full area
and the historic core. Folds: the primary assignment (seed 42) and 08's 10 other assignments, rebuilt with 07's
fold_map on all eligible cells, as 08 did. Models, feature sets and metrics as 08.
Outputs: data/pilot/location_checks_licsar_<res>m.csv and LICSAR_LOCATION_CHECKS.md."""
import importlib.util
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import shapely
from sklearn.metrics import average_precision_score, roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("checks", ROOT / "scripts/08_location_checks.py")
C8 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(C8)
P = C8.P

VEL = "lic_ud_p1"
SETS = {"A": P.BASELINE, "B": P.BASELINE + ["x_km", "y_km"], "C": P.BASELINE + [VEL], "D": P.BASELINE + ["x_km", "y_km", VEL]}
READING = [  # written after the 2026-09-30 run
    "## Result",
    "",
    "- **Full area: velocity adds nothing once location is controlled, as with Shirzaei.** Logistic regression: PR AUC "
    "−0.003 without x/y and +0.002 with (the same at 200 m). The random forest gains PR AUC without x/y (+0.010 at 250 m, "
    "+0.077 at 200 m), but with x/y the gain is +0.014 and +0.018 and ROC AUC does not rise (5 and 2 of 10 splits), so "
    "the city-wide gain is location.",
    "- **Historic core: velocity adds in the linear model at both sizes.** At 250 m, PR AUC +0.067 without x/y and +0.093 "
    "with, ROC AUC +0.043 and +0.045, in 10 of 10 splits each (Shirzaei: PR +0.071 and +0.052). At 200 m, on 510 cells, "
    "the gains are smaller: PR +0.027 (9 of 10) and +0.030 (10 of 10), ROC +0.026 and +0.025 (10 of 10); Shirzaei gave "
    "+0.068 on its 347 cells. The random forest adds in the core at 250 m (PR +0.063 and +0.048, 10 of 10) but not at "
    "200 m, as with Shirzaei.",
    "- **Outside the core the direction is reversed, which reflects a difference between the products.** In the core "
    "the collapse cells' median is below the background's (250 m: 0.06 vs 0.35 mm/yr). Outside it is above (2.21 vs "
    "−0.63; single-layer ROC AUC 0.80). On the 1,522 cells outside the core that have both products, LiCSAR gives "
    "2.26 vs 0.43 and Shirzaei −3.12 vs −3.10, so Shirzaei shows no difference. Five of the 16 outside collapse cells are "
    "in Bab Sharqi, which LiCSAR shows moving up relative to the frame references (district median +2.4 mm/yr) and "
    "Shirzaei moving down (−2.3). District medians of the two products differ by about 0 (Kesm than Al Raml) to "
    "5.7 mm/yr (Al Raml). This is a long-wavelength difference: the LiCSAR run has no GNSS tie, atmospheric correction "
    "or deramping. Outside the core, LiCSAR velocity therefore mostly marks location, and x/y removes it.",
    "- **Reading:** as with Shirzaei, the velocity result is confined to the historic core; city-wide, velocity adds "
    "nothing beyond location. The long-wavelength differences do not explain the core result, which compares cells "
    "inside the core with x/y controlled and also passes the within-block (2 km) null (`LICSAR_TEST.md`).",
    "",
]


def load(res, adm):
    cells = pd.read_csv(P.PILOT / f"cells_{res}m.csv")
    assert (cells.block.map(P.fold_map(cells, seed=P.SEED)) == cells.fold).all(), "fold map differs from 07"
    cells = cells.merge(pd.read_csv(P.PILOT / f"licsar_cells_{res}m.csv")[["row", "col", VEL]], on=["row", "col"], how="left")
    cells["x_km"], cells["y_km"] = cells.x / 1000, cells.y / 1000
    cells["core"] = shapely.contains_xy(adm[adm.shapeName.isin(C8.CORE)].union_all(), cells.x.values, cells.y.values)
    return cells


def run(res, adm):
    cells = load(res, adm)
    cov = cells[np.isfinite(cells[P.BASELINE + [VEL]]).all(axis=1)]
    rows = []
    for sd in [C8.PRIMARY] + C8.ALT:
        fm = P.fold_map(cells, seed=sd)
        for region, c in (("full area", cov), ("historic core", cov[cov.core])):
            y, fold = c.positive.values.astype(int), c.block.map(fm).values
            for kind in ("random forest", "logistic regression"):
                sc = {k: P.oof(c[f].values, y, fold, kind) for k, f in SETS.items()}
                ok = np.all([np.isfinite(v) for v in sc.values()], axis=0)
                for k, s in sc.items():
                    rows.append({"res": res, "seed": sd, "region": region, "model": kind, "set": k, "cells": int(ok.sum()),
                                 "positives": int(y[ok].sum()), "roc": roc_auc_score(y[ok], s[ok]),
                                 "pr": average_precision_score(y[ok], s[ok]), "top10": P.recall_top(y[ok], s[ok])})
        print(res, "seed", sd, "done", flush=True)
    out = pd.DataFrame(rows)
    out.to_csv(P.PILOT / f"location_checks_licsar_{res}m.csv", index=False)
    return out


def direction_table(adm):
    """LiCSAR vertical velocity P1 in collapse vs background cells, inside and outside the core (descriptive)."""
    rows = []
    for res in P.RESOLUTIONS:
        c = load(res, adm)
        c = c[np.isfinite(c[VEL])]
        for region, d in (("historic core", c[c.core]), ("outside the core", c[~c.core])):
            y = d.positive.values
            rows.append({"Cell size": f"{res} m", "Region": region, "Cells (collapse cells)": f"{len(d):,} ({int(y.sum())})",
                         "Median, collapse cells (mm/yr)": f"{d[VEL][y].median():.2f}",
                         "Median, background (mm/yr)": f"{d[VEL][~y].median():.2f}",
                         "Single-layer ROC AUC": f"{roc_auc_score(y, d[VEL]):.2f}"})
    return pd.DataFrame(rows)


def main():
    adm = gpd.read_file(P.RAW / "admin_geoboundaries/geoBoundaries-EGY-ADM2.geojson").to_crs(P.CRS)
    if "--report-only" in sys.argv:
        r = {res: pd.read_csv(P.PILOT / f"location_checks_licsar_{res}m.csv") for res in P.RESOLUTIONS}
    else:
        r = {res: run(res, adm) for res in P.RESOLUTIONS}
    lines = [
        "# Location checks with LiCSAR velocity (secondary check 6)",
        "",
        "**Plan:** `LICSAR_TEST_PLAN.md`; the design is `LOCATION_CHECKS.md`'s with LiCSAR vertical velocity P1 in place of Shirzaei "
        "velocity, on the eligible cells that have a LiCSAR value. No decision is attached.",
        "**Reproduce:** `.venv/bin/python scripts/18_licsar_location_checks.py` (after 16).",
        "",
        "- **Feature sets on identical cells:** A = baseline; B = baseline + x/y; C = baseline + velocity; D = baseline + x/y + velocity.",
        f"- **Splits:** values for the primary split (seed {C8.PRIMARY}); the Δ columns summarise the {len(C8.ALT)} other block → fold "
        "assignments. \"Splits up\" = splits where velocity raised the metric.",
        "",
        *READING,
    ]
    for res in P.RESOLUTIONS:
        for kind in ("logistic regression", "random forest"):
            t = C8.summary(r[res], kind)
            print(res, kind)
            print(t.to_string(index=False))
            lines += [f"## {kind.capitalize()} ({res} m)", "", P.md_table(t), "",
                      f"Coordinates alone (A → B, primary split): {C8.coord_effect(r[res], kind)}.", ""]
    dt = direction_table(adm)
    print(dt.to_string(index=False))
    lines += ["## Direction of the velocity difference (descriptive)", "",
              "LiCSAR vertical velocity P1; negative = subsidence relative to each frame's reference. Single-layer ROC AUC below 0.5 "
              "= lower values in collapse cells.", "", P.md_table(dt), ""]
    (P.PILOT / "LICSAR_LOCATION_CHECKS.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
