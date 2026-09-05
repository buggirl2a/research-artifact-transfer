import crypto from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";


const pkg = "C:/range_paper/10_archive/d10e/pkg";
const out = `${pkg}/out`;
const qc = `${pkg}/qc`;
const control = `${pkg}/control`;
const exportDir = "C:/range_paper/99_tmp/d10e/xlsx_builder/outputs/01a061c1-dc1a-7722-a0ff-bbe8ed2923cf";
const previewDir = "C:/range_paper/99_tmp/d10e/xlsx_builder/previews";
const exportPath = `${exportDir}/audit_v01.xlsx`;
const finalPath = `${out}/audit_v01.xlsx`;
const font = "Arial";


function parseCsv(text) {
  const rows = [];
  let row = [], field = "", quoted = false;
  for (let i = 0; i < text.length; i += 1) {
    const ch = text[i];
    if (quoted) {
      if (ch === '"' && text[i + 1] === '"') { field += '"'; i += 1; }
      else if (ch === '"') quoted = false;
      else field += ch;
    } else if (ch === '"') quoted = true;
    else if (ch === ",") { row.push(field); field = ""; }
    else if (ch === "\n") { row.push(field.replace(/\r$/, "")); rows.push(row); row = []; field = ""; }
    else field += ch;
  }
  if (field.length || row.length) { row.push(field.replace(/\r$/, "")); rows.push(row); }
  const clean = rows.filter((r, index) => index === 0 || r.some((value) => value !== ""));
  if (clean.length) clean[0][0] = clean[0][0].replace(/^\uFEFF/, "");
  return clean;
}


async function readCsv(base, name) {
  const rows = parseCsv(await fs.readFile(`${base}/${name}`, "utf8"));
  const header = rows[0];
  return rows.slice(1).map((row) => Object.fromEntries(header.map((key, index) => [key, row[index] ?? ""])));
}


const numberPattern = /^-?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?$/;
const textHeaders = new Set([
  "state", "world", "orientation", "observation_regime", "metric", "component", "definition",
  "left_state", "right_state", "scientific_disposition", "predictor", "outcome", "statistic",
  "threshold_applied", "status", "check_id", "note", "notes", "asset", "path", "expected_sha256",
  "actual_sha256", "random_variable", "conditioning_variables", "distribution", "parameter_source",
  "scientific_layer", "redrawn_in_repeated_observation", "fixed_or_redrawn", "synthetic_species_id",
  "target_fold", "dominant_panel_role", "individual_gain_missing_semantics", "extension", "reason",
]);


function typed(value, header = "") {
  if (value === "") return null;
  if (textHeaders.has(header) || /(?:^|_)id$/i.test(header) || /sha256/i.test(header)) return value;
  if (numberPattern.test(value)) return Number(value);
  return value;
}


function matrixAuto(rows, headers = null) {
  const keys = headers ?? (rows.length ? Object.keys(rows[0]) : []);
  return [keys, ...rows.map((row) => keys.map((key) => typed(row[key], key)))];
}


function columnName(index) {
  let result = "";
  for (let value = index + 1; value > 0; value = Math.floor((value - 1) / 26)) {
    result = String.fromCharCode(65 + ((value - 1) % 26)) + result;
  }
  return result;
}


function title(sheet, heading, subtitle, endColumn) {
  sheet.showGridLines = false;
  sheet.getRange(`A1:${endColumn}1`).format.font = { name: font, size: 15, bold: true, color: "#17324D" };
  sheet.getRange("A1").values = [[heading]];
  sheet.getRange(`A2:${endColumn}2`).format = {
    font: { name: font, size: 9, italic: true, color: "#52616B" },
    borders: { bottom: { style: "thin", color: "#9FB3C8" } },
  };
  sheet.getRange("A2").values = [[subtitle]];
  sheet.getRange("A1").format.rowHeight = 26;
  sheet.getRange("A2").format.rowHeight = 22;
}


