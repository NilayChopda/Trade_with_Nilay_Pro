@echo off
echo ============================================================
echo   Nilay's Scanner - Public Sharing Utility
echo ============================================================
echo.
echo This will make your local dashboard accessible on your mobile 
echo or any other device via a public URL.
echo.
echo [METHOD 1] Using npx (Requires Node.js)
echo Running localtunnel...
echo.
npx -y localtunnel --port 8501
echo.
if %errorlevel% neq 0 (
    echo.
    echo [METHOD 2] If npx failed, please:
    echo 1. Download ngrok from https://ngrok.com/download
    echo 2. Run: ngrok http 8501
    echo 3. Copy the 'Forwarding' URL to your mobile browser.
)
pause
