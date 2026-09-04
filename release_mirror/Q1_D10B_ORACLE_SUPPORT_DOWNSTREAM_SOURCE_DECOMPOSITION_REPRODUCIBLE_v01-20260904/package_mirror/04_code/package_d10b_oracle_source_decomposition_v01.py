#!/usr/bin/env python3
"""Create and independently verify the immutable D10B reproducible package."""

from __future__ import annotations

import csv
import hashlib
import json
import shutil
import zipfile
from pathlib import Path


ROOT = Path(r"C:\range_paper")
TASK_DIR = "d10b_oracle_source_decomposition_v01"
PACKAGE_NAME = "Q1_D10B_ORACLE_SUPPORT_DOWNSTREAM_SOURCE_DECOMPOSITION_REPRODUCIBLE_v01"
ARCHIVE = ROOT / "10_archive" / TASK_DIR
STAGE = ARCHIVE / "package" / PACKAGE_NAME
ZIP_PATH = ARCHIVE / f"{PACKAGE_NAME}.zip"
SIDECAR = ARCHIVE / f"{PACKAGE_NAME}.zip.sha256"
OUT = ROOT / "04_derived" / TASK_DIR
QC = ROOT / "05_qc" / TASK_DIR
SRC = ROOT / "06_src" / TASK_DIR
D10A = ROOT / "10_archive" / "d10a_real_layout_nonoracle_v01" / "Q1_D10A_REAL_LAYOUT_NONORACLE_OBSERVATION_CALIBRATION_REPRODUCIBLE_v01.zip"


def sha256(path, chunk=8 * 1024 * 1024):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(chunk), b""):
            digest.update(block)
    return digest.hexdigest()


def write_csv(path, rows, fields=None):
    rows = list(rows)
    if fields is None:
        fields = list(rows[0])
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with Path(path).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def csv_rows(path):
    with Path(path).open("r", encoding="utf-8-sig", newline="") as handle:
        return sum(1 for _ in csv.reader(handle)) - 1


def create_registry_delta():
    fields = ["TASK_ID", "input_authority_commit_version", "exact_source_path_or_release_identity", "sha256", "bytes", "status", "scientific_output_changed", "publication_candidate", "Methods_role", "Data_role", "Code_role", "QC_role"]
    rows = []
    entries = [
        ("AUTH_CONTRACT", ROOT / "00_control" / "Q1_D10B_ORACLE_SUPPORT_DOWNSTREAM_SOURCE_DECOMPOSITION_CONTRACT_v01.md", "PASS", "NO_INPUT_ONLY", "FROZEN_DIAGNOSTIC_AUTHORITY", "SOURCE_AUTHORITY", "NONE", "IDENTITY_VERIFICATION"),
        ("AUTH_EXECUTION_FREEZE", ROOT / "00_control" / "D10B_ORACLE_SUPPORT_SOURCE_DECOMPOSITION_EXECUTION_FREEZE_v01.md", "PASS", "NO_INPUT_ONLY", "FROZEN_DIAGNOSTIC_AUTHORITY", "SOURCE_AUTHORITY", "NONE", "IDENTITY_VERIFICATION"),
        ("AUTH_D10A_RELEASE", D10A, "PASS", "NO_INPUT_ONLY", "FROZEN_INPUT_AUTHORITY", "SYNTHETIC_ONLY", "NONE", "IDENTITY_VERIFICATION"),
    ]
    for path in sorted(OUT.iterdir()):
        if path.is_file():
            entries.append(("DIAGNOSTIC_COMPLETE_READY_FOR_MAINLINE_SOURCE_ATTRIBUTION", path, "READY_FOR_MAINLINE_DIAGNOSTIC_REVIEW", "YES_NEW_SYNTHETIC_DIAGNOSTIC_OUTPUT", "D10B_SOURCE_DECOMPOSITION_DIAGNOSTIC", "SYNTHETIC_ONLY", "NONE", "TRACEABILITY"))
    for version, path, status, changed, methods, data, code, qc in entries:
        rows.append({"TASK_ID": "D10B_ORACLE_SUPPORT_DOWNSTREAM_SOURCE_DECOMPOSITION_v01", "input_authority_commit_version": version, "exact_source_path_or_release_identity": str(path), "sha256": sha256(path), "bytes": path.stat().st_size, "status": status, "scientific_output_changed": changed, "publication_candidate": "NO", "Methods_role": methods, "Data_role": data, "Code_role": code, "QC_role": qc})
    target = OUT / "REGISTRY_DELTA_v01.csv"
    write_csv(target, rows, fields)
    return target


