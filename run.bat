@echo off
REM Screenshot Capture Application Launcher

echo.
echo =============================================
echo   StayX Capture - Modern GUI Tool
echo =============================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://www.python.org
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
    echo Virtual environment created.
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Check if dependencies are installed
pip list | findstr "PyQt5" >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
    echo Dependencies installed successfully.
)

REM Run the application
echo.
echo Starting Screenshot Capture...
echo.
python Capture.py

pause
