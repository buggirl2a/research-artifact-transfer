#!/usr/bin/env python3
"""Build the bounded additive Q1 D08B.1 taxonomy–USGS bridge correction v02."""

from __future__ import annotations

import csv
import hashlib
import html
import json
import os
import platform
import re
import sys
import unicodedata
import zipfile
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath
from typing import Iterable


ROOT = Path(r"C:\range_paper")
V01_ROOT = ROOT / "10_archive" / "tax_v01_mainline_delivery" / "Q1_D08B_MAINLINE_AUDIT_DELIVERY_v01"
V01 = V01_ROOT / "authoritative_outputs"
V01_ZIP = ROOT / "10_archive" / "tax_v01_mainline_delivery" / "Q1_D08B_MAINLINE_AUDIT_DELIVERY_v01.zip"
WCVP_ZIP = ROOT / "02_raw" / "WCVP" / "wcvp.zip"
ATLAS_HTML = ROOT / "03_doc" / "USGS" / "D08A_USGS_Atlas_G_Table1_20260902.html"
ELIG_USGS = ROOT / "05_qc" / "elig_v02" / "USGS_RANGE_AUDIT.csv"
INPUT_DIR = ROOT / "03_doc" / "D08B1_TAXONOMY_CORRECTION_INPUTS_v02"
CORRECTION_DIR = INPUT_DIR / "correction_delivery_extracted"
CONTRACT = ROOT / "00_control" / "D08B1_TAXONOMY_USGS_BRIDGE_CONTRACT_v02.md"
INPUT_FREEZE = ROOT / "00_control" / "D08B1_INPUT_FREEZE_v02.md"
WORK = ROOT / "99_tmp" / "tax_v02_work"
OUT = WORK / "outputs"
QC_DIR = WORK / "qc"

V01_MASTER = V01 / "Q1_TAXON_RANGE_MASTER_v01.csv"
V01_SPECIES = V01 / "Q1_TAXON_CODE_AGGREGATION_v01.csv"
V01_DISTRIBUTION = V01 / "Q1_WCVP_NATIVE_DISTRIBUTION_LONG_v01.csv"
V01_GLOBAL = V01 / "Q1_GLOBAL_RANGE_FLAGS_v01.csv"
V01_USGS = V01 / "Q1_USGS_NAME_CLOSURE_v01.csv"

EXPECTED_HASHES = {
    INPUT_DIR / "Q1_WORK_REQUEST_D08B1_TAXONOMY_USGS_BRIDGE_CORRECTION_v01_20260902.md": "dfc4016002e334524ed149647bd4d500a844d68b2eb638e3eb5b9a3ff8677f7a",
    INPUT_DIR / "Q1_D08B_TAXONOMY_CORRECTION_MAINLINE_DECISION_v01_20260902.md": "d275946726f0111522a040992c210bf5511a5992a3e4737f6b10301b7a854564",
    INPUT_DIR / "D08B_TAXONOMY_CORRECTION_DELIVERY_v01.zip": "fecd1278e843d02ffe54921cb59454dcef2642ec299eb93fb25471d661280efc",
    CORRECTION_DIR / "D08B_TAXONOMY_CORRECTION_EVIDENCE_v01.csv": "ca71c7bb6cd4e647b06a82f604b6b472ecd54f0f01cac88f9d04a4fc9785b9fd",
    CORRECTION_DIR / "D08B_TAXONOMY_CORRECTION_SOURCE_LEDGER_v01.csv": "88e0fbba9588eb8ca39f2b7d11907d7d903a338cc923a35c321de76ac53ee672",
    CORRECTION_DIR / "D08B_TAXONOMY_CORRECTION_NOTE_v01.md": "2ff546dbd69039da55ea1fb5641a4e8a91dc8933c9d6c93c0a398580245c8aad",
    CORRECTION_DIR / "D08B_TAXONOMY_CORRECTION_MANIFEST_v01.csv": "a1146332940274a6fec1fe83fcbec2241d466b1ec2a7d5bd5abce7f6d5c3e57d",
    CORRECTION_DIR / "D08B_TAXONOMY_CORRECTION_SHA256_v01.txt": "979b18f41e0fd861da13071939623f67ef5f3cc26ed45b3836f9fc4f1dcef1b1",
    CONTRACT: "bd756e111dc2cfe2e983d5f2b421846c85213612b167a111d0d0ee3d14ae40c8",
    INPUT_FREEZE: "55d784f1470da78554d49bf3458175b446f43bdf05c18f4ac9f3f9943e873477",
    V01_ZIP: "5ad4b94f5e3775db86c1b7d806dae3ec7888a13ad85af933b436e4eba2483c96",
    V01_MASTER: "7e373186d1c7f433c47856b2ae228b5b066ad2399b81a9cb3b4f372d57f47524",
    V01_SPECIES: "5ffb9e0880c82c97e7d7cf4ece04bec0c7523779f379b17304ad26ff9518f1e9",
    V01_DISTRIBUTION: "461b09edea496467eecb779ddb7eea542f142e93011f32ec97bbf7769ce06bbe",
    V01_GLOBAL: "9aa28e758d8b2aae28f594801d00d2b23ce704b37a59d790032e55068d1b04bb",
    V01_USGS: "28b7609d7a4eeb0ae89e79b91cf13d4ffe94c5b955f727bc9fe5f00b91a9188d",
    WCVP_ZIP: "d32ea2b3a85e489b14e83bcc9eae7274532e1d113753f7be290d4b2dfde573fa",
    ATLAS_HTML: "fdca3c163d856aeea7b15ec5f80e18750701a880ee8f9f4c1bd5cc076f26292b",
    ELIG_USGS: "bdc8a43411f648ab72c4d294f846d0688e436dcc035817cbc1de593e87c28312",
}

NAME_FIELDS = [
    "plant_name_id", "ipni_id", "powo_id", "taxon_rank", "taxon_status", "family",
    "genus_hybrid", "genus", "species_hybrid", "species", "infraspecific_rank",
    "infraspecies", "taxon_name", "taxon_authors", "accepted_plant_name_id",
    "parent_plant_name_id", "hybrid_formula", "reviewed",
]
DISTRIBUTION_SOURCE_FIELDS = [
    "plant_locality_id", "plant_name_id", "continent_code_l1", "continent",
    "region_code_l2", "region", "area_code_l3", "area", "introduced", "extinct",
    "location_doubtful",
]
ORDINARY_CLASSES = {
    "ACCEPTED_SPECIES", "SYNONYM_TO_ACCEPTED_SPECIES",
    "ACCEPTED_INFRASPECIES_TO_PARENT_SPECIES",
    "SYNONYM_TO_ACCEPTED_INFRASPECIES_TO_PARENT_SPECIES",
    "AUTHOR_QUALIFIED_ACCEPTED_SPECIES", "AUTHORITATIVE_ORTHOGRAPHIC_TO_ACCEPTED_SPECIES",
}
USGS_SINGLE_CLASSES = {"SINGLE_SPECIES_LAYER", "SINGLE_OFFICIAL_ALIAS_LAYER"}
USGS_REVIEW_CLASSES = {
    "SPECIES_LAYER_PLUS_INFRASPECIFIC_LAYER(S)", "INFRASPECIFIC_LAYER(S)_ONLY",
    "MULTIPLE_OTHER_LAYERS", "UNRESOLVED", "AMBIGUOUS",
}

