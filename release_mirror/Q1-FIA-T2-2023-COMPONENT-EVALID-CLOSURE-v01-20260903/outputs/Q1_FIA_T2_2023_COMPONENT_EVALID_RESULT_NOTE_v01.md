# Q1 FIA T2 2023 component-EVALID and design-membership closure v01

Generated: 2026-09-03T18:49:35.2346139+08:00
Frozen raw root: `C:\range_paper\02_raw\fia_t2_2023_raw_design_v01`

This note reports deterministic raw-key membership and structural design-table existence only. It is not a D09C PASS and makes no A/B, P2PANEL, TI/MA, estimator, WV, species, abundance, detection, or Q1 decision.

## CA2023

- EVAL_GRP: `62023`
- group CN: `1957507988290487`
- component EVALID: `62300;62301;62303;62307`
- evaluation type(s): `EXPALL;EXPCHNG;EXPCURR;EXPDWM;EXPGROW;EXPMORT;EXPREMV;EXPVOL`
- membership integrity: `PASS_RAW_KEY_CHAIN`
- design membership: `INCOMPLETE_OR_KEY_ISSUE`
- final status: `COMPONENT_EVALID_CLOSED_DESIGN_MEMBERSHIP_INCOMPLETE`
- caveat: Structural existence/key-integrity result only; this is not a D09C PASS and makes no estimator/design selection.

## OR2023

- EVAL_GRP: `412023`
- group CN: `1956358791290487`
- component EVALID: `412300;412301;412303;412307`
- evaluation type(s): `EXPALL;EXPCHNG;EXPCURR;EXPDWM;EXPGROW;EXPMORT;EXPREMV;EXPVOL`
- membership integrity: `PASS_RAW_KEY_CHAIN`
- design membership: `INCOMPLETE_OR_KEY_ISSUE`
- final status: `COMPONENT_EVALID_CLOSED_DESIGN_MEMBERSHIP_INCOMPLETE`
- caveat: Structural existence/key-integrity result only; this is not a D09C PASS and makes no estimator/design selection.

## WA2023

- EVAL_GRP: `532023`
- group CN: `1956294126290487`
- component EVALID: `532300;532301;532303;532307`
- evaluation type(s): `EXPALL;EXPCHNG;EXPCURR;EXPDWM;EXPGROW;EXPMORT;EXPREMV;EXPVOL`
- membership integrity: `PASS_RAW_KEY_CHAIN`
- design membership: `INCOMPLETE_OR_KEY_ISSUE`
- final status: `COMPONENT_EVALID_CLOSED_DESIGN_MEMBERSHIP_INCOMPLETE`
- caveat: Structural existence/key-integrity result only; this is not a D09C PASS and makes no estimator/design selection.

## Frozen key path

`POP_EVAL_GRP.EVAL_GRP -> POP_EVAL_GRP.CN -> POP_EVAL_TYP.EVAL_GRP_CN -> POP_EVAL_TYP.EVAL_CN -> POP_EVAL.CN -> POP_EVAL.EVALID`

Design crosschecks use direct EVALID only where the raw table actually contains EVALID. PLOT is linked by `POP_PLOT_STRATUM_ASSGN.PLT_CN -> PLOT.CN`; SURVEY is linked from those matched PLOT rows by `STATECD + INVYR`.
