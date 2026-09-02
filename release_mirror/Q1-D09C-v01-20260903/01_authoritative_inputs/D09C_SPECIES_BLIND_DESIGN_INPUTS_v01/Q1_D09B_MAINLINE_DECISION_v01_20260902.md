# Q1 D09B MAINLINE DECISION v01

Date: 2026-09-02
Project: Q1 species-range internal structure
Authority: scientific mainline / PI

## Verdict

D09B factual closure: PASS.
Real Q1 remains HOLD.

## 1. Temporal reporting-state decision

The mainline does NOT yet freeze a literal 48-State “2023 evaluation” because current official metadata contain no whole-State 2023 evaluation group for Montana, New Mexico, or Utah.

A design-only bounded audit shall compare two outcome-blind temporal frames before the final temporal object is frozen:

- T1: a uniform whole-State 2022 reporting-year frame, if coherent official whole-State 2022 resource-evaluation groups exist for all 48 CONUS States in the frozen/local FIADB metadata;
- T2: the latest coherent whole-State reporting state available at or immediately before 2023: 2023 for the 45 States with a whole-State 2023 group, and 2022 for Montana, New Mexico, and Utah.

Preference rule is predeclared: if T1 is fully available and internally coherent for all 48 States, it is preferred on synchronization grounds unless the design audit identifies a concrete metadata/design defect that makes it inferior. Otherwise T2 is retained as the fallback contemporary reporting-state frame.

No calendar-year MEASYEAR filter may substitute for an official/coherent evaluation object.

Texas 482023 must be resolved from actual POP_EVAL_TYP / POP_EVAL membership; no guessed single EVALID is permitted.

## 2. A/B atomic design unit

Freeze P2PANEL as the provisional indivisible A/B atom for the next audit.

Reason: D09B found official support for design-based estimation from one complete P2PANEL, whereas one SUBPANEL alone in subpaneling regions remains unsupported/unknown as a nationwide complete-panel estimator. SUBPANEL is retained only as design metadata for schedule/time auditing and must not be silently substituted as the cross-fitting atom.

No P2PANEL may be split between A and B in the next audit.

## 3. Candidate panel partitions

Each State has five P2PANEL identities. The next bounded audit shall enumerate every labeled 2-vs-3 whole-P2PANEL split compatible with the chosen temporal frame. State-specific assignments are allowed because FIA regional schedules differ, but only design variables may be used.

No species identity, species detection, species abundance, Little/USGS information, range geometry, or Q1 outcome may enter partition evaluation.

## 4. Design-only ranking criteria

Candidate partitions are to be diagnosed, not automatically frozen as final. Rank them using the following predeclared hierarchy:

1. minimize parent design area/weight represented by estimation-unit × poststratum combinations that are absent from either fold;
2. minimize fold imbalance in estimation-unit/poststratum sample representation after accounting for the 2-vs-3 panel structure;
3. minimize A-vs-B temporal-center discrepancy using actual P2PANEL/SUBPANEL measurement-year membership;
4. minimize total sampling-frame and 50-km sampling-cell coverage imbalance between folds;
5. use deterministic identifier ordering only as a final tie-breaker.

Return the full candidate table and the top-ranked candidate(s). Do not declare the final A/B partition; mainline will freeze it after audit.

## 5. Fold-specific estimation audit

Full-evaluation EXPNS must not be reused unchanged for a subset of panels.

For each candidate fold, reconstruct the design bookkeeping needed for a valid fold-specific estimator, including estimation-unit/poststratum membership, fold-specific sample sizes, area weights/expansion, nonresponse/sample-area adjustments, and variance inputs.

At minimum compare:

- TI-style pooled selected-panel estimation under coherent poststratification;
- MA-style combination of complete-panel estimates.

No species estimator is to be run. Use design-only calibration identities / synthetic constant responses where needed to test whether fold weights recover known parent areas/totals.

## 6. Temporal estimand

The intended scientific object remains a contemporary FIA reporting-state / survey-cycle population-mass surface, not an exact single-date census.

The next audit must quantify how much the candidate A and B folds differ in measurement-year center and spread. The mainline will decide whether that difference is acceptable before real Q1.

## 7. Required metadata closures

Before any corrected eligibility census:

- close actual POP_EVAL_TYP / POP_EVAL resource-evaluation membership for every State frame used;
- close Texas 482023 East/West component membership;
- map State × evaluation × estimation unit × poststratum × P2PANEL × SUBPANEL × MEASYEAR/INVYR;
- verify permanent plot lineages do not cross A/B under whole-panel assignment;
- preserve regional SUBPANEL information without treating it as the A/B atom.

## 8. Downstream boundary

D08C2, Little review, external range completion, final eligibility threshold, final paper cohort, abundance surfaces, R1/R2, World 0, paired-null, and real Q1 remain HOLD until this design-only audit returns and mainline freezes the temporal frame, A/B partition, and fold estimator.

STOP.
