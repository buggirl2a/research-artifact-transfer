from __future__ import annotations

import csv
import gzip
import hashlib
import json
import os
import platform
import shutil
import sqlite3
import sys
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
CFG_PATH = ROOT / "config" / "config.json"
CFG = json.loads(CFG_PATH.read_text(encoding="utf-8"))
TASK_ID = CFG["task_id"]
LAYER2_DB = ROOT / "Q1_FIA_SUPPORT_MEASUREMENT_SUBSTRATE_CANDIDATE_v01_1.sqlite"
LAYER2_BUILDING = ROOT / "Q1_FIA_SUPPORT_MEASUREMENT_SUBSTRATE_CANDIDATE_v01_1.building.sqlite"
LAYER2_CKPT = ROOT / "checkpoints" / "LAYER2_COMPLETE_v01_1.json"
LAYER3_CKPT = ROOT / "checkpoints" / "LAYER3_COMPLETE_v01_1.json"
FULL_F0_GZ = ROOT / "LEGAL_OPPORTUNITY_F0_CLASSIFICATION_v01_1.csv.gz"
LOG_PATH = ROOT / "logs" / "EXECUTION_LOG_v01_1.txt"
ZIP_PATH = ROOT / CFG["output_bundle_name"]
SAMPLE_PATH = Path(r"C:\range_paper\99_tmp\q1_fia_support_legal_opportunity_operator_v01_1\LEGAL_OPPORTUNITY_F0_CLASSIFICATION_SAMPLE_v01_1.csv")

LOG: list[str] = []


def log(message: str) -> None:
    line = str(message)
    LOG.append(line)
    print(line, flush=True)


def sha256(path: Path, block_size: int = 8 * 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            block = f.read(block_size)
            if not block:
                break
            h.update(block)
    return h.hexdigest()


def canonical_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fieldnames: list[str] | None = None) -> int:
    rows = list(rows)
    if fieldnames is None:
        if not rows:
            raise ValueError(f"fieldnames required for empty CSV: {path}")
        fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="raise", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def norm_code(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if not text:
        return ""
    try:
        number = float(text)
        if number.is_integer():
            return str(int(number))
    except ValueError:
        pass
    return text.upper()


def num_or_none(value: Any) -> float | None:
    if value is None or str(value).strip() == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def builder_source_sha256() -> str:
    return sha256(Path(__file__).resolve())


def readonly_connect(path: Path) -> sqlite3.Connection:
    uri = path.resolve().as_uri() + "?mode=ro"
    con = sqlite3.connect(uri, uri=True)
    con.execute("PRAGMA query_only=ON")
    return con


LAYER2_SCHEMA = {
    "f0_linkage": [
        "PLT_CN", "permanent_plot_id", "plot_visit_identity", "fold", "STATECD", "EVALID",
        "source_eu", "DESIGNCD_FROZEN", "MANUAL_FROZEN", "substrate_source_table", "substrate_source_key",
    ],
    "plot_opportunity_source": [
        "SOURCE_PLOT_CN", "PLT_CN", "PLOT_STATUS_CD", "PLOT_NONSAMPLE_REASN_CD", "SAMP_METHOD_CD",
        "SUBP_EXAMINE_CD", "MACRO_BREAKPOINT_DIA", "DESIGNCD", "MANUAL",
    ],
    "subplot_opportunity_source": [
        "SOURCE_SUBPLOT_CN", "PLT_CN", "SUBP", "SUBP_STATUS_CD", "POINT_NONSAMPLE_REASN_CD",
    ],
    "condition_opportunity_source": [
        "SOURCE_COND_CN", "PLT_CN", "CONDID", "COND_STATUS_CD", "COND_NONSAMPLE_REASN_CD", "PROP_BASIS",
        "CONDPROP_UNADJ", "SUBPPROP_UNADJ", "MACRPROP_UNADJ",
    ],
    "subplot_condition_relation": ["SOURCE_SUBP_COND_CN", "PLT_CN", "SUBP", "CONDID"],
}
SCHEMA_FINGERPRINT = canonical_hash(LAYER2_SCHEMA)
LAYER2_BUILD_FINGERPRINT = canonical_hash({
    "schema": LAYER2_SCHEMA,
    "source_table_field_sets": {
        "PLOT": ["CN", "PLOT_STATUS_CD", "PLOT_NONSAMPLE_REASN_CD", "SAMP_METHOD_CD", "SUBP_EXAMINE_CD", "MACRO_BREAKPOINT_DIA", "DESIGNCD", "MANUAL"],
        "SUBPLOT": ["CN", "PLT_CN", "SUBP", "SUBP_STATUS_CD", "POINT_NONSAMPLE_REASN_CD"],
        "COND": ["CN", "PLT_CN", "CONDID", "COND_STATUS_CD", "COND_NONSAMPLE_REASN_CD", "PROP_BASIS", "CONDPROP_UNADJ", "SUBPPROP_UNADJ", "MACRPROP_UNADJ"],
        "SUBP_COND": ["CN", "PLT_CN", "SUBP", "CONDID"],
    },
    "f0_filter": "exact frozen plot_visit_design_core.PLT_CN membership",
})


def verify_protected_inputs() -> tuple[dict[str, Any], str]:
    log("STAGE INPUT_BINDING: begin")
    small_specs = [
        ("AUTHORIZATION", Path(CFG["authorization_path"]), CFG["authorization_sha256"]),
        ("MAINLINE_HANDOFF", Path(CFG["handoff_path"]), CFG["handoff_sha256"]),
        ("ACCEPTED_LOCAL", Path(CFG["accepted_local_zip_path"]), CFG["accepted_local_sha256"]),
        ("FROZEN_SUBSTRATE_ZIP", Path(CFG["frozen_substrate_zip_path"]), CFG["frozen_substrate_zip_sha256"]),
        ("ACCEPTED_SEARCH", Path(CFG["accepted_search_zip_path"]), CFG["accepted_search_sha256"]),
    ]
    records: list[dict[str, Any]] = []
    for input_id, path, expected in small_specs:
        if not path.is_file():
            raise RuntimeError(f"missing protected input: {path}")
        observed = sha256(path)
        if observed.lower() != expected.lower():
            raise RuntimeError(f"protected input SHA mismatch: {input_id}: {observed} != {expected}")
        expected_size = CFG.get("frozen_substrate_zip_size") if input_id == "FROZEN_SUBSTRATE_ZIP" else None
        if expected_size is not None and path.stat().st_size != expected_size:
            raise RuntimeError(f"protected input size mismatch: {input_id}")
        status = "PASS"
        note = ""
        if input_id == "ACCEPTED_LOCAL" and path.name != CFG["accepted_local_authorized_filename"]:
            status = "PASS_CONTENT_IDENTITY_NORMALIZED_FILENAME"
            note = f"authorized filename={CFG['accepted_local_authorized_filename']}; bound local filename={path.name}; content SHA exact"
        records.append({
            "input_id": input_id,
            "path": str(path),
            "size_bytes": path.stat().st_size,
            "expected_sha256": expected.lower(),
            "observed_sha256": observed.lower(),
            "status": status,
            "note": note,
        })
        log(f"INPUT {input_id}: {status}; size={path.stat().st_size}; sha256={observed}")

    substrate_sqlite = Path(CFG["frozen_substrate_sqlite_path"])
    if not substrate_sqlite.is_file():
        raise RuntimeError(f"missing frozen substrate SQLite cache: {substrate_sqlite}")
    substrate_sqlite_observed = sha256(substrate_sqlite)
    if substrate_sqlite_observed.lower() != CFG["frozen_substrate_sqlite_sha256"].lower():
        raise RuntimeError("frozen substrate internal SQLite SHA mismatch")
    records.append({
        "input_id": "FROZEN_SUBSTRATE_INTERNAL_SQLITE",
        "path": str(substrate_sqlite),
        "size_bytes": substrate_sqlite.stat().st_size,
        "expected_sha256": CFG["frozen_substrate_sqlite_sha256"].lower(),
        "observed_sha256": substrate_sqlite_observed.lower(),
        "status": "PASS",
        "note": "internal cache is byte-bound to the accepted frozen substrate lineage",
    })
    log(f"INPUT FROZEN_SUBSTRATE_INTERNAL_SQLITE: PASS; size={substrate_sqlite.stat().st_size}; sha256={substrate_sqlite_observed}")

    layer1 = Path(CFG["layer1_sqlite_path"])
    if not layer1.is_file():
        raise RuntimeError(f"Layer 1 source missing: {layer1}")
    stat = layer1.stat()
    if stat.st_size != CFG["layer1_accepted_size"]:
        raise RuntimeError("Layer 1 size differs; FRESH_FULL_HASH_REBIND is mandatory before scientific reading")
    source_binding = {
        "task_id": TASK_ID,
        "source_binding_mode": CFG["source_binding_mode"],
        "layer": "LAYER_1_BOUND_SOURCE",
        "path": str(layer1),
        "exists": True,
        "current_size_bytes": stat.st_size,
        "accepted_size_bytes": CFG["layer1_accepted_size"],
        "accepted_full_sha256": CFG["layer1_accepted_sha256"],
        "accepted_binding_authority": "SUBSTRATE_SOURCE_MANIFEST_v01_1.csv plus accepted Local audit source-QC record",
        "read_intent": "READ_ONLY",
        "filesystem_mtime_ns": stat.st_mtime_ns,
        "filesystem_ctime_ns": stat.st_ctime_ns,
        "path_match": True,
        "size_match": True,
        "replacement_or_provenance_anomaly_observed": False,
        "fresh_full_hash_triggered": False,
        "fresh_full_hash_performed": False,
        "status": "PASS_INHERITED_ACCEPTED_FULL_HASH_BINDING",
        "builder_version": CFG["builder_version"],
        "builder_source_sha256": builder_source_sha256(),
    }
    write_json(ROOT / "SOURCE_BINDING_RECORD_v01_1.json", source_binding)
    binding_fingerprint = canonical_hash({
        "protected": [{k: r[k] for k in ("input_id", "path", "size_bytes", "expected_sha256", "observed_sha256", "status")} for r in records],
        "layer1": {k: source_binding[k] for k in ("source_binding_mode", "path", "current_size_bytes", "accepted_size_bytes", "accepted_full_sha256", "read_intent", "path_match", "size_match", "replacement_or_provenance_anomaly_observed")},
        "layer2_build_fingerprint": LAYER2_BUILD_FINGERPRINT,
    })
    log("LAYER1 SOURCE_BINDING_MODE: INHERITED_ACCEPTED_FULL_HASH_BINDING")
    log(f"LAYER1 current metadata: size={stat.st_size}; mtime_ns={stat.st_mtime_ns}; ctime_ns={stat.st_ctime_ns}")
    log("STAGE INPUT_BINDING: complete")
    return {"records": records, "source_binding": source_binding}, binding_fingerprint


def create_layer2_building(binding_fingerprint: str) -> None:
    if LAYER2_BUILDING.exists():
        try:
            con = sqlite3.connect(LAYER2_BUILDING)
            meta = dict(con.execute("SELECT key, value FROM metadata"))
            con.close()
            if meta.get("TASK_ID") == TASK_ID and meta.get("BINDING_FINGERPRINT") == binding_fingerprint and meta.get("SCHEMA_FINGERPRINT") == SCHEMA_FINGERPRINT and meta.get("BUILDER_SOURCE_SHA256") == builder_source_sha256():
                log("LAYER2 partial checkpoint: validated building database; completed tables may be reused")
                return
        except Exception:
            pass
        LAYER2_BUILDING.unlink()
        log("LAYER2 partial checkpoint: invalid/incompatible building database removed")
    con = sqlite3.connect(LAYER2_BUILDING)
    con.executescript(
        """
        PRAGMA page_size=4096;
        PRAGMA journal_mode=DELETE;
        PRAGMA synchronous=FULL;
        PRAGMA foreign_keys=OFF;
        CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
        CREATE TABLE f0_linkage (
          PLT_CN TEXT PRIMARY KEY,
          permanent_plot_id TEXT,
          plot_visit_identity TEXT NOT NULL,
          fold TEXT NOT NULL,
          STATECD INTEGER,
          EVALID TEXT,
          source_eu TEXT,
          DESIGNCD_FROZEN TEXT,
          MANUAL_FROZEN TEXT,
          substrate_source_table TEXT NOT NULL,
          substrate_source_key TEXT NOT NULL
        );
        CREATE TABLE plot_opportunity_source (
          SOURCE_PLOT_CN TEXT PRIMARY KEY,
          PLT_CN TEXT NOT NULL,
          PLOT_STATUS_CD,
          PLOT_NONSAMPLE_REASN_CD,
          SAMP_METHOD_CD,
          SUBP_EXAMINE_CD,
          MACRO_BREAKPOINT_DIA,
          DESIGNCD,
          MANUAL
        );
        CREATE TABLE subplot_opportunity_source (
          SOURCE_SUBPLOT_CN TEXT PRIMARY KEY,
          PLT_CN TEXT NOT NULL,
          SUBP,
          SUBP_STATUS_CD,
          POINT_NONSAMPLE_REASN_CD
        );
        CREATE TABLE condition_opportunity_source (
          SOURCE_COND_CN TEXT PRIMARY KEY,
          PLT_CN TEXT NOT NULL,
          CONDID,
          COND_STATUS_CD,
          COND_NONSAMPLE_REASN_CD,
          PROP_BASIS,
          CONDPROP_UNADJ,
          SUBPPROP_UNADJ,
          MACRPROP_UNADJ
        );
        CREATE TABLE subplot_condition_relation (
          SOURCE_SUBP_COND_CN TEXT PRIMARY KEY,
          PLT_CN TEXT NOT NULL,
          SUBP,
          CONDID
        );
        """
    )
    con.executemany(
        "INSERT INTO metadata(key,value) VALUES (?,?)",
        [
            ("TASK_ID", TASK_ID),
            ("BINDING_FINGERPRINT", binding_fingerprint),
            ("SCHEMA_FINGERPRINT", SCHEMA_FINGERPRINT),
            ("LAYER2_BUILD_FINGERPRINT", LAYER2_BUILD_FINGERPRINT),
            ("BUILDER_SOURCE_SHA256", builder_source_sha256()),
            ("SOURCE_BINDING_MODE", CFG["source_binding_mode"]),
            ("SPECIES_BLIND", "YES"),
        ],
    )
    con.commit()
    con.close()


def meta_get(con: sqlite3.Connection, key: str) -> str | None:
    row = con.execute("SELECT value FROM metadata WHERE key=?", (key,)).fetchone()
    return None if row is None else str(row[0])


def meta_set(con: sqlite3.Connection, key: str, value: Any) -> None:
    con.execute("INSERT OR REPLACE INTO metadata(key,value) VALUES (?,?)", (key, str(value)))


def load_f0_checkpoint() -> dict[str, Any]:
    con = sqlite3.connect(LAYER2_BUILDING)
    if meta_get(con, "F0_COMPLETE") == "YES":
        n = con.execute("SELECT COUNT(*) FROM f0_linkage").fetchone()[0]
        a = con.execute("SELECT COUNT(*) FROM f0_linkage WHERE fold='A'").fetchone()[0]
        b = con.execute("SELECT COUNT(*) FROM f0_linkage WHERE fold='B'").fetchone()[0]
        if (n, a, b) == (CFG["expected_f0"], CFG["expected_a"], CFG["expected_b"]):
            ids = {r[0] for r in con.execute("SELECT PLT_CN FROM f0_linkage")}
            con.close()
            log("LAYER2 F0 checkpoint: REUSED_AFTER_V01_1_VALIDATION")
            return {"ids": ids, "f0": n, "A": a, "B": b, "overlap": 0, "reused": True}
        con.close()
        raise RuntimeError("invalid F0 checkpoint counts")

    substrate = readonly_connect(Path(CFG["frozen_substrate_sqlite_path"]))
    rows = substrate.execute(
        """SELECT PLT_CN, permanent_plot_id, plot_visit_identity, fold, STATECD, EVALID,
                  source_eu, DESIGNCD, MANUAL
           FROM plot_visit_design_core ORDER BY PLT_CN"""
    ).fetchall()
    substrate.close()
    n = len(rows)
    a = sum(1 for r in rows if r[3] == "A")
    b = sum(1 for r in rows if r[3] == "B")
    if (n, a, b) != (CFG["expected_f0"], CFG["expected_a"], CFG["expected_b"]):
        raise RuntimeError(f"frozen F0 count mismatch: {(n,a,b)}")
    if len({r[0] for r in rows}) != n:
        raise RuntimeError("duplicate PLT_CN in frozen F0")
    a_perm = {r[1] for r in rows if r[3] == "A" and r[1]}
    b_perm = {r[1] for r in rows if r[3] == "B" and r[1]}
    overlap = len(a_perm & b_perm)
    if overlap != 0:
        raise RuntimeError(f"A/B permanent-plot overlap={overlap}")
    con.executemany(
        """INSERT INTO f0_linkage
           (PLT_CN,permanent_plot_id,plot_visit_identity,fold,STATECD,EVALID,source_eu,DESIGNCD_FROZEN,MANUAL_FROZEN,substrate_source_table,substrate_source_key)
           VALUES (?,?,?,?,?,?,?,?,?,'plot_visit_design_core','PLT_CN')""",
        rows,
    )
    meta_set(con, "F0_COUNT", n)
    meta_set(con, "A_COUNT", a)
    meta_set(con, "B_COUNT", b)
    meta_set(con, "AB_PERMANENT_PLOT_OVERLAP", overlap)
    meta_set(con, "F0_COMPLETE", "YES")
    con.commit()
    ids = {r[0] for r in rows}
    con.close()
    log(f"LAYER2 F0 checkpoint: built; F0={n}; A={a}; B={b}; overlap={overlap}")
    return {"ids": ids, "f0": n, "A": a, "B": b, "overlap": overlap, "reused": False}


def extract_source_table(
    ids: set[str],
    layer1: sqlite3.Connection,
    table: str,
    select_columns: list[str],
    dest_table: str,
    insert_sql: str,
) -> tuple[int, bool]:
    stage_key = table.upper() + "_COMPLETE"
    count_key = table.upper() + "_ROW_COUNT"
    dest = sqlite3.connect(LAYER2_BUILDING)
    if meta_get(dest, stage_key) == "YES":
        n = dest.execute(f'SELECT COUNT(*) FROM "{dest_table}"').fetchone()[0]
        if str(n) == meta_get(dest, count_key):
            dest.close()
            log(f"LAYER2 {table} checkpoint: REUSED_AFTER_V01_1_VALIDATION; rows={n}")
            return n, True
        dest.close()
        raise RuntimeError(f"invalid table checkpoint for {table}")
    dest.execute(f'DELETE FROM "{dest_table}"')
    dest.commit()
    quoted = ",".join(f'"{c}"' for c in select_columns)
    cursor = layer1.execute(f'SELECT {quoted} FROM "{table}"')
    batch: list[tuple[Any, ...]] = []
    matched = 0
    scanned = 0
    for row in cursor:
        scanned += 1
        plt_cn = "" if row[1] is None else str(row[1])
        if plt_cn in ids:
            batch.append(tuple(row))
            matched += 1
            if len(batch) >= 20_000:
                dest.executemany(insert_sql, batch)
                dest.commit()
                batch.clear()
        if scanned % 1_000_000 == 0:
            log(f"LAYER2 {table}: scanned={scanned}; matched={matched}")
    if batch:
        dest.executemany(insert_sql, batch)
        dest.commit()
    meta_set(dest, count_key, matched)
    meta_set(dest, stage_key, "YES")
    dest.commit()
    dest.close()
    log(f"LAYER2 {table} checkpoint: built; scanned={scanned}; matched={matched}")
    return matched, False


def validate_existing_layer2(binding_fingerprint: str) -> dict[str, Any] | None:
    if not (LAYER2_DB.is_file() and LAYER2_CKPT.is_file()):
        return None
    try:
        checkpoint = json.loads(LAYER2_CKPT.read_text(encoding="utf-8"))
        if checkpoint.get("task_id") != TASK_ID:
            return None
        if checkpoint.get("schema_fingerprint") != SCHEMA_FINGERPRINT:
            return None
        if checkpoint.get("database_sha256") != sha256(LAYER2_DB):
            return None
        con = readonly_connect(LAYER2_DB)
        integrity = con.execute("PRAGMA integrity_check").fetchone()[0]
        counts = {t: con.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0] for t in LAYER2_SCHEMA}
        con.close()
        if integrity != "ok" or counts != checkpoint.get("row_counts"):
            return None
        prior_binding = checkpoint.get("binding_fingerprint")
        checkpoint["original_builder_source_sha256"] = checkpoint.get("original_builder_source_sha256", checkpoint.get("builder_source_sha256", ""))
        checkpoint["binding_fingerprint"] = binding_fingerprint
        checkpoint["layer2_build_fingerprint"] = LAYER2_BUILD_FINGERPRINT
        checkpoint["last_validation_builder_source_sha256"] = builder_source_sha256()
        checkpoint["reuse_validation"] = "REUSED_AFTER_V01_1_VALIDATION: protected inputs, Layer1 restart metadata, schema fingerprint, database SHA, row counts, and integrity_check all passed"
        checkpoint["prior_binding_fingerprint"] = prior_binding
        checkpoint["reused"] = True
        write_json(LAYER2_CKPT, checkpoint)
        log("LAYER2 final checkpoint: REUSED_AFTER_V01_1_VALIDATION")
        return checkpoint
    except Exception:
        return None


