#!/usr/bin/env python3
"""Final independent output-only audit for Range Gate 0 v02 corrected."""

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path


ROOT = Path(r"C:\range_paper")
WORK = ROOT / "99_tmp" / "range_gate0_v02_corrected"
OUT, QC = WORK / "outputs", WORK / "qc"
CLASS = OUT / "Q1_RANGE_GATE0_V02_CORRECTED_SPECIES_CLASSIFICATION_v01.csv"
SUMMARY = OUT / "Q1_RANGE_GATE0_V02_CORRECTED_SUMMARY_v01.csv"
QUEUE = OUT / "Q1_RANGE_GATE0_V02_CORRECTED_DECISION_QUEUE_v01.csv"
FAIL = OUT / "Q1_RANGE_GATE0_V02_CORRECTED_FAIL_EXTRA_NA_v01.csv"
DELTA = OUT / "Q1_RANGE_GATE0_V01_TO_V02_CORRECTED_DELTA_AUDIT_v01.csv"
DELTA_SUMMARY = OUT / "Q1_RANGE_GATE0_V01_TO_V02_CORRECTED_DELTA_SUMMARY_v01.csv"
NOTE = OUT / "RANGE_GATE0_V02_CORRECTED_RESULT_NOTE_v01.md"
FROZEN_HASHES = {
    CLASS: "d0ff6281d3e5a8aa2cb1438fd70cc2650163b6c512ffe8299c24d3555ddfcb64",
    SUMMARY: "6fff3e6f9c90957e1c652c00691b1bf2437ef8f5f7253fb48ec266336fa92205",
    QUEUE: "da944cc5c7d035cd15cad49df76c620e1169dc18136703c16355a3a4e2bab69c",
    FAIL: "3f819a334126cbc2c66a05a3016db9ba310eb6fe9d065c4a9d15fb54408ecf2d",
}
CLASSES = ["FAIL_EXTRA_NA", "BORDERLINE_OTHER_NA", "BORDERLINE_MEXICO", "RETAIN_USCA_AUDIT", "PASS_COARSE", "UNKNOWN"]
ROUTES = {"FAIL_EXTRA_NA": "EXCLUDE_WHOLE_RANGE_CORE", "BORDERLINE_OTHER_NA": "HOLD_TARGETED_EXTERNAL_RANGE_AUDIT", "BORDERLINE_MEXICO": "HOLD_TARGETED_EXTERNAL_RANGE_AUDIT", "RETAIN_USCA_AUDIT": "RETAIN_FOR_LITTLE_OR_USCA_TRUNCATION_AUDIT", "PASS_COARSE": "COARSE_CORE_PASS", "UNKNOWN": "HOLD_TARGETED_REVIEW_LATER"}
FIXTURES = {"Magnolia virginiana": "BORDERLINE_OTHER_NA", "Ostrya virginiana": "BORDERLINE_OTHER_NA", "Quercus rugosa": "BORDERLINE_OTHER_NA", "Sorbus decora": "BORDERLINE_OTHER_NA", "Pinus banksiana": "RETAIN_USCA_AUDIT", "Populus balsamifera": "FAIL_EXTRA_NA", "Pinus balfouriana": "PASS_COARSE"}


def read(path):
    with path.open("r", encoding="utf-8-sig", newline="") as f: return list(csv.DictReader(f))


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""): h.update(block)
    return h.hexdigest()


