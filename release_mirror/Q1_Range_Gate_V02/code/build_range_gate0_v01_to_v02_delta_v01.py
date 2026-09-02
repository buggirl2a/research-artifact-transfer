#!/usr/bin/env python3
"""Post-freeze v01→v02 delta and v01 immutability audit."""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path


ROOT = Path(r"C:\range_paper")
WORK = ROOT / "99_tmp" / "range_gate0_v02_corrected"
OUT, QC = WORK / "outputs", WORK / "qc"
V02 = OUT / "Q1_RANGE_GATE0_V02_CORRECTED_SPECIES_CLASSIFICATION_v01.csv"
V01 = ROOT / "07_results" / "range_gate0_v01" / "Q1_RANGE_GATE0_SPECIES_CLASSIFICATION_v01.csv"
V02_FROZEN_SHA = "d0ff6281d3e5a8aa2cb1438fd70cc2650163b6c512ffe8299c24d3555ddfcb64"
V01_FROZEN_SHA = "243978406cb913c13898b333671000c30592079d076ef8b995822a1684f8a8cd"
V01_TREE_BASELINE = "a415cbc84b66f6d0bf01c4cfaab3449e9e49e872bed7464cf2d71a29f65e9100"
V01_ROOTS = [ROOT / "07_results" / "range_gate0_v01", ROOT / "05_qc" / "range_gate0_v01", ROOT / "10_archive" / "range_gate0_v01"]
V01_STATUS = "MAINLINE_CONTRACT_SEMANTICS_FAIL / COMPUTATIONAL_EXECUTION_PASS"


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""): h.update(block)
    return h.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f: return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
        writer.writeheader(); writer.writerows(rows)


def v01_snapshot() -> tuple[list[dict[str, object]], str]:
    rows = []
    digest_records = []
    for index, base in enumerate(V01_ROOTS, start=1):
        root_role = ["v01_results", "v01_qc", "v01_archive"][index - 1]
        # Match the case-insensitive path order used by the pre-frozen
        # PowerShell Sort-Object sentinel calculation.
        for path in sorted((p for p in base.rglob("*") if p.is_file()), key=lambda p: str(p).lower()):
            rel_legacy = path.relative_to(base.parent).as_posix()
            file_hash = sha(path)
            digest_records.append(f"{rel_legacy}|{path.stat().st_size}|{file_hash}")
            rows.append({"root_role": root_role, "local_path": str(path), "relative_path_within_root": path.relative_to(base).as_posix(), "size_bytes": path.stat().st_size, "sha256": file_hash})
    digest = hashlib.sha256((("\n".join(digest_records)) + "\n").encode("utf-8")).hexdigest()
    return rows, digest


def explanation(v01: dict[str, str], v02: dict[str, str]) -> tuple[str, str]:
    old, new = v01["range_gate0_class"], v02["range_gate0_v02_class"]
    outside = v02["confirmed_native_outside_North_America"]
    trans = v02["transcontinental_circumboreal_global_extension_flag"]
    if old == new:
        return "UNCHANGED_UNDER_CORRECTED_PRECEDENCE", "PASS"
    if old == "FAIL_EXTRA_NA" and new == "BORDERLINE_OTHER_NA" and outside == "FALSE" and trans == "TRUE":
        return "V01 transcontinental-only Class-1 authority removed; explicit frozen evidence is North-America-side other extension, so corrected Class 2 controls.", "PASS"
    if old == "BORDERLINE_SOUTH" and new == "BORDERLINE_OTHER_NA":
        return "Class 2 was renamed and broadened to the corrected frozen semantic label BORDERLINE_OTHER_NA; underlying frozen external evidence remains North-America-side.", "PASS"
    return "UNEXPECTED_CHANGE_NOT_EXPLAINED_BY_CORRECTED_SEMANTICS", "FAIL"


