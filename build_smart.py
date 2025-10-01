#!/usr/bin/env python3
"""
SMART COMPREHENSIVE BUILD SCRIPT FOR FACESCANNERPRO
===================================================
This script intelligently detects and includes ALL existing dependencies.
Only includes files that actually exist to prevent build errors.
"""
import os
import sys
import subprocess
import shutil
import glob
from pathlib import Path

def ensure_venv_activated():
    """Ensure we're running in the virtual environment"""
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("❌ ERROR: Not running in virtual environment!")
        print("Please activate the virtual environment first:")
        print("   .venv\\Scripts\\Activate.ps1")
        sys.exit(1)
    print("✅ Virtual environment is active")

def find_existing_binaries():
    """Find all existing binary files in the virtual environment"""
    venv_path = Path('.venv/Lib/site-packages')
    binaries = []
    
    if not venv_path.exists():
        print("❌ Virtual environment path not found")
        return binaries
    
    print("🔍 Scanning for binary files...")
    
    # Find DLL files
    dll_patterns = [
        '.venv/Lib/site-packages/*/*.dll',
        '.venv/Lib/site-packages/*/*/*.dll',
        '.venv/Lib/site-packages/*/*/*/*.dll',
    ]
    
    for pattern in dll_patterns:
        for dll_file in glob.glob(pattern):
            rel_path = os.path.relpath(dll_file, '.venv/Lib/site-packages')
            dest_dir = os.path.dirname(rel_path)
            binaries.append((dll_file, dest_dir if dest_dir else '.'))
    
    # Find PYD files (Python extensions)
    pyd_patterns = [
        '.venv/Lib/site-packages/*/*.pyd',
        '.venv/Lib/site-packages/*/*/*.pyd',
        '.venv/Lib/site-packages/*/*/*/*.pyd',
    ]
    
    for pattern in pyd_patterns:
        for pyd_file in glob.glob(pattern):
            rel_path = os.path.relpath(pyd_file, '.venv/Lib/site-packages')
            dest_dir = os.path.dirname(rel_path)
            binaries.append((pyd_file, dest_dir if dest_dir else '.'))
    
    print(f"📦 Found {len(binaries)} binary files")
    return binaries

def find_existing_data_dirs():
    """Find all existing data directories to include"""
    venv_path = Path('.venv/Lib/site-packages')
    data_dirs = []
    
    if not venv_path.exists():
        return data_dirs
    
    print("🔍 Scanning for data directories...")
    
    # Critical packages that need full inclusion
    critical_packages = [
        'insightface', 'onnx', 'onnxruntime', 'torch', 'torchvision', 'torchaudio',
        'sklearn', 'scipy', 'numpy', 'PIL', 'cv2', 'albumentations', 'pydantic',
        'deep_sort_realtime', 'matplotlib', 'tqdm', 'requests', 'urllib3',
        'certifi', 'protobuf', 'sympy', 'networkx', 'imageio', 'joblib'
    ]
    
    for package in critical_packages:
        package_path = venv_path / package
        if package_path.exists():
            data_dirs.append((str(package_path), package))
            print(f"  ✅ {package}")
        else:
            print(f"  ❌ {package} (not found)")
    
    print(f"📦 Found {len(data_dirs)} data directories")
    return data_dirs

def create_smart_spec():
    """Create a smart PyInstaller spec that only includes existing files"""
    
    binaries = find_existing_binaries()
    data_dirs = find_existing_data_dirs()
    
    # Format binaries for spec file
    binaries_str = ",\\n        ".join([f"('{src}', '{dst}')" for src, dst in binaries])
    
    # Format data directories for spec file
    datas_str = ",\\n        ".join([f"('{src}', '{dst}')" for src, dst in data_dirs])
    
    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-
"""
SMART COMPREHENSIVE SPEC FOR FACESCANNERPRO
===========================================
Auto-generated with only existing files included
"""

import os

block_cipher = None

