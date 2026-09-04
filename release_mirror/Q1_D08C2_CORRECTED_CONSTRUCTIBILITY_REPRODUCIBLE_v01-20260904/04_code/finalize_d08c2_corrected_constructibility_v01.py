#!/usr/bin/env python3
"""Freeze, package, hash, and validate D08C2 corrected v01 outputs."""

import csv
import hashlib
import json
import os
import shutil
import zipfile
from pathlib import Path


ROOT = Path(r"C:\range_paper")
SRC = ROOT / "06_src" / "d08c2_corrected_constructibility_v01"
OUT = ROOT / "04_derived" / "d08c2_corrected_constructibility_v01"
QC = ROOT / "05_qc" / "d08c2_corrected_constructibility_v01"
ARC = ROOT / "10_archive" / "d08c2_corrected_constructibility_v01"
PKG_NAME = "Q1_D08C2_CORRECTED_CONSTRUCTIBILITY_REPRODUCIBLE_v01"
PKG = ARC / PKG_NAME
ZIP = ARC / f"{PKG_NAME}.zip"
SIDECAR = ARC / f"{PKG_NAME}.zip.sha256"


def sha(path, chunk=8 * 1024 * 1024):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def rows(path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path, records, fields=None):
    if fields is None:
        fields = list(records[0]) if records else []
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(records)


def line_count(path):
    if path.suffix.lower() not in {".csv", ".md", ".json", ".py", ".txt"}:
        return ""
    with path.open("r", encoding="utf-8-sig", errors="replace") as f:
        return sum(1 for _ in f)


def role(path):
    name = path.name
    if name.endswith("CONTRACT_v01.md") or "FREEZE" in name:
        return "frozen_control"
    if name.startswith("Q1_D08C2_") and name.endswith(".csv"):
        return "authoritative_provisional_output"
    if name == "Q1_D08C2_RESULT_NOTE_v01.md":
        return "result_note"
    if name == "REGISTRY_DELTA_v01.csv":
        return "registry_delta"
    if path.suffix == ".py":
        return "reproduction_code"
    if path.suffix == ".json" or "QC" in name or "LOG" in name:
        return "qc"
    return "supporting"


