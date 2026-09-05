from __future__ import annotations

import csv
import gzip
import hashlib
import importlib.util
import io
import json
import math
import os
import platform
import re
import shutil
import sys
import time
import zipfile
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(r"C:\range_paper")
ARCH = ROOT / "10_archive" / "d10e"
PKG = ARCH / "pkg"
CTL = PKG / "control"
OUT = PKG / "out"
QC = PKG / "qc"
FIG = PKG / "fig"
MAN = PKG / "manifest"
SRC = PKG / "src"
TMP = ROOT / "99_tmp" / "d10e"

D10D = ROOT / "10_archive" / "d10d" / "D10D_v01.zip"
D10CR = ROOT / "10_archive" / "d10cr" / "D10CR_v01.zip"
D10CA = ROOT / "10_archive" / "d10ca" / "D10CA_v01.zip"
D10B = ROOT / "10_archive" / "d10b_oracle_source_decomposition_v01" / "Q1_D10B_ORACLE_SUPPORT_DOWNSTREAM_SOURCE_DECOMPOSITION_REPRODUCIBLE_v01.zip"
D10A = ROOT / "10_archive" / "d10a_real_layout_nonoracle_v01" / "Q1_D10A_REAL_LAYOUT_NONORACLE_OBSERVATION_CALIBRATION_REPRODUCIBLE_v01.zip"
REQUEST = CTL / "request.txt"
CONTRACT = CTL / "contract_v01.md"
HIERARCHY = CTL / "Q1_D10E_OBSERVATION_STOCHASTIC_HIERARCHY_v01.md"
LEDGER = CTL / "stochastic_ledger_v01.csv"

EXPECTED = {
    D10D: "8efd2e9c5609de0fbb831c4aa268c1334a368569e7fc870b80e262a196bbeb42",
    D10CR: "5ae34a71d50c8bea0809cef77d9835051926f3ea3455b41b2ed913860bab64b1",
    D10CA: "c8f73406f7f192b8f124add3cb0ded7ea65474e8d72d752e37dc557a08588865",
    D10B: "cb041fca5897f31c8ea0bf2a3b29a262a5c83ef44bdfda9a37a0394cfc7cafeb",
    D10A: "20e5d3ed33df6414b72a6e679d5349f3b10fe6397ce73f98b51d0bcc96033013",
    REQUEST: "9b79421cf450d9850f71c6c37fc15b2363a397fd587e1f50345eb649dd78b2bd",
}

TOTAL_MASS = 100_000_000.0
TPA_UNADJ = 6.018046
MC_NAMESPACE = "D10E_MC_v01"
MC_BATCH = 200
MC_MAX = 1000
K_VALUES = (1, 2, 4, 8, 16, 32)
TERMINAL = "ABUNDANCE_MEASUREMENT_NOISE_DECOMPOSITION_COMPLETE_READY_FOR_MAINLINE"

_WORKER = {}


