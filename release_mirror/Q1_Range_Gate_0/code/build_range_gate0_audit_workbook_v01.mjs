import fs from "node:fs/promises";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const root = "C:/range_paper";
const work = `${root}/99_tmp/range_gate0_v01`;
const out = `${work}/outputs`;
const qc = `${work}/qc`;

function parseCsv(text) {
  text = text.replace(/^\uFEFF/, "");
  const rows = [];
  let row = [], field = "", quoted = false;
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
  if (/(evidence_text|level3_areas|local_path|description|expected|actual)/.test(h)) return 42;
  if (/(sha256|reason_code|reconciliation|downstream_route|whole_range_core_route)/.test(h)) return 34;
  if (/(species_name|macro_region|class)/.test(h)) return 24;
  return Math.max(12, Math.min(22, header.length + 2));
}

const theme = {
  navy: "#17365D", blue: "#1F4E78", teal: "#0F6B78", white: "#FFFFFF",
  paleBlue: "#D9EAF7", paleGreen: "#E2F0D9", paleAmber: "#FFF2CC",
  paleRed: "#FCE4D6", gray: "#E7E6E6", text: "#1F2937",
};

const specs = [
  ["Classification", `${out}/Q1_RANGE_GATE0_SPECIES_CLASSIFICATION_v01.csv`],
  ["Class Summary", `${out}/Q1_RANGE_GATE0_SUMMARY_v01.csv`],
  ["Decision Queue", `${out}/Q1_RANGE_GATE0_DECISION_QUEUE_v01.csv`],
  ["Fail Extra NA", `${out}/Q1_RANGE_GATE0_FAIL_EXTRA_NA_v01.csv`],
  ["QC", `${qc}/Q1_RANGE_GATE0_QC_v01.csv`],
  ["Input Hash Audit", `${qc}/Q1_RANGE_GATE0_INPUT_HASH_AUDIT_v01.csv`],
];

const wb = Workbook.create();
const summarySheet = wb.worksheets.add("Summary");
const imported = new Map();

for (const [sheetName, filePath] of specs) {
  const rows = parseCsv(await fs.readFile(filePath, "utf8"));
  if (rows.length < 2) throw new Error(`Empty CSV: ${filePath}`);
  imported.set(sheetName, rows);
  const sheet = wb.worksheets.add(sheetName);
  const rowCount = rows.length, colCount = rows[0].length;
  const lastCol = colLetter(colCount - 1);
  sheet.getRangeByIndexes(0, 0, rowCount, colCount).values = rows;
  sheet.showGridLines = false;
  sheet.freezePanes.freezeRows(1);
  sheet.freezePanes.freezeColumns(Math.min(2, colCount));
  sheet.getRange(`A1:${lastCol}1`).format = {
    fill: theme.blue, font: { bold: true, color: theme.white, size: 9 },
    wrapText: true, verticalAlignment: "center",
    borders: { preset: "outside", style: "thin", color: theme.navy },
  };
  sheet.getRange(`A1:${lastCol}1`).format.rowHeight = 40;
  if (rowCount > 1) sheet.getRange(`A2:${lastCol}${rowCount}`).format = { font: { color: theme.text, size: 8 }, verticalAlignment: "top" };
  for (let c = 0; c < colCount; c += 1) {
    const header = rows[0][c] || "";
    const letter = colLetter(c);
    sheet.getRange(`${letter}1:${letter}${rowCount}`).format.columnWidth = widthFor(header);
    if (/(evidence_text|level3_areas|local_path|description|expected|actual)/i.test(header)) sheet.getRange(`${letter}2:${letter}${rowCount}`).format.wrapText = true;
    if (/(analysis_species_id|sha256|check_id)/i.test(header)) sheet.getRange(`${letter}2:${letter}${rowCount}`).format.numberFormat = "@";
  }
  sheet.tables.add(`A1:${lastCol}${rowCount}`, true, `T_${sheetName.replace(/[^A-Za-z0-9]/g, "_")}`);
  if (sheetName === "QC") sheet.getRange(`A2:${lastCol}${rowCount}`).format.rowHeight = 32;
}

