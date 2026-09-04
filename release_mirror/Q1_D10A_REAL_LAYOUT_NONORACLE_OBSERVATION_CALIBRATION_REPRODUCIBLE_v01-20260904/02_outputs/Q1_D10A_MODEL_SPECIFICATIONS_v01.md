# D10A model specifications v01

Frozen specification: `D10A_REAL_LAYOUT_NONORACLE_CALIBRATION_EXECUTION_FREEZE_v01.md`.

## Layout

The experiment uses 3,011 fixed 50-km cells and the frozen D09C whole-panel AB assignment. Legal opportunity is a sampled plot with nonblank MANUAL and DESIGNCD, at least one accessible forest condition, and at least one sampled subplot linked to an accessible condition. Partial effort equals clipped accessible-forest condition proportion times the fraction of up to four relevant sampled subplots. The six mechanically selected MANUAL groups are `9.0; 7.0; 8.0; 9.2; 9.1; 6.0`. The three DESIGNCD groups are `1; 501; 502`.

## M0

Hard detection. A source-fold cell has occupancy probability one when K is positive and zero otherwise. It is a failure baseline and has degenerate uncertainty.

## M1

M1 is an empirical-Bayes zero-inflated beta-binomial encounter model. Conditional on latent occupancy, K among N legal plot opportunities follows a beta-binomial distribution with cell mean encounter probability and a shared overdispersion concentration. Cell mean encounter probability uses source-fold mean effort, partial-sampling fraction, six MANUAL shares, three DESIGNCD shares, and a partially pooled synthetic-species intercept. Coefficients are estimated from positive histories with ridge penalties 1.0 for observation covariates and 4.0 for species offsets. Residual beta-binomial rho is estimated from observed positive-history dispersion and clipped to [0.02, 0.35]. Species occupancy prevalence is estimated by zero-mixture EM with Beta(1.5, 1.5) regularization. Generator parameters and opposite-fold abundance are absent from every fitted design matrix.

For K=0, posterior occupancy is `pi * P_BB(K=0|Z=1) / (1-pi + pi*P_BB(K=0|Z=1))`; K>0 is pinned occupied. Cells without source-fold opportunities retain the estimated species prevalence.

## M2

M2 applies a fixed four-neighbor graph-Laplacian regularizer to M1 logits. It solves the Jacobi fixed-point update with lambda 0.45 for 30 iterations and pins positive-history cells. No environmental, atlas, external occurrence, or abundance input is used.

## Uncertainty and evaluation

The complete cell posterior is the uncertainty representation. Expected support size is the sum of posterior probabilities. Fixed-seed Bernoulli support draws provide 5th/50th/95th size summaries (128 draws) and the downstream plausible-support ensemble (16 draws). Binary diagnostics use the pre-frozen 0.5 cut; calibration uses 10 equal-width bins.

## Downstream continuity audit

AB uses A support histories and B synthetic abundance; BA reverses them. World 0 and stable-intrinsic geometry receive identical support draws. Allocation fitting, stable intrinsic features, sliced-Wasserstein loss, and 90% split-conformal construction follow the historical E2c object, with fresh D10A species splits. Posterior encounter probability is diagnostic-only and is never an abundance predictor.

No model winner or scientific PASS/FAIL rule is defined in D10A.
