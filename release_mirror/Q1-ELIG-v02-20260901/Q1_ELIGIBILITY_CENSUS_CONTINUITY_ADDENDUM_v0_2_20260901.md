# Q1 ELIGIBILITY CENSUS — CONTINUITY ADDENDUM v0.2
## 结果盲资格普查：D04 连续性补充与主线冻结决策

日期：2026-09-01  
地位：与 `Q1_WORK_ELIGIBILITY_CENSUS_REQUEST_20260901.md` 联合使用；本文件仅修正/补齐 pre-run STOP 暴露的执行歧义。  
原则：尚未产生任何资格普查结果，因此这些修正均为 **pre-result scientific/engineering freeze**，不是看到结果后的调参。

---

## 0. Pre-run STOP 的分类

Work 返回的停止属于 **engineering/configuration failure（工程/配置失败）**，不是 scientific/inference failure（科学/推断失败）。

原始快照完整性已经 PASS；资格普查尚未启动；真实 Q1 继续 HOLD。

---

## 1. D04 权威连续性已恢复

主线已从项目历史文件中恢复原始 `D04_extract_FIA_pilot.py`。资格普查必须把该原始 D04 源码作为 grid/split provenance（格网/分折溯源）文件归档，不得凭摘要重新发明规则。

### 1.1 投影

D04 使用 NAD83 / CONUS Albers equal-area（EPSG:5070）椭球 Albers 正算；关键参数：

- semi-major axis = 6378137.0 m
- inverse flattening = 298.257222101
- standard parallel 1 = 29.5°
- standard parallel 2 = 45.5°
- latitude of origin = 23.0°
- central meridian = -96.0°
- false easting = 0 m
- false northing = 0 m

输入为 FIADB public longitude/latitude；不反推 confidential coordinates（保密坐标）。

### 1.2 固定格网与 cell ID

对 grain `g`（25/50/75 km）：

- `g_m = g * 1000`
- `ix = floor(x / g_m)`
- `iy = floor(y / g_m)`
- cell ID = `<g>km_<ix>_<iy>`

三个 grain 共用 EPSG:5070 原点 `(0,0)`，不得按州界、数据范围或本次全国样本重新平移原点。

50 km / 75 km 可视为同一 25-km 原点体系上的 2×2 / 3×3 嵌套粗化；执行时允许像 D04 一样从投影坐标直接计算各 grain cell ID，二者数学上必须一致。

### 1.3 D04 A/B split（原始可行性规则）

原 D04 规则：

- 只对 eligible forest plots（合格森林样地）分折；
- grouping（分组）=`source_state × P2PANEL`；缺失 `P2PANEL` 记为字面量 `NA`；
- seed=`D04_FIA_GEOMETRY_RECOVERABILITY_V1`；
- 对每个 plot measurement CN（样地测量记录 CN）计算 SHA-256 of `seed + "|" + CN`；
- 组内按 `(digest, CN)` 升序；
- 依次交替 A、B、A、B…；
- 同一个 plot measurement 不得进入两折。

D04 自身明确标注该 split 为 **feasibility-only（仅可行性用途）**，不是最终正式 cross-fitting（交叉拟合）设计。

---

## 2. 本次全国资格普查对重复测量的主线冻结

D06 已证明 FIA permanent-plot revisits（永久样地复访）典型间隔约 5–7 年，因此不能把同一物理样地的多次 measurement 当作同一生态状态下的独立 repeated detections（重复检出）。

为避免资格普查虚增空间样本量，本次 primary census（主要普查）冻结为：

> **每个 physical plot lineage（物理样地纵向谱系）在 MEASYEAR 2017–2023 内最多贡献一个 primary measurement。**

### 2.1 lineage 定义

优先使用 `PLOT.CN ↔ PREV_PLT_CN` 链接恢复物理样地 lineage。

### 2.2 primary measurement 选择

在同一 lineage 的所有 eligible 2017–2023 measurements 中：

1. 优先选择该窗口内唯一 terminal/latest measurement（终端/最新测量）；
2. 排序优先级：`MEASYEAR` → `MEASMON` → `MEASDAY` → `INVYR` → `CN`；均取最大/最新；
3. 若 PREV 链出现分叉、循环、多个不可唯一解释 terminal 等异常，不得静默猜测：标记 `lineage_ambiguous=1`，从 primary census 排除，并单独报告数量。

历史/前次 measurement 仍可保留为 longitudinal/dynamic diagnostics（纵向/动态诊断），但不作为 primary independent plot units（主要独立样地单元）重复计数。

### 2.3 A/B split continuity after de-duplication

在完成上述 one-measurement-per-lineage（每谱系单次测量）后，继续使用 **D04 原始 A/B hash/alternation rule**，hash 输入为最终保留的 measurement `CN`。

