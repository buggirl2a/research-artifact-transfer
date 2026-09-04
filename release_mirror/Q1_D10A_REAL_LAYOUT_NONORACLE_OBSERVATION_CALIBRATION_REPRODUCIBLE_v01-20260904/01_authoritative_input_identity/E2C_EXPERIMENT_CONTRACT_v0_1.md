# E2c latent occupancy-detection observation model experiment v0.1

## Freeze status

This contract is frozen before the first formal E2c execution. Its model,
seeds, evaluation set, and PASS/FAIL thresholds must not be changed after
results are observed. A code error may be repaired only if the failed run and
the exact implementation correction are retained in the audit log; scientific
parameters and thresholds remain frozen.

## Bounded purpose

E2c is a synthetic engineering experiment. It asks whether an explicit
latent occupancy-detection observation layer removes the abundance-dependent
support leakage found in E2b while preserving the genuine stable-intrinsic
geometry signal established by E1.4 and propagated by E2a.

E2c does not estimate a real-species Q1 effect, search for more data, alter the
scientific question, or authorize E2d.

## Frozen scientific object

- Primary abundance object: population-mass allocation over 50-km cells.
- A: conditional freedom of that allocation given current occupied support.
- B: honest probabilistic prediction for wholly unseen species.
- World 0: the same candidate support as the geometry model, used only as a
  hard spatial container with a generic distance-to-boundary allocation.
- Geometry model: E1.4 stable-intrinsic R2d; no absolute geography or
  environmental covariates.
- Range/support and abundance remain jointly represented in the same cells.

## Frozen FIA sampling layout

- Source: supplied D04 five-state pack (PA, WV, VA, NC, TN).
- Grain: 50 km.
- Measurement-year window: MEASYEAR 2017-2023 inclusive.
- Eligible sampling domain: D04 `eligible_forest_plot == 1`.
- Fixed A/B plot folds supplied by D04.
- Expected filtered layout: 13,546 plots (A=6,781; B=6,765) in 266 cells.
- Accessible forest effort per plot is the sum of positive accessible-forest
  `CONDPROP_UNADJ` values for that plot; values are clipped to (0, 1].

No D04 real species abundance is analyzed. The real layout is used only as the
observation/sampling geometry for fresh synthetic species.

## Fresh paired synthetic worlds

- Generate 200 new synthetic species with collection seed 1710831.
- Generate one connected latent support per species on the fixed 50-km domain,
  with 24-90 cells, using randomized anisotropic smooth fields.
- Strong abundance is a continuous function of E1.4 stable intrinsic support
  quantities: distance to boundary, graph openness at radii 2 and 4, and an
  independent smooth within-support field.
- Paired-null abundance has exactly the same positive abundance-value
  histogram as its strong pair but is smoothly rearranged relative to support
  geometry.
- Strong and paired-null have the identical latent support.
- Abundance observations use the fixed opposite FIA fold, plot effort, common
  plot-scale multiplicative noise, and Poisson counts.

## Abundance-dependent support detection challenge

The challenge is the E2b mechanism, unchanged:

- Base per-plot support detection varies continuously from approximately 0.02
  at the support edge to 0.15 in the interior, with smooth heterogeneity.
- `logit(p_detect) = logit(p_base) + 0.9 * a`, where `a` is standardized log
  relative latent abundance within the support.
- Outside latent support, detection probability is zero.
- Strong and null pairs share the same base detection field and the same
  plot-level uniform random numbers. Only abundance arrangement changes the
  realized detection history.

The observable retention rule uses no truth: a species is retained only if
strong and null worlds each have at least six hard-detected cells in both A
and B. At least 150 species must remain or the execution FAILS for inadequate
engineering sample size.

## E2c latent occupancy-detection model

For species `i`, cell `j`, and support fold `f`:

- `z_ij` is latent binary current occupancy.
- `k_ijf` detections among `n_jf` eligible repeated FIA plots follow a
  binomial detection history conditional on `z_ij=1`; `k>0` forces `z=1`
  because false positives are absent in this audit.
- Plot/cell effort enters exactly through `n_jf`.
- Detection is explicitly abundance-linked through
  `logit(p_ij) = mu_detect + u_ij + 0.9*a_ij`, with
  `u_ij ~ Normal(0, 0.65^2)` and latent standardized abundance effect
  `a_ij ~ Normal(0,1)`.
