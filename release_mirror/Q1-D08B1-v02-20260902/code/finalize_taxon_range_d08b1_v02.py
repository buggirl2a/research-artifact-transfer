#!/usr/bin/env python3
"""Freeze and package the already-built D08B1 v02 correction outputs.

This script does not recompute taxonomy, distribution, or USGS classifications.
It only copies the verified work products, writes delivery metadata, builds a
deterministic ZIP, and verifies the archive member hashes.
"""

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
WORK = ROOT / "99_tmp" / "tax_v02_work"
STAGE = ROOT / "99_tmp" / "tax_v02_release_stage"
DERIVED = ROOT / "04_derived" / "tax_v02"
QC_FINAL = ROOT / "05_qc" / "tax_v02"
ARCHIVE = ROOT / "10_archive" / "tax_v02"
PACKAGE = ARCHIVE / "package"
ZIP_NAME = "Q1_TAXON_RANGE_D08B1_CORRECTED_REPRODUCIBLE_v02.zip"
ZIP_PATH = ARCHIVE / ZIP_NAME
ZIP_ROOT = "Q1_TAXON_RANGE_D08B1_CORRECTED_REPRODUCIBLE_v02"
FIXED_ZIP_TIME = (2026, 9, 2, 0, 0, 0)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def csv_data_rows(path: Path) -> int | None:
    if path.suffix.lower() != ".csv":
        return None
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return max(sum(1 for _ in csv.reader(handle)) - 1, 0)


def text_lines(path: Path) -> int | None:
    if path.suffix.lower() not in {".md", ".json", ".txt", ".py", ".mjs", ".ndjson"}:
        return None
    with path.open("r", encoding="utf-8-sig") as handle:
        return sum(1 for _ in handle)


def copy_file(source: Path, target: Path) -> None:
    if not source.is_file():
        raise FileNotFoundError(source)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def copy_tree(source: Path, target: Path) -> None:
    if not source.is_dir():
        raise FileNotFoundError(source)
    shutil.copytree(source, target)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def file_purpose(relative: str) -> str:
    name = Path(relative).name
    exact = {
        "Q1_TAXON_RANGE_MASTER_v02.csv": "396-row FIA-code taxon–range master",
        "Q1_FIA_CODE_TO_ANALYSIS_SPECIES_v02.csv": "396-code original-name to accepted analysis-species bridge",
        "Q1_ANALYSIS_SPECIES_MASTER_v02.csv": "361-species accepted analysis-species master",
        "Q1_TAXONOMY_CORRECTION_APPLIED_v02.csv": "11-row incremental correction application ledger",
        "Q1_WCVP_NATIVE_DISTRIBUTION_LONG_v02.csv": "9,648-row WCVP Level-3 native/introduced evidence",
        "Q1_GLOBAL_RANGE_FLAGS_v02.csv": "species-level global-range flags",
        "Q1_USGS_NAME_CLOSURE_v02.csv": "USGS name/layer closure evidence",
        "Q1_USGS_LAYER_RECONSTRUCTION_REVIEW_v02.csv": "review-required USGS/Little reconstruction queue",
        "Q1_USGS_CROSS_STAGE_CONFLICT_v02.csv": "cross-stage USGS conflict and disposition audit",
        "Q1_DRC_PROTOCOL_v02.csv": "DRC retention and DBH-only sensitivity protocol",
        "Q1_HYBRID_NONCORE_AUDIT_v02.csv": "explicit hybrid/noncore code audit",
        "Q1_HYBRID_NONCORE_DISTRIBUTION_AUDIT_v02.csv": "audit-only hybrid distribution evidence",
        "Q1_TAXON_RANGE_UNRESOLVED_v02.csv": "ambiguous/unresolved decision queue",
        "Q1_TAXON_RANGE_EVIDENCE_v02.csv": "row-level provenance and decision evidence",
        "Q1_TAXON_RANGE_QC_v02.csv": "machine-readable build QC",
        "Q1_TAXON_RANGE_MAINLINE_AUDIT_v02.xlsx": "formatted mainline audit workbook",
        "D08B1_INDEPENDENT_AUDIT_v02.json": "independent post-build audit",
        "D08B1_INPUT_HASHES_v02.csv": "frozen-input hash ledger",
        "D08B1_BUILD_SUMMARY_v02.json": "build counts and status",
        "D08B1_PARAMETERS_v02.json": "frozen implementation parameters",
        "D08B1_ENVIRONMENT_v02.json": "runtime environment record",
        "D08B1_IMPLEMENTATION_LOG_v02.md": "implementation log",
        "D08B1_WORKBOOK_FORMULA_ERROR_SCAN_v02.ndjson": "workbook formula-error scan",
        "D08B1_WORKBOOK_RENDER_INDEX_v02.json": "workbook render index",
        "D08B1_WORKBOOK_SUMMARY_INSPECT_v02.ndjson": "workbook summary inspection",
        "D08B1_TAXONOMY_USGS_BRIDGE_CONTRACT_v02.md": "pre-run frozen contract and PASS/FAIL criteria",
        "D08B1_INPUT_FREEZE_v02.md": "D08B1 authoritative input freeze",
        "D08B1_CORRECTION_LOG_v02.md": "incremental correction log",
        "TAXON_RANGE_FREEZE_v02.md": "v02 output freeze declaration",
        "D08A_SOURCE_FREEZE_v02.md": "upstream D08A source freeze",
        "D08A_sha256_v02.txt": "upstream D08A hashes",
        "TAXON_RANGE_FREEZE_v01.md": "prior v01 freeze declaration",
        "README_PACKAGE.md": "reproduction and scope instructions",
    }
    if name in exact:
        return exact[name]
    if relative.startswith("inputs/new_authority/"):
        return "D08B1 mainline request/decision/correction authority input"
    if relative.startswith("inputs/frozen_v01_required/"):
        return "frozen v01 authoritative comparison input"
    if relative.startswith("inputs/frozen_v01_package/"):
        return "frozen v01 reproducible delivery package or checksum"
    if relative.startswith("inputs/frozen_atlas/"):
        return "frozen USGS Atlas G Table 1 source"
    if relative.startswith("inputs/frozen_eligibility/"):
        return "frozen eligibility-stage USGS audit input"
    if relative.startswith("code/"):
        return "reproducibility source code"
    if relative.startswith("qc/WORKBOOK_PREVIEWS_v02/"):
        return "rendered workbook visual-QA preview"
    if name == "README.md":
        return "output directory readme"
    return "supporting audit artifact"


