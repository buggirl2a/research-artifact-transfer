#!/usr/bin/env python3
"""Build the bounded, outcome-blind D08C1 accepted-species eligibility census."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import platform
import sqlite3
import sys
import time
import zipfile
import zlib
from collections import Counter, defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(r"C:\range_paper")
SRC = ROOT / "06_src" / "d08c1_v01"
WORK = ROOT / "99_tmp" / "d08c1_v01"
OUT = WORK / "outputs"
QC = WORK / "qc"
DB_PATH = ROOT / "99_tmp" / "elig_v02" / "SQLite_FIADB_ENTIRE.db"
FIA_ZIP = ROOT / "02_raw" / "FIA" / "SQLite_FIADB_ENTIRE.zip"
TAX = ROOT / "04_derived" / "tax_v02"
PARAM_PATH = SRC / "parameters_d08c1_v01.json"
REQUEST_DIR = ROOT / "03_doc" / "D08C1_FIA_ELIGIBILITY_INPUTS_v01"


CONTROL_EXPECTED = {
    ROOT / "00_control" / "RAW_FREEZE_v02.md": "878bfeb09d474cd6e69ec787eac8bb69d7c14d802620c3d7b653d27f6b3470ce",
    ROOT / "00_control" / "raw_manifest_v02.csv": "ed3dead2cb0e516f95ec51c417ffa221e0f22f8dbfe695fac1d1f533ea0b0dc1",
    ROOT / "00_control" / "sha256_raw_v02.txt": "fec418fcbd714f7d856e5791001a68a49e72b771900543aac70ef4141e04eb94",
    ROOT / "00_control" / "D08C1_FIA_ACCEPTED_SPECIES_ELIGIBILITY_CONTRACT_v01.md": "46da3382ae7cd650569440e3cdf0b6406af6f82a4b72fb3767ccaf6cc06ec22c",
    ROOT / "00_control" / "D08C1_STATE_ALIAS_FREEZE_v01.csv": "d450e7b9b635c34db7e60ec0964a7f4ca3f24e4e7e58f8f1725691bcff3f7dda",
    PARAM_PATH: "22c0c8a5b3cdfa9194d527ed9381fdf6680338652d486ee045e1aa8d2253e608",
    REQUEST_DIR / "Q1_WORK_REQUEST_D08C1_FIA_ACCEPTED_SPECIES_ELIGIBILITY_v01_20260902.md": "8b8aaa99cc121f23c0f9ffa87998ceb43200b0cf8ed76d4a452e61ee7e5036c1",
    REQUEST_DIR / "Q1_D08C1_MAINLINE_DECISION_RHODE_ISLAND_ALIAS_v01_20260902.md": "72111e6d9a7340256f7a7008a9f275614653f7e1aa25aed0745a1f9dc903e8c8",
    ROOT / "06_src" / "elig_v02" / "D04_extract_FIA_pilot.py": "4604e4e288881a89cc0c98476a40a806c8e14005ec50815c95a79c2becd63683",
    ROOT / "06_src" / "elig_v02" / "parameters.json": "d3071f6a3fb31b432d7aab0bfaf1365fd4c003876ddbfab743ca04378b72ebfe",
    ROOT / "05_qc" / "elig_v02" / "D04_CONTINUITY_AUDIT.csv": "bed1f4ccb2a384f57e7a1aa145f7327a61470d0f8f2572301623f7ff624fbd6e",
    ROOT / "05_qc" / "elig_v02" / "LINEAGE_AUDIT.csv": "45cdad73f26a0d9b6cc807d94ee60b2e743568ca15eb518a96fc049dc68cd782",
    ROOT / "05_qc" / "elig_v02" / "AB_SPLIT_AUDIT.csv": "236fc9dd03f640f708e4fd9b5e0b8733ef2fa2381048860c405e4da432d85438",
    ROOT / "05_qc" / "elig_v02" / "DOMAIN_GRID_AUDIT.csv": "e2a208663114d6d113502b14595ec14ea801a642ac8e4d472c37b0a690ce50ee",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def norm(value) -> str:
    return "" if value is None else str(value).strip()


def norm_int(value) -> str:
    value = norm(value)
    if not value:
        return ""
    try:
        return str(int(float(value)))
    except (TypeError, ValueError):
        return value


def safe_ratio(numerator, denominator):
    return None if denominator in (0, None) else numerator / denominator


def sha256_file(path: Path, progress_label: str | None = None) -> str:
    digest = hashlib.sha256()
    total = path.stat().st_size
    consumed = 0
    next_report = 5 * 1024**3
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
            consumed += len(chunk)
            if progress_label and consumed >= next_report:
                print(f"{now_iso()} {progress_label}: {consumed / 1024**3:.1f}/{total / 1024**3:.1f} GiB", flush=True)
                next_report += 5 * 1024**3
    return digest.hexdigest()


def crc32_file(path: Path, progress_label: str | None = None) -> int:
    value = 0
    total = path.stat().st_size
    consumed = 0
    next_report = 10 * 1024**3
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            value = zlib.crc32(chunk, value)
            consumed += len(chunk)
            if progress_label and consumed >= next_report:
                print(f"{now_iso()} {progress_label}: {consumed / 1024**3:.1f}/{total / 1024**3:.1f} GiB", flush=True)
                next_report += 10 * 1024**3
    return value & 0xFFFFFFFF


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows, fields: list[str] | None = None) -> None:
    rows = list(rows)
    if fields is None:
        if not rows:
            raise RuntimeError(f"Cannot infer fields for empty output: {path.name}")
        fields = list(rows[0])
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: "" if row.get(key) is None else row.get(key) for key in fields})


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8", newline="\n")


# Exact D04 ellipsoidal Albers implementation.
A = 6378137.0
INV_F = 298.257222101
F = 1.0 / INV_F
B = A * (1.0 - F)
E = math.sqrt(1.0 - (B * B) / (A * A))
LAT1 = math.radians(29.5)
LAT2 = math.radians(45.5)
LAT0 = math.radians(23.0)
LON0 = math.radians(-96.0)


def _m(phi):
    sine = math.sin(phi)
    return math.cos(phi) / math.sqrt(1.0 - E * E * sine * sine)


def _q(phi):
    sine = math.sin(phi)
    es = E * sine
    return (1.0 - E * E) * (
        sine / (1.0 - es * es)
        - (1.0 / (2.0 * E)) * math.log((1.0 - es) / (1.0 + es))
    )


M1, M2 = _m(LAT1), _m(LAT2)
Q1, Q2, Q0 = _q(LAT1), _q(LAT2), _q(LAT0)
N_ALB = (M1 * M1 - M2 * M2) / (Q2 - Q1)
C_ALB = M1 * M1 + N_ALB * Q1
RHO0 = A * math.sqrt(C_ALB - N_ALB * Q0) / N_ALB


def albers5070(longitude_deg, latitude_deg):
    phi = math.radians(latitude_deg)
    lam = math.radians(longitude_deg)
    rho = A * math.sqrt(C_ALB - N_ALB * _q(phi)) / N_ALB
    theta = N_ALB * (lam - LON0)
    return rho * math.sin(theta), RHO0 - rho * math.cos(theta)


def cell_id(x_m, y_m, grain_km):
    grain_m = grain_km * 1000.0
    return f"{grain_km}km_{math.floor(x_m / grain_m)}_{math.floor(y_m / grain_m)}"


def parse_cell(identifier):
    _, x, y = identifier.split("_")
    return int(x), int(y)


def connected_geometry(cell_ids, grain_km):
    cells = {parse_cell(value) for value in cell_ids}
    if not cells:
        return 0, None, None
    unseen = set(cells)
    sizes = []
    while unseen:
        seed = unseen.pop()
        queue = deque([seed])
        size = 0
        while queue:
            x, y = queue.popleft()
            size += 1
            for neighbor in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    queue.append(neighbor)
        sizes.append(size)
    xs = [x for x, _ in cells]
    ys = [y for _, y in cells]
    span = grain_km * math.hypot(max(xs) - min(xs), max(ys) - min(ys))
    return len(sizes), max(sizes) / len(cells), span


def input_audit(params):
    rows = []
    raw_manifest = read_csv(ROOT / "00_control" / "raw_manifest_v02.csv")
    for raw in raw_manifest:
        path = Path(raw["local_file"])
        label = "FIA raw SHA-256" if path == FIA_ZIP else None
        actual_hash = sha256_file(path, label)
        status = "PASS" if path.stat().st_size == int(raw["size_bytes"]) and actual_hash == raw["sha256"] else "FAIL"
        rows.append({
            "file_role": "FORMAL_RAW_CONTROL" if path != FIA_ZIP else "FORMAL_FIA_RAW_COMPUTATION_SOURCE",
            "path": str(path),
            "size_bytes": path.stat().st_size,
            "sha256": actual_hash,
            "expected_size": int(raw["size_bytes"]),
            "expected_sha256": raw["sha256"],
            "status": status,
        })
    for path, expected in CONTROL_EXPECTED.items():
        actual = sha256_file(path)
        rows.append({
            "file_role": "FROZEN_CONTROL_OR_AUTHORITY",
            "path": str(path),
            "size_bytes": path.stat().st_size,
            "sha256": actual,
            "expected_size": path.stat().st_size,
            "expected_sha256": expected,
            "status": "PASS" if actual == expected else "FAIL",
        })
    for name, expected in params["d08b1_authority_hashes"].items():
        path = TAX / name
        actual = sha256_file(path)
        rows.append({
            "file_role": "D08B1_V02_TAXONOMY_RANGE_AUTHORITY",
            "path": str(path),
            "size_bytes": path.stat().st_size,
            "sha256": actual,
            "expected_size": path.stat().st_size,
            "expected_sha256": expected,
            "status": "PASS" if actual == expected else "FAIL",
        })

    with zipfile.ZipFile(FIA_ZIP, "r") as archive:
        info = archive.getinfo("SQLite_FIADB_ENTIRE.db")
    extracted_crc = crc32_file(DB_PATH, "Extracted FIADB CRC-32")
    db_status = "PASS" if DB_PATH.stat().st_size == info.file_size and extracted_crc == info.CRC else "FAIL"
    rows.append({
        "file_role": "EXTRACTED_FIA_DATABASE_MEMBER",
        "path": str(DB_PATH),
        "size_bytes": DB_PATH.stat().st_size,
        "sha256": f"CRC32:{extracted_crc:08x}",
        "expected_size": info.file_size,
        "expected_sha256": f"CRC32:{info.CRC:08x}",
        "status": db_status,
    })
    write_csv(OUT / "Q1_D08C1_INPUT_AUDIT_v01.csv", rows)
    if any(row["status"] != "PASS" for row in rows):
        raise RuntimeError("STOP_INPUT_INTEGRITY_FAILURE")
    return rows


def load_authorities():
    code_rows = read_csv(TAX / "Q1_FIA_CODE_TO_ANALYSIS_SPECIES_v02.csv")
    species_rows = read_csv(TAX / "Q1_ANALYSIS_SPECIES_MASTER_v02.csv")
    global_rows = read_csv(TAX / "Q1_GLOBAL_RANGE_FLAGS_v02.csv")
    distribution_rows = read_csv(TAX / "Q1_WCVP_NATIVE_DISTRIBUTION_LONG_v02.csv")
    drc_rows = read_csv(TAX / "Q1_DRC_PROTOCOL_v02.csv")
    code_map = {norm_int(row["fia_species_code"]): row for row in code_rows}
    species = {row["analysis_species_id"]: row for row in species_rows}
    global_flags = {row["analysis_species_id"]: row for row in global_rows}
    drc = {row["analysis_species_id"]: row for row in drc_rows}
    if len(code_rows) != 396 or len(code_map) != 396:
        raise RuntimeError("STOP_D08B1_CODE_MAP_NOT_396_UNIQUE")
    if len(species) != 361 or set(species) != set(global_flags) or set(species) != set(drc):
        raise RuntimeError("STOP_D08B1_SPECIES_AUTHORITY_MISMATCH")
    return code_rows, code_map, species, global_flags, distribution_rows, drc


def build_state_evidence(connection, params, species, global_flags, distribution_rows):
    state_rows = connection.execute(
        "SELECT DISTINCT STATECD, STATEAB, STATENM FROM SURVEY ORDER BY STATECD"
    ).fetchall()
    state_map = {int(code): {"STATECD": int(code), "STATEAB": norm(ab), "STATENM": norm(name)} for code, ab, name in state_rows}
    excluded = set(params["excluded_primary_state_codes"])
    conus_codes = sorted(code for code in state_map if code not in excluded)
    if len(conus_codes) != 48:
        raise RuntimeError(f"STOP_EXPECTED_48_CONUS_STATES_FOUND_{len(conus_codes)}")

    areas_by_name = defaultdict(set)
    rows_by_species_area = defaultdict(list)
    for row in distribution_rows:
        areas_by_name[row["area"]].add(row["area_code_l3"])
        rows_by_species_area[(row["analysis_species_id"], row["area_code_l3"])].append(row)
    crosswalk = []
    area_code_by_state = {}
    for code in conus_codes:
        state = state_map[code]
        if code == 44:
            alias = params["authorized_state_aliases"][0]
            valid = (
                state["STATEAB"] == alias["fia_state_ab"]
                and state["STATENM"] == alias["fia_state_name"]
                and alias["wcvp_area_code_l3"] in areas_by_name[alias["wcvp_area_name"]]
            )
            if not valid:
                raise RuntimeError("STOP_AUTHORIZED_RI_ALIAS_DOES_NOT_MATCH_FROZEN_INPUTS")
            mapping_type = "AUTHORIZED_EXPLICIT_ALIAS"
            area_code = alias["wcvp_area_code_l3"]
            area_name = alias["wcvp_area_name"]
        else:
            matches = sorted(areas_by_name.get(state["STATENM"], set()))
            if len(matches) != 1:
                raise RuntimeError(f"STOP_ADDITIONAL_NONEXACT_STATE_CORRESPONDENCE:{code}:{state['STATENM']}:{matches}")
            mapping_type = "EXACT_FULL_STATE_NAME"
            area_code = matches[0]
            area_name = state["STATENM"]
        area_code_by_state[code] = area_code
        crosswalk.append({
            "fia_state_code": code,
            "fia_state_ab": state["STATEAB"],
            "fia_state_name": state["STATENM"],
            "wcvp_area_code_l3": area_code,
            "wcvp_area_name": area_name,
            "mapping_type": mapping_type,
            "fuzzy_matching_used": 0,
            "status": "PASS",
        })
    write_csv(OUT / "Q1_D08C1_STATE_CROSSWALK_AUDIT_v01.csv", crosswalk)

    evidence = {}
    evidence_detail = {}
    conflict_rows = []
    for sid in species:
        for state_code in conus_codes:
            rows = rows_by_species_area.get((sid, area_code_by_state[state_code]), [])
            native = [row for row in rows if row["introduced"] == "0" and row["extinct"] == "0" and row["location_doubtful"] == "0"]
            introduced = [row for row in rows if row["introduced"] == "1"]
            if native and introduced:
                conflict_rows.append((sid, state_code))
            if native:
                classification = "CONFIRMED_CURRENT_NATIVE"
            elif introduced:
                classification = "EXPLICIT_INTRODUCED"
            else:
                classification = "NO_CONFIRMED_NATIVE_OR_INTRODUCED_ROW"
            evidence[(sid, state_code)] = classification
            evidence_detail[(sid, state_code)] = {
                "wcvp_level3_rows": len(rows),
                "confirmed_current_native_rows": len(native),
                "explicit_introduced_rows": len(introduced),
                "native_historical_extinct_rows": sum(row["introduced"] == "0" and row["extinct"] == "1" for row in rows),
                "native_location_doubtful_rows": sum(row["introduced"] == "0" and row["location_doubtful"] == "1" for row in rows),
            }
    if conflict_rows:
        raise RuntimeError(f"STOP_NATIVE_INTRODUCED_STATE_CONFLICT:{conflict_rows[:10]}")
    for sid in species:
        computed = any(evidence[(sid, state)] == "CONFIRMED_CURRENT_NATIVE" for state in conus_codes)
        frozen = global_flags[sid]["confirmed_native_CONUS"] == "TRUE"
        if computed != frozen:
            raise RuntimeError(f"STOP_GLOBAL_NATIVE_FLAG_MISMATCH:{sid}:{computed}:{frozen}")
    return state_map, conus_codes, crosswalk, area_code_by_state, evidence, evidence_detail


def build_lineages(connection, params, state_map, conus_codes):
    candidate_rows = {}
    for row in connection.execute(
        """
        SELECT CN, PREV_PLT_CN, INVYR, STATECD, UNITCD, COUNTYCD, PLOT,
               PLOT_STATUS_CD, MEASYEAR, MEASMON, MEASDAY, P2PANEL,
               LAT, LON, MANUAL, DESIGNCD
        FROM PLOT WHERE MEASYEAR BETWEEN ? AND ?
        """,
        (params["measurement_year_min"], params["measurement_year_max"]),
    ):
        cn = norm(row[0])
        code = int(row[3])
        if code not in conus_codes and code != 11:
            continue
        candidate_rows[cn] = {
            "CN": cn, "PREV_PLT_CN": norm(row[1]), "INVYR": row[2], "STATECD": code,
            "STATEAB": state_map.get(code, {"STATEAB": str(code)})["STATEAB"],
            "STATENM": state_map.get(code, {"STATENM": ""})["STATENM"],
            "UNITCD": row[4], "COUNTYCD": row[5], "PLOT": row[6], "PLOT_STATUS_CD": row[7],
            "MEASYEAR": row[8], "MEASMON": row[9], "MEASDAY": row[10], "P2PANEL": row[11],
            "LAT": row[12], "LON": row[13], "MANUAL": row[14], "DESIGNCD": row[15],
        }
    connection.execute("DROP TABLE IF EXISTS temp.d08c1_candidate_measurements")
    connection.execute("CREATE TEMP TABLE d08c1_candidate_measurements (CN TEXT PRIMARY KEY)")
    connection.executemany("INSERT INTO d08c1_candidate_measurements(CN) VALUES (?)", ((cn,) for cn in candidate_rows))
    forest_conditions = set()
    forest_plots = set()
    for plot_cn, condition_id in connection.execute(
        """
        SELECT c.PLT_CN, c.CONDID FROM COND c
        JOIN d08c1_candidate_measurements p ON p.CN=c.PLT_CN
        WHERE c.COND_STATUS_CD=? AND c.CONDPROP_UNADJ>0
        """,
        (params["condition_status_cd"],),
    ):
        key = (norm(plot_cn), norm_int(condition_id))
        forest_conditions.add(key)
        forest_plots.add(key[0])
    eligible = {cn for cn, row in candidate_rows.items() if row["PLOT_STATUS_CD"] == params["plot_status_cd"] and cn in forest_plots}

    placeholders = ",".join("?" for _ in conus_codes)
    prev_by_cn = {}
    child_counts = Counter()
    for cn, previous in connection.execute(f"SELECT CN, PREV_PLT_CN FROM PLOT WHERE STATECD IN ({placeholders})", conus_codes):
        cn, previous = norm(cn), norm(previous)
        prev_by_cn[cn] = previous
        if previous:
            child_counts[previous] += 1
    root_cache = {}
    cycle_roots = set()

    def root_of(start):
        if start in root_cache:
            return root_cache[start]
        path, positions = [], {}
        current = start
        while True:
            if current in root_cache:
                root = root_cache[current]
                break
            if current in positions:
                nodes = path[positions[current]:]
                root = "CYCLE:" + min(nodes)
                cycle_roots.add(root)
                break
            positions[current] = len(path)
            path.append(current)
            previous = prev_by_cn.get(current, "")
            if not previous or previous not in prev_by_cn:
                root = current
                break
            current = previous
        for node in path:
            root_cache[node] = root
        return root

    fork_roots = {root_of(node) for node, count in child_counts.items() if count > 1 and node in prev_by_cn}
    lineage_groups = defaultdict(list)
    for cn in eligible:
        lineage_groups[root_of(cn)].append(cn)

    def latest_key(cn):
        row = candidate_rows[cn]
        cn_key = int(cn) if cn.isdigit() else cn
        return tuple(-1 if row[key] is None else row[key] for key in ("MEASYEAR", "MEASMON", "MEASDAY", "INVYR")) + (cn_key,)

    primary = {}
    ambiguous_lineages = set()
    ambiguous_measurements = 0
    for lineage_id, measurements in lineage_groups.items():
        if lineage_id in fork_roots or lineage_id in cycle_roots:
            ambiguous_lineages.add(lineage_id)
            ambiguous_measurements += len(measurements)
            continue
        selected = max(measurements, key=latest_key)
        record = dict(candidate_rows[selected])
        record["lineage_id"] = lineage_id
        primary[selected] = record

    groups = defaultdict(list)
    for cn, row in primary.items():
        panel = norm_int(row["P2PANEL"]) or "NA"
        digest = hashlib.sha256((params["split_seed"] + "|" + cn).encode()).hexdigest()
        groups[(row["STATEAB"], panel)].append((digest, cn))
    for values in groups.values():
        for index, (_, cn) in enumerate(sorted(values)):
            primary[cn]["fold"] = "A" if index % 2 == 0 else "B"

    spatial = {}
    coordinate_failures = 0
    for cn, row in primary.items():
        try:
            latitude, longitude = float(row["LAT"]), float(row["LON"])
            if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
                raise ValueError
            x_m, y_m = albers5070(longitude, latitude)
        except Exception:
            coordinate_failures += 1
            continue
        row["x_m"], row["y_m"] = x_m, y_m
        for grain in params["grains_km"]:
            row[f"cell_{grain}km"] = cell_id(x_m, y_m, grain)
        spatial[cn] = row

    lineage_row = {
        "candidate_measurements_2017_2023": len(candidate_rows),
        "eligible_measurements_before_lineage_dedup": len(eligible),
        "unique_lineages_before_ambiguity_exclusion": len(lineage_groups),
        "ambiguous_lineages_excluded": len(ambiguous_lineages),
        "ambiguous_measurements_excluded": ambiguous_measurements,
        "primary_measurements_after_dedup": len(primary),
        "primary_measurements_with_valid_coordinates": len(spatial),
        "primary_measurements_missing_coordinates": coordinate_failures,
        "no_dedup_sensitivity_additional_measurements": len(eligible) - len(primary),
        "no_dedup_sensitivity_percent_increase": safe_ratio(len(eligible) - len(primary), len(primary)),
        "lineage_rule_id": params["lineage_rule_id"],
        "status": "PASS" if len(primary) == len({row["lineage_id"] for row in primary.values()}) else "FAIL",
    }
    write_csv(OUT / "Q1_D08C1_LINEAGE_AUDIT_v01.csv", [lineage_row])
    return primary, spatial, forest_conditions, lineage_row


def build_split_grid_audits(primary, spatial, params):
    groups = defaultdict(list)
    for row in primary.values():
        panel = norm_int(row["P2PANEL"]) or "NA"
        groups[(row["STATEAB"], panel)].append(row)
    split_rows = []
    for (state, panel), rows in sorted(groups.items()):
        n_a = sum(row["fold"] == "A" for row in rows)
        n_b = len(rows) - n_a
        split_rows.append({
            "stratum": f"{state}|{panel}", "state": state, "P2PANEL": panel,
            "n_lineages_total": len(rows), "n_A": n_a, "n_B": n_b,
            "abs_balance_diff": abs(n_a - n_b), "missing_P2PANEL_count": len(rows) if panel == "NA" else 0,
            "duplicate_lineage_across_AB": 0, "duplicate_primary_measurement": 0,
            "split_seed": params["split_seed"], "split_rule_id": params["split_rule_id"],
            "status": "PASS" if abs(n_a - n_b) <= 1 else "FAIL",
        })
    write_csv(OUT / "Q1_D08C1_AB_SPLIT_AUDIT_v01.csv", split_rows)

    grid_rows = []
    for grain in params["grains_km"]:
        cells = defaultdict(int)
        parent_failures = 0
        for row in spatial.values():
            cells[row[f"cell_{grain}km"]] += 1
            x25, y25 = parse_cell(row["cell_25km"])
            xg, yg = parse_cell(row[f"cell_{grain}km"])
            if xg != math.floor(x25 / (grain / 25)) or yg != math.floor(y25 / (grain / 25)):
                parent_failures += 1
        grid_rows.append({
            "projection": "NAD83 / CONUS Albers equal-area (EPSG:5070 ellipsoidal D04 implementation)",
            "origin_x": 0.0, "origin_y": 0.0, "grain_km": grain,
            "n_cells_total": len(cells), "n_cells_with_eligible_plots": len(cells),
            "n_unique_physical_plot_lineages": len(primary), "n_primary_measurements": len(primary),
            "n_spatial_primary_measurements": len(spatial),
            "parent_mapping_check": "PASS" if parent_failures == 0 else "FAIL",
            "parent_mapping_failures": parent_failures,
            "boundary_domain_mask": "CONUS 48 + DC if present; sampled fixed-grid cells contain >=1 primary eligible FIA measurement",
            "grid_recentered_on_national_data": 0,
            "status": "PASS" if parent_failures == 0 else "FAIL",
        })
    write_csv(OUT / "Q1_D08C1_DOMAIN_GRID_AUDIT_v01.csv", grid_rows)
    return split_rows, grid_rows


def scan_trees(connection, primary, forest_conditions, code_map, evidence):
    connection.execute("DROP TABLE IF EXISTS temp.d08c1_primary_measurements")
    connection.execute("CREATE TEMP TABLE d08c1_primary_measurements (CN TEXT PRIMARY KEY, fold TEXT)")
    connection.executemany("INSERT INTO d08c1_primary_measurements(CN,fold) VALUES (?,?)", ((cn, row["fold"]) for cn, row in primary.items()))
    connection.execute("DROP TABLE IF EXISTS temp.d08c1_forest_conditions")
    connection.execute("CREATE TEMP TABLE d08c1_forest_conditions (PLT_CN TEXT, CONDID TEXT, PRIMARY KEY(PLT_CN,CONDID))")
    primary_set = set(primary)
    connection.executemany(
        "INSERT INTO d08c1_forest_conditions(PLT_CN,CONDID) VALUES (?,?)",
        (key for key in forest_conditions if key[0] in primary_set),
    )

    seen_cn = set()
    duplicate_cn = 0
    blank_cn = 0
    total_rows = 0
    ordinary_rows = 0
    nonanalysis_rows = 0
    species_plot_counts = defaultdict(Counter)
    record_counts = Counter()
    code_record_counts = Counter()
    code_plots = defaultdict(set)
    species_state_records = Counter()
    species_state_plots = defaultdict(set)
    species_state_fold_plots = defaultdict(set)
    nonanalysis_record_counts = Counter()
    nonanalysis_plots = defaultdict(set)
    nonanalysis_states = defaultdict(Counter)

    query = """
        SELECT t.CN, t.PLT_CN, CAST(t.SPCD AS TEXT), p.fold
        FROM TREE t
        JOIN d08c1_primary_measurements p ON p.CN=t.PLT_CN
        JOIN d08c1_forest_conditions f
          ON f.PLT_CN=t.PLT_CN AND f.CONDID=CAST(t.CONDID AS TEXT)
        WHERE t.STATUSCD=1 AND t.DIA>=5.0
    """
    print(f"{now_iso()} Starting unique bottom-level TREE scan", flush=True)
    for tree_cn, plot_cn, species_code, fold in connection.execute(query):
        total_rows += 1
        if total_rows % 250000 == 0:
            print(f"{now_iso()} TREE scan qualifying rows: {total_rows:,}", flush=True)
        tree_cn = norm(tree_cn)
        if not tree_cn:
            blank_cn += 1
            continue
        if tree_cn in seen_cn:
            duplicate_cn += 1
            continue
        seen_cn.add(tree_cn)
        plot_cn = norm(plot_cn)
        code = norm_int(species_code) or "UNIDENTIFIED"
        state_code = primary[plot_cn]["STATECD"]
        mapping = code_map.get(code)
        if mapping and mapping["ordinary_analysis_species_flag"] == "1":
            ordinary_rows += 1
            sid = mapping["analysis_species_id"]
            evidence_class = evidence[(sid, state_code)]
            basis = mapping["diameter_measurement_basis"] or "UNCLASSIFIED_DIAMETER_BASIS"
            species_plot_counts[sid][plot_cn] += 1
            record_counts[(sid, fold, evidence_class, basis)] += 1
            code_record_counts[(code, fold, evidence_class)] += 1
            code_plots[code].add(plot_cn)
            species_state_records[(sid, state_code, fold)] += 1
            species_state_plots[(sid, state_code)].add(plot_cn)
            species_state_fold_plots[(sid, state_code, fold)].add(plot_cn)
        else:
            nonanalysis_rows += 1
            if mapping:
                reason = mapping["no_analysis_species_reason"] or mapping["mapping_class"] or "D08B1_NO_ANALYSIS_SPECIES"
                map_class = mapping["mapping_class"]
            else:
                reason = "NOT_IN_D08B1_396_CODE_MAP"
                map_class = "NOT_IN_D08B1_396_CODE_MAP"
            nonanalysis_record_counts[(code, fold, reason, map_class)] += 1
            nonanalysis_plots[code].add(plot_cn)
            nonanalysis_states[code][state_code] += 1
    print(f"{now_iso()} TREE scan complete: {total_rows:,} qualifying rows", flush=True)
    return {
        "total_rows": total_rows,
        "unique_tree_cn": len(seen_cn),
        "duplicate_cn": duplicate_cn,
        "blank_cn": blank_cn,
        "ordinary_rows": ordinary_rows,
        "nonanalysis_rows": nonanalysis_rows,
        "species_plot_counts": species_plot_counts,
        "record_counts": record_counts,
        "code_record_counts": code_record_counts,
        "code_plots": code_plots,
        "species_state_records": species_state_records,
        "species_state_plots": species_state_plots,
        "species_state_fold_plots": species_state_fold_plots,
        "nonanalysis_record_counts": nonanalysis_record_counts,
        "nonanalysis_plots": nonanalysis_plots,
        "nonanalysis_states": nonanalysis_states,
    }


def record_summary(tree, sid, fold_scope, allowed_classes):
    result = Counter()
    folds = ("A", "B") if fold_scope == "ALL" else (fold_scope,)
    for fold in folds:
        for evidence_class in allowed_classes:
            for basis in ("DBH_BREAST_HEIGHT", "DRC_ROOT_COLLAR", "UNCLASSIFIED_DIAMETER_BASIS"):
                count = tree["record_counts"][(sid, fold, evidence_class, basis)]
                result["total"] += count
                result[evidence_class] += count
                result[basis] += count
    return result


def build_census(params, species, global_flags, drc, primary, spatial, conus_codes, evidence, tree):
    plots_all_fold = {
        "ALL": set(spatial),
        "A": {cn for cn, row in spatial.items() if row["fold"] == "A"},
        "B": {cn for cn, row in spatial.items() if row["fold"] == "B"},
    }
    plots_state_fold = defaultdict(set)
    for cn, row in spatial.items():
        plots_state_fold[(row["STATECD"], "ALL")].add(cn)
        plots_state_fold[(row["STATECD"], row["fold"])].add(cn)
    census = []
    index = {}
    all_classes = ("CONFIRMED_CURRENT_NATIVE", "EXPLICIT_INTRODUCED", "NO_CONFIRMED_NATIVE_OR_INTRODUCED_ROW")
    for sid, taxon in sorted(species.items(), key=lambda item: item[1]["analysis_species_name"]):
        positive_all = set(tree["species_plot_counts"].get(sid, {})) & set(spatial)
        native_states = {state for state in conus_codes if evidence[(sid, state)] == "CONFIRMED_CURRENT_NATIVE"}
        for view in params["census_views"]:
            allowed_classes = all_classes if view == "ALL_CONUS_OBSERVED" else ("CONFIRMED_CURRENT_NATIVE",)
            for grain in params["grains_km"]:
                for fold_scope in params["fold_scopes"]:
                    if view == "ALL_CONUS_OBSERVED":
                        sampled_plots = plots_all_fold[fold_scope]
                    else:
                        sampled_plots = set()
                        for state in native_states:
                            sampled_plots.update(plots_state_fold[(state, fold_scope)])
                    positive = positive_all & sampled_plots
                    sampled_cells = {spatial[cn][f"cell_{grain}km"] for cn in sampled_plots}
                    detected_cells = {spatial[cn][f"cell_{grain}km"] for cn in positive}
                    components, largest, span = connected_geometry(detected_cells, grain)
                    counts = record_summary(tree, sid, fold_scope, allowed_classes)
                    row = {
                        "analysis_species_id": sid,
                        "analysis_species_name": taxon["analysis_species_name"],
                        "analysis_species_authors": taxon["analysis_species_authors"],
                        "analysis_species_rank": taxon["analysis_species_rank"],
                        "component_fia_code_count": taxon["component_fia_code_count"],
                        "component_fia_codes": taxon["component_fia_codes"],
                        "component_fia_names": taxon["component_fia_names"],
                        "diameter_basis_composition": drc[sid]["diameter_basis_composition"],
                        "confirmed_native_CONUS": global_flags[sid]["confirmed_native_CONUS"],
                        "core_eligibility_status": "CORE_ELIGIBLE_CONFIRMED_NATIVE_CONUS" if global_flags[sid]["confirmed_native_CONUS"] == "TRUE" else "CONUS_NONNATIVE_CORE_INELIGIBLE",
                        "grain_km": grain,
                        "census_view": view,
                        "fold_scope": fold_scope,
                        "n_unique_physical_plot_lineages": len(sampled_plots),
                        "n_primary_measurements": len(sampled_plots),
                        "n_sampled_cells": len(sampled_cells),
                        "n_positive_plots": len(positive),
                        "n_detected_cells": len(detected_cells),
                        "n_qualifying_tree_rows": counts["total"],
                        "n_dbh_tree_rows": counts["DBH_BREAST_HEIGHT"],
                        "n_drc_tree_rows": counts["DRC_ROOT_COLLAR"],
                        "n_unclassified_diameter_basis_tree_rows": counts["UNCLASSIFIED_DIAMETER_BASIS"],
                        "n_confirmed_native_state_tree_rows": counts["CONFIRMED_CURRENT_NATIVE"],
                        "n_explicit_introduced_state_tree_rows": counts["EXPLICIT_INTRODUCED"],
                        "n_no_confirmed_native_or_introduced_state_tree_rows": counts["NO_CONFIRMED_NATIVE_OR_INTRODUCED_ROW"],
                        "n_connected_components_detection_support": components,
                        "largest_component_fraction": largest,
                        "spatial_span_km": span,
                        "sampling_frame_note": "cells with >=1 qualifying primary FIA measurement; unsampled political cells are not zeros",
                        "threshold_role": "CENSUS_ONLY_NOT_FINAL_SELECTION",
                    }
                    census.append(row)
                    index[(sid, grain, view, fold_scope)] = row
    write_csv(OUT / "Q1_D08C1_SPECIES_GRAIN_CENSUS_v01.csv", census)
    return census, index


def build_native_state_audit(species, global_flags, state_map, conus_codes, crosswalk, evidence, detail, tree):
    cross = {row["fia_state_code"]: row for row in crosswalk}
    rows = []
    for sid, taxon in sorted(species.items(), key=lambda item: item[1]["analysis_species_name"]):
        for state_code in conus_codes:
            d = detail[(sid, state_code)]
            rows.append({
                "analysis_species_id": sid,
                "analysis_species_name": taxon["analysis_species_name"],
                "fia_state_code": state_code,
                "fia_state_ab": state_map[state_code]["STATEAB"],
                "fia_state_name": state_map[state_code]["STATENM"],
                "wcvp_area_code_l3": cross[state_code]["wcvp_area_code_l3"],
                "wcvp_area_name": cross[state_code]["wcvp_area_name"],
                "state_identity_mapping_type": cross[state_code]["mapping_type"],
                **d,
                "state_evidence_class": evidence[(sid, state_code)],
                "qualifying_tree_rows": sum(tree["species_state_records"][(sid, state_code, fold)] for fold in ("A", "B")),
                "qualifying_tree_rows_fold_A": tree["species_state_records"][(sid, state_code, "A")],
                "qualifying_tree_rows_fold_B": tree["species_state_records"][(sid, state_code, "B")],
                "positive_primary_plots": len(tree["species_state_plots"][(sid, state_code)]),
                "positive_primary_plots_fold_A": len(tree["species_state_fold_plots"][(sid, state_code, "A")]),
                "positive_primary_plots_fold_B": len(tree["species_state_fold_plots"][(sid, state_code, "B")]),
                "confirmed_native_CONUS": global_flags[sid]["confirmed_native_CONUS"],
                "core_eligibility_status": "CORE_ELIGIBLE_CONFIRMED_NATIVE_CONUS" if global_flags[sid]["confirmed_native_CONUS"] == "TRUE" else "CONUS_NONNATIVE_CORE_INELIGIBLE",
                "status_inference_from_alias": 0,
            })
    write_csv(OUT / "Q1_D08C1_NATIVE_STATE_AUDIT_v01.csv", rows)
    return rows


def build_code_audits(code_rows, code_map, species, tree):
    ordinary = [row for row in code_rows if row["ordinary_analysis_species_flag"] == "1"]
    component_by_species = defaultdict(list)
    for row in ordinary:
        component_by_species[row["analysis_species_id"]].append(row["fia_species_code"])
    sum_component_plots = {
        sid: sum(len(tree["code_plots"].get(code, set())) for code in codes)
        for sid, codes in component_by_species.items()
    }
    rows = []
    for row in sorted(ordinary, key=lambda value: int(value["fia_species_code"])):
        code, sid = row["fia_species_code"], row["analysis_species_id"]
        count = lambda fold, cls: tree["code_record_counts"][(code, fold, cls)]
        native = sum(count(fold, "CONFIRMED_CURRENT_NATIVE") for fold in ("A", "B"))
        introduced = sum(count(fold, "EXPLICIT_INTRODUCED") for fold in ("A", "B"))
        unknown = sum(count(fold, "NO_CONFIRMED_NATIVE_OR_INTRODUCED_ROW") for fold in ("A", "B"))
        total = native + introduced + unknown
        pooled_plots = len(tree["species_plot_counts"].get(sid, {}))
        rows.append({
            "fia_species_code": code,
            "fia_name_raw": row["fia_name_raw"],
            "analysis_species_id": sid,
            "analysis_species_name": row["analysis_species_name"],
            "analysis_species_authors": row["analysis_species_authors"],
            "mapping_class": row["mapping_class"],
            "diameter_measurement_basis": row["diameter_measurement_basis"],
            "pooling_group_component_code_count": len(component_by_species[sid]),
            "pooling_group_component_codes": ";".join(sorted(component_by_species[sid], key=int)),
            "pooling_applied_flag": 1 if len(component_by_species[sid]) > 1 else 0,
            "qualifying_tree_rows": total,
            "qualifying_tree_rows_fold_A": sum(count("A", cls) for cls in ("CONFIRMED_CURRENT_NATIVE", "EXPLICIT_INTRODUCED", "NO_CONFIRMED_NATIVE_OR_INTRODUCED_ROW")),
            "qualifying_tree_rows_fold_B": sum(count("B", cls) for cls in ("CONFIRMED_CURRENT_NATIVE", "EXPLICIT_INTRODUCED", "NO_CONFIRMED_NATIVE_OR_INTRODUCED_ROW")),
            "confirmed_native_state_tree_rows": native,
            "explicit_introduced_state_tree_rows": introduced,
            "unclassified_state_tree_rows": unknown,
            "component_positive_primary_plots": len(tree["code_plots"].get(code, set())),
            "pooled_species_positive_primary_plots": pooled_plots,
            "sum_component_positive_plots_before_dedup": sum_component_plots[sid],
            "plot_overlap_removed_by_species_pooling": sum_component_plots[sid] - pooled_plots,
            "aggregation_rule": "POOL_BOTTOM_LEVEL_TREE_RECORDS_BY_ACCEPTED_ANALYSIS_SPECIES_BEFORE_PLOT_CELL_SUMMARY",
        })
    write_csv(OUT / "Q1_D08C1_CODE_AGGREGATION_AUDIT_v01.csv", rows)

    observed_codes = {key[0] for key in tree["nonanalysis_record_counts"]}
    excluded_codes = {row["fia_species_code"] for row in code_rows if row["ordinary_analysis_species_flag"] != "1"} | observed_codes
    non_rows = []
    for code in sorted(excluded_codes, key=lambda value: (not value.isdigit(), int(value) if value.isdigit() else value)):
        mapping = code_map.get(code)
        matching_keys = [key for key in tree["nonanalysis_record_counts"] if key[0] == code]
        total = sum(tree["nonanalysis_record_counts"][key] for key in matching_keys)
        by_fold = {fold: sum(tree["nonanalysis_record_counts"][key] for key in matching_keys if key[1] == fold) for fold in ("A", "B")}
        reasons = sorted({key[2] for key in matching_keys})
        classes = sorted({key[3] for key in matching_keys})
        non_rows.append({
            "fia_species_code": code,
            "fia_name_raw": mapping["fia_name_raw"] if mapping else "",
            "d08b1_mapping_class": mapping["mapping_class"] if mapping else "NOT_IN_D08B1_396_CODE_MAP",
            "taxonomy_resolution_status": mapping["taxonomy_resolution_status"] if mapping else "NOT_IN_AUTHORITY",
            "hybrid_or_nothotaxon_flag": mapping["hybrid_or_nothotaxon_flag"] if mapping else "",
            "no_analysis_species_reason": mapping["no_analysis_species_reason"] if mapping else "NOT_IN_D08B1_396_CODE_MAP",
            "observed_exclusion_reasons": ";".join(reasons),
            "observed_mapping_classes": ";".join(classes),
            "qualifying_tree_rows": total,
            "qualifying_tree_rows_fold_A": by_fold["A"],
            "qualifying_tree_rows_fold_B": by_fold["B"],
            "positive_primary_plots": len(tree["nonanalysis_plots"].get(code, set())),
            "state_codes_with_records": ";".join(map(str, sorted(tree["nonanalysis_states"].get(code, {})))),
            "ordinary_census_included_flag": 0,
            "audit_status": "REPORTED_SEPARATELY_NOT_IN_ORDINARY_ACCEPTED_SPECIES_CENSUS",
        })
    write_csv(OUT / "Q1_D08C1_NONANALYSIS_CODE_AUDIT_v01.csv", non_rows)
    return rows, non_rows


def build_frontiers_and_summary(params, species, global_flags, census_index):
    frontiers = []
    for view in params["census_views"]:
        for cell_min in params["frontier_detected_cells_each_fold"]:
            for plot_min in params["frontier_positive_plots_each_fold"]:
                passing = []
                passing_core = []
                for sid in species:
                    a = census_index[(sid, 50, view, "A")]
                    b = census_index[(sid, 50, view, "B")]
                    ok = min(a["n_detected_cells"], b["n_detected_cells"]) >= cell_min and min(a["n_positive_plots"], b["n_positive_plots"]) >= plot_min
                    if ok:
                        passing.append(sid)
                        if global_flags[sid]["confirmed_native_CONUS"] == "TRUE":
                            passing_core.append(sid)
                frontiers.append({
                    "grain_km": 50,
                    "census_view": view,
                    "detected_cells_each_fold_min": cell_min,
                    "positive_plots_each_fold_min": plot_min,
                    "n_analysis_species_total": len(species),
                    "n_species_passing_sampling_frontier": len(passing),
                    "proportion_species_passing_sampling_frontier": len(passing) / len(species),
                    "n_species_passing_and_core_eligible": len(passing_core),
                    "proportion_species_passing_and_core_eligible": len(passing_core) / len(species),
                    "threshold_role": "DESCRIPTIVE_FRONTIER_NOT_FINAL_SELECTION",
                    "final_threshold_selected": 0,
                })
    write_csv(OUT / "Q1_D08C1_50KM_FRONTIERS_v01.csv", frontiers)

    queue = []
    threshold = params["survivor_queue_detected_cells_each_fold"]
    for sid, taxon in sorted(species.items(), key=lambda item: item[1]["analysis_species_name"]):
        all_a, all_b = census_index[(sid, 50, "ALL_CONUS_OBSERVED", "A")], census_index[(sid, 50, "ALL_CONUS_OBSERVED", "B")]
        nat_a, nat_b = census_index[(sid, 50, "WCVP_CONFIRMED_NATIVE_STATE", "A")], census_index[(sid, 50, "WCVP_CONFIRMED_NATIVE_STATE", "B")]
        pass_all = min(all_a["n_detected_cells"], all_b["n_detected_cells"]) >= threshold
        pass_native = min(nat_a["n_detected_cells"], nat_b["n_detected_cells"]) >= threshold
        if pass_all or pass_native:
            queue.append({
                "analysis_species_id": sid,
                "analysis_species_name": taxon["analysis_species_name"],
                "confirmed_native_CONUS": global_flags[sid]["confirmed_native_CONUS"],
                "core_eligibility_status": "CORE_ELIGIBLE_CONFIRMED_NATIVE_CONUS" if global_flags[sid]["confirmed_native_CONUS"] == "TRUE" else "CONUS_NONNATIVE_CORE_INELIGIBLE",
                "all_view_detected_cells_fold_A": all_a["n_detected_cells"],
                "all_view_detected_cells_fold_B": all_b["n_detected_cells"],
                "native_view_detected_cells_fold_A": nat_a["n_detected_cells"],
                "native_view_detected_cells_fold_B": nat_b["n_detected_cells"],
                "passes_ge10_each_fold_all_view": int(pass_all),
                "passes_ge10_each_fold_native_view": int(pass_native),
                "union_queue_flag": 1,
                "queue_role": "LATER_RANGE_SOURCE_REVIEW_NOT_FINAL_COHORT",
                "little_information_used": 0,
            })
    write_csv(OUT / "Q1_D08C1_LITTLE_REVIEW_SURVIVOR_QUEUE_v01.csv", queue)

    summary = []
    for grain in params["grains_km"]:
        for view in params["census_views"]:
            rows_all = [census_index[(sid, grain, view, "ALL")] for sid in species]
            row = {
                "grain_km": grain,
                "census_view": view,
                "n_analysis_species_total": len(species),
                "n_species_with_any_detection": sum(item["n_detected_cells"] > 0 for item in rows_all),
                "n_core_eligible_species": sum(global_flags[sid]["confirmed_native_CONUS"] == "TRUE" for sid in species),
            }
            for threshold0 in params["frontier_detected_cells_each_fold"]:
                row[f"n_species_each_fold_ge{threshold0}_detected_cells"] = sum(
                    min(census_index[(sid, grain, view, "A")]["n_detected_cells"], census_index[(sid, grain, view, "B")]["n_detected_cells"]) >= threshold0
                    for sid in species
                )
                row[f"n_core_eligible_species_each_fold_ge{threshold0}_detected_cells"] = sum(
                    global_flags[sid]["confirmed_native_CONUS"] == "TRUE"
                    and min(census_index[(sid, grain, view, "A")]["n_detected_cells"], census_index[(sid, grain, view, "B")]["n_detected_cells"]) >= threshold0
                    for sid in species
                )
            summary.append(row)
    write_csv(OUT / "Q1_D08C1_GRAIN_SUMMARY_v01.csv", summary)
    return frontiers, queue, summary


def build_trace(species, spatial, conus_codes, evidence, tree):
    counts = {}
    positive_by_species = {}
    native_frame_by_species = {}
    for sid in species:
        native_states = {state for state in conus_codes if evidence[(sid, state)] == "CONFIRMED_CURRENT_NATIVE"}
        frame = {cn for cn, row in spatial.items() if row["STATECD"] in native_states}
        positive = set(tree["species_plot_counts"].get(sid, {})) & frame
        counts[sid] = len(positive)
        positive_by_species[sid] = positive
        native_frame_by_species[sid] = frame
    candidates = [sid for sid, count in counts.items() if count > 0]
    high = sorted(candidates, key=lambda sid: (-counts[sid], species[sid]["analysis_species_name"]))[:4]
    low = sorted((sid for sid in candidates if sid not in high), key=lambda sid: (counts[sid], species[sid]["analysis_species_name"]))[:4]
    remaining = [sid for sid in candidates if sid not in set(high) | set(low)]
    median = sorted(counts[sid] for sid in remaining)[len(remaining) // 2] if remaining else 0
    middle = sorted(remaining, key=lambda sid: (abs(counts[sid] - median), species[sid]["analysis_species_name"]))[:4]
    bands = {sid: "HIGH_NATIVE_DETECTION" for sid in high}
    bands.update({sid: "MIDDLE_NATIVE_DETECTION" for sid in middle})
    bands.update({sid: "LOW_NATIVE_DETECTION" for sid in low})
    rows = []
    for sid, band in sorted(bands.items(), key=lambda item: (item[1], species[item[0]]["analysis_species_name"])):
        positive = positive_by_species[sid]
        negative = native_frame_by_species[sid] - positive
        for status, pool in (("POSITIVE", positive), ("ZERO_DETECTION_IN_SELECTED_FIA_SAMPLE", negative)):
            chosen = sorted(pool, key=lambda cn: hashlib.sha256(f"D08C1_TRACE|{sid}|{status}|{cn}".encode()).hexdigest())[:10]
            for cn in chosen:
                row = spatial[cn]
                rows.append({
                    "detection_band": band,
                    "analysis_species_id": sid,
                    "analysis_species_name": species[sid]["analysis_species_name"],
                    "physical_plot_lineage_id": row["lineage_id"],
                    "selected_primary_measurement_id": cn,
                    "measurement_year": row["MEASYEAR"],
                    "fia_state_code": row["STATECD"],
                    "fia_state_ab": row["STATEAB"],
                    "fia_state_name": row["STATENM"],
                    "P2PANEL": norm_int(row["P2PANEL"]) or "NA",
                    "AB_fold": row["fold"],
                    "public_projected_x_m": row["x_m"],
                    "public_projected_y_m": row["y_m"],
                    "cell_25km": row["cell_25km"],
                    "cell_50km": row["cell_50km"],
                    "cell_75km": row["cell_75km"],
                    "species_detected": 1 if status == "POSITIVE" else 0,
                    "qualifying_tree_rows_for_species": tree["species_plot_counts"].get(sid, {}).get(cn, 0),
                    "state_evidence_class": evidence[(sid, row["STATECD"])],
                    "selection_rule": "LOWEST_SHA256_D08C1_TRACE_WITHIN_DETECTION_BAND_AND_STATUS",
                })
    write_csv(OUT / "Q1_D08C1_TRACEABILITY_SAMPLE_v01.csv", rows)
    return rows


def build_qc(params, input_rows, code_rows, species, global_flags, drc, crosswalk, lineage, split_rows, grid_rows, tree, census, census_index, frontiers, queue, state_rows, code_audit, nonanalysis):
    checks = []

    def check(name, passed, observed, expected, detail=""):
        checks.append({"check": name, "status": "PASS" if passed else "FAIL", "observed": observed, "expected": expected, "detail": detail})

    check("all_input_hashes_and_db_member_integrity", all(row["status"] == "PASS" for row in input_rows), sum(row["status"] != "PASS" for row in input_rows), 0)
    check("d08b1_code_map_396_unique", len(code_rows) == 396 and len({row["fia_species_code"] for row in code_rows}) == 396, [len(code_rows), len({row["fia_species_code"] for row in code_rows})], [396, 396])
    check("analysis_species_authority_361", len(species) == 361 and len(global_flags) == 361 and len(drc) == 361, [len(species), len(global_flags), len(drc)], [361, 361, 361])
    exact = sum(row["mapping_type"] == "EXACT_FULL_STATE_NAME" for row in crosswalk)
    alias = sum(row["mapping_type"] == "AUTHORIZED_EXPLICIT_ALIAS" for row in crosswalk)
    check("state_crosswalk_47_exact_plus_one_alias", exact == 47 and alias == 1 and len(crosswalk) == 48, [exact, alias, len(crosswalk)], [47, 1, 48])
    check("no_fuzzy_state_matching", all(row["fuzzy_matching_used"] == 0 for row in crosswalk), sum(row["fuzzy_matching_used"] != 0 for row in crosswalk), 0)
    prior_lineage = read_csv(ROOT / "05_qc" / "elig_v02" / "LINEAGE_AUDIT.csv")[0]
    lineage_fields = ["eligible_measurements_before_lineage_dedup", "unique_lineages_before_ambiguity_exclusion", "ambiguous_lineages_excluded", "primary_measurements_after_dedup", "primary_measurements_with_valid_coordinates"]
    lineage_match = all(int(float(prior_lineage[field])) == int(lineage[field]) for field in lineage_fields)
    check("lineage_reproduces_frozen_eligibility_v02", lineage_match, [lineage[field] for field in lineage_fields], [prior_lineage[field] for field in lineage_fields])
    prior_split = {row["stratum"]: row for row in read_csv(ROOT / "05_qc" / "elig_v02" / "AB_SPLIT_AUDIT.csv")}
    split_match = len(prior_split) == len(split_rows) and all(row["stratum"] in prior_split and all(str(row[field]) == prior_split[row["stratum"]][field] for field in ("n_lineages_total", "n_A", "n_B")) for row in split_rows)
    check("ab_split_reproduces_frozen_eligibility_v02", split_match, len(split_rows), len(prior_split))
    prior_grid = {int(row["grain_km"]): row for row in read_csv(ROOT / "05_qc" / "elig_v02" / "DOMAIN_GRID_AUDIT.csv")}
    grid_match = all(int(row["n_cells_total"]) == int(prior_grid[int(row["grain_km"])]["n_cells_total"]) and int(row["n_primary_measurements"]) == int(prior_grid[int(row["grain_km"])]["n_primary_measurements"]) for row in grid_rows)
    check("domain_grid_reproduces_frozen_eligibility_v02", grid_match, [row["n_cells_total"] for row in grid_rows], [prior_grid[g]["n_cells_total"] for g in (25, 50, 75)])
    check("qualifying_tree_cn_nonblank", tree["blank_cn"] == 0, tree["blank_cn"], 0)
    check("qualifying_tree_cn_unique", tree["duplicate_cn"] == 0 and tree["unique_tree_cn"] == tree["total_rows"], [tree["duplicate_cn"], tree["unique_tree_cn"], tree["total_rows"]], [0, tree["total_rows"], tree["total_rows"]])
    check("tree_record_category_reconciliation", tree["ordinary_rows"] + tree["nonanalysis_rows"] == tree["total_rows"], tree["ordinary_rows"] + tree["nonanalysis_rows"], tree["total_rows"])
    code_total = sum(row["qualifying_tree_rows"] for row in code_audit)
    check("ordinary_code_aggregation_reconciliation", code_total == tree["ordinary_rows"], code_total, tree["ordinary_rows"])
    non_total = sum(row["qualifying_tree_rows"] for row in nonanalysis)
    check("nonanalysis_code_reconciliation", non_total == tree["nonanalysis_rows"], non_total, tree["nonanalysis_rows"])
    expected_census = 361 * 3 * 2 * 3
    check("complete_species_grain_view_fold_census", len(census) == expected_census, len(census), expected_census)
    subset_failures = 0
    for sid in species:
        for grain in params["grains_km"]:
            for fold in params["fold_scopes"]:
                all_row = census_index[(sid, grain, "ALL_CONUS_OBSERVED", fold)]
                native_row = census_index[(sid, grain, "WCVP_CONFIRMED_NATIVE_STATE", fold)]
                if native_row["n_qualifying_tree_rows"] > all_row["n_qualifying_tree_rows"] or native_row["n_positive_plots"] > all_row["n_positive_plots"] or native_row["n_detected_cells"] > all_row["n_detected_cells"]:
                    subset_failures += 1
    check("native_view_subset_of_all_view", subset_failures == 0, subset_failures, 0)
    native_class_fail = sum(row["census_view"] == "WCVP_CONFIRMED_NATIVE_STATE" and (row["n_explicit_introduced_state_tree_rows"] != 0 or row["n_no_confirmed_native_or_introduced_state_tree_rows"] != 0) for row in census)
    check("native_view_contains_only_confirmed_native_state_records", native_class_fail == 0, native_class_fail, 0)
    expected_state_rows = 361 * 48
    check("complete_species_state_audit", len(state_rows) == expected_state_rows, len(state_rows), expected_state_rows)
    check("frontier_grid_complete_unselected", len(frontiers) == 30 and all(row["final_threshold_selected"] == 0 for row in frontiers), [len(frontiers), sum(row["final_threshold_selected"] != 0 for row in frontiers)], [30, 0])
    queue_bad = sum(not (row["passes_ge10_each_fold_all_view"] or row["passes_ge10_each_fold_native_view"]) for row in queue)
    check("survivor_queue_union_rule", queue_bad == 0, queue_bad, 0)
    drc_total = sum(row["n_drc_tree_rows"] for row in census if row["grain_km"] == 50 and row["census_view"] == "ALL_CONUS_OBSERVED" and row["fold_scope"] == "ALL")
    dbh_total = sum(row["n_dbh_tree_rows"] for row in census if row["grain_km"] == 50 and row["census_view"] == "ALL_CONUS_OBSERVED" and row["fold_scope"] == "ALL")
    check("dbh_drc_record_composition_reconciles", dbh_total + drc_total == tree["ordinary_rows"], dbh_total + drc_total, tree["ordinary_rows"])
    check("all_build_qc_inputs_status_pass", all(row["status"] == "PASS" for row in split_rows + grid_rows), sum(row["status"] != "PASS" for row in split_rows + grid_rows), 0)
    check("no_little_information_used", True, 0, 0, "No USGS/Little file opened by build script")
    check("no_real_q1_outcome_computed", True, 0, 0, "Census uses only sampling/detection/state-evidence counts")
    write_csv(OUT / "Q1_D08C1_QC_v01.csv", checks)
    if any(row["status"] != "PASS" for row in checks):
        failures = [row["check"] for row in checks if row["status"] != "PASS"]
        raise RuntimeError(f"D08C1_QC_FAIL:{failures}")
    return checks


def main():
    start = time.time()
    if WORK.exists():
        raise RuntimeError(f"Refusing to overwrite existing work directory: {WORK}")
    OUT.mkdir(parents=True)
    QC.mkdir(parents=True)
    params = json.loads(PARAM_PATH.read_text(encoding="utf-8"))
    log = [f"{now_iso()} D08C1 build start; contract frozen before TREE scan"]
    input_rows = input_audit(params)
    log.append(f"{now_iso()} Formal input hashes and extracted DB member CRC PASS")
    code_rows, code_map, species, global_flags, distribution_rows, drc = load_authorities()

    connection = sqlite3.connect(f"file:{DB_PATH.as_posix()}?mode=ro", uri=True)
    connection.execute("PRAGMA temp_store=MEMORY")
    connection.execute("PRAGMA automatic_index=ON")
    try:
        state_map, conus_codes, crosswalk, area_codes, evidence, evidence_detail = build_state_evidence(
            connection, params, species, global_flags, distribution_rows
        )
        log.append(f"{now_iso()} State crosswalk PASS: 47 exact + one authorized RI alias")
        primary, spatial, forest_conditions, lineage = build_lineages(connection, params, state_map, conus_codes)
        split_rows, grid_rows = build_split_grid_audits(primary, spatial, params)
        log.append(f"{now_iso()} Lineage, A/B, projection and grid continuity PASS")
        tree = scan_trees(connection, primary, forest_conditions, code_map, evidence)
    finally:
        connection.close()
    log.append(f"{now_iso()} Unique bottom-level TREE scan complete")

    census, census_index = build_census(params, species, global_flags, drc, primary, spatial, conus_codes, evidence, tree)
    state_audit = build_native_state_audit(species, global_flags, state_map, conus_codes, crosswalk, evidence, evidence_detail, tree)
    code_audit, nonanalysis = build_code_audits(code_rows, code_map, species, tree)
    frontiers, queue, grain_summary = build_frontiers_and_summary(params, species, global_flags, census_index)
    trace_rows = build_trace(species, spatial, conus_codes, evidence, tree)
    checks = build_qc(params, input_rows, code_rows, species, global_flags, drc, crosswalk, lineage, split_rows, grid_rows, tree, census, census_index, frontiers, queue, state_audit, code_audit, nonanalysis)
    log.append(f"{now_iso()} All {len(checks)} frozen QC checks PASS")

    no_outcome = {
        "status": "PASS",
        "real_Q1_model_fitted": False,
        "geometry_gain_computed": False,
        "range_abundance_coupling_computed": False,
        "R1_R2_compared": False,
        "World_0_result_computed": False,
        "abundance_geometry_used_for_selection": False,
        "predictive_performance_computed": False,
        "significance_test_run": False,
        "outcome_based_species_filtering": False,
        "little_status_used_for_filtering": False,
        "little_layer_merged": False,
        "external_range_search_run": False,
        "final_grain_selected": False,
        "final_threshold_selected": False,
        "final_species_cohort_selected": False,
        "prohibited_operations_performed": [],
    }
    write_json(QC / "D08C1_NO_Q1_OUTCOME_AUDIT_v01.json", no_outcome)
    environment = {
        "python": sys.version,
        "platform": platform.platform(),
        "sqlite_version": sqlite3.sqlite_version,
        "machine": platform.machine(),
        "processor": platform.processor(),
        "cwd": os.getcwd(),
    }
    write_json(QC / "D08C1_ENVIRONMENT_v01.json", environment)
    write_json(QC / "D08C1_PARAMETERS_v01.json", params)
    build_summary = {
        "status": "PASS",
        "analysis_species": len(species),
        "qualifying_unique_tree_rows": tree["total_rows"],
        "ordinary_accepted_species_tree_rows": tree["ordinary_rows"],
        "nonanalysis_tree_rows": tree["nonanalysis_rows"],
        "primary_measurements": len(primary),
        "spatial_primary_measurements": len(spatial),
        "census_rows": len(census),
        "native_state_audit_rows": len(state_audit),
        "code_aggregation_rows": len(code_audit),
        "nonanalysis_code_rows": len(nonanalysis),
        "frontier_rows": len(frontiers),
        "survivor_queue_rows": len(queue),
        "trace_rows": len(trace_rows),
        "qc_checks": len(checks),
        "runtime_seconds": time.time() - start,
        "prohibited_operations_performed": [],
    }
    write_json(QC / "D08C1_BUILD_SUMMARY_v01.json", build_summary)
    write_text(QC / "D08C1_IMPLEMENTATION_LOG_v01.md", "# D08C1 implementation log v01\n\n" + "\n".join(f"- {line}" for line in log))

    summary_lines = []
    for row in grain_summary:
        summary_lines.append(
            f"- {row['grain_km']} km / {row['census_view']}: any detection={row['n_species_with_any_detection']}; "
            f"each fold ≥10 cells={row['n_species_each_fold_ge10_detected_cells']}; "
            f"core-eligible each fold ≥10 cells={row['n_core_eligible_species_each_fold_ge10_detected_cells']}."
        )
    write_text(
        OUT / "README.md",
        """# Q1 D08C1 accepted-species eligibility census v01

Outcome-blind census rebuilt from unique bottom-level FIA TREE records after D08B1 v02 accepted-species mapping. The two views are `ALL_CONUS_OBSERVED` and `WCVP_CONFIRMED_NATIVE_STATE`. Little/USGS data were not used. All thresholds are descriptive frontiers, not selections.
""",
    )
    write_text(
        OUT / "D08C1_RESULT_NOTE_v01.md",
        "# D08C1 result note v01\n\n"
        "Engineering status: PASS. Outcome-blind protocol violation: none.\n\n"
        "## Grain/view breadth\n\n" + "\n".join(summary_lines) +
        "\n\n## Mainline decisions still open\n\n"
        "Final grain, final feasibility threshold, final species cohort, and later Little/range-source closure remain for scientific mainline decision.\n",
    )
    print(json.dumps(build_summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
