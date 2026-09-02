from __future__ import annotations

import csv
import hashlib
import json
import os
import platform
import shutil
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(r"C:\range_paper")
WORK = ROOT / "99_tmp" / "d09c_v01"
WORK_OUTPUT = WORK / "outputs"
WORK_QC = WORK / "qc"
FINAL_OUTPUT = ROOT / "04_derived" / "d09c_v01"
FINAL_QC = ROOT / "05_qc" / "d09c_v01"
ARCHIVE_DIR = ROOT / "10_archive" / "d09c_v01"
PACKAGE_NAME = "Q1_D09C_SPECIES_BLIND_REPORTING_STATE_PANEL_FOLD_AUDIT_REPRODUCIBLE_v01"
STAGE = ARCHIVE_DIR / PACKAGE_NAME
ZIP_PATH = ARCHIVE_DIR / f"{PACKAGE_NAME}.zip"
SIDECAR = ARCHIVE_DIR / f"{PACKAGE_NAME}.zip.sha256"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def text_lines(path: Path) -> int | None:
    if path.suffix.lower() not in {".csv", ".md", ".json", ".txt", ".py", ".mjs", ".ndjson"}:
        return None
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return sum(1 for _ in handle)


def data_rows(path: Path) -> int | None:
    if path.suffix.lower() != ".csv":
        return None
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return max(0, sum(1 for _ in csv.reader(handle)) - 1)


def relative(path: Path, base: Path = STAGE) -> str:
    return path.relative_to(base).as_posix()


def purpose_for(rel: str) -> str:
    name = Path(rel).name
    if rel.startswith("00_control/"):
        return "Frozen contract, input authority, scope, or completion state"
    if rel.startswith("01_authoritative_inputs/"):
        return "Exact authoritative request/decision/upstream evidence input"
    if rel.startswith("02_outputs/"):
        if name.endswith(".xlsx"):
            return "Human-readable audit workbook; CSV files remain canonical"
        if "PANEL_SUBPANEL_YEAR" in name:
            return "Canonical complete panel/subpanel/year/stratum/50-km all-plot ledger"
        if "TI_FOLD_WEIGHT" in name:
            return "Canonical complete temporally integrated fold-weight audit"
        if "MA_FOLD_WEIGHT" in name:
            return "Canonical complete mean-of-annual panel-weight audit"
        if name.endswith(".csv"):
            return "Canonical D09C audit output"
        return "D09C result note, decision queue, or output documentation"
    if rel.startswith("03_qc/"):
        return "Independent QC, environment, formula scan, or rendered workbook evidence"
    if rel.startswith("04_code/"):
        return "Reproducibility source code or frozen parameter file"
    return "Package metadata"


def authority_for(rel: str) -> str:
    name = Path(rel).name
    if rel.startswith("00_control/") or rel.startswith("01_authoritative_inputs/"):
        return "AUTHORITATIVE_INPUT_OR_CONTROL"
    if rel.startswith("02_outputs/") and name.endswith(".csv"):
        return "AUTHORITATIVE_OUTPUT"
    if rel.startswith("02_outputs/") and name in {"D09C_RESULT_NOTE_v01.md", "D09C_OPEN_DECISIONS_FOR_MAINLINE_v01.md"}:
        return "AUTHORITATIVE_OUTPUT"
    if name.endswith(".xlsx"):
        return "AUDIT_VIEW"
    if rel.startswith("03_qc/"):
        return "QC_EVIDENCE"
    if rel.startswith("04_code/"):
        return "REPRODUCIBILITY_CODE"
    return "PACKAGE_METADATA"


def copy_tree_exact(source: Path, destination: Path) -> None:
    shutil.copytree(source, destination, copy_function=shutil.copy2)


