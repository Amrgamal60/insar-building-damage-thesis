"""HAZARD_TX (HAZARD_TX_PLAN.md §5): foundation episodes, events, total demolitions and recent-construction exits per
city, from the permit files and the step-0 link tables. No map value is read: the population is read by id only.

§12 order: this runs AFTER freezing (step 6). Before freezing it is checked with --selftest on synthetic permit tables,
one case per rule, each with a known expected output (no real permit file is opened by the self-test).

Rules (plan §5; authors' choices fixed 2026-11-22):
- Permits issued after END (2025-12-31) are not used. Permits link to a house through the step-0 link table
  (target "population house"); others are ignored.
- Matched foundation permits:
  Dallas: "Residential Foundation Repair" (any date); any "Building (BU) Single Family ..." permit whose work
    description contains FOUNDATION (any date); look-back only: "Residential Alteration Addition Permit" whose work
    description contains FOUNDATION, issued before START. Secondary 17 (--broad): the last kind at any date.
    "Phase - ..." permits are not used.
  San Antonio: "Foundation Repair Permit" (any date).
- First episode = the house's first matched permit (permits within 365 days of an episode's first permit belong to that
  episode; the event is the first episode, so the chained and anchored readings give the same date; both episode
  counts are reported).
- Status of the first episode: before START -> "first episode before the study period" (not at risk);
  in [START, END] -> "event", unless a construction permit on the same house is dated in [t - 3 years, t)
  -> "excluded: construction permit in the 3 years before" (follow-up ends without an event).
- Construction permits: Dallas BU Single Family New Construction / Addition / Reconstruction, "Residential New
  Construction Permit", "Residential Alteration Addition Permit" whose work description contains ADDITION, and the
  total demolitions; San Antonio "Res New Building Permit", "Home Addition Permit", "Building Move Permit" and the total
  demolitions.
- Total demolition: Dallas "Demolition Permit SFD/Duplex" or "Residential Demolition Permit"; San Antonio "Demolition
  Permit"; not total if the description (Dallas work description, San Antonio project name) contains the word PARTIAL.
  The house's first total demolition at any date (up to END) is its demolition date.

Outputs (private, --out DIR/<city>[_broad]/): first_episodes.parquet (hid, t_first, status, n_matched, ...),
events.parquet (hid, t_first), demolition.parquet (hid, t_demolition); San Antonio also
construction_2022_2025.parquet (houses with a construction permit issued in the follow-up, secondary 15).
Counts only (no description, no address) go to --out-json.

Usage: python -I build_events.py --selftest
       python -I build_events.py --city dallas|sanantonio [--broad] --out DIR --out-json F
"""
import argparse
import hashlib
import os
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
START, END = pd.Timestamp("2022-01-01"), pd.Timestamp("2025-12-31")
PRIV = Path(os.environ.get("HT_PRIVATE", "/mnt/data/Master-projects/Alex_private"))  # server: HT_PRIVATE, same layout
PARTIAL = re.compile(r"\bPARTIAL\b")
FILES = {
    "dallas": dict(permits=[PRIV / "dallas_permits_20261119/e7gq-4sah.csv"],
                   permits_sha256=["e970c38a387e4b121ac417d685c7b4103de323eb9d45573127d65b4775ba3ab5"],
                   links=PRIV / "hazard_tx/dallas/links_20261119/dallas_permit_links.parquet",
                   population=PRIV / "hazard_tx/dallas/population_20261119/dallas_population_2022.parquet", id="ACCOUNT_NUM"),
    "sanantonio": dict(permits=[PRIV / "sanantonio_permits_20261118/permits_issued_ending_12312024.csv",
                                PRIV / "sanantonio_permits_20261118/permits_issued.csv"],
                       permits_sha256=["45fef079740fc567ada8b55d83ad30d325397f367e0237e2b3a3a9b4e9c1edd5",
                                       "002fe3fdda58fa455c574d3376604087100ba88a282310ac2df466267cdeed95"],
                       links=PRIV / "hazard_tx/sanantonio_20261122/links/sanantonio_permit_links.parquet",
                       population=PRIV / "hazard_tx/sanantonio_20261122/population/sanantonio_population.parquet", id="PropID"),
}
DALLAS_RFR = "Residential Foundation Repair"
DALLAS_RAA = "Residential Alteration Addition Permit"
DALLAS_DEMOLITION = ["Demolition Permit SFD/Duplex", "Residential Demolition Permit"]
DALLAS_CONSTRUCTION = ["Building (BU) Single Family  New Construction", "Building (BU) Single Family  Addition",
                       "Building (BU) Single Family  Reconstruction", "Residential New Construction Permit"]
