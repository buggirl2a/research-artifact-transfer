#!/usr/bin/env python3
"""Freeze, package, and validate Range Gate 0 v01 without recomputation."""

from __future__ import annotations

import csv
import hashlib
import json
import shutil
import zipfile
from pathlib import Path


ROOT = Path(r"C:\range_paper")
WORK = ROOT / "99_tmp" / "range_gate0_v01"
WORK_OUT = WORK / "outputs"
WORK_QC = WORK / "qc"
RESULTS = ROOT / "07_results" / "range_gate0_v01"
FINAL_QC = ROOT / "05_qc" / "range_gate0_v01"
ARCHIVE = ROOT / "10_archive" / "range_gate0_v01"
PACKAGE_NAME = "Q1_RANGE_GATE0_WHOLE_RANGE_COMPLETENESS_COARSE_SCREEN_REPRODUCIBLE_v01"
STAGE = ARCHIVE / PACKAGE_NAME
ZIP_PATH = ARCHIVE / f"{PACKAGE_NAME}.zip"
SIDECAR = ARCHIVE / f"{PACKAGE_NAME}.zip.sha256"
POST = ARCHIVE / "RANGE_GATE0_POSTPACKAGE_VALIDATION_v01.json"

FROZEN_RESULTS = {
    "Q1_RANGE_GATE0_SPECIES_CLASSIFICATION_v01.csv": "243978406cb913c13898b333671000c30592079d076ef8b995822a1684f8a8cd",
    "Q1_RANGE_GATE0_SUMMARY_v01.csv": "c44eddbcd6fe0c884856786d1fa4ab036f6c1f01956177697bda5eb83d741c05",
    "Q1_RANGE_GATE0_DECISION_QUEUE_v01.csv": "f9c066bbf25de8dca122d90446aab579f22052ab9c0de4412be616c8567016c1",
    "Q1_RANGE_GATE0_FAIL_EXTRA_NA_v01.csv": "328ceb72d649e0788f2c019c5f6884ef0f318e1ba5059d8bf5de6cfadbd8eef5",
    "RANGE_GATE0_RESULT_NOTE_v01.md": "ef49b993bf8ac2579e8ab1b3d555a4c3486fdd9147c2df423b4bdf2bc4ed8f7e",
    "Q1_RANGE_GATE0_MAINLINE_AUDIT_v01.xlsx": "d0dd7e34e9b4bfffb412fa99e643fa0a12cd33d9061b8a75c7607665c733144e",
}


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def text_count(path: Path) -> tuple[str, object]:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            count = sum(1 for _ in csv.reader(f)) - 1
        return "data_rows", count
    if suffix in {".md", ".txt", ".py", ".mjs", ".json", ".ndjson"}:
        return "text_lines", len(path.read_text(encoding="utf-8").splitlines())
    return "not_applicable", ""


def purpose_for(relative: str) -> tuple[str, str]:
    name = Path(relative).name
    if name == "Q1_RANGE_GATE0_SPECIES_CLASSIFICATION_v01.csv": return "authoritative_output", "Complete 312-species Gate 0 classification"
    if name == "Q1_RANGE_GATE0_SUMMARY_v01.csv": return "authoritative_output", "Six-class frozen summary"
    if name == "Q1_RANGE_GATE0_DECISION_QUEUE_v01.csv": return "authoritative_output", "Frozen later-review routing queue; not an immediate review command"
    if name == "Q1_RANGE_GATE0_FAIL_EXTRA_NA_v01.csv": return "authoritative_output", "Complete Class 1 evidence ledger"
    if name == "RANGE_GATE0_RESULT_NOTE_v01.md": return "authoritative_output", "Concise mainline result note and scope boundary"
    if name.endswith("MAINLINE_AUDIT_v01.xlsx"): return "audit_workbook", "Human-readable multi-sheet audit workbook"
    if relative.startswith("controls/"): return "frozen_control", "Precommitted contract, input freeze, or scientific-output freeze"
    if relative.startswith("inputs/"): return "frozen_input", "Copied source-frozen request and D08B1 v02 authority"
    if relative.startswith("qc/"): return "qc", "Quality-control, independent verification, or workbook validation evidence"
    if relative.startswith("code/"): return "source", "Reproducible build, verification, workbook, and package source"
    return "other", "Supporting reproducibility artifact"


