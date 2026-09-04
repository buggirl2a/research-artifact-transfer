# D08C2 corrected constructibility execution freeze v01

Task ID: `D08C2_CORRECTED_CONSTRUCTIBILITY_v01`

This execution freeze was written before reading any TREE.SPCD value, accepted-species identity, or D08C2 survivor count.

## Immutable authorities

- Contract attachment SHA-256: `041f57cb5d850e051a7dfc912a0678db1fdcd46df9efa75b7fcc5251dd15afc6`.
- Range Gate v02 ZIP SHA-256: `717767f71216bca5fca3e7d43762c7fa026e7e799be162d05a68d3ab45bf4d50`.
- D09C T2 final correction v02 ZIP SHA-256: `07cb461121c71ef46990fea3e0cf9d8f139fd873234b9f57910ff10c7c33752f`.
- National FIADB ZIP path: `C:\range_paper\02_raw\FIA\SQLite_FIADB_ENTIRE.zip`.
- National FIADB ZIP expected bytes: `15351832599`.
- National FIADB ZIP expected SHA-256: `ec2e4caf2a92e6079c20483f4a5f08d5ec2e7c31f498045237896a6df7e1565e`.
- CA/OR/WA observational overrides: the nine frozen ZIPs under `C:\range_paper\02_raw\fia_t2_2023_observational_gap_v01\raw_table_zips`, identified by the accepted local manifest.

No network acquisition or replacement FIADB snapshot is permitted.

## Frozen P0 gate

Before species values are read, every actually used source must expose every required field listed in sections 7 and 5 of the contract. Any missing field produces `INPUT_BLOCKED_REQUIRED_SCHEMA_FIELD_MISSING` and immediate STOP.

P0 was evaluated only from schemas/headers. No TREE.SPCD value, accepted-species identity, or survivor count was read during P0.

## Frozen D1-D4 rules

- Starting universe is exactly the Range Gate v02 rows with `range_gate0_v02_class == PASS_COARSE`; it must contain exactly 101 accepted species.
- Raw TREE codes map only through frozen D08B1 v02 before accepted-species aggregation.
- Operational native domains use only frozen WCVP state records with native confirmed and introduced/extinct/location_doubtful all zero.
- Candidate target records are live (`STATUSCD == 1`) with current `DIA >= 5.0`, inside the frozen F0 frame and operational native domain.
- Observation unit is FIA plot-visit (`PLOT.CN`). A zero is generated only after the plot is in the F0 fold and native domain, `PLOT_STATUS_CD == 1`, at least one linked accessible forest condition has `COND_STATUS_CD == 1`, at least one relevant linked subplot is sampled with `SUBP_STATUS_CD == 1`, and all required linkages are deterministic.
- Partial sampling remains legitimate and its effort metadata is retained.
- Primary provisional eligibility requires positive opportunity and positive encounter counts in both A and B. No further count, cell, abundance, precision, occupancy, support, or model threshold is permitted.
- No grid is required or generated.

## Frozen task PASS/FAIL

`PASS_READY_FOR_MAINLINE_OBSERVATION_GATE_AUDIT` requires exactly 101 mechanically classified species, unchanged D1-D4 rules, passing input/schema/QC checks, no prohibited downstream computation, and a reproducible package. The eligible count is never a task criterion.

Allowed pre-computation blocks are exactly those stated in the contract. Any block triggers immediate STOP without summarizing true species eligibility.

## Absolute boundary

This branch stops after D08C2 deliverables. It does not fit occupancy/encounter models, estimate support or abundance, select a final cohort, evaluate geometry or World 0, or run real Q1.
