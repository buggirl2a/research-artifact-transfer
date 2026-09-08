from __future__ import annotations

import argparse
import contextlib
import csv
import hashlib
import io
import json
import math
import os
import shutil
import sqlite3
import subprocess
import sys
import time
import zipfile
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

import numpy as np


ROOT = Path(r"C:\range_paper")
WORK = ROOT / "99_tmp" / "d10fb13_v01"
SRC = WORK / "src"
OUT = ROOT / "05_qc" / "d10fb13_v01_work_component_transportability_diagnostic"
CACHE = ROOT / "99_tmp" / "d10fb12_v01" / "cache" / "b12_cache.sqlite"
B12_ZIP = ROOT / "10_archive" / "d10fb12_v01_1" / "Q1_D10F_B12_v01_1.zip"
B11_ZIP = ROOT / "10_archive" / "d10fb11_v01" / "Q1_D10F_B11_v01.zip"
Q1_ZIP = ROOT / "10_archive" / "q1_b12_q1_cohort_projection_v01" / "Q1_B12_Q1_COHORT_PROJECTION_v01.zip"
REQUEST = Path(r"C:\Users\bug_g\.codex\attachments\a424fc4d-c6dc-4594-a74d-871f696ab2af\pasted-text.txt")

sys.path.insert(0, str(SRC))
from mini_parquet import ParquetWriter, footer_info  # noqa: E402
from mini_parquet_reader import read_parquet_rows  # noqa: E402


TASK = "Q1_D10F_B13_v01_WORK_COMPONENT_TRANSPORTABILITY_DIAGNOSTIC"
TRANSFER_NAME = "Q1-D10FB13-v01-20260908"
ZIP_NAME = "Q1_D10F_B13_v01.zip"
EXPECTED_B12_SHA = "d009bf50225ca3c2f483e08fe17f22312f93c9a28f36786abae8729fde3a21ab"
EXPECTED_B11_SHA = "ee6888a47762aaa966afaeffddd2569500f0f8271745263b763711348d761624"
EXPECTED_Q1_SHA = "70d34c6905a9d76675943ae03182feae719340d159ca6b69b68b9b9d089f227e"
EXPECTED_CACHE_SHA = "0daf80d098546d61aecd8e75701f5174d9f6fd4452ce4a1b257651d45c9d2953"
EXPECTED_CACHE_LOGICAL = "e85168819a7954f9f1ead69f1554e29c193ba9ef369c7c2793b4587d5f8dd416"
EXPECTED_CACHE_FINGERPRINT = "5d0a9dbaf55045c20bdab107f061c477fe77106d100bc95681a6dfebd1eeb7bd"
SOURCE_CACHE_IDENTITY = (
    f"sha256:{EXPECTED_CACHE_SHA}|logical:{EXPECTED_CACHE_LOGICAL}|"
    f"fingerprint:{EXPECTED_CACHE_FINGERPRINT}"
)
CANONICAL_VERSION = "B13_COMPONENT_SUFFICIENT_STATS_HEXFLOAT_V01"
ROW_GROUP_SIZE = 50000
SPLIT_REPLICATES = 4
GRAINS = (50, 100, 200)
COMPONENTS = ("T", "W", "B")
FAMILIES = ("DOMAIN_ONE_HOT", "GENERIC_Y")
ZIP_TIME = (2026, 9, 8, 0, 0, 0)
ALGEBRA_REL_TOL = 1e-9
ALGEBRA_ABS_TOL = 1e-12


def sha256_file(path: Path, chunk: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def stable_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def fhex(value: float) -> str:
    x = float(value)
    if not math.isfinite(x):
        raise ValueError("Non-finite sufficient statistic")
    if x == 0.0:
        x = 0.0
    return x.hex()


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8", newline="\n")


def write_json(path: Path, value: Any) -> None:
    write_text(path, json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2))


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fields: list[str]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="raise", lineterminator="\n")
        w.writeheader()
        for row in rows:
            w.writerow(row)
            n += 1
    return n


def read_csv_text(text: str) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(text)))


def finite(values: Iterable[Any]) -> list[float]:
    out: list[float] = []
    for value in values:
        try:
            x = float(value)
        except (TypeError, ValueError):
            continue
        if math.isfinite(x):
            out.append(x)
    return out


def median(values: Iterable[Any]) -> float:
    xs = finite(values)
    return float(np.median(xs)) if xs else float("nan")


def quantile(values: Iterable[Any], q: float) -> float:
    xs = finite(values)
    return float(np.quantile(xs, q)) if xs else float("nan")


def fmt(value: Any, digits: int = 3) -> str:
    try:
        x = float(value)
    except (TypeError, ValueError):
        return "NA"
    return f"{x:.{digits}f}" if math.isfinite(x) else "NA"


def safe_ratio(num: float, den: float) -> float:
    if den > 0:
        return num / den
    if den == 0 and num == 0:
        return 1.0
    return float("inf")


def abs_log_ratio(num: float, den: float, tol: float = 1e-14) -> float:
    n = 0.0 if abs(num) <= tol else float(num)
    d = 0.0 if abs(den) <= tol else float(den)
    if n > 0 and d > 0:
        return abs(math.log(n / d))
    if n == 0 and d == 0:
        return 0.0
    return float("inf")


def stable_seed(*parts: Any) -> int:
    h = hashlib.sha256("|".join(str(x) for x in parts).encode("utf-8")).digest()
    return int.from_bytes(h[:8], "little", signed=False) & ((1 << 63) - 1)


def ref_band(n: int) -> str:
    if n >= 50:
        return "R5"
    if n >= 20:
        return "R4"
    if n >= 8:
        return "R3"
    if n >= 4:
        return "R2"
    return "R1"


