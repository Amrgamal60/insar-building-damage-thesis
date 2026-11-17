"""Build the auditable Alexandria collapse inventory from the Daftar Ahwal workbook (OSF 98pyu).

Every Alexandria row is preserved verbatim with a stable record ID (DA-R<excel row>).
Derived fields (dates, severity, cause group, event grouping, duplicate flags) are added
alongside, never replacing the original values.
"""
import hashlib
import re
import urllib.parse as up
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data/raw/collapse_osf/Figure 2/Recorded Incidents of Building Collapses in Egypt Over Three Years 2014-2015-2016 from Daftar Ahwal.xlsx"
OUT = ROOT / "data/inventory"
OUT.mkdir(parents=True, exist_ok=True)

# Workbook columns (row 2 sub-headers, grouped by the row 1 headers).
COLS = [
    "serial", "event_date_raw", "governorate", "qism", "address", "indexed_name",
    "building_use", "construction", "area_m2", "floors", "apartments", "families",
    "collapse_type", "collapsed_part", "initial_cause", "material_loss",
    "deaths_n", "deaths_info", "injuries_n", "injuries_info",
    "prior_restoration_or_demolition_order", "prior_actions", "later_actions",
    "police_report_no", "notes", "documented_text",
    "official_link_1", "official_link_2", "official_link_3", "official_link_4",
    "official_link_5", "official_link_6", "official_link_7",
    "press_link_1", "press_link_2", "press_link_3",
]
LINK_COLS = [c for c in COLS if "link" in c]
ALEX = "الإسكندرية|الاسكندرية"
ORDINAL_RE = re.compile(r"\s*-\s*عقار\s+(أول|اول|ثان|ثاني|ثالث)\s*$")

# Editable mappings: raw workbook value -> derived class.
SEVERITY = {
    "كامل العقار": "total",
    # structural portion of the building
    "أجزاء منه": "partial_structural", "الجانب الأيمن": "partial_structural",
    "الجانب الغربي": "partial_structural", "الجانب الخلفي": "partial_structural",
    "الخلفية": "partial_structural", "الجهة الخلفية": "partial_structural",
    "النصف الغربي": "partial_structural", "أربعة غرف": "partial_structural",
    "سقف وواجهتين": "partial_structural", "واجهة وسقف": "partial_structural",
    "حائط وسقف": "partial_structural", "سقف وسلم": "partial_structural",
    "سقف وواجهة": "partial_structural", "شرفة وسلم": "partial_structural",
    "سلم": "partial_structural", "السلم": "partial_structural",
    "سقف": "partial_structural", "واجهة": "partial_structural",
    "الواجهة": "partial_structural",
    # single non-load-bearing or local element
    "شرفة": "partial_element", "شرفتين": "partial_element",
    "شرفة وسور": "partial_element", "شرفة وحائط": "partial_element",
    "سقف غرفة": "partial_element", "سقف حجرة": "partial_element",
    "سقف الحمام": "partial_element", "أرضية": "partial_element",
    "حائط": "partial_element",
}
CAUSE_RULES = [  # first match wins
    ("deterioration_weather", r"تقادم.*(الرياح|الأمطار)"),
    ("deterioration", r"تقادم وتهالك"),
    ("adjacent_collapse", r"انهيار بعقار مجاور"),
    ("works_adjacent", r"(مجاور|بجوار العقار|بأسفل العقار)"),
    ("works_on_building", r"(ترميم|هدم|إنشاء|إنشائ|انشاء|انشائ|بناء|تشييد|حفر|مواد البناء)"),
    ("external_accident", r"(غاز|حريق|اصطدام|أفران)"),
    ("technical_violation", r"مخالف"),
    ("water_leak", r"(تسرب|مياة|مياه)"),
]
URL_DATE_RES = [
    re.compile(r"youm7\.com/story/(\d{4})/(\d{1,2})/(\d{1,2})/"),
    re.compile(r"masrawy\.com/.*/details/(\d{4})/(\d{1,2})/(\d{1,2})/"),
    re.compile(r"/(20\d{2})/(\d{1,2})/(\d{1,2})/"),
]
SNIPPET_RE = re.compile(
    r"[^.،\n]{0,60}(?:عقار(?:ا)? رقم\s*«?\d+|شارع\s|\bش\s|حارة\s|عطفة\s|بمنطقة\s|منطقة\s|خلف\s|بجوار\s|أمام\s|مواجه)[^.،\n]{0,80}"
)


def norm_space(s):
    return re.sub(r"\s+", " ", str(s)).strip() if pd.notna(s) else None


