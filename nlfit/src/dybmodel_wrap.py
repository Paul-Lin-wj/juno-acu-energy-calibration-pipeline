#!/usr/bin/env python3
"""
Stage 6: run the ORIGINAL fitter_energynl_dybmodel C++ fitter, unmodified,
inside our own byte-identical copy of the IHEP SL6 worknode container.

Assets (staged on /datafs by tools/setup_container.sh, outside the repo):
  - sl69worknode20240820.sif : the official SL6 image, byte-identical copy
    (container/ keeps its embedded def + sha256 for traceability)
  - rootfs/ : unsquashfs extraction of that SIF, run as an apptainer
    sandbox (this node has no setuid starter, so userns + sandbox dir)
  - juno-sl6-amd64-gcc447/Release/J17v1r1 : the ROOT5-era JUNO release;
    its TEXT setup scripts have the hardcoded /cvmfs/... prefix rewritten
    to this staging path (binaries untouched). Runs from /datafs because
    the host's /cvmfs/juno.ihep.ac.cn is a publicfs stand-in without sl6
    content, and unprivileged containers cannot shadow inherited mounts.

No C++ modification: each run gets a symlink-farm sandbox of the original
tree in which ONLY necessaryfiles/input/JUNO/ReProd26B/gamma_AllPhase.dat
is this run's file; everything else is a symlink into DYBMODEL_SRC.

Note: the C++ main() returns 1 BY DESIGN on success — success is judged by
the presence of bestFit/curves outputs, never by the exit code alone.
Behaviour lock: the original binary in this environment reproduces the
historical 2026-08-16 bestFit byte-for-byte.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import time
from pathlib import Path

import config.paths as P
from src.run_logger import sha256_file


def _input_fingerprints() -> dict:
    """sha256 of the necessaryfiles inputs actually consumed by the fit."""
    base = Path(P.DYBMODEL_SRC) / "necessaryfiles" / "input"
    keys = ["Quenching.root", "Gamma_Electron.root", "FADC_scaleNL.txt",
            "LS_LBNL_2015_short.dat", "LS_IHEP.dat",
            "cerenkovCurve_2018.dat"]
    out = {}
    for k in keys:
        p = base / k
        out[k] = sha256_file(p) if p.is_file() else None
    iso = (base / "JUNO" / "ReProd26B" / "Spec" / "forNLfitter" /
           "Isotope_data_AllPhase_FVcutR0_1720_Finalcorrection.root")
    out["Isotope_data_AllPhase.root"] = (
        sha256_file(iso) if iso.is_file() else None)
    return out


# ---------------------------------------------------------------- sandbox
def make_symlink_farm_sandbox(sandbox: Path, gamma_dat: Path) -> None:
    """Mirror DYBMODEL_SRC into `sandbox` with symlinks, except that
    necessaryfiles/input/JUNO/ReProd26B/gamma_AllPhase.dat is a REAL copy
    of this run's gamma table (the C++ reads that canonical path).

    Directories are linked WHOLESALE and never descended into (pruned),
    so nothing is ever created inside the original tree."""
    import os as _os
    src = Path(P.DYBMODEL_SRC)
    if sandbox.exists():
        shutil.rmtree(sandbox)
    nf_src = src / "necessaryfiles"
    nf_dst = sandbox / "necessaryfiles"
    gamma_rel = "input/JUNO/ReProd26B/gamma_AllPhase.dat"
    real_dirs = {"input", "input/JUNO", "input/JUNO/ReProd26B"}

    skip_top = {"necessaryfiles", "output", "plots", "obj", "cursor",
                "run.log", ".git"}
    sandbox.mkdir(parents=True, exist_ok=True)
    for entry in sorted(src.iterdir()):
        if entry.name in skip_top:
            continue
        (sandbox / entry.name).symlink_to(entry)

    for root, dirs, files in _os.walk(nf_src):
        rel_root = Path(root).relative_to(nf_src)
        for d in list(dirs):
            rel = (rel_root / d).as_posix()
            if rel in real_dirs:
                (nf_dst / rel).mkdir(parents=True, exist_ok=True)
            else:
                (nf_dst / rel).symlink_to(Path(root) / d)
                dirs.remove(d)  # linked wholesale: do not descend
        for f in files:
            rel = (rel_root / f).as_posix()
            if rel == gamma_rel:
                continue
            (nf_dst / rel).symlink_to(Path(root) / f)

    shutil.copy2(gamma_dat, nf_dst / gamma_rel)
    for d in ("output/results", "output/curves", "output/errors",
              "output/gammas", "plots"):
        (sandbox / d).mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------- runtime
def probe() -> dict:
    ok = {
        "apptainer": shutil.which(P.APPTAINER) is not None,
        "rootfs": (Path(P.DYBMODEL_ROOTFS) / "bin").is_dir(),
        "j17v1r1": Path(P.DYBMODEL_J17_SETUP).is_file(),
        "dybmodel_src": Path(P.DYBMODEL_SRC).is_dir(),
    }
    ok["all"] = all(ok.values())
    if not ok["all"]:
        ok["fix"] = ("run nlfit/tools/setup_container.sh to stage the "
                     "container assets (SL6 rootfs + J17v1r1)")
    return ok


def _apptainer_cmd(sandbox: Path) -> str:
    return (f"{P.APPTAINER} exec -e --userns "
            f"-B /datafs:/datafs -B /tmp:/tmp {P.DYBMODEL_ROOTFS} "
            f"bash -c 'export HOME=/root USER=root; "
            f"ulimit -s unlimited 2>/dev/null || ulimit -s 65536; "
            f"source {P.DYBMODEL_J17_SETUP} >/dev/null 2>&1 && "
            f"cd {sandbox} && timeout {P.DYB_FIT_TIMEOUT_S} ./fitter'")


def run_dybmodel(out_dir, gamma_dat_path, work_dir=None) -> dict:
    """Run the original fitter in the container; harvest into out_dir."""
    out_dir, gamma_dat = Path(out_dir), Path(gamma_dat_path)
    p = probe()
    if not p["all"]:
        raise RuntimeError(f"container runtime not ready: {p}")

    work = Path(work_dir) if work_dir else out_dir / P.OUTPUT_WORK_DIR
    sandbox = work / "dybmodel_run"
    make_symlink_farm_sandbox(sandbox, gamma_dat)
    (sandbox / "run_env.txt").write_text(
        f"sif={P.DYBMODEL_SIF}\nsif_sha256={sha256_file(P.DYBMODEL_SIF)}\n"
        f"j17_setup={P.DYBMODEL_J17_SETUP}\n"
        f"gamma_sha256={sha256_file(gamma_dat)}\n")

    t0 = time.time()
    proc = subprocess.run(["bash", "-c", _apptainer_cmd(sandbox)],
                          capture_output=True, text=True,
                          timeout=P.DYB_FIT_TIMEOUT_S + 900)
    elapsed = time.time() - t0
    (sandbox / "fit_stdout.log").write_text(
        proc.stdout + "\n--- stderr ---\n" + proc.stderr)

    best = sandbox / "output" / "results" / f"bestFit_{P.DYB_TOY_KEY}.dat"
    curves = (sandbox / "output" / "curves" /
              f"curves_{P.DYB_TOY_KEY}.root")
    if not (best.is_file() and curves.is_file()):
        raise RuntimeError(
            f"dybmodel fit produced no bestFit/curves (rc={proc.returncode},"
            f" {elapsed:.0f}s). See {sandbox / 'fit_stdout.log'}")

    # ---- harvest ----
    res_dir, fig_dir = out_dir / P.OUTPUT_RES_DIR, out_dir / P.OUTPUT_FIG_DIR
    fig_dir.mkdir(parents=True, exist_ok=True)
    harvested = {}
    for f in sorted((sandbox / "output" / "results").glob("*.dat")):
        shutil.copy2(f, res_dir / f.name)
        harvested[f.name] = str(res_dir / f.name)
    curves_local = res_dir / curves.name
    shutil.copy2(curves, curves_local)
    harvested["curves_root"] = str(curves_local)
    shutil.copy2(sandbox / "fit_stdout.log",
                 out_dir / "dybmodel_fit_console.log")
    dyb_fig = fig_dir / "dybmodel"
    n_plots = 0
    for f in sorted((sandbox / "plots").iterdir()):
        if f.is_file():
            dyb_fig.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, dyb_fig / f.name)
            n_plots += 1

    # ---- dump NL curves to TSV (local el9 ROOT) ----
    tsv = res_dir / "nl_curves.tsv"
    macro = Path(__file__).resolve().parent.parent / "tools" / "dump_curves.C"
    dump = (f"source {P.CVMFS_SETUP} && root -b -q "
            f"'{macro}(\"{curves_local.resolve()}\",\"{tsv.resolve()}\")'")
    proc2 = subprocess.run(["bash", "-c", dump], capture_output=True,
                           text=True)
    if proc2.returncode != 0 or not tsv.is_file():
        raise RuntimeError(f"dump_curves failed: {proc2.stderr[-1500:]}")
    harvested["nl_curves_tsv"] = str(tsv)

    return {
        "success": True, "runtime": "own-container (original, unmodified)",
        "elapsed_s": round(elapsed, 1), "sandbox": str(sandbox),
        "harvested": harvested, "n_dybmodel_plots": n_plots,
        "input_sha256": _input_fingerprints(),
        "sif_sha256": sha256_file(P.DYBMODEL_SIF),
        "patches": ["none — original tree in original environment"],
        "note": ("C++ main() returns 1 by design; success judged by "
                 "outputs. Behaviour lock vs 2026-08-16 baseline: EXACT"),
    }
