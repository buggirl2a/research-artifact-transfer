from __future__ import annotations

import csv
import gzip
import hashlib
import json
import os
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path


ROOT = Path(r"C:\range_paper")
SRC = ROOT / "06_src" / "d10d"
ARCH = ROOT / "10_archive" / "d10d"
PKG = ARCH / "pkg"
OUT = PKG / "out"
QC = PKG / "qc"
MAN = PKG / "manifest"
PKG_SRC = PKG / "src"
ZIP = ARCH / "D10D_v01.zip"
SIDECAR = ARCH / "D10D_v01.zip.sha256"
EXT_INDEX = ARCH / "D10D_DELIVERY_INDEX_v01.md"
EXT_VALIDATION = ARCH / "POSTPACKAGE_VALIDATION_v01.json"
TRANSFER = ARCH / "TRANSFER_MANIFEST_v01.csv"
TRANSFER_NAME = "Q1-D10D-v01-20260905"
FIXED_TIME = (2020, 1, 1, 0, 0, 0)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def line_count(path: Path) -> str:
    suffixes = "".join(path.suffixes).lower()
    try:
        if suffixes.endswith(".csv.gz"):
            with gzip.open(path, "rt", encoding="utf-8-sig", newline="") as handle:
                return str(max(sum(1 for _ in handle) - 1, 0))
        if path.suffix.lower() == ".csv":
            with path.open("r", encoding="utf-8-sig", newline="") as handle:
                return str(max(sum(1 for _ in handle) - 1, 0))
        if path.suffix.lower() in {".md", ".txt", ".json", ".ndjson", ".py", ".mjs", ".ps1"}:
            with path.open("r", encoding="utf-8-sig", errors="replace") as handle:
                return str(sum(1 for _ in handle))
        if path.suffix.lower() == ".xlsx":
            return "7 sheets"
    except (OSError, UnicodeError):
        return "N/A"
    return "N/A"


def role_for(path: Path) -> str:
    rel = path.relative_to(PKG).as_posix()
    if rel == "D10D_DELIVERY_INDEX_v01.md":
        return "delivery_index"
    if rel == "README.md":
        return "readme"
    if rel.endswith("result_note_v01.md"):
        return "result_note"
    if rel.endswith("audit_v01.xlsx"):
        return "workbook"
    if rel.startswith("control/"):
        return "frozen_contract" if "contract" in rel else "source_request"
    if rel.startswith("out/"):
        return "result_table" if ".csv" in rel else "result_output"
    if rel.startswith("qc/"):
        return "qc"
    if rel.startswith("src/"):
        return "code"
    if rel.startswith("fig/"):
        return "figure"
    if rel.endswith("SHA256SUMS.txt"):
        return "checksum"
    if rel.startswith("manifest/"):
        return "manifest"
    return "other"