def parse_event_date(v):
    """Return (date_iso, start, end, precision)."""
    if hasattr(v, "strftime"):
        d = v.strftime("%Y-%m-%d")
        return d, d, d, "day"
    s = str(v).strip()
    m = re.fullmatch(r"(\d{1,2})-(\d{1,2})/(\d{1,2})/(\d{4})", s)  # e.g. 01-05/06/2014
    if m:
        d1, d2, mo, y = map(int, m.groups())
        return None, f"{y}-{mo:02d}-{d1:02d}", f"{y}-{mo:02d}-{d2:02d}", "range"
    months = {"يناير": 1, "فبراير": 2, "مارس": 3, "أبريل": 4, "ابريل": 4, "مايو": 5, "يونيو": 6,
              "يوليو": 7, "أغسطس": 8, "سبتمبر": 9, "أكتوبر": 10, "نوفمبر": 11, "ديسمبر": 12}
    m = re.fullmatch(r"شهر (\S+) (\d{4})", s)
    if m and m.group(1) in months:
        y, mo = int(m.group(2)), months[m.group(1)]
        end = (pd.Timestamp(y, mo, 1) + pd.offsets.MonthEnd(0)).strftime("%Y-%m-%d")
        return None, f"{y}-{mo:02d}-01", end, "month"
    return None, None, None, "unparsed"


def pub_date_from_links(links):
    dates = []
    for u in links:
        u = up.unquote(u)
        for rx in URL_DATE_RES:
            m = rx.search(u)
            if m:
                y, mo, d = map(int, m.groups())
                try:
                    dates.append(pd.Timestamp(y, mo, d))
                except ValueError:
                    pass
                break
    return min(dates).strftime("%Y-%m-%d") if dates else None


def cause_group(c):
    c = str(c)
    for name, rx in CAUSE_RULES:
        if re.search(rx, c):
            return name
    return "other"


