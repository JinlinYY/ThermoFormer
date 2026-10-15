# Web-package checks

`test_web_layout.py` verifies that the PSMI-style web tree contains the runnable backend/frontend entrypoints and that generated installs, local databases, and secrets are not part of the release.

Run from the repository root:

```powershell
python -m pytest Web/ThermoFormer-web/tests
```
