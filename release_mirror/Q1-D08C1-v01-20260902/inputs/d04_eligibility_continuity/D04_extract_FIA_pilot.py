#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
D04 FIA five-state pilot extractor and sampling census
======================================================

Purpose
-------
Prepare a SMALL, traceable FIA raw-observation pilot pack for:
PA, WV, VA, NC, TN, common nominal evaluation year 2023.

This script:
- DOES NOT run R1/R2a/R2b.
- DOES NOT test range-abundance coupling.
- DOES NOT treat grid-cell zero detections as true absence.
- DOES NOT use TreeMap or any environmental interpolation.
- DOES NOT choose a final grain or final species set.

It:
1) selects the official 2023 evaluation through
   POP_STRATUM.EVALID -> POP_PLOT_STRATUM_ASSGN.PLT_CN -> PLOT.CN;
2) retains public coordinates and measurement timing;
3) retains accessible forest conditions;
4) retains the D04 primary large-tree state:
   live TREE records with FIA DIA >= 5.0 in on accessible forest conditions.
   DIA is DBH for ordinary species and computed DRC for woodland species in FIADB;
5) constructs engineering-only 25/50/75-km grid sampling censuses;
6) creates a deterministic 50:50 plot split for FEASIBILITY diagnostics only;
7) chooses 10+10+10 test-species candidates by observed detection frequency only;
8) writes a small ZIP pack plus provenance and checksums.

