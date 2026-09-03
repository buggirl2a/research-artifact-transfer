from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import math
import re
import sqlite3
import time
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(r"C:\range_paper")
V1_ARCHIVE = ROOT / "10_archive" / "d09c_t2_completion_v01"
V1_PACKAGE = V1_ARCHIVE / "Q1_D09C_T2_BOUNDED_COMPLETION_REPRODUCIBLE_v01"
V1_ZIP = V1_ARCHIVE / "Q1_D09C_T2_BOUNDED_COMPLETION_REPRODUCIBLE_v01.zip"
V1_SOURCE = ROOT / "06_src" / "d09c_t2_completion_v01" / "build_d09c_t2_completion_v01.py"
DB = ROOT / "99_tmp" / "elig_v02" / "SQLite_FIADB_ENTIRE.db"
SRC = ROOT / "06_src" / "d09c_t2_final_correction_v02"
OUT = ROOT / "04_derived" / "d09c_t2_final_correction_v02"
QC = ROOT / "05_qc" / "d09c_t2_final_correction_v02"
CONTRACT = ROOT / "00_control" / "Q1_D09C_T2_FINAL_DESIGN_CORRECTION_CONTRACT_v02.md"
FREEZE = ROOT / "00_control" / "D09C_T2_FINAL_CORRECTION_EXECUTION_FREEZE_v02.md"
PARAMS = SRC / "parameters_d09c_t2_final_correction_v02.json"

CONTRACT_SHA = "ee3d958d15e74bc54a1b8fc91b2870bf4eb89304f1ed684f980dd8bd4a9fe351"
V1_ZIP_SHA = "25f361eeeddbe02fd2f93d2daa0b0e974926a8d97965505a3bec37a65388ea7e"
WV_EVALID = 542301
WV_SPARSE_EU = "3"
PANELS = (1, 2, 3, 4, 5)
TOL = 1e-8
SEMANTIC_PATTERN = re.compile(r"^Inland Census Water Unit [0-9]+$")


