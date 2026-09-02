#!/usr/bin/env python3
"""Read-only D08C1 preflight inspection of the frozen FIA and D08B1 inputs."""

from __future__ import annotations

import csv
import json
import sqlite3
from collections import Counter
from pathlib import Path


ROOT = Path(r"C:\range_paper")
DB = ROOT / "99_tmp" / "elig_v02" / "SQLite_FIADB_ENTIRE.db"
TAX = ROOT / "04_derived" / "tax_v02"


def read_csv(name: str) -> list[dict[str, str]]:
    with (TAX / name).open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    connection = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    try:
        schema = {}
        for table in ("TREE", "PLOT", "COND", "SURVEY", "REF_SPECIES"):
            schema[table] = [row[1] for row in connection.execute(f"PRAGMA table_info({table})")]
        indexes = {
            table: [row[1] for row in connection.execute(f"PRAGMA index_list({table})")]
            for table in ("TREE", "PLOT", "COND")
        }
        states = [
            {"state_code": int(code), "state_ab": ab, "state_name": name}
            for code, ab, name in connection.execute(
                "SELECT DISTINCT STATECD, STATEAB, STATENM FROM SURVEY ORDER BY STATECD"
            )
        ]
        table_counts = {
            table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in ("TREE", "PLOT", "COND")
        }
    finally:
        connection.close()

    distribution = read_csv("Q1_WCVP_NATIVE_DISTRIBUTION_LONG_v02.csv")
    wcvp_areas = sorted({row["area"] for row in distribution})
    state_matches = []
    for row in states:
        matches = [area for area in wcvp_areas if area == row["state_name"]]
        state_matches.append({**row, "exact_wcvp_area_matches": matches, "match_count": len(matches)})

    code_map = read_csv("Q1_FIA_CODE_TO_ANALYSIS_SPECIES_v02.csv")
    species = read_csv("Q1_ANALYSIS_SPECIES_MASTER_v02.csv")
    drc = read_csv("Q1_DRC_PROTOCOL_v02.csv")
    report = {
        "status": "PASS",
        "database_bytes": DB.stat().st_size,
        "table_counts": table_counts,
        "schema": schema,
        "indexes": indexes,
        "fia_states": states,
        "state_exact_crosswalk": state_matches,
        "state_crosswalk_failures": [row for row in state_matches if row["match_count"] != 1],
        "d08b1_rows": {
            "code_map": len(code_map),
            "analysis_species": len(species),
            "drc_protocol": len(drc),
            "wcvp_distribution": len(distribution),
        },
        "code_map_unique_codes": len({row["fia_species_code"] for row in code_map}),
        "ordinary_code_count": sum(row["ordinary_analysis_species_flag"] == "1" for row in code_map),
        "no_analysis_code_count": sum(row["ordinary_analysis_species_flag"] != "1" for row in code_map),
        "diameter_basis_counts": dict(Counter(row["diameter_measurement_basis"] for row in code_map)),
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
