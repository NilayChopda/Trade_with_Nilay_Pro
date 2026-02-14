@echo off
REM NilayChopdaScanner - Startup Script
REM This file starts the scheduler when Windows boots up
REM 
REM To use:
REM 1. Save this file to: C:\Users\%USERNAME%\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup
REM 2. Restart Windows
REM 3. Scanner will run automatically at 9:15 AM every day

setlocal enabledelayedexpansion

REM Get current directory
cd /d "G:\My Drive\Trade_with_Nilay\NSE daily Data File\tv_scanner"

REM Run scheduler in background (no window)
start /b "" python auto_scheduler.py

REM Exit silently
exit /b 0
