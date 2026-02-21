
@echo off
echo 🚀 Setting up Git for Trade with Nilay...

:: Initialize git if not already
if not exist .git (
    git init
    echo ✓ Git initialized.
) else (
    echo ✓ Git already exists.
)

:: Add all files
git add .

:: Commit
git commit -m "Deployment release for Trade-with-nilay.com"

echo.
echo ----------------------------------------------------------
echo ⚠️ ACTION REQUIRED:
echo 1. Create a PRIVATE repository on GitHub named 'trade-with-nilay'
echo 2. Run the following commands in this terminal:
echo.
echo git remote add origin https://github.com/YOUR_USERNAME/trade-with-nilay.git
echo git branch -M main
echo git push -u origin main
echo ----------------------------------------------------------
pause
