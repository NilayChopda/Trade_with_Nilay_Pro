@echo off
echo ============================================================
echo   Quick Mobile Access - Trade With Nilay
echo ============================================================
echo.
echo Starting dashboard on port 8501...
start /b streamlit run frontend\app.py --server.port 8501 --server.address 0.0.0.0
timeout /t 3

echo.
echo ============================================================
echo   MOBILE ACCESS LINK GENERATOR
echo ============================================================
echo.
echo Option 1: Using Localtunnel (Fastest)
echo.
npx -y localtunnel --port 8501

echo.
echo If the above failed, try Option 2:
echo.
echo Option 2: Using Ngrok
echo 1. Download ngrok from: https://ngrok.com/download
echo 2. Run: ngrok http 8501
echo 3. Copy the HTTPS URL to your mobile browser
echo.
pause