Dependencies: Python 3 standard library only.
"""

from __future__ import annotations

import csv
import hashlib
import io
import math
import os
import shutil
import statistics
import sys
import time
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

# ------------------------------ CONFIG ---------------------------------

STATE_INFO = {
    "PA": {"statecd": "42", "evalid": "422301", "eval_group": "422023"},
    "WV": {"statecd": "54", "evalid": "542301", "eval_group": "542023"},
    "VA": {"statecd": "51", "evalid": "512301", "eval_group": "512023"},
    "NC": {"statecd": "37", "evalid": "372301", "eval_group": "372023"},
    "TN": {"statecd": "47", "evalid": "472301", "eval_group": "472023"},
}

GRAINS_KM = (25, 50, 75)
SPLIT_SEED = "D04_FIA_GEOMETRY_RECOVERABILITY_V1"
MIN_RARE_POOL_PLOT_DETECTIONS = 30

DEFAULT_ROOT = Path.home() / "Downloads" / "D04_FIA_raw_2023"
DEFAULT_OUT = Path.home() / "Downloads" / "D04_FIA_pilot_2023"

# Exact raw tables already downloaded/verified.
REQUIRED_TABLES = (
    "PLOT",
    "PLOTGEOM",
    "COND",
    "TREE",
    "POP_PLOT_STRATUM_ASSGN",
    "POP_STRATUM",
    "POP_ESTN_UNIT",
    "POP_EVAL",
    "POP_EVAL_GRP",
    "POP_EVAL_TYP",
    "SURVEY",
)

# Fields intentionally retained if present. Missing fields are recorded as UNKNOWN.
PLOT_FIELDS = [
    "CN", "SRV_CN", "CTY_CN", "PREV_PLT_CN",
    "INVYR", "STATECD", "UNITCD", "COUNTYCD", "PLOT",
    "PLOT_STATUS_CD", "PLOT_NONSAMPLE_REASN_CD",
    "MEASYEAR", "MEASMON", "MEASDAY", "REMPER",
    "KINDCD", "DESIGNCD", "LAT", "LON",
    "ELEV", "P2PANEL", "P3PANEL", "MANUAL",
    "CYCLE", "SUBCYCLE",
]

COND_FIELDS = [
    "CN", "PLT_CN", "CONDID",
    "COND_STATUS_CD", "COND_NONSAMPLE_REASN_CD",
    "CONDPROP_UNADJ", "SUBPPROP_UNADJ", "MICRPROP_UNADJ",
    "MACRPROP_UNADJ", "PROP_BASIS",
    "OWNCD", "OWNGRPCD", "RESERVCD",
    "FORTYPCD", "FLDTYPCD", "STDAGE", "STDORGCD",
    "NF_COND_STATUS_CD",
]

TREE_FIELDS = [
    "CN", "PLT_CN", "PREV_TRE_CN", "CONDID",
    "SUBP", "TREE", "SPCD", "SPGRPCD",
    "STATUSCD", "DIA", "DIAHTCD", "HTDMP",
    "HT", "ACTUALHT", "TREECLCD",
    "TPA_UNADJ", "TPAMORT_UNADJ", "TPAREMV_UNADJ",
    "AGENTCD", "MORTYR",
]

POP_STRATUM_FIELDS = [
    "CN", "ESTN_UNIT_CN", "EVALID", "RSCD",
    "EXPNS", "ADJ_FACTOR_SUBP", "ADJ_FACTOR_MICR", "ADJ_FACTOR_MACR",
    "P1POINTCNT", "P2POINTCNT",
]

POP_ASSIGN_FIELDS = ["CN", "PLT_CN", "STRATUM_CN"]

POP_ESTN_UNIT_FIELDS = [
    "CN", "EVAL_CN", "ESTN_UNIT", "ESTN_UNIT_DESCR",
    "AREA_USED", "P1PNTCNT_EU",
]

# --------------------------- BASIC HELPERS -------------------------------

def norm(s):
    return "" if s is None else str(s).strip()

def norm_int_string(s):
    s = norm(s)
    if not s:
        return ""
    try:
        return str(int(float(s)))
    except Exception:
        return s

def to_float(s):
    s = norm(s)
    if not s:
        return None
    try:
        return float(s)
    except Exception:
        return None

def to_int(s):
    s = norm(s)
    if not s:
        return None
    try:
        return int(float(s))
    except Exception:
        return None

def sha256_file(path: Path, chunk=1024*1024):
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()

def quantile(vals, q):
    vals = sorted(vals)
    if not vals:
        return None
    if len(vals) == 1:
        return float(vals[0])
    pos = (len(vals) - 1) * q
    lo = math.floor(pos)
    hi = math.ceil(pos)
    if lo == hi:
        return float(vals[lo])
    return vals[lo] * (hi - pos) + vals[hi] * (pos - lo)

def stats_dict(vals):
    vals = list(vals)
    if not vals:
        return {
            "min": "", "q10": "", "q25": "", "median": "",
            "q75": "", "q90": "", "max": "", "mean": ""
        }
    return {
        "min": min(vals),
        "q10": quantile(vals, 0.10),
        "q25": quantile(vals, 0.25),
        "median": quantile(vals, 0.50),
        "q75": quantile(vals, 0.75),
        "q90": quantile(vals, 0.90),
        "max": max(vals),
        "mean": sum(vals)/len(vals),
    }

def ensure_clean_dir(path: Path):
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)

def find_zip(root: Path, state: str, table: str) -> Path:
    p = root / f"{state}_{table}.zip"
    if not p.exists():
        raise FileNotFoundError(f"Required source missing: {p}")
    return p

def zip_csv_member(zpath: Path):
    with zipfile.ZipFile(zpath, "r") as z:
        files = [x for x in z.infolist() if not x.is_dir()]
        if not files:
            raise RuntimeError(f"No files in ZIP: {zpath}")
        csvs = [x for x in files if x.filename.lower().endswith((".csv", ".txt"))]
        if csvs:
            return max(csvs, key=lambda x: x.file_size).filename
        return max(files, key=lambda x: x.file_size).filename

def iter_zip_dicts(zpath: Path):
    """Stream DictReader rows from the largest CSV/TXT member."""
    member = zip_csv_member(zpath)
    z = zipfile.ZipFile(zpath, "r")
    raw = z.open(member, "r")
    # Official files are generally ASCII/UTF-8 compatible. Replacement is logged by no exception.
    txt = io.TextIOWrapper(raw, encoding="utf-8-sig", errors="replace", newline="")
    reader = csv.DictReader(txt)
    if reader.fieldnames is None:
        txt.close(); raw.close(); z.close()
        raise RuntimeError(f"No CSV header: {zpath}!{member}")
    headers = [h.strip() if h else h for h in reader.fieldnames]
    reader.fieldnames = headers
    try:
        for row in reader:
            yield row
    finally:
        txt.close()
        z.close()

def get_zip_header(zpath: Path):
    member = zip_csv_member(zpath)
    with zipfile.ZipFile(zpath, "r") as z:
        with z.open(member, "r") as raw:
            txt = io.TextIOWrapper(raw, encoding="utf-8-sig", errors="replace", newline="")
            reader = csv.reader(txt)
            header = next(reader, [])
            return [h.strip() for h in header]

def existing_fields(headers, wanted):
    hs = set(headers)
    return [x for x in wanted if x in hs]

def write_csv(path: Path, fieldnames, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fieldnames})

def append_csv_rows(path: Path, fieldnames, rows, write_header=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = "w" if write_header else "a"
    with path.open(mode, encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        if write_header:
            w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fieldnames})

# ------------------------- EPSG:5070 FORWARD ----------------------------
# NAD83 / Conus Albers, ellipsoidal Albers Equal Area.
# Implemented here to avoid external Python dependencies.

A = 6378137.0
INV_F = 298.257222101
F = 1.0 / INV_F
B = A * (1.0 - F)
E = math.sqrt(1.0 - (B*B)/(A*A))

LAT1 = math.radians(29.5)
LAT2 = math.radians(45.5)
LAT0 = math.radians(23.0)
LON0 = math.radians(-96.0)

def _m(phi):
    s = math.sin(phi)
    return math.cos(phi) / math.sqrt(1.0 - E*E*s*s)

def _q(phi):
    s = math.sin(phi)
    es = E*s
    return (1.0 - E*E) * (
        s/(1.0 - es*es) - (1.0/(2.0*E))*math.log((1.0-es)/(1.0+es))
    )

M1, M2 = _m(LAT1), _m(LAT2)
Q1, Q2, Q0 = _q(LAT1), _q(LAT2), _q(LAT0)
N_ALB = (M1*M1 - M2*M2) / (Q2 - Q1)
C_ALB = M1*M1 + N_ALB*Q1
RHO0 = A * math.sqrt(C_ALB - N_ALB*Q0) / N_ALB

def albers5070(lon_deg, lat_deg):
    phi = math.radians(lat_deg)
    lam = math.radians(lon_deg)
    q = _q(phi)
    under = C_ALB - N_ALB*q
    if under < 0:
        raise ValueError("Point outside valid Albers domain")
    rho = A * math.sqrt(under) / N_ALB
    theta = N_ALB * (lam - LON0)
    x = rho * math.sin(theta)
    y = RHO0 - rho * math.cos(theta)
    return x, y

def cell_id(x, y, grain_km):
    g = grain_km * 1000.0
    ix = math.floor(x / g)
    iy = math.floor(y / g)
    return f"{grain_km}km_{ix}_{iy}"

# ------------------------- SPECIES REFERENCE ----------------------------

def load_ref_species(path: Path):
    if not path.exists():
        return {}, []
    with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as f:
        rdr = csv.DictReader(f)
        headers = [h.strip() for h in (rdr.fieldnames or [])]
        rdr.fieldnames = headers
        mapping = {}
        rows = []
        for r in rdr:
            spcd = norm_int_string(r.get("SPCD"))
            if not spcd:
                continue
            sci = ""
            for c in ("SCIENTIFIC_NAME", "SCIENTIFIC_NAME_WO_AUTHOR",
                      "SCIENTIFIC_NAME_WITHOUT_AUTHOR", "SNAME"):
                if c in r and norm(r.get(c)):
                    sci = norm(r.get(c)); break
            if not sci:
                genus = norm(r.get("GENUS"))
                species = norm(r.get("SPECIES"))
                sci = " ".join(x for x in (genus, species) if x)
            common = ""
            for c in ("COMMON_NAME", "COMMONNAME", "CNAME"):
                if c in r and norm(r.get(c)):
                    common = norm(r.get(c)); break
            mapping[spcd] = {"scientific_name": sci, "common_name": common}
            rows.append(r)
        return mapping, headers

# ------------------------- MAIN EXTRACTION ------------------------------

def main(root=DEFAULT_ROOT, outdir=DEFAULT_OUT):
    start = time.time()
    print("===== D04 FIA PILOT EXTRACTOR =====")
    print("Source:", root)
    print("Output:", outdir)

    if not root.exists():
        raise SystemExit(f"Source directory not found: {root}")

    # Ensure all expected raw source files exist.
    for st in STATE_INFO:
        for table in REQUIRED_TABLES:
            find_zip(root, st, table)
    if not (root / "REF_SPECIES.csv").exists():
        raise SystemExit(f"Missing {root/'REF_SPECIES.csv'}")

    ensure_clean_dir(outdir)
    schema_rows = []

    # Audit headers first.
    headers_by = {}
    for st in STATE_INFO:
        for table in REQUIRED_TABLES:
            zp = find_zip(root, st, table)
            headers = get_zip_header(zp)
            headers_by[(st, table)] = headers
            schema_rows.append({
                "state": st,
                "table": table,
                "zip_file": zp.name,
                "zip_member": zip_csv_member(zp),
                "column_count": len(headers),
                "columns": "|".join(headers),
            })

    write_csv(
        outdir/"schema_audit.csv",
        ["state","table","zip_file","zip_member","column_count","columns"],
        schema_rows
    )

    species_ref, ref_headers = load_ref_species(root/"REF_SPECIES.csv")

    selected_strata = {}
    strata_rows_all = []
    unit_cn_by_state = defaultdict(set)

    # 1) Select 2023 strata by exact EVALID.
    for st, info in STATE_INFO.items():
        target = info["evalid"]
        zp = find_zip(root, st, "POP_STRATUM")
        found = 0
        for r in iter_zip_dicts(zp):
            if norm_int_string(r.get("EVALID")) == target:
                found += 1
                cn = norm(r.get("CN"))
                if cn:
                    selected_strata[(st, cn)] = r
                unit = norm(r.get("ESTN_UNIT_CN"))
                if unit:
                    unit_cn_by_state[st].add(unit)
                rr = {"source_state": st, "target_evalid": target}
                for k in POP_STRATUM_FIELDS:
                    rr[k] = r.get(k, "")
                strata_rows_all.append(rr)
        if found == 0:
            raise RuntimeError(
                f"{st}: target EVALID {target} not found in POP_STRATUM. "
                f"STOP rather than silently substitute another evaluation."
            )
        print(f"{st}: selected {found:,} POP_STRATUM rows for EVALID {target}")

    write_csv(
        outdir/"pilot_pop_stratum.csv",
        ["source_state","target_evalid"] + POP_STRATUM_FIELDS,
        strata_rows_all
    )

    # 2) Use selected strata to obtain plot measurement CNs.
    plots_by_state = defaultdict(set)
    assign_rows = []
    for st in STATE_INFO:
        stratum_cns = {cn for (sst, cn) in selected_strata if sst == st}
        zp = find_zip(root, st, "POP_PLOT_STRATUM_ASSGN")
        for r in iter_zip_dicts(zp):
            scn = norm(r.get("STRATUM_CN"))
            if scn in stratum_cns:
                pcn = norm(r.get("PLT_CN"))
                if pcn:
                    plots_by_state[st].add(pcn)
                rr = {"source_state": st, "target_evalid": STATE_INFO[st]["evalid"]}
                for k in POP_ASSIGN_FIELDS:
                    rr[k] = r.get(k, "")
                assign_rows.append(rr)
        if not plots_by_state[st]:
            raise RuntimeError(f"{st}: zero plots mapped to target evaluation.")
        print(f"{st}: {len(plots_by_state[st]):,} unique plot measurements in 2023 evaluation")

    write_csv(
        outdir/"pilot_pop_plot_stratum_assgn.csv",
        ["source_state","target_evalid"] + POP_ASSIGN_FIELDS,
        assign_rows
    )

    # 3) Selected estimation-unit rows.
    estn_rows = []
    for st in STATE_INFO:
        zp = find_zip(root, st, "POP_ESTN_UNIT")
        units = unit_cn_by_state[st]
        for r in iter_zip_dicts(zp):
            if norm(r.get("CN")) in units:
                rr = {"source_state": st, "target_evalid": STATE_INFO[st]["evalid"]}
                for k in POP_ESTN_UNIT_FIELDS:
                    rr[k] = r.get(k, "")
                estn_rows.append(rr)
    write_csv(
        outdir/"pilot_pop_estn_unit.csv",
        ["source_state","target_evalid"] + POP_ESTN_UNIT_FIELDS,
        estn_rows
    )

    # 4) Copy small evaluation/survey metadata in full by state, not heuristically filtered.
    # This is deliberate: these tables are small and preserves provenance if schema differs.
    for table in ("POP_EVAL", "POP_EVAL_GRP", "POP_EVAL_TYP", "SURVEY"):
        out = outdir / f"source_{table}.csv"
        union = []
        seen = set()
        for st in STATE_INFO:
            for h in headers_by[(st, table)]:
                if h not in seen:
                    seen.add(h); union.append(h)
        fields = ["source_state"] + union
        first = True
        for st in STATE_INFO:
            rows = []
            for r in iter_zip_dicts(find_zip(root, st, table)):
                rr = {"source_state": st}
                rr.update(r)
                rows.append(rr)
            append_csv_rows(out, fields, rows, write_header=first)
            first = False

    # 5) Filter PLOT rows in official target evaluation membership.
    plot_rows = {}
    measurement_year_counts = Counter()

    for st in STATE_INFO:
        zp = find_zip(root, st, "PLOT")
        target_plots = plots_by_state[st]
        header = headers_by[(st, "PLOT")]
        keep = existing_fields(header, PLOT_FIELDS)
        for r in iter_zip_dicts(zp):
            cn = norm(r.get("CN"))
            if cn not in target_plots:
                continue
            rr = {"source_state": st, "target_evalid": STATE_INFO[st]["evalid"]}
            for k in keep:
                rr[k] = r.get(k, "")
            # Coordinate projection if valid.
            lat = to_float(r.get("LAT"))
            lon = to_float(r.get("LON"))
            if lat is not None and lon is not None and -180 <= lon <= 180 and -90 <= lat <= 90:
                try:
                    x, y = albers5070(lon, lat)
                    rr["albers5070_x_m"] = f"{x:.3f}"
                    rr["albers5070_y_m"] = f"{y:.3f}"
                    for g in GRAINS_KM:
                        rr[f"cell_{g}km"] = cell_id(x, y, g)
                except Exception:
                    for g in GRAINS_KM:
                        rr[f"cell_{g}km"] = ""
            else:
                rr["albers5070_x_m"] = ""
                rr["albers5070_y_m"] = ""
                for g in GRAINS_KM:
                    rr[f"cell_{g}km"] = ""
            plot_rows[cn] = rr
            yr = norm_int_string(r.get("MEASYEAR"))
            if yr:
                measurement_year_counts[(st, yr)] += 1

    # Warn if assignment referenced plots missing in PLOT.
    for st in STATE_INFO:
        selected = plots_by_state[st]
        found = {cn for cn, r in plot_rows.items() if r["source_state"] == st}
        missing = selected - found
        if missing:
            raise RuntimeError(f"{st}: {len(missing)} evaluation plot CNs absent from PLOT.")

    # 6) Extract PLOTGEOM rows for selected plot CNs, for provenance.
    pg_out = outdir/"pilot_plotgeom.csv"
    union_pg = []
    seen_pg = set()
    for st in STATE_INFO:
        for h in headers_by[(st, "PLOTGEOM")]:
            if h not in seen_pg:
                seen_pg.add(h); union_pg.append(h)
    first = True
    for st in STATE_INFO:
        target = plots_by_state[st]
        rows = []
        for r in iter_zip_dicts(find_zip(root, st, "PLOTGEOM")):
            cn = norm(r.get("CN"))
            if cn in target:
                rr = {"source_state": st}
                rr.update(r)
                rows.append(rr)
        append_csv_rows(pg_out, ["source_state"]+union_pg, rows, write_header=first)
        first = False

    # 7) Extract all conditions for selected evaluation plots, and mark accessible forest conditions.
    cond_rows = []
    forest_cond_keys = set()
    forest_plots = set()

    for st in STATE_INFO:
        zp = find_zip(root, st, "COND")
        header = headers_by[(st, "COND")]
        keep = existing_fields(header, COND_FIELDS)
        target = plots_by_state[st]
        for r in iter_zip_dicts(zp):
            pcn = norm(r.get("PLT_CN"))
            if pcn not in target:
                continue
            rr = {"source_state": st, "target_evalid": STATE_INFO[st]["evalid"]}
            for k in keep:
                rr[k] = r.get(k, "")
            status = norm_int_string(r.get("COND_STATUS_CD"))
            prop = to_float(r.get("CONDPROP_UNADJ"))
            is_forest = (status == "1" and prop is not None and prop > 0)
            rr["eligible_accessible_forest_condition"] = "1" if is_forest else "0"
            if is_forest:
                condid = norm_int_string(r.get("CONDID"))
                forest_cond_keys.add((pcn, condid))
                forest_plots.add(pcn)
            cond_rows.append(rr)

    cond_fields_union = ["source_state","target_evalid"]
    for x in COND_FIELDS + ["eligible_accessible_forest_condition"]:
        if x not in cond_fields_union:
            cond_fields_union.append(x)
    write_csv(outdir/"pilot_plot_condition.csv", cond_fields_union, cond_rows)

    # Plot eligibility: sampled forest plot status + at least one accessible forest condition.
    eligible_plots = set()
    for pcn, r in plot_rows.items():
        if norm_int_string(r.get("PLOT_STATUS_CD")) == "1" and pcn in forest_plots:
            eligible_plots.add(pcn)

    # 8) Deterministic near-50:50 split, balanced within state x panel where possible.
    groups = defaultdict(list)
    for pcn in eligible_plots:
        r = plot_rows[pcn]
        key = (r["source_state"], norm_int_string(r.get("P2PANEL")) or "NA")
        digest = hashlib.sha256((SPLIT_SEED + "|" + pcn).encode("utf-8")).hexdigest()
        groups[key].append((digest, pcn))
    fold_by_plot = {}
    for key, vals in groups.items():
        vals.sort()
        for j, (_, pcn) in enumerate(vals):
            fold_by_plot[pcn] = "A" if j % 2 == 0 else "B"

    for pcn, r in plot_rows.items():
        r["eligible_forest_plot"] = "1" if pcn in eligible_plots else "0"
        r["split_fold"] = fold_by_plot.get(pcn, "")

    plot_fields = ["source_state","target_evalid"] + [
        x for x in PLOT_FIELDS if any(x in r for r in plot_rows.values())
    ] + ["eligible_forest_plot","split_fold","albers5070_x_m","albers5070_y_m"] + [
        f"cell_{g}km" for g in GRAINS_KM
    ]
    write_csv(outdir/"pilot_plot.csv", plot_fields, plot_rows.values())

    # 9) Extract primary D04 large-tree state and build species detection sets.
    tree_out = outdir/"pilot_tree_large.csv"
    tree_fields_union = ["source_state","target_evalid"] + TREE_FIELDS
    tree_writer_file = tree_out.open("w", encoding="utf-8-sig", newline="")
    tree_writer = csv.DictWriter(tree_writer_file, fieldnames=tree_fields_union, extrasaction="ignore")
    tree_writer.writeheader()

    species_plots = defaultdict(set)
    species_tree_records = Counter()
    n_large = 0
    n_tree_scanned = 0

    try:
        for st in STATE_INFO:
            zp = find_zip(root, st, "TREE")
            target = eligible_plots & plots_by_state[st]
            header = headers_by[(st, "TREE")]
            keep = existing_fields(header, TREE_FIELDS)
            for r in iter_zip_dicts(zp):
                n_tree_scanned += 1
                pcn = norm(r.get("PLT_CN"))
                if pcn not in target:
                    continue
                # Accessible forest condition only.
                condid = norm_int_string(r.get("CONDID"))
                if (pcn, condid) not in forest_cond_keys:
                    continue
                # Primary pilot state: live + FIA diameter >=5 in.
                if norm_int_string(r.get("STATUSCD")) != "1":
                    continue
                dia = to_float(r.get("DIA"))
                if dia is None or dia < 5.0:
                    continue

                rr = {"source_state": st, "target_evalid": STATE_INFO[st]["evalid"]}
                for k in keep:
                    rr[k] = r.get(k, "")
                tree_writer.writerow({k: rr.get(k, "") for k in tree_fields_union})
                n_large += 1

                spcd = norm_int_string(r.get("SPCD"))
                if spcd:
                    species_plots[spcd].add(pcn)
                    species_tree_records[spcd] += 1
    finally:
        tree_writer_file.close()

    print(f"Large-tree records written: {n_large:,}")
    print(f"Species with >=1 large-tree detection: {len(species_plots):,}")

    # 10) Evaluation/measurement-year summaries.
    eval_rows = []
    year_rows = []
    for st, info in STATE_INFO.items():
        prs = [r for r in plot_rows.values() if r["source_state"] == st]
        ers = [r for p, r in plot_rows.items() if r["source_state"] == st and p in eligible_plots]
        years = [to_int(r.get("MEASYEAR")) for r in prs]
        years = [y for y in years if y is not None]
        eval_rows.append({
            "state": st,
            "target_evalid": info["evalid"],
            "eval_group_code": info["eval_group"],
            "selected_plot_measurements": len(prs),
            "eligible_forest_plots": len(ers),
            "min_measyear": min(years) if years else "",
            "max_measyear": max(years) if years else "",
            "distinct_measyears": len(set(years)),
        })
        for (sst, yr), n in sorted(measurement_year_counts.items()):
            if sst == st:
                year_rows.append({
                    "state": st, "target_evalid": info["evalid"],
                    "MEASYEAR": yr, "plot_count": n
                })

    write_csv(outdir/"evaluation_summary.csv", [
        "state","target_evalid","eval_group_code",
        "selected_plot_measurements","eligible_forest_plots",
        "min_measyear","max_measyear","distinct_measyears"
    ], eval_rows)
    write_csv(outdir/"measurement_year_counts.csv",
              ["state","target_evalid","MEASYEAR","plot_count"], year_rows)

    # 11) Grain-level sampling census.
    grain_rows = []
    eligible_cells_by_g = {}
    cell_eligible_plots = {}
    cell_all_eval_plots = {}

    for g in GRAINS_KM:
        all_by_cell = defaultdict(list)
        elig_by_cell = defaultdict(list)
        for pcn, r in plot_rows.items():
            c = norm(r.get(f"cell_{g}km"))
            if not c:
                continue
            all_by_cell[c].append(pcn)
            if pcn in eligible_plots:
                elig_by_cell[c].append(pcn)

        eligible_cells_by_g[g] = set(elig_by_cell)
        cell_eligible_plots[g] = elig_by_cell
        cell_all_eval_plots[g] = all_by_cell

        counts = [len(v) for v in elig_by_cell.values()]
        a_counts = []
        b_counts = []
        for c, plist in elig_by_cell.items():
            a_counts.append(sum(fold_by_plot.get(p) == "A" for p in plist))
            b_counts.append(sum(fold_by_plot.get(p) == "B" for p in plist))

        st = stats_dict(counts)
        sa = stats_dict(a_counts)
        sb = stats_dict(b_counts)

        row = {
            "grain_km": g,
            # IMPORTANT denominator definition:
            # not geometric state-boundary cells; cells represented by >=1 target-evaluation plot.
            "cells_represented_by_any_eval_plot": len(all_by_cell),
            "cells_with_eligible_forest_plot": len(elig_by_cell),
            "eligible_plots_total": sum(counts),
        }
        for prefix, ss in (("eligible_n", st), ("foldA_n", sa), ("foldB_n", sb)):
            for k, v in ss.items():
                row[f"{prefix}_{k}"] = v
        for t in (1, 3, 5, 10):
            row[f"cells_both_folds_ge{t}_eligible_plots"] = sum(
                (sum(fold_by_plot.get(p) == "A" for p in plist) >= t and
                 sum(fold_by_plot.get(p) == "B" for p in plist) >= t)
                for plist in elig_by_cell.values()
            )
        grain_rows.append(row)

    grain_fields = list(grain_rows[0].keys())
    write_csv(outdir/"grain_sampling_summary.csv", grain_fields, grain_rows)

    # 12) Species commonness groups from observed plot detection frequency ONLY.
    sp_counts = {sp: len(ps) for sp, ps in species_plots.items()}
    if len(sp_counts) < 30:
        raise RuntimeError("Fewer than 30 species with large-tree detections; cannot construct requested 10+10+10.")

    floor = MIN_RARE_POOL_PLOT_DETECTIONS
    candidates = [sp for sp, n in sp_counts.items() if n >= floor]
    for alt in (20, 10, 5, 1):
        if len(candidates) >= 30:
            break
        floor = alt
        candidates = [sp for sp, n in sp_counts.items() if n >= floor]
    if len(candidates) < 30:
        raise RuntimeError("Still fewer than 30 candidate species after lowering detection floor.")

    sorted_desc = sorted(candidates, key=lambda sp: (-sp_counts[sp], int(sp) if sp.isdigit() else sp))
    common = sorted_desc[:10]
    rare = sorted(candidates, key=lambda sp: (sp_counts[sp], int(sp) if sp.isdigit() else sp))[:10]
    excluded = set(common) | set(rare)
    rem = [sp for sp in candidates if sp not in excluded]
    med = statistics.median([sp_counts[sp] for sp in candidates])
    intermediate = sorted(
        rem,
        key=lambda sp: (abs(sp_counts[sp] - med), -sp_counts[sp], int(sp) if sp.isdigit() else sp)
    )[:10]

    class_by_sp = {sp: "common_top10" for sp in common}
    class_by_sp.update({sp: "intermediate10" for sp in intermediate})
    class_by_sp.update({sp: "rarer10_above_engineering_floor" for sp in rare})
    selected30 = set(class_by_sp)

    # 13) Species manifest + species-grain summary.
    manifest_rows = []
    species_grain_rows = []
    test_cell_rows = []

    for sp in sorted(sp_counts, key=lambda s: (-sp_counts[s], s)):
        ref = species_ref.get(sp, {})
        row = {
            "SPCD": sp,
            "scientific_name": ref.get("scientific_name", ""),
            "common_name": ref.get("common_name", ""),
            "detected_eligible_plots": sp_counts[sp],
            "large_tree_records": species_tree_records[sp],
            "commonness_class": class_by_sp.get(sp, ""),
            "candidate_pool_detection_floor": floor if sp in candidates else "",
        }
        for g in GRAINS_KM:
            pos_cells = {
                plot_rows[p].get(f"cell_{g}km","")
                for p in species_plots[sp]
                if plot_rows[p].get(f"cell_{g}km","")
            }
            row[f"detected_cells_{g}km"] = len(pos_cells)
            row[f"eligible_cells_{g}km"] = len(eligible_cells_by_g[g])
        manifest_rows.append(row)

        for g in GRAINS_KM:
            elig_cells = eligible_cells_by_g[g]
            positive_by_cell = defaultdict(list)
            for p in species_plots[sp]:
                c = norm(plot_rows[p].get(f"cell_{g}km"))
                if c:
                    positive_by_cell[c].append(p)

            detected_cells = set(positive_by_cell)
            pos_counts_detected = [len(v) for v in positive_by_cell.values()]
            pos_stats = stats_dict(pos_counts_detected)

            a_pos = sum(fold_by_plot.get(p) == "A" for p in species_plots[sp])
            b_pos = sum(fold_by_plot.get(p) == "B" for p in species_plots[sp])
            det_a, det_b = set(), set()
            both, aonly, bonly, neither = 0, 0, 0, 0

            for c, plist in cell_eligible_plots[g].items():
                pa = sum(p in species_plots[sp] and fold_by_plot.get(p) == "A" for p in plist)
                pb = sum(p in species_plots[sp] and fold_by_plot.get(p) == "B" for p in plist)
                if pa: det_a.add(c)
                if pb: det_b.add(c)
                if pa and pb: both += 1
                elif pa: aonly += 1
                elif pb: bonly += 1
                else: neither += 1

                if sp in selected30:
                    ea = sum(fold_by_plot.get(p) == "A" for p in plist)
                    eb = sum(fold_by_plot.get(p) == "B" for p in plist)
                    test_cell_rows.append({
                        "SPCD": sp,
                        "scientific_name": ref.get("scientific_name", ""),
                        "commonness_class": class_by_sp.get(sp, ""),
                        "grain_km": g,
                        "cell_id": c,
                        "eligible_plots_total": len(plist),
                        "eligible_plots_fold_A": ea,
                        "eligible_plots_fold_B": eb,
                        "positive_plots_total": pa + pb,
                        "positive_plots_fold_A": pa,
                        "positive_plots_fold_B": pb,
                        "zero_detection_is_not_true_absence": "1" if (pa+pb)==0 else "0",
                    })

            sr = {
                "SPCD": sp,
                "scientific_name": ref.get("scientific_name", ""),
                "commonness_class": class_by_sp.get(sp, ""),
                "grain_km": g,
                "eligible_cells_in_pilot_sampling_frame": len(elig_cells),
                "detected_cells": len(detected_cells),
                "eligible_cells_zero_detection": len(elig_cells - detected_cells),
                "positive_plots_total": len(species_plots[sp]),
                "positive_plots_fold_A": a_pos,
                "positive_plots_fold_B": b_pos,
                "detected_cells_fold_A": len(det_a),
                "detected_cells_fold_B": len(det_b),
                "cells_positive_both_folds": both,
                "cells_positive_A_only": aonly,
                "cells_positive_B_only": bonly,
                "cells_zero_detection_both_folds": neither,
            }
            for k, v in pos_stats.items():
                sr[f"positive_plots_per_detected_cell_{k}"] = v
            species_grain_rows.append(sr)

    species_manifest_fields = list(manifest_rows[0].keys())
    write_csv(outdir/"species_manifest.csv", species_manifest_fields, manifest_rows)

    sg_fields = list(species_grain_rows[0].keys())
    write_csv(outdir/"species_grain_summary.csv", sg_fields, species_grain_rows)

    tc_fields = [
        "SPCD","scientific_name","commonness_class","grain_km","cell_id",
        "eligible_plots_total","eligible_plots_fold_A","eligible_plots_fold_B",
        "positive_plots_total","positive_plots_fold_A","positive_plots_fold_B",
        "zero_detection_is_not_true_absence"
    ]
    write_csv(outdir/"test30_species_cell_counts.csv", tc_fields, test_cell_rows)

    # 14) Minimal source file inventory from already-verified local raw files.
    source_inventory = []
    checksum_manifest = root/"SHA256SUMS.csv"
    hash_lookup = {}
    if checksum_manifest.exists():
        with checksum_manifest.open("r", encoding="utf-8-sig", newline="") as f:
            for r in csv.DictReader(f):
                hash_lookup[norm(r.get("File"))] = {
                    "Bytes": norm(r.get("Bytes")), "SHA256": norm(r.get("SHA256")).lower()
                }

    for st in STATE_INFO:
        for table in REQUIRED_TABLES:
            p = find_zip(root, st, table)
            h = hash_lookup.get(p.name, {})
            source_inventory.append({
                "file": p.name,
                "bytes": h.get("Bytes", p.stat().st_size),
                "sha256": h.get("SHA256", ""),
                "role": table,
            })
    p = root/"REF_SPECIES.csv"
    h = hash_lookup.get(p.name, {})
    source_inventory.append({
        "file": p.name, "bytes": h.get("Bytes", p.stat().st_size),
        "sha256": h.get("SHA256", ""), "role": "REF_SPECIES"
    })
    write_csv(outdir/"source_inventory.csv", ["file","bytes","sha256","role"], source_inventory)

    # 15) MANIFEST.
    elapsed = time.time() - start
    now = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    test_lines = []
    for cls in ("common_top10","intermediate10","rarer10_above_engineering_floor"):
        ss = [sp for sp,c in class_by_sp.items() if c == cls]
        ss = sorted(ss, key=lambda sp: -sp_counts[sp])
        test_lines.append(f"- {cls}: " + ", ".join(
            f"{sp} {species_ref.get(sp,{}).get('scientific_name','')} (plots={sp_counts[sp]})"
            for sp in ss
        ))

    manifest = f"""# D04 FIA five-state pilot pack

