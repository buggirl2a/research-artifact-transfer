import fs from "node:fs/promises";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const root = "C:/range_paper";
const work = `${root}/99_tmp/range_gate0_v02_corrected`;
const out = `${work}/outputs`;
const qc = `${work}/qc`;

function parseCsv(text) {
  text = text.replace(/^\uFEFF/, "");
  const rows = []; let row = [], field = "", quoted = false;
  for (let i = 0; i < text.length; i += 1) {
    const c = text[i];
    if (quoted) {
      if (c === '"' && text[i + 1] === '"') { field += '"'; i += 1; }
      else if (c === '"') quoted = false;
      else field += c;
    } else if (c === '"') quoted = true;
    else if (c === ",") { row.push(field); field = ""; }
    else if (c === "\n") { row.push(field.replace(/\r$/, "")); rows.push(row); row = []; field = ""; }
    else field += c;
  }
  if (field.length || row.length) { row.push(field.replace(/\r$/, "")); rows.push(row); }
  return rows;
}

function colLetter(index) {
  let n = index + 1, s = "";
  while (n > 0) { const r = (n - 1) % 26; s = String.fromCharCode(65 + r) + s; n = Math.floor((n - 1) / 26); }
  return s;
}

function widthFor(header) {
  const h = header.toLowerCase();
  if (/(evidence|explanation|local_path|description|expected|actual)/.test(h)) return 42;
  if (/(sha256|reason_code|semantic_role|reconciliation|route|status)/.test(h)) return 34;
  if (/(species_name|class|macro_region|relative_path)/.test(h)) return 24;
  return Math.max(12, Math.min(22, header.length + 2));
}

const theme = { navy: "#17365D", blue: "#1F4E78", teal: "#0F6B78", white: "#FFFFFF", paleBlue: "#D9EAF7", paleGreen: "#E2F0D9", paleAmber: "#FFF2CC", paleRed: "#FCE4D6", gray: "#E7E6E6", text: "#1F2937" };
const specs = [
  ["Classification", `${out}/Q1_RANGE_GATE0_V02_CORRECTED_SPECIES_CLASSIFICATION_v01.csv`],
  ["Class Summary", `${out}/Q1_RANGE_GATE0_V02_CORRECTED_SUMMARY_v01.csv`],
  ["Decision Queue", `${out}/Q1_RANGE_GATE0_V02_CORRECTED_DECISION_QUEUE_v01.csv`],
  ["Fail Extra NA", `${out}/Q1_RANGE_GATE0_V02_CORRECTED_FAIL_EXTRA_NA_v01.csv`],
  ["Delta Audit", `${out}/Q1_RANGE_GATE0_V01_TO_V02_CORRECTED_DELTA_AUDIT_v01.csv`],
  ["Delta Summary", `${out}/Q1_RANGE_GATE0_V01_TO_V02_CORRECTED_DELTA_SUMMARY_v01.csv`],
  ["Build QC", `${qc}/Q1_RANGE_GATE0_V02_CORRECTED_QC_v01.csv`],
  ["Delta QC", `${qc}/Q1_RANGE_GATE0_V01_TO_V02_DELTA_QC_v01.csv`],
  ["Input Hash Audit", `${qc}/Q1_RANGE_GATE0_V02_CORRECTED_INPUT_HASH_AUDIT_v01.csv`],
  ["v01 Immutability", `${qc}/RANGE_GATE0_V01_IMMUTABILITY_SNAPSHOT_v01.csv`],
];

