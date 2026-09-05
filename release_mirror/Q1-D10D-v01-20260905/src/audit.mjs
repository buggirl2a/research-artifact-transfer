import fs from "node:fs/promises";
import { FileBlob, SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const pkg = "C:/range_paper/10_archive/d10d/pkg";
const out = `${pkg}/out`;
const qc = `${pkg}/qc`;
const fig = `${pkg}/fig`;
const exportDir = "C:/range_paper/99_tmp/d10d/outputs/e352cb2a";
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
  const clean = rows.filter((r, i) => i === 0 || r.some((v) => v !== ""));
  if (clean.length) clean[0][0] = clean[0][0].replace(/^\uFEFF/, "");
  return clean;
}

async function readCsv(name) {
  const rows = parseCsv(await fs.readFile(`${out}/${name}`, "utf8"));
  const header = rows[0];
  return rows.slice(1).map((r) => Object.fromEntries(header.map((h, i) => [h, r[i] ?? ""])));
}

const numberPattern = /^-?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?$/;
function typed(value, header = "") {
  if (value === "") return null;
  const textFields = new Set([
    "cell_50km", "split_seed", "target_fold", "orientation", "world", "state", "status", "class",
    "metric", "observation_regime", "predictor", "outcome", "statistic", "notes", "area_interpretation",
    "scientific_disposition", "matching_latent_reference", "analysis_level",
  ]);
  if (/(?:^|_)id$/i.test(header) || textFields.has(header)) return value;
  return numberPattern.test(value) ? Number(value) : value;
}

function matrix(rows, columns) {
  return [columns.map((c) => c[1]), ...rows.map((r) => columns.map((c) => typed(r[c[0]], c[0])))];
}

function writeTable(sheet, startRow, startCol, values, widths = []) {
  const range = sheet.getRangeByIndexes(startRow, startCol, values.length, values[0].length);
  range.values = values;
  const header = sheet.getRangeByIndexes(startRow, startCol, 1, values[0].length);
  header.format = {
    fill: "#244A64", font: { name: font, bold: true, color: "#FFFFFF", size: 10 },
    wrapText: true, horizontalAlignment: "center", verticalAlignment: "center",
    borders: { preset: "inside", style: "thin", color: "#FFFFFF" },
  };
  header.format.rowHeight = 32;
  if (values.length > 1) {
    const body = sheet.getRangeByIndexes(startRow + 1, startCol, values.length - 1, values[0].length);
    body.format = { font: { name: font, size: 9, color: "#1F2937" }, verticalAlignment: "top", borders: { bottom: { style: "thin", color: "#D9E2F3" } } };
  }
  for (let i = 0; i < values[0].length; i += 1) {
    sheet.getRangeByIndexes(startRow, startCol + i, values.length, 1).format.columnWidth = widths[i] ?? 18;
  }
}

function title(sheet, heading, subtitle, endCol = "H") {
  sheet.showGridLines = false;
  sheet.getRange(`A1:${endCol}1`).merge();
  sheet.getRange("A1").values = [[heading]];
  sheet.getRange(`A1:${endCol}1`).format = { font: { name: font, size: 16, bold: true, color: "#17324D" }, verticalAlignment: "center" };
  sheet.getRange(`A1:${endCol}1`).format.rowHeight = 28;
  sheet.getRange(`A2:${endCol}2`).merge();
  sheet.getRange("A2").values = [[subtitle]];
  sheet.getRange(`A2:${endCol}2`).format = { font: { name: font, size: 9, italic: true, color: "#52616B" }, borders: { bottom: { style: "thin", color: "#9FB3C8" } } };
  sheet.getRange(`A2:${endCol}2`).format.rowHeight = 24;
}

const common = await readCsv("common_v01.csv");
const attrSummary = await readCsv("attrib_summary_v01.csv");
const attribution = await readCsv("attribution_v01.csv");
const domain = await readCsv("domain_summary_v01.csv");
const domainDist = await readCsv("domain_dist_v01.csv");
const zeroDist = await readCsv("zero_dist_v01.csv");
const relationships = await readCsv("relationships_v01.csv");
const checksRows = parseCsv(await fs.readFile(`${qc}/checks_v01.csv`, "utf8"));

