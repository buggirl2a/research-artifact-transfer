# D10E frozen execution contract v01

Frozen before any E0-E5 or Monte Carlo computation.

## Scientific boundary

This branch performs synthetic, oracle-support decomposition only. It does not read real species outcomes, modify A2, create another estimator, repair support, change D3, select a real-data domain, change the 50-km grain, change World 0 or paired-null, select species, assign a scientific PASS/HOLD/FAIL, or choose a next mainline action.

## Primary universe

- Frozen D10D D3 common A-intersection-B measurable domain: 2,757 of 3,011 cells.
- Frozen 72 synthetic species, STRONG and PAIRED_NULL worlds, AB and BA orientations.
- Frozen oracle support intersected with D3 for every state.
- Frozen five split seeds and downstream scoring.
- O1/O2/O3 are retained as labels. Corrected A2 abundance does not depend on the encounter regime, so abundance results must be numerically identical across those labels.

## States

- E0: D3 matching restricted latent reference, reproduced from D10D `D3_A0_REF`.
- E1: frozen single-realization D3 A2, reproduced from D10D `D3`.
- E2: replace the final Poisson count by its exact conditional mean while holding the frozen D10C-resume plot multiplier and all upstream quantities fixed; apply unchanged A2 and then D3 normalization.
- E3: exact full observation-process expected mass map. The audited algebra gives latent cell mass exactly on D3, so no Monte Carlo approximation is used.
- E4: arithmetic mean of normalized A2 maps across all accepted repeated observations.
- E5: arithmetic mean across repeated observations of the complete frozen downstream functional evaluated separately on each normalized map.

## Monte Carlo

- Master seed namespace: `D10E_MC_v01` combined through frozen D10A `stable_seed`.
- Start with 200 independent observation realizations.
- If pooled separation MCSE exceeds 0.25 pp or either AB/BA separation MCSE exceeds 0.50 pp, continue in batches of 200 to at most 1,000.
- Each realization redraws plot multipliers and Poisson counts. Plot multipliers are shared across the paired worlds. Count generators for paired worlds are initialized from the same realization/species/fold seed, preserving the two Poisson marginals.
- The realization-level orientation statistic is the median of the five frozen split-level STRONG-minus-PAIRED_NULL separations. The pooled statistic is the median across AB and BA. MCSE is the sample standard deviation of realization-level statistics divided by the square root of accepted realizations.
- E4 is evaluated after averaging normalized maps over all accepted realizations. E5 averages realization-level downstream statistics.

## K ladder

- K values: 1, 2, 4, 8, 16, 32.
- Use consecutive non-overlapping blocks from the accepted master Monte Carlo stream. K=1 reuses E5 realizations. For every block, average unnormalized cell masses, normalize once, and run the frozen downstream scoring.
- Report all available blocks and their numerical spread. The unequal block counts are a computational diagnostic, not a scientific threshold.

## Map recovery

Within D3 and restricted oracle support, report Hellinger, sliced-Wasserstein, Pearson cell-mass correlation, bias, relative bias, RMSE, relative RMSE, entropy bias, and concentration bias for E0-E4. Relative bias/RMSE use mean positive latent cell mass as the scale. No exclusion threshold is defined.

## Empirical uncertainty

- Unit: positive latent support cell within D3, by species, world, and orientation.
- Empirical variance is the sample variance of repeated unnormalized A2 cell masses.
- Empirical-variance 95% coverage uses each realization's mass plus or minus 1.96 times the empirical cell standard deviation.
- Empirical central-95% containment records whether latent cell mass lies between the repeated 2.5th and 97.5th percentiles.
- Frozen Poisson-style coverage uses each realization's plug-in variance `sum(count × factor^2)` and the same normal multiplier.
- Dispersion is empirical variance divided by mean plug-in Poisson variance. These are diagnostics only; no new uncertainty model is fitted.

## Information diagnostics

Report relationships without thresholds using legal target-fold plots in restricted support, plots per occupied cell, target-fold TI sum, expected total count, support size, latent concentration, target fold, and the two-panel/three-panel role parsed exactly from frozen D10C-A `ti_candidate_id`. No additional-panel estimator is entered because no extra estimator authority is frozen.

## Implementation acceptance gates

- Every authoritative outer SHA-256 and applicable internal manifest matches.
- The stochastic hierarchy is uniquely closed and matches the formula ledger.
- E0 and E1 reproduce D10D within 1e-10 for common downstream numeric fields.
- E2 and E3 expected mass equal restricted latent truth within 1e-10 relative numerical tolerance.
- Every normalized map sums to one within 1e-12 and has no mass outside D3 restricted oracle support.
- Monte Carlo seeds and realization count are recorded; convergence rules are applied without scientific tuning.
- E0-E5, decomposition, K ladder, recovery, uncertainty, information, convergence, Q1-Q11 note, code, workbook, QC, checksums, registry delta, delivery index, and Relay manifest are present.
- All output and ZIP member paths remain below 256 characters.

Only the allowed success terminal may be issued after all implementation gates pass: `ABUNDANCE_MEASUREMENT_NOISE_DECOMPOSITION_COMPLETE_READY_FOR_MAINLINE`.

