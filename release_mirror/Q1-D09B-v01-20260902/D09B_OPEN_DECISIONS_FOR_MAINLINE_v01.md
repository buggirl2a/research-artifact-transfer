# D09B open decisions for Q1 scientific mainline v01

Date: 2026-09-02  
D09B factual-closure status: **PASS**  
Real Q1: HOLD

Only decisions not resolved by FIA facts are listed here.

## 1. Three-State reporting-year exception — MAINLINE DECISION REQUIRED

Current FIADB-API metadata contains no whole-State 2023 evaluation group for:

- Montana — latest published group `302022`, member years 2013–2022;
- New Mexico — latest published group `352022`, member years 2015–2022;
- Utah — latest published group `492022`, member years 2013–2022.

The other 45 CONUS States have a whole-State 2023 group.

Therefore the frozen phrase “State-specific coherent FIA 2023 evaluation state” cannot be implemented literally for all 48 States from the current official metadata. Mainline must define a deterministic exception rule before a corrected eligibility census.

D09B does **not** choose the rule.

## 2. Atomic A/B design unit — MAINLINE DECISION REQUIRED

Current FIADB uses five `P2PANEL` values, but RMRS, PNWRS and part of Oklahoma further divide each P2PANEL into two `SUBPANEL`s.

Mainline must decide—after a bounded design-only audit—whether the cross-fitting atom is:

- full P2PANEL,
- complete scheduled SUBPANEL where subpaneling is used,
- or another explicitly defined complete design unit.

A nationally uniform assumption “P2PANEL = annual panel” is ruled out.

## 3. Temporal estimand of A/B folds — MAINLINE DECISION REQUIRED

A complete panel is a valid probability sample spatially. However:

- MA estimates a weighted temporal average across selected panels;
- TI pools panels over a cycle and explicitly is not a specific-year estimate;
- 2-panel and 3-panel folds can therefore have different temporal centers.

Mainline must state what it means for both folds to estimate the “same 2023 reporting-state population” and what temporal-stability/temporal-averaging assumption is acceptable.

## 4. Fold-specific design estimator — FUTURE BOUNDED DESIGN TEST

Full-evaluation `EXPNS` cannot be reused unchanged after taking only selected panels.

A bounded, species-blind computational audit should reconstruct for each candidate fold:

- chosen State/evaluation membership;
- estimation units;
- poststrata and known stratum areas/weights;
- fold-specific plot sample sizes and nonresponse/sample-area adjustments;
- fold-specific point-estimate weights;
- official-design variance components.

It should compare MA-style independent panel estimates and TI-style pooled selected-panel estimates without using species outcomes.

D09B does not choose MA or TI.

## 5. Panel partition rule — MAINLINE DECISION AFTER DESIGN AUDIT

Candidate outcome-blind rules include:

- fixed odd/even P2PANEL;
- deterministic whole-panel allocation balancing design-level plot counts / stratum representation;
- State-specific deterministic rules where design schedules differ.

None is FIA-prescribed as a cross-fitting rule. No final grouping is selected here.

## 6. Panel/year and lineage audit — FUTURE BOUNDED DESIGN TEST

Current `wc` metadata lists evaluation member years but not the `P2PANEL/SUBPANEL → measurement year` map.

Before freezing A/B:

- tabulate State × EVALID × P2PANEL × SUBPANEL × MEASYEAR/INVYR;
- audit estimation-unit/poststratum representation by candidate fold;
- verify `PREV_PLT_CN`/stable plot lineages do not cross folds;
- document panel creep or mixed completion years.

This audit must remain species-outcome blind.

## 7. No Little / no species thresholds yet

The corrected design gate precedes D08C2. Little review, final eligibility threshold, final cohort and real Q1 remain HOLD.


## Texas component EVALID membership

**Status: FUTURE BOUNDED DESIGN TEST / REQUIRED BEFORE COMPUTATION**

The official `wc` table confirms a whole-State 2023 group `482023` covering 2014–2023. However, current FIADB update history records separate additions/corrections for `482023 (EAST)` and `482023 (WEST)`. The `wc` table alone does not expose the underlying `POP_EVAL_TYP`/`POP_EVAL` component EVALID membership.

Therefore the mainline must **not** reconstruct a guessed single Texas EVALID such as `482301`. Before D08C2, a bounded local database audit must read the actual `482023` group membership and preserve all required EXPVOL components and their estimation-unit/stratum metadata.

This is a design-metadata closure task only; no species outcomes are needed.
