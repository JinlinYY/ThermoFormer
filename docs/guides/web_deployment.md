# Web deployment boundary

The current ThermoFormer release exposes Python and command-line interfaces through `src/`, `scripts/`, and `ThermoAgent/`. A browser frontend is not distributed; [`Web/`](../../Web/) records this boundary so application code is not confused with the scientific backend.
