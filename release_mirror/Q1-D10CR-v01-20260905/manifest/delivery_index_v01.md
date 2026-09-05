# D10C resume delivery index v01

Terminal status: `ABUNDANCE_CALIBRATION_COMPLETE_READY_FOR_MAINLINE_FREEZE`.

This index describes the pre-checksum package contents. Final member identities are authoritative in `sha256sums_v01.csv`.

| Member | Role | Purpose | Rows/lines | Bytes | SHA-256 |
|---|---|---|---:|---:|---|
| `README.md` | other | Other | 9 | 798 | `b421a338b7a8ae5e808b8354f9ac4eacaa7dcb684f8bf4fc366dfd43d31f287e` |
| `control/contract_v01.md` | frozen_contract | Frozen pre-run experiment contract | 70 | 4807 | `4c2bdc611572e8962f4d2552cdc3f8664cb9a6e796e8d71251d2dd17e7787630` |
| `control/original_contract.md` | other | Other | 40 | 3170 | `f5e8a9fc5ca5fff6d4c23c52181efed82fb95542265b14234eaf3a1a2dced576` |
| `control/resume_request.txt` | other | Other | 536 | 12802 | `f34a45a597cc8bb0780812f69685d491f40205854508d13a09e70191533f057e` |
| `fig/checks_v01.png` | qc | Qc |  | 60250 | `3986063f75466c6c9b5b03ef56a704c4b7cf1ebbc4e0578f61fc061b9b785e5a` |
| `fig/downstream_v01.png` | figure | Figure |  | 84126 | `7c952d0042199e52eefdcfd202a8965f5dc2fa1aa2fb7cc7522ec29d7db2b2ca` |
| `fig/leakage_v01.png` | figure | Figure |  | 54868 | `812add0be40b1a5645b3e6e29c85cb3fa19f560fad9ad464cafa3f94e23562a5` |
| `fig/recovery_v01.png` | figure | Figure |  | 34586 | `0bcde36eae250d47970c3199457f3913888e220e2557cba2061b3c9ab9292be0` |
| `fig/summary_post_v01.png` | figure | Figure |  | 101217 | `2c1d20c8edb1174e973afbe29b399f834eebed809c8e51a52d1cac60aa71e63d` |
| `fig/summary_v01.png` | figure | Figure |  | 101071 | `00b19500b01b75f596c980c6c96b181e6746abafebbfd6ad104aa137d92713f5` |
| `manifest/registry_delta_v01.csv` | manifest | Proposed mainline registry delta | 1 | 717 | `e549c198e162fd18f07a2e9b129b4993911518150e4e0c60998c69d5a08ceb81` |
| `out/a0_v01.csv` | audit_csv | A0 latent-truth abundance layer | 17524 | 1516093 | `c7e8721c64b3bc49ee469929561f4b10e5ba95e42c19fad0142a50923b749732` |
| `out/a1_v01.csv` | audit_csv | Exact broken D10A raw-count reference | 35048 | 3673734 | `98bd38b56c2b846c5aee8833e3dbb8e9e88e2f29c00018cb24defd01a38b6f99` |
| `out/a2_impl_v01.csv` | audit_csv | Audit Csv | 8 | 798 | `a82c3b62308394d412abf83c19a3a4b4f36f2efc61e4407edf8ac27a9efc9a7b` |
| `out/a2_v01.csv.gz` | audit_csv | Frozen D10C-A design-estimator cell masses | 35048 | 1668960 | `fdfc8fac2b45a0fdc96e74dff8de6cea575dd764bf245b7e7041e04eeca56c18` |
| `out/audit_v01.xlsx` | workbook | Human-readable audit workbook |  | 15536 | `7213a86a7a50651c9e6dafbec9b3af3326622d142678291846dfb620cc4e1375` |
| `out/audit_v01.xlsx.inspect.ndjson` | other | Other | 623 | 379502 | `1950f14b0402e8810f672cdc0d0376f3908052a3330f663cc954209beb2dbb42` |
| `out/authority_v01.md` | other | Other | 5 | 808 | `b68d053526b7e36d2dc2edb2d49912be879bd9dc19aaff8a9e1abc48614d73b2` |
| `out/cell_bins_v01.csv` | audit_csv | Audit Csv | 40 | 5344 | `9491288111dcc6afa72e3f70e09443e5d4e7b3b8ec20f8f2beebfda27a39465a` |
| `out/cell_recovery_v01.csv.gz` | audit_csv | Full cell-level A1/A2 recovery audit | 70096 | 6327541 | `43a642dde66ad5a3edda95c0df163851cd684013b9e1d684227c22901c06ebca` |
| `out/common_compare_v01.csv` | audit_csv | D10B L0/L1 versus D10C A2 common comparison | 18 | 2963 | `833b71bd8af3b74b8d7d6349738fea3c3944157392cb0a795e911788e1663d87` |
| `out/downstream_v01.csv` | audit_csv | Oracle-support downstream comparison | 180 | 50990 | `a1f2fdf1bae6f19955bfacf6586c3307ebc8e90043b7b5be05e080d9fba504f8` |
| `out/layer_ledger_v01.csv` | audit_csv | Audit Csv | 3 | 473 | `d1424c51fd6dd11f2ab70987c7b680b7eb149c757284aadcdd68a0350e7c706f` |
| `out/leakage_v01.csv.gz` | audit_csv | Sampling-intensity leakage diagnostics | 19504 | 441071 | `0a67ab842146ce029a580c53bdef8e99b1eef3d1dc223badd4dbbd700cbd1bae` |
| `out/map_recovery_v01.csv` | audit_csv | Normalized-map recovery table | 576 | 148016 | `6ec0de51bf14882e96b81ec56ea222cc6751625fa23884058b2490b87aea5d37` |
| `out/orientation_v01.csv` | audit_csv | AB versus BA consistency audit | 25 | 3847 | `a942f8f32dd4d1d6d83fe28e6855258dda8c165588a13482362ded68a9483730` |
| `out/plot_obs_v01.csv.gz` | audit_csv | Sparse nonzero synthetic FIA-style plot observations | 189932 | 7936112 | `60c652c5bcaaabf80f1c5c3fb8f76051ddfcc6c9a940250e3bd873186bcd5b27` |
| `out/recovery_metrics_v01.csv` | audit_csv | Species-level recovery metrics | 576 | 215014 | `0d6727d0e87d43508c45a2a07e2902b7f4857e745ca5893672a4e9b075fbcdc7` |
| `out/recovery_summary_v01.csv` | audit_csv | Audit Csv | 8 | 1034 | `f35b631819d0688536fc9d47137ebb90f24b4635610f169b2f921d2537a0e309` |
| `out/result_note_v01.md` | result_note | Mainline result note answering Q1-Q8 | 37 | 2659 | `bc7592ac7c747ad9b2b3f85206b9a962568f67503bab1352fb75aa0ef5dd2f26` |
| `out/separation_v01.csv` | audit_csv | STRONG versus PAIRED_NULL results | 90 | 42283 | `72ac6a8cb8a22a5b9df5d5083993ab7e38dadbcc353b41f5d77ec1d2b4ef6e91` |
| `out/truth_v01.csv` | audit_csv | Frozen latent abundance truth A0 basis | 17524 | 1463515 | `4f07d12f86fd9d115b24b60df469ff8def761fd0dea38919eb16e4a99beff53f` |
| `qc/audit_errors_v01.ndjson` | qc | Qc | 1 | 60 | `acc0111e19cf44d2753fc9ecd164bf1b27fbd65597463a25cf48bd1c65e90146` |
| `qc/audit_inspect_v01.ndjson` | qc | Qc | 13 | 9920 | `4c446bb8269420b1dc223e77d8ea88846b75231ac461e0fab230c6d19e7e425d` |
| `qc/audit_render_v01.json` | qc | Qc | 30 | 727 | `f93d4553ecf8c474bef5bacae910e944852323e9f4a29b0402d66f266a8c412f` |
| `qc/build_summary_v01.json` | qc | Qc | 25 | 819 | `da2f2f9ebf16ec05b820f53b45c69981d8839986d71a5e34b8c4d5aa791203e4` |
| `qc/checks_v01.csv` | qc | Qc | 12 | 870 | `34831aa0a0681f6c05c5eaf588bbcdd613dac9a05a2588b1d688d075f12497f3` |
| `qc/environment_v01.json` | qc | Qc | 8 | 318 | `1fbae868496fd9790927c3df5875691aba69a18a81162bdd488e9988446d7646` |
| `qc/input_id_v01.csv` | qc | Frozen input identity audit | 7 | 2011 | `2d14411c0c08807547336dae79c80a1fb6a290901afa06714627d92ef12a5cdd` |
| `qc/validation_v01.json` | qc | Deterministic independent validation report | 282 | 7102 | `a843222f8d779dabf16aa38437f1b2d82fb0aa46920bf2b3bb9544ecb7a70c9b` |
| `qc/world_id_v01.csv` | qc | Qc | 144 | 72932 | `c48406f6158543f68463f3e97b6ba4088009861f57cd24cfb1a07b35dfaabfd8` |
| `qc/xlsx_validation_v01.json` | qc | Qc | 12 | 13771 | `23718fd4cea3eacaea603676fd52e4622b03a2dc5e78d498ec0a47b9f2df098a` |
| `src/audit.mjs` | source | Source | 225 | 12484 | `d2189ad5ec694ebae8138cf4caa764c4eccf45a60004ad42e488bf8c50413013` |
| `src/build.py` | source | Source | 763 | 49834 | `8b9f87c39167ea41b7497ca6381ff0e3afb6e7517ab9d6ca713b5fdefb316a11` |
| `src/finalize.py` | source | Source | 296 | 14582 | `7b5c2083b07bda14b3b0407c93acee71fc7d2ca9c1ba83594df5415b82319deb` |
| `src/run_all.ps1` | source | Source | 21 | 741 | `6d3eb6070af6a4a25224222190131bb76ea282d80da0a9c89f092eb0306dc748` |
| `src/verify.py` | source | Source | 265 | 12974 | `c2eca3247f7129f282216355a425647f4923fe880be6a8b0a4478055260ee7b6` |
| `src/verify_xlsx.mjs` | source | Source | 45 | 2265 | `acfaed9dc3e1f8776f97d7be7abc183332661629612236b09967d14df36a2509` |

No scientific PASS/HOLD/FAIL is assigned by this package.
