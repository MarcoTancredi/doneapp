
@echo off
powershell -ExecutionPolicy Bypass -File "%~dp0ip_unblock.ps1"
echo.
echo OK. Reinicie a API (tools\dev_api.ps1).
