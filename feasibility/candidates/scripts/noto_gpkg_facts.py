"""Facts from the Noto Peninsula damage GeoPackage.

Counts features, class values, municipality tokens parsed from the
municipality field, and invalid geometries (Shapely is_valid).

Run:
  ~/miniforge3/envs/opera/bin/python -I feasibility/candidates/scripts/noto_gpkg_facts.py
"""

import json
import sqlite3
import struct
from pathlib import Path

from shapely import wkb
from shapely.validation import explain_validity

GPKG = Path("/mnt/data/Master-projects/Alex_private/candidates/raw/Noto_Peninsula_Damage_2_5.gpkg")
OUT = Path("/mnt/data/Master-projects/Alex_private/candidates/raw/noto_gpkg_facts.json")

# Second comma-separated token of the municipality field is the city or town.
MUNI = {
    "珠洲市": "Suzu",
    "輪島市": "Wajima",
    "能登町": "Noto",
    "穴水町": "Anamizu",
    "七尾市": "Nanao",
    "志賀町": "Shika",
}
ENV_LEN = {0: 0, 1: 32, 2: 48, 3: 48, 4: 64}


def load_geom(blob):
    if blob is None:
        return None, "null"
    if blob[:2] != b"GP":
        return wkb.loads(blob), "raw_wkb"
    flags = blob[3]
    envelope = (flags >> 1) & 7
    if envelope not in ENV_LEN:
        return None, f"bad_envelope_{envelope}"
    offset = 8 + ENV_LEN[envelope]
    return wkb.loads(blob[offset:]), "gpkg"


def main():
    con = sqlite3.connect(GPKG)
    cur = con.cursor()
    n = cur.execute('SELECT COUNT(*) FROM "v2.5"').fetchone()[0]
    invalid = []
    n_invalid = 0
    n_empty = 0
    n_parse_fail = 0
    # stream
    cur.execute('SELECT fid, geom FROM "v2.5"')
    checked = 0
    while True:
        batch = cur.fetchmany(5000)
        if not batch:
            break
        for fid, blob in batch:
            checked += 1
            try:
                geom, kind = load_geom(blob)
            except Exception as exc:
                n_parse_fail += 1
                n_invalid += 1
                if len(invalid) < 20:
                    invalid.append({"fid": fid, "reason": f"parse:{type(exc).__name__}"})
                continue
            if geom is None or geom.is_empty:
                n_empty += 1
                n_invalid += 1
                if len(invalid) < 20:
                    invalid.append({"fid": fid, "reason": "empty_or_null"})
                continue
            if not geom.is_valid:
                n_invalid += 1
                if len(invalid) < 20:
                    invalid.append({"fid": fid, "reason": explain_validity(geom)[:200]})
        print(f"checked {checked}", flush=True)

    # municipality token
    rows = cur.execute('SELECT municipality, damage_val, damage_2 FROM "v2.5"').fetchall()
    by = {}
    unknown = {}
    for muni, dv, d2 in rows:
        if muni is None:
            token = None
            name = None
        else:
            parts = [p.strip() for p in str(muni).split("、")]
            token = parts[1] if len(parts) > 1 else parts[0]
            name = MUNI.get(token)
        key = name or f"UNPARSED:{token}"
        slot = by.setdefault(key, {"n": 0, "damage_val": {}, "damage_2": {}})
        slot["n"] += 1
        slot["damage_val"][str(dv)] = slot["damage_val"].get(str(dv), 0) + 1
        slot["damage_2"][str(d2)] = slot["damage_2"].get(str(d2), 0) + 1
        if name is None:
            unknown[str(token)] = unknown.get(str(token), 0) + 1

    overall = {
        "damage_val": {},
        "damage_2": {},
    }
    for col in ("damage_val", "damage_2"):
        for val, cnt in cur.execute(f'SELECT "{col}", COUNT(*) FROM "v2.5" GROUP BY "{col}"'):
            overall[col][str(val)] = cnt

    facts = {
        "n_features": n,
        "n_checked_geometries": checked,
        "n_invalid_geometries": n_invalid,
        "n_empty_or_null_geometries": n_empty,
        "n_parse_failures": n_parse_fail,
        "invalid_examples": invalid,
        "overall": overall,
        "by_municipality_parsed_from_field": by,
        "unparsed_token_counts": unknown,
        "municipality_field_note": "Second comma-separated token of the municipality field.",
    }
    OUT.write_text(json.dumps(facts, ensure_ascii=False, indent=2))
    print("invalid", n_invalid, "wrote", OUT)


if __name__ == "__main__":
    main()
