# -----------------------------------------------------------------------------
# Program: base_analyzer.py
# Author: Shubing Liu <liusb@ihep.ac.cn>
# Created: 2025-01-11
# Description: Base analyzer handling data loading from NPZ files
# -----------------------------------------------------------------------------

import numpy as np
import pandas as pd
import os
import matplotlib
matplotlib.use('Agg') # Ensure headless running
from matplotlib import pyplot as plt
from config_manager import AnalysisConfig
from bkg_loader import BKGLoader

import scienceplots
plt.style.use(["science", "grid", "no-latex"])
plt.rcParams["figure.dpi"] = 300

class BaseAnalyzer:
    def __init__(self, config: AnalysisConfig, run_id: int):
        self.config = config
        self.run_id = run_id
        self.data_loaded = False
        
        # 初始化BKG加载器
        self.bkg_loader = BKGLoader(config)
        
        # 运行信息 (将在 load_run_info 中填充)
        self.run_info_dict = None
        self.df_run_info = None 
        self.run_position = {'X': 0, 'Y': 0, 'Z': 0}
        
    def set_run_info(self, info_dict):
        """手动设置RUN信息 (由test.py传入)"""
        self.run_info_dict = info_dict
        if info_dict:
            self.run_position = {
                'X': info_dict.get('X(cm)', 0),
                'Y': info_dict.get('Y(cm)', 0),
                'Z': info_dict.get('Z(cm)', 0)
            }
            # 构建 DataFrame 模拟旧接口
            self.df_run_info = pd.DataFrame([info_dict])
            self.df_run_info.set_index("RUN", inplace=True)

    def _get_npz_path(self, run):
        return f"{self.config.input_data_path}/RUN{run}.npz"
    
    def load_data(self):
        """加载单个RUN的数据 (直接从 CombinedNPZ 读取)"""
        try:
            file_path = self._get_npz_path(self.run_id)
            
            if not os.path.exists(file_path):
                print(f"❌ 数据文件不存在: {file_path}")
                return False
            
            # 加载数据
            print(f"📂 Loading: {file_path}")
            raw_data = dict(np.load(file_path, allow_pickle=True))
            
            # 提取 LivingTime
            if 'LivingTime' in raw_data:
                # 处理标量或单元素数组
                lt = raw_data['LivingTime']
                self.living_time = float(lt) if np.ndim(lt)==0 else float(lt[0])
            else:
                print("⚠️ Warning: LivingTime not found in file, set to 1.0s")
                self.living_time = 1.0
                
            self.CDEvt_data = raw_data
            
            # 键名映射：CorrelationAnalyzer 代码里使用了 oec_x, oec_energy 等名称
            # 但 CombinedNPZ 里的可能是 omilrec_x, omilrec_energy
            # 这里做自动映射
            vertex_keys = self.config.get_vertex_keys()
            
            for std_key, file_key in vertex_keys.items():
                target_key = f"oec_{std_key}" # e.g., oec_x
                if file_key in self.CDEvt_data:
                    self.CDEvt_data[target_key] = self.CDEvt_data[file_key]
                else:
                    print(f"⚠️ Key mapping failed: {file_key} not found in NPZ.")

            # 加载本底数据
            self.bkg_data = self.bkg_loader.get_bkg_data()
            self.bkg_living_time = self.bkg_loader.get_bkg_living_time()
            
            self.data_loaded = True
            
            evt_count = len(self.CDEvt_data['global_time_s'])
            print(f"✅ RUN {self.run_id} 加载完成 (Events: {evt_count}, LiveTime: {self.living_time:.2f}s)")
            return True
            
        except Exception as e:
            print(f"❌ RUN {self.run_id} 数据加载失败: {e}")
            import traceback
            traceback.print_exc()
            self.data_loaded = False
            return False
            
    def get_run_info(self):
        return self.df_run_info.loc[self.run_id] if self.df_run_info is not None else None