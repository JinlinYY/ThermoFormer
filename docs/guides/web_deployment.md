# Web deployment

ThermoFormer ships a browser engineering workbench under [`Web/ThermoFormer-web/`](../../Web/ThermoFormer-web/), following the PSMI release layout. The backend is a FastAPI service and the frontend is a Next.js application; both are runnable from the repository root.

```powershell
python -m pip install -r Web/ThermoFormer-web/backend/requirements.txt
pnpm --dir Web/ThermoFormer-web/frontend install --frozen-lockfile
pwsh Web/ThermoFormer-web/scripts/run_backend.ps1
pwsh Web/ThermoFormer-web/scripts/run_frontend.ps1
```

Set `NEXT_PUBLIC_API_URL` when the frontend needs a non-local API endpoint. The backend launcher sets `THERMOFORMER_SRC` to the release `src/` directory and uses the checked-in `Web/ThermoFormer-web/backend/knowledge` tree. Keep checkpoints, credentials, caches, and generated databases outside Git.
