@echo off
setlocal
cd /d "%~dp0"

where python >nul 2>nul
set PY_MISSING=%ERRORLEVEL%
where ffmpeg >nul 2>nul
set FF_MISSING=%ERRORLEVEL%

if not %PY_MISSING%==0 (
    echo Installing Python...
    winget install --id Python.Python.3.12 -e --accept-source-agreements --accept-package-agreements
)
if not %FF_MISSING%==0 (
    echo Installing ffmpeg...
    winget install --id Gyan.FFmpeg -e --accept-source-agreements --accept-package-agreements
)

if not %PY_MISSING%==0 goto :justinstalled
if not %FF_MISSING%==0 goto :justinstalled
goto :continue

:justinstalled
echo.
echo Python/ffmpeg just got installed. Close this window and double-click
echo setup.bat again to finish (Windows needs a fresh window to see them).
pause
exit /b 0

:continue
echo Setting up the virtual environment...
python -m venv .venv
.venv\Scripts\pip install --quiet -r requirements-windows.txt

if not exist .env (
    copy .env.example .env >nul
    echo Created .env. Edit it later if you want the analysis pass ^(OPENROUTER_API_KEY^).
)

echo.
echo Downloading the Whisper model and running a quick test (one-time, a few minutes)...
set VAULT=%~dp0.setup-test
.venv\Scripts\python.exe transcribe.py sample-call.wav --prospect "Setup Test"
if errorlevel 1 (
    echo.
    echo Setup test failed, something above needs attention before you try a real call.
) else (
    echo.
    echo Setup test passed, model is cached. You're ready.
)
rmdir /s /q "%~dp0.setup-test" 2>nul
set VAULT=

echo.
echo Done. Drag an audio file onto process_call.bat to transcribe it.
pause
