@echo off
echo ============================================================
echo   GitHub Fixer - Trade With Nilay
echo ============================================================
echo.
echo Step 1: Cleaning up old Git setup...
cd /d "g:\My Drive\Trade_with_Nilay\Nilay's Scanner"
rd /s /q .git >nul 2>&1

echo.
echo Step 2: Initializing Git in the CORRECT folder...
cd /d "g:\My Drive\Trade_with_Nilay"
rd /s /q .git >nul 2>&1
git init

echo.
echo Step 3: Adding files...
git add .
git commit -m "Fresh deployment setup"

echo.
echo ============================================================
echo   FIX COMPLETE! 
echo ============================================================
echo.
echo NOW DO THIS:
echo 1. Open GitHub Desktop
echo 2. Go to File > Add Local Repository
echo 3. Select: g:\My Drive\Trade_with_Nilay
echo 4. It should now show "Current Repository: Trade_with_Nilay"
echo 5. Click "Publish Repository"
echo.
pause
