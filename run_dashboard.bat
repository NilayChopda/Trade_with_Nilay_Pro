@echo off
cd /d "%~dp0"
echo Starting Trade With Nilay Dashboard...
streamlit run frontend\app.py
pause
