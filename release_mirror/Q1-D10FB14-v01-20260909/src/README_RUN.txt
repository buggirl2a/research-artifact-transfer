Q1 D10F-B14 v01 deterministic builder

Run with the pinned Python 3.12 / SQLite 3.49.1 interpreter:
  RUN.cmd preflight
  RUN.cmd run
  RUN.cmd finalize --category <allowed category>
  RUN.cmd package

The run command refuses a nonempty output directory. Calibration is sealed before
the accepted actual24 outcome ledger is opened. package writes a deterministic ZIP
and enforces upload_target=mirror for every transfer row. It does not archive.
