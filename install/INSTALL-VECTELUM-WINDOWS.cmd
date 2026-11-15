@echo off
setlocal
cd /d "%~dp0"
where python >nul 2>nul
if errorlevel 1 (
 echo Install Python 3 from https://www.python.org/downloads/windows/ first.
 pause
 exit /b 1
)
echo VECTELUM Local - developer preview
echo Requires Ubuntu 24.04 WSL2, Git and a working native Docker Engine.
echo 1. Connect existing compatible VECTELUM installation
echo 2. Build a fresh installation (downloads dependencies; requires free disk space)
choice /c 12 /m "Choose installation mode"
if errorlevel 2 (python "%~dp0vectelum-local.py" setup --fresh) else (python "%~dp0vectelum-local.py" setup)
pause
