"""
PyInstaller hook for zoneinfo module compatibility
"""
from PyInstaller.utils.hooks import collect_all

# For Python 3.9+, zoneinfo is a standard library module
# For older versions, we need to include the backport
datas, binaries, hiddenimports = collect_all('zoneinfo')

# Add fallback for systems without zoneinfo
hiddenimports += [
    'zoneinfo',
    'backports.zoneinfo',  # backport package
    'dateutil.tz',        # alternative timezone implementation
]

# Include timezone data files if they exist
try:
    import zoneinfo
    # Include timezone database files
    from PyInstaller.utils.hooks import collect_data_files
    datas += collect_data_files('zoneinfo')
except ImportError:
    # Try backport
    try:
        from PyInstaller.utils.hooks import collect_data_files
        datas += collect_data_files('backports.zoneinfo')
    except:
        pass
