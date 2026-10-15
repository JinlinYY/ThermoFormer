# Backend launcher for ThermoFormer-web.
[CmdletBinding()]
param(
    [int]$Port = 8000,
    [string]$PythonExecutable = "python"
)
$ErrorActionPreference = "Stop"
$webRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\")).Path
$repoRoot = (Resolve-Path (Join-Path $webRoot "..\..\")).Path
$backendRoot = Join-Path $webRoot "backend"
$env:PYTHONPATH = $backendRoot
$env:KNOWLEDGE_ROOT = Join-Path $backendRoot "knowledge"
$env:THERMOFORMER_SRC = Join-Path $repoRoot "src"
$env:THERMOFORMER_FEATURE_CACHE = Join-Path $backendRoot ".thermoformer-cache"
$env:THERMO_EXPERIENCE_DB = Join-Path $backendRoot "data\agent_experience.sqlite3"
Set-Location $backendRoot
& $PythonExecutable -m uvicorn main:app --reload --host 127.0.0.1 --port $Port
