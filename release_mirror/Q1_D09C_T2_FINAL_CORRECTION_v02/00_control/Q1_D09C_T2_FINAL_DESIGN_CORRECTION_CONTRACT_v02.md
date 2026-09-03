# Q1 / D09C T2 FINAL DESIGN CORRECTION CONTRACT v02

你是 Work computational branch（有限计算工作线）。

本任务是对已经完成且主线审核过的：

`Q1_D09C_T2_BOUNDED_v01`

进行一次**严格受限的设计修正**。

基线中转身份：

* Transfer: `Q1_D09C_T2_BOUNDED_v01`
* Commit: `32ff516192862b612240fa453ca64dd7c3ca5c9c`
* Reproducible ZIP SHA-256:
  `25f361eeeddbe02fd2f93d2daa0b0e974926a8d97965505a3bec37a65388ea7e`

上一轮 Work 的工程执行、输入完整性、48州 EXPVOL closure、480个 whole-panel candidate、fold-specific TI construction、species/outcome blindness 均已被主线接受。

本轮不推倒重算科学设计，只修正两个由上一轮真实审计暴露出的 **mainline contract-level issues（主线合同层问题）**。

---

## 1. 修正一：repair class（修复等级）必须先于 balance 排名

上一版合同允许 symmetric coarsening（对称粗化）后直接与 zero-coarsening candidate（零粗化候选）比较 design balance。

真实运行发现，这会产生不合理激励：

> 大范围粗化可能因为把许多 strata 压成少量 block，反而获得更好的 balance score。

该规则正式废弃。

### 新的候选等级

每个州的10个 whole-panel 2-vs-3 candidates 必须先分类：

### R0 — NATIVE_STRATIFICATION_VALID

* fold A / B 均合法
* 无 parent-poststratum 缺样
* 不需要任何 coarsening
* 100% population area preserved

### R1 — WITHIN_EU_SYMMETRIC_COARSENING_VALID

* native stratification 不完整
* 但按照冻结规则，在同一 estimation unit 内对 A/B 同时进行 symmetric coarsening 后可合法估计
* 100% population area preserved
* 无 estimation-unit-level zero-sample fold

### R2 — SPARSE_EU_FALLBACK_VALID

仅当该州不存在任何 R0 或 R1 candidate 时才允许进入。

见第2节。

### R3 — BLOCKED

即使允许前述合法修复仍无法形成 A/B fold-specific TI。

---

## 2. 州级候选选择规则重新冻结

严格顺序：

1. 如果存在至少一个 R0 candidate：

   * 只在 R0 内排名；
   * 所有 R1/R2 自动失去竞争资格。

2. 如果没有 R0，但存在 R1：

   * 只在 R1 内排名。

3. 如果 R0/R1 全部不存在：

   * 才允许启动 R2 sparse-EU fallback。

4. R2仍失败：

   * 州状态 = DESIGN_BLOCKED。

### 同一 repair class 内的排名

仍保持上一版冻结规则：

1. design balance
2. temporal balance
3. ascending A-panel tuple mechanical tie-break

不得把 repair magnitude 重新混入 balance score。

---

## 3. CA / OR / WA 必须按新规则重新选择

上一版 mechanical top：

* CA
* OR
* WA

均因大面积 symmetric coarsening 获得排名优势，主线不接受为最终 partition。

本轮必须重新按 repair-class hierarchy 排名。

预期不是硬编码：

* 不得直接把主线观察到的某个 rank 2 / rank 3 candidate 写成答案；
* 必须从完整10 candidate 表按照新规则机械重选。

但主线已确认三州均存在 R0 candidates，因此：

> CA / OR / WA 的最终 rule-selected candidate 必须来自 R0，除非重新验证发现此前 R0 判定错误。

如发生这种冲突，STOP 回主线。

---

# 4. WV census-water 语义已经闭合

WV：

* EXPVOL EVALID = `542301`
* sparse unit:
  `Estimation Unit 3 = Inland Census Water Unit 3`
* population area ≈ `23,014.8 acres`
* full evaluation 约2 plots

主线已完成独立 FIA 官方语义审计并冻结：

### 4.1 禁止 structural-zero shortcut

不得因为名称包含 `Inland Census Water`：

* 将整个 estimation unit tree total 设为0；
* 从 population frame 删除；
* 把无样方 fold 视为合法。

正式语义：

> `TREE_POPULATION_SAMPLING_REQUIRED`

### 4.2 官方方法事实

FIA/NRS 方法允许在样本不足时：

