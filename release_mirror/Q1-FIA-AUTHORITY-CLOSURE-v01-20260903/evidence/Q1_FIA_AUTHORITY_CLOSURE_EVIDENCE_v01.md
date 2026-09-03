# Q1 FIA reporting-frame raw-authority closure v01 — official evidence

Date: 2026-09-03
Scope: official-source factual closure only. No Q1 analysis, no D09C rerun, no A/B selection, no TI/MA choice, no species/TREE analysis.

## Authority rule used

The official FIADB-API documentation defines `wc` as the evaluation-group code for the inventory of interest and directs users to `/fullreport/parameters/wc` for the valid values. Therefore the current official `wc` parameter table is treated as the positive authority for which reporting/evaluation groups are currently valid. No numeric component EVALID is reconstructed from naming conventions.

Official documentation: https://apps.fs.usda.gov/fiadb-api
Official valid-value table: https://apps.fs.usda.gov/fiadb-api/fullreport/parameters/wc

## CA2022

**Status: `OFFICIAL_UNAVAILABLE_CONFIRMED` (current official reporting/evaluation-group authority).**

Evidence chain:

1. The FIADB-API documentation states that valid `wc` evaluation-group values are enumerated in the official `wc` parameter table.
2. In the California section of the current table, the sequence is `062023 CALIFORNIA`, then `062021 CALIFORNIA`, followed by older groups. There is no `062022 CALIFORNIA` valid value.
3. The official PNW-FIA downloadable California/Oregon/Washington SQLite page, updated 2026-03-10, says that its California data extend only through inventory year 2021. Thus that official raw regional asset also does not provide a CA-2022 reporting frame.
4. The FIADB Update History contains a 2024-09-20 update to California 62021 data but no explicit 62022 entry. This absence is supporting context only; the closure rests on the documented exhaustive valid-value table, not on a search failure.

Interpretation boundary: this is a statement about the current official FIA reporting/evaluation-group authority. It is not a historical assertion that an internal or withdrawn CA-2022 object never existed. No EVALID is guessed.

## CA2023

**Status: `OFFICIAL_AVAILABLE_REPRODUCIBLE`.**

The official current `wc` table explicitly lists:

- EVALID display label: `062023 CALIFORNIA`
- EVAL_GRP: `62023`
- reporting years: 2013–2023
- growth-account flag: Y
- most-recent flag: Y

The official endpoint is stable and reproducible as a current metadata authority. The exact component EVALID is **not** inferred and is recorded as `NOT_RESOLVED_NO_GUESS`.

Important raw-data caveat: the official PNW regional CA/OR/WA SQLite download (updated 2026-03-10; 1.1 GB) states that California is included only through 2021. Therefore that downloadable raw asset cannot be used to reconstruct CA2023 design metadata. A downstream D09C rerun would require a separately identified current official raw asset/authority containing the 2023 population tables; this task does not acquire it.

## OR2023

**Status: `OFFICIAL_AVAILABLE_REPRODUCIBLE`.**

The official current `wc` table explicitly lists:

- EVALID display label: `412023 OREGON`
- EVAL_GRP: `412023`
- reporting years: 2014–2023
- growth-account flag: Y
- most-recent flag: Y

The exact component EVALID is not inferred. The current official PNW regional SQLite download contains Oregon only through 2022, so that 1.1 GB asset does not close raw-design availability for OR2023. Authority existence is nevertheless closed by the official live valid-value metadata.

## WA2023

**Status: `OFFICIAL_AVAILABLE_REPRODUCIBLE`.**

The official current `wc` table explicitly lists:

- EVALID display label: `532023 WASHINGTON`
- EVAL_GRP: `532023`
- reporting years: 2014–2023
- growth-account flag: Y
- most-recent flag: Y

The exact component EVALID is not inferred. The current official PNW regional SQLite download contains Washington only through 2022, so that 1.1 GB asset does not close raw-design availability for WA2023. Authority existence is nevertheless closed by the official live valid-value metadata.

## Official raw-download finding

The Forest Service DataMart description confirms that FIA DataMart distributes raw files and SQLite databases. The PNW-FIA regional database page provides a specific 1.1 GB CA/OR/WA SQLite asset, but its stated inventory coverage is CA through 2021 and OR/WA through 2022. It was therefore **not downloaded**, because it cannot supply the three 2023 target frames and is not needed to decide the four authority statuses.

No new national FIADB download was initiated. If the scientific mainline later requires a D09C rerun against raw 2023 population/design tables, a new bounded acquisition request should first identify the exact official updated raw asset or current raw database authority. That downstream acquisition is outside this task.

## Official sources accessed

1. FIADB-API & EVALIDator documentation — https://apps.fs.usda.gov/fiadb-api
2. FIADB-API `wc` parameter table — https://apps.fs.usda.gov/fiadb-api/fullreport/parameters/wc
3. FIADB Update History — https://apps.fs.usda.gov/fiadb-api/fiadb_update_history
4. PNW-FIADB databases — https://research.fs.usda.gov/pnw/products/dataandtools/pnw-fiadb-forest-inventory-and-analysis-databases
5. FIA DataMart description — https://research.fs.usda.gov/products/dataandtools/fia-datamart

STOP: no T1/T2 selection, no D09C rerun, no D08C2, no Little, no real Q1.
