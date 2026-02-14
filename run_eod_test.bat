@echo off
cd /d "%~dp0"
echo Generating End of Day Report...
echo This will calculate market stats and send a Telegram summary.
python test_eod.py
pause
