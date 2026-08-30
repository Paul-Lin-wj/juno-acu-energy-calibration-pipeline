#!/usr/bin/env python3
"""run type vs date：ValProd26B 各刻度源在时间轴上的可用性。

一源一行、x 轴日期、竖直灰带 = phase 实际时间跨度（带名标在顶部）。
只画中心 run（|z|≤0.5 m）——能量刻度实际消费的就是它们；非中心 z 扫描
位置与 run 号不上图，需要时查 phase_centre_runs() / 聚合表。

绘制规范：academic-research-skills / statistical_visualization_standards.md
（Tol 色盲安全板、颜色×形状双编码、无 chartjunk、300 dpi）。
"""
import csv
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

SUITE = Path(__file__).resolve().parents[2]  # runcheck/tools -> repo root
RUNS_CSV = Path(__file__).resolve().parents[1] / "data" / "CalibRUN_from_file.csv"
PHASE_CSV_SRC = SUITE / "calibsel/input/correction/data/ValProd26BPhase.csv"
PHASE_CSV = PHASE_CSV_SRC

ROWS = ["Ge68", "Cs137", "Mn54", "Co60", "K40", "AmC117"]
ROW_LABEL = {"AmC117": "AmC"}
STYLE = {
    "Ge68":   ("#0077BB", "o"),
    "Cs137":  ("#CC3311", "s"),
    "Mn54":   ("#EE7733", "^"),
    "Co60":   ("#009988", "D"),
    "K40":    ("#EE3377", "v"),
    "AmC117": ("#33BBEE", "P"),
}

plt.rcParams.update({
    "font.family": "sans-serif", "font.sans-serif": ["DejaVu Sans"],
    "font.size": 9, "axes.labelsize": 10,
    "xtick.labelsize": 8, "ytick.labelsize": 8.5,
    "figure.dpi": 300, "savefig.dpi": 300,
    "axes.spines.top": False, "axes.spines.right": False,
})

runs = []
with open(RUNS_CSV, newline="") as fh:
    for r in csv.DictReader(fh):
        runs.append({
            "run": int(r["RUN"]),
            "date": datetime.strptime(r["Date"], "%Y-%m-%d"),
            "z": float(r["Z[m]"]),
            "source": r["Source"],
        })

phases = []
with open(PHASE_CSV, newline="") as fh:
    for row in csv.DictReader(fh):
        name = next(v for v in row.values() if v and v.strip())
        lo, hi = (int(x) for x in row["Run Range"].split("-"))
        in_ph = [r for r in runs if lo <= r["run"] <= hi]
        phases.append({"name": name.replace("Phase ", "P"), "lo": lo, "hi": hi,
                       "d0": min(r["date"] for r in in_ph),
                       "d1": max(r["date"] for r in in_ph)})

P1_LO = phases[0]["lo"]
n_rows = len(ROWS)
row_of = {s: i for i, s in enumerate(ROWS)}
# phase 标签放 axes 内部顶行（ylim 顶部留出一行），与 axes 上方的副行
# 小字、更上方的加粗 title 各占独立空间，互不接触
LABEL_Y = n_rows + 0.32

fig, ax = plt.subplots(figsize=(6.9, 3.6))

# phase 时间带：交替灰带（无边界线——带间色差即边界），带名标顶部
for p, ph in enumerate(phases):
    x0, x1 = ph["d0"] - timedelta(days=2), ph["d1"] + timedelta(days=2)
    if p % 2 == 1:
        ax.axvspan(x0, x1, color="0.0", alpha=0.05, zorder=0)
    xc = x0 + (x1 - x0) / 2
    ha = "right" if ph["name"] == "P4" else "center"   # P4 带中心贴右缘，右对齐防出界
    ax.text(xc, LABEL_Y, ph["name"],
            ha=ha, va="center", fontsize=8.5, color="0.25")

# pre-P1 时间带（试运行周，最左）：带太窄，标签右移 + 细引导线（全图唯一一条线）
pre = [r for r in runs if r["run"] < P1_LO]
d_last = max(r["date"] for r in pre)
ax.axvspan(datetime(2025, 8, 20), d_last + timedelta(days=1),
           color="0.0", alpha=0.05, zorder=0)
ax.annotate("pre-P1",
            xy=(d_last, LABEL_Y), xytext=(datetime(2025, 9, 14), LABEL_Y),
            ha="left", va="center", fontsize=8.5, color="0.25",
            arrowprops=dict(arrowstyle="-", lw=0.6, color="0.45",
                            shrinkA=0, shrinkB=1))

# 中心 run：一 mark 一日期；同日多个（Ge68 10801/03/05）横向微摊开
by_day = defaultdict(list)
for r in runs:
    if abs(r["z"]) <= 0.5 and r["source"] in row_of:
        by_day[(r["source"], r["date"])].append(r)

for (src, date), group in sorted(by_day.items()):
    colour, marker = STYLE[src]
    n = len(group)
    for i, r in enumerate(sorted(group, key=lambda x: x["run"])):
        dx = timedelta(days=(i - (n - 1) / 2) * 1.0)
        ax.plot(date + dx, row_of[src], marker, ms=7,
                mfc=colour, mec="black", mew=0.4, ls="none", zorder=4)

ax.set_yticks(range(n_rows))
ax.set_yticklabels([ROW_LABEL.get(s, s) for s in ROWS])
ax.set_ylim(-0.35, n_rows + 0.55)
ax.set_xlabel("Date")
ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
ax.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
ax.set_xlim(datetime(2025, 8, 15), datetime(2026, 5, 8))
# 副行小字：axes 分数坐标 (0.5, 1.02)，正落在主 title（pad 22）与其下方之间
ax.text(0.5, 1.028, "sources at detector centre (|z| ≤ 0.5 m)",
        transform=ax.transAxes, fontsize=8, ha="center", va="bottom",
        color="0.25")
ax.set_title("ValProd26B Calibration Source Run", fontsize=10.5,
             fontweight="bold", pad=15)
fig.subplots_adjust(top=0.855, bottom=0.24, left=0.09, right=0.98)


out = Path(__file__).resolve().parents[1] / "run_date_map"
plt.savefig(out.with_suffix(".png"))
plt.savefig(out.with_suffix(".pdf"))
print(f"saved {out}.png / .pdf")