const build = JSON.parse(await fs.readFile(`${qc}/RANGE_GATE0_BUILD_SUMMARY_v01.json`, "utf8"));
const independent = JSON.parse(await fs.readFile(`${qc}/RANGE_GATE0_INDEPENDENT_AUDIT_v01.json`, "utf8"));
const classes = ["FAIL_EXTRA_NA", "BORDERLINE_SOUTH", "BORDERLINE_MEXICO", "RETAIN_USCA_AUDIT", "PASS_COARSE", "UNKNOWN"];
const counts = classes.map((name) => [name, build.class_counts[name]]);

summarySheet.showGridLines = false;
summarySheet.getRange("A1:H1").merge();
summarySheet.getRange("A1").values = [["Q1 Range Gate 0 — whole-range completeness coarse screen v01"]];
summarySheet.getRange("A1:H1").format = { fill: theme.navy, font: { bold: true, color: theme.white, size: 15 }, verticalAlignment: "center" };
summarySheet.getRange("A1:H1").format.rowHeight = 32;

summarySheet.getRange("A3:H3").values = [["Execution", null, "Input closure", null, "Output-only audit", null, "Final cohort", null]];
summarySheet.getRange("B3").formulas = [["=IF(COUNTIF('QC'!$E$2:$E$23,\"FAIL\")=0,\"PASS\",\"FAIL\")"]];
summarySheet.getRange("D3").values = [[`${build.candidate_rows}/312`]];
summarySheet.getRange("F3").values = [[`${independent.pass_count}/${independent.check_count} PASS`]];
summarySheet.getRange("H3").values = [["NOT SELECTED"]];
for (const range of ["A3:B3", "C3:D3", "E3:F3", "G3:H3"]) {
  summarySheet.getRange(range).format = { fill: theme.paleGreen, font: { bold: true, color: theme.text, size: 10 }, borders: { preset: "outside", style: "thin", color: "#A9D18E" } };
}

summarySheet.getRange("A5:D5").merge();
summarySheet.getRange("A5").values = [["Frozen class counts"]];
summarySheet.getRange("A5:D5").format = { fill: theme.teal, font: { bold: true, color: theme.white, size: 11 } };
summarySheet.getRange("A6:D6").values = [["Class", "Species", "% of 312", "Frozen downstream route"]];
summarySheet.getRange("A6:D6").format = { fill: theme.paleBlue, font: { bold: true, color: theme.text, size: 9 }, wrapText: true };
const sourceSummaryRows = imported.get("Class Summary").slice(1);
summarySheet.getRange("A7:D12").values = sourceSummaryRows;
summarySheet.getRange("A6:D12").format.borders = { preset: "all", style: "thin", color: "#D9E2F3" };
summarySheet.getRange("B7:B12").format.numberFormat = "#,##0";
summarySheet.getRange("C7:C12").format.numberFormat = "0.000000";

summarySheet.getRange("F5:H5").merge();
summarySheet.getRange("F5").values = [["Independent integrity facts"]];
summarySheet.getRange("F5:H5").format = { fill: theme.teal, font: { bold: true, color: theme.white, size: 11 } };
summarySheet.getRange("F6:H11").values = [
  ["Master rows", build.master_rows, "expected 361"],
  ["Candidate rows", build.candidate_rows, "expected 312"],
  ["Long evidence rows", build.long_evidence_rows, "frozen D08B1 v02"],
  ["QC", `${build.qc_pass_count}/${build.qc_check_count}`, "PASS"],
  ["Output-only audit", `${independent.pass_count}/${independent.check_count}`, independent.status],
  ["UNKNOWN", build.class_counts.UNKNOWN, "no guessing"],
];
summarySheet.getRange("F6:H11").format = { fill: theme.gray, borders: { preset: "all", style: "thin", color: "#BFBFBF" }, font: { size: 9 } };
summarySheet.getRange("G6:G8").format.numberFormat = "#,##0";

