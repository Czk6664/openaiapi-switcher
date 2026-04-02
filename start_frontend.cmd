@echo off
setlocal
cd /d "%~dp0"

if exist "dist\openaiapi-switcher.exe" (
  start "" "dist\openaiapi-switcher.exe"
  exit /b 0
)

if exist "launch_gui.cmd" (
  call "launch_gui.cmd"
  exit /b 0
)

where pythonw >nul 2>nul
if %errorlevel%==0 (
  start "" pythonw "main.py"
) else (
  start "" python "main.py"
)

exit /b 0
