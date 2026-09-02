# Q1 WORK REQUEST D08C1 v01
## FIA accepted-species eligibility rebuild before Little final closure

Date: 2026-09-02

## Authority

Use D08B1 v02 as downstream taxonomy authority, especially:
- Q1_FIA_CODE_TO_ANALYSIS_SPECIES_v02.csv (396 unique FIA codes)
- Q1_ANALYSIS_SPECIES_MASTER_v02.csv
- Q1_GLOBAL_RANGE_FLAGS_v02.csv
- Q1_WCVP_NATIVE_DISTRIBUTION_LONG_v02.csv
- Q1_DRC_PROTOCOL_v02.csv

Preserve all frozen D04 / eligibility-v0.2 continuity rules for CONUS domain, lineage de-duplication, fixed EPSG:5070 grids, 25/50/75-km origin and A/B split.

## Mission

Rebuild the outcome-blind FIA eligibility census from bottom-level unique FIA TREE records after applying the accepted-species mapping. This is not real Q1 and does not use abundance-geometry outcomes.

## Mandatory identity logic

1. Start from unique eligible bottom-level TREE records, not previously aggregated taxon summaries.
2. Join FIA SPCD to the 396-row v02 code map.
3. Ordinary accepted-species records mapping to the same analysis species are pooled before any plot/cell/species summary is recomputed.
4. No-analysis codes, aggregates, unresolved/UNKNOWN objects, and accepted-hybrid non-core codes do not enter the ordinary accepted-species eligibility census, but their record counts are reported separately.
5. Never add previously aggregated plot/cell counts across component codes.

## Native-CONUS diagnostics

Do not use USGS/Little to filter this task.

For each ordinary accepted species and FIA record, compare the FIA state with frozen WCVP Level-3 distribution evidence using exact full state-name correspondence. If a state-name crosswalk cannot be made deterministically, STOP and report it rather than guessing.

Produce two parallel, explicitly labeled census views:

A. ALL_CONUS_OBSERVED — all otherwise eligible FIA records in the frozen CONUS domain after accepted-species mapping.

B. WCVP_CONFIRMED_NATIVE_STATE — only records whose FIA state has a frozen WCVP confirmed-current-native Level-3 row for that accepted analysis species (introduced=0, extinct=0, location_doubtful=0).

Also separately count records in:
- explicit WCVP introduced states;
- CONUS states with no confirmed-current-native WCVP row and no explicit introduced row.

Do not silently coerce the last category to native or introduced.

Species with no confirmed-current-native CONUS Level-3 area must be flagged CONUS_NONNATIVE_CORE_INELIGIBLE, consistent with D08B1, but still retain their audit counts.

## Grain and split

Primary grain remains frozen at 50 km.
- 25 km = high-resolution sensitivity.
- 75 km = coarse-graining sensitivity.

Reuse the frozen D04 A/B plot split exactly; no new random split.

For each accepted analysis species × grain × census view × fold, recompute from bottom-level records at minimum:
- unique physical plot lineages / primary measurements;
- positive plots;
- detected cells;
- total qualifying TREE rows;
- DBH/DRC composition audit;
- state-native / introduced / unclassified record counts.

## Outcome-blind frontiers

At 50 km report candidate counts under pre-existing feasibility frontiers, without selecting one final threshold:
- minimum detected cells per fold >= 10, 15, 20;
- corresponding positive-plot frontiers as previously audited.

Also report the union of species passing >=10 detected cells per fold in either relevant native-confirmed feasibility view for later range-source review. This is a review queue, not a final cohort.

No Q1 geometry–abundance coupling, R1/R2 gain, World 0 result, significance, abundance geometry, predictive performance, or outcome-based filtering is permitted.

## Required outputs

At minimum:
- Q1_D08C1_SPECIES_GRAIN_CENSUS_v01.csv
- Q1_D08C1_50KM_FRONTIERS_v01.csv
- Q1_D08C1_NATIVE_STATE_AUDIT_v01.csv
- Q1_D08C1_CODE_AGGREGATION_AUDIT_v01.csv
- Q1_D08C1_NONANALYSIS_CODE_AUDIT_v01.csv
- Q1_D08C1_LITTLE_REVIEW_SURVIVOR_QUEUE_v01.csv
- Q1_D08C1_QC_v01.csv
- README / parameters / environment / manifest / SHA-256 / reproducible ZIP

## Hard prohibitions

- No USGS/Little layer union, selection or reconstruction.
- No external-range data search.
- No final species cohort selection.
- No final 10/15/20 threshold choice.
- No population-mass estimator implementation beyond eligibility counts.
- No real Q1.

STOP after delivery and return to scientific mainline.
