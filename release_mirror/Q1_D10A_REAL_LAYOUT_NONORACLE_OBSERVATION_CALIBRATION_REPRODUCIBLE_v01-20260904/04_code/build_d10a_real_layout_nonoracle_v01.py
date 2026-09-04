#!/usr/bin/env python3
"""D10A real-layout, non-oracle synthetic observation calibration.

This local-only runner uses species-blind F0 design and opportunity metadata.
Its SQL allowlist is deliberately limited to four design/opportunity tables.
It generates only fresh synthetic outcomes and returns all three frozen models.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import json
import math
import os
import platform
import sqlite3
import sys
import time
import zipfile
from collections import Counter, defaultdict, deque
from pathlib import Path

import numpy as np


ROOT = Path(r"C:\range_paper")
SRC = ROOT / "06_src" / "d10a_real_layout_nonoracle_v01"
OUT = ROOT / "04_derived" / "d10a_real_layout_nonoracle_v01"
QC = ROOT / "05_qc" / "d10a_real_layout_nonoracle_v01"
PARAM_PATH = SRC / "parameters_d10a_real_layout_nonoracle_v01.json"
FREEZE = ROOT / "00_control" / "D10A_REAL_LAYOUT_NONORACLE_CALIBRATION_EXECUTION_FREEZE_v01.md"

D09C_DIR = ROOT / "10_archive" / "d09c_t2_final_correction_v02"
D09C_ZIP = D09C_DIR / "Q1_D09C_T2_FINAL_CORRECTION_REPRODUCIBLE_v02.zip"
D09C_PACKAGE = D09C_DIR / "Q1_D09C_T2_FINAL_CORRECTION_REPRODUCIBLE_v02"
D09C_PARTITIONS = D09C_PACKAGE / "02_outputs" / "Q1_D09C_T2_FINAL_RULE_SELECTED_PARTITIONS_v02.csv"
D09C_TI = D09C_PACKAGE / "02_outputs" / "Q1_D09C_T2_FINAL_FOLD_SPECIFIC_TI_DESIGN_v02.csv"
D09C_PREDECESSOR = D09C_PACKAGE / "01_authoritative_inputs" / "predecessor_v01" / "Q1_D09C_T2_BOUNDED_COMPLETION_REPRODUCIBLE_v01.zip"
D09C_PRE_ROOT = "Q1_D09C_T2_BOUNDED_COMPLETION_REPRODUCIBLE_v01/"

NATIONAL_ZIP = ROOT / "02_raw" / "FIA" / "SQLite_FIADB_ENTIRE.zip"
NATIONAL_DB = ROOT / "99_tmp" / "d08c2_preflight_observational_authority_v01" / "source_cache" / "SQLite_FIADB_ENTIRE.db"
DB_AUTHORITY = ROOT / "05_qc" / "d08c2_preflight_observational_authority_v01" / "Q1_D08C2_PREFLIGHT_ASSET_AUTHORITY_v01.csv"
OBS_ZIPS = ROOT / "02_raw" / "fia_t2_2023_observational_gap_v01" / "raw_table_zips"
D04_PARAMS = ROOT / "10_archive" / "d08c1_v01" / "package" / "inputs" / "d04_eligibility_continuity" / "elig_v02_parameters.json"
E2C_REFERENCE = ROOT / "Q1_range_abundance" / "E2C_LATENT_OCCUPANCY_DETECTION_v0_1_20260831.zip"
E2C_CONTRACT = ROOT / "Q1_range_abundance" / "E2c_latent_occupancy_detection_v0_1" / "E2C_EXPERIMENT_CONTRACT_v0_1.md"

CONUS = {1, 4, 5, 6, 8, 9, 10, 12, 13, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 44, 45, 46, 47, 48, 49, 50, 51, 53, 54, 55, 56}
OVERRIDE = {6: "CA", 41: "OR", 53: "WA"}
ALLOWED_DB_TABLES = {"PLOT", "POP_PLOT_STRATUM_ASSGN", "COND", "SUBPLOT"}


class LayoutAuthorityFailure(RuntimeError):
    pass


def sha256_file(path: Path, chunk: int = 8 * 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def stable_seed(*parts: object) -> int:
    value = "|".join(map(str, parts)).encode("utf-8")
    return int.from_bytes(hashlib.sha256(value).digest()[:8], "little") % (2**32 - 1)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows, fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = list(rows)
    if fields is None:
        fields, seen = [], set()
        for row in rows:
            for key in row:
                if key not in seen:
                    fields.append(key)
                    seen.add(key)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8", newline="\n")


def text(value) -> str:
    return "" if value is None else str(value).strip()


def as_int(value, default=None):
    if value is None or text(value) == "":
        return default
    return int(float(value))


def as_float(value, default=None):
    if value is None or text(value) == "":
        return default
    return float(value)


def parse_panels(value: str) -> set[int]:
    return {int(item) for item in text(value).split("-") if item}


def sqlite_ro(path: Path):
    return sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)


def nested_design_zip(pre: zipfile.ZipFile, state: str, table: str) -> bytes:
    return pre.read(D09C_PRE_ROOT + f"01_authoritative_inputs/ca_or_wa_raw_design_zips/{state}_{table}.zip")


def nested_csv_rows(pre: zipfile.ZipFile, state: str, table: str) -> list[dict[str, str]]:
    data = nested_design_zip(pre, state, table)
    with zipfile.ZipFile(io.BytesIO(data)) as inner:
        expected = f"{state}_{table}.csv"
        if inner.namelist() != [expected]:
            raise LayoutAuthorityFailure(f"Unexpected nested members for {state}_{table}")
        return list(csv.DictReader(io.StringIO(inner.read(expected).decode("utf-8-sig"), newline="")))


def iter_zip_csv(path: Path, member: str):
    with zipfile.ZipFile(path) as archive:
        if archive.namelist() != [member]:
            raise LayoutAuthorityFailure(f"Unexpected ZIP members in {path}")
        with archive.open(member) as raw, io.TextIOWrapper(raw, encoding="utf-8-sig", newline="") as handle:
            yield from csv.DictReader(handle)


# Exact D04 ellipsoidal Albers implementation.
A_EARTH = 6378137.0
INV_F = 298.257222101
FLAT = 1.0 / INV_F
B_EARTH = A_EARTH * (1.0 - FLAT)
ECC = math.sqrt(1.0 - (B_EARTH * B_EARTH) / (A_EARTH * A_EARTH))
LAT1 = math.radians(29.5)
LAT2 = math.radians(45.5)
LAT0 = math.radians(23.0)
LON0 = math.radians(-96.0)


def _m(phi):
    sine = math.sin(phi)
    return math.cos(phi) / math.sqrt(1.0 - ECC * ECC * sine * sine)


def _q(phi):
    sine = math.sin(phi)
    es = ECC * sine
    return (1.0 - ECC * ECC) * (sine / (1.0 - es * es) - math.log((1.0 - es) / (1.0 + es)) / (2.0 * ECC))


M_PAR1, M_PAR2 = _m(LAT1), _m(LAT2)
Q_PAR1, Q_PAR2, Q_ORIGIN = _q(LAT1), _q(LAT2), _q(LAT0)
N_ALB = (M_PAR1 * M_PAR1 - M_PAR2 * M_PAR2) / (Q_PAR2 - Q_PAR1)
C_ALB = M_PAR1 * M_PAR1 + N_ALB * Q_PAR1
RHO0 = A_EARTH * math.sqrt(C_ALB - N_ALB * Q_ORIGIN) / N_ALB


def albers5070(longitude_deg: float, latitude_deg: float) -> tuple[float, float]:
    phi = math.radians(latitude_deg)
    lam = math.radians(longitude_deg)
    rho = A_EARTH * math.sqrt(C_ALB - N_ALB * _q(phi)) / N_ALB
    theta = N_ALB * (lam - LON0)
    return rho * math.sin(theta), RHO0 - rho * math.cos(theta)


def cell_id(x_m: float, y_m: float) -> str:
    return f"50km_{math.floor(x_m / 50000.0)}_{math.floor(y_m / 50000.0)}"


def cell_tuple(identifier: str) -> tuple[int, int]:
    _, ix, iy = identifier.split("_")
    return int(ix), int(iy)


def validate_inputs(param: dict) -> list[dict]:
    checks = []

    def add(check_id, path, expected_hash=None, expected_bytes=None, blocking=True, note=""):
        exists = path.exists()
        actual_bytes = path.stat().st_size if exists else None
        actual_hash = sha256_file(path) if exists and expected_hash is not None and actual_bytes < 1_000_000_000 else "NOT_REHASHED_LARGE"
        hash_ok = expected_hash is None or actual_hash == expected_hash or (actual_hash == "NOT_REHASHED_LARGE" and note.startswith("authority-chain"))
        bytes_ok = expected_bytes is None or actual_bytes == expected_bytes
        ok = exists and bytes_ok and hash_ok
        checks.append({"check_id": check_id, "path": str(path), "expected_bytes": expected_bytes or "", "actual_bytes": actual_bytes or "", "expected_sha256": expected_hash or "", "actual_sha256": actual_hash, "status": "PASS" if ok else "FAIL", "blocking": "YES" if blocking else "NO", "notes": note})
        if blocking and not ok:
            raise LayoutAuthorityFailure(f"{check_id} failed")

    add("D09C_FINAL_ZIP", D09C_ZIP, param["d09c_zip_expected_sha256"])
    add("D09C_PARTITIONS", D09C_PARTITIONS)
    add("D09C_FOLD_TI", D09C_TI)
    add("D09C_PREDECESSOR", D09C_PREDECESSOR)
    add("D04_GRID_PARAMETERS", D04_PARAMS, param["d04_parameters_expected_sha256"])
    add("NATIONAL_FROZEN_ZIP", NATIONAL_ZIP, param["national_zip_expected_sha256"], param["national_zip_expected_bytes"], note="authority-chain: full SHA-256 frozen and previously independently verified")
    add("EXTRACTED_READONLY_DATABASE", NATIONAL_DB, None, param["national_db_expected_bytes"], note="identity cross-checked to frozen preflight asset authority")
    add("EXTRACTED_DATABASE_AUTHORITY", DB_AUTHORITY)
    authority_rows = read_csv(DB_AUTHORITY)
    db_row = next((row for row in authority_rows if row.get("ASSET") == "FIA_SQLITE_EXTRACTED_WORKING_COPY"), None)
    if db_row is None or db_row.get("ACTUAL_SHA256") != "d2935fa9e2c7dd754fbdd8151ba2f093675e3772fefe260336daa308adcaeb72" or as_int(db_row.get("ACTUAL_BYTES")) != param["national_db_expected_bytes"]:
        raise LayoutAuthorityFailure("Extracted database authority row mismatch")
    for state in OVERRIDE.values():
        for table in ("COND", "SUBPLOT"):
            add(f"{state}_{table}_ZIP", OBS_ZIPS / f"{state}_{table}.zip")
    add("E2C_UNPACKED_CONTRACT", E2C_CONTRACT, param["e2c_contract_expected_sha256"], blocking=False)
    add("E2C_LOCAL_REFERENCE_HASH_MISMATCH", E2C_REFERENCE, param["e2c_contract_zip_expected_sha256"], blocking=False, note=f"available local hash is frozen as {param['e2c_local_reference_sha256']}; benchmark only")
    return checks


def schema_gate() -> list[dict]:
    required = {
        "PLOT": {"CN", "STATECD", "INVYR", "P2PANEL", "PLOT_STATUS_CD", "DESIGNCD", "MANUAL", "LAT", "LON"},
        "POP_PLOT_STRATUM_ASSGN": {"CN", "STRATUM_CN", "PLT_CN", "STATECD", "INVYR", "EVALID"},
        "COND": {"PLT_CN", "CONDID", "COND_STATUS_CD", "CONDPROP_UNADJ"},
        "SUBPLOT": {"PLT_CN", "SUBP", "SUBP_STATUS_CD", "SUBPCOND", "MACRCOND", "CONDLIST"},
    }
    con = sqlite_ro(NATIONAL_DB)
    rows = []
    try:
        available_tables = {row[0] for row in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        for table, columns in required.items():
            present = {row[1] for row in con.execute(f"PRAGMA table_info({table})")}
            missing = sorted(columns - present)
            rows.append({"table": table, "required_columns": ";".join(sorted(columns)), "missing_columns": ";".join(missing), "status": "PASS" if table in available_tables and not missing else "FAIL"})
            if table not in available_tables or missing:
                raise LayoutAuthorityFailure(f"Schema gate failed for {table}")
    finally:
        con.close()
    if set(required) != ALLOWED_DB_TABLES:
        raise LayoutAuthorityFailure("SQL allowlist changed")
    return rows


def load_f0(param: dict):
    partitions = read_csv(D09C_PARTITIONS)
    part_by_state = {as_int(row["state_fips"]): row for row in partitions}
    if len(partitions) != 48 or set(part_by_state) != CONUS:
        raise LayoutAuthorityFailure("Frozen 48-state partition identity failed")
    for state, row in part_by_state.items():
        panels_a, panels_b = parse_panels(row["final_A_panels"]), parse_panels(row["final_B_panels"])
        if len(panels_a) != 2 or len(panels_b) != 3 or panels_a & panels_b or panels_a | panels_b != {1, 2, 3, 4, 5}:
            raise LayoutAuthorityFailure(f"Invalid A/B panels in state {state}")

    plots = {}
    mismatch_rows = []
    national_states = sorted(CONUS - set(OVERRIDE))
    evalid_to_state = {as_int(part_by_state[state]["component_evalid"]): state for state in national_states}
    placeholders = ",".join("?" for _ in evalid_to_state)
    query = f"""
        SELECT a.CN AS assignment_cn,a.STRATUM_CN,a.PLT_CN,a.STATECD AS assignment_statecd,
               a.INVYR AS assignment_invyr,a.EVALID,p.STATECD AS plot_statecd,p.INVYR AS plot_invyr,
               p.P2PANEL,p.PLOT_STATUS_CD,p.DESIGNCD,p.MANUAL,p.LAT,p.LON
        FROM POP_PLOT_STRATUM_ASSGN a JOIN PLOT p ON p.CN=a.PLT_CN
        WHERE a.EVALID IN ({placeholders})
    """
    con = sqlite_ro(NATIONAL_DB)
    con.row_factory = sqlite3.Row
    try:
        for row in con.execute(query, tuple(evalid_to_state)):
            state = evalid_to_state[as_int(row["EVALID"])]
            panel = as_int(row["P2PANEL"])
            part = part_by_state[state]
            fold = "A" if panel in parse_panels(part["final_A_panels"]) else "B" if panel in parse_panels(part["final_B_panels"]) else ""
            cn = text(row["PLT_CN"])
            if cn in plots:
                raise LayoutAuthorityFailure(f"Duplicate F0 plot key {cn}")
            plots[cn] = {"plot_cn": cn, "assignment_cn": text(row["assignment_cn"]), "stratum_cn": text(row["STRATUM_CN"]), "statecd": state, "state_abbr": part["state_abbr"], "evalid": as_int(row["EVALID"]), "panel": panel, "fold": fold, "assignment_statecd": as_int(row["assignment_statecd"]), "assignment_invyr": as_int(row["assignment_invyr"]), "plot_statecd": as_int(row["plot_statecd"]), "plot_invyr": as_int(row["plot_invyr"]), "plot_status_cd": as_int(row["PLOT_STATUS_CD"]), "designcd": text(row["DESIGNCD"]), "manual": text(row["MANUAL"]), "latitude": as_float(row["LAT"]), "longitude": as_float(row["LON"]), "source": "FROZEN_NATIONAL_SQLITE"}
    finally:
        con.close()

    with zipfile.ZipFile(D09C_PREDECESSOR) as pre:
        for state, abbreviation in OVERRIDE.items():
            target_evalid = as_int(part_by_state[state]["component_evalid"])
            plot_rows = {row["CN"]: row for row in nested_csv_rows(pre, abbreviation, "PLOT")}
            assignments = [row for row in nested_csv_rows(pre, abbreviation, "POP_PLOT_STRATUM_ASSGN") if as_int(row["EVALID"]) == target_evalid]
            for assn in assignments:
                cn = assn["PLT_CN"]
                if cn in plots or cn not in plot_rows:
                    raise LayoutAuthorityFailure(f"Override F0 linkage failure {abbreviation} {cn}")
                row = plot_rows[cn]
                panel = as_int(row["P2PANEL"])
                part = part_by_state[state]
                fold = "A" if panel in parse_panels(part["final_A_panels"]) else "B" if panel in parse_panels(part["final_B_panels"]) else ""
                plots[cn] = {"plot_cn": cn, "assignment_cn": assn["CN"], "stratum_cn": assn["STRATUM_CN"], "statecd": state, "state_abbr": abbreviation, "evalid": target_evalid, "panel": panel, "fold": fold, "assignment_statecd": as_int(assn["STATECD"]), "assignment_invyr": as_int(assn["INVYR"]), "plot_statecd": as_int(row["STATECD"]), "plot_invyr": as_int(row["INVYR"]), "plot_status_cd": as_int(row["PLOT_STATUS_CD"]), "designcd": text(row["DESIGNCD"]), "manual": text(row["MANUAL"]), "latitude": as_float(row["LAT"]), "longitude": as_float(row["LON"]), "source": "FROZEN_CA_OR_WA_RAW_DESIGN_ZIPS"}
                if as_int(assn["STATECD"]) != as_int(row["STATECD"]) or as_int(assn["INVYR"]) != as_int(row["INVYR"]):
                    mismatch_rows.append({"state_abbr": abbreviation, "assignment_cn": assn["CN"], "plot_cn": cn, "assignment_statecd": assn["STATECD"], "assignment_invyr": assn["INVYR"], "plot_statecd": row["STATECD"], "plot_invyr": row["INVYR"], "retained_by_plot_key": "YES"})

    if len(plots) != param["expected_f0_plot_visits"] or any(row["fold"] not in {"A", "B"} for row in plots.values()):
        raise LayoutAuthorityFailure(f"F0 closure failed: {len(plots)} plots")
    fold_counts = Counter((row["statecd"], row["fold"]) for row in plots.values())
    ti_counts = Counter()
    for row in read_csv(D09C_TI):
        ti_counts[(as_int(row["state_fips"]), row["fold"])] += as_int(row["fold_sample_count"], 0)
    differences = [(key, fold_counts[key], ti_counts[key]) for key in sorted(ti_counts) if fold_counts[key] != ti_counts[key]]
    if differences:
        raise LayoutAuthorityFailure(f"F0/TI mismatch: {differences[:5]}")
    if len([row for row in mismatch_rows if row["state_abbr"] == "OR"]) != 4:
        raise LayoutAuthorityFailure("Frozen OR linkage treatment changed")
    return plots, part_by_state, mismatch_rows


def condition_tokens(value) -> set[int]:
    result = set()
    for token in text(value).replace(";", " ").replace(",", " ").split():
        try:
            result.add(int(float(token)))
        except ValueError:
            pass
    return result


def build_opportunities(plots: dict, param: dict):
    conditions = {}
    subplots = {}
    national_evalids = sorted({row["evalid"] for row in plots.values() if row["source"] == "FROZEN_NATIONAL_SQLITE"})
    placeholders = ",".join("?" for _ in national_evalids)
    con = sqlite_ro(NATIONAL_DB)
    con.row_factory = sqlite3.Row
    try:
        query_cond = f"SELECT c.PLT_CN,c.CONDID,c.COND_STATUS_CD,c.CONDPROP_UNADJ FROM COND c JOIN POP_PLOT_STRATUM_ASSGN a ON a.PLT_CN=c.PLT_CN WHERE a.EVALID IN ({placeholders})"
        for row in con.execute(query_cond, tuple(national_evalids)):
            cn, condid = text(row["PLT_CN"]), as_int(row["CONDID"])
            if cn in plots and condid is not None:
                conditions[(cn, condid)] = {"status": as_int(row["COND_STATUS_CD"]), "prop": as_float(row["CONDPROP_UNADJ"])}
        query_subp = f"SELECT s.PLT_CN,s.SUBP,s.SUBP_STATUS_CD,s.SUBPCOND,s.MACRCOND,s.CONDLIST FROM SUBPLOT s JOIN POP_PLOT_STRATUM_ASSGN a ON a.PLT_CN=s.PLT_CN WHERE a.EVALID IN ({placeholders})"
        for row in con.execute(query_subp, tuple(national_evalids)):
            cn, subp = text(row["PLT_CN"]), as_int(row["SUBP"])
            if cn in plots and subp is not None:
                links = condition_tokens(row["CONDLIST"])
                for key in ("SUBPCOND", "MACRCOND"):
                    value = as_int(row[key])
                    if value is not None:
                        links.add(value)
                subplots[(cn, subp)] = {"status": as_int(row["SUBP_STATUS_CD"]), "links": links}
    finally:
        con.close()

    for abbreviation in OVERRIDE.values():
        for row in iter_zip_csv(OBS_ZIPS / f"{abbreviation}_COND.zip", f"{abbreviation}_COND.csv"):
            cn, condid = text(row["PLT_CN"]), as_int(row["CONDID"])
            if cn in plots and condid is not None:
                value = {"status": as_int(row["COND_STATUS_CD"]), "prop": as_float(row["CONDPROP_UNADJ"])}
                if (cn, condid) in conditions and conditions[(cn, condid)] != value:
                    raise LayoutAuthorityFailure(f"Conflicting condition key {cn} {condid}")
                conditions[(cn, condid)] = value
        for row in iter_zip_csv(OBS_ZIPS / f"{abbreviation}_SUBPLOT.zip", f"{abbreviation}_SUBPLOT.csv"):
            cn, subp = text(row["PLT_CN"]), as_int(row["SUBP"])
            if cn in plots and subp is not None:
                links = condition_tokens(row["CONDLIST"])
                for key in ("SUBPCOND", "MACRCOND"):
                    value = as_int(row[key])
                    if value is not None:
                        links.add(value)
                value = {"status": as_int(row["SUBP_STATUS_CD"]), "links": links}
                if (cn, subp) in subplots and subplots[(cn, subp)] != value:
                    raise LayoutAuthorityFailure(f"Conflicting subplot key {cn} {subp}")
                subplots[(cn, subp)] = value

    cond_by_plot = defaultdict(dict)
    for (cn, condid), value in conditions.items():
        cond_by_plot[cn][condid] = value
    subp_by_plot = defaultdict(dict)
    for (cn, subp), value in subplots.items():
        subp_by_plot[cn][subp] = value

    legitimate_count = 0
    coord_failures = 0
    for cn, plot in plots.items():
        lat, lon = plot["latitude"], plot["longitude"]
        if lat is None or lon is None or not (-90 <= lat <= 90 and -180 <= lon <= 180):
            coord_failures += 1
            plot["x_m"] = plot["y_m"] = None
            plot["cell_50km"] = ""
        else:
            x_m, y_m = albers5070(lon, lat)
            plot["x_m"], plot["y_m"], plot["cell_50km"] = x_m, y_m, cell_id(x_m, y_m)
        accessible = {condid for condid, row in cond_by_plot.get(cn, {}).items() if row["status"] == param["accessible_forest_cond_statuscd"]}
        sampled = {subp for subp, row in subp_by_plot.get(cn, {}).items() if row["status"] == param["sampled_subplot_statuscd"]}
        relevant = {subp for subp in sampled if subp_by_plot[cn][subp]["links"] & accessible}
        props = [cond_by_plot[cn][condid]["prop"] for condid in accessible if cond_by_plot[cn][condid]["prop"] is not None and cond_by_plot[cn][condid]["prop"] > 0]
        prop_imputed = bool(accessible) and not props
        accessible_prop = min(max(sum(props), 0.0), 1.0) if props else (1.0 if accessible else 0.0)
        subplot_fraction = min(len(relevant), 4) / 4.0
        effort = accessible_prop * subplot_fraction
        legitimate = bool(plot["plot_status_cd"] == param["sampled_plot_statuscd"] and plot["designcd"] and plot["manual"] and accessible and relevant and plot["cell_50km"])
        plot.update({"accessible_condition_count": len(accessible), "accessible_forest_prop": accessible_prop, "accessible_prop_imputed": prop_imputed, "sampled_subplot_count": len(sampled), "relevant_sampled_subplot_count": len(relevant), "partial_sampling_flag": 0 < len(relevant) < 4, "effort_score": effort, "base_legitimate_opportunity_flag": legitimate})
        legitimate_count += int(legitimate)
    if coord_failures:
        raise LayoutAuthorityFailure(f"F0 public-coordinate failures: {coord_failures}")
    if legitimate_count != param["expected_legitimate_opportunities"]:
        raise LayoutAuthorityFailure(f"Legitimate opportunity count changed: {legitimate_count}")
    return plots


def layout_rows(plots: dict):
    for row in sorted(plots.values(), key=lambda item: (item["statecd"], item["fold"], item["plot_cn"])):
        yield {"plot_cn": row["plot_cn"], "state_fips": f"{row['statecd']:02d}", "state_abbr": row["state_abbr"], "component_evalid": row["evalid"], "panel": row["panel"], "fold": row["fold"], "latitude": f"{row['latitude']:.8f}", "longitude": f"{row['longitude']:.8f}", "x_m": f"{row['x_m']:.3f}", "y_m": f"{row['y_m']:.3f}", "cell_50km": row["cell_50km"], "plot_status_cd": row["plot_status_cd"], "accessible_condition_count": row["accessible_condition_count"], "accessible_forest_prop": f"{row['accessible_forest_prop']:.8f}", "accessible_prop_imputed": "YES" if row["accessible_prop_imputed"] else "NO", "sampled_subplot_count": row["sampled_subplot_count"], "relevant_sampled_subplot_count": row["relevant_sampled_subplot_count"], "partial_sampling_flag": "YES" if row["partial_sampling_flag"] else "NO", "partial_sampling_effort": f"{row['effort_score']:.8f}", "manual": row["manual"], "designcd": row["designcd"], "base_legitimate_opportunity_flag": "YES" if row["base_legitimate_opportunity_flag"] else "NO", "source": row["source"]}


def expit(values):
    values = np.clip(values, -30.0, 30.0)
    return 1.0 / (1.0 + np.exp(-values))


def logit(values, eps=1e-8):
    values = np.clip(values, eps, 1.0 - eps)
    return np.log(values / (1.0 - values))


def standardize(values: np.ndarray) -> np.ndarray:
    scale = float(np.std(values))
    return values * 0.0 if scale < 1e-12 else (values - float(np.mean(values))) / scale


def build_layout_arrays(plots: dict, param: dict):
    legit = [row for row in plots.values() if row["base_legitimate_opportunity_flag"]]
    cells = sorted({row["cell_50km"] for row in legit}, key=cell_tuple)
    cell_index = {cell: i for i, cell in enumerate(cells)}
    coords = np.array([cell_tuple(cell) for cell in cells], dtype=int)
    lookup = {tuple(value): i for i, value in enumerate(coords)}
    neighbors = []
    for ix, iy in coords:
        neighbors.append(np.asarray([lookup[(nx, ny)] for nx, ny in ((ix-1, iy),(ix+1, iy),(ix,iy-1),(ix,iy+1)) if (nx, ny) in lookup], dtype=int))
    components = []
    unseen = set(range(len(cells)))
    while unseen:
        seed = unseen.pop()
        comp = [seed]
        queue = deque([seed])
        while queue:
            node = queue.popleft()
            for nxt in neighbors[node]:
                nxt = int(nxt)
                if nxt in unseen:
                    unseen.remove(nxt)
                    comp.append(nxt)
                    queue.append(nxt)
        components.append(np.asarray(comp, dtype=int))
    main_component = max(components, key=len)

    manual_counts = Counter(row["manual"] for row in legit)
    design_counts = Counter(row["designcd"] for row in legit)
    manuals = [key for key, _ in sorted(manual_counts.items(), key=lambda item: (-item[1], item[0]))[:param["manual_top_k"]]]
    designs = [key for key, _ in sorted(design_counts.items(), key=lambda item: (-item[1], item[0]))[:param["design_top_k"]]]
    arrays = {}
    for fold in ("A", "B"):
        rows = [row for row in legit if row["fold"] == fold]
        pcell = np.asarray([cell_index[row["cell_50km"]] for row in rows], dtype=int)
        effort = np.asarray([row["effort_score"] for row in rows], dtype=float)
        partial = np.asarray([float(row["partial_sampling_flag"]) for row in rows], dtype=float)
        manual_truth = np.asarray([manual_truth_effect(row["manual"]) for row in rows], dtype=float)
        effort_z = standardize(np.log(np.clip(effort, 1e-4, 1.0)))
        n = np.bincount(pcell, minlength=len(cells)).astype(int)
        effort_sum = np.bincount(pcell, weights=effort, minlength=len(cells))
        partial_sum = np.bincount(pcell, weights=partial, minlength=len(cells))
        mean_effort = np.divide(effort_sum, n, out=np.zeros(len(cells)), where=n > 0)
        partial_fraction = np.divide(partial_sum, n, out=np.zeros(len(cells)), where=n > 0)
        manual_shares = []
        for group in manuals:
            values = np.asarray([float(row["manual"] == group) for row in rows])
            totals = np.bincount(pcell, weights=values, minlength=len(cells))
            manual_shares.append(np.divide(totals, n, out=np.zeros(len(cells)), where=n > 0))
        design_shares = []
        for group in designs:
            values = np.asarray([float(row["designcd"] == group) for row in rows])
            totals = np.bincount(pcell, weights=values, minlength=len(cells))
            design_shares.append(np.divide(totals, n, out=np.zeros(len(cells)), where=n > 0))
        features = np.column_stack([standardize(np.log(np.clip(mean_effort, 1e-4, 1.0))), standardize(partial_fraction)] + manual_shares + design_shares)
        arrays[fold] = {"rows": rows, "plot_cell": pcell, "plot_effort": effort, "plot_effort_z": effort_z, "plot_partial": partial, "plot_manual_truth": manual_truth, "N": n, "mean_effort": mean_effort, "partial_fraction": partial_fraction, "features": features}
    return {"cells": cells, "coords": coords, "metric_coords": coords.astype(float) * 50.0, "neighbors": neighbors, "main_component": main_component, "manual_groups": manuals, "design_groups": designs, "folds": arrays}


def smooth_on_graph(values: np.ndarray, neighbors, passes: int = 12) -> np.ndarray:
    result = values.astype(float).copy()
    for _ in range(passes):
        updated = result.copy()
        for node, adjacent in enumerate(neighbors):
            if len(adjacent):
                updated[node] = 0.55 * result[node] + 0.45 * float(np.mean(result[adjacent]))
        result = updated
    return result


def connected_support(rng, layout, target: int) -> np.ndarray:
    component = layout["main_component"]
    seed = int(rng.choice(component))
    coords = layout["coords"]
    angle = rng.uniform(0, math.pi)
    ratio = rng.uniform(0.55, 1.8)
    delta = coords - coords[seed]
    along = delta[:, 0] * math.cos(angle) + delta[:, 1] * math.sin(angle)
    across = -delta[:, 0] * math.sin(angle) + delta[:, 1] * math.cos(angle)
    noise = smooth_on_graph(rng.normal(size=len(coords)), layout["neighbors"], 10)
    cost = np.sqrt((along / ratio) ** 2 + (across * ratio) ** 2) - 0.8 * standardize(noise)
    allowed = set(map(int, component))
    chosen = {seed}
    frontier = {int(x) for x in layout["neighbors"][seed] if int(x) in allowed}
    while len(chosen) < target and frontier:
        nxt = min(frontier, key=lambda node: (cost[node], node))
        frontier.remove(nxt)
        chosen.add(nxt)
        frontier.update(int(x) for x in layout["neighbors"][nxt] if int(x) in allowed and int(x) not in chosen)
    support = np.zeros(len(coords), dtype=bool)
    support[list(chosen)] = True
    return support


def distance_to_boundary(support: np.ndarray, neighbors) -> np.ndarray:
    distance = np.zeros(len(support), dtype=float)
    queue = deque()
    for node in np.where(support)[0]:
        adjacent = neighbors[node]
        if len(adjacent) < 4 or any(not support[int(nxt)] for nxt in adjacent):
            distance[node] = 1.0
            queue.append(int(node))
    while queue:
        node = queue.popleft()
        for nxt in neighbors[node]:
            nxt = int(nxt)
            if support[nxt] and distance[nxt] == 0:
                distance[nxt] = distance[node] + 1.0
                queue.append(nxt)
    return distance


def openness(support: np.ndarray, neighbors, radius: int) -> np.ndarray:
    result = np.zeros(len(support), dtype=float)
    active = np.where(support)[0]
    for node in active:
        reached = {int(node)}
        frontier = {int(node)}
        for _ in range(radius):
            frontier = {int(nxt) for cur in frontier for nxt in neighbors[cur] if support[int(nxt)] and int(nxt) not in reached}
            reached.update(frontier)
        result[node] = len(reached)
    if len(active):
        result[active] = standardize(result[active])
    return result


def diffusion_returns(support: np.ndarray, neighbors) -> tuple[np.ndarray, np.ndarray]:
    active = np.where(support)[0]
    local = {node: idx for idx, node in enumerate(active)}
    if not len(active):
        return np.zeros(len(support)), np.zeros(len(support))
    transition = np.zeros((len(active), len(active)), dtype=float)
    for node in active:
        adjacent = [int(x) for x in neighbors[node] if support[int(x)]]
        if adjacent:
            transition[local[node], [local[x] for x in adjacent]] = 1.0 / len(adjacent)
        else:
            transition[local[node], local[node]] = 1.0
    current = np.eye(len(active))
    captures = {}
    for step in range(1, 9):
        current = current @ transition
        if step in (4, 8):
            captures[step] = np.diag(current).copy()
    result4, result8 = np.zeros(len(support)), np.zeros(len(support))
    result4[active], result8[active] = standardize(captures[4]), standardize(captures[8])
    return result4, result8


def stable_fields(support: np.ndarray, layout):
    distance = distance_to_boundary(support, layout["neighbors"])
    active = support
    if np.any(active):
        distance[active] = standardize(distance[active])
    open2 = openness(support, layout["neighbors"], 2)
    open4 = openness(support, layout["neighbors"], 4)
    heat4, heat8 = diffusion_returns(support, layout["neighbors"])
    return distance, open2, open4, heat4, heat8


def abundance_pair(support: np.ndarray, synthetic_id: int, layout, seed: int):
    distance, open2, open4, _, _ = stable_fields(support, layout)
    rng = np.random.default_rng(stable_seed(seed, synthetic_id, "abundance"))
    noise = smooth_on_graph(rng.normal(size=len(support)), layout["neighbors"], 14)
    strong_eta = 0.95 * distance[support] + 0.55 * open2[support] + 0.30 * open4[support] + 0.55 * standardize(noise[support])
    strong_values = np.exp(strong_eta - np.max(strong_eta))
    coords = layout["coords"].astype(float)
    angle = rng.uniform(0, math.pi)
    axis = coords[:, 0] * math.cos(angle) + coords[:, 1] * math.sin(angle)
    null_noise = smooth_on_graph(rng.normal(size=len(support)), layout["neighbors"], 18)
    null_score = standardize(axis[support]) + 0.75 * standardize(null_noise[support])
    null_values = np.empty_like(strong_values)
    null_values[np.argsort(null_score)] = np.sort(strong_values)

    def place(values):
        result = np.zeros(len(support), dtype=float)
        result[support] = values / values.sum()
        return result
    return place(strong_values), place(null_values)


def manual_truth_effect(value: str) -> float:
    raw = int.from_bytes(hashlib.sha256(value.encode("utf-8")).digest()[:4], "little") / (2**32 - 1)
    return 2.0 * raw - 1.0


def generate_synthetic(layout, param):
    nspecies, ncell = param["generated_species"], len(layout["cells"])
    rng = np.random.default_rng(param["collection_seed"])
    supports, abundances = {}, {}
    manifest = []
    for species_id in range(1, nspecies + 1):
        target = int(rng.integers(param["support_cells_min"], param["support_cells_max"] + 1))
        support = connected_support(np.random.default_rng(stable_seed(param["collection_seed"], species_id, "support")), layout, target)
        strong, paired_null = abundance_pair(support, species_id, layout, param["collection_seed"])
        supports[species_id] = support
        abundances[(species_id, "STRONG")] = strong
        abundances[(species_id, "PAIRED_NULL")] = paired_null
        for world in ("STRONG", "PAIRED_NULL"):
            for regime in sorted(param["observation_regimes"]):
                manifest.append({"synthetic_species_id": f"SYN{species_id:03d}", "world": world, "observation_regime": regime, "support_seed": stable_seed(param["collection_seed"], species_id, "support"), "observation_seed": stable_seed(param["collection_seed"], species_id, regime, "observation"), "abundance_seed": stable_seed(param["collection_seed"], species_id, "abundance"), "true_support_cells": int(support.sum()), "positive_abundance_histogram_shared_with_pair": "YES", "support_shared_with_pair": "YES", "generator_parameters_exposed_to_fit": "NO"})
    return supports, abundances, manifest


def generate_observations(layout, supports, abundances, param):
    ncell = len(layout["cells"])
    encounters = {}
    observed_abundance = {}
    plot_micro = {}
    for species_id, support in supports.items():
        for fold in ("A", "B"):
            data = layout["folds"][fold]
            rng_micro = np.random.default_rng(stable_seed(param["collection_seed"], species_id, fold, "count_micro"))
            plot_micro[(species_id, fold)] = np.exp(rng_micro.normal(0.0, param["abundance_plot_log_sd"], len(data["rows"])))
            for world in ("STRONG", "PAIRED_NULL"):
                abundance = abundances[(species_id, world)]
                mean = param["abundance_count_scale"] * abundance[data["plot_cell"]] * data["plot_effort"] * plot_micro[(species_id, fold)]
                rng_count = np.random.default_rng(stable_seed(param["collection_seed"], species_id, fold, world, "counts"))
                counts = rng_count.poisson(mean)
                observed_abundance[(species_id, world, fold)] = np.bincount(data["plot_cell"], weights=counts, minlength=len(layout["cells"])).astype(float)

        for regime, truth in param["observation_regimes"].items():
            rng_field = np.random.default_rng(stable_seed(param["collection_seed"], species_id, regime, "fields"))
            base_field = smooth_on_graph(rng_field.normal(size=ncell), layout["neighbors"], 12)
            base_field_z = standardize(base_field)
            availability_field = expit(smooth_on_graph(rng_field.normal(size=ncell), layout["neighbors"], 15))
            availability = truth["availability_low"] + (truth["availability_high"] - truth["availability_low"]) * availability_field
            species_shift = float(rng_field.normal(0.0, truth["species_intercept_sd"]))
            for fold in ("A", "B"):
                data = layout["folds"][fold]
                uniform = np.random.default_rng(stable_seed(param["collection_seed"], species_id, regime, fold, "uniform")).random(len(data["rows"]))
                manual_effect = data["plot_manual_truth"]
                for world in ("STRONG", "PAIRED_NULL"):
                    abundance = abundances[(species_id, world)]
                    active_values = np.log(abundance[support] + 1e-12)
                    standardized_abundance = np.zeros(ncell)
                    standardized_abundance[support] = standardize(active_values)
                    eta = truth["intercept"] + species_shift + truth["abundance_beta"] * standardized_abundance[data["plot_cell"]] + truth["effort_beta"] * data["plot_effort_z"] + truth["manual_beta"] * manual_effect + truth["cell_logit_sd"] * base_field_z[data["plot_cell"]]
                    probability = availability[data["plot_cell"]] * expit(eta)
                    probability[~support[data["plot_cell"]]] = 0.0
                    positives = uniform < probability
                    encounters[(species_id, world, regime, fold)] = np.bincount(data["plot_cell"], weights=positives.astype(int), minlength=ncell).astype(int)
    return encounters, observed_abundance


def beta_binomial_zero_probability(n: np.ndarray, q: np.ndarray, phi: float) -> np.ndarray:
    n = np.asarray(n, dtype=int)
    q = np.clip(np.asarray(q, dtype=float), 1e-5, 1.0 - 1e-5)
    alpha = q * phi
    beta = (1.0 - q) * phi
    result = np.ones(len(n), dtype=float)
    for step in range(int(n.max(initial=0))):
        mask = n > step
        result[mask] *= (beta[mask] + step) / (phi + step)
    return np.clip(result, 1e-12, 1.0)


def fit_m1_group(layout, encounter_group: dict[int, np.ndarray], fold: str, param: dict):
    base = layout["folds"][fold]
    n = base["N"].astype(int)
    features = base["features"]
    species_ids = sorted(encounter_group)
    nspecies = len(species_ids)
    positive_rows = []
    for sidx, species_id in enumerate(species_ids):
        k = encounter_group[species_id]
        for cell in np.where(k > 0)[0]:
            positive_rows.append((sidx, int(cell), int(k[cell]), int(n[cell])))
    if len(positive_rows) < max(20, nspecies):
        raise RuntimeError(f"Insufficient positive histories for M1: {len(positive_rows)}")
    p = 1 + features.shape[1] + nspecies
    x = np.zeros((len(positive_rows), p), dtype=float)
    response = np.zeros(len(positive_rows), dtype=float)
    weights = np.zeros(len(positive_rows), dtype=float)
    for r, (sidx, cell, k_value, n_value) in enumerate(positive_rows):
        x[r, 0] = 1.0
        x[r, 1:1+features.shape[1]] = features[cell]
        x[r, 1+features.shape[1]+sidx] = 1.0
        response[r] = logit((k_value + 0.5) / (n_value + 1.0))
        weights[r] = min(n_value, 20)
    penalty = np.zeros(p)
    penalty[1:1+features.shape[1]] = param["m1_ridge_covariates"]
    penalty[1+features.shape[1]:] = param["m1_ridge_species_offsets"]
    xtw = x.T * weights
    coefficients = np.linalg.solve(xtw @ x + np.diag(penalty), xtw @ response)

    q_by_species = {}
    residual_rho = []
    for sidx, species_id in enumerate(species_ids):
        eta = coefficients[0] + features @ coefficients[1:1+features.shape[1]] + coefficients[1+features.shape[1]+sidx]
        q = np.clip(expit(eta), 0.002, 0.85)
        q_by_species[species_id] = q
        k = encounter_group[species_id]
        mask = k > 0
        nmask = n[mask].astype(float)
        qmask = q[mask]
        denom = nmask * np.maximum(nmask - 1.0, 1.0) * qmask * (1.0 - qmask)
        raw = ((k[mask] - nmask*qmask)**2 - nmask*qmask*(1.0-qmask)) / np.maximum(denom, 1e-8)
        residual_rho.extend(raw[np.isfinite(raw)].tolist())
    rho = float(np.median(residual_rho)) if residual_rho else param["m1_rho_min"]
    rho = float(np.clip(rho, param["m1_rho_min"], param["m1_rho_max"]))
    phi = 1.0 / rho - 1.0

    posterior = {}
    diagnostics = {}
    prior_a, prior_b = param["m1_occupancy_beta_prior"]
    for species_id in species_ids:
        k = encounter_group[species_id]
        q = q_by_species[species_id]
        p0 = beta_binomial_zero_probability(n, q, phi)
        positive = k > 0
        informative_zero = (k == 0) & (n > 0)
        pi = float((positive.sum() + prior_a) / (np.sum(n > 0) + prior_a + prior_b))
        for iteration in range(param["m1_em_iterations"]):
            zero_post = pi * p0[informative_zero] / np.maximum(1.0 - pi + pi * p0[informative_zero], 1e-12)
            new_pi = float((positive.sum() + zero_post.sum() + prior_a) / (np.sum(n > 0) + prior_a + prior_b))
            if abs(new_pi - pi) < param["m1_em_tolerance"]:
                pi = new_pi
                break
            pi = new_pi
        values = np.full(len(n), pi, dtype=float)
        values[informative_zero] = pi * p0[informative_zero] / np.maximum(1.0 - pi + pi * p0[informative_zero], 1e-12)
        values[positive] = 1.0 - param["posterior_probability_clip"]
        posterior[species_id] = np.clip(values, param["posterior_probability_clip"], 1.0-param["posterior_probability_clip"])
        diagnostics[species_id] = {"pi": pi, "rho": rho, "phi": phi, "encounter_q_mean": float(np.mean(q[n > 0])), "positive_cells": int(positive.sum()), "em_iterations": iteration + 1}
    return posterior, q_by_species, diagnostics, coefficients


def spatial_regularize(probability: np.ndarray, positive: np.ndarray, layout, param: dict) -> np.ndarray:
    eta_base = logit(probability, param["posterior_probability_clip"])
    eta = eta_base.copy()
    lam = param["m2_laplacian_lambda"]
    for _ in range(param["m2_iterations"]):
        updated = eta.copy()
        for node, adjacent in enumerate(layout["neighbors"]):
            if len(adjacent):
                updated[node] = (eta_base[node] + lam * float(np.sum(eta[adjacent]))) / (1.0 + lam * len(adjacent))
        updated[positive] = logit(1.0-param["posterior_probability_clip"])
        eta = updated
    return np.clip(expit(eta), param["posterior_probability_clip"], 1.0-param["posterior_probability_clip"])


def support_metrics(probability, truth, target_mask, threshold, size_draws, draw_seed):
    p = probability[target_mask]
    y = truth[target_mask].astype(float)
    clipped = np.clip(p, 1e-6, 1-1e-6)
    predicted = p >= threshold
    tp = int(np.sum(predicted & (y == 1)))
    fp = int(np.sum(predicted & (y == 0)))
    fn = int(np.sum((~predicted) & (y == 1)))
    truth_size = int(y.sum())
    expected_size = float(p.sum())
    if size_draws > 1:
        rng = np.random.default_rng(draw_seed)
        sizes = rng.binomial(1, p, size=(size_draws, len(p))).sum(axis=1)
    else:
        sizes = np.asarray([predicted.sum()])
    return {"brier_score": float(np.mean((p-y)**2)), "log_loss": float(-np.mean(y*np.log(clipped)+(1-y)*np.log(1-clipped))), "expected_support_size": expected_size, "true_support_size": truth_size, "expected_support_size_bias": expected_size-truth_size, "expected_support_size_relative_bias": (expected_size-truth_size)/max(truth_size,1), "occupied_cell_recall": tp/max(tp+fn,1), "precision": tp/max(tp+fp,1), "iou_jaccard": tp/max(tp+fp+fn,1), "posterior_entropy_mean": float(np.mean(-(clipped*np.log(clipped)+(1-clipped)*np.log(1-clipped)))), "support_size_q05": float(np.quantile(sizes,0.05)), "support_size_q50": float(np.quantile(sizes,0.5)), "support_size_q95": float(np.quantile(sizes,0.95)), "truth_size_within_q05_q95": int(np.quantile(sizes,0.05) <= truth_size <= np.quantile(sizes,0.95)), "target_cells": int(target_mask.sum()), "predicted_cells_at_0_5": int(predicted.sum())}


def fit_all_support_models(layout, supports, encounters, param):
    posteriors, encounter_q, fit_diag = {}, {}, []
    support_rows = []
    calibration_accumulator = defaultdict(lambda: {"p": [], "y": []})
    for world in ("STRONG", "PAIRED_NULL"):
        for regime in sorted(param["observation_regimes"]):
            for source_fold, target_fold, orientation in (("A","B","AB"),("B","A","BA")):
                encounter_group = {species_id: encounters[(species_id,world,regime,source_fold)] for species_id in supports}
                m1, qvalues, diag, coefficients = fit_m1_group(layout, encounter_group, source_fold, param)
                fit_diag.append({"world": world, "observation_regime": regime, "orientation": orientation, "source_fold": source_fold, "positive_history_rows": sum(int((value>0).sum()) for value in encounter_group.values()), "m1_rho": next(iter(diag.values()))["rho"], "m1_phi": next(iter(diag.values()))["phi"], "coefficient_count": len(coefficients), "coefficient_l2_norm": float(np.linalg.norm(coefficients)), "manual_groups": ";".join(layout["manual_groups"]), "design_groups": ";".join(layout["design_groups"])})
                target_mask = layout["folds"][target_fold]["N"] > 0
                for species_id, truth in supports.items():
                    k = encounter_group[species_id]
                    model_probabilities = {
                        "M0": (k > 0).astype(float),
                        "M1": m1[species_id],
                        "M2": spatial_regularize(m1[species_id], k > 0, layout, param),
                    }
                    for model, probability in model_probabilities.items():
                        key = (model, world, regime, orientation, species_id)
                        posteriors[key] = probability
                        if model in {"M1", "M2"}:
                            encounter_q[key] = qvalues[species_id]
                        metrics = support_metrics(probability, truth, target_mask, param["binary_evaluation_threshold"], param["support_size_draws"] if model != "M0" else 1, stable_seed(param["collection_seed"], *key, "size"))
                        row = {"model": model, "world": world, "observation_regime": regime, "orientation": orientation, "source_fold": source_fold, "target_fold": target_fold, "synthetic_species_id": f"SYN{species_id:03d}", "occupancy_pi_estimate": diag[species_id]["pi"] if model != "M0" else "", "beta_binomial_rho": diag[species_id]["rho"] if model != "M0" else "", "encounter_q_mean": diag[species_id]["encounter_q_mean"] if model != "M0" else "", **metrics}
                        support_rows.append(row)
                        group = calibration_accumulator[(model,world,regime,orientation)]
                        group["p"].append(probability[target_mask])
                        group["y"].append(truth[target_mask].astype(int))
    calibration_rows = []
    for key, values in sorted(calibration_accumulator.items()):
        model, world, regime, orientation = key
        p = np.concatenate(values["p"])
        y = np.concatenate(values["y"])
        bins = np.minimum((p * param["calibration_bins"]).astype(int), param["calibration_bins"]-1)
        for index in range(param["calibration_bins"]):
            mask = bins == index
            calibration_rows.append({"model": model, "world": world, "observation_regime": regime, "orientation": orientation, "bin_index": index+1, "bin_lower": index/param["calibration_bins"], "bin_upper": (index+1)/param["calibration_bins"], "n_cell_predictions": int(mask.sum()), "mean_predicted_probability": float(np.mean(p[mask])) if np.any(mask) else "", "observed_occupancy_fraction": float(np.mean(y[mask])) if np.any(mask) else "", "absolute_calibration_gap": float(abs(np.mean(p[mask])-np.mean(y[mask]))) if np.any(mask) else ""})
    return posteriors, encounter_q, support_rows, calibration_rows, fit_diag


def support_draws(probability, hard_positive, count, seed):
    if count == 1:
        support = probability >= 0.5
        if not np.any(support):
            support[int(np.argmax(probability))] = True
        return [support]
    rng = np.random.default_rng(seed)
    result, seen = [], set()
    attempts = 0
    while len(result) < count and attempts < count * 8:
        support = rng.random(len(probability)) < probability
        support |= hard_positive
        if not np.any(support):
            support[int(np.argmax(probability))] = True
        key = np.packbits(support).tobytes()
        if key not in seen:
            seen.add(key)
            result.append(support)
        attempts += 1
    thresholds = np.linspace(0.2, 0.8, count)
    for threshold in thresholds:
        if len(result) >= count:
            break
        support = probability >= threshold
        support |= hard_positive
        if not np.any(support):
            support[int(np.argmax(probability))] = True
        key = np.packbits(support).tobytes()
        if key not in seen:
            seen.add(key)
            result.append(support)
    while len(result) < count:
        result.append(result[-1].copy())
    return result


def geometry_info(support, layout):
    active = np.where(support)[0]
    distance, open2, open4, heat4, heat8 = stable_fields(support, layout)
    d, o2, o4 = distance[active], open2[active], open4[active]
    matrix = np.column_stack([d,d*d,o2,o4,o2*o2,o4*o4,d*o2,d*o4,heat4[active],heat8[active]])
    return {"support": support, "active": active, "distance": distance[active], "matrix": matrix}


def projected_target(population, support):
    values = np.zeros(len(population), dtype=float)
    values[support] = population[support]
    total = values.sum()
    return None if total <= 0 else values / total


def baseline_from_info(info, gamma, ncell):
    values = np.exp(gamma * info["distance"])
    result = np.zeros(ncell, dtype=float)
    result[info["active"]] = values / values.sum()
    return result


def fit_allocation_models(ensemble_info, populations, train_ids, param, ncell):
    start, stop, step = param["world0_gamma_grid"]
    gamma_grid = np.arange(start, stop + 0.5*step, step)
    best_gamma, best_loglik = 0.0, -np.inf
    for gamma in gamma_grid:
        loglik = 0.0
        for species_id in train_ids:
            values = []
            for info in ensemble_info[species_id]:
                target = projected_target(populations[species_id], info["support"])
                if target is not None:
                    center = baseline_from_info(info, gamma, ncell)
                    active = info["active"]
                    values.append(float(np.sum(target[active]*np.log(center[active]+1e-15))))
            if values:
                loglik += float(np.mean(values))
        if loglik > best_loglik:
            best_loglik, best_gamma = loglik, float(gamma)
    matrices, responses, weights = [], [], []
    for species_id in train_ids:
        infos = ensemble_info[species_id]
        for info in infos:
            target = projected_target(populations[species_id], info["support"])
            if target is None:
                continue
            center = baseline_from_info(info, best_gamma, ncell)
            active = info["active"]
            response = np.log(target[active]+1e-15)-np.log(center[active]+1e-15)
            response -= response.mean()
            matrices.append(info["matrix"])
            responses.append(response)
            weights.append(np.full(len(response),1.0/(len(infos)*len(response))))
    matrix = np.vstack(matrices)
    response = np.concatenate(responses)
    weight = np.concatenate(weights)
    mean, scale = matrix.mean(axis=0), matrix.std(axis=0)
    scale[scale<1e-12] = 1.0
    standardized = (matrix-mean)/scale
    design = np.column_stack([np.ones(len(standardized)),standardized])
    weighted_design = design*np.sqrt(weight)[:,None]
    weighted_response = response*np.sqrt(weight)
    penalty = np.eye(design.shape[1])*param["geometry_ridge_alpha"]
    penalty[0,0]=0.0
    coefficients = np.linalg.solve(weighted_design.T@weighted_design+penalty,weighted_design.T@weighted_response)

    def predict(species_id, geometry):
        centers=[]
        for info in ensemble_info[species_id]:
            center=baseline_from_info(info,best_gamma,ncell)
            if geometry:
                residual=coefficients[0]+((info["matrix"]-mean)/scale)@coefficients[1:]
                values=np.exp(np.log(center[info["active"]]+1e-15)+residual)
                center=np.zeros(ncell,dtype=float)
                center[info["active"]]=values/values.sum()
            centers.append(center)
        return centers
    return best_gamma,predict


def conformal_quantile(scores, level):
    rank=min(max(int(math.ceil((len(scores)+1)*level)),1),len(scores))
    return float(np.sort(scores)[rank-1])


def build_spatial_signature_engine(layout,param):
    angles=np.linspace(0,np.pi,param["sliced_wasserstein_directions"],endpoint=False)
    directions=np.column_stack([np.cos(angles),np.sin(angles)])
    projections=layout["metric_coords"]@directions.T
    orders=np.argsort(projections,axis=0)
    levels=np.linspace(0,1,param["sliced_wasserstein_quantiles"]+2)[1:-1]
    def signature(distribution):
        result=np.empty((len(angles),len(levels)))
        for direction in range(len(angles)):
            order=orders[:,direction]
            cumulative=np.cumsum(distribution[order])
            values=projections[order,direction]
            result[direction]=np.interp(levels,cumulative,values,left=values[0],right=values[-1])
        return result
    return signature


def signature_distance(left,right):
    return float(np.mean(np.abs(left-right)))


def center_diameter(signatures):
    maximum=0.0
    for i in range(len(signatures)):
        for j in range(i+1,len(signatures)):
            maximum=max(maximum,signature_distance(signatures[i],signatures[j]))
    return maximum


def downstream_audit(layout,supports,abundances,encounters,observed_abundance,posteriors,param):
    signature=build_spatial_signature_engine(layout,param)
    species_ids=sorted(supports)
    rows=[]
    for model in ("M0","M1","M2"):
        draw_count=1 if model=="M0" else param["downstream_support_draws"]
        for world in ("STRONG","PAIRED_NULL"):
            for regime in sorted(param["observation_regimes"]):
                for source_fold,target_fold,orientation in (("A","B","AB"),("B","A","BA")):
                    ensemble_info={}
                    populations={}
                    truths={}
                    for species_id in species_ids:
                        probability=posteriors[(model,world,regime,orientation,species_id)]
                        hard=encounters[(species_id,world,regime,source_fold)]>0
                        draws=support_draws(probability,hard,draw_count,stable_seed(param["collection_seed"],model,world,regime,orientation,species_id,"downstream_draws"))
                        ensemble_info[species_id]=[geometry_info(draw,layout) for draw in draws]
                        population=observed_abundance[(species_id,world,target_fold)].copy()
                        if population.sum()<=0:
                            population=abundances[(species_id,world)].copy()
                        else:
                            population/=population.sum()
                        populations[species_id]=population
                        truths[species_id]=abundances[(species_id,world)]
                    for replicate,split_seed in enumerate(param["split_seeds"]):
                        permutation=np.random.default_rng(split_seed).permutation(species_ids)
                        n=len(permutation); ntrain=int(param["split_allocation"][0]*n); ncal=int(param["split_allocation"][1]*n)
                        train_ids=permutation[:ntrain].tolist(); calibration_ids=permutation[ntrain:ntrain+ncal].tolist(); test_ids=permutation[ntrain+ncal:].tolist()
                        gamma,predictor=fit_allocation_models(ensemble_info,populations,train_ids,param,len(layout["cells"]))
                        statistics={}
                        for geometry,label in ((False,"world0"),(True,"geometry")):
                            centers={species_id:predictor(species_id,geometry) for species_id in calibration_ids+test_ids}
                            center_signatures={species_id:[signature(center) for center in centers[species_id]] for species_id in centers}
                            observed_signatures={species_id:signature(populations[species_id]) for species_id in centers}
                            truth_signatures={species_id:signature(truths[species_id]) for species_id in test_ids}
                            scores=[min(signature_distance(candidate,observed_signatures[species_id]) for candidate in center_signatures[species_id]) for species_id in calibration_ids]
                            radius=conformal_quantile(np.asarray(scores),param["conformal_level"])
                            observed_covered=[]; truth_covered=[]; observed_errors=[]; truth_errors=[]; set_diameters=[]; dispersions=[]
                            for species_id in test_ids:
                                sigs=center_signatures[species_id]
                                observed_distance=min(signature_distance(candidate,observed_signatures[species_id]) for candidate in sigs)
                                truth_distance=min(signature_distance(candidate,truth_signatures[species_id]) for candidate in sigs)
                                point=np.mean(np.vstack(centers[species_id]),axis=0); point/=point.sum()
                                point_signature=signature(point)
                                observed_covered.append(observed_distance<=radius); truth_covered.append(truth_distance<=radius)
                                observed_errors.append(signature_distance(point_signature,observed_signatures[species_id])); truth_errors.append(signature_distance(point_signature,truth_signatures[species_id]))
                                dispersion=center_diameter(sigs); dispersions.append(dispersion); set_diameters.append(dispersion+2*radius)
                            statistics[label]={"radius":radius,"observed_coverage":float(np.mean(observed_covered)),"truth_coverage":float(np.mean(truth_covered)),"observed_error":float(np.mean(observed_errors)),"truth_error":float(np.mean(truth_errors)),"set_diameter":float(np.mean(set_diameters)),"support_dispersion":float(np.mean(dispersions))}
                        world0,geometry=statistics["world0"],statistics["geometry"]
                        rows.append({"model":model,"world":world,"observation_regime":regime,"orientation":orientation,"replicate":replicate+1,"split_seed":split_seed,"n_species":n,"n_train":len(train_ids),"n_calibration":len(calibration_ids),"n_test":len(test_ids),"world0_gamma":gamma,"latent_truth_geometry_gain_pct":100*(world0["truth_error"]-geometry["truth_error"])/max(world0["truth_error"],1e-12),"predictive_set_gain_pct":100*(world0["set_diameter"]-geometry["set_diameter"])/max(world0["set_diameter"],1e-12),"observed_map_error_gain_pct":100*(world0["observed_error"]-geometry["observed_error"])/max(world0["observed_error"],1e-12),"geometry_latent_truth_coverage":geometry["truth_coverage"],"geometry_observed_map_coverage":geometry["observed_coverage"],"world0_latent_truth_coverage":world0["truth_coverage"],"world0_observed_map_coverage":world0["observed_coverage"],"world0_set_diameter":world0["set_diameter"],"geometry_set_diameter":geometry["set_diameter"],"world0_latent_truth_error":world0["truth_error"],"geometry_latent_truth_error":geometry["truth_error"],"world0_support_dispersion":world0["support_dispersion"],"geometry_support_dispersion":geometry["support_dispersion"]})
    return rows


def write_posterior_summary(path, layout, supports, encounters, posteriors, encounter_q, param):
    fields=["model","world","observation_regime","orientation","synthetic_species_id","cell_50km","source_fold","target_fold","source_opportunities_N","source_positive_encounters_K","target_opportunities_N","latent_truth_occupied","posterior_occupancy_probability","binary_support_at_0_5","posterior_encounter_probability_diagnostic_only"]
    raw_handle=path.open("wb")
    compressed=gzip.GzipFile(filename="",mode="wb",fileobj=raw_handle,compresslevel=6,mtime=0)
    handle=io.TextIOWrapper(compressed,encoding="utf-8",newline="")
    try:
        writer=csv.DictWriter(handle,fieldnames=fields,lineterminator="\n")
        writer.writeheader()
        for key in sorted(posteriors):
            model,world,regime,orientation,species_id=key
            source_fold,target_fold=("A","B") if orientation=="AB" else ("B","A")
            source_n=layout["folds"][source_fold]["N"]
            target_n=layout["folds"][target_fold]["N"]
            k=encounters[(species_id,world,regime,source_fold)]
            truth=supports[species_id]
            probability=posteriors[key]
            q=encounter_q.get(key)
            for cell in np.where(target_n>0)[0]:
                writer.writerow({"model":model,"world":world,"observation_regime":regime,"orientation":orientation,"synthetic_species_id":f"SYN{species_id:03d}","cell_50km":layout["cells"][cell],"source_fold":source_fold,"target_fold":target_fold,"source_opportunities_N":int(source_n[cell]),"source_positive_encounters_K":int(k[cell]),"target_opportunities_N":int(target_n[cell]),"latent_truth_occupied":int(truth[cell]),"posterior_occupancy_probability":f"{probability[cell]:.8f}","binary_support_at_0_5":int(probability[cell]>=param["binary_evaluation_threshold"]),"posterior_encounter_probability_diagnostic_only":"" if q is None else f"{q[cell]:.8f}"})
    finally:
        handle.close()
        raw_handle.close()


def grouped(rows, keys):
    result=defaultdict(list)
    for row in rows:
        result[tuple(row[key] for key in keys)].append(row)
    return result


def median(values):
    return float(np.median(np.asarray(values,dtype=float)))


def mean(values):
    return float(np.mean(np.asarray(values,dtype=float)))


def model_comparison(support_rows, calibration_rows, leakage_rows):
    keys=("model","world","observation_regime","orientation")
    cal_lookup={}
    for key,rows in grouped(calibration_rows,keys).items():
        total=sum(int(row["n_cell_predictions"]) for row in rows)
        ece=sum(int(row["n_cell_predictions"])*float(row["absolute_calibration_gap"]) for row in rows if row["n_cell_predictions"] and row["absolute_calibration_gap"]!="")/max(total,1)
        cal_lookup[key]=ece
    leak_lookup=grouped(leakage_rows,keys)
    output=[]
    for key,rows in sorted(grouped(support_rows,keys).items()):
        leaks=leak_lookup[key]
        output.append({"model":key[0],"world":key[1],"observation_regime":key[2],"orientation":key[3],"synthetic_species_count":len(rows),"brier_mean":mean([r["brier_score"] for r in rows]),"log_loss_mean":mean([r["log_loss"] for r in rows]),"calibration_ece":cal_lookup[key],"expected_support_size_bias_median":median([r["expected_support_size_bias"] for r in rows]),"expected_support_size_relative_bias_median":median([r["expected_support_size_relative_bias"] for r in rows]),"occupied_cell_recall_median":median([r["occupied_cell_recall"] for r in rows]),"precision_median":median([r["precision"] for r in rows]),"iou_jaccard_median":median([r["iou_jaccard"] for r in rows]),"truth_size_interval_coverage":mean([r["truth_size_within_q05_q95"] for r in rows]),"latent_truth_geometry_gain_pct_median":median([r["latent_truth_geometry_gain_pct"] for r in leaks]),"predictive_set_gain_pct_median":median([r["predictive_set_gain_pct"] for r in leaks]),"geometry_latent_truth_coverage_median":median([r["geometry_latent_truth_coverage"] for r in leaks]),"geometry_observed_map_coverage_median":median([r["geometry_observed_map_coverage"] for r in leaks]),"scientific_pass_fail":"NOT_DEFINED","model_selected":"NO_MAINLINE_DECISION_REQUIRED"})
    return output


def model_specification_text(layout,param):
    return f"""# D10A model specifications v01

