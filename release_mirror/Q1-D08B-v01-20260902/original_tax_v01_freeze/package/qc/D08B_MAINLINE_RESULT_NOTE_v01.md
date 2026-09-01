# Q1 D08B canonical taxon–native-range result note v01

Status: **PASS**. This is an outcome-blind data-production result; no real Q1 analysis was run.

## Taxonomy

- 396/396 FIA codes classified exactly once.
- 370 codes resolve by explicit WCVP ID paths to 354 unique accepted analysis species.
- Mapping classes: {"ACCEPTED_INFRASPECIES_TO_PARENT_SPECIES": 8, "ACCEPTED_SPECIES": 328, "AMBIGUOUS": 5, "GENUS_OR_NON_SPECIES_AGGREGATE": 14, "HYBRID_OR_NOTHOTAXON": 2, "SYNONYM_TO_ACCEPTED_INFRASPECIES_TO_PARENT_SPECIES": 7, "SYNONYM_TO_ACCEPTED_SPECIES": 27, "UNRESOLVED": 5}.
- Ambiguous FIA names (5): 363 Arbutus xalapensis, 372 Betula lenta, 744 Populus heterophylla, 820 Quercus laurifolia, 822 Quercus lyrata.
- Unresolved FIA names (5): 840 Quercus margarettiae, 6511 Persea palustris, 6955 Salix fragilis, 8355 Psidium cattleianum, 8563 Schinus terebinthifolius.
- The other non-analysis objects are 14 genus/non-species aggregates and 2 hybrid/nothotaxa. None received an analysis-species ID.

## Native-range evidence

- 9429 WCVP Level-3 rows retained for accepted analysis-species IDs.
- Confirmed-current-native outside USA+Canada: 171 species; outside North America: 55.
- Confirmed-current-native in CONUS / Canada / Alaska / Mexico / Central America: 307 / 110 / 20 / 118 / 20.
- Transcontinental/circumboreal/global-extension: 60; introduced-in-CONUS audit: 90.
- Extinct-native outside primary CONUS domain: 3; doubtful-native outside primary CONUS domain: 1.
- All requested USA+Canada macro flags are determined from frozen WGSRPD hierarchy; UNKNOWN count is 0. Original Level-3 codes/names remain in the long table.

## USGS/Little

- Accepted-species mapping classes: {"AMBIGUOUS": 2, "MULTIPLE_OTHER_LAYERS": 6, "SINGLE_OFFICIAL_ALIAS_LAYER": 24, "SINGLE_SPECIES_LAYER": 243, "UNRESOLVED": 79}.
- Canonical no-review single-layer species: 262.
- Review-required species: 92 = 79 unresolved + 2 ambiguous + 6 multiple-layer + 5 otherwise-single rows with nonblank Atlas Notes.
- No layer union was constructed, and every review-required case has a blank canonical-layer field.

## DBH/DRC and QC

- FIA codes: 361 DBH and 35 DRC; all remain main-analysis candidates.
- Accepted species: 320 DBH-only, 34 DRC-only, 0 mixed.
- Mandatory QC: 24 PASS, 0 FAIL.

STOP: no FIA TREE merge, final species choice, grain/threshold selection, effect estimate, geometry gain, R1/R2 comparison, significance test, or real-Q1 result.
