#!/usr/bin/env python3
"""Independent output-only core verifier, run before v02 scientific freeze."""

import csv
import json
from collections import Counter
from pathlib import Path


ROOT = Path(r"C:\range_paper")
WORK = ROOT / "99_tmp" / "range_gate0_v02_corrected"
OUT, QC = WORK / "outputs", WORK / "qc"
CLASSES = ["FAIL_EXTRA_NA", "BORDERLINE_OTHER_NA", "BORDERLINE_MEXICO", "RETAIN_USCA_AUDIT", "PASS_COARSE", "UNKNOWN"]
ROUTES = {"FAIL_EXTRA_NA": "EXCLUDE_WHOLE_RANGE_CORE", "BORDERLINE_OTHER_NA": "HOLD_TARGETED_EXTERNAL_RANGE_AUDIT", "BORDERLINE_MEXICO": "HOLD_TARGETED_EXTERNAL_RANGE_AUDIT", "RETAIN_USCA_AUDIT": "RETAIN_FOR_LITTLE_OR_USCA_TRUNCATION_AUDIT", "PASS_COARSE": "COARSE_CORE_PASS", "UNKNOWN": "HOLD_TARGETED_REVIEW_LATER"}
FIXTURES = {"Magnolia virginiana": "BORDERLINE_OTHER_NA", "Ostrya virginiana": "BORDERLINE_OTHER_NA", "Quercus rugosa": "BORDERLINE_OTHER_NA", "Sorbus decora": "BORDERLINE_OTHER_NA", "Pinus banksiana": "RETAIN_USCA_AUDIT", "Populus balsamifera": "FAIL_EXTRA_NA", "Pinus balfouriana": "PASS_COARSE"}


def read(path):
    with path.open("r", encoding="utf-8-sig", newline="") as f: return list(csv.DictReader(f))


