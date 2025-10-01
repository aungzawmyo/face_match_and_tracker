#!/usr/bin/env python3
"""
Robust Build Script for FaceScannerPro
Uses onefile mode to avoid permission issues with directory builds
"""

import os
import sys
import shutil
import subprocess
import time
from pathlib import Path
import glob

def print_header():
    print("=" * 70)
    print("🚀 FACESCANNERPRO ROBUST BUILD")
    print("=" * 70)
    print("📦 Single File + Folder Builds")
    print("✅ Anti-Virus Safe")
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
    
    # Kill any running instances first
    try:
        subprocess.run(['taskkill', '/f', '/im', 'FaceScannerPro.exe'], 
                      capture_output=True, timeout=10)
        subprocess.run(['taskkill', '/f', '/im', 'FaceScannerPro_Folder.exe'], 
                      capture_output=True, timeout=10)
        print("   Terminated any running instances")
    except:
        pass
    
    # Wait for processes to terminate
    time.sleep(3)
    
    dirs_to_clean = ['build', 'dist', '__pycache__']
    files_to_clean = glob.glob('*.spec')
    
    for directory in dirs_to_clean:
        if os.path.exists(directory):
            try:
                shutil.rmtree(directory)
                print(f"   Removed {directory}")
            except PermissionError:
                print(f"   Warning: Could not remove {directory} (may be in use)")
            
    for file_path in files_to_clean:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"   Removed {file_path}")
            except PermissionError:
                print(f"   Warning: Could not remove {file_path}")
    
    print("   Cleanup completed")

def build_onefile():
    """Build single file executable"""
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
        'pydantic',
        'matplotlib',
        'joblib'
    ]
    
    venv_path = Path(sys.prefix)
    lib_path = venv_path / "Lib" / "site-packages"
    
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--onefile',
        '--windowed',
        '--clean',
        '--noconfirm',
        '--name', 'FaceScannerPro',
        '--add-data', f'{lib_path}/insightface;insightface/',
        '--add-data', f'{lib_path}/onnxruntime;onnxruntime/',
        '--add-data', f'{lib_path}/deep_sort_realtime;deep_sort_realtime/',
        '--add-data', 'migrations.sql;.',  # Include migrations.sql
    ]
    
    # Add hidden imports
    for import_name in hidden_imports:
        cmd.extend(['--hidden-import', import_name])
    
    cmd.append('app_modern.py')
    
    print(f"🚀 Running PyInstaller onefile build...")
    print("⏳ Building... (this may take several minutes)")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
        
        if result.returncode == 0:
            print("✅ ONEFILE BUILD SUCCESSFUL!")
            
            exe_file = Path('dist') / 'FaceScannerPro.exe'
            if exe_file.exists():
                size_mb = exe_file.stat().st_size / (1024 * 1024)
                print(f"🎯 Single File: {exe_file}")
                print(f"📊 Size: {size_mb:.1f} MB")
                return True
            else:
                print("❌ Executable file not found!")
                
        else:
            print("❌ ONEFILE BUILD FAILED!")
            if result.stderr:
                print("Error:", result.stderr[-1000:])
            
    except subprocess.TimeoutExpired:
        print("❌ Build timed out!")
    except Exception as e:
        print(f"❌ Build error: {e}")
    
    return False

def build_folder():
    """Build folder-based executable as backup"""
    print("\n🔨 Building folder executable (backup)...")
    
    # Clean first
    if os.path.exists('build'):
        shutil.rmtree('build')
    
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--clean',
        '--noconfirm',
        '--windowed',
        '--name', 'FaceScannerPro_Folder',
        '--hidden-import', 'insightface',
        '--hidden-import', 'onnxruntime',
        '--hidden-import', 'deep_sort_realtime',
        '--add-data', 'migrations.sql;.',  # Include migrations.sql
        'app_modern.py'
    ]
    
    print("⏳ Building folder version...")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        
        if result.returncode == 0:
            print("✅ FOLDER BUILD SUCCESSFUL!")
            
            exe_file = Path('dist') / 'FaceScannerPro_Folder' / 'FaceScannerPro_Folder.exe'
            if exe_file.exists():
                size_mb = exe_file.stat().st_size / (1024 * 1024)
                print(f"🎯 Folder Version: {exe_file}")
                print(f"📊 Size: {size_mb:.1f} MB")
                return True
            else:
                print("❌ Folder executable not found!")
                
        else:
            print("❌ FOLDER BUILD FAILED!")
            if result.stderr:
                print("Error:", result.stderr[-500:])
            
    except Exception as e:
        print(f"❌ Folder build error: {e}")
    
    return False

def main():
    """Main build process"""
    print_header()
    
    # Check environment
    check_virtual_env()
    
    # Clean previous builds
    clean_build()
    
    # Build single file (primary)
    onefile_success = build_onefile()
    
    # Build folder version (backup)
    folder_success = build_folder()
    
    print("\n" + "="*70)
    print("🎯 BUILD SUMMARY")
    print("="*70)
    
    if onefile_success:
        print("✅ Single File Executable: dist/FaceScannerPro.exe")
        print("   📋 Recommended for distribution")
        print("   📝 Note: First run extracts to temp folder")
    else:
        print("❌ Single File Build Failed")
    
    if folder_success:
        print("✅ Folder Executable: dist/FaceScannerPro_Folder/FaceScannerPro_Folder.exe")
        print("   📋 Backup option with faster startup")
        print("   📝 Note: Copy entire folder to deploy")
    else:
        print("❌ Folder Build Failed")
    
    if onefile_success or folder_success:
        print("\n🎉 BUILD COMPLETED!")
        print("✅ Ready for deployment")
    else:
        print("\n❌ ALL BUILDS FAILED!")
        print("Please check error messages above")
        sys.exit(1)

if __name__ == "__main__":
    main()
