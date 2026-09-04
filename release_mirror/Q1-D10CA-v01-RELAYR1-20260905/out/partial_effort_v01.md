# D10C-A partial-effort authority v01

Terminal status: `ABUNDANCE_ESTIMATOR_AUTHORITY_CLOSED_READY_FOR_D10C`

## Unique resolution

The authority question is resolved without a new estimator branch:

- **P1 applies to the official FIA adjustment**: the selected-evaluation original stratum's `ADJ_FACTOR_SUBP` or `ADJ_FACTOR_MACR` enters the tree point estimator together with `TPA_UNADJ` and the D09C fold-specific TI replacement for `EXPNS`.
- `CONDPROP_UNADJ`, `SUBPPROP_UNADJ`, and `MACRPROP_UNADJ` are official condition/sample-area proportions used in area and nonsampling-adjustment semantics. They are upstream inputs/diagnostics, not an additional multiplier on each already condition-assigned TREE row.
- **P3 applies to D10A derived partial-effort fields**: `partial_sampling_flag`, sampled-subplot counts, and `partial_sampling_effort` are retained for precision and QC only. They do not change the point estimate.
- **P2 is rejected**: multiplying the tree contribution again by a condition proportion or by inverse D10A effort would duplicate sample-area/nonresponse correction.

The exact point contribution is therefore `TPA_UNADJ × official basis-matched ADJ_FACTOR × fold-specific TI`. A downstream implementation must fail rather than infer when a PLOT/COND/stratum join or macroplot-basis decision is non-unique.

Evidence is frozen in FIADB Guide v9.4 PDF pp. 79, 185, and 480-481 and National Field Guide v9.5 PDF pp. 41, 145, and 582.
