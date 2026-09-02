# D09B complete-panel estimation methods factual closure v01

Date: 2026-09-02  
Status: PASS factual closure; no final estimator or A/B partition selected.

## 1. One complete panel — SUPPORTED by FIA

Patterson & Reams (2005), Chapter 5, states two facts directly:

1. FIA assumes **complete spatial coverage for each panel across the population of interest**.
2. For a **single panel**, estimation proceeds using the standard Chapter 4 design-based method.

Thus one *complete* panel is a probability sample capable of a standard design-based estimate. Its principal limitation is smaller sample size and therefore larger variance. The 2022 FIA documentation likewise notes that a single panel is the obvious route to a year-specific estimate but can have large year-to-year variability because of small sample size.

### Generic post-stratified total for one panel

\[
\widehat{Y}_p = \sum_h A_h \bar y_{hp}
\]

where

\[
\bar y_{hp} = \frac{1}{n_{hp}}\sum_{i\in(h,p)} y_{hip}.
\]

Plain-language Chinese:

- \(p\)：所用完整 panel；无量纲标签。
- \(h\)：父总体中的 poststratum（后分层）；无量纲标签。
- \(A_h\)：stratum \(h\) 的已知面积；单位通常为 acres。
- \(n_{hp}\)：panel \(p\) 中落入 stratum \(h\) 的有效样地数；单位 plots。
- \(y_{hip}\)：panel \(p\)、stratum \(h\) 中样地 \(i\) 的 plot-level 属性值；对树数总量可构造成 trees/acre 型样地贡献。
- \(\bar y_{hp}\)：该 panel 在 stratum \(h\) 的样地均值；单位与 \(y\) 相同。
- \(\widehat{Y}_p\)：panel \(p\) 对总体总量的估计；若 \(y\) 是 trees/acre，则单位为 trees。

对应 stratum expansion quantity under the same fixed population/stratification is

\[
EF_{hp} = \frac{A_h}{n_{hp}}.
\]

This is the same post-stratified expansion-factor logic documented by FIA; it is **not** permission to reuse the full-evaluation FIADB `EXPNS` after changing the sample.

## 2. Multiple complete panels: FIA does not prescribe one universal core combination method

Patterson & Reams explicitly state that there is **no prescribed core procedure for combining panels**. They discuss Moving Average (MA) and Temporally Indifferent (TI) approaches.

### 2.1 Moving Average (MA) — OFFICIAL METHOD

For \(P\) complete panels,

\[
\widehat{Y}_{MA} = \sum_{p=1}^{P} w_p \widehat{Y}_p,
\qquad w_p>0,\quad \sum_{p=1}^{P}w_p=1.
\]

If panel estimates are treated as independent, the corresponding variance is

\[
\widehat{\mathrm{Var}}(\widehat{Y}_{MA})
= \sum_{p=1}^{P} w_p^2\widehat{\mathrm{Var}}(\widehat{Y}_p).
\]

Plain-language Chinese:

- \(P\)：参与组合的完整 panel 数；单位 panels。
- \(\widehat{Y}_p\)：第 \(p\) 个 panel 独立得到的总体估计；例如 trees。
- \(w_p\)：赋给第 \(p\) 个 panel 的正权重；无量纲；所有 \(w_p\) 之和为 1。
- \(\widehat{Y}_{MA}\)：多个 panel 的加权组合估计；单位与 \(\widehat{Y}_p\) 相同。
- \(\widehat{\mathrm{Var}}(\widehat{Y}_p)\)：第 \(p\) 个 panel 的设计型方差估计；例如 trees²。
- 组合方差中的 \(w_p^2\) 来自加权独立估计量的方差规则。

Important temporal meaning: FIA notes that MA estimates an attribute at some time between the first and last panel years and is a **temporal average**, with potential smoothing/lag. It is not automatically a finite-population “2023 point state.”

### 2.2 Temporally Indifferent (TI) — OFFICIAL METHOD

TI pools all panels of interest into the equivalent of one large periodic inventory and applies a common Phase-1 stratification. Under simple random sampling, FIA states TI is equivalent to MA with panel weights proportional to the number of plots in each panel.

For a selected set of panels \(\mathcal P\), the post-stratified point-estimate algebra can be written as

\[
\widehat Y_{TI,\mathcal P}
= \sum_h A_h \bar y_{h,\mathcal P},
\qquad
\bar y_{h,\mathcal P}
= \frac{1}{n_{h,\mathcal P}}
  \sum_{i\in(h,\mathcal P)} y_{hi}.
\]