Generated: {now}
Source directory: `{root}`
Pilot extent: PA, WV, VA, NC, TN
Nominal common evaluation year: 2023

## Exact target EVALID values

- PA: 422301
- WV: 542301
- VA: 512301
- NC: 372301
- TN: 472301

Selection relationship:
`POP_STRATUM.EVALID -> POP_PLOT_STRATUM_ASSGN.STRATUM_CN -> PLT_CN -> PLOT.CN`

The script intentionally DOES NOT select observations with `INVYR == 2023`.
Measurement-year distributions are preserved in `evaluation_summary.csv` and
`measurement_year_counts.csv`.

## Primary abundance state

Large-tree pilot state:
- selected target-evaluation plot measurement;
- accessible forest condition (`COND_STATUS_CD == 1` and positive `CONDPROP_UNADJ`);
- live tree (`TREE.STATUSCD == 1`);
- FIA current diameter `TREE.DIA >= 5.0 in`.

FIADB DIA is DBH for ordinary/timber species and computed DRC for woodland
species; therefore woodland DRC records are not manually discarded.

This state must NOT be described as universal reproductive adults.

Basal area, 1--4.9-in saplings and seedlings are NOT primary abundance here.

## Coordinates and grids

Coordinates are the public FIA coordinates exactly as supplied in FIADB.
No attempt was made to infer confidential true locations.

