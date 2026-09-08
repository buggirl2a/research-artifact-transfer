---

# `Q1_D10F_B14_v01_WORK_SINGLETON_UNCERTAINTY_MATERIALITY_STRESS_AUDIT`

## 0. Role

You are the Q1 Work line.

Task:

`Q1_D10F_B14_v01_WORK_SINGLETON_UNCERTAINTY_MATERIALITY_STRESS_AUDIT`

Short ID:

`D10F-B14 v01`

Task class:

`WORK_EMPIRICAL_MATERIALITY_STRESS_AUDIT`

Purpose:

> **Determine whether uncertainty associated with the 24 A/B-fold singleton strata can materially perturb the abundance measurement object relevant to Q1 under predeclared, outcome-independent, empirically grounded stress conditions.**

This task is specifically designed to decide whether further singleton covariance-method development is scientifically necessary.

It is NOT:

* a new covariance estimator;
* B15;
* GVCF implementation;
* hierarchical covariance modeling;
* D10F-C;
* support recovery;
* real Q1;
* a search for a favorable result.

---

# 1. Mainline question

Current accepted evidence shows:

1. singleton strata are structurally rare;
2. observed Q1 A2 point-mass exposure is extremely small;
3. whole-covariance transport is not production-qualified;
4. no simple covariance component has yet earned production qualification.

The remaining question is therefore:

> **Could sampling uncertainty from these rare, high-TI singleton strata nevertheless perturb the abundance map enough that the unresolved covariance problem remains scientifically material?**

If not:

> further singleton covariance refinement is not justified.

If yes:

> mainline may reopen narrower method development.

---

# 2. Governing scientific principle

Hard rule:

> **Validity first, sufficiency second.**

Do not accept an invalid uncertainty construction merely because its downstream impact is small.

But equally:

> **Do not require exact singleton covariance recovery if a scientifically conservative uncertainty envelope demonstrates that remaining uncertainty cannot materially alter the abundance inference object.**

The task must protect against both:

* standards erosion;
* methodological perfectionism.

---

# 3. Critical governance principle

The task contract is an execution discipline, not an untouchable scientific truth.

If new evidence obtained during B14 proves that an optional later phase has no remaining decision value:

> STOP that optional phase.

Do NOT continue merely because it appeared in the original contract.

Conversely, if early evidence shows singleton uncertainty clearly remains potentially material:

> STOP and report that result.

Do not keep adding models in an attempt to rescue the singleton problem.

---

# 4. Accepted canonical evidence

## A. FIA substrate

`C:\range_paper\10_archive\q1_fia_substrate_v01_1\Q1_FIA_SUBSTRATE_v01_1.zip`

SHA-256:

`1dbd8cf3fdb9fdbd25945ed70af64e1c739ec78f10f24ec4866128c38d5d946e`

Protected identities:

* F0 plots = 338,619
* block×fold = 5,752
* singleton strata = 24
* A = 135,513
* B = 203,106
* A/B plot overlap = 0

---

## B. Frozen A2

`C:\range_paper\10_archive\d10ca\D10CA_v01.zip`

SHA-256:

`c8f73406f7f192b8f124add3cb0ded7ea65474e8d72d752e37dc557a08588865`

Frozen:

`TPA_UNADJ × basis-matched ADJ_FACTOR × fold-specific TI`

TI expansion exactly once.

---

## C. B12 v01_1

`C:\range_paper\10_archive\d10fb12_v01_1\Q1_D10F_B12_v01_1.zip`

SHA-256:

`d009bf50225ca3c2f483e08fe17f22312f93c9a28f36786abae8729fde3a21ab`

Status:

`ACCEPTED EMPIRICAL QUALIFICATION EVIDENCE`

---

## D. B13

`C:\range_paper\10_archive\d10fb13_v01\Q1_D10F_B13_v01.zip`

SHA-256:

