@echo off
echo.
echo ============================================================
echo   NEXUS FRAUD DETECTION PLATFORM
echo   Version 3.1.0 (Complete Edition)
echo ============================================================
echo.
echo   Starting server...
echo.
echo   Dashboard: http://localhost:8000
echo   API Docs:  http://localhost:8000/docs
echo.
echo   Press Ctrl+C to stop.
echo.
echo ============================================================
echo.

if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

cd /d "%~dp0"

REM Open browser after 2 second delay
start "" cmd /c "timeout /t 2 /nobreak >nul && start http://localhost:8000"

REM Start the server
python nexus/app.py

if errorlevel 1 (
    echo.
    echo ERROR: Failed to start. Please run INSTALL.bat first.
    echo.
    pause
)
