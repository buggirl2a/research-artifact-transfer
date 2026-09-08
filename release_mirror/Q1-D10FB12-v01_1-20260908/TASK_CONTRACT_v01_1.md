# Q1_D10F_B12_v01_1_WORK_COVARIANCE_QUALIFICATION_CLOSURE

## 0. Role and authority

You are operating as the **Work / agentic qualification line** for the Q1 Species-Range Internal Structure project.

Your role in this task is:

> inspect the completed B12 v01 real-FIA qualification, recover and verify its local artifacts/cache, close the missing covariance-level qualification and firewall evidence, independently audit the corrected results, and return an evidence package to Q1 mainline.

You are NOT the scientific mainline.

You may:

* investigate;
* inspect;
* run calculations;
* repair implementation defects;
* close qualification gaps;
* compare evidence;
* identify natural evidence strata;
* recommend next steps.

You may NOT:

* change the frozen scientific design;
* select a new production estimator;
* change B9 compatibility rules;
* start D10F-C;
* implement covariance factorization as a new method;
* run support analysis;
* run Q1;
* use full-five-panel data to alter A/B estimates.

Q1 mainline retains all final authority.

---

# 1. Task identity

Task:

`Q1_D10F_B12_v01_1_WORK_COVARIANCE_QUALIFICATION_CLOSURE`

Short ID:

`D10F-B12-v01_1-WORK`

This task succeeds B12 v01.

It is not a new scientific B12 experiment from scratch.

Its purpose is:

> **close the covariance-level qualification gaps discovered during independent mainline audit of B12 v01, while preserving all already-valid real-FIA scalar/domain-profile evidence and then determine what the corrected evidence actually implies.**

---

# 2. High-level Q1 scientific context

The Q1 scientific question is:

> Knowing contemporary occupied support structure, how much does it reduce uncertainty about population-mass allocation inside the occupied domain beyond matched counterfactual expectation, and does that reduction generalize to unseen species?

The project separates:

* support measurement;
* abundance measurement.

A/B whole-panel splitting is frozen because support and abundance must not reuse the same FIA observations.

A = 2 complete FIA panels.

B = the complementary 3 complete FIA panels.

This creates reduced fold-specific sample sizes.

The current task concerns only:

> **abundance measurement uncertainty**

and specifically the covariance treatment for 24 poststrata that become singleton (`n_h=1`) after the A/B split.

Real Q1 remains forbidden.

---

# 3. Frozen abundance estimator

D10C-A froze the A2 point-estimator semantics.

Conceptually:

`TPA_UNADJ × basis-matched official ADJ_FACTOR × fold-specific TI`

Important:

* full-evaluation EXPNS is not multiplied again;
* condition proportions are not multiplied again;
* A2 point estimates are not being reopened by B12;
* B12 concerns variance/covariance only.

For residual-covariance qualification, the plot-level residual variable must remain on the:

> **unexpanded plot scale**

before TI / population-area expansion.

Double TI/area expansion is prohibited.

---

# 4. Why singleton covariance became a project problem

The 24 singleton strata are not source-FIA singleton strata.

They are:

> `FOLD_INDUCED_SPARSE`

The complete unsplit FIA parent strata originally had approximately `n_h = 2–13`.

A/B splitting caused one fold to retain only one plot.

A single plot cannot estimate its own within-poststratum residual variance/covariance.

Therefore Q1 needs a design-valid way to estimate the missing residual covariance without changing the A2 point estimate.

---

# 5. B9 result — where variance information may come from

B9 established an outcome-independent compatible information-scope framework.

For each singleton target:

## Level1

Use compatible non-singleton poststrata from:

`same source EU + same evaluation + same fold`

subject to target-matched core design identity.

If compatible material exists, stop there.

## Level2

Only when Level1 has no usable compatible material:

`same state + same evaluation + same fold`

using the same target-matched design identity rules.

No Level3.

Accepted B9 structural result:

* 24 / 24 structurally available;
* Level1 = 11;
* Level2 = 13;
* unresolved = 0.

B9 defines:

> **who is allowed to supply variance information**

not:

> whether that information truly transports to the target.

