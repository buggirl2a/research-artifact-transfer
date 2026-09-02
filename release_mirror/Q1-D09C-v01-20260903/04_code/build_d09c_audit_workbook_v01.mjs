import fs from "node:fs/promises";
import fsSync from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const root = "C:/range_paper";
const work = `${root}/99_tmp/d09c_v01`;
const inputDir = `${work}/outputs`;
const qcDir = `${work}/qc`;
const workbookName = "Q1_D09C_MAINLINE_AUDIT_v01.xlsx";

function parseCsv(text) {
  text = text.replace(/^\uFEFF/, "");
  const rows = [];
  let row = [];
  let field = "";
  let quoted = false;
  for (let i = 0; i < text.length; i += 1) {
    const char = text[i];
    if (quoted) {
      if (char === '"' && text[i + 1] === '"') {
        field += '"';
        i += 1;
      } else if (char === '"') {
        quoted = false;
      } else {
        field += char;
      }
    } else if (char === '"') {
      quoted = true;
    } else if (char === ",") {
      row.push(field);
      field = "";
    } else if (char === "\n") {
      row.push(field.replace(/\r$/, ""));
      rows.push(row);
      row = [];
      field = "";
    } else {
      field += char;
    }
  }
  if (field.length || row.length) {
    row.push(field.replace(/\r$/, ""));
    rows.push(row);
  }
  return rows;
}

function columnLetter(index) {
  let value = index + 1;
  let result = "";
  while (value > 0) {
    const remainder = (value - 1) % 26;
    result = String.fromCharCode(65 + remainder) + result;
    value = Math.floor((value - 1) / 26);
  }
  return result;
}

function preferredWidth(header) {
  const h = header.toLowerCase();
  if (/(note|purpose|treatment|description|descr|path|codes|roots|panels|evalids|cns|role)/.test(h)) return 34;
  if (/(status|candidate_id|frame_definition|membership_source|statement_id)/.test(h)) return 24;
  if (/(name|class|method|adjustment|variance_inputs)/.test(h)) return 22;
  return Math.max(11, Math.min(20, header.length + 2));
}

function preserveAsText(header) {
  const h = header.toLowerCase();
  return h === "state_fips" || h === "target_eval_group" || h === "component_evalid" ||
    h === "component_evalids" || h === "actual_component_evalids" ||
    h === "estimation_unit_ids" || h === "observed_p2panel_values" ||
    h === "p2panel_values" || h === "lineage_root" || h === "plot_visit_cns" ||
    h.endsWith("_cn") || h.endsWith("_cns");
}

async function sha256File(filePath) {
  const hash = crypto.createHash("sha256");
  await new Promise((resolve, reject) => {
    const stream = fsSync.createReadStream(filePath);
    stream.on("data", (chunk) => hash.update(chunk));
    stream.on("end", resolve);
    stream.on("error", reject);
  });
  return hash.digest("hex");
}

const theme = {
  navy: "#17365D",
  blue: "#1F4E78",
  teal: "#0F6B78",
  paleBlue: "#D9EAF7",
  paleGreen: "#E2F0D9",
  paleAmber: "#FFF2CC",
  paleRed: "#FCE4D6",
  gray: "#E7E6E6",
  white: "#FFFFFF",
  text: "#1F2937",
};

const sheetSpecs = [
  ["Frame Summary", "D09C_TEMPORAL_FRAME_SUMMARY_v01.csv"],
  ["Frame Audit", "D09C_TEMPORAL_FRAME_AUDIT_v01.csv"],
  ["EVALID Components", "D09C_EVALID_COMPONENT_LEDGER_v01.csv"],
  ["Candidates", "D09C_WHOLE_PANEL_PARTITION_CANDIDATES_v01.csv"],
  ["Top Partitions", "D09C_TOP_PARTITION_DIAGNOSTICS_v01.csv"],
  ["Lineage", "D09C_LINEAGE_CROSSFOLD_AUDIT_v01.csv"],
  ["Calibration", "D09C_DESIGN_CALIBRATION_AUDIT_v01.csv"],
  ["Input Audit", "D09C_INPUT_AUDIT_v01.csv"],
  ["Table Access", "D09C_TABLE_ACCESS_AUDIT_v01.csv"],
  ["SQL Ledger", "D09C_SQL_LEDGER_v01.csv"],
  ["QC", "D09C_QC_v01.csv"],
];

