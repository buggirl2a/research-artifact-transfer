#!/usr/bin/env python3
"""D10C frozen estimator-authority gate.

This runner performs input/package and schema audits only. It intentionally
does not generate synthetic outcomes or compute A0/A1/A2 because the exact
nationwide plot-to-effective-design-block authority is absent.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import platform
import sys
import zipfile
from pathlib import Path


ROOT = Path(r"C:\range_paper")
TASK = "D10C_FIA_DESIGN_BASED_ABUNDANCE_MEASUREMENT_CALIBRATION_v01"
STATUS = "INPUT_BLOCKED_ABUNDANCE_ESTIMATOR_AUTHORITY_FAILURE"
OUT = ROOT / "04_derived" / "d10c_fia_design_abundance_v01"
QC = ROOT / "05_qc" / "d10c_fia_design_abundance_v01"

INPUTS = {
    "D10A": {
        "path": ROOT / "10_archive" / "d10a_real_layout_nonoracle_v01" / "Q1_D10A_REAL_LAYOUT_NONORACLE_OBSERVATION_CALIBRATION_REPRODUCIBLE_v01.zip",
        "sha256": "20e5d3ed33df6414b72a6e679d5349f3b10fe6397ce73f98b51d0bcc96033013",
        "root": "Q1_D10A_REAL_LAYOUT_NONORACLE_OBSERVATION_CALIBRATION_REPRODUCIBLE_v01/",
    },
    "D10B": {
        "path": ROOT / "10_archive" / "d10b_oracle_source_decomposition_v01" / "Q1_D10B_ORACLE_SUPPORT_DOWNSTREAM_SOURCE_DECOMPOSITION_REPRODUCIBLE_v01.zip",
        "sha256": "cb041fca5897f31c8ea0bf2a3b29a262a5c83ef44bdfda9a37a0394cfc7cafeb",
        "root": "Q1_D10B_ORACLE_SUPPORT_DOWNSTREAM_SOURCE_DECOMPOSITION_REPRODUCIBLE_v01/",
    },
    "D09C": {
        "path": ROOT / "10_archive" / "d09c_t2_final_correction_v02" / "Q1_D09C_T2_FINAL_CORRECTION_REPRODUCIBLE_v02.zip",
        "sha256": "07cb461121c71ef46990fea3e0cf9d8f139fd873234b9f57910ff10c7c33752f",
        "root": "Q1_D09C_T2_FINAL_CORRECTION_REPRODUCIBLE_v02/",
    },
}


def sha256_file(path: Path, chunk=8 * 1024 * 1024):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(chunk), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256_bytes(value: bytes):
    return hashlib.sha256(value).hexdigest()


def write_csv(path: Path, rows, fields=None):
    rows = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    if fields is None:
        fields = list(rows[0])
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_text(path: Path, value: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8", newline="\n")


def csv_rows_from_bytes(payload: bytes):
    return list(csv.DictReader(io.StringIO(payload.decode("utf-8-sig"))))


def header_from_member(archive, member):
    payload = archive.read(member)
    with io.StringIO(payload.decode("utf-8-sig")) as handle:
        return next(csv.reader(handle))


def verify_package(role, spec):
    inventory = []
    outer_sha = sha256_file(spec["path"])
    outer_ok = outer_sha == spec["sha256"]
    with zipfile.ZipFile(spec["path"]) as archive:
        names = set(archive.namelist())
        sums_member = spec["root"] + "SHA256SUMS.csv"
        sums = csv_rows_from_bytes(archive.read(sums_member))
        for row in sums:
            member = spec["root"] + row["relative_path"]
            if member not in names:
                inventory.append({"input_role": role, "relative_path": row["relative_path"], "expected_size_bytes": row["size_bytes"], "observed_size_bytes": "", "expected_sha256": row["sha256"], "observed_sha256": "", "status": "FAIL_MISSING"})
                continue
            payload = archive.read(member)
            observed = sha256_bytes(payload)
            passed = len(payload) == int(row["size_bytes"]) and observed == row["sha256"]
            inventory.append({"input_role": role, "relative_path": row["relative_path"], "expected_size_bytes": row["size_bytes"], "observed_size_bytes": len(payload), "expected_sha256": row["sha256"], "observed_sha256": observed, "status": "PASS" if passed else "FAIL_MISMATCH"})
    return outer_sha, outer_ok, inventory


def inspect_authority():
    d10a_spec, d09c_spec = INPUTS["D10A"], INPUTS["D09C"]
    with zipfile.ZipFile(d10a_spec["path"]) as d10a, zipfile.ZipFile(d09c_spec["path"]) as d09c:
        d10a_layout_member = d10a_spec["root"] + "02_outputs/Q1_D10A_REAL_F0_OPPORTUNITY_LAYOUT_v01.csv"
        d09c_ti_member = d09c_spec["root"] + "02_outputs/Q1_D09C_T2_FINAL_FOLD_SPECIFIC_TI_DESIGN_v02.csv"
        d09c_part_member = d09c_spec["root"] + "02_outputs/Q1_D09C_T2_FINAL_RULE_SELECTED_PARTITIONS_v02.csv"
        layout_header = header_from_member(d10a, d10a_layout_member)
        ti_header = header_from_member(d09c, d09c_ti_member)
        partition_rows = csv_rows_from_bytes(d09c.read(d09c_part_member))
        ti_rows = csv_rows_from_bytes(d09c.read(d09c_ti_member))
        predecessor_member = next(name for name in d09c.namelist() if name.endswith("Q1_D09C_T2_BOUNDED_COMPLETION_REPRODUCIBLE_v01.zip"))
        predecessor_payload = d09c.read(predecessor_member)
    with zipfile.ZipFile(io.BytesIO(predecessor_payload)) as predecessor:
        predecessor_names = predecessor.namelist()
        raw_state_prefixes = sorted({Path(name).name.split("_")[0] for name in predecessor_names if "/ca_or_wa_raw_design_zips/" in name and name.endswith("_POP_PLOT_STRATUM_ASSGN.zip")})
        panel_member = next(name for name in predecessor_names if name.endswith("D09C_PANEL_SUBPANEL_YEAR_LEDGER_v01.csv"))
        lineage_member = next(name for name in predecessor_names if name.endswith("D09C_LINEAGE_CROSSFOLD_AUDIT_v01.csv"))
        panel_header = header_from_member(predecessor, panel_member)
        lineage_header = header_from_member(predecessor, lineage_member)
    return {
        "d10a_layout_header": layout_header,
        "d09c_ti_header": ti_header,
        "d09c_partition_rows": partition_rows,
        "d09c_ti_rows": ti_rows,
        "predecessor_raw_assignment_states": raw_state_prefixes,
        "panel_ledger_header": panel_header,
        "lineage_audit_header": lineage_header,
    }


def build_gap_rows(evidence):
    layout = set(evidence["d10a_layout_header"])
    ti = set(evidence["d09c_ti_header"])
    panel = set(evidence["panel_ledger_header"])
    lineage = set(evidence["lineage_audit_header"])
    partitions = evidence["d09c_partition_rows"]
    ti_rows = evidence["d09c_ti_rows"]
    rows = []
    def add(check_id, required, available, status, observed, consequence):
        rows.append({"check_id": check_id, "required_for_exact_A2": required, "authority_available": available, "status": status, "observed_evidence": observed, "consequence": consequence})
    add("FROZEN_48_STATE_PARTITIONS", "YES", "YES" if len(partitions) == 48 else "NO", "PASS" if len(partitions) == 48 else "FAIL", f"partition_rows={len(partitions)}", "AB/BA whole-panel identity is available")
    add("FOLD_SPECIFIC_TI_BLOCK_WEIGHTS", "YES", "YES" if {"effective_design_block_id", "fold_specific_ti_expansion_acres_per_plot"} <= ti else "NO", "PASS" if {"effective_design_block_id", "fold_specific_ti_expansion_acres_per_plot"} <= ti else "FAIL", f"ti_rows={len(ti_rows)}; formula=effective block population area / actual fold sample count", "Block-level point-estimator weights are available")
    add("TI_TABLE_CONTAINS_PLOT_IDENTIFIER", "YES", "YES" if {"plot_cn", "plt_cn"} & {name.lower() for name in ti} else "NO", "PASS" if {"plot_cn", "plt_cn"} & {name.lower() for name in ti} else "FAIL", "TI table is block-level and has no PLT_CN", "Cannot attach each TI block weight to each F0 plot")
    block_fields = {"stratum_cn", "estn_unit_cn", "effective_design_block_id", "assignment_cn"}
    add("D10A_F0_LAYOUT_CONTAINS_DESIGN_BLOCK_KEY", "YES", "YES" if block_fields & {name.lower() for name in layout} else "NO", "PASS" if block_fields & {name.lower() for name in layout} else "FAIL", "D10A layout has plot_cn/cell_50km/fold but no stratum, estimation-unit, assignment, or effective-block key", "D10A plot rows cannot be joined to D09C TI blocks")
    raw_states = evidence["predecessor_raw_assignment_states"]
    add("NATIONWIDE_RAW_ASSIGNMENT_CROSSWALK", "YES", "YES" if len(raw_states) == 48 else "NO", "PASS" if len(raw_states) == 48 else "FAIL", f"embedded POP_PLOT_STRATUM_ASSGN raw states={','.join(raw_states)}; coverage={len(raw_states)}/48", "Only CA/OR/WA can be reconstructed from embedded raw assignments")
    add("AGGREGATE_LEDGER_IS_PLOT_BLOCK_CROSSWALK", "YES", "YES" if ({"plot_cn", "plt_cn"} & {x.lower() for x in panel}) and "stratum_cn" in {x.lower() for x in panel} else "NO", "FAIL", "Panel/subpanel/year ledger has stratum_cn but no individual plot identifier; lineage audit has plot_visit_cns but no stratum/effective block", "Two aggregate ledgers cannot be joined row-exactly without an unpublished mapping")
    add("WV_MERGED_DOMAIN_PLOT_CROSSWALK", "YES", "NO", "FAIL", "Final package publishes merged block totals but not a nationwide plot-to-final-effective-block crosswalk", "The R2 WV final block cannot be assigned to all relevant F0 plot rows from package outputs alone")
    add("PARTIAL_EFFORT_ABUNDANCE_CONTRIBUTION_RULE", "YES_IF_USED_BY_REAL_ESTIMATOR", "NO", "FAIL", "D10A publishes partial_sampling_effort; D09C freezes TI block weights but no official partial-effort-to-abundance-response contribution rule", "G3 cannot be implemented as the exact intended real branch")
    add("EXACT_NATIONWIDE_PLOT_TO_WEIGHT_JOIN", "YES", "NO", "FAIL", "No shared package key closes PLT_CN -> selected effective_design_block_id -> fold-specific TI weight for 48 states", "A2 is not constructible under frozen authority")
    add("SUBSTITUTE_ESTIMATOR_AUTHORIZED", "NO", "NO", "PASS", "Contract prohibits state-average weights, inverse plots per cell, simple means, raw counts, and ad hoc normalization", "The branch must stop rather than fill the authority gap")
    return rows


def authority_note(evidence):
    return f"""# D10C abundance-estimator authority audit v01