def main() -> int:
    classification = read(OUT / "Q1_RANGE_GATE0_V02_CORRECTED_SPECIES_CLASSIFICATION_v01.csv")
    summary = read(OUT / "Q1_RANGE_GATE0_V02_CORRECTED_SUMMARY_v01.csv")
    queue = read(OUT / "Q1_RANGE_GATE0_V02_CORRECTED_DECISION_QUEUE_v01.csv")
    fail = read(OUT / "Q1_RANGE_GATE0_V02_CORRECTED_FAIL_EXTRA_NA_v01.csv")
    source_qc = read(QC / "Q1_RANGE_GATE0_V02_CORRECTED_QC_v01.csv")
    boundary = json.loads((QC / "RANGE_GATE0_V02_CORRECTED_BOUNDARY_AUDIT_v01.json").read_text(encoding="utf-8"))
    counts = Counter(row["range_gate0_v02_class"] for row in classification)
    summary_counts = {row["class"]: int(row["species_count"]) for row in summary}
    by_name = {row["analysis_species_name"]: row for row in classification}
    checks = []
    def add(cid, description, passed, actual, expected): checks.append({"check_id": cid, "description": description, "status": "PASS" if passed else "FAIL", "actual": actual, "expected": expected})
    add("IA001", "Classification rows exactly 312", len(classification) == 312, len(classification), 312)
    add("IA002", "Classification IDs unique", len({row["analysis_species_id"] for row in classification}) == 312, len({row["analysis_species_id"] for row in classification}), 312)
    add("IA003", "Six summary rows in frozen order", [row["class"] for row in summary] == CLASSES, [row["class"] for row in summary], CLASSES)
    add("IA004", "Summary counts equal recomputed counts", all(summary_counts.get(k) == counts[k] for k in CLASSES), summary_counts, dict(counts))
    add("IA005", "Counts sum to 312", sum(counts.values()) == 312, sum(counts.values()), 312)
    add("IA006", "Each class has exact frozen route", all(row["whole_range_core_route"] == ROUTES[row["range_gate0_v02_class"]] for row in classification), sum(row["whole_range_core_route"] == ROUTES[row["range_gate0_v02_class"]] for row in classification), 312)
    add("IA007", "All species remain confirmed-native CONUS", all(row["confirmed_native_CONUS"] == "TRUE" for row in classification), sum(row["confirmed_native_CONUS"] == "TRUE" for row in classification), 312)
    trans_only = [row for row in classification if row["range_gate0_v02_class"] == "FAIL_EXTRA_NA" and row["confirmed_native_outside_North_America"] == "FALSE" and row["range_gate0_v02_reason_code"] != "FROZEN_LONG_EVIDENCE_EXTRA_NA_SUMMARY_QC_MISMATCH"]
    add("IA008", "No transcontinental-only Class 1", not trans_only, len(trans_only), 0)
    add("IA009", "Every Class 1 has explicit extra-NA reason", all(row["range_gate0_v02_reason_code"] in {"CONFIRMED_NATIVE_OUTSIDE_NORTH_AMERICA", "FROZEN_LONG_EVIDENCE_EXTRA_NA_SUMMARY_QC_MISMATCH"} for row in fail), len(fail), counts["FAIL_EXTRA_NA"])
    add("IA010", "Transcontinental semantic role diagnostic-only on all rows", all(row["transcontinental_semantic_role"] == "DIAGNOSTIC_ONLY_ZERO_INDEPENDENT_ROUTING_AUTHORITY" for row in classification), sum(row["transcontinental_semantic_role"] == "DIAGNOSTIC_ONLY_ZERO_INDEPENDENT_ROUTING_AUTHORITY" for row in classification), 312)
    add("IA011", "Transcontinental trigger use equals zero", all(row["transcontinental_independent_trigger_used"] == "0" for row in classification), sum(int(row["transcontinental_independent_trigger_used"]) for row in classification), 0)
    for index, (name, expected) in enumerate(FIXTURES.items(), start=12):
        actual = by_name.get(name, {}).get("range_gate0_v02_class", "MISSING")
        add(f"IA{index:03d}", f"Semantic regression fixture {name}", actual == expected, actual, expected)
    add("IA019", "PASS_COARSE has no corrected Class 1-4 routing flag", not [row for row in classification if row["range_gate0_v02_class"] == "PASS_COARSE" and any(row[field] == "TRUE" for field in ["confirmed_native_Canada", "confirmed_native_Alaska", "confirmed_native_Mexico", "confirmed_native_Central_America", "confirmed_native_outside_USA_Canada", "confirmed_native_outside_North_America"])], 0, 0)
    queue_classes = {"BORDERLINE_OTHER_NA", "BORDERLINE_MEXICO", "RETAIN_USCA_AUDIT", "UNKNOWN"}
    add("IA020", "Decision queue exact ID set", {row["analysis_species_id"] for row in queue} == {row["analysis_species_id"] for row in classification if row["range_gate0_v02_class"] in queue_classes}, len(queue), sum(counts[k] for k in queue_classes))
    add("IA021", "FAIL ledger exact ID set", {row["analysis_species_id"] for row in fail} == {row["analysis_species_id"] for row in classification if row["range_gate0_v02_class"] == "FAIL_EXTRA_NA"}, len(fail), counts["FAIL_EXTRA_NA"])
    add("IA022", "USA+Canada audit flags exact", all((row["requires_future_usca_little_audit"] == "1") == (row["range_gate0_v02_class"] == "RETAIN_USCA_AUDIT") for row in classification), sum(row["requires_future_usca_little_audit"] == "1" for row in classification), counts["RETAIN_USCA_AUDIT"])
    external_classes = {"BORDERLINE_OTHER_NA", "BORDERLINE_MEXICO", "UNKNOWN"}
    add("IA023", "External audit flags exact", all((row["requires_future_external_range_audit"] == "1") == (row["range_gate0_v02_class"] in external_classes) for row in classification), sum(row["requires_future_external_range_audit"] == "1" for row in classification), sum(counts[k] for k in external_classes))
    add("IA024", "All final-cohort flags zero", all(row["range_gate0_final_cohort_flag"] == "0" for row in classification), sum(int(row["range_gate0_final_cohort_flag"]) for row in classification), 0)
    add("IA025", "Every row has reason/evidence/route", all(row["range_gate0_v02_reason_code"] and row["range_gate0_v02_evidence_text"] and row["whole_range_core_route"] for row in classification), sum(bool(row["range_gate0_v02_reason_code"] and row["range_gate0_v02_evidence_text"] and row["whole_range_core_route"]) for row in classification), 312)
    add("IA026", "Source build QC all PASS", all(row["status"] == "PASS" for row in source_qc), sum(row["status"] == "PASS" for row in source_qc), len(source_qc))
    forbidden = [key for key, value in boundary.items() if key not in {"version", "allowed_scientific_inputs"} and value is True]
    add("IA027", "Boundary has no prohibited operation", not forbidden, forbidden, [])
    add("IA028", "Evidence text declares no area/share/severity/geometry inference", all("No Level-3 count was interpreted as area/share/severity; no geometry was inferred." in row["range_gate0_v02_evidence_text"] for row in classification), sum("No Level-3 count was interpreted as area/share/severity; no geometry was inferred." in row["range_gate0_v02_evidence_text"] for row in classification), 312)
    add("IA029", "Reason TRANSCONTINENTAL_EXTENSION absent", all(row["range_gate0_v02_reason_code"] != "TRANSCONTINENTAL_EXTENSION" for row in classification), sum(row["range_gate0_v02_reason_code"] == "TRANSCONTINENTAL_EXTENSION" for row in classification), 0)
    add("IA030", "Classification sorted by numeric species ID", [int(row["analysis_species_id"]) for row in classification] == sorted(int(row["analysis_species_id"]) for row in classification), "SORTED" if [int(row["analysis_species_id"]) for row in classification] == sorted(int(row["analysis_species_id"]) for row in classification) else "UNSORTED", "SORTED")
    status = "PASS" if all(row["status"] == "PASS" for row in checks) else "FAIL"
    output = {"audit_type": "independent_output_only_core_prefreeze", "status": status, "authority_or_v01_files_read": [], "check_count": len(checks), "pass_count": sum(row["status"] == "PASS" for row in checks), "class_counts_recomputed": {klass: counts[klass] for klass in CLASSES}, "checks": checks}
    target = QC / "RANGE_GATE0_V02_CORRECTED_CORE_INDEPENDENT_AUDIT_v01.json"
    target.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": status, "checks": len(checks), "pass": output["pass_count"], "audit": str(target)}))
    return 0 if status == "PASS" else 1


if __name__ == "__main__": raise SystemExit(main())