const stateOrder = ["A0_REF", "D0", "D1", "D2", "D2_A0_REF", "D3", "D3_A0_REF"];
const attrIndex = new Map(attrSummary.map((r) => [r.state, r]));
const wb = Workbook.create();

const summary = wb.worksheets.add("Summary");
title(summary, "D10D zero-opportunity source attribution", "Synthetic oracle-support diagnostic. No scientific disposition or real-data domain is selected.", "J");
const stateTable = [["State", "Separation (pp)", "Matching latent reference (pp)", "Distortion (pp)"], ...stateOrder.map((s) => {
  const r = attrIndex.get(s);
  return [s, Number(r.state_separation_pp_median), Number(r.matching_reference_separation_pp_median), Number(r.distortion_vs_matching_reference_pp_median)];
})];
writeTable(summary, 3, 0, stateTable, [18, 18, 25, 18]);
summary.getRange("B5:D11").format.numberFormat = "0.000";
const stateChart = summary.charts.add("bar", summary.getRange("A4:B11"));
stateChart.title = "STRONG − PAIRED_NULL separation (pp)";
stateChart.hasLegend = false;
stateChart.titleTextStyle.typeface = font;
stateChart.xAxis = { axisType: "textAxis", textStyle: { typeface: font, fontSize: 10 } };
stateChart.yAxis = { numberFormatCode: "0", numberFormatSourceLinked: false, textStyle: { typeface: font, fontSize: 10 } };
stateChart.setPosition("F4", "L16");

const o1 = common.filter((r) => r.observation_regime === "O1" && ["D0", "D1", "D2", "D3"].includes(r.state));
const orientTable = [["State", "AB separation (pp)", "BA separation (pp)"], ...["D0", "D1", "D2", "D3"].map((s) => {
  const ab = o1.find((r) => r.state === s && r.orientation === "AB");
  const ba = o1.find((r) => r.state === s && r.orientation === "BA");
  return [s, Number(ab.strong_minus_paired_null_geometry_gain_pct_median), Number(ba.strong_minus_paired_null_geometry_gain_pct_median)];
})];
writeTable(summary, 14, 0, orientTable, [18, 20, 20]);
summary.getRange("B16:C19").format.numberFormat = "0.000";
const orientChart = summary.charts.add("bar", summary.getRange("A15:C19"));
orientChart.title = "AB and BA separation (pp)";
orientChart.titleTextStyle.typeface = font;
orientChart.legend = { position: "top", textStyle: { typeface: font } };
orientChart.xAxis = { axisType: "textAxis", textStyle: { typeface: font, fontSize: 10 } };
orientChart.yAxis = { numberFormatCode: "0", numberFormatSourceLinked: false, textStyle: { typeface: font, fontSize: 10 } };
orientChart.setPosition("F18", "L31");

const d3ab = domain.find((r) => r.state === "D3" && r.orientation === "AB");
const d3ba = domain.find((r) => r.state === "D3" && r.orientation === "BA");
const d1 = attrIndex.get("D1"), d3 = attrIndex.get("D3");
const facts = [
  ["Diagnostic fact", "Value"],
  ["D0 maximum reproduction difference", 1.7053025658242404e-13],
  ["D1 fraction of full D0-to-A0 gap removed", Number(d1.fraction_full_D0_to_A0_gap_removed_from_pooled_medians)],
  ["D3 fraction of full D0-to-A0 gap removed", Number(d3.fraction_full_D0_to_A0_gap_removed_from_pooled_medians)],
  ["D3 common-domain F0 cell retention", Number(d3ab.fraction_F0_cells_retained)],
  ["D3 AB target-fold TI retention", Number(d3ab.fold_specific_TI_fraction_retained)],
  ["D3 BA target-fold TI retention", Number(d3ba.fold_specific_TI_fraction_retained)],
];
writeTable(summary, 21, 0, facts, [42, 22]);
summary.getRange("B23:B28").format.numberFormat = "0.000%";
summary.getRange("B22").format.numberFormat = "0.00E+00";
summary.getRange("A31:J31").merge();
summary.getRange("A31").values = [["Interpretation boundary"]];
summary.getRange("A31:J31").format = { fill: "#DDEBF7", font: { name: font, bold: true, color: "#17324D" } };
summary.getRange("A32:J36").merge(true);
summary.getRange("A32:A36").values = [
  ["D1 changes only zero-opportunity cells with oracle latent mass and cannot be used on real data."],
  ["D2 and D3 align abundance truth, A2, support, and geometry on the same measurable domain."],
  ["D1 removed 3.09% of the pooled full-domain separation gap; D2 and D3 separations remained negative."],
  ["D3 reduced the absolute AB/BA separation gap but retained only 91.56% of F0 cells."],
  ["Mainline decides the scientific category and any real-data estimand. This workbook sets no threshold."],
];
summary.getRange("A32:J36").format = { font: { name: font, size: 9, color: "#334155" }, wrapText: true };

