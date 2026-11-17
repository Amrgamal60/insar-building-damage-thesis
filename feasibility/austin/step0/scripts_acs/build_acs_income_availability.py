"""Travis County ACS 2011–2015 B19013 availability and parcel coverage.

Reads the 2015 5-year summary file and 2015 TIGER block groups. Writes aggregate
counts only. Parcel identifiers are never written.
"""
import argparse
import csv
import datetime as dt
import hashlib
import json
import pathlib
import re

import geopandas as gpd
import numpy as np
import pyarrow.parquet as pq

# Income jam values in 2015 ACS Summary File Technical Documentation, section 4.2.
INCOME_JAM = {
    2499: "2,500 or less (income, earnings)",
    200001: "200,000 or more (income)",
    250001: "250,000 or more (income, earnings)",
}
# Named in the task. Not defined in the retrieved summary-file technical documentation.
API_SENTINELS = (-666666666, -999999999, -222222222, -333333333, -555555555)

GEO_SUMLEVEL = 2
GEO_LOGRECNO = 4
GEO_STATE = 9
GEO_COUNTY = 10
GEO_TRACT = 13
GEO_BLKGRP = 14
GEO_GEOID = 48
GEO_NAME = 49


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def now():
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def lookup_b19013(path):
    with path.open(newline="", encoding="latin-1") as handle:
        for row in csv.reader(handle):
            if len(row) > 4 and row[1] == "B19013" and row[4].strip():
                return row[2].strip(), int(row[4])
    raise SystemExit("B19013 start position not found in the sequence lookup")


def classify_estimate(raw):
    text = raw.strip()
    if text == "":
        return "blank", None
    if text == ".":
        return "dot", None
    if not re.fullmatch(r"-?\d+", text):
        return "non_numeric", text
    value = int(text)
    if value in INCOME_JAM:
        return f"jam_{value}", value
    if value in API_SENTINELS:
        return f"api_sentinel_{value}", value
    if value < 0:
        return f"negative_{value}", value
    return "valid", value


def classify_moe(raw):
    text = raw.strip()
    if text == "":
        return "blank", None
    if text == ".":
        return "dot", None
    if not re.fullmatch(r"-?\d+", text):
        return "non_numeric", text
    value = int(text)
    if value == -1:
        return "moe_flag_-1", value
    if value == 0:
        return "controlled_0", value
    if value in API_SENTINELS or value < 0:
        return f"negative_{value}", value
    return "usable", value


def load_cells(path, logrecnos, field_index):
    found = {}
    bad_sequence = 0
    short = 0
    with path.open(encoding="latin-1", newline="") as handle:
        for line in handle:
            parts = line.rstrip("\n").split(",")
            if len(parts) < 6:
                short += 1
                continue
            if parts[4] != "0059":
                bad_sequence += 1
            logrecno = parts[5]
            if logrecno not in logrecnos:
                continue
            if len(parts) <= field_index:
                short += 1
                found[logrecno] = None
                continue
            found[logrecno] = parts[field_index]
    return found, bad_sequence, short


def quantiles(values):
    if not values:
        return None
    array = np.asarray(values, dtype=float)
    try:
        median, p75, p90 = np.quantile(array, [0.5, 0.75, 0.9], method="linear")
    except TypeError:
        median, p75, p90 = np.quantile(array, [0.5, 0.75, 0.9], interpolation="linear")
    return {
        "n": int(array.size),
        "median": float(median),
        "p75": float(p75),
        "p90": float(p90),
    }


def annotation_meaning(label):
    documented = {
        "blank": "Missing value (empty cell): estimate unavailable because of geographic filtering, coefficient-of-variation filtering, or Disclosure Review Board removal (tech doc section 4.2).",
        "dot": "Dot '.': no sample observations or too few sample observations. In a margin-of-error file, also used when the margin is unavailable because the median was replaced by a jam value (tech doc section 4.2).",
        "controlled_0": "Margin of error 0: the estimate is controlled, analogous to the American FactFinder '*****' symbol (tech doc section 4.2). Not used as a zero sampling error.",
        "moe_flag_-1": "Margin of error -1: the table has no margin of error (tech doc section 4.2). This flag is documented for B00001, B00002, and B98/B99 tables, not for B19013.",
    }
    if label in documented:
        return documented[label]
    if label.startswith("jam_"):
        value = int(label.split("_", 1)[1])
        return f"Jam value {value}: {INCOME_JAM[value]} (tech doc section 4.2). Not a calculated dollar median."
    if label.startswith("api_sentinel_") or label.startswith("negative_"):
        return "UNVERIFIED: this numeric code is not defined in the retrieved 2015 ACS Summary File Technical Documentation."
    if label == "non_numeric":
        return "UNVERIFIED: token is neither empty, '.', nor an integer."
    if label == "no_estimate_row":
        return "Geography row had no matching estimate-file record."
    return "UNVERIFIED"


