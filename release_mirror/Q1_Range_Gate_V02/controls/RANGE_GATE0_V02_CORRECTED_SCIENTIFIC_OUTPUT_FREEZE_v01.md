# Range Gate 0 v02 corrected scientific-output freeze v01

Frozen: 2026-09-03, after fresh D08B1-based computation and independent core verification, and before reading the v01 classification for delta construction.

## Status at freeze

- Execution: PASS.
- Scientific contract: corrected v02 semantics, pre-frozen before counts.
- Accepted master: 361 unique species.
- Candidate universe: 312 unique species with `confirmed_native_CONUS == TRUE`.
- Class counts: `FAIL_EXTRA_NA=10`, `BORDERLINE_OTHER_NA=21`, `BORDERLINE_MEXICO=94`, `RETAIN_USCA_AUDIT=86`, `PASS_COARSE=101`, `UNKNOWN=0`.
- Build QC: 31/31 PASS.
- Independent core output-only audit: 30/30 PASS.
- Mandatory semantic regression fixtures: 7/7 PASS.
- Transcontinental independent routing triggers: 0.
- Final cohort selections: 0.
- v01 classification read during v02 construction: NO.

## Frozen core scientific outputs

| File | Bytes | SHA-256 |
|---|---:|---|
| `Q1_RANGE_GATE0_V02_CORRECTED_SPECIES_CLASSIFICATION_v01.csv` | 428483 | `d0ff6281d3e5a8aa2cb1438fd70cc2650163b6c512ffe8299c24d3555ddfcb64` |
| `Q1_RANGE_GATE0_V02_CORRECTED_SUMMARY_v01.csv` | 399 | `6fff3e6f9c90957e1c652c00691b1bf2437ef8f5f7253fb48ec266336fa92205` |
| `Q1_RANGE_GATE0_V02_CORRECTED_DECISION_QUEUE_v01.csv` | 280858 | `da944cc5c7d035cd15cad49df76c620e1169dc18136703c16355a3a4e2bab69c` |
| `Q1_RANGE_GATE0_V02_CORRECTED_FAIL_EXTRA_NA_v01.csv` | 43354 | `3f819a334126cbc2c66a05a3016db9ba310eb6fe9d065c4a9d15fb54408ecf2d` |
| `Q1_RANGE_GATE0_V02_CORRECTED_QC_v01.csv` | 2643 | `5a38a871d6ad6a5dff23e4ff7b106cacfef584c2eaa7ffa729252268f0443081` |
| `RANGE_GATE0_V02_CORRECTED_CORE_INDEPENDENT_AUDIT_v01.json` | 6576 | `643c57788b82bb3c9dfcfeb1281bec49b0c00ef85e5c179deae08533cb6e8516` |

These core outputs are immutable. The subsequent v01→v02 delta audit is additive and must compare against these frozen bytes; it may not alter them. Packaging and transfer metadata likewise may not mutate or recompute them.

## Scientific interpretation boundary

The transcontinental flag is diagnostic-only. No Level-3 unit count was interpreted as area/share/severity, no geometry was reconstructed, and no Little content, external search, D08C2, FIA outcome/eligibility, abundance/detection, final cohort, or real Q1 was used.

Range Gate 0 v01 remains unchanged and is labeled `MAINLINE_CONTRACT_SEMANTICS_FAIL / COMPUTATIONAL_EXECUTION_PASS`.
