# Q1 D08B canonical taxon–native-range build contract v01

Frozen before the production build on 2026-09-02.

## Scope

- Candidate universe: the 396 FIA codes in `05_qc/elig_v02/TAXONOMY_CROSSWALK.csv`.
- Fixed order: FIA original name -> WCVP accepted taxon -> accepted analysis species -> WCVP distribution of that accepted analysis species -> map evidence back to FIA code.
- Analysis unit: accepted species.
- Natural range: WCVP records explicitly coded `introduced=0`; confirmed current native additionally requires `extinct=0` and `location_doubtful=0`.
- No FIA TREE merge, no real-Q1 outcome, no species selection, no fuzzy matching, and no USGS/Little layer union.

## Deterministic name handling

Only the following non-taxonomic string normalizations are permitted: Unicode NFC, HTML entity decoding, non-breaking-space replacement, trimming/collapsing whitespace, `ssp.` -> `subsp.`, and an ASCII hybrid marker surrounded by spaces (` x `) -> ` × `. No edit-distance, phonetic, stem, or approximate rule is permitted.

An FIA name is resolved only through exact normalized `wcvp_names.csv:taxon_name` records and WCVP identifiers:

1. A genus/non-species aggregate or unknown name is classified `GENUS_OR_NON_SPECIES_AGGREGATE` and receives no analysis species.
2. A hybrid marker or WCVP artificial-hybrid record is classified `HYBRID_OR_NOTHOTAXON` and receives no ordinary analysis species.
3. Exact WCVP `Accepted` and `Synonym` records are the only usable FIA-name evidence. Illegitimate, invalid, misapplied, unplaced, local-biotype, orthographic, and provisional records do not independently resolve an FIA name.
4. If usable exact records imply more than one distinct accepted WCVP identifier, the FIA code is `AMBIGUOUS`; the alternatives are retained.
5. A directly accepted species is `ACCEPTED_SPECIES`.
6. A synonym whose accepted identifier is an accepted species is `SYNONYM_TO_ACCEPTED_SPECIES`.
7. A directly accepted infraspecific taxon is mapped through its explicit `parent_plant_name_id` and classified `ACCEPTED_INFRASPECIES_TO_PARENT_SPECIES`.
8. A synonym whose accepted identifier is an accepted infraspecific taxon is mapped through that accepted row's explicit parent and classified `SYNONYM_TO_ACCEPTED_INFRASPECIES_TO_PARENT_SPECIES`.
9. Missing exact evidence, missing accepted rows, disallowed status-only evidence, missing parent paths, or a non-species terminal taxon is `UNRESOLVED`.

## Distribution and geography

- Distribution is queried only by the accepted analysis-species `plant_name_id`.
- Every matching Level-3 record and its original `continent`, `region`, `area`, `introduced`, `extinct`, and `location_doubtful` fields is retained.
- Blank or non-binary distribution flags are not coerced. Affected derived flags become `UNKNOWN` and the source rows remain auditable.
- CONUS is WGSRPD Level-2 regions 73–78.
- Alaska is Level-3 `ASK`.
- Canada is Level-2 regions 71–72 plus Level-3 `NUN`, `NWT`, and `YUK` in Subarctic America.
- Mexico is Level-2 region 79.
- Central America is Level-2 region 80.
- For the requested North-America flag, the paper-facing macro-region comprises WGSRPD Northern America (Level-1 7), Central America (Level-2 80), and Caribbean (Level-2 81). Presence elsewhere is flagged outside North America.
- Transcontinental/global means confirmed-current-native presence in at least two WGSRPD Level-1 botanical continents.
- The frozen primary Q1 analysis domain is CONUS 48 states plus DC if present, as recorded in `05_qc/elig_v02/MAINLINE_AUDIT_INDEX.md`. Therefore `extinct-native-outside-domain` and `doubtful-native-outside-domain` mean outside WGSRPD Level-2 regions 73–78. This build does not alter that domain.
- The separate requested `outside USA+Canada` descriptive flag uses the frozen Atlas comparison domain: CONUS Level-2 regions 73–78, Alaska Level-3 `ASK`, and Canada as defined above. It does not silently extend the Q1 primary domain.

## USGS/Little Table 1

- Atlas G Table 1 is parsed as the official original-source-name <-> then-current accepted-name bridge.
- Slash-separated accepted-name alternatives and literal `(in part)` qualifiers are retained as official row semantics; components are resolved by exact WCVP relations only.
- A layer shared by multiple accepted species, a row with unresolved alternatives, a species-plus-infraspecific set, an infraspecific-only set, any multiple-other-layer set, or any nonblank Notes field enters the review table.
- Only a unique one-row species/official-alias mapping with no unresolved alternative and no special Notes can receive a canonical layer flag.
- No species/subspecies layer is unioned, contained, or selected by this branch.

## DBH/DRC

- Candidate protocol values are preserved without reinterpretation.
- DRC codes remain main-analysis candidates and are never excluded by this build.
- The official `>=5.0 inch DBH/DRC` large-tree/subplot flag is retained.
- A DBH-only sensitivity flag is descriptive only and performs no filtering.

## Engineering PASS

PASS requires: 396/396 unique FIA codes classified once; all resolved synonym and infraspecific paths have explicit WCVP IDs; every analysis taxon is an accepted species; every distribution row is queried from its analysis-species ID; confirmed-current-native excludes introduced/extinct/doubtful records; all Level-3 evidence is retained; no aggregate/hybrid/ambiguous/unresolved code is assigned an analysis species; no USGS layer union occurs; DRC rows remain retained; and no real-Q1 result is computed.

Taxonomic or USGS cases explicitly returned as `AMBIGUOUS`, `UNRESOLVED`, or review-required do not by themselves fail engineering delivery if the evidence and reason are complete. Scientific resolution remains a mainline decision.
