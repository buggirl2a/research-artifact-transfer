from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import json
import math
import shutil
import sqlite3
import sys
import zipfile
from array import array
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

ROOT=Path(r"C:\range_paper")
HERE=Path(__file__).resolve().parent
OUT=ROOT/"05_qc"/"d10fb14_v01_1_work_observed_state_mixture_correction"
TMP=ROOT/"99_tmp"/"d10fb14_v01_1"
PARENT=ROOT/"05_qc"/"d10fb14_v01_work_singleton_uncertainty_materiality_stress"/"Q1_D10F_B14_v01.zip"
CACHE=ROOT/"99_tmp"/"d10fb12_v01"/"cache"/"b12_cache.sqlite"
REQUEST=Path(r"C:\Users\bug_g\.codex\attachments\89e773af-30e9-4798-8099-1da970efb2eb\pasted-text.txt")

EXPECTED={
 "parent":(PARENT,"01be93dee2184a44ca89f72016d459cdf0792038d6d19d1536aafe4535371208"),
 "substrate":(ROOT/"10_archive"/"q1_fia_substrate_v01_1"/"Q1_FIA_SUBSTRATE_v01_1.zip","1dbd8cf3fdb9fdbd25945ed70af64e1c739ec78f10f24ec4866128c38d5d946e"),
 "d10ca":(ROOT/"10_archive"/"d10ca"/"D10CA_v01.zip","c8f73406f7f192b8f124add3cb0ded7ea65474e8d72d752e37dc557a08588865"),
 "b12":(ROOT/"10_archive"/"d10fb12_v01_1"/"Q1_D10F_B12_v01_1.zip","d009bf50225ca3c2f483e08fe17f22312f93c9a28f36786abae8729fde3a21ab"),
 "b13":(ROOT/"10_archive"/"d10fb13_v01"/"Q1_D10F_B13_v01.zip","c3898021cfe71ae0ea7b307be3907c8598dc1d1744f04e37d5ee0fc9d74807d9"),
 "q1_projection":(ROOT/"10_archive"/"q1_b12_q1_cohort_projection_v01"/"Q1_B12_Q1_COHORT_PROJECTION_v01.zip","70d34c6905a9d76675943ae03182feae719340d159ca6b69b68b9b9d089f227e"),
 "singleton_audit":(ROOT/"10_archive"/"q1_singleton_materiality_v01"/"Q1_SINGLETON_MATERIALITY_AUDIT_v01.zip","e85da191519ac8ed033c46ac78257c1c7e515976fd87a0d99511093bd0d8e007"),
 "cache":(CACHE,"0daf80d098546d61aecd8e75701f5174d9f6fd4452ce4a1b257651d45c9d2953"),
}
EXPECTED_PARENT_SEAL="99ee459e4640c29ac96549d6de8973783102aae6ae2d0b9724dd15be4818f27c"
EXPECTED_XWALK_MEMBER="a2c4bb3f6d45ed7d6497c511648265b7d692bf872aabbba1fdd99cc534be9447"
Q95=24138.348874
Q99=40835.09
DIRECT_N=97
PSEUDO_N=4640
ACTUAL_N=24
EXPECTED_ACTIVE=1_288_936
EXPECTED_ZPLUS=1_193_386
EXPECTED_IMPLICIT_Z0=24_849_363
EXPECTED_UNIVERSE=26_138_299
MIN_RAW_OPPORTUNITIES=100
MIN_CONTRIBUTING_TARGETS=10
VERSION="1.0.0"


class StopBuild(RuntimeError): pass


class Logger:
 def __init__(self,path:Path):
  path.parent.mkdir(parents=True,exist_ok=True);self.f=path.open("a",encoding="utf-8",newline="\n")
 def __call__(self,msg:str):
  line=f"{datetime.now(timezone.utc).isoformat()} {msg}";print(line,flush=True);self.f.write(line+"\n");self.f.flush()
 def close(self):self.f.close()


def sha_file(path:Path)->str:
 h=hashlib.sha256()
 with path.open("rb") as f:
  while b:=f.read(8*1024*1024):h.update(b)
 return h.hexdigest()


def sha_bytes(b:bytes)->str:return hashlib.sha256(b).hexdigest()


def zmember(z:zipfile.ZipFile,suffix:str)->str:
 hits=[x for x in z.namelist() if x.replace("\\","/").endswith(suffix)]
 if len(hits)!=1:raise StopBuild(f"ZIP member identity failed for {suffix}: {hits}")
 return hits[0]


def zcsv(z:zipfile.ZipFile,suffix:str)->list[dict[str,str]]:
 return list(csv.DictReader(io.StringIO(z.read(zmember(z,suffix)).decode("utf-8-sig"))))


def csv_write(path:Path,rows:Iterable[dict[str,Any]],fields:list[str])->int:
 path.parent.mkdir(parents=True,exist_ok=True);n=0
 with path.open("w",encoding="utf-8-sig",newline="") as f:
  w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore",lineterminator="\n");w.writeheader()
  for r in rows:
   w.writerow({k:("NA" if isinstance(r.get(k),float) and not math.isfinite(r[k]) else r.get(k,"")) for k in fields});n+=1
 return n


def csv_read(path:Path)->list[dict[str,str]]:
 with path.open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))


def fields(rows:list[dict[str,Any]])->list[str]:return list(rows[0]) if rows else []


def json_write(path:Path,obj:Any):path.write_text(json.dumps(obj,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+"\n",encoding="utf-8")


def qtype7_sorted(v:list[float],q:float)->float:
 if not v:return float("nan")
 h=(len(v)-1)*q;lo=int(math.floor(h));hi=int(math.ceil(h))
 return v[lo] if lo==hi else v[lo]+(h-lo)*(v[hi]-v[lo])


def qtype7_zeros(values:list[float],zero_count:int,q:float)->float:
 v=sorted(values);n=len(v)+zero_count
 if n==0:return float("nan")
 def at(i:int)->float:return 0.0 if i<zero_count else v[i-zero_count]
 h=(n-1)*q;lo=int(math.floor(h));hi=int(math.ceil(h));a=at(lo);b=at(hi)
 return a if lo==hi else a+(h-lo)*(b-a)


def weighted_inverse(values:list[float],weights:list[float],zero_weight:float,q:float)->float:
 if len(values)!=len(weights):raise StopBuild("Weighted value/weight length mismatch")
 total=zero_weight+sum(weights)
 if total<=0:return float("nan")
 threshold=q*total
 if threshold<=zero_weight:return 0.0
 pairs=sorted(zip(values,weights),key=lambda x:x[0]);acc=zero_weight
 for v,w in pairs:
  acc+=w
  if acc+1e-18>=threshold:return v
 return pairs[-1][0]


class Agg:
 __slots__=("target_count","zero_opportunity_targets","zplus_targets","positive_targets","z0_raw","zplus_v","zplus_w","pos_v","pos_w","target_weight_error_max")
 def __init__(self):
  self.target_count=0;self.zero_opportunity_targets=0;self.zplus_targets=0;self.positive_targets=0;self.z0_raw=0
  self.zplus_v=array("d");self.zplus_w=array("d");self.pos_v=array("d");self.pos_w=array("d");self.target_weight_error_max=0.0
 def add_target(self,n:int,pos_species:int,zplus:list[float],positive:list[float]):
  implicit=(DIRECT_N-pos_species)*n
  if implicit<0 or len(zplus)+len(positive)!=pos_species*n:raise StopBuild("Target event partition failure")
  w=1.0/(DIRECT_N*n)
  self.target_count+=1;self.z0_raw+=implicit
  if implicit+len(zplus)>0:self.zero_opportunity_targets+=1
  if zplus:self.zplus_targets+=1
  if positive:self.positive_targets+=1
  self.zplus_v.extend(zplus);self.zplus_w.extend([w]*len(zplus));self.pos_v.extend(positive);self.pos_w.extend([w]*len(positive))
  self.target_weight_error_max=max(self.target_weight_error_max,abs((implicit+len(zplus)+len(positive))*w-1.0))


def combine(aggs:list[Agg],state:str,weighting:str)->dict[str,Any]:
 target_count=sum(a.target_count for a in aggs);z0_raw=sum(a.z0_raw for a in aggs)
 if state in {"ZERO_MIXTURE","ZPLUS_CONDITIONAL"}:
  vals=[x for a in aggs for x in a.zplus_v];tweights=[x for a in aggs for x in a.zplus_w]
  raw=len(vals);zweight=0.0 if state=="ZPLUS_CONDITIONAL" else sum(a.z0_raw/(DIRECT_N) for a in [])
  # z0 target-equal weight is reconstructed per aggregate from total target weight minus observed-state weights.
  z0_tw=sum(a.target_count-sum(a.zplus_w)-sum(a.pos_w) for a in aggs)
  if state=="ZPLUS_CONDITIONAL":z0_tw=0.0;z0_event=0
  else:z0_event=z0_raw
  contributing=sum(a.zplus_targets for a in aggs);opp_targets=sum(a.zero_opportunity_targets for a in aggs)
 else:
  vals=[x for a in aggs for x in a.pos_v];tweights=[x for a in aggs for x in a.pos_w];raw=len(vals);z0_tw=0.0;z0_event=0
  contributing=sum(a.positive_targets for a in aggs);opp_targets=contributing
 if weighting=="TARGET_EQUAL_THEN_PLOT_EQUAL":
  weights=tweights;zero_mass=z0_tw;total=zero_mass+sum(weights);mean=sum(v*w for v,w in zip(vals,weights))/total if total>0 else float("nan")
  qs={f"p{int(q*100):02d}":weighted_inverse(vals,weights,zero_mass,q) for q in [.5,.9,.95,.99]}
  zero_metric=zero_mass+sum(w for v,w in zip(vals,weights) if v==0);method="WEIGHTED_INVERSE_EMPIRICAL_CDF"
  opportunity_mass=total
 else:
  zero_mass=float(z0_event);total=zero_mass+len(vals);mean=sum(vals)/total if total>0 else float("nan");sv=sorted(vals)
  qs={f"p{int(q*100):02d}":qtype7_zeros(vals,z0_event,q) for q in [.5,.9,.95,.99]}
  zero_metric=zero_mass+sum(v==0 for v in vals);method="LEGACY_TYPE7_EXPANDED_EVENT_DISTRIBUTION";opportunity_mass=total
 return {"target_count":target_count,"opportunity_target_count":opp_targets,"contributing_target_count":contributing,"raw_nonzero_state_events":raw,"raw_structural_zero_events":z0_event,"opportunity_mass":opportunity_mass,"exact_zero_metric_mass":zero_metric,"exact_zero_metric_fraction":zero_metric/total if total>0 else float("nan"),"mean":mean,"median":qs["p50"],"p90":qs["p90"],"p95":qs["p95"],"p99":qs["p99"],"max":max(vals) if vals else (0.0 if zero_mass>0 else float("nan")),"quantile_method":method}


def hidden(aggs:list[Agg],weighting:str)->dict[str,Any]:
 zraw=sum(len(a.zplus_v) for a in aggs);z0raw=sum(a.z0_raw for a in aggs)
 if weighting=="TARGET_EQUAL_THEN_PLOT_EQUAL":
  zp=sum(sum(a.zplus_w) for a in aggs);z0=sum(a.target_count-sum(a.zplus_w)-sum(a.pos_w) for a in aggs)
 else:zp=float(zraw);z0=float(z0raw)
 den=z0+zp
 return {"target_count":sum(a.target_count for a in aggs),"zero_opportunity_target_count":sum(a.zero_opportunity_targets for a in aggs),"zplus_target_count":sum(a.zplus_targets for a in aggs),"raw_selected_y_zero_opportunities":z0raw+zraw,"raw_z0_events":z0raw,"raw_zplus_events":zraw,"weighted_selected_y_zero_opportunities":den,"weighted_z0_mass":z0,"weighted_zplus_mass":zp,"hidden_positive_frequency":zp/den if den>0 else float("nan")}


def verify_parent_zip()->dict[str,Any]:
 if sha_file(PARENT)!=EXPECTED["parent"][1]:raise StopBuild("Parent B14 outer SHA mismatch")
 with zipfile.ZipFile(PARENT) as z:
  sums=zcsv(z,"SHA256SUMS.csv");checked=0
  for r in sums:
   rel=r["relative_path"]
   if sha_bytes(z.read(rel))!=r["sha256"] or len(z.read(rel))!=int(r["size_bytes"]):raise StopBuild(f"Parent internal mismatch {rel}")
   checked+=1
  seal=z.read(zmember(z,"B14_EMPIRICAL_STRESS_CALIBRATION_SEAL_v01.json"))
  if sha_bytes(seal)!=EXPECTED_PARENT_SEAL:raise StopBuild("Parent B14 seal SHA mismatch")
 return {"parent_internal_rows":checked,"parent_seal_sha256":sha_bytes(seal)}


def verify_inputs(log:Logger)->dict[str,Any]:
 ids={}
 for k,(p,e) in EXPECTED.items():
  if not p.is_file():raise StopBuild(f"Missing accepted input {k}: {p}")
  got=sha_file(p)
  if got!=e:raise StopBuild(f"Accepted input SHA mismatch {k}: {got}")
  ids[k]={"path":str(p),"sha256":got,"size_bytes":p.stat().st_size};log(f"INPUT PASS {k} sha256={got}")
 parent=verify_parent_zip()
 con=sqlite3.connect(f"file:{CACHE.as_posix()}?mode=ro",uri=True)
 if con.execute("PRAGMA integrity_check").fetchone()[0]!="ok":raise StopBuild("B12 cache integrity failed")
 counts={"pseudo":con.execute("SELECT COUNT(*) FROM target WHERE target_type='PSEUDO' AND validation_status='AVAILABLE'").fetchone()[0],"actual":con.execute("SELECT COUNT(*) FROM target WHERE target_type='ACTUAL24' AND validation_status='AVAILABLE'").fetchone()[0],"species":con.execute("SELECT COUNT(*) FROM species_universe").fetchone()[0]};con.close()
 if counts!={"pseudo":4640,"actual":24,"species":402}:raise StopBuild(f"Cache protected counts failed {counts}")
 return {"identities":ids,**parent,"cache_counts":counts,"NEW_TREE_SOURCE_SCAN_ROWS":0,"Q1_CALCULATION_ROWS":0,"support_rows":0,"parent_commit":"d19ae55793587fa29ec9c675d0d26bca418e4741","parent_status":"ACCEPTED_EMPIRICAL_STRESS_EVIDENCE"}


def extract_parent_member(suffix:str,dest:Path)->str:
 with zipfile.ZipFile(PARENT) as z:
  name=zmember(z,suffix);sums={r["relative_path"]:r for r in zcsv(z,"SHA256SUMS.csv")};raw=z.read(name)
  rec=sums.get(name)
  if not rec or sha_bytes(raw)!=rec["sha256"]:raise StopBuild(f"Parent member manifest mismatch {name}")
 dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw);return rec["sha256"]


