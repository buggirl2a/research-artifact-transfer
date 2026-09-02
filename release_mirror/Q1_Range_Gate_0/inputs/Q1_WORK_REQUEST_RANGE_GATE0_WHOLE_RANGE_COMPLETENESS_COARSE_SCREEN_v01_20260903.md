# Q1 WORK REQUEST — Range Gate 0 whole-range completeness coarse screen

**Version:** v0.1  
**Date:** 2026-09-03  
**Project:** 分布区论文 / Q1 species-range internal structure  
**Authority:** scientific mainline / PI  
**Execution branch:** Work / bounded computational branch  
**Status:** AUTHORIZED AFTER D09C MAINLINE AUDIT

---

## 0. Scientific purpose

Range Gate 0（分布完整性粗筛门）只回答一个问题：

> 对已经确认在 CONUS（美国本土48州）有原生分布的候选物种，哪些物种的完整天然分布明显超出 CONUS，以至于 CONUS 内的 range geometry（分布区几何）不能未经进一步审核就代表 whole-range geometry（完整分布区几何）？

本阶段不是最终 whole-range completeness（完整分布区完整性）判定，不重建完整全球 range，不计算完整分布面积比例，不运行真实 Q1。

### Scientific rationale

Q1 第一篇论文的 core analysis（核心分析）目标是 whole-range core analysis（完整分布区核心分析）。FIA abundance（多度）数据目前只能支持 CONUS 研究域。因此：

- “在 CONUS 原生”只是必要条件，不等于“CONUS 基本覆盖完整天然分布”。
- 加拿大、阿拉斯加、墨西哥、中美洲、加勒比或北美之外的天然分布都可能造成 range truncation（分布区截断）。
- Range Gate 0 的任务是用**已经冻结的 WCVP / taxonomy（分类学）事实做低成本分层**，把明显可保留、明显不适合 whole-range core、以及需要后续定量审核的物种分开。

---

## 1. Governance and hard boundary

### 1.1 Work role

Work 只执行本冻结合同中的事实重组、规则分类、QC（质量控制）与可复现打包。

Work **不得**自行：

- 改变 whole-range core 的科学对象；
- 改变分类学 authority（权威）；
- 新增外部数据源；
- 根据 FIA abundance / detection / occupancy / eligibility 结果改变 Range Gate 0 分类；
- 设定任何面积比例阈值；
- 选择最终 species cohort（物种队列）；
- 运行 D08C2 或真实 Q1。

### 1.2 Outcome-blind rule（结果盲规则）

本阶段允许读取物种身份、WCVP 原生分布事实和 D08B1 冻结分类学结果；**禁止读取或使用任何物种级 FIA abundance（多度）、support/detection（支持域/检出）、A/B cell count（A/B 格子数）、D08C1/D08C2 eligibility（资格）、R1/R2、World 0、prediction（预测）或真实 Q1 outcome（结果）来影响分类。**

### 1.3 Parallelism with FIA design closure

Range Gate 0 与 FIA reporting-frame / raw-authority closure（报告时间框架 / 原始权威闭合）正交。本请求不等待 T1/T2 最终冻结，也不得触碰 T1/T2、P2PANEL、TI/MA 等 FIA 设计事项。

---

## 2. Authoritative frozen input

### 2.1 Package authority

使用已冻结的：

- GitHub release/mirror: `Q1-D08B1-v02-20260902`
- D08B1 v02 reproducible delivery ZIP SHA-256:  
  `3647c35189110d524d5f6cd64bf2d4aabaaa80828e58f42e767bb5e862188a3e`

若本地已有 D08B1 v02 authority，必须先 hash-match；若需通过项目 GitHub relay 获取，只允许获取该冻结 release/mirror，不允许访问新的 WCVP/POWO/Little/USGS/NatureServe/GBIF/网页来源。

### 2.2 Required authoritative members

至少使用下列 D08B1 v02 authoritative outputs，并验证内容 hash：

1. `outputs/Q1_ANALYSIS_SPECIES_MASTER_v02.csv`  
   作用：361-species accepted analysis-species master（361个接受分析物种主表）  
   SHA-256: `6f69874ab02723b3489aa4f3cbfb5aba188147400efdf170f27ad699d6368cb0`

2. `outputs/Q1_GLOBAL_RANGE_FLAGS_v02.csv`  
   作用：species-level global-range flags（物种级全球分布标记）  
   SHA-256: `dc64778032ed9bd301bfc7c14818fc3ba71a3b2621bb4e8b33ec558ecdf3d16d`

