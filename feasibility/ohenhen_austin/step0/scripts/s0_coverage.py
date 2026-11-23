"""Step 0 of the Ohenhen-map validation (OHENHEN_AUSTIN_PLAN.md): outcome-blind coverage of the Austin houses by
the published layers of Ohenhen et al. 2025 (Nature Cities; data doi 10.7294/27606942, CC0).

No outcome is read: from the Austin checkpoint-1 tables only house identifiers, coordinates and Baseline 1 features
are loaded (the `holds_event` column is never requested), and from the checkpoint-1 event summary only the published
yearly event counts. No house is linked to an event.

Outputs (feasibility/ohenhen_austin/step0/): coverage.json, STEP0_COVERAGE.md.
"""
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio
from pyproj import Transformer
from scipy.spatial import cKDTree
from scipy.stats import spearmanr

HERE = Path(__file__).resolve().parent
STUDY = HERE.parents[1]
ROOT = STUDY.parents[1]
PRIV = Path("/mnt/data/Master-projects/Alex_private")
RAW = PRIV / "ohenhen2025_raw"
CP1 = PRIV / "austin/checkpoint1"
OUT = STUDY / "step0"
FEATURES = ["year_built", "log_living_area", "log_lot_area", "lep_0_150", "slope_deg", "elevation_m", "log_income",
            "foundation_slab", "canopy_share", "x_km", "y_km"]
INPUTS = {"ohenhen/risk_austin.tif": RAW / "risk_austin.tif", "ohenhen/beta_austin.tif": RAW / "beta_austin.tif",
          "ohenhen/austin_VLM.csv": RAW / "austin_VLM.csv",
          "austin/reference_2018/population_2018.parquet": CP1 / "reference_2018/population_2018.parquet",
          "austin/features/features_2018.parquet": CP1 / "features/features_2018.parquet",
          "feasibility/austin/checkpoint1/events_2018.json": ROOT / "feasibility/austin/checkpoint1/events_2018.json"}
RISK_NAMES = {0: "very low", 1: "low", 2: "medium", 3: "high", 4: "very high"}
HAZARD_NAMES = {0: "low", 1: "medium", 2: "high", 3: "very high"}


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def read_class(path, lon, lat):
    with rasterio.open(path) as r:
        a = r.read(1).astype(float)
        rr, cc = (np.asarray(t) for t in rasterio.transform.rowcol(r.transform, lon, lat))
        inside = (rr >= 0) & (rr < a.shape[0]) & (cc >= 0) & (cc < a.shape[1])
        v = np.full(len(lon), np.nan)
        v[inside] = a[rr[inside], cc[inside]]
        v[~np.isfinite(v) | (v < -1e30)] = np.nan
        grid = dict(crs=str(r.crs), res_deg=list(r.res), shape=list(a.shape), bounds=list(r.bounds),
                    cells_by_class={str(int(k)): int(n) for k, n in zip(*np.unique(a[np.isfinite(a) & (a > -1e30)], return_counts=True))})
        return v, rr * 100_000 + cc, inside, grid


