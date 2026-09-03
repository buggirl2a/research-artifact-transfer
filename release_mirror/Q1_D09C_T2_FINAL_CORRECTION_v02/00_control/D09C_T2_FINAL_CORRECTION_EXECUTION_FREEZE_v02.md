# D09C T2 final design correction execution freeze v02

Date: 2026-09-03  
Authority: `Q1_D09C_T2_FINAL_DESIGN_CORRECTION_CONTRACT_v02`  
Contract SHA-256: `ee3d958d15e74bc54a1b8fc91b2870bf4eb89304f1ed684f980dd8bd4a9fe351`  
Predecessor ZIP SHA-256: `25f361eeeddbe02fd2f93d2daa0b0e974926a8d97965505a3bec37a65388ea7e`  
Status: **FROZEN BEFORE V02 CORRECTION COMPUTATION**

## Immutable predecessor

The accepted v01 package remains unchanged. V02 may reuse its verified 48-State EXPVOL frame, 480 candidates, design-only ledgers, and whitelisted raw-design inputs, but writes only to new `d09c_t2_final_correction_v02` paths.

## Repair-class hierarchy

Candidates are classified before balance ranking:

- `R0_NATURAL_STRATIFICATION_VALID`: no parent-poststratum missing in either fold, no coarsening, 100% area preserved, TI estimable.
- `R1_WITHIN_EU_SYMMETRIC_COARSENING_VALID`: native poststrata incomplete, but symmetric within-EU coarsening closes both folds with 100% area and no EU-level zero fold.
- `R2_SPARSE_EU_FALLBACK_VALID`: considered only when the State has no R0 or R1 candidate and a partner is resolved before partition construction from full-frame, outcome-blind design metadata.
- `R3_BLOCKED`: remains non-estimable after permitted repairs.

State selection first chooses the lowest available repair class (R0, then R1, then R2). Within that class only, candidates use the frozen strict lexicographic balance tuple, then temporal tuple, then ascending A-panel tuple. Repair magnitude is never included in the balance score.

## WV partner resolution frozen before coordinate inspection

Admissibility is limited to another WV estimation unit in EVALID 542301 with complete required keys and at least one valid full-frame sample.

1. Semantic class is assigned only by the transparent exact pattern `^Inland Census Water Unit [0-9]+$`; Unit 3 itself is excluded.
2. If exactly one admissible unit shares this class, it is the partner.
3. If multiple units share the class, geographic proximity is operationalized from the frozen full-five-panel `POP_PLOT_STRATUM_ASSGN.PLT_CN -> PLOT.CN` records. For each EU, compute the arithmetic centroid of all nonmissing public PLOT latitude/longitude records and the haversine distance from Unit 3's centroid. The unique strict minimum among same-class admissible units is selected. No unit number, plot count, area, candidate balance, time balance, species, or outcome enters the choice.
4. Public-coordinate fuzzing is retained as a diagnostic caveat. No proximity tolerance is invented: an exact minimum tie or missing usable coordinates returns `MERGE_PARTNER_AMBIGUOUS_NEEDS_MAINLINE`.
5. No frozen pixel/design-category field is available beyond the unit description; pixel similarity is therefore reported unavailable and is not imputed.

If no same-class candidate exists, return `MERGE_PARTNER_NOT_RESOLVED_FROM_FROZEN_DESIGN_METADATA`. No cross-class merge is permitted.

## R2 construction and PASS/FAIL

Only if a unique partner closes may Unit 3 and that partner be replaced, before A/B enumeration, by one common merged design domain. All their source strata and areas are retained; both folds use the identical merged block. Other EUs continue under the symmetric within-EU rule. Each fold weight is reconstructed as merged/effective-block area divided by its actual fold sample count. Full-evaluation EXPNS is comparator-only.

V02 may return `PASS_READY_FOR_MAINLINE_FINAL_D09C_AUDIT` only if all 48 States have a legal selected candidate, 100% area is preserved, all TI folds close within `1e-8`, and all required QC passes. Otherwise it returns only the contract-authorized blocked/ambiguous status. No criterion may be changed after results are seen.

