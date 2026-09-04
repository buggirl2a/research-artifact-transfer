# D10C-A result note v01

Terminal status: `ABUNDANCE_ESTIMATOR_AUTHORITY_CLOSED_READY_FOR_D10C`

This was a species-blind estimator-authority closure. It did not run D10C, read `TREE.SPCD`, compute real abundance/support, select species, or run real Q1.

## Answers required by the contract

**Q1. Can every frozen F0 plot visit be assigned uniquely?**  
Yes. `338,619` F0 plot visits produced `338,619` crosswalk rows; C1-C9 status is all PASS.

**Q2. Is nationwide coverage complete?**  
Yes. `48` of 48 reporting states have complete passing rows.

**Q3. Does any permanent plot identity appear in both folds?**  
No. `338,619` unique stable permanent identities were observed: `135,513` only A, `203,106` only B, and `0` in both.

**Q4. Exact contribution formula?**  
For qualifying live `DIA>=5` tree rows: plot contribution is `sum(TPA_UNADJ × basis-matched official ADJ_FACTOR)`; 50-km mass is `sum(fold-specific TI × plot contribution)` over plot visits in the cell; normalize cell masses by their species/fold total. Original `EXPNS` is replaced, not multiplied again.

**Q5. Role of TPA_UNADJ?**  
It is the official trees-per-acre representation of the individual tree record, including tally geometry. It is not by itself a population total.

**Q6. How does partial effort enter?**  
Official `ADJ_FACTOR_SUBP/MACR` is the P1 point-estimator adjustment. Condition proportions are not extra per-tree weights. D10A derived partial-effort variables are P3 precision/QC metadata. P2 is rejected.

**Q7. Is authority sufficient for an exact D10C A2 rerun?**  
Yes. The crosswalk supplies original stratum, final block, fold, fold-specific TI, official adjustment factors, cell, and deterministic source identities without an invented block or effort rule.

## Boundary

STOP after this package. Mainline must audit before any D10C rerun.
