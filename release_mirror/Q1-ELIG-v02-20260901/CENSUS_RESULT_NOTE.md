# Q1 OUTCOME-BLIND ELIGIBILITY CENSUS RESULT NOTE

Generated: 2026-09-02T01:21:21+08:00

## Engineering and input integrity

- Engineering status: PASS.
- RAW_FREEZE_v02 formal raw archives: 3/3 PASS by exact size and SHA-256.
- Candidate domain: conterminous 48 United States plus District of Columbia if present in FIADB; DC had no SURVEY state entry in this snapshot.
- Eligible 2017–2023 measurements before lineage de-duplication: 128,714.
- Primary measurements after PREV_PLT_CN lineage de-duplication: 115,725; spatially usable: 115,725.

## Grain-level sampling/detection information

- 25 km: sampled cells=10,051; species-level taxa=396; each fold >=5 detected cells=275; each fold >=10 positive plots=257.
- 50 km: sampled cells=2,970; species-level taxa=396; each fold >=5 detected cells=275; each fold >=10 positive plots=257.
- 75 km: sampled cells=1,441; species-level taxa=396; each fold >=5 detected cells=269; each fold >=10 positive plots=257.

These are descriptive census facts. They do not choose a final grain or threshold.

## A/B feasibility split

- Fold A primary measurements: 57,920.
- Fold B primary measurements: 57,805.
- Duplicate lineage across folds: 0.
- Split is D04 feasibility-only and is not declared the final cross-fitting design.

## USGS/Little range completeness

- Exact FIA-to-USGS name matches: 269; unresolved without fuzzy matching: 127.
- Matched taxa with at least one Canada atlas cell: 101.
- Median US share of US+Canada mapped cells among matched taxa: 1.0000.
- Area share, component change, largest-component change, and span retention are reported separately because high US share does not guarantee low geometric truncation.
- Mexico/global extension status remains NOT_ASSESSED from the frozen CANUSA data.

## Mainline decisions still required

- Final 25/50/75-km grain.
- Final sampling, per-fold detection, taxonomy, and range-completeness thresholds.
- Final analytic species cohort.
- Whether unresolved official accepted-name mappings or Mexico/global ranges require a narrowly scoped future audit.
- Whether and how formal FIA population expansion/variance estimation will enter the later abundance object.

## Outcome-blind statement

No real Q1 model, geometry gain, range-abundance coupling, R1/R2 comparison, significance test, or outcome-based species filtering was run. Hard detection is not interpreted as latent support truth.
