# D10C abundance-estimator authority-gate execution freeze v01

Frozen on 2026-09-05 (Asia/Shanghai) before any D10C synthetic observation, A0/A1/A2 estimate, recovery metric, leakage metric, or downstream audit was computed.

## Input identity requirements

The D10A, D10B, and D09C ZIP identities must equal the hashes in the D10C contract. The D09C internal `SHA256SUMS.csv` must close without a missing member, byte-size mismatch, or hash mismatch.

## Exact estimator-authority requirements

A successful gate requires all of the following to be available in the frozen packages:

1. the selected 48-state AB/BA whole-panel partitions;
2. every fold-specific effective design block and its authoritative TI expansion weight;
3. a complete nationwide plot-level crosswalk joining each F0 `PLT_CN` to exactly one selected fold-specific effective design block, including the WV merged-domain rule;
4. a frozen definition of how condition/subplot partial effort enters the real abundance response or plot contribution whenever required by the intended estimator;
5. sufficient identifiers to join the crosswalk to the frozen D10A F0 layout without fuzzy matching, geographic imputation, or inferred state-average weights.

The authority gate is mechanical and outcome-blind. If any item is absent, the terminal state is `INPUT_BLOCKED_ABUNDANCE_ESTIMATOR_AUTHORITY_FAILURE`; no synthetic calibration is permitted.

## Preflight evidence frozen before results

- D09C freezes `fold_specific_ti_expansion_acres_per_plot = effective block population area / actual fold sample count` and does not reuse full-evaluation EXPNS.
- `Q1_D09C_T2_FINAL_FOLD_SPECIFIC_TI_DESIGN_v02.csv` is block-level and contains no plot identifier.
- D10A `Q1_D10A_REAL_F0_OPPORTUNITY_LAYOUT_v01.csv` contains plot and cell identifiers but no stratum, estimation-unit, assignment, or effective-block identifier.
- The D09C predecessor's published nationwide ledgers are aggregate: the panel/subpanel/year ledger has stratum identifiers without individual plot identifiers, while the lineage audit has plot-visit lists without design-block identifiers.
- The only embedded raw plot/assignment design ZIPs are for CA, OR, and WA; no equivalent embedded raw design crosswalk is present for the other 45 states.
- D09C does not freeze a nationwide partial-effort-to-abundance-response contribution rule.

Therefore the required nationwide exact plot-to-weight join cannot be constructed from frozen-package authority. State-average weighting, inverse cell sample size, and use of local un-packaged FIA tables are explicitly not substituted.

Terminal state frozen for this run: `INPUT_BLOCKED_ABUNDANCE_ESTIMATOR_AUTHORITY_FAILURE`.
