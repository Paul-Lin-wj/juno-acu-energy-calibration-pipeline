#!/usr/bin/env python3
"""
make_audit_report.py — 人类可快速审计的正确性报告生成器
=======================================================

对流水线各阶段产物与"原链路参考数据"做逐字段数值比对，并产出：
  1. 叠加直方图（本流水线输出 vs 参考，双曲线应完全重合）
  2. 残差面板（差值应恒为 0）
  3. EDM 逐分支最大相对差异条形图（log 轴，逐位一致的分支为 0）
  4. report.md 汇总表（bitwise / maxdiff / 事件数 / LivingTime）

审计者只需看三件事：
  - 所有叠加曲线是否完全重合、残差是否恒为 0
  - EDM 分支差异图中，除 totalPE（已知 5月/6月版 JUNOSW 微差）外是否为 0
  - 汇总表中 bitwise_equal 是否全部为 True

用法：
    python tools/make_audit_report.py [--ref-dir data/_audit_ref] [--out audit_report]
"""

from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REF_DEFAULT = os.path.join(PROJECT, "data", "_audit_ref")

# 本地产物 -> 参考文件 的配对（bitwise 比对 + 画图）
NPZ_PAIRS = [
    ("Stage1 raw npz", "data/npz_raw/RUN12370.npz", "REF_raw_RUN12370.npz"),
    ("Stage2 corrected npz", "data/npz_corrected/RUN12370.npz", "REF_corr_RUN12370.npz"),
    ("Stage3 selection npz (fitter input)",
     "data/selection/npz/Run12370_SelectionResult.npz", "REF_sel_RUN12370.npz"),
]

# 画叠加谱用的字段（key, 标签, bin 数, x 轴范围或 None=自动）
SPECTRUM_KEYS = [
    ("omilrec_energy", "omilrec_energy (MeV)", 200, None),
    ("calib_omilrec_energy", "calib_omilrec_energy (MeV)", 200, None),
]


def load(path):
    return np.load(path, allow_pickle=True)


def compare_npz(mine_path, ref_path):
    """逐字段比对，返回 {key: dict(shape, dtype, bitwise, maxdiff, note)}。"""
    a, b = load(mine_path), load(ref_path)
    out = {}
    for k in sorted(set(a.keys()) | set(b.keys())):
        if k not in a.files or k not in b.files:
            out[k] = dict(note="KEY MISSING", bitwise=False, maxdiff=None)
            continue
        va, vb = a[k], b[k]
        rec = dict(shape=str(va.shape), dtype=str(va.dtype))
        if va.shape != vb.shape:
            rec.update(note=f"SHAPE MISMATCH {vb.shape}", bitwise=False, maxdiff=None)
        elif va.dtype.kind in "fiub":
            ident = bool(np.array_equal(va, vb))
            md = float(np.max(np.abs(va.astype(np.float64) - vb.astype(np.float64)))) if va.size else 0.0
            rec.update(bitwise=ident, maxdiff=md, note="")
        else:
            eq = (va == vb)
            eq_all = bool(np.all(eq)) if hasattr(eq, "shape") else bool(eq)
            rec.update(bitwise=eq_all, maxdiff=0.0 if eq_all else None, note="object/str")
        out[k] = rec
    return out


def overlay_hist(ax, va, vb, label, bins, rng, tag_a="this pipeline", tag_b="reference"):
    """叠加 step 直方图 + 底部残差面板由调用方布局。"""
    lo = min(va.min(), vb.min())
    hi = max(va.max(), vb.max())
    if rng is not None:
        lo, hi = rng
    edges = np.linspace(lo, hi, bins + 1)
    ha, _ = np.histogram(np.clip(va, lo, hi), bins=edges)
    hb, _ = np.histogram(np.clip(vb, lo, hi), bins=edges)
    centers = (edges[:-1] + edges[1:]) / 2
    ax[0].step(centers, ha, where="mid", color="crimson", lw=2.2,
               label=f"{tag_a} (n={va.size:,})", zorder=3)
    ax[0].step(centers, hb, where="mid", color="k", lw=1.0, ls="--",
               label=f"{tag_b} (n={vb.size:,})", zorder=2)
    ax[0].set_ylabel("events / bin")
    ax[0].set_title(label, fontsize=11)
    ax[0].legend(fontsize=8, loc="upper right")
    denom = np.where(hb > 0, hb, 1)
    rel = (ha - hb) / denom
    ax[1].step(centers, rel, where="mid", color="navy", lw=1.2)
    ax[1].axhline(0, color="k", lw=0.8)
    maxrel = float(np.max(np.abs(rel))) if rel.size else 0.0
    ax[1].set_ylabel("(this - ref)/ref")
    ax[1].set_xlabel(label.split("(")[-1].rstrip(")") if "(" in label else label)
    ax[1].set_title(f"relative residual   max|Δ| = {maxrel:.3e}", fontsize=9)
    return maxrel