`c3898021cfe71ae0ea7b307be3907c8598dc1d1744f04e37d5ee0fc9d74807d9`

Status:

`ACCEPTED EMPIRICAL DIAGNOSTIC EVIDENCE`

Important accepted result:

* whole covariance not production-qualified;
* total scale materially challenged;
* between-cell allocation/mean scatter materially challenged;
* W / unit-trace / offdiag / location components unresolved;
* D10F-C remains HOLD.

Do NOT rerun B13.

---

## E. Q1 cohort projection

`C:\range_paper\10_archive\q1_b12_q1_cohort_projection_v01\Q1_B12_Q1_COHORT_PROJECTION_v01.zip`

SHA-256:

`70d34c6905a9d76675943ae03182feae719340d159ca6b69b68b9b9d089f227e`

Primary clean species scope:

`97 direct single-SPCD Q1 species`

---

## F. Singleton materiality audit

Canonical:

`C:\range_paper\10_archive\q1_singleton_materiality_v01\Q1_SINGLETON_MATERIALITY_AUDIT_v01.zip`

Expected SHA-256:

`e85da191519ac8ed033c46ac78257c1c7e515976fd87a0d99511093bd0d8e007`

Accepted facts:

* singleton strata = 24 / 5752 = 0.41725%
* singleton plot rows = 24 / 338619 = 0.00709%
* AB abundance fold singleton strata = 2
* BA abundance fold singleton strata = 22
* AB direct97 positive singleton mass = 0 / 97 species
* BA direct97 positive singleton mass = 1 / 97 species
* direct97 BA aggregate singleton mass fraction ≈ 0.003521%
* maximum species singleton fraction ≈ 1.2673%
* maximum observed omission TV ≈ 0.012673
* many singleton strata have very high TI

Status:

`ACCEPTED DERIVED MATERIALITY EVIDENCE`

---

# 5. Source-native/task-local cache

Allowed read-only cache:

`C:\range_paper\99_tmp\d10fb12_v01\cache\b12_cache.sqlite`

Expected SHA-256:

`0daf80d098546d61aecd8e75701f5174d9f6fd4452ce4a1b257651d45c9d2953`

Logical digest:

`e85168819a7954f9f1ead69f1554e29c193ba9ef369c7c2793b4587d5f8dd416`

Fingerprint:

`5d0a9dbaf55045c20bdab107f061c477fe77106d100bc95681a6dfebd1eeb7bd`

No national TREE rescan.

Expected:

`NEW_TREE_SOURCE_SCAN_ROWS = 0`

---

# 6. Work execution governance — HARD RULES

This section is mandatory.

## 6.1 No automatic task expansion

Do NOT automatically continue from:

B14 → B15 → new estimator → GVCF → hierarchical model → replicate generator.

B14 ends at materiality evidence.

Any next method requires new mainline authorization.

---

## 6.2 No rebuilding accepted expensive analyses

Do NOT rerun:

* B11;
* B12;
* B13;
* Q1 cohort projection;
* singleton materiality audit.

Reuse accepted artifacts.

Do NOT rebuild 1.5 million B13 Stage-P objects.

---

## 6.3 Early-stop is authorized

If an earlier phase provides sufficient evidence to answer the materiality question:

> skip optional later phases.

Record exactly:

* what evidence triggered early stop;
* which phases were not run;
* why they no longer had decision value.

Early stop is NOT task failure.

---

## 6.4 Material result also triggers stop

If a scientifically credible stress construction already shows that singleton uncertainty may substantially perturb the abundance measurement object:

> STOP.

Do not continue trying alternative stresses in order to obtain a smaller effect.

---

## 6.5 Numerical rerun limit

If a full expensive phase fails only because of numerical implementation/QC:

* diagnose first;
* one corrected full rerun is allowed.

If a second full rerun would be required:

> STOP and return to mainline.

Do NOT automatically launch repeated 30–60 minute/full Stage-S reruns.

---

