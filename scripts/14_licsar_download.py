"""Clip the LiCSAR interferograms of the two Alexandria frames to the city window and lay them out as LiCSBAS's GEOC
folder, ready for LiCSBAS02 onwards.

The interferograms are read remotely from the CEDA archive, where LiCSAR moved them; the GeoTIFFs are striped, so
only the rows inside the window are fetched. Per frame the output is:
  GEOC/<frame>.geo.{E,N,U,hgt}.tif (clipped from the local metadata), GEOC/baselines, GEOC/metadata.txt,
  GEOC/<pair>/<pair>.geo.unw.tif and <pair>.geo.cc.tif (unwrapped phase in radians; coherence as uint8 0-255).
All files share the frame's 0.001 degree grid, cut to the project clip box. Resumable: finished files are skipped,
and failures are listed in GEOC/failed.txt and retried on the next run.
Usage: .venv/bin/python scripts/14_licsar_download.py [--workers 4]"""
import argparse
import concurrent.futures as cf
import shutil
import time
from pathlib import Path

import rasterio
from rasterio.windows import from_bounds

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/insar_licsar"
CEDA = "https://dap.ceda.ac.uk/neodc/comet/data/licsar_products"
FRAMES = {"065D_05935_131108": "65", "131A_05957_110910": "131"}
AOI = (29.75, 31.05, 30.15, 31.38)  # lon/lat clip box of the project (data/README.md)
GDAL_ENV = dict(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR", CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif",
                GDAL_HTTP_MAX_RETRY="4", GDAL_HTTP_RETRY_DELAY="10", GDAL_HTTP_TIMEOUT="180")


def clip(src, dst):
    """Write the AOI window of src to dst (via a temporary file, so an interrupted write is never taken as done)."""
    with rasterio.Env(**GDAL_ENV), rasterio.open(src) as s:
        w = from_bounds(*AOI, s.transform).round_offsets().round_lengths()
        a = s.read(1, window=w)
        prof = {"driver": "GTiff", "dtype": s.dtypes[0], "count": 1, "height": a.shape[0], "width": a.shape[1],
                "crs": s.crs, "transform": s.window_transform(w), "nodata": s.nodata, "compress": "deflate"}
    dst.parent.mkdir(parents=True, exist_ok=True)
    tmp = dst.with_suffix(".part")
    with rasterio.open(tmp, "w", **prof) as d:
        d.write(a, 1)
    tmp.replace(dst)


def pair_task(track, frame, pair, geoc):
    for ext in ("unw", "cc"):
        dst = geoc / pair / f"{pair}.geo.{ext}.tif"
        if not dst.exists():
            clip(f"/vsicurl/{CEDA}/{track}/{frame}/{pair}/{pair}.geo.{ext}.tif", dst)
    return pair


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()
    for frame, track in FRAMES.items():
        geoc = RAW / frame / "GEOC"
        geoc.mkdir(exist_ok=True)
        meta = RAW / frame / "metadata"
        for layer in ("E", "N", "U", "hgt"):
            dst = geoc / f"{frame}.geo.{layer}.tif"
            if not dst.exists():
                clip(meta / f"{frame}.geo.{layer}.tif", dst)
        for name in ("baselines", "metadata.txt"):
            shutil.copy2(meta / name, geoc / name)
        pairs = (RAW / frame / "interferograms.txt").read_text().split()
        todo = [p for p in pairs if not all((geoc / p / f"{p}.geo.{e}.tif").exists() for e in ("unw", "cc"))]
        print(f"{frame}: {len(pairs)} pairs, {len(todo)} to fetch", flush=True)
        failed, t0 = [], time.time()
        with cf.ThreadPoolExecutor(args.workers) as ex:
            futs = {ex.submit(pair_task, track, frame, p, geoc): p for p in todo}
            for i, f in enumerate(cf.as_completed(futs), 1):
                try:
                    f.result()
                except Exception as e:  # noqa: BLE001 - keep going, list the pair for a retry
                    failed.append(f"{futs[f]}\t{type(e).__name__}: {e}")
                if i % 100 == 0 or i == len(todo):
                    print(f"  {i}/{len(todo)} done, {len(failed)} failed, {time.time() - t0:.0f} s", flush=True)
        (geoc / "failed.txt").write_text("\n".join(failed) + ("\n" if failed else ""))
        print(f"{frame}: finished, {len(failed)} failed (GEOC/failed.txt)", flush=True)


if __name__ == "__main__":
    main()