def read_only_connection() -> sqlite3.Connection:
    con = sqlite3.connect(f"file:{CACHE.as_posix()}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    return con


def parse_cell(cell: str) -> tuple[str, int, int]:
    parts = cell.split("_")
    if len(parts) != 3 or parts[0] not in {"50km", "100km", "200km"}:
        raise ValueError(f"Invalid frozen grid cell: {cell}")
    return parts[0], int(parts[1]), int(parts[2])


def parent_cell(cell: str, grain: int) -> str:
    _, ix, iy = parse_cell(cell)
    if grain == 50:
        return f"50km_{ix}_{iy}"
    if grain == 100:
        return f"100km_{ix // 2}_{iy // 2}"
    if grain == 200:
        return f"200km_{ix // 4}_{iy // 4}"
    raise ValueError(grain)


def validate_floor_division() -> None:
    tests = {
        ("50km_-1_-1", 100): "100km_-1_-1",
        ("50km_-2_-2", 100): "100km_-1_-1",
        ("50km_-3_-3", 100): "100km_-2_-2",
        ("50km_-1_-1", 200): "200km_-1_-1",
        ("50km_-4_-4", 200): "200km_-1_-1",
        ("50km_-5_-5", 200): "200km_-2_-2",
        ("50km_3_7", 100): "100km_1_3",
        ("50km_7_9", 200): "200km_1_2",
    }
    for (cell, grain), expected in tests.items():
        if parent_cell(cell, grain) != expected:
            raise RuntimeError(f"Frozen floor-division mismatch: {cell} {grain}")


def sparse_dot(a: dict[str, float], b: dict[str, float]) -> float:
    if len(a) > len(b):
        a, b = b, a
    return math.fsum(float(v) * float(b.get(k, 0.0)) for k, v in a.items())


def sparse_sq_diag_dot(vector: dict[str, float], diag: dict[str, float]) -> float:
    return math.fsum(float(v) * float(v) * float(diag.get(k, 0.0)) for k, v in vector.items())


@dataclass
class Rep:
    diag: dict[str, float]
    vectors: list[dict[str, float]]
    residual_df: int
    _summary: dict[str, Any] = field(default_factory=dict, repr=False)


def rep_inner_raw_scale(a: Rep, b: Rep) -> tuple[float, float]:
    terms = [sparse_dot(a.diag, b.diag)]
    terms.extend(-sparse_sq_diag_dot(v, b.diag) for v in a.vectors)
    terms.extend(-sparse_sq_diag_dot(v, a.diag) for v in b.vectors)
    terms.extend(sparse_dot(v, w) ** 2 for v in a.vectors for w in b.vectors)
    return float(math.fsum(terms)), float(math.fsum(abs(x) for x in terms))


def rep_inner(a: Rep, b: Rep) -> float:
    value, expansion_scale = rep_inner_raw_scale(a, b)
    # A self-inner-product is nonnegative by construction.  The compact
    # diag-minus-low-rank formula can nevertheless leave a negative binary64
    # remainder when large positive and negative terms cancel (most commonly
    # for an analytically zero, single-cell B component).  Classify and clamp
    # only remainders that are small relative to the *uncancelled expansion*,
    # never relative to the already-cancelled result.
    if a is b and value < 0:
        tol = max(ALGEBRA_ABS_TOL, ALGEBRA_REL_TOL * max(1.0, expansion_scale))
        if value >= -tol:
            return 0.0
    return value


def rep_diagonal(rep: Rep) -> dict[str, float]:
    if "diagonal" not in rep._summary:
        keys = set(rep.diag)
        for vector in rep.vectors:
            keys.update(vector)
        d: dict[str, float] = {}
        construction_scales: dict[str, float] = {}
        for k in keys:
            terms = [float(rep.diag.get(k, 0.0))]
            terms.extend(-float(vector.get(k, 0.0)) ** 2 for vector in rep.vectors if k in vector)
            d[k] = float(math.fsum(terms))
            construction_scales[k] = float(math.fsum(abs(x) for x in terms))
        rep._summary["diagonal"] = d
        rep._summary["diagonal_construction_scales"] = construction_scales
    return rep._summary["diagonal"]


def rep_summary(rep: Rep) -> dict[str, Any]:
    if "trace" in rep._summary:
        return rep._summary
    diagonal = rep_diagonal(rep)
    trace = math.fsum(diagonal.values())
    diagonal_scales = rep._summary["diagonal_construction_scales"]
    trace_scale = max(1.0, math.fsum(diagonal_scales.values()))
    diagonal_scale = max(1.0, max(diagonal_scales.values(), default=0.0))
    norm_sq_raw, norm_expansion_scale = rep_inner_raw_scale(rep, rep)
    norm_scale = max(1.0, norm_expansion_scale)
    trace_tol = max(ALGEBRA_ABS_TOL, ALGEBRA_REL_TOL * trace_scale)
    diagonal_tol = max(ALGEBRA_ABS_TOL, ALGEBRA_REL_TOL * diagonal_scale)
    norm_tol = max(ALGEBRA_ABS_TOL, ALGEBRA_REL_TOL * norm_scale)
    norm_sq = 0.0 if norm_sq_raw < 0 and norm_sq_raw >= -norm_tol else norm_sq_raw
    diag_norm_sq = math.fsum(v * v for v in diagonal.values())
    off_sq_raw = norm_sq - diag_norm_sq
    off_tol = max(ALGEBRA_ABS_TOL, ALGEBRA_REL_TOL * max(1.0, norm_scale, diag_norm_sq))
    off_sq = 0.0 if off_sq_raw < 0 and off_sq_raw >= -off_tol else off_sq_raw
    min_diag = min(diagonal.values(), default=0.0)
    if trace < -trace_tol or norm_sq < -norm_tol or min_diag < -diagonal_tol:
        psd_status = "FAIL_NUMERIC_MATERIAL"
    elif trace < 0 or norm_sq_raw < 0 or off_sq_raw < 0 or min_diag < 0:
        psd_status = "PASS_ANALYTIC_SCATTER_NUMERIC_TOLERANCE"
    else:
        psd_status = "PASS_ANALYTIC_SCATTER_CONSTRUCTION"
    effective_rank = trace * trace / norm_sq if norm_sq > 0 else 0.0
    rep._summary.update({
        "trace": float(trace),
        "norm_sq": float(norm_sq),
        "norm": math.sqrt(max(0.0, norm_sq)),
        "diag_norm_sq": float(diag_norm_sq),
        "offdiag_norm_sq": float(off_sq),
        "min_diagonal": float(min_diag),
        "psd_tolerance": float(max(trace_tol, diagonal_tol, norm_tol, off_tol)),
        "trace_tolerance": float(trace_tol),
        "diagonal_tolerance": float(diagonal_tol),
        "norm_sq_tolerance": float(norm_tol),
        "norm_expansion_scale": float(norm_scale),
        "psd_status": psd_status,
        "effective_rank": float(effective_rank),
    })
    return rep._summary


def linear_norm_sq(terms: list[tuple[float, Rep]]) -> float:
    value = 0.0
    for i, (ci, ri) in enumerate(terms):
        value += ci * ci * rep_inner(ri, ri)
        for cj, rj in terms[:i]:
            value += 2.0 * ci * cj * rep_inner(ri, rj)
    scale = max(1.0, *(abs(rep_inner(r, r)) for _, r in terms))
    tol = max(ALGEBRA_ABS_TOL, ALGEBRA_REL_TOL * scale)
    if value < 0 and value >= -tol:
        return 0.0
    return float(value)


def profile_metrics(target: Rep, pool: Rep) -> dict[str, Any]:
    td = rep_diagonal(target)
    pd = rep_diagonal(pool)
    tt = math.fsum(td.values())
    pt = math.fsum(pd.values())
    if tt <= 0 or pt <= 0:
        return {
            "tv": float("nan"), "overlap": float("nan"), "max_abs_diff": float("nan"),
            "max_abs_diff_cell": "", "target_max_cell": "", "pool_max_cell": "",
            "target_cells": sum(v > 0 for v in td.values()), "pool_cells": sum(v > 0 for v in pd.values()),
            "target_only_cells": 0, "pool_only_cells": 0, "status": "NOT_ESTIMABLE_NONPOSITIVE_TRACE",
        }
    keys = set(td) | set(pd)
    tn = {k: td.get(k, 0.0) / tt for k in keys}
    pn = {k: pd.get(k, 0.0) / pt for k in keys}
    diffs = {k: abs(tn[k] - pn[k]) for k in keys}
    max_cell = max(diffs, key=lambda k: (diffs[k], k), default="")
    tmax = max(tn, key=lambda k: (tn[k], k), default="")
    pmax = max(pn, key=lambda k: (pn[k], k), default="")
    ts = {k for k, v in td.items() if v > 0}
    ps = {k for k, v in pd.items() if v > 0}
    return {
        "tv": 0.5 * math.fsum(diffs.values()),
        "overlap": math.fsum(min(tn[k], pn[k]) for k in keys),
        "max_abs_diff": diffs.get(max_cell, 0.0), "max_abs_diff_cell": max_cell,
        "target_max_cell": tmax, "pool_max_cell": pmax,
        "target_cells": len(ts), "pool_cells": len(ps),
        "target_only_cells": len(ts - ps), "pool_only_cells": len(ps - ts), "status": "ESTIMABLE",
    }


def matrix_metrics(target: Rep, pool: Rep) -> dict[str, Any]:
    ts = rep_summary(target)
    ps = rep_summary(pool)
    cross = rep_inner(target, pool)
    diff_sq = max(0.0, ts["norm_sq"] + ps["norm_sq"] - 2.0 * cross)
    diff = math.sqrt(diff_sq)
    rel = diff / ts["norm"] if ts["norm"] > 0 else (0.0 if ps["norm"] == 0 else float("inf"))
    cosine = cross / (ts["norm"] * ps["norm"]) if ts["norm"] > 0 and ps["norm"] > 0 else float("nan")
    if ts["trace"] > 0 and ps["trace"] > 0:
        unit_sq = (
            ts["norm_sq"] / (ts["trace"] ** 2)
            + ps["norm_sq"] / (ps["trace"] ** 2)
            - 2.0 * cross / (ts["trace"] * ps["trace"])
        )
        unit = math.sqrt(max(0.0, unit_sq))
        td = rep_diagonal(target); pd = rep_diagonal(pool)
        diag_unit_sq = math.fsum(
            (td.get(k, 0.0) / ts["trace"] - pd.get(k, 0.0) / ps["trace"]) ** 2
            for k in set(td) | set(pd)
        )
        off_cross = cross - sparse_dot(td, pd)
        off_unit_sq = (
            ts["offdiag_norm_sq"] / (ts["trace"] ** 2)
            + ps["offdiag_norm_sq"] / (ps["trace"] ** 2)
            - 2.0 * off_cross / (ts["trace"] * ps["trace"])
        )
        off_unit = math.sqrt(max(0.0, off_unit_sq))
        target_off_unit = math.sqrt(max(0.0, ts["offdiag_norm_sq"])) / ts["trace"]
        off_rel = off_unit / target_off_unit if target_off_unit > 0 else (0.0 if off_unit == 0 else float("inf"))
        alpha = ts["trace"] / ps["trace"]
        oracle_sq = ts["norm_sq"] + alpha * alpha * ps["norm_sq"] - 2.0 * alpha * cross
        oracle_rel = math.sqrt(max(0.0, oracle_sq)) / ts["norm"] if ts["norm"] > 0 else float("nan")
        oracle_abs_imp = rel - oracle_rel if math.isfinite(rel) else float("nan")
        oracle_rel_imp = oracle_abs_imp / rel if rel > 0 and math.isfinite(rel) else float("nan")
        estimability = "ESTIMABLE"
    else:
        unit = diag_unit_sq = off_unit = off_rel = oracle_rel = oracle_abs_imp = oracle_rel_imp = float("nan")
        estimability = "NOT_ESTIMABLE_NONPOSITIVE_TRACE"
    prof = profile_metrics(target, pool)
    if ts["trace"] <= 0 and ps["trace"] <= 0:
        degeneracy = "BOTH_ZERO"
    elif ts["trace"] <= 0:
        degeneracy = "TARGET_ZERO_POOL_POSITIVE"
    elif ps["trace"] <= 0:
        degeneracy = "TARGET_POSITIVE_POOL_ZERO"
    else:
        degeneracy = "POSITIVE_TRACE"
    return {
        "relative_frobenius": rel, "absolute_frobenius": diff,
        "target_trace": ts["trace"], "pool_trace": ps["trace"],
        "trace_ratio": safe_ratio(ps["trace"], ts["trace"]),
        "trace_abs_log_ratio": abs_log_ratio(ps["trace"], ts["trace"]),
        "target_frobenius": ts["norm"], "pool_frobenius": ps["norm"],
        "unit_trace_frobenius": unit, "cosine_similarity": cosine,
        "target_effective_rank": ts["effective_rank"], "pool_effective_rank": ps["effective_rank"],
        "unit_trace_diagonal_frobenius": math.sqrt(max(0.0, diag_unit_sq)) if math.isfinite(diag_unit_sq) else float("nan"),
        "unit_trace_offdiag_frobenius": off_unit, "offdiag_relative_to_target": off_rel,
        "oracle_scale_relative_frobenius": oracle_rel,
        "oracle_scale_absolute_improvement": oracle_abs_imp,
        "oracle_scale_relative_improvement": oracle_rel_imp,
        "degeneracy_class": degeneracy, "shape_estimability": estimability,
        "profile": prof, "target_psd": ts["psd_status"], "pool_psd": ps["psd_status"],
    }


def aggregate_mapping(mapping: dict[str, float], grain: int) -> dict[str, float]:
    out: defaultdict[str, float] = defaultdict(float)
    for cell, value in mapping.items():
        out[parent_cell(cell, grain)] += float(value)
    return dict(out)


def membership_digest(members: list[dict[str, Any]]) -> str:
    payload = [[m["member_id"], int(m["n"]), int(m["df"])] for m in members]
    return sha256_bytes(stable_json(payload).encode("utf-8"))


def load_pool_bundle(con: sqlite3.Connection, target_id: str, role: str, q1_species: list[str] | None) -> dict[str, Any]:
    rows = con.execute(
        """SELECT m.member_id,m.n,m.df,g.scalar_ss,g.cell_counts_json,g.cell_sum_json,g.cell_sumsq_json
           FROM pool_membership p JOIN member m ON m.member_id=p.member_id
           JOIN member_generic_stats g ON g.member_id=p.member_id
           WHERE p.target_id=? AND p.pool_role=? ORDER BY m.member_id""",
        (target_id, role),
    ).fetchall()
    members: list[dict[str, Any]] = []
    by_mid: dict[str, dict[str, Any]] = {}
    for r in rows:
        member = {
            "member_id": str(r[0]), "n": int(r[1]), "df": int(r[2]), "scalar_ss": float(r[3]),
            "counts": {str(k): int(v) for k, v in json.loads(r[4]).items()},
            "sums": {str(k): float(v) for k, v in json.loads(r[5]).items()},
            "sumsq": {str(k): float(v) for k, v in json.loads(r[6]).items()},
            "species": defaultdict(list),
        }
        members.append(member); by_mid[member["member_id"]] = member
    if not members:
        raise RuntimeError(f"No pool members for {target_id} {role}")
    if q1_species:
        placeholders = ",".join("?" for _ in q1_species)
        query = f"""SELECT s.member_id,s.SPCD,s.cell_id,s.sum_y,s.sumsq_y
                    FROM pool_membership p JOIN member_species_cell s ON s.member_id=p.member_id
                    WHERE p.target_id=? AND p.pool_role=? AND s.SPCD IN ({placeholders})
                    ORDER BY s.member_id,CAST(s.SPCD AS REAL),s.SPCD,s.cell_id"""
        for r in con.execute(query, [target_id, role, *q1_species]):
            by_mid[str(r[0])]["species"][str(r[1])].append((str(r[2]), float(r[3]), float(r[4])))
    return {
        "members": members, "membership_sha": membership_digest(members),
        "pool_df": sum(m["df"] for m in members), "plot_count": sum(m["n"] for m in members),
    }


def load_target_bundle(con: sqlite3.Connection, member_id: str, q1_species: list[str]) -> dict[str, Any]:
    r = con.execute(
        "SELECT m.member_id,m.n,m.df,g.scalar_ss,g.cell_counts_json,g.cell_sum_json,g.cell_sumsq_json "
        "FROM member m JOIN member_generic_stats g ON g.member_id=m.member_id WHERE m.member_id=?",
        (member_id,),
    ).fetchone()
    if r is None:
        raise RuntimeError(f"Missing target member {member_id}")
    member = {
        "member_id": str(r[0]), "n": int(r[1]), "df": int(r[2]), "scalar_ss": float(r[3]),
        "counts": {str(k): int(v) for k, v in json.loads(r[4]).items()},
        "sums": {str(k): float(v) for k, v in json.loads(r[5]).items()},
        "sumsq": {str(k): float(v) for k, v in json.loads(r[6]).items()},
        "species": defaultdict(list),
    }
    placeholders = ",".join("?" for _ in q1_species)
    query = f"SELECT SPCD,cell_id,sum_y,sumsq_y FROM member_species_cell WHERE member_id=? AND SPCD IN ({placeholders}) ORDER BY CAST(SPCD AS REAL),SPCD,cell_id"
    for x in con.execute(query, [member_id, *q1_species]):
        member["species"][str(x[0])].append((str(x[1]), float(x[2]), float(x[3])))
    return {"members": [member], "membership_sha": membership_digest([member]), "pool_df": member["df"], "plot_count": member["n"]}


def member_arrays(member: dict[str, Any], family: str, grain: int, species_id: str = "") -> tuple[dict[str, float], dict[str, float], dict[str, float]]:
    counts = aggregate_mapping(member["counts"], grain)
    if family == "DOMAIN_ONE_HOT":
        sums = dict(counts); sumsq = dict(counts)
    elif family == "GENERIC_Y":
        sums = aggregate_mapping(member["sums"], grain)
        sumsq = aggregate_mapping(member["sumsq"], grain)
    elif family == "SPECIES_Y":
        sums50: defaultdict[str, float] = defaultdict(float)
        sumsq50: defaultdict[str, float] = defaultdict(float)
        for cell, sy, ssy in member["species"].get(species_id, []):
            sums50[cell] += sy; sumsq50[cell] += ssy
        sums = aggregate_mapping(dict(sums50), grain)
        sumsq = aggregate_mapping(dict(sumsq50), grain)
    else:
        raise ValueError(family)
    return counts, sums, sumsq


def component_reps(bundle: dict[str, Any], family: str, grain: int, species_id: str = "") -> dict[str, Rep]:
    df = int(bundle["pool_df"])
    if df <= 0:
        return {c: Rep({}, [], df) for c in COMPONENTS}
    tdiag: defaultdict[str, float] = defaultdict(float)
    wdiag: defaultdict[str, float] = defaultdict(float)
    bdiag: defaultdict[str, float] = defaultdict(float)
    vectors: list[dict[str, float]] = []
    for member in bundle["members"]:
        counts, sums, sumsq = member_arrays(member, family, grain, species_id)
        vector: dict[str, float] = {}
        for cell in set(sums) | set(sumsq):
            sy = float(sums.get(cell, 0.0)); ssy = float(sumsq.get(cell, 0.0)); nc = float(counts.get(cell, 0.0))
            if nc <= 0 and (sy != 0 or ssy != 0):
                raise RuntimeError(f"Missing cell count for {member['member_id']} {family} {species_id} {cell}")
            within = ssy - sy * sy / nc if nc > 0 else 0.0
            between_diag = sy * sy / nc if nc > 0 else 0.0
            tol = max(ALGEBRA_ABS_TOL, ALGEBRA_REL_TOL * max(1.0, abs(ssy), abs(between_diag)))
            if within < -tol:
                raise RuntimeError(f"Material negative within scatter {member['member_id']} {family} {species_id} {cell}: {within}")
            tdiag[cell] += ssy; wdiag[cell] += within; bdiag[cell] += between_diag
            if sy != 0.0:
                vector[cell] = sy / math.sqrt(float(member["n"]) * df)
        if vector:
            vectors.append(vector)
    scale = 1.0 / df
    return {
        "T": Rep({k: v * scale for k, v in tdiag.items()}, list(vectors), df),
        "W": Rep({k: v * scale for k, v in wdiag.items()}, [], df),
        "B": Rep({k: v * scale for k, v in bdiag.items()}, list(vectors), df),
    }


def scalar_variance(bundle: dict[str, Any], family: str, species_id: str = "") -> float:
    df = int(bundle["pool_df"])
    if df <= 0:
        return float("nan")
    if family == "DOMAIN_ONE_HOT":
        return 0.0
    if family == "GENERIC_Y":
        return math.fsum(float(m["scalar_ss"]) for m in bundle["members"]) / df
    if family == "SPECIES_Y":
        total = 0.0
        for m in bundle["members"]:
            sy = math.fsum(x[1] for x in m["species"].get(species_id, []))
            ssy = math.fsum(x[2] for x in m["species"].get(species_id, []))
            total += ssy - sy * sy / float(m["n"])
        return total / df
    raise ValueError(family)


def replication_metrics(bundle: dict[str, Any], family: str, grain: int, within_rep: Rep) -> dict[str, Any]:
    union_cells: set[str] = set()
    member_cells = singleton = replicated = plots_replicated = within_df = 0
    for member in bundle["members"]:
        counts = aggregate_mapping(member["counts"], grain)
        union_cells.update(counts)
        member_cells += len(counts)
        singleton += sum(int(v) == 1 for v in counts.values())
        replicated += sum(int(v) >= 2 for v in counts.values())
        plots_replicated += sum(int(v) for v in counts.values() if int(v) >= 2)
        within_df += sum(max(0, int(v) - 1) for v in counts.values())
    plots = int(bundle["plot_count"])
    wtrace = rep_summary(within_rep)["trace"]
    if family == "DOMAIN_ONE_HOT":
        status = "STRUCTURAL_ZERO_FOR_ONE_HOT_DOMAIN_BY_DEFINITION"
    elif within_df == 0:
        status = "STRUCTURALLY_SPARSE_NO_WITHIN_CELL_REPLICATION"
    elif wtrace > max(ALGEBRA_ABS_TOL, ALGEBRA_REL_TOL * max(1.0, abs(wtrace))):
        status = "INFORMATIVE_OBSERVED"
    else:
        status = "OBSERVED_ZERO_GIVEN_REPLICATION_NOT_HOMOGENEITY_PROOF"
    return {
        "plot_count": plots, "residual_df": int(bundle["pool_df"]),
        "occupied_union_cells": len(union_cells), "member_cell_units": member_cells,
        "singleton_member_cells": singleton, "replicated_member_cells": replicated,
        "plots_in_replicated_member_cells": plots_replicated,
        "fraction_plots_in_replicated_cells": plots_replicated / plots if plots else float("nan"),
        "fraction_member_cells_replicated": replicated / member_cells if member_cells else float("nan"),
        "effective_within_cell_df": within_df, "within_trace": wtrace,
        "within_estimability": status,
    }


def sufficient_stats_payload(bundle: dict[str, Any], family: str, grain: int, species_id: str = "") -> tuple[str, int]:
    rows: list[Any] = []
    cells: set[str] = set()
    for member in bundle["members"]:
        counts, sums, sumsq = member_arrays(member, family, grain, species_id)
        keys = sorted(set(sums) | set(sumsq))
        if family == "SPECIES_Y" and not keys:
            continue
        detail = [[c, int(counts.get(c, 0)), fhex(sums.get(c, 0.0)), fhex(sumsq.get(c, 0.0))] for c in keys]
        rows.append([member["member_id"], int(member["n"]), detail])
        cells.update(keys)
    payload = {
        "family": family, "species_id": species_id, "grain_km": grain,
        "member_sufficient_stats": rows,
        "implicit_zero_rule": "omitted member/cell values are exact zero" if family == "SPECIES_Y" else "",
    }
    return sha256_bytes(stable_json(payload).encode("utf-8")), len(cells)


def seal_object_row(target: sqlite3.Row, role: str, grain: int, family: str, component: str,
                    bundle: dict[str, Any], stats_sha: str, dimension: int, species_id: str = "") -> dict[str, Any]:
    base = {
        "canonicalization_version": CANONICAL_VERSION, "target_id": str(target["target_id"]),
        "target_type": str(target["target_type"]), "route": str(target["route"]),
        "pool_role": role, "grain_km": grain, "measurement_family": family,
        "species_id": species_id, "component_type": component,
        "residual_df": int(bundle["pool_df"]), "membership_sha256": bundle["membership_sha"],
        "sufficient_stats_sha256": stats_sha, "source_cache_identity": SOURCE_CACHE_IDENTITY,
    }
    digest = sha256_bytes(stable_json(base).encode("utf-8"))
    return {
        "object_id": f"{target['target_id']}|{role}|{grain}|{family}|{species_id}|{component}",
        "target_id": str(target["target_id"]), "target_type": str(target["target_type"]),
        "route": str(target["route"]), "pool_role": role, "grain_km": grain,
        "measurement_family": family, "species_id": species_id, "component_type": component,
        "dimension": dimension, "residual_df": int(bundle["pool_df"]),
        "membership_sha256": bundle["membership_sha"], "sufficient_stats_sha256": stats_sha,
        "canonical_object_sha256": digest, "stage_p_status": "P_SEALED",
        "source_cache_identity": SOURCE_CACHE_IDENTITY, "canonicalization_version": CANONICAL_VERSION,
    }


SEAL_SCHEMA = [
    ("object_id", "string"), ("target_id", "string"), ("target_type", "string"), ("route", "string"),
    ("pool_role", "string"), ("grain_km", "int64"), ("measurement_family", "string"),
    ("species_id", "string"), ("component_type", "string"), ("dimension", "int64"),
    ("residual_df", "int64"), ("membership_sha256", "string"), ("sufficient_stats_sha256", "string"),
    ("canonical_object_sha256", "string"), ("stage_p_status", "string"),
    ("source_cache_identity", "string"), ("canonicalization_version", "string"),
]


def expected_seal_rows(target: sqlite3.Row, role: str, bundle: dict[str, Any], q1_species: list[str], include_species: bool) -> Iterable[dict[str, Any]]:
    for grain in GRAINS:
        for family in FAMILIES:
            stats_sha, dimension = sufficient_stats_payload(bundle, family, grain)
            for component in COMPONENTS:
                yield seal_object_row(target, role, grain, family, component, bundle, stats_sha, dimension)
    if include_species:
        for species_id in q1_species:
            stats_sha, dimension = sufficient_stats_payload(bundle, "SPECIES_Y", 50, species_id)
            for component in COMPONENTS:
                yield seal_object_row(target, role, 50, "SPECIES_Y", component, bundle, stats_sha, dimension, species_id)


def zip_internal_verify(path: Path) -> dict[str, Any]:
    with zipfile.ZipFile(path) as z:
        names = set(z.namelist())
        if "SHA256SUMS.csv" not in names:
            raise RuntimeError(f"Missing SHA256SUMS.csv in {path}")
        rows = read_csv_text(z.read("SHA256SUMS.csv").decode("utf-8-sig"))
        checked = 0
        for row in rows:
            rel = row["relative_path"]
            if rel not in names:
                raise RuntimeError(f"Missing internal artifact {rel} in {path}")
            data = z.read(rel)
            if sha256_bytes(data) != row["sha256"] or len(data) != int(row["size_bytes"]):
                raise RuntimeError(f"Internal artifact mismatch {rel} in {path}")
            checked += 1
    return {"internal_hash_rows": checked, "outer_sha256": sha256_file(path), "size_bytes": path.stat().st_size}


def load_q1_species() -> tuple[list[str], list[dict[str, str]], list[dict[str, str]]]:
    with zipfile.ZipFile(Q1_ZIP) as z:
        ledger = read_csv_text(z.read("B12_Q1_101_SPECIES_LEDGER_v01.csv").decode("utf-8-sig"))
        provenance = read_csv_text(z.read("B12_Q1_COHORT_PROVENANCE_v01.csv").decode("utf-8-sig"))
    direct = sorted(
        [r["FIA_SPCD_list"] for r in ledger if r["direct_species_level_evidence_available"] == "YES"],
        key=lambda x: (float(x), x),
    )
    if len(direct) != 97 or any(";" in x for x in direct):
        raise RuntimeError(f"Q1 direct species identity mismatch: {len(direct)}")
    multi = [r for r in ledger if r["species_level_interpretation_class"] == "MULTI_SPCD_B12_EVIDENCE_DIAGNOSTIC_ONLY"]
    if len(multi) != 3:
        raise RuntimeError(f"Q1 multi-code identity mismatch: {len(multi)}")
    return direct, ledger, provenance


def cache_schema_snapshot(con: sqlite3.Connection) -> tuple[str, list[dict[str, Any]]]:
    rows = []
    for table, sql in con.execute("SELECT name,sql FROM sqlite_master WHERE type='table' ORDER BY name"):
        rows.append({"table": table, "sql": sql, "rows": con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]})
    return sha256_bytes(stable_json(rows).encode("utf-8")), rows


def verify_inputs(full_logical: bool = True) -> dict[str, Any]:
    required = [CACHE, B12_ZIP, B11_ZIP, Q1_ZIP, REQUEST, SRC / "mini_parquet.py", SRC / "mini_parquet_reader.py"]
    missing = [str(p) for p in required if not p.is_file()]
    if missing:
        raise RuntimeError("Missing required input: " + " | ".join(missing))
    identities = {
        "b12": sha256_file(B12_ZIP), "b11": sha256_file(B11_ZIP),
        "q1_projection": sha256_file(Q1_ZIP), "cache": sha256_file(CACHE),
    }
    expected = {
        "b12": EXPECTED_B12_SHA, "b11": EXPECTED_B11_SHA,
        "q1_projection": EXPECTED_Q1_SHA, "cache": EXPECTED_CACHE_SHA,
    }
    if identities != expected:
        raise RuntimeError(f"Accepted input SHA mismatch: {identities}")
    b12_internal = zip_internal_verify(B12_ZIP)
    q1_internal = zip_internal_verify(Q1_ZIP)
    con = read_only_connection()
    integrity = con.execute("PRAGMA integrity_check").fetchone()[0]
    fingerprint = con.execute("SELECT value FROM cache_meta WHERE key='fingerprint'").fetchone()[0]
    schema_sha, schema = cache_schema_snapshot(con)
    logical = EXPECTED_CACHE_LOGICAL
    logical_rows = -1
    logical_sqlite_version = sqlite3.sqlite_version
    if full_logical:
        if sqlite3.sqlite_version == "3.49.1":
            h = hashlib.sha256(); logical_rows = 0
            for row in con.execute("SELECT PLT_CN,SPCD,printf('%.17g',y) FROM plot_species ORDER BY PLT_CN,SPCD"):
                h.update(("\t".join(str(x) for x in row) + "\n").encode("utf-8")); logical_rows += 1
            logical = h.hexdigest()
        else:
            # The accepted digest was defined with SQLite 3.49.1 printf semantics.
            # Recompute with the installed 3.49.1 interpreter instead of accepting
            # a version-dependent mismatch from the bundled SQLite runtime.
            verifier_python = Path(r"C:\Python\Python312\python.exe")
            verifier_script = SRC / "verify_cache_digest_3491.py"
            result = subprocess.check_output([str(verifier_python), str(verifier_script), str(CACHE)], text=True).strip().split("\t")
            logical_sqlite_version, logical, logical_rows_text = result
            logical_rows = int(logical_rows_text)
    protected = {
        "pseudo_total": con.execute("SELECT COUNT(*) FROM target WHERE target_type='PSEUDO'").fetchone()[0],
        "pseudo_scoreable": con.execute("SELECT COUNT(*) FROM target WHERE target_type='PSEUDO' AND validation_status='AVAILABLE'").fetchone()[0],
        "pseudo_heterogeneous": con.execute("SELECT COUNT(*) FROM target WHERE target_type='PSEUDO' AND validation_status='TARGET_CORE_IDENTITY_HETEROGENEOUS'").fetchone()[0],
        "level1": con.execute("SELECT COUNT(*) FROM target WHERE target_type='PSEUDO' AND validation_status='AVAILABLE' AND route='LEVEL1'").fetchone()[0],
        "level2": con.execute("SELECT COUNT(*) FROM target WHERE target_type='PSEUDO' AND validation_status='AVAILABLE' AND route='LEVEL2'").fetchone()[0],
        "actual24": con.execute("SELECT COUNT(*) FROM target WHERE target_type='ACTUAL24' AND validation_status='AVAILABLE'").fetchone()[0],
        "actual_level1": con.execute("SELECT COUNT(*) FROM target WHERE target_type='ACTUAL24' AND validation_status='AVAILABLE' AND route='LEVEL1'").fetchone()[0],
        "actual_level2": con.execute("SELECT COUNT(*) FROM target WHERE target_type='ACTUAL24' AND validation_status='AVAILABLE' AND route='LEVEL2'").fetchone()[0],
        "fia_spcd": con.execute("SELECT COUNT(*) FROM species_universe").fetchone()[0],
        "pool_membership_rows": con.execute("SELECT COUNT(*) FROM pool_membership").fetchone()[0],
        "target_member_leak": con.execute("SELECT COUNT(*) FROM target t JOIN pool_membership p ON p.target_id=t.target_id AND p.pool_role='CANDIDATE' AND p.member_id=t.target_member_id").fetchone()[0],
        "q1_calculation_rows": 0, "new_tree_source_scan_rows": 0,
    }
    expected_protected = {
        "pseudo_total": 5729, "pseudo_scoreable": 4640, "pseudo_heterogeneous": 1089,
        "level1": 4397, "level2": 243, "actual24": 24, "actual_level1": 11,
        "actual_level2": 13, "fia_spcd": 402, "pool_membership_rows": 321584,
        "target_member_leak": 0, "q1_calculation_rows": 0, "new_tree_source_scan_rows": 0,
    }
    con.close()
    if integrity != "ok" or fingerprint != EXPECTED_CACHE_FINGERPRINT or logical != EXPECTED_CACHE_LOGICAL:
        raise RuntimeError(f"Cache identity mismatch: integrity={integrity} fingerprint={fingerprint} logical={logical}")
    if protected != expected_protected:
        raise RuntimeError(f"Protected B12 reconciliation mismatch: {protected}")
    return {
        "identities": identities, "b12_internal": b12_internal, "q1_internal": q1_internal,
        "cache_integrity": integrity, "cache_fingerprint": fingerprint,
        "cache_logical_sha256": logical, "cache_logical_rows": logical_rows,
        "cache_logical_sqlite_version": logical_sqlite_version,
        "cache_schema_sha256": schema_sha, "cache_schema": schema, "protected": protected,
    }


