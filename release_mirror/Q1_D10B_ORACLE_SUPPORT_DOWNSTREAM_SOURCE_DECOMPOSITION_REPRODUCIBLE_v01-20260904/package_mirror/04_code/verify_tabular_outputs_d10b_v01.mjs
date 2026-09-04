import fs from "node:fs/promises";
import path from "node:path";
import { Workbook } from "@oai/artifact-tool";

const root = "C:\\range_paper";
const directories = [
  path.join(root, "04_derived", "d10b_oracle_source_decomposition_v01"),
  path.join(root, "05_qc", "d10b_oracle_source_decomposition_v01"),
];
const output = path.join(root, "05_qc", "d10b_oracle_source_decomposition_v01", "D10B_ARTIFACT_TOOL_TABULAR_VALIDATION_v01.json");
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
  const inspected = await workbook.inspect({ kind: "sheet,region", sheetId: "Audit", range: "A1:AZ6", maxChars: 1600, tableMaxRows: 6, tableMaxCols: 52 });
  const used = workbook.worksheets.getItem("Audit").getUsedRange(true);
  const rowCount = used ? used.rowCount : 0;
  const columnCount = used ? used.columnCount : 0;
  results.push({ file: path.basename(file), status: rowCount >= 2 && columnCount >= 2 ? "PASS" : "FAIL", rowCount, columnCount, inspection_chars: inspected.ndjson.length });
}
const status = results.every((row) => row.status === "PASS") ? "PASS" : "FAIL";
await fs.writeFile(output, JSON.stringify({ status, library: "@oai/artifact-tool", files_checked: results.length, results }, null, 2) + "\n", "utf8");
console.log(JSON.stringify({ status, files_checked: results.length }));
if (status !== "PASS") process.exit(1);
