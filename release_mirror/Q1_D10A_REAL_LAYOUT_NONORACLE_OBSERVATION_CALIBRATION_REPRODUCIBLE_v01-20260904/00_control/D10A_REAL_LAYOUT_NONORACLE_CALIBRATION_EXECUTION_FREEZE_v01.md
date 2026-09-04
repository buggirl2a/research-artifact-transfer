# D10A real-layout non-oracle calibration execution freeze v01

Frozen before any synthetic encounter or abundance outcome was generated.

## Scope

- Use only the frozen 48-state F0 plot membership, final D09C A/B whole-panel assignment, public plot coordinates, sampled status, accessible forest conditions, sampled subplots, partial-effort metadata, `PLOT.MANUAL`, and `PLOT.DESIGNCD`.
- The executable must not query any species-bearing observation table and must not contain or read `SPCD`.
- Use the D04 EPSG:5070 ellipsoidal Albers implementation, origin `(0,0)`, 50-km cells, and four-neighbor adjacency. No 25/75-km analysis.
- Generate fresh synthetic species only. No real species support, encounter, abundance, cohort, R1/R2, World 0, or publication result is authorized.

## Frozen simulation design

- 72 synthetic species; collection seed `904202604`.
- One connected support per species, 60--180 sampled-domain 50-km cells.
- Each support is shared by its STRONG and PAIRED_NULL worlds.
- STRONG abundance uses stable intrinsic support geometry plus an independent smooth within-support field.
- PAIRED_NULL assigns the identical positive abundance-value multiset by an independent smooth rearrangement that does not use intrinsic support fields.
- Three observation regimes are generated with fixed truth-only parameters: O1 abundance-dependent encounter, O2 heterogeneous within-cell availability, and O3 manual-associated heterogeneity.
- Strong/null pairs share layout, support, non-abundance observation fields, and uniform random numbers. Fitted models never receive truth parameters.

## Frozen candidate models

- M0: source-fold hard detection, `p=1` for `K>0`, otherwise `p=0`.
- M1: empirical-Bayes zero-inflated beta-binomial model. A ridge-partially-pooled encounter regression is estimated only from source-fold positive histories using legal opportunity count, mean effort, partial-sampling fraction, six most frequent MANUAL shares, three most frequent DESIGNCD shares, and species offsets. Beta-binomial concentration is estimated from observed residual overdispersion. Species occupancy prevalence is estimated by zero-mixture EM with a fixed Beta(1.5,1.5) regularizer. No opposite-fold abundance is used.
- M2: M1 plus a fixed graph-Laplacian probability regularizer on four-neighbor 50-km cells. Lambda is 0.45, 30 Jacobi iterations; positive-history cells remain pinned.
- The six MANUAL and three DESIGNCD groups are selected mechanically by species-blind legitimate-opportunity frequency, with lexical tie-breaking.

## Frozen uncertainty and support evaluation

- Binary-map evaluation cut is 0.5 for every model and regime.
- Probability calibration uses ten fixed equal-width bins.
- M1/M2 uncertainty is the complete cell-level posterior probability field. Support-size intervals use 128 fixed-seed Bernoulli draws. Downstream plausible-support ensembles use 16 fixed-seed Bernoulli draws. M0 is degenerate.
- Report Brier score, clipped log loss, calibration error, expected support-size bias, recall, precision, IoU, entropy, support-size interval, and interval coverage.
- Evaluation is on cells with at least one legitimate opportunity in the opposite target fold; fitting sees source-fold histories only.

## Frozen downstream continuity audit

- AB infers support from A and uses synthetic abundance observations from B; BA reverses the roles.
- Five fresh species splits use seeds `9042101`--`9042105`, with 40% train, 40% calibration, and 20% test.
- World 0 and stable-intrinsic geometry receive the exact same support ensemble. World 0 uses only distance-to-boundary with gamma grid 0.0--3.0 by 0.2. Geometry uses distance, squared distance, openness at radii 2 and 4 and squares/interactions, and diffusion-return signatures at steps 4 and 8, with ridge 5.
- Use 32 fixed sliced-Wasserstein directions, 31 quantiles, and 90% split conformal prediction. Report latent-truth point-error gain, predictive-set diameter gain, latent-truth coverage, and observed-map coverage for all M0/M1/M2, worlds, regimes, AB/BA, and splits.

## Interpretation and terminal status

- No scientific PASS/FAIL threshold and no winner are defined.
- All candidate results must be returned. Mainline alone may freeze a model before any real-species support is read.
- Allowed successful terminal status: `CALIBRATION_COMPLETE_READY_FOR_MAINLINE_MODEL_FREEZE`.

## Benchmark provenance limitation frozen before execution

The contract cites `E2C_LATENT_OCCUPANCY_DETECTION_v0_1_20260831_REPRODUCIBLE.zip` with SHA-256 `76a38f98e8d76c60f0b0c173ac34ac999b311949b683b68c6e69461ae01d3af4`. That exact file/hash is absent locally. The available benchmark ZIP is `C:\range_paper\Q1_range_abundance\E2C_LATENT_OCCUPANCY_DETECTION_v0_1_20260831.zip`, SHA-256 `a96914712d83b7583b090177c1852fd1e7be1771c903aa51b36cfd10bdeddcf1`. Its unpacked methods are continuity reference only, never a fitted-model parameter source. This mismatch is non-blocking because it is not the F0 layout authority, and it must remain explicit in QC and the result note.
