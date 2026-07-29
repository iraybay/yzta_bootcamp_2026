# -*- mode: python ; coding: utf-8 -*-

import sys
import os

block_cipher = None

added_files = [
    ('templates', 'templates'),
    ('static', 'static'),
    ('bulutis.db', '.'),
]

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=added_files,
    hiddenimports=[
        'flask',
        'sqlite3',
        'db_manager',
        'router',
        'router.ai',
        'router.cari',
        'router.fatura',
        'router.kasa',
        'router.main',
        'router.stok',
        'repositories',
        'repositories.cari_repository',
        'repositories.dashboard_repository',
        'repositories.db_core',
        'repositories.fatura_repository',
        'repositories.kasa_repository',
        'repositories.stok_repository',
    ],

    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='BulutIs',
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