const results = wb.worksheets.add("State Results");
title(results, "Downstream state results", "Medians across five frozen splits. O1/O2/O3 labels are retained exactly.", "N");
const commonCols = [
  ["state", "State"], ["observation_regime", "Regime"], ["orientation", "Orientation"], ["n_split_replicates", "Splits"],
  ["strong_geometry_gain_pct_median", "STRONG gain (pp)"], ["paired_null_geometry_gain_pct_median", "PAIRED_NULL gain (pp)"],
  ["strong_minus_paired_null_geometry_gain_pct_median", "STRONG − null (pp)"], ["strong_predictive_set_gain_pct_median", "STRONG set gain (pp)"],
  ["paired_null_predictive_set_gain_pct_median", "Null set gain (pp)"], ["strong_geometry_truth_coverage_median", "STRONG geometry coverage"],
  ["paired_null_geometry_truth_coverage_median", "Null geometry coverage"], ["strong_world0_truth_coverage_median", "STRONG World 0 coverage"],
  ["paired_null_world0_truth_coverage_median", "Null World 0 coverage"],
];
const commonMatrix = matrix(common, commonCols);
writeTable(results, 3, 0, commonMatrix, [16, 12, 14, 10, 18, 18, 20, 19, 18, 20, 20, 21, 20]);
results.getRange(`D5:M${commonMatrix.length + 3}`).format.numberFormat = "0.0000";
results.freezePanes.freezeRows(4);
results.freezePanes.freezeColumns(3);

const attr = wb.worksheets.add("Attribution");
title(attr, "Separation-gap attribution", "Matching restricted-domain latent references isolate residual A2 distortion from domain-induced signal changes.", "K");
const attrCols = [
  ["state", "State"], ["matching_latent_reference", "Reference"], ["state_separation_pp_median", "State separation (pp)"],
  ["matching_reference_separation_pp_median", "Reference separation (pp)"], ["distortion_vs_matching_reference_pp_median", "Distortion (pp)"],
  ["movement_from_D0_toward_positive_pp_median", "Movement from D0 (pp)"],
  ["fraction_full_D0_to_A0_gap_removed_from_pooled_medians", "Full gap removed"], ["scientific_disposition", "Scientific disposition"],
];
const attrMatrix = matrix(attrSummary, attrCols);
writeTable(attr, 3, 0, attrMatrix, [16, 18, 20, 22, 18, 20, 18, 20]);
attr.getRange(`C5:F${attrMatrix.length + 3}`).format.numberFormat = "0.000";
attr.getRange(`G5:G${attrMatrix.length + 3}`).format.numberFormat = "0.000%";
const detailCols = [
  ["state", "State"], ["matching_latent_reference", "Reference"], ["observation_regime", "Regime"], ["orientation", "Orientation"],
  ["state_separation_pp", "State separation (pp)"], ["matching_reference_separation_pp", "Reference separation (pp)"],
  ["distortion_vs_matching_reference_pp", "Distortion (pp)"], ["movement_from_D0_toward_positive_pp", "Movement from D0 (pp)"],
  ["fraction_full_D0_to_A0_gap_removed", "Full gap removed"],
];
const detailMatrix = matrix(attribution, detailCols);
writeTable(attr, 14, 0, detailMatrix, [14, 17, 12, 13, 19, 21, 17, 20, 17]);
attr.getRange(`E16:H${detailMatrix.length + 14}`).format.numberFormat = "0.000";
attr.getRange(`I16:I${detailMatrix.length + 14}`).format.numberFormat = "0.000%";
attr.freezePanes.freezeRows(4);

