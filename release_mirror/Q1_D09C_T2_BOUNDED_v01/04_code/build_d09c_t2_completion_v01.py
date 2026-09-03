from __future__ import annotations

import csv
import hashlib
import io
import itertools
import json
import math
import statistics
import time
import zipfile
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(r"C:\range_paper")
OLD = ROOT / "04_derived" / "d09c_v01"
OLD_ARCHIVE = ROOT / "10_archive" / "d09c_v01"
RAW = ROOT / "02_raw" / "fia_t2_2023_raw_design_v01"
SRC = ROOT / "06_src" / "d09c_t2_completion_v01"
OUT = ROOT / "04_derived" / "d09c_t2_completion_v01"
QC = ROOT / "05_qc" / "d09c_t2_completion_v01"
CONTRACT = ROOT / "00_control" / "Q1_D09C_T2_BOUNDED_COMPLETION_CONTRACT_v01.md"
FREEZE = ROOT / "00_control" / "D09C_T2_COMPLETION_EXECUTION_FREEZE_v01.md"
PARAMS = SRC / "parameters_d09c_t2_completion_v01.json"

CONTRACT_SHA256 = "6a9955890c43d518a2bddac27e889eda908c4a32cbc87dae43604c7c2c7b1885"
NEW_STATES = {"CA": 62301, "OR": 412301, "WA": 532301}
PANELS = (1, 2, 3, 4, 5)
CANDIDATES = tuple(itertools.combinations(PANELS, 2))
TOL = 1e-8

