#!/usr/bin/env python3
"""Independent output-level validation for D08C2 corrected v01."""

import csv
import json
from collections import Counter
from pathlib import Path


ROOT = Path(r"C:\range_paper")
OUT = ROOT / "04_derived" / "d08c2_corrected_constructibility_v01"
QC = ROOT / "05_qc" / "d08c2_corrected_constructibility_v01"
ELIGIBLE = "D08C2_ELIGIBLE_FOR_OBSERVATION_AND_MEASUREMENT_GATE"
ONE = "ONE_DIRECTION_ONLY_DIAGNOSTIC"


def read(name):
    with (OUT / name).open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def integer(row, field):
    return int(row[field])


def expected_status(row):
    if row["d1_taxonomy_reconstruction"] != "PASS":
        return "FAIL_D1_TAXONOMIC_RECONSTRUCTION"
    if row["d2_target_native_f0_linkage"] != "PASS":
        return "FAIL_D2_TARGET_NATIVE_OR_F0_LINKAGE"
    d3a = integer(row, "n_legitimate_opportunity_A") > 0
    d3b = integer(row, "n_legitimate_opportunity_B") > 0
    d4a = integer(row, "n_encounter_plot_A") > 0
    d4b = integer(row, "n_encounter_plot_B") > 0
    a, b = d3a and d4a, d3b and d4b
    if a and b:
        return ELIGIBLE
    if a != b:
        return ONE
    if not d3a:
        return "FAIL_D3_NO_LEGITIMATE_OPPORTUNITY_A"
    if not d3b:
        return "FAIL_D3_NO_LEGITIMATE_OPPORTUNITY_B"
    if not d4a:
        return "FAIL_D4_NO_POSITIVE_ENCOUNTER_A"
    return "FAIL_D4_NO_POSITIVE_ENCOUNTER_B"


