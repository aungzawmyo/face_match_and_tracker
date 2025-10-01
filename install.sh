#!/bin/bash
# FaceScannerPro Installation Script for Linux/Mac
# This script will set up the complete environment

echo "============================================"
echo "FaceScannerPro Installation Script"
echo "============================================"

# Check Python installation
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.8+ first"
    exit 1
fi

echo "Python found: $(python3 --version)"

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv .venv
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to create virtual environment"
    exit 1
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to activate virtual environment"
    exit 1
fi

# Upgrade pip
echo "Upgrading pip..."
python -m pip install --upgrade pip

# Install dependencies
echo "Installing dependencies (this may take several minutes)..."
echo "Trying minimal requirements first..."
pip install -r requirements-minimal.txt
if [ $? -ne 0 ]; then
    echo "Minimal requirements failed, trying full requirements..."
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to install dependencies"
        echo "Try manually installing: pip install torch torchvision insightface onnxruntime"
        exit 1
    fi
fi

# Initialize database
echo "Initializing database..."
python -c "from db import init_db; init_db(); print('Database initialized successfully')"
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to initialize database"
    exit 1
fi

echo "============================================"
echo "Installation completed successfully!"
echo "============================================"
echo ""
echo "To run the application:"
echo "1. Activate the environment: source .venv/bin/activate"
echo "2. Run the app: python app_modern.py"
echo ""
echo "To enroll people:"
echo "python enroll.py --name PersonName /path/to/images/"
echo ""
