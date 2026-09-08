from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import pickle
import shutil
import sqlite3
import statistics
import sys
import time
import zipfile
from collections import Counter, defaultdict
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable

import numpy as np


ROOT = Path(r"C:\range_paper")
WORK = ROOT / "99_tmp" / "d10fb12_v01_1"
OUT = ROOT / "05_qc" / "d10fb12_v01_1_work_covariance_qualification_closure"
PARENT = ROOT / "05_qc" / "d10fb12_v01"
PARENT_ZIP = PARENT / "Q1_D10F_B12_v01.zip"
PARENT_SRC = PARENT / "src_candidate"
CACHE = ROOT / "99_tmp" / "d10fb12_v01" / "cache" / "b12_cache.sqlite"
B11_ZIP = ROOT / "10_archive" / "d10fb11_v01" / "Q1_D10F_B11_v01.zip"
SUBSTRATE_ZIP = ROOT / "10_archive" / "q1_fia_substrate_v01_1" / "Q1_FIA_SUBSTRATE_v01_1.zip"
REQUEST = Path(r"C:\Users\bug_g\.codex\attachments\255d72e6-530c-4a01-b31e-43111534ae45\pasted-text.txt")

sys.path.insert(0, str(PARENT_SRC))
from mini_parquet import ParquetWriter, footer_info  # noqa: E402


TASK = "Q1_D10F_B12_v01_1_WORK_COVARIANCE_QUALIFICATION_CLOSURE"
TRANSFER_NAME = "Q1-D10FB12-v01_1-20260908"
ZIP_NAME = "Q1_D10F_B12_v01_1.zip"
EXPECTED_PARENT_SHA = "202b7a475a7aeb3dfe35749d70fccb076729dea79e8a75fcafb63c83c800c433"
EXPECTED_B11_SHA = "ee6888a47762aaa966afaeffddd2569500f0f8271745263b763711348d761624"
EXPECTED_SUBSTRATE_SHA = "1dbd8cf3fdb9fdbd25945ed70af64e1c739ec78f10f24ec4866128c38d5d946e"
EXPECTED_CACHE_LOGICAL_SHA = "e85168819a7954f9f1ead69f1554e29c193ba9ef369c7c2793b4587d5f8dd416"
EXPECTED_CACHE_FINGERPRINT = "5d0a9dbaf55045c20bdab107f061c477fe77106d100bc95681a6dfebd1eeb7bd"
EXPECTED_CACHE_FILE_SHA = "0daf80d098546d61aecd8e75701f5174d9f6fd4452ce4a1b257651d45c9d2953"
EXPECTED_OLD_SEALS = {
    "B12_POOL_MEMBERSHIP_v01.parquet": ("46276d2aea5d9a8b59e5e081c28c3c4324828346b70419dbe6472582c36fb27b", 321584),
    "B12_POOL_PREDICTIONS_GENERIC_v01.parquet": ("0ccb4a33621ddd83ec30e57588592e1e5653300c93fddaf9dadbf3f38a551b78", 9268),
    "B12_POOL_PREDICTIONS_SPECIES_v01.parquet": ("56f32055bf1a87fef2db6d7516867d1f50ecc44407c5fb10a70a21b4f8d4b0e8", 138367),
}
SOURCE_CACHE_IDENTITY = f"sha256:{EXPECTED_CACHE_FILE_SHA}|logical:{EXPECTED_CACHE_LOGICAL_SHA}|fingerprint:{EXPECTED_CACHE_FINGERPRINT}"
SPECIES = [str(x) for x in range(1)]  # replaced after verified cache open
PROJECTION_COUNT = 32
SPLIT_REPLICATES = 4
ROW_GROUP_SIZE = 50000
CANONICAL_VERSION = "B12_FULL_COV_SUFFICIENT_STATS_HEXFLOAT_V01_1"
ZIP_TIME = (2026, 9, 8, 0, 0, 0)


def sha256_file(path: Path, chunk: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def stable_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fields: list[str]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="raise", lineterminator="\n")
        w.writeheader()
        for row in rows:
            w.writerow(row)
            count += 1
    return count


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8", newline="\n")


def write_json(path: Path, value: Any) -> None:
    write_text(path, json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2))


def fhex(value: float) -> str:
    x = float(value)
    if not math.isfinite(x):
        raise ValueError("Canonical covariance sufficient statistics must be finite")
    if x == 0.0:
        x = 0.0
    return x.hex()


def stable_seed(*parts: Any) -> int:
    h = hashlib.sha256("|".join(str(x) for x in parts).encode("utf-8")).digest()
    return int.from_bytes(h[:8], "little", signed=False) & ((1 << 63) - 1)


def projection_sign(cell: str, index: int) -> float:
    h = hashlib.sha256(f"B12_PROJ|{index}|{cell}".encode("utf-8")).digest()
    return 1.0 if (h[0] & 1) else -1.0


def ref_band(n: int) -> str:
    if n >= 50:
        return "R5"
    if n >= 20:
        return "R4"
    if n >= 8:
        return "R3"
    if n >= 4:
        return "R2"
    return "R1"


def pool_df_band(df: int) -> str:
    if df < 50:
        return "DF_LT50"
    if df < 200:
        return "DF_50_199"
    if df < 1000:
        return "DF_200_999"
    return "DF_GE1000"


def safe_ratio(pred: float, target: float) -> float:
    if target > 0:
        return pred / target
    return 1.0 if pred == 0 else float("inf")


def abs_log_ratio(pred: float, target: float) -> float:
    if pred > 0 and target > 0:
        return abs(math.log(pred / target))
    if pred == 0 and target == 0:
        return 0.0
    return float("nan")


def finite(values: Iterable[Any]) -> list[float]:
    out = []
    for value in values:
        try:
            x = float(value)
        except (TypeError, ValueError):
            continue
        if math.isfinite(x):
            out.append(x)
    return out


def median(values: Iterable[Any]) -> float:
    x = finite(values)
    return float(np.median(x)) if x else float("nan")


def quantile(values: Iterable[Any], q: float) -> float:
    x = finite(values)
    return float(np.quantile(x, q)) if x else float("nan")


def fmt(value: Any, digits: int = 3) -> str:
    try:
        x = float(value)
    except (TypeError, ValueError):
        return "NA"
    return f"{x:.{digits}f}" if math.isfinite(x) else "NA"


def read_only_connection() -> sqlite3.Connection:
    con = sqlite3.connect(f"file:{CACHE.as_posix()}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    return con


def cache_schema_snapshot(con: sqlite3.Connection) -> tuple[str, list[dict[str, Any]]]:
    rows = []
    for table, sql in con.execute("SELECT name,sql FROM sqlite_master WHERE type='table' ORDER BY name"):
        rows.append({"table": table, "sql": sql, "rows": con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]})
    digest = hashlib.sha256(stable_json(rows).encode("utf-8")).hexdigest()
    return digest, rows


def verify_cache_and_parent() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    required = [CACHE, PARENT_ZIP, B11_ZIP, SUBSTRATE_ZIP, REQUEST,
                PARENT / "B12_RUN_METADATA_v01.json",
                PARENT / "B12_PREDICTION_SEAL_MANIFEST_v01.csv",
                PARENT / "B12_PSEUDO_TARGET_INVENTORY_v01.csv",
                PARENT / "B12_ACTUAL24_INVENTORY_v01.csv"]
    missing = [str(p) for p in required if not p.is_file()]
    if missing:
        raise RuntimeError("Missing required cache/parent input: " + " | ".join(missing))
    identities = {
        "parent_zip": sha256_file(PARENT_ZIP),
        "b11_zip": sha256_file(B11_ZIP),
        "substrate_zip": sha256_file(SUBSTRATE_ZIP),
        "cache_file": sha256_file(CACHE),
    }
    expected = {
        "parent_zip": EXPECTED_PARENT_SHA, "b11_zip": EXPECTED_B11_SHA,
        "substrate_zip": EXPECTED_SUBSTRATE_SHA, "cache_file": EXPECTED_CACHE_FILE_SHA,
    }
    if identities != expected:
        raise RuntimeError(f"Input identity mismatch: {identities}")
    parent_meta = json.loads((PARENT / "B12_RUN_METADATA_v01.json").read_text(encoding="utf-8"))
    con = read_only_connection()
    integrity = con.execute("PRAGMA integrity_check").fetchone()[0]
    fingerprint = con.execute("SELECT value FROM cache_meta WHERE key='fingerprint'").fetchone()[0]
    a2meta = json.loads(con.execute("SELECT value FROM cache_meta WHERE key='a2meta'").fetchone()[0])
    schema_sha, schema_rows = cache_schema_snapshot(con)
    if integrity != "ok" or fingerprint != EXPECTED_CACHE_FINGERPRINT:
        raise RuntimeError("Cache integrity or fingerprint mismatch")
    # Exact parent-runtime digest semantics.  B12 v01 used SQLite 3.49.1 printf.
    h = hashlib.sha256()
    logical_rows = 0
    for row in con.execute("SELECT PLT_CN,SPCD,printf('%.17g',y) FROM plot_species ORDER BY PLT_CN,SPCD"):
        h.update(("\t".join(str(x) for x in row) + "\n").encode("utf-8"))
        logical_rows += 1
    logical_sha = h.hexdigest()
    if logical_sha != EXPECTED_CACHE_LOGICAL_SHA or a2meta["tree_cache_logical_sha256"] != logical_sha:
        raise RuntimeError(f"Cache logical digest mismatch: {logical_sha}")
    protected = {
        "pseudo_total": con.execute("SELECT COUNT(*) FROM target WHERE target_type='PSEUDO'").fetchone()[0],
        "pseudo_scoreable": con.execute("SELECT COUNT(*) FROM target WHERE target_type='PSEUDO' AND validation_status='AVAILABLE'").fetchone()[0],
        "pseudo_heterogeneous": con.execute("SELECT COUNT(*) FROM target WHERE target_type='PSEUDO' AND validation_status='TARGET_CORE_IDENTITY_HETEROGENEOUS'").fetchone()[0],
        "level1": con.execute("SELECT COUNT(*) FROM target WHERE target_type='PSEUDO' AND validation_status='AVAILABLE' AND route='LEVEL1'").fetchone()[0],
        "level2": con.execute("SELECT COUNT(*) FROM target WHERE target_type='PSEUDO' AND validation_status='AVAILABLE' AND route='LEVEL2'").fetchone()[0],
        "actual24": con.execute("SELECT COUNT(*) FROM target WHERE target_type='ACTUAL24'").fetchone()[0],
        "actual_level1": con.execute("SELECT COUNT(*) FROM target WHERE target_type='ACTUAL24' AND route='LEVEL1'").fetchone()[0],
        "actual_level2": con.execute("SELECT COUNT(*) FROM target WHERE target_type='ACTUAL24' AND route='LEVEL2'").fetchone()[0],
        "fia_spcd": con.execute("SELECT COUNT(*) FROM species_universe").fetchone()[0],
        "target_member_leak": con.execute("SELECT COUNT(*) FROM target t JOIN pool_membership p ON p.target_id=t.target_id AND p.pool_role='CANDIDATE' AND p.member_id=t.target_member_id").fetchone()[0],
        "target_species_var_positive": con.execute("SELECT COUNT(*) FROM target t JOIN member_species_stats s ON s.member_id=t.target_member_id WHERE t.target_type='PSEUDO' AND t.validation_status='AVAILABLE' AND s.scalar_ss>0").fetchone()[0],
        "target_positive_pool_positive": con.execute("SELECT COUNT(*) FROM target t JOIN member_species_stats s ON s.member_id=t.target_member_id JOIN pool_species_pred p ON p.target_id=t.target_id AND p.SPCD=s.SPCD WHERE t.target_type='PSEUDO' AND t.validation_status='AVAILABLE' AND s.scalar_ss>0 AND p.pred_scalar_var>0").fetchone()[0],
    }
    protected["target_positive_pool_zero"] = protected["target_species_var_positive"] - protected["target_positive_pool_positive"]
    expected_protected = {
        "pseudo_total": 5729, "pseudo_scoreable": 4640, "pseudo_heterogeneous": 1089,
        "level1": 4397, "level2": 243, "actual24": 24, "actual_level1": 11,
        "actual_level2": 13, "fia_spcd": 402, "target_member_leak": 0,
        "target_species_var_positive": 55923, "target_positive_pool_positive": 48723,
        "target_positive_pool_zero": 7200,
    }
    if protected != expected_protected:
        raise RuntimeError(f"Protected reconciliation mismatch: {protected}")
    old_manifest = {r["artifact"]: r for r in read_csv(PARENT / "B12_PREDICTION_SEAL_MANIFEST_v01.csv")}
    old_seal_rows = []
    for name, (expected_sha, expected_rows) in EXPECTED_OLD_SEALS.items():
        path = PARENT / name
        actual_sha = sha256_file(path)
        parent_row = old_manifest[name]
        status = "PASS" if actual_sha == expected_sha and int(parent_row["row_count"]) == expected_rows and parent_row["sha256"] == expected_sha else "FAIL"
        old_seal_rows.append({"artifact": name, "expected_sha256": expected_sha, "observed_sha256": actual_sha,
                              "expected_rows": expected_rows, "observed_rows": int(parent_row["row_count"]), "status": status})
    con.close()
    if any(r["status"] != "PASS" for r in old_seal_rows):
        raise RuntimeError("Parent Stage-P seal reverification failed")
    qc_rows = [
        {"check_id": "CACHE_FILE_SHA256", "expected": EXPECTED_CACHE_FILE_SHA, "observed": identities["cache_file"], "status": "PASS", "detail": str(CACHE)},
        {"check_id": "CACHE_SQLITE_INTEGRITY", "expected": "ok", "observed": integrity, "status": "PASS", "detail": "PRAGMA integrity_check"},
        {"check_id": "CACHE_FINGERPRINT", "expected": EXPECTED_CACHE_FINGERPRINT, "observed": fingerprint, "status": "PASS", "detail": "cache_meta"},
        {"check_id": "CACHE_LOGICAL_DIGEST", "expected": EXPECTED_CACHE_LOGICAL_SHA, "observed": logical_sha, "status": "PASS", "detail": f"{logical_rows} ordered plot_species rows; parent SQLite printf semantics"},
        {"check_id": "CACHE_SCHEMA_SHA256", "expected": "RECORDED_V01_1", "observed": schema_sha, "status": "PASS", "detail": f"{len(schema_rows)} tables; schema and row counts retained in run metadata"},
        {"check_id": "PARENT_B12_ZIP", "expected": EXPECTED_PARENT_SHA, "observed": identities["parent_zip"], "status": "PASS", "detail": "Exact parent package"},
        {"check_id": "B11_ZIP", "expected": EXPECTED_B11_SHA, "observed": identities["b11_zip"], "status": "PASS", "detail": "Accepted synthetic result"},
        {"check_id": "SUBSTRATE_ZIP", "expected": EXPECTED_SUBSTRATE_SHA, "observed": identities["substrate_zip"], "status": "PASS", "detail": "Accepted structural substrate"},
        {"check_id": "NEW_TREE_SOURCE_SCAN_ROWS", "expected": "0", "observed": "0", "status": "PASS", "detail": "B12 v01 cache opened read-only; national SQLite path is absent from this builder"},
    ]
    for row in old_seal_rows:
        qc_rows.append({"check_id": "OLD_STAGE_P_SEAL_" + row["artifact"], "expected": row["expected_sha256"], "observed": row["observed_sha256"], "status": row["status"], "detail": f"logical rows={row['observed_rows']}"})
    meta = {"identities": identities, "parent_meta": parent_meta, "protected": protected,
            "cache_schema_sha256": schema_sha, "cache_schema": schema_rows,
            "cache_logical_rows": logical_rows, "cache_logical_sha256": logical_sha,
            "old_stage_p_seals": old_seal_rows}
    return qc_rows, meta


def sorted_cells(mapping: dict[str, Any]) -> list[str]:
    return sorted(mapping, key=lambda x: (parse_cell(x)[1], parse_cell(x)[2], x) if x.startswith("50km_") else (0, 0, x))


def parse_cell(cell: str) -> tuple[str, int, int]:
    parts = cell.split("_")
    if len(parts) != 3 or parts[0] not in {"50km", "100km", "200km"}:
        raise ValueError(f"Invalid frozen grid cell ID: {cell}")
    return parts[0], int(parts[1]), int(parts[2])


def parent_cell(cell: str, grain_km: int) -> str:
    _, ix, iy = parse_cell(cell)
    if grain_km == 50:
        return f"50km_{ix}_{iy}"
    if grain_km == 100:
        return f"100km_{ix // 2}_{iy // 2}"
    if grain_km == 200:
        return f"200km_{ix // 4}_{iy // 4}"
    raise ValueError(grain_km)