For engineering-only sampling census, public WGS84/NAD83-like lon/lat
coordinates were transformed to NAD83 / CONUS Albers (EPSG:5070 formula) and
assigned to fixed 25, 50, and 75-km square grids.

`cells_represented_by_any_eval_plot` is NOT the count of all geometric cells
intersecting the five-state political boundary. It is the number of grid cells
containing at least one selected target-evaluation FIA plot location.
This distinction is deliberate and prevents inventing state-boundary geometry.

## 50:50 split

The A/B split is FEASIBILITY-ONLY, not a final cross-fitting design.
Eligible plots are deterministically balanced approximately 50:50 within
`state x P2PANEL` groups using SHA-256 and seed:
`{SPLIT_SEED}`.

No plot measurement occurs in both folds.

## Test 30 species

Selected only by observed eligible-plot detection frequency.
Engineering minimum detection floor used: {floor} plots.
No ecological story/trait/range criterion was used.

{chr(10).join(test_lines)}

## Zero detections

Every field named `zero_detection...` means only:
"the selected FIA sample did not detect this large-tree state in that cell".
It MUST NOT be interpreted as ecological absence.

## Files

- `pilot_plot.csv` — target-evaluation plot measurements + public geometry,
  timing, eligibility and feasibility split.
- `pilot_plot_condition.csv` — condition/sampling-domain metadata.
- `pilot_tree_large.csv` — live DIA>=5-in large-tree records on accessible forest conditions.
- `pilot_plotgeom.csv` — selected PLOTGEOM records for provenance.
- `pilot_pop_stratum.csv`
- `pilot_pop_plot_stratum_assgn.csv`
- `pilot_pop_estn_unit.csv`
- `source_POP_EVAL.csv`, `source_POP_EVAL_GRP.csv`,
  `source_POP_EVAL_TYP.csv`, `source_SURVEY.csv`