---

# 6. What “target-matched design identity” means

Relevant hard identities already accepted by B9 include, where applicable:

* DESIGNCD;
* raw DESIGNCD where recovered;
* repair class;
* target INTENSITY;
* production / non-production class;
* explicit special / nonfederal / augmentation identity;
* evaluation;
* fold;
* geographic level.

Important:

> INTENSITY is matched to the target.

It is NOT restricted universally to `INTENSITY=1`.

The following remain descriptive rather than hard filters:

* MANUAL;
* regional MANUAL;
* SAMP_METHOD_CD;
* MEASYEAR.

Do not change this status during the task.

---

# 7. B10 result — how compatible information is pooled

B10 identified the primary qualification candidate:

> **full-pool within-poststratum residual covariance**

For compatible non-singleton strata `g`:

`S_P = Σ_g [(n_g - 1) S_g] / Σ_g (n_g - 1)`

Each stratum must be centered within itself before pooling.

Do not pool raw observations across strata without within-stratum centering.

The target singleton retains its own:

* point coefficient;
* W_h;
* n_h;
* TI;
* population area;
* fold identity;
* point estimate.

Only its unestimable residual covariance quantity is replaced conceptually by `S_P`.

---

# 8. B11 accepted synthetic result

Accepted B11 package:

`C:\range_paper\10_archive\d10fb11_v01\Q1_D10F_B11_v01.zip`

Expected SHA-256:

`ee6888a47762aaa966afaeffddd2569500f0f8271745263b763711348d761624`

B11 established:

1. pooled covariance implementation is mathematically correct;
2. within-stratum centering is required;
3. common-covariance worlds are unbiased;
4. non-Gaussian/heavy-tail worlds do not themselves create systematic bias;
5. pool covariance may be internally heterogeneous if the target covariance equals the df-weighted pooled covariance;
6. target–pool mismatch produces direct covariance bias;
7. cross-domain covariance can be badly wrong while marginal variance/trace looks correct;
8. Level1 and Level2 separate precision from transport risk.

Current B11 interpretation:

> **The algebra is not the main unresolved problem. Transportability is.**

---

# 9. Canonical measurement substrate

Use:

`C:\range_paper\10_archive\q1_fia_substrate_v01_1\Q1_FIA_SUBSTRATE_v01_1.zip`

Expected SHA-256:

`1dbd8cf3fdb9fdbd25945ed70af64e1c739ec78f10f24ec4866128c38d5d946e`

It contains the accepted species-blind measurement/design substrate including:

* F0 = 338,619 plot visits;
* A = 135,513;
* B = 203,106;
* 5,752 block×fold identities;
* fold-specific TI identities;
* 24 singleton targets;
* B9 Level1/Level2 structural routes;
* design identities;
* permanent-plot history.

Do not alter it.

---

# 10. Parent B12 v01 artifact

Parent B12 artifact:

`Q1_D10F_B12_v01.zip`

Expected SHA-256:

`202b7a475a7aeb3dfe35749d70fccb076729dea79e8a75fcafb63c83c800c433`

Prefer exact local copy already under the Q1 project/QC directories.

Verify SHA fresh.

Do not substitute a reconstructed package.

---

# 11. B12 v01 task-local cache

B12 v01 already completed the expensive real-FIA extraction.

Expected working/cache root:

