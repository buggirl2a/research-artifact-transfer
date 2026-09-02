# D09 FIA DESIGN-BASED POPULATION-MASS ESTIMATOR FACTUAL CLOSURE v01

**Generated:** 2026-09-02  
**Role:** Q1 data-search / factual-closure line  
**Scope:** FIA official sampling and population-estimation design only  
**Overall source-closure status:** **PASS**  
**Answer to the scientific-mainline feasibility question:** **CONDITIONAL**

This package does **not** choose the final Q1 abundance estimator. It does not run any real species, does not modify D08C1, does not construct 25/50/75-km population mass, and does not run any Q1 outcome.

## Executive answer

FIA's probability-sampling framework **can, in principle, support a design-based population total for a user-defined 50-km spatial domain**. FIA's 2022 sampling/estimation documentation explicitly states that official analytical tools can provide estimates for user-defined populations such as a GIS polygon by defining a domain \(d\) across the parent FIA estimation units. Estimation units are the independent building blocks; totals and variances are summed across them, and estimation units do not cross State boundaries.

However, this does **not** validate the naive implementation "select the public FIA plots whose coordinates fall in a 50-km cell, sum their existing official weights, and call that the design-based answer" without further conditions.

For the frozen Q1 design, three material conditions remain:

1. **Time:** calendar years 2017–2023 are not one coherent national FIA evaluation. Current EVALID metadata show different State windows. A design-based implementation must use coherent evaluation/design metadata or explicitly reconstruct/calibrate a custom calendar-window design.
2. **A/B cross-fitting:** official EXPNS/stratum weights are calibrated to the full evaluation sample. If approximately half the plots are removed for an abundance fold, those weights cannot simply be reused unchanged. A fold-specific inclusion-probability/effective-sample-size treatment is required. FIA core manuals do not provide a ready-made recipe for Q1-style A/B half-samples.
3. **Spatial membership:** public FIA coordinates are fuzzed and some private plots are swapped. Therefore exact assignment of public records to a 50-km boundary is not exact.

Thus the **scientific object is design-estimable conditionally**, but the currently frozen calendar-window + A/B + public-coordinate implementation is **not yet a standard official FIA design-based total without additional design handling**.

---

# A. FIA statistical population and sampling design — **SUPPORTED**

## A1. Population, phases, sampling frame

The 2022 FIA sampling/estimation report defines the broad target population as **all land and water within the official boundaries of the United States**. The annual base design uses an approximately 5,937-acre hexagonal grid; one sample location is associated with each hexagon, and each location is assigned to a panel so that each panel has approximately uniform spatial coverage.

Relevant phases:

- **Phase 1 (P1):** wall-to-wall auxiliary information / stratification. In contemporary poststratification, pixels from a classified map are used to form strata and known stratum weights \(W_h\).
- **Phase 2 (P2):** the probability sample of ground plots. This is the base sample used for ordinary resource estimates.
- **Phase 3 (P3):** a subset of P2 with additional forest-health measurements; it is not the base tree-number sample for the object considered here.

The standard P2 plot is a four-point cluster: one central subplot and three peripheral subplots 120 ft away. Each subplot has radius 24 ft. A microplot is nested at each subplot; an optional macroplot may be used for large trees above a breakpoint.

## A2. Distinguish the statistical objects

- **Measured sample tree:** an individual TREE record observed on a sample element. It is not itself a population tree count.
- **Subplot / plot:** the field response unit. Tree-level observations are summarized to a plot-level response for design-based domain estimation.
- **Stratum (poststratum):** a class formed from wall-to-wall auxiliary map information. Each parent population has known stratum weights \(W_h\); sample plots are assigned to strata by plot center.
- **Estimation unit (EU):** a delineated geographic population with known area to which stratification is applied. FIA states that EUs do not cross State boundaries.
- **Evaluation:** FIA glossary definition: a unique combination of statistical sample, target population, and stratification for estimating attributes at a point in time.
- **EVALID:** unique identifier for the population/evaluation used to produce an estimate.
- **Target population/domain:** the domain \(d\) can be a subclass of the parent population, including user-defined geographic areas. Domain responses are formulated at plot level; plots outside the domain contribute zero response rather than being silently removed from the design bookkeeping.

