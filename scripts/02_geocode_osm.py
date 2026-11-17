"""Geocode inventory addresses against a local OSM extract, constrained to the reported police district (qism).

Coordinates are only produced from matched OSM features; nothing is typed in by hand.
Every result carries its evidence (matched names, OSM ids, number of candidate clusters,
fuzzy suggestions) and a location-confidence category:

  A_intersection     two named streets matched and meeting (<= 25 m) in the district / named neighbourhood
  A_street           one named street matched exactly, single spatial cluster, in the district or named neighbourhood
  B_street_review    one cluster, but fuzzy name match or only outside the district polygon  -> coordinates, flagged
  B_street_ambiguous exact name, several separate streets and nothing to choose between them  -> no coordinates
  B_street_overture  street not in OSM, located from Overture places whose address names it   -> coordinates, flagged
  C_landmark         a named landmark (mosque, school, company, palace ...) matched
  C_neighbourhood    only a neighbourhood / sub-district name matched (from the address or the article text)
  D_district_only    only the police district is known                                        -> no coordinates
  E_unlocated        nothing usable                                                           -> no coordinates

`matched_extent_m` is the largest distance from the assigned point to the matched OSM geometry.
It is a property of the matched feature (how far along the street / across the polygon the
building could be *if the match is correct*), not a geocoder accuracy score.

Overture places (free-form business addresses) are a second gazetteer, used only for records OSM could
not place at street level, so they never change an OSM result. They can supply a street missing from OSM
(>= 2 places naming it in one cluster, or 1 place whose address also names the record's neighbourhood),
a landmark, or a neighbourhood missing from OSM (the main cluster of >= 3 places whose address names it).
A neighbourhood found this way may pick one of several same-named OSM streets; that result is flagged B.
"""
import json
import re
from pathlib import Path

import geopandas as gpd
import pandas as pd
from rapidfuzz import fuzz
from shapely.geometry import MultiPoint, Point
from shapely.ops import linemerge, nearest_points, unary_union

ROOT = Path(__file__).resolve().parents[1]
INV = ROOT / "data/inventory"
CRS = 32636  # UTM 36N, same as the OSF shapefiles
QISM_TO_ADM2 = {
    "العطارين": "Al Attarin", "مينا البصل": "Mina Al-Basal", "محرم بك": "Muharam Bik",
    "سيدي جابر": "Sidi Gabir", "الدخيلة": "Al Dikhila", "أول المنتزة": "Muntazah",
    "ثان المنتزة": "Muntazah", "أول الرمل": "Al Raml", "ثان الرمل": "Kesm than Al Raml",
    "الجمرك": "Al Gumruk", "اللبان": "A L Labban", "كرموز": "Karmuz", "باب شرقي": "Bab Sharqi",
    "المنشية": "Al Manshiyya", "أول العامرية": "Al Amreia",
}
DISTRICT_BUFFER_M = 300
NEAR_AREA_M = 300
STREET_TYPES = r"(?:شارع|ش|حاره|حارة|عطفه|عطفة|طريق|ميدان|زقاق|درب|ممر)"
LANDMARK_WORDS = r"(مسجد|مدرسه|مدرسة|شركه|شركة|مبنى|مبني|قصر|كافيتيريا|فيللا|فيلا|حمامات|المركز التجاري|نادي|مستشفى|عزبه|عزبة)"
RELATION_PREFIX = r"^(خلف|مواجه|بجوار|امام|منطقه|منطقة)\s+(ل(?=\S{3,}))?"
DIRECTION_SUFFIX = r"\s+(شرق|غرب|شرقي|غربي|بحري|قبلي|البحريه|القبليه|الجديده)$"
PROXY_PREFIX = r"^(محطه ترام|محطه|مزلقان ترام|مزلقان|ميدان)\s+"
HONORIFICS = {"الشيخ", "شيخ", "الدكتور", "دكتور", "سيدي", "الامام", "الاستاذ", "المهندس", "اللواء", "الشهيد", "باشا", "بك"}
TEXT_STREET_RE = re.compile(r"(?:بشارع|شارع|بحارة|حارة|بحاره|حاره)\s+((?:[^\s،.,«»()–\-\d]+\s?){1,4})")
MAX_OUTSIDE_DISTRICT_M = 1500
TEXT_AREA_RE = re.compile(r"(?:بمنطقة|بمنطقه|منطقة|منطقه|بحي|حي)\s+([^\s،.,«»()]+)(?:\s+([^\s،.,«»()]+))?")
OVERTURE = ROOT / "data/raw/overture_places/overture_places_2026-09-23.0_alexandria.parquet"
OV_GAP_M = 300       # places along one street are usually closer than this
OV_AREA_MIN = 3      # places needed to accept a neighbourhood from Overture addresses
DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
OV_STOP = {"امام", "بجوار", "بجانب", "خلف", "متفرع", "من", "مع", "اول", "اخر", "قسم", "محافظه", "الاسكندريه",
           "اسكندريه", "برج", "عماره", "مصر", "علي", "ناصيه", "تقاطع", "داخل", "الدور", "شقه", "رقم", "بعد", "قبل",
           "عند", "اسفل", "اعلي", "فوق"}