def write_prepackage_audit() -> None:
    independent = json.loads((WORK_QC / "D09C_INDEPENDENT_AUDIT_v01.json").read_text(encoding="utf-8"))
    workbook = json.loads((WORK_QC / "D09C_WORKBOOK_INDEPENDENT_AUDIT_v01.json").read_text(encoding="utf-8"))
    no_q1 = json.loads((WORK_QC / "D09C_NO_Q1_OUTCOME_AUDIT_v01.json").read_text(encoding="utf-8"))
    with (WORK_OUTPUT / "D09C_QC_v01.csv").open("r", encoding="utf-8-sig", newline="") as handle:
        qc_rows = list(csv.DictReader(handle))
    required_outputs = {
        "D09C_RESULT_NOTE_v01.md",
        "D09C_TEMPORAL_FRAME_AUDIT_v01.csv",
        "D09C_TEMPORAL_FRAME_SUMMARY_v01.csv",
        "D09C_EVALID_COMPONENT_LEDGER_v01.csv",
        "D09C_PANEL_SUBPANEL_YEAR_LEDGER_v01.csv",
        "D09C_WHOLE_PANEL_PARTITION_CANDIDATES_v01.csv",
        "D09C_TOP_PARTITION_DIAGNOSTICS_v01.csv",
        "D09C_LINEAGE_CROSSFOLD_AUDIT_v01.csv",
        "D09C_TI_FOLD_WEIGHT_AUDIT_v01.csv",
        "D09C_MA_FOLD_WEIGHT_AUDIT_v01.csv",
        "D09C_DESIGN_CALIBRATION_AUDIT_v01.csv",
        "D09C_OPEN_DECISIONS_FOR_MAINLINE_v01.md",
        "D09C_INPUT_AUDIT_v01.csv",
        "D09C_TABLE_ACCESS_AUDIT_v01.csv",
        "D09C_SQL_LEDGER_v01.csv",
        "D09C_QC_v01.csv",
        "Q1_D09C_MAINLINE_AUDIT_v01.xlsx",
        "README.md",
    }
    observed_outputs = {path.name for path in WORK_OUTPUT.iterdir() if path.is_file()}
    false_flags = {
        key: value
        for key, value in no_q1.items()
        if key not in {"status", "prohibited_operations"}
    }
    previews = list((WORK_QC / "WORKBOOK_PREVIEWS_v01").glob("*.png"))
    checks = {
        "required_outputs_present": required_outputs <= observed_outputs,
        "builder_qc_all_pass": bool(qc_rows) and all(row["status"] == "PASS" for row in qc_rows),
        "independent_output_audit_pass": independent.get("status") == "PASS" and independent.get("check_count") == 25,
        "independent_workbook_audit_pass": workbook.get("status") == "PASS" and workbook.get("check_count") == 11,
        "no_species_or_downstream_operation": no_q1.get("status") == "PASS" and not any(false_flags.values()) and not no_q1.get("prohibited_operations"),
        "workbook_preview_count_13": len(previews) == 13,
        "formula_error_scan_zero": "matched 0 entries" in (WORK_QC / "D09C_WORKBOOK_FORMULA_ERROR_SCAN_v01.ndjson").read_text(encoding="utf-8"),
    }
    failed = [name for name, passed in checks.items() if not passed]
    audit = {
        "audit_id": "D09C_PREPACKAGE_AUDIT_v01",
        "date": "2026-09-02",
        "status": "PASS" if not failed else "FAIL",
        "checks": checks,
        "failed": failed,
        "required_output_count": len(required_outputs),
        "workbook_sha256": sha256(WORK_OUTPUT / "Q1_D09C_MAINLINE_AUDIT_v01.xlsx"),
        "python": sys.version,
        "platform": platform.platform(),
    }
    (WORK_QC / "D09C_PREPACKAGE_AUDIT_v01.json").write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    if failed:
        raise RuntimeError(f"Prepackage audit failed: {failed}")


for target in [FINAL_OUTPUT, FINAL_QC, ARCHIVE_DIR]:
    if target.exists():
        raise FileExistsError(f"Refusing to overwrite existing final target: {target}")

write_prepackage_audit()

FINAL_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
FINAL_QC.parent.mkdir(parents=True, exist_ok=True)
ARCHIVE_DIR.mkdir(parents=True, exist_ok=False)
copy_tree_exact(WORK_OUTPUT, FINAL_OUTPUT)
copy_tree_exact(WORK_QC, FINAL_QC)

(STAGE / "00_control").mkdir(parents=True)
(STAGE / "01_authoritative_inputs").mkdir()

control_files = [
    ROOT / "00_control" / "RAW_FREEZE_v02.md",
    ROOT / "00_control" / "raw_manifest_v02.csv",
    ROOT / "00_control" / "sha256_raw_v02.txt",
    ROOT / "00_control" / "D09C_SPECIES_BLIND_DESIGN_AUDIT_CONTRACT_v01.md",
    ROOT / "00_control" / "D09C_INPUT_FREEZE_v01.md",
    ROOT / "00_control" / "D09C_FREEZE_v01.md",
]
for source in control_files:
    shutil.copy2(source, STAGE / "00_control" / source.name)

input_source = ROOT / "03_doc" / "D09C_SPECIES_BLIND_DESIGN_INPUTS_v01"
copy_tree_exact(input_source, STAGE / "01_authoritative_inputs" / input_source.name)
copy_tree_exact(FINAL_OUTPUT, STAGE / "02_outputs")
copy_tree_exact(FINAL_QC, STAGE / "03_qc")
copy_tree_exact(ROOT / "06_src" / "d09c_v01", STAGE / "04_code")