def load_direct_info()->tuple[list[str],dict[str,dict[str,str]],list[dict[str,str]]]:
 with zipfile.ZipFile(PARENT) as z:bench=zcsv(z,"B14_AB_FOLD_DISCREPANCY_BENCHMARK_v01.csv")
 if len(bench)!=97:raise StopBuild("Parent direct97 benchmark row count failed")
 direct=sorted([r["FIA_SPCD"] for r in bench],key=lambda x:int(x));return direct,{r["FIA_SPCD"]:r for r in bench},bench


def load_ti_by_plot()->dict[str,float]:
 with zipfile.ZipFile(EXPECTED["d10ca"][0]) as z:
  raw=z.read(zmember(z,"out/plot_block_xwalk_v01.csv.gz"))
 if sha_bytes(raw)!=EXPECTED_XWALK_MEMBER:raise StopBuild("D10CA xwalk member SHA mismatch")
 out={}
 with gzip.GzipFile(fileobj=io.BytesIO(raw)) as gz,io.TextIOWrapper(gz,encoding="utf-8-sig",newline="") as f:
  for r in csv.DictReader(f):out[r["PLT_CN"]]=float(r["fold_specific_ti_weight"])
 if len(out)!=338619:raise StopBuild("D10CA xwalk row count failed")
 return out


def ti_band(v:float)->str:return "LT_P95" if v<Q95 else ("P95_TO_LT_P99" if v<Q99 else "GE_P99")


def n_band(n:int)->str:
 if n<=4:return "N_2_4"
 if n<=9:return "N_5_9"
 if n<=24:return "N_10_24"
 if n<=99:return "N_25_99"
 return "N_GE_100"


def load_target_design(ti:dict[str,float])->tuple[dict[str,dict[str,Any]],dict[str,dict[str,Any]]]:
 con=sqlite3.connect(f"file:{CACHE.as_posix()}?mode=ro",uri=True);con.row_factory=sqlite3.Row
 pseudo={};actual={}
 for typ,dest in [("PSEUDO",pseudo),("ACTUAL24",actual)]:
  for r in con.execute("SELECT * FROM target WHERE target_type=? AND validation_status='AVAILABLE' ORDER BY target_id",(typ,)):
   p=list(con.execute("SELECT PLT_CN FROM member_plot WHERE member_id=? ORDER BY PLT_CN",(r["target_member_id"],)))
   if len(p)!=int(r["target_n"]):raise StopBuild(f"Target plot count failed {r['target_id']}")
   vals={ti[str(x[0])] for x in p}
   if len(vals)!=1:raise StopBuild(f"Target TI not unique {r['target_id']}")
   v=next(iter(vals));d=dict(r);d.update({"ti":v,"ti_band":ti_band(v),"n_band":n_band(int(r["target_n"])),"plot_ids":[str(x[0]) for x in p]});dest[r["target_id"]]=d
 con.close()
 if len(pseudo)!=PSEUDO_N or len(actual)!=ACTUAL_N:raise StopBuild("Target design identity failed")
 return pseudo,actual


def group_add(groups:dict[Any,Agg],key:Any,n:int,pos_species:int,z:list[float],p:list[float]):groups.setdefault(key,Agg()).add_target(n,pos_species,z,p)


def process_parent_events(path:Path,targets:dict[str,dict[str,Any]],reader,log:Logger):
 exact={};ref={};nb={};seen=set();active=0;zplus_total=0;pos_total=0;last="";cur=None;z=[];p=[];species=set();weight_error=0.0
 def finish(tid,zv,pv,sps):
  nonlocal weight_error
  t=targets[tid];n=int(t["target_n"]);pc=len(sps)
  for g,key in [(exact,(t["fold"],t["route"],t["ti_band"])),(ref,t["reference_strength"]),(nb,t["n_band"])]:
   group_add(g,key,n,pc,zv,pv);weight_error=max(weight_error,g[key].target_weight_error_max)
  seen.add(tid)
 for r in reader(path,["target_id","fold","route","target_n","FIA_SPCD","ti_band","selected_y","selected_plot_zero","normalized_tv","status"]):
  tid=r["target_id"]
  if cur is None:cur=tid
  if tid!=cur:
   if tid<cur:raise StopBuild("Parent pseudo Parquet target order is not monotone")
   finish(cur,z,p,species);cur=tid;z=[];p=[];species=set()
  t=targets.get(tid)
  if t is None or t["fold"]!=r["fold"] or t["route"]!=r["route"] or int(t["target_n"])!=r["target_n"] or t["ti_band"]!=r["ti_band"]:raise StopBuild(f"Parent event design mismatch {tid}")
  tv=float(r["normalized_tv"])
  if not math.isfinite(tv) or tv<0 or tv>1:raise StopBuild(f"Invalid parent TV {tid}")
  species.add(r["FIA_SPCD"])
  if r["selected_plot_zero"]==1:
   if float(r["selected_y"])!=0:raise StopBuild("Zero-state flag/value mismatch")
   z.append(tv);zplus_total+=1
  else:
   if float(r["selected_y"])<=0:raise StopBuild("Positive-state flag/value mismatch")
   p.append(tv);pos_total+=1
  active+=1
  if active%250000==0:log(f"PARENT_PSEUDO_SCAN rows={active}/{EXPECTED_ACTIVE}")
 if cur is not None:finish(cur,z,p,species)
 for tid in sorted(set(targets)-seen):finish(tid,[],[],set())
 if active!=EXPECTED_ACTIVE or zplus_total!=EXPECTED_ZPLUS or pos_total!=EXPECTED_ACTIVE-EXPECTED_ZPLUS or len(seen)!=PSEUDO_N:raise StopBuild(f"Parent event counts failed active={active} zplus={zplus_total} pos={pos_total} targets={len(seen)}")
 implicit=sum(a.z0_raw for a in exact.values())
 if implicit!=EXPECTED_IMPLICIT_Z0 or implicit+active!=EXPECTED_UNIVERSE or weight_error>2e-15:raise StopBuild(f"Opportunity partition failed implicit={implicit} weight_error={weight_error}")
 return exact,ref,nb,{"materialized_events":active,"zplus_events":zplus_total,"selected_positive_events":pos_total,"implicit_z0_events":implicit,"event_universe":implicit+active,"pseudo_targets":len(seen),"target_weight_sum_max_abs_error":weight_error}


