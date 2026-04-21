@echo off

REM Move to the folder containing this .bat file
cd /d "%~dp0"

REM Optional: show where we are running from
echo Running from:
cd
echo.

REM Run the Python test harness
python "%~dp0_test_harness.py"

echo.
pause
