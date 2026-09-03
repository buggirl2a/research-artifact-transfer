from __future__ import annotations

import csv
import json
import math
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(r"C:\range_paper")
OUT = ROOT / "04_derived" / "d09c_t2_completion_v01"
QC = ROOT / "05_qc" / "d09c_t2_completion_v01"
TOL = 1e-8


def rows(name):
    with (OUT / name).open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def f(row, key):
    return float(row[key])


def i(row, key):
    return int(row[key])


def rank_key(row):
    return (
        -i(row, "candidate_design_valid"),
        i(row, "true_eu_level_block_count"),
        i(row, "area_preservation_failure_count"),
        i(row, "unresolved_design_key_count"),
        f(row, "area_weighted_effective_block_imbalance"),
        f(row, "max_effective_block_imbalance"),
        f(row, "area_weighted_estimation_unit_imbalance"),
        f(row, "absolute_fold_A_plot_share_minus_0_4"),
        f(row, "temporal_center_abs_diff_years"),
        f(row, "temporal_distribution_l1_distance"),
        f(row, "temporal_sd_abs_diff_years"),
        tuple(int(x) for x in row["fold_A_panels"].split("-")),
    )


def main():
    frame = rows("Q1_D09C_T2_NATIONAL_FRAME_COMPLETION_v01.csv")
    candidates = rows("Q1_D09C_T2_ALL_PARTITION_CANDIDATES_v01.csv")
    tops = rows("Q1_D09C_T2_RULE_SELECTED_PARTITIONS_v01.csv")
    ti = rows("Q1_D09C_T2_FOLD_SPECIFIC_TI_DESIGN_v01.csv")
    coarse = rows("Q1_D09C_T2_SYMMETRIC_COARSENING_AUDIT_v01.csv")
    wv = rows("Q1_D09C_T2_WV_AUDIT_v01.csv")
    orm = rows("Q1_D09C_T2_OR_412301_MISMATCH_AUDIT_v01.csv")
    ma = rows("Q1_D09C_T2_MA_SENSITIVITY_FEASIBILITY_v01.csv")
    builder_qc = rows("Q1_D09C_T2_COMPLETION_QC_v01.csv")

    checks = []
    def check(name, ok, observed, expected):
        checks.append({"check": name, "status": "PASS" if ok else "FAIL", "observed": observed, "expected": expected})

    check("required_output_rows", len(frame) == 48 and len(candidates) == 480 and len(tops) == 48 and len(ma) == 96, {"frame": len(frame), "candidates": len(candidates), "tops": len(tops), "ma": len(ma)}, {"frame": 48, "candidates": 480, "tops": 48, "ma": 96})
    check("frame_evalids_real", all(r["component_evalid"] and r["required_eval_typ"] == "EXPVOL" for r in frame), sum(bool(r["component_evalid"]) for r in frame), 48)
    new_evalids = {r["state_abbr"]: int(r["component_evalid"]) for r in frame if r["state_abbr"] in {"CA", "OR", "WA"}}
    check("new_evalids_exact", new_evalids == {"CA": 62301, "OR": 412301, "WA": 532301}, new_evalids, {"CA": 62301, "OR": 412301, "WA": 532301})
    check("five_panel_and_ten_candidate_closure", all(i(r, "five_panel_complete") == 1 and i(r, "candidate_count") == 10 for r in frame), "all rows", "five panels; ten candidates")

    by_state = defaultdict(list)
    for r in candidates:
        by_state[r["state_abbr"]].append(r)
    ranking_ok = True
    for state, rs in by_state.items():
        expected = sorted(rs, key=rank_key)
        ranking_ok &= [i(r, "mechanical_rank") for r in expected] == list(range(1, 11))
        ranking_ok &= all((i(r, "mechanical_rank") == 1) == (i(r, "mechanical_top_candidate") == 1) for r in rs)
        ranking_ok &= all(len(r["fold_A_panels"].split("-")) == 2 and len(r["fold_B_panels"].split("-")) == 3 and i(r, "p2panel_split_count") == 0 for r in rs)
    check("ranking_reproduces_exactly", ranking_ok and len(by_state) == 48, len(by_state), 48)

    valid_states = {r["state_abbr"] for r in candidates if i(r, "mechanical_rank") == 1 and i(r, "candidate_design_valid") == 1}
    blocked_states = {r["state_abbr"] for r in candidates if i(r, "mechanical_rank") == 1 and r["candidate_design_status"] == "DESIGN_BLOCKED_ESTIMATION_UNIT_UNSAMPLED"}
    check("single_true_block", len(valid_states) == 47 and blocked_states == {"WV"}, {"valid": len(valid_states), "blocked": sorted(blocked_states)}, {"valid": 47, "blocked": ["WV"]})

    coarse_top_states = {r["state_abbr"] for r in coarse if i(r, "mechanical_top_candidate") == 1}
    check("mechanical_top_coarsening_states", coarse_top_states == {"CA", "OR", "WA", "WV"}, sorted(coarse_top_states), ["CA", "OR", "WA", "WV"])
    check("coarsening_preserves_area", all(i(r, "population_area_preserved_100pct") == 1 and f(r, "population_area_preservation_relative_error") <= TOL and r["threshold_used"] == "NONE" for r in coarse), len(coarse), "all rows")

    frame_area = {r["state_abbr"]: f(r, "population_area_acres") for r in frame}
    ti_sum = defaultdict(float)
    ti_status = True
    for r in ti:
        ti_sum[(r["state_abbr"], r["fold"])] += f(r, "synthetic_constant_recovered_area_acres")
        ti_status &= r["full_evaluation_expns_reused_as_final_fold_weight"] == "NO"
        ti_status &= r["calibration_status"] == "PASS" and f(r, "calibration_relative_error") <= TOL
        ti_status &= f(r, "population_area_discarded_acres") == 0.0
    ti_states = {s for s, fold in ti_sum}
    ti_status &= ti_states == valid_states
    ti_status &= all(abs(area - frame_area[state]) / max(abs(area), abs(frame_area[state]), 1.0) <= TOL for (state, fold), area in ti_sum.items())
    ti_status &= all((s, fold) in ti_sum for s in valid_states for fold in ("A", "B"))
    check("ti_47_state_fold_closure", ti_status, {"states": len(ti_states), "rows": len(ti)}, {"states": 47, "folds_each": 2})

    ma_state = {}
    for r in ma:
        ma_state[r["state_abbr"]] = r["ma_state_feasibility"]
    ma_counts = Counter(ma_state.values())
    check("ma_counts", ma_counts == Counter({"COMPLETE": 16, "PARTIAL": 31, "UNAVAILABLE": 1}) and ma_state.get("WV") == "UNAVAILABLE", dict(ma_counts), {"COMPLETE": 16, "PARTIAL": 31, "UNAVAILABLE": 1})

    check("wv_exact_block_evidence", len(wv) == 10 and all(r["parent_stratum_area_acres"] == "23014.8" and r["ti_estimable_after_coarsening"] == "NO" and r["historical_area_recovery_threshold_used"] == "NO" for r in wv), len(wv), 10)
    check("or_exact_four_retained", len(orm) == 4 and len({r["plt_cn"] for r in orm}) == 4 and all(r["component_evalid"] == "412301" and r["plot_fk_resolved"] == "YES" and r["retained_without_rewrite"] == "YES" and r["blocking_status"] == "NONBLOCKING_RESOLVED_PLOT_FK" for r in orm), [r["plt_cn"] for r in orm], "four unique resolved PLT_CN")
    check("builder_qc_all_pass", all(r["status"] == "PASS" for r in builder_qc), dict(Counter(r["status"] for r in builder_qc)), {"PASS": len(builder_qc)})
    check("status_allowlists", all(r["primary_design_status"] in {"DESIGN_COMPLETE", "DESIGN_COMPLETE_WITH_SYMMETRIC_COARSENING", "DESIGN_COMPLETE_WITH_NONBLOCKING_QC", "DESIGN_BLOCKED_ESTIMATION_UNIT_UNSAMPLED", "INPUT_BLOCKED"} for r in frame), sorted({r["primary_design_status"] for r in frame}), "contract state allowlist")

    result = {
        "audit_id": "D09C_T2_INDEPENDENT_VALIDATION_v01",
        "date": "2026-09-03",
        "mode": "output-only independent verification; no FIADB query and no species data",
        "status": "PASS" if all(c["status"] == "PASS" for c in checks) else "FAIL",
        "check_count": len(checks),
        "checks": checks,
    }
    path = QC / "D09C_T2_INDEPENDENT_VALIDATION_v01.json"
    path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "checks": len(checks)}))
    return 0 if result["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
