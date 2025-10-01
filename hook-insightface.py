#!/usr/bin/env python3
"""
PyInstaller hook for InsightFace package
"""
from PyInstaller.utils.hooks import collect_all, collect_data_files, collect_submodules

# Collect all InsightFace modules and data
datas, binaries, hiddenimports = collect_all('insightface')

# Additional data files that might be needed
additional_datas = collect_data_files('insightface')
datas.extend(additional_datas)

# Additional hidden imports for InsightFace
additional_imports = [
    'insightface.app',
    'insightface.model_zoo',
    'insightface.utils',
    'insightface.app.face_analysis',
    'insightface.model_zoo.arcface_onnx',
    'insightface.model_zoo.retinaface',
    'insightface.model_zoo.scrfd',
]

hiddenimports.extend(additional_imports)

# Collect all submodules
submodules = collect_submodules('insightface')
hiddenimports.extend(submodules)
