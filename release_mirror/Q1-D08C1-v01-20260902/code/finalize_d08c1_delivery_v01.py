#!/usr/bin/env python3
"""Finalize the frozen D08C1 delivery without rerunning analytical computation."""

from __future__ import annotations

import csv
import hashlib
import json
import shutil
import sys
import zipfile
from pathlib import Path


ROOT = Path(r"C:\range_paper")
WORK = ROOT / "99_tmp" / "d08c1_v01"
WORK_OUTPUTS = WORK / "outputs"
WORK_QC = WORK / "qc"
FINAL_OUTPUTS = ROOT / "04_derived" / "d08c1_v01"
FINAL_QC = ROOT / "05_qc" / "d08c1_v01"
ARCHIVE = ROOT / "10_archive" / "d08c1_v01"
STAGE_PARENT = ROOT / "99_tmp" / "d08c1_v01_release_stage"
BASE = "Q1_D08C1_FIA_ACCEPTED_SPECIES_ELIGIBILITY_REPRODUCIBLE_v01"
STAGE_ROOT = STAGE_PARENT / BASE
ZIP_PATH = ARCHIVE / f"{BASE}.zip"
FIXED_ZIP_TIME = (2026, 9, 2, 12, 0, 0)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def csv_rows(path: Path) -> int:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return max(sum(1 for _ in csv.reader(handle)) - 1, 0)


def text_lines(path: Path) -> int:
    with path.open("r", encoding="utf-8-sig", errors="strict") as handle:
        return sum(1 for _ in handle)


def load_json(path: Path):
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def dump_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def copy_file(source: Path, target: Path) -> None:
    require(source.is_file(), f"Missing required file: {source}")
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    require(sha256(source) == sha256(target), f"Copy hash mismatch: {source} -> {target}")


