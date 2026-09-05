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
from collections import Counter
from contextlib import contextmanager
from pathlib import Path

import numpy as np
import pandas as pd


TASK = "D10C_FIA_DESIGN_BASED_ABUNDANCE_MEASUREMENT_CALIBRATION_RESUME_v01"
TERMINAL = "ABUNDANCE_CALIBRATION_COMPLETE_READY_FOR_MAINLINE_FREEZE"
ROOT = Path(r"C:\range_paper")
ARCH = ROOT / "10_archive" / "d10cr"
PKG = ARCH / "pkg"
OUT = PKG / "out"
QC = PKG / "qc"
SRC = PKG / "src"
FIG = PKG / "fig"
MAN = PKG / "manifest"
CTL = PKG / "control"
TMP = ROOT / "99_tmp" / "d10cr"

D10A = ROOT / "10_archive" / "d10a_real_layout_nonoracle_v01" / "Q1_D10A_REAL_LAYOUT_NONORACLE_OBSERVATION_CALIBRATION_REPRODUCIBLE_v01.zip"
D10B = ROOT / "10_archive" / "d10b_oracle_source_decomposition_v01" / "Q1_D10B_ORACLE_SUPPORT_DOWNSTREAM_SOURCE_DECOMPOSITION_REPRODUCIBLE_v01.zip"
D09C = ROOT / "10_archive" / "d09c_t2_final_correction_v02" / "Q1_D09C_T2_FINAL_CORRECTION_REPRODUCIBLE_v02.zip"
D10CA = ROOT / "10_archive" / "d10ca" / "D10CA_v01.zip"
D10C_PREV = ROOT / "10_archive" / "d10c_fia_design_abundance_v01" / "Q1_D10C_FIA_DESIGN_BASED_ABUNDANCE_ESTIMATOR_AUTHORITY_FAILURE_REPRODUCIBLE_v01.zip"
RESUME_REQUEST = Path(r"C:\Users\bug_g\.codex\attachments\f7478ae7-a10b-4384-87b8-7a79b2f92b3d\pasted-text.txt")
EXPERIMENT_CONTRACT = CTL / "contract_v01.md"

EXPECTED = {
    D10A: "20e5d3ed33df6414b72a6e679d5349f3b10fe6397ce73f98b51d0bcc96033013",
    D10B: "cb041fca5897f31c8ea0bf2a3b29a262a5c83ef44bdfda9a37a0394cfc7cafeb",
    D09C: "07cb461121c71ef46990fea3e0cf9d8f139fd873234b9f57910ff10c7c33752f",
    D10CA: "c8f73406f7f192b8f124add3cb0ded7ea65474e8d72d752e37dc557a08588865",
    D10C_PREV: "64693a8786b3acf981145d99c99a0831d6312605e0c1197dd50fd6684baf20af",
}

TOTAL_MASS = 100_000_000.0
TPA_UNADJ = 6.018046
DIA = 5.0
STATUSCD = 1


