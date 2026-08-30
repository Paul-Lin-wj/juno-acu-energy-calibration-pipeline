#!/usr/bin/env python3
"""run_inventory.csv — 全部刻度/物理 run 的单表全量视图。

行 = rtraw 刻度全集 ∪ 物理 good 全集（并集），列 = 事实表信息 + 两套
DQ 状态 + ESD 存在性。启动链路前的 run check 数据底座：sort/filter/grep
皆宜，agent 可直接程序化消费（口径与细节见 runcheck/SKILL.md）。
"""
import csv
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
DATA = HERE / "data"

# ---- 事实表：刻度 run 信息 ----
info = {}
with open(DATA / "CalibRUN_from_file.csv", newline="") as fh:
    for r in csv.DictReader(fh):
        info[int(r["RUN"])] = r

# ---- phase 区间 ----
phase_ranges = []
with open(HERE.parent / "calibsel/input/correction/data/ValProd26BPhase.csv",
          newline="") as fh:
    for row in csv.DictReader(fh):
        name = next(v for v in row.values() if v and v.strip())
        lo, hi = (int(x) for x in row["Run Range"].split("-"))
        phase_ranges.append((int(name.split()[-1]), lo, hi))
phase_ranges.sort()
P1_LO = phase_ranges[0][1]

def phase_of(run):
    if run < P1_LO:
        return "pre-P1"
    for n, lo, hi in phase_ranges:
        if lo <= run <= hi:
            return f"P{n}"
    return ""

# ---- 两套 DQ + ESD ----
calib_good = set()
for f in (DATA / "calib_runlist").glob("*_calibration_good.txt"):
    calib_good |= {int(l) for l in f.read_text().split() if l.strip().isdigit()}
physics_good = set()
for f in (DATA / "goodrunlist_v5.0.5").glob("*/physics_good.txt"):
    physics_good |= {int(l) for l in f.read_text().split() if l.strip().isdigit()}
rtraw = set()
for f in (DATA / "calib_runlist/rtraw_runnames").glob("*.txt"):
    rtraw |= {int(l) for l in f.read_text().split() if l.strip().isdigit()}
kup_esd = set()
for f in (DATA / "calib_runlist/kup_esd_runnames").glob("*.txt"):
    kup_esd |= {int(l) for l in f.read_text().split() if l.strip().isdigit()}

# ---- 并集输出 ----
all_runs = sorted(rtraw | physics_good | set(info))
out = DATA / "run_inventory.csv"
n_centre = 0
with open(out, "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["run", "phase", "date", "source", "x_m", "y_m", "z_m",
                "is_centre", "in_calib_table",
                "calib_good", "prephase1_rtraw", "physics_good", "in_kup_esd",
                "run_kind"])
    for run in all_runs:
        r = info.get(run)
        if r:
            z = float(r["Z[m]"])
            centre = abs(z) <= 0.5
            kind = "calib-source" + (" centre" if centre else " z-scan")
            if r["Source"] == "K40":
                kind = "calib-source K40"
            n_centre += centre
            row = [run, phase_of(run), r["Date"], r["Source"],
                   r["X[m]"], r["Y[m]"], r["Z[m]"],
                   int(centre), 1, "", "", "", "", kind]
        else:
            row = [run, phase_of(run), "", "", "", "", "",
                   "", 0, "", "", "", "", "other-calibration" if run in rtraw
                   else "physics"]
        row[9] = int(run in calib_good)
        row[10] = int(run < P1_LO and run in rtraw) if run < P1_LO else ""
        row[11] = int(run in physics_good)
        row[12] = int(run in kup_esd)
        w.writerow(row)

print(f"rows: {len(all_runs)}  (rtraw {len(rtraw)} ∪ physics_good {len(physics_good)} "
      f"∪ calib_table {len(info)}), centre runs: {n_centre}")
print(f"saved {out}")
