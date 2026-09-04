#!/usr/bin/env python3
"""Build the immutable D10C estimator-authority-failure audit package."""

from __future__ import annotations

import csv
import hashlib
import json
import shutil
import zipfile
from pathlib import Path


ROOT = Path(r"C:\range_paper")
TASK_DIR = "d10c_fia_design_abundance_v01"
PACKAGE_NAME = "Q1_D10C_FIA_DESIGN_BASED_ABUNDANCE_ESTIMATOR_AUTHORITY_FAILURE_REPRODUCIBLE_v01"
ARCHIVE = ROOT / "10_archive" / TASK_DIR
STAGE = ARCHIVE / "package" / PACKAGE_NAME
ZIP_PATH = ARCHIVE / f"{PACKAGE_NAME}.zip"
SIDECAR = ARCHIVE / f"{PACKAGE_NAME}.zip.sha256"
OUT = ROOT / "04_derived" / TASK_DIR
QC = ROOT / "05_qc" / TASK_DIR
SRC = ROOT / "06_src" / TASK_DIR
STATUS = "INPUT_BLOCKED_ABUNDANCE_ESTIMATOR_AUTHORITY_FAILURE"
INPUTS = [
    ROOT / "10_archive" / "d10a_real_layout_nonoracle_v01" / "Q1_D10A_REAL_LAYOUT_NONORACLE_OBSERVATION_CALIBRATION_REPRODUCIBLE_v01.zip",
    ROOT / "10_archive" / "d10b_oracle_source_decomposition_v01" / "Q1_D10B_ORACLE_SUPPORT_DOWNSTREAM_SOURCE_DECOMPOSITION_REPRODUCIBLE_v01.zip",
    ROOT / "10_archive" / "d09c_t2_final_correction_v02" / "Q1_D09C_T2_FINAL_CORRECTION_REPRODUCIBLE_v02.zip",
]
EXPECTED_INPUT_HASHES = {
    "Q1_D10A_REAL_LAYOUT_NONORACLE_OBSERVATION_CALIBRATION_REPRODUCIBLE_v01.zip": "20e5d3ed33df6414b72a6e679d5349f3b10fe6397ce73f98b51d0bcc96033013",
    "Q1_D10B_ORACLE_SUPPORT_DOWNSTREAM_SOURCE_DECOMPOSITION_REPRODUCIBLE_v01.zip": "cb041fca5897f31c8ea0bf2a3b29a262a5c83ef44bdfda9a37a0394cfc7cafeb",
    "Q1_D09C_T2_FINAL_CORRECTION_REPRODUCIBLE_v02.zip": "07cb461121c71ef46990fea3e0cf9d8f139fd873234b9f57910ff10c7c33752f",
}


def sha256(path, chunk=8 * 1024 * 1024):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(chunk), b""):
            digest.update(block)
    return digest.hexdigest()


def write_csv(path, rows, fields=None):
    rows = list(rows)
    fields = fields or list(rows[0])
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with Path(path).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def csv_rows(path):
    with Path(path).open("r", encoding="utf-8-sig", newline="") as handle:
        return max(sum(1 for _ in csv.reader(handle)) - 1, 0)


def stage_files():
    mappings = []
    for path in sorted(OUT.iterdir()):
        if path.is_file():
            mappings.append((path, Path("02_outputs") / path.name))
    for path in sorted(QC.iterdir()):
        if path.is_file():
            mappings.append((path, Path("03_qc") / path.name))
    for path in sorted(SRC.iterdir()):
        if path.is_file() and path.suffix.lower() in {".py", ".mjs", ".json"}:
            mappings.append((path, Path("04_code") / path.name))
    mappings.extend([
        (ROOT / "00_control" / "Q1_D10C_FIA_DESIGN_BASED_ABUNDANCE_MEASUREMENT_CALIBRATION_CONTRACT_v01.md", Path("00_control") / "Q1_D10C_FIA_DESIGN_BASED_ABUNDANCE_MEASUREMENT_CALIBRATION_CONTRACT_v01.md"),
        (ROOT / "00_control" / "D10C_ABUNDANCE_ESTIMATOR_AUTHORITY_GATE_EXECUTION_FREEZE_v01.md", Path("00_control") / "D10C_ABUNDANCE_ESTIMATOR_AUTHORITY_GATE_EXECUTION_FREEZE_v01.md"),
    ])
    for input_path in INPUTS:
        mappings.append((input_path, Path("01_authoritative_inputs") / input_path.name))
    for source, relative in mappings:
        target = STAGE / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def package_sums():
    rows = []
    for path in sorted(STAGE.rglob("*")):
        if path.is_file() and path.name != "SHA256SUMS.csv":
            rows.append({"relative_path": path.relative_to(STAGE).as_posix(), "size_bytes": path.stat().st_size, "sha256": sha256(path)})
    write_csv(STAGE / "SHA256SUMS.csv", rows, ["relative_path", "size_bytes", "sha256"])
    return rows


