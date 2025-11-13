@echo off
echo ========================================
echo BISG Labels - Installing Dependencies
echo ========================================
echo.

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Installing/upgrading dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt

echo.
echo ========================================
echo Installation complete!
echo ========================================
echo.
echo New dependencies installed:
echo   - Flask-Limiter (rate limiting)
echo   - Flask-Talisman (security headers)
echo.
echo Next steps:
echo   1. Review .env.example for new environment variables
echo   2. Update your .env or Railway variables
echo   3. Test locally: python app/main.py
echo   4. Deploy to Railway
echo.
pause