def main():
    raw = pd.read_excel(SRC, header=None)
    raw.columns = COLS
    body = raw.iloc[3:].copy()
    body.insert(0, "excel_row", body.index + 1)  # 1-based row number in the workbook
    is_alex = body.governorate.astype(str).str.contains(ALEX)
    mentions = body.astype(str).apply(lambda c: c.str.contains(ALEX, na=False)).any(axis=1)

    body[mentions & ~is_alex].to_csv(OUT / "excluded_non_alexandria_mentions.csv", index=False, encoding="utf-8-sig")
    a = body[is_alex].copy()
    a.insert(0, "record_id", a.excel_row.map(lambda r: f"DA-R{r:03d}"))
    a.to_csv(OUT / "daftar_ahwal_alexandria_original.csv", index=False, encoding="utf-8-sig")

    rec = a[["record_id", "excel_row", "serial", "event_date_raw", "qism", "address", "indexed_name",
             "building_use", "construction", "area_m2", "floors", "apartments", "families",
             "collapse_type", "collapsed_part", "initial_cause", "deaths_n", "injuries_n",
             "prior_restoration_or_demolition_order"]].copy()
    for c in ["qism", "address", "collapsed_part", "collapse_type", "initial_cause"]:
        rec[c] = rec[c].map(norm_space)
    rec["event_date_raw"] = rec.event_date_raw.map(lambda v: v.strftime("%Y-%m-%d") if hasattr(v, "strftime") else str(v))
    parsed = a.event_date_raw.map(parse_event_date)
    rec["event_date"] = [p[0] for p in parsed]
    rec["event_date_start"] = [p[1] for p in parsed]
    rec["event_date_end"] = [p[2] for p in parsed]
    rec["event_date_precision"] = [p[3] for p in parsed]
    rec["year"] = pd.to_datetime(rec.event_date_start).dt.year

    links = a[LINK_COLS].apply(lambda r: [str(x).strip() for x in r if pd.notna(x)], axis=1)
    rec["n_links"] = links.map(len)
    rec["links"] = links.map(" | ".join)
    rec["source_domains"] = links.map(lambda L: ";".join(sorted({up.urlparse(u).netloc.replace("www.", "") for u in L})))
    rec["pub_date_from_url"] = links.map(pub_date_from_links)
    rec["pub_minus_event_days"] = (pd.to_datetime(rec.pub_date_from_url) - pd.to_datetime(rec.event_date_start)).dt.days

    text = a.documented_text.map(lambda t: norm_space(t) if pd.notna(t) else None)
    rec["text_hash"] = text.map(lambda t: hashlib.md5(t.encode()).hexdigest()[:10] if isinstance(t, str) else None)
    rec["text_shared_by_n_records"] = rec.groupby("text_hash").record_id.transform("count").where(rec.text_hash.notna())
    rec["text_address_snippets"] = [
        None if (not isinstance(t, str) or n > 1) else " || ".join(dict.fromkeys(m.group(0).strip() for m in SNIPPET_RE.finditer(t))) or None
        for t, n in zip(text, rec.text_shared_by_n_records.fillna(1))
    ]
    rec["building_no_in_text"] = text.map(lambda t: ";".join(dict.fromkeys(re.findall(r"(?:العقار|عقار) رقم\s*«?(\d+)", t))) if isinstance(t, str) else None)

    rec["severity_class"] = rec.collapsed_part.map(lambda p: SEVERITY.get(p, "unmapped"))
    rec["severity_flag"] = None
    incons = (rec.collapse_type == "كلي") & (rec.severity_class != "total") | (rec.collapse_type == "جزئي") & (rec.severity_class == "total")
    rec.loc[incons, "severity_flag"] = "collapse_type/collapsed_part disagree"
    rec["cause_group"] = rec.initial_cause.map(cause_group)

    # Event grouping: rows that describe several buildings of one incident ("عقار أول/ثان/ثالث").
    rec["building_ordinal"] = rec.address.fillna("").map(lambda s: (ORDINAL_RE.search(s).group(1) if ORDINAL_RE.search(s) else None))
    rec["address_base"] = rec.address.fillna("").map(lambda s: ORDINAL_RE.sub("", s).strip())
    key = rec.event_date_raw + "|" + rec.qism.fillna("") + "|" + rec.address_base
    rec["event_id"] = key.map({k: f"EV{i:03d}" for i, k in enumerate(dict.fromkeys(key), 1)})
    rec["event_n_buildings"] = rec.groupby("event_id").record_id.transform("count")

    flags = {r: [] for r in rec.record_id}
    for _, g in rec.groupby("event_id"):
        rep = g.building_ordinal.dropna()
        for rid in g[g.building_ordinal.isin(rep[rep.duplicated()])].record_id:
            flags[rid].append("same building ordinal repeated within event")
    ev = rec.drop_duplicates("event_id").copy()
    ev["d"] = pd.to_datetime(ev.event_date_start)
    parts = ev.address_base.map(lambda s: [p.strip() for p in s.split(" - ") if p.strip()])
    ev["streets"] = parts.map(lambda P: {p for p in P if re.match(r"^(ش|شارع|حارة|طريق)\s", p)})
    ev["areas"] = parts.map(lambda P: {p for p in P if not re.match(r"^(ش|شارع|حارة|طريق|تقاطع)\s", p)})
    evs = ev.to_dict("records")

    def add(x, y, why):
        for a_, b_ in ((x, y), (y, x)):
            for rid in rec.loc[rec.event_id == a_["event_id"], "record_id"]:
                flags[rid].append(f"{why} [{b_['event_id']}]")

    for i, x in enumerate(evs):
        for y in evs[i + 1:]:
            if x["qism"] != y["qism"] or x["qism"] in (None, "غير محدد") or pd.isna(x["d"]) or pd.isna(y["d"]):
                continue
            dd = abs((x["d"] - y["d"]).days)
            has_inj = str(x["injuries_n"]) not in ("لا يوجد", "nan")
            if dd <= 3 and (x["address_base"] == y["address_base"] or x["streets"] & y["streets"]):
                add(x, y, f"STRONG same address/street, {dd} d apart")
            elif dd == 0 and has_inj and str(x["injuries_n"]) == str(y["injuries_n"]):
                add(x, y, "MEDIUM same date, identical injury count, different address")
            elif dd == 0 and isinstance(x["text_hash"], str) and x["text_hash"] == y["text_hash"]:
                add(x, y, "WEAK same date and source text, different address (may be separate buildings)")
            elif dd <= 3 and x["areas"] & y["areas"]:
                add(x, y, f"WEAK same neighbourhood, {dd} d apart, different street")
            if x["areas"] & y["areas"] or x["address_base"] == y["address_base"]:
                for s, t in ((x, y), (y, x)):
                    if isinstance(s["pub_date_from_url"], str) and pd.notna(t["d"]) and pd.Timestamp(s["pub_date_from_url"]) == t["d"] and dd > 3:
                        add(s, t, "MEDIUM source article dated on another event in same area (date may be wrong)")
    rec["possible_duplicate"] = rec.record_id.map(lambda r: "; ".join(dict.fromkeys(flags[r])) or None)
    rec["source_is_retrospective"] = rec.pub_minus_event_days > 7

    rec.to_csv(OUT / "inventory_records.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(sorted(SEVERITY.items(), key=lambda kv: kv[1]), columns=["collapsed_part_raw", "severity_class"]).to_csv(
        OUT / "severity_mapping.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(CAUSE_RULES, columns=["cause_group", "regex_on_initial_cause"]).to_csv(
        OUT / "cause_mapping.csv", index=False, encoding="utf-8-sig")

    print("workbook data rows:", len(body), "| Alexandria rows:", len(a), "| excluded mentions:", int((mentions & ~is_alex).sum()))
    print("date precision:", rec.event_date_precision.value_counts().to_dict())
    print("rows by year:", rec.year.value_counts().sort_index().to_dict())
    print("events:", rec.event_id.nunique(), "| multi-building events:", (rec.drop_duplicates("event_id").event_n_buildings > 1).sum())
    print("severity:", rec.severity_class.value_counts().to_dict(), "| flags:", rec.severity_flag.notna().sum())
    print("cause:", rec.cause_group.value_counts().to_dict())
    print("possible duplicates (records):", rec.possible_duplicate.notna().sum())
    print("pub date found:", rec.pub_date_from_url.notna().sum(), "| lag days describe:", rec.pub_minus_event_days.describe().round(1).to_dict())


if __name__ == "__main__":
    main()
