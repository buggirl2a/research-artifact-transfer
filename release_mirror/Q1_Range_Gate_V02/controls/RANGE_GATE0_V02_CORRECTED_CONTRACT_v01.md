# Range Gate 0 v02 corrected scientific contract

Authority: scientific mainline request `Q1_WORK_REQUEST_RANGE_GATE0_v02_CORRECTED_GEOGRAPHIC_SEMANTICS_20260903.md`  
Frozen before any v02 class count was computed: 2026-09-03  
Status: AUTHORIZED BOUNDED CORRECTION ONLY

## Scientific object and invariant universe

Range Gate 0 v02 is a source-frozen, outcome-blind coarse routing screen for whole-range completeness. It is rebuilt directly from the unchanged D08B1 v02 accepted-species master, global range flags, and confirmed-current-native long evidence. The required universe is exactly 312 unique species selected by the frozen field `confirmed_native_CONUS == TRUE` from exactly 361 unique accepted analysis species.

The v01 class counts are not targets. No v01 classification row is an input to v02 construction. Range Gate 0 v01 remains an immutable negative scientific-audit artifact with status `MAINLINE_CONTRACT_SEMANTICS_FAIL / COMPUTATIONAL_EXECUTION_PASS`.

## Unchanged D08B1 geographic predicates

- CONUS: `region_code_l2` in `73,74,75,76,77,78`.
- Alaska: `area_code_l3 == ASK`.
- Canada: `region_code_l2` in `71,72`, or `area_code_l3` in `NUN,NWT,YUK`.
- Mexico: `region_code_l2 == 79`.
- Central America: `region_code_l2 == 80`.
- North-America-side: `continent_code_l1 == 7`, or `region_code_l2` in `80,81`.
- Confirmed current native: frozen long field `confirmed_current_native_flag == 1`.

Level-3 units are categorical evidence only. They are not area, range share, truncation severity, geometry, span, connected components, or thresholds.

## Corrected mutually exclusive precedence

First satisfied class controls.

1. `FAIL_EXTRA_NA`: explicit frozen confirmed-current-native evidence outside North America, from `confirmed_native_outside_North_America == TRUE` or completely reconciled frozen long evidence reproducing that predicate. Route `EXCLUDE_WHOLE_RANGE_CORE`.
2. `BORDERLINE_OTHER_NA`: without Class 1, confirmed Central America or other confirmed North-America-side extension outside CONUS, Canada, Alaska, Mexico, and Central America under the unchanged predicates. Route `HOLD_TARGETED_EXTERNAL_RANGE_AUDIT`.
3. `BORDERLINE_MEXICO`: without Classes 1–2, confirmed Mexico. Route `HOLD_TARGETED_EXTERNAL_RANGE_AUDIT`.
4. `RETAIN_USCA_AUDIT`: without Classes 1–3, confirmed Canada or Alaska. Route `RETAIN_FOR_LITTLE_OR_USCA_TRUNCATION_AUDIT`.
5. `PASS_COARSE`: without Classes 1–4, all required flags are binary, long evidence reconciles, no unresolved geographic contradiction exists, and no doubtful external native evidence could change routing. Route `COARSE_CORE_PASS`.
6. `UNKNOWN`: every remaining unresolved/nonbinary/contradictory/doubtful case. Route `HOLD_TARGETED_REVIEW_LATER`.

`transcontinental_circumboreal_global_extension_flag` is diagnostic-only. It has zero independent routing authority and is never a sufficient Class-1 reason.

## Frozen reason codes

- Class 1: `CONFIRMED_NATIVE_OUTSIDE_NORTH_AMERICA`; `FROZEN_LONG_EVIDENCE_EXTRA_NA_SUMMARY_QC_MISMATCH`.
- Class 2: `CONFIRMED_NATIVE_CENTRAL_AMERICA`; `CONFIRMED_NATIVE_OTHER_NA_EXTENSION`.
- Class 3: `CONFIRMED_NATIVE_MEXICO`.
- Class 4: `CONFIRMED_NATIVE_CANADA`; `CONFIRMED_NATIVE_ALASKA`; `CONFIRMED_NATIVE_CANADA_AND_ALASKA`.
- Class 5: `NO_CONFIRMED_EXTERNAL_NATIVE_EXTENSION_IN_FROZEN_D08B1`.
- Class 6: `REQUIRED_FLAG_MISSING_OR_NONBINARY`; `FROZEN_FLAG_EVIDENCE_CONTRADICTION`; `UNRESOLVED_FROZEN_NA_SUBREGION`; `DOUBTFUL_NATIVE_EXTERNAL_STATUS_COULD_CHANGE_ROUTE`.

## Frozen future flags

- `requires_future_usca_little_audit = 1` only for `RETAIN_USCA_AUDIT`.
- `requires_future_external_range_audit = 1` only for `BORDERLINE_OTHER_NA`, `BORDERLINE_MEXICO`, and `UNKNOWN`.
- `range_gate0_final_cohort_flag = 0` for every species.

## Mandatory semantic regression fixtures

- `Magnolia virginiana` → `BORDERLINE_OTHER_NA` if reconciled; otherwise `UNKNOWN` with contradiction.
- `Ostrya virginiana` → `BORDERLINE_OTHER_NA` if reconciled; otherwise `UNKNOWN` with contradiction.
- `Quercus rugosa` → `BORDERLINE_OTHER_NA` if reconciled; otherwise `UNKNOWN` with contradiction.
- `Sorbus decora` → `BORDERLINE_OTHER_NA` if reconciled; otherwise `UNKNOWN` with contradiction.
- `Pinus banksiana` → `RETAIN_USCA_AUDIT` if reconciled; otherwise `UNKNOWN` with contradiction.
- `Populus balsamifera` → `FAIL_EXTRA_NA` if reconciled; otherwise `UNKNOWN` with contradiction.
- `Pinus balfouriana` → `PASS_COARSE` if reconciled; otherwise `UNKNOWN` with contradiction.

Fixtures are regression checks, not count targets or tunable thresholds.

## Pre-frozen PASS/FAIL criteria

PASS requires all fifteen conditions in section 11 of the authority request, without waiver or movement after class counts: exact authority hashes; exact 361/312 closure; one valid class/route per candidate; no transcontinental-only Class 1; explicit extra-North-America evidence for every Class 1; diagnostic-only transcontinental behavior; exact corrected precedence; fixture compliance or explicit `UNKNOWN`; counts sum to 312 without target fitting; all final-cohort flags zero; no prohibited source/operation; independent output-only audit PASS; package/member/postpackage integrity PASS; post-freeze delta creation with every change explained only by corrected semantics; and no downstream phase.

Failure labels remain `INPUT_BLOCKED`, `REPRESENTATION_BLOCKED`, `ENGINEERING_FAIL`, and `SCIENTIFIC_CONTRACT_REGRESSION_FAIL`.

## Prohibited scope

No FIA TREE/species outcomes, D08C1/D08C2 eligibility, support/detection, A/B counts, abundance, R1/R2, World 0, paired-null, predictions, Little content/geometry, live/external range authority, polygon/raster/SDM, area/share/span/component/geometry inference, taxonomy repair, final cohort selection, corrected D08C2, or real Q1 may be read, run, searched, or inferred.

After v02 science freezes, the v01→v02 delta is additive audit evidence only. After the package and transport manifest are complete, STOP.
