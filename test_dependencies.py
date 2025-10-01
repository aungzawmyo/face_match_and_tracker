#!/usr/bin/env python3
"""
Test script to verify ONNX Runtime is working in the executable
"""
import sys
import os

def test_onnx():
    """Test if ONNX can be imported"""
    try:
        print("Testing ONNX import...")
        import onnx
        print(f"✅ ONNX imported successfully - Version: {onnx.__version__}")
        print(f"   ONNX path: {onnx.__file__}")
        return True
    except Exception as e:
        print(f"❌ ONNX import failed: {e}")
        print(f"   Error type: {type(e).__name__}")
        return False

def test_onnxruntime():
    """Test if ONNX Runtime can be imported and used"""
    try:
        print("Testing ONNX Runtime import...")
        import onnxruntime
        print(f"✅ ONNX Runtime imported successfully - Version: {onnxruntime.__version__}")
        print(f"   ONNX Runtime path: {onnxruntime.__file__}")
        
        # Test if we can create a session (basic functionality test)
        providers = onnxruntime.get_available_providers()
        print(f"✅ Available providers: {providers}")
        
        return True
    except Exception as e:
        print(f"❌ ONNX Runtime import failed: {e}")
        print(f"   Error type: {type(e).__name__}")
        return False

def test_insightface():
    """Test if InsightFace can be imported"""
    try:
        print("\nTesting InsightFace import...")
        import insightface
        print(f"✅ InsightFace imported successfully - Version: {insightface.__version__}")
        
        # Test app module
        try:
            import insightface.app
            print("✅ InsightFace app module imported successfully")
            return True
        except AttributeError:
            from insightface import app
            print("✅ InsightFace app module imported via alternative method")
            return True
            
    except Exception as e:
        print(f"❌ InsightFace import failed: {e}")
        print(f"   Error type: {type(e).__name__}")
        return False

def main():
    """Main test function"""
    print("🧪 Testing Dependencies for FaceScannerPro")
    print("=" * 50)
    
    print(f"Python version: {sys.version}")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Python executable: {sys.executable}")
    
    print("\n" + "=" * 50)
    
    onnx_ok = test_onnx()
    onnx_runtime_ok = test_onnxruntime()
    insight_ok = test_insightface()
    
    print("\n" + "=" * 50)
    print("📋 Test Results:")
    print(f"   ONNX:         {'✅ PASS' if onnx_ok else '❌ FAIL'}")
    print(f"   ONNX Runtime: {'✅ PASS' if onnx_runtime_ok else '❌ FAIL'}")
    print(f"   InsightFace:  {'✅ PASS' if insight_ok else '❌ FAIL'}")
    
    if onnx_ok and onnx_runtime_ok and insight_ok:
        print("\n🎉 All dependencies are working correctly!")
        return 0
    else:
        print("\n⚠️  Some dependencies failed. Check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
