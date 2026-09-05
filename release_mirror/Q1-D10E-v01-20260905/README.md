# D10E reproducible package v01

Terminal status: `ABUNDANCE_MEASUREMENT_NOISE_DECOMPOSITION_COMPLETE_READY_FOR_MAINLINE`

This package decomposes abundance-measurement noise under the frozen D3 common measurable domain using synthetic oracle worlds. It separates the expected measurement operator, normalization nonlinearity, finite-realization downstream effect, and current-realization deviation. It does not assign a scientific PASS/HOLD/FAIL, modify the frozen A2 estimator, fit a new uncertainty model, perform support recovery, read real species outcomes, or run real Q1.

## First-read files

- `out/Q1_D10E_RESULT_NOTE_v01.md`: quantitative answers and interpretation boundary.
- `out/state_summary_v01.csv`: E0-E5 state comparison.
- `out/source_decomp_v01.csv`: four-component decomposition.
- `out/k_ladder_summary_v01.csv`: repeated-survey averaging ladder.
- `out/audit_v01.xlsx`: human-readable twelve-sheet audit workbook.
- `qc/independent_validation_v01.json`: independent 30-check validation.
- `manifest/SHA256SUMS.txt`: payload hashes; it excludes itself and the delivery index to avoid circular hashes.

## Reproduction

On the frozen local environment, run `src/run_all.ps1`. It verifies authoritative inputs, rebuilds all E0-E5 outputs, runs independent checks, creates figures and the workbook, and emits a deterministic ZIP plus sidecars.

STOP boundary: mainline alone decides interpretation, any scientific disposition, and any next task.