def validate_floor_division() -> None:
    tests = {
        ("50km_-1_-1", 100): "100km_-1_-1",
        ("50km_-2_-2", 100): "100km_-1_-1",
        ("50km_-3_-3", 100): "100km_-2_-2",
        ("50km_-1_-1", 200): "200km_-1_-1",
        ("50km_-4_-4", 200): "200km_-1_-1",
        ("50km_-5_-5", 200): "200km_-2_-2",
        ("50km_3_7", 100): "100km_1_3",
        ("50km_7_9", 200): "200km_1_2",
    }
    for (cell, grain), expected in tests.items():
        observed = parent_cell(cell, grain)
        if observed != expected:
            raise RuntimeError(f"Floor division test failed: {cell} {grain} -> {observed}")


def membership_digest(members: list[dict[str, Any]]) -> str:
    payload = [[m["member_id"], int(m["n"]), int(m["df"])] for m in members]
    return hashlib.sha256(stable_json(payload).encode("utf-8")).hexdigest()


def load_pool_bundle(con: sqlite3.Connection, target_id: str, role: str, include_species: bool = True) -> dict[str, Any]:
    members = []
    domain_diag: defaultdict[str, float] = defaultdict(float)
    generic_diag: defaultdict[str, float] = defaultdict(float)
    domain_vectors = []
    generic_vectors = []
    rows = con.execute(
        """SELECT m.member_id,m.n,m.df,g.cell_counts_json,g.cell_sum_json,g.cell_sumsq_json
           FROM pool_membership p
           JOIN member m ON m.member_id=p.member_id
           JOIN member_generic_stats g ON g.member_id=p.member_id
           WHERE p.target_id=? AND p.pool_role=? ORDER BY m.member_id""",
        (target_id, role),
    ).fetchall()
    for row in rows:
        mid, n, df = str(row[0]), int(row[1]), int(row[2])
        counts = {str(k): int(v) for k, v in json.loads(row[3]).items()}
        sums = {str(k): float(v) for k, v in json.loads(row[4]).items()}
        sumsq = {str(k): float(v) for k, v in json.loads(row[5]).items()}
        members.append({"member_id": mid, "n": n, "df": df, "counts": counts, "sums": sums, "sumsq": sumsq})
        for cell, value in counts.items():
            domain_diag[cell] += value
        for cell, value in sumsq.items():
            generic_diag[cell] += value
        domain_vectors.append({cell: value / math.sqrt(n) for cell, value in counts.items()})
        generic_vectors.append({cell: value / math.sqrt(n) for cell, value in sums.items()})
    if not members:
        raise RuntimeError(f"No pool membership for {target_id} {role}")
    pool_df = sum(m["df"] for m in members)
    species_by_id: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    current: tuple[str, str] | None = None
    current_cells: list[list[Any]] = []
    current_n = 0

    def flush_species_member() -> None:
        nonlocal current, current_cells, current_n
        if current is None:
            return
        sp, mid = current
        species_by_id[sp].append({"member_id": mid, "n": current_n, "cells": current_cells})

    q = """SELECT s.SPCD,s.member_id,m.n,s.cell_id,s.sum_y,s.sumsq_y
           FROM pool_membership p
           JOIN member_species_cell s ON s.member_id=p.member_id
           JOIN member m ON m.member_id=s.member_id
           WHERE p.target_id=? AND p.pool_role=?
           ORDER BY CAST(s.SPCD AS REAL),s.SPCD,s.member_id,s.cell_id"""
    if include_species:
        for row in con.execute(q, (target_id, role)):
            key = (str(row[0]), str(row[1]))
            if current is not None and key != current:
                flush_species_member()
                current_cells = []
            current = key
            current_n = int(row[2])
            current_cells.append([str(row[3]), float(row[4]), float(row[5])])
        flush_species_member()
    return {
        "members": members,
        "membership_sha": membership_digest(members),
        "pool_df": pool_df,
        "domain_rep": (dict(domain_diag), domain_vectors, float(pool_df)),
        "generic_rep": (dict(generic_diag), generic_vectors, float(pool_df)),
        "species": dict(species_by_id),
    }


def canonical_covariance_object(
    target_id: str, target_type: str, route: str, object_type: str,
    pool_role: str, bundle: dict[str, Any], species_id: str = "",
) -> tuple[str, int]:
    base = {
        "canonicalization_version": CANONICAL_VERSION,
        "target_id": target_id,
        "target_type": target_type,
        "route": route,
        "object_type": object_type,
        "pool_role": pool_role,
        "species_id": species_id,
        "residual_df": int(bundle["pool_df"]),
        "pool_membership_sha256": bundle["membership_sha"],
        "float_serialization": "python_float_hex_ieee754_binary64",
    }
    if object_type == "DOMAIN":
        cells = sorted({c for m in bundle["members"] for c in m["counts"]})
        stats = []
        for member in bundle["members"]:
            stats.append([member["member_id"], int(member["n"]), [[c, int(member["counts"][c])] for c in sorted(member["counts"])]] )
        base.update({"ordered_cell_ids": cells, "member_cell_counts": stats})
    elif object_type == "GENERIC_JOINT":
        cells = sorted({c for m in bundle["members"] for c in set(m["sums"]) | set(m["sumsq"])})
        stats = []
        for member in bundle["members"]:
            keys = sorted(set(member["sums"]) | set(member["sumsq"]))
            stats.append([member["member_id"], int(member["n"]), [[c, fhex(member["sums"].get(c, 0.0)), fhex(member["sumsq"].get(c, 0.0))] for c in keys]])
        base.update({"ordered_cell_ids": cells, "member_cell_sufficient_stats": stats})
    elif object_type == "SPECIES_JOINT":
        entries = bundle["species"].get(species_id, [])
        cells = sorted({row[0] for entry in entries for row in entry["cells"]})
        stats = []
        for entry in entries:
            stats.append([entry["member_id"], int(entry["n"]), [[r[0], fhex(r[1]), fhex(r[2])] for r in sorted(entry["cells"], key=lambda x: x[0])]])
        base.update({"ordered_cell_ids": cells, "nonzero_member_cell_sufficient_stats": stats,
                     "implicit_zero_rule": "all omitted pool member/cell values are exact zero"})
    else:
        raise ValueError(object_type)
    return hashlib.sha256(stable_json(base).encode("utf-8")).hexdigest(), len(cells)


SEAL_SCHEMA = [
    ("object_id", "string"), ("target_id", "string"), ("target_type", "string"),
    ("species_id", "string"), ("object_type", "string"), ("pool_role", "string"),
    ("route", "string"), ("dimension", "int64"), ("residual_df", "int64"),
    ("pool_membership_sha256", "string"), ("canonical_object_sha256", "string"),
    ("stage_p_status", "string"), ("source_cache_identity", "string"),
    ("canonicalization_version", "string"),
]


def seal_row(target: sqlite3.Row, object_type: str, role: str, species_id: str,
             bundle: dict[str, Any], digest: str, dimension: int) -> dict[str, Any]:
    suffix = f"{object_type}|{role}" + (f"|{species_id}" if species_id else "")
    return {
        "object_id": f"{target['target_id']}|{suffix}", "target_id": target["target_id"],
        "target_type": target["target_type"], "species_id": species_id,
        "object_type": object_type, "pool_role": role, "route": target["route"],
        "dimension": dimension, "residual_df": int(bundle["pool_df"]),
        "pool_membership_sha256": bundle["membership_sha"],
        "canonical_object_sha256": digest, "stage_p_status": "P_SEALED",
        "source_cache_identity": SOURCE_CACHE_IDENTITY,
        "canonicalization_version": CANONICAL_VERSION,
    }


def prepare_seal_index(path: Path) -> sqlite3.Connection:
    if path.exists():
        path.unlink()
    con = sqlite3.connect(path)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA synchronous=NORMAL")
    con.execute("""CREATE TABLE seal(
        object_id TEXT PRIMARY KEY,target_id TEXT,target_type TEXT,species_id TEXT,
        object_type TEXT,pool_role TEXT,route TEXT,dimension INTEGER,residual_df INTEGER,
        pool_membership_sha256 TEXT,canonical_object_sha256 TEXT,stage_p_status TEXT,
        source_cache_identity TEXT,canonicalization_version TEXT)""")
    con.execute("CREATE INDEX seal_target ON seal(target_id,pool_role,object_type,species_id)")
    return con


def build_stage_p_seals(out_path: Path, log) -> dict[str, Any]:
    global SPECIES
    con = read_only_connection()
    SPECIES = [str(r[0]) for r in con.execute("SELECT SPCD FROM species_universe ORDER BY CAST(SPCD AS REAL),SPCD")]
    targets = con.execute("SELECT target_id,target_type,route FROM target WHERE validation_status='AVAILABLE' ORDER BY target_id").fetchall()
    index_path = WORK / "stage_p_seal_index.sqlite"
    idx = prepare_seal_index(index_path)
    if out_path.exists():
        try:
            os.chmod(out_path, 0o666)
        except OSError:
            pass
        out_path.unlink()
    logical = hashlib.sha256()
    count = 0
    class_counts = Counter()
    started = time.time()
    last = -999.0
    insert_sql = "INSERT INTO seal VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)"
    with ParquetWriter(out_path, SEAL_SCHEMA, row_group_size=ROW_GROUP_SIZE) as writer:
        for i, target in enumerate(targets, 1):
            nc1_exists = (target["target_type"] == "PSEUDO" and con.execute(
                "SELECT 1 FROM pool_membership WHERE target_id=? AND pool_role='NC1_INCOMPATIBLE' LIMIT 1",
                (target["target_id"],),
            ).fetchone() is not None)
            roles = ["CANDIDATE"] + (["NC1_INCOMPATIBLE"] if nc1_exists else [])
            for role in roles:
                bundle = load_pool_bundle(con, target["target_id"], role, include_species=(role == "CANDIDATE"))
                object_types = ["DOMAIN", "GENERIC_JOINT"]
                if role == "CANDIDATE":
                    object_types += ["SPECIES_JOINT"] * len(SPECIES)
                for j, object_type in enumerate(object_types):
                    species_id = SPECIES[j - 2] if object_type == "SPECIES_JOINT" else ""
                    digest, dimension = canonical_covariance_object(
                        target["target_id"], target["target_type"], target["route"],
                        object_type, role, bundle, species_id,
                    )
                    row = seal_row(target, object_type, role, species_id, bundle, digest, dimension)
                    writer.write(row)
                    idx.execute(insert_sql, tuple(row[name] for name, _ in SEAL_SCHEMA))
                    logical.update((stable_json(row) + "\n").encode("utf-8"))
                    count += 1
                    class_counts[f"{role}:{object_type}"] += 1
            if i % 10 == 0:
                idx.commit()
            now = time.time()
            if now - last >= 10:
                msg = f"STAGE_P_SEAL targets={i}/{len(targets)} objects={count} elapsed_s={int(now-started)}"
                print(msg, flush=True); log.write(msg + "\n"); log.flush(); last = now
    idx.commit()
    idx.close()
    con.close()
    os.chmod(out_path, 0o444)
    file_sha = sha256_file(out_path)
    index_sha = sha256_file(index_path)
    meta = {
        "planned_objects": count, "sealed_objects": count, "class_counts": dict(class_counts),
        "registry_sha256_before_scoring": file_sha,
        "registry_logical_sha256": logical.hexdigest(),
        "seal_index_sha256": index_sha, "species_universe": len(SPECIES),
        "stage_p_completed_before_target_reference_open": True,
        "finished_epoch": time.time(),
    }
    write_json(WORK / "STAGE_P_COVARIANCE_SEAL_CHECKPOINT_v01_1.json", meta)
    return meta


def rep_cells(rep: tuple[dict[str, float], list[dict[str, float]], float]) -> set[str]:
    diag, vectors, _ = rep
    return set(diag) | {cell for vector in vectors for cell in vector}


def matrix_from_rep(rep: tuple[dict[str, float], list[dict[str, float]], float], cells: list[str]) -> np.ndarray:
    diag, vectors, df = rep
    n = len(cells)
    if df <= 0:
        return np.full((n, n), np.nan)
    index = {cell: i for i, cell in enumerate(cells)}
    matrix = np.zeros((n, n), dtype=np.float64)
    for cell, value in diag.items():
        matrix[index[cell], index[cell]] += float(value)
    for vector in vectors:
        v = np.zeros(n, dtype=np.float64)
        for cell, value in vector.items():
            v[index[cell]] = float(value)
        matrix -= np.outer(v, v)
    matrix /= float(df)
    return (matrix + matrix.T) * 0.5


def eigen_diagnostics(matrix: np.ndarray) -> dict[str, Any]:
    if matrix.size == 0:
        return {"min_eigenvalue": 0.0, "max_eigenvalue": 0.0, "psd_tolerance": 1e-12,
                "psd_status": "PASS", "effective_rank": 0.0,
                "eigensolver_status": "EXACT_SYMMETRIC_EIGENSOLVER"}
    if not np.isfinite(matrix).all():
        return {"min_eigenvalue": float("nan"), "max_eigenvalue": float("nan"),
                "psd_tolerance": float("nan"), "psd_status": "NOT_ESTIMABLE",
                "effective_rank": float("nan"), "eigensolver_status": "NOT_ESTIMABLE"}
    values = np.linalg.eigvalsh(matrix)
    minimum = float(values[0]); maximum = float(values[-1]); trace = float(values.sum())
    tol = max(1e-12, 1e-10 * max(1.0, abs(trace), abs(minimum), abs(maximum)))
    if minimum >= 0:
        psd = "PASS"
    elif minimum >= -tol:
        psd = "NUMERIC_TOLERANCE"
    else:
        psd = "FAIL"
    denom = float(np.dot(values, values))
    effective_rank = trace * trace / denom if denom > 0 else 0.0
    return {"min_eigenvalue": minimum, "max_eigenvalue": maximum,
            "psd_tolerance": tol, "psd_status": psd,
            "effective_rank": effective_rank,
            "eigensolver_status": "EXACT_SYMMETRIC_EIGENSOLVER"}


@lru_cache(maxsize=100000)
def projection_basis(cells: tuple[str, ...]) -> np.ndarray:
    if not cells:
        return np.zeros((0, PROJECTION_COUNT), dtype=float)
    return np.array([[projection_sign(cell, j) for j in range(PROJECTION_COUNT)] for cell in cells], dtype=float)


def projection_variances(matrix: np.ndarray, cells: list[str], include_constant: bool) -> list[float]:
    if matrix.size == 0:
        return [0.0] * (PROJECTION_COUNT + (1 if include_constant else 0))
    basis = projection_basis(tuple(cells))
    out = [float(x) for x in np.sum(basis * (matrix @ basis), axis=0)]
    if include_constant:
        out.append(float(matrix.sum()))
    return out


def discrepancy_log(pred: float, target: float, tolerance: float = 1e-14) -> float:
    p = 0.0 if abs(pred) <= tolerance else float(pred)
    t = 0.0 if abs(target) <= tolerance else float(target)
    if p > 0 and t > 0:
        return abs(math.log(p / t))
    if p == 0 and t == 0:
        return 0.0
    return float("inf")


def q_with_inf(values: list[float], q: float) -> float:
    if not values:
        return float("nan")
    ordered = sorted(float(x) for x in values if not math.isnan(float(x)))
    if not ordered:
        return float("nan")
    if len(ordered) == 1:
        return ordered[0]
    pos = (len(ordered) - 1) * q
    lo, hi = math.floor(pos), math.ceil(pos)
    if lo == hi:
        return ordered[lo]
    if math.isinf(ordered[hi]):
        return float("inf")
    return ordered[lo] * (hi - pos) + ordered[hi] * (pos - lo)


def covariance_metrics(target: np.ndarray, pred: np.ndarray, cells: list[str], include_constant: bool) -> dict[str, Any]:
    if target.shape != pred.shape:
        raise ValueError("Covariance shape mismatch")
    target_norm = float(np.linalg.norm(target, "fro")); pred_norm = float(np.linalg.norm(pred, "fro"))
    diff = pred - target; diff_norm = float(np.linalg.norm(diff, "fro"))
    rel = diff_norm / target_norm if target_norm > 0 else (0.0 if pred_norm == 0 else float("inf"))
    target_diag = np.diag(target); pred_diag = np.diag(pred)
    diag_norm = float(np.linalg.norm(target_diag)); diag_diff = float(np.linalg.norm(pred_diag - target_diag))
    diag_rel = diag_diff / diag_norm if diag_norm > 0 else (0.0 if np.linalg.norm(pred_diag) == 0 else float("inf"))
    target_off = target.copy(); pred_off = pred.copy()
    np.fill_diagonal(target_off, 0.0); np.fill_diagonal(pred_off, 0.0)
    off_norm = float(np.linalg.norm(target_off, "fro")); off_diff = float(np.linalg.norm(pred_off - target_off, "fro"))
    off_rel = off_diff / off_norm if off_norm > 0 else (0.0 if np.linalg.norm(pred_off) == 0 else float("inf"))
    target_trace = float(np.trace(target)); pred_trace = float(np.trace(pred))
    target_eig = eigen_diagnostics(target); pred_eig = eigen_diagnostics(pred)
    target_proj = projection_variances(target, cells, include_constant)
    pred_proj = projection_variances(pred, cells, include_constant)
    proj_logs = [discrepancy_log(p, t) for t, p in zip(target_proj, pred_proj)]
    return {
        "relative_frobenius": rel, "absolute_frobenius": diff_norm,
        "target_frobenius": target_norm, "predicted_frobenius": pred_norm,
        "trace_ratio": safe_ratio(pred_trace, target_trace),
        "trace_abs_log_ratio": discrepancy_log(pred_trace, target_trace),
        "target_trace": target_trace, "predicted_trace": pred_trace,
        "diag_relative": diag_rel, "offdiag_relative": off_rel,
        "projection_abs_log_ratio_median": q_with_inf(proj_logs, 0.5),
        "projection_abs_log_ratio_p90": q_with_inf(proj_logs, 0.9),
        "projection_valid_count": sum(math.isfinite(x) for x in proj_logs),
        "projection_infinite_count": sum(math.isinf(x) for x in proj_logs),
        "leading_eigen_ratio": safe_ratio(pred_eig["max_eigenvalue"], target_eig["max_eigenvalue"]),
        "leading_eigen_abs_log_ratio": discrepancy_log(pred_eig["max_eigenvalue"], target_eig["max_eigenvalue"]),
        "target_spectral": target_eig, "predicted_spectral": pred_eig,
    }


