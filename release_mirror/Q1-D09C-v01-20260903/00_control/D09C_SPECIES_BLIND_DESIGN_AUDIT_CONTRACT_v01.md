# D09C species-blind reporting-state / whole-panel audit contract v01

Date: 2026-09-02  
Authority: Q1 scientific mainline  
Status: **FROZEN BEFORE FIADB DESIGN-METADATA COMPUTATION**

## 1. Bounded scientific object

D09C audits whether coherent FIA reporting-state frames and disjoint whole-`P2PANEL` A/B folds can be constructed with explicit fold-specific design bookkeeping. It is a sampling-design metadata audit, not a species analysis and not D08C2.

Only these FIADB tables may be read: `POP_EVAL_GRP`, `POP_EVAL_TYP`, `POP_EVAL`, `POP_ESTN_UNIT`, `POP_STRATUM`, `POP_PLOT_STRATUM_ASSGN`, `PLOT`, and `SURVEY`. No `TREE`, species-reference, species-crosswalk, Little/USGS, accepted-name, detection, abundance, occupancy, eligibility, or Q1-result table may be queried.

## 2. State universe and temporal frames

The universe is the 48 contiguous States in the frozen D09B State ledger.

- **T1:** exact official whole-State reporting group `STATE_FIPS + 2022` for every State.
- **T2:** exact official whole-State reporting group `STATE_FIPS + 2023`, except Montana, New Mexico, and Utah use their exact 2022 groups as ordered by mainline.

Group and component membership must be read from `POP_EVAL_GRP -> POP_EVAL_TYP -> POP_EVAL`. The required evaluation type is `EXPVOL`. Numeric EVALIDs may never be reconstructed from a naming convention. Texas group membership must remain the actual component membership recorded in the database.

`MEASYEAR` and `INVYR` are diagnostics only and never define either frame.

### State/frame status

- **PASS:** exact requested group exists; actual EXPVOL component membership is nonempty; all component-to-EU-to-stratum-to-plot joins close; P2PANEL values 1–5 occur; and no unresolved hard design defect exists.
- **CONDITIONAL:** official membership is closed but one or more explicit design exceptions remain (for example a multi-panel lineage or missing fold representation). The frame remains auditable, but mainline judgment is required.
- **FAIL:** group or EXPVOL membership is missing/guessed; required joins are broken; fewer than five P2PANEL identities are present; or a prohibited data source is accessed.

## 3. Observation unit and design census

The census unit is each unique evaluation-specific `POP_PLOT_STRATUM_ASSGN.PLT_CN` joined by official CN/EVALID keys to its component EVALID, estimation unit, poststratum, and PLOT design metadata. No plot-status or calendar-year filter is imposed. Duplicate assignment rows, missing join keys, null/invalid P2PANEL, zero/invalid parent design quantities, and missing public coordinates are reported explicitly.

The required ledger grain is:

`State x frame x component EVALID x estimation unit x poststratum x P2PANEL x SUBPANEL x MEASYEAR x INVYR`.

Parent stratum area is audited by both available identities:

- `A_h_EXPNS = POP_STRATUM.EXPNS * POP_STRATUM.P2POINTCNT`;
- `A_h_P1 = POP_ESTN_UNIT.AREA_USED * P1POINTCNT / sum(P1POINTCNT within EU)`.

Their relative difference is reported; no result-dependent tolerance is chosen. Exact numerical identity checks use the predeclared relative tolerance `1e-8`.

## 4. Whole-panel candidate enumeration

`P2PANEL` is indivisible. `SUBPANEL` is timing metadata only.

For every auditable State/frame, enumerate all `C(5,2)=10` candidates. Fold A is the ascending two-panel set; fold B is its ascending three-panel complement. No within-panel split is permitted.

A candidate is eligible for ranking only if no permanent plot lineage occurs in both folds. Multi-panel lineages are reported, never silently assigned. If all candidates have cross-fold lineage overlap, the State/frame is CONDITIONAL and all candidates remain in the full evidence table.

## 5. Predeclared design-only ranking

Eligible candidates are ranked lexicographically by the following frozen keys. No species identity or outcome may enter any key.

