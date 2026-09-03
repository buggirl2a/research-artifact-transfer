# Q1 D09C T2 final design correction result note v02

Date: 2026-09-03  
Nationwide status: **PASS_READY_FOR_MAINLINE_FINAL_D09C_AUDIT**

## Correction facts

- Repair-class selection is now applied before balance: final selected classes R0=47, R1=0, R2=1, R3=0.
- CA/OR/WA are selected strictly from R0. Candidate changed relative to v01 for: CA;OR;WA.
- Mechanical R2 trigger census: WV only. No other State entered sparse-EU fallback.
- WV same semantic-class partner candidates were resolved before A/B construction. Selected partner: Estimation Unit 4; resolution: UNIQUE_MINIMUM_PUBLIC_PLOT_CENTROID_DISTANCE.
- The WV merged domain preserves 100% population area and is shared identically by A and B before all ten candidates are enumerated.
- Fold-specific TI closes in 48/48 States; full-evaluation EXPNS is not reused. MA remains sensitivity-only (COMPLETE=16, PARTIAL=32, UNAVAILABLE=0).
- All four OR 412301 assignment/PLOT mismatches remain retained and nonblocking; only final fold labels were updated where necessary.

V02 does not constitute mainline scientific acceptance. No TREE, species outcome, abundance, detection, occupancy, D08C2, range, R1/R2, World 0, or real-Q1 analysis was read or run.

STOP after D09C correction.
