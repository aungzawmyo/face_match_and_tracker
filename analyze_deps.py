#!/usr/bin/env python3
"""
Dependency Analysis Script for FaceScannerPro
This script analyzes all imports and dependencies to ensure complete PyInstaller builds
"""

import os
import sys
import importlib
import pkgutil

def analyze_dependencies():
    """Analyze all dependencies used by the application"""
    print("🔍 FaceScannerPro Dependency Analysis")
    print("=" * 50)
    
    # Core application modules
    app_modules = [
        'app_modern',
        'db',
        'enroll', 
        'pipeline'
    ]
    
    print("\n📋 Analyzing core application modules...")
    all_imports = set()
    
    for module_name in app_modules:
        try:
            print(f"  📄 {module_name}.py")
            # Read the file and extract imports
            with open(f"{module_name}.py", 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Simple import extraction (basic)
            lines = content.split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith('import ') or line.startswith('from '):
                    if ' import ' in line:
                        if line.startswith('from '):
                            module = line.split('from ')[1].split(' import')[0].strip()
                        else:
                            module = line.split('import ')[1].split(' ')[0].split('.')[0].strip()
                    else:
                        module = line.split('import ')[1].split(' ')[0].split('.')[0].strip()
                    
                    # Skip relative imports and built-ins
                    if not module.startswith('.') and module not in ['os', 'sys', 'threading', 'sqlite3']:
                        all_imports.add(module)
                        
        except Exception as e:
            print(f"    ❌ Error reading {module_name}: {e}")
    
    print(f"\n📦 Found {len(all_imports)} external dependencies:")
    for imp in sorted(all_imports):
        print(f"  📌 {imp}")
    
    # Test key dependencies
    print("\n🧪 Testing key dependencies...")
    key_deps = [
        'tkinter',
        'cv2', 
        'PIL',
        'numpy',
        'insightface',
        'onnxruntime',
        'scipy',
        'sklearn',
        'matplotlib',
        'albumentations'
    ]
    
    missing_deps = []
    for dep in key_deps:
        try:
            importlib.import_module(dep)
            print(f"  ✅ {dep}")
        except ImportError:
            print(f"  ❌ {dep} - MISSING!")
            missing_deps.append(dep)
    
    if missing_deps:
        print(f"\n⚠️  Missing dependencies detected: {missing_deps}")
        print("Install missing dependencies before building executable")
    else:
        print("\n✅ All key dependencies are available")
    
    # Generate PyInstaller hidden imports
    print("\n🔧 Recommended PyInstaller hidden imports:")
    hidden_imports = [
        'tkinter',
        'tkinter.ttk', 
        'tkinter.filedialog',
        'tkinter.messagebox',
        'cv2',
        'PIL',
        'PIL.Image',
        'PIL.ImageTk',
        'numpy',
        'sqlite3',
        'insightface',
        'insightface.app',
        'insightface.model_zoo',
        'onnxruntime',
        'onnxruntime.capi',
        'scipy',
        'scipy.sparse',
        'scipy.spatial',
        'scipy.ndimage',
        'sklearn',
        'sklearn.metrics',
        'matplotlib',
        'matplotlib.pyplot',
        'matplotlib.backends',
        'albumentations',
        'albumentations.augmentations',
    ]
    
    for imp in hidden_imports:
        print(f"  --hidden-import {imp}")
    
    print(f"\n📊 Build size estimate: ~250-300 MB")
    print("💡 Tip: Use --exclude-module for unused large packages like pandas")
    
    return all_imports, missing_deps

if __name__ == "__main__":
    try:
        analyze_dependencies()
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
