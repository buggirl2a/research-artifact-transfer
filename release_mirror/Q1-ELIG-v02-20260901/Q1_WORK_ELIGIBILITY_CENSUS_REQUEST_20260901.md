# Q1 WORK REQUEST — OUTCOME-BLIND ELIGIBILITY CENSUS
## 结果盲真实数据资格普查

**版本：v0.1**  
**日期：2026-09-01**  
**角色：bounded computational branch（有边界计算分支）**

---

# 0. 当前科学状态

Q1 scientific mainline（Q1 科学主线）已经接受 D07 raw acquisition（原始数据获取）完成。

当前权威 raw snapshot（原始数据快照）为：

- `C:\range_paper\00_control\RAW_FREEZE_v02.md`
- `C:\range_paper\00_control\raw_manifest_v02.csv`
- `C:\range_paper\00_control\sha256_raw_v02.txt`

正式 raw 包括：

1. FIA Entire FIADB SQLite Database，版本参考 `FIADB_1.9.4.00`；
2. USGS/Little CSV bundle；
3. USGS/Little NetCDF bundle。

`RAW_FREEZE_v01.md` 及其 manifest/hash 仅为历史 checkpoint，不得作为当前输入。

**真实物种 Q1 效果分析继续 HOLD。**

本任务不是正式 Q1，不估计 range–abundance coupling（分布区—多度耦合），不比较 R1/R2 的真实效果，不计算 geometry gain（几何收益），不选择最漂亮的 grain（空间粒度）。

---

# 1. 本任务唯一目的

> 在完全不知道真实 Q1 结果的条件下，使用已经冻结的全国 FIA + USGS/Little 原始数据，回答：不同空间粒度、不同抽样信息量和不同分布完整性条件下，现实究竟有多少物种具备进入正式 Q1 的数据资格？

本任务的产物不是最终论文物种清单。

产物应是：

> **species-level continuous eligibility metrics（物种级连续资格指标） + threshold frontiers（阈值前沿） + data-quality flags（数据质量标记）**。

最终纳入/排除规则由 scientific mainline 在看到本次资格普查后冻结，并且必须在任何真实 Q1 效果分析之前完成。

---

# 2. 运行前必须完成的输入审计

## 2.1 Raw integrity

只读核验：

- v02 manifest；
- 三个正式 raw 文件的 size；
- 三个正式 raw 文件的 SHA-256。

必须与 `RAW_FREEZE_v02.md` 完全一致。

不得修改、重打包、覆盖 `02_raw` 中任何正式 raw 文件。

若 hash/size 不一致：

> **STOP — INPUT FAILURE**

不要继续资格普查。

## 2.2 Frozen documentation

使用 `C:\range_paper\03_doc` 中已经冻结的 FIA / USGS 官方说明、数据字典、field guide（字段指南）、sampling/estimation documentation（抽样/估计文档）。

不得因为方便而依赖未经冻结的网络二手说明替代官方定义。

## 2.3 Prior grid/split continuity

优先读取项目中已有 D04/E1/E2 使用的：

- 25 km grid definition（25 千米格网定义）；
- 50 km / 75 km aggregation rule（50/75 千米聚合规则）；
- A/B fold convention（A/B 数据折规则）。

如果相关冻结定义在本地项目中找不到：

> STOP，报告缺失文件/定义。

不得自行发明新的 grid origin（格网原点）、projection（投影）或 fold 规则。

---

# 3. 目录治理

项目根目录：

`C:\range_paper`

本任务推荐短路径：

- 工作输出：`C:\range_paper\05_qc\elig_v01`
- 可复现源码：`C:\range_paper\06_src\elig_v01`
- 最终冻结包：`C:\range_paper\10_archive\elig_v01`
- 临时缓存：`C:\range_paper\99_tmp\elig_v01`

不要建立深层嵌套目录；单个自建文件名尽量简短。

`02_raw` 永远只读。

---

# 4. 冻结的候选生态状态

本次资格普查继续使用当前主线候选状态：

