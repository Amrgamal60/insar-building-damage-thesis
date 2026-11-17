"""Clip the downloaded raster/vector layers to the Alexandria window (native CRS, no resampling) and
print a coverage summary. Outputs go to data/interim/layers/."""
from pathlib import Path

import numpy as np
import pyogrio
import rasterio
from rasterio.merge import merge
from rasterio.warp import transform_bounds
from rasterio.windows import from_bounds

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw"
OUT = ROOT / "data/interim/layers"
OUT.mkdir(parents=True, exist_ok=True)
BBOX = (29.75, 31.05, 30.15, 31.38)  # lon/lat

RASTERS = {  # output name: list of source paths (several = mosaic)
    "wsf_evolution_year": ["wsf_evolution/WSFevolution_v1_28_30.tif", "wsf_evolution/WSFevolution_v1_30_30.tif"],
    "wsf_idc_score": ["wsf_evolution/idcscore/IDC_Score_28_30.tif", "wsf_evolution/idcscore/IDC_Score_30_30.tif"],
    "ghs_built_s_1975": ["/vsizip/" + str(RAW / "ghsl_built_s/GHS_BUILT_S_E1975_GLOBE_R2023A_54009_100_V1_0_R6_C21.zip/GHS_BUILT_S_E1975_GLOBE_R2023A_54009_100_V1_0_R6_C21.tif")],
    "ghs_built_s_2000": ["/vsizip/" + str(RAW / "ghsl_built_s/GHS_BUILT_S_E2000_GLOBE_R2023A_54009_100_V1_0_R6_C21.zip/GHS_BUILT_S_E2000_GLOBE_R2023A_54009_100_V1_0_R6_C21.tif")],
    "ghs_built_s_2015": ["/vsizip/" + str(RAW / "ghsl_built_s/GHS_BUILT_S_E2015_GLOBE_R2023A_54009_100_V1_0_R6_C21.zip/GHS_BUILT_S_E2015_GLOBE_R2023A_54009_100_V1_0_R6_C21.tif")],
    "ghs_built_s_2020": ["/vsizip/" + str(RAW / "ghsl_built_s/GHS_BUILT_S_E2020_GLOBE_R2023A_54009_100_V1_0_R6_C21.zip/GHS_BUILT_S_E2020_GLOBE_R2023A_54009_100_V1_0_R6_C21.tif")],
    "ghs_built_h_anbh_2018": ["/vsizip/" + str(RAW / "ghsl_built_h/GHS_BUILT_H_ANBH_E2018_GLOBE_R2023A_54009_100_V1_0_R6_C21.zip/GHS_BUILT_H_ANBH_E2018_GLOBE_R2023A_54009_100_V1_0_R6_C21.tif")],
    "ghs_built_h_agbh_2018": ["/vsizip/" + str(RAW / "ghsl_built_h/GHS_BUILT_H_AGBH_E2018_GLOBE_R2023A_54009_100_V1_0_R6_C21.zip/GHS_BUILT_H_AGBH_E2018_GLOBE_R2023A_54009_100_V1_0_R6_C21.tif")],
    "ghs_age_1975_2020": ["/vsizip/" + str(RAW / "ghsl_age/GHS_AGE_1975052020_GLOBE_R2025A_54009_100_V1_0.zip/GHS_AGE_1975052020_GLOBE_R2025A_54009_100_V1_0.tif")],
    "gsw_occurrence": ["gsw/occurrence_20E_40Nv1_4_2021.tif", "gsw/occurrence_30E_40Nv1_4_2021.tif"],
    "gsw_change": ["gsw/change_20E_40Nv1_4_2021.tif", "gsw/change_30E_40Nv1_4_2021.tif"],
    "gsw_transitions": ["gsw/transitions_20E_40Nv1_4_2021.tif", "gsw/transitions_30E_40Nv1_4_2021.tif"],
    "nile_vlm_ohenhen2025": ["insar_deltas_ohenhen2025/gridVLM/nile_vlm.tif"],
}


def src_path(p):
    return p if p.startswith("/vsi") else str(RAW / p)


def clip(name, paths):
    srcs = [rasterio.open(src_path(p)) for p in paths]
    crs = srcs[0].crs
    b = transform_bounds("EPSG:4326", crs, *BBOX, densify_pts=21)
    if len(srcs) > 1:
        arr, tr = merge(srcs, bounds=b)
        arr = arr[0]
    else:
        s = srcs[0]
        w = from_bounds(*b, transform=s.transform).round_offsets().round_lengths()
        arr = s.read(1, window=w, boundless=True, fill_value=s.nodata or 0)
        tr = s.window_transform(w)
    prof = dict(driver="GTiff", height=arr.shape[0], width=arr.shape[1], count=1, dtype=arr.dtype, crs=crs,
                transform=tr, nodata=srcs[0].nodata, compress="deflate", tiled=True)
    with rasterio.open(OUT / f"{name}.tif", "w", **prof) as o:
        o.write(arr, 1)
    for s in srcs:
        s.close()
    return arr, srcs[0].nodata, crs, tr


def main():
    for name, paths in RASTERS.items():
        missing = [p for p in paths if not p.startswith("/vsi") and not (RAW / p).exists()]
        if missing:
            print(f"{name}: missing {missing}")
            continue
        arr, nd, crs, tr = clip(name, paths)
        v = arr[arr != nd] if nd is not None else arr.ravel()
        v = v[np.isfinite(v)] if v.dtype.kind == "f" else v
        nz = v[v != 0]
        print(f"{name:24s} {str(crs)[:14]:14s} px={abs(tr.a):.5g} shape={arr.shape} valid={len(v)} nonzero={len(nz)} "
              f"range=[{nz.min() if len(nz) else '-'}, {nz.max() if len(nz) else '-'}] "
              f"uniq={len(np.unique(nz)) if len(nz) else 0}")

    # GHS-OBAT: per-building attributes (height, age epoch, use) for Egypt -> Alexandria window
    obat = "/vsizip/" + str(RAW / "ghsl_obat/GHS_OBAT_GPKG_EGY_E2020_R2024A_V1_0.zip/GHS_OBAT_GPKG_EGY_E2020_R2024A_V1_0.gpkg")
    info = pyogrio.read_info(obat)
    print("GHS-OBAT layers:", pyogrio.list_layers(obat).tolist(), "| crs", info["crs"], "| features", info["features"])
    print("GHS-OBAT fields:", list(info["fields"]))
    crs = info["crs"]
    b = transform_bounds("EPSG:4326", crs, *BBOX, densify_pts=21)
    gdf = pyogrio.read_dataframe(obat, bbox=b)
    gdf.to_file(OUT / "ghs_obat_alexandria.gpkg", driver="GPKG")
    print("GHS-OBAT Alexandria features:", len(gdf))
    print(gdf.drop(columns="geometry").describe(include="all").T.head(20).to_string())


if __name__ == "__main__":
    main()