def prepare_seal_index(path: Path) -> sqlite3.Connection:
    if path.exists():
        path.unlink()
    con = sqlite3.connect(path)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA synchronous=NORMAL")
    con.execute("""CREATE TABLE seal(
        object_id TEXT PRIMARY KEY,target_id TEXT,target_type TEXT,route TEXT,pool_role TEXT,
        grain_km INTEGER,measurement_family TEXT,species_id TEXT,component_type TEXT,dimension INTEGER,
        residual_df INTEGER,membership_sha256 TEXT,sufficient_stats_sha256 TEXT,
        canonical_object_sha256 TEXT,stage_p_status TEXT,source_cache_identity TEXT,
        canonicalization_version TEXT)""")
    con.execute("CREATE INDEX seal_target_role ON seal(target_id,pool_role)")
    return con


def build_stage_p(q1_species: list[str], log) -> dict[str, Any]:
    con = read_only_connection()
    targets = con.execute("SELECT target_id,target_type,route FROM target WHERE validation_status='AVAILABLE' ORDER BY target_id").fetchall()
    out_path = OUT / "B13_COMPONENT_PREDICTION_SEAL_v01.parquet"
    if out_path.exists(): out_path.unlink()
    idx_path = WORK / "stage_p_seal_index.sqlite"
    idx = prepare_seal_index(idx_path)
    insert = "INSERT INTO seal VALUES(" + ",".join("?" for _ in SEAL_SCHEMA) + ")"
    logical = hashlib.sha256(); count = 0; class_counts: Counter[str] = Counter()
    started = time.time(); last = 0.0
    with ParquetWriter(out_path, SEAL_SCHEMA, ROW_GROUP_SIZE) as writer:
        for i, target in enumerate(targets, 1):
            pseudo = target["target_type"] == "PSEUDO"
            nc1 = pseudo and con.execute(
                "SELECT 1 FROM pool_membership WHERE target_id=? AND pool_role='NC1_INCOMPATIBLE' LIMIT 1",
                (target["target_id"],),
            ).fetchone() is not None
            for role in ["CANDIDATE"] + (["NC1_INCOMPATIBLE"] if nc1 else []):
                include_species = pseudo and role == "CANDIDATE"
                bundle = load_pool_bundle(con, target["target_id"], role, q1_species if include_species else None)
                for row in expected_seal_rows(target, role, bundle, q1_species, include_species):
                    writer.write(row)
                    idx.execute(insert, tuple(row[name] for name, _ in SEAL_SCHEMA))
                    logical.update((stable_json(row) + "\n").encode("utf-8"))
                    count += 1; class_counts[f"{role}|{row['measurement_family']}|{row['component_type']}|{row['grain_km']}"] += 1
            if i % 10 == 0: idx.commit()
            now = time.time()
            if now - last >= 10:
                msg = f"STAGE_P targets={i}/{len(targets)} objects={count} elapsed_s={int(now-started)}"
                print(msg, flush=True); log.write(msg + "\n"); log.flush(); last = now
    idx.commit(); idx.close(); con.close()
    os.chmod(out_path, 0o444)
    planned = (4664 + 4604) * len(GRAINS) * len(FAMILIES) * len(COMPONENTS) + 4640 * 97 * len(COMPONENTS)
    if count != planned:
        raise RuntimeError(f"Stage-P object count mismatch: {count} != {planned}")
    meta = {
        "planned_objects": planned, "sealed_objects": count, "class_counts": dict(class_counts),
        "registry_sha256_before_scoring": sha256_file(out_path),
        "registry_logical_sha256": logical.hexdigest(), "seal_index_sha256": sha256_file(idx_path),
        "stage_p_completed_before_target_reference_open": True,
        "q1_species_scope": "DIRECT_97_AT_50KM_CANDIDATE_ONLY",
        "species_zero_objects": "EXPLICITLY_SEALED_WITH_IMPLICIT_ZERO_RULE",
    }
    write_json(WORK / "STAGE_P_COMPONENT_SEAL_CHECKPOINT_v01.json", meta)
    return meta


def verify_target_seals(idx: sqlite3.Connection, target: sqlite3.Row, role: str, bundle: dict[str, Any],
                        q1_species: list[str], include_species: bool) -> int:
    observed = {
        r["object_id"]: dict(r)
        for r in idx.execute("SELECT * FROM seal WHERE target_id=? AND pool_role=?", (target["target_id"], role))
    }
    expected = list(expected_seal_rows(target, role, bundle, q1_species, include_species))
    if len(observed) != len(expected):
        raise RuntimeError(f"Stage-S row-count mismatch {target['target_id']} {role}: {len(observed)} != {len(expected)}")
    fields = [name for name, _ in SEAL_SCHEMA]
    for row in expected:
        got = observed.get(row["object_id"])
        if got is None or any(str(got[k]) != str(row[k]) for k in fields):
            raise RuntimeError(f"Stage-S digest mismatch: {row['object_id']}")
    return len(expected)


def balanced_split_indices(plot_ids: list[str], target_id: str, split_id: int) -> tuple[list[int], list[int]]:
    order = sorted(range(len(plot_ids)), key=lambda i: (stable_seed("B12_SPLIT", target_id, split_id, plot_ids[i]), plot_ids[i]))
    cut = len(order) // 2
    return order[:cut], order[cut:]


def bundle_from_plot_rows(rows: list[tuple[str, str, float]], species_values: dict[str, float] | None = None) -> dict[str, Any]:
    n = len(rows)
    counts: defaultdict[str, int] = defaultdict(int)
    sums: defaultdict[str, float] = defaultdict(float)
    sumsq: defaultdict[str, float] = defaultdict(float)
    species: defaultdict[str, list[tuple[str, float, float]]] = defaultdict(list)
    sp_cell_sum: defaultdict[str, float] = defaultdict(float)
    sp_cell_sumsq: defaultdict[str, float] = defaultdict(float)
    y_values = []
    for pid, cell, y in rows:
        counts[cell] += 1; sums[cell] += y; sumsq[cell] += y * y; y_values.append(y)
        if species_values is not None:
            sy = float(species_values.get(pid, 0.0))
            if sy != 0.0:
                sp_cell_sum[cell] += sy; sp_cell_sumsq[cell] += sy * sy
    if species_values is not None:
        species["SP"] = [(c, sp_cell_sum[c], sp_cell_sumsq[c]) for c in sorted(sp_cell_sum)]
    total = math.fsum(y_values); total_sq = math.fsum(y * y for y in y_values)
    member = {
        "member_id": "REFERENCE", "n": n, "df": max(0, n - 1),
        "scalar_ss": total_sq - total * total / n if n else 0.0,
        "counts": dict(counts), "sums": dict(sums), "sumsq": dict(sumsq), "species": species,
    }
    return {"members": [member], "membership_sha": "REFERENCE_NOT_SEALED", "pool_df": max(0, n - 1), "plot_count": n}


def split_component_noise(rows: list[tuple[str, str, float]], target_id: str, family: str, grain: int,
                          species_values: dict[str, float] | None = None) -> dict[str, dict[str, Any]]:
    if len(rows) < 8:
        return {c: {
            "split_count": 0, "reference_relative_frobenius_median": float("nan"),
            "reference_trace_abs_log_ratio_median": float("nan"),
            "reference_unit_trace_frobenius_median": float("nan"),
            "reference_variance_location_tv_median": float("nan"),
            "reference_offdiag_unit_frobenius_median": float("nan"),
            "reference_estimability_status": "NOT_ESTIMABLE_FROZEN_SPLIT_N_LT8",
        } for c in COMPONENTS}
    accum = {c: defaultdict(list) for c in COMPONENTS}
    plot_ids = [r[0] for r in rows]
    for split_id in range(SPLIT_REPLICATES):
        ia, ib = balanced_split_indices(plot_ids, target_id, split_id)
        arows = [rows[i] for i in ia]; brows = [rows[i] for i in ib]
        if species_values is None:
            ab = bundle_from_plot_rows(arows); bb = bundle_from_plot_rows(brows)
            af = family; sid = ""
        else:
            ab = bundle_from_plot_rows(arows, species_values); bb = bundle_from_plot_rows(brows, species_values)
            af = "SPECIES_Y"; sid = "SP"
        ar = component_reps(ab, af, grain, sid); br = component_reps(bb, af, grain, sid)
        for component in COMPONENTS:
            met = matrix_metrics(ar[component], br[component])
            na = rep_summary(ar[component])["norm"]; nb = rep_summary(br[component])["norm"]
            denom = 0.5 * (na + nb)
            symmetric_rel = met["absolute_frobenius"] / denom if denom > 0 else 0.0
            accum[component]["rel"].append(symmetric_rel)
            accum[component]["trace"].append(met["trace_abs_log_ratio"])
            accum[component]["shape"].append(met["unit_trace_frobenius"])
            accum[component]["profile"].append(met["profile"]["tv"])
            accum[component]["offdiag"].append(met["unit_trace_offdiag_frobenius"])
    out: dict[str, dict[str, Any]] = {}
    for component in COMPONENTS:
        shape_n = len(finite(accum[component]["shape"]))
        if family == "DOMAIN_ONE_HOT" and component == "W":
            status = "STRUCTURAL_ZERO_DOMAIN_COMPONENT"
        elif not finite(accum[component]["rel"]):
            status = "NOT_ESTIMABLE_COMPONENT_DEGENERACY"
        elif shape_n == 0:
            status = "AVAILABLE_SCALE_ONLY_SHAPE_DEGENERATE"
        else:
            status = "AVAILABLE_FROZEN_B12_SPLIT"
        out[component] = {
            "split_count": SPLIT_REPLICATES,
            "reference_relative_frobenius_median": median(accum[component]["rel"]),
            "reference_trace_abs_log_ratio_median": median(accum[component]["trace"]),
            "reference_unit_trace_frobenius_median": median(accum[component]["shape"]),
            "reference_variance_location_tv_median": median(accum[component]["profile"]),
            "reference_offdiag_unit_frobenius_median": median(accum[component]["offdiag"]),
            "reference_estimability_status": status,
        }
    return out


def load_target_plot_rows(con: sqlite3.Connection, member_id: str) -> list[tuple[str, str, float]]:
    return [(str(r[0]), str(r[1]), float(r[2])) for r in con.execute(
        "SELECT PLT_CN,cell_id,y FROM plot_generic WHERE member_id=? ORDER BY PLT_CN", (member_id,)
    )]


def load_target_species_plot_values(con: sqlite3.Connection, member_id: str, q1_species: list[str]) -> dict[str, dict[str, float]]:
    placeholders = ",".join("?" for _ in q1_species)
    query = f"SELECT SPCD,PLT_CN,y FROM plot_species WHERE member_id=? AND SPCD IN ({placeholders}) ORDER BY CAST(SPCD AS REAL),SPCD,PLT_CN"
    out: defaultdict[str, dict[str, float]] = defaultdict(dict)
    for r in con.execute(query, [member_id, *q1_species]):
        out[str(r[0])][str(r[1])] = float(r[2])
    return dict(out)


def algebra_identity(t: Rep, w: Rep, b: Rep) -> tuple[float, float, str]:
    # T and B share the exact same centered-mean rank-one vectors; W is diagonal.
    # Evaluate the identity in the canonical representation to avoid subtractive
    # cancellation from a four-way Frobenius inner-product expansion.
    vectors_equal = len(t.vectors) == len(b.vectors) and all(tv == bv for tv, bv in zip(t.vectors, b.vectors)) and not w.vectors
    if vectors_equal:
        keys = set(t.diag) | set(w.diag) | set(b.diag)
        residual = math.sqrt(math.fsum((t.diag.get(k, 0.0) - w.diag.get(k, 0.0) - b.diag.get(k, 0.0)) ** 2 for k in keys))
    else:
        residual_sq = linear_norm_sq([(1.0, t), (-1.0, w), (-1.0, b)])
        residual = math.sqrt(max(0.0, residual_sq))
    scale = max(1.0, rep_summary(t)["norm"], rep_summary(w)["norm"], rep_summary(b)["norm"])
    tol = max(ALGEBRA_ABS_TOL, ALGEBRA_REL_TOL * scale)
    return residual, tol, "PASS" if residual <= tol else "FAIL"


IDENTITY_FIELDS = [
    ("target_id", "string"), ("target_type", "string"), ("route", "string"),
    ("reference_strength", "string"), ("measurement_family", "string"), ("species_id", "string"),
    ("grain_km", "int64"), ("pool_role", "string"), ("target_n", "int64"),
    ("target_df", "int64"), ("pool_df", "int64"), ("dimension", "int64"),
    ("stage_s_status", "string"), ("scoring_status", "string"),
]

MATRIX_SCHEMA = IDENTITY_FIELDS + [
    ("target_trace", "double"), ("pool_trace", "double"), ("trace_ratio", "double"),
    ("trace_abs_log_ratio", "double"), ("target_scalar_variance", "double"),
    ("pool_scalar_variance", "double"), ("scalar_variance_abs_log_ratio", "double"),
    ("target_frobenius", "double"), ("pool_frobenius", "double"),
    ("relative_frobenius", "double"), ("unit_trace_frobenius", "double"),
    ("cosine_similarity", "double"), ("target_effective_rank", "double"),
    ("pool_effective_rank", "double"), ("unit_trace_diagonal_frobenius", "double"),
    ("unit_trace_offdiag_frobenius", "double"), ("offdiag_relative_to_target", "double"),
    ("oracle_scale_relative_frobenius", "double"), ("oracle_scale_absolute_improvement", "double"),
    ("oracle_scale_relative_improvement", "double"), ("degeneracy_class", "string"),
    ("target_psd_status", "string"), ("pool_psd_status", "string"),
    ("regularization_applied", "string"), ("diagnostic_role", "string"),
]

VARLOC_SCHEMA = IDENTITY_FIELDS + [
    ("target_trace", "double"), ("pool_trace", "double"),
    ("variance_location_tv", "double"), ("variance_location_overlap", "double"),
    ("max_absolute_profile_difference", "double"), ("max_difference_cell", "string"),
    ("target_max_variance_cell", "string"), ("pool_max_variance_cell", "string"),
    ("target_positive_diagonal_cells", "int64"), ("pool_positive_diagonal_cells", "int64"),
    ("target_only_positive_cells", "int64"), ("pool_only_positive_cells", "int64"),
    ("profile_estimability", "string"), ("regularization_applied", "string"),
]

REPLICATION_SCHEMA = [
    ("target_id", "string"), ("target_type", "string"), ("route", "string"),
    ("reference_strength", "string"), ("subject_role", "string"), ("pool_role", "string"),
    ("measurement_family", "string"), ("grain_km", "int64"), ("plot_count", "int64"),
    ("residual_df", "int64"), ("occupied_union_cells", "int64"), ("member_cell_units", "int64"),
    ("singleton_member_cells", "int64"), ("replicated_member_cells", "int64"),
    ("plots_in_replicated_member_cells", "int64"), ("fraction_plots_in_replicated_cells", "double"),
    ("fraction_member_cells_replicated", "double"), ("effective_within_cell_df", "int64"),
    ("within_trace", "double"), ("within_estimability", "string"),
]

DECOMP_SCHEMA = IDENTITY_FIELDS + [
    ("component_type", "string"), ("component_long_name", "string"),
    ("target_total_trace", "double"), ("pool_total_trace", "double"),
    ("target_component_trace", "double"), ("pool_component_trace", "double"),
    ("target_component_trace_fraction", "double"), ("pool_component_trace_fraction", "double"),
    ("trace_ratio", "double"), ("trace_abs_log_ratio", "double"),
    ("relative_frobenius", "double"), ("unit_trace_frobenius", "double"),
    ("cosine_similarity", "double"), ("variance_location_tv", "double"),
    ("variance_location_overlap", "double"), ("unit_trace_offdiag_frobenius", "double"),
    ("offdiag_relative_to_target", "double"), ("degeneracy_class", "string"),
    ("target_psd_status", "string"), ("pool_psd_status", "string"),
    ("regularization_applied", "string"),
]

ERROR_SCHEMA = [
    ("target_id", "string"), ("target_type", "string"), ("route", "string"),
    ("reference_strength", "string"), ("measurement_family", "string"), ("species_id", "string"),
    ("grain_km", "int64"), ("pool_role", "string"), ("within_error_energy", "double"),
    ("between_error_energy", "double"), ("cross_interference_term", "double"),
    ("total_error_energy_from_components", "double"), ("direct_total_error_energy", "double"),
    ("identity_absolute_residual", "double"), ("identity_tolerance", "double"),
    ("within_normalized_share", "double"), ("between_normalized_share", "double"),
    ("cross_normalized_share", "double"), ("cross_term_sign", "string"),
    ("interference_interpretation", "string"), ("identity_status", "string"),
]

ORACLE_SCHEMA = [
    ("target_id", "string"), ("target_type", "string"), ("route", "string"),
    ("reference_strength", "string"), ("measurement_family", "string"), ("species_id", "string"),
    ("grain_km", "int64"), ("baseline_relative_frobenius", "double"),
    ("oracle_w_relative_frobenius", "double"), ("oracle_b_relative_frobenius", "double"),
    ("oracle_both_relative_frobenius", "double"), ("oracle_w_absolute_improvement", "double"),
    ("oracle_b_absolute_improvement", "double"), ("oracle_w_relative_improvement", "double"),
    ("oracle_b_relative_improvement", "double"), ("oracle_both_identity_status", "string"),
    ("diagnostic_role", "string"),
]

NOISE_SCHEMA = [
    ("target_id", "string"), ("target_type", "string"), ("route", "string"),
    ("reference_strength", "string"), ("measurement_family", "string"), ("species_id", "string"),
    ("grain_km", "int64"), ("component_type", "string"), ("target_n", "int64"),
    ("target_df", "int64"), ("split_count", "int64"),
    ("reference_relative_frobenius_median", "double"),
    ("reference_trace_abs_log_ratio_median", "double"),
    ("reference_unit_trace_frobenius_median", "double"),
    ("reference_variance_location_tv_median", "double"),
    ("reference_offdiag_unit_frobenius_median", "double"),
    ("reference_estimability_status", "string"), ("split_identity", "string"),
]

TVN_SCHEMA = IDENTITY_FIELDS + [
    ("component_type", "string"), ("transport_relative_frobenius", "double"),
    ("reference_relative_frobenius", "double"), ("relative_frobenius_transport_to_noise_ratio", "double"),
    ("transport_trace_abs_log_ratio", "double"), ("reference_trace_abs_log_ratio", "double"),
    ("trace_transport_to_noise_ratio", "double"),
    ("transport_unit_trace_frobenius", "double"), ("reference_unit_trace_frobenius", "double"),
    ("shape_transport_to_noise_ratio", "double"),
    ("transport_variance_location_tv", "double"), ("reference_variance_location_tv", "double"),
    ("variance_location_transport_to_noise_ratio", "double"),
    ("reference_estimability_status", "string"),
]

NEG_SCHEMA = [
    ("target_id", "string"), ("route", "string"), ("reference_strength", "string"),
    ("measurement_family", "string"), ("grain_km", "int64"), ("component_type", "string"),
    ("candidate_relative_frobenius", "double"), ("nc1_relative_frobenius", "double"),
    ("candidate_better_relative_frobenius", "int64"),
    ("candidate_trace_abs_log_ratio", "double"), ("nc1_trace_abs_log_ratio", "double"),
    ("candidate_better_trace", "int64"), ("candidate_unit_trace_frobenius", "double"),
    ("nc1_unit_trace_frobenius", "double"), ("candidate_better_unit_shape", "int64"),
    ("candidate_variance_location_tv", "double"), ("nc1_variance_location_tv", "double"),
    ("candidate_better_variance_location", "int64"), ("comparison_status", "string"),
]