- primary time window（主要时间窗口）：`MEASYEAR 2017–2023`；
- primary life/size state（主要生命/大小状态）：live trees（活立木）且 `DIA >= 5 in`，作为 **large/established-tree state（较大/已建立树木状态）** 的当前操作候选。

但 Work 必须通过官方 FIA 文档审计并标记：

- woodland / DRC / regional protocol differences（林地/特殊直径规则/区域协议差异）；
- 任何使 `DIA >= 5 in` 在不同 taxa（类群）或 sampling domains（抽样域）之间不可直接比较的协议例外。

本任务不得擅自改成 seedlings（幼苗）、saplings（幼树）或 all stems（全部树木）。

如果发现候选状态存在必须由主线决定的结构性不一致：

> 标记并继续可做的 descriptive census（描述性普查）；不得自行改 scientific object（科学对象）。

---

# 5. Candidate geographic domain（候选地理域）

不得因为数据库里有全部州就自动把所有区域混为一个分析域。

Work 应：

1. 报告 FIA frozen raw 中可用的州/区域范围；
2. 报告 USGS/Little gridded product 的实际空间范围；
3. 建立二者空间交集和边界信息；
4. 按既有主线大陆美国候选架构输出主要 census；
5. Alaska / Hawaii / territories（阿拉斯加/夏威夷/属地）若不属于既有 grid/atlas 支持范围，应独立标记，不得静默并入或删除。

本任务不冻结最终论文 geographic extent（地理范围）。

---

# 6. Species universe audit（候选物种全集审计）

建立所有 FIA candidate taxa（候选类群）的结果盲基础表。

至少区分：

- accepted species-level record（可接受的物种级记录）；
- genus-level aggregate（属级汇总）；
- unknown / unidentified tree（未知/未定树）；
- native / introduced / uncertain（原生/外来/不确定，若冻结官方字段支持）；
- USGS/Little exact match（精确匹配）；
- USGS official accepted↔original name reconciliation（USGS 官方接受名—原图名对应）；
- unresolved taxonomy（未闭合分类学）。

不要为了提高物种数做 fuzzy matching（模糊名称匹配）。

不得使用 Q1 结果决定分类处理。

---

# 7. Grain census（空间粒度普查）

固定比较三条候选 grain：

- 25 km；
- 50 km；
- 75 km。

保持与 D04/E1/E2 完全相同的格网定义和聚合关系。

对每个 species × grain，输出连续指标，不先设唯一“合格阈值”。

至少包括：

### Sampling information（抽样信息）

- total eligible plots（总合格样地数）；
- plots per cell distribution（每格样地数分布）；
- median / quartiles / lower-tail plots per cell（每格样地数中位数、四分位数、下尾）；
- forest-domain coverage information（森林抽样域覆盖信息）。

### Observed species information（物种观测信息）

- qualifying tree records（满足候选状态的单木记录数）；
- plots with species（检出该物种的样地数）；
- hard-detected cells（至少一个样地检出的格子数）；
- observations per detected cell（每个检出格子的观测冗余）；
- fraction of detected cells represented by only one positive plot（仅一个阳性样地支撑的格子比例）。

不得把 hard-detected cells 直接称为真实 support（真实支持域）。

---

# 8. A/B split feasibility（A/B 数据折可行性）

严格使用既有冻结 A/B split convention（A/B 数据折规则）。

对每个 species × grain 报告：

- A / B eligible plot counts（A/B 合格样地数）；
- A / B positive plot counts（A/B 阳性样地数）；
- A / B hard-detected cells（A/B 检出格子数）；
- cells detected by both folds（两折共同检出格子）；
- cells detected only by A / only by B（仅一折检出格子）；
- A/B hard-support IoU or equivalent overlap（A/B 硬检出支持域重叠度或同等指标）；
- detection redundancy in each fold（两折检出冗余）。

这些只是 **support estimability diagnostics（支持域可估计性诊断）**。

