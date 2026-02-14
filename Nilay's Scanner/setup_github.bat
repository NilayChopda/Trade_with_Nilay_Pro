@echo off
echo ============================================================
echo   GitHub Setup - Trade With Nilay
echo ============================================================
echo.
echo This will initialize your project for GitHub deployment.
echo.
pause

cd /d "g:\My Drive\Trade_with_Nilay"

echo Step 1: Initializing Git repository...
git init

echo.
echo Step 2: Adding all files...
git add .

echo.
echo Step 3: Creating first commit...
git commit -m "Initial commit - Trade With Nilay v2.0"

echo.
echo ============================================================
echo   SUCCESS! Git repository initialized.
echo ============================================================
echo.
echo NEXT STEPS:
echo 1. Go to https://github.com/new
echo 2. Create a new repository named: trade-with-nilay
echo 3. Make it PUBLIC (required for free Streamlit hosting)
echo 4. Copy the repository URL
echo 5. Run this command (replace YOUR_USERNAME):
echo.
echo    git remote add origin https://github.com/YOUR_USERNAME/trade-with-nilay.git
echo    git push -u origin main
echo.
echo Then go to https://share.streamlit.io to deploy!
echo.
pause
