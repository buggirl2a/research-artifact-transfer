from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import shutil
import zipfile
from pathlib import Path


ROOT = Path(r"C:\range_paper")
ARCHIVE = ROOT / "10_archive" / "d10cr"
PKG = ARCHIVE / "pkg"
SRC = ROOT / "06_src" / "d10cr"
ZIP_PATH = ARCHIVE / "D10CR_v01.zip"
TRANSFER_NAME = "Q1-D10CR-v01-20260905"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def row_count(path: Path):
    if path.name.endswith(".csv.gz"):
        import gzip
        with gzip.open(path, "rt", encoding="utf-8-sig", newline="") as handle:
            return max(0, sum(1 for _ in handle) - 1)
    if path.suffix.lower() == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            return max(0, sum(1 for _ in handle) - 1)
    if path.suffix.lower() in {".md", ".txt", ".json", ".py", ".mjs", ".ps1", ".ndjson"}:
        with path.open("r", encoding="utf-8-sig", errors="replace") as handle:
            return sum(1 for _ in handle)
    return ""


def role_for(rel: str) -> str:
    name = Path(rel).name.lower()
    if name == "result_note_v01.md": return "result_note"
    if name == "contract_v01.md": return "frozen_contract"
    if name == "audit_v01.xlsx": return "workbook"
    if name.endswith(".py") or name.endswith(".mjs") or name.endswith(".ps1"): return "source"
    if "validation" in name or "checks" in name or rel.startswith("qc/"): return "qc"
    if "sha256" in name: return "checksum"
    if "registry" in name or "delivery_index" in name: return "manifest"
    if name.endswith(".csv") or name.endswith(".csv.gz"): return "audit_csv"
    if name.endswith(".png"): return "figure"
    return "other"


def purpose_for(rel: str) -> str:
    mapping = {
        "out/truth_v01.csv": "Frozen latent abundance truth A0 basis",
        "out/a0_v01.csv": "A0 latent-truth abundance layer",
        "out/a1_v01.csv": "Exact broken D10A raw-count reference",
        "out/a2_v01.csv.gz": "Frozen D10C-A design-estimator cell masses",
        "out/plot_obs_v01.csv.gz": "Sparse nonzero synthetic FIA-style plot observations",
        "out/cell_recovery_v01.csv.gz": "Full cell-level A1/A2 recovery audit",
        "out/recovery_metrics_v01.csv": "Species-level recovery metrics",
        "out/map_recovery_v01.csv": "Normalized-map recovery table",
        "out/leakage_v01.csv.gz": "Sampling-intensity leakage diagnostics",
        "out/downstream_v01.csv": "Oracle-support downstream comparison",
        "out/separation_v01.csv": "STRONG versus PAIRED_NULL results",
        "out/orientation_v01.csv": "AB versus BA consistency audit",
        "out/common_compare_v01.csv": "D10B L0/L1 versus D10C A2 common comparison",
        "out/result_note_v01.md": "Mainline result note answering Q1-Q8",
        "out/audit_v01.xlsx": "Human-readable audit workbook",
        "control/contract_v01.md": "Frozen pre-run experiment contract",
        "qc/input_id_v01.csv": "Frozen input identity audit",
        "qc/validation_v01.json": "Deterministic independent validation report",
        "manifest/sha256sums_v01.csv": "Internal member checksums",
        "manifest/registry_delta_v01.csv": "Proposed mainline registry delta",
    }
    return mapping.get(rel, role_for(rel).replace("_", " ").title())