def main():
    eligibility = read("Q1_D08C2_SPECIES_ELIGIBILITY_LEDGER_v01.csv")
    fold = read("Q1_D08C2_SPECIES_FOLD_DIAGNOSTICS_v01.csv")
    exclusions = read("Q1_D08C2_EXCLUSION_REASON_LEDGER_v01.csv")
    aggregation = read("Q1_D08C2_ACCEPTED_SPECIES_AGGREGATION_AUDIT_v01.csv")
    opportunity = read("Q1_D08C2_OBSERVATION_OPPORTUNITY_AUDIT_v01.csv")
    input_qc = read("Q1_D08C2_INPUT_AND_SCHEMA_QC_v01.csv")
    crosswalk = read("Q1_D08C2_OPERATIONAL_NATIVE_STATE_CROSSWALK_v01.csv")
    mismatch = read("Q1_D08C2_F0_LINKAGE_MISMATCH_AUDIT_v01.csv")
    checks = []

    def check(name, condition, observed, expected):
        checks.append({"check": name, "status": "PASS" if condition else "FAIL", "observed": observed, "expected": expected})

    ids = [r["analysis_species_id"] for r in eligibility]
    check("eligibility_exactly_101_unique", len(eligibility) == 101 and len(set(ids)) == 101, f"rows={len(eligibility)};unique={len(set(ids))}", "101;101")
    check("fold_exactly_202_unique", len(fold) == 202 and len({(r['analysis_species_id'], r['fold']) for r in fold}) == 202, len(fold), 202)
    check("fold_values_A_B", {r["fold"] for r in fold} == {"A", "B"}, sorted({r['fold'] for r in fold}), ["A", "B"])
    reconstructed = {r["analysis_species_id"]: expected_status(r) for r in eligibility}
    mismatched_status = [sid for sid, value in reconstructed.items() if value != next(r["provisional_d08c2_status"] for r in eligibility if r["analysis_species_id"] == sid)]
    check("status_mechanically_reconstructed", not mismatched_status, mismatched_status, [])
    eligible_bad = [r["analysis_species_id"] for r in eligibility if (r["provisional_d08c2_status"] == ELIGIBLE) != (integer(r,"n_legitimate_opportunity_A")>0 and integer(r,"n_legitimate_opportunity_B")>0 and integer(r,"n_encounter_plot_A")>0 and integer(r,"n_encounter_plot_B")>0)]
    check("eligible_exact_bidirectional_rule", not eligible_bad, eligible_bad, [])
    check("no_final_cohort_flags", all(r["final_cohort_flag"] == "0" for r in eligibility), sum(r["final_cohort_flag"] != "0" for r in eligibility), 0)
    check("no_grid", all(r["grid_used"] == "NO" for r in eligibility), sum(r["grid_used"] != "NO" for r in eligibility), 0)
    check("no_abundance_or_occupancy_result", all(r["abundance_or_occupancy_result_used"] == "NO" for r in eligibility), sum(r["abundance_or_occupancy_result_used"] != "NO" for r in eligibility), 0)
    check("opportunity_48_state_x_2_fold", len(opportunity) == 96 and len({(r['state_fips'],r['fold']) for r in opportunity}) == 96, len(opportunity), 96)
    check("opportunity_positive_each_state_fold", all(integer(r,"legitimate_opportunity_plot_visit_count") > 0 for r in opportunity), sum(integer(r,"legitimate_opportunity_plot_visit_count") > 0 for r in opportunity), 96)
    check("effort_not_threshold", all(r["effort_metadata_used_as_threshold"] == "NO" for r in opportunity), sum(r["effort_metadata_used_as_threshold"] != "NO" for r in opportunity), 0)
    check("native_crosswalk_47_plus_alias", len(crosswalk) == 48 and sum(r["mapping_type"] == "EXACT_FULL_STATE_NAME" for r in crosswalk) == 47 and sum(r["mapping_type"] == "AUTHORIZED_EXPLICIT_ALIAS" for r in crosswalk) == 1, Counter(r["mapping_type"] for r in crosswalk), {"EXACT_FULL_STATE_NAME":47,"AUTHORIZED_EXPLICIT_ALIAS":1})
    check("f0_or_mismatch_retained", len(mismatch) == 4 and all(r["state_abbr"] == "OR" and r["retained_by_plt_cn"] == "YES" for r in mismatch), len(mismatch), 4)
    check("aggregation_includes_frozen_396", len(aggregation) >= 396 and sum(r["mapping_present_in_frozen_d08b1"] == "1" for r in aggregation) == 396, f"rows={len(aggregation)};mapped={sum(r['mapping_present_in_frozen_d08b1']=='1' for r in aggregation)}", "rows>=396;mapped=396")
    check("unmapped_not_silently_dropped", all(r["silent_drop_used"] == "NO" for r in aggregation), sum(r["silent_drop_used"] != "NO" for r in aggregation), 0)
    check("input_qc_all_pass", all(r["status"] == "PASS" for r in input_qc), Counter(r["status"] for r in input_qc), {"PASS": len(input_qc)})
    allowed_reasons = {"FAIL_D1_TAXONOMIC_RECONSTRUCTION", "FAIL_D2_TARGET_NATIVE_OR_F0_LINKAGE", "FAIL_D3_NO_LEGITIMATE_OPPORTUNITY_A", "FAIL_D3_NO_LEGITIMATE_OPPORTUNITY_B", "FAIL_D4_NO_POSITIVE_ENCOUNTER_A", "FAIL_D4_NO_POSITIVE_ENCOUNTER_B"}
    check("exclusion_reasons_structural_only", all(r["structural_reason_code"] in allowed_reasons and r["result_threshold_used"] == "NO" and r["final_cohort_decision"] == "NO" for r in exclusions), len(exclusions), "all structural")
    check("task_status_pass", any(r["check_id"] == "TASK_LEVEL_STATUS" and r["observed"] == "PASS_READY_FOR_MAINLINE_OBSERVATION_GATE_AUDIT" and r["status"] == "PASS" for r in input_qc), [r for r in input_qc if r["check_id"] == "TASK_LEVEL_STATUS"], "PASS_READY_FOR_MAINLINE_OBSERVATION_GATE_AUDIT")

    result = {
        "validation_status": "PASS" if all(r["status"] == "PASS" for r in checks) else "FAIL",
        "check_count": len(checks),
        "pass_count": sum(r["status"] == "PASS" for r in checks),
        "fail_count": sum(r["status"] == "FAIL" for r in checks),
        "provisional_status_counts": dict(sorted(Counter(r["provisional_d08c2_status"] for r in eligibility).items())),
        "checks": checks,
    }
    QC.mkdir(parents=True, exist_ok=True)
    (QC / "D08C2_CORRECTED_INDEPENDENT_VALIDATION_v01.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, default=dict) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2, default=dict))
    raise SystemExit(0 if result["validation_status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
