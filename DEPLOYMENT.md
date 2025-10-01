# FaceScannerPro - Deployment Guide

## 📦 What's New in the Updated Requirements

The `requirements.txt` file has been completely updated to include **ALL** necessary dependencies for FaceScannerPro to work on other computers. The previous version was missing critical packages like PyTorch, which caused failures when deploying to new systems.

### 🔧 Key Additions to requirements.txt:

1. **PyTorch Stack**: `torch`, `torchvision`, `torchaudio` - Essential for neural networks
2. **Extended Computer Vision**: `scikit-image`, `opencv-python-headless` 
3. **Missing Utilities**: `pydantic`, `joblib`, `tqdm`, `networkx`, `sympy`
4. **Network Libraries**: `requests`, `urllib3`, `certifi`
5. **Data Processing**: `PyYAML`, `protobuf`, `packaging`

## 🚀 Deployment Options

### Option 1: Pre-built Executable (Recommended)
- **Single File**: `dist/FaceScannerPro.exe` (268 MB)
- **Folder Version**: `dist/FaceScannerPro_Folder/` (faster startup)
- **No installation required** - just copy and run!

### Option 2: Source Installation
Use the provided installation scripts for automatic setup:

#### Windows:
```batch
install.bat
```

#### Linux/Mac:
```bash
chmod +x install.sh
./install.sh
```

#### Manual Installation:
```bash
# Create environment
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Install dependencies (choose one)
pip install -r requirements-minimal.txt  # Conservative versions
pip install -r requirements.txt          # Latest versions

# Initialize database
python -c "from db import init_db; init_db(); print('DB ready')"

# Run application
python app_modern.py
```

## 🧪 Testing Installation

Run the dependency test to verify everything works:
```bash
python test_all_dependencies.py
```

This will check all 27+ required packages and test basic functionality.

## ⚠️ Common Issues & Solutions

### 1. PyTorch Installation Problems
```bash
# For CPU-only systems (most common)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
```

### 2. ONNX Runtime Issues
```bash
pip install onnxruntime --force-reinstall
```

### 3. InsightFace Problems
```bash
pip install insightface onnxruntime numpy>=1.20.0
```

### 4. OpenCV Issues
```bash
pip uninstall opencv-python opencv-python-headless
pip install opencv-python
```

### 5. Permission Errors (Windows)
- Run terminal as Administrator
- Disable antivirus temporarily during installation

### 6. Network/Proxy Issues
```bash
pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -r requirements.txt
```

## 📋 System Requirements

- **Python**: 3.8 or higher (3.9+ recommended)
- **RAM**: Minimum 4GB (8GB recommended)
- **Storage**: 2GB free space for dependencies
- **OS**: Windows 10/11, Ubuntu 18.04+, macOS 10.14+

## 🔍 File Structure After Installation

```
FaceScannerPro/
├── app_modern.py          # Main application
├── db.py                  # Database handling
├── enroll.py             # Face enrollment
├── pipeline.py           # Face detection pipeline
├── requirements.txt      # Full dependencies
├── requirements-minimal.txt  # Conservative versions
├── migrations.sql        # Database schema
├── install.bat          # Windows installer
├── install.sh           # Linux/Mac installer
├── test_all_dependencies.py  # Dependency tester
├── dist/                # Pre-built executables
│   ├── FaceScannerPro.exe
│   └── FaceScannerPro_Folder/
└── .venv/               # Virtual environment
```

## 🎯 Why the Updated Requirements Matter

The original `requirements.txt` only had 11 packages, but FaceScannerPro actually needs 27+ packages to work correctly. The missing packages (especially PyTorch) caused the application to fail when installed on fresh systems.

### Before (11 packages):
- Missing PyTorch, pydantic, networking libs
- Failed on new installations
- Required manual dependency hunting

### After (27+ packages):
- Complete dependency list
- Tested on fresh environments  
- Automated installation scripts
- Comprehensive testing tools

## ✅ Validation

This updated requirements.txt has been tested and validates that all 27 core dependencies work correctly:

```
Dependencies Test: 27/27 modules working
🎉 EXCELLENT! All critical dependencies are working!
🌟 PERFECT! Every single dependency is working!
```

The executable versions are also rebuilt with the missing `migrations.sql` file to prevent database initialization errors.

## 📞 Support

If you encounter issues:
1. Run `python test_all_dependencies.py` for diagnosis
2. Try the minimal requirements first: `pip install -r requirements-minimal.txt`  
3. Check the troubleshooting section above
4. Use the pre-built executable if source installation fails
