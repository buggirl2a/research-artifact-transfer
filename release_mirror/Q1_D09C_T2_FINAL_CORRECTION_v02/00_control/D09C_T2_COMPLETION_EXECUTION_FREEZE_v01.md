# D09C T2 bounded completion execution freeze v01

Date: 2026-09-03  
Authority: `Q1_D09C_T2_BOUNDED_COMPLETION_CONTRACT_v01`  
Contract SHA-256: `6a9955890c43d518a2bddac27e889eda908c4a32cbc87dae43604c7c2c7b1885`  
Status: **FROZEN BEFORE D09C T2 COMPLETION COMPUTATION**

## Bounded object

This execution closes only the species-blind FIA T2 `EXPVOL` survey-design layer for the frozen 48-State frame: 2023 for 45 States and 2022 for MT/NM/UT. T1 is dropped and is not recomputed or compared. Existing D09C v01 products remain immutable.

The only scientific inputs are frozen D09C T2 design outputs for the 45 already-closed States and the frozen CA/OR/WA raw design tables (`POP_EVAL_GRP`, `POP_EVAL_TYP`, `POP_EVAL`, `POP_ESTN_UNIT`, `POP_STRATUM`, `POP_PLOT_STRATUM_ASSGN`, `PLOT`, `SURVEY`). No TREE, species, abundance, detection, occupancy, range, trait, climate, R1/R2, World 0, or real-Q1 object may be read.

## Frozen partition and estimator rules

- Enumerate exactly ten `A=2 whole P2PANEL` versus complementary `B=3 whole P2PANEL` candidates per State.
- Rank mechanically by: design validity/estimability; area-weighted balance over effective within-EU design blocks; temporal balance; ascending A-panel tuple.
- If either fold lacks a parent poststratum, coarsen both folds symmetrically to the estimation-unit level for that EU and preserve 100% of its population area.
- If either fold remains unsampled at EU level, the candidate is design-blocked. No population area may be discarded.
- Primary estimator audit is fold-specific TI. Full-evaluation `EXPNS` is a comparator only and is never reused as the fold weight.
- MA is feasibility-only and cannot determine the primary design.
- OR 412301 assignment/PLOT STATECD or INVYR mismatches are retained when `PLT_CN -> PLOT.CN` resolves; SURVEY `STATECD+INVYR` is not required to be unique.

## Frozen PASS/FAIL criteria

Nationwide PASS requires all of the following without post-hoc threshold changes:

1. Exactly 48 real T2 EXPVOL component frames close from frozen keys, including CA 62301, OR 412301, and WA 532301.
2. Every State has P2PANEL identities 1-5 and exactly ten 2-vs-3 candidates.
3. At least one candidate per State has no EU-level unsampled fold after the symmetric-coarsening rule.
4. The rule-selected candidate in every State preserves all population area and has closed fold-specific TI construction for both A and B.
5. No full-evaluation EXPNS is reused as a final fold weight; constant-response area identities close within relative tolerance `1e-8`.
6. The OR mismatch ledger contains the exact retained records reached by `PLT_CN -> PLOT.CN`; no SURVEY false-duplicate criterion is applied.
7. No prohibited scientific data or downstream analysis is accessed.

Any missing real EXPVOL component is `INPUT_BLOCKED`. Any State with no legal 2-vs-3 candidate, any selected fold unsampled at EU level, any need to discard population area, or any need to violate the whole-panel rule is `DESIGN_BLOCKED`. These criteria are frozen before computation and will not be changed to obtain PASS.

