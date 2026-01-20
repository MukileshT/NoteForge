# -*- mode: python ; coding: utf-8 -*-
import os

block_cipher = None
SPEC_DIR = os.getcwd()  # Use current working directory

a = Analysis(
    ['main.py'],
    pathex=['src'],  # Add src to path
    binaries=[],
    datas=[
        ('src', 'src'),  # Include src directory
        ('config', 'config'),
        ('data', 'data'),
        ('.env.example', '.'),
    ],
    hiddenimports=[
        'paddleocr',
        'easyocr',
        'PIL',
        'PIL._tkinter_finder',
        'cv2',
        'numpy',
        'torch',
        'tkinter',
        'anthropic',
        'openai',
        'google.genai',
        'groq',
        'paddle',
        'paddle.fluid',
        'paddle.inference',
        'colorlog',
        'yaml',
        'dotenv',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['pytest', 'unittest', 'test'],
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
    name='ObsidianNotesConverter',
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
    icon=os.path.join(SPEC_DIR, 'icon.ico'),
)
