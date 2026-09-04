# D10C abundance-estimator authority audit v01

Terminal status: `INPUT_BLOCKED_ABUNDANCE_ESTIMATOR_AUTHORITY_FAILURE`

## Authoritative logic that is available

The accepted D09C design freezes fold-specific TI at the effective-design-block level. For selected fold `f` and effective block `h`, every sampled plot in that block would receive:

`w_hf = effective block population area / actual fold sample count`.

The final table contains 5,752 block × fold rows, preserves population area, and explicitly forbids reuse of full-evaluation EXPNS as the final fold weight. The 48 selected whole-panel partitions are also present.

## Missing authority that blocks A2

The final TI table has no plot identifier. The D10A F0 layout has `plot_cn`, `cell_50km`, and `fold`, but no assignment, stratum, estimation-unit, or effective-design-block identifier. The predecessor aggregate panel ledger has stratum identifiers without individual plot identifiers; its lineage audit has plot-visit lists without design-block identifiers. Embedded raw `POP_PLOT_STRATUM_ASSGN` design ZIPs cover only CA, OR, WA (3/48 states), not the national F0 frame. The WV merged-domain output is likewise not a complete plot-level crosswalk.

D09C also does not freeze how D10A's partial condition/subplot effort should enter the intended real abundance response or per-plot contribution. Consequently the packages do not define the exact nationwide join:

`F0 PLT_CN -> selected final effective design block -> fold-specific TI weight -> real-branch plot contribution`.

## Governance consequence

Using state-average weights, inverse cell sample size, coordinate matching, local un-packaged FIA tables, or any newly invented effort correction would change estimator authority. The D10C contract forbids those substitutions. Therefore no T_i rule was activated, no synthetic observations were generated, and A0/A1/A2 recovery or downstream results were computed.

Mainline can unblock D10C by freezing a nationwide plot-level selected-design crosswalk and the exact plot-contribution/partial-effort rule. This audit does not prescribe which rule to choose.