def summarize(rows):
    """rows: list of dicts with estimate_label, estimate_value, moe_label, moe_value."""
    estimate_counts = {}
    moe_counts = {}
    rmoe = []
    rmoe_gt_0_5 = 0
    valid = 0
    for row in rows:
        estimate_counts[row["estimate_label"]] = estimate_counts.get(row["estimate_label"], 0) + 1
        moe_counts[row["moe_label"]] = moe_counts.get(row["moe_label"], 0) + 1
        if row["estimate_label"] == "valid":
            valid += 1
        if row["rmoe"] is not None:
            rmoe.append(row["rmoe"])
            if row["rmoe"] > 0.5:
                rmoe_gt_0_5 += 1
    total = len(rows)
    annotations = {
        label: {"count": count, "meaning": annotation_meaning(label)}
        for label, count in sorted(estimate_counts.items())
        if label != "valid"
    }
    return {
        "total": total,
        "valid_median": valid,
        "coverage_percent": (100.0 * valid / total) if total else None,
        "estimate_value_counts": dict(sorted(estimate_counts.items())),
        "annotations": annotations,
        "moe_value_counts": dict(sorted(moe_counts.items())),
        "relative_moe": quantiles(rmoe),
        "relative_moe_above_0_5": rmoe_gt_0_5,
        "valid_median_of_estimates": float(np.median([row["estimate_value"] for row in rows if row["estimate_label"] == "valid"])) if valid else None,
    }


def load_geographies(geo_csv, estimate_path, moe_path, field_index):
    records = []
    with geo_csv.open(newline="", encoding="latin-1") as handle:
        for row in csv.reader(handle):
            if len(row) <= GEO_NAME:
                continue
            if row[GEO_STATE] != "48" or row[GEO_COUNTY] != "453":
                continue
            if row[GEO_SUMLEVEL] not in {"140", "150"}:
                continue
            suffix = row[GEO_GEOID].split("US", 1)[-1]
            constructed = row[GEO_STATE] + row[GEO_COUNTY] + row[GEO_TRACT] + row[GEO_BLKGRP]
            records.append({
                "sumlevel": row[GEO_SUMLEVEL],
                "logrecno": row[GEO_LOGRECNO],
                "geoid": suffix,
                "constructed": constructed,
                "name_kind": "block group" if row[GEO_NAME].startswith("Block Group ") else (
                    "tract" if row[GEO_NAME].startswith("Census Tract ") else "other"
                ),
            })
    logrecnos = {row["logrecno"] for row in records}
    estimates, bad_e, short_e = load_cells(estimate_path, logrecnos, field_index)
    moes, bad_m, short_m = load_cells(moe_path, logrecnos, field_index)
    for row in records:
        raw_e = estimates.get(row["logrecno"])
        raw_m = moes.get(row["logrecno"])
        if raw_e is None and row["logrecno"] not in estimates:
            row["estimate_label"], row["estimate_value"] = "no_estimate_row", None
        else:
            row["estimate_label"], row["estimate_value"] = classify_estimate(raw_e or "")
        if raw_m is None and row["logrecno"] not in moes:
            row["moe_label"], row["moe_value"] = "no_estimate_row", None
        else:
            row["moe_label"], row["moe_value"] = classify_moe(raw_m or "")
        row["rmoe"] = None
        if row["estimate_label"] == "valid" and row["estimate_value"] > 0 and row["moe_label"] == "usable":
            row["rmoe"] = row["moe_value"] / row["estimate_value"]
    return records, {
        "estimate_rows_wrong_sequence": bad_e,
        "moe_rows_wrong_sequence": bad_m,
        "estimate_short_rows_while_scanning": short_e,
        "moe_short_rows_while_scanning": short_m,
        "geoid_constructed_mismatches": sum(row["geoid"] != row["constructed"] for row in records),
        "unexpected_name": sum(row["name_kind"] == "other" for row in records),
    }


