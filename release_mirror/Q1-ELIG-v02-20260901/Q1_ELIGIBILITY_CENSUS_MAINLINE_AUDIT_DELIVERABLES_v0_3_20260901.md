# Q1 Eligibility Census — Mainline Audit Deliverables Addendum
## Q1 资格普查——主线独立审核交付要求（v0.3）

日期：2026-09-01  
性质：对现有 outcome-blind eligibility census（结果盲资格普查）的**交付要求追加**。  
不改变科学对象、不改变格网/分折规则、不改变资格普查本身；只规定 Work（工作模式）必须返回哪些可由主线独立审核的结果。

---

# 0. 核心原则

Work（工作模式）不能只返回：
- “PASS（通过）”；
- 最终物种数；
- 一段文字总结。

主线必须能够独立检查：
1. 原始输入是否真的是冻结的 RAW_FREEZE_v02；
2. 格网与 A/B 分折是否按冻结规则执行；
3. 同一 physical plot lineage（物理样地纵向谱系）是否没有被重复当作独立空间样本；
4. 每个物种在 25/50/75 km 下到底有多少有效样地、检出样地、格子和 A/B 信息；
5. USGS/Little 外部分布完整度和美国边界 clipping（截断）到底怎样；
6. 资格阈值变化时，候选物种数怎样变化；
7. 是否完全没有计算任何真实 Q1 outcome（Q1 结果）指标。

本轮 Work **不得替主线生成“最终正式论文物种清单”**。  
Work 只生成 census（普查）、frontier（前沿）和 objective flags（客观标记）。最终纳入/排除规则由主线在结果盲条件下冻结。

---

# 1. 必须返回的主线审核文件

## A. `INPUT_AUDIT.csv`
至少包含：
- file_role（文件角色）
- path（路径）
- size_bytes（字节大小）
- sha256（SHA-256 哈希）
- expected_size（冻结大小）
- expected_sha256（冻结哈希）
- status（PASS/FAIL）

必须覆盖：
- FIA 正式 raw（原始）文件；
- USGS CSV 正式 raw 文件；
- USGS NetCDF 正式 raw 文件；
- RAW_FREEZE_v02 及其 manifest（清单）/hash（哈希）文件；
- 本轮实际使用的 D04 grid/split（格网/分折）权威实现或冻结参数文件。

---

## B. `DOMAIN_GRID_AUDIT.csv`
按 grain（空间粒度）25/50/75 km 各一行或多行，至少报告：
- projection（投影；应为冻结 EPSG:5070）
- origin_x / origin_y（固定格网原点）
- grain_km（粒度）
- n_cells_total（候选分析域总格子数）
- n_cells_with_eligible_plots（存在合格 FIA 样地的格子数）
- n_unique_physical_plot_lineages（唯一物理样地纵向谱系数）
- n_primary_measurements（去重后主测量数）
- parent_mapping_check（25→50、25→75 嵌套/映射检查）
- boundary/domain mask（边界/分析域说明）
- status

必须明确：
- 25/50/75 km 使用同一冻结原点；
- 50/75 km 没有按全国数据重新居中；
- 同一物理样地在 2017–2023 主普查中最多贡献一次 primary measurement（主测量）。

---

## C. `AB_SPLIT_AUDIT.csv`
必须允许主线独立检查 A/B fold（A/B 数据折）是否正确。

至少报告：
- stratum（分层；如 state × P2PANEL）
- n_lineages_total
- n_A
- n_B
- abs_balance_diff
- missing_P2PANEL_count
- duplicate_lineage_across_AB（必须为 0）
- duplicate_primary_measurement（必须为 0）
- split_seed / split_rule_id（冻结种子/规则标识）
- status

另输出一张总体 summary（汇总）：
- A/B 总样地数；
- A/B 各州数量；
- A/B 各 panel（面板）数量；
- A/B 平衡度分布。

---

