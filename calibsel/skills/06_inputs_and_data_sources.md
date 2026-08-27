# Skill: Inputs & Data Sources — EDM/ESD provenance

## Description

Where the input data lives, how run numbers map to sources/backgrounds, and
how to switch datasets. Use this skill when a run cannot be found or when
processing new periods.

---

## Default Input: pre-existing ReProd26B EDM (lustrefs)

```
/lustrefs/juno26/users/zhaorz/Calib/ReProd26B/EDM_from_esd/Data/
    run_{RUN}_{i_start}_{i_end}.root        # 2799 chunks, built 2026-05-20
```

This is the dataset used by the original production chain and by the bitwise
audit (skill 10). `config/paths.py: REMOTE_EDM_DIR` points here; the default
`from-edm` mode reads it directly (read-only, nothing is written to lustrefs).

Check availability of a run:

```bash
ls /lustrefs/juno26/users/zhaorz/Calib/ReProd26B/EDM_from_esd/Data/ | grep -c "^run_12370"
```

Note: `EDM_from_miniesd/Data` on the same tree is **empty** — the miniesd
chain never produced chunks there. All verified data is in `EDM_from_esd`.

## Full ESD (only for `--full-esd`)

```
root://junoeos01.ihep.ac.cn//eos/juno/juno-reprod/ReProd26B/global_trigger/
    {run//1000*1000:08d}/{run//100*100:08d}_CalibData_phase{N}/{run}/*.esd
```

`src/list_esd.py` discovers and lists these (147 files for run 12370,
~532 MB each ≈ 75 GB per run → reconstruction takes hours).

## Run → source / background mapping

`calib_run_info/calib_to_analyze.txt` (frozen copy):

```
Source,StartRun-EndRun,PhysicsRun
Ge68,12344-12409,12419
Cs137,12110-12126,12129
...
```

- column 1: source type (drives nominal energy + robust scan config)
- column 2: calibration run range (which run you pass on the CLI)
- column 3: physics (background) run — auto-processed by Stage 2b

`calib_run_info/CalibRUN_from_file.csv` adds per-run date, ACU vertex
`X/Y/Z [m]` and source type — the physics QA uses it to place the ★ source
marker and compute the vertex-centroid distance.

## Choosing runs to process

Any run inside a mapped range can be processed, e.g.:

```bash
bash run_pipeline.sh 12355 12370 12388     # three Ge68 positions
```

`DEFAULT_RUNS` in `config/paths.py` defines what runs when no argument is
given — extend it for batch production, or wrap `pipeline/run_all.py` in your
own scheduler (it accepts `--runs` with any number of runs).

## Custom / rebuilt EDM

If you rebuild EDM chunks yourself (e.g. after a new JUNOSW tag):

```bash
bash run_pipeline.sh 12370 --full-esd --edm-input data/edm   # not needed, automatic
bash run_pipeline.sh 12370 --edm-input /path/to/my/chunks    # from-edm + custom dir
```

Remember: rebuilt chunks are only bitwise-identical to the reference for all
branches except `totalPE` (see skill 05). If you need the reference-exact
chain, use `REMOTE_EDM_DIR`.
