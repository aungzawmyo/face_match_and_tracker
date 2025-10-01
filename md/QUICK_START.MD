# FaceScannerPro Quick Start Guide

## Option 1: Using Pre-built Executable (Recommended)
1. Download the executable from the dist/ folder
2. Run `FaceScannerPro.exe` directly - no installation needed!

## Option 2: Setup from Source

### 1) Extract and Navigate
```bash
unzip face_app_starter.zip && cd face_app
```

### 2) Setup Python Environment
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate
```

### 3) Install Dependencies
```bash
# For most systems (recommended):
pip install -r requirements-minimal.txt

# For latest versions (if minimal doesn't work):
pip install -r requirements.txt

# If you encounter issues, try updating pip first:
python -m pip install --upgrade pip
```

### 4) Initialize Database
```bash
python -c "from db import init_db; init_db(); print('DB ready')"
```

### 5) Enroll People (≥5 images per person)
```bash
python enroll.py --name Alice /path/to/alice_images/
```

### 6) Start the Application
```bash
python app_modern.py
```

## Troubleshooting

### Common Issues:
- **Missing torch**: Install with `pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu`
- **ONNX Runtime issues**: Try `pip install onnxruntime --force-reinstall`
- **InsightFace problems**: Ensure you have `pip install insightface onnxruntime`

### System Requirements:
- Python 3.8+
- Windows 10/11, Linux, or macOS
- At least 4GB RAM
- 2GB free disk space
