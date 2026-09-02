# D09B result note v01

Status: **PASS factual closure; MAINLINE DESIGN DECISIONS remain**

## Bottom line

1. Current official metadata supplies a whole-State 2023 evaluation group for **45/48 CONUS States**. Montana, New Mexico and Utah lack 2023 groups and currently stop at 2022.
2. `PLOT.P2PANEL` is a five-panel design identity, not a nationally synchronized calendar-year variable.
3. Current FIADB `SUBPANEL` means that in RMRS, PNWRS, and part of Oklahoma, each P2PANEL is split into two subpanels; one subpanel is usually scheduled per year.
4. FIA explicitly supports design-based estimation from one complete panel.
5. FIA officially documents MA and TI methods for combining complete panels but does not prescribe one universal core panel-combination procedure.
6. Reusing full-evaluation `EXPNS` unchanged after selecting only A or B panels is not supported.
7. Complete-panel A/B cross-fitting is **conditionally feasible as a Q1 survey-design construction**, not an FIA-prescribed procedure.
8. A 2-panel fold and a 3-panel fold can each be spatial probability-sample estimators after correct fold-specific treatment, but they do not automatically share the same temporal estimand.
9. No final panel grouping, temporal exception rule, or estimator was selected.

STOP. No eligibility census, Little processing, or real Q1 was run.


- Texas: whole-State 2023 evaluation group `482023` exists, but official update history shows separate East/West 2023 component data. Exact component EXPVOL EVALID membership is **not closed by the public `wc` table** and must be read from local `POP_EVAL_TYP/POP_EVAL` before computation. Do not assume a single `482301`.
