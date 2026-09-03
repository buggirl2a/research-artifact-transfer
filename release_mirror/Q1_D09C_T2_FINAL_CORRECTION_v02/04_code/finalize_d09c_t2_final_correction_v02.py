from __future__ import annotations

import csv
import hashlib
import json
import shutil
import tempfile
import zipfile
from pathlib import Path


ROOT = Path(r"C:\range_paper")
OUT = ROOT / "04_derived" / "d09c_t2_final_correction_v02"
QC = ROOT / "05_qc" / "d09c_t2_final_correction_v02"
SRC = ROOT / "06_src" / "d09c_t2_final_correction_v02"
ARCHIVE = ROOT / "10_archive" / "d09c_t2_final_correction_v02"
PACKAGE_NAME = "Q1_D09C_T2_FINAL_CORRECTION_REPRODUCIBLE_v02"
PACKAGE = ARCHIVE / PACKAGE_NAME
ZIP = ARCHIVE / f"{PACKAGE_NAME}.zip"
V1_ARCHIVE = ROOT / "10_archive" / "d09c_t2_completion_v01"
V1_ZIP = V1_ARCHIVE / "Q1_D09C_T2_BOUNDED_COMPLETION_REPRODUCIBLE_v01.zip"
V1_SIDECAR = V1_ARCHIVE / "Q1_D09C_T2_BOUNDED_COMPLETION_REPRODUCIBLE_v01.zip.sha256"