def load_verify_module():
    spec = importlib.util.spec_from_file_location("d10cr_verify", SRC / "verify.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def write_readme():
    text = """# D10C resume reproducible package v01

Terminal execution status: `ABUNDANCE_CALIBRATION_COMPLETE_READY_FOR_MAINLINE_FREEZE`.

This package contains a bounded, synthetic, oracle-support abundance-measurement calibration. It preserves the frozen D10A/D10B/D09C/D10C-A identities and compares A0 latent truth, the exact broken A1 diagnostic layer, and the sole authorized A2 FIA design estimator.

Start with `out/result_note_v01.md`, `out/audit_v01.xlsx`, and `qc/validation_v01.json`. Scientific audit tables are in `out/`; source and runners are in `src/`; identities and deterministic checks are in `qc/` and `manifest/`.

No real species, support recovery, real World 0, estimator selection, or real Q1 analysis was run. This computational branch assigns no scientific PASS/HOLD/FAIL.
"""
    (PKG / "README.md").write_text(text, encoding="utf-8")


def update_registry():
    path = PKG / "manifest" / "registry_delta_v01.csv"
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
        fields = list(rows[0].keys())
    for row in rows:
        row["SHA256"] = "SEE_D10CR_v01.zip.sha256"
        row["SIZE_BYTES"] = "SEE_D10CR_v01.zip.sha256"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def inventory(exclude=()):
    excluded = {Path(x).as_posix() for x in exclude}
    files = []
    for path in sorted((p for p in PKG.rglob("*") if p.is_file()), key=lambda p: p.relative_to(PKG).as_posix()):
        rel = path.relative_to(PKG).as_posix()
        if rel in excluded:
            continue
        files.append({
            "relative_path": rel,
            "role": role_for(rel),
            "purpose": purpose_for(rel),
            "rows_or_lines": row_count(path),
            "size_bytes": path.stat().st_size,
            "sha256": sha256(path),
        })
    return files


def write_internal_index(items):
    lines = [
        "# D10C resume delivery index v01",
        "",
        "Terminal status: `ABUNDANCE_CALIBRATION_COMPLETE_READY_FOR_MAINLINE_FREEZE`.",
        "",
        "This index describes the pre-checksum package contents. Final member identities are authoritative in `sha256sums_v01.csv`.",
        "",
        "| Member | Role | Purpose | Rows/lines | Bytes | SHA-256 |",
        "|---|---|---|---:|---:|---|",
    ]
    for item in items:
        lines.append(f"| `{item['relative_path']}` | {item['role']} | {item['purpose']} | {item['rows_or_lines']} | {item['size_bytes']} | `{item['sha256']}` |")
    lines += ["", "No scientific PASS/HOLD/FAIL is assigned by this package.", ""]
    (PKG / "manifest" / "delivery_index_v01.md").write_text("\n".join(lines), encoding="utf-8")


def write_hash_manifest():
    path = PKG / "manifest" / "sha256sums_v01.csv"
    items = inventory(exclude=["manifest/sha256sums_v01.csv"])
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["relative_path", "size_bytes", "sha256"], lineterminator="\n")
        writer.writeheader()
        for item in items:
            writer.writerow({k: item[k] for k in ["relative_path", "size_bytes", "sha256"]})


