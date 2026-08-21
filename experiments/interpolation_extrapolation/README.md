# Interpolation and extrapolation experiments

This category implements controlled generalization studies, including:

- composition and temperature interpolation within observed system domains;
- temperature, pressure and composition extrapolation beyond training ranges;
- unseen binary/ternary system or molecule holdouts.

Every study has its own subdirectory containing `config.json`, `run.md` and
`results.md`. Its exact row assignment is committed under `splits/`; no result is
claimed until all requested seeds complete and are aggregated.
