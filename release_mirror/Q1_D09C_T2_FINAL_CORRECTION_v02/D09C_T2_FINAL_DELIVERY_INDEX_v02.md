# D09C T2 final correction delivery index v02

Date: 2026-09-03  
Nationwide status: **PASS_READY_FOR_MAINLINE_FINAL_D09C_AUDIT**

The predecessor v01 ZIP is embedded unchanged. V02 applies the frozen repair-class hierarchy and the pre-partition WV sparse-EU fallback only. No species or outcome data are present.

| Relative path | Role | Rows | Bytes | SHA-256 | Authoritative |
|---|---|---:|---:|---|---|
| `00_control/D09C_T2_COMPLETION_EXECUTION_FREEZE_v01.md` | control |  | 3085 | `5ead38497b6d8cd3f1a83afb752e0cdcbd268fbd237835973bfeada5932f93fd` | YES |
| `00_control/D09C_T2_FINAL_CORRECTION_EXECUTION_FREEZE_v02.md` | control |  | 3735 | `5b2554a4947ac23580bcfb1765e9b3c715130f87195fdcd89eb2a80b5ffbf7f6` | YES |
| `00_control/Q1_D09C_T2_FINAL_DESIGN_CORRECTION_CONTRACT_v02.md` | control |  | 12047 | `ee3d958d15e74bc54a1b8fc91b2870bf4eb89304f1ed684f980dd8bd4a9fe351` | YES |
| `01_authoritative_inputs/predecessor_v01/Q1_D09C_T2_BOUNDED_COMPLETION_REPRODUCIBLE_v01.zip` | authoritative predecessor |  | 22154334 | `25f361eeeddbe02fd2f93d2daa0b0e974926a8d97965505a3bec37a65388ea7e` | YES |
| `01_authoritative_inputs/predecessor_v01/Q1_D09C_T2_BOUNDED_COMPLETION_REPRODUCIBLE_v01.zip.sha256` | authoritative predecessor |  | 118 | `a3278e0e37cda62690f615e5a8d8b05e115d1fce1f7ebb01178adfa217d7b837` | YES |
| `02_outputs/Q1_D09C_T2_CA_OR_WA_RERANK_AUDIT_v02.csv` | audit output | 3 | 909 | `91f6992a15b66fe795d74243b3415c9f3c901ec20a48b707cacff656bda493b0` | YES |
| `02_outputs/Q1_D09C_T2_FINAL_COMPLETION_QC_v02.csv` | audit output | 18 | 1373 | `ffb220ed6c7f333ba84d28a47cc0db9f41891bef3d49896fb28ca9cd58bb4bfa` | YES |
| `02_outputs/Q1_D09C_T2_FINAL_FOLD_SPECIFIC_TI_DESIGN_v02.csv` | audit output | 5752 | 1492610 | `b8eff0be84e1085c94df485338ee96783d98e400b2eeb11e2c01da8941b77e0b` | YES |
| `02_outputs/Q1_D09C_T2_FINAL_RESULT_NOTE_v02.md` | audit output |  | 1263 | `4df725000378b6df6d89fb48c182c2c9e20c1e2a682f130c8a9e173659cc860b` | YES |
| `02_outputs/Q1_D09C_T2_FINAL_RULE_SELECTED_PARTITIONS_v02.csv` | audit output | 48 | 9615 | `bad20da15f40b288da7ab2ced6510e2e8456eb7d96b86c351a2a16e3d1802e22` | YES |
| `02_outputs/Q1_D09C_T2_OR_412301_MISMATCH_FINAL_AUDIT_v02.csv` | audit output | 4 | 1218 | `4b6e6ae465cebc61c59fb462c8f3ac6d773f40da37858f4f8bad8e3e14a86aef` | YES |
| `02_outputs/Q1_D09C_T2_REPAIR_CLASS_LEDGER_v02.csv` | audit output | 480 | 381978 | `938ece3a46d3294adaf763d4c91523b04e17edac4eebeb554a34be1ebd290dee` | YES |
| `02_outputs/Q1_D09C_T2_SPARSE_EU_TRIGGER_AUDIT_v02.csv` | audit output | 48 | 4835 | `7d4d75a856c3e7e3e0507c2d5871270dfbd761d809c8e4d34d31c1e6a6a0ca65` | YES |
| `02_outputs/Q1_D09C_T2_WV_MERGE_PARTNER_CANDIDATES_v02.csv` | audit output | 10 | 3679 | `feea9c2ea13523d8487ae4f01e75584863e8dbbc3d592c1d4a9dafcdc5f0d1bc` | YES |
| `02_outputs/Q1_D09C_T2_WV_MERGED_FRAME_AUDIT_v02.csv` | audit output | 10 | 3561 | `b658481a79a7844e4177df5c9f23c538fade15cde2e792ddfa95448d2b64ce21` | YES |
| `02_outputs/Q1_D09C_T2_WV_PARTNER_COORDINATE_EVIDENCE_v02.csv` | audit output | 18 | 3984 | `f5eae45bbd539a94722c8c06b09cbdb193f9bf7a11bdef58c66b0abae8a1cbf2` | YES |
| `03_qc/D09C_T2_FINAL_BUILD_SUMMARY_v02.json` | quality control |  | 913 | `78fdef3ff53a4bcc6cb44e740f86622a3626d5a3a2655e2bb8b00156ed151c8e` | YES |
| `03_qc/D09C_T2_FINAL_ENVIRONMENT_v02.json` | quality control |  | 319 | `be9325bba456a952b41a0b0a4d797be4c730706956afc3ef8baa16c16ba4dfaa` | YES |
| `03_qc/D09C_T2_FINAL_IMPLEMENTATION_LOG_v02.md` | quality control |  | 428 | `c27b6bf2bd5e41c529fda9adc5d5e781c12760bf1a358400f6a7debd1e6f0e2a` | YES |
| `03_qc/D09C_T2_FINAL_INDEPENDENT_VALIDATION_v02.json` | quality control |  | 3532 | `7ab02dae0ce61011b172d3cdaea76a3231cd00403e11c964b6e9dc780d6465c0` | YES |
| `03_qc/D09C_T2_FINAL_INPUT_INTEGRITY_v02.csv` | quality control | 39 | 11688 | `5bc12718225af8a35eeaf43b90b832aef0c2124cebe206d6e33c9a7f9bf25ee6` | YES |
| `04_code/build_d09c_t2_final_correction_v02.py` | reproducibility code |  | 42279 | `6983bbc28a3ba70cf5555798b5a03832412e9eb3646467fcec2b82d97e6aa38b` | YES |
| `04_code/finalize_d09c_t2_final_correction_v02.py` | reproducibility code |  | 9789 | `bbc72e35fb462d560958139be025c174e47e191dfd7e9ecb9885cd84a84924af` | YES |
| `04_code/parameters_d09c_t2_final_correction_v02.json` | reproducibility code |  | 1887 | `ff7016e42c8fa2cf259307b16d910c8332dee5172168be77d791055831ef998b` | YES |
| `04_code/predecessor_v01_build_d09c_t2_completion_v01.py` | reproducibility code |  | 55628 | `c9f1167f76f8cb15b4f5db31c1442f86522b927a1d1825801a8f0f1547d2a773` | YES |
| `04_code/verify_d09c_t2_final_correction_v02.py` | reproducibility code |  | 8759 | `9038f0935c3b8717934f02505e62c2795114e8bd8ebe564b2533b76a3b21b187` | YES |
