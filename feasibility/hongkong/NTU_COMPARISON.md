# Hong Kong: our velocities against the Tay et al. 2022 (NTU) map

Done 2026-10-17, as asked in the GPT review: set out how far the two products can be compared, then compare them on the same pixels. No order data were used. Numbers come from `feasibility/hk_ntu_compare.py` (saved in `mintpy/NTU_COMPARISON.json`). NTU's settings are from the Methods of Tay et al. 2022 (Nature Sustainability 5:1049–1057). ASF facts are from the HyP3 burst InSAR product guide.

## 1. Settings

| Item | NTU map (Tay et al. 2022) | Ours: run 2 | Ours: local product |
|---|---|---|---|
| Period | Oct 2014 – Apr 2020 | Jun 2015 – Apr 2023; also refitted to Jun 2015 – Apr 2020 | Same as run 2 |
| Track | One track, the one with better coverage. The file is named TA011 (ascending 11). | Ascending 11, bursts 021605–07, IW3; incidence 42–46° | Same as run 2 |
| Looks, pixel spacing, resolution | 19 × 7 looks, geocoded at 90 m | HyP3 10 × 2 looks: 40 m pixel spacing, about 80 m resolution (ASF). Goldstein filter before unwrapping. | Same as run 2 |
| Network | Each date paired with its 2 nearest dates | 862 pairs: 3 nearest dates plus about one year | Same as run 2 |
| Unwrapping and fixes | SNAPHU; MintPy bridging and phase closure. Shenzhen was left out of their study for unwrapping errors. | SNAPHU (HyP3); MintPy bridging | Each pair's phase minus the mean of the same unwrapped component within 1 km. This cancels whole-cycle component offsets. |
| Troposphere | ERA5 (PyAPS) | Height correlation | None. The 1 km reference removes most of it. |
| Plane removal | Linear | None | None (the local reference removes it) |
| DEM error | Corrected | Corrected | Corrected |
| Reference | Hand-picked stable pixel on a man-made structure, coherence > 0.85, velocity near the city's mode | MintPy's automatic choice: a pixel in Shenzhen | Each pixel against its own 1 km surroundings |
| Mask | Coherence < 0.35 left out | Temporal coherence ≥ 0.7 (used here) | Temporal coherence ≥ 0.7 |
| Gap filling | Yes. A kriging-type interpolation with per-pixel uncertainty, kept where ≥ 40 pixels lie within ~1 km. Its pixels are not independent measurements. | None | None |
| Direction | Vertical: LOS / cos(incidence) | Line of sight; converted the same way for this comparison | Same as run 2 |
| Units, sign | m/yr in the file; negative = down | m/yr in the file; positive = toward the satellite. Compared in mm/yr, negative = down. | Same as run 2 |

**Can't be matched:**
- the exact period (we have no data before June 2015);
- NTU's network, troposphere correction and interpolation;
- the NTU reference pixel (not in the file).

## 2. How they were compared

- **Shared pixels:** our pixels with temporal coherence ≥ 0.7 were averaged into each ~90 m NTU pixel. Only NTU pixels that are finite and hold at least one of ours were used: 15,344 for run 2 and 24,952 for the local product.
- **The four views:**
  - **As is:** each map with its own reference.
  - **Both trend-removed:** the same plane (lon, lat) removed from both over the shared pixels.
  - **Both 1 km-local:** the same 1 km local reference applied to both on that grid.
  - **Blocks:** both maps averaged into square blocks of 0.5, 1, 2 and 4 km, using blocks with at least 5 shared pixels.
- **Artefact check:** each map's 1 km local values correlated with the local terrain height.

## 3. Results (Spearman ρ; spreads are the 5th and 95th percentiles in mm/yr, vertical)

| | Run 2, 2015–2023 | Run 2, 2015–2020 | Local, 2015–2023 | Local, 2015–2020 |
|---|---|---|---|---|
| As is | 0.39 | −0.16 | 0.05 | 0.04 |
| Blocks 0.5 / 1 / 2 / 4 km, as is | 0.53 / 0.54 / 0.52 / 0.62 | −0.30 / −0.40 / −0.57 / −0.63 | ≈ 0 | ≈ 0 |
| Both trend-removed | **0.20** | **0.20** | 0.03 | 0.02 |
| Blocks 0.5 / 1 / 2 / 4 km, trend-removed | 0.30 / 0.25 / 0.16 / 0.20 | 0.30 / 0.27 / 0.12 / 0.13 | ≈ 0 | ≈ 0 |
| Both 1 km-local | 0.07 | 0.08 | 0.08 | 0.07 |
| Spread, trend-removed: ours vs NTU | −1.1…1.1 vs −5.1…4.2 | −1.6…1.5 vs −5.1…4.2 | −0.7…0.7 vs −8.7…7.8 | −0.9…1.1 vs −8.7…7.8 |
| Spread, 1 km-local: ours vs NTU | −0.8…0.8 vs −4.1…3.7 | −1.1…1.0 vs −4.1…3.7 | −0.6…0.6 vs −5.8…5.4 | −0.8…0.8 vs −5.8…5.4 |
| 1 km-local value vs local terrain height: ours, NTU | 0.17, 0.04 | 0.07, 0.04 | −0.04, 0.02 | −0.10, 0.02 |

The block counts in the trend-removed rows are 698, 293, 104 and 37 for run 2, and 1,193, 536, 203 and 74 for the local product.

## 4. What this shows, and what it doesn't

- **The earlier run 2 agreement (ρ 0.39, up to 0.62 on blocks) mostly came from large-scale trends.**
  - Over NTU's own period the as-is agreement turns negative.
  - Once the same plane is removed from both, both periods give the same ρ 0.20, with 0.25–0.30 on 0.5–1 km blocks.
  - So after plane removal, the two maps share a weak pattern at scales of about 0.5–1 km and larger. Aligning the period doesn't change that.
- **Small-scale agreement is near zero for every product (ρ 0.07–0.08 after the same 1 km local reference).** The local product is no worse here than run 2 referenced the same way.
- **NTU's values spread about 4–8 times wider than ours at every scale.** The cause isn't known. Possible reasons:
  - NTU's processing: sparser network, interpolation, another troposphere correction;
  - real movement our processing smooths out;
  - different time windows.
- **NTU's local values barely track terrain height (ρ 0.02–0.04),** so this check gives no sign that they are terrain artefacts. Run 2's local values track it a little (0.17 over 2015–2023).
- **Neither map is ground truth.** This comparison doesn't validate the local product and doesn't show that NTU is wrong. What the local product keeps of a known signal is measured separately by the synthetic test (`feasibility/hk_synthetic_test.py`). It keeps most of a bowl narrower than about 160 m (σ), about half at 320 m, and almost none wider than 1 km. The test starts after HyP3's processing.