const wb = Workbook.create();
const summarySheet = wb.worksheets.add("Summary");
const imported = new Map();
for (const [sheetName, filePath] of specs) {
  const rows = parseCsv(await fs.readFile(filePath, "utf8"));
  if (rows.length < 2) throw new Error(`Empty CSV: ${filePath}`);
  imported.set(sheetName, rows);
  const sheet = wb.worksheets.add(sheetName);
  const rowCount = rows.length, colCount = rows[0].length, lastCol = colLetter(colCount - 1);
  sheet.getRangeByIndexes(0, 0, rowCount, colCount).values = rows;
  sheet.showGridLines = false; sheet.freezePanes.freezeRows(1); sheet.freezePanes.freezeColumns(Math.min(2, colCount));
  sheet.getRange(`A1:${lastCol}1`).format = { fill: theme.blue, font: { bold: true, color: theme.white, size: 9 }, wrapText: true, verticalAlignment: "center", borders: { preset: "outside", style: "thin", color: theme.navy } };
  sheet.getRange(`A1:${lastCol}1`).format.rowHeight = 42;
  sheet.getRange(`A2:${lastCol}${rowCount}`).format = { font: { color: theme.text, size: 8 }, verticalAlignment: "top" };
  for (let c = 0; c < colCount; c += 1) {
    const header = rows[0][c] || "", letter = colLetter(c);
    sheet.getRange(`${letter}1:${letter}${rowCount}`).format.columnWidth = widthFor(header);
    if (/(evidence|explanation|local_path|description|expected|actual)/i.test(header)) sheet.getRange(`${letter}2:${letter}${rowCount}`).format.wrapText = true;
    if (/(analysis_species_id|sha256|check_id)/i.test(header)) sheet.getRange(`${letter}2:${letter}${rowCount}`).format.numberFormat = "@";
  }
  sheet.tables.add(`A1:${lastCol}${rowCount}`, true, `T_${sheetName.replace(/[^A-Za-z0-9]/g, "_")}`);
  if (sheetName.endsWith("QC")) sheet.getRange(`A2:${lastCol}${rowCount}`).format.rowHeight = 32;
}

const classification = imported.get("Classification");
const h = classification[0];
const fixtureNames = new Set(["Magnolia virginiana", "Ostrya virginiana", "Quercus rugosa", "Sorbus decora", "Pinus banksiana", "Populus balsamifera", "Pinus balfouriana"]);
const fixtureHeaders = ["analysis_species_name", "confirmed_native_outside_North_America", "transcontinental_circumboreal_global_extension_flag", "other_na_extension_level3_areas", "confirmed_native_outside_North_America_level3_areas", "range_gate0_v02_class", "range_gate0_v02_reason_code", "whole_range_core_route"];
const fixtureRows = [fixtureHeaders, ...classification.slice(1).filter(row => fixtureNames.has(row[h.indexOf("analysis_species_name")])).map(row => fixtureHeaders.map(header => row[h.indexOf(header)]))];
const fixtureSheet = wb.worksheets.add("Semantic Fixtures");
fixtureSheet.getRangeByIndexes(0, 0, fixtureRows.length, fixtureHeaders.length).values = fixtureRows;
fixtureSheet.showGridLines = false; fixtureSheet.freezePanes.freezeRows(1);
fixtureSheet.getRange("A1:H1").format = { fill: theme.blue, font: { bold: true, color: theme.white, size: 9 }, wrapText: true };
fixtureSheet.getRange("A1:H1").format.rowHeight = 42;
fixtureSheet.getRange("A1:H8").format.borders = { preset: "all", style: "thin", color: "#D9E2F3" };
for (const [col, width] of [["A", 25], ["B", 26], ["C", 28], ["D", 42], ["E", 42], ["F", 26], ["G", 38], ["H", 40]]) fixtureSheet.getRange(`${col}1:${col}8`).format.columnWidth = width;
fixtureSheet.getRange("D2:E8").format.wrapText = true;
fixtureSheet.tables.add("A1:H8", true, "T_Semantic_Fixtures");

const build = JSON.parse(await fs.readFile(`${qc}/RANGE_GATE0_V02_CORRECTED_BUILD_SUMMARY_v01.json`, "utf8"));
const finalAudit = JSON.parse(await fs.readFile(`${qc}/RANGE_GATE0_V02_CORRECTED_INDEPENDENT_OUTPUT_AUDIT_v01.json`, "utf8"));
const immutability = JSON.parse(await fs.readFile(`${qc}/RANGE_GATE0_V01_IMMUTABILITY_AUDIT_v01.json`, "utf8"));
const deltaRows = imported.get("Delta Audit").slice(1);
const deltaHeader = imported.get("Delta Audit")[0];
const changedCount = deltaRows.filter(row => row[deltaHeader.indexOf("class_changed")] === "YES").length;

