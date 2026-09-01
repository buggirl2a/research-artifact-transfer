# Q1 D08B.1 correction log v02

Date: 2026-09-02  
Status: PASS  
Scope: additive taxonomy correction and USGS/Little name-layer bridge repair only.

## Taxonomy patch applied

- Eight mainline-authorized ordinary Accepted Species were added with WCVP author and stable-ID evidence: FIA 363, 372, 744, 820, 822, 840, 8355, and 8563.
- FIA 6511 is identity-resolved through `Persea palustris (Raf.) Sarg.` to `Tamala palustris Raf.`, but the frozen-v16 terminal status is `Unplaced`; no Accepted analysis species was fabricated.
- FIA 6955 remains `UNKNOWN` with no forced Salix mapping.
- FIA 143 resolves to accepted hybrid `Pinus × kohae Frankis`, is removed from the ordinary accepted-species master, and is retained in an explicit hybrid/non-core audit with four frozen Level-3 distribution records.
- Existing explicit hybrid/nothotaxon codes 929 and 8313 remain non-core.

The true v02 FIA code map contains 396 unique rows and preserves all original FIA names. It maps 377 codes to 361 ordinary WCVP Accepted, rank-Species, non-nothotaxon analysis taxa.

## Distribution update

- All 9,425 Level-3 rows for unchanged ordinary v01 analysis species were preserved exactly.
- Frozen WCVP v16 rows were added only for the eight newly resolved ordinary species.
- The v02 ordinary distribution table contains 9,648 rows.
- Four `Pinus × kohae` rows were removed from the ordinary table and preserved in the hybrid audit table.
- Introduced, extinct, and location-doubtful semantics were not changed; no introduced/extinct/doubtful row enters confirmed current native.

## USGS/Little bridge repair

- Atlas current names use name plus author whenever the author is supplied.
- Author strings are compared only after Unicode NFC, whitespace normalization, and lossless spacing normalization around periods, commas, and parentheses. No fuzzy/edit-distance/phonetic matching was used.
- A matched authored WCVP status controls; no different-author homonym substitutes for an Unplaced/invalid/misapplied concept.
- All 92 v01 USGS review species are represented in the cross-stage audit.
- Seven v01 `UNRESOLVED` species had a prior exact/nonzero eligibility-v0.2 mapping. Four were repaired to canonical single-species layers (`Abies grandis`, `Pinus muricata`, `Populus angustifolia`, `Quercus incana`); three remain explicit mainline-review cases with candidate Atlas rows and author-resolution causes (`Prunus emarginata`, `Quercus macrocarpa`, `Quercus michauxii`).
- Forty-seven species with frozen evidence of no native CONUS distribution plus introduced CONUS occurrence are classified `NOT_APPLICABLE_CONUS_NONNATIVE` rather than generic unresolved.
- Multiple/shared/Notes/infraspecific/review cases have no selected or canonical layer.

## Verification

- Build QC: 31 PASS, 0 FAIL.
- Independent audit: 25 PASS, 0 FAIL.
- Human-readable workbook: 16 sheets rendered and visually reviewed; formula-error scan matched 0 cells.

## Scope guard

No D08C, FIA TREE read/merge, Little layer union/selection/reconstruction, new external-range search, final cohort/grain selection, or real-Q1 result was performed.