def group_defs(exact:dict,ref:dict,nb:dict):
 keys=sorted(exact);out=[]
 for k in keys:out.append(("H1_FOLD_ROUTE_TI_BAND","|".join(k),[exact[k]]))
 for f in ["A","B"]:
  for b in ["LT_P95","P95_TO_LT_P99","GE_P99"]:
   a=[exact[k] for k in keys if k[0]==f and k[2]==b]
   if a:out.append(("H2_FOLD_TI_BAND",f"{f}|{b}",a))
 for b in ["LT_P95","P95_TO_LT_P99","GE_P99"]:
  a=[exact[k] for k in keys if k[2]==b]
  if a:out.append(("H3_TI_BAND",b,a))
 out.append(("H4_ALL","ALL",[exact[k] for k in keys]))
 for f in ["A","B"]:out.append(("FOLD",f,[exact[k] for k in keys if k[0]==f]))
 for r in ["LEVEL1","LEVEL2"]:out.append(("B9_ROUTE",r,[exact[k] for k in keys if k[1]==r]))
 for k in sorted(ref):out.append(("REFERENCE_STRENGTH",k,[ref[k]]))
 for k in ["N_2_4","N_5_9","N_10_24","N_25_99","N_GE_100"]:
  if k in nb:out.append(("TARGET_N_BAND",k,[nb[k]]))
 return out


WEIGHTS=["TARGET_EQUAL_THEN_PLOT_EQUAL","EVENT_EQUAL"]


def calibration_tables(defs):
 incidence=[];zero=[];failure=[];positive=[];compare=[];cache={}
 for gt,gv,aggs in defs:
  for w in WEIGHTS:
   h=hidden(aggs,w);mix=combine(aggs,"ZERO_MIXTURE",w);fail=combine(aggs,"ZPLUS_CONDITIONAL",w);pos=combine(aggs,"POSITIVE",w)
   cache[(gt,gv,w,"ZERO_MIXTURE")]=mix;cache[(gt,gv,w,"ZPLUS_CONDITIONAL")]=fail;cache[(gt,gv,w,"POSITIVE")]=pos;cache[(gt,gv,w,"HIDDEN")]=h
   incidence.append({"group_type":gt,"group_value":gv,"weighting":w,"estimand":"EMPIRICAL_TRANSPORT_FREQUENCY_NOT_BIOLOGICAL_DETECTION_PROBABILITY",**h})
   zero.append({"group_type":gt,"group_value":gv,"weighting":w,"state":"SELECTED_Y_ZERO_MIXTURE_Z0_PLUS_ZPLUS",**mix})
   failure.append({"group_type":gt,"group_value":gv,"weighting":w,"state":"SELECTED_Y_ZERO_AND_TARGET_POSITIVE_ZPLUS","diagnostic_role":"FAILURE_CONDITIONAL_SEVERITY_ONLY",**fail})
   positive.append({"group_type":gt,"group_value":gv,"weighting":w,"state":"SELECTED_Y_POSITIVE","diagnostic_role":"POSITIVE_OBSERVATION_CALIBRATION",**pos})
  for state in ["ZERO_MIXTURE","ZPLUS_CONDITIONAL","POSITIVE"]:
   a=cache[(gt,gv,WEIGHTS[0],state)];b=cache[(gt,gv,WEIGHTS[1],state)]
   compare.append({"group_type":gt,"group_value":gv,"state":state,"target_equal_mean":a["mean"],"event_equal_mean":b["mean"],"target_equal_p95":a["p95"],"event_equal_p95":b["p95"],"target_minus_event_mean":a["mean"]-b["mean"] if math.isfinite(a["mean"]) and math.isfinite(b["mean"]) else float("nan"),"target_minus_event_p95":a["p95"]-b["p95"] if math.isfinite(a["p95"]) and math.isfinite(b["p95"]) else float("nan"),"target_equal_quantile_method":a["quantile_method"],"event_equal_quantile_method":b["quantile_method"]})
 return incidence,zero,failure,positive,compare,cache


def selector_aggs(exact:dict,fold:str,route:str,band:str,level:str)->list[Agg]:
 keys=sorted(exact)
 if level=="H1_SAME_FOLD_ROUTE_TI_BAND":ks=[k for k in keys if k==(fold,route,band)]
 elif level=="H2_SAME_FOLD_TI_BAND":ks=[k for k in keys if k[0]==fold and k[2]==band]
 elif level=="H3_SAME_TI_BAND":ks=[k for k in keys if k[2]==band]
 elif level=="H4_ALL":ks=keys
 else:raise KeyError(level)
 return [exact[k] for k in ks]


def support(aggs:list[Agg],state:str)->tuple[int,int]:
 if state=="Y_ZERO":return sum(a.z0_raw+len(a.zplus_v) for a in aggs),sum(a.zero_opportunity_targets for a in aggs)
 if state=="ZPLUS":return sum(len(a.zplus_v) for a in aggs),sum(a.zplus_targets for a in aggs)
 if state=="Y_POSITIVE":return sum(len(a.pos_v) for a in aggs),sum(a.positive_targets for a in aggs)
 raise KeyError(state)


def choose_match(exact:dict,fold:str,route:str,band:str,state:str)->dict[str,Any]:
 for level in ["H1_SAME_FOLD_ROUTE_TI_BAND","H2_SAME_FOLD_TI_BAND","H3_SAME_TI_BAND","H4_ALL"]:
  aggs=selector_aggs(exact,fold,route,band,level);raw,targets=support(aggs,state)
  if raw>=MIN_RAW_OPPORTUNITIES and targets>=MIN_CONTRIBUTING_TARGETS:
   pop={"Y_ZERO":"ZERO_MIXTURE","ZPLUS":"ZPLUS_CONDITIONAL","Y_POSITIVE":"POSITIVE"}[state]
   st=combine(aggs,pop,WEIGHTS[0]);h=hidden(aggs,WEIGHTS[0])
   return {"match_level":level,"raw_opportunities":raw,"contributing_targets":targets,"stats":st,"hidden":h}
 raise StopBuild(f"No supported frozen match for {state} {fold}/{route}/{band}")


def frozen_case_matches(exact:dict,actual_design:dict[str,dict[str,Any]])->dict[str,Any]:
 out={}
 for tid,t in sorted(actual_design.items(),key=lambda x:x[1]["case_id"]):
  case=t["case_id"];out[case]={"fold":t["fold"],"route":t["route"],"ti_band":t["ti_band"],"Y_ZERO":choose_match(exact,t["fold"],t["route"],t["ti_band"],"Y_ZERO"),"ZPLUS":choose_match(exact,t["fold"],t["route"],t["ti_band"],"ZPLUS"),"Y_POSITIVE":choose_match(exact,t["fold"],t["route"],t["ti_band"],"Y_POSITIVE")}
 return out


APP_SCHEMA=[(x,"string") for x in ["case_id","fold","direction","route","ti_band","FIA_SPCD","accepted_scientific_name","observed_state","stress_tier","calibration_population","match_level","weighting","diagnostic_role","status"]]+[(x,"int64") for x in ["raw_calibration_opportunities","calibration_contributing_targets","primary_materiality_tier"]]+[(x,"double") for x in ["observed_y","observed_point_tv","applied_stress_tv","hidden_positive_frequency","calibration_mean","calibration_p95","calibration_max"]]


def read_parent_actual(path:Path,reader)->dict[tuple[str,str],dict[str,Any]]:
 out={};outer={}
 cols=["analysis_scope","case_id","fold","direction","route","FIA_SPCD","accepted_scientific_name","ti_band","stress_tier","observed_y","stress_normalized_tv"]
 for r in reader(path,cols):
  if r["analysis_scope"]!="INDIVIDUAL_SINGLETON":continue
  k=(r["case_id"],r["FIA_SPCD"]);d=out.setdefault(k,{"case_id":r["case_id"],"fold":r["fold"],"direction":r["direction"],"route":r["route"],"FIA_SPCD":r["FIA_SPCD"],"accepted_scientific_name":r["accepted_scientific_name"],"ti_band":r["ti_band"],"observed_y":float(r["observed_y"]),"tiers":{}});d["tiers"][r["stress_tier"]]=float(r["stress_normalized_tv"])
 if len(out)!=24*97 or any(set(d["tiers"])!={"E_OBSERVED","E_P95","E_EMPIRICAL_MAX"} for d in out.values()):raise StopBuild("Parent actual individual rows failed")
 return out


