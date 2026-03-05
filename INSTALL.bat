@echo off
echo.
echo ============================================================
echo   NEXUS FRAUD DETECTION PLATFORM - INSTALLER
echo   Version 3.1.0 (Complete Edition)
echo ============================================================
echo.
echo   Modules Included:
echo     [1] Transaction Fraud Scoring (47 Nigerian features)
echo     [2] Insider Threat Detection (Employee monitoring)
echo     [3] CBN Report Generation (e-Fraud, STR, CTR)
echo     [4] Agent/POS Fraud Detection (Geo-fencing)
echo     [5] Database Persistence (SQLite)
echo.
echo ============================================================
echo.

echo [1/4] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ERROR: Python is not installed or not in PATH!
    echo Please install Python 3.10+ from https://python.org
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)
echo       Python found!

echo.
echo [2/4] Creating virtual environment...
if not exist "venv" (
    python -m venv venv
    echo       Virtual environment created.
) else (
    echo       Virtual environment already exists.
)

echo.
echo [3/4] Activating virtual environment and installing packages...
call venv\Scripts\activate.bat

pip install --upgrade pip >nul 2>&1
pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo ERROR: Failed to install some packages.
    echo Trying individual installation...
    pip install fastapi uvicorn pydantic aiosqlite sqlalchemy openpyxl httpx python-multipart
)

echo.
echo [4/4] Initializing database...
python -c "from nexus.app import init_database; import asyncio; asyncio.run(init_database())" 2>nul
if errorlevel 1 (
    echo       Database will be initialized on first run.
)

echo.
echo ============================================================
echo   INSTALLATION COMPLETE!
echo ============================================================
echo.
echo   To start Nexus, run:
echo     START.bat
echo.
echo   Or manually:
echo     venv\Scripts\activate
echo     python nexus/app.py
echo.
echo   Dashboard: http://localhost:8000
echo   API Docs:  http://localhost:8000/docs
echo.
echo ============================================================
echo.
pause
