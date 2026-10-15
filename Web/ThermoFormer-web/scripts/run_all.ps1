# Start both services in separate PowerShell windows.
[CmdletBinding()]
param([string]$PythonExecutable = "python")
$ErrorActionPreference = "Stop"
$scriptRoot = (Resolve-Path $PSScriptRoot).Path
Start-Process pwsh -ArgumentList @("-NoExit", "-File", (Join-Path $scriptRoot "run_backend.ps1"), "-PythonExecutable", $PythonExecutable)
Start-Process pwsh -ArgumentList @("-NoExit", "-File", (Join-Path $scriptRoot "run_frontend.ps1"))
