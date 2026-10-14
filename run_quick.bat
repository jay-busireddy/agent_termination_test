@echo off
python run_tests.py --quick
if errorlevel 1 exit /b %errorlevel%
start "" results\report.html
