# Q1 Range Gate 0 whole-range completeness coarse-screen contract v01

Frozen before inspecting Range Gate 0 class counts on 2026-09-03.

## Authorized scientific object

Range Gate 0 is a source-frozen routing screen for ordinary WCVP-accepted analysis species that are confirmed native in CONUS. It asks only whether frozen D08B1 v02 evidence shows clear native-range extension beyond CONUS, or leaves a later truncation review requirement. It is not a final whole-range-completeness decision, an area calculation, a geometry reconstruction, a species-cohort selection, D08C2, or real Q1.

## Exact frozen authority

- Request: `Q1_WORK_REQUEST_RANGE_GATE0_WHOLE_RANGE_COMPLETENESS_COARSE_SCREEN_v01_20260903.md`, SHA-256 `7b08106d190ac539e6f8127a656d36a764dc7f08a800e405d85aa0699612abd9`.
- D08B1 v02 reproducible ZIP: SHA-256 `3647c35189110d524d5f6cd64bf2d4aabaaa80828e58f42e767bb5e862188a3e`.
- `Q1_ANALYSIS_SPECIES_MASTER_v02.csv`: SHA-256 `6f69874ab02723b3489aa4f3cbfb5aba188147400efdf170f27ad699d6368cb0`.
- `Q1_GLOBAL_RANGE_FLAGS_v02.csv`: SHA-256 `dc64778032ed9bd301bfc7c14818fc3ba71a3b2621bb4e8b33ec558ecdf3d16d`.
- `Q1_WCVP_NATIVE_DISTRIBUTION_LONG_v02.csv`: SHA-256 `559a2d6f7b0d67ad886468a2c0098e117c824f196f0a85d3bb7d99c466649017`.
- Frozen macro-region implementation evidence: D08B1 build code SHA-256 `fad43f2fe935738585f78d4078b59b992de61bcb10a5ad89f1ede097055d821d`, parameters SHA-256 `65a5f60b03770c84401a1b3c741c548df10b5d972e86a35f91b3f3cd66273db7`, and D08B1 contract SHA-256 `bd756e111dc2cfe2e983d5f2b421846c85213612b167a111d0d0ee3d14ae40c8`.

No network source is permitted. The local immutable package copy is the sole authority.

## Input universe gate

The ordinary analysis-species master must contain exactly 361 unique species. Inner-joining its IDs to the 361-row global-range table must be one-to-one and complete. Filtering the frozen global field `confirmed_native_CONUS == TRUE` must yield exactly 312 unique analysis species. Any deviation is `INPUT_BLOCKED`; no classification build or repair is allowed.

## Frozen D08B1 macro-region predicates

These predicates are copied without reinterpretation from the frozen D08B1 implementation:

- CONUS: `region_code_l2` in `73, 74, 75, 76, 77, 78`.
- Alaska: `area_code_l3 == ASK`.
- Canada: `region_code_l2` in `71, 72` or `area_code_l3` in `NUN, NWT, YUK`.
- Mexico: `region_code_l2 == 79`.
- Central America: `region_code_l2 == 80`.
- North-America-side: `continent_code_l1 == 7` or `region_code_l2` in `80, 81`.
- Confirmed current native: `confirmed_current_native_flag == 1`, which in the frozen authority requires valid binary source flags and introduced/extinct/location-doubtful all equal to zero.

No new country, island, Caribbean, or macro-region dictionary may be introduced.

## Frozen classification precedence

Each of the 312 species receives exactly one class. The first satisfied class controls.

