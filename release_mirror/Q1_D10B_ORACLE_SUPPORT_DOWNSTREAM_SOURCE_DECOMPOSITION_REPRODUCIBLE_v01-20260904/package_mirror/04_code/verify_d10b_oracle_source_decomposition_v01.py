#!/usr/bin/env python3
"""Independent structural and arithmetic verification for frozen D10B outputs."""

from __future__ import annotations

import csv
import json
import math
import zipfile
from pathlib import Path


ROOT = Path(r"C:\range_paper")
OUT = ROOT / "04_derived" / "d10b_oracle_source_decomposition_v01"
QC = ROOT / "05_qc" / "d10b_oracle_source_decomposition_v01"
D10A = ROOT / "10_archive" / "d10a_real_layout_nonoracle_v01" / "Q1_D10A_REAL_LAYOUT_NONORACLE_OBSERVATION_CALIBRATION_REPRODUCIBLE_v01.zip"
D10A_ROOT = "Q1_D10A_REAL_LAYOUT_NONORACLE_OBSERVATION_CALIBRATION_REPRODUCIBLE_v01/"


def read_csv(path):
    with Path(path).open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path, rows):
    rows = list(rows)
    with Path(path).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def close(left, right, tolerance=1e-9):
    return math.isclose(float(left), float(right), rel_tol=tolerance, abs_tol=tolerance)