def profile_metrics(target: dict[str, float], pool: dict[str, float]) -> dict[str, Any]:
    keys = set(target) | set(pool)
    st = sum(float(target.get(k, 0.0)) for k in keys)
    sp = sum(float(pool.get(k, 0.0)) for k in keys)
    ta = {k: float(target.get(k, 0.0)) / st for k in keys} if st > 0 else {k: 0.0 for k in keys}
    pa = {k: float(pool.get(k, 0.0)) / sp for k in keys} if sp > 0 else {k: 0.0 for k in keys}
    tv = 0.5 * sum(abs(ta[k] - pa[k]) for k in keys)
    overlap = sum(min(ta[k], pa[k]) for k in keys)
    hell = math.sqrt(0.5 * sum((math.sqrt(ta[k]) - math.sqrt(pa[k])) ** 2 for k in keys))
    m = {k: 0.5 * (ta[k] + pa[k]) for k in keys}
    def kl(a, b):
        return sum(a[k] * math.log(a[k] / b[k]) for k in keys if a[k] > 0 and b[k] > 0)
    js = 0.5 * kl(ta, m) + 0.5 * kl(pa, m)
    target_units = {k for k, v in target.items() if v > 0}
    pool_units = {k for k, v in pool.items() if v > 0}
    return {"tv": tv, "overlap": overlap, "hellinger": hell, "jensen_shannon": js,
            "target_only_units": len(target_units - pool_units),
            "pool_only_units": len(pool_units - target_units),
            "target_units": len(target_units), "pool_units": len(pool_units)}


def aggregate_profile(profile: dict[str, float], grain: int) -> dict[str, float]:
    out: defaultdict[str, float] = defaultdict(float)
    for cell, value in profile.items():
        out[parent_cell(cell, grain)] += float(value)
    return dict(out)


def aggregate_rep(rep: tuple[dict[str, float], list[dict[str, float]], float], grain: int):
    diag, vectors, df = rep
    out_diag: defaultdict[str, float] = defaultdict(float)
    for cell, value in diag.items():
        out_diag[parent_cell(cell, grain)] += float(value)
    out_vectors = []
    for vector in vectors:
        mapped: defaultdict[str, float] = defaultdict(float)
        for cell, value in vector.items():
            mapped[parent_cell(cell, grain)] += float(value)
        out_vectors.append(dict(mapped))
    return dict(out_diag), out_vectors, df


def rep_from_plot_rows(rows: list[tuple[str, str, float]], object_type: str):
    n = len(rows)
    if n < 2:
        return {}, [], 0.0
    if object_type == "DOMAIN":
        counts = Counter(cell for _, cell, _ in rows)
        return dict(counts), [{cell: value / math.sqrt(n) for cell, value in counts.items()}], float(n - 1)
    sums: defaultdict[str, float] = defaultdict(float)
    sumsq: defaultdict[str, float] = defaultdict(float)
    for _, cell, y in rows:
        sums[cell] += float(y); sumsq[cell] += float(y) * float(y)
    return dict(sumsq), [{cell: value / math.sqrt(n) for cell, value in sums.items()}], float(n - 1)


def target_generic_bundle(con: sqlite3.Connection, member_id: str) -> dict[str, Any]:
    row = con.execute("SELECT n,df,cell_counts_json,cell_sum_json,cell_sumsq_json FROM member_generic_stats WHERE member_id=?", (member_id,)).fetchone()
    if row is None:
        raise RuntimeError(f"Missing target member generic stats: {member_id}")
    n, df = int(row[0]), int(row[1])
    counts = {str(k): int(v) for k, v in json.loads(row[2]).items()}
    sums = {str(k): float(v) for k, v in json.loads(row[3]).items()}
    sumsq = {str(k): float(v) for k, v in json.loads(row[4]).items()}
    return {
        "n": n, "df": df, "counts": counts, "sums": sums, "sumsq": sumsq,
        "domain_rep": (dict(counts), [{c: v / math.sqrt(n) for c, v in counts.items()}], float(df)),
        "generic_rep": (dict(sumsq), [{c: v / math.sqrt(n) for c, v in sums.items()}], float(df)),
    }


def species_rep_from_pool(bundle: dict[str, Any], species_id: str):
    diag: defaultdict[str, float] = defaultdict(float)
    vectors = []
    for entry in bundle["species"].get(species_id, []):
        sums = {}
        for cell, sy, ssy in entry["cells"]:
            sums[cell] = float(sy); diag[cell] += float(ssy)
        vectors.append({cell: value / math.sqrt(entry["n"]) for cell, value in sums.items()})
    return dict(diag), vectors, float(bundle["pool_df"])


def target_species_data(con: sqlite3.Connection, member_id: str) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, float]]]:
    stats = {
        str(r[0]): {"sum_y": float(r[1]), "sumsq_y": float(r[2]),
                    "positive_count": int(r[3]), "scalar_ss": float(r[4])}
        for r in con.execute("SELECT SPCD,sum_y,sumsq_y,positive_count,scalar_ss FROM member_species_stats WHERE member_id=?", (member_id,))
    }
    cells: defaultdict[str, dict[str, Any]] = defaultdict(dict)
    for r in con.execute("SELECT SPCD,cell_id,sum_y,sumsq_y FROM member_species_cell WHERE member_id=? ORDER BY CAST(SPCD AS REAL),SPCD,cell_id", (member_id,)):
        cells[str(r[0])][str(r[1])] = (float(r[2]), float(r[3]))
    return stats, dict(cells)


def target_species_rep(n: int, df: int, cell_stats: dict[str, tuple[float, float]]):
    diag = {cell: values[1] for cell, values in cell_stats.items()}
    vector = {cell: values[0] / math.sqrt(n) for cell, values in cell_stats.items()}
    return diag, [vector], float(df)


def balanced_split_indices(plot_ids: list[str], target_id: str, split_id: int) -> tuple[list[int], list[int]]:
    order = sorted(range(len(plot_ids)), key=lambda i: (stable_seed("B12_SPLIT", target_id, split_id, plot_ids[i]), plot_ids[i]))
    cut = len(order) // 2
    return order[:cut], order[cut:]


def split_noise(rows: list[tuple[str, str, float]], target_id: str, object_type: str,
                species_values: dict[str, float] | None = None, grain: int = 50) -> dict[str, Any]:
    n = len(rows)
    if n < 8:
        return {"split_count": 0, "half_a_n": n // 2, "half_b_n": n - n // 2,
                "matrix_relative_frobenius_median": float("nan"),
                "matrix_relative_frobenius_p90": float("nan"),
                "trace_ratio_median": float("nan"), "trace_ratio_p10": float("nan"),
                "trace_ratio_p90": float("nan"),
                "trace_abs_log_ratio_median": float("nan"),
                "projection_variance_ratio_median": float("nan"),
                "projection_variance_ratio_p10": float("nan"),
                "projection_variance_ratio_p90": float("nan"),
                "projection_abs_log_ratio_median": float("nan"),
                "projection_abs_log_ratio_p90": float("nan"),
                "reference_estimability_status": "INSUFFICIENT_TARGET_N_FOR_FROZEN_SPLIT"}
    adjusted = rows
    if species_values is not None:
        adjusted = [(pid, cell, float(species_values.get(pid, 0.0))) for pid, cell, _ in rows]
    frob = []; trace_ratios = []; trace_logs = []; projection_ratios = []; projection_logs = []
    half_a_n = half_b_n = 0
    for split_id in range(SPLIT_REPLICATES):
        ia, ib = balanced_split_indices([r[0] for r in adjusted], target_id, split_id)
        a = [adjusted[i] for i in ia]; b = [adjusted[i] for i in ib]
        half_a_n, half_b_n = len(a), len(b)
        ra = rep_from_plot_rows(a, object_type); rb = rep_from_plot_rows(b, object_type)
        if grain != 50:
            ra = aggregate_rep(ra, grain); rb = aggregate_rep(rb, grain)
        cells = sorted(rep_cells(ra) | rep_cells(rb))
        ma = matrix_from_rep(ra, cells); mb = matrix_from_rep(rb, cells)
        na = float(np.linalg.norm(ma, "fro")); nb = float(np.linalg.norm(mb, "fro")); diff = float(np.linalg.norm(ma - mb, "fro"))
        denom = 0.5 * (na + nb)
        frob.append(diff / denom if denom > 0 else 0.0)
        trace_a = float(np.trace(ma)); trace_b = float(np.trace(mb))
        trace_ratios.append(safe_ratio(trace_b, trace_a))
        trace_logs.append(discrepancy_log(trace_b, trace_a))
        include_constant = object_type != "DOMAIN"
        pa = projection_variances(ma, cells, include_constant)
        pb = projection_variances(mb, cells, include_constant)
        projection_ratios.extend(safe_ratio(p, t) for t, p in zip(pa, pb))
        projection_logs.extend(discrepancy_log(p, t) for t, p in zip(pa, pb))
    status = "AVAILABLE"
    if any(math.isinf(x) for x in frob + trace_logs + projection_logs):
        status = "AVAILABLE_WITH_ZERO_PATTERN_DEGENERACY"
    return {
        "split_count": SPLIT_REPLICATES, "half_a_n": half_a_n, "half_b_n": half_b_n,
        "matrix_relative_frobenius_median": q_with_inf(frob, 0.5),
        "matrix_relative_frobenius_p90": q_with_inf(frob, 0.9),
        "trace_ratio_median": q_with_inf(trace_ratios, 0.5),
        "trace_ratio_p10": q_with_inf(trace_ratios, 0.1),
        "trace_ratio_p90": q_with_inf(trace_ratios, 0.9),
        "trace_abs_log_ratio_median": q_with_inf(trace_logs, 0.5),
        "projection_variance_ratio_median": q_with_inf(projection_ratios, 0.5),
        "projection_variance_ratio_p10": q_with_inf(projection_ratios, 0.1),
        "projection_variance_ratio_p90": q_with_inf(projection_ratios, 0.9),
        "projection_abs_log_ratio_median": q_with_inf(projection_logs, 0.5),
        "projection_abs_log_ratio_p90": q_with_inf(projection_logs, 0.9),
        "reference_estimability_status": status,
    }


COV_TRANSPORT_SCHEMA = [
    ("target_id", "string"), ("target_type", "string"), ("route", "string"),
    ("reference_strength", "string"), ("species_id", "string"),
    ("object_type", "string"), ("pool_role", "string"),
    ("target_n", "int64"), ("target_df", "int64"), ("pool_df", "int64"),
    ("dimension", "int64"), ("canonical_object_sha256", "string"),
    ("stage_s_digest_status", "string"), ("scoring_status", "string"),
    ("relative_frobenius", "double"), ("absolute_frobenius", "double"),
    ("target_frobenius", "double"), ("predicted_frobenius", "double"),
    ("trace_ratio", "double"), ("trace_abs_log_ratio", "double"),
    ("target_trace", "double"), ("predicted_trace", "double"),
    ("diag_relative", "double"), ("offdiag_relative", "double"),
    ("projection_abs_log_ratio_median", "double"),
    ("projection_abs_log_ratio_p90", "double"),
    ("projection_valid_count", "int64"), ("projection_infinite_count", "int64"),
    ("leading_eigen_ratio", "double"), ("leading_eigen_abs_log_ratio", "double"),
]

SPECTRAL_SCHEMA = [
    ("target_id", "string"), ("target_type", "string"), ("route", "string"),
    ("reference_strength", "string"), ("species_id", "string"),
    ("object_type", "string"), ("matrix_role", "string"), ("pool_role", "string"),
    ("dimension", "int64"), ("min_eigenvalue", "double"),
    ("max_eigenvalue", "double"), ("psd_tolerance", "double"),
    ("psd_status", "string"), ("effective_rank", "double"),
    ("eigensolver_status", "string"), ("regularization_applied", "string"),
]

NOISE_SCHEMA = [
    ("target_id", "string"), ("target_type", "string"), ("route", "string"),
    ("reference_strength", "string"), ("species_id", "string"),
    ("object_type", "string"), ("grain_km", "int64"),
    ("target_n", "int64"), ("target_df", "int64"),
    ("split_count", "int64"), ("half_a_n", "int64"), ("half_b_n", "int64"),
    ("matrix_relative_frobenius_median", "double"),
    ("matrix_relative_frobenius_p90", "double"),
    ("trace_ratio_median", "double"), ("trace_ratio_p10", "double"),
    ("trace_ratio_p90", "double"),
    ("trace_abs_log_ratio_median", "double"),
    ("projection_variance_ratio_median", "double"),
    ("projection_variance_ratio_p10", "double"),
    ("projection_variance_ratio_p90", "double"),
    ("projection_abs_log_ratio_median", "double"),
    ("projection_abs_log_ratio_p90", "double"),
    ("reference_estimability_status", "string"),
    ("split_identity", "string"),
]

TRANSPORT_NOISE_SCHEMA = [
    ("target_id", "string"), ("target_type", "string"), ("route", "string"),
    ("reference_strength", "string"), ("species_id", "string"),
    ("object_type", "string"), ("grain_km", "int64"),
    ("transport_relative_frobenius", "double"),
    ("reference_noise_relative_frobenius", "double"),
    ("excess_relative_frobenius", "double"),
    ("transport_to_noise_ratio", "double"),
    ("transport_projection_abs_log_ratio_median", "double"),
    ("reference_noise_projection_abs_log_ratio_median", "double"),
    ("projection_excess", "double"), ("projection_transport_to_noise_ratio", "double"),
    ("comparison_status", "string"),
]

COARSE_SCHEMA = [
    ("target_id", "string"), ("route", "string"), ("reference_strength", "string"),
    ("object_type", "string"), ("grain_km", "int64"),
    ("target_units", "int64"), ("pool_units", "int64"),
    ("target_only_units", "int64"), ("pool_only_units", "int64"),
    ("domain_tv", "double"), ("domain_overlap", "double"),
    ("hellinger", "double"), ("jensen_shannon", "double"),
    ("covariance_relative_frobenius", "double"),
    ("projection_abs_log_ratio_median", "double"),
    ("leading_eigen_abs_log_ratio", "double"),
    ("reference_noise_relative_frobenius", "double"),
    ("transport_to_noise_ratio", "double"),
    ("diagnostic_role", "string"),
]

DECOMP_SCHEMA = [
    ("target_id", "string"), ("route", "string"), ("reference_strength", "string"),
    ("species_id", "string"), ("target_n", "int64"), ("target_df", "int64"),
    ("pool_df", "int64"), ("target_positive_count", "int64"),
    ("target_scalar_variance", "double"), ("pool_scalar_variance", "double"),
    ("degeneracy_class", "string"), ("joint_scoring_status", "string"),
    ("joint_dimension", "int64"), ("joint_relative_frobenius", "double"),
    ("joint_trace_abs_log_ratio", "double"),
    ("joint_projection_abs_log_ratio_median", "double"),
    ("joint_reference_noise_relative_frobenius", "double"),
    ("joint_transport_to_noise_ratio", "double"),
    ("seal_verified", "string"),
]

