@echo off
title Automation Studio - Setup
echo ============================================
echo    Automation Studio - One-Click Setup
echo ============================================
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found!
    echo Install from: https://www.python.org/downloads/
    pause
    exit /b
)

echo [1/3] Creating virtual environment...
python -m venv venv
call venv\Scripts\activate

echo [2/3] Installing dependencies...
pip install --quiet -r requirements.txt
pip install --quiet pywin32

echo [3/3] Setting up database...
if not exist .env (
    echo DATABASE_URL=sqlite:///automation.db > .env
)
python seed.py

echo.
echo ============================================
echo    Setup Complete!
echo ============================================
echo.
echo To start: venv\Scripts\activate ^&^& streamlit run app.py
pause