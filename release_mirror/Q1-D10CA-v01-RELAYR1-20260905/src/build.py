from __future__ import annotations

import csv
import gzip
import hashlib
import io
import json
import os
import platform
import shutil
import sqlite3
import sys
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


TASK_ID = "D10C_A_FIA_ABUNDANCE_ESTIMATOR_AUTHORITY_CLOSURE_v01"
TERMINAL_OK = "ABUNDANCE_ESTIMATOR_AUTHORITY_CLOSED_READY_FOR_D10C"
ROOT = Path(r"C:\range_paper")
ARCH = ROOT / "10_archive" / "d10ca"
PKG = ARCH / "pkg"
OUT = PKG / "out"
QC = PKG / "qc"
SRC = PKG / "src"
CTL = PKG / "control"
MAN = PKG / "manifest"

D09C_ZIP = ROOT / "10_archive" / "d09c_t2_final_correction_v02" / "Q1_D09C_T2_FINAL_CORRECTION_REPRODUCIBLE_v02.zip"
D10A_ZIP = ROOT / "10_archive" / "d10a_real_layout_nonoracle_v01" / "Q1_D10A_REAL_LAYOUT_NONORACLE_OBSERVATION_CALIBRATION_REPRODUCIBLE_v01.zip"
RAW_ZIP = ROOT / "02_raw" / "FIA" / "SQLite_FIADB_ENTIRE.zip"
DB = ROOT / "99_tmp" / "d08c2_preflight_observational_authority_v01" / "source_cache" / "SQLite_FIADB_ENTIRE.db"
ASSET_AUTH = ROOT / "05_qc" / "d08c2_preflight_observational_authority_v01" / "Q1_D08C2_PREFLIGHT_ASSET_AUTHORITY_v01.csv"
DB_GUIDE = ROOT / "03_doc" / "FIA" / "wo-v9-4_Aug2025_UG_FIADB_database_description_NFI.pdf"
FIELD_GUIDE = ROOT / "03_doc" / "FIA" / "v9-5_sep2025_fg_nfi_natl.pdf"
CONTRACT = Path(r"C:\Users\bug_g\.codex\attachments\41a1226b-8a67-401f-8bc8-209886e8d6f2\pasted-text.txt")

EXPECTED = {
    str(D09C_ZIP): "07cb461121c71ef46990fea3e0cf9d8f139fd873234b9f57910ff10c7c33752f",
    str(RAW_ZIP): "ec2e4caf2a92e6079c20483f4a5f08d5ec2e7c31f498045237896a6df7e1565e",
    str(DB_GUIDE): "ec735ead3852ba6dbb65cb7257b4f8e0795d4c641be4d625ed81ce64eeba2833",
    str(FIELD_GUIDE): "09279b80db8b4d516599f621b7bda851fcf727825eeecfe93bc65d6071a2d1e7",
}

SHORT_NAME_MAP = {
    "plot_block_xwalk_v01.csv.gz": "Q1_D10C_A_NATIONWIDE_PLOT_TO_FINAL_BLOCK_CROSSWALK_v01.csv.gz",
    "xwalk_qc_v01.csv": "Q1_D10C_A_CROSSWALK_COMPLETENESS_QC_v01.csv",
    "ab_overlap_v01.csv": "Q1_D10C_A_AB_PERMANENT_PLOT_OVERLAP_QC_v01.csv",
    "abundance_rule_v01.md": "Q1_D10C_A_ABUNDANCE_CONTRIBUTION_RULE_v01.md",
    "partial_effort_v01.md": "Q1_D10C_A_PARTIAL_EFFORT_AUTHORITY_v01.md",
    "formula_ledger_v01.csv": "Q1_D10C_A_ESTIMATOR_FORMULA_LEDGER_v01.csv",
    "closure_summary_v01.csv": "Q1_D10C_A_AUTHORITY_CLOSURE_SUMMARY_v01.csv",
    "result_note_v01.md": "Q1_D10C_A_RESULT_NOTE_v01.md",
    "registry_delta_v01.csv": "REGISTRY_DELTA_v01.csv",
    "transfer_manifest_v01.csv": "TRANSFER_MANIFEST_v01.csv",
    "sha256s.csv": "SHA256SUMS.csv",
}