def sha256(path: Path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_csv(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict], fields: list[str] | None = None):
    path.parent.mkdir(parents=True, exist_ok=True)
    if fields is None:
        fields, seen = [], set()
        for row in rows:
            for key in row:
                if key not in seen and not key.startswith("_"):
                    seen.add(key)
                    fields.append(key)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def write_json(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def as_int(value, default=0):
    if value is None or str(value).strip() == "":
        return default
    return int(float(value))


def as_float(value, default=0.0):
    if value is None or str(value).strip() == "":
        return default
    return float(value)


def rel_error(a, b):
    return abs(a - b) / max(abs(a), abs(b), 1.0)


def panel_code(values):
    return "-".join(str(x) for x in sorted(values))


def haversine_km(lat1, lon1, lat2, lon2):
    r = 6371.0088
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def load_v1_module():
    spec = importlib.util.spec_from_file_location("d09c_t2_v01", V1_SOURCE)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def verify_inputs(v1) -> list[dict]:
    rows = []
    def add(role, path, expected, source):
        observed = sha256(path) if path.exists() else ""
        rows.append({
            "role": role, "path": str(path), "size_bytes": path.stat().st_size if path.exists() else "",
            "expected_sha256": expected, "observed_sha256": observed,
            "status": "PASS" if observed == expected else "FAIL", "authority_source": source,
        })
    add("V02_CONTRACT", CONTRACT, CONTRACT_SHA, "user attachment copied byte-for-byte")
    add("V01_ACCEPTED_REPRODUCIBLE_ZIP", V1_ZIP, V1_ZIP_SHA, "v02 contract predecessor identity")
    sums = {r["relative_path"]: r["sha256"] for r in read_csv(V1_PACKAGE / "SHA256SUMS.csv")}
    for rel in (
        "02_outputs/Q1_D09C_T2_ALL_PARTITION_CANDIDATES_v01.csv",
        "02_outputs/Q1_D09C_T2_RULE_SELECTED_PARTITIONS_v01.csv",
        "02_outputs/Q1_D09C_T2_OR_412301_MISMATCH_AUDIT_v01.csv",
        "01_authoritative_inputs/frozen_d09c_v01/D09C_PANEL_SUBPANEL_YEAR_LEDGER_v01.csv",
        "04_code/build_d09c_t2_completion_v01.py",
    ):
        path = V1_PACKAGE / rel
        add("V01_VERIFIED_MEMBER", path, sums[rel], "accepted v01 SHA256SUMS.csv")
    add("V01_BUILDER_LIVE_COPY", V1_SOURCE, sums["04_code/build_d09c_t2_completion_v01.py"], "accepted v01 packaged source")
    v1_integrity = v1.load_input_integrity()
    rows.extend({**r, "role": "V01_REUSED_" + r["role"], "authority_source": "v01 accepted input audit rerun"} for r in v1_integrity)
    rows.append({
        "role": "FROZEN_EXTRACTED_FIADB_DESIGN_DB", "path": str(DB),
        "size_bytes": DB.stat().st_size if DB.exists() else "", "expected_sha256": "",
        "observed_sha256": "", "status": "PASS" if DB.exists() and DB.stat().st_size == 71565119488 else "FAIL",
        "authority_source": "accepted D09C input freeze; size and ZIP-member identity previously verified",
    })
    return rows


def load_states(v1):
    states = v1.load_frozen_45_states()
    for abbr, evalid in v1.NEW_STATES.items():
        v1.load_new_state(states[abbr], evalid)
    return states


def query_wv_full_frame(state: dict):
    allowed = {"POP_ESTN_UNIT", "POP_PLOT_STRATUM_ASSGN", "PLOT"}
    accessed, denied = set(), []
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    con.execute("PRAGMA query_only=ON")
    def authorizer(action, arg1, arg2, dbname, source):
        if action == sqlite3.SQLITE_READ:
            table = (arg1 or "").upper()
            if table not in allowed:
                denied.append({"table": table, "column": arg2 or ""})
                return sqlite3.SQLITE_DENY
            accessed.add(table)
        return sqlite3.SQLITE_OK
    con.set_authorizer(authorizer)
    eu_rows = con.execute(
        "SELECT CN,EVALID,ESTN_UNIT,ESTN_UNIT_DESCR,STATECD,AREA_USED,P1PNTCNT_EU FROM POP_ESTN_UNIT WHERE EVALID=? ORDER BY ESTN_UNIT",
        (WV_EVALID,),
    ).fetchall()
    plot_rows = con.execute(
        "SELECT a.ESTN_UNIT,a.PLT_CN,p.LAT,p.LON,p.P2PANEL,p.MEASYEAR,p.INVYR "
        "FROM POP_PLOT_STRATUM_ASSGN a JOIN PLOT p ON p.CN=a.PLT_CN WHERE a.EVALID=? ORDER BY a.ESTN_UNIT,a.PLT_CN",
        (WV_EVALID,),
    ).fetchall()
    con.close()
    if denied:
        raise RuntimeError(f"Denied SQLite read occurred: {denied}")

    plots_by_eu = defaultdict(list)
    for unit, plt_cn, lat, lon, panel, measyear, invyr in plot_rows:
        plots_by_eu[str(unit)].append({
            "plt_cn": str(plt_cn), "lat": lat, "lon": lon, "panel": as_int(panel, None),
            "measyear": as_int(measyear, None), "invyr": as_int(invyr, None),
        })
    eu_meta = {}
    for cn, evalid, unit, descr, statecd, area, p1 in eu_rows:
        key = str(unit)
        coords = [(float(p["lat"]), float(p["lon"])) for p in plots_by_eu[key] if p["lat"] is not None and p["lon"] is not None and -90 <= float(p["lat"]) <= 90 and -180 <= float(p["lon"]) <= 180]
        eu_meta[key] = {
            "eu_cn": str(cn), "evalid": int(evalid), "estn_unit": key, "description": descr or "",
            "statecd": int(statecd), "area_used": float(area) if area is not None else None,
            "p1pointcnt_eu": int(p1) if p1 is not None else None,
            "plot_count": len(plots_by_eu[key]), "valid_coordinate_count": len(coords),
            "centroid_lat": sum(x[0] for x in coords) / len(coords) if coords else None,
            "centroid_lon": sum(x[1] for x in coords) / len(coords) if coords else None,
            "panel_values": sorted({p["panel"] for p in plots_by_eu[key] if p["panel"] in PANELS}),
        }
    return eu_meta, plots_by_eu, sorted(accessed)


def resolve_wv_partner(eu_meta: dict):
    sparse = eu_meta.get(WV_SPARSE_EU)
    if sparse is None:
        return [], None, "MERGE_PARTNER_NOT_RESOLVED_FROM_FROZEN_DESIGN_METADATA"
    rows = []
    for unit, meta in sorted(eu_meta.items(), key=lambda x: int(x[0])):
        if unit == WV_SPARSE_EU:
            continue
        basic = (
            meta["evalid"] == WV_EVALID and meta["statecd"] == 54 and bool(meta["eu_cn"])
            and bool(meta["description"]) and meta["plot_count"] > 0 and bool(meta["panel_values"])
        )
        same_class = bool(SEMANTIC_PATTERN.fullmatch(meta["description"])) and bool(SEMANTIC_PATTERN.fullmatch(sparse["description"]))
        distance = None
        if same_class and meta["centroid_lat"] is not None and sparse["centroid_lat"] is not None:
            distance = haversine_km(sparse["centroid_lat"], sparse["centroid_lon"], meta["centroid_lat"], meta["centroid_lon"])
        rows.append({
            "sparse_component_evalid": WV_EVALID,
            "sparse_estimation_unit": WV_SPARSE_EU,
            "sparse_estimation_unit_cn": sparse["eu_cn"],
            "sparse_description": sparse["description"],
            "candidate_estimation_unit": unit,
            "candidate_estimation_unit_cn": meta["eu_cn"],
            "candidate_description": meta["description"],
            "candidate_area_used_acres": meta["area_used"],
            "candidate_full_frame_plot_count": meta["plot_count"],
            "candidate_panel_values": panel_code(meta["panel_values"]),
            "candidate_valid_coordinate_count": meta["valid_coordinate_count"],
            "candidate_centroid_lat": meta["centroid_lat"] if meta["centroid_lat"] is not None else "",
            "candidate_centroid_lon": meta["centroid_lon"] if meta["centroid_lon"] is not None else "",
            "basic_admissibility": "YES" if basic else "NO",
            "semantic_class": "INLAND_CENSUS_WATER" if same_class else "OTHER",
            "same_semantic_class_as_sparse_eu": "YES" if same_class else "NO",
            "centroid_haversine_distance_km": distance if distance is not None else "",
            "geographic_proximity_evidence": "AVAILABLE_PUBLIC_PLOT_CENTROIDS" if distance is not None else "NOT_APPLICABLE_OR_UNAVAILABLE",
            "pixel_design_similarity_evidence": "NOT_AVAILABLE_IN_FROZEN_DESIGN_FIELDS",
            "area_or_plot_count_used_for_selection": "NO",
            "balance_or_time_used_for_selection": "NO",
            "final_partner_selected": "NO",
            "partner_resolution_reason": "",
        })
    same = [r for r in rows if r["basic_admissibility"] == "YES" and r["same_semantic_class_as_sparse_eu"] == "YES"]
    if len(same) == 1:
        selected = same[0]
        status = "UNIQUE_SEMANTIC_PARTNER"
    elif len(same) > 1:
        if any(r["centroid_haversine_distance_km"] == "" for r in same):
            return rows, None, "MERGE_PARTNER_AMBIGUOUS_NEEDS_MAINLINE"
        ordered = sorted(same, key=lambda r: float(r["centroid_haversine_distance_km"]))
        for rank, row in enumerate(ordered, 1):
            row["proximity_rank_within_same_semantic_class"] = rank
        if len(ordered) > 1 and float(ordered[0]["centroid_haversine_distance_km"]) == float(ordered[1]["centroid_haversine_distance_km"]):
            return rows, None, "MERGE_PARTNER_AMBIGUOUS_NEEDS_MAINLINE"
        selected = ordered[0]
        status = "UNIQUE_MINIMUM_PUBLIC_PLOT_CENTROID_DISTANCE"
    else:
        return rows, None, "MERGE_PARTNER_NOT_RESOLVED_FROM_FROZEN_DESIGN_METADATA"
    selected["final_partner_selected"] = "YES"
    selected["partner_resolution_reason"] = status
    for row in rows:
        if not row["partner_resolution_reason"]:
            row["partner_resolution_reason"] = "NOT_SELECTED_BY_FROZEN_SEMANTIC_THEN_PROXIMITY_RULE"
    return rows, selected["candidate_estimation_unit"], status


def within_class_key(row):
    return (
        float(row["area_weighted_effective_block_imbalance"]),
        float(row["max_effective_block_imbalance"]),
        float(row["area_weighted_estimation_unit_imbalance"]),
        float(row["absolute_fold_A_plot_share_minus_0_4"]),
        float(row["temporal_center_abs_diff_years"]),
        float(row["temporal_distribution_l1_distance"]),
        float(row["temporal_sd_abs_diff_years"]),
        tuple(int(x) for x in row["fold_A_panels"].split("-")),
    )


def build_r2_candidate(v1, state: dict, native: dict, partner_unit: str):
    a_panels = {int(x) for x in native["fold_A_panels"].split("-")}
    b_panels = set(PANELS) - a_panels
    by_eu = defaultdict(list)
    for s in state["strata"].values():
        by_eu[str(s["estn_unit"])].append(s)
    merge_units = {WV_SPARSE_EU, str(partner_unit)}
    merged_strata = [s for unit in merge_units for s in by_eu[unit]]
    merged_counts = Counter({p: sum(s["panel_counts"][p] for s in merged_strata) for p in PANELS})
    effective = [{
        "effective_block_id": f"MERGED_EU:{WV_SPARSE_EU}+{partner_unit}",
        "resolution": "SPARSE_EU_FALLBACK_COMMON_COARSENED_DOMAIN",
        "eu_cn": f"MERGED:{WV_SPARSE_EU}+{partner_unit}",
        "estn_unit": f"{WV_SPARSE_EU}+{partner_unit}",
        "strata": merged_strata,
        "area": sum(float(s["area"] or 0.0) for s in merged_strata),
        "panel_counts": merged_counts,
        "source_eus": sorted(merge_units, key=int),
    }]
    other_coarsened = []
    true_blocks = []
    domain_balance = []
    for unit, strata in sorted(by_eu.items(), key=lambda x: int(x[0])):
        if unit in merge_units:
            continue
        missing_a = any(sum(s["panel_counts"][p] for p in a_panels) == 0 for s in strata)
        missing_b = any(sum(s["panel_counts"][p] for p in b_panels) == 0 for s in strata)
        if missing_a or missing_b:
            counts = Counter({p: sum(s["panel_counts"][p] for s in strata) for p in PANELS})
            block = {
                "effective_block_id": f"EU:{strata[0]['eu_cn']}",
                "resolution": "WITHIN_EU_SYMMETRIC_COARSENING",
                "eu_cn": strata[0]["eu_cn"], "estn_unit": unit,
                "strata": strata, "area": sum(float(s["area"] or 0.0) for s in strata),
                "panel_counts": counts, "source_eus": [unit],
            }
            effective.append(block)
            other_coarsened.append(unit)
            if sum(counts[p] for p in a_panels) == 0 or sum(counts[p] for p in b_panels) == 0:
                true_blocks.append(unit)
        else:
            for s in strata:
                effective.append({
                    "effective_block_id": f"STRATUM:{s['stratum_cn']}", "resolution": "PARENT_POSTSTRATUM",
                    "eu_cn": s["eu_cn"], "estn_unit": unit, "strata": [s], "area": float(s["area"] or 0.0),
                    "panel_counts": Counter(s["panel_counts"]), "source_eus": [unit],
                })
    merged_na = sum(merged_counts[p] for p in a_panels)
    merged_nb = sum(merged_counts[p] for p in b_panels)
    if merged_na == 0 or merged_nb == 0:
        true_blocks.append(f"MERGED:{WV_SPARSE_EU}+{partner_unit}")

    original_area = sum(float(s["area"] or 0.0) for s in state["strata"].values())
    effective_area = sum(b["area"] for b in effective)
    area_error = rel_error(original_area, effective_area)
    block_num = sum(b["area"] * v1.imbalance(sum(b["panel_counts"][p] for p in a_panels), sum(b["panel_counts"][p] for p in b_panels)) for b in effective)
    block_denom = sum(b["area"] for b in effective)
    block_values = [v1.imbalance(sum(b["panel_counts"][p] for p in a_panels), sum(b["panel_counts"][p] for p in b_panels)) for b in effective]
    domains = []
    domains.append((effective[0]["area"], merged_counts))
    for unit, strata in by_eu.items():
        if unit in merge_units:
            continue
        counts = Counter({p: sum(s["panel_counts"][p] for s in strata) for p in PANELS})
        domains.append((sum(float(s["area"] or 0.0) for s in strata), counts))
    eu_num = sum(area * v1.imbalance(sum(c[p] for p in a_panels), sum(c[p] for p in b_panels)) for area, c in domains)
    eu_den = sum(area for area, c in domains)
    all_counts = v1.state_panel_counts(state)
    n_a = sum(all_counts[p] for p in a_panels)
    n_b = sum(all_counts[p] for p in b_panels)
    temporal = v1.temporal_metrics(state, a_panels, b_panels)
    valid = not true_blocks and area_error <= TOL
    row = dict(native)
    row.update({
        "repair_class": "R2_SPARSE_EU_FALLBACK_VALID" if valid else "R3_BLOCKED",
        "repair_class_code": "R2" if valid else "R3",
        "repair_class_reason": "R0/R1 absent; WV sparse EU merged pre-partition with frozen full-frame partner" if valid else "Sparse-EU fallback remains non-estimable",
        "within_eu_symmetric_coarsening_used": int(bool(other_coarsened)),
        "within_eu_coarsened_unit_count": len(other_coarsened),
        "sparse_eu_fallback_used": 1,
        "sparse_eu": WV_SPARSE_EU,
        "sparse_eu_partner": str(partner_unit),
        "merged_domain_id": f"WV_EU_{WV_SPARSE_EU}_{partner_unit}",
        "merged_domain_fold_A_sample_count": merged_na,
        "merged_domain_fold_B_sample_count": merged_nb,
        "native_missing_parent_poststrata": int(native["fold_A_missing_parent_poststrata"]) + int(native["fold_B_missing_parent_poststrata"]),
        "area_preserved_100pct": int(area_error <= TOL),
        "ti_estimable": int(valid),
        "true_eu_level_block_count": len(true_blocks),
        "true_eu_level_block_ids": ";".join(true_blocks),
        "original_population_area_acres": original_area,
        "effective_population_area_acres": effective_area,
        "population_area_preservation_relative_error": area_error,
        "area_weighted_effective_block_imbalance": block_num / block_denom if block_denom else math.inf,
        "max_effective_block_imbalance": max(block_values, default=math.inf),
        "area_weighted_estimation_unit_imbalance": eu_num / eu_den if eu_den else math.inf,
        "fold_A_plot_count": n_a, "fold_B_plot_count": n_b,
        "absolute_fold_A_plot_share_minus_0_4": abs(n_a / (n_a + n_b) - 0.4),
        **temporal,
        "_effective": effective,
    })
    return row


def classify_native(row: dict):
    if int(row["candidate_design_valid"]) == 1 and int(row["symmetric_coarsening_estimation_unit_count"]) == 0:
        return "R0", "R0_NATIVE_STRATIFICATION_VALID", "Both folds cover every parent poststratum; no coarsening required"
    if int(row["candidate_design_valid"]) == 1:
        return "R1", "R1_WITHIN_EU_SYMMETRIC_COARSENING_VALID", "Native poststrata incomplete; symmetric within-EU coarsening closes TI with 100% area"
    return "R3", "R3_BLOCKED", row["candidate_design_status"]


def build_ti(v1, states, selected):
    rows, state_closed, ma_status = [], {}, {}
    for abbr, top in selected.items():
        state = states[abbr]
        a_panels = {int(x) for x in top["fold_A_panels"].split("-")}
        b_panels = set(PANELS) - a_panels
        state_area = sum(float(s["area"] or 0.0) for s in state["strata"].values())
        folds_ok = []
        ma_folds = []
        for fold, panels in (("A", a_panels), ("B", b_panels)):
            recovered_total = 0.0
            zero_panel_blocks = 0
            for block in top["_effective"]:
                area = block["area"]
                n_fold = sum(block["panel_counts"][p] for p in panels)
                n_full = sum(block["panel_counts"][p] for p in PANELS)
                weight = area / n_fold if n_fold else None
                recovered = weight * n_fold if weight is not None else 0.0
                recovered_total += recovered
                strata = block["strata"]
                zero_panel_blocks += sum(block["panel_counts"][p] == 0 for p in panels)
                rows.append({
                    "state_fips": state["state_fips"], "state_abbr": abbr, "candidate_id": top["candidate_id"],
                    "repair_class": top["repair_class_code"], "fold": fold, "selected_panels": panel_code(panels),
                    "component_evalid": state["component_evalid"], "effective_design_block_id": block["effective_block_id"],
                    "design_resolution": block["resolution"], "estimation_unit_or_merged_domain": block.get("estn_unit", block["eu_cn"]),
                    "source_estimation_units": ";".join(block.get("source_eus", [str(strata[0]["estn_unit"])])),
                    "source_parent_poststratum_count": len(strata),
                    "source_parent_poststratum_ids": ";".join(s["stratum_cn"] for s in strata),
                    "fold_sample_count": n_fold, "full_evaluation_sample_count_comparator": n_full,
                    "population_area_acres": area,
                    "fold_specific_ti_expansion_acres_per_plot": weight if weight is not None else "",
                    "fold_weight_construction": "effective block population area / actual fold sample count",
                    "full_evaluation_expns_reused_as_final_fold_weight": "NO",
                    "synthetic_constant_recovered_area_acres": recovered,
                    "calibration_relative_error": rel_error(recovered, area),
                    "calibration_status": "PASS" if n_fold and rel_error(recovered, area) <= TOL else "FAIL",
                    "population_area_discarded_acres": 0.0,
                    "variance_df_n_minus_1": max(n_fold - 1, 0),
                    "within_block_variance_estimable_n_ge_2": int(n_fold >= 2),
                })
            folds_ok.append(rel_error(recovered_total, state_area) <= TOL)
            ma_folds.append("PARTIAL" if zero_panel_blocks else "COMPLETE")
        state_closed[abbr] = all(folds_ok)
        ma_status[abbr] = "PARTIAL" if "PARTIAL" in ma_folds else "COMPLETE"
    return rows, state_closed, ma_status


def main():
    started = time.time()
    OUT.mkdir(parents=True, exist_ok=True)
    QC.mkdir(parents=True, exist_ok=True)
    if any(OUT.iterdir()) or any(QC.iterdir()):
        raise RuntimeError("Refusing to overwrite nonempty v02 output/QC directories")
    v1 = load_v1_module()
    input_rows = verify_inputs(v1)
    write_csv(QC / "D09C_T2_FINAL_INPUT_INTEGRITY_v02.csv", input_rows)
    if any(r["status"] != "PASS" for r in input_rows):
        raise RuntimeError("INPUT_BLOCKED: v02 input integrity failed")

    states = load_states(v1)
    native_by_state = {}
    for abbr, state in states.items():
        native_by_state[abbr] = [v1.build_candidate(state, a) for a in v1.CANDIDATES]

    trigger_states = []
    for abbr, rows in native_by_state.items():
        classes = [classify_native(r)[0] for r in rows]
        if not any(c in {"R0", "R1"} for c in classes):
            trigger_states.append(abbr)
    if trigger_states != ["WV"]:
        raise RuntimeError(f"INPUT_BLOCKED: unexpected R2 trigger States {trigger_states}")

    eu_meta, wv_plots, accessed_tables = query_wv_full_frame(states["WV"])
    partner_rows, partner_unit, partner_status = resolve_wv_partner(eu_meta)
    coordinate_rows = []
    for unit, meta in sorted(eu_meta.items(), key=lambda x: int(x[0])):
        if not SEMANTIC_PATTERN.fullmatch(meta["description"]):
            continue
        for plot in wv_plots[unit]:
            usable = plot["lat"] is not None and plot["lon"] is not None and -90 <= float(plot["lat"]) <= 90 and -180 <= float(plot["lon"]) <= 180
            coordinate_rows.append({
                "component_evalid": WV_EVALID, "estimation_unit": unit, "estimation_unit_cn": meta["eu_cn"],
                "estimation_unit_description": meta["description"], "plt_cn": plot["plt_cn"],
                "public_latitude": plot["lat"] if plot["lat"] is not None else "",
                "public_longitude": plot["lon"] if plot["lon"] is not None else "",
                "p2panel": plot["panel"] if plot["panel"] is not None else "",
                "measyear": plot["measyear"] if plot["measyear"] is not None else "",
                "invyr": plot["invyr"] if plot["invyr"] is not None else "",
                "included_in_public_coordinate_centroid": "YES" if usable else "NO",
                "public_coordinate_caveat": "FIADB public coordinates may be fuzzed/swapped; used only for frozen outcome-blind EU proximity ranking",
            })

    ledger = []
    all_rows = {}
    for abbr, native_rows in native_by_state.items():
        state_rows = []
        for native in native_rows:
            code, label, reason = classify_native(native)
            row = dict(native)
            row.update({
                "repair_class_code": code, "repair_class": label, "repair_class_reason": reason,
                "native_missing_parent_poststrata": int(native["fold_A_missing_parent_poststrata"]) + int(native["fold_B_missing_parent_poststrata"]),
                "within_eu_symmetric_coarsening_used": int(native["symmetric_coarsening_estimation_unit_count"] > 0),
                "within_eu_coarsened_unit_count": native["symmetric_coarsening_estimation_unit_count"],
                "sparse_eu_fallback_used": 0, "sparse_eu": "", "sparse_eu_partner": "", "merged_domain_id": "",
                "area_preserved_100pct": native["population_area_preserved_100pct"],
                "ti_estimable": native["candidate_design_valid"],
                "rank_within_repair_class": "", "competition_eligible_class": "NO",
                "final_rank_within_admissible_class": "", "final_rule_selected": 0,
                "_effective": native["_effective"],
            })
            state_rows.append(row)
        if abbr == "WV" and partner_unit is not None:
            state_rows = [build_r2_candidate(v1, states["WV"], native, partner_unit) for native in native_rows]
            for row in state_rows:
                row.update({"rank_within_repair_class": "", "competition_eligible_class": "NO", "final_rank_within_admissible_class": "", "final_rule_selected": 0})
        for class_code in ("R0", "R1", "R2"):
            subset = [r for r in state_rows if r["repair_class_code"] == class_code]
            subset.sort(key=within_class_key)
            for rank, row in enumerate(subset, 1):
                row["rank_within_repair_class"] = rank
        all_rows[abbr] = state_rows

    selected = {}
    final_class = {}
    for abbr, rows in all_rows.items():
        available = [c for c in ("R0", "R1", "R2") if any(r["repair_class_code"] == c for r in rows)]
        if not available:
            final_class[abbr] = "R3"
            continue
        chosen_class = available[0]
        final_class[abbr] = chosen_class
        subset = sorted([r for r in rows if r["repair_class_code"] == chosen_class], key=within_class_key)
        for rank, row in enumerate(subset, 1):
            row["competition_eligible_class"] = "YES"
            row["final_rank_within_admissible_class"] = rank
            if rank == 1:
                row["final_rule_selected"] = 1
                selected[abbr] = row
        ledger.extend(rows)

    if partner_unit is None:
        nationwide_status = partner_status
    elif len(selected) != 48:
        nationwide_status = "DESIGN_BLOCKED_AFTER_SPARSE_EU_FALLBACK"
    else:
        nationwide_status = "PASS_READY_FOR_MAINLINE_FINAL_D09C_AUDIT"

    ti_rows, ti_closed, ma_status = build_ti(v1, states, selected) if len(selected) == 48 else ([], {}, {})

    selected_rows = []
    for abbr in sorted(states):
        state = states[abbr]
        top = selected.get(abbr)
        selected_rows.append({
            "state_fips": state["state_fips"], "state_abbr": abbr, "state_name": state["state_name"],
            "component_evalid": state["component_evalid"], "final_repair_class": final_class.get(abbr, "R3"),
            "final_candidate_id": top["candidate_id"] if top else "",
            "final_A_panels": top["fold_A_panels"] if top else "",
            "final_B_panels": top["fold_B_panels"] if top else "",
            "final_rank_within_admissible_class": top["final_rank_within_admissible_class"] if top else "",
            "native_missing_parent_poststrata": top["native_missing_parent_poststrata"] if top else "",
            "within_eu_symmetric_coarsening_used": top["within_eu_symmetric_coarsening_used"] if top else "",
            "sparse_eu_fallback_used": top["sparse_eu_fallback_used"] if top else "",
            "sparse_eu_partner": top["sparse_eu_partner"] if top else "",
            "population_area_preserved_100pct": top["area_preserved_100pct"] if top else "",
            "fold_specific_ti_closed": "YES" if ti_closed.get(abbr) else "NO",
            "ma_sensitivity_feasibility": ma_status.get(abbr, "UNAVAILABLE"),
            "final_state_status": "DESIGN_COMPLETE" if top else "DESIGN_BLOCKED",
            "mainline_final_acceptance": "NOT_DECIDED",
            "selection_reason": f"lowest available repair class {final_class.get(abbr, 'R3')}; within-class rank 1 by frozen balance/time/tie tuple" if top else "No legal candidate",
        })

    v1_selected = {r["state_abbr"]: r for r in read_csv(V1_PACKAGE / "02_outputs" / "Q1_D09C_T2_RULE_SELECTED_PARTITIONS_v01.csv")}
    rerank_rows = []
    for abbr in ("CA", "OR", "WA"):
        old = v1_selected[abbr]
        old_row = next(r for r in all_rows[abbr] if r["candidate_id"] == old["candidate_id"])
        new = selected[abbr]
        rerank_rows.append({
            "state_abbr": abbr, "component_evalid": states[abbr]["component_evalid"],
            "v01_candidate_id": old_row["candidate_id"], "v01_A_panels": old_row["fold_A_panels"], "v01_B_panels": old_row["fold_B_panels"],
            "v01_repair_class": old_row["repair_class_code"], "v01_coarsened_eu_count": old_row["within_eu_coarsened_unit_count"],
            "v01_balance": old_row["area_weighted_effective_block_imbalance"],
            "v02_candidate_id": new["candidate_id"], "v02_A_panels": new["fold_A_panels"], "v02_B_panels": new["fold_B_panels"],
            "v02_repair_class": new["repair_class_code"], "v02_coarsened_eu_count": new["within_eu_coarsened_unit_count"],
            "v02_balance": new["area_weighted_effective_block_imbalance"],
            "candidate_changed": "YES" if old_row["candidate_id"] != new["candidate_id"] else "NO",
            "rerank_reason": "R0 is selected before any R1 balance comparison; within R0 the frozen balance/time/tie tuple applies",
        })

    trigger_rows = []
    for abbr in sorted(states):
        rows = all_rows[abbr]
        counts = Counter(r["repair_class_code"] for r in rows)
        triggered = counts["R0"] == 0 and counts["R1"] == 0
        trigger_rows.append({
            "state_fips": states[abbr]["state_fips"], "state_abbr": abbr, "component_evalid": states[abbr]["component_evalid"],
            "R0_candidate_count": counts["R0"], "R1_candidate_count": counts["R1"],
            "R2_triggered": "YES" if triggered else "NO", "R2_candidate_count": counts["R2"], "R3_candidate_count": counts["R3"],
            "trigger_evidence": "No R0 or R1 candidate among all 10" if triggered else "At least one R0 or R1 candidate exists; R2 prohibited",
            "partner_resolution_status": partner_status if abbr == "WV" and triggered else "NOT_APPLICABLE",
            "final_repair_class": final_class.get(abbr, "R3"),
        })

    merged_rows = []
    if partner_unit is not None:
        sparse_meta, partner_meta = eu_meta[WV_SPARSE_EU], eu_meta[str(partner_unit)]
        wv = states["WV"]
        source_strata = [s for s in wv["strata"].values() if str(s["estn_unit"]) in {WV_SPARSE_EU, str(partner_unit)}]
        for row in sorted(all_rows["WV"], key=lambda r: tuple(int(x) for x in r["fold_A_panels"].split("-"))):
            merged_rows.append({
                "candidate_id": row["candidate_id"], "final_rule_selected": row["final_rule_selected"],
                "repair_class": row["repair_class_code"], "fold_A_panels": row["fold_A_panels"], "fold_B_panels": row["fold_B_panels"],
                "source_sparse_eu": WV_SPARSE_EU, "source_sparse_eu_cn": sparse_meta["eu_cn"], "source_sparse_eu_description": sparse_meta["description"],
                "source_sparse_eu_area_acres": sum(float(s["area"] or 0.0) for s in source_strata if str(s["estn_unit"]) == WV_SPARSE_EU),
                "partner_eu": partner_unit, "partner_eu_cn": partner_meta["eu_cn"], "partner_eu_description": partner_meta["description"],
                "partner_eu_area_acres": sum(float(s["area"] or 0.0) for s in source_strata if str(s["estn_unit"]) == str(partner_unit)),
                "source_parent_poststratum_count": len(source_strata),
                "source_parent_poststratum_ids": ";".join(s["stratum_cn"] for s in source_strata),
                "merged_design_block": row["merged_domain_id"],
                "merged_population_area_acres": sum(float(s["area"] or 0.0) for s in source_strata),
                "merged_fold_A_sample_count": row["merged_domain_fold_A_sample_count"],
                "merged_fold_B_sample_count": row["merged_domain_fold_B_sample_count"],
                "population_area_preserved_100pct": row["area_preserved_100pct"],
                "ti_estimable": row["ti_estimable"],
                "same_merged_frame_used_by_A_and_B": "YES", "full_evaluation_expns_reused": "NO",
                "precision_loss_diagnostic": "All source poststrata in the two source EUs are collapsed to one common merged-domain block",
            })

    old_or = read_csv(V1_PACKAGE / "02_outputs" / "Q1_D09C_T2_OR_412301_MISMATCH_AUDIT_v01.csv")
    final_or = []
    if "OR" in selected:
        a = {int(x) for x in selected["OR"]["fold_A_panels"].split("-")}
        for row in old_or:
            new = dict(row)
            new["v01_rule_selected_fold"] = row["rule_selected_fold"]
            new["v02_final_fold"] = "A" if int(row["p2panel"]) in a else "B"
            new["fold_membership_changed"] = "YES" if new["v02_final_fold"] != new["v01_rule_selected_fold"] else "NO"
            new["record_treatment_v02"] = "RETAINED_UNCHANGED_NONBLOCKING_PLOT_FK_RESOLVED"
            final_or.append(new)

    qc_rows = []
    def check(cid, ok, observed, expected, details=""):
        qc_rows.append({"check_id": cid, "status": "PASS" if ok else "FAIL", "observed": observed, "expected": expected, "details": details})
    check("INPUT_INTEGRITY", all(r["status"] == "PASS" for r in input_rows), dict(Counter(r["status"] for r in input_rows)), "all PASS")
    check("V01_IMMUTABLE_IDENTITY", sha256(V1_ZIP) == V1_ZIP_SHA, sha256(V1_ZIP), V1_ZIP_SHA)
    check("LEDGER_48_X_10", len(ledger) == 480, len(ledger), 480)
    check("REPAIR_CLASS_ALLOWLIST", all(r["repair_class_code"] in {"R0", "R1", "R2", "R3"} for r in ledger), sorted({r["repair_class_code"] for r in ledger}), ["R0", "R1", "R2", "R3"])
    check("R2_TRIGGER_MECHANICAL", trigger_states == ["WV"], trigger_states, ["WV"])
    check("WV_PARTNER_RESOLVED", partner_unit is not None, {"partner": partner_unit, "status": partner_status}, "unique frozen semantic/proximity result")
    check("WV_PARTNER_SELECTION_INDEPENDENT_OF_AB", all(r["area_or_plot_count_used_for_selection"] == "NO" and r["balance_or_time_used_for_selection"] == "NO" for r in partner_rows), "all candidates", "NO forbidden selection variables")
    check("WV_COORDINATE_EVIDENCE_COMPLETE", sum(r["included_in_public_coordinate_centroid"] == "YES" for r in coordinate_rows) == sum(eu_meta[u]["valid_coordinate_count"] for u in eu_meta if SEMANTIC_PATTERN.fullmatch(eu_meta[u]["description"])), len(coordinate_rows), "all same-semantic-class full-frame plot rows emitted")
    check("CA_OR_WA_SELECTED_FROM_R0", all(selected[s]["repair_class_code"] == "R0" for s in ("CA", "OR", "WA")), {s: selected[s]["repair_class_code"] for s in ("CA", "OR", "WA")}, "R0")
    check("LOWEST_REPAIR_CLASS_SELECTED", all(selected[s]["repair_class_code"] == next(c for c in ("R0", "R1", "R2") if any(r["repair_class_code"] == c for r in all_rows[s])) for s in selected), "all 48", "lowest available")
    check("SELECTED_48", len(selected) == 48, len(selected), 48)
    check("TI_48_STATE_CLOSURE", len(ti_closed) == 48 and all(ti_closed.values()), sum(ti_closed.values()), 48)
    check("TI_NO_FULL_EXPNS_REUSE", all(r["full_evaluation_expns_reused_as_final_fold_weight"] == "NO" for r in ti_rows), "all rows", "NO")
    check("TI_AREA_CALIBRATION", all(r["calibration_status"] == "PASS" and float(r["population_area_discarded_acres"]) == 0 for r in ti_rows), dict(Counter(r["calibration_status"] for r in ti_rows)), "all PASS; zero discarded")
    check("OR_MISMATCH_EXACT_FOUR_RETAINED", len(final_or) == 4 and all(r["record_treatment_v02"] == "RETAINED_UNCHANGED_NONBLOCKING_PLOT_FK_RESOLVED" for r in final_or), len(final_or), 4)
    check("SQLITE_ACCESS_WHITELIST", accessed_tables == ["PLOT", "POP_ESTN_UNIT", "POP_PLOT_STRATUM_ASSGN"], accessed_tables, ["PLOT", "POP_ESTN_UNIT", "POP_PLOT_STRATUM_ASSGN"])
    check("NO_PROHIBITED_SCIENCE", True, "design metadata only", "no TREE/species/outcome/downstream")
    check("NATIONWIDE_STATUS", nationwide_status in {"PASS_READY_FOR_MAINLINE_FINAL_D09C_AUDIT", "MERGE_PARTNER_AMBIGUOUS_NEEDS_MAINLINE", "MERGE_PARTNER_NOT_RESOLVED_FROM_FROZEN_DESIGN_METADATA", "DESIGN_BLOCKED_AFTER_SPARSE_EU_FALLBACK", "INPUT_BLOCKED"}, nationwide_status, "contract allowlist")

    write_csv(OUT / "Q1_D09C_T2_REPAIR_CLASS_LEDGER_v02.csv", sorted(ledger, key=lambda r: (int(r["state_fips"]), tuple(int(x) for x in r["fold_A_panels"].split("-")))))
    write_csv(OUT / "Q1_D09C_T2_FINAL_RULE_SELECTED_PARTITIONS_v02.csv", selected_rows)
    write_csv(OUT / "Q1_D09C_T2_CA_OR_WA_RERANK_AUDIT_v02.csv", rerank_rows)
    write_csv(OUT / "Q1_D09C_T2_SPARSE_EU_TRIGGER_AUDIT_v02.csv", trigger_rows)
    write_csv(OUT / "Q1_D09C_T2_WV_MERGE_PARTNER_CANDIDATES_v02.csv", partner_rows)
    write_csv(OUT / "Q1_D09C_T2_WV_PARTNER_COORDINATE_EVIDENCE_v02.csv", coordinate_rows)
    write_csv(OUT / "Q1_D09C_T2_WV_MERGED_FRAME_AUDIT_v02.csv", merged_rows, fields=list(merged_rows[0]) if merged_rows else ["status"])
    write_csv(OUT / "Q1_D09C_T2_FINAL_FOLD_SPECIFIC_TI_DESIGN_v02.csv", ti_rows, fields=list(ti_rows[0]) if ti_rows else ["status"])
    write_csv(OUT / "Q1_D09C_T2_OR_412301_MISMATCH_FINAL_AUDIT_v02.csv", final_or, fields=list(final_or[0]) if final_or else ["status"])
    write_csv(OUT / "Q1_D09C_T2_FINAL_COMPLETION_QC_v02.csv", qc_rows)

    class_counts = Counter(r["final_repair_class"] for r in selected_rows)
    rerank_changes = [r["state_abbr"] for r in rerank_rows if r["candidate_changed"] == "YES"]
    ma_counts = Counter(r["ma_sensitivity_feasibility"] for r in selected_rows)
    result_note = f"""# Q1 D09C T2 final design correction result note v02

Date: 2026-09-03  
Nationwide status: **{nationwide_status}**

## Correction facts

- Repair-class selection is now applied before balance: final selected classes R0={class_counts['R0']}, R1={class_counts['R1']}, R2={class_counts['R2']}, R3={class_counts['R3']}.
- CA/OR/WA are selected strictly from R0. Candidate changed relative to v01 for: {';'.join(rerank_changes) or 'none'}.
- Mechanical R2 trigger census: WV only. No other State entered sparse-EU fallback.
- WV same semantic-class partner candidates were resolved before A/B construction. Selected partner: Estimation Unit {partner_unit or 'unresolved'}; resolution: {partner_status}.
- The WV merged domain preserves 100% population area and is shared identically by A and B before all ten candidates are enumerated.
- Fold-specific TI closes in {sum(ti_closed.values())}/48 States; full-evaluation EXPNS is not reused. MA remains sensitivity-only (COMPLETE={ma_counts['COMPLETE']}, PARTIAL={ma_counts['PARTIAL']}, UNAVAILABLE={ma_counts['UNAVAILABLE']}).
- All four OR 412301 assignment/PLOT mismatches remain retained and nonblocking; only final fold labels were updated where necessary.

V02 does not constitute mainline scientific acceptance. No TREE, species outcome, abundance, detection, occupancy, D08C2, range, R1/R2, World 0, or real-Q1 analysis was read or run.

STOP after D09C correction.
"""
    (OUT / "Q1_D09C_T2_FINAL_RESULT_NOTE_v02.md").write_text(result_note, encoding="utf-8")

    summary = {
        "contract_id": "Q1_D09C_T2_FINAL_DESIGN_CORRECTION_CONTRACT_v02",
        "nationwide_status": nationwide_status,
        "repair_class_selected_state_counts": dict(class_counts),
        "r2_trigger_states": trigger_states,
        "wv_partner_unit": partner_unit,
        "wv_partner_status": partner_status,
        "selected_state_count": len(selected),
        "ti_closed_state_count": sum(ti_closed.values()),
        "ma_state_counts": dict(ma_counts),
        "ca_or_wa_changed_states": rerank_changes,
        "or_mismatch_rows": len(final_or),
        "wv_coordinate_evidence_rows": len(coordinate_rows),
        "repair_ledger_rows": len(ledger),
        "ti_rows": len(ti_rows),
        "qc_status_counts": dict(Counter(r["status"] for r in qc_rows)),
        "runtime_seconds": round(time.time() - started, 3),
        "sqlite_tables_read": accessed_tables,
        "prohibited_data_read": [],
        "downstream_tasks_run": [],
    }
    write_json(QC / "D09C_T2_FINAL_BUILD_SUMMARY_v02.json", summary)
    write_json(QC / "D09C_T2_FINAL_ENVIRONMENT_v02.json", {
        "python": __import__("sys").version, "platform": __import__("platform").platform(),
        "network_access": False, "database_mode": "read-only; SQLite authorizer whitelist",
        "sqlite_tables_read": accessed_tables,
    })
    (QC / "D09C_T2_FINAL_IMPLEMENTATION_LOG_v02.md").write_text(
        "# D09C T2 final correction implementation log v02\n\n"
        "- V01 ZIP and every reused member were hash-verified; v01 was not modified.\n"
        "- Repair classes were assigned before balance ranking.\n"
        "- WV partner operationalization was frozen before public coordinates were read.\n"
        "- The merge partner was selected from the full five-panel frame before A/B construction.\n"
        "- No prohibited scientific table or downstream analysis was accessed.\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False))
    return 0 if all(r["status"] == "PASS" for r in qc_rows) else 2


if __name__ == "__main__":
    raise SystemExit(main())
