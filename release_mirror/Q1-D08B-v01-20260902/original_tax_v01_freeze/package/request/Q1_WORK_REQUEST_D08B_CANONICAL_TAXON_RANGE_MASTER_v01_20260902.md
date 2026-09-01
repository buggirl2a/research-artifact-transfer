# Q1 WORK REQUEST D08B v01
## Canonical taxonomy–native-range master construction
## 正式分类学—原生分布主表构建

Date: 2026-09-02
Role: bounded computational branch（有边界的计算分支）
Status entering task: D08A source closure PASS; real-species Q1 remains HOLD.

## 0. Scientific-mainline decisions frozen before this task

1. Primary Q1 grain remains 50 km; this task does not revisit grain.
2. Analysis unit is the accepted species, not the raw FIA name/code.
3. Required order:
   FIA original identity -> WCVP accepted taxon -> analysis species ->
   evaluate native distribution using the accepted analysis species ->
   map back to original FIA identity.
4. Old names/synonyms must never be used first to determine global range.
5. Natural range uses native distribution only.
   Introduced / naturalized / invasive distributions do not enter natural range.
6. For current-range screening:
   - introduced = exclude from natural range;
   - extinct = retain as historical audit, but do not count as confirmed current native range;
   - location_doubtful = retain as uncertainty, but do not count as confirmed current native range.
7. WCVP species-level native distribution is used for the accepted analysis species.
   Do not mechanically union WCVP infraspecific distributions to reconstruct a species range.
   If the accepted species distribution itself is missing/ambiguous, flag it; do not invent it.
8. FIA DBH/DRC decision:
   Include both DBH and DRC taxa in the primary candidate pool because FIA defines >=5.0 inch
   DBH/DRC as the same core large-tree/subplot tally state. Preserve measurement basis.
   A later DBH-only sensitivity analysis is reserved.
   Do not reinterpret DRC as DBH.
9. USGS/Little:
   Atlas G Table 1 is the official name bridge.
   There is no universal rule that species-level and infraspecific layers should be unioned.
   Use row-specific Notes. Never mechanically union.
10. No real Q1 outcome may be computed.

## 1. Frozen inputs

Use, read-only:

### D08A source authority
`C:\range_paper\00_control\D08A_SOURCE_FREEZE_v02.md`

WCVP:
`C:\range_paper\02_raw\WCVP\wcvp.zip`
Expected SHA-256:
`d32ea2b3a85e489b14e83bcc9eae7274532e1d113753f7be290d4b2dfde573fa`

