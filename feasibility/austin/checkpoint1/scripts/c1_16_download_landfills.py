"""Checkpoint 1 (AUSTIN_PLAN §7 sign check, §13 step 2; §14 landfill entry of 2026-11-10):
download and hash the landfill layers. No InSAR value is read.

- City of Austin "Landfill Perimeters" (the footprints used by the sign check) and the City's
  landfill points.
- TCEQ municipal solid waste sites: "MSW Facilities" (Regulated Facilities Viewer) and
  "Active Landfills". Points only; they define no footprint.
The raw copies hold owner and facility names, addresses and telephone numbers, so they stay in
the private area. The project JSON holds counts, areas, status and active years only.
"""
import datetime as dt
import hashlib
import json
import sys
from pathlib import Path

import geopandas as gpd
import requests
import shapely

out, boundary, out_json = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
out.mkdir(parents=True, exist_ok=False)
LAYERS = {
    "city_landfill_perimeters": "https://maps.austintexas.gov/arcgis/rest/services/Shared/Environmental_1/MapServer/10",
    "city_landfill_points": "https://maps.austintexas.gov/arcgis/rest/services/Shared/Environmental_1/MapServer/9",
    "tceq_msw_facilities": "https://gisweb.tceq.texas.gov/arcgis/rest/services/Regulated_Facilities_Viewer/Regulated_Facilities_Viewer/MapServer/2",
    "tceq_active_landfills": "https://gisweb.tceq.texas.gov/arcgis/rest/services/Public/Landfills/MapServer/0",
}
H = {"User-Agent": "research-client"}
S = dict(downloaded_utc=dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), layers={})
frames = {}
for name, url in LAYERS.items():
    meta = requests.get(url, params={"f": "json"}, headers=H, timeout=120)
    meta.raise_for_status()
    n = requests.get(url + "/query", params={"where": "1=1", "returnCountOnly": "true", "f": "json"}, headers=H, timeout=120).json()["count"]
    assert n <= meta.json()["maxRecordCount"]
    r = requests.get(url + "/query", params={"where": "1=1", "outFields": "*", "outSR": 4326, "f": "geojson"}, headers=H, timeout=300)
    r.raise_for_status()
    (out / f"{name}.layer.json").write_bytes(meta.content)
    (out / f"{name}.geojson").write_bytes(r.content)
    g = gpd.read_file(out / f"{name}.geojson")
    assert len(g) == n, (name, len(g), n)
    frames[name] = g
    S["layers"][name] = dict(url=url, layer_name=meta.json()["name"], features=n, bytes=len(r.content),
                             sha256=hashlib.sha256(r.content).hexdigest(), layer_json_sha256=hashlib.sha256(meta.content).hexdigest())

b = gpd.read_file(boundary)
city = shapely.union_all(b.to_crs(32614).geometry.to_numpy())
if not shapely.is_valid(city):
    city = shapely.make_valid(city)
per = frames["city_landfill_perimeters"].to_crs(32614)
per["geometry"] = shapely.make_valid(per.geometry.to_numpy())
hit = per[per.intersects(city)]
S["city_landfill_perimeters"] = dict(
    perimeters=len(per), intersect_the_full_purpose_boundary=len(hit),
    area_ha_of_intersecting_perimeters=round(float(hit.area.sum()) / 1e4, 1),
    union_area_ha=round(float(shapely.union_all(hit.geometry.to_numpy()).area) / 1e4, 1),
    pixels_30m_equivalent=int(round(float(shapely.union_all(hit.geometry.to_numpy()).area) / 900)),
    operating_status=hit.OPERATING_STATUS.fillna("not stated").value_counts().to_dict(),
    type_of_landfill=hit.TYPE_OF_LANDFILL.fillna("not stated").value_counts().to_dict(),
    active_years=sorted(hit.ACTIVE_YEARS.fillna("not stated").tolist()),
    area_ha_each=sorted(round(float(v) / 1e4, 2) for v in hit.area))
pts = frames["city_landfill_points"].to_crs(32614)
S["city_landfill_points"] = dict(points=len(pts), inside_the_full_purpose_boundary=int(pts.within(city).sum()))
for name, col in (("tceq_msw_facilities", "FAC_TYPE"), ("tceq_active_landfills", "LANDFILL_T")):
    t = frames[name].to_crs(32614)
    t = t[~t.geometry.is_empty & t.geometry.notna()]
    ins = t[t.within(city)]
    near = t[t.distance(city) <= 2000]
    S[name] = dict(points=len(frames[name]), in_travis_county=int(frames[name].COUNTY.astype(str).str.upper().str.contains("TRAVIS").sum()),
                   inside_the_full_purpose_boundary=len(ins), within_2_km_of_the_boundary=len(near),
                   inside_by_type=ins[col].fillna("not stated").value_counts().to_dict(),
                   inside_and_within_a_city_perimeter=int(ins.within(shapely.union_all(per.geometry.to_numpy())).sum()))
    if name == "tceq_msw_facilities":
        S[name]["inside_by_status"] = ins.ADDN_STATUS.fillna("not stated").value_counts().to_dict()
out_json.write_text(json.dumps(S, indent=1, default=str) + "\n")
print(json.dumps(S, indent=1, default=str))
