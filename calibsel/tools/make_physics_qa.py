#!/usr/bin/env python3
"""
make_physics_qa.py — 生产用单 run 物理 QA 图生成器（无需任何参考链路）
=====================================================================

对每个 run 产出一页人类可快速判读的物理特征图 + 数值摘要：

  图（data/physics_qa/Run{RUN}_physics_qa.png）：
    A. 全事例能谱（MuonVeto 通过，log-y）：源特征 γ 线（竖实线）+
       常见本底线 K40 1.461 / Tl208 2.615（竖虚线）+ 康普顿沿标记
    B. EFV 选择后能谱放大 + 主峰高斯拟合：峰位 μ、σ、σ/E（分辨率）
    C. ρ–Z 顶点密度 2D + 源位置（★）+ EFV 选择事件轮廓
    D. X–Y 顶点密度 2D + 源位置（★）
    E. 能量-时间稳定性：分时间箱中位能量 ± MAD（应水平）
    F. 事例率-时间：分时间箱 Hz（应平稳，缺口=DAQ 问题）
    G. totalPE–E 线性：2D 密度 + 中位 profile + 直线参考

  数值摘要（同名 .json / .md）：
    事例数、LivingTime、veto 占比、E<0 垃圾占比、各拟合峰 (μ,σ,σ/E)、
    能量时间漂移、率均值/RMS、顶点质心 vs 源位置距离、PE 线性残差

  人工判读要点（图上直接印出）：
    · 峰是否出现在源物理线附近（±几%）
    · σ/E 是否在源能量的合理分辨率范围
    · 顶点团簇是否贴住源位置、EFV 形状是否正常
    · E/F 是否水平/平稳，G 是否直线

用法：
    python tools/make_physics_qa.py --run 12370
    python tools/make_physics_qa.py --run 12370 --corrected-dir data/npz_corrected
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import tempfile

os.environ.setdefault("MPLCONFIGDIR", tempfile.gettempdir())

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.gridspec import GridSpec  # noqa: E402

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 源 → (光电峰列表, 康普顿沿列表)  [MeV]
SOURCE_LINES = {
    "Ge68":  ([0.511, 1.022], [0.341]),
    "Cs137": ([0.6617], [0.477]),
    "Mn54":  ([0.8348], [0.639]),
    "Co60":  ([1.1725, 1.3325, 2.5057], [0.963, 1.118]),
    "K40":   ([1.4608], [1.256]),
    "AmC":   ([2.2233, 4.4389], []),
}
BKG_LINES = [1.4608, 2.6145]  # K40, Tl208
BKG_LABEL = ["K40 1.461", "Tl208 2.615"]


def source_of_run(run: int):
    """从 CalibRUN_from_file.csv 读 (source, x, y, z) [m]；读不到返回 (None,)*4。"""
    path = os.path.join(os.path.dirname(PROJECT), "runcheck", "data", "CalibRUN_from_file.csv")
    if not os.path.exists(path):
        return None, None, None, None
    with open(path) as f:
        for row in csv.DictReader(f):
            try:
                if int(row["RUN"]) == run:
                    return (row["Source"], float(row["X[m]"]), float(row["Y[m]"]),
                            float(row["Z[m]"]))
            except (KeyError, ValueError):
                continue
    return None, None, None, None


def bkg_run_of(run: int):
    path = os.path.join(os.path.dirname(PROJECT), "runcheck", "data", "calib_to_analyze.txt")
    if not os.path.exists(path):
        return None
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("Source"):
                continue
            p = [x.strip() for x in line.split(",")]
            if len(p) < 3 or "-" not in p[1]:
                continue
            a, b = p[1].split("-")[:2]
            try:
                if int(a) <= run <= int(b):
                    return p[2]
            except ValueError:
                continue
    return None


def fit_gaussian(c, h, e0, amp0):
    """在 e0 附近对直方图做 高斯+线性本底 拟合，返回 (mu, sigma, amp) 或 None。"""
    from scipy.optimize import curve_fit
    w = max(0.06, 0.10 * e0)
    m = (c > e0 - w) & (c < e0 + w)
    if m.sum() < 10:
        return None
    x, y = c[m], h[m]
    sig0 = max(0.012, 0.035 * e0)

    def model(x, A, mu, sg, k, b):
        return A * np.exp(-0.5 * ((x - mu) / sg) ** 2) + k * (x - e0) + b

    try:
        p, _ = curve_fit(model, x, y, p0=[amp0, e0, sig0, 0, amp0 * 0.3],
                         maxfev=20000)
        A, mu, sg = p[0], p[1], abs(p[2])
        acc = max(0.06, 0.10 * e0)
        if A <= 0 or not (e0 - acc < mu < e0 + acc):
            return None
        return mu, sg, A
    except Exception:
        return None


def main() -> int:
    ap = argparse.ArgumentParser(description="single-run physics QA")
    ap.add_argument("--run", type=int, required=True)
    ap.add_argument("--corrected-dir",
                    default=os.path.join(PROJECT, "data", "npz_corrected"))
    ap.add_argument("--selection-npz", default=None)
    ap.add_argument("--out-dir", default=os.path.join(PROJECT, "data", "physics_qa"))
    args = ap.parse_args()
    run = args.run

    corr_path = os.path.join(args.corrected_dir, f"RUN{run}.npz")
    if not os.path.exists(corr_path):
        print(f"[ERROR] {corr_path} not found"); return 1
    d = np.load(corr_path, allow_pickle=True)

    E = d["omilrec_energy"].astype(np.float64)
    X = d["omilrec_x"].astype(np.float64) / 1000.0  # mm -> m
    Y = d["omilrec_y"].astype(np.float64) / 1000.0
    Z = d["omilrec_z"].astype(np.float64) / 1000.0
    PE = d["totalPE"].astype(np.float64)
    T = d["global_time_s"].astype(np.int64)
    veto = d["MuonVeto"].astype(bool)
    livetime = float(d["LivingTime"])

    keep = ~veto
    Ek, Xk, Yk, Zk, PEk, Tk = E[keep], X[keep], Y[keep], Z[keep], PE[keep], T[keep]
    n_sel, sel = None, None
    sel_path = args.selection_npz or os.path.join(
        PROJECT, "data", "selection", "npz", f"Run{run}_SelectionResult.npz")
    if os.path.exists(sel_path):
        sel = np.load(sel_path)
        n_sel = sel["calib_omilrec_energy"].size

    src, sx, sy, sz = source_of_run(run)
    lines, ces = ([], [])
    if src:
        key = src if src in SOURCE_LINES else src.rstrip("0123456789")
        lines, ces = SOURCE_LINES.get(key, ([], []))
    bkg = bkg_run_of(run)

    # ---------- 拟合峰（EFV 谱主峰 + 次峰；无 selection 用全体谱） ----------
    Es = sel["calib_omilrec_energy"].astype(np.float64) if sel is not None else Ek
    h, edges = np.histogram(Es, bins=800, range=(0, max(3.0, Es.max())))
    c = (edges[:-1] + edges[1:]) / 2
    from scipy.ndimage import gaussian_filter1d
    hs = gaussian_filter1d(h.astype(float), 4)
    order = np.argsort(hs)[::-1]
    peaks = []
    used = []
    for i in order:
        if hs[i] < hs.max() * 0.04:
            break
        if any(abs(c[i] - u) < 0.07 for u in used):
            continue
        r = fit_gaussian(c, h, c[i], hs[i])
        if r:
            mu, sg, A = r
            peaks.append(dict(E_MeV=round(mu, 4), sigma_MeV=round(sg, 4),
                              res_percent=round(100 * sg / mu, 2),
                              amp=int(A)))
            used.append(mu)
        if len(peaks) >= 4:
            break

    # ---------- 时间分箱稳定性 / 率 ----------
    t0, t1 = Tk.min(), Tk.max()
    span = max(t1 - t0, 1)
    nbin = min(120, max(20, span // 30))
    tb = np.linspace(t0, t1, nbin + 1)
    tc = (tb[:-1] + tb[1:]) / 2
    idx = np.clip(np.searchsorted(tb, Tk) - 1, 0, nbin - 1)
    rate = np.bincount(idx, minlength=nbin) / np.diff(tb)
    if sel is not None:
        ts = T[keep][np.isin(Ek, np.unique(sel["calib_omilrec_energy"]))]
    med_e, mad_e = [], []
    for i in range(nbin):
        m = idx == i
        med_e.append(np.median(Ek[m]) if m.any() else np.nan)
        mad_e.append(np.median(np.abs(Ek[m] - med_e[-1])) if m.any() else np.nan)
    med_e, mad_e = np.array(med_e, float), np.array(mad_e, float)
    finite = np.isfinite(med_e)
    drift_pct = 100 * (np.nanmax(med_e) - np.nanmin(med_e)) / np.nanmedian(med_e) \
        if finite.any() else float("nan")

    # ---------- PE–E profile 平滑性（0.3–2.7 MeV 稠密区；不做直线假设，
    # 因为 E 已过修正而 PE 为原始量，PE/E 本就不为常数；QA 看的是形状平滑性） ----------
    mpe = (Ek > 0.05) & (Ek < 8) & (PEk > 10)
    ebin = np.linspace(0.1, 4.0, 40)
    nb = len(ebin) - 1
    eidx = np.clip(np.searchsorted(ebin, Ek[mpe]) - 1, 0, nb - 1)
    prof = np.array([np.median(PEk[mpe][eidx == i]) if (eidx == i).any() else np.nan
                     for i in range(nb)])
    ec = (ebin[:-1] + ebin[1:]) / 2
    dense = (ec >= 0.3) & (ec <= 2.7) & np.isfinite(prof)
    ratio = prof[dense] / ec[dense]
    smooth_ok = dense.sum() >= 3
    jump_pct = float(np.max(np.abs(np.diff(ratio) / ratio[:-1])) * 100) \
        if smooth_ok else float("nan")

    # ---------- 顶点质心 vs 源位置 ----------
    if sel is not None:
        cx, cy, cz = (np.median(sel["calib_omilrec_x"]) / 1000,
                      np.median(sel["calib_omilrec_y"]) / 1000,
                      np.median(sel["calib_omilrec_z"]) / 1000)
        dist_mm = (np.hypot(cx - sx, np.hypot(cy - sy, cz - sz)) * 1000
                   if sx is not None else None)
    else:
        dist_mm = None

    # ---------- 画图 ----------
    fig = plt.figure(figsize=(18, 11))
    gs = GridSpec(3, 3, figure=fig, hspace=0.34, wspace=0.28)
    fig.suptitle(f"Physics QA — RUN {run}   source={src}   "
                 f"pos=({sx},{sy},{sz}) m   bkg={bkg}   "
                 f"{Ek.size:,} evts (veto-pass) / {E.size:,} total   "
                 f"LivingTime={livetime:.1f}s", fontsize=12)

    # A 全谱
    axA = fig.add_subplot(gs[0, 0])
    hA, eA = np.histogram(np.clip(Ek, 0, 8), bins=400, range=(0, 8))
    cA = (eA[:-1] + eA[1:]) / 2
    axA.step(cA, hA, where="mid", color="steelblue", lw=1)
    axA.set_yscale("log")
    for Eline in lines:
        axA.axvline(Eline, color="crimson", lw=1.2)
        axA.text(Eline, axA.get_ylim()[1], f" {Eline:.3f}", color="crimson",
                 fontsize=7, rotation=90, va="top")
    for Ece in ces:
        axA.axvline(Ece, color="darkorange", lw=0.9, ls=":")
    for Eb, lb in zip(BKG_LINES, BKG_LABEL):
        axA.axvline(Eb, color="gray", lw=0.9, ls="--")
        axA.text(Eb, axA.get_ylim()[1] * 0.5, f" {lb}", color="gray",
                 fontsize=6, rotation=90, va="top")
    axA.set_xlabel("omilrec_energy [MeV]")
    axA.set_ylabel("events / bin (log)")
    axA.set_title(f"A. full spectrum (MuonVeto-pass)   "
                  f"red=source lines, dotted=Compton edges\n"
                  f"E<0 junk: {(E < 0).mean():.2%}   vetoed: {veto.mean():.2%}",
                  fontsize=9)

    # B EFV 谱放大 + 拟合
    axB = fig.add_subplot(gs[0, 1])
    hB, eB = np.histogram(Es, bins=300,
                          range=(0, min(3.0, np.percentile(Es, 99.99) + 0.5)))
    cB = (eB[:-1] + eB[1:]) / 2
    axB.step(cB, hB, where="mid", color="steelblue", lw=1)
    axB.set_yscale("log")
    xx = np.linspace(0, cB.max(), 500)
    for p in peaks:
        A0 = p["amp"]
        axB.plot(xx, A0 * np.exp(-0.5 * ((xx - p["E_MeV"]) / p["sigma_MeV"]) ** 2),
                 "r--", lw=1)
        axB.annotate(f'{p["E_MeV"]:.3f} MeV\nσ/E={p["res_percent"]:.1f}%',
                     (p["E_MeV"], A0), fontsize=7, color="r",
                     xytext=(6, -2), textcoords="offset points")
    for Eline in lines:
        axB.axvline(Eline, color="crimson", lw=0.8, alpha=0.5)
    axB.set_xlabel("omilrec_energy [MeV]")
    axB.set_ylabel("events / bin (log)")
    axB.set_title("B. EFV-selected spectrum + Gaussian fits"
                  + (f"  (n={n_sel:,})" if n_sel else "  (all events)"), fontsize=9)

    # C ρ-Z
    axC = fig.add_subplot(gs[1, 0])
    r = np.hypot(Xk, Yk)
    hh, xe, ye = np.histogram2d(Zk, r, bins=(160, 160),
                                range=((-18.5, 18.5), (0, 18.5)))
    axC.pcolormesh(xe, ye, hh.T, norm=matplotlib.colors.LogNorm(), cmap="viridis")
    if sel is not None:
        rs = np.hypot(sel["calib_omilrec_x"] / 1000, sel["calib_omilrec_y"] / 1000)
        axC.scatter(sel["calib_omilrec_z"] / 1000, rs, s=0.3, c="red", alpha=0.04)
    if sx is not None:
        axC.scatter([sz], [np.hypot(sx, sy)], marker="*", s=220, c="w",
                    edgecolors="k", zorder=5)
    axC.set_xlabel("Z [m]"); axC.set_ylabel("ρ [m]")
    axC.set_title("C. vertex ρ–Z (log density), red=EFV selected, ★=source"
                  + (f"\ncentroid dist = {dist_mm:.0f} mm" if dist_mm else ""),
                  fontsize=9)

    # D X-Y
    axD = fig.add_subplot(gs[1, 1])
    hh, xe, ye = np.histogram2d(Xk, Yk, bins=(160, 160),
                                range=((-18.5, 18.5),) * 2)
    axD.pcolormesh(xe, ye, hh.T, norm=matplotlib.colors.LogNorm(), cmap="viridis")
    if sx is not None:
        axD.scatter([sx], [sy], marker="*", s=220, c="w", edgecolors="k", zorder=5)
    axD.set_xlabel("X [m]"); axD.set_ylabel("Y [m]")
    axD.set_title("D. vertex X–Y (log density), ★=source", fontsize=9)

    # E 能量稳定性
    axE = fig.add_subplot(gs[1, 2])
    dt = tc - t0
    axE.errorbar(dt[finite], med_e[finite], yerr=mad_e[finite], fmt="o-",
                 ms=2.5, lw=0.8, color="navy", elinewidth=0.7)
    gm = np.nanmedian(med_e)
    axE.axhline(gm, color="crimson", ls="--", lw=1)
    axE.set_xlabel("time since run start [s]")
    axE.set_ylabel("median E [MeV]")
    axE.set_title(f"E. energy stability   max drift = {drift_pct:.2f}%", fontsize=9)

    # F 率
    axF = fig.add_subplot(gs[2, 0])
    axF.step(dt, rate, where="mid", color="darkgreen", lw=1)
    axF.axhline(rate.mean(), color="crimson", ls="--", lw=1)
    axF.set_xlabel("time since run start [s]")
    axF.set_ylabel("rate [Hz]")
    axF.set_title(f"F. event rate   mean={rate.mean():.1f} Hz   "
                  f"rms/mean={rate.std()/rate.mean():.2%}", fontsize=9)

    # G PE–E profile
    axG = fig.add_subplot(gs[2, 1])
    hh, xe, ye = np.histogram2d(Ek[mpe], PEk[mpe], bins=(200, 200))
    axG.pcolormesh(xe, ye, hh.T, norm=matplotlib.colors.LogNorm(), cmap="viridis")
    axG.plot(ec[dense], prof[dense], "r--", lw=1.4)
    axG.set_xlabel("omilrec_energy [MeV]"); axG.set_ylabel("totalPE")
    axG.set_title(f"G. totalPE vs E (red = median profile)\n"
                  f"PE/E ratio max adjacent-bin jump = "
                  f"{jump_pct:.1f}% (0.3–2.7 MeV; should be smooth)", fontsize=9)

    # H 文本摘要
    axH = fig.add_subplot(gs[2, 2]); axH.axis("off")
    summary = [
        f"RUN {run}   source={src}",
        f"events total/veto-pass : {E.size:,} / {Ek.size:,}",
        f"MuonVeto fraction      : {veto.mean():.2%}",
        f"E<0 junk fraction      : {(E<0).mean():.2%}",
        f"LivingTime             : {livetime:.1f} s",
        f"EFV selected           : {n_sel if n_sel else 'n/a'}",
        "",
        "fitted peaks (EFV):",
        *[f'  {p["E_MeV"]:.3f} MeV  σ/E {p["res_percent"]:.1f}%  '
          f'({p["amp"]} evts/bin)' for p in peaks],
        "",
        f"energy drift (E)       : {drift_pct:.2f}%",
        f"rate mean / rms        : {rate.mean():.1f} / {rate.std():.1f} Hz",
        f"PE/E profile jump      : {jump_pct:.1f}% (smooth expected)",
    ]
    if dist_mm is not None:
        summary.append(f"vertex centroid dist   : {dist_mm:.0f} mm")
    axH.text(0.02, 0.98, "\n".join(summary), va="top", fontsize=9, family="monospace")

    os.makedirs(args.out_dir, exist_ok=True)
    png = os.path.join(args.out_dir, f"Run{run}_physics_qa.png")
    fig.savefig(png, dpi=130)
    plt.close(fig)

    payload = dict(run=run, source=src, source_pos_m=[sx, sy, sz], bkg_run=bkg,
                   n_total=int(E.size), n_veto_pass=int(Ek.size),
                   veto_fraction=round(float(veto.mean()), 5),
                   junk_negative_fraction=round(float((E < 0).mean()), 6),
                   living_time_s=round(livetime, 2), n_efv_selected=n_sel,
                   fitted_peaks=peaks, energy_drift_pct=round(float(drift_pct), 3),
                   rate_hz=dict(mean=round(float(rate.mean()), 2),
                                rms=round(float(rate.std()), 2)),
                   pe_over_e_profile=dict(
                       energy_range_MeV=[0.3, 2.7],
                       ratio_at_1MeV=round(float(np.interp(1.0, ec[dense], ratio)), 0),
                       max_adjacent_bin_jump_pct=None if not smooth_ok
                       else round(jump_pct, 2)),
                   vertex_centroid_dist_mm=None if dist_mm is None else round(float(dist_mm), 1))
    with open(os.path.join(args.out_dir, f"Run{run}_physics_qa.json"), "w") as f:
        json.dump(payload, f, indent=1)

    print(f"written: {png}")
    print(json.dumps(payload, indent=1)[:1200])
    return 0


if __name__ == "__main__":
    sys.exit(main())