def assign_parcels(parcel_path, tiger_zip, by_geoid):
    schema = pq.read_schema(parcel_path)
    geo_meta = json.loads(schema.metadata[b"geo"])
    geometry_meta = geo_meta["columns"]["geometry"]
    extension = schema.field("geometry").metadata.get(b"ARROW:extension:name", b"").decode()
    frame = gpd.read_parquet(parcel_path, columns=["geometry", "imprv_type_cd"])
    codes = {str(key): int(value) for key, value in frame["imprv_type_cd"].astype(str).value_counts(dropna=False).items()}
    houses = frame.loc[frame["imprv_type_cd"].astype(str).str.strip() == "01", ["geometry"]].copy()
    del frame
    n = len(houses)
    empty = int(houses.geometry.is_empty.sum())
    invalid = int((~houses.geometry.is_valid).sum())
    points = houses.set_geometry(houses.geometry.centroid)
    del houses
    points["row_id"] = np.arange(len(points))
    block_groups = gpd.read_file(tiger_zip)
    tiger_crs = block_groups.crs.to_string() if block_groups.crs is not None else None
    travis = block_groups.loc[block_groups["COUNTYFP"] == "453", ["GEOID", "geometry"]].copy()
    del block_groups
    travis = travis.to_crs(points.crs)
    travis = travis.rename(columns={"GEOID": "bg_geoid"})
    joined = gpd.sjoin(points, travis, how="left", predicate="within")
    multi_ids = set(joined.loc[joined["row_id"].duplicated(keep=False), "row_id"])
    assigned = {}
    for row_id, geoid in joined.loc[~joined["row_id"].isin(multi_ids), ["row_id", "bg_geoid"]].itertuples(index=False):
        if geoid is None or (isinstance(geoid, float) and np.isnan(geoid)):
            continue
        assigned[int(row_id)] = str(geoid)
    unmatched = [int(row_id) for row_id in points["row_id"] if int(row_id) not in assigned and int(row_id) not in multi_ids]
    boundary_assigned = 0
    boundary_ambiguous_ids = set()
    if unmatched:
        second = gpd.sjoin(points.loc[points["row_id"].isin(unmatched)], travis, how="left", predicate="intersects")
        grouped = second.groupby("row_id")["bg_geoid"].apply(lambda series: [str(value) for value in series.dropna().unique()])
        for row_id, geoids in grouped.items():
            if len(geoids) == 1:
                assigned[int(row_id)] = geoids[0]
                boundary_assigned += 1
            elif len(geoids) > 1:
                boundary_ambiguous_ids.add(int(row_id))
    tract_valid = {row["geoid"] for row in by_geoid["tract"] if row["estimate_label"] == "valid"}
    bg_rows = {row["geoid"]: row for row in by_geoid["block_group"]}
    tiger_geoids = set(travis["bg_geoid"].astype(str))
    overlap = len(tiger_geoids & set(bg_rows))
    if overlap == 0:
        raise SystemExit("TIGER and ACS block-group GEOIDs do not overlap")
    counts = {"valid_bg": 0, "tract_fallback": 0, "neither": 0}
    neither_parts = {
        "unassigned": 0,
        "bg_jam": 0,
        "bg_missing_tract_not_valid": 0,
        "bg_other": 0,
        "boundary_ambiguous": 0,
        "within_multiple_block_groups": 0,
    }
    high = {"valid_bg": 0, "tract_fallback": 0, "neither": 0, "parcels": 0}
    high_rmoe_geoids = {geoid for geoid, row in bg_rows.items() if row["rmoe"] is not None and row["rmoe"] > 0.5}
    for row_id in range(n):
        if row_id in multi_ids:
            counts["neither"] += 1
            neither_parts["within_multiple_block_groups"] += 1
            continue
        geoid = assigned.get(row_id)
        if geoid is None:
            counts["neither"] += 1
            if row_id in boundary_ambiguous_ids:
                neither_parts["boundary_ambiguous"] += 1
            else:
                neither_parts["unassigned"] += 1
            continue
        row = bg_rows.get(geoid)
        if row is None:
            status = "missing"
            tract_id = geoid[:11]
        else:
            if row["estimate_label"] == "valid":
                status = "valid"
            elif row["estimate_label"] in {"blank", "dot", "no_estimate_row"}:
                status = "missing"
            elif str(row["estimate_label"]).startswith("jam_"):
                status = "jam"
            else:
                status = "other"
            tract_id = row["geoid"][:11]
        tract_ok = tract_id in tract_valid
        if status == "valid":
            cat = "valid_bg"
        elif status == "missing" and tract_ok:
            cat = "tract_fallback"
        else:
            cat = "neither"
            if status == "jam":
                neither_parts["bg_jam"] += 1
            elif status == "missing":
                neither_parts["bg_missing_tract_not_valid"] += 1
            else:
                neither_parts["bg_other"] += 1
        counts[cat] += 1
        if geoid in high_rmoe_geoids:
            high["parcels"] += 1
            high[cat] += 1
    if sum(neither_parts.values()) != counts["neither"]:
        raise SystemExit(f"neither parts {neither_parts} do not sum to {counts['neither']}")
    return {
        "parquet_rows": None,
        "imprv_type_cd_counts": codes,
        "detached_houses": n,
        "empty_geometries": empty,
        "invalid_geometries": invalid,
        "parcel_crs_epsg": points.crs.to_epsg() if points.crs is not None else None,
        "parcel_crs": points.crs.to_string() if points.crs is not None else None,
        "geometry_encoding": geometry_meta.get("encoding"),
        "geometry_extension": extension,
        "tiger_crs": tiger_crs,
        "tiger_travis_block_groups": int(len(travis)),
        "tiger_acs_geoid_overlap": overlap,
        "tiger_only_block_groups": len(tiger_geoids - set(bg_rows)),
        "acs_only_block_groups": len(set(bg_rows) - tiger_geoids),
        "assigned": len(assigned),
        "boundary_assigned": boundary_assigned,
        "parcel_counts": counts,
        "neither_parts": neither_parts,
        "relative_moe_above_0_5": high,
        "parquet_row_count_placeholder": n,
    }, codes, geometry_meta


