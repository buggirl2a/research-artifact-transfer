# Q1_D10F_B13_v01_WORK_COMPONENT_TRANSPORTABILITY_DIAGNOSTIC

## 0. Role

You are the Q1 Work line.

Task:

`Q1_D10F_B13_v01_WORK_COMPONENT_TRANSPORTABILITY_DIAGNOSTIC`

Short ID:

`D10F-B13 v01`

Purpose:

> **Diagnose which components of B9 pool→target covariance transportability are supported, challenged, or unresolved in real FIA pseudo-target evidence, without implementing or selecting a new production estimator.**

This is a **pathology / mechanism diagnostic task**.

It is NOT:

* D10F-C;
* a new covariance estimator;
* production uncertainty propagation;
* support recovery;
* Q1 calculation;
* method selection based on Q1 outcome.

The task succeeds if it provides a scientifically interpretable diagnosis, even if the diagnosis is that no component is sufficiently transportable.

---

# 1. Current mainline status

The following are already accepted and must not be modified.

## FROZEN

* A/B split
* A2 point-estimator semantics
* B9 compatibility routes
* 50-km primary grain

## ACCEPTED EVIDENCE

B11:

`C:\range_paper\10_archive\d10fb11_v01\Q1_D10F_B11_v01.zip`

SHA-256:

`ee6888a47762aaa966afaeffddd2569500f0f8271745263b763711348d761624`

B12 v01_1:

`C:\range_paper\10_archive\d10fb12_v01_1\Q1_D10F_B12_v01_1.zip`

SHA-256:

`d009bf50225ca3c2f483e08fe17f22312f93c9a28f36786abae8729fde3a21ab`

Scientific status:

`ACCEPTED EMPIRICAL QUALIFICATION EVIDENCE`

Mainline disposition of unchanged whole-covariance transport:

`NOT PRODUCTION-QUALIFIED`

D10F-C:

`HOLD`

---

# 2. Accepted Q1 cohort projection

Accepted derived projection:

`Q1_B12_Q1_COHORT_PROJECTION_v01.zip`

Expected SHA-256:

`70d34c6905a9d76675943ae03182feae719340d159ca6b69b68b9b9d089f227e`

If a canonical archive copy exists, use it.

Otherwise search only under:

`C:\range_paper`

and accept only an exact SHA-identical copy.

This projection is required only for predeclared Q1 subgroup summaries.

It must NOT determine:

* component definition;
* method selection;
* thresholds;
* inclusion in primary B13 qualification.

Primary qualification universe remains the outcome-unselected B12 pseudo-target universe.

---

# 3. Required task-local cache

Use the already accepted B12 task-local cache read-only:

`C:\range_paper\99_tmp\d10fb12_v01\cache\b12_cache.sqlite`

Expected SHA-256:

`0daf80d098546d61aecd8e75701f5174d9f6fd4452ce4a1b257651d45c9d2953`

Expected logical digest:

`e85168819a7954f9f1ead69f1554e29c193ba9ef369c7c2793b4587d5f8dd416`

Expected fingerprint:

`5d0a9dbaf55045c20bdab107f061c477fe77106d100bc95681a6dfebd1eeb7bd`

If the exact cache is absent or mismatched:

> STOP.

Do NOT rebuild it by rescanning national TREE.

Expected:

`NEW_TREE_SOURCE_SCAN_ROWS = 0`

---

# 4. Protected B12 identities

Preserve:

* pseudo targets total = `5729`
* pseudo scoreable = `4640`
* Level1 = `4397`
* Level2 = `243`
* actual singleton = `24`
* actual Level1 = `11`
* actual Level2 = `13`
* FIA SPCD universe = `402`
* target-member leak = `0`

Do not modify B9 pool membership.

Do not create a different "better" pool.

---

# 5. Central scientific question

The original B9/B11 route effectively asked:

> Can the compatible pool's whole residual covariance represent the singleton target?

B12 v01_1 showed:

> only partially; unchanged whole-covariance transport is not sufficiently qualified.

B13 must ask the narrower question:

> **Which components of covariance mismatch are responsible, and which components—if any—show reproducible transportability?**

---

# 6. Do NOT begin with a biological factorization assumption

