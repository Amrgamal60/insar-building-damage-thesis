---
name: next-study-hong-kong
description: After the NYC report, next work is the supervisor's deep-learning coastal study; Hong Kong + Miami-Dade (Mumbai reserve); plan in NYC plan §17
metadata:
  type: project
---

On 2026-10-10 the supervisor (after the 7 Oct brief on Mumbai/Hong Kong/Lagos/Miami) asked to download every dataset in the brief and pick a deep-learning model linking satellite data to collapse prediction in coastal cities. The user said to start it only after the NYC ML steps (real run + report) finish. Steps are in Alex/feasibility/nyc/NYC_REPLICATION_PLAN.md §17 (not part of the preregistration).

Cities (user, 2026-10-10: only the best 2 beside NYC, not all four): Hong Kong (main) + Miami-Dade (OPERA time series, folio-located unsafe-structure cases; must pass a bulk-export / ≥100 cases since 2017 check), Mumbai as reserve, Lagos dropped. Order: audit the two → Hong Kong (≈1,320 S26 + 80 S26A buildings with coordinates; first check whether monthly order snapshots since May 2023 exist to date orders) → Sentinel-1 via ASF HyP3 + MintPy → choose DL model from data shape (CNN if static maps; temporal CNN/LSTM/ConvLSTM if time series; attention only if it beats plain ConvLSTM) → same safeguards as NYC (frozen plan, spatial folds, LR/RF baselines, spatial null, decoy). Lagos is descriptive only (≈8 collapses after its 2018–2021 InSAR). Still to confirm with the supervisor: "الانهيارات الأرضية" may mean ground failure, not building failure.

**Why:** the user preferred my critique over GPT's ConvLSTM-first proposal (data and label count decide the model).
**How to apply:** don't start before the NYC report is done; then begin with step 1–3 of §17. Related: [[nyc-replication-frozen]].
