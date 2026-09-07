# D10FB3 singleton provenance and WV operator equivalence audit v01

## B3-A — singleton provenance

Recovery: **PASS**. The exact D09C table yields 24 `n_h=1` block×fold cases, 22 final effective blocks, and 11 states, matching D10F-B.

Classification counts:

* `FOLD_INDUCED_SPARSE`: 24
* `SOURCE_SPARSE_OR_SPECIAL_EXCEPTION`: 0
* `UNRESOLVED_IDENTITY`: 0

Every case is an R0 `PARENT_POSTSTRATUM` identity with one source EU and one source parent poststratum. Every full-evaluation comparator exceeds one (range 2–13), and every A+B count equals that comparator. The singleton therefore arises from the frozen 2+3 whole-panel split, not from a source singleton or recovered special exception. No authority follow-up is required for this provenance classification. Region identity is not present in the required frozen rows and was left blank rather than inferred.

## B3-B — WV pooled versus separate-EU operator

Result: `NON_EQUIVALENT_PROJECT_OPERATOR`.

The selected partition is `T2_WV_A3-5_B1-2-4`. The frozen source areas are EU3 `23014.8` acres and EU4 `51962.0` acres; their exact sum is the pooled `74976.8` acres.

For fold A, the pooled coefficient is `74976.8/8 = 9372.1`. Separate-EU coefficients are `23014.8/2 = 11507.4` for EU3 and `51962.0/6 = 8660.333333333333333` for EU4. Neither equals the pooled coefficient.

For fold B, all five contributing plots are in EU4. The pooled coefficient is `74976.8/5 = 14995.36`, whereas the separate-EU coefficient is `51962.0/5 = 10392.4`. EU3 has zero fold-B plots, so a separate-EU fold-B sum has no observed EU3 contribution.

All 13 plot coefficients are non-equal under exact Fraction arithmetic. Maximum absolute difference is `4602.96` acres per plot; maximum relative difference is `0.442915977060159` under `abs(P-S)/abs(S)`.

This result states only that the frozen pooled-TI point representation is not algebraically identical to the audited separate-EU point representation. It does not alter A2 or decide how WV uncertainty should be represented.

## Governance

No estimator was modified. No covariance was implemented. No real-species outcome was accessed. No external search was performed. B3 stops here and returns to Q1 mainline.
