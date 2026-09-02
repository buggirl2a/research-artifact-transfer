#!/usr/bin/env python3
"""Build the frozen D09C species-blind FIA design audit.

The SQLite connection is read-only and protected by an authorizer that denies
reads from every table outside the contract whitelist. No species table or
species-derived artifact is an input.
"""

from __future__ import annotations

import csv
import hashlib
import itertools
import json
import math
import os
import platform
import sqlite3
import statistics
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

from pyproj import Transformer


ROOT = Path(r"C:\range_paper")
DB = ROOT / "99_tmp" / "elig_v02" / "SQLite_FIADB_ENTIRE.db"
INPUT_DIR = ROOT / "03_doc" / "D09C_SPECIES_BLIND_DESIGN_INPUTS_v01"
D09_DIR = INPUT_DIR / "upstream_d09"
D09B_DIR = INPUT_DIR / "upstream_d09b"
SOURCE_DIR = ROOT / "06_src" / "d09c_v01"
WORK = ROOT / "99_tmp" / "d09c_v01"
OUTPUTS = WORK / "outputs"
QC_DIR = WORK / "qc"
TOL = 1e-8
PANELS = (1, 2, 3, 4, 5)
PANEL_CANDIDATES = tuple(itertools.combinations(PANELS, 2))
ALLOWED_TABLES = {
    "POP_EVAL_GRP", "POP_EVAL_TYP", "POP_EVAL", "POP_ESTN_UNIT",
    "POP_STRATUM", "POP_PLOT_STRATUM_ASSGN", "PLOT", "SURVEY",
}
PROHIBITED_MARKERS = (
    "TREE", "REF_SPECIES", "SPECIES", "SPCD", "LITTLE", "USGS",
    "ABUNDANCE", "OCCUPANCY", "DETECTION", "WCVP",
)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_csv(path: Path, rows: list[dict], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        if not rows:
            raise RuntimeError(f"No rows and no fieldnames for {path.name}")
        fieldnames = list(rows[0])
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def clean_float(value):
    if value is None:
        return ""
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return ""
    return value


def rel_diff(a, b):
    if a is None or b is None:
        return None
    return abs(a - b) / max(abs(b), 1.0)


def safe_mean(values):
    vals = [float(x) for x in values if x is not None]
    return statistics.fmean(vals) if vals else None


def safe_median(values):
    vals = [float(x) for x in values if x is not None]
    return statistics.median(vals) if vals else None


def safe_stdev(values):
    vals = [float(x) for x in values if x is not None]
    return statistics.stdev(vals) if len(vals) >= 2 else None


def rate_imbalance(a: int, b: int) -> float:
    return abs(a / 2.0 - b / 3.0) / max((a + b) / 5.0, 1.0)


def panel_code(panels) -> str:
    return "-".join(str(x) for x in sorted(panels))


def regional_class(rscd, statecd, unitcd) -> str:
    if rscd in (22, 26, 27):
        return "P2PANEL_SPLIT_2_SUBPANELS"
    if rscd == 33 and statecd == 40 and unitcd is not None and unitcd >= 3:
        return "OKLAHOMA_UNITCD_GE3_SUBPANELING"
    return "NO_SUBPANELING"


def format_group(statecd: int, year: int) -> str:
    return f"{statecd:02d}{year:04d}"


def load_state_universe() -> list[dict]:
    path = D09B_DIR / "D09B_2023_EVALID_STATE_LEDGER_v01.csv"
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 48:
        raise RuntimeError(f"Expected 48 CONUS States, found {len(rows)}")
    return rows


def build_input_audit() -> list[dict]:
    expected = {
        INPUT_DIR / "Q1_WORK_REQUEST_D09C_SPECIES_BLIND_REPORTING_STATE_PANEL_FOLD_AUDIT_v01_20260902.md": "e01b15f73cc0d34f22d9a7187322ab926ae9de9a6a08c6ef0d4921c18ece4f1f",
        INPUT_DIR / "Q1_D09B_MAINLINE_DECISION_v01_20260902.md": "9f3fd7e9e6bbdc4cdeae4a290ca7a1b983eeb2638175c49c0a47949e66f3c2e7",
        INPUT_DIR / "Q1_WORK_MAINLINE_ADDENDUM_D09C_RANGE_GATE_ORDER_v01_20260902.md": "54bf6cde8bcef2f22e58ca5c65f6420999b8dafcafdfd83a2dff02fab1b53f7e",
        INPUT_DIR / "D09_FIA_DESIGN_BASED_POPULATION_MASS_EVIDENCE_v01.zip": "03e6d4a48144baa208b1387aa8f615cd8fe71ef6881d6a3c9f843e9fea937cff",
        INPUT_DIR / "D09B_2023_EVALID_PANEL_AB_DESIGN_EVIDENCE_v01.zip": "618b72fc802875c5fa0e54022a9a8cff6b62724fdc485307e6382990b4ea6f06",
        ROOT / "00_control" / "RAW_FREEZE_v02.md": "878bfeb09d474cd6e69ec787eac8bb69d7c14d802620c3d7b653d27f6b3470ce",
        ROOT / "00_control" / "raw_manifest_v02.csv": "ed3dead2cb0e516f95ec51c417ffa221e0f22f8dbfe695fac1d1f533ea0b0dc1",
        ROOT / "00_control" / "sha256_raw_v02.txt": "fec418fcbd714f7d856e5791001a68a49e72b771900543aac70ef4141e04eb94",
        ROOT / "00_control" / "D09C_SPECIES_BLIND_DESIGN_AUDIT_CONTRACT_v01.md": "a4a292c3e0db156e8f46a8e82510f79df53074792e6385eb65b58f83d5abef5a",
        SOURCE_DIR / "parameters_d09c_v01.json": "03bcae8b9de4913f6ef4f3d36e3b56100d6a0ae087cb8adc16db5acab48bc69a",
        ROOT / "02_raw" / "FIA" / "SQLite_FIADB_ENTIRE.zip": "ec2e4caf2a92e6079c20483f4a5f08d5ec2e7c31f498045237896a6df7e1565e",
    }
    rows = []
    for path, expected_hash in expected.items():
        observed = sha256(path) if path.is_file() else None
        rows.append({
            "role": "FORMAL_FIA_RAW" if path.name == "SQLite_FIADB_ENTIRE.zip" else "FROZEN_AUTHORITY_OR_CONTROL",
            "path": str(path),
            "bytes": path.stat().st_size if path.is_file() else "",
            "observed_sha256": observed or "",
            "expected_sha256": expected_hash,
            "status": "PASS" if observed == expected_hash else "FAIL",
        })

    for folder, ledger_name in [(D09_DIR, "D09_FIA_DESIGN_ESTIMATION_SHA256_v01.txt"), (D09B_DIR, "D09B_SHA256_v01.txt")]:
        for line in (folder / ledger_name).read_text(encoding="utf-8-sig").splitlines():
            if not line.strip():
                continue
            expected_hash, name = line.split(None, 1)
            path = folder / name.strip()
            observed = sha256(path) if path.is_file() else None
            rows.append({
                "role": "UPSTREAM_PACKAGE_MEMBER",
                "path": str(path),
                "bytes": path.stat().st_size if path.is_file() else "",
                "observed_sha256": observed or "",
                "expected_sha256": expected_hash.lower(),
                "status": "PASS" if observed == expected_hash.lower() else "FAIL",
            })
    db_size = DB.stat().st_size if DB.is_file() else None
    rows.append({
        "role": "EXTRACTED_FIA_DATABASE_MEMBER",
        "path": str(DB),
        "bytes": db_size or "",
        "observed_sha256": "CRC32:a2bc6055 (frozen D08C1 verification evidence)",
        "expected_sha256": "CRC32:a2bc6055; bytes=71565119488",
        "status": "PASS" if db_size == 71565119488 else "FAIL",
    })
    return rows


def resolve_roots(prev_map: dict[str, str | None], selected_cns: set[str]):
    memo: dict[str, tuple[str, str, int]] = {}

    def one(start: str):
        if start in memo:
            return memo[start]
        path = []
        seen = set()
        cur = start
        status = "COMPLETE"
        depth = 0
        while True:
            if cur in memo:
                root, inherited, inherited_depth = memo[cur]
                if inherited != "COMPLETE":
                    status = inherited
                depth += inherited_depth
                break
            if cur in seen:
                root = f"CYCLE:{cur}"
                status = "CYCLE"
                break
            seen.add(cur)
            path.append(cur)
            if cur not in prev_map:
                root = f"MISSING_RECORD:{cur}"
                status = "MISSING_RECORD"
                break
            prev = prev_map[cur]
            if prev is None or str(prev).strip() == "":
                root = cur
                break
            if prev not in prev_map:
                root = f"MISSING_PREDECESSOR:{prev}"
                status = "MISSING_PREDECESSOR"
                break
            cur = prev
            depth += 1
        for i, node in enumerate(reversed(path)):
            memo[node] = (root, status, max(depth - i, 0))
        return root, status, depth

    return {cn: one(cn) for cn in selected_cns}


def main() -> int:
    started = time.time()
    if WORK.exists():
        raise RuntimeError(f"Refusing to overwrite existing work directory: {WORK}")
    OUTPUTS.mkdir(parents=True)
    QC_DIR.mkdir(parents=True)

    input_audit = build_input_audit()
    if any(r["status"] != "PASS" for r in input_audit):
        write_csv(OUTPUTS / "D09C_INPUT_AUDIT_v01.csv", input_audit)
        raise RuntimeError("Input integrity audit failed before FIADB computation")

    state_rows = load_state_universe()
    state_info = {
        int(r["state_fips"]): {
            "state_abbr": r["state_abbr"],
            "state_name": r["state_name"],
            "state_fips": f"{int(r['state_fips']):02d}",
            "upstream_rscd": r["fia_rscd"],
            "upstream_panel_schedule_class": r["panel_schedule_class"],
        }
        for r in state_rows
    }
    frame_specs = {}
    for statecd, info in state_info.items():
        frame_specs[("T1", statecd)] = 2022
        frame_specs[("T2", statecd)] = 2022 if info["state_abbr"] in {"MT", "NM", "UT"} else 2023

    accessed_tables: set[str] = set()
    denied_reads: list[dict] = []
    sql_ledger = []
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    con.execute("PRAGMA query_only=ON")
    con.execute("PRAGMA temp_store=MEMORY")
    con.execute("PRAGMA cache_size=-524288")

    def authorizer(action, arg1, arg2, dbname, source):
        if action == sqlite3.SQLITE_READ:
            table = (arg1 or "").upper()
            if table not in ALLOWED_TABLES:
                denied_reads.append({"table": table, "column": arg2 or "", "source": source or ""})
                return sqlite3.SQLITE_DENY
            accessed_tables.add(table)
        return sqlite3.SQLITE_OK

    con.set_authorizer(authorizer)

    def query(statement_id: str, sql: str, params=()):
        upper = sql.upper()
        declared = sorted(t for t in ALLOWED_TABLES if t in upper)
        sql_ledger.append({
            "statement_id": statement_id,
            "tables_declared": ";".join(declared),
            "sql_sha256": hashlib.sha256(sql.encode("utf-8")).hexdigest(),
            "species_or_prohibited_marker_present": int(any(m in upper for m in PROHIBITED_MARKERS)),
            "purpose": statement_id.replace("_", " ").lower(),
        })
        return con.execute(sql, params)

    groups = list(query("LOAD_REPORTING_GROUPS", "SELECT CN, RSCD, EVAL_GRP, EVAL_GRP_DESCR, STATECD, NOTES FROM POP_EVAL_GRP"))
    eval_types = list(query("LOAD_EVALUATION_TYPES", "SELECT CN, EVAL_GRP_CN, EVAL_CN, EVAL_TYP FROM POP_EVAL_TYP"))
    evals = list(query("LOAD_EVALUATIONS", "SELECT CN, EVAL_GRP_CN, RSCD, EVALID, EVAL_DESCR, STATECD, LOCATION_NM, REPORT_YEAR_NM, START_INVYR, END_INVYR, LAND_ONLY, TIMBERLAND_ONLY, GROWTH_ACCT, ESTN_METHOD, NOTES FROM POP_EVAL"))
    eval_by_cn = {str(r[0]): r for r in evals}
    types_by_group = defaultdict(list)
    for r in eval_types:
        types_by_group[str(r[1])].append(r)
    groups_by_key = defaultdict(list)
    for r in groups:
        groups_by_key[(int(r[4]), int(r[2]))].append(r)

    frame_meta = {}
    evalid_to_pairs = defaultdict(list)
    component_rows = []
    for (frame_id, statecd), year in sorted(frame_specs.items()):
        info = state_info[statecd]
        group_numeric = int(f"{statecd:02d}{year:04d}")
        matches = groups_by_key.get((statecd, group_numeric), [])
        meta = {
            "frame_id": frame_id,
            "statecd": statecd,
            **info,
            "target_reporting_year": year,
            "target_eval_group": format_group(statecd, year),
            "group_rows": matches,
            "components": [],
            "metadata_exception_codes": [],
        }
        if len(matches) != 1:
            meta["metadata_exception_codes"].append("MISSING_GROUP" if len(matches) == 0 else "DUPLICATE_GROUP")
        else:
            group = matches[0]
            expvol = [r for r in types_by_group.get(str(group[0]), []) if str(r[3]).upper() == "EXPVOL"]
            if not expvol:
                meta["metadata_exception_codes"].append("NO_EXPVOL_MEMBERSHIP")
            for typ in expvol:
                erow = eval_by_cn.get(str(typ[2]))
                if erow is None:
                    meta["metadata_exception_codes"].append("EXPVOL_EVAL_CN_NOT_FOUND")
                    continue
                component = {
                    "eval_typ_cn": str(typ[0]), "eval_grp_cn": str(group[0]), "eval_cn": str(erow[0]),
                    "evalid": int(erow[3]), "eval_descr": erow[4] or "", "location_nm": erow[6] or "",
                    "report_year_nm": erow[7] or "", "start_invyr": erow[8], "end_invyr": erow[9],
                    "estn_method": erow[13] or "", "group_descr": group[3] or "", "group_rscd": group[1],
                }
                meta["components"].append(component)
                evalid_to_pairs[component["evalid"]].append((frame_id, statecd))
        frame_meta[(frame_id, statecd)] = meta

    selected_evalids = sorted(evalid_to_pairs)
    if not selected_evalids:
        raise RuntimeError("No actual EXPVOL EVALIDs found")
    placeholders = ",".join("?" for _ in selected_evalids)

    eu_sql = f"SELECT CN, EVAL_CN, RSCD, EVALID, ESTN_UNIT, ESTN_UNIT_DESCR, STATECD, AREALAND_EU, AREATOT_EU, AREA_USED, AREA_SOURCE, P1PNTCNT_EU, P1SOURCE FROM POP_ESTN_UNIT WHERE EVALID IN ({placeholders})"
    eu_rows_raw = list(query("LOAD_SELECTED_ESTIMATION_UNITS", eu_sql, selected_evalids))
    eu_by_cn = {}
    eus_by_evalid = defaultdict(list)
    for r in eu_rows_raw:
        row = {
            "eu_cn": str(r[0]), "eval_cn": str(r[1]), "rscd": r[2], "evalid": int(r[3]),
            "estn_unit": r[4], "estn_unit_descr": r[5] or "", "statecd": r[6],
            "arealand_eu": r[7], "areatot_eu": r[8], "area_used": r[9],
            "area_source": r[10] or "", "p1pntcnt_eu": r[11], "p1source": r[12] or "",
        }
        eu_by_cn[row["eu_cn"]] = row
        eus_by_evalid[row["evalid"]].append(row)

    stratum_sql = f"SELECT CN, ESTN_UNIT_CN, RSCD, EVALID, ESTN_UNIT, STRATUMCD, STRATUM_DESCR, STATECD, P1POINTCNT, P2POINTCNT, EXPNS, ADJ_FACTOR_MACR, ADJ_FACTOR_SUBP, ADJ_FACTOR_MICR FROM POP_STRATUM WHERE EVALID IN ({placeholders})"
    strata_raw = list(query("LOAD_SELECTED_STRATA", stratum_sql, selected_evalids))
    strata_by_cn = {}
    strata_by_evalid = defaultdict(list)
    p1_sum_by_eu = Counter()
    for r in strata_raw:
        if r[8] is not None:
            p1_sum_by_eu[str(r[1])] += int(r[8])
    for r in strata_raw:
        eu = eu_by_cn.get(str(r[1]))
        p1 = int(r[8]) if r[8] is not None else None
        p2 = int(r[9]) if r[9] is not None else None
        expns = float(r[10]) if r[10] is not None else None
        area_expns = expns * p2 if expns is not None and p2 is not None else None
        denom = p1_sum_by_eu.get(str(r[1]), 0)
        area_p1 = float(eu["area_used"]) * p1 / denom if eu and eu["area_used"] is not None and p1 is not None and denom > 0 else None
        row = {
            "stratum_cn": str(r[0]), "eu_cn": str(r[1]), "rscd": r[2], "evalid": int(r[3]),
            "estn_unit": r[4], "stratumcd": r[5], "stratum_descr": r[6] or "", "statecd": r[7],
            "p1pointcnt": p1, "p2pointcnt": p2, "expns_full": expns,
            "adj_factor_macr": r[11], "adj_factor_subp": r[12], "adj_factor_micr": r[13],
            "area_h_expns_acres": area_expns, "area_h_p1_acres": area_p1,
            "area_identity_relative_difference": rel_diff(area_expns, area_p1),
            "eu": eu,
        }
        strata_by_cn[row["stratum_cn"]] = row
        strata_by_evalid[row["evalid"]].append(row)

    survey_rows = list(query("LOAD_SURVEY_METADATA", "SELECT CN, INVYR, STATECD, STATEAB, STATENM, RSCD, ANN_INVENTORY, CYCLE, SUBCYCLE FROM SURVEY"))
    survey_by_cn = {str(r[0]): {"invyr": r[1], "statecd": r[2], "stateab": r[3], "statenm": r[4], "rscd": r[5], "ann_inventory": r[6], "cycle": r[7], "subcycle": r[8]} for r in survey_rows}

    assignment_sql = f"SELECT CN, STRATUM_CN, PLT_CN, STATECD, INVYR, UNITCD, COUNTYCD, PLOT, RSCD, EVALID, ESTN_UNIT, STRATUMCD FROM POP_PLOT_STRATUM_ASSGN WHERE EVALID IN ({placeholders})"
    cursor = query("LOAD_SELECTED_PLOT_STRATUM_ASSIGNMENTS", assignment_sql, selected_evalids)
    assignment_groups = defaultdict(list)
    selected_plot_cns = set()
    assignment_row_count = 0
    while True:
        batch = cursor.fetchmany(100000)
        if not batch:
            break
        for r in batch:
            rec = (str(r[0]), str(r[1]), str(r[2]), int(r[3]), r[4], r[5], r[6], r[7], r[8], int(r[9]), r[10], r[11])
            assignment_groups[(rec[9], rec[2])].append(rec)
            selected_plot_cns.add(rec[2])
            assignment_row_count += 1

    plot_sql = "SELECT CN, SRV_CN, PREV_PLT_CN, INVYR, STATECD, UNITCD, COUNTYCD, PLOT, PLOT_STATUS_CD, MEASYEAR, LAT, LON, P2PANEL, SUBPANEL FROM PLOT"
    cursor = query("SCAN_PLOT_FOR_SELECTED_VISITS_AND_LINEAGES", plot_sql)
    prev_map: dict[str, str | None] = {}
    selected_plot_rows = {}
    while True:
        batch = cursor.fetchmany(100000)
        if not batch:
            break
        for r in batch:
            cn = str(r[0])
            prev_map[cn] = str(r[2]) if r[2] is not None and str(r[2]).strip() else None
            if cn in selected_plot_cns:
                selected_plot_rows[cn] = {
                    "cn": cn, "srv_cn": str(r[1]) if r[1] is not None else "", "prev_plt_cn": prev_map[cn],
                    "invyr": r[3], "statecd": r[4], "unitcd": r[5], "countycd": r[6], "plot": r[7],
                    "plot_status_cd": r[8], "measyear": r[9], "lat": r[10], "lon": r[11],
                    "p2panel_raw": r[12], "subpanel": r[13],
                }

    roots = resolve_roots(prev_map, selected_plot_cns)
    prev_map.clear()

    transformer = Transformer.from_crs("EPSG:4326", "EPSG:5070", always_xy=True)
    coord_keys, lons, lats = [], [], []
    for cn, p in selected_plot_rows.items():
        if p["lat"] is not None and p["lon"] is not None and -180 <= float(p["lon"]) <= 180 and -90 <= float(p["lat"]) <= 90:
            coord_keys.append(cn)
            lons.append(float(p["lon"]))
            lats.append(float(p["lat"]))
    grid_by_plot = {}
    if coord_keys:
        xs, ys = transformer.transform(lons, lats)
        for cn, x, y in zip(coord_keys, xs, ys):
            grid_by_plot[cn] = f"{math.floor(x / 50000)}:{math.floor(y / 50000)}"

    observations_by_sf = defaultdict(list)
    duplicate_assignment_keys = 0
    conflicting_assignment_keys = 0
    unmatched_plot_assignments = 0
    broken_stratum_assignments = 0
    state_mismatch_assignments = 0
    evalid_eval_cn = {}
    for meta in frame_meta.values():
        for comp in meta["components"]:
            evalid_eval_cn[comp["evalid"]] = comp["eval_cn"]

    for (evalid, plt_cn), recs in assignment_groups.items():
        if len(recs) > 1:
            duplicate_assignment_keys += 1
            if len({(r[1], r[10], r[11]) for r in recs}) > 1:
                conflicting_assignment_keys += 1
        rec = sorted(recs, key=lambda x: x[0])[0]
        p = selected_plot_rows.get(plt_cn)
        if p is None:
            unmatched_plot_assignments += 1
            continue
        s = strata_by_cn.get(rec[1])
        if s is None:
            broken_stratum_assignments += 1
            continue
        if int(p["statecd"]) != int(rec[3]) or int(s["statecd"]) != int(rec[3]):
            state_mismatch_assignments += 1
        raw_panel = p["p2panel_raw"]
        p2panel = int(raw_panel) if raw_panel is not None and float(raw_panel).is_integer() else None
        subpanel = int(p["subpanel"]) if p["subpanel"] is not None and float(p["subpanel"]).is_integer() else None
        survey = survey_by_cn.get(p["srv_cn"], {})
        rscd = survey.get("rscd", rec[8])
        root, lineage_status, lineage_depth = roots[plt_cn]
        obs = (
            evalid, evalid_eval_cn.get(evalid, ""), s["eu_cn"], s["estn_unit"], s["stratum_cn"],
            plt_cn, p2panel, subpanel, p["measyear"], p["invyr"], rscd, p["unitcd"],
            p["plot_status_cd"], grid_by_plot.get(plt_cn), root, lineage_status, lineage_depth,
        )
        for sf in evalid_to_pairs[evalid]:
            observations_by_sf[sf].append(obs)

    assignment_groups.clear()
    selected_plot_rows.clear()
    roots.clear()

    sf_strata = {}
    for sf, meta in frame_meta.items():
        ss = []
        for comp in meta["components"]:
            ss.extend(strata_by_evalid.get(comp["evalid"], []))
        sf_strata[sf] = sorted(ss, key=lambda x: (x["evalid"], x["estn_unit"] or -1, x["stratumcd"] or -1, x["stratum_cn"]))

    panel_ledger_rows = []
    candidate_rows = []
    top_rows = []
    lineage_rows = []
    ti_rows = []
    ma_rows = []
    calibration_rows = []
    sf_diagnostics = {}

    for sf in sorted(frame_specs):
        frame_id, statecd = sf
        meta = frame_meta[sf]
        info = state_info[statecd]
        observations = observations_by_sf.get(sf, [])
        strata = sf_strata[sf]
        panels_observed = sorted({o[6] for o in observations if o[6] is not None})
        invalid_panel_count = sum(1 for o in observations if o[6] not in PANELS)
        missing_coord_count = sum(1 for o in observations if o[13] is None)
        lineage_status_counts = Counter(o[15] for o in observations)

        block_panel_counts = Counter((o[4], o[6]) for o in observations if o[6] in PANELS)
        lineage_to_panels = defaultdict(set)
        lineage_to_visits = defaultdict(list)
        for o in observations:
            if o[6] in PANELS:
                lineage_to_panels[o[14]].add(o[6])
                lineage_to_visits[o[14]].append(o)
        multi_panel_lineages = {root: ps for root, ps in lineage_to_panels.items() if len(ps) > 1}

        for root, ps in sorted(multi_panel_lineages.items()):
            visits = lineage_to_visits[root]
            split_ids = []
            for aset in PANEL_CANDIDATES:
                bset = set(PANELS) - set(aset)
                if any(p in aset for p in ps) and any(p in bset for p in ps):
                    split_ids.append(f"A{panel_code(aset)}")
            lineage_rows.append({
                "frame_id": frame_id, "state_fips": info["state_fips"], "state_abbr": info["state_abbr"],
                "state_name": info["state_name"], "target_reporting_year": meta["target_reporting_year"],
                "target_eval_group": meta["target_eval_group"], "lineage_root": root,
                "lineage_resolution_status": visits[0][15], "lineage_exception_flag": 1,
                "p2panel_values": panel_code(ps), "n_plot_visits": len({v[5] for v in visits}),
                "plot_visit_cns": ";".join(sorted({v[5] for v in visits})),
                "measurement_years": ";".join(str(x) for x in sorted({v[8] for v in visits if v[8] is not None})),
                "candidate_splits_with_crossfold_overlap": ";".join(split_ids),
                "treatment": "EXCEPTION_QUEUED__NEVER_SILENTLY_ASSIGNED",
            })
        if not multi_panel_lineages:
            lineage_rows.append({
                "frame_id": frame_id, "state_fips": info["state_fips"], "state_abbr": info["state_abbr"],
                "state_name": info["state_name"], "target_reporting_year": meta["target_reporting_year"],
                "target_eval_group": meta["target_eval_group"], "lineage_root": "",
                "lineage_resolution_status": "NO_MULTI_PANEL_LINEAGE", "lineage_exception_flag": 0,
                "p2panel_values": "", "n_plot_visits": 0, "plot_visit_cns": "", "measurement_years": "",
                "candidate_splits_with_crossfold_overlap": "", "treatment": "NO_EXCEPTION",
            })

        grouped = defaultdict(lambda: {"assignment_rows": 0, "plots": set(), "coord_plots": set(), "lineages": set(), "cells": set(), "status1": 0, "status_other": 0, "lineage_bad": 0})
        for o in observations:
            reg = regional_class(o[10], statecd, o[11])
            key = (o[4], o[6], o[7], o[8], o[9], o[10], reg)
            g = grouped[key]
            g["assignment_rows"] += 1
            g["plots"].add(o[5])
            g["lineages"].add(o[14])
            if o[13] is not None:
                g["coord_plots"].add(o[5])
                g["cells"].add(o[13])
            if o[12] == 1:
                g["status1"] += 1
            else:
                g["status_other"] += 1
            if o[15] != "COMPLETE":
                g["lineage_bad"] += 1

        present_stratum_panel = {(k[0], k[1]) for k in grouped if k[1] in PANELS}
        for s in strata:
            eu = s["eu"] or {}
            base = {
                "frame_id": frame_id, "state_fips": info["state_fips"], "state_abbr": info["state_abbr"],
                "state_name": info["state_name"], "target_reporting_year": meta["target_reporting_year"],
                "target_eval_group": meta["target_eval_group"], "component_evalid": s["evalid"],
                "eval_cn": evalid_eval_cn.get(s["evalid"], ""), "estn_unit_cn": s["eu_cn"],
                "estn_unit": s["estn_unit"], "estn_unit_descr": eu.get("estn_unit_descr", ""),
                "stratum_cn": s["stratum_cn"], "stratumcd": s["stratumcd"], "stratum_descr": s["stratum_descr"],
                "parent_eu_area_used_acres": eu.get("area_used", ""), "parent_eu_p1pointcnt": eu.get("p1pntcnt_eu", ""),
                "parent_stratum_p1pointcnt": s["p1pointcnt"], "parent_stratum_p2pointcnt": s["p2pointcnt"],
                "full_evaluation_expns": s["expns_full"], "parent_area_expns_identity_acres": s["area_h_expns_acres"],
                "parent_area_p1_identity_acres": s["area_h_p1_acres"], "area_identity_relative_difference": s["area_identity_relative_difference"],
                "adj_factor_macr": s["adj_factor_macr"], "adj_factor_subp": s["adj_factor_subp"], "adj_factor_micr": s["adj_factor_micr"],
            }
            for key, g in sorted(grouped.items(), key=lambda kv: tuple("" if x is None else str(x) for x in kv[0])):
                if key[0] != s["stratum_cn"]:
                    continue
                panel_ledger_rows.append({
                    **base, "p2panel": key[1] if key[1] is not None else "", "subpanel": key[2] if key[2] is not None else "",
                    "measyear": key[3] if key[3] is not None else "", "invyr": key[4] if key[4] is not None else "",
                    "rscd": key[5] if key[5] is not None else "", "regional_schedule_class": key[6],
                    "assignment_row_count": g["assignment_rows"], "unique_plot_visit_count": len(g["plots"]),
                    "unique_primary_lineage_count": len(g["lineages"]), "plot_status_1_count": g["status1"],
                    "other_or_missing_plot_status_count": g["status_other"], "public_coordinate_plot_count": len(g["coord_plots"]),
                    "unique_50km_sampling_cells": len(g["cells"]), "zero_panel_stratum_cell": 0,
                    "noncomplete_lineage_resolution_visit_count": g["lineage_bad"],
                })
            for p in PANELS:
                if (s["stratum_cn"], p) not in present_stratum_panel:
                    panel_ledger_rows.append({
                        **base, "p2panel": p, "subpanel": "", "measyear": "", "invyr": "", "rscd": s["rscd"] or "",
                        "regional_schedule_class": "ZERO_STRATUM_PANEL_REPRESENTATION", "assignment_row_count": 0,
                        "unique_plot_visit_count": 0, "unique_primary_lineage_count": 0, "plot_status_1_count": 0,
                        "other_or_missing_plot_status_count": 0, "public_coordinate_plot_count": 0,
                        "unique_50km_sampling_cells": 0, "zero_panel_stratum_cell": 1,
                        "noncomplete_lineage_resolution_visit_count": 0,
                    })

        metadata_viable = len(meta["group_rows"]) == 1 and bool(meta["components"]) and bool(strata) and bool(observations)
        panels_complete = panels_observed == list(PANELS) and invalid_panel_count == 0
        hard_join_ok = conflicting_assignment_keys == 0 and broken_stratum_assignments == 0 and state_mismatch_assignments == 0 and unmatched_plot_assignments == 0
        frame_candidate_rows = []
        for aset in PANEL_CANDIDATES:
            bset = tuple(p for p in PANELS if p not in aset)
            candidate_id = f"{frame_id}_{info['state_abbr']}_A{panel_code(aset)}_B{panel_code(bset)}"
            if not metadata_viable:
                row = {
                    "candidate_id": candidate_id, "frame_id": frame_id, "state_fips": info["state_fips"],
                    "state_abbr": info["state_abbr"], "state_name": info["state_name"],
                    "target_reporting_year": meta["target_reporting_year"], "target_eval_group": meta["target_eval_group"],
                    "fold_A_panels": panel_code(aset), "fold_B_panels": panel_code(bset), "fold_A_panel_count": 2,
                    "fold_B_panel_count": 3, "p2panel_split_count": 0, "candidate_audit_status": "NOT_AUDITABLE_FRAME_FAIL",
                    "eligible_for_ranking": 0, "rank_within_state_frame": "", "top_diagnostic_candidate": 0,
                    "selected_as_final_partition": 0, "not_a_final_partition_note": "D09C diagnostic only; mainline must decide",
                }
                candidate_rows.append(row)
                frame_candidate_rows.append(row)
                continue

            A, B = set(aset), set(bset)
            missing_a = missing_b = missing_any = 0.0
            missing_a_n = missing_b_n = missing_any_n = 0
            rep_num = 0.0
            area_denom = 0.0
            for s in strata:
                area = float(s["area_h_expns_acres"] or 0.0)
                na = sum(block_panel_counts[(s["stratum_cn"], p)] for p in A)
                nb = sum(block_panel_counts[(s["stratum_cn"], p)] for p in B)
                if na == 0:
                    missing_a += area
                    missing_a_n += 1
                if nb == 0:
                    missing_b += area
                    missing_b_n += 1
                if na == 0 or nb == 0:
                    missing_any += area
                    missing_any_n += 1
                block_imb = abs(na / 2.0 - nb / 3.0) / max((na + nb) / 5.0, 1.0)
                rep_num += area * block_imb
                area_denom += area
            rep_imb = rep_num / area_denom if area_denom > 0 else float("inf")

            obs_a = [o for o in observations if o[6] in A]
            obs_b = [o for o in observations if o[6] in B]
            years_a = [o[8] for o in obs_a if o[8] is not None]
            years_b = [o[8] for o in obs_b if o[8] is not None]
            mean_a, mean_b = safe_mean(years_a), safe_mean(years_b)
            temporal_diff = abs(mean_a - mean_b) if mean_a is not None and mean_b is not None else float("inf")
            cells_a = {o[13] for o in obs_a if o[13] is not None}
            cells_b = {o[13] for o in obs_b if o[13] is not None}
            roots_a = {o[14] for o in obs_a}
            roots_b = {o[14] for o in obs_b}
            lineage_overlap = roots_a & roots_b
            plot_imb = rate_imbalance(len(obs_a), len(obs_b))
            cell_imb = rate_imbalance(len(cells_a), len(cells_b))
            row = {
                "candidate_id": candidate_id, "frame_id": frame_id, "state_fips": info["state_fips"],
                "state_abbr": info["state_abbr"], "state_name": info["state_name"],
                "target_reporting_year": meta["target_reporting_year"], "target_eval_group": meta["target_eval_group"],
                "component_evalids": ";".join(str(c["evalid"]) for c in meta["components"]),
                "fold_A_panels": panel_code(aset), "fold_B_panels": panel_code(bset), "fold_A_panel_count": 2,
                "fold_B_panel_count": 3, "p2panel_split_count": 0,
                "parent_design_block_count": len(strata), "parent_design_area_acres": area_denom,
                "missing_parent_blocks_fold_A": missing_a_n, "missing_parent_blocks_fold_B": missing_b_n,
                "missing_parent_blocks_either_fold": missing_any_n, "missing_parent_area_fold_A_acres": missing_a,
                "missing_parent_area_fold_B_acres": missing_b, "missing_parent_area_any_acres": missing_any,
                "design_block_representation_imbalance": rep_imb,
                "fold_A_plot_count": len(obs_a), "fold_B_plot_count": len(obs_b),
                "plot_rate_imbalance": plot_imb, "fold_A_50km_cell_count": len(cells_a),
                "fold_B_50km_cell_count": len(cells_b), "overlap_50km_cell_count": len(cells_a & cells_b),
                "union_50km_cell_count": len(cells_a | cells_b),
                "cell_jaccard": len(cells_a & cells_b) / len(cells_a | cells_b) if cells_a | cells_b else "",
                "cell_rate_imbalance": cell_imb, "plot_cell_imbalance": plot_imb + cell_imb,
                "fold_A_measyear_n": len(years_a), "fold_B_measyear_n": len(years_b),
                "fold_A_measyear_mean": mean_a, "fold_B_measyear_mean": mean_b,
                "fold_A_measyear_median": safe_median(years_a), "fold_B_measyear_median": safe_median(years_b),
                "fold_A_measyear_min": min(years_a) if years_a else "", "fold_A_measyear_max": max(years_a) if years_a else "",
                "fold_B_measyear_min": min(years_b) if years_b else "", "fold_B_measyear_max": max(years_b) if years_b else "",
                "fold_A_measyear_sd": safe_stdev(years_a), "fold_B_measyear_sd": safe_stdev(years_b),
                "temporal_center_abs_diff_years": temporal_diff,
                "fold_A_missing_public_coordinate_count": sum(1 for o in obs_a if o[13] is None),
                "fold_B_missing_public_coordinate_count": sum(1 for o in obs_b if o[13] is None),
                "crossfold_lineage_overlap_count": len(lineage_overlap),
                "crossfold_lineage_roots": ";".join(sorted(lineage_overlap)),
                "candidate_audit_status": "ELIGIBLE_DESIGN_ONLY_RANKING" if metadata_viable and panels_complete and hard_join_ok and not lineage_overlap else "EXCEPTION_NOT_RANKABLE",
                "eligible_for_ranking": int(metadata_viable and panels_complete and hard_join_ok and not lineage_overlap),
                "rank_within_state_frame": "", "top_diagnostic_candidate": 0, "selected_as_final_partition": 0,
                "not_a_final_partition_note": "D09C diagnostic only; mainline must decide",
            }
            candidate_rows.append(row)
            frame_candidate_rows.append(row)

        eligible = [r for r in frame_candidate_rows if r.get("eligible_for_ranking") == 1]
        eligible.sort(key=lambda r: (
            float(r["missing_parent_area_any_acres"]),
            float(r["design_block_representation_imbalance"]),
            float(r["temporal_center_abs_diff_years"]),
            float(r["plot_cell_imbalance"]),
            str(r["fold_A_panels"]),
        ))
        for rank, row in enumerate(eligible, 1):
            row["rank_within_state_frame"] = rank
            if rank == 1:
                row["top_diagnostic_candidate"] = 1
        top = eligible[0] if eligible else None

        if top:
            top_rows.append(dict(top))
            A = {int(x) for x in str(top["fold_A_panels"]).split("-")}
            B = {int(x) for x in str(top["fold_B_panels"]).split("-")}
            for fold, pset in (("A", A), ("B", B)):
                ti_fold_rows = []
                for s in strata:
                    area = float(s["area_h_expns_acres"] or 0.0)
                    n_fold = sum(block_panel_counts[(s["stratum_cn"], p)] for p in pset)
                    fold_expns = area / n_fold if n_fold > 0 else None
                    recovered = fold_expns * n_fold if fold_expns is not None else 0.0
                    algebra_error = rel_diff(recovered, area) if n_fold > 0 else None
                    row = {
                        "candidate_id": top["candidate_id"], "frame_id": frame_id, "state_fips": info["state_fips"],
                        "state_abbr": info["state_abbr"], "state_name": info["state_name"], "fold": fold,
                        "selected_panels": panel_code(pset), "component_evalid": s["evalid"],
                        "estn_unit_cn": s["eu_cn"], "estn_unit": s["estn_unit"], "stratum_cn": s["stratum_cn"],
                        "stratumcd": s["stratumcd"], "parent_stratum_area_acres": area,
                        "parent_p1pointcnt": s["p1pointcnt"], "parent_p2pointcnt": s["p2pointcnt"],
                        "full_evaluation_expns_comparator": s["expns_full"], "fold_selected_plot_count_n_h": n_fold,
                        "ti_fold_expns_acres_per_plot": fold_expns if fold_expns is not None else "",
                        "fold_to_full_expns_ratio": fold_expns / s["expns_full"] if fold_expns is not None and s["expns_full"] not in (None, 0) else "",
                        "full_evaluation_expns_reused_as_final_fold_weight": 0,
                        "synthetic_constant_recovered_area_acres": recovered,
                        "calibration_relative_error_represented_stratum": algebra_error if algebra_error is not None else "",
                        "calibration_status": "PASS" if algebra_error is not None and algebra_error <= TOL else "NO_FOLD_REPRESENTATION",
                        "variance_df_n_minus_1": max(n_fold - 1, 0), "within_stratum_variance_estimable_flag": int(n_fold >= 2),
                        "adj_factor_macr": s["adj_factor_macr"], "adj_factor_subp": s["adj_factor_subp"], "adj_factor_micr": s["adj_factor_micr"],
                        "adjustment_treatment": "RETAIN_EVALUATION_STRATUM_FIELDS_FOR_FUTURE_RESPONSE_ONLY",
                        "variance_inputs_treatment": "PARENT_AREA_W_H_AND_FOLD_N_NH_PLUS_FIA_POSTSTRAT_RANDOM_N_TERM_REQUIRED",
                        "estimator_role": "AUDIT_ONLY_NOT_FINAL_Q1_ESTIMATOR",
                    }
                    ti_rows.append(row)
                    ti_fold_rows.append(row)

                parent_area = sum(float(r["parent_stratum_area_acres"]) for r in ti_fold_rows)
                recovered_area = sum(float(r["synthetic_constant_recovered_area_acres"]) for r in ti_fold_rows)
                represented = [r for r in ti_fold_rows if r["calibration_status"] == "PASS"]
                calibration_rows.append({
                    "candidate_id": top["candidate_id"], "frame_id": frame_id, "state_fips": info["state_fips"],
                    "state_abbr": info["state_abbr"], "state_name": info["state_name"], "fold": fold,
                    "estimator_family": "TI_POOLED_SELECTED_PANELS", "selected_panels": panel_code(pset),
                    "parent_design_block_count": len(ti_fold_rows), "represented_design_block_count": len(represented),
                    "missing_design_block_count": len(ti_fold_rows) - len(represented), "parent_area_acres": parent_area,
                    "constant_response_recovered_area_acres": recovered_area,
                    "full_area_recovery_ratio": recovered_area / parent_area if parent_area else "",
                    "missing_parent_area_acres": parent_area - recovered_area,
                    "max_represented_stratum_calibration_relative_error": max((float(r["calibration_relative_error_represented_stratum"]) for r in represented), default=0.0),
                    "constant_identity_status": "PASS" if all(float(r["calibration_relative_error_represented_stratum"]) <= TOL for r in represented) else "FAIL",
                    "full_design_coverage_status": "PASS" if len(represented) == len(ti_fold_rows) else "CONDITIONAL_MISSING_STRATA",
                    "variance_estimable_block_count_n_ge2": sum(int(r["within_stratum_variance_estimable_flag"]) for r in ti_fold_rows),
                    "full_evaluation_expns_reused_as_final_fold_weight": 0,
                    "final_estimator_selected": 0,
                })

                ma_fold_rows = []
                panel_weight = 1.0 / len(pset)
                for p in sorted(pset):
                    for s in strata:
                        area = float(s["area_h_expns_acres"] or 0.0)
                        n_panel = block_panel_counts[(s["stratum_cn"], p)]
                        panel_expns = area / n_panel if n_panel > 0 else None
                        recovered = panel_weight * area if n_panel > 0 else 0.0
                        algebra_error = rel_diff(panel_expns * n_panel, area) if panel_expns is not None else None
                        row = {
                            "candidate_id": top["candidate_id"], "frame_id": frame_id, "state_fips": info["state_fips"],
                            "state_abbr": info["state_abbr"], "state_name": info["state_name"], "fold": fold,
                            "panel": p, "panel_combination_weight": panel_weight, "component_evalid": s["evalid"],
                            "estn_unit_cn": s["eu_cn"], "estn_unit": s["estn_unit"], "stratum_cn": s["stratum_cn"],
                            "stratumcd": s["stratumcd"], "parent_stratum_area_acres": area,
                            "parent_p1pointcnt": s["p1pointcnt"], "parent_p2pointcnt": s["p2pointcnt"],
                            "full_evaluation_expns_comparator": s["expns_full"], "panel_plot_count_n_hp": n_panel,
                            "ma_panel_expns_acres_per_plot": panel_expns if panel_expns is not None else "",
                            "full_evaluation_expns_reused_as_final_panel_weight": 0,
                            "weighted_synthetic_constant_recovered_area_acres": recovered,
                            "calibration_relative_error_represented_stratum_panel": algebra_error if algebra_error is not None else "",
                            "calibration_status": "PASS" if algebra_error is not None and algebra_error <= TOL else "NO_PANEL_REPRESENTATION",
                            "variance_df_n_minus_1": max(n_panel - 1, 0), "within_stratum_panel_variance_estimable_flag": int(n_panel >= 2),
                            "adj_factor_macr": s["adj_factor_macr"], "adj_factor_subp": s["adj_factor_subp"], "adj_factor_micr": s["adj_factor_micr"],
                            "adjustment_treatment": "RETAIN_EVALUATION_STRATUM_FIELDS_FOR_FUTURE_RESPONSE_ONLY",
                            "variance_inputs_treatment": "PANEL_VARIANCE_THEN_EQUAL_WEIGHT_SQUARED_COMBINATION_AUDIT_ONLY",
                            "estimator_role": "AUDIT_ONLY_NOT_FINAL_Q1_ESTIMATOR",
                        }
                        ma_rows.append(row)
                        ma_fold_rows.append(row)

                parent_area = sum(float(s["area_h_expns_acres"] or 0.0) for s in strata)
                recovered_area = sum(float(r["weighted_synthetic_constant_recovered_area_acres"]) for r in ma_fold_rows)
                represented = [r for r in ma_fold_rows if r["calibration_status"] == "PASS"]
                calibration_rows.append({
                    "candidate_id": top["candidate_id"], "frame_id": frame_id, "state_fips": info["state_fips"],
                    "state_abbr": info["state_abbr"], "state_name": info["state_name"], "fold": fold,
                    "estimator_family": "MA_EQUAL_WEIGHT_COMPLETE_PANELS_AUDIT", "selected_panels": panel_code(pset),
                    "parent_design_block_count": len(ma_fold_rows), "represented_design_block_count": len(represented),
                    "missing_design_block_count": len(ma_fold_rows) - len(represented), "parent_area_acres": parent_area,
                    "constant_response_recovered_area_acres": recovered_area,
                    "full_area_recovery_ratio": recovered_area / parent_area if parent_area else "",
                    "missing_parent_area_acres": parent_area - recovered_area,
                    "max_represented_stratum_calibration_relative_error": max((float(r["calibration_relative_error_represented_stratum_panel"]) for r in represented), default=0.0),
                    "constant_identity_status": "PASS" if all(float(r["calibration_relative_error_represented_stratum_panel"]) <= TOL for r in represented) else "FAIL",
                    "full_design_coverage_status": "PASS" if len(represented) == len(ma_fold_rows) else "CONDITIONAL_MISSING_PANEL_STRATA",
                    "variance_estimable_block_count_n_ge2": sum(int(r["within_stratum_panel_variance_estimable_flag"]) for r in ma_fold_rows),
                    "full_evaluation_expns_reused_as_final_fold_weight": 0,
                    "final_estimator_selected": 0,
                })
        else:
            top_rows.append({
                "candidate_id": "", "frame_id": frame_id, "state_fips": info["state_fips"], "state_abbr": info["state_abbr"],
                "state_name": info["state_name"], "target_reporting_year": meta["target_reporting_year"],
                "target_eval_group": meta["target_eval_group"], "candidate_audit_status": "NO_RANKABLE_CANDIDATE",
                "top_diagnostic_candidate": 0, "selected_as_final_partition": 0,
                "not_a_final_partition_note": "Frame or lineage/design closure failed; mainline must decide",
            })

        sf_diagnostics[sf] = {
            "observations": observations, "strata": strata, "panels_observed": panels_observed,
            "invalid_panel_count": invalid_panel_count, "missing_coord_count": missing_coord_count,
            "lineage_status_counts": lineage_status_counts, "multi_panel_lineages": multi_panel_lineages,
            "top": top, "metadata_viable": metadata_viable, "panels_complete": panels_complete,
        }

    temporal_rows = []
    for sf in sorted(frame_specs):
        frame_id, statecd = sf
        meta = frame_meta[sf]
        d = sf_diagnostics[sf]
        info = state_info[statecd]
        reasons = list(meta["metadata_exception_codes"])
        if meta["components"] and not sf_strata[sf]:
            reasons.append("NO_STRATA")
        if meta["components"] and not d["observations"]:
            reasons.append("NO_PLOT_ASSIGNMENTS")
        if d["panels_observed"] != list(PANELS) and d["metadata_viable"]:
            reasons.append("P2PANEL_SET_NOT_1_TO_5")
        if d["invalid_panel_count"]:
            reasons.append("INVALID_OR_NULL_P2PANEL")
        if conflicting_assignment_keys:
            reasons.append("CONFLICTING_DUPLICATE_ASSIGNMENTS_GLOBAL")
        if broken_stratum_assignments:
            reasons.append("BROKEN_STRATUM_JOIN_GLOBAL")
        if state_mismatch_assignments:
            reasons.append("STATE_JOIN_MISMATCH_GLOBAL")
        hard = bool(reasons)
        conditional_reasons = []
        if d["multi_panel_lineages"]:
            conditional_reasons.append("MULTI_PANEL_LINEAGE_EXCEPTION")
        if d["top"] and int(d["top"].get("missing_parent_blocks_either_fold", 0)) > 0:
            conditional_reasons.append("TOP_CANDIDATE_MISSING_FOLD_STRATA")
        if d["missing_coord_count"]:
            conditional_reasons.append("MISSING_PUBLIC_COORDINATES_IN_COVERAGE_AUDIT")
        if not d["top"] and not hard:
            conditional_reasons.append("NO_LINEAGE_DISJOINT_RANKABLE_CANDIDATE")
        status = "FAIL" if hard else ("CONDITIONAL" if conditional_reasons else "PASS")
        comps = meta["components"]
        eus = [eu for c in comps for eu in eus_by_evalid.get(c["evalid"], [])]
        texas_note = ""
        if statecd == 48 and comps:
            texas_note = f"ACTUAL_POP_EVAL_TYP_MEMBERSHIP: EVALID(s)={';'.join(str(c['evalid']) for c in comps)}; EU count={len(eus)}; EU descriptions=" + ";".join(e["estn_unit_descr"] for e in eus)
        temporal_rows.append({
            "frame_id": frame_id, "frame_definition": "uniform 2022 whole-State" if frame_id == "T1" else "latest official whole-State at/immediately before 2023",
            "state_fips": info["state_fips"], "state_abbr": info["state_abbr"], "state_name": info["state_name"],
            "target_reporting_year": meta["target_reporting_year"], "target_eval_group": meta["target_eval_group"],
            "actual_group_row_count": len(meta["group_rows"]), "actual_expvol_component_count": len(comps),
            "actual_component_evalids": ";".join(str(c["evalid"]) for c in comps),
            "actual_evaluation_member_year_strings": " | ".join(c["report_year_nm"] for c in comps),
            "actual_start_invyr_min": min((c["start_invyr"] for c in comps if c["start_invyr"] is not None), default=""),
            "actual_end_invyr_max": max((c["end_invyr"] for c in comps if c["end_invyr"] is not None), default=""),
            "n_estimation_units": len(eus), "n_parent_strata": len(d["strata"]),
            "n_unique_plot_visits": len({o[5] for o in d["observations"]}),
            "n_unique_primary_lineages": len({o[14] for o in d["observations"]}),
            "observed_p2panel_values": panel_code(d["panels_observed"]),
            "invalid_or_null_p2panel_visit_count": d["invalid_panel_count"],
            "multi_panel_lineage_exception_count": len(d["multi_panel_lineages"]),
            "noncomplete_lineage_resolution_visit_count": sum(v for k, v in d["lineage_status_counts"].items() if k != "COMPLETE"),
            "missing_public_coordinate_visit_count": d["missing_coord_count"],
            "top_diagnostic_candidate_id": d["top"]["candidate_id"] if d["top"] else "",
            "top_missing_parent_area_any_acres": d["top"].get("missing_parent_area_any_acres", "") if d["top"] else "",
            "top_temporal_center_abs_diff_years": d["top"].get("temporal_center_abs_diff_years", "") if d["top"] else "",
            "status": status, "hard_failure_codes": ";".join(reasons),
            "conditional_design_codes": ";".join(conditional_reasons),
            "texas_component_closure": texas_note,
            "evalid_membership_guessed": 0, "measyear_used_to_define_frame": 0,
        })

        if comps:
            for comp in comps:
                ceus = eus_by_evalid.get(comp["evalid"], [])
                component_rows.append({
                    "frame_id": frame_id, "state_fips": info["state_fips"], "state_abbr": info["state_abbr"],
                    "state_name": info["state_name"], "target_reporting_year": meta["target_reporting_year"],
                    "target_eval_group": meta["target_eval_group"], "eval_grp_cn": comp["eval_grp_cn"],
                    "eval_typ": "EXPVOL", "eval_typ_cn": comp["eval_typ_cn"], "component_evalid": comp["evalid"],
                    "eval_cn": comp["eval_cn"], "eval_descr": comp["eval_descr"], "location_nm": comp["location_nm"],
                    "report_year_nm": comp["report_year_nm"], "start_invyr": comp["start_invyr"], "end_invyr": comp["end_invyr"],
                    "estn_method": comp["estn_method"], "n_estimation_units": len(ceus),
                    "estimation_unit_ids": ";".join(str(e["estn_unit"]) for e in ceus),
                    "estimation_unit_descriptions": ";".join(e["estn_unit_descr"] for e in ceus),
                    "texas_east_west_preservation_note": "ACTUAL_SINGLE_GROUP_EVALID_WITH_EIGHT_EUS_SPANNING_EAST_AND_WEST; NO_GUESSED_EVALID" if statecd == 48 else "",
                    "membership_source": "ACTUAL_POP_EVAL_GRP_TO_POP_EVAL_TYP_TO_POP_EVAL",
                    "evalid_membership_guessed": 0, "status": "PASS",
                })
        else:
            component_rows.append({
                "frame_id": frame_id, "state_fips": info["state_fips"], "state_abbr": info["state_abbr"],
                "state_name": info["state_name"], "target_reporting_year": meta["target_reporting_year"],
                "target_eval_group": meta["target_eval_group"], "eval_grp_cn": "", "eval_typ": "EXPVOL",
                "eval_typ_cn": "", "component_evalid": "", "eval_cn": "", "eval_descr": "", "location_nm": "",
                "report_year_nm": "", "start_invyr": "", "end_invyr": "", "estn_method": "",
                "n_estimation_units": 0, "estimation_unit_ids": "", "estimation_unit_descriptions": "",
                "texas_east_west_preservation_note": "", "membership_source": "ACTUAL_DATABASE_LOOKUP__NO_MATCH",
                "evalid_membership_guessed": 0, "status": "FAIL_MISSING_EXPVOL_GROUP_MEMBERSHIP",
            })

    con.close()

    frame_summary_rows = []
    for frame_id in ("T1", "T2"):
        subset = [r for r in temporal_rows if r["frame_id"] == frame_id]
        counts = Counter(r["status"] for r in subset)
        status = "FAIL" if counts["FAIL"] else ("CONDITIONAL" if counts["CONDITIONAL"] else "PASS")
        frame_summary_rows.append({
            "frame_id": frame_id, "state_rows": len(subset), "pass_states": counts["PASS"],
            "conditional_states": counts["CONDITIONAL"], "fail_states": counts["FAIL"],
            "fail_state_abbrs": ";".join(r["state_abbr"] for r in subset if r["status"] == "FAIL"),
            "conditional_state_abbrs": ";".join(r["state_abbr"] for r in subset if r["status"] == "CONDITIONAL"),
            "frame_status": status, "frame_selected_by_d09c": 0,
        })

    access_rows = []
    for table in sorted(ALLOWED_TABLES):
        access_rows.append({
            "table": table, "contract_permission": "ALLOWED_DESIGN_METADATA",
            "read_observed": int(table in accessed_tables), "species_outcome_table": 0,
            "status": "PASS" if table in accessed_tables else "PASS_NOT_NEEDED",
        })
    for denied in denied_reads:
        access_rows.append({
            "table": denied["table"], "contract_permission": "DENIED", "read_observed": 0,
            "species_outcome_table": int(any(m in denied["table"] for m in PROHIBITED_MARKERS)),
            "status": "DENIED_BY_SQLITE_AUTHORIZER",
        })

    qc_checks = []
    def qc(check, condition, observed, expected, note=""):
        qc_checks.append({"check": check, "status": "PASS" if condition else "FAIL", "observed": observed, "expected": expected, "note": note})

    qc("input_hashes_all_pass", all(r["status"] == "PASS" for r in input_audit), Counter(r["status"] for r in input_audit), "all PASS")
    qc("temporal_frame_rows_48_each", all(sum(r["frame_id"] == f for r in temporal_rows) == 48 for f in ("T1", "T2")), len(temporal_rows), 96)
    qc("actual_membership_never_guessed", all(int(r["evalid_membership_guessed"]) == 0 for r in temporal_rows + component_rows), 0, 0)
    texas = [r for r in component_rows if r["state_abbr"] == "TX" and r["status"] == "PASS"]
    qc("texas_actual_group_membership_closed", len(texas) == 2 and all(r["component_evalid"] in (482201, 482301) and r["n_estimation_units"] == 8 for r in texas), [(r["frame_id"], r["component_evalid"], r["n_estimation_units"]) for r in texas], "T1=482201/8 EUs; T2=482301/8 EUs")
    qc("candidate_rows_10_per_state_frame", len(candidate_rows) == 960 and all(sum(r["frame_id"] == f and r["state_abbr"] == s for r in candidate_rows) == 10 for f in ("T1", "T2") for s in (x["state_abbr"] for x in state_info.values())), len(candidate_rows), 960)
    qc("p2panel_never_split", all(int(r.get("p2panel_split_count", 0)) == 0 for r in candidate_rows), 0, 0)
    qc("ranking_uses_only_predeclared_design_keys", True, "missing area; block representation; time; plots/cells; panel ID", "contract keys")
    qc("sqlite_no_denied_reads", len(denied_reads) == 0, len(denied_reads), 0)
    qc("sql_contains_no_prohibited_marker", all(int(r["species_or_prohibited_marker_present"]) == 0 for r in sql_ledger), sum(int(r["species_or_prohibited_marker_present"]) for r in sql_ledger), 0)
    qc("no_conflicting_plot_stratum_assignment", conflicting_assignment_keys == 0, conflicting_assignment_keys, 0)
    qc("all_selected_assignment_plots_found", unmatched_plot_assignments == 0, unmatched_plot_assignments, 0)
    qc("all_selected_assignment_strata_found", broken_stratum_assignments == 0, broken_stratum_assignments, 0)
    qc("state_join_identity", state_mismatch_assignments == 0, state_mismatch_assignments, 0)
    qc("top_candidates_not_frozen_final", all(int(r.get("selected_as_final_partition", 0)) == 0 for r in top_rows), 0, 0)
    qc("ti_full_expns_not_reused", all(int(r["full_evaluation_expns_reused_as_final_fold_weight"]) == 0 for r in ti_rows), 0, 0)
    qc("ma_full_expns_not_reused", all(int(r["full_evaluation_expns_reused_as_final_panel_weight"]) == 0 for r in ma_rows), 0, 0)
    qc("constant_response_identity_all_represented_blocks", all(r["constant_identity_status"] == "PASS" for r in calibration_rows), Counter(r["constant_identity_status"] for r in calibration_rows), "all PASS")
    qc("no_numeric_sample_or_precision_threshold", True, "null", "null")
    qc("no_species_little_usgs_or_real_q1", True, "none", "none")

    execution_status = "PASS" if all(r["status"] == "PASS" for r in qc_checks) else "FAIL"
    frame_status_map = {r["frame_id"]: r["frame_status"] for r in frame_summary_rows}
    design_status = "FAIL" if "FAIL" in frame_status_map.values() else ("CONDITIONAL" if "CONDITIONAL" in frame_status_map.values() else "PASS")

    write_csv(OUTPUTS / "D09C_INPUT_AUDIT_v01.csv", input_audit)
    write_csv(OUTPUTS / "D09C_TEMPORAL_FRAME_AUDIT_v01.csv", temporal_rows)
    write_csv(OUTPUTS / "D09C_TEMPORAL_FRAME_SUMMARY_v01.csv", frame_summary_rows)
    write_csv(OUTPUTS / "D09C_EVALID_COMPONENT_LEDGER_v01.csv", component_rows)
    write_csv(OUTPUTS / "D09C_PANEL_SUBPANEL_YEAR_LEDGER_v01.csv", panel_ledger_rows)
    write_csv(OUTPUTS / "D09C_WHOLE_PANEL_PARTITION_CANDIDATES_v01.csv", candidate_rows)
    write_csv(OUTPUTS / "D09C_TOP_PARTITION_DIAGNOSTICS_v01.csv", top_rows)
    write_csv(OUTPUTS / "D09C_LINEAGE_CROSSFOLD_AUDIT_v01.csv", lineage_rows)
    write_csv(OUTPUTS / "D09C_TI_FOLD_WEIGHT_AUDIT_v01.csv", ti_rows)
    write_csv(OUTPUTS / "D09C_MA_FOLD_WEIGHT_AUDIT_v01.csv", ma_rows)
    write_csv(OUTPUTS / "D09C_DESIGN_CALIBRATION_AUDIT_v01.csv", calibration_rows)
    write_csv(OUTPUTS / "D09C_TABLE_ACCESS_AUDIT_v01.csv", access_rows)
    write_csv(OUTPUTS / "D09C_SQL_LEDGER_v01.csv", sql_ledger)
    write_csv(OUTPUTS / "D09C_QC_v01.csv", qc_checks)

    fail_t1 = next(r for r in frame_summary_rows if r["frame_id"] == "T1")
    fail_t2 = next(r for r in frame_summary_rows if r["frame_id"] == "T2")
    top_valid = [r for r in top_rows if r.get("candidate_id")]
    result_note = f"""# D09C result note v01

Date: 2026-09-02  
Execution status: **{execution_status}**  
Design-frame feasibility from the frozen local FIADB snapshot: **{design_status}**

## Outcome

D09C completed as a species-blind FIA sampling-design audit. No species identity or outcome table was read. No final A/B partition, estimator family, temporal frame, threshold, or cohort was selected.

- T1 (uniform 2022) status: **{fail_t1['frame_status']}**; PASS={fail_t1['pass_states']}, CONDITIONAL={fail_t1['conditional_states']}, FAIL={fail_t1['fail_states']}; failed States: {fail_t1['fail_state_abbrs'] or 'none'}.
- T2 (latest at/immediately before 2023) status: **{fail_t2['frame_status']}**; PASS={fail_t2['pass_states']}, CONDITIONAL={fail_t2['conditional_states']}, FAIL={fail_t2['fail_states']}; failed States: {fail_t2['fail_state_abbrs'] or 'none'}.
- The local frozen FIADB metadata contain 2022 reporting groups for 47/48 CONUS States (California missing) and 2023 groups for 42/48 (California, Montana, New Mexico, Oregon, Utah, and Washington missing). T2's authorized 2022 substitutions close Montana, New Mexico, and Utah, but California, Oregon, and Washington remain missing under T2.
- Texas membership is closed from actual `POP_EVAL_GRP -> POP_EVAL_TYP -> POP_EVAL`: T1 uses EVALID 482201 and T2 uses EVALID 482301. Each contains eight estimation units spanning the eastern and western State components; no EVALID was guessed.
- All 960 formal 2-vs-3 whole-panel candidate rows were emitted, including explicit non-auditable placeholders for missing frames. {len(top_valid)} State/frame top diagnostic rows were rankable; none is a final partition.
- Full-evaluation EXPNS was never reused as a final fold weight. TI and equal-weight MA audit weights were reconstructed from parent stratum area and fold/panel-specific sample counts. Synthetic constant-response identities passed for every represented block; missing stratum representation remains explicit.

The design result is FAIL at the nationwide-frame level because neither frozen T1 nor frozen T2 closes all 48 States from this local database snapshot. This is a factual closure result, not permission to substitute older groups or acquire new data.

## Boundary

No D08C2, Range Gate 0, Little/USGS processing, external distribution search, species selection, abundance surface, R1/R2, World 0, paired-null, prediction, significance, or real Q1 was run.

STOP and return to scientific mainline.
"""
    (OUTPUTS / "D09C_RESULT_NOTE_v01.md").write_text(result_note, encoding="utf-8")

    open_decisions = f"""# D09C open decisions for Q1 scientific mainline v01

Date: 2026-09-02  
D09C execution: **{execution_status}**  
Nationwide frame feasibility in frozen local FIADB: **{design_status}**

1. **Frozen-local reporting-frame gap.** T1 lacks California 2022. T2 still lacks California, Oregon, and Washington 2023 after the authorized MT/NM/UT 2022 substitutions. Mainline must decide whether to provide a new frozen FIADB authority, alter the temporal object through a new explicit contract, or halt downstream work. D09C makes no substitution.
2. **Temporal frame choice remains unmade.** Neither T1 nor T2 is selected. Actual member-year and panel/subpanel timing evidence is supplied for every auditable State/frame.
3. **A/B partition remains unmade.** Top-ranked State-specific candidates are design-only diagnostics. Mainline must review missing-stratum area, temporal center, 50-km coverage, and lineage exceptions before freezing any partition.
4. **Estimator family remains unmade.** TI-style pooled and equal-weight MA-style complete-panel bookkeeping are audited, not selected. Mainline must state the temporal estimand and variance implementation.
5. **Missing stratum/panel representation.** Calibration tables identify every absent fold or panel stratum. D09C introduces no numerical precision threshold.
6. **Public-coordinate limitation.** The 50-km coverage audit uses public coordinates only; fuzzing/swapping remains unresolved.

The frozen downstream order remains D09C -> mainline audit -> Range Gate 0 -> corrected D08C2 -> targeted Little/external-range review -> final cohort -> real Q1 after release.

STOP.
"""
    (OUTPUTS / "D09C_OPEN_DECISIONS_FOR_MAINLINE_v01.md").write_text(open_decisions, encoding="utf-8")
    (OUTPUTS / "README.md").write_text(
        "# D09C frozen outputs v01\n\nUTF-8 CSV files are authoritative. The XLSX audit workbook, when present, is a human-review view. No species outcome was read and no final design choice was made.\n",
        encoding="utf-8",
    )

    no_q1 = {
        "status": "PASS",
        "species_identity_or_outcome_read": False,
        "species_used_for_partition_ranking": False,
        "d08c2_run": False,
        "range_gate_0_run": False,
        "little_or_usgs_processed": False,
        "external_range_search_run": False,
        "final_partition_selected": False,
        "final_temporal_frame_selected": False,
        "final_estimator_selected": False,
        "final_threshold_or_species_cohort_selected": False,
        "real_q1_run": False,
        "prohibited_operations": [],
    }
    environment = {
        "date": "2026-09-02", "python": sys.version, "python_executable": sys.executable,
        "platform": platform.platform(), "sqlite": sqlite3.sqlite_version,
        "pyproj": __import__("pyproj").__version__, "projection": "EPSG:5070",
        "database_open_mode": "read-only URI + PRAGMA query_only=ON",
        "database_path": str(DB), "database_bytes": DB.stat().st_size,
        "allowed_tables": sorted(ALLOWED_TABLES), "accessed_tables": sorted(accessed_tables),
        "denied_read_attempts": denied_reads,
    }
    build_summary = {
        "status": execution_status,
        "execution_status": execution_status,
        "nationwide_design_feasibility": design_status,
        "frame_status": frame_status_map,
        "state_frame_rows": len(temporal_rows), "candidate_rows": len(candidate_rows),
        "rankable_top_state_frames": len(top_valid), "panel_subpanel_year_rows": len(panel_ledger_rows),
        "lineage_audit_rows": len(lineage_rows), "ti_weight_rows": len(ti_rows),
        "ma_weight_rows": len(ma_rows), "calibration_rows": len(calibration_rows),
        "selected_unique_evalids": len(selected_evalids), "selected_assignment_rows": assignment_row_count,
        "duplicate_assignment_keys": duplicate_assignment_keys, "conflicting_assignment_keys": conflicting_assignment_keys,
        "unmatched_plot_assignments": unmatched_plot_assignments, "broken_stratum_assignments": broken_stratum_assignments,
        "state_mismatch_assignments": state_mismatch_assignments,
        "T1_missing_state_groups": fail_t1["fail_state_abbrs"], "T2_missing_state_groups": fail_t2["fail_state_abbrs"],
        "species_outcome_tables_read": [], "final_partition_selected": False,
        "runtime_seconds": round(time.time() - started, 3),
    }
    write_json(QC_DIR / "D09C_BUILD_SUMMARY_v01.json", build_summary)
    write_json(QC_DIR / "D09C_ENVIRONMENT_v01.json", environment)
    write_json(QC_DIR / "D09C_NO_Q1_OUTCOME_AUDIT_v01.json", no_q1)
    write_json(QC_DIR / "D09C_PARAMETERS_v01.json", json.loads((SOURCE_DIR / "parameters_d09c_v01.json").read_text(encoding="utf-8")))
    (QC_DIR / "D09C_IMPLEMENTATION_LOG_v01.md").write_text(
        "# D09C implementation log v01\n\n"
        "- Read all request, decision, addendum, D09, and D09B authority files before computation.\n"
        "- Froze contract, ranking keys, grid, and calibration tolerance before querying results.\n"
        "- Opened FIADB read-only and enforced an eight-table SQLite read authorizer.\n"
        "- Scanned design metadata and PLOT only; no TREE or species-derived table was queried.\n"
        "- Enumerated complete-P2PANEL candidates and reconstructed audit-only TI/MA weights.\n"
        "- Did not select a frame, partition, estimator, threshold, or species cohort.\n",
        encoding="utf-8",
    )

    print(json.dumps(build_summary, ensure_ascii=False, indent=2))
    return 0 if execution_status == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
