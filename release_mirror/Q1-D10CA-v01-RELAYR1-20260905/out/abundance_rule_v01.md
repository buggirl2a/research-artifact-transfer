# D10C-A abundance contribution rule v01

Task: `D10C_A_FIA_ABUNDANCE_ESTIMATOR_AUTHORITY_CLOSURE_v01`  
Terminal status: `ABUNDANCE_ESTIMATOR_AUTHORITY_CLOSED_READY_FOR_D10C`

This document freezes estimator authority only. No species outcome, D10C calibration, support repair, or real Q1 result was computed.

## Eligible tree record and tally basis

A downstream TREE row may contribute only when `STATUSCD = 1` and `DIA >= 5.0`. DBH and DRC taxa use the same `DIA` threshold and remain retained. The row must join uniquely to its PLOT, selected-evaluation stratum, condition, F0 cell, final design block, and fold-specific TI row.

For a fixed-radius core plot, trees at least 5 inches are tallied on the 24-foot-radius subplot; where `PLOT.MACRO_BREAKPOINT_DIA` is present and the tree reaches that threshold, the macroplot basis applies. The field guide defines the four-subplot layout and this diameter/basis rule. `TREE.TPA_UNADJ` is the stored number of trees per acre theoretically represented by that record and already embodies the record's sample geometry.

## Frozen formula

For target species `i`, qualifying TREE row `t` on plot visit `j`, final block `h`, fold `f`, and 50-km cell `x(j)`:

`a(t) = ADJ_FACTOR_MACR[h0]` when the official macroplot tally basis applies; otherwise `a(t) = ADJ_FACTOR_SUBP[h0]`, where `h0` is the original selected-evaluation stratum retained in the crosswalk.

`q_ijt = TPA_UNADJ_t * a(t)` trees per acre after the official selected-evaluation nonresponse adjustment.

`Y_ij = sum_t q_ijt` over qualifying rows of species `i` in plot visit `j`. Trees from multiple accessible forest conditions are summed after a unique `TREE.CONDID -> COND.CONDID` validation. Condition proportions are not multiplied into individual tree records.

`M_if(x) = sum_{j in fold f, x(j)=x} TI_hf * Y_ij`, where `TI_hf` is the D09C fold-specific acres-per-plot weight in this crosswalk. It replaces the original full-evaluation `POP_STRATUM.EXPNS`; it is not multiplied by that original `EXPNS`.

If `sum_x M_if(x) > 0`, normalize as `p_if(x) = M_if(x) / sum_x M_if(x)`. No plot-count divisor or state-average weight is added.

## Field roles

- `TPA_UNADJ`: tree-level trees-per-acre factor, including official plot/subplot geometry; never a population-total weight by itself.
- `ADJ_FACTOR_SUBP` / `ADJ_FACTOR_MACR`: official original-stratum nonsampling adjustment selected by the tree's official tally basis.
- `fold_specific_TI_weight`: D09C final block×fold area expansion and the only population-area expansion used here.
- `CONDID`: assignment/integrity key. `CONDPROP_UNADJ`, `SUBPPROP_UNADJ`, and `MACRPROP_UNADJ` describe condition/sample-area proportions and support FIA's area/adjustment construction; they are not extra per-tree multipliers.
- D10A `partial_sampling_flag` and `partial_sampling_effort`: precision/QC metadata only; no additional point-estimator multiplier.

## Frozen evidence

- FIADB Guide v9.4, PDF pp. 28-29: core subplot/microplot/macroplot `TPA_UNADJ` factors and separation of plot/sample geometry from population expansion.
- FIADB Guide v9.4, PDF p. 79: `CONDPROP_UNADJ` / `SUBPPROP_UNADJ` / `MACRPROP_UNADJ` are condition-area proportions; official adjustment factors address partial nonsampling.
- FIADB Guide v9.4, PDF p. 185: `TREE.TPA_UNADJ` is the theoretical trees-per-acre representation and must be adjusted with POP_STRATUM factors for population estimates.
- FIADB Guide v9.4, PDF pp. 480-481: `EXPNS` is population-area expansion; `ADJ_FACTOR_SUBP` and `ADJ_FACTOR_MACR`, with `EXPNS` and `TPA_UNADJ`, provide tree estimates for sampled land.
- National Field Guide v9.5, PDF pp. 41, 145, 582: four 24-foot-radius core subplots; DBH/DRC diameter semantics; trees at least 5 inches are tallied on subplot/macroplot and macroplot breakpoint is regional.
