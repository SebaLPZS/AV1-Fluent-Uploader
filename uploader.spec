# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['uploader.py'],
    pathex=[],
    binaries=[],
    datas=[('C:\\\\Users\\\\Sebastian\\\\AppData\\\\Local\\\\Packages\\\\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\\\\LocalCache\\\\local-packages\\\\Python312\\\\site-packages\\\\plyer\\\\platforms', 'plyer/platforms')],
    hiddenimports=['plyer.platforms.win.notification'],
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
    name='uploader',
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
    icon=['app.ico'],
)
