import fs from "node:fs/promises";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const root = "C:/range_paper";
const sourceDir = `${root}/99_tmp/tax_v02_work/outputs`;
const builderRoot = `${root}/99_tmp/tax_v02_work/xlsx_builder`;
const qcDir = `${builderRoot}/qc`;
const previewDir = `${qcDir}/WORKBOOK_PREVIEWS_v02`;
const outputDir = `${builderRoot}/outputs/01a05787-06b4-72e2-9534-74d911222b3b`;
const outputPath = `${outputDir}/Q1_TAXON_RANGE_MAINLINE_AUDIT_v02.xlsx`;

function parseCsv(text) {
  const rows = [];
  let row = [];
  let field = "";
  let quoted = false;
  for (let i = 0; i < text.length; i += 1) {
    const ch = text[i];
    if (quoted) {
      if (ch === '"' && text[i + 1] === '"') {
        field += '"';
        i += 1;
      } else if (ch === '"') {
        quoted = false;
      } else {
        field += ch;
      }
    } else if (ch === '"') {
      quoted = true;
    } else if (ch === ",") {
      row.push(field);
      field = "";
    } else if (ch === "\n") {
      row.push(field.replace(/\r$/, ""));
      rows.push(row);
      row = [];
      field = "";
    } else {
      field += ch;
    }
  }
  if (field.length || row.length) {
    row.push(field.replace(/\r$/, ""));
    rows.push(row);
  }
  return rows.filter((values, index) => index === 0 || values.some((value) => value !== ""));
}

function colLetter(index) {
  let value = index + 1;
  let result = "";
  while (value > 0) {
    value -= 1;
    result = String.fromCharCode(65 + (value % 26)) + result;
    value = Math.floor(value / 26);
  }
  return result;
}

function safeName(value) {
  return value.replace(/[^A-Za-z0-9_-]+/g, "_");
}

function widthFor(header) {
  const low = header.toLowerCase();
  if (low === "description") return 42;
  if (low === "expected" || low === "observed") return 26;
  if (low.includes("reason") || low.includes("evidence") || low.includes("note") || low.includes("source") || low.includes("names") || low.includes("areas")) return 34;
  if (low.includes("sha256")) return 28;
  if (low.includes("author") || low.includes("taxon_name") || low.includes("species_name") || low.includes("scientific_name") || low.includes("name_raw") || low.endsWith("_name")) return 26;
  if (low.includes("status") || low.includes("class") || low.includes("flag")) return 26;
  if (low.includes("id") || low.includes("code") || low.includes("count") || low.startsWith("n_")) return 14;
  return Math.min(24, Math.max(12, header.length + 2));
}

const sheets = [
  ["Code Map", "Q1_FIA_CODE_TO_ANALYSIS_SPECIES_v02.csv"],
  ["Corrections", "Q1_TAXONOMY_CORRECTION_APPLIED_v02.csv"],
  ["Analysis Species", "Q1_ANALYSIS_SPECIES_MASTER_v02.csv"],
  ["Hybrid Audit", "Q1_HYBRID_NONCORE_AUDIT_v02.csv"],
  ["Hybrid Dist", "Q1_HYBRID_NONCORE_DISTRIBUTION_AUDIT_v02.csv"],
  ["Global Range", "Q1_GLOBAL_RANGE_FLAGS_v02.csv"],
  ["USGS Closure", "Q1_USGS_NAME_CLOSURE_v02.csv"],
  ["USGS Review", "Q1_USGS_LAYER_RECONSTRUCTION_REVIEW_v02.csv"],
  ["Cross Stage", "Q1_USGS_CROSS_STAGE_CONFLICT_v02.csv"],
  ["DRC Protocol", "Q1_DRC_PROTOCOL_v02.csv"],
  ["QC", "Q1_TAXON_RANGE_QC_v02.csv"],
  ["Unresolved", "Q1_TAXON_RANGE_UNRESOLVED_v02.csv"],
  ["Evidence", "Q1_TAXON_RANGE_EVIDENCE_v02.csv"],
  ["WCVP Level3", "Q1_WCVP_NATIVE_DISTRIBUTION_LONG_v02.csv"],
  ["Taxon Master", "Q1_TAXON_RANGE_MASTER_v02.csv"],
];

