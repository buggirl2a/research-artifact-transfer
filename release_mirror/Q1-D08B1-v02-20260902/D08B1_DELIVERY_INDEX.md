# D08B1 delivery index v02

This index inventories every payload file present before the three self-referential package-control files are finalized. CSV `rows` exclude the header. `authoritative=YES` is restricted to the machine-readable v02 CSV outputs; the audit workbook and all provenance/QC artifacts are review aids.

Payload files indexed: **76**

| File | Purpose | Rows | Lines | Bytes | SHA-256 | Authoritative |
|---|---|---:|---:|---:|---|---|
| `code/build_taxon_range_audit_xlsx_v02.mjs` | reproducibility source code |  | 213 | 9823 | `499c43294b554c71480ae747132620a02ce0f1487a8c656e62d70c6ec5f5fa14` | NO |
| `code/build_taxon_range_d08b1_v02.py` | reproducibility source code |  | 1109 | 86536 | `fad43f2fe935738585f78d4078b59b992de61bcb10a5ad89f1ede097055d821d` | NO |
| `code/finalize_taxon_range_d08b1_v02.py` | reproducibility source code |  | 404 | 17472 | `36205c09445ff8715530391b800a222e9bc2ce2d2aa5a580b7ed3210327ca4d0` | NO |
| `code/verify_taxon_range_d08b1_v02.py` | reproducibility source code |  | 139 | 10011 | `ed56e8f592799b33e9f65e613d6e057c91257f1740e11ee4082951979ed903a1` | NO |
| `control/D08A_sha256_v02.txt` | upstream D08A hashes |  | 19 | 2056 | `6e34db428e84c7ab1de246fc4cbf0b2ff17d71af4c6a3f99a363c86388c8e98d` | NO |
| `control/D08A_SOURCE_FREEZE_v02.md` | upstream D08A source freeze |  | 51 | 2414 | `4afe035bf6667b204eec46ab19ae1dd7c1e952b5feebc4ea166c293c73c7557c` | NO |
| `control/D08B1_CORRECTION_LOG_v02.md` | incremental correction log |  | 44 | 3121 | `9a9792c35bade775eedc4b1038afd67197c1bd42932e25726341138b5150468e` | NO |
| `control/D08B1_INPUT_FREEZE_v02.md` | D08B1 authoritative input freeze |  | 43 | 3063 | `55d784f1470da78554d49bf3458175b446f43bdf05c18f4ac9f3f9943e873477` | NO |
| `control/D08B1_TAXONOMY_USGS_BRIDGE_CONTRACT_v02.md` | pre-run frozen contract and PASS/FAIL criteria |  | 80 | 7120 | `bd756e111dc2cfe2e983d5f2b421846c85213612b167a111d0d0ee3d14ae40c8` | NO |
| `control/TAXON_RANGE_FREEZE_v01.md` | prior v01 freeze declaration |  | 31 | 1699 | `9e3d5665091cc49e4a9fe679513258b109a934ce66ab82645abd148bbd752ca9` | NO |
| `control/TAXON_RANGE_FREEZE_v02.md` | v02 output freeze declaration |  | 34 | 1873 | `04f08ae046f490bc3b5dc8fe680d547bb5dea32a5eed4c59b17a73fb74eace9d` | NO |
| `inputs/frozen_atlas/D08A_USGS_Atlas_G_Table1_20260902.html` | frozen USGS Atlas G Table 1 source |  |  | 241941 | `fdca3c163d856aeea7b15ec5f80e18750701a880ee8f9f4c1bd5cc076f26292b` | NO |
| `inputs/frozen_eligibility/PACKAGE_MANIFEST_SHA256.csv` | frozen eligibility-stage USGS audit input | 69 |  | 9252 | `97a4bb5de5992aaa338accd540780be304f5376c4818ef529309697e2a8d5ee6` | NO |
| `inputs/frozen_eligibility/PACKAGE_VERIFICATION.json` | frozen eligibility-stage USGS audit input |  | 11 | 392 | `d3badb3ecf08bb73e730fef54713721493d7b649d8aa24ff6fcc81d2876b490d` | NO |
| `inputs/frozen_eligibility/USGS_RANGE_AUDIT.csv` | frozen eligibility-stage USGS audit input | 269 |  | 116675 | `bdc8a43411f648ab72c4d294f846d0688e436dcc035817cbc1de593e87c28312` | NO |
| `inputs/frozen_eligibility/ZIP_SHA256.txt` | frozen eligibility-stage USGS audit input |  | 1 | 111 | `b5f9c31dbd4db5105acea015c1ed4ef41b2fff19e56204b53951f7d0a8444285` | NO |
| `inputs/frozen_v01_package/DELIVERY_ARCHIVE_INDEX_v01.json` | frozen v01 reproducible delivery package or checksum |  | 20 | 762 | `01cf6700d1398e1b093a3e6309b9167ee4d160ce798964188e5c27070df5894d` | NO |
| `inputs/frozen_v01_package/Q1_D08B_MAINLINE_AUDIT_DELIVERY_v01.zip` | frozen v01 reproducible delivery package or checksum |  |  | 2748725 | `5ad4b94f5e3775db86c1b7d806dae3ec7888a13ad85af933b436e4eba2483c96` | NO |
| `inputs/frozen_v01_package/Q1_D08B_MAINLINE_AUDIT_DELIVERY_v01.zip.sha256` | frozen v01 reproducible delivery package or checksum |  |  | 106 | `3d6f3b96853dad1d96e10c65721d0f341d02c4cb49ca17354db7279bd5161597` | NO |
| `inputs/frozen_v01_required/Q1_GLOBAL_RANGE_FLAGS_v01.csv` | frozen v01 authoritative comparison input | 354 |  | 188035 | `9aa28e758d8b2aae28f594801d00d2b23ce704b37a59d790032e55068d1b04bb` | NO |
| `inputs/frozen_v01_required/Q1_TAXON_CODE_AGGREGATION_v01.csv` | frozen v01 authoritative comparison input | 354 |  | 63463 | `5ffb9e0880c82c97e7d7cf4ece04bec0c7523779f379b17304ad26ff9518f1e9` | NO |
| `inputs/frozen_v01_required/Q1_TAXON_RANGE_MASTER_v01.csv` | frozen v01 authoritative comparison input | 396 |  | 201452 | `7e373186d1c7f433c47856b2ae228b5b066ad2399b81a9cb3b4f372d57f47524` | NO |
| `inputs/frozen_v01_required/Q1_USGS_NAME_CLOSURE_v01.csv` | frozen v01 authoritative comparison input | 360 |  | 89188 | `28b7609d7a4eeb0ae89e79b91cf13d4ffe94c5b955f727bc9fe5f00b91a9188d` | NO |
| `inputs/frozen_v01_required/Q1_WCVP_NATIVE_DISTRIBUTION_LONG_v01.csv` | frozen v01 authoritative comparison input | 9429 |  | 1594669 | `461b09edea496467eecb779ddb7eea542f142e93011f32ec97bbf7769ce06bbe` | NO |
| `inputs/new_authority/correction_delivery_extracted/D08B_TAXONOMY_CORRECTION_EVIDENCE_v01.csv` | D08B1 mainline request/decision/correction authority input | 11 |  | 12097 | `ca71c7bb6cd4e647b06a82f604b6b472ecd54f0f01cac88f9d04a4fc9785b9fd` | NO |
| `inputs/new_authority/correction_delivery_extracted/D08B_TAXONOMY_CORRECTION_MANIFEST_v01.csv` | D08B1 mainline request/decision/correction authority input | 3 |  | 367 | `a1146332940274a6fec1fe83fcbec2241d466b1ec2a7d5bd5abce7f6d5c3e57d` | NO |
| `inputs/new_authority/correction_delivery_extracted/D08B_TAXONOMY_CORRECTION_NOTE_v01.md` | D08B1 mainline request/decision/correction authority input |  | 43 | 3075 | `2ff546dbd69039da55ea1fb5641a4e8a91dc8933c9d6c93c0a398580245c8aad` | NO |
| `inputs/new_authority/correction_delivery_extracted/D08B_TAXONOMY_CORRECTION_SHA256_v01.txt` | D08B1 mainline request/decision/correction authority input |  | 4 | 432 | `979b18f41e0fd861da13071939623f67ef5f3cc26ed45b3836f9fc4f1dcef1b1` | NO |
| `inputs/new_authority/correction_delivery_extracted/D08B_TAXONOMY_CORRECTION_SOURCE_LEDGER_v01.csv` | D08B1 mainline request/decision/correction authority input | 30 |  | 7791 | `88e0fbba9588eb8ca39f2b7d11907d7d903a338cc923a35c321de76ac53ee672` | NO |
| `inputs/new_authority/D08B_TAXONOMY_CORRECTION_DELIVERY_v01.zip` | D08B1 mainline request/decision/correction authority input |  |  | 8954 | `fecd1278e843d02ffe54921cb59454dcef2642ec299eb93fb25471d661280efc` | NO |
| `inputs/new_authority/Q1_D08B_TAXONOMY_CORRECTION_MAINLINE_DECISION_v01_20260902.md` | D08B1 mainline request/decision/correction authority input |  | 74 | 5316 | `d275946726f0111522a040992c210bf5511a5992a3e4737f6b10301b7a854564` | NO |
| `inputs/new_authority/Q1_WORK_REQUEST_D08B1_TAXONOMY_USGS_BRIDGE_CORRECTION_v01_20260902.md` | D08B1 mainline request/decision/correction authority input |  | 155 | 6671 | `dfc4016002e334524ed149647bd4d500a844d68b2eb638e3eb5b9a3ff8677f7a` | NO |
| `outputs/Q1_ANALYSIS_SPECIES_MASTER_v02.csv` | 361-species accepted analysis-species master | 361 |  | 89217 | `6f69874ab02723b3489aa4f3cbfb5aba188147400efdf170f27ad699d6368cb0` | YES |
| `outputs/Q1_DRC_PROTOCOL_v02.csv` | DRC retention and DBH-only sensitivity protocol | 361 |  | 68280 | `d49059c3131258aae09b240387cca6a0f53be3a057470338304c3de3b3b8b952` | YES |
| `outputs/Q1_FIA_CODE_TO_ANALYSIS_SPECIES_v02.csv` | 396-code original-name to accepted analysis-species bridge | 396 |  | 165626 | `d19db4f15c2f5f3f328d39bbc9ad17486a384de509253ff0c237ee25ab481cdd` | YES |
| `outputs/Q1_GLOBAL_RANGE_FLAGS_v02.csv` | species-level global-range flags | 361 |  | 191352 | `dc64778032ed9bd301bfc7c14818fc3ba71a3b2621bb4e8b33ec558ecdf3d16d` | YES |
| `outputs/Q1_HYBRID_NONCORE_AUDIT_v02.csv` | explicit hybrid/noncore code audit | 3 |  | 920 | `485129e7c9e43d7c516f1e62ada0ddbc1c1dde60d38305ab261697520621f95e` | YES |
| `outputs/Q1_HYBRID_NONCORE_DISTRIBUTION_AUDIT_v02.csv` | audit-only hybrid distribution evidence | 4 |  | 1433 | `1835554f971ed31c7080fc6c96808839b0a9c8a629b59989796f485344648f1d` | YES |
| `outputs/Q1_TAXON_RANGE_EVIDENCE_v02.csv` | row-level provenance and decision evidence | 142 |  | 39105 | `01160229bdfb64b5961deaadfb8b4e26ff8bd8eb80f091490f0149b69c582691` | YES |
| `outputs/Q1_TAXON_RANGE_MAINLINE_AUDIT_v02.xlsx` | formatted mainline audit workbook |  |  | 1253393 | `f7c40ce3918f6c9c774d667f796ca252afd7b3d1355387bffb432226be379c98` | NO |
| `outputs/Q1_TAXON_RANGE_MASTER_v02.csv` | 396-row FIA-code taxon–range master | 396 |  | 280753 | `e6ce453b91ff5b0813d65993129252b6a30adccd694ed34a760ecfe1b0d4c97c` | YES |
| `outputs/Q1_TAXON_RANGE_QC_v02.csv` | machine-readable build QC | 31 |  | 2656 | `ee26c8a5c0cd454e1747289ccffc76d5c6738e2f1e44a04c3bdeef0d7697a073` | YES |
| `outputs/Q1_TAXON_RANGE_UNRESOLVED_v02.csv` | ambiguous/unresolved decision queue | 74 |  | 16560 | `aaf4d79f78c745deb2e1c151d3710f147967e5b690b4329458af8f68300679f2` | YES |
| `outputs/Q1_TAXONOMY_CORRECTION_APPLIED_v02.csv` | 11-row incremental correction application ledger | 11 |  | 6354 | `4ff52036d36f149d09355006ca8bebb8999e66ed045535966fc65730d9f2cf3c` | YES |
| `outputs/Q1_USGS_CROSS_STAGE_CONFLICT_v02.csv` | cross-stage USGS conflict and disposition audit | 123 |  | 59602 | `d67a5af21db7d3db0cf635bc21e523c5745b22127cc0a8132dface82f478faaf` | YES |
| `outputs/Q1_USGS_LAYER_RECONSTRUCTION_REVIEW_v02.csv` | review-required USGS/Little reconstruction queue | 69 |  | 19631 | `32e3b77c318d60d266fef00952c73b11acf43e4c5cbedb72d3bd9f9bf7bae865` | YES |
| `outputs/Q1_USGS_NAME_CLOSURE_v02.csv` | USGS name/layer closure evidence | 366 |  | 140718 | `fc3f66493c9d0c09a8e90681e1a4922e42d2a3446a197adc84f398dccec1f36e` | YES |
| `outputs/Q1_WCVP_NATIVE_DISTRIBUTION_LONG_v02.csv` | 9,648-row WCVP Level-3 native/introduced evidence | 9648 |  | 1631728 | `559a2d6f7b0d67ad886468a2c0098e117c824f196f0a85d3bb7d99c466649017` | YES |
| `outputs/README.md` | output directory readme |  | 3 | 381 | `1de92eedcfa96fc01de0930b3905d9d7fd4edcac461118feebe09b1e6f15a8c5` | NO |
| `qc/D08B1_BUILD_SUMMARY_v02.json` | build counts and status |  | 37 | 984 | `0754f1c0741a3e1975a76dad8b33827a55051fdfaa81316d8a11914a33a8a2ef` | NO |
| `qc/D08B1_ENVIRONMENT_v02.json` | runtime environment record |  | 8 | 334 | `bc18b9e4c7dc9d35f39485eb60d430ea29af8bdb6ae6bd96b53023cf1e22a5f5` | NO |
| `qc/D08B1_IMPLEMENTATION_LOG_v02.md` | implementation log |  | 8 | 734 | `d08b622adfd47d40e67fe1d65a0c1f12b870a98fef0f91866a28ab5ae92b2be0` | NO |
| `qc/D08B1_INDEPENDENT_AUDIT_v02.json` | independent post-build audit |  | 184 | 3644 | `c14343b1a1e361185c444d2bfa10c4bf56fe882d2c8fc0ee98d08c6c7dbbd4c8` | NO |
| `qc/D08B1_INPUT_HASHES_v02.csv` | frozen-input hash ledger | 19 |  | 4408 | `bd4b6d640748f20edb623a01da9d999f005ac1ff7e59c4b91bcaf5eca20ba1d0` | NO |
| `qc/D08B1_PARAMETERS_v02.json` | frozen implementation parameters |  | 42 | 983 | `65a5f60b03770c84401a1b3c741c548df10b5d972e86a35f91b3f3cd66273db7` | NO |
| `qc/D08B1_WORKBOOK_FORMULA_ERROR_SCAN_v02.ndjson` | workbook formula-error scan |  | 1 | 60 | `acc0111e19cf44d2753fc9ecd164bf1b27fbd65597463a25cf48bd1c65e90146` | NO |
| `qc/D08B1_WORKBOOK_RENDER_INDEX_v02.json` | workbook render index |  | 86 | 3022 | `a976b7498f21e668096d49ea73b51588a08a251c753c5d66cfedaa6caa402c2f` | NO |
| `qc/D08B1_WORKBOOK_SUMMARY_INSPECT_v02.ndjson` | workbook summary inspection |  | 1 | 1686 | `9c4ff446017c74cdb591cfbd8f0a68a4baed75edbb7c02f8ad9dd20cdfe642c8` | NO |
| `qc/WORKBOOK_PREVIEWS_v02/.gitkeep` | rendered workbook visual-QA preview |  |  | 1 | `01ba4719c80b6fe911b091a7c05124b64eeece964e09c058ef8f9805daca546b` | NO |
| `qc/WORKBOOK_PREVIEWS_v02/Analysis_Species.png` | rendered workbook visual-QA preview |  |  | 255757 | `3f1f3634c1dcf4cb34196575db379284da0dcc064767ec3c736560680ce6c3d1` | NO |
| `qc/WORKBOOK_PREVIEWS_v02/Code_Map.png` | rendered workbook visual-QA preview |  |  | 260489 | `b34f4ff4925a382352b1baee8e629fe6a568e5fdf4e7395bb9c77dc0471958ff` | NO |
| `qc/WORKBOOK_PREVIEWS_v02/Corrections.png` | rendered workbook visual-QA preview |  |  | 166278 | `d3da2b4a8db639bcd182eab801fe45cee9c77c0b5dfbee52d41ae159ef25593e` | NO |
| `qc/WORKBOOK_PREVIEWS_v02/Cross_Stage.png` | rendered workbook visual-QA preview |  |  | 216383 | `27021a83865446ec3afef03c617a936ccf365f49bcbbc8d5be30a2ad68f72cb3` | NO |
| `qc/WORKBOOK_PREVIEWS_v02/DRC_Protocol.png` | rendered workbook visual-QA preview |  |  | 201656 | `ea9e0aa06a0c5e9260f1eb2cff3608a6c3869c88672effd90b5389f38f5ca267` | NO |
| `qc/WORKBOOK_PREVIEWS_v02/Evidence.png` | rendered workbook visual-QA preview |  |  | 551178 | `0a73f0a1797463548e523c03b0f76e8df691c4ddf14016278d3c92640b400024` | NO |
| `qc/WORKBOOK_PREVIEWS_v02/Global_Range.png` | rendered workbook visual-QA preview |  |  | 152440 | `ce82b460a891d17030ea696634d3d5e8c28f3e992d1b7ad8df6d7cab2122eae6` | NO |
| `qc/WORKBOOK_PREVIEWS_v02/Hybrid_Audit.png` | rendered workbook visual-QA preview |  |  | 43515 | `317f77d5f80dd087453476b5952acab134411c17bbe1520f4a5ee1b384735bb0` | NO |
| `qc/WORKBOOK_PREVIEWS_v02/Hybrid_Dist.png` | rendered workbook visual-QA preview |  |  | 45239 | `8731b4b868835dd063a99e81ae5cc159f24d5df33bb7ce96b2780c2c3aa51c4d` | NO |
| `qc/WORKBOOK_PREVIEWS_v02/QC.png` | rendered workbook visual-QA preview |  |  | 218432 | `f4965c19876c1049b8d6d88b3a65cb667892d3c459b845545e4011d033415a2c` | NO |
| `qc/WORKBOOK_PREVIEWS_v02/Summary.png` | rendered workbook visual-QA preview |  |  | 97316 | `be15f19b1ae4c651cb13e50d791d5be9884bc321c49526f2bfc45046ec7d69c5` | NO |
| `qc/WORKBOOK_PREVIEWS_v02/Taxon_Master.png` | rendered workbook visual-QA preview |  |  | 186459 | `8b4b1805a86516853fcec07182191e19134bcb75298d2529de557be5b0063c5e` | NO |
| `qc/WORKBOOK_PREVIEWS_v02/Unresolved.png` | rendered workbook visual-QA preview |  |  | 458912 | `cb2fa01bb67b100ed01da4536e5884356eb8baa0a2f6d6d9a03193e066ec86e8` | NO |
| `qc/WORKBOOK_PREVIEWS_v02/USGS_Closure.png` | rendered workbook visual-QA preview |  |  | 222710 | `e0d11ddee039601fcfa852a1ccbcc707d3c386fdc1718a51724cf35a0098617a` | NO |
| `qc/WORKBOOK_PREVIEWS_v02/USGS_Review.png` | rendered workbook visual-QA preview |  |  | 191381 | `b5c44accf3913e44791410a1f75a0ecf897d16e5cff1cccb52e25034d48b6312` | NO |
| `qc/WORKBOOK_PREVIEWS_v02/WCVP_Level3.png` | rendered workbook visual-QA preview |  |  | 184100 | `8a1a5f7160cdbd92b85ef3fd368420df1905a13aea9944e3decc8b6410e1f633` | NO |
| `README_PACKAGE.md` | reproduction and scope instructions |  | 18 | 1560 | `ce88d67c563c09be2fdb1c4b15491a4e05213ec83b4ed5e94fe5a47c607aa2f9` | NO |

## Package-control files

`D08B1_DELIVERY_INDEX.md` (this file), `MANIFEST.json`, and `SHA256SUMS.csv` are finalized after payload enumeration. Their final hashes are included in `SHA256SUMS.csv` wherever non-self-referential; `SHA256SUMS.csv` necessarily omits its own hash.
