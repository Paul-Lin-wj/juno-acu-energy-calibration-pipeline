#!/usr/bin/env python3
"""Calibration run inventory figures (the run-vs-date convention).

REFERENCE implementation of the plotting convention described in
.claude/skills/calib-run-timeline/SKILL.md — draw these figures through
this script rather than re-implementing, so every user's version of the
figure is comparable (same source colours/markers, phase bands, fonts,
legend placement, dual-format output).

Figures over calibsel/calib_run_info/CalibRUN_from_file.csv:
  fig1  run-vs-date timeline: x = date, y = source (nominal-E order),
        marker+colour per source, filled = centre run (|z|<=CENTRE_Z),
        ValProd26B phases shaded (run ranges -> dates, gap-midpoint edges)
  fig2  z-scan coverage: source z position vs date, acrylic sphere edge
  fig3  data-taking cadence: runs/day stacked by source + cumulative

Usage:
  calibsel/.venv/bin/python calibsel/tools/plot_run_inventory.py \
      [--out-dir DIR] [--figs all|1,2,3] [--centre-z 0.5]
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timedelta
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

# ---- style contract (see SKILL.md; do not weaken without updating it) ----
plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Nimbus Roman", "Liberation Serif", "Times New Roman",
                   "DejaVu Serif"],
    "mathtext.fontset": "stix",
    "font.size": 14,
    "axes.labelsize": 16,
    "axes.titlesize": 17,
    "xtick.labelsize": 13,
    "ytick.labelsize": 14,
    "legend.fontsize": 13,
    "axes.linewidth": 1.1,
    "savefig.dpi": 200,
})

REPO = Path(__file__).resolve().parents[2]
CSV = REPO / "calibsel" / "calib_run_info" / "CalibRUN_from_file.csv"
PHASE_CSV = (REPO / "calibsel" / "input" / "correction" / "data" /
             "ValProd26BPhase.csv")

SRC_ORDER = ["Cs137", "Mn54", "Ge68", "Co60", "K40", "AmC117"]  # by nominal E
SRC_LABEL = {
    "Cs137": "Cs137  0.662", "Mn54": "Mn54  0.835", "Ge68": "Ge68  2$\\times$511",
    "Co60": "Co60  1.17/1.33", "K40": "K40  1.461",
    "AmC117": "AmC  2.22/4.94/6.13",
}
SRC_STYLE = {   # FIXED mapping — comparability across users/versions
    "Cs137": ("tab:blue", "o"), "Mn54": ("tab:orange", "s"), "Ge68": ("tab:green", "^"),
    "Co60": ("tab:red", "D"), "K40": ("tab:purple", "*"), "AmC117": ("tab:brown", "v"),
}


def load_runs(csv_path):
    rows = []
    with Path(csv_path).open(newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            rows.append({
                "run": int(r["RUN"]),
                "date": datetime.strptime(r["Date"], "%Y-%m-%d"),
                "x": float(r["X[m]"]), "y": float(r["Y[m]"]), "z": float(r["Z[m]"]),
                "source": r["Source"],
            })
    rows.sort(key=lambda r: (r["date"], r["run"]))
    return rows


def load_phases(phase_csv):
    phases = []
    with Path(phase_csv).open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            p = int(next(v for v in row.values() if v and v[0] == "P").split()[-1])
            lo, hi = (int(v) for v in row["Run Range"].split("-"))
            phases.append((p, lo, hi))
    return sorted(phases)


def phase_spans(rows, phases):
    """phase -> (first_date, last_date) among the runs, + gap-midpoint edges."""
    def phase_of(run):
        for p, lo, hi in phases:
            if lo <= run <= hi:
                return p
        return 0
    span = {}
    for r in rows:
        p = phase_of(r["run"])
        d0, d1 = span.get(p, (r["date"], r["date"]))
        span[p] = (min(d0, r["date"]), max(d1, r["date"]))
    ordered = sorted(span)
    edges = [span[ordered[0]][0] - timedelta(days=3)]
    for left, right in zip(ordered, ordered[1:]):
        gap_a, gap_b = span[left][1], span[right][0]
        edges.append(gap_a + (gap_b - gap_a) / 2)
    edges.append(span[ordered[-1]][1] + timedelta(days=3))
    return ordered, span, edges


def shade_phases(ax, ordered, edges, label=True):
    for i, p in enumerate(ordered):
        ax.axvspan(edges[i], edges[i + 1], color="tab:blue" if i % 2 else "tab:gray",
                   alpha=0.07, lw=0, zorder=0)
        if label:
            mid = edges[i] + (edges[i + 1] - edges[i]) / 2
            ax.text(mid, 1.025, f"P{p}" if p else "pre-P1", ha="center",
                    va="bottom", fontsize=15, fontweight="bold", color="0.35",
                    transform=ax.get_xaxis_transform())


def fmt_axis(ax):
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.tick_params(axis="x", rotation=45)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


def deterministic_jitter(run):
    """Same jitter for the same run id on every machine (no random state)."""
    return ((run * 2654435761) % 1000) / 1000 * 0.26 - 0.13


# ---------------------------------------------------------------- figures
def fig1_timeline(rows, out, centre_z, ordered, span, edges):
    fig, ax = plt.subplots(figsize=(15, 6.4), layout="constrained")
    for iy, src in enumerate(SRC_ORDER):
        color, marker = SRC_STYLE[src]
        sub = [r for r in rows if r["source"] == src]
        n_cen = sum(abs(r["z"]) <= centre_z for r in sub)
        for r in sub:
            ax.plot(r["date"], iy + deterministic_jitter(r["run"]), marker,
                    ms=9 if marker != "*" else 17,
                    mfc=color if abs(r["z"]) <= centre_z else "none",
                    mec=color, mew=1.5, alpha=0.8, ls="none")
        ax.text(1.005, iy, f"{len(sub)} runs / {n_cen} centre",
                transform=ax.get_yaxis_transform(), va="center",
                fontsize=11, color="0.3")
    ax.set_yticks(range(len(SRC_ORDER)),
                  [SRC_LABEL[s] + " MeV" for s in SRC_ORDER])
    ax.set_ylim(-0.7, len(SRC_ORDER) - 0.3)
    ax.set_xlim(span[ordered[0]][0] - timedelta(days=6),
                span[ordered[-1]][1] + timedelta(days=48))
    shade_phases(ax, ordered, edges)
    fmt_axis(ax)
    ax.set_ylabel("calibration source\n(ordered by nominal $E$)")
    ax.set_title(f"JUNO ACU calibration data-taking — {len(rows)} runs, "
                 f"{rows[0]['date']:%b %Y} – {rows[-1]['date']:%b %Y}")
    handles = [Line2D([], [], color=SRC_STYLE[s][0], marker=SRC_STYLE[s][1],
                      ls="none", mfc=SRC_STYLE[s][0], mec=SRC_STYLE[s][0],
                      label=s, ms=10) for s in SRC_ORDER]
    handles += [Line2D([], [], color="0.4", marker="o", ls="none", mfc="0.4",
                       label=f"centre run ($|z|\\leq${centre_z} m)", ms=10),
                Line2D([], [], color="0.4", marker="o", ls="none", mfc="none",
                       mec="0.4", label="$z$-scan point", ms=10)]
    fig.legend(handles=handles, loc="outside lower center", ncols=4, frameon=False)
    for ext in ("png", "pdf"):
        fig.savefig(out / f"fig1_run_timeline.{ext}")
    plt.close(fig)


def fig2_zscan(rows, out, ordered, span, edges):
    fig, ax = plt.subplots(figsize=(15, 6.2), layout="constrained")
    for src in SRC_ORDER:
        color, marker = SRC_STYLE[src]
        sub = [r for r in rows if r["source"] == src]
        ax.plot([r["date"] for r in sub], [r["z"] for r in sub], marker,
                ms=8, mfc=color, mec=color, alpha=0.75, ls="none",
                label=f"{src} ({len(sub)})")
    for z in (17.7, -17.7):
        ax.axhline(z, color="0.2", ls="--", lw=1.2)
    ax.text(0.01, 17.95, "acrylic sphere  $R$ = 17.7 m", fontsize=12,
            color="0.25", transform=ax.get_yaxis_transform())
    ax.text(0.01, -18.35, "acrylic sphere  $R$ = 17.7 m", fontsize=12,
            color="0.25", transform=ax.get_yaxis_transform())
    ax.axhline(0, color="0.85", lw=0.8)
    shade_phases(ax, ordered, edges)
    ax.set_ylim(-19.4, 20.2)
    fmt_axis(ax)
    ax.set_ylabel("source $z$ position [m]")
    ax.set_title("ACU source $z$-scan coverage along the detector axis "
                 "(all runs at $x=y=0$)")
    fig.legend(loc="outside lower center", ncols=6, frameon=False)
    for ext in ("png", "pdf"):
        fig.savefig(out / f"fig2_zscan_coverage.{ext}")
    plt.close(fig)


def fig3_cadence(rows, out, ordered, span, edges):
    from collections import Counter
    daily = {}
    for r in rows:
        daily.setdefault(r["date"], Counter())[r["source"]] += 1
    dates = sorted(daily)
    fig, ax = plt.subplots(figsize=(15, 5.6), layout="constrained")
    bottom = [0] * len(dates)
    for src in SRC_ORDER:
        color, _ = SRC_STYLE[src]
        vals = [daily[d][src] for d in dates]
        ax.bar(dates, vals, bottom=bottom, width=1.6, color=color, alpha=0.9,
               label=src, edgecolor="white", linewidth=0.4)
        bottom = [b + v for b, v in zip(bottom, vals)]
    tot = list(bottom)
    ax2 = ax.twinx()
    ax2.plot(dates, tot, color="0.25", lw=1.8, marker=".", ms=5,
             label="cumulative")
    ax2.set_ylabel("cumulative runs", color="0.25")
    ax2.tick_params(axis="y", labelcolor="0.25")
    ax2.set_ylim(0, max(tot) * 1.08)
    ax2.spines["top"].set_visible(False)
    shade_phases(ax, ordered, edges)
    fmt_axis(ax)
    ax.set_ylabel("runs per day")
    ax.set_ylim(0, max(tot) * 1.05)
    ax.set_title("Data-taking cadence: calibration runs per day, "
                 "stacked by source")
    fig.legend(loc="outside lower center", ncols=7, frameon=False)
    for ext in ("png", "pdf"):
        fig.savefig(out / f"fig3_daily_cadence.{ext}")
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--csv", default=str(CSV), help="CalibRUN_from_file.csv")
    ap.add_argument("--phase-csv", default=str(PHASE_CSV),
                    help="ValProd26BPhase.csv (phase run ranges)")
    ap.add_argument("--out-dir", default=str(REPO / "output" / "calib_inventory"))
    ap.add_argument("--figs", default="all", help="'all' or subset like '1,3'")
    ap.add_argument("--centre-z", type=float, default=0.5,
                    help="centre-run definition: |z| <= this [m] (default 0.5)")
    args = ap.parse_args()

    rows = load_runs(args.csv)
    phases = load_phases(args.phase_csv)
    ordered, span, edges = phase_spans(rows, phases)
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    which = set(range(1, 4)) if args.figs == "all" else {
        int(v) for v in args.figs.split(",")}
    if 1 in which:
        fig1_timeline(rows, out, args.centre_z, ordered, span, edges)
    if 2 in which:
        fig2_zscan(rows, out, ordered, span, edges)
    if 3 in which:
        fig3_cadence(rows, out, ordered, span, edges)
    print(f"[calib-inventory] {len(rows)} runs, phases "
          f"{','.join('P%d' % p for p in ordered)} -> {out}")


if __name__ == "__main__":
    main()
