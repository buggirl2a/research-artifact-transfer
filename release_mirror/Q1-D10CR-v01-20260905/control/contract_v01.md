# D10C resume experiment contract v01

Task: `D10C_FIA_DESIGN_BASED_ABUNDANCE_MEASUREMENT_CALIBRATION_RESUME_v01`

Frozen before A2 generation or result inspection on 2026-09-05.

## Scope

The experiment uses the exact D10A 72-species synthetic worlds, STRONG and PAIRED_NULL pairing, 50-km grid, latent allocations, F0 layout, AB/BA orientation, five split seeds, oracle support, World 0, R1 geometry representation, conformal level, and D10B scoring code. It does not read `TREE.SPCD`, any real-species outcome, M0/M1/M2 support output for estimation, or real Q1 data. It performs no support recovery or repair.

## Frozen layers

- A0 is the exact D10A latent allocation.
- A1 is the exact released D10A count generator and raw cell aggregation. It remains `BROKEN_REFERENCE_ONLY`. For cell-mass error only, its normalized allocation is multiplied by the fixed total below so that scale does not dominate the diagnostic.
- A2 is the D10C-A design estimator. No alternative estimator is evaluated.

## Synthetic total and record representation

- Every species has fixed total mass `T_i = 100,000,000` trees in both worlds. This constant is independent of support, geometry, F0 intensity, state, panel, manual, and design code.
- Every A2 synthetic record is a live established tree equivalent with `STATUSCD=1`, `DIA=5.0`, subplot tally basis, and `TPA_UNADJ=6.018046` trees per acre. A 5-inch record is below all numeric macroplot breakpoints in the frozen F0 crosswalk, so `ADJ_FACTOR_SUBP` is the unique basis-matched adjustment.
- D10A `partial_sampling_effort` affects observation opportunity only. It is not an A2 estimator multiplier.
- The D10A lognormal plot heterogeneity (`abundance_plot_log_sd=0.25`) and its released `count_micro` seed are retained.
- A2 Poisson draws use the released D10A `counts` seed for each species, world, and fold.

## A2 observation generator and estimator

For species `i`, world `w`, fold `f`, cell `x`, and legal plot `j`, define

`d_j = TI_jf * ADJ_FACTOR_SUBP_j * effort_j * micro_ij`.

For a cell with positive design exposure `D_x = sum_j d_j`, generate

`K_ij ~ Poisson((M_i(x)/D_x) * effort_j * micro_ij / TPA_UNADJ)`.

The plot contribution used by A2 is

`K_ij * TPA_UNADJ * ADJ_FACTOR_SUBP_j`,

and the cell estimate is

`Mhat_if(x) = sum_j TI_jf * K_ij * TPA_UNADJ * ADJ_FACTOR_SUBP_j`.

Therefore `E[Mhat_if(x) | F0, micro] = M_i(x)` whenever `D_x>0`. `EXPNS`, condition proportions, plot-count divisors, state-average weights, inverse plots-per-cell corrections, and inverse partial-effort corrections are absent.

Cells with `D_x=0` have no target-fold observation and remain estimated as zero. They are flagged as structural zero-exposure cells and retained in full-map metrics. No interpolation, support restriction, renormalization of truth, or other repair is allowed.

## Frozen metrics

- Cell metrics: signed bias, relative bias where true mass is positive, RMSE, Pearson correlation as a diagnostic, analytic Poisson variance, 95% normal-interval coverage, and true-mass quintile summaries.
- Map metrics: Hellinger distance; the exact D10A 32-direction, 31-quantile sliced-Wasserstein distance; centroid displacement in km; entropy bias; concentration (`sum p^2`) bias; and total-mass relative error.
- Leakage metrics: correlations and pooled linear slopes of signed error, absolute error, normalized-allocation residual, and estimated allocation against plot count, summed effort, partial fraction, panel, state, manual, design code, and final block summaries. Design variables are audit-only and never repair A2.
- Downstream metrics and splits are the exact D10B oracle-support implementation. A0 and A1 must reproduce released D10B L0 and L1 before A2 is interpreted.

## Completion and terminal criteria

No scientific PASS/FAIL threshold is defined. Performance cannot change this contract.

`ABUNDANCE_CALIBRATION_COMPLETE_READY_FOR_MAINLINE_FREEZE` requires:

1. all five frozen package hashes match;
2. the D10A regenerated manifest matches exactly;
3. D10C-A crosswalk C1-C9 and its 5,752 block-fold aggregate checks pass;
4. every legal F0 plot maps uniquely to crosswalk authority;
5. A1 downstream reconstruction reproduces D10B L1 within numeric tolerance and A0 reproduces L0;
6. all required result tables, diagnostics, code, figures, hashes, transfer manifest, registry delta, and deterministic validation are present;
7. all absolute delivery paths and ZIP member paths are shorter than 256 characters;
8. no prohibited real-species, support-recovery, or real-Q1 operation occurs.

Identity failure, unresolved estimator authority, or implementation failure uses only the terminal statuses authorized by the resume contract. Scientific behavior is reported to mainline without selecting A2 or declaring a model winner.

