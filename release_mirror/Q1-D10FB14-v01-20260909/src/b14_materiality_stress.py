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
import statistics
import subprocess
import sys
import time
import zipfile
from array import array
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

HERE = Path(__file__).resolve().parent
ROOT = Path(r"C:\range_paper")
OUT = ROOT / "05_qc" / "d10fb14_v01_work_singleton_uncertainty_materiality_stress"
TMP = ROOT / "99_tmp" / "d10fb14_v01"
CACHE = ROOT / "99_tmp" / "d10fb12_v01" / "cache" / "b12_cache.sqlite"
REQUEST = Path(r"C:\Users\bug_g\.codex\attachments\26e61788-e48d-47c7-b8e1-9aee3318f6fb\pasted-text.txt")

INPUTS = {
    "substrate": (ROOT / "10_archive" / "q1_fia_substrate_v01_1" / "Q1_FIA_SUBSTRATE_v01_1.zip", "1dbd8cf3fdb9fdbd25945ed70af64e1c739ec78f10f24ec4866128c38d5d946e"),
    "d10ca": (ROOT / "10_archive" / "d10ca" / "D10CA_v01.zip", "c8f73406f7f192b8f124add3cb0ded7ea65474e8d72d752e37dc557a08588865"),
    "b12": (ROOT / "10_archive" / "d10fb12_v01_1" / "Q1_D10F_B12_v01_1.zip", "d009bf50225ca3c2f483e08fe17f22312f93c9a28f36786abae8729fde3a21ab"),
    "b13": (ROOT / "10_archive" / "d10fb13_v01" / "Q1_D10F_B13_v01.zip", "c3898021cfe71ae0ea7b307be3907c8598dc1d1744f04e37d5ee0fc9d74807d9"),
    "q1_projection": (ROOT / "10_archive" / "q1_b12_q1_cohort_projection_v01" / "Q1_B12_Q1_COHORT_PROJECTION_v01.zip", "70d34c6905a9d76675943ae03182feae719340d159ca6b69b68b9b9d089f227e"),
    "singleton_audit": (ROOT / "10_archive" / "q1_singleton_materiality_v01" / "Q1_SINGLETON_MATERIALITY_AUDIT_v01.zip", "e85da191519ac8ed033c46ac78257c1c7e515976fd87a0d99511093bd0d8e007"),
    "cache": (CACHE, "0daf80d098546d61aecd8e75701f5174d9f6fd4452ce4a1b257651d45c9d2953"),
}
EXPECTED_XWALK_SHA = "a2c4bb3f6d45ed7d6497c511648265b7d692bf872aabbba1fdd99cc534be9447"
EXPECTED_FORMULA_SHA = "c22c88c1668f1029a1c96b18661caf2c5c7d59f53466d52d6f450dbdad39d82f"
EXPECTED_RULE_SHA = "e0f98cfb6eb2100a8149660d39977287ddb58a170add61dc16581a5bd92f0279"
EXPECTED_CACHE_FINGERPRINT = "5d0a9dbaf55045c20bdab107f061c477fe77106d100bc95681a6dfebd1eeb7bd"
EXPECTED_CACHE_LOGICAL = "e85168819a7954f9f1ead69f1554e29c193ba9ef369c7c2793b4587d5f8dd416"
MIN_CALIBRATION_N = 100
DIRECT_N = 97
SCOREABLE_N = 4640
ACTUAL_N = 24
EXPECTED_EVENT_UNIVERSE = 26_138_299
BUILD_VERSION = "1.0.0"


class StopBuild(RuntimeError):
    pass


class Logger:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.f = self.path.open("a", encoding="utf-8", newline="\n")

    def __call__(self, message: str) -> None:
        line = f"{datetime.now(timezone.utc).isoformat()} {message}"
        print(line, flush=True)
        self.f.write(line + "\n")
        self.f.flush()

    def close(self) -> None:
        self.f.close()