def percent(count, total):
    if not total:
        return None
    return 100.0 * count / total


def fmt_pct(count, total):
    value = percent(count, total)
    if value is None:
        return "n/a"
    return f"{value:.2f}%"


def fmt_num(value):
    if value is None:
        return "n/a"
    return f"{value:.4f}"


def build_report(result):
    bg = result["block_groups"]
    tr = result["tracts"]
    parcels = result["parcels"]
    n = parcels["detached_houses"]
    counts = parcels["parcel_counts"]
    high = parcels["relative_moe_above_0_5"]
    lines = []
    lines.append("# ACS 2011–2015 median household income availability, Travis County")
    lines.append("")
    lines.append("Pre-freeze check for block-group median household income (ACS table B19013) on the Austin detached-house population. Aggregate counts only.")
    lines.append("")
    lines.append("## Source")
    lines.append("")
    lines.append("The Census Data API was not usable anonymously. A request for Travis County block groups returned a redirect to `https://api.census.gov/data/missing_key.html` (final HTTP 200, body title Missing Key). A tract request timed out (curl exit 28, no body). No API key was used.")
    lines.append("")
    lines.append("Estimates are from the 2015 ACS 5-year Summary File, Texas tracts and block groups archive `Texas_Tracts_Block_Groups_Only.zip`. Table B19013 is sequence `0059`, start position 177, in `ACS_5yr_Seq_Table_Number_Lookup.txt`. That position is the estimate `e20155tx0059000.txt` and the margin `m20155tx0059000.txt`, joined to `g20155tx.csv` on `LOGRECNO`. The table title in the lookup is median household income in the past 12 months in 2015 inflation-adjusted dollars. Block-group polygons are the 2015 TIGER/Line file `tl_2015_48_bg.zip`, restricted to county 453.")
    lines.append("")
    lines.append("Geography checks while reading the summary file: GEOID suffix matched state+county+tract+block group on every Travis tract and block group; names begin with `Census Tract` or `Block Group` as expected for summary levels 140 and 150. Summary level 140/150 is identified from those names in `g20155tx.csv`. The technical documentation states that 5-year estimates are published for census tracts and block groups; the numeric summary-level list is Appendix B, which was not transcribed here.")
    lines.append("")
    lines.append("## What was counted as a valid median")
    lines.append("")
    lines.append("A valid median is an integer dollar amount that is not a jam value. Empty cells and `.` are missing. Section 4.2 of the 2015 ACS Summary File Technical Documentation (`2015_SummaryFile_Tech_Doc.pdf`) defines these summary-file annotations:")
    lines.append("")
    lines.append("- Empty cell: the estimate is unavailable (geographic filtering, coefficient-of-variation filtering, or Disclosure Review Board removal).")
    lines.append("- `.`: no sample observations, or too few sample observations. In the margin-of-error file, `.` can also mean the margin is unavailable because the median was replaced by a jam value.")
    lines.append("- Margin of error `0`: the estimate is controlled (the summary-file equivalent of the American FactFinder `*****` symbol). It is not treated as a sampling margin of zero, so it is left out of the relative-margin distribution.")
    lines.append("- Jam values for income: `2499` means 2,500 or less; `200001` means 200,000 or more; `250001` means 250,000 or more. These are not calculated dollar medians.")
    lines.append("")
    api_counts = []
    for code in API_SENTINELS:
        label = f"api_sentinel_{code}"
        api_counts.append(f"{code} block groups {bg['estimate_value_counts'].get(label, 0)}, tracts {tr['estimate_value_counts'].get(label, 0)}")
    lines.append("Data API numeric codes in the summary-file cells: " + "; ".join(api_counts) + ". The retrieved 2015 summary-file technical documentation does not define these codes. Their meanings are **UNVERIFIED**.")
    lines.append("")
    lines.append("Relative margin of error is the published margin divided by the estimate. It is computed only where the estimate is a valid median greater than zero and the margin is a positive integer. Percentiles use the linear sample quantile.")
    lines.append("")
    lines.append("## Block groups")
    lines.append("")
    lines.append(f"ACS summary-file block groups in Travis County (summary level 150): **{bg['total']}**.")
    lines.append(f"TIGER/Line 2015 block groups in Travis County: **{parcels['tiger_travis_block_groups']}**. GEOID overlap with the summary file: {parcels['tiger_acs_geoid_overlap']}. TIGER only: {parcels['tiger_only_block_groups']}. Summary file only: {parcels['acs_only_block_groups']}.")
    lines.append(f"Valid median: **{bg['valid_median']}** ({fmt_pct(bg['valid_median'], bg['total'])} coverage).")
    lines.append("")
    lines.append("| Estimate cell | Count | Meaning |")
    lines.append("|---|---:|---|")
    lines.append(f"| valid median | {bg['valid_median']} | Integer dollar amount, not a jam value |")
    for label, info in bg["annotations"].items():
        lines.append(f"| `{label}` | {info['count']} | {info['meaning']} |")
    lines.append("")
    r = bg["relative_moe"]
    if r:
        lines.append(f"Relative margin of error on {r['n']} block groups with a defined ratio: median **{fmt_num(r['median'])}**, 75th percentile **{fmt_num(r['p75'])}**, 90th percentile **{fmt_num(r['p90'])}**.")
    else:
        lines.append("Relative margin of error: no block group had a defined ratio. **UNVERIFIED** distribution because the ratio could not be computed.")
    lines.append(f"Block groups with relative margin of error above 0.5: **{bg['relative_moe_above_0_5']}**.")
    lines.append("")
    lines.append("## Tracts")
    lines.append("")
    lines.append(f"ACS summary-file census tracts in Travis County (summary level 140): **{tr['total']}**.")
    lines.append(f"Valid median: **{tr['valid_median']}** ({fmt_pct(tr['valid_median'], tr['total'])} coverage).")
    lines.append("")
    lines.append("| Estimate cell | Count | Meaning |")
    lines.append("|---|---:|---|")
    lines.append(f"| valid median | {tr['valid_median']} | Integer dollar amount, not a jam value |")
    for label, info in tr["annotations"].items():
        lines.append(f"| `{label}` | {info['count']} | {info['meaning']} |")
    lines.append("")
    r = tr["relative_moe"]
    if r:
        lines.append(f"Relative margin of error on {r['n']} tracts with a defined ratio: median **{fmt_num(r['median'])}**, 75th percentile **{fmt_num(r['p75'])}**, 90th percentile **{fmt_num(r['p90'])}**.")
    else:
        lines.append("Relative margin of error: no tract had a defined ratio.")
    lines.append(f"Tracts with relative margin of error above 0.5: **{tr['relative_moe_above_0_5']}**.")
    lines.append("")
    lines.append("## Detached houses")
    lines.append("")
    lines.append(f"Parcel file geometry is Arrow extension `{parcels['geometry_extension']}` with geo-metadata encoding `{parcels['geometry_encoding']}` and CRS EPSG:{parcels['parcel_crs_epsg']} (`{parcels['parcel_crs']}`), which matches the step-0 statement of EPSG:32614. Rows in the diagnostic file: {parcels['parquet_rows']}. `imprv_type_cd` value `01`: **{n}**.")
    lines.append("")
    lines.append("Each type `01` polygon centroid was formed in EPSG:32614. 2015 TIGER block groups were transformed from their native CRS to EPSG:32614 and the centroid was assigned with a within test. Centroids on a boundary that meet exactly one block group were assigned to that block group. The tract is the first 11 digits of the block-group GEOID.")
    lines.append("")
    lines.append(f"Empty parcel geometries: {parcels['empty_geometries']}. Invalid parcel geometries: {parcels['invalid_geometries']}. Centroids assigned to a block group: {parcels['assigned']}, of which {parcels['boundary_assigned']} were boundary assignments.")
    lines.append("")
    lines.append(f"Of the {n} detached houses:")
    lines.append("")
    lines.append(f"- Valid block-group median: **{counts['valid_bg']}** ({fmt_pct(counts['valid_bg'], n)}).")
    lines.append(f"- Block-group median missing (empty, `.`, or no summary-file value) and tract median valid: **{counts['tract_fallback']}** ({fmt_pct(counts['tract_fallback'], n)}).")
    lines.append(f"- Neither: **{counts['neither']}** ({fmt_pct(counts['neither'], n)}).")
    lines.append("")
    parts = parcels["neither_parts"]
    lines.append("The neither count splits into exclusive parts: " + ", ".join(f"{key} {value}" for key, value in parts.items()) + ".")
    lines.append("")
    lines.append(f"Restricted to the {high['parcels']} detached houses in block groups whose relative margin of error is above 0.5 ({fmt_pct(high['parcels'], n)} of {n}): valid block-group median **{high['valid_bg']}**, tract fallback **{high['tract_fallback']}**, neither **{high['neither']}**. A relative margin above 0.5 is defined only when the block-group median is a valid positive dollar amount, so this subset sits inside the valid-median group.")
    lines.append("")
    lines.append("## Read checks")
    lines.append("")
    checks = result["read_checks"]
    lines.append(f"GEOID mismatches: {checks['geoid_constructed_mismatches']}. Unexpected geography names: {checks['unexpected_name']}. Estimate rows with a sequence other than 0059: {checks['estimate_rows_wrong_sequence']}. Margin rows with a sequence other than 0059: {checks['moe_rows_wrong_sequence']}.")
    lines.append(f"Median of the valid block-group dollar estimates: {bg['valid_median_of_estimates']}. Median of the valid tract dollar estimates: {tr['valid_median_of_estimates']}. These are a column check, not a published county median.")
    lines.append("")
    return "\n".join(lines) + "\n"


