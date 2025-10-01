# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['app_modern.py'],
    pathex=[],
    binaries=[],
    datas=[('D:\\Workspace\\python\\FaceScannerPro\\face_reco\\.venv\\Lib\\site-packages/insightface', 'insightface/'), ('D:\\Workspace\\python\\FaceScannerPro\\face_reco\\.venv\\Lib\\site-packages/onnxruntime', 'onnxruntime/'), ('D:\\Workspace\\python\\FaceScannerPro\\face_reco\\.venv\\Lib\\site-packages/deep_sort_realtime', 'deep_sort_realtime/')],
    hiddenimports=['insightface', 'insightface.app', 'insightface.model_zoo', 'onnx', 'onnxruntime', 'torch', 'torchvision', 'cv2', 'numpy', 'sklearn', 'scipy', 'PIL', 'deep_sort_realtime', 'pydantic', 'matplotlib', 'joblib'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='FaceScannerPro',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
