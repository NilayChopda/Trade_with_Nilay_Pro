@echo off
REM Order Block Scanner Scheduler Launcher
REM This script starts the automated Order Block scanner with Telegram alerts

cd /d "%~dp0"

echo Starting Order Block Scanner Scheduler...
echo.

python main.py --scheduler --scan-interval 60 --monitor-interval 30

echo.
echo Scheduler stopped.
pause