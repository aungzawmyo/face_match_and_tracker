"""
PyInstaller hook for pydantic module
"""
from PyInstaller.utils.hooks import collect_all, collect_submodules

# Collect all pydantic modules and data
datas, binaries, hiddenimports = collect_all('pydantic')

# Ensure all internal modules are included
hiddenimports += collect_submodules('pydantic._internal')
hiddenimports += collect_submodules('pydantic.dataclasses')
hiddenimports += collect_submodules('pydantic.networks')
hiddenimports += collect_submodules('pydantic.types')

# Add specific modules that might be missing
hiddenimports += [
    'pydantic._migration',
    'pydantic.fields',
    'pydantic.main',
    'pydantic.parse',
    'pydantic.schema',
    'pydantic.utils',
    'pydantic.validators',
    'pydantic.version',
    'pydantic._internal._validators',
    'pydantic._internal._core_utils',
    'pydantic._internal._fields',
    'pydantic._internal._typing_extra',
    'typing_extensions',
    'annotated_types',
]

# Handle timezone dependencies
try:
    import zoneinfo
    hiddenimports.append('zoneinfo')
except ImportError:
    try:
        import backports.zoneinfo
        hiddenimports.append('backports.zoneinfo')
    except ImportError:
        hiddenimports.append('dateutil.tz')
