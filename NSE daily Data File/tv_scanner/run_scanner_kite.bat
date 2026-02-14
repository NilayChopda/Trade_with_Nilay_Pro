@echo off
REM NSE Scanner with KITE API - Quick Start
REM Scans ALL 2700+ NSE securities with real-time prices from Zerodha
REM Sends instant alerts to Telegram

echo.
echo ============================================================
echo NSE SCANNER - KITE API Integration
echo Scanning ALL 2700+ NSE Securities with Live Prices
echo ============================================================
echo.

REM Check if environment variables are set
if not defined KITE_API_KEY (
    echo [ERROR] KITE_API_KEY not set!
    echo.
    echo Please set environment variables:
    echo   1. KITE_API_KEY = Your Zerodha API Key
    echo   2. KITE_ACCESS_TOKEN = Your KITE Access Token
    echo   3. TG_BOT_TOKEN = Your Telegram Bot Token
    echo   4. TG_CHAT_ID = Your Telegram Chat ID
    echo.
    echo See KITE_SETUP_GUIDE.md for detailed instructions
    pause
    exit /b 1
)

echo [✓] Environment variables detected
echo [✓] KITE API Key: %KITE_API_KEY:~0,10%...
echo [✓] Telegram Bot: %TG_BOT_TOKEN:~0,10%...
echo.

REM Offer options
echo Select scan type:
echo   1. Scan ALL NSE securities (2700+) - Full scan
echo   2. Scan with limit (100 symbols) - Testing
echo   3. Scan specific symbols
echo   4. Exit
echo.

set /p choice="Enter your choice (1-4): "

if "%choice%"=="1" (
    echo.
    echo Running FULL NSE scan...
    echo This will scan all 2700+ symbols and send Telegram alerts.
    echo Estimated time: 30-45 minutes
    echo.
    python main_kite.py --all
) else if "%choice%"=="2" (
    echo.
    echo Running LIMITED scan (first 100 symbols)...
    python main_kite.py --all --limit 100
) else if "%choice%"=="3" (
    set /p symbols="Enter symbols separated by space (e.g., INFY TCS WIPRO): "
    python main_kite.py --symbols %symbols%
) else if "%choice%"=="4" (
    echo Exiting...
    exit /b 0
) else (
    echo Invalid choice!
    pause
    exit /b 1
)

echo.
echo ============================================================
echo Scan complete!
echo Check your Telegram bot for alerts.
echo ============================================================
pause
