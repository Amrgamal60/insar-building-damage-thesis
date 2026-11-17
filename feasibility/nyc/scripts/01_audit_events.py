"""NYC feasibility audit: how many clean, located structural-collapse events have InSAR history before them?

Input: the OEM Emergency Response Incidents table (NYC Open Data pasr-j7fb), downloaded to raw/incidents.csv.
Steps: keep Structural-Collapse and Structural-Partial Collapse; merge duplicate reports (same address within 3 days);
geocode every event with NYC Planning Geosearch (BBL, BIN, point); attach PLUTO (current release) building attributes;
flag major DOB works (NB/DM/A1 permits issued in the 365 days before the event); count the events with 1, 2 and 3
years of OPERA DISP-S1 history (frame F08622, first epoch 2016-07-16).
Outputs: out/events_clean.csv and out/AUDIT.md.
Usage: python -I scripts/01_audit_events.py raw out"""
import csv
import datetime as dt
import json
import math
import re
import sys
import time
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

RAW, OUT = Path(sys.argv[1]), Path(sys.argv[2])
OUT.mkdir(exist_ok=True)
TYPES = ("Structural-Collapse", "Structural-Partial Collapse")
OPERA_START = dt.date(2016, 7, 16)  # first secondary-date epoch of OPERA DISP-S1 frame F08622 (CMR, 2026-10-07)
BORO = {"BRONX": "Bronx", "BROOKLYN": "Brooklyn", "MANHATTAN": "Manhattan", "NEW YORK": "Manhattan",
        "QUEENS": "Queens", "LONG ISLAND CITY": "Queens", "JAMACIA": "Queens", "STATEN ISLAND": "Staten Island"}
BORO_CODE = {"Manhattan": "1", "Bronx": "2", "Brooklyn": "3", "Queens": "4", "Staten Island": "5"}


def get_json(url, tries=4):
    for i in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                return json.load(r)
        except Exception:
            if i == tries - 1:
                raise
            time.sleep(2 * (i + 1))


def cached(name, fn):
    p = RAW / name
    if p.exists():
        return json.loads(p.read_text())
    v = fn()
    p.write_text(json.dumps(v))
    return v


def metres(a, b):
    """Approximate distance in metres between two (lat, lon) points."""
    dy = (a[0] - b[0]) * 111_320
    dx = (a[1] - b[1]) * 111_320 * math.cos(math.radians(a[0]))
    return math.hypot(dx, dy)


def norm_addr(s):
    s = re.sub(r"\s+", " ", s.upper().strip())
    s = re.sub(r"\b(\d+)(ST|ND|RD|TH)\b", r"\1", s)
    for a, b in ((" STREET", " ST"), (" AVENUE", " AVE"), (" PLACE", " PL"), (" ROAD", " RD"), (" BOULEVARD", " BLVD"),
                 (" PARKWAY", " PKWY"), ("EAST ", "E "), ("WEST ", "W ")):
        s = s.replace(a, b)
    return s


# 1. Records and duplicate merging
rows = [r for r in csv.DictReader(open(RAW / "incidents.csv")) if r["Incident Type"] in TYPES]
for r in rows:
    r["date"] = dt.datetime.strptime(r["Creation Date"], "%m/%d/%Y %I:%M:%S %p").date()
    r["boro"] = BORO.get(r["Borough"].strip().upper(), r["Borough"].strip())
    r["key"] = (norm_addr(r["Location"]), r["boro"])
rows.sort(key=lambda r: (r["key"], r["date"]))
events = []
for r in rows:
    e = events[-1] if events else None
    if e and e["key"] == r["key"] and (r["date"] - e["last"]).days <= 3:
        e["n_reports"] += 1
        e["last"] = r["date"]
        e["types"].add(r["Incident Type"])
        continue
    events.append({"key": r["key"], "address": r["Location"].strip(), "boro": r["boro"], "date": r["date"],
                   "last": r["date"], "n_reports": 1, "types": {r["Incident Type"]},
                   "oem_lat": float(r["Latitude"]) if r["Latitude"] else None,
                   "oem_lon": float(r["Longitude"]) if r["Longitude"] else None})

# OEM points shared by several different addresses are placeholders, not locations
pt_addrs = defaultdict(set)
for e in events:
    if e["oem_lat"] is not None:
        pt_addrs[(round(e["oem_lat"], 5), round(e["oem_lon"], 5))].add(e["key"])
placeholders = {p for p, a in pt_addrs.items() if len(a) > 1}

# 2. Geocoding (NYC Planning Geosearch v2; cached)
def geocode(e):
    q = urllib.parse.quote(f"{e['address']}, {e['boro']}, NY")
    d = get_json(f"https://geosearch.planninglabs.nyc/v2/search?text={q}&size=1")
    time.sleep(0.15)
    if not d.get("features"):
        return None
    f = d["features"][0]
    p = f["properties"]
    pad = (p.get("addendum") or {}).get("pad") or {}
    return {"label": p.get("label"), "confidence": p.get("confidence"), "match_type": p.get("match_type"),
            "layer": p.get("layer"), "borough": p.get("borough"), "bbl": pad.get("bbl"), "bin": pad.get("bin"),
            "lon": f["geometry"]["coordinates"][0], "lat": f["geometry"]["coordinates"][1]}