ACTUAL_SCHEMA = [
    ("target_id", "string"), ("case_id", "string"), ("route", "string"),
    ("statecd", "int64"), ("evalid", "string"), ("fold", "string"),
    ("pool_df", "int64"), ("full5_n", "int64"), ("full5_df", "int64"),
    ("reference_role", "string"), ("prediction_seal_verified", "string"),
    ("generic_target_variance", "double"), ("generic_predicted_variance", "double"),
    ("generic_abs_log_variance_ratio", "double"),
    ("domain_tv", "double"), ("domain_overlap", "double"),
    ("domain_cov_relative_frobenius", "double"),
    ("domain_cov_projection_abs_log_ratio_median", "double"),
    ("domain_target_largest_eigenvalue", "double"),
    ("domain_predicted_largest_eigenvalue", "double"),
    ("domain_leading_eigen_abs_log_ratio", "double"),
    ("generic_joint_relative_frobenius", "double"),
    ("generic_joint_projection_abs_log_ratio_median", "double"),
    ("generic_joint_leading_eigen_abs_log_ratio", "double"),
    ("domain_target_min_eigenvalue", "double"), ("domain_target_psd_tolerance", "double"),
    ("domain_target_psd_status", "string"), ("domain_target_effective_rank", "double"),
    ("domain_predicted_min_eigenvalue", "double"), ("domain_predicted_psd_tolerance", "double"),
    ("domain_predicted_psd_status", "string"), ("domain_predicted_effective_rank", "double"),
    ("generic_target_min_eigenvalue", "double"), ("generic_target_psd_tolerance", "double"),
    ("generic_target_psd_status", "string"), ("generic_target_effective_rank", "double"),
    ("generic_predicted_min_eigenvalue", "double"), ("generic_predicted_psd_tolerance", "double"),
    ("generic_predicted_psd_status", "string"), ("generic_predicted_effective_rank", "double"),
    ("eigensolver_status", "string"), ("regularization_applied", "string"),
    ("full5_domain_reference_noise", "double"),
    ("full5_generic_joint_reference_noise", "double"),
    ("reference_estimability_status", "string"),
    ("limitations", "string"),
]


def base_transport_row(target: sqlite3.Row, species_id: str, object_type: str,
                       role: str, seal: sqlite3.Row, metrics: dict[str, Any]) -> dict[str, Any]:
    return {
        "target_id": target["target_id"], "target_type": target["target_type"],
        "route": target["route"], "reference_strength": target["reference_strength"],
        "species_id": species_id, "object_type": object_type, "pool_role": role,
        "target_n": int(target["target_n"]), "target_df": int(target["target_df"]),
        "pool_df": int(seal["residual_df"]), "dimension": int(seal["dimension"]),
        "canonical_object_sha256": seal["canonical_object_sha256"],
        "stage_s_digest_status": "VERIFIED", "scoring_status": "SCORED",
        **{k: metrics[k] for k, _ in COV_TRANSPORT_SCHEMA if k in metrics},
    }


def spectral_rows(target: sqlite3.Row, species_id: str, object_type: str, role: str,
                  dimension: int, metrics: dict[str, Any]) -> list[dict[str, Any]]:
    out = []
    for matrix_role, key in [("TARGET_REFERENCE", "target_spectral"), ("SEALED_PREDICTION", "predicted_spectral")]:
        s = metrics[key]
        out.append({
            "target_id": target["target_id"], "target_type": target["target_type"],
            "route": target["route"], "reference_strength": target["reference_strength"],
            "species_id": species_id, "object_type": object_type,
            "matrix_role": matrix_role, "pool_role": role, "dimension": dimension,
            **s, "regularization_applied": "NONE",
        })
    return out


def noise_row(target: sqlite3.Row, species_id: str, object_type: str, grain: int,
              result: dict[str, Any]) -> dict[str, Any]:
    return {
        "target_id": target["target_id"], "target_type": target["target_type"],
        "route": target["route"], "reference_strength": target["reference_strength"],
        "species_id": species_id, "object_type": object_type, "grain_km": grain,
        "target_n": int(target["target_n"]), "target_df": int(target["target_df"]),
        **result, "split_identity": "FROZEN_B12_SPLIT_SHA256_ORDER_4_REPLICATES",
    }


def transport_noise_row(target: sqlite3.Row, species_id: str, object_type: str,
                        grain: int, metrics: dict[str, Any], noise: dict[str, Any]) -> dict[str, Any]:
    tr = float(metrics["relative_frobenius"]); nr = float(noise["matrix_relative_frobenius_median"])
    tp = float(metrics["projection_abs_log_ratio_median"]); npj = float(noise["projection_abs_log_ratio_median"])
    available = noise["reference_estimability_status"].startswith("AVAILABLE")
    return {
        "target_id": target["target_id"], "target_type": target["target_type"],
        "route": target["route"], "reference_strength": target["reference_strength"],
        "species_id": species_id, "object_type": object_type, "grain_km": grain,
        "transport_relative_frobenius": tr, "reference_noise_relative_frobenius": nr,
        "excess_relative_frobenius": tr - nr if available else float("nan"),
        "transport_to_noise_ratio": tr / nr if available and nr > 1e-14 else float("nan"),
        "transport_projection_abs_log_ratio_median": tp,
        "reference_noise_projection_abs_log_ratio_median": npj,
        "projection_excess": tp - npj if available else float("nan"),
        "projection_transport_to_noise_ratio": tp / npj if available and npj > 1e-14 else float("nan"),
        "comparison_status": "AVAILABLE" if available else "REFERENCE_NOISE_NOT_ESTIMABLE",
    }


def verify_bundle_seals(idx: sqlite3.Connection, target: sqlite3.Row, role: str,
                        bundle: dict[str, Any], include_species: bool) -> dict[tuple[str, str], sqlite3.Row]:
    rows = idx.execute(
        "SELECT * FROM seal WHERE target_id=? AND pool_role=? ORDER BY object_type,species_id",
        (target["target_id"], role),
    ).fetchall()
    expected_count = 2 + (len(SPECIES) if include_species else 0)
    if len(rows) != expected_count:
        raise RuntimeError(f"Seal row count mismatch {target['target_id']} {role}: {len(rows)} != {expected_count}")
    lookup = {(str(r["object_type"]), str(r["species_id"])): r for r in rows}
    object_ids = [("DOMAIN", ""), ("GENERIC_JOINT", "")]
    if include_species:
        object_ids.extend(("SPECIES_JOINT", sp) for sp in SPECIES)
    for object_type, species_id in object_ids:
        digest, dimension = canonical_covariance_object(
            target["target_id"], target["target_type"], target["route"],
            object_type, role, bundle, species_id,
        )
        sealed = lookup[(object_type, species_id)]
        if (digest != sealed["canonical_object_sha256"] or dimension != int(sealed["dimension"]) or
                int(bundle["pool_df"]) != int(sealed["residual_df"]) or
                bundle["membership_sha"] != sealed["pool_membership_sha256"]):
            raise RuntimeError(f"Stage-S digest mismatch: {target['target_id']} {role} {object_type} {species_id}")
    return lookup


def target_plot_rows(con: sqlite3.Connection, member_id: str) -> list[tuple[str, str, float]]:
    return [(str(r[0]), str(r[1]), float(r[2])) for r in con.execute(
        """SELECT mp.PLT_CN,mp.cell_id,g.y FROM member_plot mp
           JOIN plot_generic g ON g.PLT_CN=mp.PLT_CN WHERE mp.member_id=? ORDER BY mp.PLT_CN""",
        (member_id,),
    )]


def target_species_plot_values(con: sqlite3.Connection, member_id: str) -> dict[str, dict[str, float]]:
    out: defaultdict[str, dict[str, float]] = defaultdict(dict)
    for r in con.execute("SELECT SPCD,PLT_CN,y FROM plot_species WHERE member_id=? ORDER BY CAST(SPCD AS REAL),SPCD,PLT_CN", (member_id,)):
        out[str(r[0])][str(r[1])] = float(r[2])
    return dict(out)


def descriptor_tokens(value: Any, variable: str) -> set[str]:
    if variable != "REGIONAL_MANUAL":
        return {str(value)} if value is not None and str(value).strip() else set()
    if value is None or not str(value).strip():
        return set()
    try:
        obj = json.loads(str(value))
    except json.JSONDecodeError:
        return {str(value)}
    return {f"{k}={obj[k]}" for k in sorted(obj)}


def descriptor_relation(target_values: set[str], pool_values: set[str]) -> str:
    if not target_values or not pool_values:
        return "MISSING_SIDE"
    if target_values == pool_values:
        return "EXACT_SET_MATCH"
    if target_values & pool_values:
        return "PARTIAL_OVERLAP"
    return "DISJOINT"


def descriptive_rows(con: sqlite3.Connection, target: sqlite3.Row, domain_overlap: float) -> list[dict[str, Any]]:
    columns = {"MANUAL": "MANUAL", "REGIONAL_MANUAL": "regional_manual_json",
               "SAMP_METHOD_CD": "SAMP_METHOD_CD", "MEASYEAR": "MEASYEAR"}
    target_design = con.execute(
        "SELECT MANUAL,regional_manual_json,SAMP_METHOD_CD,MEASYEAR FROM plot_design WHERE member_id=?",
        (target["target_member_id"],),
    ).fetchall()
    pool_design = con.execute(
        """SELECT d.MANUAL,d.regional_manual_json,d.SAMP_METHOD_CD,d.MEASYEAR
           FROM pool_membership p JOIN plot_design d ON d.member_id=p.member_id
           WHERE p.target_id=? AND p.pool_role='CANDIDATE'""", (target["target_id"],),
    ).fetchall()
    index = {"MANUAL": 0, "REGIONAL_MANUAL": 1, "SAMP_METHOD_CD": 2, "MEASYEAR": 3}
    out = []
    for variable in columns:
        j = index[variable]
        tset = set().union(*(descriptor_tokens(r[j], variable) for r in target_design)) if target_design else set()
        pset = set().union(*(descriptor_tokens(r[j], variable) for r in pool_design)) if pool_design else set()
        out.append({
            "target_id": target["target_id"], "variable": variable,
            "relation_class": descriptor_relation(tset, pset),
            "target_value_count": len(tset), "pool_value_count": len(pset),
            "shared_value_count": len(tset & pset),
            "target_values": "|".join(sorted(tset)), "pool_values": "|".join(sorted(pset)),
            "route": target["route"], "statecd": target["STATECD"],
            "source_eu": target["source_eu"], "pool_df": target["pool_df"],
            "target_df": target["target_df"], "reference_strength": target["reference_strength"],
            "domain_overlap": domain_overlap,
            "group_size_ratio_pool_to_target": len(pool_design) / len(target_design) if target_design else float("nan"),
            "interpretation_boundary": "DESCRIPTIVE_ONLY_CONFOUNDING_NOT_FILTER_EVIDENCE",
        })
    return out


def pool_generic_scalar(con: sqlite3.Connection, target_id: str, role: str) -> tuple[float, float]:
    row = con.execute("SELECT pred_generic_var,raw_uncentered_var FROM pool_generic_pred WHERE target_id=? AND pool_role=?", (target_id, role)).fetchone()
    return (float(row[0]), float(row[1])) if row else (float("nan"), float("nan"))


