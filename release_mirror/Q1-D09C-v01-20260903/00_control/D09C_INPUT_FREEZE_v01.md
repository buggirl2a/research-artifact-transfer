# D09C input freeze v01

Date: 2026-09-02  
Status: **PASS / FROZEN BEFORE DESIGN AUDIT COMPUTATION**

## Formal FIADB input

| Role | File | Bytes | Integrity value | Status |
|---|---|---:|---|---|
| formal raw archive | `C:\range_paper\02_raw\FIA\SQLite_FIADB_ENTIRE.zip` | 15,351,832,599 | SHA-256 `ec2e4caf2a92e6079c20483f4a5f08d5ec2e7c31f498045237896a6df7e1565e` | PASS, freshly rehashed 2026-09-02 |
| extracted read-only database member | `C:\range_paper\99_tmp\elig_v02\SQLite_FIADB_ENTIRE.db` | 71,565,119,488 | ZIP-member CRC-32 `a2bc6055`; size/CRC previously independently verified in frozen D08C1 input audit | PASS |

Only the design-metadata tables whitelisted in `D09C_SPECIES_BLIND_DESIGN_AUDIT_CONTRACT_v01.md` may be read. The SQLite database is opened read-only.

## New request and mainline authority

| File | Bytes | SHA-256 |
|---|---:|---|
| `Q1_WORK_REQUEST_D09C_SPECIES_BLIND_REPORTING_STATE_PANEL_FOLD_AUDIT_v01_20260902.md` | 6,227 | `e01b15f73cc0d34f22d9a7187322ab926ae9de9a6a08c6ef0d4921c18ece4f1f` |
| `Q1_D09B_MAINLINE_DECISION_v01_20260902.md` | 5,150 | `9f3fd7e9e6bbdc4cdeae4a290ca7a1b983eeb2638175c49c0a47949e66f3c2e7` |
| `Q1_WORK_MAINLINE_ADDENDUM_D09C_RANGE_GATE_ORDER_v01_20260902.md` | 3,255 | `54bf6cde8bcef2f22e58ca5c65f6420999b8dafcafdfd83a2dff02fab1b53f7e` |

Exact project-controlled copies are stored under `C:\range_paper\03_doc\D09C_SPECIES_BLIND_DESIGN_INPUTS_v01\`.

## Upstream factual-closure packages

| Package | Bytes | SHA-256 | Member-ledger verification |
|---|---:|---|---|
| `D09_FIA_DESIGN_BASED_POPULATION_MASS_EVIDENCE_v01.zip` | 24,988 | `03e6d4a48144baa208b1387aa8f615cd8fe71ef6881d6a3c9f843e9fea937cff` | 7/7 member hashes PASS |
| `D09B_2023_EVALID_PANEL_AB_DESIGN_EVIDENCE_v01.zip` | 18,123 | `618b72fc802875c5fa0e54022a9a8cff6b62724fdc485307e6382990b4ea6f06` | 8/8 member hashes PASS |

Both ZIP hashes match their supplied sidecars and the Downloads originals. Every package member was read completely before D09C computation.

## Frozen controls

| File | Bytes | SHA-256 |
|---|---:|---|
| `RAW_FREEZE_v02.md` | 2,345 | `878bfeb09d474cd6e69ec787eac8bb69d7c14d802620c3d7b653d27f6b3470ce` |
| `raw_manifest_v02.csv` | 1,774 | `ed3dead2cb0e516f95ec51c417ffa221e0f22f8dbfe695fac1d1f533ea0b0dc1` |
| `sha256_raw_v02.txt` | 379 | `fec418fcbd714f7d856e5791001a68a49e72b771900543aac70ef4141e04eb94` |
| `D09C_SPECIES_BLIND_DESIGN_AUDIT_CONTRACT_v01.md` | 8,407 | `a4a292c3e0db156e8f46a8e82510f79df53074792e6385eb65b58f83d5abef5a` |
| `parameters_d09c_v01.json` | 1,398 | `03bcae8b9de4913f6ef4f3d36e3b56100d6a0ae087cb8adc16db5acab48bc69a` |

No D08C1/D08B1 species file, Little/USGS file, external range source, or real-Q1 output is an input to D09C.
