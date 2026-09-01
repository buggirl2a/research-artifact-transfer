# Q1 D08B.1 input freeze v02

Date: 2026-09-02  
Status: PASS  
Scope: bounded additive taxonomy correction and USGS/Little name-layer bridge repair only.

## New authoritative inputs

All three user-supplied files were copied byte-for-byte to `03_doc/D08B1_TAXONOMY_CORRECTION_INPUTS_v02/` after complete reading.

| File | Bytes | SHA-256 |
|---|---:|---|
| `Q1_WORK_REQUEST_D08B1_TAXONOMY_USGS_BRIDGE_CORRECTION_v01_20260902.md` | 6671 | `dfc4016002e334524ed149647bd4d500a844d68b2eb638e3eb5b9a3ff8677f7a` |
| `Q1_D08B_TAXONOMY_CORRECTION_MAINLINE_DECISION_v01_20260902.md` | 5316 | `d275946726f0111522a040992c210bf5511a5992a3e4737f6b10301b7a854564` |
| `D08B_TAXONOMY_CORRECTION_DELIVERY_v01.zip` | 8954 | `fecd1278e843d02ffe54921cb59454dcef2642ec299eb93fb25471d661280efc` |

The correction ZIP contains exactly five members. Its internal three-row manifest and four-row SHA-256 sidecar were independently verified with zero mismatch. Extracted member hashes are:

| Member | Bytes | SHA-256 |
|---|---:|---|
| `D08B_TAXONOMY_CORRECTION_EVIDENCE_v01.csv` | 12097 | `ca71c7bb6cd4e647b06a82f604b6b472ecd54f0f01cac88f9d04a4fc9785b9fd` |
| `D08B_TAXONOMY_CORRECTION_SOURCE_LEDGER_v01.csv` | 7791 | `88e0fbba9588eb8ca39f2b7d11907d7d903a338cc923a35c321de76ac53ee672` |
| `D08B_TAXONOMY_CORRECTION_NOTE_v01.md` | 3075 | `2ff546dbd69039da55ea1fb5641a4e8a91dc8933c9d6c93c0a398580245c8aad` |
| `D08B_TAXONOMY_CORRECTION_MANIFEST_v01.csv` | 367 | `a1146332940274a6fec1fe83fcbec2241d466b1ec2a7d5bd5abce7f6d5c3e57d` |
| `D08B_TAXONOMY_CORRECTION_SHA256_v01.txt` | 432 | `979b18f41e0fd861da13071939623f67ef5f3cc26ed45b3836f9fc4f1dcef1b1` |

## Pre-existing frozen inputs

| Input | Bytes | SHA-256 | Role |
|---|---:|---|---|
| `10_archive/tax_v01_mainline_delivery/Q1_D08B_MAINLINE_AUDIT_DELIVERY_v01.zip` | 2748725 | `5ad4b94f5e3775db86c1b7d806dae3ec7888a13ad85af933b436e4eba2483c96` | Immutable D08B v01 baseline. |
| `02_raw/WCVP/wcvp.zip` | 88179649 | `d32ea2b3a85e489b14e83bcc9eae7274532e1d113753f7be290d4b2dfde573fa` | WCVP v16 names and Level-3 distributions; no new download. |
| `03_doc/USGS/D08A_USGS_Atlas_G_Table1_20260902.html` | 241941 | `fdca3c163d856aeea7b15ec5f80e18750701a880ee8f9f4c1bd5cc076f26292b` | Frozen official Little Atlas G Table 1 bridge. |
| `10_archive/elig_v02/Q1_ELIGIBILITY_CENSUS_v0_2_REPRODUCIBLE.zip` | 2738865 | `c291b224018422ee732d8b71fbbacdb69aff88a7dd1ccffaec82c88d1590f5ba` | Frozen outcome-blind eligibility package. |
| `05_qc/elig_v02/USGS_RANGE_AUDIT.csv` | 116675 | `bdc8a43411f648ab72c4d294f846d0688e436dcc035817cbc1de593e87c28312` | Cross-stage diagnostic evidence; hash matches the frozen eligibility package manifest. |

## Fixed execution contract

`00_control/D08B1_TAXONOMY_USGS_BRIDGE_CONTRACT_v02.md` was frozen before the correction build. Its predeclared PASS/FAIL criteria cannot be relaxed after inspecting results.

## Prohibited scope

No D08C, FIA TREE merge, Little layer union/selection/reconstruction, new external range-map search, final cohort/grain selection, or real-Q1 outcome analysis is authorized.
