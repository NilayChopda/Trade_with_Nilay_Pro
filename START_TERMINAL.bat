
@echo off
echo.
echo 🚀 TRADE WITH NILAY - STARTING TERMINAL...
echo.

:: Check for python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found! Please install Python 3.10+
    pause
    exit
)

:: Install requirements
echo [1/3] Checking dependencies...
pip install -r requirements.txt --quiet

:: Init DB
echo [2/3] Preparing database...
python database.py

:: Run app
echo [3/3] Launching Terminal...
echo.
echo 📡 TERMINAL READY! 
echo.
echo 👉 OPEN: http://127.0.0.1:5000 in your browser.
echo.
echo --------------------------------------------------
python app.py
pause