## 6.6 Numerical correction versus scientific relaxation

Allowed:

* stable summation;
* correct `inf/NaN` equivalence;
* analytically justified floating-point tolerance;
* correction of coding errors.

Not allowed without mainline authorization:

* changing scientific stress level;
* dropping difficult cases;
* changing pool membership;
* changing cohort;
* loosening a scientific acceptance threshold;
* removing a stress state because it produces a large effect.

---

## 6.7 New evidence may change task priority

If B14 shows the singleton issue is clearly a bounded tail:

> do not continue optional deep characterization merely for completeness.

The task is not a standalone covariance-method paper.

---

# 7. Primary strategy

B14 must follow an escalation ladder.

## Phase A

Deterministic baseline and ordinary A/B fold discrepancy.

## Phase B

Empirical pseudo-singletonization stress calibration.

## Phase C

Apply frozen empirical stress envelope to singleton materiality.

## Phase D

Only if Phase B/C remain inconclusive:
use covariance-based B13 stress as secondary sensitivity.

Do NOT start Phase D automatically.

---

# 8. Phase A — frozen A2 abundance-map benchmark

For the 97 direct Q1 species reconstruct the accepted frozen A2 abundance maps separately for:

* fold A;
* fold B.

No support data.

For each species calculate:

* total A2 mass A;
* total A2 mass B;
* normalized map A;
* normalized map B;
* TV(A,B);
* total-mass ratio/difference.

Interpret:

> A/B map difference is an empirical two-realization sampling discrepancy benchmark.

It is NOT:

* truth;
* a confidence interval;
* biological temporal change.

Create:

`B14_AB_FOLD_DISCREPANCY_BENCHMARK_v01.csv`

---

# 9. Purpose of A/B benchmark

Later compare singleton stress effects against:

> the magnitude of ordinary whole-fold sampling disagreement already present between independent A/B abundance realizations.

This comparison is descriptive.

Do NOT set an arbitrary rule such as:

`singleton effect < 10% of A/B = PASS`.

Mainline will interpret continuous ratios.

---

# 10. Phase B — empirical pseudo-singletonization

This is the preferred primary stress calibration because it does not require assuming a production covariance model.

Use only accepted scoreable B12 pseudo-target strata.

Primary question:

> What happens in real FIA data when a stratum that normally has multiple plots is artificially reduced to one observed plot?

---

# 11. Pseudo-singletonization identity

Before implementation, verify whether the frozen A2/current FIA design supports the exact stratum identity:

For a target member with `n_g` equal-probability fold plots and per-plot TI `TI_g`:

reference stratum contribution:

`M_g = TI_g × Σ_i y_i`

hypothetical one-plot representation:

`M_g^(j) = (n_g × TI_g) × y_j`

where `j` is one retained plot.

The same logic applies cellwise using the retained plot's cell.

This is allowed ONLY if the accepted A2/substrate design identity supports:

`stratum-area coefficient = n_g × TI_g`

for that target member.

If this identity cannot be established from accepted artifacts:

> DO NOT improvise.

Mark:

`PSEUDO_SINGLETONIZATION_A2_IDENTITY_NOT_QUALIFIED`

and proceed to the predefined fallback in Section 25.

---

# 12. No source overclaim

Pseudo-singletonization is:

`PROJECT_DIAGNOSTIC`

not an FIA official estimator.

It asks:

> how different a one-plot realization could look from the same stratum's multi-plot estimate.

It does not claim the multi-plot estimate is ecological truth.

---

# 13. Pseudo-singletonization scope

Primary:

* 4,640 scoreable pseudo-target strata;
* direct97 species;
* 50-km primary grain.

Do NOT automatically expand to all402 unless an invariant/QC need requires it.

Do NOT run 100/200 km unless Phase B indicates a spatial-scale ambiguity relevant to the materiality decision.

This is intentionally narrower than B13.

---