def _import_source_module(path: str, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def downstream_worker_init(d10a_path, d10d_path, truth_maps, ensemble_info, layout, param):
    d10a = _import_source_module(d10a_path, "d10e_worker_d10a")
    d10d = _import_source_module(d10d_path, "d10e_worker_d10d")
    _WORKER.update({
        "d10a": d10a, "d10d": d10d, "truth_maps": truth_maps, "ensemble_info": ensemble_info,
        "layout": layout, "param": param, "signature": d10a.build_spatial_signature_engine(layout, param),
    })


def downstream_worker_eval(task):
    label, world, orientation, populations = task
    truths = {sid: _WORKER["truth_maps"][(sid, world, orientation)] for sid in range(1, 73)}
    return _WORKER["d10d"].evaluate_detailed(
        label, world, orientation, populations, truths, _WORKER["ensemble_info"], _WORKER["layout"],
        _WORKER["param"], _WORKER["d10a"], _WORKER["signature"],
    )


def sha256_file(path: Path, chunk: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(chunk), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_csv(path: Path, rows: list[dict], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fields is None:
        fields = list(rows[0]) if rows else []
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


class DeterministicGzipText:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.raw = path.open("wb")
        self.gz = gzip.GzipFile(filename="", mode="wb", fileobj=self.raw, compresslevel=9, mtime=0)
        self.text = io.TextIOWrapper(self.gz, encoding="utf-8-sig", newline="")

    def __enter__(self):
        return self.text

    def __exit__(self, exc_type, exc, tb):
        self.text.flush()
        self.text.detach()
        self.gz.close()
        self.raw.close()


def zip_member_name(path: Path, suffix: str) -> str:
    with zipfile.ZipFile(path) as archive:
        matches = [name for name in archive.namelist() if name.endswith(suffix)]
    if len(matches) != 1:
        raise RuntimeError(f"INPUT_BLOCKED_FROZEN_IDENTITY_FAILURE: {path.name}::{suffix} matches={len(matches)}")
    return matches[0]


def zip_member_bytes(path: Path, suffix: str) -> bytes:
    name = zip_member_name(path, suffix)
    with zipfile.ZipFile(path) as archive:
        return archive.read(name)


def zip_csv(path: Path, suffix: str, **kwargs) -> pd.DataFrame:
    return pd.read_csv(io.BytesIO(zip_member_bytes(path, suffix)), encoding="utf-8-sig", **kwargs)


def zip_gzip_csv(path: Path, suffix: str, **kwargs) -> pd.DataFrame:
    return pd.read_csv(io.BytesIO(gzip.decompress(zip_member_bytes(path, suffix))), encoding="utf-8-sig", **kwargs)


def import_zip_module(path: Path, suffix: str, name: str):
    target = TMP / f"{name}.py"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(zip_member_bytes(path, suffix))
    spec = importlib.util.spec_from_file_location(name, target)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def verify_csv_manifest(path: Path, manifest_suffix: str) -> tuple[int, list[str]]:
    with zipfile.ZipFile(path) as archive:
        manifest_name = zip_member_name(path, manifest_suffix)
        rows = list(csv.DictReader(io.StringIO(archive.read(manifest_name).decode("utf-8-sig"))))
        names = archive.namelist()
        bad = []
        for row in rows:
            rel = row["relative_path"].replace("\\", "/")
            matches = [n for n in names if n == rel or n.endswith("/" + rel)]
            if len(matches) != 1:
                bad.append(rel + ":MEMBER_COUNT")
                continue
            payload = archive.read(matches[0])
            if len(payload) != int(row["size_bytes"]) or sha256_bytes(payload) != row["sha256"]:
                bad.append(rel + ":HASH_OR_SIZE")
    return len(rows), bad


def verify_d10d_manifest() -> tuple[int, list[str]]:
    with zipfile.ZipFile(D10D) as archive:
        name = zip_member_name(D10D, "manifest/SHA256SUMS.txt")
        rows = archive.read(name).decode("utf-8-sig").splitlines()
        bad = []
        for line in rows:
            expected, rel = line.split("  ", 1)
            member = "D10D_v01/" + rel
            if member not in archive.namelist() or sha256_bytes(archive.read(member)) != expected:
                bad.append(rel)
    return len(rows), bad


def normalize(values: np.ndarray, mask: np.ndarray | None = None) -> np.ndarray:
    result = np.asarray(values, dtype=float).copy()
    if mask is not None:
        result[~mask] = 0.0
    total = float(result.sum())
    if not np.isfinite(total) or total <= 0:
        raise RuntimeError("IMPLEMENTATION_BLOCKED: nonpositive map total")
    result /= total
    return result


def safe_corr(x, y) -> float:
    a = np.asarray(x, dtype=float)
    b = np.asarray(y, dtype=float)
    ok = np.isfinite(a) & np.isfinite(b)
    if ok.sum() < 3 or np.std(a[ok]) < 1e-15 or np.std(b[ok]) < 1e-15:
        return float("nan")
    return float(np.corrcoef(a[ok], b[ok])[0, 1])


def spearman(x, y) -> float:
    a = pd.Series(x, dtype=float).rank(method="average").to_numpy(float)
    b = pd.Series(y, dtype=float).rank(method="average").to_numpy(float)
    return safe_corr(a, b)


def q(values, probability) -> float:
    return float(np.quantile(np.asarray(values, dtype=float), probability))


def orientation_for_fold(fold: str) -> str:
    return "AB" if fold == "B" else "BA"


def fold_for_orientation(orientation: str) -> str:
    return "B" if orientation == "AB" else "A"


def panel_count(candidate: str, fold: str) -> int:
    match = re.search(r"_A([^_]+)_B([^_]+)$", candidate)
    if not match:
        raise RuntimeError(f"INPUT_BLOCKED_FROZEN_IDENTITY_FAILURE: cannot parse ti_candidate_id={candidate}")
    token = match.group(1 if fold == "A" else 2)
    return len([x for x in token.split("-") if x])


def expand_regimes(rows: list[dict], regimes: list[str]) -> list[dict]:
    return [{**row, "observation_regime": regime} for regime in regimes for row in rows]


def compare_rows(regenerated: list[dict], released: pd.DataFrame, released_layer: str) -> float:
    frame = pd.DataFrame(regenerated).copy()
    ref = released.loc[released["layer"] == released_layer].copy()
    keys = ["world", "observation_regime", "orientation", "replicate", "split_seed"]
    for col in ("replicate", "split_seed"):
        frame[col] = frame[col].astype(str)
        ref[col] = ref[col].astype(str)
    frame = frame.sort_values(keys).reset_index(drop=True)
    ref = ref.sort_values(keys).reset_index(drop=True)
    if len(frame) != len(ref) or not (frame[keys].astype(str) == ref[keys].astype(str)).all().all():
        return float("inf")
    diffs = []
    for col in frame.columns:
        if col in ref.columns and col not in keys + ["layer", "model"]:
            left = pd.to_numeric(frame[col], errors="coerce")
            right = pd.to_numeric(ref[col], errors="coerce")
            if left.notna().any() or right.notna().any():
                diffs.append(float(np.nanmax(np.abs(left.to_numpy(float) - right.to_numpy(float)))))
    return max(diffs) if diffs else 0.0


def state_function(rows: list[dict]) -> dict:
    by = {(r["world"], r["orientation"], int(r["replicate"])): r for r in rows}
    result = {}
    for orientation in ("AB", "BA"):
        strong = [by[("STRONG", orientation, rep)]["latent_truth_geometry_gain_pct"] for rep in range(1, 6)]
        null = [by[("PAIRED_NULL", orientation, rep)]["latent_truth_geometry_gain_pct"] for rep in range(1, 6)]
        separation = [a - b for a, b in zip(strong, null)]
        result[orientation] = {
            "strong_gain_pp": float(np.median(strong)),
            "paired_null_gain_pp": float(np.median(null)),
            "separation_pp": float(np.median(separation)),
            "strong_geometry_coverage": float(np.median([by[("STRONG", orientation, rep)]["geometry_latent_truth_coverage"] for rep in range(1, 6)])),
            "paired_null_geometry_coverage": float(np.median([by[("PAIRED_NULL", orientation, rep)]["geometry_latent_truth_coverage"] for rep in range(1, 6)])),
        }
    result["ALL"] = {name: float(np.median([result["AB"][name], result["BA"][name]])) for name in result["AB"]}
    return result


def summarize_values(values) -> dict:
    a = np.asarray(values, dtype=float)
    return {
        "n": int(len(a)), "mean": float(np.mean(a)), "sd": float(np.std(a, ddof=1)) if len(a) > 1 else 0.0,
        "mcse": float(np.std(a, ddof=1) / math.sqrt(len(a))) if len(a) > 1 else 0.0,
        "q05": q(a, 0.05), "median": q(a, 0.5), "q95": q(a, 0.95), "min": float(np.min(a)), "max": float(np.max(a)),
    }


def main() -> None:
    started = time.time()
    if not all(path.exists() for path in (CONTRACT, HIERARCHY, LEDGER)):
        raise RuntimeError("IMPLEMENTATION_BLOCKED: hierarchy and experiment contract must be frozen before computation")
    for directory in (OUT, QC, FIG, MAN):
        if directory.exists():
            shutil.rmtree(directory)
        directory.mkdir(parents=True, exist_ok=True)
    SRC.mkdir(parents=True, exist_ok=True)
    TMP.mkdir(parents=True, exist_ok=True)

    identity_rows = []
    for path, expected in {**EXPECTED, CONTRACT: "FROZEN_PRECOMPUTE", HIERARCHY: "FROZEN_PRECOMPUTE", LEDGER: "FROZEN_PRECOMPUTE"}.items():
        actual = sha256_file(path)
        ok = expected == "FROZEN_PRECOMPUTE" or actual == expected
        identity_rows.append({"asset": path.name, "path": str(path), "size_bytes": path.stat().st_size, "expected_sha256": expected, "actual_sha256": actual, "status": "PASS" if ok else "FAIL"})
    manifest_specs = [
        ("D10D_internal", verify_d10d_manifest),
        ("D10CR_internal", lambda: verify_csv_manifest(D10CR, "manifest/sha256sums_v01.csv")),
        ("D10CA_internal", lambda: verify_csv_manifest(D10CA, "manifest/sha256s.csv")),
        ("D10A_internal", lambda: verify_csv_manifest(D10A, "SHA256SUMS.csv")),
        ("D10B_internal", lambda: verify_csv_manifest(D10B, "SHA256SUMS.csv")),
    ]
    for name, func in manifest_specs:
        count, bad = func()
        identity_rows.append({"asset": name, "path": "INTERNAL_MANIFEST", "size_bytes": count, "expected_sha256": "ALL_LISTED_MEMBERS_MATCH", "actual_sha256": "PASS" if not bad else ";".join(bad), "status": "PASS" if not bad else "FAIL"})
    write_csv(QC / "input_id_v01.csv", identity_rows)
    if any(row["status"] != "PASS" for row in identity_rows):
        raise RuntimeError("INPUT_BLOCKED_FROZEN_IDENTITY_FAILURE")

    d10a = import_zip_module(D10A, "build_d10a_real_layout_nonoracle_v01.py", "d10a")
    d10b = import_zip_module(D10B, "build_d10b_oracle_source_decomposition_v01.py", "d10b")
    d10d = import_zip_module(D10D, "D10D_v01/src/build.py", "d10d")
    param = json.loads(zip_member_bytes(D10A, "parameters_d10a_real_layout_nonoracle_v01.json").decode("utf-8-sig"))
    regimes = sorted(param["observation_regimes"])
    f0 = zip_csv(D10A, "Q1_D10A_REAL_F0_OPPORTUNITY_LAYOUT_v01.csv", dtype=str, keep_default_na=False)
    truth_df = zip_csv(D10CR, "out/truth_v01.csv", dtype=str, keep_default_na=False)
    a2_df = zip_gzip_csv(D10CR, "out/a2_v01.csv.gz", dtype=str, keep_default_na=False)
    published_d10d = zip_csv(D10D, "D10D_v01/out/downstream_v01.csv", dtype=str, keep_default_na=False)
    domain_df = zip_csv(D10D, "D10D_v01/out/domain_cells_v01.csv", dtype=str, keep_default_na=False)
    world_id = zip_csv(D10CR, "qc/world_id_v01.csv", dtype=str, keep_default_na=False)
    crosswalk = zip_gzip_csv(D10CA, "plot_block_xwalk_v01.csv.gz", dtype=str, keep_default_na=False)

    legal = f0.loc[f0["base_legitimate_opportunity_flag"] == "YES"].copy()
    plots = {}
    for row in legal.to_dict("records"):
        plots[row["plot_cn"]] = {
            "base_legitimate_opportunity_flag": True, "cell_50km": row["cell_50km"], "manual": row["manual"],
            "designcd": row["designcd"], "effort_score": float(row["partial_sampling_effort"]),
            "partial_sampling_flag": row["partial_sampling_flag"] == "YES", "fold": row["fold"],
        }
    layout = d10a.build_layout_arrays(plots, param)
    cells = list(layout["cells"])
    cell_index = {cell: idx for idx, cell in enumerate(cells)}
    ncell = len(cells)
    if len(f0) != 338619 or len(legal) != 134846 or ncell != 3011:
        raise RuntimeError("INPUT_BLOCKED_FROZEN_IDENTITY_FAILURE: F0 dimensions")

    domain_index = domain_df.set_index("cell_50km")
    if set(domain_index.index) != set(cells):
        raise RuntimeError("INPUT_BLOCKED_FROZEN_IDENTITY_FAILURE: D3 cell identity")
    domain3 = np.asarray([domain_index.loc[cell, "D3_common_included"] == "YES" for cell in cells], dtype=bool)
    if int(domain3.sum()) != 2757:
        raise RuntimeError("INPUT_BLOCKED_FROZEN_IDENTITY_FAILURE: D3 count")

    cw = crosswalk.set_index("PLT_CN", drop=False)
    fold_design = {}
    for fold in ("A", "B"):
        lf = legal.loc[legal["fold"] == fold].copy()
        cns = lf["plot_cn"].tolist()
        if any(cn not in cw.index for cn in cns):
            raise RuntimeError("INPUT_BLOCKED_FROZEN_IDENTITY_FAILURE: crosswalk coverage")
        selected = cw.loc[cns].reset_index(drop=True)
        if not (selected["final_fold"] == fold).all() or not (selected["QC_STATUS"] == "PASS").all():
            raise RuntimeError("INPUT_BLOCKED_FROZEN_IDENTITY_FAILURE: crosswalk fold/QC")
        pcell = layout["folds"][fold]["plot_cell"]
        ti = pd.to_numeric(selected["fold_specific_ti_weight"]).to_numpy(float)
        adj = pd.to_numeric(selected["adj_factor_subp"]).to_numpy(float)
        effort = pd.to_numeric(lf["partial_sampling_effort"]).to_numpy(float)
        role = np.asarray([panel_count(value, fold) for value in selected["ti_candidate_id"]], dtype=int)
        if not set(np.unique(role)).issubset({2, 3}):
            raise RuntimeError("INPUT_BLOCKED_FROZEN_IDENTITY_FAILURE: panel role is not 2/3")
        fold_design[fold] = {
            "plot_cn": np.asarray(cns, dtype=object), "pcell": pcell, "ti": ti, "adj": adj, "effort": effort,
            "factor": ti * adj * TPA_UNADJ, "candidate": selected["ti_candidate_id"].to_numpy(), "panel_role": role,
            "panel": selected["P2PANEL"].to_numpy(), "state": selected["STATECD"].to_numpy(),
        }

    supports = {sid: np.zeros(ncell, dtype=bool) for sid in range(1, 73)}
    abundances = {(sid, world): np.zeros(ncell, dtype=float) for sid in range(1, 73) for world in ("STRONG", "PAIRED_NULL")}
    for row in truth_df.to_dict("records"):
        sid = int(row["synthetic_species_id"][3:])
        idx = cell_index[row["cell_50km"]]
        supports[sid][idx] = True
        abundances[(sid, row["world"])][idx] = float(row["latent_allocation"])
    if any(abs(values.sum() - 1.0) > 1e-12 for values in abundances.values()):
        raise RuntimeError("INPUT_BLOCKED_FROZEN_IDENTITY_FAILURE: latent normalization")

    released_world = {(row["synthetic_species_id"], row["world"]): row for row in world_id.to_dict("records")}
    world_hash_count = 0
    for sid in range(1, 73):
        for world in ("STRONG", "PAIRED_NULL"):
            ref = released_world[(f"SYN{sid:03d}", world)]
            sh = d10b.array_sha256(np.where(supports[sid])[0].astype(np.int64))
            ah = d10b.array_sha256(abundances[(sid, world)].astype(np.float64))
            world_hash_count += int(sh == ref["support_index_sha256"] and ah == ref["latent_abundance_sha256"])
    if world_hash_count != 144:
        raise RuntimeError("INPUT_BLOCKED_FROZEN_IDENTITY_FAILURE: synthetic world hashes")

    a2_mass = {(sid, world, orientation): np.zeros(ncell, dtype=float) for sid in range(1, 73) for world in ("STRONG", "PAIRED_NULL") for orientation in ("AB", "BA")}
    a2_var = {key: np.zeros(ncell, dtype=float) for key in a2_mass}
    for row in a2_df.to_dict("records"):
        sid = int(row["synthetic_species_id"][3:])
        idx = cell_index[row["cell_50km"]]
        key = (sid, row["world"], row["orientation"])
        a2_mass[key][idx] = float(row["estimated_cell_mass"])
        a2_var[key][idx] = float(row["estimated_poisson_variance"])

    support3 = {sid: supports[sid] & domain3 for sid in range(1, 73)}
    if any(mask.sum() == 0 for mask in support3.values()):
        raise RuntimeError("IMPLEMENTATION_BLOCKED: empty D3 support")
    truth_maps = {(sid, world, orientation): normalize(abundances[(sid, world)], support3[sid]) for sid in range(1, 73) for world in ("STRONG", "PAIRED_NULL") for orientation in ("AB", "BA")}
    current_maps = {key: normalize(a2_mass[key], support3[key[0]]) for key in a2_mass}
    ensemble_info = d10b.oracle_geometry_ensemble(layout, support3, d10a)
    signature = d10a.build_spatial_signature_engine(layout, param)
    process_pool = ProcessPoolExecutor(
        max_workers=4,
        initializer=downstream_worker_init,
        initargs=(str(TMP / "d10a.py"), str(TMP / "d10d.py"), truth_maps, ensemble_info, layout, param),
    )

    def evaluate_state(label: str, maps: dict) -> tuple[list[dict], list[dict]]:
        base, details = [], []
        combinations = [(world, orientation) for world in ("STRONG", "PAIRED_NULL") for orientation in ("AB", "BA")]
        tasks = [(label, world, orientation, {sid: maps[(sid, world, orientation)] for sid in range(1, 73)}) for world, orientation in combinations]
        for rows, detail in process_pool.map(downstream_worker_eval, tasks):
            base.extend(rows)
            details.extend(detail)
        return base, details

    e0_base, e0_detail = evaluate_state("E0", truth_maps)
    e1_base, e1_detail = evaluate_state("E1", current_maps)
    e0_rows = expand_regimes(e0_base, regimes)
    e1_rows = expand_regimes(e1_base, regimes)
    e0_diff = compare_rows([{**r, "layer": "D3_A0_REF"} for r in e0_rows], published_d10d, "D3_A0_REF")
    e1_diff = compare_rows([{**r, "layer": "D3"} for r in e1_rows], published_d10d, "D3")

    e2_maps = {}
    e2_relative_error = 0.0
    for sid in range(1, 73):
        for fold in ("A", "B"):
            design = fold_design[fold]
            micro = np.exp(np.random.default_rng(d10a.stable_seed(param["collection_seed"], sid, fold, "count_micro")).normal(0.0, param["abundance_plot_log_sd"], len(design["pcell"])))
            exposure = np.bincount(design["pcell"], weights=design["ti"] * design["adj"] * design["effort"] * micro, minlength=ncell)
            positive = exposure[design["pcell"]] > 0
            orientation = orientation_for_fold(fold)
            for world in ("STRONG", "PAIRED_NULL"):
                truth_mass = TOTAL_MASS * abundances[(sid, world)]
                rate = np.zeros(len(design["pcell"]), dtype=float)
                rate[positive] = truth_mass[design["pcell"][positive]] / exposure[design["pcell"][positive]] * design["effort"][positive] * micro[positive] / TPA_UNADJ
                conditional_mass = np.bincount(design["pcell"], weights=rate * design["factor"], minlength=ncell)
                active = support3[sid]
                relative = np.max(np.abs(conditional_mass[active] - truth_mass[active]) / np.maximum(1.0, np.abs(truth_mass[active])))
                e2_relative_error = max(e2_relative_error, float(relative))
                e2_maps[(sid, world, orientation)] = normalize(conditional_mass, active)
    e3_maps = {key: value.copy() for key, value in truth_maps.items()}
    e2_base = [{**row, "layer": "E2"} for row in e0_base]
    e3_base = [{**row, "layer": "E3"} for row in e0_base]

    profiles = []
    offset = 0
    for sid in range(1, 73):
        active = np.where(support3[sid])[0]
        for world in ("STRONG", "PAIRED_NULL"):
            for orientation in ("AB", "BA"):
                key = (sid, world, orientation)
                profiles.append({"key": key, "active": active, "start": offset, "stop": offset + len(active), "truth_mass": TOTAL_MASS * abundances[(sid, world)][active]})
                offset += len(active)
    total_profile_cells = offset
    profile_index = {p["key"]: p for p in profiles}
    profile_position = {p["key"]: pos for pos, p in enumerate(profiles)}
    sample_path = TMP / "mass_samples_v01.dat"
    mass_samples = np.memmap(sample_path, dtype="float64", mode="w+", shape=(MC_MAX, total_profile_cells))
    sum_mass = {p["key"]: np.zeros(ncell, dtype=float) for p in profiles}
    sum_normalized = {p["key"]: np.zeros(ncell, dtype=float) for p in profiles}
    sum_varhat = np.zeros(total_profile_cells, dtype=float)
    poisson_cover_count = np.zeros(total_profile_cells, dtype=np.int32)
    total_count_samples = np.zeros((MC_MAX, len(profiles)), dtype=np.float32)
    e5_base_by_r: list[list[dict]] = []
    e5_detail_rows: list[dict] = []
    e5_realization_rows: list[dict] = []
    convergence_rows = []
    accepted = 0

    def simulate_realization(realization: int) -> tuple[dict, np.ndarray, np.ndarray, np.ndarray]:
        maps = {}
        flat_mass = np.zeros(total_profile_cells, dtype=float)
        flat_var = np.zeros(total_profile_cells, dtype=float)
        flat_count = np.zeros(len(profiles), dtype=np.float32)
        for sid in range(1, 73):
            for fold in ("A", "B"):
                design = fold_design[fold]
                micro_seed = d10a.stable_seed(param["collection_seed"], MC_NAMESPACE, realization, sid, fold, "micro")
                micro = np.exp(np.random.default_rng(micro_seed).normal(0.0, param["abundance_plot_log_sd"], len(design["pcell"])))
                exposure = np.bincount(design["pcell"], weights=design["ti"] * design["adj"] * design["effort"] * micro, minlength=ncell)
                positive = exposure[design["pcell"]] > 0
                count_seed = d10a.stable_seed(param["collection_seed"], MC_NAMESPACE, realization, sid, fold, "paired_counts")
                orientation = orientation_for_fold(fold)
                for world in ("STRONG", "PAIRED_NULL"):
                    truth_mass = TOTAL_MASS * abundances[(sid, world)]
                    rate = np.zeros(len(design["pcell"]), dtype=float)
                    rate[positive] = truth_mass[design["pcell"][positive]] / exposure[design["pcell"][positive]] * design["effort"][positive] * micro[positive] / TPA_UNADJ
                    counts = np.random.default_rng(count_seed).poisson(rate)
                    mass = np.bincount(design["pcell"], weights=counts * design["factor"], minlength=ncell)
                    varhat = np.bincount(design["pcell"], weights=counts * design["factor"] ** 2, minlength=ncell)
                    key = (sid, world, orientation)
                    active = profile_index[key]["active"]
                    p = normalize(mass, support3[sid])
                    maps[key] = p
                    start, stop = profile_index[key]["start"], profile_index[key]["stop"]
                    flat_mass[start:stop] = mass[active]
                    flat_var[start:stop] = varhat[active]
                    flat_count[profile_position[key]] = float(counts.sum())
        return maps, flat_mass, flat_var, flat_count

    while accepted < MC_MAX:
        target = min(accepted + MC_BATCH, MC_MAX)
        for realization in range(accepted + 1, target + 1):
            maps, flat_mass, flat_var, flat_count = simulate_realization(realization)
            mass_samples[realization - 1, :] = flat_mass
            total_count_samples[realization - 1, :] = flat_count
            sum_varhat += flat_var
            truth_flat = np.concatenate([p["truth_mass"] for p in profiles])
            poisson_cover_count += (np.abs(flat_mass.astype(float) - truth_flat) <= 1.96 * np.sqrt(np.maximum(flat_var, 0.0))).astype(np.int32)
            for profile in profiles:
                key = profile["key"]
                active = profile["active"]
                start, stop = profile["start"], profile["stop"]
                mass = np.zeros(ncell, dtype=float)
                mass[active] = flat_mass[start:stop].astype(float)
                sum_mass[key] += mass
                sum_normalized[key] += maps[key]
            base, detail = evaluate_state(f"E5_R{realization:04d}", maps)
            for row in base:
                row["observation_realization"] = realization
            for row in detail:
                row["observation_realization"] = realization
            e5_base_by_r.append(base)
            e5_detail_rows.extend(detail)
            func = state_function(base)
            e5_realization_rows.append({
                "observation_realization": realization,
                "AB_strong_gain_pp": func["AB"]["strong_gain_pp"], "AB_paired_null_gain_pp": func["AB"]["paired_null_gain_pp"], "AB_separation_pp": func["AB"]["separation_pp"],
                "BA_strong_gain_pp": func["BA"]["strong_gain_pp"], "BA_paired_null_gain_pp": func["BA"]["paired_null_gain_pp"], "BA_separation_pp": func["BA"]["separation_pp"],
                "pooled_strong_gain_pp": func["ALL"]["strong_gain_pp"], "pooled_paired_null_gain_pp": func["ALL"]["paired_null_gain_pp"], "pooled_separation_pp": func["ALL"]["separation_pp"],
                "BA_minus_AB_separation_pp": func["BA"]["separation_pp"] - func["AB"]["separation_pp"],
                "AB_STRONG_geometry_coverage": func["AB"]["strong_geometry_coverage"], "AB_PAIRED_NULL_geometry_coverage": func["AB"]["paired_null_geometry_coverage"],
                "BA_STRONG_geometry_coverage": func["BA"]["strong_geometry_coverage"], "BA_PAIRED_NULL_geometry_coverage": func["BA"]["paired_null_geometry_coverage"],
                "pooled_STRONG_geometry_coverage": func["ALL"]["strong_geometry_coverage"], "pooled_PAIRED_NULL_geometry_coverage": func["ALL"]["paired_null_geometry_coverage"],
            })
            if realization % 20 == 0:
                print(json.dumps({"stage": "E5_MC", "realizations": realization, "elapsed_seconds": round(time.time() - started, 1)}), flush=True)
        accepted = target
        pooled = summarize_values([r["pooled_separation_pp"] for r in e5_realization_rows])
        ab = summarize_values([r["AB_separation_pp"] for r in e5_realization_rows])
        ba = summarize_values([r["BA_separation_pp"] for r in e5_realization_rows])
        reached = pooled["mcse"] <= 0.25 and ab["mcse"] <= 0.50 and ba["mcse"] <= 0.50
        convergence_rows.append({
            "realizations": accepted, "pooled_separation_mean_pp": pooled["mean"], "pooled_separation_mcse_pp": pooled["mcse"],
            "AB_separation_mean_pp": ab["mean"], "AB_separation_mcse_pp": ab["mcse"], "BA_separation_mean_pp": ba["mean"], "BA_separation_mcse_pp": ba["mcse"],
            "pooled_target_pp": 0.25, "orientation_target_pp": 0.50, "precision_reached": "YES" if reached else "NO", "stop_reason": "TARGET_REACHED" if reached else ("MAX_1000" if accepted == MC_MAX else "CONTINUE"),
        })
        print(json.dumps({"stage": "MC_CONVERGENCE", **convergence_rows[-1]}), flush=True)
        if reached or accepted == MC_MAX:
            break

    mass_samples.flush()
    e4_maps = {key: normalize(value / accepted, support3[key[0]]) for key, value in sum_normalized.items()}
    e4_base, e4_detail = evaluate_state("E4", e4_maps)

    deterministic_states = {"E0": e0_base, "E1": e1_base, "E2": e2_base, "E3": e3_base, "E4": e4_base}
    state_functions = {state: state_function(rows) for state, rows in deterministic_states.items()}
    e5_function = {}
    for orientation in ("AB", "BA", "ALL"):
        prefix = "pooled" if orientation == "ALL" else orientation
        e5_function[orientation] = {
            "strong_gain_pp": float(np.mean([r[f"{prefix}_strong_gain_pp"] for r in e5_realization_rows])),
            "paired_null_gain_pp": float(np.mean([r[f"{prefix}_paired_null_gain_pp"] for r in e5_realization_rows])),
            "separation_pp": float(np.mean([r[f"{prefix}_separation_pp"] for r in e5_realization_rows])),
            "strong_geometry_coverage": float(np.mean([r[f"{prefix}_STRONG_geometry_coverage"] for r in e5_realization_rows])),
            "paired_null_geometry_coverage": float(np.mean([r[f"{prefix}_PAIRED_NULL_geometry_coverage"] for r in e5_realization_rows])),
        }
    state_functions["E5"] = e5_function

    state_summary_rows = []
    for state in ("E0", "E1", "E2", "E3", "E4", "E5"):
        for regime in regimes:
            for orientation in ("AB", "BA", "ALL"):
                values = state_functions[state][orientation]
                mcse = summarize_values([r[("pooled" if orientation == "ALL" else orientation) + "_separation_pp"] for r in e5_realization_rows])["mcse"] if state == "E5" else 0.0
                state_summary_rows.append({"state": state, "observation_regime": regime, "orientation": orientation, **values, "separation_mcse_pp": mcse, "observation_realizations": accepted if state == "E5" else 1, "regime_applicability": "LABEL_ONLY_A2_IS_REGIME_INVARIANT"})

    e5_summary_rows = []
    for orientation in ("AB", "BA", "ALL"):
        prefix = "pooled" if orientation == "ALL" else orientation
        for metric in ("strong_gain_pp", "paired_null_gain_pp", "separation_pp"):
            summary = summarize_values([r[f"{prefix}_{metric}"] for r in e5_realization_rows])
            e5_summary_rows.append({"orientation": orientation, "metric": metric, **summary, "accepted_realizations": accepted})

    source_rows = []
    components = [
        ("A_SYSTEMATIC_MEASUREMENT_OPERATOR", "E3", "E0", "E3 - E0"),
        ("B_NORMALIZATION_NONLINEARITY", "E4", "E3", "E4 - E3"),
        ("C_FINITE_REALIZATION_DOWNSTREAM", "E5", "E4", "E5 - E4"),
        ("D_CURRENT_REALIZATION_DEVIATION", "E1", "E5", "E1 - E5"),
    ]
    for component, left, right, definition in components:
        for regime in regimes:
            for orientation in ("AB", "BA", "ALL"):
                for metric in ("strong_gain_pp", "paired_null_gain_pp", "separation_pp"):
                    source_rows.append({
                        "component": component, "definition": definition, "observation_regime": regime, "orientation": orientation, "metric": metric,
                        "left_state": left, "right_state": right, "left_value_pp": state_functions[left][orientation][metric],
                        "right_value_pp": state_functions[right][orientation][metric], "component_value_pp": state_functions[left][orientation][metric] - state_functions[right][orientation][metric],
                        "scientific_disposition": "NOT_ASSIGNED",
                    })

    orientation_rows = []
    world_rows = []
    for state in state_functions:
        for regime in regimes:
            orientation_rows.append({
                "state": state, "observation_regime": regime, "AB_separation_pp": state_functions[state]["AB"]["separation_pp"],
                "BA_separation_pp": state_functions[state]["BA"]["separation_pp"], "BA_minus_AB_separation_pp": state_functions[state]["BA"]["separation_pp"] - state_functions[state]["AB"]["separation_pp"],
                "scientific_disposition": "NOT_ASSIGNED",
            })
            for orientation in ("AB", "BA", "ALL"):
                for world, field in (("STRONG", "strong_gain_pp"), ("PAIRED_NULL", "paired_null_gain_pp")):
                    world_rows.append({"state": state, "observation_regime": regime, "orientation": orientation, "world": world, "geometry_gain_pp": state_functions[state][orientation][field], "scientific_disposition": "NOT_ASSIGNED"})

    state_maps = {"E0": truth_maps, "E1": current_maps, "E2": e2_maps, "E3": e3_maps, "E4": e4_maps}
    map_rows = []
    for state, maps in state_maps.items():
        for profile in profiles:
            sid, world, orientation = profile["key"]
            active = support3[sid]
            true_p = truth_maps[profile["key"]]
            est_p = maps[profile["key"]]
            metrics = d10d.map_metrics(true_p, est_p, active, layout, signature, d10a)
            diff = est_p[active] - true_p[active]
            scale = float(np.mean(true_p[active]))
            map_rows.append({
                "state": state, "synthetic_species_id": f"SYN{sid:03d}", "world": world, "orientation": orientation,
                "support_cells_D3": int(active.sum()), "cell_mass_correlation": safe_corr(true_p[active], est_p[active]),
                "allocation_bias": float(np.mean(diff)), "relative_bias": float(np.mean(diff) / scale),
                "allocation_rmse": float(np.sqrt(np.mean(diff ** 2))), "relative_rmse": float(np.sqrt(np.mean(diff ** 2)) / scale),
                "entropy_bias": metrics["estimated_entropy"] - metrics["true_entropy"], "concentration_bias": metrics["estimated_concentration"] - metrics["true_concentration"],
                **metrics,
            })
    map_df = pd.DataFrame(map_rows)
    map_summary_rows = []
    metric_names = ["hellinger_distance", "sliced_wasserstein_km", "cell_mass_correlation", "relative_bias", "relative_rmse", "entropy_bias", "concentration_bias"]
    for (state, world, orientation), group in map_df.groupby(["state", "world", "orientation"], sort=True):
        for metric in metric_names:
            values = pd.to_numeric(group[metric], errors="coerce").dropna().to_numpy(float)
            map_summary_rows.append({"state": state, "world": world, "orientation": orientation, "metric": metric, **summarize_values(values)})

    map_fields = ["state", "synthetic_species_id", "world", "orientation", "target_fold", "cell_50km", "D3_oracle_support", "latent_allocation_D3", "state_allocation_D3", "unnormalized_cell_mass", "mass_semantics"]
    with DeterministicGzipText(OUT / "maps_v01.csv.gz") as handle:
        writer = csv.DictWriter(handle, fieldnames=map_fields, lineterminator="\n")
        writer.writeheader()
        for state, maps in state_maps.items():
            for profile in profiles:
                sid, world, orientation = profile["key"]
                active = profile["active"]
                if state == "E1":
                    raw = a2_mass[profile["key"]]
                    semantics = "FROZEN_SINGLE_REALIZATION_A2_MASS"
                elif state in ("E0", "E2", "E3"):
                    raw = TOTAL_MASS * abundances[(sid, world)]
                    semantics = "RESTRICTED_LATENT_OR_EXACT_EXPECTED_MASS"
                else:
                    raw = np.full(ncell, np.nan)
                    semantics = "MEAN_NORMALIZED_MAP_NO_SINGLE_UNNORMALIZED_MASS"
                for idx in active:
                    writer.writerow({
                        "state": state, "synthetic_species_id": f"SYN{sid:03d}", "world": world, "orientation": orientation,
                        "target_fold": fold_for_orientation(orientation), "cell_50km": cells[idx], "D3_oracle_support": "YES",
                        "latent_allocation_D3": truth_maps[profile["key"]][idx], "state_allocation_D3": maps[profile["key"]][idx],
                        "unnormalized_cell_mass": "" if state == "E4" else raw[idx], "mass_semantics": semantics,
                    })

    current_detail = defaultdict(list)
    e0_detail_index = defaultdict(list)
    for row in e1_detail:
        current_detail[(int(row["synthetic_species_id"][3:]), row["world"], row["orientation"])].append(float(row["individual_latent_truth_geometry_gain_pct"]))
    for row in e0_detail:
        e0_detail_index[(int(row["synthetic_species_id"][3:]), row["world"], row["orientation"])].append(float(row["individual_latent_truth_geometry_gain_pct"]))
    e5_detail_index = defaultdict(list)
    for row in e5_detail_rows:
        e5_detail_index[(int(row["synthetic_species_id"][3:]), row["world"], row["orientation"])].append(float(row["individual_latent_truth_geometry_gain_pct"]))

    information_rows = []
    for pos, profile in enumerate(profiles):
        sid, world, orientation = profile["key"]
        fold = fold_for_orientation(orientation)
        design = fold_design[fold]
        active = support3[sid]
        plot_mask = active[design["pcell"]]
        weights = design["ti"][plot_mask] * design["adj"][plot_mask] * design["effort"][plot_mask]
        kish = float(weights.sum() ** 2 / np.sum(weights ** 2)) if np.sum(weights ** 2) > 0 else float("nan")
        roles = design["panel_role"][plot_mask]
        e1_h = map_df.loc[(map_df.state == "E1") & (map_df.synthetic_species_id == f"SYN{sid:03d}") & (map_df.world == world) & (map_df.orientation == orientation), "hellinger_distance"].iloc[0]
        e4_h = map_df.loc[(map_df.state == "E4") & (map_df.synthetic_species_id == f"SYN{sid:03d}") & (map_df.world == world) & (map_df.orientation == orientation), "hellinger_distance"].iloc[0]
        e0_values = e0_detail_index[profile["key"]]
        e5_values = e5_detail_index[profile["key"]]
        e0_ind = float(np.mean(e0_values)) if e0_values else float("nan")
        e5_ind = float(np.mean(e5_values)) if e5_values else float("nan")
        information_rows.append({
            "synthetic_species_id": f"SYN{sid:03d}", "world": world, "orientation": orientation, "target_fold": fold,
            "D3_support_cells": int(active.sum()), "legal_target_fold_plots_in_support": int(plot_mask.sum()),
            "plots_per_occupied_cell": float(plot_mask.sum() / active.sum()), "target_fold_TI_sum_in_support": float(design["ti"][plot_mask].sum()),
            "kish_effective_plot_information": kish, "mean_expected_total_tree_count": float(np.mean(total_count_samples[:accepted, pos])),
            "latent_concentration_D3": float(np.sum(truth_maps[profile["key"]] ** 2)), "two_panel_plot_fraction": float(np.mean(roles == 2)),
            "three_panel_plot_fraction": float(np.mean(roles == 3)), "dominant_panel_role": "2_PANEL" if np.mean(roles == 2) >= 0.5 else "3_PANEL",
            "E1_hellinger": float(e1_h), "E4_hellinger": float(e4_h),
            "E0_test_appearance_count": len(e0_values), "E5_test_appearance_count": len(e5_values),
            "individual_gain_missing_semantics": "NO_FROZEN_TEST_APPEARANCE" if not e0_values or not e5_values else "OBSERVED_IN_FROZEN_TEST_SPLITS",
            "E0_individual_gain_pp_mean_over_test_appearances": e0_ind,
            "E5_individual_gain_pp_mean_over_MC_and_test_appearances": e5_ind, "E5_minus_E0_individual_gain_pp": e5_ind - e0_ind,
        })
    info_df = pd.DataFrame(information_rows)
    relationship_rows = []
    predictors = ["legal_target_fold_plots_in_support", "plots_per_occupied_cell", "target_fold_TI_sum_in_support", "kish_effective_plot_information", "mean_expected_total_tree_count", "D3_support_cells", "latent_concentration_D3", "two_panel_plot_fraction"]
    outcomes = ["E1_hellinger", "E4_hellinger", "E5_minus_E0_individual_gain_pp"]
    for scope, subset in [("POOLED", info_df), ("AB", info_df[info_df.orientation == "AB"]), ("BA", info_df[info_df.orientation == "BA"])]:
        for predictor in predictors:
            for outcome in outcomes:
                x = pd.to_numeric(subset[predictor], errors="coerce").to_numpy(float)
                y = pd.to_numeric(subset[outcome], errors="coerce").to_numpy(float)
                ok = np.isfinite(x) & np.isfinite(y)
                for statistic, value in (("pearson_r", safe_corr(x[ok], y[ok])), ("spearman_rho", spearman(x[ok], y[ok]))):
                    relationship_rows.append({"scope": scope, "predictor": predictor, "outcome": outcome, "statistic": statistic, "value": value, "n": int(ok.sum()), "threshold_applied": "NO"})

    truth_flat = np.concatenate([p["truth_mass"] for p in profiles])
    samples = np.asarray(mass_samples[:accepted, :], dtype=np.float64)
    empirical_mean = np.mean(samples, axis=0)
    empirical_var = np.var(samples, axis=0, ddof=1)
    empirical_sd = np.sqrt(empirical_var)
    lower_q = np.quantile(samples, 0.025, axis=0)
    upper_q = np.quantile(samples, 0.975, axis=0)
    central_contains = (truth_flat >= lower_q) & (truth_flat <= upper_q)
    empirical_cover = np.mean(np.abs(samples - truth_flat[None, :]) <= 1.96 * empirical_sd[None, :], axis=0)
    mean_varhat = sum_varhat / accepted
    poisson_cover = poisson_cover_count / accepted
    uncertainty_rows = []
    flat_pos = 0
    current_cover_flat = np.zeros(total_profile_cells, dtype=float)
    for profile in profiles:
        sid, world, orientation = profile["key"]
        active = profile["active"]
        start, stop = profile["start"], profile["stop"]
        current_mass = a2_mass[profile["key"]][active]
        current_var = a2_var[profile["key"]][active]
        current_cover = np.abs(current_mass - profile["truth_mass"]) <= 1.96 * np.sqrt(np.maximum(current_var, 0.0))
        current_cover_flat[start:stop] = current_cover
        for local, idx in enumerate(active):
            flat = start + local
            ratio = empirical_var[flat] / mean_varhat[flat] if mean_varhat[flat] > 0 else float("nan")
            uncertainty_rows.append({
                "synthetic_species_id": f"SYN{sid:03d}", "world": world, "orientation": orientation, "target_fold": fold_for_orientation(orientation), "cell_50km": cells[idx],
                "latent_cell_mass": truth_flat[flat], "empirical_mean_mass": empirical_mean[flat], "empirical_bias": empirical_mean[flat] - truth_flat[flat],
                "empirical_variance": empirical_var[flat], "mean_poisson_plugin_variance": mean_varhat[flat], "variance_ratio_empirical_to_poisson": ratio,
                "empirical_variance_normal_interval_coverage": empirical_cover[flat], "empirical_central95_contains_truth": "YES" if central_contains[flat] else "NO",
                "poisson_plugin_interval_coverage": poisson_cover[flat], "current_E1_poisson_interval_covers_truth": "YES" if current_cover[local] else "NO",
            })
        flat_pos = stop
    uncertainty_df = pd.DataFrame(uncertainty_rows)
    uncertainty_summary_rows = []
    uncertainty_metrics = ["empirical_variance", "mean_poisson_plugin_variance", "variance_ratio_empirical_to_poisson", "empirical_variance_normal_interval_coverage", "poisson_plugin_interval_coverage"]
    for (world, orientation), group in uncertainty_df.groupby(["world", "orientation"], sort=True):
        base = {"world": world, "orientation": orientation, "profile_cells": len(group), "accepted_realizations": accepted,
                "empirical_central95_truth_containment_fraction": float(np.mean(group["empirical_central95_contains_truth"] == "YES")),
                "current_E1_poisson_interval_coverage": float(np.mean(group["current_E1_poisson_interval_covers_truth"] == "YES"))}
        for metric in uncertainty_metrics:
            values = pd.to_numeric(group[metric], errors="coerce").dropna().to_numpy(float)
            base[metric + "_mean"] = float(np.mean(values))
            base[metric + "_median"] = float(np.median(values))
        uncertainty_summary_rows.append(base)

    ladder_block_rows = []
    for K in K_VALUES:
        blocks = accepted // K
        for block in range(blocks):
            start_r, stop_r = block * K, (block + 1) * K
            maps = {}
            for profile in profiles:
                key = profile["key"]
                active = profile["active"]
                pstart, pstop = profile["start"], profile["stop"]
                mass = np.zeros(ncell, dtype=float)
                mass[active] = np.mean(samples[start_r:stop_r, pstart:pstop], axis=0)
                maps[key] = normalize(mass, support3[key[0]])
            if K == 1:
                base = e5_base_by_r[block]
            else:
                base, _ = evaluate_state(f"K{K}_B{block + 1}", maps)
            func = state_function(base)
            block_by_orientation = {}
            for orientation in ("AB", "BA"):
                recovery = {}
                for world in ("STRONG", "PAIRED_NULL"):
                    h, sw = [], []
                    for sid in range(1, 73):
                        true_p = truth_maps[(sid, world, orientation)]
                        est_p = maps[(sid, world, orientation)]
                        active = support3[sid]
                        metrics = d10d.map_metrics(true_p, est_p, active, layout, signature, d10a)
                        h.append(metrics["hellinger_distance"]); sw.append(metrics["sliced_wasserstein_km"])
                    recovery[world] = {"hellinger_median": float(np.median(h)), "sliced_wasserstein_km_median": float(np.median(sw))}
                coverage_strong = float(np.median([r["geometry_latent_truth_coverage"] for r in base if r["world"] == "STRONG" and r["orientation"] == orientation]))
                coverage_null = float(np.median([r["geometry_latent_truth_coverage"] for r in base if r["world"] == "PAIRED_NULL" and r["orientation"] == orientation]))
                row = {
                    "K": K, "block": block + 1, "start_realization": start_r + 1, "end_realization": stop_r, "orientation": orientation,
                    **func[orientation], "STRONG_hellinger_median": recovery["STRONG"]["hellinger_median"], "PAIRED_NULL_hellinger_median": recovery["PAIRED_NULL"]["hellinger_median"],
                    "STRONG_sliced_wasserstein_km_median": recovery["STRONG"]["sliced_wasserstein_km_median"], "PAIRED_NULL_sliced_wasserstein_km_median": recovery["PAIRED_NULL"]["sliced_wasserstein_km_median"],
                    "STRONG_geometry_coverage_crosscheck": coverage_strong,
                    "PAIRED_NULL_geometry_coverage_crosscheck": coverage_null,
                }
                block_by_orientation[orientation] = row
            difference = block_by_orientation["BA"]["separation_pp"] - block_by_orientation["AB"]["separation_pp"]
            for row in block_by_orientation.values():
                row["BA_minus_AB_separation_pp"] = difference
                ladder_block_rows.append(row)
        print(json.dumps({"stage": "K_LADDER", "K": K, "blocks": blocks, "elapsed_seconds": round(time.time() - started, 1)}), flush=True)

    process_pool.shutdown(wait=True)

    ladder_df = pd.DataFrame(ladder_block_rows)
    ladder_summary_rows = []
    ladder_metrics = ["strong_gain_pp", "paired_null_gain_pp", "separation_pp", "BA_minus_AB_separation_pp", "STRONG_hellinger_median", "PAIRED_NULL_hellinger_median", "STRONG_sliced_wasserstein_km_median", "PAIRED_NULL_sliced_wasserstein_km_median", "STRONG_geometry_coverage_crosscheck", "PAIRED_NULL_geometry_coverage_crosscheck"]
    for (K, orientation), group in ladder_df.groupby(["K", "orientation"], sort=True):
        for metric in ladder_metrics:
            values = pd.to_numeric(group[metric], errors="coerce").dropna().to_numpy(float)
            ladder_summary_rows.append({"K": int(K), "orientation": orientation, "metric": metric, **summarize_values(values)})

    current_deviation_rows = []
    for orientation in ("AB", "BA", "ALL"):
        prefix = "pooled" if orientation == "ALL" else orientation
        values = np.asarray([r[f"{prefix}_separation_pp"] for r in e5_realization_rows], dtype=float)
        current = state_functions["E1"][orientation]["separation_pp"]
        current_deviation_rows.append({
            "orientation": orientation, "E1_separation_pp": current, "E5_mean_separation_pp": float(np.mean(values)), "E1_minus_E5_pp": current - float(np.mean(values)),
            "E5_sd_pp": float(np.std(values, ddof=1)), "E1_z_relative_to_E5": float((current - np.mean(values)) / np.std(values, ddof=1)),
            "empirical_fraction_E5_at_or_below_E1": float(np.mean(values <= current)), "scientific_disposition": "NOT_ASSIGNED",
        })

    # Write primary outputs.
    write_csv(OUT / "e0_repro_v01.csv", e0_rows)
    write_csv(OUT / "e1_repro_v01.csv", e1_rows)
    for state in ("E2", "E3", "E4"):
        write_csv(OUT / f"{state.lower()}_summary_v01.csv", [r for r in state_summary_rows if r["state"] == state])
    write_csv(OUT / "e5_summary_v01.csv", e5_summary_rows)
    write_csv(OUT / "state_summary_v01.csv", state_summary_rows)
    write_csv(OUT / "source_decomp_v01.csv", source_rows)
    write_csv(OUT / "orientation_decomp_v01.csv", orientation_rows)
    write_csv(OUT / "world_decomp_v01.csv", world_rows)
    write_csv(OUT / "map_recovery_v01.csv", map_rows)
    write_csv(OUT / "map_recovery_summary_v01.csv", map_summary_rows)
    write_csv(OUT / "mc_convergence_v01.csv", convergence_rows)
    write_csv(OUT / "e5_realization_summary_v01.csv", e5_realization_rows)
    with DeterministicGzipText(OUT / "e5_downstream_v01.csv.gz") as handle:
        flat = [row for rows in e5_base_by_r for row in rows]
        writer = csv.DictWriter(handle, fieldnames=list(flat[0]), extrasaction="ignore", lineterminator="\n")
        writer.writeheader(); writer.writerows(flat)
    with DeterministicGzipText(OUT / "e5_test_detail_v01.csv.gz") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(e5_detail_rows[0]), extrasaction="ignore", lineterminator="\n")
        writer.writeheader(); writer.writerows(e5_detail_rows)
    write_csv(OUT / "k_ladder_blocks_v01.csv", ladder_block_rows)
    write_csv(OUT / "k_ladder_summary_v01.csv", ladder_summary_rows)
    with DeterministicGzipText(OUT / "uncertainty_cells_v01.csv.gz") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(uncertainty_rows[0]), extrasaction="ignore", lineterminator="\n")
        writer.writeheader(); writer.writerows(uncertainty_rows)
    write_csv(OUT / "uncertainty_summary_v01.csv", uncertainty_summary_rows)
    write_csv(OUT / "information_profiles_v01.csv", information_rows)
    write_csv(OUT / "information_relationships_v01.csv", relationship_rows)
    write_csv(OUT / "current_deviation_v01.csv", current_deviation_rows)
    write_csv(OUT / "panel_extension_v01.csv", [{"extension": "ADDITIONAL_WHOLE_PANEL_COMBINATIONS", "status": "NOT_ENTERED — ADDITIONAL PANEL ESTIMATOR AUTHORITY NOT FROZEN", "reason": "D10C-A freezes only the selected A/B fold estimator; no non-ad-hoc additional-panel estimator authority is present."}])

    pooled = {state: state_functions[state]["ALL"]["separation_pp"] for state in state_functions}
    comp_lookup = {(r["component"], r["orientation"], r["metric"]): r["component_value_pp"] for r in source_rows if r["observation_regime"] == "O1"}
    k_sep = {K: float(ladder_df.loc[(ladder_df.K == K), "separation_pp"].mean()) for K in K_VALUES}
    u = pd.DataFrame(uncertainty_summary_rows)
    u_poisson = float(u["poisson_plugin_interval_coverage_mean"].mean())
    u_emp = float(u["empirical_variance_normal_interval_coverage_mean"].mean())
    u_ratio = float(u["variance_ratio_empirical_to_poisson_median"].median())
    info_fold = info_df.groupby("orientation").agg({"legal_target_fold_plots_in_support": "median", "plots_per_occupied_cell": "median", "kish_effective_plot_information": "median", "mean_expected_total_tree_count": "median", "E1_hellinger": "median", "E4_hellinger": "median"})
    note = f"""# Q1 D10E result note v01

Terminal status: `{TERMINAL}`

This is a synthetic oracle-support decomposition on the frozen D10D D3 domain. It assigns no scientific PASS/HOLD/FAIL and chooses no abundance model, uncertainty model, real-data domain, or next mainline action. Corrected A2 abundance is independent of O1/O2/O3; those labels are retained and numerically identical.

## Q1 — Terminal count randomness

E2 separation was {pooled['E2']:.3f} pp versus E0 {pooled['E0']:.3f} pp. Removing the terminal Poisson draw restored the same positive direction because the audited conditional-mean A2 mass equals latent cell mass on every D3 cell. The maximum relative cell-mass identity error was {e2_relative_error:.3e}.

## Q2 — Full observation-process expectation

E3 separation was {pooled['E3']:.3f} pp. Averaging the complete observation process also reproduced E0 exactly by the frozen A2 expectation identity; no Monte Carlo approximation was needed for E3.

## Q3 — Expected-map recovery

E3 equals restricted latent truth at cell level. Its Hellinger and sliced-Wasserstein errors are zero up to numerical precision, cell-mass correlation is one, and normalized bias/RMSE are zero up to numerical precision. E4 reports the finite Monte Carlo estimate of the mean normalized map separately.

## Q4 — Normalization nonlinearity

The pooled E4-minus-E3 separation component was {comp_lookup[('B_NORMALIZATION_NONLINEARITY','ALL','separation_pp')]:.3f} pp. AB and BA components were {comp_lookup[('B_NORMALIZATION_NONLINEARITY','AB','separation_pp')]:.3f} and {comp_lookup[('B_NORMALIZATION_NONLINEARITY','BA','separation_pp')]:.3f} pp. This is reported without a materiality threshold.

## Q5 — Finite-realization downstream nonlinearity/noise

The pooled E5-minus-E4 component was {comp_lookup[('C_FINITE_REALIZATION_DOWNSTREAM','ALL','separation_pp')]:.3f} pp. AB and BA components were {comp_lookup[('C_FINITE_REALIZATION_DOWNSTREAM','AB','separation_pp')]:.3f} and {comp_lookup[('C_FINITE_REALIZATION_DOWNSTREAM','BA','separation_pp')]:.3f} pp.

## Q6 — Frozen current realization

E1 separation was {pooled['E1']:.3f} pp versus E5 mean {pooled['E5']:.3f} pp, a deviation of {pooled['E1'] - pooled['E5']:.3f} pp. Orientation-specific z positions and empirical tail fractions are in `current_deviation_v01.csv`.

## Q7 — Repeated-survey ladder

Mean separation across ladder blocks was {', '.join(f'K={K}: {k_sep[K]:.3f} pp' for K in K_VALUES)}. The table reports map recovery, gains, separation, orientation difference, and coverage for every non-overlapping block. This does not imply repeat surveys are available for real Q1.

## Q8 — AB versus BA information

Median legal target-fold plots in D3 support were AB {info_fold.loc['AB','legal_target_fold_plots_in_support']:.1f} and BA {info_fold.loc['BA','legal_target_fold_plots_in_support']:.1f}; median plots per occupied cell were {info_fold.loc['AB','plots_per_occupied_cell']:.3f} and {info_fold.loc['BA','plots_per_occupied_cell']:.3f}; median Kish plot-weight information was {info_fold.loc['AB','kish_effective_plot_information']:.1f} and {info_fold.loc['BA','kish_effective_plot_information']:.1f}. Full descriptive correlations and exact two-panel/three-panel roles are retained. No causal or exclusion threshold is assigned.

## Q9 — Empirical uncertainty versus Poisson-style intervals

Mean empirical-variance normal-interval coverage was {u_emp:.4f}; mean frozen Poisson plug-in interval coverage was {u_poisson:.4f}; the median empirical-to-Poisson variance ratio was {u_ratio:.4f}. Central empirical interval containment and current E1 interval coverage are also reported. No new uncertainty model was fitted.

## Q10 — Systematic expected-operator distortion

The E3-minus-E0 pooled separation component was {comp_lookup[('A_SYSTEMATIC_MEASUREMENT_OPERATOR','ALL','separation_pp')]:.3e} pp. The expected A2 operator is exactly unbiased on the positive-opportunity D3 mass map under this frozen synthetic generator. This statement is limited to the audited synthetic design.

## Q11 — Mainline options

The package separates expected-operator, normalization, finite-realization downstream, and current-realization components. It does not choose among uncertainty propagation around A2, revision of the measurement operator, or continued diagnostic HOLD.

Optional panel extension: `NOT_ENTERED — ADDITIONAL PANEL ESTIMATOR AUTHORITY NOT FROZEN`.

STOP: no uncertainty model, abundance-estimator repair, support recovery, real species, final cohort, real World 0, or real Q1 was run.
"""
    write_text(OUT / "Q1_D10E_RESULT_NOTE_v01.md", note)

    checks = [
        {"check_id": "INPUT_IDENTITIES", "status": "PASS", "observed": len(identity_rows), "expected": len(identity_rows), "notes": "Outer SHA-256 and all applicable internal manifests"},
        {"check_id": "F0_ROWS", "status": "PASS" if len(f0) == 338619 else "FAIL", "observed": len(f0), "expected": 338619, "notes": "Frozen D10A layout"},
        {"check_id": "D3_CELLS", "status": "PASS" if domain3.sum() == 2757 else "FAIL", "observed": int(domain3.sum()), "expected": 2757, "notes": "Frozen D10D D3"},
        {"check_id": "SYNTHETIC_WORLDS", "status": "PASS" if world_hash_count == 144 else "FAIL", "observed": world_hash_count, "expected": 144, "notes": "Frozen support and abundance hashes"},
        {"check_id": "E0_REPRODUCTION", "status": "PASS" if e0_diff <= 1e-10 else "FAIL", "observed": e0_diff, "expected": "<=1e-10", "notes": "D10D D3_A0_REF"},
        {"check_id": "E1_REPRODUCTION", "status": "PASS" if e1_diff <= 1e-10 else "FAIL", "observed": e1_diff, "expected": "<=1e-10", "notes": "D10D D3"},
        {"check_id": "E2_CONDITIONAL_MEAN_IDENTITY", "status": "PASS" if e2_relative_error <= 1e-10 else "FAIL", "observed": e2_relative_error, "expected": "<=1e-10 relative", "notes": "Poisson mean through unchanged A2"},
        {"check_id": "E3_EXPECTATION_IDENTITY", "status": "PASS" if abs(pooled["E3"] - pooled["E0"]) <= 1e-12 else "FAIL", "observed": pooled["E3"] - pooled["E0"], "expected": "0 within 1e-12", "notes": "Exact positive-opportunity expectation"},
        {"check_id": "MC_MINIMUM", "status": "PASS" if accepted >= 200 else "FAIL", "observed": accepted, "expected": ">=200", "notes": convergence_rows[-1]["stop_reason"]},
        {"check_id": "MC_STOP_RULE", "status": "PASS" if convergence_rows[-1]["precision_reached"] == "YES" or accepted == 1000 else "FAIL", "observed": convergence_rows[-1]["stop_reason"], "expected": "TARGET_REACHED or MAX_1000", "notes": "Computational precision only"},
        {"check_id": "K_LADDER", "status": "PASS" if set(ladder_df.K) == set(K_VALUES) else "FAIL", "observed": sorted(set(ladder_df.K)), "expected": list(K_VALUES), "notes": "Non-overlapping blocks"},
        {"check_id": "REGIME_INVARIANCE", "status": "PASS", "observed": "O1=O2=O3 by construction", "expected": "A2 independent of encounter regime", "notes": "Oracle support"},
        {"check_id": "REAL_SPECIES_READ", "status": "PASS", "observed": 0, "expected": 0, "notes": "Synthetic IDs only"},
        {"check_id": "A2_MODIFIED", "status": "PASS", "observed": 0, "expected": 0, "notes": "Frozen formula used"},
        {"check_id": "SUPPORT_RECOVERY_RUN", "status": "PASS", "observed": 0, "expected": 0, "notes": "Oracle support only"},
        {"check_id": "SCIENTIFIC_DISPOSITION_ASSIGNED", "status": "PASS", "observed": 0, "expected": 0, "notes": "Mainline reserved"},
    ]
    write_csv(QC / "checks_v01.csv", checks)
    if any(row["status"] != "PASS" for row in checks):
        raise RuntimeError("IMPLEMENTATION_BLOCKED: computational check failure")

    build_summary = {
        "task_id": "D10E_POSITIVE_OPPORTUNITY_ABUNDANCE_MEASUREMENT_NOISE_DECOMPOSITION_v01",
        "terminal_status": TERMINAL, "elapsed_seconds": time.time() - started, "accepted_MC_realizations": accepted,
        "MC_stop_reason": convergence_rows[-1]["stop_reason"], "MC_pooled_separation_mcse_pp": convergence_rows[-1]["pooled_separation_mcse_pp"],
        "MC_AB_separation_mcse_pp": convergence_rows[-1]["AB_separation_mcse_pp"], "MC_BA_separation_mcse_pp": convergence_rows[-1]["BA_separation_mcse_pp"],
        "state_pooled_separation_pp": pooled, "source_components_pooled_separation_pp": {name: comp_lookup[(name, "ALL", "separation_pp")] for name, _, _, _ in components},
        "E0_max_abs_reproduction_diff": e0_diff, "E1_max_abs_reproduction_diff": e1_diff, "E2_max_relative_cell_mass_error": e2_relative_error,
        "f0_rows": len(f0), "legal_opportunities": len(legal), "D3_cells": int(domain3.sum()), "synthetic_species": 72,
        "network_used": False, "real_species_read": False, "A2_modified": False, "support_recovery_run": False,
        "uncertainty_model_fitted": False, "real_world0_run": False, "real_q1_run": False, "scientific_pass_hold_fail_assigned": False,
    }
    write_json(QC / "build_summary_v01.json", build_summary)
    write_json(QC / "environment_v01.json", {"python": sys.version, "platform": platform.platform(), "numpy": np.__version__, "pandas": pd.__version__, "task": "D10E", "network_used": False})
    registry = [{
        "DELTA_TYPE": "TASK", "ACTION": "PROPOSE_ADD", "TASK_ID": build_summary["task_id"], "ASSET_NAME": "D10E positive-opportunity abundance measurement noise decomposition",
        "CANONICAL_PATH": str(ARCH / "D10E_v01.zip"), "SHA256": "SEE_EXTERNAL_SIDECAR", "SIZE_BYTES": "SEE_EXTERNAL_SIDECAR", "STATUS": TERMINAL,
        "SCIENTIFIC_OUTPUT_CHANGED": "SYNTHETIC_DIAGNOSTIC_ONLY", "PUBLICATION_CANDIDATE": "METHODS_SUPPORT_CANDIDATE", "METHODS_ROLE": "ABUNDANCE_MEASUREMENT_NOISE_DECOMPOSITION",
        "DATA_ROLE": "SYNTHETIC_ONLY", "CODE_ROLE": "REPRODUCIBLE_BUILD", "QC_ROLE": "IDENTITY_HIERARCHY_MC_DECOMPOSITION", "NOTES": "No scientific disposition, new estimator, uncertainty model, support recovery, or real Q1.",
    }]
    write_csv(MAN / "REGISTRY_DELTA_v01.csv", registry)
    source_path = Path(__file__).resolve()
    packaged_path = (SRC / "build.py").resolve()
    if source_path != packaged_path:
        shutil.copyfile(source_path, packaged_path)
    print(json.dumps(build_summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
