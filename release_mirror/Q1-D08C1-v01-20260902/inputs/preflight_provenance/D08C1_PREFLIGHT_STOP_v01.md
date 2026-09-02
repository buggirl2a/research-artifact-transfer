# D08C1 preflight STOP report v01

Date: 2026-09-02

Status: **STOP — MAINLINE DECISION REQUIRED**

## Trigger

`Q1_WORK_REQUEST_D08C1_FIA_ACCEPTED_SPECIES_ELIGIBILITY_v01_20260902.md` requires exact full state-name correspondence between FIA and frozen WCVP Level-3 evidence and explicitly requires STOP rather than guessing when that crosswalk cannot be made deterministically.

The frozen inputs contain the following non-exact pair inside the primary CONUS domain:

| Source | State code | State abbreviation | State/area name |
|---|---:|---|---|
| FIA `SURVEY.STATENM` | 44 | RI | `Rhode Island` |
| WCVP Level-3 `area` | RHO | — | `Rhode I.` |

These strings are not an exact full-name match. WCVP v02 contains 85 Level-3 rows with `area_code_l3=RHO` and `area=Rhode I.`. The frozen eligibility-v0.2 audit contains 130 primary RI measurements (67 A; 63 B), so the mismatch affects records that may enter the requested census and cannot be ignored as an empty-state edge case.

## Mainline decision required

The bounded computational branch needs an explicit frozen rule deciding whether:

1. `FIA: Rhode Island` may map to `WCVP RHO: Rhode I.` as an authorized alias; or
2. exact string equality remains mandatory, in which case RI records must be classified under a mainline-specified category.

No alias rule, exclusion rule, or native/introduced classification was inferred.

## Work not performed

- No accepted-species eligibility census was run.
- No Little/USGS status or layer was used.
- No FIA–Little layer merge was performed.
- No external distribution search was performed.
- No grain or threshold was selected.
- No real Q1 quantity, geometry–abundance result, significance test, or outcome-based filter was computed.

## Preflight facts verified before STOP

- D08B1 v02 code map: 396 rows and 396 unique FIA codes.
- D08B1 v02 analysis-species master: 361 rows.
- D08B1 v02 global-range flags: 361 rows.
- D08B1 v02 WCVP Level-3 evidence: 9,648 rows.
- D08B1 v02 DRC protocol: 361 rows.
- Extracted frozen FIADB database is readable; `TREE` has a unique record identifier field `CN` and 26,412,261 rows.

This report is a pre-computation protocol stop, not an engineering or scientific PASS/FAIL result for D08C1.
