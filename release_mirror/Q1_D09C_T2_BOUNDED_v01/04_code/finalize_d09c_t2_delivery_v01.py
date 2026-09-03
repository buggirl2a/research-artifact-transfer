from __future__ import annotations

import csv
import hashlib
import json
import shutil
import tempfile
import zipfile
from pathlib import Path


ROOT = Path(r"C:\range_paper")
OUT = ROOT / "04_derived" / "d09c_t2_completion_v01"
QC = ROOT / "05_qc" / "d09c_t2_completion_v01"
SRC = ROOT / "06_src" / "d09c_t2_completion_v01"
ARCHIVE = ROOT / "10_archive" / "d09c_t2_completion_v01"
PACKAGE_NAME = "Q1_D09C_T2_BOUNDED_COMPLETION_REPRODUCIBLE_v01"
PACKAGE = ARCHIVE / PACKAGE_NAME
ZIP = ARCHIVE / f"{PACKAGE_NAME}.zip"
RAW = ROOT / "02_raw" / "fia_t2_2023_raw_design_v01"
OLD = ROOT / "04_derived" / "d09c_v01"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def data_rows(path: Path) -> int | str:
    if path.suffix.lower() == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            return max(sum(1 for _ in csv.reader(f)) - 1, 0)
    return ""


