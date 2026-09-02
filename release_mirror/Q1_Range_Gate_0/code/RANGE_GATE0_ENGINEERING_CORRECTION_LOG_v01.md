# Range Gate 0 engineering correction log v01

- Frozen scientific contract and PASS/FAIL criteria: unchanged.
- Initial implementation-only issue: D08B1 global summary flags are encoded as `TRUE`/`FALSE`, while the frozen long evidence table encodes its Boolean fields as `1`/`0`.
- Observed symptom: long-table native rows were not recognized, creating artificial summary/long contradictions.
- Correction: the long-table Boolean parser now recognizes its frozen integer encoding; no geography rule, category condition, precedence, route, threshold, or scientific object changed.
- Disposition: the erroneous temporary build was removed before producing deliverable outputs and is not a scientific result.