Frozen specification: `D10A_REAL_LAYOUT_NONORACLE_CALIBRATION_EXECUTION_FREEZE_v01.md`.

## Layout

The experiment uses {len(layout['cells']):,} fixed 50-km cells and the frozen D09C whole-panel AB assignment. Legal opportunity is a sampled plot with nonblank MANUAL and DESIGNCD, at least one accessible forest condition, and at least one sampled subplot linked to an accessible condition. Partial effort equals clipped accessible-forest condition proportion times the fraction of up to four relevant sampled subplots. The six mechanically selected MANUAL groups are `{'; '.join(layout['manual_groups'])}`. The three DESIGNCD groups are `{'; '.join(layout['design_groups'])}`.

## M0

Hard detection. A source-fold cell has occupancy probability one when K is positive and zero otherwise. It is a failure baseline and has degenerate uncertainty.

## M1

M1 is an empirical-Bayes zero-inflated beta-binomial encounter model. Conditional on latent occupancy, K among N legal plot opportunities follows a beta-binomial distribution with cell mean encounter probability and a shared overdispersion concentration. Cell mean encounter probability uses source-fold mean effort, partial-sampling fraction, six MANUAL shares, three DESIGNCD shares, and a partially pooled synthetic-species intercept. Coefficients are estimated from positive histories with ridge penalties {param['m1_ridge_covariates']} for observation covariates and {param['m1_ridge_species_offsets']} for species offsets. Residual beta-binomial rho is estimated from observed positive-history dispersion and clipped to [{param['m1_rho_min']}, {param['m1_rho_max']}]. Species occupancy prevalence is estimated by zero-mixture EM with Beta({param['m1_occupancy_beta_prior'][0]}, {param['m1_occupancy_beta_prior'][1]}) regularization. Generator parameters and opposite-fold abundance are absent from every fitted design matrix.

