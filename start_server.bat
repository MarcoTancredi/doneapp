#Action CreateFile
Local: start_server.bat
@echo off
title DoneApp Server
echo 🚀 Starting DoneApp Server
echo 💡 Press CTRL+C to stop (ESC not supported in cmd)
echo ========================================
conda activate doneapp
python tools/server_manager.py
pause
#END Action CreateFile