## A3. How plots connect to known land area

Poststratification supplies \(W_h\), the known proportion of population pixels in stratum \(h\). In FIADB implementation, POP_STRATUM.EXPNS is the area a sampled unit (usually a plot) represents: approximately stratum area divided by the number of sampled plots in that stratum. The parent area appears through the estimation-unit/evaluation system.

**Source basis:** S04 Chapter 2; S03 Chapter 3; S09 glossary.

---

# B. TREE.TPA_UNADJ — **SUPPORTED**

Current FIADB Database Description v9.4 defines `TREE.TPA_UNADJ` as **trees per acre unadjusted**, the number of trees per acre that a sample tree theoretically represents based on the sample design.

For mapped fixed-radius design (`PLOT.DESIGNCD = 1`), current v9.4 gives:

- subplot tree: **6.018046 trees/acre**
- microplot tree: **74.965282 trees/acre**
- macroplot tree: **0.999188 trees/acre**

Older variable-radius inventories may have diameter-dependent values.

It is **tree-level and per-acre**, not a population total. It is "unadjusted" because official population estimation additionally applies the appropriate `POP_STRATUM` nonresponse/sample-area adjustment factor and the area expansion factor.

The current national field names are:

- `ADJ_FACTOR_SUBP`
- `ADJ_FACTOR_MICR`
- `ADJ_FACTOR_MACR`

For the frozen Q1 large-tree object (>=5 inches d.b.h./d.r.c.), the official Example 3-3 logic is:

- `<5 in` -> microplot factor
- `>=5 in` but below an applicable macroplot breakpoint -> subplot factor
- above macroplot breakpoint -> macroplot factor

Therefore **"large tree" does not mean every >=5-inch record always uses SUBP**; macroplot design must be honored where applicable.

**Status:** SUPPORTED.

---

# C. POP_STRATUM.EXPNS — **SUPPORTED**

The official Population Estimation User Guide states:

> `POP_STRATUM.EXPNS` is the area the sampled unit represents; the sampled unit is usually a plot, and the expansion is the area represented by a stratum divided by the number of sampled plots in that stratum.

Thus, when area is stored in acres, EXPNS is operationally **acres represented per sampled unit/plot**.

For a tree-number contribution:

1. `TPA_UNADJ`: trees per acre represented by the sample tree.
2. multiply by the appropriate `ADJ_FACTOR_*`: adjusts for partially nonsampled plot area.
3. multiply by `EXPNS`: acres represented by that sampled unit.
4. result: population **number of trees** represented by that sample-tree contribution.

EXPNS is not a permanent weight independent of design context. It is stored on evaluation/stratum records; 2022 documentation states poststratification is repeated as new panels are added, so \(W_h\), \(n_h\), assignments and derived expansion quantities can change across evaluation vintages/restratification.

**Status:** SUPPORTED.

---

# D. Official live-tree population-total estimator — **SUPPORTED**

## D1. Official FIADB implementation

Population Estimation User Guide Example 3-3 explicitly estimates:

**"Number of live trees (at least 1 inch d.b.h./d.r.c.), in trees, on forest land."**

Its point-estimate logic is:

\[
\widehat T =
\sum_{\text{eligible trees}}
TPA\_UNADJ_t
\times ADJ_{j(t)}
\times EXPNS_{h(t)}
\]

with `TREE.STATUSCD = 1`.

`j(t)` is the sample element on which the tree was measured: MICR, SUBP, or MACR according to diameter and macroplot breakpoint.

### Chinese line-by-line interpretation

- 对每棵符合条件的样木 \(t\)，读取 `TREE.TPA_UNADJ`：它先表示该样木在其采样元件上代表多少 **trees/acre**。
- 根据树的采样元件乘 `ADJ_FACTOR_MICR/SUBP/MACR`：修正部分样地未测量的非响应/面积比例。
- 再乘该样地所在 evaluation-specific stratum 的 `EXPNS`：把每英亩贡献扩展到该 sampled unit 所代表的总体面积。
- 对所有符合 domain 和属性条件的树贡献求和，单位成为 **trees**。

## D2. Verified FIADB join path

Official guide verifies the design join sequence:

