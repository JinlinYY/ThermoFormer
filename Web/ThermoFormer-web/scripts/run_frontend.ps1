# Frontend launcher for ThermoFormer-web.
[CmdletBinding()]
param(
    [int]$Port = 3000,
    [string]$ApiUrl = "http://localhost:8000"
)
$ErrorActionPreference = "Stop"
$frontendRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\frontend")).Path
$env:NEXT_PUBLIC_API_URL = $ApiUrl
Set-Location $frontendRoot
& pnpm dev --hostname 127.0.0.1 --port $Port
