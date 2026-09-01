# Q1 TAXON RANGE FREEZE v01

Date: 2026-09-02
Status: PASS
Scope: D08B canonical FIA taxonomy -> WCVP accepted analysis species -> native distribution -> USGS/Little layer audit.

## Frozen results

- FIA codes: 396 classified once; 370 resolve to 354 accepted WCVP analysis species.
- Mapping classes: {"ACCEPTED_INFRASPECIES_TO_PARENT_SPECIES": 8, "ACCEPTED_SPECIES": 328, "AMBIGUOUS": 5, "GENUS_OR_NON_SPECIES_AGGREGATE": 14, "HYBRID_OR_NOTHOTAXON": 2, "SYNONYM_TO_ACCEPTED_INFRASPECIES_TO_PARENT_SPECIES": 7, "SYNONYM_TO_ACCEPTED_SPECIES": 27, "UNRESOLVED": 5}.
- WCVP Level-3 rows retained: 9429.
- Species confirmed native outside USA+Canada: 171.
- USGS canonical no-review single-layer species: 262; review-required: 92.
- DRC/DBH FIA codes: 35 / 361.
- Mandatory QC: 24 PASS, 0 FAIL.

## Frozen source identity

- WCVP v16 ZIP SHA-256: d32ea2b3a85e489b14e83bcc9eae7274532e1d113753f7be290d4b2dfde573fa.
- USGS Atlas G Table 1 SHA-256: fdca3c163d856aeea7b15ec5f80e18750701a880ee8f9f4c1bd5cc076f26292b.
- Build contract: `00_control/TAXON_RANGE_BUILD_CONTRACT_v01.md`.
- Audit correction log: `00_control/TAXON_RANGE_BUILD_CORRECTION_LOG_v01.md`.

## Immutable package

- Archive directory: `C:\range_paper\10_archive\tax_v01`.
- ZIP: `Q1_TAXON_RANGE_REPRODUCIBLE_v01.zip`.
- ZIP SHA-256 is stored in the sibling `Q1_TAXON_RANGE_REPRODUCIBLE_v01.zip.sha256` sidecar. The hash cannot be embedded inside the ZIP without circularly changing the ZIP hash.
- Internal payload hashes are frozen in `package/SHA256SUMS.csv` and `package/MANIFEST.json`.

STOP. This freeze contains no FIA TREE merge or real-Q1 result and authorizes no continuation into later analysis.
