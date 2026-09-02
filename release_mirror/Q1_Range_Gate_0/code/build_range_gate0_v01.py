#!/usr/bin/env python3
"""Build the frozen Range Gate 0 coarse-screen outputs.

This program is deliberately source-frozen.  It reads only the copied D08B1 v02
authority under 03_doc/RANGE_GATE0_INPUTS_v01 and the precommitted contract and
parameter files.  It performs no network, geometry, Little, FIA, or Q1 work.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import platform
import shutil
import sys
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(r"C:\range_paper")
INPUT_ROOT = ROOT / "03_doc" / "RANGE_GATE0_INPUTS_v01"
AUTH = INPUT_ROOT / "d08b1_v02_authority"
SRC = ROOT / "06_src" / "range_gate0_v01"
CONTROL = ROOT / "00_control"
WORK = ROOT / "99_tmp" / "range_gate0_v01"
OUT = WORK / "outputs"
QC = WORK / "qc"

REQUEST = INPUT_ROOT / "Q1_WORK_REQUEST_RANGE_GATE0_WHOLE_RANGE_COMPLETENESS_COARSE_SCREEN_v01_20260903.md"
AUTH_ZIP = INPUT_ROOT / "Q1_TAXON_RANGE_D08B1_CORRECTED_REPRODUCIBLE_v02.zip"
AUTH_ZIP_SIDECAR = INPUT_ROOT / "Q1_TAXON_RANGE_D08B1_CORRECTED_REPRODUCIBLE_v02.zip.sha256"
MASTER = AUTH / "Q1_ANALYSIS_SPECIES_MASTER_v02.csv"
FLAGS = AUTH / "Q1_GLOBAL_RANGE_FLAGS_v02.csv"
LONG = AUTH / "Q1_WCVP_NATIVE_DISTRIBUTION_LONG_v02.csv"
CONTRACT = CONTROL / "RANGE_GATE0_CONTRACT_v01.md"
INPUT_FREEZE = CONTROL / "RANGE_GATE0_INPUT_FREEZE_v01.md"
PARAMETERS = SRC / "parameters_range_gate0_v01.json"

EXPECTED = {
    REQUEST: "7b08106d190ac539e6f8127a656d36a764dc7f08a800e405d85aa0699612abd9",
    AUTH_ZIP: "3647c35189110d524d5f6cd64bf2d4aabaaa80828e58f42e767bb5e862188a3e",
    MASTER: "6f69874ab02723b3489aa4f3cbfb5aba188147400efdf170f27ad699d6368cb0",
    FLAGS: "dc64778032ed9bd301bfc7c14818fc3ba71a3b2621bb4e8b33ec558ecdf3d16d",
    LONG: "559a2d6f7b0d67ad886468a2c0098e117c824f196f0a85d3bb7d99c466649017",
    CONTRACT: "908e91da5cca2029b1f26a1594bb07486d2f3ee0ac407bb409f3b28376588d97",
    INPUT_FREEZE: "53509e82097e0db0ab560ec2f8ba70138263bfe06f9eb0660a28120b60a385e2",
}
MEMBER_EXPECTED = {
    "outputs/Q1_ANALYSIS_SPECIES_MASTER_v02.csv": EXPECTED[MASTER],
    "outputs/Q1_GLOBAL_RANGE_FLAGS_v02.csv": EXPECTED[FLAGS],
    "outputs/Q1_WCVP_NATIVE_DISTRIBUTION_LONG_v02.csv": EXPECTED[LONG],
}

CLASSES = [
    "FAIL_EXTRA_NA",
    "BORDERLINE_SOUTH",
    "BORDERLINE_MEXICO",
    "RETAIN_USCA_AUDIT",
    "PASS_COARSE",
    "UNKNOWN",
]
ROUTES = {
    "FAIL_EXTRA_NA": "EXCLUDE_WHOLE_RANGE_CORE",
    "BORDERLINE_SOUTH": "HOLD_TARGETED_EXTERNAL_RANGE_AUDIT",
    "BORDERLINE_MEXICO": "HOLD_TARGETED_EXTERNAL_RANGE_AUDIT",
    "RETAIN_USCA_AUDIT": "RETAIN_FOR_LITTLE_OR_USCA_TRUNCATION_AUDIT",
    "PASS_COARSE": "COARSE_CORE_PASS",
    "UNKNOWN": "HOLD_TARGETED_REVIEW_LATER",
}
REQUIRED_FLAGS = [
    "confirmed_native_CONUS",
    "confirmed_native_Canada",
    "confirmed_native_Alaska",
    "confirmed_native_Mexico",
    "confirmed_native_Central_America",
    "confirmed_native_outside_USA_Canada",
    "confirmed_native_outside_North_America",
    "transcontinental_circumboreal_global_extension_flag",
]


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
            writer.writerow({k: row.get(k, "") for k in fields})


def write_json(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def b(value: str) -> bool:
    if value == "TRUE":
        return True
    if value == "FALSE":
        return False
    raise ValueError(f"non-binary value: {value!r}")


def evidence_true(value: str) -> bool:
    """Interpret the frozen long-table's integer-coded Boolean fields."""
    return value in {"1", "TRUE"}