`POP_EVAL_GRP -> POP_EVAL_TYP -> POP_EVAL -> POP_ESTN_UNIT -> POP_STRATUM -> POP_PLOT_STRATUM_ASSGN -> PLOT -> COND -> TREE`

Key relations include:

- `POP_EVAL_TYP.EVAL_GRP_CN = POP_EVAL_GRP.CN`
- `POP_EVAL.CN = POP_EVAL_TYP.EVAL_CN`
- `POP_ESTN_UNIT.EVAL_CN = POP_EVAL.CN`
- `POP_STRATUM.ESTN_UNIT_CN = POP_ESTN_UNIT.CN`
- `POP_PLOT_STRATUM_ASSGN.STRATUM_CN = POP_STRATUM.CN`
- `POP_PLOT_STRATUM_ASSGN.PLT_CN = PLOT.CN`
- `COND.PLT_CN = PLOT.CN`
- `TREE.PLT_CN = COND.PLT_CN AND TREE.CONDID = COND.CONDID`

This path is design metadata, not optional decoration.

**Status:** SUPPORTED.

---

# E. Can a user-defined 50-km grid cell be a valid FIA design-based domain? — **CONDITIONAL**

## E1. Formal theory

Yes, **as a domain**, conditionally. The 2022 FIA report explicitly states that EVALIDator/DATIM provide estimates for State populations or other **user-defined populations (e.g. a GIS polygon)**. Such a polygon is normally specified as domain \(d\) and applied across all parent estimation units. EUs with no plots containing the domain contribute zero to both estimate and variance.

Therefore a 50-km equal-area cell is not disqualified merely because it is not a county or standard FIA geography.

## E2. Is "select plots in cell and sum existing weights" valid?

### Point estimate: **CONDITIONAL**

If all of the following hold:

- plots and their population assignments come from one coherent evaluation,
- domain membership is correctly known,
- the correct tree sample-element adjustment is used,
- the parent EU/stratum EXPNS values are retained correctly,

then the domain point-total algebra can be expressed by assigning zero response to plots outside the cell. Because zeros do not change the point sum, a filtered sum can be algebraically equivalent to the point estimate.

But this is **not a complete official domain analysis** if filtering discards parent design quantities.

### Variance: **NOT SUPPORTED by selected in-cell plots alone**

Official domain variance depends on parent \(n\), \(n_h\), \(W_h\), and zero responses outside the domain. Appendix 1 shows that shortcut expansion-factor variance can be materially inaccurate; its worked example had domain-based variance 2.5 times the shortcut variance.

Therefore selected in-cell trees/plots plus official weights are insufficient for the **official sampling error**.

## E3. Must Phase-1/stratum areas be recalculated for the cell?

Not necessarily for the **basic domain estimator**. The basic domain estimator uses the parent population's poststrata and assigns a domain response.

However, FIA Appendix 1 provides two approaches if explicit **area control** at the cell scale is desired:

1. preferred: define the desired scale as the population and develop poststratification weights specifically for it, with adequate sample size;
2. ratio approach: estimate domain proportion and multiply by the known domain area.

D09 does not choose between them.

## E4. Cell cuts strata / EUs / States

- **Cuts strata:** supported; normal domain estimation.
- **Cuts EUs:** supported; estimate within EU, then sum.
- **Crosses State boundary:** conditionally supported by State-side decomposition because EUs do not cross States and EUs are treated as independent.
- **Forest + nonforest:** supported; FIA samples all land/water, and tree response is zero where no qualifying trees occur.

## E5. Sparse cells

Formal computation is possible, but statistical precision may be poor. FIA statistical literature shows small \(n_h\) and small total \(n\) can destabilize means/SEs. The published numerical recommendations are variable-specific and **must not be converted into a universal Q1 50-km threshold**.

## E6. Public coordinates

This is a separate operational limitation. FIA exact coordinates are confidential. Public coordinates are fuzzed (most <=0.5 mile, remainder up to 1 mile), and some private forest plots are swapped within county. Consequently, exact public-FIADB assignment to a 50-km cell boundary is not exact.

**Overall E status:** CONDITIONAL.

---

# F. State-crossing cells and State-specific addition — **SUPPORTED, CONDITIONALLY**

FIA states that estimation units do not cross State boundaries and are treated as independent. Multi-EU, multi-State totals are produced by summing component totals, and the variances are summed under the independence assumption.

