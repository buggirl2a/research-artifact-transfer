#!/usr/bin/env python3
"""Independent output-level verifier for D09C; does not query FIADB."""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(r"C:\range_paper")
WORK = ROOT / "99_tmp" / "d09c_v01"
OUT = WORK / "outputs"
QC = WORK / "qc"
ALLOWED = {
    "POP_EVAL_GRP", "POP_EVAL_TYP", "POP_EVAL", "POP_ESTN_UNIT",
    "POP_STRATUM", "POP_PLOT_STRATUM_ASSGN", "PLOT", "SURVEY",
}


def rows(name: str) -> list[dict]:
    with (OUT / name).open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def load_json(path: Path):
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def main() -> int:
    required = [
        "D09C_RESULT_NOTE_v01.md",
        "D09C_TEMPORAL_FRAME_AUDIT_v01.csv",
        "D09C_EVALID_COMPONENT_LEDGER_v01.csv",
        "D09C_PANEL_SUBPANEL_YEAR_LEDGER_v01.csv",
        "D09C_WHOLE_PANEL_PARTITION_CANDIDATES_v01.csv",
        "D09C_TOP_PARTITION_DIAGNOSTICS_v01.csv",
        "D09C_LINEAGE_CROSSFOLD_AUDIT_v01.csv",
        "D09C_TI_FOLD_WEIGHT_AUDIT_v01.csv",
        "D09C_MA_FOLD_WEIGHT_AUDIT_v01.csv",
        "D09C_DESIGN_CALIBRATION_AUDIT_v01.csv",
        "D09C_OPEN_DECISIONS_FOR_MAINLINE_v01.md",
        "D09C_INPUT_AUDIT_v01.csv",
        "D09C_TABLE_ACCESS_AUDIT_v01.csv",
        "D09C_SQL_LEDGER_v01.csv",
        "D09C_QC_v01.csv",
    ]
    checks = []

    def check(name, condition, observed, expected):
        checks.append({"check": name, "status": "PASS" if condition else "FAIL", "observed": observed, "expected": expected})

    missing = [name for name in required if not (OUT / name).is_file()]
    check("required_outputs_present", not missing, missing, [])

    temporal = rows("D09C_TEMPORAL_FRAME_AUDIT_v01.csv")
    frame_summary = rows("D09C_TEMPORAL_FRAME_SUMMARY_v01.csv")
    component = rows("D09C_EVALID_COMPONENT_LEDGER_v01.csv")
    panel_ledger = rows("D09C_PANEL_SUBPANEL_YEAR_LEDGER_v01.csv")
    candidates = rows("D09C_WHOLE_PANEL_PARTITION_CANDIDATES_v01.csv")
    top = rows("D09C_TOP_PARTITION_DIAGNOSTICS_v01.csv")
    lineage = rows("D09C_LINEAGE_CROSSFOLD_AUDIT_v01.csv")
    ti = rows("D09C_TI_FOLD_WEIGHT_AUDIT_v01.csv")
    ma = rows("D09C_MA_FOLD_WEIGHT_AUDIT_v01.csv")
    calibration = rows("D09C_DESIGN_CALIBRATION_AUDIT_v01.csv")
    input_audit = rows("D09C_INPUT_AUDIT_v01.csv")
    access = rows("D09C_TABLE_ACCESS_AUDIT_v01.csv")
    sql = rows("D09C_SQL_LEDGER_v01.csv")
    builder_qc = rows("D09C_QC_v01.csv")
    build = load_json(QC / "D09C_BUILD_SUMMARY_v01.json")
    no_q1 = load_json(QC / "D09C_NO_Q1_OUTCOME_AUDIT_v01.json")

    check("input_audit_all_pass", all(r["status"] == "PASS" for r in input_audit), Counter(r["status"] for r in input_audit), {"PASS": len(input_audit)})
    check("builder_qc_all_pass", all(r["status"] == "PASS" for r in builder_qc), Counter(r["status"] for r in builder_qc), {"PASS": len(builder_qc)})
    check("temporal_rows_96_and_48_each", len(temporal) == 96 and Counter(r["frame_id"] for r in temporal) == {"T1": 48, "T2": 48}, [len(temporal), Counter(r["frame_id"] for r in temporal)], [96, {"T1": 48, "T2": 48}])
    failed = {(r["frame_id"], r["state_abbr"]) for r in temporal if r["status"] == "FAIL"}
    check("frozen_local_frame_failures_exact", failed == {("T1", "CA"), ("T2", "CA"), ("T2", "OR"), ("T2", "WA")}, sorted(failed), [["T1", "CA"], ["T2", "CA"], ["T2", "OR"], ["T2", "WA"]])
    summary_status = {r["frame_id"]: r["frame_status"] for r in frame_summary}
    check("both_nationwide_frames_fail_without_substitution", summary_status == {"T1": "FAIL", "T2": "FAIL"}, summary_status, {"T1": "FAIL", "T2": "FAIL"})
    check("evalid_membership_not_guessed", all(r["evalid_membership_guessed"] == "0" for r in temporal + component), 0, 0)
    texas = {(r["frame_id"], r["component_evalid"], r["n_estimation_units"]) for r in component if r["state_abbr"] == "TX" and r["status"] == "PASS"}
    check("texas_actual_component_closure", texas == {("T1", "482201", "8"), ("T2", "482301", "8")}, sorted(texas), [["T1", "482201", "8"], ["T2", "482301", "8"]])

    by_sf = defaultdict(list)
    for row in candidates:
        by_sf[(row["frame_id"], row["state_abbr"])].append(row)
    check("candidate_rows_960_ten_per_state_frame", len(candidates) == 960 and len(by_sf) == 96 and all(len(v) == 10 for v in by_sf.values()), [len(candidates), len(by_sf), sorted(set(len(v) for v in by_sf.values()))], [960, 96, [10]])
    check("p2panel_never_split", all(r["p2panel_split_count"] == "0" for r in candidates), 0, 0)
    check("no_final_partition_selected", all(r["selected_as_final_partition"] == "0" for r in candidates + top), 0, 0)

    rank_errors = []
    for sf, group in by_sf.items():
        eligible = [r for r in group if r["eligible_for_ranking"] == "1"]
        if not eligible:
            continue
        expected = min(eligible, key=lambda r: (
            float(r["missing_parent_area_any_acres"]),
            float(r["design_block_representation_imbalance"]),
            float(r["temporal_center_abs_diff_years"]),
            float(r["plot_cell_imbalance"]),
            r["fold_A_panels"],
        ))
        selected = [r for r in eligible if r["top_diagnostic_candidate"] == "1" and r["rank_within_state_frame"] == "1"]
        if len(selected) != 1 or selected[0]["candidate_id"] != expected["candidate_id"]:
            rank_errors.append(sf)
    check("lexicographic_top_ranking_reproduces", not rank_errors, rank_errors, [])
    rankable_top = [r for r in top if r["candidate_id"]]
    check("rankable_top_state_frames_92", len(rankable_top) == 92, len(rankable_top), 92)
    check("top_crossfold_lineage_overlap_zero", all(r["crossfold_lineage_overlap_count"] == "0" for r in rankable_top), Counter(r["crossfold_lineage_overlap_count"] for r in rankable_top), {"0": 92})
    check("lineage_exceptions_explicitly_closed", len(lineage) == 96 and all(r["lineage_exception_flag"] == "0" for r in lineage), [len(lineage), Counter(r["lineage_exception_flag"] for r in lineage)], [96, {"0": 96}])

    check("panel_ledger_contains_zero_representation_rows", any(r["zero_panel_stratum_cell"] == "1" for r in panel_ledger), sum(r["zero_panel_stratum_cell"] == "1" for r in panel_ledger), ">0 explicit zeros")
    check("ti_fold_rows_match_build", len(ti) == build["ti_weight_rows"], len(ti), build["ti_weight_rows"])
    check("ma_fold_rows_match_build", len(ma) == build["ma_weight_rows"], len(ma), build["ma_weight_rows"])
    check("no_full_expns_reused_in_ti_or_ma", all(r["full_evaluation_expns_reused_as_final_fold_weight"] == "0" for r in ti) and all(r["full_evaluation_expns_reused_as_final_panel_weight"] == "0" for r in ma), 0, 0)
    check("constant_response_calibration_identity_pass", all(r["constant_identity_status"] == "PASS" for r in calibration), Counter(r["constant_identity_status"] for r in calibration), {"PASS": len(calibration)})
    check("calibration_rows_368", len(calibration) == 368, len(calibration), 368)

    observed_tables = {r["table"] for r in access if r["read_observed"] == "1"}
    check("table_access_exact_whitelist", observed_tables == ALLOWED, sorted(observed_tables), sorted(ALLOWED))
    check("sql_ledger_no_prohibited_marker", all(r["species_or_prohibited_marker_present"] == "0" for r in sql), Counter(r["species_or_prohibited_marker_present"] for r in sql), {"0": len(sql)})
    check("no_q1_or_downstream_operation", no_q1.get("status") == "PASS" and not no_q1.get("prohibited_operations") and not any(v for k, v in no_q1.items() if k not in {"status", "prohibited_operations"}), no_q1, "all operation flags false")
    check("execution_and_design_status_distinguished", build["execution_status"] == "PASS" and build["nationwide_design_feasibility"] == "FAIL", [build["execution_status"], build["nationwide_design_feasibility"]], ["PASS", "FAIL"])

    status = "PASS" if all(c["status"] == "PASS" for c in checks) else "FAIL"
    report = {
        "audit_id": "D09C_INDEPENDENT_OUTPUT_AUDIT_v01",
        "date": "2026-09-02",
        "status": status,
        "mode": "output-only verification; no FIADB query and no species data",
        "check_count": len(checks),
        "checks": checks,
    }
    (QC / "D09C_INDEPENDENT_AUDIT_v01.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": status, "check_count": len(checks), "failed": [c["check"] for c in checks if c["status"] == "FAIL"]}, ensure_ascii=False, indent=2))
    return 0 if status == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
