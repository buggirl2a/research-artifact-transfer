# PRECHECK RESOLUTION LOG

- Initial forced-gate result: `STOP_USGS_CSV_NETCDF_SEMANTIC_DIFFERENCE`.
- Diagnostic: all 690 species presence/absence arrays already matched exactly; the only failed row was the metadata identifier set, because the NetCDF projection variable used the long-name `Albers conical equal-area projection details` and that exact metadata label was absent from the non-species allow-list.
- Resolution: the observed projection metadata label was added to the fixed non-species metadata identifiers and the full semantic audit was rerun.
- Final gate: PASS; 690/690 species arrays, 27,984 grid records per species, zero PA mismatches. Row, column, and elevation matched exactly. Latitude/longitude differences remain the documented NetCDF precision update.
- Standards statement: no PASS/FAIL threshold, species rule, grain, domain, A/B split, lineage rule, or scientific object was changed.

This log records an implementation metadata-name correction, not post hoc adjustment of an experimental eligibility standard.

## Reproducibility-entry self-test

- The first standalone `prepare_inputs.py` self-test stopped because two manually transcribed USGS archive hash constants did not exactly match the authoritative manifest (`...c89340...` and `...b5fdcf...d22...` are the correct substrings).
- The main census was unaffected: `eligibility_census.py` reads the formal raw manifest and its `INPUT_AUDIT.csv` had already verified the actual archives exactly.
- The standalone preparation constants were corrected to the authoritative hashes and rerun; all three required archive members passed and were reused at exact uncompressed sizes.
- This was reproducibility-script QA only; no input file, inclusion rule, grain, split, threshold, or result was changed.
