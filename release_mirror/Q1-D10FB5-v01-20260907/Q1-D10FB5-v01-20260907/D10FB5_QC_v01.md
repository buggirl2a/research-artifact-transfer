# D10FB5 QC v01

Deterministic checks validate identities, algebra, execution boundaries, and covariance arithmetic. Synthetic bias/variance/coverage values are evidence, not QC gates.

| Check | Status | Observed | Expected | Notes |
|---|---|---:|---:|---|
| Q01 | PASS | 22 | 22 | All required outer packages, internal manifests, commits, and selected members passed. |
| Q02 | PASS | 24 | 24 | Exact B3 singleton cases carried forward. |
| Q03 | PASS | 24 | 24 | No unauthorized singleton assignment was created. |
| Q04 | PASS | 24 | 24 | Singleton point coefficients unchanged by no-op. |
| Q05 | PASS | 13 | 13 | Exact WV plot coefficient rows. |
| Q06 | PASS | 13 | 13 | Combined-population representation matches current pooled operator. |
| Q07 | PASS | 23014.8+51962=74976.8 | exact equality | WV union area control. |
| Q08 | PASS | A:8;B:5 | A:8;B:5 | WV fold sample counts. |
| Q09 | PASS | A EU3=2,EU4=6;B EU3=0,EU4=5 | A 2/6;B 0/5 | WV source-EU counts. |
| Q10 | PASS | 0 | 0 | No same PLT_CN overlap. |
| Q11 | PASS | 12 | 12 | W0/W1 x A/B x all/zero/positive summaries produced. |
| Q12 | PASS | 2658 | >0 | Every WV synthetic summary subset is populated. |
| Q13 | PASS | 7.05754322103e-15 | <=1e-12 relative | Empirical union covariance identity arithmetic check; maximum absolute residual=0.000202178955078. |
| Q14 | PASS | 5.88324787773e-14 | <=1e-12 relative | Candidate union covariance identity arithmetic check; maximum absolute residual=0.00105667114258. |
| Q15 | PASS | 1 | 1 | All candidate 2x2 covariance matrices are PSD within -1e-8 numerical tolerance. |
| Q16 | PASS | 0 | 0 | No real/cross-fold outcome, network, or production access. |
| Q17 | PASS | TREE/SPCD=0;real_outcome=0;D10F-C=0 | all zero | Scope boundary observed. |

## Boundary

Singleton implementation stopped before an unauthorized grouping rule. WV qualification used deterministic synthetic outcomes only. No production covariance, replicate engine, 50-km matrix, real-species analysis, external search, or A2 modification occurred.