Do not assume in advance that covariance equals:

`abundance variance × spatial allocation`

or any similarly simple product.

The cross-disciplinary scout explicitly found that this simplification is not established.

B13 must begin from exact covariance/sample-scatter identities.

Any ecological/process interpretation comes only after algebraic diagnosis.

---

# 7. Two-layer decomposition strategy

B13 must use two distinct diagnostic layers.

## Layer A — matrix-level decomposition

This is the primary, safest decomposition.

It does not claim a biological process.

For every target and pool covariance matrix `C`, characterize at minimum:

### A1. Total covariance scale

Use an explicit scalar such as:

`trace(C)`

and retain any already accepted scalar variance quantity separately.

Compare target versus pool using:

* ratio
* absolute log ratio
* reference-noise analogue

### A2. Unit-trace covariance shape

For positive trace:

`U = C / trace(C)`

This removes total covariance scale while preserving spatial covariance shape.

Compare target versus pool using at minimum:

* Frobenius discrepancy
* Frobenius cosine similarity or equivalent normalized matrix similarity
* spectral summaries where valid

### A3. Variance-location profile

From the covariance diagonal:

`d_j = C_jj / trace(C)`

when trace > 0.

This asks:

> Where in the map is sampling variance located?

Compare target versus pool using:

* total variation distance
* overlap
* other clearly defined distance if useful

### A4. Off-diagonal dependence structure

After unit-trace normalization, separate:

* diagonal component
* off-diagonal component

Quantify whether disagreement persists after total-scale and diagonal-location differences are removed/characterized.

Do NOT force a correlation matrix where zero or near-zero diagonals make it unstable.

If a correlation-style diagnostic is used:

* report estimability;
* do not silently regularize.

---

# 8. Layer A oracle-scale diagnostic

Allowed diagnostic:

> rescale the already sealed pool covariance to the held-out target total trace while preserving pool shape.

This is:

`DIAGNOSTIC_ORACLE_ONLY`

It is NOT an estimator.

Purpose:

> determine how much full-covariance mismatch remains if total scale were known perfectly.

For each scoreable target report:

* baseline full-covariance discrepancy
* oracle-scale-matched discrepancy
* absolute and relative improvement
* Level1 / Level2
* reference-strength groups
* 50/100/200-km diagnostics

Do not derive any production rule from target trace.

---

# 9. Layer B — exact within-cell / between-cell sample-scatter decomposition

After Layer A, implement an exact finite-sample decomposition consistent with the accepted B10/B11 pooled residual algebra.

For each **member group `g` separately**, define the per-plot spatial contribution vector:

`x_gi = y_gi * e_cell`

where:

* `y_gi` is the accepted unexpanded per-plot analysis variable represented in the accepted B12 cache;
* `e_cell` is the one-hot spatial cell indicator.

Do NOT use already fully expanded values in a way that introduces double expansion.

Within each member group:

`T_g = Σ_i (x_gi - x̄_g)(x_gi - x̄_g)'`

Partition plots by spatial cell.

Define exact:

`W_g = Σ_c Σ_{i∈c} (x_gi - x̄_gc)(x_gi - x̄_gc)'`

and:

`B_g = Σ_c n_gc (x̄_gc - x̄_g)(x̄_gc - x̄_g)'`

Verify numerically:

`T_g = W_g + B_g`

to deterministic floating tolerance.

Then for a B9 pool:

`ν_P = Σ_g (n_g - 1)`

and:

`T_P = Σ_g T_g / ν_P`

`W_P = Σ_g W_g / ν_P`

`B_P = Σ_g B_g / ν_P`

Verify:

`T_P = W_P + B_P`

Do NOT concatenate all pool plots and center them globally.

That would change the accepted B10/B11 estimator semantics.

---

# 10. Interpretation boundary for Layer B

Use the following terminology unless evidence justifies stronger language:

### `WITHIN_CELL_OBSERVED_RESIDUAL_SCATTER`

not automatically:

`latent abundance residual process`

### `BETWEEN_CELL_ALLOCATION_MEAN_SCATTER`

not automatically:

`pure spatial allocation`

The between-cell component contains both:

* where plots/cells occur;
* between-cell differences in mean abundance contribution.

