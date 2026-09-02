# Q1 D09C freeze v01

Date: 2026-09-02  
Scope: species-blind FIA reporting-state / P2PANEL fold / temporal balance / weight and variance calibration audit only.

## Frozen status

- Computational execution: **PASS**.
- Independent output audit: **PASS (25/25)**.
- Independent workbook audit: **PASS (11/11)**.
- Nationwide design feasibility from the frozen local FIADB snapshot: **FAIL**.
- T1: **FAIL** (46 PASS, 1 CONDITIONAL, 1 FAIL; failed State: CA; conditional State: WV).
- T2: **FAIL** (44 PASS, 1 CONDITIONAL, 3 FAIL; failed States: CA, OR, WA; conditional State: WV).
- Final temporal frame: **NOT SELECTED**.
- Final A/B partition: **NOT SELECTED**.
- Final estimator family: **NOT SELECTED**.

## Frozen factual diagnostics

- T1 has 47/48 required local 2022 reporting-State groups; California is absent.
- T2 has 45/48 required groups after the specifically authorized 2022 substitutions for Montana, New Mexico, and Utah; California, Oregon, and Washington remain absent.
- Texas component membership is closed through actual `POP_EVAL_GRP -> POP_EVAL_TYP -> POP_EVAL` relationships: T1 EVALID 482201 and T2 EVALID 482301, each with eight estimation units spanning eastern and western components. No EVALID membership was guessed.
- All 960 formal whole-P2PANEL 2-versus-3 candidates are present. Ninety-two State/frame top diagnostics are rankable; none is a frozen final partition.
- No multi-panel lineage exception was detected. No P2PANEL was split.
- Full-evaluation EXPNS was not reused as a final fold/panel weight. All 368 represented-block synthetic constant-response calibration identities pass.
- Missing-stratum representation remains explicit. No numerical precision threshold was introduced.

## Workbook treatment

The audit workbook contains all core State/frame, component, candidate, top-partition, lineage, calibration, input, SQL/table-access, and QC tables. The three largest canonical ledgers remain complete UTF-8 CSV files and are indexed in the workbook by exact row count, byte size, and SHA-256 to avoid an unusably large workbook:

- `D09C_PANEL_SUBPANEL_YEAR_LEDGER_v01.csv` — 65,233 data rows.
- `D09C_TI_FOLD_WEIGHT_AUDIT_v01.csv` — 9,472 data rows.
- `D09C_MA_FOLD_WEIGHT_AUDIT_v01.csv` — 23,680 data rows.

## Boundary confirmation

No species identity or outcome table was read. No D08C2, Range Gate 0, Little/USGS processing, external range search, final cohort selection, or real Q1 analysis was run.

Frozen downstream order remains: D09C -> scientific mainline audit -> Range Gate 0 -> corrected D08C2 -> targeted Little/external-range review -> final species cohort -> real Q1.

STOP after packaging and transfer validation.
