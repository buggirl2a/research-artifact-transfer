# Q1 / D10B — Oracle-Support Downstream Source-Decomposition Diagnostic v01

TASK_ID: `D10B_ORACLE_SUPPORT_DOWNSTREAM_SOURCE_DECOMPOSITION_v01`

This immutable local contract records the authoritative D10B request received on 2026-09-04. The complete source request is identified by SHA-256 `af2cdc08264b4bf4061b89dafdc5687f52d965c6b327af38fe3c8e7b98f8c4cf` (13,048 bytes).

## Purpose and boundary

D10A is complete but remains under `SCIENTIFIC_MODEL_FREEZE_HOLD`; no M0/M1/M2 model is selected or repaired here. D10B is a diagnostic-only decomposition of D10A downstream paired-null gain. It must not read the 93 real species, real supports, real abundance, or real Q1 results. It must not run D10C, form a final cohort, download FIA, or change the scientific question.

## Sole authoritative input

Use only the frozen D10A reproducible archive:

`C:\range_paper\10_archive\d10a_real_layout_nonoracle_v01\Q1_D10A_REAL_LAYOUT_NONORACLE_OBSERVATION_CALIBRATION_REPRODUCIBLE_v01.zip`

Required SHA-256:

`20e5d3ed33df6414b72a6e679d5349f3b10fe6397ce73f98b51d0bcc96033013`

Transfer identity: `Q1_D10A_REAL_LAYOUT_NONORACLE_OBSERVATION_CALIBRATION_REPRODUCIBLE_v01-20260904`; commit `5df38b433708d838f794d7d0a9fcdcac0bcccb73`.

The D10A synthetic generator and all of its identities are frozen: 72 synthetic species, exact supports, STRONG and PAIRED_NULL abundance-value pairs, O1/O2/O3 regimes, split seeds and allocations, stable intrinsic geometry features, sliced-Wasserstein distance, and 90% split-conformal construction. The current World 0 `baseline_from_info`, gamma grid 0.0–3.0 by 0.2, geometry features, and ridge alpha 5.0 are unchanged.

## Frozen layers

- L0: exact generator-known true support plus generator-known latent true abundance. No encounter history, posterior occupancy, support draws, or M0/M1/M2.
- L1: exact true support plus D10A target-fold observed abundance: B for AB and A for BA. No M0/M1/M2 support.
- L2: direct aligned reference to D10A M0/M1/M2 full observed-pipeline results. L2 is not recomputed or redefined.

For each world, regime, orientation, and split, retain geometry gain, predictive-set gain, World 0 and geometry coverage, set diameters, and errors.

Under PAIRED_NULL, report the diagnostic—not causal—decomposition:

- comparator component = L0 gain;
- abundance-observation increment = L1 gain − L0 gain;
- support-recovery increment for Mx = L2_Mx gain − L1 gain.

Also report STRONG minus PAIRED_NULL separation at L0, L1, and L2.

## Prohibitions

No real-species data; no model selection; no support or World 0 repair; no M1/M2 changes; no new occupancy model; no lambda, gamma, geometry-feature, paired-null-generator, conformal-level, or split changes; no result-conditioned tuning.

## Allowed terminal states

- `DIAGNOSTIC_COMPLETE_READY_FOR_MAINLINE_SOURCE_ATTRIBUTION`
- `INPUT_BLOCKED_D10A_WORLD_IDENTITY_FAILURE`
- `IMPLEMENTATION_BLOCKED`

There is no scientific PASS/FAIL and no model winner in D10B. On completion, STOP and return to the scientific mainline.
