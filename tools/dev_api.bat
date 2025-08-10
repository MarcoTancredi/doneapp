
@echo off
setlocal
set PORT=8000

REM Vai para a raiz do repo (pasta pai de tools\)
cd /d "%~dp0.."

:loop
conda run -n py312 uvicorn app.api.main:app --host 127.0.0.1 --port %PORT% --reload
timeout /t 1 >nul
goto loop
