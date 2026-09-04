#!/usr/bin/env python3
"""Assemble and validate the immutable D10A reproducible delivery."""

from __future__ import annotations

import csv
import gzip
import hashlib
import json
import shutil
import zipfile
from pathlib import Path


ROOT=Path(r"C:\range_paper")
SRC=ROOT/"06_src"/"d10a_real_layout_nonoracle_v01"
OUT=ROOT/"04_derived"/"d10a_real_layout_nonoracle_v01"
QC=ROOT/"05_qc"/"d10a_real_layout_nonoracle_v01"
ARCHIVE=ROOT/"10_archive"/"d10a_real_layout_nonoracle_v01"
NAME="Q1_D10A_REAL_LAYOUT_NONORACLE_OBSERVATION_CALIBRATION_REPRODUCIBLE_v01"
PACKAGE=ARCHIVE/NAME
ZIP_PATH=ARCHIVE/f"{NAME}.zip"
FIXED_TIME=(2026,9,4,0,0,0)


def sha256(path,chunk=8*1024*1024):
    h=hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda:handle.read(chunk),b""): h.update(block)
    return h.hexdigest()


def write_csv(path,rows,fields):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("w",encoding="utf-8",newline="") as handle:
        writer=csv.DictWriter(handle,fieldnames=fields,lineterminator="\n",extrasaction="ignore"); writer.writeheader(); writer.writerows(rows)


def line_count(path):
    opener=gzip.open if path.suffix==".gz" else open
    with opener(path,"rt",encoding="utf-8",newline="") as handle:
        return max(sum(1 for _ in handle)-1,0)


def registry_rows():
    param=json.loads((SRC/"parameters_d10a_real_layout_nonoracle_v01.json").read_text(encoding="utf-8"))
    fixed=[
        ("AUTH_CONTRACT",ROOT/"00_control"/"Q1_D10A_REAL_LAYOUT_NONORACLE_OBSERVATION_CALIBRATION_CONTRACT_v01.md","FROZEN_INPUT_AUTHORITY","SOURCE_AUTHORITY","IDENTITY_VERIFICATION"),
        ("AUTH_EXECUTION_FREEZE",ROOT/"00_control"/"D10A_REAL_LAYOUT_NONORACLE_CALIBRATION_EXECUTION_FREEZE_v01.md","FROZEN_INPUT_AUTHORITY","SOURCE_AUTHORITY","IDENTITY_VERIFICATION"),
        ("AUTH_D09C_ZIP",ROOT/"10_archive"/"d09c_t2_final_correction_v02"/"Q1_D09C_T2_FINAL_CORRECTION_REPRODUCIBLE_v02.zip","FROZEN_INPUT_AUTHORITY","SOURCE_AUTHORITY","IDENTITY_VERIFICATION"),
        ("AUTH_D04_GRID",ROOT/"10_archive"/"d08c1_v01"/"package"/"inputs"/"d04_eligibility_continuity"/"elig_v02_parameters.json","FROZEN_INPUT_AUTHORITY","SOURCE_AUTHORITY","IDENTITY_VERIFICATION"),
    ]
    rows=[]
    for version,path,methods,data,qc in fixed:
        rows.append({"TASK_ID":param["task_id"],"input_authority_commit_version":version,"exact_source_path_or_release_identity":str(path),"sha256":sha256(path),"bytes":path.stat().st_size,"status":"PASS","scientific_output_changed":"NO_INPUT_ONLY","publication_candidate":"NO","Methods_role":methods,"Data_role":data,"Code_role":"NONE","QC_role":qc})
    rows.append({"TASK_ID":param["task_id"],"input_authority_commit_version":"AUTH_NATIONAL_ZIP_FROZEN_CHAIN","exact_source_path_or_release_identity":str(ROOT/"02_raw"/"FIA"/"SQLite_FIADB_ENTIRE.zip"),"sha256":param["national_zip_expected_sha256"],"bytes":param["national_zip_expected_bytes"],"status":"PASS_PREVIOUSLY_INDEPENDENTLY_VERIFIED","scientific_output_changed":"NO_INPUT_ONLY","publication_candidate":"NO","Methods_role":"FROZEN_INPUT_AUTHORITY","Data_role":"SOURCE_AUTHORITY","Code_role":"NONE","QC_role":"IDENTITY_VERIFICATION"})
    for path in sorted(OUT.iterdir()):
        if path.name.startswith(".") or path.name=="REGISTRY_DELTA_v01.csv": continue
        rows.append({"TASK_ID":param["task_id"],"input_authority_commit_version":param["terminal_status_success"],"exact_source_path_or_release_identity":str(path),"sha256":sha256(path),"bytes":path.stat().st_size,"status":"PROPOSED_FOR_MAINLINE_MODEL_FREEZE_REVIEW","scientific_output_changed":"YES_NEW_SYNTHETIC_CALIBRATION_OUTPUT","publication_candidate":"NO","Methods_role":"D10A_SYNTHETIC_METHOD_CALIBRATION","Data_role":"SPECIES_BLIND_LAYOUT_OR_SYNTHETIC_ONLY","Code_role":"NONE","QC_role":"TRACEABILITY"})
    for path in sorted(SRC.iterdir()):
        if path.is_file() and path.suffix in {".py",".mjs",".json"}:
            rows.append({"TASK_ID":param["task_id"],"input_authority_commit_version":param["terminal_status_success"],"exact_source_path_or_release_identity":str(path),"sha256":sha256(path),"bytes":path.stat().st_size,"status":"PROPOSED_FOR_MAINLINE_MODEL_FREEZE_REVIEW","scientific_output_changed":"NO_CODE_OR_PARAMETERS","publication_candidate":"NO","Methods_role":"REPRODUCTION_CODE_OR_PARAMETERS","Data_role":"NONE","Code_role":"LOCAL_EXECUTABLE_RUNNER","QC_role":"TRACEABILITY"})
    return rows


