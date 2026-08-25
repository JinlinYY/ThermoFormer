# Figure_dataset_overview_v3：论文题注与数据集说明

## 中文题注

**图 1 | 二元与三元汽液相平衡数据集的规模及覆盖范围。** **a，** 二元和三元数据集所包含的实验 VLE 状态点、唯一无序化学体系和分子组分数量。二元数据集包含 23,061 个状态点、700 个体系和 333 种组分；三元数据集包含 5,229 个状态点、126 个体系和 125 种组分。**b，** 两类数据在温度–压力空间中的覆盖。压力采用对数坐标，密度等高线表示主要采样区域；温度断轴保留了 25 个高于 650 K 的观测。**c，** 基于 RDKit/SMARTS 结构规则划分的化学家族覆盖，其中 c1 与 c2 对唯一体系数采用相同的绝对气泡面积标度。**c1，** 二元体系的家族对分布；每个无序家族对仅在上三角矩阵中出现一次，气泡面积表示唯一二元体系数，颜色表示实验 VLE 点数。**c2，** 三元体系的家族三元组合分布；在全部 49 种组合中显示实验点数最多的 18 种，横坐标表示实验点数，气泡面积表示唯一三元体系数。**d，** 组成空间覆盖；左图为二元体系液相摩尔分数 $x_1$ 与气相摩尔分数 $y_1$ 的二维密度分布，虚线为 $y_1=x_1$；右图为三元体系液相组成在单纯形中的分布，三个顶点对应源数据中记录的组分 1、2 和 3，仅表示记录顺序，不代表跨体系统一的化学身份。**e，** 三元体系与对应二元子体系的覆盖关系；对每个三元体系 $A+B+C$，统计其三个二元子体系 $A+B$、$A+C$ 和 $B+C$ 中已有多少出现在二元数据集中。所有体系均按与组分排列顺序无关的标识进行计数。

## 正文结果描述

整理后的数据集共包含 28,290 个实验 VLE 状态点，其中二元记录 23,061 条、三元记录 5,229 条，分别覆盖 700 个二元体系和 126 个三元体系。与三元数据相比，二元数据在体系数、组分数和状态点数上均具有更大的覆盖范围。两类数据覆盖了较宽的热力学状态空间：二元数据的温度和压力范围分别为 153.23–1550 K 和 0.010–50,180 kPa，三元数据分别为 253.27–1400 K 和 0.010–15,000 kPa。数据主要集中在常见实验温压区间，但仍包含少量高温和高压记录，因此图 1b 同时采用对数压力坐标和温度断轴，以保留长尾状态而不压缩主体分布。

化学家族统计显示，该数据集并非由少量同质体系构成，而是覆盖 79 种二元家族对和 49 种三元家族组合，同时呈现明显的长尾分布。二元数据中，卤代化合物–烃类、醇–酯、卤代化合物–卤代化合物、醇–醚和醇–烃类是覆盖体系数较多的组合，分别包含 55、39、38、36 和 34 个唯一体系。三元数据中，实验点数最多的组合依次包括醇–未解析组分–水（550 点，12 个体系）、醇–其他–未解析组分（368 点，10 个体系）、醇–酯–烃类（364 点，3 个体系）、醇–醚–水（335 点，4 个体系）以及醇–酯–未解析组分（334 点，10 个体系）。图 1c2 所示的前 18 种组合合计贡献 4,083 个实验点和 80 个三元体系，分别占三元数据的 78.1% 和 63.5%，说明高频化学组合与低频长尾体系并存。“未解析组分”表示相应记录缺少可可靠解析的分子结构，不能据此推断其真实官能团类别。

组成空间分析进一步表明，二元记录涵盖了从近纯组分端点到混合物内部的广泛组成区域，其中 18.1% 的记录位于 $x_1\leq0.05$ 或 $x_1\geq0.95$ 的液相端点附近；$|y_1-x_1|$ 的中位数为 0.152，反映出数据中存在显著的液–气相组成差异。三元液相记录中，68.7% 位于三个摩尔分数均不低于 0.05 的单纯形内部，7.0% 位于某一组分摩尔分数不低于 0.90 的顶点邻域。对于三元到二元的层级迁移，30 个三元体系具有全部三个对应二元子体系，22 个具有两个，69 个仅具有一个，另有 5 个没有任何对应二元子体系。这一分布同时提供了高覆盖内插、部分覆盖迁移和低覆盖外推等不同难度的评估场景。