Thus, for a cell crossing State boundaries, a design-consistent conceptual construction is:

\[
\widehat T_{\text{cell}}
=
\sum_s \widehat T_{\text{cell}\cap s}
\]

and

\[
\widehat V(\widehat T_{\text{cell}})
=
\sum_s \widehat V(\widehat T_{\text{cell}\cap s})
\]

provided each State-side piece is estimated under a coherent State evaluation/design.

If explicit cell-area control is used, the State-side/piece areas and poststratification/ratio framework must also be handled consistently.

**Status:** SUPPORTED for addition; **CONDITIONAL** on coherent per-State design inputs.

---

# G. Sampling variance / standard error — **SUPPORTED for coherent domains**

The current foundational FIA poststratified domain framework gives:

\[
\widehat{\bar y}_d = \sum_{h=1}^{H} W_h \bar y_{hd}
\]

with

\[
\bar y_{hd} = \frac{1}{n_h}\sum_{i=1}^{n_h} y_{hid}.
\]

Here \(y_{hid}\) is the plot-level response for domain \(d\); a plot outside the domain has response zero.

The official variance contains:

- ordinary stratified-sampling variability; and
- an additional poststratification term reflecting random within-stratum sample size.

For total:

\[
\widehat Y_d=A_T\widehat{\bar y}_d
\]

\[
\widehat V(\widehat Y_d)=A_T^2\widehat V(\widehat{\bar y}_d)
\]

and `SE = sqrt(variance)`.

Across independent estimation units, variances are summed.

### Required inputs

At minimum:

- parent population area \(A_T\);
- stratum weights \(W_h\);
- total parent sample size \(n\);
- within-stratum sample sizes \(n_h\);
- plot-level domain responses \(y_{hid}\);
- evaluation-specific plot-to-stratum assignment;
- nonresponse/sample-element adjustment for tree responses.

### Custom 50-km variance

A valid domain variance is formally available if the cell is represented as a domain within a coherent parent design. It is **not** obtained by computing variance only from the plots falling inside the cell.

With very few plots, SE can be very large or unstable; an EU with no sampled domain plots contributes zero estimate/variance under the official domain implementation. This is a recognized small-domain limitation, not proof that the true population is zero.

**Status:** SUPPORTED if coherent parent design is retained; otherwise NOT SUPPORTED.

---

# H. Is frozen 2017–2023 compatible with official evaluations/panels? — **NOT SUPPORTED as one national official evaluation**

## H1. No national 2017–2023 EVALID object

The current official EVALIDator `wc` table directly demonstrates different State windows for 2023 evaluations:

- Delaware `102023`: **2017–2023**
- Florida `122023`: **2016–2023**
- California `062023`: **2013–2023**
- Washington `532023`: **2014–2023**

Other States also differ.

Therefore "all records measured in calendar years 2017–2023" is **not one coherent national FIA evaluation**.

## H2. Why this matters

FIA defines an evaluation as a combined sample + target population + stratification object. The 2022 documentation states that poststratification is repeated when a new panel is added. Patterson & Reams also state that FIA assumes spatially complete panels and that combining panels can require modified estimation procedures.

Thus, selecting measurements by calendar year while attaching expansion/stratum data from varying evaluations can disconnect:

- which plot visits belong to the statistical sample,
- which stratum assignment applies,
- which \(n_h\) applies,
- which expansion factors/area basis applies.

### INFERENCE

A raw `MEASYEAR between 2017 and 2023` filter can therefore mix incompatible evaluation vintages and, where repeated plot visits are present, can risk using records in a way that is not equivalent to a single official design sample. D09 did not run a real data audit to quantify that risk.

## H3. Authoritative alternatives that remain open

Without selecting one:

- use coherent State-specific official EVALIDs;
- or construct a custom 2017–2023 statistical sample with explicitly recalibrated design metadata/weights;
- or conduct a future bounded design audit to determine whether another synchronized panel strategy is defensible.

**Status:** 2017–2023 as a nationwide official evaluation = NOT SUPPORTED.

---

# I. Critical A/B cross-fitting consequence — **FULL-SAMPLE WEIGHTS NOT SUPPORTED UNCHANGED**

