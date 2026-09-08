Q1 D10F-B14 v01_1 targeted observed-state mixture correction.

Commands:
  RUN.cmd run
  RUN.cmd finalize --category <allowed recommendation>
  RUN.cmd package

The run reuses the accepted B14 pseudo-event Parquet and never rewrites the parent.
Calibration is sealed before actual24 species outcomes are parsed. Packaging enforces
upload_target=mirror and does not archive.
