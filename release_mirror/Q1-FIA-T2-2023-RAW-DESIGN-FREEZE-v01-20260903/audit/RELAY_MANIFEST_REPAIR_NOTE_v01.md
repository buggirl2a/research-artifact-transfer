# Q1 FIA T2 2023 Relay manifest repair note v01

Status: TRANSPORT_ONLY_REPAIR
Generated: 2026-09-03T17:35:24.7228865+08:00
Frozen scientific root: C:\range_paper\02_raw\fia_t2_2023_raw_design_v01
Original downloader result: unchanged
Original transfer manifest retained unchanged at: C:\range_paper\02_raw\fia_t2_2023_raw_design_v01\manifests\TRANSFER_MANIFEST_v01.csv
Audit copy: C:\range_paper\02_raw\fia_t2_2023_raw_design_v01\relay_payload_v01\audit\SOURCE_TRANSFER_MANIFEST_PRE_RELAY_SCHEMA_v01.csv

Reason:
The downloader-generated TRANSFER_MANIFEST_v01.csv used descriptive transport fields but did not use the Research Artifact Relay v0.2.2 native relative_path schema. This repair does not alter, recompute, extract, re-download, re-compress, or overwrite any frozen FIA raw/provenance asset.

Repair action:
- only rows previously marked MUST_RELAY=YES are staged;
- source byte size and SHA-256 are verified before copy;
- staged copies are byte-identical and re-hashed;
- raw_table_zips remain local and are not staged;
- a Relay-native manifest is generated with fields:
  local_path, relative_path, role, upload_target, required, mainline_priority, size_bytes, sha256, notes;
- upload_target is mirror for compact evidence in this transport repair.

Scientific boundary:
No D09C, component-EVALID inference, A/B partition, TI/MA comparison, TREE access, abundance/detection analysis, or real Q1 is performed.