Q1's A/B cross-fitting requirement remains frozen. D09 does not alter it.

## I1. Can standard EXPNS/weights be reused after removing half the plots?

**No, not unchanged.**

`EXPNS` and the poststratified weights encode the effective full-evaluation sample size / inclusion probabilities. FIA-authored statistical literature states explicitly that a sampling weight arises as the inverse inclusion probability and that it is inappropriate to alter effective sample size without adjusting the weight. In a panel context, when effective \(n\) changes, poststratified weights must change.

Q1 A/B thinning is not the same scientific problem as retrospective disturbance estimation, but the weighting principle is directly relevant.

## I2. Would naive unchanged weights give about half the total?

**INFERENCE: yes in expectation under ideal independent 50% thinning.**

If every full-sample plot is retained independently with probability 0.5 and the full-sample contribution `TPA_UNADJ × ADJ × EXPNS` is left unchanged, a simple fold sum has expectation approximately 0.5 times the full-sample sum.

This is mathematical survey-sampling reasoning, **not an FIA official A/B estimator**.

## I3. Does a missing constant factor cancel after within-species normalization?

Only under an exact condition:

\[
\frac{cT_c}{\sum_k cT_k}=\frac{T_c}{\sum_k T_k}
\]

if the same scalar \(c\) applies to every cell for that species/fold and the support/membership is unchanged.

Random A/B thinning does not guarantee equal realized retention across cells, strata, EUs or panels, and it can create cell-specific zero samples. Therefore the "factor 2 will cancel" argument is **not sufficient**. Sampling variance also does not cancel.

## I4. What would design-consistent A/B require?

Official core FIA sources do **not** provide a ready-made Q1 A/B half-sample procedure.

At minimum, design-based logic requires that the fold-selection probability/effective sample size be incorporated into weights and variance. A plausible strategy would preserve balance within major design blocks (State, coherent EVALID, EU, stratum, and possibly panel) and recalibrate fold-specific weights, but this is an **INFERENCE / FUTURE BOUNDED TEST**, not an FIA-prescribed recipe.

No standard BRR / balanced-half-sample / replicate-weight recipe for this Q1 use case was identified in the core official sources searched. This absence is recorded as "not found in the bounded core search", not proof that no relevant method exists anywhere.

**Status:** original full-evaluation weights on A-only/B-only = NOT SUPPORTED; a recalibrated fold estimator = CONDITIONAL / FUTURE BOUNDED TEST.

---

# J. Population total versus density — **SUPPORTED distinctions**

FIA officially supports both population totals and ratios.

## J1. Total number of trees in a domain

Direct poststratified population total in **trees**. This is the FIA target quantity most directly analogous to the frozen Q1 "population-mass" object, but D09 does not choose it as final.

## J2. Trees per acre of total land/population area

If total parent/domain area is known, divide tree total by the known total area. This is a mean per total acre; denominator is fixed/known.

## J3. Trees per acre of forest land

This is a **ratio estimator**:

tree total / estimated forest-land area.

The denominator is itself an estimated random quantity, so its variance requires numerator variance, denominator variance, and covariance.

These are different estimands and must not be conflated.

---

# Direct answer to the mainline question

> Can FIA's own probability-sampling design support a defensible estimate of each species' live large-tree population total inside a user-defined 50-km grid cell, under frozen 2017–2023 and A/B cross-fitting?

**Answer: CONDITIONAL.**

- **50-km geometry itself:** yes, as a user-defined domain in FIA design-based theory.
- **Cross-stratum/EU/State:** supported by domain estimation plus EU/State summation.
- **Official variance:** available only if parent design information is retained; selected in-cell plots alone are insufficient.
- **2017–2023 calendar window:** not a coherent national official evaluation.
- **A/B half-fold:** full-sample EXPNS/weights cannot be reused unchanged.
- **public plot coordinates:** exact cell membership is uncertain because of fuzzing/swapping.
- **sparse 50-km/species cells:** formally estimable but may lack acceptable design precision.

The minimum scientifically defensible next step is therefore **not real Q1 computation**. It is a bounded statistical-design decision/test that resolves temporal evaluation coherence, fold-specific weight recalibration/variance, and spatial-domain membership before any final estimator is implemented.

**STOP.**
