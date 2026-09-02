# Q1 D08C1 accepted-species eligibility reproducible package v01

Status: **PASS; frozen outcome-blind census**  
Date: 2026-09-02

This package contains the frozen D08C1 accepted-species eligibility outputs, independent QC, audit workbook, exact D08B1 v02 authority inputs, D04/eligibility continuity inputs, request and Rhode Island decision, controls, and source code.

The analytical computation was not rerun during finalization. Finalization only validated existing files, copied them byte-for-byte, generated inventories/hashes, and created a deterministic ZIP.

The 15.35 GB formal FIA ZIP and extracted 71.565 GB SQLite database are not duplicated inside this delivery. Their frozen path, SHA-256, member size, and CRC-32 checks are recorded in `control/D08C1_INPUT_FREEZE_v01.md` and `outputs/Q1_D08C1_INPUT_AUDIT_v01.csv`.

Authoritative scientific tables are the UTF-8 CSV files under `outputs/`. The XLSX workbook is a human-review view, not a replacement authority.

To reproduce from the frozen local raw snapshot, review the contract and parameters, then run the builder and verifier from `code/` in the recorded environment. To recreate only the delivery package from already frozen outputs, run `code/finalize_d08c1_delivery_v01.py` from a clean target state.

No final grain, threshold, or species cohort is selected. No Little layer is merged, no external range search is performed, and no real-Q1 outcome is computed.
