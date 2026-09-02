# D09 FIA OPEN DECISIONS FOR SCIENTIFIC MAINLINE v01

**Generated:** 2026-09-02  
**Source-closure status:** PASS  
**Real Q1:** HOLD

Only decisions that remain after factual closure are listed here.

## 1. Temporal design object for the frozen 2017–2023 scientific window

**FACT:** 2017–2023 is not one coherent nationwide official FIA evaluation; State EVALID windows differ.

**MAINLINE DECISION / FUTURE BOUNDED TEST:** decide whether to:
- anchor each State to a coherent official EVALID and accept differing measurement spans;
- build a custom calendar-2017–2023 design object with recalibrated strata/weights;
- or authorize another explicitly defined temporally synchronized design.

D09 does not choose among these.

## 2. A/B cross-fitting as a second-phase sample

**FACT:** full-evaluation EXPNS/weights cannot be reused unchanged after arbitrary ~50% plot thinning if design-based population totals are intended.

**MAINLINE DECISION / FUTURE BOUNDED TEST:** freeze a survey-design treatment for A/B:
- fold inclusion probability;
- fold-specific effective n and n_h;
- fold-specific expansion/recalibration;
- variance estimator;
- balance requirements across design blocks.

A candidate split within State × coherent EVALID × estimation unit × stratum (and potentially panel) is a design-preserving **inference**, not an official FIA recipe. It must be tested/contracted before implementation.

## 3. 50-km spatial membership with public coordinates

**FACT:** public FIA coordinates are fuzzed and some private forest plots are swapped.

**MAINLINE DECISION:** determine acceptable spatial-domain treatment:
- accept public-coordinate approximate membership with a predeclared boundary-uncertainty sensitivity;
- seek an FIA Spatial Data Services solution when operationally available;
- or define another design-consistent coarse-domain procedure.

D09 does not choose.

## 4. Basic domain estimate versus explicit 50-km area control

**FACT:** FIA supports basic domain estimation without rebuilding cell-specific P1 strata. FIA also describes explicit area-control options: new poststratification at desired population scale or ratio-to-known-domain-area.

**MAINLINE DECISION:** decide whether Q1 requires:
- basic domain total under parent EUs/strata;
- or explicit known-area control at 50-km cell scale.

No choice made here.

## 5. Precision / minimum sample gate

**FACT:** sparse domains can have unstable/high sampling error. Published FIA sample-size recommendations are variable-specific and are not a universal threshold for species-level 50-km tree totals.

**FUTURE BOUNDED TEST:** predefine diagnostics for per-cell/per-fold n, n_h, effective sample size, SE/CV behavior, zero-domain sampling, and a PASS/FAIL gate before real Q1.

## 6. Macroplot handling in the frozen large-tree tally

**FACT:** >=5-inch trees are not universally all subplot-weighted; where a macroplot design applies, trees above `PLOT.MACRO_BREAKPOINT_DIA` require `ADJ_FACTOR_MACR`.

**IMPLEMENTATION CONTRACT REQUIRED:** future estimator implementation must select the official sampling element per record rather than applying one universal large-tree expansion constant.

## 7. No final estimator has been selected

D09 establishes what is design-consistent and what is not. It does not authorize:
- a final point estimator;
- a final temporal evaluation window;
- a final fold weighting recipe;
- a final cell precision threshold;
- or any real Q1 run.

**STOP and return to scientific mainline.**