这样既保持 D04 分折连续性，又保证同一物理样地在 primary census 中不会因多时点重复而跨折或重复计权。

同时输出一个 sensitivity-only（仅敏感性）计数：若不去重、把全部 2017–2023 eligible measurements 都计入，样本量增加多少。不得把该敏感性版本用于正式 eligibility threshold（资格阈值）推荐。

---

## 3. Candidate geographic domain（候选地理域）冻结

本次全国 eligibility census 的 **primary candidate domain（主要候选域）** 定义为：

> **conterminous United States（美国本土相连的 48 州）+ District of Columbia（哥伦比亚特区，如 FIADB 中存在合格记录）。**

明确：

- Alaska（阿拉斯加）排除出 primary census，单独报告；
- Hawaii（夏威夷）排除出 primary census，单独报告；
- Puerto Rico（波多黎各）及其他 territories（属地）排除出 primary census，单独报告；
- 本定义只是资格普查的候选分析域，不等于最终论文 extent（研究范围）已经冻结。

理由：当前 USGS/Little CANUSA representation（美加图谱表征）、D04 的 EPSG:5070 体系与第一篇 FIA 主架构均围绕美国本土相连区域建立。

---

## 4. USGS/Little representation（表征）冻结

### 4.1 Primary representation

资格普查、taxonomy crosswalk（分类名称对照）、US-vs-Canada range completeness（范围完整度）和 clipping diagnostics（截断诊断）的 **primary USGS representation** 采用：

> **D07 冻结的官方 USGS CSV bundle（CSV 数据包）。**

理由：D06 的 27,984 equal-area grid（等面积格网）、690 species matrix（物种矩阵）和 accepted↔original nomenclatural closure（接受名↔原图名闭合）已经在 CSV representation 上完成事实核验。

### 4.2 NetCDF role

D07 冻结的 NetCDF bundle（NetCDF 数据包）保留为：

> **independent file-format/semantic verification representation（独立文件格式/语义核验表征）**。

Work 在运行 clipping census 前，应做一次 CSV↔NetCDF semantic equivalence audit（语义等价审计）：

- grid dimensions / coordinates（格网维度/坐标）；
- species/taxon identifiers（物种/类群标识）；
- presence–absence values（出现–缺失值）。

文件很小，若可行应做全量语义一致性核验。

若二者对同一 taxon/grid 的 presence–absence 发生无法由 metadata（元数据）解释的差异：

> **STOP → MAINLINE**

不得平均、合并或自行选择“更好看”的 representation。

通过等价审计后，后续资格普查以 CSV 为权威计算输入，NetCDF 不重复计算同一科学指标。

---

## 5. Sampling-frame denominator（抽样框分母）连续性

FIA grain census（粒度普查）沿用 D04 原则：

> `cell with eligible plot` 表示在 primary candidate domain 内，至少含一个最终 primary eligible FIA plot measurement 的固定格网 cell。

不得把没有任何 FIA 样地代表的政治边界格子自动视作“调查过的零值格子”。

USGS atlas geometry 的 cell universe（格子全集）则使用官方 USGS grid，自成一个外部 representation domain；不得与 FIA sampling-frame denominator 偷换。

---

## 6. 本次普查仍然不得决定的事项

本补充没有冻结：

- 最终论文 grain（空间粒度）；
- 最终 eligibility threshold（资格阈值）；
- 最终 species list（物种清单）；
- 最终 whole-range completeness threshold（完整分布阈值）；
- 正式 latent support model（潜在支持域模型）；
- 正式 abundance model（多度模型）；
- R1/R2 主次；
- World 0 的真实数据具体实现。

以上均由 scientific mainline 在 eligibility census 返回后、任何真实 Q1 效果分析之前冻结。

---

## 7. Work 恢复执行

Work 应使用：

1. `Q1_WORK_ELIGIBILITY_CENSUS_REQUEST_20260901.md`；
2. 本 `Q1_ELIGIBILITY_CENSUS_CONTINUITY_ADDENDUM_v0_2_20260901.md`；
3. 原始 `D04_extract_FIA_pilot.py`（仅作 grid/split provenance）；
4. `RAW_FREEZE_v02` 权威原始快照。

重新从 pre-run input audit 开始执行同一个 outcome-blind eligibility census（结果盲资格普查）。

之前的 `elig_v01` 工程 FAIL 包必须保留，不覆盖、不删除；新一轮建议写入 `elig_v02` 短路径目录。

若除本文件已经补齐的事项外又出现新的 scientific ambiguity（科学歧义），继续 STOP 回主线，不得自行发明。

真实 Q1 继续 HOLD。