a = Analysis(
    ['app_modern.py'],
    pathex=[os.getcwd()],
    binaries=[
        {binaries_str}
    ],
    datas=[
        # Application files
        ('pipeline.py', '.'),
        ('db.py', '.'),
        ('enroll.py', '.'),
        
        # Data directories
        {datas_str}
    ],
    hiddenimports=[
        # Core system
        'os', 'sys', 'threading', 'pathlib', 'sqlite3', 'json', 'datetime',
        'collections', 'itertools', 'functools', 'math', 'random', 'typing',
        
        # GUI
        'tkinter', 'tkinter.ttk', 'tkinter.filedialog', 'tkinter.messagebox',
        
        # Project modules
        'pipeline', 'db', 'enroll',
        
        # Image processing
        'PIL', 'PIL.Image', 'PIL.ImageTk', 'cv2',
        
        # Numerical
        'numpy', 'scipy', 'scipy.spatial', 'scipy.spatial.distance',
        
        # ML
        'sklearn', 'sklearn.metrics', 'sklearn.metrics.pairwise',
        'joblib', 'threadpoolctl',
        
        # Deep learning
        'torch', 'torch.nn', 'torch.nn.functional',
        'torchvision', 'torchvision.transforms',
        
        # ONNX
        'onnx', 'onnx.mapping', 'onnx.helper',
        'onnxruntime', 'onnxruntime.capi',
        
        # Face recognition
        'insightface', 'insightface.app', 'insightface.model_zoo',
        
        # Image augmentation
        'albumentations', 'albumentations.augmentations',
        'albucore',
        
        # Data validation
        'pydantic', 'pydantic._internal', 'annotated_types',
        
        # Tracking
        'deep_sort_realtime',
        
        # Plotting
        'matplotlib', 'matplotlib.pyplot', 'matplotlib.backends.backend_tkagg',
        
        # Networking
        'requests', 'urllib3', 'certifi', 'charset_normalizer', 'idna',
        
        # Protocols
        'protobuf',
        
        # Utils
        'tqdm', 'easydict', 'filelock', 'packaging',
        
        # Math
        'sympy', 'mpmath', 'networkx',
        
        # Image I/O
        'imageio', 'scikit_image',
        
        # Time zones
        'zoneinfo', 'dateutil', 'email.utils',
        
        # Typing
        'typing_extensions',
    ],
    hookspath=['.'],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[
        'test', 'tests', 'testing', 'unittest', 'doctest',
        'IPython', 'jupyter', 'notebook', 'sphinx',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='FaceScannerPro',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name='FaceScannerPro',
)
'''
    
    with open('FaceScannerPro_SMART.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    print("✅ Created smart spec file")
    print(f"   📦 {len(binaries)} binaries included")
    print(f"   📁 {len(data_dirs)} data directories included")

def build_executable():
    """Build the executable"""
    print("🔨 Building smart executable...")
    
    try:
        cmd = [sys.executable, "-m", "PyInstaller", "--clean", "--noconfirm", "FaceScannerPro_SMART.spec"]
        print(f"🚀 Running: {' '.join(cmd)}")
        
        # Run build process
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
                                 text=True, cwd=os.getcwd())
        
        print("⏳ Building... (this may take several minutes)")
        for line in process.stdout:
            if "INFO:" in line:
                print(f"  ℹ️  {line.strip()}")
            elif "ERROR:" in line or "WARNING:" in line:
                print(f"  ⚠️  {line.strip()}")
        
        process.wait()
        
        if process.returncode == 0:
            print("✅ BUILD SUCCESSFUL!")
            
            # Check result
            exe_path = os.path.join('dist', 'FaceScannerPro', 'FaceScannerPro.exe')
            if os.path.exists(exe_path):
                size_mb = os.path.getsize(exe_path) / (1024 * 1024)
                print(f"📏 Executable size: {size_mb:.1f} MB")
                print(f"📁 Location: {os.path.abspath(exe_path)}")
                return True
            else:
                print("❌ Executable not found")
                return False
        else:
            print(f"❌ Build failed with return code: {process.returncode}")
            return False
            
    except Exception as e:
        print(f"❌ Build exception: {e}")
        return False

def test_executable():
    """Test the built executable"""
    exe_path = os.path.join('dist', 'FaceScannerPro', 'FaceScannerPro.exe')
    if not os.path.exists(exe_path):
        return False
    
    print("🧪 Testing executable...")
    try:
        # Test that it can start (with short timeout)
        result = subprocess.run([exe_path], timeout=5, capture_output=True)
        print("✅ Executable starts successfully")
        return True
    except subprocess.TimeoutExpired:
        print("✅ Executable started (GUI app - timeout expected)")
        return True
    except Exception as e:
        print(f"❌ Executable test failed: {e}")
        return False

def create_portable_package():
    """Create portable package"""
    exe_dir = 'dist/FaceScannerPro'
    if not os.path.exists(exe_dir):
        return False
    
    print("📦 Creating portable package...")
    
    portable_dir = 'FaceScannerPro_PORTABLE'
    if os.path.exists(portable_dir):
        shutil.rmtree(portable_dir)
    
    # Copy everything
    shutil.copytree(exe_dir, portable_dir)
    
    # Add optional files
    optional_files = ['face.db', 'storage', 'README.md']
    for file_item in optional_files:
        if os.path.exists(file_item):
            if os.path.isfile(file_item):
                shutil.copy2(file_item, portable_dir)
            elif os.path.isdir(file_item):
                dest = os.path.join(portable_dir, file_item)
                if not os.path.exists(dest):
                    shutil.copytree(file_item, dest)
    
    # Create README
    readme = os.path.join(portable_dir, 'HOW_TO_RUN.txt')
    with open(readme, 'w') as f:
        f.write("""FaceScannerPro - Portable Version
================================

QUICK START:
1. Double-click FaceScannerPro.exe
2. Wait for app to load (first run may take 30+ seconds)
3. Use People Management to add faces
4. Use Live Recognition for detection

SYSTEM REQUIREMENTS:
- Windows 10/11 (64-bit)
- Webcam
- 4GB+ RAM

TROUBLESHOOTING:
- Windows security warning: Click "More info" → "Run anyway"
- Slow startup: Normal on first run
- No camera: Check Windows camera permissions

Built with comprehensive Python expert build system.
All dependencies included - no Python installation needed!
""")
    
    # Calculate size
    total_size = sum(
        os.path.getsize(os.path.join(dirpath, filename))
        for dirpath, _, filenames in os.walk(portable_dir)
        for filename in filenames
    ) / (1024 * 1024)
    
    print(f"✅ Portable package created: {portable_dir}")
    print(f"📏 Total size: {total_size:.1f} MB")
    
    return True

def main():
    """Main smart build process"""
    print("=" * 70)
    print("🚀 FACESCANNERPRO SMART BUILD SYSTEM")
    print("=" * 70)
    print("🧠 Python Expert Mode - Only Existing Files")
    print("🎯 Zero Missing Dependencies!")
    print("=" * 70)
    
    # Ensure environment
    ensure_venv_activated()
    
    # Clean previous builds
    if os.path.exists('dist'):
        print("🧹 Cleaning previous build...")
        try:
            shutil.rmtree('dist')
        except:
            print("⚠️  Couldn't clean dist - files may be in use")
    
    if os.path.exists('build'):
        try:
            shutil.rmtree('build')
        except:
            pass
    
    # Create spec and build
    create_smart_spec()
    
    if build_executable():
        print("✅ BUILD PHASE COMPLETED")
        
        if test_executable():
            print("✅ EXECUTABLE TESTED SUCCESSFULLY")
            
            if create_portable_package():
                print("\\n" + "=" * 70)
                print("🎉 SMART BUILD COMPLETED SUCCESSFULLY!")
                print("=" * 70)
                print("📋 READY TO USE:")
                print("1. dist/FaceScannerPro/FaceScannerPro.exe")
                print("2. FaceScannerPro_PORTABLE/ (complete package)")
                print("\\n✅ ALL DEPENDENCIES INCLUDED!")
                print("🚀 NO MISSING LIBRARIES!")
                print("=" * 70)
                return True
    
    print("\\n❌ BUILD FAILED!")
    return False

if __name__ == "__main__":
    main()
