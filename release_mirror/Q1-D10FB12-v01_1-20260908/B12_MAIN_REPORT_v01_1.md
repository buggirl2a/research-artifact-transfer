# B12 v01_1 work covariance-qualification closure

This package is additive qualification evidence over accepted B12 v01. It preserves the frozen design and accepted scalar/domain-profile results, closes the full-covariance firewall/noise/spectral gaps, and stops before D10F-C.

## Executive disposition

All 1,893,464 planned covariance prediction objects were Stage-P sealed before any held-out reference was opened. Stage S independently reconstructed and verified 1,893,464 object digests with 0 failures; each actual prediction bundle was verified before opening FULL5_LIMITED_REFERENCE.

Exact symmetric eigensolvers replaced the invalid domain all-ones start. Across all scored target/prediction covariance matrices, material PSD failures = 0; no clipping, ridge, nearest-PD, or shrinkage was applied.

## Answers to the ten qualification questions

**Q1 — Does B9 compatibility translate into covariance transportability?** Only partially. The accepted scalar/profile evidence is unchanged (overall median domain TV 0.442; median generic |log variance ratio| 1.070). At full covariance level the median relative Frobenius discrepancies are 0.770 for domain and 0.999 for generic joint; median fixed-projection |log variance ratios are 0.154 and 1.406. These are continuous qualification results, not pass/fail thresholds.

**Q2 — Level1 versus Level2 after reference noise?** Level1 median domain-covariance transport/noise ratio is 0.923 across 3511 estimable targets, versus 1.012 across 156 for Level2. Generic-joint ratios are 1.066 and 0.854, respectively. Reference weakness remains explicit.

**Q3 — Does Level2 pool df compensate for cross-EU mismatch?** No empirical compensation is demonstrated: median pool df is 2477 for Level2 versus 170 for Level1, while Level2 retains larger domain/profile and covariance transport distance.

**Q4 — Does Level2 spatial mismatch persist at 100/200 km?** Level2 median domain TV changes from 0.932 at 50 km to 0.855 at 100 km and 0.669 at 200 km; domain-covariance relative Frobenius medians are 0.983, 0.970, and 0.944. Coarsening is diagnostic only and does not define a new Q1 grain.

**Q5 — Is Level1 spatially reasonable but abundance transport heterogeneous?** Level1 is materially closer spatially than Level2 (50-km median TV 0.424 versus 0.932), yet the accepted Level1 median generic scalar |log ratio| remains 1.067, and generic-joint covariance discrepancy remains heterogeneous.

**Q6 — Species-specific transport?** All 1,865,280 pseudo-target×SPCD combinations retain their degeneracy class. 34,840 informative joint objects were scored; the per-target median species-joint relative Frobenius median is 1.004. The protected scalar evidence remains 55,923 target-positive cases, including 48,723 positive/positive cases (accepted median |log ratio| ≈1.698) and 7,200 target-positive/pool-zero cases. The all-402 result is not generalized to the strict 101 Q1 candidates.

**Q7 — Mismatch beyond internal covariance noise?** Among estimable references, median transport/noise ratios are 0.926 for domain, 1.061 for generic joint, and 0.739 for the per-target species-joint summaries. Raw transport and noise are both retained; no universal threshold was invented.

**Q8 — Candidate versus fixed incompatible NC1?** Among metric-specific comparable cases, candidate-better fractions are 0.536 for scalar (n=3920), 1.000 for domain profile, 0.940 for domain covariance, and 0.620 for generic joint. The control remains the predeclared different-state incompatible pool, not random geography. NC2 is also preserved: median uncentered/centered variance ratio 1.814, with 93.8% of finite cases >1.

**Q9 — Descriptive identities?** Non-exact target/pool set relations occur for MANUAL=3127, regional MANUAL=2036, SAMP_METHOD_CD=2186, and MEASYEAR=3682 targets. Route, state/EU, pool df, target df, domain overlap, and group-size imbalance are retained beside each relation. The patterns remain confounded descriptive evidence and do not justify changing B9 filters.

**Q10 — Work recommendation.** Keep unchanged D10F-C on HOLD. The repaired evidence warrants a separately authorized, narrower methodological investigation of whether abundance residual process and absolute domain allocation can be qualified without transporting the entire joint covariance wholesale. This is a recommendation only; no factorized estimator was implemented or selected.

## Fixed-projection interpretation boundary

Fixed random ±1 projections summarize anonymous aggregate variance directions, while relative Frobenius and domain-profile metrics preserve absolute cell locations. Their different numerical scales are not directly interchangeable: projection agreement cannot override absolute spatial covariance mismatch. This distinction is especially important for Level2 and remains visible at all three diagnostic grains.

## Actual 24 FULL5_LIMITED_REFERENCE

All 24 cases were retained (Level1=11, Level2=13). Among 16 positive generic full5 references, the median |log variance ratio| is 0.862. Full5 n ranges 2–13; it is direct but weak evidence, never truth, tuning input, filter input, or an A/B correction target.

## Firewall and self-audit

- Cache file and logical digests matched B12 v01; `NEW_TREE_SOURCE_SCAN_ROWS = 0`.
- Target-member pool leak = 0.
- Old membership/generic/species Stage-P artifacts were freshly rehashed and matched.
- Negative-index floor-division tests passed for 100/200-km parent grids.
- Planned/sealed/verified/failed objects = 1,893,464/1,893,464/1,893,464/0.
- No support analysis, Q1 calculation, B9 filter modification, covariance factorization, or D10F-C execution occurred.

## Status discipline

- FROZEN: A/B split, A2 point-estimator semantics, B9 compatibility routes, 50-km primary grain.
- ACCEPTED EVIDENCE: B11 algebra and protected B12 v01 scalar/domain-profile results.
- B12 EMPIRICAL QUALIFICATION EVIDENCE: corrected covariance sealing, split-half noise, spectral/PSD, coarse diagnostics, NC1 extensions, actual-24 comparisons.
- HYPOTHESIS / DESIGN CANDIDATE: future separation of abundance residual and domain-allocation processes.
- OPEN: mainline scientific disposition and any separately authorized next experiment.

## STOP boundary

Return this exact package to Q1 mainline. Do not continue automatically into D10F-C, method development, support recovery, or real Q1.
