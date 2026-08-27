#!/usr/bin/env python3
"""
Intermediate QC plots for the nlfit stages (one figure per stage, same
conventions as the sibling fitter figures: PNG + PDF, 200 dpi).

  stage5_gamma_peaks  — the 7 gamma peaks: nonlinearity E_rec/E_true vs
                        E_true (fitter-provided vs pinned vs historical)
                        + deviation panel
  stage6_nl_curves    — dybmodel fitted NL curves with the data points
                        overlaid + data/model ratio panel
  stage7_inversion    — E_true = f(E_rec) lookup curves + round-trip error
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

COLORS = {"fitter": "#1f77b4", "pinned": "#d62728", "hist": "#7f7f7f"}
CURVE_STYLE = {
    "electronicsNL": dict(color="#7f7f7f", ls="--", lw=1.4),
    "gammaScintNL": dict(color="#2ca02c", ls=":", lw=1.6),
    "gammaFullNL": dict(color="#d62728", ls="-", lw=2.0),
    "electronScintNL": dict(color="#9467bd", ls=":", lw=1.4),
    "electronFullNL": dict(color="#1f77b4", ls="-", lw=2.0),
    "positronFullNL": dict(color="#ff7f0e", ls="-.", lw=1.8),
}
CURVE_LABEL = {
    "electronicsNL": "electronics",
    "gammaScintNL": "γ scint.",
    "gammaFullNL": "γ full (e⁻ from γ shower)",
    "electronScintNL": "e⁻ scint.",
    "electronFullNL": "e⁻ full",
    "positronFullNL": "e⁺ full",
}


def _save(fig, out_dir: Path, stem: str):
    out_dir.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "pdf"):
        p = out_dir / f"{stem}.{ext}"
        fig.savefig(p, dpi=200, bbox_inches="tight")
        print(f"[plots] saved {p}")
    plt.close(fig)


# ---------------------------------------------------------------- stage 5
def plot_stage5(peaks: list[dict], fig_dir):
    peaks = [p for p in peaks if p.get("mu")]
    e_true = np.array([p["e_true"] for p in peaks])
    nl = np.array([p["mu"] for p in peaks]) / e_true
    nl_err = np.array([p["err_rel"] for p in peaks]) * nl
    hist_nl = np.array([p["mu_historical"] for p in peaks]) / e_true
    dev = np.array([p["dev_vs_historical"] for p in peaks]) * 100

    fig, (ax, ax2) = plt.subplots(
        2, 1, figsize=(8, 6.5), sharex=True,
        gridspec_kw={"height_ratios": [3, 1], "hspace": 0.08})
    ax.axhline(1.0, color="k", lw=0.8, alpha=0.5)
    ax.errorbar(e_true, hist_nl, fmt="x", color=COLORS["hist"], ms=8,
                mew=1.8, label="historical (ReProd26B analysis)", zorder=2)
    fit_m = np.array([not p["pinned"] for p in peaks])
    pin_m = ~fit_m
    if fit_m.any():
        ax.errorbar(e_true[fit_m], nl[fit_m], yerr=nl_err[fit_m], fmt="o",
                    color=COLORS["fitter"], ms=8, capsize=4, lw=1.6,
                    label="this pipeline (fitter μ)", zorder=4)
    if pin_m.any():
        ax.errorbar(e_true[pin_m], nl[pin_m], yerr=nl_err[pin_m], fmt="s",
                    mfc="none", color=COLORS["pinned"], ms=9, capsize=4,
                    lw=1.6, label="pinned (external input)", zorder=3)
    for p, x, y in zip(peaks, e_true, nl):
        ax.annotate(p["key"], (x, y), textcoords="offset points",
                    xytext=(8, 6), fontsize=10)
    ax.set_ylabel(r"$E_{\mathrm{rec}}/E_{\mathrm{true}}$", fontsize=13)
    ax.set_title("Stage 5 — gamma peak inputs for the NL fit "
                 "(dybmodel 7-peak convention)", fontsize=12,
                 fontweight="bold")
    ax.grid(True, alpha=0.3, ls=":")
    ax.legend(fontsize=10, loc="lower left")

    ax2.axhline(0, color="k", lw=0.8, alpha=0.5)
    ax2.bar(e_true, dev, width=0.12, color=COLORS["fitter"], alpha=0.7)
    ax2.set_ylabel("μ − hist. [%]", fontsize=11)
    ax2.set_xlabel(r"$E_{\mathrm{true}}$ [MeV]", fontsize=13)
    ax2.grid(True, alpha=0.3, ls=":", axis="y")
    _save(fig, Path(fig_dir), "stage5_gamma_peaks")


# ---------------------------------------------------------------- stage 6
def plot_stage6(curves: dict, peaks: list[dict], fig_dir):
    fig, (ax, ax2) = plt.subplots(
        2, 1, figsize=(8.5, 7), sharex=True,
        gridspec_kw={"height_ratios": [3, 1], "hspace": 0.08})
    ax.axhline(1.0, color="k", lw=0.8, alpha=0.5)
    for name, style in CURVE_STYLE.items():
        if name not in curves:
            continue
        x, y = curves[name]
        ax.plot(x, y, label=CURVE_LABEL.get(name, name), zorder=2, **style)

    peaks = [p for p in peaks if p.get("mu")]
    e_true = np.array([p["e_true"] for p in peaks])
    nl = np.array([p["mu"] for p in peaks]) / e_true
    nl_err = np.array([p["err_rel"] for p in peaks]) * nl
    ax.errorbar(e_true, nl, yerr=nl_err, fmt="k o", ms=7, capsize=4,
                lw=1.5, label="gamma data points", zorder=5)
    for p, x, y in zip(peaks, e_true, nl):
        ax.annotate(p["key"], (x, y), textcoords="offset points",
                    xytext=(8, 6), fontsize=9)

    if "gammaFullNL" in curves:
        cx, cy = curves["gammaFullNL"]
        model = np.interp(e_true, cx, cy)
        ratio = nl / model
        ratio_err = nl_err / model
        ax2.axhline(1.0, color="k", lw=0.8, alpha=0.5)
        ax2.errorbar(e_true, ratio, yerr=ratio_err, fmt="k o", ms=6,
                     capsize=3, lw=1.2)
        ax2.set_ylabel("data / γ-full model", fontsize=11)

    ax.set_ylabel(r"$E_{\mathrm{rec}}/E_{\mathrm{true}}$", fontsize=13)
    ax.set_title("Stage 6 — dybmodel global NL fit", fontsize=12,
                 fontweight="bold")
    ax.set_xlim(0, 12)
    ax.grid(True, alpha=0.3, ls=":")
    ax.legend(fontsize=9.5, loc="lower right", ncol=2)
    ax2.set_xlabel(r"$E_{\mathrm{true}}$ [MeV]", fontsize=13)
    ax2.grid(True, alpha=0.3, ls=":")
    _save(fig, Path(fig_dir), "stage6_nl_curves")


# ---------------------------------------------------------------- stage 7
def plot_stage7(curves: dict, lookup: dict, fig_dir):
    fig, (ax, ax2) = plt.subplots(
        2, 1, figsize=(8, 6.5), sharex=True,
        gridspec_kw={"height_ratios": [2.2, 1], "hspace": 0.08})
    e_rec = lookup["e_rec_grid"]
    ax.plot(e_rec, e_rec, "k--", lw=1.0, alpha=0.5, label="diagonal")
    for name, style in CURVE_STYLE.items():
        key = f"{name}_e_true"
        if key not in lookup:
            continue
        ax.plot(e_rec, lookup[key], label=CURVE_LABEL.get(name, name),
                zorder=3, **{k: v for k, v in style.items() if k != "ls"})
    ax.set_ylabel(r"$E_{\mathrm{true}}$ [MeV]", fontsize=13)
    ax.set_title("Stage 7 — $E_{\\mathrm{true}} = f(E_{\\mathrm{rec}})$ "
                 "lookup (inverted NL curves)", fontsize=12,
                 fontweight="bold")
    ax.grid(True, alpha=0.3, ls=":")
    ax.legend(fontsize=10, loc="upper left")

    ax2.axhline(0, color="k", lw=0.8, alpha=0.5)
    for name in ("gammaFullNL", "electronFullNL", "positronFullNL"):
        key = f"{name}_e_true"
        if key not in lookup or name not in curves:
            continue
        cx, cy = curves[name]          # round-trip on the curve's own grid
        e_rec_curve = cx * cy
        back = np.interp(e_rec_curve, e_rec, lookup[key],
                         left=np.nan, right=np.nan)
        rel = np.abs(back - cx) / cx
        ax2.plot(e_rec_curve, rel, lw=1.4,
                 color=CURVE_STYLE[name]["color"],
                 label=CURVE_LABEL.get(name, name))
    ax2.set_yscale("log")
    ax2.set_ylabel("round-trip |Δ|/E", fontsize=11)
    ax2.set_xlabel(r"$E_{\mathrm{rec}}$ [MeV]", fontsize=13)
    ax2.grid(True, alpha=0.3, ls=":")
    ax2.legend(fontsize=9.5, loc="upper right")
    _save(fig, Path(fig_dir), "stage7_inversion")