def main() -> int:
    rows, summary, queue, fail, delta, delta_summary = read(CLASS), read(SUMMARY), read(QUEUE), read(FAIL), read(DELTA), read(DELTA_SUMMARY)
    build_qc = read(QC / "Q1_RANGE_GATE0_V02_CORRECTED_QC_v01.csv")
    delta_qc = read(QC / "Q1_RANGE_GATE0_V01_TO_V02_DELTA_QC_v01.csv")
    core_audit = json.loads((QC / "RANGE_GATE0_V02_CORRECTED_CORE_INDEPENDENT_AUDIT_v01.json").read_text(encoding="utf-8"))
    boundary = json.loads((QC / "RANGE_GATE0_V02_CORRECTED_BOUNDARY_AUDIT_v01.json").read_text(encoding="utf-8"))
    immutability = json.loads((QC / "RANGE_GATE0_V01_IMMUTABILITY_AUDIT_v01.json").read_text(encoding="utf-8"))
    counts = Counter(row["range_gate0_v02_class"] for row in rows)
    summary_counts = {row["class"]: int(row["species_count"]) for row in summary}
    delta_transitions = Counter((row["v01_class"], row["v02_class"], row["class_changed"]) for row in delta)
    reported_transitions = {(row["v01_class"], row["v02_class"], row["class_changed"]): int(row["species_count"]) for row in delta_summary}
    by_name = {row["analysis_species_name"]: row for row in rows}
    checks = []
    def add(cid, description, passed, actual, expected): checks.append({"check_id": cid, "description": description, "status": "PASS" if passed else "FAIL", "actual": actual, "expected": expected})
    add("FA001", "Frozen core output hashes remain exact", all(sha(path) == expected for path, expected in FROZEN_HASHES.items()), {path.name: sha(path) for path in FROZEN_HASHES}, {path.name: expected for path, expected in FROZEN_HASHES.items()})
    add("FA002", "Classification has exactly 312 unique IDs", len(rows) == len({row["analysis_species_id"] for row in rows}) == 312, [len(rows), len({row["analysis_species_id"] for row in rows})], [312, 312])
    add("FA003", "All six corrected classes occur in frozen summary order", [row["class"] for row in summary] == CLASSES, [row["class"] for row in summary], CLASSES)
    add("FA004", "Summary counts equal classification counts", all(summary_counts[k] == counts[k] for k in CLASSES), summary_counts, dict(counts))
    add("FA005", "Counts total exactly 312", sum(counts.values()) == 312, sum(counts.values()), 312)
    add("FA006", "Routes exactly follow corrected class map", all(row["whole_range_core_route"] == ROUTES[row["range_gate0_v02_class"]] for row in rows), sum(row["whole_range_core_route"] == ROUTES[row["range_gate0_v02_class"]] for row in rows), 312)
    add("FA007", "No transcontinental-only Class 1", not [row for row in rows if row["range_gate0_v02_class"] == "FAIL_EXTRA_NA" and row["confirmed_native_outside_North_America"] == "FALSE"], sum(row["range_gate0_v02_class"] == "FAIL_EXTRA_NA" and row["confirmed_native_outside_North_America"] == "FALSE" for row in rows), 0)
    add("FA008", "Every Class 1 has explicit corrected reason", all(row["range_gate0_v02_reason_code"] in {"CONFIRMED_NATIVE_OUTSIDE_NORTH_AMERICA", "FROZEN_LONG_EVIDENCE_EXTRA_NA_SUMMARY_QC_MISMATCH"} for row in fail), len(fail), counts["FAIL_EXTRA_NA"])
    add("FA009", "Transcontinental semantic role diagnostic-only throughout", all(row["transcontinental_semantic_role"] == "DIAGNOSTIC_ONLY_ZERO_INDEPENDENT_ROUTING_AUTHORITY" for row in rows), sum(row["transcontinental_semantic_role"] == "DIAGNOSTIC_ONLY_ZERO_INDEPENDENT_ROUTING_AUTHORITY" for row in rows), 312)
    add("FA010", "Transcontinental independent triggers zero", all(row["transcontinental_independent_trigger_used"] == "0" for row in rows), sum(int(row["transcontinental_independent_trigger_used"]) for row in rows), 0)
    add("FA011", "No obsolete transcontinental sufficient reason", all(row["range_gate0_v02_reason_code"] != "TRANSCONTINENTAL_EXTENSION" for row in rows), sum(row["range_gate0_v02_reason_code"] == "TRANSCONTINENTAL_EXTENSION" for row in rows), 0)
    for index, (name, expected) in enumerate(FIXTURES.items(), start=12):
        actual = by_name.get(name, {}).get("range_gate0_v02_class", "MISSING")
        add(f"FA{index:03d}", f"Mandatory regression fixture {name}", actual == expected, actual, expected)
    queue_classes = {"BORDERLINE_OTHER_NA", "BORDERLINE_MEXICO", "RETAIN_USCA_AUDIT", "UNKNOWN"}
    add("FA019", "Decision queue is exact", {row["analysis_species_id"] for row in queue} == {row["analysis_species_id"] for row in rows if row["range_gate0_v02_class"] in queue_classes}, len(queue), sum(counts[k] for k in queue_classes))
    add("FA020", "FAIL ledger is exact", {row["analysis_species_id"] for row in fail} == {row["analysis_species_id"] for row in rows if row["range_gate0_v02_class"] == "FAIL_EXTRA_NA"}, len(fail), counts["FAIL_EXTRA_NA"])
    add("FA021", "All future audit flags follow corrected contract", all((row["requires_future_usca_little_audit"] == "1") == (row["range_gate0_v02_class"] == "RETAIN_USCA_AUDIT") and (row["requires_future_external_range_audit"] == "1") == (row["range_gate0_v02_class"] in {"BORDERLINE_OTHER_NA", "BORDERLINE_MEXICO", "UNKNOWN"}) for row in rows), 312, 312)
    add("FA022", "All final-cohort flags zero", all(row["range_gate0_final_cohort_flag"] == "0" for row in rows), sum(int(row["range_gate0_final_cohort_flag"]) for row in rows), 0)
    add("FA023", "Delta contains exact 312 species", len(delta) == len({row["analysis_species_id"] for row in delta}) == 312, [len(delta), len({row["analysis_species_id"] for row in delta})], [312, 312])
    transition_actual_display = {f"{a}->{b}|{flag}": count for (a, b, flag), count in sorted(delta_transitions.items())}
    transition_reported_display = {f"{a}->{b}|{flag}": count for (a, b, flag), count in sorted(reported_transitions.items())}
    add("FA024", "Delta transition summary exactly recomputes", delta_transitions == Counter(reported_transitions), transition_actual_display, transition_reported_display)
    changed = [row for row in delta if row["class_changed"] == "YES"]
    add("FA025", "Every changed row has PASS semantic attribution", all(row["semantic_attribution_status"] == "PASS" for row in changed), sum(row["semantic_attribution_status"] == "PASS" for row in changed), len(changed))
    allowed_changed = {("FAIL_EXTRA_NA", "BORDERLINE_OTHER_NA"), ("BORDERLINE_SOUTH", "BORDERLINE_OTHER_NA")}
    add("FA026", "Changed transitions are only corrected semantic transitions", all((row["v01_class"], row["v02_class"]) in allowed_changed for row in changed), sorted({(row["v01_class"], row["v02_class"]) for row in changed}), sorted(allowed_changed))
    old_fail_moves = [row for row in changed if row["v01_class"] == "FAIL_EXTRA_NA"]
    add("FA027", "All moved v01 FAIL rows were outside-NA FALSE/transcontinental TRUE", all(row["confirmed_native_outside_North_America"] == "FALSE" and row["transcontinental_circumboreal_global_extension_flag"] == "TRUE" for row in old_fail_moves), sum(row["confirmed_native_outside_North_America"] == "FALSE" and row["transcontinental_circumboreal_global_extension_flag"] == "TRUE" for row in old_fail_moves), len(old_fail_moves))
    add("FA028", "All delta rows preserve v01 scientific status label", all(row["v01_scientific_status"] == "MAINLINE_CONTRACT_SEMANTICS_FAIL / COMPUTATIONAL_EXECUTION_PASS" for row in delta), sum(row["v01_scientific_status"] == "MAINLINE_CONTRACT_SEMANTICS_FAIL / COMPUTATIONAL_EXECUTION_PASS" for row in delta), 312)
    add("FA029", "Build QC all PASS", all(row["status"] == "PASS" for row in build_qc), sum(row["status"] == "PASS" for row in build_qc), len(build_qc))
    add("FA030", "Delta QC all PASS", all(row["status"] == "PASS" for row in delta_qc), sum(row["status"] == "PASS" for row in delta_qc), len(delta_qc))
    add("FA031", "Core independent audit PASS", core_audit["status"] == "PASS", core_audit["status"], "PASS")
    add("FA032", "v01 immutability audit PASS", immutability["status"] == "PASS" and not immutability["v01_files_modified"], immutability, "PASS / no files modified")
    forbidden = [key for key, value in boundary.items() if key not in {"version", "allowed_scientific_inputs"} and value is True]
    add("FA033", "Boundary reports no prohibited operation", not forbidden, forbidden, [])
    add("FA034", "Result note states STOP and corrected interpretation", "STOP" in NOTE.read_text(encoding="utf-8") and "diagnostic-only" in NOTE.read_text(encoding="utf-8"), True, True)
    add("FA035", "No class count is represented as a threshold target", all("target" not in row["range_gate0_v02_evidence_text"].lower() for row in rows), sum("target" in row["range_gate0_v02_evidence_text"].lower() for row in rows), 0)
    status = "PASS" if all(row["status"] == "PASS" for row in checks) else "FAIL"
    output = {"audit_type": "independent_output_only_final", "status": status, "authority_or_v01_files_read": [], "check_count": len(checks), "pass_count": sum(row["status"] == "PASS" for row in checks), "class_counts_recomputed": {klass: counts[klass] for klass in CLASSES}, "changed_row_count_recomputed": len(changed), "transition_counts_recomputed": {f"{a}->{b}|{flag}": count for (a, b, flag), count in sorted(delta_transitions.items())}, "checks": checks, "output_hashes": {path.name: sha(path) for path in [CLASS, SUMMARY, QUEUE, FAIL, DELTA, DELTA_SUMMARY, NOTE]}}
    target = QC / "RANGE_GATE0_V02_CORRECTED_INDEPENDENT_OUTPUT_AUDIT_v01.json"
    target.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": status, "checks": len(checks), "pass": output["pass_count"], "changed_rows": len(changed), "audit": str(target)}))
    return 0 if status == "PASS" else 1


if __name__ == "__main__": raise SystemExit(main())