geo = cached("geosearch.json", lambda: {f"{e['address']}|{e['boro']}": geocode(e) for e in events})
for e in events:
    g = geo.get(f"{e['address']}|{e['boro']}")
    e["geo"] = g
    oem_ok = e["oem_lat"] is not None and (round(e["oem_lat"], 5), round(e["oem_lon"], 5)) not in placeholders
    e["oem_point_ok"] = oem_ok
    e["geo_boro_ok"] = bool(g) and (g.get("borough") or "").lower() == e["boro"].lower()
    # Geosearch v2 labels address hits as layer "venue"; count a hit as address-level only when it has a BBL and its
    # label starts with the record's house number (blank or intersection-only records then fail)
    hn = re.match(r"\s*(\d+(?:-\d+)?)\s+\S", e["address"])
    e["geo_addr_level"] = bool(g) and bool(g.get("bbl")) and bool(hn) and (g.get("label") or "").startswith(hn.group(1) + " ")
    e["dist_geo_oem_m"] = round(metres((g["lat"], g["lon"]), (e["oem_lat"], e["oem_lon"]))) if g and oem_ok else None

# 3. PLUTO attributes by BBL (current release)
bbls = sorted({e["geo"]["bbl"] for e in events if e["geo_addr_level"]})


def pluto():
    out = {}
    for i in range(0, len(bbls), 80):
        where = "bbl in (" + ",".join(f"'{b}'" for b in bbls[i:i + 80]) + ")"
        q = urllib.parse.urlencode({"$select": "bbl,yearbuilt,bldgclass,landuse,numfloors,unitsres,histdist",
                                    "$where": where, "$limit": 5000})
        for r in get_json(f"https://data.cityofnewyork.us/resource/64uk-42ks.json?{q}"):
            out[str(int(float(r["bbl"])))] = r
    return out


pl = cached("pluto.json", pluto)

# 4. DOB permits on the event's tax block, from both permit systems: BIS (ipu4-2q9a; NB new building, DM demolition,
# A1 major alteration) and DOB NOW: Build (rbx6-tga4; excavation, foundation and demolition work types). Same lot:
# any of these; adjacent (another lot on the block within 50 m): new building, demolition or excavation work only.
blocks = sorted({b[:6] for b in bbls})
NOW_TYPES = ("Full Demolition", "Foundation", "Earth Work", "Support of Excavation")
BORO_NAME = {"1": "MANHATTAN", "2": "BRONX", "3": "BROOKLYN", "4": "QUEENS", "5": "STATEN ISLAND"}


def permits():
    """BIS rows often lack a BBL, so BIS is queried by borough + block (text) and the BBL rebuilt; DOB NOW by BBL range."""
    out = []
    for i in range(0, len(blocks), 25):
        chunk = blocks[i:i + 25]
        bis = " or ".join(f"(borough='{BORO_NAME[b[0]]}' and block='{b[1:]}')" for b in chunk)
        q = urllib.parse.urlencode({"$select": "borough,block,lot,job_type,issuance_date,gis_latitude,gis_longitude",
                                    "$where": f"({bis}) and job_type in ('NB','DM','A1')", "$limit": 50000})
        out += [{"src": "BIS", "bbl": BORO_CODE[r["borough"].title()] + r["block"] + r["lot"][-4:],
                 "kind": r.get("job_type"), "date": r.get("issuance_date"),
                 "lat": r.get("gis_latitude"), "lon": r.get("gis_longitude")}
                for r in get_json(f"https://data.cityofnewyork.us/resource/ipu4-2q9a.json?{q}")
                if r.get("borough") and r.get("block") and r.get("lot")]
        rng = " or ".join(f"(bbl between {b}0000 and {b}9999)" for b in chunk)
        types = ",".join(f"'{t}'" for t in NOW_TYPES)
        q = urllib.parse.urlencode({"$select": "bbl,work_type,issued_date,latitude,longitude",
                                    "$where": f"({rng}) and work_type in ({types})", "$limit": 50000})
        out += [{"src": "NOW", "bbl": r.get("bbl"), "kind": r.get("work_type"), "date": r.get("issued_date"),
                 "lat": r.get("latitude"), "lon": r.get("longitude")}
                for r in get_json(f"https://data.cityofnewyork.us/resource/rbx6-tga4.json?{q}")]
    return out


pm_by_block = defaultdict(list)
for r in cached("permits_blocks.json", permits):
    if r.get("bbl"):
        pm_by_block[str(int(float(r["bbl"])))[:6]].append(r)


def pdate(s):
    try:
        return dt.datetime.strptime(s[:10], "%m/%d/%Y").date()
    except (TypeError, ValueError):
        try:
            return dt.date.fromisoformat(s[:10])
        except (TypeError, ValueError):
            return None


