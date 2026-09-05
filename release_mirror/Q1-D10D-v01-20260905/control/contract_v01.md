# D10D frozen execution contract v01

Task: `D10D_ZERO_OPPORTUNITY_MEASURABLE_DOMAIN_SOURCE_ATTRIBUTION_v01`

Frozen before any D10D diagnostic state was evaluated. This contract permits only the observation-domain transformations defined below. It does not authorize a new abundance estimator, support estimator, estimand choice, or real-species analysis.

## Frozen identities

- D10C resume ZIP: `C:\range_paper\10_archive\d10cr\D10CR_v01.zip`; SHA-256 `5ae34a71d50c8bea0809cef77d9835051926f3ea3455b41b2ed913860bab64b1`.
- D10C-A authority ZIP: `C:\range_paper\10_archive\d10ca\D10CA_v01.zip`; SHA-256 `c8f73406f7f192b8f124add3cb0ded7ea65474e8d72d752e37dc557a08588865`.
- D10B oracle-reference ZIP: `C:\range_paper\10_archive\d10b_oracle_source_decomposition_v01\Q1_D10B_ORACLE_SUPPORT_DOWNSTREAM_SOURCE_DECOMPOSITION_REPRODUCIBLE_v01.zip`; SHA-256 `cb041fca5897f31c8ea0bf2a3b29a262a5c83ef44bdfda9a37a0394cfc7cafeb`.
- The inherited D10A layout/parameter ZIP identified by D10C remains fixed at SHA-256 `20e5d3ed33df6414b72a6e679d5349f3b10fe6397ce73f98b51d0bcc96033013`.
- Request file SHA-256: `37f555ce071ea1afec988df302398183f6fdf5c03c94c4b86dff353058aeaacb`.

The frozen D10C cell tables supply the 72 synthetic species, both worlds, oracle supports, latent allocations, and realized A2 cell masses. The synthetic universe will not be regenerated. The inherited D10A package is used only to reconstruct the exact 3,011-cell coordinate/signature layout and legal A/B opportunity frame required by the frozen downstream functions.

## Diagnostic states

- `A0_REF`: exact full-domain D10B/D10C latent-truth oracle reference.
- `D0`: exact current A2 cell masses, full latent truth, and full oracle support.
- `D1`: in every target-fold cell with zero legal opportunities, replace only A2 mass with frozen latent A0 mass; retain every positive-opportunity A2 mass; then normalize on full support. Full oracle support geometry and full latent truth remain unchanged. D1 is oracle-assisted and unusable as a real-data method.
- `D2`: orientation-specific target-fold measurable domain. AB uses cells with at least one legal B-fold opportunity; BA uses cells with at least one legal A-fold opportunity. Intersect support, latent truth, and A2 with the same domain, normalize both abundance layers there, and derive geometry only from the intersected support.
- `D3`: one species-blind common domain consisting of cells with at least one legal A opportunity and at least one legal B opportunity. Apply it identically to all species, worlds, and orientations; intersect support, latent truth, and A2; normalize within the common domain; derive geometry from the restricted support.
- `D2_A0_REF` and `D3_A0_REF` are auxiliary latent-truth references on the corresponding restricted domains. They separate domain-induced signal changes from residual A2 measurement distortion and are not alternative estimands.

## Frozen downstream machinery

The D10B oracle-support model fitting, five released split seeds, train/calibration/test allocation, World 0, conformal scoring, three observation-regime labels, spatial signature, geometry representation, gain definitions, and AB/BA assignments remain byte-for-byte sourced from the frozen code. No refit or parameter change is permitted outside the state-specific domain inputs above.

## Frozen quantitative summaries

- Official downstream rows retain all split-level metrics. STRONG-minus-PAIRED_NULL separation uses the frozen paired rows.
- State gap to a matching latent reference is `state separation - reference separation`.
- Movement toward the full A0 reference is `state separation - D0 separation`.
- Fraction of the full D0-to-A0 separation gap removed is `(state - D0) / (A0_REF - D0)` and is descriptive only.
- Cell-map recovery uses the same Hellinger and sliced-Wasserstein definitions as D10C. D2/D3 compare A2 and A0 after both are normalized on the same restricted domain.
- Domain cost reports exact cell counts, target-fold plot counts, fold-specific TI-weight sums, support-cell retention, and latent-mass retention.
- No severe-truncation threshold is selected. A descriptive cutoff frontier will report full counts at several support-loss and mass-loss cutoffs for mainline use.
- Relationships are reported as Pearson and Spearman correlations. Species-level map relationships use all 72 species per world/orientation. Downstream relationships use only frozen held-out test occurrences and split-level official scores; no new split is created.

## Computational PASS/FAIL only

The package may complete only if all frozen hashes match; D0 reproduces the frozen D10C A2 downstream rows within maximum absolute numeric difference `1e-10`; the 72-species/two-world/AB-BA identities match; D1 leaves every positive-opportunity A2 cell unchanged before normalization; D2/D3 support, truth, A2, and geometry domains are identical within each state; all normalized maps sum to one within `1e-12`; no required state has empty species support or zero total mass; deterministic hashes validate; and local absolute plus ZIP-member paths are each shorter than 256 characters.

These are implementation gates only. No numerical scientific PASS/HOLD/FAIL threshold, acceptable domain-loss threshold, estimator winner, or final Q1 domain rule is defined.

Allowed successful terminal status: `ZERO_OPPORTUNITY_SOURCE_ATTRIBUTION_COMPLETE_READY_FOR_MAINLINE`.

STOP after the frozen D0/D1/D2/D3 package. Do not run support recovery, abundance repair, real species, real World 0, or real Q1.
