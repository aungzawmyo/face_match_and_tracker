#!/usr/bin/env python3
"""
Quick test script to verify imports work
"""

import sys
import os

# Add the current directory to path to find dependencies
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

try:
    print("Testing ONNX import...")
    import onnx
    print(f"✅ ONNX imported successfully: {onnx.__version__}")
    
    print("Testing ONNX Runtime import...")
    import onnxruntime
    print(f"✅ ONNX Runtime imported successfully: {onnxruntime.__version__}")
    
    print("Testing InsightFace import...")
    import insightface
    print(f"✅ InsightFace imported successfully: {insightface.__version__}")
    
    print("\n🎉 All imports successful!")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    sys.exit(1)
