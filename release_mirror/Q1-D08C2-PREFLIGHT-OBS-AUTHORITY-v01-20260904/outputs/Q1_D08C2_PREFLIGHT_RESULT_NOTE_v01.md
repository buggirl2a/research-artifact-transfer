# Q1 D08C2 preflight observational authority closure v01

Task: `D08C2_PREFLIGHT_OBS_AUTHORITY_v01`
Status: **PREFLIGHT_BLOCKED_ACQUISITION_GAP_IDENTIFIED**
Generated: 2026-09-04 02:08:25

## Scope
This is the final narrow preflight before the corrected D08C2 contract. It does not run D08C2 and does not evaluate any species. It verifies local observational input authority, minimum FIA table/field support for legitimate large-tree observation opportunities, and structural compatibility with frozen F0 inputs.

## Frozen scientific boundaries preserved
- No species-level eligibility or outcome result was read.
- No abundance total, TPA-based species threshold, support estimate, occupancy probability, encounter-cell threshold, grid, World 0, R1/R2, or Q1 result was computed.
- F0 T2/EXPVOL/A-B/fold-specific-TI decisions are inputs, not re-selected.
- WCVP confirmed-native state remains an operational state-level native target domain; it does not establish individual TREE provenance.
- No local or central Registry file was edited; only `REGISTRY_DELTA_v01.csv` is proposed for mainline audit.

## Observation-opportunity implication
The minimum observational bundle is TREE + PLOT + COND + SUBPLOT, plus the already-frozen F0 design tables/assets and the frozen FIA national field-guide species/protocol authority. Absence of a TREE row is never a zero by itself. A legitimate non-detection can only be constructed after F0/native-domain membership, sampled accessible-forest opportunity, and applicable FIA tally-tree protocol eligibility are established.

## Acquisition decision
See `Q1_D08C2_PREFLIGHT_ACQUISITION_GAPS_v01.csv`. Data Search should be invoked only if this ledger contains genuine missing tables/fields or stale F0 coverage after mainline audit.

## Working extraction
If the national FIADB SQLite was not already present as an exact extracted copy, this preflight may extract the single immutable ZIP member into `99_tmp\d08c2_preflight_observational_authority_v01\source_cache`. This is a working copy only; the canonical raw authority remains the frozen ZIP and its SHA-256.