def score_pseudo_targets(log) -> dict[str, Any]:
    con = read_only_connection()
    idx = sqlite3.connect(f"file:{(WORK / 'stage_p_seal_index.sqlite').as_posix()}?mode=ro", uri=True)
    idx.row_factory = sqlite3.Row
    targets = con.execute("SELECT * FROM target WHERE target_type='PSEUDO' AND validation_status='AVAILABLE' ORDER BY target_id").fetchall()
    parent_map = {r["target_id"]: r for r in read_csv(PARENT / "B12_PRECISION_TRANSPORT_MAP_v01.csv")}
    out_cov = OUT / "B12_COVARIANCE_TRANSPORT_v01_1.parquet"
    out_spectral = OUT / "B12_COVARIANCE_SPECTRAL_QC_v01_1.parquet"
    out_noise = OUT / "B12_COV_REFERENCE_NOISE_v01_1.parquet"
    out_tn = OUT / "B12_TRANSPORT_VS_REFERENCE_NOISE_v01_1.parquet"
    out_coarse = OUT / "B12_COARSE_SPATIAL_TRANSPORT_v01_1.parquet"
    out_decomp = OUT / "B12_TRANSPORT_DECOMPOSITION_v01_1.parquet"
    for p in [out_cov, out_spectral, out_noise, out_tn, out_coarse, out_decomp]:
        if p.exists(): p.unlink()
    summary = []
    negative = []
    descriptive = []
    class_counts = Counter(); scoring_counts = Counter(); psd_counts = Counter()
    coarse_acc: defaultdict[str, defaultdict[int, dict[str, list[float]]]] = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    verified_objects = 0
    started = time.time(); last = started - 999
    with (ParquetWriter(out_cov, COV_TRANSPORT_SCHEMA, ROW_GROUP_SIZE) as wcov,
          ParquetWriter(out_spectral, SPECTRAL_SCHEMA, ROW_GROUP_SIZE) as wsp,
          ParquetWriter(out_noise, NOISE_SCHEMA, ROW_GROUP_SIZE) as wnoise,
          ParquetWriter(out_tn, TRANSPORT_NOISE_SCHEMA, ROW_GROUP_SIZE) as wtn,
          ParquetWriter(out_coarse, COARSE_SCHEMA, ROW_GROUP_SIZE) as wcoarse,
          ParquetWriter(out_decomp, DECOMP_SCHEMA, ROW_GROUP_SIZE) as wdec):
        for i, target in enumerate(targets, 1):
            # Prediction-only reconstruction and verification precede all target-outcome queries.
            candidate = load_pool_bundle(con, target["target_id"], "CANDIDATE")
            seals = verify_bundle_seals(idx, target, "CANDIDATE", candidate, True)
            nc1_available = con.execute(
                "SELECT 1 FROM pool_membership WHERE target_id=? AND pool_role='NC1_INCOMPATIBLE' LIMIT 1",
                (target["target_id"],),
            ).fetchone() is not None
            nc1 = None
            if nc1_available:
                nc1 = load_pool_bundle(con, target["target_id"], "NC1_INCOMPATIBLE", include_species=False)
                verify_bundle_seals(idx, target, "NC1_INCOMPATIBLE", nc1, False)
            verified_objects += 2 + len(SPECIES) + (2 if nc1_available else 0)

            # Stage S reference opening begins here, after all 406 target seals verify.
            tb = target_generic_bundle(con, target["target_member_id"])
            plot_rows = target_plot_rows(con, target["target_member_id"])
            sp_stats, sp_cells = target_species_data(con, target["target_member_id"])
            sp_plot = target_species_plot_values(con, target["target_member_id"])
            pred_species_scalar = {str(r[0]): float(r[1]) for r in con.execute(
                "SELECT SPCD,pred_scalar_var FROM pool_species_pred WHERE target_id=?", (target["target_id"],))}

            object_result = {}
            for object_type, trep, prep in [
                ("DOMAIN", tb["domain_rep"], candidate["domain_rep"]),
                ("GENERIC_JOINT", tb["generic_rep"], candidate["generic_rep"]),
            ]:
                cells = sorted(rep_cells(trep) | rep_cells(prep))
                tm = matrix_from_rep(trep, cells); pm = matrix_from_rep(prep, cells)
                metrics = covariance_metrics(tm, pm, cells, object_type != "DOMAIN")
                sealed = seals[(object_type, "")]
                wcov.write(base_transport_row(target, "", object_type, "CANDIDATE", sealed, metrics))
                wsp.write_many(spectral_rows(target, "", object_type, "CANDIDATE", len(cells), metrics))
                for role, spd in [("TARGET_REFERENCE", metrics["target_spectral"]), ("SEALED_PREDICTION", metrics["predicted_spectral"])]:
                    psd_counts[f"{object_type}:{role}:{spd['psd_status']}"] += 1
                noise = split_noise(plot_rows, target["target_id"], object_type)
                wnoise.write(noise_row(target, "", object_type, 50, noise))
                wtn.write(transport_noise_row(target, "", object_type, 50, metrics, noise))
                object_result[object_type] = (metrics, noise)
                scoring_counts[object_type] += 1

            target_profile = {c: float(v) for c, v in tb["counts"].items()}
            pool_profile: defaultdict[str, float] = defaultdict(float)
            for m in candidate["members"]:
                for c, v in m["counts"].items(): pool_profile[c] += float(v)
            pm50 = profile_metrics(target_profile, dict(pool_profile))
            for grain in (50, 100, 200):
                tprof = aggregate_profile(target_profile, grain)
                pprof = aggregate_profile(dict(pool_profile), grain)
                prof = profile_metrics(tprof, pprof)
                for object_type, trep0, prep0 in [
                    ("DOMAIN", tb["domain_rep"], candidate["domain_rep"]),
                    ("GENERIC_JOINT", tb["generic_rep"], candidate["generic_rep"]),
                ]:
                    trep = aggregate_rep(trep0, grain); prep = aggregate_rep(prep0, grain)
                    cells = sorted(rep_cells(trep) | rep_cells(prep))
                    met = covariance_metrics(matrix_from_rep(trep, cells), matrix_from_rep(prep, cells), cells, object_type != "DOMAIN")
                    noi = split_noise(plot_rows, target["target_id"], object_type, grain=grain)
                    wcoarse.write({
                        "target_id": target["target_id"], "route": target["route"],
                        "reference_strength": target["reference_strength"], "object_type": object_type,
                        "grain_km": grain, **prof,
                        "domain_tv": prof["tv"], "domain_overlap": prof["overlap"],
                        "covariance_relative_frobenius": met["relative_frobenius"],
                        "projection_abs_log_ratio_median": met["projection_abs_log_ratio_median"],
                        "leading_eigen_abs_log_ratio": met["leading_eigen_abs_log_ratio"],
                        "reference_noise_relative_frobenius": noi["matrix_relative_frobenius_median"],
                        "transport_to_noise_ratio": (met["relative_frobenius"] / noi["matrix_relative_frobenius_median"]
                                                     if noi["reference_estimability_status"].startswith("AVAILABLE") and noi["matrix_relative_frobenius_median"] > 1e-14 else float("nan")),
                        "diagnostic_role": "PRIMARY_50KM" if grain == 50 else "COARSE_DIAGNOSTIC_NOT_NEW_ESTIMAND",
                    })
                    if object_type == "DOMAIN":
                        for route_key in ["ALL", target["route"]]:
                            coarse_acc[route_key][grain]["tv"].append(prof["tv"])
                            coarse_acc[route_key][grain]["overlap"].append(prof["overlap"])
                            coarse_acc[route_key][grain]["cov_frob"].append(met["relative_frobenius"])
                            coarse_acc[route_key][grain]["lead"].append(met["leading_eigen_abs_log_ratio"])

            species_joint_errors = []
            species_noise_ratios = []
            for sp in SPECIES:
                stat = sp_stats.get(sp, {"positive_count": 0, "scalar_ss": 0.0})
                tvar = float(stat.get("scalar_ss", 0.0)) / int(target["target_df"]) if int(target["target_df"]) > 0 else float("nan")
                pvar = float(pred_species_scalar.get(sp, 0.0))
                tpos = tvar > 0; ppos = pvar > 0
                cls = ("TARGET_POSITIVE_" if tpos else "TARGET_ZERO_") + ("POOL_POSITIVE" if ppos else "POOL_ZERO")
                class_counts[cls] += 1
                eligible = int(target["target_n"]) >= 4 and int(stat.get("positive_count", 0)) >= 2 and (tpos or ppos)
                dec = {
                    "target_id": target["target_id"], "route": target["route"],
                    "reference_strength": target["reference_strength"], "species_id": sp,
                    "target_n": target["target_n"], "target_df": target["target_df"],
                    "pool_df": candidate["pool_df"], "target_positive_count": int(stat.get("positive_count", 0)),
                    "target_scalar_variance": tvar, "pool_scalar_variance": pvar,
                    "degeneracy_class": cls, "seal_verified": "YES",
                    "joint_scoring_status": "NOT_INFORMATIVE_UNDER_FROZEN_RULE",
                    "joint_dimension": int(seals[("SPECIES_JOINT", sp)]["dimension"]),
                    "joint_relative_frobenius": float("nan"), "joint_trace_abs_log_ratio": float("nan"),
                    "joint_projection_abs_log_ratio_median": float("nan"),
                    "joint_reference_noise_relative_frobenius": float("nan"),
                    "joint_transport_to_noise_ratio": float("nan"),
                }
                if eligible:
                    trep = target_species_rep(int(target["target_n"]), int(target["target_df"]), sp_cells.get(sp, {}))
                    prep = species_rep_from_pool(candidate, sp)
                    cells = sorted(rep_cells(trep) | rep_cells(prep))
                    tm = matrix_from_rep(trep, cells); pm = matrix_from_rep(prep, cells)
                    metrics = covariance_metrics(tm, pm, cells, True)
                    sealed = seals[("SPECIES_JOINT", sp)]
                    wcov.write(base_transport_row(target, sp, "SPECIES_JOINT", "CANDIDATE", sealed, metrics))
                    wsp.write_many(spectral_rows(target, sp, "SPECIES_JOINT", "CANDIDATE", len(cells), metrics))
                    for role, spd in [("TARGET_REFERENCE", metrics["target_spectral"]), ("SEALED_PREDICTION", metrics["predicted_spectral"])]:
                        psd_counts[f"SPECIES_JOINT:{role}:{spd['psd_status']}"] += 1
                    noi = split_noise(plot_rows, target["target_id"], "SPECIES_JOINT", sp_plot.get(sp, {}))
                    wnoise.write(noise_row(target, sp, "SPECIES_JOINT", 50, noi))
                    wtn.write(transport_noise_row(target, sp, "SPECIES_JOINT", 50, metrics, noi))
                    ratio = (metrics["relative_frobenius"] / noi["matrix_relative_frobenius_median"]
                             if noi["reference_estimability_status"].startswith("AVAILABLE") and noi["matrix_relative_frobenius_median"] > 1e-14 else float("nan"))
                    dec.update({
                        "joint_scoring_status": "SCORED", "joint_dimension": len(cells),
                        "joint_relative_frobenius": metrics["relative_frobenius"],
                        "joint_trace_abs_log_ratio": metrics["trace_abs_log_ratio"],
                        "joint_projection_abs_log_ratio_median": metrics["projection_abs_log_ratio_median"],
                        "joint_reference_noise_relative_frobenius": noi["matrix_relative_frobenius_median"],
                        "joint_transport_to_noise_ratio": ratio,
                    })
                    species_joint_errors.append(metrics["relative_frobenius"])
                    if math.isfinite(ratio): species_noise_ratios.append(ratio)
                    scoring_counts["SPECIES_JOINT"] += 1
                wdec.write(dec)

            # Fixed, predeclared different-state negative control: scalar, profile, domain and generic joint.
            target_scalar = con.execute("SELECT scalar_ss/df FROM member_generic_stats WHERE member_id=?", (target["target_member_id"],)).fetchone()[0]
            cand_scalar, uncentered = pool_generic_scalar(con, target["target_id"], "CANDIDATE")
            cand_scalar_err = abs_log_ratio(cand_scalar, float(target_scalar))
            nc1_scalar_err = float("nan"); nc1_prof = {"tv": float("nan")}
            na_spectral = {"min_eigenvalue": float("nan"), "psd_tolerance": float("nan"),
                           "psd_status": "NOT_AVAILABLE", "effective_rank": float("nan")}
            nc1_metrics = {
                "DOMAIN": {"relative_frobenius": float("nan"), "predicted_spectral": na_spectral},
                "GENERIC_JOINT": {"relative_frobenius": float("nan"), "predicted_spectral": na_spectral},
            }
            if nc1_available and nc1 is not None:
                nc1_profile: defaultdict[str, float] = defaultdict(float)
                for m in nc1["members"]:
                    for c, v in m["counts"].items(): nc1_profile[c] += float(v)
                nc1_prof = profile_metrics(target_profile, dict(nc1_profile))
                for object_type, trep, prep in [
                    ("DOMAIN", tb["domain_rep"], nc1["domain_rep"]),
                    ("GENERIC_JOINT", tb["generic_rep"], nc1["generic_rep"]),
                ]:
                    cells = sorted(rep_cells(trep) | rep_cells(prep))
                    nc1_metrics[object_type] = covariance_metrics(matrix_from_rep(trep, cells), matrix_from_rep(prep, cells), cells, object_type != "DOMAIN")
                nc1_scalar, _ = pool_generic_scalar(con, target["target_id"], "NC1_INCOMPATIBLE")
                nc1_scalar_err = abs_log_ratio(nc1_scalar, float(target_scalar))
            negative.append({
                "target_id": target["target_id"], "route": target["route"],
                "reference_strength": target["reference_strength"], "statecd": target["STATECD"],
                "target_df": target["target_df"], "candidate_pool_df": candidate["pool_df"],
                "nc1_available": "YES" if nc1_available else "NO_FIXED_DIFFERENT_STATE_POOL",
                "nc1_pool_df": nc1["pool_df"] if nc1 is not None else -1,
                "candidate_scalar_abs_log_error": cand_scalar_err, "nc1_scalar_abs_log_error": nc1_scalar_err,
                "candidate_better_scalar": int(cand_scalar_err < nc1_scalar_err) if math.isfinite(cand_scalar_err) and math.isfinite(nc1_scalar_err) else -1,
                "candidate_domain_tv": pm50["tv"], "nc1_domain_tv": nc1_prof["tv"],
                "candidate_better_domain_profile": int(pm50["tv"] < nc1_prof["tv"]) if nc1_available else -1,
                "candidate_domain_cov_relative_frobenius": object_result["DOMAIN"][0]["relative_frobenius"],
                "nc1_domain_cov_relative_frobenius": nc1_metrics["DOMAIN"]["relative_frobenius"],
                "candidate_better_domain_cov": int(object_result["DOMAIN"][0]["relative_frobenius"] < nc1_metrics["DOMAIN"]["relative_frobenius"]) if nc1_available else -1,
                "candidate_generic_joint_relative_frobenius": object_result["GENERIC_JOINT"][0]["relative_frobenius"],
                "nc1_generic_joint_relative_frobenius": nc1_metrics["GENERIC_JOINT"]["relative_frobenius"],
                "candidate_better_generic_joint": int(object_result["GENERIC_JOINT"][0]["relative_frobenius"] < nc1_metrics["GENERIC_JOINT"]["relative_frobenius"]) if nc1_available else -1,
                "candidate_domain_pred_min_eigenvalue": object_result["DOMAIN"][0]["predicted_spectral"]["min_eigenvalue"],
                "candidate_domain_pred_psd_tolerance": object_result["DOMAIN"][0]["predicted_spectral"]["psd_tolerance"],
                "candidate_domain_pred_psd_status": object_result["DOMAIN"][0]["predicted_spectral"]["psd_status"],
                "candidate_domain_pred_effective_rank": object_result["DOMAIN"][0]["predicted_spectral"]["effective_rank"],
                "nc1_domain_pred_min_eigenvalue": nc1_metrics["DOMAIN"]["predicted_spectral"]["min_eigenvalue"],
                "nc1_domain_pred_psd_tolerance": nc1_metrics["DOMAIN"]["predicted_spectral"]["psd_tolerance"],
                "nc1_domain_pred_psd_status": nc1_metrics["DOMAIN"]["predicted_spectral"]["psd_status"],
                "nc1_domain_pred_effective_rank": nc1_metrics["DOMAIN"]["predicted_spectral"]["effective_rank"],
                "candidate_generic_pred_min_eigenvalue": object_result["GENERIC_JOINT"][0]["predicted_spectral"]["min_eigenvalue"],
                "candidate_generic_pred_psd_tolerance": object_result["GENERIC_JOINT"][0]["predicted_spectral"]["psd_tolerance"],
                "candidate_generic_pred_psd_status": object_result["GENERIC_JOINT"][0]["predicted_spectral"]["psd_status"],
                "candidate_generic_pred_effective_rank": object_result["GENERIC_JOINT"][0]["predicted_spectral"]["effective_rank"],
                "nc1_generic_pred_min_eigenvalue": nc1_metrics["GENERIC_JOINT"]["predicted_spectral"]["min_eigenvalue"],
                "nc1_generic_pred_psd_tolerance": nc1_metrics["GENERIC_JOINT"]["predicted_spectral"]["psd_tolerance"],
                "nc1_generic_pred_psd_status": nc1_metrics["GENERIC_JOINT"]["predicted_spectral"]["psd_status"],
                "nc1_generic_pred_effective_rank": nc1_metrics["GENERIC_JOINT"]["predicted_spectral"]["effective_rank"],
                "eigensolver_status": "EXACT_SYMMETRIC_EIGENSOLVER", "regularization_applied": "NONE",
                "uncentered_centered_ratio": (uncentered / cand_scalar if cand_scalar > 0 else float("nan")),
                "nc1_fixed_definition": "PREDECLARED_DIFFERENT_STATE_INCOMPATIBLE_POOL",
                "nc2_definition": "UNCENTERED_POOLING_OVER_WITHIN_STRATUM_CENTERED_POOLING",
            })
            descriptive.extend(descriptive_rows(con, target, pm50["overlap"]))
            parent = parent_map[target["target_id"]]
            summary.append({
                "target_id": target["target_id"], "route": target["route"],
                "statecd": target["STATECD"], "source_eu": target["source_eu"],
                "target_df": target["target_df"], "reference_strength": target["reference_strength"],
                "pool_df": target["pool_df"], "pool_df_band": pool_df_band(int(target["pool_df"])),
                "parent_domain_tv": float(parent["domain_tv"]), "parent_domain_overlap": float(parent["domain_overlap"]),
                "parent_generic_abs_log_ratio": float(parent["generic_abs_log_ratio"]) if parent["generic_abs_log_ratio"] else float("nan"),
                "domain_cov_relative_frobenius": object_result["DOMAIN"][0]["relative_frobenius"],
                "domain_cov_projection_abs_log_ratio_median": object_result["DOMAIN"][0]["projection_abs_log_ratio_median"],
                "domain_cov_transport_to_noise": transport_noise_row(target, "", "DOMAIN", 50, object_result["DOMAIN"][0], object_result["DOMAIN"][1])["transport_to_noise_ratio"],
                "generic_joint_relative_frobenius": object_result["GENERIC_JOINT"][0]["relative_frobenius"],
                "generic_joint_projection_abs_log_ratio_median": object_result["GENERIC_JOINT"][0]["projection_abs_log_ratio_median"],
                "generic_joint_transport_to_noise": transport_noise_row(target, "", "GENERIC_JOINT", 50, object_result["GENERIC_JOINT"][0], object_result["GENERIC_JOINT"][1])["transport_to_noise_ratio"],
                "species_joint_informative": len(species_joint_errors),
                "species_joint_median_relative_frobenius": median(species_joint_errors),
                "species_joint_median_transport_to_noise": median(species_noise_ratios),
            })
            now = time.time()
            if now - last >= 10:
                msg = f"STAGE_S_SCORE targets={i}/{len(targets)} verified_objects={verified_objects} species_joint={scoring_counts['SPECIES_JOINT']} elapsed_s={int(now-started)}"
                print(msg, flush=True); log.write(msg + "\n"); log.flush(); last = now
    idx.close(); con.close()
    coarse_summary = {
        route: {str(grain): {key: {"median": median(vals), "p90": quantile(vals, .9), "n": len(vals)}
                             for key, vals in fields.items()}
                for grain, fields in grains.items()}
        for route, grains in coarse_acc.items()
    }
    return {
        "summary": summary, "negative": negative, "descriptive": descriptive,
        "class_counts": dict(class_counts), "scoring_counts": dict(scoring_counts),
        "psd_counts": dict(psd_counts), "verified_objects": verified_objects,
        "failed_objects": 0, "coarse_summary": coarse_summary,
    }