summarySheet.getRange("A14:H14").merge();
summarySheet.getRange("A14").values = [["Scientific interpretation boundary"]];
summarySheet.getRange("A14:H14").format = { fill: theme.teal, font: { bold: true, color: theme.white, size: 11 } };
summarySheet.getRange("A15:H18").values = [
  ["Object", "Outcome-blind, source-frozen coarse routing of whole-range completeness using D08B1 v02 only", null, null, null, null, null, null],
  ["Not inferred", "Administrative-unit counts are not area, range share, geometry, or truncation severity", null, null, null, null, null, null],
  ["Not performed", "Little decisions; external search; D08C2; FIA outcome/eligibility; abundance/detection; real Q1", null, null, null, null, null, null],
  ["Next action", "STOP and return the immutable package to scientific mainline for audit", null, null, null, null, null, null],
];
for (let r = 15; r <= 18; r += 1) summarySheet.getRange(`B${r}:H${r}`).merge();
summarySheet.getRange("A15:H18").format = { fill: theme.paleAmber, borders: { preset: "all", style: "thin", color: "#E6B800" }, wrapText: true, font: { size: 9 } };
summarySheet.getRange("A15:H18").format.rowHeight = 30;

summarySheet.freezePanes.freezeRows(1);
for (const [col, width] of [["A", 25], ["B", 24], ["C", 18], ["D", 42], ["E", 20], ["F", 25], ["G", 22], ["H", 24]]) summarySheet.getRange(`${col}1:${col}18`).format.columnWidth = width;

await fs.rm(`${qc}/WORKBOOK_PREVIEWS_v01`, { recursive: true, force: true });
await fs.mkdir(`${qc}/WORKBOOK_PREVIEWS_v01`, { recursive: true });
const summaryInspect = await wb.inspect({ kind: "table", sheetId: "Summary", range: "A1:H18", include: "values,formulas", tableMaxRows: 18, tableMaxCols: 8, maxChars: 10000 });
await fs.writeFile(`${qc}/RANGE_GATE0_WORKBOOK_SUMMARY_INSPECT_v01.ndjson`, summaryInspect.ndjson, "utf8");
const errors = await wb.inspect({ kind: "match", searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A", options: { useRegex: true, maxResults: 300 }, summary: "Range Gate 0 formula error scan" });
await fs.writeFile(`${qc}/RANGE_GATE0_WORKBOOK_FORMULA_ERROR_SCAN_v01.ndjson`, errors.ndjson, "utf8");

const renderIndex = [];
for (const sheetName of ["Summary", ...specs.map(([name]) => name)]) {
  const rows = sheetName === "Summary" ? Array(18).fill(Array(8).fill("")) : imported.get(sheetName);
  const renderRows = Math.min(rows.length, 24);
  const renderCols = Math.min(rows[0].length, 12);
  const range = `A1:${colLetter(renderCols - 1)}${renderRows}`;
  const png = await wb.render({ sheetName, range, scale: 1.05, format: "png" });
  const previewPath = `${qc}/WORKBOOK_PREVIEWS_v01/${sheetName.replace(/[^A-Za-z0-9]+/g, "_")}.png`;
  await fs.writeFile(previewPath, new Uint8Array(await png.arrayBuffer()));
  renderIndex.push({ sheet_name: sheetName, range, preview_path: previewPath });
}
await fs.writeFile(`${qc}/RANGE_GATE0_WORKBOOK_RENDER_INDEX_v01.json`, JSON.stringify(renderIndex, null, 2) + "\n", "utf8");

const xlsx = await SpreadsheetFile.exportXlsx(wb);
const outputPath = `${out}/Q1_RANGE_GATE0_MAINLINE_AUDIT_v01.xlsx`;
await xlsx.save(outputPath);
console.log(JSON.stringify({ status: "PASS", workbook: outputPath, sheets: 7, previews: renderIndex.length }));