* merge/collapse sparse strata；
* 条件性合并 sparse estimation units。

但没有现成的官方 “Q1 2-vs-3 fold-specific merge” 规则。

因此本项目采用的 sparse-EU rule 是：

> outcome-blind、design-aligned、symmetric Q1 fallback，

不是声称为 FIA 官方标准 estimator。

---

# 5. Sparse-EU fallback 的触发条件

只有当某州：

> 全部10个 candidates 在 R0/R1 下都无法得到合法 A/B fold-specific TI

才允许启动。

不得为了改善 balance、time balance 或 precision 主动使用。

当前上一版证据显示只有 WV 触发，但必须重新机械验证，不能硬编码“只有WV”。

---

# 6. Sparse-EU merge 必须先于 A/B partition 构造

这是关键约束。

不得：

> 先看某个 partition 哪一折缺样，再针对那一折临时找 merge partner。

正确顺序：

1. 从该州完整 five-panel EXPVOL design frame 识别 sparse EU；
2. 使用 full-frame species-blind design metadata 选择 merge partner；
3. 生成一个共同的 merged design frame；
4. A/B 两折都使用完全相同的 merged frame；
5. 然后重新枚举全部10个 2-vs-3 candidates；
6. 再进行合法性和排名。

因此 merge partner：

> 与 A/B candidate、support、abundance、species outcome 完全无关。

---

# 7. WV merge partner 的 admissibility（可接受性）

候选 partner 必须：

* 同一州 WV；
* 同一 EXPVOL component `542301`；
* 是真实存在的 estimation unit；
* 不是 Unit 3 自身；
* 所需 design keys 完整；
* full five-panel frame 中有有效样本。

不得跨州。

不得借另一 evaluation。

---

# 8. Merge partner 的选择必须基于冻结设计信息，不准凭感觉

FIA 官方 sparse-EU 原则强调：

* nearby
* similar pixel / design category
* preferably relatively small unit

Work 首先检查 frozen design inputs 是否足以对这些条件进行**客观、可复现的 operationalization（操作化）**。

### 8.1 优先检查 semantic class

对 estimation-unit descriptions 做透明、可审计的语义分类。

如果除 Unit 3 外：

> 存在唯一一个可以客观判定为同一 `Inland Census Water` semantic class 的 admissible unit，

可以把它作为 unique semantic partner candidate。

不得仅凭 unit number 的大小关系推断邻近。

### 8.2 若存在多个同类候选

必须检查 frozen design data 是否提供足够信息判断：

* geographic proximity；
* 或官方可用的 pixel/design similarity。

如果能够客观判定唯一 partner：

> 输出全部候选及排序依据后继续。

如果不能：

> 状态 = `MERGE_PARTNER_AMBIGUOUS_NEEDS_MAINLINE`

立即 STOP。

不得使用：

* 最小 unit number；
* 最大 plot count；
* 最漂亮 A/B balance；
* 最小时间差；
* 任意人工选择

作为替代。

### 8.3 若不存在同 semantic-class candidate

除非 frozen design data 中存在明确、可复现的 FIA-compatible similarity criterion：

> 不得自行跨类别合并。

返回：

`MERGE_PARTNER_NOT_RESOLVED_FROM_FROZEN_DESIGN_METADATA`

并 STOP。

---

# 9. 如果 WV merge partner 唯一闭合

只有满足第8节后才能真正构造 R2。

合并方式必须：

> 在 full five-panel frame 中，将 sparse EU 与 selected partner 定义成一个共同 merged design domain。

为了避免 sparse water stratum 在合并后仍然成为 fold-specific empty stratum：

> 对该 merged domain 使用共同的 coarsened design block，使 A/B 两折都采用相同空间/设计分辨率。

要求：

* combined population area 100% preserved；
* 所有源 EU / stratum 身份保留在 audit ledger；
* A/B 对称；
* 不删除任何 population area；
* 不复用 full-evaluation EXPNS；
* fold-specific TI weights 重新合法构造；
* 记录 precision loss / coarsening magnitude，但不得据此改变 merge partner。

然后：

> 在这个共同 merged frame 上重新生成 WV 的10个 whole-panel candidates。

---

# 10. Sparse-EU fallback 后仍然 BLOCK 的条件

如果合并后：

* 某一 fold 在 merged domain 仍无 sample；
* design key 不完整；
* 100% area 无法保存；
* fold-specific TI 无法构造；

则：

`DESIGN_BLOCKED_AFTER_SPARSE_EU_FALLBACK`

STOP。

