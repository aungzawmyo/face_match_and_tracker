#!/usr/bin/env python3
"""
Build script to create executable for FaceScannerPro
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path

def install_pyinstaller():
    """Install PyInstaller if not already installed"""
    try:
        import PyInstaller
        print("✅ PyInstaller is already installed")
    except ImportError:
        print("📦 Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("✅ PyInstaller installed successfully")

def clean_build_dirs():
    """Clean previous build directories"""
    dirs_to_clean = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print(f"🧹 Cleaning {dir_name}...")
            shutil.rmtree(dir_name)

def create_spec_file():
    """Create PyInstaller spec file with proper configuration"""
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# Analysis phase - collect all dependencies
a = Analysis(
    ['app_modern.py'],
    pathex=[],
    binaries=[
        # Include ONNX Runtime binaries explicitly
        ('.venv/Lib/site-packages/onnxruntime/capi/onnxruntime.dll', 'onnxruntime/capi'),
        ('.venv/Lib/site-packages/onnxruntime/capi/onnxruntime_providers_shared.dll', 'onnxruntime/capi'),
        ('.venv/Lib/site-packages/onnxruntime/capi/onnxruntime_pybind11_state.pyd', 'onnxruntime/capi'),
    ],
    datas=[
        # Include storage directory for face embeddings
        ('storage', 'storage'),
        # Include database file in executable directory
        ('face.db', '.'),
        # Include SQL migration file
        ('migrations.sql', '.'),
        # Include Python module files explicitly
        ('pipeline.py', '.'),
        ('db.py', '.'),
        ('enroll.py', '.'),
        # Include DeepSort model weights
        ('.venv/Lib/site-packages/deep_sort_realtime/embedder/weights', 'deep_sort_realtime/embedder/weights'),
        # Include InsightFace model data and weights
        ('.venv/Lib/site-packages/insightface', 'insightface'),
        # Include ONNX runtime data files
        ('.venv/Lib/site-packages/onnxruntime', 'onnxruntime'),
    ],
    hiddenimports=[
        # Core dependencies
        'tkinter',
        'tkinter.ttk',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'PIL',
        'PIL.Image',
        'PIL.ImageTk',
        'cv2',
        'numpy',
        'sqlite3',
        'threading',
        'os',
        'sys',
        'pathlib',
        
        # Project modules - explicitly include local modules
        'pipeline',
        'db',
        'enroll',
        
        # Face recognition dependencies
        'insightface',
        'insightface.app',
        'insightface.model_zoo',
        'insightface.utils',
        'insightface.app.face_analysis',
        'insightface.model_zoo.arcface_onnx',
        'insightface.model_zoo.retinaface',
        'insightface.model_zoo.scrfd',
        'onnxruntime',
        'onnxruntime.capi',
        'onnxruntime.capi.onnxruntime_pybind11_state',
        'onnxruntime.capi._pybind_state',
        'onnxruntime.capi.onnxruntime_inference_collection',
        'onnxruntime.capi.onnxruntime_validation',
        'sklearn',
        'sklearn.metrics',
        'sklearn.metrics.pairwise',
        
        # Deep SORT dependencies (if used)
        'deep_sort_realtime',
        
        # Additional hidden imports that might be needed
        'pkg_resources.py2_warn',
        'pkg_resources.markers',
        'scipy',
        'scipy.sparse',
        'scipy.sparse.csgraph',
        'scipy.spatial',
        'scipy.spatial.distance',
        'albumentations',
        'albumentations.augmentations',
        'albumentations.core',
        'matplotlib',
        'matplotlib.pyplot',
        'matplotlib.backends',
        'matplotlib.backends.backend_tkagg',
        
        # ONNX and model-related imports
        'onnx',
        'onnx.mapping',
        'google',
        'google.protobuf',
        'protobuf',
        
        # Additional InsightFace and face recognition imports
        'mxnet',
        'gluoncv',
        'tqdm',
        'requests',
        'urllib3',
        'certifi',
        
        # Time and timezone modules for pydantic
        'zoneinfo',
        'datetime',
        'time',
        'calendar',
        'email.utils',
        
        # Pydantic and validation modules
        'pydantic',
        'pydantic.fields',
        'pydantic.types',
        'pydantic._internal',
        'pydantic._internal._validators',
        'pydantic._migration',
        
        # Typing extensions for modern Python features
        'typing_extensions',
    ],
    hookspath=['.'],  # Look for hooks in current directory
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude unnecessary modules to reduce size - be conservative
        'pandas',
        'jupyter',
        'IPython',
        'pytest',
        # Exclude problematic Cython modules that cause extraction issues
        'Cython',
        'cython',
        'pyximport',
        # Exclude modules that cause timezone conflicts
        'babel',
        'babel.dates',
        'pytz',
        # Exclude testing frameworks
        'unittest',
        'doctest',
        'nose',
        'coverage',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Remove duplicate dependencies
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Create executable - Use directory mode to avoid Cython extraction issues
exe = EXE(
    pyz,
    a.scripts,
    [],  # Empty - don't include binaries/zipfiles/datas here for directory mode
    exclude_binaries=True,  # This creates a directory-based distribution
    name='FaceScannerPro',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # Disable UPX compression to avoid ONNX Runtime extraction issues
    console=False,  # Disable console for GUI app
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico' if os.path.exists('icon.ico') else None,
)

# Create COLLECT for directory distribution
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='FaceScannerPro',
)
'''
    
    with open('FaceScannerPro.spec', 'w') as f:
        f.write(spec_content)
    print("✅ Created FaceScannerPro.spec file")

def create_icon():
    """Create a simple icon file if none exists"""
    if not os.path.exists('icon.ico'):
        print("📝 Note: No icon.ico found. You can add a custom icon later.")
        print("   Place your icon file as 'icon.ico' in the project root.")

def build_executable():
    """Build the executable using PyInstaller"""
    print("🔨 Building executable...")
    print("This may take several minutes...")
    
    try:
        # Build using the spec file
        cmd = [sys.executable, "-m", "PyInstaller", "--clean", "FaceScannerPro.spec"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Build completed successfully!")
            print(f"📁 Executable created in: {os.path.abspath('dist')}")
            
            # Check if executable exists
            exe_path = os.path.join('dist', 'FaceScannerPro.exe')
            if os.path.exists(exe_path):
                size_mb = os.path.getsize(exe_path) / (1024 * 1024)
                print(f"📏 Executable size: {size_mb:.1f} MB")
                print(f"🎯 Executable path: {os.path.abspath(exe_path)}")
            
        else:
            print("❌ Build failed!")
            print("Error output:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Build error: {e}")
        return False
    
    return True

def create_portable_package():
    """Create a portable package with all necessary files"""
    if not os.path.exists('dist/FaceScannerPro.exe'):
        print("❌ Executable not found. Build failed.")
        return
    
    print("📦 Creating portable package...")
    
    # Create package directory
    package_dir = 'FaceScannerPro_Portable'
    if os.path.exists(package_dir):
        shutil.rmtree(package_dir)
    os.makedirs(package_dir)
    
    # Copy executable
    shutil.copy2('dist/FaceScannerPro.exe', package_dir)
    
    # Copy database if exists
    if os.path.exists('face.db'):
        shutil.copy2('face.db', package_dir)
    
    # Copy storage directory if exists
    if os.path.exists('storage'):
        shutil.copytree('storage', os.path.join(package_dir, 'storage'))
    
    # Create README for the package
    readme_content = """FaceScannerPro Portable
