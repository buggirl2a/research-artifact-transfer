# Q1 D08B build correction log v01

Final-output freeze had not yet occurred. During pre-workbook audit, the initial USGS Table 1 transformation was found to ignore the author field when an Atlas accepted-name string had WCVP homonyms.

Concrete diagnostic: Atlas G identifies `Acer floridanum (Chapm.) Pax`. WCVP contains that authored name as `Unplaced`, while a distinct homonym `Acer floridanum Rössig` is a synonym with an accepted-species link. Name-only resolution would therefore assign the Atlas layer to the wrong accepted species.

Correction: slash-separated Atlas accepted names and authors are aligned component by component. When an exact Atlas name has multiple WCVP rows and an author is supplied, an exact author match is mandatory. An author-matched row with a disallowed/unresolved WCVP status remains unresolved; it is never replaced by a different author's usable row.

This correction implements the frozen exact-evidence and official-Table-1 rules. It does not change the candidate universe, taxonomic mapping classes, distribution rules, geographic flags, DRC/DBH rules, PASS criteria, or any scientific threshold. All final CSV/XLSX/archive hashes are produced only after the corrected build.

During visual workbook QA, QC017's expected-value label was corrected from `0` to `<=1`, matching its already-frozen rule and predicate. QC column widths/wrapping were also adjusted for legibility. Neither correction changed data results or PASS/FAIL evaluations.
