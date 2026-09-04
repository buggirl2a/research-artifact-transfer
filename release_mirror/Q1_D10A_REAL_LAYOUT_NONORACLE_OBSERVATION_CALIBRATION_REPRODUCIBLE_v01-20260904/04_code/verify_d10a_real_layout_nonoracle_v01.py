#!/usr/bin/env python3
"""Independent file-level verifier for the frozen D10A delivery."""

from __future__ import annotations

import csv
import gzip
import json
import math
from collections import Counter
from pathlib import Path


ROOT=Path(r"C:\range_paper")
OUT=ROOT/"04_derived"/"d10a_real_layout_nonoracle_v01"
QC=ROOT/"05_qc"/"d10a_real_layout_nonoracle_v01"
SRC=ROOT/"06_src"/"d10a_real_layout_nonoracle_v01"


def rows(path):
    with path.open("r",encoding="utf-8-sig",newline="") as handle:
        yield from csv.DictReader(handle)


def main():
    checks=[]
    def add(check_id,observed,expected,ok,details=""):
        checks.append({"check_id":check_id,"observed":observed,"expected":expected,"status":"PASS" if ok else "FAIL","details":details})

    builder=(SRC/"build_d10a_real_layout_nonoracle_v01.py").read_text(encoding="utf-8").lower()
    forbidden_a="sp"+"cd"; forbidden_b="tr"+"ee"
    add("EXECUTABLE_FORBIDDEN_IDENTITY_TOKEN",sum(builder.count(x) for x in (forbidden_a,forbidden_b)),0,forbidden_a not in builder and forbidden_b not in builder)
    query_tables={"plot","pop_plot_stratum_assgn","cond","subplot"}
    add("EXECUTABLE_SQL_ALLOWLIST_DECLARED",";".join(sorted(query_tables)),"four species-blind tables",all(name in builder for name in query_tables))

    layout_path=OUT/"Q1_D10A_REAL_F0_OPPORTUNITY_LAYOUT_v01.csv"
    count=legit=cell_fail=0; plot_keys=set(); fold_legit=Counter(); cells=set(); forbidden_headers=[]
    with layout_path.open("r",encoding="utf-8",newline="") as handle:
        reader=csv.DictReader(handle); forbidden_headers=[name for name in reader.fieldnames if "species" in name.lower() or forbidden_a in name.lower()]
        for row in reader:
            count+=1; plot_keys.add(row["plot_cn"])
            if row["base_legitimate_opportunity_flag"]=="YES":
                legit+=1; fold_legit[row["fold"]]+=1; cells.add(row["cell_50km"])
            ix=math.floor(float(row["x_m"])/50000.0); iy=math.floor(float(row["y_m"])/50000.0)
            if row["cell_50km"]!=f"50km_{ix}_{iy}": cell_fail+=1
    add("LAYOUT_ROW_COUNT",count,338619,count==338619)
    add("LAYOUT_UNIQUE_PLOT_KEYS",len(plot_keys),count,len(plot_keys)==count)
    add("LAYOUT_LEGITIMATE_OPPORTUNITIES",legit,134846,legit==134846,details=json.dumps(fold_legit,sort_keys=True))
    add("LAYOUT_50KM_CELL_RULE_FAILURES",cell_fail,0,cell_fail==0)
    add("LAYOUT_FORBIDDEN_RESULT_COLUMNS",";".join(forbidden_headers),"none",not forbidden_headers)

    manifest=list(rows(OUT/"Q1_D10A_SYNTHETIC_WORLD_MANIFEST_v01.csv"))
    add("SYNTHETIC_MANIFEST_ROWS",len(manifest),432,len(manifest)==432)
    ids={row["synthetic_species_id"] for row in manifest}; combos={(row["world"],row["observation_regime"]) for row in manifest}
    add("SYNTHETIC_SPECIES_COUNT",len(ids),72,len(ids)==72)
    add("SYNTHETIC_WORLD_REGIME_CLOSURE",len(combos),6,len(combos)==6)
    pair_check=all(len({int(row["true_support_cells"]) for row in manifest if row["synthetic_species_id"]==sid})==1 for sid in ids)
    add("PAIRED_SUPPORT_SIZE_IDENTITY",pair_check,True,pair_check)

    support=list(rows(OUT/"Q1_D10A_SUPPORT_CALIBRATION_RESULTS_v01.csv"))
    add("SUPPORT_RESULT_ROWS",len(support),2592,len(support)==2592)
    support_keys={(r["model"],r["world"],r["observation_regime"],r["orientation"],r["synthetic_species_id"]) for r in support}
    add("SUPPORT_RESULT_UNIQUE_KEYS",len(support_keys),len(support),len(support_keys)==len(support))
    finite_fields=["brier_score","log_loss","expected_support_size","expected_support_size_bias","occupied_cell_recall","precision","iou_jaccard","posterior_entropy_mean"]
    bad_finite=sum(not math.isfinite(float(r[field])) for r in support for field in finite_fields)
    bad_bounds=sum(not (0<=float(r[field])<=1) for r in support for field in ("brier_score","occupied_cell_recall","precision","iou_jaccard"))
    add("SUPPORT_FINITE_METRICS",bad_finite,0,bad_finite==0)
    add("SUPPORT_BOUNDED_METRICS",bad_bounds,0,bad_bounds==0)

    leakage=list(rows(OUT/"Q1_D10A_LEAKAGE_AUDIT_RESULTS_v01.csv"))
    add("LEAKAGE_RESULT_ROWS",len(leakage),180,len(leakage)==180)
    leak_keys={(r["model"],r["world"],r["observation_regime"],r["orientation"],r["split_seed"]) for r in leakage}
    add("LEAKAGE_UNIQUE_KEYS",len(leak_keys),len(leakage),len(leak_keys)==len(leakage))
    coverage_bad=sum(not (0<=float(r[field])<=1) for r in leakage for field in ("geometry_latent_truth_coverage","geometry_observed_map_coverage","world0_latent_truth_coverage","world0_observed_map_coverage"))
    add("LEAKAGE_COVERAGE_BOUNDS",coverage_bad,0,coverage_bad==0)

    comparison=list(rows(OUT/"Q1_D10A_MODEL_COMPARISON_v01.csv"))
    add("MODEL_COMPARISON_ROWS",len(comparison),36,len(comparison)==36)
    add("NO_MODEL_SELECTED",sum(r["model_selected"]!="NO_MAINLINE_DECISION_REQUIRED" for r in comparison),0,all(r["model_selected"]=="NO_MAINLINE_DECISION_REQUIRED" for r in comparison))
    add("NO_SCIENTIFIC_PASS_FAIL",sum(r["scientific_pass_fail"]!="NOT_DEFINED" for r in comparison),0,all(r["scientific_pass_fail"]=="NOT_DEFINED" for r in comparison))

    posterior_path=OUT/"Q1_D10A_POSTERIOR_OCCUPANCY_SUMMARY_v01.csv.gz"
    posterior_rows=bad_probability=bad_count=pinned_fail=0
    with gzip.open(posterior_path,"rt",encoding="utf-8",newline="") as handle:
        for row in csv.DictReader(handle):
            posterior_rows+=1; p=float(row["posterior_occupancy_probability"]); n=int(row["source_opportunities_N"]); k=int(row["source_positive_encounters_K"])
            bad_probability+=int(not (0<=p<=1)); bad_count+=int(k<0 or n<0 or k>n)
            if k>0 and row["model"] in {"M1","M2"}: pinned_fail+=int(p<0.999)
    expected=1296*(2913+2855)
    add("POSTERIOR_CELL_ROWS",posterior_rows,expected,posterior_rows==expected)
    add("POSTERIOR_PROBABILITY_BOUNDS",bad_probability,0,bad_probability==0)
    add("POSTERIOR_HISTORY_COUNT_BOUNDS",bad_count,0,bad_count==0)
    add("POSTERIOR_POSITIVE_PINNING",pinned_fail,0,pinned_fail==0)

    inputs=list(rows(QC/"D10A_INPUT_IDENTITY_v01.csv"))
    blocking_fail=sum(row["blocking"]=="YES" and row["status"]!="PASS" for row in inputs)
    benchmark_mismatch=sum(row["check_id"]=="E2C_LOCAL_REFERENCE_HASH_MISMATCH" and row["status"]=="FAIL" and row["blocking"]=="NO" for row in inputs)
    add("BLOCKING_INPUT_FAILURES",blocking_fail,0,blocking_fail==0)
    add("DECLARED_NONBLOCKING_E2C_MISMATCH",benchmark_mismatch,1,benchmark_mismatch==1)

    overall=all(row["status"]=="PASS" for row in checks)
    result={"task_id":"D10A_REAL_LAYOUT_NONORACLE_OBSERVATION_CALIBRATION_v01","validation_status":"PASS" if overall else "FAIL","terminal_status":"CALIBRATION_COMPLETE_READY_FOR_MAINLINE_MODEL_FREEZE" if overall else "IMPLEMENTATION_BLOCKED","checks":checks}
    (QC/"D10A_INDEPENDENT_VALIDATION_v01.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    with (QC/"D10A_INDEPENDENT_VALIDATION_CHECKS_v01.csv").open("w",encoding="utf-8",newline="") as handle:
        writer=csv.DictWriter(handle,fieldnames=["check_id","observed","expected","status","details"],lineterminator="\n"); writer.writeheader(); writer.writerows(checks)
    print(json.dumps({"validation_status":result["validation_status"],"checks":len(checks),"posterior_rows":posterior_rows},indent=2))
    if not overall: raise SystemExit(1)


if __name__=="__main__":
    main()
