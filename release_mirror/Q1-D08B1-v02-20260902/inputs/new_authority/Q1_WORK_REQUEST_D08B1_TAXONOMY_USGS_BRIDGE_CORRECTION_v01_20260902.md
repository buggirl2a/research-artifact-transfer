# Q1 Work Request D08B.1
## Apply additive taxonomy patch + repair USGS/Little name-layer bridge

Date: 2026-09-02
Role: bounded computational branch
Status: AUTHORIZED BOUNDED CORRECTION ONLY
Real Q1: HOLD
FIA TREE merge: HOLD
Little layer union/reconstruction: HOLD

## 0. Purpose
D08B engineering passed, but scientific-mainline audit identified two bounded corrections before D08C:
1. apply the accepted 11-case taxonomy identity correction decisions;
2. repair conservative false-negative behavior in the USGS/Little Atlas G Table 1 bridge.

This is additive correction, not a new eligibility analysis and not a real-Q1 run.

Authoritative mainline decision:
`Q1_D08B_TAXONOMY_CORRECTION_MAINLINE_DECISION_v01_20260902.md`

## 1. Frozen inputs
Use without modification:
- frozen D08B v01 package/mirror;
- D08A source freeze;
- WCVP v16, extracted 2026-06-04, frozen SHA-256;
- frozen Atlas G Table 1;
- frozen eligibility census v0.2, especially `USGS_RANGE_AUDIT.csv` as diagnostic cross-stage evidence;
- D08B taxonomy correction evidence/source ledger/note accepted by mainline.

## 2. Apply the taxonomy patch exactly
### Ordinary accepted species
- 363 -> `Arbutus xalapensis Kunth`
- 372 -> `Betula lenta L.`
- 744 -> `Populus heterophylla L.`
- 820 -> `Quercus laurifolia Michx.`
- 822 -> `Quercus lyrata Walter`
- 840 -> `Quercus margaretta (Ashe) Small`
- 8355 -> `Psidium cattleyanum Sabine`
- 8563 -> `Schinus terebinthifolia Raddi`

### No accepted analysis species
- 6511 `Persea palustris (Raf.) Sarg.`: identity resolved; target `Tamala palustris Raf.` is frozen-v16 `Unplaced`. Encode explicitly; no Accepted replacement.
- 6955 `Salix fragilis`: remain UNKNOWN; no forced mapping.

### Accepted hybrid / non-core
- 143 `Pinus monophylla var. fallax` -> `Pinus × kohae Frankis`, Accepted hybrid. Remove from ordinary accepted-species analysis master/core candidate class and place in explicit accepted-hybrid/non-core class. Preserve native distribution evidence for audit only.

Do not alter the frozen D08B v01 files; produce v02/additive outputs.

## 3. Author-aware data model
Add/preserve, where available:
- FIA raw scientific name
- FIA concept author / author-evidence status
- WCVP matched name + author + stable ID
- accepted name + author + stable ID
- analysis species name + author + stable ID
- taxonomic status and hybrid/nothotaxon flag

Bare names may never silently override competing author-qualified concepts.

## 4. Produce a true 396-row code map
Create:
`Q1_FIA_CODE_TO_ANALYSIS_SPECIES_v02.csv`

Requirements:
- exactly 396 data rows;
- FIA code unique;
- original FIA name immutable;
- explicit mapping class/status;
- explicit analysis-species ID/name/author where ordinary accepted species exists;
- explicit no-analysis-species reason for aggregate, hybrid, unplaced-target, ambiguous, or unresolved objects.

Also rebuild the accepted-analysis-species summary from this code map.

## 5. WCVP distribution update
Do not recompute unrelated taxonomy.
- Add WCVP native-distribution rows/flags for newly resolved ordinary accepted species.
- Remove `Pinus × kohae` from the ordinary-species master while preserving its evidence in a hybrid audit table.
- Preserve all frozen native/introduced semantics.
- Do not search new external range-map systems.

