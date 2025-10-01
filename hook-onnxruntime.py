#!/usr/bin/env python3
"""
PyInstaller hook for ONNX Runtime package
"""
from PyInstaller.utils.hooks import collect_all, collect_data_files, collect_dynamic_libs

# Collect all ONNX Runtime modules and data
datas, binaries, hiddenimports = collect_all('onnxruntime')

# Collect dynamic libraries specifically
additional_binaries = collect_dynamic_libs('onnxruntime')
binaries.extend(additional_binaries)

# Additional data files that might be needed
additional_datas = collect_data_files('onnxruntime')
datas.extend(additional_datas)

# Additional hidden imports for ONNX Runtime
additional_imports = [
    'onnxruntime.capi',
    'onnxruntime.capi.onnxruntime_pybind11_state',
    'onnxruntime.capi._pybind_state',
    'onnxruntime.capi.onnxruntime_inference_collection',
    'onnxruntime.capi.onnxruntime_validation',
    'onnxruntime.backend',
    'onnxruntime.backend.backend',
]

hiddenimports.extend(additional_imports)
