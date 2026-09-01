# D08B Taxonomy Correction — bounded factual closure v01

Date: 2026-09-02  
Scope: exactly 11 D08B identity cases.  
Status: **FACTUAL CLOSURE COMPLETE; STOP**

This work does **not** modify the frozen D08B master, rerun the 396-code build, reconstruct Little/USGS layers, merge FIA TREE records, recompute plots/grids, search new external range-map systems, or run real Q1.

## Outcome summary

- **RESOLVED: 10 / 11**
- **UNKNOWN: 1 / 11** — FIA code 6955, *Salix fragilis*
- No additive master patch has been applied.

## Resolved ambiguous cases

- 363 *Arbutus xalapensis* -> **Arbutus xalapensis Kunth**; the Andrews ex Hook. homonym is a different concept leading to *Comarostaphylis polifolia* subsp. *polifolia*.
- 372 *Betula lenta* -> **Betula lenta L.**; the Du Roi homonym leads to *Betula pubescens* var. *pubescens*.
- 744 *Populus heterophylla* -> **Populus heterophylla L.**; FIA separately codes plains cottonwood at 745, excluding the Du Roi/*P. deltoides* concept.
- 820 *Quercus laurifolia* -> **Quercus laurifolia Michx.**; the Miq. homonym belongs to a *Lithocarpus* concept.
- 822 *Quercus lyrata* -> **Quercus lyrata Walter**; FIA separately codes *Quercus lobata* at 821.

## D08B unresolved cases

- 840 *Quercus margarettiae* -> **Quercus margaretta (Ashe) Small**. Code/common-name continuity supports spelling normalization; preserve the FIA raw name.
- 6511 *Persea palustris* -> identity **RESOLVED** as *Persea palustris* (Raf.) Sarg.; WCVP/POWO routes it to *Tamala palustris* Raf., but that target is currently **Unplaced**, not Accepted. This does not create a deterministic Accepted replacement.
- 6955 *Salix fragilis* -> **UNKNOWN**. POWO has incompatible Host misapplied concepts and a separate accepted hybrid *Salix × fragilis* L. No code-6955-specific FIA author/reference concept was recovered, so the request's special rule forbids guessing.
- 8355 *Psidium cattleianum* -> **Psidium cattleyanum Sabine**, a spelling standardization with author/common-name concept preserved.
- 8563 *Schinus terebinthifolius* -> **Schinus terebinthifolia Raddi**, with FIA code/common-name/PLANTS-symbol concept and POWO author identity consistent.

## Hybrid case

- 143 *Pinus monophylla* var. *fallax* -> **Pinus × kohae Frankis**, WCVP/POWO Accepted hybrid taxon. POWO gives parentage *P. californiarum × P. edulis* and native distribution Arizona, Nevada, New Mexico, Utah. Core-analysis inclusion remains a mainline decision.

## Governance notes

1. Standard FIA `REF_SPECIES` does not expose author; where author is absent, FIA code + official common name + official scientific name and code-neighbor distinctions were used, followed by author-qualified WCVP/POWO.
2. No naked-name match was used as final evidence where homonyms or competing concepts existed.
3. *Persea palustris* is identity-resolved but lacks a current Accepted POWO target.
4. *Salix fragilis* remains UNKNOWN deliberately.
5. Existing D08B frozen outputs remain immutable.

STOP. Return to Q1 scientific mainline for any additive correction-patch decision.