- `evaluation_summary.csv`
- `measurement_year_counts.csv`
- `grain_sampling_summary.csv`
- `species_manifest.csv`
- `species_grain_summary.csv`
- `test30_species_cell_counts.csv`
- `schema_audit.csv`
- `source_inventory.csv`
- `OUTPUT_SHA256SUMS.csv`

## Known/intentional limitations

1. No range-abundance analysis was run.
2. No wall-to-wall interpolation was run.
3. No cell zero is treated as true absence.
4. No final grain is selected.
5. The five-state 2023 evaluation is a nominal common evaluation, not a
   strictly synchronous ecological snapshot.
6. Public-coordinate fuzzing/swapping is not corrected here.
7. There is no plot-level FIA public flag proving which private plots were swapped.
8. The grid census denominator is evaluation-plot-represented cells, not exact
   five-state polygon-intersection cells.
9. Population-estimation metadata are retained, but formal design weights are
   NOT applied in this D04 extraction/census.
10. A/B splitting is an engineering stress-test split only.

## External documentation audited before extraction

- FIADB Database Description v9.4, August 2025.
- FIA National Core/Nationwide Field Guide, current 2025/2026 release line.
- FIADB EVALIDator current database/service, checked 2026-08-31.
- DataMart source files downloaded 2026-08-31 and independently passed local
  56-file ZIP/SHA-256 integrity audit before this extractor was run.

