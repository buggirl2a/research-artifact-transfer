import fs from "node:fs/promises";
import path from "node:path";
import { Workbook } from "@oai/artifact-tool";

const outDir = String.raw`C:\range_paper\05_qc\d10fb13_v01_work_component_transportability_diagnostic`;
const qcDir = String.raw`C:\range_paper\99_tmp\d10fb13_v01\artifact_tool_qc`;
const files = [
  "B13_LEVEL_ROUTE_SUMMARY_v01.csv",
  "B13_COARSE_GRAIN_SUMMARY_v01.csv",
  "B13_Q1_97_DIRECT_SUBGROUP_SUMMARY_v01.csv",
  "B13_COMPONENT_DISPOSITION_MATRIX_v01.csv",
  "B13_PROVENANCE_v01.csv",
  "B13_OPEN_ITEMS_v01.csv",
  "B13_INVARIANT_QC_v01.csv",
  "B13_REFERENCE_FIREWALL_QC_v01.csv",
  "SHA256SUMS.csv",
  "TRANSFER_MANIFEST_v01.csv",
];

await fs.mkdir(qcDir, { recursive: true });
const results = [];
for (const name of files) {
  const csvText = await fs.readFile(path.join(outDir, name), "utf8");
  const workbook = await Workbook.fromCSV(csvText, { sheetName: "Data" });
  workbook.recalculate();
  const summary = await workbook.inspect({
    kind: "workbook,sheet,table",
    maxChars: 5000,
    tableMaxRows: 8,
    tableMaxCols: 14,
    tableMaxCellChars: 100,
  });
  const errors = await workbook.inspect({
    kind: "match",
    searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!",
    options: { useRegex: true, maxResults: 100 },
    summary: `formula error scan ${name}`,
  });
  const preview = await workbook.render({ sheetName: "Data", autoCrop: "all", scale: 0.8, format: "png" });
  const previewName = `${name.replace(/\.csv$/i, "")}.png`;
  await fs.writeFile(path.join(qcDir, previewName), new Uint8Array(await preview.arrayBuffer()));
  const errorText = String(errors.ndjson ?? "");
  const bad = /#REF!|#DIV\/0!|#VALUE!|#NAME\?|#N\/A|#NUM!|#NULL!|#SPILL!|#CALC!/.test(errorText);
  if (bad) throw new Error(`Spreadsheet formula error marker found in ${name}: ${errorText.slice(0, 1000)}`);
  results.push({
    file: name,
    csvBytes: Buffer.byteLength(csvText, "utf8"),
    preview: path.join(qcDir, previewName),
    inspect: String(summary.ndjson ?? "").slice(0, 5000),
    errorScan: errorText.slice(0, 2000),
    status: "PASS",
  });
}
await fs.writeFile(path.join(qcDir, "artifact_tool_csv_verification.json"), JSON.stringify({
  artifactTool: "@oai/artifact-tool",
  operation: "import_recalculate_inspect_error_scan_render",
  files: results,
  status: "PASS",
}, null, 2));
console.log(JSON.stringify({ status: "PASS", verifiedCsvFiles: results.length, qcDir }, null, 2));
