# Range Gate 0 scientific-output freeze v01

Date: 2026-09-03

## Frozen execution state

- Execution: PASS.
- Frozen D08B1 v02 accepted-species master: 361 rows.
- Frozen input universe: 312 rows with `confirmed_native_CONUS == TRUE`.
- Class counts: `FAIL_EXTRA_NA=30`, `BORDERLINE_SOUTH=1`, `BORDERLINE_MEXICO=94`, `RETAIN_USCA_AUDIT=86`, `PASS_COARSE=101`, `UNKNOWN=0`.
- Build QC: 22/22 PASS.
- Independent output-only audit: 25/25 PASS.
- Workbook validation: 10/10 PASS.
- Final cohort selections: 0.

## Authoritative scientific outputs

| File | Bytes | SHA-256 |
|---|---:|---|
| `Q1_RANGE_GATE0_SPECIES_CLASSIFICATION_v01.csv` | 397437 | `243978406cb913c13898b333671000c30592079d076ef8b995822a1684f8a8cd` |
| `Q1_RANGE_GATE0_SUMMARY_v01.csv` | 395 | `c44eddbcd6fe0c884856786d1fa4ab036f6c1f01956177697bda5eb83d741c05` |
| `Q1_RANGE_GATE0_DECISION_QUEUE_v01.csv` | 225894 | `f9c066bbf25de8dca122d90446aab579f22052ab9c0de4412be616c8567016c1` |
| `Q1_RANGE_GATE0_FAIL_EXTRA_NA_v01.csv` | 77161 | `328ceb72d649e0788f2c019c5f6884ef0f318e1ba5059d8bf5de6cfadbd8eef5` |
| `RANGE_GATE0_RESULT_NOTE_v01.md` | 1255 | `ef49b993bf8ac2579e8ab1b3d555a4c3486fdd9147c2df423b4bdf2bc4ed8f7e` |
| `Q1_RANGE_GATE0_MAINLINE_AUDIT_v01.xlsx` | 111062 | `d0dd7e34e9b4bfffb412fa99e643fa0a12cd33d9061b8a75c7607665c733144e` |

No class, reason, route, threshold, or output row may be changed after this freeze without a new mainline-authorized version. Packaging and the later Research Artifact Relay manifest are transport operations only and may not mutate or trigger recomputation of these files.

## Scope boundary retained

No administrative-unit count was interpreted as area/share/severity; no geometry, Little decision, external range search, D08C2, FIA outcome/eligibility, abundance/detection, final cohort selection, or real Q1 was performed.
