@echo off
echo =====================================
echo NSE TradingView Scanner
echo =====================================
echo.

REM Set environment variables (optional - can also use system env vars)
REM set TG_BOT_TOKEN=your_token_here
REM set TG_CHAT_ID=your_chat_id_here  
REM set TV_USERNAME=your_username
REM set TV_PASSWORD=your_password

echo Running scanner...
python main.py

echo.
echo =====================================
echo Scan Complete! Check results.csv
echo =====================================
pause
