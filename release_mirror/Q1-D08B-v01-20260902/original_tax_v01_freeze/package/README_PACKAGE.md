# Q1 D08B reproducible package v01

Status: PASS. Canonical result files are under `outputs/`; the audit workbook is a rendering of the UTF-8 CSVs.

Run from the frozen `C:\range_paper` project root with the bundled workspace Python and Node runtimes:

1. `code/build_taxon_range_master_v01.py`
2. `code/build_taxon_range_audit_xlsx_v01.mjs`
3. `code/verify_taxon_range_audit_xlsx_v01.mjs`

The 88 MB WCVP raw ZIP is not duplicated in this transfer package; its required absolute identity and SHA-256 are frozen in the control/QC files. Atlas Table 1 and the 396-code input tables are included. No external data search is part of reproduction.

Mainline must review `outputs/Q1_TAXON_RANGE_UNRESOLVED_v01.csv` and `outputs/Q1_USGS_LAYER_RECONSTRUCTION_REVIEW_v01.csv`. This package contains no real-Q1 analysis and must not be interpreted as a final species selection.