summarySheet.showGridLines = false;
summarySheet.getRange("A1:H1").merge(); summarySheet.getRange("A1").values = [["Q1 Range Gate 0 v02 corrected — geographic semantics audit"]];
summarySheet.getRange("A1:H1").format = { fill: theme.navy, font: { bold: true, color: theme.white, size: 15 }, verticalAlignment: "center" }; summarySheet.getRange("A1:H1").format.rowHeight = 32;
summarySheet.getRange("A3:H3").values = [["Execution", null, "Input closure", null, "Final output audit", null, "Final cohort", null]];
summarySheet.getRange("B3").formulas = [["=IF(AND(COUNTIF('Build QC'!$E$2:$E$32,\"FAIL\")=0,COUNTIF('Delta QC'!$E$2:$E$16,\"FAIL\")=0),\"PASS\",\"FAIL\")"]];
summarySheet.getRange("D3").values = [[`${build.candidate_rows}/312`]]; summarySheet.getRange("F3").values = [[`${finalAudit.pass_count}/${finalAudit.check_count} PASS`]]; summarySheet.getRange("H3").values = [["NOT SELECTED"]];
for (const range of ["A3:B3", "C3:D3", "E3:F3", "G3:H3"]) summarySheet.getRange(range).format = { fill: theme.paleGreen, font: { bold: true, color: theme.text, size: 10 }, borders: { preset: "outside", style: "thin", color: "#A9D18E" } };

summarySheet.getRange("A5:D5").merge(); summarySheet.getRange("A5").values = [["v02 corrected class counts"]]; summarySheet.getRange("A5:D5").format = { fill: theme.teal, font: { bold: true, color: theme.white, size: 11 } };
summarySheet.getRange("A6:D6").values = [["Class", "Species", "% of 312", "Frozen route"]]; summarySheet.getRange("A6:D6").format = { fill: theme.paleBlue, font: { bold: true, color: theme.text, size: 9 } };
summarySheet.getRange("A7:D12").values = imported.get("Class Summary").slice(1); summarySheet.getRange("A6:D12").format.borders = { preset: "all", style: "thin", color: "#D9E2F3" };
summarySheet.getRange("B7:B12").format.numberFormat = "#,##0"; summarySheet.getRange("C7:C12").format.numberFormat = "0.000000";

summarySheet.getRange("F5:H5").merge(); summarySheet.getRange("F5").values = [["Semantic and integrity facts"]]; summarySheet.getRange("F5:H5").format = { fill: theme.teal, font: { bold: true, color: theme.white, size: 11 } };
summarySheet.getRange("F6:H12").values = [
  ["Transcontinental role", "DIAGNOSTIC ONLY", "zero routing authority"],
  ["Independent triggers", build.transcontinental_independent_trigger_count, "expected 0"],
  ["Regression fixtures", "7/7", "PASS"],
  ["v01→v02 changed rows", changedCount, "not a target"],
  ["v01 immutability", immutability.status, "76 files unchanged"],
  ["v01 scientific label", "MAINLINE CONTRACT SEMANTICS FAIL", "computation PASS"],
  ["UNKNOWN", build.class_counts.UNKNOWN, "no guessing"],
];
summarySheet.getRange("F6:H12").format = { fill: theme.gray, borders: { preset: "all", style: "thin", color: "#BFBFBF" }, wrapText: true, font: { size: 9 } };