## 数据集构建方法

本研究使用 `dataset` 目录中的 `binary_vle_english.xlsx` 和 `ternary_vle_english.xlsx` 两份工作簿构建统一的二元–三元 VLE 数据资源。两份工作簿汇总了带有 DOI 来源标识的实验平衡记录，合计对应 392 个不重复 DOI 标识；其中二元表含 387 个 DOI，三元表含 84 个 DOI，两者有 79 个重合。每条记录均保留源文献中的组分名称，并统一提供分子式、可获得时的 SMILES、两项热力学一致性质量码、实验温度、实验压力、液相组成、气相组成及 DOI。英文版本统一了字段名称和数据字典，但没有对原始组分名称进行未经核验的翻译，从而保留了与来源记录的可追溯关系。

在标准化过程中，温度由摄氏度转换为开尔文，即 $T\,(\mathrm{K})=T\,(^{\circ}\mathrm{C})+273.15$；压力由 mmHg 转换为 kPa，采用 $1\ \mathrm{mmHg}=0.133322368\ \mathrm{kPa}$。二元表保存独立变量 $x_1$ 和 $y_1$，其余组成通过闭合关系 $x_2=1-x_1$ 和 $y_2=1-y_1$ 重建。三元表保存 $x_1$、$x_2$、$y_1$ 和 $y_2$，第三组分通过 $x_3=1-x_1-x_2$ 和 $y_3=1-y_1-y_2$ 重建。上述操作仅用于形成统一的分析和建模表示，不改变工作簿中的原始实验数值。

为避免同一化学体系因组分排列不同而被重复计数，组分名称首先进行 Unicode 规范化、大小写统一和空白清理；可解析的 SMILES 随后通过 RDKit 规范化，并生成规范 SMILES 和 InChIKey。对于缺失 SMILES 的记录，若规范化名称与分子式能够唯一对应到已有结构，则链接到该结构；否则由规范化名称和分子式生成稳定的回退标识，而不臆造分子结构。体系标识由组分稳定标识排序后构成，因此 $A+B$ 与 $B+A$、以及三元体系的不同排列均被视为同一体系。化学家族采用带优先级的 RDKit/SMARTS 规则划分为水、酸、酰胺、酯、酮、醇、胺、醚、含硫化合物、卤代化合物、芳香化合物、烃类和其他；无法可靠获得结构的组分单独标记为 unresolved。

两项质量码均遵循 `1 = 通过`、`0 = 未通过`、`−1 = 未评价` 的定义。合并记录中，4,696 条至少有一项检查通过且无失败项，3,860 条至少有一项检查失败，19,734 条未经过可判定的一致性评价。描述性统计和图 1 的覆盖分析保留这些质量状态，没有静默删除失败或未评价记录。审计未发现完全相同的原始重复行；在统一体系身份、温度、压力和组成顺序后，共有 18 行涉及重复状态，对应 9 条首条记录之外的重复记录，可在后续训练划分或样本加权阶段显式处理。每条标准化记录仍保留来源文件、Excel 行号和 DOI，从而支持从模型输入回溯到原始实验条目。

## English caption

**Figure 1 | Scale and coverage of the binary and ternary vapor–liquid equilibrium datasets.** **a,** Numbers of experimental VLE state points, unique unordered chemical systems, and molecular components. The binary dataset contains 23,061 state points from 700 systems and 333 components, whereas the ternary dataset contains 5,229 state points from 126 systems and 125 components. **b,** Temperature–pressure coverage. Pressure is shown on a logarithmic scale, density contours summarize the principal sampling regions, and the broken temperature axis retains 25 observations above 650 K. **c,** Chemical-family coverage assigned using RDKit/SMARTS rules; c1 and c2 share an absolute bubble-area scale for the number of unique systems. **c1,** Upper-triangular distribution of unordered binary family pairs, with bubble color indicating the number of experimental VLE points. **c2,** The 18 ternary family triplets with the most experimental points among 49 triplets in total; horizontal position denotes experimental points and bubble area denotes unique ternary systems. **d,** Composition-space coverage, shown as the binary $x_1$–$y_1$ density relative to $y_1=x_1$ and the ternary liquid-composition simplex. The ternary vertices denote the component order recorded in the source data and do not have a common chemical identity across systems. **e,** Binary-to-ternary coverage, quantified by the number of constituent binary subsystems observed for each ternary system. System identities are invariant to component order.
