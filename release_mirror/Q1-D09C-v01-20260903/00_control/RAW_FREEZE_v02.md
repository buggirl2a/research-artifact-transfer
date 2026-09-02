# Q1 D07 RAW FREEZE v02

Generated: 2026-09-01 23:24:01 +08:00
Root: C:\range_paper
Status: PASS
Supersedes for mainline use: RAW_FREEZE_v01.md (retained unchanged as historical acquisition record)

## Audit correction
Final D07 audit found that USGS explicitly documents non-identical information in the NetCDF representation: updated Albers conical equal-area projection details and grid-point coordinates recalculated to six decimal places. Under the original D07 acquisition contract, a second representation must be retained when it contains additional information. Therefore the official NetCDF asset(s) were added without modifying or replacing any v01 raw file.

The CSV representation remains the Atlas-faithful representation with the original three-decimal grid-point coordinates and country/state/province/county assignment fields. The NetCDF representation is frozen as an additional representation, not declared the primary scientific representation. Representation choice remains for the Q1 scientific mainline.

## Formal raw closure
FIA: Entire FIADB SQLite Database; FIADB version reference FIADB_1.9.4.00.
USGS/Little: DOI 10.5066/P9FPD80E; official CSV bundle plus 1 NetCDF asset(s).
Formal raw file count: 3
Formal raw total bytes: 15368466996

All v01 raw files were rehashed before v02 creation and matched their v01 recorded SHA-256 values.
All v02 formal raw files have SHA-256 recorded in sha256_raw_v02.txt.
ZIP central-directory checks and/or NetCDF signature checks: PASS.

## Control files for v02
- C:\range_paper\00_control\raw_manifest_v02.csv
- C:\range_paper\00_control\sha256_raw_v02.txt
- C:\range_paper\00_control\D07_raw_archive_inventory_v02.csv
- C:\range_paper\00_control\D07_USGS_NETCDF_ADDENDUM_v01.csv
- C:\range_paper\00_control\D07_USGS_WRAPPER_ARCHIVE_INVENTORY_v06.csv
- C:\range_paper\00_control\doc_manifest.csv

## Immutable raw-layer rule
All formal files already present in 02_raw remain unchanged. The NetCDF asset(s) are additive official raw files extracted from the previously retained official ScienceBase attached-files wrapper. From this v02 closure onward, 02_raw is the frozen raw input layer. Later extraction/transformation must go to 99_tmp or 04_derived.

## D07 return
PASS
Raw snapshot v02 is ready for Q1 scientific-mainline audit.
STOP. Do not start eligibility census.
