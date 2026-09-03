from __future__ import annotations

import csv
import json
import math
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(r"C:\range_paper")
OUT = ROOT / "04_derived" / "d09c_t2_final_correction_v02"
QC = ROOT / "05_qc" / "d09c_t2_final_correction_v02"
TOL = 1e-8


def read(name):
    with (OUT / name).open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def as_int(v):
    return int(float(v))


def as_float(v):
    return float(v)


def within_class_key(row):
    return (
        as_float(row["area_weighted_effective_block_imbalance"]),
        as_float(row["max_effective_block_imbalance"]),
        as_float(row["area_weighted_estimation_unit_imbalance"]),
        as_float(row["absolute_fold_A_plot_share_minus_0_4"]),
        as_float(row["temporal_center_abs_diff_years"]),
        as_float(row["temporal_distribution_l1_distance"]),
        as_float(row["temporal_sd_abs_diff_years"]),
        tuple(int(x) for x in row["fold_A_panels"].split("-")),
    )


def haversine_km(lat1, lon1, lat2, lon2):
    radius = 6371.0088
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * radius * math.asin(math.sqrt(a))


def main():
    ledger = read("Q1_D09C_T2_REPAIR_CLASS_LEDGER_v02.csv")
    selected = read("Q1_D09C_T2_FINAL_RULE_SELECTED_PARTITIONS_v02.csv")
    rerank = read("Q1_D09C_T2_CA_OR_WA_RERANK_AUDIT_v02.csv")
    trigger = read("Q1_D09C_T2_SPARSE_EU_TRIGGER_AUDIT_v02.csv")
    partners = read("Q1_D09C_T2_WV_MERGE_PARTNER_CANDIDATES_v02.csv")
    coordinates = read("Q1_D09C_T2_WV_PARTNER_COORDINATE_EVIDENCE_v02.csv")
    merged = read("Q1_D09C_T2_WV_MERGED_FRAME_AUDIT_v02.csv")
    ti = read("Q1_D09C_T2_FINAL_FOLD_SPECIFIC_TI_DESIGN_v02.csv")
    orm = read("Q1_D09C_T2_OR_412301_MISMATCH_FINAL_AUDIT_v02.csv")
    builder_qc = read("Q1_D09C_T2_FINAL_COMPLETION_QC_v02.csv")

    checks = []
    def check(cid, ok, observed, expected):
        checks.append({"check": cid, "status": "PASS" if ok else "FAIL", "observed": observed, "expected": expected})

    check("required_row_counts", len(ledger) == 480 and len(selected) == 48 and len(rerank) == 3 and len(trigger) == 48 and len(merged) == 10 and len(orm) == 4,
          {"ledger": len(ledger), "selected": len(selected), "rerank": len(rerank), "trigger": len(trigger), "merged": len(merged), "or": len(orm)},
          {"ledger": 480, "selected": 48, "rerank": 3, "trigger": 48, "merged": 10, "or": 4})

    by_state = defaultdict(list)
    for row in ledger:
        by_state[row["state_abbr"]].append(row)
    check("ten_candidates_each", len(by_state) == 48 and all(len(v) == 10 for v in by_state.values()), len(by_state), 48)
    hierarchy_ok = True
    selected_map = {r["state_abbr"]: r for r in selected}
    for state, rows in by_state.items():
        classes = {r["repair_class_code"] for r in rows}
        chosen = next((c for c in ("R0", "R1", "R2") if c in classes), "R3")
        srow = selected_map[state]
        hierarchy_ok &= srow["final_repair_class"] == chosen
        eligible = sorted([r for r in rows if r["repair_class_code"] == chosen], key=within_class_key)
        hierarchy_ok &= len(eligible) > 0 and eligible[0]["final_rule_selected"] == "1"
        hierarchy_ok &= all((r["competition_eligible_class"] == "YES") == (r["repair_class_code"] == chosen) for r in rows)
        hierarchy_ok &= [as_int(r["final_rank_within_admissible_class"]) for r in eligible] == list(range(1, len(eligible) + 1))
    check("repair_hierarchy_and_rank_reproduce", hierarchy_ok, "all states", "lowest valid class then exact within-class tuple")

    class_counts = Counter(r["final_repair_class"] for r in selected)
    check("selected_class_counts", class_counts == Counter({"R0": 47, "R2": 1}), dict(class_counts), {"R0": 47, "R2": 1})
    changed = {r["state_abbr"] for r in rerank if r["candidate_changed"] == "YES"}
    check("ca_or_wa_reranked_to_r0", changed == {"CA", "OR", "WA"} and all(r["v02_repair_class"] == "R0" and r["v01_repair_class"] == "R1" for r in rerank), sorted(changed), ["CA", "OR", "WA"])

    triggered = {r["state_abbr"] for r in trigger if r["R2_triggered"] == "YES"}
    check("r2_trigger_only_wv", triggered == {"WV"}, sorted(triggered), ["WV"])
    same = sorted([r for r in partners if r["same_semantic_class_as_sparse_eu"] == "YES"], key=lambda r: as_float(r["centroid_haversine_distance_km"]))
    partner_ok = len(same) == 2 and same[0]["candidate_estimation_unit"] == "4" and same[0]["final_partner_selected"] == "YES" and same[1]["candidate_estimation_unit"] == "2" and as_float(same[0]["centroid_haversine_distance_km"]) < as_float(same[1]["centroid_haversine_distance_km"])
    check("wv_partner_unique_by_frozen_rule", partner_ok, [(r["candidate_estimation_unit"], r["centroid_haversine_distance_km"], r["final_partner_selected"]) for r in same], "Unit 4 unique minimum among same-class Units 2 and 4")
    check("partner_selection_forbidden_metrics_absent", all(r["area_or_plot_count_used_for_selection"] == "NO" and r["balance_or_time_used_for_selection"] == "NO" for r in partners), "all rows", "NO")
    coord_groups = defaultdict(list)
    for row in coordinates:
        if row["included_in_public_coordinate_centroid"] == "YES":
            coord_groups[row["estimation_unit"]].append((as_float(row["public_latitude"]), as_float(row["public_longitude"])))
    centroids = {u: (sum(x[0] for x in pts) / len(pts), sum(x[1] for x in pts) / len(pts)) for u, pts in coord_groups.items()}
    partner_dist = {r["candidate_estimation_unit"]: as_float(r["centroid_haversine_distance_km"]) for r in same}
    recomputed = {u: haversine_km(centroids["3"][0], centroids["3"][1], centroids[u][0], centroids[u][1]) for u in ("2", "4")}
    check("partner_coordinate_evidence_reproduces", set(coord_groups) == {"2", "3", "4"} and len(coordinates) == 18 and all(abs(recomputed[u] - partner_dist[u]) <= 1e-10 for u in ("2", "4")), {"rows": len(coordinates), "distances": recomputed}, {"units": ["2", "3", "4"], "rows": 18})

    merged_ok = all(r["repair_class"] == "R2" and r["partner_eu"] == "4" and r["population_area_preserved_100pct"] == "1" and r["ti_estimable"] == "1" and r["same_merged_frame_used_by_A_and_B"] == "YES" and r["full_evaluation_expns_reused"] == "NO" for r in merged)
    check("wv_all_ten_r2_candidates_valid", merged_ok, len(merged), 10)

    ti_sums = defaultdict(float)
    ti_ok = True
    for row in ti:
        ti_sums[(row["state_abbr"], row["fold"])] += as_float(row["synthetic_constant_recovered_area_acres"])
        ti_ok &= row["calibration_status"] == "PASS" and as_float(row["calibration_relative_error"]) <= TOL
        ti_ok &= row["full_evaluation_expns_reused_as_final_fold_weight"] == "NO"
        ti_ok &= as_float(row["population_area_discarded_acres"]) == 0.0
    ti_states = {s for s, fold in ti_sums}
    ti_ok &= len(ti_states) == 48 and all((s, f) in ti_sums for s in ti_states for f in ("A", "B"))
    ti_ok &= all(abs(ti_sums[(s, "A")] - ti_sums[(s, "B")]) / max(abs(ti_sums[(s, "A")]), abs(ti_sums[(s, "B")]), 1.0) <= TOL for s in ti_states)
    check("ti_nationwide_area_closure", ti_ok, {"states": len(ti_states), "rows": len(ti)}, {"states": 48, "folds": 2})

    or_ok = len({r["plt_cn"] for r in orm}) == 4 and all(r["component_evalid"] == "412301" and r["plot_fk_resolved"] == "YES" and r["retained_without_rewrite"] == "YES" and r["record_treatment_v02"] == "RETAINED_UNCHANGED_NONBLOCKING_PLOT_FK_RESOLVED" for r in orm)
    check("or_four_retained", or_ok, [r["plt_cn"] for r in orm], "four unique resolved retained records")
    check("builder_qc_all_pass", all(r["status"] == "PASS" for r in builder_qc), dict(Counter(r["status"] for r in builder_qc)), {"PASS": len(builder_qc)})
    check("status_ready_for_mainline", len(selected) == 48 and ti_ok, "PASS_READY_FOR_MAINLINE_FINAL_D09C_AUDIT", "PASS_READY_FOR_MAINLINE_FINAL_D09C_AUDIT")

    result = {
        "audit_id": "D09C_T2_FINAL_INDEPENDENT_VALIDATION_v02",
        "date": "2026-09-03",
        "mode": "output-only independent verification; no FIADB query and no species data",
        "status": "PASS" if all(r["status"] == "PASS" for r in checks) else "FAIL",
        "check_count": len(checks),
        "checks": checks,
    }
    path = QC / "D09C_T2_FINAL_INDEPENDENT_VALIDATION_v02.json"
    path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "checks": len(checks)}))
    return 0 if result["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