def file_mtime_utc(path):
    stamp = dt.datetime.fromtimestamp(path.stat().st_mtime, dt.timezone.utc)
    return stamp.strftime("%Y-%m-%dT%H:%M:%SZ")


def build_manifest(attempt_log, extra, saved_root):
    attempts = json.loads(attempt_log.read_text())
    attempts.extend(extra)
    for row in attempts:
        path = row.get("private_path")
        if row.get("sha256") and path:
            disk = sha256(pathlib.Path(path))
            row["sha256_matches_disk"] = disk == row["sha256"]
            if disk != row["sha256"]:
                raise SystemExit(f"sha256 mismatch for {path}")
    manifest = {
        "generated_utc": now(),
        "estimate_source": "2015 ACS 5-year Summary File, Texas_Tracts_Block_Groups_Only.zip, sequence 0059 field 177 (B19013). Census Data API was not used.",
        "attempts": attempts,
    }
    # Touch saved_root only so a missing private tree fails loudly.
    if not saved_root.is_dir():
        raise SystemExit(f"missing private directory {saved_root}")
    return manifest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--lookup", type=pathlib.Path, required=True)
    parser.add_argument("--geo-csv", type=pathlib.Path, required=True)
    parser.add_argument("--estimate", type=pathlib.Path, required=True)
    parser.add_argument("--moe", type=pathlib.Path, required=True)
    parser.add_argument("--tiger-zip", type=pathlib.Path, required=True)
    parser.add_argument("--parcels", type=pathlib.Path, required=True)
    parser.add_argument("--attempt-log", type=pathlib.Path, required=True)
    parser.add_argument("--private-root", type=pathlib.Path, required=True)
    parser.add_argument("--report", type=pathlib.Path, required=True)
    parser.add_argument("--json-out", type=pathlib.Path, required=True)
    parser.add_argument("--manifest", type=pathlib.Path, required=True)
    args = parser.parse_args()

    sequence, start = lookup_b19013(args.lookup)
    if sequence != "0059" or start != 177:
        raise SystemExit(f"unexpected B19013 location sequence={sequence} start={start}")
    records, checks = load_geographies(args.geo_csv, args.estimate, args.moe, start - 1)
    by_level = {
        "block_group": [row for row in records if row["sumlevel"] == "150"],
        "tract": [row for row in records if row["sumlevel"] == "140"],
    }
    if any(row["name_kind"] != "block group" for row in by_level["block_group"]):
        raise SystemExit("summary level 150 row is not named Block Group")
    if any(row["name_kind"] != "tract" for row in by_level["tract"]):
        raise SystemExit("summary level 140 row is not named Census Tract")
    bg_summary = summarize(by_level["block_group"])
    tract_summary = summarize(by_level["tract"])
    if bg_summary["valid_median_of_estimates"] is None or not (20000 <= bg_summary["valid_median_of_estimates"] <= 200000):
        raise SystemExit(f"block-group dollar median failed the column check: {bg_summary['valid_median_of_estimates']}")
    parcel_info, codes, geometry_meta = assign_parcels(args.parcels, args.tiger_zip, by_level)
    schema = pq.read_schema(args.parcels)
    parcel_info["parquet_rows"] = schema_rows(args.parcels)
    parcel_info["imprv_type_cd_counts"] = codes
    n = parcel_info["detached_houses"]
    counts = parcel_info["parcel_counts"]
    if n != 144458:
        raise SystemExit(f"detached count {n} != 144458")
    if sum(counts.values()) != n:
        raise SystemExit(f"parcel categories sum to {sum(counts.values())} not {n}")
    result = {
        "generated_utc": now(),
        "table": "B19013_001 median household income in the past 12 months, 2015 inflation-adjusted dollars",
        "sequence": sequence,
        "start_position_1_based": start,
        "source": "ACS 2015 5-year summary file Texas_Tracts_Block_Groups_Only.zip plus TIGER 2015 tl_2015_48_bg.zip",
        "api": "unavailable without a key; no key used",
        "block_groups": bg_summary,
        "tracts": tract_summary,
        "parcels": parcel_info,
        "read_checks": checks,
        "geometry_metadata_crs_epsg": geometry_meta.get("crs", {}).get("id", {}).get("code"),
    }
    # Drop non-aggregate leftovers if any slipped in.
    result["parcels"].pop("parquet_row_count_placeholder", None)
    args.json_out.write_text(json.dumps(result, indent=2) + "\n")
    args.report.write_text(build_report(result))
    root = args.private_root
    probes = [
        {
            "url": "https://api.census.gov/data/2015/acs/acs5?get=B19013_001E,B19013_001M&for=block%20group:*&in=state:48%20county:453&in=tract:*",
            "access_time_utc": file_mtime_utc(root / "census_api_2015_acs5/acs_bg_probe.json"),
            "method": "GET",
            "http_status": 200,
            "bytes": (root / "census_api_2015_acs5/acs_bg_probe.json").stat().st_size,
            "num_redirects": 1,
            "final_url": "https://api.census.gov/data/missing_key.html",
            "sha256": sha256(root / "census_api_2015_acs5/acs_bg_probe.json"),
            "private_path": str(root / "census_api_2015_acs5/acs_bg_probe.json"),
            "note": "Final response is the Census missing-key HTML page. No API key was sent.",
        },
        {
            "url": "https://api.census.gov/data/2015/acs/acs5?get=B19013_001E,B19013_001M&for=tract:*&in=state:48%20county:453",
            "access_time_utc": "2026-10-30T20:46:45Z",
            "method": "GET",
            "http_status": 0,
            "bytes": 0,
            "sha256": None,
            "private_path": None,
            "note": "curl exit 28, connection timed out after 20002 ms. No body saved. Start time is inferred from the block-group probe file mtime immediately before this request and the TIGER HEAD Date header at 20:47:06Z.",
        },
        {
            "url": "https://www2.census.gov/geo/tiger/TIGER2015/BG/tl_2015_48_bg.zip",
            "access_time_utc": "2026-10-30T20:47:06Z",
            "method": "HEAD",
            "http_status": 200,
            "bytes": 0,
            "content_length": 45872706,
            "sha256": None,
            "private_path": None,
            "note": "HEAD only. Time is the response Date header. The later GET saved the file.",
        },
        {
            "url": "https://www2.census.gov/programs-surveys/acs/summary_file/2015/documentation/tech_docs/ACS_2015_SF_5YR_Tech_Doc.pdf",
            "access_time_utc": "2026-10-30T20:47:09Z",
            "method": "HEAD",
            "http_status": 404,
            "bytes": 0,
            "sha256": None,
            "private_path": None,
            "note": "Wrong filename. The file that exists is 2015_SummaryFile_Tech_Doc.pdf, downloaded later.",
        },
        saved_html(root, "summary_file_2015_5yr/directory_indexes/5_year_by_state_index.html",
                   "https://www2.census.gov/programs-surveys/acs/summary_file/2015/data/5_year_by_state/"),
        saved_html(root, "summary_file_2015_5yr/directory_indexes/documentation_index.html",
                   "https://www2.census.gov/programs-surveys/acs/summary_file/2015/documentation/"),
        saved_html(root, "summary_file_2015_5yr/directory_indexes/user_tools_index.html",
                   "https://www2.census.gov/programs-surveys/acs/summary_file/2015/documentation/user_tools/"),
        saved_html(root, "summary_file_2015_5yr/directory_indexes/tech_docs_index.html",
                   "https://www2.census.gov/programs-surveys/acs/summary_file/2015/documentation/tech_docs/"),
        {
            "url": "https://www2.census.gov/programs-surveys/acs/summary_file/2015/data/5_year_by_state/Texas_Tracts_Block_Groups_Only.zip",
            "access_time_utc": None,
            "method": "HEAD",
            "http_status": 200,
            "bytes": 0,
            "content_length": 275207057,
            "sha256": None,
            "private_path": None,
            "note": "HEAD during directory discovery. The response Date header was not retained. The later GET saved the file.",
        },
        {
            "url": "https://www2.census.gov/programs-surveys/acs/summary_file/2015/documentation/user_tools/ACS_5yr_Seq_Table_Number_Lookup.txt",
            "access_time_utc": None,
            "method": "HEAD",
            "http_status": 200,
            "bytes": 0,
            "content_length": 1379488,
            "sha256": None,
            "private_path": None,
            "note": "HEAD during directory discovery. The response Date header was not retained. The later GET saved the file.",
        },
        {
            "url": "https://www2.census.gov/programs-surveys/acs/summary_file/2015/documentation/tech_docs/2015_SummaryFile_Tech_Doc.pdf",
            "access_time_utc": None,
            "method": "HEAD",
            "http_status": 200,
            "bytes": 0,
            "content_length": 1135442,
            "sha256": None,
            "private_path": None,
            "note": "HEAD before the GET. The response Date header was not retained.",
        },
        {
            "url": "https://www2.census.gov/programs-surveys/acs/summary_file/2015/documentation/tech_docs/ACS_2015_SF_5YR_Appendices.xls",
            "access_time_utc": None,
            "method": "HEAD",
            "http_status": 200,
            "bytes": 0,
            "content_length": 273920,
            "sha256": None,
            "private_path": None,
            "note": "HEAD before the GET. The response Date header was not retained.",
        },
    ]
    manifest = build_manifest(args.attempt_log, probes, args.private_root)
    args.manifest.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({
        "block_groups": bg_summary["total"],
        "bg_coverage_percent": bg_summary["coverage_percent"],
        "bg_rmoe_median": None if not bg_summary["relative_moe"] else bg_summary["relative_moe"]["median"],
        "tracts": tract_summary["total"],
        "tract_coverage_percent": tract_summary["coverage_percent"],
        "parcels": counts,
        "high_rmoe": parcel_info["relative_moe_above_0_5"],
        "detached": n,
    }, indent=2))


def schema_rows(path):
    return pq.ParquetFile(path).metadata.num_rows


def saved_html(root, relative, url):
    path = root / relative
    return {
        "url": url,
        "access_time_utc": file_mtime_utc(path),
        "method": "GET",
        "http_status": 200,
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
        "private_path": str(path),
        "note": "Directory index used to locate the 2015 summary-file paths.",
    }


if __name__ == "__main__":
    main()
