
param(
  [string]$EnvName = "py312"
)
$ErrorActionPreference = "Stop"
Write-Host ">>> Installing API deps into conda env: $EnvName"
conda run -n $EnvName python -m pip install --upgrade pip
conda run -n $EnvName python -m pip install -r requirements.api.txt
Write-Host ">>> Done."