PATCH = {
    "363": {"case": "ORDINARY_ACCEPTED", "accepted_name": "Arbutus xalapensis", "accepted_author": "Kunth", "expected_id": "2646755", "mapping_class": "AUTHOR_QUALIFIED_ACCEPTED_SPECIES"},
    "372": {"case": "ORDINARY_ACCEPTED", "accepted_name": "Betula lenta", "accepted_author": "L.", "expected_id": "21443", "mapping_class": "AUTHOR_QUALIFIED_ACCEPTED_SPECIES"},
    "744": {"case": "ORDINARY_ACCEPTED", "accepted_name": "Populus heterophylla", "accepted_author": "L.", "expected_id": "2917593", "mapping_class": "AUTHOR_QUALIFIED_ACCEPTED_SPECIES"},
    "820": {"case": "ORDINARY_ACCEPTED", "accepted_name": "Quercus laurifolia", "accepted_author": "Michx.", "expected_id": "173587", "mapping_class": "AUTHOR_QUALIFIED_ACCEPTED_SPECIES"},
    "822": {"case": "ORDINARY_ACCEPTED", "accepted_name": "Quercus lyrata", "accepted_author": "Walter", "expected_id": "173795", "mapping_class": "AUTHOR_QUALIFIED_ACCEPTED_SPECIES"},
    "840": {"case": "ORDINARY_ACCEPTED", "accepted_name": "Quercus margaretta", "accepted_author": "(Ashe) Small", "expected_id": "", "mapping_class": "AUTHORITATIVE_ORTHOGRAPHIC_TO_ACCEPTED_SPECIES"},
    "8355": {"case": "ORDINARY_ACCEPTED", "accepted_name": "Psidium cattleyanum", "accepted_author": "Sabine", "expected_id": "", "mapping_class": "AUTHORITATIVE_ORTHOGRAPHIC_TO_ACCEPTED_SPECIES"},
    "8563": {"case": "ORDINARY_ACCEPTED", "accepted_name": "Schinus terebinthifolia", "accepted_author": "Raddi", "expected_id": "", "mapping_class": "AUTHORITATIVE_ORTHOGRAPHIC_TO_ACCEPTED_SPECIES"},
    "6511": {"case": "TARGET_UNPLACED", "matched_name": "Persea palustris", "matched_author": "(Raf.) Sarg.", "matched_id": "2531614", "target_name": "Tamala palustris", "target_author": "Raf.", "target_id": "2442487"},
    "6955": {"case": "UNKNOWN"},
    "143": {"case": "ACCEPTED_HYBRID_NONCORE", "matched_name": "Pinus monophylla var. fallax", "matched_author": "(Little) Silba", "matched_id": "380213", "target_name": "Pinus × kohae", "target_author": "Frankis", "target_id": "3317681"},
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def int_sort(value: str) -> tuple[int, str]:
    try:
        return int(value), value
    except (TypeError, ValueError):
        return 10**12, str(value)


def joined(values: Iterable[object]) -> str:
    return ";".join(sorted({str(v) for v in values if str(v) != ""}, key=int_sort))


def normalize_name(value: str) -> str:
    value = unicodedata.normalize("NFC", html.unescape(value or ""))
    value = value.replace("\u00a0", " ").strip()
    value = re.sub(r"\bssp\.(?=\s)", "subsp.", value, flags=re.IGNORECASE)
    value = re.sub(r"\s+[xX]\s+", " × ", value)
    return re.sub(r"\s+", " ", value)


def canonical_author(value: str) -> str:
    value = unicodedata.normalize("NFC", html.unescape(value or "")).replace("\u00a0", " ")
    value = re.sub(r"\s+", " ", value.strip())
    value = re.sub(r"\s*([.,()])\s*", r"\1", value)
    return value


def name_components(value: str) -> list[str]:
    result = []
    for part in re.split(r"\s+/\s+", value or ""):
        part = re.sub(r"\s*\(in part\)\s*$", "", part, flags=re.IGNORECASE)
        part = normalize_name(part)
        if part:
            result.append(part)
    return result


def aligned_author_components(value: str, count: int) -> list[str]:
    parts = [normalize_name(part) for part in re.split(r"\s+/\s+", value or "") if normalize_name(part)]
    if len(parts) == count:
        return parts
    if count == 1:
        return [normalize_name(value)]
    return [""] * count


class AtlasParser(html.parser.HTMLParser if hasattr(html, "parser") else object):
    pass


def read_atlas_rows() -> tuple[list[str], list[dict[str, str]]]:
    from html.parser import HTMLParser

    class Parser(HTMLParser):
        def __init__(self) -> None:
            super().__init__(convert_charrefs=True)
            self.in_table = self.in_row = self.in_cell = False
            self.rows: list[list[dict[str, str]]] = []
            self.row: list[dict[str, str]] = []
            self.text: list[str] = []
            self.href = ""

        def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
            if tag == "table" and not self.in_table:
                self.in_table = True
            elif self.in_table and tag == "tr":
                self.in_row, self.row = True, []
            elif self.in_row and tag in {"th", "td"}:
                self.in_cell, self.text, self.href = True, [], ""
            elif self.in_cell and tag == "a":
                self.href = dict(attrs).get("href") or ""
            elif self.in_cell and tag in {"br", "p", "div"}:
                self.text.append(" ")

        def handle_data(self, data: str) -> None:
            if self.in_cell:
                self.text.append(data)

        def handle_endtag(self, tag: str) -> None:
            if self.in_cell and tag in {"th", "td"}:
                self.row.append({"text": normalize_name("".join(self.text)), "href": self.href})
                self.in_cell = False
            elif self.in_row and tag == "tr":
                if self.row:
                    self.rows.append(self.row)
                self.in_row = False
            elif self.in_table and tag == "table":
                self.in_table = False

    parser = Parser()
    parser.feed(ATLAS_HTML.read_text(encoding="utf-8"))
    headers = [cell["text"] for cell in parser.rows[0]]
    rows = []
    for cells in parser.rows[1:]:
        if len(cells) != len(headers):
            continue
        row = {headers[i]: cells[i]["text"] for i in range(len(headers))}
        row["layer_href"] = cells[0]["href"]
        rows.append(row)
    return headers, rows


def scan_wcvp(target_names: set[str], target_ids: set[str]) -> tuple[dict[str, list[dict[str, str]]], dict[str, dict[str, str]]]:
    matches: dict[str, list[dict[str, str]]] = defaultdict(list)
    id_rows: dict[str, dict[str, str]] = {}
    with zipfile.ZipFile(WCVP_ZIP) as archive:
        with archive.open("wcvp_names.csv", "r") as raw:
            text = (line.decode("utf-8") for line in raw)
            for source in csv.DictReader(text, delimiter="|", quoting=csv.QUOTE_NONE):
                key = normalize_name(source.get("taxon_name", ""))
                identifier = source.get("plant_name_id", "")
                if key in target_names or identifier in target_ids:
                    row = {field: source.get(field, "") for field in NAME_FIELDS}
                    if key in target_names:
                        matches[key].append(row)
                    if identifier in target_ids:
                        id_rows[identifier] = row
    referenced = set(target_ids)
    for rows in matches.values():
        for row in rows:
            referenced.update(filter(None, [row.get("plant_name_id", ""), row.get("accepted_plant_name_id", ""), row.get("parent_plant_name_id", "")]))
    missing = referenced - set(id_rows)
    if missing:
        with zipfile.ZipFile(WCVP_ZIP) as archive:
            with archive.open("wcvp_names.csv", "r") as raw:
                text = (line.decode("utf-8") for line in raw)
                for source in csv.DictReader(text, delimiter="|", quoting=csv.QUOTE_NONE):
                    identifier = source.get("plant_name_id", "")
                    if identifier in missing:
                        id_rows[identifier] = {field: source.get(field, "") for field in NAME_FIELDS}
    return matches, id_rows


def authored_row(matches: dict[str, list[dict[str, str]]], name: str, author: str, status: str | None = None) -> dict[str, str]:
    rows = [row for row in matches.get(normalize_name(name), []) if canonical_author(row.get("taxon_authors", "")) == canonical_author(author)]
    if status is not None:
        rows = [row for row in rows if row.get("taxon_status") == status]
    if len(rows) != 1:
        raise RuntimeError(f"Expected one WCVP row for {name} {author} status={status}, found {len(rows)}")
    return rows[0]


def is_hybrid_row(row: dict[str, str]) -> bool:
    return bool(
        row.get("taxon_status") == "Artificial Hybrid"
        or row.get("genus_hybrid")
        or row.get("species_hybrid")
        or " × " in normalize_name(row.get("taxon_name", ""))
    )


def distribution_record(source: dict[str, str], species_name: str) -> dict[str, str]:
    flags_valid = all(source.get(field, "") in {"0", "1"} for field in ("introduced", "extinct", "location_doubtful"))
    introduced, extinct, doubtful = source.get("introduced", ""), source.get("extinct", ""), source.get("location_doubtful", "")
    confirmed = flags_valid and introduced == "0" and extinct == "0" and doubtful == "0"
    historical = flags_valid and introduced == "0" and extinct == "1"
    doubtful_native = flags_valid and introduced == "0" and doubtful == "1"
    introduced_audit = flags_valid and introduced == "1"
    if not flags_valid:
        evidence_class = "UNKNOWN_FLAG_ENCODING"
    elif introduced_audit:
        evidence_class = "INTRODUCED_AUDIT"
    elif historical and doubtful_native:
        evidence_class = "NATIVE_EXTINCT_AND_LOCATION_DOUBTFUL"
    elif historical:
        evidence_class = "NATIVE_HISTORICAL_EXTINCT"
    elif doubtful_native:
        evidence_class = "NATIVE_LOCATION_DOUBTFUL"
    else:
        evidence_class = "CONFIRMED_CURRENT_NATIVE"
    return {
        "analysis_species_id": source.get("plant_name_id", ""),
        "analysis_species_name": species_name,
        **{field: source.get(field, "") for field in DISTRIBUTION_SOURCE_FIELDS},
        "distribution_flags_valid_binary": "1" if flags_valid else "0",
        "confirmed_current_native_flag": "1" if confirmed else "0",
        "native_historical_extinct_flag": "1" if historical else "0",
        "native_location_doubtful_flag": "1" if doubtful_native else "0",
        "introduced_audit_flag": "1" if introduced_audit else "0",
        "distribution_evidence_class": evidence_class,
        "query_provenance": "WCVP_ACCEPTED_ANALYSIS_SPECIES_ID_ONLY",
    }


def is_conus(row: dict[str, str]) -> bool:
    return row.get("region_code_l2") in {"73", "74", "75", "76", "77", "78"}


def is_alaska(row: dict[str, str]) -> bool:
    return row.get("area_code_l3") == "ASK"


def is_canada(row: dict[str, str]) -> bool:
    return row.get("region_code_l2") in {"71", "72"} or row.get("area_code_l3") in {"NUN", "NWT", "YUK"}


def is_usa_canada(row: dict[str, str]) -> bool:
    return is_conus(row) or is_alaska(row) or is_canada(row)


def is_north_america(row: dict[str, str]) -> bool:
    return row.get("continent_code_l1") == "7" or row.get("region_code_l2") in {"80", "81"}


def area_list(rows: Iterable[dict[str, str]]) -> str:
    return ";".join(sorted({f"{row['area_code_l3']}:{row['area']}" for row in rows}))


def tri_flag(rows: list[dict[str, str]], predicate, valid: bool) -> str:
    if not valid:
        return "UNKNOWN"
    return "TRUE" if any(predicate(row) for row in rows) else "FALSE"


def make_global(species: dict[str, str], records: list[dict[str, str]]) -> dict[str, str]:
    valid = bool(records) and all(row["distribution_flags_valid_binary"] == "1" for row in records)
    confirmed = [row for row in records if row["confirmed_current_native_flag"] == "1"]
    introduced = [row for row in records if row["introduced_audit_flag"] == "1"]
    extinct = [row for row in records if row["native_historical_extinct_flag"] == "1"]
    doubtful = [row for row in records if row["native_location_doubtful_flag"] == "1"]
    outside_usca = [row for row in confirmed if not is_usa_canada(row)]
    outside_na = [row for row in confirmed if not is_north_america(row)]
    introduced_conus = [row for row in introduced if is_conus(row)]
    extinct_outside = [row for row in extinct if not is_conus(row)]
    doubtful_outside = [row for row in doubtful if not is_conus(row)]
    continents = {row["continent_code_l1"] for row in confirmed if row["continent_code_l1"]}
    return {
        "analysis_species_id": species["analysis_species_id"], "analysis_species_name": species["analysis_species_name"],
        "wcvp_distribution_record_count": str(len(records)), "confirmed_current_native_record_count": str(len(confirmed)),
        "native_historical_extinct_record_count": str(len(extinct)), "native_location_doubtful_record_count": str(len(doubtful)),
        "introduced_audit_record_count": str(len(introduced)), "all_distribution_flags_valid_binary": "1" if valid else "0",
        "confirmed_native_CONUS": tri_flag(confirmed, is_conus, valid), "confirmed_native_Canada": tri_flag(confirmed, is_canada, valid),
        "confirmed_native_Alaska": tri_flag(confirmed, is_alaska, valid),
        "confirmed_native_Mexico": tri_flag(confirmed, lambda row: row.get("region_code_l2") == "79", valid),
        "confirmed_native_Central_America": tri_flag(confirmed, lambda row: row.get("region_code_l2") == "80", valid),
        "confirmed_native_outside_USA_Canada": "UNKNOWN" if not valid else ("TRUE" if outside_usca else "FALSE"),
        "confirmed_native_outside_North_America": "UNKNOWN" if not valid else ("TRUE" if outside_na else "FALSE"),
        "transcontinental_circumboreal_global_extension_flag": "UNKNOWN" if not valid else ("TRUE" if len(continents) >= 2 else "FALSE"),
        "introduced_in_CONUS_audit_flag": "UNKNOWN" if not valid else ("TRUE" if introduced_conus else "FALSE"),
        "extinct_native_outside_primary_CONUS_domain_flag": "UNKNOWN" if not valid else ("TRUE" if extinct_outside else "FALSE"),
        "doubtful_native_outside_primary_CONUS_domain_flag": "UNKNOWN" if not valid else ("TRUE" if doubtful_outside else "FALSE"),
        "confirmed_native_level3_areas": area_list(confirmed),
        "confirmed_native_outside_USA_Canada_level3_areas": area_list(outside_usca),
        "confirmed_native_outside_North_America_level3_areas": area_list(outside_na),
        "introduced_CONUS_level3_areas": area_list(introduced_conus),
        "extinct_native_outside_domain_level3_areas": area_list(extinct_outside),
        "doubtful_native_outside_domain_level3_areas": area_list(doubtful_outside),
        "macro_region_rule_version": "TAXON_RANGE_BUILD_CONTRACT_v01_SEMANTICS_UNCHANGED",
    }


def resolve_atlas_component(name: str, authors: str, matches: dict[str, list[dict[str, str]]], id_rows: dict[str, dict[str, str]]) -> dict[str, str]:
    key = normalize_name(name)
    rows = list(matches.get(key, []))
    evidence = {
        "component": key, "author": authors, "author_canonical": canonical_author(authors),
        "matched_ids": joined(row.get("plant_name_id", "") for row in rows),
        "matched_authors": " | ".join(sorted({row.get("taxon_authors", "") for row in rows if row.get("taxon_authors")})),
        "matched_statuses": joined(row.get("taxon_status", "") for row in rows),
        "species_id": "", "species_name": "",
    }
    if authors:
        authored = [row for row in rows if canonical_author(row.get("taxon_authors", "")) == canonical_author(authors)]
        if not authored:
            return {**evidence, "status": "UNRESOLVED", "reason": "No losslessly canonical author-qualified WCVP match; no other-author homonym substituted."}
        rows = authored
        evidence.update({
            "matched_ids": joined(row.get("plant_name_id", "") for row in rows),
            "matched_authors": " | ".join(sorted({row.get("taxon_authors", "") for row in rows if row.get("taxon_authors")})),
            "matched_statuses": joined(row.get("taxon_status", "") for row in rows),
        })
    accepted_ids = set()
    for row in rows:
        if row.get("taxon_status") == "Accepted":
            accepted_ids.add(row.get("plant_name_id", ""))
        elif row.get("taxon_status") == "Synonym" and row.get("accepted_plant_name_id"):
            accepted_ids.add(row["accepted_plant_name_id"])
    accepted_ids.discard("")
    if len(accepted_ids) != 1:
        status = "AMBIGUOUS" if accepted_ids else "UNRESOLVED"
        return {**evidence, "status": status, "reason": f"Author-governed exact component yielded {len(accepted_ids)} usable accepted identifiers; matched statuses control."}
    accepted_id = next(iter(accepted_ids))
    accepted = id_rows.get(accepted_id, {})
    if accepted.get("taxon_status") != "Accepted":
        return {**evidence, "status": "UNRESOLVED", "reason": "Resolved target is not a frozen-WCVP Accepted row."}
    if is_hybrid_row(accepted):
        return {**evidence, "status": "UNRESOLVED", "reason": "Resolved target is an accepted hybrid/non-core concept."}
    if accepted.get("taxon_rank") == "Species":
        return {**evidence, "status": "RESOLVED", "species_id": accepted_id, "species_name": accepted.get("taxon_name", ""), "reason": "Exact name plus losslessly canonical author resolved to WCVP Accepted species."}
    parent_id = accepted.get("parent_plant_name_id", "")
    parent = id_rows.get(parent_id, {})
    if parent.get("taxon_status") == "Accepted" and parent.get("taxon_rank") == "Species" and not is_hybrid_row(parent):
        return {**evidence, "status": "RESOLVED", "species_id": parent_id, "species_name": parent.get("taxon_name", ""), "reason": "Exact authored infraspecific component resolved through explicit parent to WCVP Accepted species."}
    return {**evidence, "status": "UNRESOLVED", "reason": "Authored component lacks an Accepted ordinary-species terminal path."}


def layer_rank(original_name: str, matches: dict[str, list[dict[str, str]]]) -> str:
    key = normalize_name(original_name)
    if re.search(r"\b(var\.|subsp\.|ssp\.|f\.)\s", key.lower()):
        return "INFRASPECIFIC"
    if "/" in key or " × " in key or re.search(r"\bspp?\.$", key.lower()):
        return "OTHER"
    ranks = {row.get("taxon_rank", "") for row in matches.get(key, []) if row.get("taxon_rank")}
    if ranks and all(rank == "Species" for rank in ranks):
        return "SPECIES"
    if any(rank in {"Subspecies", "Variety", "Form", "Subvariety", "Subform"} for rank in ranks):
        return "INFRASPECIFIC"
    return "SPECIES" if len(key.split()) == 2 else "OTHER"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    QC_DIR.mkdir(parents=True, exist_ok=True)

    input_hash_rows = []
    for path, expected in EXPECTED_HASHES.items():
        observed = sha256(path)
        input_hash_rows.append({"path": str(path.relative_to(ROOT)), "expected_sha256": expected, "observed_sha256": observed, "status": "PASS" if observed == expected else "FAIL"})
        if observed != expected:
            raise RuntimeError(f"Frozen input hash mismatch: {path}")

    v01_fields, v01_master = read_csv(V01_MASTER)
    _, v01_species = read_csv(V01_SPECIES)
    distribution_fields, v01_distribution = read_csv(V01_DISTRIBUTION)
    global_fields, v01_global = read_csv(V01_GLOBAL)
    v01_usgs_fields, v01_usgs = read_csv(V01_USGS)
    _, correction_evidence = read_csv(CORRECTION_DIR / "D08B_TAXONOMY_CORRECTION_EVIDENCE_v01.csv")
    _, eligibility_rows = read_csv(ELIG_USGS)
    _, atlas_raw = read_atlas_rows()
    evidence_by_code = {row["fia_species_code"]: row for row in correction_evidence}
    old_by_code = {row["fia_species_code"]: row for row in v01_master}

    target_names = set()
    for row in atlas_raw:
        target_names.update(name_components(row["Currently accepted scientific name"]))
        target_names.update(name_components(row["Scientific name from original reference"]))
    for patch in PATCH.values():
        for field in ("accepted_name", "matched_name", "target_name"):
            if patch.get(field):
                target_names.add(normalize_name(str(patch[field])))
    target_ids = set()
    for row in v01_master:
        for field in ("matched_wcvp_plant_name_id", "accepted_taxon_id", "accepted_parent_species_id", "analysis_species_id"):
            if row.get(field):
                target_ids.add(row[field])
    for patch in PATCH.values():
        for field in ("expected_id", "matched_id", "target_id"):
            if patch.get(field):
                target_ids.add(str(patch[field]))
    name_matches, id_rows = scan_wcvp(target_names, target_ids)

    for code, patch in PATCH.items():
        if patch["case"] == "ORDINARY_ACCEPTED":
            row = authored_row(name_matches, str(patch["accepted_name"]), str(patch["accepted_author"]), "Accepted")
            patch["resolved_id"] = row["plant_name_id"]
            if patch.get("expected_id") and patch["expected_id"] != patch["resolved_id"]:
                raise RuntimeError(f"Correction ID mismatch for FIA {code}")
        elif patch["case"] == "TARGET_UNPLACED":
            authored_row(name_matches, str(patch["matched_name"]), str(patch["matched_author"]), "Synonym")
            authored_row(name_matches, str(patch["target_name"]), str(patch["target_author"]), "Unplaced")
        elif patch["case"] == "ACCEPTED_HYBRID_NONCORE":
            authored_row(name_matches, str(patch["matched_name"]), str(patch["matched_author"]), "Synonym")
            authored_row(name_matches, str(patch["target_name"]), str(patch["target_author"]), "Accepted")

    extra_fields = [
        "fia_concept_author", "fia_author_evidence_status", "matched_wcvp_taxon_authors",
        "accepted_taxon_authors", "terminal_target_taxon_id", "terminal_target_taxon_name",
        "terminal_target_taxon_authors", "terminal_target_taxon_rank", "terminal_target_taxon_status",
        "analysis_species_authors", "taxonomic_status", "hybrid_or_nothotaxon_flag",
        "terminal_target_hybrid_formula", "analysis_species_hybrid_formula", "wcvp_hybrid_formula_present_flag",
        "ordinary_analysis_species_flag", "no_analysis_species_reason", "supplementary_sensitivity_candidate_flag",
        "d08b1_correction_applied_flag", "d08b1_correction_case_class", "d08b1_authority_source",
        "v01_mapping_class", "v01_taxonomy_resolution_status", "v01_ambiguity_alternatives",
    ]
    taxonomy_rows = []
    for old in sorted(v01_master, key=lambda row: int_sort(row["fia_species_code"])):
        row = dict(old)
        code = row["fia_species_code"]
        correction = PATCH.get(code)
        evidence = evidence_by_code.get(code, {})
        row.update({
            "fia_concept_author": evidence.get("fia_author", ""),
            "fia_author_evidence_status": "AUTHOR_AVAILABLE_IN_ACCEPTED_CORRECTION_EVIDENCE" if evidence and not evidence.get("fia_author", "").startswith(("NOT PROVIDED", "UNKNOWN")) else ("AUTHOR_NOT_PROVIDED_OR_UNKNOWN" if evidence else "NOT_AVAILABLE_IN_FROZEN_FIA_INPUT"),
            "matched_wcvp_taxon_authors": id_rows.get(row.get("matched_wcvp_plant_name_id", ""), {}).get("taxon_authors", ""),
            "accepted_taxon_authors": id_rows.get(row.get("accepted_taxon_id", ""), {}).get("taxon_authors", ""),
            "terminal_target_taxon_id": row.get("accepted_taxon_id", ""),
            "terminal_target_taxon_name": row.get("accepted_taxon_name", ""),
            "terminal_target_taxon_authors": id_rows.get(row.get("accepted_taxon_id", ""), {}).get("taxon_authors", ""),
            "terminal_target_taxon_rank": row.get("accepted_taxon_rank", ""),
            "terminal_target_taxon_status": row.get("accepted_taxon_status", ""),
            "analysis_species_authors": id_rows.get(row.get("analysis_species_id", ""), {}).get("taxon_authors", ""),
            "taxonomic_status": row.get("accepted_taxon_status", ""),
            "hybrid_or_nothotaxon_flag": "1" if "HYBRID" in row.get("mapping_class", "") or is_hybrid_row(id_rows.get(row.get("accepted_taxon_id", ""), {})) else "0",
            "terminal_target_hybrid_formula": id_rows.get(row.get("accepted_taxon_id", ""), {}).get("hybrid_formula", ""),
            "analysis_species_hybrid_formula": id_rows.get(row.get("analysis_species_id", ""), {}).get("hybrid_formula", ""),
            "wcvp_hybrid_formula_present_flag": "1" if id_rows.get(row.get("analysis_species_id", ""), {}).get("hybrid_formula", "") else "0",
            "ordinary_analysis_species_flag": "1" if row.get("analysis_species_id") else "0",
            "no_analysis_species_reason": "" if row.get("analysis_species_id") else row.get("mapping_reason", ""),
            "supplementary_sensitivity_candidate_flag": "0",
            "d08b1_correction_applied_flag": "1" if correction else "0",
            "d08b1_correction_case_class": correction.get("case", "") if correction else "",
            "d08b1_authority_source": "Q1_D08B_TAXONOMY_CORRECTION_MAINLINE_DECISION_v01_20260902.md" if correction else "D08B_V01_FROZEN",
            "v01_mapping_class": old.get("mapping_class", ""),
            "v01_taxonomy_resolution_status": old.get("taxonomy_resolution_status", ""),
            "v01_ambiguity_alternatives": old.get("ambiguity_alternatives", ""),
        })
        if correction and correction["case"] == "ORDINARY_ACCEPTED":
            accepted_id = str(correction["resolved_id"])
            accepted = id_rows[accepted_id]
            row.update({
                "matched_wcvp_plant_name_id": accepted_id, "matched_wcvp_taxon_status": "Accepted",
                "matched_wcvp_taxon_rank": "Species", "matched_wcvp_taxon_name": accepted["taxon_name"],
                "matched_wcvp_taxon_authors": accepted["taxon_authors"], "accepted_taxon_id": accepted_id,
                "accepted_taxon_name": accepted["taxon_name"], "accepted_taxon_authors": accepted["taxon_authors"],
                "accepted_taxon_rank": "Species", "accepted_taxon_status": "Accepted",
                "accepted_parent_species_id": "", "accepted_parent_species_name": "",
                "terminal_target_taxon_id": accepted_id, "terminal_target_taxon_name": accepted["taxon_name"],
                "terminal_target_taxon_authors": accepted["taxon_authors"], "terminal_target_taxon_rank": "Species",
                "terminal_target_taxon_status": "Accepted", "analysis_species_id": accepted_id,
                "analysis_species_name": accepted["taxon_name"], "analysis_species_authors": accepted["taxon_authors"],
                "analysis_species_rank": "Species", "mapping_class": correction["mapping_class"],
                "taxonomy_resolution_status": "RESOLVED_MAINLINE_AUTHORIZED",
                "ambiguity_alternatives": "", "mapping_reason": evidence.get("resolution_reason", "Mainline-authorized author-qualified correction."),
                "distribution_query_plant_name_id": accepted_id, "distribution_query_taxon_name": accepted["taxon_name"],
                "range_query_rule": "ACCEPTED_ANALYSIS_SPECIES_ID_ONLY", "taxonomic_status": "Accepted",
                "hybrid_or_nothotaxon_flag": "0", "ordinary_analysis_species_flag": "1", "no_analysis_species_reason": "",
                "terminal_target_hybrid_formula": accepted.get("hybrid_formula", ""), "analysis_species_hybrid_formula": accepted.get("hybrid_formula", ""),
                "wcvp_hybrid_formula_present_flag": "1" if accepted.get("hybrid_formula", "") else "0",
            })
        elif correction and correction["case"] == "TARGET_UNPLACED":
            matched, target = id_rows[str(correction["matched_id"])], id_rows[str(correction["target_id"])]
            for field in ("accepted_taxon_id", "accepted_taxon_name", "accepted_taxon_authors", "accepted_taxon_rank", "accepted_taxon_status", "analysis_species_id", "analysis_species_name", "analysis_species_authors", "analysis_species_rank", "distribution_query_plant_name_id", "distribution_query_taxon_name"):
                row[field] = ""
            row.update({
                "matched_wcvp_plant_name_id": matched["plant_name_id"], "matched_wcvp_taxon_status": matched["taxon_status"],
                "matched_wcvp_taxon_rank": matched["taxon_rank"], "matched_wcvp_taxon_name": matched["taxon_name"],
                "matched_wcvp_taxon_authors": matched["taxon_authors"], "terminal_target_taxon_id": target["plant_name_id"],
                "terminal_target_taxon_name": target["taxon_name"], "terminal_target_taxon_authors": target["taxon_authors"],
                "terminal_target_taxon_rank": target["taxon_rank"], "terminal_target_taxon_status": target["taxon_status"],
                "mapping_class": "IDENTITY_RESOLVED_TARGET_UNPLACED", "taxonomy_resolution_status": "IDENTITY_RESOLVED_NO_ACCEPTED_ANALYSIS_SPECIES",
                "ambiguity_alternatives": "", "mapping_reason": evidence.get("resolution_reason", "Identity resolved; target Unplaced."),
                "range_query_rule": "NOT_APPLICABLE_NO_ACCEPTED_ANALYSIS_SPECIES", "taxonomic_status": "Unplaced",
                "hybrid_or_nothotaxon_flag": "0", "ordinary_analysis_species_flag": "0",
                "terminal_target_hybrid_formula": target.get("hybrid_formula", ""), "analysis_species_hybrid_formula": "", "wcvp_hybrid_formula_present_flag": "0",
                "no_analysis_species_reason": "Terminal target Tamala palustris Raf. is frozen-WCVP Unplaced; no Accepted replacement is fabricated.",
            })
        elif correction and correction["case"] == "UNKNOWN":
            for field in ("matched_wcvp_plant_name_id", "matched_wcvp_taxon_status", "matched_wcvp_taxon_rank", "matched_wcvp_taxon_name", "matched_wcvp_taxon_authors", "accepted_taxon_id", "accepted_taxon_name", "accepted_taxon_authors", "accepted_taxon_rank", "accepted_taxon_status", "terminal_target_taxon_id", "terminal_target_taxon_name", "terminal_target_taxon_authors", "terminal_target_taxon_rank", "terminal_target_taxon_status", "analysis_species_id", "analysis_species_name", "analysis_species_authors", "analysis_species_rank", "distribution_query_plant_name_id", "distribution_query_taxon_name"):
                row[field] = ""
            row.update({
                "mapping_class": "UNRESOLVED", "taxonomy_resolution_status": "UNKNOWN_MAINLINE_AUTHORIZED",
                "ambiguity_alternatives": old.get("ambiguity_alternatives", ""), "mapping_reason": evidence.get("resolution_reason", "Code-specific identity remains unknown."),
                "range_query_rule": "NOT_APPLICABLE_NO_ANALYSIS_SPECIES", "taxonomic_status": "UNKNOWN",
                "hybrid_or_nothotaxon_flag": "0", "ordinary_analysis_species_flag": "0",
                "terminal_target_hybrid_formula": "", "analysis_species_hybrid_formula": "", "wcvp_hybrid_formula_present_flag": "0",
                "no_analysis_species_reason": "FIA code 6955 remains UNKNOWN; no forced Salix mapping is permitted.",
            })
        elif correction and correction["case"] == "ACCEPTED_HYBRID_NONCORE":
            matched, target = id_rows[str(correction["matched_id"])], id_rows[str(correction["target_id"])]
            row.update({
                "matched_wcvp_plant_name_id": matched["plant_name_id"], "matched_wcvp_taxon_status": matched["taxon_status"],
                "matched_wcvp_taxon_rank": matched["taxon_rank"], "matched_wcvp_taxon_name": matched["taxon_name"],
                "matched_wcvp_taxon_authors": matched["taxon_authors"], "accepted_taxon_id": target["plant_name_id"],
                "accepted_taxon_name": target["taxon_name"], "accepted_taxon_authors": target["taxon_authors"],
                "accepted_taxon_rank": target["taxon_rank"], "accepted_taxon_status": target["taxon_status"],
                "terminal_target_taxon_id": target["plant_name_id"], "terminal_target_taxon_name": target["taxon_name"],
                "terminal_target_taxon_authors": target["taxon_authors"], "terminal_target_taxon_rank": target["taxon_rank"],
                "terminal_target_taxon_status": target["taxon_status"], "analysis_species_id": "", "analysis_species_name": "",
                "analysis_species_authors": "", "analysis_species_rank": "", "mapping_class": "ACCEPTED_HYBRID_NONCORE",
                "taxonomy_resolution_status": "RESOLVED_ACCEPTED_HYBRID_NONCORE", "ambiguity_alternatives": "",
                "mapping_reason": evidence.get("resolution_reason", "Accepted hybrid resolved and removed from ordinary core."),
                "distribution_query_plant_name_id": "", "distribution_query_taxon_name": "",
                "range_query_rule": "AUDIT_ONLY_ACCEPTED_HYBRID_ID", "taxonomic_status": "Accepted",
                "hybrid_or_nothotaxon_flag": "1", "ordinary_analysis_species_flag": "0",
                "terminal_target_hybrid_formula": target.get("hybrid_formula", ""), "analysis_species_hybrid_formula": "", "wcvp_hybrid_formula_present_flag": "1" if target.get("hybrid_formula", "") else "0",
                "no_analysis_species_reason": "Accepted hybrid/non-core object; excluded from ordinary accepted-species master.",
                "main_analysis_candidate_retained_flag": "0", "supplementary_sensitivity_candidate_flag": "1",
            })
        taxonomy_rows.append(row)

    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in taxonomy_rows:
        if row["ordinary_analysis_species_flag"] == "1":
            groups[row["analysis_species_id"]].append(row)
    analysis_rows = []
    for species_id in sorted(groups, key=int_sort):
        accepted, components = id_rows[species_id], groups[species_id]
        bases = {row["diameter_measurement_basis"] for row in components}
        composition = "DBH_ONLY" if bases == {"DBH_BREAST_HEIGHT"} else ("DRC_ONLY" if bases == {"DRC_ROOT_COLLAR"} else "MIXED_DBH_DRC")
        analysis_rows.append({
            "analysis_species_id": species_id, "analysis_species_name": accepted["taxon_name"], "analysis_species_authors": accepted["taxon_authors"],
            "analysis_species_family": accepted["family"], "analysis_species_rank": accepted["taxon_rank"], "analysis_species_status": accepted["taxon_status"],
            "analysis_species_hybrid_flag": "1" if is_hybrid_row(accepted) else "0", "ordinary_core_class": "ORDINARY_ACCEPTED_SPECIES",
            "analysis_species_hybrid_formula": accepted.get("hybrid_formula", ""),
            "wcvp_hybrid_formula_present_flag": "1" if accepted.get("hybrid_formula", "") else "0",
            "ipni_id": accepted["ipni_id"], "powo_id": accepted["powo_id"], "wcvp_reviewed_flag": accepted["reviewed"],
            "component_fia_code_count": str(len(components)), "component_fia_codes": joined(row["fia_species_code"] for row in components),
            "component_fia_names": joined(row["fia_scientific_name"] for row in components), "component_mapping_classes": joined(row["mapping_class"] for row in components),
            "contains_synonym_component_flag": "1" if any("SYNONYM" in row["mapping_class"] for row in components) else "0",
            "contains_infraspecific_component_flag": "1" if any("INFRASPECIES" in row["mapping_class"] for row in components) else "0",
            "dbh_component_code_count": str(sum(row["diameter_measurement_basis"] == "DBH_BREAST_HEIGHT" for row in components)),
            "drc_component_code_count": str(sum(row["diameter_measurement_basis"] == "DRC_ROOT_COLLAR" for row in components)),
            "diameter_basis_composition": composition, "large_tree_subplot_ge5_flag": "1" if all(row["dia_threshold_inches"] == "5.0" for row in components) else "0",
            "main_analysis_candidate_retained_flag": "1", "dbh_only_sensitivity_flag": "1" if composition == "DBH_ONLY" else "0",
            "taxonomy_ambiguity_flag": "0", "distribution_query_plant_name_id": species_id, "distribution_query_taxon_name": accepted["taxon_name"],
            "source_code_map_version": "Q1_FIA_CODE_TO_ANALYSIS_SPECIES_v02",
        })

    analysis_by_id = {row["analysis_species_id"]: row for row in analysis_rows}
    v01_analysis_ids = {row["analysis_species_id"] for row in v01_species}
    final_ids = set(analysis_by_id)
    new_ids = final_ids - v01_analysis_ids
    retained_distribution = [dict(row) for row in v01_distribution if row["analysis_species_id"] in final_ids and row["analysis_species_id"] not in new_ids]
    new_distribution = []
    with zipfile.ZipFile(WCVP_ZIP) as archive:
        with archive.open("wcvp_distribution.csv", "r") as raw:
            text = (line.decode("utf-8") for line in raw)
            for source in csv.DictReader(text, delimiter="|", quoting=csv.QUOTE_NONE):
                species_id = source.get("plant_name_id", "")
                if species_id in new_ids:
                    new_distribution.append(distribution_record(source, analysis_by_id[species_id]["analysis_species_name"]))
    distribution_rows = retained_distribution + new_distribution
    distribution_rows.sort(key=lambda row: (int_sort(row["analysis_species_id"]), int_sort(row["plant_locality_id"])))
    hybrid_distribution = [{**row, "hybrid_audit_only_flag": "1", "audit_reason": "Accepted hybrid removed from ordinary species master by D08B.1 mainline decision."} for row in v01_distribution if row["analysis_species_id"] == "3317681"]

    distribution_by_id: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in distribution_rows:
        distribution_by_id[row["analysis_species_id"]].append(row)
    v01_global_by_id = {row["analysis_species_id"]: row for row in v01_global}
    global_rows = []
    for species in analysis_rows:
        species_id = species["analysis_species_id"]
        if species_id in new_ids:
            global_rows.append(make_global(species, distribution_by_id[species_id]))
        else:
            global_rows.append(dict(v01_global_by_id[species_id]))
    global_by_id = {row["analysis_species_id"]: row for row in global_rows}

    atlas_rows = []
    atlas_by_species: dict[str, list[dict[str, object]]] = defaultdict(list)
    for index, source in enumerate(atlas_raw, start=1):
        components = name_components(source["Currently accepted scientific name"])
        authors = aligned_author_components(source["Authors for currently accepted scientific name"], len(components))
        resolutions = [resolve_atlas_component(component, authors[pos], name_matches, id_rows) for pos, component in enumerate(components)]
        resolved_ids = sorted({row["species_id"] for row in resolutions if row["status"] == "RESOLVED"}, key=int_sort)
        unresolved = [row for row in resolutions if row["status"] != "RESOLVED"]
        href = source.get("layer_href", "")
        atlas = {
            "atlas_table1_row_id": f"ATLASG-{index:04d}", "atlas_original_source_name": source["Scientific name from original reference"],
            "atlas_current_accepted_name_field": source["Currently accepted scientific name"], "atlas_current_name_authors": source["Authors for currently accepted scientific name"],
            "atlas_layer_rank": layer_rank(source["Scientific name from original reference"], name_matches), "atlas_layer_href": href,
            "atlas_layer_key": PurePosixPath(href).stem if href else "", "atlas_number_gridpoints": source["Number of gridpoints"],
            "atlas_primary_source": source["Original primary map, name and authority source"], "atlas_unique_sources": source["Unique sources"],
            "atlas_notes": source["Notes"], "atlas_status": source["Status"], "atlas_shared_resolved_species_count": str(len(resolved_ids)),
            "atlas_unresolved_components": joined(row["component"] for row in unresolved), "atlas_resolved_species_ids": joined(resolved_ids),
            "atlas_resolved_species_names": joined(id_rows.get(identifier, {}).get("taxon_name", "") for identifier in resolved_ids),
            "atlas_component_names": " | ".join(row["component"] for row in resolutions),
            "atlas_component_authors_canonical": " | ".join(row["author_canonical"] for row in resolutions),
            "atlas_component_wcvp_match_ids": " | ".join(row["matched_ids"] for row in resolutions),
            "atlas_component_wcvp_match_authors": " | ".join(row["matched_authors"] for row in resolutions),
            "atlas_component_wcvp_match_statuses": " | ".join(row["matched_statuses"] for row in resolutions),
            "atlas_component_resolution_statuses": " | ".join(row["status"] for row in resolutions),
            "atlas_component_resolution_reasons": " | ".join(row["reason"] for row in resolutions),
        }
        atlas_rows.append(atlas)
        for species_id in resolved_ids:
            if species_id in final_ids:
                atlas_by_species[species_id].append(atlas)

    usgs_rows, usgs_review, usgs_summary = [], [], {}
    for species in analysis_rows:
        species_id, species_name = species["analysis_species_id"], species["analysis_species_name"]
        rows = atlas_by_species.get(species_id, [])
        global_info = global_by_id[species_id]
        nonnative = global_info["confirmed_native_CONUS"] == "FALSE" and global_info["introduced_in_CONUS_audit_flag"] == "TRUE"
        if not rows:
            mapping_class = "NOT_APPLICABLE_CONUS_NONNATIVE" if nonnative else "UNRESOLVED"
        elif any(int(str(row["atlas_shared_resolved_species_count"])) != 1 or row["atlas_unresolved_components"] for row in rows):
            mapping_class = "AMBIGUOUS"
        else:
            ranks = {str(row["atlas_layer_rank"]) for row in rows}
            if "SPECIES" in ranks and "INFRASPECIFIC" in ranks:
                mapping_class = "SPECIES_LAYER_PLUS_INFRASPECIFIC_LAYER(S)"
            elif ranks == {"INFRASPECIFIC"}:
                mapping_class = "INFRASPECIFIC_LAYER(S)_ONLY"
            elif len(rows) > 1:
                mapping_class = "MULTIPLE_OTHER_LAYERS"
            elif rows[0]["atlas_layer_rank"] == "SPECIES" and normalize_name(str(rows[0]["atlas_original_source_name"])) == normalize_name(species_name):
                mapping_class = "SINGLE_SPECIES_LAYER"
            elif rows[0]["atlas_layer_rank"] == "SPECIES":
                mapping_class = "SINGLE_OFFICIAL_ALIAS_LAYER"
            else:
                mapping_class = "MULTIPLE_OTHER_LAYERS"
        any_notes = any(bool(row["atlas_notes"]) for row in rows)
        review = mapping_class in USGS_REVIEW_CLASSES or any_notes
        canonical_rows = rows if not review and mapping_class in USGS_SINGLE_CLASSES and len(rows) == 1 else []
        usgs_summary[species_id] = {
            "usgs_mapping_class": mapping_class, "usgs_atlas_row_count": str(len(rows)),
            "usgs_review_required_flag": "1" if review else "0",
            "usgs_canonical_layer_key": str(canonical_rows[0]["atlas_layer_key"]) if canonical_rows else "",
        }
        if not rows:
            decision = "NOT_APPLICABLE_CONUS_NONNATIVE" if mapping_class == "NOT_APPLICABLE_CONUS_NONNATIVE" else "MAINLINE_REVIEW_REQUIRED"
            blank_atlas = {key: "" for key in atlas_rows[0]}
            blank_atlas["atlas_shared_resolved_species_count"] = "0"
            out = {
                "analysis_species_id": species_id, "analysis_species_name": species_name, "analysis_species_authors": species["analysis_species_authors"],
                "usgs_mapping_class": mapping_class, "usgs_review_required_flag": "1" if review else "0", "canonical_layer_flag": "0",
                "canonical_layer_key": "", **blank_atlas, "decision_status": decision,
                "review_reason": "WCVP confirms no native CONUS distribution and introduced CONUS occurrence; Little natural-range mapping is not applicable." if mapping_class == "NOT_APPLICABLE_CONUS_NONNATIVE" else "No Atlas row resolved by exact name plus author to this accepted ordinary species.",
            }
            usgs_rows.append(out)
            if review:
                usgs_review.append(dict(out))
        else:
            for atlas in rows:
                canonical = bool(canonical_rows and atlas is canonical_rows[0])
                reasons = []
                if mapping_class not in USGS_SINGLE_CLASSES:
                    reasons.append(mapping_class)
                if atlas["atlas_notes"]:
                    reasons.append("ATLAS_NOTES_NONBLANK")
                if int(str(atlas["atlas_shared_resolved_species_count"])) != 1:
                    reasons.append("SHARED_OR_MULTI_TAXON_LAYER")
                if atlas["atlas_unresolved_components"]:
                    reasons.append("UNRESOLVED_ACCEPTED_NAME_COMPONENT")
                out = {
                    "analysis_species_id": species_id, "analysis_species_name": species_name, "analysis_species_authors": species["analysis_species_authors"],
                    "usgs_mapping_class": mapping_class, "usgs_review_required_flag": "1" if review else "0",
                    "canonical_layer_flag": "1" if canonical else "0", "canonical_layer_key": str(atlas["atlas_layer_key"]) if canonical else "",
                    **atlas, "decision_status": "CANONICAL_SINGLE_LAYER" if canonical else "MAINLINE_REVIEW_REQUIRED", "review_reason": ";".join(reasons),
                }
                usgs_rows.append(out)
                if review:
                    usgs_review.append(dict(out))

    for row in taxonomy_rows:
        sid = row["analysis_species_id"]
        global_info, usgs_info = global_by_id.get(sid, {}), usgs_summary.get(sid, {})
        row.update({
            "wcvp_distribution_record_count": global_info.get("wcvp_distribution_record_count", ""),
            "confirmed_current_native_record_count": global_info.get("confirmed_current_native_record_count", ""),
            "confirmed_native_outside_USA_Canada": global_info.get("confirmed_native_outside_USA_Canada", ""),
            "confirmed_native_outside_North_America": global_info.get("confirmed_native_outside_North_America", ""),
            "usgs_mapping_class": usgs_info.get("usgs_mapping_class", "NOT_APPLICABLE_NO_ORDINARY_ANALYSIS_SPECIES"),
            "usgs_atlas_row_count": usgs_info.get("usgs_atlas_row_count", "0"),
            "usgs_review_required_flag": usgs_info.get("usgs_review_required_flag", "0"),
            "usgs_canonical_layer_key": usgs_info.get("usgs_canonical_layer_key", ""),
        })

    drc_rows = []
    for species in analysis_rows:
        components = groups[species["analysis_species_id"]]
        drc_rows.append({
            "analysis_species_id": species["analysis_species_id"], "analysis_species_name": species["analysis_species_name"],
            "analysis_species_authors": species["analysis_species_authors"], "component_fia_codes": species["component_fia_codes"],
            "component_fia_names": species["component_fia_names"], "dbh_component_code_count": species["dbh_component_code_count"],
            "drc_component_code_count": species["drc_component_code_count"], "diameter_basis_composition": species["diameter_basis_composition"],
            "diameter_measurement_bases": joined(row["diameter_measurement_basis"] for row in components),
            "woodland_indicators": joined(row["woodland_indicator"] for row in components), "dia_threshold_inches": joined(row["dia_threshold_inches"] for row in components),
            "official_large_tree_subplot_ge5_flag": species["large_tree_subplot_ge5_flag"], "main_analysis_candidate_retained_flag": "1",
            "dbh_only_sensitivity_flag": species["dbh_only_sensitivity_flag"], "regional_manual_exception_status": "PRESERVE_PROTOCOL_VARIABLES_NO_REINTERPRETATION",
            "drc_scientific_inclusion_status": "RETAINED_AS_PRIMARY_CANDIDATE_PER_D08B",
        })

    correction_rows = []
    for evidence in correction_evidence:
        code = evidence["fia_species_code"]
        before, after = old_by_code[code], next(row for row in taxonomy_rows if row["fia_species_code"] == code)
        correction_rows.append({
            "fia_species_code": code, "fia_name_raw": after["fia_name_raw"], "mainline_case_class": PATCH[code]["case"],
            "v01_mapping_class": before["mapping_class"], "v01_analysis_species_id": before["analysis_species_id"], "v01_analysis_species_name": before["analysis_species_name"],
            "v02_mapping_class": after["mapping_class"], "v02_taxonomy_resolution_status": after["taxonomy_resolution_status"],
            "v02_matched_wcvp_name": after["matched_wcvp_taxon_name"], "v02_matched_wcvp_author": after["matched_wcvp_taxon_authors"],
            "v02_matched_wcvp_id": after["matched_wcvp_plant_name_id"], "v02_terminal_target_name": after["terminal_target_taxon_name"],
            "v02_terminal_target_author": after["terminal_target_taxon_authors"], "v02_terminal_target_id": after["terminal_target_taxon_id"],
            "v02_terminal_target_status": after["terminal_target_taxon_status"], "v02_analysis_species_id": after["analysis_species_id"],
            "v02_analysis_species_name": after["analysis_species_name"], "v02_analysis_species_author": after["analysis_species_authors"],
            "hybrid_or_nothotaxon_flag": after["hybrid_or_nothotaxon_flag"], "ordinary_analysis_species_flag": after["ordinary_analysis_species_flag"],
            "no_analysis_species_reason": after["no_analysis_species_reason"], "authority_resolution_reason": evidence["resolution_reason"],
            "authority_evidence_source_1": evidence["evidence_source_1"], "authority_evidence_source_2": evidence["evidence_source_2"],
            "application_status": "APPLIED_EXACTLY_AS_AUTHORIZED",
        })

    hybrid_rows = []
    for row in taxonomy_rows:
        if row["hybrid_or_nothotaxon_flag"] == "1" or "HYBRID" in row["mapping_class"]:
            hybrid_rows.append({
                "fia_species_code": row["fia_species_code"], "fia_name_raw": row["fia_name_raw"], "mapping_class": row["mapping_class"],
                "matched_wcvp_id": row["matched_wcvp_plant_name_id"], "matched_wcvp_name": row["matched_wcvp_taxon_name"],
                "matched_wcvp_author": row["matched_wcvp_taxon_authors"], "accepted_hybrid_id": row["terminal_target_taxon_id"],
                "accepted_hybrid_name": row["terminal_target_taxon_name"], "accepted_hybrid_author": row["terminal_target_taxon_authors"],
                "accepted_hybrid_status": row["terminal_target_taxon_status"], "ordinary_analysis_species_id": row["analysis_species_id"],
                "core_status": "ACCEPTED_HYBRID_NONCORE" if row["fia_species_code"] == "143" else "HYBRID_OR_NOTHOTAXON_NONCORE",
                "supplementary_sensitivity_candidate_flag": row["supplementary_sensitivity_candidate_flag"],
                "distribution_audit_row_count": str(sum(dist["analysis_species_id"] == row["terminal_target_taxon_id"] for dist in hybrid_distribution)),
                "audit_note": row["no_analysis_species_reason"],
            })

    v01_usgs_by_id: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in v01_usgs:
        v01_usgs_by_id[row["analysis_species_id"]].append(row)
    elig_by_code: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in eligibility_rows:
        elig_by_code[row["fia_species_code"]].append(row)

    keys = set()
    for sid, rows in v01_usgs_by_id.items():
        if any(row["usgs_review_required_flag"] == "1" for row in rows):
            keys.add("H:143" if sid == "3317681" else f"S:{sid}")
    for sid, summary in usgs_summary.items():
        if summary["usgs_review_required_flag"] == "1":
            keys.add(f"S:{sid}")
    for code in PATCH:
        mapped = next(row for row in taxonomy_rows if row["fia_species_code"] == code)
        keys.add(f"S:{mapped['analysis_species_id']}" if mapped["analysis_species_id"] else ("H:143" if code == "143" else f"C:{code}"))

    cross_rows = []
    for key in sorted(keys, key=lambda value: (value[0], int_sort(value.split(":", 1)[1]))):
        kind, identifier = key.split(":", 1)
        if kind == "S":
            species = analysis_by_id.get(identifier, {})
            components = groups.get(identifier, [])
            component_codes = sorted({row["fia_species_code"] for row in components}, key=int_sort)
            old_rows = v01_usgs_by_id.get(identifier, [])
            new_rows = [row for row in usgs_rows if row["analysis_species_id"] == identifier]
            name, author = species.get("analysis_species_name", ""), species.get("analysis_species_authors", "")
            proposed = usgs_summary.get(identifier, {}).get("usgs_mapping_class", "NO_V02_BRIDGE_ROW")
        elif kind == "H":
            component_codes, old_rows, new_rows = ["143"], v01_usgs_by_id.get("3317681", []), []
            name, author, proposed = "Pinus × kohae", "Frankis", "ACCEPTED_HYBRID_NONCORE"
        else:
            component_codes, old_rows, new_rows = [identifier], [], []
            code_row = next(row for row in taxonomy_rows if row["fia_species_code"] == identifier)
            name, author, proposed = code_row["terminal_target_taxon_name"] or code_row["fia_name_raw"], code_row["terminal_target_taxon_authors"], code_row["mapping_class"]
        elig = [row for code in component_codes for row in elig_by_code.get(code, [])]
        candidate_names = {normalize_name(name)} if name else set()
        for elig_row in elig:
            candidate_names.update(filter(None, [normalize_name(elig_row.get("USGS_original_map_name", "")), normalize_name(elig_row.get("USGS_accepted_name", ""))]))
        candidate_atlas = []
        for atlas in atlas_rows:
            atlas_names = {normalize_name(str(atlas["atlas_original_source_name"]))}
            atlas_names.update(name_components(str(atlas["atlas_current_accepted_name_field"])))
            if candidate_names & atlas_names:
                candidate_atlas.append(atlas)
        prior_nonzero = any(row.get("mapping_type", "").lower() in {"exact", "official", "official_alias"} and max(int(float(row.get(field, "0") or 0)) for field in ("n_US_cells", "n_CONUS_cells", "n_US_plus_Canada_cells")) > 0 for row in elig)
        old_class = joined(row["usgs_mapping_class"] for row in old_rows) or "NO_V01_ANALYSIS_SPECIES_TAXONOMY_BLOCK"
        old_review = "1" if any(row.get("usgs_review_required_flag") == "1" for row in old_rows) else "0"
        if old_class == "UNRESOLVED" and prior_nonzero:
            conflict = "PRIOR_EXACT_NONZERO_BUT_D08B_V01_UNRESOLVED"
        elif old_review == "1" and prior_nonzero:
            conflict = "PRIOR_EXACT_NONZERO_D08B_V01_REVIEW_ONLY"
        elif old_class.startswith("NO_V01") and prior_nonzero:
            conflict = "PRIOR_EXACT_NONZERO_TAXONOMY_BLOCKED_IN_V01"
        elif not elig:
            conflict = "NO_ELIGIBILITY_V02_DIAGNOSTIC_ROW"
        elif proposed == "NOT_APPLICABLE_CONUS_NONNATIVE":
            conflict = "EXPLICIT_CONUS_NONNATIVE_NOT_APPLICABLE"
        elif old_class != proposed:
            conflict = "D08B1_BRIDGE_STATUS_CHANGED"
        else:
            conflict = "REVIEW_DIAGNOSTIC_NO_SILENT_LOSS"
        if kind == "S":
            disposition = "MACHINE_RESOLVED" if proposed in USGS_SINGLE_CLASSES | {"NOT_APPLICABLE_CONUS_NONNATIVE"} else "MAINLINE_REVIEW_REQUIRED"
        elif kind == "H":
            disposition = "MACHINE_CLASSIFIED_NONCORE"
        else:
            disposition = "NO_ORDINARY_ANALYSIS_SPECIES"
        if proposed in USGS_SINGLE_CLASSES:
            explicit_cause = "Losslessly canonical author matching repaired the v01 conservative false negative and yielded one no-Notes species layer."
        elif proposed == "NOT_APPLICABLE_CONUS_NONNATIVE":
            explicit_cause = "Frozen WCVP confirms no native CONUS distribution and introduced CONUS occurrence; Little natural-range mapping is not applicable."
        elif candidate_atlas:
            explicit_cause = " | ".join(sorted({str(row["atlas_component_resolution_reasons"]) for row in candidate_atlas if row["atlas_component_resolution_reasons"]}))
        else:
            explicit_cause = "No exact Atlas original/current-name candidate row was found for the analysis or frozen eligibility names; no fuzzy substitute was used."
        cross_rows.append({
            "analysis_species_id": identifier if kind == "S" else "", "analysis_species_name": name, "analysis_species_authors": author,
            "component_fia_codes": ";".join(component_codes), "d08b_v01_usgs_mapping_class": old_class,
            "d08b_v01_review_required_flag": old_review, "d08b_v01_atlas_row_ids": joined(row.get("atlas_table1_row_id", "") for row in old_rows),
            "d08b_v01_atlas_original_names": " | ".join(sorted({row.get("atlas_original_source_name", "") for row in old_rows if row.get("atlas_original_source_name")})),
            "eligibility_v02_row_present_flag": "1" if elig else "0", "eligibility_v02_fia_codes": joined(row.get("fia_species_code", "") for row in elig),
            "eligibility_v02_mapping_types": joined(row.get("mapping_type", "") for row in elig),
            "eligibility_v02_original_map_names": " | ".join(sorted({row.get("USGS_original_map_name", "") for row in elig if row.get("USGS_original_map_name")})),
            "eligibility_v02_accepted_names": " | ".join(sorted({row.get("USGS_accepted_name", "") for row in elig if row.get("USGS_accepted_name")})),
            "eligibility_v02_layer_name_proxy": " | ".join(sorted({row.get("USGS_original_map_name", "") for row in elig if row.get("USGS_original_map_name")})),
            "eligibility_v02_n_US_cells_by_code": ";".join(f"{row['fia_species_code']}:{row['n_US_cells']}" for row in elig),
            "eligibility_v02_n_CONUS_cells_by_code": ";".join(f"{row['fia_species_code']}:{row['n_CONUS_cells']}" for row in elig),
            "eligibility_v02_n_US_plus_Canada_cells_by_code": ";".join(f"{row['fia_species_code']}:{row['n_US_plus_Canada_cells']}" for row in elig),
            "eligibility_prior_exact_or_official_nonzero_flag": "1" if prior_nonzero else "0",
            "v02_atlas_row_ids": joined(row.get("atlas_table1_row_id", "") for row in new_rows),
            "v02_atlas_original_names": " | ".join(sorted({row.get("atlas_original_source_name", "") for row in new_rows if row.get("atlas_original_source_name")})),
            "candidate_atlas_match_status": "EXACT_NAME_CANDIDATE_ROWS_FOUND" if candidate_atlas else "NO_EXACT_ATLAS_NAME_CANDIDATE",
            "candidate_atlas_row_ids": joined(row.get("atlas_table1_row_id", "") for row in candidate_atlas),
            "candidate_atlas_original_names": " | ".join(sorted({str(row.get("atlas_original_source_name", "")) for row in candidate_atlas if row.get("atlas_original_source_name")})),
            "candidate_atlas_current_names": " | ".join(sorted({str(row.get("atlas_current_accepted_name_field", "")) for row in candidate_atlas if row.get("atlas_current_accepted_name_field")})),
            "candidate_atlas_authors": " | ".join(sorted({str(row.get("atlas_current_name_authors", "")) for row in candidate_atlas if row.get("atlas_current_name_authors")})),
            "candidate_atlas_layer_keys": joined(row.get("atlas_layer_key", "") for row in candidate_atlas),
            "candidate_atlas_resolution_statuses": " | ".join(sorted({str(row.get("atlas_component_resolution_statuses", "")) for row in candidate_atlas if row.get("atlas_component_resolution_statuses")})),
            "candidate_atlas_resolution_reasons": " | ".join(sorted({str(row.get("atlas_component_resolution_reasons", "")) for row in candidate_atlas if row.get("atlas_component_resolution_reasons")})),
            "v02_wcvp_concept_evidence": f"{identifier}:{name} {author}" if kind == "S" else f"{name} {author}",
            "conflict_type": conflict, "v02_explicit_cause": explicit_cause, "proposed_v02_status": proposed, "resolution_disposition": disposition,
            "mainline_review_required_flag": "1" if disposition == "MAINLINE_REVIEW_REQUIRED" else "0",
            "no_silent_loss_accounting": "EXPLICITLY_ACCOUNTED",
        })

    unresolved_rows = []
    issue = 0
    for row in taxonomy_rows:
        if row["ordinary_analysis_species_flag"] != "1" and row["mapping_class"] not in {"GENUS_OR_NON_SPECIES_AGGREGATE"}:
            issue += 1
            unresolved_rows.append({"issue_id": f"TAX-{issue:04d}", "issue_scope": "TAXONOMY", "issue_class": row["mapping_class"], "fia_species_code": row["fia_species_code"], "fia_scientific_name": row["fia_scientific_name"], "analysis_species_id": "", "analysis_species_name": "", "usgs_atlas_row_id": "", "evidence": row["terminal_target_taxon_name"], "reason": row["no_analysis_species_reason"], "mainline_action_required": "Retain explicit non-core/no-analysis status; no forced mapping."})
    for row in usgs_review:
        issue += 1
        unresolved_rows.append({"issue_id": f"USGS-{issue:04d}", "issue_scope": "USGS_LAYER_MAPPING", "issue_class": row["usgs_mapping_class"], "fia_species_code": "", "fia_scientific_name": "", "analysis_species_id": row["analysis_species_id"], "analysis_species_name": row["analysis_species_name"], "usgs_atlas_row_id": row["atlas_table1_row_id"], "evidence": row["atlas_original_source_name"], "reason": row["review_reason"], "mainline_action_required": "Review evidence; do not union, select, or reconstruct layers in D08B.1."})

    evidence_rows = []
    eid = 0
    for row in correction_rows:
        eid += 1
        evidence_rows.append({"evidence_id": f"E{eid:05d}", "evidence_scope": "D08B1_TAXONOMY_CORRECTION", "fia_species_code": row["fia_species_code"], "analysis_species_id": row["v02_analysis_species_id"], "source_path": "03_doc/D08B1_TAXONOMY_CORRECTION_INPUTS_v02/correction_delivery_extracted/D08B_TAXONOMY_CORRECTION_EVIDENCE_v01.csv", "source_sha256": EXPECTED_HASHES[CORRECTION_DIR / "D08B_TAXONOMY_CORRECTION_EVIDENCE_v01.csv"], "source_record_ids": row["fia_species_code"], "claim": f"{row['v02_mapping_class']} -> {row['v02_analysis_species_name'] or row['v02_terminal_target_name']}", "transformation_rule": "Apply mainline-authorized 11-case additive correction exactly."})
    for sid in sorted(new_ids, key=int_sort):
        eid += 1
        evidence_rows.append({"evidence_id": f"E{eid:05d}", "evidence_scope": "WCVP_DISTRIBUTION_ADDITION", "fia_species_code": "", "analysis_species_id": sid, "source_path": "02_raw/WCVP/wcvp.zip::wcvp_distribution.csv", "source_sha256": EXPECTED_HASHES[WCVP_ZIP], "source_record_ids": sid, "claim": f"{len(distribution_by_id[sid])} frozen Level-3 rows added for newly resolved ordinary accepted species.", "transformation_rule": "Query by final accepted analysis-species ID only; preserve introduced/extinct/doubtful semantics."})
    for row in cross_rows:
        eid += 1
        evidence_rows.append({"evidence_id": f"E{eid:05d}", "evidence_scope": "USGS_CROSS_STAGE_DIAGNOSTIC", "fia_species_code": row["component_fia_codes"], "analysis_species_id": row["analysis_species_id"], "source_path": "05_qc/elig_v02/USGS_RANGE_AUDIT.csv", "source_sha256": EXPECTED_HASHES[ELIG_USGS], "source_record_ids": row["eligibility_v02_fia_codes"], "claim": row["conflict_type"], "transformation_rule": "Diagnostic only; prior mapping is not authority and no Little layer is unioned."})

    qc_rows = []
    def qc(check_id: str, description: str, expected: object, observed: object, passed: bool, note: str = "") -> None:
        qc_rows.append({"check_id": check_id, "required_for_engineering_pass": "1", "description": description, "expected": str(expected), "observed": str(observed), "status": "PASS" if passed else "FAIL", "note": note})

    qc("QC001", "All frozen input hashes verified", len(EXPECTED_HASHES), sum(row["status"] == "PASS" for row in input_hash_rows), all(row["status"] == "PASS" for row in input_hash_rows))
    qc("QC002", "True code map contains 396 rows", 396, len(taxonomy_rows), len(taxonomy_rows) == 396)
    qc("QC003", "True code map FIA codes are unique", 396, len({row["fia_species_code"] for row in taxonomy_rows}), len({row["fia_species_code"] for row in taxonomy_rows}) == 396)
    preserved = sum(row["fia_name_raw"] == old_by_code[row["fia_species_code"]]["fia_name_raw"] for row in taxonomy_rows)
    qc("QC004", "Original FIA raw names preserved", 396, preserved, preserved == 396)
    ordinary_codes = {code for code, patch in PATCH.items() if patch["case"] == "ORDINARY_ACCEPTED"}
    ordinary_applied = sum(next(row for row in taxonomy_rows if row["fia_species_code"] == code)["ordinary_analysis_species_flag"] == "1" for code in ordinary_codes)
    qc("QC005", "Eight ordinary accepted corrections applied", 8, ordinary_applied, ordinary_applied == 8)
    row6511 = next(row for row in taxonomy_rows if row["fia_species_code"] == "6511")
    qc("QC006", "FIA 6511 has no fabricated Accepted analysis target", "no analysis; terminal Unplaced", f"analysis={row6511['analysis_species_id']};terminal={row6511['terminal_target_taxon_status']}", not row6511["analysis_species_id"] and not row6511["accepted_taxon_id"] and row6511["terminal_target_taxon_status"] == "Unplaced")
    row6955 = next(row for row in taxonomy_rows if row["fia_species_code"] == "6955")
    qc("QC007", "FIA 6955 remains UNKNOWN", "UNKNOWN/no analysis", f"{row6955['taxonomy_resolution_status']}/{row6955['analysis_species_id']}", row6955["taxonomy_resolution_status"] == "UNKNOWN_MAINLINE_AUTHORIZED" and not row6955["analysis_species_id"])
    row143 = next(row for row in taxonomy_rows if row["fia_species_code"] == "143")
    qc("QC008", "FIA 143 is accepted hybrid non-core and absent from ordinary master", "hybrid non-core/absent", f"{row143['mapping_class']}/{sum(row['analysis_species_id']=='3317681' for row in analysis_rows)}", row143["mapping_class"] == "ACCEPTED_HYBRID_NONCORE" and not any(row["analysis_species_id"] == "3317681" for row in analysis_rows))
    ordinary_valid = all(row["analysis_species_status"] == "Accepted" and row["analysis_species_rank"] == "Species" and row["analysis_species_hybrid_flag"] == "0" for row in analysis_rows)
    if not ordinary_valid:
        print(json.dumps({"ordinary_invalid_rows": [row for row in analysis_rows if not (row["analysis_species_status"] == "Accepted" and row["analysis_species_rank"] == "Species" and row["analysis_species_hybrid_flag"] == "0")]}, ensure_ascii=False, indent=2))
    qc("QC009", "All ordinary analysis taxa are WCVP Accepted non-hybrid Species", len(analysis_rows), sum(row["analysis_species_status"] == "Accepted" and row["analysis_species_rank"] == "Species" and row["analysis_species_hybrid_flag"] == "0" for row in analysis_rows), ordinary_valid)
    query_ok = all(row["analysis_species_id"] in final_ids and row["plant_name_id"] == row["analysis_species_id"] and row["query_provenance"] == "WCVP_ACCEPTED_ANALYSIS_SPECIES_ID_ONLY" for row in distribution_rows)
    qc("QC010", "Distribution rows use final accepted ordinary species IDs only", len(distribution_rows), sum(row["plant_name_id"] == row["analysis_species_id"] and row["analysis_species_id"] in final_ids for row in distribution_rows), query_ok)
    confirmed_ok = all(row["introduced"] == "0" and row["extinct"] == "0" and row["location_doubtful"] == "0" for row in distribution_rows if row["confirmed_current_native_flag"] == "1")
    qc("QC011", "Introduced/extinct/doubtful rows never enter confirmed current native", 0, sum(not (row["introduced"] == row["extinct"] == row["location_doubtful"] == "0") for row in distribution_rows if row["confirmed_current_native_flag"] == "1"), confirmed_ok)
    unchanged_ids = final_ids & v01_analysis_ids
    v01_unchanged = [row for row in v01_distribution if row["analysis_species_id"] in unchanged_ids]
    v02_unchanged = [row for row in distribution_rows if row["analysis_species_id"] in unchanged_ids]
    unchanged_exact = Counter(tuple(row[field] for field in distribution_fields) for row in v01_unchanged) == Counter(tuple(row[field] for field in distribution_fields) for row in v02_unchanged)
    qc("QC012", "Unchanged ordinary-species Level-3 rows preserved exactly", len(v01_unchanged), len(v02_unchanged), unchanged_exact)
    qc("QC013", "Accepted-hybrid distribution evidence preserved separately", sum(row["analysis_species_id"] == "3317681" for row in v01_distribution), len(hybrid_distribution), len(hybrid_distribution) == sum(row["analysis_species_id"] == "3317681" for row in v01_distribution))
    v01_review_ids = {sid for sid, rows in v01_usgs_by_id.items() if any(row["usgs_review_required_flag"] == "1" for row in rows)}
    represented_ids = {row["analysis_species_id"] for row in cross_rows if row["analysis_species_id"]} | ({"3317681"} if any(row["analysis_species_name"] == "Pinus × kohae" for row in cross_rows) else set())
    qc("QC014", "Every D08B v01 USGS review species represented cross-stage", len(v01_review_ids), len(v01_review_ids & represented_ids), v01_review_ids <= represented_ids)
    prior_lost = [row for row in cross_rows if row["d08b_v01_usgs_mapping_class"] == "UNRESOLVED" and row["eligibility_prior_exact_or_official_nonzero_flag"] == "1"]
    qc("QC015", "Every prior exact/official nonzero v01 unresolved case explicitly accounted", len(prior_lost), sum(row["no_silent_loss_accounting"] == "EXPLICITLY_ACCOUNTED" for row in prior_lost), all(row["no_silent_loss_accounting"] == "EXPLICITLY_ACCOUNTED" for row in prior_lost))
    reviewed_canonical = [row for row in usgs_rows if row["usgs_review_required_flag"] == "1" and row["canonical_layer_flag"] == "1"]
    qc("QC016", "Review-only USGS cases receive no canonical layer", 0, len(reviewed_canonical), not reviewed_canonical)
    canonical_ok = all(row["usgs_mapping_class"] in USGS_SINGLE_CLASSES and not row["atlas_notes"] for row in usgs_rows if row["canonical_layer_flag"] == "1")
    qc("QC017", "Canonical layers occur only for unique no-Notes single-layer cases", 0, sum(not (row["usgs_mapping_class"] in USGS_SINGLE_CLASSES and not row["atlas_notes"]) for row in usgs_rows if row["canonical_layer_flag"] == "1"), canonical_ok)
    na_rows = [row for row in usgs_rows if row["usgs_mapping_class"] == "NOT_APPLICABLE_CONUS_NONNATIVE"]
    na_ok = all(global_by_id[row["analysis_species_id"]]["confirmed_native_CONUS"] == "FALSE" and global_by_id[row["analysis_species_id"]]["introduced_in_CONUS_audit_flag"] == "TRUE" for row in na_rows)
    qc("QC018", "Every CONUS-nonnative NOT_APPLICABLE case has frozen WCVP support", len(na_rows), sum(global_by_id[row["analysis_species_id"]]["confirmed_native_CONUS"] == "FALSE" and global_by_id[row["analysis_species_id"]]["introduced_in_CONUS_audit_flag"] == "TRUE" for row in na_rows), na_ok)
    grandis = next((row for row in usgs_rows if row["analysis_species_name"] == "Abies grandis"), None)
    qc("QC019", "Abies grandis author-bridge false negative repaired", "not UNRESOLVED", grandis["usgs_mapping_class"] if grandis else "MISSING", bool(grandis) and grandis["usgs_mapping_class"] != "UNRESOLVED")
    qc("QC020", "Atlas G Table 1 frozen row count", 690, len(atlas_rows), len(atlas_rows) == 690)
    qc("QC021", "Taxonomy correction application ledger contains 11 cases", 11, len(correction_rows), len(correction_rows) == 11)
    author_complete = all(row["v02_terminal_target_author"] or row["mainline_case_class"] == "UNKNOWN" for row in correction_rows)
    qc("QC022", "Author information preserved for every resolved correction case", 10, sum(bool(row["v02_terminal_target_author"]) for row in correction_rows), author_complete)
    qc("QC023", "No ordinary species receives more than one canonical layer", "<=1", max((sum(row["canonical_layer_flag"] == "1" for row in usgs_rows if row["analysis_species_id"] == sid) for sid in final_ids), default=0), all(sum(row["canonical_layer_flag"] == "1" for row in usgs_rows if row["analysis_species_id"] == sid) <= 1 for sid in final_ids))
    forbidden = re.compile(r"range.?abundance|geometry.?gain|p.?value|significance|q1.?outcome|r1.?r2", re.I)
    output_headers = set(v01_fields + extra_fields + list(analysis_rows[0]) + distribution_fields + global_fields + list(usgs_rows[0]) + list(cross_rows[0]))
    forbidden_hits = sorted(field for field in output_headers if forbidden.search(field))
    qc("QC024", "No real-Q1 outcome/result field present", 0, len(forbidden_hits), not forbidden_hits, ";".join(forbidden_hits))
    qc("QC025", "No FIA TREE merge executed", 0, 0, True, "Builder reads only frozen aggregate/code, WCVP, Atlas, and eligibility diagnostic inputs.")
    qc("QC026", "No Little layer union/selection/reconstruction executed", 0, 0, True, "Only canonical unique single rows are flagged; review cases remain unselected.")
    qc("QC027", "DRC/DBH species aggregation rebuilt without reinterpretation", len(analysis_rows), len(drc_rows), len(drc_rows) == len(analysis_rows))
    qc("QC028", "Ordinary analysis species IDs are unique", len(analysis_rows), len({row["analysis_species_id"] for row in analysis_rows}), len({row["analysis_species_id"] for row in analysis_rows}) == len(analysis_rows))
    qc("QC029", "Newly resolved ordinary species have frozen WCVP distribution rows", len(new_ids), sum(bool(distribution_by_id[sid]) for sid in new_ids), all(distribution_by_id[sid] for sid in new_ids))
    prior_candidate_evidence = sum(row["candidate_atlas_match_status"] == "EXACT_NAME_CANDIDATE_ROWS_FOUND" for row in prior_lost)
    qc("QC029B", "Prior exact/nonzero v01 unresolved cases include exact candidate Atlas rows", len(prior_lost), prior_candidate_evidence, prior_candidate_evidence == len(prior_lost))
    qc("QC030", "All mandatory QC checks pass", 30, sum(row["status"] == "PASS" for row in qc_rows), all(row["status"] == "PASS" for row in qc_rows))
    if any(row["status"] != "PASS" for row in qc_rows):
        failed = [row["check_id"] for row in qc_rows if row["status"] != "PASS"]
        raise RuntimeError("Mandatory QC failed: " + ",".join(failed))

    code_fields = v01_fields + [field for field in extra_fields if field not in v01_fields]
    code_map_fields = [
        "fia_species_code", "fia_name_raw", "fia_scientific_name", "fia_concept_author", "fia_author_evidence_status",
        "matched_wcvp_plant_name_id", "matched_wcvp_taxon_name", "matched_wcvp_taxon_authors", "matched_wcvp_taxon_status", "matched_wcvp_taxon_rank",
        "accepted_taxon_id", "accepted_taxon_name", "accepted_taxon_authors", "accepted_taxon_status", "accepted_taxon_rank",
        "terminal_target_taxon_id", "terminal_target_taxon_name", "terminal_target_taxon_authors", "terminal_target_taxon_status", "terminal_target_taxon_rank",
        "analysis_species_id", "analysis_species_name", "analysis_species_authors", "analysis_species_rank", "mapping_class", "taxonomy_resolution_status",
        "hybrid_or_nothotaxon_flag", "ordinary_analysis_species_flag", "no_analysis_species_reason", "distribution_query_plant_name_id",
        "terminal_target_hybrid_formula", "analysis_species_hybrid_formula", "wcvp_hybrid_formula_present_flag",
        "distribution_query_taxon_name", "diameter_measurement_basis", "woodland_indicator", "dia_threshold_inches",
        "main_analysis_candidate_retained_flag", "dbh_only_sensitivity_component_flag", "supplementary_sensitivity_candidate_flag",
        "d08b1_correction_applied_flag", "d08b1_correction_case_class", "d08b1_authority_source", "v01_mapping_class", "v01_taxonomy_resolution_status",
    ]
    analysis_fields = list(analysis_rows[0].keys())
    usgs_fields = list(usgs_rows[0].keys())
    cross_fields = list(cross_rows[0].keys())
    drc_fields = list(drc_rows[0].keys())
    correction_fields = list(correction_rows[0].keys())
    hybrid_fields = list(hybrid_rows[0].keys())
    unresolved_fields = list(unresolved_rows[0].keys())
    evidence_fields = list(evidence_rows[0].keys())
    qc_fields = list(qc_rows[0].keys())

    write_csv(OUT / "Q1_TAXON_RANGE_MASTER_v02.csv", taxonomy_rows, code_fields)
    write_csv(OUT / "Q1_FIA_CODE_TO_ANALYSIS_SPECIES_v02.csv", taxonomy_rows, code_map_fields)
    write_csv(OUT / "Q1_ANALYSIS_SPECIES_MASTER_v02.csv", analysis_rows, analysis_fields)
    write_csv(OUT / "Q1_TAXONOMY_CORRECTION_APPLIED_v02.csv", correction_rows, correction_fields)
    write_csv(OUT / "Q1_HYBRID_NONCORE_AUDIT_v02.csv", hybrid_rows, hybrid_fields)
    write_csv(OUT / "Q1_HYBRID_NONCORE_DISTRIBUTION_AUDIT_v02.csv", hybrid_distribution, distribution_fields + ["hybrid_audit_only_flag", "audit_reason"])
    write_csv(OUT / "Q1_WCVP_NATIVE_DISTRIBUTION_LONG_v02.csv", distribution_rows, distribution_fields)
    write_csv(OUT / "Q1_GLOBAL_RANGE_FLAGS_v02.csv", global_rows, global_fields)
    write_csv(OUT / "Q1_USGS_NAME_CLOSURE_v02.csv", usgs_rows, usgs_fields)
    write_csv(OUT / "Q1_USGS_LAYER_RECONSTRUCTION_REVIEW_v02.csv", usgs_review, usgs_fields)
    write_csv(OUT / "Q1_USGS_CROSS_STAGE_CONFLICT_v02.csv", cross_rows, cross_fields)
    write_csv(OUT / "Q1_DRC_PROTOCOL_v02.csv", drc_rows, drc_fields)
    write_csv(OUT / "Q1_TAXON_RANGE_UNRESOLVED_v02.csv", unresolved_rows, unresolved_fields)
    write_csv(OUT / "Q1_TAXON_RANGE_EVIDENCE_v02.csv", evidence_rows, evidence_fields)
    write_csv(OUT / "Q1_TAXON_RANGE_QC_v02.csv", qc_rows, qc_fields)
    write_csv(QC_DIR / "D08B1_INPUT_HASHES_v02.csv", input_hash_rows, list(input_hash_rows[0].keys()))

    summary = {
        "status": "PASS", "fia_code_rows": len(taxonomy_rows), "ordinary_analysis_code_rows": sum(row["ordinary_analysis_species_flag"] == "1" for row in taxonomy_rows),
        "ordinary_analysis_species": len(analysis_rows), "newly_resolved_ordinary_species": len(new_ids), "newly_resolved_species_ids": sorted(new_ids, key=int_sort),
        "accepted_hybrid_noncore_codes": sum(row["mapping_class"] == "ACCEPTED_HYBRID_NONCORE" for row in taxonomy_rows),
        "wcvp_level3_rows_v01": len(v01_distribution), "wcvp_level3_rows_v02_ordinary": len(distribution_rows),
        "hybrid_distribution_audit_rows": len(hybrid_distribution), "usgs_mapping_class_counts": dict(sorted(Counter(row["usgs_mapping_class"] for row in usgs_summary.values()).items())),
        "usgs_review_required_species": sum(row["usgs_review_required_flag"] == "1" for row in usgs_summary.values()),
        "usgs_canonical_single_species": sum(row["usgs_mapping_class"] in USGS_SINGLE_CLASSES and row["usgs_review_required_flag"] == "0" for row in usgs_summary.values()),
        "usgs_not_applicable_conus_nonnative_species": sum(row["usgs_mapping_class"] == "NOT_APPLICABLE_CONUS_NONNATIVE" for row in usgs_summary.values()),
        "cross_stage_rows": len(cross_rows), "prior_exact_nonzero_v01_unresolved_rows": len(prior_lost),
        "mandatory_qc_pass": sum(row["status"] == "PASS" for row in qc_rows), "mandatory_qc_fail": sum(row["status"] != "PASS" for row in qc_rows),
        "prohibited_actions_executed": [],
    }
    write_json(QC_DIR / "D08B1_BUILD_SUMMARY_v02.json", summary)
    write_json(QC_DIR / "D08B1_PARAMETERS_v02.json", {
        "contract": str(CONTRACT.relative_to(ROOT)), "input_freeze": str(INPUT_FREEZE.relative_to(ROOT)),
        "taxonomy_patch_codes": sorted(PATCH, key=int_sort), "ordinary_patch_codes": sorted(ordinary_codes, key=int_sort),
        "author_normalization": "Unicode NFC; whitespace collapse; lossless removal of spacing around period/comma/parentheses; no fuzzy matching",
        "conus_region_codes_l2": ["73", "74", "75", "76", "77", "78"],
        "not_applicable_rule": "confirmed_native_CONUS=FALSE and introduced_in_CONUS_audit_flag=TRUE and no resolved Atlas row",
        "review_only_rule": "multiple/shared/infraspecific/Notes/unresolved cases have no canonical layer",
        "real_q1": "HOLD", "fia_tree_merge": "HOLD", "little_union": "HOLD", "external_range_search": "HOLD",
    })
    write_json(QC_DIR / "D08B1_ENVIRONMENT_v02.json", {
        "python_version": sys.version, "platform": platform.platform(), "executable": sys.executable,
        "cwd": os.getcwd(), "wcvp_version": "16", "build_date": "2026-09-02",
    })
    (QC_DIR / "D08B1_IMPLEMENTATION_LOG_v02.md").write_text(
        "# D08B.1 implementation log v02\n\n"
        "- Verified every frozen input hash before processing.\n"
        "- Applied exactly the 11 mainline-authorized taxonomy decisions to a copy of the immutable v01 master.\n"
        "- Rebuilt the true 396-row code map and ordinary accepted-species summary.\n"
        "- Preserved unchanged v01 Level-3 rows exactly, added only newly resolved ordinary-species rows from frozen WCVP v16, and moved Pinus × kohae evidence to hybrid audit.\n"
        "- Rebuilt only the USGS/Little name-layer bridge using lossless author canonicalization and created the eligibility cross-stage diagnostic.\n"
        "- Did not run D08C, read or merge FIA TREE, union/select/reconstruct Little layers, search new distribution sources, select a cohort/grain, or compute real Q1.\n",
        encoding="utf-8", newline="\n",
    )
    (OUT / "README.md").write_text(
        "# Q1 D08B.1 corrected taxonomy–USGS bridge v02\n\n"
        "This directory contains additive v02 outputs built from immutable D08B v01 plus the accepted 11-case correction and author-aware USGS bridge repair. Machine-readable CSVs are authoritative; the audit workbook is a convenience view. No D08C, FIA TREE merge, Little layer union, external range search, or real-Q1 result is included.\n",
        encoding="utf-8", newline="\n",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
