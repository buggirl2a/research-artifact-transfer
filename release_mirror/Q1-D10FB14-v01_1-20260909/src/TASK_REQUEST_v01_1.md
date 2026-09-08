# `Q1_D10F_B14_v01_1_WORK_OBSERVED_STATE_ALIGNED_MIXTURE_STRESS_CORRECTION`

## 0. Task identity

Task:

`Q1_D10F_B14_v01_1_WORK_OBSERVED_STATE_ALIGNED_MIXTURE_STRESS_CORRECTION`

Short ID:

`D10F-B14 v01_1`

Task class:

`WORK_TARGETED_DERIVED_CORRECTION`

This is a **targeted correction to B14 scientific interpretation**, not a new estimator and not a rerun of B14.

Primary question:

> Given only the information actually observed in an actual singleton plot—principally whether species `y=0` or `y>0`—what empirical stress distribution is supported by pseudo-singleton data?

The correction must distinguish:

1. **incidence of hidden-positive failure**, and
2. **severity conditional on that failure having occurred**.

B14 v01 correctly estimated (2), but incorrectly used it as if failure incidence were 100% for every actual observed zero.

---

# 1. Mainline correction statement — HARD

The B14 v01 implementation followed its contract correctly.

The mainline contract itself was over-conservative.

Therefore:

> Do NOT describe B14 v01 as a coding failure, computational failure, invalid artifact, or governance violation.

B14 v01 remains:

`ACCEPTED EMPIRICAL STRESS EVIDENCE`

The scientific disposition:

`MATERIAL_SINGLETON_UNCERTAINTY_REMAINS`

is **not adopted by mainline**, because it was based on a failure-conditioned outer envelope.

The v01_1 task corrects only this inferential step.

---

# 2. Exact parent B14

Use:

`C:\range_paper\05_qc\d10fb14_v01_work_singleton_uncertainty_materiality_stress\Q1_D10F_B14_v01.zip`

Expected SHA-256:

`01be93dee2184a44ca89f72016d459cdf0792038d6d19d1536aafe4535371208`

Accepted mirror evidence:

commit

`d19ae55793587fa29ec9c675d0d26bca418e4741`

Accepted B14 calibration seal SHA-256:

`99ee459e4640c29ac96549d6de8973783102aae6ae2d0b9724dd15be4818f27c`

Do NOT modify, overwrite, regenerate, or replace B14 v01.

---

# 3. Other protected upstream identities

Retain exactly the accepted identities used by B14 v01:

### FIA substrate

SHA-256:

`1dbd8cf3fdb9fdbd25945ed70af64e1c739ec78f10f24ec4866128c38d5d946e`

### D10CA

SHA-256:

`c8f73406f7f192b8f124add3cb0ded7ea65474e8d72d752e37dc557a08588865`

### B12 v01_1

SHA-256:

`d009bf50225ca3c2f483e08fe17f22312f93c9a28f36786abae8729fde3a21ab`

### B13

SHA-256:

`c3898021cfe71ae0ea7b307be3907c8598dc1d1744f04e37d5ee0fc9d74807d9`

### Q1 cohort projection

SHA-256:

`70d34c6905a9d76675943ae03182feae719340d159ca6b69b68b9b9d089f227e`

### Singleton materiality audit

SHA-256:

`e85da191519ac8ed033c46ac78257c1c7e515976fd87a0d99511093bd0d8e007`

### B12 read-only cache

SHA-256:

`0daf80d098546d61aecd8e75701f5174d9f6fd4452ce4a1b257651d45c9d2953`

No national TREE rescan.

Expected:

`NEW_TREE_SOURCE_SCAN_ROWS = 0`

---

# 4. Frozen facts from B14 v01

Do not recompute unless lightweight identity verification requires it.

Accepted:

* scoreable pseudo targets = 4,640
* direct species = 97
* pseudo event universe = 26,138,299
* materialized target-positive events = 1,288,936
* implicit target-zero exact-zero events = 24,849,363
* selected-y-zero / target-positive events = 1,193,386
* actual singleton cases = 24
* AB actual singleton cases = 2
* BA actual singleton cases = 22
* actual positive singleton point exposure remains localized to *Abies procera*
* observed maximum omission TV = 0.0126727477

Accepted failure-conditioned severity:

For

`selected y=0 AND target stratum positive`

overall normalized-TV:

* median ≈ 0.00420333
* p90 ≈ 0.0406629
* p95 ≈ 0.0793958
* max = 1

