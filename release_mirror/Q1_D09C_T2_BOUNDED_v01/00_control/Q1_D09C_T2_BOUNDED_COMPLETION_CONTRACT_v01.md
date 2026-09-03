这是 **Q1 / D09C T2 BOUNDED COMPLETION CONTRACT v01**。

你是 **Work computational branch（有限计算工作线）**。本任务由聊天主线冻结科学合同后授权执行。

你的职责是：

> 在不读取物种结果、不改变科学定义、不自行选择新的估计目标的前提下，把已经选定的 FIA T2 reporting-frame family（报告框架族）补全为全国可审计的 A/B whole-panel design（整面板 A/B 设计），并返回主线做最终科学 PASS/FAIL 与设计选择。

你不是 PI，不得改变本合同。

---

# 0. 科学背景与冻结目标

Q1 的核心科学问题是：

> 已知一个物种当前 occupied support（占据支持域）的空间结构以后，我们究竟因此知道了多少关于其 population-mass allocation（种群质量空间配置）的信息？

本任务 **不是 Q1 分析本身**。

本任务只负责闭合 FIA survey-design layer（FIA抽样设计层），为后续：

* support branch（支持域分支）
* abundance branch（多度分支）
* A/B cross-fitting（A/B交叉拟合）
* corrected D08C2
* observation model
* real Q1

提供一个冻结、合法、可复现的 FIA sampling design（抽样设计）。

---

# 1. 已冻结的 reporting-frame family

## 1.1 T1

`T1 uniform 2022`

正式状态：

> **DROP**

不得恢复、比较、优化或重新选择。

---

## 1.2 T2

T2 已由主线选为唯一允许进入本任务的 reporting-frame family：

> **2023 reporting frame for 45 states + 2022 MT/NM/UT**

不得重新比较 T1/T2。

---

# 2. 主 evaluation concept 已冻结

Q1 的 population object（种群对象）是：

> contemporary large-tree population-mass allocation（当前大树计测状态下的种群质量空间配置）

因此统一使用：

> **component evaluation carrying `EVAL_TYP = EXPVOL`**

即：

> current area + current volume / tree-population estimation frame（当前面积 + 当前材积/树木总体估计框架）

不得因为某个其他 component 行数更多或结构更完整而改用：

* EXPALL
* EXPCHNG
* EXPGROW
* EXPMORT
* EXPREMV
* EXPDWM

### 已闭合三州 component EVALID

* CA2023 → `62301`
* OR2023 → `412301`
* WA2023 → `532301`

其他州必须按已有 D09C/T2 官方 raw key / frozen evidence 使用其真实 EXPVOL component。

不得根据编号命名规律猜 EVALID。

---

# 3. Support 与 abundance 使用同一个 reporting frame

后续：

* support branch
* abundance branch

必须基于：

> **相同 EXPVOL reporting frame**

不得出现：

> support 用 EXPALL，abundance 用 EXPVOL

之类的 frame mismatch（框架不一致）。

本任务只建立这个共同 survey frame，不做 support 或 abundance 计算。

---

# 4. A/B whole-panel design 冻结

FIA 的 `P2PANEL` 是州内 five-panel design identity（五面板设计身份）。

## 4.1 基本结构

每州：

* A = **2 whole panels**
* B = **其余互补 3 whole panels**

不得拆 panel。

不得按 plot 随机分割。

不得按物种分割。

---

## 4.2 每州共有 10 个候选

每州枚举：

> `C(5,2)=10`

个 2-vs-3 whole-panel partitions（整面板划分）。

---

## 4.3 每州可以选择不同 partition

允许：

> 每个州根据同一套 outcome-blind design rule（结果盲设计规则）选择自己的最佳 partition。

不要求全国所有州使用相同 panel 编号组合。

原因：

> P2PANEL 是州内设计身份，而不是全国共享的生态/时间分组。

---

## 4.4 但州内一旦选定，所有物种统一

最终某州选定 A/B partition 后：

> 该州所有后续物种必须共用这一套 partition。

绝对禁止：

* species-specific partition
* genus-specific partition
* abundance-informed partition
* detection-informed partition

---

## 4.5 AB / BA

后续正式交叉方向定义为：

### AB

A → support
B → abundance

### BA

B → support
A → abundance

BA 只交换 A/B 的科学角色。

> **不得为 BA 重新选择另一套 panel partition。**

---

# 5. Partition ranking rule 已冻结

所有 10 个候选必须用完全 species-blind（物种盲）、outcome-blind（结果盲）的设计变量排序。

优先级严格为：

## Priority 1 — design validity / estimability

设计有效性 / 可估计性

必须检查：

* component EVALID membership
* estimation-unit presence
* stratum availability
* plot-to-stratum linkage
* fold-specific estimation feasibility
* population area preservation
* required design keys