const domainSheet = wb.worksheets.add("Domain");
title(domainSheet, "Measurable-domain cost", "Cell, target-fold plot, TI-weight, and effective-block area representation from frozen design authority.", "O");
const domainCols = [
  ["state", "State"], ["orientation", "Orientation"], ["target_fold", "Target fold"], ["total_F0_cells", "F0 cells"],
  ["retained_cells", "Retained cells"], ["removed_cells", "Removed cells"], ["fraction_F0_cells_retained", "Cell retention"],
  ["target_fold_legal_plots_total", "Target legal plots"], ["target_fold_legal_plots_retained", "Retained target plots"],
  ["target_fold_legal_plot_fraction_retained", "Plot retention"], ["fold_specific_TI_fraction_retained", "TI retention"],
  ["effective_block_area_fraction_represented", "Block-area representation"], ["area_interpretation", "Area interpretation"],
];
const domainMatrix = matrix(domain, domainCols);
writeTable(domainSheet, 3, 0, domainMatrix, [12, 13, 12, 12, 14, 14, 16, 17, 19, 16, 15, 20, 42]);
domainSheet.getRange(`G5:G${domainMatrix.length + 3}`).format.numberFormat = "0.000%";
domainSheet.getRange(`J5:L${domainMatrix.length + 3}`).format.numberFormat = "0.000%";
domainSheet.freezePanes.freezeRows(4);

const trunc = wb.worksheets.add("Truncation");
title(trunc, "Species-domain truncation distributions", "No acceptable-loss or severe-truncation threshold is defined.", "M");
const distCols = [
  ["state", "State"], ["world", "World"], ["orientation", "Orientation"], ["metric", "Metric"], ["n", "N"],
  ["min", "Min"], ["q05", "Q05"], ["q25", "Q25"], ["median", "Median"], ["q75", "Q75"], ["q95", "Q95"], ["max", "Max"],
];
const distMatrix = matrix(domainDist, distCols);
writeTable(trunc, 3, 0, distMatrix, [12, 18, 14, 30, 8, 12, 12, 12, 12, 12, 12, 12]);
trunc.getRange(`F5:L${distMatrix.length + 3}`).format.numberFormat = "0.0000%";
const zeroCols = [["world", "World"], ["orientation", "Orientation"], ["n_species", "Species"], ["median", "Median zero mass"], ["q95", "Q95 zero mass"], ["maximum", "Maximum zero mass"], ["species_with_any_zero_truth_mass", "Species with any zero mass"]];
const zeroMatrix = matrix(zeroDist, zeroCols);
writeTable(trunc, 30, 0, zeroMatrix, [18, 14, 12, 19, 17, 20, 24]);
trunc.getRange(`D32:F${zeroMatrix.length + 30}`).format.numberFormat = "0.0000%";
trunc.freezePanes.freezeRows(4);

const rel = wb.worksheets.add("Relationships");
title(rel, "Zero-opportunity relationships", "Pearson and Spearman statistics. Held-out rows use only the five frozen test splits.", "K");
const relCols = [
  ["analysis_level", "Level"], ["state", "State"], ["world", "World"], ["orientation", "Orientation"],
  ["predictor", "Predictor"], ["outcome", "Outcome"], ["statistic", "Statistic"], ["value", "Value"], ["n", "N"], ["notes", "Notes"],
];
const relMatrix = matrix(relationships, relCols);
writeTable(rel, 3, 0, relMatrix, [34, 13, 22, 14, 35, 42, 16, 14, 9, 48]);
rel.getRange(`H5:H${relMatrix.length + 3}`).format.numberFormat = "0.0000";
rel.freezePanes.freezeRows(4);
rel.freezePanes.freezeColumns(4);

