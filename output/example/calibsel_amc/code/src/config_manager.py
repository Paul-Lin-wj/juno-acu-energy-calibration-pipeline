# -----------------------------------------------------------------------------
# Program: config_manager.py
# Author: Shubing Liu <liusb@ihep.ac.cn>
# Created: 2025-01-11
# Updated: 2026-03-18
# Description: Configuration management for Correlation Analysis
# -----------------------------------------------------------------------------

import os
from dataclasses import dataclass

@dataclass
class AnalysisConfig:
    # --- 基础路径配置 (将在 test.py 中被覆盖) ---
    input_data_path: str = "./CombinedNPZ/Data"
    calib_info_file: str = "./calib_to_analyze.txt"
    calib_pos_file: str = "./CalibRUN.csv"
    
    # --- 输出配置 ---
    output_base_dir: str = "./Results"
    timestamp_dir: str = "./Timestamp" # 修改：直接指向 Timestamp 目录
    
    # --- 算法配置 ---
    vertex_chose: str = "omilrec"  # 默认使用的顶点算法 (omilrec, mpv, jvtx...)
    
    # --- 运行时动态变量 (由程序自动填充) ---
    calib_type: str = ""      # e.g., AmC, Co60
    calib_type_short: str = ""
    BKG_run: int = 0          # 本底 RUN 号
    LS_level: str = "LSfull_25C" # 仅作为标签保留，不再用于生成目录
    
    def __post_init__(self):
        # 直接输出到 output_base_dir (现在 test.py 会传入 ./Results/RUNxxx)
        self.output_dir = self.output_base_dir
        
        # 简化路径结构，所有结果都直接放在 output_dir 下
        self.LS_info_path = self.output_dir 
        self.select_result_path = self.output_dir # 不再强制添加 /Corre_Selection
        self.save_check_path = self.output_dir
        
        # 确保目录存在
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.timestamp_dir, exist_ok=True) 
        
    def get_vertex_keys(self):
        """获取当前顶点算法对应的 npz 键名映射"""
        return {
            'x': f"{self.vertex_chose}_x",
            'y': f"{self.vertex_chose}_y",
            'z': f"{self.vertex_chose}_z",
            'energy': f"{self.vertex_chose}_energy"
        }