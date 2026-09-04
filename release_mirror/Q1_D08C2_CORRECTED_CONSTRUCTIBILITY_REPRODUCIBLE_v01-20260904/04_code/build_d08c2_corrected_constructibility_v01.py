#!/usr/bin/env python3
"""Deterministic, local-only runner for D08C2 corrected constructibility v01.

The runner never opens a network connection. It verifies frozen local authorities,
executes the mandatory P0 schema gate before reading species identities or any
TREE.SPCD value, constructs the F0 plot-visit opportunity universe, and stops at
D1-D4 provisional constructibility.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import platform
import re
import sqlite3
import sys
import time
import zipfile
import zlib
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(r"C:\range_paper")
SRC = ROOT / "06_src" / "d08c2_corrected_constructibility_v01"
OUT = ROOT / "04_derived" / "d08c2_corrected_constructibility_v01"
QC = ROOT / "05_qc" / "d08c2_corrected_constructibility_v01"
TMP = ROOT / "99_tmp" / "d08c2_corrected_constructibility_v01"
CONTROL = ROOT / "00_control"
PARAM_PATH = SRC / "parameters_d08c2_corrected_constructibility_v01.json"
CONTRACT = CONTROL / "Q1_D08C2_CORRECTED_CONSTRUCTIBILITY_CONTRACT_v01.md"
FREEZE = CONTROL / "D08C2_CORRECTED_CONSTRUCTIBILITY_EXECUTION_FREEZE_v01.md"

RANGE_DIR = ROOT / "10_archive" / "range_gate0_v02_corrected"
RANGE_ZIP = RANGE_DIR / "Q1_RANGE_GATE0_V02_CORRECTED_GEOGRAPHIC_SEMANTICS_REPRODUCIBLE_v01.zip"
RANGE_PACKAGE = RANGE_DIR / "Q1_RANGE_GATE0_V02_CORRECTED_GEOGRAPHIC_SEMANTICS_REPRODUCIBLE_v01"
RANGE_SUMS = RANGE_PACKAGE / "SHA256SUMS.csv"
RANGE_CLASS = RANGE_PACKAGE / "outputs" / "Q1_RANGE_GATE0_V02_CORRECTED_SPECIES_CLASSIFICATION_v01.csv"
D08B1_ZIP = RANGE_PACKAGE / "inputs" / "Q1_TAXON_RANGE_D08B1_CORRECTED_REPRODUCIBLE_v02.zip"
D08B1_ROOT = "Q1_TAXON_RANGE_D08B1_CORRECTED_REPRODUCIBLE_v02/"

D09C_DIR = ROOT / "10_archive" / "d09c_t2_final_correction_v02"
D09C_ZIP = D09C_DIR / "Q1_D09C_T2_FINAL_CORRECTION_REPRODUCIBLE_v02.zip"
D09C_PACKAGE = D09C_DIR / "Q1_D09C_T2_FINAL_CORRECTION_REPRODUCIBLE_v02"
D09C_SUMS = D09C_PACKAGE / "SHA256SUMS.csv"
D09C_PARTITIONS = D09C_PACKAGE / "02_outputs" / "Q1_D09C_T2_FINAL_RULE_SELECTED_PARTITIONS_v02.csv"
D09C_TI = D09C_PACKAGE / "02_outputs" / "Q1_D09C_T2_FINAL_FOLD_SPECIFIC_TI_DESIGN_v02.csv"
D09C_PREDECESSOR = D09C_PACKAGE / "01_authoritative_inputs" / "predecessor_v01" / "Q1_D09C_T2_BOUNDED_COMPLETION_REPRODUCIBLE_v01.zip"
D09C_PRE_ROOT = "Q1_D09C_T2_BOUNDED_COMPLETION_REPRODUCIBLE_v01/"

NATIONAL_ZIP = ROOT / "02_raw" / "FIA" / "SQLite_FIADB_ENTIRE.zip"
NATIONAL_DB_CANDIDATES = (
    ROOT / "99_tmp" / "d08c2_preflight_observational_authority_v01" / "source_cache" / "SQLite_FIADB_ENTIRE.db",
    ROOT / "99_tmp" / "elig_v02" / "SQLite_FIADB_ENTIRE.db",
    TMP / "source_cache" / "SQLite_FIADB_ENTIRE.db",
)
OBS_ROOT = ROOT / "02_raw" / "fia_t2_2023_observational_gap_v01"
OBS_ZIPS = OBS_ROOT / "raw_table_zips"
OBS_MANIFEST = OBS_ROOT / "manifests" / "Q1_D08C2_CAORWA_OBS_RAW_ASSET_MANIFEST_v01.csv"

REQ = {
    "PLOT": ["CN", "STATECD", "INVYR", "P2PANEL", "PLOT_STATUS_CD", "PLOT_NONSAMPLE_REASN_CD", "DESIGNCD", "MANUAL", "MACRO_BREAKPOINT_DIA"],
    "COND": ["PLT_CN", "CONDID", "COND_STATUS_CD", "COND_NONSAMPLE_REASN_CD", "PROP_BASIS", "CONDPROP_UNADJ", "SUBPPROP_UNADJ", "MACRPROP_UNADJ"],
    "SUBPLOT": ["PLT_CN", "SUBP", "SUBP_STATUS_CD", "POINT_NONSAMPLE_REASN_CD", "SUBPCOND", "MACRCOND", "CONDLIST"],
    "TREE": ["CN", "PLT_CN", "STATECD", "INVYR", "CONDID", "SUBP", "SPCD", "STATUSCD", "DIA", "TPA_UNADJ"],
    "POP_EVAL": ["CN", "EVALID", "STATECD"],
    "POP_PLOT_STRATUM_ASSGN": ["CN", "STRATUM_CN", "PLT_CN", "STATECD", "INVYR", "EVALID"],
    "POP_STRATUM": ["CN", "ESTN_UNIT_CN", "EVALID"],
    "POP_ESTN_UNIT": ["CN", "EVALID"],
}

STATUS_ELIGIBLE = "D08C2_ELIGIBLE_FOR_OBSERVATION_AND_MEASUREMENT_GATE"
STATUS_ONE = "ONE_DIRECTION_ONLY_DIAGNOSTIC"
TASK_PASS = "PASS_READY_FOR_MAINLINE_OBSERVATION_GATE_AUDIT"


class ContractStop(RuntimeError):
    def __init__(self, status: str, detail: str):
        super().__init__(f"{status}: {detail}")
        self.status = status
        self.detail = detail


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path, chunk: int = 8 * 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def crc32_file(path: Path, chunk: int = 16 * 1024 * 1024) -> int:
    value = 0
    with path.open("rb") as f:
        for block in iter(lambda: f.read(chunk), b""):
            value = zlib.crc32(block, value)
    return value & 0xFFFFFFFF


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def read_csv_bytes(data: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(data.decode("utf-8-sig"), newline="")))


def write_csv(path: Path, rows: list[dict], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fields is None:
        fields, seen = [], set()
        for row in rows:
            for key in row:
                if key not in seen:
                    fields.append(key)
                    seen.add(key)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def as_int(value, default=None):
    if value is None or str(value).strip() == "":
        return default
    return int(float(value))


def as_float(value, default=None):
    if value is None or str(value).strip() == "":
        return default
    return float(value)


def text(value) -> str:
    return "" if value is None else str(value).strip()


def true_value(value) -> bool:
    return text(value).upper() in {"1", "TRUE", "YES", "Y"}


def qc_row(check_id, stage, scope, expected, observed, ok, blocking="YES", details=""):
    return {
        "check_id": check_id,
        "stage": stage,
        "scope": scope,
        "expected": expected,
        "observed": observed,
        "status": "PASS" if ok else "FAIL",
        "blocking": blocking,
        "details": details,
    }


def rows_by_path(path: Path) -> dict[str, dict[str, str]]:
    return {row["relative_path"]: row for row in read_csv(path)}


def zip_csv_header(path: Path, member: str) -> list[str]:
    with zipfile.ZipFile(path) as zf:
        if zf.namelist() != [member]:
            raise ContractStop("INPUT_BLOCKED_AUTHORITY_HASH_FAILURE", f"Unexpected ZIP members in {path}")
        with zf.open(member) as raw, io.TextIOWrapper(raw, encoding="utf-8-sig", newline="") as f:
            return next(csv.reader(f))


def iter_zip_csv(path: Path, member: str):
    with zipfile.ZipFile(path) as zf:
        if zf.namelist() != [member]:
            raise ContractStop("INPUT_BLOCKED_AUTHORITY_HASH_FAILURE", f"Unexpected ZIP members in {path}")
        with zf.open(member) as raw, io.TextIOWrapper(raw, encoding="utf-8-sig", newline="") as f:
            yield from csv.DictReader(f)


def d08b1_member(zf: zipfile.ZipFile, relative: str) -> bytes:
    return zf.read(D08B1_ROOT + relative)


def nested_design_zip(pre: zipfile.ZipFile, state: str, table: str) -> bytes:
    return pre.read(D09C_PRE_ROOT + f"01_authoritative_inputs/ca_or_wa_raw_design_zips/{state}_{table}.zip")


def nested_csv_rows(pre: zipfile.ZipFile, state: str, table: str) -> list[dict[str, str]]:
    data = nested_design_zip(pre, state, table)
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        expected = f"{state}_{table}.csv"
        if zf.namelist() != [expected]:
            raise ContractStop("INPUT_BLOCKED_AUTHORITY_HASH_FAILURE", f"Unexpected nested members for {state}_{table}")
        return read_csv_bytes(zf.read(expected))


def nested_csv_header(pre: zipfile.ZipFile, state: str, table: str) -> list[str]:
    data = nested_design_zip(pre, state, table)
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        expected = f"{state}_{table}.csv"
        if zf.namelist() != [expected]:
            raise ContractStop("INPUT_BLOCKED_AUTHORITY_HASH_FAILURE", f"Unexpected nested members for {state}_{table}")
        with zf.open(expected) as raw, io.TextIOWrapper(raw, encoding="utf-8-sig", newline="") as f:
            return next(csv.reader(f))


def parse_panels(value: str) -> set[int]:
    return {int(x) for x in text(value).split("-") if x}


def condition_tokens(value: str) -> set[int]:
    return {int(x) for x in re.findall(r"\d+", text(value))}


def sqlite_ro(path: Path) -> sqlite3.Connection:
    uri = "file:" + path.as_posix() + "?mode=ro&immutable=1"
    con = sqlite3.connect(uri, uri=True)
    con.row_factory = sqlite3.Row
    return con


def locate_verified_db(params: dict, raw_info: zipfile.ZipInfo, qc: list[dict]) -> Path:
    expected_size = int(params["national_db_expected_bytes"])
    for candidate in NATIONAL_DB_CANDIDATES:
        if not candidate.exists() or candidate.stat().st_size != expected_size:
            continue
        observed_crc = crc32_file(candidate)
        ok = observed_crc == raw_info.CRC
        qc.append(qc_row("AUTH_NATIONAL_DB_MEMBER_CRC32", "AUTHORITY", str(candidate), f"{raw_info.CRC:08x}", f"{observed_crc:08x}", ok))
        if ok:
            return candidate
    target = NATIONAL_DB_CANDIDATES[-1]
    target.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(NATIONAL_ZIP) as zf, zf.open(raw_info) as src, target.open("wb") as dst:
        while True:
            block = src.read(16 * 1024 * 1024)
            if not block:
                break
            dst.write(block)
    observed_crc = crc32_file(target)
    ok = target.stat().st_size == expected_size and observed_crc == raw_info.CRC
    qc.append(qc_row("AUTH_NATIONAL_DB_LOCAL_EXTRACTION", "AUTHORITY", str(target), f"bytes={expected_size};crc32={raw_info.CRC:08x}", f"bytes={target.stat().st_size};crc32={observed_crc:08x}", ok))
    if not ok:
        raise ContractStop("INPUT_BLOCKED_AUTHORITY_HASH_FAILURE", "Local extraction does not match frozen national ZIP member")
    return target


def verify_authorities_and_p0(params: dict):
    """Returns (db_path, qc_rows, input_records). Does not read species values."""
    qc: list[dict] = []
    inputs: list[dict] = []

    expected_files = [CONTRACT, FREEZE, PARAM_PATH, RANGE_ZIP, RANGE_SUMS, RANGE_CLASS, D08B1_ZIP, D09C_ZIP, D09C_SUMS, D09C_PARTITIONS, D09C_TI, D09C_PREDECESSOR, NATIONAL_ZIP, OBS_MANIFEST]
    missing = [str(p) for p in expected_files if not p.exists()]
    qc.append(qc_row("AUTH_REQUIRED_LOCAL_FILES", "AUTHORITY", "all frozen local paths", "0 missing", len(missing), not missing, details=";".join(missing)))
    if missing:
        raise ContractStop("INPUT_BLOCKED_AUTHORITY_HASH_FAILURE", f"Missing local inputs: {missing}")

    identities = [
        ("AUTH_CONTRACT_SHA256", CONTRACT, params["contract_expected_sha256"]),
        ("AUTH_RANGE_GATE_ZIP_SHA256", RANGE_ZIP, params["range_gate_zip_expected_sha256"]),
        ("AUTH_D09C_ZIP_SHA256", D09C_ZIP, params["d09c_zip_expected_sha256"]),
        ("AUTH_NATIONAL_ZIP_SHA256", NATIONAL_ZIP, params["national_zip_expected_sha256"]),
    ]
    for check_id, path, expected in identities:
        observed = sha256_file(path)
        ok = observed == expected
        qc.append(qc_row(check_id, "AUTHORITY", str(path), expected, observed, ok))
        inputs.append({"role": check_id, "path": str(path), "size_bytes": path.stat().st_size, "sha256": observed, "status": "PASS" if ok else "FAIL"})
        if not ok:
            raise ContractStop("INPUT_BLOCKED_AUTHORITY_HASH_FAILURE", f"Hash mismatch: {path}")
    bytes_ok = NATIONAL_ZIP.stat().st_size == int(params["national_zip_expected_bytes"])
    qc.append(qc_row("AUTH_NATIONAL_ZIP_BYTES", "AUTHORITY", str(NATIONAL_ZIP), params["national_zip_expected_bytes"], NATIONAL_ZIP.stat().st_size, bytes_ok))
    if not bytes_ok:
        raise ContractStop("INPUT_BLOCKED_AUTHORITY_HASH_FAILURE", "National ZIP byte count mismatch")

    with zipfile.ZipFile(NATIONAL_ZIP) as zf:
        infos = zf.infolist()
        ok = len(infos) == 1 and infos[0].filename == params["national_db_member"] and infos[0].file_size == int(params["national_db_expected_bytes"])
        qc.append(qc_row("AUTH_NATIONAL_ZIP_MEMBER", "P0", str(NATIONAL_ZIP), f"one {params['national_db_member']} member; bytes={params['national_db_expected_bytes']}", f"members={len(infos)};name={infos[0].filename if infos else ''};bytes={infos[0].file_size if infos else ''}", ok))
        if not ok:
            raise ContractStop("INPUT_BLOCKED_AUTHORITY_HASH_FAILURE", "National ZIP member identity failure")
        raw_info = infos[0]
    db_path = locate_verified_db(params, raw_info, qc)

    range_sums = rows_by_path(RANGE_SUMS)
    for rel, path in [
        ("outputs/Q1_RANGE_GATE0_V02_CORRECTED_SPECIES_CLASSIFICATION_v01.csv", RANGE_CLASS),
        ("inputs/Q1_TAXON_RANGE_D08B1_CORRECTED_REPRODUCIBLE_v02.zip", D08B1_ZIP),
    ]:
        expected = range_sums[rel]["sha256"]
        observed = sha256_file(path)
        ok = expected == observed
        qc.append(qc_row("AUTH_RANGE_MEMBER_SHA256", "AUTHORITY", rel, expected, observed, ok))
        inputs.append({"role": "RANGE_GATE_MEMBER", "path": str(path), "size_bytes": path.stat().st_size, "sha256": observed, "status": "PASS" if ok else "FAIL"})
        if not ok:
            raise ContractStop("INPUT_BLOCKED_AUTHORITY_HASH_FAILURE", f"Range Gate member mismatch: {rel}")

    d09c_sums = rows_by_path(D09C_SUMS)
    for rel, path in [
        ("02_outputs/Q1_D09C_T2_FINAL_RULE_SELECTED_PARTITIONS_v02.csv", D09C_PARTITIONS),
        ("02_outputs/Q1_D09C_T2_FINAL_FOLD_SPECIFIC_TI_DESIGN_v02.csv", D09C_TI),
        ("01_authoritative_inputs/predecessor_v01/Q1_D09C_T2_BOUNDED_COMPLETION_REPRODUCIBLE_v01.zip", D09C_PREDECESSOR),
    ]:
        expected = d09c_sums[rel]["sha256"]
        observed = sha256_file(path)
        ok = expected == observed
        qc.append(qc_row("AUTH_D09C_MEMBER_SHA256", "AUTHORITY", rel, expected, observed, ok))
        inputs.append({"role": "D09C_MEMBER", "path": str(path), "size_bytes": path.stat().st_size, "sha256": observed, "status": "PASS" if ok else "FAIL"})
        if not ok:
            raise ContractStop("INPUT_BLOCKED_AUTHORITY_HASH_FAILURE", f"D09C member mismatch: {rel}")

    obs_manifest = read_csv(OBS_MANIFEST)
    expected_obs = {(row["STATE"], row["TABLE"]): row for row in obs_manifest}
    for state in ("CA", "OR", "WA"):
        for table in ("TREE", "COND", "SUBPLOT"):
            row = expected_obs[(state, table)]
            path = OBS_ZIPS / f"{state}_{table}.zip"
            observed = sha256_file(path)
            size_ok = path.stat().st_size == int(row["BYTES"])
            hash_ok = observed == row["SHA256"]
            qc.append(qc_row("AUTH_OBS_OVERRIDE", "AUTHORITY", f"{state}_{table}", f"bytes={row['BYTES']};sha256={row['SHA256']}", f"bytes={path.stat().st_size};sha256={observed}", size_ok and hash_ok))
            inputs.append({"role": "CA_OR_WA_OBSERVATIONAL_OVERRIDE", "path": str(path), "size_bytes": path.stat().st_size, "sha256": observed, "status": "PASS" if size_ok and hash_ok else "FAIL"})
            if not (size_ok and hash_ok):
                raise ContractStop("INPUT_BLOCKED_AUTHORITY_HASH_FAILURE", f"Override identity failure: {state}_{table}")

    con = sqlite_ro(db_path)
    try:
        for table, fields in REQ.items():
            observed = {row[1] for row in con.execute(f"PRAGMA table_info({table})")}
            missing_fields = [field for field in fields if field not in observed]
            qc.append(qc_row("P0_NATIONAL_SCHEMA", "P0", table, ";".join(fields), ";".join(missing_fields) if missing_fields else "ALL_PRESENT", not missing_fields))
            if missing_fields:
                raise ContractStop("INPUT_BLOCKED_REQUIRED_SCHEMA_FIELD_MISSING", f"{table}: {missing_fields}")
    finally:
        con.close()

    with zipfile.ZipFile(D09C_PREDECESSOR) as pre:
        manifest_data = pre.read(D09C_PRE_ROOT + "01_authoritative_inputs/ca_or_wa_raw_design_manifests/RAW_ASSET_MANIFEST_v01.csv")
        design_manifest = read_csv_bytes(manifest_data)
        expected_design = {(row["STATE_ABBR"], row["TABLE"]): row for row in design_manifest}
        for state in ("CA", "OR", "WA"):
            for table in ("PLOT", "POP_EVAL", "POP_PLOT_STRATUM_ASSGN", "POP_STRATUM", "POP_ESTN_UNIT"):
                data = nested_design_zip(pre, state, table)
                row = expected_design[(state, table)]
                hash_ok = sha256_bytes(data) == row["SHA256"] and len(data) == int(row["BYTES"])
                header = set(nested_csv_header(pre, state, table))
                missing_fields = [field for field in REQ[table] if field not in header]
                ok = hash_ok and not missing_fields
                qc.append(qc_row("P0_OVERRIDE_DESIGN_SCHEMA", "P0", f"{state}_{table}", "frozen hash and all required fields", f"hash_ok={hash_ok};missing={';'.join(missing_fields)}", ok))
                if not ok:
                    status = "INPUT_BLOCKED_REQUIRED_SCHEMA_FIELD_MISSING" if missing_fields else "INPUT_BLOCKED_AUTHORITY_HASH_FAILURE"
                    raise ContractStop(status, f"{state}_{table} P0 failure")
        for state in ("CA", "OR", "WA"):
            for table in ("TREE", "COND", "SUBPLOT"):
                header = set(zip_csv_header(OBS_ZIPS / f"{state}_{table}.zip", f"{state}_{table}.csv"))
                missing_fields = [field for field in REQ[table] if field not in header]
                qc.append(qc_row("P0_OVERRIDE_OBS_SCHEMA", "P0", f"{state}_{table}", ";".join(REQ[table]), ";".join(missing_fields) if missing_fields else "ALL_PRESENT", not missing_fields))
                if missing_fields:
                    raise ContractStop("INPUT_BLOCKED_REQUIRED_SCHEMA_FIELD_MISSING", f"{state}_{table}: {missing_fields}")

    qc.append(qc_row("P0_SPECIES_BLIND_ORDER", "P0", "execution order", "schema gate before species identity/TREE.SPCD", "P0 completed before authority species rows or TREE.SPCD were read", True))
    return db_path, qc, inputs


def load_scientific_authorities(db_path: Path, params: dict, qc: list[dict]):
    classification = read_csv(RANGE_CLASS)
    starting = [row for row in classification if row["range_gate0_v02_class"] == params["range_gate_class"]]
    starting_ids = {row["analysis_species_id"] for row in starting}
    identity_ok = len(starting) == params["expected_starting_species"] and len(starting_ids) == params["expected_starting_species"]
    qc.append(qc_row("STARTING_UNIVERSE_IDENTITY", "D1", "Range Gate v02 PASS_COARSE", params["expected_starting_species"], f"rows={len(starting)};unique_ids={len(starting_ids)}", identity_ok))
    if not identity_ok:
        raise ContractStop("INPUT_BLOCKED_STARTING_UNIVERSE_IDENTITY_FAILURE", f"rows={len(starting)} unique={len(starting_ids)}")

    with zipfile.ZipFile(D08B1_ZIP) as zf:
        sums = {row["relative_path"]: row for row in read_csv_bytes(d08b1_member(zf, "SHA256SUMS.csv"))}
        members = {
            "master": "outputs/Q1_ANALYSIS_SPECIES_MASTER_v02.csv",
            "code_map": "outputs/Q1_FIA_CODE_TO_ANALYSIS_SPECIES_v02.csv",
            "global": "outputs/Q1_GLOBAL_RANGE_FLAGS_v02.csv",
            "distribution": "outputs/Q1_WCVP_NATIVE_DISTRIBUTION_LONG_v02.csv",
        }
        raw = {}
        for role, rel in members.items():
            data = d08b1_member(zf, rel)
            expected = sums[rel]["sha256"]
            observed = sha256_bytes(data)
            ok = observed == expected and len(data) == int(sums[rel]["bytes"])
            qc.append(qc_row("AUTH_D08B1_MEMBER_SHA256", "AUTHORITY", rel, expected, observed, ok))
            if not ok:
                raise ContractStop("INPUT_BLOCKED_AUTHORITY_HASH_FAILURE", f"D08B1 member mismatch: {rel}")
            raw[role] = read_csv_bytes(data)

    master = {row["analysis_species_id"]: row for row in raw["master"]}
    global_flags = {row["analysis_species_id"]: row for row in raw["global"]}
    code_rows = raw["code_map"]
    code_map = {as_int(row["fia_species_code"]): row for row in code_rows}
    authority_ok = len(code_rows) == 396 and len(code_map) == 396 and starting_ids <= set(master) and starting_ids <= set(global_flags)
    qc.append(qc_row("D08B1_AUTHORITY_CLOSURE", "D1", "frozen taxonomy/native authority", "396 unique raw codes and all 101 species in master/global flags", f"code_rows={len(code_rows)};unique_codes={len(code_map)};master={len(master)};global={len(global_flags)}", authority_ok))
    if not authority_ok:
        raise ContractStop("INPUT_BLOCKED_AUTHORITY_HASH_FAILURE", "Frozen D08B1 authority closure failure")

    contributors = defaultdict(list)
    for row in code_rows:
        sid = row["analysis_species_id"]
        if sid:
            contributors[sid].append(row)
    contributor_ok = all(contributors[sid] for sid in starting_ids)
    qc.append(qc_row("D1_STARTING_SPECIES_HAVE_FROZEN_CONTRIBUTORS", "D1", "101 accepted species", 101, sum(bool(contributors[sid]) for sid in starting_ids), contributor_ok))

    con = sqlite_ro(db_path)
    try:
        state_rows = con.execute("SELECT DISTINCT STATECD, STATEAB, STATENM FROM SURVEY ORDER BY STATECD").fetchall()
    finally:
        con.close()
    state_map = {int(row[0]): {"statecd": int(row[0]), "abbr": text(row[1]), "name": text(row[2])} for row in state_rows}
    conus = set(params["conus_state_codes"])
    if not conus <= set(state_map):
        raise ContractStop("INPUT_BLOCKED_F0_LINKAGE_FAILURE", f"State metadata missing: {sorted(conus-set(state_map))}")

    areas_by_name = defaultdict(set)
    rows_by_species_area = defaultdict(list)
    for row in raw["distribution"]:
        areas_by_name[row["area"]].add(row["area_code_l3"])
        rows_by_species_area[(row["analysis_species_id"], row["area_code_l3"])].append(row)
    area_by_state = {}
    state_crosswalk = []
    for code in sorted(conus):
        state = state_map[code]
        if code == 44:
            alias = params["authorized_state_aliases"][0]
            valid = state["abbr"] == alias["fia_state_ab"] and state["name"] == alias["fia_state_name"] and alias["wcvp_area_code_l3"] in areas_by_name[alias["wcvp_area_name"]]
            if not valid:
                raise ContractStop("INPUT_BLOCKED_F0_LINKAGE_FAILURE", "Authorized RI/RHO alias failed exact frozen identity")
            area_code, area_name, mapping_type = alias["wcvp_area_code_l3"], alias["wcvp_area_name"], "AUTHORIZED_EXPLICIT_ALIAS"
        else:
            matches = sorted(areas_by_name.get(state["name"], set()))
            if len(matches) != 1:
                raise ContractStop("INPUT_BLOCKED_F0_LINKAGE_FAILURE", f"Additional non-exact state correspondence: {code} {state['name']} {matches}")
            area_code, area_name, mapping_type = matches[0], state["name"], "EXACT_FULL_STATE_NAME"
        area_by_state[code] = area_code
        state_crosswalk.append({
            "fia_state_code": code,
            "fia_state_ab": state["abbr"],
            "fia_state_name": state["name"],
            "wcvp_area_code_l3": area_code,
            "wcvp_area_name": area_name,
            "mapping_type": mapping_type,
            "fuzzy_matching_used": 0,
            "status": "PASS",
        })
    qc.append(qc_row("NATIVE_STATE_CROSSWALK", "D2", "48 CONUS states", "47 exact + 1 authorized RI/RHO alias", f"exact={sum(r['mapping_type']=='EXACT_FULL_STATE_NAME' for r in state_crosswalk)};alias={sum(r['mapping_type']=='AUTHORIZED_EXPLICIT_ALIAS' for r in state_crosswalk)}", len(state_crosswalk) == 48))

    native_states = defaultdict(set)
    evidence_detail = {}
    conflicts = []
    for sid in starting_ids:
        for statecd in sorted(conus):
            rows = rows_by_species_area.get((sid, area_by_state[statecd]), [])
            native = [row for row in rows if row["introduced"] == "0" and row["extinct"] == "0" and row["location_doubtful"] == "0" and true_value(row.get("confirmed_current_native_flag", "1"))]
            introduced = [row for row in rows if row["introduced"] == "1"]
            if native and introduced:
                conflicts.append((sid, statecd))
            if native:
                native_states[sid].add(statecd)
            evidence_detail[(sid, statecd)] = {
                "wcvp_rows": len(rows),
                "native_rows": len(native),
                "introduced_rows": len(introduced),
                "extinct_rows": sum(row["introduced"] == "0" and row["extinct"] == "1" for row in rows),
                "doubtful_rows": sum(row["introduced"] == "0" and row["location_doubtful"] == "1" for row in rows),
            }
    if conflicts:
        raise ContractStop("INPUT_BLOCKED_F0_LINKAGE_FAILURE", f"Native/introduced conflicts: {conflicts[:10]}")
    native_ok = all(native_states[sid] for sid in starting_ids)
    qc.append(qc_row("OPERATIONAL_NATIVE_DOMAIN_CLOSURE", "D2", "101 species", "at least one confirmed-native CONUS state each", sum(bool(native_states[sid]) for sid in starting_ids), native_ok))
    if not native_ok:
        raise ContractStop("INPUT_BLOCKED_F0_LINKAGE_FAILURE", "Starting species without a confirmed-native operational state domain")
    return starting, starting_ids, master, global_flags, code_rows, code_map, contributors, state_map, state_crosswalk, native_states, evidence_detail


def load_f0_frame(db_path: Path, params: dict, qc: list[dict]):
    partitions = read_csv(D09C_PARTITIONS)
    part_by_state = {as_int(row["state_fips"]): row for row in partitions}
    conus = set(params["conus_state_codes"])
    partition_ok = len(partitions) == 48 and set(part_by_state) == conus
    qc.append(qc_row("F0_PARTITION_IDENTITY", "F0", "D09C final partitions", "48 states", f"rows={len(partitions)};states={len(part_by_state)}", partition_ok))
    if not partition_ok:
        raise ContractStop("INPUT_BLOCKED_F0_LINKAGE_FAILURE", "D09C partition identity failure")
    for statecd, row in part_by_state.items():
        a, b = parse_panels(row["final_A_panels"]), parse_panels(row["final_B_panels"])
        if len(a) != 2 or len(b) != 3 or a & b or a | b != set(params["panels"]):
            raise ContractStop("INPUT_BLOCKED_F0_LINKAGE_FAILURE", f"Invalid frozen A/B panels for {statecd}")

    plots = {}
    mismatches = []
    national_states = sorted(conus - set(params["override_state_codes"]))
    evalid_to_state = {as_int(part_by_state[state]["component_evalid"]): state for state in national_states}
    placeholders = ",".join("?" for _ in evalid_to_state)
    sql = f"""
        SELECT a.CN AS assignment_cn,a.STRATUM_CN,a.PLT_CN,a.STATECD AS assignment_statecd,
               a.INVYR AS assignment_invyr,a.EVALID,p.STATECD AS plot_statecd,p.INVYR AS plot_invyr,
               p.P2PANEL,p.PLOT_STATUS_CD,p.PLOT_NONSAMPLE_REASN_CD,p.DESIGNCD,p.MANUAL,
               p.MACRO_BREAKPOINT_DIA
        FROM POP_PLOT_STRATUM_ASSGN a JOIN PLOT p ON p.CN=a.PLT_CN
        WHERE a.EVALID IN ({placeholders})
    """
    con = sqlite_ro(db_path)
    try:
        for row in con.execute(sql, tuple(evalid_to_state)):
            statecd = evalid_to_state[as_int(row["EVALID"])]
            panel = as_int(row["P2PANEL"])
            p = part_by_state[statecd]
            a_panels = parse_panels(p["final_A_panels"])
            fold = "A" if panel in a_panels else "B" if panel in parse_panels(p["final_B_panels"]) else ""
            cn = text(row["PLT_CN"])
            if cn in plots:
                raise ContractStop("INPUT_BLOCKED_F0_LINKAGE_FAILURE", f"Duplicate national F0 PLT_CN: {cn}")
            plots[cn] = {
                "plot_cn": cn,
                "assignment_cn": text(row["assignment_cn"]),
                "stratum_cn": text(row["STRATUM_CN"]),
                "statecd": statecd,
                "state_abbr": part_by_state[statecd]["state_abbr"],
                "evalid": as_int(row["EVALID"]),
                "panel": panel,
                "fold": fold,
                "assignment_statecd": as_int(row["assignment_statecd"]),
                "assignment_invyr": as_int(row["assignment_invyr"]),
                "plot_statecd": as_int(row["plot_statecd"]),
                "plot_invyr": as_int(row["plot_invyr"]),
                "plot_status_cd": as_int(row["PLOT_STATUS_CD"]),
                "plot_nonsample_reason": text(row["PLOT_NONSAMPLE_REASN_CD"]),
                "designcd": text(row["DESIGNCD"]),
                "manual": text(row["MANUAL"]),
                "macro_breakpoint_dia": text(row["MACRO_BREAKPOINT_DIA"]),
                "source": "FROZEN_NATIONAL_SQLITE",
            }
    finally:
        con.close()

    with zipfile.ZipFile(D09C_PREDECESSOR) as pre:
        for statecd in params["override_state_codes"]:
            state = params["override_state_abbreviations"][str(statecd)]
            target_evalid = as_int(part_by_state[statecd]["component_evalid"])
            plot_rows = {row["CN"]: row for row in nested_csv_rows(pre, state, "PLOT")}
            assignments = [row for row in nested_csv_rows(pre, state, "POP_PLOT_STRATUM_ASSGN") if as_int(row["EVALID"]) == target_evalid]
            seen = set()
            for assn in assignments:
                cn = assn["PLT_CN"]
                if cn in seen or cn in plots:
                    raise ContractStop("INPUT_BLOCKED_F0_LINKAGE_FAILURE", f"Duplicate override F0 PLT_CN: {cn}")
                seen.add(cn)
                row = plot_rows.get(cn)
                if row is None:
                    raise ContractStop("INPUT_BLOCKED_F0_LINKAGE_FAILURE", f"Missing override PLOT for {state} {cn}")
                panel = as_int(row["P2PANEL"])
                part = part_by_state[statecd]
                fold = "A" if panel in parse_panels(part["final_A_panels"]) else "B" if panel in parse_panels(part["final_B_panels"]) else ""
                plots[cn] = {
                    "plot_cn": cn,
                    "assignment_cn": assn["CN"],
                    "stratum_cn": assn["STRATUM_CN"],
                    "statecd": statecd,
                    "state_abbr": state,
                    "evalid": target_evalid,
                    "panel": panel,
                    "fold": fold,
                    "assignment_statecd": as_int(assn["STATECD"]),
                    "assignment_invyr": as_int(assn["INVYR"]),
                    "plot_statecd": as_int(row["STATECD"]),
                    "plot_invyr": as_int(row["INVYR"]),
                    "plot_status_cd": as_int(row["PLOT_STATUS_CD"]),
                    "plot_nonsample_reason": text(row["PLOT_NONSAMPLE_REASN_CD"]),
                    "designcd": text(row["DESIGNCD"]),
                    "manual": text(row["MANUAL"]),
                    "macro_breakpoint_dia": text(row["MACRO_BREAKPOINT_DIA"]),
                    "source": "FROZEN_CA_OR_WA_RAW_DESIGN_ZIPS",
                }
                if as_int(assn["STATECD"]) != as_int(row["STATECD"]) or as_int(assn["INVYR"]) != as_int(row["INVYR"]):
                    mismatches.append({"state_abbr": state, "assignment_cn": assn["CN"], "plot_cn": cn, "assignment_statecd": assn["STATECD"], "assignment_invyr": assn["INVYR"], "plot_statecd": row["STATECD"], "plot_invyr": row["INVYR"], "retained_by_plt_cn": "YES"})

    per_state_fold = Counter((row["statecd"], row["fold"]) for row in plots.values())
    frame_ok = all(per_state_fold[(state, fold)] > 0 for state in conus for fold in ("A", "B")) and all(row["fold"] in {"A", "B"} for row in plots.values())
    qc.append(qc_row("F0_PLOT_FRAME_CLOSURE", "F0", "48-state whole-panel F0", "positive A/B plot counts in every state", f"plots={len(plots)};state_fold_cells={sum(per_state_fold[(s,f)]>0 for s in conus for f in ('A','B'))}", frame_ok))
    if not frame_ok:
        raise ContractStop("INPUT_BLOCKED_F0_LINKAGE_FAILURE", "F0 plot/fold closure failure")
    ti_counts = Counter()
    for row in read_csv(D09C_TI):
        ti_counts[(as_int(row["state_fips"]), row["fold"])] += as_int(row["fold_sample_count"], 0)
    ti_mismatches = [
        {"state": state, "fold": fold, "plots": per_state_fold[(state, fold)], "ti": ti_counts[(state, fold)]}
        for state in sorted(conus) for fold in ("A", "B")
        if per_state_fold[(state, fold)] != ti_counts[(state, fold)]
    ]
    qc.append(qc_row("F0_PLOT_COUNTS_RECONCILE_TO_FROZEN_TI", "F0", "48 states x A/B", "zero mismatches", len(ti_mismatches), not ti_mismatches, details=json.dumps(ti_mismatches[:10], sort_keys=True)))
    if ti_mismatches:
        raise ContractStop("INPUT_BLOCKED_F0_LINKAGE_FAILURE", f"F0/TI plot-count mismatches: {ti_mismatches[:10]}")
    wv = part_by_state[54]
    wv_ok = wv["final_repair_class"] == "R2" and wv["sparse_eu_fallback_used"] == "1" and wv["sparse_eu_partner"] == "4"
    qc.append(qc_row("F0_WV_MERGED_FRAME_IDENTITY", "F0", "WV", "R2 sparse fallback with EU3 partner EU4", f"class={wv['final_repair_class']};fallback={wv['sparse_eu_fallback_used']};partner={wv['sparse_eu_partner']}", wv_ok))
    if not wv_ok:
        raise ContractStop("INPUT_BLOCKED_F0_LINKAGE_FAILURE", "WV frozen merged-frame identity failure")
    or_mismatch_ok = len([r for r in mismatches if r["state_abbr"] == "OR"]) == 4
    qc.append(qc_row("F0_OR_LINKAGE_TREATMENT", "F0", "OR 412301", "4 retained PLT_CN-resolved mismatches", len([r for r in mismatches if r["state_abbr"] == "OR"]), or_mismatch_ok, blocking="YES", details="No STATECD/INVYR rewrite"))
    if not or_mismatch_ok:
        raise ContractStop("INPUT_BLOCKED_F0_LINKAGE_FAILURE", "OR mismatch treatment does not match accepted F0")
    return plots, part_by_state, mismatches


def add_condition(conditions, row, plots, duplicate_counter):
    plot_cn = text(row["PLT_CN"])
    if plot_cn not in plots:
        return
    condid = as_int(row["CONDID"])
    if condid is None:
        duplicate_counter["missing_condid"] += 1
        return
    key = (plot_cn, condid)
    value = {
        "status": as_int(row["COND_STATUS_CD"]),
        "nonsample_reason": text(row["COND_NONSAMPLE_REASN_CD"]),
        "prop_basis": text(row["PROP_BASIS"]),
        "condprop": as_float(row["CONDPROP_UNADJ"]),
        "subpprop": as_float(row["SUBPPROP_UNADJ"]),
        "macrprop": as_float(row["MACRPROP_UNADJ"]),
    }
    if key in conditions:
        duplicate_counter["duplicate_condition_key"] += 1
        if conditions[key] != value:
            duplicate_counter["conflicting_condition_key"] += 1
        return
    conditions[key] = value


def add_subplot(subplots, row, plots, duplicate_counter):
    plot_cn = text(row["PLT_CN"])
    if plot_cn not in plots:
        return
    subp = as_int(row["SUBP"])
    if subp is None:
        duplicate_counter["missing_subp"] += 1
        return
    key = (plot_cn, subp)
    links = condition_tokens(row["CONDLIST"])
    for field in ("SUBPCOND", "MACRCOND"):
        value = as_int(row[field])
        if value is not None:
            links.add(value)
    value = {
        "status": as_int(row["SUBP_STATUS_CD"]),
        "nonsample_reason": text(row["POINT_NONSAMPLE_REASN_CD"]),
        "subpcond": as_int(row["SUBPCOND"]),
        "macrcond": as_int(row["MACRCOND"]),
        "condlist": text(row["CONDLIST"]),
        "links": links,
    }
    if key in subplots:
        duplicate_counter["duplicate_subplot_key"] += 1
        if subplots[key] != value:
            duplicate_counter["conflicting_subplot_key"] += 1
        return
    subplots[key] = value


def build_opportunities(db_path: Path, plots: dict, part_by_state: dict, params: dict, qc: list[dict]):
    conditions = {}
    subplots = {}
    duplicate_counter = Counter()
    national_evalids = sorted({row["evalid"] for row in plots.values() if row["source"] == "FROZEN_NATIONAL_SQLITE"})
    placeholders = ",".join("?" for _ in national_evalids)
    con = sqlite_ro(db_path)
    try:
        cond_sql = f"""
            SELECT c.PLT_CN,c.CONDID,c.COND_STATUS_CD,c.COND_NONSAMPLE_REASN_CD,
                   c.PROP_BASIS,c.CONDPROP_UNADJ,c.SUBPPROP_UNADJ,c.MACRPROP_UNADJ
            FROM COND c JOIN POP_PLOT_STRATUM_ASSGN a ON a.PLT_CN=c.PLT_CN
            WHERE a.EVALID IN ({placeholders})
        """
        for row in con.execute(cond_sql, tuple(national_evalids)):
            add_condition(conditions, row, plots, duplicate_counter)
        subplot_sql = f"""
            SELECT s.PLT_CN,s.SUBP,s.SUBP_STATUS_CD,s.POINT_NONSAMPLE_REASN_CD,
                   s.SUBPCOND,s.MACRCOND,s.CONDLIST
            FROM SUBPLOT s JOIN POP_PLOT_STRATUM_ASSGN a ON a.PLT_CN=s.PLT_CN
            WHERE a.EVALID IN ({placeholders})
        """
        for row in con.execute(subplot_sql, tuple(national_evalids)):
            add_subplot(subplots, row, plots, duplicate_counter)
    finally:
        con.close()

    for state in ("CA", "OR", "WA"):
        for row in iter_zip_csv(OBS_ZIPS / f"{state}_COND.zip", f"{state}_COND.csv"):
            add_condition(conditions, row, plots, duplicate_counter)
        for row in iter_zip_csv(OBS_ZIPS / f"{state}_SUBPLOT.zip", f"{state}_SUBPLOT.csv"):
            add_subplot(subplots, row, plots, duplicate_counter)

    conflict_ok = duplicate_counter["conflicting_condition_key"] == 0 and duplicate_counter["conflicting_subplot_key"] == 0 and duplicate_counter["missing_condid"] == 0 and duplicate_counter["missing_subp"] == 0
    qc.append(qc_row("OBSERVATION_LINK_KEY_DETERMINISM", "D3", "F0 COND/SUBPLOT", "zero conflicting or missing keys", json.dumps(duplicate_counter, sort_keys=True), conflict_ok))
    if not conflict_ok:
        raise ContractStop("INPUT_BLOCKED_F0_LINKAGE_FAILURE", f"COND/SUBPLOT linkage conflicts: {dict(duplicate_counter)}")

    cond_by_plot = defaultdict(dict)
    for (plot_cn, condid), row in conditions.items():
        cond_by_plot[plot_cn][condid] = row
    subplot_by_plot = defaultdict(dict)
    for (plot_cn, subp), row in subplots.items():
        subplot_by_plot[plot_cn][subp] = row

    opportunity = {}
    accessible_by_plot = {}
    sampled_by_plot = {}
    links_by_plot_subp = {}
    failure_reason = Counter()
    for plot_cn, plot in plots.items():
        accessible = {condid for condid, row in cond_by_plot.get(plot_cn, {}).items() if row["status"] == params["accessible_forest_cond_statuscd"]}
        sampled = {subp for subp, row in subplot_by_plot.get(plot_cn, {}).items() if row["status"] == params["sampled_subplot_statuscd"]}
        relevant = set()
        for subp in sampled:
            links = subplot_by_plot[plot_cn][subp]["links"]
            links_by_plot_subp[(plot_cn, subp)] = links
            if links & accessible:
                relevant.add(subp)
        accessible_by_plot[plot_cn] = accessible
        sampled_by_plot[plot_cn] = sampled
        checks = {
            "PLOT_STATUS_NOT_SAMPLED": plot["plot_status_cd"] == params["sampled_plot_statuscd"],
            "DESIGNCD_MISSING": bool(plot["designcd"]),
            "MANUAL_MISSING": bool(plot["manual"]),
            "NO_ACCESSIBLE_FOREST_CONDITION": bool(accessible),
            "NO_RELEVANT_SAMPLED_SUBPLOT": bool(relevant),
        }
        legitimate = all(checks.values())
        opportunity[plot_cn] = legitimate
        if not legitimate:
            for reason, ok in checks.items():
                if not ok:
                    failure_reason[reason] += 1
        plot["accessible_condition_count"] = len(accessible)
        plot["sampled_subplot_count"] = len(sampled)
        plot["relevant_sampled_subplot_count"] = len(relevant)
        plot["legitimate_opportunity"] = legitimate

    audit_rows = []
    for statecd in sorted(part_by_state):
        for fold in ("A", "B"):
            p_rows = [p for p in plots.values() if p["statecd"] == statecd and p["fold"] == fold]
            p_cns = {p["plot_cn"] for p in p_rows}
            c_rows = [row for (plot_cn, _), row in conditions.items() if plot_cn in p_cns and row["status"] == params["accessible_forest_cond_statuscd"]]
            s_rows = [row for (plot_cn, _), row in subplots.items() if plot_cn in p_cns and row["status"] == params["sampled_subplot_statuscd"]]
            legit = [p for p in p_rows if opportunity[p["plot_cn"]]]
            partial = sum(0 < p["sampled_subplot_count"] < 4 for p in legit)
            def nums(field):
                return [row[field] for row in c_rows if row[field] is not None]
            def value_range(field):
                values = nums(field)
                return "" if not values else f"{min(values):.12g}..{max(values):.12g}"
            part = part_by_state[statecd]
            audit_rows.append({
                "state_fips": f"{statecd:02d}",
                "state_abbr": part["state_abbr"],
                "fold": fold,
                "selected_panels": part["final_A_panels"] if fold == "A" else part["final_B_panels"],
                "component_evalid": part["component_evalid"],
                "f0_plot_visit_count": len(p_rows),
                "plot_status_sampled_count": sum(p["plot_status_cd"] == params["sampled_plot_statuscd"] for p in p_rows),
                "protocol_designcd_nonblank_count": sum(bool(p["designcd"]) for p in p_rows),
                "protocol_manual_nonblank_count": sum(bool(p["manual"]) for p in p_rows),
                "plot_with_accessible_forest_condition_count": sum(bool(accessible_by_plot[p["plot_cn"]]) for p in p_rows),
                "plot_with_sampled_subplot_count": sum(bool(sampled_by_plot[p["plot_cn"]]) for p in p_rows),
                "plot_with_relevant_sampled_subplot_count": sum(p["relevant_sampled_subplot_count"] > 0 for p in p_rows),
                "legitimate_opportunity_plot_visit_count": len(legit),
                "partial_sampling_opportunity_count": partial,
                "accessible_forest_condition_count": len(c_rows),
                "sampled_subplot_element_count": len(s_rows),
                "designcd_values": ";".join(sorted({p["designcd"] for p in p_rows if p["designcd"]})),
                "manual_values": ";".join(sorted({p["manual"] for p in p_rows if p["manual"]})),
                "prop_basis_values": ";".join(sorted({row["prop_basis"] for row in c_rows if row["prop_basis"]})),
                "condprop_unadj_range": value_range("condprop"),
                "subpprop_unadj_range": value_range("subpprop"),
                "macrprop_unadj_range": value_range("macrprop"),
                "partial_sampling_allowed": "YES",
                "effort_metadata_used_as_threshold": "NO",
                "opportunity_rule_id": "D08C2_PLOT_VISIT_LEGITIMATE_OPPORTUNITY_v01",
            })
    opp_ok = all(int(row["legitimate_opportunity_plot_visit_count"]) > 0 for row in audit_rows)
    qc.append(qc_row("D3_STATE_FOLD_OPPORTUNITY_CLOSURE", "D3", "48 states x A/B", "96 positive legitimate-opportunity cells", sum(int(r["legitimate_opportunity_plot_visit_count"]) > 0 for r in audit_rows), opp_ok, details=json.dumps(failure_reason, sort_keys=True)))
    return opportunity, accessible_by_plot, sampled_by_plot, links_by_plot_subp, audit_rows, duplicate_counter


def process_trees(db_path: Path, plots: dict, code_map: dict, starting_ids: set[str], native_states: dict, opportunity: dict, accessible_by_plot: dict, sampled_by_plot: dict, links_by_plot_subp: dict, params: dict, qc: list[dict]):
    raw_stats = defaultdict(Counter)
    raw_sets = defaultdict(lambda: {"states": set(), "folds": set(), "valid_states": set(), "valid_folds": set()})
    species_stats = defaultdict(Counter)
    encounter_plots = defaultdict(set)
    observed_contributor_codes = defaultdict(set)
    invalid_reasons = defaultdict(Counter)
    tree_key_seen = set()
    duplicate_tree_keys = 0
    tree_plot_state_mismatch = 0
    tree_plot_invyr_mismatch = 0

    def consume(row, source):
        nonlocal duplicate_tree_keys, tree_plot_state_mismatch, tree_plot_invyr_mismatch
        if as_int(row["STATUSCD"]) != params["live_statuscd"]:
            return
        dia = as_float(row["DIA"])
        if dia is None or dia < params["dia_min_inches"]:
            return
        plot_cn = text(row["PLT_CN"])
        plot = plots.get(plot_cn)
        if plot is None:
            return
        tree_cn = text(row["CN"])
        if tree_cn in tree_key_seen:
            duplicate_tree_keys += 1
            return
        tree_key_seen.add(tree_cn)
        code = as_int(row["SPCD"])
        raw_stats[code]["f0_live_large_tree_count"] += 1
        raw_stats[code][f"fold_{plot['fold']}_tree_count"] += 1
        raw_sets[code]["states"].add(plot["statecd"])
        raw_sets[code]["folds"].add(plot["fold"])
        if as_int(row["STATECD"]) != plot["plot_statecd"]:
            tree_plot_state_mismatch += 1
        if as_int(row["INVYR"]) != plot["plot_invyr"]:
            tree_plot_invyr_mismatch += 1
        mapping = code_map.get(code)
        if mapping is None:
            raw_stats[code]["unmapped_tree_count"] += 1
            return
        sid = mapping["analysis_species_id"]
        if sid not in starting_ids:
            raw_stats[code]["outside_starting_universe_tree_count"] += 1
            return
        observed_contributor_codes[sid].add(code)
        species_stats[sid]["f0_live_large_tree_count"] += 1
        if plot["statecd"] not in native_states[sid]:
            species_stats[sid]["outside_operational_native_domain_tree_count"] += 1
            raw_stats[code]["outside_operational_native_domain_tree_count"] += 1
            return
        species_stats[sid]["f0_native_candidate_tree_count"] += 1
        raw_stats[code]["f0_native_candidate_tree_count"] += 1
        reason = ""
        condid = as_int(row["CONDID"])
        subp = as_int(row["SUBP"])
        if not opportunity.get(plot_cn, False):
            reason = "PLOT_NOT_LEGITIMATE_OPPORTUNITY"
        elif condid not in accessible_by_plot.get(plot_cn, set()):
            reason = "TREE_COND_NOT_ACCESSIBLE_FOREST"
        elif subp not in sampled_by_plot.get(plot_cn, set()):
            reason = "TREE_SUBPLOT_NOT_SAMPLED"
        elif condid not in links_by_plot_subp.get((plot_cn, subp), set()):
            reason = "TREE_SUBPLOT_CONDITION_LINK_NOT_RELEVANT"
        if reason:
            species_stats[sid]["invalid_native_candidate_link_tree_count"] += 1
            raw_stats[code]["invalid_native_candidate_link_tree_count"] += 1
            invalid_reasons[sid][reason] += 1
            return
        fold = plot["fold"]
        species_stats[sid][f"valid_tree_count_{fold}"] += 1
        encounter_plots[(sid, fold)].add(plot_cn)
        raw_stats[code]["valid_encounter_tree_count"] += 1
        raw_stats[code][f"valid_encounter_tree_count_{fold}"] += 1
        raw_sets[code]["valid_states"].add(plot["statecd"])
        raw_sets[code]["valid_folds"].add(fold)

    national_evalids = sorted({row["evalid"] for row in plots.values() if row["source"] == "FROZEN_NATIONAL_SQLITE"})
    placeholders = ",".join("?" for _ in national_evalids)
    sql = f"""
        SELECT t.CN,t.PLT_CN,t.STATECD,t.INVYR,t.CONDID,t.SUBP,t.SPCD,t.STATUSCD,t.DIA,t.TPA_UNADJ
        FROM TREE t JOIN POP_PLOT_STRATUM_ASSGN a ON a.PLT_CN=t.PLT_CN
        WHERE a.EVALID IN ({placeholders}) AND t.STATUSCD=? AND t.DIA>=?
    """
    con = sqlite_ro(db_path)
    try:
        for row in con.execute(sql, tuple(national_evalids) + (params["live_statuscd"], params["dia_min_inches"])):
            consume(row, "FROZEN_NATIONAL_SQLITE")
    finally:
        con.close()
    for state in ("CA", "OR", "WA"):
        for row in iter_zip_csv(OBS_ZIPS / f"{state}_TREE.zip", f"{state}_TREE.csv"):
            consume(row, f"FROZEN_{state}_TREE_OVERRIDE")

    tree_key_ok = duplicate_tree_keys == 0
    qc.append(qc_row("TREE_UNIQUE_KEY", "D1_D2", "F0 live DIA>=5 TREE.CN", "0 duplicates", duplicate_tree_keys, tree_key_ok))
    if not tree_key_ok:
        raise ContractStop("INPUT_BLOCKED_F0_LINKAGE_FAILURE", "Duplicate TREE.CN in combined F0 observational sources")
    qc.append(qc_row("TREE_PLT_CN_LINKAGE_DIAGNOSTIC", "D2", "retained TREE records", "PLT_CN authoritative; mismatches audited", f"state_mismatch={tree_plot_state_mismatch};invyr_mismatch={tree_plot_invyr_mismatch}", True, blocking="NO", details="Accepted OR and all other records retain PLT_CN linkage; no key rewrite"))
    return raw_stats, raw_sets, species_stats, encounter_plots, observed_contributor_codes, invalid_reasons, len(tree_key_seen)


def classify_species(starting, master, contributors, native_states, plots, opportunity, species_stats, encounter_plots, observed_contributor_codes, invalid_reasons, qc):
    opp_state_fold = Counter()
    f0_state_fold = Counter()
    for plot in plots.values():
        f0_state_fold[(plot["statecd"], plot["fold"])] += 1
        if opportunity[plot["plot_cn"]]:
            opp_state_fold[(plot["statecd"], plot["fold"])] += 1

    eligibility = []
    fold_rows = []
    exclusions = []
    for row in sorted(starting, key=lambda r: (r["analysis_species_name"], r["analysis_species_id"])):
        sid = row["analysis_species_id"]
        m = master[sid]
        c_rows = contributors[sid]
        d1 = bool(c_rows) and all(
            c["analysis_species_id"] == sid
            and c["ordinary_analysis_species_flag"] == "1"
            and "UNRESOLVED" not in c["taxonomy_resolution_status"]
            and "AMBIGUOUS" not in c["taxonomy_resolution_status"]
            for c in c_rows
        )
        d2_invalid = species_stats[sid]["invalid_native_candidate_link_tree_count"]
        valid_tree_total = species_stats[sid]["valid_tree_count_A"] + species_stats[sid]["valid_tree_count_B"]
        candidate_tree_total = species_stats[sid]["f0_native_candidate_tree_count"]
        # Structurally ineligible records are explicitly audited and excluded. They
        # do not invalidate a species object when at least one candidate record is
        # legally linked; D2 fails only when candidate positives exist but none can
        # be legally linked (or the operational native domain itself is absent).
        d2 = bool(native_states[sid]) and not (candidate_tree_total > 0 and valid_tree_total == 0 and d2_invalid > 0)
        values = {}
        for fold in ("A", "B"):
            n_opp = sum(opp_state_fold[(statecd, fold)] for statecd in native_states[sid])
            n_f0 = sum(f0_state_fold[(statecd, fold)] for statecd in native_states[sid])
            n_enc = len(encounter_plots[(sid, fold)])
            n_tree = species_stats[sid][f"valid_tree_count_{fold}"]
            values[fold] = {"n_f0": n_f0, "n_opp": n_opp, "n_enc": n_enc, "n_tree": n_tree}
            fold_rows.append({
                "analysis_species_id": sid,
                "analysis_species_name": m["analysis_species_name"],
                "fold": fold,
                "native_state_count": len(native_states[sid]),
                "native_state_codes": ";".join(str(x) for x in sorted(native_states[sid])),
                "f0_plot_visit_count_in_native_domain": n_f0,
                "legitimate_opportunity_plot_visit_count": n_opp,
                "encounter_plot_visit_count": n_enc,
                "qualifying_tree_count": n_tree,
                "f0_live_large_tree_count_all_states": species_stats[sid]["f0_live_large_tree_count"],
                "f0_native_candidate_tree_count": species_stats[sid]["f0_native_candidate_tree_count"],
                "outside_operational_native_domain_tree_count": species_stats[sid]["outside_operational_native_domain_tree_count"],
                "invalid_native_candidate_link_tree_count": d2_invalid,
                "opportunity_positive": int(n_opp > 0),
                "encounter_positive": int(n_enc > 0),
                "direction_constructible": int(n_opp > 0 and n_enc > 0),
                "tp_unadj_used_for_eligibility": "NO",
                "abundance_total_computed": "NO",
            })
        d3a, d3b = values["A"]["n_opp"] > 0, values["B"]["n_opp"] > 0
        d4a, d4b = values["A"]["n_enc"] > 0, values["B"]["n_enc"] > 0
        dir_a, dir_b = d3a and d4a, d3b and d4b
        if not d1:
            status = "FAIL_D1_TAXONOMIC_RECONSTRUCTION"
        elif not d2:
            status = "FAIL_D2_TARGET_NATIVE_OR_F0_LINKAGE"
        elif dir_a and dir_b:
            status = STATUS_ELIGIBLE
        elif dir_a != dir_b:
            status = STATUS_ONE
        elif not d3a:
            status = "FAIL_D3_NO_LEGITIMATE_OPPORTUNITY_A"
        elif not d3b:
            status = "FAIL_D3_NO_LEGITIMATE_OPPORTUNITY_B"
        elif not d4a:
            status = "FAIL_D4_NO_POSITIVE_ENCOUNTER_A"
        else:
            status = "FAIL_D4_NO_POSITIVE_ENCOUNTER_B"

        reason_events = []
        if not d1:
            reason_events.append(("D1", "", "FAIL_D1_TAXONOMIC_RECONSTRUCTION", 1, "Frozen contributor mapping is absent or not deterministic."))
        if not d2:
            reason_events.append(("D2", "", "FAIL_D2_TARGET_NATIVE_OR_F0_LINKAGE", d2_invalid, ";".join(f"{k}:{v}" for k, v in sorted(invalid_reasons[sid].items())) or "No confirmed-native operational state domain."))
        if not d3a:
            reason_events.append(("D3", "A", "FAIL_D3_NO_LEGITIMATE_OPPORTUNITY_A", 1, "No legitimate F0 plot-visit opportunity in fold A across confirmed-native states."))
        if not d3b:
            reason_events.append(("D3", "B", "FAIL_D3_NO_LEGITIMATE_OPPORTUNITY_B", 1, "No legitimate F0 plot-visit opportunity in fold B across confirmed-native states."))
        if not d4a:
            reason_events.append(("D4", "A", "FAIL_D4_NO_POSITIVE_ENCOUNTER_A", 1, "No qualifying accepted-species TREE encounter in a legitimate fold-A opportunity."))
        if not d4b:
            reason_events.append(("D4", "B", "FAIL_D4_NO_POSITIVE_ENCOUNTER_B", 1, "No qualifying accepted-species TREE encounter in a legitimate fold-B opportunity."))
        for stage, fold, reason, count, details in reason_events:
            exclusions.append({
                "reason_event_id": f"EX{len(exclusions)+1:04d}",
                "analysis_species_id": sid,
                "analysis_species_name": m["analysis_species_name"],
                "provisional_d08c2_status": status,
                "stage": stage,
                "fold": fold,
                "structural_reason_code": reason,
                "event_count": count,
                "details": details,
                "result_threshold_used": "NO",
                "final_cohort_decision": "NO",
            })

        eligibility.append({
            "analysis_species_id": sid,
            "analysis_species_name": m["analysis_species_name"],
            "analysis_species_authors": m["analysis_species_authors"],
            "analysis_species_family": m["analysis_species_family"],
            "diameter_basis_composition": m["diameter_basis_composition"],
            "frozen_raw_fia_code_contributors": ";".join(str(as_int(c["fia_species_code"])) for c in sorted(c_rows, key=lambda x: as_int(x["fia_species_code"]))),
            "observed_f0_raw_fia_code_contributors": ";".join(str(x) for x in sorted(observed_contributor_codes[sid])),
            "native_state_count": len(native_states[sid]),
            "native_state_codes": ";".join(str(x) for x in sorted(native_states[sid])),
            "d1_taxonomy_reconstruction": "PASS" if d1 else "FAIL",
            "d2_target_native_f0_linkage": "PASS" if d2 else "FAIL",
            "d3_legitimate_opportunity_A": "PASS" if d3a else "FAIL",
            "d3_legitimate_opportunity_B": "PASS" if d3b else "FAIL",
            "d4_positive_encounter_A": "PASS" if d4a else "FAIL",
            "d4_positive_encounter_B": "PASS" if d4b else "FAIL",
            "n_legitimate_opportunity_A": values["A"]["n_opp"],
            "n_legitimate_opportunity_B": values["B"]["n_opp"],
            "n_encounter_plot_A": values["A"]["n_enc"],
            "n_encounter_plot_B": values["B"]["n_enc"],
            "n_qualifying_tree_A": values["A"]["n_tree"],
            "n_qualifying_tree_B": values["B"]["n_tree"],
            "invalid_native_candidate_link_tree_count": d2_invalid,
            "provisional_d08c2_status": status,
            "bidirectional_constructible": int(status == STATUS_ELIGIBLE),
            "final_cohort_flag": 0,
            "grid_used": "NO",
            "abundance_or_occupancy_result_used": "NO",
        })

    status_counts = Counter(row["provisional_d08c2_status"] for row in eligibility)
    qc.append(qc_row("SPECIES_LEDGER_ROW_COUNT", "FINAL", "eligibility ledger", 101, len(eligibility), len(eligibility) == 101))
    qc.append(qc_row("SPECIES_MECHANICAL_CLASSIFICATION", "FINAL", "eligibility ledger", "all 101 have one allowed status", sum(bool(r["provisional_d08c2_status"]) for r in eligibility), len(eligibility) == 101 and all(r["provisional_d08c2_status"] for r in eligibility), details=json.dumps(status_counts, sort_keys=True)))
    return eligibility, fold_rows, exclusions, status_counts


def build_aggregation_audit(code_rows, code_map, starting_ids, raw_stats, raw_sets):
    all_codes = set(code_map) | set(raw_stats)
    rows = []
    for code in sorted(all_codes, key=lambda x: (-1 if x is None else x)):
        mapping = code_map.get(code)
        stats = raw_stats[code]
        sets = raw_sets[code]
        sid = mapping["analysis_species_id"] if mapping else ""
        rows.append({
            "fia_species_code": "" if code is None else code,
            "fia_name_raw": mapping["fia_name_raw"] if mapping else "",
            "mapping_present_in_frozen_d08b1": int(mapping is not None),
            "mapping_class": mapping["mapping_class"] if mapping else "UNMAPPED_CODE_NOT_IN_FROZEN_AUTHORITY",
            "taxonomy_resolution_status": mapping["taxonomy_resolution_status"] if mapping else "UNMAPPED",
            "analysis_species_id": sid,
            "analysis_species_name": mapping["analysis_species_name"] if mapping else "",
            "belongs_to_101_starting_universe": int(sid in starting_ids),
            "f0_live_large_tree_count": stats["f0_live_large_tree_count"],
            "f0_live_large_tree_state_codes": ";".join(str(x) for x in sorted(sets["states"])),
            "f0_live_large_tree_folds": ";".join(sorted(sets["folds"])),
            "f0_native_candidate_tree_count": stats["f0_native_candidate_tree_count"],
            "valid_encounter_tree_count": stats["valid_encounter_tree_count"],
            "valid_encounter_tree_count_A": stats["valid_encounter_tree_count_A"],
            "valid_encounter_tree_count_B": stats["valid_encounter_tree_count_B"],
            "outside_operational_native_domain_tree_count": stats["outside_operational_native_domain_tree_count"],
            "invalid_native_candidate_link_tree_count": stats["invalid_native_candidate_link_tree_count"],
            "outside_starting_universe_tree_count": stats["outside_starting_universe_tree_count"],
            "unmapped_tree_count": stats["unmapped_tree_count"],
            "valid_encounter_state_codes": ";".join(str(x) for x in sorted(sets["valid_states"])),
            "valid_encounter_folds": ";".join(sorted(sets["valid_folds"])),
            "silent_drop_used": "NO",
        })
    return rows


def build_registry_delta(task_status: str, input_records: list[dict], output_paths: list[Path]):
    rows = []
    for record in input_records:
        rows.append({
            "TASK_ID": "D08C2_CORRECTED_CONSTRUCTIBILITY_v01",
            "input_authority_commit_version": record["role"],
            "exact_source_path_or_release_identity": record["path"],
            "sha256": record["sha256"],
            "bytes": record["size_bytes"],
            "status": record["status"],
            "scientific_output_changed": "NO_INPUT_ONLY",
            "publication_candidate": "NO",
            "Methods_role": "FROZEN_INPUT_AUTHORITY",
            "Data_role": "SOURCE_AUTHORITY",
            "Code_role": "NONE",
            "QC_role": "IDENTITY_VERIFICATION",
        })
    for path in output_paths:
        role = "CODE" if path.suffix == ".py" else "QC" if path.parent == QC else "OUTPUT"
        rows.append({
            "TASK_ID": "D08C2_CORRECTED_CONSTRUCTIBILITY_v01",
            "input_authority_commit_version": task_status,
            "exact_source_path_or_release_identity": str(path),
            "sha256": sha256_file(path),
            "bytes": path.stat().st_size,
            "status": "PROPOSED_FOR_MAINLINE_ACCEPTANCE",
            "scientific_output_changed": "YES_NEW_D08C2_OUTPUT",
            "publication_candidate": "YES_CANDIDATE_ONLY_BEFORE_F1" if path.name in {"Q1_D08C2_SPECIES_ELIGIBILITY_LEDGER_v01.csv", "Q1_D08C2_EXCLUSION_REASON_LEDGER_v01.csv", "Q1_D08C2_ACCEPTED_SPECIES_AGGREGATION_AUDIT_v01.csv", "Q1_D08C2_OBSERVATION_OPPORTUNITY_AUDIT_v01.csv"} else "NO",
            "Methods_role": "D08C2_RULE_OR_AUDIT" if role != "CODE" else "REPRODUCTION_CODE",
            "Data_role": "PROVISIONAL_D08C2" if role == "OUTPUT" else "NONE",
            "Code_role": "LOCAL_EXECUTABLE_RUNNER" if role == "CODE" else "NONE",
            "QC_role": "VALIDATION" if role == "QC" else "TRACEABILITY",
        })
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(ROOT), help="Frozen local Q1 workspace; v01 contract is fixed to C:\\range_paper")
    args = parser.parse_args()
    if Path(args.root).resolve() != ROOT.resolve():
        raise ContractStop("IMPLEMENTATION_BLOCKED_CONTRACT_VIOLATION", "Runner root must remain C:\\range_paper for this frozen execution")
    started = time.time()
    params = json.loads(PARAM_PATH.read_text(encoding="utf-8"))
    OUT.mkdir(parents=True, exist_ok=True)
    QC.mkdir(parents=True, exist_ok=True)

    db_path, qc, input_records = verify_authorities_and_p0(params)
    print("STAGE=P0_PASS", flush=True)
    (starting, starting_ids, master, global_flags, code_rows, code_map, contributors,
     state_map, state_crosswalk, native_states, evidence_detail) = load_scientific_authorities(db_path, params, qc)
    print("STAGE=D1_D2_AUTHORITY_PASS", flush=True)
    plots, part_by_state, f0_mismatches = load_f0_frame(db_path, params, qc)
    print(f"STAGE=F0_FRAME_PASS PLOTS={len(plots)}", flush=True)
    opportunity, accessible, sampled, links, opportunity_audit, duplicates = build_opportunities(db_path, plots, part_by_state, params, qc)
    print(f"STAGE=D3_OPPORTUNITY_COMPLETE LEGITIMATE={sum(opportunity.values())}", flush=True)
    (raw_stats, raw_sets, species_stats, encounter_plots, observed_codes,
     invalid_reasons, retained_tree_count) = process_trees(db_path, plots, code_map, starting_ids, native_states, opportunity, accessible, sampled, links, params, qc)
    print(f"STAGE=TREE_SCAN_COMPLETE ROWS={retained_tree_count}", flush=True)
    eligibility, fold_rows, exclusions, status_counts = classify_species(starting, master, contributors, native_states, plots, opportunity, species_stats, encounter_plots, observed_codes, invalid_reasons, qc)
    aggregation = build_aggregation_audit(code_rows, code_map, starting_ids, raw_stats, raw_sets)

    qc.extend([
        qc_row("NO_ABUNDANCE_TOTAL", "BOUNDARY", "D08C2", "not computed", "not computed", True),
        qc_row("NO_OCCUPANCY_OR_DETECTION_MODEL", "BOUNDARY", "D08C2", "not fitted", "not fitted", True),
        qc_row("NO_SUPPORT_OR_GEOMETRY_GATE", "BOUNDARY", "D08C2", "not run", "not run", True),
        qc_row("NO_GRID", "BOUNDARY", "D08C2", "NO GRID REQUIRED", "no grid read/generated", True),
        qc_row("NO_NETWORK_ACQUISITION", "BOUNDARY", "runner", "local-only", "standard-library local filesystem/SQLite/ZIP only", True),
        qc_row("CENTRAL_REGISTRY_NOT_MODIFIED", "GOVERNANCE", "Registry", "delta only", "REGISTRY_DELTA_v01.csv only", True),
    ])
    task_ok = len(eligibility) == 101 and all(row["status"] == "PASS" for row in qc if row["blocking"] == "YES")
    task_status = TASK_PASS if task_ok else "IMPLEMENTATION_BLOCKED_CONTRACT_VIOLATION"
    qc.append(qc_row("TASK_LEVEL_STATUS", "FINAL", "D08C2_CORRECTED_CONSTRUCTIBILITY_v01", TASK_PASS, task_status, task_ok, details="Eligible-species count is descriptive and not a PASS criterion"))

    paths = {
        "eligibility": OUT / "Q1_D08C2_SPECIES_ELIGIBILITY_LEDGER_v01.csv",
        "exclusions": OUT / "Q1_D08C2_EXCLUSION_REASON_LEDGER_v01.csv",
        "fold": OUT / "Q1_D08C2_SPECIES_FOLD_DIAGNOSTICS_v01.csv",
        "aggregation": OUT / "Q1_D08C2_ACCEPTED_SPECIES_AGGREGATION_AUDIT_v01.csv",
        "opportunity": OUT / "Q1_D08C2_OBSERVATION_OPPORTUNITY_AUDIT_v01.csv",
        "state_crosswalk": OUT / "Q1_D08C2_OPERATIONAL_NATIVE_STATE_CROSSWALK_v01.csv",
        "f0_mismatch": OUT / "Q1_D08C2_F0_LINKAGE_MISMATCH_AUDIT_v01.csv",
        "qc": OUT / "Q1_D08C2_INPUT_AND_SCHEMA_QC_v01.csv",
    }
    write_csv(paths["eligibility"], eligibility)
    write_csv(paths["exclusions"], exclusions, ["reason_event_id", "analysis_species_id", "analysis_species_name", "provisional_d08c2_status", "stage", "fold", "structural_reason_code", "event_count", "details", "result_threshold_used", "final_cohort_decision"])
    write_csv(paths["fold"], fold_rows)
    write_csv(paths["aggregation"], aggregation)
    write_csv(paths["opportunity"], opportunity_audit)
    write_csv(paths["state_crosswalk"], state_crosswalk)
    write_csv(paths["f0_mismatch"], f0_mismatches, ["state_abbr", "assignment_cn", "plot_cn", "assignment_statecd", "assignment_invyr", "plot_statecd", "plot_invyr", "retained_by_plt_cn"])
    write_csv(paths["qc"], qc)

    elapsed = time.time() - started
    summary = {
        "task_id": params["task_id"],
        "task_status": task_status,
        "starting_species_count": len(eligibility),
        "provisional_status_counts": dict(sorted(status_counts.items())),
        "eligible_species_count": status_counts[STATUS_ELIGIBLE],
        "one_direction_only_count": status_counts[STATUS_ONE],
        "f0_plot_visit_count": len(plots),
        "legitimate_opportunity_plot_visit_count": sum(opportunity.values()),
        "retained_f0_live_large_tree_count": retained_tree_count,
        "aggregation_audit_rows": len(aggregation),
        "exclusion_reason_rows": len(exclusions),
        "f0_or_mismatch_rows": len([r for r in f0_mismatches if r["state_abbr"] == "OR"]),
        "blocking_qc_failures": sum(r["status"] == "FAIL" and r["blocking"] == "YES" for r in qc),
        "elapsed_seconds": elapsed,
        "network_acquisition": "NONE",
        "grid": "NONE",
        "downstream_models": "NONE",
    }
    write_json(QC / "D08C2_CORRECTED_BUILD_SUMMARY_v01.json", summary)
    write_json(QC / "D08C2_CORRECTED_ENVIRONMENT_v01.json", {
        "python": sys.version,
        "platform": platform.platform(),
        "sqlite_version": sqlite3.sqlite_version,
        "working_directory": os.getcwd(),
        "database_path": str(db_path),
        "network_used": False,
    })
    log = (
        f"# D08C2 corrected implementation log v01\n\n"
        f"- Task status: `{task_status}`\n"
        f"- P0 completed before species identities or TREE.SPCD values were read.\n"
        f"- National FIADB source: frozen local ZIP only; no download or replacement snapshot.\n"
        f"- CA/OR/WA observational source: nine frozen override ZIPs.\n"
        f"- F0: accepted D09C T2 final correction v02 partitions, TI design, WV merged frame, and OR PLT_CN treatment.\n"
        f"- Eligibility: only bidirectional positive mathematical constructibility; no count threshold beyond >0.\n"
        f"- No grid, abundance total, occupancy/detection fit, support gate, final cohort, geometry, World 0, or real Q1.\n"
        f"- Runtime seconds: {elapsed:.3f}.\n"
    )
    (QC / "D08C2_CORRECTED_IMPLEMENTATION_LOG_v01.md").write_text(log, encoding="utf-8")
    note = (
        f"# Q1 corrected D08C2 result note v01\n\n"
        f"Task status: **{task_status}**\n\n"
        f"## Frozen object\n\n"
        f"This result audits D1 taxonomy reconstruction, D2 operational-native/F0 linkage, D3 legitimate plot-visit opportunities, and D4 bidirectional positive constructibility for exactly {len(eligibility)} Range Gate v02 `PASS_COARSE` accepted species. It is not a final cohort.\n\n"
        f"## Mechanical result\n\n"
        f"- Provisional bidirectionally constructible: {status_counts[STATUS_ELIGIBLE]} species.\n"
        f"- One-direction-only diagnostic: {status_counts[STATUS_ONE]} species.\n"
        + "".join(f"- {key}: {value} species.\n" for key, value in sorted(status_counts.items()) if key not in {STATUS_ELIGIBLE, STATUS_ONE})
        + f"- F0 plot-visits audited: {len(plots)}; legitimate opportunities: {sum(opportunity.values())}.\n"
        f"- F0 live DIA>=5 TREE records audited without TPA magnitude selection: {retained_tree_count}.\n"
        f"- OR PLT_CN-resolved mismatch rows retained: {len([r for r in f0_mismatches if r['state_abbr']=='OR'])}.\n\n"
        f"## Boundary\n\n"
        f"No grid or encounter-cell threshold was used. No abundance total/precision, occupancy or detection model, support recoverability, final cohort, R1/R2, World 0, prediction, conformal inference, or real Q1 was run. STOP and return to scientific mainline.\n"
    )
    result_note = OUT / "Q1_D08C2_RESULT_NOTE_v01.md"
    result_note.write_text(note, encoding="utf-8")

    initial_outputs = list(paths.values()) + [result_note, QC / "D08C2_CORRECTED_BUILD_SUMMARY_v01.json", QC / "D08C2_CORRECTED_ENVIRONMENT_v01.json", QC / "D08C2_CORRECTED_IMPLEMENTATION_LOG_v01.md", SRC / "build_d08c2_corrected_constructibility_v01.py", PARAM_PATH]
    registry = build_registry_delta(task_status, input_records, initial_outputs)
    registry_path = OUT / "REGISTRY_DELTA_v01.csv"
    write_csv(registry_path, registry)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        main()
    except ContractStop as exc:
        QC.mkdir(parents=True, exist_ok=True)
        write_json(QC / "D08C2_CORRECTED_BLOCKED_STATUS_v01.json", {"task_id": "D08C2_CORRECTED_CONSTRUCTIBILITY_v01", "status": exc.status, "detail": exc.detail})
        print(json.dumps({"status": exc.status, "detail": exc.detail}, ensure_ascii=False), file=sys.stderr)
        raise SystemExit(2)