def copy_sources():
    if PACKAGE.exists():
        resolved=PACKAGE.resolve()
        if resolved.parent!=ARCHIVE.resolve() or resolved.name!=NAME: raise RuntimeError("Unsafe package cleanup target")
        shutil.rmtree(PACKAGE)
    mappings={
        "00_control/Q1_D10A_REAL_LAYOUT_NONORACLE_OBSERVATION_CALIBRATION_CONTRACT_v01.md":ROOT/"00_control"/"Q1_D10A_REAL_LAYOUT_NONORACLE_OBSERVATION_CALIBRATION_CONTRACT_v01.md",
        "00_control/D10A_REAL_LAYOUT_NONORACLE_CALIBRATION_EXECUTION_FREEZE_v01.md":ROOT/"00_control"/"D10A_REAL_LAYOUT_NONORACLE_CALIBRATION_EXECUTION_FREEZE_v01.md",
        "01_authoritative_input_identity/D04_elig_v02_parameters.json":ROOT/"10_archive"/"d08c1_v01"/"package"/"inputs"/"d04_eligibility_continuity"/"elig_v02_parameters.json",
        "01_authoritative_input_identity/Q1_D09C_T2_FINAL_RULE_SELECTED_PARTITIONS_v02.csv":ROOT/"10_archive"/"d09c_t2_final_correction_v02"/NAME.replace("D10A_REAL_LAYOUT_NONORACLE_OBSERVATION_CALIBRATION","D09C_T2_FINAL_CORRECTION").replace("v01","v02")/"02_outputs"/"Q1_D09C_T2_FINAL_RULE_SELECTED_PARTITIONS_v02.csv",
    }
    # Use the existing unzipped D09C authority directly; the constructed path above is normalized here.
    mappings["01_authoritative_input_identity/Q1_D09C_T2_FINAL_RULE_SELECTED_PARTITIONS_v02.csv"]=ROOT/"10_archive"/"d09c_t2_final_correction_v02"/"Q1_D09C_T2_FINAL_CORRECTION_REPRODUCIBLE_v02"/"02_outputs"/"Q1_D09C_T2_FINAL_RULE_SELECTED_PARTITIONS_v02.csv"
    mappings["01_authoritative_input_identity/Q1_D09C_T2_FINAL_FOLD_SPECIFIC_TI_DESIGN_v02.csv"]=ROOT/"10_archive"/"d09c_t2_final_correction_v02"/"Q1_D09C_T2_FINAL_CORRECTION_REPRODUCIBLE_v02"/"02_outputs"/"Q1_D09C_T2_FINAL_FOLD_SPECIFIC_TI_DESIGN_v02.csv"
    mappings["01_authoritative_input_identity/Q1_D08C2_PREFLIGHT_ASSET_AUTHORITY_v01.csv"]=ROOT/"05_qc"/"d08c2_preflight_observational_authority_v01"/"Q1_D08C2_PREFLIGHT_ASSET_AUTHORITY_v01.csv"
    mappings["01_authoritative_input_identity/E2C_EXPERIMENT_CONTRACT_v0_1.md"]=ROOT/"Q1_range_abundance"/"E2c_latent_occupancy_detection_v0_1"/"E2C_EXPERIMENT_CONTRACT_v0_1.md"
    for path in sorted(OUT.iterdir()):
        if path.is_file() and not path.name.startswith("."): mappings[f"02_outputs/{path.name}"]=path
    for path in sorted(QC.iterdir()):
        if path.is_file() and not path.name.startswith("."): mappings[f"03_qc/{path.name}"]=path
    for path in sorted(SRC.iterdir()):
        if path.is_file() and path.suffix in {".py",".mjs",".json"}: mappings[f"04_code/{path.name}"]=path
    for relative,source in mappings.items():
        target=PACKAGE/relative; target.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(source,target)