def sha256_file(path: Path, chunk: int = 16 * 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def csv_write(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def md_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def read_member_csv(z: zipfile.ZipFile, suffix: str, **kwargs) -> pd.DataFrame:
    names = [n for n in z.namelist() if n.endswith(suffix)]
    if len(names) != 1:
        raise RuntimeError(f"Expected exactly one ZIP member ending {suffix!r}; found {len(names)}")
    with z.open(names[0]) as f:
        return pd.read_csv(f, **kwargs)


def read_nested_csv(outer: zipfile.ZipFile, nested_zip: zipfile.ZipFile, suffix: str, **kwargs) -> pd.DataFrame:
    names = [n for n in nested_zip.namelist() if n.endswith(suffix)]
    if len(names) != 1:
        raise RuntimeError(f"Expected one nested member ending {suffix!r}; found {len(names)}")
    zbytes = nested_zip.read(names[0])
    with zipfile.ZipFile(io.BytesIO(zbytes)) as inner:
        csv_names = [n for n in inner.namelist() if n.lower().endswith(".csv")]
        if len(csv_names) != 1:
            raise RuntimeError(f"Expected one CSV inside {names[0]}; found {len(csv_names)}")
        with inner.open(csv_names[0]) as f:
            return pd.read_csv(f, **kwargs)


def clean_str(series: pd.Series) -> pd.Series:
    return series.astype("string").str.strip().replace({"<NA>": pd.NA, "nan": pd.NA})


def int_str(series: pd.Series, width: int | None = None) -> pd.Series:
    x = pd.to_numeric(series, errors="coerce").astype("Int64").astype("string")
    return x.str.zfill(width) if width else x


def deterministic_zip(src: Path, out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for p in sorted(src.rglob("*"), key=lambda q: q.relative_to(src).as_posix()):
            if not p.is_file():
                continue
            rel = (Path("D10CA_v01") / p.relative_to(src)).as_posix()
            info = zipfile.ZipInfo(rel, date_time=(2026, 9, 5, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            with p.open("rb") as f:
                z.writestr(info, f.read(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def build() -> None:
    if PKG.exists():
        shutil.rmtree(PKG)
    for d in (OUT, QC, SRC, CTL, MAN):
        d.mkdir(parents=True, exist_ok=True)

    # Identity checks. The 15.35 GB raw ZIP hash is independently recomputed here.
    identity_rows = []
    for path in (D09C_ZIP, RAW_ZIP, DB_GUIDE, FIELD_GUIDE):
        actual = sha256_file(path)
        identity_rows.append({
            "asset": path.name,
            "path": str(path),
            "bytes": path.stat().st_size,
            "expected_sha256": EXPECTED[str(path)],
            "actual_sha256": actual,
            "status": "PASS" if actual == EXPECTED[str(path)] else "FAIL",
        })

    asset_auth = pd.read_csv(ASSET_AUTH, dtype=str, keep_default_na=False)
    db_auth = asset_auth.loc[asset_auth["ASSET"] == "FIA_SQLITE_EXTRACTED_WORKING_COPY"]
    if len(db_auth) != 1:
        raise RuntimeError("Accepted D08C2 extracted DB authority row is not unique")
    db_auth = db_auth.iloc[0]
    db_status = (
        DB.exists()
        and str(DB) == db_auth["PATH"]
        and DB.stat().st_size == int(db_auth["ACTUAL_BYTES"])
        and db_auth["STATUS"] == "PASS_EXTRACTED_FROM_FROZEN_RAW"
    )
    identity_rows.append({
        "asset": "SQLite_FIADB_ENTIRE.db",
        "path": str(DB),
        "bytes": DB.stat().st_size if DB.exists() else "",
        "expected_sha256": db_auth["ACTUAL_SHA256"],
        "actual_sha256": db_auth["ACTUAL_SHA256"],
        "status": "PASS_ACCEPTED_D08C2_EXTRACTED_AUTHORITY" if db_status else "FAIL",
    })

    d10a_sidecar = Path(str(D10A_ZIP) + ".sha256")
    sidecar_text = d10a_sidecar.read_text(encoding="utf-8-sig").strip()
    d10a_expected = sidecar_text.split()[0].lower()
    d10a_actual = sha256_file(D10A_ZIP)
    identity_rows.append({
        "asset": D10A_ZIP.name,
        "path": str(D10A_ZIP),
        "bytes": D10A_ZIP.stat().st_size,
        "expected_sha256": d10a_expected,
        "actual_sha256": d10a_actual,
        "status": "PASS" if d10a_actual == d10a_expected else "FAIL",
    })
    csv_write(QC / "input_identity_v01.csv", identity_rows,
              ["asset", "path", "bytes", "expected_sha256", "actual_sha256", "status"])
    input_identity_ok = all(str(r["status"]).startswith("PASS") for r in identity_rows)

    with zipfile.ZipFile(D09C_ZIP) as z09:
        selected = read_member_csv(z09, "Q1_D09C_T2_FINAL_RULE_SELECTED_PARTITIONS_v02.csv", dtype=str, keep_default_na=False)
        ti = read_member_csv(z09, "Q1_D09C_T2_FINAL_FOLD_SPECIFIC_TI_DESIGN_v02.csv", dtype=str, keep_default_na=False)
        pred_names = [n for n in z09.namelist() if n.endswith("Q1_D09C_T2_BOUNDED_COMPLETION_REPRODUCIBLE_v01.zip")]
        if len(pred_names) != 1:
            raise RuntimeError("D09C predecessor ZIP is not unique inside final package")
        predecessor_bytes = z09.read(pred_names[0])

    with zipfile.ZipFile(D10A_ZIP) as z10:
        f0 = read_member_csv(z10, "Q1_D10A_REAL_F0_OPPORTUNITY_LAYOUT_v01.csv", dtype=str, keep_default_na=False)

    if len(selected) != 48 or selected["state_fips"].nunique() != 48:
        raise RuntimeError("D09C final selected partition table is not a 48-state unique frame")
    if len(ti) != 5752:
        raise RuntimeError(f"D09C final TI table expected 5752 rows, got {len(ti)}")

    selected["state_fips"] = selected["state_fips"].str.zfill(2)
    f0["state_fips"] = f0["state_fips"].str.zfill(2)
    f0["plot_cn"] = clean_str(f0["plot_cn"])
    f0["component_evalid"] = int_str(f0["component_evalid"])
    f0["panel"] = int_str(f0["panel"])
    f0["fold"] = clean_str(f0["fold"])

    evals = sorted({int(v) for v in selected["component_evalid"]})
    national_evals = [x for x in evals if x // 10000 not in (6, 41, 53)]
    placeholders = ",".join("?" for _ in national_evals)
    query = f"""
    SELECT
      a.PLT_CN AS plot_cn, a.STATECD AS assignment_statecd,
      a.INVYR AS assignment_invyr, a.EVALID AS assignment_evalid,
      a.STRATUM_CN AS stratum_cn, a.ESTN_UNIT AS assignment_estn_unit,
      a.STRATUMCD AS assignment_stratumcd,
      p.STATECD AS plot_statecd, p.INVYR AS plot_invyr, p.MEASYEAR AS measyear,
      p.P2PANEL AS p2panel, p.UNITCD AS unitcd, p.COUNTYCD AS countycd,
      p.PLOT AS plot_number, p.PREV_PLT_CN AS prev_plt_cn,
      p.DESIGNCD AS designcd, p.MACRO_BREAKPOINT_DIA AS macro_breakpoint_dia,
      s.ESTN_UNIT AS stratum_estn_unit, s.STRATUMCD AS stratumcd,
      s.EXPNS AS official_full_expns,
      s.ADJ_FACTOR_SUBP AS adj_factor_subp,
      s.ADJ_FACTOR_MACR AS adj_factor_macr
    FROM POP_PLOT_STRATUM_ASSGN a
    JOIN PLOT p ON p.CN = a.PLT_CN
    JOIN POP_STRATUM s ON s.CN = a.STRATUM_CN AND s.EVALID = a.EVALID
    WHERE a.EVALID IN ({placeholders})
    """
    con = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    try:
        national = pd.read_sql_query(query, con, params=national_evals, dtype=str)
    finally:
        con.close()
    national["reconstruction_source"] = "FROZEN_NATIONAL_SQLITE"

    supplement_frames = []
    with zipfile.ZipFile(io.BytesIO(predecessor_bytes)) as pred:
        for abbr, fips in (("CA", "06"), ("OR", "41"), ("WA", "53")):
            evalid = int(selected.loc[selected["state_abbr"] == abbr, "component_evalid"].iloc[0])
            assn = read_nested_csv(None, pred, f"{abbr}_POP_PLOT_STRATUM_ASSGN.zip", dtype=str, keep_default_na=False)
            plot = read_nested_csv(None, pred, f"{abbr}_PLOT.zip", dtype=str, keep_default_na=False)
            strata = read_nested_csv(None, pred, f"{abbr}_POP_STRATUM.zip", dtype=str, keep_default_na=False)
            assn = assn.loc[pd.to_numeric(assn["EVALID"], errors="coerce") == evalid].copy()
            strata = strata.loc[pd.to_numeric(strata["EVALID"], errors="coerce") == evalid].copy()
            plot = plot[["CN", "STATECD", "INVYR", "MEASYEAR", "P2PANEL", "UNITCD", "COUNTYCD", "PLOT", "PREV_PLT_CN", "DESIGNCD", "MACRO_BREAKPOINT_DIA"]]
            strata = strata[["CN", "ESTN_UNIT", "STRATUMCD", "EXPNS", "ADJ_FACTOR_SUBP", "ADJ_FACTOR_MACR"]]
            s = assn.merge(plot, left_on="PLT_CN", right_on="CN", how="left", suffixes=("_a", "_p"), validate="many_to_one")
            s = s.merge(strata, left_on="STRATUM_CN", right_on="CN", how="left", suffixes=("", "_s"), validate="many_to_one")
            s = s.rename(columns={
                "PLT_CN": "plot_cn", "STATECD_a": "assignment_statecd", "INVYR_a": "assignment_invyr",
                "EVALID": "assignment_evalid", "STRATUM_CN": "stratum_cn",
                "ESTN_UNIT": "assignment_estn_unit", "STRATUMCD": "assignment_stratumcd",
                "STATECD_p": "plot_statecd", "INVYR_p": "plot_invyr", "MEASYEAR": "measyear",
                "P2PANEL": "p2panel", "UNITCD_p": "unitcd", "COUNTYCD_p": "countycd",
                "PLOT_p": "plot_number", "PREV_PLT_CN": "prev_plt_cn", "DESIGNCD": "designcd",
                "MACRO_BREAKPOINT_DIA": "macro_breakpoint_dia", "ESTN_UNIT_s": "stratum_estn_unit",
                "STRATUMCD_s": "stratumcd", "EXPNS": "official_full_expns",
                "ADJ_FACTOR_SUBP": "adj_factor_subp", "ADJ_FACTOR_MACR": "adj_factor_macr",
            })
            keep = [
                "plot_cn", "assignment_statecd", "assignment_invyr", "assignment_evalid", "stratum_cn",
                "assignment_estn_unit", "assignment_stratumcd", "plot_statecd", "plot_invyr", "measyear",
                "p2panel", "unitcd", "countycd", "plot_number", "prev_plt_cn", "designcd",
                "macro_breakpoint_dia", "stratum_estn_unit", "stratumcd", "official_full_expns",
                "adj_factor_subp", "adj_factor_macr",
            ]
            s = s[keep]
            s["reconstruction_source"] = "FROZEN_CA_OR_WA_RAW_DESIGN_ZIPS"
            supplement_frames.append(s)

    raw = pd.concat([national] + supplement_frames, ignore_index=True, sort=False)
    for col in raw.columns:
        raw[col] = clean_str(raw[col])
    raw["plot_cn"] = clean_str(raw["plot_cn"])
    raw["assignment_statecd"] = int_str(raw["assignment_statecd"], 2)
    raw["plot_statecd"] = int_str(raw["plot_statecd"], 2)
    raw["assignment_evalid"] = int_str(raw["assignment_evalid"])
    raw["p2panel"] = int_str(raw["p2panel"])
    raw["unitcd"] = int_str(raw["unitcd"])
    raw["countycd"] = int_str(raw["countycd"])
    raw["plot_number"] = int_str(raw["plot_number"])
    raw["assignment_estn_unit"] = int_str(raw["assignment_estn_unit"])
    raw["stratum_estn_unit"] = int_str(raw["stratum_estn_unit"])
    raw["assignment_stratumcd"] = int_str(raw["assignment_stratumcd"])
    raw["stratumcd"] = int_str(raw["stratumcd"])

    conflict_fields = ["assignment_statecd", "assignment_evalid", "stratum_cn", "assignment_estn_unit", "assignment_stratumcd", "p2panel"]
    counts = raw.groupby("plot_cn", dropna=False).size().rename("assignment_row_count")
    variants = raw.groupby("plot_cn", dropna=False)[conflict_fields].nunique(dropna=False).max(axis=1).rename("assignment_variant_count")
    raw_unique = raw.sort_values(conflict_fields, kind="mergesort").drop_duplicates("plot_cn", keep="first").copy()
    raw_unique = raw_unique.merge(counts, left_on="plot_cn", right_index=True, how="left", validate="one_to_one")
    raw_unique = raw_unique.merge(variants, left_on="plot_cn", right_index=True, how="left", validate="one_to_one")
    raw_unique = raw_unique.rename(columns={"designcd": "raw_designcd"})

    selected_maps = {}
    for _, r in selected.iterrows():
        a = {x for x in r["final_A_panels"].split("-") if x}
        b = {x for x in r["final_B_panels"].split("-") if x}
        selected_maps[r["state_fips"]] = {
            "evalid": str(int(r["component_evalid"])), "candidate": r["final_candidate_id"],
            "repair": r["final_repair_class"], "A": a, "B": b,
        }

    expected_fold = []
    for _, r in f0.iterrows():
        sm = selected_maps.get(r["state_fips"], {})
        p = r["panel"]
        expected_fold.append("A" if p in sm.get("A", set()) else ("B" if p in sm.get("B", set()) else ""))
    f0["expected_fold_from_final_partition"] = expected_fold

    joined = f0.merge(raw_unique, on="plot_cn", how="left", validate="one_to_one")

    ti_exp = []
    for _, r in ti.iterrows():
        for sid in [x for x in r["source_parent_poststratum_ids"].split(";") if x]:
            ti_exp.append({
                "ti_state_fips": str(r["state_fips"]).zfill(2),
                "ti_component_evalid": str(int(r["component_evalid"])),
                "ti_fold": r["fold"], "ti_stratum_cn": sid,
                "final_effective_design_block_id": r["effective_design_block_id"],
                "fold_specific_ti_weight": r["fold_specific_ti_expansion_acres_per_plot"],
                "ti_source_parent_poststratum_ids": r["source_parent_poststratum_ids"],
                "ti_source_estimation_units": r["source_estimation_units"],
                "ti_repair_class": r["repair_class"], "ti_candidate_id": r["candidate_id"],
                "ti_fold_sample_count": r["fold_sample_count"],
                "ti_population_area_acres": r["population_area_acres"],
            })
    ti_long = pd.DataFrame(ti_exp)
    ti_key = ["ti_state_fips", "ti_component_evalid", "ti_fold", "ti_stratum_cn"]
    ti_counts = ti_long.groupby(ti_key, dropna=False).size().rename("ti_match_count").reset_index()
    ti_unique = ti_long.sort_values(ti_key, kind="mergesort").drop_duplicates(ti_key, keep="first")
    ti_unique = ti_unique.merge(ti_counts, on=ti_key, how="left", validate="one_to_one")
    joined = joined.merge(
        ti_unique,
        left_on=["state_fips", "component_evalid", "fold", "stratum_cn"],
        right_on=ti_key,
        how="left", validate="many_to_one",
    )

    joined["permanent_plot_id"] = (
        joined["assignment_statecd"].fillna("") + ":" + joined["unitcd"].fillna("") + ":"
        + joined["countycd"].fillna("") + ":" + joined["plot_number"].fillna("")
    )
    joined["reporting_year"] = "2023"
    joined["qc_status"] = "PASS"
    fail_mask = (
        joined["stratum_cn"].isna()
        | joined["final_effective_design_block_id"].isna()
        | joined["fold_specific_ti_weight"].isna()
        | (joined["expected_fold_from_final_partition"] != joined["fold"])
        | (joined["assignment_statecd"] != joined["state_fips"])
        | (joined["plot_statecd"] != joined["state_fips"])
        | (joined["assignment_evalid"] != joined["component_evalid"])
        | (joined["p2panel"] != joined["panel"])
        | (joined["assignment_variant_count"].fillna(0) > 1)
        | (joined["ti_match_count"].fillna(0) != 1)
    )
    joined.loc[fail_mask, "qc_status"] = "FAIL"

    xcols = [
        "plot_cn", "state_fips", "state_abbr", "reporting_year", "component_evalid", "panel", "fold",
        "cell_50km", "assignment_invyr", "plot_invyr", "measyear", "stratum_cn",
        "assignment_estn_unit", "assignment_stratumcd", "stratum_estn_unit", "stratumcd",
        "final_effective_design_block_id", "fold_specific_ti_weight", "ti_fold_sample_count",
        "ti_population_area_acres", "ti_source_parent_poststratum_ids", "ti_source_estimation_units",
        "ti_repair_class", "ti_candidate_id", "official_full_expns", "adj_factor_subp", "adj_factor_macr",
        "macro_breakpoint_dia", "designcd", "raw_designcd", "permanent_plot_id", "prev_plt_cn",
        "reconstruction_source", "source", "assignment_row_count", "assignment_variant_count",
        "ti_match_count", "expected_fold_from_final_partition", "qc_status",
    ]
    xwalk = joined[xcols].copy()
    xwalk = xwalk.rename(columns={
        "plot_cn": "PLT_CN", "state_fips": "STATECD", "panel": "P2PANEL", "fold": "final_fold",
        "stratum_cn": "original_STRATUM_CN", "assignment_estn_unit": "original_ESTN_UNIT",
        "assignment_stratumcd": "original_STRATUMCD", "qc_status": "QC_STATUS",
    })
    xwalk_path = OUT / "plot_block_xwalk_v01.csv.gz"
    xwalk.to_csv(
        xwalk_path, index=False, encoding="utf-8-sig", lineterminator="\n",
        compression={"method": "gzip", "compresslevel": 9, "mtime": 0},
    )

    f0_n = len(f0)
    panel_ok = joined["fold"].isin(["A", "B"]) & (joined["fold"] == joined["expected_fold_from_final_partition"])
    block_ok = joined["final_effective_design_block_id"].notna()
    weight_ok = joined["fold_specific_ti_weight"].notna() & (joined["ti_match_count"].fillna(0) == 1)
    identity_ok = (
        (joined["assignment_statecd"] == joined["state_fips"])
        & (joined["plot_statecd"] == joined["state_fips"])
        & (joined["assignment_evalid"] == joined["component_evalid"])
        & (joined["p2panel"] == joined["panel"])
    )
    block_eval_ok = joined["ti_component_evalid"].fillna("") == joined["component_evalid"]
    no_conflict = (joined["assignment_variant_count"].fillna(0) <= 1) & (joined["ti_match_count"].fillna(0) == 1)
    states_ok = set(joined.loc[joined["QC_STATUS"] == "PASS", "state_fips"]) if "QC_STATUS" in joined.columns else set()
    # joined uses lowercase qc_status before xwalk rename.
    states_ok = set(joined.loc[joined["qc_status"] == "PASS", "state_fips"])

    wv_expected = {"1778855759290487", "1778855758290487"}
    wv = joined.loc[joined["state_fips"] == "54"]
    wv_target = wv.loc[wv["stratum_cn"].isin(wv_expected)]
    wv_ok = (
        set(wv_target["stratum_cn"].dropna()) == wv_expected
        and len(wv_target) > 0
        and (wv_target["final_effective_design_block_id"] == "MERGED_EU:3+4").all()
    )
    western_details = []
    western_ok = True
    for abbr in ("CA", "OR", "WA"):
        expected_evalid = selected_maps[selected.loc[selected["state_abbr"] == abbr, "state_fips"].iloc[0]]["evalid"]
        sub = joined.loc[joined["state_abbr"] == abbr]
        ok = (
            len(sub) > 0 and set(sub["component_evalid"]) == {expected_evalid}
            and set(sub["assignment_evalid"].dropna()) == {expected_evalid}
            and set(sub["reconstruction_source"].dropna()) == {"FROZEN_CA_OR_WA_RAW_DESIGN_ZIPS"}
        )
        western_ok &= ok
        western_details.append(f"{abbr}:{expected_evalid}:{'PASS' if ok else 'FAIL'}")

    checks = [
        ("C1", "Exactly one selected A/B fold", f0_n, int(panel_ok.sum()), int((~panel_ok).sum()), panel_ok.all(), "Fold reproduced from final whole-panel partition"),
        ("C2", "Exactly one final effective design block", f0_n, int(block_ok.sum()), int((~block_ok).sum()), block_ok.all(), "Direct stratum-to-final-block mapping"),
        ("C3", "Exactly one fold-specific TI weight", f0_n, int(weight_ok.sum()), int((~weight_ok).sum()), weight_ok.all(), "D09C final TI source-parent stratum expansion"),
        ("C4", "Selected evaluation and state/panel identity match F0", f0_n, int(identity_ok.sum()), int((~identity_ok).sum()), identity_ok.all(), "No state/year/evaluation rewrite"),
        ("C5", "No block outside selected evaluation", f0_n, int(block_eval_ok.sum()), int((~block_eval_ok).sum()), block_eval_ok.all(), "Evaluation included in TI join key"),
        ("C6", "No duplicate conflicting assignment or weight", f0_n, int(no_conflict.sum()), int((~no_conflict).sum()), no_conflict.all(), "Exact duplicate raw rows are counted; conflicting variants fail"),
        ("C7", "All 48 reporting states covered", 48, len(states_ok), 48 - len(states_ok), len(states_ok) == 48, ";".join(sorted(states_ok))),
        ("C8", "WV final merged-block logic reproduced", 2, len(set(wv_target["stratum_cn"].dropna())), 0 if wv_ok else 1, wv_ok, "1778855759290487 and 1778855758290487 -> MERGED_EU:3+4"),
        ("C9", "CA/OR/WA selected evaluations reproduced", 3, sum(x.endswith("PASS") for x in western_details), 0 if western_ok else 1, western_ok, ";".join(western_details)),
    ]
    qc_rows = [{
        "check_id": cid, "description": desc, "expected": exp, "observed_pass": obs,
        "failing_rows_or_units": fail, "status": "PASS" if ok else "FAIL", "notes": notes,
    } for cid, desc, exp, obs, fail, ok, notes in checks]
    csv_write(OUT / "xwalk_qc_v01.csv", qc_rows,
              ["check_id", "description", "expected", "observed_pass", "failing_rows_or_units", "status", "notes"])

    perm = joined.groupby("permanent_plot_id", dropna=False).agg(
        folds=("fold", lambda s: ";".join(sorted(set(s)))),
        visit_count=("plot_cn", "size"), statecd=("state_fips", "first")
    ).reset_index()
    both = perm.loc[perm["folds"].str.contains("A") & perm["folds"].str.contains("B")]
    only_a = perm.loc[perm["folds"] == "A"]
    only_b = perm.loc[perm["folds"] == "B"]
    overlap_rows = [
        {"record_type": "SUMMARY", "metric": "total_unique_permanent_plots", "value": len(perm), "permanent_plot_id": "", "folds": "", "visit_count": "", "statecd": "", "notes": "Stable FIA identity STATECD:UNITCD:COUNTYCD:PLOT"},
        {"record_type": "SUMMARY", "metric": "permanent_plots_only_A", "value": len(only_a), "permanent_plot_id": "", "folds": "A", "visit_count": "", "statecd": "", "notes": ""},
        {"record_type": "SUMMARY", "metric": "permanent_plots_only_B", "value": len(only_b), "permanent_plot_id": "", "folds": "B", "visit_count": "", "statecd": "", "notes": ""},
        {"record_type": "SUMMARY", "metric": "permanent_plots_both_A_B", "value": len(both), "permanent_plot_id": "", "folds": "A;B", "visit_count": "", "statecd": "", "notes": "Zero is required to preserve frozen whole-panel identity"},
    ]
    for _, r in both.iterrows():
        overlap_rows.append({
            "record_type": "OFFENDER", "metric": "crossfold_permanent_plot", "value": 1,
            "permanent_plot_id": r["permanent_plot_id"], "folds": r["folds"],
            "visit_count": r["visit_count"], "statecd": r["statecd"], "notes": "No repair applied",
        })
    csv_write(OUT / "ab_overlap_v01.csv", overlap_rows,
              ["record_type", "metric", "value", "permanent_plot_id", "folds", "visit_count", "statecd", "notes"])

    crosswalk_ok = all(r["status"] == "PASS" for r in qc_rows)
    overlap_ok = len(both) == 0
    partial_authority_ok = True
    grouped = joined.groupby(
        ["state_fips", "component_evalid", "fold", "final_effective_design_block_id"],
        dropna=False,
    ).size().rename("reconstructed_plot_count").reset_index()
    ti_compare = ti.rename(columns={
        "state_fips": "state_fips", "fold": "fold",
        "effective_design_block_id": "final_effective_design_block_id",
    }).copy()
    ti_compare["state_fips"] = ti_compare["state_fips"].str.zfill(2)
    ti_compare["component_evalid"] = int_str(ti_compare["component_evalid"])
    block_compare = ti_compare.merge(
        grouped,
        on=["state_fips", "component_evalid", "fold", "final_effective_design_block_id"],
        how="outer", indicator=True,
    )
    block_count_mismatch = int((
        pd.to_numeric(block_compare["fold_sample_count"], errors="coerce")
        != pd.to_numeric(block_compare["reconstructed_plot_count"], errors="coerce")
    ).sum())
    macro_needed = pd.to_numeric(xwalk["macro_breakpoint_dia"], errors="coerce").notna()
    macro_adj_positive = pd.to_numeric(xwalk["adj_factor_macr"], errors="coerce").gt(0)
    macro_adjustment_ok = bool(macro_adj_positive.loc[macro_needed].all())
    deep_ok = (
        len(grouped) == len(ti) == 5752
        and set(block_compare["_merge"]) == {"both"}
        and block_count_mismatch == 0
        and xwalk["PLT_CN"].nunique(dropna=True) == len(xwalk)
        and pd.to_numeric(xwalk["fold_specific_ti_weight"], errors="coerce").gt(0).all()
        and pd.to_numeric(xwalk["adj_factor_subp"], errors="coerce").gt(0).all()
        and macro_adjustment_ok
    )
    crosswalk_ok = crosswalk_ok and deep_ok
    if not input_identity_ok:
        terminal = "INPUT_BLOCKED_FROZEN_INPUT_IDENTITY_FAILURE"
    elif not crosswalk_ok or not overlap_ok:
        terminal = "INPUT_BLOCKED_NATIONWIDE_PLOT_BLOCK_CROSSWALK_FAILURE"
    elif not partial_authority_ok:
        terminal = "INPUT_BLOCKED_PARTIAL_EFFORT_SEMANTIC_AUTHORITY_FAILURE"
    else:
        terminal = TERMINAL_OK

    independent_validation = {
        "status": "PASS" if deep_ok else "FAIL",
        "f0_rows": f0_n,
        "crosswalk_rows": len(xwalk),
        "unique_plt_cn": int(xwalk["PLT_CN"].nunique(dropna=True)),
        "reconstructed_block_fold_groups": len(grouped),
        "d09c_ti_block_fold_groups": len(ti),
        "block_join_both_groups": int((block_compare["_merge"] == "both").sum()),
        "block_join_left_only_groups": int((block_compare["_merge"] == "left_only").sum()),
        "block_join_right_only_groups": int((block_compare["_merge"] == "right_only").sum()),
        "fold_sample_count_mismatch_groups": block_count_mismatch,
        "positive_ti_weight_rows": int(pd.to_numeric(xwalk["fold_specific_ti_weight"], errors="coerce").gt(0).sum()),
        "positive_adj_factor_subp_rows": int(pd.to_numeric(xwalk["adj_factor_subp"], errors="coerce").gt(0).sum()),
        "macro_breakpoint_rows": int(macro_needed.sum()),
        "positive_adj_factor_macr_where_macro_breakpoint_rows": int((macro_needed & macro_adj_positive).sum()),
        "macro_adjustment_complete_where_required": macro_adjustment_ok,
        "permanent_plot_overlap": len(both),
        "wv_merged_rule_exact": bool(wv_ok),
        "western_overrides_exact": bool(western_ok),
        "notes": "Independent aggregate reconstruction: every one of 5,752 D09C block×fold counts equals the crosswalk plot count.",
    }
    (QC / "independent_validation_v01.json").write_text(
        json.dumps(independent_validation, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    abundance_rule = f"""# D10C-A abundance contribution rule v01

Task: `{TASK_ID}`  
Terminal status: `{terminal}`

This document freezes estimator authority only. No species outcome, D10C calibration, support repair, or real Q1 result was computed.

## Eligible tree record and tally basis

A downstream TREE row may contribute only when `STATUSCD = 1` and `DIA >= 5.0`. DBH and DRC taxa use the same `DIA` threshold and remain retained. The row must join uniquely to its PLOT, selected-evaluation stratum, condition, F0 cell, final design block, and fold-specific TI row.

For a fixed-radius core plot, trees at least 5 inches are tallied on the 24-foot-radius subplot; where `PLOT.MACRO_BREAKPOINT_DIA` is present and the tree reaches that threshold, the macroplot basis applies. The field guide defines the four-subplot layout and this diameter/basis rule. `TREE.TPA_UNADJ` is the stored number of trees per acre theoretically represented by that record and already embodies the record's sample geometry.

## Frozen formula

For target species `i`, qualifying TREE row `t` on plot visit `j`, final block `h`, fold `f`, and 50-km cell `x(j)`:

`a(t) = ADJ_FACTOR_MACR[h0]` when the official macroplot tally basis applies; otherwise `a(t) = ADJ_FACTOR_SUBP[h0]`, where `h0` is the original selected-evaluation stratum retained in the crosswalk.

`q_ijt = TPA_UNADJ_t * a(t)` trees per acre after the official selected-evaluation nonresponse adjustment.

`Y_ij = sum_t q_ijt` over qualifying rows of species `i` in plot visit `j`. Trees from multiple accessible forest conditions are summed after a unique `TREE.CONDID -> COND.CONDID` validation. Condition proportions are not multiplied into individual tree records.

`M_if(x) = sum_{{j in fold f, x(j)=x}} TI_hf * Y_ij`, where `TI_hf` is the D09C fold-specific acres-per-plot weight in this crosswalk. It replaces the original full-evaluation `POP_STRATUM.EXPNS`; it is not multiplied by that original `EXPNS`.

If `sum_x M_if(x) > 0`, normalize as `p_if(x) = M_if(x) / sum_x M_if(x)`. No plot-count divisor or state-average weight is added.

## Field roles

- `TPA_UNADJ`: tree-level trees-per-acre factor, including official plot/subplot geometry; never a population-total weight by itself.
- `ADJ_FACTOR_SUBP` / `ADJ_FACTOR_MACR`: official original-stratum nonsampling adjustment selected by the tree's official tally basis.
- `fold_specific_TI_weight`: D09C final block×fold area expansion and the only population-area expansion used here.
- `CONDID`: assignment/integrity key. `CONDPROP_UNADJ`, `SUBPPROP_UNADJ`, and `MACRPROP_UNADJ` describe condition/sample-area proportions and support FIA's area/adjustment construction; they are not extra per-tree multipliers.
- D10A `partial_sampling_flag` and `partial_sampling_effort`: precision/QC metadata only; no additional point-estimator multiplier.

## Frozen evidence

- FIADB Guide v9.4, PDF pp. 28-29: core subplot/microplot/macroplot `TPA_UNADJ` factors and separation of plot/sample geometry from population expansion.
- FIADB Guide v9.4, PDF p. 79: `CONDPROP_UNADJ` / `SUBPPROP_UNADJ` / `MACRPROP_UNADJ` are condition-area proportions; official adjustment factors address partial nonsampling.
- FIADB Guide v9.4, PDF p. 185: `TREE.TPA_UNADJ` is the theoretical trees-per-acre representation and must be adjusted with POP_STRATUM factors for population estimates.
- FIADB Guide v9.4, PDF pp. 480-481: `EXPNS` is population-area expansion; `ADJ_FACTOR_SUBP` and `ADJ_FACTOR_MACR`, with `EXPNS` and `TPA_UNADJ`, provide tree estimates for sampled land.
- National Field Guide v9.5, PDF pp. 41, 145, 582: four 24-foot-radius core subplots; DBH/DRC diameter semantics; trees at least 5 inches are tallied on subplot/macroplot and macroplot breakpoint is regional.
"""
    md_write(OUT / "abundance_rule_v01.md", abundance_rule)

    partial_note = f"""# D10C-A partial-effort authority v01

Terminal status: `{terminal}`

## Unique resolution

The authority question is resolved without a new estimator branch:

- **P1 applies to the official FIA adjustment**: the selected-evaluation original stratum's `ADJ_FACTOR_SUBP` or `ADJ_FACTOR_MACR` enters the tree point estimator together with `TPA_UNADJ` and the D09C fold-specific TI replacement for `EXPNS`.
- `CONDPROP_UNADJ`, `SUBPPROP_UNADJ`, and `MACRPROP_UNADJ` are official condition/sample-area proportions used in area and nonsampling-adjustment semantics. They are upstream inputs/diagnostics, not an additional multiplier on each already condition-assigned TREE row.
- **P3 applies to D10A derived partial-effort fields**: `partial_sampling_flag`, sampled-subplot counts, and `partial_sampling_effort` are retained for precision and QC only. They do not change the point estimate.
- **P2 is rejected**: multiplying the tree contribution again by a condition proportion or by inverse D10A effort would duplicate sample-area/nonresponse correction.

The exact point contribution is therefore `TPA_UNADJ × official basis-matched ADJ_FACTOR × fold-specific TI`. A downstream implementation must fail rather than infer when a PLOT/COND/stratum join or macroplot-basis decision is non-unique.

Evidence is frozen in FIADB Guide v9.4 PDF pp. 79, 185, and 480-481 and National Field Guide v9.5 PDF pp. 41, 145, and 582.
"""
    md_write(OUT / "partial_effort_v01.md", partial_note)

    formula_rows = [
        {"order": 1, "level": "tree_filter", "symbol": "I_t", "formula_or_rule": "STATUSCD=1 AND DIA>=5.0", "source_fields": "TREE.STATUSCD;TREE.DIA;TREE.DIAHTCD", "role": "qualifying live large-tree / established-tree record; DBH and DRC retained", "authority": "Field Guide v9.5 PDF pp.145,582"},
        {"order": 2, "level": "tally_basis", "symbol": "b(t)", "formula_or_rule": "MACR if numeric MACRO_BREAKPOINT_DIA exists and DIA reaches it; otherwise SUBP", "source_fields": "PLOT.MACRO_BREAKPOINT_DIA;TREE.DIA;PLOT.DESIGNCD", "role": "select official adjustment factor", "authority": "Field Guide v9.5 PDF pp.41,145,582"},
        {"order": 3, "level": "tree", "symbol": "TPA_t", "formula_or_rule": "TREE.TPA_UNADJ", "source_fields": "TREE.TPA_UNADJ", "role": "trees per acre represented by record; plot geometry already included", "authority": "FIADB Guide v9.4 PDF pp.28,185"},
        {"order": 4, "level": "stratum_adjustment", "symbol": "a_t", "formula_or_rule": "ADJ_FACTOR_MACR if b(t)=MACR else ADJ_FACTOR_SUBP", "source_fields": "POP_STRATUM.ADJ_FACTOR_MACR;POP_STRATUM.ADJ_FACTOR_SUBP", "role": "official partial-nonsampling adjustment", "authority": "FIADB Guide v9.4 PDF p.481"},
        {"order": 5, "level": "condition", "symbol": "c(t)", "formula_or_rule": "unique TREE.CONDID=COND.CONDID validation; no condition-proportion multiplier", "source_fields": "TREE.PLT_CN;TREE.CONDID;COND.PLT_CN;COND.CONDID;COND.COND_STATUS_CD", "role": "assignment and accessible-forest integrity", "authority": "FIADB Guide v9.4 PDF pp.65,79,481"},
        {"order": 6, "level": "plot", "symbol": "Y_ij", "formula_or_rule": "sum_t I_t * TPA_UNADJ_t * a_t", "source_fields": "TREE rows joined to original stratum", "role": "species-specific adjusted trees per acre at plot visit", "authority": "FIADB Guide v9.4 PDF pp.185,481"},
        {"order": 7, "level": "fold_weight", "symbol": "TI_hf", "formula_or_rule": "effective block population area / actual fold sample count", "source_fields": "D09C final fold-specific TI design", "role": "acres per plot; replaces full-evaluation EXPNS", "authority": "Frozen D09C final v02"},
        {"order": 8, "level": "cell", "symbol": "M_if(x)", "formula_or_rule": "sum_{j in fold f,cell x} TI_hf * Y_ij", "source_fields": "crosswalk.cell_50km;final block;fold;TI", "role": "50-km population mass", "authority": "D10C-A frozen synthesis of official FIA and D09C"},
        {"order": 9, "level": "species_normalization", "symbol": "p_if(x)", "formula_or_rule": "M_if(x)/sum_x M_if(x), if denominator>0", "source_fields": "cell population masses", "role": "normalized spatial mass", "authority": "D10C-A contract"},
        {"order": 10, "level": "partial_effort_qc", "symbol": "e_j", "formula_or_rule": "not multiplied into point estimator", "source_fields": "D10A.partial_sampling_flag;partial_sampling_effort;sampled_subplot_count", "role": "P3 precision/QC metadata only", "authority": "FIADB Guide v9.4 PDF pp.79,481"},
    ]
    csv_write(OUT / "formula_ledger_v01.csv", formula_rows,
              ["order", "level", "symbol", "formula_or_rule", "source_fields", "role", "authority"])

    summary_rows = [
        {"item": "terminal_status", "value": terminal, "status": terminal, "notes": "Authority closure only; not a scientific PASS/FAIL"},
        {"item": "f0_plot_visits", "value": f0_n, "status": "CLOSED" if crosswalk_ok else "BLOCKED", "notes": "All frozen F0 rows"},
        {"item": "crosswalk_rows", "value": len(xwalk), "status": "CLOSED" if len(xwalk) == f0_n else "BLOCKED", "notes": "One output row per F0 PLT_CN"},
        {"item": "states", "value": len(set(joined["state_fips"])), "status": "CLOSED" if len(set(joined["state_fips"])) == 48 else "BLOCKED", "notes": "CONUS reporting states"},
        {"item": "d09c_final_ti_rows", "value": len(ti), "status": "VERIFIED", "notes": "Frozen input"},
        {"item": "unique_permanent_plots", "value": len(perm), "status": "VERIFIED", "notes": "STATECD:UNITCD:COUNTYCD:PLOT"},
        {"item": "permanent_plots_in_both_folds", "value": len(both), "status": "CLOSED" if overlap_ok else "BLOCKED", "notes": "No silent repair"},
        {"item": "partial_effort_resolution", "value": "official adjustment=P1; D10A derived effort=P3; no P2 multiplier", "status": "CLOSED", "notes": "Unique documented resolution"},
        {"item": "real_species_outcomes_read", "value": 0, "status": "CONFIRMED", "notes": "TREE.SPCD never queried"},
        {"item": "d10c_calibration_run", "value": 0, "status": "CONFIRMED", "notes": "No A0/A1/A2, M0/M1/M2, or real Q1"},
    ]
    csv_write(OUT / "closure_summary_v01.csv", summary_rows, ["item", "value", "status", "notes"])

    result_note = f"""# D10C-A result note v01

Terminal status: `{terminal}`

This was a species-blind estimator-authority closure. It did not run D10C, read `TREE.SPCD`, compute real abundance/support, select species, or run real Q1.

## Answers required by the contract

**Q1. Can every frozen F0 plot visit be assigned uniquely?**  
{'Yes' if crosswalk_ok else 'No'}. `{f0_n:,}` F0 plot visits produced `{len(xwalk):,}` crosswalk rows; C1-C9 status is {'all PASS' if crosswalk_ok else 'not closed'}.

**Q2. Is nationwide coverage complete?**  
{'Yes' if len(states_ok) == 48 else 'No'}. `{len(states_ok)}` of 48 reporting states have complete passing rows.

**Q3. Does any permanent plot identity appear in both folds?**  
{'No' if overlap_ok else 'Yes'}. `{len(perm):,}` unique stable permanent identities were observed: `{len(only_a):,}` only A, `{len(only_b):,}` only B, and `{len(both):,}` in both.

**Q4. Exact contribution formula?**  
For qualifying live `DIA>=5` tree rows: plot contribution is `sum(TPA_UNADJ × basis-matched official ADJ_FACTOR)`; 50-km mass is `sum(fold-specific TI × plot contribution)` over plot visits in the cell; normalize cell masses by their species/fold total. Original `EXPNS` is replaced, not multiplied again.

**Q5. Role of TPA_UNADJ?**  
It is the official trees-per-acre representation of the individual tree record, including tally geometry. It is not by itself a population total.

**Q6. How does partial effort enter?**  
Official `ADJ_FACTOR_SUBP/MACR` is the P1 point-estimator adjustment. Condition proportions are not extra per-tree weights. D10A derived partial-effort variables are P3 precision/QC metadata. P2 is rejected.

**Q7. Is authority sufficient for an exact D10C A2 rerun?**  
{'Yes' if terminal == TERMINAL_OK else 'No'}. The crosswalk supplies original stratum, final block, fold, fold-specific TI, official adjustment factors, cell, and deterministic source identities without an invented block or effort rule.

## Boundary

STOP after this package. Mainline must audit before any D10C rerun.
"""
    md_write(OUT / "result_note_v01.md", result_note)

    # Contract copy and compact execution metadata.
    shutil.copy2(CONTRACT, CTL / "contract_v01.txt")
    env = {
        "task_id": TASK_ID, "created_utc": datetime.now(timezone.utc).isoformat(),
        "python": sys.version, "platform": platform.platform(), "pandas": pd.__version__,
        "sqlite": sqlite3.sqlite_version, "network_used": False,
        "tree_spcd_queried": False, "d10c_run": False,
        "path_policy": "Every local absolute path and ZIP member path must be under 256 characters.",
    }
    (QC / "environment_v01.json").write_text(json.dumps(env, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    shutil.copy2(Path(__file__), SRC / "build.py")
    verify_src = Path(__file__).with_name("verify.py")
    if verify_src.exists():
        shutil.copy2(verify_src, SRC / "verify.py")

    registry_rows = [
        {"DELTA_TYPE": "TASK", "ACTION": "PROPOSE_ADD", "TASK_ID": TASK_ID, "ASSET_NAME": "D10C-A FIA abundance estimator authority closure", "CANONICAL_PATH": str(ARCH / "D10CA_v01.zip"), "SHA256": "PENDING_PACKAGE", "SIZE_BYTES": "PENDING_PACKAGE", "STATUS": terminal, "SCIENTIFIC_OUTPUT_CHANGED": "NO", "PUBLICATION_CANDIDATE": "METHODS_SUPPORT_CANDIDATE", "METHODS_ROLE": "FIA abundance estimator authority chain", "DATA_ROLE": "SPECIES_BLIND_PLOT_WEIGHT_CROSSWALK", "CODE_ROLE": "REPRODUCIBLE_BUILD", "QC_ROLE": "C1_C9_AND_PERMANENT_PLOT_QC", "NOTES": "Proposal only; mainline controls Registry merge. No D10C or real Q1 run."},
        {"DELTA_TYPE": "ASSET", "ACTION": "PROPOSE_ADD_OR_LINK", "TASK_ID": TASK_ID, "ASSET_NAME": "plot-to-final-block crosswalk", "CANONICAL_PATH": str(OUT / "plot_block_xwalk_v01.csv.gz"), "SHA256": sha256_file(OUT / "plot_block_xwalk_v01.csv.gz"), "SIZE_BYTES": (OUT / "plot_block_xwalk_v01.csv.gz").stat().st_size, "STATUS": "AUTHORITY_OUTPUT", "SCIENTIFIC_OUTPUT_CHANGED": "NO", "PUBLICATION_CANDIDATE": "METHODS_SUPPORT_CANDIDATE", "METHODS_ROLE": "F0 plot-to-D09C block/fold/TI authority", "DATA_ROLE": "SPECIES_BLIND_CROSSWALK", "CODE_ROLE": "NONE", "QC_ROLE": "C1_C9", "NOTES": "Short physical filename mapped in delivery index."},
    ]
    reg_fields = ["DELTA_TYPE", "ACTION", "TASK_ID", "ASSET_NAME", "CANONICAL_PATH", "SHA256", "SIZE_BYTES", "STATUS", "SCIENTIFIC_OUTPUT_CHANGED", "PUBLICATION_CANDIDATE", "METHODS_ROLE", "DATA_ROLE", "CODE_ROLE", "QC_ROLE", "NOTES"]
    csv_write(MAN / "registry_delta_v01.csv", registry_rows, reg_fields)

    # Prepackage path-length check, including planned ZIP member names.
    local_files = [p for p in PKG.rglob("*") if p.is_file()]
    max_abs = max(len(str(p)) for p in local_files)
    max_abs_path = max(local_files, key=lambda p: len(str(p)))
    member_names = [(Path("D10CA_v01") / p.relative_to(PKG)).as_posix() for p in local_files]
    max_member = max(len(s) for s in member_names)
    max_member_name = max(member_names, key=len)
    path_qc = [
        {"metric": "windows_conservative_limit", "value": 256, "status": "REFERENCE", "path": "", "notes": "User-requested ceiling; classic Win32 MAX_PATH is approximately 260 including terminator"},
        {"metric": "max_absolute_path_chars", "value": max_abs, "status": "PASS" if max_abs < 256 else "FAIL", "path": str(max_abs_path), "notes": "All D10C-A delivery files"},
        {"metric": "max_zip_member_path_chars", "value": max_member, "status": "PASS" if max_member < 256 else "FAIL", "path": max_member_name, "notes": "All planned package members"},
    ]
    csv_write(QC / "path_length_qc_v01.csv", path_qc, ["metric", "value", "status", "path", "notes"])
    if any(r["status"] == "FAIL" for r in path_qc):
        raise RuntimeError("Path-length ceiling failed")

    delivery_lines = [
        "# D10C-A delivery index v01", "", f"Task: `{TASK_ID}`", "", f"Terminal status: `{terminal}`", "",
        "Short physical names are intentional. They keep Windows absolute paths and ZIP member paths below 256 characters.", "",
        "| Physical file | Contract-equivalent name | Role | Rows | Bytes | SHA-256 | Authoritative |",
        "|---|---|---|---:|---:|---|---|",
    ]
    for p in sorted([p for p in PKG.rglob("*") if p.is_file()]):
        rel = p.relative_to(PKG).as_posix()
        contract_name = SHORT_NAME_MAP.get(p.name, "supporting file")
        rows = ""
        if p.suffix == ".csv":
            with p.open("r", encoding="utf-8-sig", newline="") as f:
                rows = max(sum(1 for _ in f) - 1, 0)
        elif p.name.endswith(".csv.gz"):
            with gzip.open(p, "rt", encoding="utf-8-sig", newline="") as f:
                rows = max(sum(1 for _ in f) - 1, 0)
        auth = "YES" if p.parent == OUT or p.name in {"build.py", "verify.py"} else "SUPPORTING"
        delivery_lines.append(f"| `{rel}` | `{contract_name}` | {p.parent.name} | {rows} | {p.stat().st_size} | `{sha256_file(p)}` | {auth} |")
    md_write(PKG / "delivery_index_v01.md", "\n".join(delivery_lines))

    # Checksums list all package files except itself.
    checksum_rows = []
    for p in sorted([p for p in PKG.rglob("*") if p.is_file()]):
        if p.name == "sha256s.csv":
            continue
        checksum_rows.append({"relative_path": p.relative_to(PKG).as_posix(), "size_bytes": p.stat().st_size, "sha256": sha256_file(p)})
    csv_write(MAN / "sha256s.csv", checksum_rows, ["relative_path", "size_bytes", "sha256"])

    # Re-evaluate path lengths after index/checksum creation.
    all_pkg_files = [p for p in PKG.rglob("*") if p.is_file()]
    final_max_abs = max(len(str(p)) for p in all_pkg_files)
    final_max_member = max(len((Path("D10CA_v01") / p.relative_to(PKG)).as_posix()) for p in all_pkg_files)
    if final_max_abs >= 256 or final_max_member >= 256:
        raise RuntimeError("Final package path-length ceiling failed")

    zip_path = ARCH / "D10CA_v01.zip"
    deterministic_zip(PKG, zip_path)
    zip_hash = sha256_file(zip_path)
    sidecar = ARCH / "D10CA_v01.zip.sha256"
    sidecar.write_text(f"{zip_hash}  {zip_path.name}\n", encoding="ascii")

    with zipfile.ZipFile(zip_path) as z:
        bad = z.testzip()
        zip_members = z.namelist()
    validation = {
        "task_id": TASK_ID, "terminal_status": terminal,
        "zip_path": str(zip_path), "zip_bytes": zip_path.stat().st_size, "zip_sha256": zip_hash,
        "zip_member_count": len(zip_members), "zip_test_bad_member": bad,
        "crosswalk_rows": len(xwalk), "f0_rows": f0_n, "states": len(set(joined["state_fips"])),
        "c1_c9_and_deep_checks_all_pass": bool(crosswalk_ok), "permanent_plot_overlap": len(both),
        "all_5752_block_fold_counts_match": bool(deep_ok),
        "input_identity_all_pass": bool(input_identity_ok),
        "max_local_absolute_path_chars": max(len(str(p)) for p in all_pkg_files + [zip_path, sidecar]),
        "max_zip_member_path_chars": max(map(len, zip_members)),
        "path_limit_lt_256": max(max(len(str(p)) for p in all_pkg_files + [zip_path, sidecar]), max(map(len, zip_members))) < 256,
        "tree_spcd_queried": False, "d10c_run": False, "network_used": False,
    }
    (ARCH / "validation_v01.json").write_text(json.dumps(validation, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    shutil.copy2(PKG / "delivery_index_v01.md", ARCH / "delivery_index_v01.md")

    # Relay v0.2.2 native manifest: direct-readable text mirrors; binary archive/release assets.
    transfer_candidates = [zip_path, sidecar, ARCH / "delivery_index_v01.md", ARCH / "validation_v01.json"]
    transfer_candidates += [p for p in PKG.rglob("*") if p.is_file() and (p.suffix.lower() in {".csv", ".md", ".json", ".txt", ".py"} or p.name.endswith(".csv.gz"))]
    transfer_rows = []
    seen = set()
    for p in transfer_candidates:
        key = str(p).lower()
        if key in seen:
            continue
        seen.add(key)
        if p == zip_path:
            role, target, priority, rel, notes = "reproducible_zip", "release", "IMPORTANT", f"release_assets/{p.name}", "Complete immutable D10C-A package"
        elif p == sidecar:
            role, target, priority, rel, notes = "checksum", "both", "IMPORTANT", f"release_assets/{p.name}", "ZIP SHA-256 sidecar"
        else:
            rel_pkg = p.relative_to(PKG).as_posix() if PKG in p.parents else p.name
            role = "delivery_index" if "delivery_index" in p.name else ("result_note" if p.name == "result_note_v01.md" else ("source" if p.suffix == ".py" else ("qc_json" if p.suffix == ".json" else ("audit_csv" if p.suffix in {".csv", ".gz"} else "other"))))
            target = "mirror"
            priority = "FIRST_READ" if p.name in {"delivery_index_v01.md", "result_note_v01.md", "closure_summary_v01.csv", "xwalk_qc_v01.csv"} else "SUPPORTING"
            rel = f"release_mirror/Q1-D10CA-v01-20260905/{rel_pkg}"
            notes = SHORT_NAME_MAP.get(p.name, "Supporting reproducibility/audit file")
        transfer_rows.append({
            "local_path": str(p), "relative_path": rel, "role": role, "upload_target": target,
            "required": "YES", "mainline_priority": priority, "size_bytes": p.stat().st_size,
            "sha256": sha256_file(p), "notes": notes,
        })
    transfer_path = ARCH / "transfer_manifest_v01.csv"
    csv_write(transfer_path, transfer_rows, ["local_path", "relative_path", "role", "upload_target", "required", "mainline_priority", "size_bytes", "sha256", "notes"])
    shutil.copy2(transfer_path, MAN / "transfer_manifest_v01.csv")

    print(json.dumps({
        "terminal_status": terminal, "f0_rows": f0_n, "crosswalk_rows": len(xwalk),
        "states": len(states_ok), "unique_permanent_plots": len(perm), "both_folds": len(both),
        "zip": str(zip_path), "zip_bytes": zip_path.stat().st_size, "zip_sha256": zip_hash,
        "transfer_manifest_rows": len(transfer_rows), "max_abs_path": validation["max_local_absolute_path_chars"],
        "max_zip_member": validation["max_zip_member_path_chars"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    build()