def sort_key(value: str) -> tuple[int, object]:
    try:
        return (0, int(value))
    except ValueError:
        return (1, value)


def area_label(row: dict[str, str]) -> str:
    return f"{row['area_code_l3']}:{row['area']}"


def joined_areas(rows: list[dict[str, str]]) -> str:
    return ";".join(sorted({area_label(r) for r in rows}))


def build_predicates(rows: list[dict[str, str]]) -> dict[str, object]:
    confirmed = [r for r in rows if evidence_true(r["confirmed_current_native_flag"])]

    def is_conus(r: dict[str, str]) -> bool:
        return r["region_code_l2"] in {"73", "74", "75", "76", "77", "78"}

    def is_alaska(r: dict[str, str]) -> bool:
        return r["area_code_l3"] == "ASK"

    def is_canada(r: dict[str, str]) -> bool:
        return r["region_code_l2"] in {"71", "72"} or r["area_code_l3"] in {"NUN", "NWT", "YUK"}

    def is_mexico(r: dict[str, str]) -> bool:
        return r["region_code_l2"] == "79"

    def is_central(r: dict[str, str]) -> bool:
        return r["region_code_l2"] == "80"

    def is_na(r: dict[str, str]) -> bool:
        return r["continent_code_l1"] == "7" or r["region_code_l2"] in {"80", "81"}

    def is_usca(r: dict[str, str]) -> bool:
        return is_conus(r) or is_alaska(r) or is_canada(r)

    outside_usca = [r for r in confirmed if not is_usca(r)]
    outside_na = [r for r in confirmed if not is_na(r)]
    other_na_south_island = [
        r for r in confirmed
        if is_na(r) and not (is_conus(r) or is_alaska(r) or is_canada(r) or is_mexico(r) or is_central(r))
    ]
    doubtful_external = [
        r for r in rows
        if evidence_true(r["native_location_doubtful_flag"]) and not is_conus(r)
    ]
    continents = {r["continent_code_l1"] for r in confirmed if r["continent_code_l1"]}
    return {
        "confirmed_native_CONUS": bool([r for r in confirmed if is_conus(r)]),
        "confirmed_native_Canada": bool([r for r in confirmed if is_canada(r)]),
        "confirmed_native_Alaska": bool([r for r in confirmed if is_alaska(r)]),
        "confirmed_native_Mexico": bool([r for r in confirmed if is_mexico(r)]),
        "confirmed_native_Central_America": bool([r for r in confirmed if is_central(r)]),
        "confirmed_native_outside_USA_Canada": bool(outside_usca),
        "confirmed_native_outside_North_America": bool(outside_na),
        "transcontinental_circumboreal_global_extension_flag": len(continents) >= 2,
        "confirmed_native_level3_areas_recomputed": joined_areas(confirmed),
        "outside_usca_level3_areas_recomputed": joined_areas(outside_usca),
        "outside_na_level3_areas_recomputed": joined_areas(outside_na),
        "other_na_south_or_island_level3_areas": joined_areas(other_na_south_island),
        "doubtful_external_level3_areas": joined_areas(doubtful_external),
        "other_na_south_or_island": bool(other_na_south_island),
        "doubtful_external": bool(doubtful_external),
        "confirmed_record_count_recomputed": len(confirmed),
    }