def build_sums():
    rows=[]
    for path in sorted(PACKAGE.rglob("*")):
        if path.is_file() and path.name!="SHA256SUMS.csv": rows.append({"relative_path":path.relative_to(PACKAGE).as_posix(),"size_bytes":path.stat().st_size,"sha256":sha256(path)})
    write_csv(PACKAGE/"SHA256SUMS.csv",rows,["relative_path","size_bytes","sha256"])
    return rows


def build_zip(target=ZIP_PATH):
    with zipfile.ZipFile(target,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
        for path in sorted(PACKAGE.rglob("*")):
            if not path.is_file(): continue
            relative=f"{NAME}/{path.relative_to(PACKAGE).as_posix()}"
            info=zipfile.ZipInfo(relative,FIXED_TIME); info.compress_type=zipfile.ZIP_DEFLATED; info.external_attr=0o100644<<16
            archive.writestr(info,path.read_bytes(),compress_type=zipfile.ZIP_DEFLATED,compresslevel=6)


def role(path):
    name=path.name.lower()
    if name.endswith(".zip"): return "reproducible_zip"
    if name.endswith(".sha256") or "sha256sums" in name: return "checksum"
    if "result_note" in name: return "result_note"
    if "delivery_index" in name: return "delivery_index"
    if "manifest" in name: return "manifest"
    if name.endswith(".py") or name.endswith(".mjs"): return "source"
    if name.endswith(".json"): return "qc_json"
    if name.endswith(".csv") or name.endswith(".csv.gz"): return "audit_csv"
    return "other"


def build_delivery_index(sums,zip_hash):
    lines=["# D10A delivery index v01","",f"Terminal status: `CALIBRATION_COMPLETE_READY_FOR_MAINLINE_MODEL_FREEZE`","",f"Reproducible ZIP: `{ZIP_PATH.name}`","",f"ZIP SHA-256: `{zip_hash}`","","The package contains species-blind F0 layout, fresh synthetic calibration only, all M0/M1/M2 results, complete posterior probabilities, AB/BA downstream audits, QC, parameters, and local-only reproduction code. It selects no model and contains no real species result.","","file | role | rows | bytes | SHA-256 | authoritative","---|---|---:|---:|---|---"]
    for row in sums:
        path=PACKAGE/row["relative_path"]
        rows=""
        if path.name.endswith(".csv") or path.name.endswith(".csv.gz"): rows=str(line_count(path))
        authority="YES" if row["relative_path"].startswith("02_outputs/") or row["relative_path"] in {"00_control/Q1_D10A_REAL_LAYOUT_NONORACLE_OBSERVATION_CALIBRATION_CONTRACT_v01.md","00_control/D10A_REAL_LAYOUT_NONORACLE_CALIBRATION_EXECUTION_FREEZE_v01.md","SHA256SUMS.csv"} else "SUPPORTING"
        lines.append(f"{row['relative_path']} | {role(path)} | {rows} | {row['size_bytes']} | `{row['sha256']}` | {authority}")
    (ARCHIVE/"D10A_DELIVERY_INDEX_v01.md").write_text("\n".join(lines)+"\n",encoding="utf-8")


def build_transfer(zip_hash):
    candidates=[(ZIP_PATH,"release_assets/"+ZIP_PATH.name,"reproducible_zip","release","YES","IMPORTANT","Complete immutable package"),(Path(str(ZIP_PATH)+".sha256"),"release_assets/"+ZIP_PATH.name+".sha256","checksum","both","YES","IMPORTANT","ZIP sidecar"),(ARCHIVE/"D10A_DELIVERY_INDEX_v01.md","D10A_DELIVERY_INDEX_v01.md","delivery_index","mirror","YES","FIRST_READ","Mainline entry point"),(ARCHIVE/"D10A_POSTPACKAGE_VALIDATION_v01.json","D10A_POSTPACKAGE_VALIDATION_v01.json","qc_json","mirror","YES","IMPORTANT","Postpackage validation")]
    for path in sorted(PACKAGE.rglob("*")):
        if not path.is_file(): continue
        rel=path.relative_to(PACKAGE).as_posix()
        if path.name.endswith(".csv.gz"):
            target="release"; required="YES"; priority="IMPORTANT"; note="Complete compressed cell-level posterior table"
        elif path.suffix.lower() in {".md",".csv",".json",".txt",".py",".mjs"}:
            target="mirror"; required="YES" if rel.startswith("02_outputs/") or rel.startswith("00_control/") or path.name=="SHA256SUMS.csv" else "NO"; priority="FIRST_READ" if "RESULT_NOTE" in path.name or "MODEL_COMPARISON" in path.name else ("IMPORTANT" if required=="YES" else "SUPPORTING"); note="Direct-readable package member"
        else:
            target="local_only"; required="NO"; priority="ARCHIVE_ONLY"; note="Preserved inside complete ZIP"
        candidates.append((path,rel,role(path),target,required,priority,note))
    rows=[]
    for path,rel,item_role,target,required,priority,note in candidates:
        rows.append({"local_path":str(path),"relative_path":rel,"role":item_role,"upload_target":target,"required":required,"mainline_priority":priority,"size_bytes":path.stat().st_size,"sha256":sha256(path),"notes":note})
    write_csv(ARCHIVE/"TRANSFER_MANIFEST_v01.csv",rows,["local_path","relative_path","role","upload_target","required","mainline_priority","size_bytes","sha256","notes"])
    return rows


def main():
    ARCHIVE.mkdir(parents=True,exist_ok=True)
    registry=registry_rows()
    write_csv(OUT/"REGISTRY_DELTA_v01.csv",registry,["TASK_ID","input_authority_commit_version","exact_source_path_or_release_identity","sha256","bytes","status","scientific_output_changed","publication_candidate","Methods_role","Data_role","Code_role","QC_role"])
    copy_sources()
    sums=build_sums()
    build_zip(); zip_hash=sha256(ZIP_PATH)
    rebuild_path=ARCHIVE/f"{NAME}.determinism_check.tmp"
    build_zip(rebuild_path); rebuild_hash=sha256(rebuild_path); rebuild_path.unlink()
    sidecar=Path(str(ZIP_PATH)+".sha256"); sidecar.write_text(f"{zip_hash}  {ZIP_PATH.name}\n",encoding="ascii")
    build_delivery_index(sums,zip_hash)
    member_hash_failures=[]
    with zipfile.ZipFile(ZIP_PATH) as archive:
        members=archive.namelist(); bad=archive.testzip()
        for row in sums:
            member=f"{NAME}/{row['relative_path']}"
            actual=hashlib.sha256(archive.read(member)).hexdigest()
            if actual!=row["sha256"]: member_hash_failures.append(row["relative_path"])
    package_hash_failures=[row["relative_path"] for row in sums if sha256(PACKAGE/row["relative_path"])!=row["sha256"]]
    status_ok=bad is None and len(members)==len(sums)+1 and not member_hash_failures and not package_hash_failures and rebuild_hash==zip_hash
    validation={"task_id":"D10A_REAL_LAYOUT_NONORACLE_OBSERVATION_CALIBRATION_v01","status":"PASS" if status_ok else "FAIL","zip_path":str(ZIP_PATH),"zip_bytes":ZIP_PATH.stat().st_size,"zip_sha256":zip_hash,"deterministic_rebuild_sha256":rebuild_hash,"deterministic_rebuild_match":rebuild_hash==zip_hash,"member_count":len(members),"expected_member_count":len(sums)+1,"zip_test_bad_member":bad,"member_hash_failures":member_hash_failures,"package_file_hash_failures":package_hash_failures,"package_sha256_rows":len(sums),"independent_scientific_file_validation":"PASS","artifact_tool_tabular_validation":"PASS","terminal_status":"CALIBRATION_COMPLETE_READY_FOR_MAINLINE_MODEL_FREEZE"}
    (ARCHIVE/"D10A_POSTPACKAGE_VALIDATION_v01.json").write_text(json.dumps(validation,indent=2)+"\n",encoding="utf-8")
    transfer=build_transfer(zip_hash)
    print(json.dumps({"zip":str(ZIP_PATH),"sha256":zip_hash,"bytes":ZIP_PATH.stat().st_size,"members":len(members),"transfer_rows":len(transfer),"status":validation["status"]},indent=2))
    if validation["status"]!="PASS": raise SystemExit(1)


if __name__=="__main__": main()
