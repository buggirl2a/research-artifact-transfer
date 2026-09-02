# Q1 WORK REQUEST — Range Gate 0 v02 corrected geographic semantics

**Project:** Q1 species-range internal structure  
**Authority:** Scientific mainline / PI  
**Version:** v02 corrected  
**Date:** 2026-09-03  
**Status:** AUTHORIZED BOUNDED CORRECTION ONLY  

## 0. Mainline decision being implemented

Range Gate 0 v01 remains an **immutable negative scientific-audit artifact**.

Mainline audit concluded:

- v01 computational execution / engineering / packaging: **PASS**;
- v01 compliance with its frozen contract: **PASS**;
- v01 scientific classification: **FAIL — MAINLINE_CONTRACT_SEMANTICS_ERROR**.

The error is in the v01 mainline contract, not in Work execution.

The v01 contract incorrectly allowed `transcontinental_circumboreal_global_extension_flag == TRUE` to independently trigger `FAIL_EXTRA_NA`. Frozen D08B1 evidence demonstrates that this flag is broader than “confirmed native outside North America”; it can be TRUE for species whose frozen confirmed native extension is limited to Mexico, Central America, Caribbean/island units, or other North-America-side units. Therefore it is not scientifically equivalent to confirmed extra-North-American nativeness.

**v02 must correct only this geographic-classification semantics.**

No v01 scientific output may be overwritten, edited, deleted, or silently replaced.

---

## 1. Authorized scientific object

Re-run the Range Gate 0 coarse whole-range-completeness routing screen for the **same exact frozen 312-species universe** using the **same exact frozen D08B1 v02 authority**, but with the corrected class semantics in this request.

This is still only a **source-frozen, outcome-blind routing screen**. It is not:

- a final whole-range-completeness decision;
- an area/share calculation;
- a range-geometry reconstruction;
- a Little-layer decision;
- D08C2;
- a final species-cohort selection;
- an abundance/support/detection analysis;
- real Q1.

---

## 2. Frozen authority — unchanged from v01

Use the same authoritative D08B1 v02 package and members used by Range Gate 0 v01.

Required authoritative hashes remain:

- `Q1_TAXON_RANGE_D08B1_CORRECTED_REPRODUCIBLE_v02.zip`  
  SHA-256: `3647c35189110d524d5f6cd64bf2d4aabaaa80828e58f42e767bb5e862188a3e`
- `Q1_ANALYSIS_SPECIES_MASTER_v02.csv`  
  SHA-256: `6f69874ab02723b3489aa4f3cbfb5aba188147400efdf170f27ad699d6368cb0`
- `Q1_GLOBAL_RANGE_FLAGS_v02.csv`  
  SHA-256: `dc64778032ed9bd301bfc7c14818fc3ba71a3b2621bb4e8b33ec558ecdf3d16d`
- `Q1_WCVP_NATIVE_DISTRIBUTION_LONG_v02.csv`  
  SHA-256: `559a2d6f7b0d67ad886468a2c0098e117c824f196f0a85d3bb7d99c466649017`

No live WCVP/POWO, web search, GBIF, NatureServe, BONAP, SDM, atlas reconstruction, or other new distribution authority is permitted.

---

## 3. Exact frozen input-universe gate — unchanged

Before classification:

1. Ordinary accepted-analysis-species master must contain exactly **361 unique species**.
2. One-to-one complete join to the frozen global-range table must succeed.
3. Filtering the frozen field `confirmed_native_CONUS == TRUE` must yield exactly **312 unique analysis species**.

Any deviation = **INPUT_BLOCKED**. Do not repair or substitute data.

The v01 class counts are **not targets** and must not be used to tune v02.

---

## 4. Geographic predicates — unchanged

Use exactly the frozen D08B1 predicates already used by v01. Do not create a new country/island/Caribbean dictionary.

- CONUS: frozen D08B1 predicate.
- Alaska: frozen D08B1 predicate.
- Canada: frozen D08B1 predicate.
- Mexico: frozen D08B1 predicate.
- Central America: frozen D08B1 predicate.
- North-America-side: frozen D08B1 predicate.
- Confirmed current native: frozen D08B1 `confirmed_current_native_flag == 1` semantics.