Therefore:

> do not call it pure domain allocation.

---

# 11. Mandatory cell-replication audit

Before interpreting Layer B, quantify whether within-cell residual scatter is empirically observable.

For every target/pool/grain report:

* number of occupied analysis cells
* number of cells with `n_cell = 1`
* number with `n_cell >= 2`
* fraction of plots in replicated cells
* fraction of cells replicated
* effective within-cell residual df if definable
* whether `W` is informative or structurally sparse

Do this at:

* 50 km primary
* 100 km diagnostic
* 200 km diagnostic

Critical rule:

> A zero or small observed `W` caused by no within-cell replication must NOT be interpreted as ecological/residual homogeneity.

---

# 12. Layer B component transport scores

For target versus candidate pool, separately compare:

### `W_target` vs `W_pool`

and

### `B_target` vs `B_pool`

At minimum:

* trace/log-scale mismatch
* unit-trace shape mismatch when estimable
* relative Frobenius
* diagonal variance-location profile
* reference-noise ratio where available

Retain degeneracy/estimability classes.

---

# 13. Exact error-geometry decomposition

For every estimable target:

`D_W = W_pool - W_target`

`D_B = B_pool - B_target`

and:

`D_T = D_W + D_B`

Verify:

`D_T = T_pool - T_target`

Then decompose total squared Frobenius error:

`||D_T||² = ||D_W||² + ||D_B||² + 2 <D_W, D_B>`

Report:

* within-component error energy
* between-component error energy
* cross/interference term
* normalized shares where meaningful
* sign of the cross term

This is important because component errors may:

* reinforce;
* partially cancel.

Do NOT infer component importance only from separate Frobenius magnitudes.

---

# 14. Oracle component-swap diagnostics

Allowed only as held-out pathology diagnostics.

After candidate pool components are sealed, construct:

### Oracle W swap

`T_oracle_W = W_target + B_pool`

Question:

> If within-cell observed residual scatter were known perfectly, how much mismatch remains?

### Oracle B swap

`T_oracle_B = W_pool + B_target`

Question:

> If between-cell allocation/mean scatter were known perfectly, how much mismatch remains?

### Oracle both

Must reproduce:

`T_target`

within numerical tolerance.

These are NOT production estimators.

Do not use oracle performance to choose or tune B9 pool membership.

---

# 15. Reference noise at component level

Repeat the accepted B12 split-half reference-noise logic for:

* full `T`
* within-cell `W`
* between-cell `B`
* Layer A total scale
* Layer A unit-trace shape
* variance-location profile

Use the existing frozen split identity unless a mathematically unavoidable reason prevents it.

If a component is not estimable under the existing split:

* retain `NOT_ESTIMABLE`;
* do not invent an alternative split after seeing results.

Compare:

`transport discrepancy / target-own reference noise`

where meaningful.

---

# 16. Negative control

Reuse the **predeclared B12 NC1 fixed incompatible pool**.

Do not create a new negative control after inspecting component results.

For each component ask:

> Is the B9 candidate systematically closer to target than the incompatible pool?

Report comparable-case fractions and continuous distances.

No hard pass threshold is authorized.

---

# 17. Level1 versus Level2

This is a major required analysis.

For each decomposition axis compare:

* Level1
* Level2

Questions:

1. Is Level2 failure dominated by variance-location / between-cell structure?
2. Does Level1 retain substantially better unit-trace shape?
3. Is total scale transport similarly poor in Level1 and Level2?
4. Does coarse aggregation improve only location structure, or also covariance shape?
5. Does higher Level2 pool df buy precision without buying relevance?

Do not pool Level1 and Level2 into one interpretation if their mechanisms differ.

---

# 18. 50 / 100 / 200 km

Primary Q1 grain remains:

`50 km`

100 and 200 km are:

`DIAGNOSTIC_COARSENING_ONLY`

At each grain rerun the component diagnostics consistently.

Do NOT:

* redefine the Q1 grain;
* recommend changing grain solely because diagnostics improve.

Use coarse results only to distinguish:

> fine-scale spatial mismatch

from:

> persistent component nontransportability.

---

# 19. Q1 cohort subgroup