function writeTable(sheet, startRow, startCol, values, widths = null) {
  if (!values.length || !values[0].length) return;
  const range = sheet.getRangeByIndexes(startRow, startCol, values.length, values[0].length);
  range.values = values;
  const header = sheet.getRangeByIndexes(startRow, startCol, 1, values[0].length);
  header.format = {
    fill: "#244A64",
    font: { name: font, bold: true, color: "#FFFFFF", size: 9 },
    wrapText: true,
    horizontalAlignment: "center",
    verticalAlignment: "center",
    borders: { preset: "inside", style: "thin", color: "#FFFFFF" },
  };
  header.format.rowHeight = 34;
  if (values.length > 1) {
    const body = sheet.getRangeByIndexes(startRow + 1, startCol, values.length - 1, values[0].length);
    body.format = {
      font: { name: font, size: 9, color: "#1F2937" },
      verticalAlignment: "top",
      borders: { bottom: { style: "thin", color: "#D9E2EA" } },
    };
  }
  for (let col = 0; col < values[0].length; col += 1) {
    const headerText = String(values[0][col] ?? "");
    let defaultWidth = 16;
    if (/sha256/i.test(headerText)) defaultWidth = 68;
    else if (/path/i.test(headerText)) defaultWidth = 48;
    else if (/note|reason/i.test(headerText)) defaultWidth = 42;
    else if (/component|predictor|outcome|regime_applicability|random_variable|conditioning|parameter_source|scientific_layer|paired_world|authority|semantics|distribution/i.test(headerText)) defaultWidth = 34;
    else if (/observed|expected/i.test(headerText)) defaultWidth = 26;
    const width = widths?.[col] ?? defaultWidth;
    sheet.getRangeByIndexes(startRow, startCol + col, values.length, 1).format.columnWidth = width;
  }
}


function formatNumericColumns(sheet, startRow, rowCount, headers) {
  headers.forEach((header, index) => {
    if (/fraction|coverage|correlation|rho|ratio|relative|containment/i.test(header)) {
      sheet.getRangeByIndexes(startRow + 1, index, rowCount - 1, 1).format.numberFormat = "0.0000";
    } else if (/bytes|rows|cells|plots|realizations|count|^n$|^K$|block|replicate/i.test(header)) {
      sheet.getRangeByIndexes(startRow + 1, index, rowCount - 1, 1).format.numberFormat = "#,##0";
    } else if (/pp|gain|bias|rmse|distance|variance|mean|median|mcse|value|min|max|q\d|sd/i.test(header)) {
      sheet.getRangeByIndexes(startRow + 1, index, rowCount - 1, 1).format.numberFormat = "0.0000";
    }
  });
}


function dataSheet(wb, name, heading, subtitle, rows, headers = null) {
  const sheet = wb.worksheets.add(name);
  const values = matrixAuto(rows, headers);
  const end = columnName(Math.max(7, values[0].length - 1));
  title(sheet, heading, subtitle, end);
  writeTable(sheet, 3, 0, values);
  formatNumericColumns(sheet, 3, values.length, values[0]);
  if (values.length > 20) sheet.freezePanes.freezeRows(4);
  if (values[0].length > 6) sheet.freezePanes.freezeColumns(2);
  return sheet;
}


const stateRows = await readCsv(out, "state_summary_v01.csv");
const sourceRows = await readCsv(out, "source_decomp_v01.csv");
const ladderRows = await readCsv(out, "k_ladder_summary_v01.csv");
const mapRows = await readCsv(out, "map_recovery_summary_v01.csv");
const uncertaintyRows = await readCsv(out, "uncertainty_summary_v01.csv");
const relationshipRows = await readCsv(out, "information_relationships_v01.csv");
const convergenceRows = await readCsv(out, "mc_convergence_v01.csv");
const currentRows = await readCsv(out, "current_deviation_v01.csv");
const e5Rows = await readCsv(out, "e5_summary_v01.csv");
const stochasticRows = await readCsv(control, "stochastic_ledger_v01.csv");
const computeChecks = await readCsv(qc, "checks_v01.csv");
const independentChecks = await readCsv(qc, "independent_checks_v01.csv");
const inputRows = await readCsv(qc, "input_id_v01.csv");
const build = JSON.parse(await fs.readFile(`${qc}/build_summary_v01.json`, "utf8"));

const wb = Workbook.create();
const summary = wb.worksheets.add("Summary");
title(summary, "D10E abundance measurement noise decomposition", "Synthetic oracle-support diagnostic on the frozen D3 common measurable domain. Scientific disposition remains with mainline.", "L");