def is_authoritative(relative: str) -> str:
    return "YES" if relative.startswith("outputs/") and relative.lower().endswith(".csv") else "NO"


def write_readme(stage: Path) -> None:
    write_text(
        stage / "README_PACKAGE.md",
        """# D08B1 corrected taxon–USGS bridge reproducible package v02

This is the frozen incremental correction delivery requested by the Q1 scientific mainline. It does **not** run D08C, merge FIA TREE records, merge Little layers, search for new extra-CONUS range data, select final Q1 species, or estimate any Q1 outcome.

## Authoritative outputs

The UTF-8 CSV files in `outputs/` are the authoritative v02 machine-readable products. The XLSX file is an audit view of the same products and is not independently authoritative. `D08B1_DELIVERY_INDEX.md`, `MANIFEST.json`, and `SHA256SUMS.csv` provide file-level provenance and integrity checks.

## Reproduction

1. Use Python 3 and Node.js with the bundled `artifact-tool` runtime recorded in `qc/D08B1_ENVIRONMENT_v02.json`.
2. Place the frozen external WCVP v16 archive at `C:/range_paper/02_raw/WCVP/wcvp.zip`; its required SHA-256 is recorded in `qc/D08B1_INPUT_HASHES_v02.csv` and `control/D08B1_INPUT_FREEZE_v02.md`.
3. Run `code/build_taxon_range_d08b1_v02.py` to regenerate CSV outputs from the frozen inputs.
4. Run `code/verify_taxon_range_d08b1_v02.py` for the independent audit.
5. Run `code/build_taxon_range_audit_xlsx_v02.mjs` to rebuild the audit workbook.
6. Compare every regenerated file to `SHA256SUMS.csv`.

The 88 MB WCVP archive is intentionally referenced by immutable SHA-256 rather than duplicated in this transfer package. All incremental mainline authorities, the frozen v01 comparison inputs, frozen Atlas source, and the eligibility USGS audit used by this correction are included.
""",
    )


