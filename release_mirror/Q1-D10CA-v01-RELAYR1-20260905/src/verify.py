from __future__ import annotations

import csv
import gzip
import hashlib
import json
import sys
import zipfile
from pathlib import Path


ARCH = Path(r"C:\range_paper\10_archive\d10ca")
ZIP = ARCH / "D10CA_v01.zip"
SIDECAR = ARCH / "D10CA_v01.zip.sha256"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while b := f.read(16 * 1024 * 1024):
            h.update(b)
    return h.hexdigest()


def main() -> None:
    expected = SIDECAR.read_text(encoding="ascii").split()[0]
    actual = sha256_file(ZIP)
    errors = []
    if actual != expected:
        errors.append("ZIP SHA-256 mismatch")
    with zipfile.ZipFile(ZIP) as z:
        bad = z.testzip()
        if bad:
            errors.append(f"Bad ZIP member: {bad}")
        names = z.namelist()
        if max(map(len, names)) >= 256:
            errors.append("ZIP member path >=256 characters")
        xname = [n for n in names if n.endswith("out/plot_block_xwalk_v01.csv.gz")]
        qname = [n for n in names if n.endswith("out/xwalk_qc_v01.csv")]
        iname = [n for n in names if n.endswith("qc/independent_validation_v01.json")]
        sname = [n for n in names if n.endswith("manifest/sha256s.csv")]
        if len(xname) != 1 or len(qname) != 1:
            errors.append("Required crosswalk/QC members not unique")
        else:
            with gzip.open(z.open(xname[0]), mode="rt", encoding="utf-8-sig", newline="") as f:
                row_count = sum(1 for _ in f) - 1
            with z.open(qname[0]) as raw:
                rows = list(csv.DictReader((line.decode("utf-8-sig") for line in raw)))
            if row_count != 338619:
                errors.append(f"Crosswalk rows {row_count}, expected 338619")
            if len(rows) != 9 or any(r["status"] != "PASS" for r in rows):
                errors.append("C1-C9 not all PASS")
        if len(iname) != 1:
            errors.append("Independent validation member not unique")
        else:
            with z.open(iname[0]) as f:
                iv = json.load(f)
            if iv.get("status") != "PASS" or iv.get("fold_sample_count_mismatch_groups") != 0:
                errors.append("Independent block-count validation failed")
        if len(sname) != 1:
            errors.append("Internal SHA256SUMS member not unique")
        else:
            rows = list(csv.DictReader(z.read(sname[0]).decode("utf-8-sig").splitlines()))
            for row in rows:
                member = "D10CA_v01/" + row["relative_path"]
                if member not in names:
                    errors.append(f"Checksum target missing: {member}")
                    continue
                data = z.read(member)
                if len(data) != int(row["size_bytes"]):
                    errors.append(f"Size mismatch: {member}")
                if hashlib.sha256(data).hexdigest() != row["sha256"]:
                    errors.append(f"SHA-256 mismatch: {member}")
    result = {"status": "PASS" if not errors else "FAIL", "zip_sha256": actual, "errors": errors}
    print(json.dumps(result, indent=2))
    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
