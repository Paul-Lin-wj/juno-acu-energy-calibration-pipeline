# -----------------------------------------------------------------------------
# Program: fv_selector.py
# Author: Shubing Liu <liusb@ihep.ac.cn>
# Created: 2025-01-11
# Updated: 2026-03-25
# Description: FV Selector for Correlated Events & Single Events
# -----------------------------------------------------------------------------

from base_analyzer import BaseAnalyzer
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.backends.backend_pdf import PdfPages
import os
from config_manager import AnalysisConfig
from local_reconstruction_ana import HistBasedLimitFinding, GetBinCenter

class FVSelector(BaseAnalyzer):
    def __init__(self, config: AnalysisConfig, run_id: int):
        super().__init__(config, run_id)
        self.fv_cuts = {}
        self.efv_index = None
        self.select_result_path = config.select_result_path
        os.makedirs(self.select_result_path, exist_ok=True)
        
        # 参数设置
        self.Promt_region = [0.5, 12]  # MeV
        self.Delay_region = [1.4, 12]  # MeV
        self.fv_energy_region = [0.5, 10.0]  # 可由 test.py 覆盖
        
    def optimize_fv_cuts(self, output_pdf=True):
        """统一的FV选择入口，统一走标准关联FV优化"""
        if not self.data_loaded:
            self.load_data()
            
        self._optimize_standard_fv(output_pdf)
            
        return self.fv_cuts

    def _optimize_standard_fv(self, output_pdf=True):
        """关联事例的标准 FV 优化"""
        fv_e_low, fv_e_high = self.fv_energy_region
        print(f"🎯 开始优化 RUN {self.run_id} 的关联事例 FV 切割条件 ({fv_e_low:.2f}-{fv_e_high:.2f} MeV)...")
        
        bins_energy = np.arange(0.0, 12.0, 0.005)
        bins_energy_center = GetBinCenter(bins_energy)
        bins_pos = np.arange(-17.8, 17.8, 0.05)
        bins_pos_center = GetBinCenter(bins_pos)
        bins_diff = np.arange(0, 5, 0.05)
        bins_diff_center = GetBinCenter(bins_diff)
        
        weights_bkg = np.ones_like(self.bkg_data["oec_energy"]) / self.bkg_living_time
        weights_run = np.ones_like(self.CDEvt_data["oec_energy"]) / self.living_time
        
        x_m, y_m, z_m = self.df_run_info.loc[self.run_id][["X(cm)", "Y(cm)", "Z(cm)"]].values / 1e2
        index_NonSingle = self.CDEvt_data["MuonVeto"] == False
        if "MuonVeto" in self.bkg_data:
            index_NonSingle_bkg = self.bkg_data["MuonVeto"] == False
        else:
            index_NonSingle_bkg = np.ones_like(self.bkg_data["oec_energy"], dtype=bool)
        
        if output_pdf:
            pdf = PdfPages(f"{self.select_result_path}/xyz_distribution_RUN{self.run_id}.pdf")
            
        try:
            fig, axes = plt.subplots(4, 2, figsize=(3 * 2.5, 2.5 * 4), dpi=300, width_ratios=[1, 2])
            
            # --- 1. Energy (0.5-10 MeV) ---
            ax = axes[0, :]
            hist_run, _, _ = ax[0].hist(self.CDEvt_data["oec_energy"][index_NonSingle], bins=bins_energy, histtype="step", color="tab:red", weights=weights_run[index_NonSingle])
            hist_bkg, _, _ = ax[0].hist(self.bkg_data["oec_energy"][index_NonSingle_bkg], bins=bins_energy, alpha=0.3, color="tab:blue", weights=weights_bkg[index_NonSingle_bkg])
            
            hist_diff = np.zeros_like(hist_run)
            hist_diff_err = np.zeros_like(hist_run)
            valid_idx = hist_run > 0
            hist_diff[valid_idx] = (hist_run[valid_idx] - hist_bkg[valid_idx]) / hist_run[valid_idx] * 100
            valid_err_idx = (hist_run > 0) & (hist_bkg > 0)
            hist_diff_err[valid_err_idx] = (hist_bkg[valid_err_idx] / hist_run[valid_err_idx]) * np.sqrt(1 / (hist_run[valid_err_idx] * self.living_time) + 1 / (hist_bkg[valid_err_idx] * self.bkg_living_time))
            
            ax[0].set_xlabel(r"$E_{rec}$ [MeV]")
            ax[0].set_ylabel("Event Rate [Hz]")
            if np.any(hist_run > 0): ax[0].set_yscale("log")

            ax[1].errorbar(bins_energy_center, hist_diff, yerr=hist_diff_err, color="tab:orange", capsize=3, marker="o", mfc="None", markersize=2)
            RD_threshold = np.mean(hist_diff)
            best_region = [fv_e_low, fv_e_high]

            ax[1].axhline(RD_threshold, ls="--", color="tab:red", label=fr"R$_{{\mathrm{{diff}}}}$ = {RD_threshold:.0f} %", zorder=10, lw=2)
            ax[1].axvspan(best_region[0], best_region[1], color="tab:blue", alpha=0.3, label=f"Selected Region\n{best_region[0]:.2f} - {best_region[1]:.2f} MeV")
            ax[1].set_xlabel(r"$E_{rec}$ [MeV]")
            ax[1].set_ylabel(r"R$_{\mathrm{diff}}$ [%]")
            ax[1].set_ylim(-10, max(hist_diff) + 10 if len(hist_diff[hist_diff>0])>0 else 100)
            ax[1].legend(fontsize=10, framealpha=0.6)

            # --- 2. X cut ---
            ax = axes[1, :]
            index_energy_run = (self.CDEvt_data["oec_energy"] > best_region[0]) & (self.CDEvt_data["oec_energy"] < best_region[1])
            index_energy_bkg = (self.bkg_data["oec_energy"] > best_region[0]) & (self.bkg_data["oec_energy"] < best_region[1])
            run_mask_x = index_NonSingle & index_energy_run
            bkg_mask_x = index_NonSingle_bkg & index_energy_bkg
            
            hist_pos, _ = np.histogram(self.CDEvt_data["oec_x"][run_mask_x] / 1e3, bins=bins_pos, weights=weights_run[run_mask_x])
            if np.abs(x_m) < 17: 
                index_pos_tmp = np.logical_and(bins_pos_center > (x_m - 0.5), bins_pos_center < (x_m + 0.5))
                x_expected = bins_pos_center[index_pos_tmp][np.argmax(hist_pos[index_pos_tmp])] if np.sum(hist_pos[index_pos_tmp]) > 0 else x_m
            else:
                x_expected = x_m

            hist_run, _, _ = ax[0].hist(np.abs(self.CDEvt_data["oec_x"][run_mask_x] / 1e3 - x_expected), bins=bins_diff, histtype="step", color="tab:red", weights=weights_run[run_mask_x], label=f"True X: {x_m:.2f} m\nRec. X: {x_expected:.2f} m")
            hist_bkg, _, _ = ax[0].hist(np.abs(self.bkg_data["oec_x"][bkg_mask_x] / 1e3 - x_expected), bins=bins_diff, alpha=0.3, color="tab:blue", weights=weights_bkg[bkg_mask_x])
            
            hist_diff = np.zeros_like(hist_run)
            hist_diff_err = np.zeros_like(hist_run)
            valid_idx = hist_run > 0
            hist_diff[valid_idx] = (hist_run[valid_idx] - hist_bkg[valid_idx]) / hist_run[valid_idx] * 100
            valid_err_idx = (hist_run > 0) & (hist_bkg > 0)
            hist_diff_err[valid_err_idx] = (hist_bkg[valid_err_idx] / hist_run[valid_err_idx]) * np.sqrt(1 / (hist_run[valid_err_idx] * self.living_time) + 1 / (hist_bkg[valid_err_idx] * self.bkg_living_time))
            
            ax[0].set_xlabel(r"$\Delta$X [m]")
            if np.any(hist_run > 0): ax[0].set_yscale("log")
            ax[0].legend(fontsize=10, framealpha=0.6)

            ax[1].errorbar(bins_diff_center, hist_diff, yerr=hist_diff_err, color="tab:orange", capsize=3, marker="o", mfc="None", markersize=2)
            RD_threshold = np.mean(hist_diff)
            scan_result = HistBasedLimitFinding(x_values=bins_diff_center, y_values=hist_diff, threshold=RD_threshold, direction="right", start_point=None)
            x_limit = scan_result[1]
            
            ax[1].axhline(RD_threshold, ls="--", color="tab:red", label=fr"R$_{{\mathrm{{diff}}}}$ = {RD_threshold:.0f} %", zorder=10, lw=2)
            ax[1].axvspan(0, x_limit, color="tab:blue", alpha=0.3, label=f"Selected Region\n0 - {x_limit:.2f} m")
            ax[1].set_xlabel(r"$\Delta$X [m]")
            ax[1].set_ylabel(r"R$_{\mathrm{diff}}$ [%]")
            ax[1].set_ylim(-10, max(hist_diff) + 10 if len(hist_diff[hist_diff>0])>0 else 100)
            ax[1].legend(fontsize=10, framealpha=0.6)

            # --- 3. Y cut ---
            ax = axes[2, :]
            index_x_run = np.abs(self.CDEvt_data["oec_x"]/1e3 - x_expected) <= x_limit
            index_x_bkg = np.abs(self.bkg_data["oec_x"]/1e3 - x_expected) <= x_limit
            run_mask_y = run_mask_x & index_x_run
            bkg_mask_y = bkg_mask_x & index_x_bkg
            
            hist_pos, _ = np.histogram(self.CDEvt_data["oec_y"][run_mask_y] / 1e3, bins=bins_pos, weights=weights_run[run_mask_y])
            if np.abs(y_m) < 17: 
                index_pos_tmp = np.logical_and(bins_pos_center > (y_m - 0.5), bins_pos_center < (y_m + 0.5))
                y_expected = bins_pos_center[index_pos_tmp][np.argmax(hist_pos[index_pos_tmp])] if np.sum(hist_pos[index_pos_tmp]) > 0 else y_m
            else:
                y_expected = y_m

            hist_run, _, _ = ax[0].hist(np.abs(self.CDEvt_data["oec_y"][run_mask_y] / 1e3 - y_expected), bins=bins_diff, histtype="step", color="tab:red", weights=weights_run[run_mask_y], label=f"True Y: {y_m:.2f} m\nRec. Y: {y_expected:.2f} m")
            hist_bkg, _, _ = ax[0].hist(np.abs(self.bkg_data["oec_y"][bkg_mask_y] / 1e3 - y_expected), bins=bins_diff, alpha=0.3, color="tab:blue", weights=weights_bkg[bkg_mask_y])
            
            hist_diff = np.zeros_like(hist_run)
            hist_diff_err = np.zeros_like(hist_run)
            valid_idx = hist_run > 0
            hist_diff[valid_idx] = (hist_run[valid_idx] - hist_bkg[valid_idx]) / hist_run[valid_idx] * 100
            valid_err_idx = (hist_run > 0) & (hist_bkg > 0)
            hist_diff_err[valid_err_idx] = (hist_bkg[valid_err_idx] / hist_run[valid_err_idx]) * np.sqrt(1 / (hist_run[valid_err_idx] * self.living_time) + 1 / (hist_bkg[valid_err_idx] * self.bkg_living_time))
            
            ax[0].set_xlabel(r"$\Delta$Y [m]")
            if np.any(hist_run > 0): ax[0].set_yscale("log")
            ax[0].legend(fontsize=10, framealpha=0.6)

            ax[1].errorbar(bins_diff_center, hist_diff, yerr=hist_diff_err, color="tab:orange", capsize=3, marker="o", mfc="None", markersize=2)
            RD_threshold = np.mean(hist_diff)
            scan_result = HistBasedLimitFinding(x_values=bins_diff_center, y_values=hist_diff, threshold=RD_threshold, direction="right", start_point=None)
            y_limit = scan_result[1]
            
            ax[1].axhline(RD_threshold, ls="--", color="tab:red", label=fr"R$_{{\mathrm{{diff}}}}$ = {RD_threshold:.0f} %", zorder=10, lw=2)
            ax[1].axvspan(0, y_limit, color="tab:blue", alpha=0.3, label=f"Selected Region\n0 - {y_limit:.2f} m")
            ax[1].set_xlabel(r"$\Delta$Y [m]")
            ax[1].set_ylabel(r"R$_{\mathrm{diff}}$ [%]")
            ax[1].set_ylim(-10, max(hist_diff) + 10 if len(hist_diff[hist_diff>0])>0 else 100)
            ax[1].legend(fontsize=10, framealpha=0.6)

            # --- 4. Z cut ---
            ax = axes[3, :]
            index_y_run = np.abs(self.CDEvt_data["oec_y"]/1e3 - y_expected) <= y_limit
            index_y_bkg = np.abs(self.bkg_data["oec_y"]/1e3 - y_expected) <= y_limit
            run_mask_z = run_mask_y & index_y_run
            bkg_mask_z = bkg_mask_y & index_y_bkg
            
            hist_pos, _ = np.histogram(self.CDEvt_data["oec_z"][run_mask_z] / 1e3, bins=bins_pos, weights=weights_run[run_mask_z])
            if np.abs(z_m) < 17: 
                index_pos_tmp = np.logical_and(bins_pos_center > (z_m - 0.5), bins_pos_center < (z_m + 0.5))
                z_expected = bins_pos_center[index_pos_tmp][np.argmax(hist_pos[index_pos_tmp])] if np.sum(hist_pos[index_pos_tmp]) > 0 else z_m
            else:
                z_expected = z_m

            hist_run, _, _ = ax[0].hist(np.abs(self.CDEvt_data["oec_z"][run_mask_z] / 1e3 - z_expected), bins=bins_diff, histtype="step", color="tab:red", weights=weights_run[run_mask_z], label=f"True Z: {z_m:.2f} m\nRec. Z: {z_expected:.2f} m")
            hist_bkg, _, _ = ax[0].hist(np.abs(self.bkg_data["oec_z"][bkg_mask_z] / 1e3 - z_expected), bins=bins_diff, alpha=0.3, color="tab:blue", weights=weights_bkg[bkg_mask_z])
            
            hist_diff = np.zeros_like(hist_run)
            hist_diff_err = np.zeros_like(hist_run)
            valid_idx = hist_run > 0
            hist_diff[valid_idx] = (hist_run[valid_idx] - hist_bkg[valid_idx]) / hist_run[valid_idx] * 100
            valid_err_idx = (hist_run > 0) & (hist_bkg > 0)
            hist_diff_err[valid_err_idx] = (hist_bkg[valid_err_idx] / hist_run[valid_err_idx]) * np.sqrt(1 / (hist_run[valid_err_idx] * self.living_time) + 1 / (hist_bkg[valid_err_idx] * self.bkg_living_time))
            
            ax[0].set_xlabel(r"$\Delta$Z [m]")
            if np.any(hist_run > 0): ax[0].set_yscale("log")
            ax[0].legend(fontsize=10, framealpha=0.6)

            ax[1].errorbar(bins_diff_center, hist_diff, yerr=hist_diff_err, color="tab:orange", capsize=3, marker="o", mfc="None", markersize=2)
            RD_threshold = np.mean(hist_diff)
            scan_result = HistBasedLimitFinding(x_values=bins_diff_center, y_values=hist_diff, threshold=RD_threshold, direction="right", start_point=None)
            z_limit = scan_result[1]
            
            ax[1].axhline(RD_threshold, ls="--", color="tab:red", label=fr"R$_{{\mathrm{{diff}}}}$ = {RD_threshold:.0f} %", zorder=10, lw=2)
            ax[1].axvspan(0, z_limit, color="tab:blue", alpha=0.3, label=f"Selected Region\n0 - {z_limit:.2f} m")
            ax[1].set_xlabel(r"$\Delta$Z [m]")
            ax[1].set_ylabel(r"R$_{\mathrm{diff}}$ [%]")
            ax[1].set_ylim(-10, max(hist_diff) + 10 if len(hist_diff[hist_diff>0])>0 else 100)
            ax[1].legend(fontsize=10, framealpha=0.6)

            # --- 保存标准 cut ---
            self.fv_cuts['energy'] = best_region
            self.fv_cuts['x'] = [x_expected, x_limit]
            self.fv_cuts['y'] = [y_expected, y_limit]
            self.fv_cuts['z'] = [z_expected, z_limit]
            
            label_pos = f"({x_m*100:.0f}, {y_m*100:.0f}, {z_m*100:.0f}) cm"
            plt.suptitle(f"RUN{self.run_id}: {label_pos}", y=0.98)
            plt.tight_layout()
            
            if output_pdf:
                pdf.savefig(fig)
                pdf.close()
                print(f"✅ 标准 FV优化图已保存: {self.select_result_path}/xyz_distribution_RUN{self.run_id}.pdf")
            plt.close()
            
        except Exception as e:
            print(f"❌ 关联事例 FV优化失败: {e}")
            if output_pdf and 'pdf' in locals(): pdf.close()
            raise e
    
    def apply_fv_selection(self):
        """应用FV选择 (计算生成 efv_index 供主程序和关联分析使用)"""
        if not self.fv_cuts:
            self.optimize_fv_cuts()
            
        print(f"🎯 应用RUN {self.run_id}的宏观FV选择...")
        
        # 统一使用关联分析算出的标准cut
        if 'energy' in self.fv_cuts:
            energy_cut = self.fv_cuts['energy']
            x_center, x_cut = self.fv_cuts['x']
            y_center, y_cut = self.fv_cuts['y']
            z_center, z_cut = self.fv_cuts['z']
        else:
            print("⚠️ 未找到任何有效的切割条件")
            return None
        
        if x_cut <= 0 or y_cut <= 0 or z_cut <= 0:
            index_ellipse = np.zeros_like(self.CDEvt_data["oec_energy"], dtype=bool)
        else:
            x_scale = ((self.CDEvt_data["oec_x"] / 1e3 - x_center) / x_cut)**2
            y_scale = ((self.CDEvt_data["oec_y"] / 1e3 - y_center) / y_cut)**2
            z_scale = ((self.CDEvt_data["oec_z"] / 1e3 - z_center) / z_cut)**2
            index_ellipse = (x_scale + y_scale + z_scale) <= 1
            
        index_MuonVeto = self.CDEvt_data["MuonVeto"] == True
        index_energy = (self.CDEvt_data["oec_energy"] > energy_cut[0]) & (self.CDEvt_data["oec_energy"] < energy_cut[1])
        
        self.efv_index = ~index_MuonVeto & index_ellipse & index_energy
        
        total_events = len(self.CDEvt_data["oec_energy"])
        after_fv_events = np.sum(self.efv_index)
        efficiency = after_fv_events / total_events * 100 if total_events > 0 else 0
        
        print(f"✅ FV选择应用完成 (总数: {total_events}, 挑选后: {after_fv_events}, 效率: {efficiency:.2f}%)")
        return self.efv_index
    
    def save_fv_cuts(self):
        if not self.fv_cuts: return
        output_file = f"{self.select_result_path}/fv_cuts_RUN{self.run_id}.npz"
        np.savez(output_file, **self.fv_cuts)
        print(f"✅ FV切割条件已保存: {output_file}")
    
    def load_fv_cuts(self):
        input_file = f"{self.select_result_path}/fv_cuts_RUN{self.run_id}.npz"
        if os.path.exists(input_file):
            self.fv_cuts = dict(np.load(input_file, allow_pickle=True))
            return True
        return False
    
    def get_fv_statistics(self):
        if self.efv_index is None: return None
        total_events = len(self.CDEvt_data["oec_energy"])
        return {
            'run_id': self.run_id, 'total_events': total_events,
            'after_fv_events': np.sum(self.efv_index),
            'efficiency': np.sum(self.efv_index) / total_events * 100 if total_events > 0 else 0,
            'fv_cuts': self.fv_cuts
        }