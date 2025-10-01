@echo off
echo Building FaceScannerPro Executable...
echo ===================================

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Install PyInstaller if not present
pip install pyinstaller

REM Clean previous builds
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist *.spec del *.spec

REM Build executable with all dependencies
echo Building executable... This may take several minutes...
pyinstaller --onefile --windowed --name FaceScannerPro ^
    --add-data "storage;storage" ^
    --add-data "face.db;." ^
    --add-data "migrations.sql;." ^
    --hidden-import insightface ^
    --hidden-import onnxruntime ^
    --hidden-import cv2 ^
    --hidden-import tkinter ^
    --hidden-import PIL ^
    --hidden-import sqlite3 ^
    --hidden-import scipy ^
    --hidden-import scipy.sparse ^
    --hidden-import scipy.spatial ^
    --hidden-import albumentations ^
    --hidden-import matplotlib ^
    --hidden-import matplotlib.pyplot ^
    --exclude-module pandas ^
    app_modern.py

if exist dist\FaceScannerPro.exe (
    echo.
    echo ✓ Build successful!
    echo Executable created: dist\FaceScannerPro.exe
    
    REM Get file size
    for %%A in (dist\FaceScannerPro.exe) do echo File size: %%~zA bytes
    
    echo.
    echo You can now distribute the executable from the dist folder.
    echo Test it by running: dist\FaceScannerPro.exe
    
    pause
) else (
    echo.
    echo ✗ Build failed!
    echo Check the error messages above.
    pause
)
