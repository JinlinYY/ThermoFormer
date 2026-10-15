# ThermoFormer web workbench

This directory contains the runnable browser workbench for the ThermoFormer release. Its layout follows the research-release convention used by [PSMI](https://github.com/JinlinYY/PSMI/tree/main/Web/PSMI-LLE-web):

```text
ThermoFormer-web/
├── backend/     FastAPI API, thermodynamic agent, schemas, knowledge base
├── frontend/    Next.js/React workbench and TypeScript API contracts
├── scripts/     Windows PowerShell and POSIX launch helpers
└── tests/       Web-package layout and integration checks
```

The numerical policy is unchanged: the language model can classify and orchestrate requests, while equilibrium values must come from the deterministic `thermo_engine` and pass validation. Missing parameters, checkpoints, or optional feature dependencies are reported as structured failures.

## Quick start

From the repository root, install the backend dependencies with Python 3.11 or newer:

```powershell
python -m pip install -r Web/ThermoFormer-web/backend/requirements.txt
```

Install the frontend dependencies with Node.js and pnpm 11:

```powershell
pnpm --dir Web/ThermoFormer-web/frontend install --frozen-lockfile
```

Start two terminals:

```powershell
pwsh Web/ThermoFormer-web/scripts/run_backend.ps1
pwsh Web/ThermoFormer-web/scripts/run_frontend.ps1
```

Open <http://localhost:3000>. The API is available at <http://localhost:8000> and its OpenAPI document is at <http://localhost:8000/docs>.

POSIX shells can use `scripts/run_backend.sh` and `scripts/run_frontend.sh`.

## Runtime configuration

The backend launcher sets `PYTHONPATH` to the packaged backend and points `KNOWLEDGE_ROOT` at the checked-in knowledge base. It also points `THERMOFORMER_SRC` at the repository's top-level `src/` tree, so the scientific model implementation remains shared with the main release. If trained checkpoint files are stored outside Git LFS, set `THERMOFORMER_CHECKPOINT` explicitly. Never commit `.env` files or API keys.

The frontend reads `NEXT_PUBLIC_API_URL`; it defaults to `http://localhost:8000`.

## Checks

```powershell
python -m pytest Web/ThermoFormer-web/tests
pnpm --dir Web/ThermoFormer-web/frontend test
pnpm --dir Web/ThermoFormer-web/frontend lint
pnpm --dir Web/ThermoFormer-web/frontend build
```

The full scientific test suite remains at the repository root. The web package intentionally does not copy generated `node_modules`, `.next`, Python caches, local databases, or model weights.