Terminal status: `{STATUS}`

## Authoritative logic that is available

The accepted D09C design freezes fold-specific TI at the effective-design-block level. For selected fold `f` and effective block `h`, every sampled plot in that block would receive:

`w_hf = effective block population area / actual fold sample count`.

The final table contains {len(evidence['d09c_ti_rows']):,} block × fold rows, preserves population area, and explicitly forbids reuse of full-evaluation EXPNS as the final fold weight. The 48 selected whole-panel partitions are also present.

## Missing authority that blocks A2

The final TI table has no plot identifier. The D10A F0 layout has `plot_cn`, `cell_50km`, and `fold`, but no assignment, stratum, estimation-unit, or effective-design-block identifier. The predecessor aggregate panel ledger has stratum identifiers without individual plot identifiers; its lineage audit has plot-visit lists without design-block identifiers. Embedded raw `POP_PLOT_STRATUM_ASSGN` design ZIPs cover only {', '.join(evidence['predecessor_raw_assignment_states'])} ({len(evidence['predecessor_raw_assignment_states'])}/48 states), not the national F0 frame. The WV merged-domain output is likewise not a complete plot-level crosswalk.

D09C also does not freeze how D10A's partial condition/subplot effort should enter the intended real abundance response or per-plot contribution. Consequently the packages do not define the exact nationwide join:

