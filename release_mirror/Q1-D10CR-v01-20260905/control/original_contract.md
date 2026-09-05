# Q1 / D10C — FIA Design-Based Abundance Measurement Calibration v01

TASK_ID: `D10C_FIA_DESIGN_BASED_ABUNDANCE_MEASUREMENT_CALIBRATION_v01`

This immutable local contract records the authoritative D10C request received on 2026-09-05. The complete source request is identified by SHA-256 `d3fba3e4a350466ce5138172c61fff814e0883cd7e24bd8eb269ac2bac0844dd` (17,597 bytes).

## Sole scientific purpose

Under exact oracle support, calibrate the intended FIA fold-specific design-based abundance measurement chain from latent 50-km population mass through FIA-like plot observations to design-estimated cell population mass and normalized allocation. Compare A0 latent truth, A1 broken raw-count reference, and A2 frozen FIA design-based estimator, followed only by the bounded frozen downstream preservation audit.

## Authoritative inputs

- D10A release ZIP SHA-256 `20e5d3ed33df6414b72a6e679d5349f3b10fe6397ce73f98b51d0bcc96033013`.
- D10B release ZIP SHA-256 `cb041fca5897f31c8ea0bf2a3b29a262a5c83ef44bdfda9a37a0394cfc7cafeb`.
- D09C final design ZIP SHA-256 `07cb461121c71ef46990fea3e0cf9d8f139fd873234b9f57910ff10c7c33752f`.

D10A supplies only the frozen 72-species synthetic worlds, oracle supports, STRONG/PAIRED_NULL latent maps, splits, 50-km grid, F0 layout, and AB/BA panels. D10A observed-abundance arrays and raw-count aggregation are not A2. D10B is diagnostic continuity only. D09C must authoritatively define the exact intended fold-specific TI estimator.

## Mandatory authority gate

Before any synthetic calibration result is generated, the accepted D09C package must contain enough information to implement the intended fold-specific design-based estimator exactly. It is forbidden to replace missing authority with raw plot/tree counts, positive-plot counts, simple means, inverse plots per cell, state-average weights, ad hoc normalization, or any convenience estimator.

If the exact estimator cannot be attached to the actual F0 plot layout from the frozen packages, terminate `INPUT_BLOCKED_ABUNDANCE_ESTIMATOR_AUTHORITY_FAILURE`. No A0/A1/A2 experiment may be run after that finding.

## Fixed successful-run objects

If and only if the authority gate passes: freeze a deterministic species-total rule independent of geometry, F0 intensity, panels, state, MANUAL, and DESIGNCD; generate plot observations satisfying G1–G5; evaluate A0/A1/A2 cell- and map-level recovery, sampling-intensity leakage, and the bounded oracle downstream audit with unchanged World 0, geometry, paired null, splits, conformal level, metric, grain, and AB/BA assignment.

## Prohibitions

No real 93-species outcomes, TREE.SPCD, real abundance/support maps, M0/M1/M2 refitting, support recovery/repair, D10D, final cohort, real Q1, grain/panel/World 0/geometry/paired-null/split changes, network acquisition, or FIA download.

## Allowed terminal states

- `ABUNDANCE_CALIBRATION_COMPLETE_READY_FOR_MAINLINE_FREEZE`
- `INPUT_BLOCKED_ABUNDANCE_ESTIMATOR_AUTHORITY_FAILURE`
- `INPUT_BLOCKED_FROZEN_DESIGN_IDENTITY_FAILURE`
- `IMPLEMENTATION_BLOCKED`

There is no scientific PASS/FAIL and no abundance-model winner. Stop immediately at the applicable terminal state.
