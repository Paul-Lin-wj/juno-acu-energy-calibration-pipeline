---
name: calib-run-timeline
description: Draw the JUNO ACU calibration run-vs-date inventory figures (取数时间线/z-scan 覆盖/取数节奏) with the standardized convention — fixed source colours/markers, ValProd26B phase bands, centre-run encoding, Times-like serif fonts, out-of-data legends, png+pdf dual output. Use when asked to "画 run vs date 的图", "刻度取数时间线", "calibration data-taking timeline", "z-scan coverage", "取数节奏/日程图", "which runs were taken in which phase", or before publishing/reporting any figure that maps calibration runs onto dates.
---

# Calibration run inventory figures（run vs date 规范画法）

三张套图的标准画法。**第一选择永远是跑参考脚本**，不要徒手重画——规范的价值
就在于跨用户跨版本可比：

```bash
calibsel/.venv/bin/python calibsel/tools/plot_run_inventory.py \
    [--out-dir DIR] [--figs all|1,2,3] [--centre-z 0.5]
```

只有当脚本确实不满足需求（新维度、新数据源）时才扩展，且扩展必须遵守下面的
约定并回写脚本/本文件。

## 输入（唯一事实源，勿手工誊抄）

| 数据 | 路径 | 用途 |
|---|---|---|
| run 清单 | `calibsel/calib_run_info/CalibRUN_from_file.csv`（RUN, Date, X/Y/Z[m], Source, R[m]） | 全部三张图 |
| phase 区间 | `calibsel/input/correction/data/ValProd26BPhase.csv`（run 号区间 P1–P4） | phase 色带 |
| 分析批次 | `calibsel/calib_run_info/calib_to_analyze.txt` | （可选）标注分析目标 |

## 方法约定（fig1：run vs date 时间线）

1. **x = 日期**（`%Y-%m` 月刻度，45° 旋转）；**y = 刻度源**，按标称能量排序：
   Cs137 0.662 → Mn54 0.835 → Ge68 2×511 → Co60 1.17/1.33 → K40 1.461 →
   AmC 2.22/4.94/6.13（y 刻度标签带能量）。
2. **源的颜色+符号固定**（跨图跨用户一致，禁止自选）：
   Cs137 蓝`o`、Mn54 橙`s`、Ge68 绿`^`、Co60 红`D`、K40 紫`*`、AmC 棕`v`。
3. **实心 = 中心 run（|z|≤0.5 m，与生产 AllPhase 对比口径一致），空心 = z 扫描点**；
   同日多 run 用**确定性 jitter**（`((run*2654435761)%1000)/1000*0.26-0.13`，
   禁用随机数）。
4. **phase 色带**：由 ValProd26BPhase.csv 的 run 区间 × run↔date 单调映射得出；
   边界取相邻两 phase 取数空窗的**中点**；灰/蓝交替底纹；顶部标 P1…P4，
   区间前的 run 标 **pre-P1**（26B 修正按就近 phase 归并，需在图注说明）。
5. 右缘逐源标注 `n runs / k centre`。

## 样式约定（三张图通用，禁止削弱）

- **字体**：Times 系衬线——`font.serif = ["Nimbus Roman", "Liberation Serif",
  "Times New Roman", "DejaVu Serif"]` + `mathtext.fontset="stix"`（本机无
  TNR 本体时 Nimbus Roman 是 metric 兼容替身；勿退回 DejaVu sans）。
- **字号下限**：tick ≥12、轴标签 ≥15、标题 ≥16、legend ≥12；`savefig.dpi=200`；
  宽幅 `figsize≈(15, 6)`。
- **legend 必须在数据区外**（`fig.legend(loc="outside lower center", ncols=…)`，
  需 `layout="constrained"`）；绝不压在散点上。
- **双格式输出**：同名 `.png`（看屏）+ `.pdf`（幻灯/打印）。
- 顶部 phase 标签、球边界虚线（fig2 的 ±17.7 m）等注释不得与数据重叠。

## 变体

- **fig2 z-scan 覆盖**：y=源 z 位置，虚线标亚克力球 ±17.7 m（Ge68 会越过球顶，
  属真实取数）。
- **fig3 取数节奏**：按日按源堆叠 + 右轴累计线。
- 单相/子区间版：加 run 过滤后同样式；**颜色/符号映射不得改**。

## 交付前自查

- [ ] 三源输入来自上表路径，未手抄数字
- [ ] 颜色/符号/能量序与约定一致；实心空心语义正确
- [ ] phase 带边界落在取数空窗中点；pre-P1 有标注
- [ ] legend 在数据区外；无字体重叠/截断；字号达标
- [ ] png+pdf 成对产出；报告引用时注明 run 总数与时间范围
