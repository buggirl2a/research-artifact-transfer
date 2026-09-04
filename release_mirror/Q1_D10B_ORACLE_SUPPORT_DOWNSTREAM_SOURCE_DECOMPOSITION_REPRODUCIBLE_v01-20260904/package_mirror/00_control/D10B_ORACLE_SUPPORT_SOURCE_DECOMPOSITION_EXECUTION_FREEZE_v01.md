# D10B Oracle-Support Source-Decomposition Execution Freeze v01

Frozen before the first L0/L1 experiment run on 2026-09-04 (Asia/Shanghai).

## Input identity gate

The sole input is the D10A reproducible ZIP named in the D10B contract. Its outer SHA-256 must equal `20e5d3ed33df6414b72a6e679d5349f3b10fe6397ce73f98b51d0bcc96033013`. Internal members used in D10B must match the D10A package's own `SHA256SUMS.csv`. Failure of the ZIP, internal checksum, 72-species identity, manifest identity, split identity, support identity, or abundance-pair identity gate terminates as `INPUT_BLOCKED_D10A_WORLD_IDENTITY_FAILURE`.

## Computation frozen before results

1. Load the exact D10A code, parameters, F0 layout, synthetic-world manifest, and leakage-audit results from the frozen ZIP only.
2. Mechanically regenerate D10A true supports and STRONG/PAIRED_NULL latent abundances with the frozen generator and seeds.
3. Mechanically regenerate only the target-fold observed-abundance count stage using the exact corresponding code path, parameters, and seeds. O1/O2/O3 identities remain D10A identities; no encounter/support-recovery stage is used for L1.
4. Verify regenerated manifest fields and per-species/world identity invariants before downstream evaluation.
5. Evaluate L0 and L1 with the unchanged D10A World 0, gamma grid, geometry feature set, ridge alpha, sliced-Wasserstein metric, split assignments, and 90% split-conformal construction.
6. Duplicate oracle-layer results only where a frozen factor is structurally irrelevant: regimes for L0/L1, and orientation for L0. Preserve all required alignment keys.
7. Create L2 exclusively by copying and aligning D10A leakage-audit reference rows; do not recompute it.
8. Compute PAIRED_NULL stepwise increments and STRONG-minus-PAIRED_NULL separations mechanically. No threshold, winner, repair, tuning, or scientific PASS/FAIL is defined.

## Frozen output schema and row expectations

- oracle world identities: one row per synthetic species × world, with manifest/identity evidence;
- L0: 2 worlds × 3 regimes × 2 orientations × 5 splits = 60 rows;
- L1: 60 rows;
- L2: 3 models × 2 worlds × 3 regimes × 2 orientations × 5 splits = 180 rows;
- paired-null source decomposition: one row per model × regime × orientation × split = 90 rows;
- strong-null separation: L0 30 + L1 30 + L2 90 = 150 rows;
- diagnostic summary: grouped evidence pattern only, without a decision threshold.

Any departure from this freeze requires mainline authorization and is outside D10B.
