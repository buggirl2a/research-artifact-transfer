# Q1 / corrected D08C2 — Final Constructibility Contract v01

TASK_ID: `D08C2_CORRECTED_CONSTRUCTIBILITY_v01`

Status: **FROZEN BEFORE REAL SPECIES-LEVEL COMPUTATION**

你是 Work computational branch（有限计算工作线）。

本任务只执行 corrected D08C2，即：

> 在已经冻结的 strict whole-range starting universe 和 F0 FIA survey design 下，判断每个 accepted analysis species 是否能够被合法构造成进入后续 occupancy–encounter/support 与 abundance measurement 的双折 empirical input。

D08C2 **不是 final species cohort**。

不得运行 occupancy model、support recoverability、abundance precision Gate 或 real Q1。

---

# 1. Frozen scientific object

D08C2 的资格链严格为：

D1 taxonomy reconstruction
→ D2 target-population / operational native-domain / F0 linkage
→ D3 observation-opportunity constructibility
→ D4 bidirectional positive constructibility
→ provisional D08C2 eligibility
→ STOP

之后才由主线另行授权：

occupancy–encounter identifiability
→ support recoverability
→ abundance measurement quality
→ F1 Cohort & Observation Freeze

不得把后续问题提前塞进 D08C2。

---

# 2. Starting universe — immutable

Primary starting universe 必须恰好来自：

`Q1_Range_Gate_V02`

Commit:

`df01c2bd122d38b6dbbad9900c46cc8d7a0090af`

Reproducible ZIP:

`Q1_RANGE_GATE0_V02_CORRECTED_GEOGRAPHIC_SEMANTICS_REPRODUCIBLE_v01.zip`

SHA-256:

`717767f71216bca5fca3e7d43762c7fa026e7e799be162d05a68d3ab45bf4d50`

只选择：

`range_gate0_v02_class == PASS_COARSE`

预期 starting universe = **101 accepted species**。

如果不是恰好 101：

`INPUT_BLOCKED_STARTING_UNIVERSE_IDENTITY_FAILURE`

不得回到 361 species、312 species、旧 D08C1 231 queue 或旧 ≥10/15/20-cell survivor sets。

不得根据 D08C2 真实剩余物种数扩张 Tier 2。

---

# 3. Frozen taxonomy / native authority

accepted-species reconstruction 必须来自被冻结的 D08B1 v02 authority，不能重新做 taxonomy。

Range Gate v02 reproducible package 中被冻结的 D08B1 authority，包括：

* accepted analysis-species master；
* raw FIA taxon/code → accepted analysis-species mapping；
* WCVP native distribution long table；
* global range flags。

必须使用包内 manifest/SHA 对实际 member 做 identity verification。

不得：

* fuzzy-match species；
* 用当前网络 taxonomy 替换；
* 根据 TREE abundance/commonness 改 mapping；
* 先按 raw FIA code 统计再事后合并 accepted species。

正确顺序：

raw TREE record
→ frozen D08B1 mapping
→ accepted analysis species
→ species-level aggregation / eligibility diagnostics

---

# 4. Operational native-domain rule

WCVP confirmed-native state 仅定义：

**operational state-level native target domain**

它不证明任何 FIA TREE individual 本身的来源一定是野生原生。

Primary D08C2 observation universe 只使用被冻结 WCVP authority 中：

* native confirmed；
* introduced = 0；
* extinct = 0；
* location_doubtful = 0

的 target states。

explicit introduced state、unknown/unclassified state：

* 不进入 primary positive encounter；
* 不得产生 species-specific zero；
* 只允许进入 audit ledger。

不得利用 climate、forest type、Little、GBIF occurrence envelope 或真实 TREE 分布进一步缩窄 native-domain opportunity universe。

---

# 5. F0 survey design — immutable

必须继承已经 ACCEPT 的：

`Q1_D09C_T2_FINAL_CORRECTION_v02`

Commit:

`0ec3fce71258e38958ecbb7534f3635e2eb05a63`

Reproducible ZIP SHA-256:

`07cb461121c71ef46990fea3e0cf9d8f139fd873234b9f57910ff10c7c33752f`

强制使用：

* T2 reporting-frame family；
* EXPVOL；
* 45 states = 2023；
* MT/NM/UT = 2022；
* final 48-state whole-panel A/B partitions；
* A = frozen 2 complete P2PANELs；
* B = complementary frozen 3 complete P2PANELs；
* fold-specific TI；
* WV frozen `WV_EU_3_4` merged frame；
* accepted OR PLT_CN linkage treatment。

禁止：

