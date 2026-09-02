#!/usr/bin/env python3
"""Verify the exported Range Gate 0 audit workbook without editing it."""

import json
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(r"C:\range_paper")
WORK = ROOT / "99_tmp" / "range_gate0_v01"
BOOK = WORK / "outputs" / "Q1_RANGE_GATE0_MAINLINE_AUDIT_v01.xlsx"
QC = WORK / "qc"
EXPECTED_SHEETS = ["Summary", "Classification", "Class Summary", "Decision Queue", "Fail Extra NA", "QC", "Input Hash Audit"]


def main() -> int:
    checks = []
    def add(name, passed, actual, expected):
        checks.append({"check": name, "status": "PASS" if passed else "FAIL", "actual": actual, "expected": expected})

    add("workbook_exists", BOOK.is_file(), str(BOOK), "existing file")
    add("workbook_nonempty", BOOK.stat().st_size > 10000, BOOK.stat().st_size, ">10000")
    with zipfile.ZipFile(BOOK, "r") as zf:
        bad = zf.testzip()
        add("xlsx_zip_integrity", bad is None, bad, None)
        root = ET.fromstring(zf.read("xl/workbook.xml"))
        ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
        sheets = [n.attrib["name"] for n in root.findall("m:sheets/m:sheet", ns)]
        add("sheet_names_and_order", sheets == EXPECTED_SHEETS, sheets, EXPECTED_SHEETS)
        worksheet_members = [n for n in zf.namelist() if n.startswith("xl/worksheets/sheet") and n.endswith(".xml")]
        add("worksheet_member_count", len(worksheet_members) == 7, len(worksheet_members), 7)
    formula_scan = (QC / "RANGE_GATE0_WORKBOOK_FORMULA_ERROR_SCAN_v01.ndjson").read_text(encoding="utf-8")
    add("formula_error_scan_zero", "matched 0 entries" in formula_scan, formula_scan.strip(), "matched 0 entries")
    inspect = (QC / "RANGE_GATE0_WORKBOOK_SUMMARY_INSPECT_v01.ndjson").read_text(encoding="utf-8")
    add("summary_cached_execution_pass", '"Execution","PASS"' in inspect, "PASS" if '"Execution","PASS"' in inspect else "MISSING", "PASS")
    add("summary_cached_input_312", '"312/312"' in inspect, "312/312" in inspect, True)
    render_index = json.loads((QC / "RANGE_GATE0_WORKBOOK_RENDER_INDEX_v01.json").read_text(encoding="utf-8"))
    add("all_sheets_rendered", [r["sheet_name"] for r in render_index] == EXPECTED_SHEETS, [r["sheet_name"] for r in render_index], EXPECTED_SHEETS)
    previews = [Path(r["preview_path"]) for r in render_index]
    add("all_previews_nonempty", all(p.is_file() and p.stat().st_size > 0 for p in previews), sum(p.is_file() and p.stat().st_size > 0 for p in previews), 7)
    status = "PASS" if all(c["status"] == "PASS" for c in checks) else "FAIL"
    output = {"status": status, "workbook": str(BOOK), "check_count": len(checks), "pass_count": sum(c["status"] == "PASS" for c in checks), "checks": checks}
    target = QC / "RANGE_GATE0_WORKBOOK_VALIDATION_v01.json"
    target.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": status, "checks": len(checks), "pass": output["pass_count"], "validation": str(target)}))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