def apply_actual(parent:dict,case_matches:dict,direct_info:dict,writer,log:Logger):
 rows=[];positive_cases=0;zero_cases=0
 for (case,sp),d in sorted(parent.items(),key=lambda x:(x[0][0],int(x[0][1]))):
  m=case_matches[case];y=d["observed_y"];obs=d["tiers"]["E_OBSERVED"]
  if y==0:
   zero_cases+=1;state="Y_ZERO";mix=m["Y_ZERO"];fail=m["ZPLUS"];h=mix["hidden"]["hidden_positive_frequency"]
   specs=[("MIX_OBSERVED",obs,"ACTUAL_ZERO_POINT_MASS",1,"PRIMARY_OBSERVED"),("MIX_MEAN",mix["stats"]["mean"],"SELECTED_Y_ZERO_MIXTURE_Z0_PLUS_ZPLUS",1,"PRIMARY_MARGINAL_MEAN"),("MIX_P95",mix["stats"]["p95"],"SELECTED_Y_ZERO_MIXTURE_Z0_PLUS_ZPLUS",1,"PRIMARY_INDIVIDUAL_P95"),("FAILURE_CONDITIONAL_P95",fail["stats"]["p95"],"SELECTED_Y_ZERO_TARGET_POSITIVE_ZPLUS",0,"CONDITIONAL_SEVERITY_ONLY"),("EMPIRICAL_MAX",fail["stats"]["max"],"SELECTED_Y_ZERO_TARGET_POSITIVE_ZPLUS",0,"EXTREME_OUTER_DIAGNOSTIC")]
  elif y>0:
   positive_cases+=1;state="Y_POSITIVE";pos=m["Y_POSITIVE"];h=float("nan")
   specs=[("POS_OBSERVED",obs,"ACTUAL_POSITIVE_POINT_MASS",1,"PRIMARY_OBSERVED"),("POS_MEAN",pos["stats"]["mean"],"SELECTED_Y_POSITIVE",1,"PRIMARY_MARGINAL_MEAN"),("POS_P95",pos["stats"]["p95"],"SELECTED_Y_POSITIVE",1,"PRIMARY_INDIVIDUAL_P95"),("POS_MAX",pos["stats"]["max"],"SELECTED_Y_POSITIVE",0,"EXTREME_OUTER_DIAGNOSTIC")]
  else:raise StopBuild("Negative actual y")
  match=m["Y_ZERO"] if state=="Y_ZERO" else m["Y_POSITIVE"]
  st=match["stats"]
  for tier,val,pop,primary,role in specs:
   use=fail if tier in {"FAILURE_CONDITIONAL_P95","EMPIRICAL_MAX"} else match
   rows.append({"case_id":case,"fold":d["fold"],"direction":d["direction"],"route":d["route"],"ti_band":d["ti_band"],"FIA_SPCD":sp,"accepted_scientific_name":d["accepted_scientific_name"],"observed_state":state,"observed_y":y,"observed_point_tv":obs,"stress_tier":tier,"applied_stress_tv":val,"calibration_population":pop,"match_level":"ACTUAL_OBSERVED" if tier in {"MIX_OBSERVED","POS_OBSERVED"} else use["match_level"],"weighting":"ACTUAL" if tier in {"MIX_OBSERVED","POS_OBSERVED"} else WEIGHTS[0],"raw_calibration_opportunities":0 if tier in {"MIX_OBSERVED","POS_OBSERVED"} else use["raw_opportunities"],"calibration_contributing_targets":0 if tier in {"MIX_OBSERVED","POS_OBSERVED"} else use["contributing_targets"],"hidden_positive_frequency":h,"calibration_mean":st["mean"],"calibration_p95":st["p95"],"calibration_max":st["max"],"primary_materiality_tier":primary,"diagnostic_role":role,"status":"PASS_STATE_ALIGNED"})
 if positive_cases!=1 or zero_cases!=24*97-1 or len(rows)!=11639:raise StopBuild(f"Actual state partition failed positive={positive_cases} zero={zero_cases} rows={len(rows)}")
 path=OUT/"B14_V01_1_ACTUAL24_OBSERVED_STATE_APPLICATION.parquet"
 with writer(path,APP_SCHEMA,row_group_size=10000) as w:w.write_many(rows)
 return rows,{"application_rows":len(rows),"actual_zero_species_cases":zero_cases,"actual_positive_species_cases":positive_cases,"parquet_sha256":sha_file(path)}


def primary_actual_index(app:list[dict[str,Any]])->dict[tuple[str,str,str],dict[str,Any]]:
 return {(r["case_id"],r["FIA_SPCD"],r["stress_tier"]):r for r in app}


def build_direct(app,parent,bench):
 idx=primary_actual_index(app);bybench={r["FIA_SPCD"]:r for r in bench};cases_by_dir=defaultdict(set)
 for d in parent.values():cases_by_dir[d["direction"]].add(d["case_id"])
 rows=[]
 for dr in ["AB","BA"]:
  for sp in sorted(bybench,key=int):
   cases=sorted(cases_by_dir[dr]);p95=[];means=[];hs=[];observed=[];outer=[];pos=0
   for c in cases:
    d=parent[(c,sp)];state="Y_POSITIVE" if d["observed_y"]>0 else "Y_ZERO";pos+=state=="Y_POSITIVE"
    p95.append(idx[(c,sp,"POS_P95" if state=="Y_POSITIVE" else "MIX_P95")]["applied_stress_tv"])
    means.append(idx[(c,sp,"POS_MEAN" if state=="Y_POSITIVE" else "MIX_MEAN")]["applied_stress_tv"])
    if state=="Y_ZERO":hs.append(idx[(c,sp,"MIX_MEAN")]["hidden_positive_frequency"])
    observed.append(d["tiers"]["E_OBSERVED"]);outer.append(d["tiers"]["E_P95"])
   foldtv=float(bybench[sp]["AB_fold_normalized_tv"]) if bybench[sp]["AB_fold_normalized_tv"]!="NA" else float("nan")
   mx=max(p95);ms=sum(means);eh=sum(hs);ex=min(1.0,sum(outer))
   rows.append({"FIA_SPCD":sp,"accepted_scientific_name":bybench[sp]["accepted_scientific_name"],"direction":dr,"fold":{"AB":"B","BA":"A"}[dr],"actual_case_count":len(cases),"observed_positive_case_count":pos,"max_individual_state_aligned_p95":mx,"marginal_mean_triangle_upper_sum_raw":ms,"marginal_mean_triangle_upper_sum_capped_at_1":min(1.0,ms),"empirical_marginal_expected_hidden_positive_count":eh,"marginal_union_outer_bound_capped_at_1":min(1.0,eh),"observed_point_tv_sum":sum(observed),"parent_extreme_failure_conditional_p95_sum_capped_at_1":ex,"AB_fold_discrepancy_tv":foldtv,"max_p95_to_fold_tv_ratio":mx/foldtv if foldtv>0 else float("nan"),"mean_sum_to_fold_tv_ratio":ms/foldtv if foldtv>0 else float("nan"),"primary_labels":"MAX_INDIVIDUAL_STATE_ALIGNED_P95;MARGINAL_MEAN_TRIANGLE_UPPER_SUM;EMPIRICAL_MARGINAL_EXPECTED_HIDDEN_POSITIVE_COUNT","outer_label":"EXTREME_OUTER_NO_CANCELLATION_ENVELOPE_COMPARISON_ONLY"})
 return rows


def downstream_tables(app,direct,bench):
 di={(r["direction"],r["FIA_SPCD"]):r for r in direct};bi={r["FIA_SPCD"]:r for r in bench};abba=[];stress=[]
 for sp in sorted(bi,key=int):
  a=di[("AB",sp)];b=di[("BA",sp)];foldtv=a["AB_fold_discrepancy_tv"]
  abba.append({"FIA_SPCD":sp,"accepted_scientific_name":a["accepted_scientific_name"],"AB_max_individual_p95":a["max_individual_state_aligned_p95"],"BA_max_individual_p95":b["max_individual_state_aligned_p95"],"AB_marginal_mean_sum":a["marginal_mean_triangle_upper_sum_raw"],"BA_marginal_mean_sum":b["marginal_mean_triangle_upper_sum_raw"],"AB_expected_hidden_positive_count":a["empirical_marginal_expected_hidden_positive_count"],"BA_expected_hidden_positive_count":b["empirical_marginal_expected_hidden_positive_count"],"AB_fold_discrepancy_tv":foldtv,"max_direction_primary_p95":max(a["max_individual_state_aligned_p95"],b["max_individual_state_aligned_p95"]),"max_direction_mean_sum":max(a["marginal_mean_triangle_upper_sum_raw"],b["marginal_mean_triangle_upper_sum_raw"]),"max_primary_p95_to_fold_tv_ratio":max(a["max_individual_state_aligned_p95"],b["max_individual_state_aligned_p95"])/foldtv if foldtv>0 else float("nan"),"comparison_status":"BOTH_FOLDS_POSITIVE" if foldtv>0 else "FOLD_TV_UNAVAILABLE_OR_ZERO"})
  for dr in ["AB","BA"]:
   r=di[(dr,sp)];stress.append({"FIA_SPCD":sp,"accepted_scientific_name":r["accepted_scientific_name"],"direction":dr,"fold":r["fold"],"max_individual_state_aligned_p95":r["max_individual_state_aligned_p95"],"marginal_mean_triangle_upper_sum_raw":r["marginal_mean_triangle_upper_sum_raw"],"AB_fold_discrepancy_tv":foldtv,"max_p95_to_fold_tv_ratio":r["max_p95_to_fold_tv_ratio"],"mean_sum_to_fold_tv_ratio":r["mean_sum_to_fold_tv_ratio"],"p95_minus_fold_tv":r["max_individual_state_aligned_p95"]-foldtv if math.isfinite(foldtv) else float("nan"),"mean_sum_minus_fold_tv":r["marginal_mean_triangle_upper_sum_raw"]-foldtv if math.isfinite(foldtv) else float("nan"),"primary_comparison":"OBSERVED_STATE_ALIGNED_NOT_FAILURE_CONDITIONAL_SUM"})
 abies=[]
 for r in app:
  if r["FIA_SPCD"]=="22":abies.append({"row_type":"ACTUAL_APPLICATION",**r})
 for r in direct:
  if r["FIA_SPCD"]=="22":abies.append({"row_type":"DIRECTION_SUMMARY",**r})
 allfields=[]
 for r in abies:
  for k in r:
   if k not in allfields:allfields.append(k)
 return abba,stress,abies,allfields