def write_delivery_index(stage: Path) -> None:
    entries = []
    for path in sorted(p for p in stage.rglob("*") if p.is_file()):
        relative = path.relative_to(stage).as_posix()
        if relative in {"D08B1_DELIVERY_INDEX.md", "MANIFEST.json", "SHA256SUMS.csv"}:
            continue
        entries.append(
            {
                "file": relative,
                "purpose": file_purpose(relative),
                "rows": csv_data_rows(path),
                "lines": text_lines(path),
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
                "authoritative": is_authoritative(relative),
            }
        )

    lines = [
        "# D08B1 delivery index v02",
        "",
        "This index inventories every payload file present before the three self-referential package-control files are finalized. CSV `rows` exclude the header. `authoritative=YES` is restricted to the machine-readable v02 CSV outputs; the audit workbook and all provenance/QC artifacts are review aids.",
        "",
        f"Payload files indexed: **{len(entries)}**",
        "",
        "| File | Purpose | Rows | Lines | Bytes | SHA-256 | Authoritative |",
        "|---|---|---:|---:|---:|---|---|",
    ]
    for item in entries:
        rows = "" if item["rows"] is None else str(item["rows"])
        text_count = "" if item["lines"] is None else str(item["lines"])
        safe_purpose = item["purpose"].replace("|", "\\|")
        lines.append(
            f"| `{item['file']}` | {safe_purpose} | {rows} | {text_count} | {item['bytes']} | `{item['sha256']}` | {item['authoritative']} |"
        )
    lines.extend(
        [
            "",
            "## Package-control files",
            "",
            "`D08B1_DELIVERY_INDEX.md` (this file), `MANIFEST.json`, and `SHA256SUMS.csv` are finalized after payload enumeration. Their final hashes are included in `SHA256SUMS.csv` wherever non-self-referential; `SHA256SUMS.csv` necessarily omits its own hash.",
            "",
        ]
    )
    write_text(stage / "D08B1_DELIVERY_INDEX.md", "\n".join(lines))


