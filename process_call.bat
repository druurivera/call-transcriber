@echo off
setlocal
cd /d "%~dp0"

if "%~1"=="" (
    echo Drag an audio file onto this .bat file to transcribe it.
    pause
    exit /b 1
)

set PROSPECT=%~2
if "%PROSPECT%"=="" set /p PROSPECT=Prospect name for this call?

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0process_call.ps1" -Audio "%~1" -Prospect "%PROSPECT%"
pause
