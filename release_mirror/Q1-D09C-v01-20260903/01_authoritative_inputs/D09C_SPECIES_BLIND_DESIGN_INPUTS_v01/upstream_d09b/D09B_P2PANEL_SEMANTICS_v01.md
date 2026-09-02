# D09B P2PANEL semantics factual closure v01

Date: 2026-09-02  
Status: PASS factual closure; no A/B partition selected.

## 1. Current official definition

Current FIADB Database Description v9.4 (August 2025), PLOT.P2PANEL:

> Phase 2 panel number. P2PANEL ranges from 1 to 5 for annual inventories and is null for periodic inventories. A panel is a sample in which the same elements are measured on two or more occasions. FIA divides plots in each State into five panels that can be used to independently sample the population.

Therefore:

- `P2PANEL` is a **panel identity**, not an inventory year, cycle number, or subpanel.
- The labels 1–5 repeat across States and across successive remeasurement cycles; they are not nationally synchronized calendar-year labels.
- The design assigns plots/hexagons to a panel and remeasures panels on a rotating schedule. Thus panel membership is intended as a persistent design assignment rather than a new random label at each cycle.
- Because historical panel integration, plot replacement and panel creep can occur, Q1 must verify lineage consistency (`PREV_PLT_CN` or equivalent plot identity) before treating panel membership as mechanically invariant in every historical record.

## 2. SUBPANEL is a critical current-schema exception

Current FIADB v9.4 `PLOT.SUBPANEL` states that some work units divide each of the five P2 panels into two subpanels (`SUBPANEL=1/2`), yielding ten subpanels. One subpanel is usually scheduled for measurement each year.

Current work units listed by FIA:

- RMRS: `SURVEY.RSCD=22`;
- PNWRS: `SURVEY.RSCD=26,27`;
- SRS: `SURVEY.RSCD=33`, only Oklahoma with `UNITCD >= 3`.

For CONUS this affects the RMRS States (AZ, CO, ID, MT, NV, NM, UT, WY), the PNWRS States (CA, OR, WA), and part of Oklahoma.

**Consequent fact:** `P2PANEL=1...5` cannot be treated nationally as “five interchangeable annual samples.” In subpaneling work units, one complete P2PANEL generally consists of two scheduled subpanels and can span more than one measurement year.

## 3. Relation to evaluation membership and time

An FIA evaluation is a statistical sample + target population + stratification used for an estimate. A 2023 evaluation group may contain 5, 7, 8, 9, 10, or even 11 measurement years in current metadata. The member-year list does **not** imply the same number of P2PANEL values.

`P2PANEL` alone does not determine:

- whether a plot measurement belongs to a particular EVALID;
- which calendar year that panel was actually completed;
- whether panel creep split completion across field seasons;
- which subpanel was scheduled/measured in subpaneling regions.

The current evaluation-group (`wc`) metadata exposes member years but not a panel-ID → measurement-year crosswalk. Therefore the exact 2023 State-specific panel/year map is **not closed from public evaluation-group metadata alone**.

### Required future bounded design audit (not executed here)

After mainline chooses how to handle the three States lacking 2023 groups, a design-only local audit should join the chosen EVALID membership to PLOT records and tabulate, without species outcomes:

`State × EVALID × P2PANEL × SUBPANEL × MEASYEAR/INVYR × estimation unit × poststratum`

and verify plot lineage does not occur in both proposed folds.

This is a design diagnostic, not a new eligibility census.

## 4. Practical interpretation for Q1 A/B

- Using complete panels is substantially closer to FIA's probability design than randomly discarding half the plots inside each P2PANEL.
- However, the correct atomic temporal/design unit is not uniform nationally because of `SUBPANEL`.
- A nationally uniform `odd P2PANEL vs even P2PANEL` rule is therefore **not yet justified**.
- No final panel partition is selected in D09B.

## Evidence class

Everything above through the official P2PANEL/SUBPANEL definitions is **OFFICIAL FIA FACT**.  
The recommendation to verify lineages and to treat the split atom as a mainline design decision is **Q1 DESIGN INFERENCE**.

Sources:
- FIADB Database Description/User Guide v9.4 (August 2025), PLOT fields P2PANEL and SUBPANEL.
- Bechtold & Patterson (eds.) 2005, SRS-GTR-80, sampling frame/plot design/panel chapters.
- FIA 2022 Sampling and Estimation Documentation, NRS-GTR-207.


## Evaluation group versus EVALID

The FIADB-API `wc` selector is an **evaluation-group code**, not proof that the group contains exactly one underlying numeric EVALID. This matters for exceptional structures such as Texas. Panel membership must ultimately be audited against the actual evaluation-group membership and population tables in the frozen FIADB database.
