# Q1 Range Gate 0 input freeze v01

Date: 2026-09-03  
Status: frozen before classification execution.

All authorized inputs were copied byte-for-byte to `C:\range_paper\03_doc\RANGE_GATE0_INPUTS_v01\`.

| Frozen file | Bytes | SHA-256 | Role |
|---|---:|---|---|
| `Q1_WORK_REQUEST_RANGE_GATE0_WHOLE_RANGE_COMPLETENESS_COARSE_SCREEN_v01_20260903.md` | 15725 | `7b08106d190ac539e6f8127a656d36a764dc7f08a800e405d85aa0699612abd9` | Scientific mainline request and class precedence. |
| `Q1_TAXON_RANGE_D08B1_CORRECTED_REPRODUCIBLE_v02.zip` | 7408346 | `3647c35189110d524d5f6cd64bf2d4aabaaa80828e58f42e767bb5e862188a3e` | Complete frozen D08B1 v02 authority. |
| `Q1_TAXON_RANGE_D08B1_CORRECTED_REPRODUCIBLE_v02.zip.sha256` | 118 | `b8d2bf7537d024da63ca48ec366c6379fa340013725c70bc62983579252c5ce9` | D08B1 ZIP sidecar. |
| `d08b1_v02_authority/Q1_ANALYSIS_SPECIES_MASTER_v02.csv` | 89217 | `6f69874ab02723b3489aa4f3cbfb5aba188147400efdf170f27ad699d6368cb0` | 361-species accepted analysis master. |
| `d08b1_v02_authority/Q1_GLOBAL_RANGE_FLAGS_v02.csv` | 191352 | `dc64778032ed9bd301bfc7c14818fc3ba71a3b2621bb4e8b33ec558ecdf3d16d` | Frozen species-level global-range flags. |
| `d08b1_v02_authority/Q1_WCVP_NATIVE_DISTRIBUTION_LONG_v02.csv` | 1631728 | `559a2d6f7b0d67ad886468a2c0098e117c824f196f0a85d3bb7d99c466649017` | Frozen 9,648-row WCVP Level-3 evidence. |
| `d08b1_v02_authority/D08B1_TAXONOMY_USGS_BRIDGE_CONTRACT_v02.md` | 7120 | `bd756e111dc2cfe2e983d5f2b421846c85213612b167a111d0d0ee3d14ae40c8` | Frozen D08B1 semantic contract. |
| `d08b1_v02_authority/D08B1_PARAMETERS_v02.json` | 983 | `65a5f60b03770c84401a1b3c741c548df10b5d972e86a35f91b3f3cd66273db7` | Frozen D08B1 parameter record. |
| `d08b1_v02_authority/build_taxon_range_d08b1_v02.py` | 86536 | `fad43f2fe935738585f78d4078b59b992de61bcb10a5ad89f1ede097055d821d` | Frozen executable evidence for macro-region predicates. |

The three required authority-member hashes and the complete D08B1 ZIP hash match the scientific mainline request exactly. No GitHub download or other network access was needed.

The input-universe count is deliberately not recorded here; it will be evaluated by the blocked preflight in the frozen execution code. Any result other than exactly 361 master rows and 312 `confirmed_native_CONUS == TRUE` species is `INPUT_BLOCKED`.

No Little layer content, FIA outcome/eligibility data, external range source, geometry object, or real-Q1 result is an authorized input.
