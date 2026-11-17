"""Apply the locked keyword regex and exclusion rules. Write counts and an A4 sample.

The regex and exclusion rules are copied from keyword_protocol.md and are not
edited to fit the counts.

Run:
  ~/miniforge3/envs/opera/bin/python -I feasibility/candidates/scripts/filter_keyword_matches.py
"""

import json
import math
import random
import re
from collections import Counter
from datetime import datetime
from pathlib import Path

RAW = Path("/mnt/data/Master-projects/Alex_private/candidates/raw")
PRIV = Path("/mnt/data/Master-projects/Alex_private/candidates")
PROJ = Path("/mnt/data/Master-projects/Alex/feasibility/candidates")

# Locked in keyword_protocol.md before any match counts.
RX = re.compile(
    r"foundation|underpin(?:ning)?|slab repair|levell?ing|house level|mudjack|re-level|\bshim\b|helical|(?:push )?pier(?:s|ing)?",
    re.I,
)
REPAIR_LANG = re.compile(
    r"foundation repair|underpin|helical|mudjack|house level|re-level|\bshim\b|slab repair|levell?ing|(?:push )?pier(?:s|ing)?",
    re.I,
)
NEW_MARK = re.compile(
    r"\bnew construction\b|\bnew building\b|\bnew single[\s-]*family\b|\bnew s\.?\s?f\.?\b|\bnew residence\b|\bnew residential\b|\bnew commercial\b|\bnew duplex\b|\bnew home\b|\bnew structure\b",
    re.I,
)
POOL = re.compile(r"\bswimming pool\b|\bpool\b|\bspa\b", re.I)
SIGN = re.compile(r"\bbillboard\b|\bmonument sign\b|\bsign\b", re.I)
WALL = re.compile(r"\bretaining wall\b|\bscreen wall\b|\bfence footing\b", re.I)
WATER_PIER = re.compile(r"\bdock\b|\bboat pier\b|\bfishing pier\b|\bbridge pier\b|\bwaterfront\b", re.I)


def blob_austin(row):
    parts = [
        row.get("description"),
        row.get("work_class"),
        row.get("permit_class"),
        row.get("permittype"),
        row.get("permit_type_desc"),
    ]
    return " \n ".join("" if v is None else str(v) for v in parts)


def exclusion(text, work_class):
    """Return the first matching exclusion code, or None to keep the row."""
    wc = (work_class or "").strip().lower()
    is_new = wc in {"new", "new construction"} or bool(NEW_MARK.search(text))
    has_repair_lang = bool(REPAIR_LANG.search(text))
    # 1. New construction whose only foundation language is installation of a new foundation.
    # The phrases below are the examples written in keyword_protocol.md.
    installs_new = re.search(r"foundation only|new foundation|pour foundation", text, re.I)
    if is_new and not has_repair_lang and installs_new:
        return "new_construction_foundation_only"
    # 2. Pool or spa, and the keyword hit is not building-foundation repair language.
    if POOL.search(text) and not has_repair_lang:
        return "pool"
    # 3. Sign.
    if SIGN.search(text) and not has_repair_lang:
        return "sign"
    # 4. Retaining wall / screen wall / fence footing only.
    if WALL.search(text) and not has_repair_lang:
        return "retaining_wall"
    # 5. Waterfront, dock, boat, fishing, or bridge pier, with no other foundation language.
    if WATER_PIER.search(text) and not re.search(r"foundation|underpin|helical|mudjack|levell?ing|house level|slab repair", text, re.I):
        return "pier_not_foundation"
    return None


