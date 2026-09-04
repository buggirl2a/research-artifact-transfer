# Q1 / D10A — Real-layout Non-oracle Observation Calibration v01

TASK_ID:

`D10A_REAL_LAYOUT_NONORACLE_OBSERVATION_CALIBRATION_v01`

状态：

**FROZEN BEFORE SYNTHETIC CALIBRATION（在合成校准结果产生前冻结）**

## 1. 科学目的

本任务不运行真实 Q1。

本任务只回答：

> 在真实 FIA 48 州 F0 抽样布局下，如果不知道真实的检出/遭遇过程参数，能否仅凭合法调查机会、样地遭遇历史、调查努力量和空间结构，恢复一个不过度收缩的 latent occupied support（潜在占据支持域），同时避免 abundance-dependent encounter（多度依赖的遭遇过程）制造虚假的 support–abundance（支持域—多度）关系？

这是历史 E2c.1 的正式继续。

---

## 2. 禁止读取的真实结果

本任务禁止使用：

* 93 个 D08C2 主分析候选物种的真实 TREE.SPCD 值；
* 真实 species encounter counts（物种遭遇次数）；
* 真实 species abundance（物种多度）；
* 真实 support（真实支持域）；
* 真实 Q1 outcome（真实 Q1 结果）。

不得根据真实 93-species results（93 个物种结果）选择模型或调参数。

---

## 3. 可以使用的真实 FIA 信息

只允许使用 species-blind sampling layout（不含物种结果的真实抽样布局）：

* frozen F0 plot membership（冻结 F0 样地成员）；
* final A/B whole-panel assignment（最终 A/B 整面板分配）；
* public FIA coordinates（公开 FIA 坐标）；
* sampled / nonsampled plot status（已调查/未调查样地状态）；
* accessible forest condition（可调查森林条件）；
* sampled subplot information（已调查子样方信息）；
* partial-sampling effort metadata（部分调查努力量元数据）；
* `PLOT.MANUAL`（FIA 野外调查手册版本）；
* `PLOT.DESIGNCD`（样地设计代码）。

不得读取 TREE.SPCD。

---

## 4. 规范空间格网

Primary grain（主空间粒度）：

**50 km**

使用已经结果前冻结的 D04 continuity authority（D04 连续性权威）：

* NAD83 / CONUS Albers equal-area（NAD83 / 美国本土阿尔伯斯等面积投影）；
* EPSG:5070；
* fixed origin（固定原点） `(0,0)`；
* `ix = floor(x / 50000)`；
* `iy = floor(y / 50000)`；
* cell ID（格网编号）：
  `50km_<ix>_<iy>`。

不得重新选择原点、投影或格网。

25/75 km 暂不参与本轮模型选择。

---

## 5. 如果 Work 无法直接读取 C:\range_paper

不得重新下载 FIA。

正确模式：

1. 生成 deterministic local extractor（确定性本地抽取器）；
2. 用户在本地机械运行；
3. 只生成 compact species-blind layout（紧凑的不含物种结果的抽样布局）；
4. 经 Research Artifact Relay（研究产物中转）返回 Work；
5. Work 再执行合成校准。

抽取文件至少包含：

* plot CN；
* state；
* fold A/B；
* public coordinates（公开坐标）；
* 50-km cell ID；
* PLOT_STATUS；
* sampled subplot count（已调查子样方数量）；
* partial-sampling effort（部分调查努力量）；
* MANUAL；
* DESIGNCD；
* base legitimate opportunity flag（基础合法调查机会标记）。

不得包含 SPCD、真实物种名或真实 TREE outcome（TREE 结果）。

---

## 6. 合成世界

在真实 FIA sampling layout（抽样布局）上生成 fresh synthetic species（全新合成物种）和 fresh seeds（全新随机种子）。

至少保留两种生态世界：

### STRONG WORLD（强信号世界）

