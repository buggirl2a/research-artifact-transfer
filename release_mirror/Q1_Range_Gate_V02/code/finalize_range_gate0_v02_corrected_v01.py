#!/usr/bin/env python3
"""Create and validate the immutable Range Gate 0 v02 corrected package."""

from __future__ import annotations

import csv
import hashlib
import json
import shutil
import zipfile
from pathlib import Path


ROOT = Path(r"C:\range_paper")
WORK = ROOT / "99_tmp" / "range_gate0_v02_corrected"
WORK_OUT, WORK_QC = WORK / "outputs", WORK / "qc"
RESULTS = ROOT / "07_results" / "range_gate0_v02_corrected"
FINAL_QC = ROOT / "05_qc" / "range_gate0_v02_corrected"
ARCHIVE = ROOT / "10_archive" / "range_gate0_v02_corrected"
PACKAGE_NAME = "Q1_RANGE_GATE0_V02_CORRECTED_GEOGRAPHIC_SEMANTICS_REPRODUCIBLE_v01"
STAGE = ARCHIVE / PACKAGE_NAME
ZIP_PATH = ARCHIVE / f"{PACKAGE_NAME}.zip"
SIDECAR = ARCHIVE / f"{PACKAGE_NAME}.zip.sha256"
POST = ARCHIVE / "RANGE_GATE0_V02_CORRECTED_POSTPACKAGE_VALIDATION_v01.json"
V01_CLASS = ROOT / "07_results" / "range_gate0_v01" / "Q1_RANGE_GATE0_SPECIES_CLASSIFICATION_v01.csv"
V01_ROOTS = [ROOT / "07_results" / "range_gate0_v01", ROOT / "05_qc" / "range_gate0_v01", ROOT / "10_archive" / "range_gate0_v01"]
V01_TREE_SHA = "a415cbc84b66f6d0bf01c4cfaab3449e9e49e872bed7464cf2d71a29f65e9100"
V01_CLASS_SHA = "243978406cb913c13898b333671000c30592079d076ef8b995822a1684f8a8cd"
CORE_HASHES = {
    "Q1_RANGE_GATE0_V02_CORRECTED_SPECIES_CLASSIFICATION_v01.csv": "d0ff6281d3e5a8aa2cb1438fd70cc2650163b6c512ffe8299c24d3555ddfcb64",
    "Q1_RANGE_GATE0_V02_CORRECTED_SUMMARY_v01.csv": "6fff3e6f9c90957e1c652c00691b1bf2437ef8f5f7253fb48ec266336fa92205",
    "Q1_RANGE_GATE0_V02_CORRECTED_DECISION_QUEUE_v01.csv": "da944cc5c7d035cd15cad49df76c620e1169dc18136703c16355a3a4e2bab69c",
    "Q1_RANGE_GATE0_V02_CORRECTED_FAIL_EXTRA_NA_v01.csv": "3f819a334126cbc2c66a05a3016db9ba310eb6fe9d065c4a9d15fb54408ecf2d",
}


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""): h.update(block)
    return h.hexdigest()


def v01_tree_digest() -> tuple[int, str]:
    records = []
    for base in V01_ROOTS:
        for path in sorted((p for p in base.rglob("*") if p.is_file()), key=lambda p: str(p).lower()):
            records.append(f"{path.relative_to(base.parent).as_posix()}|{path.stat().st_size}|{sha(path)}")
    return len(records), hashlib.sha256((("\n".join(records)) + "\n").encode("utf-8")).hexdigest()


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n"); writer.writeheader(); writer.writerows(rows)


def count_text(path: Path) -> tuple[str, object]:
    if path.suffix.lower() == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as f: return "data_rows", sum(1 for _ in csv.reader(f)) - 1
    if path.suffix.lower() in {".md", ".txt", ".py", ".mjs", ".json", ".ndjson"}: return "text_lines", len(path.read_text(encoding="utf-8").splitlines())
    return "not_applicable", ""