SA_FOUNDATION = "Foundation Repair Permit"
SA_DEMOLITION = "Demolition Permit"
SA_CONSTRUCTION = ["Res New Building Permit", "Home Addition Permit", "Building Move Permit"]
BEXAR_PAGES = PRIV / "bexar_parcels_current_20261119/pages"
BEXAR_PAGES_DIGEST = "d6c9ff98abe72491217080f65852e72a62ad93237dd0c04e93515219ea78102e"  # s0_population.py, step 0


def sa_recent_parcels():
    """Secondary 15 count: PropIDs of state code A1 whose CURRENT year built is after 2019 (the same layer pages as
    s0_population.py; attributes only)."""
    import pyogrio
    pages = sorted(BEXAR_PAGES.glob("oid_*_*.json"), key=lambda f: int(f.stem.split("_")[1]))
    assert hashlib.sha256("".join(sha256(f) for f in pages).encode()).hexdigest() == BEXAR_PAGES_DIGEST, "layer pages changed"
    g = pd.concat([pyogrio.read_dataframe(f, columns=["OBJECTID", "PropID", "State_cd", "YrBlt"], read_geometry=False)
                   for f in pages], ignore_index=True).drop_duplicates("OBJECTID")
    yb = pd.to_numeric(g.YrBlt, errors="coerce")
    return set(g.PropID[g.State_cd.eq("A1") & (yb > 2019)].astype(str).str.strip())


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


# ---------------------------------------------------------------- city adapters: one row per permit
def classify_dallas(t, desc, date, broad=False):
    """t: permit type, desc: work description (upper case), date: issue date. -> dict of boolean masks."""
    found_kw = desc.str.contains("FOUNDATION", regex=False)
    bu_sf = t.str.startswith("Building (BU) Single Family")
    raa = t.eq(DALLAS_RAA)
    found = t.eq(DALLAS_RFR) | (bu_sf & found_kw) | (raa & found_kw & (True if broad else (date < START)))
    demol = t.isin(DALLAS_DEMOLITION) & ~desc.str.contains(PARTIAL)
    constr = t.isin(DALLAS_CONSTRUCTION) | (raa & desc.str.contains("ADDITION", regex=False)) | demol
    return dict(found=found, demol=demol, constr=constr)


def classify_sanantonio(t, desc, date, broad=False):
    assert not broad, "--broad is a Dallas secondary"
    demol = t.eq(SA_DEMOLITION) & ~desc.str.contains(PARTIAL)
    return dict(found=t.eq(SA_FOUNDATION), demol=demol, constr=t.isin(SA_CONSTRUCTION) | demol)


CLASSIFY = dict(dallas=classify_dallas, sanantonio=classify_sanantonio)


def read_permits(city):
    """One row per permit: permit_number, type, description (upper case; Dallas work description, San Antonio project
    name), hid (population house or NA) and issue date, from the link table joined to the permit file(s)."""
    F = FILES[city]
    for f, s in zip(F["permits"], F["permits_sha256"]):
        assert sha256(f) == s, f"permit file changed: {f.name}"
    L = pd.read_parquet(F["links"], columns=["permit_number", "permit_type", "issue_date", F["id"], "target"])
    assert L.permit_number.is_unique
    if city == "dallas":
        P = pd.read_csv(F["permits"][0], dtype=str, keep_default_na=False, usecols=["Permit Number", "Permit Type", "Work Description"])
        P = P.rename(columns={"Permit Number": "permit_number", "Permit Type": "ptype", "Work Description": "desc"})
    else:
        P = pd.concat([pd.read_csv(f, dtype=str, keep_default_na=False, usecols=["PERMIT #", "PERMIT TYPE", "PROJECT NAME"])
                       for f in F["permits"]], ignore_index=True)
        P = P.rename(columns={"PERMIT #": "permit_number", "PERMIT TYPE": "ptype", "PROJECT NAME": "desc"})
        P = P.drop_duplicates("permit_number")  # the files repeat rows per contact (s4_link_check: first row kept)
    assert P.permit_number.is_unique
    D = L.merge(P, on="permit_number", how="left", validate="one_to_one")
    assert D.ptype.notna().all() and (D.ptype == D.permit_type).all(), "link table and permit file disagree"
    D["desc"] = D.desc.fillna("").str.upper()
    pop = pd.read_parquet(F["population"], columns=[F["id"]])  # ids only: no map value is read
    ids = set(pop[F["id"]].astype(str))
    on = D.target.eq("population house")
    assert D.loc[on, F["id"]].astype(str).isin(ids).all()
    D["hid"] = np.where(on, city + ":" + D[F["id"]].astype(str), None)
    D["date"] = pd.to_datetime(D.issue_date)
    return D[["permit_number", "ptype", "desc", "hid", "date", F["id"], "target"]], pop


