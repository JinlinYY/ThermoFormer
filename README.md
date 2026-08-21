# ThermoFormer：二元/三元汽液相平衡模型

ThermoFormer 使用 Uni-Mol v2 分子表征、可配置多组分交互与可微热力学求解器建模低压 VLE。当前范围只包括二元和三元体系；LLM-Agent、四元体系与高压气相 EOS 暂不实现。

## 工程结构

```text
src/                                  # 模型、数据、训练及热力学求解器
scripts/
  train_thermoformer.py               # 统一实验运行源码
  audit_dataset.py                    # 数据审计与三元子体系覆盖
  generate_splits.py                  # 生成固定、带数据摘要的协议划分
  validate_splits.py                  # 回读并审计全部划分
  run_paper_experiment.py             # 单协议/单种子论文运行器
  run_paper_suite.py                  # 五种子实验套件
  aggregate_results.py                # mean ± std 聚合
experiments/
  README.md                           # 实验总索引
  baseline/thermoformer_base/         # 完整模型基线
  ablation/
    component/                        # 模型组件消融
    thermodynamic_loss/               # 热力学一致性 loss 消融
  comparison/                         # 对比实验
  interpolation_extrapolation/        # 内插/外推实验设计与后续结果
  explainability/                     # 可解释性实验设计与后续结果
splits/                               # 75 个固定划分 JSON（15 协议 × 5 seeds）
reports/                              # 实现、数据、划分和训练诊断审计
results/                              # 逐种子预测 CSV 与指标 JSON/CSV
figures/                              # 由结果脚本生成的 PDF/PNG 图
checkpoints/                          # 正式最佳模型（*.pt 默认不入 Git）
dataset/
  binary_vle_english.xlsx             # 二元 VLE 数据
  ternary_vle_english.xlsx            # 三元 VLE 数据
tests/                                # 回归与端到端测试
runs/experiments/                     # checkpoint、历史和机器可读结果
runs/legacy/                          # 整理前的旧运行，仅归档
environment-ggnn39.yml                # 项目 Conda 环境声明
```

`dataset/` 只保留模型实际使用的两个工作簿。训练源码与实验记录分离：可执行 Python 源码放在 `scripts/`；每个具体实验按“实验类别/子类别/实验名”组织，并在最终实验目录内保存 `config.json`、`run.md` 和 `results.md`。具体实验不得直接放在 `experiments/` 根目录。

## 开发环境

项目统一使用本地 Conda 环境 `ggnn39`：

```powershell
conda activate ggnn39
python -V
python -m unittest discover -s tests -v
```

已验证的核心版本包括 Python 3.9.25、PyTorch 2.6.0+cu126、NumPy 1.26.4、Pandas 1.5.3、OpenPyXL 3.1.5 和 `unimol-tools` 0.1.4.post1。当前 Uni-Mol 安装支持 `model_name="unimolv2"`、84M 权重和 `cls_repr` 输出。

## 数据集

- `dataset/binary_vle_english.xlsx`：23,061 条二元 VLE 原始记录；
- `dataset/ternary_vle_english.xlsx`：5,229 条三元 VLE 原始记录。

工作簿使用英文字段、工作表名和数据字典；实验值、SMILES、分子式、质量码和 DOI 保持原始含义。化学名称保留数据源写法并明确标为 `original_name`，模型以 SMILES 识别分子。

默认加载规则包括：

- °C 转换为 K，mmHg 转换为 kPa；
- 质量码 `1=通过、0=失败、-1=无法判定`；
- 失败记录默认排除，无法判定记录权重为 0.5；
- 默认只保留不高于 500 kPa 的记录，使当前修正 Raoult 方程保持在低压使用范围；
- 训练分区要求纯组分端点温度锚定。

加载器会把原始行、质量失败、SMILES 缺失、非法状态、压力过滤、去重和纯端点过滤分别计数，并写入每次运行的 `dataset_manifest.json` 与 `results.md`。若数据提供显式 `experiment_mode`，加载器优先采用；否则按同一物系、DOI 和来源内重复的温度/压力条件推断等温、等压或完整状态，并记录逐行置信度。缺少 DOI 或温度/压力证据冲突的行保守回退为 `full_state`。

## 模型输入与输出

| 输入 | 形状 | 含义 |
|---|---:|---|
| `molecules` | `[B, 3, D_uni]` | Uni-Mol v2 `cls_repr`；二元体系第三项补零 |
| `temperature_k` | `[B, 1]` | 温度，K |
| `pressure_kpa` | `[B, 1]` | 压力，kPa |
| `x` | `[B, 3]` | 液相摩尔分数 |
| `mask` | `[B, 3]` | 真实组分为 1，padding 为 0 |
| `experiment_mode` | `[B]` | 等温、等压或完整状态，用于选择泡点求解方向 |
| `pure_property_parameters` | `[B, 3, 11]` | 可选纯物性相关式类型、系数、单位换算、有效温区和可用标志 |

神经网络直接输出 `log_gamma`、学习型纯组分 `log_psat`、非理想性 token 和 `g^E/RT`。若配置了可靠 Antoine 或 DIPPR 101 参数且温度处于声明的有效范围，求解器优先使用相关式；否则回退到学习型 `P_i^sat(T)`。热力学求解器进一步输出平衡 `T/P`、`x/y`、`gamma`、`P^sat`、平衡残差、收敛标志与迭代次数。等温模式给定 `T,x` 求 `P,y`；等压模式给定 `P,x` 求 `T,y`。