const workbook = Workbook.create();
const summary = workbook.worksheets.add("Summary");
const matrices = new Map();

for (const [sheetName, fileName] of sheets) {
  const csvText = await fs.readFile(`${sourceDir}/${fileName}`, "utf8");
  const matrix = parseCsv(csvText);
  matrices.set(sheetName, matrix);
  const sheet = workbook.worksheets.add(sheetName);
  sheet.showGridLines = false;
  sheet.getRangeByIndexes(0, 0, matrix.length, matrix[0].length).values = matrix;
  const header = sheet.getRangeByIndexes(0, 0, 1, matrix[0].length);
  header.format = {
    fill: "#0F4C5C",
    font: { bold: true, color: "#FFFFFF" },
    wrapText: true,
    verticalAlignment: "center",
    borders: { preset: "outside", style: "thin", color: "#0B3440" },
  };
  header.format.rowHeight = 34;
  const data = sheet.getRangeByIndexes(1, 0, Math.max(1, matrix.length - 1), matrix[0].length);
  data.format = {
    font: { color: "#1F2937" },
    verticalAlignment: "top",
  };
  for (let col = 0; col < matrix[0].length; col += 1) {
    const column = sheet.getRangeByIndexes(0, col, matrix.length, 1);
    column.format.columnWidth = widthFor(matrix[0][col]);
    if (widthFor(matrix[0][col]) >= 24) column.format.wrapText = true;
  }
  sheet.freezePanes.freezeRows(1);
  sheet.freezePanes.freezeColumns(Math.min(2, matrix[0].length));

  const statusCol = matrix[0].findIndex((value) => value === "status" || value === "application_status" || value === "resolution_disposition");
  if (statusCol >= 0 && matrix.length > 1) {
    const range = sheet.getRangeByIndexes(1, statusCol, matrix.length - 1, 1);
    range.conditionalFormats.add("containsText", { text: "PASS", format: { fill: "#DCFCE7", font: { color: "#166534", bold: true } } });
    range.conditionalFormats.add("containsText", { text: "FAIL", format: { fill: "#FEE2E2", font: { color: "#991B1B", bold: true } } });
    range.conditionalFormats.add("containsText", { text: "REVIEW", format: { fill: "#FEF3C7", font: { color: "#92400E", bold: true } } });
  }
}

