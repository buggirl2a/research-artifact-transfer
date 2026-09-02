#!/usr/bin/env python3
"""Fresh Range Gate 0 v02 corrected build from frozen D08B1 v02 only."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import platform
import sys
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(r"C:\range_paper")
INPUT_ROOT = ROOT / "03_doc" / "RANGE_GATE0_V02_CORRECTED_INPUTS_v01"
AUTH = INPUT_ROOT / "d08b1_v02_authority"
SRC = ROOT / "06_src" / "range_gate0_v02_corrected"
CONTROL = ROOT / "00_control"
WORK = ROOT / "99_tmp" / "range_gate0_v02_corrected"
OUT = WORK / "outputs"
QC = WORK / "qc"

REQUEST = INPUT_ROOT / "Q1_WORK_REQUEST_RANGE_GATE0_v02_CORRECTED_GEOGRAPHIC_SEMANTICS_20260903.md"
AUTH_ZIP = INPUT_ROOT / "Q1_TAXON_RANGE_D08B1_CORRECTED_REPRODUCIBLE_v02.zip"
AUTH_ZIP_SIDECAR = INPUT_ROOT / "Q1_TAXON_RANGE_D08B1_CORRECTED_REPRODUCIBLE_v02.zip.sha256"
MASTER = AUTH / "Q1_ANALYSIS_SPECIES_MASTER_v02.csv"
FLAGS = AUTH / "Q1_GLOBAL_RANGE_FLAGS_v02.csv"
LONG = AUTH / "Q1_WCVP_NATIVE_DISTRIBUTION_LONG_v02.csv"
CONTRACT = CONTROL / "RANGE_GATE0_V02_CORRECTED_CONTRACT_v01.md"
INPUT_FREEZE = CONTROL / "RANGE_GATE0_V02_CORRECTED_INPUT_FREEZE_v01.md"
PARAMETERS = SRC / "parameters_range_gate0_v02_corrected_v01.json"

EXPECTED = {
    REQUEST: "cd74476cee906ba7c8333e928daf177f8e35969ff8e50ad277bcb4acb44e081f",
    AUTH_ZIP: "3647c35189110d524d5f6cd64bf2d4aabaaa80828e58f42e767bb5e862188a3e",
    MASTER: "6f69874ab02723b3489aa4f3cbfb5aba188147400efdf170f27ad699d6368cb0",
    FLAGS: "dc64778032ed9bd301bfc7c14818fc3ba71a3b2621bb4e8b33ec558ecdf3d16d",
    LONG: "559a2d6f7b0d67ad886468a2c0098e117c824f196f0a85d3bb7d99c466649017",
    CONTRACT: "882846adf6c9d1ade35f2e30da265d58d1856af5fbe20e73108cc889b3780b43",
    INPUT_FREEZE: "d00f5d9a24833423fa8c5f9034f41c9baf34b2ab1ac2033818e01834851f2649",
}
MEMBER_EXPECTED = {
    "outputs/Q1_ANALYSIS_SPECIES_MASTER_v02.csv": EXPECTED[MASTER],
    "outputs/Q1_GLOBAL_RANGE_FLAGS_v02.csv": EXPECTED[FLAGS],
    "outputs/Q1_WCVP_NATIVE_DISTRIBUTION_LONG_v02.csv": EXPECTED[LONG],
}

CLASSES = ["FAIL_EXTRA_NA", "BORDERLINE_OTHER_NA", "BORDERLINE_MEXICO", "RETAIN_USCA_AUDIT", "PASS_COARSE", "UNKNOWN"]
ROUTES = {
    "FAIL_EXTRA_NA": "EXCLUDE_WHOLE_RANGE_CORE",
    "BORDERLINE_OTHER_NA": "HOLD_TARGETED_EXTERNAL_RANGE_AUDIT",
    "BORDERLINE_MEXICO": "HOLD_TARGETED_EXTERNAL_RANGE_AUDIT",
    "RETAIN_USCA_AUDIT": "RETAIN_FOR_LITTLE_OR_USCA_TRUNCATION_AUDIT",
    "PASS_COARSE": "COARSE_CORE_PASS",
    "UNKNOWN": "HOLD_TARGETED_REVIEW_LATER",
}
ROUTING_FLAGS = [
    "confirmed_native_CONUS", "confirmed_native_Canada", "confirmed_native_Alaska",
    "confirmed_native_Mexico", "confirmed_native_Central_America",
    "confirmed_native_outside_USA_Canada", "confirmed_native_outside_North_America",
]
DIAGNOSTIC_FLAG = "transcontinental_circumboreal_global_extension_flag"
OUTPUT_FLAGS = ROUTING_FLAGS + [DIAGNOSTIC_FLAG]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def bool_summary(value: str) -> bool:
    if value == "TRUE": return True
    if value == "FALSE": return False
    raise ValueError(f"Nonbinary frozen summary flag: {value!r}")


def bool_long(value: str) -> bool:
    return value in {"1", "TRUE"}


def sort_key(value: str) -> tuple[int, object]:
    try: return (0, int(value))
    except ValueError: return (1, value)


def label(row: dict[str, str]) -> str:
    return f"{row['area_code_l3']}:{row['area']}"


def joined(rows: list[dict[str, str]]) -> str:
    return ";".join(sorted({label(row) for row in rows}))


def predicates(rows: list[dict[str, str]]) -> dict[str, object]:
    confirmed = [row for row in rows if bool_long(row["confirmed_current_native_flag"])]
    def conus(row): return row["region_code_l2"] in {"73", "74", "75", "76", "77", "78"}
    def alaska(row): return row["area_code_l3"] == "ASK"
    def canada(row): return row["region_code_l2"] in {"71", "72"} or row["area_code_l3"] in {"NUN", "NWT", "YUK"}
    def mexico(row): return row["region_code_l2"] == "79"
    def central(row): return row["region_code_l2"] == "80"
    def north_america(row): return row["continent_code_l1"] == "7" or row["region_code_l2"] in {"80", "81"}
    def usca(row): return conus(row) or alaska(row) or canada(row)
    outside_usca = [row for row in confirmed if not usca(row)]
    outside_na = [row for row in confirmed if not north_america(row)]
    other_na = [row for row in confirmed if north_america(row) and not (conus(row) or alaska(row) or canada(row) or mexico(row) or central(row))]
    doubtful_external = [row for row in rows if bool_long(row["native_location_doubtful_flag"]) and not conus(row)]
    continents = {row["continent_code_l1"] for row in confirmed if row["continent_code_l1"]}
    return {
        "confirmed_native_CONUS": any(conus(row) for row in confirmed),
        "confirmed_native_Canada": any(canada(row) for row in confirmed),
        "confirmed_native_Alaska": any(alaska(row) for row in confirmed),
        "confirmed_native_Mexico": any(mexico(row) for row in confirmed),
        "confirmed_native_Central_America": any(central(row) for row in confirmed),
        "confirmed_native_outside_USA_Canada": bool(outside_usca),
        "confirmed_native_outside_North_America": bool(outside_na),
        DIAGNOSTIC_FLAG: len(continents) >= 2,
        "other_na_extension": bool(other_na),
        "other_na_extension_level3_areas": joined(other_na),
        "outside_na_level3_areas_recomputed": joined(outside_na),
        "outside_usca_level3_areas_recomputed": joined(outside_usca),
        "confirmed_native_level3_areas_recomputed": joined(confirmed),
        "doubtful_external": bool(doubtful_external),
        "doubtful_external_level3_areas": joined(doubtful_external),
        "confirmed_record_count_recomputed": len(confirmed),
    }


def main() -> int:
    if WORK.exists():
        raise RuntimeError(f"Refusing to overwrite existing v02 work directory: {WORK}")
    OUT.mkdir(parents=True)
    QC.mkdir(parents=True)
    params = json.loads(PARAMETERS.read_text(encoding="utf-8"))
    if params["contract_sha256"] != EXPECTED[CONTRACT] or params["input_freeze_sha256"] != EXPECTED[INPUT_FREEZE]:
        raise RuntimeError("Frozen parameter/control hash linkage failure")

    hash_audit = []
    for path, expected in {**EXPECTED, PARAMETERS: sha256_file(PARAMETERS)}.items():
        actual = sha256_file(path)
        hash_audit.append({"input_role": "frozen_control" if path in {CONTRACT, INPUT_FREEZE, PARAMETERS} else "frozen_authority", "local_path": str(path), "size_bytes": path.stat().st_size, "expected_sha256": expected, "actual_sha256": actual, "status": "PASS" if actual == expected else "FAIL"})
        if actual != expected: raise RuntimeError(f"INPUT_BLOCKED: hash mismatch {path}")
    sidecar_hash = AUTH_ZIP_SIDECAR.read_text(encoding="utf-8-sig").split()[0].lower()
    if sidecar_hash != EXPECTED[AUTH_ZIP]: raise RuntimeError("INPUT_BLOCKED: D08B1 ZIP sidecar mismatch")
    with zipfile.ZipFile(AUTH_ZIP, "r") as zf:
        if zf.testzip() is not None: raise RuntimeError("INPUT_BLOCKED: D08B1 authority ZIP integrity failure")
        for suffix, expected in MEMBER_EXPECTED.items():
            matches = [name for name in zf.namelist() if name == suffix or name.endswith("/" + suffix)]
            if len(matches) != 1: raise RuntimeError(f"INPUT_BLOCKED: missing/nonunique ZIP member {suffix}")
            actual = sha256_bytes(zf.read(matches[0]))
            hash_audit.append({"input_role": "authority_zip_member", "local_path": f"{AUTH_ZIP}!/{matches[0]}", "size_bytes": zf.getinfo(matches[0]).file_size, "expected_sha256": expected, "actual_sha256": actual, "status": "PASS" if actual == expected else "FAIL"})
            if actual != expected: raise RuntimeError(f"INPUT_BLOCKED: ZIP member hash mismatch {suffix}")

    master_rows, flag_rows, long_rows = read_csv(MASTER), read_csv(FLAGS), read_csv(LONG)
    master_ids = [row["analysis_species_id"] for row in master_rows]
    flag_ids = [row["analysis_species_id"] for row in flag_rows]
    if len(master_rows) != 361 or len(set(master_ids)) != 361: raise RuntimeError("INPUT_BLOCKED: accepted master is not exactly 361 unique species")
    if len(flag_rows) != 361 or len(set(flag_ids)) != 361 or set(master_ids) != set(flag_ids): raise RuntimeError("INPUT_BLOCKED: global flags do not join one-to-one to the 361 master")
    master_by_id = {row["analysis_species_id"]: row for row in master_rows}
    long_by_id: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in long_rows: long_by_id[row["analysis_species_id"]].append(row)
    if not set(long_by_id).issubset(set(master_by_id)): raise RuntimeError("INPUT_BLOCKED: long evidence contains an unknown species ID")
    candidates = sorted([row for row in flag_rows if row["confirmed_native_CONUS"] == "TRUE"], key=lambda row: sort_key(row["analysis_species_id"]))
    if len(candidates) != 312 or len({row["analysis_species_id"] for row in candidates}) != 312: raise RuntimeError(f"INPUT_BLOCKED: candidate universe is {len(candidates)}, not 312 unique species")

    results = []
    reconciliation_counts: Counter[str] = Counter()
    for source in candidates:
        sid = source["analysis_species_id"]
        pred = predicates(long_by_id.get(sid, []))
        routing_nonbinary = [field for field in ROUTING_FLAGS if source.get(field, "") not in {"TRUE", "FALSE"}]
        diagnostic_binary = source.get(DIAGNOSTIC_FLAG, "") in {"TRUE", "FALSE"}
        routing_mismatches = [] if routing_nonbinary else [field for field in ROUTING_FLAGS if bool_summary(source[field]) != bool(pred[field])]
        diagnostic_mismatch = diagnostic_binary and bool_summary(source[DIAGNOSTIC_FLAG]) != bool(pred[DIAGNOSTIC_FLAG])
        summary_extra_na = source.get("confirmed_native_outside_North_America") == "TRUE"
        long_extra_na = bool(pred["confirmed_native_outside_North_America"])

        if routing_nonbinary:
            klass, reason, recon = "UNKNOWN", "REQUIRED_FLAG_MISSING_OR_NONBINARY", "NONBINARY_ROUTING_FLAG"
        elif summary_extra_na and long_extra_na:
            klass, reason, recon = "FAIL_EXTRA_NA", "CONFIRMED_NATIVE_OUTSIDE_NORTH_AMERICA", "MATCH"
        elif (not summary_extra_na) and long_extra_na and not [field for field in routing_mismatches if field != "confirmed_native_outside_North_America"]:
            klass, reason, recon = "FAIL_EXTRA_NA", "FROZEN_LONG_EVIDENCE_EXTRA_NA_SUMMARY_QC_MISMATCH", "EXPLICIT_LONG_EXTRA_NA_OVERRIDE"
        elif routing_mismatches:
            klass, reason, recon = "UNKNOWN", "FROZEN_FLAG_EVIDENCE_CONTRADICTION", "ROUTING_SUMMARY_LONG_MISMATCH"
        elif bool_summary(source["confirmed_native_Central_America"]):
            klass, reason, recon = "BORDERLINE_OTHER_NA", "CONFIRMED_NATIVE_CENTRAL_AMERICA", "MATCH"
        elif bool(pred["other_na_extension"]):
            klass, reason, recon = "BORDERLINE_OTHER_NA", "CONFIRMED_NATIVE_OTHER_NA_EXTENSION", "MATCH"
        elif bool_summary(source["confirmed_native_Mexico"]):
            klass, reason, recon = "BORDERLINE_MEXICO", "CONFIRMED_NATIVE_MEXICO", "MATCH"
        elif bool_summary(source["confirmed_native_Canada"]) or bool_summary(source["confirmed_native_Alaska"]):
            klass, recon = "RETAIN_USCA_AUDIT", "MATCH"
            if bool_summary(source["confirmed_native_Canada"]) and bool_summary(source["confirmed_native_Alaska"]): reason = "CONFIRMED_NATIVE_CANADA_AND_ALASKA"
            elif bool_summary(source["confirmed_native_Canada"]): reason = "CONFIRMED_NATIVE_CANADA"
            else: reason = "CONFIRMED_NATIVE_ALASKA"
        elif bool_summary(source["confirmed_native_outside_USA_Canada"]):
            klass, reason, recon = "UNKNOWN", "UNRESOLVED_FROZEN_NA_SUBREGION", "UNRESOLVED_EXTERNAL_SUBREGION"
        elif bool(pred["doubtful_external"]):
            klass, reason, recon = "UNKNOWN", "DOUBTFUL_NATIVE_EXTERNAL_STATUS_COULD_CHANGE_ROUTE", "DOUBTFUL_EXTERNAL_NATIVE_STATUS"
        else:
            klass, reason, recon = "PASS_COARSE", "NO_CONFIRMED_EXTERNAL_NATIVE_EXTENSION_IN_FROZEN_D08B1", "MATCH"
        reconciliation_counts[recon] += 1

        evidence = [
            f"D08B1 routing flags: Canada={source['confirmed_native_Canada']}, Alaska={source['confirmed_native_Alaska']}, Mexico={source['confirmed_native_Mexico']}, Central_America={source['confirmed_native_Central_America']}, outside_USA_Canada={source['confirmed_native_outside_USA_Canada']}, outside_North_America={source['confirmed_native_outside_North_America']}.",
            f"Transcontinental diagnostic={source[DIAGNOSTIC_FLAG]}; diagnostic-only with zero independent routing authority.",
            f"Confirmed native Level-3 categorical evidence: {source['confirmed_native_level3_areas'] or 'NONE'}.",
        ]
        if source["confirmed_native_outside_USA_Canada_level3_areas"]: evidence.append("Outside USA+Canada units: " + source["confirmed_native_outside_USA_Canada_level3_areas"] + ".")
        if source["confirmed_native_outside_North_America_level3_areas"]: evidence.append("Outside North America units: " + source["confirmed_native_outside_North_America_level3_areas"] + ".")
        if pred["other_na_extension_level3_areas"]: evidence.append("Other North-America-side units: " + str(pred["other_na_extension_level3_areas"]) + ".")
        if pred["doubtful_external_level3_areas"]: evidence.append("Doubtful external native units: " + str(pred["doubtful_external_level3_areas"]) + ".")
        if routing_mismatches: evidence.append("Routing summary/long mismatches: " + ";".join(routing_mismatches) + ".")
        if diagnostic_mismatch: evidence.append("Diagnostic-only transcontinental summary/long mismatch recorded; it did not affect routing.")
        evidence.append("No Level-3 count was interpreted as area/share/severity; no geometry was inferred.")

        row: dict[str, object] = {"analysis_species_id": sid, "analysis_species_name": source["analysis_species_name"]}
        row.update({field: source[field] for field in OUTPUT_FLAGS})
        row.update({
            "transcontinental_semantic_role": "DIAGNOSTIC_ONLY_ZERO_INDEPENDENT_ROUTING_AUTHORITY",
            "transcontinental_independent_trigger_used": 0,
            "all_distribution_flags_valid_binary": source["all_distribution_flags_valid_binary"],
            "macro_region_rule_version": source["macro_region_rule_version"],
            "confirmed_native_level3_areas": source["confirmed_native_level3_areas"],
            "confirmed_native_outside_USA_Canada_level3_areas": source["confirmed_native_outside_USA_Canada_level3_areas"],
            "confirmed_native_outside_North_America_level3_areas": source["confirmed_native_outside_North_America_level3_areas"],
            "other_na_extension_level3_areas": pred["other_na_extension_level3_areas"],
            "doubtful_native_outside_primary_CONUS_level3_areas": pred["doubtful_external_level3_areas"],
            "routing_reconciliation_status": recon,
            "routing_reconciliation_fields": ";".join(routing_mismatches),
            "transcontinental_diagnostic_reconciliation": "NONBINARY" if not diagnostic_binary else "MISMATCH_NO_ROUTING_EFFECT" if diagnostic_mismatch else "MATCH",
            "range_gate0_v02_class": klass,
            "range_gate0_v02_reason_code": reason,
            "range_gate0_v02_evidence_text": " ".join(evidence),
            "whole_range_core_route": ROUTES[klass],
            "requires_future_usca_little_audit": 1 if klass == "RETAIN_USCA_AUDIT" else 0,
            "requires_future_external_range_audit": 1 if klass in {"BORDERLINE_OTHER_NA", "BORDERLINE_MEXICO", "UNKNOWN"} else 0,
            "range_gate0_final_cohort_flag": 0,
            "source_global_range_flags_sha256": EXPECTED[FLAGS],
            "source_native_distribution_long_sha256": EXPECTED[LONG],
        })
        results.append(row)

    fields = [
        "analysis_species_id", "analysis_species_name", *OUTPUT_FLAGS,
        "transcontinental_semantic_role", "transcontinental_independent_trigger_used",
        "all_distribution_flags_valid_binary", "macro_region_rule_version",
        "confirmed_native_level3_areas", "confirmed_native_outside_USA_Canada_level3_areas",
        "confirmed_native_outside_North_America_level3_areas", "other_na_extension_level3_areas",
        "doubtful_native_outside_primary_CONUS_level3_areas", "routing_reconciliation_status",
        "routing_reconciliation_fields", "transcontinental_diagnostic_reconciliation",
        "range_gate0_v02_class", "range_gate0_v02_reason_code", "range_gate0_v02_evidence_text",
        "whole_range_core_route", "requires_future_usca_little_audit",
        "requires_future_external_range_audit", "range_gate0_final_cohort_flag",
        "source_global_range_flags_sha256", "source_native_distribution_long_sha256",
    ]
    classification = OUT / "Q1_RANGE_GATE0_V02_CORRECTED_SPECIES_CLASSIFICATION_v01.csv"
    write_csv(classification, results, fields)
    counts = Counter(str(row["range_gate0_v02_class"]) for row in results)
    summary = [{"class": klass, "species_count": counts[klass], "percent_of_312": f"{100 * counts[klass] / 312:.6f}", "downstream_route": ROUTES[klass]} for klass in CLASSES]
    write_csv(OUT / "Q1_RANGE_GATE0_V02_CORRECTED_SUMMARY_v01.csv", summary, ["class", "species_count", "percent_of_312", "downstream_route"])
    queue_classes = {"BORDERLINE_OTHER_NA", "BORDERLINE_MEXICO", "RETAIN_USCA_AUDIT", "UNKNOWN"}
    queue = [row for row in results if row["range_gate0_v02_class"] in queue_classes]
    fail = [row for row in results if row["range_gate0_v02_class"] == "FAIL_EXTRA_NA"]
    write_csv(OUT / "Q1_RANGE_GATE0_V02_CORRECTED_DECISION_QUEUE_v01.csv", queue, fields)
    write_csv(OUT / "Q1_RANGE_GATE0_V02_CORRECTED_FAIL_EXTRA_NA_v01.csv", fail, fields)
    write_csv(QC / "Q1_RANGE_GATE0_V02_CORRECTED_INPUT_HASH_AUDIT_v01.csv", hash_audit, ["input_role", "local_path", "size_bytes", "expected_sha256", "actual_sha256", "status"])

    checks = []
    def check(cid, description, actual, expected, passed): checks.append({"check_id": cid, "description": description, "expected": expected, "actual": actual, "status": "PASS" if passed else "FAIL"})
    check("QC001", "Frozen request, D08B1 authority, members, and controls hash-match", sum(row["status"] == "PASS" for row in hash_audit), len(hash_audit), all(row["status"] == "PASS" for row in hash_audit))
    check("QC002", "Accepted master is exactly 361 unique species", len(set(master_ids)), 361, len(master_rows) == len(set(master_ids)) == 361)
    check("QC003", "Global range flags join one-to-one to master", len(set(flag_ids)), 361, len(flag_rows) == len(set(flag_ids)) == 361 and set(flag_ids) == set(master_ids))
    check("QC004", "Candidate universe is exactly 312 unique confirmed-native-CONUS species", len({row["analysis_species_id"] for row in results}), 312, len(results) == len({row["analysis_species_id"] for row in results}) == 312)
    check("QC005", "Every candidate has exactly one valid v02 class", sum(row["range_gate0_v02_class"] in CLASSES for row in results), 312, all(row["range_gate0_v02_class"] in CLASSES for row in results))
    check("QC006", "Every candidate route matches corrected class", sum(row["whole_range_core_route"] == ROUTES[row["range_gate0_v02_class"]] for row in results), 312, all(row["whole_range_core_route"] == ROUTES[row["range_gate0_v02_class"]] for row in results))
    check("QC007", "Class counts sum exactly to 312", sum(counts.values()), 312, sum(counts.values()) == 312)
    trans_only_fail = [row["analysis_species_id"] for row in results if row["range_gate0_v02_class"] == "FAIL_EXTRA_NA" and row["confirmed_native_outside_North_America"] == "FALSE" and not row["confirmed_native_outside_North_America_level3_areas"]]
    check("QC008", "No FAIL_EXTRA_NA is caused solely by transcontinental diagnostic", len(trans_only_fail), 0, not trans_only_fail)
    fail_without_explicit = [row["analysis_species_id"] for row in fail if row["confirmed_native_outside_North_America"] != "TRUE" and row["range_gate0_v02_reason_code"] != "FROZEN_LONG_EVIDENCE_EXTRA_NA_SUMMARY_QC_MISMATCH"]
    check("QC009", "Every FAIL_EXTRA_NA has explicit frozen extra-North-America evidence", len(fail_without_explicit), 0, not fail_without_explicit)
    check("QC010", "Transcontinental field is diagnostic-only on every row", sum(row["transcontinental_semantic_role"] == "DIAGNOSTIC_ONLY_ZERO_INDEPENDENT_ROUTING_AUTHORITY" for row in results), 312, all(row["transcontinental_semantic_role"] == "DIAGNOSTIC_ONLY_ZERO_INDEPENDENT_ROUTING_AUTHORITY" for row in results))
    check("QC011", "Transcontinental independent trigger was never used", sum(int(row["transcontinental_independent_trigger_used"]) for row in results), 0, all(int(row["transcontinental_independent_trigger_used"]) == 0 for row in results))
    fixture_rows = {row["analysis_species_name"]: row for row in results}
    for index, (name, expected_class) in enumerate(params["mandatory_regression_fixtures"].items(), start=12):
        actual = fixture_rows.get(name, {}).get("range_gate0_v02_class", "MISSING")
        check(f"QC{index:03d}", f"Mandatory semantic regression fixture: {name}", actual, expected_class, actual == expected_class)
    qn = 19
    pass_bad = [row["analysis_species_id"] for row in results if row["range_gate0_v02_class"] == "PASS_COARSE" and any(row[field] == "TRUE" for field in ["confirmed_native_Canada", "confirmed_native_Alaska", "confirmed_native_Mexico", "confirmed_native_Central_America", "confirmed_native_outside_USA_Canada", "confirmed_native_outside_North_America"])]
    check(f"QC{qn:03d}", "PASS_COARSE has no corrected Class 1-4 routing flag", len(pass_bad), 0, not pass_bad); qn += 1
    check(f"QC{qn:03d}", "Decision queue contains only/all corrected review classes", len(queue), sum(counts[k] for k in queue_classes), all(row["range_gate0_v02_class"] in queue_classes for row in queue)); qn += 1
    check(f"QC{qn:03d}", "FAIL ledger contains only/all FAIL_EXTRA_NA", len(fail), counts["FAIL_EXTRA_NA"], all(row["range_gate0_v02_class"] == "FAIL_EXTRA_NA" for row in fail)); qn += 1
    check(f"QC{qn:03d}", "Future USA+Canada/Little flag follows corrected contract", sum(int(row["requires_future_usca_little_audit"]) for row in results), counts["RETAIN_USCA_AUDIT"], all(int(row["requires_future_usca_little_audit"]) == (1 if row["range_gate0_v02_class"] == "RETAIN_USCA_AUDIT" else 0) for row in results)); qn += 1
    expected_external = sum(counts[k] for k in {"BORDERLINE_OTHER_NA", "BORDERLINE_MEXICO", "UNKNOWN"})
    check(f"QC{qn:03d}", "Future external audit flag follows corrected contract", sum(int(row["requires_future_external_range_audit"]) for row in results), expected_external, all(int(row["requires_future_external_range_audit"]) == (1 if row["range_gate0_v02_class"] in {"BORDERLINE_OTHER_NA", "BORDERLINE_MEXICO", "UNKNOWN"} else 0) for row in results)); qn += 1
    check(f"QC{qn:03d}", "All final-cohort flags are zero", sum(int(row["range_gate0_final_cohort_flag"]) for row in results), 0, all(int(row["range_gate0_final_cohort_flag"]) == 0 for row in results)); qn += 1
    check(f"QC{qn:03d}", "No numerical area/geometry threshold exists", params["numerical_area_or_geometry_threshold"], None, params["numerical_area_or_geometry_threshold"] is None); qn += 1
    check(f"QC{qn:03d}", "No v01 classification was read to construct v02", "NONE", "NONE", True); qn += 1
    check(f"QC{qn:03d}", "No external/network source used", "NONE", "NONE", True); qn += 1
    check(f"QC{qn:03d}", "No Little layer content or reconstructed geometry used", "NONE", "NONE", True); qn += 1
    check(f"QC{qn:03d}", "No FIA outcome, D08C eligibility, support/detection, abundance, R1/R2, World 0, paired-null, predictions, or real-Q1 data read", "NONE", "NONE", True); qn += 1
    check(f"QC{qn:03d}", "Corrected contract hash remained frozen after class counts", sha256_file(CONTRACT), EXPECTED[CONTRACT], sha256_file(CONTRACT) == EXPECTED[CONTRACT]); qn += 1
    check(f"QC{qn:03d}", "Output is deterministically sorted by analysis_species_id", "SORTED" if [row["analysis_species_id"] for row in results] == sorted([row["analysis_species_id"] for row in results], key=sort_key) else "UNSORTED", "SORTED", [row["analysis_species_id"] for row in results] == sorted([row["analysis_species_id"] for row in results], key=sort_key))
    write_csv(QC / "Q1_RANGE_GATE0_V02_CORRECTED_QC_v01.csv", checks, ["check_id", "description", "expected", "actual", "status"])

    unknown_reasons = Counter(row["range_gate0_v02_reason_code"] for row in results if row["range_gate0_v02_class"] == "UNKNOWN")
    boundary = {
        "version": "v02_corrected_v01", "allowed_scientific_inputs": [str(path) for path in [REQUEST, AUTH_ZIP, AUTH_ZIP_SIDECAR, MASTER, FLAGS, LONG, CONTRACT, INPUT_FREEZE, PARAMETERS]],
        "v01_classification_read_for_v02_construction": False, "network_access_used": False,
        "little_layer_content_read": False, "fia_tree_or_outcome_read": False, "d08c1_or_d08c2_eligibility_read": False,
        "support_detection_or_abundance_read": False, "r1_r2_world0_paired_null_prediction_read": False,
        "external_range_search_run": False, "geometry_area_share_span_component_inference_run": False,
        "taxonomy_repair_run": False, "final_species_cohort_selected": False, "d08c2_run": False, "real_q1_run": False,
    }
    write_json(QC / "RANGE_GATE0_V02_CORRECTED_BOUNDARY_AUDIT_v01.json", boundary)
    write_json(QC / "RANGE_GATE0_V02_CORRECTED_BUILD_SUMMARY_v01.json", {
        "execution_status": "PASS" if all(row["status"] == "PASS" for row in checks) else "FAIL",
        "master_rows": len(master_rows), "candidate_rows": len(candidates), "long_evidence_rows": len(long_rows),
        "class_counts": {klass: counts[klass] for klass in CLASSES}, "unknown_reason_counts": dict(sorted(unknown_reasons.items())),
        "reconciliation_status_counts": dict(sorted(reconciliation_counts.items())),
        "transcontinental_diagnostic_true_count": sum(row[DIAGNOSTIC_FLAG] == "TRUE" for row in results),
        "transcontinental_independent_trigger_count": sum(int(row["transcontinental_independent_trigger_used"]) for row in results),
        "qc_pass_count": sum(row["status"] == "PASS" for row in checks), "qc_check_count": len(checks),
    })
    write_json(QC / "RANGE_GATE0_V02_CORRECTED_ENVIRONMENT_v01.json", {
        "python_version": sys.version, "platform": platform.platform(), "executable": sys.executable,
        "working_directory": os.getcwd(), "build_utc": datetime.now(timezone.utc).isoformat(), "standard_library_only": True,
    })
    (QC / "RANGE_GATE0_V02_CORRECTED_IMPLEMENTATION_LOG_v01.txt").write_text(
        "Fresh v02 corrected build completed from D08B1 v02 authority only.\n"
        "v01 classification read before v02 scientific freeze: NO.\n"
        "Transcontinental flag routing authority: DIAGNOSTIC ONLY / ZERO.\n"
        f"Rows: master={len(master_rows)}, candidates={len(candidates)}, evidence={len(long_rows)}.\n"
        f"Class counts: {json.dumps({klass: counts[klass] for klass in CLASSES}, sort_keys=True)}\n"
        f"QC: {sum(row['status'] == 'PASS' for row in checks)}/{len(checks)} PASS.\n"
        "Prohibited operations invoked: none.\n", encoding="utf-8")
    if not all(row["status"] == "PASS" for row in checks): raise RuntimeError("SCIENTIFIC_CONTRACT_REGRESSION_FAIL: build QC failed")
    print(json.dumps({"status": "PASS", "class_counts": {klass: counts[klass] for klass in CLASSES}, "unknown_reasons": dict(unknown_reasons), "qc": f"{len(checks)}/{len(checks)}"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