# 14. Deterministic pseudo-singleton alternatives

For every eligible pseudo-target and every actual plot `j` in the target stratum:

construct the hypothetical one-plot stratum representation.

Replace only that target stratum in the same fold's frozen A2 species map.

All other strata remain unchanged.

For each direct97 species calculate:

* full target-map total mass;
* pseudo-singleton map total mass;
* total-mass relative change;
* normalized map TV;
* cell of retained plot;
* whether retained plot recorded the species;
* whether multi-plot target stratum had positive species mass;
* target stratum fraction of whole-species mass.

---

# 15. Critical zero-observation subset

Explicitly isolate:

`SELECTED_PLOT_ZERO_TARGET_STRATUM_POSITIVE`

meaning:

* retained pseudo-singleton plot has species y = 0;
* the multi-plot target stratum has positive species mass.

This is the closest empirical analogue to the concern:

> actual singleton plot recorded no species but the stratum could nevertheless have nonzero species mass.

This subset is a primary B14 diagnostic.

Do not hide it inside aggregate summaries.

---

# 16. High-TI stress strata

The accepted materiality audit showed many actual singleton strata are high-TI.

Therefore predeclare descriptive TI bands using the full 5,752 block×fold TI distribution:

* `<95th percentile`
* `95th–<99th percentile`
* `>=99th percentile`

These bands are already motivated independently of B14 outcomes.

Do NOT redefine them after seeing results.

Report pseudo-singleton stress separately by TI band.

---

# 17. Additional predeclared grouping

Allowed outcome-independent grouping:

* fold A / B;
* Level1 / Level2;
* target `n_g`;
* reference-strength band;
* TI band.

Do NOT group by:

* whether result is favorable;
* Q1 effect;
* eventual stress magnitude.

---

# 18. Phase-B required empirical summaries

For normalized-map TV and total-mass perturbation report:

* exact zero fraction;
* median;
* IQR;
* p90;
* p95;
* maximum finite observed;
* count.

Separately for:

* all pseudo-singleton events;
* high-TI;
* > =99th percentile TI;
* selected-plot-zero / target-stratum-positive;
* Level1;
* Level2;
* fold A;
* fold B.

No scientific threshold is implied by p90/p95.

They are descriptive stress levels.

---

# 19. Freeze stress calibration before actual24 application

Once Phase B is complete:

create and hash:

`B14_EMPIRICAL_STRESS_CALIBRATION_SEAL_v01.json`

It must contain the exact stress summaries to be used in Phase C.

After seal creation:

> stress definitions may not be changed based on actual24 results.

This is the B14 outcome firewall.

---

# 20. Required stress tiers

At minimum freeze:

### `E_OBSERVED`

actual observed singleton contribution.

### `E_P95`

95th-percentile empirical pseudo-singleton perturbation from the predeclared relevant matching group.

### `E_EMPIRICAL_MAX`

maximum finite perturbation observed in that matching group.

These are stress diagnostics, not probability claims.

If matching group sample size is too small:

use the broader predeclared parent group, and record the fallback.

Do not choose a broader/narrower group after observing actual24 effect.

---

# 21. Phase C — actual singleton materiality application

Primary actual scope:

* 24 singleton strata;
* 97 direct Q1 species.

Retain all species in the ledger.

Do not restrict analysis only to *Abies procera*.

Reason:

> observed zero contribution does not imply zero uncertainty.

---

# 22. Actual singleton matching rule

Match each singleton to empirical stress calibration using only pre-outcome design fields.

Priority order:

1. same fold + same route + same TI band;
2. same fold + same TI band;
3. same TI band;
4. all pseudo-target stress distribution.

Predeclare this hierarchy.

Do not use species outcome to select the matching group.

---

# 23. Species-specific application

For each actual singleton × direct97 species report:

* observed singleton A2 mass;
* observed singleton mass fraction;
* observed omission-TV bound;
* stress tier;
* empirical matched-group sample size;
* empirical stressed total-mass perturbation;
* empirical stressed normalized-map TV;
* design-match level.