# ---------------------------------------------------------------- rules (city-free)
def build(D, city, broad=False):
    """D: permit_number, ptype, desc, hid, date. Returns (first, events, demolition, counts)."""
    C = dict(permits=len(D), undated=int(D.date.isna().sum()), after_end_not_used=int((D.date > END).sum()))
    D = D[D.date.notna() & (D.date <= END)].copy()
    k = CLASSIFY[city](D.ptype, D.desc, D.date, broad)
    on = D.hid.notna()
    C["matched_foundation_permits"] = dict(all=int(k["found"].sum()), on_population_houses=int((k["found"] & on).sum()))
    m = D[k["found"] & on].sort_values(["hid", "date", "permit_number"])
    gap = m.groupby("hid").date.diff().dt.days
    n_anchor = 0
    for _, days in m.assign(t=(m.date - pd.Timestamp("1900-01-01")).dt.days).groupby("hid").t:
        s = None
        for v in days.to_numpy():
            if s is None or v - s > 365:
                s, n_anchor = v, n_anchor + 1
    C["episodes"] = dict(chained=int((gap.isna() | (gap > 365)).sum()), anchored=n_anchor, houses=int(m.hid.nunique()))
    first = m.groupby("hid", as_index=False).agg(t_first=("date", "first"), first_permit_number=("permit_number", "first"),
                                                 first_type=("ptype", "first"), n_matched=("date", "size"))
    con = D[k["constr"] & on][["hid", "date"]]
    first["status"] = np.where(first.t_first < START, "first episode before the study period", "event")
    j = first.loc[first.status.eq("event"), ["hid", "t_first"]].merge(con, on="hid")
    recent = j[(j.date < j.t_first) & (j.date >= j.t_first - pd.DateOffset(years=3))]
    first.loc[first.hid.isin(set(recent.hid)) & first.status.eq("event"), "status"] = "excluded: construction permit in the 3 years before"
    C["first_episode_status"] = {s: int(v) for s, v in first.status.value_counts().items()}
    ev = first.loc[first.status.eq("event"), ["hid", "t_first", "first_type"]].reset_index(drop=True)
    C["events"] = len(ev)
    C["events_by_year"] = {str(y): int(v) for y, v in ev.t_first.dt.year.value_counts().sort_index().items()}
    C["events_by_first_permit_type"] = {s: int(v) for s, v in ev.first_type.value_counts().items()}
    dm = D[k["demol"] & on].sort_values(["hid", "date", "permit_number"])
    dem = dm.groupby("hid", as_index=False).agg(t_demolition=("date", "first"))
    partial = on & D.ptype.isin(DALLAS_DEMOLITION + [SA_DEMOLITION]) & D.desc.str.contains(PARTIAL)
    C["demolition"] = dict(total_on_population_houses=len(dm), partial_on_population_houses=int(partial.sum()),
                           houses=len(dem), houses_on_or_before_2021_12_31=int((dem.t_demolition < START).sum()),
                           houses_by_year={str(y): int(v) for y, v in dem.t_demolition.dt.year.value_counts().sort_index().items()})
    C["construction_permits_on_population_houses"] = len(con)
    con_fu = con[(con.date >= START) & (con.date <= END)]
    return first, ev, dem, con_fu.drop_duplicates("hid")[["hid"]].reset_index(drop=True), C


# ---------------------------------------------------------------- self-test (synthetic permit tables only)
def write_tables(out, first, ev, dem, con_fu=None):
    """The files run_ht.read_tables reads (the self-test reads them back through it)."""
    first.to_parquet(out / "first_episodes.parquet", index=False)
    ev[["hid", "t_first"]].to_parquet(out / "events.parquet", index=False)
    dem.to_parquet(out / "demolition.parquet", index=False)
    if con_fu is not None:
        con_fu.to_parquet(out / "construction_2022_2025.parquet", index=False)


