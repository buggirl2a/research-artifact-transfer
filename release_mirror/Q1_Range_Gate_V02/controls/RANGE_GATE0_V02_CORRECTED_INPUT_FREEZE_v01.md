# Range Gate 0 v02 corrected input freeze

Frozen: 2026-09-03, before any v02 class count was computed.

## Mainline request

- File: `Q1_WORK_REQUEST_RANGE_GATE0_v02_CORRECTED_GEOGRAPHIC_SEMANTICS_20260903.md`
- Bytes: 14918
- SHA-256: `cd74476cee906ba7c8333e928daf177f8e35969ff8e50ad277bcb4acb44e081f`

## Unchanged D08B1 v02 authority

| File | Bytes | SHA-256 |
|---|---:|---|
| `Q1_TAXON_RANGE_D08B1_CORRECTED_REPRODUCIBLE_v02.zip` | 7408346 | `3647c35189110d524d5f6cd64bf2d4aabaaa80828e58f42e767bb5e862188a3e` |
| `Q1_ANALYSIS_SPECIES_MASTER_v02.csv` | 89217 | `6f69874ab02723b3489aa4f3cbfb5aba188147400efdf170f27ad699d6368cb0` |
| `Q1_GLOBAL_RANGE_FLAGS_v02.csv` | 191352 | `dc64778032ed9bd301bfc7c14818fc3ba71a3b2621bb4e8b33ec558ecdf3d16d` |
| `Q1_WCVP_NATIVE_DISTRIBUTION_LONG_v02.csv` | 1631728 | `559a2d6f7b0d67ad886468a2c0098e117c824f196f0a85d3bb7d99c466649017` |

Local copies are under `C:\range_paper\03_doc\RANGE_GATE0_V02_CORRECTED_INPUTS_v01\`. All four authority hashes match the mainline request.

## v01 immutable baseline

The following digest covers 76 path/byte/SHA records across the existing v01 `07_results`, `05_qc`, and `10_archive` trees, ordered deterministically. It is an immutability sentinel, not a v02 scientific input.

- Baseline tree digest: `a415cbc84b66f6d0bf01c4cfaab3449e9e49e872bed7464cf2d71a29f65e9100`
- v01 reproducible ZIP SHA-256: `ec99bf40ca5a22ae856ec8228b053fedf959af64675fc1cc5d99b4827fb0aafd`
- v01 classification SHA-256: `243978406cb913c13898b333671000c30592079d076ef8b995822a1684f8a8cd`
- v01 transfer manifest SHA-256: `53a7674acd744c80e91ed3c1a3ce750e6c56bfd68b40129baf5b142903df76f9`

No v01 file will be opened as a classification source until v02 scientific outputs have been independently checked and frozen. No v01 file may be modified.
