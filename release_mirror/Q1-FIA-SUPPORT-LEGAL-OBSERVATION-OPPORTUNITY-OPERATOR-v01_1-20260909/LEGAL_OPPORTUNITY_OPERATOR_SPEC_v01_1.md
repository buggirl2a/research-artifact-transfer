# Legal observation-opportunity operator specification — v01_1

Provenance: `PROJECT-INDUCED CANDIDATE LAYER 3 OPERATOR`. Status: candidate, not frozen.

Rule fingerprint: `84bef3e5f0103d0b28f080fa461577559e8c715314c68f58dfcd94d82c7e24ba`

## Unit and firewall

The classification unit is one frozen F0 plot visit. Direct opportunity is resolved through the species-blind chain:

`F0 visit × field method × directly examined sampled subplot × linked accessible forest condition × applicable diameter/tally frame`.

The operator never queries TREE, SPCD, species outcomes, support, nondetection, abundance, coordinates, or A2.

## Deterministic rule order

1. Bind exactly one Layer 1 `PLOT.CN` to each F0 `PLT_CN`; otherwise retain `UNRESOLVED_PLOT_SOURCE_BINDING`.
2. Validate `PLOT_STATUS_CD` against accepted codes; missing/other is unresolved. Plot status remains present in the full classification.
3. Interpret `SAMP_METHOD_CD` before choosing the terminal no-opportunity label: code 2 is explicitly retained as remote/non-field and has no direct tree opportunity.
4. For non-remote records, `PLOT_STATUS_CD=3` has no direct opportunity and code 2 has no Q1 forest opportunity; for `PLOT_STATUS_CD=1`, missing/other sampling method is unresolved and code 1 continues.
5. Interpret `SUBP_EXAMINE_CD`: code 1 limits direct scope to subplot 1; code 4 identifies subplots 1–4 as fully described. It does not create independent repeat-detection occasions.
6. Require one unique accepted `SUBP_STATUS_CD` for each directly examined element. Code 1 contributes sampled-accessible opportunity; codes 2/3 do not. Missing/duplicate/other remains unresolved.
7. Use the retained `SUBP_COND` relationship to require at least one `COND_STATUS_CD=1` condition linked to a sampled direct element. Missing/ambiguous linkage or condition status remains unresolved.
8. If `MACRO_BREAKPOINT_DIA>5`, use subplot opportunity for `5<=DIA<breakpoint` and macroplot opportunity for `DIA>=breakpoint`. If a positive breakpoint is `<=5`, the whole frozen target is in the macroplot frame.
9. For a positive breakpoint, every linked accessible condition used by the operator must retain `PROP_BASIS=MACR` and numeric `MACRPROP_UNADJ`; otherwise retain `UNRESOLVED_MACRO_CONDITION_BASIS`.
10. If no positive breakpoint is present, retain `UNRESOLVED_DIAMETER_FRAME_NO_POSITIVE_BREAKPOINT`. Do not infer subplot-only opportunity.
11. Preserve every F0 row. Never promote remote, inferred, nonsampled, nonforest, missing, or unresolved states to species nondetection.

## Interpretation boundary

A fully classified direct-opportunity state establishes only where a later method may evaluate a species encounter/nondetection. It is not itself detection, nondetection, biological absence, support, or abundance. Condition proportions remain representation metadata and are not multiplied into A2.

Observed qualification: F0=338,619; fully classified=219,709; explicitly unresolved=118,910.
