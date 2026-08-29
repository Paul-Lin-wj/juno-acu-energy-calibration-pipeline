按**当前默认配置**（开 Gamma + B12 + C11 + C10），最小可编译、可运行清单如下。源目录：

`/lustrefs/juno26/users/zhaorz/Calib/fitter_EnergyNL_DYBmodel`

---

## 必须复制

### 1. 编译相关（整目录/文件）

```
Makefile
run.sh
include/          # 全部 .h（不要漏）
src/*.cxx         # 只要顶层的 22 个 .cxx，不要 src/backup/
```

`src/` 里**不要**拷：`backup/`、`*.cxx_bak`、`test.C`

### 2. 运行时输入（当前开关需要的）

```
necessaryfiles/input/Quenching.root                          # ~364MB，最大
necessaryfiles/input/cerenkovCurve_2018.dat
necessaryfiles/input/Gamma_Electron.root                     # gamma peak PDF
necessaryfiles/input/JUNO/ReProd26B/gamma_AllPhase.dat
necessaryfiles/input/JUNO/ReProd26B/Spec/forNLfitter/Isotope_data_AllPhase_FVcutR0_1720_Finalcorrection.root
necessaryfiles/input/JUNO/ReProd26B/predSpec_fromChengzhuo_IHEP/forNLfitter/
    12B_pure_beta_0_20MeV_80bins.root
    12N_pure_beta_0_20MeV_80bins.root
    11C_pure_beta_0_4MeV_200bins.root
    10C_pure_beta_0_4MeV_80bins.root
    11C_pure_beta_0_4MeV_80bins.root
    11Be_pure_beta_0_4MeV_80bins.root
```

路径相对关系必须保持和上面一致。

### 3. 本地建空目录（不用拷内容）

```bash
mkdir -p obj
mkdir -p output/{results,curves,errors,gammas}
mkdir -p plots/JUNO/26B
```

---

## 不用复制

`analysis/`、`ErrorBand/`、`genPullCurve/`、`NLGenerator/`、`SpNIBD/`、`share/`、`backup/`、`Hist_*.root`、`ibdFile.root`、已编译的 `fitter`、`obj/`、`output/`、`plots/` 里的旧结果。

---

## 示例（你自己改目标路径）

```bash
SRC=/lustrefs/juno26/users/zhaorz/Calib/fitter_EnergyNL_DYBmodel
DST=/你的目标目录

mkdir -p "$DST"/{include,src,obj,output/{results,curves,errors,gammas},plots/JUNO/26B}
mkdir -p "$DST"/necessaryfiles/input/JUNO/ReProd26B/{Spec/forNLfitter,predSpec_fromChengzhuo_IHEP/forNLfitter}

cp "$SRC"/Makefile "$SRC"/run.sh "$DST"/
cp "$SRC"/include/*.h "$DST"/include/
cp "$SRC"/src/*.cxx "$DST"/src/

cp "$SRC"/necessaryfiles/input/Quenching.root "$DST"/necessaryfiles/input/
cp "$SRC"/necessaryfiles/input/cerenkovCurve_2018.dat "$DST"/necessaryfiles/input/
cp "$SRC"/necessaryfiles/input/Gamma_Electron.root "$DST"/necessaryfiles/input/
cp "$SRC"/necessaryfiles/input/JUNO/ReProd26B/gamma_AllPhase.dat \
   "$DST"/necessaryfiles/input/JUNO/ReProd26B/
cp "$SRC"/necessaryfiles/input/JUNO/ReProd26B/Spec/forNLfitter/Isotope_data_AllPhase_FVcutR0_1720_Finalcorrection.root \
   "$DST"/necessaryfiles/input/JUNO/ReProd26B/Spec/forNLfitter/
cp "$SRC"/necessaryfiles/input/JUNO/ReProd26B/predSpec_fromChengzhuo_IHEP/forNLfitter/*.root \
   "$DST"/necessaryfiles/input/JUNO/ReProd26B/predSpec_fromChengzhuo_IHEP/forNLfitter/
```

然后：

```bash
/cvmfs/container.ihep.ac.cn/bin/hep_container shell SL6 -g dyw
cd /你的目标目录
./run.sh
```

若以后打开 K40/Bi/Tl/LS/FADC 等开关，还要再拷对应的 `necessaryfiles/input/*.root` / `.dat`；当前默认不用。


[luxiaoying@lxlogin008 fitter_energynl_dybmodel]$ cp -r /lustrefs/juno26/users/zhaorz/Calib/fitter_EnergyNL_DYBmodel/necessaryfiles/input/theo/ necessaryfiles/input/
[luxiaoying@lxlogin008 fitter_energynl_dybmodel]$ cp /lustrefs/juno26/users/zhaorz/Calib/fitter_EnergyNL_DYBmodel/necessaryfiles/input/LS_LBNL_2015_short.dat necessaryfiles/input/
[luxiaoying@lxlogin008 fitter_energynl_dybmodel]$ cp /lustrefs/juno26/users/zhaorz/Calib/fitter_EnergyNL_DYBmodel/necessaryfiles/input/LS_IHEP.dat necessaryfiles/input/
[luxiaoying@lxlogin008 fitter_energynl_dybmodel]$ cp /lustrefs/juno26/users/zhaorz/Calib/fitter_EnergyNL_DYBmodel/necessaryfiles/input/FADC_scaleNL.txt necessaryfiles/input/