Runtime: {elapsed:.1f} seconds
"""
    (outdir/"MANIFEST.md").write_text(manifest, encoding="utf-8")

    # 16) Output hashes.
    hash_rows = []
    for p in sorted(outdir.iterdir()):
        if p.is_file() and p.name != "OUTPUT_SHA256SUMS.csv":
            hash_rows.append({
                "file": p.name,
                "bytes": p.stat().st_size,
                "sha256": sha256_file(p),
            })
    write_csv(outdir/"OUTPUT_SHA256SUMS.csv", ["file","bytes","sha256"], hash_rows)

    # 17) Zip final pack.
    zip_path = outdir.parent / "D04_FIA_pilot_2023_pack.zip"
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for p in sorted(outdir.iterdir()):
            if p.is_file():
                z.write(p, arcname=p.name)

    print("")
    print("===== COMPLETE =====")
    print("Pilot directory:", outdir)
    print("Pilot ZIP:", zip_path)
    print(f"ZIP size: {zip_path.stat().st_size/1024/1024:.2f} MiB")
    print("ZIP SHA256:", sha256_file(zip_path))
    print("")
    print("UPLOAD ONLY THIS SMALL FILE:")
    print(zip_path)


if __name__ == "__main__":
    root = Path(sys.argv[1]) if len(sys.argv) >= 2 else DEFAULT_ROOT
    outdir = Path(sys.argv[2]) if len(sys.argv) >= 3 else DEFAULT_OUT
    main(root, outdir)