## D. `SPECIES_GRAIN_CENSUS.csv` —— **最重要的主线审核表**

一行必须对应：

> species × grain

即每个物种在 25、50、75 km 各有一行。

至少包含：

### 分类与身份
- fia_species_code
- fia_name_raw（FIA 原始名称）
- scientific_name（物种科学名）
- taxon_rank（分类等级）
- species_level_flag（是否明确到物种）
- native_status_if_available（若冻结数据本身可得，则记录原生状态；不可得就 NA，不得擅自联网补）

### 总体空间信息
- grain_km
- n_unique_plot_lineages_total
- n_detection_plots_total
- n_sampled_cells_total
- n_detection_cells_total

### A/B 分折信息
- n_plots_A
- n_plots_B
- n_detection_plots_A
- n_detection_plots_B
- n_sampled_cells_A
- n_sampled_cells_B
- n_detection_cells_A
- n_detection_cells_B

### 分折稳定性（只允许用“出现/抽样信息”，不得用真实 abundance geometry）
- cell_detection_IoU_AB（A/B 检出格子交并比）
- detection_cell_count_ratio_AB
- detection_plot_count_ratio_AB

### 空间自由度/几何可分析性（只允许 outcome-blind 量）
至少提供：
- n_connected_components_detection_support（检出支持域连通块数；若有 A/B 则分别报告）
- largest_component_fraction
- spatial_span_km 或等价的冻结非结果性空间跨度量
- geometry_information_flag（只按预先冻结的数据可识别性规则生成；不得参考 Q1 结果）

禁止加入：
- geometry gain（几何收益）
- range–abundance coupling（分布区—多度耦合）
- Wasserstein improvement（瓦瑟斯坦改善）
- R1/R2 prediction（R1/R2 预测）
- p-value（显著性）
- 任何真实 Q1 outcome（结果）

---

## E. `USGS_RANGE_AUDIT.csv`

一行对应一个可 crosswalk（名称对应）的 FIA 物种。

至少包含：
- FIA name
- USGS original map name
- USGS accepted name
- mapping_type（exact / official accepted-name mapping / unresolved）
- n_US_cells
- n_Canada_cells
- n_US_plus_Canada_cells
- US_share_USCA
- Canada_extension_flag
- USGS_full_support_components
- US_only_support_components
- full_vs_US_component_change
- full_vs_US_area_or_cell_loss
- full_vs_US_span_change（或其他预先冻结、易解释的截断几何诊断）
- Mexico_or_global_extension_status（只能填 KNOWN / UNKNOWN / NOT_ASSESSED；不得用现有 USGS 数据伪推全球）
- notes

主线尤其需要看到：
> US-share（美国占美国+加拿大图谱范围比例）高，并不一定意味着 geometry truncation（几何截断）小。

所以必须至少保留一个 topology/geometry-sensitive（拓扑/几何敏感）的截断诊断，而不能只给面积比例。

---

## F. `ELIGIBILITY_FRONTIERS.csv`

这是为了让主线在**不看 Q1 结果**的情况下冻结正式阈值。

Work 不得只给一个阈值结果。

至少输出这些连续/离散 frontier（前沿）：

### 1. 检出格子阈值
例如：
5 / 10 / 15 / 20 / 25 / 30 / 40 / 50 detection cells（检出格子）

### 2. 每折检出格子阈值
例如：
A、B 各至少 5 / 10 / 15 / 20 / 25 detection cells

### 3. 每折检测样地阈值
给出一系列合理节点，而不是提前选一个冠军阈值。

### 4. USGS US-share 阈值
70% / 80% / 90% / 95%

### 5. grain（空间粒度）
25 / 50 / 75 km

每个组合至少报告：
- n_species_remaining
- proportion_of_species_remaining

如果组合数量过大，可以：
- 完整输出机器可读 CSV；
- 主报告只展示关键二维切片。