Primary B13 qualification remains all B12 pseudo-targets and the 402-code outcome-unselected measurement universe where species-specific analyses apply.

Additionally provide predeclared Q1 subgroup summaries using the accepted projection:

### Direct clean subgroup

`97 direct single-SPCD Q1 species`

### Multi-code

retain the 3 multi-SPCD species as code-level diagnostic only.

Do not combine their SPCDs.

Do not use Q1 subgroup behavior to define or select components.

The subgroup only answers:

> Is the component diagnosis relevant to the actual Q1 cohort?

---

# 20. Species-specific scope

Species-joint component diagnostics may be computationally large.

Use Work judgment to implement efficiently, but preserve the scientific hierarchy:

1. generic/domain component diagnosis is mandatory;
2. Q1-relevant direct 97-species component diagnosis is strongly preferred;
3. full 402 species-specific component analysis may be done if computationally reasonable.

Do not weaken generic qualification because species-specific expansion is expensive.

If species-specific Layer B is underidentified because within-cell replication is sparse:

> report that fact rather than forcing a result.

---

# 21. Actual24 secondary check

The 24 actual singleton cases may be assessed only with the already accepted:

`FULL5_LIMITED_REFERENCE`

Rules remain:

* prediction/component objects sealed before opening full5;
* full5 is never truth;
* full5 is never tuning input;
* full5 does not alter B9 pool;
* full5 does not correct A/B.

Because full5 n is only 2–13:

> component-level actual24 evidence is secondary and potentially very weak.

Retain all 24 cases.

Do not exclude inconvenient cases.

---

# 22. Stage-P / Stage-S firewall

The new component diagnostic must preserve an outcome firewall.

Before target held-out reference is used for scoring:

Stage-P must seal, at minimum, all pool-derived component objects required for:

* candidate
* NC1

at all predeclared grains.

Each sealed object must include:

* target_id
* pool role
* grain
* component type
* residual df
* membership digest
* canonical sufficient-statistic digest
* source-cache identity
* canonicalization version

Stage-S must independently reconstruct and verify before opening the target reference.

Digest mismatch:

> HARD STOP.

Oracle objects are constructed only after the corresponding sealed pool objects verify.

---

# 23. No hidden regularization

Do not apply without explicit separate authorization:

* clipping
* ridge
* shrinkage
* nearest-PD
* matrix smoothing
* spatial smoothing
* covariance completion

If numerical tolerance is required for PSD diagnostics:

* document scale-aware tolerance;
* distinguish numeric tolerance from substantive repair.

---

# 24. Component identifiability must precede component interpretation

This is a hard scientific rule.

If a component is poorly observed because the target/reference has too little replication:

> classify it as weakly identified / not estimable.

Do NOT conclude:

> the component is small or transportable.

Observed absence of component scatter is not equivalent to true absence.

---

# 25. No new estimator

B13 may recommend a next methodological family only after diagnosis.

B13 must NOT implement:

* GVCF production estimator
* variance-function estimator
* correlation-sharing estimator
* hierarchical covariance model
* fine-stratum variance estimator
* partial-pooling estimator
* joint abundance replicate generator

All remain future tasks.

---

# 26. Possible scientific dispositions

B13 is allowed to conclude any of the following, based on evidence:

### A

Scale is the main transport failure; normalized shape is relatively stable.

### B

Variance-location / between-cell structure is the main failure.

### C

Scale is stable but covariance shape/dependence is not.

### D

Level1 and Level2 fail for different reasons.

### E

Both scale and shape are materially nontransportable.

### F

Observed component mismatch is largely indistinguishable from reference noise.

### G

Within/between process decomposition is underidentified because of insufficient within-cell replication.

### H

B9 design identities predict some components but not others.

### I

No useful component is sufficiently transportable under current information.

Do not force a favorable decomposition.

---

# 27. Decision logic for future mainline

The report may recommend, but not authorize:

### If scale poor, shape stable

Investigate:

* variance-function / scale model
* shared normalized covariance shape

### If scale stable, shape poor

Investigate:

* target-specific spatial/dependence model
* do not assume whole-shape transport

### If between-cell component poor, within component relatively stable

Investigate:

* domain/allocation-aware reconstruction
* residual borrowing only

