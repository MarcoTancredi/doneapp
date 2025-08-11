
Param(
  [string]$Root = "D:\Bin\DoneApp"
)
$Data = Join-Path $Root "data"
$File = Join-Path $Data "ip_lists.json"
if (!(Test-Path $Data)) { New-Item -ItemType Directory -Path $Data | Out-Null }
@"
{
  "allow": [],
  "deny": []
}
"@ | Set-Content -Encoding UTF8 $File
Write-Output "IP lists resetadas em $File"
