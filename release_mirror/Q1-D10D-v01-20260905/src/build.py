from __future__ import annotations

import csv
import gzip
import hashlib
import importlib.util
import io
import json
import math
import platform
import shutil
import sys
import zipfile
from collections import defaultdict
from contextlib import contextmanager
from pathlib import Path

import numpy as np
import pandas as pd


TASK = "D10D_ZERO_OPPORTUNITY_MEASURABLE_DOMAIN_SOURCE_ATTRIBUTION_v01"
TERMINAL = "ZERO_OPPORTUNITY_SOURCE_ATTRIBUTION_COMPLETE_READY_FOR_MAINLINE"
ROOT = Path(r"C:\range_paper")
ARCH = ROOT / "10_archive" / "d10d"
PKG = ARCH / "pkg"
OUT = PKG / "out"
QC = PKG / "qc"
FIG = PKG / "fig"
MAN = PKG / "manifest"
SRC = PKG / "src"
CTL = PKG / "control"
TMP = ROOT / "99_tmp" / "d10d"

D10CR = ROOT / "10_archive" / "d10cr" / "D10CR_v01.zip"
D10CA = ROOT / "10_archive" / "d10ca" / "D10CA_v01.zip"
D10B = ROOT / "10_archive" / "d10b_oracle_source_decomposition_v01" / "Q1_D10B_ORACLE_SUPPORT_DOWNSTREAM_SOURCE_DECOMPOSITION_REPRODUCIBLE_v01.zip"
D10A = ROOT / "10_archive" / "d10a_real_layout_nonoracle_v01" / "Q1_D10A_REAL_LAYOUT_NONORACLE_OBSERVATION_CALIBRATION_REPRODUCIBLE_v01.zip"
REQUEST = Path(r"C:\Users\bug_g\.codex\attachments\e352cb2a-2719-4005-b6df-590b9ff5fb77\pasted-text.txt")
CONTRACT = CTL / "contract_v01.md"

EXPECTED = {
    D10CR: "5ae34a71d50c8bea0809cef77d9835051926f3ea3455b41b2ed913860bab64b1",
    D10CA: "c8f73406f7f192b8f124add3cb0ded7ea65474e8d72d752e37dc557a08588865",
    D10B: "cb041fca5897f31c8ea0bf2a3b29a262a5c83ef44bdfda9a37a0394cfc7cafeb",
    D10A: "20e5d3ed33df6414b72a6e679d5349f3b10fe6397ce73f98b51d0bcc96033013",
    REQUEST: "37f555ce071ea1afec988df302398183f6fdf5c03c94c4b86dff353058aeaacb",
}


