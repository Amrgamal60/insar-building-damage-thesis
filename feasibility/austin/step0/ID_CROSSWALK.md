# Austin 2019–2026 TCAD identifier crosswalk

Outcome-blind audit, 2026-10-31. The frozen inputs contain **151,944 eligible 2019 parcel accounts**, conventionally called houses in the plan. **150,053 have a parcel-account successor and 1,891 remain unresolved**. Account or lot continuity does not establish continuity of the physical dwelling.

The main verified obstacle is missing corresponding coverage in the public 2026 products: **1,837 of the 1,891 unresolved representative points lie in gaps in the complete hosted geometry**; another **54** intersect hosted polygons but fail the overlap rules. Broad or local geometric misregistration does not explain this group. The institutional causes of the missing records—confidentiality suppression, condominium conversion, re-subdivision, or another omission—remain **UNVERIFIED**. Unresolved does **not** mean demolished, no improvement, or a missing historical permit key.

## Scope and source control

No permit file, outcome, InSAR/OPERA/Sentinel data or metadata was read, and no model was fitted. Row-level IDs, geographic aliases, geometry and evidence tables are confined to `/mnt/data/Master-projects/Alex_private/austin/crosswalk/`. No owner, mailing, address or situs fields are extracted by the final script. Following the coordinator's confidential-record guard, no legal-description recovery rule or cross-source text join is included; exploratory text-join products were discarded and no such matches were accepted.

Sources are the September 2019 TxGIO/TCAD mirror; 2026 certified supplement-0 `PROP`, full raw `IMP_INFO`, their fixed-width layouts; the previously produced, outcome-blind all-A1 `static_checks_2026/parcel_fields.parquet`; the 2026 diagnostic population; all valid geometry pages named in `tcad_manifest.json`; and the existing official full-purpose boundary. The all-A1 derivative provides the selected type 01/16 main dwelling even when hosted geometry is absent. It uses the existing largest living-floor-area rule, ties by improvement ID, and the minimum positive first-floor year. Foundation and living area are not extracted for this audit.

The hosted layer is named “TCAD Parcels Dec 2025”, is maintained monthly, and its metadata reports a last edit on 2026-10-02. Its precise geometry observation date and the dates of individual identifier transitions are **UNVERIFIED**; the layer name is not a December 2025 freeze. The 2019 population uses its original centroid strictly inside the same official Austin boundary as v1, then deduplicates property ID; it retains the denominator of 151,944.

