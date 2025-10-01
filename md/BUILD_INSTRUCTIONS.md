# Quick Build Instructions for FaceScannerPro

## Method 1: Using the Build Script (Recommended)

Run the automated build script:
```bash
python build_exe.py
```

This will:
- Install PyInstaller if needed
- Create the executable with all dependencies
- Package everything into a portable folder

## Method 2: Manual PyInstaller Commands

### Basic build:
```bash
pyinstaller --onefile --windowed --name FaceScannerPro app_modern.py
```

### Advanced build with all dependencies:
```bash
pyinstaller --onedir --windowed --name FaceScannerPro ^
    --add-data "storage;storage" ^
    --add-data "*.db;." ^
    --add-data "migrations.sql;." ^
    --add-binary ".venv/Lib/site-packages/onnxruntime/capi/onnxruntime.dll;onnxruntime/capi" ^
    --add-binary ".venv/Lib/site-packages/onnxruntime/capi/onnxruntime_providers_shared.dll;onnxruntime/capi" ^
    --add-binary ".venv/Lib/site-packages/onnxruntime/capi/onnxruntime_pybind11_state.pyd;onnxruntime/capi" ^
    --hidden-import insightface ^
    --hidden-import insightface.app ^
    --hidden-import onnxruntime ^
    --hidden-import onnxruntime.capi ^
    --hidden-import cv2 ^
    --hidden-import tkinter ^
    --hidden-import PIL ^
    --exclude-module matplotlib ^
    --exclude-module scipy ^
    app_modern.py
```

## Method 3: Using Spec File

1. Create spec file:
```bash
pyinstaller --onefile --windowed --name FaceScannerPro app_modern.py
```

2. Edit the generated .spec file as needed

3. Build using spec:
```bash
pyinstaller FaceScannerPro.spec
```

## Troubleshooting

### Common Issues:

1. **Missing modules**: Add to hidden imports
2. **Large file size**: Use `--exclude-module` for unused packages
3. **Slow startup**: Use `--onedir` instead of `--onefile`
4. **Missing data files**: Use `--add-data` to include them
5. **ONNX Runtime errors**: 
   - Ensure ONNX Runtime binaries are included with `--add-binary`
   - Use `--onedir` mode (not `--onefile`) for better compatibility
   - Include ONNX Runtime hidden imports: `onnxruntime`, `onnxruntime.capi`
6. **InsightFace import errors**:
   - Include all InsightFace submodules: `insightface.app`, `insightface.model_zoo`
   - Ensure ONNX Runtime is working first (InsightFace depends on it)

### Size Optimization:
- Use virtual environment with only required packages
- Exclude unnecessary modules
- Use UPX compression (if available)

### Testing:
1. Test on a clean machine without Python
2. Check all features work correctly
3. Verify camera access permissions

## Distribution
- Include README.txt with usage instructions
- Include any required data files
- Test on target machines before distribution
