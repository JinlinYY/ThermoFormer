# Article-aligned repository scope

The active repository contains experiments required by the supplied ThermoFormer article:

- VLE and LLE dataset construction and audits;
- VLE and LLE predictive-performance benchmarks;
- composition, thermodynamic-state, system-disjoint, and unseen-component generalization;
- VLE machine-learning and thermodynamic-model comparisons;
- joint binary--ternary molecular-representation and interaction-architecture ablations;
- Stage 0--3 thermodynamic optimization diagnostics;
- VLE molecular-view and composition-dependent interaction analyses;
- the deterministic ThermoEqui-Agent separation-design case studies in
  `ThermoAgent/`, including the binary distillation, extractive distillation,
  and crossflow-extraction calculations described in SI S7;
- the execution and evidence-review records associated with SI S8.

The release separates deterministic numerical reproduction from optional LLM
orchestration and external DWSIM integration. The former is runnable from the
bundled `ThermoAgent/reproduce.py`; the latter is not required for the
reported numerical values and is not used as a hidden substitute.

Independent experiments for mixtures above ternary order and a separate closed-loop entrainer-screening framework are outside this repository scope. Runtime caches, smoke-run outputs, redundant checkpoint collections, and source-reference collections are also excluded from the active tree. Binary-to-ternary transfer material remains because it is referenced by the registered generalization report and supports the article's discussion of interaction transfer.

`models/registry.json` remains the authoritative catalog for the 105 validation-selected VLE/LLE prediction and generalization checkpoints.
