from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import math
import re
import statistics
import zipfile
from collections import defaultdict
from pathlib import Path


EXPECTED_ROWS = {
    "out/truth_v01.csv": 17_524,
    "out/a0_v01.csv": 17_524,
    "out/a1_v01.csv": 35_048,
    "out/a2_v01.csv.gz": 35_048,
    "out/plot_obs_v01.csv.gz": 189_932,
    "out/cell_recovery_v01.csv.gz": 70_096,
    "out/recovery_metrics_v01.csv": 576,
    "out/leakage_v01.csv.gz": 19_504,
    "out/downstream_v01.csv": 180,
    "out/separation_v01.csv": 90,
    "out/common_compare_v01.csv": 18,
    "out/orientation_v01.csv": 25,
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read_rows(path: Path):
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8-sig", newline="") as handle:
        yield from csv.DictReader(handle)


def count_rows(path: Path) -> int:
    return sum(1 for _ in read_rows(path))


def median(values):
    return statistics.median(values)


def validate_package(pkg: Path) -> dict:
    checks = []

    def add(check_id: str, passed: bool, observed, expected, notes=""):
        checks.append({
            "check_id": check_id,
            "status": "PASS" if passed else "FAIL",
            "observed": observed,
            "expected": expected,
            "notes": notes,
        })

    required = [
        "control/contract_v01.md",
        "out/layer_ledger_v01.csv",
        "out/a2_impl_v01.csv",
        "out/cell_recovery_v01.csv.gz",
        "out/map_recovery_v01.csv",
        "out/leakage_v01.csv.gz",
        "out/downstream_v01.csv",
        "out/separation_v01.csv",
        "out/orientation_v01.csv",
        "out/common_compare_v01.csv",
        "out/result_note_v01.md",
        "out/audit_v01.xlsx",
        "qc/input_id_v01.csv",
        "qc/checks_v01.csv",
        "qc/build_summary_v01.json",
        "manifest/registry_delta_v01.csv",
        "src/build.py",
        "src/audit.mjs",
        "src/verify_xlsx.mjs",
        "src/finalize.py",
        "src/verify.py",
        "src/run_all.ps1",
    ]
    missing = [name for name in required if not (pkg / name).is_file()]
    add("REQUIRED_FILES", not missing, len(required) - len(missing), len(required), "; ".join(missing))

    input_rows = list(read_rows(pkg / "qc/input_id_v01.csv"))
    bad_identity = [r["asset"] for r in input_rows if r.get("status") != "PASS"]
    hash_bad = [r["asset"] for r in input_rows if re.fullmatch(r"[0-9a-f]{64}", r.get("expected_sha256", "")) and r.get("expected_sha256") != r.get("actual_sha256")]
    add("INPUT_IDENTITIES", len(input_rows) == 7 and not bad_identity and not hash_bad, len(input_rows), 7, f"bad_status={bad_identity}; bad_hash={hash_bad}")

    qc_rows = list(read_rows(pkg / "qc/checks_v01.csv"))
    qc_fail = [r["check_id"] for r in qc_rows if r.get("status") != "PASS"]
    add("BUILD_QC", len(qc_rows) == 12 and not qc_fail, len(qc_rows), 12, f"nonpass={qc_fail}")

    observed_counts = {}
    for rel, expected in EXPECTED_ROWS.items():
        n = count_rows(pkg / rel)
        observed_counts[rel] = n
        add(f"ROWS_{Path(rel).name.upper().replace('.', '_')}", n == expected, n, expected)

    truth = list(read_rows(pkg / "out/truth_v01.csv"))
    a0 = list(read_rows(pkg / "out/a0_v01.csv"))
    species = sorted({r["synthetic_species_id"] for r in truth})
    expected_species = [f"SYN{i:03d}" for i in range(1, 73)]
    worlds = sorted({r["world"] for r in truth})
    add("SYNTHETIC_UNIVERSE", species == expected_species and worlds == ["PAIRED_NULL", "STRONG"], {"species": len(species), "worlds": worlds}, {"species": 72, "worlds": ["PAIRED_NULL", "STRONG"]})
    add("A0_EXACT_TRUTH", all(r0["synthetic_species_id"] == rt["synthetic_species_id"] and r0["world"] == rt["world"] and r0["cell_50km"] == rt["cell_50km"] and math.isclose(float(r0["latent_cell_mass"]), float(rt["latent_cell_mass"]), rel_tol=0, abs_tol=1e-9) for r0, rt in zip(a0, truth)), len(a0), len(truth))

    truth_sums = defaultdict(float)
    for r in truth:
        truth_sums[(r["synthetic_species_id"], r["world"])] += float(r["latent_allocation"])
    truth_max = max(abs(v - 1.0) for v in truth_sums.values())
    add("TRUTH_NORMALIZATION", truth_max <= 1e-12, truth_max, "<=1e-12")

    a2_rows = list(read_rows(pkg / "out/a2_v01.csv.gz"))
    a2_sums = defaultdict(float)
    structural_bad = []
    for r in a2_rows:
        key = (r["synthetic_species_id"], r["world"], r["orientation"])
        a2_sums[key] += float(r["normalized_allocation"])
        if r["structural_zero_exposure"] == "YES" and (float(r["estimated_cell_mass"]) != 0.0 or int(float(r["plot_count"])) != 0):
            structural_bad.append(key + (r["cell_50km"],))
    a2_norm_max = max(abs(v - 1.0) for v in a2_sums.values())
    add("A2_NORMALIZATION", a2_norm_max <= 1e-12, a2_norm_max, "<=1e-12")
    add("A2_STRUCTURAL_ZERO_RULE", not structural_bad, len(structural_bad), 0)

    plot_mass = defaultdict(float)
    plot_species = set()
    with gzip.open(pkg / "out/plot_obs_v01.csv.gz", "rt", encoding="utf-8-sig", newline="") as handle:
        for r in csv.DictReader(handle):
            key = (r["synthetic_species_id"], r["world"], r["orientation"], r["cell_50km"])
            plot_mass[key] += float(r["weighted_cell_mass"])
            plot_species.add(r["synthetic_species_id"])
    max_mass_diff = 0.0
    for r in a2_rows:
        key = (r["synthetic_species_id"], r["world"], r["orientation"], r["cell_50km"])
        max_mass_diff = max(max_mass_diff, abs(float(r["estimated_cell_mass"]) - plot_mass.get(key, 0.0)))
    add("A2_PLOT_TO_CELL_RECONSTRUCTION", max_mass_diff <= 1e-6, max_mass_diff, "<=1e-6")
    add("NO_REAL_SPECIES_IDS", plot_species <= set(expected_species), len(plot_species - set(expected_species)), 0)

    recovery = list(read_rows(pkg / "out/recovery_metrics_v01.csv"))
    h_a1 = median([float(r["hellinger_distance"]) for r in recovery if r["layer"] == "A1"])
    h_a2 = median([float(r["hellinger_distance"]) for r in recovery if r["layer"] == "A2"])
    sw_a1 = median([float(r["sliced_wasserstein_km"]) for r in recovery if r["layer"] == "A1"])
    sw_a2 = median([float(r["sliced_wasserstein_km"]) for r in recovery if r["layer"] == "A2"])
    add("RECOVERY_IMPROVEMENT_FACT", h_a2 < h_a1 and sw_a2 < sw_a1, {"A1_H": h_a1, "A2_H": h_a2, "A1_SW": sw_a1, "A2_SW": sw_a2}, "A2 lower than A1; descriptive only")

    common = list(read_rows(pkg / "out/common_compare_v01.csv"))
    separation = {}
    for layer in ["A0", "A1", "A2"]:
        separation[layer] = median([float(r["strong_minus_null_geometry_gain_pct_median"]) for r in common if r["layer"] == layer])
    expected_sep = {"A0": 6.05399724982147, "A1": -127.88865001066259, "A2": -26.285067058946254}
    sep_diff = max(abs(separation[k] - expected_sep[k]) for k in expected_sep)
    add("DOWNSTREAM_SEPARATION_REPRODUCTION", sep_diff <= 1e-12, separation, expected_sep)

    leak_values = []
    with gzip.open(pkg / "out/leakage_v01.csv.gz", "rt", encoding="utf-8-sig", newline="") as handle:
        for r in csv.DictReader(handle):
            if r["analysis_level"] == "POOLED_WITHIN_SPECIES_CORRELATION" and r["layer"] == "A2" and r["outcome"] == "p_residual":
                leak_values.append(abs(float(r["value"])))
    max_leak = max(leak_values)
    add("A2_POOLED_RESIDUAL_LEAKAGE_REPRODUCTION", len(leak_values) == 16 and abs(max_leak - 0.20792108740741067) <= 1e-12, {"n": len(leak_values), "max_abs_r": max_leak}, {"n": 16, "max_abs_r": 0.20792108740741067})

    summary = json.loads((pkg / "qc/build_summary_v01.json").read_text(encoding="utf-8"))
    add("TERMINAL_STATUS", summary.get("terminal_status") == "ABUNDANCE_CALIBRATION_COMPLETE_READY_FOR_MAINLINE_FREEZE", summary.get("terminal_status"), "ABUNDANCE_CALIBRATION_COMPLETE_READY_FOR_MAINLINE_FREEZE")
    scope_ok = summary.get("network_used") is False and summary.get("real_species_read") is False and summary.get("support_recovery_run") is False and summary.get("real_q1_run") is False
    add("SCOPE_FIREWALL", scope_ok, {k: summary.get(k) for k in ["network_used", "real_species_read", "support_recovery_run", "real_q1_run"]}, "all false")

    workbook_ok = (pkg / "out/audit_v01.xlsx").stat().st_size > 0
    error_text = (pkg / "qc/audit_errors_v01.ndjson").read_text(encoding="utf-8")
    render = json.loads((pkg / "qc/audit_render_v01.json").read_text(encoding="utf-8"))
    post_xlsx = json.loads((pkg / "qc/xlsx_validation_v01.json").read_text(encoding="utf-8"))
    add("AUDIT_WORKBOOK", workbook_ok and "matched 0 entries" in error_text and render.get("status") == "PASS" and len(render.get("renders", [])) == 5 and post_xlsx.get("status") == "PASS", {"bytes": (pkg / "out/audit_v01.xlsx").stat().st_size, "renders": len(render.get("renders", [])), "postimport": post_xlsx.get("status")}, "nonempty workbook; zero formula errors; 5 renders; post-import PASS")

    files = [p for p in pkg.rglob("*") if p.is_file()]
    max_abs_path = max((len(str(p.resolve())), str(p.resolve())) for p in files)
    max_member = max((len(p.relative_to(pkg).as_posix()), p.relative_to(pkg).as_posix()) for p in files)
    add("WINDOWS_PATH_LIMIT", max_abs_path[0] < 256 and max_member[0] < 256, {"max_abs_chars": max_abs_path[0], "max_abs_path": max_abs_path[1], "max_member_chars": max_member[0], "max_member": max_member[1]}, "both <256")

    return {
        "task_id": "D10C_FIA_DESIGN_BASED_ABUNDANCE_MEASUREMENT_CALIBRATION_RESUME_v01",
        "terminal_status": "ABUNDANCE_CALIBRATION_COMPLETE_READY_FOR_MAINLINE_FREEZE",
        "validation_status": "PASS" if all(c["status"] == "PASS" for c in checks) else "FAIL",
        "scientific_pass_fail_assigned": False,
        "row_counts": observed_counts,
        "key_results": {
            "median_hellinger_A1": h_a1,
            "median_hellinger_A2": h_a2,
            "median_sliced_wasserstein_km_A1": sw_a1,
            "median_sliced_wasserstein_km_A2": sw_a2,
            "strong_minus_paired_null_downstream_separation_pp": separation,
            "max_abs_A2_pooled_within_species_p_residual_r": max_leak,
        },
        "checks": checks,
    }


def validate_zip(zip_path: Path, pkg_report: dict) -> dict:
    sidecar = Path(str(zip_path) + ".sha256")
    expected = sidecar.read_text(encoding="utf-8").split()[0]
    actual = sha256(zip_path)
    with zipfile.ZipFile(zip_path) as zf:
        bad_member = zf.testzip()
        names = zf.namelist()
        member_max = max((len(n), n) for n in names)
        manifest_rows = list(csv.DictReader(zf.read("manifest/sha256sums_v01.csv").decode("utf-8-sig").splitlines()))
        hash_bad = []
        size_bad = []
        for row in manifest_rows:
            payload = zf.read(row["relative_path"])
            if hashlib.sha256(payload).hexdigest() != row["sha256"]:
                hash_bad.append(row["relative_path"])
            if len(payload) != int(row["size_bytes"]):
                size_bad.append(row["relative_path"])
        deterministic_times = sorted({info.date_time for info in zf.infolist()})
    checks = {
        "zip_sha256_matches_sidecar": actual == expected,
        "zip_integrity": bad_member is None,
        "internal_hash_manifest": not hash_bad and not size_bad,
        "deterministic_member_timestamps": deterministic_times == [(1980, 1, 1, 0, 0, 0)],
        "zip_member_paths_lt_256": member_max[0] < 256,
        "package_validation_pass": pkg_report.get("validation_status") == "PASS",
    }
    return {
        "status": "PASS" if all(checks.values()) else "FAIL",
        "zip_path": str(zip_path),
        "zip_size_bytes": zip_path.stat().st_size,
        "zip_sha256": actual,
        "sidecar_path": str(sidecar),
        "member_count": len(names),
        "max_zip_member_chars": member_max[0],
        "max_zip_member": member_max[1],
        "checks": checks,
        "hash_failures": hash_bad,
        "size_failures": size_bad,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pkg", type=Path, required=True)
    parser.add_argument("--zip", dest="zip_path", type=Path)
    parser.add_argument("--write", type=Path)
    args = parser.parse_args()
    report = validate_package(args.pkg.resolve())
    if args.zip_path:
        report["postpackage"] = validate_zip(args.zip_path.resolve(), report)
        if report["postpackage"]["status"] != "PASS":
            report["validation_status"] = "FAIL"
    payload = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.write:
        args.write.write_text(payload, encoding="utf-8")
    print(payload, end="")
    raise SystemExit(0 if report["validation_status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