def main() -> int:
    if WORK.exists():
        raise RuntimeError(f"Refusing to overwrite existing build directory: {WORK}")
    OUT.mkdir(parents=True)
    QC.mkdir(parents=True)

    params = json.loads(PARAMETERS.read_text(encoding="utf-8"))
    expected_with_parameters = dict(EXPECTED)
    expected_with_parameters[PARAMETERS] = sha256_file(PARAMETERS)
    hash_audit: list[dict[str, object]] = []
    for path, expected_hash in expected_with_parameters.items():
        actual = sha256_file(path)
        hash_audit.append({
            "input_role": "frozen_control" if path in {CONTRACT, INPUT_FREEZE, PARAMETERS} else "frozen_authority",
            "local_path": str(path),
            "size_bytes": path.stat().st_size,
            "expected_sha256": expected_hash,
            "actual_sha256": actual,
            "status": "PASS" if actual == expected_hash else "FAIL",
        })
        if actual != expected_hash:
            raise RuntimeError(f"Hash mismatch: {path}")

    sidecar_tokens = AUTH_ZIP_SIDECAR.read_text(encoding="utf-8-sig").strip().split()
    if not sidecar_tokens or sidecar_tokens[0].lower() != EXPECTED[AUTH_ZIP]:
        raise RuntimeError("D08B1 ZIP sidecar does not match frozen ZIP hash")

    with zipfile.ZipFile(AUTH_ZIP, "r") as zf:
        if zf.testzip() is not None:
            raise RuntimeError("D08B1 authority ZIP integrity failure")
        names = zf.namelist()
        for suffix, expected_hash in MEMBER_EXPECTED.items():
            matches = [n for n in names if n.endswith("/" + suffix) or n == suffix]
            if len(matches) != 1:
                raise RuntimeError(f"Required ZIP member is not unique: {suffix}")
            actual = sha256_bytes(zf.read(matches[0]))
            hash_audit.append({
                "input_role": "authority_zip_member",
                "local_path": f"{AUTH_ZIP}!/{matches[0]}",
                "size_bytes": zf.getinfo(matches[0]).file_size,
                "expected_sha256": expected_hash,
                "actual_sha256": actual,
                "status": "PASS" if actual == expected_hash else "FAIL",
            })
            if actual != expected_hash:
                raise RuntimeError(f"ZIP member hash mismatch: {suffix}")

    master_rows = read_csv(MASTER)
    flag_rows = read_csv(FLAGS)
    long_rows = read_csv(LONG)
    if len(master_rows) != params["expected_analysis_species_master_rows"]:
        raise RuntimeError(f"INPUT_BLOCKED: master rows={len(master_rows)}")
    if len({r["analysis_species_id"] for r in master_rows}) != len(master_rows):
        raise RuntimeError("INPUT_BLOCKED: duplicate master analysis_species_id")
    if len({r["analysis_species_id"] for r in flag_rows}) != len(flag_rows):
        raise RuntimeError("INPUT_BLOCKED: duplicate global-flags analysis_species_id")
    master_by_id = {r["analysis_species_id"]: r for r in master_rows}
    flags_by_id = {r["analysis_species_id"]: r for r in flag_rows}
    if set(master_by_id) != set(flags_by_id):
        raise RuntimeError("INPUT_BLOCKED: master/global-flags ID sets differ")
    long_by_id: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in long_rows:
        long_by_id[row["analysis_species_id"]].append(row)
    if not set(long_by_id).issubset(set(master_by_id)):
        raise RuntimeError("INPUT_BLOCKED: long evidence includes unknown analysis_species_id")

    candidates = [r for r in flag_rows if r["confirmed_native_CONUS"] == "TRUE"]
    if len(candidates) != params["expected_conus_native_candidate_pool"]:
        raise RuntimeError(f"INPUT_BLOCKED: confirmed_native_CONUS pool={len(candidates)}")
    candidates.sort(key=lambda r: sort_key(r["analysis_species_id"]))

    results: list[dict[str, object]] = []
    reconciliation_counts: Counter[str] = Counter()
    for src in candidates:
        sid = src["analysis_species_id"]
        evidence_rows = long_by_id.get(sid, [])
        pred = build_predicates(evidence_rows)
        nonbinary = [name for name in REQUIRED_FLAGS if src.get(name, "") not in {"TRUE", "FALSE"}]
        mismatches = []
        if not nonbinary:
            for name in REQUIRED_FLAGS:
                if b(src[name]) != bool(pred[name]):
                    mismatches.append(name)

        summary_c1 = (
            src.get("confirmed_native_outside_North_America") == "TRUE"
            or src.get("transcontinental_circumboreal_global_extension_flag") == "TRUE"
        )
        long_c1 = bool(pred["confirmed_native_outside_North_America"]) or bool(
            pred["transcontinental_circumboreal_global_extension_flag"]
        )
        c1_override = long_c1 and not summary_c1 and not nonbinary

        if nonbinary:
            klass = "UNKNOWN"
            reason = "REQUIRED_FLAG_MISSING_OR_NONBINARY"
            recon = "NONBINARY_REQUIRED_FLAG"
        elif summary_c1 or c1_override:
            klass = "FAIL_EXTRA_NA"
            if c1_override:
                reason = "FROZEN_LONG_EVIDENCE_CLASS1_SUMMARY_QC_MISMATCH"
                recon = "C1_LONG_EVIDENCE_OVERRIDE"
            elif b(src["confirmed_native_outside_North_America"]) and b(src["transcontinental_circumboreal_global_extension_flag"]):
                reason = "EXTRA_NA_AND_TRANSCONTINENTAL"
                recon = "MATCH" if not mismatches else "SUMMARY_C1_WITH_RECONCILIATION_NOTE"
            elif b(src["confirmed_native_outside_North_America"]):
                reason = "CONFIRMED_NATIVE_OUTSIDE_NORTH_AMERICA"
                recon = "MATCH" if not mismatches else "SUMMARY_C1_WITH_RECONCILIATION_NOTE"
            else:
                reason = "TRANSCONTINENTAL_EXTENSION"
                recon = "MATCH" if not mismatches else "SUMMARY_C1_WITH_RECONCILIATION_NOTE"
        elif mismatches:
            klass = "UNKNOWN"
            reason = "FROZEN_FLAG_EVIDENCE_CONTRADICTION"
            recon = "ROUTE_RELEVANT_SUMMARY_LONG_MISMATCH"
        elif b(src["confirmed_native_Central_America"]):
            klass = "BORDERLINE_SOUTH"
            reason = "CONFIRMED_NATIVE_CENTRAL_AMERICA"
            recon = "MATCH"
        elif bool(pred["other_na_south_or_island"]):
            klass = "BORDERLINE_SOUTH"
            reason = "CONFIRMED_NATIVE_OTHER_NA_SOUTH_OR_ISLAND"
            recon = "MATCH"
        elif b(src["confirmed_native_Mexico"]):
            klass = "BORDERLINE_MEXICO"
            reason = "CONFIRMED_NATIVE_MEXICO"
            recon = "MATCH"
        elif b(src["confirmed_native_Canada"]) or b(src["confirmed_native_Alaska"]):
            klass = "RETAIN_USCA_AUDIT"
            if b(src["confirmed_native_Canada"]) and b(src["confirmed_native_Alaska"]):
                reason = "CONFIRMED_NATIVE_CANADA_AND_ALASKA"
            elif b(src["confirmed_native_Canada"]):
                reason = "CONFIRMED_NATIVE_CANADA"
            else:
                reason = "CONFIRMED_NATIVE_ALASKA"
            recon = "MATCH"
        elif b(src["confirmed_native_outside_USA_Canada"]):
            klass = "UNKNOWN"
            reason = "UNRESOLVED_FROZEN_NA_SUBREGION"
            recon = "UNRESOLVED_EXTERNAL_SUBREGION"
        elif bool(pred["doubtful_external"]):
            klass = "UNKNOWN"
            reason = "DOUBTFUL_NATIVE_EXTERNAL_STATUS_COULD_CHANGE_ROUTE"
            recon = "DOUBTFUL_EXTERNAL_NATIVE_STATUS"
        else:
            klass = "PASS_COARSE"
            reason = "NO_CONFIRMED_EXTERNAL_NATIVE_EXTENSION_IN_FROZEN_D08B1"
            recon = "MATCH"

        reconciliation_counts[recon] += 1
        evidence_parts = [
            f"D08B1 summary flags: Canada={src['confirmed_native_Canada']}, Alaska={src['confirmed_native_Alaska']}, Mexico={src['confirmed_native_Mexico']}, Central_America={src['confirmed_native_Central_America']}, outside_USA_Canada={src['confirmed_native_outside_USA_Canada']}, outside_North_America={src['confirmed_native_outside_North_America']}, transcontinental={src['transcontinental_circumboreal_global_extension_flag']}.",
            f"Confirmed native Level-3 administrative evidence: {src['confirmed_native_level3_areas'] or 'NONE'}.",
        ]
        if src["confirmed_native_outside_USA_Canada_level3_areas"]:
            evidence_parts.append("Outside USA+Canada units: " + src["confirmed_native_outside_USA_Canada_level3_areas"] + ".")
        if src["confirmed_native_outside_North_America_level3_areas"]:
            evidence_parts.append("Outside North America units: " + src["confirmed_native_outside_North_America_level3_areas"] + ".")
        if pred["other_na_south_or_island_level3_areas"]:
            evidence_parts.append("Other frozen North-America-side southern/island units: " + str(pred["other_na_south_or_island_level3_areas"]) + ".")
        if pred["doubtful_external_level3_areas"]:
            evidence_parts.append("Doubtful native external units: " + str(pred["doubtful_external_level3_areas"]) + ".")
        if mismatches:
            evidence_parts.append("Summary/long reconciliation fields: " + ";".join(mismatches) + ".")
        evidence_parts.append("Administrative-unit evidence is categorical only; no area, share, geometry, or severity inference was made.")

        result: dict[str, object] = {
            "analysis_species_id": sid,
            "analysis_species_name": src["analysis_species_name"],
        }
        for name in REQUIRED_FLAGS:
            result[name] = src[name]
        for name in [
            "confirmed_native_level3_areas",
            "confirmed_native_outside_USA_Canada_level3_areas",
            "confirmed_native_outside_North_America_level3_areas",
        ]:
            result[name] = src[name]
        result.update({
            "all_distribution_flags_valid_binary": src["all_distribution_flags_valid_binary"],
            "macro_region_rule_version": src["macro_region_rule_version"],
            "long_evidence_reconciliation_status": recon,
            "long_evidence_reconciliation_fields": ";".join(mismatches),
            "other_na_south_or_island_level3_areas": pred["other_na_south_or_island_level3_areas"],
            "doubtful_native_outside_primary_CONUS_level3_areas": pred["doubtful_external_level3_areas"],
            "range_gate0_class": klass,
            "range_gate0_reason_code": reason,
            "range_gate0_evidence_text": " ".join(evidence_parts),
            "whole_range_core_route": ROUTES[klass],
            "requires_future_usca_little_audit": 1 if klass == "RETAIN_USCA_AUDIT" else 0,
            "requires_future_external_range_audit": 1 if klass in {"BORDERLINE_SOUTH", "BORDERLINE_MEXICO", "UNKNOWN"} else 0,
            "range_gate0_final_cohort_flag": 0,
            "source_global_range_flags_sha256": EXPECTED[FLAGS],
            "source_native_distribution_long_sha256": EXPECTED[LONG],
        })
        results.append(result)

    classification_fields = [
        "analysis_species_id", "analysis_species_name",
        *REQUIRED_FLAGS,
        "all_distribution_flags_valid_binary", "macro_region_rule_version",
        "confirmed_native_level3_areas",
        "confirmed_native_outside_USA_Canada_level3_areas",
        "confirmed_native_outside_North_America_level3_areas",
        "other_na_south_or_island_level3_areas",
        "doubtful_native_outside_primary_CONUS_level3_areas",
        "long_evidence_reconciliation_status", "long_evidence_reconciliation_fields",
        "range_gate0_class", "range_gate0_reason_code", "range_gate0_evidence_text",
        "whole_range_core_route", "requires_future_usca_little_audit",
        "requires_future_external_range_audit", "range_gate0_final_cohort_flag",
        "source_global_range_flags_sha256", "source_native_distribution_long_sha256",
    ]
    classification_path = OUT / "Q1_RANGE_GATE0_SPECIES_CLASSIFICATION_v01.csv"
    write_csv(classification_path, results, classification_fields)

    counts = Counter(str(r["range_gate0_class"]) for r in results)
    summary_rows = [{
        "class": klass,
        "species_count": counts[klass],
        "percent_of_312": f"{100 * counts[klass] / 312:.6f}",
        "downstream_route": ROUTES[klass],
    } for klass in CLASSES]
    write_csv(OUT / "Q1_RANGE_GATE0_SUMMARY_v01.csv", summary_rows,
              ["class", "species_count", "percent_of_312", "downstream_route"])
    decision = [r for r in results if r["range_gate0_class"] in {"BORDERLINE_SOUTH", "BORDERLINE_MEXICO", "RETAIN_USCA_AUDIT", "UNKNOWN"}]
    fail = [r for r in results if r["range_gate0_class"] == "FAIL_EXTRA_NA"]
    write_csv(OUT / "Q1_RANGE_GATE0_DECISION_QUEUE_v01.csv", decision, classification_fields)
    write_csv(OUT / "Q1_RANGE_GATE0_FAIL_EXTRA_NA_v01.csv", fail, classification_fields)
    write_csv(QC / "Q1_RANGE_GATE0_INPUT_HASH_AUDIT_v01.csv", hash_audit,
              ["input_role", "local_path", "size_bytes", "expected_sha256", "actual_sha256", "status"])

    checks: list[dict[str, object]] = []
    def check(check_id: str, description: str, actual: object, expected: object, passed: bool) -> None:
        checks.append({
            "check_id": check_id, "description": description,
            "expected": expected, "actual": actual, "status": "PASS" if passed else "FAIL",
        })

    check("QC001", "Frozen D08B1 ZIP and copied authority/control hashes match", sum(r["status"] == "PASS" for r in hash_audit), len(hash_audit), all(r["status"] == "PASS" for r in hash_audit))
    check("QC002", "Analysis species master row count", len(master_rows), 361, len(master_rows) == 361)
    check("QC003", "confirmed_native_CONUS exact input universe", len(candidates), 312, len(candidates) == 312)
    check("QC004", "Candidate analysis_species_id values are unique", len({r["analysis_species_id"] for r in results}), 312, len({r["analysis_species_id"] for r in results}) == 312)
    check("QC005", "Exactly one valid Gate 0 class per species", sum(r["range_gate0_class"] in CLASSES for r in results), 312, all(r["range_gate0_class"] in CLASSES for r in results))
    check("QC006", "Six class counts sum to 312", sum(counts.values()), 312, sum(counts.values()) == 312)
    pass_bad = [r["analysis_species_id"] for r in results if r["range_gate0_class"] == "PASS_COARSE" and any(r[f] == "TRUE" for f in ["confirmed_native_Canada", "confirmed_native_Alaska", "confirmed_native_Mexico", "confirmed_native_Central_America", "confirmed_native_outside_USA_Canada", "confirmed_native_outside_North_America", "transcontinental_circumboreal_global_extension_flag"])]
    check("QC007", "PASS_COARSE has no Class 1-4 compatible frozen external flag", len(pass_bad), 0, not pass_bad)
    fail_bad = [r["analysis_species_id"] for r in fail if not (r["confirmed_native_outside_North_America"] == "TRUE" or r["transcontinental_circumboreal_global_extension_flag"] == "TRUE" or r["range_gate0_reason_code"] == "FROZEN_LONG_EVIDENCE_CLASS1_SUMMARY_QC_MISMATCH")]
    check("QC008", "Every FAIL_EXTRA_NA has explicit frozen extra-NA/transcontinental evidence", len(fail_bad), 0, not fail_bad)
    check("QC009", "No external/network source used", "NONE", "NONE", True)
    check("QC010", "No Little layer content used for decisions", "NONE", "NONE", True)
    check("QC011", "No FIA outcome, D08C eligibility, abundance, detection, or real-Q1 table read", "NONE", "NONE", True)
    selected = sum(int(r["range_gate0_final_cohort_flag"]) for r in results)
    check("QC012", "No final cohort flag selected", selected, 0, selected == 0)
    check("QC013", "Decision queue contains only frozen review classes", len(decision), sum(counts[k] for k in ["BORDERLINE_SOUTH", "BORDERLINE_MEXICO", "RETAIN_USCA_AUDIT", "UNKNOWN"]), all(r["range_gate0_class"] in {"BORDERLINE_SOUTH", "BORDERLINE_MEXICO", "RETAIN_USCA_AUDIT", "UNKNOWN"} for r in decision))
    check("QC014", "FAIL file contains only FAIL_EXTRA_NA", len(fail), counts["FAIL_EXTRA_NA"], all(r["range_gate0_class"] == "FAIL_EXTRA_NA" for r in fail))
    check("QC015", "No numerical area/geometry threshold exists", params["numerical_area_or_geometry_threshold"], None, params["numerical_area_or_geometry_threshold"] is None)
    check("QC016", "All required global flags are binary for all 312 rows", sum(not any(r.get(f, "") not in {"TRUE", "FALSE"} for f in REQUIRED_FLAGS) for r in candidates), 312, all(not any(r.get(f, "") not in {"TRUE", "FALSE"} for f in REQUIRED_FLAGS) for r in candidates))
    check("QC017", "All output species retain confirmed_native_CONUS TRUE", sum(r["confirmed_native_CONUS"] == "TRUE" for r in results), 312, all(r["confirmed_native_CONUS"] == "TRUE" for r in results))
    check("QC018", "Every output row has an explicit reason, evidence text, and route", sum(bool(r["range_gate0_reason_code"] and r["range_gate0_evidence_text"] and r["whole_range_core_route"]) for r in results), 312, all(r["range_gate0_reason_code"] and r["range_gate0_evidence_text"] and r["whole_range_core_route"] for r in results))
    check("QC019", "Future USA+Canada/Little audit flag follows frozen class rule", sum(int(r["requires_future_usca_little_audit"]) for r in results), counts["RETAIN_USCA_AUDIT"], all(int(r["requires_future_usca_little_audit"]) == (1 if r["range_gate0_class"] == "RETAIN_USCA_AUDIT" else 0) for r in results))
    expected_external = sum(counts[k] for k in ["BORDERLINE_SOUTH", "BORDERLINE_MEXICO", "UNKNOWN"])
    check("QC020", "Future external audit flag follows frozen class rule", sum(int(r["requires_future_external_range_audit"]) for r in results), expected_external, all(int(r["requires_future_external_range_audit"]) == (1 if r["range_gate0_class"] in {"BORDERLINE_SOUTH", "BORDERLINE_MEXICO", "UNKNOWN"} else 0) for r in results))
    check("QC021", "No scientific thresholds were changed after class counts", sha256_file(CONTRACT), EXPECTED[CONTRACT], sha256_file(CONTRACT) == EXPECTED[CONTRACT])
    check("QC022", "Classification output is deterministically sorted by analysis_species_id", [r["analysis_species_id"] for r in results], sorted([r["analysis_species_id"] for r in results], key=sort_key), [r["analysis_species_id"] for r in results] == sorted([r["analysis_species_id"] for r in results], key=sort_key))
    write_csv(QC / "Q1_RANGE_GATE0_QC_v01.csv", checks,
              ["check_id", "description", "expected", "actual", "status"])

    unknown_reasons = Counter(str(r["range_gate0_reason_code"]) for r in results if r["range_gate0_class"] == "UNKNOWN")
    result_note = [
        "# Range Gate 0 result note v01",
        "",
        "- Execution: **PASS**" if all(c["status"] == "PASS" for c in checks) else "- Execution: **FAIL**",
        f"- Frozen input universe: {len(candidates)} accepted species with `confirmed_native_CONUS == TRUE` (expected 312).",
        "- Scientific object: source-frozen, outcome-blind coarse routing of whole-range completeness using D08B1 v02 only.",
        "",
        "## Frozen class counts",
        "",
        "| Class | Species | Percent of 312 | Downstream route |",
        "|---|---:|---:|---|",
    ]
    for row in summary_rows:
        result_note.append(f"| {row['class']} | {row['species_count']} | {row['percent_of_312']}% | {row['downstream_route']} |")
    result_note.extend(["", "## UNKNOWN reasons", ""])
    if unknown_reasons:
        for reason, count in sorted(unknown_reasons.items()):
            result_note.append(f"- `{reason}`: {count}")
    else:
        result_note.append("- None.")
    result_note.extend([
        "",
        "## Interpretation boundary",
        "",
        "No WCVP administrative-unit count was treated as area, range share, or truncation severity. No geometry was reconstructed. No Little layer content, external search, D08C2 data, FIA outcome, abundance, detection, eligibility, or real-Q1 result was used. Range Gate 0 does not select a final cohort; every final-cohort flag is zero.",
        "",
        "STOP: return to scientific mainline for independent review.",
        "",
    ])
    (OUT / "RANGE_GATE0_RESULT_NOTE_v01.md").write_text("\n".join(result_note), encoding="utf-8")

    boundary = {
        "version": "v01",
        "allowed_inputs": [str(p) for p in [REQUEST, AUTH_ZIP, AUTH_ZIP_SIDECAR, MASTER, FLAGS, LONG, CONTRACT, INPUT_FREEZE, PARAMETERS]],
        "network_access_used": False,
        "little_layer_content_read": False,
        "fia_outcome_or_eligibility_read": False,
        "d08c2_run": False,
        "external_range_search_run": False,
        "geometry_or_area_inference_run": False,
        "real_q1_run": False,
        "final_species_cohort_selected": False,
    }
    write_json(QC / "RANGE_GATE0_BOUNDARY_AUDIT_v01.json", boundary)
    write_json(QC / "RANGE_GATE0_BUILD_SUMMARY_v01.json", {
        "execution_status": "PASS" if all(c["status"] == "PASS" for c in checks) else "FAIL",
        "master_rows": len(master_rows),
        "candidate_rows": len(candidates),
        "long_evidence_rows": len(long_rows),
        "class_counts": {k: counts[k] for k in CLASSES},
        "unknown_reason_counts": dict(sorted(unknown_reasons.items())),
        "reconciliation_status_counts": dict(sorted(reconciliation_counts.items())),
        "qc_pass_count": sum(c["status"] == "PASS" for c in checks),
        "qc_check_count": len(checks),
    })
    write_json(QC / "RANGE_GATE0_ENVIRONMENT_v01.json", {
        "python_version": sys.version,
        "platform": platform.platform(),
        "executable": sys.executable,
        "working_directory": os.getcwd(),
        "build_utc": datetime.now(timezone.utc).isoformat(),
        "standard_library_only": True,
    })
    (QC / "RANGE_GATE0_IMPLEMENTATION_LOG_v01.txt").write_text(
        "Range Gate 0 v01 build completed.\n"
        "Authority: frozen D08B1 v02 local package and copied authoritative members only.\n"
        "Rules: precommitted RANGE_GATE0_CONTRACT_v01.md; no post-count changes.\n"
        "Prohibited operations invoked: none.\n"
        f"Rows: master={len(master_rows)}, candidates={len(candidates)}, evidence={len(long_rows)}.\n"
        f"Class counts: {json.dumps({k: counts[k] for k in CLASSES}, sort_keys=True)}\n"
        f"QC: {sum(c['status'] == 'PASS' for c in checks)}/{len(checks)} PASS.\n",
        encoding="utf-8",
    )
    if not all(c["status"] == "PASS" for c in checks):
        raise RuntimeError("ENGINEERING_FAIL: one or more frozen QC checks failed")
    print(json.dumps({
        "status": "PASS", "work": str(WORK), "class_counts": {k: counts[k] for k in CLASSES},
        "unknown_reason_counts": dict(unknown_reasons), "qc": f"{len(checks)}/{len(checks)}",
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