payload_files = sorted(path for path in STAGE.rglob("*") if path.is_file())
manifest = {
    "package": PACKAGE_NAME,
    "date": "2026-09-02",
    "scope": "species-blind FIA reporting-state / whole-P2PANEL fold / temporal / weight and variance calibration audit",
    "execution_status": "PASS",
    "nationwide_design_feasibility": "FAIL",
    "final_partition_selected": False,
    "downstream_started": False,
    "files": [
        {
            "path": relative(path),
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
            "text_lines": text_lines(path),
            "csv_data_rows": data_rows(path),
            "authority": authority_for(relative(path)),
            "purpose": purpose_for(relative(path)),
        }
        for path in payload_files
    ],
}
manifest_path = STAGE / "D09C_CONTENT_MANIFEST_v01.json"
manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

index_items = manifest["files"] + [
    {
        "path": manifest_path.name,
        "bytes": manifest_path.stat().st_size,
        "sha256": sha256(manifest_path),
        "text_lines": text_lines(manifest_path),
        "csv_data_rows": None,
        "authority": "PACKAGE_METADATA",
        "purpose": "Machine-readable content manifest",
    }
]
index_lines = [
    "# D09C delivery index v01",
    "",
    "Date: 2026-09-02  ",
    "Execution status: **PASS**  ",
    "Nationwide design feasibility: **FAIL**  ",
    "Final frame/partition/estimator: **NOT SELECTED**",
    "",
    "The full UTF-8 CSV files are authoritative. The XLSX workbook is an audit view. No species outcome, D08C2, Range Gate 0, Little/USGS, external range search, final cohort, or real Q1 operation is present.",
    "",
    "| Path | Purpose | CSV data rows | Text lines | Bytes | SHA-256 | Authority |",
    "|---|---|---:|---:|---:|---|---|",
]
for item in index_items:
    row_count = "" if item["csv_data_rows"] is None else str(item["csv_data_rows"])
    line_count = "" if item["text_lines"] is None else str(item["text_lines"])
    purpose = str(item["purpose"]).replace("|", "\\|")
    index_lines.append(
        f"| `{item['path']}` | {purpose} | {row_count} | {line_count} | {item['bytes']} | `{item['sha256']}` | {item['authority']} |"
    )
index_path = STAGE / "D09C_DELIVERY_INDEX_v01.md"
index_path.write_text("\n".join(index_lines) + "\n", encoding="utf-8")

hash_files = sorted(path for path in STAGE.rglob("*") if path.is_file())
hash_path = STAGE / "SHA256SUMS_v01.csv"
with hash_path.open("w", encoding="utf-8", newline="") as handle:
    writer = csv.writer(handle, lineterminator="\n")
    writer.writerow(["path", "bytes", "sha256"])
    for path in hash_files:
        writer.writerow([relative(path), path.stat().st_size, sha256(path)])

zip_members = sorted(path for path in STAGE.rglob("*") if path.is_file())
fixed_time = (2026, 9, 2, 0, 0, 0)
with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
    for source in zip_members:
        arcname = f"{PACKAGE_NAME}/{relative(source)}"
        info = zipfile.ZipInfo(arcname, date_time=fixed_time)
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 0o100644 << 16
        archive.writestr(info, source.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)

zip_sha = sha256(ZIP_PATH)
SIDECAR.write_text(f"{zip_sha}  {ZIP_PATH.name}\n", encoding="ascii")

archive_index = ARCHIVE_DIR / "ARCHIVE_INDEX.md"
archive_index.write_text(
    "\n".join(
        [
            "# D09C archive index v01",
            "",
            f"- ZIP: `{ZIP_PATH.name}`",
            f"- Bytes: {ZIP_PATH.stat().st_size}",
            f"- SHA-256: `{zip_sha}`",
            f"- Sidecar: `{SIDECAR.name}`",
            f"- Staged package: `{STAGE.name}/`",
            "- Execution: PASS",
            "- Nationwide design feasibility: FAIL",
            "- Downstream work: NOT STARTED",
        ]
    )
    + "\n",
    encoding="utf-8",
)

print(
    json.dumps(
        {
            "status": "PASS",
            "final_output": str(FINAL_OUTPUT),
            "final_qc": str(FINAL_QC),
            "stage": str(STAGE),
            "zip": str(ZIP_PATH),
            "zip_bytes": ZIP_PATH.stat().st_size,
            "zip_sha256": zip_sha,
            "zip_members": len(zip_members),
        },
        indent=2,
    )
)
