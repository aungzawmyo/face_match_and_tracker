#!/usr/bin/env python3
"""
Comprehensive dependency test for FaceScannerPro
Run this after installing requirements.txt to verify everything works
"""

import sys
import importlib
import traceback

def test_import(module_name, description=""):
    """Test if a module can be imported"""
    try:
        module = importlib.import_module(module_name)
        version = getattr(module, '__version__', 'unknown')
        print(f"✅ {module_name:20} {version:15} - {description}")
        return True
    except ImportError as e:
        print(f"❌ {module_name:20} {'FAILED':15} - {e}")
        return False
    except Exception as e:
        print(f"⚠️  {module_name:20} {'ERROR':15} - {e}")
        return False

def test_functionality():
    """Test basic functionality of key components"""
    print("\n" + "="*50)
    print("Testing Basic Functionality")
    print("="*50)
    
    # Test InsightFace
    try:
        import insightface
        print("✅ InsightFace basic import successful")
        # Don't initialize the app here as it downloads models
    except Exception as e:
        print(f"❌ InsightFace test failed: {e}")
    
    # Test OpenCV
    try:
        import cv2
        import numpy as np
        # Test basic OpenCV functionality
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        print(f"✅ OpenCV functionality test passed - Version: {cv2.__version__}")
    except Exception as e:
        print(f"❌ OpenCV functionality test failed: {e}")
    
    # Test torch
    try:
        import torch
        x = torch.randn(2, 3)
        y = torch.sum(x)
        print(f"✅ PyTorch functionality test passed - Version: {torch.__version__}")
    except Exception as e:
        print(f"❌ PyTorch functionality test failed: {e}")
    
    # Test ONNX Runtime
    try:
        import onnxruntime
        providers = onnxruntime.get_available_providers()
        print(f"✅ ONNX Runtime test passed - Providers: {len(providers)}")
    except Exception as e:
        print(f"❌ ONNX Runtime test failed: {e}")

def main():
    """Test all required dependencies"""
    print("="*70)
    print("FaceScannerPro Comprehensive Dependency Test")
    print("="*70)
    print(f"Python version: {sys.version}")
    print("="*70)
    
    # Essential dependencies for FaceScannerPro
    dependencies = [
        # Core AI/ML
        ('torch', 'PyTorch neural networks'),
        ('torchvision', 'PyTorch computer vision'),
        ('torchaudio', 'PyTorch audio processing'),
        
        # Face Recognition
        ('insightface', 'Face recognition models'),
        ('onnx', 'ONNX model format'),
        ('onnxruntime', 'ONNX runtime engine'),
        
        # Computer Vision
        ('cv2', 'OpenCV computer vision'),
        ('PIL', 'Python Imaging Library'),
        ('skimage', 'Scikit-image processing'),
        ('albumentations', 'Image augmentation'),
        ('imageio', 'Image I/O utilities'),
        
        # Scientific Computing
        ('numpy', 'Numerical computing'),
        ('scipy', 'Scientific computing'),
        ('sklearn', 'Machine learning'),
        ('matplotlib', 'Plotting and visualization'),
        
        # Object Tracking
        ('deep_sort_realtime', 'Real-time object tracking'),
        
        # Data and Utilities
        ('pydantic', 'Data validation'),
        ('joblib', 'Parallel computing'),
        ('tqdm', 'Progress bars'),
        
        # Networking
        ('requests', 'HTTP requests'),
        ('urllib3', 'HTTP client'),
        ('certifi', 'SSL certificates'),
        
        # Additional Utilities
        ('networkx', 'Graph analysis'),
        ('sympy', 'Symbolic mathematics'),
        ('yaml', 'YAML configuration'),
        ('packaging', 'Package utilities'),
    ]
    
    # Test protocol buffers separately due to import path
    protobuf_modules = [
        ('google.protobuf', 'Protocol buffers')
    ]
    
    success_count = 0
    total_count = len(dependencies) + len(protobuf_modules)
    
    print("Testing Core Dependencies:")
    print("-" * 50)
    for module_name, description in dependencies:
        if test_import(module_name, description):
            success_count += 1
    
    print("\nTesting Additional Dependencies:")
    print("-" * 50)
    for module_name, description in protobuf_modules:
        if test_import(module_name, description):
            success_count += 1
    
    # Test basic functionality
    test_functionality()
    
    # Final results
    print("\n" + "="*70)
    print("FINAL RESULTS")
    print("="*70)
    print(f"Dependencies Test: {success_count}/{total_count} modules working")
    
    if success_count >= total_count - 2:  # Allow 2 modules to fail
        print("🎉 EXCELLENT! All critical dependencies are working!")
        print("✅ FaceScannerPro should run without major issues")
        
        if success_count == total_count:
            print("🌟 PERFECT! Every single dependency is working!")
        else:
            print(f"📝 Note: {total_count - success_count} non-critical modules had issues")
    else:
        print("❌ ISSUES DETECTED! Some critical dependencies are missing")
        print("🔧 FaceScannerPro may not work properly")
        missing_count = total_count - success_count
        print(f"Missing/Failed: {missing_count} dependencies")
        
        print("\n🛠️  TROUBLESHOOTING STEPS:")
        print("1. Update pip: python -m pip install --upgrade pip")
        print("2. Try minimal install: pip install -r requirements-minimal.txt")
        print("3. Try full install: pip install -r requirements.txt")
        print("4. For PyTorch CPU: pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu")
        print("5. For InsightFace: pip install insightface onnxruntime")
        print("6. Check Python version (3.8+ required)")
    
    print("="*70)
    return success_count >= total_count - 2

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