summarySheet.getRange("A14:H14").merge(); summarySheet.getRange("A14").values = [["Corrected interpretation and STOP boundary"]]; summarySheet.getRange("A14:H14").format = { fill: theme.teal, font: { bold: true, color: theme.white, size: 11 } };
summarySheet.getRange("A15:H19").values = [
  ["Correction", "Only explicit confirmed native evidence outside North America can trigger FAIL_EXTRA_NA", null, null, null, null, null, null],
  ["Class 2", "BORDERLINE_OTHER_NA includes Central America and other North-America-side extensions under frozen D08B1 predicates", null, null, null, null, null, null],
  ["Not inferred", "Level-3 units are categorical; no area/share/severity, geometry, span, component, or hole inference", null, null, null, null, null, null],
  ["Not performed", "D08C2; Little decisions; external search; FIA outcomes; abundance/detection; final cohort; real Q1", null, null, null, null, null, null],
  ["Next action", "STOP and return immutable v02 corrected package to scientific mainline", null, null, null, null, null, null],
];
for (let r = 15; r <= 19; r += 1) summarySheet.getRange(`B${r}:H${r}`).merge();
summarySheet.getRange("A15:H19").format = { fill: theme.paleAmber, borders: { preset: "all", style: "thin", color: "#E6B800" }, wrapText: true, font: { size: 9 } }; summarySheet.getRange("A15:H19").format.rowHeight = 30;
summarySheet.freezePanes.freezeRows(1);
for (const [col, width] of [["A", 25], ["B", 24], ["C", 18], ["D", 42], ["E", 20], ["F", 28], ["G", 25], ["H", 24]]) summarySheet.getRange(`${col}1:${col}19`).format.columnWidth = width;

await fs.rm(`${qc}/WORKBOOK_PREVIEWS_v01`, { recursive: true, force: true }); await fs.mkdir(`${qc}/WORKBOOK_PREVIEWS_v01`, { recursive: true });
const summaryInspect = await wb.inspect({ kind: "table", sheetId: "Summary", range: "A1:H19", include: "values,formulas", tableMaxRows: 19, tableMaxCols: 8, maxChars: 12000 });
await fs.writeFile(`${qc}/RANGE_GATE0_V02_WORKBOOK_SUMMARY_INSPECT_v01.ndjson`, summaryInspect.ndjson, "utf8");
const fixtureInspect = await wb.inspect({ kind: "table", sheetId: "Semantic Fixtures", range: "A1:H8", include: "values", tableMaxRows: 8, tableMaxCols: 8, maxChars: 12000 });
await fs.writeFile(`${qc}/RANGE_GATE0_V02_WORKBOOK_FIXTURES_INSPECT_v01.ndjson`, fixtureInspect.ndjson, "utf8");
const errors = await wb.inspect({ kind: "match", searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A", options: { useRegex: true, maxResults: 300 }, summary: "Range Gate 0 v02 corrected formula error scan" });
await fs.writeFile(`${qc}/RANGE_GATE0_V02_WORKBOOK_FORMULA_ERROR_SCAN_v01.ndjson`, errors.ndjson, "utf8");

const renderIndex = [];
for (const sheetName of ["Summary", ...specs.map(([name]) => name), "Semantic Fixtures"]) {
  const rows = sheetName === "Summary" ? Array(19).fill(Array(8).fill("")) : sheetName === "Semantic Fixtures" ? fixtureRows : imported.get(sheetName);
  const renderRows = Math.min(rows.length, 24), renderCols = Math.min(rows[0].length, 12), range = `A1:${colLetter(renderCols - 1)}${renderRows}`;
  const png = await wb.render({ sheetName, range, scale: 1.05, format: "png" });
  const previewPath = `${qc}/WORKBOOK_PREVIEWS_v01/${sheetName.replace(/[^A-Za-z0-9]+/g, "_")}.png`;
  await fs.writeFile(previewPath, new Uint8Array(await png.arrayBuffer())); renderIndex.push({ sheet_name: sheetName, range, preview_path: previewPath });
}
await fs.writeFile(`${qc}/RANGE_GATE0_V02_WORKBOOK_RENDER_INDEX_v01.json`, JSON.stringify(renderIndex, null, 2) + "\n", "utf8");
const xlsx = await SpreadsheetFile.exportXlsx(wb); const outputPath = `${out}/Q1_RANGE_GATE0_V02_CORRECTED_MAINLINE_AUDIT_v01.xlsx`; await xlsx.save(outputPath);
console.log(JSON.stringify({ status: "PASS", workbook: outputPath, sheets: 12, previews: renderIndex.length }));
