# Mumbai and Lagos acquisition audit

Two city folders: [Mumbai](mumbai/AUDIT_REPORT.md) and [Lagos](lagos/AUDIT_REPORT.md).

**Status on 2026-10-10: acquisition blocked; source metadata audit prepared; no source dataset downloaded.** Shell networking is explicitly disabled and all 16 attempted inventory/file requests failed DNS resolution. Browser tools recovered some documentation and official historical C-1 links, but cannot save the requested binary datasets into this workspace.

Each city contains:

- `downloads/`: destination for source files; currently empty.
- `metadata/dataset_catalog.json`: documented properties with uncertainties and model-use judgments.
- `metadata/acquisition_plan.json`: sources and pending asset selections.
- `audit/dataset_audit.csv`: all requested audit columns; null size is unknown, not zero-byte data.
- `audit/download_attempts.json`: actual failed requests and reasons.
- `audit/file_content_audit.json`: empty until files are acquired.
- `audit/local_inventory_summary.json`: actual local file count and byte total.

Mumbai also has `audit/c1_year_coverage.csv`, `metadata/c1_sources.json` and a header-only `audit/first_appearance_template.csv`. No first-appearance dates have been inferred from incomplete snippets.

Run from the project root in an environment with network access:

```bash
.venv/bin/python feasibility/download_audit_cities.py --download
.venv/bin/python feasibility/download_audit_cities.py --download-extra
.venv/bin/python feasibility/download_audit_cities.py --audit-only
```

The first command fetches Mumbai Figshare v2 files for Mumbai, the incident catalog and README, all advertised files from the current Lagos Figshare version, and seven recovered C-1 PDF candidates. The second additionally attempts WSF and public GLO-30 mirror candidates. Candidate URLs and provisional city bounds still require successful retrieval and header verification. Neither command selects raw Sentinel-1 scenes, Open Buildings shards, GHSL tiles, WorldPop variants or groundwater stations. Those product selections remain outstanding and are described in the city plans.

The script validates byte sizes/MD5 when provided, PDF/TIFF/ZIP signatures, ZIP CRCs, and records SHA256. Failed responses never become source files. Existing unverified files are retained and flagged rather than overwritten. Metadata is recorded separately from source data. The static reports/catalog describe this audit date; subsequent runs write measured file audits and download logs without rewriting the original reports.

Auditor validation passed on temporary fixtures: headerless numeric CSV retained its first row; CSV null/infinity, TIFF mask/NaN and Excel null counts were correct. Actual dataset auditing remains outstanding.
