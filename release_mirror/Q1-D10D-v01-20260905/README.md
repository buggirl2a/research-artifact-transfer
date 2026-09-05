# D10D reproducible package v01

Terminal status: `ZERO_OPPORTUNITY_SOURCE_ATTRIBUTION_COMPLETE_READY_FOR_MAINLINE`

This package is a synthetic oracle-support diagnostic of zero-opportunity and measurable-domain source attribution. It does not assign a scientific PASS/HOLD/FAIL, select a real-data measurable domain, repair the frozen A2 estimator, read real species outcomes, or run real Q1.

## First-read files

- `out/result_note_v01.md`: quantitative answers to Q1-Q8 and the interpretation boundary.
- `out/attrib_summary_v01.csv`: pooled D0/D1/D2/D3 source-attribution summary.
- `out/common_v01.csv`: common downstream comparison by state, regime, and orientation.
- `out/domain_summary_v01.csv`: cell, plot, TI-weight, and effective-block-area retention.
- `out/audit_v01.xlsx`: human-readable seven-sheet audit workbook.
- `qc/validation_v01.json`: independent post-computation validation.
- `manifest/SHA256SUMS.txt`: payload hashes; by construction it excludes itself and the delivery index.

## Reproduction

On the frozen local environment, run `src/run_all.ps1`. The runner verifies all authoritative input identities, rebuilds D0/D1/D2/D3, exports and re-imports the workbook, independently validates outputs, and creates the deterministic ZIP and sidecars. It uses only the frozen local D10CR, D10C-A, D10B, and D10A packages.

STOP boundary: mainline alone decides interpretation, any real-data estimand, and any next task.
