#!/usr/bin/env python3
"""Verify the v02 corrected audit workbook without editing it."""

import json
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(r"C:\range_paper")
WORK = ROOT / "99_tmp" / "range_gate0_v02_corrected"
BOOK = WORK / "outputs" / "Q1_RANGE_GATE0_V02_CORRECTED_MAINLINE_AUDIT_v01.xlsx"
QC = WORK / "qc"
EXPECTED = ["Summary", "Classification", "Class Summary", "Decision Queue", "Fail Extra NA", "Delta Audit", "Delta Summary", "Build QC", "Delta QC", "Input Hash Audit", "v01 Immutability", "Semantic Fixtures"]


def main() -> int:
    checks = []
    def add(name, passed, actual, expected): checks.append({"check": name, "status": "PASS" if passed else "FAIL", "actual": actual, "expected": expected})
    add("workbook_exists", BOOK.is_file(), str(BOOK), "existing file")
    add("workbook_nonempty", BOOK.stat().st_size > 10000, BOOK.stat().st_size, ">10000")
    with zipfile.ZipFile(BOOK, "r") as zf:
        add("xlsx_zip_integrity", zf.testzip() is None, zf.testzip(), None)
        root = ET.fromstring(zf.read("xl/workbook.xml")); ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
        names = [node.attrib["name"] for node in root.findall("m:sheets/m:sheet", ns)]
        add("sheet_names_and_order", names == EXPECTED, names, EXPECTED)
        members = [name for name in zf.namelist() if name.startswith("xl/worksheets/sheet") and name.endswith(".xml")]
        add("worksheet_member_count", len(members) == 12, len(members), 12)
    formula_scan = (QC / "RANGE_GATE0_V02_WORKBOOK_FORMULA_ERROR_SCAN_v01.ndjson").read_text(encoding="utf-8")
    add("formula_error_scan_zero", "matched 0 entries" in formula_scan, formula_scan.strip(), "matched 0 entries")
    summary = (QC / "RANGE_GATE0_V02_WORKBOOK_SUMMARY_INSPECT_v01.ndjson").read_text(encoding="utf-8")
    fixtures = (QC / "RANGE_GATE0_V02_WORKBOOK_FIXTURES_INSPECT_v01.ndjson").read_text(encoding="utf-8")
    add("summary_cached_execution_pass", '\"Execution\",\"PASS\"' in summary, "PASS" if '\"Execution\",\"PASS\"' in summary else "MISSING", "PASS")
    add("summary_cached_input_closure", '\"312/312\"' in summary, "312/312" in summary, True)
    add("fixture_sheet_contains_all_named_cases", all(name in fixtures for name in ["Magnolia virginiana", "Ostrya virginiana", "Quercus rugosa", "Sorbus decora", "Pinus banksiana", "Populus balsamifera", "Pinus balfouriana"]), sum(name in fixtures for name in ["Magnolia virginiana", "Ostrya virginiana", "Quercus rugosa", "Sorbus decora", "Pinus banksiana", "Populus balsamifera", "Pinus balfouriana"]), 7)
    index = json.loads((QC / "RANGE_GATE0_V02_WORKBOOK_RENDER_INDEX_v01.json").read_text(encoding="utf-8"))
    add("all_sheets_rendered", [item["sheet_name"] for item in index] == EXPECTED, [item["sheet_name"] for item in index], EXPECTED)
    previews = [Path(item["preview_path"]) for item in index]
    add("all_previews_nonempty", all(path.is_file() and path.stat().st_size > 0 for path in previews), sum(path.is_file() and path.stat().st_size > 0 for path in previews), 12)
    status = "PASS" if all(row["status"] == "PASS" for row in checks) else "FAIL"
    output = {"status": status, "workbook": str(BOOK), "check_count": len(checks), "pass_count": sum(row["status"] == "PASS" for row in checks), "checks": checks}
    target = QC / "RANGE_GATE0_V02_CORRECTED_WORKBOOK_VALIDATION_v01.json"
    target.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": status, "checks": len(checks), "pass": output["pass_count"], "validation": str(target)}))
    return 0 if status == "PASS" else 1


if __name__ == "__main__": raise SystemExit(main())