Do not call the stressed value a confidence interval.

---

# 24. Multiple singleton strata for one species

If multiple singleton strata can affect the same species:

report both:

### individual-stratum stress

and

### conservative additive envelope

For additive envelope, explicitly label:

`CONSERVATIVE_NO_CANCELLATION_BOUND`

Do not assume independent errors.

Do not probabilistically combine stresses without separate authorization.

---

# 25. Predefined fallback if pseudo-singletonization identity is not qualified

Only if Section 11 fails:

use accepted B13/B12 covariance evidence as a secondary **stress construction**, not estimator.

Allowed states:

### C1

B9 candidate whole covariance.

### C2

B9 candidate covariance with empirical high-tail scale inflation derived from B13 pseudo-target trace underestimation distribution.

### C3

fixed NC1 incompatible shape rescaled to C2 scale.

Stress calibration must be frozen from pseudo-target evidence before actual24 evaluation.

No Gaussian confidence interpretation unless separately justified.

If covariance-to-map perturbation requires an unapproved distributional assumption:

> STOP.

Do not invent one.

---

# 26. Optional Phase D trigger

Phase D is allowed only if:

* Phase B/C cannot resolve materiality;
* and a predefined covariance stress can be applied without new estimator/distributional invention.

Otherwise:

> skip Phase D.

---

# 27. Comparison to ordinary A/B sampling discrepancy

For each direct97 species calculate:

`stress_TV / TV(A,B)`

when A/B TV > 0.

Also report:

* absolute stress TV;
* A/B TV;
* ratio.

If A/B TV = 0:

retain as separate class.

Interpretation:

> relative scale of singleton stress versus observed full-fold sampling discrepancy.

Do NOT interpret A/B TV as truth error.

---

# 28. Cohort-level summaries

For each stress tier report:

* number direct97 species with any nonzero stressed perturbation;
* median stressed TV;
* p90;
* p95;
* maximum;
* median stress/A-B ratio;
* p90 stress/A-B ratio;
* maximum;
* top affected species.

Separately:

* AB direction;
* BA direction.

---

# 29. Explicit *Abies procera* case

Because the accepted point-mass audit identified *Abies procera* as the only direct97 species with positive observed singleton mass:

provide a dedicated case summary.

But:

> do not design stress levels around *Abies procera*.

Stress calibration must already be frozen.

---

# 30. Zero-observed actual cases

This is a hard requirement.

For actual singleton × species with observed y=0, report the empirical stress inherited from:

`SELECTED_PLOT_ZERO_TARGET_STRATUM_POSITIVE`

or its predeclared fallback group.

This directly tests the remaining concern that:

> observed zero may conceal positive stratum abundance.

---

# 31. No support / no Q1

Strictly prohibited:

* support maps;
* occupancy models;
* range geometry;
* paired-null;
* Q1 effect;
* Q1 direction;
* Q1 predictive information.

Expected:

`Q1_CALCULATION_ROWS = 0`

B14 can close only the singleton-abundance-uncertainty subproblem.

---

# 32. No species exclusion

Do NOT create:

* singleton-safe species;
* failed species;
* eligible/ineligible cohort.

No species is removed.

If one/few species appear sensitive:

report them as:

`SPECIES_LEVEL_SENSITIVITY_REQUIRED`

not exclusion.

---

# 33. No arbitrary pass threshold

Do NOT invent:

* <1% PASS;
* <5% negligible;
* stress/A-B <0.1 PASS.

Report continuous evidence.

Mainline decides whether impact is scientifically limited.

---

# 34. Main scientific interpretation categories

B14 may recommend one of:

### `NONMATERIAL_TAIL_CANDIDATE`

Conservative empirical stresses produce limited abundance-map perturbation.

### `LOCALIZED_SPECIES_LEVEL_SENSITIVITY`