======================

This is a portable version of FaceScannerPro - Advanced Face Recognition System.

Files included:
- FaceScannerPro.exe - Main application
- face.db - Database file (if exists)
- storage/ - Face embeddings storage (if exists)

How to use:
1. Double-click FaceScannerPro.exe to run the application
2. The application will create a camera feed for face recognition
3. Use the People Management tab to enroll new people
4. Use the Live Recognition tab for real-time face detection

System Requirements:
- Windows 10/11 (64-bit)
- Webcam for live recognition
- At least 4GB RAM recommended

Note: On first run, Windows may show a security warning.
Click "More info" -> "Run anyway" to proceed.

For support, visit: https://github.com/aungzawmyo/face_match_and_tracker
"""
    
    with open(os.path.join(package_dir, 'README.txt'), 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print(f"✅ Portable package created: {os.path.abspath(package_dir)}")
    print("📋 Package contents:")
    for item in os.listdir(package_dir):
        item_path = os.path.join(package_dir, item)
        if os.path.isfile(item_path):
            size_mb = os.path.getsize(item_path) / (1024 * 1024)
            print(f"   📄 {item} ({size_mb:.1f} MB)")
        else:
            print(f"   📁 {item}/")

def main():
    """Main build process"""
    print("🚀 FaceScannerPro Executable Builder")
    print("=" * 40)
    
    # Change to script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    print(f"📁 Working directory: {script_dir}")
    
    # Step 1: Install PyInstaller
    install_pyinstaller()
    
    # Step 2: Clean previous builds
    clean_build_dirs()
    
    # Step 3: Create spec file
    create_spec_file()
    
    # Step 4: Check for icon
    create_icon()
    
    # Step 5: Build executable
    if build_executable():
        # Step 6: Create portable package
        create_portable_package()
        
        print("\n🎉 Build process completed successfully!")
        print("\n📋 Next steps:")
        print("1. Test the executable in dist/FaceScannerPro.exe")
        print("2. Distribute the FaceScannerPro_Portable folder")
        print("3. Users can run FaceScannerPro.exe directly")
        
    else:
        print("\n❌ Build process failed!")
        print("Check the error messages above for troubleshooting.")

if __name__ == "__main__":
    main()