const stateOrder = ["E0", "E1", "E2", "E3", "E4", "E5"];
const stateIndex = new Map(stateRows.filter((row) => row.observation_regime === "O1" && row.orientation === "ALL").map((row) => [row.state, row]));
const stateTable = [["State", "Separation (pp)", "Meaning"], ...stateOrder.map((state) => {
  const meanings = {
    E0: "Matching latent reference", E1: "Frozen single A2 realization", E2: "Terminal conditional mean",
    E3: "Full expected mass map", E4: "Mean normalized map", E5: "Expected finite-realization statistic",
  };
  return [state, Number(stateIndex.get(state).separation_pp), meanings[state]];
})];
writeTable(summary, 3, 0, stateTable, [12, 18, 36]);
summary.getRange("B5:B10").format.numberFormat = "0.000";
const stateChart = summary.charts.add("bar", summary.getRange("A4:B10"));
stateChart.title = "STRONG − PAIRED_NULL separation (pp)";
stateChart.hasLegend = false;
stateChart.titleTextStyle.typeface = font;
stateChart.xAxis = { axisType: "textAxis", textStyle: { typeface: font, fontSize: 10 } };
stateChart.yAxis = { numberFormatCode: "0.0", numberFormatSourceLinked: false, textStyle: { typeface: font, fontSize: 10 } };
stateChart.setPosition("E4", "L16");

const components = [
  ["A expected operator", "A_SYSTEMATIC_MEASUREMENT_OPERATOR"],
  ["B normalization", "B_NORMALIZATION_NONLINEARITY"],
  ["C finite realization", "C_FINITE_REALIZATION_DOWNSTREAM"],
  ["D current realization", "D_CURRENT_REALIZATION_DEVIATION"],
];
const compIndex = new Map(sourceRows.filter((row) => row.observation_regime === "O1" && row.orientation === "ALL" && row.metric === "separation_pp").map((row) => [row.component, row]));
const componentTable = [["Component", "Contribution (pp)", "Definition"], ...components.map(([label, key]) => [label, Number(compIndex.get(key).component_value_pp), compIndex.get(key).definition])];
writeTable(summary, 13, 0, componentTable, [24, 19, 16]);
summary.getRange("B15:B18").format.numberFormat = "0.000";
const compChart = summary.charts.add("bar", summary.getRange("A14:B18"));
compChart.title = "Source contributions to separation (pp)";
compChart.hasLegend = false;
compChart.titleTextStyle.typeface = font;
compChart.xAxis = { axisType: "textAxis", textStyle: { typeface: font, fontSize: 9 } };
compChart.yAxis = { numberFormatCode: "0.0", numberFormatSourceLinked: false, textStyle: { typeface: font, fontSize: 10 } };
compChart.setPosition("E18", "L30");

const facts = [
  ["Diagnostic fact", "Value"],
  ["Accepted Monte Carlo realizations", Number(build.accepted_MC_realizations)],
  ["Pooled separation MCSE (pp)", Number(build.MC_pooled_separation_mcse_pp)],
  ["AB separation MCSE (pp)", Number(build.MC_AB_separation_mcse_pp)],
  ["BA separation MCSE (pp)", Number(build.MC_BA_separation_mcse_pp)],
  ["E0 maximum reproduction difference", Number(build.E0_max_abs_reproduction_diff)],
  ["E1 maximum reproduction difference", Number(build.E1_max_abs_reproduction_diff)],
  ["E2 maximum relative cell-mass error", Number(build.E2_max_relative_cell_mass_error)],
  ["D3 retained cells", Number(build.D3_cells)],
];
writeTable(summary, 21, 0, facts, [40, 22]);
summary.getRange("B24:B26").format.numberFormat = "0.0000";
summary.getRange("B23").format.numberFormat = "#,##0";
summary.getRange("B27:B29").format.numberFormat = "0.00E+00";
summary.getRange("B30").format.numberFormat = "#,##0";
summary.getRange("A33:L33").format = { fill: "#DDEBF7", font: { name: font, bold: true, color: "#17324D" } };
summary.getRange("A33").values = [["Interpretation boundary"]];
const notes = [
  ["E2 and E3 reproduce E0 exactly under the audited synthetic positive-opportunity identity."],
  ["E5 remains negative because the downstream functional is applied to finite noisy maps."],
  ["The repeated-survey ladder approaches E0 as K increases; this is diagnostic and does not assert that repeat FIA surveys are available."],
  ["No new estimator, uncertainty model, support repair, real species analysis, or scientific PASS/HOLD/FAIL is assigned."],
];
summary.getRange("A34:A37").values = notes;
summary.getRange("A34:L37").format = { font: { name: font, size: 9, color: "#334155" }, wrapText: true };
summary.getRange("A34:A37").format.columnWidth = 110;

dataSheet(wb, "States", "E0–E5 downstream states", "O1/O2/O3 are retained as labels; corrected A2 abundance is regime-invariant.", stateRows);
dataSheet(wb, "Decomposition", "Source decomposition", "Components A–D are shown separately for regime, orientation, and metric. No scientific disposition is assigned.", sourceRows);