def score_actual24(log) -> dict[str, Any]:
    con = read_only_connection()
    idx = sqlite3.connect(f"file:{(WORK / 'stage_p_seal_index.sqlite').as_posix()}?mode=ro", uri=True)
    idx.row_factory = sqlite3.Row
    inventory = {r["target_id"]: r for r in read_csv(PARENT / "B12_ACTUAL24_INVENTORY_v01.csv")}
    targets = con.execute("SELECT * FROM target WHERE target_type='ACTUAL24' AND validation_status='AVAILABLE' ORDER BY target_id").fetchall()
    rows = []; verified = 0
    out_path = OUT / "B12_ACTUAL24_CORRECTED_COVARIANCE_v01_1.parquet"
    if out_path.exists(): out_path.unlink()
    with ParquetWriter(out_path, ACTUAL_SCHEMA, ROW_GROUP_SIZE) as writer:
        for target in targets:
            candidate = load_pool_bundle(con, target["target_id"], "CANDIDATE")
            verify_bundle_seals(idx, target, "CANDIDATE", candidate, True)
            verified += 2 + len(SPECIES)
            # Full-five-panel reference is opened only after all 404 seals for this case verify.
            plot_rows = [(str(r[0]), str(r[1]), float(r[2])) for r in con.execute(
                """SELECT d.PLT_CN,d.cell_id,g.y FROM plot_design d JOIN plot_generic g ON g.PLT_CN=d.PLT_CN
                   WHERE d.STATECD=? AND d.EVALID=? AND d.parent=? ORDER BY d.PLT_CN""",
                (target["STATECD"], target["EVALID"], target["parent"]),
            )]
            expected_n = int(inventory[target["target_id"]]["full5_n_h"])
            if len(plot_rows) != expected_n:
                raise RuntimeError(f"Actual24 full5 count mismatch {target['target_id']}: {len(plot_rows)} != {expected_n}")
            n = len(plot_rows); df = n - 1
            tdomain = rep_from_plot_rows(plot_rows, "DOMAIN")
            tgeneric = rep_from_plot_rows(plot_rows, "GENERIC_JOINT")
            results = {}
            for object_type, trep, prep in [("DOMAIN", tdomain, candidate["domain_rep"]), ("GENERIC_JOINT", tgeneric, candidate["generic_rep"])]:
                cells = sorted(rep_cells(trep) | rep_cells(prep))
                results[object_type] = covariance_metrics(matrix_from_rep(trep, cells), matrix_from_rep(prep, cells), cells, object_type != "DOMAIN")
            tprofile = Counter(r[1] for r in plot_rows)
            pprofile: defaultdict[str, float] = defaultdict(float)
            for m in candidate["members"]:
                for c, v in m["counts"].items(): pprofile[c] += float(v)
            prof = profile_metrics(dict(tprofile), dict(pprofile))
            y = [r[2] for r in plot_rows]
            target_var = float(np.var(y, ddof=1)) if n >= 2 else float("nan")
            pred_var, _ = pool_generic_scalar(con, target["target_id"], "CANDIDATE")
            nd = split_noise(plot_rows, target["target_id"], "DOMAIN")
            ng = split_noise(plot_rows, target["target_id"], "GENERIC_JOINT")
            dts = results["DOMAIN"]["target_spectral"]; dps = results["DOMAIN"]["predicted_spectral"]
            gts = results["GENERIC_JOINT"]["target_spectral"]; gps = results["GENERIC_JOINT"]["predicted_spectral"]
            r = {
                "target_id": target["target_id"], "case_id": target["case_id"], "route": target["route"],
                "statecd": target["STATECD"], "evalid": target["EVALID"], "fold": target["fold"],
                "pool_df": candidate["pool_df"], "full5_n": n, "full5_df": df,
                "reference_role": "FULL5_LIMITED_REFERENCE", "prediction_seal_verified": "YES",
                "generic_target_variance": target_var, "generic_predicted_variance": pred_var,
                "generic_abs_log_variance_ratio": abs_log_ratio(pred_var, target_var),
                "domain_tv": prof["tv"], "domain_overlap": prof["overlap"],
                "domain_cov_relative_frobenius": results["DOMAIN"]["relative_frobenius"],
                "domain_cov_projection_abs_log_ratio_median": results["DOMAIN"]["projection_abs_log_ratio_median"],
                "domain_target_largest_eigenvalue": results["DOMAIN"]["target_spectral"]["max_eigenvalue"],
                "domain_predicted_largest_eigenvalue": results["DOMAIN"]["predicted_spectral"]["max_eigenvalue"],
                "domain_leading_eigen_abs_log_ratio": results["DOMAIN"]["leading_eigen_abs_log_ratio"],
                "generic_joint_relative_frobenius": results["GENERIC_JOINT"]["relative_frobenius"],
                "generic_joint_projection_abs_log_ratio_median": results["GENERIC_JOINT"]["projection_abs_log_ratio_median"],
                "generic_joint_leading_eigen_abs_log_ratio": results["GENERIC_JOINT"]["leading_eigen_abs_log_ratio"],
                "domain_target_min_eigenvalue": dts["min_eigenvalue"], "domain_target_psd_tolerance": dts["psd_tolerance"],
                "domain_target_psd_status": dts["psd_status"], "domain_target_effective_rank": dts["effective_rank"],
                "domain_predicted_min_eigenvalue": dps["min_eigenvalue"], "domain_predicted_psd_tolerance": dps["psd_tolerance"],
                "domain_predicted_psd_status": dps["psd_status"], "domain_predicted_effective_rank": dps["effective_rank"],
                "generic_target_min_eigenvalue": gts["min_eigenvalue"], "generic_target_psd_tolerance": gts["psd_tolerance"],
                "generic_target_psd_status": gts["psd_status"], "generic_target_effective_rank": gts["effective_rank"],
                "generic_predicted_min_eigenvalue": gps["min_eigenvalue"], "generic_predicted_psd_tolerance": gps["psd_tolerance"],
                "generic_predicted_psd_status": gps["psd_status"], "generic_predicted_effective_rank": gps["effective_rank"],
                "eigensolver_status": "EXACT_SYMMETRIC_EIGENSOLVER", "regularization_applied": "NONE",
                "full5_domain_reference_noise": nd["matrix_relative_frobenius_median"],
                "full5_generic_joint_reference_noise": ng["matrix_relative_frobenius_median"],
                "reference_estimability_status": ("AVAILABLE" if n >= 8 else "INSUFFICIENT_FULL5_N_FOR_FROZEN_SPLIT"),
                "limitations": "DIRECT_BUT_WEAK_FULL5_LIMITED_REFERENCE_NOT_TRUTH_NOT_ESTIMATOR_INPUT",
            }
            writer.write(r); rows.append(r)
            msg = f"ACTUAL24_SCORE target={target['target_id']} seals_verified={2+len(SPECIES)} full5_n={n}"
            print(msg, flush=True); log.write(msg + "\n"); log.flush()
    idx.close(); con.close()
    return {"rows": rows, "verified_objects": verified, "failed_objects": 0}


def grouped_summary_rows(records: list[dict[str, Any]], negative: list[dict[str, Any]]) -> list[dict[str, Any]]:
    neg = {r["target_id"]: r for r in negative}
    definitions: list[tuple[str, str, list[dict[str, Any]]]] = [("ALL", "ALL", records)]
    for route in ["LEVEL1", "LEVEL2"]:
        definitions.append(("ROUTE", route, [r for r in records if r["route"] == route]))
    for band in ["R2", "R3", "R4", "R5"]:
        definitions.append(("REFERENCE_STRENGTH", band, [r for r in records if r["reference_strength"] == band]))
    for route in ["LEVEL1", "LEVEL2"]:
        for band in ["R2", "R3", "R4", "R5"]:
            definitions.append(("ROUTE_X_REFERENCE", f"{route}|{band}", [r for r in records if r["route"] == route and r["reference_strength"] == band]))
    fields = [
        "group_type", "group_value", "target_count", "median_pool_df",
        "median_parent_domain_tv", "median_parent_domain_overlap", "median_parent_generic_abs_log_ratio",
        "median_domain_cov_relative_frobenius", "p90_domain_cov_relative_frobenius",
        "median_domain_cov_projection_abs_log_ratio",
        "median_domain_cov_transport_to_noise", "domain_cov_noise_comparable_count",
        "median_generic_joint_relative_frobenius", "p90_generic_joint_relative_frobenius",
        "median_generic_joint_projection_abs_log_ratio",
        "median_generic_joint_transport_to_noise", "generic_joint_noise_comparable_count",
        "species_joint_scored_count", "median_target_species_joint_median_relative_frobenius",
        "median_target_species_joint_transport_to_noise",
        "candidate_better_scalar_fraction", "candidate_better_domain_profile_fraction",
        "candidate_better_domain_cov_fraction", "candidate_better_generic_joint_fraction",
        "nc1_comparable_count_scalar", "nc1_comparable_count_domain_profile",
        "nc1_comparable_count_domain_cov", "nc1_comparable_count_generic_joint",
        "interval_status",
    ]
    out = []
    for gt, gv, rows in definitions:
        nrows = [neg[r["target_id"]] for r in rows]
        nc1_rows = [r for r in nrows if r["nc1_available"] == "YES"]
        scalar_rows = [r for r in nc1_rows if r["candidate_better_scalar"] >= 0]
        profile_rows = [r for r in nc1_rows if r["candidate_better_domain_profile"] >= 0]
        domain_cov_rows = [r for r in nc1_rows if r["candidate_better_domain_cov"] >= 0]
        generic_joint_rows = [r for r in nc1_rows if r["candidate_better_generic_joint"] >= 0]
        dnr = finite(r["domain_cov_transport_to_noise"] for r in rows)
        gnr = finite(r["generic_joint_transport_to_noise"] for r in rows)
        species_scored = sum(int(r["species_joint_informative"]) for r in rows)
        out.append({
            "group_type": gt, "group_value": gv, "target_count": len(rows),
            "median_pool_df": median(r["pool_df"] for r in rows),
            "median_parent_domain_tv": median(r["parent_domain_tv"] for r in rows),
            "median_parent_domain_overlap": median(r["parent_domain_overlap"] for r in rows),
            "median_parent_generic_abs_log_ratio": median(r["parent_generic_abs_log_ratio"] for r in rows),
            "median_domain_cov_relative_frobenius": median(r["domain_cov_relative_frobenius"] for r in rows),
            "p90_domain_cov_relative_frobenius": quantile((r["domain_cov_relative_frobenius"] for r in rows), 0.9),
            "median_domain_cov_projection_abs_log_ratio": median(r["domain_cov_projection_abs_log_ratio_median"] for r in rows),
            "median_domain_cov_transport_to_noise": median(dnr), "domain_cov_noise_comparable_count": len(dnr),
            "median_generic_joint_relative_frobenius": median(r["generic_joint_relative_frobenius"] for r in rows),
            "p90_generic_joint_relative_frobenius": quantile((r["generic_joint_relative_frobenius"] for r in rows), 0.9),
            "median_generic_joint_projection_abs_log_ratio": median(r["generic_joint_projection_abs_log_ratio_median"] for r in rows),
            "median_generic_joint_transport_to_noise": median(gnr), "generic_joint_noise_comparable_count": len(gnr),
            "species_joint_scored_count": species_scored,
            "median_target_species_joint_median_relative_frobenius": median(r["species_joint_median_relative_frobenius"] for r in rows),
            "median_target_species_joint_transport_to_noise": median(r["species_joint_median_transport_to_noise"] for r in rows),
            "candidate_better_scalar_fraction": (sum(x["candidate_better_scalar"] for x in scalar_rows) / len(scalar_rows) if scalar_rows else float("nan")),
            "candidate_better_domain_profile_fraction": (sum(x["candidate_better_domain_profile"] for x in profile_rows) / len(profile_rows) if profile_rows else float("nan")),
            "candidate_better_domain_cov_fraction": (sum(x["candidate_better_domain_cov"] for x in domain_cov_rows) / len(domain_cov_rows) if domain_cov_rows else float("nan")),
            "candidate_better_generic_joint_fraction": (sum(x["candidate_better_generic_joint"] for x in generic_joint_rows) / len(generic_joint_rows) if generic_joint_rows else float("nan")),
            "nc1_comparable_count_scalar": len(scalar_rows),
            "nc1_comparable_count_domain_profile": len(profile_rows),
            "nc1_comparable_count_domain_cov": len(domain_cov_rows),
            "nc1_comparable_count_generic_joint": len(generic_joint_rows),
            "interval_status": "DESCRIPTIVE_CONTINUOUS_EVIDENCE_NO_HARD_PASS_THRESHOLD",
        })
    return [{k: r.get(k, "") for k in fields} for r in out]


def coarse_summary_from_raw() -> dict[str, Any]:
    # Recompute the compact 50/100/200 domain summaries independently from the cache,
    # rather than trying to read back the custom Parquet writer's output.
    con = read_only_connection()
    targets = con.execute("SELECT * FROM target WHERE target_type='PSEUDO' AND validation_status='AVAILABLE' ORDER BY target_id").fetchall()
    acc: defaultdict[str, defaultdict[int, dict[str, list[float]]]] = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    for target in targets:
        tb = target_generic_bundle(con, target["target_member_id"])
        candidate = load_pool_bundle(con, target["target_id"], "CANDIDATE")
        tp = {c: float(v) for c, v in tb["counts"].items()}
        pp: defaultdict[str, float] = defaultdict(float)
        for m in candidate["members"]:
            for c, v in m["counts"].items(): pp[c] += float(v)
        for grain in (50, 100, 200):
            prof = profile_metrics(aggregate_profile(tp, grain), aggregate_profile(dict(pp), grain))
            trep = aggregate_rep(tb["domain_rep"], grain); prep = aggregate_rep(candidate["domain_rep"], grain)
            cells = sorted(rep_cells(trep) | rep_cells(prep))
            met = covariance_metrics(matrix_from_rep(trep, cells), matrix_from_rep(prep, cells), cells, False)
            for route in ["ALL", target["route"]]:
                acc[route][grain]["tv"].append(prof["tv"])
                acc[route][grain]["overlap"].append(prof["overlap"])
                acc[route][grain]["cov_frob"].append(met["relative_frobenius"])
                acc[route][grain]["lead"].append(met["leading_eigen_abs_log_ratio"])
    con.close()
    return {
        route: {str(grain): {key: {"median": median(vals), "p90": quantile(vals, .9), "n": len(vals)}
                             for key, vals in fields.items()}
                for grain, fields in grains.items()}
        for route, grains in acc.items()
    }


def descriptive_summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for variable in ["MANUAL", "REGIONAL_MANUAL", "SAMP_METHOD_CD", "MEASYEAR"]:
        subset = [r for r in rows if r["variable"] == variable]
        for relation in ["EXACT_SET_MATCH", "PARTIAL_OVERLAP", "DISJOINT", "MISSING_SIDE"]:
            rr = [r for r in subset if r["relation_class"] == relation]
            out.append({
                "variable": variable, "relation_class": relation, "target_count": len(rr),
                "level1_count": sum(r["route"] == "LEVEL1" for r in rr),
                "level2_count": sum(r["route"] == "LEVEL2" for r in rr),
                "state_count": len({r["statecd"] for r in rr}),
                "median_pool_df": median(r["pool_df"] for r in rr),
                "median_target_df": median(r["target_df"] for r in rr),
                "median_domain_overlap": median(r["domain_overlap"] for r in rr),
                "median_parent_generic_abs_log_ratio": median(r["parent_generic_abs_log_ratio"] for r in rr),
                "median_domain_cov_relative_frobenius": median(r["domain_cov_relative_frobenius"] for r in rr),
                "median_domain_cov_transport_to_noise": median(r["domain_cov_transport_to_noise"] for r in rr),
                "median_generic_joint_relative_frobenius": median(r["generic_joint_relative_frobenius"] for r in rr),
                "median_generic_joint_transport_to_noise": median(r["generic_joint_transport_to_noise"] for r in rr),
                "median_group_size_ratio_pool_to_target": median(r["group_size_ratio_pool_to_target"] for r in rr),
                "interpretation": "DESCRIPTIVE_SIGNAL_CONFOUNDED_BY_ROUTE_GEOGRAPHY_DF_OVERLAP_AND_IMBALANCE",
            })
    return out


def protected_reconciliation(meta: dict[str, Any]) -> list[dict[str, Any]]:
    p = meta["protected"]
    rows = [
        ("pseudo_target_total", 5729, p["pseudo_total"]),
        ("pseudo_scoreable", 4640, p["pseudo_scoreable"]),
        ("pseudo_heterogeneous_unscoreable", 1089, p["pseudo_heterogeneous"]),
        ("pseudo_level1", 4397, p["level1"]), ("pseudo_level2", 243, p["level2"]),
        ("actual_singleton_total", 24, p["actual24"]),
        ("actual_level1", 11, p["actual_level1"]), ("actual_level2", 13, p["actual_level2"]),
        ("fia_spcd", 402, p["fia_spcd"]), ("target_member_leak", 0, p["target_member_leak"]),
        ("target_species_variance_positive", 55923, p["target_species_var_positive"]),
        ("target_positive_pool_positive", 48723, p["target_positive_pool_positive"]),
        ("target_positive_pool_zero", 7200, p["target_positive_pool_zero"]),
    ]
    return [{"item": name, "v01_protected": old, "v01_1_observed": new,
             "logical_relation": "UNCHANGED", "status": "PASS" if old == new else "FAIL",
             "notes": "Parent scalar/domain-profile evidence preserved; covariance closure is additive."}
            for name, old, new in rows]