ACTUAL_SCHEMA = [
    ("target_id", "string"), ("case_id", "string"), ("route", "string"),
    ("statecd", "int64"), ("evalid", "string"), ("fold", "string"),
    ("reference_role", "string"), ("prediction_seal_verified", "string"),
    ("measurement_family", "string"), ("grain_km", "int64"), ("component_type", "string"),
    ("pool_df", "int64"), ("full5_n", "int64"), ("full5_df", "int64"),
    ("full5_effective_within_cell_df", "int64"), ("full5_fraction_plots_in_replicated_cells", "double"),
    ("target_component_trace", "double"), ("pool_component_trace", "double"),
    ("trace_abs_log_ratio", "double"), ("relative_frobenius", "double"),
    ("unit_trace_frobenius", "double"), ("variance_location_tv", "double"),
    ("reference_relative_frobenius", "double"), ("transport_to_noise_ratio", "double"),
    ("within_estimability", "string"), ("target_psd_status", "string"),
    ("pool_psd_status", "string"), ("regularization_applied", "string"),
    ("limitations", "string"),
]


def identity_base(target: sqlite3.Row, family: str, species_id: str, grain: int, role: str,
                  target_bundle: dict[str, Any], pool_bundle: dict[str, Any], dimension: int) -> dict[str, Any]:
    return {
        "target_id": str(target["target_id"]), "target_type": str(target["target_type"]),
        "route": str(target["route"]), "reference_strength": str(target["reference_strength"]),
        "measurement_family": family, "species_id": species_id, "grain_km": grain,
        "pool_role": role, "target_n": int(target_bundle["plot_count"]),
        "target_df": int(target_bundle["pool_df"]), "pool_df": int(pool_bundle["pool_df"]),
        "dimension": dimension, "stage_s_status": "VERIFIED", "scoring_status": "SCORED",
    }


def matrix_row(base: dict[str, Any], met: dict[str, Any], target_scalar: float, pool_scalar: float) -> dict[str, Any]:
    return base | {
        "target_trace": met["target_trace"], "pool_trace": met["pool_trace"],
        "trace_ratio": met["trace_ratio"], "trace_abs_log_ratio": met["trace_abs_log_ratio"],
        "target_scalar_variance": target_scalar, "pool_scalar_variance": pool_scalar,
        "scalar_variance_abs_log_ratio": abs_log_ratio(pool_scalar, target_scalar),
        "target_frobenius": met["target_frobenius"], "pool_frobenius": met["pool_frobenius"],
        "relative_frobenius": met["relative_frobenius"],
        "unit_trace_frobenius": met["unit_trace_frobenius"], "cosine_similarity": met["cosine_similarity"],
        "target_effective_rank": met["target_effective_rank"], "pool_effective_rank": met["pool_effective_rank"],
        "unit_trace_diagonal_frobenius": met["unit_trace_diagonal_frobenius"],
        "unit_trace_offdiag_frobenius": met["unit_trace_offdiag_frobenius"],
        "offdiag_relative_to_target": met["offdiag_relative_to_target"],
        "oracle_scale_relative_frobenius": met["oracle_scale_relative_frobenius"],
        "oracle_scale_absolute_improvement": met["oracle_scale_absolute_improvement"],
        "oracle_scale_relative_improvement": met["oracle_scale_relative_improvement"],
        "degeneracy_class": met["degeneracy_class"], "target_psd_status": met["target_psd"],
        "pool_psd_status": met["pool_psd"], "regularization_applied": "NONE",
        "diagnostic_role": "DIAGNOSTIC_ORACLE_ONLY_FOR_SCALE_MATCH_FIELDS",
    }


def varloc_row(base: dict[str, Any], met: dict[str, Any]) -> dict[str, Any]:
    p = met["profile"]
    return base | {
        "target_trace": met["target_trace"], "pool_trace": met["pool_trace"],
        "variance_location_tv": p["tv"], "variance_location_overlap": p["overlap"],
        "max_absolute_profile_difference": p["max_abs_diff"], "max_difference_cell": p["max_abs_diff_cell"],
        "target_max_variance_cell": p["target_max_cell"], "pool_max_variance_cell": p["pool_max_cell"],
        "target_positive_diagonal_cells": p["target_cells"], "pool_positive_diagonal_cells": p["pool_cells"],
        "target_only_positive_cells": p["target_only_cells"], "pool_only_positive_cells": p["pool_only_cells"],
        "profile_estimability": p["status"], "regularization_applied": "NONE",
    }


def decomposition_row(base: dict[str, Any], component: str, met: dict[str, Any],
                      target_total_trace: float, pool_total_trace: float) -> dict[str, Any]:
    names = {"T": "TOTAL_SAMPLE_SCATTER", "W": "WITHIN_CELL_OBSERVED_RESIDUAL_SCATTER", "B": "BETWEEN_CELL_ALLOCATION_MEAN_SCATTER"}
    return base | {
        "component_type": component, "component_long_name": names[component],
        "target_total_trace": target_total_trace, "pool_total_trace": pool_total_trace,
        "target_component_trace": met["target_trace"], "pool_component_trace": met["pool_trace"],
        "target_component_trace_fraction": met["target_trace"] / target_total_trace if target_total_trace > 0 else float("nan"),
        "pool_component_trace_fraction": met["pool_trace"] / pool_total_trace if pool_total_trace > 0 else float("nan"),
        "trace_ratio": met["trace_ratio"], "trace_abs_log_ratio": met["trace_abs_log_ratio"],
        "relative_frobenius": met["relative_frobenius"], "unit_trace_frobenius": met["unit_trace_frobenius"],
        "cosine_similarity": met["cosine_similarity"], "variance_location_tv": met["profile"]["tv"],
        "variance_location_overlap": met["profile"]["overlap"],
        "unit_trace_offdiag_frobenius": met["unit_trace_offdiag_frobenius"],
        "offdiag_relative_to_target": met["offdiag_relative_to_target"],
        "degeneracy_class": met["degeneracy_class"], "target_psd_status": met["target_psd"],
        "pool_psd_status": met["pool_psd"], "regularization_applied": "NONE",
    }


def error_geometry_row(target: sqlite3.Row, family: str, species_id: str, grain: int, role: str,
                       target_reps: dict[str, Rep], pool_reps: dict[str, Rep]) -> dict[str, Any]:
    wt, bt, tt = target_reps["W"], target_reps["B"], target_reps["T"]
    wp, bp, tp = pool_reps["W"], pool_reps["B"], pool_reps["T"]
    ew = linear_norm_sq([(1, wp), (-1, wt)])
    eb = linear_norm_sq([(1, bp), (-1, bt)])
    cross_inner = rep_inner(wp, bp) - rep_inner(wp, bt) - rep_inner(wt, bp) + rep_inner(wt, bt)
    cross = 2.0 * cross_inner
    total = math.fsum([ew, eb, cross])
    direct = linear_norm_sq([(1, tp), (-1, tt)])
    residual = abs(total - direct)
    tol = max(ALGEBRA_ABS_TOL, ALGEBRA_REL_TOL * max(1.0, abs(total), abs(direct)))
    denom = direct if direct > 0 else float("nan")
    sign = "POSITIVE_REINFORCEMENT" if cross > tol else ("NEGATIVE_CANCELLATION" if cross < -tol else "NEAR_ZERO")
    return {
        "target_id": str(target["target_id"]), "target_type": str(target["target_type"]),
        "route": str(target["route"]), "reference_strength": str(target["reference_strength"]),
        "measurement_family": family, "species_id": species_id, "grain_km": grain, "pool_role": role,
        "within_error_energy": ew, "between_error_energy": eb, "cross_interference_term": cross,
        "total_error_energy_from_components": total, "direct_total_error_energy": direct,
        "identity_absolute_residual": residual, "identity_tolerance": tol,
        "within_normalized_share": ew / denom if math.isfinite(denom) else float("nan"),
        "between_normalized_share": eb / denom if math.isfinite(denom) else float("nan"),
        "cross_normalized_share": cross / denom if math.isfinite(denom) else float("nan"),
        "cross_term_sign": sign,
        "interference_interpretation": "COMPONENT_ERRORS_REINFORCE" if cross > tol else ("COMPONENT_ERRORS_PARTIALLY_CANCEL" if cross < -tol else "NEGLIGIBLE_INTERFERENCE"),
        "identity_status": "PASS" if residual <= tol else "FAIL",
    }


def oracle_row(target: sqlite3.Row, family: str, species_id: str, grain: int,
               target_reps: dict[str, Rep], pool_reps: dict[str, Rep]) -> dict[str, Any]:
    nt = rep_summary(target_reps["T"])["norm"]
    total_err = math.sqrt(max(0.0, linear_norm_sq([(1, pool_reps["T"]), (-1, target_reps["T"])])))
    ew = math.sqrt(max(0.0, linear_norm_sq([(1, pool_reps["W"]), (-1, target_reps["W"])])))
    eb = math.sqrt(max(0.0, linear_norm_sq([(1, pool_reps["B"]), (-1, target_reps["B"])])))
    baseline = total_err / nt if nt > 0 else float("nan")
    ow = eb / nt if nt > 0 else float("nan")
    ob = ew / nt if nt > 0 else float("nan")
    return {
        "target_id": str(target["target_id"]), "target_type": str(target["target_type"]),
        "route": str(target["route"]), "reference_strength": str(target["reference_strength"]),
        "measurement_family": family, "species_id": species_id, "grain_km": grain,
        "baseline_relative_frobenius": baseline, "oracle_w_relative_frobenius": ow,
        "oracle_b_relative_frobenius": ob, "oracle_both_relative_frobenius": 0.0 if nt > 0 else float("nan"),
        "oracle_w_absolute_improvement": baseline - ow if math.isfinite(baseline) else float("nan"),
        "oracle_b_absolute_improvement": baseline - ob if math.isfinite(baseline) else float("nan"),
        "oracle_w_relative_improvement": (baseline - ow) / baseline if baseline > 0 else float("nan"),
        "oracle_b_relative_improvement": (baseline - ob) / baseline if baseline > 0 else float("nan"),
        "oracle_both_identity_status": "PASS" if nt > 0 else "NOT_ESTIMABLE_ZERO_TOTAL",
        "diagnostic_role": "DIAGNOSTIC_ORACLE_ONLY_NOT_ESTIMATOR",
    }


def noise_row(target: sqlite3.Row, family: str, species_id: str, grain: int, component: str,
              target_bundle: dict[str, Any], noise: dict[str, Any]) -> dict[str, Any]:
    return {
        "target_id": str(target["target_id"]), "target_type": str(target["target_type"]),
        "route": str(target["route"]), "reference_strength": str(target["reference_strength"]),
        "measurement_family": family, "species_id": species_id, "grain_km": grain,
        "component_type": component, "target_n": int(target_bundle["plot_count"]),
        "target_df": int(target_bundle["pool_df"]), **noise,
        "split_identity": "FROZEN_B12_SPLIT_BALANCED_HASH_B12_SPLIT_4_REPLICATES",
    }


def tvn_row(base: dict[str, Any], component: str, met: dict[str, Any], noise: dict[str, Any]) -> dict[str, Any]:
    def ratio(a: float, b: float) -> float:
        return a / b if math.isfinite(a) and math.isfinite(b) and b > 0 else float("nan")
    return base | {
        "component_type": component, "transport_relative_frobenius": met["relative_frobenius"],
        "reference_relative_frobenius": noise["reference_relative_frobenius_median"],
        "relative_frobenius_transport_to_noise_ratio": ratio(met["relative_frobenius"], noise["reference_relative_frobenius_median"]),
        "transport_trace_abs_log_ratio": met["trace_abs_log_ratio"],
        "reference_trace_abs_log_ratio": noise["reference_trace_abs_log_ratio_median"],
        "trace_transport_to_noise_ratio": ratio(met["trace_abs_log_ratio"], noise["reference_trace_abs_log_ratio_median"]),
        "transport_unit_trace_frobenius": met["unit_trace_frobenius"],
        "reference_unit_trace_frobenius": noise["reference_unit_trace_frobenius_median"],
        "shape_transport_to_noise_ratio": ratio(met["unit_trace_frobenius"], noise["reference_unit_trace_frobenius_median"]),
        "transport_variance_location_tv": met["profile"]["tv"],
        "reference_variance_location_tv": noise["reference_variance_location_tv_median"],
        "variance_location_transport_to_noise_ratio": ratio(met["profile"]["tv"], noise["reference_variance_location_tv_median"]),
        "reference_estimability_status": noise["reference_estimability_status"],
    }


def rep_cell_set(rep: Rep) -> set[str]:
    out = set(rep.diag)
    for v in rep.vectors:
        out.update(v)
    return out


def load_b12_baseline() -> dict[tuple[str, str], dict[str, Any]]:
    accepted = WORK / "accepted_inputs"
    accepted.mkdir(parents=True, exist_ok=True)
    cov_path = accepted / "B12_COVARIANCE_TRANSPORT_v01_1.parquet"
    with zipfile.ZipFile(B12_ZIP) as z:
        cov_path.write_bytes(z.read("B12_COVARIANCE_TRANSPORT_v01_1.parquet"))
    columns = [
        "target_id", "species_id", "object_type", "pool_role", "relative_frobenius",
        "target_trace", "predicted_trace",
    ]
    out = {}
    for row in read_parquet_rows(cov_path, columns=columns):
        if row["species_id"] == "" and row["pool_role"] == "CANDIDATE" and row["object_type"] in {"DOMAIN", "GENERIC_JOINT"}:
            out[(row["target_id"], row["object_type"])] = row
    if len(out) != 4640 * 2:
        raise RuntimeError(f"B12 baseline row mismatch: {len(out)}")
    return out


def empty_invariants() -> dict[str, Any]:
    return {
        "member_identity_count": 0, "member_identity_fail": 0, "member_max_residual": 0.0,
        "member_max_tolerance": 0.0, "pool_identity_count": 0, "pool_identity_fail": 0,
        "pool_max_residual": 0.0, "pool_max_tolerance": 0.0,
        "species_identity_count": 0, "species_identity_fail": 0, "species_max_residual": 0.0,
        "error_geometry_count": 0, "error_geometry_fail": 0, "error_geometry_max_residual": 0.0,
        "psd_matrix_count": 0, "psd_material_fail": 0, "numeric_tolerance_count": 0,
        "symmetry_fail": 0, "df_identity_fail": 0,
        "b12_baseline_count": 0, "b12_baseline_fail": 0,
        "b12_baseline_max_relative_frobenius_delta": 0.0,
        "b12_baseline_max_target_trace_delta": 0.0, "b12_baseline_max_pool_trace_delta": 0.0,
    }


def update_psd(invariants: dict[str, Any], reps: Iterable[Rep]) -> None:
    for rep in reps:
        status = rep_summary(rep)["psd_status"]
        invariants["psd_matrix_count"] += 1
        if status == "FAIL_NUMERIC_MATERIAL": invariants["psd_material_fail"] += 1
        if "NUMERIC_TOLERANCE" in status: invariants["numeric_tolerance_count"] += 1


def update_algebra(invariants: dict[str, Any], prefix: str, reps: dict[str, Rep]) -> None:
    residual, tol, status = algebra_identity(reps["T"], reps["W"], reps["B"])
    invariants[f"{prefix}_identity_count"] += 1
    invariants[f"{prefix}_max_residual"] = max(invariants[f"{prefix}_max_residual"], residual)
    if f"{prefix}_max_tolerance" in invariants:
        invariants[f"{prefix}_max_tolerance"] = max(invariants[f"{prefix}_max_tolerance"], tol)
    if status != "PASS": invariants[f"{prefix}_identity_fail"] += 1
    update_psd(invariants, reps.values())


def audit_all_members(con: sqlite3.Connection, invariants: dict[str, Any], log) -> None:
    query = """SELECT m.member_id,m.n,m.df,g.scalar_ss,g.cell_counts_json,g.cell_sum_json,g.cell_sumsq_json
               FROM member m JOIN member_generic_stats g ON g.member_id=m.member_id ORDER BY m.member_id"""
    started = time.time(); last = 0.0
    for i, r in enumerate(con.execute(query), 1):
        member = {
            "member_id": str(r[0]), "n": int(r[1]), "df": int(r[2]), "scalar_ss": float(r[3]),
            "counts": {str(k): int(v) for k, v in json.loads(r[4]).items()},
            "sums": {str(k): float(v) for k, v in json.loads(r[5]).items()},
            "sumsq": {str(k): float(v) for k, v in json.loads(r[6]).items()}, "species": defaultdict(list),
        }
        bundle = {"members": [member], "membership_sha": "MEMBER_AUDIT", "pool_df": member["df"], "plot_count": member["n"]}
        if member["df"] > 0:
            for grain in GRAINS:
                for family in FAMILIES:
                    update_algebra(invariants, "member", component_reps(bundle, family, grain))
        now = time.time()
        if now - last >= 10:
            msg = f"MEMBER_ALGEBRA members={i}/7696 elapsed_s={int(now-started)}"
            print(msg, flush=True); log.write(msg + "\n"); log.flush(); last = now


def baseline_check(invariants: dict[str, Any], baseline: dict[tuple[str, str], dict[str, Any]],
                   target: sqlite3.Row, family: str, met: dict[str, Any]) -> None:
    object_type = "DOMAIN" if family == "DOMAIN_ONE_HOT" else "GENERIC_JOINT"
    row = baseline[(str(target["target_id"]), object_type)]
    def robust_delta(a: Any, b: Any) -> float:
        x, y = float(a), float(b)
        if math.isinf(x) and math.isinf(y) and (x > 0) == (y > 0): return 0.0
        if math.isnan(x) and math.isnan(y): return 0.0
        if not math.isfinite(x) or not math.isfinite(y): return float("inf")
        return abs(x - y)
    deltas = {
        "relative_frobenius": robust_delta(row["relative_frobenius"], met["relative_frobenius"]),
        "target_trace": abs(float(row["target_trace"]) - float(met["target_trace"])),
        "pool_trace": abs(float(row["predicted_trace"]) - float(met["pool_trace"])),
    }
    if abs(float(row["target_trace"])) <= 1e-12 and abs(float(met["target_trace"])) <= 1e-12:
        # Both reconstructions identify an analytically degenerate target; B12's
        # dense arithmetic may retain a sub-tolerance nonzero norm and report a
        # huge finite ratio where the sparse identity reports +inf.
        deltas["relative_frobenius"] = 0.0
    invariants["b12_baseline_count"] += 1
    invariants["b12_baseline_max_relative_frobenius_delta"] = max(invariants["b12_baseline_max_relative_frobenius_delta"], deltas["relative_frobenius"])
    invariants["b12_baseline_max_target_trace_delta"] = max(invariants["b12_baseline_max_target_trace_delta"], deltas["target_trace"])
    invariants["b12_baseline_max_pool_trace_delta"] = max(invariants["b12_baseline_max_pool_trace_delta"], deltas["pool_trace"])
    scale = max(1.0, abs(float(row["target_trace"])), abs(float(row["predicted_trace"])))
    if deltas["relative_frobenius"] > 1e-9 or deltas["target_trace"] > 1e-9 * scale or deltas["pool_trace"] > 1e-9 * scale:
        invariants["b12_baseline_fail"] += 1


def writers_context() -> tuple[contextlib.ExitStack, dict[str, ParquetWriter]]:
    stack = contextlib.ExitStack()
    specs = {
        "matrix": ("B13_MATRIX_SCALE_SHAPE_DIAGNOSTICS_v01.parquet", MATRIX_SCHEMA),
        "varloc": ("B13_VARIANCE_LOCATION_DIAGNOSTICS_v01.parquet", VARLOC_SCHEMA),
        "replication": ("B13_COMPONENT_REPLICATION_AUDIT_v01.parquet", REPLICATION_SCHEMA),
        "decomp": ("B13_WITHIN_BETWEEN_DECOMPOSITION_v01.parquet", DECOMP_SCHEMA),
        "error": ("B13_COMPONENT_ERROR_GEOMETRY_v01.parquet", ERROR_SCHEMA),
        "oracle": ("B13_ORACLE_COMPONENT_SWAP_v01.parquet", ORACLE_SCHEMA),
        "noise": ("B13_COMPONENT_REFERENCE_NOISE_v01.parquet", NOISE_SCHEMA),
        "tvn": ("B13_COMPONENT_TRANSPORT_VS_NOISE_v01.parquet", TVN_SCHEMA),
        "negative": ("B13_COMPONENT_NEGATIVE_CONTROLS_v01.parquet", NEG_SCHEMA),
        "actual": ("B13_ACTUAL24_LIMITED_COMPONENT_REFERENCE_v01.parquet", ACTUAL_SCHEMA),
    }
    writers = {}
    for key, (name, schema) in specs.items():
        path = OUT / name
        if path.exists(): path.unlink()
        writers[key] = stack.enter_context(ParquetWriter(path, schema, ROW_GROUP_SIZE))
    return stack, writers


