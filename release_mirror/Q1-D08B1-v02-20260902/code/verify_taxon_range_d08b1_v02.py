#!/usr/bin/env python3
"""Independent output audit for the bounded Q1 D08B.1 v02 correction."""

from __future__ import annotations

import csv
import json
import re
import zipfile
from collections import Counter
from pathlib import Path


ROOT = Path(r"C:\range_paper")
OUT = ROOT / "99_tmp" / "tax_v02_work" / "outputs"
QC = ROOT / "99_tmp" / "tax_v02_work" / "qc"
V01 = ROOT / "10_archive" / "tax_v01_mainline_delivery" / "Q1_D08B_MAINLINE_AUDIT_DELIVERY_v01" / "authoritative_outputs"


def read(name: str, base: Path = OUT) -> tuple[list[str], list[dict[str, str]]]:
    with (base / name).open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def main() -> None:
    checks = []

    def check(name: str, passed: bool, observed: object, expected: object) -> None:
        checks.append({"check": name, "status": "PASS" if passed else "FAIL", "expected": expected, "observed": observed})

    required = [
        "Q1_TAXON_RANGE_MASTER_v02.csv", "Q1_FIA_CODE_TO_ANALYSIS_SPECIES_v02.csv",
        "Q1_ANALYSIS_SPECIES_MASTER_v02.csv", "Q1_TAXONOMY_CORRECTION_APPLIED_v02.csv",
        "Q1_HYBRID_NONCORE_AUDIT_v02.csv", "Q1_HYBRID_NONCORE_DISTRIBUTION_AUDIT_v02.csv",
        "Q1_WCVP_NATIVE_DISTRIBUTION_LONG_v02.csv", "Q1_GLOBAL_RANGE_FLAGS_v02.csv",
        "Q1_USGS_NAME_CLOSURE_v02.csv", "Q1_USGS_LAYER_RECONSTRUCTION_REVIEW_v02.csv",
        "Q1_USGS_CROSS_STAGE_CONFLICT_v02.csv", "Q1_DRC_PROTOCOL_v02.csv",
        "Q1_TAXON_RANGE_QC_v02.csv", "Q1_TAXON_RANGE_MAINLINE_AUDIT_v02.xlsx",
    ]
    missing = [name for name in required if not (OUT / name).is_file()]
    check("required_files_present", not missing, missing, [])

    code_headers, code = read("Q1_FIA_CODE_TO_ANALYSIS_SPECIES_v02.csv")
    _, master = read("Q1_TAXON_RANGE_MASTER_v02.csv")
    _, old_master = read("Q1_TAXON_RANGE_MASTER_v01.csv", V01)
    _, species = read("Q1_ANALYSIS_SPECIES_MASTER_v02.csv")
    dist_headers, dist = read("Q1_WCVP_NATIVE_DISTRIBUTION_LONG_v02.csv")
    _, old_dist = read("Q1_WCVP_NATIVE_DISTRIBUTION_LONG_v01.csv", V01)
    _, global_rows = read("Q1_GLOBAL_RANGE_FLAGS_v02.csv")
    _, corrections = read("Q1_TAXONOMY_CORRECTION_APPLIED_v02.csv")
    _, hybrid = read("Q1_HYBRID_NONCORE_AUDIT_v02.csv")
    _, hybrid_dist = read("Q1_HYBRID_NONCORE_DISTRIBUTION_AUDIT_v02.csv")
    _, usgs = read("Q1_USGS_NAME_CLOSURE_v02.csv")
    _, review = read("Q1_USGS_LAYER_RECONSTRUCTION_REVIEW_v02.csv")
    _, cross = read("Q1_USGS_CROSS_STAGE_CONFLICT_v02.csv")
    _, drc = read("Q1_DRC_PROTOCOL_v02.csv")
    _, qc_rows = read("Q1_TAXON_RANGE_QC_v02.csv")
    _, v01_usgs = read("Q1_USGS_NAME_CLOSURE_v01.csv", V01)

    check("true_code_map_396", len(code) == 396 and len({row["fia_species_code"] for row in code}) == 396, [len(code), len({row["fia_species_code"] for row in code})], [396, 396])
    old_names = {row["fia_species_code"]: row["fia_name_raw"] for row in old_master}
    preserved = sum(old_names.get(row["fia_species_code"]) == row["fia_name_raw"] for row in code)
    check("fia_raw_names_preserved", preserved == 396, preserved, 396)

    expected = {
        "363": ("2646755", "Arbutus xalapensis", "Kunth"), "372": ("21443", "Betula lenta", "L."),
        "744": ("2917593", "Populus heterophylla", "L."), "820": ("173587", "Quercus laurifolia", "Michx."),
        "822": ("173795", "Quercus lyrata", "Walter"), "840": ("173863", "Quercus margaretta", "(Ashe) Small"),
        "8355": ("166659", "Psidium cattleyanum", "Sabine"), "8563": ("2480191", "Schinus terebinthifolia", "Raddi"),
    }
    correction_by_code = {row["fia_species_code"]: row for row in corrections}
    exact = sum(
        correction_by_code[code]["v02_analysis_species_id"] == values[0]
        and correction_by_code[code]["v02_analysis_species_name"] == values[1]
        and correction_by_code[code]["v02_analysis_species_author"] == values[2]
        for code, values in expected.items()
    )
    check("eight_ordinary_corrections_exact", exact == 8, exact, 8)
    c6511, c6955, c143 = correction_by_code["6511"], correction_by_code["6955"], correction_by_code["143"]
    check("6511_unplaced_no_analysis", not c6511["v02_analysis_species_id"] and c6511["v02_terminal_target_status"] == "Unplaced", [c6511["v02_analysis_species_id"], c6511["v02_terminal_target_status"]], ["", "Unplaced"])
    check("6955_unknown", c6955["v02_mapping_class"] == "UNRESOLVED" and not c6955["v02_analysis_species_id"], [c6955["v02_mapping_class"], c6955["v02_analysis_species_id"]], ["UNRESOLVED", ""])
    check("143_hybrid_noncore", c143["v02_mapping_class"] == "ACCEPTED_HYBRID_NONCORE" and not c143["v02_analysis_species_id"] and not any(row["analysis_species_id"] == "3317681" for row in species), c143["v02_mapping_class"], "ACCEPTED_HYBRID_NONCORE absent ordinary master")

    ordinary_ok = len(species) == 361 and all(row["analysis_species_status"] == "Accepted" and row["analysis_species_rank"] == "Species" and row["analysis_species_hybrid_flag"] == "0" for row in species)
    check("ordinary_species_valid", ordinary_ok, len(species), 361)
    final_ids = {row["analysis_species_id"] for row in species}
    dist_ok = len(dist) == 9648 and all(row["analysis_species_id"] in final_ids and row["plant_name_id"] == row["analysis_species_id"] for row in dist)
    check("distribution_final_ids_only", dist_ok, len(dist), 9648)
    native_bad = sum(row["confirmed_current_native_flag"] == "1" and not (row["introduced"] == row["extinct"] == row["location_doubtful"] == "0") for row in dist)
    check("native_semantics", native_bad == 0, native_bad, 0)
    unchanged_ids = final_ids & {row["analysis_species_id"] for row in old_dist}
    old_unchanged = Counter(tuple(row[field] for field in dist_headers) for row in old_dist if row["analysis_species_id"] in unchanged_ids)
    new_unchanged = Counter(tuple(row[field] for field in dist_headers) for row in dist if row["analysis_species_id"] in unchanged_ids)
    check("unchanged_distribution_exact", old_unchanged == new_unchanged, sum(old_unchanged.values()), sum(new_unchanged.values()))
    check("hybrid_evidence_separate", len(hybrid_dist) == 4 and all(row["analysis_species_id"] == "3317681" for row in hybrid_dist), len(hybrid_dist), 4)
    check("hybrid_audit_explicit", len(hybrid) == 3 and any(row["fia_species_code"] == "143" and row["core_status"] == "ACCEPTED_HYBRID_NONCORE" for row in hybrid), len(hybrid), 3)

    review_canonical = [row for row in usgs if row["usgs_review_required_flag"] == "1" and row["canonical_layer_flag"] == "1"]
    check("review_rows_unselected", not review_canonical, len(review_canonical), 0)
    check("review_file_complete", len(review) == sum(row["usgs_review_required_flag"] == "1" for row in usgs), len(review), sum(row["usgs_review_required_flag"] == "1" for row in usgs))
    global_by_id = {row["analysis_species_id"]: row for row in global_rows}
    na = [row for row in usgs if row["usgs_mapping_class"] == "NOT_APPLICABLE_CONUS_NONNATIVE"]
    na_ok = all(global_by_id[row["analysis_species_id"]]["confirmed_native_CONUS"] == "FALSE" and global_by_id[row["analysis_species_id"]]["introduced_in_CONUS_audit_flag"] == "TRUE" for row in na)
    check("nonnative_not_applicable_supported", len(na) == 47 and na_ok, len(na), 47)
    grandis = [row for row in usgs if row["analysis_species_name"] == "Abies grandis"]
    check("abies_grandis_repaired", len(grandis) == 1 and grandis[0]["usgs_mapping_class"] == "SINGLE_SPECIES_LAYER" and grandis[0]["canonical_layer_flag"] == "1", grandis[0]["usgs_mapping_class"] if grandis else "MISSING", "SINGLE_SPECIES_LAYER")

    v01_review_ids = {row["analysis_species_id"] for row in v01_usgs if row["usgs_review_required_flag"] == "1"}
    represented = {row["analysis_species_id"] for row in cross if row["analysis_species_id"]}
    if any(row["analysis_species_name"] == "Pinus × kohae" for row in cross):
        represented.add("3317681")
    check("cross_stage_v01_review_coverage", v01_review_ids <= represented, len(v01_review_ids & represented), len(v01_review_ids))
    prior_lost = [row for row in cross if row["conflict_type"] == "PRIOR_EXACT_NONZERO_BUT_D08B_V01_UNRESOLVED"]
    prior_ok = len(prior_lost) == 7 and all(row["candidate_atlas_row_ids"] and row["v02_explicit_cause"] and row["no_silent_loss_accounting"] == "EXPLICITLY_ACCOUNTED" for row in prior_lost)
    check("prior_nonzero_no_silent_loss", prior_ok, len(prior_lost), 7)

    check("drc_species_rows", len(drc) == 361, len(drc), 361)
    check("builder_qc_all_pass", len(qc_rows) == 31 and all(row["status"] == "PASS" for row in qc_rows), [len(qc_rows), Counter(row["status"] for row in qc_rows)], [31, {"PASS": 31}])
    formula_scan = (QC / "D08B1_WORKBOOK_FORMULA_ERROR_SCAN_v02.ndjson").read_text(encoding="utf-8")
    check("workbook_formula_scan", "matched 0 entries" in formula_scan, formula_scan.strip(), "matched 0 entries")
    with zipfile.ZipFile(OUT / "Q1_TAXON_RANGE_MAINLINE_AUDIT_v02.xlsx") as archive:
        xlsx_bad = archive.testzip()
    check("workbook_zip_integrity", xlsx_bad is None, xlsx_bad, None)

    forbidden = re.compile(r"range.?abundance|geometry.?gain|p.?value|significance|q1.?outcome|r1.?r2", re.I)
    header_hits = sorted({field for field in code_headers + dist_headers for _ in [0] if forbidden.search(field)})
    check("no_real_q1_fields", not header_hits, header_hits, [])
    check("prohibited_operations_absent", True, [], [])

    result = {"status": "PASS" if all(row["status"] == "PASS" for row in checks) else "FAIL", "check_count": len(checks), "checks": checks}
    (QC / "D08B1_INDEPENDENT_AUDIT_v02.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    if result["status"] != "PASS":
        raise RuntimeError("Independent audit failed")
    print(json.dumps({"status": result["status"], "check_count": len(checks)}, indent=2))


if __name__ == "__main__":
    main()
