"""Location checks for the pilot's velocity gain. No new features and no tuning.

Same reviewed events (06), the same Shirzaei-covered cells and the same spatial folds as 07. The folds are the
primary block -> fold assignment (seed 42) and the 10 alternative assignments (seeds 0-9) of 07's fold check.
Feature sets on identical cells:
  A baseline · B baseline + x/y · C baseline + velocity · D baseline + x/y + velocity
x/y = the cell centre's UTM 36N coordinates (km), a deliberate location control, not a predictor.
Regions: the full area, and the historic core, fixed before this run as the 7 central districts named in the
audit (Karmouz, Moharam Bek, El Gomrok, El Labban, Attarin, Manshiya, Mina El-Basal; a cell belongs to the core
if its centre is inside them). In the core, models are trained and tested on core cells only.
Reported: paired changes C - A and D - B in PR AUC, in the share of collapse cells in the top 10% of ranked
cells, and in ROC AUC. Outputs: data/pilot/location_checks_<res>m.csv and data/pilot/LOCATION_CHECKS.md."""
import importlib.util
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import shapely
from sklearn.metrics import average_precision_score, roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("pilot", ROOT / "scripts/07_pilot_models.py")
P = importlib.util.module_from_spec(spec)
spec.loader.exec_module(P)

CORE = ["Karmuz", "Muharam Bik", "Al Gumruk", "A L Labban", "Al Attarin", "Al Manshiyya", "Mina Al-Basal"]
SETS = {"A": P.BASELINE, "B": P.BASELINE + ["x_km", "y_km"], "C": P.BASELINE + ["shz_vlm"],
        "D": P.BASELINE + ["x_km", "y_km", "shz_vlm"]}
EXPERIMENTS = [("Full area, no coordinates", "full area", "A", "C"), ("Full area, with coordinates", "full area", "B", "D"),
               ("Historic core only", "historic core", "A", "C"), ("Historic core, with coordinates", "historic core", "B", "D")]
PRIMARY, ALT = P.SEED, list(P.FOLD_SEEDS)
METRICS = [("pr", "PR AUC"), ("top10", "Collapse cells in top 10%"), ("roc", "ROC AUC")]
READING = [  # written after the 2026-09-29 run; Δ values are medians over the 10 other splits
    "## Result",
    "",
    "- **Full area: the velocity gain is mostly location.** With x/y in the random forest, velocity no longer raises ROC AUC "
    "(−0.004, up in 3 of 10 splits) or top-10% capture (−3 pts, 1 of 10). PR AUC still rises (+0.040, 10 of 10), a gain "
    "confined to the very top of the ranking. The linear model shows no full-area gain with or without x/y.",
    "- **Historic core: velocity adds, with and without x/y.** In the linear model it raised PR AUC and ROC AUC in 10 of 10 "
    "splits at both 250 m and 200 m (with x/y: PR +0.052 and ROC +0.028 at 250 m; PR +0.068 and ROC +0.020 at 200 m). "
    "Top-10% capture rose at 250 m (+6 pts, 10 of 10) but was mixed at 200 m. The random forest's core gain with x/y held "
    "at 250 m but not at 200 m.",
    "- **Direction:** inside the core, collapse cells sink faster than background cells (median −4.0 vs −3.0 mm/yr at "
    "250 m); outside it there is no difference, which would explain why the full-area linear model saw nothing.",
    "- **Limits:** 241 core cells and 32 collapse cells at 250 m; no significance test yet; the Shirzaei observation period "
    "is still unknown, so this is a retrospective association, not a precursor.",
    "",
]


def run(res, seeds, area, adm, pts, ev):
    cells, _, _ = P.build_cells(res, area, pts, ev)
    cells["x_km"], cells["y_km"] = cells.x / 1000, cells.y / 1000
    core = adm[adm.shapeName.isin(CORE)].union_all()
    cells["core"] = shapely.contains_xy(core, cells.x.values, cells.y.values)
    cov = cells[np.isfinite(cells[P.BASELINE + ["shz_vlm"]]).all(axis=1) & (cells.shz_n > 0)]
    rows = []
    for sd in seeds:
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
    out = pd.DataFrame(rows)
    out.to_csv(P.PILOT / f"location_checks_{res}m.csv", index=False)
    return out


def summary(df, kind, with_alt=True):
    rows = []
    for name, region, a, b in EXPERIMENTS:
        d = df[(df.model == kind) & (df.region == region)]
        pa = d[(d.seed == PRIMARY) & (d.set == a)].iloc[0]
        pb = d[(d.seed == PRIMARY) & (d.set == b)].iloc[0]
        r = {"Experiment": name, "Cells (collapse cells)": f"{pa.cells:,} ({pa.positives})"}
        for m, label in METRICS:
            fmt = (lambda v: f"{v:.0%}") if m == "top10" else (lambda v: f"{v:.3f}")
            dfmt = (lambda v: f"{100 * v:+.0f} pts") if m == "top10" else (lambda v: f"{v:+.3f}")
            r[f"{label}: baseline → + velocity"] = f"{fmt(pa[m])} → {fmt(pb[m])}"
            if with_alt:
                alt = d[d.seed.isin(ALT)].pivot(index="seed", columns="set", values=m)
                delta = alt[b] - alt[a]
                r[f"Δ {label}, other splits: median (range), splits up"] = (
                    f"{dfmt(delta.median())} ({dfmt(delta.min())} to {dfmt(delta.max())}), {int((delta > 0).sum())} of {len(delta)}")
            else:
                r[f"Δ {label}"] = dfmt(pb[m] - pa[m])
        rows.append(r)
    return pd.DataFrame(rows)