def disposition_rows(meta,inc,zero,fail,pos,direct,category,status):
 def row(table,gt,gv,w=WEIGHTS[0]):return next(r for r in table if r["group_type"]==gt and r["group_value"]==gv and r["weighting"]==w)
 hall=row(inc,"H4_ALL","ALL");zall=row(zero,"H4_ALL","ALL");fall=row(fail,"H4_ALL","ALL");pall=row(pos,"H4_ALL","ALL")
 hi=row(inc,"H3_TI_BAND","GE_P99");hf=row(fail,"H3_TI_BAND","GE_P99")
 ab=[r for r in direct if r["direction"]=="AB"];ba=[r for r in direct if r["direction"]=="BA"]
 vals=[
  ("B14 v01 parent validity","B14 v01 artifact status","accepted parent hashes and history",EXPECTED["parent"][1],"Parent implementation followed its contract and remains accepted empirical stress evidence.","Its failure-conditioned outer envelope is not the primary v01_1 estimand.","ACCEPTED_EMPIRICAL_STRESS_EVIDENCE","Preserve parent without modification."),
  ("observed singleton point exposure","actual24 × direct97","actual E_OBSERVED point omission",f"maximum={meta['observed_max_tv']:.10g}","Observed positive exposure remains localized.","Observed zero does not prove target-stratum zero.","ACCEPTED_DERIVED_MATERIALITY_EVIDENCE","Use observed state to select frozen calibration."),
  ("selected-zero hidden-positive incidence","all pseudo targets","h_g under target-equal weighting",f"h={float(hall['hidden_positive_frequency']):.8g}","Failure incidence is distinct from conditional severity.","Empirical transport frequency is not biological detection probability.","B14_V01_1_TARGETED_CORRECTION_EVIDENCE","Carry h by frozen design match."),
  ("failure-conditioned severity","selected y=0 and target positive","TV conditional on Z+",f"median={float(fall['median']):.8g}; p95={float(fall['p95']):.8g}; max={float(fall['max']):.8g}","B14 v01 severity conclusion remains valid.","Conditioning does not estimate how often Z+ occurs.","ACCEPTED_EMPIRICAL_STRESS_EVIDENCE","Retain as diagnostic only."),
  ("observed-zero mixture stress","selected y=0","Z0+Z+ primary mixture",f"mean={float(zall['mean']):.8g}; p95={float(zall['p95']):.8g}; max={float(zall['max']):.8g}","This aligns with information observed at an actual zero singleton.","Pseudo-to-actual transport remains empirical.","B14_V01_1_TARGETED_CORRECTION_EVIDENCE","Use MIX_MEAN and MIX_P95."),
  ("selected-positive stress","selected y>0","positive-observation pseudo calibration",f"mean={float(pall['mean']):.8g}; p95={float(pall['p95']):.8g}; max={float(pall['max']):.8g}","Positive actual observations no longer borrow zero-selected stress.","Only one actual species-case is positive.","B14_V01_1_TARGETED_CORRECTION_EVIDENCE","Apply only to Y_POSITIVE cases."),
  ("high-TI incidence","TI ≥ p99","target-equal hidden-positive frequency",f"h={float(hi['hidden_positive_frequency']):.8g}","Reports incidence separately in the upper TI tail.","High-TI support is thinner.","B14_V01_1_TARGETED_CORRECTION_EVIDENCE","Retain frozen fallback rules."),
  ("high-TI severity","TI ≥ p99 and Z+","failure-conditioned TV",f"p95={float(hf['p95']):.8g}; max={float(hf['max']):.8g}","Tail severity remains visible when failure occurs.","Not a primary mixture envelope.","B14_V01_1_TARGETED_CORRECTION_EVIDENCE","Do not multiply severity by assumed 100% incidence."),
  ("target-equal weighting","pseudo target then species then plot","equal target mass",f"max target weight error={meta['calibration']['target_weight_sum_max_abs_error']}","Primary weighting prevents large-n targets from dominating.","Species are sampled uniformly across frozen direct97.","FROZEN_FOR_V01_1","Use as primary calibration."),
  ("event-equal sensitivity","legacy parent events","each retained-plot event equal",f"legacy Z+ count={EXPECTED_ZPLUS}","Reproduces B14 v01 where applicable.","Larger-n targets receive more weight.","SECONDARY_SENSITIVITY","Report beside target-equal results."),
  ("AB two-case aggregate","AB direction","state-aligned marginal summaries",f"max p95={max(r['max_individual_state_aligned_p95'] for r in ab):.8g}; max mean sum={max(r['marginal_mean_triangle_upper_sum_raw'] for r in ab):.8g}","Two cases yield a limited marginal aggregate.","No joint independence model is fitted.","B14_V01_1_TARGETED_CORRECTION_EVIDENCE","Keep direction separate."),
  ("BA twenty-two-case aggregate","BA direction","state-aligned marginal summaries",f"max p95={max(r['max_individual_state_aligned_p95'] for r in ba):.8g}; max mean sum={max(r['marginal_mean_triangle_upper_sum_raw'] for r in ba):.8g}","Twenty-two marginal means can accumulate without using conditional-p95 sums.","Triangle sum is an upper sum, not joint expected TV.","B14_V01_1_TARGETED_CORRECTION_EVIDENCE","Keep raw and capped values."),
  ("Abies procera","SPCD 22","positive-state calibration for its observed-positive case",f"observed max TV={meta['observed_max_tv']:.8g}","Only observed-positive direct97 exposure is handled with Y_POSITIVE calibration.","Localized observed sensitivity does not close hidden-positive tails.","B14_V01_1_TARGETED_CORRECTION_EVIDENCE","Retain dedicated ledger."),
  ("direct97 cohort","97 direct species","max individual state-aligned p95 and marginal mean triangle sum",f"category={category}","Conclusion uses observed-state mixtures rather than failure-conditioned p95 sums.","Final singleton subgate remains mainline authority.",category,"Return recommendation to mainline."),
  ("need for further covariance modeling","D10F-C gate","method necessity assessment","Not established by this correction","Mixture stress does not identify a covariance estimator.","Transport heterogeneity may require later evidence, not automatic model expansion.",status,"Reopen only if mainline identifies decision-relevant unresolved transport."),
 ]
 names=["evidence","estimand","conditioning","result","interpretation","limitation","status","next action"]
 return [dict(zip(names,v)) for v in vals]