## 6. Repair USGS/Little bridge
### 6.1 Author-concept resolution
For Atlas G Table 1 name components:
- use name + author when author is supplied;
- allow only lossless author canonicalization: Unicode normalization, collapse whitespace, normalize spacing around periods/commas/parentheses; no fuzzy/edit-distance/phonetic matching;
- if canonically matching an authored WCVP row, that row's status controls;
- never substitute a different author's usable homonym for an authored Unplaced/invalid/misapplied concept.

### 6.2 Cross-stage diagnostic
For every D08B USGS `UNRESOLVED`, `AMBIGUOUS`, multiple-layer, shared-layer, or Notes-review species, compare with eligibility-v0.2 `USGS_RANGE_AUDIT.csv`.

Create:
`Q1_USGS_CROSS_STAGE_CONFLICT_v02.csv`

At minimum include:
- analysis species
- D08B status
- eligibility-v0.2 mapping type/name/layer and grid counts
- Atlas Table 1 row(s)
- WCVP concept evidence
- conflict type
- proposed v02 status
- machine-resolved vs mainline-review-required

Any prior exact/official mapped nonzero layer that becomes unresolved in D08B must be explicitly accounted for; no silent loss.

### 6.3 Non-native-CONUS cases
Where WCVP confirms no native CONUS distribution and CONUS occurrence is introduced, encode lack of Little natural-range mapping as `NOT_APPLICABLE_CONUS_NONNATIVE` (or an equivalent explicit class), not generic unresolved.

### 6.4 Review-only remains review-only
Do not union/select/reconstruct:
- multiple layers;
- shared/multi-taxon layers;
- species + infraspecific layer sets;
- infraspecific-only sets;
- nonblank Atlas Notes special cases.

Output all such rows with complete evidence for mainline review.

## 7. Required outputs
At minimum:
1. `Q1_TAXON_RANGE_MASTER_v02.csv`
2. `Q1_FIA_CODE_TO_ANALYSIS_SPECIES_v02.csv` (396 rows)
3. `Q1_ANALYSIS_SPECIES_MASTER_v02.csv`
4. `Q1_TAXONOMY_CORRECTION_APPLIED_v02.csv`
5. `Q1_HYBRID_NONCORE_AUDIT_v02.csv`
6. `Q1_WCVP_NATIVE_DISTRIBUTION_LONG_v02.csv`
7. `Q1_GLOBAL_RANGE_FLAGS_v02.csv`
8. `Q1_USGS_NAME_CLOSURE_v02.csv`
9. `Q1_USGS_LAYER_RECONSTRUCTION_REVIEW_v02.csv`
10. `Q1_USGS_CROSS_STAGE_CONFLICT_v02.csv`
11. `Q1_DRC_PROTOCOL_v02.csv` (no scientific reinterpretation; update only species aggregation if needed)
12. `Q1_TAXON_RANGE_QC_v02.csv`
13. correction log, parameters, environment, manifest, SHA-256, reproducible ZIP
14. human-readable audit workbook if practical.

## 8. Mandatory QC
Include explicit checks for:
- 396/396 FIA codes present uniquely in true code map;
- all eight newly ordinary-accepted corrections exactly applied;
- 6511 has no fabricated Accepted target;
- 6955 remains UNKNOWN;
- 143 is accepted hybrid and absent from ordinary-species core master;
- all ordinary analysis taxa are WCVP Accepted Species and non-hybrid;
- distribution queries use final accepted analysis-species IDs only;
- no introduced rows enter confirmed native;
- every D08B USGS unresolved with a prior eligibility exact/nonzero mapping is represented in the cross-stage conflict table;
- no Little layer union or selection for review-only cases;
- no FIA TREE merge;
- no real-Q1 field/result.

## 9. STOP boundary
After producing the corrected v02 package, STOP and return it to scientific mainline.
Do not start D08C, do not merge FIA TREE, do not reconstruct Little layers, do not choose final cohort thresholds, and do not run real Q1.
