#!/usr/bin/env python3
"""
paper_style_nl_figures.py — 复刻 JUNO 首篇文章 Extended Data Fig. 2 的 a/d 两 panel。

只读工具：输入 = 某棵 phase 留档树的 nlfit/results/（nl_curves.tsv + gamma 表
provenance），输出两张图：

  fig_a_scintillator_nl — 闪烁体非线性 vs 等效单 γ 能量
      横坐标 = "effective single γ energy"（论文图 a 口径）：
        单 γ 源（Cs137/Mn54/nH/nC/O16）→ 线能量本身
        多 γ 源（Ge68=0.511×2, Co60=1.250×2）→ 沿 gammaScintNL 曲线反解的等效点
      （复刻 dybGammaPeak::GetEffectiveEnergy / GetDataScintNL 的定义：
        dataScintNL = eVis/E_total，eVis 由 eRec 去电子学NL 反解）
  fig_d_full_nl — e⁻/e⁺/γ 三条 full NL 曲线 vs E_true（论文图 d 口径）

用法（在仓库根目录）：
  nlfit/.venv/bin/python nlfit/tools/paper_style_nl_figures.py \
      --tree output/<ts>/phase1 [--out <dir>]

注：论文图的 68% C.L. 误差带需要用协方差矩阵扰动参数重算 C++ 模型曲线，
本工具不重算（曲线无误差带，只有中心值）。
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import CubicSpline

# 论文 marker 约定：单 γ 源实心圆、多 γ 源空心菱形
SINGLE_GAMMA = {"Cs137", "Mn54", "nH", "nC", "O16"}
MULTI_GAMMA = {"Ge68", "Co60"}
# (key, E_true_total, E_true_single)——dybGammaData.cxx LoadData 同表
PEAK_ENERGY = {
    "Cs137": (0.6617, 0.6617), "Mn54": (0.8348, 0.8348),
    "Ge68": (1.022, 0.511), "nH": (2.2233, 2.2233),
    "Co60": (2.506, 1.250), "nC": (4.95, 4.95), "O16": (6.129, 6.129),
}
C_CURVE = "#d62728"      # gamma 曲线（沿用 stage6 风格）
C_SINGLE = "#1f77b4"
C_MULTI = "#e87ba4"
INK = "#52514e"


def load_curves(tsv: Path) -> dict:
    curves, name = {}, None
    for ln in tsv.read_text().splitlines():
        if ln.startswith("#"):
            parts = ln.split()
            if len(parts) >= 3 and parts[1] == "curve":
                name = parts[2]
                curves[name] = ([], [])
            continue
        if name and ln.strip():
            x, y = ln.split()
            curves[name][0].append(float(x))
            curves[name][1].append(float(y))
    return {k: (np.array(a), np.array(b)) for k, (a, b) in curves.items()}


def data_points(prov: dict, curves: dict):
    """每峰算 (eEff, dataScintNL, err)——复刻 dybGammaPeak 的定义。"""
    elx, ely = curves["electronicsNL"]
    gx, gy = curves["gammaScintNL"]
    spl = CubicSpline(gx, gy)
    grid = np.linspace(gx.min(), gx.max(), 200001)
    grid_y = spl(grid)
    out = []
    for p in prov["peaks"]:
        key = p["key"]
        if not p.get("mu"):
            continue
        e_tot, e_single = PEAK_ENERGY[key]
        e_rec = p["mu"]
        e_vis = e_rec
        for _ in range(60):  # eRec = eVis·ElectronicsNL(eVis) 反解
            e_vis = e_rec / np.interp(e_vis, elx, ely)
        scint_nl = e_vis / e_tot
        if key in SINGLE_GAMMA:
            e_eff = e_single
        else:               # 沿 gammaScintNL 反解等效单 γ 能
            m = grid_y >= scint_nl
            e_eff = float(grid[m][0]) if m.any() else float("nan")
        out.append(dict(key=key, e_eff=e_eff, scint_nl=scint_nl,
                        err=p["err_rel"] * scint_nl))
    return out


def fig_a(points, curves, out_dir: Path, tag: str):
    gx, gy = curves["gammaScintNL"]
    # γ 系曲线 C++ 侧仅 18 点（0.2-1.0 步长 0.1，以上步长 1）；样条加密仅作显示
    spl = CubicSpline(gx, gy)
    xs = np.linspace(gx.min(), gx.max(), 981)
    fig, (ax, axr) = plt.subplots(
        2, 1, figsize=(8, 6.2), sharex=True,
        gridspec_kw={"height_ratios": [3, 1], "hspace": 0.08})
    ax.plot(xs, spl(xs), color=C_CURVE, lw=2.0, label="best fit", zorder=2)
    for p in points:
        multi = p["key"] in MULTI_GAMMA
        ax.errorbar(p["e_eff"], p["scint_nl"], yerr=p["err"],
                    fmt="D" if multi else "o",
                    mfc="none" if multi else "k",
                    mec="k", ecolor="k",
                    ms=8, mew=1.6, capsize=3, lw=1.4, zorder=4)
        ax.annotate(p["key"], (p["e_eff"], p["scint_nl"]),
                    textcoords="offset points", xytext=(7, 5), fontsize=9)
    ax.axhline(1.0, color="k", lw=0.8, alpha=0.4)
    ax.set_ylabel("scintillator non-linearity", fontsize=12)
    ax.set_title(f"Scintillator NL vs effective single-γ energy — {tag}",
                 fontsize=12, fontweight="bold")
    ax.grid(True, alpha=0.3, ls=":")
    h1 = plt.Line2D([], [], color="k", marker="o", mfc="k", ls="",
                    ms=7, label="single-γ source")
    h2 = plt.Line2D([], [], color="k", marker="D", mfc="none", ls="",
                    ms=7, mew=1.6, label="multiple-γ source")
    h3 = plt.Line2D([], [], color=C_CURVE, lw=2, label="best fit")
    ax.legend(handles=[h3, h1, h2], fontsize=9.5, loc="lower right")

    axr.axhline(0, color="k", lw=0.8, alpha=0.5)
    for p in points:
        resid = p["scint_nl"] / spl(p["e_eff"]) - 1
        multi = p["key"] in MULTI_GAMMA
        axr.errorbar(p["e_eff"], resid, yerr=p["err"] / spl(p["e_eff"]),
                     fmt="D" if multi else "o",
                     mfc="none" if multi else "k",
                     mec="k", ecolor="k",
                     ms=6, mew=1.4, capsize=2.5, lw=1.2)
    axr.set_xlabel("effective single-γ energy [MeV]", fontsize=12)
    axr.set_ylabel("residual", fontsize=10)
    axr.grid(True, alpha=0.3, ls=":", axis="y")
    for ext in ("png", "pdf"):
        fig.savefig(out_dir / f"fig_a_scintillator_nl.{ext}", dpi=200,
                    bbox_inches="tight")
    plt.close(fig)


def fig_d(curves, out_dir: Path, tag: str, band_tsv=None):
    fig, ax = plt.subplots(figsize=(8, 5.6))
    # 68% C.L. band (optional): nominal TGraphAsymmErrors dumped from the
    # errors root as TSV. DrawErrors samples positronFullNL only, so the
    # band belongs on the e+ curve (x from 1.022 MeV up).
    if band_tsv is not None and Path(band_tsv).is_file():
        b = np.loadtxt(band_tsv)
        ax.fill_between(b[:, 0], b[:, 1] - b[:, 2], b[:, 1] + b[:, 3],
                        color="#ff7f0e", alpha=0.18, lw=0, zorder=1,
                        label="e\u207a 68% C.L.")
    for name, color, ls, lbl in [
            ("electronFullNL", "#1f77b4", "-", "e⁻"),
            ("gammaFullNL", "#d62728", "-", "γ"),
            ("positronFullNL", "#ff7f0e", "-", "e⁺")]:
        x, y = curves[name]
        if name == "gammaFullNL":
            # γ 曲线 C++ 侧仅 18 个采样点（0.2-1.0 步长 0.1，以上步长 1），
            # 折线感来自采样网格而非模型；样条加密到 0.01 MeV 仅作显示
            xs = np.linspace(x.min(), x.max(), 981)
            ys = CubicSpline(x, y)(xs)
            ax.plot(xs, ys, color=color, ls=ls, lw=2.0, label=lbl)
        else:
            ax.plot(x, y, color=color, ls=ls, lw=2.0, label=lbl)
    ax.axhline(1.0, color="k", lw=0.8, alpha=0.4)
    ax.set_ylim(0.8, None)
    ax.set_xlim(0, 12)
    ax.set_xlabel("true energy [MeV]", fontsize=12)
    ax.set_ylabel("full non-linearity", fontsize=12)
    ax.set_title(f"Full NL model (e⁻/γ/e⁺) — {tag}", fontsize=12,
                 fontweight="bold")
    ax.grid(True, alpha=0.3, ls=":")
    ax.legend(fontsize=11, loc="lower right")
    for ext in ("png", "pdf"):
        fig.savefig(out_dir / f"fig_d_full_nl.{ext}", dpi=200,
                    bbox_inches="tight")
    plt.close(fig)


def _band_tsv(res: Path):
    """results/cl_band_nominal.tsv 存在即自动带上（clband 作业约定产物）。"""
    c = res / "cl_band_nominal.tsv"
    return c if c.is_file() else None


def render(res: Path, out_dir: Path, tag: str) -> list[str]:
    """出 fig_a + fig_d。pipeline Stage 8 与 CLI main() 共用这一入口。

    res = nlfit/results 目录（nl_curves.tsv + gamma_*.dat.provenance.json）。
    返回写出的文件路径列表。"""
    out_dir.mkdir(parents=True, exist_ok=True)
    curves = load_curves(res / "nl_curves.tsv")
    ph = json.loads((list(res.glob("gamma_Phase*.dat.provenance.json")
                          or res.glob("gamma_AllPhase.dat.provenance.json"))[0])
                    .read_text())
    points = data_points(ph, curves)
    fig_a(points, curves, out_dir, tag)
    fig_d(curves, out_dir, tag, band_tsv=_band_tsv(res))
    print(f"[paper-style] saved fig_a / fig_d to {out_dir}")
    for p in points:
        print(f"  {p['key']:6s} eEff={p['e_eff']:.4f}  scintNL={p['scint_nl']:.4f}")
    return [str(out_dir / f"fig_a_scintillator_nl.{ext}") for ext in ("png", "pdf")] \
        + [str(out_dir / f"fig_d_full_nl.{ext}") for ext in ("png", "pdf")]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tree", required=True, help="phase 留档树（含 nlfit/results）")
    ap.add_argument("--out", default=None)
    ap.add_argument("--tag", default=None)
    ap.add_argument("--band", default=None,
                    help="CL band TSV (errors-root nominal dump)")
    args = ap.parse_args()
    tree = Path(args.tree)
    res = tree / "nlfit" / "results"
    out_dir = Path(args.out) if args.out else res.parent / "figures"
    tag = args.tag or tree.resolve().name
    render(res, out_dir, tag)


if __name__ == "__main__":
    main()