### If within component poor, between component stable

Investigate:

* abundance-residual variance modeling
* preserve target spatial component

### If both poor

Investigate:

* richer design/auxiliary predictors
* hierarchical model
* partial identification / bounded uncertainty

### If reference noise dominates

Investigate:

* reference-strength problem before increasing model complexity.

Again:

> recommendation only.

---

# 28. Hard scientific guard against perfectionism

B13 must not require any component to equal target truth exactly.

The purpose is to determine whether component mismatch is:

* scientifically material;
* distinguishable from reference noise;
* systematically better than incompatible control;
* stable enough to justify a narrower future model.

Do not invent arbitrary zero-error requirements.

---

# 29. Equally hard guard against standards erosion

B13 must not declare a component “good enough” merely because it is the best available component.

A component can be:

> best among candidates

and still:

> not sufficiently qualified.

Do not convert relative superiority into absolute production qualification.

---

# 30. Required primary outputs

At minimum produce:

`B13_MAIN_REPORT_v01.md`

`B13_MATRIX_SCALE_SHAPE_DIAGNOSTICS_v01.parquet`

`B13_VARIANCE_LOCATION_DIAGNOSTICS_v01.parquet`

`B13_COMPONENT_REPLICATION_AUDIT_v01.parquet`

`B13_WITHIN_BETWEEN_DECOMPOSITION_v01.parquet`

`B13_COMPONENT_ERROR_GEOMETRY_v01.parquet`

`B13_ORACLE_COMPONENT_SWAP_v01.parquet`

`B13_COMPONENT_REFERENCE_NOISE_v01.parquet`

`B13_COMPONENT_TRANSPORT_VS_NOISE_v01.parquet`

`B13_COMPONENT_NEGATIVE_CONTROLS_v01.parquet`

`B13_LEVEL_ROUTE_SUMMARY_v01.csv`

`B13_COARSE_GRAIN_SUMMARY_v01.csv`

`B13_Q1_97_DIRECT_SUBGROUP_SUMMARY_v01.csv`

`B13_ACTUAL24_LIMITED_COMPONENT_REFERENCE_v01.parquet`

`B13_PROVENANCE_v01.csv`

`B13_OPEN_ITEMS_v01.csv`

`B13_INVARIANT_QC_v01.csv`

`B13_REFERENCE_FIREWALL_QC_v01.csv`

`B13_RUN_METADATA_v01.json`

`SHA256SUMS.csv`

`TRANSFER_MANIFEST_v01.csv`

required code/config and concise logs.

---

# 31. Main report — required plain-language answers

The report must answer these in clear Chinese.

### Q1

Is the original whole-covariance mismatch mainly a scale problem, a shape/location problem, or both?

### Q2

After perfect oracle correction of total covariance scale, how much mismatch remains?

### Q3

Where is variance located differently between target and pool?

### Q4

Does the off-diagonal dependence structure transport better or worse than diagonal variance location?

### Q5

What does the exact within-cell / between-cell sample-scatter decomposition show?

### Q6

Is within-cell scatter actually identifiable at 50 km, or is cell replication too sparse?

### Q7

Does 100/200-km aggregation change which component is responsible?

### Q8

Do Level1 and Level2 fail for the same reason?

### Q9

Which component discrepancies exceed target-own reference noise?

### Q10

Which components are more target-like under B9 candidate than under the fixed incompatible NC1 pool?

### Q11

Does the direct 97-species Q1 cohort show the same component pattern?

### Q12

Do the actual24 limited references provide any consistent secondary signal?

### Q13

Which candidate component-sharing hypotheses remain scientifically plausible?

### Q14

Which candidate hypotheses are materially challenged?

### Q15

What is the narrowest justified next methodological investigation?

---

# 32. Required “what we learned” table

Create:

`B13_COMPONENT_DISPOSITION_MATRIX_v01.csv`

Rows at minimum:

* total scale
* unit-trace full shape
* normalized diagonal variance-location profile
* off-diagonal dependence
* within-cell observed residual scatter
* between-cell allocation/mean scatter

Columns:

* mathematical definition
* empirical estimability
* Level1 transport evidence
* Level2 transport evidence
* reference-noise context
* NC1 discrimination
* 50-km result
* coarse-grain result
* Q1-97 relevance
* actual24 relevance
* scientific status
* recommended next investigation
* major caveat