def build_zip():
    with zipfile.ZipFile(ZIP_PATH, "w") as zf:
        for path in sorted((p for p in PKG.rglob("*") if p.is_file()), key=lambda p: p.relative_to(PKG).as_posix()):
            rel = path.relative_to(PKG).as_posix()
            info = zipfile.ZipInfo(rel, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            zf.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    digest = sha256(ZIP_PATH)
    Path(str(ZIP_PATH) + ".sha256").write_text(f"{digest}  {ZIP_PATH.name}\n", encoding="utf-8")
    return digest


def write_external_index(zip_digest, post):
    items = inventory()
    lines = [
        "# D10C resume external delivery index v01",
        "",
        f"- ZIP: `{ZIP_PATH}`",
        f"- ZIP bytes: {ZIP_PATH.stat().st_size}",
        f"- ZIP SHA-256: `{zip_digest}`",
        f"- Members: {len(items)}",
        f"- Postpackage validation: `{post['postpackage']['status']}`",
        f"- Maximum local absolute path: {post['package_path_qc']['max_abs_chars']} characters",
        f"- Maximum ZIP member path: {post['postpackage']['max_zip_member_chars']} characters",
        "",
        "| ZIP member | Role | Purpose | Rows/lines | Bytes | SHA-256 |",
        "|---|---|---|---:|---:|---|",
    ]
    for item in items:
        lines.append(f"| `{item['relative_path']}` | {item['role']} | {item['purpose']} | {item['rows_or_lines']} | {item['size_bytes']} | `{item['sha256']}` |")
    lines += ["", "Scientific tables remain outcome-blind synthetic calibration evidence. Mainline alone determines scientific disposition.", ""]
    (ARCHIVE / "delivery_index_v01.md").write_text("\n".join(lines), encoding="utf-8")


def classify_transfer(path: Path, rel: str):
    name = path.name.lower()
    if path == ZIP_PATH:
        return "reproducible_zip", "release", "YES", "IMPORTANT", "Complete immutable D10C resume package"
    if name.endswith(".zip.sha256"):
        return "checksum", "both", "YES", "IMPORTANT", "ZIP identity sidecar"
    if name == "delivery_index_v01.md" and path.parent == ARCHIVE:
        return "delivery_index", "mirror", "YES", "FIRST_READ", "External package index"
    if name == "validation_v01.json" and path.parent == ARCHIVE:
        return "qc_json", "mirror", "YES", "IMPORTANT", "Independent postpackage validation"
    if name == "audit_v01.xlsx":
        return "workbook", "release", "YES", "IMPORTANT", "Human-readable audit workbook; authoritative values remain CSV"
    if name.endswith(".csv.gz"):
        return "audit_csv", "local_only", "NO", "ARCHIVE_ONLY", "Contained in required reproducible ZIP"
    role = role_for(rel)
    priority = "FIRST_READ" if name in {"readme.md", "result_note_v01.md", "contract_v01.md"} else "IMPORTANT" if name in {"common_compare_v01.csv", "recovery_summary_v01.csv", "validation_v01.json", "input_id_v01.csv", "sha256sums_v01.csv"} else "SUPPORTING"
    required = "YES" if priority in {"FIRST_READ", "IMPORTANT"} else "NO"
    return role, "mirror", required, priority, "Loose audit mirror; byte-identical to packaged file"


def write_transfer_manifest():
    manifest = ARCHIVE / "transfer_manifest_v01.csv"
    external = [ZIP_PATH, Path(str(ZIP_PATH) + ".sha256"), ARCHIVE / "delivery_index_v01.md", ARCHIVE / "validation_v01.json"]
    candidates = [(p, p.name) for p in external]
    candidates += [(p, p.relative_to(PKG).as_posix()) for p in sorted((q for q in PKG.rglob("*") if q.is_file()), key=lambda q: q.relative_to(PKG).as_posix())]
    rows = []
    for path, rel in candidates:
        role, target, required, priority, notes = classify_transfer(path, rel)
        if path == ZIP_PATH or path.name.endswith(".zip.sha256") or (path.parent == ARCHIVE):
            relative = f"release_assets/{path.name}" if target in {"release", "both"} and path.parent == ARCHIVE and path.suffix != ".md" and path.suffix != ".json" else f"release_mirror/{TRANSFER_NAME}/{path.name}"
        elif target == "release":
            relative = f"release_assets/{path.name}"
        else:
            relative = f"release_mirror/{TRANSFER_NAME}/{rel}"
        rows.append({
            "local_path": str(path.resolve()),
            "relative_path": relative,
            "role": role,
            "upload_target": target,
            "required": required,
            "mainline_priority": priority,
            "size_bytes": path.stat().st_size,
            "sha256": sha256(path),
            "notes": notes,
        })
    with manifest.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["local_path", "relative_path", "role", "upload_target", "required", "mainline_priority", "size_bytes", "sha256", "notes"], lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    return len(rows), sha256(manifest)


def main():
    (PKG / "src").mkdir(parents=True, exist_ok=True)
    for name in ["build.py", "audit.mjs", "verify_xlsx.mjs", "finalize.py", "verify.py", "run_all.ps1"]:
        shutil.copyfile(SRC / name, PKG / "src" / name)
    write_readme()
    update_registry()

    verifier = load_verify_module()
    pre = verifier.validate_package(PKG.resolve())
    if pre["validation_status"] != "PASS":
        raise RuntimeError(json.dumps(pre, indent=2, ensure_ascii=False))
    (PKG / "qc" / "validation_v01.json").write_text(json.dumps(pre, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    write_internal_index(inventory(exclude=["manifest/delivery_index_v01.md", "manifest/sha256sums_v01.csv"]))
    write_hash_manifest()
    zip_digest = build_zip()

    post = verifier.validate_package(PKG.resolve())
    post["postpackage"] = verifier.validate_zip(ZIP_PATH.resolve(), post)
    files = [p for p in PKG.rglob("*") if p.is_file()]
    max_abs = max((len(str(p.resolve())), str(p.resolve())) for p in files)
    max_member = max((len(p.relative_to(PKG).as_posix()), p.relative_to(PKG).as_posix()) for p in files)
    post["package_path_qc"] = {"status": "PASS" if max_abs[0] < 256 and max_member[0] < 256 else "FAIL", "max_abs_chars": max_abs[0], "max_abs_path": max_abs[1], "max_member_chars": max_member[0], "max_member": max_member[1], "limit": 256}
    if post["validation_status"] != "PASS" or post["postpackage"]["status"] != "PASS" or post["package_path_qc"]["status"] != "PASS":
        raise RuntimeError(json.dumps(post, indent=2, ensure_ascii=False))
    (ARCHIVE / "validation_v01.json").write_text(json.dumps(post, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_external_index(zip_digest, post)
    transfer_rows, transfer_sha = write_transfer_manifest()

    summary = {
        "terminal_status": "ABUNDANCE_CALIBRATION_COMPLETE_READY_FOR_MAINLINE_FREEZE",
        "zip": str(ZIP_PATH),
        "zip_bytes": ZIP_PATH.stat().st_size,
        "zip_sha256": zip_digest,
        "members": post["postpackage"]["member_count"],
        "validation": post["postpackage"]["status"],
        "max_abs_path_chars": post["package_path_qc"]["max_abs_chars"],
        "max_zip_member_chars": post["postpackage"]["max_zip_member_chars"],
        "transfer_manifest_rows": transfer_rows,
        "transfer_manifest_sha256": transfer_sha,
    }
    (ARCHIVE / "finalize_summary_v01.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