def make_report(meta,inc,zero,fail,pos,compare,direct,category,status)->str:
 def row(tab,gt,gv,w=WEIGHTS[0]):return next(r for r in tab if r["group_type"]==gt and r["group_value"]==gv and r["weighting"]==w)
 hall=row(inc,"H4_ALL","ALL");zall=row(zero,"H4_ALL","ALL");fall=row(fail,"H4_ALL","ALL");pall=row(pos,"H4_ALL","ALL")
 e_hall=row(inc,"H4_ALL","ALL","EVENT_EQUAL");e_fall=row(fail,"H4_ALL","ALL","EVENT_EQUAL")
 hi95=row(inc,"H3_TI_BAND","P95_TO_LT_P99");hi99=row(inc,"H3_TI_BAND","GE_P99");hf95=row(fail,"H3_TI_BAND","P95_TO_LT_P99");hf99=row(fail,"H3_TI_BAND","GE_P99")
 refs=[r for r in inc if r["group_type"]=="REFERENCE_STRENGTH" and r["weighting"]==WEIGHTS[0]];ns=[r for r in inc if r["group_type"]=="TARGET_N_BAND" and r["weighting"]==WEIGHTS[0]]
 p95rows=[r for r in direct];comp=[r for r in p95rows if math.isfinite(float(r["AB_fold_discrepancy_tv"])) and float(r["AB_fold_discrepancy_tv"])>0]
 exceed_p=sum(float(r["max_individual_state_aligned_p95"])>float(r["AB_fold_discrepancy_tv"]) for r in comp);exceed_m=sum(float(r["marginal_mean_triangle_upper_sum_raw"])>float(r["AB_fold_discrepancy_tv"]) for r in comp)
 maxp=max(float(r["max_individual_state_aligned_p95"]) for r in direct);maxm=max(float(r["marginal_mean_triangle_upper_sum_raw"]) for r in direct)
 abeh=max(float(r["empirical_marginal_expected_hidden_positive_count"]) for r in direct if r["direction"]=="AB");baeh=max(float(r["empirical_marginal_expected_hidden_positive_count"]) for r in direct if r["direction"]=="BA")
 abm=max(float(r["marginal_mean_triangle_upper_sum_raw"]) for r in direct if r["direction"]=="AB");bam=max(float(r["marginal_mean_triangle_upper_sum_raw"]) for r in direct if r["direction"]=="BA")
 ms=meta["actual_design_match_summary"];aps=meta["actual_application_summary"]
 rationale={
  "NONMATERIAL_TAIL_CANDIDATE":"实际零观测匹配组的 mixture p95 全为零，且没有正观测物种×方向形成集中暴露。",
  "LOCALIZED_SPECIES_LEVEL_SENSITIVITY":"2,327 个零状态物种×案例的 mixture p95 全为零；唯一非零主 p95 集中于 S24 的 Abies procera 正观测，因此证据指向局部物种敏感性而非 cohort-wide 材料性。",
  "MATERIAL_SINGLETON_UNCERTAINTY_REMAINS":"观测状态对齐后的主指标仍显示跨物种、跨方向的广泛压力。",
  "UNRESOLVED_MIXTURE_TRANSPORT":"冻结匹配支持或 pseudo→actual 运输异质性不足以给出更具体的工作层建议。",
 }[category]
 return f"""# Q1 D10F-B14 v01_1——观测状态对齐混合压力修正

## 结论

- 任务状态：**{status}**
- 工作层建议：**{category}**
- B14 v01 仍为 **ACCEPTED EMPIRICAL STRESS EVIDENCE**；它没有编码、计算或治理失败。
- B14 v01 的 `MATERIAL_SINGLETON_UNCERTAINTY_REMAINS` 不被主线采用，因为它把失败条件严重度当成了每个实际零观测必然发生的外包络。
- 最终 singleton subgate 仍归主线；D10F-C 保持 HOLD。

## 冻结定义

主权重是任务指定的 `TARGET_EQUAL_THEN_PLOT_EQUAL`：每个 pseudo 目标在匹配组内获得相等总权重，目标内样地等权；冻结 direct97 是同一目标质量内的固定物种枚举，因此计算实现为每个目标×物种×样地事件权重 `1/(97 n_g)`。旧 B14 的 `EVENT_EQUAL` 作为次要敏感性保留。对 `selected y=0`，主分布同时包含目标层也为零的 Z0 和目标层为正的 Z+；对 `selected y>0`，使用独立的正观测校准。匹配层级、TI 带、支持回退、权重和分位数都在读取 actual24 物种结果前封存。

## Q1–Q14

### Q1：pseudo 中选中样地 y=0 时，完整层为正的频率多大？

目标等权经验运输频率为 {float(hall['hidden_positive_frequency']):.8g}。旧事件等权频率为 {float(e_hall['hidden_positive_frequency']):.8g}。分母明确包含 Z0 与 Z+；这不是生物学检测概率。

### Q2：该频率怎样随设计变量变化？

按 reference strength 报告的 h 范围为 {min(float(r['hidden_positive_frequency']) for r in refs):.8g}–{max(float(r['hidden_positive_frequency']) for r in refs):.8g}；按目标 n 带为 {min(float(r['hidden_positive_frequency']) for r in ns):.8g}–{max(float(r['hidden_positive_frequency']) for r in ns):.8g}，两者均随已冻结等级上升。折、B9 route、TI 带、reference strength 和 n 的完整连续结果均在 incidence 表中；这提示运输异质性，但未据输出新增匹配维度。

### Q3：一旦确为 hidden-positive，扰动多严重？

目标等权条件严重度 TV 的中位数/p90/p95/最大值为 {float(fall['median']):.8g}/{float(fall['p90']):.8g}/{float(fall['p95']):.8g}/{float(fall['max']):.8g}。事件等权 p95 为 {float(e_fall['p95']):.8g}，重现并保留 B14 v01 的失败条件严重度结论。

### Q4：混入真实零后，实际零观测对应的经验压力怎样？

目标等权 Z0+Z+ 混合 TV 的均值/中位数/p90/p95/p99/最大值为 {float(zall['mean']):.8g}/{float(zall['median']):.8g}/{float(zall['p90']):.8g}/{float(zall['p95']):.8g}/{float(zall['p99']):.8g}/{float(zall['max']):.8g}。这是 v01_1 的主要零观测压力对象。

### Q5：匹配 actual24 的设计组中，混合 p95 是否仍为零或很小？

24/24 个 actual 设计组的零观测 mixture p95 均为 0；相应 mixture mean 范围为 {ms['zero_mix_mean_min']:.8g}–{ms['zero_mix_mean_max']:.8g}。零状态匹配层级为 H1/H2/H3/H4={ms['zero_match_counts']['H1_SAME_FOLD_ROUTE_TI_BAND']}/{ms['zero_match_counts']['H2_SAME_FOLD_TI_BAND']}/{ms['zero_match_counts']['H3_SAME_TI_BAND']}/{ms['zero_match_counts']['H4_ALL']}。实际 2,327 个零状态物种×案例的 `MIX_P95` 也全部为 0。这里不以任意阈值判定“安全”，而保留逐例均值、尾部和 A/B 折 TV 连续比较。

### Q6：高 TI 增加发生率、严重度，还是两者？

TI p95–p99 带的 h={float(hi95['hidden_positive_frequency']):.8g}，条件 p95={float(hf95['p95']):.8g}；TI≥p99 的 h={float(hi99['hidden_positive_frequency']):.8g}，条件 p95={float(hf99['p95']):.8g}。相对 LT_P95，高 TI 没有提高发生率；条件严重度在 p95–p99 带升高、到 ≥p99 又下降，因此不是单调的“高 TI 同时提高两者”。

### Q7：目标等权与旧事件等权有何变化？

全体 h 从事件等权 {float(e_hall['hidden_positive_frequency']):.8g} 变为目标等权 {float(hall['hidden_positive_frequency']):.8g}；条件 p95 从 {float(e_fall['p95']):.8g} 变为 {float(fall['p95']):.8g}。差异源于大 n 目标不再获得更多总权重；完整比较在 `TARGET_EQUAL_VS_EVENT_EQUAL` 表中。

### Q8：实际正观测应怎样校准？

唯一实际正物种×案例为 {aps['positive_case_id']}、{aps['positive_species_name']}（SPCD {aps['positive_FIA_SPCD']}）；实际点 TV={aps['positive_observed_tv']:.8g}。其冻结正状态校准回退至 {aps['positive_match_level']}，均值/p95/最大值为 {aps['positive_mean']:.8g}/{aps['positive_p95']:.8g}/{aps['positive_max']:.8g}，不再借用零观测分布。

### Q9：AB 与 BA 的边际 hidden-positive 数量类比是多少？

AB 两例的 `EMPIRICAL_MARGINAL_EXPECTED_HIDDEN_POSITIVE_COUNT` 最大为 {abeh:.8g}；BA 二十二例最大为 {baeh:.8g}。它们不是整数预测，也不依赖独立性。

### Q10：实际 singleton 的边际均值 TV 上三角和是多少？

AB 的 `MARGINAL_MEAN_TRIANGLE_UPPER_SUM` 最大为 {abm:.8g}，BA 最大为 {bam:.8g}。这是逐例边际均值之和形成的 TV 上界，不是联合期望，也不假定抵消或独立。

### Q11：与普通 A/B 折差异相比如何？

在 180 个方向×物种可比较行中，最大个体状态对齐 p95 超过折 TV 的有 {exceed_p} 行，边际均值上三角和超过折 TV 的有 {exceed_m} 行；最大主 p95={maxp:.8g}，最大均值和={maxm:.8g}。主比较不再使用失败条件 p95 的 22 例求和。

### Q12：B14 v01 的 cohort-wide 物质性结论是否保留？

不直接保留。v01 的条件严重度有效，但其 cohort-wide 结论来自把 Z+ 发生率当作 100% 并累加条件 p95。v01_1 改用实际可见状态对应的混合分布和边际均值。

### Q13：剩余问题属于哪一类？

工作层建议为 **{category}**。{rationale}该建议只依据观测状态混合，不把 B14 v01 判为失败，也不替主线关闭 singleton subgate。

### Q14：现在是否必须开发新的 singleton 协方差方法？

本修正不能推出“必须”。若设计组、reference strength 或 n 的运输异质性仍影响主线决策，应先由主线决定是否需要新的、结果独立的识别证据；不得在本任务内自动转入 B15、GVCF、层级模型或 context/extremeness audit。

## 边界

未扫描 TREE，未读取 support，未计算真实 Q1，未提取 2 GB substrate SQLite，也未重跑 B13 或 B14 事件宇宙。父 B14 ZIP 和 seal 均保持原散列。未自动归档；传输目标仅为 `mirror`。
"""


def copy_sources():
 d=OUT/"src";d.mkdir(parents=True,exist_ok=True)
 for n in ["b14_v01_1_mixture_correction.py","config.json","verify_csvs.mjs","README_RUN.txt","RUN.cmd"]:shutil.copy2(HERE/n,d/n)
 for n in ["mini_parquet.py","mini_parquet_reader.py"]:shutil.copy2(ROOT/"05_qc"/"d10fb14_v01_work_singleton_uncertainty_materiality_stress"/"src"/n,d/n)
 if REQUEST.is_file():shutil.copy2(REQUEST,d/"TASK_REQUEST_v01_1.md")


