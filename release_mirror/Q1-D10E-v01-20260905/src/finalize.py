from __future__ import annotations

import csv
import gzip
import hashlib
import json
import shutil
import tempfile
import zipfile
from pathlib import Path


ROOT = Path(r"C:\range_paper")
SRC = ROOT / "06_src" / "d10e"
ARCH = ROOT / "10_archive" / "d10e"
PKG = ARCH / "pkg"
OUT = PKG / "out"
QC = PKG / "qc"
MAN = PKG / "manifest"
PKG_SRC = PKG / "src"
ZIP = ARCH / "D10E_v01.zip"
SIDECAR = ARCH / "D10E_v01.zip.sha256"
EXT_INDEX = ARCH / "D10E_DELIVERY_INDEX_v01.md"
EXT_VALIDATION = ARCH / "POSTPACKAGE_VALIDATION_v01.json"
TRANSFER = ARCH / "TRANSFER_MANIFEST_v01.csv"
TRANSFER_NAME = "Q1-D10E-v01-20260905"
TERMINAL = "ABUNDANCE_MEASUREMENT_NOISE_DECOMPOSITION_COMPLETE_READY_FOR_MAINLINE"
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
            return "12 sheets"
    except (OSError, UnicodeError):
        return "N/A"
    return "N/A"


def role_for(path: Path) -> str:
    rel = path.relative_to(PKG).as_posix()
    low = rel.lower()
    if rel == "D10E_DELIVERY_INDEX_v01.md":
        return "delivery_index"
    if rel == "README.md":
        return "readme"
    if low.endswith("result_note_v01.md"):
        return "result_note"
    if low.endswith("audit_v01.xlsx"):
        return "workbook"
    if rel.startswith("control/"):
        return "frozen_contract" if "contract" in low or "hierarchy" in low or "ledger" in low else "source_request"
    if rel.startswith("out/"):
        return "result_table" if ".csv" in low else "result_output"
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


def package_files() -> list[Path]:
    return sorted((p for p in PKG.rglob("*") if p.is_file()), key=lambda p: p.relative_to(PKG).as_posix())


