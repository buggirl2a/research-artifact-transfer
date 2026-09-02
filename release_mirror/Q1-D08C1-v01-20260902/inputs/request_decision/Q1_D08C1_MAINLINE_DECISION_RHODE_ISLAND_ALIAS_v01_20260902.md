# Q1 D08C1 Mainline Decision — Rhode Island / WCVP RHO Alias v01

Date: 2026-09-02
Status: AUTHORIZED — RESUME D08C1

## Trigger

D08C1 preflight stopped because FIA `SURVEY.STATENM = Rhode Island` (STATECD 44, RI) does not exactly equal frozen WCVP Level-3 `area = Rhode I.` (`area_code_l3 = RHO`). The mismatch affects 130 frozen primary measurements (A=67, B=63), so it cannot be ignored.

## Frozen mainline decision

Authorize exactly one explicit geographic-name alias:

- FIA `STATECD = 44`
- FIA state abbreviation `RI`
- FIA state name `Rhode Island`
- maps to WCVP Level-3 `area_code_l3 = RHO`
- with WCVP area name exactly `Rhode I.`

This is an explicit one-to-one authority mapping, not fuzzy matching and not a general abbreviation rule.

## Scientific semantics

The alias resolves geographic identity only. It does **not** itself classify any FIA record as native, introduced, extinct, doubtful, or unknown.

For each analysis species, after the alias is applied:

1. If frozen WCVP v16 contains an `RHO` Level-3 row, use that row's frozen `introduced`, `extinct`, and `location_doubtful` fields under the existing D08C1 rules.
2. If no applicable `RHO` row exists for that species, retain the existing D08C1 missing/unknown evidence treatment. Do not infer state status from neighboring states, range geometry, FIA occurrence, or common knowledge.
3. The 130 RI primary measurements remain eligible for classification under the same rules as all other CONUS states; they are not automatically retained as native and not automatically excluded.

## Guardrails

- No other FIA↔WCVP state-name alias is authorized by this decision.
- No fuzzy, edit-distance, substring, abbreviation-expansion, or manual best-guess rule is authorized.
- If any further non-exact state/area correspondence is encountered, STOP and return to scientific mainline.
- Do not alter D08B1 v02 taxonomy, WCVP source rows, A/B split, grain, thresholds, Little/USGS status, or any real-Q1 quantity.

## Authorization

D08C1 may resume from preflight using this additive rule. No prior D08C1 scientific census result exists, so no result-dependent decision has been made.

STOP only if another contract-defined preflight condition is triggered.
