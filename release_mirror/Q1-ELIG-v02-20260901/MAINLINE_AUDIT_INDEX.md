# Q1 ELIGIBILITY CENSUS v0.2 — MAINLINE AUDIT INDEX

## Scope and boundary

This package is an outcome-blind eligibility census on the frozen `RAW_FREEZE_v02` inputs. It does not fit a real-Q1 model, compute range–abundance coupling or geometry gain, compare R1/R2, run significance tests, select a final grain/threshold/species cohort, or use abundance/geometry outcomes to filter taxa.

The authoritative analysis domain is conterminous 48 states plus DC if present. DC has no SURVEY state entry in this FIADB snapshot. Alaska, Hawaii, and territories are reported separately and excluded from the primary census. FIA denominator cells are fixed-grid cells represented by at least one primary eligible plot; unsampled cells are not invented as zeros.

## Core audit files

- `INPUT_AUDIT.csv`: frozen archive, control, request, D04 source, and parameter hashes/sizes.
- `D04_CONTINUITY_AUDIT.csv`: exact D04 source hash plus projection, fixed-grid, and A/B reproduction checks against retained D04 pilot records.
- `LINEAGE_AUDIT.csv`, `REGION_COVERAGE_AUDIT.csv`: 2017–2023 eligibility, PREV_PLT_CN lineage de-duplication, primary-measurement selection, coordinate coverage, and excluded-region counts.
- `AB_SPLIT_AUDIT.csv`, `AB_SPLIT_SUMMARY.csv`: every state × P2PANEL stratum, A/B sizes, balance, missing-panel count, and leakage/duplication checks.
- `DOMAIN_GRID_AUDIT.csv`: projection, common origin, 25/50/75-km cell counts, parent mapping, and eligible plots per cell.
- `SPECIES_GRAIN_CENSUS.csv`: complete 396-taxon × 3-grain table with sampling, detections, A/B overlap, continuous geometry diagnostics, TPA_UNADJ availability, and protocol indicators.
- `FOLD_METRICS.csv`: complete taxon × grain × A/B table with eligible plots, positive plots, qualifying tree records, and detected-cell counts.
- `TAXONOMY_CROSSWALK.csv`: exact-name-only FIA–USGS mapping; no fuzzy matching.
- `USGS_SEMANTIC_EQUIVALENCE_AUDIT.csv`: full CSV-versus-NetCDF comparison, including 690 full-grid binary PA comparisons.
- `USGS_RANGE_AUDIT.csv`: US, CONUS, Canada, US+Canada cell counts and continuous component/largest-component/span clipping diagnostics for exact matches.
- `ELIGIBILITY_FRONTIERS.csv`: full frozen Cartesian frontier over grain, total detected-cell, per-fold detected-cell, per-fold positive-plot, and optional US-share nodes. These are descriptive nodes, not selected standards.
- `OBJECTIVE_FLAGS.csv`, `PROTOCOL_FLAGS.csv`, `GLOBAL_RANGE_REVIEW_QUEUE.csv`: objective risk flags and future-review queues; flags are not exclusion decisions.
- `TRACEABILITY_SAMPLE_SELECTION.csv`, `TRACEABILITY_SAMPLE.csv`: deterministic high/middle/low detection-band species selections and positive/negative plot examples with exact lineage, measurement, fold, and grid IDs.
- `REPRODUCIBILITY_CHECKS.csv`, `QC_SUMMARY.json`: independent structural/arithmetic verification (31/31 PASS).
- `NO_Q1_OUTCOME_AUDIT.json`: prohibited-output audit.
- `Q1_ELIGIBILITY_CENSUS_AUDIT_v0_2.xlsx`: styled 16-sheet audit workbook; canonical long trace identifiers are preserved as text.
- `FIGURE_01_TOTAL_CELL_FRONTIER.png`, `FIGURE_02_AB_IOU_DISTRIBUTION.png`, `FIGURE_03_USGS_CLIPPING_DIAGNOSTIC.png`: outcome-blind audit figures only.
- `PRECHECK_RESOLUTION_LOG.md`: transparent record of the non-scientific NetCDF projection-metadata label correction made before the final full run.
- `CENSUS_RESULT_NOTE.md`, `RUN_SUMMARY.json`, `IMPLEMENTATION_LOG.md`, `SOFTWARE_ENVIRONMENT.json`: concise results, execution stages, and runtime versions.

## Mainline decisions deliberately not made

- Final 25/50/75-km grain.
- Formal sampling, per-fold detection, taxonomy, or range-completeness thresholds.
- Final paper species cohort.
- Whether the absent official accepted↔original USGS name table warrants a narrowly scoped future audit for the 127 unresolved names.
- Whether Mexico/global range extensions warrant a separately authorized data audit; frozen CANUSA data cannot answer this.
- Whether and how formal FIA population expansion and sampling variance enter a later abundance object. `TPA_UNADJ` availability is audited, but formal population weighting/variance estimation is not applied here.

## Known protocol facts retained as flags

- FIADB woodland taxa use DRC/root-collar diameter rather than standard DBH; the common 5-inch DIA screen is therefore not assumed directly cross-taxon comparable.
- PREV_PLT_CN is used exactly as frozen for physical lineage construction; no unapproved composite-key linkage was invented when historical links were absent.
- Hard detection (`at least one qualifying live TREE record with DIA ≥ 5 inches in a forest condition`) is an observation fact, not latent support truth.
- USGS CSV is the primary representation. NetCDF latitude/longitude precision differs as documented; PA, ID, row, column, and elevation semantics passed the frozen checks.

STOP after mainline delivery. This branch does not enter real-species Q1 analysis.
