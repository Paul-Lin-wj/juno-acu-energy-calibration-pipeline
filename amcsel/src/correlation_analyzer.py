# -----------------------------------------------------------------------------
# Program: correlation_analyzer.py
# Author: Shubing Liu <liusb@ihep.ac.cn>
# Created: 2025-01-11
# Updated: 2026-03-25
# Description: Analyzer for Correlated Events (Prompt-Delay) and Single Events (Cs137)
# -----------------------------------------------------------------------------

from base_analyzer import BaseAnalyzer
from fv_selector import FVSelector
import numpy as np
import awkward as ak
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Rectangle
from iminuit import Minuit
from iminuit import cost
import os
from config_manager import AnalysisConfig
from local_reconstruction_ana import GetBinCenter, getCoinTag, PlotFitResult

class CorrelationAnalyzer(FVSelector):
    def __init__(self, config: AnalysisConfig, run_id: int):
        super().__init__(config, run_id)
        self.correlation_result = None
        self.cs137_result = None
        self.dn_result = None  # Dark Noise result
        
        # Parameters
        self.energy_limit = 0.5  # MeV
        self.Delay_region = [1.4, 12]  # MeV
        self.Promt_region = [0.5, 12]  # MeV
        self.nH_region = [1.8, 2.25]   # nH region
        self.Distance_limit = 1  # m
        self.dt_cut = 1000  # us
        
        # Output path
        self.select_result_path = config.select_result_path
        os.makedirs(self.select_result_path, exist_ok=True)
        
    def set_parameters(self, energy_limit=0.5, delay_region=None, promt_region=None, 
                     nH_region=None, distance_limit=1, dt_cut=1000):
        """Set analysis parameters"""
        self.energy_limit = energy_limit
        self.Delay_region = delay_region if delay_region else [1.4, 12]
        self.Promt_region = promt_region if promt_region else [0.5, 12]
        if nH_region:
            self.nH_region = nH_region
        self.Distance_limit = distance_limit
        self.dt_cut = dt_cut
    
    def calculate_dark_noise(self):
        """Calculate Dark Noise (Ported from DNAnalyzer)"""
        if not self.data_loaded:
            self.load_data()
            
        # Select periodic triggers that are not Muon Vetoed
        trigger_types = self.CDEvt_data['trigger_type']
        index_periodic = trigger_types == "Periodic"
        index_Muonveto = self.CDEvt_data['MuonVeto'] == True
        
        dn_data = {}
        skip_cols = ["trigger_type", "global_time_s", "global_time_ns", "Muon", "MuonVeto", "LivingTime"]
        
        for col in self.CDEvt_data.keys():
            if col in skip_cols:
                continue
            
            # Skip scalars
            data_col = self.CDEvt_data[col]
            if np.ndim(data_col) == 0: 
                continue
                
            if len(data_col) > 0:
                dn_data[col] = data_col[index_periodic & ~index_Muonveto]
        
        self.dn_result = {}
        for col, data in dn_data.items():
            if len(data) > 0:
                self.dn_result[col] = (
                    np.mean(data), 
                    np.std(data)/np.sqrt(len(data)) if len(data) > 1 else 0
                )
            else:
                self.dn_result[col] = (0.0, 0.0)
        
        if "totalPE" not in self.dn_result:
             self.dn_result["totalPE"] = (0.0, 0.0)

        return self.dn_result
    
    def find_correlated_events(self, dt_cut=None):
        """Find correlated events (Prompt-Delay pairs)"""
        if dt_cut is not None:
            self.dt_cut = dt_cut
            
        if self.efv_index is None:
            self.apply_fv_selection()
            
        print(f"🔍 开始寻找RUN {self.run_id}的关联事件 (dt_cut={self.dt_cut}us)...")
        print(f"   当前筛选条件: Prompt {self.Promt_region} MeV, Delay {self.Delay_region} MeV")
        
        # Timestamp calculation
        timestamp = (self.CDEvt_data["global_time_s"] * 1e6 + 
                    self.CDEvt_data["global_time_ns"] * 1e-3)  # us

        # Calculate DN if not done
        if self.dn_result is None:
            self.calculate_dark_noise()
        
        # Subtract DN
        dn_totalPE = self.dn_result.get("totalPE", (0, 0))[0]
        Total_PE = np.array(self.CDEvt_data["totalPE"]) - dn_totalPE
        OEC_energy = np.array(self.CDEvt_data["oec_energy"])
        
        # Position reference
        position = self.run_position['Z'] / 100.0  # cm -> m
        
        idx_arr = np.arange(0, len(Total_PE), 1)

        # Step 1: Initial Selection
        index_MuonVeto = self.CDEvt_data["MuonVeto"] == True
        index_init = (
            (OEC_energy > self.energy_limit) &
            (OEC_energy < 14) &
            (~index_MuonVeto) &
            self.efv_index
        )
        
        idx_init = idx_arr[index_init]
        
        if len(idx_init) == 0:
            print(f"⚠️ RUN {self.run_id}: 没有满足初始选择条件的事件")
            self.correlation_result = None # Clear previous result
            return None

        # Step 2: Correlation Search
        OEC_energy_init = OEC_energy[index_init]
        timestamp_us_init = timestamp[index_init]
        
        dict_tag = getCoinTag(OEC_energy_init, timestamp_us_init, self.dt_cut)
        
        # Filter pairs
        index_pair = ak.where(ak.count(dict_tag["index"], axis=1) == 2)[0]
        
        if len(index_pair) == 0:
            print(f"⚠️ RUN {self.run_id}: 没有找到关联事件对")
            self.correlation_result = None
            return None

        # Get indices for Prompt and Delay
        pair_indices = dict_tag["index"][index_pair]
        idx_promt = idx_init[pair_indices[:, 0]]
        idx_delay = idx_init[pair_indices[:, 1]]

        # Step 3: Further Selection (Distance & Energy Window)
        promt_x = self.CDEvt_data["oec_x"][idx_promt]
        promt_y = self.CDEvt_data["oec_y"][idx_promt]
        promt_z = self.CDEvt_data["oec_z"][idx_promt]
        
        delay_x = self.CDEvt_data["oec_x"][idx_delay]
        delay_y = self.CDEvt_data["oec_y"][idx_delay]
        delay_z = self.CDEvt_data["oec_z"][idx_delay]
        
        Distance_Pair = np.sqrt(
            (delay_x - promt_x)**2 +
            (delay_y - promt_y)**2 +
            (delay_z - promt_z)**2
        )

        promt_E = self.CDEvt_data["oec_energy"][idx_promt]
        delay_E = self.CDEvt_data["oec_energy"][idx_delay]

        # Apply cuts
        index_Delay = (delay_E > self.Delay_region[0]) & (delay_E < self.Delay_region[1])
        index_Promt = (promt_E > self.Promt_region[0]) & (promt_E < self.Promt_region[1])
        index_Distance = (Distance_Pair / 1e3) < self.Distance_limit
        
        index_final = index_Distance & index_Delay & index_Promt

        # Final indices
        idx_delay_final = idx_delay[index_final]
        idx_promt_final = idx_promt[index_final]
        
        # Distributions for plotting
        dt_pair = timestamp[idx_delay_final] - timestamp[idx_promt_final]
        pe_promt_final = Total_PE[idx_promt_final]
        pe_delay_final = Total_PE[idx_delay_final]

        self.correlation_result = {
            'idx_promt': idx_promt_final,
            'idx_delay': idx_delay_final,
            'dt_distribution': dt_pair,
            'distance_distribution': Distance_Pair[index_final],
            'prompt_energy': promt_E[index_final],
            'delay_energy': delay_E[index_final],
            'total_pe_prompt': pe_promt_final,
            'total_pe_delay': pe_delay_final,
            'position': position
        }
        
        print(f"✅ RUN {self.run_id} 关联事件查找完成")
        print(f"   找到 {len(idx_promt_final)} 个有效事件对")
        print(f"   Prompt事件率: {len(idx_promt_final)/self.living_time:.2f} Hz")
        print(f"   Delay事件率: {len(idx_delay_final)/self.living_time:.2f} Hz")
        
        return self.correlation_result
    
    def find_cs137_events(self, isolation_time=1000, n_std_cut=3.0):
        """两步能量 cut 的孤立单事例挑选：先 first cut，再做原有 3sigma cut"""
        print(f"🔍 正在运用反符合逻辑 (±{isolation_time} μs) 挑选孤立单事例...")

        if self.efv_index is None:
            self.apply_fv_selection()

        timestamp = (self.CDEvt_data["global_time_s"] * 1e6 + self.CDEvt_data["global_time_ns"] * 1e-3)
        dt_prev = np.zeros_like(timestamp)
        dt_next = np.zeros_like(timestamp)

        if len(timestamp) > 1:
            dt_prev[1:] = np.diff(timestamp)
            dt_prev[0] = np.inf
            dt_next[:-1] = np.diff(timestamp)
            dt_next[-1] = np.inf
        else:
            dt_prev[0] = np.inf
            dt_next[0] = np.inf

        is_isolated = (dt_prev > isolation_time) & (dt_next > isolation_time)

        # 仅使用 MuonVeto + 空间椭球 FV（不再额外叠加 FV 能量窗）
        x_center, x_cut = self.fv_cuts.get('x', [0, 0])
        y_center, y_cut = self.fv_cuts.get('y', [0, 0])
        z_center, z_cut = self.fv_cuts.get('z', [0, 0])
        index_MuonVeto = self.CDEvt_data["MuonVeto"] == True

        if x_cut <= 0 or y_cut <= 0 or z_cut <= 0:
            index_ellipse = np.zeros_like(self.CDEvt_data["oec_energy"], dtype=bool)
        else:
            x_scale = ((self.CDEvt_data["oec_x"] / 1e3 - x_center) / x_cut) ** 2
            y_scale = ((self.CDEvt_data["oec_y"] / 1e3 - y_center) / y_cut) ** 2
            z_scale = ((self.CDEvt_data["oec_z"] / 1e3 - z_center) / z_cut) ** 2
            index_ellipse = (x_scale + y_scale + z_scale) <= 1

        index_cs137_base = is_isolated & (~index_MuonVeto) & index_ellipse
        energies_base = self.CDEvt_data["oec_energy"][index_cs137_base]

        if len(energies_base) == 0:
            self.cs137_wo_ecut_result = None
            self.cs137_result = None
            print(f"⚠️ RUN {self.run_id}: 没有找到符合孤立时间条件的单事例")
            return

        # ---------- 第一次能量 cut：0-12 MeV, 100 bins, 峰后右扫直到停止下降 ----------
        counts_first, edges_first = np.histogram(energies_base, bins=100, range=(0.0, 12.0))
        centers_first = (edges_first[:-1] + edges_first[1:]) / 2
        peak_idx = int(np.argmax(counts_first))
        first_cut_idx = len(counts_first) - 1
        for i in range(peak_idx, len(counts_first) - 1):
            if counts_first[i + 1] > counts_first[i]:
                first_cut_idx = i
                break
        first_cut_max = edges_first[first_cut_idx + 1]

        index_cs137_first = index_cs137_base & (self.CDEvt_data["oec_energy"] <= first_cut_max)
        energies_first = self.CDEvt_data["oec_energy"][index_cs137_first]

        self.cs137_wo_ecut_result = {
            'energy': energies_first,
            'x': self.CDEvt_data["oec_x"][index_cs137_first],
            'y': self.CDEvt_data["oec_y"][index_cs137_first],
            'z': self.CDEvt_data["oec_z"][index_cs137_first],
            'global_time_s': self.CDEvt_data["global_time_s"][index_cs137_first],
            'global_time_ns': self.CDEvt_data["global_time_ns"][index_cs137_first],
            'first_cut_max': first_cut_max,
            'hist_centers': centers_first,
            'hist_counts': counts_first,
        }

        self.plot_cs137_first_cut(
            energies_base=energies_base,
            first_cut_max=first_cut_max,
            n_before=len(energies_base),
            n_after=len(energies_first),
        )

        if len(energies_first) == 0:
            self.cs137_result = None
            print(f"⚠️ RUN {self.run_id}: 第一次能量cut后无事例")
            return

        # ---------- 第二次能量 cut：沿用原有 3sigma 动态拟合流程 ----------
        energies_all = energies_first

        counts, bin_edges = np.histogram(energies_all, bins=200)
        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
        peak_idx = np.argmax(counts)
        peak_E = bin_centers[peak_idx]

        x_left_idx = peak_idx
        for i in range(peak_idx, -1, -1):
            if counts[i] == 0:
                x_left_idx = i
                break
        else:
            x_left_idx = 0
        x_left = bin_centers[x_left_idx]

        x_right_idx = peak_idx
        for i in range(peak_idx, len(counts) - 1):
            if counts[i + 1] > counts[i]:
                x_right_idx = i
                break
        else:
            x_right_idx = len(counts) - 1
        x_right = bin_centers[x_right_idx]

        fit_left_stage1 = min(x_left, x_right)
        fit_right = max(x_left, x_right)
        if np.isclose(fit_left_stage1, fit_right):
            fit_right = fit_left_stage1 + 1e-3

        fit_low = 0.32
        fit_high = first_cut_max
        if fit_low < fit_left_stage1:
            fit_low = fit_left_stage1
        if fit_low >= fit_high:
            fit_low = fit_left_stage1

        # Keep displayed/stored fit upper bound consistent with the actual second-fit upper bound.
        x_right = fit_high

        energies_fit_range = energies_all[(energies_all >= fit_low) & (energies_all <= fit_high)]
        counts_fit, bins_fit = np.histogram(energies_fit_range, bins=100, range=(fit_low, fit_high))
        centers_fit = (bins_fit[:-1] + bins_fit[1:]) / 2

        mask_fit = counts_fit > 0
        x_fit = centers_fit[mask_fit]
        y_fit = counts_fit[mask_fit]
        err_y_fit = np.sqrt(y_fit)

        def fit_pdf(x, amp, mean, sigma, Ac, q, Ec, wc, c0, c1):
            gauss = amp * np.exp(-0.5 * ((x - mean) / sigma) ** 2)
            edge = 1.0 / (1.0 + np.exp((x - Ec) / wc))
            continuum = Ac * np.clip(1.0 + q * (x - fit_low), 0.0, None) * edge
            bkg = c0 + c1 * x
            return gauss + continuum + bkg

        try:
            from iminuit import cost, Minuit

            cst = cost.LeastSquares(x_fit, y_fit, err_y_fit, fit_pdf)

            amp0 = float(max(np.max(y_fit) - np.median(y_fit), 1.0)) if len(y_fit) > 0 else 1.0
            mean0 = float(peak_E)
            sigma0 = float(max(0.012, min(0.09, np.std(energies_fit_range) if len(energies_fit_range) > 1 else 0.03)))

            comp_mask = (x_fit >= max(fit_low, peak_E - 0.22)) & (x_fit <= max(fit_low + 0.02, peak_E - 0.08))
            Ac0 = float(max(np.median(y_fit[comp_mask]) if np.any(comp_mask) else np.median(y_fit), 1.0))
            q0 = 2.0 / max((fit_high - fit_low), 1e-3)
            Ec0 = float(max(fit_low + 0.04, min(0.72 * peak_E, peak_E - 0.01, fit_high - 0.01)))
            wc0 = 0.020

            c00 = float(max(np.min(y_fit), 0.0)) if len(y_fit) > 0 else 0.0
            c10 = 0.0

            m = Minuit(
                cst,
                amp=amp0,
                mean=mean0,
                sigma=sigma0,
                Ac=Ac0,
                q=q0,
                Ec=Ec0,
                wc=wc0,
                c0=c00,
                c1=c10,
            )

            peak_window = max(0.03, min(0.08, 0.20 * (fit_high - fit_low)))
            mean_low = max(fit_low, peak_E - peak_window)
            mean_high = min(fit_high, peak_E + peak_window)

            ec_low = max(fit_low + 0.03, 0.58 * peak_E)
            ec_high = min(fit_high - 0.005, peak_E - 0.001)

            m.limits['amp'] = (0.0, None)
            m.limits['mean'] = (mean_low, mean_high)
            m.limits['sigma'] = (0.008, 0.10)
            m.limits['Ac'] = (0.0, None)
            m.limits['q'] = (-8.0, 25.0)
            m.limits['Ec'] = (ec_low, ec_high)
            m.limits['wc'] = (0.004, 0.10)

            m.migrad()
            m.hesse()

            res = m.values
            fit_mean = res["mean"]
            fit_sigma = abs(res["sigma"])
            chi2 = m.fval
            ndf = len(x_fit) - m.nfit
            fit_params = {name: m.values[name] for name in m.parameters}
            fit_params['chi2'] = chi2
            fit_params['ndf'] = ndf
            print(f"   ✅ 拟合成功: mean={fit_mean:.3f}, sigma={fit_sigma:.3f}, chi2/ndf={chi2:.1f}/{ndf}")
        except Exception as e:
            print(f"   ⚠️ 拟合失败: {type(e).__name__}: {repr(e)}，回退到粗略估算")
            fit_mean = peak_E
            energies_for_std = energies_all[(energies_all >= x_left) & (energies_all <= x_right)]
            fit_sigma = np.std(energies_for_std) if len(energies_for_std) > 0 else 0.05
            fit_sigma = max(fit_sigma, 1e-3)
            c_fallback = float(np.median(y_fit)) if len(y_fit) > 0 else 0.0
            amp_fallback = float(max(np.max(y_fit) - c_fallback, 1.0)) if len(y_fit) > 0 else 1.0
            fit_params = {
                'amp': amp_fallback,
                'mean': float(fit_mean),
                'sigma': float(fit_sigma),
                'Ac': float(max(c_fallback, 1.0)),
                'q': 2.0 / max((fit_high - fit_low), 1e-3),
                'Ec': float(min(fit_high, fit_mean - 0.03)),
                'wc': 0.02,
                'c0': c_fallback,
                'c1': 0.0,
                'chi2': np.nan,
                'ndf': 0,
            }

        cut_min = fit_mean - n_std_cut * fit_sigma
        cut_max = fit_mean + n_std_cut * fit_sigma

        index_cs137_final = index_cs137_first & (self.CDEvt_data["oec_energy"] >= cut_min) & (self.CDEvt_data["oec_energy"] <= cut_max)

        if np.sum(index_cs137_final) > 0:
            self.cs137_result = {
                'energy_all': energies_all,
                'energy': self.CDEvt_data["oec_energy"][index_cs137_final],
                'x': self.CDEvt_data["oec_x"][index_cs137_final],
                'y': self.CDEvt_data["oec_y"][index_cs137_final],
                'z': self.CDEvt_data["oec_z"][index_cs137_final],
                'global_time_s': self.CDEvt_data["global_time_s"][index_cs137_final],
                'global_time_ns': self.CDEvt_data["global_time_ns"][index_cs137_final],
                'cut_min': cut_min,
                'cut_max': cut_max,
                'x_left': fit_low,
                'x_right': x_right,
                'fit_params': fit_params,
                'fit_bin_centers': centers_fit,
                'fit_bin_counts': counts_fit,
                'fit_bin_width': (bins_fit[1] - bins_fit[0]) if len(bins_fit) > 1 else 0.0,
                'first_cut_max': first_cut_max,
            }
            print(f"✅ RUN {self.run_id} 成功找到 {np.sum(index_cs137_final)} 个符合条件的孤立单事例 (FirstCut后: {np.sum(index_cs137_first)} 个)！")
            print(f"   First Cut: E <= {first_cut_max:.3f} MeV")
            print(f"   3σ Cut Range: [{cut_min:.3f}, {cut_max:.3f}] MeV")
            self.plot_cs137_spectrum()
        else:
            self.cs137_result = None
            print(f"⚠️ RUN {self.run_id}: 没有找到符合能量区间 [{cut_min:.3f}, {cut_max:.3f}] MeV 的单事例")

    def plot_cs137_first_cut(self, energies_base, first_cut_max, n_before, n_after):
        """绘制 Cs137 第一次能量 cut 示意图"""
        print(f"🎨 绘制RUN {self.run_id}的 Cs137 第一次能量cut示意图...")

        fig, ax = plt.subplots(dpi=300, figsize=(8, 5))
        bins = np.linspace(0.0, 12.0, 101)

        ax.hist(energies_base, bins=bins, histtype='step', color='tab:blue', linewidth=1.5, label='Before 1st E cut')
        ax.axvline(first_cut_max, color='tab:red', linestyle='--', linewidth=1.8, label=f'1st E cut: E <= {first_cut_max:.3f} MeV')

        ax.set_xlabel(r"$E_{rec}$ [MeV]")
        ax.set_ylabel("Counts / bin")
        ax.set_yscale('log')
        ax.set_title(f"Cs137 First Energy Cut RUN {self.run_id}")
        ax.legend(fontsize=9)

        ratio = (n_after / n_before * 100.0) if n_before > 0 else 0.0
        stats_text = (
            f"1st Cut: E <= {first_cut_max:.3f} MeV\n"
            f"Before: {n_before}\n"
            f"After: {n_after}\n"
            f"Ratio: {ratio:.2f}%"
        )
        ax.text(
            0.98,
            0.95,
            stats_text,
            transform=ax.transAxes,
            fontsize=10,
            va='top',
            ha='right',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.85),
        )

        output_pdf = os.path.join(self.select_result_path, f"Cs137_First_Ecut_Spectrum_RUN{self.run_id}.pdf")
        fig.tight_layout()
        fig.savefig(output_pdf)
        plt.close(fig)
        print(f"✅ 第一次能量cut示意图已保存: {output_pdf}")

    def plot_cs137_spectrum(self):
        """绘制挑选出的最终单事例全能谱"""
        if self.cs137_result is None:
            return

        print(f"🎨 绘制RUN {self.run_id}的单事例全能谱...")

        # 主图 + 右侧信息面板，保证图例和统计框统一排版且不重叠
        fig = plt.figure(dpi=300, figsize=(11, 5))
        gs = fig.add_gridspec(1, 2, width_ratios=[3.8, 1.9], wspace=0.05)
        ax = fig.add_subplot(gs[0, 0])
        ax_info = fig.add_subplot(gs[0, 1])
        ax_info.axis('off')

        # 设置刻度线向内
        plt.rcParams['xtick.direction'] = 'in'
        plt.rcParams['ytick.direction'] = 'in'

        energies_all = self.cs137_result['energy_all']
        energies_final = self.cs137_result['energy']
        cut_min = self.cs137_result.get('cut_min', 0)
        cut_max = self.cs137_result.get('cut_max', 1)
        x_left = self.cs137_result.get('x_left', 0)
        x_right = self.cs137_result.get('x_right', 1)
        fit_params = self.cs137_result.get('fit_params', None)

        # 1. 用于拟合的数据分 bin（fit range 内 100 bins）画黑色散点 + xy 误差
        fit_bin_centers = self.cs137_result.get('fit_bin_centers', None)
        fit_bin_counts = self.cs137_result.get('fit_bin_counts', None)
        fit_bin_width = self.cs137_result.get('fit_bin_width', None)

        if fit_bin_centers is None or fit_bin_counts is None:
            # 兼容旧结果文件：若未保存拟合 bin，则临时按 fit range 现算
            counts_fit, bins_fit = np.histogram(
                energies_all[(energies_all >= x_left) & (energies_all <= x_right)],
                bins=50,
                range=(x_left, x_right),
            )
            fit_bin_counts = counts_fit
            fit_bin_centers = (bins_fit[:-1] + bins_fit[1:]) / 2
            fit_bin_width = (bins_fit[1] - bins_fit[0]) if len(bins_fit) > 1 else 0.0

        counts = np.asarray(fit_bin_counts)
        bin_centers = np.asarray(fit_bin_centers)
        bin_width = float(fit_bin_width) if fit_bin_width is not None else 0.0
        y_err = np.sqrt(counts)

        mask_gt0 = counts > 0
        ax.errorbar(
            bin_centers[mask_gt0],
            counts[mask_gt0],
            yerr=y_err[mask_gt0],
            xerr=bin_width / 2,
            fmt='ko',
            markersize=3,
            elinewidth=1,
            capsize=2,
            label='Data (fit bins)',
        )

        # 2. 灰色虚线标出拟合区间
        ax.axvline(x_left, color='gray', linestyle='--', label='Fit Range')
        ax.axvline(x_right, color='gray', linestyle='--')

        # 将 Cut 范围也画上去 (红色点划线)
        ax.axvline(cut_min, color='r', linestyle='-.', alpha=0.7, label='Cut Range')
        ax.axvline(cut_max, color='r', linestyle='-.', alpha=0.7)

        # 3. 绘制拟合曲线
        if fit_params:
            x_fit_curve = np.linspace(x_left, x_right, 200)
            amp, mean, sigma = fit_params['amp'], fit_params['mean'], fit_params['sigma']
            Ac, q = fit_params['Ac'], fit_params['q']
            Ec, wc = fit_params['Ec'], fit_params['wc']
            c0, c1 = fit_params['c0'], fit_params['c1']

            sig_curve = amp * np.exp(-0.5 * ((x_fit_curve - mean) / sigma)**2)
            edge_curve = 1.0 / (1.0 + np.exp((x_fit_curve - Ec) / wc))
            comp_curve = Ac * np.clip(1.0 + q * (x_fit_curve - x_left), 0.0, None) * edge_curve
            bkg_curve = c0 + c1 * x_fit_curve
            tot_curve = sig_curve + comp_curve + bkg_curve

            ax.plot(x_fit_curve, tot_curve, 'r-', linewidth=2, label='Total Fit')
            ax.plot(x_fit_curve, sig_curve, 'g--', linewidth=1.5, label='Signal (Gauss)')
            ax.plot(x_fit_curve, comp_curve + bkg_curve, 'b:', linewidth=1.8, label='Compton + Bkg')

        ax.set_xlabel(r"$E_{rec}$ [MeV]")
        ax.set_ylabel("Counts / bin")
        ax.set_title(f"Cs137 Spectrum RUN {self.run_id} (Fit: [{x_left:.3f}, {x_right:.3f}] MeV)")
        x_min = max(0.0, 0.9 * x_left)
        x_max = 1.1 * x_right
        if x_max > x_min:
            ax.set_xlim(x_min, x_max)

        # 使用线性坐标显示 Cs137 能谱
        # if np.max(counts) > 0:
        #     ax.set_yscale("log")

        # 4. 提取并计算统计信息
        total_before = len(energies_all)
        total_after = len(energies_final)
        cut_removed = total_before - total_after
        ratio = total_after / total_before * 100 if total_before > 0 else 0

        stats_text = (f"Before Cut: {total_before}\n"
                      f"Final Events: {total_after}\n"
                      f"Cut Removed: {cut_removed}\n"
                      f"Ratio: {ratio:.1f}%\n"
                      f"Fit Range: [{x_left:.3f}, {x_right:.3f}]\n"
                      f"Cut Range: [{cut_min:.3f}, {cut_max:.3f}]\n")

        if fit_params:
            chi2 = fit_params.get('chi2', 0)
            ndf = fit_params.get('ndf', 1)
            chi2_ndf = chi2 / ndf if ndf > 0 else 0
            stats_text += (f"Mean: {fit_params['mean']:.3f} MeV\n"
                           f"Sigma: {fit_params['sigma']:.4f} MeV\n"
                           f"chi2/ndf: {chi2:.1f}/{ndf} = {chi2_ndf:.2f}")

        # 右侧面板统一放置图例和统计框
        handles, labels = ax.get_legend_handles_labels()
        ax_info.legend(handles, labels, loc='upper left', fontsize=9, frameon=True)
        ax_info.text(
            0.02,
            0.05,
            stats_text,
            transform=ax_info.transAxes,
            fontsize=10,
            verticalalignment='bottom',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.85),
        )

        output_pdf = os.path.join(self.select_result_path, f"Cs137_Final_Spectrum_RUN{self.run_id}.pdf")
        fig.savefig(output_pdf, bbox_inches='tight')
        plt.close(fig)

        print(f"✅ 单事例能谱图已保存: {output_pdf}")


    def fit_capture_time(self):
        """拟合中子俘获时间"""
        if self.correlation_result is None:
            self.find_correlated_events()
            
        if self.correlation_result is None or len(self.correlation_result['dt_distribution']) == 0:
            print(f"⚠️ RUN {self.run_id}: 没有关联事件可用于拟合")
            return None
            
        print(f"📊 开始拟合RUN {self.run_id}的中子俘获时间...")
        
        dt_data = self.correlation_result['dt_distribution']
        bins_dt = np.linspace(0, self.dt_cut, 40)
        hist_count, _ = np.histogram(dt_data, bins=bins_dt)
        
        # 计算误差
        err_hist = np.sqrt(hist_count)
        index_err = err_hist > 0
        bins_center = GetBinCenter(bins_dt)
        # 拟合范围选择有数据的部分
        index_fit_range = index_err

        def fcnmodel(x, decay, A, c):
            return A * np.exp(-x / decay) + c

        # 初始参数估计
        init_decay = 200  # us
        # 简单的初始值估计
        max_count = np.max(hist_count)
        tail_mean = np.mean(hist_count[-5:]) if len(hist_count) > 5 else 0
        init_A = max_count - tail_mean
        init_c = tail_mean

        # 使用iminuit拟合
        try:
            c = cost.LeastSquares(
                bins_center[index_fit_range],
                hist_count[index_fit_range],
                err_hist[index_fit_range],
                fcnmodel,
            )
            m = Minuit(c, decay=init_decay, A=init_A, c=init_c)

            m.limits["decay"] = (1, 10000)
            m.limits["A"] = (0, None)
            m.limits["c"] = (0, None)
            m.migrad()

            if not m.valid:
                print(f"❌ RUN {self.run_id}: 拟合无效")
                # 即使无效也尝试返回参数，方便调试
            
            # 计算拟合结果
            v = m.parameters
            dict_result = {}
            for key in v:
                value = float(m.values[key])
                dict_result[key] = value
                try:
                    err = float(m.errors[key])
                except:
                    err = 0
                dict_result[f"{key}_err"] = err

            # 计算χ²/NDF
            y_fit = fcnmodel(bins_center[index_fit_range], 
                           dict_result["decay"], dict_result["A"], dict_result["c"])
            y_data = hist_count[index_fit_range]
            y_err = err_hist[index_fit_range]
            
            chi2 = np.sum(((y_data - y_fit) / y_err) ** 2)
            ndf = len(y_data) - 3  # 3个参数
            red_chi2 = chi2 / ndf if ndf > 0 else 0
            
            dict_result["chi2ndf"] = red_chi2
            dict_result["fval"] = m.fval
            dict_result["ndof"] = m.ndof

            print(f"✅ RUN {self.run_id} 俘获时间拟合完成")
            print(f"   τ = {dict_result['decay']:.1f} ± {dict_result['decay_err']:.1f} μs")
            print(f"   χ²/NDF = {red_chi2:.2f}")

            return dict_result
            
        except Exception as e:
            print(f"❌ RUN {self.run_id} 拟合失败: {e}")
            return None
    
    def plot_correlation_results(self, output_pdf=True):
        """绘制关联分析结果"""
        if self.correlation_result is None:
            # 尝试查找，如果依然没有结果则返回
            if self.find_correlated_events() is None:
                return
            
        print(f"🎨 绘制RUN {self.run_id}的关联分析结果...")
        
        # 获取拟合结果
        fit_result = self.fit_capture_time()
        
        if output_pdf:
            pdf = PdfPages(f"{self.select_result_path}/Correlation_RUN{self.run_id}.pdf")
        
        try:
            # 创建图形
            plt.figure(dpi=300, figsize=(10, 12))
            
            # 1. 时间差与距离的2D分布
            plt.subplot(321)
            dt_data = self.correlation_result['dt_distribution']
            distance_data = self.correlation_result['distance_distribution'] / 1e3  # 转换为m
            
            plt.hist2d(
                dt_data,
                distance_data,
                bins=(np.linspace(0, self.dt_cut, 40), 100),
                norm="log",
                cmap="rainbow",
            )
            # 使用 LaTeX 替代 Unicode
            plt.xlabel(r"$\Delta t$ [$\mu$s]") 
            plt.ylabel("Distance [m]")
            plt.axhline(self.Distance_limit, ls="--", color="tab:red", alpha=0.7)
            plt.colorbar(label="Counts")
            plt.title(f"Time vs Distance (RUN {self.run_id})")

            # 2. 时间差分布和拟合
            plt.subplot(322)
            bins_dt = np.linspace(0, self.dt_cut, 40)
            hist_count, _ = np.histogram(dt_data, bins=bins_dt)
            bins_center = GetBinCenter(bins_dt)
            
            plt.errorbar(
                bins_center,
                hist_count,
                yerr=np.sqrt(hist_count),
                fmt="o",
                mfc="none",
                label=f"Total events: {int(np.sum(hist_count))}",
                markersize=3,
            )
            
            if fit_result is not None:
                # 绘制拟合曲线
                x_fit = np.linspace(0, self.dt_cut, 100)
                y_fit = fit_result["A"] * np.exp(-x_fit / fit_result["decay"]) + fit_result["c"]
                # 使用 LaTeX 替代 Unicode (τ -> \tau, μs -> \mu s, χ -> \chi)
                label_fit = (f"Fit: tau={fit_result['decay']:.1f}+-{fit_result['decay_err']:.1f} us"
                             "\n"
                             fr"chi2/NDF={fit_result['chi2ndf']:.2f}")
                plt.plot(x_fit, y_fit, c="tab:green", label=label_fit)
                plt.axhline(fit_result["c"], ls="--", c="tab:green", alpha=0.7)

            plt.xlabel(r"$\Delta t$ [$\mu$s]")
            plt.ylabel("Counts")
            plt.legend(fontsize=8)
            plt.title("Capture Time Distribution")

            # 3. Prompt vs Delay能量分布
            plt.subplot(323)
            prompt_energy = self.correlation_result['prompt_energy']
            delay_energy = self.correlation_result['delay_energy']
            
            plt.hist2d(
                delay_energy,
                prompt_energy,
                bins=(np.arange(0, 12, 0.05), np.arange(0, 12, 0.05)),
                cmap="rainbow",
                norm="log",
            )
            plt.colorbar(label="Counts")
            plt.xlabel("Delay Energy [MeV]")
            plt.ylabel("Prompt Energy [MeV]")
            
            # 添加选择区域
            rect = Rectangle(
                (self.Delay_region[0], self.Promt_region[0]),
                self.Delay_region[1] - self.Delay_region[0],
                self.Promt_region[1] - self.Promt_region[0],
                linewidth=1.5,
                edgecolor="r",
                facecolor="none",
                ls="--",
                label=f"Selection region"
            )
            plt.gca().add_patch(rect)
            if "Am" in self.config.calib_type or "Cf" in self.config.calib_type:
                plt.axvline(self.nH_region[0], color="tab:orange", ls=":", lw=1.8, label=f"nH cut ({self.nH_region[0]}-{self.nH_region[1]} MeV)")
                plt.axvline(self.nH_region[1], color="tab:orange", ls=":", lw=1.8)
            plt.legend(fontsize=8)

            # 4. Prompt和Delay的PE分布
            plt.subplot(324)
            bins_pe = np.arange(0, 20000, 100)
            prompt_pe = self.correlation_result['total_pe_prompt']
            delay_pe = self.correlation_result['total_pe_delay']
            
            plt.hist(prompt_pe, bins=bins_pe, alpha=0.7, label="Prompt", density=True)
            plt.hist(delay_pe, bins=bins_pe, alpha=0.7, label="Delay", density=True, histtype="step", linewidth=2)
            plt.xlabel("Total PE (DN removed)")
            plt.ylabel("Normalized Counts")
            plt.yscale("log")
            plt.legend()
            plt.title("PE Distribution")

            # 5. Prompt和Delay的能量分布
            plt.subplot(325)
            bins_energy = np.arange(0, 14, 0.1)
            
            plt.hist(prompt_energy, bins=bins_energy, alpha=0.7, label="Prompt", density=True)
            plt.hist(delay_energy, bins=bins_energy, alpha=0.7, label="Delay", density=True, 
                    histtype="step", linewidth=2)
            plt.xlabel("Energy [MeV]")
            plt.ylabel("Normalized Counts")
            plt.yscale("log")
            plt.legend()
            plt.title("Energy Distribution")

            # 6. 统计信息
            plt.subplot(326)
            plt.axis('off')
            
            # 安全获取 fit_result 值，防止 None
            tau_str = f"{fit_result['decay']:.1f} +/- {fit_result['decay_err']:.1f}" if fit_result else "N/A"
            chi2_str = f"{fit_result['chi2ndf']:.2f}" if fit_result else "N/A"
            A_str = f"{fit_result['A']:.1f} +/- {fit_result['A_err']:.1f}" if fit_result else "N/A"
            c_str = f"{fit_result['c']:.1f} +/- {fit_result['c_err']:.1f}" if fit_result else "N/A"

            # 文本统计使用简单的ASCII，避免复杂的LaTeX渲染问题
            stats_text = f"""
                RUN {self.run_id} Correlation Analysis
                Position: {self.correlation_result['position']:.2f} m
                Living Time: {self.living_time:.1f} s

                Event Statistics:
                Total Prompt Events: {len(prompt_energy)}
                Total Delay Events: {len(delay_energy)}
                Prompt Rate: {len(prompt_energy)/self.living_time:.1f} Hz
                Delay Rate: {len(delay_energy)/self.living_time:.1f} Hz

                Fit Results:
                Capture Time (tau): {tau_str} us
                Chi2/NDF: {chi2_str}
                Amplitude: {A_str}
                Background: {c_str}
            """
            
            plt.text(0.1, 0.9, stats_text, transform=plt.gca().transAxes, 
                    fontsize=10, verticalalignment='top', fontfamily='monospace')

            plt.tight_layout()
            
            if output_pdf:
                pdf.savefig()
                pdf.close()
                print(f"✅ 关联分析图已保存: {self.select_result_path}/Correlation_RUN{self.run_id}.pdf")
            else:
                plt.show()
            plt.close()
            
        except Exception as e:
            print(f"❌ 绘图失败: {e}")
            import traceback
            traceback.print_exc()
            if output_pdf and 'pdf' in locals():
                pdf.close()
            plt.close()
    
    def save_correlation_results(self):
        """仅保存挑选后的 prompt/delay/nH/Cs137 的能量与顶点信息"""
        save_dict = {}

        if self.correlation_result is not None:
            idx_prompt = self.correlation_result['idx_promt']
            idx_delay = self.correlation_result['idx_delay']

            prompt_energy = self.CDEvt_data["oec_energy"][idx_prompt]
            prompt_x = self.CDEvt_data["oec_x"][idx_prompt]
            prompt_y = self.CDEvt_data["oec_y"][idx_prompt]
            prompt_z = self.CDEvt_data["oec_z"][idx_prompt]

            delay_energy = self.CDEvt_data["oec_energy"][idx_delay]
            delay_x = self.CDEvt_data["oec_x"][idx_delay]
            delay_y = self.CDEvt_data["oec_y"][idx_delay]
            delay_z = self.CDEvt_data["oec_z"][idx_delay]

            save_dict.update({
                'prompt_energy': prompt_energy,
                'prompt_x': prompt_x,
                'prompt_y': prompt_y,
                'prompt_z': prompt_z,
                'delay_energy': delay_energy,
                'delay_x': delay_x,
                'delay_y': delay_y,
                'delay_z': delay_z,
            })

            nH_mask = (delay_energy >= self.nH_region[0]) & (delay_energy <= self.nH_region[1])
            save_dict.update({
                'nH_energy': delay_energy[nH_mask],
                'nH_x': delay_x[nH_mask],
                'nH_y': delay_y[nH_mask],
                'nH_z': delay_z[nH_mask],
            })

        # npz only keeps Cs137 events after the first energy cut.
        if getattr(self, 'cs137_wo_ecut_result', None) is not None:
            save_dict.update({
                'cs137_energy': self.cs137_wo_ecut_result['energy'],
                'cs137_x': self.cs137_wo_ecut_result['x'],
                'cs137_y': self.cs137_wo_ecut_result['y'],
                'cs137_z': self.cs137_wo_ecut_result['z'],
            })

        if len(save_dict) == 0:
            print("⚠️ 没有可保存的关联或 Cs137 挑选结果")
            return

        output_file = f"{self.select_result_path}/correlation_result_RUN{self.run_id}.npz"
        np.savez(output_file, **save_dict)
        print(f"✅ 挑选结果已保存: {output_file}")

    def get_correlation_statistics(self):
        """获取关联分析统计信息"""
        if self.correlation_result is None:
            return None
            
        fit_result = self.fit_capture_time()
        stats = {
            'run_id': self.run_id,
            'living_time': self.living_time,
            'position': self.correlation_result['position'],
            'prompt_events': len(self.correlation_result['idx_promt']),
            'delay_events': len(self.correlation_result['idx_delay']),
            'prompt_rate': len(self.correlation_result['idx_promt']) / self.living_time,
            'delay_rate': len(self.correlation_result['idx_delay']) / self.living_time,
        }
        
        if fit_result is not None:
            stats.update({
                'capture_time': fit_result['decay'],
                'capture_time_error': fit_result['decay_err'],
                'chi2_ndf': fit_result['chi2ndf']
            })
        
        return stats
    
    def fit_delay_pe_distribution(self, pmt_types=None, adree_types=None):
        """对Delay信号的PE分布进行高斯拟合"""
        # 简化版实现，防止依赖其他复杂的拟合工具
        pass
    def save_timestamps(self):
        """保存挑选后的事件时间戳 (txt): prompt/delay/nH/Cs137_wo_Ecut/Cs137_Ecut"""
        if self.correlation_result is None and getattr(self, 'cs137_result', None) is None and getattr(self, 'cs137_wo_ecut_result', None) is None:
            print("⚠️ 没有关联分析或Cs137结果可保存时间戳")
            return

        base_dir = self.config.timestamp_dir
        prompt_dir = os.path.join(base_dir, "prompt")
        delay_dir = os.path.join(base_dir, "delay")
        nH_dir = os.path.join(base_dir, "nH")
        cs137_wo_ecut_dir = os.path.join(base_dir, "Cs137_wo_Ecut")
        cs137_ecut_dir = os.path.join(base_dir, "Cs137_Ecut")

        os.makedirs(prompt_dir, exist_ok=True)
        os.makedirs(delay_dir, exist_ok=True)
        os.makedirs(nH_dir, exist_ok=True)
        os.makedirs(cs137_wo_ecut_dir, exist_ok=True)
        os.makedirs(cs137_ecut_dir, exist_ok=True)

        print("✅ 时间戳已开始保存 (TXT, comma-separated):")

        if self.correlation_result is not None:
            idx_delay = self.correlation_result['idx_delay']
            idx_prompt = self.correlation_result['idx_promt']
            delay_energy = self.correlation_result['delay_energy']

            if len(idx_prompt) > 0:
                prompt_data = np.column_stack((
                    self.CDEvt_data["global_time_s"][idx_prompt],
                    self.CDEvt_data["global_time_ns"][idx_prompt],
                ))
                np.savetxt(f"{prompt_dir}/RUN{self.run_id}.txt", prompt_data, fmt='%d', delimiter=',')
                print(f"   [All events] Prompt: {prompt_dir}/RUN{self.run_id}.txt")

            if len(idx_delay) > 0:
                delay_data = np.column_stack((
                    self.CDEvt_data["global_time_s"][idx_delay],
                    self.CDEvt_data["global_time_ns"][idx_delay],
                ))
                np.savetxt(f"{delay_dir}/RUN{self.run_id}.txt", delay_data, fmt='%d', delimiter=',')
                print(f"   [All events] Delay:  {delay_dir}/RUN{self.run_id}.txt")

            min_E, max_E = self.nH_region
            nH_mask = (delay_energy >= min_E) & (delay_energy <= max_E)
            idx_delay_nH = idx_delay[nH_mask]

            if len(idx_delay_nH) > 0:
                nH_data = np.column_stack((
                    self.CDEvt_data["global_time_s"][idx_delay_nH],
                    self.CDEvt_data["global_time_ns"][idx_delay_nH],
                ))
                np.savetxt(f"{nH_dir}/RUN{self.run_id}.txt", nH_data, fmt='%d', delimiter=',')
                print(f"   [nH (Delay)] nH:     {nH_dir}/RUN{self.run_id}.txt")
            else:
                print(f"⚠️ 在 {min_E}-{max_E} MeV 范围内没有找到 nH 事件。")

            print(f"   (共 {len(idx_delay)} 个事件对，其中 nH 候选 {len(idx_delay_nH)} 个)")

        if getattr(self, 'cs137_wo_ecut_result', None) is not None:
            cs137_wo_data = np.column_stack((
                self.cs137_wo_ecut_result["global_time_s"],
                self.cs137_wo_ecut_result["global_time_ns"],
            ))
            np.savetxt(f"{cs137_wo_ecut_dir}/RUN{self.run_id}.txt", cs137_wo_data, fmt='%d', delimiter=',')
            print(f"   [Cs137 1st cut] Cs137_wo_Ecut: {cs137_wo_ecut_dir}/RUN{self.run_id}.txt")

        if getattr(self, 'cs137_result', None) is not None:
            cs137_ecut_data = np.column_stack((
                self.cs137_result["global_time_s"],
                self.cs137_result["global_time_ns"],
            ))
            np.savetxt(f"{cs137_ecut_dir}/RUN{self.run_id}.txt", cs137_ecut_data, fmt='%d', delimiter=',')
            print(f"   [Cs137 2nd cut] Cs137_Ecut: {cs137_ecut_dir}/RUN{self.run_id}.txt")