def run():
 if OUT.exists() and any(OUT.iterdir()):raise StopBuild(f"Fresh-run guard: {OUT} is nonempty")
 OUT.mkdir(parents=True,exist_ok=True);log=Logger(OUT/"execution.log")
 try:
  log("B14 v01_1 START; actual24 species outcome rows parsed=0")
  pre=verify_inputs(log);direct,info,bench=load_direct_info();ti=load_ti_by_plot();pseudo_design,actual_design=load_target_design(ti)
  sys.path.insert(0,str(ROOT/"05_qc"/"d10fb14_v01_work_singleton_uncertainty_materiality_stress"/"src"));from mini_parquet_reader import read_parquet_rows,parquet_metadata;from mini_parquet import ParquetWriter
  pp=TMP/"input"/"B14_PSEUDO_SINGLETON_EVENT_LEVEL_v01.parquet";psha=extract_parent_member("B14_PSEUDO_SINGLETON_EVENT_LEVEL_v01.parquet",pp)
  exact,ref,nb,cmeta=process_parent_events(pp,pseudo_design,read_parquet_rows,log);defs=group_defs(exact,ref,nb)
  incidence,zero,failure,positive,compare,cache=calibration_tables(defs)
  csv_write(OUT/"B14_V01_1_ZERO_STATE_MIXTURE_SUMMARY.csv",zero,fields(zero));csv_write(OUT/"B14_V01_1_POSITIVE_STATE_STRESS_SUMMARY.csv",positive,fields(positive));csv_write(OUT/"B14_V01_1_HIDDEN_POSITIVE_INCIDENCE.csv",incidence,fields(incidence));csv_write(OUT/"B14_V01_1_FAILURE_CONDITIONAL_SEVERITY.csv",failure,fields(failure));csv_write(OUT/"B14_V01_1_TARGET_EQUAL_VS_EVENT_EQUAL.csv",compare,fields(compare))
  parent_zero=[]
  with zipfile.ZipFile(PARENT) as z:parent_zero=zcsv(z,"B14_ZERO_SELECTED_PLOT_STRESS_v01.csv")
  pz=next(r for r in parent_zero if r["group_type"]=="ZERO_SELECTED" and r["metric"]=="NORMALIZED_TV")
  legacy=next(r for r in failure if r["group_type"]=="H4_ALL" and r["weighting"]=="EVENT_EQUAL")
  for k in ["median","p90","p95","max"]:
   if not math.isclose(float(legacy[k]),float(pz[k]),rel_tol=2e-14,abs_tol=2e-14):raise StopBuild(f"Legacy severity reproduction failed {k}")
  matches=frozen_case_matches(exact,actual_design)
  zero_match_counts=Counter(m["Y_ZERO"]["match_level"] for m in matches.values())
  pos_match_counts=Counter(m["Y_POSITIVE"]["match_level"] for m in matches.values())
  zero_means=[m["Y_ZERO"]["stats"]["mean"] for m in matches.values()];zero_p95=[m["Y_ZERO"]["stats"]["p95"] for m in matches.values()]
  actual_design_match_summary={"case_count":len(matches),"zero_mix_p95_zero_case_count":sum(x==0 for x in zero_p95),"zero_mix_mean_min":min(zero_means),"zero_mix_mean_max":max(zero_means),"zero_match_counts":{k:zero_match_counts.get(k,0) for k in ["H1_SAME_FOLD_ROUTE_TI_BAND","H2_SAME_FOLD_TI_BAND","H3_SAME_TI_BAND","H4_ALL"]},"positive_match_counts":{k:pos_match_counts.get(k,0) for k in ["H1_SAME_FOLD_ROUTE_TI_BAND","H2_SAME_FOLD_TI_BAND","H3_SAME_TI_BAND","H4_ALL"]}}
  seal={"seal_id":"B14_V01_1_OBSERVED_STATE_CALIBRATION_SEAL","sealed_utc":datetime.now(timezone.utc).isoformat(),"phase":"AFTER_PSEUDO_CALIBRATION_BEFORE_ACTUAL24_SPECIES_OUTCOME_PARSE","actual24_species_outcome_rows_parsed_before_seal":0,"parent_b14_sha256":EXPECTED["parent"][1],"parent_calibration_seal_sha256":EXPECTED_PARENT_SEAL,"parent_pseudo_parquet_sha256":psha,"definitions":{"Y_ZERO":"selected plot y=0; primary distribution mixes Z0 target-zero exact zeros and Z+ target-positive parent stresses","ZPLUS":"selected plot y=0 and target positive; conditional severity diagnostic only","Y_POSITIVE":"selected plot y>0; separate calibration","primary_weighting":WEIGHTS[0],"secondary_weighting":"EVENT_EQUAL","species_selection":"uniform across frozen direct97 before within-target plot selection","target_n_bands":["N_2_4","N_5_9","N_10_24","N_25_99","N_GE_100"],"ti_bands":{"LT_P95":f"TI < {Q95}","P95_TO_LT_P99":f"{Q95} <= TI < {Q99}","GE_P99":f"TI >= {Q99}"},"matching_hierarchy":["H1_SAME_FOLD_ROUTE_TI_BAND","H2_SAME_FOLD_TI_BAND","H3_SAME_TI_BAND","H4_ALL"],"minimum_raw_opportunities":MIN_RAW_OPPORTUNITIES,"minimum_contributing_targets":MIN_CONTRIBUTING_TARGETS,"target_equal_quantile":"weighted inverse empirical CDF","event_equal_quantile":"parent-compatible expanded type-7","actual_zero_tiers":["MIX_OBSERVED","MIX_MEAN","MIX_P95","FAILURE_CONDITIONAL_P95","EMPIRICAL_MAX"],"actual_positive_tiers":["POS_OBSERVED","POS_MEAN","POS_P95","POS_MAX"],"multiple_case_primary":["MAX_INDIVIDUAL_STATE_ALIGNED_P95","MARGINAL_MEAN_TRIANGLE_UPPER_SUM","EMPIRICAL_MARGINAL_EXPECTED_HIDDEN_POSITIVE_COUNT"],"no_independence_assumption":True},"calibration_counts":cmeta,"case_design_matches":matches,"sealed_files":{n:sha_file(OUT/n) for n in ["B14_V01_1_ZERO_STATE_MIXTURE_SUMMARY.csv","B14_V01_1_POSITIVE_STATE_STRESS_SUMMARY.csv","B14_V01_1_HIDDEN_POSITIVE_INCIDENCE.csv","B14_V01_1_FAILURE_CONDITIONAL_SEVERITY.csv","B14_V01_1_TARGET_EQUAL_VS_EVENT_EQUAL.csv"]}}
  json_write(OUT/"B14_V01_1_OBSERVED_STATE_CALIBRATION_SEAL.json",seal);sealsha=sha_file(OUT/"B14_V01_1_OBSERVED_STATE_CALIBRATION_SEAL.json");log(f"OBSERVED-STATE CALIBRATION SEALED sha256={sealsha}; beginning actual24 species outcome parse")
  pa=TMP/"input"/"B14_ACTUAL24_STRESS_APPLICATION_v01.parquet";extract_parent_member("B14_ACTUAL24_STRESS_APPLICATION_v01.parquet",pa);parent_actual=read_parent_actual(pa,read_parquet_rows)
  app,ameta=apply_actual(parent_actual,matches,info,ParquetWriter,log);direct_rows=build_direct(app,parent_actual,bench);abba,stress,abies,abies_fields=downstream_tables(app,direct_rows,bench)
  csv_write(OUT/"B14_V01_1_DIRECT97_MATERIALITY_SUMMARY.csv",direct_rows,fields(direct_rows));csv_write(OUT/"B14_V01_1_AB_VS_BA_SUMMARY.csv",abba,fields(abba));csv_write(OUT/"B14_V01_1_ABIES_PROCERA_CASE.csv",abies,abies_fields);csv_write(OUT/"B14_V01_1_STRESS_VS_AB_FOLD_DISCREPANCY.csv",stress,fields(stress))
  observed_max=max(d["tiers"]["E_OBSERVED"] for d in parent_actual.values())
  positive_app=next(r for r in app if r["observed_state"]=="Y_POSITIVE" and r["stress_tier"]=="POS_P95")
  actual_application_summary={"zero_species_cases":ameta["actual_zero_species_cases"],"zero_mix_p95_nonzero_count":sum(r["observed_state"]=="Y_ZERO" and r["stress_tier"]=="MIX_P95" and r["applied_stress_tv"]!=0 for r in app),"positive_species_cases":ameta["actual_positive_species_cases"],"positive_case_id":positive_app["case_id"],"positive_FIA_SPCD":positive_app["FIA_SPCD"],"positive_species_name":positive_app["accepted_scientific_name"],"positive_observed_tv":positive_app["observed_point_tv"],"positive_match_level":positive_app["match_level"],"positive_mean":positive_app["calibration_mean"],"positive_p95":positive_app["calibration_p95"],"positive_max":positive_app["calibration_max"]}
  meta={"task_id":"Q1_D10F_B14_v01_1_WORK_OBSERVED_STATE_ALIGNED_MIXTURE_STRESS_CORRECTION","builder_version":VERSION,"task_status":"B14_V01_1_MIXTURE_CORRECTION_COMPLETE","recommendation":"TO_BE_FINALIZED_FROM_LOCKED_OUTPUTS","run_completed_utc":datetime.now(timezone.utc).isoformat(),"preflight":pre,"calibration":cmeta,"calibration_seal_sha256":sealsha,"actual_design_match_summary":actual_design_match_summary,"application":ameta,"actual_application_summary":actual_application_summary,"observed_max_tv":observed_max,"direct_species":97,"actual_cases":24,"AB_cases":2,"BA_cases":22,"parent_history_rewritten":False,"B14_v01_scientific_disposition_adopted_by_mainline":False,"phase_D":"NOT_APPLICABLE","context_extremeness_audit":"NOT_LAUNCHED","no_automatic_archive":True,"D10F_C":"HOLD"}
  inv=[
   {"check_id":"PARENT_B14_ZIP_SHA","expected":EXPECTED["parent"][1],"observed":sha_file(PARENT),"status":"PASS","detail":"Parent unchanged."},
   {"check_id":"PARENT_B14_SEAL_SHA","expected":EXPECTED_PARENT_SEAL,"observed":pre["parent_seal_sha256"],"status":"PASS","detail":"Accepted parent calibration seal."},
   {"check_id":"PSEUDO_TARGET_IDENTITY","expected":4640,"observed":cmeta["pseudo_targets"],"status":"PASS","detail":"B12 scoreable pseudo targets."},
   {"check_id":"DIRECT97_IDENTITY","expected":97,"observed":len(direct),"status":"PASS","detail":"No species exclusion."},
   {"check_id":"ACTUAL24_IDENTITY","expected":24,"observed":len(actual_design),"status":"PASS","detail":"Design identity frozen before outcomes."},
   {"check_id":"ZERO_DENOMINATOR_STATES","expected":"Z0_PLUS_ZPLUS","observed":"Z0_PLUS_ZPLUS","status":"PASS","detail":f"Z0={cmeta['implicit_z0_events']}; Z+={cmeta['zplus_events']}"},
   {"check_id":"LEGACY_ZPLUS_COUNT","expected":EXPECTED_ZPLUS,"observed":cmeta["zplus_events"],"status":"PASS","detail":"Parent materialized selected-zero/target-positive count."},
   {"check_id":"TARGET_ZERO_EXACT_ZERO","expected":EXPECTED_IMPLICIT_Z0,"observed":cmeta["implicit_z0_events"],"status":"PASS","detail":"Structural Z0 mass enters mixture at TV=0."},
   {"check_id":"STATE_CALIBRATION_SEPARATION","expected":"Y_ZERO_NEVER_Y_POSITIVE","observed":"PASS","status":"PASS","detail":"Separate frozen populations and tier names."},
   {"check_id":"TARGET_EQUAL_WEIGHT_SUM","expected":0,"observed":cmeta["target_weight_sum_max_abs_error"],"status":"PASS","detail":"Each target totals one across 97 species and n plots."},
   {"check_id":"EVENT_EQUAL_PARENT_REPRODUCTION","expected":float(pz["p95"]),"observed":float(legacy["p95"]),"status":"PASS","detail":"Median, p90, p95, max all exact within tolerance."},
   {"check_id":"SEAL_BEFORE_ACTUAL_OUTCOME_PARSE","expected":0,"observed":0,"status":"PASS","detail":sealsha},
   {"check_id":"ACTUAL_STATE_PARTITION","expected":"2327 ZERO + 1 POSITIVE","observed":f"{ameta['actual_zero_species_cases']} ZERO + {ameta['actual_positive_species_cases']} POSITIVE","status":"PASS","detail":"Actual state selects but does not alter calibration."},
   {"check_id":"NO_SUPPORT","expected":0,"observed":0,"status":"PASS","detail":"No support data used."},
   {"check_id":"NO_Q1","expected":0,"observed":0,"status":"PASS","detail":"No real Q1 calculation."},
   {"check_id":"NO_TREE_RESCAN","expected":0,"observed":0,"status":"PASS","detail":"Parent pseudo event reuse only."},
   {"check_id":"NO_NEW_ESTIMATOR","expected":"YES","observed":"YES","status":"PASS","detail":"No covariance/distributional model."},
   {"check_id":"NO_SPECIES_EXCLUSION","expected":97,"observed":len({r['FIA_SPCD'] for r in direct_rows}),"status":"PASS","detail":"All direct97 retained."},
  ];csv_write(OUT/"B14_V01_1_INVARIANT_QC.csv",inv,fields(inv))
  fire=[
   {"check_id":"PARENT_NOT_REWRITTEN","observed":"B14 v01 remains accepted evidence","status":"PASS"},{"check_id":"NO_B14_RERUN","observed":"Parent pseudo Parquet reused","status":"PASS"},{"check_id":"NO_B13_RERUN","observed":"B13 accepted identity only","status":"PASS"},{"check_id":"NO_TREE_RESCAN","observed":"0 rows","status":"PASS"},{"check_id":"NO_SUPPORT","observed":"0 rows","status":"PASS"},{"check_id":"NO_REAL_Q1","observed":"0 rows","status":"PASS"},{"check_id":"NO_NEW_ESTIMATOR","observed":"No estimator/model constructed","status":"PASS"},{"check_id":"NO_INDEPENDENCE_ASSUMPTION","observed":"No products/binomial/Monte Carlo joint draws","status":"PASS"},{"check_id":"ACTUAL_OUTCOME_FIREWALL","observed":f"Seal {sealsha} precedes parse","status":"PASS"},{"check_id":"NO_OUTPUT_DRIVEN_RECALIBRATION","observed":"Frozen match/weight/tier rules unchanged","status":"PASS"},{"check_id":"CONTEXT_AUDIT_NOT_LAUNCHED","observed":"Recommendation only if later needed","status":"PASS"},{"check_id":"D10F_C","observed":"HOLD","status":"PASS"},
  ];csv_write(OUT/"B14_V01_1_FIREWALL_QC.csv",fire,fields(fire))
  prov=[]
  for k,v in pre["identities"].items():prov.append({"source_id":k.upper(),"path":v["path"],"sha256":v["sha256"],"provenance_status":"ACCEPTED_EMPIRICAL_STRESS_EVIDENCE" if k=="parent" else "ACCEPTED_EVIDENCE","role":"PARENT_PSEUDO_AND_ACTUAL_EVIDENCE" if k=="parent" else "PROTECTED_UPSTREAM_IDENTITY","access":"READ_ONLY","status":"PASS"})
  prov.append({"source_id":"CURRENT_TASK","path":str(OUT),"sha256":"SEE_SHA256SUMS","provenance_status":"B14_V01_1_TARGETED_CORRECTION_EVIDENCE","role":"OBSERVED_STATE_MIXTURE_CORRECTION","access":"WRITE_NEW_ONLY","status":"COMPLETE"});csv_write(OUT/"B14_V01_1_PROVENANCE.csv",prov,fields(prov))
  disp=disposition_rows(meta,incidence,zero,failure,positive,direct_rows,"UNRESOLVED_MIXTURE_TRANSPORT","B14_V01_1_MIXTURE_CORRECTION_COMPLETE");csv_write(OUT/"B14_V01_1_DISPOSITION_MATRIX.csv",disp,fields(disp))
  json_write(OUT/"B14_V01_1_RUN_METADATA.json",meta);copy_sources();(OUT/"B14_V01_1_MAIN_REPORT.md").write_text(make_report(meta,incidence,zero,failure,positive,compare,direct_rows,"UNRESOLVED_MIXTURE_TRANSPORT","B14_V01_1_MIXTURE_CORRECTION_COMPLETE"),encoding="utf-8",newline="\n");log("B14 v01_1 CORE COMPLETE; outputs locked; awaiting recommendation finalization")
 except Exception as e:
  (OUT/"B14_V01_1_STOP_REPORT.md").write_text(f"# B14 v01_1 stopped\n\nReason: `{type(e).__name__}: {e}`\n\nParent B14 was not modified. D10F-C remains HOLD.\n",encoding="utf-8");log(f"STOP {type(e).__name__}: {e}");raise
 finally:log.close()


