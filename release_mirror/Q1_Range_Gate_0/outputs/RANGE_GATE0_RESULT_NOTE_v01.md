# Range Gate 0 result note v01

- Execution: **PASS**
- Frozen input universe: 312 accepted species with `confirmed_native_CONUS == TRUE` (expected 312).
- Scientific object: source-frozen, outcome-blind coarse routing of whole-range completeness using D08B1 v02 only.

## Frozen class counts

| Class | Species | Percent of 312 | Downstream route |
|---|---:|---:|---|
| FAIL_EXTRA_NA | 30 | 9.615385% | EXCLUDE_WHOLE_RANGE_CORE |
| BORDERLINE_SOUTH | 1 | 0.320513% | HOLD_TARGETED_EXTERNAL_RANGE_AUDIT |
| BORDERLINE_MEXICO | 94 | 30.128205% | HOLD_TARGETED_EXTERNAL_RANGE_AUDIT |
| RETAIN_USCA_AUDIT | 86 | 27.564103% | RETAIN_FOR_LITTLE_OR_USCA_TRUNCATION_AUDIT |
| PASS_COARSE | 101 | 32.371795% | COARSE_CORE_PASS |
| UNKNOWN | 0 | 0.000000% | HOLD_TARGETED_REVIEW_LATER |

## UNKNOWN reasons

- None.

## Interpretation boundary

No WCVP administrative-unit count was treated as area, range share, or truncation severity. No geometry was reconstructed. No Little layer content, external search, D08C2 data, FIA outcome, abundance, detection, eligibility, or real-Q1 result was used. Range Gate 0 does not select a final cohort; every final-cohort flag is zero.

STOP: return to scientific mainline for independent review.