def copy_file(src: Path, rel: str):
    dst = PACKAGE / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def build_zip(source: Path, target: Path):
    files = sorted(p for p in source.rglob("*") if p.is_file())
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for path in files:
            rel = path.relative_to(source.parent).as_posix()
            info = zipfile.ZipInfo(rel, date_time=(2026, 9, 3, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            zf.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def main():
    ARCHIVE.mkdir(parents=True, exist_ok=True)
    if any(ARCHIVE.iterdir()):
        raise RuntimeError(f"Refusing to overwrite nonempty archive: {ARCHIVE}")
    PACKAGE.mkdir()

    copy_file(ROOT / "00_control" / "Q1_D09C_T2_BOUNDED_COMPLETION_CONTRACT_v01.md", "00_control/Q1_D09C_T2_BOUNDED_COMPLETION_CONTRACT_v01.md")
    copy_file(ROOT / "00_control" / "D09C_T2_COMPLETION_EXECUTION_FREEZE_v01.md", "00_control/D09C_T2_COMPLETION_EXECUTION_FREEZE_v01.md")
    copy_file(ROOT / "00_control" / "D09C_FREEZE_v01.md", "00_control/D09C_FREEZE_v01.md")

    old_files = [
        "D09C_TEMPORAL_FRAME_AUDIT_v01.csv",
        "D09C_EVALID_COMPONENT_LEDGER_v01.csv",
        "D09C_PANEL_SUBPANEL_YEAR_LEDGER_v01.csv",
        "D09C_LINEAGE_CROSSFOLD_AUDIT_v01.csv",
    ]
    for name in old_files:
        copy_file(OLD / name, f"01_authoritative_inputs/frozen_d09c_v01/{name}")
    for path in sorted((RAW / "raw_table_zips").glob("*.zip")):
        copy_file(path, f"01_authoritative_inputs/ca_or_wa_raw_design_zips/{path.name}")
    for name in ("RAW_ASSET_MANIFEST_v01.csv", "DOWNLOAD_FREEZE_QC_v01.csv", "SHA256SUMS.csv"):
        copy_file(RAW / "manifests" / name, f"01_authoritative_inputs/ca_or_wa_raw_design_manifests/{name}")

    for path in sorted(OUT.iterdir()):
        if path.is_file():
            copy_file(path, f"02_outputs/{path.name}")
    for path in sorted(QC.iterdir()):
        if path.is_file():
            copy_file(path, f"03_qc/{path.name}")
    for path in sorted(SRC.iterdir()):
        if path.is_file() and path.suffix.lower() in {".py", ".json"}:
            copy_file(path, f"04_code/{path.name}")

    package_files = sorted(p for p in PACKAGE.rglob("*") if p.is_file())
    index_lines = [
        "# D09C T2 bounded completion delivery index v01",
        "",
        "Date: 2026-09-03  ",
        "Nationwide status: **DESIGN_BLOCKED** (WV estimation unit 3 is unsampled in one fold for every legal 2-vs-3 whole-panel partition).",
        "",
        "This package is a bounded sampling-design audit. It contains no TREE, species outcome, abundance, detection, occupancy, D08C2, range, or real-Q1 result.",
        "",
        "| Relative path | Role | Rows | Bytes | SHA-256 | Authoritative |",
        "|---|---|---:|---:|---|---|",
    ]
    for path in package_files:
        rel = path.relative_to(PACKAGE).as_posix()
        if rel.startswith("00_control/"):
            role, authoritative = "frozen control", "YES"
        elif rel.startswith("01_authoritative_inputs/"):
            role, authoritative = "frozen input", "YES"
        elif rel.startswith("02_outputs/"):
            role, authoritative = "scientific audit output", "YES"
        elif rel.startswith("03_qc/"):
            role, authoritative = "quality control", "YES"
        else:
            role, authoritative = "reproducibility code", "YES"
        index_lines.append(f"| `{rel}` | {role} | {data_rows(path)} | {path.stat().st_size} | `{sha256(path)}` | {authoritative} |")
    index_path = PACKAGE / "D09C_T2_DELIVERY_INDEX_v01.md"
    index_path.write_text("\n".join(index_lines) + "\n", encoding="utf-8")

    sum_rows = []
    for path in sorted(p for p in PACKAGE.rglob("*") if p.is_file()):
        if path.name == "SHA256SUMS.csv":
            continue
        sum_rows.append({"relative_path": path.relative_to(PACKAGE).as_posix(), "size_bytes": path.stat().st_size, "sha256": sha256(path)})
    sums_path = PACKAGE / "SHA256SUMS.csv"
    with sums_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["relative_path", "size_bytes", "sha256"], lineterminator="\n")
        w.writeheader()
        w.writerows(sum_rows)
    shutil.copy2(sums_path, ARCHIVE / "SHA256SUMS.csv")
    shutil.copy2(index_path, ARCHIVE / "D09C_T2_DELIVERY_INDEX_v01.md")

    build_zip(PACKAGE, ZIP)
    with tempfile.TemporaryDirectory(dir=ROOT / "99_tmp") as td:
        second = Path(td) / "rebuild.zip"
        build_zip(PACKAGE, second)
        reproducible = sha256(second) == sha256(ZIP) and second.stat().st_size == ZIP.stat().st_size
    zip_hash = sha256(ZIP)
    sidecar = ZIP.with_suffix(ZIP.suffix + ".sha256")
    sidecar.write_text(f"{zip_hash}  {ZIP.name}\n", encoding="utf-8")

    with zipfile.ZipFile(ZIP) as zf:
        names = set(zf.namelist())
        expected_prefix = PACKAGE_NAME + "/"
        member_checks = []
        for row in sum_rows:
            member = expected_prefix + row["relative_path"]
            member_checks.append(member in names and hashlib.sha256(zf.read(member)).hexdigest() == row["sha256"])
        sums_member = expected_prefix + "SHA256SUMS.csv"
        sums_ok = sums_member in names and hashlib.sha256(zf.read(sums_member)).hexdigest() == sha256(sums_path)

    validation = {
        "validation_id": "D09C_T2_POSTPACKAGE_VALIDATION_v01",
        "date": "2026-09-03",
        "status": "PASS" if reproducible and all(member_checks) and sums_ok else "FAIL",
        "nationwide_scientific_status": "DESIGN_BLOCKED",
        "zip_path": str(ZIP),
        "zip_size_bytes": ZIP.stat().st_size,
        "zip_sha256": zip_hash,
        "deterministic_rebuild_identical": reproducible,
        "manifested_member_count": len(sum_rows),
        "manifested_members_verified": sum(member_checks),
        "sha256sums_member_verified": sums_ok,
        "species_or_outcome_data_in_package": False,
    }
    validation_path = ARCHIVE / "D09C_T2_POSTPACKAGE_VALIDATION_v01.json"
    validation_path.write_text(json.dumps(validation, indent=2) + "\n", encoding="utf-8")

    transfer_rows = []
    def add_transfer(path: Path, relative_path: str, role: str, target: str, required: str, priority: str, notes: str):
        transfer_rows.append({
            "local_path": str(path),
            "relative_path": relative_path,
            "role": role,
            "upload_target": target,
            "required": required,
            "mainline_priority": priority,
            "size_bytes": path.stat().st_size,
            "sha256": sha256(path),
            "notes": notes,
        })
    add_transfer(ZIP, f"release_assets/{ZIP.name}", "reproducible_zip", "release", "YES", "IMPORTANT", "Complete immutable reproducible package; scientific status DESIGN_BLOCKED.")
    add_transfer(sidecar, f"release_assets/{sidecar.name}", "checksum", "both", "YES", "IMPORTANT", "ZIP SHA-256 sidecar.")
    add_transfer(index_path, "D09C_T2_DELIVERY_INDEX_v01.md", "delivery_index", "mirror", "YES", "FIRST_READ", "Package file index with hashes.")
    add_transfer(validation_path, validation_path.name, "qc_json", "mirror", "YES", "FIRST_READ", "Postpackage reproducibility and member-hash validation.")
    add_transfer(ARCHIVE / "SHA256SUMS.csv", "SHA256SUMS.csv", "checksum", "mirror", "YES", "IMPORTANT", "Package member hashes.")
    for path in sorted((PACKAGE / "02_outputs").iterdir()):
        role = "result_note" if path.suffix.lower() == ".md" else "audit_csv"
        priority = "FIRST_READ" if path.name in {"Q1_D09C_T2_RESULT_NOTE_v01.md", "Q1_D09C_T2_NATIONAL_FRAME_COMPLETION_v01.csv", "Q1_D09C_T2_WV_AUDIT_v01.csv"} else "IMPORTANT"
        add_transfer(path, f"02_outputs/{path.name}", role, "mirror", "YES", priority, "Direct-readable frozen D09C T2 completion output.")
    for path in sorted((PACKAGE / "03_qc").iterdir()):
        add_transfer(path, f"03_qc/{path.name}", "qc_json" if path.suffix.lower() == ".json" else "other", "mirror", "YES", "SUPPORTING", "Direct-readable QC or execution record.")
    for path in sorted((PACKAGE / "04_code").iterdir()):
        add_transfer(path, f"04_code/{path.name}", "source", "mirror", "YES", "SUPPORTING", "Reproduction/verification source or frozen parameters.")
    for path in sorted((PACKAGE / "00_control").iterdir()):
        add_transfer(path, f"00_control/{path.name}", "manifest", "mirror", "YES", "IMPORTANT", "Frozen contract/control.")
    for path in sorted((PACKAGE / "01_authoritative_inputs").rglob("*")):
        if path.is_file():
            add_transfer(path, f"01_authoritative_inputs/{path.relative_to(PACKAGE / '01_authoritative_inputs').as_posix()}", "other", "local_only", "NO", "ARCHIVE_ONLY", "Embedded in reproducible ZIP; not recommended for direct mirror.")

    manifest_path = ARCHIVE / "TRANSFER_MANIFEST_v01.csv"
    with manifest_path.open("w", encoding="utf-8", newline="") as f:
        fields = ["local_path", "relative_path", "role", "upload_target", "required", "mainline_priority", "size_bytes", "sha256", "notes"]
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        w.writerows(transfer_rows)

    if validation["status"] != "PASS":
        raise RuntimeError("Postpackage validation failed")
    print(json.dumps({
        "status": "PASS",
        "scientific_status": "DESIGN_BLOCKED",
        "zip": str(ZIP),
        "zip_size_bytes": ZIP.stat().st_size,
        "zip_sha256": zip_hash,
        "transfer_manifest_rows": len(transfer_rows),
    }))


if __name__ == "__main__":
    main()