def selftest():
    T = pd.Timestamp
    rows = [  # (hid, type, description, date)
        # A: episode straddling 2021-12-31 -> first episode before the study period
        ("A", DALLAS_RFR, "", "2021-11-01"), ("A", DALLAS_RFR, "", "2022-03-01"),
        # B: demolition before the episode -> the demolition is also a construction permit: excluded; follow() exits B
        #    by demolition
        ("B", "Residential Demolition Permit", "DEMO SFD", "2022-05-01"), ("B", DALLAS_RFR, "", "2022-07-01"),
        # C: addition 2 years before -> excluded
        ("C", DALLAS_RAA, "ROOM ADDITION", "2020-03-01"), ("C", DALLAS_RFR, "", "2022-06-01"),
        # D: construction exactly 3 years before -> excluded (window [t-3y, t) is closed at t-3y)
        ("D", "Residential New Construction Permit", "", "2019-06-01"), ("D", DALLAS_RFR, "", "2022-06-01"),
        # E: construction 3 years and 1 day before -> event
        ("E", "Residential New Construction Permit", "", "2019-05-31"), ("E", DALLAS_RFR, "", "2022-06-01"),
        # F: RAA FOUNDATION in follow-up -> not matched (primary); event under --broad
        ("F", DALLAS_RAA, "FOUNDATION REPAIR", "2022-02-01"),
        # G: RAA FOUNDATION in the look-back -> first episode before the study period
        ("G", DALLAS_RAA, "FOUNDATION REPAIR", "2021-08-01"), ("G", DALLAS_RFR, "", "2023-01-01"),
        # H: partial demolition -> no demolition, no construction exit
        ("H", "Residential Demolition Permit", "PARTIAL DEMO OF REAR", "2022-01-10"), ("H", DALLAS_RFR, "", "2022-02-10"),
        # I: permit after END -> not used
        ("I", DALLAS_RFR, "", "2026-01-05"),
        # J: BU single family FOUNDATION in 2021-Q1 -> look-back
        ("J", "Building (BU) Single Family  Alteration", "FOUNDATION REPAIR", "2021-02-01"), ("J", DALLAS_RFR, "", "2022-02-01"),
        # K: event on the first day; L: alteration (no ADDITION) before an event -> event
        ("K", DALLAS_RFR, "", "2022-01-01"),
        ("L", DALLAS_RAA, "KITCHEN REMODEL", "2021-06-01"), ("L", DALLAS_RFR, "", "2022-06-01"),
        # M: non-population permit -> ignored
        (None, DALLAS_RFR, "", "2022-06-01"),
        # N: event on the last day; O: demolition on or before 2021-12-31; Q: demolition after the event -> event
        ("N", DALLAS_RFR, "", "2025-12-31"), ("O", "Demolition Permit SFD/Duplex", "", "2021-12-31"),
        ("Q", DALLAS_RFR, "", "2022-03-01"), ("Q", "Residential Demolition Permit", "", "2023-01-01"),
    ]
    D = pd.DataFrame(rows, columns=["hid", "ptype", "desc", "date"])
    D["date"] = pd.to_datetime(D.date)
    D["permit_number"] = [f"p{i:03d}" for i in range(len(D))]
    first, ev, dem, con_fu, C = build(D, "dallas")
    st = first.set_index("hid").status
    want = {"A": "first episode before the study period", "B": "excluded: construction permit in the 3 years before",
            "C": "excluded: construction permit in the 3 years before",
            "D": "excluded: construction permit in the 3 years before", "E": "event",
            "G": "first episode before the study period", "H": "event", "J": "first episode before the study period",
            "K": "event", "L": "event", "N": "event", "Q": "event"}
    assert st.to_dict() == want, st.to_dict()
    assert set(ev.hid) == {"E", "H", "K", "L", "N", "Q"} and C["after_end_not_used"] == 1
    assert dem.set_index("hid").t_demolition.to_dict() == {"B": T("2022-05-01"), "O": T("2021-12-31"), "Q": T("2023-01-01")}
    fb, evb, *_ = build(D, "dallas", broad=True)
    assert set(evb.hid) == {"E", "F", "H", "K", "L", "N", "Q"} and fb.set_index("hid").status["G"].startswith("first episode before")
    # follow-up: the frozen Ohenhen-Austin follow() on these tables
    sys.path.insert(0, str(HERE))
    import run_ht as R  # noqa: E402
    hids = list("ABCDEFGHIJKLMNOQ") + ["P"]
    W = R.world_from_tables(pd.Series(hids), first, ev, dem)
    # the file hand-off: write as main() writes, read back as run_ht reads (decoy and real modes)
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        write_tables(Path(tmp), first, ev, dem, con_fu)
        t = R.read_tables(tmp)
        W2 = R.world_from_tables(pd.Series(hids), t["first"], t["ev"], t["dem"])
        assert W2.equals(W) and set(t) == {"first", "ev", "dem", "con"} and t["con"].hid.tolist() == con_fu.hid.tolist()
    F = R.follow(W.t_ep, W.t_dem, W.t_event, START, END, np.ones(len(hids), bool))
    at = dict(zip(hids, F["at"])); y = dict(zip(hids, F["y"])); py = dict(zip(hids, np.round(F["py"] * 365.25, 6)))
    assert not at["A"] and not at["G"] and not at["J"] and not at["O"] and at["B"] and at["P"]
    assert y["B"] == 0 and F["demolished"][hids.index("B")] == 1 and py["B"] == (T("2022-05-01") - START).days + 0.5
    assert y["C"] == 0 and py["C"] == (T("2022-06-01") - START).days + 0.5  # exit without event
    assert y["K"] == 1 and py["K"] == 0.5 and y["N"] == 1 and py["N"] == (END - START).days + 0.5
    assert y["P"] == 0 and py["P"] == (END - START).days + 1 == 1461 and y["F"] == 0 and py["F"] == 1461
    assert y["Q"] == 1 and py["Q"] == (T("2022-03-01") - START).days + 0.5 and F["demolished"][hids.index("Q")] == 0
    sa = pd.DataFrame([("S1", SA_FOUNDATION, "", "2022-03-01"), ("S2", "Home Addition Permit", "", "2021-03-01"),
                       ("S2", SA_FOUNDATION, "", "2023-01-01"), ("S3", SA_DEMOLITION, "PARTIAL DEMOLITION", "2022-01-05"),
                       ("S3", SA_FOUNDATION, "", "2022-04-01"), ("S4", "Res Foundation Permit", "", "2022-04-01"),
                       ("S5", "Building Move Permit", "", "2022-02-01"), ("S5", SA_FOUNDATION, "", "2024-02-01")],
                      columns=["hid", "ptype", "desc", "date"])
    sa["date"] = pd.to_datetime(sa.date)
    sa["permit_number"] = [f"s{i}" for i in range(len(sa))]
    f2, e2, d2, c2, _ = build(sa, "sanantonio")
    assert set(e2.hid) == {"S1", "S3"} and len(d2) == 0 and set(c2.hid) == {"S5"}
    assert f2.set_index("hid").status["S2"].startswith("excluded") and f2.set_index("hid").status["S5"].startswith("excluded")
    print("build_events self-test passed: 22 synthetic houses (look-back, straddling episode, demolition before episode, "
          "3-year construction window edges, partial demolition, permits after END, broad Dallas outcome, half-day exits; file hand-off to run_ht)")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--city", choices=list(FILES))
    ap.add_argument("--broad", action="store_true")
    ap.add_argument("--out", type=Path)
    ap.add_argument("--out-json", type=Path)
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    sys.path.insert(0, str(HERE))
    import run_ht as R  # noqa: E402  (refuses real permits until the plan is frozen)
    R.assert_frozen()
    out = a.out / (a.city + ("_broad" if a.broad else ""))
    out.mkdir(parents=True, exist_ok=False)
    D, pop = read_permits(a.city)
    first, ev, dem, con_fu, C = build(D, a.city, a.broad)
    write_tables(out, first, ev, dem, con_fu if a.city == "sanantonio" else None)
    if a.city == "sanantonio":
        k = classify_sanantonio(D.ptype, D.desc, D.date)
        fu = k["constr"] & D.date.between(START, END)
        recent = sa_recent_parcels()
        C["secondary_15"] = dict(population_houses_with_construction_permit_2022_2025=len(con_fu),
                                 construction_permits_2022_2025_on_a1_parcels_built_after_2019=int((fu & D.PropID.astype(str).isin(recent)).sum()),
                                 a1_parcels_built_after_2019=len(recent))
    S = dict(city=a.city, broad=a.broad, inputs={f.name: sha256(f) for f in FILES[a.city]["permits"]} |
             {"links": sha256(FILES[a.city]["links"]), "population": sha256(FILES[a.city]["population"])},
             population_houses=len(pop), counts=C, script_sha256=sha256(Path(__file__)),
             private_outputs_sha256={f.name: sha256(f) for f in sorted(out.glob("*.parquet"))},
             note="No map value was read. Counts only; no description or address.")
    a.out_json.write_text(json.dumps(S, indent=1) + "\n")
    print(json.dumps(S, indent=1))


if __name__ == "__main__":
    main()