1. `FAIL_EXTRA_NA`: frozen `confirmed_native_outside_North_America == TRUE`, frozen `transcontinental_circumboreal_global_extension_flag == TRUE`, or completely closed frozen long evidence reproduces either fact while a summary flag alone is inconsistent. Route: `EXCLUDE_WHOLE_RANGE_CORE`.
2. `BORDERLINE_SOUTH`: without Class 1, frozen `confirmed_native_Central_America == TRUE`, or confirmed-current-native long evidence satisfies the frozen North-America-side predicate but is outside CONUS, Canada, Alaska, Mexico, and Central America. Route: `RETAIN_BORDERLINE_EXTERNAL_AUDIT_LATER`.
3. `BORDERLINE_MEXICO`: without Classes 1–2, frozen `confirmed_native_Mexico == TRUE`. Route: `RETAIN_BORDERLINE_EXTERNAL_AUDIT_LATER`.
4. `RETAIN_USCA_AUDIT`: without Classes 1–3, frozen `confirmed_native_Canada == TRUE` or `confirmed_native_Alaska == TRUE`. Route: `RETAIN_FOR_LITTLE_OR_USCA_TRUNCATION_AUDIT`.
5. `PASS_COARSE`: without Classes 1–4, all required flags are valid/binary, frozen long evidence reconciles to the summary flags, no unresolved frozen geographic contradiction exists, and no doubtful-native evidence outside the primary CONUS domain could change the route. Route: `COARSE_CORE_PASS`.
6. `UNKNOWN`: all remaining cases, including missing/non-binary required flags, unresolved summary-versus-long contradiction, an outside-USA/Canada extension not classifiable by the frozen predicates, or unresolved doubtful-native evidence that could alter the route. Route: `HOLD_TARGETED_REVIEW_LATER`.

## Frozen reason codes

- Class 1: `CONFIRMED_NATIVE_OUTSIDE_NORTH_AMERICA`, `TRANSCONTINENTAL_EXTENSION`, `EXTRA_NA_AND_TRANSCONTINENTAL`, or `FROZEN_LONG_EVIDENCE_CLASS1_SUMMARY_QC_MISMATCH`.
- Class 2: `CONFIRMED_NATIVE_CENTRAL_AMERICA` or `CONFIRMED_NATIVE_OTHER_NA_SOUTH_OR_ISLAND`.
- Class 3: `CONFIRMED_NATIVE_MEXICO`.
- Class 4: `CONFIRMED_NATIVE_CANADA`, `CONFIRMED_NATIVE_ALASKA`, or `CONFIRMED_NATIVE_CANADA_AND_ALASKA`.
- Class 5: `NO_CONFIRMED_EXTERNAL_NATIVE_EXTENSION_IN_FROZEN_D08B1`.
- Class 6: `REQUIRED_FLAG_MISSING_OR_NONBINARY`, `FROZEN_FLAG_EVIDENCE_CONTRADICTION`, `UNRESOLVED_FROZEN_NA_SUBREGION`, or `DOUBTFUL_NATIVE_EXTERNAL_STATUS_COULD_CHANGE_ROUTE`.

## Output fields and future-audit flags

- `requires_future_usca_little_audit=1` only for `RETAIN_USCA_AUDIT`.
- `requires_future_external_range_audit=1` only for `BORDERLINE_SOUTH`, `BORDERLINE_MEXICO`, and `UNKNOWN`.
- `range_gate0_final_cohort_flag=0` for every species.
- Level-3 names are retained only as frozen administrative evidence. They are never converted to area, proportion, severity, geometry, or a numerical threshold.

## Pre-frozen computational PASS/FAIL criteria

PASS requires all ten conditions in Section 6 of the authoritative request, plus exact output schemas, deterministic row ordering by `analysis_species_id`, output-only independent audit PASS, reproducible ZIP member-hash closure, and a final transfer manifest created only after the scientific package is frozen.

Failure categories are fixed as `INPUT_BLOCKED`, `REPRESENTATION_BLOCKED`, and `ENGINEERING_FAIL`. Class counts cannot alter this contract or any threshold because no scientific numerical threshold exists in Range Gate 0.

## Prohibited reads and operations

No FIA table, FIA species result, D08C1/D08C2 eligibility result, support/detection, A/B cell count, abundance, R1/R2, World 0, prediction, Little layer content, geometry source, polygon/raster, external website, live WCVP/POWO, NatureServe, GBIF, BONAP, SDM, final cohort, or real-Q1 result may be read or produced.

After immutable delivery and Relay manifest generation: **STOP**.