不得继续发明第二层补救。

---

# 11. TI / MA规则不变

Primary：

> fold-specific TI

禁止：

> full-evaluation EXPNS reuse。

MA：

> sensitivity feasibility only。

本轮不因 MA 结果改变 partition。

---

# 12. OR 412301 四条 mismatch

维持上一版主线裁决：

* `PLT_CN -> PLOT.CN` 全部解析成功；
* 四条全部保留；
* 不改写；
* 继续作为 nonblocking QC；
* 新 partition 若改变其 A/B fold membership，只更新 ledger 中的 final fold；
* 不删除记录。

---

# 13. 严格禁止

继续禁止读取或使用：

* TREE
* species identity/outcome
* abundance
* detection
* occupancy
* D08C2
* range / Little
* R1/R2
* World 0
* traits
* phylogeny
* climate
* real Q1

本轮仍然必须完全 species-blind / outcome-blind。

---

# 14. 不得重做已接受的无关工作

上一版 package 保持 immutable。

不得覆盖：

`Q1_D09C_T2_BOUNDED_v01`

本轮必须生成新版本输出。

建议：

`Q1_D09C_T2_FINAL_CORRECTION_v02`

旧结果作为 audit predecessor（审计前序）保存。

---

# 15. 必须输出

至少包括：

### 1.

`Q1_D09C_T2_REPAIR_CLASS_LEDGER_v02.csv`

48 × 10 candidates：

* state
* candidate
* A/B panels
* R0/R1/R2/R3
* reason
* native missing strata
* within-EU coarsening
* sparse-EU fallback
* area preserved
* TI estimable
* design balance
* temporal balance
* final rank within admissible class

### 2.

`Q1_D09C_T2_FINAL_RULE_SELECTED_PARTITIONS_v02.csv`

48州最终候选或 BLOCK。

### 3.

`Q1_D09C_T2_CA_OR_WA_RERANK_AUDIT_v02.csv`

明确比较旧 top 与新 repair-class selected candidate。

### 4.

`Q1_D09C_T2_SPARSE_EU_TRIGGER_AUDIT_v02.csv`

证明哪些州触发或未触发 R2。

### 5.

`Q1_D09C_T2_WV_MERGE_PARTNER_CANDIDATES_v02.csv`

必须输出所有 admissible partner、可用/缺失的 similarity evidence、最终是否唯一闭合。

### 6.

如果 partner 闭合：

`Q1_D09C_T2_WV_MERGED_FRAME_AUDIT_v02.csv`

包含：

* source sparse EU
* partner EU
* original areas
* combined area
* source strata
* merged design block
* A/B sample counts
* area preservation
* TI estimability

### 7.

`Q1_D09C_T2_FINAL_FOLD_SPECIFIC_TI_DESIGN_v02.csv`

### 8.

`Q1_D09C_T2_OR_412301_MISMATCH_FINAL_AUDIT_v02.csv`

### 9.

`Q1_D09C_T2_FINAL_COMPLETION_QC_v02.csv`

### 10.

`Q1_D09C_T2_FINAL_RESULT_NOTE_v02.md`

### 11.

`D09C_T2_FINAL_INDEPENDENT_VALIDATION_v02`

### 12.

`SHA256SUMS.csv`

### 13.

`TRANSFER_MANIFEST_v01.csv`

必须使用 Research Artifact Relay v0.2.2 native schema：

* local_path
* relative_path
* role
* upload_target
* required
* mainline_priority
* size_bytes
* sha256
* notes

---

# 16. 最终允许返回的全国状态

仅允许：

### `PASS_READY_FOR_MAINLINE_FINAL_D09C_AUDIT`

只有48州全部形成合法设计时。

### `MERGE_PARTNER_AMBIGUOUS_NEEDS_MAINLINE`

如果 WV partner 无法由冻结数据唯一决定。

### `MERGE_PARTNER_NOT_RESOLVED_FROM_FROZEN_DESIGN_METADATA`

如果缺乏可操作相似性信息。

### `DESIGN_BLOCKED_AFTER_SPARSE_EU_FALLBACK`

如果已合法选定 partner 但仍不能估计。

### `INPUT_BLOCKED`

输入异常。

---

# 17. STOP

完成 D09C correction 后立即 STOP。

不得：

* corrected D08C2
* species cohort
* support
* abundance
* occupancy
* Q1

本轮最终科学接受权仍属于聊天主线。

Contract ID:

`Q1_D09C_T2_FINAL_DESIGN_CORRECTION_CONTRACT_v02`