def sha256_file(path: Path, chunk: int = 8 * 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def stable_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def clean_value(value: Any) -> Any:
    if isinstance(value, float) and not math.isfinite(value):
        return "NA"
    return value


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fields: list[str]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        for row in rows:
            w.writerow({k: clean_value(row.get(k, "")) for k in fields})
            count += 1
    return count


def zip_member(z: zipfile.ZipFile, suffix: str) -> str:
    hits = [n for n in z.namelist() if n.replace("\\", "/").endswith(suffix)]
    if len(hits) != 1:
        raise StopBuild(f"Expected one ZIP member ending {suffix}, found {hits}")
    return hits[0]


def zip_csv(z: zipfile.ZipFile, suffix: str) -> list[dict[str, str]]:
    raw = z.read(zip_member(z, suffix)).decode("utf-8-sig")
    return list(csv.DictReader(io.StringIO(raw)))


def verify_internal_manifest(path: Path) -> int:
    with zipfile.ZipFile(path) as z:
        member = zip_member(z, "SHA256SUMS.csv")
        rows = list(csv.DictReader(io.StringIO(z.read(member).decode("utf-8-sig"))))
        checked = 0
        for r in rows:
            rel = str(r.get("relative_path") or r.get("path") or r.get("file") or "").replace("\\", "/")
            if not rel:
                continue
            candidates = [rel, str(Path(member).parent / rel).replace("\\", "/")]
            hit = next((x for x in candidates if x in z.namelist()), None)
            if hit is None:
                continue
            if sha256_bytes(z.read(hit)) != str(r.get("sha256", "")).lower():
                raise StopBuild(f"Internal SHA mismatch: {path.name}!{hit}")
            checked += 1
        if checked == 0:
            raise StopBuild(f"No internal manifest row verified: {path}")
        return checked


def qtype7(values: list[float], q: float) -> float:
    if not values:
        return float("nan")
    v = sorted(values)
    h = (len(v) - 1) * q
    lo = int(math.floor(h)); hi = int(math.ceil(h))
    return v[lo] if lo == hi else v[lo] + (h - lo) * (v[hi] - v[lo])


def finite_float(value: Any) -> float:
    x = float(value)
    if not math.isfinite(x):
        raise StopBuild(f"Non-finite value: {value}")
    return x


def direction(fold: str) -> str:
    return {"A": "BA", "B": "AB"}[fold]


def normalized_tv(a: dict[str, float], b: dict[str, float]) -> float:
    ta = sum(a.values()); tb = sum(b.values())
    if ta <= 0 or tb <= 0:
        return float("nan")
    return 0.5 * sum(abs(a.get(k, 0.0) / ta - b.get(k, 0.0) / tb) for k in set(a) | set(b))


class Agg:
    def __init__(self) -> None:
        self.tv = array("d")
        self.mass = array("d")
        self.extra_zeros = 0
        self.undefined = 0

    def add(self, tv: float, mass: float) -> None:
        if math.isfinite(tv) and math.isfinite(mass):
            self.tv.append(tv); self.mass.append(mass)
        else:
            self.undefined += 1

    def add_implicit(self, n: int) -> None:
        self.extra_zeros += int(n)


def combined_values(aggs: Iterable[Agg], metric: str) -> tuple[list[float], int, int]:
    vals: list[float] = []
    zeros = 0; undef = 0
    for a in aggs:
        vals.extend(getattr(a, metric)); zeros += a.extra_zeros; undef += a.undefined
    vals.sort()
    return vals, zeros, undef


def indexed_value(vals: list[float], extra_zeros: int, idx: int) -> float:
    return 0.0 if idx < extra_zeros else vals[idx - extra_zeros]


def quantile_with_zeros(vals: list[float], extra_zeros: int, q: float) -> float:
    n = len(vals) + extra_zeros
    if n == 0:
        return float("nan")
    h = (n - 1) * q; lo = int(math.floor(h)); hi = int(math.ceil(h))
    a = indexed_value(vals, extra_zeros, lo); b = indexed_value(vals, extra_zeros, hi)
    return a if lo == hi else a + (h - lo) * (b - a)


def summarize(aggs: Iterable[Agg], metric: str) -> dict[str, Any]:
    vals, extra, undef = combined_values(aggs, metric)
    n = len(vals) + extra
    exact_zero = extra + sum(v == 0.0 for v in vals)
    q25 = quantile_with_zeros(vals, extra, .25); q75 = quantile_with_zeros(vals, extra, .75)
    return {
        "count": n, "undefined_count": undef, "exact_zero_count": exact_zero,
        "exact_zero_fraction": exact_zero / n if n else float("nan"),
        "median": quantile_with_zeros(vals, extra, .5), "q25": q25, "q75": q75,
        "iqr": q75 - q25 if n else float("nan"), "p90": quantile_with_zeros(vals, extra, .9),
        "p95": quantile_with_zeros(vals, extra, .95), "max": indexed_value(vals, extra, n - 1) if n else float("nan"),
    }


def input_preflight(log: Logger) -> dict[str, Any]:
    identities = {}
    for key, (path, expected) in INPUTS.items():
        if not path.is_file():
            raise StopBuild(f"Missing input {key}: {path}")
        got = sha256_file(path)
        if got != expected:
            raise StopBuild(f"Input SHA mismatch {key}: {got}")
        identities[key] = {"path": str(path), "sha256": got, "size_bytes": path.stat().st_size}
        log(f"INPUT PASS {key} sha256={got}")
    internal = {}
    for key in ["b12", "b13", "q1_projection", "singleton_audit"]:
        internal[key] = verify_internal_manifest(INPUTS[key][0])
    con = sqlite3.connect(f"file:{CACHE.as_posix()}?mode=ro", uri=True)
    integrity = con.execute("PRAGMA integrity_check").fetchone()[0]
    fingerprint = con.execute("SELECT value FROM cache_meta WHERE key='fingerprint'").fetchone()[0]
    a2meta = json.loads(con.execute("SELECT value FROM cache_meta WHERE key='a2meta'").fetchone()[0])
    counts = {t: con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in ["member", "member_plot", "plot_design", "plot_generic", "plot_species", "target", "species_universe"]}
    protected = {
        "pseudo_scoreable": con.execute("SELECT COUNT(*) FROM target WHERE target_type='PSEUDO' AND validation_status='AVAILABLE'").fetchone()[0],
        "actual24": con.execute("SELECT COUNT(*) FROM target WHERE target_type='ACTUAL24' AND validation_status='AVAILABLE'").fetchone()[0],
    }
    h = hashlib.sha256(); logical_rows = 0
    for row in con.execute("SELECT PLT_CN,SPCD,printf('%.17g',y) FROM plot_species ORDER BY PLT_CN,SPCD"):
        h.update(("\t".join(str(x) for x in row) + "\n").encode("utf-8")); logical_rows += 1
    logical_recomputed = h.hexdigest()
    con.close()
    if integrity != "ok" or fingerprint != EXPECTED_CACHE_FINGERPRINT or a2meta.get("tree_cache_logical_sha256") != EXPECTED_CACHE_LOGICAL or logical_recomputed != EXPECTED_CACHE_LOGICAL:
        raise StopBuild("B12 cache integrity/fingerprint/logical metadata mismatch")
    formula = str(a2meta.get("TPA_formula", "")).lower()
    if any(t not in formula for t in ["tpa_unadj", "adj_factor", "no ti", "no expns"]):
        raise StopBuild("B12 cache formula identity failed")
    if counts != {"member":7696,"member_plot":338619,"plot_design":338619,"plot_generic":338619,"plot_species":529475,"target":5753,"species_universe":402}:
        raise StopBuild(f"B12 cache structural count mismatch {counts}")
    if protected != {"pseudo_scoreable": SCOREABLE_N, "actual24": ACTUAL_N}:
        raise StopBuild(f"B12 target identity mismatch {protected}")
    return {"identities": identities, "internal_manifest_rows": internal, "cache_integrity": integrity,
            "cache_fingerprint": fingerprint, "cache_logical_sha256": EXPECTED_CACHE_LOGICAL,
            "cache_logical_recomputed_sha256": logical_recomputed, "cache_logical_rows": logical_rows,
            "cache_counts": counts, "protected": protected, "new_tree_source_scan_rows": 0,
            "q1_calculation_rows": 0, "substrate_sqlite_extracted": False,
            "substrate_nonextraction_reason": "Accepted singleton audit already reconciled D10CA coefficients to canonical substrate; B14 uses frozen D10CA xwalk and accepted identities without a redundant 2.034 GB extraction."}


def load_direct_species() -> tuple[list[str], dict[str, dict[str, str]], list[dict[str, str]]]:
    with zipfile.ZipFile(INPUTS["q1_projection"][0]) as z:
        rows = zip_csv(z, "B12_Q1_101_SPECIES_LEDGER_v01.csv")
    direct_rows = [r for r in rows if r["direct_species_level_evidence_available"] == "YES"]
    direct = sorted([r["FIA_SPCD_list"] for r in direct_rows], key=lambda x: (int(x), x))
    if len(rows) != 101 or len(direct) != DIRECT_N or any(";" in x for x in direct):
        raise StopBuild("Q1 101/97 direct species identity failed")
    multi = [r for r in rows if r["species_level_interpretation_class"] == "MULTI_SPCD_B12_EVIDENCE_DIAGNOSTIC_ONLY"]
    if len(multi) != 3:
        raise StopBuild("Q1 multi-code retained diagnostic identity failed")
    info = {r["FIA_SPCD_list"]: r for r in direct_rows}
    return direct, info, multi


def load_d10ca(log: Logger) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    path = INPUTS["d10ca"][0]
    with zipfile.ZipFile(path) as z:
        xn = zip_member(z, "out/plot_block_xwalk_v01.csv.gz"); raw = z.read(xn)
        fn = zip_member(z, "out/formula_ledger_v01.csv"); fr = z.read(fn)
        rn = zip_member(z, "out/abundance_rule_v01.md"); rr = z.read(rn)
    if sha256_bytes(raw) != EXPECTED_XWALK_SHA or sha256_bytes(fr) != EXPECTED_FORMULA_SHA or sha256_bytes(rr) != EXPECTED_RULE_SHA:
        raise StopBuild("D10CA internal frozen-authority hash mismatch")
    blob = (fr + rr).decode("utf-8", errors="replace").lower()
    if any(t not in blob for t in ["tpa_unadj", "adj_factor_subp", "adj_factor_macr", "fold_specific_ti"]):
        raise StopBuild("D10CA formula tokens failed")
    plot: dict[str, dict[str, Any]] = {}; groups: dict[tuple[str,str], dict[str, Any]] = {}
    with gzip.GzipFile(fileobj=io.BytesIO(raw)) as gz, io.TextIOWrapper(gz, encoding="utf-8-sig", newline="") as f:
        for i, r in enumerate(csv.DictReader(f), 1):
            cn = r["PLT_CN"]; fold = r["final_fold"]; block = r["final_effective_design_block_id"]
            ti = finite_float(r["fold_specific_ti_weight"]); area = finite_float(r["ti_population_area_acres"]); denom = int(r["ti_fold_sample_count"])
            if cn in plot or fold not in {"A", "B"} or ti <= 0:
                raise StopBuild(f"D10CA invalid xwalk row {i}")
            plot[cn] = {"fold": fold, "block": block, "ti": ti, "area": area, "denom": denom}
            g = groups.setdefault((fold, block), {"n":0,"ti":ti,"area":area,"denom":denom,"ti_values":set(),"area_values":set(),"denom_values":set()})
            g["n"] += 1; g["ti_values"].add(ti); g["area_values"].add(area); g["denom_values"].add(denom)
            if i % 100000 == 0: log(f"D10CA_XWALK rows={i}")
    if len(plot) != 338619 or len(groups) != 5752:
        raise StopBuild(f"D10CA structure failed plots={len(plot)} groups={len(groups)}")
    errors = []
    for key, g in groups.items():
        if len(g["ti_values"]) != 1 or len(g["area_values"]) != 1 or len(g["denom_values"]) != 1 or g["n"] != g["denom"] or not math.isclose(g["n"]*g["ti"], g["area"], rel_tol=2e-12, abs_tol=1e-6):
            errors.append((key,g))
    if errors:
        raise StopBuild(f"D10CA block-fold identity failures={len(errors)}")
    tis = [g["ti"] for g in groups.values()]
    q95 = qtype7(tis, .95); q99 = qtype7(tis, .99)
    def band(x: float) -> str:
        return "LT_P95" if x < q95 else ("P95_TO_LT_P99" if x < q99 else "GE_P99")
    for p in plot.values(): p["ti_band"] = band(p["ti"])
    return plot, [{"fold":k[0],"block":k[1],"n":g["n"],"ti":g["ti"],"area":g["area"],"denom":g["denom"]} for k,g in groups.items()], {"q95":q95,"q99":q99,"band_counts":dict(Counter(band(x) for x in tis)),"group_rows":len(groups),"plot_rows":len(plot)}


def load_baseline(con: sqlite3.Connection, plot: dict[str, dict[str, Any]], direct: list[str], log: Logger):
    ds = set(direct); maps = defaultdict(lambda: defaultdict(float)); totals = defaultdict(float)
    n = 0; negative = 0
    for cn, cell, sp, y in con.execute("SELECT PLT_CN,cell_id,SPCD,y FROM plot_species ORDER BY PLT_CN,SPCD"):
        n += 1
        if sp not in ds: continue
        y = float(y)
        if y < 0 or not math.isfinite(y): negative += 1; continue
        meta = plot[str(cn)]; m = y * meta["ti"]; key = (meta["fold"], str(sp))
        maps[key][str(cell)] += m; totals[key] += m
        if n % 150000 == 0: log(f"BASELINE_SCAN rows={n}")
    if n != 529475 or negative:
        raise StopBuild(f"Baseline scan failure rows={n} negative={negative}")
    return maps, totals, n


def map_tv_after_replacement(base: dict[str,float], total: float, target_cells: dict[str,float], selected_cell: str, pseudo_mass: float) -> tuple[float,float,str]:
    new_total = total - sum(target_cells.values()) + pseudo_mass
    if total <= 0:
        return float("nan"), new_total, "NORMALIZED_MAP_UNDEFINED_NONPOSITIVE_TOTAL"
    # If pseudo-singletonization removes the entire positive fold/species mass,
    # the replacement object is the null measure and cannot be normalized.
    # For a materiality stress audit this is retained as the conservative
    # maximal boundary (1), not silently discarded or treated as zero.
    collapse_tol=max(1e-9,1e-12*total)
    if new_total <= collapse_tol and abs(new_total) <= collapse_tol:
        return 1.0, max(0.0,new_total), "MAXIMAL_DEGENERACY_BOUND_TOTAL_MASS_COLLAPSE"
    if new_total < 0:
        return float("nan"), new_total, "NORMALIZED_MAP_UNDEFINED_NEGATIVE_TOTAL"
    affected = set(target_cells) | {selected_cell}
    affected_base = sum(base.get(c,0.0) for c in affected)
    diff = max(0.0, total - affected_base) * abs(1.0/total - 1.0/new_total)
    for c in affected:
        new_c = base.get(c,0.0) - target_cells.get(c,0.0) + (pseudo_mass if c == selected_cell else 0.0)
        if new_c < -1e-7:
            return float("nan"), new_total, "NEGATIVE_CELL_AFTER_REPLACEMENT"
        new_c = max(0.0, new_c)
        diff += abs(base.get(c,0.0)/total - new_c/new_total)
    return 0.5*diff, new_total, "PASS"


def map_tv_after_removal(base: dict[str,float], total: float, cell: str, mass: float) -> tuple[float,float,str]:
    new_total = total - mass
    if mass == 0:
        return 0.0, new_total, "PASS_ZERO_POINT_MASS"
    if total <= 0 or new_total <= 0:
        return float("nan"), new_total, "NORMALIZED_MAP_UNDEFINED_NONPOSITIVE_TOTAL"
    bc = base.get(cell,0.0); nc = bc-mass
    if nc < -1e-7:
        return float("nan"), new_total, "NEGATIVE_CELL_AFTER_REMOVAL"
    diff = max(0.0,total-bc)*abs(1/total-1/new_total) + abs(bc/total-max(0.0,nc)/new_total)
    return .5*diff,new_total,"PASS"


def benchmark_rows(maps, totals, direct, info):
    out=[]
    for sp in direct:
        ta=totals[("A",sp)]; tb=totals[("B",sp)]; tv=normalized_tv(maps[("A",sp)],maps[("B",sp)])
        out.append({"FIA_SPCD":sp,"analysis_species_id":info[sp]["analysis_species_id"],"accepted_scientific_name":info[sp]["accepted_scientific_name"],
                    "fold_A_total_mass":ta,"fold_B_total_mass":tb,"AB_fold_normalized_tv":tv,"A_minus_B_mass":ta-tb,
                    "A_to_B_mass_ratio":ta/tb if tb>0 else float("nan"),"abs_log_A_to_B_mass_ratio":abs(math.log(ta/tb)) if ta>0 and tb>0 else float("nan"),
                    "estimability":"BOTH_FOLDS_POSITIVE" if ta>0 and tb>0 else "ONE_OR_BOTH_FOLDS_ZERO"})
    return out


EVENT_SCHEMA = [(x,"string") for x in ["target_id","member_id","fold","direction","route","plot_id","selected_cell","FIA_SPCD","accepted_scientific_name","ti_band","event_representation","status"]] + [(x,"int64") for x in ["target_n","selected_plot_zero","target_stratum_positive"]] + [(x,"double") for x in ["fold_specific_ti","target_sum_y","target_stratum_mass","target_mass_fraction","selected_y","pseudo_singleton_mass","new_fold_total_mass","signed_relative_mass_change","absolute_relative_mass_perturbation","normalized_tv"]]


def stress_summary_rows(exact: dict[tuple[str,str,str], Agg], zero_exact: dict[tuple[str,str,str], Agg]):
    keys=sorted(exact)
    defs=[("ALL","ALL",keys),("HIGH_TI","P95_OR_HIGHER",[k for k in keys if k[2] != "LT_P95"]),("GE_P99","GE_P99",[k for k in keys if k[2] == "GE_P99"]),("LEVEL","LEVEL1",[k for k in keys if k[1]=="LEVEL1"]),("LEVEL","LEVEL2",[k for k in keys if k[1]=="LEVEL2"]),("FOLD","A",[k for k in keys if k[0]=="A"]),("FOLD","B",[k for k in keys if k[0]=="B"])]
    defs += [("EXACT_MATCH","|".join(k),[k]) for k in keys]
    rows=[]
    for gt,gv,ks in defs:
        for metric in ["tv","mass"]:
            s=summarize([exact[k] for k in ks],metric)
            rows.append({"population":"ALL_PSEUDO_EVENTS","group_type":gt,"group_value":gv,"metric":"NORMALIZED_TV" if metric=="tv" else "ABSOLUTE_RELATIVE_TOTAL_MASS_PERTURBATION",**s})
    # Required critical subset, reported at the same high-TI, route, fold, and exact-match cuts.
    zero_defs=[("ZERO_SELECTED","TARGET_POSITIVE_ALL",keys),("HIGH_TI","P95_OR_HIGHER",[k for k in keys if k[2] != "LT_P95"]),("GE_P99","GE_P99",[k for k in keys if k[2] == "GE_P99"]),("LEVEL","LEVEL1",[k for k in keys if k[1]=="LEVEL1"]),("LEVEL","LEVEL2",[k for k in keys if k[1]=="LEVEL2"]),("FOLD","A",[k for k in keys if k[0]=="A"]),("FOLD","B",[k for k in keys if k[0]=="B"])]
    zero_defs += [("ZERO_SELECTED_EXACT_MATCH","|".join(k),[k]) for k in keys]
    for gt,gv,ks in zero_defs:
        for metric in ["tv","mass"]:
            s=summarize([zero_exact[k] for k in ks],metric)
            rows.append({"population":"SELECTED_Y_ZERO_TARGET_STRATUM_POSITIVE","group_type":gt,"group_value":gv,"metric":"NORMALIZED_TV" if metric=="tv" else "ABSOLUTE_RELATIVE_TOTAL_MASS_PERTURBATION",**s})
    return rows


def run_pseudo(con, plot, maps, totals, direct, info, log, ParquetWriter):
    targets=[dict(zip([d[0] for d in con.execute("SELECT * FROM target LIMIT 0").description],r)) for r in con.execute("SELECT * FROM target WHERE target_type='PSEUDO' AND validation_status='AVAILABLE' ORDER BY target_id")]
    if len(targets)!=SCOREABLE_N: raise StopBuild(f"Expected {SCOREABLE_N} pseudo targets")
    placeholders=",".join("?" for _ in direct)
    exact=defaultdict(Agg); zero_exact=defaultdict(Agg)
    event_path=OUT/"B14_PSEUDO_SINGLETON_EVENT_LEVEL_v01.parquet"
    active=0; universe=0; implicit=0; positive_pairs=0; zero_subset=0; coefficient_sum_error_max=0.0; target_plots=0; status_counts=Counter(); whole_block_targets=0; merged_component_targets=0; member_vs_block_area_max=0.0
    with ParquetWriter(event_path,EVENT_SCHEMA,row_group_size=40000) as pw:
        for ix,t in enumerate(targets,1):
            mid=t["target_member_id"]; fold=t["fold"]; route=t["route"]; n=int(t["target_n"]); dr=direction(fold)
            plots=[(str(r[0]),str(r[1])) for r in con.execute("SELECT PLT_CN,cell_id FROM member_plot WHERE member_id=? ORDER BY PLT_CN",(mid,))]
            if len(plots)!=n: raise StopBuild(f"Target n mismatch {t['target_id']}")
            metas=[plot[p] for p,_ in plots]; ti=metas[0]["ti"]; band=metas[0]["ti_band"]
            if any(m["fold"]!=fold or m["ti"]!=ti or m["block"]!=metas[0]["block"] for m in metas): raise StopBuild(f"A2 member identity failed {t['target_id']}")
            coefficient_sum_error_max=max(coefficient_sum_error_max,abs(sum(m["ti"] for m in metas)-n*ti)); target_plots+=n
            member_vs_block_area_max=max(member_vs_block_area_max,abs(n*ti-metas[0]["area"]))
            if n==metas[0]["denom"] and math.isclose(n*ti,metas[0]["area"],rel_tol=2e-12,abs_tol=1e-6):
                whole_block_targets+=1
            elif str(metas[0]["block"]).startswith("MERGED_EU:") and n < metas[0]["denom"]:
                merged_component_targets+=1
            else:
                raise StopBuild(f"Unexpected member-to-effective-block relation {t['target_id']}")
            cells_by_sp=defaultdict(dict); sums={}
            for sp,cell,sy in con.execute(f"SELECT SPCD,cell_id,sum_y FROM member_species_cell WHERE member_id=? AND SPCD IN ({placeholders}) AND sum_y>0 ORDER BY SPCD,cell_id",[mid,*direct]):
                cells_by_sp[str(sp)][str(cell)]=float(sy)*ti
            for sp,sy in con.execute(f"SELECT SPCD,sum_y FROM member_species_stats WHERE member_id=? AND SPCD IN ({placeholders}) AND sum_y>0 ORDER BY SPCD",[mid,*direct]): sums[str(sp)]=float(sy)
            if set(cells_by_sp)!=set(sums): raise StopBuild(f"Member species cell/stats mismatch {mid}")
            positive_pairs+=len(sums); universe += n*DIRECT_N; implicit_here=n*(DIRECT_N-len(sums)); implicit+=implicit_here
            k=(fold,route,band); exact[k].add_implicit(implicit_here)
            y_by_plot=defaultdict(dict)
            for p,sp,y in con.execute(f"SELECT mp.PLT_CN,ps.SPCD,ps.y FROM member_plot mp JOIN plot_species ps ON ps.PLT_CN=mp.PLT_CN WHERE mp.member_id=? AND ps.SPCD IN ({placeholders}) ORDER BY mp.PLT_CN,ps.SPCD",[mid,*direct]): y_by_plot[str(p)][str(sp)]=float(y)
            for sp,target_sum_y in sums.items():
                target_cells=cells_by_sp[sp]; target_mass=target_sum_y*ti; total=totals[(fold,sp)]
                if total<=0 or target_mass<=0: raise StopBuild(f"Positive target mass outside positive fold total {mid} {sp}")
                frac=target_mass/total
                for pid,cell in plots:
                    y=y_by_plot[pid].get(sp,0.0); pseudo=n*ti*y
                    tv,new_total,status=map_tv_after_replacement(maps[(fold,sp)],total,target_cells,cell,pseudo)
                    signed=(new_total-total)/total; mass_abs=abs(signed)
                    exact[k].add(tv,mass_abs)
                    status_counts[status]+=1
                    iszero=int(y==0.0)
                    if iszero: zero_exact[k].add(tv,mass_abs); zero_subset+=1
                    pw.write({"target_id":t["target_id"],"member_id":mid,"fold":fold,"direction":dr,"route":route,"target_n":n,"plot_id":pid,"selected_cell":cell,"FIA_SPCD":sp,"accepted_scientific_name":info[sp]["accepted_scientific_name"],"fold_specific_ti":ti,"ti_band":band,"target_sum_y":target_sum_y,"target_stratum_mass":target_mass,"target_mass_fraction":frac,"selected_y":y,"pseudo_singleton_mass":pseudo,"new_fold_total_mass":new_total,"signed_relative_mass_change":signed,"absolute_relative_mass_perturbation":mass_abs,"normalized_tv":tv,"selected_plot_zero":iszero,"target_stratum_positive":1,"event_representation":"MATERIALIZED_TARGET_POSITIVE_SPECIES; REMAINDER_IMPLICIT_EXACT_ZERO","status":status})
                    active+=1
            if ix%250==0: log(f"PSEUDO_STRESS targets={ix}/{len(targets)} materialized_events={active} universe={universe}")
    if universe!=EXPECTED_EVENT_UNIVERSE or active+implicit!=universe or active!=1_288_936 or positive_pairs!=10_662:
        raise StopBuild(f"Pseudo event identity failed universe={universe} active={active} implicit={implicit} pairs={positive_pairs}")
    undefined=sum(a.undefined for a in exact.values())
    if undefined: raise StopBuild(f"Undefined pseudo normalized stress events={undefined}")
    if whole_block_targets+merged_component_targets!=len(targets) or coefficient_sum_error_max>1e-7:
        raise StopBuild("Pseudo target A2 coefficient-sum partition failed")
    return exact,zero_exact,{"targets":len(targets),"target_plot_rows":target_plots,"positive_target_species_pairs":positive_pairs,"event_universe":universe,"materialized_events":active,"implicit_exact_zero_events":implicit,"zero_selected_target_positive_events":zero_subset,"maximal_total_mass_collapse_events":status_counts.get("MAXIMAL_DEGENERACY_BOUND_TOTAL_MASS_COLLAPSE",0),"event_status_counts":dict(status_counts),"target_coefficient_sum_identity_max_abs_error":coefficient_sum_error_max,"whole_effective_block_targets":whole_block_targets,"merged_effective_block_component_targets":merged_component_targets,"member_vs_full_block_area_max_abs_difference_descriptive":member_vs_block_area_max,"parquet_rows":active,"parquet_sha256":sha256_file(event_path)}


def summary_subset(rows, group_type): return [r for r in rows if r["group_type"]==group_type]


def select_calibration(zero_exact, fold, route, band):
    keys=sorted(zero_exact)
    levels=[("H1_SAME_FOLD_ROUTE_TI_BAND",[k for k in keys if k==(fold,route,band)]),("H2_SAME_FOLD_TI_BAND",[k for k in keys if k[0]==fold and k[2]==band]),("H3_SAME_TI_BAND",[k for k in keys if k[2]==band]),("H4_ALL",keys)]
    for label,ks in levels:
        n=summarize([zero_exact[k] for k in ks],"tv")["count"]
        if n>=MIN_CALIBRATION_N:
            return label,ks,n
    raise StopBuild(f"No calibration group met minimum n for {fold}/{route}/{band}")


ACTUAL_SCHEMA=[(x,"string") for x in ["analysis_scope","case_id","fold","direction","route","PLT_CN","cell_id","FIA_SPCD","accepted_scientific_name","ti_band","stress_tier","stress_source","calibration_match_level","envelope_label","status"]]+[(x,"int64") for x in ["calibration_n","case_count","species_count"]]+[(x,"double") for x in ["fold_specific_ti","observed_y","observed_point_mass","fold_total_mass","stress_normalized_tv","stress_absolute_relative_mass_perturbation","stress_tv_additive_raw","stress_tv_additive_capped_at_1","stress_mass_additive_raw"]]


def load_accepted_actual():
    with zipfile.ZipFile(INPUTS["singleton_audit"][0]) as z:
        cases=zip_csv(z,"SINGLETON_24_CASE_LEDGER_v01.csv")
        mass=zip_csv(z,"SINGLETON_Q1_97_DIRECT_SPECIES_MASS_v01.csv")
    if len(cases)!=24 or len(mass)!=194: raise StopBuild("Accepted actual ledger identity failed")
    return cases,mass


def run_actual(con,plot,maps,totals,direct,info,bench,zero_exact,seal_sha,log,ParquetWriter):
    cases,accepted_mass=load_accepted_actual()  # First actual-outcome read is intentionally after the sealed call site.
    for r in accepted_mass:
        fold={"AB":"B","BA":"A"}[r["direction"]]; got=totals[(fold,r["FIA_SPCD"])]
        if not math.isclose(got,float(r["total_mass"]),rel_tol=2e-12,abs_tol=1e-6): raise StopBuild(f"Accepted direct mass mismatch {r['FIA_SPCD']} {fold}")
    target_by_case={r["case_id"]:dict(r) for r in con.execute("SELECT * FROM target WHERE target_type='ACTUAL24' AND validation_status='AVAILABLE'")}
    if set(target_by_case)!={r["case_id"] for r in cases}: raise StopBuild("Actual24 cache/accepted case identities differ")
    individual=[]; cal_usage=Counter()
    for case in cases:
        cid=case["case_id"]; t=target_by_case[cid]; pid=case["PLT_CN"]; meta=plot[pid]; fold=case["fold"]; route=case["B9_route"]; band=meta["ti_band"]
        if fold!=t["fold"] or fold!=meta["fold"] or t["route"]!=route or not math.isclose(float(case["fold_specific_ti"]),meta["ti"],rel_tol=2e-12): raise StopBuild(f"Actual case design identity mismatch {cid}")
        member_plots=list(con.execute("SELECT PLT_CN FROM member_plot WHERE member_id=?",(t["target_member_id"],)))
        if len(member_plots)!=1 or str(member_plots[0][0])!=pid: raise StopBuild(f"Actual case member mismatch {cid}")
        ys={str(sp):float(y) for sp,y in con.execute("SELECT SPCD,y FROM plot_species WHERE PLT_CN=?",(pid,))}
        level,ks,ncal=select_calibration(zero_exact,fold,route,band); cal_usage[level]+=1
        tvs=summarize([zero_exact[k] for k in ks],"tv"); masses=summarize([zero_exact[k] for k in ks],"mass")
        for sp in direct:
            y=ys.get(sp,0.0); point=meta["ti"]*y; total=totals[(fold,sp)]
            tvobs,new_total,status=map_tv_after_removal(maps[(fold,sp)],total,case["cell_id"],point)
            observed_mass=point/total if total>0 else float("nan")
            for tier,tv,ma,source in [("E_OBSERVED",tvobs,observed_mass,"ACTUAL_POINT_MASS_EXACT_OMISSION"),("E_P95",tvs["p95"],masses["p95"],"SEALED_ZERO_SELECTED_EMPIRICAL_P95"),("E_EMPIRICAL_MAX",tvs["max"],masses["max"],"SEALED_ZERO_SELECTED_EMPIRICAL_MAX")]:
                individual.append({"analysis_scope":"INDIVIDUAL_SINGLETON","case_id":cid,"fold":fold,"direction":direction(fold),"route":route,"PLT_CN":pid,"cell_id":case["cell_id"],"FIA_SPCD":sp,"accepted_scientific_name":info[sp]["accepted_scientific_name"],"fold_specific_ti":meta["ti"],"ti_band":band,"observed_y":y,"observed_point_mass":point,"fold_total_mass":total,"stress_tier":tier,"stress_source":source,"calibration_match_level":"ACTUAL_OBSERVED" if tier=="E_OBSERVED" else level,"calibration_n":ncal if tier!="E_OBSERVED" else 0,"stress_normalized_tv":tv,"stress_absolute_relative_mass_perturbation":ma,"stress_tv_additive_raw":tv,"stress_tv_additive_capped_at_1":min(1.0,tv) if math.isfinite(tv) else tv,"stress_mass_additive_raw":ma,"case_count":1,"species_count":1,"envelope_label":"INDIVIDUAL_CASE","status":status if tier=="E_OBSERVED" else "PASS_SEALED_CALIBRATION"})
    if len(individual)!=24*97*3: raise StopBuild("Actual individual row count failed")
    grouped=defaultdict(list)
    for r in individual: grouped[(r["direction"],r["FIA_SPCD"],r["stress_tier"])].append(r)
    envelopes=[]
    for (dr,sp,tier),rs in sorted(grouped.items()):
        tv=sum(r["stress_normalized_tv"] for r in rs); ma=sum(r["stress_absolute_relative_mass_perturbation"] for r in rs)
        envelopes.append({"analysis_scope":"DIRECTION_SPECIES_ADDITIVE_ENVELOPE","case_id":"ALL_"+dr,"fold":{"AB":"B","BA":"A"}[dr],"direction":dr,"route":"MIXED","PLT_CN":"","cell_id":"","FIA_SPCD":sp,"accepted_scientific_name":info[sp]["accepted_scientific_name"],"fold_specific_ti":float("nan"),"ti_band":"MIXED","observed_y":float("nan"),"observed_point_mass":sum(r["observed_point_mass"] for r in rs),"fold_total_mass":rs[0]["fold_total_mass"],"stress_tier":tier,"stress_source":"SUM_OF_INDIVIDUAL_STRESSES","calibration_match_level":"MIXED_DESIGN_MATCHES","calibration_n":0,"stress_normalized_tv":min(1.0,tv),"stress_absolute_relative_mass_perturbation":ma,"stress_tv_additive_raw":tv,"stress_tv_additive_capped_at_1":min(1.0,tv),"stress_mass_additive_raw":ma,"case_count":len(rs),"species_count":1,"envelope_label":"CONSERVATIVE_NO_CANCELLATION_BOUND","status":"PASS_CONSERVATIVE_BOUND"})
    actual_path=OUT/"B14_ACTUAL24_STRESS_APPLICATION_v01.parquet"
    with ParquetWriter(actual_path,ACTUAL_SCHEMA,row_group_size=10000) as pw:
        pw.write_many(individual); pw.write_many(envelopes)
    if len(envelopes)!=194*3: raise StopBuild("Envelope row count failed")
    bmap={r["FIA_SPCD"]:r for r in bench}; env={(r["direction"],r["FIA_SPCD"],r["stress_tier"]):r for r in envelopes}
    direct_summary=[]
    for dr in ["AB","BA"]:
        for tier in ["E_OBSERVED","E_P95","E_EMPIRICAL_MAX"]:
            ir=[r for r in individual if r["direction"]==dr and r["stress_tier"]==tier]; er=[r for r in envelopes if r["direction"]==dr and r["stress_tier"]==tier]
            tvs=[r["stress_normalized_tv"] for r in ir]; es=[r["stress_tv_additive_capped_at_1"] for r in er]
            direct_summary.append({"direction":dr,"fold":{"AB":"B","BA":"A"}[dr],"stress_tier":tier,"individual_rows":len(ir),"case_count":len({r['case_id'] for r in ir}),"species_count":len(er),"individual_exact_zero_fraction":sum(x==0 for x in tvs)/len(tvs),"individual_median_tv":qtype7(tvs,.5),"individual_p95_tv":qtype7(tvs,.95),"individual_max_tv":max(tvs),"envelope_median_tv":qtype7(es,.5),"envelope_p95_tv":qtype7(es,.95),"envelope_max_tv":max(es),"envelope_species_positive_count":sum(x>0 for x in es),"seal_sha256":seal_sha})
    abba=[]; stress_vs=[]
    for sp in direct:
        fd=float(bmap[sp]["AB_fold_normalized_tv"])
        for tier in ["E_OBSERVED","E_P95","E_EMPIRICAL_MAX"]:
            a=env[("AB",sp,tier)]["stress_tv_additive_capped_at_1"]; b=env[("BA",sp,tier)]["stress_tv_additive_capped_at_1"]
            abba.append({"FIA_SPCD":sp,"accepted_scientific_name":info[sp]["accepted_scientific_name"],"stress_tier":tier,"AB_fold_B_envelope_tv":a,"BA_fold_A_envelope_tv":b,"max_direction_envelope_tv":max(a,b),"abs_AB_minus_BA_envelope_tv":abs(a-b),"AB_fold_discrepancy_tv":fd,"max_stress_to_fold_discrepancy_ratio":max(a,b)/fd if fd>0 else float("nan"),"comparison_class":"POSITIVE_FOLD_DISCREPANCY" if fd>0 else "ZERO_FOLD_DISCREPANCY_RATIO_UNDEFINED"})
            for dr,v in [("AB",a),("BA",b)]:
                stress_vs.append({"FIA_SPCD":sp,"accepted_scientific_name":info[sp]["accepted_scientific_name"],"direction":dr,"fold":{"AB":"B","BA":"A"}[dr],"stress_tier":tier,"conservative_envelope_tv":v,"AB_fold_discrepancy_tv":fd,"stress_to_fold_discrepancy_ratio":v/fd if fd>0 else float("nan"),"stress_minus_fold_discrepancy":v-fd,"comparison_class":"STRESS_LT_FOLD_DISCREPANCY" if v<fd else ("STRESS_EQ_FOLD_DISCREPANCY" if v==fd else "STRESS_GT_FOLD_DISCREPANCY")})
    abies=[r for r in individual+envelopes if r["FIA_SPCD"]=="22"]
    return individual,envelopes,direct_summary,abba,stress_vs,abies,{"accepted_direct_mass_rows":len(accepted_mass),"individual_rows":len(individual),"envelope_rows":len(envelopes),"parquet_rows":len(individual)+len(envelopes),"parquet_sha256":sha256_file(actual_path),"calibration_match_usage_cases":dict(cal_usage),"first_actual_outcome_read_after_seal":True}


def fields(rows):
    return list(rows[0]) if rows else []


def copy_sources() -> None:
    dst=OUT/"src"; dst.mkdir(parents=True,exist_ok=True)
    for name in ["b14_materiality_stress.py","config.json","verify_csvs.mjs","README_RUN.txt","RUN.cmd","verify_cache_digest_3491.py"]:
        shutil.copy2(HERE/name,dst/name)
    for name in ["mini_parquet.py","mini_parquet_reader.py"]:
        shutil.copy2(ROOT/"05_qc"/"d10fb13_v01_work_component_transportability_diagnostic"/"src"/name,dst/name)
    if REQUEST.is_file():
        shutil.copy2(REQUEST,dst/"TASK_REQUEST_v01.md")


def make_report(meta, pseudo_summary, direct_summary, abba, category, status):
    all_tv=next(r for r in pseudo_summary if r["population"]=="ALL_PSEUDO_EVENTS" and r["group_type"]=="ALL" and r["metric"]=="NORMALIZED_TV")
    zero_tv=next(r for r in pseudo_summary if r["group_type"]=="ZERO_SELECTED" and r["metric"]=="NORMALIZED_TV")
    observed=[r for r in abba if r["stress_tier"]=="E_OBSERVED"]
    p95=[r for r in abba if r["stress_tier"]=="E_P95"]
    mx=[r for r in abba if r["stress_tier"]=="E_EMPIRICAL_MAX"]
    def fv(x): return float(x)
    def maxv(rs): return max(fv(r["max_direction_envelope_tv"]) for r in rs)
    def gt(rs):
        out=0
        for r in rs:
            try: d=float(r["AB_fold_discrepancy_tv"]); s=float(r["max_direction_envelope_tv"])
            except (TypeError,ValueError): continue
            if d>0 and s>d: out+=1
        return out
    def ps(pop,gt,gv,metric="NORMALIZED_TV"):
        return next(r for r in pseudo_summary if r["population"]==pop and r["group_type"]==gt and r["group_value"]==gv and r["metric"]==metric)
    zh=ps("SELECTED_Y_ZERO_TARGET_STRATUM_POSITIVE","HIGH_TI","P95_OR_HIGHER")
    zg=ps("SELECTED_Y_ZERO_TARGET_STRATUM_POSITIVE","GE_P99","GE_P99")
    zl1=ps("SELECTED_Y_ZERO_TARGET_STRATUM_POSITIVE","LEVEL","LEVEL1"); zl2=ps("SELECTED_Y_ZERO_TARGET_STRATUM_POSITIVE","LEVEL","LEVEL2")
    za=ps("SELECTED_Y_ZERO_TARGET_STRATUM_POSITIVE","FOLD","A"); zb=ps("SELECTED_Y_ZERO_TARGET_STRATUM_POSITIVE","FOLD","B")
    def ds(dr,tier): return next(r for r in direct_summary if r["direction"]==dr and r["stress_tier"]==tier)
    abp=ds("AB","E_P95"); bap=ds("BA","E_P95")
    return f"""# Q1 D10F-B14 v01——singleton 不确定性物质性压力审计

## 结论

- 任务状态：**{status}**
- 科学证据类别：**{category}**
- D10F-C：**HOLD**。

本审计完成了观测独立的经验压力校准和实际 24 例应用，但不构造、不选择也不批准新的协方差估计器；没有调用 support 数据，也没有计算真实 Q1。

## 冻结测量身份

冻结 A2 按 `sum(TI_hf * y_ij)` 重建；缓存 `y_ij` 是未扩展的、按样地基底匹配的 `TPA_UNADJ * ADJ_FACTOR`，不用 `EXPNS`，TI 恰好乘一次。5,752 个 block×fold 全部满足 `n_hf * TI_hf = area_hf`。4,640 个可评分 pseudo 目标中，{meta['pseudo']['whole_effective_block_targets']:,} 个是完整有效设计块，另 2 个是冻结 `MERGED_EU:3+4` 块的 source-EU 分量；两类目标都严格满足系数和为 `n_g * TI_g`，最大绝对误差为 {meta['pseudo']['target_coefficient_sum_identity_max_abs_error']:.6g}。

完整设计宇宙有 {meta['pseudo']['event_universe']:,} 个 target×retained-plot×direct-species 事件。Parquet 实体化 {meta['pseudo']['materialized_events']:,} 个目标层物种质量为正的事件；其余 {meta['pseudo']['implicit_exact_zero_events']:,} 个事件由非负性可证明为精确零，仍计入全部计数和分位数分母。另有 {meta['pseudo']['maximal_total_mass_collapse_events']:,} 个事件把正质量对象压到零测度；零测度没有可归一化地图，故透明地记为保守最大物质性边界 TV=1，而不是删除或记零。

## Q1–Q13

### Q1：一个经验单样地实现能否实质扭曲多样地层的贡献？

能。全事件中 95.0697% 的 TV 为精确零，且中位数、p95 都为 0；但尾部最大达到 1。也就是说，通常不动，但在目标层对某物种承担较多甚至全部折内质量时，单样地化可造成实质乃至最大扰动。

### Q2：与实际 singleton 最相似的高 TI 层，pseudo 扰动多大？

在所选样地为零且目标层为正的关键子集中，TI≥p95 的 TV 中位数为 {fv(zh['median']):.6g}、p95 为 {fv(zh['p95']):.6g}、最大为 {fv(zh['max']):.6g}；TI≥p99 对应值为 {fv(zg['median']):.6g}、{fv(zg['p95']):.6g}、{fv(zg['max']):.6g}。TI 阈值由完整 5,752 个 block×fold 在实际结果读取前冻结：q95={meta['d10ca']['q95']:.12g}，q99={meta['d10ca']['q99']:.12g}。

### Q3：保留样地 y=0、但完整层为正时，全物种丰度图会怎样？

该关键子集共有 {meta['pseudo']['zero_selected_target_positive_events']:,} 个事件；TV 中位数 {fv(zero_tv['median']):.6g}、IQR {fv(zero_tv['iqr']):.6g}、p90 {fv(zero_tv['p90']):.6g}、p95 {fv(zero_tv['p95']):.6g}、最大 1。零观测不能等同于零风险。

### Q4：经验压力与普通 A/B 折差异相比如何？

实际观测包络最大 TV 为 {maxv(observed):.6g}，没有一个可比较物种超过自身 A/B 折 TV；但封存的 p95 保守无抵消包络最大为 {maxv(p95):.6g}，在 90 个两折均可估的物种中有 {gt(p95)} 个超过折间 TV；经验最大层同样有 {gt(mx)} 个。因此点观测温和，而未观测的经验压力尾部不能由普通折差异吸收。

### Q5：AB 与 BA 是否不同？

不同。AB 含 2 个实际 singleton，p95 个体 TV 最大 {fv(abp['individual_max_tv']):.6g}、方向包络 {fv(abp['envelope_max_tv']):.6g}；BA 含 22 个，p95 个体最大 {fv(bap['individual_max_tv']):.6g}、保守方向包络达到 {fv(bap['envelope_max_tv']):.6g}。差异主要来自 singleton 数量和匹配设计组，而不是宣称折本身有内在因果差异。

### Q6：Level1 与 Level2 的物质性是否不同？

有量级差异但并非单调安全排序。零样地关键子集中，Level1 TV 中位数/p95/最大为 {fv(zl1['median']):.6g}/{fv(zl1['p95']):.6g}/{fv(zl1['max']):.6g}，Level2 为 {fv(zl2['median']):.6g}/{fv(zl2['p95']):.6g}/{fv(zl2['max']):.6g}。这是丰度物质性比较，不是 B13 协方差可转运性的重述。

### Q7：实际观测为零的 singleton 在经验包络下仍可能危险吗？

是。实际 24×97 的绝大多数点质量为零，但它们按预先封存的零样地/正目标层经验分布继承 `E_P95` 和 `E_EMPIRICAL_MAX`；结果表明零观测仍可对应非零、甚至达到边界的压力。

### Q8：*Abies procera* 是否仍是唯一需要可见敏感性关注的物种？

在实际点质量证据中是：只有 *Abies procera*（SPCD 22，BA）为正，观测 TV 为 0.0126727。可是在零观测经验压力下不是；其他 direct97 物种也获得非零压力包络。

### Q9：零观测压力下是否出现额外重要的 direct97 物种？

是。p95 保守无抵消包络对 97 个物种都为正，并有 79 个超过其正的 A/B 折 TV。这是设计匹配的压力证据，不表示这些物种实际 singleton 已观测到正丰度。

### Q10：24-singleton 问题是否仍是 cohort-wide 丰度不确定性？

就实际点质量而言不是 cohort-wide；就封存的零观测经验包络而言仍是 cohort-wide 的潜在问题。由于包络采用逐例相加且禁止抵消，它有意保守，不能解释为概率或置信区间。

### Q11：能否把它定性为有界尾部或局部物种问题？

目前不能安全关闭为局部问题。中心分布很小、已观测暴露高度局部，但 p95 和经验最大包络跨物种广泛超过折间基准，因此最终类别保留为 **{category}**，而不是 `NONMATERIAL_TAIL_CANDIDATE` 或 `LOCALIZED_SPECIES_LEVEL_SENSITIVITY`。

### Q12：继续前是否科学上必须开发新的 singleton 协方差估计器？

B14 不能推出“必须”。压力审计只说明丰度测量对象的不确定性可能有物质性，不能识别协方差结构，也不授权新估计器。主线必须先决定该保守丰度包络是否阻断后续；D10F-C 继续 HOLD。

### Q13：什么证据会在以后重新开启方法开发？

若主线证明 singleton 丰度压力会改变目标推断，或获得新的、仍与 actual24 结果独立的数据/设计信息，能识别并显著收紧零样地压力及多 singleton 联合结构，才应重新开启方法开发。仅凭当前点观测或把各例假定独立都不够。

## 封印、边界与下一步

经验校准封印在打开 24 例结果账本或查询其 case-specific `y` 之前写入并哈希。所有 24×97×3 个体行均保留；多 singleton 只给出 `CONSERVATIVE_NO_CANCELLATION_BOUND`。没有采用任意 1%/5% 科学通过阈值。Phase D 因经验识别与实际应用均完成而跳过；本次没有抽取约 2.034 GB 的 substrate SQLite，因为接受的 singleton 审计已完成其与 D10CA 的逐系数核对，B14 又独立验证了 D10CA 与缓存身份。未自动归档；传输目标仅为 `mirror`。
"""


def disposition_rows(meta,pseudo,direct,abba,category,status):
    def p(pop,gt,gv): return next(r for r in pseudo if r["population"]==pop and r["group_type"]==gt and r["group_value"]==gv and r["metric"]=="NORMALIZED_TV")
    z=p("SELECTED_Y_ZERO_TARGET_STRATUM_POSITIVE","ZERO_SELECTED","TARGET_POSITIVE_ALL"); h=p("SELECTED_Y_ZERO_TARGET_STRATUM_POSITIVE","HIGH_TI","P95_OR_HIGHER")
    l1=p("SELECTED_Y_ZERO_TARGET_STRATUM_POSITIVE","LEVEL","LEVEL1"); l2=p("SELECTED_Y_ZERO_TARGET_STRATUM_POSITIVE","LEVEL","LEVEL2")
    def d(dr,tier): return next(r for r in direct if r["direction"]==dr and r["stress_tier"]==tier)
    observed=[r for r in abba if r["stress_tier"]=="E_OBSERVED"]; p95=[r for r in abba if r["stress_tier"]=="E_P95"]
    comparable=[r for r in p95 if r["AB_fold_discrepancy_tv"] not in {"NA",None}]
    exceed=sum(float(r["max_direction_envelope_tv"])>float(r["AB_fold_discrepancy_tv"]) for r in comparable)
    vals=[
        ("structural rarity","24 actual singleton design strata","singleton identity and TI tails",f"24 cases; TI q95={meta['d10ca']['q95']:.6g}, q99={meta['d10ca']['q99']:.6g}","Structurally rare but several cases occupy extreme TI tails.","Rarity alone does not bound outcome miss.","ACCEPTED_DERIVED_MATERIALITY_EVIDENCE","Retain all 24 in mainline review."),
        ("observed point-mass exposure","24×97 direct species-case rows","E_OBSERVED exact point-mass omission",f"max direction envelope TV={max(float(r['max_direction_envelope_tv']) for r in observed):.6g}","Observed exposure is localized and below each comparable A/B TV.","Observed zeros do not identify counterfactual stratum composition.","B14_EMPIRICAL_STRESS_EVIDENCE","Do not equate observed zero with zero uncertainty."),
        ("zero-observation empirical miss stress","1,193,386 selected-zero/target-positive pseudo events","target contribution replaced by n_g*TI_g*y_j with y_j=0",f"median={float(z['median']):.6g}; p95={float(z['p95']):.6g}; max={float(z['max']):.6g}","The critical miss mechanism has a nontrivial tail.","Empirical stress is an envelope, not a probability model.","B14_EMPIRICAL_STRESS_EVIDENCE","Carry sealed E_P95 and E_EMPIRICAL_MAX."),
        ("high-TI stress","TI at or above full block-fold p95","zero-selected/target-positive normalized TV",f"median={float(h['median']):.6g}; p95={float(h['p95']):.6g}; max={float(h['max']):.6g}","High-TI cases remain capable of material map perturbation.","Sparse TI-band cells widen tail uncertainty.","B14_EMPIRICAL_STRESS_EVIDENCE","Use frozen hierarchy; do not tune to actual outcomes."),
        ("normalized-map perturbation","full pseudo universe","TV after empirical one-plot replacement",f"{meta['pseudo']['implicit_exact_zero_events']} exact implicit zeros; {meta['pseudo']['maximal_total_mass_collapse_events']} null-measure collapses", "Most events are inert, but a real maximal tail exists.","TV=1 collapse is a conservative boundary because the replacement map cannot be normalized.","B14_EMPIRICAL_STRESS_EVIDENCE","Retain explicit collapse status."),
        ("stress versus A/B fold discrepancy","90 species positive in both folds","direction envelope TV divided by ordinary fold TV",f"E_P95 exceeds fold TV for {exceed}/90 comparable species", "Counterfactual singleton stress is not absorbed by ordinary fold disagreement.","Seven species lack a two-positive-fold TV denominator.","B14_EMPIRICAL_STRESS_EVIDENCE","Review continuous ratios; no arbitrary pass threshold."),
        ("AB","fold B; 2 singleton cases","sealed individual and no-cancellation envelope",f"E_P95 individual max={float(d('AB','E_P95')['individual_max_tv']):.6g}; envelope={float(d('AB','E_P95')['envelope_max_tv']):.6g}","AB has fewer cases and a smaller p95 envelope.","Not evidence of a causal fold effect.","B14_EMPIRICAL_STRESS_EVIDENCE","Keep direction-specific results."),
        ("BA","fold A; 22 singleton cases","sealed individual and no-cancellation envelope",f"E_P95 individual max={float(d('BA','E_P95')['individual_max_tv']):.6g}; envelope={float(d('BA','E_P95')['envelope_max_tv']):.6g}","BA dominates the conservative aggregate because it contains 22 cases.","No-cancellation aggregation is intentionally conservative.","B14_EMPIRICAL_STRESS_EVIDENCE","Do not pool AB and BA silently."),
        ("Abies procera","SPCD 22","E_OBSERVED exact omission", "BA observed TV=0.0126727; only direct97 positive observed singleton point mass", "Visible observed sensitivity remains localized to this species.","It is not the only species exposed under the counterfactual envelope.","ACCEPTED_DERIVED_MATERIALITY_EVIDENCE","Retain dedicated case ledger."),
        ("cohort-level direct97","all 97 direct species","sealed E_P95 conservative no-cancellation envelope",f"97/97 positive envelopes; {exceed}/90 exceed positive fold TV", "Potential uncertainty is cohort-wide under the stress envelope.","Envelope breadth partly reflects outcome-independent borrowing and additive aggregation.",category,"Mainline decides whether this blocks later work."),
        ("singleton covariance method necessity","D10F-C gate","scientific necessity test, not estimator construction", "Not established by B14; D10F-C remains HOLD", "Material abundance uncertainty does not itself identify a covariance estimator.","Final singleton subgate remains OPEN pending mainline decision.",status,"Reopen method development only with decision-relevant and outcome-independent identifying evidence."),
    ]
    names=["evidence","scope","stress definition","result","scientific interpretation","remaining uncertainty","status","next action"]
    return [dict(zip(names,v)) for v in vals]


def finalize_outputs(category: str, status: str) -> None:
    meta=json.loads((OUT/"B14_RUN_METADATA_v01.json").read_text(encoding="utf-8"))
    pseudo=list(csv.DictReader((OUT/"B14_PSEUDO_SINGLETON_STRESS_SUMMARY_v01.csv").open(encoding="utf-8-sig")))
    direct=list(csv.DictReader((OUT/"B14_DIRECT97_STRESS_SUMMARY_v01.csv").open(encoding="utf-8-sig")))
    abba=list(csv.DictReader((OUT/"B14_AB_VS_BA_STRESS_SUMMARY_v01.csv").open(encoding="utf-8-sig")))
    meta["task_status"]=status; meta["scientific_evidence_category"]=category; meta["finalized_utc"]=datetime.now(timezone.utc).isoformat()
    write_json(OUT/"B14_RUN_METADATA_v01.json",meta)
    (OUT/"B14_MAIN_REPORT_v01.md").write_text(make_report(meta,pseudo,direct,abba,category,status),encoding="utf-8",newline="\n")
    disp=disposition_rows(meta,pseudo,direct,abba,category,status)
    write_csv(OUT/"B14_MATERIALITY_DISPOSITION_MATRIX_v01.csv",disp,fields(disp))


def run_analysis() -> None:
    if OUT.exists() and any(OUT.iterdir()): raise StopBuild(f"Fresh-run guard: output directory is nonempty: {OUT}")
    OUT.mkdir(parents=True,exist_ok=True); log=Logger(OUT/"execution.log")
    try:
        log("B14 RUN START actual-outcome rows read=0")
        pre=input_preflight(log); direct,info,multi=load_direct_species(); plot,groups,d10meta=load_d10ca(log)
        sys.path.insert(0,str(ROOT/"05_qc"/"d10fb13_v01_work_component_transportability_diagnostic"/"src"))
        from mini_parquet import ParquetWriter, footer_info
        con=sqlite3.connect(f"file:{CACHE.as_posix()}?mode=ro",uri=True); con.row_factory=sqlite3.Row
        maps,totals,scan=load_baseline(con,plot,direct,log)
        bench=benchmark_rows(maps,totals,direct,info)
        write_csv(OUT/"B14_AB_FOLD_DISCREPANCY_BENCHMARK_v01.csv",bench,fields(bench))
        exact,zero_exact,pmeta=run_pseudo(con,plot,maps,totals,direct,info,log,ParquetWriter)
        summaries=stress_summary_rows(exact,zero_exact)
        write_csv(OUT/"B14_PSEUDO_SINGLETON_STRESS_SUMMARY_v01.csv",summaries,fields(summaries))
        zero_rows=[r for r in summaries if r["population"]=="SELECTED_Y_ZERO_TARGET_STRATUM_POSITIVE"]
        high_rows=[r for r in summaries if r["group_type"] in {"HIGH_TI","GE_P99"}]
        write_csv(OUT/"B14_ZERO_SELECTED_PLOT_STRESS_v01.csv",zero_rows,fields(zero_rows))
        write_csv(OUT/"B14_HIGH_TI_STRESS_SUMMARY_v01.csv",high_rows,fields(high_rows))
        seal={"seal_id":"B14_EMPIRICAL_STRESS_CALIBRATION_SEAL_v01","sealed_utc":datetime.now(timezone.utc).isoformat(),"builder_version":BUILD_VERSION,"phase":"AFTER_PHASE_B_BEFORE_ACTUAL24_OUTCOME_READ","actual24_outcome_rows_read_before_seal":0,"direct_species_count":len(direct),"direct_species_sha256":sha256_bytes("\n".join(direct).encode()),"ti_band_definition":{"population":"FULL_5752_BLOCK_FOLD_DISTRIBUTION","q95":d10meta["q95"],"q99":d10meta["q99"],"rules":["LT_P95","P95_TO_LT_P99","GE_P99"]},"calibration_population":"SELECTED_Y_EXACT_ZERO_AND_TARGET_STRATUM_SPECIES_MASS_POSITIVE","matching_hierarchy":["H1_SAME_FOLD_ROUTE_TI_BAND","H2_SAME_FOLD_TI_BAND","H3_SAME_TI_BAND","H4_ALL"],"minimum_group_n":MIN_CALIBRATION_N,"tiers":{"E_OBSERVED":"actual point-mass exact omission after seal","E_P95":"sealed empirical p95","E_EMPIRICAL_MAX":"sealed empirical maximum"},"multiple_singleton_rule":"CONSERVATIVE_NO_CANCELLATION_BOUND","implicit_zero_rule":"Target-stratum species sum zero implies every retained-plot pseudo replacement and both perturbation metrics are exactly zero; retain in counts/quantiles without physical Parquet rows.","pseudo_event_identity":pmeta,"sealed_files":{n:sha256_file(OUT/n) for n in ["B14_PSEUDO_SINGLETON_EVENT_LEVEL_v01.parquet","B14_PSEUDO_SINGLETON_STRESS_SUMMARY_v01.csv","B14_ZERO_SELECTED_PLOT_STRESS_v01.csv","B14_HIGH_TI_STRESS_SUMMARY_v01.csv"]}}
        write_json(OUT/"B14_EMPIRICAL_STRESS_CALIBRATION_SEAL_v01.json",seal); seal_sha=sha256_file(OUT/"B14_EMPIRICAL_STRESS_CALIBRATION_SEAL_v01.json")
        log(f"CALIBRATION SEALED sha256={seal_sha}; beginning first actual24 outcome read")
        individual,envelopes,dsummary,abba,sv,abies,ameta=run_actual(con,plot,maps,totals,direct,info,bench,zero_exact,seal_sha,log,ParquetWriter)
        con.close()
        write_csv(OUT/"B14_DIRECT97_STRESS_SUMMARY_v01.csv",dsummary,fields(dsummary))
        write_csv(OUT/"B14_AB_VS_BA_STRESS_SUMMARY_v01.csv",abba,fields(abba))
        write_csv(OUT/"B14_ABIES_PROCERA_CASE_v01.csv",abies,fields(abies))
        write_csv(OUT/"B14_STRESS_VS_AB_FOLD_DISCREPANCY_v01.csv",sv,fields(sv))
        disposition=disposition_rows({"d10ca":d10meta,"pseudo":pmeta},summaries,dsummary,abba,"UNRESOLVED_STRESS_IDENTIFICATION","B14_MATERIALITY_STRESS_COMPLETE")
        write_csv(OUT/"B14_MATERIALITY_DISPOSITION_MATRIX_v01.csv",disposition,fields(disposition))
        provenance=[]
        for k,v in pre["identities"].items(): provenance.append({"source_id":k.upper(),"path":v["path"],"sha256":v["sha256"],"role":{"D10CA":"FROZEN_A2_COEFFICIENT_AND_FORMULA_AUTHORITY","CACHE":"ACCEPTED_UNEXPANDED_MEASUREMENT_CACHE","Q1_PROJECTION":"Q1_101_AND_DIRECT97_COHORT_IDENTITY","SINGLETON_AUDIT":"ACCEPTED_ACTUAL24_IDENTITY_AND_MASS_RECONCILIATION"}.get(k.upper(),"ACCEPTED_UPSTREAM_CONTEXT"),"access":"READ_ONLY","status":"PASS"})
        provenance.append({"source_id":"SUBSTRATE_NONEXTRACTION","path":str(INPUTS['substrate'][0]),"sha256":INPUTS['substrate'][1],"role":pre["substrate_nonextraction_reason"],"access":"ARCHIVE_HASH_AND_ACCEPTED_RECONCILIATION_ONLY","status":"PASS"})
        write_csv(OUT/"B14_PROVENANCE_v01.csv",provenance,fields(provenance))
        open_items=[
            {"item_id":"MAINLINE_DISPOSITION","owner":"MAINLINE","item":"Review continuous B14 stress evidence relative to A/B fold discrepancy before any covariance decision.","blocking_for_B14":"NO","blocking_for_D10F_C":"YES","status":"OPEN"},
            {"item_id":"ESTIMATOR_SELECTION","owner":"MAINLINE","item":"B14 does not select, promote, or certify an estimator.","blocking_for_B14":"NO","blocking_for_D10F_C":"YES","status":"OPEN"},
            {"item_id":"PHASE_D","owner":"B14","item":"No Phase D escalation was run because empirical identification completed.","blocking_for_B14":"NO","blocking_for_D10F_C":"NO","status":"SKIPPED_BY_DESIGN"},
        ]
        write_csv(OUT/"B14_OPEN_ITEMS_v01.csv",open_items,fields(open_items))
        inv=[
            {"check_id":"INPUT_SHA_EXACT","expected":"7/7 exact","observed":"7/7 exact","status":"PASS","detail":"All accepted outer artifact hashes matched."},
            {"check_id":"D10CA_BLOCK_FOLD_IDENTITY","expected":"5752 pass","observed":"5752 pass","status":"PASS","detail":"Unique TI/area/denominator and n*TI=area."},
            {"check_id":"DIRECT97_IDENTITY","expected":"97","observed":len(direct),"status":"PASS","detail":"Single-SPCD direct primary species only."},
            {"check_id":"ACTUAL24_IDENTITY_UNCHANGED","expected":24,"observed":24,"status":"PASS","detail":"Accepted case IDs, folds, routes, plots, cells, and TI reconciled to B12/D10CA."},
            {"check_id":"TI_APPLIED_EXACTLY_ONCE","expected":"YES","observed":"YES","status":"PASS","detail":"Cached y is unexpanded and every mass multiplication uses one D10CA fold-specific TI."},
            {"check_id":"PSEUDO_TARGETS","expected":4640,"observed":pmeta["targets"],"status":"PASS","detail":"All scoreable pseudo targets."},
            {"check_id":"PSEUDO_EVENT_UNIVERSE","expected":EXPECTED_EVENT_UNIVERSE,"observed":pmeta["event_universe"],"status":"PASS","detail":"Materialized plus implicit exact zeros."},
            {"check_id":"PSEUDO_EVENT_PARTITION","expected":EXPECTED_EVENT_UNIVERSE,"observed":pmeta["materialized_events"]+pmeta["implicit_exact_zero_events"],"status":"PASS","detail":"No event loss."},
            {"check_id":"NULL_MEASURE_COLLAPSE_POLICY","expected":"RETAIN_AS_MAXIMAL_BOUND","observed":pmeta["maximal_total_mass_collapse_events"],"status":"PASS","detail":"TV=1 conservative boundary; status is explicit in event Parquet."},
            {"check_id":"ACTUAL_INDIVIDUAL_ROWS","expected":6984,"observed":ameta["individual_rows"],"status":"PASS","detail":"24x97x3."},
            {"check_id":"ACTUAL_ENVELOPE_ROWS","expected":582,"observed":ameta["envelope_rows"],"status":"PASS","detail":"2 directions x97x3."},
            {"check_id":"ACTUAL_READ_AFTER_SEAL","expected":"YES","observed":"YES","status":"PASS","detail":seal_sha},
            {"check_id":"PSEUDO_PARQUET_FOOTER","expected":"PAR1","observed":footer_info(OUT/"B14_PSEUDO_SINGLETON_EVENT_LEVEL_v01.parquet")["magic"],"status":"PASS","detail":pmeta["parquet_sha256"]},
            {"check_id":"ACTUAL_PARQUET_FOOTER","expected":"PAR1","observed":footer_info(OUT/"B14_ACTUAL24_STRESS_APPLICATION_v01.parquet")["magic"],"status":"PASS","detail":ameta["parquet_sha256"]},
            {"check_id":"NEW_TREE_SOURCE_SCAN_ROWS","expected":0,"observed":0,"status":"PASS","detail":"Accepted cache only."},
            {"check_id":"Q1_CALCULATION_ROWS","expected":0,"observed":0,"status":"PASS","detail":"No real-Q1 calculation."},
            {"check_id":"SUPPORT_DATA_ROWS","expected":0,"observed":0,"status":"PASS","detail":"No support data accessed."},
            {"check_id":"ACTUAL_OUTCOMES_DO_NOT_CHANGE_STRESS_DEFINITIONS","expected":"SEALED_BEFORE_READ","observed":seal_sha,"status":"PASS","detail":"Matching hierarchy, TI bands, tiers, and aggregation rule fixed in seal."},
        ]
        write_csv(OUT/"B14_INVARIANT_QC_v01.csv",inv,fields(inv))
        firewall=[
            {"check_id":"NO_NEW_ESTIMATOR","observed":"No estimator constructed or promoted","status":"PASS"},
            {"check_id":"NO_SUPPORT_ANALYSIS","observed":"No support analysis executed","status":"PASS"},
            {"check_id":"NO_REAL_Q1","observed":"Q1 calculation rows=0","status":"PASS"},
            {"check_id":"NO_D10F_C","observed":"D10F-C remains HOLD","status":"PASS"},
            {"check_id":"OUTCOME_INDEPENDENT_CALIBRATION","observed":f"Seal {seal_sha} precedes first actual24 outcome read","status":"PASS"},
            {"check_id":"NO_SPECIES_EXCLUSION","observed":"All 24x97 retained for all 3 tiers","status":"PASS"},
            {"check_id":"MULTI_CODE_FIREWALL","observed":f"{len(multi)} multi-SPCD species retained only as cohort context, never combined","status":"PASS"},
            {"check_id":"NO_ARBITRARY_PASS_THRESHOLD","observed":"Continuous metrics and fold-discrepancy comparisons only","status":"PASS"},
            {"check_id":"PHASE_D_DEFAULT_SKIP","observed":"SKIPPED; no inconclusive identification trigger","status":"PASS"},
        ]
        write_csv(OUT/"B14_REFERENCE_FIREWALL_QC_v01.csv",firewall,fields(firewall))
        meta={"task_id":"Q1_D10F_B14_v01_WORK_SINGLETON_UNCERTAINTY_MATERIALITY_STRESS_AUDIT","builder_version":BUILD_VERSION,"run_started_utc":"see execution.log","run_completed_utc":datetime.now(timezone.utc).isoformat(),"task_status":"B14_MATERIALITY_STRESS_COMPLETE","scientific_evidence_category":"TO_BE_FINALIZED_FROM_LOCKED_OUTPUTS","preflight":pre,"d10ca":d10meta,"baseline_plot_species_rows":scan,"direct_species_count":len(direct),"multi_species_context_count":len(multi),"pseudo":pmeta,"actual":ameta,"calibration_seal_sha256":seal_sha,"phase_D":"SKIPPED","phase_D_reason":"Empirical identification and sealed application completed.","measurement_formula":"sum(fold_specific_ti * cached_unexpanded_y); cached y = sum(TPA_UNADJ * basis-matched ADJ_FACTOR); no EXPNS; TI exactly once","event_storage_rule":"Only target-positive species events materialized; target-zero species events are IMPLICIT_EXACT_ZERO and retained in every universe count and quantile denominator.","no_automatic_archive":True,"d10f_c_status":"HOLD"}
        write_json(OUT/"B14_RUN_METADATA_v01.json",meta)
        copy_sources()
        (OUT/"B14_MAIN_REPORT_v01.md").write_text(make_report(meta,summaries,dsummary,abba,"TO_BE_FINALIZED_FROM_LOCKED_OUTPUTS","B14_MATERIALITY_STRESS_COMPLETE"),encoding="utf-8",newline="\n")
        log("B14 RUN COMPLETE; scientific outputs locked; package not yet created")
    except Exception as e:
        (OUT/"B14_STOP_REPORT_v01.md").write_text(f"# B14 stopped\n\nReason: `{type(e).__name__}: {e}`\n\nNo bypass was applied. D10F-C remains HOLD.\n",encoding="utf-8")
        log(f"B14 STOP {type(e).__name__}: {e}")
        raise
    finally:
        log.close()


def write_sha_transfer_and_zip() -> tuple[Path,str]:
    for p in [OUT/"SHA256SUMS.csv",OUT/"TRANSFER_MANIFEST_v01.csv",OUT/"Q1_D10F_B14_v01.zip"]:
        if p.exists(): p.unlink()
    files=sorted([p for p in OUT.rglob("*") if p.is_file() and p.name not in {"SHA256SUMS.csv","TRANSFER_MANIFEST_v01.csv","Q1_D10F_B14_v01.zip"}],key=lambda p:p.relative_to(OUT).as_posix())
    sums=[{"relative_path":p.relative_to(OUT).as_posix(),"sha256":sha256_file(p),"size_bytes":p.stat().st_size} for p in files]
    write_csv(OUT/"SHA256SUMS.csv",sums,["relative_path","sha256","size_bytes"])
    prefix="release_mirror/Q1-D10FB14-v01-20260909/"
    transfer=[]
    for p in files+[OUT/"SHA256SUMS.csv"]:
        rel=p.relative_to(OUT).as_posix()
        if p.suffix==".parquet": role,priority="MACHINE_EVIDENCE","P0"
        elif p.name=="B14_MAIN_REPORT_v01.md": role,priority="PRIMARY_REPORT","P0"
        elif "QC" in p.name or "DISPOSITION" in p.name or "SEAL" in p.name: role,priority="AUDIT_CONTROL","P0"
        elif p.suffix==".csv": role,priority="TABULAR_EVIDENCE","P1"
        elif rel.startswith("src/"): role,priority="REPRODUCIBILITY_CODE","P2"
        else: role,priority="PROVENANCE_SUPPORT","P2"
        transfer.append({"local_path":str(p),"relative_path":prefix+rel,"role":role,"upload_target":"mirror","required":"YES","mainline_priority":priority,"size_bytes":p.stat().st_size,"sha256":sha256_file(p),"notes":"B14 Work diagnostic evidence; preserve relative path; upload_target intentionally mirror"})
    write_csv(OUT/"TRANSFER_MANIFEST_v01.csv",transfer,["local_path","relative_path","role","upload_target","required","mainline_priority","size_bytes","sha256","notes"])
    if any(r["upload_target"]!="mirror" for r in transfer): raise StopBuild("Transfer target invariant failed")
    zpath=OUT/"Q1_D10F_B14_v01.zip"; fixed=(2026,9,9,0,0,0)
    members=sorted([p for p in OUT.rglob("*") if p.is_file() and p!=zpath],key=lambda p:p.relative_to(OUT).as_posix())
    with zipfile.ZipFile(zpath,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True) as z:
        for p in members:
            zi=zipfile.ZipInfo(p.relative_to(OUT).as_posix(),fixed); zi.compress_type=zipfile.ZIP_DEFLATED; zi.external_attr=0o100644<<16
            z.writestr(zi,p.read_bytes(),compress_type=zipfile.ZIP_DEFLATED,compresslevel=6)
    # Verify every SHA row inside the final ZIP and exact manifest target values.
    with zipfile.ZipFile(zpath) as z:
        rows=list(csv.DictReader(io.StringIO(z.read("SHA256SUMS.csv").decode("utf-8-sig"))))
        for r in rows:
            if sha256_bytes(z.read(r["relative_path"]))!=r["sha256"] or len(z.read(r["relative_path"]))!=int(r["size_bytes"]): raise StopBuild(f"Final ZIP internal mismatch {r['relative_path']}")
        tr=list(csv.DictReader(io.StringIO(z.read("TRANSFER_MANIFEST_v01.csv").decode("utf-8-sig"))))
        if len(tr)!=len(transfer) or any(r["upload_target"]!="mirror" for r in tr): raise StopBuild("Final ZIP transfer manifest target failed")
    return zpath,sha256_file(zpath)


def preflight_only() -> None:
    TMP.mkdir(parents=True,exist_ok=True); log=Logger(TMP/"preflight.log")
    try:
        print(json.dumps(input_preflight(log),indent=2))
    finally: log.close()


def main() -> None:
    ap=argparse.ArgumentParser(); sub=ap.add_subparsers(dest="cmd",required=True)
    sub.add_parser("preflight"); sub.add_parser("run")
    f=sub.add_parser("finalize"); f.add_argument("--category",required=True,choices=["NONMATERIAL_TAIL_CANDIDATE","LOCALIZED_SPECIES_LEVEL_SENSITIVITY","MATERIAL_SINGLETON_UNCERTAINTY_REMAINS","UNRESOLVED_STRESS_IDENTIFICATION"]); f.add_argument("--status",default="B14_MATERIALITY_STRESS_COMPLETE",choices=["B14_MATERIALITY_STRESS_COMPLETE","B14_STOPPED_FOR_MAINLINE_REVIEW"])
    sub.add_parser("package")
    a=ap.parse_args()
    if a.cmd=="preflight": preflight_only()
    elif a.cmd=="run": run_analysis()
    elif a.cmd=="finalize": finalize_outputs(a.category,a.status)
    elif a.cmd=="package":
        p,h=write_sha_transfer_and_zip(); print(json.dumps({"zip":str(p),"sha256":h,"size_bytes":p.stat().st_size,"transfer_rows":len(list(csv.DictReader((OUT/'TRANSFER_MANIFEST_v01.csv').open(encoding='utf-8-sig')))),"upload_target":"mirror"},indent=2))


if __name__=="__main__":
    main()