def norm(s):
    if not isinstance(s, str):
        return ""
    s = re.sub(r"[ً-ْٰـ]", "", s)
    s = s.translate(str.maketrans("أإآٱىةؤئ", "اااايهوي"))
    s = re.sub(r"[^\w\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def street_key(s):
    """Canonical key for a street name: drop the type word, 'ال', spaces; unify ابن/بن."""
    s = norm(s)
    s = re.sub(rf"^{STREET_TYPES}\s+", "", s)
    words = ["ابن" if w == "بن" else w for w in s.split()]
    words = [w[2:] if w.startswith("ال") and len(w) > 3 else w for w in words]
    return "".join(words)


def type_word(s):
    m = re.match(rf"^({STREET_TYPES})\s+", norm(s))
    if not m:
        return None
    return {"ش": "شارع", "حاره": "حاره", "حارة": "حاره", "عطفة": "عطفه"}.get(m.group(1), m.group(1))


def honorific_key(s):
    s = norm(s)
    s = re.sub(rf"^{STREET_TYPES}\s+", "", s)
    words = [w for w in s.split() if w not in HONORIFICS and not (w.startswith("ال") and w[2:] in HONORIFICS)]
    return street_key(" ".join(words))


def tag(other_tags, key):
    m = re.search(rf'"{re.escape(key)}"=>"([^"]*)"', other_tags if isinstance(other_tags, str) else "")
    return m.group(1) if m else None


def load_osm():
    hw = gpd.read_parquet(ROOT / "data/interim/osm_alex_highways.parquet").to_crs(CRS)
    rows = []
    for r in hw.itertuples():
        for nm in {r.name, tag(r.other_tags, "name:ar"), tag(r.other_tags, "alt_name"), tag(r.other_tags, "old_name")}:
            if isinstance(nm, str) and nm:
                rows.append((r.osm_id, nm, street_key(nm), honorific_key(nm), norm(nm), r.highway, r.geometry))
    streets = gpd.GeoDataFrame(rows, columns=["osm_id", "osm_name", "key", "hkey", "nname", "highway", "geometry"], crs=CRS)

    pts = gpd.read_parquet(ROOT / "data/interim/osm_alex_points.parquet").to_crs(CRS)
    pts["osm_ref"] = "node/" + pts.osm_id.astype(str)
    polys = gpd.read_parquet(ROOT / "data/interim/osm_alex_multipolygons.parquet").to_crs(CRS)
    polys["osm_ref"] = polys.apply(lambda r: f"way/{int(r.osm_way_id)}" if pd.notna(r.osm_way_id) else f"relation/{r.osm_id}", axis=1)
    feats = pd.concat([pts[["osm_ref", "name", "place", "other_tags", "geometry"]],
                       polys[["osm_ref", "name", "place", "other_tags", "geometry"]]], ignore_index=True)
    feats = gpd.GeoDataFrame(feats, crs=CRS)
    feats["nname"] = feats.name.map(norm)
    feats = feats[feats.nname != ""]
    return streets, feats


def load_districts():
    g = gpd.read_file(ROOT / "data/raw/admin_geoboundaries/geoBoundaries-EGY-ADM2.geojson").to_crs(CRS)
    return {q: g.loc[g.shapeName == n, "geometry"].union_all() for q, n in QISM_TO_ADM2.items()}


def ov_street_phrases(addr):
    """Complete street names in a free-form Overture address: the words after a street-type word, up to a
    delimiter, a house number or a relation word (امام, بجوار ...)."""
    if not isinstance(addr, str):
        return []
    a = re.sub(r"(?<=\d)(?=[^\d\s,،\-])|(?<=[^\d\s,،\-])(?=\d)", " ", addr.translate(DIGITS))
    out = []
    for part in re.split(r"[,،\-–/|()]", a):
        words = norm(part).split()
        for i, w in enumerate(words):
            if not re.fullmatch(STREET_TYPES, w):
                continue
            name = []
            for j, x in enumerate(words[i + 1:i + 6]):
                if x in OV_STOP or re.fullmatch(STREET_TYPES, x) or (j and re.search(r"\d", x)):
                    break
                name.append(x)
            if name:
                out.append(" ".join(name))
    return out


def load_overture():
    o = pd.read_parquet(OVERTURE)
    o = gpd.GeoDataFrame(o, geometry=gpd.points_from_xy(o.lon, o.lat), crs=4326).to_crs(CRS)
    o["phrases"] = o.address.map(ov_street_phrases)
    o["naddr"] = " " + o.address.map(lambda s: norm(s.translate(DIGITS)) if isinstance(s, str) else "") + " "
    o["nname"] = o.name.map(norm)
    return o


def clusters(geoms, gap=60):
    """Group candidate street segments into spatially connected clusters."""
    blobs = unary_union([g.buffer(gap / 2) for g in geoms])
    blobs = list(getattr(blobs, "geoms", [blobs]))
    return [unary_union([g for g in geoms if g.intersects(b)]) for b in blobs]


def rep_point(geom):
    if geom.geom_type == "Point":
        return geom, 0.0
    merged = linemerge(geom) if geom.geom_type == "MultiLineString" else geom
    if merged.geom_type == "LineString":
        p = merged.interpolate(0.5, normalized=True)
    elif merged.geom_type in ("Polygon", "MultiPolygon"):
        p = merged.representative_point()
    else:
        p = nearest_points(merged.centroid, merged)[1]
    return p, p.hausdorff_distance(geom)


def parse_address(addr):
    parts = [p.strip() for p in re.split(r"\s+-\s+", addr if isinstance(addr, str) else "") if p.strip()]
    parts = [p for p in parts if not re.fullmatch(r"عقار\s+(أول|اول|ثان|ثاني|ثالث)", p)]
    streets, inters, landmarks, areas = [], [], [], []
    for p in parts:
        n = norm(p)
        m = re.match(rf"^(?:تقاطع\s+)?{STREET_TYPES}\s+(.+?)\s+(?:مع|من)\s+{STREET_TYPES}\s+(.+)$", n)
        if m:
            inters.append((m.group(1), m.group(2)))
        elif re.match(rf"^{STREET_TYPES}\s+", n):
            streets.append(n)
        elif re.search(LANDMARK_WORDS, n):
            landmarks.append(re.sub(RELATION_PREFIX, "", n))
        elif n and n != "غير محدد":
            areas.append(re.sub(RELATION_PREFIX, "", n))
    if len(streets) >= 2 and not inters:  # "ش X - ش Y" is usually a corner
        inters.append((streets[0], streets[1]))
    return streets, inters, landmarks, areas


def diameter(g):
    return g.convex_hull.hausdorff_distance(g.centroid) * 2 if not g.is_empty else 0


def area_tokens(nname):
    """Sub-district polygons are sometimes named 'X و Y' or 'X, Y'."""
    return {t.strip() for t in re.split(r"\s+و\s+|,|،", nname) if t.strip()}


def find_area(area, feats, district, qism, from_text=False):
    """Neighbourhood polygon(s) named `area`; else a place point; else tram-station/square proxy.

    Returns (geometry, kind, osm_refs, extent_known)."""
    base = norm(area)
    nq = norm(qism or "")
    if not base or base == nq or (nq and base in nq) or (from_text and len(base) < 4):
        return None, None, [], False
    local = feats if district is None else feats[feats.intersects(district.buffer(DISTRICT_BUFFER_M))]
    stripped = local.nname.str.replace(DIRECTION_SUFFIX, "", regex=True)
    tok = local.place.notna() & local.name.map(lambda n: base in {re.sub(DIRECTION_SUFFIX, "", norm(t)) for t in area_tokens(n)})
    named = local[(local.nname == base) | (stripped == base) | (local.nname == "عزبه " + base) | tok]
    polys = named[named.geometry.geom_type.isin(["Polygon", "MultiPolygon"]) & named.place.notna()]
    if len(polys):
        return polys.union_all(), "neighbourhood polygon", polys.osm_ref.tolist(), True
    placepts = named[named.place.notna()]
    if len(placepts) and diameter(placepts.union_all()) < 1500:
        return placepts.union_all(), "place point(s)", placepts.osm_ref.tolist(), False
    proxy = local[local.nname.str.replace(PROXY_PREFIX, "", regex=True).str.replace(r"\s*(الكبري|الصغري|\(.*\))$", "", regex=True) == base]
    proxy = proxy[proxy.nname.str.match(PROXY_PREFIX)]
    if len(proxy) and diameter(proxy.union_all()) < 1500:
        return proxy.union_all(), "tram-station/square proxy", proxy.osm_ref.tolist(), False
    other = named[named.geometry.geom_type.isin(["Polygon", "MultiPolygon"])]
    if len(other) == 1:
        return other.geometry.iloc[0], "same-named feature polygon (e.g. historic site)", other.osm_ref.tolist(), True
    return None, None, [], False


def fuzzy_suggestions(name, streets, district, n=3):
    k = street_key(name)
    local = streets if district is None else streets[streets.intersects(district.buffer(DISTRICT_BUFFER_M))]
    sc = local.assign(score=local.key.map(lambda x: fuzz.ratio(x, k))).sort_values("score", ascending=False)
    sc = sc.drop_duplicates("key").head(n)
    return [{"osm_name": r.osm_name, "score": int(r.score), "osm_id": r.osm_id} for r in sc.itertuples() if r.score >= 70]


def restrict(cands, district, area_geom):
    """Keep candidates near the named neighbourhood, else inside the district. Returns (cands, where, extra)."""
    if area_geom is not None:
        near = cands[cands.distance(area_geom) <= NEAR_AREA_M]
        if len(near):
            return near, "near_neighbourhood", {}
    if district is None:
        return cands, "no_district", {}
    inside = cands[cands.intersects(district.buffer(DISTRICT_BUFFER_M))]
    if len(inside):
        return inside, "in_district", {}
    return cands, "outside_district", {"distance_to_district_m": round(cands.distance(district).min())}


def match_street(name, streets, district, area_geom, allow_fuzzy=True):
    """Return (candidates, how, extra). how = '<match>_<where>' e.g. exact_in_district, honorific_near_neighbourhood."""
    tries = [("exact", streets[streets.key == street_key(name)])]
    hk = honorific_key(name)
    if hk:
        tries.append(("honorific", streets[streets.hkey == hk]))
    for kind, cands in tries:
        if not len(cands):
            continue
        c, where, extra = restrict(cands, district, area_geom)
        if where == "outside_district":
            extra["rejected_outside_candidates"] = sorted(set(c.osm_name))[:3]
            if extra["distance_to_district_m"] > MAX_OUTSIDE_DISTRICT_M or len(clusters(list(c.geometry))) > 1:
                continue  # a same-named street elsewhere in the city is not evidence
        return c, f"{kind}_{where}", extra
    if allow_fuzzy and district is not None:
        local = streets[streets.intersects(district.buffer(DISTRICT_BUFFER_M))]
        sc = local.key.map(lambda x: fuzz.ratio(x, street_key(name)))
        if len(sc) and sc.max() >= 90:
            return local[sc == sc.max()], f"fuzzy{int(sc.max())}_in_district", {}
    return streets.iloc[0:0], "none", {}


def text_areas(text):
    if not isinstance(text, str):
        return []
    out = []
    for m in TEXT_AREA_RE.finditer(text):
        w1, w2 = m.group(1), m.group(2)
        if w2:
            out.append(f"{w1} {w2}")
        out.append(w1)
    return list(dict.fromkeys(out))


def text_streets(text):
    """Street names mentioned in the article text, longest phrasing first."""
    if not isinstance(text, str):
        return []
    out = []
    for m in TEXT_STREET_RE.finditer(text):
        words = m.group(1).split()
        for n in range(min(4, len(words)), 0, -1):
            out.append("ش " + re.sub(r"[\"'“”]", "", " ".join(words[:n])).strip())
    return list(dict.fromkeys(out))


def resolve_clusters(c, name):
    """Several separate streets with the same name: try the record's type word (شارع vs حارة)."""
    cl = clusters(list(c.geometry))
    if len(cl) > 1:
        tw = type_word(name)
        if tw:
            same = c[c.osm_name.map(type_word) == tw]
            if len(same) and len(clusters(list(same.geometry))) == 1:
                return clusters(list(same.geometry)), "resolved by street type word"
    return cl, None


def ov_match(phrases, s, areas):
    """'exact' if an address names the street (optionally followed by the record's neighbourhood);
    'longer' if it only names a longer street that starts with the same words."""
    k, kind = street_key(s), None
    for p in phrases:
        if street_key("ش " + p) == k:
            return "exact"
        w = p.split()
        for n in range(1, len(w)):
            if street_key("ش " + " ".join(w[:n])) == k:
                if " ".join(w[n:]) in areas:
                    return "exact"
                kind = "longer"
    return kind


def overture_street(s, ov, district, area_geom, areas):
    """A street missing from OSM, located from Overture places whose address names it.
    Returns (point, geometry, evidence); the point is None when the evidence is not enough."""
    local = ov[ov.intersects(district.buffer(DISTRICT_BUFFER_M))]
    kind = local.phrases.map(lambda ps: ov_match(ps, s, areas))
    ex, longer = local[kind == "exact"], local[kind == "longer"]
    info = {"street": s, "n_places": len(ex)}
    if len(longer):
        k = street_key(s)
        info["n_places_longer_name"] = len(longer)
        info["longer_names"] = sorted({p for ps in longer.phrases for p in ps if street_key("ش " + p).startswith(k)})[:3]
    if area_geom is not None and (ex.distance(area_geom) <= NEAR_AREA_M).any():
        ex = ex[ex.distance(area_geom) <= NEAR_AREA_M]
        info["where"] = "near_neighbourhood"
    if not len(ex):
        return None, None, info
    info["places"] = [{"id": r.id, "name": r.name, "address": r.address} for r in ex.head(5).itertuples()]
    cl = clusters(list(ex.geometry), gap=OV_GAP_M)
    info["n_clusters"] = len(cl)
    names_area = len(ex) == 1 and any(f" {a} " in ex.naddr.iloc[0] for a in areas)
    if len(cl) == 1 and (len(ex) >= 2 or names_area):
        pts = list(ex.geometry)
        p = min(pts, key=lambda q: sum(q.distance(x) for x in pts))  # medoid: an actual place location
        info["rule"] = "places in one cluster" if len(ex) >= 2 else "1 place, its address also names the neighbourhood"
        info["spread_m"] = round(max(p.distance(x) for x in pts))
        return p, (MultiPoint(pts) if len(pts) > 1 else p), info
    info["rule"] = "not enough evidence"
    return None, None, info


def overture_area(a, ov, district, qism):
    """A neighbourhood missing from OSM: the main cluster of Overture places whose address names it."""
    base, nq = norm(a), norm(qism or "")
    if district is None or len(base) < 4 or base == nq or base in nq:
        return None, None
    local = ov[ov.intersects(district.buffer(DISTRICT_BUFFER_M))]
    hit = local[local.naddr.str.contains(f" {base} ", regex=False)]
    info = {"name": a, "source": "address", "kind": "Overture address cluster", "n_places": len(hit)}
    if len(hit) < OV_AREA_MIN:
        return None, info
    cl = clusters(list(hit.geometry), gap=OV_GAP_M)
    main = max(cl, key=lambda c: len(getattr(c, "geoms", [c])))
    n = len(getattr(main, "geoms", [main]))
    info["n_places_main_cluster"] = n
    if n < OV_AREA_MIN or n < 2 / 3 * len(hit):
        return None, info
    info["overture_ids"] = hit[hit.intersects(main.buffer(1))].id.tolist()[:6]
    return main.convex_hull, info


def overture_landmark(lm, ov, district, area_geom):
    """A landmark missing from OSM, matched by Overture place name in the district (and near the neighbourhood)."""
    k = norm(lm)
    cand = ov[(ov.nname == k) | ov.nname.str.startswith(k + " ")]
    cand = cand[cand.intersects(district.buffer(DISTRICT_BUFFER_M))]
    info = {"name": lm, "n_places_in_district": len(cand), "names": cand.name.tolist()[:3]}
    if area_geom is not None and len(cand):
        info["distance_to_neighbourhood_m"] = sorted(round(x) for x in cand.distance(area_geom))[:3]
        cand = cand[cand.distance(area_geom) <= NEAR_AREA_M]
    if len(cand) and diameter(cand.union_all()) < 800:
        return cand, info
    return None, info


def overture_fallback(res, rec, text, streets, feats, districts, ov):
    """Second pass with Overture places, only for records OSM could not place at street level."""
    cat, p, ext, ev, g, area_geom = res
    qism = rec.qism if isinstance(rec.qism, str) and rec.qism != "غير محدد" else None
    district = districts.get(qism)
    if cat in ("A_intersection", "A_street", "B_street_review") or district is None:
        return res
    st, inters, lms, areas = parse_address(rec.address)
    ov_area = None
    if "area_match" not in ev:
        for a in areas:
            ga, info = overture_area(a, ov, district, qism)
            if info and info["n_places"]:
                ev.setdefault("overture_area_attempts", []).append(info)
            if ga is not None:
                ov_area = (ga, info)
                break

    # 1. several same-named OSM streets: a neighbourhood found in Overture addresses may pick one
    if cat == "B_street_ambiguous" and ov_area is not None:
        r2 = geocode(rec, text, streets, feats, districts, area_override=ov_area)
        if r2[0] in ("A_intersection", "A_street", "B_street_review"):
            r2[3]["overture_resolved"] = "OSM alone: B_street_ambiguous; cluster chosen by a neighbourhood found in Overture addresses"
            return ("B_street_review",) + tuple(r2[1:])

    # 2. street missing from OSM
    near = area_geom if area_geom is not None else (ov_area[0] if ov_area else None)
    for u in ev.get("unmatched_streets", []):
        pt, geom, info = overture_street(u["name"], ov, district, near, areas)
        if pt is not None:
            ev["overture_street"] = info
            return "B_street_overture", pt, None, ev, geom, area_geom
        if info["n_places"] or info.get("n_places_longer_name"):
            ev.setdefault("overture_street_candidates", []).append(info)

    # 3. landmark missing from OSM
    if cat != "C_landmark":
        for lm in lms:
            cand, info = overture_landmark(lm, ov, district, area_geom)
            if info["n_places_in_district"]:
                ev.setdefault("overture_landmark_candidates", []).append(info)
            if cand is not None:
                gl = cand.union_all()
                ev["landmark_match"] = {"name": lm, "source": "overture", "names": cand.name.tolist()[:5],
                                        "overture_ids": cand.id.tolist()[:5]}
                return "C_landmark", rep_point(gl)[0], None, ev, gl, area_geom

    # 4. neighbourhood missing from OSM
    if cat in ("D_district_only", "E_unlocated") and ov_area is not None:
        ev["area_match"] = ov_area[1]
        return "C_neighbourhood", rep_point(ov_area[0])[0], None, ev, ov_area[0], ov_area[0]
    return cat, p, ext, ev, g, area_geom


def geocode(rec, text, streets, feats, districts, area_override=None):
    qism = rec.qism if isinstance(rec.qism, str) and rec.qism != "غير محدد" else None
    district = districts.get(qism)
    st, inters, lms, areas = parse_address(rec.address)
    ev = {"parsed": {"streets": st, "intersections": inters, "landmarks": lms, "areas": areas},
          "district_polygon": QISM_TO_ADM2.get(qism)}
    area_geom, area_ext_known = None, False
    if area_override is not None:
        area_geom, ev["area_match"] = area_override
    for src, names in (() if area_override is not None else
                       (("address", areas), ("article_text", text_areas(text) if qism else []))):
        for a in names:
            g, kind, refs, known = find_area(a, feats, district, qism, from_text=(src == "article_text"))
            if g is not None:
                area_geom, area_ext_known = g, known
                ev["area_match"] = {"name": a, "source": src, "kind": kind, "osm": refs[:6]}
                break
            if src == "address" and district is not None:
                g2, kind2, refs2, _ = find_area(a, feats, None, qism)
                if g2 is not None:
                    ev.setdefault("area_outside_reported_district", []).append(
                        {"name": a, "kind": kind2, "distance_to_district_m": round(g2.distance(district)), "osm": refs2[:3]})
        if area_geom is not None:
            break

    # Streets mentioned in the article text: used to confirm / correct the address spelling, and to flag conflicts.
    tstreets = []
    for t in text_streets(text):
        c, how, _ = match_street(t, streets, district, area_geom, allow_fuzzy=False)
        if len(c) and how.startswith("exact") and "outside" not in how:
            if not any(street_key(t).startswith(street_key(x)) or street_key(x).startswith(street_key(t)) for x in tstreets):
                tstreets.append(t)
    if tstreets:
        ev["article_text_streets"] = tstreets

    def consistent(a, b):
        ka, kb = street_key(a), street_key(b)
        return fuzz.ratio(ka, kb) >= 80 or honorific_key(a) == honorific_key(b) or ka.startswith(kb) or kb.startswith(ka)

    # 1. intersections (fall back to the individual streets if they do not meet)
    for x, y in inters:
        cx, hx, _ = match_street(x, streets, district, area_geom, allow_fuzzy=False)
        cy, hy, _ = match_street(y, streets, district, area_geom, allow_fuzzy=False)
        info = {"a": x, "b": y, "how_a": hx, "how_b": hy}
        if len(cx) and len(cy) and hx.startswith("exact") and hy.startswith("exact") and "outside" not in hx + hy:
            pa, pb = nearest_points(cx.geometry.union_all(), cy.geometry.union_all())
            info["gap_m"] = round(pa.distance(pb), 1)
            if pa.distance(pb) <= 25:
                ev["intersection"] = info
                p = Point((pa.x + pb.x) / 2, (pa.y + pb.y) / 2)
                return "A_intersection", p, info["gap_m"], ev, p, area_geom
        ev["intersection"] = info
        st = st + [s for s in (f"ش {x}", f"ش {y}") if s not in st]

    # 2. single street: exact/honorific from the address, then the article's spelling of the same street, then fuzzy
    attempts = []
    for s in st:
        attempts.append((s, "address", False))
    for s in st:
        for t in tstreets:
            if consistent(s, t):
                attempts.append((t, "article_text_spelling", False))
    for s in st:
        attempts.append((s, "address", True))
    for s, src, fz in attempts:
        c, how, extra = match_street(s, streets, district, area_geom, allow_fuzzy=fz)
        if not len(c) or (fz and not how.startswith("fuzzy")):
            continue
        cl, note = resolve_clusters(c, s)
        others = [t for t in tstreets if not any(consistent(t, x) for x in st)]
        conflicts = others if tstreets and len(others) == len(tstreets) else []
        ev["street_match"] = {"name": s, "source": src, "how": how, "n_clusters": len(cl), "note": note, **extra,
                              "osm_names": sorted(set(c.osm_name))[:5], "osm_ids": sorted(set(c.osm_id))[:15]}
        if others:
            ev["street_match"]["article_also_mentions"] = others
        if conflicts:
            ev["street_match"]["conflict_article_never_mentions_address_street"] = True
        if len(cl) > 1:
            ev["street_match"]["cluster_centroids_utm"] = [[round(g.centroid.x), round(g.centroid.y)] for g in cl][:10]
            return "B_street_ambiguous", None, None, ev, None, area_geom
        p, ext = rep_point(cl[0])
        good = how in ("exact_near_neighbourhood", "exact_in_district") and not conflicts
        return ("A_street" if good else "B_street_review"), p, round(ext), ev, cl[0], area_geom
    for s in st:
        ev.setdefault("unmatched_streets", []).append({"name": s, "suggestions": fuzzy_suggestions(s, streets, district)})

    # 3. landmark (name equal to / starting with the landmark phrase)
    for lm in lms:
        k = norm(lm)
        cand = feats[(feats.nname == k) | feats.nname.str.startswith(k + " ")]
        if district is not None:
            cand = cand[cand.intersects(district.buffer(DISTRICT_BUFFER_M))]
        if len(cand) and diameter(cand.union_all()) < 800:
            g = cand.union_all()
            p, ext = rep_point(g)
            ev["landmark_match"] = {"name": lm, "osm_names": cand.name.tolist()[:5], "osm": cand.osm_ref.tolist()[:5]}
            return "C_landmark", p, round(ext), ev, g, area_geom
        ev.setdefault("unmatched_landmarks", []).append({"name": lm, "n_candidates": int(len(cand))})

    # 4. neighbourhood
    if area_geom is not None:
        p, ext = rep_point(area_geom)
        return "C_neighbourhood", p, (round(ext) if area_ext_known else None), ev, area_geom, area_geom

    if district is not None:
        return "D_district_only", None, None, ev, None, area_geom
    return "E_unlocated", None, None, ev, None, area_geom


def main():
    rec = pd.read_csv(INV / "inventory_records.csv")
    orig = pd.read_csv(INV / "daftar_ahwal_alexandria_original.csv", usecols=["record_id", "documented_text"])
    rec = rec.merge(orig, on="record_id", how="left")
    rec.loc[rec.text_shared_by_n_records.fillna(1) > 1, "documented_text"] = None  # summary texts cover other events
    streets, feats = load_osm()
    districts = load_districts()
    ov = load_overture()
    out, geoms, osm_only = [], [], []
    for r in rec.itertuples():
        res = geocode(r, r.documented_text, streets, feats, districts)
        osm_only.append(res[0])
        cat, p, ext, ev, g, _ = overture_fallback(res, r, r.documented_text, streets, feats, districts, ov)
        out.append({"record_id": r.record_id, "loc_category": cat,
                    "x_utm36": round(p.x, 1) if p is not None else None,
                    "y_utm36": round(p.y, 1) if p is not None else None,
                    "matched_extent_m": ext, "evidence": json.dumps(ev, ensure_ascii=False, default=str)})
        geoms.append(g)
    g = pd.DataFrame(out)
    pts = gpd.GeoSeries.from_xy(g.x_utm36, g.y_utm36, crs=CRS).to_crs(4326)
    g["lon"] = pts.x.round(6).where(g.x_utm36.notna())
    g["lat"] = pts.y.round(6).where(g.x_utm36.notna())
    g.to_csv(INV / "geocode_auto.csv", index=False, encoding="utf-8-sig")
    gpd.GeoDataFrame(g[["record_id", "loc_category"]], geometry=geoms, crs=CRS).dropna(subset=["geometry"]).to_file(
        INV / "geocode_auto_matched_features.gpkg", driver="GPKG")
    print(g.loc_category.value_counts().to_dict())
    changed = g.loc_category != pd.Series(osm_only)
    print("changed by Overture:", pd.crosstab(pd.Series(osm_only)[changed].rename("OSM only"), g.loc_category[changed]).to_string())
    print(g.groupby("loc_category").matched_extent_m.describe()[["count", "50%", "max"]].round(0).to_string())


if __name__ == "__main__":
    main()
