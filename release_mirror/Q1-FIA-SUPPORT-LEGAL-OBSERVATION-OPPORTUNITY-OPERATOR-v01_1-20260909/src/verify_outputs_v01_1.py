from __future__ import annotations

import csv
import gzip
import hashlib
import json
import sqlite3
import zipfile
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "Q1_FIA_SUPPORT_MEASUREMENT_SUBSTRATE_CANDIDATE_v01_1.sqlite"
F0 = ROOT / "LEGAL_OPPORTUNITY_F0_CLASSIFICATION_v01_1.csv.gz"
ZIP = ROOT / "Q1_FIA_SUPPORT_LEGAL_OBSERVATION_OPPORTUNITY_OPERATOR_v01_1.zip"
QC_OUT = Path(r"C:\range_paper\99_tmp\q1_fia_support_legal_opportunity_operator_v01_1\independent_output_qc.json")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


with gzip.open(F0, "rt", encoding="utf-8", newline="") as f:
    reader = csv.DictReader(f)
    required = {"PLT_CN", "fold", "classification_status", "legal_opportunity_class", "unresolved_reason", "species_blind"}
    assert required <= set(reader.fieldnames or [])
    forbidden = {"SPCD", "SPECIES_IDENTITY", "SPECIES_OUTCOME", "SUPPORT", "ABUNDANCE", "Q1_RESULT"}
    assert not (forbidden & set(reader.fieldnames or []))
    n = 0
    ids = set()
    folds = Counter()
    statuses = Counter()
    classes = Counter()
    unresolved = Counter()
    for row in reader:
        n += 1
        ids.add(row["PLT_CN"])
        folds[row["fold"]] += 1
        statuses[row["classification_status"]] += 1
        classes[row["legal_opportunity_class"]] += 1
        if row["unresolved_reason"]:
            unresolved[row["unresolved_reason"]] += 1
        assert row["species_blind"] == "YES"
assert n == 338619
assert len(ids) == 338619
assert folds == Counter({"B": 203106, "A": 135513})
assert sum(statuses.values()) == 338619
assert statuses["FULLY_CLASSIFIED"] + statuses["EXPLICITLY_UNRESOLVED"] == 338619
assert sum(unresolved.values()) == statuses["EXPLICITLY_UNRESOLVED"]

con = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
integrity = con.execute("PRAGMA integrity_check").fetchone()[0]
tables = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
expected_tables = {"metadata", "f0_linkage", "plot_opportunity_source", "subplot_opportunity_source", "condition_opportunity_source", "subplot_condition_relation"}
assert tables == expected_tables
assert integrity == "ok"
db_counts = {t: con.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0] for t in expected_tables if t != "metadata"}
assert db_counts == {
    "f0_linkage": 338619,
    "plot_opportunity_source": 334387,
    "subplot_opportunity_source": 1337548,
    "condition_opportunity_source": 405427,
    "subplot_condition_relation": 1384227,
}
all_columns = {r[1].upper() for t in tables for r in con.execute(f'PRAGMA table_info("{t}")')}
assert "SPCD" not in all_columns
assert not any("SPECIES" in name for name in all_columns)
assert not any("LAT" in name or "LON" in name for name in all_columns)
con.close()

with (ROOT / "TRANSFER_MANIFEST_v01_1.csv").open(encoding="utf-8", newline="") as f:
    transfer = list(csv.DictReader(f))
assert transfer
assert {r["upload_target"] for r in transfer} == {"mirror"}

with (ROOT / "SHA256SUMS.csv").open(encoding="utf-8", newline="") as f:
    manifest = list(csv.DictReader(f))
for row in manifest:
    p = ROOT / row["relative_path"]
    assert p.is_file()
    data = p.read_bytes()
    assert sha256_bytes(data) == row["sha256"]
    assert len(data) == int(row["size_bytes"])

with zipfile.ZipFile(ZIP) as zf:
    names = set(zf.namelist())
    assert "SHA256SUMS.csv" in names
    for row in manifest:
        assert row["relative_path"] in names
        data = zf.read(row["relative_path"])
        assert sha256_bytes(data) == row["sha256"]
        assert len(data) == int(row["size_bytes"])

result = {
    "status": "PASS",
    "f0_rows": n,
    "unique_plt_cn": len(ids),
    "fold_counts": dict(folds),
    "classification_status_counts": dict(statuses),
    "class_counts": dict(sorted(classes.items())),
    "unresolved_counts": dict(sorted(unresolved.items())),
    "layer2_integrity": integrity,
    "layer2_row_counts": db_counts,
    "transfer_upload_targets": sorted({r["upload_target"] for r in transfer}),
    "sha_manifest_rows": len(manifest),
    "zip_member_count": len(names),
}
QC_OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(result, indent=2, sort_keys=True))