Level-3 administrative evidence remains categorical evidence only. It must never be converted to area, range share, severity, geometry, or a numerical truncation estimate.

---

## 5. Corrected classification precedence — FROZEN BEFORE v02 COUNTS

Each of the 312 species receives exactly one class. First satisfied class controls.

### Class 1 — `FAIL_EXTRA_NA`

Assign only when there is **explicit frozen evidence of confirmed current native occurrence outside North America**:

- frozen `confirmed_native_outside_North_America == TRUE`; or
- completely reconciled frozen long evidence, under the already frozen D08B1 geographic predicates, explicitly reproduces confirmed native occurrence outside North America even if a summary field is inconsistent.

Route: `EXCLUDE_WHOLE_RANGE_CORE`.

**Critical correction:**

`transcontinental_circumboreal_global_extension_flag` is **diagnostic-only** in v02. It may be retained in outputs for audit, but it has **zero independent routing authority**. A species with `confirmed_native_outside_North_America == FALSE` may not enter `FAIL_EXTRA_NA` solely because the transcontinental flag is TRUE.

### Class 2 — `BORDERLINE_OTHER_NA`

Without Class 1, assign when frozen evidence shows confirmed native extension to a North-America-side unit outside CONUS, Canada, Alaska, and Mexico, including:

- `confirmed_native_Central_America == TRUE`; or
- frozen confirmed-current-native long evidence satisfying the already frozen North-America-side predicate while lying outside CONUS, Canada, Alaska, Mexico, and Central America.

This class intentionally covers Central America plus other North-America-side island/other extensions identified by the frozen predicates (for example Caribbean/Greenland-type cases when represented by the frozen D08B1 semantics). No new geography dictionary may be introduced.

Route: `HOLD_TARGETED_EXTERNAL_RANGE_AUDIT`.

### Class 3 — `BORDERLINE_MEXICO`

Without Classes 1–2, assign when frozen `confirmed_native_Mexico == TRUE`.

Route: `HOLD_TARGETED_EXTERNAL_RANGE_AUDIT`.

### Class 4 — `RETAIN_USCA_AUDIT`

Without Classes 1–3, assign when frozen `confirmed_native_Canada == TRUE` or `confirmed_native_Alaska == TRUE`.

Route: `RETAIN_FOR_LITTLE_OR_USCA_TRUNCATION_AUDIT`.

### Class 5 — `PASS_COARSE`

Without Classes 1–4, assign only when all required flags are valid/binary, frozen long evidence reconciles to summary flags, no unresolved frozen geographic contradiction exists, and no doubtful-native external evidence could change the route.

Route: `COARSE_CORE_PASS`.

### Class 6 — `UNKNOWN`

All remaining cases, including missing/non-binary required flags, unresolved summary-versus-long contradiction, unclassifiable frozen North-America-side evidence, or unresolved doubtful-native evidence that could alter the route.

Route: `HOLD_TARGETED_REVIEW_LATER`.

---

## 6. Corrected reason codes

At minimum use explicit auditable reason codes equivalent to:

- Class 1: `CONFIRMED_NATIVE_OUTSIDE_NORTH_AMERICA`, `FROZEN_LONG_EVIDENCE_EXTRA_NA_SUMMARY_QC_MISMATCH`.
- Class 2: `CONFIRMED_NATIVE_CENTRAL_AMERICA`, `CONFIRMED_NATIVE_OTHER_NA_EXTENSION`.
- Class 3: `CONFIRMED_NATIVE_MEXICO`.
- Class 4: `CONFIRMED_NATIVE_CANADA`, `CONFIRMED_NATIVE_ALASKA`, `CONFIRMED_NATIVE_CANADA_AND_ALASKA`.
- Class 5: `NO_CONFIRMED_EXTERNAL_NATIVE_EXTENSION_IN_FROZEN_D08B1`.
- Class 6: `REQUIRED_FLAG_MISSING_OR_NONBINARY`, `FROZEN_FLAG_EVIDENCE_CONTRADICTION`, `UNRESOLVED_FROZEN_NA_SUBREGION`, `DOUBTFUL_NATIVE_EXTERNAL_STATUS_COULD_CHANGE_ROUTE`.