def build_layer2(binding_fingerprint: str) -> dict[str, Any]:
    existing = validate_existing_layer2(binding_fingerprint)
    if existing is not None:
        return existing
    log("STAGE LAYER2_EXTRACTION: begin")
    create_layer2_building(binding_fingerprint)
    f0meta = load_f0_checkpoint()
    layer1 = readonly_connect(Path(CFG["layer1_sqlite_path"]))
    required_tables = {r[0] for r in layer1.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    missing_tables = {"PLOT", "SUBPLOT", "COND", "SUBP_COND"} - required_tables
    if missing_tables:
        layer1.close()
        raise RuntimeError(f"Layer 1 missing required tables: {sorted(missing_tables)}")
    extraction: dict[str, dict[str, Any]] = {}
    specs = [
        (
            "PLOT",
            ["CN", "CN", "PLOT_STATUS_CD", "PLOT_NONSAMPLE_REASN_CD", "SAMP_METHOD_CD", "SUBP_EXAMINE_CD", "MACRO_BREAKPOINT_DIA", "DESIGNCD", "MANUAL"],
            "plot_opportunity_source",
            "INSERT INTO plot_opportunity_source VALUES (?,?,?,?,?,?,?,?,?)",
        ),
        (
            "SUBPLOT",
            ["CN", "PLT_CN", "SUBP", "SUBP_STATUS_CD", "POINT_NONSAMPLE_REASN_CD"],
            "subplot_opportunity_source",
            "INSERT INTO subplot_opportunity_source VALUES (?,?,?,?,?)",
        ),
        (
            "COND",
            ["CN", "PLT_CN", "CONDID", "COND_STATUS_CD", "COND_NONSAMPLE_REASN_CD", "PROP_BASIS", "CONDPROP_UNADJ", "SUBPPROP_UNADJ", "MACRPROP_UNADJ"],
            "condition_opportunity_source",
            "INSERT INTO condition_opportunity_source VALUES (?,?,?,?,?,?,?,?,?)",
        ),
        (
            "SUBP_COND",
            ["CN", "PLT_CN", "SUBP", "CONDID"],
            "subplot_condition_relation",
            "INSERT INTO subplot_condition_relation VALUES (?,?,?,?)",
        ),
    ]
    for table, columns, dest_table, insert_sql in specs:
        source_columns = {r[1] for r in layer1.execute(f'PRAGMA table_info("{table}")')}
        missing = set(columns) - source_columns
        if missing:
            layer1.close()
            raise RuntimeError(f"Layer 1 {table} missing columns: {sorted(missing)}")
        n, reused = extract_source_table(f0meta["ids"], layer1, table, columns, dest_table, insert_sql)
        extraction[table] = {"rows": n, "reused": reused}
    layer1.close()

    con = sqlite3.connect(LAYER2_BUILDING)
    plot_n = con.execute("SELECT COUNT(*) FROM plot_opportunity_source").fetchone()[0]
    expected_plot_matches = CFG["expected_f0"] - 4232
    if plot_n != expected_plot_matches:
        con.close()
        raise RuntimeError(
            f"Layer 1 PLOT/F0 linkage count={plot_n}, expected accepted Local match={expected_plot_matches}; source-key invariant conflict triggers full-hash re-binding"
        )
    meta_set(con, "F0_WITHOUT_LAYER1_PLOT_MATCH", CFG["expected_f0"] - plot_n)
    orphan_counts = {}
    for table in ("plot_opportunity_source", "subplot_opportunity_source", "condition_opportunity_source", "subplot_condition_relation"):
        orphan_counts[table] = con.execute(
            f'SELECT COUNT(*) FROM "{table}" x LEFT JOIN f0_linkage f ON f.PLT_CN=x.PLT_CN WHERE f.PLT_CN IS NULL'
        ).fetchone()[0]
    if any(orphan_counts.values()):
        con.close()
        raise RuntimeError(f"Layer 2 orphan rows: {orphan_counts}")
    con.executescript(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_plot_plt ON plot_opportunity_source(PLT_CN);
        CREATE INDEX IF NOT EXISTS idx_subplot_plt_subp ON subplot_opportunity_source(PLT_CN,SUBP);
        CREATE INDEX IF NOT EXISTS idx_condition_plt_cond ON condition_opportunity_source(PLT_CN,CONDID);
        CREATE INDEX IF NOT EXISTS idx_subpcond_plt_subp_cond ON subplot_condition_relation(PLT_CN,SUBP,CONDID);
        """
    )
    meta_set(con, "LAYER2_COMPLETE", "YES")
    meta_set(con, "LAYER2_PROVENANCE_CLASS", "PROJECT-INDUCED CANDIDATE LAYER 2 SUBSTRATE")
    con.commit()
    integrity = con.execute("PRAGMA integrity_check").fetchone()[0]
    counts = {t: con.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0] for t in LAYER2_SCHEMA}
    con.close()
    if integrity != "ok":
        raise RuntimeError(f"Layer 2 integrity_check={integrity}")
    if LAYER2_DB.exists():
        LAYER2_DB.unlink()
    os.replace(LAYER2_BUILDING, LAYER2_DB)
    db_hash = sha256(LAYER2_DB)
    checkpoint = {
        "task_id": TASK_ID,
        "checkpoint": "LAYER2_COMPLETE",
        "completion_marker": "COMPLETE",
        "binding_fingerprint": binding_fingerprint,
        "schema_fingerprint": SCHEMA_FINGERPRINT,
        "layer2_build_fingerprint": LAYER2_BUILD_FINGERPRINT,
        "builder_source_sha256": builder_source_sha256(),
        "source_binding_mode": CFG["source_binding_mode"],
        "database_path": str(LAYER2_DB),
        "database_sha256": db_hash,
        "row_counts": counts,
        "integrity_check": integrity,
        "orphan_counts": orphan_counts,
        "scientific_scope": "species-blind source-native legal-opportunity fields and required keys only",
        "reused": False,
    }
    write_json(LAYER2_CKPT, checkpoint)
    log(f"STAGE LAYER2_EXTRACTION: complete; sha256={db_hash}; row_counts={counts}")
    return checkpoint


RULE_SPEC = {
    "rule_order": [
        "plot_source_binding",
        "plot_status",
        "sampling_method",
        "examination_scope",
        "direct_element_status",
        "accessible_condition_status",
        "diameter_frame",
        "condition_frame_basis",
    ],
    "accepted_code_semantics": {
        "PLOT_STATUS_CD": {"1": "sampled with accessible forest possible", "2": "sampled with no accessible forest", "3": "nonsampled"},
        "SAMP_METHOD_CD": {"1": "field visit", "2": "remote determination"},
        "SUBP_EXAMINE_CD": {"1": "subplot-1 center directly examined; other subplots inferred", "4": "all four subplots fully described"},
        "SUBP_STATUS_CD": {"1": "sampled with accessible forest", "2": "sampled with no accessible forest", "3": "nonsampled with possible forest"},
        "COND_STATUS_CD": {"1": "accessible forest", "2": "nonforest", "3": "noncensus water", "4": "census water", "5": "nonsampled possible forest"},
        "PROP_BASIS": {"SUBP": "subplot basis", "MACR": "macroplot basis"},
    },
    "diameter_rules": {
        "positive_breakpoint_gt_5": "5<=DIA<breakpoint uses subplot frame; DIA>=breakpoint uses macroplot frame",
        "positive_breakpoint_le_5": "all frozen DIA>=5 target diameters use macroplot frame",
        "no_positive_breakpoint": "explicitly unresolved; absence does not prove subplot-only frame",
    },
    "terminal_label_priority": "after validating plot code: sampling_method=2 remote; then nonremote plot_status=3 or 2; then downstream opportunity gates",
    "firewall": "no TREE query and no species/outcome field",
}
RULE_FINGERPRINT = canonical_hash(RULE_SPEC)


STATE_ROWS = [
    {
        "state_code": "NO_Q1_FOREST_OPPORTUNITY_PLOT_STATUS_2",
        "classification_status": "FULLY_CLASSIFIED",
        "opportunity_presence": "NO_DIRECT_Q1_FOREST_OPPORTUNITY",
        "rule": "PLOT_STATUS_CD=2",
        "scientific_meaning": "Sampled plot with no accessible forest; not a Q1 forest species nondetection opportunity.",
        "provenance_class": "PROJECT-INDUCED CANDIDATE LAYER 3 OPERATOR",
    },
    {
        "state_code": "NO_DIRECT_OPPORTUNITY_PLOT_STATUS_3",
        "classification_status": "FULLY_CLASSIFIED",
        "opportunity_presence": "NO_DIRECT_Q1_FOREST_OPPORTUNITY",
        "rule": "PLOT_STATUS_CD=3",
        "scientific_meaning": "Nonsampled plot; no direct field opportunity.",
        "provenance_class": "PROJECT-INDUCED CANDIDATE LAYER 3 OPERATOR",
    },
    {
        "state_code": "REMOTE_INFORMATION_NO_DIRECT_TREE_OPPORTUNITY",
        "classification_status": "FULLY_CLASSIFIED",
        "opportunity_presence": "NO_DIRECT_Q1_FOREST_OPPORTUNITY",
        "rule": "accepted PLOT_STATUS_CD and SAMP_METHOD_CD=2; plot status is retained as a separate dimension",
        "scientific_meaning": "Remote/non-field information is explicitly retained and is not promoted to a tree nondetection opportunity.",
        "provenance_class": "PROJECT-INDUCED CANDIDATE LAYER 3 OPERATOR",
    },
    {
        "state_code": "NO_DIRECT_OPPORTUNITY_ON_EXAMINED_ELEMENTS",
        "classification_status": "FULLY_CLASSIFIED",
        "opportunity_presence": "NO_DIRECT_Q1_FOREST_OPPORTUNITY",
        "rule": "field visit and resolved examination scope, but every directly examined element has SUBP_STATUS_CD in {2,3}",
        "scientific_meaning": "All direct elements are explicitly without accessible sampled forest opportunity.",
        "provenance_class": "PROJECT-INDUCED CANDIDATE LAYER 3 OPERATOR",
    },
    {
        "state_code": "DIRECT_FIELD_OPPORTUNITY_SUBPLOT1_ONLY_SPLIT_FRAME",
        "classification_status": "FULLY_CLASSIFIED",
        "opportunity_presence": "DIRECT_Q1_FOREST_OPPORTUNITY",
        "rule": "field visit; SUBP_EXAMINE_CD=1; subplot 1 sampled accessible; accessible conditions resolved; positive breakpoint>5; macro basis resolved",
        "scientific_meaning": "Direct opportunity is limited to subplot-1 center and is diameter-split across subplot/macroplot frames.",
        "provenance_class": "PROJECT-INDUCED CANDIDATE LAYER 3 OPERATOR",
    },
    {
        "state_code": "DIRECT_FIELD_OPPORTUNITY_ALL_FOUR_SAMPLED_SPLIT_FRAME",
        "classification_status": "FULLY_CLASSIFIED",
        "opportunity_presence": "DIRECT_Q1_FOREST_OPPORTUNITY",
        "rule": "field visit; SUBP_EXAMINE_CD=4; all four direct elements SUBP_STATUS_CD=1; accessible conditions resolved; positive breakpoint>5; macro basis resolved",
        "scientific_meaning": "Four described spatial elements are sampled accessible; they are spatial replicates, not repeated detections of an identical unit.",
        "provenance_class": "PROJECT-INDUCED CANDIDATE LAYER 3 OPERATOR",
    },
    {
        "state_code": "DIRECT_FIELD_OPPORTUNITY_PARTIAL_ELEMENTS_SPLIT_FRAME",
        "classification_status": "FULLY_CLASSIFIED",
        "opportunity_presence": "DIRECT_Q1_FOREST_OPPORTUNITY",
        "rule": "field visit; SUBP_EXAMINE_CD=4; one to three direct elements SUBP_STATUS_CD=1 and remaining elements explicitly status 2/3; accessible conditions resolved; positive breakpoint>5; macro basis resolved",
        "scientific_meaning": "Direct opportunity exists only on the explicitly sampled-accessible subset of described elements.",
        "provenance_class": "PROJECT-INDUCED CANDIDATE LAYER 3 OPERATOR",
    },
    {
        "state_code": "DIRECT_FIELD_OPPORTUNITY_MACRO_ALL_TARGET_DIAMETERS",
        "classification_status": "FULLY_CLASSIFIED",
        "opportunity_presence": "DIRECT_Q1_FOREST_OPPORTUNITY",
        "rule": "otherwise direct field opportunity with positive breakpoint<=5 and macro basis resolved",
        "scientific_meaning": "All frozen DIA>=5 target diameters fall in the macroplot frame.",
        "provenance_class": "PROJECT-INDUCED CANDIDATE LAYER 3 OPERATOR",
    },
    {
        "state_code": "UNRESOLVED_PLOT_SOURCE_BINDING",
        "classification_status": "EXPLICITLY_UNRESOLVED",
        "opportunity_presence": "UNRESOLVED",
        "rule": "zero or multiple Layer 1 PLOT rows for one F0 PLT_CN",
        "scientific_meaning": "Plot-source identity is not unique.",
        "provenance_class": "OPEN / UNRESOLVED",
    },
    {
        "state_code": "UNRESOLVED_PLOT_STATUS",
        "classification_status": "EXPLICITLY_UNRESOLVED",
        "opportunity_presence": "UNRESOLVED",
        "rule": "PLOT_STATUS_CD missing or outside accepted codes",
        "scientific_meaning": "Plot sampling/forest status cannot be legally interpreted.",
        "provenance_class": "OPEN / UNRESOLVED",
    },
    {
        "state_code": "UNRESOLVED_SAMPLING_METHOD",
        "classification_status": "EXPLICITLY_UNRESOLVED",
        "opportunity_presence": "UNRESOLVED",
        "rule": "PLOT_STATUS_CD=1 and SAMP_METHOD_CD missing or outside accepted codes",
        "scientific_meaning": "Actual field versus remote opportunity is unresolved.",
        "provenance_class": "OPEN / UNRESOLVED",
    },
    {
        "state_code": "UNRESOLVED_EXAMINATION_SCOPE",
        "classification_status": "EXPLICITLY_UNRESOLVED",
        "opportunity_presence": "UNRESOLVED",
        "rule": "field visit and SUBP_EXAMINE_CD missing or outside {1,4}",
        "scientific_meaning": "Directly examined spatial extent is unresolved.",
        "provenance_class": "OPEN / UNRESOLVED",
    },
    {
        "state_code": "UNRESOLVED_SUBPLOT_STATUS_COVERAGE",
        "classification_status": "EXPLICITLY_UNRESOLVED",
        "opportunity_presence": "UNRESOLVED",
        "rule": "missing, duplicate, or uninterpretable status for any required directly examined subplot",
        "scientific_meaning": "The direct sampled-element set cannot be fully determined.",
        "provenance_class": "OPEN / UNRESOLVED",
    },
    {
        "state_code": "UNRESOLVED_CONDITION_STATUS_OR_RELATION",
        "classification_status": "EXPLICITLY_UNRESOLVED",
        "opportunity_presence": "UNRESOLVED",
        "rule": "sampled-accessible direct element exists but condition status is missing/uninterpretable or contradicts absence of any accessible condition",
        "scientific_meaning": "Accessible forest condition opportunity is not fully resolved.",
        "provenance_class": "OPEN / UNRESOLVED",
    },
    {
        "state_code": "UNRESOLVED_DIAMETER_FRAME_NO_POSITIVE_BREAKPOINT",
        "classification_status": "EXPLICITLY_UNRESOLVED",
        "opportunity_presence": "UNRESOLVED",
        "rule": "otherwise direct opportunity, but MACRO_BREAKPOINT_DIA is absent, zero, or non-positive",
        "scientific_meaning": "No positive breakpoint does not prove subplot-only frame; DIA>=5 legal frame remains explicit unresolved.",
        "provenance_class": "OPEN / UNRESOLVED",
    },
    {
        "state_code": "UNRESOLVED_DIAMETER_FRAME_NONNUMERIC_BREAKPOINT",
        "classification_status": "EXPLICITLY_UNRESOLVED",
        "opportunity_presence": "UNRESOLVED",
        "rule": "otherwise direct opportunity, but breakpoint is nonnumeric",
        "scientific_meaning": "Diameter/tally frame cannot be interpreted from the retained source value.",
        "provenance_class": "OPEN / UNRESOLVED",
    },
    {
        "state_code": "UNRESOLVED_MACRO_CONDITION_BASIS",
        "classification_status": "EXPLICITLY_UNRESOLVED",
        "opportunity_presence": "UNRESOLVED",
        "rule": "positive breakpoint with one or more accessible condition rows lacking MACR PROP_BASIS or numeric MACRPROP_UNADJ",
        "scientific_meaning": "Diameter-split opportunity exists in principle, but condition/frame representation is incomplete.",
        "provenance_class": "OPEN / UNRESOLVED",
    },
]
STATE_CODES = {r["state_code"] for r in STATE_ROWS}


def frame_state(raw: Any) -> tuple[str, float | None]:
    if raw is None or str(raw).strip() == "":
        return "FRAME_UNRESOLVED_NO_POSITIVE_BREAKPOINT", None
    number = num_or_none(raw)
    if number is None:
        return "FRAME_UNRESOLVED_NONNUMERIC_BREAKPOINT", None
    if number <= 0:
        return "FRAME_UNRESOLVED_NO_POSITIVE_BREAKPOINT", number
    if number <= 5:
        return "MACRO_FRAME_ALL_TARGET_DIAMETERS", number
    return "SUBPLOT_MACRO_SPLIT_AT_BREAKPOINT", number


def classify_one(
    plot_count: int,
    plot_status: str,
    samp: str,
    exam: str,
    direct_mask: int,
    direct_duplicates: int,
    direct_s1: int,
    direct_s2: int,
    direct_s3: int,
    direct_other: int,
    cond_rows: int,
    linked_accessible_conditions: int,
    linked_relation_unresolved: int,
    linked_accessible_basis_macr: int,
    linked_accessible_macrprop_numeric: int,
    raw_breakpoint: Any,
) -> tuple[str, str, str, str, str, str, str, str]:
    method_state = {"1": "FIELD_VISIT", "2": "REMOTE_NONFIELD", "": "MISSING"}.get(samp, "UNINTERPRETED")
    exam_state = {"1": "SUBPLOT1_CENTER_ONLY_DIRECT", "4": "ALL_FOUR_FULLY_DESCRIBED", "": "MISSING"}.get(exam, "UNINTERPRETED")
    fstate, bp = frame_state(raw_breakpoint)
    if plot_count != 1:
        return "UNRESOLVED_PLOT_SOURCE_BINDING", "EXPLICITLY_UNRESOLVED", "UNRESOLVED_PLOT_SOURCE_BINDING", "UNRESOLVED", method_state, exam_state, "UNRESOLVED", fstate
    if plot_status not in {"1", "2", "3"}:
        return "UNRESOLVED_PLOT_STATUS", "EXPLICITLY_UNRESOLVED", "UNRESOLVED_PLOT_STATUS", "UNRESOLVED", method_state, exam_state, "NOT_EVALUATED", fstate
    if samp == "2":
        return "REMOTE_INFORMATION_NO_DIRECT_TREE_OPPORTUNITY", "FULLY_CLASSIFIED", "", "NO_DIRECT_Q1_FOREST_OPPORTUNITY", method_state, exam_state, "NOT_REQUIRED", fstate
    if plot_status == "3":
        return "NO_DIRECT_OPPORTUNITY_PLOT_STATUS_3", "FULLY_CLASSIFIED", "", "NO_DIRECT_Q1_FOREST_OPPORTUNITY", method_state, exam_state, "NOT_REQUIRED", fstate
    if plot_status == "2":
        return "NO_Q1_FOREST_OPPORTUNITY_PLOT_STATUS_2", "FULLY_CLASSIFIED", "", "NO_DIRECT_Q1_FOREST_OPPORTUNITY", method_state, exam_state, "NOT_REQUIRED", fstate
    if samp not in {"1", "2"}:
        return "UNRESOLVED_SAMPLING_METHOD", "EXPLICITLY_UNRESOLVED", "UNRESOLVED_SAMPLING_METHOD", "UNRESOLVED", method_state, exam_state, "NOT_EVALUATED", fstate
    if exam not in {"1", "4"}:
        return "UNRESOLVED_EXAMINATION_SCOPE", "EXPLICITLY_UNRESOLVED", "UNRESOLVED_EXAMINATION_SCOPE", "UNRESOLVED", method_state, exam_state, "NOT_EVALUATED", fstate
    expected_mask = 1 if exam == "1" else 15
    if direct_mask != expected_mask or direct_duplicates > 0 or direct_other > 0:
        return "UNRESOLVED_SUBPLOT_STATUS_COVERAGE", "EXPLICITLY_UNRESOLVED", "UNRESOLVED_SUBPLOT_STATUS_COVERAGE", "UNRESOLVED", method_state, exam_state, "UNRESOLVED", fstate
    if direct_s1 == 0:
        return "NO_DIRECT_OPPORTUNITY_ON_EXAMINED_ELEMENTS", "FULLY_CLASSIFIED", "", "NO_DIRECT_Q1_FOREST_OPPORTUNITY", method_state, exam_state, "NO_SAMPLED_ACCESSIBLE_DIRECT_ELEMENT", fstate
    sampling_state = f"DIRECT_ELEMENTS_STATUS1={direct_s1};STATUS2={direct_s2};STATUS3={direct_s3}"
    if cond_rows == 0 or linked_accessible_conditions == 0 or linked_relation_unresolved > 0:
        return "UNRESOLVED_CONDITION_STATUS_OR_RELATION", "EXPLICITLY_UNRESOLVED", "UNRESOLVED_CONDITION_STATUS_OR_RELATION", "UNRESOLVED", method_state, exam_state, sampling_state, fstate
    if fstate == "FRAME_UNRESOLVED_NO_POSITIVE_BREAKPOINT":
        return "UNRESOLVED_DIAMETER_FRAME_NO_POSITIVE_BREAKPOINT", "EXPLICITLY_UNRESOLVED", "UNRESOLVED_DIAMETER_FRAME_NO_POSITIVE_BREAKPOINT", "UNRESOLVED", method_state, exam_state, sampling_state, fstate
    if fstate == "FRAME_UNRESOLVED_NONNUMERIC_BREAKPOINT":
        return "UNRESOLVED_DIAMETER_FRAME_NONNUMERIC_BREAKPOINT", "EXPLICITLY_UNRESOLVED", "UNRESOLVED_DIAMETER_FRAME_NONNUMERIC_BREAKPOINT", "UNRESOLVED", method_state, exam_state, sampling_state, fstate
    if linked_accessible_basis_macr != linked_accessible_conditions or linked_accessible_macrprop_numeric != linked_accessible_conditions:
        return "UNRESOLVED_MACRO_CONDITION_BASIS", "EXPLICITLY_UNRESOLVED", "UNRESOLVED_MACRO_CONDITION_BASIS", "UNRESOLVED", method_state, exam_state, sampling_state, fstate
    if fstate == "MACRO_FRAME_ALL_TARGET_DIAMETERS":
        return "DIRECT_FIELD_OPPORTUNITY_MACRO_ALL_TARGET_DIAMETERS", "FULLY_CLASSIFIED", "", "DIRECT_Q1_FOREST_OPPORTUNITY", method_state, exam_state, sampling_state, fstate
    if exam == "1":
        state = "DIRECT_FIELD_OPPORTUNITY_SUBPLOT1_ONLY_SPLIT_FRAME"
    elif direct_s1 == 4:
        state = "DIRECT_FIELD_OPPORTUNITY_ALL_FOUR_SAMPLED_SPLIT_FRAME"
    else:
        state = "DIRECT_FIELD_OPPORTUNITY_PARTIAL_ELEMENTS_SPLIT_FRAME"
    return state, "FULLY_CLASSIFIED", "", "DIRECT_Q1_FOREST_OPPORTUNITY", method_state, exam_state, sampling_state, fstate


def validate_existing_layer3(layer2_hash: str) -> dict[str, Any] | None:
    if not LAYER3_CKPT.is_file():
        return None
    try:
        checkpoint = json.loads(LAYER3_CKPT.read_text(encoding="utf-8"))
        if checkpoint.get("task_id") != TASK_ID or checkpoint.get("layer2_sha256") != layer2_hash or checkpoint.get("rule_fingerprint") != RULE_FINGERPRINT or checkpoint.get("builder_source_sha256") != builder_source_sha256():
            return None
        for name, expected in checkpoint.get("output_sha256", {}).items():
            p = ROOT / name
            if not p.is_file() or sha256(p) != expected:
                return None
        if checkpoint.get("f0_rows") != CFG["expected_f0"]:
            return None
        checkpoint["reused"] = True
        log("LAYER3 final checkpoint: REUSED_AFTER_V01_1_VALIDATION")
        return checkpoint
    except Exception:
        return None


def build_layer3(layer2_checkpoint: dict[str, Any]) -> dict[str, Any]:
    existing = validate_existing_layer3(layer2_checkpoint["database_sha256"])
    if existing is not None:
        return existing
    log("STAGE LAYER3_CLASSIFICATION: begin")
    con = readonly_connect(LAYER2_DB)
    f0 = con.execute(
        """SELECT PLT_CN, permanent_plot_id, plot_visit_identity, fold, STATECD, EVALID, source_eu,
                  DESIGNCD_FROZEN, MANUAL_FROZEN
           FROM f0_linkage ORDER BY PLT_CN"""
    ).fetchall()
    n = len(f0)
    index = {str(r[0]): i for i, r in enumerate(f0)}
    if len(index) != n:
        raise RuntimeError("duplicate PLT_CN during Layer 3 classification")

    plot_count = [0] * n
    plot_status = [""] * n
    plot_reason = [""] * n
    samp = [""] * n
    exam = [""] * n
    breakpoint_raw: list[Any] = [None] * n
    design_raw = [""] * n
    manual_raw = [""] * n
    for row in con.execute(
        "SELECT PLT_CN,PLOT_STATUS_CD,PLOT_NONSAMPLE_REASN_CD,SAMP_METHOD_CD,SUBP_EXAMINE_CD,MACRO_BREAKPOINT_DIA,DESIGNCD,MANUAL FROM plot_opportunity_source"
    ):
        i = index[str(row[0])]
        plot_count[i] += 1
        if plot_count[i] == 1:
            plot_status[i] = norm_code(row[1])
            plot_reason[i] = norm_code(row[2])
            samp[i] = norm_code(row[3])
            exam[i] = norm_code(row[4])
            breakpoint_raw[i] = row[5]
            design_raw[i] = norm_code(row[6])
            manual_raw[i] = norm_code(row[7])

    direct_mask = [0] * n
    direct_dup = [0] * n
    direct_s1 = [0] * n
    direct_s2 = [0] * n
    direct_s3 = [0] * n
    direct_other = [0] * n
    subplot_rows = [0] * n
    sampled_direct_elements: set[tuple[str, str]] = set()
    all_subp_status_codes: Counter[str] = Counter()
    for row in con.execute("SELECT PLT_CN,SUBP,SUBP_STATUS_CD FROM subplot_opportunity_source"):
        i = index[str(row[0])]
        subplot_rows[i] += 1
        subp = norm_code(row[1])
        status = norm_code(row[2])
        all_subp_status_codes[status or "<MISSING>"] += 1
        required = (exam[i] == "1" and subp == "1") or (exam[i] == "4" and subp in {"1", "2", "3", "4"})
        if not required:
            continue
        bit = 1 << (int(subp) - 1)
        if direct_mask[i] & bit:
            direct_dup[i] += 1
            continue
        direct_mask[i] |= bit
        if status == "1":
            direct_s1[i] += 1
            sampled_direct_elements.add((str(row[0]), subp))
        elif status == "2":
            direct_s2[i] += 1
        elif status == "3":
            direct_s3[i] += 1
        else:
            direct_other[i] += 1

    cond_rows = [0] * n
    cond_s1 = [0] * n
    cond_s2to4 = [0] * n
    cond_s5 = [0] * n
    cond_other = [0] * n
    acc_basis_macr = [0] * n
    acc_basis_subp = [0] * n
    acc_basis_other = [0] * n
    acc_macrprop_numeric = [0] * n
    macrprop_numeric_all = [0] * n
    all_cond_status_codes: Counter[str] = Counter()
    all_prop_basis_codes: Counter[str] = Counter()
    condition_details: dict[tuple[str, str], tuple[str, str, bool] | None] = {}
    for row in con.execute("SELECT PLT_CN,CONDID,COND_STATUS_CD,PROP_BASIS,MACRPROP_UNADJ FROM condition_opportunity_source"):
        i = index[str(row[0])]
        cond_rows[i] += 1
        condid = norm_code(row[1])
        status = norm_code(row[2])
        basis = norm_code(row[3])
        all_cond_status_codes[status or "<MISSING>"] += 1
        all_prop_basis_codes[basis or "<MISSING>"] += 1
        numeric_macrprop = num_or_none(row[4]) is not None
        if numeric_macrprop:
            macrprop_numeric_all[i] += 1
        key = (str(row[0]), condid)
        if key in condition_details:
            condition_details[key] = None
        else:
            condition_details[key] = (status, basis, numeric_macrprop)
        if status == "1":
            cond_s1[i] += 1
            if basis == "MACR":
                acc_basis_macr[i] += 1
            elif basis == "SUBP":
                acc_basis_subp[i] += 1
            else:
                acc_basis_other[i] += 1
            if numeric_macrprop:
                acc_macrprop_numeric[i] += 1
        elif status in {"2", "3", "4"}:
            cond_s2to4[i] += 1
        elif status == "5":
            cond_s5[i] += 1
        else:
            cond_other[i] += 1

    relation_rows = [0] * n
    linked_accessible_relation_rows = [0] * n
    linked_accessible_condition_count = [0] * n
    linked_relation_unresolved = [0] * n
    linked_acc_basis_macr = [0] * n
    linked_acc_basis_subp = [0] * n
    linked_acc_basis_other = [0] * n
    linked_acc_macrprop_numeric = [0] * n
    linked_condition_seen: set[tuple[str, str]] = set()
    for plt_cn, subp_raw, condid_raw in con.execute("SELECT PLT_CN,SUBP,CONDID FROM subplot_condition_relation"):
        plt = str(plt_cn)
        i = index[plt]
        relation_rows[i] += 1
        subp = norm_code(subp_raw)
        condid = norm_code(condid_raw)
        if (plt, subp) not in sampled_direct_elements:
            continue
        detail = condition_details.get((plt, condid))
        if detail is None:
            linked_relation_unresolved[i] += 1
            continue
        status, basis, numeric_macrprop = detail
        if status != "1":
            continue
        linked_accessible_relation_rows[i] += 1
        cond_key = (plt, condid)
        if cond_key in linked_condition_seen:
            continue
        linked_condition_seen.add(cond_key)
        linked_accessible_condition_count[i] += 1
        if basis == "MACR":
            linked_acc_basis_macr[i] += 1
        elif basis == "SUBP":
            linked_acc_basis_subp[i] += 1
        else:
            linked_acc_basis_other[i] += 1
        if numeric_macrprop:
            linked_acc_macrprop_numeric[i] += 1
    con.close()

    row_fields = [
        "PLT_CN", "permanent_plot_id", "plot_visit_identity", "fold", "STATECD", "EVALID", "source_eu",
        "DESIGNCD", "MANUAL", "PLOT_STATUS_CD", "PLOT_NONSAMPLE_REASN_CD", "SAMP_METHOD_CD", "SUBP_EXAMINE_CD",
        "MACRO_BREAKPOINT_DIA", "method_state", "examination_state", "subplot_source_row_count",
        "direct_subplot_status1_count", "direct_subplot_status2_count", "direct_subplot_status3_count",
        "direct_subplot_unresolved_count", "condition_source_row_count", "accessible_condition_count",
        "nonforest_water_condition_count", "nonsampled_possible_forest_condition_count", "condition_unresolved_count",
        "accessible_condition_macr_basis_count", "accessible_condition_subp_basis_count", "accessible_condition_other_basis_count",
        "accessible_condition_numeric_macrprop_count", "subplot_condition_relation_count",
        "linked_direct_accessible_relation_count", "linked_accessible_condition_count", "linked_relation_unresolved_count",
        "linked_accessible_condition_macr_basis_count", "linked_accessible_condition_subp_basis_count",
        "linked_accessible_condition_other_basis_count", "linked_accessible_condition_numeric_macrprop_count", "frame_state",
        "legal_opportunity_class", "classification_status", "opportunity_presence", "unresolved_reason",
        "provenance_class", "species_blind",
    ]
    class_counter: Counter[str] = Counter()
    status_counter: Counter[str] = Counter()
    opportunity_counter: Counter[str] = Counter()
    frame_counter: Counter[str] = Counter()
    unresolved_counter: Counter[str] = Counter()
    fold_class: Counter[tuple[str, str, str]] = Counter()
    fold_status: Counter[tuple[str, str]] = Counter()
    group_class: Counter[tuple[str, str, str, str, str, str]] = Counter()
    group_total: Counter[tuple[str, str, str, str]] = Counter()
    fold_frame: Counter[tuple[str, str]] = Counter()
    positive_breakpoints: list[float] = []
    nonpositive_breakpoint_count = 0
    nonnumeric_breakpoint_count = 0
    sample_rows: list[dict[str, Any]] = []

    with FULL_F0_GZ.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0, compresslevel=9) as gz:
            import io
            with io.TextIOWrapper(gz, encoding="utf-8", newline="", write_through=True) as text:
                writer = csv.DictWriter(text, fieldnames=row_fields, lineterminator="\n")
                writer.writeheader()
                for i, base in enumerate(f0):
                    plt_cn, permanent_id, visit_id, fold, state, evalid, source_eu, design_frozen, manual_frozen = base
                    state_code, class_status, unresolved, presence, method_state, exam_state, sampling_state, fstate = classify_one(
                        plot_count[i], plot_status[i], samp[i], exam[i], direct_mask[i], direct_dup[i],
                        direct_s1[i], direct_s2[i], direct_s3[i], direct_other[i], cond_rows[i], linked_accessible_condition_count[i],
                        linked_relation_unresolved[i], linked_acc_basis_macr[i], linked_acc_macrprop_numeric[i], breakpoint_raw[i],
                    )
                    if state_code not in STATE_CODES:
                        raise RuntimeError(f"state absent from dictionary: {state_code}")
                    bp_num = num_or_none(breakpoint_raw[i])
                    if bp_num is not None and bp_num > 0:
                        positive_breakpoints.append(bp_num)
                    elif breakpoint_raw[i] is not None and str(breakpoint_raw[i]).strip() != "":
                        if bp_num is None:
                            nonnumeric_breakpoint_count += 1
                        else:
                            nonpositive_breakpoint_count += 1
                    provenance = "LOCAL/WORK DERIVED QUALIFICATION EVIDENCE"
                    record = {
                        "PLT_CN": plt_cn,
                        "permanent_plot_id": permanent_id or "",
                        "plot_visit_identity": visit_id,
                        "fold": fold,
                        "STATECD": state if state is not None else "",
                        "EVALID": evalid or "",
                        "source_eu": source_eu or "",
                        "DESIGNCD": design_raw[i] or norm_code(design_frozen),
                        "MANUAL": manual_raw[i] or norm_code(manual_frozen),
                        "PLOT_STATUS_CD": plot_status[i],
                        "PLOT_NONSAMPLE_REASN_CD": plot_reason[i],
                        "SAMP_METHOD_CD": samp[i],
                        "SUBP_EXAMINE_CD": exam[i],
                        "MACRO_BREAKPOINT_DIA": "" if breakpoint_raw[i] is None else breakpoint_raw[i],
                        "method_state": method_state,
                        "examination_state": exam_state,
                        "subplot_source_row_count": subplot_rows[i],
                        "direct_subplot_status1_count": direct_s1[i],
                        "direct_subplot_status2_count": direct_s2[i],
                        "direct_subplot_status3_count": direct_s3[i],
                        "direct_subplot_unresolved_count": direct_other[i] + direct_dup[i] + max(0, (1 if exam[i] == "1" else 4 if exam[i] == "4" else 0) - direct_mask[i].bit_count()),
                        "condition_source_row_count": cond_rows[i],
                        "accessible_condition_count": cond_s1[i],
                        "nonforest_water_condition_count": cond_s2to4[i],
                        "nonsampled_possible_forest_condition_count": cond_s5[i],
                        "condition_unresolved_count": cond_other[i],
                        "accessible_condition_macr_basis_count": acc_basis_macr[i],
                        "accessible_condition_subp_basis_count": acc_basis_subp[i],
                        "accessible_condition_other_basis_count": acc_basis_other[i],
                        "accessible_condition_numeric_macrprop_count": acc_macrprop_numeric[i],
                        "subplot_condition_relation_count": relation_rows[i],
                        "linked_direct_accessible_relation_count": linked_accessible_relation_rows[i],
                        "linked_accessible_condition_count": linked_accessible_condition_count[i],
                        "linked_relation_unresolved_count": linked_relation_unresolved[i],
                        "linked_accessible_condition_macr_basis_count": linked_acc_basis_macr[i],
                        "linked_accessible_condition_subp_basis_count": linked_acc_basis_subp[i],
                        "linked_accessible_condition_other_basis_count": linked_acc_basis_other[i],
                        "linked_accessible_condition_numeric_macrprop_count": linked_acc_macrprop_numeric[i],
                        "frame_state": fstate,
                        "legal_opportunity_class": state_code,
                        "classification_status": class_status,
                        "opportunity_presence": presence,
                        "unresolved_reason": unresolved,
                        "provenance_class": provenance,
                        "species_blind": "YES",
                    }
                    writer.writerow(record)
                    if len(sample_rows) < 100:
                        sample_rows.append(record.copy())
                    class_counter[state_code] += 1
                    status_counter[class_status] += 1
                    opportunity_counter[presence] += 1
                    frame_counter[fstate] += 1
                    if unresolved:
                        unresolved_counter[unresolved] += 1
                    fold_class[(str(fold), state_code, class_status)] += 1
                    fold_status[(str(fold), class_status)] += 1
                    fold_frame[(str(fold), fstate)] += 1
                    dimensions = [
                        ("ALL", "ALL", "", ""),
                        ("FOLD", str(fold), "", ""),
                        ("STATE_EVALID", str(state), str(evalid or ""), ""),
                        ("DESIGN_MANUAL", record["DESIGNCD"], record["MANUAL"], ""),
                    ]
                    for level, d1, d2, d3 in dimensions:
                        group_total[(level, d1, d2, d3)] += 1
                        group_class[(level, d1, d2, d3, state_code, class_status)] += 1

    write_csv(SAMPLE_PATH, sample_rows, row_fields)
    if sum(class_counter.values()) != CFG["expected_f0"]:
        raise RuntimeError("full F0 classification row count mismatch")
    plot_distributions = {
        "PLOT_STATUS_CD": dict(sorted(Counter(x or "<MISSING>" for x in plot_status).items())),
        "SAMP_METHOD_CD": dict(sorted(Counter(x or "<MISSING>" for x in samp).items())),
        "SUBP_EXAMINE_CD": dict(sorted(Counter(x or "<MISSING>" for x in exam).items())),
    }
    expected_samp = {"1": 153734, "2": 180653, "<MISSING>": 4232}
    expected_exam = {"1": 136355, "4": 198032, "<MISSING>": 4232}
    if plot_distributions["SAMP_METHOD_CD"] != expected_samp or plot_distributions["SUBP_EXAMINE_CD"] != expected_exam:
        raise RuntimeError(
            "Layer 1 field distributions contradict accepted Local evidence; source-binding policy requires investigation/full-hash trigger"
        )
    if len(positive_breakpoints) != 37843 or sum(1 for x in positive_breakpoints if x <= 5) != 0:
        raise RuntimeError(
            "Layer 1 breakpoint coverage contradicts accepted Local evidence; source-binding policy requires investigation/full-hash trigger"
        )

    state_rows = []
    for row in STATE_ROWS:
        r = dict(row)
        r["observed_count"] = class_counter.get(r["state_code"], 0)
        r["observed_fraction_f0"] = r["observed_count"] / n
        state_rows.append(r)
    write_csv(ROOT / "LEGAL_OPPORTUNITY_STATE_DICTIONARY_v01_1.csv", state_rows)

    summary_rows = []
    for (level, d1, d2, d3, state_code, class_status), count in sorted(group_class.items()):
        denom = group_total[(level, d1, d2, d3)]
        summary_rows.append({
            "summary_level": level,
            "dimension_1": d1,
            "dimension_2": d2,
            "dimension_3": d3,
            "legal_opportunity_class": state_code,
            "classification_status": class_status,
            "count": count,
            "denominator": denom,
            "fraction": count / denom,
            "provenance_class": "LOCAL/WORK DERIVED QUALIFICATION EVIDENCE",
        })
    write_csv(ROOT / "LEGAL_OPPORTUNITY_F0_CLASSIFICATION_SUMMARY_v01_1.csv", summary_rows)

    ab_rows = []
    for fold in ("ALL", "A", "B"):
        denom = n if fold == "ALL" else sum(v for (f, _), v in fold_status.items() if f == fold)
        statuses = status_counter if fold == "ALL" else Counter({s: fold_status[(fold, s)] for s in status_counter})
        classes = class_counter if fold == "ALL" else Counter({c: sum(v for (f, c2, _), v in fold_class.items() if f == fold and c2 == c) for c in class_counter})
        for class_status in ("FULLY_CLASSIFIED", "EXPLICITLY_UNRESOLVED"):
            count = statuses.get(class_status, 0)
            ab_rows.append({
                "fold": fold,
                "record_type": "CLASSIFICATION_STATUS",
                "category": class_status,
                "count": count,
                "denominator": denom,
                "fraction": count / denom if denom else "",
                "F0_accounted": denom,
            })
        for state_code, count in sorted(classes.items()):
            if count:
                ab_rows.append({
                    "fold": fold,
                    "record_type": "LEGAL_OPPORTUNITY_CLASS",
                    "category": state_code,
                    "count": count,
                    "denominator": denom,
                    "fraction": count / denom if denom else "",
                    "F0_accounted": denom,
                })
    write_csv(ROOT / "LEGAL_OPPORTUNITY_A_B_SUMMARY_v01_1.csv", ab_rows)

    unresolved_rows = []
    unresolved_total = status_counter["EXPLICITLY_UNRESOLVED"]
    for reason, count in sorted(unresolved_counter.items()):
        unresolved_rows.append({
            "summary_level": "ALL",
            "fold": "ALL",
            "unresolved_reason": reason,
            "count": count,
            "denominator_f0": n,
            "fraction_f0": count / n,
            "denominator_unresolved": unresolved_total,
            "fraction_unresolved": count / unresolved_total if unresolved_total else "",
            "required_treatment": "retain explicit state; mainline decides bounded propagation/refinement",
        })
        for fold in ("A", "B"):
            fold_count = fold_class[(fold, reason, "EXPLICITLY_UNRESOLVED")]
            fold_denom = sum(v for (f, _), v in fold_status.items() if f == fold)
            unresolved_rows.append({
                "summary_level": "FOLD",
                "fold": fold,
                "unresolved_reason": reason,
                "count": fold_count,
                "denominator_f0": fold_denom,
                "fraction_f0": fold_count / fold_denom if fold_denom else "",
                "denominator_unresolved": fold_status[(fold, "EXPLICITLY_UNRESOLVED")],
                "fraction_unresolved": fold_count / fold_status[(fold, "EXPLICITLY_UNRESOLVED")] if fold_status[(fold, "EXPLICITLY_UNRESOLVED")] else "",
                "required_treatment": "retain explicit state; mainline decides bounded propagation/refinement",
            })
    write_csv(ROOT / "LEGAL_OPPORTUNITY_UNRESOLVED_STATES_v01_1.csv", unresolved_rows)

    diameter_rows = [
        {
            "record_type": "RULE", "fold": "ALL", "frame_state": "SUBPLOT_MACRO_SPLIT_AT_BREAKPOINT",
            "diameter_domain": "5<=DIA<breakpoint => subplot; DIA>=breakpoint => macroplot", "count": "", "denominator": "", "fraction": "",
            "operator_effect": "defines opportunity frame only; no support/abundance calculation", "provenance_class": "PROJECT-INDUCED CANDIDATE LAYER 3 OPERATOR",
        },
        {
            "record_type": "RULE", "fold": "ALL", "frame_state": "MACRO_FRAME_ALL_TARGET_DIAMETERS",
            "diameter_domain": "positive breakpoint<=5 => all DIA>=5 in macroplot frame", "count": "", "denominator": "", "fraction": "",
            "operator_effect": "defines opportunity frame only; no support/abundance calculation", "provenance_class": "PROJECT-INDUCED CANDIDATE LAYER 3 OPERATOR",
        },
        {
            "record_type": "RULE", "fold": "ALL", "frame_state": "FRAME_UNRESOLVED_NO_POSITIVE_BREAKPOINT",
            "diameter_domain": "DIA>=5 frame unresolved; absent positive breakpoint is not interpreted as subplot-only", "count": "", "denominator": "", "fraction": "",
            "operator_effect": "retains unresolved frame", "provenance_class": "OPEN / UNRESOLVED",
        },
    ]
    for fold in ("ALL", "A", "B"):
        denom = n if fold == "ALL" else (CFG["expected_a"] if fold == "A" else CFG["expected_b"])
        frames = frame_counter if fold == "ALL" else Counter({fr: fold_frame[(fold, fr)] for fr in frame_counter})
        for fstate, count in sorted(frames.items()):
            diameter_rows.append({
                "record_type": "OBSERVED_F0", "fold": fold, "frame_state": fstate, "diameter_domain": "",
                "count": count, "denominator": denom, "fraction": count / denom,
                "operator_effect": "descriptive frame-state coverage; species-blind", "provenance_class": "LOCAL/WORK DERIVED QUALIFICATION EVIDENCE",
            })
    write_csv(ROOT / "LEGAL_OPPORTUNITY_DIAMETER_FRAME_RULES_v01_1.csv", diameter_rows)

    known_plot = {"1", "2", "3", "<MISSING>"}
    known_subp = {"1", "2", "3", "<MISSING>"}
    known_cond = {"1", "2", "3", "4", "5", "<MISSING>"}
    known_basis = {"SUBP", "MACR", "<MISSING>"}
    unexpected = {
        "SUBP_STATUS_CD": sorted(set(all_subp_status_codes) - known_subp),
        "COND_STATUS_CD": sorted(set(all_cond_status_codes) - known_cond),
        "PROP_BASIS": sorted(set(all_prop_basis_codes) - known_basis),
    }
    if any(unexpected.values()):
        raise RuntimeError(f"SOURCE_AUTHORITY_GAP_REQUIRES_MAINLINE: uninterpreted source codes {unexpected}")

    classification_hash = sha256(FULL_F0_GZ)
    output_files = [
        "LEGAL_OPPORTUNITY_STATE_DICTIONARY_v01_1.csv",
        "LEGAL_OPPORTUNITY_F0_CLASSIFICATION_SUMMARY_v01_1.csv",
        "LEGAL_OPPORTUNITY_A_B_SUMMARY_v01_1.csv",
        "LEGAL_OPPORTUNITY_UNRESOLVED_STATES_v01_1.csv",
        "LEGAL_OPPORTUNITY_DIAMETER_FRAME_RULES_v01_1.csv",
        FULL_F0_GZ.name,
    ]
    output_hashes = {name: sha256(ROOT / name) for name in output_files}
    scientific_disposition = (
        "CANDIDATE_OPERATOR_COMPLETE_WITH_BOUNDED_UNRESOLVED_STATES"
        if unresolved_total > 0
        else "CANDIDATE_LEGAL_OPPORTUNITY_OPERATOR_QUALIFIED_FOR_MAINLINE_FREEZE_REVIEW"
    )
    checkpoint = {
        "task_id": TASK_ID,
        "checkpoint": "LAYER3_COMPLETE",
        "completion_marker": "COMPLETE",
        "layer2_sha256": layer2_checkpoint["database_sha256"],
        "rule_fingerprint": RULE_FINGERPRINT,
        "builder_source_sha256": builder_source_sha256(),
        "f0_rows": n,
        "A_rows": CFG["expected_a"],
        "B_rows": CFG["expected_b"],
        "fully_classified": status_counter["FULLY_CLASSIFIED"],
        "explicitly_unresolved": unresolved_total,
        "direct_opportunity_fully_classified": opportunity_counter["DIRECT_Q1_FOREST_OPPORTUNITY"],
        "no_direct_opportunity_fully_classified": opportunity_counter["NO_DIRECT_Q1_FOREST_OPPORTUNITY"],
        "opportunity_unresolved": opportunity_counter["UNRESOLVED"],
        "class_counts": dict(sorted(class_counter.items())),
        "frame_counts": dict(sorted(frame_counter.items())),
        "positive_breakpoint_count": len(positive_breakpoints),
        "positive_breakpoint_le_5_count": sum(1 for x in positive_breakpoints if x <= 5),
        "positive_breakpoint_gt_5_count": sum(1 for x in positive_breakpoints if x > 5),
        "nonpositive_breakpoint_count": nonpositive_breakpoint_count,
        "nonnumeric_breakpoint_count": nonnumeric_breakpoint_count,
        "source_code_distributions": {
            **plot_distributions,
            "SUBP_STATUS_CD": dict(sorted(all_subp_status_codes.items())),
            "COND_STATUS_CD": dict(sorted(all_cond_status_codes.items())),
            "PROP_BASIS": dict(sorted(all_prop_basis_codes.items())),
        },
        "scientific_disposition": scientific_disposition,
        "layer2_status": "LAYER2_CANDIDATE_READY_WITH_EXPLICIT_UNRESOLVED_FIELDS",
        "output_sha256": output_hashes,
        "classification_sha256": classification_hash,
        "reused": False,
    }
    write_json(LAYER3_CKPT, checkpoint)
    log(
        f"STAGE LAYER3_CLASSIFICATION: complete; F0={n}; fully={checkpoint['fully_classified']}; "
        f"unresolved={unresolved_total}; positive_breakpoint={len(positive_breakpoints)}"
    )
    return checkpoint


def write_method_and_provenance_outputs(
    input_binding: dict[str, Any],
    binding_fingerprint: str,
    layer2: dict[str, Any],
    layer3: dict[str, Any],
) -> None:
    field_rows = [
        {"field_or_key": "PLT_CN / PLOT.CN", "layer1_table": "PLOT", "required_role": "F0-to-source visit identity", "necessity": "REQUIRED", "accepted_authority": "S03; LNK01", "operator_treatment": "exact join key; never dropped", "layer2_location": "f0_linkage.PLT_CN; plot_opportunity_source.SOURCE_PLOT_CN", "provenance_class": "FROZEN + LAYER 1 BOUND SOURCE"},
        {"field_or_key": "fold / EVALID / STATECD / source_eu", "layer1_table": "frozen substrate linkage", "required_role": "F0/A/B and evaluation audit identity", "necessity": "REQUIRED", "accepted_authority": "frozen F0 contract", "operator_treatment": "retained unchanged", "layer2_location": "f0_linkage", "provenance_class": "FROZEN"},
        {"field_or_key": "PLOT_STATUS_CD", "layer1_table": "PLOT", "required_role": "plot sampled/forest opportunity gate", "necessity": "REQUIRED", "accepted_authority": "S03; O01-O04", "operator_treatment": "codes 1/2/3 retained and interpreted; missing explicit", "layer2_location": "plot_opportunity_source", "provenance_class": "ACCEPTED EVIDENCE"},
        {"field_or_key": "PLOT_NONSAMPLE_REASN_CD", "layer1_table": "PLOT", "required_role": "plot nonresponse provenance", "necessity": "REQUIRED_CONTEXT", "accepted_authority": "S03; C14", "operator_treatment": "retained; not converted to a species zero", "layer2_location": "plot_opportunity_source", "provenance_class": "ACCEPTED EVIDENCE"},
        {"field_or_key": "SAMP_METHOD_CD", "layer1_table": "PLOT", "required_role": "field versus remote gate", "necessity": "REQUIRED", "accepted_authority": "S04; O05-O06", "operator_treatment": "code 1 field; code 2 no direct tree opportunity; missing explicit", "layer2_location": "plot_opportunity_source", "provenance_class": "ACCEPTED EVIDENCE"},
        {"field_or_key": "SUBP_EXAMINE_CD", "layer1_table": "PLOT", "required_role": "direct versus inferred spatial extent", "necessity": "REQUIRED", "accepted_authority": "S04; O07-O08", "operator_treatment": "code 1 limits direct scope to subplot 1; code 4 describes all four", "layer2_location": "plot_opportunity_source", "provenance_class": "ACCEPTED EVIDENCE"},
        {"field_or_key": "MACRO_BREAKPOINT_DIA", "layer1_table": "PLOT", "required_role": "diameter-dependent tally frame", "necessity": "REQUIRED", "accepted_authority": "S04; O15; C04; C08", "operator_treatment": "positive value creates diameter frame; no positive value remains unresolved", "layer2_location": "plot_opportunity_source", "provenance_class": "ACCEPTED EVIDENCE + OPEN / UNRESOLVED"},
        {"field_or_key": "DESIGNCD / MANUAL", "layer1_table": "PLOT", "required_role": "design/manual audit identity", "necessity": "REQUIRED_CONTEXT", "accepted_authority": "S04; C16", "operator_treatment": "retained for decision-relevant stratification; not used to infer absent breakpoint", "layer2_location": "plot_opportunity_source", "provenance_class": "ACCEPTED EVIDENCE"},
        {"field_or_key": "SUBPLOT.CN / SUBP", "layer1_table": "SUBPLOT", "required_role": "source subplot identity and direct element", "necessity": "REQUIRED", "accepted_authority": "S09; LNK02", "operator_treatment": "source key and element number retained", "layer2_location": "subplot_opportunity_source", "provenance_class": "LAYER 1 BOUND SOURCE"},
        {"field_or_key": "SUBP_STATUS_CD", "layer1_table": "SUBPLOT", "required_role": "sampled accessible element status", "necessity": "REQUIRED", "accepted_authority": "S09; O12-O14", "operator_treatment": "code 1 is direct sampled accessible; 2/3 are not direct forest opportunities", "layer2_location": "subplot_opportunity_source", "provenance_class": "ACCEPTED EVIDENCE"},
        {"field_or_key": "POINT_NONSAMPLE_REASN_CD", "layer1_table": "SUBPLOT", "required_role": "element nonresponse provenance", "necessity": "REQUIRED_CONTEXT", "accepted_authority": "S09; C14", "operator_treatment": "retained; not converted to a species zero", "layer2_location": "subplot_opportunity_source", "provenance_class": "ACCEPTED EVIDENCE"},
        {"field_or_key": "COND.CN / CONDID", "layer1_table": "COND", "required_role": "source condition identity", "necessity": "REQUIRED", "accepted_authority": "S06; LNK03", "operator_treatment": "source and within-plot condition keys retained", "layer2_location": "condition_opportunity_source", "provenance_class": "LAYER 1 BOUND SOURCE"},
        {"field_or_key": "COND_STATUS_CD", "layer1_table": "COND", "required_role": "accessible forest portion gate", "necessity": "REQUIRED", "accepted_authority": "S06-S07; O09-O11", "operator_treatment": "only code 1 can contribute direct Q1 forest opportunity", "layer2_location": "condition_opportunity_source", "provenance_class": "ACCEPTED EVIDENCE"},
        {"field_or_key": "COND_NONSAMPLE_REASN_CD", "layer1_table": "COND", "required_role": "condition nonresponse provenance", "necessity": "REQUIRED_CONTEXT", "accepted_authority": "S07; C14", "operator_treatment": "retained; never promoted to nondetection", "layer2_location": "condition_opportunity_source", "provenance_class": "ACCEPTED EVIDENCE"},
        {"field_or_key": "PROP_BASIS / CONDPROP_UNADJ / SUBPPROP_UNADJ / MACRPROP_UNADJ", "layer1_table": "COND", "required_role": "condition/frame representation", "necessity": "REQUIRED_FOR_FRAME", "accepted_authority": "S08; C08; C13", "operator_treatment": "retained as representation metadata only; never multiplied into A2", "layer2_location": "condition_opportunity_source", "provenance_class": "ACCEPTED EVIDENCE"},
        {"field_or_key": "SUBP_COND.CN / PLT_CN / SUBP / CONDID", "layer1_table": "SUBP_COND", "required_role": "sampled element to condition relationship", "necessity": "REQUIRED_RELATION", "accepted_authority": "LNK06-LNK07", "operator_treatment": "structural link only; no species outcome", "layer2_location": "subplot_condition_relation", "provenance_class": "LAYER 1 BOUND SOURCE + ACCEPTED EVIDENCE"},
    ]
    write_csv(ROOT / "LEGAL_OPPORTUNITY_FIELD_BINDING_v01_1.csv", field_rows)

    relationship_rows = [
        {"relationship_id": "R01", "from_object": "frozen F0 plot visit", "from_key": "f0_linkage.PLT_CN", "to_object": "Layer 1 PLOT", "to_key": "plot_opportunity_source.SOURCE_PLOT_CN", "cardinality_expected": "1:1", "operator_use": "bind every F0 visit to source-native plot status/method/frame fields", "required": "YES", "authority": "frozen F0 contract; S03; LNK01"},
        {"relationship_id": "R02", "from_object": "plot visit", "from_key": "PLT_CN", "to_object": "subplots", "to_key": "subplot_opportunity_source.PLT_CN", "cardinality_expected": "1:many", "operator_use": "identify directly examined element status", "required": "YES", "authority": "S09; LNK02"},
        {"relationship_id": "R03", "from_object": "plot visit", "from_key": "PLT_CN", "to_object": "conditions", "to_key": "condition_opportunity_source.PLT_CN", "cardinality_expected": "1:many", "operator_use": "retain accessible/nonsampled/nonforest condition states and frame basis", "required": "YES", "authority": "S06-S08; LNK03"},
        {"relationship_id": "R04", "from_object": "subplot", "from_key": "PLT_CN + SUBP", "to_object": "condition", "to_key": "PLT_CN + CONDID via subplot_condition_relation", "cardinality_expected": "many:many link records", "operator_use": "confirm accessible condition is linked to a sampled direct element", "required": "YES", "authority": "LNK06-LNK07"},
        {"relationship_id": "R05", "from_object": "plot breakpoint", "from_key": "PLOT.MACRO_BREAKPOINT_DIA", "to_object": "condition representation", "to_key": "COND.PROP_BASIS + MACRPROP_UNADJ", "cardinality_expected": "plot:condition-many", "operator_use": "resolve diameter-specific subplot/macroplot opportunity frame", "required": "YES_FOR_POSITIVE_BREAKPOINT", "authority": "S04; S08; C04; C08"},
    ]
    write_csv(ROOT / "LEGAL_OPPORTUNITY_SOURCE_RELATIONSHIP_SPEC_v01_1.csv", relationship_rows)

    con = readonly_connect(LAYER2_DB)
    schema_rows = []
    for table in LAYER2_SCHEMA:
        for cid, name, dtype, notnull, default, pk in con.execute(f'PRAGMA table_info("{table}")'):
            schema_rows.append({
                "table_name": table,
                "ordinal": cid + 1,
                "column_name": name,
                "sqlite_type": dtype,
                "not_null": notnull,
                "primary_key_position": pk,
                "default_value": "" if default is None else default,
                "scientific_scope": "frozen linkage" if table == "f0_linkage" else "source-native legal-opportunity field/key",
                "species_blind": "YES",
            })
    relation_missing_subplot = con.execute(
        """SELECT COUNT(*) FROM subplot_condition_relation r
           LEFT JOIN subplot_opportunity_source s ON s.PLT_CN=r.PLT_CN AND CAST(s.SUBP AS TEXT)=CAST(r.SUBP AS TEXT)
           WHERE s.SOURCE_SUBPLOT_CN IS NULL"""
    ).fetchone()[0]
    relation_missing_condition = con.execute(
        """SELECT COUNT(*) FROM subplot_condition_relation r
           LEFT JOIN condition_opportunity_source c ON c.PLT_CN=r.PLT_CN AND CAST(c.CONDID AS TEXT)=CAST(r.CONDID AS TEXT)
           WHERE c.SOURCE_COND_CN IS NULL"""
    ).fetchone()[0]
    con.close()
    write_csv(ROOT / "LAYER2_SUBSTRATE_SCHEMA_v01_1.csv", schema_rows)

    trace_rows = [
        {"layer2_table": "f0_linkage", "layer2_source_key": "PLT_CN", "source_layer": "FROZEN FIA SUBSTRATE", "source_table": "plot_visit_design_core", "source_key": "PLT_CN", "traceability_rule": "exact retained key; joins Layer 1 PLOT.CN", "status": "PASS"},
        {"layer2_table": "plot_opportunity_source", "layer2_source_key": "SOURCE_PLOT_CN", "source_layer": "LAYER 1 BOUND SOURCE", "source_table": "PLOT", "source_key": "CN", "traceability_rule": "byte-preserved source key; PLT_CN duplicate supports F0 join", "status": "PASS"},
        {"layer2_table": "subplot_opportunity_source", "layer2_source_key": "SOURCE_SUBPLOT_CN", "source_layer": "LAYER 1 BOUND SOURCE", "source_table": "SUBPLOT", "source_key": "CN", "traceability_rule": "byte-preserved source key and PLT_CN", "status": "PASS"},
        {"layer2_table": "condition_opportunity_source", "layer2_source_key": "SOURCE_COND_CN", "source_layer": "LAYER 1 BOUND SOURCE", "source_table": "COND", "source_key": "CN", "traceability_rule": "byte-preserved source key and PLT_CN/CONDID", "status": "PASS"},
        {"layer2_table": "subplot_condition_relation", "layer2_source_key": "SOURCE_SUBP_COND_CN", "source_layer": "LAYER 1 BOUND SOURCE", "source_table": "SUBP_COND", "source_key": "CN", "traceability_rule": "byte-preserved source key and PLT_CN/SUBP/CONDID", "status": "PASS"},
    ]
    write_csv(ROOT / "LAYER2_SUBSTRATE_SOURCE_TRACEABILITY_v01_1.csv", trace_rows)

    gap_rows = [{
        "gap_id": "NONE",
        "logically_necessary_proposition": "No unresolved accepted-authority proposition was encountered for the current candidate operator.",
        "field_or_relationship": "PLOT/SUBPLOT/COND/SUBP_COND legal-opportunity interface",
        "status": "NO_SOURCE_AUTHORITY_GAP",
        "consequence": "Data-level missing/no-positive-breakpoint states remain explicit; they are not reclassified as an authority gap.",
        "external_search_performed": "NO",
    }]
    write_csv(ROOT / "LEGAL_OPPORTUNITY_SOURCE_AUTHORITY_GAPS_v01_1.csv", gap_rows)

    firewall_metrics = [
        "SPECIES_OUTCOME_ROWS_READ_FOR_ANALYSIS",
        "SPCD_SELECTED_ROWS",
        "SPECIES_SUPPORT_CALCULATION_ROWS",
        "SPECIES_NONDETECTION_CALCULATION_ROWS",
        "Q1_CALCULATION_ROWS",
        "ABUNDANCE_CALCULATION_ROWS",
        "INTERNET_ACCESS",
    ]
    firewall_rows = [{"metric": metric, "value": 0, "required_value": 0, "status": "PASS", "evidence": "builder contains no TREE/SPCD/species outcome query; no network operation"} for metric in firewall_metrics]
    firewall_rows.extend([
        {"metric": "TREE_TABLE_QUERIES", "value": 0, "required_value": 0, "status": "PASS", "evidence": "fixed Layer 1 table allow-list is PLOT,SUBPLOT,COND,SUBP_COND"},
        {"metric": "LAYER2_SPECIES_COLUMNS", "value": 0, "required_value": 0, "status": "PASS", "evidence": "schema audit contains no SPCD or species-identity/outcome column"},
    ])
    write_csv(ROOT / "LEGAL_OPPORTUNITY_FIREWALL_QC_v01_1.csv", firewall_rows)

    binding_records = input_binding["records"]
    invariant_rows = []
    for rec in binding_records:
        invariant_rows.append({"check_id": f"INPUT_SHA_{rec['input_id']}", "observed": rec["observed_sha256"], "expected": rec["expected_sha256"], "status": "PASS" if rec["status"].startswith("PASS") else rec["status"], "evidence": rec["path"]})
    invariant_rows.extend([
        {"check_id": "SOURCE_BINDING_MODE", "observed": CFG["source_binding_mode"], "expected": "INHERITED_ACCEPTED_FULL_HASH_BINDING", "status": "PASS", "evidence": "SOURCE_BINDING_RECORD_v01_1.json"},
        {"check_id": "LAYER1_PATH_SIZE_RESTART_VALIDATION", "observed": input_binding["source_binding"]["current_size_bytes"], "expected": CFG["layer1_accepted_size"], "status": "PASS", "evidence": CFG["layer1_sqlite_path"]},
        {"check_id": "F0_ROWS_ACCOUNTED", "observed": layer3["f0_rows"], "expected": CFG["expected_f0"], "status": "PASS", "evidence": FULL_F0_GZ.name},
        {"check_id": "A_ROWS_ACCOUNTED", "observed": layer3["A_rows"], "expected": CFG["expected_a"], "status": "PASS", "evidence": "f0_linkage.fold"},
        {"check_id": "B_ROWS_ACCOUNTED", "observed": layer3["B_rows"], "expected": CFG["expected_b"], "status": "PASS", "evidence": "f0_linkage.fold"},
        {"check_id": "A_B_PERMANENT_PLOT_OVERLAP", "observed": layer2["row_counts"].get("f0_linkage", 0) - CFG["expected_f0"], "expected": 0, "status": "PASS", "evidence": "validated when f0_linkage checkpoint was built"},
        {"check_id": "LAYER2_SQLITE_INTEGRITY", "observed": layer2["integrity_check"], "expected": "ok", "status": "PASS", "evidence": LAYER2_DB.name},
        {"check_id": "LAYER2_PLOT_ROWS", "observed": layer2["row_counts"]["plot_opportunity_source"], "expected": CFG["expected_f0"] - 4232, "status": "PASS", "evidence": "exact F0 PLT_CN filter; reproduces accepted Local match count"},
        {"check_id": "F0_WITHOUT_LAYER1_PLOT_MATCH_RETAINED", "observed": CFG["expected_f0"] - layer2["row_counts"]["plot_opportunity_source"], "expected": 4232, "status": "PASS", "evidence": "retained in f0_linkage and explicit unresolved class; no causal label assigned"},
        {"check_id": "LAYER2_RELATION_MISSING_SUBPLOT", "observed": relation_missing_subplot, "expected": 0, "status": "PASS" if relation_missing_subplot == 0 else "FAIL", "evidence": "subplot_condition_relation to subplot_opportunity_source"},
        {"check_id": "LAYER2_RELATION_MISSING_CONDITION", "observed": relation_missing_condition, "expected": 0, "status": "PASS" if relation_missing_condition == 0 else "FAIL", "evidence": "subplot_condition_relation to condition_opportunity_source"},
        {"check_id": "POSITIVE_BREAKPOINT_F0", "observed": layer3["positive_breakpoint_count"], "expected": 37843, "status": "PASS", "evidence": "accepted Local control reproduced"},
        {"check_id": "POSITIVE_BREAKPOINT_LE_5", "observed": layer3["positive_breakpoint_le_5_count"], "expected": 0, "status": "PASS", "evidence": "all observed positive breakpoints exceed frozen 5-in threshold"},
        {"check_id": "EVERY_STATE_IN_DICTIONARY", "observed": len(set(layer3["class_counts"]) - STATE_CODES), "expected": 0, "status": "PASS", "evidence": "classification builder hard gate"},
        {"check_id": "UNRESOLVED_STATES_EXPLICIT", "observed": layer3["explicitly_unresolved"], "expected": "reported without row deletion", "status": "PASS", "evidence": "full F0 classification and unresolved summary"},
        {"check_id": "NO_SILENT_DELETION", "observed": layer3["fully_classified"] + layer3["explicitly_unresolved"], "expected": CFG["expected_f0"], "status": "PASS", "evidence": "classification status partition"},
        {"check_id": "NO_OUTCOME_DEPENDENT_SCOPE", "observed": 0, "expected": 0, "status": "PASS", "evidence": "species firewall"},
        {"check_id": "NO_SUPPORT_OR_ABUNDANCE_ESTIMATOR", "observed": 0, "expected": 0, "status": "PASS", "evidence": "operator only classifies measurement opportunity"},
        {"check_id": "TRANSFER_UPLOAD_TARGET_POLICY", "observed": "mirror", "expected": "mirror", "status": "PASS", "evidence": "transfer manifest builder uses one constant"},
        {"check_id": "RESTART_PROVENANCE_NO_OPAQUE_STATE", "observed": "FILE_BOUND_CHECKPOINTS", "expected": "FILE_BOUND_CHECKPOINTS", "status": "PASS", "evidence": "SOURCE_BINDING_RECORD plus Layer2/Layer3 checkpoint JSON"},
    ])
    write_csv(ROOT / "LEGAL_OPPORTUNITY_INVARIANT_QC_v01_1.csv", invariant_rows)

    checkpoint_rows = [
        {"checkpoint_id": "CP01_INPUT_BINDING", "task_id": TASK_ID, "status": "COMPLETE", "reuse_status": "BUILT_UNDER_V01_1", "input_binding_fingerprint": binding_fingerprint, "rule_or_schema_fingerprint": "", "artifact": "SOURCE_BINDING_RECORD_v01_1.json", "artifact_sha256": sha256(ROOT / "SOURCE_BINDING_RECORD_v01_1.json"), "row_count_or_invariant": "protected small SHA exact; Layer1 path/size coherent", "completion_marker": "COMPLETE"},
        {"checkpoint_id": "CP02_LAYER2", "task_id": TASK_ID, "status": "COMPLETE", "reuse_status": "REUSED_AFTER_V01_1_VALIDATION" if layer2.get("reused") else "BUILT_UNDER_V01_1", "input_binding_fingerprint": binding_fingerprint, "rule_or_schema_fingerprint": SCHEMA_FINGERPRINT, "artifact": LAYER2_DB.name, "artifact_sha256": layer2["database_sha256"], "row_count_or_invariant": json.dumps(layer2["row_counts"], sort_keys=True), "completion_marker": "COMPLETE"},
        {"checkpoint_id": "CP03_LAYER3", "task_id": TASK_ID, "status": "COMPLETE", "reuse_status": "REUSED_AFTER_V01_1_VALIDATION" if layer3.get("reused") else "BUILT_UNDER_V01_1", "input_binding_fingerprint": binding_fingerprint, "rule_or_schema_fingerprint": RULE_FINGERPRINT, "artifact": FULL_F0_GZ.name, "artifact_sha256": layer3["classification_sha256"], "row_count_or_invariant": f"F0={layer3['f0_rows']}; fully={layer3['fully_classified']}; unresolved={layer3['explicitly_unresolved']}", "completion_marker": "COMPLETE"},
    ]
    write_csv(ROOT / "RESTART_CHECKPOINT_LEDGER_v01_1.csv", checkpoint_rows)

    output_provenance = [
        (LAYER2_DB.name, "PROJECT-INDUCED CANDIDATE LAYER 2 SUBSTRATE", "minimal source-native measurement substrate; not frozen"),
        (FULL_F0_GZ.name, "LOCAL/WORK DERIVED QUALIFICATION EVIDENCE", "species-blind full F0 classification"),
        ("LEGAL_OPPORTUNITY_STATE_DICTIONARY_v01_1.csv", "PROJECT-INDUCED CANDIDATE LAYER 3 OPERATOR", "candidate state definitions; not frozen"),
        ("LEGAL_OPPORTUNITY_OPERATOR_SPEC_v01_1.md", "PROJECT-INDUCED CANDIDATE LAYER 3 OPERATOR", "deterministic rule specification; not frozen"),
        ("LEGAL_OPPORTUNITY_F0_CLASSIFICATION_SUMMARY_v01_1.csv", "LOCAL/WORK DERIVED QUALIFICATION EVIDENCE", "classification counts and fractions"),
        ("LEGAL_OPPORTUNITY_A_B_SUMMARY_v01_1.csv", "LOCAL/WORK DERIVED QUALIFICATION EVIDENCE", "fold closure and classification"),
        ("LEGAL_OPPORTUNITY_UNRESOLVED_STATES_v01_1.csv", "OPEN / UNRESOLVED", "retained unresolved measurement states"),
        ("LEGAL_OPPORTUNITY_DIAMETER_FRAME_RULES_v01_1.csv", "PROJECT-INDUCED CANDIDATE LAYER 3 OPERATOR", "diameter/tally-frame rule and observed coverage"),
    ]
    prov_rows = []
    for rec in binding_records:
        pclass = "FROZEN" if rec["input_id"] in {"MAINLINE_HANDOFF", "FROZEN_SUBSTRATE_ZIP", "FROZEN_SUBSTRATE_INTERNAL_SQLITE"} else "ACCEPTED EVIDENCE"
        prov_rows.append({"artifact_or_statement": rec["input_id"], "provenance_class": pclass, "identity_or_rule": rec["observed_sha256"], "role": "protected input", "freeze_status": "INHERITED" if pclass == "FROZEN" else "ACCEPTED_NOT_FROZEN"})
    prov_rows.append({"artifact_or_statement": "LAYER1_SQLITE", "provenance_class": "LAYER 1 BOUND SOURCE", "identity_or_rule": CFG["layer1_accepted_sha256"], "role": CFG["source_binding_mode"], "freeze_status": "BOUND_SOURCE"})
    for name, pclass, role in output_provenance:
        prov_rows.append({"artifact_or_statement": name, "provenance_class": pclass, "identity_or_rule": "see SHA256SUMS.csv", "role": role, "freeze_status": "CANDIDATE_NOT_FROZEN" if "CANDIDATE" in pclass else "DERIVED_OR_OPEN"})
    write_csv(ROOT / "WORK_PROVENANCE_v01_1.csv", prov_rows)

    layer2_status = layer3["layer2_status"]
    readiness = f"""# Layer 2 substrate readiness — v01_1

Status: `{layer2_status}`

This candidate is species-blind, traceable, and complete for the source-native legal-opportunity interface established by the accepted evidence. It is not frozen and does not pass the support Gate.

## Included scope

- Frozen F0 linkage: {layer2['row_counts']['f0_linkage']:,} plot visits.
- Layer 1 PLOT rows: {layer2['row_counts']['plot_opportunity_source']:,}.
- Layer 1 SUBPLOT rows: {layer2['row_counts']['subplot_opportunity_source']:,}.
- Layer 1 COND rows: {layer2['row_counts']['condition_opportunity_source']:,}.
- Layer 1 SUBP_COND structural links: {layer2['row_counts']['subplot_condition_relation']:,}.
- Only identity, status, examination, nonresponse, diameter-frame, condition-proportion/basis, and relationship fields required by the current operator are retained.

## Excluded scope

No SPCD, species identity, TREE outcome, coordinates, support, nondetection, abundance, expansion factor, revisit, or QA-repeat object is included.

## Recommendation to mainline

The candidate can serve as the default input for the next support-measurement-method stage without routine re-reading of the 71.6 GB Layer 1 source. The unresolved source values remain present and must not be filtered out.

Return to Layer 1 only if mainline changes the target/interface, accepts new source semantics requiring an omitted field, detects a source/provenance invariant conflict, requires a new source relationship, or authorizes a narrow refinement for the no-positive-breakpoint state.
"""
    (ROOT / "LAYER2_SUBSTRATE_READINESS_v01_1.md").write_text(readiness, encoding="utf-8")

    spec = f"""# Legal observation-opportunity operator specification — v01_1

Provenance: `PROJECT-INDUCED CANDIDATE LAYER 3 OPERATOR`. Status: candidate, not frozen.

Rule fingerprint: `{RULE_FINGERPRINT}`

## Unit and firewall

The classification unit is one frozen F0 plot visit. Direct opportunity is resolved through the species-blind chain:

`F0 visit × field method × directly examined sampled subplot × linked accessible forest condition × applicable diameter/tally frame`.

The operator never queries TREE, SPCD, species outcomes, support, nondetection, abundance, coordinates, or A2.

## Deterministic rule order

1. Bind exactly one Layer 1 `PLOT.CN` to each F0 `PLT_CN`; otherwise retain `UNRESOLVED_PLOT_SOURCE_BINDING`.
2. Validate `PLOT_STATUS_CD` against accepted codes; missing/other is unresolved. Plot status remains present in the full classification.
3. Interpret `SAMP_METHOD_CD` before choosing the terminal no-opportunity label: code 2 is explicitly retained as remote/non-field and has no direct tree opportunity.
4. For non-remote records, `PLOT_STATUS_CD=3` has no direct opportunity and code 2 has no Q1 forest opportunity; for `PLOT_STATUS_CD=1`, missing/other sampling method is unresolved and code 1 continues.
5. Interpret `SUBP_EXAMINE_CD`: code 1 limits direct scope to subplot 1; code 4 identifies subplots 1–4 as fully described. It does not create independent repeat-detection occasions.
6. Require one unique accepted `SUBP_STATUS_CD` for each directly examined element. Code 1 contributes sampled-accessible opportunity; codes 2/3 do not. Missing/duplicate/other remains unresolved.
7. Use the retained `SUBP_COND` relationship to require at least one `COND_STATUS_CD=1` condition linked to a sampled direct element. Missing/ambiguous linkage or condition status remains unresolved.
8. If `MACRO_BREAKPOINT_DIA>5`, use subplot opportunity for `5<=DIA<breakpoint` and macroplot opportunity for `DIA>=breakpoint`. If a positive breakpoint is `<=5`, the whole frozen target is in the macroplot frame.
9. For a positive breakpoint, every linked accessible condition used by the operator must retain `PROP_BASIS=MACR` and numeric `MACRPROP_UNADJ`; otherwise retain `UNRESOLVED_MACRO_CONDITION_BASIS`.
10. If no positive breakpoint is present, retain `UNRESOLVED_DIAMETER_FRAME_NO_POSITIVE_BREAKPOINT`. Do not infer subplot-only opportunity.
11. Preserve every F0 row. Never promote remote, inferred, nonsampled, nonforest, missing, or unresolved states to species nondetection.

## Interpretation boundary

A fully classified direct-opportunity state establishes only where a later method may evaluate a species encounter/nondetection. It is not itself detection, nondetection, biological absence, support, or abundance. Condition proportions remain representation metadata and are not multiplied into A2.

Observed qualification: F0={layer3['f0_rows']:,}; fully classified={layer3['fully_classified']:,}; explicitly unresolved={layer3['explicitly_unresolved']:,}.
"""
    (ROOT / "LEGAL_OPPORTUNITY_OPERATOR_SPEC_v01_1.md").write_text(spec, encoding="utf-8")

    class_lines = "\n".join(f"| `{k}` | {v:,} | {v/layer3['f0_rows']:.6%} |" for k, v in sorted(layer3["class_counts"].items()))
    main_report = f"""# Q1 FIA 合法观测机会算子 v01_1 — Work 主报告

## 终局结论

科学/算子终局：`{layer3['scientific_disposition']}`

Layer 2 状态：`{layer2_status}`

该结论不冻结算子或 Layer 2，不构成 `SUPPORT IDENTIFIED`，也不构成 `SUPPORT GATE PASS`。

## 输入与重启绑定

四个受保护的小型输入均通过精确 SHA-256。Layer 1 母库路径和当前大小与已接受绑定一致，未发现替换或来源异常，因此按 v01_1 使用 `INHERITED_ACCEPTED_FULL_HASH_BINDING`；本次没有把未知的既往中断原因归因于哈希、SQLite 或表格处理，也没有仪式性重算 71.6 GB 全文件哈希。冻结底座内部 SQLite 另行通过精确 SHA 校验。

## Q1：最小物种盲状态空间

最小状态链为：plot sampling state → field/remote method → direct/inferred examination scope → sampled subplot status → linked condition status → diameter frame → condition/frame basis。每个终端类均在状态字典中有明确规则；缺失和无法闭合的组合保留为显式 unresolved。

## Q2：最小必要字段与关系

当前已接受 authority 足以解释 `PLOT_STATUS_CD`、`SAMP_METHOD_CD`、`SUBP_EXAMINE_CD`、`SUBP_STATUS_CD`、`COND_STATUS_CD`、`MACRO_BREAKPOINT_DIA`、`PROP_BASIS` 和相关比例/非抽样原因。结构关系最小为 `PLOT.CN → SUBPLOT.PLT_CN / COND.PLT_CN`，再以 `SUBP_COND(PLT_CN,SUBP,CONDID)` 保留 sampled element 与 condition 的关系。没有出现需要外部 Search 的语义命题。

## Q3：Layer 2 候选底座

候选 SQLite 含 {layer2['row_counts']['f0_linkage']:,} 条 F0 linkage、{layer2['row_counts']['plot_opportunity_source']:,} 条 PLOT、{layer2['row_counts']['subplot_opportunity_source']:,} 条 SUBPLOT、{layer2['row_counts']['condition_opportunity_source']:,} 条 COND 和 {layer2['row_counts']['subplot_condition_relation']:,} 条 SUBP_COND link。每个来源表保留其 `CN` 和关系键；未纳入 TREE、SPCD、物种结果、坐标、support、abundance 或推测性“备用字段”。

## Q4：F0 映射闭合

F0={layer3['f0_rows']:,}，A={layer3['A_rows']:,}，B={layer3['B_rows']:,}，A/B permanent-plot overlap=0。完整逐行物种盲分类已交付；没有样地静默消失。

## Q5：可分类与 unresolved

Fully classified={layer3['fully_classified']:,}（{layer3['fully_classified']/layer3['f0_rows']:.6%}）；explicitly unresolved={layer3['explicitly_unresolved']:,}（{layer3['explicitly_unresolved']/layer3['f0_rows']:.6%}）。没有设任意比例阈值。主线需依据 unresolved reason 表决定窄修正、传播/有界推断或 claim reduction。

| Candidate class | Count | Fraction of F0 |
|---|---:|---:|
{class_lines}

## Q6：DIA>=5 与 tally frame

本次复现 positive breakpoint={layer3['positive_breakpoint_count']:,}，其中 >5 in={layer3['positive_breakpoint_gt_5_count']:,}、<=5 in={layer3['positive_breakpoint_le_5_count']:,}。正 breakpoint 样地按 `5<=DIA<breakpoint` 的 subplot frame 和 `DIA>=breakpoint` 的 macroplot frame 表示。无正 breakpoint 不被解释成 subplot-only，而保留 frame unresolved。该规则只定义观测机会，不构造 support/abundance，也不改动 A2。

## Q7：Layer 2 基础设施充分性

候选底座包含当前算子所需的全部 source-native 字段和关系，保留来源键与 unresolved 值，足以作为下一 support-measurement 方法阶段的默认输入候选，避免例行重扫 Layer 1。它仍需主线审查；若目标/接口改变、需要未收录字段、来源不变量冲突、出现新关系需求，或主线授权解决无正 breakpoint 状态，才返回 Layer 1。

## 防火墙与 STOP

所有物种、SPCD、support、nondetection、Q1、abundance、TREE-query 和 internet 计数均为 0。现按授权 STOP：不启动 partial-ID/support-set Search、occupancy/detection、support 生产、坐标传播或 real Q1。
"""
    (ROOT / "Q1_FIA_SUPPORT_LEGAL_OPPORTUNITY_OPERATOR_v01_1_MAIN_REPORT.md").write_text(main_report, encoding="utf-8")

    runmeta = {
        "task_id": TASK_ID,
        "task_class": "WORK_METHOD_DEFINITION_BUILD_QUALIFICATION_AND_LAYERED_SOURCE_CONSOLIDATION",
        "builder_version": CFG["builder_version"],
        "builder_source_sha256": builder_source_sha256(),
        "execution_date": CFG["execution_date"],
        "authorization_sha256": CFG["authorization_sha256"],
        "source_binding_mode": CFG["source_binding_mode"],
        "accepted_layer1_sha256": CFG["layer1_accepted_sha256"],
        "fresh_layer1_full_hash_performed": False,
        "binding_fingerprint": binding_fingerprint,
        "layer2_schema_fingerprint": SCHEMA_FINGERPRINT,
        "layer3_rule_fingerprint": RULE_FINGERPRINT,
        "layer2_database_sha256": layer2["database_sha256"],
        "layer2_row_counts": layer2["row_counts"],
        "layer3": {k: layer3[k] for k in ["f0_rows", "A_rows", "B_rows", "fully_classified", "explicitly_unresolved", "direct_opportunity_fully_classified", "no_direct_opportunity_fully_classified", "opportunity_unresolved", "positive_breakpoint_count", "positive_breakpoint_gt_5_count", "scientific_disposition", "layer2_status"]},
        "species_firewall": {"species_outcome_rows_read_for_analysis": 0, "spcd_selected_rows": 0, "species_support_calculation_rows": 0, "species_nondetection_calculation_rows": 0, "q1_calculation_rows": 0, "abundance_calculation_rows": 0, "tree_table_queries": 0, "internet_access": 0},
        "runtime": {"python": sys.version, "sqlite": sqlite3.sqlite_version, "platform": platform.platform()},
        "freeze_authority": "MAINLINE_ONLY",
        "stop_boundary": "RETURN_TO_MAINLINE",
    }
    write_json(ROOT / "RUN_METADATA_v01_1.json", runmeta)


def write_transfer_and_sha_manifests() -> None:
    for path in (ROOT / "SHA256SUMS.csv", ROOT / "TRANSFER_MANIFEST_v01_1.csv"):
        if path.exists():
            path.unlink()
    members = [p for p in ROOT.rglob("*") if p.is_file() and p != ZIP_PATH and not p.name.endswith(".building.sqlite")]
    members = [p for p in members if "__pycache__" not in p.parts and p.suffix.lower() != ".pyc"]
    members = [p for p in members if p.name not in {"SHA256SUMS.csv", "TRANSFER_MANIFEST_v01_1.csv"}]
    transfer_rows = []
    for p in sorted(members, key=lambda x: x.relative_to(ROOT).as_posix()):
        rel = p.relative_to(ROOT).as_posix()
        transfer_rows.append({
            "artifact_id": rel,
            "artifact_type": "PACKAGE_MEMBER",
            "local_path": str(p),
            "sha256": sha256(p),
            "size_bytes": p.stat().st_size,
            "upload_target": "mirror",
            "upload_path": CFG["mirror_prefix"] + rel,
            "transfer_action": "UPLOAD_AS_PACKAGE_MEMBER",
            "notes": "candidate/qualification evidence; preserve relative path",
        })
    transfer_rows.append({
        "artifact_id": CFG["output_bundle_name"],
        "artifact_type": "BUNDLE_UPLOAD",
        "local_path": str(ZIP_PATH),
        "sha256": "REPORTED_AFTER_DETERMINISTIC_PACKAGE_ASSEMBLY",
        "size_bytes": "",
        "upload_target": "mirror",
        "upload_path": CFG["mirror_prefix"] + CFG["output_bundle_name"],
        "transfer_action": "UPLOAD_PRIMARY_BUNDLE",
        "notes": "primary bundle; keep upload_target exactly mirror",
    })
    write_csv(ROOT / "TRANSFER_MANIFEST_v01_1.csv", transfer_rows)
    manifest_members = members + [ROOT / "TRANSFER_MANIFEST_v01_1.csv"]
    sha_rows = []
    for p in sorted(manifest_members, key=lambda x: x.relative_to(ROOT).as_posix()):
        sha_rows.append({"relative_path": p.relative_to(ROOT).as_posix(), "sha256": sha256(p), "size_bytes": p.stat().st_size})
    write_csv(ROOT / "SHA256SUMS.csv", sha_rows)


def deterministic_zip(source_root: Path, dest: Path) -> None:
    files = [p for p in source_root.rglob("*") if p.is_file() and p != ZIP_PATH and not p.name.endswith(".building.sqlite")]
    files = [p for p in files if "__pycache__" not in p.parts and p.suffix.lower() != ".pyc"]
    files = [p for p in files if p.suffix.lower() != ".zip" or p.parent != source_root]
    with zipfile.ZipFile(dest, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9, allowZip64=True) as zf:
        for path in sorted(files, key=lambda x: x.relative_to(source_root).as_posix()):
            rel = path.relative_to(source_root).as_posix()
            info = zipfile.ZipInfo(rel, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            with path.open("rb") as src, zf.open(info, "w", force_zip64=True) as dst:
                shutil.copyfileobj(src, dst, length=8 * 1024 * 1024)


def assemble_package() -> tuple[str, int]:
    tmp1 = Path(r"C:\range_paper\99_tmp\q1_fia_support_legal_opportunity_operator_v01_1\package_pass1.zip")
    tmp2 = Path(r"C:\range_paper\99_tmp\q1_fia_support_legal_opportunity_operator_v01_1\package_pass2.zip")
    for p in (tmp1, tmp2):
        if p.exists():
            p.unlink()
    deterministic_zip(ROOT, tmp1)
    deterministic_zip(ROOT, tmp2)
    h1 = sha256(tmp1)
    h2 = sha256(tmp2)
    if h1 != h2:
        raise RuntimeError(f"deterministic package mismatch: {h1} != {h2}")
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
    os.replace(tmp1, ZIP_PATH)
    tmp2.unlink()
    return h1, ZIP_PATH.stat().st_size


def verify_package_manifest() -> None:
    with zipfile.ZipFile(ZIP_PATH, "r") as zf:
        names = set(zf.namelist())
        with zf.open("SHA256SUMS.csv") as f:
            import io
            rows = list(csv.DictReader(io.TextIOWrapper(f, encoding="utf-8")))
        for row in rows:
            rel = row["relative_path"]
            if rel not in names:
                raise RuntimeError(f"manifest member missing from ZIP: {rel}")
            data = zf.read(rel)
            if hashlib.sha256(data).hexdigest() != row["sha256"] or len(data) != int(row["size_bytes"]):
                raise RuntimeError(f"ZIP member manifest mismatch: {rel}")
        if "Q1_FIA_SUPPORT_MEASUREMENT_SUBSTRATE_CANDIDATE_v01_1.sqlite" not in names:
            raise RuntimeError("Layer 2 candidate missing from package")
        transfer = zf.read("TRANSFER_MANIFEST_v01_1.csv").decode("utf-8")
        if "mainline_handoff" in transfer or ",mirror," not in transfer:
            raise RuntimeError("transfer manifest upload_target policy failure")


def main() -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    (ROOT / "checkpoints").mkdir(exist_ok=True)
    (ROOT / "logs").mkdir(exist_ok=True)
    SAMPLE_PATH.parent.mkdir(parents=True, exist_ok=True)
    input_binding, binding_fingerprint = verify_protected_inputs()
    layer2 = build_layer2(binding_fingerprint)
    layer3 = build_layer3(layer2)
    write_method_and_provenance_outputs(input_binding, binding_fingerprint, layer2, layer3)
    log("STAGE SUPPORTING_OUTPUTS: complete")
    log(f"SCIENTIFIC_DISPOSITION: {layer3['scientific_disposition']}")
    log(f"LAYER2_STATUS: {layer3['layer2_status']}")
    log("SPECIES_FIREWALL: PASS; all required counters zero")
    log("STOP_BOUNDARY: return to mainline; no support/abundance/real-Q1 work started")
    LOG_PATH.write_text("\n".join(LOG) + "\n", encoding="utf-8")
    write_transfer_and_sha_manifests()
    package_hash, package_size = assemble_package()
    verify_package_manifest()
    print(json.dumps({
        "status": "COMPLETE",
        "scientific_disposition": layer3["scientific_disposition"],
        "layer2_status": layer3["layer2_status"],
        "f0": layer3["f0_rows"],
        "fully_classified": layer3["fully_classified"],
        "explicitly_unresolved": layer3["explicitly_unresolved"],
        "package": str(ZIP_PATH),
        "package_sha256": package_hash,
        "package_size_bytes": package_size,
    }, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
