# D10E observation stochastic hierarchy v01

Task: `D10E_POSITIVE_OPPORTUNITY_ABUNDANCE_MEASUREMENT_NOISE_DECOMPOSITION_v01`

Status: hierarchy uniquely reconstructed from frozen D10A, D10C-resume, D10C-A, and D10D artifacts before any E0-E5 experiment was run.

## Authoritative path from latent truth to A2

The frozen ecological object consists of a species support mask and a normalized cell allocation for each STRONG or PAIRED_NULL world. The FIA F0 plot layout, partial-effort values, D09C A/B fold, D10C-A adjustment factor, fold-specific TI, 50-km cell assignment, and total synthetic species mass are fixed design quantities.

For species `i`, target fold `f`, plot `j`, and cell `x`, D10C-resume draws a plot multiplier

`U_ifj = exp(Z_ifj)`, where `Z_ifj ~ Normal(0, 0.25^2)`.

The same realized `U_ifj` is shared by STRONG and PAIRED_NULL for a species and fold. It is independent across the frozen species/fold/plot streams defined by `stable_seed(collection_seed, species, fold, "count_micro")`.

For a positive-opportunity cell,

`E_if(x) = sum_j TI_fj * ADJ_j * effort_j * U_ifj`

and the terminal tree count is conditionally independent across plots:

`C_iwfj | truth, layout, U ~ Poisson(lambda_iwfj)`

with

`lambda_iwfj = [T_i * p_iw(x) / E_if(x)] * effort_j * U_ifj / TPA_UNADJ`.

The frozen A2 cell mass is

`Mhat_iwf(x) = sum_j C_iwfj * TI_fj * ADJ_j * TPA_UNADJ`.

There is no encounter/detection draw, environmental predictor, smoothing term, or additional random quantity on the corrected A2 abundance path. O1/O2/O3 generate separate encounter histories for support calibration in D10A; D10E uses oracle support, so those random fields and uniform encounter draws do not enter A2 and are not redrawn.

## Exact conditional-mean identity

For every positive-opportunity cell,

`E[Mhat_iwf(x) | truth, layout, U] = T_i * p_iw(x)`.

This follows because the sum of `lambda_iwfj * TI_fj * ADJ_j * TPA_UNADJ` over plots in the cell equals the numerator times `E_if(x) / E_if(x)`. D10D D3 contains only cells with positive opportunity in both folds. Therefore:

- E2, which removes only the terminal Poisson draw while holding the frozen plot multipliers fixed, equals restricted latent truth exactly before normalization.
- E3, which also averages over the plot multipliers, has the same exact expected mass map. Monte Carlo is not required for E3.
- E0, E2, and E3 must be identical after the frozen D3 restriction and normalization, up to numerical tolerance.

This identity is an implementation expectation, not a scientific acceptance threshold.

## Repeated-observation semantics

E4, E5, the K ladder, and empirical uncertainty redraw both observation-stage components: plot multipliers and terminal Poisson counts. The support, latent abundance, plot layout, design weights, A/B assignment, D3 mask, World identity, oracle geometry, downstream split seeds, and World 0 definition remain fixed.

Repeated STRONG and PAIRED_NULL observations share each species/fold plot-multiplier stream. They also use matched count-stream seeds, initialized separately with the same seed for the paired worlds. This preserves each Poisson marginal while reducing Monte Carlo noise in the frozen paired comparison. The current E1 realization retains its original D10C-resume seeds and is never replaced by a repeated-diagnostic draw.

## Authority trail

- D10C-resume `src/build.py`, especially the frozen A2 generator block defining `plot_micro`, cell exposure, Poisson rate, terminal count, A2 factor, and analytic Poisson variance.
- D10A `04_code/build_d10a_real_layout_nonoracle_v01.py`, defining `stable_seed`, frozen ecological support/abundance generation, and the separate encounter-process hierarchy.
- D10A parameters, defining collection seed `904202604` and plot log standard deviation `0.25`.
- D10C-A formula ledger, defining A2 as the sum of `TI × count × TPA_UNADJ × ADJ_FACTOR_SUBP` with normalization only after cell-mass construction.
- D10D, defining D3, oracle support/geometry, synthetic identities, downstream scoring, frozen splits, World 0, and paired-null comparison.

Conclusion: the hierarchy is uniquely closed. The authority-failure terminal is not triggered.

