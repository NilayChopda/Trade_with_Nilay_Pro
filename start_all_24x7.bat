@echo off
setlocal
echo ============================================================
echo   Trade With Nilay - Professional 24/7 Launcher (v1.6)
echo ============================================================
echo.
echo 1. Clearing old sessions...
taskkill /f /im python.exe /t >nul 2>&1
taskkill /f /im node.exe /t >nul 2>&1

echo 2. Starting Market Scanner (Signals) in background...
start /b python backend/scanner/scanner_engine.py > scanner.log 2>&1

echo 3. Starting Alert Monitor (Real-time Telegram) in background...
start /b python backend/services/alert_monitor.py > alerts.log 2>&1

echo 4. Starting Professional Dashboard in background...
start /b streamlit run frontend/app.py --server.port 8501 --server.address 0.0.0.0 > dashboard.log 2>&1

echo 5. Waiting for services to stabilize...
timeout /t 5

echo 6. Starting Public Sharing (Remote Access)...
echo ------------------------------------------------------------
echo YOUR PUBLIC URL WILL APPEAR BELOW:
echo ------------------------------------------------------------
npx -y localtunnel --port 8501
pause