This severity result is valid.

Do NOT discard it.

---

# 5. Core inferential correction

For an actual singleton with `y=0`, the observed information is:

`SELECTED_Y_ZERO`

It is NOT:

`SELECTED_Y_ZERO_AND_TARGET_STRATUM_POSITIVE`

Therefore the primary empirical analogue must contain both:

### State Z0

selected plot y=0
and full multi-plot pseudo target stratum also has zero species mass.

Stress = exact zero.

### State Z+

selected plot y=0
but full multi-plot pseudo target stratum has positive species mass.

This is the hidden-positive miss state.

Stress = the B14 v01 pseudo-singleton perturbation.

The primary empirical stress distribution is therefore:

> **the observed-zero mixture of Z0 + Z+**, not Z+ alone.

---

# 6. Primary quantities

For every predeclared design matching group `g`, estimate directly from pseudo data:

### Hidden-positive incidence

`h_g = N(Z+ | selected_y=0, g) / N(selected_y=0, g)`

Report this as an **empirical transport frequency**, not a biological truth or formal detection probability.

### Conditional failure severity

Distribution:

`TV | Z+, selected_y=0, g`

This should reproduce B14 v01 failure-conditioned severity.

### Observed-state mixture stress

Distribution:

`TV | selected_y=0, g`

which contains:

* exact zeros from Z0;
* observed B14 perturbations from Z+.

This is the primary v01_1 stress object.

---

# 7. Also correct the actual positive observation case

B14 v01 used the zero-selected calibration even for actual species/cases where `selected y>0`.

This must not continue.

Predeclare a second empirical state:

`SELECTED_Y_POSITIVE`

For actual singleton × species with observed `y>0`, calibrate from pseudo events where the retained pseudo-singleton plot also has `y>0`.

Estimate:

`TV | selected_y>0, design group`

Do NOT use the hidden-positive zero-selected distribution for a positive actual observation.

The currently known positive actual case must be handled by this positive-observation calibration.

---

# 8. No actual24 outcome leakage into calibration design

Before reading actual24 species outcomes, freeze:

* zero-observation mixture definition;
* positive-observation definition;
* matching hierarchy;
* weighting rule;
* summary metrics;
* fallback rules.

The actual result may determine whether a case uses the `Y_ZERO` or `Y_POSITIVE` frozen calibration, but must not change how either calibration was constructed.

Create:

`B14_V01_1_OBSERVED_STATE_CALIBRATION_SEAL.json`

before case-specific actual24 outcome application.

---

# 9. Matching hierarchy

Primary design matching hierarchy:

1. same fold + same B9 route + same TI band;
2. same fold + same TI band;
3. same TI band;
4. all eligible pseudo targets.

Retain:

* `LT_P95`
* `P95_TO_LT_P99`
* `GE_P99`

using the already frozen full-5752 TI thresholds.

Do not tune bands.

---

# 10. Reference strength / parent-n diagnostic

Because hidden-positive incidence may depend on how much reference information a pseudo stratum contains, report as a **secondary diagnostic**:

* target `n_g`;
* accepted B12 reference-strength band.

Do not automatically add them as mandatory matching dimensions if doing so destroys support.

First report whether hidden-positive rate changes materially across these strata.

If clearly heterogeneous, return it to mainline rather than inventing a new matching model.

---

# 11. Important weighting correction

The scientific unit is the **pseudo target stratum**, not merely the raw retained-plot event.

Therefore primary calibration must use:

> `TARGET_EQUAL_THEN_PLOT_EQUAL`

Meaning:

* each eligible pseudo target receives equal total weight within a matching group;
* within a target, its possible retained plots each receive weight `1/n_g`.

This corresponds to:

> choose a pseudo stratum, then choose one of its plots as the hypothetical singleton.

Also reproduce B14 v01's:

`EVENT_EQUAL`

weighting as a secondary sensitivity.

Do NOT silently replace one with the other.

This comparison is required because B14 v01 event-level quantiles weight larger-n targets more heavily.

---

# 12. Hidden-positive incidence must be explicit

For every zero-observation calibration group report:

* number of pseudo targets;
* weighted selected-y-zero opportunities;
* weighted Z0 mass;
* weighted Z+ mass;
* empirical hidden-positive frequency `h_g`;
* conditional severity mean/median/p90/p95/max;
* mixture stress mean/median/p90/p95/p99/max.

The report must make visually obvious the difference between:

> **How often failure occurs**

and

