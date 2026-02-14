@echo off
echo ============================================================
echo   Trade With Nilay - Professional 24/7 Deployment
echo ============================================================
echo.
echo 1. Stopping existing containers...
docker-compose down

echo 2. Building fresh images (Ensures latest code is applied)...
docker-compose build --no-cache

echo 3. Starting Services in Background (Detach Mode)...
docker-compose up -d

echo 4. Cleaning up dangling images to save space...
docker image prune -f

echo.
echo ============================================================
echo   🚀 SYSTEM IS RUNNING 24/7 IN THE BACKGROUND
echo ============================================================
echo Dashboard is available at: http://localhost:8501
echo.
echo [OPTIONAL] Starting Public Sharing...
echo If you want mobile access, keep this window open.
echo.
timeout /t 5
npx -y localtunnel --port 8501
pause
