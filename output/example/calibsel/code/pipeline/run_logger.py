"""
run_logger.py — audit-grade run logging for the standalone_esd2npz pipeline.

Schema 2.0, aligned with the standalone_fitter logging discipline:

  pipeline_metadata: launched_by, command[], exit_code, start/end (UTC+local),
    system (hostname/user/platform/python_version/python_executable), git
    (commit/branch/has_uncommitted_changes), packages (core versions),
    pip_freeze, config_files + config_snapshot (path+sha256+size of every
    tunable file), errors[]
  runs[]: per-run records — run_info (date/position from CalibRUN.csv),
    input fingerprints (EDM dir, chunk count), event_statistics (counts,
    energy range/mean/median, 200-bin pre-selection spectrum), stage detail
    with per-stage status/elapsed, cut references, output fingerprints
  code_snapshot/ + sha256 of every algorithm file (the authoritative record
    of the cut/selection logic)

On unhandled exceptions a traceback.log is written and status=failed; failed
runs still dump the log (partial stage records preserved).
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import socket
import subprocess
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

SCHEMA_VERSION = "2.0"

# Algorithm files whose exact content defines the processing (and the cuts).
# Anything listed here is copied verbatim into code_snapshot/ at run start.
CODE_FILES = [
    "src/convert_edm_to_npz.py",
    "src/apply_final_correction.py",
    "src/combine_selection.py",
    "src/local_utils.py",
    "src/esd_to_edm.py",
    "src/list_esd.py",
    "input/correction/correction_api.py",
    "config/paths.py",
    "pipeline/run_all.py",
    "pipeline/cuts_parser.py",
]

# Config/tunable files fingerprinted (path+sha256+size) in config_snapshot.
CONFIG_FILES = [
    "config/paths.py",
    "requirements.txt",
    "calib_run_info/calib_to_analyze.txt",
    "calib_run_info/CalibRUN_from_file.csv",
    "input/correction/correction_api.py",
]


def sha256_file(path) -> str:
    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return "unavailable"


def file_info(path) -> dict:
    p = Path(path)
    return {
        "path": str(p.resolve()),
        "exists": p.exists(),
        "size_bytes": p.stat().st_size if p.exists() else None,
        "sha256": sha256_file(path) if p.exists() else None,
    }


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _now_local() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S %Z")


def _core_packages():
    pkgs = {}
    for name in ("numpy", "pandas", "scipy", "matplotlib", "uproot"):
        try:
            mod = __import__(name)
            pkgs[name] = getattr(mod, "__version__", "unknown")
        except Exception:
            pkgs[name] = "not-installed"
    return pkgs


def _pip_freeze():
    try:
        r = subprocess.run(
            [sys.executable, "-m", "pip", "freeze", "--all"],
            capture_output=True, text=True, timeout=60)
        return sorted(l for l in r.stdout.splitlines() if l.strip())
    except Exception:
        return []


def _git_info(root: Path) -> dict:
    def _git(*args):
        try:
            return subprocess.run(
                ["git", "-C", str(root), *args], capture_output=True,
                text=True, timeout=10).stdout.strip()
        except Exception:
            return ""
    commit = _git("rev-parse", "HEAD")
    return {
        "commit": commit or "not-a-repo",
        "branch": _git("rev-parse", "--abbrev-ref", "HEAD"),
        "has_uncommitted_changes": bool(_git("status", "--porcelain"))
        if commit else None,
    }


class RunLogger:
    """Context manager that records everything about one pipeline run."""

    def __init__(self, output_dir: Path, project_root: Path,
                 launched_by: str = "script"):
        self.output_dir = Path(output_dir)
        self.project_root = Path(project_root)
        self.launched_by = launched_by
        self._exit_code: int | None = None
        self.data = {
            "schema_version": SCHEMA_VERSION,
            "run_id": datetime.now().strftime("%Y%m%dT%H%M%S")
                      + "_" + os.urandom(3).hex(),
            "status": "running",
            "launched_by": launched_by,
            "command": [os.path.basename(sys.argv[0]), *sys.argv[1:]],
            "exit_code": None,
            "pipeline_metadata": {
                "timestamp_start_utc": _now_utc(),
                "timestamp_start_local": _now_local(),
                "system": {
                    "hostname": socket.gethostname(),
                    "user": os.environ.get("USER", ""),
                    "platform": platform.platform(),
                    "python_version": sys.version.split()[0],
                    "python_executable": sys.executable,
                    "timestamp_utc": _now_utc(),
                },
                "git": _git_info(project_root),
                "packages": _core_packages(),
                "pip_freeze": _pip_freeze(),
                "config_files": {},   # name -> absolute path
                "config_snapshot": {},  # name -> {path, sha256, size_bytes}
                "timestamp_end_utc": None,
                "timestamp_end_local": None,
                "elapsed_s": None,
            },
            "errors": [],
            "runs": [],       # per-run records (see add_run)
            "outputs": [],    # global deliverable list (also per-run)
        }
        self._t0 = time.time()
        self._fh = None

    # ---------------- console tee ----------------
    class ConsoleTee:
        def __init__(self, stream, logger):
            self.stream, self.logger = stream, logger

        def write(self, text):
            self.stream.write(text)
            if self.logger._fh:
                self.logger._fh.write(text)
                self.logger._fh.flush()
            return len(text)

        def flush(self):
            self.stream.flush()

    def __enter__(self):
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._fh = open(self.output_dir / "console.log", "w")
        return self

    def __exit__(self, exc_type, exc, tb):
        md = self.data["pipeline_metadata"]
        md["timestamp_end_utc"] = _now_utc()
        md["timestamp_end_local"] = _now_local()
        md["elapsed_s"] = round(time.time() - self._t0, 2)
        if exc_type is not None:
            # unhandled exception: write traceback.log, mark failed
            with open(self.output_dir / "traceback.log", "w") as f:
                traceback.print_exception(exc_type, exc, tb, file=f)
            self.data["exit_code"] = self._exit_code if self._exit_code is not None else 1
            self.data["status"] = "failed"
            self.add_error("unhandled-exception", f"{exc_type.__name__}: {exc}")
        elif self._exit_code is not None:
            self.data["exit_code"] = self._exit_code
            self.data["status"] = "failed" if self._exit_code != 0 else "completed"
        else:
            self.data["exit_code"] = 0
            self.data["status"] = "completed"
        self.data["summary"] = {
            "n_runs": len(self.data["runs"]),
            "n_ok": sum(1 for r in self.data["runs"] if r.get("status") == "ok"),
            "n_failed": sum(1 for r in self.data["runs"] if r.get("status") != "ok"),
            "n_outputs": sum(len(r.get("outputs", []))
                            for r in self.data["runs"]),
            "n_errors": len(self.data["errors"]),
        }
        self.dump()
        if self._fh:
            self._fh.close()
        return False

    # ---------------- records ----------------
    def set_pipeline_info(self, **kw):
        """Free-form pipeline-level info (mode, runs, dirs, ...)."""
        self.data.setdefault("pipeline", {}).update(kw)
        self.dump()

    def set_exit_code(self, code: int):
        self._exit_code = int(code)

    def add_error(self, source: str, message: str):
        self.data["errors"].append({
            "timestamp_utc": _now_utc(),
            "source": source,
            "message": str(message),
        })

    # ---------------- full code snapshot + audit ----------------
    def _iter_source_files(self):
        """Yield relative paths of every source file in the project tree
        (same exclusion rule as the snapshot; includes untracked files).

        Excludes only ROOT-LEVEL runtime dirs (.venv, data, output, TMP,
        audit_report, .git) and python caches — nested data dirs such as
        input/correction/data/ (the correction models, part of the algorithm)
        are kept.
        """
        excludes = {".venv", "data", "output", "TMP", "audit_report", ".git"}
        for path in sorted(self.project_root.rglob("*")):
            if path.is_dir():
                continue
            rel = path.relative_to(self.project_root)
            if rel.parts[0] in excludes:
                continue
            if "__pycache__" in rel.parts:
                continue
            if path.name.endswith(".pyc") or \
               path.name.startswith("esd_list_"):
                continue
            yield rel

    def snapshot_code_full(self) -> dict:
        """Copy the COMPLETE code tree into output/<ts>/code/ + sha256.json.

        This is the run-time provenance snapshot: every source file that
        produced this run's data, byte-for-byte. Returns a summary dict.
        """
        code_dir = self.output_dir / "code"
        code_dir.mkdir(parents=True, exist_ok=True)
        hashes = {}
        n = 0
        for rel in self._iter_source_files():
            src = self.project_root / rel
            dst = code_dir / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            try:
                shutil.copy2(src, dst)
            except OSError as e:
                self.add_error("code-snapshot", f"copy {rel}: {e}")
                continue
            hashes[str(rel)] = sha256_file(src)
            n += 1
        with open(code_dir / "sha256.json", "w") as f:
            json.dump(hashes, f, indent=1)
        return {"n_files": n, "sha256_file": "code/sha256.json"}

    def run_audit(self, expected_outputs: list) -> dict:
        """End-of-run completeness audit.

        1. code/: every source file present and sha256-identical to the
           working tree (no missing/mismatched/extra files);
        2. outputs/: every expected deliverable file exists.

        Result is written into run_log.json["audit"] and shown in run_log.md.
        """
        code_dir = self.output_dir / "code"
        audit = {
            "timestamp_utc": _now_utc(),
            "code_snapshot": {"n_files": 0, "all_match": False,
                              "missing": [], "mismatched": [], "extra": []},
            "outputs": {"all_present": False, "missing": []},
            "passed": False,
        }
        # --- code completeness ---
        snap_sha = {}
        sha_file = code_dir / "sha256.json"
        if sha_file.exists():
            try:
                snap_sha = json.loads(sha_file.read_text())
            except Exception:
                snap_sha = {}
        src_rels = [str(r) for r in self._iter_source_files()]
        # physical presence inside code/ (files listed but deleted from snapshot)
        missing_in_snap = [r for r in snap_sha
                           if not (code_dir / r).exists()]
        # byte-identity: snapshot copy vs working tree
        mismatched = [r for r in snap_sha
                      if (code_dir / r).exists()
                      and sha256_file(code_dir / r)
                      != sha256_file(self.project_root / r)]
        # source files never snapshotted
        missing_from_src = [r for r in src_rels if r not in snap_sha]
        extra = sorted(set(snap_sha) - set(src_rels))
        missing = sorted(set(missing_in_snap) | set(missing_from_src))
        audit["code_snapshot"].update(
            n_files=len(snap_sha),
            all_match=not (missing or mismatched or extra),
            missing=missing, mismatched=mismatched, extra=extra)
        # --- output completeness ---
        miss_out = [str(p) for p in expected_outputs if not Path(p).exists()]
        audit["outputs"].update(all_present=not miss_out, missing=miss_out)
        audit["passed"] = (audit["code_snapshot"]["all_match"]
                           and audit["outputs"]["all_present"])
        self.data["audit"] = audit
        self.dump()
        return audit


    def add_run(self, *, run: int, status: str, source: str | None = None,
                run_info: dict | None = None, input: dict | None = None,
                event_statistics: dict | None = None,
                stages: list | None = None,
                cuts_ref: str | None = None,
                outputs: list | None = None) -> None:
        """Append one per-run audit record (mirrors fitter's sources[])."""
        self.data["runs"].append({
            "run": int(run),
            "source": source,
            "status": status,
            "run_info": run_info or {},
            "input": input or {},
            "event_statistics": event_statistics or {},
            "stages": stages or [],
            "cuts_ref": cuts_ref,
            "outputs": outputs or [],
        })
        self.dump()

    def add_output(self, path, kind):
        p = Path(path)
        self.data["outputs"].append({
            "kind": kind, "path": str(p),
            "size_bytes": p.stat().st_size if p.exists() else None,
            "sha256": sha256_file(p) if p.exists() else None,
        })

    def dump(self):
        with open(self.output_dir / "run_log.json", "w") as f:
            json.dump(self.data, f, indent=1, ensure_ascii=False)
        with open(self.output_dir / "run_log.md", "w") as f:
            f.write(self._markdown())

    # ---------------- snapshots ----------------
    def snapshot_code(self):
        """Copy algorithm files + hashes: the authoritative cut/provenance record."""
        snap = self.output_dir / "code_snapshot"
        snap.mkdir(parents=True, exist_ok=True)
        hashes = {}
        for rel in CODE_FILES:
            src = self.project_root / rel
            if not src.exists():
                continue
            dst = snap / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(src.read_bytes())
            hashes[rel] = sha256_file(src)
        with open(snap / "sha256.json", "w") as f:
            json.dump(hashes, f, indent=1)
        return hashes

    def snapshot_config(self):
        """Fingerprint every tunable/config file (mirrors fitter config_snapshot)
        and write the standalone config_snapshot.json next to the run log."""
        md = self.data["pipeline_metadata"]
        for name in CONFIG_FILES:
            path = self.project_root / name
            md["config_files"][name] = str(path.resolve())
            md["config_snapshot"][name] = file_info(path)
        with open(self.output_dir / "config_snapshot.json", "w") as f:
            json.dump(md["config_snapshot"], f, indent=1, ensure_ascii=False)

    # ---------------- markdown ----------------
    def _markdown(self) -> str:
        d = self.data
        md = d["pipeline_metadata"]
        L = [f"# Run Log — standalone_esd2npz (schema {SCHEMA_VERSION})", "",
             f"**Run ID**: `{d['run_id']}`  |  **Status**: `{d['status']}`  |  "
             f"**Elapsed**: {md.get('elapsed_s', '?')} s", "",
             f"**Command**: `{' '.join(d['command'])}`", "",
             f"**Exit code**: `{d['exit_code']}`", "",
             "## System Information", "",
             "| Field | Value |", "|---|---|"]
        for k, v in md["system"].items():
            L.append(f"| {k} | `{v}` |")
        L += ["", "## Code Version", "",
              "| Field | Value |", "|---|---|"]
        for k, v in md["git"].items():
            L.append(f"| Git {k} | `{v}` |")
        if md["git"].get("has_uncommitted_changes"):
            L += ["", "> Warning: Working tree has uncommitted changes."]
        L += ["", "## Package Versions", ""]
        for k, v in md["packages"].items():
            L.append(f"- **{k}**: `{v}`")
        L += ["", "## Configuration Files", "",
              "| Config | Path | SHA-256 |", "|---|---|---|"]
        for name, info in md["config_snapshot"].items():
            sh = (info.get("sha256") or "n/a")[:16] + "..."
            L.append(f"| {name} | `{info['path']}` | `{sh}` |")
        if d["errors"]:
            L += ["", "## Errors", ""]
            for e in d["errors"]:
                L.append(f"- `{e['timestamp_utc']}` [{e['source']}] {e['message']}")
        L += ["", "## Pipeline", ""]
        for k, v in d.get("pipeline", {}).items():
            L.append(f"- **{k}**: `{v}`")
        L += ["", "## Audit (end-of-run completeness)", ""]
        a = d.get("audit")
        if not a:
            L.append("_no audit record (audit not executed for this run)_")
        else:
            cs, oo = a["code_snapshot"], a["outputs"]
            L += ["| Check | Result |", "|---|---|"]
            L.append(f"| code/ snapshot files | `{cs['n_files']}` |")
            L.append(f"| code all sha256 match | `{cs['all_match']}` |")
            if cs["missing"]:
                L.append(f"| missing in code/ | `{', '.join(cs['missing'][:8])}` |")
            if cs["mismatched"]:
                L.append(f"| sha256 mismatch | `{', '.join(cs['mismatched'][:8])}` |")
            if cs["extra"]:
                L.append(f"| extra in code/ | `{', '.join(cs['extra'][:8])}` |")
            L.append(f"| outputs all present | `{oo['all_present']}` |")
            if oo["missing"]:
                L.append(f"| missing outputs | `{', '.join(oo['missing'][:8])}` |")
            L.append(f"| **audit passed** | **`{a['passed']}`** |")
        L += ["", "## Per-Run Records", ""]
        for r in d["runs"]:
            st = "OK" if r.get("status") == "ok" else r.get("status", "?")
            L.append(f"\n### [{st}] {'RUN' + str(r['run'])}"
                     f"{' — ' + r['source'] if r.get('source') else ''}\n")
            L += ["| Field | Value |", "|---|---|"]
            L.append(f"| Status | {r.get('status')} |")
            ri = r.get("run_info") or {}
            for k, v in ri.items():
                L.append(f"| {k} | `{v}` |")
            inp = r.get("input") or {}
            if inp:
                L.append(f"| EDM dir | `{inp.get('edm_dir')}` |")
                L.append(f"| EDM chunks | `{inp.get('n_chunks')}` |")
            es = r.get("event_statistics") or {}
            if es:
                L.append(f"| Events (total / finite) | "
                         f"`{es.get('total_events')} / {es.get('finite_events')}` |")
                L.append(f"| Energy min/max | "
                         f"`{es.get('energy_min')} / {es.get('energy_max')} MeV` |")
                L.append(f"| Energy mean/median | "
                         f"`{es.get('energy_mean')} / {es.get('energy_median')} MeV` |")
            if r.get("cuts_ref"):
                L.append(f"| Cuts | `{r['cuts_ref']}` |")
            L += ["", "| stage | status | seconds | detail |", "|---|---|---|---|"]
            for s in r.get("stages", []):
                det = s.get("detail", "")
                if isinstance(det, dict):
                    det = "; ".join(f"{k}={v}" for k, v in det.items())
                L.append(f"| {s.get('stage','')} | {s.get('status','')} | "
                         f"{s.get('elapsed_s','')} | {det} |")
            if r.get("outputs"):
                L += ["", "| output | kind | sha256 |", "|---|---|---|"]
                for o in r["outputs"]:
                    sh = (o.get("sha256") or "n/a")[:16]
                    L.append(f"| `{o['path']}` | {o['kind']} | `{sh}...` |")
        L += ["", f"See `code_snapshot/sha256.json` for the exact algorithm "
                  f"versions (cut logic) used by this run, and `cuts/` for the "
                  f"run-specific selection conditions."]
        return "\n".join(L) + "\n"
