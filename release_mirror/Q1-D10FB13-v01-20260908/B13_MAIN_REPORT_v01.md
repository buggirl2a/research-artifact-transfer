# B13 工作协方差成分可迁移性诊断

## 结论状态

`B13_DIAGNOSTIC_COMPLETE`。本包是经验诊断证据；D10F-C 仍为 `HOLD`。本任务没有构造生产协方差估计器。

## 方法边界与验真

Stage-P 在任何目标参考开启前封存 1,517,064 个池派生成分对象；Stage-S 验证 1,517,064 个对象，失败 0。B12 缓存只读复用，`NEW_TREE_SOURCE_SCAN_ROWS=0`，`Q1_CALCULATION_ROWS=0`。

矩阵从逐 member 的有限样本充分统计量直接构造。池估计始终使用 `Σ_g T_g/Σ_g(n_g-1)`，没有把池样地拼接后全局中心化。W 称为 `WITHIN_CELL_OBSERVED_RESIDUAL_SCATTER`，B 称为 `BETWEEN_CELL_ALLOCATION_MEAN_SCATTER`。没有 clipping、ridge、shrinkage、nearest-PD、平滑或协方差补全。

## Q1—Q15

**Q1：原整协方差不匹配主要是尺度、形状/位置，还是两者？** 尺度项相对更突出，但形状仍不能据此获得生产资格。50 km generic T 的中位迹 |log ratio|=1.379，单位迹 Frobenius 差=0.569，方差位置 TV=0.622；相应 transport/noise 中位比分别为 2.432、0.681、0.895。

**Q2：完美 oracle 尺度校正后还剩多少？** 50 km generic T 的基线中位相对 Frobenius=0.999，把已封存池矩阵缩放到目标迹后为 0.927，中位相对改善=0.167。剩余差异明确非零；目标迹只用于 `DIAGNOSTIC_ORACLE_ONLY`。

**Q3：方差位置在哪里不同？** 总体中位 TV=0.622、重叠=0.378。逐目标的最大差异单元、目标最大方差单元和池最大方差单元保存在 `B13_VARIANCE_LOCATION_DIAGNOSTICS_v01.parquet`；这些位置差异包含样地位置与单元均值差，不能命名为纯分配。

**Q4：非对角依赖是否比对角位置更能迁移？** 单位迹 off-diagonal 差的中位 transport/noise 比=0.865，对角位置 TV 的对应比=0.895。两者使用不同原始距离尺度，只通过各自参考噪声归一化作方向性比较；没有为零对角强制相关矩阵。

**Q5：精确 W/B 分解显示什么？** generic 50 km 的误差能量中位份额为 W=0.084、B=0.638、交叉项=0.259；负交叉项比例=0.076，说明部分目标存在成分误差抵消。按中位误差能量，B 成分更大，但单独 Frobenius 大小不能替代完整误差几何。oracle W/B 交换的逐目标结果已保留。

**Q6：50 km 的 within-cell scatter 可识别吗？** 目标中 effective within-cell df>0 的比例=0.952，观测 W 为信息性的比例=0.799，中位 effective within-cell df=11.000，位于重复单元的样地比例中位数=0.917。无重复产生的零 W 被标为结构稀疏，不解释为同质性。

**Q7：100/200 km 是否改变责任成分？** generic T 中位相对 Frobenius 从 50 km 的 0.999 变为 100/200 km 的 0.984/0.952；单位迹差为 0.569/0.516/0.388。目标 W 的有效 within-df 比例变为 0.981/0.992。粗化提高重复度，但不能把 50 km Q1 粒度改写为 100/200 km。

**Q8：Level1 与 Level2 是否因同一原因失败？** Level1/Level2 的 T 相对 Frobenius中位数=0.998/1.044，位置 TV=0.605/0.970；W/B 相对误差分别为 0.999/1.008 与 1.000/1.043。50 km 有效 within-df 比例=0.957/0.868。机制与可识别性不同，不能合并成一个解释。

**Q9：哪些差异超过目标自身参考噪声？** T/W/B 的相对 Frobenius transport/noise 中位数=1.061/0.825/1.107；分量为 NOT_ESTIMABLE 时保持缺失，不改用事后拆分。比值 1 只是同量纲自然参照，不是生产阈值。

**Q10：B9 候选是否比固定 NC1 更像目标？** 在可比对象中，T/W/B 的候选相对 Frobenius 更小比例=0.603/0.589/0.573。相对优于不兼容池并不等于绝对合格。

**Q11：直接97物种是否呈现同样模式？** 预声明的 450,080 个目标×代码配对中，池或目标 T 非零并进入成分评分的有 30,258 个。T/W/B 的有限相对误差中位数=1.002/1.000/1.004；W 的结果标记为 `Q1_DIRECT97_DIAGNOSTIC_ONLY_NO_COMPONENT_SELECTION`。三类 multi-SPCD 只保留 accepted projection 的 code-level 诊断，不合并 SPCD。

**Q12：actual24 是否有一致的次级信号？** 24 个案例全部保留，FULL5 n=2–13。50 km generic T/W/B 中位相对 Frobenius=1.396/1.006/1.315。由于 full5 很小，这些仅是 `FULL5_LIMITED_REFERENCE`，不是 truth、调参、筛选或 A/B 修正输入。

**Q13：哪些成分共享假设仍具科学可行性？** 可以继续调查“尺度模型与单位迹结构分开”“只借用可识别的残差成分、保留目标域位置成分”两类窄假设。它们仍是 `HYPOTHESIS / DESIGN CANDIDATE`，尚未被本包升级为估计器。

**Q14：哪些假设受到实质挑战？** 未经改变地搬运整协方差继续受到挑战；把 B 解释成纯空间分配、把无重复产生的零 W 当成同质性、把候选优于 NC1 当成生产资格，也都与本诊断边界不相容。

**Q15：最窄的下一步是什么？** 在 mainline 另行授权后，先做预声明的尺度/单位迹分离检验，并按 Level1/Level2 与参考强度分层；若 B 仍主导，再调查域/分配感知重构。不要直接进入整套 GVCF、层级协方差或 replicate generation。

## 代数与防火墙结果

member 恒等式检查 43,308 次、池/实际候选检查 55,752 次、Q1 物种非零对象检查 60,516 次；`T=W+B` 材料失败为 0。误差几何检查 85,722 次，失败 0。B12 50 km 整协方差基线重建 9,280 次，失败 0。所有矩阵由解析散度构造给出对称/PSD 状态；材料 PSD 失败 0。

## 解释边界

这是一项项目统计分析，不是 FIA 官方估计器。不存在生产 pass；B9 pool、A/B、A2、50 km 主粒度和 Q1 cohort identity 均未改变。