def main() -> int:
    if sha(V02) != V02_FROZEN_SHA: raise RuntimeError("Frozen v02 classification changed before delta construction")
    snapshot_rows, tree_digest = v01_snapshot()
    if tree_digest != V01_TREE_BASELINE: raise RuntimeError(f"v01 immutability failure before delta: {tree_digest}")
    if sha(V01) != V01_FROZEN_SHA: raise RuntimeError("v01 classification hash mismatch")
    write_csv(QC / "RANGE_GATE0_V01_IMMUTABILITY_SNAPSHOT_v01.csv", snapshot_rows, ["root_role", "local_path", "relative_path_within_root", "size_bytes", "sha256"])

    v01_rows, v02_rows = read_csv(V01), read_csv(V02)
    if len(v01_rows) != 312 or len(v02_rows) != 312: raise RuntimeError("Delta universe does not close at 312×312")
    old_by_id = {row["analysis_species_id"]: row for row in v01_rows}
    new_by_id = {row["analysis_species_id"]: row for row in v02_rows}
    if set(old_by_id) != set(new_by_id) or len(old_by_id) != 312: raise RuntimeError("v01/v02 delta ID sets differ")

    delta = []
    for sid in sorted(new_by_id, key=int):
        old, new = old_by_id[sid], new_by_id[sid]
        if old["analysis_species_name"] != new["analysis_species_name"]: raise RuntimeError(f"Name mismatch for {sid}")
        text, attribution = explanation(old, new)
        external = new["confirmed_native_outside_USA_Canada_level3_areas"] or "NONE"
        delta.append({
            "analysis_species_id": sid, "analysis_species_name": new["analysis_species_name"],
            "v01_scientific_status": V01_STATUS, "v01_class": old["range_gate0_class"], "v02_class": new["range_gate0_v02_class"],
            "v01_reason_code": old["range_gate0_reason_code"], "v02_reason_code": new["range_gate0_v02_reason_code"],
            "class_changed": "YES" if old["range_gate0_class"] != new["range_gate0_v02_class"] else "NO",
            "change_explanation": text, "semantic_attribution_status": attribution,
            "confirmed_native_outside_North_America": new["confirmed_native_outside_North_America"],
            "transcontinental_circumboreal_global_extension_flag": new["transcontinental_circumboreal_global_extension_flag"],
            "transcontinental_semantic_role_v02": new["transcontinental_semantic_role"],
            "relevant_frozen_level3_external_evidence": external,
            "frozen_outside_North_America_level3_evidence": new["confirmed_native_outside_North_America_level3_areas"] or "NONE",
            "frozen_other_NA_extension_level3_evidence": new["other_na_extension_level3_areas"] or "NONE",
            "v01_classification_sha256": V01_FROZEN_SHA, "v02_classification_sha256": V02_FROZEN_SHA,
        })
    fields = list(delta[0].keys())
    delta_path = OUT / "Q1_RANGE_GATE0_V01_TO_V02_CORRECTED_DELTA_AUDIT_v01.csv"
    write_csv(delta_path, delta, fields)
    transitions = Counter((row["v01_class"], row["v02_class"], row["class_changed"]) for row in delta)
    summary = [{"v01_class": old, "v02_class": new, "class_changed": changed, "species_count": count} for (old, new, changed), count in sorted(transitions.items())]
    write_csv(OUT / "Q1_RANGE_GATE0_V01_TO_V02_CORRECTED_DELTA_SUMMARY_v01.csv", summary, ["v01_class", "v02_class", "class_changed", "species_count"])

    changed = [row for row in delta if row["class_changed"] == "YES"]
    checks = []
    def add(cid, description, actual, expected, passed): checks.append({"check_id": cid, "description": description, "expected": expected, "actual": actual, "status": "PASS" if passed else "FAIL"})
    add("DQ001", "Frozen v02 classification hash unchanged before/after delta", sha(V02), V02_FROZEN_SHA, sha(V02) == V02_FROZEN_SHA)
    add("DQ002", "v01 classification hash matches immutable baseline", sha(V01), V01_FROZEN_SHA, sha(V01) == V01_FROZEN_SHA)
    add("DQ003", "v01 full-tree digest matches pre-v02 immutability sentinel", tree_digest, V01_TREE_BASELINE, tree_digest == V01_TREE_BASELINE)
    add("DQ004", "v01 immutable snapshot file count", len(snapshot_rows), 76, len(snapshot_rows) == 76)
    add("DQ005", "Both classifications contain 312 unique identical IDs", len(set(old_by_id) & set(new_by_id)), 312, len(old_by_id) == len(new_by_id) == len(set(old_by_id) & set(new_by_id)) == 312)
    add("DQ006", "Delta contains one row per species", len(delta), 312, len(delta) == 312)
    add("DQ007", "All names match between v01 and v02", sum(old_by_id[sid]["analysis_species_name"] == new_by_id[sid]["analysis_species_name"] for sid in new_by_id), 312, all(old_by_id[sid]["analysis_species_name"] == new_by_id[sid]["analysis_species_name"] for sid in new_by_id))
    add("DQ008", "Every changed row is attributable only to corrected semantics", sum(row["semantic_attribution_status"] == "PASS" for row in changed), len(changed), all(row["semantic_attribution_status"] == "PASS" for row in changed))
    old_fail_moves = [row for row in changed if row["v01_class"] == "FAIL_EXTRA_NA"]
    add("DQ009", "Every v01 FAIL move has outside-NA FALSE and transcontinental TRUE", sum(row["confirmed_native_outside_North_America"] == "FALSE" and row["transcontinental_circumboreal_global_extension_flag"] == "TRUE" for row in old_fail_moves), len(old_fail_moves), all(row["confirmed_native_outside_North_America"] == "FALSE" and row["transcontinental_circumboreal_global_extension_flag"] == "TRUE" for row in old_fail_moves))
    add("DQ010", "No v02 FAIL has outside-NA FALSE", sum(row["v02_class"] == "FAIL_EXTRA_NA" and row["confirmed_native_outside_North_America"] == "FALSE" for row in delta), 0, not any(row["v02_class"] == "FAIL_EXTRA_NA" and row["confirmed_native_outside_North_America"] == "FALSE" for row in delta))
    add("DQ011", "Every v01 BORDERLINE_SOUTH row maps to corrected BORDERLINE_OTHER_NA", sum(row["v01_class"] == "BORDERLINE_SOUTH" and row["v02_class"] == "BORDERLINE_OTHER_NA" for row in delta), sum(row["v01_class"] == "BORDERLINE_SOUTH" for row in delta), all(row["v02_class"] == "BORDERLINE_OTHER_NA" for row in delta if row["v01_class"] == "BORDERLINE_SOUTH"))
    add("DQ012", "v01 status label present on all delta rows", sum(row["v01_scientific_status"] == V01_STATUS for row in delta), 312, all(row["v01_scientific_status"] == V01_STATUS for row in delta))
    add("DQ013", "Delta was computed only after v02 scientific freeze note exists", (ROOT / "00_control" / "RANGE_GATE0_V02_CORRECTED_SCIENTIFIC_OUTPUT_FREEZE_v01.md").is_file(), True, (ROOT / "00_control" / "RANGE_GATE0_V02_CORRECTED_SCIENTIFIC_OUTPUT_FREEZE_v01.md").is_file())
    add("DQ014", "No v01 file was written", "READ_ONLY", "READ_ONLY", tree_digest == V01_TREE_BASELINE)
    add("DQ015", "Transition summary totals 312", sum(int(row["species_count"]) for row in summary), 312, sum(int(row["species_count"]) for row in summary) == 312)
    write_csv(QC / "Q1_RANGE_GATE0_V01_TO_V02_DELTA_QC_v01.csv", checks, ["check_id", "description", "expected", "actual", "status"])
    immutability = {"status": "PASS" if tree_digest == V01_TREE_BASELINE else "FAIL", "v01_scientific_status": V01_STATUS, "baseline_tree_digest": V01_TREE_BASELINE, "observed_tree_digest": tree_digest, "file_records": len(snapshot_rows), "v01_zip_sha256": "ec99bf40ca5a22ae856ec8228b053fedf959af64675fc1cc5d99b4827fb0aafd", "v01_classification_sha256": sha(V01), "v01_files_modified": False}
    (QC / "RANGE_GATE0_V01_IMMUTABILITY_AUDIT_v01.json").write_text(json.dumps(immutability, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if not all(row["status"] == "PASS" for row in checks): raise RuntimeError("SCIENTIFIC_CONTRACT_REGRESSION_FAIL: delta audit failed")

    v02_summary = read_csv(OUT / "Q1_RANGE_GATE0_V02_CORRECTED_SUMMARY_v01.csv")
    note = [
        "# Range Gate 0 v02 corrected result note", "", "- Execution: **PASS**.",
        "- Scientific correction: `transcontinental_circumboreal_global_extension_flag` is diagnostic-only and has zero independent routing authority.",
        "- Frozen input universe: 312/312 accepted species with `confirmed_native_CONUS == TRUE` from the unchanged 361-species D08B1 v02 master.",
        "- v01 status retained: `MAINLINE_CONTRACT_SEMANTICS_FAIL / COMPUTATIONAL_EXECUTION_PASS`.", "", "## v02 corrected class counts", "",
        "| Class | Species | Percent of 312 | Route |", "|---|---:|---:|---|",
    ]
    for row in v02_summary: note.append(f"| {row['class']} | {row['species_count']} | {row['percent_of_312']}% | {row['downstream_route']} |")
    note.extend(["", "## v01→v02 delta", "", f"- Changed classifications: {len(changed)}."])
    for row in summary:
        if row["class_changed"] == "YES": note.append(f"- `{row['v01_class']}` → `{row['v02_class']}`: {row['species_count']} species.")
    note.extend(["", "## Boundary", "", "No class count was targeted. No v01 row was edited. No WCVP unit count was treated as area/share/severity; no geometry, Little decision, external search, D08C2, FIA outcome/eligibility, support/detection, abundance, final cohort, or real Q1 was used.", "", "STOP: return to scientific mainline for audit.", ""])
    (OUT / "RANGE_GATE0_V02_CORRECTED_RESULT_NOTE_v01.md").write_text("\n".join(note), encoding="utf-8")
    print(json.dumps({"status": "PASS", "delta_rows": len(delta), "changed_rows": len(changed), "transitions": {f"{a}->{b}": c for (a, b, changed_flag), c in transitions.items() if changed_flag == "YES"}, "v01_tree_digest": tree_digest, "qc": f"{len(checks)}/{len(checks)}"}))
    return 0


if __name__ == "__main__": raise SystemExit(main())
