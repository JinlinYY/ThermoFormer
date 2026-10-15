# 原论文三个案例的 Agent 可靠性实验

本轮仅增加实验入口、输入与证据校验、执行记录和图表，不修改论文正文或 SI。
现有优化策略实验保留；本轮不调整原论文的物理设计条件。

## 实验设计

- 15 条完整需求：每个案例 5 条，涵盖中英文表达、单位换算、组分顺序与需求顺序变化。
- 9 条异常需求：每个案例 3 条，涵盖缺失量、相互矛盾的条件、组成不归一及未注明溶剂比基准。
- 每条需求 3 次独立请求，单批 72 次。LLM 请求使用已有 DeepSeek 配置，temperature=0。
- 每次请求独立上下文；提供工具协议说明，不提供评测标签、标准答案或以前的成功轨迹。
- LLM 提取原始数字、单位与原文片段，并选择协议。单位换算、适用性判断、数值求解与校验由程序完成。
- LLM 报告限定为结论 ID 和证据 ID 的结构化绑定；数值由工具插入，不允许 LLM 生成平衡数字。

这是三个已知体系内的**开发评测**。这些任务在调试过程中已使用，不能作为盲测、跨体系泛化或
LLM 优化策略优越性的证据。3 次重复用于观察接口输出波动，不等于 3 倍独立设计任务。

## 数值不变的边界

|案例|本轮冻结协议|与论文比较的标准|
|---|---|---|
|二元精馏|原 16 点组成网格；原精确回流比；PCHIP 与线性插值|级数和进料级精确一致|
|萃取精馏|原质量溶剂比、回流比、182/183 级和原进料位置；直接泡点复核|纯度与回收率绝对差不超过 2e-6，且未舍入达标判断相同|
|错流萃取|303.15 K、原进料和总溶剂量；原 1–4 级等分及 22 个分配候选|回收率和保留率绝对差不超过 1e-7，且原级数选择不变|

首次出现有效的数值任务时，实际调用 `ggnn39` 中的 ThermoFormer 和过程求解器。
后续等价任务复用该批次的数值 JSON，并在轨迹中标记 `cache_hit`、来源路径及 SHA-256。
因此，重复请求的结果一致性主要检验正确编排与缓存绑定，不是多次独立的热力学验证。

萃取精馏使用通用初值及本次计算的连续初值，未把已发表塔内轨迹作为初值。
精馏与萃取计算均经 `thermo_engine` 的数值入口与校验；误差检查不等于实验准确性、全局相稳定性
或 DWSIM 独立验证。原论文数据、求解器源文件、权重及历史实验结果保持不变。

## 指标与分母

- 完整输入：任务编译、工具计划、工具执行、原论文结果一致性、证据报告完整性；每个案例分母 15。
- 异常输入：LLM 原始澄清是否正确、整个系统是否阻止执行；每个案例分母 9。
- 原始澄清要求：`status=clarify`，且问题字段与问题类型对应。不把后续程序拦截算作 LLM 成功。
- 报告评分检查必要证据、附加引用相关性、遗漏限制及结论范围；评分发生在最终输出拦截之前。
- 计算成本记录 API 次数、API 返回 token 数、总耗时及缓存状态。首次计算与缓存请求耗时分别解释。

报告来自有限结论集合，这项实验不衡量开放文本生成的全部幻觉风险。
受支持的流程计划也是登记好的协议，不是任意流程综合或不受约束的自主搜索。

## 开发记录

所有批次均保留原始请求、响应、工具来源及失败记录，没有覆写失败结果。

- `experiments/supporting_information/s8_agent_reliability/results/historical/reliability-20260926-v1`：初始 72 次。发现合法单位别名被拒绝、相关的多证据引用被过严判定，
  以及 LLM 对质量比协议的误解。修正了单位与证据校验并澄清协议说明。
- `experiments/supporting_information/s8_agent_reliability/results/historical/reliability-20260926-v2`：复测 72 次。发现 LLM 将缺失基准的 `32:1` 标成质量比，
  三次异常请求进入了计算路径。该批次的 `audit.json` 明确保留失败。
- `experiments/supporting_information/s8_agent_reliability/results/reliability-20260926-v3`：增加基于原文片段及局部上下文的质量基准检查后重新运行。
  本批次的实测结论以其 `RESULTS.md`、`evaluation.csv`、`summary.json` 和 `audit.json` 为准。

v1 与后续版本的证据引用评分规则不同，不能把其通过率差异全归因于 LLM 能力提升。
v2 到 v3 的关键补充是输入校验，不是更换 ThermoFormer 或改变过程设计结果。

## 代码入口

- `Web/ThermoFormer-web/backend/paper_agent/reliability.py`：独立的实验契约、DeepSeek 结构化接口、单位和依据检查、报告证据绑定。
- `Web/ThermoFormer-web/backend/thermo_engine/paper_reliability.py`：冻结原论文计算协议的数值适配器。
- `scripts/benchmarks/paper_agent/reliability_tasks.py`：完整任务与评分标签；标签不发送给 LLM。
- `scripts/benchmarks/paper_agent/reliability_run.py`：保存不可覆写的运行记录、计算缓存和源文件快照。
- `scripts/benchmarks/paper_agent/reliability_report.py`：从日志生成 CSV、PNG、SVG、PDF 与实验结果说明。
- `scripts/benchmarks/paper_agent/audit_reliability.py`：核对真实请求、源文件快照、数值文件哈希、环境与权重。

这些契约未加入网页 API；本轮通过命令行运行，不改变现有网页或旧优化实验接口。

The original source-tree run used the following commands (paths and environment are intentionally
kept out of the release because they contain machine-specific settings):

```powershell
python -m benchmarks.paper_agent.reliability_run --output outputs/paper_agent/reliability-new --repeats 3
python -m benchmarks.paper_agent.reliability_report --input outputs/paper_agent/reliability-new
python -m benchmarks.paper_agent.audit_reliability --input outputs/paper_agent/reliability-new
```

The copied files under `scripts/benchmarks/paper_agent/` are provenance snapshots. A live release
rerun requires adapting `PYTHONPATH` and the backend paths to the local checkout first.

输出目录必须是新目录；只有协议与源码哈希均一致时才能 `--resume`。
Provider 错误保留并停止该批次，不自动替换为规则策略。
