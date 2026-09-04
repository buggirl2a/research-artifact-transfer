# Q1 FIA Tally Protocol Crosswalk Rules v01

**TASK_ID:** `D08C2_TALLY_PROTOCOL_APPLICABILITY_CLOSURE_v01`  
**Terminal status:** `INPUT_BLOCKED_REQUIRED_OFFICIAL_ASSET_MISSING`  
**Scope:** official FIA protocol authority only. No corrected D08C2 execution; no survivor-result inspection; no occupancy/support/abundance/Q1 outcome.

## 1. Closed semantic facts

### 1.1 Applicability is a combination, not one national yes/no list
For CONUS NFI P2/P3 visits, the protocol authority is a combination of:

1. the visit's exact **Field Guide version** (`PLOT.MANUAL`);
2. the **Master Tree Species List / Mainland sub-list** applicable to that version;
3. the plot visit's **office-assigned National Forest System (NFS) regional boundary**;
4. the version-matched **NFS P2/3 exclusion sub-list** for that region; and
5. confirmation that the visit's `DESIGNCD` is within the protocol to which that list rule applies.

The national guide explicitly states that NFS regional boundaries do not always follow State boundaries. Therefore `STATECD` alone is not a valid substitute for NFS region. `SURVEY.RSCD` is an FIA work-unit identifier (RMRS, PNWRS, SRS, etc.), not the NFS Region 1/2/3/4/5/6/8/9/10 code used by the exclusion lists.

### 1.2 The public visit-version field is closed
`PLOT.MANUAL` is the official FIADB field-guide version number for the procedures used on that plot visit. `PLOT.DESIGNCD` identifies the plot design. Thus a future deterministic runner may use these fields as visit identity inputs, but neither field supplies the missing NFS exclusion-region code.

### 1.3 Legal tally rule
For a standard CONUS P2/P3 visit, a raw FIA `SPCD` is protocol-eligible only when official version-matched authority establishes that the species is on the applicable Mainland list and is **not** excluded by the visit's NFS P2/3 sub-list. If it is on that regional exclusion sub-list, `TALLY_ELIGIBLE=0`. If the required list version or NFS-region identity cannot be resolved, retain `UNKNOWN`.

The UNLISTED TREE protocol confirms that a species can be present on a broad FIA list yet be **not a legal tally tree** in a particular exclusion zone. Therefore current Master List membership by itself does not authorize a zero for all plot visits.

### 1.4 Manual/version dependence is real
Official FIADB v9.1 update notes document additions to, deletions from, and NFS-region reassignment within the NFS exclusion list. The 2017-2023 target interval spans national guide versions 7.2, 8.0, 9.0, 9.1, 9.2 and 9.3. Consequently, the future runner must match the authority to `PLOT.MANUAL`; it must not use a single current species list for every historical visit.

### 1.5 DRC/DBH treatment
Woodland species are FIA tally tree species measured at diameter at root collar (DRC). DRC status is therefore a **measurement-mode attribute**, not a blanket protocol exclusion. A woodland/DRC taxon still uses the same legal-tally applicability test. If otherwise legal, it remains eligible; if regionally excluded, it is ineligible there. This closure does not re-exclude DRC taxa.

## 2. Public-schema blocker

The official PNW field manuals expose a downloaded `NATIONAL FOREST REGION` plot code used specifically to enforce NFS tree-species exclusions. In those manuals, neighboring downloaded variables that are published in FIADB display explicit `[PLOT.<field>]` mappings; the NATIONAL FOREST REGION item does not show such a public mapping. A targeted audit of the current FIADB v9.4 documentation found no documented public `PLOT`/`PLOTSNAP` column for this office-assigned NFS exclusion-region code.

This is a documentation-bounded statement: **no documented public FIADB mapping was found**, not a claim that no internal FIA database field exists.

Because the NFS regional boundaries can cross State boundaries, neither `STATECD` nor `SURVEY.RSCD` may be substituted. A deterministic nationwide `T_ij` therefore remains blocked for species whose eligibility varies by NFS region unless an exact official visit-level NFS-region identity or official deterministic public crosswalk is supplied.

## 3. Missing authority required to instantiate the rule table

Two official inputs remain necessary before `Q1_FIA_TALLY_PROTOCOL_APPLICABILITY_v01.csv` can be expanded into a complete `SPCD × visit` 0/1 authority:

1. **Version-matched species-list/exclusion matrices** for every `PLOT.MANUAL` represented in frozen F0 visits. Current FIADB `REF_SPECIES` cannot supply the historical crosswalk because several older geographic/manual applicability fields, including `MANUAL_START` and `MANUAL_END`, were deleted in v9.2.
2. **Exact NFS region per plot visit**, or an official deterministic public crosswalk to the office-assigned NFS-region code.

The current official DataMart Tree Species List route was identified, but a current list alone is not sufficient for the historical 2017-2023 visit set. Its raw Box bytes were therefore not treated as a closure-completing canonical asset here.

## 4. Deterministic future rule order

The machine-readable rules file encodes the following order:

1. Match `PLOT.MANUAL` to its official species-list/exclusion version.
2. Confirm the visit is under the standard P2/P3 tally protocol or resolve a design-specific rule for `DESIGNCD`.
3. Resolve raw `SPCD` Mainland-list membership.
4. If not Mainland-legal: `TALLY_ELIGIBLE=0`.
5. If Mainland-legal and the species is never on any NFS exclusion sub-list in that version: `TALLY_ELIGIBLE=1` even if the exact NFS region is otherwise irrelevant.
6. If the species has region-specific exclusions, require exact visit NFS region.
7. On the visit's exclusion sub-list: `0`; otherwise `1`.
8. Any missing required authority: `UNKNOWN`.
9. Woodland/DRC modifies measurement mode only; it does not override steps 3-8.

## 5. Terminal decision

`INPUT_BLOCKED_REQUIRED_OFFICIAL_ASSET_MISSING`

The **protocol semantics are closed**, but the **operational nationwide applicability crosswalk is not**. The blocker is missing official input authority, not conceptual ambiguity. Corrected D08C2 v02 must not convert these unresolved cases to 0 or 1 unless mainline first closes the missing assets.

STOP.
