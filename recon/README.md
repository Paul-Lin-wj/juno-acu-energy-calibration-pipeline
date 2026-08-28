# recon — Stage −1: rtraw → ESD 本地重建

刻度能标定链的最上游可选段：把 DAQ 的 rtraw 原始数据用**官方 junosw 重建链**
（CVMFS J26.1.1 的 `tut_rtraw2rec.py`：waverec 波形刻度 + OEC + mixedphase +
jvertex + OMILREC 顶点/能量）重建成 ESD，供 calibsel Stage 0（MySimpleTag）消费。

**本模块是纯编排**：一行重建代码都没有。`--impl` 决定 OMILREC 用哪个实现：

| impl | 说明 |
|---|---|
| `omilrecv2`（默认） | 叠加优化版 OMILRECV2 overlay（`../omilrec_opt/omilrecv2`，~8× 提速；与基线差 ≤55 keV/150 mm，非逐位一致） |
| `baseline` | CVMFS J26.1.1 官方基线 OMILREC（"官方 junosw"答案） |

不开启本模块（默认）时，calibsel 直接读生产 ReProd26B ESD——行为与引入本模块前完全一致。

## 用法

```bash
# 冒烟级（1 个 rtraw 文件 × 100 事例）
bash run_pipeline.sh                                  # 默认 10110
bash run_pipeline.sh 10110 --impl baseline

# 全量 run（10110 有 297 个 rtraw 文件）
bash run_pipeline.sh 10110 --slice 297 --evtmax -1

# 套件联合跑（driver 默认关；环境变量开启）
RECON_IMPL=omilrecv2 bash ../run_pipeline.sh 12370
```

无需 venv：编排脚本仅标准库；重建在生成的 bash wrapper 内用 CVMFS python 跑。

## 输出布局

```
output/<ts>/
├── results/esd/RUN<N>/recon_RUN<N>.root   # ESD（含 Event/CdVertexRecOMILREC）
├── results/esd_lists/esd_list_<N>.txt     # 衔接清单 → calibsel --esd-list-dir
├── logs/  _work/  code/  config_snapshot.json  run_log.md/.json
```

每个 run 的 stages：`-1pre` 四件套 map/PDF sha256 校验 → `-1a` rtraw 清单
（EOS xrootd：DAQ 按日期档 `/eos/juno/rtraw/<YYYY>/<MMDD>/`，回退精选区
`/eos/juno/juno-rtraw/<VER>/…`）→ `-1b` 重建 + 产物校验（CdVertexRecOMILREC
事例数 >0）→ handoff 写 esd_list。

## 前置条件（一次性）

- CVMFS J26.1.1（本机盘 `/cvmfs/juno.ihep.ac.cn/el9_amd64_gcc11/Release/J26.1.1/`）
- omilrecv2 已在其目录内构建（`InstallArea/setup.sh` 存在；重建方法见其 README）
- map/PDF 四件套在 `/data/juno/dingxf/OMILREC_maps/`（sha256 锁定于 config/paths.py，
  与 `/data/juno/dingxf/inputs/` 样例输入一并由 v1.0-postv107-gated 包校验过）
- calibsel 侧：本地编译的 JUNOSW_MyAlgz（`../JUNOSW_MyAlgz`，calibsel paths.py 自动优先）

## 已知口径问题（重要）

冻结的 global tag 是 **ReProd26A_v1**（同事跑法的原值），而当前 calibsel 默认吃的
生产 ESD 是 **ReProd26B** 产物。本地重建结果与 26B 生产 ESD 之间的差异尚未量化
（同一切片对比实验待做；或向 Shubing Liu 确认 26B 对应 tag/steering）。
对齐前，**本地重建输出的物理数字不与生产数字混用**。

详见 [PROVENANCE.md](PROVENANCE.md)。
