# Q1 D10E result note v01

Terminal status: `ABUNDANCE_MEASUREMENT_NOISE_DECOMPOSITION_COMPLETE_READY_FOR_MAINLINE`

This is a synthetic oracle-support decomposition on the frozen D10D D3 domain. It assigns no scientific PASS/HOLD/FAIL and chooses no abundance model, uncertainty model, real-data domain, or next mainline action. Corrected A2 abundance is independent of O1/O2/O3; those labels are retained and numerically identical.

## Q1 — Terminal count randomness

E2 separation was 11.231 pp versus E0 11.231 pp. Removing the terminal Poisson draw restored the same positive direction because the audited conditional-mean A2 mass equals latent cell mass on every D3 cell. The maximum relative cell-mass identity error was 1.608e-15.

## Q2 — Full observation-process expectation

E3 separation was 11.231 pp. Averaging the complete observation process also reproduced E0 exactly by the frozen A2 expectation identity; no Monte Carlo approximation was needed for E3.

## Q3 — Expected-map recovery

E3 equals restricted latent truth at cell level. Its Hellinger and sliced-Wasserstein errors are zero up to numerical precision, cell-mass correlation is one, and normalized bias/RMSE are zero up to numerical precision. E4 reports the finite Monte Carlo estimate of the mean normalized map separately.

## Q4 — Normalization nonlinearity

The pooled E4-minus-E3 separation component was 0.017 pp. AB and BA components were 0.027 and 0.007 pp. This is reported without a materiality threshold.

## Q5 — Finite-realization downstream nonlinearity/noise

The pooled E5-minus-E4 component was -30.757 pp. AB and BA components were -24.557 and -36.958 pp.

## Q6 — Frozen current realization

E1 separation was -22.147 pp versus E5 mean -19.509 pp, a deviation of -2.637 pp. Orientation-specific z positions and empirical tail fractions are in `current_deviation_v01.csv`.

## Q7 — Repeated-survey ladder

Mean separation across ladder blocks was K=1: -19.509 pp, K=2: -6.593 pp, K=4: -1.682 pp, K=8: 3.515 pp, K=16: 6.438 pp, K=32: 9.265 pp. The table reports map recovery, gains, separation, orientation difference, and coverage for every non-overlapping block. This does not imply repeat surveys are available for real Q1.

## Q8 — AB versus BA information

Median legal target-fold plots in D3 support were AB 3234.5 and BA 2117.0; median plots per occupied cell were 30.449 and 20.219; median Kish plot-weight information was 2604.5 and 1681.7. Full descriptive correlations and exact two-panel/three-panel roles are retained. No causal or exclusion threshold is assigned.

## Q9 — Empirical uncertainty versus Poisson-style intervals

Mean empirical-variance normal-interval coverage was 0.9498; mean frozen Poisson plug-in interval coverage was 0.7032; the median empirical-to-Poisson variance ratio was 0.9923. Central empirical interval containment and current E1 interval coverage are also reported. No new uncertainty model was fitted.

## Q10 — Systematic expected-operator distortion

The E3-minus-E0 pooled separation component was 0.000e+00 pp. The expected A2 operator is exactly unbiased on the positive-opportunity D3 mass map under this frozen synthetic generator. This statement is limited to the audited synthetic design.

## Q11 — Mainline options

The package separates expected-operator, normalization, finite-realization downstream, and current-realization components. It does not choose among uncertainty propagation around A2, revision of the measurement operator, or continued diagnostic HOLD.

Optional panel extension: `NOT_ENTERED — ADDITIONAL PANEL ESTIMATOR AUTHORITY NOT FROZEN`.

STOP: no uncertainty model, abundance-estimator repair, support recovery, real species, final cohort, real World 0, or real Q1 was run.