Most cohort stable but one/few species show meaningful stress sensitivity.

### `MATERIAL_SINGLETON_UNCERTAINTY_REMAINS`

Scientifically credible stress states produce broad or large measurement perturbation.

### `UNRESOLVED_STRESS_IDENTIFICATION`

Available evidence cannot construct a defensible stress envelope.

These are recommendations only.

Mainline makes final Gate decision.

---

# 35. Strong stopping rule

If B14 supports:

`NONMATERIAL_TAIL_CANDIDATE`

or

`LOCALIZED_SPECIES_LEVEL_SENSITIVITY`

and no validity failure exists:

> do not begin new covariance-method development inside B14.

STOP and return evidence.

---

# 36. Equally strong negative stopping rule

If B14 supports:

`MATERIAL_SINGLETON_UNCERTAINTY_REMAINS`

> STOP.

Do not add stronger/weaker alternative methods trying to reduce the effect.

---

# 37. Context/extremeness audit trigger

Do NOT automatically start:

`Q1_SINGLETON_CONTEXT_AND_EXTREMENESS_AUDIT`

It becomes justified only if B14 shows:

* material uncertainty;
* strong heterogeneity among singleton cases;
* or clear need for auxiliary contextual predictors.

Otherwise:

> contextual audit remains deferred.

---

# 38. Required outputs

At minimum:

`B14_MAIN_REPORT_v01.md`

`B14_AB_FOLD_DISCREPANCY_BENCHMARK_v01.csv`

`B14_PSEUDO_SINGLETON_EVENT_LEVEL_v01.parquet`

`B14_PSEUDO_SINGLETON_STRESS_SUMMARY_v01.csv`

`B14_ZERO_SELECTED_PLOT_STRESS_v01.csv`

`B14_HIGH_TI_STRESS_SUMMARY_v01.csv`

`B14_EMPIRICAL_STRESS_CALIBRATION_SEAL_v01.json`

`B14_ACTUAL24_STRESS_APPLICATION_v01.parquet`

`B14_DIRECT97_STRESS_SUMMARY_v01.csv`

`B14_AB_VS_BA_STRESS_SUMMARY_v01.csv`

`B14_ABIES_PROCERA_CASE_v01.csv`

`B14_STRESS_VS_AB_FOLD_DISCREPANCY_v01.csv`

`B14_MATERIALITY_DISPOSITION_MATRIX_v01.csv`

`B14_PROVENANCE_v01.csv`

`B14_OPEN_ITEMS_v01.csv`

`B14_INVARIANT_QC_v01.csv`

`B14_REFERENCE_FIREWALL_QC_v01.csv`

`B14_RUN_METADATA_v01.json`

`SHA256SUMS.csv`

`TRANSFER_MANIFEST_v01.csv`

required source/config/log.

---

# 39. Main report required questions

Answer in plain Chinese.

### Q1

Can an empirical one-plot realization materially distort a multi-plot stratum's contribution?

### Q2

How large are pseudo-singleton perturbations in the high-TI strata most analogous to the actual singleton cases?

### Q3

When the retained plot has y=0 but the full stratum is positive, how large is the resulting whole-species abundance-map perturbation?

### Q4

How does the empirical stress compare with ordinary A/B fold abundance-map disagreement?

### Q5

Do AB and BA differ?

### Q6

Do Level1 and Level2 differ in materiality, not merely covariance transportability?

### Q7

Do actual observed-zero singleton cases remain potentially dangerous under the empirical stress envelope?

### Q8

Does *Abies procera* remain the only species requiring visible sensitivity attention?

### Q9

Do any additional direct97 species become important under zero-observation stress?

### Q10

Does the 24-singleton problem remain a cohort-wide abundance uncertainty problem?

### Q11

Is it better characterized as a bounded tail / localized species-level issue?

### Q12

Is any new singleton covariance estimator scientifically necessary before proceeding?