凡是无法构造合法 fold-specific estimator 的 candidate：

> 不得因 temporal balance 或 plot count 好看而获胜。

---

## Priority 2 — spatial / design balance

空间 / 设计平衡

在合法 candidate 中，优先 A/B 在各：

* estimation units
* relevant poststrata / strata
* survey-design blocks

内接近理论 2/5 vs 3/5 覆盖结构。

不得仅用：

> statewide total plot count

作为设计平衡唯一指标。

应优先防止：

> 某些设计单元几乎全部落入 A 或 B。

---

## Priority 3 — temporal balance

时间平衡

仅在前两项相近时，优先：

> A 与 B measurement-year distribution / center（测量年份分布/中心）更接近的 partition。

时间平衡不得凌驾于设计完整性。

---

## Tie-break

若以上指标完全无法区分：

> 使用预先固定的机械 tie-break。

建议：

> 按 A-panel tuple 的 ascending lexicographic order（升序字典序）

不得人工挑选。

---

# 6. Primary estimator 已冻结：TI

主 estimand（估计目标）不是某一个瞬时日期的树木总体，而是：

> **contemporary survey-window population state（当前调查窗口内的种群状态）**

因此：

> **Primary estimator = fold-specific TI — Temporally Indifferent estimation（折内时间不敏感估计）**

---

## 6.1 严禁复用 full-evaluation EXPNS

官方完整 five-panel evaluation 的 `EXPNS`：

> 不得直接套给 2-panel A 或 3-panel B。

A/B 每一折必须：

> 基于该 fold 实际进入的 FIA sample + frozen design metadata

重新构造合法：

> **fold-specific design weights / expansion factors（折内设计权重/扩展因子）**

不得把完整5-panel expansion factor 当作子样本 fold factor。

---

# 7. MA 的地位已冻结

MA = Moving Average estimation（移动平均估计）

正式角色：

> **sensitivity only（仅敏感性分析）**

不得让：

* MA completeness
* MA stability
* MA numerically nicer results

反过来决定 primary estimator。

如果 MA 在某州/某 fold 因 sparse single-panel structure（单面板稀疏结构）无法稳定合法构造：

> 记录原因即可。

不得因此推翻 TI。

不得为了“救 MA”增加复杂工程。

---

# 8. Empty poststratum 治理规则已冻结

不得使用任何类似：

> 99%
> 99.5%
> 99.8%

这样的任意 area-recovery threshold（面积恢复阈值）决定 PASS。

尤其不得因为 WV 已知 recovery ≈ 0.9985 而事后创造阈值。

---

## 8.1 全国统一规则

如果某个 A/B fold 在某 estimation unit 内：

> 一个 parent poststratum 没有任何有效 sample plot

则：

> **不得直接删除该 poststratum 对应的 population area。**

必须使用：

> **symmetric coarsening（A/B 对称粗化）**

即：

在该 estimation unit 内，把 A 和 B 两折都统一降到相同的、更粗一级 stratification（分层）。

即使只有一折缺失：

> 另一折也跟随使用相同粗化后的 stratification。

目标：

* 保留100% population area
* A/B 使用同一设计分辨率
* 不因 fold-specific missing stratum 制造不对称
* 只牺牲局部 precision（精度），不丢总体面积

---

## 8.2 粗化边界

只允许在：

> **同一 estimation unit 内**

进行必要的 stratification coarsening（分层粗化）。

不得跨州任意合并。

不得跨不相干 estimation unit 合并。

---

## 8.3 真正的 BLOCK 条件

如果粗化到 estimation-unit level 后：

> 某一 fold 在该 estimation unit 仍然没有任何有效 sample plot

则状态必须：

> **DESIGN_BLOCKED_ESTIMATION_UNIT_UNSAMPLED**

并立即返回主线。

不得自行：

* 丢掉该 estimation unit
* 借另一折估计
* 借邻州估计
* 插值
* impute（插补）
* 使用物种数据补救
* 修改 A/B 规则

---

# 9. WV exception

WV 不再拥有任何州级特殊宽容规则。

此前约：

> missing parent poststratum ≈ 23,014.8 acres
> area recovery ≈ 0.9985158

只作为 historical diagnostic（历史诊断）保留。

正式处理：

> **服从与全国所有州完全相同的 symmetric coarsening rule。**

不得设置 `WV-specific exception`。

---

# 10. Oregon 412301 四条 mismatch

已知：

> OR `EVALID=412301`

中有4条记录：

`POP_PLOT_STRATUM_ASSGN` 冗余保存的 `STATECD/INVYR`

与其所链接 `PLOT` 记录存在 mismatch。

但：

> `PLT_CN → PLOT.CN`

全部成功，未发生 unresolved foreign key。

正式规则：

