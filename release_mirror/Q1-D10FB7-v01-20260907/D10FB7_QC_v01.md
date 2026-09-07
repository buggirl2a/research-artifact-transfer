
# D10FB7 QC v01

## Result

`PASS`

## Frozen input identity

- D09C whole ZIP SHA-256: PASS.
- D10C-A whole ZIP SHA-256: PASS.
- B3 relay commit `9cd8974cf32834554d50f48bc33359daabae6cf3`: PASS.
- B5 relay commit `64b428658b4a4597e30646aa5c1fcbcbc1d3725f`: PASS.
- B6 whole ZIP SHA-256 `4822b8fa6b02bedf3f2c918883aa810fcd97931344bad000138f2f2cb5255cdb`: PASS.
- D10C-A extracted crosswalk byte identity against the ZIP member: PASS.
- Frozen national SQLite inherited SHA authority and current 71,565,119,488-byte size: PASS.

## Singleton checks

- B3 singleton rows: 24.
- Target parent recovered at exactly current `n_h=1`: 24/24.
- Identity complete: 24/24.
- Structurally available: 11/24.
- Structurally isolated: 13/24.
- One same-source-EU scope covers all 24: NO.
- Donor assignments: 0.
- Pooling weights or variance rules: 0.

## WV checks

- B5 current WV identities: 13 unique.
- D10C-A exact PLT_CN matches: 13/13.
- Frozen SQLite exact PLOT matches: 13/13.
- Source EU matches both D10C-A `original_ESTN_UNIT` and PLOT `UNITCD`: 13/13.
- P2PANEL matches D10C-A and PLOT: 13/13.
- `DESIGNCD=1`: 13/13.
- `KINDCD=2`: 13/13.
- production `QA_STATUS=1`: 13/13.
- `INTENSITY=1`: 13/13.
- Current-row exception flags: 0.
- WV local result: `NO LOCAL EXCEPTION EVIDENCE`.
- Fold-B EU3 result: `NO LOCAL STRUCTURAL RESTRICTION EVIDENCE`.

## Governance zero-count checks

- real target-species reads: 0.
- TREE table queries: 0.
- SPCD reads: 0.
- donor assignments: 0.
- variance estimates: 0.
- synthetic runs: 0.
- covariance runs: 0.
- external searches: 0.
- A2 reopening actions: 0.
- D10F-C authorization actions: 0.

## Transfer-manifest controls

- Frozen schema: exactly `local_path,relative_path,role,upload_target,required,mainline_priority,size_bytes,sha256,notes`.
- Every row `upload_target=mirror`.
- `mainline_handoff` occurrences: 0.
- Every `relative_path` starts with `release_mirror/Q1-D10FB7-v01-20260907/`.
- No duplicated `Q1-D10FB7-v01-20260907/Q1-D10FB7-v01-20260907` segment.
- Relay v0.2.2 accepts `mirror` and preserves an already fully-qualified same-transfer mirror path.

## Spreadsheet verification

CSV encoding is UTF-8, line endings are LF, every table has one header row and a stable flat-record schema. A separate Artifact Tool verifier imports and inspects every delivered CSV after generation.