def main():
    identities = read_csv(OUT / "Q1_D10B_ORACLE_WORLD_IDENTITIES_v01.csv")
    l0 = read_csv(OUT / "Q1_D10B_L0_ORACLE_SUPPORT_LATENT_ABUNDANCE_RESULTS_v01.csv")
    l1 = read_csv(OUT / "Q1_D10B_L1_ORACLE_SUPPORT_OBSERVED_ABUNDANCE_RESULTS_v01.csv")
    l2 = read_csv(OUT / "Q1_D10B_L2_D10A_REFERENCE_RESULTS_v01.csv")
    decomposition = read_csv(OUT / "Q1_D10B_NULL_GAIN_SOURCE_DECOMPOSITION_v01.csv")
    separation = read_csv(OUT / "Q1_D10B_STRONG_NULL_SEPARATION_v01.csv")
    summary = read_csv(OUT / "Q1_D10B_DIAGNOSTIC_SUMMARY_v01.csv")
    checks = []

    def add(check_id, passed, observed, expected):
        checks.append({"check_id": check_id, "status": "PASS" if passed else "FAIL", "observed": str(observed), "expected": str(expected)})

    add("IDENTITY_UNIQUE_KEYS", len({(r["synthetic_species_id"], r["world"]) for r in identities}) == 144, len({(r["synthetic_species_id"], r["world"]) for r in identities}), 144)
    add("IDENTITY_ALL_PASS", all(r["identity_gate"] == "PASS" for r in identities), sum(r["identity_gate"] == "PASS" for r in identities), 144)
    for name, rows, expected in (("L0", l0, 60), ("L1", l1, 60), ("L2", l2, 180), ("DECOMPOSITION", decomposition, 90), ("SEPARATION", separation, 150), ("SUMMARY", summary, 30)):
        add(name + "_ROW_COUNT", len(rows) == expected, len(rows), expected)

    key_fields = ("world", "observation_regime", "orientation", "split_seed", "model")
    for name, rows in (("L0", l0), ("L1", l1), ("L2", l2)):
        keys = {tuple(row[field] for field in key_fields) for row in rows}
        add(name + "_UNIQUE_KEYS", len(keys) == len(rows), len(keys), len(rows))

    metric_fields = (
        "latent_truth_geometry_gain_pct", "predictive_set_gain_pct", "observed_map_error_gain_pct",
        "geometry_latent_truth_coverage", "geometry_observed_map_coverage",
        "world0_latent_truth_coverage", "world0_observed_map_coverage",
        "world0_set_diameter", "geometry_set_diameter",
        "world0_latent_truth_error", "geometry_latent_truth_error",
    )
    add("ALL_METRICS_FINITE", all(math.isfinite(float(row[field])) for row in l0 + l1 + l2 for field in metric_fields), "FINITE", "FINITE")
    add("COVERAGE_BOUNDS", all(0 <= float(row[field]) <= 1 for row in l0 + l1 + l2 for field in ("geometry_latent_truth_coverage", "geometry_observed_map_coverage", "world0_latent_truth_coverage", "world0_observed_map_coverage")), "WITHIN_0_1", "WITHIN_0_1")

    def invariant_duplicates(rows, ignored):
        fields = [field for field in rows[0] if field not in ignored]
        groups = {}
        for row in rows:
            key = tuple(row[field] for field in fields)
            groups.setdefault(key, 0)
            groups[key] += 1
        return groups

    l0_regime = invariant_duplicates(l0, {"observation_regime"})
    l1_regime = invariant_duplicates(l1, {"observation_regime"})
    add("L0_REGIME_STRUCTURAL_DUPLICATION", len(l0_regime) == 20 and set(l0_regime.values()) == {3}, f"{len(l0_regime)}|{set(l0_regime.values())}", "20|{3}")
    add("L1_REGIME_STRUCTURAL_DUPLICATION", len(l1_regime) == 20 and set(l1_regime.values()) == {3}, f"{len(l1_regime)}|{set(l1_regime.values())}", "20|{3}")

    with zipfile.ZipFile(D10A) as archive:
        member = D10A_ROOT + "02_outputs/Q1_D10A_LEAKAGE_AUDIT_RESULTS_v01.csv"
        with archive.open(member) as binary:
            import io
            released = list(csv.DictReader(io.TextIOWrapper(binary, encoding="utf-8-sig", newline="")))
    l2_by_key = {tuple(r[field] for field in key_fields): r for r in l2}
    exact = True
    for source in released:
        key = tuple(source[field] for field in key_fields)
        target = l2_by_key.get(key)
        if target is None:
            exact = False
            break
        for field, value in source.items():
            if field in {"model", "world", "observation_regime", "orientation"}:
                exact &= target[field] == value
            else:
                exact &= close(target[field], value)
    add("L2_NUMERICALLY_EXACT_DIRECT_REFERENCE", exact, "MATCH" if exact else "MISMATCH", "MATCH")

    l0_index = {(r["world"], r["observation_regime"], r["orientation"], r["split_seed"]): r for r in l0}
    l1_index = {(r["world"], r["observation_regime"], r["orientation"], r["split_seed"]): r for r in l1}
    l2_index = {(r["world"], r["observation_regime"], r["orientation"], r["split_seed"], r["model"]): r for r in l2}
    arithmetic_ok = True
    for row in decomposition:
        base = (row["world"], row["observation_regime"], row["orientation"], row["split_seed"])
        a, b, c = l0_index[base], l1_index[base], l2_index[base + (row["l2_model"],)]
        for metric in ("latent_truth_geometry_gain", "predictive_set_gain", "observed_map_error_gain"):
            source = metric + "_pct"
            arithmetic_ok &= close(row["comparator_component_" + metric + "_pct"], a[source])
            arithmetic_ok &= close(row["abundance_observation_increment_" + metric + "_pct"], float(b[source]) - float(a[source]))
            arithmetic_ok &= close(row["support_recovery_increment_" + metric + "_pct"], float(c[source]) - float(b[source]))
    add("SOURCE_DECOMPOSITION_ARITHMETIC", arithmetic_ok, "MATCH" if arithmetic_ok else "MISMATCH", "MATCH")

    all_index = {}
    for row in l0 + l1 + l2:
        all_index[(row["layer"], row["model"], row["world"], row["observation_regime"], row["orientation"], row["split_seed"])] = row
    separation_ok = True
    for row in separation:
        prefix = (row["layer"], row["model"])
        suffix = (row["observation_regime"], row["orientation"], row["split_seed"])
        strong = all_index[prefix + ("STRONG",) + suffix]
        null = all_index[prefix + ("PAIRED_NULL",) + suffix]
        for metric in ("latent_truth_geometry_gain_pct", "predictive_set_gain_pct", "observed_map_error_gain_pct"):
            separation_ok &= close(row["strong_minus_paired_null_" + metric], float(strong[metric]) - float(null[metric]))
    add("STRONG_NULL_SEPARATION_ARITHMETIC", separation_ok, "MATCH" if separation_ok else "MISMATCH", "MATCH")

    note = (OUT / "Q1_D10B_RESULT_NOTE_v01.md").read_text(encoding="utf-8")
    add("RESULT_NOTE_Q1_TO_Q5", all(f"## Q{i}" in note for i in range(1, 6)), "PRESENT", "PRESENT")
    add("NO_SCIENTIFIC_PASS_FAIL", "defines no scientific PASS/FAIL" in note, "NOT_DEFINED", "NOT_DEFINED")
    add("NO_REAL_Q1", "no repair, D10C, real-species" in note, "NO", "NO")

    status = "PASS" if all(row["status"] == "PASS" for row in checks) else "FAIL"
    write_csv(QC / "D10B_INDEPENDENT_POSTRUN_VALIDATION_CHECKS_v01.csv", checks)
    (QC / "D10B_INDEPENDENT_POSTRUN_VALIDATION_v01.json").write_text(json.dumps({"status": status, "checks": len(checks), "checks_passed": sum(row["status"] == "PASS" for row in checks), "real_q1_run": False, "network_used": False}, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": status, "checks": len(checks)}, indent=2))
    if status != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
