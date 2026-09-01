# Q1 taxonomy–native-range freeze v02 (D08B.1)

Date: 2026-09-02  
Status: PASS  
Supersedes for downstream use: D08B v01, which remains immutable and retained for audit.

## Frozen results

- FIA code map: 396 rows, 396 unique codes, original FIA names preserved.
- Ordinary analysis mapping: 377 FIA codes -> 361 WCVP Accepted non-nothotaxon Species.
- Mainline taxonomy correction: 11/11 cases applied exactly.
- Ordinary WCVP Level-3 evidence: 9,648 rows.
- Accepted-hybrid audit: FIA 143 `Pinus × kohae Frankis`, four Level-3 rows retained audit-only.
- USGS/Little bridge: 250 canonical no-review single-layer species; 47 explicit `NOT_APPLICABLE_CONUS_NONNATIVE`; 64 review-required species.
- Cross-stage diagnostic: 123 rows; all 92 v01 review species represented; all seven prior exact/nonzero v01-unresolved cases explicitly accounted.
- Mandatory build QC: 31 PASS, 0 FAIL.
- Independent audit: 25 PASS, 0 FAIL.

## Frozen rules

- Contract: `00_control/D08B1_TAXONOMY_USGS_BRIDGE_CONTRACT_v02.md`.
- Input freeze: `00_control/D08B1_INPUT_FREEZE_v02.md`.
- Correction log: `00_control/D08B1_CORRECTION_LOG_v02.md`.
- WCVP identity: v16 ZIP SHA-256 `d32ea2b3a85e489b14e83bcc9eae7274532e1d113753f7be290d4b2dfde573fa`.
- Atlas G Table 1 SHA-256 `fdca3c163d856aeea7b15ec5f80e18750701a880ee8f9f4c1bd5cc076f26292b`.
- Eligibility diagnostic `USGS_RANGE_AUDIT.csv` SHA-256 `bdc8a43411f648ab72c4d294f846d0688e436dcc035817cbc1de593e87c28312`.

## Immutable package convention

The final reproducible ZIP is stored in `10_archive/tax_v02/`; its SHA-256 is stored in the sibling `.zip.sha256` sidecar to avoid circular self-hashing. Internal payload hashes are recorded in the package manifest and checksum table.

## STOP boundary

D08C, FIA TREE merge, Little layer union/reconstruction, new external range search, final cohort selection, and real Q1 remain on HOLD.
