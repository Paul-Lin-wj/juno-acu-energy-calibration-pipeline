# Skill: Setup Environment — standalone_esd2npz

## Description

How to create the virtual environment and (only for `--full-esd` mode) verify
the external JUNO software dependencies. Use this skill on a fresh machine or
after moving the project.

---

## Standard Setup (stages 1–4 only)

```bash
cd standalone_esd2npz
bash setup_env.sh
```

This creates `.venv/` (python3) and installs `requirements.txt`
(numpy, pandas, scipy, matplotlib, uproot). It also copies
`libpcre.so.1` from CVMFS into `lib/` **only if** the host lacks PCRE1 —
that library is needed exclusively by the `--full-esd` reconstruction stage.

Activate manually when calling stage scripts directly:

```bash
source .venv/bin/activate
```

Verify the install:

```bash
.venv/bin/python -c "import numpy,pandas,scipy,matplotlib,uproot;print('ok')"
```

## External Dependencies (ONLY for `--full-esd`)

Default mode (`from-edm`) needs **none** of these. `--full-esd` additionally
requires all of the following to be reachable (paths live in
`config/paths.py`):

| Path | Purpose |
|---|---|
| `/cvmfs/juno.ihep.ac.cn/.../J26.3.1/setup.sh` | JUNO offline software (Sniper, ROOT, xrootd client) |
| `/lustrefs/juno26/users/zhaorz/Calib/JUNOSW_MyAlgz/InstallArea/setup.sh` | MySimpleTag algorithm build (2026-06-06) |
| `/lustrefs/.../JUNOSW_MyAlgz/SimpleTagAlgz/share/run.py` | ESD→EDM reconstruction entry |
| `root://junoeos01.ihep.ac.cn//eos/juno/...` | ESD files on EOS (note the **double slash**) |

Quick check:

```bash
ls /cvmfs/juno.ihep.ac.cn/el9_amd64_gcc11/Release/J26.3.1/setup.sh \
   /lustrefs/juno26/users/zhaorz/Calib/JUNOSW_MyAlgz/InstallArea/setup.sh
```

## Known Environment Gotchas (already handled by the code)

1. **EOS xrootd double-slash URLs** — `root://host//eos/...` is required by
   the IHEP EOS gateway; single slash returns
   `[3010] Opening relative path ... is disallowed`. `src/list_esd.py`
   generates the correct form.
2. **libpcre.so.1 missing** on newer distros (EL9 ships it, Ubuntu 24 does
   not). `setup_env.sh` copies the single file from CVMFS anaconda into
   `lib/`; the Stage-0 wrapper prepends only that directory to
   `LD_LIBRARY_PATH` (adding the whole anaconda lib dir would shadow the
   system libstdc++ and break with `GLIBCXX_3.4.29 not found`).
3. **xrdfs needs the full CVMFS environment** — `src/list_esd.py` captures
   PATH/LD_LIBRARY_PATH by sourcing the CVMFS setup in a sub-shell.
4. **matplotlib cache warning** — harmless; the pipeline sets
   `MPLCONFIGDIR` to `TMP/matplotlib`.
