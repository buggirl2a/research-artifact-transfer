import fs from "node:fs/promises";
import { gunzipSync } from "node:zlib";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const root = "C:/range_paper/10_archive/d10cr/pkg";
const outDir = `${root}/out`;
const qcDir = `${root}/qc`;
const figDir = `${root}/fig`;

function parseCsv(text) {
  const rows = [];
  let row = [];
  let field = "";
  let quoted = false;
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
  if (clean.length && clean[0].length) clean[0][0] = clean[0][0].replace(/^\uFEFF/, "");
  return clean;
}

async function readCsv(file) {
  const p = `${outDir}/${file}`;
  const text = file.endsWith(".gz")
    ? gunzipSync(await fs.readFile(p)).toString("utf8")
    : await fs.readFile(p, "utf8");
  const rows = parseCsv(text);
  const header = rows[0];
  return rows.slice(1).map((r) => Object.fromEntries(header.map((h, i) => [h, r[i] ?? ""])));
}

const num = (x) => x === "" || x == null ? null : Number(x);
const median = (xs) => {
  const v = xs.filter(Number.isFinite).sort((a, b) => a - b);
  if (!v.length) return null;
  const m = Math.floor(v.length / 2);
  return v.length % 2 ? v[m] : (v[m - 1] + v[m]) / 2;
};

function writeTable(sheet, anchor, matrix, widths = []) {
  const range = sheet.getRangeByIndexes(anchor[0], anchor[1], matrix.length, matrix[0].length);
  range.values = matrix;
  const header = sheet.getRangeByIndexes(anchor[0], anchor[1], 1, matrix[0].length);
  header.format = {
    fill: "#1F4E78",
    font: { name: "Aptos", bold: true, color: "#FFFFFF", size: 10 },
    wrapText: true,
    verticalAlignment: "center",
    borders: { preset: "all", style: "thin", color: "#B4C7E7" },
  };
  header.format.rowHeight = 34;
  const body = sheet.getRangeByIndexes(anchor[0] + 1, anchor[1], Math.max(1, matrix.length - 1), matrix[0].length);
  body.format = {
    font: { name: "Aptos", color: "#1F2937", size: 9 },
    verticalAlignment: "top",
    borders: { preset: "all", style: "thin", color: "#D9E2F3" },
  };
  for (let i = 0; i < matrix[0].length; i += 1) {
    sheet.getRangeByIndexes(anchor[0], anchor[1] + i, matrix.length, 1).format.columnWidth = widths[i] ?? 18;
  }
}

const recovery = await readCsv("recovery_summary_v01.csv");
const common = await readCsv("common_compare_v01.csv");
const metrics = await readCsv("recovery_metrics_v01.csv");
const leakage = await readCsv("leakage_v01.csv.gz");
const checks = await readCsv("../qc/checks_v01.csv".replace("../qc/", "checks_v01.csv")).catch(async () => {
  const rows = parseCsv(await fs.readFile(`${qcDir}/checks_v01.csv`, "utf8"));
  const h = rows[0];
  return rows.slice(1).map((r) => Object.fromEntries(h.map((k, i) => [k, r[i] ?? ""])));
});

const allA1H = metrics.filter((r) => r.layer === "A1").map((r) => num(r.hellinger_distance));
const allA2H = metrics.filter((r) => r.layer === "A2").map((r) => num(r.hellinger_distance));
const allA1W = metrics.filter((r) => r.layer === "A1").map((r) => num(r.sliced_wasserstein_km));
const allA2W = metrics.filter((r) => r.layer === "A2").map((r) => num(r.sliced_wasserstein_km));

const sepByLayer = [];
for (const layer of ["A0", "A1", "A2"]) {
  const values = common.filter((r) => r.layer === layer).map((r) => num(r.strong_minus_null_geometry_gain_pct_median));
  sepByLayer.push([layer, median(values)]);
}

const leakageSummary = leakage
  .filter((r) => r.analysis_level === "POOLED_WITHIN_SPECIES_CORRELATION" && r.layer === "A2" && r.outcome === "p_residual")
  .map((r) => [r.world, r.orientation, r.design_variable, num(r.n), num(r.value), Math.abs(num(r.value))])
  .sort((a, b) => b[5] - a[5]);

const structural = [];
for (const layer of ["A1", "A2"]) {
  for (const world of ["STRONG", "PAIRED_NULL"]) {
    for (const orientation of ["AB", "BA"]) {
      const rows = metrics.filter((r) => r.layer === layer && r.world === world && r.orientation === orientation);
      structural.push([
        layer, world, orientation, rows.length,
        rows.filter((r) => num(r.support_cells_zero_target_fold_plots) > 0).length,
        median(rows.map((r) => num(r.support_truth_mass_fraction_zero_target_fold_plots))),
        Math.max(...rows.map((r) => num(r.support_truth_mass_fraction_zero_target_fold_plots))),
        median(rows.map((r) => num(r.ci95_coverage_positive_exposure))),
      ]);
    }
  }
}