def deterministic_zip(destination: Path) -> None:
    files = sorted((p for p in PKG.rglob("*") if p.is_file()), key=lambda p: p.relative_to(PKG).as_posix())
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9, allowZip64=True) as archive:
        for path in files:
            rel = path.relative_to(PKG).as_posix()
            info = zipfile.ZipInfo(f"D10D_v01/{rel}", date_time=FIXED_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = (0o100644 & 0xFFFF) << 16
            info.flag_bits |= 0x800
            archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def verify_zip(path: Path) -> tuple[list[dict[str, object]], list[str]]:
    failures: list[str] = []
    rows: list[dict[str, object]] = []
    expected = {f"D10D_v01/{p.relative_to(PKG).as_posix()}": p for p in PKG.rglob("*") if p.is_file()}
    with zipfile.ZipFile(path, "r") as archive:
        infos = archive.infolist()
        names = [x.filename for x in infos]
        if len(names) != len(set(names)):
            failures.append("duplicate ZIP member names")
        if set(names) != set(expected):
            failures.append("ZIP member set differs from frozen package directory")
        if archive.testzip() is not None:
            failures.append("ZIP CRC failure")
        for info in infos:
            data = archive.read(info.filename)
            disk = expected.get(info.filename)
            disk_sha = sha256_file(disk) if disk else "MISSING"
            member_sha = sha256_bytes(data)
            if member_sha != disk_sha:
                failures.append(f"member hash mismatch: {info.filename}")
            rows.append({"member": info.filename, "size_bytes": info.file_size, "sha256": member_sha})
    return rows, failures


for name in ["build.py", "audit.mjs", "verify.py", "finalize.py", "run_all.ps1"]:
    shutil.copyfile(SRC / name, PKG_SRC / name)

registry_lower = MAN / "registry_delta_v01.csv"
registry_upper = MAN / "REGISTRY_DELTA_v01.csv"
if registry_lower.is_file():
    actual_name = next((p.name for p in MAN.iterdir() if p.name.lower() == "registry_delta_v01.csv"), "")
    if actual_name != "REGISTRY_DELTA_v01.csv":
        registry_temp = MAN / "registry_delta_tmp.csv"
        registry_lower.rename(registry_temp)
        registry_temp.rename(registry_upper)

readme = """# D10D reproducible package v01

Terminal status: `ZERO_OPPORTUNITY_SOURCE_ATTRIBUTION_COMPLETE_READY_FOR_MAINLINE`

This package is a synthetic oracle-support diagnostic of zero-opportunity and measurable-domain source attribution. It does not assign a scientific PASS/HOLD/FAIL, select a real-data measurable domain, repair the frozen A2 estimator, read real species outcomes, or run real Q1.

## First-read files

- `out/result_note_v01.md`: quantitative answers to Q1-Q8 and the interpretation boundary.
- `out/attrib_summary_v01.csv`: pooled D0/D1/D2/D3 source-attribution summary.
- `out/common_v01.csv`: common downstream comparison by state, regime, and orientation.
- `out/domain_summary_v01.csv`: cell, plot, TI-weight, and effective-block-area retention.
- `out/audit_v01.xlsx`: human-readable seven-sheet audit workbook.
- `qc/validation_v01.json`: independent post-computation validation.
- `manifest/SHA256SUMS.txt`: payload hashes; by construction it excludes itself and the delivery index.

## Reproduction

On the frozen local environment, run `src/run_all.ps1`. The runner verifies all authoritative input identities, rebuilds D0/D1/D2/D3, exports and re-imports the workbook, independently validates outputs, and creates the deterministic ZIP and sidecars. It uses only the frozen local D10CR, D10C-A, D10B, and D10A packages.

STOP boundary: mainline alone decides interpretation, any real-data estimand, and any next task.
"""
(PKG / "README.md").write_text(readme, encoding="utf-8")

sha_path = MAN / "SHA256SUMS.txt"
index_path = PKG / "D10D_DELIVERY_INDEX_v01.md"
for stale in [sha_path, index_path]:
    if stale.exists():
        stale.unlink()

manifest_files = sorted((p for p in PKG.rglob("*") if p.is_file()), key=lambda p: p.relative_to(PKG).as_posix())
sha_lines = [f"{sha256_file(p)}  {p.relative_to(PKG).as_posix()}" for p in manifest_files]
sha_path.write_text("\n".join(sha_lines) + "\n", encoding="utf-8")

index_files = sorted((p for p in PKG.rglob("*") if p.is_file() and p != index_path), key=lambda p: p.relative_to(PKG).as_posix())
index_lines = [
    "# D10D delivery index v01",
    "",
    "Terminal: `ZERO_OPPORTUNITY_SOURCE_ATTRIBUTION_COMPLETE_READY_FOR_MAINLINE`",
    "",
    "The table lists every frozen package file except this index itself. `manifest/SHA256SUMS.txt` lists every payload file that existed before the checksum and index were written, thereby avoiding circular self-hashes.",
    "",
    "| Relative path | Role | Rows/lines | Bytes | SHA-256 | Authority |",
    "|---|---:|---:|---:|---|---|",
]
for path in index_files:
    rel = path.relative_to(PKG).as_posix()
    authority = "YES" if rel.startswith(("control/", "out/", "qc/", "manifest/")) or rel in {"README.md"} else "SUPPORTING"
    index_lines.append(f"| `{rel}` | {role_for(path)} | {line_count(path)} | {path.stat().st_size} | `{sha256_file(path)}` | {authority} |")
index_lines.extend(["", "Scientific disposition: `NOT_ASSIGNED`. No real species or real Q1 output is present.", ""])
index_path.write_text("\n".join(index_lines), encoding="utf-8")
shutil.copyfile(index_path, EXT_INDEX)

deterministic_zip(ZIP)
zip_sha = sha256_file(ZIP)
SIDECAR.write_text(f"{zip_sha}  {ZIP.name}\n", encoding="utf-8")

with tempfile.TemporaryDirectory(dir=ROOT / "99_tmp" / "d10d") as temp_dir:
    second_zip = Path(temp_dir) / "repeat.zip"
    deterministic_zip(second_zip)
    repeat_sha = sha256_file(second_zip)

members, zip_failures = verify_zip(ZIP)
sidecar_ok = SIDECAR.read_text(encoding="utf-8").strip() == f"{zip_sha}  {ZIP.name}"
deterministic_ok = repeat_sha == zip_sha
internal_validation = json.loads((QC / "validation_v01.json").read_text(encoding="utf-8"))
xlsx_validation = json.loads((QC / "xlsx_validation_v01.json").read_text(encoding="utf-8"))
max_member_chars = max(len(r["member"]) for r in members)
path_candidates = list(PKG.rglob("*")) + [ZIP, SIDECAR, EXT_INDEX, EXT_VALIDATION, TRANSFER]
max_abs_chars = max(len(str(p.resolve())) for p in path_candidates)
post_status = "PASS" if not zip_failures and sidecar_ok and deterministic_ok and internal_validation.get("validation_status") == "PASS" and xlsx_validation.get("status") == "PASS" and max_abs_chars < 256 and max_member_chars < 256 else "FAIL"
post = {
    "task_id": "D10D_ZERO_OPPORTUNITY_MEASURABLE_DOMAIN_SOURCE_ATTRIBUTION_v01",
    "terminal_status": "ZERO_OPPORTUNITY_SOURCE_ATTRIBUTION_COMPLETE_READY_FOR_MAINLINE",
    "postpackage_validation_status": post_status,
    "scientific_disposition": "NOT_ASSIGNED",
    "zip_path": str(ZIP),
    "zip_size_bytes": ZIP.stat().st_size,
    "zip_sha256": zip_sha,
    "zip_member_count": len(members),
    "zip_member_set_and_hashes_match_disk": not zip_failures,
    "zip_failures": zip_failures,
    "deterministic_repeat_sha256": repeat_sha,
    "deterministic_repeat_match": deterministic_ok,
    "sidecar_exact": sidecar_ok,
    "internal_validation_status": internal_validation.get("validation_status"),
    "xlsx_validation_status": xlsx_validation.get("status"),
    "max_absolute_path_chars": max_abs_chars,
    "max_zip_member_path_chars": max_member_chars,
    "windows_path_limit_check": "PASS" if max_abs_chars < 256 and max_member_chars < 256 else "FAIL",
    "boundary": "Synthetic diagnostic only; no scientific disposition, real species, estimator repair, support repair, real World 0, or real Q1.",
}
EXT_VALIDATION.write_text(json.dumps(post, indent=2) + "\n", encoding="utf-8")

transfer_rows: list[dict[str, object]] = []


def add_transfer(path: Path, relative: str, role: str, target: str, required: str, priority: str, notes: str) -> None:
    transfer_rows.append({
        "local_path": str(path.resolve()),
        "relative_path": relative,
        "role": role,
        "upload_target": target,
        "required": required,
        "mainline_priority": priority,
        "size_bytes": path.stat().st_size,
        "sha256": sha256_file(path),
        "notes": notes,
    })


add_transfer(ZIP, ZIP.name, "reproducible_zip", "release", "YES", "FIRST_READ", "Complete deterministic frozen package.")
add_transfer(SIDECAR, SIDECAR.name, "checksum", "mirror", "YES", "FIRST_READ", "Exact SHA-256 sidecar for the Release ZIP.")
add_transfer(EXT_INDEX, EXT_INDEX.name, "delivery_index", "mirror", "YES", "FIRST_READ", "Human-readable inventory with sizes and hashes.")
add_transfer(EXT_VALIDATION, EXT_VALIDATION.name, "qc_json", "mirror", "YES", "IMPORTANT", "Independent post-package integrity validation.")

for path in sorted((p for p in PKG.rglob("*") if p.is_file()), key=lambda p: p.relative_to(PKG).as_posix()):
    rel = path.relative_to(PKG).as_posix()
    suffixes = "".join(path.suffixes).lower()
    role = role_for(path)
    direct_text = path.suffix.lower() in {".csv", ".md", ".json", ".txt", ".ndjson", ".py", ".mjs", ".ps1"}
    if direct_text:
        target = "mirror"
    elif suffixes.endswith(".csv.gz") or path.suffix.lower() in {".xlsx", ".png"}:
        target = "release"
    else:
        target = "local_only"
    required = "YES" if role in {"result_note", "result_table", "workbook", "frozen_contract", "qc", "code", "checksum", "manifest", "delivery_index", "readme"} else "NO"
    priority = "FIRST_READ" if role in {"result_note", "delivery_index", "readme"} else "IMPORTANT" if role in {"workbook", "frozen_contract", "qc", "checksum", "manifest"} else "SUPPORTING" if role in {"result_table", "code"} else "ARCHIVE_ONLY"
    add_transfer(path, f"release_mirror/{TRANSFER_NAME}/{rel}", role, target, required, priority, "Frozen package member; preserve bytes and SHA-256.")

transfer_fields = ["local_path", "relative_path", "role", "upload_target", "required", "mainline_priority", "size_bytes", "sha256", "notes"]
write_csv(TRANSFER, transfer_rows, transfer_fields)

transfer_sha = sha256_file(TRANSFER)

print(json.dumps({
    "status": post_status,
    "terminal_status": post["terminal_status"],
    "zip": str(ZIP),
    "zip_size_bytes": ZIP.stat().st_size,
    "zip_sha256": zip_sha,
    "zip_members": len(members),
    "transfer_manifest_rows": len(transfer_rows),
    "transfer_manifest_sha256": transfer_sha,
    "max_absolute_path_chars": max_abs_chars,
    "max_zip_member_path_chars": max_member_chars,
}, indent=2))
raise SystemExit(0 if post_status == "PASS" else 1)