def build_zip(source, destination):
    epoch = (1980, 1, 1, 0, 0, 0)
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for path in sorted((p for p in source.rglob("*") if p.is_file()), key=lambda p: p.relative_to(source).as_posix()):
            arcname = f"{source.name}/{path.relative_to(source).as_posix()}"
            info = zipfile.ZipInfo(arcname, epoch)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            zf.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def main():
    ARC.mkdir(parents=True, exist_ok=True)
    if PKG.exists():
        resolved = PKG.resolve()
        if resolved.parent != ARC.resolve() or resolved.name != PKG_NAME:
            raise RuntimeError("Unsafe package removal target")
        shutil.rmtree(PKG)
    for path in (ZIP, SIDECAR):
        if path.exists():
            path.unlink()

    copies = [
        (ROOT / "00_control" / "Q1_D08C2_CORRECTED_CONSTRUCTIBILITY_CONTRACT_v01.md", PKG / "00_control" / "Q1_D08C2_CORRECTED_CONSTRUCTIBILITY_CONTRACT_v01.md"),
        (ROOT / "00_control" / "D08C2_CORRECTED_CONSTRUCTIBILITY_EXECUTION_FREEZE_v01.md", PKG / "00_control" / "D08C2_CORRECTED_CONSTRUCTIBILITY_EXECUTION_FREEZE_v01.md"),
        (ROOT / "10_archive" / "range_gate0_v02_corrected" / "Q1_RANGE_GATE0_V02_CORRECTED_GEOGRAPHIC_SEMANTICS_REPRODUCIBLE_v01" / "SHA256SUMS.csv", PKG / "01_authoritative_input_identity" / "RANGE_GATE0_V02_SHA256SUMS.csv"),
        (ROOT / "10_archive" / "d09c_t2_final_correction_v02" / "Q1_D09C_T2_FINAL_CORRECTION_REPRODUCIBLE_v02" / "SHA256SUMS.csv", PKG / "01_authoritative_input_identity" / "D09C_T2_FINAL_V02_SHA256SUMS.csv"),
        (ROOT / "02_raw" / "fia_t2_2023_observational_gap_v01" / "manifests" / "Q1_D08C2_CAORWA_OBS_RAW_ASSET_MANIFEST_v01.csv", PKG / "01_authoritative_input_identity" / "Q1_D08C2_CAORWA_OBS_RAW_ASSET_MANIFEST_v01.csv"),
    ]
    for path in sorted(OUT.iterdir()):
        if path.is_file():
            copies.append((path, PKG / "02_outputs" / path.name))
    for path in sorted(QC.iterdir()):
        if path.is_file() and path.name != "D08C2_CORRECTED_BLOCKED_STATUS_v01.json":
            copies.append((path, PKG / "03_qc" / path.name))
    for name in ("build_d08c2_corrected_constructibility_v01.py", "verify_d08c2_corrected_constructibility_v01.py", "finalize_d08c2_corrected_constructibility_v01.py", "parameters_d08c2_corrected_constructibility_v01.json"):
        copies.append((SRC / name, PKG / "04_code" / name))
    for source, target in copies:
        if not source.exists():
            raise RuntimeError(f"Missing required package input: {source}")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)

    independent = json.loads((PKG / "03_qc" / "D08C2_CORRECTED_INDEPENDENT_VALIDATION_v01.json").read_text(encoding="utf-8"))
    build = json.loads((PKG / "03_qc" / "D08C2_CORRECTED_BUILD_SUMMARY_v01.json").read_text(encoding="utf-8"))
    if independent["validation_status"] != "PASS" or build["task_status"] != "PASS_READY_FOR_MAINLINE_OBSERVATION_GATE_AUDIT":
        raise RuntimeError("Prepackage scientific validation did not pass")

    indexed = []
    for path in sorted((p for p in PKG.rglob("*") if p.is_file()), key=lambda p: p.relative_to(PKG).as_posix()):
        rel = path.relative_to(PKG).as_posix()
        indexed.append({"relative_path": rel, "role": role(path), "line_or_row_count_including_header": line_count(path), "size_bytes": path.stat().st_size, "sha256": sha(path), "authoritative_output": "YES" if rel.startswith("02_outputs/Q1_D08C2_") else "NO"})
    index_lines = [
        "# D08C2 corrected constructibility delivery index v01",
        "",
        f"Task status: **{build['task_status']}**",
        "",
        "The package is a bounded D1-D4 constructibility result, not a final cohort. Large raw FIA assets are intentionally referenced by exact path/hash and are not duplicated. The executable runner performs no network acquisition.",
        "",
        "| Relative path | Role | Lines/rows incl. header | Bytes | SHA-256 | Authoritative output |",
        "|---|---:|---:|---:|---|---:|",
    ]
    for r in indexed:
        index_lines.append(f"| `{r['relative_path']}` | {r['role']} | {r['line_or_row_count_including_header']} | {r['size_bytes']} | `{r['sha256']}` | {r['authoritative_output']} |")
    index_lines.extend(["", "STOP: return to scientific mainline for D08C2 audit.", ""])
    (PKG / "D08C2_DELIVERY_INDEX_v01.md").write_text("\n".join(index_lines), encoding="utf-8")

    sum_rows = []
    for path in sorted((p for p in PKG.rglob("*") if p.is_file() and p.name != "SHA256SUMS.csv"), key=lambda p: p.relative_to(PKG).as_posix()):
        sum_rows.append({"relative_path": path.relative_to(PKG).as_posix(), "size_bytes": path.stat().st_size, "sha256": sha(path)})
    write_csv(PKG / "SHA256SUMS.csv", sum_rows, ["relative_path", "size_bytes", "sha256"])
    shutil.copy2(PKG / "SHA256SUMS.csv", ARC / "SHA256SUMS.csv")
    shutil.copy2(PKG / "D08C2_DELIVERY_INDEX_v01.md", ARC / "D08C2_DELIVERY_INDEX_v01.md")

    build_zip(PKG, ZIP)
    zip_hash = sha(ZIP)
    SIDECAR.write_text(f"{zip_hash}  {ZIP.name}\n", encoding="utf-8")
    test_zip = ARC / f".{PKG_NAME}.determinism_test.zip"
    build_zip(PKG, test_zip)
    deterministic = sha(test_zip) == zip_hash
    test_zip.unlink()

    sums = rows(PKG / "SHA256SUMS.csv")
    package_hash_failures = []
    for r in sums:
        path = PKG / Path(r["relative_path"])
        if not path.exists() or path.stat().st_size != int(r["size_bytes"]) or sha(path) != r["sha256"]:
            package_hash_failures.append(r["relative_path"])
    with zipfile.ZipFile(ZIP) as zf:
        zip_members = sorted(zf.namelist())
        expected_members = sorted(f"{PKG_NAME}/{p.relative_to(PKG).as_posix()}" for p in PKG.rglob("*") if p.is_file())
        zip_member_match = zip_members == expected_members and zf.testzip() is None
    post = {
        "validation_status": "PASS" if deterministic and not package_hash_failures and zip_member_match and independent["validation_status"] == "PASS" else "FAIL",
        "zip_path": str(ZIP),
        "zip_size_bytes": ZIP.stat().st_size,
        "zip_sha256": zip_hash,
        "deterministic_rebuild_match": deterministic,
        "package_hash_failure_count": len(package_hash_failures),
        "package_hash_failures": package_hash_failures,
        "zip_member_set_match": zip_member_match,
        "independent_validation_status": independent["validation_status"],
        "task_status": build["task_status"],
        "national_fiadb_downloaded_by_finalizer": False,
    }
    post_path = ARC / "D08C2_CORRECTED_POSTPACKAGE_VALIDATION_v01.json"
    post_path.write_text(json.dumps(post, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if post["validation_status"] != "PASS":
        raise RuntimeError(f"Postpackage validation failed: {post}")

    transfer = []
    def add(path, relative, file_role, target, required, priority, notes):
        transfer.append({"local_path": str(path), "relative_path": relative, "role": file_role, "upload_target": target, "required": required, "mainline_priority": priority, "size_bytes": path.stat().st_size, "sha256": sha(path), "notes": notes})
    add(ZIP, f"release_assets/{ZIP.name}", "reproducible_zip", "release", "YES", "IMPORTANT", "Complete deterministic package; large frozen raw data referenced by verified local identity, not duplicated.")
    add(SIDECAR, f"release_assets/{SIDECAR.name}", "checksum", "both", "YES", "IMPORTANT", "ZIP SHA-256 sidecar.")
    add(post_path, post_path.name, "qc_json", "mirror", "YES", "IMPORTANT", "Postpackage hash, member-set, and deterministic rebuild validation.")
    for path in sorted((p for p in PKG.rglob("*") if p.is_file()), key=lambda p: p.relative_to(PKG).as_posix()):
        rel = path.relative_to(PKG).as_posix()
        if path.suffix.lower() not in {".csv", ".md", ".json", ".py", ".txt"}:
            continue
        priority = "FIRST_READ" if path.name in {"Q1_D08C2_RESULT_NOTE_v01.md", "Q1_D08C2_SPECIES_ELIGIBILITY_LEDGER_v01.csv", "D08C2_DELIVERY_INDEX_v01.md"} else "IMPORTANT" if rel.startswith(("02_outputs/", "03_qc/")) else "SUPPORTING"
        file_role = "delivery_index" if path.name == "D08C2_DELIVERY_INDEX_v01.md" else "result_note" if path.name == "Q1_D08C2_RESULT_NOTE_v01.md" else "audit_csv" if path.suffix == ".csv" else "qc_json" if path.suffix == ".json" else "source" if path.suffix == ".py" else "other"
        add(path, rel, file_role, "mirror", "YES" if priority in {"FIRST_READ", "IMPORTANT"} else "NO", priority, "Direct-readable UTF-8 package member.")
    transfer_path = ARC / "TRANSFER_MANIFEST_v01.csv"
    write_csv(transfer_path, transfer, ["local_path", "relative_path", "role", "upload_target", "required", "mainline_priority", "size_bytes", "sha256", "notes"])
    print(json.dumps({"status": post["validation_status"], "zip": str(ZIP), "zip_size_bytes": ZIP.stat().st_size, "zip_sha256": zip_hash, "transfer_rows": len(transfer)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