const wb = Workbook.create();
const summary = wb.worksheets.add("Summary");
summary.showGridLines = false;
summary.getRange("A1:H1").merge();
summary.getRange("A1").values = [["Q1 D10C — FIA design-based abundance calibration resume v01"]];
summary.getRange("A1:H1").format = { fill: "#17365D", font: { name: "Aptos Display", bold: true, color: "#FFFFFF", size: 16 }, verticalAlignment: "center" };
summary.getRange("A1:H1").format.rowHeight = 32;
summary.getRange("A3:B11").values = [
  ["Audit fact", "Value"],
  ["Terminal execution status", "ABUNDANCE_CALIBRATION_COMPLETE_READY_FOR_MAINLINE_FREEZE"],
  ["Synthetic species", 72],
  ["F0 plot visits", 338619],
  ["Legal opportunities", 134846],
  ["50-km cells", 3011],
  ["A1 median Hellinger", median(allA1H)],
  ["A2 median Hellinger", median(allA2H)],
  ["A1 median SW (km)", median(allA1W)],
];
summary.getRange("A12:B12").values = [["A2 median SW (km)", median(allA2W)]];
writeTable(summary, [2, 0], summary.getRange("A3:B12").values, [34, 58]);
summary.getRange("B7:B8").format.numberFormat = "#,##0";
summary.getRange("B9:B12").format.numberFormat = "0.0000";

const recChartData = [
  ["Layer", "Median Hellinger", "Median SW km"],
  ["A1", median(allA1H), median(allA1W)],
  ["A2", median(allA2H), median(allA2W)],
];
writeTable(summary, [14, 0], recChartData, [16, 20, 18]);
summary.getRange("B16:C17").format.numberFormat = "0.0000";
const sepData = [["Layer", "STRONG − paired-null gain (pp)"], ...sepByLayer];
writeTable(summary, [19, 0], sepData, [16, 30]);
summary.getRange("B21:B23").format.numberFormat = "0.000";

summary.getRange("A32:J32").merge();
summary.getRange("A32").values = [["Interpretation boundary"]];
summary.getRange("A32:J32").format = { fill: "#D9EAF7", font: { bold: true, color: "#17365D" } };
summary.getRange("A33:J37").merge(true);
summary.getRange("A33:A37").values = [
  ["A2 sharply improves normalized-map recovery over the intentionally broken A1 count layer."],
  ["A2 does not restore the positive A0 STRONG-minus-PAIRED_NULL downstream direction: A0 +6.054 pp, A1 −127.889 pp, A2 −26.285 pp."],
  ["Zero-opportunity target-fold cells are retained as structural limitations and are never repaired."],
  ["No real species, support recovery, estimator selection, scientific threshold, or real Q1 analysis is included."],
  ["These are calibration facts for mainline judgment; this branch assigns no scientific PASS/HOLD/FAIL."],
];
summary.getRange("A33:J37").format = { fill: "#F8FAFC", wrapText: true, font: { color: "#334155", size: 10 } };
summary.freezePanes.freezeRows(1);

const recChart = summary.charts.add("column", summary.getRange("A15:C17"));
recChart.title = "Map recovery: A1 versus A2 (different units)";
recChart.setPosition("D3", "J15");
const sepChart = summary.charts.add("column", summary.getRange("A20:B23"));
sepChart.title = "Downstream STRONG − PAIRED_NULL separation";
sepChart.hasLegend = false;
sepChart.setPosition("D16", "J29");

const recoverySheet = wb.worksheets.add("Recovery");
recoverySheet.showGridLines = false;
const recMatrix = [["layer", "world", "orientation", "n_species", "hellinger_median", "sw_km_median", "relative_rmse_median", "total_mass_relative_error_median"], ...recovery.map((r) => [r.layer, r.world, r.orientation, num(r.n_species), num(r.hellinger_median), num(r.sw_km_median), num(r.relative_rmse_median), num(r.total_mass_relative_error_median)])];
writeTable(recoverySheet, [0, 0], recMatrix, [12, 18, 14, 12, 18, 16, 20, 26]);
recoverySheet.getRange(`D2:H${recMatrix.length}`).format.numberFormat = "0.0000";
recoverySheet.freezePanes.freezeRows(1);