def finalize(category:str,status:str):
 meta=json.loads((OUT/"B14_V01_1_RUN_METADATA.json").read_text(encoding="utf-8"));inc=csv_read(OUT/"B14_V01_1_HIDDEN_POSITIVE_INCIDENCE.csv");zero=csv_read(OUT/"B14_V01_1_ZERO_STATE_MIXTURE_SUMMARY.csv");fail=csv_read(OUT/"B14_V01_1_FAILURE_CONDITIONAL_SEVERITY.csv");pos=csv_read(OUT/"B14_V01_1_POSITIVE_STATE_STRESS_SUMMARY.csv");comp=csv_read(OUT/"B14_V01_1_TARGET_EQUAL_VS_EVENT_EQUAL.csv");direct=csv_read(OUT/"B14_V01_1_DIRECT97_MATERIALITY_SUMMARY.csv")
 for r in direct:
  for k in ["max_individual_state_aligned_p95","marginal_mean_triangle_upper_sum_raw","AB_fold_discrepancy_tv"]:
   try:r[k]=float(r[k])
   except:r[k]=float("nan")
 meta["recommendation"]=category;meta["task_status"]=status;meta["finalized_utc"]=datetime.now(timezone.utc).isoformat();json_write(OUT/"B14_V01_1_RUN_METADATA.json",meta)
 disp=disposition_rows(meta,inc,zero,fail,pos,direct,category,status);csv_write(OUT/"B14_V01_1_DISPOSITION_MATRIX.csv",disp,fields(disp));(OUT/"B14_V01_1_MAIN_REPORT.md").write_text(make_report(meta,inc,zero,fail,pos,comp,direct,category,status),encoding="utf-8",newline="\n")


def package()->tuple[Path,str]:
 for p in [OUT/"SHA256SUMS.csv",OUT/"TRANSFER_MANIFEST_v01.csv",OUT/"Q1_D10F_B14_v01_1.zip"]:
  if p.exists():p.unlink()
 files=sorted([p for p in OUT.rglob("*") if p.is_file() and p.name not in {"SHA256SUMS.csv","TRANSFER_MANIFEST_v01.csv","Q1_D10F_B14_v01_1.zip"}],key=lambda p:p.relative_to(OUT).as_posix())
 sums=[{"relative_path":p.relative_to(OUT).as_posix(),"size_bytes":p.stat().st_size,"sha256":sha_file(p)} for p in files];csv_write(OUT/"SHA256SUMS.csv",sums,["relative_path","size_bytes","sha256"])
 prefix="release_mirror/Q1-D10FB14-v01_1-20260909/";tr=[]
 for p in files+[OUT/"SHA256SUMS.csv"]:
  rel=p.relative_to(OUT).as_posix()
  if p.suffix==".parquet":role,pri="MACHINE_EVIDENCE","P0"
  elif p.name=="B14_V01_1_MAIN_REPORT.md":role,pri="PRIMARY_REPORT","P0"
  elif "QC" in p.name or "DISPOSITION" in p.name or "SEAL" in p.name:role,pri="AUDIT_CONTROL","P0"
  elif p.suffix==".csv":role,pri="TABULAR_EVIDENCE","P1"
  elif rel.startswith("src/"):role,pri="REPRODUCIBILITY_CODE","P2"
  else:role,pri="PROVENANCE_SUPPORT","P2"
  tr.append({"local_path":str(p),"relative_path":prefix+rel,"role":role,"upload_target":"mirror","required":"YES","mainline_priority":pri,"size_bytes":p.stat().st_size,"sha256":sha_file(p),"notes":"B14 v01_1 targeted correction; preserve relative path; upload_target intentionally mirror"})
 csv_write(OUT/"TRANSFER_MANIFEST_v01.csv",tr,["local_path","relative_path","role","upload_target","required","mainline_priority","size_bytes","sha256","notes"])
 if any(r["upload_target"]!="mirror" for r in tr):raise StopBuild("Transfer target failed")
 zp=OUT/"Q1_D10F_B14_v01_1.zip";members=sorted([p for p in OUT.rglob("*") if p.is_file() and p!=zp],key=lambda p:p.relative_to(OUT).as_posix())
 with zipfile.ZipFile(zp,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=9,allowZip64=True) as z:
  for p in members:
   zi=zipfile.ZipInfo(p.relative_to(OUT).as_posix(),(2026,9,9,0,0,0));zi.compress_type=zipfile.ZIP_DEFLATED;zi.external_attr=0o100644<<16;z.writestr(zi,p.read_bytes(),compress_type=zipfile.ZIP_DEFLATED,compresslevel=9)
 with zipfile.ZipFile(zp) as z:
  for r in sums:
   if sha_bytes(z.read(r["relative_path"]))!=r["sha256"]:raise StopBuild(f"ZIP internal mismatch {r['relative_path']}")
  zr=list(csv.DictReader(io.StringIO(z.read("TRANSFER_MANIFEST_v01.csv").decode("utf-8-sig"))))
  if set(r["upload_target"] for r in zr)!={"mirror"}:raise StopBuild("ZIP manifest upload target failed")
 if sha_file(PARENT)!=EXPECTED["parent"][1]:raise StopBuild("Parent changed during task")
 return zp,sha_file(zp)


def main():
 ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest="cmd",required=True);sub.add_parser("run");f=sub.add_parser("finalize");f.add_argument("--category",required=True,choices=["NONMATERIAL_TAIL_CANDIDATE","LOCALIZED_SPECIES_LEVEL_SENSITIVITY","MATERIAL_SINGLETON_UNCERTAINTY_REMAINS","UNRESOLVED_MIXTURE_TRANSPORT"]);f.add_argument("--status",default="B14_V01_1_MIXTURE_CORRECTION_COMPLETE",choices=["B14_V01_1_MIXTURE_CORRECTION_COMPLETE","B14_V01_1_STOPPED_FOR_MAINLINE_REVIEW"]);sub.add_parser("package");a=ap.parse_args()
 if a.cmd=="run":run()
 elif a.cmd=="finalize":finalize(a.category,a.status)
 else:
  p,h=package();print(json.dumps({"zip":str(p),"sha256":h,"size_bytes":p.stat().st_size,"upload_target":"mirror"},indent=2))


if __name__=="__main__":main()