def copy_inputs(registry):
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
        (ROOT / "00_control" / "Q1_D10B_ORACLE_SUPPORT_DOWNSTREAM_SOURCE_DECOMPOSITION_CONTRACT_v01.md", Path("00_control") / "Q1_D10B_ORACLE_SUPPORT_DOWNSTREAM_SOURCE_DECOMPOSITION_CONTRACT_v01.md"),
        (ROOT / "00_control" / "D10B_ORACLE_SUPPORT_SOURCE_DECOMPOSITION_EXECUTION_FREEZE_v01.md", Path("00_control") / "D10B_ORACLE_SUPPORT_SOURCE_DECOMPOSITION_EXECUTION_FREEZE_v01.md"),
        (D10A, Path("01_authoritative_input_identity") / D10A.name),
    ])
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
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6, allowZip64=True) as archive:
        for path in sorted(Path(source).rglob("*")):
            if not path.is_file():
                continue
            relative = (Path(PACKAGE_NAME) / path.relative_to(source)).as_posix()
            info = zipfile.ZipInfo(relative, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            with path.open("rb") as handle:
                archive.writestr(info, handle.read(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=6)


def validate_package(sums):
    prefix = PACKAGE_NAME + "/"
    required = {
        "02_outputs/Q1_D10B_ORACLE_WORLD_IDENTITIES_v01.csv",
        "02_outputs/Q1_D10B_L0_ORACLE_SUPPORT_LATENT_ABUNDANCE_RESULTS_v01.csv",
        "02_outputs/Q1_D10B_L1_ORACLE_SUPPORT_OBSERVED_ABUNDANCE_RESULTS_v01.csv",
        "02_outputs/Q1_D10B_L2_D10A_REFERENCE_RESULTS_v01.csv",
        "02_outputs/Q1_D10B_NULL_GAIN_SOURCE_DECOMPOSITION_v01.csv",
        "02_outputs/Q1_D10B_STRONG_NULL_SEPARATION_v01.csv",
        "02_outputs/Q1_D10B_DIAGNOSTIC_SUMMARY_v01.csv",
        "02_outputs/Q1_D10B_RESULT_NOTE_v01.md",
        "02_outputs/REGISTRY_DELTA_v01.csv",
        "SHA256SUMS.csv",
    }
    with zipfile.ZipFile(ZIP_PATH) as archive:
        names = set(archive.namelist())
        missing = sorted(prefix + name for name in required if prefix + name not in names)
        mismatches = []
        for row in sums:
            payload = archive.read(prefix + row["relative_path"])
            observed = hashlib.sha256(payload).hexdigest()
            if observed != row["sha256"] or len(payload) != int(row["size_bytes"]):
                mismatches.append(row["relative_path"])
        nested = archive.read(prefix + "01_authoritative_input_identity/" + D10A.name)
        nested_sha = hashlib.sha256(nested).hexdigest()
        member_count = len(names)
    temp_zip = ARCHIVE / (PACKAGE_NAME + ".determinism_check.tmp.zip")
    deterministic_zip(STAGE, temp_zip)
    deterministic_match = sha256(temp_zip) == sha256(ZIP_PATH)
    temp_zip.unlink()
    independent = json.loads((QC / "D10B_INDEPENDENT_POSTRUN_VALIDATION_v01.json").read_text(encoding="utf-8"))
    artifact = json.loads((QC / "D10B_ARTIFACT_TOOL_TABULAR_VALIDATION_v01.json").read_text(encoding="utf-8"))
    result = {
        "status": "PASS" if not missing and not mismatches and nested_sha == "20e5d3ed33df6414b72a6e679d5349f3b10fe6397ce73f98b51d0bcc96033013" and deterministic_match and independent["status"] == "PASS" and artifact["status"] == "PASS" else "FAIL",
        "zip_path": str(ZIP_PATH),
        "zip_size_bytes": ZIP_PATH.stat().st_size,
        "zip_sha256": sha256(ZIP_PATH),
        "zip_member_count": member_count,
        "required_members_missing": missing,
        "checksum_mismatches": mismatches,
        "nested_d10a_sha256": nested_sha,
        "nested_d10a_identity": "PASS" if nested_sha == "20e5d3ed33df6414b72a6e679d5349f3b10fe6397ce73f98b51d0bcc96033013" else "FAIL",
        "deterministic_rebuild_sha256_match": deterministic_match,
        "independent_postrun_validation": independent["status"],
        "artifact_tool_tabular_validation": artifact["status"],
    }
    return result


def delivery_index(validation):
    rows = []
    for path in sorted(STAGE.rglob("*")):
        if path.is_file():
            relative = path.relative_to(STAGE).as_posix()
            count = csv_rows(path) if path.suffix.lower() == ".csv" else "NA"
            authoritative = "YES" if relative.startswith("02_outputs/Q1_D10B_") or relative == "02_outputs/REGISTRY_DELTA_v01.csv" else "NO"
            rows.append((relative, path.stat().st_size, sha256(path), count, authoritative))
    lines = [
        "# D10B delivery index v01", "",
        f"Terminal status: `DIAGNOSTIC_COMPLETE_READY_FOR_MAINLINE_SOURCE_ATTRIBUTION`", "",
        f"Reproducible ZIP: `{ZIP_PATH}`", "",
        f"ZIP bytes: `{validation['zip_size_bytes']}`", "",
        f"ZIP SHA-256: `{validation['zip_sha256']}`", "",
        "D10B is diagnostic-only: no scientific PASS/FAIL, model winner, repair, real species, D10C, or real Q1.", "",
        "file | purpose | rows | bytes | SHA-256 | authoritative output", "---|---|---:|---:|---|---",
    ]
    purpose = {
        ".csv": "machine-readable audit/result table",
        ".json": "parameters or QC metadata",
        ".md": "contract, note, or log",
        ".py": "reproducibility code",
        ".mjs": "artifact-tool validation code",
        ".zip": "frozen authoritative predecessor",
    }
    for relative, size, digest, count, authoritative in rows:
        lines.append(f"`{relative}` | {purpose.get(Path(relative).suffix.lower(), 'package file')} | {count} | {size} | `{digest}` | {authoritative}")
    target = ARCHIVE / "D10B_DELIVERY_INDEX_v01.md"
    target.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return target


def transfer_manifest(delivery, postvalidation):
    fields = ["local_path", "relative_path", "role", "upload_target", "required", "mainline_priority", "size_bytes", "sha256", "notes"]
    rows = []
    def add(path, relative, role, target, required, priority, notes):
        rows.append({"local_path": str(path), "relative_path": relative, "role": role, "upload_target": target, "required": required, "mainline_priority": priority, "size_bytes": path.stat().st_size, "sha256": sha256(path), "notes": notes})
    add(ZIP_PATH, "release_assets/" + ZIP_PATH.name, "reproducible_zip", "release", "YES", "IMPORTANT", "Complete immutable D10B package")
    add(SIDECAR, "release_assets/" + SIDECAR.name, "checksum", "both", "YES", "IMPORTANT", "ZIP SHA-256 sidecar")
    add(delivery, delivery.name, "delivery_index", "mirror", "YES", "FIRST_READ", "Mainline entry point")
    add(postvalidation, postvalidation.name, "qc_json", "mirror", "YES", "IMPORTANT", "Postpackage validation")
    for path in sorted(STAGE.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(STAGE).as_posix()
        suffix = path.suffix.lower()
        if relative.startswith("01_authoritative_input_identity/") and suffix == ".zip":
            add(path, "package_mirror/" + relative, "source", "local_only", "NO", "ARCHIVE_ONLY", "Already preserved inside complete D10B ZIP and in canonical D10A release")
            continue
        if suffix not in {".csv", ".md", ".json", ".txt", ".py", ".mjs"}:
            continue
        role = "audit_csv" if suffix == ".csv" else "qc_json" if suffix == ".json" else "source" if suffix in {".py", ".mjs"} else "result_note" if "RESULT_NOTE" in path.name else "other"
        priority = "FIRST_READ" if "RESULT_NOTE" in path.name else "IMPORTANT" if relative.startswith("02_outputs/") or relative.startswith("03_qc/") else "SUPPORTING"
        required = "YES" if relative.startswith("02_outputs/") or relative.startswith("03_qc/") or path.name == "SHA256SUMS.csv" else "NO"
        add(path, "package_mirror/" + relative, role, "mirror", required, priority, "Directly readable package member")
    target = ARCHIVE / "TRANSFER_MANIFEST_v01.csv"
    write_csv(target, rows, fields)
    return target


def main():
    if STAGE.exists() or ZIP_PATH.exists() or SIDECAR.exists():
        raise SystemExit("Refusing to overwrite an existing frozen D10B package")
    ARCHIVE.mkdir(parents=True, exist_ok=True)
    create_registry_delta()
    STAGE.mkdir(parents=True)
    copy_inputs(OUT / "REGISTRY_DELTA_v01.csv")
    sums = package_sums()
    deterministic_zip(STAGE, ZIP_PATH)
    zip_digest = sha256(ZIP_PATH)
    SIDECAR.write_text(f"{zip_digest}  {ZIP_PATH.name}\n", encoding="ascii", newline="\n")
    validation = validate_package(sums)
    postvalidation = ARCHIVE / "D10B_POSTPACKAGE_VALIDATION_v01.json"
    postvalidation.write_text(json.dumps(validation, indent=2) + "\n", encoding="utf-8", newline="\n")
    if validation["status"] != "PASS":
        raise SystemExit("Postpackage validation failed")
    delivery = delivery_index(validation)
    manifest = transfer_manifest(delivery, postvalidation)
    print(json.dumps({"status": "PASS", "zip": str(ZIP_PATH), "bytes": ZIP_PATH.stat().st_size, "sha256": zip_digest, "members": validation["zip_member_count"], "transfer_manifest": str(manifest), "transfer_rows": csv_rows(manifest)}, indent=2))


if __name__ == "__main__":
    main()