1. `missing_parent_area_any_acres = sum_h A_h * I(n_Ah=0 or n_Bh=0)` across component-EVALID x EU x poststratum blocks.
2. `design_block_representation_imbalance = area-weighted mean_h[abs(n_Ah/2 - n_Bh/3) / max((n_Ah+n_Bh)/5, 1)]`.
3. `temporal_center_abs_diff_years = abs(mean_MEASYEAR_A - mean_MEASYEAR_B)` over all assigned plots with nonmissing MEASYEAR.
4. `plot_cell_imbalance = plot_rate_imbalance + cell_rate_imbalance`, where each rate compares the per-panel A and B counts: `abs(x_A/2 - x_B/3) / max((x_A+x_B)/5, 1)`. Plot and 50-km cell components are also reported separately.
5. Ascending zero-padded A-panel identifier as deterministic tie-breaker.

The top-ranked row is a diagnostic recommendation only. D09C does not freeze any A/B assignment.

## 6. Time, spatial coverage, and lineage definitions

- Time summaries use actual `PLOT.MEASYEAR` and `PLOT.INVYR`: count, mean, median, minimum, maximum, standard deviation, and A-minus-B center differences.
- Public PLOT coordinates are projected to EPSG:5070 and assigned to the fixed 50-km grid with origin `(0,0)` meters by `floor(x/50000), floor(y/50000)`. This is a sampling-frame coverage diagnostic only; public-coordinate fuzzing/swapping remains an explicit caveat.
- A permanent lineage is the root obtained by following `PLOT.PREV_PLT_CN` recursively. Cycles, missing predecessor records, multiple P2PANEL identities, and top-candidate cross-fold appearances are exception-queued.

## 7. Fold-specific estimator audits

Only the top diagnostic candidate per State/frame is expanded for estimator bookkeeping. This does not select it for Q1.

### TI-style pooled selected-panel audit

For each fold and parent stratum, define `n_h,fold` from the selected complete panels and construct `EXPNS_TI_fold = A_h / n_h,fold` when `n_h,fold > 0`. The full-evaluation EXPNS is retained only as an audit comparator and is never reused as the final fold weight.

### MA-style complete-panel audit

For each complete panel and parent stratum, define `EXPNS_panel = A_h / n_h,panel` when represented. Within each fold, combine complete-panel constant-response calibration totals with equal positive panel weights `1/k` solely as a transparent design audit. This does not freeze MA weights for real Q1.

### Calibration and variance bookkeeping

- Synthetic constant response `1` must recover the represented parent area exactly within relative tolerance `1e-8`.
- Missing strata and their parent area are reported rather than imputed.
- Each TI fold and MA panel records sample counts, `n-1` variance degrees of freedom, whether within-stratum variance is estimable (`n>=2`), Phase-1/Phase-2 counts, nonresponse/sample-element adjustment fields, and the requirement to retain the official poststratification variance terms.
- No species response, tree total, precision threshold, or final variance estimator choice is introduced.

## 8. Hard PASS/FAIL rules

The computational execution is PASS only if:

1. all request, upstream ZIP, upstream member, and formal FIADB raw hashes match;
2. T1 and T2 each contain exactly 48 State audit rows and all actual group/component memberships are closed without guessing;
3. Texas component membership is explicitly obtained from actual database rows;
4. all 10 whole-panel candidates are emitted per State/frame, and no P2PANEL is split;
5. the SQLite read-authorizer/table-access ledger confirms no non-whitelisted or species-result table was read;
6. lineage overlap is zero for each ranked top candidate or is explicitly exception-queued with State/frame status CONDITIONAL;
7. fold-specific TI/MA weights are constructed from parent area and selected-panel counts; full-evaluation EXPNS is not reused unchanged as the final fold weight;
8. constant-response calibration identities pass within `1e-8` for represented strata;
9. no D08C2, Little/USGS, external search, final partition/cohort/threshold selection, or real-Q1 quantity is performed.

Scientific design feasibility may be **CONDITIONAL** even when execution is PASS; this occurs when the evidence package is complete but mainline must adjudicate temporal estimand, candidate partition, estimator family, coordinate uncertainty, or explicit design exceptions.

## 9. Frozen downstream order and STOP

`D09C -> mainline audit -> Range Gate 0 -> corrected D08C2 -> targeted Little/external-range review -> final cohort decision -> real Q1 after release`.

After the verified D09C package is delivered, STOP. D09C does not authorize any downstream stage.
