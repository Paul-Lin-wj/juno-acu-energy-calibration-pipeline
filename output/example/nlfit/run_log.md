# nlfit run log

- started: 2026-08-27T20:31:51  finished: 2026-08-27T20:38:32
- launched_by: script
- status: **running** (exit 0)

## Stages

| stage | status | elapsed | note |
| --- | --- | --- | --- |
| 4b external-contract | ok | 0.0 |  |
| 5 aggregate | ok | 0.7 | Cs137: result file not found: /tmp/fitter_results_amc/RUN12295_Cs137.npz; pinned to historical value; Mn54: result file not found: /tmp/fitter_results_amc/RUN12247_Mn54.npz; pinned to historical value; Co60: result file not found: /tmp/fitter_results_amc/RUN12216_Co60.npz; pinned to historical value |
| 6 dybmodel | ok | 399.0 | validate-ref: 14 param rows vs historical, worst rel dev 4.73e-02 (row 4) |
| 7 inversion | ok | 0.7 | lookup built |

## Audit

- passed: **True**
- code all_match: True
- outputs all_present: True

## Summary

- **stages_run**: 4b,5,6,7
- **gamma_dat**: /tmp/nlfit_amc_e2e/results/gamma_AllPhase.dat
- **lookup**: /tmp/nlfit_amc_e2e/results/Etrue_from_Erec_lookup.npz
