@echo off
python run_tests.py
if errorlevel 1 exit /b %errorlevel%
start "" results\report.html