const checks = wb.worksheets.add("Checks");
title(checks, "Execution checks", "Implementation gates only. Scientific PASS/HOLD/FAIL is not assigned.", "F");
const checkTyped = [checksRows[0], ...checksRows.slice(1).map((r) => r.map((v, i) => typed(v, checksRows[0][i])))];
writeTable(checks, 3, 0, checkTyped, [38, 12, 26, 24, 58]);
checks.getRange(`B5:B${checkTyped.length + 3}`).conditionalFormats.add("containsText", { text: "PASS", format: { fill: "#E2F0D9", font: { color: "#27632A", bold: true } } });
checks.freezePanes.freezeRows(4);

await fs.mkdir(fig, { recursive: true });
await fs.mkdir(exportDir, { recursive: true });
const inspection = await wb.inspect({ kind: "workbook,sheet,table", maxChars: 18000, tableMaxRows: 6, tableMaxCols: 14, tableMaxCellChars: 90 });
await fs.writeFile(`${qc}/audit_inspect_v01.ndjson`, inspection.ndjson, "utf8");
const errors = await wb.inspect({ kind: "match", searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!", options: { useRegex: true, maxResults: 200 }, summary: "D10D formula error scan" });
await fs.writeFile(`${qc}/audit_errors_v01.ndjson`, errors.ndjson, "utf8");

const renderSpecs = [
  ["Summary", "A1:L36"], ["State Results", "A1:N20"], ["Attribution", "A1:K26"],
  ["Domain", "A1:O10"], ["Truncation", "A1:M35"], ["Relationships", "A1:K24"], ["Checks", `A1:F${checkTyped.length + 3}`],
];
const renders = [];
for (const [sheetName, range] of renderSpecs) {
  const blob = await wb.render({ sheetName, range, scale: 1.0, format: "png" });
  const file = `${fig}/${sheetName.toLowerCase().replace(/[^a-z0-9]+/g, "_")}_v01.png`;
  await fs.writeFile(file, new Uint8Array(await blob.arrayBuffer()));
  renders.push({ sheet: sheetName, range, file });
}
await fs.writeFile(`${qc}/audit_render_v01.json`, `${JSON.stringify({ status: "PASS", renders }, null, 2)}\n`, "utf8");

const xlsx = await SpreadsheetFile.exportXlsx(wb);
await xlsx.save(exportPath);
await fs.copyFile(exportPath, finalPath);

const imported = await SpreadsheetFile.importXlsx(await FileBlob.load(finalPath));
const postStructure = await imported.inspect({ kind: "workbook,sheet,table", maxChars: 16000, tableMaxRows: 5, tableMaxCols: 12, tableMaxCellChars: 90 });
const postSummary = await imported.inspect({ kind: "region", sheetId: "Summary", range: "A1:L36", maxChars: 14000 });
const postErrors = await imported.inspect({ kind: "match", searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!", options: { useRegex: true, maxResults: 200 }, summary: "D10D post-import formula error scan" });
const postPreview = await imported.render({ sheetName: "Summary", range: "A1:L36", scale: 1.0, format: "png" });
await fs.writeFile(`${fig}/summary_post_v01.png`, new Uint8Array(await postPreview.arrayBuffer()));
const postText = postStructure.ndjson || String(postStructure);
const summaryText = postSummary.ndjson || String(postSummary);
const errorText = postErrors.ndjson || String(postErrors);
const postGates = {
  seven_sheets: /"sheets"\s*:\s*7/.test(postText),
  title_readback: postText.includes("D10D zero-opportunity source attribution"),
  d0_readback: summaryText.includes("-26.285067058946254"),
  no_formula_errors: /matched\s+0\s+entries/i.test(errorText),
};
const postStatus = Object.values(postGates).every(Boolean) ? "PASS" : "FAIL";
await fs.writeFile(`${qc}/xlsx_validation_v01.json`, `${JSON.stringify({ status: postStatus, gates: postGates, library: "@oai/artifact-tool", workbook: finalPath, bytes: (await fs.stat(finalPath)).size, structure: postText, summary: summaryText, errors: errorText, preview: `${fig}/summary_post_v01.png` }, null, 2)}\n`, "utf8");
console.log(JSON.stringify({ status: postStatus, gates: postGates, workbook: finalPath, sheets: 7, renders: renders.length }, null, 2));
if (postStatus !== "PASS") process.exitCode = 1;
