#!/usr/bin/env python3
"""Read-only, species-blind preflight for frozen D09C FIADB design inputs."""

from __future__ import annotations

import csv
import json
import sqlite3
from pathlib import Path


ROOT = Path(r"C:\range_paper")
DB = ROOT / "99_tmp" / "elig_v02" / "SQLite_FIADB_ENTIRE.db"
STATE_LEDGER = ROOT / "03_doc" / "D09C_SPECIES_BLIND_DESIGN_INPUTS_v01" / "upstream_d09b" / "D09B_2023_EVALID_STATE_LEDGER_v01.csv"
ALLOWED = {
    "POP_EVAL_GRP", "POP_EVAL_TYP", "POP_EVAL", "POP_ESTN_UNIT",
    "POP_STRATUM", "POP_PLOT_STRATUM_ASSGN", "PLOT", "SURVEY",
}


def main() -> None:
    with STATE_LEDGER.open("r", encoding="utf-8-sig", newline="") as handle:
        states = {int(row["state_fips"]): {"abbr": row["state_abbr"], "name": row["state_name"]} for row in csv.DictReader(handle)}
    accessed: set[str] = set()

    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)

    def authorizer(action, arg1, arg2, dbname, source):
        if action == sqlite3.SQLITE_READ:
            table = (arg1 or "").upper()
            if table not in ALLOWED:
                return sqlite3.SQLITE_DENY
            accessed.add(table)
        return sqlite3.SQLITE_OK

    con.set_authorizer(authorizer)
    group_rows = list(con.execute(
        "SELECT STATECD, EVAL_GRP, CN, EVAL_GRP_DESCR FROM POP_EVAL_GRP "
        "WHERE STATECD BETWEEN 1 AND 56 AND (EVAL_GRP % 10000) IN (2022, 2023)"
    ))
    coverage = {}
    for year in (2022, 2023):
        got = {int(r[0]) for r in group_rows if int(r[1]) % 10000 == year and int(r[0]) in states}
        coverage[str(year)] = {
            "count": len(got),
            "missing": [{"state_fips": code, **states[code]} for code in sorted(set(states) - got)],
        }

    texas = []
    sql = """
    SELECT g.EVAL_GRP, e.EVALID, e.CN AS EVAL_CN, e.EVAL_DESCR,
           u.CN AS ESTN_UNIT_CN, u.ESTN_UNIT, u.ESTN_UNIT_DESCR,
           u.AREA_USED, u.AREATOT_EU, u.AREALAND_EU
    FROM POP_EVAL_GRP g
    JOIN POP_EVAL_TYP t ON t.EVAL_GRP_CN = g.CN AND t.EVAL_TYP = 'EXPVOL'
    JOIN POP_EVAL e ON e.CN = t.EVAL_CN
    JOIN POP_ESTN_UNIT u ON u.EVAL_CN = e.CN
    WHERE g.EVAL_GRP IN (482022, 482023)
    ORDER BY g.EVAL_GRP, e.EVALID, u.ESTN_UNIT
    """
    columns = None
    cursor = con.execute(sql)
    columns = [d[0] for d in cursor.description]
    texas = [dict(zip(columns, row)) for row in cursor]

    counts = {}
    for table in sorted(ALLOWED):
        counts[table] = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    con.close()

    result = {
        "status": "PASS",
        "mode": "read-only species-blind FIADB design preflight",
        "state_count": len(states),
        "reporting_group_coverage": coverage,
        "texas_actual_expvol_estimation_units": texas,
        "allowed_tables": sorted(ALLOWED),
        "accessed_tables": sorted(accessed),
        "table_row_counts": counts,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