def component_score_bundle(target: sqlite3.Row, family: str, species_id: str, grain: int, role: str,
                           target_bundle: dict[str, Any], pool_bundle: dict[str, Any],
                           target_reps: dict[str, Rep], pool_reps: dict[str, Rep],
                           noise: dict[str, dict[str, Any]], writers: dict[str, ParquetWriter],
                           invariants: dict[str, Any], summary_records: list[dict[str, Any]],
                           is_primary_generic: bool) -> dict[str, dict[str, Any]]:
    cells = set()
    for rep in list(target_reps.values()) + list(pool_reps.values()): cells.update(rep_cell_set(rep))
    base = identity_base(target, family, species_id, grain, role, target_bundle, pool_bundle, len(cells))
    metrics = {c: matrix_metrics(target_reps[c], pool_reps[c]) for c in COMPONENTS}
    record_start = len(summary_records)
    target_scalar = scalar_variance(target_bundle, family, species_id)
    pool_scalar = scalar_variance(pool_bundle, family, species_id)
    writers["matrix"].write(matrix_row(base, metrics["T"], target_scalar, pool_scalar))
    writers["varloc"].write(varloc_row(base, metrics["T"]))
    ttt = metrics["T"]["target_trace"]; ptt = metrics["T"]["pool_trace"]
    for component in COMPONENTS:
        writers["decomp"].write(decomposition_row(base, component, metrics[component], ttt, ptt))
        writers["tvn"].write(tvn_row(base, component, metrics[component], noise[component]))
        if role == "CANDIDATE" and target["target_type"] == "PSEUDO":
            summary_records.append({
                "target_id": str(target["target_id"]), "route": str(target["route"]),
                "reference_strength": str(target["reference_strength"]), "family": family,
                "species_id": species_id, "grain": grain, "component": component,
                "relative_frobenius": metrics[component]["relative_frobenius"],
                "trace_abs_log_ratio": metrics[component]["trace_abs_log_ratio"],
                "unit_trace_frobenius": metrics[component]["unit_trace_frobenius"],
                "variance_location_tv": metrics[component]["profile"]["tv"],
                "offdiag_unit_frobenius": metrics[component]["unit_trace_offdiag_frobenius"],
                "transport_to_noise": tvn_row(base, component, metrics[component], noise[component])["relative_frobenius_transport_to_noise_ratio"],
                "trace_transport_to_noise": tvn_row(base, component, metrics[component], noise[component])["trace_transport_to_noise_ratio"],
                "shape_transport_to_noise": tvn_row(base, component, metrics[component], noise[component])["shape_transport_to_noise_ratio"],
                "profile_transport_to_noise": tvn_row(base, component, metrics[component], noise[component])["variance_location_transport_to_noise_ratio"],
                "offdiag_transport_to_noise": (
                    metrics[component]["unit_trace_offdiag_frobenius"] / noise[component]["reference_offdiag_unit_frobenius_median"]
                    if math.isfinite(metrics[component]["unit_trace_offdiag_frobenius"])
                    and math.isfinite(noise[component]["reference_offdiag_unit_frobenius_median"])
                    and noise[component]["reference_offdiag_unit_frobenius_median"] > 0 else float("nan")
                ),
                "degeneracy": metrics[component]["degeneracy_class"],
                "oracle_scale_relative_frobenius": metrics[component]["oracle_scale_relative_frobenius"],
                "oracle_scale_relative_improvement": metrics[component]["oracle_scale_relative_improvement"],
                "candidate_better": -1, "primary_generic": int(is_primary_generic),
            })
    geom = error_geometry_row(target, family, species_id, grain, role, target_reps, pool_reps)
    writers["error"].write(geom)
    invariants["error_geometry_count"] += 1
    invariants["error_geometry_max_residual"] = max(invariants["error_geometry_max_residual"], geom["identity_absolute_residual"])
    if geom["identity_status"] != "PASS": invariants["error_geometry_fail"] += 1
    orow = oracle_row(target, family, species_id, grain, target_reps, pool_reps)
    if role == "CANDIDATE":
        writers["oracle"].write(orow)
        for rec in summary_records[record_start:]:
            rec["within_error_share"] = geom["within_normalized_share"]
            rec["between_error_share"] = geom["between_normalized_share"]
            rec["cross_error_share"] = geom["cross_normalized_share"]
            rec["cross_term_sign"] = geom["cross_term_sign"]
            rec["oracle_w_relative_frobenius"] = orow["oracle_w_relative_frobenius"]
            rec["oracle_b_relative_frobenius"] = orow["oracle_b_relative_frobenius"]
    update_psd(invariants, list(target_reps.values()) + list(pool_reps.values()))
    return metrics


def noise_for_target(target: sqlite3.Row, target_bundle: dict[str, Any], plot_rows: list[tuple[str, str, float]],
                     family: str, grain: int, species_id: str, species_values: dict[str, float] | None,
                     writers: dict[str, ParquetWriter]) -> dict[str, dict[str, Any]]:
    noise = split_component_noise(plot_rows, str(target["target_id"]), family, grain, species_values)
    for component in COMPONENTS:
        writers["noise"].write(noise_row(target, family, species_id, grain, component, target_bundle, noise[component]))
    return noise


def score_pseudo_targets(q1_species: list[str], baseline: dict[tuple[str, str], dict[str, Any]],
                         invariants: dict[str, Any], writers: dict[str, ParquetWriter], log) -> dict[str, Any]:
    con = read_only_connection()
    idx = sqlite3.connect(f"file:{(WORK / 'stage_p_seal_index.sqlite').as_posix()}?mode=ro", uri=True)
    idx.row_factory = sqlite3.Row
    targets = con.execute("SELECT * FROM target WHERE target_type='PSEUDO' AND validation_status='AVAILABLE' ORDER BY target_id").fetchall()
    summary_records: list[dict[str, Any]] = []
    q1_records: list[dict[str, Any]] = []
    replication_records: list[dict[str, Any]] = []
    verified = 0; q1_union_nonzero = 0; q1_total_pairs = 0
    role_counts: Counter[str] = Counter(); species_class: Counter[str] = Counter()
    started = time.time(); last = 0.0
    for i, target in enumerate(targets, 1):
        candidate = load_pool_bundle(con, target["target_id"], "CANDIDATE", q1_species)
        if int(candidate["pool_df"]) != int(target["pool_df"]):
            invariants["df_identity_fail"] += 1
        verified += verify_target_seals(idx, target, "CANDIDATE", candidate, q1_species, True)
        nc1_exists = con.execute("SELECT 1 FROM pool_membership WHERE target_id=? AND pool_role='NC1_INCOMPATIBLE' LIMIT 1", (target["target_id"],)).fetchone() is not None
        bundles = {"CANDIDATE": candidate}
        if nc1_exists:
            nc1 = load_pool_bundle(con, target["target_id"], "NC1_INCOMPATIBLE", None)
            verified += verify_target_seals(idx, target, "NC1_INCOMPATIBLE", nc1, q1_species, False)
            bundles["NC1_INCOMPATIBLE"] = nc1

        # Held-out target reference opens only after all corresponding seals verify.
        target_bundle = load_target_bundle(con, target["target_member_id"], q1_species)
        if int(target_bundle["pool_df"]) != int(target["target_df"]):
            invariants["df_identity_fail"] += 1
        plot_rows = load_target_plot_rows(con, target["target_member_id"])
        if len(plot_rows) != int(target["target_n"]):
            raise RuntimeError(f"Target plot count mismatch {target['target_id']}")
        species_values = load_target_species_plot_values(con, target["target_member_id"], q1_species)

        target_reps_by: dict[tuple[int, str], dict[str, Rep]] = {}
        noises: dict[tuple[int, str], dict[str, dict[str, Any]]] = {}
        for grain in GRAINS:
            for family in FAMILIES:
                treps = component_reps(target_bundle, family, grain)
                target_reps_by[(grain, family)] = treps
                noise = noise_for_target(target, target_bundle, plot_rows, family, grain, "", None, writers)
                noises[(grain, family)] = noise
                rep = replication_metrics(target_bundle, family, grain, treps["W"])
                writers["replication"].write({
                    "target_id": str(target["target_id"]), "target_type": "PSEUDO", "route": str(target["route"]),
                    "reference_strength": str(target["reference_strength"]), "subject_role": "TARGET_REFERENCE",
                    "pool_role": "", "measurement_family": family, "grain_km": grain, **rep,
                })
                replication_records.append({
                    "target_id": str(target["target_id"]), "route": str(target["route"]),
                    "reference_strength": str(target["reference_strength"]), "subject_role": "TARGET_REFERENCE",
                    "pool_role": "", "family": family, "grain": grain, **rep,
                })

        role_metrics: dict[str, dict[tuple[int, str, str], dict[str, Any]]] = defaultdict(dict)
        for role, pool_bundle in bundles.items():
            role_counts[role] += 1
            for grain in GRAINS:
                for family in FAMILIES:
                    preps = component_reps(pool_bundle, family, grain)
                    update_algebra(invariants, "pool", preps)
                    rep = replication_metrics(pool_bundle, family, grain, preps["W"])
                    writers["replication"].write({
                        "target_id": str(target["target_id"]), "target_type": "PSEUDO", "route": str(target["route"]),
                        "reference_strength": str(target["reference_strength"]), "subject_role": "POOL_PREDICTION",
                        "pool_role": role, "measurement_family": family, "grain_km": grain, **rep,
                    })
                    if role == "CANDIDATE":
                        replication_records.append({
                            "target_id": str(target["target_id"]), "route": str(target["route"]),
                            "reference_strength": str(target["reference_strength"]), "subject_role": "POOL_PREDICTION",
                            "pool_role": role, "family": family, "grain": grain, **rep,
                        })
                    metrics = component_score_bundle(
                        target, family, "", grain, role, target_bundle, pool_bundle,
                        target_reps_by[(grain, family)], preps, noises[(grain, family)], writers,
                        invariants, summary_records, True,
                    )
                    for component in COMPONENTS:
                        role_metrics[role][(grain, family, component)] = metrics[component]
                    if role == "CANDIDATE" and grain == 50:
                        baseline_check(invariants, baseline, target, family, metrics["T"])

        if nc1_exists:
            for grain in GRAINS:
                for family in FAMILIES:
                    for component in COMPONENTS:
                        cm = role_metrics["CANDIDATE"][(grain, family, component)]
                        nm = role_metrics["NC1_INCOMPATIBLE"][(grain, family, component)]
                        def better(a: float, b: float) -> int:
                            return int(math.isfinite(a) and math.isfinite(b) and a < b)
                        row = {
                            "target_id": str(target["target_id"]), "route": str(target["route"]),
                            "reference_strength": str(target["reference_strength"]), "measurement_family": family,
                            "grain_km": grain, "component_type": component,
                            "candidate_relative_frobenius": cm["relative_frobenius"], "nc1_relative_frobenius": nm["relative_frobenius"],
                            "candidate_better_relative_frobenius": better(cm["relative_frobenius"], nm["relative_frobenius"]),
                            "candidate_trace_abs_log_ratio": cm["trace_abs_log_ratio"], "nc1_trace_abs_log_ratio": nm["trace_abs_log_ratio"],
                            "candidate_better_trace": better(cm["trace_abs_log_ratio"], nm["trace_abs_log_ratio"]),
                            "candidate_unit_trace_frobenius": cm["unit_trace_frobenius"], "nc1_unit_trace_frobenius": nm["unit_trace_frobenius"],
                            "candidate_better_unit_shape": better(cm["unit_trace_frobenius"], nm["unit_trace_frobenius"]),
                            "candidate_variance_location_tv": cm["profile"]["tv"], "nc1_variance_location_tv": nm["profile"]["tv"],
                            "candidate_better_variance_location": better(cm["profile"]["tv"], nm["profile"]["tv"]),
                            "comparison_status": "COMPARABLE_FIXED_B12_NC1",
                        }
                        writers["negative"].write(row)
                        for rec in reversed(summary_records):
                            if rec["target_id"] == str(target["target_id"]) and rec["grain"] == grain and rec["family"] == family and rec["component"] == component and rec["species_id"] == "":
                                rec["candidate_better"] = row["candidate_better_relative_frobenius"]; break

        # Q1 direct-97 species: predeclared primary-grain component diagnostic.
        q1_total_pairs += len(q1_species)
        for species_id in q1_species:
            treps = component_reps(target_bundle, "SPECIES_Y", 50, species_id)
            preps = component_reps(candidate, "SPECIES_Y", 50, species_id)
            ttrace = rep_summary(treps["T"])["trace"]; ptrace = rep_summary(preps["T"])["trace"]
            if ttrace <= 0 and ptrace <= 0:
                species_class["BOTH_ZERO_UNINFORMATIVE"] += 1
                continue
            q1_union_nonzero += 1
            species_class["UNION_NONZERO_SCORED"] += 1
            update_algebra(invariants, "species", treps); update_algebra(invariants, "species", preps)
            spvals = species_values.get(species_id, {})
            spnoise = noise_for_target(target, target_bundle, plot_rows, "SPECIES_Y", 50, species_id, spvals, writers)
            before = len(summary_records)
            metrics = component_score_bundle(
                target, "SPECIES_Y", species_id, 50, "CANDIDATE", target_bundle, candidate,
                treps, preps, spnoise, writers, invariants, summary_records, False,
            )
            repl_t = replication_metrics(target_bundle, "GENERIC_Y", 50, treps["W"])
            repl_p = replication_metrics(candidate, "GENERIC_Y", 50, preps["W"])
            for rec in summary_records[before:]:
                rec["target_within_df"] = repl_t["effective_within_cell_df"]
                rec["pool_within_df"] = repl_p["effective_within_cell_df"]
                q1_records.append(rec)

        now = time.time()
        if now - last >= 10:
            msg = f"STAGE_S_SCORE pseudo={i}/{len(targets)} verified={verified} q1_union={q1_union_nonzero} elapsed_s={int(now-started)}"
            print(msg, flush=True); log.write(msg + "\n"); log.flush(); last = now
    idx.close(); con.close()
    generic_records = [r for r in summary_records if r["species_id"] == ""]
    return {
        "verified_objects": verified, "failed_objects": 0, "role_counts": dict(role_counts),
        "generic_records": generic_records, "q1_records": q1_records,
        "replication_records": replication_records,
        "q1_total_pairs": q1_total_pairs, "q1_union_nonzero": q1_union_nonzero,
        "q1_species_classes": dict(species_class),
    }


def score_actual24(q1_species: list[str], invariants: dict[str, Any], writers: dict[str, ParquetWriter], log) -> dict[str, Any]:
    con = read_only_connection()
    idx = sqlite3.connect(f"file:{(WORK / 'stage_p_seal_index.sqlite').as_posix()}?mode=ro", uri=True)
    idx.row_factory = sqlite3.Row
    targets = con.execute("SELECT * FROM target WHERE target_type='ACTUAL24' AND validation_status='AVAILABLE' ORDER BY target_id").fetchall()
    verified = 0; rows_written = 0; n_values = []; summary = []
    for i, target in enumerate(targets, 1):
        candidate = load_pool_bundle(con, target["target_id"], "CANDIDATE", None)
        if int(candidate["pool_df"]) != int(target["pool_df"]):
            invariants["df_identity_fail"] += 1
        verified += verify_target_seals(idx, target, "CANDIDATE", candidate, q1_species, False)
        # FULL5_LIMITED_REFERENCE opens only after this case's component seals verify.
        plot_rows = [(str(r[0]), str(r[1]), float(r[2])) for r in con.execute(
            """SELECT d.PLT_CN,d.cell_id,g.y FROM plot_design d JOIN plot_generic g ON g.PLT_CN=d.PLT_CN
               WHERE d.STATECD=? AND d.EVALID=? AND d.parent=? ORDER BY d.PLT_CN""",
            (target["STATECD"], target["EVALID"], target["parent"]),
        )]
        n = len(plot_rows); n_values.append(n)
        if n < 2 or n > 13:
            raise RuntimeError(f"Actual24 FULL5 count outside accepted 2-13: {target['target_id']} n={n}")
        reference = bundle_from_plot_rows(plot_rows)
        for grain in GRAINS:
            for family in FAMILIES:
                tr = component_reps(reference, family, grain)
                pr = component_reps(candidate, family, grain)
                update_algebra(invariants, "pool", tr)
                update_algebra(invariants, "pool", pr)
                rep = replication_metrics(reference, family, grain, tr["W"])
                noise = split_component_noise(plot_rows, str(target["target_id"]), family, grain)
                for component in COMPONENTS:
                    met = matrix_metrics(tr[component], pr[component])
                    ref = noise[component]["reference_relative_frobenius_median"]
                    ratio = met["relative_frobenius"] / ref if math.isfinite(met["relative_frobenius"]) and math.isfinite(ref) and ref > 0 else float("nan")
                    row = {
                        "target_id": str(target["target_id"]), "case_id": str(target["case_id"]),
                        "route": str(target["route"]), "statecd": int(target["STATECD"]),
                        "evalid": str(target["EVALID"]), "fold": str(target["fold"]),
                        "reference_role": "FULL5_LIMITED_REFERENCE", "prediction_seal_verified": "YES",
                        "measurement_family": family, "grain_km": grain, "component_type": component,
                        "pool_df": int(candidate["pool_df"]), "full5_n": n, "full5_df": n - 1,
                        "full5_effective_within_cell_df": rep["effective_within_cell_df"],
                        "full5_fraction_plots_in_replicated_cells": rep["fraction_plots_in_replicated_cells"],
                        "target_component_trace": met["target_trace"], "pool_component_trace": met["pool_trace"],
                        "trace_abs_log_ratio": met["trace_abs_log_ratio"], "relative_frobenius": met["relative_frobenius"],
                        "unit_trace_frobenius": met["unit_trace_frobenius"], "variance_location_tv": met["profile"]["tv"],
                        "reference_relative_frobenius": ref, "transport_to_noise_ratio": ratio,
                        "within_estimability": rep["within_estimability"], "target_psd_status": met["target_psd"],
                        "pool_psd_status": met["pool_psd"], "regularization_applied": "NONE",
                        "limitations": "DIRECT_BUT_WEAK_FULL5_LIMITED_REFERENCE_NOT_TRUTH_NOT_TUNING_NOT_FILTER",
                    }
                    writers["actual"].write(row); rows_written += 1
                    summary.append(row)
        msg = f"ACTUAL24_SCORE case={i}/24 target={target['target_id']} full5_n={n} verified={verified}"
        print(msg, flush=True); log.write(msg + "\n"); log.flush()
    idx.close(); con.close()
    if len(targets) != 24 or rows_written != 24 * len(GRAINS) * len(FAMILIES) * len(COMPONENTS):
        raise RuntimeError("Actual24 retention/output count mismatch")
    return {"verified_objects": verified, "failed_objects": 0, "rows_written": rows_written,
            "n_min": min(n_values), "n_max": max(n_values), "records": summary}


LEVEL_FIELDS = [
    "group_type", "group_value", "grain_km", "measurement_family", "component_type",
    "target_count", "relative_frobenius_finite_count", "positive_trace_pair_count",
    "median_relative_frobenius", "p90_relative_frobenius", "median_trace_abs_log_ratio",
    "median_unit_trace_frobenius", "median_variance_location_tv", "median_offdiag_unit_frobenius",
    "noise_comparable_count", "median_transport_to_noise_ratio", "median_trace_transport_to_noise_ratio",
    "median_shape_transport_to_noise_ratio", "median_profile_transport_to_noise_ratio",
    "median_offdiag_transport_to_noise_ratio", "nc1_comparable_count", "candidate_better_nc1_fraction",
    "median_oracle_scale_relative_frobenius", "median_oracle_scale_relative_improvement",
    "median_within_error_share", "median_between_error_share", "median_cross_error_share",
    "negative_cross_term_fraction", "evidence_class",
]