> **plot identity 以 `POP_PLOT_STRATUM_ASSGN.PLT_CN → PLOT.CN` 为准。**

因此这4条：

* 保留
* 不删除
* 不改写
* 不阻断 D09C
* 单独输出 QC evidence

不得自行“清洗”。

---

# 11. SURVEY duplicate-key false alarm

此前 local verification 将：

> 相同 `STATECD + INVYR` 出现多条 SURVEY record

判为 duplicate issue。

主线已裁定：

> **不得要求 `STATECD + INVYR` 在 SURVEY 中唯一。**

后续 Work 不得因此把 CA/OR/WA 判 design incomplete。

需要 SURVEY 时：

> 使用 FIADB 的真实合法 identity / keys 和实际调查记录关系。

不得依赖错误的两字段唯一性假设。

---

# 12. 必须补全的全国范围

目标：

> **完整 T2 48-state design completion**

也就是将新闭合：

* CA2023
* OR2023
* WA2023

接回此前已有 D09C T2 全国框架。

不得重跑或覆盖此前已经 accepted/frozen 的无关科学产物。

允许为了生成一致的全国 D09C completion package：

> 读取已有 D09C frozen design outputs + 新三州 frozen raw-design evidence

并重新构造必要的全国 design tables。

---

# 13. Work 必须完成的计算

至少包括：

### A. T2 EXPVOL frame inventory

每州：

* target reporting frame
* EXPVOL component EVALID
* reporting/inventory-year span
* component membership integrity

---

### B. five-panel closure

每州：

* P2PANEL 1–5 presence
* plot counts
* design-block distribution
* measurement-year distribution
* relevant estimation-unit / stratum coverage

---

### C. 10 candidate partitions

每州枚举全部10个：

* A = 2 panels
* B = complementary 3 panels

---

### D. design validity

每 candidate / fold 检查：

* estimation-unit coverage
* stratum/poststratum coverage
* population area preservation
* necessary coarsening
* fold-specific TI estimability
* any true design block

---

### E. symmetric coarsening

根据本合同统一规则：

* 标记哪些 candidate 需要 coarsening
* coarsening 在哪个 estimation unit
* 原始 stratum structure
* coarsened structure
* preserved area
* A/B resulting design

---

### F. design balance ranking

对合法候选计算 species-blind design-balance metrics。

必须能让主线看到：

> 为什么 candidate X 比 candidate Y 更均衡。

不得只输出一个总分而没有分量。

---

### G. temporal balance

对合法候选计算：

* A measurement-year distribution
* B measurement-year distribution
* temporal center / spread difference

仅作为第三优先级。

---

### H. candidate ranking

严格应用：

1. design validity
2. design balance
3. temporal balance
4. mechanical tie-break

输出：

> 每州全部10个候选的完整排名

以及：

> rule-selected top candidate

注意：

> Work 可以根据冻结规则机械地产生“rule-selected top candidate”，但这不等于主线已经最终 ACCEPT。

最终科学签字由主线完成。

---

### I. fold-specific TI construction audit

对 rule-selected candidate 至少完成：

* A fold TI design construction
* B fold TI design construction
* no full-evaluation EXPNS reuse
* population-area accounting
* estimation-unit accounting
* poststratum/coarsening accounting

---

### J. MA sensitivity feasibility

只检查：

* 是否可合法实现
* 是否有 empty/sparse panel blocks
* 是否值得进入后续 sensitivity

不得让 MA 决定 primary design。

---

### K. Oregon 4 mismatch audit

精确返回4条：

* PLT_CN
* assignment STATECD/INVYR
* PLOT STATECD/INVYR
* component EVALID
* panel
* design membership
* whether included in rule-selected A or B

只报告，不删除。

---

### L. WV audit

精确报告：

* 哪个 candidate / fold 曾出现 parent-poststratum issue
* symmetric coarsening 后结果
* population area preservation
* TI estimability

不得使用旧 99.x% 放行逻辑。

---

# 14. 严格禁止读取的科学数据

本任务必须保持 species-blind / outcome-blind。

禁止读取或使用：

* TREE species outcomes
* species abundance
* species detection
* species occupancy
* D08C2 species eligibility
* range geometry
* Little range
* WCVP range flags except already frozen reporting context
* support maps
* R1 / R2
* World 0
* traits
* phylogeny
* climate
* Q1 prediction outcomes

尤其：

> 不得根据“哪个 partition 对物种效果更好”选择 panel。

---

# 15. 不得执行的下游任务

本任务不得：

* 运行 corrected D08C2
* 产生最终 species cohort
* 估计 support
* 运行 occupancy–encounter model
* 读取 TREE 计算 abundance
* 生成50 km abundance maps
* 运行 AB / BA Q1
* 构造 R1/R2
* 运行 World 0
* 训练 cross-species model
* 做 conformal prediction
* 做 real Q1
* 写论文结果