for e in events:
    b = e["geo"]["bbl"] if e["geo_addr_level"] else None
    p = pl.get(b, {}) if b else {}
    e["yearbuilt"] = int(float(p["yearbuilt"])) if p.get("yearbuilt") not in (None, "", "0") else None
    e["bldgclass"] = p.get("bldgclass")
    e["numfloors"] = p.get("numfloors")
    e["histdist"] = p.get("histdist")
    same, near, after = set(), set(), set()
    for r in pm_by_block.get(b[:6], []) if b else []:
        d = pdate(r.get("date") or "")
        if not d:
            continue
        lag = (e["date"] - d).days
        if str(int(float(r["bbl"]))) == b:
            if 0 <= lag <= 365:
                same.add(r["kind"])
            elif -365 <= lag < 0 and r["kind"] in ("DM", "NB", "Full Demolition"):
                after.add(r["kind"])
        elif 0 <= lag <= 365 and r["kind"] != "A1" and r.get("lat") and r.get("lon") and \
                metres((float(r["lat"]), float(r["lon"])), (e["geo"]["lat"], e["geo"]["lon"])) <= 50:
            near.add(r["kind"])
    e["works_before"] = ",".join(sorted(same))
    e["adjacent_works_before"] = ",".join(sorted(near))
    e["demo_or_nb_after"] = ",".join(sorted(after))
    e["replaced"] = bool(e["yearbuilt"] and e["yearbuilt"] > e["date"].year) or (e["bldgclass"] or "").startswith("V")
    e["insar_years_before"] = round((e["date"] - OPERA_START).days / 365.25, 2)

# 5. Funnel
located = [e for e in events if e["geo_addr_level"] and e["geo_boro_ok"]]
agree = [e for e in located if e["dist_geo_oem_m"] is None or e["dist_geo_oem_m"] <= 150]
building = [e for e in agree if e["bldgclass"]]
no_lot_works = [e for e in building if not e["works_before"]]
no_works = [e for e in no_lot_works if not e["adjacent_works_before"]]
stages = [("Records (Structural-Collapse + Partial Collapse)", len(rows)),
          ("Events after merging duplicate reports (same address, within 3 days)", len(events)),
          ("… geocoded to an address-level tax lot in the right borough", len(located)),
          ("… and within 150 m of the OEM point (or no usable OEM point)", len(agree)),
          ("… and the lot has a PLUTO record", len(building)),
          ("… and no major works permitted on the lot in the 365 days before", len(no_lot_works)),
          ("… and no new-building, demolition or excavation permit within 50 m on the block in the 365 days before",
           len(no_works))]
yrs = [(f"≥ {k} year(s) of OPERA history before the event", sum(e["insar_years_before"] >= k for e in no_works))
       for k in (0, 1, 2, 3)]

with open(OUT / "events_clean.csv", "w", newline="") as f:
    cols = ["address", "boro", "date", "n_reports", "types", "oem_lat", "oem_lon", "oem_point_ok", "geo_label",
            "geo_lat", "geo_lon", "bbl", "bin", "geo_addr_level", "geo_boro_ok", "dist_geo_oem_m", "yearbuilt",
            "bldgclass", "numfloors", "histdist", "works_before", "adjacent_works_before", "demo_or_nb_after", "replaced",
            "insar_years_before"]
    w = csv.DictWriter(f, fieldnames=cols)
    w.writeheader()
    for e in events:
        g = e["geo"] or {}
        w.writerow({**{c: e.get(c) for c in cols}, "types": "+".join(sorted(e["types"])), "geo_label": g.get("label"),
                    "geo_lat": g.get("lat"), "geo_lon": g.get("lon"), "bbl": g.get("bbl"), "bin": g.get("bin")})

by_year = Counter(e["date"].year for e in no_works)
ages = sorted(e["date"].year - e["yearbuilt"] for e in no_works if e["yearbuilt"] and e["yearbuilt"] <= e["date"].year)
cls = Counter((e["bldgclass"] or "?")[0] for e in no_works)
dists = sorted(e["dist_geo_oem_m"] for e in located if e["dist_geo_oem_m"] is not None)
lines = ["| Stage | Events |", "|---|---|"] + [f"| {a} | {b} |" for a, b in stages + yrs]
print("\n".join(lines))
print("placeholder OEM points:", {p: len(a) for p, a in pt_addrs.items() if p in placeholders})
print("events per year (final):", sorted(by_year.items()))
print("geocode-OEM distance m: median", dists[len(dists) // 2] if dists else None, "p90",
      dists[int(len(dists) * 0.9)] if dists else None, "n", len(dists))
print("building age at event: median", ages[len(ages) // 2] if ages else None, "n", len(ages),
      "share >= 80y", round(sum(a >= 80 for a in ages) / len(ages), 2) if ages else None)
print("building class first letter (final):", cls.most_common())
print("replaced since (yearbuilt after event or vacant lot):", sum(e["replaced"] for e in no_works))
print("DM/NB permit within a year after:", sum(bool(e["demo_or_nb_after"]) for e in no_works))
print("partial-only events (final):", sum(e["types"] == {"Structural-Partial Collapse"} for e in no_works))
print("distinct BBLs (final):", len({e["geo"]["bbl"] for e in no_works}))
(OUT / "funnel.md").write_text("\n".join(lines) + "\n")
