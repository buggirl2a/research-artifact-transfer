# D08B1 corrected taxon–USGS bridge reproducible package v02

This is the frozen incremental correction delivery requested by the Q1 scientific mainline. It does **not** run D08C, merge FIA TREE records, merge Little layers, search for new extra-CONUS range data, select final Q1 species, or estimate any Q1 outcome.

## Authoritative outputs

The UTF-8 CSV files in `outputs/` are the authoritative v02 machine-readable products. The XLSX file is an audit view of the same products and is not independently authoritative. `D08B1_DELIVERY_INDEX.md`, `MANIFEST.json`, and `SHA256SUMS.csv` provide file-level provenance and integrity checks.

## Reproduction

1. Use Python 3 and Node.js with the bundled `artifact-tool` runtime recorded in `qc/D08B1_ENVIRONMENT_v02.json`.
2. Place the frozen external WCVP v16 archive at `C:/range_paper/02_raw/WCVP/wcvp.zip`; its required SHA-256 is recorded in `qc/D08B1_INPUT_HASHES_v02.csv` and `control/D08B1_INPUT_FREEZE_v02.md`.
3. Run `code/build_taxon_range_d08b1_v02.py` to regenerate CSV outputs from the frozen inputs.
4. Run `code/verify_taxon_range_d08b1_v02.py` for the independent audit.
5. Run `code/build_taxon_range_audit_xlsx_v02.mjs` to rebuild the audit workbook.
6. Compare every regenerated file to `SHA256SUMS.csv`.

The 88 MB WCVP archive is intentionally referenced by immutable SHA-256 rather than duplicated in this transfer package. All incremental mainline authorities, the frozen v01 comparison inputs, frozen Atlas source, and the eligibility USGS audit used by this correction are included.