可选纯物性目录通过 `data.pure_property_catalog` 指定 JSON 文件，键为标准化 SMILES。每项用 `type` 选择 `antoine` 或 `dippr101`，并明确 `pressure_unit`、`temperature_unit`、`minimum_temperature_k` 与 `maximum_temperature_k`。Antoine 采用 `log10(P)=A-B/(C+T)`；DIPPR 101 采用 `ln(P)=A+B/T+C ln(T)+D T^E`。为兼容已有目录，省略 `type` 和单位时按 Antoine、mmHg、°C 解释；默认目录留空，不伪造缺失参数。

## 实验运行与结果

实验总表位于 `experiments/README.md`。完整模型命令记录在 `experiments/baseline/thermoformer_base/run.md`，实际运行源码始终是 `scripts/train_thermoformer.py`：

```powershell
conda activate ggnn39
python scripts/train_thermoformer.py --config experiments/baseline/thermoformer_base/config.json
```

当前预置实验包括：

- `baseline/thermoformer_base`：完整模型，默认 5 折交叉验证；
- `ablation/component/no_film`：移除 FiLM 条件调制；
- `ablation/component/no_transformer`：移除组分交互 Transformer；
- `ablation/component/no_mixture_token`：移除全局 mixture token；
- `ablation/thermodynamic_loss/no_continuity_loss`：关闭连续性热力学 loss；
- `ablation/thermodynamic_loss/no_boundary_loss`：关闭近纯组成边界 loss；
- `ablation/thermodynamic_loss/no_solver_loss`：关闭可微泡点求解监督；
- `comparison/ideal_activity`：理想活度系数对比基线。

`interpolation_extrapolation/` 和 `explainability/` 已建立独立类别及实验设计说明；在具体方案和数据划分尚未确定前，不创建虚假的实验结果目录。

消融配置通过 `extends` 继承完整基线，只覆盖目标开关、输出目录和结果文件路径。配置 section 或字段拼写错误会直接报错。

每次成功运行会：

1. 将 checkpoint、训练历史、数据 manifest 和完整指标写入与实验层级一致的 `runs/experiments/<category>/.../<experiment>/`；
2. 自动更新 `experiments/<category>/.../<experiment>/results.md`，记录最终测试指标与交叉验证均值/标准差。

结果摘要使用同目录临时文件完成后再原子替换，写入中断不会破坏上一次结果。`--skip-validation` 会把 checkpoint、history、manifest 和 `smoke_results.md` 全部隔离到正式输出目录下的 `smoke/` 子目录；Uni-Mol 特征缓存可以安全共享，正式产物不会被清理或覆盖。整理前生成的旧运行已隔离至 `runs/legacy/`，不得与当前配置结果混用。

## 训练、验证与测试划分

默认先按无序化学物系隔离独立测试集，再在其余数据上进行 5 折分组交叉验证，最后用全部 CV 数据重训并仅评价一次测试集。A–B 与 B–A 始终在同一分区，二元和三元体系分别分层，纯端点参考体系仅进入训练侧。

每次拟合分为两阶段：默认先进行 80 个 epoch 的实验数据监督，再从最佳监督模型继续进行 5 个 epoch 的物理微调。物理阶段加入相图连续性、近纯边界，以及每个 epoch 少量批次上的可微泡点求解监督。组分置换等变性由模型结构硬约束并由测试验证，不再用数值近零、无有效梯度的辅助 loss。求解器监督批次数和迭代次数均可通过配置调整，以兼顾物理性与训练速度。

论文实验将 80/5 视为阶段上限：监督阶段采用验证 patience 12（至少 10 epoch），物理阶段以监督最佳 checkpoint 作为 epoch 0 候选，只有共同实验验证目标改善时才接受微调结果。监督/物理学习率分别为 `2e-4`/`2e-5`，连续性权重为 `1e-5`；这些设置来自 `reports/first_training_diagnosis.md` 中明确标为非正式结果的单种子 pilot。训练历史记录预裁剪梯度均值/最大值，正式求解评估使用 48 次迭代并始终报告收敛覆盖率。

固定协议划分先运行：

```powershell
python scripts/audit_dataset.py
python scripts/generate_splits.py
python scripts/validate_splits.py
```

随后可按协议执行 seeds 0–4，例如：

```powershell
python scripts/run_paper_suite.py --protocol overall_binary_ternary --device cuda
```

每个正式运行保存完整 split 引用、数据 SHA-256、Git commit、解析后的配置、最佳 checkpoint、训练曲线、逐样本预测和点/物系等权指标。代码、配置或划分未提交时，正式运行会拒绝启动；`--smoke` 产物隔离在 `runs/suite_smoke/` 且不会被五种子聚合器当作正式结果。

单次训练/验证/测试划分可通过覆盖参数运行：

```powershell
python scripts/train_thermoformer.py `
  --config experiments/baseline/thermoformer_base/config.json `
  --evaluation-mode holdout `
  --set evaluation.validation_fraction=0.15 `
  --set evaluation.test_fraction=0.15
```

`P_i^sat(T)` 只依赖单分子表示和温度，或来自有效温区内的可靠 Antoine/DIPPR 相关式；`ln(gamma_i)` 由学习到的 `g^E/RT` 对组成求导。等温与等压求解器均保留梯度，并已接入物理微调与模式化评估。求解从固定、与标签无关的状态开始，观测 `P/T` 只用于计算误差；直接代入观测 `T,P,x` 的结果明确标为 `teacher_forced` 诊断。正式指标分别报告等温压力误差、等压温度误差、汽相组成和收敛率。训练 loss、梯度或任一折指标出现 NaN/Inf 时会立即失败，不会污染参数或被静默删除。