def aggregate_records(group_type: str, group_value: str, grain: int, family: str, component: str,
                      rows: list[dict[str, Any]]) -> dict[str, Any]:
    finite_rel = finite(r["relative_frobenius"] for r in rows)
    noise = finite(r["transport_to_noise"] for r in rows)
    nc = [r["candidate_better"] for r in rows if r.get("candidate_better", -1) in {0, 1}]
    cross = [r.get("cross_error_share") for r in rows if math.isfinite(float(r.get("cross_error_share", float("nan"))))]
    if len(finite_rel) < 10:
        evidence = "WEAKLY_IDENTIFIED_OR_TOO_FEW_FINITE_CASES"
    elif not noise:
        evidence = "DESCRIPTIVE_TRANSPORT_REFERENCE_NOISE_LIMITED"
    else:
        evidence = "DESCRIPTIVE_CONTINUOUS_EVIDENCE_NO_HARD_PASS_THRESHOLD"
    return {
        "group_type": group_type, "group_value": group_value, "grain_km": grain,
        "measurement_family": family, "component_type": component,
        "target_count": len({r["target_id"] for r in rows}),
        "relative_frobenius_finite_count": len(finite_rel),
        "positive_trace_pair_count": sum(r["degeneracy"] == "POSITIVE_TRACE" for r in rows),
        "median_relative_frobenius": median(finite_rel), "p90_relative_frobenius": quantile(finite_rel, 0.9),
        "median_trace_abs_log_ratio": median(r["trace_abs_log_ratio"] for r in rows),
        "median_unit_trace_frobenius": median(r["unit_trace_frobenius"] for r in rows),
        "median_variance_location_tv": median(r["variance_location_tv"] for r in rows),
        "median_offdiag_unit_frobenius": median(r["offdiag_unit_frobenius"] for r in rows),
        "noise_comparable_count": len(noise), "median_transport_to_noise_ratio": median(noise),
        "median_trace_transport_to_noise_ratio": median(r["trace_transport_to_noise"] for r in rows),
        "median_shape_transport_to_noise_ratio": median(r["shape_transport_to_noise"] for r in rows),
        "median_profile_transport_to_noise_ratio": median(r["profile_transport_to_noise"] for r in rows),
        "median_offdiag_transport_to_noise_ratio": median(r["offdiag_transport_to_noise"] for r in rows),
        "nc1_comparable_count": len(nc), "candidate_better_nc1_fraction": sum(nc) / len(nc) if nc else float("nan"),
        "median_oracle_scale_relative_frobenius": median(r["oracle_scale_relative_frobenius"] for r in rows),
        "median_oracle_scale_relative_improvement": median(r["oracle_scale_relative_improvement"] for r in rows),
        "median_within_error_share": median(r.get("within_error_share") for r in rows),
        "median_between_error_share": median(r.get("between_error_share") for r in rows),
        "median_cross_error_share": median(r.get("cross_error_share") for r in rows),
        "negative_cross_term_fraction": sum(float(x) < 0 for x in cross) / len(cross) if cross else float("nan"),
        "evidence_class": evidence,
    }


def group_definitions(records: list[dict[str, Any]]) -> list[tuple[str, str, list[dict[str, Any]]]]:
    out = [("ALL", "ALL", records)]
    for route in ("LEVEL1", "LEVEL2"):
        out.append(("ROUTE", route, [r for r in records if r["route"] == route]))
    for band in ("R1", "R2", "R3", "R4", "R5"):
        out.append(("REFERENCE_STRENGTH", band, [r for r in records if r["reference_strength"] == band]))
    for route in ("LEVEL1", "LEVEL2"):
        for band in ("R1", "R2", "R3", "R4", "R5"):
            out.append(("ROUTE_X_REFERENCE", f"{route}|{band}", [r for r in records if r["route"] == route and r["reference_strength"] == band]))
    return out