3. `outputs/Q1_WCVP_NATIVE_DISTRIBUTION_LONG_v02.csv`  
   作用：WCVP Level-3 native/introduced evidence（WCVP三级单元原生/引入证据）  
   SHA-256: `559a2d6f7b0d67ad886468a2c0098e117c824f196f0a85d3bb7d99c466649017`

4. 如需解释 D08B1 已冻结的 macro-region rule（宏区域规则），只允许读取同一 D08B1 v02 package 内的冻结 contract/control/code/provenance；不得创建新的地理区字典或访问外部来源。

### 2.3 Exact Gate 0 input universe

从 361 个 ordinary accepted analysis species（普通接受分析物种）中，使用 D08B1 v02 的冻结字段：

`confirmed_native_CONUS == TRUE`

定义 Range Gate 0 的输入宇宙。

**预期必须恰好为 312 个物种。**

若不是 312：

> `INPUT_BLOCKED`

立即 STOP，返回输入差异，不得自行修补、重新解释或改用其他名单。

312 只能称为：

> **CONUS-native candidate pool（美国本土原生候选池）**

不得称为 final cohort（最终队列）或 whole-range-complete cohort（完整分布区队列）。

---

## 3. Frozen scientific classification

Range Gate 0 必须对 312 个物种逐一且唯一分类。分类使用以下优先级；高优先级一旦满足，不再被低优先级覆盖。

### Class 1 — `FAIL_EXTRA_NA`

中文：**北美之外也有确认原生分布；whole-range core 粗筛排除**。

满足任一冻结事实：

- `confirmed_native_outside_North_America == TRUE`；或
- `transcontinental_circumboreal_global_extension_flag == TRUE`；或
- 同一 D08B1 v02 冻结原生分布证据明确显示存在北美之外的原生 Level-3 unit，而现有汇总 flag 因已知 QC 问题未反映；此类只能在 package 内部证据完全闭合时使用，并必须单列 audit note（审计说明）。

科学含义：CONUS FIA abundance 无法代表其 whole-range population geography（完整分布种群地理），因此第一篇 whole-range core analysis 原则排除。

后续路线：

`EXCLUDE_WHOLE_RANGE_CORE`

不得删除原始记录；保留为 non-core / future sensitivity（非核心 / 未来敏感性）候选。

---

### Class 2 — `BORDERLINE_SOUTH`

中文：**中美洲 / 加勒比 / 其他南部或岛屿型北美延伸的高风险边界候选**。

在未满足 Class 1 的前提下，若冻结 D08B1 v02 证据显示：

- `confirmed_native_Central_America == TRUE`；或
- 存在除 CONUS、Canada、Alaska、Mexico 之外的、仍属于 D08B1 冻结 North-America-side macro-region rules（北美侧宏区域规则）的确认原生 Level-3 units（例如加勒比/相关岛屿单元）。

**只允许复用 D08B1 v02 已冻结的 macro-region mapping（宏区域映射）。若冻结规则无法无歧义识别该单元，不得自行新建 Caribbean whitelist（加勒比白名单）；改列 `UNKNOWN`。**

后续路线：

`RETAIN_BORDERLINE_EXTERNAL_AUDIT_LATER`

本阶段不下载或搜索外部完整 range。

---

### Class 3 — `BORDERLINE_MEXICO`

中文：**墨西哥延伸边界候选**。

在未满足 Class 1–2 的前提下：

- `confirmed_native_Mexico == TRUE`

后续路线：

`RETAIN_BORDERLINE_EXTERNAL_AUDIT_LATER`

本阶段不根据墨西哥 Level-3 unit 数量推断面积，也不搜索墨西哥地图。

---

### Class 4 — `RETAIN_USCA_AUDIT`

中文：**美国+加拿大/阿拉斯加范围候选；保留进入后续定量截断审核**。

在未满足 Class 1–3 的前提下，满足任一：

- `confirmed_native_Canada == TRUE`；
- `confirmed_native_Alaska == TRUE`。

科学含义：仅凭 WCVP 行政地理事实不能判断 CONUS 保留了多少完整 geometry（几何）；必须后续在真正的 D08C2 幸存者中用可用的 USA+Canada/Alaska geometry source（几何来源，优先已冻结 Little 可覆盖部分）定量审核。

后续路线：

