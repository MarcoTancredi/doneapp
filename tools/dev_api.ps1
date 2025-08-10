
param(
  [string]$EnvName = "py312",
  [int]$Port = 8000
)
$ErrorActionPreference = "Stop"

# Garante diretório raiz do repo (um nível acima de tools\)
$Root = Split-Path $PSScriptRoot -Parent
Set-Location $Root

while ($true) {
  try {
    conda run -n $EnvName uvicorn app.api.main:app --host 127.0.0.1 --port $Port --reload
  } catch {
    Write-Host "API crashed: $($_.Exception.Message)"
  }
  Start-Sleep -Seconds 1
}