For K=0, posterior occupancy is `pi * P_BB(K=0|Z=1) / (1-pi + pi*P_BB(K=0|Z=1))`; K>0 is pinned occupied. Cells without source-fold opportunities retain the estimated species prevalence.

## M2

M2 applies a fixed four-neighbor graph-Laplacian regularizer to M1 logits. It solves the Jacobi fixed-point update with lambda {param['m2_laplacian_lambda']} for {param['m2_iterations']} iterations and pins positive-history cells. No environmental, atlas, external occurrence, or abundance input is used.

## Uncertainty and evaluation

The complete cell posterior is the uncertainty representation. Expected support size is the sum of posterior probabilities. Fixed-seed Bernoulli support draws provide 5th/50th/95th size summaries ({param['support_size_draws']} draws) and the downstream plausible-support ensemble ({param['downstream_support_draws']} draws). Binary diagnostics use the pre-frozen {param['binary_evaluation_threshold']} cut; calibration uses {param['calibration_bins']} equal-width bins.

## Downstream continuity audit

AB uses A support histories and B synthetic abundance; BA reverses them. World 0 and stable-intrinsic geometry receive identical support draws. Allocation fitting, stable intrinsic features, sliced-Wasserstein loss, and 90% split-conformal construction follow the historical E2c object, with fresh D10A species splits. Posterior encounter probability is diagnostic-only and is never an abundance predictor.