def write_manifest(stage: Path) -> None:
    files = []
    for path in sorted(p for p in stage.rglob("*") if p.is_file()):
        relative = path.relative_to(stage).as_posix()
        if relative in {"MANIFEST.json", "SHA256SUMS.csv"}:
            continue
        files.append(
            {
                "path": relative,
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
                "authoritative": is_authoritative(relative) == "YES",
            }
        )
    manifest = {
        "package": ZIP_ROOT,
        "version": "v02",
        "scope": "D08B1 incremental taxonomy-USGS bridge correction",
        "created_utc": "2026-09-02T00:00:00Z",
        "payload_file_count": len(files),
        "files": files,
    }
    write_text(stage / "MANIFEST.json", json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")


def write_sha256s(stage: Path) -> None:
    rows = []
    for path in sorted(p for p in stage.rglob("*") if p.is_file()):
        relative = path.relative_to(stage).as_posix()
        if relative == "SHA256SUMS.csv":
            continue
        rows.append((relative, path.stat().st_size, sha256(path)))
    with (stage / "SHA256SUMS.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["relative_path", "bytes", "sha256"])
        writer.writerows(rows)


def verify_sha256s(stage: Path) -> None:
    with (stage / "SHA256SUMS.csv").open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        path = stage / row["relative_path"]
        if not path.is_file():
            raise RuntimeError(f"Missing package file: {row['relative_path']}")
        if path.stat().st_size != int(row["bytes"]):
            raise RuntimeError(f"Size mismatch: {row['relative_path']}")
        if sha256(path) != row["sha256"]:
            raise RuntimeError(f"Hash mismatch: {row['relative_path']}")


def deterministic_zip(package: Path, target: Path) -> int:
    member_count = 0
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(p for p in package.rglob("*") if p.is_file()):
            relative = path.relative_to(package).as_posix()
            info = zipfile.ZipInfo(f"{ZIP_ROOT}/{relative}", date_time=FIXED_ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = (0o100644 & 0xFFFF) << 16
            info.flag_bits |= 0x800
            archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
            member_count += 1
    return member_count


def verify_zip(package: Path, target: Path) -> int:
    expected = {
        f"{ZIP_ROOT}/{path.relative_to(package).as_posix()}": sha256(path)
        for path in package.rglob("*")
        if path.is_file()
    }
    with zipfile.ZipFile(target, "r") as archive:
        names = archive.namelist()
        if len(names) != len(expected) or set(names) != set(expected):
            raise RuntimeError("ZIP member set does not match frozen package")
        for name in names:
            if hashlib.sha256(archive.read(name)).hexdigest() != expected[name]:
                raise RuntimeError(f"ZIP member hash mismatch: {name}")
    return len(expected)


def main() -> None:
    for final_path in (DERIVED, QC_FINAL, ARCHIVE, STAGE):
        if final_path.exists():
            raise RuntimeError(f"Refusing to overwrite existing path: {final_path}")
    if not (WORK / "outputs").is_dir() or not (WORK / "qc").is_dir():
        raise RuntimeError("Verified work products are missing")

    stage = STAGE / "package"
    stage.mkdir(parents=True)

    copy_tree(WORK / "outputs", stage / "outputs")
    copy_tree(WORK / "qc", stage / "qc")

    source_dir = ROOT / "06_src" / "tax_v02"
    for name in (
        "build_taxon_range_d08b1_v02.py",
        "verify_taxon_range_d08b1_v02.py",
        "build_taxon_range_audit_xlsx_v02.mjs",
        "finalize_taxon_range_d08b1_v02.py",
    ):
        copy_file(source_dir / name, stage / "code" / name)

    control_dir = ROOT / "00_control"
    for name in (
        "D08B1_TAXONOMY_USGS_BRIDGE_CONTRACT_v02.md",
        "D08B1_INPUT_FREEZE_v02.md",
        "D08B1_CORRECTION_LOG_v02.md",
        "TAXON_RANGE_FREEZE_v02.md",
        "D08A_SOURCE_FREEZE_v02.md",
        "D08A_sha256_v02.txt",
        "TAXON_RANGE_FREEZE_v01.md",
    ):
        copy_file(control_dir / name, stage / "control" / name)

    copy_tree(
        ROOT / "03_doc" / "D08B1_TAXONOMY_CORRECTION_INPUTS_v02",
        stage / "inputs" / "new_authority",
    )

    v01_authority = (
        ROOT
        / "10_archive"
        / "tax_v01_mainline_delivery"
        / "Q1_D08B_MAINLINE_AUDIT_DELIVERY_v01"
        / "authoritative_outputs"
    )
    for name in (
        "Q1_TAXON_RANGE_MASTER_v01.csv",
        "Q1_TAXON_CODE_AGGREGATION_v01.csv",
        "Q1_WCVP_NATIVE_DISTRIBUTION_LONG_v01.csv",
        "Q1_GLOBAL_RANGE_FLAGS_v01.csv",
        "Q1_USGS_NAME_CLOSURE_v01.csv",
    ):
        copy_file(v01_authority / name, stage / "inputs" / "frozen_v01_required" / name)

    v01_delivery = ROOT / "10_archive" / "tax_v01_mainline_delivery"
    for name in (
        "Q1_D08B_MAINLINE_AUDIT_DELIVERY_v01.zip",
        "Q1_D08B_MAINLINE_AUDIT_DELIVERY_v01.zip.sha256",
        "DELIVERY_ARCHIVE_INDEX_v01.json",
    ):
        copy_file(v01_delivery / name, stage / "inputs" / "frozen_v01_package" / name)

    copy_file(
        ROOT / "03_doc" / "USGS" / "D08A_USGS_Atlas_G_Table1_20260902.html",
        stage / "inputs" / "frozen_atlas" / "D08A_USGS_Atlas_G_Table1_20260902.html",
    )
    for name in ("USGS_RANGE_AUDIT.csv",):
        copy_file(ROOT / "05_qc" / "elig_v02" / name, stage / "inputs" / "frozen_eligibility" / name)
    for name in ("PACKAGE_MANIFEST_SHA256.csv", "ZIP_SHA256.txt", "PACKAGE_VERIFICATION.json"):
        copy_file(ROOT / "10_archive" / "elig_v02" / name, stage / "inputs" / "frozen_eligibility" / name)

    write_readme(stage)
    write_delivery_index(stage)
    write_manifest(stage)
    write_sha256s(stage)
    verify_sha256s(stage)

    shutil.copytree(WORK / "outputs", DERIVED)
    shutil.copytree(WORK / "qc", QC_FINAL)
    ARCHIVE.mkdir(parents=True)
    shutil.copytree(stage, PACKAGE)

    member_count = deterministic_zip(PACKAGE, ZIP_PATH)
    verified_members = verify_zip(PACKAGE, ZIP_PATH)
    zip_hash = sha256(ZIP_PATH)
    write_text(ARCHIVE / f"{ZIP_NAME}.sha256", f"{zip_hash}  {ZIP_NAME}\n")
    copy_file(control_dir / "TAXON_RANGE_FREEZE_v02.md", ARCHIVE / "TAXON_RANGE_FREEZE_v02.md")

    archive_index = {
        "status": "PASS",
        "scope": "D08B1 incremental correction delivery only",
        "zip_name": ZIP_NAME,
        "zip_bytes": ZIP_PATH.stat().st_size,
        "zip_sha256": zip_hash,
        "zip_members": member_count,
        "verified_zip_members": verified_members,
        "authoritative_output_directory": str(DERIVED),
        "qc_directory": str(QC_FINAL),
        "package_directory": str(PACKAGE),
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "finalized_utc": datetime.now(timezone.utc).isoformat(),
        "prohibited_operations_performed": [],
    }
    write_text(ARCHIVE / "ARCHIVE_INDEX_v02.json", json.dumps(archive_index, indent=2) + "\n")

    shutil.rmtree(STAGE)
    print(json.dumps(archive_index, indent=2))


if __name__ == "__main__":
    main()
