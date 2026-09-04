# D10A formal run attempt 1 implementation interruption

Attempt 1 began after the experiment freeze and successfully produced the deterministic 48-state plot-level layout. It was manually interrupted before any synthetic result table was written.

Reason: the deterministic MANUAL-to-generator-effect mapping and standardized plot effort were recomputed inside every synthetic species/regime loop. This was an implementation-only performance defect that would have repeated identical species-blind calculations tens of millions of times.

Correction: cache the exact same MANUAL mapping and standardized effort once per fold in the species-blind layout arrays, then reuse those arrays. No seed, generator parameter, support definition, fitted model, evaluation rule, threshold, split, or terminal interpretation changed.

The incomplete attempt produced no support calibration, leakage, comparison, or terminal-success output. Its layout file is deterministic and may be overwritten byte-for-byte by the corrected full run.
