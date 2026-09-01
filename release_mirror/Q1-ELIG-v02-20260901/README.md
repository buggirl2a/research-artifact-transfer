# Q1 outcome-blind eligibility census v0.2

This directory contains the executable bounded eligibility-census branch. It uses only `RAW_FREEZE_v02`, the frozen local FIA/USGS documentation, the restored original D04 grid/split source, and the three governing request/addendum files. It does not perform real-Q1 effect analysis or make a final grain, threshold, or species-cohort decision.

- `parameters.json` freezes the candidate domain, lineage, A/B, grid, tree, threshold-frontier, geometry, taxonomy, and trace-sample rules.
- `prepare_inputs.py` rehashes the three formal raw archives and extracts only the required FIADB database and USGS individual-species CSV/NetCDF members.
- `eligibility_census.py` creates the full audit tables without fitting or evaluating any real-Q1 effect.
- `verify_outputs.py` independently checks required gates, table completeness, arithmetic, grid nesting, A/B leakage/balance, USGS equivalence, frontier completeness/monotonicity, trace samples, and the prohibited-outcome audit.
- `nc3_reader.py` is a minimal read-only NetCDF classic (CDF-1) reader used only for the frozen CSV/NetCDF semantic comparison.
- `make_figures.py`, `build_audit_workbook.mjs`, and `capture_environment.py` generate audit-only figures, the consolidated XLSX, previews, and runtime records.
- `package_release.py` builds a deterministic-member ZIP, a payload manifest, and independent ZIP verification files.
- `run_all.ps1` is the single entry point for the complete bounded branch.
- `D04_extract_FIA_pilot.py` is the exact restored authoritative D04 source, byte-for-byte.
- `contracts/` contains exact copies of the three governing request/addendum documents.

The FIADB extraction requires about 72 GB of temporary disk space. Authoritative CSV results are written to `C:\range_paper\05_qc\elig_v02`; the consolidated XLSX is an audit convenience and does not replace them. Temporary extracted members are written to `C:\range_paper\99_tmp\elig_v02`, and the release ZIP to `C:\range_paper\10_archive\elig_v02`.

Run `run_all.ps1` only in the already frozen `C:\range_paper` workspace. Inspect `NO_Q1_OUTCOME_AUDIT.json`, `REPRODUCIBILITY_CHECKS.csv`, the package manifest, and ZIP verification record. The workflow ends after packaging and must not be extended into real-species Q1 analysis. Hard-detected cells remain observation diagnostics, not latent-support truth.