def deterministic_zip(source, target):
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=3, allowZip64=True) as archive:
        for path in sorted(Path(source).rglob("*")):
            if not path.is_file():
                continue
            relative = (Path(PACKAGE_NAME) / path.relative_to(source)).as_posix()
            info = zipfile.ZipInfo(relative, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            with path.open("rb") as handle:
                archive.writestr(info, handle.read(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=3)


def validate(sums):
    prefix = PACKAGE_NAME + "/"
    required = {
        "02_outputs/Q1_D10C_ABUNDANCE_ESTIMATOR_AUTHORITY_v01.md",
        "02_outputs/Q1_D10C_ESTIMATOR_AUTHORITY_GAP_AUDIT_v01.csv",
        "02_outputs/Q1_D10C_REQUIRED_OUTPUT_DISPOSITION_v01.csv",
        "02_outputs/Q1_D10C_RESULT_NOTE_v01.md",
        "02_outputs/REGISTRY_DELTA_v01.csv",
        "03_qc/D10C_TERMINAL_STATUS_v01.json",
        "03_qc/D10C_INDEPENDENT_VALIDATION_v01.json",
        "03_qc/D10C_ARTIFACT_TOOL_TABULAR_VALIDATION_v01.json",
        "SHA256SUMS.csv",
    }
    forbidden_science = {
        "02_outputs/Q1_D10C_SYNTHETIC_POPULATION_TRUTH_v01.csv",
        "02_outputs/Q1_D10C_SYNTHETIC_PLOT_OBSERVATIONS_v01.csv.gz",
        "02_outputs/Q1_D10C_A2_DESIGN_BASED_CELL_MASS_ESTIMATES_v01.csv.gz",
        "02_outputs/Q1_D10C_ABUNDANCE_RECOVERY_METRICS_v01.csv",
        "02_outputs/Q1_D10C_ORACLE_Q1_PRESERVATION_RESULTS_v01.csv",
    }
    with zipfile.ZipFile(ZIP_PATH) as archive:
        names = set(archive.namelist())
        missing = sorted(prefix + name for name in required if prefix + name not in names)
        forbidden_present = sorted(prefix + name for name in forbidden_science if prefix + name in names)
        mismatches = []
        for row in sums:
            payload = archive.read(prefix + row["relative_path"])
            if len(payload) != int(row["size_bytes"]) or hashlib.sha256(payload).hexdigest() != row["sha256"]:
                mismatches.append(row["relative_path"])
        input_hashes = {}
        for name, expected in EXPECTED_INPUT_HASHES.items():
            payload = archive.read(prefix + "01_authoritative_inputs/" + name)
            input_hashes[name] = hashlib.sha256(payload).hexdigest()
        member_count = len(names)
    temporary = ARCHIVE / (PACKAGE_NAME + ".determinism_check.tmp.zip")
    deterministic_zip(STAGE, temporary)
    deterministic_match = sha256(temporary) == sha256(ZIP_PATH)
    temporary.unlink()
    independent = json.loads((QC / "D10C_INDEPENDENT_VALIDATION_v01.json").read_text(encoding="utf-8"))
    artifact = json.loads((QC / "D10C_ARTIFACT_TOOL_TABULAR_VALIDATION_v01.json").read_text(encoding="utf-8"))
    inputs_ok = all(input_hashes[name] == expected for name, expected in EXPECTED_INPUT_HASHES.items())
    status = "PASS" if not missing and not forbidden_present and not mismatches and inputs_ok and deterministic_match and independent["status"] == "PASS" and artifact["status"] == "PASS" else "FAIL"
    return {"status": status, "terminal_status": STATUS, "zip_path": str(ZIP_PATH), "zip_size_bytes": ZIP_PATH.stat().st_size, "zip_sha256": sha256(ZIP_PATH), "zip_member_count": member_count, "required_members_missing": missing, "forbidden_scientific_members_present": forbidden_present, "checksum_mismatches": mismatches, "authoritative_input_sha256": input_hashes, "authoritative_input_identity": "PASS" if inputs_ok else "FAIL", "deterministic_rebuild_sha256_match": deterministic_match, "independent_validation": independent["status"], "artifact_tool_tabular_validation": artifact["status"], "scientific_calibration_run": False}


def delivery_index(validation):
    lines = [
        "# D10C estimator-authority-failure delivery index v01", "",
        f"Terminal status: `{STATUS}`", "",
        f"Reproducible ZIP: `{ZIP_PATH}`", "",
        f"ZIP bytes: `{validation['zip_size_bytes']}`", "",
        f"ZIP SHA-256: `{validation['zip_sha256']}`", "",
        "The authority gate stopped D10C before any A0/A1/A2 calibration or downstream result. This is not a scientific FAIL.", "",
        "file | rows | bytes | SHA-256 | role", "---|---:|---:|---|---",
    ]
    for path in sorted(STAGE.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(STAGE).as_posix()
        rows = csv_rows(path) if path.suffix.lower() == ".csv" else "NA"
        role = "authoritative predecessor" if relative.startswith("01_authoritative_inputs/") else "blocked-state evidence" if relative.startswith("02_outputs/") else "QC" if relative.startswith("03_qc/") else "reproducibility code" if relative.startswith("04_code/") else "contract/checksum"
        lines.append(f"`{relative}` | {rows} | {path.stat().st_size} | `{sha256(path)}` | {role}")
    target = ARCHIVE / "D10C_DELIVERY_INDEX_v01.md"
    target.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return target


def transfer_manifest(delivery, postvalidation):
    fields = ["local_path", "relative_path", "role", "upload_target", "required", "mainline_priority", "size_bytes", "sha256", "notes"]
    rows = []
    def add(path, relative, role, target, required, priority, notes):
        rows.append({"local_path": str(path), "relative_path": relative, "role": role, "upload_target": target, "required": required, "mainline_priority": priority, "size_bytes": path.stat().st_size, "sha256": sha256(path), "notes": notes})
    add(ZIP_PATH, "release_assets/" + ZIP_PATH.name, "reproducible_zip", "release", "YES", "IMPORTANT", "Complete authority-blocked D10C audit package")
    add(SIDECAR, "release_assets/" + SIDECAR.name, "checksum", "both", "YES", "IMPORTANT", "ZIP SHA-256 sidecar")
    add(delivery, delivery.name, "delivery_index", "mirror", "YES", "FIRST_READ", "Mainline entry point")
    add(postvalidation, postvalidation.name, "qc_json", "mirror", "YES", "IMPORTANT", "Postpackage validation")
    for path in sorted(STAGE.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(STAGE).as_posix()
        if relative.startswith("01_authoritative_inputs/"):
            add(path, "package_mirror/" + relative, "source", "local_only", "NO", "ARCHIVE_ONLY", "Preserved inside complete ZIP; predecessor already has canonical release")
            continue
        if path.suffix.lower() not in {".csv", ".md", ".json", ".txt", ".py", ".mjs"}:
            continue
        role = "audit_csv" if path.suffix.lower() == ".csv" else "qc_json" if path.suffix.lower() == ".json" else "source" if path.suffix.lower() in {".py", ".mjs"} else "result_note" if "RESULT_NOTE" in path.name else "other"
        priority = "FIRST_READ" if "RESULT_NOTE" in path.name or "ABUNDANCE_ESTIMATOR_AUTHORITY" in path.name else "IMPORTANT" if relative.startswith(("02_outputs/", "03_qc/")) else "SUPPORTING"
        required = "YES" if relative.startswith(("02_outputs/", "03_qc/")) or path.name == "SHA256SUMS.csv" else "NO"
        add(path, "package_mirror/" + relative, role, "mirror", required, priority, "Directly readable package member")
    target = ARCHIVE / "TRANSFER_MANIFEST_v01.csv"
    write_csv(target, rows, fields)
    return target


def main():
    if STAGE.exists() or ZIP_PATH.exists() or SIDECAR.exists():
        raise SystemExit("Refusing to overwrite an existing frozen D10C package")
    ARCHIVE.mkdir(parents=True, exist_ok=True)
    STAGE.mkdir(parents=True)
    stage_files()
    sums = package_sums()
    deterministic_zip(STAGE, ZIP_PATH)
    digest = sha256(ZIP_PATH)
    SIDECAR.write_text(f"{digest}  {ZIP_PATH.name}\n", encoding="ascii", newline="\n")
    validation = validate(sums)
    postvalidation = ARCHIVE / "D10C_POSTPACKAGE_VALIDATION_v01.json"
    postvalidation.write_text(json.dumps(validation, indent=2) + "\n", encoding="utf-8", newline="\n")
    if validation["status"] != "PASS":
        raise SystemExit("Postpackage validation failed")
    delivery = delivery_index(validation)
    manifest = transfer_manifest(delivery, postvalidation)
    print(json.dumps({"status": "PASS", "terminal_status": STATUS, "zip": str(ZIP_PATH), "bytes": ZIP_PATH.stat().st_size, "sha256": digest, "members": validation["zip_member_count"], "transfer_manifest": str(manifest), "transfer_rows": csv_rows(manifest)}, indent=2))


if __name__ == "__main__":
    main()
