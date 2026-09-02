# Range Gate 0 v02 corrected engineering log

## Post-freeze delta preflight

The first delta-preflight attempt stopped before reading the v01 classification because the Python implementation sorted v01 file paths case-sensitively, while the pre-frozen PowerShell tree sentinel used case-insensitive `Sort-Object` ordering. The original PowerShell digest was recomputed and remained exactly `a415cbc84b66f6d0bf01c4cfaab3449e9e49e872bed7464cf2d71a29f65e9100`; the v01 ZIP, classification, and transfer-manifest hashes also remained exact.

The sentinel implementation was corrected to reproduce the frozen ordering. No v01 file, v02 scientific output, contract, class, route, reason, criterion, or threshold was changed.

## Final output-only audit serialization

The first final-audit write attempt completed the comparisons but could not serialize a diagnostic transition-count mapping whose display keys were Python tuples. The display mapping was converted to deterministic string keys. No scientific output, delta row, audit criterion, or result was changed.