def copy_tree_exact(source: Path, target: Path) -> None:
    require(source.is_dir(), f"Missing required directory: {source}")
    require(not target.exists(), f"Refusing to overwrite directory: {target}")
    shutil.copytree(source, target)
    source_files = {p.relative_to(source).as_posix(): sha256(p) for p in source.rglob("*") if p.is_file()}
    target_files = {p.relative_to(target).as_posix(): sha256(p) for p in target.rglob("*") if p.is_file()}
    require(source_files == target_files, f"Directory copy verification failed: {source} -> {target}")


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def final_prepackage_audit() -> dict:
    required_rows = {
        "Q1_D08C1_SPECIES_GRAIN_CENSUS_v01.csv": 6498,
        "Q1_D08C1_GRAIN_SUMMARY_v01.csv": 6,
        "Q1_D08C1_50KM_FRONTIERS_v01.csv": 30,
        "Q1_D08C1_AB_SPLIT_AUDIT_v01.csv": 240,
        "Q1_D08C1_DOMAIN_GRID_AUDIT_v01.csv": 3,
        "Q1_D08C1_NATIVE_STATE_AUDIT_v01.csv": 17328,
        "Q1_D08C1_CODE_AGGREGATION_AUDIT_v01.csv": 377,
        "Q1_D08C1_NONANALYSIS_CODE_AUDIT_v01.csv": 19,
        "Q1_D08C1_LITTLE_REVIEW_SURVIVOR_QUEUE_v01.csv": 231,
        "Q1_D08C1_STATE_CROSSWALK_AUDIT_v01.csv": 48,
        "Q1_D08C1_TRACEABILITY_SAMPLE_v01.csv": 204,
        "Q1_D08C1_QC_v01.csv": 23,
    }
    checks = []
    for name, expected in required_rows.items():
        path = WORK_OUTPUTS / name
        observed = csv_rows(path) if path.is_file() else None
        checks.append({"check": f"row_count::{name}", "status": "PASS" if observed == expected else "FAIL", "observed": observed, "expected": expected})

    workbook = WORK_OUTPUTS / "Q1_D08C1_MAINLINE_AUDIT_v01.xlsx"
    workbook_ok = False
    if workbook.is_file():
        with zipfile.ZipFile(workbook, "r") as archive:
            workbook_ok = archive.testzip() is None
    checks.append({"check": "workbook_zip_integrity", "status": "PASS" if workbook_ok else "FAIL", "observed": workbook_ok, "expected": True})
    workbook_hash = sha256(workbook) if workbook.is_file() else None
    checks.append({"check": "frozen_workbook_sha256", "status": "PASS" if workbook_hash == "dd36759aba79b5f8d641c80dc658506deb80581c694bcfa45a2176c7c3ccf454" else "FAIL", "observed": workbook_hash, "expected": "dd36759aba79b5f8d641c80dc658506deb80581c694bcfa45a2176c7c3ccf454"})

    build = load_json(WORK_QC / "D08C1_BUILD_SUMMARY_v01.json")
    independent = load_json(WORK_QC / "D08C1_INDEPENDENT_AUDIT_v01.json")
    no_q1 = load_json(WORK_QC / "D08C1_NO_Q1_OUTCOME_AUDIT_v01.json")
    checks.extend([
        {"check": "build_status", "status": "PASS" if build.get("status") == "PASS" else "FAIL", "observed": build.get("status"), "expected": "PASS"},
        {"check": "independent_audit_19_of_19", "status": "PASS" if independent.get("status") == "PASS" and independent.get("check_count") == 19 and all(c.get("status") == "PASS" for c in independent.get("checks", [])) else "FAIL", "observed": {"status": independent.get("status"), "check_count": independent.get("check_count")}, "expected": {"status": "PASS", "check_count": 19}},
        {"check": "no_Q1_audit", "status": "PASS" if no_q1.get("status") == "PASS" and not no_q1.get("prohibited_operations_performed") else "FAIL", "observed": {"status": no_q1.get("status"), "prohibited_operations_performed": no_q1.get("prohibited_operations_performed")}, "expected": {"status": "PASS", "prohibited_operations_performed": []}},
    ])

    formula_scan = (WORK_QC / "D08C1_WORKBOOK_FORMULA_ERROR_SCAN_v01.ndjson").read_text(encoding="utf-8-sig")
    checks.append({"check": "workbook_formula_error_scan_zero", "status": "PASS" if "matched 0 entries" in formula_scan else "FAIL", "observed": "matched 0 entries" in formula_scan, "expected": True})
    preview_count = len(list((WORK_QC / "WORKBOOK_PREVIEWS_v01").glob("*.png")))
    checks.append({"check": "workbook_preview_count", "status": "PASS" if preview_count == 15 else "FAIL", "observed": preview_count, "expected": 15})

    params = load_json(ROOT / "06_src" / "d08c1_v01" / "parameters_d08c1_v01.json")
    authority_dir = ROOT / "04_derived" / "tax_v02"
    for name, expected_hash in params["d08b1_authority_hashes"].items():
        observed_hash = sha256(authority_dir / name)
        checks.append({"check": f"D08B1_authority_sha256::{name}", "status": "PASS" if observed_hash == expected_hash else "FAIL", "observed": observed_hash, "expected": expected_hash})

    alias_hash = sha256(ROOT / "00_control" / "D08C1_STATE_ALIAS_FREEZE_v01.csv")
    checks.append({"check": "state_alias_freeze_sha256", "status": "PASS" if alias_hash == "d450e7b9b635c34db7e60ec0964a7f4ca3f24e4e7e58f8f1725691bcff3f7dda" else "FAIL", "observed": alias_hash, "expected": "d450e7b9b635c34db7e60ec0964a7f4ca3f24e4e7e58f8f1725691bcff3f7dda"})

    status = "PASS" if all(c["status"] == "PASS" for c in checks) else "FAIL"
    report = {
        "audit_id": "D08C1_FINAL_PREPACKAGE_AUDIT_v01",
        "date": "2026-09-02",
        "mode": "read-only validation of frozen analytical outputs; no analysis rerun",
        "status": status,
        "check_count": len(checks),
        "checks": checks,
    }
    require(status == "PASS", "Final prepackage audit failed")
    return report