The freshly retrieved [public hosted-layer schema](https://services1.arcgis.com/HGcSYZ5bvjRswoCb/arcgis/rest/services/TCAD_Parcels_Dec_2025/FeatureServer/0?f=pjson) is archived privately with URL, UTC time, HTTP status, bytes and SHA-256 in `crosswalk_manifest.json`. Independent Tax Office layer metadata and a fresh TCAD FAQ request timed out and are recorded as failed attempts; no alternate geometry was downloaded. TCAD's FAQ was already archived by the earlier availability audit. No gate, login or credential was used.

## Crosswalk rules and final stages

Every historical account takes the first accepted stage. Identifiers are compared as stripped strings with numeric padding removed, while original geographic strings and leading zeros are retained in private outputs. Blank keys are never matches. Repeated 2026 polygon features are dissolved by property ID; geometry is repaired before intersection, in EPSG:32614.

1. **Same property ID:** the internal ID exists in the 2026 certified roll, regardless of state code. All **149,857** such matches also have the same geographic ID. This establishes account continuity, including changed uses or replacement houses.
2. **Same geographic ID under a different property ID:** require nonblank keys unique among the 2019 reference accounts and in the 2026 roll, plus hosted geometry corroboration with at least 90% overlap in both directions. **0** pass.
3. **Spatial:** let *a* be intersection area / old area and *b* intersection area / successor area. A unique polygon with *a* ≥ 0.9 and *b* ≥ 0.9 is a one-to-one **renumbering**; a unique polygon with *a* ≥ 0.9 and *b* < 0.9 is a **merge**. Otherwise, at least two polygons each with *b* ≥ 0.9 must jointly cover ≥90% of the old lot for a **split**; competing full-cover candidates remain ambiguous. Coverage uses the geometric union, so overlapping successors cannot double-count old area. All other cases are unresolved. Geometry establishes a lot relationship, not a dated cadastral lineage or an unchanged house.

| Final stage | 2019 accounts |
|---|---:|
| Stage 1: same property ID | 149,857 |
| Stage 2: corroborated geographic ID | 0 |
| Stage 3: one-to-one renumbering | 21 |
| Stage 3: merged lot | 126 |
| Stage 3: split lot | 49 |
| Unresolved | 1,891 |
| **Total** | **151,944** |

**Correction to v1:** both of its stage-2 geographic candidates have **zero area overlap** with the named current account's polygon; one old key also occurs on a different reference house. Their actual lots have reciprocal spatial overlap of approximately 99.6–100% with different current polygons. Both therefore move to stage-3 renumberings: v1 had 2 geographic matches and 19 renumberings; this audit has 0 and 21. The 126 merges, 49 splits and 1,891 unresolved counts are unchanged. The zero-overlap count and rejection-reason counts are in the aggregate JSON. This is a correction of misleading key matches, not an additional recovery.

Three historical geographic keys each occur on two distinct reference houses—**six accounts**, with non-overlapping lots and centroid separations approximately 129–140 m. The private alias table flags collisions. Do not choose an arbitrary first account or copy one permit to both houses.

## One final category for every historical account

The following mutually exclusive categories exhaust the denominator. For merges/splits the final category records the parcel change; the private crosswalk additionally preserves the set of successor statuses. For single-successor cases it records the roll/main-dwelling status. Full non-A1 state-code detail remains in `status_by_stage` in the aggregate JSON.

| Final category | 2019 accounts |
|---|---:|
| 2026 A1 townhouse, different/missing recorded year | 2 |
| 2026 A1 townhouse, same recorded year | 2,152 |
| 2026 A1 type 01 pre-2016, outside diagnostic geometry/boundary | 25 |
| 2026 A1 type 01, recorded year missing | 8 |
| 2026 A1, recorded year after 2015 (rebuild/update proxy) | 2,483 |
| 2026 A1, selected main dwelling missing | 26 |
| 2026 detached diagnostic population | 144,056 |
| 2026 non-A1 | 1,124 |
| parcel merged: physical continuity unverified | 126 |
| parcel split: physical continuity unverified | 49 |
| successor absent from certified roll | 2 |
| unresolved: partial/ambiguous hosted overlap | 54 |
| unresolved: point in hosted gap | 1,837 |
| **Total** | **151,944** |

A recorded 2026 year after 2015 is a **rebuild/update proxy**, not a verified demolition or construction date. Current type 01 plus an old recorded year is likewise not conclusive proof that the original dwelling survives. Status uses the roll's improvement state code; land-only A1 is not silently promoted to an improved A1 dwelling.

Using all A1 roll accounts repairs v1's treatment of 28 same-ID A1 accounts missing hosted polygons: it had mislabeled these as “not A1”. Among same-ID accounts, the revised figures include **2,479** with a recorded year after 2015, **2,152** type-16 townhouses with the same recorded year, **2** type-16 townhouses with a different/missing year, and **1,124** non-A1 accounts. The original 144,041 same-ID accounts in the current detached diagnostic population are unchanged.

## Why the 1,891 remain unresolved

**Pagination/coverage audit.** All 39 valid pages are present: **386,682 features, 386,682 distinct object IDs, 373,524 distinct property IDs**. Invalid JSON and ArcGIS error bodies in the manifest are skipped; valid retries fill every expected 10,000-record offset. Thus this is not a lost-page explanation. The fresh layer schema has no definition expression, relationships, previous/parent/reference/UDI fields. This rules out a published layer-level filter expression, not omissions upstream of publishing.

**Direct spatial evidence.** Only 54 representative points are inside any hosted polygon; 1,837 are outside every polygon. Nearest-polygon distances have median **8.76 m**, 90th percentile **15.67 m**, 95th **21.32 m**, and maximum **92.09 m**. Some positive overlap exists for **1,721** old lots, commonly boundary slivers; the other **170** have none. Tiny slivers do not identify a successor. Even a 50% threshold leaves 1,842 unresolved.

**Misregistration test.** There are **149,826** same-ID historical houses with current geometry. Their median intersection-over-union is **0.999997**; 90% have IoU at least approximately 0.999987. For each unresolved lot, up to 20 nearest same-ID control centroids within 200 m provide a local median displacement. **1,889** have at least one such control; **1,774** have a local displacement below 1 m, the median is approximately **0.000010 m**, and the 95th percentile is **1.30 m**. Applying that diagnostic local translation brings only **one** unresolved lot to a maximum individual overlap ≥90%; none is accepted through a shift rule. Two lots lack nearby controls, so their local alignment test is **UNVERIFIED**. Large displacement outliers do exist among individual changed parcels; there is no evidence for a common offset explaining the group.

**Property-type omissions and condominium conversion.** The certified roll has **54,571 A4 condominium accounts**, of which **53,543 lack hosted polygons**, versus **414/289,879 A1** accounts lacking polygons. Commercial condominiums are also poorly represented (**2,798/2,825 F4** without polygons). Therefore “full feature count” does not mean full roll coverage, and condominium-regime accounts can lack independently mappable polygons. Eleven same-ID old A1 houses now have an A4 roll code, verifying some account-class conversion outside the unresolved group. But current condo accounts are not linked individually to the missing old lots: the number of unresolved houses attributable to condominium conversion is **UNVERIFIED**. Missing condo geometry alone cannot explain the 1,891 as a proven cause.

**Re-subdivision.** The 126 merges and 49 splits verify strong geometric lot reconfiguration. The unresolved 54 contained points have inadequate or ambiguous coverage, compatible with further reconfiguration; no dated parent/child record confirms that interpretation. Their individual underlying cause remains **UNVERIFIED**.

**Suppression/other source omissions.** [TCAD's FAQ](https://traviscad.org/faqs) confirms that eligible people can request restrictions on publicly accessible home-address information. The raw export includes confidentiality flags: current-appraisal and property-year flags are false for all 493,324 rows, while 25 January-1 flags are true. Together with isolated geometry gaps and absence of exact current account/geo matches, suppression is a plausible explanation. Whether TCAD suppresses these particular records, and how much of the group it explains, is **UNVERIFIED**; no individual withheld account was identified or recovered. A missing public record is not evidence that its house ceased to exist.

**Reference fields.** The full property layout has generic `ref_id1` and `ref_id2`, but neither is documented as a prior/parent identifier. After deduplicating current property ID, `ref_id1` is nonblank for **35,715** accounts; `ref_id2` for **493,246**. Neither yields an exact unresolved old property-ID or geographic-ID match. `udi_group` is explicitly a grouping of partial owners, not a split/merge history: only **34 distinct property accounts** have nonzero groups after deduplication, and none points to an unresolved old ID. The 112 raw nonzero UDI rows collapse because of repeated owner-level property rows. Supplement action/code/description are blank throughout this certified supplement-0 snapshot. No documented parent/previous-ID crosswalk was recovered; no undocumented prefix or numeric coincidence becomes a link.

## Improvement-absence correction

The derived `IMP_INFO.TXT.parquet` was restricted to the **289,879 A1 property IDs**, with **zero** non-A1 property IDs. Its absence cannot mean “no improvement” for other property classes. The full raw file has **454,986 rows / 401,279 distinct property IDs**. Among the **1,124** same-ID accounts now non-A1, **568 have raw improvement records** and **556 do not**. V1's blanket no-improvement suffix was therefore invalid and has been removed. Even absence from the raw file is not a demolition date or proof that the historical house was removed.

## Threshold sensitivity

The two misleading geographic candidates are sent to stage 3 at every threshold; its denominator is therefore **2,087** historical accounts. Both remain spatial renumberings at these thresholds.

| Threshold for *a*, *b*, and union coverage | Renumbered | Merged | Split | Unresolved |
|---|---:|---:|---:|---:|
| 0.9 | 21 | 126 | 49 | 1,891 |
| 0.8 | 25 | 132 | 62 | 1,868 |
| 0.5 | 97 | 110 | 38 | 1,842 |

The 0.8 and 0.5 rules recover only **23** and **49** additional accounts relative to 0.9. Kind counts need not increase monotonically: a lot can change from split/merged to a one-to-one classification when the threshold is relaxed. The v1 sum-of-overlaps rule gives the same classifications on these inputs at each threshold, apart from its earlier two geographic assignments; union coverage guards against a false split on future overlapping geometry. Retain 0.9 for the registered rule. Looser thresholds and local shifts are diagnostics, not extra accepted edges.

## Reverse reconciliation: all 417

The current detached diagnostic population has **144,458** accounts. Of these, **144,041** have a same-ID eligible historical account, leaving **417**. The following first-applicable reasons exhaust those 417; “not in 2019 layer” is not interpreted as a newly constructed house because missing historical coverage is also possible.

| Reason | Current accounts |
|---|---:|
| 2019 state code A2 | 24 |
| 2019 state code A3 | 17 |
| 2019 state code A4 | 26 |
| 2019 state code A9 | 1 |
| 2019 state code B1 | 2 |
| 2019 state code B2 | 80 |
| 2019 state code B3 | 3 |
| 2019 state code B4 | 1 |
| 2019 state code C1 | 13 |
| 2019 state code E1 | 1 |
| 2019 state code F1 | 10 |
| 2019 state code F5 | 8 |
| 2019 state code O1 | 18 |
| 2019 state code missing | 10 |
| 2019 year built missing or after 2015 | 62 |
| not in 2019 layer | 96 |
| successor of 2019 house(s), stages 2/3 | 45 |
| **Total** | **417** |

Among crosswalk-linked current accounts, the kinds are merged: **12**, renumbered: **15**, same geo_id: **0**, split: **18**. These are current-account counts, distinct from counts of old houses pointing to them. **2** current accounts have multiple historical predecessors. Correcting the two geographic candidates increases linked successors from v1's 43 to **45** and decreases the residual absent-from-2019-layer category from 98 to **96**. The private reverse table records every predecessor rather than silently selecting one. Do not add reverse-only entrants to the historical cohort.

## Recommendation to register

**Population membership.** Fix membership from the 2019 A1/year/boundary rule and retain accounts later rebuilt, reclassified, split, merged or unresolved. Use stages 1 and corroborated 2, and one-to-one stage-3 renumberings, as parcel-identity evidence only; use a matching recorded year and a unique relationship before transporting a later house characteristic to the reference house. Do not exclude an old house just because a current account is absent, lacks a polygon, or is now commercial/vacant. Splits and merges remain historical cohort members with physical continuity and successor-characteristic transfer marked unknown.

A strictly detached 2019 population cannot be proved from the historical layer's A1 code alone. Prefer describing C as an **A1 historical house proxy**, with current townhouse flags reported, and a prespecified sensitivity excluding the **2,152** unambiguous same-ID, same-recorded-year current townhouses (leaving **149,792** historical accounts). If the plan instead uses this proxy exclusion in the primary analysis, register the assumption that unchanged recorded year implies unchanged dwelling type, and call unknown historical types unknown. In particular, do not call the 1,891 unresolved accounts “gone detached houses”.

**Permit linkage.** Use the original 2019 `GEO_ID` as the primary key independently of 2026 survival. Every reference account has a historical key, although **three keys / six accounts are ambiguous** and must be reported as unallocatable rather than assigned by first match or duplicated. Stage 1 supplies the same geographic key; a validated stage 2 would also preserve that key, but none passes here. For changed-key linkage, pre-register unique one-to-one stage-3 renumbering aliases only as an explicitly flagged extension/sensitivity: current geometry alone cannot date when an alias belonged to the old house. Of the 21 renumberings, 19 successors are present in the certified roll and supply changed geographic aliases; two are geometry-only accounts absent from that roll. Do not treat the 21 spatial renumberings as 21 proven unchanged physical houses, and exclude current-only/no-roll aliases from a certified-roll-confirmed mapping. Original-key links to unresolved accounts remain possible; no outcome match rate was examined here.

**Split/merged lots and unrecoverable information.** Do not allocate a successor's permits to all predecessor houses, distribute permits by area, or copy old houses into each new child. Retain direct historical-key permit links under the plan's construction exclusions and demolition censoring; successor-key permits for split/merged or conflicting relationships remain unallocated to an individual reference house without an independently documented, dated and outcome-blind building-level chain. Do not infer a demolition date from the endpoint roll. The current successors of 1,891 accounts, some historical dwelling types, and transition dates remain unrecoverable from these products. The corresponding uncertainty must not be converted to a zero outcome.

## Reproduction and validation

Run from the project root, offline:

```sh
/mnt/data/Master-projects/Alex/.venv/bin/python -I feasibility/austin/step0/scripts_refdata/id_crosswalk.py /mnt/data/Master-projects/Alex_private/austin feasibility/austin/step0/id_crosswalk.json /mnt/data/Master-projects/Alex_private/austin/crosswalk/crosswalk_2019_2026.parquet feasibility/austin/step0/tcad_manifest.json
```

The script caches parsed parcel and selected raw-roll fields only in the private crosswalk directory, keyed by source hashes and schema version. The original v1 script and JSON are preserved privately as `id_crosswalk_v1.py` and `id_crosswalk_v1.json`; the aggregate JSON also records v1's stage counts and original threshold sensitivity for comparison. Input hashes and invariant checks are in `id_crosswalk.json`; remove the private cache files to force extraction again. No download is required to rerun the audit. `crosswalk_2019_2026.parquet` contains exactly one row per historical account, its rule/final category, successor IDs/statuses, preserved geographic strings and raw-improvement availability. Separate private files contain reverse relationships, collision-flagged geographic aliases, overlap evidence and nearest-polygon evidence.

Validation: all **151,944** rows have one category, stage/category totals reconcile, all **417** reverse cases reconcile, and the final aggregate JSON was reproduced byte-for-byte on a second execution. The final script was syntax-checked and inspected for explicit input paths; no forbidden data path or owner/address/situs/text-recovery extraction is present. Only the assigned script, aggregate JSON, this report and download manifest were changed in the project.

## Coordinator check (Claude, 2026-10-31)

- **Reproduction:** rerunning the script from the project root, with the row-level output in a separate private folder, gave an `id_crosswalk.json` byte-identical to this one (SHA-256 `cc452d5be4c12a1f…`).
- **Condominium figures:** an independent count gave A4 54,675 accounts (53,646 without polygons) and A1 290,624 (441 without polygons). It differs slightly from the counts above because its state code falls back to the land state code when the improvement state code is blank. The conclusion is the same.
- **Plan use:** the registered rule is in AUSTIN_PLAN §5. It follows the recommendation above, but keeps the townhouse exclusion in the primary population under C, with the assumption registered (confirmed by the user on 2026-11-01). Sensitivity P0 drops that exclusion (AUSTIN_PLAN §12).