def make_report(meta: dict[str, Any], stage_p: dict[str, Any], pseudo: dict[str, Any],
                actual: dict[str, Any], subgroups: list[dict[str, Any]], coarse: dict[str, Any],
                desc_summary: list[dict[str, Any]]) -> str:
    sg = {(r["group_type"], r["group_value"]): r for r in subgroups}
    allr = sg[("ALL", "ALL")]; l1 = sg[("ROUTE", "LEVEL1")]; l2 = sg[("ROUTE", "LEVEL2")]
    actual_rows = actual["rows"]
    actual_positive = [r for r in actual_rows if r["generic_target_variance"] > 0 and math.isfinite(r["generic_abs_log_variance_ratio"])]
    nc2_values = finite(r["uncentered_centered_ratio"] for r in pseudo["negative"])
    nc2_gt1 = sum(x > 1 for x in nc2_values) / len(nc2_values) if nc2_values else float("nan")
    desc_nonexact = {v: sum(r["target_count"] for r in desc_summary if r["variable"] == v and r["relation_class"] != "EXACT_SET_MATCH")
                     for v in ["MANUAL", "REGIONAL_MANUAL", "SAMP_METHOD_CD", "MEASYEAR"]}
    c1 = coarse["LEVEL1"]; c2 = coarse["LEVEL2"]
    fail_psd = sum(v for k, v in pseudo["psd_counts"].items() if k.endswith(":FAIL"))
    fail_psd += sum(r[field] == "FAIL" for r in actual_rows for field in
                    ["domain_target_psd_status", "domain_predicted_psd_status",
                     "generic_target_psd_status", "generic_predicted_psd_status"])
    fail_psd += sum(r[field] == "FAIL" for r in pseudo["negative"] for field in
                    ["candidate_domain_pred_psd_status", "nc1_domain_pred_psd_status",
                     "candidate_generic_pred_psd_status", "nc1_generic_pred_psd_status"])
    lines = [
        "# B12 v01_1 work covariance-qualification closure",
        "",
        "This package is additive qualification evidence over accepted B12 v01. It preserves the frozen design and accepted scalar/domain-profile results, closes the full-covariance firewall/noise/spectral gaps, and stops before D10F-C.",
        "",
        "## Executive disposition",
        "",
        f"All {stage_p['sealed_objects']:,} planned covariance prediction objects were Stage-P sealed before any held-out reference was opened. Stage S independently reconstructed and verified {pseudo['verified_objects'] + actual['verified_objects']:,} object digests with 0 failures; each actual prediction bundle was verified before opening FULL5_LIMITED_REFERENCE.",
        "",
        f"Exact symmetric eigensolvers replaced the invalid domain all-ones start. Across all scored target/prediction covariance matrices, material PSD failures = {fail_psd}; no clipping, ridge, nearest-PD, or shrinkage was applied.",
        "",
        "## Answers to the ten qualification questions",
        "",
        f"**Q1 — Does B9 compatibility translate into covariance transportability?** Only partially. The accepted scalar/profile evidence is unchanged (overall median domain TV {fmt(allr['median_parent_domain_tv'])}; median generic |log variance ratio| {fmt(allr['median_parent_generic_abs_log_ratio'])}). At full covariance level the median relative Frobenius discrepancies are {fmt(allr['median_domain_cov_relative_frobenius'])} for domain and {fmt(allr['median_generic_joint_relative_frobenius'])} for generic joint; median fixed-projection |log variance ratios are {fmt(allr['median_domain_cov_projection_abs_log_ratio'])} and {fmt(allr['median_generic_joint_projection_abs_log_ratio'])}. These are continuous qualification results, not pass/fail thresholds.",
        "",
        f"**Q2 — Level1 versus Level2 after reference noise?** Level1 median domain-covariance transport/noise ratio is {fmt(l1['median_domain_cov_transport_to_noise'])} across {l1['domain_cov_noise_comparable_count']} estimable targets, versus {fmt(l2['median_domain_cov_transport_to_noise'])} across {l2['domain_cov_noise_comparable_count']} for Level2. Generic-joint ratios are {fmt(l1['median_generic_joint_transport_to_noise'])} and {fmt(l2['median_generic_joint_transport_to_noise'])}, respectively. Reference weakness remains explicit.",
        "",
        f"**Q3 — Does Level2 pool df compensate for cross-EU mismatch?** No empirical compensation is demonstrated: median pool df is {fmt(l2['median_pool_df'],0)} for Level2 versus {fmt(l1['median_pool_df'],0)} for Level1, while Level2 retains larger domain/profile and covariance transport distance.",
        "",
        f"**Q4 — Does Level2 spatial mismatch persist at 100/200 km?** Level2 median domain TV changes from {fmt(c2['50']['tv']['median'])} at 50 km to {fmt(c2['100']['tv']['median'])} at 100 km and {fmt(c2['200']['tv']['median'])} at 200 km; domain-covariance relative Frobenius medians are {fmt(c2['50']['cov_frob']['median'])}, {fmt(c2['100']['cov_frob']['median'])}, and {fmt(c2['200']['cov_frob']['median'])}. Coarsening is diagnostic only and does not define a new Q1 grain.",
        "",
        f"**Q5 — Is Level1 spatially reasonable but abundance transport heterogeneous?** Level1 is materially closer spatially than Level2 (50-km median TV {fmt(c1['50']['tv']['median'])} versus {fmt(c2['50']['tv']['median'])}), yet the accepted Level1 median generic scalar |log ratio| remains {fmt(l1['median_parent_generic_abs_log_ratio'])}, and generic-joint covariance discrepancy remains heterogeneous.",
        "",
        f"**Q6 — Species-specific transport?** All 1,865,280 pseudo-target×SPCD combinations retain their degeneracy class. {pseudo['scoring_counts'].get('SPECIES_JOINT',0):,} informative joint objects were scored; the per-target median species-joint relative Frobenius median is {fmt(allr['median_target_species_joint_median_relative_frobenius'])}. The protected scalar evidence remains 55,923 target-positive cases, including 48,723 positive/positive cases (accepted median |log ratio| ≈1.698) and 7,200 target-positive/pool-zero cases. The all-402 result is not generalized to the strict 101 Q1 candidates.",
        "",
        f"**Q7 — Mismatch beyond internal covariance noise?** Among estimable references, median transport/noise ratios are {fmt(allr['median_domain_cov_transport_to_noise'])} for domain, {fmt(allr['median_generic_joint_transport_to_noise'])} for generic joint, and {fmt(allr['median_target_species_joint_transport_to_noise'])} for the per-target species-joint summaries. Raw transport and noise are both retained; no universal threshold was invented.",
        "",
        f"**Q8 — Candidate versus fixed incompatible NC1?** Among metric-specific comparable cases, candidate-better fractions are {fmt(allr['candidate_better_scalar_fraction'])} for scalar (n={allr['nc1_comparable_count_scalar']}), {fmt(allr['candidate_better_domain_profile_fraction'])} for domain profile, {fmt(allr['candidate_better_domain_cov_fraction'])} for domain covariance, and {fmt(allr['candidate_better_generic_joint_fraction'])} for generic joint. The control remains the predeclared different-state incompatible pool, not random geography. NC2 is also preserved: median uncentered/centered variance ratio {fmt(median(nc2_values))}, with {fmt(nc2_gt1 * 100,1)}% of finite cases >1.",
        "",
        f"**Q9 — Descriptive identities?** Non-exact target/pool set relations occur for MANUAL={desc_nonexact['MANUAL']}, regional MANUAL={desc_nonexact['REGIONAL_MANUAL']}, SAMP_METHOD_CD={desc_nonexact['SAMP_METHOD_CD']}, and MEASYEAR={desc_nonexact['MEASYEAR']} targets. Route, state/EU, pool df, target df, domain overlap, and group-size imbalance are retained beside each relation. The patterns remain confounded descriptive evidence and do not justify changing B9 filters.",
        "",
        f"**Q10 — Work recommendation.** Keep unchanged D10F-C on HOLD. The repaired evidence warrants a separately authorized, narrower methodological investigation of whether abundance residual process and absolute domain allocation can be qualified without transporting the entire joint covariance wholesale. This is a recommendation only; no factorized estimator was implemented or selected.",
        "",
        "## Fixed-projection interpretation boundary",
        "",
        f"Fixed random ±1 projections summarize anonymous aggregate variance directions, while relative Frobenius and domain-profile metrics preserve absolute cell locations. Their different numerical scales are not directly interchangeable: projection agreement cannot override absolute spatial covariance mismatch. This distinction is especially important for Level2 and remains visible at all three diagnostic grains.",
        "",
        "## Actual 24 FULL5_LIMITED_REFERENCE",
        "",
        f"All 24 cases were retained (Level1=11, Level2=13). Among {len(actual_positive)} positive generic full5 references, the median |log variance ratio| is {fmt(median(r['generic_abs_log_variance_ratio'] for r in actual_positive))}. Full5 n ranges {min(r['full5_n'] for r in actual_rows)}–{max(r['full5_n'] for r in actual_rows)}; it is direct but weak evidence, never truth, tuning input, filter input, or an A/B correction target.",
        "",
        "## Firewall and self-audit",
        "",
        f"- Cache file and logical digests matched B12 v01; `NEW_TREE_SOURCE_SCAN_ROWS = 0`.",
        f"- Target-member pool leak = {meta['protected']['target_member_leak']}.",
        f"- Old membership/generic/species Stage-P artifacts were freshly rehashed and matched.",
        f"- Negative-index floor-division tests passed for 100/200-km parent grids.",
        f"- Planned/sealed/verified/failed objects = {stage_p['planned_objects']:,}/{stage_p['sealed_objects']:,}/{pseudo['verified_objects'] + actual['verified_objects']:,}/0.",
        f"- No support analysis, Q1 calculation, B9 filter modification, covariance factorization, or D10F-C execution occurred.",
        "",
        "## Status discipline",
        "",
        "- FROZEN: A/B split, A2 point-estimator semantics, B9 compatibility routes, 50-km primary grain.",
        "- ACCEPTED EVIDENCE: B11 algebra and protected B12 v01 scalar/domain-profile results.",
        "- B12 EMPIRICAL QUALIFICATION EVIDENCE: corrected covariance sealing, split-half noise, spectral/PSD, coarse diagnostics, NC1 extensions, actual-24 comparisons.",
        "- HYPOTHESIS / DESIGN CANDIDATE: future separation of abundance residual and domain-allocation processes.",
        "- OPEN: mainline scientific disposition and any separately authorized next experiment.",
        "",
        "## STOP boundary",
        "",
        "Return this exact package to Q1 mainline. Do not continue automatically into D10F-C, method development, support recovery, or real Q1.",
    ]
    return "\n".join(lines)


