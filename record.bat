@echo off
setlocal
cd /d "%~dp0"

set NAME=%~1
if "%NAME%"=="" set NAME=call

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0record.ps1" -Name "%NAME%"
pause
