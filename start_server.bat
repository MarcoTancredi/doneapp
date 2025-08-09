

@echo off

title DoneApp Server

echo Starting DoneApp Server

echo Press CTRL+C to stop

echo ========================================

call conda activate doneapp

python tools/server_manager.py

pause
