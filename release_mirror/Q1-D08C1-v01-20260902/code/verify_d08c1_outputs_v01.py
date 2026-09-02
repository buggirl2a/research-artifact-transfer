#!/usr/bin/env python3
"""Independent internal-consistency audit for frozen D08C1 v01 outputs."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


ROOT = Path(r"C:\range_paper")
OUT = ROOT / "99_tmp" / "d08c1_v01" / "outputs"
QC = ROOT / "99_tmp" / "d08c1_v01" / "qc"


def read(name):
    with (OUT / name).open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def integer(row, field):
    return int(float(row[field]))


def main():
    checks = []

    def check(name, passed, observed, expected):
        checks.append({"check": name, "status": "PASS" if passed else "FAIL", "observed": observed, "expected": expected})

    required = [
        "Q1_D08C1_SPECIES_GRAIN_CENSUS_v01.csv",
        "Q1_D08C1_50KM_FRONTIERS_v01.csv",
        "Q1_D08C1_NATIVE_STATE_AUDIT_v01.csv",
        "Q1_D08C1_CODE_AGGREGATION_AUDIT_v01.csv",
        "Q1_D08C1_NONANALYSIS_CODE_AUDIT_v01.csv",
        "Q1_D08C1_LITTLE_REVIEW_SURVIVOR_QUEUE_v01.csv",
        "Q1_D08C1_QC_v01.csv",
    ]
    missing = [name for name in required if not (OUT / name).is_file()]
    check("required_outputs_present", not missing, missing, [])

    census = read("Q1_D08C1_SPECIES_GRAIN_CENSUS_v01.csv")
    frontiers = read("Q1_D08C1_50KM_FRONTIERS_v01.csv")
    states = read("Q1_D08C1_NATIVE_STATE_AUDIT_v01.csv")
    codes = read("Q1_D08C1_CODE_AGGREGATION_AUDIT_v01.csv")
    excluded = read("Q1_D08C1_NONANALYSIS_CODE_AUDIT_v01.csv")
    queue = read("Q1_D08C1_LITTLE_REVIEW_SURVIVOR_QUEUE_v01.csv")
    qc_rows = read("Q1_D08C1_QC_v01.csv")
    crosswalk = read("Q1_D08C1_STATE_CROSSWALK_AUDIT_v01.csv")
    input_rows = read("Q1_D08C1_INPUT_AUDIT_v01.csv")
    trace = read("Q1_D08C1_TRACEABILITY_SAMPLE_v01.csv")

    key = lambda row: (row["analysis_species_id"], int(row["grain_km"]), row["census_view"], row["fold_scope"])
    census_by = {key(row): row for row in census}
    species_ids = sorted({row["analysis_species_id"] for row in census})
    check("complete_unique_census_keys", len(census) == 6498 and len(census_by) == 6498 and len(species_ids) == 361, [len(census), len(census_by), len(species_ids)], [6498, 6498, 361])

    exact = sum(row["mapping_type"] == "EXACT_FULL_STATE_NAME" for row in crosswalk)
    alias_rows = [row for row in crosswalk if row["mapping_type"] == "AUTHORIZED_EXPLICIT_ALIAS"]
    alias_ok = len(alias_rows) == 1 and all(alias_rows[0][key0] == value for key0, value in {
        "fia_state_code": "44", "fia_state_ab": "RI", "fia_state_name": "Rhode Island",
        "wcvp_area_code_l3": "RHO", "wcvp_area_name": "Rhode I.", "fuzzy_matching_used": "0",
    }.items())
    check("state_crosswalk_exact_and_single_authorized_alias", exact == 47 and alias_ok, [exact, alias_rows], "47 exact + RI/RHO alias")

    check("input_audit_all_pass", all(row["status"] == "PASS" for row in input_rows), Counter(row["status"] for row in input_rows), {"PASS": len(input_rows)})
    check("builder_qc_all_pass", all(row["status"] == "PASS" for row in qc_rows), Counter(row["status"] for row in qc_rows), {"PASS": len(qc_rows)})

    ordinary_code_total = sum(integer(row, "qualifying_tree_rows") for row in codes)
    census_total = sum(
        integer(row, "n_qualifying_tree_rows")
        for row in census
        if row["grain_km"] == "50" and row["census_view"] == "ALL_CONUS_OBSERVED" and row["fold_scope"] == "ALL"
    )
    check("ordinary_code_to_species_record_reconciliation", ordinary_code_total == census_total == 2477511, [ordinary_code_total, census_total], [2477511, 2477511])
    nonanalysis_total = sum(integer(row, "qualifying_tree_rows") for row in excluded)
    check("nonanalysis_record_reconciliation", nonanalysis_total == 5632, nonanalysis_total, 5632)

    fold_fail = 0
    for sid in species_ids:
        for grain in (25, 50, 75):
            for view in ("ALL_CONUS_OBSERVED", "WCVP_CONFIRMED_NATIVE_STATE"):
                total, a, b = (census_by[(sid, grain, view, fold)] for fold in ("ALL", "A", "B"))
                for field in (
                    "n_unique_physical_plot_lineages", "n_primary_measurements", "n_positive_plots",
                    "n_qualifying_tree_rows", "n_dbh_tree_rows", "n_drc_tree_rows",
                    "n_confirmed_native_state_tree_rows", "n_explicit_introduced_state_tree_rows",
                    "n_no_confirmed_native_or_introduced_state_tree_rows",
                ):
                    if integer(total, field) != integer(a, field) + integer(b, field):
                        fold_fail += 1
    check("A_B_add_to_ALL_for_additive_metrics", fold_fail == 0, fold_fail, 0)

    subset_fail = 0
    nonnative_native_nonzero = 0
    for sid in species_ids:
        for grain in (25, 50, 75):
            for fold in ("ALL", "A", "B"):
                all_row = census_by[(sid, grain, "ALL_CONUS_OBSERVED", fold)]
                native = census_by[(sid, grain, "WCVP_CONFIRMED_NATIVE_STATE", fold)]
                for field in ("n_unique_physical_plot_lineages", "n_sampled_cells", "n_positive_plots", "n_detected_cells", "n_qualifying_tree_rows"):
                    if integer(native, field) > integer(all_row, field):
                        subset_fail += 1
                if native["core_eligibility_status"] == "CONUS_NONNATIVE_CORE_INELIGIBLE" and (
                    integer(native, "n_unique_physical_plot_lineages") or integer(native, "n_qualifying_tree_rows")
                ):
                    nonnative_native_nonzero += 1
    check("native_view_subset_all_metrics", subset_fail == 0, subset_fail, 0)
    check("core_ineligible_species_have_empty_native_view", nonnative_native_nonzero == 0, nonnative_native_nonzero, 0)

    check("native_state_audit_complete", len(states) == 361 * 48, len(states), 361 * 48)
    state_class_counts = Counter(row["state_evidence_class"] for row in states)
    check("state_evidence_classes_closed", set(state_class_counts) == {"CONFIRMED_CURRENT_NATIVE", "EXPLICIT_INTRODUCED", "NO_CONFIRMED_NATIVE_OR_INTRODUCED_ROW"}, sorted(state_class_counts), ["CONFIRMED_CURRENT_NATIVE", "EXPLICIT_INTRODUCED", "NO_CONFIRMED_NATIVE_OR_INTRODUCED_ROW"])
    alias_status_inference = sum(row["status_inference_from_alias"] != "0" for row in states)
    check("RI_alias_has_no_status_inference", alias_status_inference == 0, alias_status_inference, 0)

    monotonic_fail = 0
    for view in {row["census_view"] for row in frontiers}:
        subset = [row for row in frontiers if row["census_view"] == view]
        for plot_min in sorted({integer(row, "positive_plots_each_fold_min") for row in subset}):
            values = [integer(row, "n_species_passing_sampling_frontier") for row in sorted((row for row in subset if integer(row, "positive_plots_each_fold_min") == plot_min), key=lambda row: integer(row, "detected_cells_each_fold_min"))]
            monotonic_fail += sum(values[index] < values[index + 1] for index in range(len(values) - 1))
        for cell_min in sorted({integer(row, "detected_cells_each_fold_min") for row in subset}):
            values = [integer(row, "n_species_passing_sampling_frontier") for row in sorted((row for row in subset if integer(row, "detected_cells_each_fold_min") == cell_min), key=lambda row: integer(row, "positive_plots_each_fold_min"))]
            monotonic_fail += sum(values[index] < values[index + 1] for index in range(len(values) - 1))
    check("frontier_counts_monotone", monotonic_fail == 0, monotonic_fail, 0)
    check("frontier_not_selected", len(frontiers) == 30 and all(row["final_threshold_selected"] == "0" for row in frontiers), [len(frontiers), sum(row["final_threshold_selected"] != "0" for row in frontiers)], [30, 0])

    expected_queue = set()
    for sid in species_ids:
        all_pass = min(integer(census_by[(sid, 50, "ALL_CONUS_OBSERVED", fold)], "n_detected_cells") for fold in ("A", "B")) >= 10
        native_pass = min(integer(census_by[(sid, 50, "WCVP_CONFIRMED_NATIVE_STATE", fold)], "n_detected_cells") for fold in ("A", "B")) >= 10
        if all_pass or native_pass:
            expected_queue.add(sid)
    actual_queue = {row["analysis_species_id"] for row in queue}
    check("survivor_queue_exact_union", actual_queue == expected_queue and len(actual_queue) == 231, [len(actual_queue), len(expected_queue), sorted(actual_queue ^ expected_queue)], [231, 231, []])
    check("queue_contains_no_Little_information", all(row["little_information_used"] == "0" for row in queue), sum(row["little_information_used"] != "0" for row in queue), 0)

    trace_species = {row["analysis_species_id"] for row in trace}
    trace_bad = sum(row["state_evidence_class"] != "CONFIRMED_CURRENT_NATIVE" for row in trace)
    check("trace_sample_native_and_twelve_species", len(trace_species) == 12 and trace_bad == 0, [len(trace_species), trace_bad], [12, 0])

    no_q1 = json.loads((QC / "D08C1_NO_Q1_OUTCOME_AUDIT_v01.json").read_text(encoding="utf-8"))
    prohibited_true = [key for key, value in no_q1.items() if key not in {"status", "prohibited_operations_performed"} and value is True]
    check("no_Q1_or_prohibited_operation", no_q1["status"] == "PASS" and not prohibited_true and not no_q1["prohibited_operations_performed"], prohibited_true, [])

    status = "PASS" if all(row["status"] == "PASS" for row in checks) else "FAIL"
    result = {"status": status, "check_count": len(checks), "checks": checks}
    (QC / "D08C1_INDEPENDENT_AUDIT_v01.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": status, "checks": len(checks), "failures": [row["check"] for row in checks if row["status"] == "FAIL"]}, indent=2))
    if status != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
