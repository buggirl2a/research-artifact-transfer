# D10A real-layout non-oracle observation calibration result

Terminal status: `CALIBRATION_COMPLETE_READY_FOR_MAINLINE_MODEL_FREEZE`

The frozen 48-state F0 layout contains 134,846 legitimate plot opportunities in 3,011 fixed 50-km cells. The experiment generated 72 fresh synthetic species in STRONG and PAIRED_NULL worlds under O1/O2/O3 observation stress, evaluated M0/M1/M2 in AB and BA, and did not read or estimate any real species result.

## Mainline reading rule

All candidate rows are returned. D10A defines no scientific PASS/FAIL threshold and selects no model. Mainline must freeze any observation model using synthetic-only evidence before real support is read.

## Compact comparison

model | world | regime | direction | Brier | IoU | support bias | truth geometry gain | set gain | truth coverage
---|---|---|---|---:|---:|---:|---:|---:|---:
M0 | PAIRED_NULL | O1 | AB | 0.0220 | 0.448 | -61.5 | -3.7% | -33.5% | 0.94
M0 | PAIRED_NULL | O1 | BA | 0.0187 | 0.562 | -51.0 | -3.8% | -17.1% | 0.81
M0 | PAIRED_NULL | O2 | AB | 0.0245 | 0.386 | -67.5 | -4.3% | -34.9% | 0.88
M0 | PAIRED_NULL | O2 | BA | 0.0207 | 0.489 | -55.0 | -6.6% | -28.5% | 0.88
M0 | PAIRED_NULL | O3 | AB | 0.0240 | 0.410 | -68.0 | -15.1% | -16.4% | 0.94
M0 | PAIRED_NULL | O3 | BA | 0.0190 | 0.562 | -49.0 | -9.5% | -29.5% | 0.94
M0 | STRONG | O1 | AB | 0.0214 | 0.485 | -59.5 | -47.2% | -72.9% | 0.94
M0 | STRONG | O1 | BA | 0.0181 | 0.556 | -50.0 | -54.6% | -24.3% | 0.88
M0 | STRONG | O2 | AB | 0.0241 | 0.414 | -68.0 | -50.6% | -66.6% | 0.94
M0 | STRONG | O2 | BA | 0.0203 | 0.509 | -54.0 | -39.7% | -92.9% | 0.88
M0 | STRONG | O3 | AB | 0.0234 | 0.443 | -65.0 | -27.2% | -126.5% | 1.00
M0 | STRONG | O3 | BA | 0.0189 | 0.565 | -49.5 | -41.8% | -49.4% | 0.94
M1 | PAIRED_NULL | O1 | AB | 0.0217 | 0.448 | -35.9 | 67.1% | 68.4% | 0.88
M1 | PAIRED_NULL | O1 | BA | 0.0185 | 0.562 | -23.8 | 54.6% | 69.2% | 0.88
M1 | PAIRED_NULL | O2 | AB | 0.0242 | 0.386 | -33.8 | 68.7% | 69.5% | 0.81
M1 | PAIRED_NULL | O2 | BA | 0.0205 | 0.489 | -20.2 | 61.7% | 62.3% | 0.88
M1 | PAIRED_NULL | O3 | AB | 0.0237 | 0.410 | -33.3 | 65.4% | 62.0% | 0.94
M1 | PAIRED_NULL | O3 | BA | 0.0188 | 0.562 | -13.7 | 65.1% | 62.0% | 0.94
M1 | STRONG | O1 | AB | 0.0211 | 0.485 | -29.8 | 57.9% | 67.0% | 0.81
M1 | STRONG | O1 | BA | 0.0179 | 0.556 | -24.2 | 53.8% | 68.5% | 0.81
M1 | STRONG | O2 | AB | 0.0238 | 0.414 | -33.2 | 66.9% | 70.0% | 0.88
M1 | STRONG | O2 | BA | 0.0201 | 0.509 | -21.3 | 63.5% | 57.9% | 0.88
M1 | STRONG | O3 | AB | 0.0231 | 0.443 | -24.9 | 69.9% | 70.0% | 1.00
M1 | STRONG | O3 | BA | 0.0187 | 0.565 | -11.9 | 58.7% | 48.1% | 1.00
M2 | PAIRED_NULL | O1 | AB | 0.0122 | 0.678 | -1.2 | 47.8% | 51.3% | 0.88
M2 | PAIRED_NULL | O1 | BA | 0.0097 | 0.746 | 7.4 | 42.8% | 49.3% | 0.94
M2 | PAIRED_NULL | O2 | AB | 0.0122 | 0.691 | 4.0 | 44.1% | 48.1% | 0.94
M2 | PAIRED_NULL | O2 | BA | 0.0093 | 0.790 | 16.0 | 45.7% | 50.3% | 0.81
M2 | PAIRED_NULL | O3 | AB | 0.0121 | 0.708 | 8.1 | 43.6% | 39.4% | 0.94
M2 | PAIRED_NULL | O3 | BA | 0.0091 | 0.816 | 21.5 | 41.2% | 38.5% | 1.00
M2 | STRONG | O1 | AB | 0.0103 | 0.707 | -5.7 | -12.4% | -0.2% | 0.94
M2 | STRONG | O1 | BA | 0.0079 | 0.780 | -0.8 | -19.2% | -15.9% | 0.88
M2 | STRONG | O2 | AB | 0.0112 | 0.712 | 5.2 | 39.9% | 25.0% | 0.94
M2 | STRONG | O2 | BA | 0.0085 | 0.799 | 13.5 | 7.1% | -42.4% | 0.94
M2 | STRONG | O3 | AB | 0.0111 | 0.733 | 9.9 | 37.1% | 16.5% | 1.00
M2 | STRONG | O3 | BA | 0.0085 | 0.821 | 18.9 | 8.0% | -0.4% | 0.88

## Provenance limitation

The exact E2c benchmark ZIP hash cited by the contract was not present locally. The available unpacked E2c methods were used only for scientific-object continuity; its generator-informed observation parameters were not used in M1/M2. This mismatch is recorded as non-blocking because the benchmark is not the F0 layout authority.

STOP: no real support, abundance, cohort, or Q1 effect analysis was run.