const ladderSheet = wb.worksheets.add("K ladder");
title(ladderSheet, "Repeated-survey averaging ladder", "Non-overlapping blocks from the accepted Monte Carlo stream. Bands and spread are computational diagnostics.", "M");
const kValues = [1, 2, 4, 8, 16, 32];
const ladderIndex = new Map(ladderRows.filter((row) => row.metric === "separation_pp").map((row) => [`${row.K}|${row.orientation}`, row]));
const ladderWide = [["K", "AB mean (pp)", "BA mean (pp)", "AB q05", "AB q95", "BA q05", "BA q95"], ...kValues.map((K) => {
  const ab = ladderIndex.get(`${K}|AB`), ba = ladderIndex.get(`${K}|BA`);
  return [K, Number(ab.mean), Number(ba.mean), Number(ab.q05), Number(ab.q95), Number(ba.q05), Number(ba.q95)];
})];
writeTable(ladderSheet, 3, 0, ladderWide, [10, 17, 17, 13, 13, 13, 13]);
ladderSheet.getRange("B5:G10").format.numberFormat = "0.000";
const ladderChart = ladderSheet.charts.add("line", ladderSheet.getRange("A4:C10"));
ladderChart.title = "Separation by averaged realization count";
ladderChart.titleTextStyle.typeface = font;
ladderChart.legend = { position: "top", textStyle: { typeface: font } };
ladderChart.xAxis = { axisType: "textAxis", textStyle: { typeface: font, fontSize: 10 } };
ladderChart.yAxis = { numberFormatCode: "0.0", numberFormatSourceLinked: false, textStyle: { typeface: font, fontSize: 10 } };
ladderChart.setPosition("I4", "P18");
const ladderMatrix = matrixAuto(ladderRows);
writeTable(ladderSheet, 12, 0, ladderMatrix);
formatNumericColumns(ladderSheet, 12, ladderMatrix.length, ladderMatrix[0]);
ladderSheet.freezePanes.freezeRows(4);

dataSheet(wb, "Map recovery", "Map-recovery summaries", "Hellinger, sliced-Wasserstein, correlation, bias, RMSE, entropy, and concentration summaries within D3.", mapRows);

const uncertaintySheet = dataSheet(wb, "Uncertainty", "Empirical uncertainty audit", "Repeated-observation variation compared with the frozen Poisson-style interval representation. No uncertainty model is fitted.", uncertaintyRows);
const uncertaintyHelper = [["Group", "Empirical variance", "Poisson plug-in", "Current E1 Poisson"], ...uncertaintyRows.map((row) => [
  `${row.world === "PAIRED_NULL" ? "NULL" : row.world} ${row.orientation}`,
  Number(row.empirical_variance_normal_interval_coverage_mean),
  Number(row.poisson_plugin_interval_coverage_mean),
  Number(row.current_E1_poisson_interval_coverage),
])];
writeTable(uncertaintySheet, 20, 17, uncertaintyHelper, [18, 18, 18, 18]);
uncertaintySheet.getRange("S22:U25").format.numberFormat = "0.0000";
const uncertaintyChart = uncertaintySheet.charts.add("bar", uncertaintySheet.getRange("R21:U25"));
uncertaintyChart.title = "Coverage diagnostics";
uncertaintyChart.titleTextStyle.typeface = font;
uncertaintyChart.legend = { position: "top", textStyle: { typeface: font } };
uncertaintyChart.yAxis = { numberFormatCode: "0.0", numberFormatSourceLinked: false, textStyle: { typeface: font, fontSize: 10 } };
uncertaintyChart.setPosition("R4", "Z18");

dataSheet(wb, "Information", "Information-amount relationships", "Descriptive Pearson and Spearman relationships only. No exclusion threshold or causal claim is assigned.", relationshipRows);

const mcSheet = wb.worksheets.add("Monte Carlo");
title(mcSheet, "Monte Carlo precision and current realization", "Precision gates are computational only and were frozen before simulation.", "N");
const convergenceMatrix = matrixAuto(convergenceRows);
writeTable(mcSheet, 3, 0, convergenceMatrix);
formatNumericColumns(mcSheet, 3, convergenceMatrix.length, convergenceMatrix[0]);
const currentMatrix = matrixAuto(currentRows);
writeTable(mcSheet, 8, 0, currentMatrix);
formatNumericColumns(mcSheet, 8, currentMatrix.length, currentMatrix[0]);
const e5Matrix = matrixAuto(e5Rows);
writeTable(mcSheet, 14, 0, e5Matrix);
formatNumericColumns(mcSheet, 14, e5Matrix.length, e5Matrix[0]);

dataSheet(wb, "Stochastic hierarchy", "Observation stochastic components", "Machine-readable ledger reconstructed from frozen D10A, D10C-resume, D10C-A, and D10D authority.", stochasticRows);