不得据此拟合正式 latent occupancy model（潜在占据模型）。

---

# 9. Abundance estimability diagnostics（多度可估计性诊断）

本任务不生成正式 species abundance surfaces（物种多度表面）。

只需要回答：另一折数据是否有足够信息支持未来 population-mass allocation（种群质量空间配置）估计。

至少报告：

- qualifying trees per species / fold / grain（每物种/数据折/粒度的合格单木数）；
- positive plots per fold（每折阳性样地数）；
- detected cells with ≥1 / ≥2 / ≥3 positive plots（有至少 1/2/3 个阳性样地的检出格子数）；
- design/expansion-weight availability（正式抽样权重/扩展因子是否可获得并适用于候选状态）；
- obvious variance-support failures（明显无法估计抽样不确定性的情况）。

允许做为了资格审计所需的 sampling-variance metadata diagnostics（抽样方差元数据诊断）；

不得计算 geometry-conditioned abundance prediction（几何条件多度预测）。

---

# 10. Range completeness & truncation audit（分布完整性与截断审计）

## 10.1 USGS/Little match

对所有可闭合物种输出：

- USGS/Little mapped cells total（图谱总格子数）；
- US cells；
- Canada cells；
- US share of US+Canada mapped range（美国占美国+加拿大图谱范围比例）；
- Canada extension flag（加拿大延伸标记）。

保留 D06 的 70 / 80 / 90 / 95% summary thresholds（汇总阈值），但不得选择最终 threshold（阈值）。

## 10.2 Geometry clipping diagnostics（几何截断诊断）

因为 Q1 研究 geometry（几何），仅面积比例不够。

在 USGS/Little 支持的 US+Canada domain 内，比较：

- full CANUSA atlas geometry（美国+加拿大完整图谱几何）；
- US-clipped atlas geometry（只保留美国部分的截断几何）。

至少给出一组低复杂度、结果盲的 clipping diagnostics（截断诊断）：

- occupied-area fraction retained（保留占据面积比例）；
- component-count change（连通块数量变化）；
- largest-component fraction change（最大连通块比例变化）；
- geographic diameter / major-span change（地理直径/主要跨度变化）；
- one additional stable geometry distortion summary if already available from frozen R1/R2 infrastructure（如果冻结的 R1/R2 工具已有稳定几何差异摘要，可增加一项；不得为本任务发明新算法）。

不得用这些量与 abundance（多度）做关联。

## 10.3 Mexico / global truncation

USGS/Little CANUSA 产品不能闭合 Mexico（墨西哥）或跨大陆全球分布。

因此必须输出：

- Mexico/global-range status = known / suspected / unknown（已知/疑似/未知，只基于冻结数据和官方 metadata）；
- list of taxa requiring future external global-range review（未来需要外部全球分布审计的物种列表）。

不得联网自行完成新的全球分布数据库搜索。

这张列表返回主线后，若确有必要，主线再向数据搜索线发一个极窄的 global-range audit request（全球分布审计请求）。

---

# 11. Threshold frontier（阈值前沿）

本任务不允许输出“最佳阈值”。

应输出连续 species-level metrics（物种级连续指标），并额外生成若干预先指定的 descriptive frontiers（描述性前沿），帮助主线结果盲冻结最终规则。

至少包括：

### Hard-detected cells per fold（每折检出格子数）

候选门槛：

- ≥5
- ≥10
- ≥15
- ≥20
- ≥30
- ≥40

### Positive plots per fold（每折阳性样地数）

候选门槛：

- ≥10
- ≥20
- ≥30
- ≥50
- ≥100

### US share of US+Canada atlas range（美国占美加图谱范围比例）

- ≥70%
- ≥80%
- ≥90%
- ≥95%

报告在 25 / 50 / 75 km 下，分别还能保留多少 species（物种）。

若组合门槛产生过大的笛卡尔积，不需要穷举全部组合；以 species-level metrics table（物种级指标表）为权威，附少量有解释意义的二维/三维 frontier summaries（前沿汇总）即可。

