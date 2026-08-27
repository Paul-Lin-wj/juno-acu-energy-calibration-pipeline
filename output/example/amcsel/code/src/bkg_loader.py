# -----------------------------------------------------------------------------
# Program: bkg_loader.py
# Author: Shubing Liu <liusb@ihep.ac.cn>
# Created: 2025-01-11
# Description: Simplified Background Loader for NPZ files
# -----------------------------------------------------------------------------

import numpy as np
import os
from config_manager import AnalysisConfig

class BKGLoader:
    """BKG数据加载器 - 单例模式"""
    _instance = None
    _bkg_data = None
    _bkg_living_time = 0
    _loaded_run = None
    _config = None
    
    def __new__(cls, config: AnalysisConfig):
        if cls._instance is None:
            cls._instance = super(BKGLoader, cls).__new__(cls)
            cls._config = config
        return cls._instance
    
    def get_bkg_data(self):
        """获取BKG数据，如果RUN变了或没加载，则加载"""
        target_bkg_run = self._config.BKG_run
        
        # 懒加载：只有当本底RUN改变或未加载时才读取文件
        if self._bkg_data is None or self._loaded_run != target_bkg_run:
            self._load_bkg_data(target_bkg_run)
            
        return self._bkg_data
    
    def get_bkg_living_time(self):
        return self._bkg_living_time
    
    def _load_bkg_data(self, run_id):
        """加载指定 RUN 的 BKG 数据"""
        file_path = f"{self._config.input_data_path}/RUN{run_id}.npz"
        print(f"🔄 加载本底 RUN {run_id} ...")
        
        if not os.path.exists(file_path):
            print(f"❌ BKG文件不存在: {file_path}")
            # 返回空结构防止崩溃
            self._bkg_data = {'oec_energy': [], 'oec_x': [], 'oec_y': [], 'oec_z': []}
            self._bkg_living_time = 1.0
            return

        try:
            data = dict(np.load(file_path, allow_pickle=True))
            
            # 处理 LivingTime
            if 'LivingTime' in data:
                lt = data['LivingTime']
                self._bkg_living_time = float(lt) if np.ndim(lt)==0 else float(lt[0])
            else:
                self._bkg_living_time = 1.0
                
            # 键名映射 (适配 correlation_analyzer 的 oec_ 前缀)
            vertex_keys = self._config.get_vertex_keys()
            for std_key, file_key in vertex_keys.items():
                target_key = f"oec_{std_key}"
                if file_key in data:
                    data[target_key] = data[file_key]
            
            self._bkg_data = data
            self._loaded_run = run_id
            print(f"✅ BKG RUN {run_id} 加载成功 (活时间: {self._bkg_living_time:.2f} s)")
            
        except Exception as e:
            print(f"❌ BKG加载失败: {e}")
            self._bkg_data = {}
            self._bkg_living_time = 1.0

    # 兼容旧接口
    @classmethod
    def get_bkg_dn_data(cls):
        return {} 
        
    def get_bkg_event_rate(self, key='totalPE'):
        return 0