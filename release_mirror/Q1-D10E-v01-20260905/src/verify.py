from __future__ import annotations

import csv
import gzip
import hashlib
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(r"C:\range_paper")
PKG = ROOT / "10_archive" / "d10e" / "pkg"
OUT = PKG / "out"
QC = PKG / "qc"
CTL = PKG / "control"
TERMINAL = "ABUNDANCE_MEASUREMENT_NOISE_DECOMPOSITION_COMPLETE_READY_FOR_MAINLINE"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def csv_rows(path: Path) -> list[dict]:
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def numeric(value) -> float:
    return float(value)


def close(left, right, atol=1e-10, rtol=1e-10) -> bool:
    return bool(np.isclose(float(left), float(right), atol=atol, rtol=rtol, equal_nan=False))


def main() -> None:
    checks: list[dict] = []

    def add(check_id: str, passed: bool, observed, expected, note: str = "") -> None:
        checks.append({
            "check_id": check_id,
            "status": "PASS" if passed else "FAIL",
            "observed": observed,
            "expected": expected,
            "note": note,
        })

    required = [
        CTL / "request.txt",
        CTL / "contract_v01.md",
        CTL / "Q1_D10E_OBSERVATION_STOCHASTIC_HIERARCHY_v01.md",
        CTL / "stochastic_ledger_v01.csv",
        OUT / "e0_repro_v01.csv",
        OUT / "e1_repro_v01.csv",
        OUT / "e2_summary_v01.csv",
        OUT / "e3_summary_v01.csv",
        OUT / "e4_summary_v01.csv",
        OUT / "e5_summary_v01.csv",
        OUT / "state_summary_v01.csv",
        OUT / "source_decomp_v01.csv",
        OUT / "orientation_decomp_v01.csv",
        OUT / "world_decomp_v01.csv",
        OUT / "map_recovery_v01.csv",
        OUT / "map_recovery_summary_v01.csv",
        OUT / "maps_v01.csv.gz",
        OUT / "e5_realization_summary_v01.csv",
        OUT / "e5_downstream_v01.csv.gz",
        OUT / "e5_test_detail_v01.csv.gz",
        OUT / "k_ladder_blocks_v01.csv",
        OUT / "k_ladder_summary_v01.csv",
        OUT / "uncertainty_cells_v01.csv.gz",
        OUT / "uncertainty_summary_v01.csv",
        OUT / "information_profiles_v01.csv",
        OUT / "information_relationships_v01.csv",
        OUT / "mc_convergence_v01.csv",
        OUT / "current_deviation_v01.csv",
        OUT / "panel_extension_v01.csv",
        OUT / "Q1_D10E_RESULT_NOTE_v01.md",
        QC / "input_id_v01.csv",
        QC / "checks_v01.csv",
        QC / "build_summary_v01.json",
        QC / "environment_v01.json",
        PKG / "manifest" / "REGISTRY_DELTA_v01.csv",
    ]
    missing = [str(path.relative_to(PKG)) for path in required if not path.is_file()]
    add("REQUIRED_CORE_FILES", not missing, ";".join(missing) if missing else len(required), len(required))
    if missing:
        raise RuntimeError("Independent validation cannot continue with missing core files")

    build = json.loads((QC / "build_summary_v01.json").read_text(encoding="utf-8"))
    add("TERMINAL_STATUS", build.get("terminal_status") == TERMINAL, build.get("terminal_status"), TERMINAL)
    add("BOUNDARY_FLAGS", all(build.get(name) is False for name in (
        "network_used", "real_species_read", "A2_modified", "support_recovery_run",
        "uncertainty_model_fitted", "real_world0_run", "real_q1_run",
        "scientific_pass_hold_fail_assigned",
    )), "all prohibited-action flags false", "all prohibited-action flags false")

    input_ids = csv_rows(QC / "input_id_v01.csv")
    add("INPUT_ID_ROWS", len(input_ids) == 14, len(input_ids), 14)
    add("INPUT_ID_STATUS", all(row["status"] == "PASS" for row in input_ids), Counter(row["status"] for row in input_ids), "all PASS")
    compute_checks = csv_rows(QC / "checks_v01.csv")
    add("COMPUTE_CHECKS", len(compute_checks) == 16 and all(row["status"] == "PASS" for row in compute_checks), Counter(row["status"] for row in compute_checks), "16 PASS")

    state = pd.read_csv(OUT / "state_summary_v01.csv", encoding="utf-8-sig")
    add("STATE_ROWS", len(state) == 54, len(state), 54)
    add("STATE_KEYS", not state.duplicated(["state", "observation_regime", "orientation"]).any(), int(state.duplicated(["state", "observation_regime", "orientation"]).sum()), 0)
    add("STATE_COVERAGE", set(state.state) == set(f"E{i}" for i in range(6)) and set(state.observation_regime) == {"O1", "O2", "O3"} and set(state.orientation) == {"AB", "BA", "ALL"}, "complete", "E0-E5 x O1-O3 x AB/BA/ALL")
    regime_spread = state.groupby(["state", "orientation"])[["strong_gain_pp", "paired_null_gain_pp", "separation_pp"]].agg(lambda values: float(np.max(values) - np.min(values))).to_numpy(float)
    add("REGIME_INVARIANCE", float(np.max(np.abs(regime_spread))) <= 1e-12, float(np.max(np.abs(regime_spread))), "<=1e-12")
    o1_all = state[(state.observation_regime == "O1") & (state.orientation == "ALL")].set_index("state")
    state_match = all(close(o1_all.loc[name, "separation_pp"], value, atol=1e-12, rtol=0) for name, value in build["state_pooled_separation_pp"].items())
    add("BUILD_STATE_SUMMARY_MATCH", state_match, "checked E0-E5", "exact within 1e-12")

    e0 = csv_rows(OUT / "e0_repro_v01.csv")
    e1 = csv_rows(OUT / "e1_repro_v01.csv")
    add("E0_E1_ROWS", len(e0) == 60 and len(e1) == 60, f"{len(e0)},{len(e1)}", "60,60")
    add("E0_E1_FROZEN_UNIVERSE", all(int(row["n_species"]) == 72 and row["model"] == "ORACLE" for row in e0 + e1), "72-species oracle summaries", "72 species and ORACLE model")

    source = pd.read_csv(OUT / "source_decomp_v01.csv", encoding="utf-8-sig")
    add("DECOMPOSITION_ROWS", len(source) == 108, len(source), 108)
    row_diff = np.max(np.abs(source.component_value_pp - (source.left_value_pp - source.right_value_pp)))
    add("DECOMPOSITION_ROW_ARITHMETIC", row_diff <= 1e-12, float(row_diff), "<=1e-12")
    expected_components = {
        "A_SYSTEMATIC_MEASUREMENT_OPERATOR",
        "B_NORMALIZATION_NONLINEARITY",
        "C_FINITE_REALIZATION_DOWNSTREAM",
        "D_CURRENT_REALIZATION_DEVIATION",
    }
    add("DECOMPOSITION_COMPONENT_SET", set(source.component) == expected_components, sorted(set(source.component)), sorted(expected_components))
    max_telescope = 0.0
    for (regime, orientation, metric), group in source.groupby(["observation_regime", "orientation", "metric"]):
        actual = float(group.component_value_pp.sum())
        expected = float(o1_all.loc["E1", metric] - o1_all.loc["E0", metric]) if orientation == "ALL" else float(
            state[(state.state == "E1") & (state.observation_regime == regime) & (state.orientation == orientation)][metric].iloc[0]
            - state[(state.state == "E0") & (state.observation_regime == regime) & (state.orientation == orientation)][metric].iloc[0]
        )
        max_telescope = max(max_telescope, abs(actual - expected))
    add("DECOMPOSITION_TELESCOPES", max_telescope <= 1e-10, max_telescope, "<=1e-10")

    mc = pd.read_csv(OUT / "mc_convergence_v01.csv", encoding="utf-8-sig")
    last = mc.iloc[-1]
    add("MC_ACCEPTED", int(last.realizations) == int(build["accepted_MC_realizations"]) == 200, int(last.realizations), 200)
    add("MC_PRECISION", last.precision_reached == "YES" and numeric(last.pooled_separation_mcse_pp) <= 0.25 and numeric(last.AB_separation_mcse_pp) <= 0.50 and numeric(last.BA_separation_mcse_pp) <= 0.50, f"{last.pooled_separation_mcse_pp},{last.AB_separation_mcse_pp},{last.BA_separation_mcse_pp}", "<=0.25,<=0.50,<=0.50")

    realizations = pd.read_csv(OUT / "e5_realization_summary_v01.csv", encoding="utf-8-sig")
    add("E5_REALIZATION_ROWS", len(realizations) == 200 and realizations.observation_realization.nunique() == 200, len(realizations), 200)
    e5 = pd.read_csv(OUT / "e5_summary_v01.csv", encoding="utf-8-sig")
    max_e5 = 0.0
    for _, row in e5.iterrows():
        prefix = "pooled" if row.orientation == "ALL" else row.orientation
        values = realizations[f"{prefix}_{row.metric}"].to_numpy(float)
        max_e5 = max(max_e5, abs(float(row["mean"]) - float(np.mean(values))))
    add("E5_SUMMARY_RECONSTRUCTION", max_e5 <= 1e-12, max_e5, "<=1e-12")

    ladder = pd.read_csv(OUT / "k_ladder_blocks_v01.csv", encoding="utf-8-sig")
    expected_blocks = {1: 200, 2: 100, 4: 50, 8: 25, 16: 12, 32: 6}
    observed_blocks = {int(k): int(group.block.nunique()) for k, group in ladder.groupby("K")}
    per_orientation_ok = all(len(ladder[(ladder.K == k) & (ladder.orientation == orientation)]) == count for k, count in expected_blocks.items() for orientation in ("AB", "BA"))
    add("K_LADDER_BLOCK_COUNTS", observed_blocks == expected_blocks and per_orientation_ok, observed_blocks, expected_blocks)
    ladder_summary = pd.read_csv(OUT / "k_ladder_summary_v01.csv", encoding="utf-8-sig")
    max_ladder = 0.0
    for _, row in ladder_summary.iterrows():
        values = ladder[(ladder.K == row.K) & (ladder.orientation == row.orientation)][row.metric].to_numpy(float)
        max_ladder = max(max_ladder, abs(float(row["mean"]) - float(np.mean(values))))
    add("K_LADDER_SUMMARY_RECONSTRUCTION", max_ladder <= 1e-12, max_ladder, "<=1e-12")

    maps = csv_rows(OUT / "maps_v01.csv.gz")
    map_counts = Counter(row["state"] for row in maps)
    add("MAP_ROWS_BY_STATE", map_counts == Counter({name: 33200 for name in ("E0", "E1", "E2", "E3", "E4")}), dict(map_counts), "33,200 per state")
    map_key_counts = Counter((row["state"], row["synthetic_species_id"], row["world"], row["orientation"], row["cell_50km"]) for row in maps)
    add("MAP_KEY_UNIQUENESS", max(map_key_counts.values(), default=0) == 1, max(map_key_counts.values(), default=0), 1)

    uncertainty = pd.read_csv(OUT / "uncertainty_summary_v01.csv", encoding="utf-8-sig")
    coverage_cols = [
        "empirical_central95_truth_containment_fraction",
        "current_E1_poisson_interval_coverage",
        "empirical_variance_normal_interval_coverage_mean",
        "poisson_plugin_interval_coverage_mean",
    ]
    coverage_ok = all(((uncertainty[col] >= 0) & (uncertainty[col] <= 1)).all() for col in coverage_cols)
    add("UNCERTAINTY_SUMMARY", len(uncertainty) == 4 and int(uncertainty.profile_cells.sum()) == 33200 and coverage_ok, f"rows={len(uncertainty)},cells={int(uncertainty.profile_cells.sum())}", "4 rows,33,200 cells,coverage in [0,1]")

    info = pd.read_csv(OUT / "information_profiles_v01.csv", encoding="utf-8-sig")
    info_ids_ok = info.synthetic_species_id.str.fullmatch(r"SYN\d{3}").all()
    add("INFORMATION_PROFILES", len(info) == 288 and info_ids_ok and set(info.orientation) == {"AB", "BA"}, len(info), 288)
    relationships = pd.read_csv(OUT / "information_relationships_v01.csv", encoding="utf-8-sig")
    add("INFORMATION_RELATIONSHIPS", len(relationships) == 144 and set(relationships.threshold_applied) == {"NO"}, len(relationships), 144)

    panel = csv_rows(OUT / "panel_extension_v01.csv")
    add("OPTIONAL_PANEL_AUTHORITY", len(panel) == 1 and panel[0]["status"].startswith("NOT_ENTERED"), panel[0]["status"] if panel else "missing", "NOT_ENTERED")

    long_paths = [str(path.relative_to(PKG)).replace("\\", "/") for path in PKG.rglob("*") if path.is_file() and len(str(path.resolve())) >= 256]
    add("PATH_LENGTHS", not long_paths, max((len(str(path.resolve())) for path in PKG.rglob("*") if path.is_file()), default=0), "<256")

    status = "PASS" if all(check["status"] == "PASS" for check in checks) else "FAIL"
    report = {
        "task_id": build["task_id"],
        "terminal_status": build["terminal_status"],
        "status": status,
        "checks_total": len(checks),
        "checks_passed": sum(check["status"] == "PASS" for check in checks),
        "checks_failed": [check["check_id"] for check in checks if check["status"] != "PASS"],
        "core_output_sha256": {str(path.relative_to(PKG)).replace("\\", "/"): sha256_file(path) for path in required},
    }
    QC.mkdir(parents=True, exist_ok=True)
    with (QC / "independent_checks_v01.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(checks[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(checks)
    (QC / "independent_validation_v01.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    if status != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