`C:\range_paper\99_tmp\d10fb12_v01\`

This cache must be treated as the primary computational source for the correction.

Important:

> **Do not rescan national TREE / the ~71.6 GB FIA SQLite.**

The B12 v01 extraction already read:

`4,727,482 TREE rows`

The correction should report:

`NEW_TREE_SOURCE_SCAN_ROWS = 0`

If the exact cache cannot be reliably verified:

> STOP and return to mainline.

Do not silently reconstruct the extraction.

---

# 12. What B12 v01 already did successfully

Independent mainline audit accepted the following architecture/evidence.

## Pseudo-target universe

* total structural pseudo-targets = `5,729`
* scoreable = `4,640`
* target core-identity heterogeneous / unscoreable under the frozen B9 target identity = `1,089`

Among the 4,640:

* Level1 = `4,397`
* Level2 = `243`

## Actual singletons

* actual targets = `24`
* Level1 = `11`
* Level2 = `13`

## FIA SPCD measurement universe

* FIA SPCD codes = `402`

## Stage-P holdout structure

* target-member leak = `0`
* pool membership matched the B9 construction
* support analysis = `0`
* Q1 calculation = `0`

These results are protected.

---

# 13. What pseudo-target validation means

For a normal non-singleton poststratum:

1. treat its residual covariance as unavailable;
2. exclude the target stratum from the compatible pool;
3. apply the same B9 Level1/Level2 rule used for a true singleton;
4. predict the target residual covariance from other strata;
5. seal the prediction;
6. only then reveal the held-out target residual information;
7. score prediction versus target reference.

Thus B12 tests:

> whether the B9 borrowing rule predicts real FIA targets that actually have observable residual structure.

The true 24 singleton targets cannot directly reveal their fold-specific covariance because `n_h=1`.

Pseudo-targets provide the main empirical validation mechanism.

---

# 14. Role of full five-panel FIA reference

For the actual 24 singleton cases, the complete five-panel FIA parent stratum has approximately 2–13 plots.

This can provide:

> limited target-specific observed residual information.

It is strictly:

`FULL5_LIMITED_REFERENCE`

It is NOT:

* ecological truth;
* a gold standard;
* an input to the A/B estimator;
* an input to pool construction;
* a correction target;
* a tuning target;
* a reason to remove a case.

Prediction must be constructed without this reference.

Reference may only be opened after prediction is sealed.

---

# 15. Accepted B12 v01 empirical signal

The corrected Work task must preserve, not overwrite, the accepted scalar/domain-profile results.

### Level1

Among scoreable pseudo-targets:

* n = `4,397`
* median pool residual df ≈ `170`
* median 50-km domain TV distance ≈ `0.424`
* median cell-frequency overlap ≈ `0.576`
* median generic `|log variance ratio| ≈ 1.067`

This corresponds to a typical generic variance factor discrepancy of roughly:

`exp(1.067) ≈ 2.9×`

### Level2

* n = `243`
* median pool residual df ≈ `2,477`
* median domain TV distance ≈ `0.932`
* median cell-frequency overlap ≈ `0.068`
* median generic `|log variance ratio| ≈ 1.220`

Typical generic variance factor discrepancy:

`≈3.4×`

---

# 16. Strong-reference evidence

Within strong-reference `R5` pseudo-targets (`target df >=49`):

Level1 spatial mismatch remains materially lower than Level2.

Accepted approximate medians:

### Level1

* domain TV ≈ `0.306`
* overlap ≈ `0.694`

### Level2

* domain TV ≈ `0.974`
* overlap ≈ `0.026`

Thus:

> larger Level2 pool df does not automatically imply smaller transport distance.

---

# 17. Generic abundance-residual signal

Within Level1 R5 pseudo-targets:

* median pool-target `|log variance ratio| ≈ 1.135`
* median target internal split-half noise ≈ `0.399`

Approximate scale:

* pool-target ≈ `3.1×`
* target internal split noise ≈ `1.5×`

Thus many pool-target discrepancies appear larger than target-reference noise.

This is already accepted empirical evidence.

---

# 18. Species-specific accepted evidence

The correct counts are:

* target species variance > 0 = `55,923`
* target variance >0 and pool variance >0 = `48,723`
* target variance >0 but pool prediction =0 = `7,200`

Therefore:

`7,200 / 55,923 ≈ 12.87%`

of target-positive-variance cases have no corresponding positive residual-variance signal in the compatible pool.

Among the `48,723` positive/positive cases:

median:

`|log variance ratio| ≈ 1.698`

equivalent typical factor discrepancy:

`≈5.46×`

Do NOT repeat the earlier inaccurate number `55,927`.

---

# 19. Species-universe interpretation boundary

The 402 FIA SPCD codes are:

> outcome-unselected FIA measurement codes.

They are not identical to the exact 101 Q1 Range Gate candidates.

If the exact accepted taxonomy/range mapping is not locally and uniquely available:

> do not reconstruct it from summaries.

B12 v01_1 does not need to solve this unless necessary for evidence interpretation.

Do not generalize the all-402 magnitude directly to the 101 strict Q1 candidates.

---

# 20. Actual24 accepted limited-reference signal

For generic full-five-panel limited-reference comparisons, accepted approximate medians were:

* overall `|log variance ratio| ≈ 0.862`
* Level1 ≈ `0.826`
* Level2 ≈ `1.604`

Of the 16 actual targets with positive generic target variance:

* prediction within bootstrap reference interval = `9/16`
* Level2 positive-reference cases = `5`
* Level2 within bootstrap reference interval = `0/5`

Because full parent n is only 2–13:

> treat this as direct but weak evidence.

Do not overstate it.

---

# 21. Negative-control evidence from v01

## NC2

Incorrect uncentered pooling produced:

* median uncentered/centered variance ≈ `1.81×`
* approximately `93.8%` of finite cases >1

This supports the necessity of within-stratum centering.

Preserve this result.

## NC1

The fixed different-state incompatible pool did not perform dramatically worse than the candidate in generic scalar prediction.

Overall candidate better fraction was approximately:

`53.6%`

Among stronger R5 targets it was approximately:

`62.6%`

Correct interpretation:

> B9 has some discriminatory value, especially under stronger references, but scalar evidence alone does not establish strong transportability.

Do not describe the control as “random geography”.

---

# 22. Why B12 v01 was not canonically accepted

Mainline audit identified three primary qualification gaps and several secondary ones.

These gaps do NOT invalidate the accepted scalar/domain-profile empirical evidence.

They must be closed before final B12 acceptance.

---

# 23. Gap A — full covariance predictions were not fully Stage-P sealed

B12 v01 sealed:

* pool membership;
* generic scalar/projection predictions;
* species scalar/projection predictions.

However Stage-S full covariance scoring reconstructed covariance objects from task-local sufficient statistics.

The complete:

* domain covariance prediction;
* generic abundance×domain covariance prediction;
* species abundance×domain covariance prediction

were not all cryptographically committed as Stage-P immutable prediction objects before held-out scoring.

No target leak has been detected.

But the frozen prediction-before-reference firewall contract was not fully demonstrated.

This must be corrected.

---

# 24. Gap B — covariance-level target-reference noise was incomplete

B12 v01 adequately retained scalar split-half target noise.

It also computed some:

* domain projection split diagnostics;
* generic-joint projection split diagnostics;

but did not properly deliver them in the qualification outputs.

Species joint covariance reference-noise qualification was incomplete.

Therefore existing full-matrix discrepancies cannot yet be interpreted with the same reference-noise discipline as scalar discrepancies.

This must be corrected.

---

# 25. Gap C — leading eigenvalue diagnostic implementation bug

B12 v01 used an all-ones starting vector for power iteration.

For one-hot domain covariance:

> the all-ones direction lies in the covariance null space.

Therefore all scored domain leading-eigenvalue ratios became NaN.

This is a deterministic implementation defect, not a scientific result.

It must be fixed.

---

# 26. Secondary qualification gaps

Also address:

1. explicit PSD diagnostics;
2. deterministic coarse spatial aggregation diagnostics;
3. NC1 domain/joint comparison;
4. substantive interpretation of MANUAL / SAMP_METHOD_CD / MEASYEAR;
5. evidence-based Q10 recommendation;
6. v01 → v01_1 logical reconciliation.

---

# 27. Work-specific instruction

Unlike the former local deterministic execution line, you are authorized to:

> inspect intermediate artifacts and code, investigate why each qualification gap occurred, repair the smallest valid implementation surface, run the missing analyses, self-audit them, and decide whether additional non-method-changing checks are necessary to interpret the evidence correctly.

However:

> do not expand scope merely because additional analyses are interesting.

Every additional check must directly close or interpret the specified B12 transportability question.

---

# 28. Preserve accepted parent evidence

Do not recompute or alter parent outputs unless necessary for verification.

Where parent results are protected:

* verify logical identity;
* reuse;
* reconcile.

The correction must not silently replace existing scalar evidence with a newly implemented alternative.

---

# 29. Cache verification first

Before any corrected analysis:

verify the existing B12 task-local cache.

At minimum establish:

* exact file identity;
* schema;
* row counts;
* logical digests or parent-recorded fingerprints;
* linkage to parent B12 provenance.

Create an explicit cache verification record.

If the cache cannot be verified:

> STOP.

Do not rescan TREE.

---

# 30. No national TREE rescan

Hard requirement:

`NEW_TREE_SOURCE_SCAN_ROWS = 0`

Do not reopen the full national TREE source or the 71.6-GB SQLite to rebuild the extraction.

If a required missing quantity genuinely cannot be recovered from the verified cache and parent artifacts:

> return the blocker to Q1 mainline.

---

# 31. Close the full-covariance Stage-P firewall

For every covariance object that will be scored against held-out target/reference data, establish a deterministic Stage-P prediction identity.

Required object classes:

* DOMAIN
* GENERIC_JOINT
* SPECIES_JOINT

The object need not be stored as a giant dense matrix.

A deterministic sufficient-stat representation is acceptable.

---

# 32. Canonical covariance prediction representation

Construct a canonical prediction representation sufficient to reproduce the predicted covariance exactly.

Possible contents:

* ordered cell IDs;
* pooled residual df;
* first moments;
* second moments;
* cross-products;
* pooled sufficient statistics;
* target identity;
* species identity where relevant;
* route;
* dimensional ordering.

Use:

* deterministic ordering;
* explicit data types;
* stable float serialization;
* no worker-order dependence.

Hash:

`SHA256(canonical object)`

before scoring.

---

# 33. Required full covariance seal registry

Produce:

`B12_FULL_COV_PREDICTION_SEAL_v01_1.parquet`

At minimum:

* object_id
* target_id
* species_id if applicable
* object_type
* route
* dimension
* residual_df
* canonical_object_sha256
* Stage-P status
* source cache identity

Seal this registry before held-out scoring.

---

# 34. Stage-S verification

Before scoring each full covariance object:

1. reconstruct the predicted object;
2. canonicalize it using the exact Stage-P procedure;
3. recompute digest;
4. verify against the Stage-P seal;
5. only then score against held-out reference data.

Any mismatch:

> HARD STOP.

Report:

* planned objects;
* sealed objects;
* verified objects;
* failed objects.

---

# 35. Reverify old Stage-P seals

Also independently verify the existing parent B12:

* pool-membership seal;
* generic scalar/projection seal;
* species scalar/projection seal.

Demonstrate that their logical contents remain unchanged.

---

# 36. Covariance-level target-reference noise

Complete target-internal noise diagnostics for:

## Domain-only

`one_hot(50km cell)`

## Generic joint

`generic unexpanded y × one_hot(cell)`

## Species joint

`species unexpanded y_s × one_hot(cell)`

Use the already frozen deterministic split identity from B12 v01.

Do not optimize or regenerate favorable splits.

---

# 37. Domain split-half qualification

For pseudo-targets with sufficient target sample size, compare deterministic target halves.

Retain at minimum:

* half sizes;
* domain projection variance ratios;
* absolute log ratios;
* median projection discrepancy;
* p90 projection discrepancy;
* matrix relative Frobenius discrepancy when estimable;
* trace ratio;
* reference estimability status.

---

# 38. Generic-joint split-half qualification

For the accepted generic A2-compatible unexpanded abundance quantity:

`z_i = y_i × one_hot(cell_i)`

perform analogous target-half covariance diagnostics.

Do not redefine `y`.

---

# 39. Species-joint split-half qualification

For informative target × SPCD cases:

`z_i,s = y_i,s × one_hot(cell_i)`

compute target-internal projection/covariance noise where estimable.

Classify, rather than delete, cases with insufficient target information.

---

# 40. Transport versus reference-noise comparison

For every informative object compare:

* candidate pool → target covariance discrepancy;
* target-half → target-half covariance discrepancy.

Return:

* raw transport discrepancy;
* reference-noise discrepancy;
* excess discrepancy;
* ratio where stable.

Do not invent a universal threshold.

The purpose is:

> determine whether observed target-pool covariance mismatch materially exceeds the noise of estimating the target covariance itself.

---

# 41. Fix spectral diagnostics

Replace the invalid all-ones-only power iteration.

Preferred:

> exact symmetric eigensolver where computationally tractable.

Otherwise use a deterministic multi-start eigensolver with outcome-independent starting vectors.

Do not use target outcomes to choose the start.

Return:

* target largest eigenvalue;
* predicted largest eigenvalue;
* ratio;
* convergence status;
* effective rank.

---

# 42. PSD diagnostics

For every scored covariance object report:

* minimum eigenvalue or valid deterministic equivalent;
* scale-aware numerical tolerance;
* PSD status:

  * PASS
  * NUMERIC_TOLERANCE
  * FAIL;
* effective rank.

Do not:

* clip eigenvalues;
* add ridge;
* use nearest-PD;
* shrink the matrix.

If material non-PSD behavior appears:

> investigate whether it is implementation error or algebraic consequence, and report before continuing to scientific interpretation.

---

# 43. Coarse spatial diagnostics

Primary scientific grain remains:

> 50 km.

Do not alter it.

However use deterministic parent-grid aggregation as a transportability diagnostic.

Using accepted grid IDs such as:

`50km_<ix>_<iy>`

construct at minimum:

### 100-km diagnostic parent grid

`floor(ix/2), floor(iy/2)`

### 200-km diagnostic parent grid

`floor(ix/4), floor(iy/4)`

Use mathematically correct floor division for negative indices.

Unit-test negative indices explicitly.

---

# 44. Purpose of coarse diagnostics

The key question is:

> Is Level2's extreme 50-km transport mismatch mainly fine-scale spatial relabeling, or does substantial mismatch persist even at broader absolute spatial structure?

Do not treat 100/200 km as:

* alternative Q1 grains;
* sensitivity grains;
* new estimands.

They are diagnostic aggregations only.

---

# 45. Required coarse metrics

At 50, 100 and 200 km diagnostics, compare target versus pool using at least:

* total-variation distance;
* overlap;
* Hellinger distance;
* Jensen-Shannon divergence;
* target-only spatial units;
* pool-only spatial units;
* covariance discrepancy;
* projection variance discrepancy;
* leading eigenvalue discrepancy.

Where target-reference noise is available, compare mismatch against it.

---

# 46. Random projection limitation

B12 v01 suggested a potentially important phenomenon:

> full absolute-cell covariance could differ greatly while fixed random ±1 projections appear much less different.

Investigate this carefully.

Do not treat projection agreement as sufficient evidence of absolute spatial covariance transportability.

Distinguish:

* anonymous aggregate variance structure;
* absolute spatial-location covariance structure.

Q1 ultimately operates on geographically meaningful cells.

---

# 47. Strengthen NC1

Retain the predeclared fixed incompatible different-state control.

Do not search for a worse control.

Extend it, where possible, from generic scalar to:

* domain profile;
* domain covariance;
* generic joint covariance.

Species-joint NC1 is optional only if computational burden is disproportionate.

---

# 48. Candidate versus NC1 interpretation

Compare candidate B9 pool versus fixed incompatible pool by:

* Level1/Level2;
* reference-strength class;
* scalar discrepancy;
* domain discrepancy;
* covariance discrepancy.

Do not reduce the result to one national percentage.

A result where candidate is only modestly better than NC1 is scientifically meaningful.

Report it.

---

# 49. Descriptive identity investigation

Investigate whether transport discrepancy is associated with:

* MANUAL;
* regional MANUAL;
* SAMP_METHOD_CD;
* MEASYEAR.

These remain descriptive variables.

Do not modify B9 filters.

For each comparison, explicitly inspect confounding by:

* Level1/Level2 route;
* state/EU;
* pool df;
* target df/reference strength;
* domain overlap;
* group-size imbalance.

---

# 50. Descriptive identity interpretation

B12 v01 suggested apparent differences such as stronger performance among some exact-match groups.

However exact-match groups were often small and structurally different.

Do not report an association as evidence for a hard filter unless the qualification evidence genuinely distinguishes it from confounding.

A scientifically valid outcome may be:

> visible descriptive signal, but insufficient evidence to modify compatibility rules.

---

# 51. Preserve species-specific degeneracy classes

Do not drop cases where:

* target variance = 0;
* pool variance = 0;
* target positive variance / pool zero;
* insufficient joint reference.

These are measurement outcomes.

They may themselves inform transportability.

---

# 52. Actual 24 singleton direct diagnostics

Retain all 24.

For each report:

* Level1/Level2;
* pool df;
* full5 parent n/df;
* generic scalar comparison;
* domain comparison;
* corrected covariance comparison where estimable;
* reference-noise strength;
* uncertainty/limitations.

Full five-panel evidence remains:

`FULL5_LIMITED_REFERENCE`

Never rename it “truth”.

---

# 53. Full5 firewall

Hard requirement:

full-five-panel target reference must not enter:

* pool construction;
* hard filters;
* prediction covariance;
* case exclusion;
* estimator selection;
* method tuning.

Prediction must be sealed before full5 reference scoring.

Demonstrate this in audit outputs.

---

# 54. No new estimator inside B12 v01_1

The evidence may suggest that directly transporting the entire domain×abundance covariance is too strong.

A possible future idea is to separate:

* abundance residual process;
* domain allocation process.

This is currently only:

`DESIGN CANDIDATE / HYPOTHESIS`

Do NOT implement it.

Do NOT compare competing factorized estimators.

If corrected evidence motivates such work:

> recommend a new, separately authorized investigation.

---

# 55. No hard pass threshold for transportability

Do not invent:

* 10% acceptable error;
* correlation cutoffs;
* acceptable TV threshold;
* required fraction of cases passing.

Return continuous evidence and natural structure.

Mainline will determine whether later formal qualification strata are justified.

---

# 56. Evidence layers to keep distinct

At minimum separate:

## Precision

How much information is in the pool?

Examples:

* residual df;
* number of strata;
* number of plots.

## Abundance-residual transport

How well does scalar abundance residual variance transport?

## Spatial/domain transport

How well does absolute cell allocation/covariance transport?

## Combined covariance transport

How well does abundance×domain covariance transport?

## Reference strength

How reliable is the held-out target covariance reference?

Do not compress these into one score.

---

# 57. Expected key scientific questions

The corrected evidence should allow Work to answer:

### Q1

Does B9 design compatibility translate into real residual-covariance transportability?

### Q2

Is Level1 materially more transportable than Level2, once reference noise is considered?

### Q3

Does Level2's large pool df compensate for cross-EU spatial mismatch?

### Q4

Does Level2's 50-km mismatch persist at 100/200-km diagnostic aggregation?

### Q5

Is Level1 spatially reasonable but abundance-residual transport still heterogeneous?

### Q6

Is species-specific transport substantially weaker than generic all-live-tree transport?

### Q7

How much target-pool covariance mismatch remains after accounting for target internal split-half covariance noise?

### Q8

Does the candidate B9 pool clearly outperform the fixed incompatible NC1 at domain and covariance levels?

### Q9

Do MANUAL/SAMP_METHOD/MEASYEAR differences provide credible evidence for future refinement, or only confounded descriptive signals?

### Q10

Does the corrected evidence support unchanged D10F-C, continued HOLD, or a new explicitly scoped methodological investigation?

Q10 is a recommendation.

Mainline retains authority.

---

# 58. Work self-audit requirement

Before returning results, perform an explicit independent self-audit of:

* object sealing;
* target leakage;
* full5 leakage;
* cache identity;
* protected parent evidence;
* eigensystem implementation;
* PSD computation;
* coarse-grid floor division;
* scoring completeness;
* output consistency.

Do not rely only on self-generated QC claims.

Where practical:

> recompute key metrics from final outputs using an independent path.

---

# 59. Protected reconciliation

Generate a v01 → v01_1 reconciliation.

Protected values must include at least:

* pseudo-target total = 5,729;
* scoreable = 4,640;
* heterogeneous/unscoreable = 1,089;
* scored Level1 = 4,397;
* scored Level2 = 243;
* actual singleton = 24;
* actual Level1/Level2 = 11/13;
* FIA SPCD = 402;
* target-member leak = 0;
* target species variance >0 = 55,923;
* target>0/pool>0 = 48,723;
* target>0/pool=0 = 7,200.

Any unexplained change:

> STOP.

---

# 60. Required outputs

Return a coherent qualification package.

At minimum include:

* `B12_MAIN_REPORT_v01_1.md`
* `B12_V01_TO_V01_1_RECONCILIATION_v01_1.csv`
* `B12_CACHE_REUSE_QC_v01_1.csv`
* `B12_FULL_COV_PREDICTION_SEAL_v01_1.parquet`
* `B12_REFERENCE_FIREWALL_QC_v01_1.csv`
* `B12_COV_REFERENCE_NOISE_v01_1.parquet`
* `B12_TRANSPORT_VS_REFERENCE_NOISE_v01_1.parquet`
* `B12_COVARIANCE_SPECTRAL_QC_v01_1.parquet`
* `B12_COVARIANCE_TRANSPORT_v01_1.parquet`
* `B12_COARSE_SPATIAL_TRANSPORT_v01_1.parquet`
* `B12_TRANSPORT_DECOMPOSITION_v01_1.parquet`
* `B12_NEGATIVE_CONTROLS_v01_1.csv`
* `B12_DESCRIPTIVE_IDENTITY_TRANSPORT_v01_1.csv`
* `B12_ACTUAL24_CORRECTED_COVARIANCE_v01_1.parquet`
* `B12_SUBGROUP_SUMMARY_v01_1.csv`
* `B12_OPEN_ITEMS_v01_1.csv`
* `B12_PROVENANCE_v01_1.csv`
* `B12_INVARIANT_QC_v01_1.csv`
* `B12_RUN_METADATA_v01_1.json`
* `SHA256SUMS.csv`
* `TRANSFER_MANIFEST_v01.csv`
* required code/config and concise execution logs

Final artifact:

`Q1_D10F_B12_v01_1.zip`

---

# 61. Scientific status discipline

Strictly distinguish:

* `FROZEN`
* `ACCEPTED EVIDENCE`
* `B12 EMPIRICAL QUALIFICATION EVIDENCE`
* `HYPOTHESIS`
* `DESIGN CANDIDATE`
* `OPEN`

Do not mix FROZEN and ACCEPTED EVIDENCE into one provenance status.

---

# 62. Prohibited final claims

Do NOT declare:

* B9 invalid as a whole;
* Level2 must be deleted;
* Level1 is production-qualified;
* MANUAL must become a hard filter;
* full5 is truth;
* factorization selected;
* D10F-C permanently rejected;
* abundance Gate permanently failed;
* Q1 infeasible.

---

# 63. Allowed final recommendations

Depending on evidence, Work may recommend:

* unchanged D10F-C remains on HOLD;
* corrected evidence is sufficient to reconsider D10F-C;
* a narrower transportability qualification is required;
* a new factorization investigation is scientifically warranted;
* Level1/Level2 should be treated as distinct evidence strata in future qualification;
* specific real-FIA structure requires further authority investigation.

Recommendations are not authorizations.

---

# 64. Universal code/handoff rule

If Work can complete the required investigation and computation directly in its authorized execution environment:

> do so.

If Work instead needs to hand user-run code back to the user:

do NOT paste source code in chat.

Generate a downloadable execution ZIP and explicitly state:

1. where to extract it;
2. which file to run;
3. where results will appear;
4. which exact result ZIP must be returned to Q1 mainline.

Use short Windows paths under `C:\range_paper\99_tmp\exec\...`.

The user should not have to manually configure or assemble the run.

---

# 65. STOP boundary

The task ends when the corrected B12 evidence package has been completed, self-audited, and returned to Q1 mainline.

Do NOT continue automatically into:

* D10F-C;
* factorized covariance development;
* support recovery;
* real Q1.

Return to Q1 mainline for scientific judgment.