`F0 PLT_CN -> selected final effective design block -> fold-specific TI weight -> real-branch plot contribution`.

## Governance consequence

Using state-average weights, inverse cell sample size, coordinate matching, local un-packaged FIA tables, or any newly invented effort correction would change estimator authority. The D10C contract forbids those substitutions. Therefore no T_i rule was activated, no synthetic observations were generated, and A0/A1/A2 recovery or downstream results were computed.

Mainline can unblock D10C by freezing a nationwide plot-level selected-design crosswalk and the exact plot-contribution/partial-effort rule. This audit does not prescribe which rule to choose.
"""


def result_note():
    return f"""# D10C result note v01 — estimator-authority gate

Terminal status: `{STATUS}`

No scientific PASS/FAIL is defined. No abundance estimator was selected, repaired, or evaluated.

## Q1 — A2 recovery of latent cell mass

Not evaluated. Exact A2 could not be attached to the nationwide F0 plot layout from the frozen packages.

## Q2 — A2 improvement over A1

Not evaluated. Generating A1 while A2 was unauthorized would not answer the contracted comparison.

## Q3 — Dependence on plot count, effort, panel, state, MANUAL, or DESIGNCD

Not evaluated. The missing plot-to-final-design-block crosswalk and partial-effort contribution rule prevent an exact leakage audit.

