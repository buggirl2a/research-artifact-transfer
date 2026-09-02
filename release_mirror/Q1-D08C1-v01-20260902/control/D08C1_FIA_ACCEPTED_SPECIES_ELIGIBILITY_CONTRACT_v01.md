# D08C1 FIA accepted-species eligibility contract v01

Date frozen: 2026-09-02  
Status before computation: **FROZEN / AUTHORIZED TO RUN**

## Scope

Rebuild an outcome-blind accepted-species eligibility census from unique bottom-level FIA `TREE` records using D08B1 v02 as the sole taxonomy authority. This contract does not authorize real Q1, Little/USGS filtering or layer operations, external distribution searches, final grain selection, final threshold selection, or a final paper cohort.

## Frozen record eligibility

1. Candidate plot measurements: FIADB `PLOT.MEASYEAR` 2017–2023 in CONUS 48 states plus DC if present.
2. Eligible plot measurement: `PLOT_STATUS_CD=1` and at least one `COND` row with `COND_STATUS_CD=1` and `CONDPROP_UNADJ>0`.
3. Physical lineage: frozen `PREV_PLT_CN` chain rule `PREV_PLT_CN_ONE_LATEST_ELIGIBLE_2017_2023_V1`; ambiguous forks/cycles are excluded and reported.
4. Primary measurement: latest eligible measurement per unambiguous lineage by `MEASYEAR → MEASMON → MEASDAY → INVYR → CN`, descending.
5. TREE record: join to a primary measurement and eligible forest condition, then require `TREE.STATUSCD=1` and `TREE.DIA>=5.0` inches.
6. Bottom-level uniqueness key: `TREE.CN`. A duplicate qualifying `TREE.CN` is a hard FAIL.
7. Taxonomy join: exact normalized integer `TREE.SPCD` to the 396-row `Q1_FIA_CODE_TO_ANALYSIS_SPECIES_v02.csv`.
8. Codes with `ordinary_analysis_species_flag=1` are pooled by `analysis_species_id` before plot/cell/species summaries. No-analysis, aggregate, unresolved/UNKNOWN, hybrid non-core, and codes absent from the 396-row map are excluded from the ordinary census and reported separately.
9. Previously aggregated code-level plot/cell counts are never added.

## Frozen geography and fold

- Projection: D04 ellipsoidal NAD83 / CONUS Albers, EPSG:5070.
- Fixed origin: `(0,0)` metres.
- Grains: 25, 50, 75 km; 50 km is primary only by prior protocol, not selected by this run.
- Cell: `ix=floor(x/(grain_km*1000)); iy=floor(y/(grain_km*1000))`.
- Split: `source_state × P2PANEL`, missing panel literal `NA`.
- Seed: `D04_FIA_GEOMETRY_RECOVERABILITY_V1`.
- Within stratum: ascending `(SHA256(seed + "|" + primary measurement CN), CN)`, alternating A/B from A.

## Frozen FIA–WCVP state identity

- Forty-seven CONUS state names must match WCVP `area` by exact full string equality.
- The only authorized alias is FIA `STATECD=44 / RI / Rhode Island` → WCVP `area_code_l3=RHO / area=Rhode I.`.
- This alias resolves geographic identity only. No fuzzy, substring, edit-distance, abbreviation-expansion, neighboring-state, geometry, FIA-occurrence, or common-knowledge rule is permitted.
- Any additional non-exact CONUS state correspondence is a hard STOP.

## Frozen state evidence classification

For each accepted analysis species × FIA state:

1. `CONFIRMED_CURRENT_NATIVE` if the mapped frozen WCVP Level-3 row has `introduced=0`, `extinct=0`, and `location_doubtful=0`.
2. `EXPLICIT_INTRODUCED` if there is no confirmed-current-native row and at least one mapped row has `introduced=1`.
3. `NO_CONFIRMED_NATIVE_OR_INTRODUCED_ROW` if neither condition holds; native/introduced is not inferred.
4. A state with both confirmed-current-native and introduced evidence for the same accepted species is a hard STOP pending mainline review.
5. Species with frozen `confirmed_native_CONUS=FALSE` are flagged `CONUS_NONNATIVE_CORE_INELIGIBLE` but retain all audit counts.

## Frozen census views

- `ALL_CONUS_OBSERVED`: all otherwise qualifying ordinary accepted-species TREE records in the frozen primary domain.
- `WCVP_CONFIRMED_NATIVE_STATE`: only records whose accepted species × FIA state class is `CONFIRMED_CURRENT_NATIVE`.

Each analysis species × grain × view × fold (`ALL`, `A`, `B`) reports sampling-frame lineages/measurements/cells, positive plots, detected cells, qualifying TREE rows, DBH/DRC composition, and native/introduced/unclassified record counts. Detection-support geometry is limited to 4-neighbor connected components, largest-component fraction, and fixed-grid bounding-box span.

## Frozen 50-km descriptive frontiers

- Minimum detected cells in each fold: 10, 15, 20.
- Minimum positive plots in each fold: 10, 20, 30, 50, 100.
- Both census views are reported; all combinations are descriptive and none is selected.
- The later Little review queue is the union of species passing at least 10 detected cells in both folds in either census view. It is not a final cohort and contains no Little information.

## PASS/FAIL criteria frozen before TREE scan

PASS requires all of the following:

1. Every formal raw/control, D08B1 v02 authority, D04 continuity input, request, and mainline-decision hash matches the frozen ledger.
2. The extracted FIADB database member matches the formal raw ZIP member size and CRC-32.
3. The state identity audit yields exactly 47 exact matches plus the one authorized RI alias and no other mismatch.
4. D04 projection/grid/split continuity and rebuilt lineage, A/B stratum, and domain-grid audits reproduce the frozen eligibility-v0.2 facts.
5. All qualifying bottom-level TREE records have unique nonblank `TREE.CN` and reconcile exactly between ordinary and nonanalysis categories.
6. The 396-code map is unique; ordinary code pooling reconciles exactly from record → code → accepted species; every census native view is a subset of its all-observed counterpart.
7. Outputs contain all 361 accepted analysis species, both views, all three grains, and all three fold scopes, including zero-detection rows.
8. `Q1_D08C1_QC_v01.csv` contains no FAIL and the independent audit contains no FAIL.
9. No prohibited Q1 outcome, Little operation, external search, final threshold, final grain, or final cohort selection occurs.

No PASS/FAIL criterion may be changed after inspecting census results. Failure is reported diagnostically, not repaired by changing standards.

## Required delivery

The seven request-mandated CSV outputs, supporting state/cell/fold/lineage/trace audits, parameters, environment, logs, input hashes, QC, independent audit, audit XLSX, delivery index, manifest, SHA-256 ledger, and deterministic reproducible ZIP. Then STOP.