occupied-support geometry（占据支持域几何）真正约束 abundance allocation（多度配置）。

### PAIRED-NULL WORLD（配对空世界）

support（支持域）与 abundance（多度）保留相同机械约束和一般空间结构，但不存在 species-specific support-geometry ↔ abundance-arrangement correspondence（物种特异的支持域几何—多度配置对应关系）。

必须与历史 E2b/E2c 的科学含义连续。

---

## 7. 观测过程压力情景

拟合模型不得获得生成器真实参数。

至少生成三类 observation regimes（观测情景）：

### O1 — abundance-dependent encounter（多度依赖遭遇）

局部种群质量越高，被有限 FIA 样地碰到的概率越高。

### O2 — heterogeneous within-cell availability（格子内部可利用/占据比例异质）

即使 50-km cell（50 千米格子）真实占据，物种也可能只覆盖其中部分森林空间。

### O3 — survey/manual heterogeneity（调查手册/调查制度异质）

使 encounter probability（遭遇概率）存在与真实 `PLOT.MANUAL` 分布相对应的观测异质性。

生成参数只允许用于模拟和事后 truth-based evaluation（真值评估），禁止输入拟合模型。

---

## 8. 模型候选

只比较最低复杂度的三层。

### M0 — hard-detection baseline（硬检出基线）

某格至少一个 positive encounter（正遭遇）即 observed occupied（观测占据）。

仅作失败基准，不作为预设赢家。

### M1 — hierarchical zero-inflated beta-binomial encounter model

（分层零膨胀 Beta-Binomial 遭遇模型）

对 species i、cell x、fold f：

* latent Z = 潜在占据状态；
* N = 合法 FIA 空间子样本数量；
* K = 发生正遭遇的子样本数量；
* 若 Z=0，则 K=0；
* 若 Z=1，则 K 由一个允许 cell-to-cell / species-to-species encounter heterogeneity（格子间/物种间遭遇异质性）的 Beta-Binomial 分布生成。

所有遭遇参数必须从观测数据估计/部分汇聚，不得使用合成生成器参数。

可以使用：

* N / sampling effort（抽样努力量）；
* MANUAL（调查手册版本）；
* partial-sampling information（部分调查信息）。

不得使用 opposite-fold abundance（另一折多度）。

### M2 — M1 + spatial regularization

（M1 + 空间正则化）

在 M1 基础上，对相邻 50-km cells（50 千米格子）的 latent occupancy probability（潜在占据概率）加入最简单、透明的空间平滑/图正则化。

不得加入：

* climate（气候）；
* terrain（地形）；
* Little atlas（Little 图谱）；
* GBIF；
* TreeMap；
* 真实 abundance（真实多度）。

---

## 9. 输出必须是 support uncertainty（支持域不确定性）

M1/M2 不得只输出一张 hard binary map（硬二元地图）。

必须输出：

* posterior occupancy probability（后验占据概率）；
* plausible support ensemble（合理支持域集合）或等价的不确定性表示；
* expected support size（期望支持域大小）；
* uncertainty diagnostics（不确定性诊断）。

不得把 posterior encounter probability（后验遭遇概率）直接作为 abundance predictor（多度预测变量）。

---

## 10. 评价

本轮是 synthetic method calibration（合成方法校准），不是正式真实数据 Gate。

允许使用 synthetic latent truth（合成潜在真值）评价模型。

必须报告：

### Support quality（支持域质量）

* Brier score（布里尔评分）；
* log score / log loss（对数评分 / 对数损失）；
* calibration（概率校准）；
* expected support-size bias（期望支持域大小偏差）；
* occupied-cell recall（真实占据格子召回率）；
* precision（精确率）；
* IoU / Jaccard（交并比 / 杰卡德指数）。

### Leakage control（泄漏控制）

继续使用历史 E2c 的 paired-null downstream audit（配对空世界下游审计）。

两种方向：

* AB；
* BA。

继续报告：