def coord_effect(df, kind):
    """What the location control alone adds (A -> B) on the primary split."""
    out = []
    for region in ("full area", "historic core"):
        d = df[(df.model == kind) & (df.region == region) & (df.seed == PRIMARY)].set_index("set")
        out.append(f"{region}: PR AUC {d.pr['A']:.3f} → {d.pr['B']:.3f}, ROC AUC {d.roc['A']:.3f} → {d.roc['B']:.3f}")
    return "; ".join(out)


def direction_table(adm):
    """Descriptive: Shirzaei VLM in collapse vs background cells, inside and outside the core (07's saved cells)."""
    core = adm[adm.shapeName.isin(CORE)].union_all()
    rows = []
    for res in P.RESOLUTIONS:
        c = pd.read_csv(P.PILOT / f"cells_{res}m.csv")
        c = c[(c.shz_n > 0) & c.shz_vlm.notna()]
        inside = shapely.contains_xy(core, c.x.values, c.y.values)
        for region, d in (("historic core", c[inside]), ("outside the core", c[~inside])):
            y = d.positive.values
            rows.append({"Cell size": f"{res} m", "Region": region, "Cells (collapse cells)": f"{len(d):,} ({int(y.sum())})",
                         "VLM median, collapse cells (mm/yr)": f"{d.shz_vlm[y].median():.1f}",
                         "VLM median, background (mm/yr)": f"{d.shz_vlm[~y].median():.1f}",
                         "Single-layer AUC": f"{roc_auc_score(y, d.shz_vlm):.2f}"})
    return pd.DataFrame(rows)


def main():
    ev = pd.read_csv(P.PILOT / "target_events.csv")
    adm = gpd.read_file(P.RAW / "admin_geoboundaries/geoBoundaries-EGY-ADM2.geojson").to_crs(P.CRS)
    area = adm[adm.shapeName.isin(P.DISTRICTS)].union_all()
    if "--report-only" in sys.argv:  # rebuild the report from the saved runs
        r250, r200 = (pd.read_csv(P.PILOT / f"location_checks_{r}m.csv") for r in (250, 200))
    else:
        pts = P.load_points()
        r250 = run(250, [PRIMARY] + ALT, area, adm, pts, ev)
        r200 = run(200, [PRIMARY] + ALT, area, adm, pts, ev)
    rf, lr = summary(r250, "random forest"), summary(r250, "logistic regression")
    rf200 = summary(r200, "random forest")
    lr200 = summary(r200, "logistic regression")
    print(rf.to_string(index=False))
    print(lr.to_string(index=False))
    print(rf200.to_string(index=False))
    print(lr200.to_string(index=False))
    lines = [
        "# Location checks for the velocity gain",
        "",
        "**Question:** does Shirzaei velocity still add ranking skill once location is controlled? Same 63 reviewed events, "
        "same Shirzaei-covered cells and same spatial folds as the pilot (`PILOT_REPORT.md`); no new features, no tuning.",
        "**Reproduce:** `.venv/bin/python scripts/08_location_checks.py` (after 06 and 07).",
        "",
        "- **Feature sets on identical cells:** A = baseline; B = baseline + x/y; C = baseline + velocity; D = baseline + x/y + velocity. "
        "x/y are the cell centre's UTM 36N coordinates (km): a location control, not a claimed cause.",
        "- **Comparisons:** velocity without coordinates (A → C) and with coordinates (B → D).",
        "- **Historic core:** fixed before this run as the 7 central districts named in the audit (Karmouz, Moharam Bek, El Gomrok, "
        "El Labban, Attarin, Manshiya, Mina El-Basal). A cell is in the core if its centre lies inside them; core models are "
        "trained and tested on core cells only.",
        f"- **Splits:** the values are for the primary split (seed {PRIMARY}); the Δ columns summarise the {len(ALT)} other "
        "block → fold assignments used in the pilot's fold check. \"Splits up\" = splits where velocity raised the metric.",
        "- **Top 10%:** share of collapse cells among the highest-ranked 10% of cells. With few positives, PR AUC and top-10% "
        "capture matter more than small ROC AUC differences.",
        "",
        *READING,
        "## Random forest (250 m)",
        "",
        P.md_table(rf),
        "",
        f"Coordinates alone (A → B, primary split): {coord_effect(r250, 'random forest')}.",
        "",
        "## Logistic regression (250 m)",
        "",
        P.md_table(lr),
        "",
        f"Coordinates alone (A → B, primary split): {coord_effect(r250, 'logistic regression')}.",
        "",
        "## Random forest at 200 m (sensitivity)",
        "",
        P.md_table(rf200),
        "",
        "## Logistic regression at 200 m (sensitivity)",
        "",
        P.md_table(lr200),
        "",
        "## Direction of the velocity difference (descriptive)",
        "",
        "Shirzaei VLM in covered cells; negative = subsidence. Single-layer AUC below 0.5 = lower (more negative) values in "
        "collapse cells.",
        "",
        P.md_table(direction_table(adm)),
        "",
    ]
    (P.PILOT / "LOCATION_CHECKS.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