---

# 12. Geometry-information diagnostics（几何信息量诊断）

本任务需要判断一个物种在某粒度下是否还保留足够二维空间结构，但不能使用真实 Q1 效果。

允许的结果盲指标包括：

- number of occupied/detected cells（检出格子数）；
- number of connected components（连通块数）；
- bounding-box / convex-hull span（包围盒/凸包跨度）；
- low-complexity support shape diagnostics already frozen in prior infrastructure（此前已冻结的低复杂度支持域形态诊断）。

如果已有 D04 的 recoverability frontier（可恢复性前沿）可直接映射到这些指标，优先复用。

不得使用 abundance arrangement（多度排列）判断“几何够不够好”。

---

# 13. 绝对禁止事项

本任务不得：

- 拟合真实 Q1 geometry→abundance model（几何→多度模型）；
- 计算真实 geometry gain（几何收益）；
- 比较 R1 vs R2 谁在真实数据中效果好；
- 计算真实 predictive-set shrinkage（预测集合缩小）；
- 根据显著性/效应大小筛物种；
- 根据哪个 grain 的 Q1 结果漂亮选择 grain；
- 修改 World 0（零世界）；
- 进入 Q1c/Q1d；
- 下载新的外部数据库；
- 修改 `02_raw`；
- 将 USGS/Little 当作 current S*（当前真实支持域）；
- 将 hard detection（硬检出）当作 latent support truth（潜在支持域真值）。

任何需要上述行为才能继续的问题：

> STOP → 报告主线。

---

# 14. 结果交付

至少生成：

1. `INPUT_AUDIT.md`
2. `species_metrics.csv`  
   每物种 × grain 的连续资格指标，核心权威表。
3. `taxonomy_crosswalk.csv`
4. `fold_metrics.csv`
5. `range_clipping.csv`
6. `threshold_frontier.csv`
7. `protocol_flags.csv`
8. `global_range_review_queue.csv`
9. `grain_summary.csv`
10. `CENSUS_NOTE.md`
11. `IMPLEMENTATION_LOG.md`
12. `PACKAGE_MANIFEST_SHA256.csv`
13. 可复现实验源码与参数文件
14. 必要的结果盲诊断图
15. `Q1_ELIGIBILITY_CENSUS_v0_1_REPRODUCIBLE.zip`

最终 ZIP 放入：

`C:\range_paper\10_archive\elig_v01`

源码放入：

`C:\range_paper\06_src\elig_v01`

结果表放入：

`C:\range_paper\05_qc\elig_v01`

---

# 15. Work 返回主线时的聊天格式

只报告：

1. engineering PASS / FAIL（工程是否完成）；
2. raw snapshot hash audit（原始快照哈希审计）；
3. 25 / 50 / 75 km 下 candidate species breadth（候选物种规模）；
4. A/B fold information frontier（A/B 数据折信息前沿）；
5. USGS/Little range-completeness frontier（分布完整性前沿）；
6. 主要 protocol/taxonomy/global-range flags（协议/分类/全球分布标记）；
7. 哪些事实仍需主线决策；
8. reproducible ZIP path/link；
9. STOP。

**不得在聊天中推荐最终 grain、最终物种阈值或最终论文物种清单。**

---

# 16. 本任务的科学定位

这是：

> **正式研究设计冻结前的结果盲数据可行性与分析队列审计。**

它不是论文生态结果。

未来论文 Methods（方法）中会写入的是：

- 主线在本次普查后冻结的最终纳入/排除标准；
- 最终 spatial grain（空间粒度）；
- 最终 analytic cohort construction（分析队列构建）。

而不是把本次所有阈值探索过程原样写进正文。

---

# 17. 一句话任务

> **不要回答“哪些物种的 Q1 效果最好”；只回答“在完全不知道 Q1 答案的前提下，现实数据允许我们诚实研究哪些物种、在哪些空间粒度上研究，以及不同资格标准会付出多少样本量与几何信息代价”。**