`RETAIN_FOR_LITTLE_OR_USCA_TRUNCATION_AUDIT`

本阶段**不计算**：

- CONUS share；
- area retention（面积保留）；
- span retention（跨度保留）；
- component retention（连通组分保留）；
- geometry distortion（几何畸变）。

---

### Class 5 — `PASS_COARSE`

中文：**当前冻结事实下未发现 CONUS 外确认原生延伸；粗筛通过**。

必须同时满足：

- `confirmed_native_CONUS == TRUE`；
- 未满足 Class 1–4；
- D08B1 v02 原生分布证据没有 unresolved geographic contradiction（未解决地理矛盾）。

后续路线：

`COARSE_CORE_PASS`

注意：`PASS_COARSE` 不是最终 whole-range completeness PASS，更不是 final cohort。它只表示“冻结 WCVP 粗筛没有发现明显 CONUS 外天然范围截断”。

---

### Class 6 — `UNKNOWN`

中文：**冻结事实不足或地理分类无法无歧义闭合**。

包括但不限于：

- required flags 缺失/非二值/冲突；
- D08B1 v02 的 Level-3 evidence 与汇总 flags 存在不能在冻结 package 内解决的冲突；
- Caribbean / island / macro-region 归属无法从 D08B1 已冻结规则无歧义恢复；
- native status（原生状态）存在未解决 doubtful / unresolved 情况且会改变 Gate 0 类别。

后续路线：

`HOLD_TARGETED_REVIEW_LATER`

不得猜测补齐。

---

## 4. Critical interpretation rules

### 4.1 Administrative-unit counts are NOT area

硬规则：

> **不得用 WCVP Level-3 行政/植物地理单元数量代替 range area（分布面积）、CONUS share（CONUS占比）或 truncation severity（截断严重度）。**

禁止类似：

- “美国20州、加拿大2省，因此美国占约90%”；
- “墨西哥只有1个 Level-3 unit，因此影响很小”；
- 按 unit count 设置任何 PASS/FAIL 阈值。

### 4.2 No geometry reconstruction

本阶段不构造 polygon / raster（多边形/栅格），不计算 shape/topology（形状/拓扑），不做 range completeness proportion（分布完整度比例）。

### 4.3 No Little decision use

本阶段不得读取 Little 图层内容来改变 Gate 0 class，也不得修复全部 Little review cases。

若 D08B1 v02 中已有 Little bridge status（桥接状态），可在最终表中作为**原样 passthrough audit metadata（透传审计元数据）**，但不得进入分类逻辑。

### 4.4 No new external range search

禁止新访问/搜索：

- NatureServe；
- GBIF；
- POWO/WCVP live pages；
- BONAP；
- 加拿大/墨西哥/加勒比国家或区域 atlas；
- SDM（物种分布模型）；
- 任何新全球范围图。

Range Gate 0 必须完全 source-frozen（来源冻结）。

---

## 5. Required outputs

建议输出目录：

