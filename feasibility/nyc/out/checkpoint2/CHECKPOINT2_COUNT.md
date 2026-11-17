# Checkpoint 2, part 1: grid, eligibility, domain and the §6 event count

**Reproduce:** from `feasibility/nyc/`, `../../.venv/bin/python -I scripts/04_grid_domain.py raw out`. No InSAR value is read.

- **PLUTO 15v1 lots:** 859,464; with a lot point 834,271; point inside the study area 833,767.
- **Year built recorded (> 0):** 811,595 lots in the study area, of which 463,017 were built before 1940. Recorded values range from 1661 to 2040.
- **WSF settled pixels (1985–2015) around NYC:** 2,223,702.

|  | 250 m | 200 m |
|---|---|---|
| Cells with a lot point | 10521 | 15736 |
| Built-up | 10403 | 15559 |
| Eligible (built-up and settled) | 10320 | 15438 |
| Eligible and in the domain | 5001 | 7475 |
| Eligible cells with centre on water | 272 | 291 |
| Events from 2017-07-16 | 82 | 82 |
| … cell eligible | 82 | 82 |
| … and no earlier event in the cell (whole NYC) | 79 | 80 |
| … and in the domain (§6 count) | 65 | 70 |
| First events sharing a cell and date | 2 | 2 |

**Eligible 250 m cells by landmass group:** Bronx 1,417 (702 in the domain); Brooklyn+Queens 6,250 (3,392 in the domain); Manhattan 855 (648 in the domain); Staten Island 1,798 (259 in the domain).

**§6 decision (250 m):** 65 events, so the primary population is **the older-building domain**. The 200 m count (70) is reported only; the decision is made once, at 250 m.
