import fs from "node:fs/promises";
import path from "node:path";
import { Workbook } from "@oai/artifact-tool";

const outDir=String.raw`C:\range_paper\05_qc\q1_fia_support_legal_opportunity_operator_v01_1_work`;
const qcDir=String.raw`C:\range_paper\99_tmp\q1_fia_support_legal_opportunity_operator_v01_1\artifact_tool_qc`;
const sample=String.raw`C:\range_paper\99_tmp\q1_fia_support_legal_opportunity_operator_v01_1\LEGAL_OPPORTUNITY_F0_CLASSIFICATION_SAMPLE_v01_1.csv`;
const files=[
  "LEGAL_OPPORTUNITY_STATE_DICTIONARY_v01_1.csv",
  "LEGAL_OPPORTUNITY_FIELD_BINDING_v01_1.csv",
  "LEGAL_OPPORTUNITY_SOURCE_RELATIONSHIP_SPEC_v01_1.csv",
  "LAYER2_SUBSTRATE_SCHEMA_v01_1.csv",
  "LAYER2_SUBSTRATE_SOURCE_TRACEABILITY_v01_1.csv",
  "LEGAL_OPPORTUNITY_F0_CLASSIFICATION_SUMMARY_v01_1.csv",
  "LEGAL_OPPORTUNITY_A_B_SUMMARY_v01_1.csv",
  "LEGAL_OPPORTUNITY_UNRESOLVED_STATES_v01_1.csv",
  "LEGAL_OPPORTUNITY_DIAMETER_FRAME_RULES_v01_1.csv",
  "LEGAL_OPPORTUNITY_SOURCE_AUTHORITY_GAPS_v01_1.csv",
  "RESTART_CHECKPOINT_LEDGER_v01_1.csv",
  "LEGAL_OPPORTUNITY_FIREWALL_QC_v01_1.csv",
  "LEGAL_OPPORTUNITY_INVARIANT_QC_v01_1.csv",
  "WORK_PROVENANCE_v01_1.csv",
  "SHA256SUMS.csv",
  "TRANSFER_MANIFEST_v01_1.csv",
];
await fs.mkdir(qcDir,{recursive:true});
const inputs=[...files.map(name=>({name,file:path.join(outDir,name)})),{name:"LEGAL_OPPORTUNITY_F0_CLASSIFICATION_SAMPLE_v01_1.csv",file:sample}];
const results=[];
for(const item of inputs){
  const txt=await fs.readFile(item.file,"utf8");
  const wb=await Workbook.fromCSV(txt,{sheetName:"Data"});
  wb.recalculate();
  const inspect=await wb.inspect({kind:"workbook,sheet,table",maxChars:5000,tableMaxRows:10,tableMaxCols:14,tableMaxCellChars:120});
  const errors=await wb.inspect({kind:"match",searchTerm:"#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!",options:{useRegex:true,maxResults:100},summary:`formula error scan ${item.name}`});
  const png=await wb.render({sheetName:"Data",range:"A1:L20",scale:1.1,format:"png"});
  const preview=path.join(qcDir,item.name.replace(/\.csv$/i,".png"));
  await fs.writeFile(preview,new Uint8Array(await png.arrayBuffer()));
  const errorText=String(errors.ndjson??"");
  if(/#REF!|#DIV\/0!|#VALUE!|#NAME\?|#N\/A|#NUM!|#NULL!|#SPILL!|#CALC!/.test(errorText)) throw new Error(`spreadsheet error marker in ${item.name}`);
  results.push({file:item.name,preview,inspect:String(inspect.ndjson??"").slice(0,5000),status:"PASS"});
}
await fs.writeFile(path.join(qcDir,"artifact_tool_csv_verification.json"),JSON.stringify({artifactTool:"@oai/artifact-tool",verifiedCsvFiles:results.length,files:results,status:"PASS"},null,2));
console.log(JSON.stringify({status:"PASS",verifiedCsvFiles:results.length,qcDir},null,2));
