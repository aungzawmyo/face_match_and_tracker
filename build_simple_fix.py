#!/usr/bin/env python3
"""
Simple build script focused on ONNX Runtime fix
"""
import os
import subprocess
import sys

def build_simple():
    """Simple build with ONNX Runtime fix"""
    print("🔨 Building FaceScannerPro with ONNX Runtime fix...")
    
    # Get virtual environment path
    venv_path = ".venv/Lib/site-packages"
    
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onedir",  # Use directory mode for better compatibility
        "--windowed",
        "--name", "FaceScannerPro",
        "--clean",
        
        # Data files
        "--add-data", "storage;storage",
        "--add-data", "face.db;.",
        "--add-data", "migrations.sql;.",
        "--add-data", "pipeline.py;.",
        "--add-data", "db.py;.",
        "--add-data", "enroll.py;.",
        
        # ONNX Runtime binaries (crucial fix)
        "--add-binary", f"{venv_path}/onnxruntime/capi/onnxruntime.dll;onnxruntime/capi",
        "--add-binary", f"{venv_path}/onnxruntime/capi/onnxruntime_providers_shared.dll;onnxruntime/capi", 
        "--add-binary", f"{venv_path}/onnxruntime/capi/onnxruntime_pybind11_state.pyd;onnxruntime/capi",
        
        # Include entire ONNX package (required by InsightFace)
        "--add-data", f"{venv_path}/onnx;onnx",
        
        # Include entire ONNX Runtime package
        "--add-data", f"{venv_path}/onnxruntime;onnxruntime",
        
        # Include entire InsightFace package
        "--add-data", f"{venv_path}/insightface;insightface",
        
        # Hidden imports
        "--hidden-import", "onnx",
        "--hidden-import", "onnx.mapping",
        "--hidden-import", "onnx.defs",
        "--hidden-import", "insightface",
        "--hidden-import", "insightface.app", 
        "--hidden-import", "insightface.model_zoo",
        "--hidden-import", "onnxruntime",
        "--hidden-import", "onnxruntime.capi",
        "--hidden-import", "onnxruntime.capi.onnxruntime_pybind11_state",
        "--hidden-import", "cv2",
        "--hidden-import", "tkinter",
        "--hidden-import", "PIL",
        "--hidden-import", "numpy",
        "--hidden-import", "sklearn",
        
        # Exclude problematic modules to avoid build issues
        "--exclude-module", "sqlalchemy",
        "--exclude-module", "pandas",
        "--exclude-module", "matplotlib",
        "--exclude-module", "scipy",
        "--exclude-module", "torch",
        "--exclude-module", "tensorflow",
        
        # Main script
        "app_modern.py"
    ]
    
    print("Running PyInstaller...")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ Build completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed!")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return False

if __name__ == "__main__":
    build_simple()