- The primary correctly specified audit uses `mu_detect = logit(0.06)`.
- For zero histories, the occupied-cell nondetection likelihood
  `E[(1-p_ij)^n_jf]` is marginalized by fixed 31-node Gauss-Hermite
  quadrature. Neither the latent `a` field nor any soft detection intensity is
  exposed to the abundance predictor.
- Spatial support regularization is an interpretable Ising prior on the
  4-neighbor cell graph. The fixed full conditional prior log-odds are
  `alpha + rho*(2*neighbor_occupancy_fraction-1)`, with alpha=-1 and rho=4.
- Posterior inference uses 80 burn-in sweeps, then eight binary support draws
  separated by ten sweeps. Positive-detection cells are forced occupied.
- Duplicate draws are removed. If fewer than three unique draws remain,
  deterministic posterior-probability cuts at 0.35, 0.50, and 0.65 are added,
  always unioned with hard detections. Every retained support has at least six
  cells.
- Common posterior-sampler random numbers are used for a strong/null pair
  within each species and fold to isolate the observation-model effect.

The output passed downstream is only the equal-weight ensemble of plausible
binary support draws. Posterior occupancy probabilities, detection scores,
`k/n`, and latent abundance terms are diagnostic-only and are never R2d input.

## Frozen World 0 and R2d comparison

For each species, world, and orientation:

- AB uses support detections from fold A and abundance counts from fold B.
- BA uses support detections from fold B and abundance counts from fold A.
- World 0 and R2d receive exactly the same posterior support draws.
- Each training species contributes equal total weight; its weight is divided
  equally among support draws and occupied cells.
- Observed abundance is projected to each candidate support only for fitting,
  then renormalized; abundance never changes the support draw.
- World 0 learns only the generic distance-to-boundary exponent on the training
  species, using a fixed grid 0.0-3.0 by 0.1.
- R2d uses distance and distance squared, graph openness at radii 2 and 4 and
  their squares, distance-by-openness interactions, and sign-invariant
  intrinsic diffusion return signatures at steps 4 and 8. Ridge alpha is 5.
- No single eigenvector, direction label, absolute location, environmental
  variable, or soft detection field is used.

## Unseen-species evaluation and uncertainty

- Five fixed independent species splits: 930831-930835.
- Allocation: 40% train, 40% calibration, 20% test.
- Spatial loss: deterministic sliced 2-Wasserstein approximation using 32
  fixed directions and 31 fixed weighted quantiles on normalized cell centers.
- Calibration: ordinary 90% split conformal, separately for World 0 and R2d,
  using minimum distance from the observed calibration map to any support-draw
  prediction center.
- Point prediction: equal-weight mean of centers.
- Predictive set: union of equal-radius metric balls around all centers.
- Set-diameter proxy: maximum pairwise center distance plus twice the conformal
  radius. World 0 pays the same support-posterior dispersion penalty.

Primary test quantities are latent-truth point-error gain, predictive-set
diameter gain, latent-truth coverage, and observed-map coverage. All gains are
percent reductions relative to World 0.

## Frozen PASS/FAIL criteria

All criteria are evaluated across the five splits and must hold separately in
both AB and BA.

Strong world:

- median latent-truth point-error gain >5%;
- median predictive-set diameter gain >5%;
- median latent-truth coverage >=0.80;
- median observed-map coverage >=0.85;
- predictive-set diameter gain is positive in at least 4/5 splits.

Paired-null world:

- median latent-truth point-error gain <=5%;
- median predictive-set diameter gain <=5%;
- latent-truth gain >5% in no more than 1/5 splits;
- predictive-set diameter gain >5% in no more than 1/5 splits.

E2c PASS requires the retention floor and every criterion above in both
orientations. Otherwise E2c FAILS. A failure is frozen and localized before any
new correction is proposed; thresholds are not changed.

## Required diagnostics and outputs

The reproducible package must contain this contract, full standalone executed
source, parameter/seed file, input hashes, retained-species table,
replicate-level results, summary table, pass/fail JSON, support-posterior and
leakage diagnostics, useful figures, a concise result note, and the D04 input
pack or an exact embedded copy sufficient to reproduce the run.

The principal observation diagnostic compares paired strong/null hard-support
IoU with paired strong/null posterior median-support IoU and posterior
inclusion-field correlation. Improvement in that diagnostic cannot substitute
for the registered prediction/coverage PASS criteria.

