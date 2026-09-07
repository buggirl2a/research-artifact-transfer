
# D10FB8 State-Level Fallback Constructibility Preflight v01

## 普通中文结论

### 问题1：13个原 EU 内完全孤立的 singleton，扩大到同州＋同评价＋同 fold 后，有多少个能找到方差信息？

13/13 个案例都找到了 non-singleton 方差信息材料；其中 1 个同州范围整体兼容，12 个范围含设计异质，0 个仍孤立。

### 问题2：新增材料的抽样设计身份是否兼容？

12 个案例的同州范围混有非 base INTENSITY 等特殊身份，不能把整个州级范围直接视为统一方差池；但 13/13 个案例在保留标准全国 base-design 身份后仍有 non-singleton 材料。SAMP_METHOD=1/2 只作描述性盘点，不自行升级为设计冲突。

### 问题3：两级规则是否足以覆盖全部24个 singleton？

按当前仅写到州级范围的两级规则，还不能宣布全部 24 个 singleton 已获兼容覆盖；不过没有案例缺材料，B8 也没有证明必须扩大到第三级地理 fallback。主线首先需要冻结州内设计身份限制。

## Mainline answer

**Does Level 1 + Level 2 provide structurally available and locally design-compatible variance information for all 24 singleton cases without a third fallback? NO.**

- Level 1 solved: 11.
- Level 2 newly solved as compatible: 1.
- Level 2 scopes with nested standard-compatible non-singleton material: 13/13.
- Remaining state-scope isolated: 0.
- Available but heterogeneous: 12.
- Identity incomplete: 0.
- Total compatible structural coverage: 12/24.
- Unresolved remainder: 12.

This is not a statement that a pseudo-strata method is qualified. It is a deterministic local material-and-identity finding.

## By-state decomposition

| State | B8 cases | Compatible available | Heterogeneous | Isolated | Identity incomplete |
|---|---:|---:|---:|---:|---:|
| IA | 1 | 1 | 0 | 0 | 0 |
| IN | 3 | 0 | 3 | 0 | 0 |
| MO | 2 | 0 | 2 | 0 | 0 |
| NY | 3 | 0 | 3 | 0 | 0 |
| OH | 2 | 0 | 2 | 0 | 0 |
| PA | 2 | 0 | 2 | 0 | 0 |

## Aggregate structural distributions across the 13 Level-2 cases

- Non-singleton poststrata: min 28, median 45, max 73.
- Non-singleton plots: min 1490, median 1774, max 4393.
- Residual-df proxy `sum(n_h-1)`: min 1459, median 1714, max 4348.
- Distinct source EUs represented: min 10, median 17, max 29.

## Design-compatibility interpretation

- Every candidate non-singleton row was audited against D10C-A and frozen local PLOT/SURVEY identity.
- MANUAL values are inventoried, but version differences alone were not promoted into an invented incompatibility rule.
- `DESIGNCD`, raw `DESIGNCD`, repair class, `INTENSITY`, production QA, `KINDCD`, sampling method, `SUBPANEL`, source EU, and locally recoverable regional/NF fields are reported.
- `SAMP_METHOD_CD=1/2` is reported but does not itself define a new design class here; several target singleton rows themselves use code 2.
- Candidate material is an inventory. No poststratum, source EU, plot, or identity bucket was selected as a donor.

## WA special attention

- B8 target cases in WA: 0.
- Therefore the B7 warning about WA `DESIGNCD=501/502` is retained but is not part of any B8 target pool.
- B8 does not merge, reinterpret, or qualify 501 and 502.

## Governance audit

- real target-species reads = 0
- TREE/SPCD scientific analysis = 0
- donor assignments = 0
- variance calculations = 0
- covariance calculations = 0
- synthetic runs = 0
- external search = 0
- A2 modification = 0
- D10F-C implementation = 0

## Status discipline

B8 does not announce pseudo-strata PASS, singleton Gate PASS, abundance Gate PASS, or D10F-C authorization. Final project-specific contract freeze belongs to Q1 mainline.

**STOP after B8 and return to Q1 mainline.**