> **How bad it is when it occurs.**

---

# 13. Do not misuse the full pseudo-event p95

B14 v01 already showed that across the entire pseudo event universe:

* ≈95.07% of normalized-TV events are exact zero;
* global p95 is zero;
* high-TI all-event p95 is also zero.

These are useful clues but are not themselves sufficient to close the actual24 issue.

v01_1 must condition on the actually observed state and design match.

---

# 14. Actual-zero stress tiers

For actual `y=0`, use:

### `MIX_OBSERVED`

actual observed point mass = zero.

### `MIX_MEAN`

empirical mean of:

`TV | selected_y=0, matched design`

### `MIX_P95`

empirical p95 of:

`TV | selected_y=0, matched design`

### `FAILURE_CONDITIONAL_P95`

retain B14 v01's:

`TV | selected_y=0, target_positive`

as a **conditional severity diagnostic only**.

### `EMPIRICAL_MAX`

retain only as an extreme outer-bound diagnostic.

`FAILURE_CONDITIONAL_P95` and `EMPIRICAL_MAX` must NOT be the primary actual24 materiality envelope.

---

# 15. Actual-positive stress tiers

For actual `y>0`:

### `POS_OBSERVED`

the actual point estimate.

### `POS_MEAN`

empirical mean:

`TV | selected_y>0, matched design`

### `POS_P95`

empirical p95:

`TV | selected_y>0, matched design`

### `POS_MAX`

empirical maximum, outer diagnostic only.

Do not borrow `Y_ZERO` stress.

---

# 16. Multiple singleton aggregation — correct the B14 v01 overreach

B14 v01 used:

`SUM_OF_INDIVIDUAL_P95_NO_CANCELLATION`

and capped at TV=1.

This may remain as:

`EXTREME_OUTER_NO_CANCELLATION_ENVELOPE`

but it is NOT the primary materiality statistic.

Do NOT again conclude cohort-wide materiality merely because 22 marginal conditional p95 values sum to ≥1.

---

# 17. Primary multiple-case summaries

Without assuming independence, report for each species and direction:

### A. Maximum individual mixture p95

`max_i MIX_P95_i`

### B. Sum of marginal mixture means

`Σ_i E(TV_i | observed state, design_i)`

Label:

`MARGINAL_MEAN_TRIANGLE_UPPER_SUM`

Because combined perturbation TV is bounded above by the sum of individual TVs.

This does NOT require assuming cancellation.

### C. Expected hidden-positive count analogue

For actual zero cases:

`Σ_i h_i`

Label:

`EMPIRICAL_MARGINAL_EXPECTED_HIDDEN_POSITIVE_COUNT`

This is an empirical-transport diagnostic.

It is not an integer prediction and not a formal probability guarantee.

### D. Extreme B14-v01 outer envelope

Retain for comparison only.

---

# 18. No independence assumption

Do NOT assume the 24 singleton errors are independent.

Do NOT multiply `(1-h_i)` across cases as a primary result.

Do NOT generate a binomial number of hidden positives.

Do NOT construct Monte Carlo joint draws unless separately authorized by mainline.

Marginal empirical transport is sufficient for this correction.

---

# 19. Optional dependence-free probability bound

Only if scientifically useful and trivial to compute, Work may report a clearly labeled union upper bound:

`P(any hidden-positive) <= Σ h_i`

capped at1.

It must be labeled:

`MARGINAL_UNION_OUTER_BOUND`

Do not interpret it as estimated probability.

This is optional.

---

# 20. Compare with A/B fold discrepancy

For each direct97 species retain the already accepted:

`TV(A,B)`

Compare against:

* max individual mixture p95;
* marginal mean triangle upper sum.

Report continuous ratios when denominator >0.

Do NOT compare A/B against:

`SUM_OF_FAILURE_CONDITIONAL_P95`

as the primary result.

That was the over-conservative B14 v01 comparison.

---

# 21. Preserve the useful B14 failure result

v01_1 must explicitly retain this conclusion:

> If a singleton zero is in fact a hidden-positive miss, the conditional severity tail can be material.

The correction must NOT turn into:

> “B14 was pessimistic, therefore singleton is harmless.”

That conclusion is not authorized.

The question is whether incidence × severity supports broad materiality in actual24.

---

# 22. Primary scientific questions

The main report must answer:

### Q1

Among pseudo cases with a selected plot `y=0`, how often is the full stratum actually positive?

### Q2

