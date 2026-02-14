@echo off
cd /d "%~dp0"
echo Starting Chartink Scanner Engine (Continuous Mode)...
echo Press Ctrl+C to stop.
python backend\scanner\scanner_engine.py
pause
