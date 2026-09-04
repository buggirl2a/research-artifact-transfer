#!/usr/bin/env python3
"""Independent validation of the D10C authority-blocked deliverable."""

from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(r"C:\range_paper")
OUT = ROOT / "04_derived" / "d10c_fia_design_abundance_v01"
QC = ROOT / "05_qc" / "d10c_fia_design_abundance_v01"
STATUS = "INPUT_BLOCKED_ABUNDANCE_ESTIMATOR_AUTHORITY_FAILURE"


def read_csv(path):
    with Path(path).open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path, rows):
    rows = list(rows)
    with Path(path).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main():
    checks = []
    def add(check_id, passed, observed, expected):
        checks.append({"check_id": check_id, "status": "PASS" if passed else "FAIL", "observed": str(observed), "expected": str(expected)})

    inputs = read_csv(QC / "D10C_INPUT_IDENTITY_v01.csv")
    inventory = read_csv(QC / "D10C_INPUT_PACKAGE_MEMBER_INVENTORY_v01.csv")
    gaps = read_csv(OUT / "Q1_D10C_ESTIMATOR_AUTHORITY_GAP_AUDIT_v01.csv")
    disposition = read_csv(OUT / "Q1_D10C_REQUIRED_OUTPUT_DISPOSITION_v01.csv")
    terminal = json.loads((QC / "D10C_TERMINAL_STATUS_v01.json").read_text(encoding="utf-8"))
    note = (OUT / "Q1_D10C_RESULT_NOTE_v01.md").read_text(encoding="utf-8")

    add("THREE_INPUT_PACKAGES", len(inputs) == 3, len(inputs), 3)
    add("OUTER_AND_INTERNAL_INPUT_IDENTITY", all(row["status"] == "PASS" and row["internal_member_failures"] == "0" for row in inputs), sum(row["status"] == "PASS" for row in inputs), 3)
    add("INTERNAL_MEMBER_INVENTORY", len(inventory) == 88 and all(row["status"] == "PASS" for row in inventory), f"{len(inventory)}|{sum(row['status']=='PASS' for row in inventory)}", "88|88")
    gap_index = {row["check_id"]: row for row in gaps}
    expected_failures = {"TI_TABLE_CONTAINS_PLOT_IDENTIFIER", "D10A_F0_LAYOUT_CONTAINS_DESIGN_BLOCK_KEY", "NATIONWIDE_RAW_ASSIGNMENT_CROSSWALK", "AGGREGATE_LEDGER_IS_PLOT_BLOCK_CROSSWALK", "WV_MERGED_DOMAIN_PLOT_CROSSWALK", "PARTIAL_EFFORT_ABUNDANCE_CONTRIBUTION_RULE", "EXACT_NATIONWIDE_PLOT_TO_WEIGHT_JOIN"}
    observed_failures = {key for key, row in gap_index.items() if row["status"] == "FAIL"}
    add("EXPECTED_AUTHORITY_GAPS", observed_failures == expected_failures, ";".join(sorted(observed_failures)), ";".join(sorted(expected_failures)))
    add("PARTITIONS_AVAILABLE", gap_index["FROZEN_48_STATE_PARTITIONS"]["status"] == "PASS", gap_index["FROZEN_48_STATE_PARTITIONS"]["status"], "PASS")
    add("BLOCK_WEIGHTS_AVAILABLE", gap_index["FOLD_SPECIFIC_TI_BLOCK_WEIGHTS"]["status"] == "PASS", gap_index["FOLD_SPECIFIC_TI_BLOCK_WEIGHTS"]["status"], "PASS")
    add("EXACT_JOIN_NOT_CONSTRUCTIBLE", gap_index["EXACT_NATIONWIDE_PLOT_TO_WEIGHT_JOIN"]["status"] == "FAIL", gap_index["EXACT_NATIONWIDE_PLOT_TO_WEIGHT_JOIN"]["status"], "FAIL")
    add("SUBSTITUTION_NOT_AUTHORIZED", gap_index["SUBSTITUTE_ESTIMATOR_AUTHORIZED"]["authority_available"] == "NO", gap_index["SUBSTITUTE_ESTIMATOR_AUTHORIZED"]["authority_available"], "NO")
    add("TERMINAL_STATUS", terminal["terminal_status"] == STATUS, terminal["terminal_status"], STATUS)
    add("NO_SCIENTIFIC_PASS_FAIL", terminal["scientific_pass_fail"] == "NOT_DEFINED", terminal["scientific_pass_fail"], "NOT_DEFINED")
    add("NO_CALIBRATION_RUN", terminal["synthetic_calibration_run"] is False, terminal["synthetic_calibration_run"], False)
    add("RESULT_NOTE_Q1_TO_Q7", all(f"## Q{i}" in note for i in range(1, 8)), "PRESENT", "PRESENT")

    forbidden = [
        "Q1_D10C_SYNTHETIC_POPULATION_TRUTH_v01.csv",
        "Q1_D10C_SYNTHETIC_PLOT_OBSERVATIONS_v01.csv.gz",
        "Q1_D10C_A0_LATENT_ABUNDANCE_REFERENCE_v01.csv",
        "Q1_D10C_A1_BROKEN_RAW_COUNT_REFERENCE_v01.csv",
        "Q1_D10C_A2_DESIGN_BASED_CELL_MASS_ESTIMATES_v01.csv.gz",
        "Q1_D10C_ABUNDANCE_RECOVERY_METRICS_v01.csv",
        "Q1_D10C_SAMPLING_INTENSITY_LEAKAGE_AUDIT_v01.csv",
        "Q1_D10C_ORACLE_Q1_PRESERVATION_RESULTS_v01.csv",
        "Q1_D10C_STRONG_NULL_SEPARATION_v01.csv",
        "Q1_D10C_COMPARISON_WITH_D10B_v01.csv",
    ]
    absent = [name for name in forbidden if not (OUT / name).exists()]
    add("SCIENTIFIC_OUTPUTS_ABSENT_AFTER_GATE_FAILURE", len(absent) == len(forbidden), len(absent), len(forbidden))
    disposition_index = {row["required_output"]: row for row in disposition}
    add("DISPOSITION_RECORDS_ALL_SCIENTIFIC_ABSENCES", all(disposition_index[name]["disposition"] == "NOT_PRODUCED" for name in forbidden), "RECORDED", "RECORDED")
    add("REAL_Q1_NOT_RUN", "real Q1 was run" in note and "no synthetic abundance experiment" in note, "NO", "NO")

    status = "PASS" if all(row["status"] == "PASS" for row in checks) else "FAIL"
    write_csv(QC / "D10C_INDEPENDENT_VALIDATION_CHECKS_v01.csv", checks)
    (QC / "D10C_INDEPENDENT_VALIDATION_v01.json").write_text(json.dumps({"status": status, "checks": len(checks), "checks_passed": sum(row["status"] == "PASS" for row in checks), "terminal_status": STATUS, "scientific_calibration_run": False}, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": status, "checks": len(checks)}, indent=2))
    if status != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
