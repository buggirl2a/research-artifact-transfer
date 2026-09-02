# Q1 WORK REQUEST D09C — SPECIES-BLIND REPORTING-STATE + WHOLE-PANEL FOLD AUDIT v01

Date: 2026-09-02
Role: bounded computational branch
Authority: Q1 scientific mainline

## Mission

Perform a species-blind, design-only audit that determines whether a coherent nationwide FIA reporting-state frame and disjoint whole-P2PANEL A/B folds can be constructed with defensible fold-specific design weights and variance bookkeeping.

This is NOT D08C2 and NOT a species analysis.

Use as authority:
- D09 factual-closure package;
- D09B factual-closure package;
- Q1_D09B_MAINLINE_DECISION_v01_20260902.md;
- frozen FIADB database and design tables already under project control.

## A. Temporal frames to audit

Audit both:

T1 — uniform 2022 whole-State reporting-year frame:
- determine from actual local/frozen POP_EVAL_TYP / POP_EVAL / POP_EVAL_GRP metadata whether all 48 CONUS States have coherent whole-State 2022 EXPVOL/resource evaluation group membership;
- do not reconstruct or guess EVALIDs from naming convention alone.

T2 — latest official whole-State state at or immediately before 2023:
- 2023 where a whole-State 2023 group exists;
- 2022 for Montana, New Mexico, and Utah;
- Texas 482023 must use actual group/component membership from POP_EVAL_TYP / POP_EVAL, preserving East/West components as required.

Return PASS/FAIL/CONDITIONAL for each State under each frame.

Do not use MEASYEAR filtering as the definition of a design frame.

## B. Freeze P2PANEL as indivisible provisional fold atom

For this audit:
- no P2PANEL may be split between A and B;
- SUBPANEL is metadata only for timing/schedule diagnostics;
- do not use a SUBPANEL as an A/B atom.

## C. Build the design metadata census

For every State and each viable temporal frame, build a design-only table at least at:

State × reporting frame × component EVALID × estimation unit × poststratum × P2PANEL × SUBPANEL × MEASYEAR/INVYR.

Report:
- plot/primary-lineage counts;
- parent stratum area/weight information;
- P1/P2 counts needed for design reconstruction;
- EXPNS and adjustment metadata;
- measurement-year center/spread;
- missing or zero cells;
- regional work-unit/subpanel class.

Verify actual join keys and membership from FIADB design tables.

## D. Lineage audit

Using stable physical plot lineages / PREV_PLT_CN logic, verify whether whole-P2PANEL assignment yields disjoint A/B permanent-plot lineages.

Any lineage appearing in more than one P2PANEL within the chosen frame must be explicitly reported and treated as a design exception. Do not silently assign it.

## E. Enumerate all whole-panel A/B candidates

For each State/frame, enumerate all labeled 2-vs-3 P2PANEL partitions.

For each candidate calculate design-only diagnostics, including:
- estimation-unit/poststratum representation in each fold;
- parent design area/weight absent from either fold;
- fold plot-count/effective-sample imbalance by design block;
- actual measurement-year mean/median/range or other transparent timing summaries;
- A-vs-B temporal-center difference;
- sampling-frame 50-km cell coverage for all plots, without any species field;
- A/B cell-count imbalance and overlap;
- lineage overlap count.

No species outcome or species identity may be read for ranking.

## F. Predeclared candidate ranking

Rank candidates lexicographically by:

1. smallest parent design area/weight in EU × poststratum combinations absent from either fold;
2. smallest design-block representation imbalance;
3. smallest A-vs-B temporal-center discrepancy;
4. smallest total plot / 50-km sampling-cell coverage imbalance;
5. deterministic panel-ID ordering as tie-breaker.

Return full candidate tables and top-ranked candidate(s), but DO NOT freeze a final partition.

## G. Fold-specific estimator reconstruction

For each top candidate, reconstruct design bookkeeping for A and B without using species outcomes.

Full-evaluation EXPNS may not be reused unchanged.

At minimum audit two estimator families supported by D09B facts:

1. TI-style pooled selected-panel estimator under coherent poststratification;
2. MA-style combination of complete-panel estimates.

For each family document:
- point-weight construction;
- fold-specific n and n_h treatment;
- stratum/EU area calibration;
- nonresponse/sample-element adjustment handling;
- variance inputs;
- how multiple EUs/State components are combined;
- whether the 2-panel and 3-panel folds target the same stated reporting-state object or only different temporal averages.

Use synthetic constant responses / known-area calibration identities where useful. Do not run tree-species totals.

## H. Required PASS/FAIL diagnostics

At minimum:
- all input hashes and upstream authority verified;
- no guessed EVALID membership;
- T1 and T2 State coverage explicitly closed;
- Texas component membership explicitly closed;
- P2PANEL never split;
- no species table/outcome used for ranking;
- lineage overlap explicitly zero or exception-queued;
- fold-specific weight calibration checked;
- no full-evaluation EXPNS reused unchanged as final fold weight;
- no Little/USGS processing;
- no real Q1 computation.

Do not invent a numerical sample-size/precision threshold in this audit.

## I. Required outputs

Produce at minimum:

- D09C_RESULT_NOTE_v01.md
- D09C_TEMPORAL_FRAME_AUDIT_v01.csv
- D09C_EVALID_COMPONENT_LEDGER_v01.csv
- D09C_PANEL_SUBPANEL_YEAR_LEDGER_v01.csv
- D09C_WHOLE_PANEL_PARTITION_CANDIDATES_v01.csv
- D09C_TOP_PARTITION_DIAGNOSTICS_v01.csv
- D09C_LINEAGE_CROSSFOLD_AUDIT_v01.csv
- D09C_TI_FOLD_WEIGHT_AUDIT_v01.csv
- D09C_MA_FOLD_WEIGHT_AUDIT_v01.csv
- D09C_DESIGN_CALIBRATION_AUDIT_v01.csv
- D09C_OPEN_DECISIONS_FOR_MAINLINE_v01.md
- QC, manifest, SHA-256 ledger, reproducibility code/logs, and audit workbook if useful.

## J. STOP boundary

Do not:
- run D08C2;
- use accepted species identities for partition selection;
- calculate species detection/abundance/frontiers;
- process Little/USGS;
- search external range maps;
- select a final A/B partition;
- select a final eligibility threshold;
- run R1/R2, World 0, paired null, prediction, significance, or real Q1.

After the design-only evidence package is complete, STOP and return to scientific mainline.