完成 D09C bounded completion 后 STOP。

---

# 16. 必须输出的核心结果

文件名可保持该语义，版本统一 v01。

至少包含：

1. `Q1_D09C_T2_NATIONAL_FRAME_COMPLETION_v01.csv`

每州一行，记录：

* reporting frame
* EXPVOL EVALID
* panel completeness
* primary design status
* blocking status

---

2. `Q1_D09C_T2_ALL_PARTITION_CANDIDATES_v01.csv`

48 × 10 candidate 全表。

至少包含：

* state
* A panels
* B panels
* design-validity metrics
* estimation-unit coverage
* stratum/poststratum coverage
* coarsening requirements
* area preservation
* design-balance metrics
* temporal-balance metrics
* ranking components
* final mechanical rank

---

3. `Q1_D09C_T2_RULE_SELECTED_PARTITIONS_v01.csv`

每州一行：

* selected A
* selected B
* why selected
* coarsening status
* TI feasibility
* MA sensitivity feasibility
* QC flags

---

4. `Q1_D09C_T2_FOLD_SPECIFIC_TI_DESIGN_v01.csv`

rule-selected design 的：

* state
* fold
* estimation unit
* stratum/coarsened stratum
* sample support
* population area
* fold-specific design weight / expansion-factor construction evidence
* no-full-EXPNS-reuse evidence

---

5. `Q1_D09C_T2_SYMMETRIC_COARSENING_AUDIT_v01.csv`

列出所有发生 coarsening 的州 / candidate / estimation unit。

---

6. `Q1_D09C_T2_WV_AUDIT_v01.csv`

---

7. `Q1_D09C_T2_OR_412301_MISMATCH_AUDIT_v01.csv`

---

8. `Q1_D09C_T2_MA_SENSITIVITY_FEASIBILITY_v01.csv`

只做 feasibility，不做 outcome comparison。

---

9. `Q1_D09C_T2_COMPLETION_QC_v01.csv`

---

10. `Q1_D09C_T2_RESULT_NOTE_v01.md`

只总结设计事实，不替主线做科学外推。

---

11. `SHA256SUMS.csv`

---

12. `TRANSFER_MANIFEST_v01.csv`

使用 Research Artifact Relay v0.2.2 native schema：

* `local_path`
* `relative_path`
* `role`
* `upload_target`
* `required`
* `mainline_priority`
* `size_bytes`
* `sha256`
* `notes`

---

# 17. 状态词限制

全国整体只允许返回：

* `PASS_READY_FOR_MAINLINE_D09C_SCIENTIFIC_AUDIT`
* `PASS_WITH_NONBLOCKING_QC_READY_FOR_MAINLINE_AUDIT`
* `DESIGN_BLOCKED`
* `INPUT_BLOCKED`

每州可以使用：

* `DESIGN_COMPLETE`
* `DESIGN_COMPLETE_WITH_SYMMETRIC_COARSENING`
* `DESIGN_COMPLETE_WITH_NONBLOCKING_QC`
* `DESIGN_BLOCKED_ESTIMATION_UNIT_UNSAMPLED`
* `INPUT_BLOCKED`

不得自行使用：

> `FINAL_ACCEPTED`
> `Q1_READY`
> `SPECIES_READY`

等越权状态。

---

# 18. STOP conditions

如果发现以下任意情况：

### A.

某州无法找到真实 EXPVOL component

→ STOP / INPUT_BLOCKED

### B.

某 fold 即使 estimation-unit-level coarsening 后仍无样方

→ DESIGN_BLOCKED

### C.

需要违反 A=2 whole panels / B=3 whole panels 才能估计

→ DESIGN_BLOCKED

### D.

需要丢弃 population area 才能估计

→ DESIGN_BLOCKED

### E.

需要读取 TREE / species outcome 才能决定 partition

→ STOP，不得读取

### F.

冻结合同本身存在无法解释的冲突

→ STOP，返回主线，不得自行修改合同

---

# 19. 最终回传顺序

完成后首先只报告：

1. 全国 T2 EXPVOL frame：

   * 完整州数
   * BLOCK州数

2. 48州是否都存在合法 2-vs-3 whole-panel design

3. 需要 symmetric coarsening 的州数

4. 是否存在 estimation-unit-level true block

5. TI fold-specific design：

   * 是否全国闭合

6. MA sensitivity：

   * 完整 / 部分 / 不可用州数

7. WV 状态

8. OR 4 mismatch 状态

然后：

> STOP

等待聊天主线审计。

不要继续 D08C2、TREE、abundance、occupancy 或 Q1。

本合同版本：

> **Q1_D09C_T2_BOUNDED_COMPLETION_CONTRACT_v01**

Science decisions frozen by mainline before Work execution.
