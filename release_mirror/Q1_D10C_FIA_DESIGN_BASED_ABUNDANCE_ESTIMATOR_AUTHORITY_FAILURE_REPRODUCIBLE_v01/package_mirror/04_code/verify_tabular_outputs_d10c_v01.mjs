import fs from "node:fs/promises";
import path from "node:path";
import { Workbook } from "@oai/artifact-tool";

const root = "C:\\range_paper";
const directories = [
  path.join(root, "04_derived", "d10c_fia_design_abundance_v01"),
  path.join(root, "05_qc", "d10c_fia_design_abundance_v01"),
];
const output = path.join(root, "05_qc", "d10c_fia_design_abundance_v01", "D10C_ARTIFACT_TOOL_TABULAR_VALIDATION_v01.json");
const files = [];
for (const directory of directories) {
  for (const name of await fs.readdir(directory)) {
    if (name.toLowerCase().endsWith(".csv")) files.push(path.join(directory, name));
  }
}
files.sort();
const results = [];
for (const file of files) {
  const csvText = await fs.readFile(file, "utf8");
  const workbook = await Workbook.fromCSV(csvText, { sheetName: "Audit" });
  const sheet = workbook.worksheets.getItem("Audit");
  const used = sheet.getUsedRange(true);
  const inspection = await workbook.inspect({ kind: "sheet,region", sheetId: "Audit", range: "A1:AZ6", maxChars: 1600, tableMaxRows: 6, tableMaxCols: 52 });
  results.push({ file: path.basename(file), status: used && used.rowCount >= 2 && used.columnCount >= 2 ? "PASS" : "FAIL", rowCount: used ? used.rowCount : 0, columnCount: used ? used.columnCount : 0, inspection_chars: inspection.ndjson.length });
}
const status = results.every((row) => row.status === "PASS") ? "PASS" : "FAIL";
await fs.writeFile(output, JSON.stringify({ status, library: "@oai/artifact-tool", files_checked: results.length, results }, null, 2) + "\n", "utf8");
console.log(JSON.stringify({ status, files_checked: results.length }));
if (status !== "PASS") process.exit(1);