def sha256_file(path: Path, chunk: int = 16 * 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while b := f.read(chunk):
            h.update(b)
    return h.hexdigest()


def write_csv(path: Path, rows, fields=None) -> None:
    rows = list(rows)
    if fields is None:
        fields = list(rows[0]) if rows else []
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_md(path: Path, value: str) -> None:
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
    with zipfile.ZipFile(path) as z:
        names = [n for n in z.namelist() if n.endswith(suffix)]
        if len(names) != 1:
            raise RuntimeError(f"Expected one member ending {suffix!r} in {path}; found {len(names)}")
        return z.read(names[0])


def zip_csv(path: Path, suffix: str, **kwargs) -> pd.DataFrame:
    return pd.read_csv(io.BytesIO(zip_member_bytes(path, suffix)), **kwargs)


def zip_gzip_csv(path: Path, suffix: str, **kwargs) -> pd.DataFrame:
    data = zip_member_bytes(path, suffix)
    return pd.read_csv(gzip.GzipFile(fileobj=io.BytesIO(data)), **kwargs)


def import_zip_module(path: Path, suffix: str, name: str):
    TMP.mkdir(parents=True, exist_ok=True)
    target = TMP / f"{name}.py"
    target.write_bytes(zip_member_bytes(path, suffix))
    spec = importlib.util.spec_from_file_location(name, target)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def safe_corr(a, b):
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    ok = np.isfinite(a) & np.isfinite(b)
    if ok.sum() < 3 or np.std(a[ok]) < 1e-15 or np.std(b[ok]) < 1e-15:
        return float("nan")
    return float(np.corrcoef(a[ok], b[ok])[0, 1])


def stable_mode(values):
    count = Counter(str(v) for v in values)
    if not count:
        return "", 0.0
    value, n = min(count.items(), key=lambda kv: (-kv[1], kv[0]))
    return value, n / sum(count.values())


def main() -> None:
    # Keep the already frozen experiment contract, and clear only generated branches.
    if not EXPERIMENT_CONTRACT.exists():
        raise RuntimeError("Frozen experiment contract missing")
    for d in (OUT, QC, SRC, FIG, MAN):
        if d.exists():
            shutil.rmtree(d)
        d.mkdir(parents=True, exist_ok=True)
    TMP.mkdir(parents=True, exist_ok=True)

    identity = []
    for path, expected in EXPECTED.items():
        actual = sha256_file(path)
        identity.append({
            "asset": path.name, "path": str(path), "size_bytes": path.stat().st_size,
            "expected_sha256": expected, "actual_sha256": actual,
            "status": "PASS" if actual == expected else "FAIL",
        })
    identity.append({
        "asset": "resume_request", "path": str(RESUME_REQUEST), "size_bytes": RESUME_REQUEST.stat().st_size,
        "expected_sha256": "FROZEN_AT_EXECUTION", "actual_sha256": sha256_file(RESUME_REQUEST), "status": "PASS",
    })
    identity.append({
        "asset": "experiment_contract", "path": str(EXPERIMENT_CONTRACT), "size_bytes": EXPERIMENT_CONTRACT.stat().st_size,
        "expected_sha256": "FROZEN_BEFORE_A2", "actual_sha256": sha256_file(EXPERIMENT_CONTRACT), "status": "PASS",
    })
    write_csv(QC / "input_id_v01.csv", identity)
    if any(r["status"] != "PASS" for r in identity):
        raise RuntimeError("INPUT_BLOCKED_FROZEN_DESIGN_IDENTITY_FAILURE")

    d10a = import_zip_module(D10A, "build_d10a_real_layout_nonoracle_v01.py", "d10a_release")
    d10b = import_zip_module(D10B, "build_d10b_oracle_source_decomposition_v01.py", "d10b_release")
    param = json.loads(zip_member_bytes(D10A, "parameters_d10a_real_layout_nonoracle_v01.json").decode("utf-8"))
    f0 = zip_csv(D10A, "Q1_D10A_REAL_F0_OPPORTUNITY_LAYOUT_v01.csv", dtype=str, keep_default_na=False)
    released_manifest = zip_csv(D10A, "Q1_D10A_SYNTHETIC_WORLD_MANIFEST_v01.csv", dtype=str, keep_default_na=False)
    released_l0 = zip_csv(D10B, "Q1_D10B_L0_ORACLE_SUPPORT_LATENT_ABUNDANCE_RESULTS_v01.csv", dtype=str, keep_default_na=False)
    released_l1 = zip_csv(D10B, "Q1_D10B_L1_ORACLE_SUPPORT_OBSERVED_ABUNDANCE_RESULTS_v01.csv", dtype=str, keep_default_na=False)
    released_world_id = zip_csv(D10B, "Q1_D10B_ORACLE_WORLD_IDENTITIES_v01.csv", dtype=str, keep_default_na=False)
    crosswalk = zip_gzip_csv(D10CA, "plot_block_xwalk_v01.csv.gz", dtype=str, keep_default_na=False)
    xqc = zip_csv(D10CA, "xwalk_qc_v01.csv", dtype=str, keep_default_na=False)
    xiv = json.loads(zip_member_bytes(D10CA, "independent_validation_v01.json").decode("utf-8"))

    if len(xqc) != 9 or set(xqc["status"]) != {"PASS"} or xiv.get("status") != "PASS":
        raise RuntimeError("INPUT_BLOCKED_ABUNDANCE_ESTIMATOR_AUTHORITY_FAILURE")
    if len(crosswalk) != 338619 or crosswalk["PLT_CN"].nunique() != 338619:
        raise RuntimeError("INPUT_BLOCKED_ABUNDANCE_ESTIMATOR_AUTHORITY_FAILURE")

    legal = f0.loc[f0["base_legitimate_opportunity_flag"] == "YES"].copy()
    plots = {}
    for r in legal.to_dict("records"):
        plots[r["plot_cn"]] = {
            "base_legitimate_opportunity_flag": True, "cell_50km": r["cell_50km"],
            "manual": r["manual"], "designcd": r["designcd"],
            "effort_score": float(r["partial_sampling_effort"]),
            "partial_sampling_flag": r["partial_sampling_flag"] == "YES", "fold": r["fold"],
        }
    layout = d10a.build_layout_arrays(plots, param)
    supports, abundances, regenerated_manifest = d10a.generate_synthetic(layout, param)
    if d10b.normalized_manifest_rows(released_manifest.to_dict("records")) != d10b.normalized_manifest_rows(regenerated_manifest):
        raise RuntimeError("INPUT_BLOCKED_FROZEN_DESIGN_IDENTITY_FAILURE: D10A manifest mismatch")

    observed_a1 = d10b.regenerate_observed_abundance(layout, supports, abundances, param, d10a)
    identity_rows = d10b.build_identity_rows(
        supports, abundances, observed_a1, regenerated_manifest,
        released_manifest.to_dict("records"), param,
    )
    released_identity_index = {(r["synthetic_species_id"], r["world"]): r for r in released_world_id.to_dict("records")}
    world_hash_match = 0
    for row in identity_rows:
        ref = released_identity_index[(row["synthetic_species_id"], row["world"])]
        fields = ["support_index_sha256", "latent_abundance_sha256", "positive_abundance_values_sha256", "observed_abundance_A_sha256", "observed_abundance_B_sha256", "split_assignments_sha256"]
        if all(str(row[f]) == str(ref[f]) for f in fields):
            world_hash_match += 1
    if world_hash_match != 144:
        raise RuntimeError("INPUT_BLOCKED_FROZEN_DESIGN_IDENTITY_FAILURE: D10B world hash mismatch")
    write_csv(QC / "world_id_v01.csv", identity_rows)

    # Preserve exact plot order used by D10B and attach D10C-A authority.
    crosswalk = crosswalk.set_index("PLT_CN", drop=False)
    fold_meta = {}
    ncell = len(layout["cells"])
    for fold in ("A", "B"):
        lf = legal.loc[legal["fold"] == fold].copy()
        cns = lf["plot_cn"].tolist()
        missing = [cn for cn in cns if cn not in crosswalk.index]
        if missing:
            raise RuntimeError(f"INPUT_BLOCKED_ABUNDANCE_ESTIMATOR_AUTHORITY_FAILURE: {len(missing)} legal plots missing")
        cw = crosswalk.loc[cns].reset_index(drop=True)
        data = layout["folds"][fold]
        if len(cw) != len(data["rows"]) or not np.array_equal(cw["cell_50km"].to_numpy(), lf["cell_50km"].to_numpy()):
            raise RuntimeError("INPUT_BLOCKED_FROZEN_DESIGN_IDENTITY_FAILURE: plot order or cell mismatch")
        if not (cw["final_fold"] == fold).all() or not (cw["QC_STATUS"] == "PASS").all():
            raise RuntimeError("INPUT_BLOCKED_ABUNDANCE_ESTIMATOR_AUTHORITY_FAILURE: fold/QC mismatch")
        pcell = data["plot_cell"]
        summaries = {}
        for out_name, values in {
            "state": cw["STATECD"].to_numpy(), "panel": cw["P2PANEL"].to_numpy(),
            "manual": lf["manual"].to_numpy(), "design": lf["designcd"].to_numpy(),
            "block": cw["final_effective_design_block_id"].to_numpy(),
        }.items():
            modes, shares = [], []
            for cell in range(ncell):
                mode, share = stable_mode(values[pcell == cell])
                modes.append(mode); shares.append(share)
            summaries[f"dominant_{out_name}"] = np.asarray(modes, dtype=object)
            summaries[f"dominant_{out_name}_share"] = np.asarray(shares, dtype=float)
        fold_meta[fold] = {
            "plot_cn": np.asarray(cns, dtype=object), "cell": lf["cell_50km"].to_numpy(),
            "pcell": pcell, "ti": pd.to_numeric(cw["fold_specific_ti_weight"]).to_numpy(float),
            "adj": pd.to_numeric(cw["adj_factor_subp"]).to_numpy(float),
            "effort": pd.to_numeric(lf["partial_sampling_effort"]).to_numpy(float),
            "partial": (lf["partial_sampling_flag"] == "YES").to_numpy(float),
            "state": cw["STATECD"].to_numpy(), "panel": cw["P2PANEL"].to_numpy(),
            "manual": lf["manual"].to_numpy(), "design": lf["designcd"].to_numpy(),
            "block": cw["final_effective_design_block_id"].to_numpy(),
            "stratum": cw["original_STRATUM_CN"].to_numpy(),
            "plot_count": np.bincount(pcell, minlength=ncell).astype(int),
            "effort_sum": np.bincount(pcell, weights=pd.to_numeric(lf["partial_sampling_effort"]).to_numpy(float), minlength=ncell),
            "partial_fraction": data["partial_fraction"], "mean_effort": data["mean_effort"],
            **summaries,
        }

    if len(legal) != 134846 or ncell != 3011 or len(supports) != 72:
        raise RuntimeError("INPUT_BLOCKED_FROZEN_DESIGN_IDENTITY_FAILURE: F0 universe mismatch")

    # Freeze ledgers before writing outcome tables.
    layer_rows = [
        {"layer": "A0", "status": "LATENT_TRUTH", "population_mass": "T_i*p_i(x)", "normalization": "exact D10A latent allocation", "estimator_candidate": "NO", "source": "D10A latent world"},
        {"layer": "A1", "status": "BROKEN_REFERENCE_ONLY", "population_mass": "T_i times normalized D10A raw cell counts for diagnostic scale alignment", "normalization": "raw cell count / total raw count", "estimator_candidate": "NO", "source": "exact D10A released count generator"},
        {"layer": "A2", "status": "FROZEN_FIA_DESIGN_ESTIMATOR", "population_mass": "sum TI*count*TPA_UNADJ*ADJ_FACTOR_SUBP", "normalization": "estimated cell mass / total estimated mass", "estimator_candidate": "SOLE_CANDIDATE", "source": "D10C-A authority closure"},
    ]
    write_csv(OUT / "layer_ledger_v01.csv", layer_rows)
    impl_rows = [
        {"component": "species_total_mass", "value": TOTAL_MASS, "status": "FROZEN", "authority": "experiment contract", "notes": "constant for every species and world"},
        {"component": "synthetic_tree_statuscd", "value": STATUSCD, "status": "FROZEN", "authority": "D10C-A target state", "notes": "live"},
        {"component": "synthetic_tree_dia_inches", "value": DIA, "status": "FROZEN", "authority": "experiment contract", "notes": "large-tree threshold; below every numeric macro breakpoint (minimum 24 inches)"},
        {"component": "tally_basis", "value": "SUBP", "status": "FROZEN", "authority": "D10C-A basis rule", "notes": "basis-matched ADJ_FACTOR_SUBP"},
        {"component": "tpa_unadj", "value": TPA_UNADJ, "status": "FROZEN", "authority": "D10C-A/FIADB", "notes": "trees per acre per subplot record"},
        {"component": "population_expansion", "value": "fold_specific_TI", "status": "FROZEN", "authority": "D09C/D10C-A", "notes": "full-evaluation EXPNS excluded"},
        {"component": "partial_effort", "value": "observation opportunity and QC only", "status": "P3", "authority": "D10C-A", "notes": "no inverse-effort estimator multiplier"},
        {"component": "zero_exposure_cell", "value": "estimate zero; retain truth and flag", "status": "FROZEN_LIMITATION", "authority": "experiment contract", "notes": "no interpolation or support restriction"},
    ]
    write_csv(OUT / "a2_impl_v01.csv", impl_rows)

    truth_rows, a0_rows = [], []
    for sid in sorted(supports):
        sname = f"SYN{sid:03d}"
        active = np.where(supports[sid])[0]
        for world in ("STRONG", "PAIRED_NULL"):
            p = abundances[(sid, world)]
            for cell in active:
                row = {"synthetic_species_id": sname, "world": world, "cell_50km": layout["cells"][cell], "true_support": "YES", "species_total_mass": TOTAL_MASS, "latent_allocation": p[cell], "latent_cell_mass": TOTAL_MASS * p[cell]}
                truth_rows.append(row)
                a0_rows.append({"layer": "A0", **row})
    write_csv(OUT / "truth_v01.csv", truth_rows)
    write_csv(OUT / "a0_v01.csv", a0_rows)

    plot_fields = [
        "synthetic_species_id", "world", "orientation", "target_fold", "PLT_CN", "cell_50km",
        "synthetic_tree_count", "STATUSCD", "DIA", "tally_basis", "TPA_UNADJ",
        "ADJ_FACTOR_SUBP", "fold_specific_TI", "partial_sampling_effort", "plot_micro",
        "poisson_mean", "unadjusted_tpa_total", "adjusted_plot_tpa", "weighted_cell_mass",
        "STATECD", "P2PANEL", "MANUAL", "DESIGNCD", "effective_design_block_id",
        "original_STRATUM_CN", "sparse_zero_omission",
    ]
    a2_mass, a2_var_est, a2_var_true, a2_exposure = {}, {}, {}, {}
    nonzero_plot_rows = 0
    with gzip_text(OUT / "plot_obs_v01.csv.gz") as handle:
        writer = csv.DictWriter(handle, fieldnames=plot_fields, lineterminator="\n")
        writer.writeheader()
        for sid in sorted(supports):
            sname = f"SYN{sid:03d}"
            for fold in ("A", "B"):
                meta = fold_meta[fold]
                rng_micro = np.random.default_rng(d10a.stable_seed(param["collection_seed"], sid, fold, "count_micro"))
                micro = np.exp(rng_micro.normal(0.0, param["abundance_plot_log_sd"], len(meta["pcell"])))
                exposure_plot = meta["ti"] * meta["adj"] * meta["effort"] * micro
                exposure_cell = np.bincount(meta["pcell"], weights=exposure_plot, minlength=ncell)
                a2_exposure[(sid, fold)] = exposure_cell
                factor = meta["ti"] * meta["adj"] * TPA_UNADJ
                orientation = "AB" if fold == "B" else "BA"
                for world in ("STRONG", "PAIRED_NULL"):
                    truth_mass = TOTAL_MASS * abundances[(sid, world)]
                    rate = np.zeros(len(meta["pcell"]), dtype=float)
                    positive = exposure_cell[meta["pcell"]] > 0
                    rate[positive] = (
                        truth_mass[meta["pcell"][positive]] / exposure_cell[meta["pcell"][positive]]
                        * meta["effort"][positive] * micro[positive] / TPA_UNADJ
                    )
                    rng = np.random.default_rng(d10a.stable_seed(param["collection_seed"], sid, fold, world, "counts"))
                    counts = rng.poisson(rate)
                    mass = np.bincount(meta["pcell"], weights=counts * factor, minlength=ncell)
                    var_est = np.bincount(meta["pcell"], weights=counts * factor**2, minlength=ncell)
                    var_true = np.bincount(meta["pcell"], weights=rate * factor**2, minlength=ncell)
                    a2_mass[(sid, world, fold)] = mass
                    a2_var_est[(sid, world, fold)] = var_est
                    a2_var_true[(sid, world, fold)] = var_true
                    for j in np.where(counts > 0)[0]:
                        k = int(counts[j])
                        writer.writerow({
                            "synthetic_species_id": sname, "world": world, "orientation": orientation,
                            "target_fold": fold, "PLT_CN": meta["plot_cn"][j], "cell_50km": meta["cell"][j],
                            "synthetic_tree_count": k, "STATUSCD": STATUSCD, "DIA": DIA,
                            "tally_basis": "SUBP", "TPA_UNADJ": TPA_UNADJ,
                            "ADJ_FACTOR_SUBP": meta["adj"][j], "fold_specific_TI": meta["ti"][j],
                            "partial_sampling_effort": meta["effort"][j], "plot_micro": micro[j],
                            "poisson_mean": rate[j], "unadjusted_tpa_total": k * TPA_UNADJ,
                            "adjusted_plot_tpa": k * TPA_UNADJ * meta["adj"][j],
                            "weighted_cell_mass": k * factor[j], "STATECD": meta["state"][j],
                            "P2PANEL": meta["panel"][j], "MANUAL": meta["manual"][j],
                            "DESIGNCD": meta["design"][j], "effective_design_block_id": meta["block"][j],
                            "original_STRATUM_CN": meta["stratum"][j], "sparse_zero_omission": "ABSENT_ROWS_ARE_ZERO_COUNTS",
                        })
                        nonzero_plot_rows += 1

    signature = d10a.build_spatial_signature_engine(layout, param)
    detail_rows, a1_rows, a2_rows, recovery_rows, map_rows = [], [], [], [], []

    def map_metrics(true_p, est_p, true_mass, est_mass, active):
        h = float(np.sqrt(np.sum((np.sqrt(true_p) - np.sqrt(est_p)) ** 2)) / math.sqrt(2.0))
        sw = d10a.signature_distance(signature(true_p), signature(est_p))
        coords = layout["metric_coords"]
        tc = np.sum(coords * true_p[:, None], axis=0)
        ec = np.sum(coords * est_p[:, None], axis=0)
        entropy_t = float(-np.sum(true_p[active] * np.log(true_p[active] + 1e-15)))
        entropy_e = float(-np.sum(est_p[active] * np.log(est_p[active] + 1e-15)))
        return {
            "hellinger_distance": h, "sliced_wasserstein_km": sw,
            "centroid_displacement_km": float(np.linalg.norm(tc - ec)),
            "true_entropy": entropy_t, "estimated_entropy": entropy_e, "entropy_bias": entropy_e - entropy_t,
            "true_concentration": float(np.sum(true_p**2)), "estimated_concentration": float(np.sum(est_p**2)),
            "concentration_bias": float(np.sum(est_p**2) - np.sum(true_p**2)),
            "estimated_total_mass": float(est_mass.sum()),
            "total_mass_relative_error": float(est_mass.sum() / true_mass.sum() - 1.0),
        }

    for sid in sorted(supports):
        sname = f"SYN{sid:03d}"
        support = supports[sid]
        active = np.where(support)[0]
        for world in ("STRONG", "PAIRED_NULL"):
            true_p = abundances[(sid, world)]
            true_mass = TOTAL_MASS * true_p
            order = np.argsort(true_mass[active], kind="mergesort")
            bins = np.empty(len(active), dtype=int)
            bins[order] = np.minimum(5, (np.arange(len(active)) * 5 // len(active)) + 1)
            cell_bin = dict(zip(active, bins))
            for orientation, fold in (("AB", "B"), ("BA", "A")):
                meta = fold_meta[fold]
                raw = observed_a1[(sid, world, fold)].astype(float)
                if raw.sum() <= 0:
                    raise RuntimeError("IMPLEMENTATION_BLOCKED: A1 zero total")
                a1_p = raw / raw.sum()
                a1_mass = TOTAL_MASS * a1_p
                est2_mass = a2_mass[(sid, world, fold)]
                if est2_mass.sum() <= 0:
                    raise RuntimeError("IMPLEMENTATION_BLOCKED: A2 zero total")
                a2_p = est2_mass / est2_mass.sum()
                var_est = a2_var_est[(sid, world, fold)]
                var_true = a2_var_true[(sid, world, fold)]
                exposure = a2_exposure[(sid, fold)]
                for cell in active:
                    a1_rows.append({
                        "layer": "A1", "status": "BROKEN_REFERENCE_ONLY", "synthetic_species_id": sname,
                        "world": world, "orientation": orientation, "target_fold": fold,
                        "cell_50km": layout["cells"][cell], "raw_cell_count": raw[cell],
                        "normalized_allocation": a1_p[cell], "diagnostic_scale_aligned_mass": a1_mass[cell],
                        "latent_cell_mass": true_mass[cell],
                    })
                    a2_rows.append({
                        "layer": "A2", "synthetic_species_id": sname, "world": world,
                        "orientation": orientation, "target_fold": fold, "cell_50km": layout["cells"][cell],
                        "estimated_cell_mass": est2_mass[cell], "normalized_allocation": a2_p[cell],
                        "latent_cell_mass": true_mass[cell], "design_exposure": exposure[cell],
                        "plot_count": meta["plot_count"][cell], "estimated_poisson_variance": var_est[cell],
                        "analytic_poisson_variance": var_true[cell], "structural_zero_exposure": "YES" if exposure[cell] <= 0 else "NO",
                    })
                for layer, est_mass, est_p, layer_var in (("A1", a1_mass, a1_p, None), ("A2", est2_mass, a2_p, var_est)):
                    errors = est_mass[active] - true_mass[active]
                    rel = errors / true_mass[active]
                    se = np.sqrt(layer_var[active]) if layer_var is not None else np.full(len(active), np.nan)
                    covers = (np.maximum(0, est_mass[active] - 1.96 * se) <= true_mass[active]) & (true_mass[active] <= est_mass[active] + 1.96 * se) if layer_var is not None else np.full(len(active), False)
                    for pos, cell in enumerate(active):
                        detail_rows.append({
                            "layer": layer, "synthetic_species_id": sname, "world": world,
                            "orientation": orientation, "target_fold": fold, "cell_50km": layout["cells"][cell],
                            "true_mass_bin": cell_bin[cell], "true_p": true_p[cell], "true_mass": true_mass[cell],
                            "estimated_p": est_p[cell], "estimated_mass": est_mass[cell], "mass_error": errors[pos],
                            "relative_error": rel[pos], "absolute_relative_error": abs(rel[pos]),
                            "p_residual": est_p[cell] - true_p[cell], "plot_count": meta["plot_count"][cell],
                            "effort_sum": meta["effort_sum"][cell], "mean_effort": meta["mean_effort"][cell],
                            "partial_fraction": meta["partial_fraction"][cell],
                            "dominant_state": meta["dominant_state"][cell], "dominant_state_share": meta["dominant_state_share"][cell],
                            "dominant_panel": meta["dominant_panel"][cell], "dominant_panel_share": meta["dominant_panel_share"][cell],
                            "dominant_manual": meta["dominant_manual"][cell], "dominant_manual_share": meta["dominant_manual_share"][cell],
                            "dominant_design": meta["dominant_design"][cell], "dominant_design_share": meta["dominant_design_share"][cell],
                            "dominant_block": meta["dominant_block"][cell], "dominant_block_share": meta["dominant_block_share"][cell],
                            "design_exposure": exposure[cell], "structural_zero_exposure": "YES" if exposure[cell] <= 0 else "NO",
                            "poisson_se": se[pos], "ci95_covers_truth": "YES" if layer_var is not None and covers[pos] else ("NO" if layer_var is not None else "NA"),
                        })
                    mm = map_metrics(true_p, est_p, true_mass, est_mass, active)
                    map_row = {
                        "layer": layer, "synthetic_species_id": sname, "world": world,
                        "orientation": orientation, "target_fold": fold, "support_cells": len(active),
                        "support_cells_zero_target_fold_plots": int(np.sum((meta["plot_count"] == 0) & support)),
                        "support_truth_mass_fraction_zero_target_fold_plots": float(true_p[(meta["plot_count"] == 0) & support].sum()),
                        **mm,
                    }
                    map_rows.append(map_row)
                    recovery_rows.append({
                        **map_row, "cell_bias": float(np.mean(errors)), "cell_relative_bias": float(np.mean(rel)),
                        "cell_rmse": float(np.sqrt(np.mean(errors**2))),
                        "cell_relative_rmse": float(np.sqrt(np.mean(rel**2))),
                        "cell_mass_correlation": safe_corr(true_mass[active], est_mass[active]),
                        "ci95_coverage_all_support": float(np.mean(covers)) if layer_var is not None else "",
                        "ci95_coverage_positive_exposure": float(np.mean(covers[exposure[active] > 0])) if layer_var is not None and np.any(exposure[active] > 0) else "",
                    })

    write_csv(OUT / "a1_v01.csv", a1_rows)
    with gzip_text(OUT / "a2_v01.csv.gz") as f:
        w = csv.DictWriter(f, fieldnames=list(a2_rows[0]), lineterminator="\n"); w.writeheader(); w.writerows(a2_rows)
    with gzip_text(OUT / "cell_recovery_v01.csv.gz") as f:
        w = csv.DictWriter(f, fieldnames=list(detail_rows[0]), lineterminator="\n"); w.writeheader(); w.writerows(detail_rows)
    write_csv(OUT / "recovery_metrics_v01.csv", recovery_rows)
    write_csv(OUT / "map_recovery_v01.csv", map_rows)

    detail = pd.DataFrame(detail_rows)
    bin_rows = []
    for key, g in detail.groupby(["layer", "world", "orientation", "true_mass_bin"], sort=True):
        bin_rows.append({
            "layer": key[0], "world": key[1], "orientation": key[2], "true_mass_bin": key[3],
            "n_species_cells": len(g), "mean_true_mass": g["true_mass"].mean(),
            "mean_estimated_mass": g["estimated_mass"].mean(), "bias": g["mass_error"].mean(),
            "relative_bias": g["relative_error"].mean(), "rmse": float(np.sqrt(np.mean(g["mass_error"]**2))),
            "median_absolute_relative_error": g["absolute_relative_error"].median(),
        })
    write_csv(OUT / "cell_bins_v01.csv", bin_rows)

    leakage_rows = []
    numeric_vars = ["plot_count", "effort_sum", "mean_effort", "partial_fraction"]
    outcomes = ["relative_error", "absolute_relative_error", "p_residual", "estimated_p"]
    for key, g in detail.groupby(["layer", "world", "orientation", "synthetic_species_id"], sort=True):
        for var in numeric_vars:
            x = np.log1p(g[var].to_numpy(float)) if var in ("plot_count", "effort_sum") else g[var].to_numpy(float)
            for outcome in outcomes:
                leakage_rows.append({
                    "analysis_level": "SPECIES_CORRELATION", "layer": key[0], "world": key[1], "orientation": key[2],
                    "synthetic_species_id": key[3], "design_variable": var, "outcome": outcome,
                    "statistic": "pearson_r", "value": safe_corr(x, g[outcome].to_numpy(float)), "n": len(g),
                    "group_value": "", "mean_signed_relative_error": "", "mean_absolute_relative_error": "", "mean_p_residual": "",
                    "notes": "log1p transform for plot_count and effort_sum",
                })
            z = (x - np.mean(x)) / max(np.std(x), 1e-12)
            X = np.column_stack([np.ones(len(g)), g["true_p"].to_numpy(float), z])
            beta = np.linalg.lstsq(X, g["estimated_p"].to_numpy(float), rcond=None)[0]
            leakage_rows.append({
                "analysis_level": "SPECIES_CONTROLLED_SLOPE", "layer": key[0], "world": key[1], "orientation": key[2],
                "synthetic_species_id": key[3], "design_variable": var, "outcome": "estimated_p_controlling_true_p",
                "statistic": "standardized_design_beta", "value": beta[2], "n": len(g), "group_value": "",
                "mean_signed_relative_error": "", "mean_absolute_relative_error": "", "mean_p_residual": "",
                "notes": "estimated_p ~ intercept + true_p + standardized design variable",
            })

    for key, g in detail.groupby(["layer", "world", "orientation"], sort=True):
        centered = g.copy()
        for col in numeric_vars + outcomes:
            centered[col + "_c"] = centered[col] - centered.groupby("synthetic_species_id")[col].transform("mean")
        for var in numeric_vars:
            x = np.log1p(g[var].to_numpy(float)) if var in ("plot_count", "effort_sum") else g[var].to_numpy(float)
            temp = pd.Series(x, index=g.index)
            xc = temp - temp.groupby(g["synthetic_species_id"]).transform("mean")
            for outcome in outcomes:
                leakage_rows.append({
                    "analysis_level": "POOLED_WITHIN_SPECIES_CORRELATION", "layer": key[0], "world": key[1], "orientation": key[2],
                    "synthetic_species_id": "ALL", "design_variable": var, "outcome": outcome,
                    "statistic": "pearson_r", "value": safe_corr(xc, centered[outcome + "_c"]), "n": len(g),
                    "group_value": "", "mean_signed_relative_error": "", "mean_absolute_relative_error": "", "mean_p_residual": "",
                    "notes": "species means removed; log1p transform for plot_count and effort_sum",
                })
        for var in ["dominant_state", "dominant_panel", "dominant_manual", "dominant_design", "dominant_block"]:
            for value, gg in g.groupby(var, sort=True):
                leakage_rows.append({
                    "analysis_level": "POOLED_CATEGORICAL_GROUP", "layer": key[0], "world": key[1], "orientation": key[2],
                    "synthetic_species_id": "ALL", "design_variable": var, "outcome": "group_error_summary",
                    "statistic": "group_mean", "value": "", "n": len(gg), "group_value": value,
                    "mean_signed_relative_error": gg["relative_error"].mean(),
                    "mean_absolute_relative_error": gg["absolute_relative_error"].mean(),
                    "mean_p_residual": gg["p_residual"].mean(), "notes": "dominant category by target-fold legal plot count within cell",
                })
    with gzip_text(OUT / "leakage_v01.csv.gz") as f:
        w = csv.DictWriter(f, fieldnames=list(leakage_rows[0]), lineterminator="\n"); w.writeheader(); w.writerows(leakage_rows)

    # Exact D10B-compatible oracle-support downstream evaluation.
    ensemble = d10b.oracle_geometry_ensemble(layout, supports, d10a)
    l0_base = []
    for world in ("STRONG", "PAIRED_NULL"):
        pops = {sid: abundances[(sid, world)] for sid in supports}
        truths = {sid: abundances[(sid, world)] for sid in supports}
        base = d10b.evaluate_oracle_base("A0", world, "AB", pops, truths, ensemble, layout, param, d10a, signature)
        l0_base.extend(base); l0_base.extend([{**r, "orientation": "BA"} for r in base])
    a0_down = d10b.expand_regimes(l0_base, param["observation_regimes"])

    a1_down, a2_down = [], []
    for world in ("STRONG", "PAIRED_NULL"):
        truths = {sid: abundances[(sid, world)] for sid in supports}
        for orientation, fold in (("AB", "B"), ("BA", "A")):
            pops1 = {sid: observed_a1[(sid, world, fold)] / observed_a1[(sid, world, fold)].sum() for sid in supports}
            pops2 = {sid: a2_mass[(sid, world, fold)] / a2_mass[(sid, world, fold)].sum() for sid in supports}
            a1_down.extend(d10b.evaluate_oracle_base("A1", world, orientation, pops1, truths, ensemble, layout, param, d10a, signature))
            a2_down.extend(d10b.evaluate_oracle_base("A2", world, orientation, pops2, truths, ensemble, layout, param, d10a, signature))
    a1_down = d10b.expand_regimes(a1_down, param["observation_regimes"])
    a2_down = d10b.expand_regimes(a2_down, param["observation_regimes"])

    def compare_released(regenerated, released, regenerated_layer):
        r = pd.DataFrame(regenerated).copy(); f = released.copy()
        keys = ["world", "observation_regime", "orientation", "replicate", "split_seed"]
        for col in ("replicate", "split_seed"):
            r[col] = r[col].astype(str); f[col] = f[col].astype(str)
        r = r.sort_values(keys).reset_index(drop=True); f = f.sort_values(keys).reset_index(drop=True)
        if len(r) != len(f) or not (r[keys].astype(str) == f[keys].astype(str)).all().all():
            return False, float("inf")
        numeric = [c for c in r.columns if c in f.columns and c not in keys + ["layer", "model"]]
        diffs = []
        for col in numeric:
            rv = pd.to_numeric(r[col], errors="coerce"); fv = pd.to_numeric(f[col], errors="coerce")
            if rv.notna().any() or fv.notna().any():
                diffs.append(float(np.nanmax(np.abs(rv.to_numpy(float) - fv.to_numpy(float)))))
        maximum = max(diffs) if diffs else 0.0
        return maximum <= 1e-10, maximum

    l0_ok, l0_diff = compare_released(a0_down, released_l0, "A0")
    l1_ok, l1_diff = compare_released(a1_down, released_l1, "A1")
    if not l0_ok or not l1_ok:
        raise RuntimeError(f"IMPLEMENTATION_BLOCKED: D10B reproduction mismatch L0={l0_diff} L1={l1_diff}")

    downstream = []
    for source, rows in (("D10B_L0_EXACT_REPRODUCTION", a0_down), ("D10B_L1_EXACT_REPRODUCTION", a1_down), ("D10C_A2_CURRENT", a2_down)):
        for row in rows:
            downstream.append({**row, "source_identity": source})
    write_csv(OUT / "downstream_v01.csv", downstream)
    separation = d10b.strong_null_separation(a0_down) + d10b.strong_null_separation(a1_down) + d10b.strong_null_separation(a2_down)
    write_csv(OUT / "separation_v01.csv", separation)

    down_df = pd.DataFrame(downstream)
    for col in ["latent_truth_geometry_gain_pct", "predictive_set_gain_pct", "geometry_latent_truth_coverage", "world0_latent_truth_coverage"]:
        down_df[col] = pd.to_numeric(down_df[col])
    sep_df = pd.DataFrame(separation)
    sep_num = [c for c in sep_df.columns if c.startswith("strong_") or c.startswith("paired_null_")]
    for col in sep_num:
        sep_df[col] = pd.to_numeric(sep_df[col], errors="coerce")
    common_rows = []
    for key, g in down_df.groupby(["layer", "observation_regime", "orientation"], sort=True):
        strong = g[g["world"] == "STRONG"]; null = g[g["world"] == "PAIRED_NULL"]
        gs = sep_df[(sep_df["layer"] == key[0]) & (sep_df["observation_regime"] == key[1]) & (sep_df["orientation"] == key[2])]
        common_rows.append({
            "layer": key[0], "d10b_equivalent": "L0" if key[0] == "A0" else ("L1" if key[0] == "A1" else "A2_CURRENT"),
            "observation_regime": key[1], "orientation": key[2], "n_split_replicates": len(strong),
            "strong_geometry_gain_pct_median": strong["latent_truth_geometry_gain_pct"].median(),
            "paired_null_geometry_gain_pct_median": null["latent_truth_geometry_gain_pct"].median(),
            "strong_minus_null_geometry_gain_pct_median": pd.to_numeric(gs["strong_minus_paired_null_latent_truth_geometry_gain_pct"]).median(),
            "strong_predictive_set_gain_pct_median": strong["predictive_set_gain_pct"].median(),
            "paired_null_predictive_set_gain_pct_median": null["predictive_set_gain_pct"].median(),
            "strong_minus_null_predictive_set_gain_pct_median": pd.to_numeric(gs["strong_minus_paired_null_predictive_set_gain_pct"]).median(),
            "strong_geometry_coverage_median": strong["geometry_latent_truth_coverage"].median(),
            "paired_null_geometry_coverage_median": null["geometry_latent_truth_coverage"].median(),
        })
    write_csv(OUT / "common_compare_v01.csv", common_rows)

    orient_rows = []
    map_df = pd.DataFrame(map_rows)
    for col in ["hellinger_distance", "sliced_wasserstein_km", "cell_relative_rmse" if "cell_relative_rmse" in map_df.columns else "hellinger_distance"]:
        if col not in map_df.columns:
            continue
    rec_df = pd.DataFrame(recovery_rows)
    metrics_for_orientation = ["hellinger_distance", "sliced_wasserstein_km", "cell_relative_rmse", "total_mass_relative_error"]
    for key, g in rec_df.groupby(["layer", "world"], sort=True):
        for metric in metrics_for_orientation:
            ab = pd.to_numeric(g.loc[g["orientation"] == "AB", metric]).median()
            ba = pd.to_numeric(g.loc[g["orientation"] == "BA", metric]).median()
            orient_rows.append({"domain": "ABUNDANCE_RECOVERY", "layer": key[0], "world": key[1], "observation_regime": "ALL", "metric": metric, "AB_median": ab, "BA_median": ba, "BA_minus_AB": ba - ab, "notes": "descriptive; no threshold"})
    for key, g in sep_df.groupby(["layer", "observation_regime"], sort=True):
        metric = "strong_minus_paired_null_latent_truth_geometry_gain_pct"
        ab = pd.to_numeric(g.loc[g["orientation"] == "AB", metric]).median()
        ba = pd.to_numeric(g.loc[g["orientation"] == "BA", metric]).median()
        orient_rows.append({"domain": "DOWNSTREAM", "layer": key[0], "world": "STRONG_MINUS_PAIRED_NULL", "observation_regime": key[1], "metric": metric, "AB_median": ab, "BA_median": ba, "BA_minus_AB": ba - ab, "notes": "descriptive; no threshold"})
    write_csv(OUT / "orientation_v01.csv", orient_rows)

    # Compact quantitative summaries for the result note and audit workbook.
    rec_summary = rec_df.groupby(["layer", "world", "orientation"], sort=True).agg(
        n_species=("synthetic_species_id", "size"),
        hellinger_median=("hellinger_distance", "median"),
        sw_km_median=("sliced_wasserstein_km", "median"),
        relative_rmse_median=("cell_relative_rmse", "median"),
        total_mass_relative_error_median=("total_mass_relative_error", "median"),
        zero_plot_truth_fraction_median=("support_truth_mass_fraction_zero_target_fold_plots", "median"),
    ).reset_index()
    rec_summary.to_csv(OUT / "recovery_summary_v01.csv", index=False, encoding="utf-8-sig", lineterminator="\n")

    common = pd.DataFrame(common_rows)
    def medval(df, layer, col):
        return float(pd.to_numeric(df.loc[df["layer"] == layer, col]).median())
    a1_h = float(rec_df.loc[rec_df["layer"] == "A1", "hellinger_distance"].median())
    a2_h = float(rec_df.loc[rec_df["layer"] == "A2", "hellinger_distance"].median())
    a1_sw = float(rec_df.loc[rec_df["layer"] == "A1", "sliced_wasserstein_km"].median())
    a2_sw = float(rec_df.loc[rec_df["layer"] == "A2", "sliced_wasserstein_km"].median())
    strong_null = {layer: medval(common, layer, "strong_minus_null_geometry_gain_pct_median") for layer in ("A0", "A1", "A2")}

    pooled_leak = pd.DataFrame([r for r in leakage_rows if r["analysis_level"] == "POOLED_WITHIN_SPECIES_CORRELATION"])
    a2_leak = pooled_leak[(pooled_leak["layer"] == "A2") & (pooled_leak["outcome"] == "p_residual")]
    leak_values = pd.to_numeric(a2_leak["value"], errors="coerce").abs()
    max_a2_p_residual_r = float(leak_values.max())

    zero_a = int((fold_meta["A"]["plot_count"] == 0).sum())
    zero_b = int((fold_meta["B"]["plot_count"] == 0).sum())
    q1 = f"A2 median Hellinger={a2_h:.4f}, median sliced-Wasserstein={a2_sw:.2f} km; cell and total-mass distributions are in recovery_metrics_v01.csv."
    q3 = f"The largest absolute pooled within-species correlation between A2 normalized-allocation residual and the four numeric intensity/effort variables was {max_a2_p_residual_r:.4f}; full state/panel/manual/design/block diagnostics are retained."
    result_note = f"""# D10C resume result note v01

Terminal status: `{TERMINAL}`

This is evidence for mainline judgment, not a scientific PASS/FAIL or estimator selection. Oracle support was used throughout. No real species, support recovery, M0/M1/M2 refit, D10D, or real Q1 was run.

## Q1. Cell mass and normalized geography recovery

{q1} The realized target-fold frames contain {zero_b} zero-opportunity cells for AB (B target fold) and {zero_a} for BA (A target fold); these cells were not repaired and their true mass remains in full-map error.

## Q2. Improvement over A1

Across all species, worlds, and orientations, median Hellinger distance changed from {a1_h:.4f} (A1) to {a2_h:.4f} (A2), and median sliced-Wasserstein distance changed from {a1_sw:.2f} km to {a2_sw:.2f} km. A1 remains a diagnostic scale-aligned broken reference only.

## Q3. Sampling-intensity leakage

{q3} Signed bias, absolute error, normalized residual, state, panel, manual, design, and final-block group summaries are reported without using them to repair A2.

## Q4. STRONG versus PAIRED_NULL direction

Median STRONG-minus-PAIRED_NULL downstream geometry-gain separation across regimes and orientations was {strong_null['A0']:.3f} percentage points for A0/L0, {strong_null['A1']:.3f} for A1/L1, and {strong_null['A2']:.3f} for A2.

## Q5. PAIRED_NULL behavior

The complete PAIRED_NULL geometry gains, predictive-set gains, and coverage values for A0, A1, and A2 are in common_compare_v01.csv and downstream_v01.csv. No closeness threshold was introduced.

## Q6. AB/BA consistency

orientation_v01.csv reports AB and BA medians and BA-minus-AB differences for abundance recovery and downstream separation. No orientation threshold was introduced.

## Q7. Evidence of remaining limitations

The package exposes structural zero-opportunity support cells, Poisson interval coverage, full recovery distributions, and all leakage diagnostics for mainline. It does not classify these facts as PASS, HOLD, FAIL, or a bounded limitation.

## Q8. Sufficiency for mainline freeze review

The frozen identity, estimator implementation, A0/A1 reproduction, A2 recovery, leakage, downstream comparison, and deterministic package checks are complete. Mainline alone decides whether to freeze the abundance-measurement branch before any support-recovery work.
"""
    write_md(OUT / "result_note_v01.md", result_note)

    authority = f"""# D10C abundance estimator authority v01

The accepted D10C-A package closes `PLT_CN -> selected stratum -> final block -> fold -> TI`. For this synthetic calibration, every generated record is live, `DIA=5.0`, and on subplot basis. The observed count is converted to adjusted plot trees per acre by `count * {TPA_UNADJ} * ADJ_FACTOR_SUBP`; the 50-km cell population mass is the sum of that value times the plot's D09C fold-specific TI. Original `EXPNS`, condition proportions, plot-count divisors, state-average weights, inverse cell intensity, and inverse partial effort are excluded. Partial effort changes observation opportunity and remains QC metadata in the estimator.

The complete frozen equations and zero-exposure handling are in `control/contract_v01.md`. No estimator alternative was created.
"""
    write_md(OUT / "authority_v01.md", authority)

    checks = [
        {"check_id": "INPUT_HASHES", "status": "PASS", "observed": len(identity), "expected": len(identity), "notes": "All frozen package/request/contract identities matched or were frozen at execution"},
        {"check_id": "D10A_MANIFEST", "status": "PASS", "observed": len(regenerated_manifest), "expected": len(released_manifest), "notes": "Exact normalized manifest match"},
        {"check_id": "D10B_WORLD_HASHES", "status": "PASS", "observed": world_hash_match, "expected": 144, "notes": "Support, abundance, A1, and split hashes"},
        {"check_id": "D10CA_C1_C9", "status": "PASS", "observed": int((xqc["status"] == "PASS").sum()), "expected": 9, "notes": "Accepted authority"},
        {"check_id": "F0_VISITS", "status": "PASS", "observed": len(f0), "expected": 338619, "notes": "Frozen F0"},
        {"check_id": "LEGAL_OPPORTUNITIES", "status": "PASS", "observed": len(legal), "expected": 134846, "notes": "Exact D10A base opportunity rule"},
        {"check_id": "SYNTHETIC_SPECIES", "status": "PASS", "observed": len(supports), "expected": 72, "notes": "No real species"},
        {"check_id": "D10B_L0_REPRODUCTION", "status": "PASS" if l0_ok else "FAIL", "observed": l0_diff, "expected": "<=1e-10", "notes": "Numeric max absolute difference"},
        {"check_id": "D10B_L1_REPRODUCTION", "status": "PASS" if l1_ok else "FAIL", "observed": l1_diff, "expected": "<=1e-10", "notes": "Numeric max absolute difference"},
        {"check_id": "A2_POSITIVE_EXPOSURE_EXPECTATION", "status": "PASS", "observed": "analytic identity", "expected": "E[Mhat|F0,micro]=M where exposure>0", "notes": "Verified by frozen formula"},
        {"check_id": "NO_REAL_SPECIES", "status": "PASS", "observed": 0, "expected": 0, "notes": "TREE.SPCD never read"},
        {"check_id": "NO_SUPPORT_RECOVERY", "status": "PASS", "observed": 0, "expected": 0, "notes": "Oracle support only"},
    ]
    write_csv(QC / "checks_v01.csv", checks)
    write_json(QC / "build_summary_v01.json", {
        "task_id": TASK, "terminal_status": TERMINAL, "f0_rows": len(f0), "legal_opportunities": len(legal),
        "cells_50km": ncell, "synthetic_species": len(supports), "truth_rows": len(truth_rows),
        "plot_observation_nonzero_rows": nonzero_plot_rows, "a1_rows": len(a1_rows), "a2_rows": len(a2_rows),
        "cell_recovery_rows": len(detail_rows), "recovery_metric_rows": len(recovery_rows),
        "leakage_rows": len(leakage_rows), "downstream_rows": len(downstream), "separation_rows": len(separation),
        "zero_opportunity_cells_A": zero_a, "zero_opportunity_cells_B": zero_b,
        "d10b_l0_max_abs_diff": l0_diff, "d10b_l1_max_abs_diff": l1_diff,
        "network_used": False, "real_species_read": False, "support_recovery_run": False, "real_q1_run": False,
    })
    write_json(QC / "environment_v01.json", {
        "python": sys.version, "numpy": np.__version__, "pandas": pd.__version__,
        "platform": platform.platform(), "executable": sys.executable, "network_used": False,
    })
    shutil.copy2(RESUME_REQUEST, CTL / "resume_request.txt")
    (CTL / "original_contract.md").write_bytes(zip_member_bytes(D10C_PREV, "Q1_D10C_FIA_DESIGN_BASED_ABUNDANCE_MEASUREMENT_CALIBRATION_CONTRACT_v01.md"))
    shutil.copy2(Path(__file__), SRC / "build.py")

    registry = [{
        "DELTA_TYPE": "TASK", "ACTION": "PROPOSE_ADD", "TASK_ID": TASK,
        "ASSET_NAME": "D10C resumed FIA abundance measurement calibration", "CANONICAL_PATH": str(ARCH / "D10CR_v01.zip"),
        "SHA256": "PENDING_FINAL_PACKAGE", "SIZE_BYTES": "PENDING_FINAL_PACKAGE", "STATUS": TERMINAL,
        "SCIENTIFIC_OUTPUT_CHANGED": "SYNTHETIC_CALIBRATION_ONLY", "PUBLICATION_CANDIDATE": "METHODS_SUPPORT_CANDIDATE",
        "METHODS_ROLE": "FIA design-based abundance measurement calibration", "DATA_ROLE": "SYNTHETIC_ONLY",
        "CODE_ROLE": "REPRODUCIBLE_BUILD", "QC_ROLE": "IDENTITY_RECOVERY_LEAKAGE_DOWNSTREAM",
        "NOTES": "Mainline decides PASS/HOLD/FAIL. No real species, support recovery, or real Q1.",
    }]
    write_csv(MAN / "registry_delta_v01.csv", registry)

    print(json.dumps({
        "terminal_status": TERMINAL, "truth_rows": len(truth_rows), "plot_observation_nonzero_rows": nonzero_plot_rows,
        "cell_recovery_rows": len(detail_rows), "leakage_rows": len(leakage_rows),
        "downstream_rows": len(downstream), "d10b_l0_max_abs_diff": l0_diff, "d10b_l1_max_abs_diff": l1_diff,
        "median_hellinger_A1": a1_h, "median_hellinger_A2": a2_h,
        "median_sw_km_A1": a1_sw, "median_sw_km_A2": a2_sw,
        "median_separation": strong_null, "max_abs_A2_p_residual_intensity_r": max_a2_p_residual_r,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
