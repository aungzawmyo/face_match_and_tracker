@echo off
REM FaceScannerPro Installation Script for Windows
REM This script will set up the complete environment

echo ============================================
echo FaceScannerPro Installation Script
echo ============================================

echo Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

echo Python found. Creating virtual environment...
python -m venv .venv
if errorlevel 1 (
    echo ERROR: Failed to create virtual environment
    pause
    exit /b 1
)

echo Activating virtual environment...
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)

echo Upgrading pip...
python -m pip install --upgrade pip

echo Installing dependencies (this may take several minutes)...
echo Trying minimal requirements first...
pip install -r requirements-minimal.txt
if errorlevel 1 (
    echo Minimal requirements failed, trying full requirements...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies
        echo Try manually installing: pip install torch torchvision insightface onnxruntime
        pause
        exit /b 1
    )
)

echo Initializing database...
python -c "from db import init_db; init_db(); print('Database initialized successfully')"
if errorlevel 1 (
    echo ERROR: Failed to initialize database
    pause
    exit /b 1
)

echo ============================================
echo Installation completed successfully!
echo ============================================
echo.
echo To run the application:
echo 1. Activate the environment: .venv\Scripts\activate
echo 2. Run the app: python app_modern.py
echo.
echo To enroll people:
echo python enroll.py --name PersonName /path/to/images/
echo.
pause
