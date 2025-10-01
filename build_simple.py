#!/usr/bin/env python3
"""
Simple Build Script for FaceScannerPro
Creates a single executable file for easy distribution
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
import glob

def print_header():
    print("=" * 70)
    print("🚀 FACESCANNERPRO SIMPLE BUILD")
    print("=" * 70)
    print("📦 Single File Executable")
    print("✅ Easy Distribution")
    print("=" * 70)

def check_virtual_env():
    """Check if virtual environment is active"""
    venv_active = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    if venv_active:
        print("✅ Virtual environment is active")
    else:
        print("❌ Virtual environment is not active")
        sys.exit(1)

def clean_build():
    """Clean previous build artifacts"""
    print("🧹 Cleaning previous build...")
    dirs_to_clean = ['build', 'dist', '__pycache__']
    files_to_clean = glob.glob('*.spec')
    
    for directory in dirs_to_clean:
        if os.path.exists(directory):
            shutil.rmtree(directory)
            
    for file_path in files_to_clean:
        if os.path.exists(file_path):
            os.remove(file_path)

def build_executable():
    """Build the executable using PyInstaller with minimal options"""
    print("🔨 Building single file executable...")
    
    hidden_imports = [
        'insightface',
        'insightface.app',
        'insightface.model_zoo',
        'onnx',
        'onnxruntime',
        'torch',
        'torchvision',
        'cv2',
        'numpy',
        'sklearn',
        'scipy',
        'PIL',
        'deep_sort_realtime',
        'pkg_resources.py2_warn',
    ]
    
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--onefile',
        '--windowed',
        '--clean',
        '--noconfirm',
        '--name', 'FaceScannerPro',
        '--add-data', f'{sys.prefix}/Lib/site-packages/insightface;insightface/',
        '--add-data', f'{sys.prefix}/Lib/site-packages/onnxruntime;onnxruntime/',
        '--add-data', f'{sys.prefix}/Lib/site-packages/deep_sort_realtime;deep_sort_realtime/',
    ]
    
    # Add hidden imports
    for import_name in hidden_imports:
        cmd.extend(['--hidden-import', import_name])
    
    cmd.append('app_modern.py')
    
    print(f"🚀 Running: {' '.join(cmd[:10])}...")  # Show first part of command
    print("⏳ Building... (this may take several minutes)")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=1200)
        
        if result.returncode == 0:
            print("✅ BUILD SUCCESSFUL!")
            
            # Check output
            exe_file = Path('dist') / 'FaceScannerPro.exe'
            if exe_file.exists():
                size_mb = exe_file.stat().st_size / (1024 * 1024)
                print(f"🎯 Executable: {exe_file}")
                print(f"📊 Size: {size_mb:.1f} MB")
                return True
            else:
                print("❌ Executable file not found!")
                
        else:
            print("❌ BUILD FAILED!")
            print("STDERR:", result.stderr[-2000:])  # Show last 2000 chars
            
    except subprocess.TimeoutExpired:
        print("❌ Build timed out!")
    except Exception as e:
        print(f"❌ Build error: {e}")
    
    return False

def main():
    """Main build process"""
    print_header()
    
    # Check environment
    check_virtual_env()
    
    # Clean previous builds
    clean_build()
    
    # Build executable
    success = build_executable()
    
    if success:
        print("\n🎉 BUILD COMPLETED SUCCESSFULLY!")
        print("✅ Ready for deployment")
        print("🚀 Run the executable: dist/FaceScannerPro.exe")
        print("📝 Note: First run may be slower as it extracts dependencies")
    else:
        print("\n❌ BUILD FAILED!")
        print("Please check the error messages above")
        sys.exit(1)

if __name__ == "__main__":
    main()