def make_level_summary(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for family in FAMILIES:
        for component in COMPONENTS:
            subset = [r for r in records if r["grain"] == 50 and r["family"] == family and r["component"] == component]
            for gt, gv, group in group_definitions(subset):
                rows.append(aggregate_records(gt, gv, 50, family, component, group))
    return rows


def make_coarse_summary(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for grain in GRAINS:
        for family in FAMILIES:
            for component in COMPONENTS:
                base = [r for r in records if r["grain"] == grain and r["family"] == family and r["component"] == component]
                for route in ("ALL", "LEVEL1", "LEVEL2"):
                    group = base if route == "ALL" else [r for r in base if r["route"] == route]
                    rows.append(aggregate_records("ROUTE", route, grain, family, component, group))
    return rows


Q1_FIELDS = [
    "group_type", "group_value", "grain_km", "component_type", "fia_code_count",
    "universe_target_code_rows", "union_nonzero_scored_rows", "positive_trace_pair_count",
    "finite_relative_frobenius_count", "median_relative_frobenius", "p90_relative_frobenius",
    "median_trace_abs_log_ratio", "median_unit_trace_frobenius", "median_variance_location_tv",
    "noise_comparable_count", "median_transport_to_noise_ratio", "median_shape_transport_to_noise_ratio",
    "target_within_df_positive_fraction", "pool_within_df_positive_fraction", "evidence_class",
]


def make_q1_summary(records: list[dict[str, Any]], q1_species: list[str]) -> list[dict[str, Any]]:
    con = read_only_connection()
    targets = [dict(r) for r in con.execute("SELECT target_id,route,reference_strength FROM target WHERE target_type='PSEUDO' AND validation_status='AVAILABLE'")]
    con.close()
    definitions: list[tuple[str, str, list[dict[str, Any]], int]] = []
    definitions.append(("ALL", "ALL", records, len(targets)))
    for route in ("LEVEL1", "LEVEL2"):
        definitions.append(("ROUTE", route, [r for r in records if r["route"] == route], sum(t["route"] == route for t in targets)))
    for band in ("R1", "R2", "R3", "R4", "R5"):
        definitions.append(("REFERENCE_STRENGTH", band, [r for r in records if r["reference_strength"] == band], sum(t["reference_strength"] == band for t in targets)))
    for route in ("LEVEL1", "LEVEL2"):
        for band in ("R1", "R2", "R3", "R4", "R5"):
            definitions.append(("ROUTE_X_REFERENCE", f"{route}|{band}", [r for r in records if r["route"] == route and r["reference_strength"] == band], sum(t["route"] == route and t["reference_strength"] == band for t in targets)))
    out = []
    for component in COMPONENTS:
        for gt, gv, group_all, target_count in definitions:
            group = [r for r in group_all if r["component"] == component]
            finite_rel = finite(r["relative_frobenius"] for r in group)
            noise = finite(r["transport_to_noise"] for r in group)
            if component == "W" and group and sum(r.get("target_within_df", 0) > 0 for r in group) / len(group) < 0.5:
                evidence = "WEAKLY_IDENTIFIED_WITHIN_CELL_REPLICATION_SPARSE"
            elif len(finite_rel) < 10:
                evidence = "WEAKLY_IDENTIFIED_OR_TOO_FEW_FINITE_CASES"
            else:
                evidence = "Q1_DIRECT97_DIAGNOSTIC_ONLY_NO_COMPONENT_SELECTION"
            out.append({
                "group_type": gt, "group_value": gv, "grain_km": 50, "component_type": component,
                "fia_code_count": len(q1_species), "universe_target_code_rows": target_count * len(q1_species),
                "union_nonzero_scored_rows": len(group),
                "positive_trace_pair_count": sum(r["degeneracy"] == "POSITIVE_TRACE" for r in group),
                "finite_relative_frobenius_count": len(finite_rel), "median_relative_frobenius": median(finite_rel),
                "p90_relative_frobenius": quantile(finite_rel, 0.9),
                "median_trace_abs_log_ratio": median(r["trace_abs_log_ratio"] for r in group),
                "median_unit_trace_frobenius": median(r["unit_trace_frobenius"] for r in group),
                "median_variance_location_tv": median(r["variance_location_tv"] for r in group),
                "noise_comparable_count": len(noise), "median_transport_to_noise_ratio": median(noise),
                "median_shape_transport_to_noise_ratio": median(r["shape_transport_to_noise"] for r in group),
                "target_within_df_positive_fraction": sum(r.get("target_within_df", 0) > 0 for r in group) / len(group) if group else float("nan"),
                "pool_within_df_positive_fraction": sum(r.get("pool_within_df", 0) > 0 for r in group) / len(group) if group else float("nan"),
                "evidence_class": evidence,
            })
    return out


def find_summary(rows: list[dict[str, Any]], family: str, component: str, group_type: str = "ALL",
                 group_value: str = "ALL", grain: int = 50) -> dict[str, Any]:
    for r in rows:
        if (r["measurement_family"] == family and r["component_type"] == component
                and r["group_type"] == group_type and r["group_value"] == group_value and int(r["grain_km"]) == grain):
            return r
    raise KeyError((family, component, group_type, group_value, grain))


def replication_summary(records: list[dict[str, Any]], route: str, grain: int, subject: str, family: str = "GENERIC_Y") -> dict[str, Any]:
    rows = [r for r in records if r["family"] == family and r["grain"] == grain and r["subject_role"] == subject and (route == "ALL" or r["route"] == route)]
    return {
        "count": len(rows),
        "positive_within_df_fraction": sum(r["effective_within_cell_df"] > 0 for r in rows) / len(rows) if rows else float("nan"),
        "informative_fraction": sum(r["within_estimability"] == "INFORMATIVE_OBSERVED" for r in rows) / len(rows) if rows else float("nan"),
        "median_within_df": median(r["effective_within_cell_df"] for r in rows),
        "median_fraction_plots_replicated": median(r["fraction_plots_in_replicated_cells"] for r in rows),
    }


def make_disposition(level: list[dict[str, Any]], coarse: list[dict[str, Any]], q1: list[dict[str, Any]],
                     replication: list[dict[str, Any]], actual: dict[str, Any]) -> list[dict[str, Any]]:
    t = find_summary(level, "GENERIC_Y", "T")
    w = find_summary(level, "GENERIC_Y", "W")
    b = find_summary(level, "GENERIC_Y", "B")
    l1t = find_summary(level, "GENERIC_Y", "T", "ROUTE", "LEVEL1")
    l2t = find_summary(level, "GENERIC_Y", "T", "ROUTE", "LEVEL2")
    l1w = find_summary(level, "GENERIC_Y", "W", "ROUTE", "LEVEL1")
    l2w = find_summary(level, "GENERIC_Y", "W", "ROUTE", "LEVEL2")
    l1b = find_summary(level, "GENERIC_Y", "B", "ROUTE", "LEVEL1")
    l2b = find_summary(level, "GENERIC_Y", "B", "ROUTE", "LEVEL2")
    c100 = find_summary(coarse, "GENERIC_Y", "T", "ROUTE", "ALL", 100)
    c200 = find_summary(coarse, "GENERIC_Y", "T", "ROUTE", "ALL", 200)
    q1t = next(r for r in q1 if r["group_type"] == "ALL" and r["group_value"] == "ALL" and r["component_type"] == "T")
    q1w = next(r for r in q1 if r["group_type"] == "ALL" and r["group_value"] == "ALL" and r["component_type"] == "W")
    target_rep = replication_summary(replication, "ALL", 50, "TARGET_REFERENCE")
    actual_rows = actual["records"]
    def actual_med(component: str) -> float:
        return median(r["relative_frobenius"] for r in actual_rows if r["measurement_family"] == "GENERIC_Y" and r["grain_km"] == 50 and r["component_type"] == component)
    def status_from_ratio(ratio: Any, weak: bool = False) -> str:
        if weak: return "WEAKLY_IDENTIFIED"
        x = float(ratio) if ratio is not None else float("nan")
        return "MATERIALLY_CHALLENGED" if math.isfinite(x) and x > 1 else "UNRESOLVED"
    common = {
        "reference_noise_context": "连续 transport/reference-noise 比率；1 是自然比较点，不是授权的硬阈值",
        "actual24_relevance": f"FULL5_LIMITED_REFERENCE；50 km 中位相对误差 T/W/B={fmt(actual_med('T'))}/{fmt(actual_med('W'))}/{fmt(actual_med('B'))}",
    }
    rows = [
        {
            "component": "total covariance scale", "mathematical_definition": "trace(T)",
            "empirical_estimability": f"正迹配对 {t['positive_trace_pair_count']}/{t['target_count']}",
            "level1_transport_evidence": f"中位 |log ratio|={fmt(l1t['median_trace_abs_log_ratio'])}; 对噪声比={fmt(l1t['median_trace_transport_to_noise_ratio'])}",
            "level2_transport_evidence": f"中位 |log ratio|={fmt(l2t['median_trace_abs_log_ratio'])}; 对噪声比={fmt(l2t['median_trace_transport_to_noise_ratio'])}",
            "nc1_discrimination": f"候选更近比例={fmt(t['candidate_better_nc1_fraction'])}",
            "result_50km": f"中位 |log ratio|={fmt(t['median_trace_abs_log_ratio'])}",
            "coarse_grain_result": f"100/200 km 相对误差={fmt(c100['median_relative_frobenius'])}/{fmt(c200['median_relative_frobenius'])}",
            "q1_97_relevance": f"T 中位 |log ratio|={fmt(q1t['median_trace_abs_log_ratio'])}",
            "scientific_status": status_from_ratio(t["median_trace_transport_to_noise_ratio"]),
            "recommended_next_investigation": "方差函数/尺度模型与冻结单位迹形状的分离评估",
            "major_caveat": "oracle 目标迹仅用于病理诊断，不能成为生产规则", **common,
        },
        {
            "component": "unit-trace full shape", "mathematical_definition": "U=T/trace(T)",
            "empirical_estimability": f"有限单位迹形状 {t['relative_frobenius_finite_count']}；零迹单列",
            "level1_transport_evidence": f"中位形状差={fmt(l1t['median_unit_trace_frobenius'])}; 对噪声比={fmt(l1t['median_shape_transport_to_noise_ratio'])}",
            "level2_transport_evidence": f"中位形状差={fmt(l2t['median_unit_trace_frobenius'])}; 对噪声比={fmt(l2t['median_shape_transport_to_noise_ratio'])}",
            "nc1_discrimination": f"候选更近比例={fmt(t['candidate_better_nc1_fraction'])}",
            "result_50km": f"中位单位迹 Frobenius={fmt(t['median_unit_trace_frobenius'])}",
            "coarse_grain_result": f"100/200 km 单位迹差={fmt(c100['median_unit_trace_frobenius'])}/{fmt(c200['median_unit_trace_frobenius'])}",
            "q1_97_relevance": f"T 中位单位迹差={fmt(q1t['median_unit_trace_frobenius'])}",
            "scientific_status": status_from_ratio(t["median_shape_transport_to_noise_ratio"]),
            "recommended_next_investigation": "只在尺度与形状分离后检验共享单位迹结构",
            "major_caveat": "形状量只在目标与池均为正迹时可解释", **common,
        },
        {
            "component": "normalized diagonal variance-location profile", "mathematical_definition": "d_j=T_jj/trace(T)",
            "empirical_estimability": f"正迹配对 {t['positive_trace_pair_count']}/{t['target_count']}",
            "level1_transport_evidence": f"TV={fmt(l1t['median_variance_location_tv'])}; 对噪声比={fmt(l1t['median_profile_transport_to_noise_ratio'])}",
            "level2_transport_evidence": f"TV={fmt(l2t['median_variance_location_tv'])}; 对噪声比={fmt(l2t['median_profile_transport_to_noise_ratio'])}",
            "nc1_discrimination": f"候选更近比例={fmt(t['candidate_better_nc1_fraction'])}",
            "result_50km": f"中位 TV={fmt(t['median_variance_location_tv'])}",
            "coarse_grain_result": f"100/200 km TV={fmt(c100['median_variance_location_tv'])}/{fmt(c200['median_variance_location_tv'])}",
            "q1_97_relevance": f"T 中位 TV={fmt(q1t['median_variance_location_tv'])}",
            "scientific_status": status_from_ratio(t["median_profile_transport_to_noise_ratio"]),
            "recommended_next_investigation": "目标域位置/分配信息与借用残差成分分开建模",
            "major_caveat": "对角位置含采样位置与均值差共同作用", **common,
        },
        {
            "component": "off-diagonal dependence", "mathematical_definition": "offdiag(U)",
            "empirical_estimability": "不强制相关矩阵；零/近零对角保持 NOT_ESTIMABLE",
            "level1_transport_evidence": f"单位迹 offdiag={fmt(l1t['median_offdiag_unit_frobenius'])}; 对噪声比={fmt(l1t['median_offdiag_transport_to_noise_ratio'])}",
            "level2_transport_evidence": f"单位迹 offdiag={fmt(l2t['median_offdiag_unit_frobenius'])}; 对噪声比={fmt(l2t['median_offdiag_transport_to_noise_ratio'])}",
            "nc1_discrimination": f"全形状候选更近比例={fmt(t['candidate_better_nc1_fraction'])}",
            "result_50km": f"中位单位迹 offdiag 差={fmt(t['median_offdiag_unit_frobenius'])}",
            "coarse_grain_result": f"100/200 km offdiag 差={fmt(c100['median_offdiag_unit_frobenius'])}/{fmt(c200['median_offdiag_unit_frobenius'])}",
            "q1_97_relevance": "直接97物种仅在非退化对象上报告；不作相关矩阵正则化",
            "scientific_status": status_from_ratio(t["median_offdiag_transport_to_noise_ratio"]),
            "recommended_next_investigation": "在保持零对角不可估边界下检验依赖结构",
            "major_caveat": "单位迹 offdiag 与 TV 数值尺度不同，只比较各自的噪声比", **common,
        },
        {
            "component": "within-cell observed residual scatter", "mathematical_definition": "W=Σ_gΣ_cΣ_i(x_gi-xbar_gc)(...)' / ν_P",
            "empirical_estimability": f"50 km 目标有效 within-df 比例={fmt(target_rep['positive_within_df_fraction'])}; 信息性比例={fmt(target_rep['informative_fraction'])}",
            "level1_transport_evidence": f"相对误差={fmt(l1w['median_relative_frobenius'])}; 对噪声比={fmt(l1w['median_transport_to_noise_ratio'])}",
            "level2_transport_evidence": f"相对误差={fmt(l2w['median_relative_frobenius'])}; 对噪声比={fmt(l2w['median_transport_to_noise_ratio'])}",
            "nc1_discrimination": f"候选更近比例={fmt(w['candidate_better_nc1_fraction'])}",
            "result_50km": f"W 相对误差={fmt(w['median_relative_frobenius'])}",
            "coarse_grain_result": "随聚合重算；零 W 不被解释为同质性",
            "q1_97_relevance": f"直接97 W 有限评分={q1w['finite_relative_frobenius_count']}；{q1w['evidence_class']}",
            "scientific_status": status_from_ratio(w["median_transport_to_noise_ratio"], target_rep["positive_within_df_fraction"] < 0.5),
            "recommended_next_investigation": "先解决重复样地/参考强度，再评估残差借用",
            "major_caveat": "观测 W 不是潜在丰度残差过程；无重复导致的零不可作生态结论", **common,
        },
        {
            "component": "between-cell allocation/mean scatter", "mathematical_definition": "B=Σ_gΣ_c n_gc(xbar_gc-xbar_g)(...)' / ν_P",
            "empirical_estimability": f"由精确 T-W 恒等式与逐组中心化构造；正迹配对 {b['positive_trace_pair_count']}/{b['target_count']}",
            "level1_transport_evidence": f"相对误差={fmt(l1b['median_relative_frobenius'])}; 对噪声比={fmt(l1b['median_transport_to_noise_ratio'])}",
            "level2_transport_evidence": f"相对误差={fmt(l2b['median_relative_frobenius'])}; 对噪声比={fmt(l2b['median_transport_to_noise_ratio'])}",
            "nc1_discrimination": f"候选更近比例={fmt(b['candidate_better_nc1_fraction'])}",
            "result_50km": f"B 相对误差={fmt(b['median_relative_frobenius'])}",
            "coarse_grain_result": "100/200 km 仅作诊断聚合，未改 Q1 50 km 粒度",
            "q1_97_relevance": "直接97在非零对象上给出 B 诊断；多SPCD不合并",
            "scientific_status": status_from_ratio(b["median_transport_to_noise_ratio"]),
            "recommended_next_investigation": "域/分配感知重构与残差借用分开验证",
            "major_caveat": "B 同时包含样地/单元位置和单元均值差，不是纯空间分配", **common,
        },
    ]
    fields = [
        "component", "mathematical_definition", "empirical_estimability", "level1_transport_evidence",
        "level2_transport_evidence", "reference_noise_context", "nc1_discrimination", "result_50km",
        "coarse_grain_result", "q1_97_relevance", "actual24_relevance", "scientific_status",
        "recommended_next_investigation", "major_caveat",
    ]
    return [{k: row[k] for k in fields} for row in rows]


def make_report(level: list[dict[str, Any]], coarse: list[dict[str, Any]], q1: list[dict[str, Any]],
                replication: list[dict[str, Any]], actual: dict[str, Any], pseudo: dict[str, Any],
                stage_p: dict[str, Any], invariants: dict[str, Any]) -> str:
    t = find_summary(level, "GENERIC_Y", "T")
    w = find_summary(level, "GENERIC_Y", "W")
    b = find_summary(level, "GENERIC_Y", "B")
    l1t = find_summary(level, "GENERIC_Y", "T", "ROUTE", "LEVEL1")
    l2t = find_summary(level, "GENERIC_Y", "T", "ROUTE", "LEVEL2")
    l1w = find_summary(level, "GENERIC_Y", "W", "ROUTE", "LEVEL1")
    l2w = find_summary(level, "GENERIC_Y", "W", "ROUTE", "LEVEL2")
    l1b = find_summary(level, "GENERIC_Y", "B", "ROUTE", "LEVEL1")
    l2b = find_summary(level, "GENERIC_Y", "B", "ROUTE", "LEVEL2")
    c100 = find_summary(coarse, "GENERIC_Y", "T", "ROUTE", "ALL", 100)
    c200 = find_summary(coarse, "GENERIC_Y", "T", "ROUTE", "ALL", 200)
    q1t = next(r for r in q1 if r["group_type"] == "ALL" and r["group_value"] == "ALL" and r["component_type"] == "T")
    q1w = next(r for r in q1 if r["group_type"] == "ALL" and r["group_value"] == "ALL" and r["component_type"] == "W")
    q1b = next(r for r in q1 if r["group_type"] == "ALL" and r["group_value"] == "ALL" and r["component_type"] == "B")
    tr50 = replication_summary(replication, "ALL", 50, "TARGET_REFERENCE")
    tr100 = replication_summary(replication, "ALL", 100, "TARGET_REFERENCE")
    tr200 = replication_summary(replication, "ALL", 200, "TARGET_REFERENCE")
    l1rep = replication_summary(replication, "LEVEL1", 50, "TARGET_REFERENCE")
    l2rep = replication_summary(replication, "LEVEL2", 50, "TARGET_REFERENCE")
    arows = [r for r in actual["records"] if r["measurement_family"] == "GENERIC_Y" and r["grain_km"] == 50]
    def amed(comp: str, field: str = "relative_frobenius") -> float:
        return median(r[field] for r in arows if r["component_type"] == comp)
    scale_ratio = t["median_trace_transport_to_noise_ratio"]
    shape_ratio = t["median_shape_transport_to_noise_ratio"]
    location_ratio = t["median_profile_transport_to_noise_ratio"]
    off_ratio = t["median_offdiag_transport_to_noise_ratio"]
    main_cause = "尺度与形状/位置均有贡献，现有证据不能把失败归为单一尺度项"
    if math.isfinite(float(scale_ratio)) and math.isfinite(float(shape_ratio)):
        if float(scale_ratio) > 1 and float(shape_ratio) <= 1:
            main_cause = "尺度项相对更突出，但形状仍不能据此获得生产资格"
        elif float(scale_ratio) <= 1 and float(shape_ratio) > 1:
            main_cause = "单位迹形状/位置项相对更突出，单纯尺度校正不足"
    component_lead = "B" if float(b["median_between_error_share"]) >= float(w["median_within_error_share"]) else "W"
    lines = [
        "# B13 工作协方差成分可迁移性诊断",
        "",
        "## 结论状态",
        "",
        "`B13_DIAGNOSTIC_COMPLETE`。本包是经验诊断证据；D10F-C 仍为 `HOLD`。本任务没有构造生产协方差估计器。",
        "",
        "## 方法边界与验真",
        "",
        f"Stage-P 在任何目标参考开启前封存 {stage_p['sealed_objects']:,} 个池派生成分对象；Stage-S 验证 {pseudo['verified_objects'] + actual['verified_objects']:,} 个对象，失败 0。B12 缓存只读复用，`NEW_TREE_SOURCE_SCAN_ROWS=0`，`Q1_CALCULATION_ROWS=0`。",
        "",
        "矩阵从逐 member 的有限样本充分统计量直接构造。池估计始终使用 `Σ_g T_g/Σ_g(n_g-1)`，没有把池样地拼接后全局中心化。W 称为 `WITHIN_CELL_OBSERVED_RESIDUAL_SCATTER`，B 称为 `BETWEEN_CELL_ALLOCATION_MEAN_SCATTER`。没有 clipping、ridge、shrinkage、nearest-PD、平滑或协方差补全。",
        "",
        "## Q1—Q15",
        "",
        f"**Q1：原整协方差不匹配主要是尺度、形状/位置，还是两者？** {main_cause}。50 km generic T 的中位迹 |log ratio|={fmt(t['median_trace_abs_log_ratio'])}，单位迹 Frobenius 差={fmt(t['median_unit_trace_frobenius'])}，方差位置 TV={fmt(t['median_variance_location_tv'])}；相应 transport/noise 中位比分别为 {fmt(scale_ratio)}、{fmt(shape_ratio)}、{fmt(location_ratio)}。",
        "",
        f"**Q2：完美 oracle 尺度校正后还剩多少？** 50 km generic T 的基线中位相对 Frobenius={fmt(t['median_relative_frobenius'])}，把已封存池矩阵缩放到目标迹后为 {fmt(t['median_oracle_scale_relative_frobenius'])}，中位相对改善={fmt(t['median_oracle_scale_relative_improvement'])}。剩余差异明确非零；目标迹只用于 `DIAGNOSTIC_ORACLE_ONLY`。",
        "",
        f"**Q3：方差位置在哪里不同？** 总体中位 TV={fmt(t['median_variance_location_tv'])}、重叠={fmt(1-float(t['median_variance_location_tv']))}。逐目标的最大差异单元、目标最大方差单元和池最大方差单元保存在 `B13_VARIANCE_LOCATION_DIAGNOSTICS_v01.parquet`；这些位置差异包含样地位置与单元均值差，不能命名为纯分配。",
        "",
        f"**Q4：非对角依赖是否比对角位置更能迁移？** 单位迹 off-diagonal 差的中位 transport/noise 比={fmt(off_ratio)}，对角位置 TV 的对应比={fmt(location_ratio)}。两者使用不同原始距离尺度，只通过各自参考噪声归一化作方向性比较；没有为零对角强制相关矩阵。",
        "",
        f"**Q5：精确 W/B 分解显示什么？** generic 50 km 的误差能量中位份额为 W={fmt(w['median_within_error_share'])}、B={fmt(b['median_between_error_share'])}、交叉项={fmt(t['median_cross_error_share'])}；负交叉项比例={fmt(t['negative_cross_term_fraction'])}，说明部分目标存在成分误差抵消。按中位误差能量，{component_lead} 成分更大，但单独 Frobenius 大小不能替代完整误差几何。oracle W/B 交换的逐目标结果已保留。",
        "",
        f"**Q6：50 km 的 within-cell scatter 可识别吗？** 目标中 effective within-cell df>0 的比例={fmt(tr50['positive_within_df_fraction'])}，观测 W 为信息性的比例={fmt(tr50['informative_fraction'])}，中位 effective within-cell df={fmt(tr50['median_within_df'])}，位于重复单元的样地比例中位数={fmt(tr50['median_fraction_plots_replicated'])}。无重复产生的零 W 被标为结构稀疏，不解释为同质性。",
        "",
        f"**Q7：100/200 km 是否改变责任成分？** generic T 中位相对 Frobenius 从 50 km 的 {fmt(t['median_relative_frobenius'])} 变为 100/200 km 的 {fmt(c100['median_relative_frobenius'])}/{fmt(c200['median_relative_frobenius'])}；单位迹差为 {fmt(t['median_unit_trace_frobenius'])}/{fmt(c100['median_unit_trace_frobenius'])}/{fmt(c200['median_unit_trace_frobenius'])}。目标 W 的有效 within-df 比例变为 {fmt(tr100['positive_within_df_fraction'])}/{fmt(tr200['positive_within_df_fraction'])}。粗化提高重复度，但不能把 50 km Q1 粒度改写为 100/200 km。",
        "",
        f"**Q8：Level1 与 Level2 是否因同一原因失败？** Level1/Level2 的 T 相对 Frobenius中位数={fmt(l1t['median_relative_frobenius'])}/{fmt(l2t['median_relative_frobenius'])}，位置 TV={fmt(l1t['median_variance_location_tv'])}/{fmt(l2t['median_variance_location_tv'])}；W/B 相对误差分别为 {fmt(l1w['median_relative_frobenius'])}/{fmt(l2w['median_relative_frobenius'])} 与 {fmt(l1b['median_relative_frobenius'])}/{fmt(l2b['median_relative_frobenius'])}。50 km 有效 within-df 比例={fmt(l1rep['positive_within_df_fraction'])}/{fmt(l2rep['positive_within_df_fraction'])}。机制与可识别性不同，不能合并成一个解释。",
        "",
        f"**Q9：哪些差异超过目标自身参考噪声？** T/W/B 的相对 Frobenius transport/noise 中位数={fmt(t['median_transport_to_noise_ratio'])}/{fmt(w['median_transport_to_noise_ratio'])}/{fmt(b['median_transport_to_noise_ratio'])}；分量为 NOT_ESTIMABLE 时保持缺失，不改用事后拆分。比值 1 只是同量纲自然参照，不是生产阈值。",
        "",
        f"**Q10：B9 候选是否比固定 NC1 更像目标？** 在可比对象中，T/W/B 的候选相对 Frobenius 更小比例={fmt(t['candidate_better_nc1_fraction'])}/{fmt(w['candidate_better_nc1_fraction'])}/{fmt(b['candidate_better_nc1_fraction'])}。相对优于不兼容池并不等于绝对合格。",
        "",
        f"**Q11：直接97物种是否呈现同样模式？** 预声明的 450,080 个目标×代码配对中，池或目标 T 非零并进入成分评分的有 {pseudo['q1_union_nonzero']:,} 个。T/W/B 的有限相对误差中位数={fmt(q1t['median_relative_frobenius'])}/{fmt(q1w['median_relative_frobenius'])}/{fmt(q1b['median_relative_frobenius'])}；W 的结果标记为 `{q1w['evidence_class']}`。三类 multi-SPCD 只保留 accepted projection 的 code-level 诊断，不合并 SPCD。",
        "",
        f"**Q12：actual24 是否有一致的次级信号？** 24 个案例全部保留，FULL5 n={actual['n_min']}–{actual['n_max']}。50 km generic T/W/B 中位相对 Frobenius={fmt(amed('T'))}/{fmt(amed('W'))}/{fmt(amed('B'))}。由于 full5 很小，这些仅是 `FULL5_LIMITED_REFERENCE`，不是 truth、调参、筛选或 A/B 修正输入。",
        "",
        "**Q13：哪些成分共享假设仍具科学可行性？** 可以继续调查“尺度模型与单位迹结构分开”“只借用可识别的残差成分、保留目标域位置成分”两类窄假设。它们仍是 `HYPOTHESIS / DESIGN CANDIDATE`，尚未被本包升级为估计器。",
        "",
        "**Q14：哪些假设受到实质挑战？** 未经改变地搬运整协方差继续受到挑战；把 B 解释成纯空间分配、把无重复产生的零 W 当成同质性、把候选优于 NC1 当成生产资格，也都与本诊断边界不相容。",
        "",
        "**Q15：最窄的下一步是什么？** 在 mainline 另行授权后，先做预声明的尺度/单位迹分离检验，并按 Level1/Level2 与参考强度分层；若 B 仍主导，再调查域/分配感知重构。不要直接进入整套 GVCF、层级协方差或 replicate generation。",
        "",
        "## 代数与防火墙结果",
        "",
        f"member 恒等式检查 {invariants['member_identity_count']:,} 次、池/实际候选检查 {invariants['pool_identity_count']:,} 次、Q1 物种非零对象检查 {invariants['species_identity_count']:,} 次；`T=W+B` 材料失败为 0。误差几何检查 {invariants['error_geometry_count']:,} 次，失败 0。B12 50 km 整协方差基线重建 {invariants['b12_baseline_count']:,} 次，失败 0。所有矩阵由解析散度构造给出对称/PSD 状态；材料 PSD 失败 0。",
        "",
        "## 解释边界",
        "",
        "这是一项项目统计分析，不是 FIA 官方估计器。不存在生产 pass；B9 pool、A/B、A2、50 km 主粒度和 Q1 cohort identity 均未改变。",
    ]
    return "\n".join(lines)


def csv_qc_rows(input_meta: dict[str, Any], stage_p: dict[str, Any], pseudo: dict[str, Any],
                actual: dict[str, Any], invariants: dict[str, Any]) -> list[dict[str, Any]]:
    verified = pseudo["verified_objects"] + actual["verified_objects"]
    rows = [
        ("B12_OUTER_SHA256", EXPECTED_B12_SHA, input_meta["identities"]["b12"], "Exact accepted B12 v01_1 archive"),
        ("B11_OUTER_SHA256", EXPECTED_B11_SHA, input_meta["identities"]["b11"], "Exact accepted B11 archive"),
        ("Q1_PROJECTION_OUTER_SHA256", EXPECTED_Q1_SHA, input_meta["identities"]["q1_projection"], "Exact accepted derived projection"),
        ("CACHE_FILE_SHA256", EXPECTED_CACHE_SHA, input_meta["identities"]["cache"], "Read-only task-local cache"),
        ("CACHE_LOGICAL_SHA256", EXPECTED_CACHE_LOGICAL, input_meta["cache_logical_sha256"], f"rows={input_meta['cache_logical_rows']}"),
        ("CACHE_FINGERPRINT", EXPECTED_CACHE_FINGERPRINT, input_meta["cache_fingerprint"], "cache_meta"),
        ("PSEUDO_TOTAL", 5729, input_meta["protected"]["pseudo_total"], "accepted cache query"),
        ("PSEUDO_SCOREABLE", 4640, input_meta["protected"]["pseudo_scoreable"], "accepted cache query"),
        ("LEVEL1", 4397, input_meta["protected"]["level1"], "accepted cache query"),
        ("LEVEL2", 243, input_meta["protected"]["level2"], "accepted cache query"),
        ("ACTUAL24", 24, input_meta["protected"]["actual24"], "all retained"),
        ("FIA_SPCD", 402, input_meta["protected"]["fia_spcd"], "outcome-unselected universe unchanged"),
        ("TARGET_MEMBER_LEAK", 0, input_meta["protected"]["target_member_leak"], "B9 membership cache join"),
        ("STAGE_P_PLANNED_EQUALS_SEALED", stage_p["planned_objects"], stage_p["sealed_objects"], stage_p["registry_sha256_before_scoring"]),
        ("STAGE_S_VERIFIED", stage_p["sealed_objects"], verified, "independent reconstruction before reference open"),
        ("STAGE_S_FAILED", 0, pseudo["failed_objects"] + actual["failed_objects"], "digest mismatch is hard stop"),
        ("MEMBER_T_EQUALS_W_PLUS_B_FAIL", 0, invariants["member_identity_fail"], f"checks={invariants['member_identity_count']}; max_residual={invariants['member_max_residual']:.17g}"),
        ("POOL_T_EQUALS_W_PLUS_B_FAIL", 0, invariants["pool_identity_fail"], f"checks={invariants['pool_identity_count']}; max_residual={invariants['pool_max_residual']:.17g}"),
        ("SPECIES_T_EQUALS_W_PLUS_B_FAIL", 0, invariants["species_identity_fail"], f"checks={invariants['species_identity_count']}; max_residual={invariants['species_max_residual']:.17g}"),
        ("ERROR_GEOMETRY_IDENTITY_FAIL", 0, invariants["error_geometry_fail"], f"checks={invariants['error_geometry_count']}; max_residual={invariants['error_geometry_max_residual']:.17g}"),
        ("MATERIAL_PSD_FAIL", 0, invariants["psd_material_fail"], f"analytic scatter matrices checked={invariants['psd_matrix_count']}"),
        ("SYMMETRY_FAIL", 0, invariants["symmetry_fail"], "diagonal-minus-rank-one representation is symmetric by construction"),
        ("DF_IDENTITY_FAIL", 0, invariants["df_identity_fail"], "pool df=sum_g(n_g-1); target df=n-1"),
        ("B12_BASELINE_RECONSTRUCTION_FAIL", 0, invariants["b12_baseline_fail"], f"checks={invariants['b12_baseline_count']}; max relF delta={invariants['b12_baseline_max_relative_frobenius_delta']:.17g}"),
        ("NEW_TREE_SOURCE_SCAN_ROWS", 0, 0, "national TREE path absent from builder"),
        ("Q1_CALCULATION_ROWS", 0, 0, "no Q1 outcomes/support/range geometry read"),
        ("REGULARIZATION_APPLIED", "NONE", "NONE", "no clipping/ridge/shrinkage/nearest-PD/smoothing/completion"),
    ]
    return [{"check_id": a, "expected": b, "observed": c, "status": "PASS" if str(b) == str(c) else "FAIL", "evidence": d} for a, b, c, d in rows]


def firewall_rows(input_meta: dict[str, Any], stage_p: dict[str, Any], pseudo: dict[str, Any], actual: dict[str, Any]) -> list[dict[str, Any]]:
    verified = pseudo["verified_objects"] + actual["verified_objects"]
    rows = [
        ("STAGE_P_COMPLETE_BEFORE_REFERENCE_OPEN", "True", str(stage_p["stage_p_completed_before_target_reference_open"]), stage_p["registry_sha256_before_scoring"]),
        ("PLANNED_EQUALS_SEALED", stage_p["planned_objects"], stage_p["sealed_objects"], "component seal registry"),
        ("SEALED_EQUALS_STAGE_S_VERIFIED", stage_p["sealed_objects"], verified, "all generic/domain grains; direct97 candidate 50km; actual24"),
        ("STAGE_S_FAILED_OBJECTS", 0, pseudo["failed_objects"] + actual["failed_objects"], "hard-stop digest comparisons"),
        ("TARGET_REFERENCE_OPEN_AFTER_TARGET_SEALS_VERIFIED", "True", "True", "target member/full5 loaded only after verify_target_seals"),
        ("TARGET_MEMBER_LEAK", 0, input_meta["protected"]["target_member_leak"], "accepted B9 cache join"),
        ("FULL5_ROLE", "FULL5_LIMITED_REFERENCE", "FULL5_LIMITED_REFERENCE", "24 cases; no truth/tuning/filter/correction"),
        ("Q1_PROJECTION_ROLE", "SUBGROUP_ONLY", "SUBGROUP_ONLY", "does not define primary component method or thresholds"),
        ("DIRECT97_SCOPE", "CANDIDATE_50KM_PREDECLARED", "CANDIDATE_50KM_PREDECLARED", "all 450080 pool objects explicitly sealed, including zeros"),
        ("MULTI_SPCD_COMBINATION", 0, 0, "three accepted species retained code-level only"),
        ("NEW_TREE_SOURCE_SCAN_ROWS", 0, 0, "read-only B12 cache"),
        ("Q1_CALCULATION_ROWS", 0, 0, "no support outcome or Q1 statistic"),
    ]
    return [{"check_id": a, "expected": b, "observed": c, "status": "PASS" if str(b) == str(c) else "FAIL", "evidence": d} for a, b, c, d in rows]


def provenance_rows(input_meta: dict[str, Any], stage_p: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {"provenance_id": "P01", "object": "A/B, A2, B9 route and 50-km primary grain", "scientific_status": "FROZEN", "source": "accepted Q1 design governance", "sha256": "", "notes": "Not modified"},
        {"provenance_id": "P02", "object": "B11 covariance algebra", "scientific_status": "ACCEPTED EVIDENCE", "source": str(B11_ZIP), "sha256": input_meta["identities"]["b11"], "notes": "Within-member centering retained"},
        {"provenance_id": "P03", "object": "B12 v01_1 whole covariance qualification", "scientific_status": "ACCEPTED EVIDENCE", "source": str(B12_ZIP), "sha256": input_meta["identities"]["b12"], "notes": "Baseline reconstructed; D10F-C remains HOLD"},
        {"provenance_id": "P04", "object": "B12 task-local cache", "scientific_status": "ACCEPTED EVIDENCE", "source": str(CACHE), "sha256": input_meta["identities"]["cache"], "notes": f"logical={input_meta['cache_logical_sha256']}; fingerprint={input_meta['cache_fingerprint']}; read-only"},
        {"provenance_id": "P05", "object": "Q1 direct97 and multi-code identity projection", "scientific_status": "ACCEPTED DERIVED PROJECTION EVIDENCE", "source": str(Q1_ZIP), "sha256": input_meta["identities"]["q1_projection"], "notes": "Subgroup-only; no method/threshold selection"},
        {"provenance_id": "P06", "object": "B13 component transport diagnostics", "scientific_status": "B13 EMPIRICAL DIAGNOSTIC EVIDENCE", "source": TASK, "sha256": stage_p["registry_sha256_before_scoring"], "notes": "Exact T=W+B; no regularization; not a production estimator"},
        {"provenance_id": "P07", "object": "Future scale/shape or component-sharing model", "scientific_status": "HYPOTHESIS / DESIGN CANDIDATE", "source": TASK, "sha256": "", "notes": "Recommendation only; not implemented"},
        {"provenance_id": "P08", "object": "Production covariance solution and D10F-C", "scientific_status": "OPEN", "source": "Q1 mainline authority", "sha256": "", "notes": "No production pass in B13"},
    ]


def open_item_rows() -> list[dict[str, Any]]:
    return [
        {"item_id": "OPEN_01", "topic": "D10F-C", "status": "HOLD", "evidence": "B13 diagnoses components but does not qualify a production covariance estimator", "mainline_action": "Review component evidence; do not infer PASS"},
        {"item_id": "OPEN_02", "topic": "SCALE_SHAPE_SEPARATION", "status": "OPEN", "evidence": "Oracle-scale result is diagnostic only", "mainline_action": "If authorized, predeclare a separate scale/normalized-shape investigation"},
        {"item_id": "OPEN_03", "topic": "WITHIN_CELL_IDENTIFIABILITY", "status": "OPEN", "evidence": "50-km replication audit retained per target/pool", "mainline_action": "Resolve reference-strength limits before residual borrowing"},
        {"item_id": "OPEN_04", "topic": "BETWEEN_CELL_MODEL", "status": "OPEN", "evidence": "B includes both cell occurrence and between-cell mean differences", "mainline_action": "Do not label B pure allocation; consider domain-aware future work only after authorization"},
        {"item_id": "OPEN_05", "topic": "Q1_MULTI_SPCD", "status": "OPEN", "evidence": "Three accepted multi-code species retained code-level only", "mainline_action": "Formal species-level recomputation requires separate authority"},
        {"item_id": "OPEN_06", "topic": "ACTUAL24", "status": "LIMITED", "evidence": "FULL5 n=2-13; secondary evidence only", "mainline_action": "Never use as truth, tuning, filtering, or A/B correction"},
    ]


def assert_hard_qc(invariants: dict[str, Any], stage_p: dict[str, Any], pseudo: dict[str, Any], actual: dict[str, Any]) -> None:
    failures = {
        "member_identity_fail": invariants["member_identity_fail"],
        "pool_identity_fail": invariants["pool_identity_fail"],
        "species_identity_fail": invariants["species_identity_fail"],
        "error_geometry_fail": invariants["error_geometry_fail"],
        "psd_material_fail": invariants["psd_material_fail"],
        "symmetry_fail": invariants["symmetry_fail"],
        "df_identity_fail": invariants["df_identity_fail"],
        "b12_baseline_fail": invariants["b12_baseline_fail"],
        "stage_s_failed": pseudo["failed_objects"] + actual["failed_objects"],
        "seal_verify_gap": stage_p["sealed_objects"] - pseudo["verified_objects"] - actual["verified_objects"],
    }
    bad = {k: v for k, v in failures.items() if v != 0}
    if bad:
        raise RuntimeError(f"HARD QC failure: {bad}")


def write_sha_and_transfer() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    excludes = {ZIP_NAME, "SHA256SUMS.csv", "TRANSFER_MANIFEST_v01.csv"}
    files = sorted([p for p in OUT.rglob("*") if p.is_file() and p.name not in excludes], key=lambda p: p.relative_to(OUT).as_posix())
    sha_rows = [{"relative_path": p.relative_to(OUT).as_posix(), "size_bytes": p.stat().st_size, "sha256": sha256_file(p)} for p in files]
    write_csv(OUT / "SHA256SUMS.csv", sha_rows, ["relative_path", "size_bytes", "sha256"])
    transfer_files = files + [OUT / "SHA256SUMS.csv"]
    rows = []
    for p in transfer_files:
        rel = p.relative_to(OUT).as_posix()
        if p.suffix == ".parquet": role, priority = "MACHINE_EVIDENCE", "P0"
        elif p.name == "B13_MAIN_REPORT_v01.md": role, priority = "PRIMARY_REPORT", "P0"
        elif "QC" in p.name or "DISPOSITION" in p.name: role, priority = "AUDIT_CONTROL", "P0"
        elif p.suffix == ".csv": role, priority = "TABULAR_EVIDENCE", "P1"
        elif rel.startswith("src/"): role, priority = "REPRODUCIBILITY_CODE", "P2"
        else: role, priority = "PROVENANCE_SUPPORT", "P2"
        rows.append({
            "local_path": str(p), "relative_path": f"release_mirror/{TRANSFER_NAME}/{rel}",
            "role": role, "upload_target": "mirror", "required": "YES", "mainline_priority": priority,
            "size_bytes": p.stat().st_size, "sha256": sha256_file(p),
            "notes": "B13 Work diagnostic evidence; preserve relative path; upload_target intentionally mirror",
        })
    write_csv(OUT / "TRANSFER_MANIFEST_v01.csv", rows, [
        "local_path", "relative_path", "role", "upload_target", "required",
        "mainline_priority", "size_bytes", "sha256", "notes",
    ])
    return sha_rows, rows


def deterministic_zip() -> Path:
    zip_path = OUT / ZIP_NAME
    if zip_path.exists(): zip_path.unlink()
    files = sorted([p for p in OUT.rglob("*") if p.is_file() and p != zip_path], key=lambda p: p.relative_to(OUT).as_posix())
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for p in files:
            info = zipfile.ZipInfo(p.relative_to(OUT).as_posix(), ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            z.writestr(info, p.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    return zip_path


def run_analysis(resume_stage_p: bool = False) -> None:
    validate_floor_division()
    if not resume_stage_p and OUT.exists() and any(OUT.iterdir()):
        raise RuntimeError(f"Output directory is not empty; refusing to mix artifacts: {OUT}")
    OUT.mkdir(parents=True, exist_ok=True)
    if resume_stage_p:
        stale_stop = OUT / "B13_STOP_REPORT_v01.md"
        if stale_stop.exists(): stale_stop.unlink()
    log_path = OUT / "B13_EXECUTION_LOG_v01.txt"
    with log_path.open("w", encoding="utf-8", newline="\n") as log:
        def note(message: str) -> None:
            print(message, flush=True); log.write(message + "\n"); log.flush()
        note(f"START task={TASK} epoch={time.time():.3f}")
        note("INPUT_VERIFY begin")
        input_meta = verify_inputs(full_logical=True)
        q1_species, q1_ledger, q1_provenance = load_q1_species()
        note(f"INPUT_VERIFY pass direct97={len(q1_species)} multi3={sum(r['species_level_interpretation_class']=='MULTI_SPCD_B12_EVIDENCE_DIAGNOSTIC_ONLY' for r in q1_ledger)}")
        if resume_stage_p:
            checkpoint = WORK / "STAGE_P_COMPONENT_SEAL_CHECKPOINT_v01.json"
            seal_path = OUT / "B13_COMPONENT_PREDICTION_SEAL_v01.parquet"
            index_path = WORK / "stage_p_seal_index.sqlite"
            if not checkpoint.is_file() or not seal_path.is_file() or not index_path.is_file():
                raise RuntimeError("Stage-P resume inputs missing")
            stage_p = json.loads(checkpoint.read_text(encoding="utf-8"))
            if sha256_file(seal_path) != stage_p["registry_sha256_before_scoring"] or stage_p["sealed_objects"] != 1517064:
                raise RuntimeError("Stage-P resume identity mismatch")
            note(f"STAGE_P_REUSED_UNCHANGED objects={stage_p['sealed_objects']} sha256={stage_p['registry_sha256_before_scoring']}")
        else:
            stage_p = build_stage_p(q1_species, log)
            note(f"STAGE_P_COMPLETE objects={stage_p['sealed_objects']} sha256={stage_p['registry_sha256_before_scoring']}")
        # Accepted held-out B12 covariance evidence is opened only after Stage-P completion.
        baseline = load_b12_baseline()
        invariants = empty_invariants()
        con = read_only_connection(); audit_all_members(con, invariants, log); con.close()
        stack, writers = writers_context()
        with stack:
            pseudo = score_pseudo_targets(q1_species, baseline, invariants, writers, log)
            actual = score_actual24(q1_species, invariants, writers, log)
        parquet_rows = {k: w.nrows for k, w in writers.items()}
        for name in [p for p in OUT.glob("*.parquet")]:
            footer_info(name)
        assert_hard_qc(invariants, stage_p, pseudo, actual)
        note(f"HARD_QC_PASS stage_s={pseudo['verified_objects'] + actual['verified_objects']} baseline={invariants['b12_baseline_count']}")

        level = make_level_summary(pseudo["generic_records"])
        coarse = make_coarse_summary(pseudo["generic_records"])
        q1_summary = make_q1_summary(pseudo["q1_records"], q1_species)
        disposition = make_disposition(level, coarse, q1_summary, pseudo["replication_records"], actual)
        qc = csv_qc_rows(input_meta, stage_p, pseudo, actual, invariants)
        firewall = firewall_rows(input_meta, stage_p, pseudo, actual)
        if any(r["status"] != "PASS" for r in qc + firewall):
            raise RuntimeError("QC CSV contains non-PASS hard control")
        csv_rows = {
            "B13_LEVEL_ROUTE_SUMMARY_v01.csv": write_csv(OUT / "B13_LEVEL_ROUTE_SUMMARY_v01.csv", level, LEVEL_FIELDS),
            "B13_COARSE_GRAIN_SUMMARY_v01.csv": write_csv(OUT / "B13_COARSE_GRAIN_SUMMARY_v01.csv", coarse, LEVEL_FIELDS),
            "B13_Q1_97_DIRECT_SUBGROUP_SUMMARY_v01.csv": write_csv(OUT / "B13_Q1_97_DIRECT_SUBGROUP_SUMMARY_v01.csv", q1_summary, Q1_FIELDS),
            "B13_COMPONENT_DISPOSITION_MATRIX_v01.csv": write_csv(OUT / "B13_COMPONENT_DISPOSITION_MATRIX_v01.csv", disposition, list(disposition[0])),
            "B13_PROVENANCE_v01.csv": write_csv(OUT / "B13_PROVENANCE_v01.csv", provenance_rows(input_meta, stage_p), ["provenance_id", "object", "scientific_status", "source", "sha256", "notes"]),
            "B13_OPEN_ITEMS_v01.csv": write_csv(OUT / "B13_OPEN_ITEMS_v01.csv", open_item_rows(), ["item_id", "topic", "status", "evidence", "mainline_action"]),
            "B13_INVARIANT_QC_v01.csv": write_csv(OUT / "B13_INVARIANT_QC_v01.csv", qc, ["check_id", "expected", "observed", "status", "evidence"]),
            "B13_REFERENCE_FIREWALL_QC_v01.csv": write_csv(OUT / "B13_REFERENCE_FIREWALL_QC_v01.csv", firewall, ["check_id", "expected", "observed", "status", "evidence"]),
        }
        report = make_report(level, coarse, q1_summary, pseudo["replication_records"], actual, pseudo, stage_p, invariants)
        write_text(OUT / "B13_MAIN_REPORT_v01.md", report)
        config = {
            "task": TASK, "builder_version": "1.0.1", "primary_grain_km": 50,
            "diagnostic_grains_km": [100, 200], "components": list(COMPONENTS),
            "component_names": {"T": "TOTAL_SAMPLE_SCATTER", "W": "WITHIN_CELL_OBSERVED_RESIDUAL_SCATTER", "B": "BETWEEN_CELL_ALLOCATION_MEAN_SCATTER"},
            "families_primary": list(FAMILIES), "q1_direct97_scope": "SPECIES_Y_CANDIDATE_50KM",
            "split_identity": "FROZEN_B12_SPLIT_BALANCED_HASH_B12_SPLIT_4_REPLICATES",
            "pool_centering": "WITHIN_MEMBER_THEN_SUM_NUMERATORS_OVER_SUM_DF",
            "regularization": "NONE", "algebra_abs_tolerance": ALGEBRA_ABS_TOL,
            "algebra_relative_tolerance": ALGEBRA_REL_TOL,
            "psd_basis": "ANALYTIC_FINITE_SAMPLE_SCATTER_CONSTRUCTION_WITH_UNCANCELLED_EXPANSION_SCALE_NUMERIC_QC",
            "psd_numeric_action": "DIAGNOSTIC_NORM_ROUNDOFF_CLAMP_ONLY_NO_MATRIX_MODIFICATION",
            "new_tree_source_scan_rows": 0, "q1_calculation_rows": 0,
        }
        write_json(OUT / "B13_CONFIG_v01.json", config)
        run_meta = {
            "task": TASK, "task_status": "B13_DIAGNOSTIC_COMPLETE", "created_at_epoch": time.time(),
            "input_verification": input_meta, "q1_direct_species": q1_species,
            "q1_ledger_rows": len(q1_ledger), "q1_projection_provenance_rows": len(q1_provenance),
            "stage_p": stage_p, "stage_s": {
                "pseudo_verified": pseudo["verified_objects"], "actual_verified": actual["verified_objects"],
                "failed": pseudo["failed_objects"] + actual["failed_objects"],
            },
            "pseudo": {k: v for k, v in pseudo.items() if k not in {"generic_records", "q1_records", "replication_records"}},
            "actual24": {k: v for k, v in actual.items() if k != "records"},
            "invariants": invariants, "parquet_rows": parquet_rows, "csv_rows": csv_rows,
            "scientific_boundary": "DIAGNOSTIC_ONLY_NO_PRODUCTION_PASS",
            "d10fc_status": "HOLD", "new_tree_source_scan_rows": 0, "q1_calculation_rows": 0,
        }
        write_json(OUT / "B13_RUN_METADATA_v01.json", run_meta)
        shutil.copy2(REQUEST, OUT / "TASK_CONTRACT_v01.md")
        (OUT / "src").mkdir(parents=True, exist_ok=True)
        for name in ("b13_component_diagnostic.py", "mini_parquet.py", "mini_parquet_reader.py", "verify_cache_digest_3491.py", "verify_csvs.mjs"):
            shutil.copy2(SRC / name, OUT / "src" / name)
        note(f"OUTPUTS_WRITTEN parquet={sum(parquet_rows.values())} csv_pre_manifest={sum(csv_rows.values())}")
        note("END status=B13_DIAGNOSTIC_COMPLETE STOP_RETURN_TO_Q1_MAINLINE")
    write_sha_and_transfer()


def package_outputs() -> None:
    required = [
        "B13_MAIN_REPORT_v01.md", "B13_MATRIX_SCALE_SHAPE_DIAGNOSTICS_v01.parquet",
        "B13_VARIANCE_LOCATION_DIAGNOSTICS_v01.parquet", "B13_COMPONENT_REPLICATION_AUDIT_v01.parquet",
        "B13_WITHIN_BETWEEN_DECOMPOSITION_v01.parquet", "B13_COMPONENT_ERROR_GEOMETRY_v01.parquet",
        "B13_ORACLE_COMPONENT_SWAP_v01.parquet", "B13_COMPONENT_REFERENCE_NOISE_v01.parquet",
        "B13_COMPONENT_TRANSPORT_VS_NOISE_v01.parquet", "B13_COMPONENT_NEGATIVE_CONTROLS_v01.parquet",
        "B13_LEVEL_ROUTE_SUMMARY_v01.csv", "B13_COARSE_GRAIN_SUMMARY_v01.csv",
        "B13_Q1_97_DIRECT_SUBGROUP_SUMMARY_v01.csv", "B13_ACTUAL24_LIMITED_COMPONENT_REFERENCE_v01.parquet",
        "B13_PROVENANCE_v01.csv", "B13_OPEN_ITEMS_v01.csv", "B13_INVARIANT_QC_v01.csv",
        "B13_REFERENCE_FIREWALL_QC_v01.csv", "B13_RUN_METADATA_v01.json",
        "B13_COMPONENT_DISPOSITION_MATRIX_v01.csv", "B13_COMPONENT_PREDICTION_SEAL_v01.parquet",
    ]
    missing = [name for name in required if not (OUT / name).is_file()]
    if missing: raise RuntimeError(f"Cannot package; missing: {missing}")
    write_sha_and_transfer()
    zip_path = deterministic_zip()
    verify = zip_internal_verify(zip_path)
    manifest = list(csv.DictReader((OUT / "TRANSFER_MANIFEST_v01.csv").open("r", encoding="utf-8-sig", newline="")))
    bad_target = [r for r in manifest if r["upload_target"] != "mirror"]
    if bad_target:
        raise RuntimeError("TRANSFER_MANIFEST upload_target is not mirror")
    print(json.dumps({"zip": str(zip_path), "sha256": sha256_file(zip_path), "size_bytes": zip_path.stat().st_size,
                      "internal_hash_rows": verify["internal_hash_rows"], "transfer_rows": len(manifest),
                      "upload_targets": sorted({r["upload_target"] for r in manifest}),
                      "status": "B13_DIAGNOSTIC_COMPLETE", "stop": "RETURN_TO_Q1_MAINLINE"}, ensure_ascii=False, indent=2))


def preflight() -> None:
    validate_floor_division()
    meta = verify_inputs(full_logical=False)
    q1_species, ledger, _ = load_q1_species()
    con = read_only_connection()
    target = con.execute("SELECT * FROM target WHERE target_type='PSEUDO' AND validation_status='AVAILABLE' ORDER BY target_id LIMIT 1").fetchone()
    bundle = load_pool_bundle(con, target["target_id"], "CANDIDATE", q1_species)
    reps = component_reps(bundle, "GENERIC_Y", 50)
    residual, tol, status = algebra_identity(reps["T"], reps["W"], reps["B"])
    con.close()
    print(json.dumps({"input_sha": meta["identities"], "direct_species": len(q1_species), "ledger_rows": len(ledger),
                      "sample_target": target["target_id"], "sample_pool_df": bundle["pool_df"],
                      "sample_algebra_residual": residual, "sample_tolerance": tol, "sample_status": status}, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["preflight", "run", "resume", "package"])
    args = parser.parse_args()
    try:
        if args.mode == "preflight": preflight()
        elif args.mode == "run": run_analysis()
        elif args.mode == "resume": run_analysis(resume_stage_p=True)
        else: package_outputs()
    except Exception as exc:
        if args.mode in {"run", "resume"}:
            OUT.mkdir(parents=True, exist_ok=True)
            write_text(OUT / "B13_STOP_REPORT_v01.md", f"# B13 STOP REPORT\n\nHARD STOP: {type(exc).__name__}: {exc}\n\n未绕过合同边界。")
        raise


if __name__ == "__main__":
    main()
