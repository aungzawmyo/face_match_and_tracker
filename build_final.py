#!/usr/bin/env python3
"""
Final Build Script for FaceScannerPro
Comprehensive executable builder with proper path handling and extensive dependencies
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
    print("🚀 FACESCANNERPRO FINAL BUILD SYSTEM")
    print("=" * 70)
    print("🎯 Production Ready Executable")
    print("✅ Fixed Path Handling")
    print("=" * 70)

def check_virtual_env():
    """Check if virtual environment is active"""
    venv_active = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    if venv_active:
        print("✅ Virtual environment is active")
    else:
        print("❌ Virtual environment is not active")
        print("Please activate virtual environment first:")
        print("  .venv\\Scripts\\Activate.ps1")
        sys.exit(1)

def clean_build():
    """Clean previous build artifacts"""
    print("🧹 Cleaning previous build...")
    
    # Kill any running instances first
    try:
        subprocess.run(['taskkill', '/f', '/im', 'FaceScannerPro.exe'], 
                      capture_output=True, timeout=10)
        print("   Terminated any running instances")
    except:
        pass
    
    # Wait a moment for processes to fully terminate
    import time
    time.sleep(2)
    
    dirs_to_clean = ['build', 'dist', '__pycache__']
    files_to_clean = glob.glob('*.spec')
    
    for directory in dirs_to_clean:
        if os.path.exists(directory):
            try:
                shutil.rmtree(directory)
                print(f"   Removed {directory}")
            except PermissionError:
                print(f"   Warning: Could not remove {directory} (files may be in use)")
                # Try to remove individual files
                for root, dirs, files in os.walk(directory):
                    for file in files:
                        try:
                            os.chmod(os.path.join(root, file), 0o777)
                            os.remove(os.path.join(root, file))
                        except:
                            pass
                try:
                    shutil.rmtree(directory)
                except:
                    print(f"   Warning: {directory} may still contain some files")
            
    for file_path in files_to_clean:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"   Removed {file_path}")
            except PermissionError:
                print(f"   Warning: Could not remove {file_path}")
    
    print("   Cleanup completed")

def find_binary_files():
    """Find binary files with proper path handling"""
    print("🔍 Scanning for binary files...")
    
    venv_path = Path(sys.prefix)
    lib_path = venv_path / "Lib" / "site-packages"
    
    binary_extensions = ['.dll', '.pyd', '.so']
    binaries = []
    
    for root, dirs, files in os.walk(lib_path):
        for file in files:
            if any(file.endswith(ext) for ext in binary_extensions):
                src_path = Path(root) / file
                # Convert to relative path from lib_path
                rel_path = src_path.relative_to(lib_path)
                # Get the package directory
                package_dir = str(rel_path.parts[0])
                if len(rel_path.parts) > 1:
                    package_dir = str(Path(*rel_path.parts[:-1]))
                
                # Use forward slashes for PyInstaller
                src_str = str(src_path).replace('\\', '/')
                dst_str = package_dir.replace('\\', '/')
                
                binaries.append((src_str, dst_str))
    
    print(f"📦 Found {len(binaries)} binary files")
    return binaries

def find_data_directories():
    """Find data directories for packages"""
    print("🔍 Scanning for data directories...")
    
    venv_path = Path(sys.prefix)
    lib_path = venv_path / "Lib" / "site-packages"
    
    packages_with_data = [
        'insightface', 'onnx', 'onnxruntime', 'torch', 'torchvision', 'torchaudio',
        'sklearn', 'scipy', 'numpy', 'PIL', 'cv2', 'albumentations', 'pydantic',
        'deep_sort_realtime', 'matplotlib', 'tqdm', 'requests', 'urllib3', 'certifi',
        'sympy', 'networkx', 'imageio', 'joblib', 'skimage'
    ]
    
    datas = []
    for package in packages_with_data:
        package_path = lib_path / package
        if package_path.exists():
            # Use forward slashes for PyInstaller
            src_str = str(package_path).replace('\\', '/')
            datas.append((src_str, package))
            print(f"  ✅ {package}")
        else:
            print(f"  ❌ {package} (not found)")
    
    print(f"📦 Found {len(datas)} data directories")
    return datas

def create_spec_file(binaries, datas):
    """Create PyInstaller spec file with proper formatting"""
    print("✅ Creating production spec file...")
    
    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# Hidden imports for AI/ML packages
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
    'albumentations',
    'pydantic',
    'deep_sort_realtime',
    'matplotlib',
    'tqdm',
    'requests',
    'urllib3',
    'certifi',
    'sympy',
    'networkx',
    'imageio',
    'joblib',
    'skimage',
    'pkg_resources.py2_warn',
]

# Binary files
binaries = [
'''
    
    # Add binaries with proper formatting
    for i, (src, dst) in enumerate(binaries):
        spec_content += f'    ("{src}", "{dst}"),\n'
    
    spec_content += ']\n\n# Data files\ndatas = [\n'
    
    # Add data directories
    for src, dst in datas:
        spec_content += f'    ("{src}", "{dst}"),\n'
    
    spec_content += ''']

a = Analysis(
    ['app_modern.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='FaceScannerPro',
)
'''
    
    spec_file = 'FaceScannerPro_FINAL.spec'
    with open(spec_file, 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    print(f"   📝 Created {spec_file}")
    print(f"   📦 {len(binaries)} binaries included")
    print(f"   📁 {len(datas)} data directories included")
    
    return spec_file

def build_executable(spec_file):
    """Build the executable using PyInstaller"""
    print("🔨 Building production executable...")
    
    # Ensure no processes are using the output directory
    try:
        subprocess.run(['taskkill', '/f', '/im', 'FaceScannerPro.exe'], 
                      capture_output=True, timeout=10)
    except:
        pass
    
    # Wait for processes to terminate
    import time
    time.sleep(3)
    
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--clean',
        '--noconfirm',
        '--distpath', 'dist_new',  # Use different output directory
        spec_file
    ]
    
    print(f"🚀 Running: {' '.join(cmd)}")
    print("⏳ Building... (this may take several minutes)")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        
        if result.returncode == 0:
            print("✅ BUILD SUCCESSFUL!")
            
            # Check output
            dist_dir = Path('dist_new') / 'FaceScannerPro'
            if dist_dir.exists():
                exe_file = dist_dir / 'FaceScannerPro.exe'
                if exe_file.exists():
                    size_mb = exe_file.stat().st_size / (1024 * 1024)
                    
                    # Move to final location
                    final_dist = Path('dist')
                    if final_dist.exists():
                        try:
                            shutil.rmtree(final_dist)
                        except:
                            pass
                    
                    shutil.move('dist_new', 'dist')
                    
                    print(f"📁 Output directory: dist/FaceScannerPro")
                    print(f"🎯 Executable: dist/FaceScannerPro/FaceScannerPro.exe")
                    print(f"📊 Size: {size_mb:.1f} MB")
                    return True
                else:
                    print("❌ Executable file not found!")
            else:
                print("❌ Output directory not found!")
                
        else:
            print("❌ BUILD FAILED!")
            print("STDOUT:", result.stdout[-1000:] if result.stdout else "No stdout")
            print("STDERR:", result.stderr[-1000:] if result.stderr else "No stderr")
            
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
    
    # Find dependencies
    binaries = find_binary_files()
    datas = find_data_directories()
    
    # Create spec file
    spec_file = create_spec_file(binaries, datas)
    
    # Build executable
    success = build_executable(spec_file)
    
    if success:
        print("\n🎉 BUILD COMPLETED SUCCESSFULLY!")
        print("✅ Ready for deployment")
        print("🚀 Run the executable from: dist/FaceScannerPro/FaceScannerPro.exe")
    else:
        print("\n❌ BUILD FAILED!")
        print("Please check the error messages above")
        sys.exit(1)

if __name__ == "__main__":
    main()
