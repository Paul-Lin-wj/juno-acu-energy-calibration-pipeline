#!/usr/bin/env python3
"""amcsel（Stage 3c）集中配置 —— 本模块唯一需要按环境修改的文件。

数据约定（与 esd2npz 的 26B Finalcorrection 输出原生对接）：
  INPUT_DATA_DIR/RUN<N>.npz       刻度源 run（键含 omilrec_{x,y,z,energy},
                                  global_time_s, LivingTime）
  INPUT_DATA_DIR/RUN<bkg>.npz     本底 run（run 号来自 calib_to_analyze.txt
                                  第三列 PhysicsRun，esd2npz 会自动补跑）
"""
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# ---- 输入 ----
INPUT_DATA_DIR = PROJECT_ROOT / "input" / "Data"
CALIB_INFO_FILE = PROJECT_ROOT / "calib_run_info" / "calib_to_analyze.txt"
CALIB_POS_FILE = PROJECT_ROOT / "calib_run_info" / "CalibRUN_from_file.csv"

# ---- 输出 ----
OUTPUT_DIR = PROJECT_ROOT / "output"
OUTPUT_RES_DIR = "results"          # 相对每次运行的 out 目录
OUTPUT_FIG_DIR = "figures"

# ---- 以下分析参数逐字节取自 correlate_selection/test.py（2026-04-14 版）----
# 只做编排、不改数字：凡与本文件不一致者以 test.py 原值为准。
VERTEX_ALGO = "omilrec"                      # test.py §6
FV_ENERGY_REGION = [0.5, 10.0]               # test.py §8
CS137_ISOLATION_TIME = 1500                  # us, test.py §7
CS137_ENERGY_STD_CUT = 3.0                   # test.py §7
SOURCES_DO_CORRELATION = ["AmC", "AmC100", "AmC117", "AmC-Cs137",
                          "Co60", "Cf252"]    # test.py §9
SOURCES_DO_CS137 = ["AmC-Cs137", "Cs137"]

# 中子源（Am*/Cf*）与普通源的关联参数 —— test.py main() 第 5 步原值
PARAMS_NEUTRON = {
    "energy_limit": 0.5,
    "delay_region": [1.9, 5.7],
    "nH_region": [2.0, 2.4],
    "promt_region": [0.5, 12],
    "distance_limit": 1.5,
    "dt_cut": 1000,
}
PARAMS_STANDARD = {
    "energy_limit": 0.5,
    "delay_region": [1.0, 3.0],
    "promt_region": [0.5, 12],
    "distance_limit": 2.0,
    "dt_cut": 2000,
}
