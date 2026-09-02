#!/usr/bin/env python3
"""Independent output-only verifier for Range Gate 0 v01."""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(r"C:\range_paper")
WORK = ROOT / "99_tmp" / "range_gate0_v01"
OUT = WORK / "outputs"
QC = WORK / "qc"
CLASSES = ["FAIL_EXTRA_NA", "BORDERLINE_SOUTH", "BORDERLINE_MEXICO", "RETAIN_USCA_AUDIT", "PASS_COARSE", "UNKNOWN"]
ROUTES = {
    "FAIL_EXTRA_NA": "EXCLUDE_WHOLE_RANGE_CORE",
    "BORDERLINE_SOUTH": "HOLD_TARGETED_EXTERNAL_RANGE_AUDIT",
    "BORDERLINE_MEXICO": "HOLD_TARGETED_EXTERNAL_RANGE_AUDIT",
    "RETAIN_USCA_AUDIT": "RETAIN_FOR_LITTLE_OR_USCA_TRUNCATION_AUDIT",
    "PASS_COARSE": "COARSE_CORE_PASS",
    "UNKNOWN": "HOLD_TARGETED_REVIEW_LATER",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main() -> int:
    classification_path = OUT / "Q1_RANGE_GATE0_SPECIES_CLASSIFICATION_v01.csv"
    summary_path = OUT / "Q1_RANGE_GATE0_SUMMARY_v01.csv"
    decision_path = OUT / "Q1_RANGE_GATE0_DECISION_QUEUE_v01.csv"
    fail_path = OUT / "Q1_RANGE_GATE0_FAIL_EXTRA_NA_v01.csv"
    note_path = OUT / "RANGE_GATE0_RESULT_NOTE_v01.md"
    qc_path = QC / "Q1_RANGE_GATE0_QC_v01.csv"
    boundary_path = QC / "RANGE_GATE0_BOUNDARY_AUDIT_v01.json"
    paths = [classification_path, summary_path, decision_path, fail_path, note_path, qc_path, boundary_path]
    rows = read_csv(classification_path)
    summary = read_csv(summary_path)
    decision = read_csv(decision_path)
    fail = read_csv(fail_path)
    source_qc = read_csv(qc_path)
    boundary = json.loads(boundary_path.read_text(encoding="utf-8"))
    counts = Counter(r["range_gate0_class"] for r in rows)
    summary_counts = {r["class"]: int(r["species_count"]) for r in summary}
    checks: list[dict[str, object]] = []

    def add(cid: str, description: str, passed: bool, actual: object, expected: object) -> None:
        checks.append({"check_id": cid, "description": description, "status": "PASS" if passed else "FAIL", "actual": actual, "expected": expected})

    add("IA001", "Required output/QC files exist", all(p.is_file() for p in paths), sum(p.is_file() for p in paths), len(paths))
    add("IA002", "Classification has exactly 312 rows", len(rows) == 312, len(rows), 312)
    add("IA003", "Species IDs are unique", len({r["analysis_species_id"] for r in rows}) == 312, len({r["analysis_species_id"] for r in rows}), 312)
    add("IA004", "All six summary classes occur exactly once", [r["class"] for r in summary] == CLASSES, [r["class"] for r in summary], CLASSES)
    add("IA005", "Classification counts equal summary counts", all(counts[k] == summary_counts.get(k) for k in CLASSES), dict(counts), summary_counts)
    add("IA006", "Summary counts total 312", sum(summary_counts.values()) == 312, sum(summary_counts.values()), 312)
    pct_sum = sum(float(r["percent_of_312"]) for r in summary)
    add("IA007", "Summary percentages close to 100 after rounding", abs(pct_sum - 100) < 0.00001, pct_sum, 100)
    add("IA008", "Every row has a valid class", all(r["range_gate0_class"] in CLASSES for r in rows), sum(r["range_gate0_class"] in CLASSES for r in rows), 312)
    add("IA009", "Every row route matches class", all(r["whole_range_core_route"] == ROUTES[r["range_gate0_class"]] for r in rows), sum(r["whole_range_core_route"] == ROUTES[r["range_gate0_class"]] for r in rows), 312)
    add("IA010", "All candidates are frozen confirmed native CONUS", all(r["confirmed_native_CONUS"] == "TRUE" for r in rows), sum(r["confirmed_native_CONUS"] == "TRUE" for r in rows), 312)
    add("IA011", "All final-cohort flags are zero", all(r["range_gate0_final_cohort_flag"] == "0" for r in rows), sum(r["range_gate0_final_cohort_flag"] == "0" for r in rows), 312)
    add("IA012", "USA+Canada audit flags exactly match RETAIN class", all((r["requires_future_usca_little_audit"] == "1") == (r["range_gate0_class"] == "RETAIN_USCA_AUDIT") for r in rows), sum(r["requires_future_usca_little_audit"] == "1" for r in rows), counts["RETAIN_USCA_AUDIT"])
    ext_classes = {"BORDERLINE_SOUTH", "BORDERLINE_MEXICO", "UNKNOWN"}
    add("IA013", "External audit flags exactly match frozen review classes", all((r["requires_future_external_range_audit"] == "1") == (r["range_gate0_class"] in ext_classes) for r in rows), sum(r["requires_future_external_range_audit"] == "1" for r in rows), sum(counts[k] for k in ext_classes))
    add("IA014", "Decision queue has only and all frozen queue classes", {r["analysis_species_id"] for r in decision} == {r["analysis_species_id"] for r in rows if r["range_gate0_class"] in ext_classes | {"RETAIN_USCA_AUDIT"}}, len(decision), sum(counts[k] for k in ext_classes | {"RETAIN_USCA_AUDIT"}))
    add("IA015", "FAIL file has only and all FAIL_EXTRA_NA", {r["analysis_species_id"] for r in fail} == {r["analysis_species_id"] for r in rows if r["range_gate0_class"] == "FAIL_EXTRA_NA"}, len(fail), counts["FAIL_EXTRA_NA"])
    pass_bad = [r for r in rows if r["range_gate0_class"] == "PASS_COARSE" and any(r[f] == "TRUE" for f in ["confirmed_native_Canada", "confirmed_native_Alaska", "confirmed_native_Mexico", "confirmed_native_Central_America", "confirmed_native_outside_USA_Canada", "confirmed_native_outside_North_America", "transcontinental_circumboreal_global_extension_flag"])]
    add("IA016", "PASS_COARSE has no compatible Class 1-4 flag", not pass_bad, len(pass_bad), 0)
    fail_bad = [r for r in fail if not (r["confirmed_native_outside_North_America"] == "TRUE" or r["transcontinental_circumboreal_global_extension_flag"] == "TRUE" or r["range_gate0_reason_code"] == "FROZEN_LONG_EVIDENCE_CLASS1_SUMMARY_QC_MISMATCH")]
    add("IA017", "FAIL_EXTRA_NA has explicit frozen evidence", not fail_bad, len(fail_bad), 0)
    add("IA018", "Every row has reason/evidence/route", all(r["range_gate0_reason_code"] and r["range_gate0_evidence_text"] and r["whole_range_core_route"] for r in rows), sum(bool(r["range_gate0_reason_code"] and r["range_gate0_evidence_text"] and r["whole_range_core_route"]) for r in rows), 312)
    add("IA019", "Source QC has no failed check", all(r["status"] == "PASS" for r in source_qc), sum(r["status"] == "PASS" for r in source_qc), len(source_qc))
    forbidden_true = [k for k, v in boundary.items() if k not in {"allowed_inputs", "version"} and v is True]
    add("IA020", "Boundary audit reports no prohibited operation", not forbidden_true, forbidden_true, [])
    add("IA021", "Boundary allowed-input list is explicit", len(boundary.get("allowed_inputs", [])) >= 9, len(boundary.get("allowed_inputs", [])), ">=9")
    add("IA022", "Output source hashes are constant across rows", len({r["source_global_range_flags_sha256"] for r in rows}) == 1 and len({r["source_native_distribution_long_sha256"] for r in rows}) == 1, [len({r["source_global_range_flags_sha256"] for r in rows}), len({r["source_native_distribution_long_sha256"] for r in rows})], [1, 1])
    add("IA023", "Administrative evidence includes no numerical inference claim", all("no area, share, geometry, or severity inference" in r["range_gate0_evidence_text"] for r in rows), sum("no area, share, geometry, or severity inference" in r["range_gate0_evidence_text"] for r in rows), 312)
    add("IA024", "Result note declares STOP", "STOP" in note_path.read_text(encoding="utf-8"), "STOP" in note_path.read_text(encoding="utf-8"), True)
    add("IA025", "Every output file has a computable SHA-256", all(len(sha(p)) == 64 for p in paths), len(paths), len(paths))

    status = "PASS" if all(c["status"] == "PASS" for c in checks) else "FAIL"
    audit = {
        "audit_type": "independent_output_only",
        "version": "v01",
        "status": status,
        "input_files_read": [str(p) for p in paths],
        "authority_or_scientific_input_files_read": [],
        "check_count": len(checks),
        "pass_count": sum(c["status"] == "PASS" for c in checks),
        "class_counts_recomputed": {k: counts[k] for k in CLASSES},
        "checks": checks,
        "output_hashes": {p.name: sha(p) for p in paths},
    }
    target = QC / "RANGE_GATE0_INDEPENDENT_AUDIT_v01.json"
    target.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": status, "checks": len(checks), "pass": audit["pass_count"], "audit": str(target)}))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
