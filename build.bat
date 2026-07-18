@echo off
REM StayX Capture Executable Compiler Launcher

echo.
echo =============================================
echo   StayX Capture - App Builder Launcher
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

REM Install core requirements if needed
pip list | findstr "PyQt5" >nul 2>&1
if errorlevel 1 (
    echo Installing base application dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install requirements
        pause
        exit /b 1
    )
)

REM Check if PyInstaller is installed
pip list | findstr "pyinstaller" >nul 2>&1
if errorlevel 1 (
    echo PyInstaller not found. Installing...
    pip install pyinstaller
    if errorlevel 1 (
        echo ERROR: Failed to install PyInstaller
        pause
        exit /b 1
    )
    echo PyInstaller installed successfully.
)

REM Run the builder GUI
echo Starting StayX Builder...
python StayXBuilder.py

pause
