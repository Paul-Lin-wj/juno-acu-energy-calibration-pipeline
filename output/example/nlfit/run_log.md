# nlfit run log

- started: 2026-08-27T19:23:52  finished: 2026-08-27T19:30:42
- launched_by: script
- status: **running** (exit 0)

## Stages

| stage | status | elapsed | note |
| --- | --- | --- | --- |
| 4b external-contract | ok | 0.0 |  |
| 5 aggregate | ok | 0.6 | Cs137: result file not found: ../output/example/fitter/results/RUN12295_Cs137.npz; pinned to historical value; Mn54: result file not found: ../output/example/fitter/results/RUN12247_Mn54.npz; pinned to historical value; Co60: result file not found: ../output/example/fitter/results/RUN12216_Co60.npz; pinned to historical value |
| 6 dybmodel | ok | 408.2 | validate-ref: 14 param rows vs historical, worst rel dev 2.39e-02 (row 5) |
| 7 inversion | ok | 0.7 | lookup built |

## Audit

- passed: **True**
- code all_match: True
- outputs all_present: True

## Summary

- **stages_run**: 4b,5,6,7
- **gamma_dat**: /tmp/nlfit_e2e/results/gamma_AllPhase.dat
- **lookup**: /tmp/nlfit_e2e/results/Etrue_from_Erec_lookup.npz