def edm_branch_diff(ax, local_root, ref_root):
    """EDM 逐分支最大相对差异条形图（需 uproot）。"""
    import uproot
    BR = ["global_time_s", "global_time_ns", "MuonVeto", "omilrec_x",
          "omilrec_y", "omilrec_z", "omilrec_energy", "totalPE"]
    loc = uproot.open(local_root)["CDCalib"].arrays(BR, library="np")
    ref = uproot.open(ref_root)["CDCalib"].arrays(BR, library="np")
    n = min(len(loc["global_time_s"]), len(ref["global_time_s"]))
    names, maxrel = [], []
    for b in BR:
        a, c = loc[b][:n].astype(np.float64), ref[b][:n].astype(np.float64)
        denom = np.maximum(np.abs(c), 1e-9)
        names.append(b)
        maxrel.append(float(np.max(np.abs(a - c) / denom)) if b != "MuonVeto"
                      else float(np.max(np.abs(a - c))))
    y = np.arange(len(names))
    colors = ["seagreen" if v == 0 else ("darkorange" if k == "totalPE" else "crimson")
              for k, v in zip(names, maxrel)]
    ax.barh(y, [max(v, 1e-18) for v in maxrel], color=colors)
    ax.set_yticks(y, names, fontsize=8)
    ax.set_xscale("log")
    ax.set_xlabel("max per-event |relative difference|  (log)")
    ax.set_title("Stage 0 rebuilt EDM vs reference EDM (first "
                 f"{n:,} events)\ngreen = bitwise identical; orange = totalPE "
                 "(known May/June JUNOSW build diff, not used downstream)", fontsize=9)
    for yi, v in zip(y, maxrel):
        txt = "0 (bitwise)" if v == 0 else f"{v:.1e}"
        ax.text(max(v, 1e-18) * 1.5, yi, txt, va="center", fontsize=7)
    ax.set_xlim(1e-18, 1e0)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--ref-dir", default=REF_DEFAULT)
    ap.add_argument("--out", default=os.path.join(PROJECT, "audit_report"))
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    report = {"npz": {}, "plots": []}
    lines = ["# standalone_esd2npz 正确性审计报告（自动生成）\n",
             "| 产物 | 字段 | shape | dtype | bitwise_equal | maxdiff |",
             "|---|---|---|---|---|---|"]

    # ---- NPZ 比对 + 叠加谱 ----
    fig_specs = []  # (ax pair list, png name)
    for tag, mine_rel, ref_name in NPZ_PAIRS:
        mine = os.path.join(PROJECT, mine_rel)
        ref = os.path.join(args.ref_dir, ref_name)
        if not (os.path.exists(mine) and os.path.exists(ref)):
            lines.append(f"| {tag} | — | — | — | SKIP (missing file) | — |")
            continue
        res = compare_npz(mine, ref)
        all_bit = all(r.get("bitwise", False) for r in res.values())
        report["npz"][tag] = dict(fields=res, all_bitwise=all_bit)
        for k, r in res.items():
            lines.append(f"| {tag} | `{k}` | {r['shape']} | {r['dtype']} | "
                         f"**{r.get('bitwise')}** | {r.get('maxdiff')} {r.get('note','')} |")
        # 画能量谱叠加图（raw/corrected 用 omilrec_energy, selection 用 calib_omilrec_energy）
        key = "calib_omilrec_energy" if "selection" in tag else "omilrec_energy"
        if key in res and res[key].get("bitwise") is not None:
            fig, axp = plt.subplots(2, 1, figsize=(7, 5.4), sharex=True,
                                    gridspec_kw=dict(height_ratios=[3, 1]))
            va, vb = load(mine)[key].astype(np.float64), load(ref)[key].astype(np.float64)
            maxrel = overlay_hist(axp, va, vb, f"{tag} — {key}", 200, None)
            png = f"{tag.split()[0]}_{key}.png".replace(" ", "_")
            fig.tight_layout()
            fig.savefig(os.path.join(args.out, png), dpi=130)
            plt.close(fig)
            report["plots"].append(png)
            lines.append(f"| {tag} | spectrum overlay | — | — | max rel residual = {maxrel:.3e} | {png} |")

    # ---- EDM 逐分支差异图 ----
    local_edm = os.path.join(PROJECT, "data/edm/run_12370_0_0.root")
    ref_edm = os.path.join(args.ref_dir, "REF_run_12370_0_19.root")
    if os.path.exists(local_edm) and os.path.exists(ref_edm):
        fig, ax = plt.subplots(figsize=(8, 3.6))
        edm_branch_diff(ax, local_edm, ref_edm)
        fig.tight_layout()
        png = "Stage0_EDM_branch_diff.png"
        fig.savefig(os.path.join(args.out, png), dpi=130)
        plt.close(fig)
        report["plots"].append(png)
        lines.append(f"| Stage 0 EDM | per-branch | — | — | see plot | {png} |")

    # ---- 汇总 ----
    overall = all(v["all_bitwise"] for v in report["npz"].values()) if report["npz"] else False
    report["overall_all_bitwise"] = overall
    lines.append("")
    lines.append(f"**结论：{'全部 NPZ 产物与原链路参考逐位一致 (PASS)' if overall else '存在差异，见上表 (CHECK)'}**\n")
    lines.append("绿色分支 = 逐位一致；橙色 totalPE = 已知的 5月/6月版 JUNOSW 构建差异，"
                 "不进入 fitter 输入（SelectionResult.npz 仅含 calib_omilrec_*）。\n")

    with open(os.path.join(args.out, "report.md"), "w") as f:
        f.write("\n".join(lines))
    with open(os.path.join(args.out, "report.json"), "w") as f:
        json.dump(report, f, indent=1, default=str)
    print(f"report written to {args.out}")
    print("OVERALL:", "PASS (all bitwise identical)" if overall else "CHECK differences")
    return 0


if __name__ == "__main__":
    sys.exit(main())
