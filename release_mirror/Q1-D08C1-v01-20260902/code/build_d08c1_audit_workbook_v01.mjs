import fs from "node:fs/promises";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const root = "C:/range_paper";
const work = `${root}/99_tmp/d08c1_v01`;
const inputDir = `${work}/outputs`;
const qcDir = `${work}/qc`;
const threadOutputDir = `${work}/xlsx_builder/outputs/01a05787-06b4-72e2-9534-74d911222b3b`;
const workbookName = "Q1_D08C1_MAINLINE_AUDIT_v01.xlsx";

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

function isNumericHeader(header) {
  return (
    header === "grain_km" || header === "fia_state_code" || header === "wcvp_level3_rows" ||
    header.startsWith("n_") || header.endsWith("_count") || header.endsWith("_fraction") ||
    header.endsWith("_proportion") || header.startsWith("proportion_") || header.endsWith("_flag") ||
    header.endsWith("_min") || header.endsWith("_max") || header.endsWith("_seconds") ||
    header.includes("percent_increase") || header.includes("projected_x_m") ||
    header.includes("projected_y_m") || header === "spatial_span_km" ||
    header === "status_inference_from_alias" || header === "fuzzy_matching_used" ||
    header === "qualifying_tree_rows" || header.startsWith("qualifying_tree_rows_") ||
    header === "positive_primary_plots" || header.startsWith("positive_primary_plots_") ||
    header === "component_positive_primary_plots" || header === "pooled_species_positive_primary_plots" ||
    header === "sum_component_positive_plots_before_dedup" || header === "plot_overlap_removed_by_species_pooling" ||
    header === "detected_cells_each_fold_min" || header === "positive_plots_each_fold_min"
  );
}

function convertCsvRows(rows) {
  const headers = rows[0];
  return rows.map((row, rowIndex) => row.map((value, colIndex) => {
    if (rowIndex === 0 || value === "") return value;
    const header = headers[colIndex] ?? "";
    if (isNumericHeader(header) && /^-?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?$/.test(value)) {
      return Number(value);
    }
    return value;
  }));
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
  ["Grain Summary", "Q1_D08C1_GRAIN_SUMMARY_v01.csv"],
  ["50km Frontiers", "Q1_D08C1_50KM_FRONTIERS_v01.csv"],
  ["Survivor Queue", "Q1_D08C1_LITTLE_REVIEW_SURVIVOR_QUEUE_v01.csv"],
  ["Census", "Q1_D08C1_SPECIES_GRAIN_CENSUS_v01.csv"],
  ["Native State", "Q1_D08C1_NATIVE_STATE_AUDIT_v01.csv"],
  ["Code Aggregation", "Q1_D08C1_CODE_AGGREGATION_AUDIT_v01.csv"],
  ["Nonanalysis", "Q1_D08C1_NONANALYSIS_CODE_AUDIT_v01.csv"],
  ["State Crosswalk", "Q1_D08C1_STATE_CROSSWALK_AUDIT_v01.csv"],
  ["A-B Split", "Q1_D08C1_AB_SPLIT_AUDIT_v01.csv"],
  ["Domain Grid", "Q1_D08C1_DOMAIN_GRID_AUDIT_v01.csv"],
  ["Lineage", "Q1_D08C1_LINEAGE_AUDIT_v01.csv"],
  ["QC", "Q1_D08C1_QC_v01.csv"],
  ["Input Audit", "Q1_D08C1_INPUT_AUDIT_v01.csv"],
  ["Trace Sample", "Q1_D08C1_TRACEABILITY_SAMPLE_v01.csv"],
];

const workbook = Workbook.create();
const summary = workbook.worksheets.add("Summary");
const imported = new Map();

