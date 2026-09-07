
# D10FB9 QC v01

## Result

`PASS`

## Exact input identity

- B7 ZIP SHA-256 and relay commit: PASS.
- B8 ZIP SHA-256 `009573506cd9c11d8209e0e28b7ae7004aa8a78f41042d0136a4ae7a71e42118` and relay commit `e4dcc5294ebf2304179e21207b79006d698bbe7c`: PASS.
- D10C-A ZIP and extracted crosswalk member identity: PASS.
- Frozen national SQLite inherited SHA authority and current 71,565,119,488-byte size: PASS.
- Frozen WA PLOT/SURVEY ZIP SHA-256 values and raw-asset manifest identities: PASS.

## Identity and hierarchy checks

- S01-S24 recovered in exact order: 24/24.
- Target core identity complete: 24/24.
- Unique state-scope plots queried: 41958.
- National SQLite identities used: 41012.
- Frozen WA raw-design ZIP fallback identities used: 946.
- Unresolved identities after controlled fallback: 0.
- Level 1 resolved: 11.
- Level 2 resolved: 13.
- Unavailable: 0.
- Identity incomplete: 0.
- Main decision: `YES_24_OF_24_STRUCTURALLY_AVAILABLE`.

## Required special checks

- WA S22/S23/S24 exact target DESIGNCD/raw DESIGNCD audit: complete.
- WA 501/502 automatic mixing: 0.
- B8 Level-2 reconciliation PASS: 13/13.
- B8 discrepancies: 0.
- MANUAL hard exclusions: 0.
- SAMP_METHOD hard exclusions: 0.

## Governance zero counts

- real target-species reads: 0.
- TREE/SPCD analysis: 0.
- abundance/support access: 0.
- donor assignments: 0.
- pseudo-strata assignments: 0.
- variance calculations: 0.
- covariance calculations: 0.
- synthetic runs: 0.
- external searches: 0.
- A2 modifications: 0.
- D10F-C implementation: 0.

## Transfer controls

- Schema exactly `local_path,relative_path,role,upload_target,required,mainline_priority,size_bytes,sha256,notes`.
- Every row uses `upload_target=mirror`.
- `mainline_handoff` occurrences: 0.
- Every path starts with `release_mirror/Q1-D10FB9-v01-20260907/`.
- Duplicated transfer-name segment: 0.

## Spreadsheet verification

All eight delivered CSVs are UTF-8 flat tables with LF line endings and deterministic order. The post-package Artifact Tool verifier imports, recalculates, inspects, error-scans, and renders every CSV.
