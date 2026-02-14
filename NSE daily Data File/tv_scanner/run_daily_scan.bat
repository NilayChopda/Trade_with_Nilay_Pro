@echo off
REM NilayChopdaScanner - Windows Task Scheduler Script
REM Runs daily at 9:15 AM automatically
REM Place this file in: C:\Users\%USERNAME%\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup

setlocal enabledelayedexpansion

echo.
echo =========================================================================
echo NilayChopdaScanner - Daily Auto-Scan
echo =========================================================================
echo Time: %date% %time%
echo.

REM Set working directory
cd /d "G:\My Drive\Trade_with_Nilay\NSE daily Data File\tv_scanner"

REM Run Python scanner
python nilaychopda_live_scanner.py

REM Log completion
echo [%date% %time%] Scanner completed >> scanner_daily.log

echo.
echo =========================================================================
echo Scan finished at %time%
echo Next scan: Tomorrow at 09:15 AM
echo =========================================================================
echo.

pause
