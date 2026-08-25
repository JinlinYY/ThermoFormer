# Source-layout migration

The scientific implementation remains backward compatible. The following
curated interfaces are preferred for new research code:

| Existing import | Preferred interface |
|---|---|
| `src.model` | `src.thermoformer.model` |
| `src.representation` | `src.thermoformer.features` |
| `src.data` | `src.thermoformer.data` |
| `src.thermo`, `src.pure_properties` | `src.thermoformer.thermodynamics` |
| `src.training`, `src.losses`, `src.physics_finetuning` | `src.thermoformer.training` |
| `src.evaluation`, `src.metrics` | `src.thermoformer.evaluation` |
| `src.config` | `src.thermoformer.configuration` |

Historical data-preparation and early reporting programs moved from `scripts/`
and `src/` to `archive/legacy_code/`. They are preserved for provenance and are
not supported execution paths.