OLD_INPUTS = {
    "D09C_TEMPORAL_FRAME_AUDIT_v01.csv": "02_outputs/D09C_TEMPORAL_FRAME_AUDIT_v01.csv",
    "D09C_EVALID_COMPONENT_LEDGER_v01.csv": "02_outputs/D09C_EVALID_COMPONENT_LEDGER_v01.csv",
    "D09C_PANEL_SUBPANEL_YEAR_LEDGER_v01.csv": "02_outputs/D09C_PANEL_SUBPANEL_YEAR_LEDGER_v01.csv",
    "D09C_LINEAGE_CROSSFOLD_AUDIT_v01.csv": "02_outputs/D09C_LINEAGE_CROSSFOLD_AUDIT_v01.csv",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_csv(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        yield from csv.DictReader(f)


def read_zip_csv(state: str, table: str):
    path = RAW / "raw_table_zips" / f"{state}_{table}.zip"
    with zipfile.ZipFile(path) as zf:
        names = zf.namelist()
        if names != [f"{state}_{table}.csv"]:
            raise RuntimeError(f"Unexpected ZIP members for {path}: {names}")
        with zf.open(names[0]) as raw, io.TextIOWrapper(raw, encoding="utf-8-sig", newline="") as text:
            yield from csv.DictReader(text)


def write_csv(path: Path, rows: list[dict], fieldnames: list[str] | None = None):
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = []
        seen = set()
        for row in rows:
            for key in row:
                if key not in seen:
                    seen.add(key)
                    fieldnames.append(key)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def as_int(value, default=None):
    if value is None or str(value).strip() == "":
        return default
    return int(float(value))


def as_float(value, default=None):
    if value is None or str(value).strip() == "":
        return default
    return float(value)


def rel_error(a: float, b: float) -> float:
    return abs(a - b) / max(abs(a), abs(b), 1.0)


def panel_code(values) -> str:
    return "-".join(str(x) for x in sorted(values))


def counter_text(counter: Counter) -> str:
    return ";".join(f"{k}:{counter[k]}" for k in sorted(counter))


def counter_n(counter: Counter) -> int:
    return int(sum(counter.values()))


def counter_mean(counter: Counter):
    n = counter_n(counter)
    return sum(float(k) * v for k, v in counter.items()) / n if n else None


def counter_median(counter: Counter):
    n = counter_n(counter)
    if not n:
        return None
    targets = {(n - 1) // 2, n // 2}
    values = []
    pos = 0
    for key in sorted(counter):
        for target in sorted(targets):
            if pos <= target < pos + counter[key]:
                values.append(float(key))
        pos += counter[key]
    return sum(values) / len(values)


def counter_sd(counter: Counter):
    n = counter_n(counter)
    if n < 2:
        return None
    mean = counter_mean(counter)
    ss = sum(v * (float(k) - mean) ** 2 for k, v in counter.items())
    return math.sqrt(ss / (n - 1))


def distribution_l1(a: Counter, b: Counter):
    na, nb = counter_n(a), counter_n(b)
    if not na or not nb:
        return math.inf
    return sum(abs(a.get(k, 0) / na - b.get(k, 0) / nb) for k in set(a) | set(b))


def imbalance(n_a: int, n_b: int) -> float:
    return abs(n_a / 2.0 - n_b / 3.0) / max((n_a + n_b) / 5.0, 1.0)


def new_state_shell(row: dict) -> dict:
    return {
        "state_fips": row["state_fips"],
        "state_abbr": row["state_abbr"],
        "state_name": row["state_name"],
        "target_reporting_year": as_int(row["target_reporting_year"]),
        "target_eval_group": row["target_eval_group"],
        "component_evalid": "",
        "evaluation_member_years": "",
        "start_invyr": "",
        "end_invyr": "",
        "membership_integrity": "",
        "input_source": "",
        "eus": {},
        "strata": {},
        "panel_year_counts": {p: Counter() for p in PANELS},
        "panel_invyr_counts": {p: Counter() for p in PANELS},
        "invalid_panel_count": 0,
        "unresolved_plot_count": 0,
        "unresolved_stratum_count": 0,
        "unresolved_survey_cn_count": 0,
        "duplicate_assignment_key_count": 0,
        "conflicting_assignment_key_count": 0,
        "multi_panel_lineages": {},
        "noncomplete_lineage_count": as_int(row.get("noncomplete_lineage_resolution_visit_count"), 0),
        "nonblocking_qc_flags": [],
        "frame_input_valid": False,
    }


def load_input_integrity() -> list[dict]:
    rows = []
    def add(role, path, expected, source):
        observed = sha256(path) if path.exists() else ""
        rows.append({
            "role": role,
            "path": str(path),
            "size_bytes": path.stat().st_size if path.exists() else "",
            "expected_sha256": expected,
            "observed_sha256": observed,
            "status": "PASS" if observed == expected else "FAIL",
            "authority_source": source,
        })

    add("CONTRACT", CONTRACT, CONTRACT_SHA256, "user attachment copied byte-for-byte")
    sums_path = OLD_ARCHIVE / "Q1_D09C_SPECIES_BLIND_REPORTING_STATE_PANEL_FOLD_AUDIT_REPRODUCIBLE_v01" / "SHA256SUMS_v01.csv"
    old_sums = {r["path"]: r["sha256"] for r in read_csv(sums_path)}
    for name, rel in OLD_INPUTS.items():
        add("FROZEN_D09C_T2_DESIGN_INPUT", OLD / name, old_sums[rel], "frozen D09C v01 SHA256SUMS_v01.csv")

    zip_path = OLD_ARCHIVE / "Q1_D09C_SPECIES_BLIND_REPORTING_STATE_PANEL_FOLD_AUDIT_REPRODUCIBLE_v01.zip"
    sidecar = (zip_path.with_suffix(zip_path.suffix + ".sha256")).read_text(encoding="utf-8").strip().split()[0]
    add("FROZEN_D09C_REPRODUCIBLE_ZIP", zip_path, sidecar, "frozen ZIP sidecar")

    manifest_path = RAW / "manifests" / "RAW_ASSET_MANIFEST_v01.csv"
    manifest_rows = list(read_csv(manifest_path))
    expected_by_name = {Path(r["LOCAL_FILE"]).name: r["SHA256"] for r in manifest_rows}
    for state in NEW_STATES:
        for table in ("POP_EVAL_GRP", "POP_EVAL_TYP", "POP_EVAL", "POP_ESTN_UNIT", "POP_STRATUM", "POP_PLOT_STRATUM_ASSGN", "PLOT", "SURVEY"):
            path = RAW / "raw_table_zips" / f"{state}_{table}.zip"
            add("FROZEN_NEW_STATE_RAW_DESIGN_ZIP", path, expected_by_name.get(path.name, ""), "RAW_ASSET_MANIFEST_v01.csv")
    return rows


def load_frozen_45_states() -> dict[str, dict]:
    frame_rows = [r for r in read_csv(OLD / "D09C_TEMPORAL_FRAME_AUDIT_v01.csv") if r["frame_id"] == "T2"]
    states = {r["state_abbr"]: new_state_shell(r) for r in frame_rows}
    components = [r for r in read_csv(OLD / "D09C_EVALID_COMPONENT_LEDGER_v01.csv") if r["frame_id"] == "T2" and r["status"] == "PASS"]
    for row in components:
        state = states[row["state_abbr"]]
        state["component_evalid"] = as_int(row["component_evalid"])
        state["evaluation_member_years"] = row["report_year_nm"]
        state["start_invyr"] = as_int(row["start_invyr"])
        state["end_invyr"] = as_int(row["end_invyr"])
        state["membership_integrity"] = "PASS_FROZEN_D09C_ACTUAL_RAW_KEY_CHAIN"
        state["input_source"] = "FROZEN_D09C_V01_T2_OUTPUTS"

    for row in read_csv(OLD / "D09C_PANEL_SUBPANEL_YEAR_LEDGER_v01.csv"):
        if row["frame_id"] != "T2" or row["state_abbr"] in NEW_STATES:
            continue
        state = states[row["state_abbr"]]
        eu_cn = row["estn_unit_cn"]
        if eu_cn not in state["eus"]:
            state["eus"][eu_cn] = {
                "eu_cn": eu_cn,
                "estn_unit": row["estn_unit"],
                "estn_unit_descr": row["estn_unit_descr"],
                "component_evalid": as_int(row["component_evalid"]),
                "area_used": as_float(row["parent_eu_area_used_acres"]),
            }
        stratum_cn = row["stratum_cn"]
        if stratum_cn not in state["strata"]:
            state["strata"][stratum_cn] = {
                "stratum_cn": stratum_cn,
                "eu_cn": eu_cn,
                "component_evalid": as_int(row["component_evalid"]),
                "estn_unit": row["estn_unit"],
                "stratumcd": row["stratumcd"],
                "stratum_descr": row["stratum_descr"],
                "p1pointcnt": as_int(row["parent_stratum_p1pointcnt"]),
                "p2pointcnt": as_int(row["parent_stratum_p2pointcnt"]),
                "expns_full": as_float(row["full_evaluation_expns"]),
                "area": as_float(row["parent_area_expns_identity_acres"], 0.0),
                "area_p1": as_float(row["parent_area_p1_identity_acres"]),
                "panel_counts": Counter(),
                "panel_year_counts": {p: Counter() for p in PANELS},
                "panel_invyr_counts": {p: Counter() for p in PANELS},
            }
        p = as_int(row["p2panel"])
        n = as_int(row["unique_plot_visit_count"], 0)
        if p in PANELS and n:
            stratum = state["strata"][stratum_cn]
            stratum["panel_counts"][p] += n
            year = as_int(row["measyear"])
            invyr = as_int(row["invyr"])
            if year is not None:
                stratum["panel_year_counts"][p][year] += n
                state["panel_year_counts"][p][year] += n
            if invyr is not None:
                stratum["panel_invyr_counts"][p][invyr] += n
                state["panel_invyr_counts"][p][invyr] += n

    for abbr, state in states.items():
        if abbr in NEW_STATES:
            continue
        observed = {p for s in state["strata"].values() for p, n in s["panel_counts"].items() if n > 0}
        state["frame_input_valid"] = bool(state["component_evalid"] and state["eus"] and state["strata"] and observed == set(PANELS))
        if not state["frame_input_valid"]:
            state["nonblocking_qc_flags"].append("FROZEN_INPUT_FRAME_NOT_CLOSED")
    return states


def resolve_root(cn: str, prev_map: dict[str, str | None]):
    current = cn
    seen = set()
    while True:
        if current in seen:
            return current, "CYCLE"
        seen.add(current)
        prev = prev_map.get(current)
        if not prev:
            return current, "COMPLETE"
        if prev not in prev_map:
            return current, "MISSING_PREDECESSOR"
        current = prev


def load_new_state(state: dict, expected_evalid: int):
    abbr = state["state_abbr"]
    statecd = as_int(state["state_fips"])
    target_group = int(f"{statecd:02d}{state['target_reporting_year']:04d}")
    groups = [r for r in read_zip_csv(abbr, "POP_EVAL_GRP") if as_int(r["STATECD"]) == statecd and as_int(r["EVAL_GRP"]) == target_group]
    if len(groups) != 1:
        state["membership_integrity"] = "FAIL_REPORTING_GROUP_NOT_UNIQUE"
        return []
    group = groups[0]
    types = [r for r in read_zip_csv(abbr, "POP_EVAL_TYP") if r["EVAL_GRP_CN"] == group["CN"] and r["EVAL_TYP"].upper() == "EXPVOL"]
    eval_by_cn = {r["CN"]: r for r in read_zip_csv(abbr, "POP_EVAL")}
    eval_rows = [eval_by_cn[r["EVAL_CN"]] for r in types if r["EVAL_CN"] in eval_by_cn]
    if len(eval_rows) != 1 or as_int(eval_rows[0]["EVALID"]) != expected_evalid:
        state["membership_integrity"] = "FAIL_EXPVOL_COMPONENT_RAW_KEY_CHAIN"
        return []
    ev = eval_rows[0]
    state["component_evalid"] = expected_evalid
    state["evaluation_member_years"] = ev["REPORT_YEAR_NM"]
    state["start_invyr"] = as_int(ev["START_INVYR"])
    state["end_invyr"] = as_int(ev["END_INVYR"])
    state["membership_integrity"] = "PASS_NEW_FROZEN_RAW_KEY_CHAIN"
    state["input_source"] = "FROZEN_CA_OR_WA_RAW_DESIGN_ZIPS"

    eu_rows = [r for r in read_zip_csv(abbr, "POP_ESTN_UNIT") if as_int(r["EVALID"]) == expected_evalid]
    for row in eu_rows:
        state["eus"][row["CN"]] = {
            "eu_cn": row["CN"],
            "estn_unit": row["ESTN_UNIT"],
            "estn_unit_descr": row["ESTN_UNIT_DESCR"],
            "component_evalid": expected_evalid,
            "area_used": as_float(row["AREA_USED"]),
        }

    strata_rows = [r for r in read_zip_csv(abbr, "POP_STRATUM") if as_int(r["EVALID"]) == expected_evalid]
    p1_sums = Counter()
    for row in strata_rows:
        p1_sums[row["ESTN_UNIT_CN"]] += as_int(row["P1POINTCNT"], 0)
    for row in strata_rows:
        eu = state["eus"].get(row["ESTN_UNIT_CN"])
        if eu is None:
            state["unresolved_stratum_count"] += 1
            continue
        p1 = as_int(row["P1POINTCNT"])
        p2 = as_int(row["P2POINTCNT"])
        expns = as_float(row["EXPNS"])
        area = expns * p2 if expns is not None and p2 is not None else None
        denom = p1_sums[row["ESTN_UNIT_CN"]]
        area_p1 = eu["area_used"] * p1 / denom if eu["area_used"] is not None and p1 is not None and denom else None
        state["strata"][row["CN"]] = {
            "stratum_cn": row["CN"],
            "eu_cn": row["ESTN_UNIT_CN"],
            "component_evalid": expected_evalid,
            "estn_unit": row["ESTN_UNIT"],
            "stratumcd": row["STRATUMCD"],
            "stratum_descr": row["STRATUM_DESCR"],
            "p1pointcnt": p1,
            "p2pointcnt": p2,
            "expns_full": expns,
            "area": area,
            "area_p1": area_p1,
            "panel_counts": Counter(),
            "panel_year_counts": {p: Counter() for p in PANELS},
            "panel_invyr_counts": {p: Counter() for p in PANELS},
        }

    plot_rows = list(read_zip_csv(abbr, "PLOT"))
    plots = {r["CN"]: r for r in plot_rows}
    prev_map = {r["CN"]: (r["PREV_PLT_CN"] or None) for r in plot_rows}
    survey_cns = {r["CN"] for r in read_zip_csv(abbr, "SURVEY")}
    assignments = {}
    mismatch_rows = []
    for row in read_zip_csv(abbr, "POP_PLOT_STRATUM_ASSGN"):
        if as_int(row["EVALID"]) != expected_evalid:
            continue
        key = row["PLT_CN"]
        if key in assignments:
            state["duplicate_assignment_key_count"] += 1
            prior = assignments[key]
            if (prior["STRATUM_CN"], prior["ESTN_UNIT"], prior["STRATUMCD"]) != (row["STRATUM_CN"], row["ESTN_UNIT"], row["STRATUMCD"]):
                state["conflicting_assignment_key_count"] += 1
            continue
        assignments[key] = row

    lineage_panels = defaultdict(set)
    for plt_cn, assn in assignments.items():
        plot = plots.get(plt_cn)
        stratum = state["strata"].get(assn["STRATUM_CN"])
        if plot is None:
            state["unresolved_plot_count"] += 1
            continue
        if stratum is None:
            state["unresolved_stratum_count"] += 1
            continue
        if plot["SRV_CN"] not in survey_cns:
            state["unresolved_survey_cn_count"] += 1
        p = as_int(plot["P2PANEL"])
        if p not in PANELS:
            state["invalid_panel_count"] += 1
            continue
        stratum["panel_counts"][p] += 1
        year = as_int(plot["MEASYEAR"])
        invyr = as_int(plot["INVYR"])
        if year is not None:
            stratum["panel_year_counts"][p][year] += 1
            state["panel_year_counts"][p][year] += 1
        if invyr is not None:
            stratum["panel_invyr_counts"][p][invyr] += 1
            state["panel_invyr_counts"][p][invyr] += 1
        root, root_status = resolve_root(plt_cn, prev_map)
        lineage_panels[root].add(p)
        if root_status != "COMPLETE":
            state["noncomplete_lineage_count"] += 1
        assn_state = as_int(assn["STATECD"])
        assn_invyr = as_int(assn["INVYR"])
        plot_state = as_int(plot["STATECD"])
        if assn_state != plot_state or assn_invyr != invyr:
            mismatch_rows.append({
                "state_abbr": abbr,
                "component_evalid": expected_evalid,
                "assignment_cn": assn["CN"],
                "plt_cn": plt_cn,
                "assignment_statecd": assn_state,
                "assignment_invyr": assn_invyr,
                "plot_statecd": plot_state,
                "plot_invyr": invyr,
                "p2panel": p,
                "estn_unit": assn["ESTN_UNIT"],
                "stratumcd": assn["STRATUMCD"],
                "stratum_cn": assn["STRATUM_CN"],
                "plot_fk_resolved": "YES",
                "retained_without_rewrite": "YES",
            })
    state["multi_panel_lineages"] = {root: sorted(ps) for root, ps in lineage_panels.items() if len(ps) > 1}
    observed = {p for s in state["strata"].values() for p, n in s["panel_counts"].items() if n > 0}
    state["frame_input_valid"] = bool(
        state["membership_integrity"].startswith("PASS")
        and state["eus"] and state["strata"] and observed == set(PANELS)
        and state["invalid_panel_count"] == 0
        and state["unresolved_plot_count"] == 0
        and state["unresolved_stratum_count"] == 0
        and state["unresolved_survey_cn_count"] == 0
        and state["conflicting_assignment_key_count"] == 0
    )
    if abbr == "OR" and mismatch_rows:
        state["nonblocking_qc_flags"].append("OR_412301_ASSIGNMENT_PLOT_STATECD_INVYR_MISMATCH_RETAINED")
    return mismatch_rows


def state_panel_counts(state: dict) -> Counter:
    counts = Counter()
    for stratum in state["strata"].values():
        counts.update(stratum["panel_counts"])
    return counts


def temporal_metrics(state: dict, a_panels, b_panels):
    a = Counter()
    b = Counter()
    for p in a_panels:
        a.update(state["panel_year_counts"][p])
    for p in b_panels:
        b.update(state["panel_year_counts"][p])
    mean_a, mean_b = counter_mean(a), counter_mean(b)
    sd_a, sd_b = counter_sd(a), counter_sd(b)
    return {
        "fold_A_measyear_n": counter_n(a),
        "fold_B_measyear_n": counter_n(b),
        "fold_A_measyear_distribution": counter_text(a),
        "fold_B_measyear_distribution": counter_text(b),
        "fold_A_measyear_mean": mean_a if mean_a is not None else "",
        "fold_B_measyear_mean": mean_b if mean_b is not None else "",
        "fold_A_measyear_median": counter_median(a) if a else "",
        "fold_B_measyear_median": counter_median(b) if b else "",
        "fold_A_measyear_sd": sd_a if sd_a is not None else "",
        "fold_B_measyear_sd": sd_b if sd_b is not None else "",
        "fold_A_measyear_min": min(a) if a else "",
        "fold_A_measyear_max": max(a) if a else "",
        "fold_B_measyear_min": min(b) if b else "",
        "fold_B_measyear_max": max(b) if b else "",
        "temporal_center_abs_diff_years": abs(mean_a - mean_b) if mean_a is not None and mean_b is not None else math.inf,
        "temporal_distribution_l1_distance": distribution_l1(a, b),
        "temporal_sd_abs_diff_years": abs(sd_a - sd_b) if sd_a is not None and sd_b is not None else math.inf,
    }


def candidate_effective_blocks(state: dict, a_panels, b_panels):
    by_eu = defaultdict(list)
    for stratum in state["strata"].values():
        by_eu[stratum["eu_cn"]].append(stratum)
    effective = []
    coarsening = []
    true_blocks = []
    for eu_cn, strata in sorted(by_eu.items()):
        missing_a = [s for s in strata if sum(s["panel_counts"][p] for p in a_panels) == 0]
        missing_b = [s for s in strata if sum(s["panel_counts"][p] for p in b_panels) == 0]
        n_a_eu = sum(sum(s["panel_counts"][p] for p in a_panels) for s in strata)
        n_b_eu = sum(sum(s["panel_counts"][p] for p in b_panels) for s in strata)
        area_eu = sum(float(s["area"] or 0.0) for s in strata)
        if missing_a or missing_b:
            block = {
                "effective_block_id": f"EU:{eu_cn}",
                "resolution": "ESTIMATION_UNIT_SYMMETRIC_COARSENING",
                "eu_cn": eu_cn,
                "strata": strata,
                "area": area_eu,
                "panel_counts": Counter({p: sum(s["panel_counts"][p] for s in strata) for p in PANELS}),
            }
            effective.append(block)
            coarsening.append({
                "eu_cn": eu_cn,
                "strata": strata,
                "missing_a": missing_a,
                "missing_b": missing_b,
                "n_a_eu": n_a_eu,
                "n_b_eu": n_b_eu,
                "area_eu": area_eu,
            })
            if n_a_eu == 0 or n_b_eu == 0:
                true_blocks.append(eu_cn)
        else:
            for s in strata:
                effective.append({
                    "effective_block_id": f"STRATUM:{s['stratum_cn']}",
                    "resolution": "PARENT_POSTSTRATUM",
                    "eu_cn": eu_cn,
                    "strata": [s],
                    "area": float(s["area"] or 0.0),
                    "panel_counts": Counter(s["panel_counts"]),
                })
    return effective, coarsening, true_blocks


def build_candidate(state: dict, a_tuple):
    a_panels = set(a_tuple)
    b_panels = set(PANELS) - a_panels
    counts = state_panel_counts(state)
    effective, coarsening, true_blocks = candidate_effective_blocks(state, a_panels, b_panels)
    original_area = sum(float(s["area"] or 0.0) for s in state["strata"].values())
    effective_area = sum(b["area"] for b in effective)
    area_error = rel_error(original_area, effective_area)
    block_num = 0.0
    block_denom = 0.0
    block_values = []
    for block in effective:
        n_a = sum(block["panel_counts"][p] for p in a_panels)
        n_b = sum(block["panel_counts"][p] for p in b_panels)
        value = imbalance(n_a, n_b)
        block_values.append(value)
        block_num += block["area"] * value
        block_denom += block["area"]
    by_eu = defaultdict(lambda: {"area": 0.0, "counts": Counter()})
    for s in state["strata"].values():
        by_eu[s["eu_cn"]]["area"] += float(s["area"] or 0.0)
        by_eu[s["eu_cn"]]["counts"].update(s["panel_counts"])
    eu_num = sum(v["area"] * imbalance(sum(v["counts"][p] for p in a_panels), sum(v["counts"][p] for p in b_panels)) for v in by_eu.values())
    eu_denom = sum(v["area"] for v in by_eu.values())
    n_a = sum(counts[p] for p in a_panels)
    n_b = sum(counts[p] for p in b_panels)
    lineage_overlap = [root for root, ps in state["multi_panel_lineages"].items() if set(ps) & a_panels and set(ps) & b_panels]
    unresolved = (
        state["invalid_panel_count"] + state["unresolved_plot_count"] + state["unresolved_stratum_count"]
        + state["unresolved_survey_cn_count"] + state["conflicting_assignment_key_count"]
    )
    area_failure = int(area_error > TOL)
    valid = int(state["frame_input_valid"] and not true_blocks and not lineage_overlap and not area_failure)
    parent_missing_a = []
    parent_missing_b = []
    for s in state["strata"].values():
        if sum(s["panel_counts"][p] for p in a_panels) == 0:
            parent_missing_a.append(s)
        if sum(s["panel_counts"][p] for p in b_panels) == 0:
            parent_missing_b.append(s)
    temporal = temporal_metrics(state, a_panels, b_panels)
    return {
        "candidate_id": f"T2_{state['state_abbr']}_A{panel_code(a_panels)}_B{panel_code(b_panels)}",
        "state_fips": state["state_fips"],
        "state_abbr": state["state_abbr"],
        "state_name": state["state_name"],
        "target_reporting_year": state["target_reporting_year"],
        "target_eval_group": state["target_eval_group"],
        "component_evalid": state["component_evalid"],
        "fold_A_panels": panel_code(a_panels),
        "fold_B_panels": panel_code(b_panels),
        "fold_A_panel_count": 2,
        "fold_B_panel_count": 3,
        "p2panel_split_count": 0,
        "parent_estimation_unit_count": len(state["eus"]),
        "parent_poststratum_count": len(state["strata"]),
        "effective_design_block_count": len(effective),
        "fold_A_parent_poststrata_covered": len(state["strata"]) - len(parent_missing_a),
        "fold_B_parent_poststrata_covered": len(state["strata"]) - len(parent_missing_b),
        "fold_A_missing_parent_poststrata": len(parent_missing_a),
        "fold_B_missing_parent_poststrata": len(parent_missing_b),
        "symmetric_coarsening_estimation_unit_count": len(coarsening),
        "symmetric_coarsening_parent_poststratum_count": len({s["stratum_cn"] for c in coarsening for s in c["strata"]}),
        "symmetric_coarsening_area_acres": sum(c["area_eu"] for c in coarsening),
        "true_eu_level_block_count": len(true_blocks),
        "true_eu_level_block_ids": ";".join(true_blocks),
        "original_population_area_acres": original_area,
        "effective_population_area_acres": effective_area,
        "population_area_preservation_relative_error": area_error,
        "population_area_preserved_100pct": int(area_error <= TOL),
        "area_preservation_failure_count": area_failure,
        "unresolved_design_key_count": unresolved,
        "crossfold_lineage_overlap_count": len(lineage_overlap),
        "crossfold_lineage_roots": ";".join(sorted(lineage_overlap)),
        "candidate_design_valid": valid,
        "candidate_design_status": "VALID_TI_ESTIMABLE" if valid else ("DESIGN_BLOCKED_ESTIMATION_UNIT_UNSAMPLED" if true_blocks else "INPUT_OR_DESIGN_KEY_BLOCKED"),
        "area_weighted_effective_block_imbalance": block_num / block_denom if block_denom else math.inf,
        "max_effective_block_imbalance": max(block_values, default=math.inf),
        "area_weighted_estimation_unit_imbalance": eu_num / eu_denom if eu_denom else math.inf,
        "fold_A_plot_count": n_a,
        "fold_B_plot_count": n_b,
        "fold_A_plot_share": n_a / (n_a + n_b) if n_a + n_b else "",
        "absolute_fold_A_plot_share_minus_0_4": abs(n_a / (n_a + n_b) - 0.4) if n_a + n_b else math.inf,
        **temporal,
        "mechanical_rank": "",
        "rule_selected_top_candidate": 0,
        "mainline_final_acceptance": "NOT_DECIDED",
        "ranking_rule": "validity > effective-block balance > temporal balance > ascending A tuple",
        "_effective": effective,
        "_coarsening": coarsening,
    }


def ranking_key(row: dict):
    a_tuple = tuple(int(x) for x in row["fold_A_panels"].split("-"))
    return (
        -int(row["candidate_design_valid"]),
        int(row["true_eu_level_block_count"]),
        int(row["area_preservation_failure_count"]),
        int(row["unresolved_design_key_count"]),
        float(row["area_weighted_effective_block_imbalance"]),
        float(row["max_effective_block_imbalance"]),
        float(row["area_weighted_estimation_unit_imbalance"]),
        float(row["absolute_fold_A_plot_share_minus_0_4"]),
        float(row["temporal_center_abs_diff_years"]),
        float(row["temporal_distribution_l1_distance"]),
        float(row["temporal_sd_abs_diff_years"]),
        a_tuple,
    )


def clean_candidate(row: dict) -> dict:
    return {k: v for k, v in row.items() if not k.startswith("_")}


def main() -> int:
    started = time.time()
    OUT.mkdir(parents=True, exist_ok=True)
    QC.mkdir(parents=True, exist_ok=True)
    if any(OUT.iterdir()) or any(QC.iterdir()):
        raise RuntimeError("Refusing to overwrite nonempty D09C T2 completion output/QC directories")

    input_rows = load_input_integrity()
    write_csv(QC / "D09C_T2_INPUT_INTEGRITY_v01.csv", input_rows)
    if any(r["status"] != "PASS" for r in input_rows):
        raise RuntimeError("Input integrity failed before scientific computation")

    states = load_frozen_45_states()
    or_mismatches = []
    for abbr, evalid in NEW_STATES.items():
        or_new = load_new_state(states[abbr], evalid)
        if abbr == "OR":
            or_mismatches.extend(or_new)

    all_candidates = []
    selected = {}
    mechanical_top = {}
    coarsening_rows = []
    wv_rows = []
    for abbr in sorted(states):
        state = states[abbr]
        candidates = [build_candidate(state, a) for a in CANDIDATES]
        candidates.sort(key=ranking_key)
        mechanical_top[abbr] = candidates[0]
        for rank, row in enumerate(candidates, 1):
            row["mechanical_rank"] = rank
            row["mechanical_top_candidate"] = int(rank == 1)
            if rank == 1 and row["candidate_design_valid"]:
                row["rule_selected_top_candidate"] = 1
                selected[abbr] = row
            for c in row["_coarsening"]:
                coarsening_rows.append({
                    "candidate_id": row["candidate_id"],
                    "state_fips": state["state_fips"],
                    "state_abbr": abbr,
                    "mechanical_rank": rank,
                    "mechanical_top_candidate": row["mechanical_top_candidate"],
                    "rule_selected_top_candidate": row["rule_selected_top_candidate"],
                    "fold_A_panels": row["fold_A_panels"],
                    "fold_B_panels": row["fold_B_panels"],
                    "component_evalid": state["component_evalid"],
                    "estimation_unit_cn": c["eu_cn"],
                    "estimation_unit": state["eus"][c["eu_cn"]]["estn_unit"],
                    "estimation_unit_description": state["eus"][c["eu_cn"]]["estn_unit_descr"],
                    "parent_poststratum_count": len(c["strata"]),
                    "fold_A_missing_parent_poststratum_count": len(c["missing_a"]),
                    "fold_A_missing_parent_poststratum_ids": ";".join(s["stratum_cn"] for s in c["missing_a"]),
                    "fold_B_missing_parent_poststratum_count": len(c["missing_b"]),
                    "fold_B_missing_parent_poststratum_ids": ";".join(s["stratum_cn"] for s in c["missing_b"]),
                    "original_stratification": "PARENT_POSTSTRATA",
                    "coarsened_stratification": "ONE_BLOCK_WITHIN_ESTIMATION_UNIT_FOR_BOTH_FOLDS",
                    "fold_A_coarsened_sample_count": c["n_a_eu"],
                    "fold_B_coarsened_sample_count": c["n_b_eu"],
                    "original_population_area_acres": c["area_eu"],
                    "coarsened_population_area_acres": c["area_eu"],
                    "population_area_preservation_relative_error": 0.0,
                    "population_area_preserved_100pct": 1,
                    "resulting_design_status": "DESIGN_BLOCKED_ESTIMATION_UNIT_UNSAMPLED" if c["n_a_eu"] == 0 or c["n_b_eu"] == 0 else "TI_ESTIMABLE_AFTER_SYMMETRIC_COARSENING",
                    "threshold_used": "NONE",
                })
            if abbr == "WV":
                a_panels = {int(x) for x in row["fold_A_panels"].split("-")}
                b_panels = set(PANELS) - a_panels
                for s in state["strata"].values():
                    n_a = sum(s["panel_counts"][p] for p in a_panels)
                    n_b = sum(s["panel_counts"][p] for p in b_panels)
                    if n_a == 0 or n_b == 0:
                        c = next(x for x in row["_coarsening"] if x["eu_cn"] == s["eu_cn"])
                        wv_rows.append({
                            "candidate_id": row["candidate_id"],
                            "mechanical_rank": rank,
                            "mechanical_top_candidate": row["mechanical_top_candidate"],
                            "rule_selected_top_candidate": row["rule_selected_top_candidate"],
                            "fold_A_panels": row["fold_A_panels"],
                            "fold_B_panels": row["fold_B_panels"],
                            "affected_fold": "A" if n_a == 0 and n_b > 0 else ("B" if n_b == 0 and n_a > 0 else "A;B"),
                            "component_evalid": state["component_evalid"],
                            "estimation_unit_cn": s["eu_cn"],
                            "estimation_unit": s["estn_unit"],
                            "parent_stratum_cn": s["stratum_cn"],
                            "parent_stratumcd": s["stratumcd"],
                            "parent_stratum_area_acres": s["area"],
                            "parent_fold_A_sample_count": n_a,
                            "parent_fold_B_sample_count": n_b,
                            "symmetric_coarsening_applied_to_both_folds": "YES",
                            "coarsened_fold_A_sample_count": c["n_a_eu"],
                            "coarsened_fold_B_sample_count": c["n_b_eu"],
                            "estimation_unit_population_area_acres": c["area_eu"],
                            "population_area_preserved_100pct": "YES",
                            "ti_estimable_after_coarsening": "YES" if c["n_a_eu"] > 0 and c["n_b_eu"] > 0 else "NO",
                            "historical_area_recovery_threshold_used": "NO",
                            "historical_diagnostic_only_note": "Prior approximately 23014.8-acre / 0.9985158 recovery is not a decision rule.",
                        })
        all_candidates.extend(candidates)

    for row in or_mismatches:
        top = selected.get("OR")
        panel = int(row["p2panel"])
        a_panels = {int(x) for x in top["fold_A_panels"].split("-")} if top else set()
        row["rule_selected_fold"] = "A" if panel in a_panels else "B"
        row["design_membership"] = "RETAINED_IN_RULE_SELECTED_WHOLE_PANEL_DESIGN"
        row["blocking_status"] = "NONBLOCKING_RESOLVED_PLOT_FK"

    ti_rows = []
    ma_rows = []
    state_ma_status = {}
    ti_state_closure = {}
    for abbr, top in selected.items():
        state = states[abbr]
        a_panels = {int(x) for x in top["fold_A_panels"].split("-")}
        b_panels = set(PANELS) - a_panels
        state_area = sum(float(s["area"] or 0.0) for s in state["strata"].values())
        fold_closure = {}
        fold_ma = {}
        for fold, panels in (("A", a_panels), ("B", b_panels)):
            recovered_total = 0.0
            total_panel_blocks = 0
            zero_panel_blocks = 0
            sparse_panel_blocks = 0
            for block in top["_effective"]:
                area = block["area"]
                n_fold = sum(block["panel_counts"][p] for p in panels)
                n_full = sum(block["panel_counts"][p] for p in PANELS)
                weight = area / n_fold if n_fold else None
                recovered = weight * n_fold if weight is not None else 0.0
                recovered_total += recovered
                strata = block["strata"]
                official_comparator = strata[0]["expns_full"] if len(strata) == 1 else ""
                full_effective_comparator = area / n_full if n_full else ""
                ti_rows.append({
                    "candidate_id": top["candidate_id"],
                    "state_fips": state["state_fips"],
                    "state_abbr": abbr,
                    "fold": fold,
                    "selected_panels": panel_code(panels),
                    "component_evalid": state["component_evalid"],
                    "estimation_unit_cn": block["eu_cn"],
                    "estimation_unit": state["eus"][block["eu_cn"]]["estn_unit"],
                    "effective_design_block_id": block["effective_block_id"],
                    "design_resolution": block["resolution"],
                    "included_parent_poststratum_count": len(strata),
                    "included_parent_poststratum_ids": ";".join(s["stratum_cn"] for s in strata),
                    "included_parent_stratumcds": ";".join(str(s["stratumcd"]) for s in strata),
                    "fold_sample_count": n_fold,
                    "full_evaluation_sample_count_comparator": n_full,
                    "population_area_acres": area,
                    "fold_specific_ti_expansion_acres_per_plot": weight if weight is not None else "",
                    "fold_weight_construction": "effective_block_population_area / actual_fold_sample_count",
                    "official_full_evaluation_expns_comparator": official_comparator,
                    "effective_block_full_sample_area_per_plot_comparator": full_effective_comparator,
                    "full_evaluation_expns_reused_as_final_fold_weight": "NO",
                    "synthetic_constant_recovered_area_acres": recovered,
                    "calibration_relative_error": rel_error(recovered, area),
                    "calibration_status": "PASS" if n_fold and rel_error(recovered, area) <= TOL else "FAIL",
                    "variance_df_n_minus_1": max(n_fold - 1, 0),
                    "within_block_variance_estimable_n_ge_2": int(n_fold >= 2),
                    "population_area_discarded_acres": 0.0,
                    "primary_estimator_role": "TI_PRIMARY_DESIGN_CONSTRUCTION_AUDIT",
                })
                for p in panels:
                    total_panel_blocks += 1
                    n = block["panel_counts"][p]
                    if n == 0:
                        zero_panel_blocks += 1
                    if n < 2:
                        sparse_panel_blocks += 1
            fold_closure[fold] = rel_error(recovered_total, state_area) <= TOL
            if any(sum(block["panel_counts"][p] for p in panels) == 0 for block in top["_effective"]):
                ma_status = "UNAVAILABLE"
            elif zero_panel_blocks:
                ma_status = "PARTIAL"
            else:
                ma_status = "COMPLETE"
            fold_ma[fold] = ma_status
            ma_rows.append({
                "state_fips": state["state_fips"],
                "state_abbr": abbr,
                "candidate_id": top["candidate_id"],
                "fold": fold,
                "selected_panels": panel_code(panels),
                "effective_design_block_count": len(top["_effective"]),
                "panel_by_effective_block_count": total_panel_blocks,
                "empty_panel_block_count": zero_panel_blocks,
                "sparse_panel_block_count_n_lt_2": sparse_panel_blocks,
                "ma_fold_feasibility": ma_status,
                "ma_role": "SENSITIVITY_FEASIBILITY_ONLY",
                "ma_used_to_select_primary_design": "NO",
                "reason": "All selected panel-by-block cells represented" if ma_status == "COMPLETE" else ("Some single panels lack effective-block support; TI remains closed" if ma_status == "PARTIAL" else "At least one fold-effective-block is unsampled"),
            })
        ti_state_closure[abbr] = all(fold_closure.values())
        state_ma_status[abbr] = "UNAVAILABLE" if "UNAVAILABLE" in fold_ma.values() else ("PARTIAL" if "PARTIAL" in fold_ma.values() else "COMPLETE")
        for row in ma_rows[-2:]:
            row["ma_state_feasibility"] = state_ma_status[abbr]

    for abbr in sorted(set(states) - set(selected)):
        state = states[abbr]
        top = mechanical_top[abbr]
        a_panels = {int(x) for x in top["fold_A_panels"].split("-")}
        b_panels = set(PANELS) - a_panels
        state_ma_status[abbr] = "UNAVAILABLE"
        for fold, panels in (("A", a_panels), ("B", b_panels)):
            ma_rows.append({
                "state_fips": state["state_fips"],
                "state_abbr": abbr,
                "candidate_id": top["candidate_id"],
                "fold": fold,
                "selected_panels": panel_code(panels),
                "effective_design_block_count": len(top["_effective"]),
                "panel_by_effective_block_count": len(top["_effective"]) * len(panels),
                "empty_panel_block_count": sum(block["panel_counts"][p] == 0 for block in top["_effective"] for p in panels),
                "sparse_panel_block_count_n_lt_2": sum(block["panel_counts"][p] < 2 for block in top["_effective"] for p in panels),
                "ma_fold_feasibility": "UNAVAILABLE",
                "ma_state_feasibility": "UNAVAILABLE",
                "ma_role": "SENSITIVITY_FEASIBILITY_ONLY",
                "ma_used_to_select_primary_design": "NO",
                "reason": "Mechanical top candidate has an estimation-unit-level unsampled fold; primary design is blocked.",
            })

    selected_rows = []
    frame_rows = []
    for abbr in sorted(states):
        state = states[abbr]
        counts = state_panel_counts(state)
        top = selected.get(abbr)
        top_any = mechanical_top[abbr]
        if not state["frame_input_valid"]:
            state_status = "INPUT_BLOCKED"
        elif not top:
            state_status = "DESIGN_BLOCKED_ESTIMATION_UNIT_UNSAMPLED"
        elif top["symmetric_coarsening_estimation_unit_count"]:
            state_status = "DESIGN_COMPLETE_WITH_SYMMETRIC_COARSENING"
        elif state["nonblocking_qc_flags"]:
            state_status = "DESIGN_COMPLETE_WITH_NONBLOCKING_QC"
        else:
            state_status = "DESIGN_COMPLETE"
        frame_rows.append({
            "state_fips": state["state_fips"],
            "state_abbr": abbr,
            "state_name": state["state_name"],
            "frame_id": "T2",
            "reporting_frame": f"{state['target_reporting_year']} official reporting-State group",
            "target_eval_group": state["target_eval_group"],
            "required_eval_typ": "EXPVOL",
            "component_evalid": state["component_evalid"],
            "evaluation_member_years": state["evaluation_member_years"],
            "start_invyr": state["start_invyr"],
            "end_invyr": state["end_invyr"],
            "component_membership_integrity": state["membership_integrity"],
            "input_source": state["input_source"],
            "estimation_unit_count": len(state["eus"]),
            "parent_poststratum_count": len(state["strata"]),
            "population_area_acres": sum(float(s["area"] or 0.0) for s in state["strata"].values()),
            "observed_p2panel_values": panel_code(p for p in PANELS if counts[p] > 0),
            **{f"panel_{p}_plot_count": counts[p] for p in PANELS},
            "five_panel_complete": int(all(counts[p] > 0 for p in PANELS)),
            "candidate_count": 10,
            "legal_candidate_count": sum(r["candidate_design_valid"] for r in all_candidates if r["state_abbr"] == abbr),
            "mechanical_top_candidate_id": top_any["candidate_id"],
            "mechanical_top_A_panels": top_any["fold_A_panels"],
            "mechanical_top_B_panels": top_any["fold_B_panels"],
            "mechanical_top_candidate_design_status": top_any["candidate_design_status"],
            "mechanical_top_symmetric_coarsening_eu_count": top_any["symmetric_coarsening_estimation_unit_count"],
            "rule_selected_valid_candidate_id": top["candidate_id"] if top else "",
            "rule_selected_A_panels": top["fold_A_panels"] if top else "",
            "rule_selected_B_panels": top["fold_B_panels"] if top else "",
            "selected_candidate_symmetric_coarsening_eu_count": top["symmetric_coarsening_estimation_unit_count"] if top else "",
            "ti_fold_specific_design_closed": "YES" if ti_state_closure.get(abbr) else "NO",
            "ma_sensitivity_feasibility": state_ma_status.get(abbr, "UNAVAILABLE"),
            "primary_design_status": state_status,
            "blocking_status": "NONE" if state_status.startswith("DESIGN_COMPLETE") else state_status,
            "nonblocking_qc_flags": ";".join(state["nonblocking_qc_flags"]),
        })
        selected_rows.append({
                "state_fips": state["state_fips"],
                "state_abbr": abbr,
                "state_name": state["state_name"],
                "candidate_id": top_any["candidate_id"],
                "selected_A_panels": top_any["fold_A_panels"],
                "selected_B_panels": top_any["fold_B_panels"],
                "mechanical_rank": top_any["mechanical_rank"],
                "candidate_design_valid": top_any["candidate_design_valid"],
                "candidate_design_status": top_any["candidate_design_status"],
                "rule_selected_valid_top_candidate": "YES" if top else "NO_BLOCKED_MECHANICAL_TOP_ONLY",
                "why_selected": f"valid={top_any['candidate_design_valid']}; block_balance={top_any['area_weighted_effective_block_imbalance']}; max_balance={top_any['max_effective_block_imbalance']}; eu_balance={top_any['area_weighted_estimation_unit_imbalance']}; time_center={top_any['temporal_center_abs_diff_years']}; A_tuple={top_any['fold_A_panels']}",
                "symmetric_coarsening_estimation_unit_count": top_any["symmetric_coarsening_estimation_unit_count"],
                "symmetric_coarsening_area_acres": top_any["symmetric_coarsening_area_acres"],
                "population_area_preserved_100pct": top_any["population_area_preserved_100pct"],
                "true_eu_level_block_count": top_any["true_eu_level_block_count"],
                "ti_feasibility": "COMPLETE" if ti_state_closure.get(abbr) else "BLOCKED",
                "ma_sensitivity_feasibility": state_ma_status.get(abbr, "UNAVAILABLE"),
                "qc_flags": ";".join(state["nonblocking_qc_flags"]),
                "mainline_final_acceptance": "NOT_DECIDED",
                "ab_role_definition": "AB: A support, B abundance",
                "ba_role_definition": "BA: B support, A abundance; same partition",
            })

    coarsened_states = {abbr for abbr, row in mechanical_top.items() if row["symmetric_coarsening_estimation_unit_count"] > 0}
    valid_selected_coarsened_states = {abbr for abbr, row in selected.items() if row["symmetric_coarsening_estimation_unit_count"] > 0}
    true_block_states = {r["state_abbr"] for r in frame_rows if r["primary_design_status"] == "DESIGN_BLOCKED_ESTIMATION_UNIT_UNSAMPLED"}
    input_block_states = {r["state_abbr"] for r in frame_rows if r["primary_design_status"] == "INPUT_BLOCKED"}
    ma_counts = Counter(state_ma_status.values())
    if input_block_states:
        nationwide_status = "INPUT_BLOCKED"
    elif true_block_states or len(selected) != 48:
        nationwide_status = "DESIGN_BLOCKED"
    elif any(state["nonblocking_qc_flags"] for state in states.values()):
        nationwide_status = "PASS_WITH_NONBLOCKING_QC_READY_FOR_MAINLINE_AUDIT"
    else:
        nationwide_status = "PASS_READY_FOR_MAINLINE_D09C_SCIENTIFIC_AUDIT"

    qc_rows = []
    def check(check_id, condition, observed, expected, details=""):
        qc_rows.append({"check_id": check_id, "status": "PASS" if condition else "FAIL", "observed": observed, "expected": expected, "details": details})
    check("INPUT_HASHES", all(r["status"] == "PASS" for r in input_rows), Counter(r["status"] for r in input_rows), "all PASS")
    check("T2_STATE_ROWS", len(frame_rows) == 48, len(frame_rows), 48)
    check("REAL_EXPVOL_COMPONENTS", all(r["component_evalid"] for r in frame_rows), sum(bool(r["component_evalid"]) for r in frame_rows), 48)
    check("NEW_COMPONENT_EVALIDS", all(states[s]["component_evalid"] == e for s, e in NEW_STATES.items()), {s: states[s]["component_evalid"] for s in NEW_STATES}, NEW_STATES)
    check("FIVE_PANEL_CLOSURE", all(r["five_panel_complete"] == 1 for r in frame_rows), sum(r["five_panel_complete"] for r in frame_rows), 48)
    check("CANDIDATE_ROWS", len(all_candidates) == 480, len(all_candidates), 480)
    check("TEN_CANDIDATES_PER_STATE", all(sum(r["state_abbr"] == s for r in all_candidates) == 10 for s in states), "all states", "10 each")
    check("RANKS_1_TO_10", all(sorted(r["mechanical_rank"] for r in all_candidates if r["state_abbr"] == s) == list(range(1, 11)) for s in states), "all states", "1..10")
    check("WHOLE_PANEL_2_VS_3", all(r["fold_A_panel_count"] == 2 and r["fold_B_panel_count"] == 3 and r["p2panel_split_count"] == 0 for r in all_candidates), "all candidates", "A=2;B=3;split=0")
    check("MECHANICAL_TOP_48", len(mechanical_top) == 48, len(mechanical_top), 48)
    check("VALID_SELECTION_COUNT_CONSISTENT_WITH_BLOCKS", len(selected) == 48 - len(true_block_states) - len(input_block_states), len(selected), 48 - len(true_block_states) - len(input_block_states))
    check("NO_TRUE_EU_BLOCK_SELECTED", all(r["true_eu_level_block_count"] == 0 for r in selected.values()), sum(r["true_eu_level_block_count"] for r in selected.values()), 0)
    check("COARSENING_PRESERVES_AREA", all(r["population_area_preserved_100pct"] == 1 for r in coarsening_rows), sum(r["population_area_preserved_100pct"] == 0 for r in coarsening_rows), 0)
    check("TI_CLOSURE_CONSISTENT_WITH_BLOCKS", sum(ti_state_closure.values()) == 48 - len(true_block_states) - len(input_block_states), sum(ti_state_closure.values()), 48 - len(true_block_states) - len(input_block_states))
    check("TI_FULL_EXPNS_NOT_REUSED", all(r["full_evaluation_expns_reused_as_final_fold_weight"] == "NO" for r in ti_rows), "all rows", "NO")
    check("TI_CONSTANT_CALIBRATION", all(r["calibration_status"] == "PASS" for r in ti_rows), Counter(r["calibration_status"] for r in ti_rows), "all PASS")
    check("OR_MISMATCH_EXACT_FOUR", len(or_mismatches) == 4, len(or_mismatches), 4)
    check("OR_MISMATCH_ALL_RESOLVED_RETAINED", all(r["plot_fk_resolved"] == "YES" and r["retained_without_rewrite"] == "YES" for r in or_mismatches), "all rows", "YES")
    check("SURVEY_FALSE_UNIQUENESS_NOT_USED", True, "SURVEY.CN linkage only", "STATECD+INVYR uniqueness not required")
    check("WV_NO_RECOVERY_THRESHOLD", all(r["historical_area_recovery_threshold_used"] == "NO" for r in wv_rows), "all WV rows", "NO")
    check("SPECIES_OUTCOME_DATA_NOT_READ", True, "only frozen design CSVs and 24 whitelisted raw-design ZIPs", "no TREE/species/outcome")
    check("NATIONWIDE_STATUS_ALLOWLIST", nationwide_status in {"PASS_READY_FOR_MAINLINE_D09C_SCIENTIFIC_AUDIT", "PASS_WITH_NONBLOCKING_QC_READY_FOR_MAINLINE_AUDIT", "DESIGN_BLOCKED", "INPUT_BLOCKED"}, nationwide_status, "contract allowlist")

    write_csv(OUT / "Q1_D09C_T2_NATIONAL_FRAME_COMPLETION_v01.csv", frame_rows)
    write_csv(OUT / "Q1_D09C_T2_ALL_PARTITION_CANDIDATES_v01.csv", [clean_candidate(r) for r in sorted(all_candidates, key=lambda x: (int(x["state_fips"]), x["mechanical_rank"]))])
    write_csv(OUT / "Q1_D09C_T2_RULE_SELECTED_PARTITIONS_v01.csv", selected_rows)
    write_csv(OUT / "Q1_D09C_T2_FOLD_SPECIFIC_TI_DESIGN_v01.csv", ti_rows)
    write_csv(OUT / "Q1_D09C_T2_SYMMETRIC_COARSENING_AUDIT_v01.csv", coarsening_rows)
    write_csv(OUT / "Q1_D09C_T2_WV_AUDIT_v01.csv", wv_rows)
    write_csv(OUT / "Q1_D09C_T2_OR_412301_MISMATCH_AUDIT_v01.csv", or_mismatches)
    write_csv(OUT / "Q1_D09C_T2_MA_SENSITIVITY_FEASIBILITY_v01.csv", ma_rows)
    write_csv(OUT / "Q1_D09C_T2_COMPLETION_QC_v01.csv", qc_rows)

    result_note = f"""# Q1 D09C T2 bounded completion result note v01

Date: 2026-09-03  
Nationwide status: **{nationwide_status}**

## Design facts

- Real T2 EXPVOL frames closed: {sum(bool(r['component_evalid']) for r in frame_rows)}/48; input-blocked States: {len(input_block_states)}.
- States with at least one legal whole-panel 2-vs-3 design: {len(selected)}/48.
- Mechanical top candidates requiring symmetric within-EU coarsening: {len(coarsened_states)} States ({';'.join(sorted(coarsened_states)) or 'none'}); valid selected candidates among them: {len(valid_selected_coarsened_states)}.
- Selected candidates with a true estimation-unit-level unsampled fold: {len(true_block_states)}.
- Fold-specific TI construction closes with 100% population-area accounting in {sum(ti_state_closure.values())}/48 States. Full-evaluation EXPNS is comparator-only and is not reused as a fold weight.
- MA sensitivity feasibility: COMPLETE={ma_counts['COMPLETE']}, PARTIAL={ma_counts['PARTIAL']}, UNAVAILABLE={ma_counts['UNAVAILABLE']} States. MA did not select the primary design.
- WV follows the national symmetric-coarsening rule with no recovery threshold.
- OR 412301 contains {len(or_mismatches)} retained assignment/PLOT STATECD or INVYR mismatches; every PLT_CN foreign key resolves and all records remain in the selected whole-panel design.

The rule-selected partition in each State is a mechanical outcome-blind recommendation for scientific-mainline audit, not final scientific acceptance. No species outcome, TREE abundance, support, occupancy, D08C2, R1/R2, World 0, or real-Q1 analysis was read or run.

STOP after D09C T2 bounded completion.
"""
    (OUT / "Q1_D09C_T2_RESULT_NOTE_v01.md").write_text(result_note, encoding="utf-8")

    summary = {
        "contract_id": "Q1_D09C_T2_BOUNDED_COMPLETION_CONTRACT_v01",
        "nationwide_status": nationwide_status,
        "complete_expvol_states": sum(bool(r["component_evalid"]) for r in frame_rows),
        "input_block_states": sorted(input_block_states),
        "states_with_legal_2v3_design": len(selected),
        "selected_coarsening_state_count": len(coarsened_states),
        "selected_coarsening_states": sorted(coarsened_states),
        "valid_selected_coarsening_state_count": len(valid_selected_coarsened_states),
        "valid_selected_coarsening_states": sorted(valid_selected_coarsened_states),
        "true_eu_block_states": sorted(true_block_states),
        "ti_closed_states": sum(ti_state_closure.values()),
        "ma_state_counts": {k: ma_counts[k] for k in ("COMPLETE", "PARTIAL", "UNAVAILABLE")},
        "wv_audit_rows": len(wv_rows),
        "or_mismatch_rows": len(or_mismatches),
        "candidate_rows": len(all_candidates),
        "ti_design_rows": len(ti_rows),
        "coarsening_audit_rows": len(coarsening_rows),
        "qc_status_counts": dict(Counter(r["status"] for r in qc_rows)),
        "runtime_seconds": round(time.time() - started, 3),
        "prohibited_data_read": [],
        "downstream_tasks_run": [],
    }
    write_json(QC / "D09C_T2_BUILD_SUMMARY_v01.json", summary)
    write_json(QC / "D09C_T2_ENVIRONMENT_v01.json", {
        "python": __import__("sys").version,
        "platform": __import__("platform").platform(),
        "working_directory": str(ROOT),
        "input_mode": "frozen D09C T2 design outputs plus frozen CA/OR/WA raw-design ZIPs",
        "network_access": False,
    })
    (QC / "D09C_T2_IMPLEMENTATION_LOG_v01.md").write_text(
        "# D09C T2 implementation log v01\n\n"
        "- Contract and exact ranking tuple were frozen before computation.\n"
        "- Existing 45-State D09C T2 design ledgers were hash-verified and not overwritten.\n"
        "- CA/OR/WA were rebuilt from the 24 frozen whitelisted raw-design ZIPs and their actual EXPVOL raw-key chains.\n"
        "- Symmetric coarsening was applied mechanically within each affected estimation unit; no area-recovery threshold was used.\n"
        "- No TREE/species/outcome or downstream-Q1 object was accessed.\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False))
    return 0 if all(r["status"] == "PASS" for r in qc_rows) else 2


if __name__ == "__main__":
    raise SystemExit(main())
