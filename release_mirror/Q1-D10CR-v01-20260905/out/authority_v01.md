# D10C abundance estimator authority v01

The accepted D10C-A package closes `PLT_CN -> selected stratum -> final block -> fold -> TI`. For this synthetic calibration, every generated record is live, `DIA=5.0`, and on subplot basis. The observed count is converted to adjusted plot trees per acre by `count * 6.018046 * ADJ_FACTOR_SUBP`; the 50-km cell population mass is the sum of that value times the plot's D09C fold-specific TI. Original `EXPNS`, condition proportions, plot-count divisors, state-average weights, inverse cell intensity, and inverse partial effort are excluded. Partial effort changes observation opportunity and remains QC metadata in the estimator.

The complete frozen equations and zero-exposure handling are in `control/contract_v01.md`. No estimator alternative was created.