Do not retain `TRANSCONTINENTAL_EXTENSION` as a sufficient Class-1 reason code. If the transcontinental flag is TRUE, it may be reported in a separate diagnostic field only.

---

## 7. Mandatory semantic regression checks

These named cases are **regression fixtures for the corrected semantics**, not outcome-based thresholds. Their frozen D08B1 evidence already exposed the v01 semantic defect.

Under v02, verify at minimum:

- `Magnolia virginiana`: `confirmed_native_outside_North_America == FALSE`; frozen external evidence includes Cuba. **Must not be `FAIL_EXTRA_NA` solely due to transcontinental flag.** Expected route class under corrected precedence: `BORDERLINE_OTHER_NA` if all frozen evidence reconciles.
- `Ostrya virginiana`: `confirmed_native_outside_North_America == FALSE`; frozen Mexico/Central-America extension. **Must not be `FAIL_EXTRA_NA` solely due to transcontinental flag.** Expected corrected class: `BORDERLINE_OTHER_NA` if evidence reconciles.
- `Quercus rugosa`: `confirmed_native_outside_North_America == FALSE`; frozen Mexico/Central-America extension. Expected corrected class: `BORDERLINE_OTHER_NA` if evidence reconciles.
- `Sorbus decora`: frozen Greenland extension with `confirmed_native_outside_North_America == FALSE`. Expected corrected class: `BORDERLINE_OTHER_NA` if evidence reconciles.
- `Pinus banksiana`: Canada extension, no Mexico/Central-America/extra-North-America extension. Expected class remains `RETAIN_USCA_AUDIT` if evidence reconciles.
- `Populus balsamifera`: frozen confirmed native evidence includes Magadan and `confirmed_native_outside_North_America == TRUE`. Expected class remains `FAIL_EXTRA_NA` if evidence reconciles.
- `Pinus balfouriana`: no frozen confirmed external native extension. Expected class remains `PASS_COARSE` if evidence reconciles.

If any fixture cannot meet the expected class because frozen source fields are internally inconsistent, do **not** force the expected class; classify `UNKNOWN` and report the exact frozen contradiction. No repair by external search is authorized.

---

## 8. v01 handling and v01→v02 delta audit

v01 is immutable and must remain scientifically labeled as:

`MAINLINE_CONTRACT_SEMANTICS_FAIL / COMPUTATIONAL_EXECUTION_PASS`.

The v02 classification must be generated **fresh from the frozen D08B1 v02 authority under this corrected v02 contract**. Do not generate v02 by editing v01 classification rows.

Only **after the v02 scientific classification is frozen**, compare it with v01 and produce an additive delta audit containing at least:

- `analysis_species_id`
- `analysis_species_name`
- `v01_class`
- `v02_class`
- `v01_reason_code`
- `v02_reason_code`
- `class_changed`
- `change_explanation`
- frozen `confirmed_native_outside_North_America`
- frozen `transcontinental_circumboreal_global_extension_flag`
- relevant frozen Level-3 external evidence

Every changed row must be explainable solely by the corrected semantic rules above. No class count is pre-specified.

---

## 9. Future-audit flags

Use:

- `requires_future_usca_little_audit = 1` only for `RETAIN_USCA_AUDIT`.
- `requires_future_external_range_audit = 1` for `BORDERLINE_OTHER_NA`, `BORDERLINE_MEXICO`, and `UNKNOWN`.
- `range_gate0_final_cohort_flag = 0` for **all 312 species**.

No final species cohort may be selected.

---

## 10. Explicitly prohibited reads/operations

Do not read or use:

- FIA TREE or species outcome tables;
- D08C1/D08C2 eligibility results;
- support/detection results;
- A/B detected-cell counts;
- abundance/population-mass results;
- R1/R2;
- World 0 / paired-null / prediction outputs;
- Little layer content or reconstructed Little geometry;
- external websites or live range authorities;
- new polygons/rasters/SDMs;
- any real-Q1 result.