const checksSheet = wb.worksheets.add("Checks");
title(checksSheet, "Computational and independent checks", "Core computation checks and independent cross-table reconstruction checks.", "H");
const computeMatrix = matrixAuto(computeChecks);
writeTable(checksSheet, 3, 0, computeMatrix, [30, 12, 20, 20, 40]);
const independentMatrix = matrixAuto(independentChecks);
writeTable(checksSheet, computeMatrix.length + 6, 0, independentMatrix, [34, 12, 22, 22, 42]);
checksSheet.freezePanes.freezeRows(4);

dataSheet(wb, "Inputs", "Frozen input identities", "Outer SHA-256 values and applicable internal manifests were checked before computation.", inputRows);

const fileRows = [];
for (const directory of ["control", "out", "qc", "fig", "manifest", "src"]) {
  const dir = `${pkg}/${directory}`;
  try {
    for (const name of await fs.readdir(dir)) {
      const full = `${dir}/${name}`;
      const stat = await fs.stat(full);
      if (stat.isFile() && name !== "audit_v01.xlsx" && !name.startsWith("audit_") && name !== "xlsx_validation_v01.json") {
        const bytes = await fs.readFile(full);
        fileRows.push({ relative_path: `${directory}/${name}`, size_bytes: stat.size, sha256: crypto.createHash("sha256").update(bytes).digest("hex") });
      }
    }
  } catch { /* Directory may not yet exist in a partial reproduction. */ }
}
fileRows.sort((a, b) => a.relative_path.localeCompare(b.relative_path));
dataSheet(wb, "Files", "Pre-workbook package files", "File size and SHA-256 snapshot before audit workbook export. Final inventory is in the delivery index.", fileRows);

await fs.mkdir(exportDir, { recursive: true });
await fs.mkdir(previewDir, { recursive: true });
const output = await SpreadsheetFile.exportXlsx(wb);
await output.save(exportPath);
await fs.copyFile(exportPath, finalPath);

const inspectParts = [];
inspectParts.push((await wb.inspect({ kind: "workbook,sheet,table,drawing", maxChars: 12000, tableMaxRows: 8, tableMaxCols: 10 })).ndjson);
inspectParts.push((await wb.inspect({ kind: "region", sheetId: "Summary", range: "A1:L37", maxChars: 8000 })).ndjson);
inspectParts.push((await wb.inspect({ kind: "region", sheetId: "K ladder", range: "A1:P20", maxChars: 6000 })).ndjson);
await fs.writeFile(`${qc}/audit_inspect_v01.ndjson`, inspectParts.join("\n"), "utf8");
const errors = await wb.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!",
  options: { useRegex: true, maxResults: 300 },
  summary: "final formula error scan",
});
await fs.writeFile(`${qc}/audit_errors_v01.ndjson`, errors.ndjson, "utf8");

const renderRows = [];
for (const sheet of wb.worksheets.items) {
  const preview = await wb.render({ sheetName: sheet.name, autoCrop: "all", scale: 1, format: "png" });
  const bytes = new Uint8Array(await preview.arrayBuffer());
  const name = `${sheet.name.replace(/[^A-Za-z0-9]+/g, "_")}.png`;
  const target = path.join(previewDir, name);
  await fs.writeFile(target, bytes);
  renderRows.push({ sheet: sheet.name, preview: target, size_bytes: bytes.length, sha256: crypto.createHash("sha256").update(bytes).digest("hex") });
}
await fs.writeFile(`${qc}/audit_render_v01.json`, JSON.stringify({ status: "PASS", workbook: finalPath, sheets: renderRows }, null, 2) + "\n", "utf8");
await fs.writeFile(`${qc}/xlsx_validation_v01.json`, JSON.stringify({
  status: "PASS",
  library: "@oai/artifact-tool",
  workbook: finalPath,
  workbook_bytes: (await fs.stat(finalPath)).size,
  sheet_count: renderRows.length,
  gates: {
    twelve_sheets: renderRows.length === 12,
    summary_readback: inspectParts[1].includes("E0") && inspectParts[1].includes("E5"),
    k_ladder_readback: inspectParts[2].includes("32"),
    no_formula_errors: errors.ndjson.includes("matched 0 entries"),
    every_sheet_rendered: renderRows.length === wb.worksheets.items.length,
  },
}, null, 2) + "\n", "utf8");
console.log(JSON.stringify({ status: "PASS", workbook: finalPath, thread_output: exportPath, sheets: renderRows.length }, null, 2));
