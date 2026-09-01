# Q1 D08B Taxonomy Correction — Mainline Decision v01

Date: 2026-09-02
Role: Q1 scientific mainline / PI decision
Status: ADDITIVE CORRECTION EVIDENCE ACCEPTED
Real Q1: HOLD
D08C FIA TREE merge: HOLD

## 1. Integrity audit
The uploaded bounded factual-closure delivery is internally consistent. The manifest hashes for the evidence, source ledger, and note match the delivered files. The delivery ZIP contains the same evidence, ledger, note, manifest, and SHA-256 sidecar without modifying the frozen D08B master.

## 2. Taxonomic decisions
The following additive decisions are authorized for a D08B.1 correction build. Original FIA names/codes must remain immutable provenance fields.

### Resolve to ordinary accepted species
- FIA 363 `Arbutus xalapensis` -> `Arbutus xalapensis Kunth`.
- FIA 372 `Betula lenta` -> `Betula lenta L.`.
- FIA 744 `Populus heterophylla` -> `Populus heterophylla L.`.
- FIA 820 `Quercus laurifolia` -> `Quercus laurifolia Michx.`.
- FIA 822 `Quercus lyrata` -> `Quercus lyrata Walter`.
- FIA 840 `Quercus margarettiae` -> accepted `Quercus margaretta (Ashe) Small`; preserve raw FIA spelling.
- FIA 8355 `Psidium cattleianum` -> accepted `Psidium cattleyanum Sabine`; preserve raw FIA spelling.
- FIA 8563 `Schinus terebinthifolius` -> accepted `Schinus terebinthifolia Raddi`; preserve raw FIA spelling.

### Identity resolved, but no accepted analysis species
- FIA 6511 `Persea palustris` = `Persea palustris (Raf.) Sarg.`; WCVP/POWO routes to `Tamala palustris Raf.`, whose frozen-v16 status is `Unplaced`. Do not invent an Accepted replacement. Encode as identity-resolved / target-unplaced / no accepted analysis species.

### Remain unresolved
- FIA 6955 `Salix fragilis` remains `UNKNOWN`. Do not force to `Salix euxina`, `Salix pentandra`, or accepted hybrid `Salix × fragilis L.` without code-specific FIA concept evidence.

### Accepted hybrid, non-core
- FIA 143 `Pinus monophylla var. fallax` -> accepted hybrid `Pinus × kohae Frankis` (synonym path confirmed). It must not be treated as an ordinary accepted-species core taxon. Preserve in a separate accepted-hybrid/non-core class. It may remain eligible only for a later supplementary sensitivity analysis if otherwise informative.

## 3. Matching rule correction
Final taxonomic identity tables must preserve author information wherever available. Bare scientific-name strings are retrieval keys, not sufficient final identity evidence when homonyms or competing concepts exist.

Evidence priority:
1. FIA code + official taxon concept/full name/author when available;
2. WCVP/POWO stable identifier + accepted name + author;
3. explicit synonym chain;
4. authoritative orthographic correction;
5. bare name only when no competing concept exists.

## 4. Required true code mapping
D08B.1 must generate `Q1_FIA_CODE_TO_ANALYSIS_SPECIES_v02.csv` with exactly 396 unique FIA-code rows. The previous 354-row `Q1_TAXON_CODE_AGGREGATION_v01.csv` is an analysis-species summary and must not be used as a TREE-record code map.

## 5. USGS/Little bridge correction principles
The frozen D08B USGS bridge is not accepted as final because the author-resolution rule produced conservative false negatives (e.g. `Abies grandis` is unresolved in D08B despite an exact, nonzero USGS/Little mapping in eligibility v0.2).

D08B.1 must revise only the bridge, not union layers.

### Author handling
- Resolve Atlas Table 1 concepts by name + author when author is available.
- Permit only lossless author-string canonicalization (Unicode normalization, whitespace normalization, and punctuation/spacing normalization such as `D. Don` vs `D.Don`). No fuzzy matching or edit distance.
- If a canonically author-matched WCVP row exists, its status governs; an Unplaced/invalid/misapplied row may not be replaced by a different author's usable homonym. This preserves the prior `Acer floridanum` safeguard.

### Cross-stage conflict audit
Compare every D08B USGS review/unresolved species against the frozen eligibility-v0.2 `USGS_RANGE_AUDIT.csv`. Any species previously having an exact/official mapped layer with nonzero grid cells but now classified unresolved must enter a dedicated conflict table and receive an explicit cause/proposed resolution. Previous eligibility mapping is diagnostic evidence, not by itself authority.

### Non-native CONUS species
If WCVP confirms a species is not native in CONUS and FIA occurrence is introduced, lack of a Little native-range layer is not a mapping failure for core eligibility. Encode such cases as `NOT_APPLICABLE_CONUS_NONNATIVE` (or equivalent), while retaining audit provenance.

### Review-only cases
Multiple layers, shared/multi-taxon layers, infraspecific-only layer sets, and any Atlas Notes special cases remain review-only. Do not union, select, or reconstruct them in D08B.1.

## 6. Geography
No new CONUS-external range-map search is authorized now. WCVP geography is used only to classify native-range extension states. Targeted external-range completion audit is postponed until after the outcome-blind eligibility cohort is rebuilt and only for remaining borderline species.

## 7. Gate state
- D08B factual correction evidence: PASS.
- Taxonomy patch authorization: PASS.
- D08B USGS/Little bridge: CORRECTION REQUIRED.
- D08C FIA TREE merge: HOLD.
- Real Q1: HOLD.
