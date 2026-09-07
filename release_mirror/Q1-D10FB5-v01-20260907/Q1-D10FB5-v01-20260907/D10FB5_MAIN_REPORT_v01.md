# D10FB5 Main Report v01

Task: `Q1_D10F_B5_BOUNDED_VARIANCE_INTERFACE_QUALIFICATION_v01`

Scope: local frozen artifacts, exact algebra, and species-blind synthetic qualification only. No real-species outcome was read. No production D10F-C work was performed.

## Executive result

Singleton constructibility: **NO at the exact-rule stage**. B4 supports variance-only pseudo-strata as an architecture, but B4 O01 explicitly leaves the exact Q1 pairing/grouping rule open. B4 does not freeze a unique rule or a small finite candidate set, and the local metadata do not remove that ambiguity. Under the B5 stop rule, all 24 cases are delivered as a blocked inventory; no donor was assigned and no singleton synthetic/covariance qualification was run.

WV combined-population mapping: **YES algebraically, bounded for design interpretation**. All 13 current pooled plot coefficients equal the coefficient obtained by defining `WV_EU_3_4 = EU3 union EU4` as one estimation population before fold-specific estimation: A uses `74976.8/8 = 9372.1`, and B uses `74976.8/5 = 14995.36`. This changes interpretation only and does not alter A2.

The frozen artifacts demonstrate the union area, selected panels, plot identities, fold counts, source-EU counts, zero plot overlap, and pooled coefficient formula. B4 supports combined geographic populations and one-block pooled-operator variance structurally. The exact eligible-location inclusion probabilities, base-weight/calibration mapping, and strict 2-D randomization are not demonstrated.

## A. Singleton

### A1. Is a B4-supported rule uniquely or finitely constructible?

No. B4 A04/A05 support the candidate family and require design-only, a priori grouping with same-fold outcomes. B4 O01 states that no source specifies the exact state/EU/poststratum pairing. The authority also does not determine pair versus larger group, same-EU constraints, or a similarity measure. Enumerating such candidates in B5 would invent method choices.

### A2. Metadata available

The frozen inventory supplies state, EVALID, source EU, source parent poststratum, selected panels, full and fold `n_h`, population area, and design/repair class. These variables are species-blind, but their availability does not authorize a ranking, distance, or threshold.

### A3. Point estimator and leakage

A2 remains unchanged. The 24 before/after TI coefficients are exactly equal because no variance grouping was instantiated. `cross_fold_target_outcome_access = 0`; real target abundance/support access is also zero.

### A4. Synthetic variance and covariance

Not run. Section 11 of the task is conditional on a constructible candidate. Running synthetic trials over analyst-created partners and selecting the best coverage would violate the no-method-shopping rule.

### A5. Remaining need

Mainline must freeze an outcome-independent grouping rule or an authority-bounded finite candidate set before singleton qualification can resume. The exact transition from a pooled-residual implementation to FIA V1+V2 also remains open.

## B. WV

### B1. Exact coefficient mapping

`U = EU3 union EU4`, with `A_U = 23014.8 + 51962.0 = 74976.8` acres. D09C fixes the same merged frame for A and B, then computes fold TI as block area divided by actual fold sample count. The current B3 pooled coefficient and the pre-estimation combined-population coefficient match for 13/13 plots under exact rational arithmetic.

### B2. Demonstrated, authority-supported, and not demonstrated

Demonstrated locally:

* A panels 3 and 5; B panels 1, 2, and 4.
* A has 8 plots: EU3=2 and EU4=6. B has 5 plots: EU3=0 and EU4=5.
* No `PLT_CN` or permanent-plot identity overlaps between folds in this merged block.
* One merged block uses the common `A_U/n` coefficient and preserves the exact area control.

Supported by B4 authority:

* combined geographic estimation populations;
* subset-panel estimation as a sparse-population context;
* a one-block variance/covariance construction for the pooled operator itself, never `Var(EU3)+Var(EU4)` attached to the pooled point estimate.

Not demonstrated:

* exact eligible-location inclusion probabilities across EU3 and EU4;
* a base-weight/calibration solution producing the common coefficient;
* strict two-dimensional spatial randomization identity.

### B3. Fold-B EU3 zero sample

It is exactly demonstrated that the realized frozen B sample contains zero EU3 plots and that the two observed EU3 plots are both in panel 5. The frozen artifacts do not encode counterfactual panel assignment probabilities for all eligible EU3 locations. Therefore B5 cannot strictly classify the event as either pure realized imbalance or structural exclusion. It remains a bounded stress case, not automatic proof of point bias.

### B4. Synthetic point and variance evidence

The synthetic finite population uses exactly 374,884 elements of 0.2 acres: 115,074 in EU3 and 259,810 in EU4. `synthetic_y` is a deterministic trigonometric signal with different EU means. Each fold/regime uses 50,000 repeated samples. These are qualification worlds, not reconstructed FIA randomization.

W0 uses SRSWOR over the union and the one-block variance `A_U^2(1-n/N)s^2/n`:

* Fold A: relative bias 1.67053336904e-05; variance ratio 0.995230317898; 95% coverage 0.90048 (MCSE 0.001338773839); zero-EU3 frequency 0.05316.
* Fold B: relative bias -0.000715700124406; variance ratio 1.00054381919; 95% coverage 0.82654 (MCSE 0.00169334951147); zero-EU3 frequency 0.1579.
* Conditional Fold-B zero-EU3 draws have bias 230303.864636 and coverage 0.131475617479. This is a conditional stress diagnostic; unconditional W0 is the intended design result.

W1 fixes per-draw EU3 representation at 0.08 rather than its population share 0.306958952636, while sampling distinctly within each EU. The same unweighted pooled operator is then design-mismatched:

* Fold A: relative bias 0.133816225759; variance ratio 1.0030630625; coverage 0.46444.
* Fold B: relative bias 0.133781682542; variance ratio 0.999532953372; coverage 0.43318; zero-EU3 frequency 0.65656.
* Conditional Fold-B zero-EU3 draws have bias 230547.14074 and coverage 0.137413183867.

No coverage threshold is converted into a PASS/FAIL status. These are accepted-evidence candidates for mainline review.

### B5. Bounded covariance check

Fixed outcome-blind domains are EU3 and EU4 contributions. For every regime/fold/subset, both empirical and candidate calculations satisfy `Var(D1 union D2) = Var(D1) + Var(D2) + 2 Cov(D1,D2)` to floating-point precision. The candidate 2x2 matrices are positive semidefinite within a `-1e-8` numerical tolerance. W0 assesses compatible joint behavior; W1 shows that algebraic consistency alone cannot protect a point/variance interface from inclusion-intensity misspecification.

### B6. Is A2 reopening required?

No evidence in B5 requires reopening A2. Exact coefficient mapping passes. W0 shows the pooled operator is coherent in a valid common-probability qualification world, while W1 identifies the design assumption whose violation causes failure. Because actual inclusion-probability identity remains unproven, this is a contract candidate rather than production authorization.

## C. Implication

Proposed mainline interpretation:

* Singleton: hold implementation until mainline freezes an outcome-independent grouping rule or finite candidate set. Do not alter A2.
* WV: retain the exact combined-population representation as a pooled-operator variance contract candidate, with the actual inclusion-probability/weight mapping explicitly bounded or recovered before production.
* Do not authorize D10F-C from this Work package alone.

STOP. Return to Q1 mainline.
