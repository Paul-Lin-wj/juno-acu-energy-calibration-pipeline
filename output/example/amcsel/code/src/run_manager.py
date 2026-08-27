# -----------------------------------------------------------------------------
# Program: run_manager.py
# Author: Shubing Liu <liusb@ihep.ac.cn>
# Created: 2025-01-11
# Description: Manages run metadata lookup (Source, BKG, Position)
# -----------------------------------------------------------------------------

import pandas as pd
import numpy as np
import os
import sys
from config_manager import AnalysisConfig

class RunManager:
    def __init__(self, config: AnalysisConfig):
        self.config = config
        self.df_run_pos = None
        self._load_position_db()
        # 模拟旧代码的 df_run_info，用于兼容性
        self.df_run_info = pd.DataFrame() 
        
    def _load_position_db(self):
        """加载位置信息数据库 (CalibRUN.csv)"""
        if os.path.exists(self.config.calib_pos_file):
            try:
                self.df_run_pos = pd.read_csv(self.config.calib_pos_file)
            except Exception as e:
                print(f"Warning: Failed to load position file: {e}")
        else:
            print(f"Warning: Position file not found: {self.config.calib_pos_file}")

    def get_run_config(self, target_run):
        """
        从 calib_to_analyze.txt 获取 Source 和 PhysicsRun
        格式: Source,StartRun-EndRun,PhysicsRun
        """
        if not os.path.exists(self.config.calib_info_file):
            print(f"Error: Config file not found at {self.config.calib_info_file}")
            sys.exit(1)

        source_found = None
        bkg_run_found = None

        with open(self.config.calib_info_file, 'r') as f:
            lines = f.readlines()
            
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'): continue
            
            parts = line.split(',')
            if len(parts) < 2: continue
            
            src = parts[0].strip()
            run_range = parts[1].strip()
            
            try:
                # 解析范围 10858-10862 或 单个 run 9593
                if '-' in run_range:
                    start_r, end_r = map(int, run_range.split('-'))
                else:
                    start_r = int(run_range)
                    end_r = int(run_range)
                    
                if start_r <= target_run <= end_r:
                    source_found = src
                    # Check for Physics Run (第三列)
                    if len(parts) >= 3:
                        try:
                            bkg_run_found = int(parts[2].strip())
                        except ValueError:
                            pass
                    break
            except ValueError:
                continue
                
        return source_found, bkg_run_found

    def get_run_info(self, run_id):
        """获取完整的 RUN 信息字典，包括位置"""
        source, bkg_run = self.get_run_config(run_id)
        
        if source is None:
            return None
            
        # 默认位置 (0,0,0)
        pos_info = {'X[m]': 0.0, 'Y[m]': 0.0, 'Z[m]': 0.0, 'Date': 'Unknown'}
        
        # 查找位置信息
        if self.df_run_pos is not None:
            row = self.df_run_pos[self.df_run_pos["RUN"] == run_id]
            if not row.empty:
                pos_info['X[m]'] = row["X[m]"].values[0]
                pos_info['Y[m]'] = row["Y[m]"].values[0]
                pos_info['Z[m]'] = row["Z[m]"].values[0]
                if "Date" in row.columns:
                    pos_info['Date'] = row["Date"].values[0]

        # 构造信息字典
        info_dict = {
            "RUN": run_id,
            "Source": source,
            "BKG_RUN": bkg_run,
            # 将米转换为厘米，适配下游代码习惯
            "X(cm)": pos_info['X[m]'] * 100, 
            "Y(cm)": pos_info['Y[m]'] * 100,
            "Z(cm)": pos_info['Z[m]'] * 100,
            "Date": pos_info['Date']
        }
        
        # 更新内部 DataFrame 缓存 (为了兼容 base_analyzer 中可能的调用)
        self.df_run_info = pd.DataFrame([info_dict])
        self.df_run_info.set_index("RUN", inplace=True)
        
        return info_dict