* re-rank panel partitions；
* species-specific panel choice；
* AB/BA separately selecting partitions；
* full-evaluation EXPNS reuse as fold weight；
* reopening D09C。

---

# 6. FIA observational raw authorities

For states other than CA/OR/WA，使用被冻结 national FIADB raw authority：

`C:\range_paper\02_raw\FIA\SQLite_FIADB_ENTIRE.zip`

Version reference:

`FIADB_1.9.4.00`

SHA-256:

`ec2e4caf2a92e6079c20483f4a5f08d5ec2e7c31f498045237896a6df7e1565e`

Size:

`15351832599`

CA/OR/WA 的 F0 2023 observational tables 必须 override stale national SQLite content，并使用：

`C:\range_paper\02_raw\fia_t2_2023_observational_gap_v01\raw_table_zips\`

下被冻结的 9 个 official ZIP：

CA_TREE / CA_COND / CA_SUBPLOT
OR_TREE / OR_COND / OR_SUBPLOT
WA_TREE / WA_COND / WA_SUBPLOT

其 exact SHA/bytes 必须来自 accepted transfer：

`Q1-D08C2-CAORWA-OBS-GAP-CLOSURE-v01-20260904`

Commit:

`4fd2213ccca95f9a517472bba8187ce38b9b35ec`

CA/OR/WA PLOT 与 design metadata 不重新下载，继续使用此前 frozen raw-design authority。

不得混用 national SQLite 中 stale CA/OR/WA observational rows 来代表 F0 2023 frame。

---

# 7. P0 — mandatory full-schema gate before species values

这是执行前 integrity gate，不是科学筛选。

在读取任何 TREE.SPCD value、任何 species identity 或 survivor count 之前，必须验证所有实际使用 source 都含以下字段。

PLOT:
CN, STATECD, INVYR, P2PANEL, PLOT_STATUS_CD,
PLOT_NONSAMPLE_REASN_CD, DESIGNCD, MANUAL,
MACRO_BREAKPOINT_DIA

COND:
PLT_CN, CONDID, COND_STATUS_CD,
COND_NONSAMPLE_REASN_CD, PROP_BASIS,
CONDPROP_UNADJ, SUBPPROP_UNADJ, MACRPROP_UNADJ

SUBPLOT:
PLT_CN, SUBP, SUBP_STATUS_CD,
POINT_NONSAMPLE_REASN_CD,
SUBPCOND, MACRCOND, CONDLIST

TREE:
CN, PLT_CN, STATECD, INVYR, CONDID, SUBP,
SPCD, STATUSCD, DIA, TPA_UNADJ

F0 design keys required by the accepted D09C package must also resolve.

任何 required field 缺失：

`INPUT_BLOCKED_REQUIRED_SCHEMA_FIELD_MISSING`

STOP。

不得在发现 schema 缺失以后读取 species outcome 来决定是否“其实不需要”。

---

# 8. Target TREE population membership

Primary target tally state：

**FIA live large-tree / established-tree state**

qualifying positive TREE record 必须：

* belong to frozen F0 plot/frame；
* map deterministically through D08B1；
* accepted species belongs to the 101 starting universe；
* state lies inside that species' frozen operational confirmed-native domain；
* TREE.STATUSCD indicates live target state；
* FIA current DIA >= 5.0 inches。

DBH and DRC taxa both remain eligible according to FIA protocol.

不得建立 DBH-only primary filter。

DIA 只用于 target-state membership。

TPA_UNADJ：

* 可以携带给后续 abundance branch；
* 不得按 magnitude 用于 D08C2 eligibility；
* 不得计算 species weighted population totals。

---

# 9. D1 — taxonomy reconstruction

For each of exactly 101 accepted species:

从 bottom-level TREE records 使用 frozen mapping 重构 accepted-species positives。

必须输出：

* raw FIA taxon/code contributors；
* accepted species identity；
* mapping status；
* unmapped/ambiguous raw code audit。

任何本应属于 frozen mapping universe 的记录无法确定映射：

不得静默删除。

必须进入 QC / exclusion-reason audit。

不得因该物种记录多少改变 taxonomy。

---

# 10. D2 — target-population / native / F0 linkage

每条 candidate positive record 必须能够：

TREE.PL T_CN
→ F0 PLOT.CN
→ frozen state/frame
→ frozen P2PANEL fold
→ accepted F0 design membership

并同时满足 target-tree state 和 operational native-domain rule。

F0/native-domain 外的 positives 可计入 audit，但不得进入 primary D08C2 positive table。

无法合法链接的 candidate target record 不得静默删除。

D2 判断的是合法 data object 是否可构造，不是 abundance precision。

---

# 11. D3 — eligible observation-opportunity universe

Observation unit：

**FIA plot-visit / PLOT.CN**

对 species i、fold f、plot-visit j 定义 opportunity indicator：

O_ifj = 1

只有在冻结规则允许该 plot-visit 成为 species i 的合法 large-tree observation opportunity 时成立。

最低要求：

1. plot belongs to frozen F0 frame/fold；
2. state belongs to species i operational confirmed-native target domain；
3. PLOT_STATUS_CD = 1；
4. applicable accessible forest condition exists with COND_STATUS_CD = 1；
5. at least one relevant SUBPLOT sampling element has SUBP_STATUS_CD = 1；
6. FIA tally-tree/protocol eligibility is applicable under retained MANUAL/DESIGNCD authority；
7. required PLOT/COND/SUBPLOT linkage is deterministic。

COND_STATUS_CD = 5 或 nonsampled plot/subplot 不能产生 zero。

Partial sampling：

* 可以构成 legitimate opportunity；
* effort metadata 必须保留；
* 不要求四个 subplots 全部完整。

Sampling/condition proportion metadata：
CONDPROP_UNADJ, SUBPPROP_UNADJ, MACRPROP_UNADJ, PROP_BASIS
只作为 observation-effort metadata。

它们不是 species-selection threshold。

---

# 12. Legitimate non-detection rule

只有 O_ifj = 1 后才允许生成：

Y_ifj = 1：
存在至少一个 qualifying accepted-species TREE encounter。

Y_ifj = 0：
该 legitimate observation opportunity 中不存在 qualifying TREE encounter。

O_ifj = 0：
Y_ifj 必须为 NA / outside observation universe。

严格禁止：

“TREE table 中没有 species row”
直接解释为
“non-detection = 0”。

plot-level 0 也不等于 50-km cell absence，更不等于 latent Z_i(x)=0。

D08C2 不估计 Z。

---

# 13. D4 — bidirectional mathematical constructibility

Primary provisional D08C2 eligibility 要求：

A fold:

* at least one legitimate observation opportunity；
* at least one qualifying positive encounter。

B fold:

* at least one legitimate observation opportunity；
* at least one qualifying positive encounter。

即：

N_opp(i,A) > 0
N_opp(i,B) > 0
N_enc(i,A) > 0
N_enc(i,B) > 0

这是 AB/BA mathematical constructibility rule，不是 sample-quality threshold。

如果只有一个方向可构造：

status =
`ONE_DIRECTION_ONLY_DIAGNOSTIC`

保留 audit，但不得进入 primary bidirectional provisional pool。

---

# 14. Explicitly forbidden thresholds

D08C2 不得使用任何下列 threshold 决定 species eligibility：

* minimum number of TREE records beyond >0 constructibility；
* minimum encounter plots beyond >0；
* minimum 25/50/75-km encounter cells；
* old ≥10 / ≥15 / ≥20 cell criteria；
* minimum state count；
* minimum abundance；
* TPA_UNADJ magnitude；
* weighted population total；
* abundance CV / SE / precision；
* occupancy probability；
* detection probability；
* support recoverability；
* R1/R2 geometry；
* World 0 performance；
* Q1 predictive performance。

真实 survivor number 无论是多少，都不得修改以上规则。

---

# 15. Grid policy

D08C2 v01 默认：

**NO GRID REQUIRED**

不得自行生成或选择新的 25/50/75-km grid。

如果 execution environment 没有 mainline-authorized exact canonical grid identity：

不输出 encounter-cell eligibility threshold；
不因缺 grid 阻断 D1-D4。

Cell diagnostics 后移。

---

# 16. D08C2 status semantics

Per-species provisional status 至少允许：

`D08C2_ELIGIBLE_FOR_OBSERVATION_AND_MEASUREMENT_GATE`

`FAIL_D1_TAXONOMIC_RECONSTRUCTION`

`FAIL_D2_TARGET_NATIVE_OR_F0_LINKAGE`

`FAIL_D3_NO_LEGITIMATE_OPPORTUNITY_A`

`FAIL_D3_NO_LEGITIMATE_OPPORTUNITY_B`

`FAIL_D4_NO_POSITIVE_ENCOUNTER_A`

`FAIL_D4_NO_POSITIVE_ENCOUNTER_B`

`ONE_DIRECTION_ONLY_DIAGNOSTIC`

不得使用：

`FINAL_COHORT`

不得用 “support unrecoverable” 作为 D08C2 exclusion reason。

---

# 17. Required outputs

必须至少生成：

1. `Q1_D08C2_SPECIES_ELIGIBILITY_LEDGER_v01.csv`

   * exactly 101 rows；
   * D1/D2/D3A/D3B/D4A/D4B；
   * provisional final D08C2 status；
   * no final-cohort terminology。

2. `Q1_D08C2_EXCLUSION_REASON_LEDGER_v01.csv`

   * one row per exclusion/reason event；
   * reasons structural only。

3. `Q1_D08C2_SPECIES_FOLD_DIAGNOSTICS_v01.csv`

   * species × A/B；
   * legitimate opportunity count；
   * encounter plot count；
   * qualifying TREE count；
   * native-state count / F0 linkage diagnostics as appropriate；
   * no abundance totals。

4. `Q1_D08C2_ACCEPTED_SPECIES_AGGREGATION_AUDIT_v01.csv`

5. `Q1_D08C2_OBSERVATION_OPPORTUNITY_AUDIT_v01.csv`

   * compact summary/audit；
   * huge raw species × plot zero matrix need not be Relay'ed。

6. `Q1_D08C2_INPUT_AND_SCHEMA_QC_v01.csv`

7. `Q1_D08C2_RESULT_NOTE_v01.md`

8. deterministic reproducibility package / code

9. `SHA256SUMS.csv`

10. Relay v0.2.2 native:
    `TRANSFER_MANIFEST_v01.csv`

11. `REGISTRY_DELTA_v01.csv`

Potential publication candidates:

* species eligibility ledger；
* exclusion-reason/species-flow ledger；
* accepted-species aggregation audit；
* Methods-level opportunity rule summary。

但它们在 F1 前都只是 candidate，不得标成 final manuscript asset。

---

# 18. Registry governance

Branch 不得修改 central Registry。

REGISTRY_DELTA 必须记录：

TASK_ID
input authority / commit / version
exact source path or release identity
SHA-256 / bytes where applicable
status
scientific-output-changed
publication candidate
Methods role
Data role
Code role
QC role

Downloads toolkit 是 historical execution toolkit，不自动成为 canonical publication code。

只有 mainline ACCEPT 后，canonical reproduction code 才可进入 `06_src` governance path。

---

# 19. Local-data-gravity execution mode

禁止 Work 为了方便重新下载整个 national FIADB。

如果 Work runtime 无法直接读取用户的 `C:\range_paper` raw assets，正确执行模式是：

1. 按本冻结合同构建 deterministic local execution runner；
2. runner 自带 input SHA verification、P0 schema gate、scientific-boundary checks、QC、packaging 和 Relay-native manifest；
3. 用户只执行 runner；
4. local outputs 通过 Research Artifact Relay 回主线；
5. mainline 对真实 D08C2 result 做科学 audit。

不得因为 Work cloud environment 看不到 C:\ 数据而改用另一套 FIA snapshot。

不得把“无法远程读取本地 raw”报告成 scientific INPUT_BLOCKED；这是预期 data-gravity architecture。

---

# 20. Task-level PASS / FAIL

Task may return:

`PASS_READY_FOR_MAINLINE_OBSERVATION_GATE_AUDIT`

只要求：

* exactly 101 starting species audited；
* D1-D4 rule frozen and unchanged；
* all eligible/excluded species mechanically classified；
* all input/schema/QC checks pass；
* no prohibited downstream analysis；
* output package reproducible。

**D08C2 eligible species 少于 101 不是 task FAIL。**

真实 eligible count 不得成为修改规则的理由。

Pre-computation failure statuses：

`INPUT_BLOCKED_STARTING_UNIVERSE_IDENTITY_FAILURE`

`INPUT_BLOCKED_REQUIRED_SCHEMA_FIELD_MISSING`

`INPUT_BLOCKED_AUTHORITY_HASH_FAILURE`

`INPUT_BLOCKED_F0_LINKAGE_FAILURE`

`IMPLEMENTATION_BLOCKED_CONTRACT_VIOLATION`

任何 blocked status 都必须 STOP，不得继续读取/总结真实 species eligibility。

---

# 21. Absolute STOP boundary

本任务完成后不得继续：

* occupancy–encounter fitting；
* support probability；
* support recoverability Gate；
* abundance total estimation；
* abundance precision Gate；
* final cohort；
* R1/R2；
* World 0；
* cross-species prediction；
* conformal prediction；
* real Q1。

返回 mainline，由 PI 做 D08C2 science audit 并决定下一步。

END OF FROZEN CONTRACT