const workbook = Workbook.create();
const summary = workbook.worksheets.add("Summary");
const imported = new Map();

for (const [sheetName, fileName] of sheetSpecs) {
  const rows = parseCsv(await fs.readFile(`${inputDir}/${fileName}`, "utf8"));
  if (rows.length < 2 || rows[0].length < 1) throw new Error(`Empty audit CSV: ${fileName}`);
  const sheet = workbook.worksheets.add(sheetName);
  imported.set(sheetName, { rows, headers: rows[0], fileName });
  const rowCount = rows.length;
  const colCount = rows[0].length;
  const lastCol = columnLetter(colCount - 1);
  const identifierColumns = new Set(rows[0].map((header, index) => preserveAsText(header) ? index : -1).filter((index) => index >= 0));
  const displayRows = rows.map((sourceRow, rowIndex) => rowIndex === 0 ? sourceRow : sourceRow.map((value, colIndex) => identifierColumns.has(colIndex) ? "" : value));
  sheet.getRangeByIndexes(0, 0, rowCount, colCount).values = displayRows;
  sheet.showGridLines = false;
  sheet.freezePanes.freezeRows(1);
  sheet.freezePanes.freezeColumns(Math.min(5, colCount));
  sheet.getRange(`A1:${lastCol}1`).format = {
    fill: theme.blue,
    font: { bold: true, color: theme.white, size: 9 },
    wrapText: true,
    verticalAlignment: "center",
    borders: { preset: "outside", style: "thin", color: theme.navy },
  };
  sheet.getRange(`A1:${lastCol}1`).format.rowHeight = 38;
  if (rowCount > 1) {
    sheet.getRange(`A2:${lastCol}${rowCount}`).format = {
      font: { color: theme.text, size: 8 },
      verticalAlignment: "top",
    };
  }
  for (let col = 0; col < colCount; col += 1) {
    const header = rows[0][col] ?? "";
    const letter = columnLetter(col);
    sheet.getRange(`${letter}1:${letter}${rowCount}`).format.columnWidth = preferredWidth(header);
    if (/(note|purpose|treatment|description|descr|path|codes|roots|panels|evalids|cns|role)/i.test(header)) {
      sheet.getRange(`${letter}2:${letter}${rowCount}`).format.wrapText = true;
    }
    if (preserveAsText(header) || /(state_abbr|candidate_id|frame_id|stratumcd|p2panel|subpanel)/i.test(header)) {
      sheet.getRange(`${letter}2:${letter}${rowCount}`).format.numberFormat = "@";
    }
  }
  sheet.tables.add(`A1:${lastCol}${rowCount}`, true, `T_${sheetName.replace(/[^A-Za-z0-9]/g, "_")}`);
  for (let col = 0; col < colCount; col += 1) {
    const header = rows[0][col] ?? "";
    if (!preserveAsText(header)) continue;
    const letter = columnLetter(col);
    sheet.getRange(`${letter}2:${letter}${rowCount}`).formulas = rows.slice(1).map((sourceRow) => {
      const value = String(sourceRow[col] ?? "").replace(/"/g, '""');
      return [`="${value}"`];
    });
  }
  const setWidth = (headerName, width) => {
    const col = rows[0].indexOf(headerName);
    if (col >= 0) sheet.getRange(`${columnLetter(col)}1:${columnLetter(col)}${rowCount}`).format.columnWidth = width;
  };
  if (sheetName === "Input Audit") {
    setWidth("role", 30); setWidth("path", 58); setWidth("bytes", 16);
    setWidth("observed_sha256", 68); setWidth("expected_sha256", 68); setWidth("status", 14);
    sheet.getRange(`A2:${lastCol}${rowCount}`).format.rowHeight = 34;
  } else if (sheetName === "SQL Ledger") {
    setWidth("statement_id", 34); setWidth("tables_declared", 32); setWidth("sql_sha256", 68);
    setWidth("species_or_prohibited_marker_present", 24); setWidth("purpose", 42);
  } else if (sheetName === "QC") {
    setWidth("check", 42); setWidth("status", 14); setWidth("observed", 38);
    setWidth("expected", 38); setWidth("note", 48);
  }
}

const build = JSON.parse(await fs.readFile(`${qcDir}/D09C_BUILD_SUMMARY_v01.json`, "utf8"));
const largeLedgerSpecs = [
  ["D09C_PANEL_SUBPANEL_YEAR_LEDGER_v01.csv", build?.panel_subpanel_year_rows ?? 65233, "Complete panel/subpanel/year/stratum/50-km all-plot ledger"],
  ["D09C_TI_FOLD_WEIGHT_AUDIT_v01.csv", build?.ti_weight_rows ?? 9472, "Complete temporally integrated fold-weight audit"],
  ["D09C_MA_FOLD_WEIGHT_AUDIT_v01.csv", build?.ma_weight_rows ?? 23680, "Complete mean-of-annual panel-weight audit"],
];

const ledgerIndexRows = [["canonical_file", "data_rows", "bytes", "sha256", "role", "workbook_treatment"]];
for (const [fileName, rowCount, role] of largeLedgerSpecs) {
  const filePath = `${inputDir}/${fileName}`;
  const stat = await fs.stat(filePath);
  ledgerIndexRows.push([fileName, String(rowCount), String(stat.size), await sha256File(filePath), role, "Full UTF-8 CSV is authoritative and packaged; indexed here to keep the audit workbook usable"]);
}
const largeLedgerIndex = workbook.worksheets.add("Large Ledger Index");
largeLedgerIndex.getRangeByIndexes(0, 0, ledgerIndexRows.length, ledgerIndexRows[0].length).values = ledgerIndexRows;
largeLedgerIndex.showGridLines = false;
largeLedgerIndex.freezePanes.freezeRows(1);
largeLedgerIndex.getRange("A1:F1").format = { fill: theme.blue, font: { bold: true, color: theme.white, size: 9 }, wrapText: true };
largeLedgerIndex.getRange("A1:F4").format.borders = { preset: "all", style: "thin", color: "#D9E2F3" };
largeLedgerIndex.getRange("A1:A4").format.columnWidth = 40;
largeLedgerIndex.getRange("B1:C4").format.columnWidth = 15;
largeLedgerIndex.getRange("D1:D4").format.columnWidth = 68;
largeLedgerIndex.getRange("E1:F4").format.columnWidth = 44;
largeLedgerIndex.getRange("E2:F4").format.wrapText = true;
largeLedgerIndex.tables.add("A1:F4", true, "T_Large_Ledger_Index");
const frameSummaryRows = imported.get("Frame Summary").rows.slice(1);
summary.showGridLines = false;
summary.getRange("A1:H1").merge();
summary.getRange("A1").values = [["Q1 D09C — Species-blind reporting-state / panel-fold design audit v01"]];
summary.getRange("A1:H1").format = {
  fill: theme.navy,
  font: { bold: true, color: theme.white, size: 15 },
  horizontalAlignment: "left",
  verticalAlignment: "center",
};
summary.getRange("A1:H1").format.rowHeight = 32;

summary.getRange("A3:H3").values = [["Execution status", null, "Nationwide feasibility", null, "Final partition", null, "Outcome tables read", null]];
summary.getRange("B3").formulas = [["=IF(COUNTIF('QC'!$B$2:$B$20,\"FAIL\")=0,\"PASS\",\"FAIL\")"]];
summary.getRange("D3").formulas = [["=IF(COUNTIF('Frame Summary'!$H$2:$H$3,\"FAIL\")>0,\"FAIL\",\"PASS\")"]];
summary.getRange("F3").values = [[build.final_partition_selected ? "SELECTED" : "NOT SELECTED"]];
summary.getRange("H3").values = [[build.species_outcome_tables_read.length ? build.species_outcome_tables_read.join(";") : "NONE"]];
for (const range of ["A3:B3", "C3:D3", "E3:F3", "G3:H3"]) {
  summary.getRange(range).format = {
    fill: theme.paleGreen,
    font: { bold: true, color: theme.text, size: 10 },
    borders: { preset: "outside", style: "thin", color: "#A9D18E" },
  };
}
summary.getRange("C3:D3").format.fill = theme.paleRed;

summary.getRange("A5:H5").merge();
summary.getRange("A5").values = [["Frozen build counts and integrity checks"]];
summary.getRange("A5:H5").format = { fill: theme.teal, font: { bold: true, color: theme.white, size: 11 } };
summary.getRange("A6:H9").values = [
  ["State×frame rows", build.state_frame_rows, "Whole-panel candidates", build.candidate_rows, "Rankable top diagnostics", build.rankable_top_state_frames, "Panel-year ledger rows", build.panel_subpanel_year_rows],
  ["Lineage audit rows", build.lineage_audit_rows, "TI weight rows", build.ti_weight_rows, "MA weight rows", build.ma_weight_rows, "Calibration rows", build.calibration_rows],
  ["Selected unique EVALIDs", build.selected_unique_evalids, "Assignments", build.selected_assignment_rows, "Duplicate assignment keys", build.duplicate_assignment_keys, "Unmatched assignments", build.unmatched_plot_assignments],
  ["Broken stratum assignments", build.broken_stratum_assignments, "State mismatches", build.state_mismatch_assignments, "Runtime seconds", build.runtime_seconds, "Workbook role", "AUDIT VIEW"],
];
summary.getRange("A6:H9").format = { borders: { preset: "all", style: "thin", color: "#D9E2F3" }, font: { size: 9 } };
for (const cell of ["B6", "D6", "F6", "H6", "B7", "D7", "F7", "H7", "B8", "D8", "F8", "H8", "B9", "D9"]) {
  summary.getRange(cell).format.numberFormat = "#,##0";
}
summary.getRange("F9").format.numberFormat = "0.000";

summary.getRange("A11:I11").merge();
summary.getRange("A11").values = [["Frozen temporal-frame result"]];
summary.getRange("A11:I11").format = { fill: theme.teal, font: { bold: true, color: theme.white, size: 11 } };
summary.getRange("A12:I12").values = [imported.get("Frame Summary").rows[0]];
summary.getRange("A13:I14").values = frameSummaryRows;
summary.getRange("A12:I12").format = { fill: theme.paleBlue, font: { bold: true, color: theme.text, size: 9 }, wrapText: true };
summary.getRange("A12:I14").format.borders = { preset: "all", style: "thin", color: "#D9E2F3" };

summary.getRange("A16:H16").merge();
summary.getRange("A16").values = [["Key design diagnostics"]];
summary.getRange("A16:H16").format = { fill: theme.teal, font: { bold: true, color: theme.white, size: 11 } };
summary.getRange("A17:H20").values = [
  ["T1 missing state group", build.T1_missing_state_groups || "NONE", null, null, "T2 missing state groups", build.T2_missing_state_groups || "NONE", null, null],
  ["Texas membership", "Actual POP_EVAL_GRP → POP_EVAL_TYP → EXPVOL components; no guessed EVALID membership", null, null, null, null, null, null],
  ["Candidate unit", "Whole P2PANEL only; two panels versus complementary three panels", null, null, "50-km grid", "EPSG:5070, fixed origin (0,0)", null, null],
  ["Estimator audit", "TI fold recalibration and MA equal complete-panel combination; full-evaluation EXPNS comparator only", null, null, "Final estimator", "NOT SELECTED", null, null],
];
for (const row of [17, 18, 19, 20]) {
  summary.getRange(`B${row}:D${row}`).merge();
  summary.getRange(`F${row}:H${row}`).merge();
}
summary.getRange("A17:H20").format = { fill: theme.paleAmber, borders: { preset: "all", style: "thin", color: "#E6B800" }, wrapText: true, font: { size: 9 } };

summary.getRange("A22:H22").merge();
summary.getRange("A22").values = [["Scope guardrails and transfer decision"]];
summary.getRange("A22:H22").format = { fill: theme.teal, font: { bold: true, color: theme.white, size: 11 } };
summary.getRange("A23:H26").values = [
  ["Allowed evidence", "FIA reporting state, EVALID, full P2PANEL, estimation unit, post-stratum, plots, time, 50-km all-plot coverage, weights/variance", null, null, null, null, null, null],
  ["Prohibited and not performed", "Species outcomes, D08C2, Range Gate 0, Little/USGS, external range search, final cohort, real Q1", null, null, null, null, null, null],
  ["Interpretation", "Computational execution PASS; nationwide design feasibility FAIL under the frozen local database", null, null, null, null, null, null],
  ["Next action", "STOP and return to scientific mainline for audit/decision; no downstream phase started", null, null, null, null, null, null],
];
for (let row = 23; row <= 26; row += 1) summary.getRange(`B${row}:H${row}`).merge();
summary.getRange("A23:H26").format = { fill: theme.gray, borders: { preset: "all", style: "thin", color: "#BFBFBF" }, wrapText: true, font: { size: 9 } };

summary.freezePanes.freezeRows(1);
summary.getRange("A1:A26").format.columnWidth = 23;
summary.getRange("B1:B26").format.columnWidth = 29;
summary.getRange("C1:C26").format.columnWidth = 23;
summary.getRange("D1:D26").format.columnWidth = 24;
summary.getRange("E1:E26").format.columnWidth = 23;
summary.getRange("F1:F26").format.columnWidth = 27;
summary.getRange("G1:G26").format.columnWidth = 22;
summary.getRange("H1:H26").format.columnWidth = 25;
summary.getRange("I1:I26").format.columnWidth = 22;
summary.getRange("A17:H20").format.rowHeight = 34;
summary.getRange("A23:H26").format.rowHeight = 34;

await fs.mkdir(inputDir, { recursive: true });
await fs.rm(`${qcDir}/WORKBOOK_PREVIEWS_v01`, { recursive: true, force: true });
await fs.mkdir(`${qcDir}/WORKBOOK_PREVIEWS_v01`, { recursive: true });

const summaryInspect = await workbook.inspect({
  kind: "table",
  sheetId: "Summary",
  range: "A1:I26",
  include: "values,formulas",
  tableMaxRows: 26,
  tableMaxCols: 9,
  maxChars: 12000,
});
await fs.writeFile(`${qcDir}/D09C_WORKBOOK_SUMMARY_INSPECT_v01.ndjson`, summaryInspect.ndjson, "utf8");

const formulaErrors = await workbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
  options: { useRegex: true, maxResults: 300 },
  summary: "D09C final formula error scan",
});
await fs.writeFile(`${qcDir}/D09C_WORKBOOK_FORMULA_ERROR_SCAN_v01.ndjson`, formulaErrors.ndjson, "utf8");

