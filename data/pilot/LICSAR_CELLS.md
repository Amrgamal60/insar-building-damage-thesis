# LiCSAR velocity per cell

**Plan:** `LICSAR_TEST_PLAN.md`. **Processing:** `scripts/15_licsbas_run.sh` (LiCSBAS steps 02 and 11–16, then P1/P2 velocity and the vertical decomposition). **Reproduce:** `.venv/bin/python scripts/16_licsar_cells.py` (after 07 and 15).

- **P1** = first epoch to 2016-12-31 (primary); **P2** = full period. Linear fits to LiCSBAS's filtered cumulative displacement, masked by step 15. Vertical = both frames decomposed with their LOS unit vectors, assuming no north–south motion; mm/yr, positive up. The reference is each frame's own stable point, so absolute levels are arbitrary; the tests only use differences between cells.
- **Cell value** = mean of the valid pixels (0.001°, about 95 × 111 m) whose centres fall in the cell, on the pilot's grid.

## Result

- **Coverage is complete for the primary test.** All 241 of the Shirzaei test's core cells at 250 m, and all 32 of their collapse cells, have a LiCSAR vertical velocity, so no cell is dropped. 341 of the 416 core cells have one (all 34 collapse cells), as do 2,872 of the 3,300 eligible cells city-wide (all 50) and 345 of the Shirzaei test's 347 cells at 200 m.
- **Processing:** LiCSBAS kept 822 of 1,153 interferograms (065D) and 1,621 of 2,199 (131A). Step 15 kept 38–39% of the pixels with a time series; 20,575 pixels are valid in both frames. Both networks have gaps in 2015 (065D: October–November; 131A: June–September and October–November), which LiCSBAS bridges with its default linear constraint, so P1 (64 and 57 epochs) rests mainly on the connected stretch from November 2015 to December 2016.
- **Agreement with Shirzaei (secondary check 7):** Spearman ρ = 0.81 city-wide (1,763 shared cells) and 0.77 in the core (241) for P1; 0.75 and 0.89 for P2. The medians differ (LiCSAR +0.5 and +2.5 mm/yr, Shirzaei −3.1) because LiCSAR is relative to each frame's reference point and Shirzaei is in IGS14; the tests use only differences between cells.

## LiCSBAS processing

| Frame | Interferograms | Dropped in step 11 | Dropped in step 12 | Epochs used | Epochs in P1 | Pixels kept by step 15 | Pixels with a P1 velocity | Reference (step 16) |
|---|---|---|---|---|---|---|---|---|
| 065D_05935_131108 | 1153 | 8 | 323 | 227 (20141010–20230824) | 64 | 23,795 of 62,387 with a time series (38%; box 132,000) | 23,794 | 214:215/161:162 |
| 131A_05957_110910 | 2199 | 0 | 578 | 408 (20141107–20230909) | 57 | 24,308 of 62,851 with a time series (39%; box 132,000) | 24,307 | 334:335/191:192 |

## Coverage (cells with a value; collapse cells in brackets)

| Cell size | Cells | Count (collapse cells) | Vertical, P1 (primary) | Vertical, P2 | 065D line of sight, P1 | 131A line of sight, P1 | Pixels per covered cell, vertical P1 (median) |
|---|---|---|---|---|---|---|---|
| 250 m | All eligible cells | 3,300 (50) | 2,872 (50) | 2,872 (50) | 2,959 (50) | 2,989 (50) | 5 |
| 250 m | Historic core, cells with baseline inputs | 416 (34) | 341 (34) | 341 (34) | 346 (34) | 353 (34) | 6 |
| 250 m | Historic core, Shirzaei-covered (Shirzaei test's cells) | 241 (32) | 241 (32) | 241 (32) | 241 (32) | 241 (32) | 6 |
| 200 m | All eligible cells | 4,745 (53) | 4,141 (53) | 4,141 (53) | 4,287 (53) | 4,299 (53) | 4 |
| 200 m | Historic core, cells with baseline inputs | 623 (38) | 510 (38) | 510 (38) | 520 (38) | 518 (38) | 4 |
| 200 m | Historic core, Shirzaei-covered (Shirzaei test's cells) | 347 (36) | 345 (36) | 345 (36) | 346 (36) | 345 (36) | 4 |

## Agreement with Shirzaei velocity (secondary check 7, descriptive)

| Cell size | Cells | LiCSAR | Shared cells | Spearman ρ with Shirzaei VLM | Median, LiCSAR / Shirzaei (mm/yr) |
|---|---|---|---|---|---|
| 250 m | All eligible cells | Vertical, P1 (primary) | 1,763 | 0.81 | 0.5 / -3.1 |
| 250 m | All eligible cells | Vertical, P2 | 1,763 | 0.75 | 2.5 / -3.1 |
| 250 m | Historic core | Vertical, P1 (primary) | 241 | 0.77 | 0.6 / -3.1 |
| 250 m | Historic core | Vertical, P2 | 241 | 0.89 | 2.6 / -3.1 |
| 200 m | All eligible cells | Vertical, P1 (primary) | 2,419 | 0.80 | 0.6 / -3.1 |
| 200 m | All eligible cells | Vertical, P2 | 2,419 | 0.73 | 2.7 / -3.1 |
| 200 m | Historic core | Vertical, P1 (primary) | 345 | 0.76 | 0.6 / -3.1 |
| 200 m | Historic core | Vertical, P2 | 345 | 0.89 | 2.7 / -3.1 |
