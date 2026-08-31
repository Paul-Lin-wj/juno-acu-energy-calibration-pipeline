#!/usr/bin/env python3
"""
compare_phases_vs_production.py — 四 phase 复刻结果 vs 生产 gamma 表汇总对比图。

只读工具：从四棵 phase 留档树的 gamma_Phase{N}.dat + .provenance.json 与
dybmodel_data 里的生产表（跳过 P1 的 K40 行）取数，画两张 panel：

  上  E_rec/E_true vs E_true——生产值（×）与各 phase 复刻值（●）逐峰对照
  下  相对偏差 (ours − production)/production [%]，各 phase 一色

用法：
  python tools/compare_phases_vs_production.py \
      --phase 1:output/<ts1>/phase1 --phase 2:output/<ts2>/phase2 ... \
      [--out output/<ts>/phase_comparison]

不指定 --out 时写到第一棵 phase 树的上级目录（output/<ts>/）。
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

PEAKS = ["Cs137", "Mn54", "Ge68", "nH", "Co60", "nC", "O16"]
# dataviz 固定槽序散点四色（--pairs all 校验通过：blue/magenta/aqua/violet；
# CVD floor band 6.1 由峰名直接标注 + 终端数值表作副编码兜底）
PHASE_COLORS = {1: "#2a78d6", 2: "#e87ba4", 3: "#1baf7a", 4: "#4a3aa7"}
# 生产表位置（P1 表 8 行含 K40 在 index 3，跳过）
PROD_DIR = Path(__file__).resolve().parent.parent / "dybmodel_data" / \
    "necessaryfiles" / "input" / "JUNO" / "ReProd26B"


def load_phase(tree: Path, ph: int):
    res = tree / "nlfit" / "results"
    ours = np.loadtxt(res / f"gamma_Phase{ph}.dat")[:, 0]
    prov = json.loads((res / f"gamma_Phase{ph}.dat.provenance.json").read_text())
    prod_file = PROD_DIR / (f"gamma_Phase{ph}_K40.dat" if ph == 1
                            else f"gamma_Phase{ph}.dat")
    prod = np.loadtxt(prod_file)[:, 0]
    if len(prod) == 8:                      # P1: 跳 K40 行（index 3）
        prod = prod[[0, 1, 2, 4, 5, 6, 7]]
    e_true = np.array([p["e_true"] for p in prov["peaks"]])
    return e_true, ours, prod, prov


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", action="append", required=True,
                    metavar="N:PATH", help="e.g. 1:output/<ts>/phase1")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    phases = []
    for spec in args.phase:
        n, path = spec.split(":", 1)
        phases.append((int(n), Path(path)))
    out_dir = Path(args.out) if args.out else phases[0][1].parent
    out_dir.mkdir(parents=True, exist_ok=True)

    data = {}
    for n, path in phases:
        data[n] = load_phase(path, n)

    fig, (ax, ax2) = plt.subplots(
        2, 1, figsize=(9.5, 7.5), sharex=True,
        gridspec_kw={"height_ratios": [2.2, 1], "hspace": 0.09})

    # ---- 上 panel：NL 点位（生产 × vs 复刻 ●） ----
    for n, _ in phases:
        e, ours, prod, _prov = data[n]
        ax.plot(e, prod / e, "x", color=PHASE_COLORS[n], ms=9, mew=1.8,
                alpha=0.9, zorder=2)
        ax.plot(e, ours / e, "o", color=PHASE_COLORS[n], ms=6.5,
                mec="white", mew=0.7, zorder=4, label=f"Phase {n}")
    # 峰名表头行（panel 上方；散点副编码：CVD floor band 的兜底之一）
    e0, _, _, _ = data[phases[0][0]]
    for x, pk in zip(e0, PEAKS):
        ax.annotate(pk, (x, 0), xytext=(x, 1.015),
                    textcoords=("data", "axes fraction"), fontsize=8.5,
                    color="#52514e", ha="center", va="bottom")
    ax.axhline(1.0, color="k", lw=0.8, alpha=0.4)
    ax.set_ylabel(r"$E_{\mathrm{rec}}/E_{\mathrm{true}}$", fontsize=13)
    ax.set_title("Phase-by-phase replication vs production gamma tables "
                 "(from-EDM full chain)", fontsize=12.5, fontweight="bold")
    ax.grid(True, alpha=0.3, ls=":")
    # marker 语义说明（× 生产 / ● 本链路 from-EDM；灰点仅示意 marker 形状，
    # 实际颜色=phase——"Phase N"图例条目已给颜色）
    handles, labels = ax.get_legend_handles_labels()
    prod_h = plt.Line2D([], [], color="#52514e", marker="x", ls="", ms=9,
                        mew=1.8, label="production table (×, same color)")
    ours_h = plt.Line2D([], [], color="#52514e", marker="o", ls="", ms=6.5,
                        label="this pipeline from-EDM (●, color=phase)")
    ax.legend(handles + [prod_h, ours_h], labels + [prod_h.get_label(),
               ours_h.get_label()], fontsize=9.5, ncol=2, loc="lower right")

    # ---- 下 panel：逐峰相对偏差 ----
    ax2.axhline(0, color="k", lw=0.8, alpha=0.5)
    for n, _ in phases:
        e, ours, prod, _prov = data[n]
        dev = (ours / prod - 1) * 100
        ax2.plot(e, dev, "o", color=PHASE_COLORS[n], ms=6,
                 mec="white", mew=0.6, label=f"Phase {n}")
    ax2.axhspan(-0.1, 0.1, color="#52514e", alpha=0.10, zorder=0)
    ax2.text(6.42, 0.11, "±0.1% band", fontsize=8.5, color="#52514e",
             ha="right", va="bottom")
    ax2.set_ylabel("deviation vs production [%]", fontsize=11)
    ax2.set_xlabel(r"$E_{\mathrm{true}}$ [MeV]", fontsize=13)
    ax2.set_xticks(e0)
    ax2.set_xticklabels([f"{x:g}" for x in e0], fontsize=9)
    ax2.grid(True, alpha=0.3, ls=":", axis="y")
    ax2.set_ylim(-1.6, 0.8)
    ax2.legend(fontsize=9.5, ncol=4, loc="lower right", framealpha=0.9)

    # nC 钉值口径注记（生产钉 5.08140，本链路默认不钉）
    ax2.annotate("nC: production pinned 5.08140,\nthis pipeline unpinned "
                 "(convention, not a bug)", xy=(4.95, -1.18), xytext=(2.0, -1.5),
                 fontsize=8.5, color="#52514e",
                 arrowprops=dict(arrowstyle="-", color="#52514e", lw=0.7))

    for ext in ("png", "pdf"):
        p = out_dir / f"phase_comparison_vs_production.{ext}"
        fig.savefig(p, dpi=200, bbox_inches="tight")
        print(f"[compare] saved {p}")
    plt.close(fig)

    # 终端表格（表视图义务：contrast WARN 的槽位靠可见标签+数值表兜底）
    print(f"\n{'peak':6s}" + "".join(f"{'P'+str(n):>12s}" for n, _ in phases)
          + "   (deviation %)")
    for i, pk in enumerate(PEAKS):
        row = f"{pk:6s}"
        for n, _ in phases:
            e, ours, prod, _prov = data[n]
            row += f"{(ours[i]/prod[i]-1)*100:>11.3f}%"
        print(row)


if __name__ == "__main__":
    main()