def deterministic_zip(destination: Path) -> None:
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9, allowZip64=True) as archive:
        for path in package_files():
            rel = path.relative_to(PKG).as_posix()
            info = zipfile.ZipInfo(f"D10E_v01/{rel}", date_time=FIXED_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = (0o100644 & 0xFFFF) << 16
            info.flag_bits |= 0x800
            archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def verify_zip(path: Path) -> tuple[list[dict[str, object]], list[str]]:
    failures: list[str] = []
    rows: list[dict[str, object]] = []
    expected = {f"D10E_v01/{p.relative_to(PKG).as_posix()}": p for p in package_files()}
    with zipfile.ZipFile(path, "r") as archive:
        infos = archive.infolist()
        names = [info.filename for info in infos]
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


def verify_internal_sha() -> list[str]:
    failures: list[str] = []
    sha_path = MAN / "SHA256SUMS.txt"
    for line in sha_path.read_text(encoding="utf-8").splitlines():
        expected, rel = line.split("  ", 1)
        path = PKG / Path(rel)
        if not path.is_file():
            failures.append(f"missing manifest payload: {rel}")
        elif sha256_file(path) != expected:
            failures.append(f"manifest hash mismatch: {rel}")
    return failures


for directory in (ARCH, PKG, OUT, QC, MAN, PKG_SRC):
    directory.mkdir(parents=True, exist_ok=True)

source_names = ["build.py", "verify.py", "figures.py", "audit.mjs", "finalize.py", "run_all.ps1"]
for name in source_names:
    source = SRC / name
    if not source.is_file():
        raise RuntimeError(f"missing reproduction source: {source}")
    shutil.copyfile(source, PKG_SRC / name)

required = [
    OUT / "Q1_D10E_RESULT_NOTE_v01.md",
    OUT / "state_summary_v01.csv",
    OUT / "source_decomp_v01.csv",
    OUT / "k_ladder_summary_v01.csv",
    OUT / "map_recovery_summary_v01.csv",
    OUT / "uncertainty_summary_v01.csv",
    OUT / "information_relationships_v01.csv",
    OUT / "audit_v01.xlsx",
    QC / "build_summary_v01.json",
    QC / "independent_validation_v01.json",
    QC / "xlsx_validation_v01.json",
    MAN / "REGISTRY_DELTA_v01.csv",
]
required.extend(PKG / "fig" / name for name in (
    "state_separation_v01.png",
    "source_decomposition_v01.png",
    "k_ladder_v01.png",
    "uncertainty_coverage_v01.png",
))
missing = [str(path) for path in required if not path.is_file()]
if missing:
    raise RuntimeError("missing final package inputs: " + "; ".join(missing))

readme = f"""# D10E reproducible package v01

Terminal status: `{TERMINAL}`

This package decomposes abundance-measurement noise under the frozen D3 common measurable domain using synthetic oracle worlds. It separates the expected measurement operator, normalization nonlinearity, finite-realization downstream effect, and current-realization deviation. It does not assign a scientific PASS/HOLD/FAIL, modify the frozen A2 estimator, fit a new uncertainty model, perform support recovery, read real species outcomes, or run real Q1.

## First-read files

- `out/Q1_D10E_RESULT_NOTE_v01.md`: quantitative answers and interpretation boundary.
- `out/state_summary_v01.csv`: E0-E5 state comparison.
- `out/source_decomp_v01.csv`: four-component decomposition.
- `out/k_ladder_summary_v01.csv`: repeated-survey averaging ladder.
- `out/audit_v01.xlsx`: human-readable twelve-sheet audit workbook.
- `qc/independent_validation_v01.json`: independent 30-check validation.
- `manifest/SHA256SUMS.txt`: payload hashes; it excludes itself and the delivery index to avoid circular hashes.

## Reproduction

On the frozen local environment, run `src/run_all.ps1`. It verifies authoritative inputs, rebuilds all E0-E5 outputs, runs independent checks, creates figures and the workbook, and emits a deterministic ZIP plus sidecars.

STOP boundary: mainline alone decides interpretation, any scientific disposition, and any next task.
"""
(PKG / "README.md").write_text(readme, encoding="utf-8")

sha_path = MAN / "SHA256SUMS.txt"
index_path = PKG / "D10E_DELIVERY_INDEX_v01.md"
for stale in (sha_path, index_path):
    if stale.exists():
        stale.unlink()

manifest_files = package_files()
sha_path.write_text("\n".join(f"{sha256_file(p)}  {p.relative_to(PKG).as_posix()}" for p in manifest_files) + "\n", encoding="utf-8")

index_files = [p for p in package_files() if p != index_path]
index_lines = [
    "# D10E delivery index v01",
    "",
    f"Terminal: `{TERMINAL}`",
    "",
    "Every frozen package file except this index is listed below. `manifest/SHA256SUMS.txt` covers every payload present before the checksum and index were written, avoiding circular self-hashes.",
    "",
    "| Relative path | Role | Rows/lines | Bytes | SHA-256 | Authority |",
    "|---|---:|---:|---:|---|---|",
]
for path in index_files:
    rel = path.relative_to(PKG).as_posix()
    authority = "YES" if rel.startswith(("control/", "out/", "qc/", "manifest/")) or rel == "README.md" else "SUPPORTING"
    index_lines.append(f"| `{rel}` | {role_for(path)} | {line_count(path)} | {path.stat().st_size} | `{sha256_file(path)}` | {authority} |")
index_lines.extend(["", "Scientific disposition: `NOT_ASSIGNED`. No real species or real Q1 output is present.", ""])
index_path.write_text("\n".join(index_lines), encoding="utf-8")
shutil.copyfile(index_path, EXT_INDEX)

deterministic_zip(ZIP)
zip_sha = sha256_file(ZIP)
SIDECAR.write_text(f"{zip_sha}  {ZIP.name}\n", encoding="utf-8")
with tempfile.TemporaryDirectory(dir=ROOT / "99_tmp" / "d10e") as temp_dir:
    repeat_zip = Path(temp_dir) / "repeat.zip"
    deterministic_zip(repeat_zip)
    repeat_sha = sha256_file(repeat_zip)

members, zip_failures = verify_zip(ZIP)
manifest_failures = verify_internal_sha()
sidecar_ok = SIDECAR.read_text(encoding="utf-8").strip() == f"{zip_sha}  {ZIP.name}"
deterministic_ok = repeat_sha == zip_sha
independent = json.loads((QC / "independent_validation_v01.json").read_text(encoding="utf-8"))
xlsx = json.loads((QC / "xlsx_validation_v01.json").read_text(encoding="utf-8"))
build = json.loads((QC / "build_summary_v01.json").read_text(encoding="utf-8"))
xlsx_gates_ok = xlsx.get("status") == "PASS" and all(xlsx.get("gates", {}).values())
max_member_chars = max(len(row["member"]) for row in members)
path_candidates = list(PKG.rglob("*")) + [ZIP, SIDECAR, EXT_INDEX, EXT_VALIDATION, TRANSFER]
max_abs_chars = max(len(str(path.resolve())) for path in path_candidates)
post_ok = all((
    not zip_failures,
    not manifest_failures,
    sidecar_ok,
    deterministic_ok,
    independent.get("status") == "PASS" and independent.get("checks_passed") == independent.get("checks_total") == 30,
    xlsx_gates_ok,
    build.get("terminal_status") == TERMINAL,
    max_abs_chars < 256,
    max_member_chars < 256,
))
post_status = "PASS" if post_ok else "FAIL"
post = {
    "task_id": "D10E_POSITIVE_OPPORTUNITY_ABUNDANCE_MEASUREMENT_NOISE_DECOMPOSITION_v01",
    "terminal_status": TERMINAL,
    "postpackage_validation_status": post_status,
    "scientific_disposition": "NOT_ASSIGNED",
    "zip_path": str(ZIP),
    "zip_size_bytes": ZIP.stat().st_size,
    "zip_sha256": zip_sha,
    "zip_member_count": len(members),
    "zip_member_set_crc_and_hashes_match_disk": not zip_failures,
    "zip_failures": zip_failures,
    "internal_sha256_manifest_status": "PASS" if not manifest_failures else "FAIL",
    "internal_sha256_manifest_failures": manifest_failures,
    "deterministic_repeat_sha256": repeat_sha,
    "deterministic_repeat_match": deterministic_ok,
    "sidecar_exact": sidecar_ok,
    "independent_validation_status": independent.get("status"),
    "independent_checks": f"{independent.get('checks_passed')}/{independent.get('checks_total')}",
    "xlsx_validation_status": xlsx.get("status"),
    "xlsx_all_gates_pass": xlsx_gates_ok,
    "max_absolute_path_chars": max_abs_chars,
    "max_zip_member_path_chars": max_member_chars,
    "windows_path_limit_check": "PASS" if max_abs_chars < 256 and max_member_chars < 256 else "FAIL",
    "boundary": "Synthetic measurement-noise diagnostic only; no scientific disposition, estimator modification, new uncertainty model, support recovery, real World 0, or real Q1.",
}
EXT_VALIDATION.write_text(json.dumps(post, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

transfer_rows: list[dict[str, object]] = []


def add_transfer(path: Path, relative: str, role: str, target: str, required_flag: str, priority: str, notes: str) -> None:
    transfer_rows.append({
        "local_path": str(path.resolve()),
        "relative_path": relative,
        "role": role,
        "upload_target": target,
        "required": required_flag,
        "mainline_priority": priority,
        "size_bytes": path.stat().st_size,
        "sha256": sha256_file(path),
        "notes": notes,
    })


add_transfer(ZIP, ZIP.name, "reproducible_zip", "release", "YES", "FIRST_READ", "Complete deterministic frozen package.")
add_transfer(SIDECAR, SIDECAR.name, "checksum", "mirror", "YES", "FIRST_READ", "Exact SHA-256 sidecar for the Release ZIP.")
add_transfer(EXT_INDEX, EXT_INDEX.name, "delivery_index", "mirror", "YES", "FIRST_READ", "Human-readable inventory with sizes and hashes.")
add_transfer(EXT_VALIDATION, EXT_VALIDATION.name, "qc_json", "mirror", "YES", "IMPORTANT", "Independent post-package integrity validation.")
for path in package_files():
    rel = path.relative_to(PKG).as_posix()
    suffixes = "".join(path.suffixes).lower()
    role = role_for(path)
    direct_text = path.suffix.lower() in {".csv", ".md", ".json", ".txt", ".ndjson", ".py", ".mjs", ".ps1"}
    target = "mirror" if direct_text else "release" if suffixes.endswith(".csv.gz") or path.suffix.lower() in {".xlsx", ".png"} else "local_only"
    required_flag = "YES" if role in {"result_note", "result_table", "workbook", "frozen_contract", "qc", "code", "checksum", "manifest", "delivery_index", "readme"} else "NO"
    priority = "FIRST_READ" if role in {"result_note", "delivery_index", "readme"} else "IMPORTANT" if role in {"workbook", "frozen_contract", "qc", "checksum", "manifest"} else "SUPPORTING" if role in {"result_table", "code"} else "ARCHIVE_ONLY"
    add_transfer(path, f"release_mirror/{TRANSFER_NAME}/{rel}", role, target, required_flag, priority, "Frozen package member; preserve bytes and SHA-256.")

fields = ["local_path", "relative_path", "role", "upload_target", "required", "mainline_priority", "size_bytes", "sha256", "notes"]
write_csv(TRANSFER, transfer_rows, fields)
print(json.dumps({
    "status": post_status,
    "terminal_status": TERMINAL,
    "zip": str(ZIP),
    "zip_size_bytes": ZIP.stat().st_size,
    "zip_sha256": zip_sha,
    "zip_members": len(members),
    "transfer_manifest_rows": len(transfer_rows),
    "transfer_manifest_sha256": sha256_file(TRANSFER),
    "independent_checks": post["independent_checks"],
    "xlsx_all_gates_pass": xlsx_gates_ok,
    "max_absolute_path_chars": max_abs_chars,
    "max_zip_member_path_chars": max_member_chars,
}, indent=2), flush=True)
raise SystemExit(0 if post_status == "PASS" else 1)