def parse_date(value):
    if not value:
        return None
    s = str(value).replace("Z", "")
    for fmt in ("%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S", "%Y/%m/%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(s[:26], fmt)
        except ValueError:
            continue
    return None


def usable_coord(lat, lon):
    try:
        lat = float(lat)
        lon = float(lon)
    except (TypeError, ValueError):
        return False
    if not math.isfinite(lat) or not math.isfinite(lon):
        return False
    if lat == 0 and lon == 0:
        return False
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        return False
    return True


def clopper_pearson(k, n, alpha=0.05):
    """95% Clopper-Pearson interval from the binomial tail definition.

    Tails are summed in log space. Lower p_L solves P(X >= k) = alpha/2.
    Upper p_U solves P(X <= k) = alpha/2. Endpoints are 0 or 1 when k is 0 or n.
    """
    if n == 0:
        return None

    def log_pmf(j, p):
        if j < 0 or j > n:
            return float("-inf")
        return (
            math.lgamma(n + 1) - math.lgamma(j + 1) - math.lgamma(n - j + 1)
            + j * math.log(p) + (n - j) * math.log(1 - p)
        )

    def cdf_le(j, p):
        if j < 0:
            return 0.0
        if p <= 0:
            return 1.0
        if p >= 1:
            return 1.0 if j >= n else 0.0
        logs = [log_pmf(i, p) for i in range(0, j + 1)]
        m = max(logs)
        return min(1.0, math.exp(m + math.log(sum(math.exp(x - m) for x in logs))))

    def cdf_ge(j, p):
        if j <= 0:
            return 1.0
        return 1.0 - cdf_le(j - 1, p)

    if k <= 0:
        lo = 0.0
    else:
        a, b = 0.0, 1.0
        for _ in range(80):
            mid = (a + b) / 2
            # P(X >= k) increases with p.
            if cdf_ge(k, mid) > alpha / 2:
                b = mid
            else:
                a = mid
        lo = (a + b) / 2
    if k >= n:
        hi = 1.0
    else:
        a, b = 0.0, 1.0
        for _ in range(80):
            mid = (a + b) / 2
            # P(X <= k) decreases with p.
            if cdf_le(k, mid) > alpha / 2:
                a = mid
            else:
                b = mid
        hi = (a + b) / 2
    return [lo, hi]


def year_counts(dates):
    out = {str(y): 0 for y in range(2010, 2027)}
    out["before_2010"] = 0
    out["after_2026"] = 0
    out["missing_date"] = 0
    for d in dates:
        if d is None:
            out["missing_date"] += 1
        elif d.year < 2010:
            out["before_2010"] += 1
        elif d.year > 2026:
            out["after_2026"] += 1
        else:
            out[str(d.year)] += 1
    return out


def on_or_after(dates, y, m, day):
    cut = datetime(y, m, day)
    return sum(1 for d in dates if d is not None and d >= cut)


def norm_addr(value):
    if value is None:
        return None
    s = re.sub(r"\s+", " ", str(value).strip().upper())
    return s or None


def filter_rows(rows, text_fn, work_class_fn):
    kept = []
    excluded = Counter()
    superset_no_regex = 0
    for row in rows:
        text = text_fn(row)
        if not RX.search(text):
            superset_no_regex += 1
            continue
        reason = exclusion(text, work_class_fn(row))
        if reason:
            excluded[reason] += 1
            continue
        kept.append(row)
    return kept, dict(excluded), superset_no_regex


def main():
    austin = json.loads((RAW / "austin_keyword_superset.json").read_text())
    kept, excluded, no_rx = filter_rows(austin, blob_austin, lambda r: r.get("work_class"))
    dates = [parse_date(r.get("issue_date")) for r in kept]
    addrs = [norm_addr(r.get("original_address1")) for r in kept]
    addr_counts = Counter(a for a in addrs if a)
    parcels = [norm_addr(r.get("tcad_id")) for r in kept]
    parcel_counts = Counter(p for p in parcels if p)
    n = len(kept)
    n_coord = sum(1 for r in kept if usable_coord(r.get("latitude"), r.get("longitude")))
    n_addr = sum(1 for a in addrs if a)
    n_addr_no_coord = sum(
        1 for r, a in zip(kept, addrs)
        if a and not usable_coord(r.get("latitude"), r.get("longitude"))
    )
    desc_counts = Counter((r.get("description") or "").strip() for r in kept)
    top30 = desc_counts.most_common(30)
    type_counts = Counter((r.get("permit_class_mapped") or "") for r in kept)
    work_counts = Counter((r.get("work_class") or "") for r in kept)
    ptype_counts = Counter((r.get("permittype") or "") for r in kept)

    rng = random.Random(20261026)
    sample_n = min(60, n)
    sample = rng.sample(kept, sample_n) if sample_n else []
    sample_out = []
    for r in sample:
        sample_out.append({
            "permit_number": r.get("permit_number"),
            "issue_date": r.get("issue_date"),
            "permittype": r.get("permittype"),
            "permit_type_desc": r.get("permit_type_desc"),
            "permit_class": r.get("permit_class"),
            "permit_class_mapped": r.get("permit_class_mapped"),
            "work_class": r.get("work_class"),
            "description": r.get("description"),
            "original_address1": r.get("original_address1"),
            "tcad_id": r.get("tcad_id"),
        })
    (PRIV / "samples" / "austin_a4_sample.json").write_text(json.dumps(sample_out, indent=2))

    austin_stats = {
        "superset_n": len(austin),
        "superset_failed_locked_regex": no_rx,
        "excluded": excluded,
        "matched_n": n,
        "by_year": year_counts(dates),
        "issued_on_or_after_2016_07_01": on_or_after(dates, 2016, 7, 1),
        "issued_on_or_after_2018_07_01": on_or_after(dates, 2018, 7, 1),
        "unique_addresses": len(addr_counts),
        "addresses_with_more_than_one_matched_permit": sum(1 for c in addr_counts.values() if c > 1),
        "permits_with_blank_address": n - n_addr,
        "unique_tcad_id": len(parcel_counts),
        "tcad_id_with_more_than_one_matched_permit": sum(1 for c in parcel_counts.values() if c > 1),
        "permits_with_blank_tcad_id": sum(1 for p in parcels if not p),
        "usable_coordinates": n_coord,
        "share_usable_coordinates": (n_coord / n) if n else None,
        "address_present": n_addr,
        "share_address_present": (n_addr / n) if n else None,
        "address_present_without_usable_coordinates": n_addr_no_coord,
        "share_address_present_without_usable_coordinates": (n_addr_no_coord / n) if n else None,
        "permit_class_mapped_counts": dict(type_counts),
        "work_class_counts": dict(work_counts),
        "permittype_counts": dict(ptype_counts),
        "top30_descriptions": [{"description": d, "n": c} for d, c in top30],
        "a4_sample_n": sample_n,
        "a4_seed": 20261026,
        "a4_permit_numbers": [r.get("permit_number") for r in sample],
    }
    (RAW / "austin_match_stats.json").write_text(json.dumps(austin_stats, indent=2))
    print("austin matched", n, "excluded", excluded, "no_regex", no_rx)
    print("after 2016-07-01", austin_stats["issued_on_or_after_2016_07_01"])
    print("after 2018-07-01", austin_stats["issued_on_or_after_2018_07_01"])


if __name__ == "__main__":
    main()
