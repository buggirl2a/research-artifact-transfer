import fs from "node:fs/promises";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const root = "C:/range_paper/10_archive/d10cr/pkg";
const inputPath = `${root}/out/audit_v01.xlsx`;
const input = await FileBlob.load(inputPath);
const workbook = await SpreadsheetFile.importXlsx(input);

const structure = await workbook.inspect({ kind: "workbook,sheet,table", maxChars: 18000, tableMaxRows: 5, tableMaxCols: 14, tableMaxCellChars: 100 });
const summary = await workbook.inspect({ kind: "region", sheetId: "Summary", range: "A1:J37", maxChars: 16000 });
const checks = await workbook.inspect({ kind: "region", sheetId: "Checks", range: "A1:E13", maxChars: 12000 });
const errors = await workbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!",
  options: { useRegex: true, maxResults: 100 },
  summary: "D10C resume post-import formula error scan",
});

const structureText = structure.ndjson || String(structure);
const summaryText = summary.ndjson || String(summary);
const checksText = checks.ndjson || String(checks);
const errorsText = errors.ndjson || String(errors);
const status = structureText.includes('"sheets":6')
  && summaryText.includes("ABUNDANCE_CALIBRATION_COMPLETE_READY_FOR_MAINLINE_FREEZE")
  && summaryText.includes("0.13294353494439515")
  && structureText.includes("NO_SUPPORT_RECOVERY")
  && errorsText.includes("matched 0 entries") ? "PASS" : "FAIL";

const preview = await workbook.render({ sheetName: "Summary", range: "A1:J37", scale: 1.0, format: "png" });
await fs.writeFile(`${root}/fig/summary_post_v01.png`, new Uint8Array(await preview.arrayBuffer()));
const report = {
  status,
  library: "@oai/artifact-tool",
  input_path: inputPath,
  input_bytes: (await fs.stat(inputPath)).size,
  expected_sheets: 6,
  postimport_preview: `${root}/fig/summary_post_v01.png`,
  structure: structureText,
  summary_region: summaryText,
  checks_region: checksText,
  formula_error_scan: errorsText,
};
await fs.writeFile(`${root}/qc/xlsx_validation_v01.json`, `${JSON.stringify(report, null, 2)}\n`, "utf8");
console.log(JSON.stringify({ status, inputPath, expectedSheets: 6, formulaErrorScan: errorsText }, null, 2));
if (status !== "PASS") process.exitCode = 1;
