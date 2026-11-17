# Keyword protocol (locked before any match counts)

Access date of this lock: 2026-10-26.
This file is written before any filtered counts are retrieved. The keyword list and exclusion rules below are not changed after counts are seen.

## Fields

- Work-description field: the permit description / work description text, case-insensitive.
- Work-class or type field: included in the same keyword search when the dataset has one (Austin: `work_class` and `permit_type` and `permit_class` if present; Houston: equivalent type/class columns if present). A row matches if ANY searched text field contains a keyword.

## Keywords (substring, case-insensitive)

foundation, pier, piers, piering, push pier, helical, underpin, underpinning, slab repair, leveling, levelling, house level, mudjack, re-level, shim, foundation repair

Applied as a single regular expression with word-aware handling only where a short token would otherwise match inside an unrelated word:

- `pier` also matches `piers` and `piering` via the tokens `pier`, `piers`, `piering`.
- `shim` is matched as a whole word (`\bshim\b`) so it does not match "shimmer" or similar.
- `leveling`, `levelling`, `re-level`, `house level` are substrings.
- `helical` is a substring (covers "helical pier").
- `foundation` is a substring (covers "foundation repair").

Regex (Python, IGNORECASE), locked:

```
foundation|underpin(?:ning)?|slab repair|levell?ing|house level|mudjack|re-level|\bshim\b|helical|(?:push )?pier(?:s|ing)?
```

Note: `foundation` already covers the phrase `foundation repair`. The phrase is listed in the task and is not an extra rule.

## Exclusion rules (applied after the keyword match, before counts are recorded)

A keyword-matched permit is excluded when the description or type/class text shows any of the following. Rules are applied in this order; the first matching rule is the exclusion reason.

1. **new_construction_foundation_only** — permit class/type or description indicates new construction, new building, or new residential structure (for example permit type "Building Permit" with work class "New", or description starting with or dominated by "new" single-family / new commercial building), AND the only foundation language is installation of a new foundation ("foundation only", "new foundation", "pour foundation") with no repair, pier, underpin, level, mudjack, or shim language.
2. **pool** — description or type is a swimming pool, spa, or pool deck, and the foundation/pier language refers to the pool shell or pool deck rather than a building foundation.
3. **sign** — description or type is a sign, billboard, or monument sign.
4. **retaining_wall** — description is only a retaining wall, screen wall, or fence footing, with no building-foundation repair language.
5. **pier_not_foundation** — the only hit is "pier" used for a waterfront pier, dock, boat pier, fishing pier, or bridge pier, with no building-foundation language.
6. **mechanical_or_electrical_pier** — "pier" appears only as part of an unrelated trade phrase that is not a foundation pier (none anticipated; recorded if observed). This rule is not used to drop helical piers, push piers, or concrete piers under a building.

Permits that mention both a new building and foundation repair, underpinning, leveling, or piers under an existing structure are KEPT.

Permits whose description is only the keyword with no other context are KEPT and left for the A4 manual sample to classify.

No other exclusion is applied. Counts below this protocol use this locked list.