summary.showGridLines = false;
summary.getRange("A1:H1").merge();
summary.getRange("A1").values = [["Q1 D08B.1 Taxonomy–USGS Bridge Correction v02"]];
summary.getRange("A1:H1").format = {
  fill: "#0B3440",
  font: { bold: true, color: "#FFFFFF", size: 16 },
  horizontalAlignment: "left",
  verticalAlignment: "center",
};
summary.getRange("A1:H1").format.rowHeight = 32;
summary.getRange("A3:B13").values = [
  ["Audit metric", "Value"],
  ["FIA code-map rows", null],
  ["Ordinary accepted species", null],
  ["WCVP Level-3 ordinary rows", null],
  ["Applied correction cases", null],
  ["Hybrid/non-core code rows", null],
  ["USGS cross-stage rows", null],
  ["Mandatory QC PASS", null],
  ["Mandatory QC FAIL", null],
  ["D08C / FIA TREE / real Q1", "HOLD / NOT RUN"],
  ["Package status", "PASS — pending mainline scientific audit"],
];
summary.getRange("B4:B11").formulas = [
  ["=COUNTA('Code Map'!$A$2:$A$397)"],
  ["=COUNTA('Analysis Species'!$A$2:$A$362)"],
  ["=COUNTA('WCVP Level3'!$A$2:$A$9649)"],
  ["=COUNTA('Corrections'!$A$2:$A$12)"],
  ["=COUNTA('Hybrid Audit'!$A$2:$A$4)"],
  ["=COUNTA('Cross Stage'!$A$2:$A$124)"],
  ["=COUNTIF('QC'!$F$2:$F$32,\"PASS\")"],
  ["=COUNTIF('QC'!$F$2:$F$32,\"FAIL\")"],
];
summary.getRange("A3:B3").format = { fill: "#0F4C5C", font: { bold: true, color: "#FFFFFF" } };
summary.getRange("A4:A13").format = { fill: "#E6F2F4", font: { bold: true, color: "#0B3440" } };
summary.getRange("B4:B13").format = { fill: "#F8FAFC", font: { color: "#111827" } };
summary.getRange("B4:B11").format.numberFormat = "#,##0";
summary.getRange("A15:H15").merge();
summary.getRange("A15").values = [["Frozen scope and interpretation"]];
summary.getRange("A15:H15").format = { fill: "#CFE8ED", font: { bold: true, color: "#0B3440" } };
summary.getRange("A16:H20").merge(true);
summary.getRange("A16:A20").values = [
  ["Taxonomy: exactly 11 mainline-authorized identity decisions; original FIA names remain immutable."],
  ["USGS/Little: author-aware exact bridge only; no fuzzy matching, layer union, selection, or reconstruction."],
  ["Range: frozen WCVP v16 Level-3 native/introduced semantics; no new external distribution search."],
  ["Cross-stage eligibility mappings are diagnostic evidence, not authority."],
  ["This workbook is an audit convenience; authoritative outputs are the UTF-8 CSV files."],
];
summary.getRange("A16:H20").format = { fill: "#F8FAFC", wrapText: true, font: { color: "#334155" } };
summary.getRange("A:A").format.columnWidth = 34;
summary.getRange("B:B").format.columnWidth = 28;
summary.getRange("C:H").format.columnWidth = 12;
summary.freezePanes.freezeRows(1);

await fs.mkdir(previewDir, { recursive: true });
await fs.mkdir(outputDir, { recursive: true });

const summaryInspect = await workbook.inspect({ kind: "table", range: "Summary!A1:H20", include: "values,formulas", tableMaxRows: 22, tableMaxCols: 8, maxChars: 12000 });
await fs.writeFile(`${qcDir}/D08B1_WORKBOOK_SUMMARY_INSPECT_v02.ndjson`, summaryInspect.ndjson, "utf8");
const errorInspect = await workbook.inspect({ kind: "match", searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A", options: { useRegex: true, maxResults: 300 }, summary: "D08B1 final formula error scan" });
await fs.writeFile(`${qcDir}/D08B1_WORKBOOK_FORMULA_ERROR_SCAN_v02.ndjson`, errorInspect.ndjson, "utf8");

const rendered = [];
for (const sheetName of ["Summary", ...sheets.map(([name]) => name)]) {
  const matrix = sheetName === "Summary" ? null : matrices.get(sheetName);
  const maxCol = sheetName === "Summary" ? 7 : Math.min(11, matrix[0].length - 1);
  const maxRow = sheetName === "Summary" ? 19 : Math.min(24, matrix.length - 1);
  const preview = await workbook.render({ sheetName, range: `A1:${colLetter(maxCol)}${maxRow + 1}`, scale: 1.25, format: "png" });
  const previewPath = `${previewDir}/${safeName(sheetName)}.png`;
  await fs.writeFile(previewPath, new Uint8Array(await preview.arrayBuffer()));
  rendered.push({ sheet_name: sheetName, preview_path: previewPath, range: `A1:${colLetter(maxCol)}${maxRow + 1}` });
}
await fs.writeFile(`${qcDir}/D08B1_WORKBOOK_RENDER_INDEX_v02.json`, JSON.stringify({ status: "PASS", sheets_rendered: rendered.length, rendered }, null, 2) + "\n", "utf8");

const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(outputPath);
console.log(JSON.stringify({ status: "PASS", outputPath, sheetCount: 16, previews: rendered.length }, null, 2));