const downstreamSheet = wb.worksheets.add("Downstream");
downstreamSheet.showGridLines = false;
const comHead = ["layer", "D10B equivalent", "regime", "orientation", "n_rep", "strong gain", "null gain", "strong−null", "strong set gain", "null set gain", "set strong−null", "strong coverage", "null coverage"];
const comMatrix = [comHead, ...common.map((r) => [r.layer, r.d10b_equivalent, r.observation_regime, r.orientation, num(r.n_split_replicates), num(r.strong_geometry_gain_pct_median), num(r.paired_null_geometry_gain_pct_median), num(r.strong_minus_null_geometry_gain_pct_median), num(r.strong_predictive_set_gain_pct_median), num(r.paired_null_predictive_set_gain_pct_median), num(r.strong_minus_null_predictive_set_gain_pct_median), num(r.strong_geometry_coverage_median), num(r.paired_null_geometry_coverage_median)])];
writeTable(downstreamSheet, [0, 0], comMatrix, [10, 18, 12, 12, 10, 14, 14, 16, 16, 16, 18, 16, 16]);
downstreamSheet.getRange(`F2:M${comMatrix.length}`).format.numberFormat = "0.0000";
downstreamSheet.freezePanes.freezeRows(1);
downstreamSheet.freezePanes.freezeColumns(4);

const leakageSheet = wb.worksheets.add("Leakage");
leakageSheet.showGridLines = false;
const leakMatrix = [["world", "orientation", "design variable", "n cells", "pooled within-species r", "|r|"], ...leakageSummary];
writeTable(leakageSheet, [0, 0], leakMatrix, [18, 14, 28, 12, 16, 16]);
leakageSheet.getRange(`E2:F${leakMatrix.length}`).format.numberFormat = "0.0000";
leakageSheet.freezePanes.freezeRows(1);

const structuralSheet = wb.worksheets.add("Structural");
structuralSheet.showGridLines = false;
const structMatrix = [["layer", "world", "orientation", "n species", "species with zero-exposure support", "median truth mass fraction in zero cells", "max truth mass fraction in zero cells", "median CI95 coverage, positive exposure"], ...structural];
writeTable(structuralSheet, [0, 0], structMatrix, [10, 18, 14, 12, 28, 28, 28, 30]);
structuralSheet.getRange(`F2:H${structMatrix.length}`).format.numberFormat = "0.0000";
structuralSheet.freezePanes.freezeRows(1);

const checkSheet = wb.worksheets.add("Checks");
checkSheet.showGridLines = false;
const checkMatrix = [["check_id", "status", "observed", "expected", "notes"], ...checks.map((r) => [r.check_id, r.status, r.observed, r.expected, r.notes])];
writeTable(checkSheet, [0, 0], checkMatrix, [34, 12, 24, 24, 64]);
checkSheet.getRange(`B2:B${checkMatrix.length}`).conditionalFormats.add("containsText", { text: "PASS", format: { fill: "#DCFCE7", font: { color: "#166534", bold: true } } });
checkSheet.freezePanes.freezeRows(1);

await fs.mkdir(figDir, { recursive: true });
const inspect = await wb.inspect({ kind: "workbook,sheet,table", maxChars: 18000, tableMaxRows: 8, tableMaxCols: 14, tableMaxCellChars: 100 });
await fs.writeFile(`${qcDir}/audit_inspect_v01.ndjson`, inspect.ndjson, "utf8");
const errors = await wb.inspect({ kind: "match", searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A", options: { useRegex: true, maxResults: 200 }, summary: "D10C resume formula error scan" });
await fs.writeFile(`${qcDir}/audit_errors_v01.ndjson`, errors.ndjson, "utf8");

const renders = [];
for (const [sheetName, range] of [["Summary", "A1:J37"], ["Recovery", "A1:H9"], ["Downstream", "A1:M19"], ["Leakage", `A1:F${Math.min(25, leakMatrix.length)}`], ["Checks", `A1:E${checkMatrix.length}`]]) {
  const blob = await wb.render({ sheetName, range, scale: 1.0, format: "png" });
  const file = `${figDir}/${sheetName.toLowerCase()}_v01.png`;
  await fs.writeFile(file, new Uint8Array(await blob.arrayBuffer()));
  renders.push({ sheet: sheetName, range, file });
}
await fs.writeFile(`${qcDir}/audit_render_v01.json`, JSON.stringify({ status: "PASS", renders }, null, 2) + "\n", "utf8");

const xlsx = await SpreadsheetFile.exportXlsx(wb);
await xlsx.save(`${outDir}/audit_v01.xlsx`);
console.log(JSON.stringify({ status: "PASS", output: `${outDir}/audit_v01.xlsx`, sheets: 6, renders: renders.length }, null, 2));