def role_purpose(rel: str) -> tuple[str, str, str]:
    name = Path(rel).name
    if name == "Q1_RANGE_GATE0_V02_CORRECTED_SPECIES_CLASSIFICATION_v01.csv": return "authoritative_output", "Fresh 312-species v02 corrected classification", "YES"
    if name == "Q1_RANGE_GATE0_V02_CORRECTED_SUMMARY_v01.csv": return "authoritative_output", "Corrected six-class summary", "YES"
    if name == "Q1_RANGE_GATE0_V02_CORRECTED_DECISION_QUEUE_v01.csv": return "authoritative_output", "Corrected later-review routing queue", "YES"
    if name == "Q1_RANGE_GATE0_V02_CORRECTED_FAIL_EXTRA_NA_v01.csv": return "authoritative_output", "Corrected explicit extra-North-America ledger", "YES"
    if "DELTA_AUDIT" in name: return "authoritative_audit", "Complete post-freeze v01-to-v02 species delta", "YES"
    if "DELTA_SUMMARY" in name: return "authoritative_audit", "Post-freeze delta transition summary", "YES"
    if name == "RANGE_GATE0_V02_CORRECTED_RESULT_NOTE_v01.md": return "authoritative_output", "Mainline result note and STOP boundary", "YES"
    if name.endswith("MAINLINE_AUDIT_v01.xlsx"): return "audit_workbook", "Mainline-readable audit workbook", "NO"
    if rel.startswith("controls/"): return "frozen_control", "Corrected contract, freezes, and v01 negative-audit status", "YES"
    if rel.startswith("inputs/v01_immutable_baseline/"): return "frozen_baseline", "Read-only v01 classification copied after v02 science freeze for delta reproducibility", "YES"
    if rel.startswith("inputs/"): return "frozen_input", "Source-frozen v02 request and unchanged D08B1 v02 authority", "YES"
    if rel.startswith("qc/"): return "qc", "Build, semantic-regression, delta, immutability, independent, or workbook QC", "NO"
    if rel.startswith("code/"): return "source", "Reproducible source and frozen parameters", "NO"
    return "other", "Supporting reproducibility artifact", "NO"


