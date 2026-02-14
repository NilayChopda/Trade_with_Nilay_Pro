@echo off
cd /d "%~dp0"
echo Starting Data Scheduler (Mon-Fri 9:15 AM - 3:30 PM)...
python backend\scheduler.py
pause