How does hidden-positive incidence vary by fold, B9 route, TI band, reference strength and target n?

### Q3

Conditional on hidden-positive failure, how severe is the perturbation?

### Q4

After mixing true-zero and hidden-positive cases, what is the empirical stress distribution corresponding to the information actually observed in an actual singleton zero?

### Q5

Does the mixture p95 remain zero or small for the design groups matching actual24?

### Q6

Does high TI increase failure incidence, failure severity, neither, or both?

### Q7

What changes under target-equal versus legacy event-equal weighting?

### Q8

For the actual positive singleton observation, what does the correct `selected_y>0` calibration show?

### Q9

How many hidden-positive cases are suggested at the marginal empirical-frequency level across AB and BA?

### Q10

What is the sum of marginal mean TV stress across actual singleton cases?

### Q11

How does that compare with ordinary A/B fold discrepancy?

### Q12

Does the B14 v01 conclusion of cohort-wide materiality survive after conditioning only on information actually observed?

### Q13

Is the remaining problem:

* a nonmaterial tail candidate;
* localized species sensitivity;
* still materially concerning;
* or unresolved because pseudo→actual transport is insufficient?

### Q14

Is new singleton covariance methodology actually necessary now?

---

# 23. No arbitrary scientific threshold

Do NOT invent:

* hidden-positive rate <5% = safe;
* mixture p95 <1% = safe;
* mean stress <10% of A/B = PASS.

Report continuous evidence.

Mainline decides the subgate.

---

# 24. Interpretation statuses

Work may recommend, but not authorize:

### `NONMATERIAL_TAIL_CANDIDATE`

### `LOCALIZED_SPECIES_LEVEL_SENSITIVITY`

### `MATERIAL_SINGLETON_UNCERTAINTY_REMAINS`

### `UNRESOLVED_MIXTURE_TRANSPORT`

The recommendation must be based on the observed-state mixture, not the failure-conditioned p95 envelope.

Final singleton subgate remains mainline authority.

---

# 25. Strong governance rule: do not turn this into B15

This task must NOT automatically develop:

* new covariance estimator;
* GVCF;
* hierarchical covariance;
* detection model;
* abundance model;
* replicate generator;
* ecological context model;
* support model.

If mixture transport remains unresolved:

> return `UNRESOLVED_MIXTURE_TRANSPORT`.

Do not solve it by task expansion.

---

# 26. Context/extremeness audit remains conditional

Do NOT launch:

`Q1_SINGLETON_CONTEXT_AND_EXTREMENESS_AUDIT`

inside this task.

It becomes relevant only if v01_1 shows hidden-positive incidence or mixture stress remains materially heterogeneous and additional design/ecological covariates could plausibly resolve that heterogeneity.

Return that as a recommendation only.

---

# 27. Work-efficiency rules — HARD

This task is expected to be much lighter than B14 v01.

Reuse:

* B14 pseudo event parquet;
* B14 summaries;
* B12 cache only where exact group denominators are required.

Do NOT regenerate the 26,138,299-event universe unless absolutely necessary.

Do NOT rerun B13.

Do NOT rescan TREE.

Do NOT extract the 2-GB substrate SQLite merely for procedural symmetry if accepted identities already suffice.

---

# 28. Expensive-run rule

Before any computation expected to exceed 20 minutes, determine whether it is actually necessary for the correction.

If not necessary:

> do not run it.

If a full scientific calculation fails for numerical implementation reasons:

* diagnose;
* allow at most one corrected full rerun.

A second expensive rerun requires STOP and mainline review.

---

# 29. New-evidence scope review

If an early result makes the answer clear, optional later diagnostics may be skipped.

Examples:

* observed-state mixture is overwhelmingly zero and stable across predeclared design groups;
* or conversely, mixture stress remains clearly broad/material even without failure conditioning.

Document early-stop reasoning.

Do not continue merely because optional tables were originally listed.

---

# 30. No output-driven recalibration

Actual24 outcomes may select frozen `Y_ZERO` versus `Y_POSITIVE` calibration.

They may NOT alter:

* matching hierarchy;
* TI bands;
* weighting;
* mixture definition;
* fallback hierarchy;
* quantile choices.

---

# 31. Required outputs

At minimum:

`B14_V01_1_MAIN_REPORT.md`

`B14_V01_1_OBSERVED_STATE_CALIBRATION_SEAL.json`

`B14_V01_1_ZERO_STATE_MIXTURE_SUMMARY.csv`