No model winner or scientific PASS/FAIL rule is defined in D10A.
"""


def result_note_text(layout,support_rows,comparison_rows,param,elapsed):
    legit=sum(len(layout["folds"][fold]["rows"]) for fold in ("A","B"))
    lines=["# D10A real-layout non-oracle observation calibration result","",f"Terminal status: `{param['terminal_status_success']}`","",f"The frozen 48-state F0 layout contains {legit:,} legitimate plot opportunities in {len(layout['cells']):,} fixed 50-km cells. The experiment generated {param['generated_species']} fresh synthetic species in STRONG and PAIRED_NULL worlds under O1/O2/O3 observation stress, evaluated M0/M1/M2 in AB and BA, and did not read or estimate any real species result.","","## Mainline reading rule","","All candidate rows are returned. D10A defines no scientific PASS/FAIL threshold and selects no model. Mainline must freeze any observation model using synthetic-only evidence before real support is read.","","## Compact comparison","","model | world | regime | direction | Brier | IoU | support bias | truth geometry gain | set gain | truth coverage","---|---|---|---|---:|---:|---:|---:|---:|---:"]
    for row in comparison_rows:
        lines.append(f"{row['model']} | {row['world']} | {row['observation_regime']} | {row['orientation']} | {row['brier_mean']:.4f} | {row['iou_jaccard_median']:.3f} | {row['expected_support_size_bias_median']:.1f} | {row['latent_truth_geometry_gain_pct_median']:.1f}% | {row['predictive_set_gain_pct_median']:.1f}% | {row['geometry_latent_truth_coverage_median']:.2f}")
    lines.extend(["","## Provenance limitation","","The exact E2c benchmark ZIP hash cited by the contract was not present locally. The available unpacked E2c methods were used only for scientific-object continuity; its generator-informed observation parameters were not used in M1/M2. This mismatch is recorded as non-blocking because the benchmark is not the F0 layout authority.","","STOP: no real support, abundance, cohort, or Q1 effect analysis was run."])
    return "\n".join(lines)


def run():
    start=time.time()
    param=json.loads(PARAM_PATH.read_text(encoding="utf-8"))
    OUT.mkdir(parents=True,exist_ok=True); QC.mkdir(parents=True,exist_ok=True)
    input_checks=validate_inputs(param)
    schema_rows=schema_gate()
    plots,partitions,mismatches=load_f0(param)
    plots=build_opportunities(plots,param)
    layout_path=OUT/"Q1_D10A_REAL_F0_OPPORTUNITY_LAYOUT_v01.csv"
    write_csv(layout_path,layout_rows(plots))
    layout=build_layout_arrays(plots,param)
    supports,abundances,manifest=generate_synthetic(layout,param)
    encounters,observed_abundance=generate_observations(layout,supports,abundances,param)
    posteriors,encounter_q,support_rows,calibration_rows,fit_diag=fit_all_support_models(layout,supports,encounters,param)
    leakage_rows=downstream_audit(layout,supports,abundances,encounters,observed_abundance,posteriors,param)
    comparison_rows=model_comparison(support_rows,calibration_rows,leakage_rows)

    write_csv(OUT/"Q1_D10A_SYNTHETIC_WORLD_MANIFEST_v01.csv",manifest)
    write_text(OUT/"Q1_D10A_MODEL_SPECIFICATIONS_v01.md",model_specification_text(layout,param))
    write_csv(OUT/"Q1_D10A_SUPPORT_CALIBRATION_RESULTS_v01.csv",support_rows)
    write_csv(OUT/"Q1_D10A_CALIBRATION_BIN_RESULTS_v01.csv",calibration_rows)
    write_csv(OUT/"Q1_D10A_LEAKAGE_AUDIT_RESULTS_v01.csv",leakage_rows)
    write_csv(OUT/"Q1_D10A_MODEL_COMPARISON_v01.csv",comparison_rows)
    write_posterior_summary(OUT/"Q1_D10A_POSTERIOR_OCCUPANCY_SUMMARY_v01.csv.gz",layout,supports,encounters,posteriors,encounter_q,param)
    write_csv(QC/"D10A_INPUT_IDENTITY_v01.csv",input_checks)
    write_csv(QC/"D10A_SQL_SCHEMA_ALLOWLIST_v01.csv",schema_rows)
    write_csv(QC/"D10A_F0_LINKAGE_MISMATCH_AUDIT_v01.csv",mismatches,fields=["state_abbr","assignment_cn","plot_cn","assignment_statecd","assignment_invyr","plot_statecd","plot_invyr","retained_by_plot_key"])
    write_csv(QC/"D10A_MODEL_FIT_DIAGNOSTICS_v01.csv",fit_diag)
    layout_summary={"f0_plot_visits":len(plots),"legitimate_opportunities":sum(row["base_legitimate_opportunity_flag"] for row in plots.values()),"cells_50km":len(layout["cells"]),"fold_A_opportunities":len(layout["folds"]["A"]["rows"]),"fold_B_opportunities":len(layout["folds"]["B"]["rows"]),"cells_with_A_opportunity":int(np.sum(layout["folds"]["A"]["N"]>0)),"cells_with_B_opportunity":int(np.sum(layout["folds"]["B"]["N"]>0)),"manual_groups":layout["manual_groups"],"design_groups":layout["design_groups"],"largest_graph_component_cells":len(layout["main_component"]),"synthetic_species":param["generated_species"],"support_result_rows":len(support_rows),"leakage_result_rows":len(leakage_rows),"terminal_status":param["terminal_status_success"]}
    write_json(QC/"D10A_BUILD_SUMMARY_v01.json",layout_summary)
    write_json(QC/"D10A_ENVIRONMENT_v01.json",{"python":sys.version,"platform":platform.platform(),"numpy":np.__version__,"sqlite":sqlite3.sqlite_version,"executable":sys.executable,"network_used":False,"working_directory":str(ROOT)})
    write_text(OUT/"Q1_D10A_RESULT_NOTE_v01.md",result_note_text(layout,support_rows,comparison_rows,param,time.time()-start))
    write_json(QC/"D10A_TERMINAL_STATUS_v01.json",{"task_id":param["task_id"],"terminal_status":param["terminal_status_success"],"scientific_pass_fail":"NOT_DEFINED","model_selected":False,"real_q1_run":False})
    write_text(QC/"D10A_IMPLEMENTATION_LOG_v01.md",f"# D10A implementation log\n\nFormal frozen run completed once. Input and schema gates passed. Layout, fresh synthetic calibration, all model candidates, and downstream AB/BA audit completed. No network access occurred.\n\nTerminal status: `{param['terminal_status_success']}`.\n")
    print(json.dumps(layout_summary,indent=2))


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--run",action="store_true",help="execute the frozen local calibration")
    args=parser.parse_args()
    if not args.run:
        parser.error("--run is required")
    try:
        run()
    except LayoutAuthorityFailure as exc:
        write_json(QC/"D10A_TERMINAL_STATUS_v01.json",{"task_id":"D10A_REAL_LAYOUT_NONORACLE_OBSERVATION_CALIBRATION_v01","terminal_status":"INPUT_BLOCKED_LAYOUT_AUTHORITY_FAILURE","detail":str(exc)})
        raise
    except Exception as exc:
        write_json(QC/"D10A_TERMINAL_STATUS_v01.json",{"task_id":"D10A_REAL_LAYOUT_NONORACLE_OBSERVATION_CALIBRATION_v01","terminal_status":"IMPLEMENTATION_BLOCKED","detail":repr(exc)})
        raise


if __name__=="__main__":
    main()
