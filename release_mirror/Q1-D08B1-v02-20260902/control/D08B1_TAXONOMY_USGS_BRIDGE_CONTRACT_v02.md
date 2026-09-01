# Q1 D08B.1 taxonomy–USGS bridge correction contract v02

Frozen before the additive correction build on 2026-09-02.

## Authority and scope

This contract implements only the bounded D08B.1 correction authorized by:

- `Q1_WORK_REQUEST_D08B1_TAXONOMY_USGS_BRIDGE_CORRECTION_v01_20260902.md` (SHA-256 `dfc4016002e334524ed149647bd4d500a844d68b2eb638e3eb5b9a3ff8677f7a`);
- `Q1_D08B_TAXONOMY_CORRECTION_MAINLINE_DECISION_v01_20260902.md` (SHA-256 `d275946726f0111522a040992c210bf5511a5992a3e4737f6b10301b7a854564`);
- `D08B_TAXONOMY_CORRECTION_DELIVERY_v01.zip` (SHA-256 `fecd1278e843d02ffe54921cb59454dcef2642ec299eb93fb25471d661280efc`).

The frozen D08B v01 files are immutable inputs. D08B.1 produces additive v02 outputs only. It does not redesign Q1, run D08C, merge FIA TREE, union/select/reconstruct Little layers, search for new CONUS-external distribution data, select a final cohort or grain, or compute a real-Q1 field/result.

## Taxonomy patch

The following decisions are fixed and may not be tuned after inspection:

- FIA 363 -> accepted ordinary species `Arbutus xalapensis Kunth`, WCVP plant-name ID `2646755`.
- FIA 372 -> accepted ordinary species `Betula lenta L.`, WCVP plant-name ID `21443`.
- FIA 744 -> accepted ordinary species `Populus heterophylla L.`, WCVP plant-name ID `2917593`.
- FIA 820 -> accepted ordinary species `Quercus laurifolia Michx.`, WCVP plant-name ID `173587`.
- FIA 822 -> accepted ordinary species `Quercus lyrata Walter`, WCVP plant-name ID `173795`.
- FIA 840 -> accepted ordinary species `Quercus margaretta (Ashe) Small`, using frozen WCVP plant-name ID if present; preserve raw FIA spelling `Quercus margarettiae`.
- FIA 8355 -> accepted ordinary species `Psidium cattleyanum Sabine`, using frozen WCVP plant-name ID if present; preserve raw FIA spelling `Psidium cattleianum`.
- FIA 8563 -> accepted ordinary species `Schinus terebinthifolia Raddi`, using frozen WCVP plant-name ID if present; preserve raw FIA spelling `Schinus terebinthifolius`.
- FIA 6511 -> identity resolved to `Persea palustris (Raf.) Sarg.` with target `Tamala palustris Raf.` frozen-v16 status `Unplaced`; no accepted analysis species may be assigned.
- FIA 6955 -> `UNKNOWN`; no forced accepted mapping.
- FIA 143 -> accepted hybrid `Pinus × kohae Frankis`, non-core; absent from the ordinary accepted-species master; its frozen distribution evidence is audit-only.

Final identity tables preserve FIA raw name, FIA author/evidence status, WCVP matched name/author/stable ID, accepted name/author/stable ID, analysis-species name/author/stable ID, taxonomic status, and hybrid/nothotaxon flag where available. A bare name never silently overrides competing author-qualified concepts.

## True code map and ordinary analysis master

- `Q1_FIA_CODE_TO_ANALYSIS_SPECIES_v02.csv` has exactly 396 unique FIA codes.
- Original FIA names remain byte-for-byte values from the frozen v01 master.
- Every row has an explicit mapping class/status and either an accepted ordinary analysis-species identity or an explicit no-analysis-species reason.
- The ordinary accepted-analysis-species summary is rebuilt from the 396-row map and contains only WCVP Accepted, rank Species, non-hybrid taxa.

## WCVP distribution semantics

- Existing v01 distribution rows are preserved for unchanged ordinary analysis species.
- Distribution rows for the eight newly resolved ordinary accepted species are selected only from frozen WCVP v16 using the final accepted analysis-species IDs.
- `Pinus × kohae` evidence is preserved separately for hybrid audit only.
- `confirmed_current_native_flag=1` requires valid binary flags with `introduced=0`, `extinct=0`, and `location_doubtful=0`.
- Introduced rows never enter confirmed native. No external range system is searched.

## USGS/Little bridge rules

- Atlas Table 1 name components use name plus author when author is supplied.
- The only author-string normalization is Unicode NFC, whitespace collapse, and lossless spacing normalization around periods, commas, and parentheses. No fuzzy, edit-distance, phonetic, stem, or approximate matching is allowed.
- A canonical author match controls even when its WCVP status is Unplaced, invalid, or misapplied; another author's usable homonym may not substitute.
- Every v01 unresolved, ambiguous, multiple-layer, shared-layer, or Notes-review ordinary species is compared with frozen eligibility-v0.2 `USGS_RANGE_AUDIT.csv`.
- Any prior exact/official nonzero mapping lost by v01 is represented in `Q1_USGS_CROSS_STAGE_CONFLICT_v02.csv` with cause, proposed status, and machine/review disposition.
- WCVP-confirmed non-native-CONUS cases with introduced CONUS occurrence may receive `NOT_APPLICABLE_CONUS_NONNATIVE`; provenance remains visible.
- Multiple layers, shared/multi-taxon layers, species-plus-infraspecific sets, infraspecific-only sets, and all nonblank Atlas Notes cases remain review-only. No layer is unioned, selected, or reconstructed.

## Pre-frozen PASS/FAIL criteria

PASS requires all of the following; any failure is a build FAIL and must not be waived after results are seen:

1. The three new authoritative attachments and every correction-ZIP member pass SHA-256 verification.
2. The v01 baseline and eligibility-v0.2 diagnostic file match their frozen hashes.
3. The true code map contains exactly 396 rows and 396 unique FIA codes, with all original FIA names preserved.
4. All eight ordinary accepted-species corrections are applied exactly, with author-qualified accepted names and stable WCVP IDs.
5. FIA 6511 has no fabricated Accepted target; FIA 6955 remains UNKNOWN.
6. FIA 143 is an accepted hybrid/non-core object and is absent from the ordinary accepted-species master.
7. Every ordinary analysis taxon is WCVP Accepted, rank Species, non-hybrid.
8. Every v02 distribution row is keyed by a final ordinary accepted analysis-species ID; introduced/extinct/doubtful rows do not enter confirmed current native.
9. The complete frozen Level-3 semantics are preserved for retained and newly resolved ordinary species; hybrid evidence is separate.
10. Every applicable v01 USGS review/unresolved species is cross-stage audited; every prior exact/official nonzero layer lost in v01 is explicitly represented.
11. All non-native-CONUS `NOT_APPLICABLE` cases are supported by frozen WCVP and eligibility evidence rather than absence alone.
12. No review-only Little case receives a selected, unioned, or reconstructed canonical layer.
13. DRC/DBH protocol values are not scientifically reinterpreted; only species aggregation changes caused by the authorized taxonomy patch are allowed.
14. No FIA TREE record, real-Q1 outcome, coupling, geometry-gain, significance, cohort threshold, or grain-selection field/result is present.
15. Manifest/checksum verification and reproducible ZIP member verification pass with zero mismatch.

## STOP boundary

After the v02 correction package and audit artifacts are produced and verified, stop and return them to scientific mainline. D08C, FIA TREE merge, Little layer union/reconstruction, final cohort selection, and real Q1 remain on hold.