### Q13

What evidence would reopen method development later?

---

# 40. Required disposition matrix

Create:

`B14_MATERIALITY_DISPOSITION_MATRIX_v01.csv`

Rows:

* structural rarity
* observed point-mass exposure
* zero-observation empirical miss stress
* high-TI stress
* normalized-map perturbation
* stress versus A/B fold discrepancy
* AB
* BA
* *Abies procera*
* cohort-level direct97
* singleton covariance method necessity

Columns:

* evidence
* scope
* stress definition
* result
* scientific interpretation
* remaining uncertainty
* status
* next action

---

# 41. Exact identities/QC

Verify:

* 24 singleton identity unchanged;
* 97 direct species unchanged;
* A2 reconstruction exact;
* TI applied once;
* no TREE rescan;
* no Q1 calculation;
* stress calibration sealed before actual application;
* actual outcomes do not alter stress definitions;
* multi-SPCD species not silently combined;
* no support data used.

---

# 42. Stage-P/Stage-S scope — keep it light

Do NOT reproduce B13's million-object sealing architecture unless scientifically required.

For B14 the firewall only needs to seal:

1. pseudo-singleton stress calibration;
2. matching hierarchy;
3. empirical stress tiers;

before actual singleton results are evaluated.

A small deterministic seal is preferable.

Do not create millions of objects for procedural symmetry with B13.

---

# 43. Work computational-efficiency rule

Before launching any computation expected to exceed 20 minutes, ask internally:

> Does this computation materially improve the B14 decision?

If no:

> do not run it.

No user clarification is required; document the omission.

The purpose is scientific sufficiency, not computational maximalism.

---

# 44. Repeated-calculation prohibition

Do not run the same full stress calibration multiple times merely to polish formatting/QC.

After successful scientific computation:

* CSV rendering/checking may use lightweight verification;
* do not rerun the scientific core for presentation-only issues.

---

# 45. Packaging/relay

Output:

`C:\range_paper\05_qc\d10fb14_v01_work_singleton_uncertainty_materiality_stress\`

Final:

`Q1_D10F_B14_v01.zip`

Use established relay:

`upload_target=mirror`

Do not introduce `mainline_handoff`.

Large ZIP may be Release asset.

---

# 46. Scientific statuses

Strictly distinguish:

### FROZEN

A/B, A2, B9 route, 50-km primary grain.

### ACCEPTED EVIDENCE

B11/B12/B13.

### ACCEPTED DERIVED MATERIALITY EVIDENCE

singleton materiality audit.

### B14 EMPIRICAL STRESS EVIDENCE

current task if accepted.

### OPEN

final singleton subgate disposition until mainline decision.

### NOT AUTHORIZED

new production covariance estimator.

---

# 47. STOP conditions

STOP if:

* any canonical SHA mismatch;
* pseudo-singleton A2 identity cannot be justified;
* A2 reconstruction fails;
* stress calibration uses actual24 outcome;
* national TREE rescan would be required;
* support/Q1 data would be required;
* new estimator/distributional model becomes necessary;
* multi-SPCD aggregation would be required;
* second expensive full numerical rerun would be needed;
* task begins expanding beyond materiality assessment.

Return explicit STOP report.

Do not improvise.

---

# 48. Completion states

Allowed:

`B14_MATERIALITY_STRESS_COMPLETE`

or

`B14_STOPPED_FOR_MAINLINE_REVIEW`

Do NOT state:

* `D10F-C PASS`
* `COVARIANCE SOLVED`
* `Q1 PASS`
* `SINGLETONS IRRELEVANT`

Only mainline can make the final subgate decision.

---

# 49. Final STOP

After B14 evidence is complete:

> STOP and return to Q1 mainline.

Do not automatically continue to:

* B15;
* GVCF;
* hierarchical model;
* context/extremeness audit;
* D10F-C;
* support;
* real Q1.

