# D10C resume result note v01

Terminal status: `ABUNDANCE_CALIBRATION_COMPLETE_READY_FOR_MAINLINE_FREEZE`

This is evidence for mainline judgment, not a scientific PASS/FAIL or estimator selection. Oracle support was used throughout. No real species, support recovery, M0/M1/M2 refit, D10D, or real Q1 was run.

## Q1. Cell mass and normalized geography recovery

A2 median Hellinger=0.1329, median sliced-Wasserstein=4.09 km; cell and total-mass distributions are in recovery_metrics_v01.csv. The realized target-fold frames contain 98 zero-opportunity cells for AB (B target fold) and 156 for BA (A target fold); these cells were not repaired and their true mass remains in full-map error.

## Q2. Improvement over A1

Across all species, worlds, and orientations, median Hellinger distance changed from 0.2995 (A1) to 0.1329 (A2), and median sliced-Wasserstein distance changed from 26.20 km to 4.09 km. A1 remains a diagnostic scale-aligned broken reference only.

## Q3. Sampling-intensity leakage

The largest absolute pooled within-species correlation between A2 normalized-allocation residual and the four numeric intensity/effort variables was 0.2079; full state/panel/manual/design/block diagnostics are retained. Signed bias, absolute error, normalized residual, state, panel, manual, design, and final-block group summaries are reported without using them to repair A2.

## Q4. STRONG versus PAIRED_NULL direction

Median STRONG-minus-PAIRED_NULL downstream geometry-gain separation across regimes and orientations was 6.054 percentage points for A0/L0, -127.889 for A1/L1, and -26.285 for A2.

## Q5. PAIRED_NULL behavior

The complete PAIRED_NULL geometry gains, predictive-set gains, and coverage values for A0, A1, and A2 are in common_compare_v01.csv and downstream_v01.csv. No closeness threshold was introduced.

## Q6. AB/BA consistency

orientation_v01.csv reports AB and BA medians and BA-minus-AB differences for abundance recovery and downstream separation. No orientation threshold was introduced.

## Q7. Evidence of remaining limitations

The package exposes structural zero-opportunity support cells, Poisson interval coverage, full recovery distributions, and all leakage diagnostics for mainline. It does not classify these facts as PASS, HOLD, FAIL, or a bounded limitation.

## Q8. Sufficiency for mainline freeze review

The frozen identity, estimator implementation, A0/A1 reproduction, A2 recovery, leakage, downstream comparison, and deterministic package checks are complete. Mainline alone decides whether to freeze the abundance-measurement branch before any support-recovery work.