* latent-truth geometry gain（潜在真值几何收益）；
* predictive-set gain（预测集合收益）；
* coverage（覆盖率）。

### Strong-signal preservation（强信号保留）

检查观测校正是否在消除虚假关系的同时保留真正的 support–abundance signal（支持域—多度信号）。

---

## 11. 本轮不事后选择阈值

本轮属于 method-development calibration（方法开发校准）。

Work 不得自行宣布最终 observation model（观测模型）。

必须返回 M0/M1/M2 全部结果。

Mainline 将依据 synthetic-only evidence（仅合成证据）选择最终模型，并在读取真实 93 个物种 support（支持域）之前冻结正式 observation/recoverability contract（观测/可恢复性合同）。

---

## 12. 既有 E2c benchmark（E2c 基准）

历史 E2c reproducible package（可复现包）身份：

`E2C_LATENT_OCCUPANCY_DETECTION_v0_1_20260831_REPRODUCIBLE.zip`

SHA-256：

`76a38f98e8d76c60f0b0c173ac34ac999b311949b683b68c6e69461ae01d3af4`

它只作为 benchmark（基准）。

不得复制其 generator-informed observation parameters（生成器已知观测参数）进入 M1/M2 拟合。

---

## 13. 已知 protocol limitation（调查协议局限）

D08C2 protocol-risk audit（调查协议风险审计）已经冻结：

101 strict species（101 个严格物种）与 56 known-affected FIA codes（56 个已知受影响 FIA 代码）交集 = 0。

这不等于证明 protocol invariance（调查协议永远不变）。

本轮 species-blind calibration（不含真实物种的校准）只需：

* 保留 MANUAL；
* 不模拟“所有历史协议绝对一致”的假设；
* 将 manual-associated heterogeneity（手册相关观测异质性）纳入 O3 压力情景。

不得继续恢复 exact NFS region（精确美国国家森林系统区域）。

---

## 14. Required outputs（必需输出）

至少返回：

1. `Q1_D10A_REAL_F0_OPPORTUNITY_LAYOUT_v01.csv`
2. `Q1_D10A_SYNTHETIC_WORLD_MANIFEST_v01.csv`
3. `Q1_D10A_MODEL_SPECIFICATIONS_v01.md`
4. `Q1_D10A_SUPPORT_CALIBRATION_RESULTS_v01.csv`
5. `Q1_D10A_LEAKAGE_AUDIT_RESULTS_v01.csv`
6. `Q1_D10A_MODEL_COMPARISON_v01.csv`
7. `Q1_D10A_RESULT_NOTE_v01.md`
8. complete reproducibility code（完整可复现代码）
9. `SHA256SUMS.csv`
10. Relay v0.2.2 `TRANSFER_MANIFEST_v01.csv`
11. `REGISTRY_DELTA_v01.csv`

如果 plot-level layout（样地级布局）过大，Relay 可传压缩版本；不得重新下载 raw FIA。

---

## 15. Terminal statuses（允许终态）

只允许：

`CALIBRATION_COMPLETE_READY_FOR_MAINLINE_MODEL_FREEZE`
（校准完成，可返回主线冻结正式观测模型）

`INPUT_BLOCKED_LAYOUT_AUTHORITY_FAILURE`
（抽样布局权威输入阻断）

`IMPLEMENTATION_BLOCKED`
（实现阻断）

本轮没有 scientific PASS/FAIL（科学通过/失败）终态。

模型优劣由主线在完整 synthetic calibration（合成校准）返回后判断。

---

## 16. Absolute STOP（绝对停止边界）

不得继续：

* 真实 93-species support estimation（93 个真实物种支持域估计）；
* abundance estimation（多度估计）；
* final cohort（最终物种队列）；
* R1/R2 real analysis（R1/R2 真实分析）；
* World 0 real Q1（World 0 真实 Q1）；
* publication result（论文结果）。

返回主线。

END