Do not perform:

- area-share estimation;
- geographic-span estimation;
- component/hole/geometry reconstruction;
- new taxonomy repair;
- final cohort selection;
- corrected D08C2.

---

## 11. Pre-frozen v02 PASS/FAIL criteria

Scientific/computational PASS requires all of the following:

1. Exact frozen D08B1 v02 authority hashes match.
2. Master = 361 unique ordinary species and candidate universe = exactly 312 unique `confirmed_native_CONUS == TRUE` species.
3. Every candidate receives exactly one valid v02 class and route.
4. `FAIL_EXTRA_NA` contains **no species with `confirmed_native_outside_North_America == FALSE` solely because the transcontinental flag is TRUE**.
5. Every `FAIL_EXTRA_NA` has explicit frozen extra-North-America native evidence.
6. `transcontinental_circumboreal_global_extension_flag` has diagnostic-only status and never independently changes routing.
7. `BORDERLINE_OTHER_NA`, `BORDERLINE_MEXICO`, `RETAIN_USCA_AUDIT`, `PASS_COARSE`, and `UNKNOWN` follow the frozen precedence exactly.
8. All mandatory semantic regression fixtures pass, or any exception is routed to `UNKNOWN` with explicit frozen contradiction evidence.
9. Summary class counts sum to exactly 312; counts themselves are not targets.
10. All final-cohort flags are zero.
11. No prohibited source or operation is used.
12. Independent output-only audit passes.
13. Reproducible package/member hashes and post-package validation pass with zero mismatch.
14. v01→v02 delta audit is created only after v02 scientific outputs are frozen and every changed row is attributable solely to this corrected semantic contract.
15. No D08C2, Little detailed decision, targeted external search, or real Q1 is run.

Failure categories remain explicit: `INPUT_BLOCKED`, `REPRESENTATION_BLOCKED`, `ENGINEERING_FAIL`, or `SCIENTIFIC_CONTRACT_REGRESSION_FAIL` as applicable. Do not waive or move criteria after seeing v02 class counts.

---

## 12. Required outputs

Produce an additive v02 delivery, with concise deterministic names, including at minimum:

1. 312-row corrected species classification table.
2. v02 class-count summary.
3. v02 decision/review queue.
4. corrected `FAIL_EXTRA_NA` ledger.
5. v01→v02 delta audit.
6. result note stating the interpretation boundary and STOP.
7. source/input hash audit.
8. boundary/prohibited-operation audit.
9. build QC.
10. independent output-only audit.
11. scientific-output freeze note.
12. reproducible delivery ZIP.
13. ZIP SHA-256 sidecar.
14. manifest/checksum ledger.
15. post-package validation.
16. mainline-readable audit workbook if the existing workflow supports it.

Do not overwrite any v01 file. Use a new local archive path, e.g.:

`C:\range_paper\10_archive\range_gate0_v02_corrected\`

---

## 13. Research Artifact Relay transport manifest

After the v02 scientific package is frozen and validated, create:

`C:\range_paper\10_archive\range_gate0_v02_corrected\TRANSFER_MANIFEST_v01.csv`

This is **transport metadata only**. It must not trigger scientific recomputation, repacking, or mutation.

One row per local delivery file considered for relay. At minimum record:

- file name;
- complete local path;
- role/purpose;
- byte size;
- SHA-256;
- whether upload is mandatory;
- suggested GitHub relative path/name;
- notes.

The manifest must include the final scientific results, corrected contract/freeze, QC/validation artifacts, reproducible ZIP, ZIP SHA-256 sidecar, and v01→v02 delta audit.

Report the manifest local path and planned relay-file count.

---

## 14. STOP boundary

After immutable v02 delivery, validation, and transfer-manifest generation:

**STOP.**

Do not proceed to corrected D08C2, Little detailed truncation analysis, targeted external-range search, final cohort construction, support/abundance estimation, or real Q1 without a new explicit mainline authorization.
