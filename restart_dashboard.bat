@echo off
echo ============================================================
echo   Trade With Nilay - Clean Restart
echo ============================================================
echo.
echo Step 1: Killing old processes...
taskkill /F /IM streamlit.exe >nul 2>&1
taskkill /F /IM python.exe >nul 2>&1
timeout /t 2

echo Step 2: Starting fresh dashboard...
cd /d "%~dp0"
streamlit run frontend\app.py --server.port 8501

pause