`B14_V01_1_POSITIVE_STATE_STRESS_SUMMARY.csv`

`B14_V01_1_HIDDEN_POSITIVE_INCIDENCE.csv`

`B14_V01_1_FAILURE_CONDITIONAL_SEVERITY.csv`

`B14_V01_1_TARGET_EQUAL_VS_EVENT_EQUAL.csv`

`B14_V01_1_ACTUAL24_OBSERVED_STATE_APPLICATION.parquet`

`B14_V01_1_DIRECT97_MATERIALITY_SUMMARY.csv`

`B14_V01_1_AB_VS_BA_SUMMARY.csv`

`B14_V01_1_ABIES_PROCERA_CASE.csv`

`B14_V01_1_STRESS_VS_AB_FOLD_DISCREPANCY.csv`

`B14_V01_1_DISPOSITION_MATRIX.csv`

`B14_V01_1_PROVENANCE.csv`

`B14_V01_1_INVARIANT_QC.csv`

`B14_V01_1_FIREWALL_QC.csv`

`B14_V01_1_RUN_METADATA.json`

`SHA256SUMS.csv`

`TRANSFER_MANIFEST_v01.csv`

plus required source/config/log.

---

# 32. Required disposition matrix

Rows:

* B14 v01 parent validity
* observed singleton point exposure
* selected-zero hidden-positive incidence
* failure-conditioned severity
* observed-zero mixture stress
* selected-positive stress
* high-TI incidence
* high-TI severity
* target-equal weighting
* event-equal sensitivity
* AB two-case aggregate
* BA twenty-two-case aggregate
* *Abies procera*
* direct97 cohort
* need for further covariance modeling

Columns:

* evidence
* estimand
* conditioning
* result
* interpretation
* limitation
* status
* next action

---

# 33. Invariant/QC requirements

Verify:

* parent B14 ZIP exact SHA;
* parent B14 seal exact SHA;
* pseudo target identity = 4,640;
* direct97 = 97;
* actual24 = 24;
* zero-state denominator includes both Z0 and Z+;
* Z+ count reproduces B14 v01 `1,193,386` under legacy event representation before weighting;
* target-zero cases contribute exact zero stress;
* selected-positive and selected-zero calibrations never mixed;
* TARGET_EQUAL_THEN_PLOT_EQUAL weights sum correctly within target;
* EVENT_EQUAL reproduces parent B14 legacy summaries where applicable;
* no support;
* no Q1;
* no TREE rescan;
* no new estimator;
* no species exclusion.

---

# 34. Provenance status

Use:

### FROZEN

A/B, A2, B9 route, 50-km primary grain.

### ACCEPTED EVIDENCE

B11/B12/B13.

### ACCEPTED EMPIRICAL STRESS EVIDENCE

B14 v01 parent experiment.

### B14 v01_1 TARGETED CORRECTION EVIDENCE

current task.

### OPEN

final singleton subgate.

Do not rewrite B14 v01 history.

---

# 35. Packaging

Output directory:

`C:\range_paper\05_qc\d10fb14_v01_1_work_observed_state_mixture_correction\`

Final artifact:

`Q1_D10F_B14_v01_1.zip`

Relay name:

`Q1-D10FB14-v01_1-20260909`

Use:

`upload_target=mirror`

Do not introduce `mainline_handoff`.

---

# 36. Completion state

Allowed:

`B14_V01_1_MIXTURE_CORRECTION_COMPLETE`

or:

`B14_V01_1_STOPPED_FOR_MAINLINE_REVIEW`

Do NOT state:

* `D10F-C PASS`
* `SINGLETON GATE PASS`
* `COVARIANCE SOLVED`
* `Q1 PASS`

Final decision belongs to mainline.

---

# 37. STOP conditions

STOP if:

* any canonical hash fails;
* zero-state mixture denominator cannot be reconstructed exactly;
* target-equal weighting cannot be defined unambiguously;
* selected-positive calibration cannot be isolated;
* actual outcomes alter calibration definitions;
* new distributional/covariance model becomes necessary;
* national TREE rescan becomes necessary;
* support/Q1 data would be required;
* task starts expanding beyond this conditioning correction;
* a second expensive scientific rerun would be necessary.

Return evidence rather than improvising.

---

# 38. Final STOP

After the targeted correction is complete:

> **STOP and return to Q1 mainline.**

Do not automatically start:

* B15;
* GVCF;
* context/extremeness audit;
* D10F-C;
* support work;
* real Q1.
