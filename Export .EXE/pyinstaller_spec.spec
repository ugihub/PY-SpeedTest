# -*- mode: python ; coding: utf-8 -*-

"""
PyInstaller Spec File for PY-SpeedTest
Build command: pyinstaller pyinstaller_spec.spec
"""

import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Get the script directory
spec_root = os.path.abspath(SPECPATH)

# Application metadata
app_name = 'PY-SpeedTest'
script_name = 'pyspeedtest_modern.pyw'
icon_file = 'app_icon.ico'

# Collect data files
datas = []

# Collect customtkinter data files
datas += collect_data_files('customtkinter')

# Hidden imports (packages that PyInstaller might miss)
hiddenimports = [
    'customtkinter',
    'tkinter',
    'PIL',
    'PIL._tkinter_finder',
    'matplotlib',
    'matplotlib.backends.backend_tkagg',
    'csv',
    'threading',
    'datetime',

    'supabase',
    'mistralai',
    'numpy',
    'requests',
    # Speedtest and network modules
    'speedtest',
    'urllib',
    'urllib.request',
    'urllib.error',
    'http',
    'http.client',
    'socket',
    'ssl',
]

# Collect all submodules for critical packages
hiddenimports += collect_submodules('customtkinter')
hiddenimports += collect_submodules('matplotlib')

a = Analysis(
    [script_name],  # Only main script - pyspeedtest.pyw will be auto-detected as dependency
    pathex=[spec_root],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['pyi_rth_speedtest.py'],
    excludes=[
        'tests',
        'pytest',
        'unittest',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name=app_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window (GUI app)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None, 
    entitlements_file=None,
    icon=icon_file if os.path.exists(os.path.join(spec_root, icon_file)) else None,
)

# Note: This is ONE-FILE mode
# For ONE-DIR mode, use the COLLECT section below instead:

# coll = COLLECT(
#     exe,
#     a.binaries,
#     a.zipfiles,
#     a.datas,
#     strip=False,
#     upx=True,
#     upx_exclude=[],
#     name=app_name,
# )