for (const [sheetName, fileName] of sheetSpecs) {
  const raw = parseCsv(await fs.readFile(`${inputDir}/${fileName}`, "utf8"));
  const rows = convertCsvRows(raw);
  const sheet = workbook.worksheets.add(sheetName);
  imported.set(sheetName, { rows, headers: raw[0] });
  const rowCount = rows.length;
  const colCount = rows[0].length;
  sheet.getRangeByIndexes(0, 0, rowCount, colCount).values = rows;
  sheet.showGridLines = false;
  sheet.freezePanes.freezeRows(1);
  const lastCol = columnLetter(colCount - 1);
  sheet.getRange(`A1:${lastCol}1`).format = {
    fill: theme.blue,
    font: { bold: true, color: theme.white, size: 10 },
    wrapText: true,
    verticalAlignment: "center",
    borders: { preset: "outside", style: "thin", color: theme.navy },
  };
  sheet.getRange(`A1:${lastCol}1`).format.rowHeight = 34;
  if (rowCount > 1) {
    sheet.getRange(`A2:${lastCol}${rowCount}`).format = {
      font: { color: theme.text, size: 9 },
      verticalAlignment: "top",
    };
  }
  for (let col = 0; col < colCount; col += 1) {
    const header = raw[0][col] ?? "";
    let width = Math.max(10, Math.min(34, header.length + 3));
    if (header.includes("note") || header.includes("reason") || header.includes("rule") || header.includes("role") || header.includes("path")) width = 34;
    if (header === "census_view") width = 32;
    if (header.includes("name") || header.includes("status") || header.includes("class")) width = Math.max(width, 24);
    const letter = columnLetter(col);
    sheet.getRange(`${letter}1:${letter}${rowCount}`).format.columnWidth = width;
    if (header.includes("note") || header.includes("reason") || header.includes("rule") || header.includes("role") || header.includes("path")) {
      sheet.getRange(`${letter}2:${letter}${rowCount}`).format.wrapText = true;
    }
    if (header.includes("proportion") || header.endsWith("_fraction") || header.includes("percent_increase")) {
      sheet.getRange(`${letter}2:${letter}${rowCount}`).format.numberFormat = "0.0%";
    } else if (header === "physical_plot_lineage_id" || header === "selected_primary_measurement_id") {
      sheet.getRange(`${letter}2:${letter}${rowCount}`).format.numberFormat = "@";
      sheet.getRange(`${letter}2:${letter}${rowCount}`).formulas = raw.slice(1).map((sourceRow) => [`="FIA-"&TEXT(${sourceRow[col]},"0")`]);
    } else if (isNumericHeader(header)) {
      sheet.getRange(`${letter}2:${letter}${rowCount}`).format.numberFormat = header.includes("projected_") ? "#,##0.0" : "#,##0";
    }
  }
}

const build = JSON.parse(await fs.readFile(`${qcDir}/D08C1_BUILD_SUMMARY_v01.json`, "utf8"));
const grainRows = imported.get("Grain Summary").rows.slice(1);
summary.showGridLines = false;
summary.getRange("A1:H1").merge();
summary.getRange("A1").values = [["Q1 D08C1 — Accepted-species eligibility census audit v01"]];
summary.getRange("A1:H1").format = {
  fill: theme.navy,
  font: { bold: true, color: theme.white, size: 16 },
  horizontalAlignment: "left",
  verticalAlignment: "center",
};
summary.getRange("A1:H1").format.rowHeight = 32;
summary.getRange("A3:B3").values = [["Engineering status", null]];
summary.getRange("B3").formulas = [["=IF(COUNTIF('QC'!$B$2:$B$24,\"FAIL\")=0,\"PASS\",\"FAIL\")"]];
summary.getRange("D3:E3").values = [["Outcome-blind violation", "NONE"]];
summary.getRange("G3:H3").values = [["Final threshold/cohort", "NOT SELECTED"]];
for (const range of ["A3:B3", "D3:E3", "G3:H3"]) {
  summary.getRange(range).format = {
    fill: theme.paleGreen,
    font: { bold: true, color: theme.text, size: 11 },
    borders: { preset: "outside", style: "thin", color: "#A9D18E" },
  };
}
summary.getRange("A5:H5").merge();
summary.getRange("A5").values = [["Frozen build counts"]];
summary.getRange("A5:H5").format = { fill: theme.teal, font: { bold: true, color: theme.white, size: 11 } };
summary.getRange("A6:H9").values = [
  ["Accepted analysis species", build.analysis_species, "Unique qualifying TREE rows", build.qualifying_unique_tree_rows, "Ordinary accepted-species rows", build.ordinary_accepted_species_tree_rows, "Nonanalysis rows", build.nonanalysis_tree_rows],
  ["Primary measurements", build.primary_measurements, "Census rows", build.census_rows, "Species×state rows", build.native_state_audit_rows, "Survivor queue rows", build.survivor_queue_rows],
  ["Code aggregation rows", build.code_aggregation_rows, "Nonanalysis code rows", build.nonanalysis_code_rows, "Frontier rows", build.frontier_rows, "Frozen QC checks", build.qc_checks],
  ["Workbook role", "AUDIT VIEW", "Little/USGS used", "NO", "Real Q1 run", "NO", "Status", "STOP AFTER DELIVERY"],
];
summary.getRange("A6:H9").format = { borders: { preset: "all", style: "thin", color: "#D9E2F3" }, font: { size: 10 } };
summary.getRange("B6:H8").format.numberFormat = "#,##0";