`C:\range_paper\07_results\range_gate0_v01\`

### 5.1 `Q1_RANGE_GATE0_SPECIES_CLASSIFICATION_v01.csv`

必须 312 行，一物种一行。至少包含：

- `analysis_species_id`
- `analysis_species_name`
- `confirmed_native_CONUS`
- `confirmed_native_Canada`
- `confirmed_native_Alaska`
- `confirmed_native_Mexico`
- `confirmed_native_Central_America`
- `confirmed_native_outside_USA_Canada`
- `confirmed_native_outside_North_America`
- `transcontinental_circumboreal_global_extension_flag`
- `confirmed_native_level3_areas`
- `confirmed_native_outside_USA_Canada_level3_areas`
- `confirmed_native_outside_North_America_level3_areas`
- `range_gate0_class`
- `range_gate0_reason_code`
- `range_gate0_evidence_text`
- `whole_range_core_route`
- `requires_future_usca_little_audit`
- `requires_future_external_range_audit`
- `range_gate0_final_cohort_flag`（必须全部为 0；Range Gate 0 不选 final cohort）

### 5.2 `Q1_RANGE_GATE0_SUMMARY_v01.csv`

按 class 汇总：

- class
- species_count
- percent_of_312
- downstream_route

所有类别总数必须精确等于 312。

### 5.3 `Q1_RANGE_GATE0_DECISION_QUEUE_v01.csv`

只包含：

- `BORDERLINE_SOUTH`
- `BORDERLINE_MEXICO`
- `RETAIN_USCA_AUDIT`
- `UNKNOWN`

用于未来和 corrected D08C2 幸存者求交集后再定向处理。

本文件**不是立即人工审核清单**；不得据此启动 Little 或外部搜索。

### 5.4 `Q1_RANGE_GATE0_FAIL_EXTRA_NA_v01.csv`

只列 `FAIL_EXTRA_NA`，保留完整冻结证据与 reason code（理由代码），供主线审核 whole-range core 排除是否合理。

### 5.5 `Q1_RANGE_GATE0_QC_v01.csv`

至少检查：

- D08B1 package/member hashes；
- 361 analysis species master row count；
- input universe exact 312；
- all 312 unique analysis_species_id；
- exactly one Gate 0 class per species；
- class counts sum to 312；
- no `PASS_COARSE` species has any frozen confirmed external-native flag compatible with Class 1–4；
- every `FAIL_EXTRA_NA` has explicit frozen extra-North-America/transcontinental evidence；
- no external/network source used except optional project GitHub relay to obtain the exact frozen D08B1 package；
- no Little layer content used for decisions；
- no FIA outcome / D08C eligibility / abundance / detection / real-Q1 table read；
- no final cohort flag selected。

### 5.6 `RANGE_GATE0_RESULT_NOTE_v01.md`

简要报告：

- execution PASS/FAIL；
- 312 输入闭合；
- 六类数量；
- 任何 `UNKNOWN` 原因；
- 明确声明没有做面积推断、Little 精细处理、外部搜索、D08C2 或真实 Q1；
- STOP，交回 scientific mainline。

### 5.7 Reproducibility package

生成：

- reproducible ZIP；
- ZIP SHA-256；
- delivery index；
- content manifest；
- 独立 output-only audit（输出独立审计）。

代码文件可放在可复现包内，但**不要在聊天正文返回源代码**。

---

## 6. Computational PASS / FAIL

### PASS only if all are true

1. Frozen D08B1 v02 authority hashes match.
2. 361-species master closes exactly.
3. `confirmed_native_CONUS == TRUE` yields exactly 312 input species.
4. All 312 receive exactly one class according to the frozen precedence.
5. All class assignments are traceable to frozen D08B1 v02 evidence.
6. No WCVP unit count is converted to area/truncation proportion.
7. No new external source or Little layer content is used for classification.
8. No FIA species outcome / eligibility / abundance / detection / Q1 result is read.
9. No final cohort is selected.
10. Required outputs and independent audit close reproducibly.

### FAIL / INPUT_BLOCKED categories

- `INPUT_BLOCKED`: frozen package/hash/312-universe mismatch.
- `REPRESENTATION_BLOCKED`: frozen D08B1 geography rules are insufficient to distinguish a required category; affected species must be `UNKNOWN`, not guessed. If this becomes systemic and prevents meaningful Gate 0 classification, STOP and report.
- `ENGINEERING_FAIL`: computation/QC/package integrity failure.

No scientific threshold may be modified after seeing class counts.

---

## 7. Scientific interpretation boundary

Range Gate 0 is a **coarse routing gate（粗筛路由门）**，不是最终完整分布裁决。

After mainline audit:

- `FAIL_EXTRA_NA`：原则上从第一篇 whole-range core analysis 排除，但主线最终确认；
- `PASS_COARSE`：只表示粗筛无明显外延；仍需后续 FIA eligibility（资格）等 Gate；
- `RETAIN_USCA_AUDIT`：未来只对 corrected D08C2 真正幸存者做 USA+Canada/Alaska quantitative truncation audit（定量截断审核）；
- `BORDERLINE_MEXICO` / `BORDERLINE_SOUTH`：未来只对真正幸存者做 targeted external-range audit（定向外部分布审核）；
- `UNKNOWN`：未来只在成为真正幸存候选时定向解决。

**不得因为本次 class count 很多/很少而事后调整分类规则。**

---

## 8. Frozen downstream order after this request

Range Gate 0 与 FIA raw-authority/design closure 可并行。

二者完成并经 scientific mainline 审核后：

> `FIA design closure + Range Gate 0 -> corrected D08C2 -> intersect with Gate 0 routes -> targeted Little / external-range audit only for survivors -> final cohort -> real Q1`

本请求完成后：

> **STOP. Return package to scientific mainline.**

不得自动启动 corrected D08C2、Little、外部分布搜索或真实 Q1。