def sha256_file(path: Path, chunk: int = 16 * 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def write_csv(path: Path, rows, fields=None) -> None:
    rows = list(rows)
    if fields is None:
        fields = list(rows[0]) if rows else []
    path.parent.mkdir(parents=True, exist_ok=True)
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


@contextmanager
def gzip_text(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = path.open("wb")
    gz = gzip.GzipFile(filename="", mode="wb", fileobj=raw, compresslevel=9, mtime=0)
    text = io.TextIOWrapper(gz, encoding="utf-8-sig", newline="")
    try:
        yield text
    finally:
        text.close()
        raw.close()


def zip_member_bytes(path: Path, suffix: str) -> bytes:
    with zipfile.ZipFile(path) as archive:
        names = [name for name in archive.namelist() if name.endswith(suffix)]
        if len(names) != 1:
            raise RuntimeError(f"Expected one member ending {suffix!r} in {path}; found {len(names)}")
        return archive.read(names[0])


def zip_csv(path: Path, suffix: str, **kwargs) -> pd.DataFrame:
    return pd.read_csv(io.BytesIO(zip_member_bytes(path, suffix)), **kwargs)


def zip_gzip_csv(path: Path, suffix: str, **kwargs) -> pd.DataFrame:
    payload = zip_member_bytes(path, suffix)
    return pd.read_csv(gzip.GzipFile(fileobj=io.BytesIO(payload)), **kwargs)


def import_zip_module(path: Path, suffix: str, name: str):
    TMP.mkdir(parents=True, exist_ok=True)
    target = TMP / f"{name}.py"
    target.write_bytes(zip_member_bytes(path, suffix))
    spec = importlib.util.spec_from_file_location(name, target)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def verify_d10cr_internal() -> tuple[int, list[str]]:
    bad = []
    with zipfile.ZipFile(D10CR) as archive:
        rows = list(csv.DictReader(io.StringIO(archive.read("manifest/sha256sums_v01.csv").decode("utf-8-sig"))))
        for row in rows:
            payload = archive.read(row["relative_path"])
            if len(payload) != int(row["size_bytes"]) or sha256_bytes(payload) != row["sha256"]:
                bad.append(row["relative_path"])
    return len(rows), bad


def normalize(values: np.ndarray, mask: np.ndarray | None = None) -> np.ndarray:
    result = np.asarray(values, dtype=float).copy()
    if mask is not None:
        result[~mask] = 0.0
    total = float(result.sum())
    if total <= 0:
        raise RuntimeError("IMPLEMENTATION_BLOCKED: nonpositive normalized total")
    result /= total
    return result


def safe_corr(a, b) -> float:
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    ok = np.isfinite(a) & np.isfinite(b)
    if ok.sum() < 3 or np.std(a[ok]) < 1e-15 or np.std(b[ok]) < 1e-15:
        return float("nan")
    return float(np.corrcoef(a[ok], b[ok])[0, 1])


def spearman(a, b) -> float:
    x = pd.Series(a, dtype=float).rank(method="average").to_numpy(float)
    y = pd.Series(b, dtype=float).rank(method="average").to_numpy(float)
    return safe_corr(x, y)


def quantile(values, q) -> float:
    return float(np.quantile(np.asarray(values, dtype=float), q))


def map_metrics(true_p, est_p, active, layout, signature, d10a):
    h = float(np.sqrt(np.sum((np.sqrt(true_p) - np.sqrt(est_p)) ** 2)) / math.sqrt(2.0))
    sw = float(d10a.signature_distance(signature(true_p), signature(est_p)))
    coords = layout["metric_coords"]
    tc = np.sum(coords * true_p[:, None], axis=0)
    ec = np.sum(coords * est_p[:, None], axis=0)
    return {
        "hellinger_distance": h,
        "sliced_wasserstein_km": sw,
        "centroid_displacement_km": float(np.linalg.norm(tc - ec)),
        "true_entropy": float(-np.sum(true_p[active] * np.log(true_p[active] + 1e-15))),
        "estimated_entropy": float(-np.sum(est_p[active] * np.log(est_p[active] + 1e-15))),
        "true_concentration": float(np.sum(true_p**2)),
        "estimated_concentration": float(np.sum(est_p**2)),
    }


def evaluate_detailed(layer, world, orientation, populations, truths, ensemble_info, layout, param, d10a, signature):
    species_ids = sorted(ensemble_info)
    ncell = len(layout["cells"])
    population_signatures = {sid: signature(populations[sid]) for sid in species_ids}
    truth_signatures = {sid: signature(truths[sid]) for sid in species_ids}
    rows, details = [], []
    for replicate, seed in enumerate(param["split_seeds"], start=1):
        permutation = np.random.default_rng(seed).permutation(species_ids)
        n = len(permutation)
        ntrain = int(param["split_allocation"][0] * n)
        ncal = int(param["split_allocation"][1] * n)
        train_ids = permutation[:ntrain].tolist()
        calibration_ids = permutation[ntrain:ntrain + ncal].tolist()
        test_ids = permutation[ntrain + ncal:].tolist()
        gamma, predictor = d10a.fit_allocation_models(ensemble_info, populations, train_ids, param, ncell)
        state_stats = {}
        species_stats = defaultdict(dict)
        for geometry, label in ((False, "world0"), (True, "geometry")):
            centers = {sid: predictor(sid, geometry) for sid in calibration_ids + test_ids}
            center_signatures = {sid: [signature(center) for center in centers[sid]] for sid in centers}
            scores = [min(d10a.signature_distance(candidate, population_signatures[sid]) for candidate in center_signatures[sid]) for sid in calibration_ids]
            radius = d10a.conformal_quantile(np.asarray(scores), param["conformal_level"])
            observed_covered, truth_covered = [], []
            observed_errors, truth_errors, diameters, dispersions = [], [], [], []
            for sid in test_ids:
                sigs = center_signatures[sid]
                observed_distance = min(d10a.signature_distance(candidate, population_signatures[sid]) for candidate in sigs)
                truth_distance = min(d10a.signature_distance(candidate, truth_signatures[sid]) for candidate in sigs)
                point = np.mean(np.vstack(centers[sid]), axis=0)
                point /= point.sum()
                point_signature = signature(point)
                observed_error = d10a.signature_distance(point_signature, population_signatures[sid])
                truth_error = d10a.signature_distance(point_signature, truth_signatures[sid])
                dispersion = d10a.center_diameter(sigs)
                diameter = dispersion + 2 * radius
                observed_covered.append(observed_distance <= radius)
                truth_covered.append(truth_distance <= radius)
                observed_errors.append(observed_error)
                truth_errors.append(truth_error)
                dispersions.append(dispersion)
                diameters.append(diameter)
                species_stats[sid][label] = {
                    "observed_error": float(observed_error), "truth_error": float(truth_error),
                    "observed_covered": bool(observed_distance <= radius), "truth_covered": bool(truth_distance <= radius),
                    "set_diameter": float(diameter), "support_dispersion": float(dispersion), "radius": float(radius),
                }
            state_stats[label] = {
                "observed_coverage": float(np.mean(observed_covered)), "truth_coverage": float(np.mean(truth_covered)),
                "observed_error": float(np.mean(observed_errors)), "truth_error": float(np.mean(truth_errors)),
                "set_diameter": float(np.mean(diameters)), "support_dispersion": float(np.mean(dispersions)),
            }
        w0, geo = state_stats["world0"], state_stats["geometry"]
        rows.append({
            "layer": layer, "model": "ORACLE", "world": world, "orientation": orientation,
            "replicate": replicate, "split_seed": seed, "n_species": n, "n_train": len(train_ids),
            "n_calibration": len(calibration_ids), "n_test": len(test_ids), "world0_gamma": gamma,
            "latent_truth_geometry_gain_pct": 100 * (w0["truth_error"] - geo["truth_error"]) / max(w0["truth_error"], 1e-12),
            "predictive_set_gain_pct": 100 * (w0["set_diameter"] - geo["set_diameter"]) / max(w0["set_diameter"], 1e-12),
            "observed_map_error_gain_pct": 100 * (w0["observed_error"] - geo["observed_error"]) / max(w0["observed_error"], 1e-12),
            "geometry_latent_truth_coverage": geo["truth_coverage"], "geometry_observed_map_coverage": geo["observed_coverage"],
            "world0_latent_truth_coverage": w0["truth_coverage"], "world0_observed_map_coverage": w0["observed_coverage"],
            "world0_set_diameter": w0["set_diameter"], "geometry_set_diameter": geo["set_diameter"],
            "world0_latent_truth_error": w0["truth_error"], "geometry_latent_truth_error": geo["truth_error"],
            "world0_observed_map_error": w0["observed_error"], "geometry_observed_map_error": geo["observed_error"],
            "world0_support_dispersion": w0["support_dispersion"], "geometry_support_dispersion": geo["support_dispersion"],
        })
        for sid in test_ids:
            a, b = species_stats[sid]["world0"], species_stats[sid]["geometry"]
            details.append({
                "layer": layer, "world": world, "orientation": orientation, "replicate": replicate,
                "split_seed": seed, "synthetic_species_id": f"SYN{sid:03d}", "split_role": "TEST",
                "world0_latent_truth_error": a["truth_error"], "geometry_latent_truth_error": b["truth_error"],
                "individual_latent_truth_geometry_gain_pct": 100 * (a["truth_error"] - b["truth_error"]) / max(a["truth_error"], 1e-12),
                "world0_observed_map_error": a["observed_error"], "geometry_observed_map_error": b["observed_error"],
                "individual_observed_map_error_gain_pct": 100 * (a["observed_error"] - b["observed_error"]) / max(a["observed_error"], 1e-12),
                "world0_set_diameter": a["set_diameter"], "geometry_set_diameter": b["set_diameter"],
                "individual_predictive_set_gain_pct": 100 * (a["set_diameter"] - b["set_diameter"]) / max(a["set_diameter"], 1e-12),
                "world0_truth_covered": "YES" if a["truth_covered"] else "NO",
                "geometry_truth_covered": "YES" if b["truth_covered"] else "NO",
            })
    return rows, details


def compare_released(regenerated, released, released_layer):
    r = pd.DataFrame(regenerated).copy()
    f = released.loc[released["layer"] == released_layer].copy()
    keys = ["world", "observation_regime", "orientation", "replicate", "split_seed"]
    for col in ("replicate", "split_seed"):
        r[col] = r[col].astype(str)
        f[col] = f[col].astype(str)
    r = r.sort_values(keys).reset_index(drop=True)
    f = f.sort_values(keys).reset_index(drop=True)
    if len(r) != len(f) or not (r[keys].astype(str) == f[keys].astype(str)).all().all():
        return False, float("inf")
    numeric = [c for c in r.columns if c in f.columns and c not in keys + ["layer", "model", "source_identity"]]
    diffs = []
    for col in numeric:
        rv = pd.to_numeric(r[col], errors="coerce")
        fv = pd.to_numeric(f[col], errors="coerce")
        if rv.notna().any() or fv.notna().any():
            diffs.append(float(np.nanmax(np.abs(rv.to_numpy(float) - fv.to_numpy(float)))))
    maximum = max(diffs) if diffs else 0.0
    return maximum <= 1e-10, maximum


def add_relationship(rows, frame, level, state, predictor, outcome, world="ALL", orientation="ALL", notes=""):
    x = pd.to_numeric(frame[predictor], errors="coerce").to_numpy(float)
    y = pd.to_numeric(frame[outcome], errors="coerce").to_numpy(float)
    ok = np.isfinite(x) & np.isfinite(y)
    for statistic, value in (("pearson_r", safe_corr(x[ok], y[ok])), ("spearman_rho", spearman(x[ok], y[ok]))):
        rows.append({
            "analysis_level": level, "state": state, "world": world, "orientation": orientation,
            "predictor": predictor, "outcome": outcome, "statistic": statistic,
            "value": value, "n": int(ok.sum()), "notes": notes,
        })


def main():
    if not CONTRACT.exists():
        raise RuntimeError("IMPLEMENTATION_BLOCKED: frozen D10D contract missing")
    for directory in (OUT, QC, FIG, MAN, SRC):
        if directory.exists():
            shutil.rmtree(directory)
        directory.mkdir(parents=True, exist_ok=True)
    TMP.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(REQUEST, CTL / "request.txt")

    identity = []
    for path, expected in {**EXPECTED, CONTRACT: "FROZEN_BEFORE_D0_D1_D2_D3"}.items():
        actual = sha256_file(path)
        identity.append({
            "asset": path.name, "path": str(path), "size_bytes": path.stat().st_size,
            "expected_sha256": expected, "actual_sha256": actual,
            "status": "PASS" if expected.startswith("FROZEN_") or actual == expected else "FAIL",
        })
    internal_n, internal_bad = verify_d10cr_internal()
    identity.append({
        "asset": "D10CR_internal_manifest", "path": str(D10CR), "size_bytes": internal_n,
        "expected_sha256": "ALL_INTERNAL_MEMBERS_MATCH", "actual_sha256": "PASS" if not internal_bad else ";".join(internal_bad),
        "status": "PASS" if not internal_bad else "FAIL",
    })
    write_csv(QC / "input_id_v01.csv", identity)
    if any(row["status"] != "PASS" for row in identity):
        raise RuntimeError("INPUT_BLOCKED_FROZEN_IDENTITY_FAILURE")

    d10a = import_zip_module(D10A, "build_d10a_real_layout_nonoracle_v01.py", "d10a_release")
    d10b = import_zip_module(D10B, "build_d10b_oracle_source_decomposition_v01.py", "d10b_release")
    param = json.loads(zip_member_bytes(D10A, "parameters_d10a_real_layout_nonoracle_v01.json").decode("utf-8"))
    f0 = zip_csv(D10A, "Q1_D10A_REAL_F0_OPPORTUNITY_LAYOUT_v01.csv", dtype=str, keep_default_na=False)
    truth_df = zip_csv(D10CR, "out/truth_v01.csv", dtype=str, keep_default_na=False)
    a2_df = zip_gzip_csv(D10CR, "out/a2_v01.csv.gz", dtype=str, keep_default_na=False)
    published_down = zip_csv(D10CR, "out/downstream_v01.csv", dtype=str, keep_default_na=False)
    published_recovery = zip_csv(D10CR, "out/recovery_metrics_v01.csv", dtype=str, keep_default_na=False)
    world_id = zip_csv(D10CR, "qc/world_id_v01.csv", dtype=str, keep_default_na=False)
    d10cr_summary = json.loads(zip_member_bytes(D10CR, "qc/build_summary_v01.json").decode("utf-8"))
    crosswalk = zip_gzip_csv(D10CA, "plot_block_xwalk_v01.csv.gz", dtype=str, keep_default_na=False)

    legal = f0.loc[f0["base_legitimate_opportunity_flag"] == "YES"].copy()
    plots = {}
    for row in legal.to_dict("records"):
        plots[row["plot_cn"]] = {
            "base_legitimate_opportunity_flag": True, "cell_50km": row["cell_50km"],
            "manual": row["manual"], "designcd": row["designcd"],
            "effort_score": float(row["partial_sampling_effort"]),
            "partial_sampling_flag": row["partial_sampling_flag"] == "YES", "fold": row["fold"],
        }
    layout = d10a.build_layout_arrays(plots, param)
    cells = list(layout["cells"])
    cell_index = {cell: i for i, cell in enumerate(cells)}
    ncell = len(cells)
    if len(f0) != 338619 or len(legal) != 134846 or ncell != 3011:
        raise RuntimeError("INPUT_BLOCKED_FROZEN_IDENTITY_FAILURE: F0 dimensions")

    fold_count = {fold: np.bincount(layout["folds"][fold]["plot_cell"], minlength=ncell).astype(int) for fold in ("A", "B")}
    fold_effort = {fold: np.bincount(layout["folds"][fold]["plot_cell"], weights=layout["folds"][fold]["plot_effort"], minlength=ncell) for fold in ("A", "B")}
    domain_a = fold_count["A"] > 0
    domain_b = fold_count["B"] > 0
    domain_common = domain_a & domain_b

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
        fold_design[fold] = {
            "rows": selected, "pcell": pcell, "ti": ti,
            "ti_cell": np.bincount(pcell, weights=ti, minlength=ncell),
        }

    supports = {sid: np.zeros(ncell, dtype=bool) for sid in range(1, 73)}
    abundances = {}
    for sid in range(1, 73):
        for world in ("STRONG", "PAIRED_NULL"):
            abundances[(sid, world)] = np.zeros(ncell, dtype=float)
    for row in truth_df.to_dict("records"):
        sid = int(row["synthetic_species_id"][3:])
        idx = cell_index[row["cell_50km"]]
        supports[sid][idx] = True
        abundances[(sid, row["world"])][idx] = float(row["latent_allocation"])
    if any(abs(arr.sum() - 1.0) > 1e-12 for arr in abundances.values()):
        raise RuntimeError("INPUT_BLOCKED_FROZEN_IDENTITY_FAILURE: latent normalization")

    world_ref = {(row["synthetic_species_id"], row["world"]): row for row in world_id.to_dict("records")}
    hash_match = 0
    for sid in range(1, 73):
        for world in ("STRONG", "PAIRED_NULL"):
            ref = world_ref[(f"SYN{sid:03d}", world)]
            support_hash = d10b.array_sha256(np.where(supports[sid])[0].astype(np.int64))
            abundance_hash = d10b.array_sha256(abundances[(sid, world)].astype(np.float64))
            if support_hash == ref["support_index_sha256"] and abundance_hash == ref["latent_abundance_sha256"]:
                hash_match += 1
    if hash_match != 144:
        raise RuntimeError("INPUT_BLOCKED_FROZEN_IDENTITY_FAILURE: D10CR world arrays")

    a2_mass = {(sid, world, orientation): np.zeros(ncell, dtype=float) for sid in range(1, 73) for world in ("STRONG", "PAIRED_NULL") for orientation in ("AB", "BA")}
    zero_flag_mismatch = 0
    for row in a2_df.to_dict("records"):
        sid = int(row["synthetic_species_id"][3:])
        idx = cell_index[row["cell_50km"]]
        orientation = row["orientation"]
        fold = "B" if orientation == "AB" else "A"
        a2_mass[(sid, row["world"], orientation)][idx] = float(row["estimated_cell_mass"])
        expected_zero = fold_count[fold][idx] == 0
        if expected_zero != (row["structural_zero_exposure"] == "YES"):
            zero_flag_mismatch += 1
    if zero_flag_mismatch:
        raise RuntimeError("INPUT_BLOCKED_FROZEN_IDENTITY_FAILURE: D10CR zero flags")

    domain_rows = []
    for idx, cell in enumerate(cells):
        domain_rows.append({
            "cell_50km": cell, "A_legal_opportunities": fold_count["A"][idx], "B_legal_opportunities": fold_count["B"][idx],
            "A_effort_sum": fold_effort["A"][idx], "B_effort_sum": fold_effort["B"][idx],
            "A_fold_ti_weight_sum": fold_design["A"]["ti_cell"][idx], "B_fold_ti_weight_sum": fold_design["B"]["ti_cell"][idx],
            "A_measurable": "YES" if domain_a[idx] else "NO", "B_measurable": "YES" if domain_b[idx] else "NO",
            "D2_AB_included": "YES" if domain_b[idx] else "NO", "D2_BA_included": "YES" if domain_a[idx] else "NO",
            "D3_common_included": "YES" if domain_common[idx] else "NO",
            "zero_opportunity_class": "BOTH" if not domain_a[idx] and not domain_b[idx] else ("A_ONLY_ZERO" if not domain_a[idx] else ("B_ONLY_ZERO" if not domain_b[idx] else "NONE")),
        })
    write_csv(OUT / "domain_cells_v01.csv", domain_rows)
    write_csv(OUT / "zero_cells_v01.csv", [r for r in domain_rows if r["zero_opportunity_class"] != "NONE"])

    def domain_design_row(state, orientation, mask):
        fold = "B" if orientation == "AB" else "A"
        meta = fold_design[fold]
        retained_plot = mask[meta["pcell"]]
        rows = meta["rows"]
        block_area = rows.groupby("final_effective_design_block_id", sort=True)["ti_population_area_acres"].first().astype(float)
        retained_blocks = set(rows.loc[retained_plot, "final_effective_design_block_id"])
        represented = float(block_area.loc[block_area.index.isin(retained_blocks)].sum())
        return {
            "state": state, "orientation": orientation, "target_fold": fold,
            "total_F0_cells": ncell, "retained_cells": int(mask.sum()), "removed_cells": int((~mask).sum()),
            "fraction_F0_cells_retained": float(mask.mean()),
            "target_fold_legal_plots_total": int(len(meta["pcell"])), "target_fold_legal_plots_retained": int(retained_plot.sum()),
            "target_fold_legal_plot_fraction_retained": float(retained_plot.mean()),
            "fold_specific_TI_sum_total": float(meta["ti"].sum()), "fold_specific_TI_sum_retained": float(meta["ti"][retained_plot].sum()),
            "fold_specific_TI_fraction_retained": float(meta["ti"][retained_plot].sum() / meta["ti"].sum()),
            "effective_block_area_acres_total": float(block_area.sum()), "effective_block_area_acres_represented": represented,
            "effective_block_area_fraction_represented": represented / float(block_area.sum()),
            "area_interpretation": "TI-weight and block-area representation from frozen D10C-A; not polygonal geographic area",
        }

    domain_summary = [
        domain_design_row("FULL", "AB", np.ones(ncell, dtype=bool)), domain_design_row("FULL", "BA", np.ones(ncell, dtype=bool)),
        domain_design_row("D2", "AB", domain_b), domain_design_row("D2", "BA", domain_a),
        domain_design_row("D3", "AB", domain_common), domain_design_row("D3", "BA", domain_common),
    ]
    write_csv(OUT / "domain_summary_v01.csv", domain_summary)

    state_inputs = {}
    state_supports = {}
    d1_cells, domain_layers, domain_species, map_rows, zero_species = [], [], [], [], []
    signature = d10a.build_spatial_signature_engine(layout, param)

    for world in ("STRONG", "PAIRED_NULL"):
        for orientation, fold in (("AB", "B"), ("BA", "A")):
            full_truths, d0_pops, d1_pops = {}, {}, {}
            d2_truths, d2_pops, d2_supports = {}, {}, {}
            d3_truths, d3_pops, d3_supports = {}, {}, {}
            target_domain = domain_b if orientation == "AB" else domain_a
            zero_domain = ~target_domain
            for sid in range(1, 73):
                support = supports[sid]
                true_p = abundances[(sid, world)]
                raw_a2 = a2_mass[(sid, world, orientation)]
                d0 = normalize(raw_a2)
                d1_raw = raw_a2.copy()
                d1_raw[zero_domain & support] = true_p[zero_domain & support] * 100_000_000.0
                d1 = normalize(d1_raw)
                support2 = support & target_domain
                support3 = support & domain_common
                if not support2.any() or not support3.any():
                    raise RuntimeError("IMPLEMENTATION_BLOCKED: empty restricted oracle support")
                truth2 = normalize(true_p, support2)
                pop2 = normalize(raw_a2, support2)
                truth3 = normalize(true_p, support3)
                pop3 = normalize(raw_a2, support3)
                full_truths[sid] = true_p
                d0_pops[sid] = d0
                d1_pops[sid] = d1
                d2_truths[sid] = truth2
                d2_pops[sid] = pop2
                d2_supports[sid] = support2
                d3_truths[sid] = truth3
                d3_pops[sid] = pop3
                d3_supports[sid] = support3

                zero_cells = support & zero_domain
                zero_mass = float(true_p[zero_cells].sum())
                d0m = map_metrics(true_p, d0, np.where(support)[0], layout, signature, d10a)
                d1m = map_metrics(true_p, d1, np.where(support)[0], layout, signature, d10a)
                zero_species.append({
                    "synthetic_species_id": f"SYN{sid:03d}", "world": world, "orientation": orientation, "target_fold": fold,
                    "oracle_support_cells": int(support.sum()), "zero_opportunity_support_cells": int(zero_cells.sum()),
                    "zero_opportunity_support_fraction": float(zero_cells.sum() / support.sum()),
                    "zero_opportunity_truth_mass_fraction": zero_mass,
                    "D0_hellinger": d0m["hellinger_distance"], "D1_hellinger": d1m["hellinger_distance"],
                    "D1_minus_D0_hellinger": d1m["hellinger_distance"] - d0m["hellinger_distance"],
                    "D0_sliced_wasserstein_km": d0m["sliced_wasserstein_km"], "D1_sliced_wasserstein_km": d1m["sliced_wasserstein_km"],
                    "D1_minus_D0_sliced_wasserstein_km": d1m["sliced_wasserstein_km"] - d0m["sliced_wasserstein_km"],
                })
                for idx in np.where(support)[0]:
                    d1_cells.append({
                        "synthetic_species_id": f"SYN{sid:03d}", "world": world, "orientation": orientation, "target_fold": fold,
                        "cell_50km": cells[idx], "zero_target_fold_opportunity": "YES" if zero_domain[idx] else "NO",
                        "A0_latent_cell_mass": 100_000_000.0 * true_p[idx], "D0_A2_cell_mass": raw_a2[idx],
                        "D1_pre_normalization_cell_mass": d1_raw[idx], "D1_normalized_allocation": d1[idx],
                        "positive_opportunity_A2_unchanged": "NA" if zero_domain[idx] else ("YES" if d1_raw[idx] == raw_a2[idx] else "NO"),
                    })
                for state, mask, retained_support, truth_state, pop_state in (
                    ("D2", target_domain, support2, truth2, pop2), ("D3", domain_common, support3, truth3, pop3),
                ):
                    retained_truth = float(np.clip(true_p[retained_support].sum(), 0.0, 1.0))
                    total_a2 = float(raw_a2.sum())
                    retained_a2 = float(raw_a2[retained_support].sum())
                    retained_a2_fraction = float(np.clip(retained_a2 / total_a2, 0.0, 1.0))
                    domain_species.append({
                        "state": state, "synthetic_species_id": f"SYN{sid:03d}", "world": world, "orientation": orientation,
                        "target_fold": fold, "original_support_cells": int(support.sum()), "retained_support_cells": int(retained_support.sum()),
                        "lost_support_cells": int(support.sum() - retained_support.sum()), "support_fraction_retained": float(retained_support.sum() / support.sum()),
                        "support_fraction_lost": float(1 - retained_support.sum() / support.sum()),
                        "latent_truth_mass_fraction_retained": retained_truth, "latent_truth_mass_fraction_lost": max(0.0, 1.0 - retained_truth),
                        "A2_raw_mass_fraction_retained": retained_a2_fraction, "A2_raw_mass_fraction_lost": max(0.0, 1.0 - retained_a2_fraction),
                    })
                    for idx in np.where(support)[0]:
                        domain_layers.append({
                            "state": state, "synthetic_species_id": f"SYN{sid:03d}", "world": world, "orientation": orientation,
                            "target_fold": fold, "cell_50km": cells[idx], "domain_included": "YES" if mask[idx] else "NO",
                            "restricted_oracle_support": "YES" if retained_support[idx] else "NO",
                            "A0_full_allocation": true_p[idx], "A2_full_cell_mass": raw_a2[idx],
                            "A0_restricted_allocation": truth_state[idx], "A2_restricted_allocation": pop_state[idx],
                        })

                for state, pop, truth_state, active, mask in (
                    ("D0", d0, true_p, np.where(support)[0], support),
                    ("D1", d1, true_p, np.where(support)[0], support),
                    ("D2", pop2, truth2, np.where(support2)[0], support2),
                    ("D3", pop3, truth3, np.where(support3)[0], support3),
                ):
                    metrics = map_metrics(truth_state, pop, active, layout, signature, d10a)
                    map_rows.append({
                        "state": state, "synthetic_species_id": f"SYN{sid:03d}", "world": world, "orientation": orientation,
                        "target_fold": fold, "original_support_cells": int(support.sum()), "evaluated_support_cells": int(mask.sum()),
                        "zero_opportunity_truth_mass_fraction_full_domain": zero_mass,
                        "latent_truth_mass_fraction_retained": float(true_p[mask].sum()), **metrics,
                    })

            key = (world, orientation)
            state_inputs[("A0_REF",) + key] = (full_truths, full_truths)
            state_supports[("A0_REF",) + key] = supports
            state_inputs[("D0",) + key] = (d0_pops, full_truths)
            state_supports[("D0",) + key] = supports
            state_inputs[("D1",) + key] = (d1_pops, full_truths)
            state_supports[("D1",) + key] = supports
            state_inputs[("D2",) + key] = (d2_pops, d2_truths)
            state_supports[("D2",) + key] = d2_supports
            state_inputs[("D2_A0_REF",) + key] = (d2_truths, d2_truths)
            state_supports[("D2_A0_REF",) + key] = d2_supports
            state_inputs[("D3",) + key] = (d3_pops, d3_truths)
            state_supports[("D3",) + key] = d3_supports
            state_inputs[("D3_A0_REF",) + key] = (d3_truths, d3_truths)
            state_supports[("D3_A0_REF",) + key] = d3_supports

    write_csv(OUT / "zero_species_v01.csv", zero_species)
    with gzip_text(OUT / "d1_cells_v01.csv.gz") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(d1_cells[0]), lineterminator="\n"); writer.writeheader(); writer.writerows(d1_cells)
    with gzip_text(OUT / "domain_layers_v01.csv.gz") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(domain_layers[0]), lineterminator="\n"); writer.writeheader(); writer.writerows(domain_layers)
    write_csv(OUT / "species_domain_v01.csv", domain_species)
    write_csv(OUT / "map_metrics_v01.csv", map_rows)

    frontier_rows = []
    domain_frame = pd.DataFrame(domain_species)
    for keys, group in list(domain_frame.groupby(["state", "world", "orientation"], sort=True)) + [(('ALL', 'ALL', 'ALL'), domain_frame)]:
        state, world, orientation = keys
        for metric, cuts in (
            ("support_fraction_lost", [0.0, 0.05, 0.10, 0.25, 0.50]),
            ("latent_truth_mass_fraction_lost", [0.0, 0.001, 0.01, 0.05, 0.10, 0.25, 0.50]),
        ):
            values = pd.to_numeric(group[metric]).to_numpy(float)
            for cut in cuts:
                n = int(np.sum(values > cut)) if cut == 0 else int(np.sum(values >= cut))
                frontier_rows.append({
                    "state": state, "world": world, "orientation": orientation, "metric": metric,
                    "descriptive_cutoff": cut, "comparison": ">0" if cut == 0 else ">=cutoff",
                    "n_profiles": len(values), "n_at_or_beyond_cutoff": n, "fraction_at_or_beyond_cutoff": n / len(values),
                    "decision_status": "DESCRIPTIVE_FRONTIER_ONLY_NO_ACCEPTABLE_LOSS_THRESHOLD",
                })
    write_csv(OUT / "trunc_frontier_v01.csv", frontier_rows)

    downstream_base, test_detail = [], []
    for state in ("A0_REF", "D0", "D1", "D2", "D3", "D2_A0_REF", "D3_A0_REF"):
        for world in ("STRONG", "PAIRED_NULL"):
            for orientation in ("AB", "BA"):
                pops, truths = state_inputs[(state, world, orientation)]
                ss = state_supports[(state, world, orientation)]
                ensemble = d10b.oracle_geometry_ensemble(layout, ss, d10a)
                rows, detail = evaluate_detailed(state, world, orientation, pops, truths, ensemble, layout, param, d10a, signature)
                downstream_base.extend(rows)
                test_detail.extend(detail)
    downstream = d10b.expand_regimes(downstream_base, param["observation_regimes"])
    d0_ok, d0_diff = compare_released([r for r in downstream if r["layer"] == "D0"], published_down, "A2")
    a0_ok, a0_diff = compare_released([r for r in downstream if r["layer"] == "A0_REF"], published_down, "A0")
    if not d0_ok or not a0_ok:
        raise RuntimeError(f"IMPLEMENTATION_BLOCKED: D0/A0 reproduction D0={d0_diff} A0={a0_diff}")
    write_csv(OUT / "d0_repro_v01.csv", [r for r in downstream if r["layer"] == "D0"])
    write_csv(OUT / "downstream_v01.csv", downstream)
    with gzip_text(OUT / "test_detail_v01.csv.gz") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(test_detail[0]), lineterminator="\n"); writer.writeheader(); writer.writerows(test_detail)

    separation = []
    for state in ("A0_REF", "D0", "D1", "D2", "D3", "D2_A0_REF", "D3_A0_REF"):
        separation.extend(d10b.strong_null_separation([r for r in downstream if r["layer"] == state]))
    write_csv(OUT / "separation_v01.csv", separation)
    down_df = pd.DataFrame(downstream)
    sep_df = pd.DataFrame(separation)
    numeric_down = [
        "latent_truth_geometry_gain_pct", "predictive_set_gain_pct", "observed_map_error_gain_pct",
        "geometry_latent_truth_coverage", "geometry_observed_map_coverage", "world0_latent_truth_coverage", "world0_observed_map_coverage",
    ]
    for col in numeric_down:
        down_df[col] = pd.to_numeric(down_df[col])
    sep_metric = "strong_minus_paired_null_latent_truth_geometry_gain_pct"
    sep_df[sep_metric] = pd.to_numeric(sep_df[sep_metric])
    common_rows = []
    for key, group in down_df.groupby(["layer", "observation_regime", "orientation"], sort=True):
        state, regime, orientation = key
        strong = group[group["world"] == "STRONG"]
        null = group[group["world"] == "PAIRED_NULL"]
        sg = sep_df[(sep_df["layer"] == state) & (sep_df["observation_regime"] == regime) & (sep_df["orientation"] == orientation)]
        common_rows.append({
            "state": state, "observation_regime": regime, "orientation": orientation, "n_split_replicates": len(strong),
            "strong_geometry_gain_pct_median": strong["latent_truth_geometry_gain_pct"].median(),
            "paired_null_geometry_gain_pct_median": null["latent_truth_geometry_gain_pct"].median(),
            "strong_minus_paired_null_geometry_gain_pct_median": sg[sep_metric].median(),
            "strong_predictive_set_gain_pct_median": strong["predictive_set_gain_pct"].median(),
            "paired_null_predictive_set_gain_pct_median": null["predictive_set_gain_pct"].median(),
            "strong_geometry_truth_coverage_median": strong["geometry_latent_truth_coverage"].median(),
            "paired_null_geometry_truth_coverage_median": null["geometry_latent_truth_coverage"].median(),
            "strong_world0_truth_coverage_median": strong["world0_latent_truth_coverage"].median(),
            "paired_null_world0_truth_coverage_median": null["world0_latent_truth_coverage"].median(),
        })
    write_csv(OUT / "common_v01.csv", common_rows)

    common_df = pd.DataFrame(common_rows)
    orientation_rows = []
    for (state, regime), group in common_df.groupby(["state", "observation_regime"], sort=True):
        for metric in [
            "strong_geometry_gain_pct_median", "paired_null_geometry_gain_pct_median",
            "strong_minus_paired_null_geometry_gain_pct_median", "strong_predictive_set_gain_pct_median",
            "paired_null_predictive_set_gain_pct_median", "strong_geometry_truth_coverage_median",
            "paired_null_geometry_truth_coverage_median",
        ]:
            ab = float(group.loc[group["orientation"] == "AB", metric].iloc[0])
            ba = float(group.loc[group["orientation"] == "BA", metric].iloc[0])
            orientation_rows.append({
                "state": state, "observation_regime": regime, "metric": metric,
                "AB_median": ab, "BA_median": ba, "BA_minus_AB": ba - ab,
                "interpretation": "DESCRIPTIVE_NO_CONSISTENCY_THRESHOLD",
            })
    write_csv(OUT / "orientation_v01.csv", orientation_rows)

    reference_for = {"A0_REF": "A0_REF", "D0": "A0_REF", "D1": "A0_REF", "D2": "D2_A0_REF", "D3": "D3_A0_REF", "D2_A0_REF": "D2_A0_REF", "D3_A0_REF": "D3_A0_REF"}
    common_index = {(r["state"], r["observation_regime"], r["orientation"]): r for r in common_rows}
    attribution_rows = []
    for row in common_rows:
        state, regime, orientation = row["state"], row["observation_regime"], row["orientation"]
        value = float(row["strong_minus_paired_null_geometry_gain_pct_median"])
        ref = reference_for[state]
        ref_value = float(common_index[(ref, regime, orientation)]["strong_minus_paired_null_geometry_gain_pct_median"])
        d0_value = float(common_index[("D0", regime, orientation)]["strong_minus_paired_null_geometry_gain_pct_median"])
        a0_value = float(common_index[("A0_REF", regime, orientation)]["strong_minus_paired_null_geometry_gain_pct_median"])
        denom = a0_value - d0_value
        attribution_rows.append({
            "state": state, "matching_latent_reference": ref, "observation_regime": regime, "orientation": orientation,
            "state_separation_pp": value, "matching_reference_separation_pp": ref_value,
            "distortion_vs_matching_reference_pp": value - ref_value,
            "D0_separation_pp": d0_value, "full_A0_reference_separation_pp": a0_value,
            "movement_from_D0_toward_positive_pp": value - d0_value,
            "fraction_full_D0_to_A0_gap_removed": (value - d0_value) / denom if abs(denom) > 1e-12 else float("nan"),
            "interpretation": "QUANTITATIVE_SOURCE_ATTRIBUTION_NO_SCIENTIFIC_CATEGORY",
        })
    write_csv(OUT / "attribution_v01.csv", attribution_rows)
    attr_df = pd.DataFrame(attribution_rows)
    attr_summary = []
    for state, group in attr_df.groupby("state", sort=True):
        attr_summary.append({
            "state": state, "matching_latent_reference": reference_for[state], "n_regime_orientation_summaries": len(group),
            "state_separation_pp_median": pd.to_numeric(group["state_separation_pp"]).median(),
            "matching_reference_separation_pp_median": pd.to_numeric(group["matching_reference_separation_pp"]).median(),
            "distortion_vs_matching_reference_pp_median": pd.to_numeric(group["distortion_vs_matching_reference_pp"]).median(),
            "movement_from_D0_toward_positive_pp_median": pd.to_numeric(group["movement_from_D0_toward_positive_pp"]).median(),
            "fraction_full_D0_to_A0_gap_removed_median": pd.to_numeric(group["fraction_full_D0_to_A0_gap_removed"]).median(),
            "scientific_disposition": "NOT_ASSIGNED",
        })
    pooled_sep = {state: float(common_df.loc[common_df["state"] == state, "strong_minus_paired_null_geometry_gain_pct_median"].median()) for state in common_df["state"].unique()}
    pooled_gap = pooled_sep["A0_REF"] - pooled_sep["D0"]
    for row in attr_summary:
        row["fraction_full_D0_to_A0_gap_removed_from_pooled_medians"] = (row["state_separation_pp_median"] - pooled_sep["D0"]) / pooled_gap if abs(pooled_gap) > 1e-12 else float("nan")
    write_csv(OUT / "attrib_summary_v01.csv", attr_summary)

    zero_df = pd.DataFrame(zero_species)
    relationships = []
    for (world, orientation), group in zero_df.groupby(["world", "orientation"], sort=True):
        for outcome in ["D0_hellinger", "D0_sliced_wasserstein_km", "D1_minus_D0_hellinger", "D1_minus_D0_sliced_wasserstein_km"]:
            add_relationship(relationships, group, "SPECIES_MAP", "D0_D1", "zero_opportunity_truth_mass_fraction", outcome, world, orientation, "72 synthetic species; fixed state/world/orientation")
    for outcome in ["D0_hellinger", "D0_sliced_wasserstein_km", "D1_minus_D0_hellinger", "D1_minus_D0_sliced_wasserstein_km"]:
        add_relationship(relationships, zero_df, "SPECIES_MAP_POOLED", "D0_D1", "zero_opportunity_truth_mass_fraction", outcome, notes="Pooled species/world/orientation profiles")

    detail_df = pd.DataFrame(test_detail)
    gain_col = "individual_latent_truth_geometry_gain_pct"
    detail_wide = detail_df.pivot_table(index=["synthetic_species_id", "world", "orientation", "replicate", "split_seed"], columns="layer", values=gain_col, aggfunc="first").reset_index()
    detail_wide = detail_wide.merge(zero_df[["synthetic_species_id", "world", "orientation", "zero_opportunity_truth_mass_fraction"]], on=["synthetic_species_id", "world", "orientation"], how="left", validate="many_to_one")
    detail_wide["D0_minus_A0_individual_gain_pp"] = detail_wide["D0"] - detail_wide["A0_REF"]
    detail_wide["D1_minus_D0_individual_gain_pp"] = detail_wide["D1"] - detail_wide["D0"]
    for (world, orientation), group in detail_wide.groupby(["world", "orientation"], sort=True):
        for outcome in ["D0_minus_A0_individual_gain_pp", "D1_minus_D0_individual_gain_pp"]:
            add_relationship(relationships, group, "HELDOUT_SPECIES_DOWNSTREAM", "D0_D1", "zero_opportunity_truth_mass_fraction", outcome, world, orientation, "Frozen test occurrences only; individual diagnostic gain is not the official aggregate score")
    for outcome in ["D0_minus_A0_individual_gain_pp", "D1_minus_D0_individual_gain_pp"]:
        add_relationship(relationships, detail_wide, "HELDOUT_SPECIES_DOWNSTREAM_POOLED", "D0_D1", "zero_opportunity_truth_mass_fraction", outcome, notes="Frozen test occurrences pooled; no new split")

    pair = detail_wide.pivot_table(index=["synthetic_species_id", "orientation", "replicate", "split_seed"], columns="world", values=["A0_REF", "D0", "D1", "zero_opportunity_truth_mass_fraction"], aggfunc="first")
    pair.columns = [f"{a}_{b}" for a, b in pair.columns]
    pair = pair.reset_index()
    pair["mean_zero_truth_mass_fraction"] = 0.5 * (pair["zero_opportunity_truth_mass_fraction_STRONG"] + pair["zero_opportunity_truth_mass_fraction_PAIRED_NULL"])
    pair["strong_minus_null_zero_truth_mass_fraction"] = pair["zero_opportunity_truth_mass_fraction_STRONG"] - pair["zero_opportunity_truth_mass_fraction_PAIRED_NULL"]
    pair["A0_individual_separation_pp"] = pair["A0_REF_STRONG"] - pair["A0_REF_PAIRED_NULL"]
    pair["D0_individual_separation_pp"] = pair["D0_STRONG"] - pair["D0_PAIRED_NULL"]
    pair["D1_individual_separation_pp"] = pair["D1_STRONG"] - pair["D1_PAIRED_NULL"]
    pair["D0_minus_A0_individual_separation_distortion_pp"] = pair["D0_individual_separation_pp"] - pair["A0_individual_separation_pp"]
    pair["D1_minus_D0_individual_separation_change_pp"] = pair["D1_individual_separation_pp"] - pair["D0_individual_separation_pp"]
    for orientation, group in pair.groupby("orientation", sort=True):
        for predictor in ["mean_zero_truth_mass_fraction", "strong_minus_null_zero_truth_mass_fraction"]:
            for outcome in ["D0_minus_A0_individual_separation_distortion_pp", "D1_minus_D0_individual_separation_change_pp"]:
                add_relationship(relationships, group, "HELDOUT_SPECIES_PAIR", "D0_D1", predictor, outcome, "STRONG_MINUS_PAIRED_NULL", orientation, "Frozen paired test occurrences")
    write_csv(OUT / "relationships_v01.csv", relationships)

    # Official split-level attribution with the exact aggregate gain definition.
    base_df = pd.DataFrame(downstream_base)
    base_df["latent_truth_geometry_gain_pct"] = pd.to_numeric(base_df["latent_truth_geometry_gain_pct"])
    gain_wide = base_df.pivot_table(index=["world", "orientation", "replicate", "split_seed"], columns="layer", values="latent_truth_geometry_gain_pct", aggfunc="first").reset_index()
    test_ids = detail_df.loc[detail_df["layer"] == "D0", ["synthetic_species_id", "world", "orientation", "replicate", "split_seed"]]
    test_ids = test_ids.merge(zero_df[["synthetic_species_id", "world", "orientation", "zero_opportunity_truth_mass_fraction"]], on=["synthetic_species_id", "world", "orientation"], how="left", validate="many_to_one")
    zsplit = test_ids.groupby(["world", "orientation", "replicate", "split_seed"], as_index=False)["zero_opportunity_truth_mass_fraction"].mean().rename(columns={"zero_opportunity_truth_mass_fraction": "test_mean_zero_truth_mass_fraction"})
    gain_wide = gain_wide.merge(zsplit, on=["world", "orientation", "replicate", "split_seed"], validate="one_to_one")
    split_pair = gain_wide.pivot_table(index=["orientation", "replicate", "split_seed"], columns="world", values=["A0_REF", "D0", "D1", "D2", "D3", "D2_A0_REF", "D3_A0_REF", "test_mean_zero_truth_mass_fraction"], aggfunc="first")
    split_pair.columns = [f"{a}_{b}" for a, b in split_pair.columns]
    split_pair = split_pair.reset_index()
    split_rows = []
    for row in split_pair.to_dict("records"):
        out = {"orientation": row["orientation"], "replicate": row["replicate"], "split_seed": row["split_seed"]}
        for state in ["A0_REF", "D0", "D1", "D2", "D3", "D2_A0_REF", "D3_A0_REF"]:
            out[f"{state}_strong_minus_paired_null_separation_pp"] = row[f"{state}_STRONG"] - row[f"{state}_PAIRED_NULL"]
        out["test_mean_zero_truth_mass_fraction_STRONG"] = row["test_mean_zero_truth_mass_fraction_STRONG"]
        out["test_mean_zero_truth_mass_fraction_PAIRED_NULL"] = row["test_mean_zero_truth_mass_fraction_PAIRED_NULL"]
        out["test_mean_zero_truth_mass_fraction_both_worlds"] = 0.5 * (row["test_mean_zero_truth_mass_fraction_STRONG"] + row["test_mean_zero_truth_mass_fraction_PAIRED_NULL"])
        out["D0_minus_A0_separation_distortion_pp"] = out["D0_strong_minus_paired_null_separation_pp"] - out["A0_REF_strong_minus_paired_null_separation_pp"]
        out["D1_minus_D0_separation_change_pp"] = out["D1_strong_minus_paired_null_separation_pp"] - out["D0_strong_minus_paired_null_separation_pp"]
        split_rows.append(out)
    write_csv(OUT / "split_attrib_v01.csv", split_rows)
    split_df = pd.DataFrame(split_rows)
    for outcome in ["D0_minus_A0_separation_distortion_pp", "D1_minus_D0_separation_change_pp"]:
        add_relationship(relationships, split_df, "OFFICIAL_SPLIT_AGGREGATE", "D0_D1", "test_mean_zero_truth_mass_fraction_both_worlds", outcome, "STRONG_MINUS_PAIRED_NULL", "ALL", "Exact official aggregate gain; 10 orientation-split rows")
    write_csv(OUT / "relationships_v01.csv", relationships)

    # Compact distribution audit.
    distribution_rows = []
    for (state, world, orientation), group in domain_frame.groupby(["state", "world", "orientation"], sort=True):
        for metric in ["support_fraction_lost", "latent_truth_mass_fraction_lost", "A2_raw_mass_fraction_lost"]:
            values = pd.to_numeric(group[metric]).to_numpy(float)
            distribution_rows.append({
                "state": state, "world": world, "orientation": orientation, "metric": metric, "n": len(values),
                "min": float(np.min(values)), "q05": quantile(values, 0.05), "q25": quantile(values, 0.25),
                "median": quantile(values, 0.50), "q75": quantile(values, 0.75), "q95": quantile(values, 0.95), "max": float(np.max(values)),
            })
    zero_dist = []
    for (world, orientation), group in zero_df.groupby(["world", "orientation"], sort=True):
        values = pd.to_numeric(group["zero_opportunity_truth_mass_fraction"]).to_numpy(float)
        zero_dist.append({
            "world": world, "orientation": orientation, "n_species": len(values), "minimum": float(np.min(values)),
            "q05": quantile(values, 0.05), "q25": quantile(values, 0.25), "median": quantile(values, 0.50),
            "q75": quantile(values, 0.75), "q95": quantile(values, 0.95), "maximum": float(np.max(values)),
            "species_with_any_zero_truth_mass": int(np.sum(values > 0)),
        })
    write_csv(OUT / "domain_dist_v01.csv", distribution_rows)
    write_csv(OUT / "zero_dist_v01.csv", zero_dist)

    attr_summary_df = pd.DataFrame(attr_summary).set_index("state")
    state_sep = {state: float(attr_summary_df.loc[state, "state_separation_pp_median"]) for state in attr_summary_df.index}
    d1_fraction = float(attr_summary_df.loc["D1", "fraction_full_D0_to_A0_gap_removed_from_pooled_medians"])
    d0_ab = float(common_df[(common_df.state == "D0") & (common_df.orientation == "AB")]["strong_minus_paired_null_geometry_gain_pct_median"].median())
    d0_ba = float(common_df[(common_df.state == "D0") & (common_df.orientation == "BA")]["strong_minus_paired_null_geometry_gain_pct_median"].median())
    d1_ab = float(common_df[(common_df.state == "D1") & (common_df.orientation == "AB")]["strong_minus_paired_null_geometry_gain_pct_median"].median())
    d1_ba = float(common_df[(common_df.state == "D1") & (common_df.orientation == "BA")]["strong_minus_paired_null_geometry_gain_pct_median"].median())
    d3_ab = float(common_df[(common_df.state == "D3") & (common_df.orientation == "AB")]["strong_minus_paired_null_geometry_gain_pct_median"].median())
    d3_ba = float(common_df[(common_df.state == "D3") & (common_df.orientation == "BA")]["strong_minus_paired_null_geometry_gain_pct_median"].median())
    d0_orientation_gap = abs(d0_ba - d0_ab)
    d3_orientation_gap = abs(d3_ba - d3_ab)
    orientation_gap_reduction = d0_orientation_gap - d3_orientation_gap
    d3_profiles = domain_frame[domain_frame.state == "D3"]
    d3_support_median = float(d3_profiles.support_fraction_retained.median())
    d3_mass_median = float(d3_profiles.latent_truth_mass_fraction_retained.median())
    d3_mass_q05 = float(d3_profiles.latent_truth_mass_fraction_retained.quantile(0.05))
    common_fraction = float(domain_common.mean())
    rel_frame = pd.DataFrame(relationships)
    def relationship_value(level, outcome):
        found = rel_frame[(rel_frame.analysis_level == level) & (rel_frame.outcome == outcome) & (rel_frame.statistic == "pearson_r")]
        return float(found.iloc[0].value)
    map_h_r = relationship_value("SPECIES_MAP_POOLED", "D0_hellinger")
    map_fill_r = relationship_value("SPECIES_MAP_POOLED", "D1_minus_D0_hellinger")
    heldout_distortion_r = relationship_value("HELDOUT_SPECIES_DOWNSTREAM_POOLED", "D0_minus_A0_individual_gain_pp")
    heldout_fill_r = relationship_value("HELDOUT_SPECIES_DOWNSTREAM_POOLED", "D1_minus_D0_individual_gain_pp")
    result_note = f"""# D10D source-attribution result note v01

Terminal status: `{TERMINAL}`

This is a synthetic, oracle-support source-attribution diagnostic. It assigns no scientific PASS/HOLD/FAIL and does not select a real-data estimator or domain. D1 is oracle-assisted and cannot be used on real data.

## Q1 — Oracle filling of zero-opportunity cells

The pooled median STRONG-minus-PAIRED_NULL separation moved from {state_sep['D0']:.3f} pp in D0 to {state_sep['D1']:.3f} pp in D1, a change of {state_sep['D1'] - state_sep['D0']:.3f} pp toward the full-domain A0 reference ({state_sep['A0_REF']:.3f} pp). The descriptive fraction of the full D0-to-A0 separation gap removed was {d1_fraction:.6f}. The orientation effects differed: AB changed from {d0_ab:.3f} to {d1_ab:.3f} pp, while BA changed from {d0_ba:.3f} to {d1_ba:.3f} pp. Full split results are retained.

## Q2 — Target-fold measurable domain

D2 separation remained negative at {state_sep['D2']:.3f} pp. Its matching restricted-latent reference was {state_sep['D2_A0_REF']:.3f} pp, leaving a median distortion of {state_sep['D2'] - state_sep['D2_A0_REF']:.3f} pp. This reports direction and residual distortion without assigning a scientific disposition.

## Q3 — Common A-intersection-B domain

D3 separation remained negative at {state_sep['D3']:.3f} pp. Its matching common-domain latent reference was {state_sep['D3_A0_REF']:.3f} pp, leaving a median distortion of {state_sep['D3'] - state_sep['D3_A0_REF']:.3f} pp. No final common-domain estimand is selected.

## Q4 — AB/BA agreement under D3

D3 AB and BA median separations were {d3_ab:.3f} and {d3_ba:.3f} pp; their absolute gap was {d3_orientation_gap:.3f} pp. D0's absolute AB/BA gap was {d0_orientation_gap:.3f} pp, so D3 reduced the descriptive gap by {orientation_gap_reduction:.3f} pp. No consistency threshold was defined.

## Q5 — D3 domain cost

The common domain retained {int(domain_common.sum()):,} of {ncell:,} F0 cells ({common_fraction:.6%}). Across all D3 species/world/orientation profiles, median support-cell retention was {d3_support_median:.6%}; median latent truth-mass retention was {d3_mass_median:.6%}, and its 5th percentile was {d3_mass_q05:.6%}. Full distributions and a non-decision cutoff frontier are supplied, so mainline can define any later severe-truncation criterion.

## Q6 — Sufficiency of zero-opportunity cells

D1's gap-removal fraction is {d1_fraction:.6f}; the remaining D1-to-A0 separation difference is {state_sep['D1'] - state_sep['A0_REF']:.3f} pp. Zero-opportunity truth mass was strongly related to D0 map Hellinger error (pooled Pearson r={map_h_r:.3f}) and to the D1-minus-D0 Hellinger change (r={map_fill_r:.3f}). In contrast, its pooled relationship with held-out individual downstream gain distortion was r={heldout_distortion_r:.3f}, and with the D1 individual downstream change was r={heldout_fill_r:.3f}. This branch reports those quantities without assigning the mainline categories dominant/material/bounded/unsupported.

## Q7 — Residual positive-opportunity distortion

D2 and D3 exclude zero-opportunity mismatch by aligning truth, A2, and oracle geometry on the same measurable domain. Their differences from their matching latent references are {state_sep['D2'] - state_sep['D2_A0_REF']:.3f} and {state_sep['D3'] - state_sep['D3_A0_REF']:.3f} pp, respectively. These are the residual downstream distortions after domain alignment.

## Q8 — Mainline options

The package supplies full-domain, oracle-fill, target-fold-domain, common-domain, and matching latent-reference evidence. It does not choose among retaining the full domain, redefining the estimand, developing another abundance model, or continuing HOLD.

STOP: no abundance repair, support recovery, real species, final cohort, real World 0, or real Q1 was run.
"""
    write_text(OUT / "result_note_v01.md", result_note)

    checks = [
        {"check_id": "INPUT_IDENTITIES", "status": "PASS", "observed": len(identity), "expected": len(identity), "notes": "Outer hashes and D10CR internal manifest"},
        {"check_id": "D10CR_INTERNAL_MEMBERS", "status": "PASS", "observed": internal_n, "expected": internal_n, "notes": "All member hashes and sizes match"},
        {"check_id": "F0_ROWS", "status": "PASS", "observed": len(f0), "expected": 338619, "notes": "Frozen D10A layout"},
        {"check_id": "LEGAL_OPPORTUNITIES", "status": "PASS", "observed": len(legal), "expected": 134846, "notes": "Frozen legal opportunity rule"},
        {"check_id": "CELLS_50KM", "status": "PASS", "observed": ncell, "expected": 3011, "notes": "Fixed grain"},
        {"check_id": "SYNTHETIC_WORLD_HASHES", "status": "PASS", "observed": hash_match, "expected": 144, "notes": "Loaded from D10CR cell truth; generator not rerun"},
        {"check_id": "A_ZERO_OPPORTUNITY_CELLS", "status": "PASS" if int((~domain_a).sum()) == 156 else "FAIL", "observed": int((~domain_a).sum()), "expected": 156, "notes": "BA target fold"},
        {"check_id": "B_ZERO_OPPORTUNITY_CELLS", "status": "PASS" if int((~domain_b).sum()) == 98 else "FAIL", "observed": int((~domain_b).sum()), "expected": 98, "notes": "AB target fold"},
        {"check_id": "D0_REPRODUCTION", "status": "PASS" if d0_ok else "FAIL", "observed": d0_diff, "expected": "<=1e-10", "notes": "All common D10C A2 downstream numeric fields"},
        {"check_id": "A0_REPRODUCTION", "status": "PASS" if a0_ok else "FAIL", "observed": a0_diff, "expected": "<=1e-10", "notes": "All common D10C A0 downstream numeric fields"},
        {"check_id": "D1_POSITIVE_CELLS_UNCHANGED", "status": "PASS" if all(r["positive_opportunity_A2_unchanged"] in ("YES", "NA") for r in d1_cells) else "FAIL", "observed": sum(r["positive_opportunity_A2_unchanged"] == "NO" for r in d1_cells), "expected": 0, "notes": "Before normalization"},
        {"check_id": "NORMALIZATION", "status": "PASS", "observed": "ALL_STATE_MAPS", "expected": "sum=1 within 1e-12", "notes": "Enforced by normalize"},
        {"check_id": "NO_EMPTY_RESTRICTED_SUPPORT", "status": "PASS", "observed": min(r["retained_support_cells"] for r in domain_species), "expected": ">0", "notes": "D2 and D3"},
        {"check_id": "DOWNSTREAM_ROWS", "status": "PASS" if len(downstream) == 420 else "FAIL", "observed": len(downstream), "expected": 420, "notes": "7 states x 2 worlds x 2 orientations x 5 splits x 3 regimes"},
        {"check_id": "REAL_SPECIES_READ", "status": "PASS", "observed": 0, "expected": 0, "notes": "Synthetic IDs only; TREE.SPCD not read"},
        {"check_id": "SUPPORT_RECOVERY_RUN", "status": "PASS", "observed": 0, "expected": 0, "notes": "Oracle support only"},
        {"check_id": "NETWORK_USED", "status": "PASS", "observed": 0, "expected": 0, "notes": "Frozen local packages only"},
        {"check_id": "SCIENTIFIC_DISPOSITION_ASSIGNED", "status": "PASS", "observed": 0, "expected": 0, "notes": "Quantitative attribution only"},
    ]
    write_csv(QC / "checks_v01.csv", checks)
    if any(row["status"] != "PASS" for row in checks):
        raise RuntimeError("IMPLEMENTATION_BLOCKED: QC failure")

    build_summary = {
        "task_id": TASK, "terminal_status": TERMINAL, "f0_rows": len(f0), "legal_opportunities": len(legal),
        "cells_50km": ncell, "A_opportunity_cells": int(domain_a.sum()), "B_opportunity_cells": int(domain_b.sum()),
        "common_opportunity_cells": int(domain_common.sum()), "synthetic_species": 72,
        "D0_max_abs_reproduction_diff": d0_diff, "A0_max_abs_reproduction_diff": a0_diff,
        "downstream_rows": len(downstream), "test_detail_rows": len(test_detail),
        "state_separation_pp_median": state_sep, "D1_fraction_full_gap_removed_from_pooled_medians": d1_fraction,
        "network_used": False, "real_species_read": False, "support_recovery_run": False,
        "abundance_model_repair_run": False, "real_world0_run": False, "real_q1_run": False,
        "scientific_pass_hold_fail_assigned": False,
    }
    write_json(QC / "build_summary_v01.json", build_summary)
    write_json(QC / "environment_v01.json", {
        "python": sys.version, "platform": platform.platform(), "numpy": np.__version__, "pandas": pd.__version__,
        "working_root": str(ROOT), "network_used": False,
    })
    write_csv(MAN / "registry_delta_v01.csv", [{
        "DELTA_TYPE": "TASK", "ACTION": "PROPOSE_ADD", "TASK_ID": TASK,
        "ASSET_NAME": "D10D zero-opportunity measurable-domain source attribution",
        "CANONICAL_PATH": str(ARCH / "D10D_v01.zip"), "SHA256": "SEE_EXTERNAL_SIDECAR",
        "SIZE_BYTES": "SEE_EXTERNAL_SIDECAR", "STATUS": TERMINAL,
        "SCIENTIFIC_OUTPUT_CHANGED": "SYNTHETIC_DIAGNOSTIC_ONLY", "PUBLICATION_CANDIDATE": "METHODS_SUPPORT_CANDIDATE",
        "METHODS_ROLE": "OBSERVATION_DOMAIN_SOURCE_ATTRIBUTION", "DATA_ROLE": "SYNTHETIC_ONLY",
        "CODE_ROLE": "REPRODUCIBLE_BUILD", "QC_ROLE": "IDENTITY_DOMAIN_DOWNSTREAM_ATTRIBUTION",
        "NOTES": "No scientific disposition, estimator selection, support recovery, or real Q1.",
    }])
    shutil.copyfile(Path(__file__), SRC / "build.py")
    print(json.dumps(build_summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
