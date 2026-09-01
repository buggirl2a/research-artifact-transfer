# Q1 D08A SOURCE FREEZE v02

Generated: 2026-09-02 04:14:18 +08:00
Status: PASS
Root: C:\range_paper
Supersedes for D08A source-closure use: D08A_SOURCE_FREEZE_v01.md; v01 is retained unchanged for audit history.

This is an additive source freeze. RAW_FREEZE_v02 is not modified.

## Frozen WCVP identity
- C:\range_paper\02_raw\WCVP\wcvp.zip
- bytes: 88179649
- SHA-256: d32ea2b3a85e489b14e83bcc9eae7274532e1d113753f7be290d4b2dfde573fa
- WCVP Version 16; extracted 04/06/2026
- CC BY 3.0
- DOI 10.34885/egs6-cp24

## WCVP standard ZIP sufficiency
PASS. Correct pipe-delimited header audit confirms all essential relations for later Q1_TAXON_RANGE_MASTER. DwC-A is not required and is not authorized/downloaded.

## Fixed downstream taxonomy order
FIA original name -> WCVP accepted name -> analysis species -> accepted analysis-species native distribution -> map back to unique FIA TREE records.

## Natural-range rule
Only native WCVP/POWO distribution defines natural range. Introduced/naturalized/invasive distribution does not enter natural range.

## USGS/Little
Atlas G Table 1 is frozen as the official original-source-name <-> currently-accepted-name bridge. Universal species/subspecies layer containment remains UNKNOWN; use row-specific Notes and no mechanical union.

## FIA DBH/DRC
Core source rule is closed: 1.0-4.9 inch DBH/DRC = microplot small-tree domain; >=5.0 inch DBH/DRC = large-tree/subplot diameter state. DRC-taxon inclusion remains a scientific-mainline decision.

## Geography
Preserve WCVP TDWG/WGSRPD Level-3 botanical area codes/names plus introduced, extinct, and location_doubtful flags.

## v02 evidence outputs
- C:\range_paper\05_qc\tax\D08A_WCVP_SOURCE_AUDIT_v02.csv
- C:\range_paper\05_qc\tax\D08A_WCVP_FIELD_MAP_v02.csv
- C:\range_paper\05_qc\tax\D08A_WCVP_ZIP_CORE_AUDIT_v02.csv
- C:\range_paper\05_qc\tax\D08A_USGS_NAME_SOURCE_AUDIT_v02.csv
- C:\range_paper\05_qc\tax\D08A_DRC_EVIDENCE_v02.csv
- C:\range_paper\05_qc\tax\D08A_GEO_SEMANTICS_v02.csv
- C:\range_paper\05_qc\tax\D08A_SOURCE_EVIDENCE_v02.csv
- C:\range_paper\03_doc\WCVP\D08A_POWO_OFFICIAL_WEB_EVIDENCE_v02.md
- C:\range_paper\00_control\D08A_CORRECTION_LOG_v02.md

## Non-blocking unresolved/mainline-only items
- UNKNOWN: universal Little species-level versus infraspecific-layer containment rule.
- MAINLINE_DECISION_REQUIRED: DRC taxa inclusion in final scientific analysis.

STOP. Source layer only.
