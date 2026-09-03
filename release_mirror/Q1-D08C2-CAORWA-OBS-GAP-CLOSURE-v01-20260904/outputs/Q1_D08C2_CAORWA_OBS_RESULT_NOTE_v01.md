# Q1 corrected D08C2 — CA/OR/WA observational-data gap closure v01

TASK_ID: D08C2_CAORWA_OBSERVATIONAL_GAP_CLOSURE_v01

Final status: **GAP_CLOSED_READY_FOR_MAINLINE_D08C2_CONTRACT_FREEZE**

## Scope
Only the nine authorized official FIA DataMart state-table ZIPs were acquired/frozen: CA/OR/WA × TREE/COND/SUBPLOT. Previously frozen PLOT/design authority was read-only and SHA-verified. No PLOT was re-downloaded; no national SQLite or other source was accessed by the script.

## Frozen F0 components
- CA = 62301
- OR = 412301
- WA = 532301

## State linkage summary
- CA F0 EVALID 62301: observational TREE/COND/SUBPLOT structural linkage = PASS.
- OR F0 EVALID 412301: observational TREE/COND/SUBPLOT structural linkage = PASS.
- WA F0 EVALID 532301: observational TREE/COND/SUBPLOT structural linkage = PASS.

## Interpretation boundary
This closure is species-blind. TREE values used only PLT_CN/STATECD/INVYR for mechanical linkage and temporal coverage; SPCD was checked only as a column name. No species identity values, eligibility, survivor counts, abundance/support, occupancy/detection, grid construction, or corrected D08C2 analysis were produced.

Absence of a TREE row for an individual F0 PLOT is not treated as linkage failure because a plot may legitimately have no TREE record; the check requires positive legal linkage at table/state level and 2023 temporal coverage.

## Authorities
- Preflight: Q1-D08C2-PREFLIGHT-OBS-AUTHORITY-v01-20260904 @ 0cfbc033e9fc49fdba4d8823df113b7862e172ea
- CA/OR/WA raw-design freeze: Q1-FIA-T2-2023-RAW-DESIGN-FREEZE-v01-20260903 @ 4bdec2bfc27a0b2de9a64abfc491e6dfea9f07eb
- Accepted F0 / D09C final: Q1_D09C_T2_FINAL_CORRECTION_v02 @ 0ec3fce71258e38958ecbb7534f3635e2eb05a63; reproducible ZIP SHA-256 07cb461121c71ef46990fea3e0cf9d8f139fd873234b9f57910ff10c7c33752f

## STOP
No corrected D08C2 was run. Mainline must freeze the next contract before any species-level or Q1 computation.