def package_inputs() -> list[tuple[Path, Path]]:
    return [
        (ROOT / "03_doc" / "D08C1_FIA_ELIGIBILITY_INPUTS_v01" / "Q1_WORK_REQUEST_D08C1_FIA_ACCEPTED_SPECIES_ELIGIBILITY_v01_20260902.md", STAGE_ROOT / "inputs" / "request_decision" / "Q1_WORK_REQUEST_D08C1_FIA_ACCEPTED_SPECIES_ELIGIBILITY_v01_20260902.md"),
        (ROOT / "03_doc" / "D08C1_FIA_ELIGIBILITY_INPUTS_v01" / "Q1_D08C1_MAINLINE_DECISION_RHODE_ISLAND_ALIAS_v01_20260902.md", STAGE_ROOT / "inputs" / "request_decision" / "Q1_D08C1_MAINLINE_DECISION_RHODE_ISLAND_ALIAS_v01_20260902.md"),
        (ROOT / "04_derived" / "tax_v02" / "Q1_FIA_CODE_TO_ANALYSIS_SPECIES_v02.csv", STAGE_ROOT / "inputs" / "d08b1_v02_authority" / "Q1_FIA_CODE_TO_ANALYSIS_SPECIES_v02.csv"),
        (ROOT / "04_derived" / "tax_v02" / "Q1_ANALYSIS_SPECIES_MASTER_v02.csv", STAGE_ROOT / "inputs" / "d08b1_v02_authority" / "Q1_ANALYSIS_SPECIES_MASTER_v02.csv"),
        (ROOT / "04_derived" / "tax_v02" / "Q1_GLOBAL_RANGE_FLAGS_v02.csv", STAGE_ROOT / "inputs" / "d08b1_v02_authority" / "Q1_GLOBAL_RANGE_FLAGS_v02.csv"),
        (ROOT / "04_derived" / "tax_v02" / "Q1_WCVP_NATIVE_DISTRIBUTION_LONG_v02.csv", STAGE_ROOT / "inputs" / "d08b1_v02_authority" / "Q1_WCVP_NATIVE_DISTRIBUTION_LONG_v02.csv"),
        (ROOT / "04_derived" / "tax_v02" / "Q1_DRC_PROTOCOL_v02.csv", STAGE_ROOT / "inputs" / "d08b1_v02_authority" / "Q1_DRC_PROTOCOL_v02.csv"),
        (ROOT / "06_src" / "elig_v02" / "D04_extract_FIA_pilot.py", STAGE_ROOT / "inputs" / "d04_eligibility_continuity" / "D04_extract_FIA_pilot.py"),
        (ROOT / "06_src" / "elig_v02" / "parameters.json", STAGE_ROOT / "inputs" / "d04_eligibility_continuity" / "elig_v02_parameters.json"),
        (ROOT / "05_qc" / "elig_v02" / "D04_CONTINUITY_AUDIT.csv", STAGE_ROOT / "inputs" / "d04_eligibility_continuity" / "D04_CONTINUITY_AUDIT.csv"),
        (ROOT / "05_qc" / "elig_v02" / "LINEAGE_AUDIT.csv", STAGE_ROOT / "inputs" / "d04_eligibility_continuity" / "LINEAGE_AUDIT.csv"),
        (ROOT / "05_qc" / "elig_v02" / "AB_SPLIT_AUDIT.csv", STAGE_ROOT / "inputs" / "d04_eligibility_continuity" / "AB_SPLIT_AUDIT.csv"),
        (ROOT / "05_qc" / "elig_v02" / "DOMAIN_GRID_AUDIT.csv", STAGE_ROOT / "inputs" / "d04_eligibility_continuity" / "DOMAIN_GRID_AUDIT.csv"),
    ]


def row_or_line_count(path: Path):
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return csv_rows(path), "data_rows"
    if suffix in {".md", ".txt", ".json", ".ndjson", ".py", ".mjs"}:
        return text_lines(path), "text_lines"
    return None, "not_applicable"


def purpose_for(relative_path: str) -> str:
    if relative_path.startswith("outputs/"):
        return "Frozen D08C1 result or mainline audit view"
    if relative_path.startswith("qc/"):
        return "QC, environment, log, or visual-verification evidence"
    if relative_path.startswith("code/"):
        return "Reproduction, verification, workbook, or packaging source"
    if relative_path.startswith("control/"):
        return "Frozen contract, input, alias, raw-snapshot, or completion control"
    if relative_path.startswith("inputs/"):
        return "Frozen request, authority, continuity, or preflight-provenance input"
    return "Package documentation"


def authoritative(relative_path: str) -> str:
    return "YES" if relative_path.startswith("outputs/") and relative_path.lower().endswith(".csv") else "NO"


def write_readme() -> None:
    text = """# Q1 D08C1 accepted-species eligibility reproducible package v01

Status: **PASS; frozen outcome-blind census**  
Date: 2026-09-02

This package contains the frozen D08C1 accepted-species eligibility outputs, independent QC, audit workbook, exact D08B1 v02 authority inputs, D04/eligibility continuity inputs, request and Rhode Island decision, controls, and source code.

The analytical computation was not rerun during finalization. Finalization only validated existing files, copied them byte-for-byte, generated inventories/hashes, and created a deterministic ZIP.

The 15.35 GB formal FIA ZIP and extracted 71.565 GB SQLite database are not duplicated inside this delivery. Their frozen path, SHA-256, member size, and CRC-32 checks are recorded in `control/D08C1_INPUT_FREEZE_v01.md` and `outputs/Q1_D08C1_INPUT_AUDIT_v01.csv`.

Authoritative scientific tables are the UTF-8 CSV files under `outputs/`. The XLSX workbook is a human-review view, not a replacement authority.

To reproduce from the frozen local raw snapshot, review the contract and parameters, then run the builder and verifier from `code/` in the recorded environment. To recreate only the delivery package from already frozen outputs, run `code/finalize_d08c1_delivery_v01.py` from a clean target state.

No final grain, threshold, or species cohort is selected. No Little layer is merged, no external range search is performed, and no real-Q1 outcome is computed.
"""
    (STAGE_ROOT / "README_PACKAGE.md").write_text(text, encoding="utf-8")