def deterministic_zip(source: Path, target: Path) -> None:
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for path in sorted(p for p in source.rglob("*") if p.is_file()):
            arcname = (Path(PACKAGE_NAME) / path.relative_to(source)).as_posix()
            info = zipfile.ZipInfo(arcname, date_time=(2026, 9, 3, 0, 0, 0)); info.compress_type = zipfile.ZIP_DEFLATED; info.external_attr = 0o100644 << 16
            zf.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def main() -> int:
    for target in [RESULTS, FINAL_QC, ARCHIVE]:
        if target.exists(): raise RuntimeError(f"Refusing to overwrite final target: {target}")
    for name, expected in CORE_HASHES.items():
        if sha(WORK_OUT / name) != expected: raise RuntimeError(f"Frozen v02 core changed: {name}")
    v01_count, v01_digest = v01_tree_digest()
    if v01_count != 76 or v01_digest != V01_TREE_SHA or sha(V01_CLASS) != V01_CLASS_SHA: raise RuntimeError("v01 immutable baseline changed before packaging")
    final_audit = json.loads((WORK_QC / "RANGE_GATE0_V02_CORRECTED_INDEPENDENT_OUTPUT_AUDIT_v01.json").read_text(encoding="utf-8"))
    workbook_audit = json.loads((WORK_QC / "RANGE_GATE0_V02_CORRECTED_WORKBOOK_VALIDATION_v01.json").read_text(encoding="utf-8"))
    if final_audit["status"] != "PASS" or workbook_audit["status"] != "PASS": raise RuntimeError("Independent output/workbook audit not PASS")

    RESULTS.parent.mkdir(parents=True, exist_ok=True); FINAL_QC.parent.mkdir(parents=True, exist_ok=True); ARCHIVE.mkdir(parents=True)
    shutil.copytree(WORK_OUT, RESULTS, ignore=shutil.ignore_patterns("*.xlsx.inspect.ndjson")); shutil.copytree(WORK_QC, FINAL_QC)
    (STAGE / "outputs").mkdir(parents=True); (STAGE / "controls").mkdir(); (STAGE / "code").mkdir(); (STAGE / "qc").mkdir()
    shutil.copytree(ROOT / "03_doc" / "RANGE_GATE0_V02_CORRECTED_INPUTS_v01", STAGE / "inputs")
    (STAGE / "inputs" / "v01_immutable_baseline").mkdir()
    shutil.copy2(V01_CLASS, STAGE / "inputs" / "v01_immutable_baseline" / V01_CLASS.name)
    for path in RESULTS.iterdir():
        if path.is_file(): shutil.copy2(path, STAGE / "outputs" / path.name)
    shutil.copytree(FINAL_QC, STAGE / "qc", dirs_exist_ok=True)
    for name in ["RANGE_GATE0_V02_CORRECTED_CONTRACT_v01.md", "RANGE_GATE0_V02_CORRECTED_INPUT_FREEZE_v01.md", "RANGE_GATE0_V02_CORRECTED_SCIENTIFIC_OUTPUT_FREEZE_v01.md", "RANGE_GATE0_V02_CORRECTED_V01_BASELINE_STATUS_v01.md"]:
        shutil.copy2(ROOT / "00_control" / name, STAGE / "controls" / name)
    for name in ["parameters_range_gate0_v02_corrected_v01.json", "build_range_gate0_v02_corrected_v01.py", "verify_range_gate0_v02_core_v01.py", "build_range_gate0_v01_to_v02_delta_v01.py", "verify_range_gate0_v02_outputs_v01.py", "build_range_gate0_v02_audit_workbook_v01.mjs", "verify_range_gate0_v02_workbook_v01.py", "finalize_range_gate0_v02_corrected_v01.py", "RANGE_GATE0_V02_ENGINEERING_LOG_v01.md"]:
        shutil.copy2(ROOT / "06_src" / "range_gate0_v02_corrected" / name, STAGE / "code" / name)

    payload = sorted(p for p in STAGE.rglob("*") if p.is_file())
    manifest_rows = []
    for path in payload:
        rel = path.relative_to(STAGE).as_posix(); role, purpose, authoritative = role_purpose(rel); count_type, count = count_text(path)
        manifest_rows.append({"relative_path": rel, "role": role, "purpose": purpose, "count_type": count_type, "count": count, "size_bytes": path.stat().st_size, "sha256": sha(path), "authoritative": authoritative})
    content_manifest = STAGE / "CONTENT_MANIFEST_v01.csv"
    write_csv(content_manifest, manifest_rows, ["relative_path", "role", "purpose", "count_type", "count", "size_bytes", "sha256", "authoritative"])
    index = ["# Range Gate 0 v02 corrected delivery index", "", "Scientific status: v02 corrected PASS. v01 is preserved as `MAINLINE_CONTRACT_SEMANTICS_FAIL / COMPUTATIONAL_EXECUTION_PASS`.", "", "Read first: `outputs/RANGE_GATE0_V02_CORRECTED_RESULT_NOTE_v01.md`, `outputs/Q1_RANGE_GATE0_V02_CORRECTED_SUMMARY_v01.csv`, `qc/RANGE_GATE0_V02_CORRECTED_INDEPENDENT_OUTPUT_AUDIT_v01.json`, and `outputs/Q1_RANGE_GATE0_V01_TO_V02_CORRECTED_DELTA_AUDIT_v01.csv`.", "", "UTF-8 CSV/MD/JSON outputs are authoritative; the XLSX is an audit view. `CONTENT_MANIFEST_v01.csv` covers payload files present before the index and checksum ledger were written.", "", "| Relative path | Role | Purpose | Count | Bytes | SHA-256 | Authoritative |", "|---|---|---|---:|---:|---|---|"]
    for row in manifest_rows:
        count = f"{row['count']} {row['count_type']}" if row["count"] != "" else "—"
        index.append(f"| `{row['relative_path']}` | {row['role']} | {row['purpose']} | {count} | {row['size_bytes']} | `{row['sha256']}` | {row['authoritative']} |")
    index.extend(["", "STOP: this package does not authorize D08C2, Little detailed processing, external range search, final cohort construction, or real Q1.", ""])
    delivery_index = STAGE / "RANGE_GATE0_V02_CORRECTED_DELIVERY_INDEX_v01.md"; delivery_index.write_text("\n".join(index), encoding="utf-8")
    ledger = STAGE / "SHA256SUMS.csv"; ledger_files = sorted(p for p in STAGE.rglob("*") if p.is_file())
    write_csv(ledger, [{"relative_path": p.relative_to(STAGE).as_posix(), "bytes": p.stat().st_size, "sha256": sha(p)} for p in ledger_files], ["relative_path", "bytes", "sha256"])
    deterministic_zip(STAGE, ZIP_PATH); zip_hash = sha(ZIP_PATH); SIDECAR.write_text(f"{zip_hash}  {ZIP_PATH.name}\n", encoding="utf-8")

    checks = []
    def add(name, passed, actual, expected): checks.append({"check": name, "status": "PASS" if passed else "FAIL", "actual": actual, "expected": expected})
    with zipfile.ZipFile(ZIP_PATH, "r") as zf:
        bad = zf.testzip(); members = zf.namelist()
        add("zip_integrity", bad is None, bad, None); add("zip_member_count", len(members) == len([p for p in STAGE.rglob("*") if p.is_file()]), len(members), len([p for p in STAGE.rglob("*") if p.is_file()]))
    ledger_rows = list(csv.DictReader(ledger.open("r", encoding="utf-8-sig", newline="")))
    bad_ledger = [row["relative_path"] for row in ledger_rows if sha(STAGE / row["relative_path"]) != row["sha256"] or (STAGE / row["relative_path"]).stat().st_size != int(row["bytes"])]
    add("stage_checksum_ledger", not bad_ledger, bad_ledger, [])
    add("sidecar_matches_zip", SIDECAR.read_text(encoding="utf-8").split()[0] == zip_hash, SIDECAR.read_text(encoding="utf-8").split()[0], zip_hash)
    core_copy_bad = [name for name, expected in CORE_HASHES.items() if sha(RESULTS / name) != expected or sha(STAGE / "outputs" / name) != expected]
    add("frozen_core_copied_byte_for_byte", not core_copy_bad, core_copy_bad, [])
    add("v01_classification_copy_exact", sha(STAGE / "inputs" / "v01_immutable_baseline" / V01_CLASS.name) == V01_CLASS_SHA, sha(STAGE / "inputs" / "v01_immutable_baseline" / V01_CLASS.name), V01_CLASS_SHA)
    final_v01_count, final_v01_digest = v01_tree_digest(); add("v01_full_tree_still_immutable", final_v01_count == 76 and final_v01_digest == V01_TREE_SHA, [final_v01_count, final_v01_digest], [76, V01_TREE_SHA])
    add("independent_output_audit_PASS", final_audit["status"] == "PASS", final_audit["status"], "PASS")
    add("workbook_validation_PASS", workbook_audit["status"] == "PASS", workbook_audit["status"], "PASS")
    add("delta_present_in_package", (STAGE / "outputs" / "Q1_RANGE_GATE0_V01_TO_V02_CORRECTED_DELTA_AUDIT_v01.csv").is_file(), True, True)
    status = "PASS" if all(row["status"] == "PASS" for row in checks) else "FAIL"
    post = {"status": status, "package_name": PACKAGE_NAME, "package_directory": str(STAGE), "zip_path": str(ZIP_PATH), "zip_size_bytes": ZIP_PATH.stat().st_size, "zip_sha256": zip_hash, "sidecar_path": str(SIDECAR), "validation_check_count": len(checks), "validation_pass_count": sum(row["status"] == "PASS" for row in checks), "v01_tree_digest_after_packaging": final_v01_digest, "checks": checks}
    POST.write_text(json.dumps(post, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    shutil.copy2(delivery_index, ARCHIVE / "RANGE_GATE0_V02_CORRECTED_DELIVERY_INDEX_v01.md")
    if status != "PASS": raise RuntimeError("ENGINEERING_FAIL: postpackage validation failed")
    print(json.dumps({"status": status, "zip": str(ZIP_PATH), "bytes": ZIP_PATH.stat().st_size, "sha256": zip_hash, "stage_files": len(members), "validation": f"{post['validation_pass_count']}/{post['validation_check_count']}", "v01_tree_digest": final_v01_digest}))
    return 0


if __name__ == "__main__": raise SystemExit(main())
