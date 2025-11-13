@echo off
REM Quick start script for local BISG label generator (Windows)

echo ============================================================
echo 🏷️  BISG Label Generator - Local Setup
echo ============================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Error: Python is not installed
    echo    Please install Python 3.9 or higher
    pause
    exit /b 1
)

echo ✅ Python found
python --version
echo.

REM Check if dependencies are installed
echo 📦 Checking dependencies...
python -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Dependencies not installed. Installing now...
    python -m pip install -r requirements_local.txt
    echo.
) else (
    echo ✅ Dependencies already installed
    echo.
)

REM Run the application
echo 🚀 Starting local label generator...
echo.
python local_app.py
