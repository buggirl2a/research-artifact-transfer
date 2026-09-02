# D09C result note v01

Date: 2026-09-02  
Execution status: **PASS**  
Design-frame feasibility from the frozen local FIADB snapshot: **FAIL**

## Outcome

D09C completed as a species-blind FIA sampling-design audit. No species identity or outcome table was read. No final A/B partition, estimator family, temporal frame, threshold, or cohort was selected.

- T1 (uniform 2022) status: **FAIL**; PASS=46, CONDITIONAL=1, FAIL=1; failed States: CA.
- T2 (latest at/immediately before 2023) status: **FAIL**; PASS=44, CONDITIONAL=1, FAIL=3; failed States: CA;OR;WA.
- The local frozen FIADB metadata contain 2022 reporting groups for 47/48 CONUS States (California missing) and 2023 groups for 42/48 (California, Montana, New Mexico, Oregon, Utah, and Washington missing). T2's authorized 2022 substitutions close Montana, New Mexico, and Utah, but California, Oregon, and Washington remain missing under T2.
- Texas membership is closed from actual `POP_EVAL_GRP -> POP_EVAL_TYP -> POP_EVAL`: T1 uses EVALID 482201 and T2 uses EVALID 482301. Each contains eight estimation units spanning the eastern and western State components; no EVALID was guessed.
- All 960 formal 2-vs-3 whole-panel candidate rows were emitted, including explicit non-auditable placeholders for missing frames. 92 State/frame top diagnostic rows were rankable; none is a final partition.
- Full-evaluation EXPNS was never reused as a final fold weight. TI and equal-weight MA audit weights were reconstructed from parent stratum area and fold/panel-specific sample counts. Synthetic constant-response identities passed for every represented block; missing stratum representation remains explicit.

The design result is FAIL at the nationwide-frame level because neither frozen T1 nor frozen T2 closes all 48 States from this local database snapshot. This is a factual closure result, not permission to substitute older groups or acquire new data.

## Boundary

No D08C2, Range Gate 0, Little/USGS processing, external distribution search, species selection, abundance surface, R1/R2, World 0, paired-null, prediction, significance, or real Q1 was run.

STOP and return to scientific mainline.
