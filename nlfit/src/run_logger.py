#!/usr/bin/env python3
"""
Slim run logger for the nlfit module — same artifact contract as the
sibling calibsel/fitter loggers (run_log.{md,json}, config_snapshot.json,
console.log, code/ + sha256.json, end-of-run audit), reduced to the
stages this module runs (4b contract, 5 aggregate, 6 dybmodel, 7 invert).
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from pathlib import Path

SCHEMA_VERSION = "1.0"
# code files that define this module's behaviour (snapshot + audit scope)
_CODE_GLOBS = ["config/*.py", "src/*.py", "pipeline/*.py", "tools/*",
               "run_pipeline.sh", "setup_env.sh", "external_inputs/*"]


def sha256_file(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


class ConsoleTee:
    """Tee stdout/stderr into the logger's console.log."""

    def __init__(self, stream, logger):
        self._stream, self._logger = stream, logger

    def write(self, data):
        self._stream.write(data)
        self._logger._console.write(data)
        self._logger._console.flush()

    def flush(self):
        self._stream.flush()


class RunLogger:
    def __init__(self, output_dir, project_root, launched_by="script",
                 agent_name="", agent_version="", agent_workflow=""):
        self.out = Path(output_dir)
        self.out.mkdir(parents=True, exist_ok=True)
        self.root = Path(project_root)
        self.data = {
            "schema": SCHEMA_VERSION,
            "module": "nlfit",
            "launched_by": launched_by,
            "agent": {"name": agent_name, "version": agent_version,
                      "workflow": agent_workflow},
            "started_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "system": {
                "hostname": os.uname().nodename,
                "python": sys.version.split()[0],
                "argv": sys.argv,
            },
            "stage_records": [],
            "errors": [],
            "status": "running",
            "exit_code": 0,
        }
        self._console = open(self.out / "console.log", "a", encoding="utf-8")

    # ---------------------------------------------------------------- api
    def set_pipeline_info(self, **kw):
        self.data.setdefault("pipeline_metadata", {}).update(kw)

    def add_stage(self, stage, status="ok", elapsed_s=None, detail=None,
                  outputs=None):
        self.data["stage_records"].append({
            "stage": stage, "status": status, "elapsed_s": elapsed_s,
            "detail": detail or {}, "outputs": outputs or {},
        })

    def add_error(self, stage, message):
        self.data["errors"].append(
            {"stage": stage, "message": message,
             "at": time.strftime("%Y-%m-%dT%H:%M:%S")})

    def snapshot_config(self):
        """Fingerprint the effective config (paths.py + MANIFEST + env)."""
        import config.paths as P  # noqa: PLC0415
        cfg = {
            "fitter_results_dir": str(P.FITTER_RESULTS_DIR),
            "external_manifest": str(P.EXTERNAL_MANIFEST),
            "peaks": [{"key": k, "e_true": e, "provider": p, "run_id": r}
                      for k, e, p, r in P.PEAKS],
            "dybmodel_src": str(P.DYBMODEL_SRC),
            "dybmodel_container": str(P.DYBMODEL_CONTAINER_DIR),
            "dybmodel_j17": str(P.DYBMODEL_J17),
            "cvmfs_setup": P.CVMFS_SETUP,
            "dyb_toy_key": P.DYB_TOY_KEY,
            "cwd": os.getcwd(),
        }
        path = self.out / "config_snapshot.json"
        path.write_text(json.dumps(cfg, indent=2, ensure_ascii=False))
        self.data["config_snapshot"] = str(path)

    def snapshot_code(self):
        """Copy this module's code tree to code/ with sha256 index."""
        dest = self.out / "code"
        dest.mkdir(parents=True, exist_ok=True)
        index = {}
        for pattern in _CODE_GLOBS:
            for f in sorted(self.root.glob(pattern)):
                if not f.is_file() or ".venv" in f.parts:
                    continue
                rel = f.relative_to(self.root)
                target = dest / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(f.read_bytes())
                index[rel.as_posix()] = sha256_file(f)
        (dest / "sha256.json").write_text(
            json.dumps(index, indent=2, sort_keys=True))
        self.data["code_snapshot"] = {
            "n_files": len(index),
            "index_path": str(dest / "sha256.json"),
        }
        return self.data["code_snapshot"]

    def run_audit(self, expected_outputs):
        """Verify code snapshot matches the working tree byte-for-byte and
        every expected deliverable exists. Flushes run_log.{md,json} first
        so the logs themselves can be part of the expected outputs."""
        self._write_logs()
        cs, oo = {"all_match": True, "missing": [], "mismatched": [],
                  "extra": []}, {"all_present": True, "missing": []}
        snap_index = json.loads(
            (self.out / "code" / "sha256.json").read_text())
        current = {}
        for pattern in _CODE_GLOBS:
            for f in sorted(self.root.glob(pattern)):
                if f.is_file() and ".venv" not in f.parts:
                    current[f.relative_to(self.root).as_posix()] = sha256_file(f)
        for rel in snap_index:
            if rel not in current:
                cs["missing"].append(rel)
            elif current[rel] != snap_index[rel]:
                cs["mismatched"].append(rel)
        for rel in current:
            if rel not in snap_index:
                cs["extra"].append(rel)
        cs["all_match"] = not (cs["missing"] or cs["mismatched"])
        for p in expected_outputs:
            if not Path(p).exists():
                oo["missing"].append(str(p))
        oo["all_present"] = not oo["missing"]
        audit = {"passed": cs["all_match"] and oo["all_present"],
                 "code_snapshot": cs, "outputs": oo,
                 "checked_at": time.strftime("%Y-%m-%dT%H:%M:%S")}
        self.data["audit"] = audit
        return audit

    def set_summary(self, summary):
        self.data["summary"] = summary

    def set_exit_code(self, code):
        self.data["exit_code"] = int(code)
        if code == 0 and self.data["status"] == "running":
            self.data["status"] = "ok"

    def record_command(self, argv):
        self.data["system"]["argv"] = list(argv)

    # ------------------------------------------------------------- writer
    def _write_logs(self):
        self.data["finished_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        (self.out / "run_log.json").write_text(
            json.dumps(self.data, indent=2, ensure_ascii=False, default=str))
        lines = [
            "# nlfit run log", "",
            f"- started: {self.data['started_at']}  "
            f"finished: {self.data.get('finished_at', '')}",
            f"- launched_by: {self.data['launched_by']}",
            f"- status: **{self.data['status']}** "
            f"(exit {self.data['exit_code']})", "",
            "## Stages", "",
            "| stage | status | elapsed | note |",
            "| --- | --- | --- | --- |",
        ]
        for r in self.data["stage_records"]:
            note = r["detail"].get("note", "")
            lines.append(f"| {r['stage']} | {r['status']} | "
                         f"{r['elapsed_s'] if r['elapsed_s'] is not None else ''} "
                         f"| {note} |")
        if self.data["errors"]:
            lines += ["", "## Errors", ""]
            lines += [f"- [{e['stage']}] {e['message']}"
                      for e in self.data["errors"]]
        if "audit" in self.data:
            a = self.data["audit"]
            lines += ["", "## Audit", "",
                      f"- passed: **{a['passed']}**",
                      f"- code all_match: {a['code_snapshot']['all_match']}",
                      f"- outputs all_present: {a['outputs']['all_present']}"]
        if "summary" in self.data:
            lines += ["", "## Summary", ""]
            for k, v in self.data["summary"].items():
                lines.append(f"- **{k}**: {v}")
        (self.out / "run_log.md").write_text("\n".join(lines) + "\n")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        if exc_type is not None:
            self.data["status"] = "failed"
            self.add_error("exception", f"{exc_type.__name__}: {exc}")
            self.data["exit_code"] = 1
        self._write_logs()
        self._console.close()
        return False
