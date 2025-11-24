@echo off
REM BISG Label Generator Launcher
REM This starts the server and opens your browser automatically

REM Set window title
title BISG Label Generator

REM Change to script directory
cd /d "%~dp0"

REM Set port (change if 5000 is in use)
set PORT=5000

REM Clear screen and show banner
cls
echo ============================================================
echo           BISG LABEL GENERATOR
echo ============================================================
echo.
echo Starting server on port %PORT%...
echo.
echo The browser will open automatically in a few seconds.
echo.
echo To stop the server: Close this window or press Ctrl+C
echo ============================================================
echo.

REM Start server in background and open browser after 3 seconds
start /B py local_app.py

REM Wait for server to start
timeout /t 3 /nobreak >nul

REM Open browser
start http://localhost:%PORT%

REM Keep window open and show server logs
py local_app.py

REM If server stops, pause before closing
pause
