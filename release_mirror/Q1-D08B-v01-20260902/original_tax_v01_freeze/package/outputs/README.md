# Q1 canonical taxon–native-range master v01

Engineering status: **PASS**. This is a bounded D08B data product, not a real-Q1 analysis.

## Canonical order

FIA original name -> exact WCVP accepted-ID path -> accepted analysis species -> native distribution queried only by that accepted species ID. Introduced, extinct, and location-doubtful rows are retained but excluded from confirmed-current-native. No fuzzy taxonomic evidence and no USGS/Little layer union were used.

## Contents

- `Q1_TAXON_RANGE_MASTER_v01.csv`: exactly 396 FIA codes and complete mapping/evidence status.
- `Q1_ANALYSIS_SPECIES_MASTER_v01.csv`: one row per accepted WCVP analysis species.
- `Q1_WCVP_NATIVE_DISTRIBUTION_LONG_v01.csv`: all WCVP Level-3 distribution rows for accepted analysis-species IDs, with explicit evidence classes.
- `Q1_GLOBAL_RANGE_FLAGS_v01.csv`: tri-state macro-region and audit flags plus retained Level-3 area lists.
- `Q1_USGS_NAME_LAYER_MAP_v01.csv`: accepted-species-to-Atlas-Table-1 layer rows; canonical layer is populated only for unique no-review cases.
- `Q1_USGS_LAYER_RECONSTRUCTION_REVIEW_v01.csv`: all multi-layer, infraspecific-only, shared/ambiguous, notes-bearing, and unresolved cases.
- `Q1_DRC_DBH_MASTER_v01.csv`: accepted-species DBH/DRC composition; DRC remains retained and DBH-only is a sensitivity flag only.
- `Q1_TAXON_RANGE_UNRESOLVED_v01.csv`: taxonomy, range, and USGS issues requiring audit or mainline judgment.
- `Q1_TAXON_RANGE_EVIDENCE_v01.csv`: source/hash and record-level lineage.
- `Q1_TAXON_RANGE_QC_v01.csv`: mandatory engineering checks.
- `Q1_TAXON_RANGE_MAINLINE_AUDIT_v01.xlsx`: formatted audit copy; CSV files remain canonical.

## Frozen rules and counts

The pre-build contract is `00_control/TAXON_RANGE_BUILD_CONTRACT_v01.md`. Resolved FIA codes: 370/396; unique accepted species: 354; WCVP Level-3 rows retained: 9429; USGS review-required species: 92. All unresolved and ambiguous cases are explicit and were not post-hoc resolved.

## STOP boundary

No FIA TREE records were merged. No range–abundance coupling, geometry gain, R1/R2 comparison, significance test, final grain, threshold, or paper species list was computed or selected.
