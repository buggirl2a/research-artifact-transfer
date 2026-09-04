# D10B oracle-support downstream source-decomposition result

Terminal status: `DIAGNOSTIC_COMPLETE_READY_FOR_MAINLINE_SOURCE_ATTRIBUTION`

D10B is diagnostic only. It defines no scientific PASS/FAIL, chooses no observation model, and does not repair World 0 or support recovery.

## Q1 — Exact support plus latent abundance

Across the six regime × orientation summaries, 0/6 PAIRED_NULL median geometry gains were positive. The pooled median of those six medians was -0.627 percentage points (range -0.627 to -0.627).

## Q2 — Target-fold abundance sampling increment

The pooled median L1−L0 geometry-gain increment was 4.095 percentage points across the six regime × orientation summaries (range 3.970 to 4.221).

## Q3 — Estimated-support increment

- M0: pooled median L2−L1 geometry-gain increment -12.440 percentage points; pooled median L2 paired-null geometry gain -7.110%.
- M1: pooled median L2−L1 geometry-gain increment 60.868 percentage points; pooled median L2 paired-null geometry gain 64.865%.
- M2: pooled median L2−L1 geometry-gain increment 37.876 percentage points; pooled median L2 paired-null geometry gain 43.853%.

## Q4 — Evidence pattern

The absolute pooled-median diagnostic components rank as: support recovery M1 60.868 points; support recovery M2 37.876 points; support recovery M0 12.440 points; abundance measurement 4.095 points; downstream comparator 0.627 points. This is a descriptive magnitude pattern, not a causal decomposition and not a mainline scientific decision.

## Q5 — STRONG versus PAIRED_NULL separation

- L0-ORACLE: pooled median STRONG−PAIRED_NULL geometry-gain separation 6.054 percentage points.
- L1-ORACLE: pooled median STRONG−PAIRED_NULL geometry-gain separation -120.656 percentage points.
- L2-M0: pooled median STRONG−PAIRED_NULL geometry-gain separation -38.982 percentage points.
- L2-M1: pooled median STRONG−PAIRED_NULL geometry-gain separation 0.126 percentage points.
- L2-M2: pooled median STRONG−PAIRED_NULL geometry-gain separation -33.876 percentage points.
- L0 to L1: separation decreased by 126.710 points (worsened).
- L2-M0 versus L1: separation increased by 81.674 points (improved relative to L1); versus L0 it changed by -45.036 points and remained lower than L0.
- L2-M1 versus L1: separation increased by 120.782 points (improved relative to L1); versus L0 it changed by -5.928 points and remained lower than L0.
- L2-M2 versus L1: separation increased by 86.780 points (improved relative to L1); versus L0 it changed by -39.930 points and remained lower than L0.

## Reproducibility qualification

The D10A true supports, latent abundance pairs, manifest fields, seeds, splits, parameters, and downstream functions were mechanically recovered from the checksum-verified D10A release. L2 rows are direct copies of its leakage-audit table. D10A did not publish its hidden cell-level observed-abundance arrays or pre-export in-memory plot order; L1 therefore reconstructs the released count stage using the canonical published F0 layout row order plus the frozen code and seeds. This limitation is explicit and no alternative data were accessed.

STOP: no repair, D10C, real-species support, real abundance, cohort, or real Q1 analysis was run.