const renderIndex = [];
for (const sheetName of ["Summary", "Large Ledger Index", ...sheetSpecs.map(([name]) => name)]) {
  const info = sheetName === "Summary" ? { rows: 26, cols: 9 } : sheetName === "Large Ledger Index" ? { rows: 4, cols: 6 } : {
    rows: imported.get(sheetName).rows.length,
    cols: imported.get(sheetName).rows[0].length,
  };
  const renderRows = Math.min(info.rows, 26);
  const renderCols = Math.min(info.cols, 14);
  const renderRange = `A1:${columnLetter(renderCols - 1)}${renderRows}`;
  const preview = await workbook.render({ sheetName, range: renderRange, scale: 1.05, format: "png" });
  const previewName = `${sheetName.replace(/[^A-Za-z0-9]+/g, "_")}.png`;
  const previewPath = `${qcDir}/WORKBOOK_PREVIEWS_v01/${previewName}`;
  await fs.writeFile(previewPath, new Uint8Array(await preview.arrayBuffer()));
  renderIndex.push({ sheet_name: sheetName, range: renderRange, preview_path: previewPath });
}
await fs.writeFile(`${qcDir}/D09C_WORKBOOK_RENDER_INDEX_v01.json`, JSON.stringify(renderIndex, null, 2) + "\n", "utf8");

const xlsx = await SpreadsheetFile.exportXlsx(workbook);
const outputPath = `${inputDir}/${workbookName}`;
await xlsx.save(outputPath);
console.log(JSON.stringify({ status: "PASS", workbook: outputPath, sheets: 13, previews: renderIndex.length }, null, 2));
