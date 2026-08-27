# dybmodel 运行容器（一比一自备副本）

Stage 6 在**原版 SL6 容器**里跑原版（未修改）的 `fitter_energynl_dybmodel`。
本目录与 `/datafs` 上的资产使流水线**不依赖** `container.ihep.ac.cn` 与任何登录节点。

## 资产（不入库，`tools/setup_container.sh` 一键布防）

| 资产 | 大小 | 位置（`/datafs/users/wujxy/containers/dybmodel-sl6/`） | 说明 |
| --- | --- | --- | --- |
| `sl69worknode20240820.sif` | 3.6 GB | 根目录 | IHEP 官方 SL6 工作节点镜像的**字节级副本**（`hep_container` 的 SL6 即它） |
| `rootfs/` | ~11 GB 解压 | 根目录 | SIF 的 unsquashfs 解包，运行时作为 apptainer 沙箱（本机无 setuid starter → `--userns` + 目录沙箱） |
| `juno-sl6-amd64-gcc447/Release/J17v1r1` | 3.0 GB | 根目录 | ROOT 5.34.11 时代 JUNO release；**文本** setup 脚本的 `/cvmfs/...` 前缀已改写到本目录（二进制不动） |

已知差异：J17v1r1 里 11 个 Geant4 `PhotonEvaporation` 数据文件因 cvmfs 权限
（拷贝账号无读权限）未能复制——与 dybmodel 运行无关（拟合只用 ROOT5/Minuit）。

## 为什么 J17 放在 /datafs 而不是 /cvmfs

- 本类节点上宿主的 `/cvmfs/juno.ihep.ac.cn` 其实是 **publicfs 磁盘伪装**
  （fstab 直挂），没有 sl6 内容；无特权（userns）容器**无法遮盖继承挂载**。
- 容器内**凡是与 cvmfs 仓库名同名的目录**（如 `juno.ihep.ac.cn`）会被宿主仓库
  自动挂载盖掉——所以暂存目录刻意避开仓库名（`juno-sl6-amd64-gcc447`）。

## 运行时两个必要细节（wrap 已内置）

- **`ulimit -s unlimited`**：SL6 二进制（glibc 2.12）在 el9 新内核下默认
  8 MB 栈会在 MIGRAD 迭代中触发 SIGSTKFLT（退出码 144）崩溃；放开栈后正常。
- **`apptainer exec -e --userns`**：本机 apptainer 无 setuid starter，
  SIF 直跑会报 `starter-suid doesn't have setuid bit set`；
  rootfs 目录沙箱 + userns 模式即可。

## 可复现性

- `sl69worknode20240820.def`：从 SIF 内部提取（`apptainer inspect --deffile`）。
  镜像是链式构建（`from: sl69worknode20240729`），无完整 scratch 配方——
  "一模一样"由 **SHA-256 校验的字节级副本**保证（`SHA256SUMS`）。
- 行为锁定基线：原版二进制 + 本容器 + 历史 gamma 表 → 与 2026-08-16 历史
  `bestFit_*.dat` **逐字节一致**（lxlogin 官方容器与本副本均已验证）。

## 新用户布防

```bash
# 需要能 ssh 到一台挂了 container.ihep.ac.cn 的登录节点（默认 lxlogin002）
bash nlfit/tools/setup_container.sh [user@loginnode]
```

完成后 `nlfit` 的 Stage 6 自动探测使用（`config/paths.py` 里的资产路径按需调整）。