def sha256(path: Path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def row_count(path: Path):
    if path.suffix.lower() != ".csv":
        return ""
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return max(sum(1 for _ in csv.reader(f)) - 1, 0)


def copy_file(src: Path, rel: str):
    dst = PACKAGE / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def build_zip(source: Path, target: Path):
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for path in sorted(p for p in source.rglob("*") if p.is_file()):
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

    for name in (
        "Q1_D09C_T2_FINAL_DESIGN_CORRECTION_CONTRACT_v02.md",
        "D09C_T2_FINAL_CORRECTION_EXECUTION_FREEZE_v02.md",
        "D09C_T2_COMPLETION_EXECUTION_FREEZE_v01.md",
    ):
        copy_file(ROOT / "00_control" / name, f"00_control/{name}")
    copy_file(V1_ZIP, f"01_authoritative_inputs/predecessor_v01/{V1_ZIP.name}")
    copy_file(V1_SIDECAR, f"01_authoritative_inputs/predecessor_v01/{V1_SIDECAR.name}")

    for path in sorted(OUT.iterdir()):
        if path.is_file():
            copy_file(path, f"02_outputs/{path.name}")
    for path in sorted(QC.iterdir()):
        if path.is_file():
            copy_file(path, f"03_qc/{path.name}")
    for path in sorted(SRC.iterdir()):
        if path.is_file() and path.suffix.lower() in {".py", ".json"}:
            copy_file(path, f"04_code/{path.name}")
    copy_file(ROOT / "06_src" / "d09c_t2_completion_v01" / "build_d09c_t2_completion_v01.py", "04_code/predecessor_v01_build_d09c_t2_completion_v01.py")

    files = sorted(p for p in PACKAGE.rglob("*") if p.is_file())
    index = [
        "# D09C T2 final correction delivery index v02", "", "Date: 2026-09-03  ",
        "Nationwide status: **PASS_READY_FOR_MAINLINE_FINAL_D09C_AUDIT**", "",
        "The predecessor v01 ZIP is embedded unchanged. V02 applies the frozen repair-class hierarchy and the pre-partition WV sparse-EU fallback only. No species or outcome data are present.", "",
        "| Relative path | Role | Rows | Bytes | SHA-256 | Authoritative |", "|---|---|---:|---:|---|---|",
    ]
    for path in files:
        rel = path.relative_to(PACKAGE).as_posix()
        role = "control" if rel.startswith("00_control/") else ("authoritative predecessor" if rel.startswith("01_authoritative_inputs/") else ("audit output" if rel.startswith("02_outputs/") else ("quality control" if rel.startswith("03_qc/") else "reproducibility code")))
        index.append(f"| `{rel}` | {role} | {row_count(path)} | {path.stat().st_size} | `{sha256(path)}` | YES |")
    index_path = PACKAGE / "D09C_T2_FINAL_DELIVERY_INDEX_v02.md"
    index_path.write_text("\n".join(index) + "\n", encoding="utf-8")

    sums = []
    for path in sorted(p for p in PACKAGE.rglob("*") if p.is_file()):
        if path.name == "SHA256SUMS.csv":
            continue
        sums.append({"relative_path": path.relative_to(PACKAGE).as_posix(), "size_bytes": path.stat().st_size, "sha256": sha256(path)})
    sums_path = PACKAGE / "SHA256SUMS.csv"
    with sums_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["relative_path", "size_bytes", "sha256"], lineterminator="\n")
        w.writeheader(); w.writerows(sums)
    shutil.copy2(sums_path, ARCHIVE / "SHA256SUMS.csv")
    shutil.copy2(index_path, ARCHIVE / "D09C_T2_FINAL_DELIVERY_INDEX_v02.md")

    build_zip(PACKAGE, ZIP)
    with tempfile.TemporaryDirectory(dir=ROOT / "99_tmp") as td:
        second = Path(td) / "second.zip"
        build_zip(PACKAGE, second)
        deterministic = sha256(second) == sha256(ZIP) and second.stat().st_size == ZIP.stat().st_size
    zip_hash = sha256(ZIP)
    sidecar = ZIP.with_suffix(ZIP.suffix + ".sha256")
    sidecar.write_text(f"{zip_hash}  {ZIP.name}\n", encoding="utf-8")

    with zipfile.ZipFile(ZIP) as zf:
        prefix = PACKAGE_NAME + "/"
        names = set(zf.namelist())
        checks = [prefix + r["relative_path"] in names and hashlib.sha256(zf.read(prefix + r["relative_path"])).hexdigest() == r["sha256"] for r in sums]
        sums_ok = prefix + "SHA256SUMS.csv" in names and hashlib.sha256(zf.read(prefix + "SHA256SUMS.csv")).hexdigest() == sha256(sums_path)
    validation = {
        "validation_id": "D09C_T2_FINAL_POSTPACKAGE_VALIDATION_v02", "date": "2026-09-03",
        "status": "PASS" if deterministic and all(checks) and sums_ok else "FAIL",
        "nationwide_status": "PASS_READY_FOR_MAINLINE_FINAL_D09C_AUDIT",
        "zip_path": str(ZIP), "zip_size_bytes": ZIP.stat().st_size, "zip_sha256": zip_hash,
        "deterministic_rebuild_identical": deterministic, "manifested_member_count": len(sums),
        "manifested_members_verified": sum(checks), "sha256sums_member_verified": sums_ok,
        "predecessor_v01_embedded_sha256": sha256(PACKAGE / "01_authoritative_inputs" / "predecessor_v01" / V1_ZIP.name),
        "species_or_outcome_data_in_package": False,
    }
    validation_path = ARCHIVE / "D09C_T2_FINAL_POSTPACKAGE_VALIDATION_v02.json"
    validation_path.write_text(json.dumps(validation, indent=2) + "\n", encoding="utf-8")

    transfer = []
    def add(path, rel, role, target, required, priority, notes):
        transfer.append({
            "local_path": str(path), "relative_path": rel, "role": role, "upload_target": target,
            "required": required, "mainline_priority": priority, "size_bytes": path.stat().st_size,
            "sha256": sha256(path), "notes": notes,
        })
    add(ZIP, f"release_assets/{ZIP.name}", "reproducible_zip", "release", "YES", "IMPORTANT", "Complete immutable v02 correction package with embedded accepted predecessor.")
    add(sidecar, f"release_assets/{sidecar.name}", "checksum", "both", "YES", "IMPORTANT", "V02 ZIP SHA-256 sidecar.")
    add(index_path, index_path.name, "delivery_index", "mirror", "YES", "FIRST_READ", "File roles, rows, sizes, and hashes.")
    add(validation_path, validation_path.name, "qc_json", "mirror", "YES", "FIRST_READ", "Postpackage deterministic rebuild and member validation.")
    add(ARCHIVE / "SHA256SUMS.csv", "SHA256SUMS.csv", "checksum", "mirror", "YES", "IMPORTANT", "Package member hashes.")
    for path in sorted((PACKAGE / "02_outputs").iterdir()):
        role = "result_note" if path.suffix.lower() == ".md" else "audit_csv"
        priority = "FIRST_READ" if path.name in {"Q1_D09C_T2_FINAL_RESULT_NOTE_v02.md", "Q1_D09C_T2_FINAL_RULE_SELECTED_PARTITIONS_v02.csv", "Q1_D09C_T2_WV_MERGE_PARTNER_CANDIDATES_v02.csv", "Q1_D09C_T2_CA_OR_WA_RERANK_AUDIT_v02.csv"} else "IMPORTANT"
        add(path, f"02_outputs/{path.name}", role, "mirror", "YES", priority, "Direct-readable frozen v02 output.")
    for path in sorted((PACKAGE / "03_qc").iterdir()):
        add(path, f"03_qc/{path.name}", "qc_json" if path.suffix.lower() == ".json" else "other", "mirror", "YES", "SUPPORTING", "Direct-readable v02 QC record.")
    for path in sorted((PACKAGE / "04_code").iterdir()):
        add(path, f"04_code/{path.name}", "source", "mirror", "YES", "SUPPORTING", "Reproduction/verification source or parameters.")
    for path in sorted((PACKAGE / "00_control").iterdir()):
        add(path, f"00_control/{path.name}", "manifest", "mirror", "YES", "IMPORTANT", "Frozen contract/control.")
    for path in sorted((PACKAGE / "01_authoritative_inputs").rglob("*")):
        if path.is_file():
            add(path, f"01_authoritative_inputs/{path.relative_to(PACKAGE / '01_authoritative_inputs').as_posix()}", "other", "local_only", "NO", "ARCHIVE_ONLY", "Embedded in v02 ZIP; predecessor binary need not be mirrored.")
    manifest = ARCHIVE / "TRANSFER_MANIFEST_v01.csv"
    with manifest.open("w", encoding="utf-8", newline="") as f:
        fields = ["local_path", "relative_path", "role", "upload_target", "required", "mainline_priority", "size_bytes", "sha256", "notes"]
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n"); w.writeheader(); w.writerows(transfer)

    if validation["status"] != "PASS":
        raise RuntimeError("Postpackage validation failed")
    print(json.dumps({"status": "PASS", "nationwide_status": validation["nationwide_status"], "zip": str(ZIP), "zip_size_bytes": ZIP.stat().st_size, "zip_sha256": zip_hash, "transfer_manifest_rows": len(transfer)}))


if __name__ == "__main__":
    main()
