# setup_env.ps1 — Windows 11 24H2
# Purpose: Install Volta, pin Node.js 22.18.0 LTS, enable Corepack;
#          Install Miniforge, set conda-forge, install mamba; ensure base Python 3.12;
#          Create env 'py312' (Python 3.12).
# Run this script in an elevated PowerShell (Admin) window:  Right click > Run as Administrator.

$ErrorActionPreference = "Stop"

function Assert-Command($name) {
  if (-not (Get-Command $name -ErrorAction SilentlyContinue)) {
    Write-Error "Required command '$name' not found."
  }
}

Write-Host "=== 1) Install Volta via winget ==="
try {
  winget install --id Volta.Volta -e --source winget --accept-source-agreements --accept-package-agreements
} catch {
  Write-Warning "winget install failed. You can manually download Volta from https://docs.volta.sh/guide/getting-started"
}

# Ensure Volta is on PATH for this session
$voltaPath = "$Env:ProgramFiles\Volta"
if (Test-Path $voltaPath) { $Env:PATH = "$voltaPath;$Env:PATH" }

Write-Host "=== 2) Install and pin Node 22.18.0 LTS with Volta ==="
Assert-Command volta
volta install node@22.18.0
volta pin node@22.18.0
node -v
npm -v

Write-Host "=== 3) Enable Corepack (for Yarn/pnpm via Node) ==="
corepack enable
corepack --version

Write-Host "=== 4) Download & Install Miniforge (user-scoped) ==="
# If you already downloaded the installer, set $miniforgeInstaller to that path.
# Otherwise, we attempt to fetch the latest stable Miniforge3-Windows-x86_64.exe.
# NOTE: The exact file name can change; if this download fails, download manually from:
# https://github.com/conda-forge/miniforge/releases (Miniforge3 Windows x86_64 .exe)

$temp = New-Item -ItemType Directory -Path "$Env:TEMP\miniforge_dl" -Force
$miniforgeInstaller = "$($temp.FullName)\Miniforge3-Windows-x86_64.exe"
$downloaded = $false

$urls = @(
  "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Windows-x86_64.exe"
)
foreach ($u in $urls) {
  try {
    Invoke-WebRequest -Uri $u -OutFile $miniforgeInstaller -UseBasicParsing
    $downloaded = $true
    break
  } catch {
    Write-Warning "Failed to download from $u"
  }
}
if (-not $downloaded) {
  Write-Warning "Automatic download failed. Manually download Miniforge3-Windows-x86_64.exe and re-run."
  exit 1
}

# Silent install to %USERPROFILE%\Miniforge3 and add to PATH
$installDir = "$Env:USERPROFILE\Miniforge3"
Start-Process -FilePath $miniforgeInstaller -ArgumentList "/S","/InstallationType=JustMe","/AddToPath=1","/RegisterPython=0","/D=$installDir" -Wait

# Initialize conda for PowerShell
& "$installDir\Scripts\conda.exe" init powershell

# Ensure new PATH for current session
$Env:PATH = "$installDir;$installDir\Library\bin;$installDir\Scripts;$installDir\condabin;$Env:PATH"

# Use conda with conda-forge only, install mamba, and pin Python 3.12 in base
Write-Host "=== 5) Configure conda-forge + mamba; set base Python=3.12; create env py312 ==="
& conda config --set auto_activate_base false
& conda config --set channel_priority strict
& conda config --remove-key default_channels 2>$null
& conda config --add channels conda-forge

# Install mamba in base
& conda install -n base -y mamba -c conda-forge

# Ensure base uses Python 3.12
& conda install -n base -y python=3.12

# Create project env py312
& mamba create -n py312 -y python=3.12

Write-Host "=== DONE ==="
Write-Host "Open a NEW PowerShell and run: conda activate py312"