## Q4 — Recovery of STRONG greater than PAIRED_NULL

Not evaluated. The bounded downstream audit was not entered.

## Q5 — PAIRED_NULL proximity to oracle null

Not evaluated. No A2 map exists under current authority.

## Q6 — AB/BA consistency

Not evaluated. Although the selected AB/BA partitions and block-level fold weights exist, the nationwide plot-level weight join does not.

## Q7 — Evidence of insufficiency for the next stage

Yes at the authority/constructibility level, not as a scientific performance failure. D09C supplies block-level TI weights but not the complete national `PLT_CN -> final effective design block` crosswalk; D10A supplies F0 plot/cell/fold rows but no block key; embedded raw assignments cover only CA/OR/WA; and no frozen partial-effort abundance-contribution rule is present. The contract therefore requires stopping before calibration.

Required mainline action: freeze and deliver the missing nationwide plot-to-final-block crosswalk and exact plot-contribution/partial-effort rule, or explicitly authorize a revised estimator contract.

STOP: no synthetic abundance experiment, support recovery, D10D, real species, real abundance, cohort, or real Q1 was run.
"""


def output_disposition():
    entries = [
        ("Q1_D10C_ABUNDANCE_ESTIMATOR_AUTHORITY_v01.md", "PRODUCED", "Authority audit is the blocking deliverable"),
        ("Q1_D10C_SYNTHETIC_POPULATION_TRUTH_v01.csv", "NOT_PRODUCED", "Authority gate failed before T_i activation or synthetic truth materialization"),
        ("Q1_D10C_SYNTHETIC_PLOT_OBSERVATIONS_v01.csv.gz", "NOT_PRODUCED", "Exact A2 observation chain is not authorized/constructible"),
        ("Q1_D10C_A0_LATENT_ABUNDANCE_REFERENCE_v01.csv", "NOT_PRODUCED", "Calibration experiment not entered"),
        ("Q1_D10C_A1_BROKEN_RAW_COUNT_REFERENCE_v01.csv", "NOT_PRODUCED", "Calibration experiment not entered"),
        ("Q1_D10C_A2_DESIGN_BASED_CELL_MASS_ESTIMATES_v01.csv.gz", "NOT_PRODUCED", "Exact plot-to-weight join absent"),
        ("Q1_D10C_ABUNDANCE_RECOVERY_METRICS_v01.csv", "NOT_PRODUCED", "No authorized A2 estimates"),
        ("Q1_D10C_SAMPLING_INTENSITY_LEAKAGE_AUDIT_v01.csv", "NOT_PRODUCED", "No authorized A2 estimates"),
        ("Q1_D10C_ORACLE_Q1_PRESERVATION_RESULTS_v01.csv", "NOT_PRODUCED", "Downstream audit not entered"),
        ("Q1_D10C_STRONG_NULL_SEPARATION_v01.csv", "NOT_PRODUCED", "Downstream audit not entered"),
        ("Q1_D10C_COMPARISON_WITH_D10B_v01.csv", "NOT_PRODUCED", "No D10C A2 result exists"),
        ("Q1_D10C_RESULT_NOTE_v01.md", "PRODUCED", "Direct Q1-Q7 blocked-state answers"),
        ("complete reproducibility code", "PRODUCED", "Authority-gate audit, validation, and packaging code"),
        ("SHA256SUMS.csv", "PRODUCED_AT_PACKAGE_STAGE", "Package checksum manifest"),
        ("TRANSFER_MANIFEST_v01.csv", "PRODUCED_AT_PACKAGE_STAGE", "Relay v0.2.2 native manifest"),
        ("REGISTRY_DELTA_v01.csv", "PRODUCED", "Blocked-state registry delta"),
    ]
    return [{"required_output": name, "disposition": status, "reason": reason, "terminal_status": STATUS} for name, status, reason in entries]


def registry_delta():
    fields = ["TASK_ID", "input_authority_commit_version", "exact_source_path_or_release_identity", "sha256", "bytes", "status", "scientific_output_changed", "publication_candidate", "Methods_role", "Data_role", "Code_role", "QC_role"]
    entries = [
        ("AUTH_CONTRACT", ROOT / "00_control" / "Q1_D10C_FIA_DESIGN_BASED_ABUNDANCE_MEASUREMENT_CALIBRATION_CONTRACT_v01.md", "FROZEN_INPUT_AUTHORITY"),
        ("AUTH_EXECUTION_FREEZE", ROOT / "00_control" / "D10C_ABUNDANCE_ESTIMATOR_AUTHORITY_GATE_EXECUTION_FREEZE_v01.md", "FROZEN_INPUT_AUTHORITY"),
    ] + [("AUTH_" + role, spec["path"], "FROZEN_PREDECESSOR_AUTHORITY") for role, spec in INPUTS.items()]
    entries += [(STATUS, OUT / "Q1_D10C_ABUNDANCE_ESTIMATOR_AUTHORITY_v01.md", "AUTHORITY_FAILURE_AUDIT"), (STATUS, OUT / "Q1_D10C_ESTIMATOR_AUTHORITY_GAP_AUDIT_v01.csv", "AUTHORITY_FAILURE_AUDIT"), (STATUS, OUT / "Q1_D10C_RESULT_NOTE_v01.md", "BLOCKED_RESULT_NOTE")]
    rows = []
    for version, path, role in entries:
        rows.append({"TASK_ID": TASK, "input_authority_commit_version": version, "exact_source_path_or_release_identity": str(path), "sha256": sha256_file(path), "bytes": path.stat().st_size, "status": STATUS if version == STATUS else "PASS_INPUT_IDENTITY", "scientific_output_changed": "NO_SCIENTIFIC_CALIBRATION_NOT_RUN", "publication_candidate": "NO", "Methods_role": role, "Data_role": "SYNTHETIC_CALIBRATION_NOT_RUN", "Code_role": "AUTHORITY_GATE_ONLY", "QC_role": "TRACEABILITY"})
    write_csv(OUT / "REGISTRY_DELTA_v01.csv", rows, fields)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    QC.mkdir(parents=True, exist_ok=True)
    input_rows, inventory = [], []
    for role, spec in INPUTS.items():
        observed, outer_ok, member_rows = verify_package(role, spec)
        input_rows.append({"input_role": role, "path": str(spec["path"]), "size_bytes": spec["path"].stat().st_size, "expected_sha256": spec["sha256"], "observed_sha256": observed, "outer_identity_status": "PASS" if outer_ok else "FAIL", "internal_member_checks": len(member_rows), "internal_member_failures": sum(row["status"] != "PASS" for row in member_rows), "status": "PASS" if outer_ok and all(row["status"] == "PASS" for row in member_rows) else "FAIL"})
        inventory.extend(member_rows)
    if any(row["status"] != "PASS" for row in input_rows):
        raise RuntimeError("INPUT_BLOCKED_FROZEN_DESIGN_IDENTITY_FAILURE")
    evidence = inspect_authority()
    gaps = build_gap_rows(evidence)
    exact_join = next(row for row in gaps if row["check_id"] == "EXACT_NATIONWIDE_PLOT_TO_WEIGHT_JOIN")
    if exact_join["status"] == "PASS":
        raise RuntimeError("Authority audit unexpectedly passed; a new execution freeze is required before any experiment")

    write_text(OUT / "Q1_D10C_ABUNDANCE_ESTIMATOR_AUTHORITY_v01.md", authority_note(evidence))
    write_csv(OUT / "Q1_D10C_ESTIMATOR_AUTHORITY_GAP_AUDIT_v01.csv", gaps)
    write_csv(OUT / "Q1_D10C_REQUIRED_OUTPUT_DISPOSITION_v01.csv", output_disposition())
    write_text(OUT / "Q1_D10C_RESULT_NOTE_v01.md", result_note())
    write_csv(QC / "D10C_INPUT_IDENTITY_v01.csv", input_rows)
    write_csv(QC / "D10C_INPUT_PACKAGE_MEMBER_INVENTORY_v01.csv", inventory)
    write_json(QC / "D10C_BUILD_SUMMARY_v01.json", {"task_id": TASK, "terminal_status": STATUS, "input_packages": len(input_rows), "input_internal_members_checked": len(inventory), "authority_gap_checks": len(gaps), "authority_gap_failures": sum(row["status"] == "FAIL" for row in gaps), "d09c_ti_rows": len(evidence["d09c_ti_rows"]), "d09c_partition_rows": len(evidence["d09c_partition_rows"]), "embedded_raw_assignment_state_coverage": evidence["predecessor_raw_assignment_states"], "synthetic_calibration_run": False, "a0_a1_a2_outputs_run": False, "downstream_audit_run": False, "network_used": False, "real_species_read": False, "real_q1_run": False})
    write_json(QC / "D10C_ENVIRONMENT_v01.json", {"python": sys.version, "platform": platform.platform(), "executable": sys.executable, "working_directory": str(ROOT), "network_used": False})
    write_json(QC / "D10C_TERMINAL_STATUS_v01.json", {"task_id": TASK, "terminal_status": STATUS, "scientific_pass_fail": "NOT_DEFINED", "abundance_model_selected": False, "synthetic_calibration_run": False, "real_q1_run": False})
    write_text(QC / "D10C_IMPLEMENTATION_LOG_v01.md", f"# D10C implementation log\n\nThe frozen input and estimator-authority gate was executed. D10A, D10B, and D09C outer and internal package checks passed. The exact nationwide F0 plot-to-final-effective-design-block join and partial-effort abundance-contribution authority were absent, so the contract-required terminal state `{STATUS}` was recorded before any synthetic calibration result. No substitute estimator was constructed.\n")
    registry_delta()
    summary = {"task_id": TASK, "terminal_status": STATUS, "input_identity": "PASS", "scientific_calibration_run": False, "authority_gap_failures": sum(row["status"] == "FAIL" for row in gaps)}
    sys.stdout.write(json.dumps(summary, indent=2) + "\n")


if __name__ == "__main__":
    main()
