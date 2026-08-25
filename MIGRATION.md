# Source-layout migration

The scientific implementation remains backward compatible. The following
active modules are preferred for new research code:

| Existing import | Preferred interface |
|---|---|
| `src.model` | `src.thermoformer.models` |
| `src.representation` | `src.thermoformer.features` |
| `src.data` | `src.thermoformer.data` |
| `src.thermo`, `src.pure_properties` | `src.thermoformer.thermodynamics` |
| `src.training`, `src.losses`, `src.physics_finetuning` | `src.thermoformer.training` |
| `src.evaluation`, `src.metrics` | `src.thermoformer.evaluation` |
| `src.config` | `src.thermoformer.configuration` |
| `src.protocols`, `src.paper_runner` | `src.thermoformer.protocols` |
| `src.results`, `src.reporting`, `src.artifacts` | `src.thermoformer.reporting` |

Historical `src.*` modules are adapters that alias the canonical implementation
module. This preserves mocks, strict checkpoint loading, and imports of helper
functions used by earlier experiment programs.

Historical data-preparation and early reporting programs moved from `scripts/`
and `src/` to `archive/legacy_code/`. They are preserved for provenance and are
not supported execution paths.

The superseded supervised-only `overall_binary_ternary` experiment record is
preserved at `archive/legacy_code/experiment_records/overall_binary_ternary_supervised/`.
The canonical manuscript experiment at
`experiments/predictive_performance/overall_binary_ternary/` represents the
validation-selected final C1 model with fugacity fine-tuning.