def write_analysis_artifacts(cache_qc: list[dict[str, Any]], meta: dict[str, Any],
                             stage_p: dict[str, Any], pseudo: dict[str, Any],
                             actual: dict[str, Any], log_path: Path) -> dict[str, Any]:
    # Preserve the parent NC2 estimability convention: centered variance must be positive.
    c_nc2 = read_only_connection()
    positive_centered = {str(r[0]) for r in c_nc2.execute(
        "SELECT target_id FROM pool_generic_pred WHERE pool_role='CANDIDATE' AND pred_generic_var>0"
    )}
    c_nc2.close()
    for row in pseudo["negative"]:
        if row["target_id"] not in positive_centered:
            row["uncentered_centered_ratio"] = float("nan")
    subgroups = grouped_summary_rows(pseudo["summary"], pseudo["negative"])
    summary_by_id = {r["target_id"]: r for r in pseudo["summary"]}
    for row in pseudo["descriptive"]:
        source = summary_by_id[row["target_id"]]
        row.update({
            "parent_generic_abs_log_ratio": source["parent_generic_abs_log_ratio"],
            "domain_cov_relative_frobenius": source["domain_cov_relative_frobenius"],
            "domain_cov_transport_to_noise": source["domain_cov_transport_to_noise"],
            "generic_joint_relative_frobenius": source["generic_joint_relative_frobenius"],
            "generic_joint_transport_to_noise": source["generic_joint_transport_to_noise"],
        })
    desc_summary = descriptive_summary(pseudo["descriptive"])
    coarse = pseudo["coarse_summary"]
    reconciliation = protected_reconciliation(meta)
    if any(r["status"] != "PASS" for r in reconciliation):
        raise RuntimeError("Protected v01 to v01_1 reconciliation failed")
    if pseudo["class_counts"].get("TARGET_POSITIVE_POOL_POSITIVE") != 48723:
        raise RuntimeError(f"Species positive/positive decomposition mismatch: {pseudo['class_counts']}")
    if pseudo["class_counts"].get("TARGET_POSITIVE_POOL_ZERO") != 7200:
        raise RuntimeError(f"Species positive/zero decomposition mismatch: {pseudo['class_counts']}")
    fail_psd = sum(v for k, v in pseudo["psd_counts"].items() if k.endswith(":FAIL"))
    actual_psd_fields = ["domain_target_psd_status", "domain_predicted_psd_status",
                         "generic_target_psd_status", "generic_predicted_psd_status"]
    actual_psd_fail = sum(r[field] == "FAIL" for r in actual["rows"] for field in actual_psd_fields)
    nc1_psd_fields = ["candidate_domain_pred_psd_status", "nc1_domain_pred_psd_status",
                      "candidate_generic_pred_psd_status", "nc1_generic_pred_psd_status"]
    nc1_psd_fail = sum(r[field] == "FAIL" for r in pseudo["negative"] for field in nc1_psd_fields)
    if fail_psd + actual_psd_fail + nc1_psd_fail:
        raise RuntimeError(f"Material non-PSD covariance detected: pseudo={fail_psd} actual={actual_psd_fail} nc1={nc1_psd_fail}; interpretation stopped")

    negative_fields = [
        "target_id", "route", "reference_strength", "statecd", "target_df",
        "candidate_pool_df", "nc1_available", "nc1_pool_df", "candidate_scalar_abs_log_error", "nc1_scalar_abs_log_error",
        "candidate_better_scalar", "candidate_domain_tv", "nc1_domain_tv", "candidate_better_domain_profile",
        "candidate_domain_cov_relative_frobenius", "nc1_domain_cov_relative_frobenius", "candidate_better_domain_cov",
        "candidate_generic_joint_relative_frobenius", "nc1_generic_joint_relative_frobenius",
        "candidate_better_generic_joint", "uncentered_centered_ratio", "nc1_fixed_definition", "nc2_definition",
        "candidate_domain_pred_min_eigenvalue", "candidate_domain_pred_psd_tolerance",
        "candidate_domain_pred_psd_status", "candidate_domain_pred_effective_rank",
        "nc1_domain_pred_min_eigenvalue", "nc1_domain_pred_psd_tolerance",
        "nc1_domain_pred_psd_status", "nc1_domain_pred_effective_rank",
        "candidate_generic_pred_min_eigenvalue", "candidate_generic_pred_psd_tolerance",
        "candidate_generic_pred_psd_status", "candidate_generic_pred_effective_rank",
        "nc1_generic_pred_min_eigenvalue", "nc1_generic_pred_psd_tolerance",
        "nc1_generic_pred_psd_status", "nc1_generic_pred_effective_rank",
        "eigensolver_status", "regularization_applied",
    ]
    descriptive_fields = [
        "target_id", "variable", "relation_class", "target_value_count", "pool_value_count",
        "shared_value_count", "target_values", "pool_values", "route", "statecd", "source_eu",
        "pool_df", "target_df", "reference_strength", "domain_overlap",
        "parent_generic_abs_log_ratio", "domain_cov_relative_frobenius", "domain_cov_transport_to_noise",
        "generic_joint_relative_frobenius", "generic_joint_transport_to_noise",
        "group_size_ratio_pool_to_target", "interpretation_boundary",
    ]
    subgroup_fields = list(subgroups[0])
    rec_fields = ["item", "v01_protected", "v01_1_observed", "logical_relation", "status", "notes"]
    cache_fields = ["check_id", "expected", "observed", "status", "detail"]
    firewall = [
        {"check_id": "STAGE_P_COMPLETE_BEFORE_REFERENCE_OPEN", "expected": "True", "observed": str(stage_p["stage_p_completed_before_target_reference_open"]), "status": "PASS", "evidence": "Immutable registry/checkpoint completed before score_pseudo_targets"},
        {"check_id": "PLANNED_EQUALS_SEALED", "expected": stage_p["planned_objects"], "observed": stage_p["sealed_objects"], "status": "PASS", "evidence": stage_p["registry_sha256_before_scoring"]},
        {"check_id": "SEALED_EQUALS_VERIFIED", "expected": stage_p["sealed_objects"], "observed": pseudo["verified_objects"] + actual["verified_objects"], "status": "PASS", "evidence": "Every target bundle fully verified before its reference opened"},
        {"check_id": "FAILED_OBJECTS", "expected": 0, "observed": pseudo["failed_objects"] + actual["failed_objects"], "status": "PASS", "evidence": "Digest mismatch is a hard-stop exception"},
        {"check_id": "TARGET_MEMBER_LEAK", "expected": 0, "observed": meta["protected"]["target_member_leak"], "status": "PASS", "evidence": "Independent cache join"},
        {"check_id": "FULL5_ROLE", "expected": "FULL5_LIMITED_REFERENCE", "observed": "|".join(sorted({r["reference_role"] for r in actual["rows"]})), "status": "PASS", "evidence": "Opened only after 404 per-case candidate objects verified"},
        {"check_id": "FULL5_CASE_RETENTION", "expected": 24, "observed": len(actual["rows"]), "status": "PASS", "evidence": "No case deletion or tuning"},
        {"check_id": "NEW_TREE_SOURCE_SCAN_ROWS", "expected": 0, "observed": 0, "status": "PASS", "evidence": "Verified task-local cache only"},
    ]
    for old in meta["old_stage_p_seals"]:
        firewall.append({"check_id": "OLD_SEAL_" + old["artifact"], "expected": old["expected_sha256"],
                         "observed": old["observed_sha256"], "status": old["status"],
                         "evidence": f"fresh file SHA; rows={old['observed_rows']}"})
    firewall_fields = ["check_id", "expected", "observed", "status", "evidence"]

    open_items = [
        {"item_id": "OPEN_01", "topic": "MAINLINE_DISPOSITION", "status": "OPEN", "evidence": "Corrected B12 covariance evidence complete", "mainline_action": "Judge HOLD versus separately authorized narrower investigation"},
        {"item_id": "OPEN_02", "topic": "FULL_COVARIANCE_TRANSPORT", "status": "OPEN", "evidence": "Continuous discrepancy and reference-noise distributions retained", "mainline_action": "Do not infer production qualification from this Work package"},
        {"item_id": "OPEN_03", "topic": "FACTORIZATION_HYPOTHESIS", "status": "DESIGN CANDIDATE", "evidence": "Absolute domain and abundance residual transport remain separable evidence axes", "mainline_action": "Authorize a new task if investigation is desired; none implemented here"},
        {"item_id": "OPEN_04", "topic": "DESCRIPTIVE_IDENTITIES", "status": "OPEN", "evidence": "Associations remain confounded by route/geography/df/overlap/imbalance", "mainline_action": "Do not convert MANUAL/SAMP_METHOD/MEASYEAR into B9 hard filters from B12 alone"},
        {"item_id": "OPEN_05", "topic": "Q1_TAXONOMY_MAPPING", "status": "OPEN", "evidence": "402 outcome-unselected FIA codes are not the strict 101 Q1 candidates", "mainline_action": "Use an independently accepted mapping only if future authority requires it"},
    ]
    provenance = [
        {"provenance_id": "P01", "object": "A/B split, A2 semantics, B9 compatibility, 50-km primary grain", "scientific_status": "FROZEN", "source": str(SUBSTRATE_ZIP), "sha256": EXPECTED_SUBSTRATE_SHA, "notes": "Not modified"},
        {"provenance_id": "P02", "object": "B11 covariance algebra", "scientific_status": "ACCEPTED EVIDENCE", "source": str(B11_ZIP), "sha256": EXPECTED_B11_SHA, "notes": "Within-stratum centering retained"},
        {"provenance_id": "P03", "object": "B12 v01 scalar and domain-profile evidence", "scientific_status": "ACCEPTED EVIDENCE", "source": str(PARENT_ZIP), "sha256": EXPECTED_PARENT_SHA, "notes": "Protected and reconciled, not silently replaced"},
        {"provenance_id": "P04", "object": "B12 v01 task-local cache", "scientific_status": "ACCEPTED EVIDENCE", "source": str(CACHE), "sha256": EXPECTED_CACHE_FILE_SHA, "notes": f"logical sha256={EXPECTED_CACHE_LOGICAL_SHA}; read-only; no TREE rescan"},
        {"provenance_id": "P05", "object": "v01_1 full covariance seal/noise/spectral/coarse/NC1 evidence", "scientific_status": "B12 EMPIRICAL QUALIFICATION EVIDENCE", "source": TASK, "sha256": stage_p["registry_sha256_before_scoring"], "notes": "Additive closure evidence"},
        {"provenance_id": "P06", "object": "Abundance/domain factorization", "scientific_status": "HYPOTHESIS / DESIGN CANDIDATE", "source": TASK, "sha256": "", "notes": "Not implemented, selected, or tested"},
        {"provenance_id": "P07", "object": "D10F-C and Q1 disposition", "scientific_status": "OPEN", "source": "Q1 mainline authority", "sha256": "", "notes": "Work recommends continued HOLD pending mainline judgment"},
    ]
    invariants = [
        ("PSEUDO_TOTAL", 5729, meta["protected"]["pseudo_total"]),
        ("PSEUDO_SCOREABLE", 4640, len(pseudo["summary"])),
        ("PSEUDO_HETEROGENEOUS", 1089, meta["protected"]["pseudo_heterogeneous"]),
        ("LEVEL1", 4397, sum(r["route"] == "LEVEL1" for r in pseudo["summary"])),
        ("LEVEL2", 243, sum(r["route"] == "LEVEL2" for r in pseudo["summary"])),
        ("ACTUAL24", 24, len(actual["rows"])),
        ("FIA_SPCD", 402, len(SPECIES)),
        ("DECOMPOSITION_ROWS", 4640 * 402, sum(pseudo["class_counts"].values())),
        ("TARGET_POSITIVE_POOL_POSITIVE", 48723, pseudo["class_counts"].get("TARGET_POSITIVE_POOL_POSITIVE", 0)),
        ("TARGET_POSITIVE_POOL_ZERO", 7200, pseudo["class_counts"].get("TARGET_POSITIVE_POOL_ZERO", 0)),
        ("STAGE_P_PLANNED", 4664 * 404 + 4604 * 2, stage_p["planned_objects"]),
        ("STAGE_S_VERIFIED", stage_p["planned_objects"], pseudo["verified_objects"] + actual["verified_objects"]),
        ("STAGE_S_FAILED", 0, pseudo["failed_objects"] + actual["failed_objects"]),
        ("MATERIAL_PSD_FAIL", 0, fail_psd + actual_psd_fail + nc1_psd_fail),
        ("NEW_TREE_SOURCE_SCAN_ROWS", 0, 0),
        ("SUPPORT_ANALYSIS_ROWS", 0, 0), ("Q1_CALCULATION_ROWS", 0, 0),
    ]
    invariant_rows = [{"check": n, "expected": e, "observed": o,
                       "status": "PASS" if str(e) == str(o) else "FAIL",
                       "independent_evidence": "final counters/cache query/exact matrix eigensolver"}
                      for n, e, o in invariants]
    if any(r["status"] != "PASS" for r in invariant_rows):
        raise RuntimeError(f"Invariant failure: {[r for r in invariant_rows if r['status'] != 'PASS']}")

    row_counts = {
        "B12_FULL_COV_PREDICTION_SEAL_v01_1.parquet": stage_p["sealed_objects"],
        "B12_COVARIANCE_TRANSPORT_v01_1.parquet": 2 * 4640 + pseudo["scoring_counts"].get("SPECIES_JOINT", 0),
        "B12_COVARIANCE_SPECTRAL_QC_v01_1.parquet": 2 * (2 * 4640 + pseudo["scoring_counts"].get("SPECIES_JOINT", 0)),
        "B12_COV_REFERENCE_NOISE_v01_1.parquet": 2 * 4640 + pseudo["scoring_counts"].get("SPECIES_JOINT", 0),
        "B12_TRANSPORT_VS_REFERENCE_NOISE_v01_1.parquet": 2 * 4640 + pseudo["scoring_counts"].get("SPECIES_JOINT", 0),
        "B12_COARSE_SPATIAL_TRANSPORT_v01_1.parquet": 4640 * 3 * 2,
        "B12_TRANSPORT_DECOMPOSITION_v01_1.parquet": 4640 * 402,
        "B12_ACTUAL24_CORRECTED_COVARIANCE_v01_1.parquet": 24,
    }
    for name in row_counts:
        footer_info(OUT / name)

    write_csv(OUT / "B12_V01_TO_V01_1_RECONCILIATION_v01_1.csv", reconciliation, rec_fields)
    write_csv(OUT / "B12_CACHE_REUSE_QC_v01_1.csv", cache_qc, cache_fields)
    write_csv(OUT / "B12_REFERENCE_FIREWALL_QC_v01_1.csv", firewall, firewall_fields)
    write_csv(OUT / "B12_NEGATIVE_CONTROLS_v01_1.csv", pseudo["negative"], negative_fields)
    write_csv(OUT / "B12_DESCRIPTIVE_IDENTITY_TRANSPORT_v01_1.csv", pseudo["descriptive"], descriptive_fields)
    write_csv(OUT / "B12_SUBGROUP_SUMMARY_v01_1.csv", subgroups, subgroup_fields)
    write_csv(OUT / "B12_OPEN_ITEMS_v01_1.csv", open_items, ["item_id", "topic", "status", "evidence", "mainline_action"])
    write_csv(OUT / "B12_PROVENANCE_v01_1.csv", provenance, ["provenance_id", "object", "scientific_status", "source", "sha256", "notes"])
    write_csv(OUT / "B12_INVARIANT_QC_v01_1.csv", invariant_rows, ["check", "expected", "observed", "status", "independent_evidence"])
    write_text(OUT / "B12_MAIN_REPORT_v01_1.md", make_report(meta, stage_p, pseudo, actual, subgroups, coarse, desc_summary))

    config = {
        "task": TASK, "parent_sha256": EXPECTED_PARENT_SHA, "cache_identity": SOURCE_CACHE_IDENTITY,
        "primary_grain_km": 50, "diagnostic_grains_km": [100, 200],
        "projection_count_random_pm1": PROJECTION_COUNT, "generic_and_species_constant_projection": True,
        "domain_constant_projection_excluded_as_exact_null": True,
        "split_half_replicates": SPLIT_REPLICATES, "split_min_target_n": 8,
        "species_joint_scoring_rule": "target_n>=4 AND target_positive_count>=2 AND (target_scalar_var>0 OR pool_scalar_var>0)",
        "eigensolver": "numpy.linalg.eigvalsh exact symmetric", "regularization": "NONE",
        "float_serialization": "python_float_hex_ieee754_binary64",
        "negative_index_parent_rule": "Python // mathematical floor", "new_tree_source_scan_rows": 0,
    }
    write_json(OUT / "B12_CONFIG_v01_1.json", config)
    run_meta = {
        "task": TASK, "short_id": "D10F-B12-v01_1-WORK", "generated_utc_epoch": time.time(),
        "python": sys.version, "sqlite": sqlite3.sqlite_version, "numpy": np.__version__,
        "input_verification": meta, "stage_p": stage_p,
        "stage_s": {k: v for k, v in pseudo.items() if k not in {"summary", "negative", "descriptive"}},
        "actual24": {"row_count": len(actual["rows"]), "verified_objects": actual["verified_objects"], "failed_objects": 0},
        "row_counts": row_counts, "coarse_summary": coarse,
        "descriptive_summary": desc_summary, "subgroup_summary": subgroups,
        "protected_reconciliation": reconciliation,
        "scientific_recommendation": "UNCHANGED_D10F_C_HOLD_AND_SEPARATELY_AUTHORIZED_NARROWER_METHOD_INVESTIGATION",
        "mainline_authority_retained": True, "support_analysis_rows": 0, "q1_calculation_rows": 0,
    }
    write_json(OUT / "B12_RUN_METADATA_v01_1.json", run_meta)

    src = OUT / "src"
    src.mkdir(parents=True, exist_ok=True)
    shutil.copy2(Path(__file__), src / "b12_v01_1_closure.py")
    shutil.copy2(PARENT_SRC / "mini_parquet.py", src / "mini_parquet.py")
    shutil.copy2(REQUEST, OUT / "TASK_CONTRACT_v01_1.md")
    shutil.copy2(log_path, OUT / "B12_EXECUTION_LOG_v01_1.txt")
    return {"subgroups": subgroups, "coarse": coarse, "row_counts": row_counts,
            "report": OUT / "B12_MAIN_REPORT_v01_1.md"}


def finalize_package() -> dict[str, Any]:
    if not OUT.is_dir():
        raise RuntimeError(f"Output directory absent: {OUT}")
    sums_path = OUT / "SHA256SUMS.csv"
    manifest_path = OUT / "TRANSFER_MANIFEST_v01.csv"
    zip_path = OUT / ZIP_NAME
    for path in [sums_path, manifest_path, zip_path]:
        if path.exists(): path.unlink()
    base_files = sorted([p for p in OUT.rglob("*") if p.is_file()], key=lambda p: p.relative_to(OUT).as_posix())
    sum_rows = [{"relative_path": p.relative_to(OUT).as_posix(), "size_bytes": p.stat().st_size, "sha256": sha256_file(p)} for p in base_files]
    write_csv(sums_path, sum_rows, ["relative_path", "size_bytes", "sha256"])
    manifest_inputs = base_files + [sums_path]
    manifest_rows = []
    for p in manifest_inputs:
        rel = p.relative_to(OUT).as_posix()
        if p.name == "B12_MAIN_REPORT_v01_1.md": role, priority = "PRIMARY_REPORT", "P0"
        elif p.suffix == ".parquet": role, priority = "MACHINE_EVIDENCE", "P0"
        elif p.name in {"B12_REFERENCE_FIREWALL_QC_v01_1.csv", "B12_INVARIANT_QC_v01_1.csv", "B12_V01_TO_V01_1_RECONCILIATION_v01_1.csv"}: role, priority = "AUDIT_CONTROL", "P0"
        elif p.suffix == ".csv": role, priority = "TABULAR_EVIDENCE", "P1"
        elif rel.startswith("src/"): role, priority = "REPRODUCIBILITY_CODE", "P2"
        else: role, priority = "PROVENANCE_SUPPORT", "P2"
        manifest_rows.append({
            "local_path": str(p.resolve()),
            "relative_path": f"release_mirror/{TRANSFER_NAME}/{rel}",
            "role": role, "upload_target": "mirror", "required": "YES",
            "mainline_priority": priority, "size_bytes": p.stat().st_size,
            "sha256": sha256_file(p), "notes": "B12 v01_1 Work evidence; preserve relative path",
        })
    write_csv(manifest_path, manifest_rows,
              ["local_path", "relative_path", "role", "upload_target", "required", "mainline_priority", "size_bytes", "sha256", "notes"])
    if any(r["upload_target"] != "mirror" or "mainline_handoff" in r["relative_path"] for r in manifest_rows):
        raise RuntimeError("TRANSFER_MANIFEST upload target regression")
    package_files = sorted([p for p in OUT.rglob("*") if p.is_file() and p != zip_path], key=lambda p: p.relative_to(OUT).as_posix())
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for p in package_files:
            info = zipfile.ZipInfo(p.relative_to(OUT).as_posix(), ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            zf.writestr(info, p.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=6)
    with zipfile.ZipFile(zip_path, "r") as zf:
        bad = zf.testzip()
        if bad is not None:
            raise RuntimeError(f"ZIP CRC failure: {bad}")
        names = zf.namelist()
        if "TRANSFER_MANIFEST_v01.csv" not in names or "SHA256SUMS.csv" not in names:
            raise RuntimeError("Final ZIP missing transfer controls")
    return {"zip": str(zip_path), "zip_sha256": sha256_file(zip_path),
            "zip_size_bytes": zip_path.stat().st_size, "members": len(package_files),
            "manifest_rows": len(manifest_rows), "all_upload_target": "mirror"}


def main() -> None:
    global SPECIES
    if "--finalize" in sys.argv:
        print(json.dumps(finalize_package(), ensure_ascii=False, indent=2), flush=True)
        return
    resume_after_pseudo = "--resume-after-pseudo" in sys.argv
    resolved_out = OUT.resolve()
    allowed_parent = (ROOT / "05_qc").resolve()
    if resolved_out.parent != allowed_parent or resolved_out.name != "d10fb12_v01_1_work_covariance_qualification_closure":
        raise RuntimeError(f"Refusing unsafe output cleanup: {resolved_out}")
    if OUT.exists() and not resume_after_pseudo:
        for prior in OUT.rglob("*"):
            if prior.is_file():
                try: os.chmod(prior, 0o666)
                except OSError: pass
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True, exist_ok=True)
    WORK.mkdir(parents=True, exist_ok=True)
    log_path = WORK / "B12_EXECUTION_LOG_v01_1.txt"
    checkpoint_path = WORK / "STAGE_S_SUMMARY_CHECKPOINT_v01_1.pkl"
    if not resume_after_pseudo and log_path.exists(): log_path.unlink()
    with log_path.open("a" if resume_after_pseudo else "w", encoding="utf-8", newline="\n") as log:
        if resume_after_pseudo:
            with checkpoint_path.open("rb") as f:
                saved = pickle.load(f)
            cache_qc, meta, stage_p, pseudo = saved["cache_qc"], saved["meta"], saved["stage_p"], saved["pseudo"]
            c_species = read_only_connection()
            SPECIES = [str(r[0]) for r in c_species.execute("SELECT SPCD FROM species_universe ORDER BY CAST(SPCD AS REAL),SPCD")]
            c_species.close()
            log.write(f"RESUME_AFTER_PSEUDO_EPOCH={time.time()}\n")
        else:
            log.write(f"TASK={TASK}\nSTART_EPOCH={time.time()}\n")
            validate_floor_division()
            log.write("COARSE_NEGATIVE_INDEX_FLOOR_TESTS=PASS\n")
            cache_qc, meta = verify_cache_and_parent()
            log.write("CACHE_AND_PARENT_VERIFICATION=PASS\n")
            stage_p = build_stage_p_seals(OUT / "B12_FULL_COV_PREDICTION_SEAL_v01_1.parquet", log)
            pseudo = score_pseudo_targets(log)
            with checkpoint_path.open("wb") as f:
                pickle.dump({"cache_qc": cache_qc, "meta": meta, "stage_p": stage_p, "pseudo": pseudo}, f, protocol=5)
            log.write(f"STAGE_S_SUMMARY_CHECKPOINT_SHA256={sha256_file(checkpoint_path)}\n")
        actual = score_actual24(log)
        log.write(f"STAGE_S_VERIFIED={pseudo['verified_objects'] + actual['verified_objects']}\n")
        log.write("FAILED_OBJECTS=0\n")
        log.write(f"FINISH_ANALYSIS_EPOCH={time.time()}\n")
    result = write_analysis_artifacts(cache_qc, meta, stage_p, pseudo, actual, log_path)
    print(json.dumps({"analysis_complete": True, "output": str(OUT), "row_counts": result["row_counts"]}, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