def deterministic_zip(source_dir: Path, zip_path: Path) -> None:
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for path in sorted(p for p in source_dir.rglob("*") if p.is_file()):
            arcname = (Path(PACKAGE_NAME) / path.relative_to(source_dir)).as_posix()
            info = zipfile.ZipInfo(arcname, date_time=(2026, 9, 3, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            zf.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def main() -> int:
    for target in [RESULTS, FINAL_QC, ARCHIVE]:
        if target.exists():
            raise RuntimeError(f"Refusing to overwrite existing final target: {target}")

    for name, expected in FROZEN_RESULTS.items():
        actual = sha(WORK_OUT / name)
        if actual != expected:
            raise RuntimeError(f"Frozen scientific output changed: {name}: {actual}")
    independent = json.loads((WORK_QC / "RANGE_GATE0_INDEPENDENT_AUDIT_v01.json").read_text(encoding="utf-8"))
    workbook = json.loads((WORK_QC / "RANGE_GATE0_WORKBOOK_VALIDATION_v01.json").read_text(encoding="utf-8"))
    if independent["status"] != "PASS" or workbook["status"] != "PASS":
        raise RuntimeError("Independent or workbook validation is not PASS")

    RESULTS.parent.mkdir(parents=True, exist_ok=True)
    FINAL_QC.parent.mkdir(parents=True, exist_ok=True)
    ARCHIVE.mkdir(parents=True)
    shutil.copytree(WORK_OUT, RESULTS, ignore=shutil.ignore_patterns("*.xlsx.inspect.ndjson"))
    shutil.copytree(WORK_QC, FINAL_QC)

    (STAGE / "outputs").mkdir(parents=True)
    (STAGE / "qc").mkdir()
    (STAGE / "controls").mkdir()
    (STAGE / "code").mkdir()
    shutil.copytree(ROOT / "03_doc" / "RANGE_GATE0_INPUTS_v01", STAGE / "inputs")
    for path in RESULTS.iterdir():
        if path.is_file(): shutil.copy2(path, STAGE / "outputs" / path.name)
    shutil.copytree(FINAL_QC, STAGE / "qc", dirs_exist_ok=True)
    for name in ["RANGE_GATE0_CONTRACT_v01.md", "RANGE_GATE0_INPUT_FREEZE_v01.md", "RANGE_GATE0_FREEZE_v01.md"]:
        shutil.copy2(ROOT / "00_control" / name, STAGE / "controls" / name)
    for name in [
        "parameters_range_gate0_v01.json", "build_range_gate0_v01.py",
        "verify_range_gate0_outputs_v01.py", "build_range_gate0_audit_workbook_v01.mjs",
        "verify_range_gate0_workbook_v01.py", "finalize_range_gate0_v01.py",
        "RANGE_GATE0_ENGINEERING_CORRECTION_LOG_v01.md",
    ]:
        shutil.copy2(ROOT / "06_src" / "range_gate0_v01" / name, STAGE / "code" / name)

    payload = sorted(p for p in STAGE.rglob("*") if p.is_file())
    manifest_rows = []
    for path in payload:
        rel = path.relative_to(STAGE).as_posix()
        role, purpose = purpose_for(rel)
        count_type, count = text_count(path)
        manifest_rows.append({
            "relative_path": rel, "role": role, "purpose": purpose,
            "count_type": count_type, "count": count,
            "size_bytes": path.stat().st_size, "sha256": sha(path),
            "authoritative": "YES" if role in {"authoritative_output", "frozen_control", "frozen_input"} else "NO",
        })
    content_manifest = STAGE / "CONTENT_MANIFEST_v01.csv"
    write_csv(content_manifest, manifest_rows, ["relative_path", "role", "purpose", "count_type", "count", "size_bytes", "sha256", "authoritative"])

    index_lines = [
        "# Range Gate 0 delivery index v01", "",
        "Read first: `outputs/RANGE_GATE0_RESULT_NOTE_v01.md`, `outputs/Q1_RANGE_GATE0_SUMMARY_v01.csv`, and `qc/RANGE_GATE0_INDEPENDENT_AUDIT_v01.json`.", "",
        "The authoritative scientific classification is `outputs/Q1_RANGE_GATE0_SPECIES_CLASSIFICATION_v01.csv`. The XLSX is an audit view; the UTF-8 CSV files are authoritative. `CONTENT_MANIFEST_v01.csv` enumerates the payload present before the index and checksum ledger were written.", "",
        "| Relative path | Role | Purpose | Count | Bytes | SHA-256 | Authoritative |", "|---|---|---|---:|---:|---|---|",
    ]
    for row in manifest_rows:
        count = f"{row['count']} {row['count_type']}" if row["count"] != "" else "—"
        index_lines.append(f"| `{row['relative_path']}` | {row['role']} | {row['purpose']} | {count} | {row['size_bytes']} | `{row['sha256']}` | {row['authoritative']} |")
    index_lines.extend(["", "STOP: this package does not authorize D08C2, Little fine processing, external range search, final cohort selection, or real Q1.", ""])
    delivery_index = STAGE / "RANGE_GATE0_DELIVERY_INDEX_v01.md"
    delivery_index.write_text("\n".join(index_lines), encoding="utf-8")

    ledger_files = sorted(p for p in STAGE.rglob("*") if p.is_file())
    ledger = STAGE / "SHA256SUMS.csv"
    write_csv(ledger, [{"relative_path": p.relative_to(STAGE).as_posix(), "bytes": p.stat().st_size, "sha256": sha(p)} for p in ledger_files], ["relative_path", "bytes", "sha256"])

    deterministic_zip(STAGE, ZIP_PATH)
    zip_hash = sha(ZIP_PATH)
    SIDECAR.write_text(f"{zip_hash}  {ZIP_PATH.name}\n", encoding="utf-8")

    validation_checks = []
    def add(check, passed, actual, expected):
        validation_checks.append({"check": check, "status": "PASS" if passed else "FAIL", "actual": actual, "expected": expected})
    with zipfile.ZipFile(ZIP_PATH, "r") as zf:
        bad = zf.testzip()
        zip_names = zf.namelist()
        add("zip_integrity", bad is None, bad, None)
        add("zip_member_count", len(zip_names) == len([p for p in STAGE.rglob("*") if p.is_file()]), len(zip_names), len([p for p in STAGE.rglob("*") if p.is_file()]))
    ledger_rows = list(csv.DictReader(ledger.open("r", encoding="utf-8-sig", newline="")))
    ledger_bad = [r["relative_path"] for r in ledger_rows if sha(STAGE / r["relative_path"]) != r["sha256"] or (STAGE / r["relative_path"]).stat().st_size != int(r["bytes"])]
    add("stage_checksum_ledger", not ledger_bad, ledger_bad, [])
    add("sidecar_matches_zip", SIDECAR.read_text(encoding="utf-8").split()[0] == zip_hash, SIDECAR.read_text(encoding="utf-8").split()[0], zip_hash)
    result_copy_bad = [name for name, expected in FROZEN_RESULTS.items() if sha(RESULTS / name) != expected or sha(STAGE / "outputs" / name) != expected]
    add("frozen_results_copied_byte_for_byte", not result_copy_bad, result_copy_bad, [])
    authority_zip = STAGE / "inputs" / "Q1_TAXON_RANGE_D08B1_CORRECTED_REPRODUCIBLE_v02.zip"
    add("frozen_D08B1_zip_retained", sha(authority_zip) == "3647c35189110d524d5f6cd64bf2d4aabaaa80828e58f42e767bb5e862188a3e", sha(authority_zip), "3647c35189110d524d5f6cd64bf2d4aabaaa80828e58f42e767bb5e862188a3e")
    add("independent_output_audit_PASS", independent["status"] == "PASS", independent["status"], "PASS")
    add("workbook_validation_PASS", workbook["status"] == "PASS", workbook["status"], "PASS")
    status = "PASS" if all(c["status"] == "PASS" for c in validation_checks) else "FAIL"
    post = {
        "status": status, "package_name": PACKAGE_NAME,
        "package_directory": str(STAGE), "zip_path": str(ZIP_PATH),
        "zip_size_bytes": ZIP_PATH.stat().st_size, "zip_sha256": zip_hash,
        "sidecar_path": str(SIDECAR), "validation_check_count": len(validation_checks),
        "validation_pass_count": sum(c["status"] == "PASS" for c in validation_checks),
        "checks": validation_checks,
    }
    POST.write_text(json.dumps(post, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    shutil.copy2(delivery_index, ARCHIVE / "RANGE_GATE0_DELIVERY_INDEX_v01.md")
    if status != "PASS":
        raise RuntimeError("ENGINEERING_FAIL: postpackage validation failed")
    print(json.dumps({"status": status, "zip": str(ZIP_PATH), "bytes": ZIP_PATH.stat().st_size, "sha256": zip_hash, "stage_files": len(zip_names), "validation": f"{post['validation_pass_count']}/{post['validation_check_count']}"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
