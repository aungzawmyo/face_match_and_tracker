#!/usr/bin/env python3
"""
PyInstaller hook for ONNX package
"""
from PyInstaller.utils.hooks import collect_all, collect_data_files, collect_dynamic_libs

# Collect all ONNX modules and data
datas, binaries, hiddenimports = collect_all('onnx')

# Collect dynamic libraries specifically
additional_binaries = collect_dynamic_libs('onnx')
binaries.extend(additional_binaries)

# Additional data files that might be needed
additional_datas = collect_data_files('onnx')
datas.extend(additional_datas)

# Additional hidden imports for ONNX
additional_imports = [
    'onnx.mapping',
    'onnx.defs',
    'onnx.helper',
    'onnx.numpy_helper',
    'onnx.backend',
    'onnx.backend.base',
]

hiddenimports.extend(additional_imports)