def write_delivery_index() -> None:
    rows = []
    excluded = {"D08C1_DELIVERY_INDEX.md", "MANIFEST.json", "SHA256SUMS.csv"}
    for path in sorted(p for p in STAGE_ROOT.rglob("*") if p.is_file()):
        rp = rel(path, STAGE_ROOT)
        if rp in excluded:
            continue
        count, count_type = row_or_line_count(path)
        rows.append((rp, purpose_for(rp), count_type, "" if count is None else str(count), path.stat().st_size, sha256(path), authoritative(rp)))
    lines = [
        "# D08C1 delivery index v01",
        "",
        "Date: 2026-09-02  ",
        "Status: **FROZEN / PASS**",
        "",
        "Every non-self-referential payload file is listed below. `MANIFEST.json` and `SHA256SUMS.csv` provide the final machine-readable inventory.",
        "",
        "| File | Purpose | Count type | Count | Bytes | SHA-256 | Authoritative output |",
        "|---|---|---:|---:|---:|---|---|",
    ]
    for row in rows:
        lines.append("| `" + "` | `".join([row[0], row[1], row[2], row[3], str(row[4]), row[5], row[6]]) + "` |")
    lines.append("")
    (STAGE_ROOT / "D08C1_DELIVERY_INDEX.md").write_text("\n".join(lines), encoding="utf-8")


