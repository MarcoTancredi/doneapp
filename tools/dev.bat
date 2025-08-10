@echo off
setlocal
set HOST=127.0.0.1
set PORT=5000
:loop
conda run -n py312 python tools\apply_changes.py --host %HOST% --port %PORT%
timeout /t 1 >nul
goto loop