def main():
    cols = ["prop_id", "block"] + FEATURES + ["complete_b1"]
    f = pd.read_parquet(INPUTS["austin/features/features_2018.parquet"], columns=cols)  # outcome column not read
    pop = pd.read_parquet(INPUTS["austin/reference_2018/population_2018.parquet"], columns=["prop_id", "x", "y"]).merge(f, on="prop_id")
    lon, lat = Transformer.from_crs(32614, 4326, always_xy=True).transform(pop.x.to_numpy(), pop.y.to_numpy())
    rec = dict(houses=len(pop), houses_complete_b1=int(pop.complete_b1.sum()), layers={})
    for name, key, names in (("risk", "ohenhen/risk_austin.tif", RISK_NAMES), ("hazard", "ohenhen/beta_austin.tif", HAZARD_NAMES)):
        v, cell, inside, grid = read_class(INPUTS[key], lon, lat)
        pop[name], pop[name + "_cell"] = v, cell
        ok = np.isfinite(v)
        rec["layers"][name] = dict(grid=grid, inside_extent=float(inside.mean()), valid_share=float(ok.mean()),
                                   valid_share_complete_b1=float(ok[pop.complete_b1.to_numpy(bool)].mean()),
                                   houses_by_class={names[int(k)]: int(n) for k, n in pop[name].value_counts().sort_index().items()},
                                   cells_with_houses=int(pd.Series(cell[ok]).nunique()),
                                   houses_per_cell_median=float(pd.Series(cell[ok]).value_counts().median()))
    rec["hazard_by_risk"] = {HAZARD_NAMES[int(h)]: {RISK_NAMES[int(r)]: int(n) for r, n in g.items()}
                             for h, g in pd.crosstab(pop.hazard, pop.risk).iterrows()}
    v = pd.read_csv(INPUTS["ohenhen/austin_VLM.csv"])
    vx, vy = Transformer.from_crs(4326, 32614, always_xy=True).transform(v.longitude_deg.to_numpy(), v.latitude_deg.to_numpy())
    tree = cKDTree(np.c_[vx, vy])
    d, _ = tree.query(np.c_[pop.x, pop.y], k=1)
    n50 = np.array([len(i) for i in tree.query_ball_point(np.c_[pop.x, pop.y], r=50)])
    sp, _ = cKDTree(np.c_[vx, vy]).query(np.c_[vx, vy][::50], k=2)
    rec["vlm_points"] = dict(points=len(v), spacing_m_median=float(np.median(sp[:, 1])),
                             vlm_mm_yr=dict(zip(["p5", "median", "p95"], np.percentile(v.VLM_mmPerYr, [5, 50, 95]).tolist())),
                             vlm_std_median=float(v.VLM_std_mmPerYr.median()),
                             house_nearest_m=dict(median=float(np.median(d)), p90=float(np.percentile(d, 90))),
                             house_share_point_within={f"{r} m": float((d <= r).mean()) for r in (30, 50, 100)},
                             house_points_within_50m_median=float(np.median(n50)))
    pop["covered"] = pop.risk.notna()
    rec["covered_vs_not_median"] = {c: {"covered": float(pop.loc[pop.covered, c].median()), "not covered": float(pop.loc[~pop.covered, c].median())} for c in FEATURES}
    dec = (pop.year_built // 20) * 20
    rec["covered_share_by_year_built_20y"] = {str(int(k)): dict(share=float(g.covered.mean()), houses=len(g)) for k, g in pop.groupby(dec) if k >= 1900}
    c = pop[pop.covered]
    rec["spearman_with_class_covered"] = {x: dict(risk=float(spearmanr(c.risk[c[x].notna()], c[x].dropna())[0]),
                                               hazard=float(spearmanr(c.hazard[c[x].notna()], c[x].dropna())[0])) for x in FEATURES}
    hi = c.risk >= 3
    rec["flagged_high_or_very_high_risk"] = dict(houses=int(hi.sum()), share_of_covered=float(hi.mean()),
                                                 blocks=int(c.loc[hi, "block"].nunique()), blocks_total=int(pop.block.nunique()),
                                                 cells=int(c.loc[hi, "risk_cell"].nunique()),
                                                 median=c.loc[hi, FEATURES].median().to_dict(), median_other_covered=c.loc[~hi, FEATURES].median().to_dict())
    hz = c.hazard >= 2
    rec["flagged_high_or_very_high_hazard"] = dict(houses=int(hz.sum()), blocks=int(c.loc[hz, "block"].nunique()))
    ev = json.loads(INPUTS["feasibility/austin/checkpoint1/events_2018.json"].read_text())["foundation"]["events_by_year"]
    n_follow = sum(ev[y] for y in ("2022", "2023", "2024", "2025"))
    rec["events_by_year_all_houses"] = ev
    rec["events_2022_2025_all_houses"] = n_follow
    rec["expected_if_unrelated"] = dict(note="events 2022-2025 x covered share x flagged share; ignores the at-risk rule and any association",
                                        covered=n_follow * float(pop.covered.mean()),
                                        flagged=n_follow * float(pop.covered.mean()) * float(hi.mean()))
    rec["inputs_sha256"] = {k: sha256(p) for k, p in INPUTS.items()}
    rec["script_sha256"] = sha256(Path(__file__))
    (OUT / "coverage.json").write_text(json.dumps(rec, indent=1) + "\n")
    print(json.dumps({k: rec[k] for k in ("houses", "flagged_high_or_very_high_risk", "expected_if_unrelated")}, indent=1, default=float))


if __name__ == "__main__":
    main()