and the corresponding stratum expansion factor is

\[
EF_{h,\mathcal P}=\frac{A_h}{n_{h,\mathcal P}}.
\]

Plain-language Chinese:

- \(\mathcal P\)：被选入该组合的完整 panels 集合。
- \(n_{h,\mathcal P}\)：这些 panels 合并后在 stratum \(h\) 中的有效样地数；plots。
- \(A_h\)：父总体 stratum 面积；acres。
- \(EF_{h,\mathcal P}\)：该 panel 子集在 stratum \(h\) 的有效扩展因子；acres/plot。
- 其余符号同上。

The 2022 FIA report states that most FIA estimates historically used TI: all panels in the periodic cycle are pooled, the post-stratified estimator is used, and the method **does not produce an estimate for any specific year**.

## 3. What happens to FIADB EXPNS when only selected panels are used?

### Official facts

- Post-stratification is repeated as panels are added.
- Its key objects are stratum area weights \(W_h\), plot-to-stratum membership, and within-stratum sample size \(n_h\).
- FIA expansion-factor algebra gives \(EF_h=A_h/n_h\).

### D09B inference for Q1

Therefore an official full-evaluation `POP_STRATUM.EXPNS` is **not automatically valid** for a fold that retains only a subset of panels.

A simple global multiplication such as “full EXPNS × (5/2)” or “× (5/3)” is exact only under restrictive conditions—for example, if the selected/full effective sample-size ratio is identical in every relevant stratum and the nonresponse/sample-area adjustment structure is unchanged. FIA does not document such a shortcut as a universal panel-subset method.

A fold-specific design implementation must instead reconstruct/recalibrate the effective panel-subset design using the parent population area/stratification plus fold-specific effective sample counts and appropriate nonresponse/sample-area adjustments. The exact FIADB implementation is a **FUTURE BOUNDED DESIGN TEST**, not selected here.

## 4. Can 3 panels and 2 panels each estimate the same total?

### Spatial/probability-sample answer: CONDITIONAL YES

Because a complete panel is designed to cover the population, a 3-panel subset and a 2-panel subset can each support design-based estimation after proper panel-specific/fold-specific estimation and variance treatment. Unequal panel counts primarily change precision.

### Temporal-estimand answer: NOT AUTOMATICALLY THE SAME

Panels are measured at different times. MA is explicitly a temporal average, and TI pools observations across a cycle and is explicitly not a specific-year estimate. Therefore a 3-panel fold and a 2-panel fold generally have different temporal centers/compositions.

Calling both “the same 2023 reporting-state population” requires an explicit Q1 temporal estimand/assumption. FIA does not prescribe A/B cross-fitting or declare arbitrary disjoint panel subsets to be identical time-point estimates.

## 5. A/B cross-fitting with complete panels

The following is **Q1 survey-design inference**, not an FIA-prescribed workflow:

- use disjoint complete design units rather than random within-panel half-samples;
- maintain one coherent State evaluation object;
- recompute fold-specific design weights and variances;
- keep estimation-unit/poststratum bookkeeping;
- verify no permanent-plot lineage appears in both folds.

This direction is statistically more design-aligned than D08C1's within-`State × P2PANEL` random split, but D09B does not select the panel grouping or estimator.

## 6. Important regional qualification

In current FIADB, RMRS and PNWRS—and part of Oklahoma—use `SUBPANEL`. A complete `P2PANEL` is not necessarily a one-year annual sample there. Any eventual A/B implementation must decide whether the atomic fold unit is complete P2PANEL, complete SUBPANEL, or another officially coherent complete design unit after a local design audit.

## Sources

- Patterson, P.L. & Reams, G.A. 2005. Combining panels for FIA estimation. SRS-GTR-80, Chapter 5.
- Westfall et al. 2022. Sampling and estimation documentation for the Enhanced FIA Program. NRS-GTR-207.
- FIADB Database Description v9.4 (August 2025).
- FIADB Population Estimation User Guide (November 2018).


## Texas evaluation-group caveat

The public `wc` metadata identifies `482023 TEXAS` as the 2014–2023 whole-State evaluation group, but current FIADB update history separately records 2023 East and West component data. Thus a **group code is not always safely interchangeable with one reconstructed numeric EVALID**. Any implementation must read the actual `POP_EVAL_TYP/POP_EVAL` membership for the selected group from the frozen FIADB database.

This does not change the panel-estimation theory above; it changes the required metadata join/closure before applying it.
