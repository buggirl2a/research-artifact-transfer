# Q1 FIA 合法观测机会算子 v01_1 — Work 主报告

## 终局结论

科学/算子终局：`CANDIDATE_OPERATOR_COMPLETE_WITH_BOUNDED_UNRESOLVED_STATES`

Layer 2 状态：`LAYER2_CANDIDATE_READY_WITH_EXPLICIT_UNRESOLVED_FIELDS`

该结论不冻结算子或 Layer 2，不构成 `SUPPORT IDENTIFIED`，也不构成 `SUPPORT GATE PASS`。

## 输入与重启绑定

四个受保护的小型输入均通过精确 SHA-256。Layer 1 母库路径和当前大小与已接受绑定一致，未发现替换或来源异常，因此按 v01_1 使用 `INHERITED_ACCEPTED_FULL_HASH_BINDING`；本次没有把未知的既往中断原因归因于哈希、SQLite 或表格处理，也没有仪式性重算 71.6 GB 全文件哈希。冻结底座内部 SQLite 另行通过精确 SHA 校验。

## Q1：最小物种盲状态空间

最小状态链为：plot sampling state → field/remote method → direct/inferred examination scope → sampled subplot status → linked condition status → diameter frame → condition/frame basis。每个终端类均在状态字典中有明确规则；缺失和无法闭合的组合保留为显式 unresolved。

## Q2：最小必要字段与关系

当前已接受 authority 足以解释 `PLOT_STATUS_CD`、`SAMP_METHOD_CD`、`SUBP_EXAMINE_CD`、`SUBP_STATUS_CD`、`COND_STATUS_CD`、`MACRO_BREAKPOINT_DIA`、`PROP_BASIS` 和相关比例/非抽样原因。结构关系最小为 `PLOT.CN → SUBPLOT.PLT_CN / COND.PLT_CN`，再以 `SUBP_COND(PLT_CN,SUBP,CONDID)` 保留 sampled element 与 condition 的关系。没有出现需要外部 Search 的语义命题。

## Q3：Layer 2 候选底座

候选 SQLite 含 338,619 条 F0 linkage、334,387 条 PLOT、1,337,548 条 SUBPLOT、405,427 条 COND 和 1,384,227 条 SUBP_COND link。每个来源表保留其 `CN` 和关系键；未纳入 TREE、SPCD、物种结果、坐标、support、abundance 或推测性“备用字段”。

## Q4：F0 映射闭合

F0=338,619，A=135,513，B=203,106，A/B permanent-plot overlap=0。完整逐行物种盲分类已交付；没有样地静默消失。

## Q5：可分类与 unresolved

Fully classified=219,709（64.883837%）；explicitly unresolved=118,910（35.116163%）。没有设任意比例阈值。主线需依据 unresolved reason 表决定窄修正、传播/有界推断或 claim reduction。

| Candidate class | Count | Fraction of F0 |
|---|---:|---:|
| `DIRECT_FIELD_OPPORTUNITY_ALL_FOUR_SAMPLED_SPLIT_FRAME` | 17,185 | 5.075025% |
| `DIRECT_FIELD_OPPORTUNITY_PARTIAL_ELEMENTS_SPLIT_FRAME` | 2,393 | 0.706694% |
| `NO_DIRECT_OPPORTUNITY_PLOT_STATUS_3` | 21 | 0.006202% |
| `NO_Q1_FOREST_OPPORTUNITY_PLOT_STATUS_2` | 19,457 | 5.745986% |
| `REMOTE_INFORMATION_NO_DIRECT_TREE_OPPORTUNITY` | 180,653 | 53.349930% |
| `UNRESOLVED_DIAMETER_FRAME_NO_POSITIVE_BREAKPOINT` | 114,678 | 33.866381% |
| `UNRESOLVED_PLOT_SOURCE_BINDING` | 4,232 | 1.249782% |

## Q6：DIA>=5 与 tally frame

本次复现 positive breakpoint=37,843，其中 >5 in=37,843、<=5 in=0。正 breakpoint 样地按 `5<=DIA<breakpoint` 的 subplot frame 和 `DIA>=breakpoint` 的 macroplot frame 表示。无正 breakpoint 不被解释成 subplot-only，而保留 frame unresolved。该规则只定义观测机会，不构造 support/abundance，也不改动 A2。

## Q7：Layer 2 基础设施充分性

候选底座包含当前算子所需的全部 source-native 字段和关系，保留来源键与 unresolved 值，足以作为下一 support-measurement 方法阶段的默认输入候选，避免例行重扫 Layer 1。它仍需主线审查；若目标/接口改变、需要未收录字段、来源不变量冲突、出现新关系需求，或主线授权解决无正 breakpoint 状态，才返回 Layer 1。

## 防火墙与 STOP

所有物种、SPCD、support、nondetection、Q1、abundance、TREE-query 和 internet 计数均为 0。现按授权 STOP：不启动 partial-ID/support-set Search、occupancy/detection、support 生产、坐标传播或 real Q1。