**绝对禁止根据哪一组留下的物种 Q1 效果最好而推荐阈值。**

---

## G. `OBJECTIVE_FLAGS.csv`

一行一个物种，给出客观资格风险标记，而不是最终纳入决定。

建议至少包含：
- non_species_level_flag
- insufficient_sampling_25
- insufficient_sampling_50
- insufficient_sampling_75
- severe_AB_imbalance_flag
- low_detection_information_flag
- USGS_unresolved_flag
- Canada_truncation_flag
- geometry_truncation_risk_flag
- Mexico_global_unknown_flag
- introduced_or_uncertain_status_flag_if_known
- protocol_incompatibility_flag_if_known

对于尚未冻结正式阈值的 flag：
- 必须明确标记为 descriptive/diagnostic（描述性/诊断性）
- 不得把它偷偷变成最终 exclusion（排除）

---

## H. `TRACEABILITY_SAMPLE.csv`

用于主线做“抽查”。

必须从 census（普查）中确定性选择一小组物种，例如 12 个：
- 4 个高检出；
- 4 个中等检出；
- 4 个低检出；

选择只能基于 sampling/detection information（抽样/检出信息），不能基于 Q1 outcome（结果）。

每个样例至少给：
- species
- physical plot lineage ID（物理样地纵向谱系 ID）
- selected primary measurement ID
- year
- state
- P2PANEL
- A/B fold
- projected x/y（若公共 FIA 坐标允许；否则只给 cell ID）
- 25/50/75 km cell ID
- species detected yes/no

目的：
主线能够从原始记录 → 去重 → 分折 → 格网 → 物种普查数字进行人工追溯。

---

## I. `NO_Q1_OUTCOME_AUDIT.json`

必须明确记录并自检：
- real_Q1_model_fitted = false
- geometry_gain_computed = false
- R1_R2_compared = false
- abundance_geometry_used_for_selection = false
- significance_test_run = false
- outcome_based_species_filtering = false

如果任何一项为 true：
> STOP，并把本轮判为 protocol violation（协议违规），不得继续资格普查裁决。

---

## J. `CENSUS_RESULT_NOTE.md`

只允许总结：
1. 输入完整性；
2. 全国候选分析域和实际可用范围；
3. 25/50/75 km 的 sampling/detection information frontier（抽样/检出信息前沿）；
4. A/B 分折表现；
5. USGS 范围完整度前沿；
6. 尚需主线决定的阈值和规则；
7. 哪些问题仍因 Mexico/global range（墨西哥/全球分布）而 UNKNOWN（未知）。

不得写：
- “50 km 最好，因为 Q1 效果更强”
- “某物种 geometry coupling（几何耦合）很强”
- 任何真实论文效果结论。

---

# 2. 可复现包

最终建立新版本，例如：

`C:\range_paper\10_archive\elig_v02\`

其中至少保存：
- 本轮正式 request（请求）
- v0.2 continuity addendum（连续性补充）
- 本 v0.3 audit-deliverables addendum（审核交付补充）
- executable source（可执行源码）
- parameter/seed file（参数/种子文件）
- environment/package record（环境/软件包记录）
- execution log（执行日志）
- 上述全部审核 CSV/JSON/MD
- manifest（清单）
- SHA-256 哈希
- 完整 reproducible ZIP（可复现压缩包）

源码只放文件/ZIP，不要在聊天正文中粘贴。

---

# 3. Work 最终回报格式

聊天正文只回：

1. engineering PASS / FAIL（工程通过/失败）；
2. 是否违反 outcome-blind（结果盲）协议；
3. 25/50/75 km 候选物种 breadth（候选物种广度）的简要数字；
4. A/B 信息前沿的最重要事实；
5. USGS 分布完整度最重要事实；
6. 未决问题；
7. 可复现包路径/哈希；
8. STOP。

**不要替主线选最终 grain（粒度）、阈值或正式物种清单。**
