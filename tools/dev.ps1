# Loop para relançar o servidor após restart
param(
  [string]$HostIp = "127.0.0.1",
  [int]$Port = 5000
)
while ($true) {
  try {
    conda run -n py312 python tools\apply_changes.py --host $HostIp --port $Port
  } catch {
    Write-Host "Server crashed: $($_.Exception.Message)"
  }
  Start-Sleep -Seconds 3
}
