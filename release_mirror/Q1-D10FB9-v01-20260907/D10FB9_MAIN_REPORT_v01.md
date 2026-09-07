
# D10FB9 Target-Matched Design Compatibility Preflight v01

## 普通中文结论

### 问题1：24个 singleton 在设计身份过滤后，是否全部仍有方差信息材料？

是。24/24 个 singleton 在应用 target-matched 核心设计过滤后仍保留至少一个 matched non-singleton poststratum。

### 问题2：多少个在原 EU 内解决，多少个需要州级 fallback？

11 个在原 source EU 内解决，13 个按规则进入州级 fallback 后解决；0 个未解决，0 个身份不完整。

### 问题3：WA 的 501/502 和 B8 的非 base intensity 是否被干净处理？

是。WA 的 S22/S23/S24 只保留与各自 target 的 exact DESIGNCD/raw DESIGNCD 相同的材料，不混用 501 和 502。B8 的 13 个 Level-2 case 与 nested-standard counts 全部精确对账；其中非 target-matched intensity plot rows 共排除 630 条。

WA 身份恢复遵循受控优先级：先用冻结全国 SQLite；仅对其中缺失的 CN，使用 D09C 已冻结的 WA PLOT/SURVEY 原始设计 ZIP 补齐。该 fallback 补齐 946 条、未覆盖全国 SQLite 中已存在的任何记录。

### 问题4：是否还需要第三级地理 fallback？

不需要。B9 没有发现要求第三级地理 fallback 的案例。

### 问题5：如果24/24有材料，下一步是否已经可以进入 synthetic qualification？

不能由 B9 自行授权。**Proposed mainline implication:** Q1 主线可以据此审议是否冻结两级地理范围加 target-matched core design filter，并另行授权后续 statistical/synthetic qualification。B9 本身没有运行 synthetic，也没有实现 variance。

## Main decision

`YES_24_OF_24_STRUCTURALLY_AVAILABLE`

- Total cases: 24.
- Resolved at Level 1 after filter: 11.
- Resolved at Level 2 after filter: 13.
- No compatible material within two levels: 0.
- Identity incomplete: 0.

## WA exact-match audit

| Case | Target DESIGNCD | Target raw DESIGNCD | Matched poststrata | Matched plots | Residual-df proxy |
|---|---:|---:|---:|---:|---:|
| S22 | 501 | 501 | 31 | 297 | 266 |
| S23 | 502 | 502 | 37 | 207 | 170 |
| S24 | 502 | 502 | 12 | 63 | 51 |

## B8 reconciliation

- B8 Level-2 cases checked: 13/13.
- Exact count reconciliation PASS: 13/13.
- Discrepancies: 0.
- B9 excludes non-base intensity only when it differs from the target. MANUAL and SAMP_METHOD are descriptive and never generate a hard exclusion.

## Filter authority

`B9_CORE_DESIGN_MATCH_CANDIDATE` is a project-specific contract candidate. It is not presented as an official FIA exact donor/grouping rule. Availability means only that at least one post-filter poststratum retains matched `n_h>=2`; no statistical sufficiency threshold is implied.

## Governance audit

- real target species reads = 0
- TREE/SPCD scientific analysis = 0
- abundance/support access = 0
- donor assignments = 0
- pseudo-strata assignments = 0
- variance calculations = 0
- covariance calculations = 0
- synthetic runs = 0
- external search = 0
- A2 modification = 0
- D10F-C implementation = 0

**STOP after B9 and return to Q1 mainline.**