summary.getRange("A11:K11").merge();
summary.getRange("A11").values = [["Outcome-blind species breadth by frozen grain and census view"]];
summary.getRange("A11:K11").format = { fill: theme.teal, font: { bold: true, color: theme.white, size: 11 } };
summary.getRange("A12:K12").values = [imported.get("Grain Summary").rows[0]];
summary.getRange("A13:K18").values = grainRows;
summary.getRange("A12:K12").format = { fill: theme.paleBlue, font: { bold: true, color: theme.text, size: 9 }, wrapText: true };
summary.getRange("A12:K18").format.borders = { preset: "all", style: "thin", color: "#D9E2F3" };
summary.getRange("A13:A18").format.numberFormat = "#,##0";
summary.getRange("C13:K18").format.numberFormat = "#,##0";

summary.getRange("A20:H20").merge();
summary.getRange("A20").values = [["Scope guardrails"]];
summary.getRange("A20:H20").format = { fill: theme.teal, font: { bold: true, color: theme.white, size: 11 } };
summary.getRange("A21:H24").values = [
  ["State identity", "47 exact full-name matches + the single authorized RI → RHO alias", null, null, null, null, null, null],
  ["Native semantics", "Frozen WCVP flags only; alias itself has no status effect", null, null, null, null, null, null],
  ["Frontiers", "50-km 10/15/20 detected cells per fold × 10/20/30/50/100 positive plots per fold; none selected", null, null, null, null, null, null],
  ["Prohibited", "No Little layer/status, no external search, no Q1 effects, no final grain/threshold/cohort", null, null, null, null, null, null],
];
for (let row = 21; row <= 24; row += 1) summary.getRange(`B${row}:H${row}`).merge();
summary.getRange("A21:H24").format = { fill: theme.paleAmber, borders: { preset: "all", style: "thin", color: "#E6B800" }, wrapText: true, font: { size: 10 } };
summary.freezePanes.freezeRows(1);
summary.getRange("A1:A24").format.columnWidth = 24;
summary.getRange("B1:B24").format.columnWidth = 34;
summary.getRange("C1:C24").format.columnWidth = 19;
summary.getRange("D1:D24").format.columnWidth = 23;
summary.getRange("E1:E24").format.columnWidth = 21;
summary.getRange("F1:F24").format.columnWidth = 23;
summary.getRange("G1:G24").format.columnWidth = 27;
summary.getRange("H1:H24").format.columnWidth = 24;
summary.getRange("A21:H24").format.rowHeight = 30;

await fs.mkdir(threadOutputDir, { recursive: true });
await fs.mkdir(`${qcDir}/WORKBOOK_PREVIEWS_v01`, { recursive: true });

const summaryInspect = await workbook.inspect({
  kind: "table",
  sheetId: "Summary",
  range: "A1:K24",
  include: "values,formulas",
  tableMaxRows: 24,
  tableMaxCols: 11,
  maxChars: 10000,
});
await fs.writeFile(`${qcDir}/D08C1_WORKBOOK_SUMMARY_INSPECT_v01.ndjson`, summaryInspect.ndjson, "utf8");

const formulaErrors = await workbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
  options: { useRegex: true, maxResults: 300 },
  summary: "D08C1 final formula error scan",
});
await fs.writeFile(`${qcDir}/D08C1_WORKBOOK_FORMULA_ERROR_SCAN_v01.ndjson`, formulaErrors.ndjson, "utf8");

const renderIndex = [];
for (const sheetName of ["Summary", ...sheetSpecs.map(([name]) => name)]) {
  const info = sheetName === "Summary" ? { rows: 24, cols: 11 } : {
    rows: imported.get(sheetName).rows.length,
    cols: imported.get(sheetName).rows[0].length,
  };
  const renderRows = Math.min(info.rows, 26);
  const renderCols = Math.min(info.cols, 14);
  const renderRange = `A1:${columnLetter(renderCols - 1)}${renderRows}`;
  const preview = await workbook.render({ sheetName, range: renderRange, scale: 1.2, format: "png" });
  const previewName = `${sheetName.replace(/[^A-Za-z0-9]+/g, "_")}.png`;
  const previewPath = `${qcDir}/WORKBOOK_PREVIEWS_v01/${previewName}`;
  await fs.writeFile(previewPath, new Uint8Array(await preview.arrayBuffer()));
  renderIndex.push({ sheet_name: sheetName, range: renderRange, preview_path: previewPath });
}
await fs.writeFile(`${qcDir}/D08C1_WORKBOOK_RENDER_INDEX_v01.json`, JSON.stringify(renderIndex, null, 2) + "\n", "utf8");

const xlsx = await SpreadsheetFile.exportXlsx(workbook);
const threadOutput = `${threadOutputDir}/${workbookName}`;
await xlsx.save(threadOutput);
await fs.copyFile(threadOutput, `${inputDir}/${workbookName}`);
console.log(JSON.stringify({ status: "PASS", workbook: `${inputDir}/${workbookName}`, thread_output: threadOutput, sheets: 15, previews: renderIndex.length }, null, 2));