def write_manifests() -> None:
    manifest_files = []
    for path in sorted(p for p in STAGE_ROOT.rglob("*") if p.is_file()):
        rp = rel(path, STAGE_ROOT)
        if rp in {"MANIFEST.json", "SHA256SUMS.csv"}:
            continue
        count, count_type = row_or_line_count(path)
        manifest_files.append({
            "path": rp,
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
            "count_type": count_type,
            "count": count,
            "authoritative_output": authoritative(rp) == "YES",
        })
    dump_json(STAGE_ROOT / "MANIFEST.json", {
        "package_id": BASE,
        "date": "2026-09-02",
        "status": "PASS",
        "analysis_rerun_during_finalization": False,
        "file_count_excluding_self_controls": len(manifest_files),
        "files": manifest_files,
    })

    ledger_paths = sorted(p for p in STAGE_ROOT.rglob("*") if p.is_file() and p.name != "SHA256SUMS.csv")
    with (STAGE_ROOT / "SHA256SUMS.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["relative_path", "bytes", "sha256"])
        for path in ledger_paths:
            writer.writerow([rel(path, STAGE_ROOT), path.stat().st_size, sha256(path)])


def verify_stage() -> dict:
    ledger = STAGE_ROOT / "SHA256SUMS.csv"
    with ledger.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        path = STAGE_ROOT / row["relative_path"]
        require(path.is_file(), f"Ledger member missing: {path}")
        require(path.stat().st_size == int(row["bytes"]), f"Ledger byte mismatch: {path}")
        require(sha256(path) == row["sha256"], f"Ledger hash mismatch: {path}")
    actual = {rel(p, STAGE_ROOT) for p in STAGE_ROOT.rglob("*") if p.is_file() and p.name != "SHA256SUMS.csv"}
    listed = {row["relative_path"] for row in rows}
    require(actual == listed, "SHA256SUMS.csv does not cover every non-self file")
    return {"status": "PASS", "ledger_file_count": len(rows), "stage_file_count": len(actual) + 1}


def make_deterministic_zip() -> None:
    files = sorted(p for p in STAGE_ROOT.rglob("*") if p.is_file())
    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in files:
            arcname = f"{BASE}/{rel(path, STAGE_ROOT)}"
            info = zipfile.ZipInfo(arcname, FIXED_ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def verify_zip() -> dict:
    stage_hashes = {f"{BASE}/{rel(p, STAGE_ROOT)}": sha256(p) for p in STAGE_ROOT.rglob("*") if p.is_file()}
    with zipfile.ZipFile(ZIP_PATH, "r") as archive:
        require(archive.testzip() is None, "ZIP CRC test failed")
        members = [i for i in archive.infolist() if not i.is_dir()]
        require({i.filename for i in members} == set(stage_hashes), "ZIP member set differs from stage")
        for info in members:
            observed = hashlib.sha256(archive.read(info.filename)).hexdigest()
            require(observed == stage_hashes[info.filename], f"ZIP member hash mismatch: {info.filename}")
    return {"status": "PASS", "member_count": len(stage_hashes), "zip_bytes": ZIP_PATH.stat().st_size, "zip_sha256": sha256(ZIP_PATH)}


def main() -> int:
    for target in [FINAL_OUTPUTS, FINAL_QC, ARCHIVE, STAGE_PARENT]:
        require(not target.exists(), f"Refusing to overwrite existing finalization target: {target}")
    require(WORK_OUTPUTS.is_dir() and WORK_QC.is_dir(), "Frozen work outputs/QC are missing")

    audit = final_prepackage_audit()
    dump_json(WORK_QC / "D08C1_FINAL_PREPACKAGE_AUDIT_v01.json", audit)

    copy_tree_exact(WORK_OUTPUTS, FINAL_OUTPUTS)
    copy_tree_exact(WORK_QC, FINAL_QC)

    STAGE_ROOT.mkdir(parents=True, exist_ok=False)
    copy_tree_exact(FINAL_OUTPUTS, STAGE_ROOT / "outputs")
    copy_tree_exact(FINAL_QC, STAGE_ROOT / "qc")

    code_dir = STAGE_ROOT / "code"
    for name in [
        "inspect_d08c1_inputs_v01.py",
        "build_d08c1_accepted_species_eligibility_v01.py",
        "verify_d08c1_outputs_v01.py",
        "build_d08c1_audit_workbook_v01.mjs",
        "parameters_d08c1_v01.json",
        "finalize_d08c1_delivery_v01.py",
    ]:
        copy_file(ROOT / "06_src" / "d08c1_v01" / name, code_dir / name)

    control_dir = STAGE_ROOT / "control"
    for name in [
        "D08C1_FIA_ACCEPTED_SPECIES_ELIGIBILITY_CONTRACT_v01.md",
        "D08C1_STATE_ALIAS_FREEZE_v01.csv",
        "D08C1_INPUT_FREEZE_v01.md",
        "D08C1_FREEZE_v01.md",
        "RAW_FREEZE_v02.md",
        "raw_manifest_v02.csv",
        "sha256_raw_v02.txt",
    ]:
        copy_file(ROOT / "00_control" / name, control_dir / name)

    for source, target in package_inputs():
        copy_file(source, target)
    copy_tree_exact(ROOT / "05_qc" / "d08c1_v01_preflight", STAGE_ROOT / "inputs" / "preflight_provenance")

    write_readme()
    write_delivery_index()
    write_manifests()
    stage_verification = verify_stage()

    ARCHIVE.mkdir(parents=True, exist_ok=False)
    copy_tree_exact(STAGE_ROOT, ARCHIVE / "package")
    make_deterministic_zip()
    zip_verification = verify_zip()
    zip_hash = zip_verification["zip_sha256"]
    (ARCHIVE / f"{BASE}.zip.sha256").write_text(f"{zip_hash}  {BASE}.zip\n", encoding="ascii")
    dump_json(ARCHIVE / "ARCHIVE_INDEX_v01.json", {
        "package_id": BASE,
        "date": "2026-09-02",
        "status": "PASS",
        "analysis_rerun_during_finalization": False,
        "final_outputs": str(FINAL_OUTPUTS),
        "final_qc": str(FINAL_QC),
        "package_directory": str(ARCHIVE / "package"),
        "zip": str(ZIP_PATH),
        "zip_sha256": zip_hash,
        "stage_verification": stage_verification,
        "zip_verification": zip_verification,
    })
    copy_file(ROOT / "00_control" / "D08C1_FREEZE_v01.md", ARCHIVE / "D08C1_FREEZE_v01.md")

    print(json.dumps({
        "status": "PASS",
        "analysis_rerun": False,
        "prepackage_audit_checks": audit["check_count"],
        "final_outputs": str(FINAL_OUTPUTS),
        "final_qc": str(FINAL_QC),
        "zip": str(ZIP_PATH),
        "zip_bytes": ZIP_PATH.stat().st_size,
        "zip_sha256": zip_hash,
        "zip_members": zip_verification["member_count"],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, ensure_ascii=False, indent=2), file=sys.stderr)
        raise