Statuses must be evidence-based, e.g.:

* `SUPPORTED_CANDIDATE`
* `MATERIALLY_CHALLENGED`
* `WEAKLY_IDENTIFIED`
* `UNRESOLVED`

Do NOT use `PRODUCTION_PASS`.

---

# 33. Exact algebra QC

Create a dedicated invariant QC proving:

For every member where calculable:

`T_g = W_g + B_g`

and for every pool:

`T_P = W_P + B_P`

within an explicitly documented deterministic floating tolerance.

Also verify:

* all component matrices symmetric;
* PSD status;
* no silent regularization;
* df identity;
* original B12 whole-covariance reconstruction matches accepted B12 sufficient statistics.

Any material algebra discrepancy:

> HARD FAIL.

---

# 34. Protected B12 reconciliation

B13 must verify that it has not changed:

* B9 pool membership
* target identities
* Level1/Level2 route
* B12 full-covariance baseline
* Q1 cohort identities
* A/B
* A2

Baseline B12 v01_1 metrics used in B13 summaries must reconcile with the accepted package.

---

# 35. Source/provenance statuses

Strictly distinguish:

### FROZEN

A/B, A2, B9 route, 50-km grain.

### ACCEPTED EVIDENCE

B11 and B12 v01_1.

### ACCEPTED DERIVED PROJECTION EVIDENCE

Q1 cohort projection.

### B13 EMPIRICAL DIAGNOSTIC EVIDENCE

new component results if task passes.

### HYPOTHESIS / DESIGN CANDIDATE

any proposed future component-sharing model.

### OPEN

production covariance solution and D10F-C.

---

# 36. No source-native overclaim

This component decomposition is a project statistical analysis.

Do not describe it as an FIA official estimator unless an exact FIA authority exists.

FIA source authority remains distinct from project-induced decomposition.

---

# 37. No Q1 calculation

Expected:

`Q1_CALCULATION_ROWS = 0`

Do not read:

* support outcome
* range geometry
* Q1 statistic
* paired-null results

No component may be selected because it produces a favorable Q1 effect.

---

# 38. Output location

Use:

`C:\range_paper\05_qc\d10fb13_v01_work_component_transportability_diagnostic\`

Temporary:

`C:\range_paper\99_tmp\d10fb13_v01\`

Final package:

`Q1_D10F_B13_v01.zip`

Do not archive automatically.

---

# 39. Transfer

Use the established artifact-relay design.

`TRANSFER_MANIFEST_v01.csv` should follow the relay system's required `mirror` semantics.

Do not introduce `mainline_handoff` if that breaks the accepted relay workflow.

Large final ZIP may be placed as Release asset; mirror should expose the audit-relevant component files.

---

# 40. Chat-return discipline

Do not paste source code into chat.

Return only:

* task status;
* key scientific findings;
* exact final ZIP path;
* SHA-256;
* transfer/release information;
* STOP statement.

All code must remain inside the returned artifact package.

---

# 41. STOP conditions

STOP if:

* B12 v01_1 SHA mismatch;
* B12 cache SHA/logical digest mismatch;
* B9 membership differs from accepted B12;
* Stage-P/Stage-S firewall fails;
* exact `T=W+B` identity materially fails;
* national TREE would need to be rescanned;
* hidden regularization is required;
* component diagnostics require changing A2 or B9;
* Q1 outcome would be needed to choose a component;
* a new estimator would have to be implemented to complete the diagnostic.

Generate explicit STOP report.

Do not improvise around these boundaries.

---

# 42. Completion state

On successful completion, the Work line may state:

`B13_DIAGNOSTIC_COMPLETE`

but must NOT state:

* `D10F-C PASS`
* `COVARIANCE SOLVED`
* `PRODUCTION READY`

The final scientific decision remains with Q1 mainline.

---

# 43. Final STOP

After completing B13:

> STOP and return the exact package to Q1 mainline.

Do not automatically continue into:

* GVCF
* hierarchical covariance modeling
* variance-function modeling
* replicate generation
* D10F-C
* support recovery
* real Q1.