USGS Atlas G Table 1:
frozen D08A official copy under `C:\range_paper\03_doc\USGS\`

FIA documentation:
frozen D08A official field/database guides under `C:\range_paper\03_doc\FIA\`

### Eligibility-census candidate universe
Use the frozen Q1 eligibility census v0.2 candidate set (396 FIA taxon codes) and its
`TAXONOMY_CROSSWALK.csv`, `PROTOCOL_FLAGS.csv`, `GLOBAL_RANGE_REVIEW_QUEUE.csv`
as the candidate universe only.

Do not use census outcomes to alter taxonomic decisions.

## 2. Mission A — Build a code-level canonical taxonomic crosswalk

Create one and only one row for every one of the 396 FIA candidate taxon codes.

Preserve:
- FIA SPCD/code
- FIA raw scientific name
- FIA raw rank/metadata
- common name where available
- original identity unchanged

Resolve against WCVP Version 16 using nomenclatural structure, not approximate spelling.

Allowed deterministic normalization:
- whitespace/case normalization;
- standard rank-token normalization;
- removal/standardization of authorship only where the botanical name identity remains exact;
- WCVP synonym -> accepted_plant_name_id relations;
- WCVP parent_plant_name_id relations.

Forbidden:
- edit-distance fuzzy matching as evidence;
- picking the “closest-looking” WCVP name;
- using sampling abundance or range data to choose among names.

For each FIA code classify:
- ACCEPTED_SPECIES
- SYNONYM_TO_ACCEPTED_SPECIES
- ACCEPTED_INFRASPECIES_TO_PARENT_SPECIES
- SYNONYM_TO_ACCEPTED_INFRASPECIES_TO_PARENT_SPECIES
- GENUS_OR_NON_SPECIES_AGGREGATE
- HYBRID_OR_NOTHOTAXON
- AMBIGUOUS
- UNRESOLVED

For every resolved taxon record:
- matched WCVP plant_name_id;
- matched WCVP name/status/rank;
- accepted WCVP plant_name_id;
- accepted WCVP name/rank;
- accepted parent species plant_name_id/name if applicable;
- analysis_species_id;
- analysis_species_name;
- mapping path;
- evidence fields.

### Critical rule for infraspecific FIA records
If an FIA code resolves to an accepted or synonymous infraspecific taxon and WCVP gives an
unambiguous accepted parent species, set `analysis_species` to that accepted species.

Do NOT drop the FIA record merely because it was recorded at variety/subspecies level.

The later TREE-level aggregation will combine unique records mapped to the same analysis species.

### Non-species aggregates
Examples such as `Larix spp.` must remain non-species aggregates and must not be assigned to a
particular species without authoritative evidence.

## 3. Mission B — Build the accepted-analysis-species master

Deduplicate the code-level mapping to one row per `analysis_species_id`.

Create:
`Q1_ANALYSIS_SPECIES_MASTER_v01.csv`

For each analysis species record:
- WCVP accepted species ID/name;
- all component FIA codes;
- all FIA raw names;
- number of component codes;
- whether any component is infraspecific;
- whether any component is synonymic;
- hybrid/nothotaxon flag;
- DRC/DBH protocol composition;
- taxonomic ambiguity status.

No final inclusion/exclusion is authorized except that unresolved/non-species records cannot be
pretended to be species.

## 4. Mission C — Native/global-range facts from the accepted analysis species only

For each analysis species, retrieve WCVP distribution rows using the accepted analysis-species
WCVP species ID/name.

Never query native/global range from the FIA raw synonym/old name first.

Preserve a long evidence table containing at least:
- analysis_species_id/name
- WCVP distribution plant_name_id
- area_code_l3
- area
- introduced
- extinct
- location_doubtful
- raw distribution row identity if available

Derive three separate distribution sets:

1. `confirmed_current_native`
   native, not introduced, not extinct, not location_doubtful.

2. `native_historical_extinct`
   native but extinct in that area.

3. `native_location_doubtful`
   native-status row carrying location_doubtful.

Introduced/naturalized/invasive areas are retained in an audit field/table but never enter any
native-range flag.

Do not silently coerce missing/blank distribution-status flags to FALSE unless the frozen WCVP
README explicitly defines that encoding. If a row's native/current status cannot be determined from
the frozen schema semantics, retain it as UNKNOWN/UNCERTAIN rather than treating it as confirmed native.

For each analysis species derive descriptive flags:
- confirmed native in CONUS (if identifiable from WCVP Level-3 units)
- confirmed native in Canada
- confirmed native in Alaska
- confirmed native in Mexico
- confirmed native in Central America
- confirmed native outside USA+Canada
- confirmed native outside North America
- transcontinental/circumboreal/global-extension flag
- introduced-in-CONUS audit flag if identifiable
- extinct-native-outside-domain flag
- doubtful-native-outside-domain flag

Preserve the original Level-3 codes/names. Do not collapse away the original WCVP geography.

If a requested macro-region flag cannot be derived without an unapproved geographic lookup,
mark that flag UNKNOWN and return the distinct Level-3 areas for mainline review. Do not guess.

## 5. Mission D — Official USGS/Little name and layer closure

Use frozen Atlas G Table 1.

Map the accepted analysis species to official atlas source layer(s) through the Table 1 accepted-name
and original-source-name bridge.

For each analysis species classify:
- SINGLE_SPECIES_LAYER
- SINGLE_OFFICIAL_ALIAS_LAYER
- SPECIES_LAYER_PLUS_INFRASPECIFIC_LAYER(S)
- INFRASPECIFIC_LAYER(S)_ONLY
- MULTIPLE_OTHER_LAYERS
- UNRESOLVED
- AMBIGUOUS

Retain all relevant Table 1 Notes verbatim or in a lossless evidence field.

### Hard rule
Do not union atlas layers in D08B.

Instead create:
`Q1_USGS_LAYER_RECONSTRUCTION_REVIEW_v01.csv`

This review table must list every analysis species for which:
- more than one atlas layer maps to it;
- a species-level layer coexists with infraspecific layer(s);
- only infraspecific layers are available;
- Table 1 Notes imply special treatment;
- mapping is ambiguous.

For single unambiguous species-level/official-alias layers, identify the canonical layer directly.

Mainline will freeze reconstruction rules before any union is performed.

## 6. Mission E — DRC/DBH protocol fields

For every analysis species record:
- FIA diameter basis by component code: DBH / DRC / MIXED / OTHER / UNKNOWN;
- official >=5-inch large-tree/subplot-state flag;
- any regional/manual protocol exception flag found in frozen D08A evidence.

Scientific rule for this task:
DRC taxa remain eligible primary candidates.
Do not exclude them merely because diameter is measured at root collar.

Reserve a `DBH_ONLY_SENSITIVITY_FLAG` for later sensitivity analysis.

## 7. Required outputs

Write formal derived outputs under:
`C:\range_paper\04_derived\tax\`

Required:

1. `Q1_TAXON_RANGE_MASTER_v01.csv`
   - exactly 396 rows, one per FIA candidate code.

2. `Q1_ANALYSIS_SPECIES_MASTER_v01.csv`
   - one row per resolved accepted analysis species.

3. `Q1_WCVP_NATIVE_DISTRIBUTION_LONG_v01.csv`
   - preserved WCVP Level-3 distribution evidence by analysis species.

4. `Q1_GLOBAL_RANGE_FLAGS_v01.csv`
   - derived descriptive range flags.

5. `Q1_USGS_NAME_LAYER_MAP_v01.csv`
   - accepted analysis species -> official USGS/Little mapping.

6. `Q1_USGS_LAYER_RECONSTRUCTION_REVIEW_v01.csv`
   - all multi-layer/infraspecific/ambiguous cases requiring mainline review.

7. `Q1_DRC_DBH_MASTER_v01.csv`

8. `Q1_TAXON_RANGE_UNRESOLVED_v01.csv`
   - every unresolved/ambiguous/non-species case with reason.

9. `Q1_TAXON_RANGE_EVIDENCE_v01.csv`

10. `Q1_TAXON_RANGE_QC_v01.csv`

11. concise `README.md`

## 8. Mainline audit workbook

Also create one user-readable Excel workbook:
`Q1_TAXON_RANGE_MAINLINE_AUDIT_v01.xlsx`

It must include at least these sheets:
- Summary
- FIA_Code_Master
- Analysis_Species
- WCVP_Range_Flags
- USGS_Layer_Map
- USGS_Review
- DRC_DBH
- Unresolved
- QC

Keep identifiers as text where necessary.

This workbook is for mainline audit; CSVs remain canonical machine-readable outputs.

## 9. Mandatory QC

At minimum test:

- 396/396 FIA candidate codes represented exactly once.
- No duplicate FIA code rows.
- Every resolved synonym follows an explicit WCVP accepted-ID path.
- Every infraspecific -> species aggregation has an explicit WCVP parent-species path.
- No genus/spp. aggregate assigned to a species without evidence.
- Every analysis species is at accepted species rank.
- Native/global range was queried from the accepted analysis species, not from raw FIA synonyms.
- introduced rows never contribute to confirmed-current-native flags.
- extinct rows never contribute to confirmed-current-native flags.
- location_doubtful rows never contribute to confirmed-current-native flags.
- all original WCVP Level-3 evidence is retained.
- no USGS multi-layer case is mechanically unioned.
- DRC taxa are not automatically excluded.
- no real Q1 output exists.

## 10. Freeze and reproducibility

After successful construction, create:
`C:\range_paper\00_control\TAXON_RANGE_FREEZE_v01.md`

and archive:
`C:\range_paper\10_archive\tax_v01\`

Include:
- request;
- exact input hashes;
- executable source;
- environment;
- logs;
- all outputs;
- manifest;
- SHA-256;
- reproducible ZIP.

Do not modify D08A_SOURCE_FREEZE_v02 or RAW_FREEZE_v02.

## 11. Forbidden

- No FIA TREE-level merge yet.
- No recalculation of plot/cell/fold metrics yet.
- No final species cohort.
- No final sampling threshold.
- No range-abundance coupling.
- No geometry gain.
- No R1/R2 comparison.
- No real Q1.
- No atlas-layer union in ambiguous/multi-layer cases.
- No outcome-based taxonomic decision.

## 12. STOP

Return:
- engineering PASS/FAIL;
- number of 396 FIA codes resolved to accepted analysis species;
- number of unique accepted analysis species;
- counts by mapping class;
- number of species with native range outside USA+Canada;
- USGS single-layer vs review-required counts;
- unresolved/ambiguous counts;
- DRC/DBH counts;
- QC status;
- archive path + SHA-256;
- then STOP.

Scientific mainline will audit the master and freeze any remaining atlas-layer reconstruction rules
before D08C TREE-level accepted-species aggregation.
