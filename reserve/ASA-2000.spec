# -*- mode: python ; coding: utf-8 -*-
"""
ASA-2000 (Audio Spectrum Analyzer) PyInstaller spec file
macOS 앱 번들 생성용
"""

import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# 프로젝트 경로
project_path = os.path.dirname(os.path.abspath(SPEC))

# matplotlib 데이터 파일 수집
matplotlib_datas = collect_data_files('matplotlib')

# scipy 서브모듈 수집
scipy_hiddenimports = collect_submodules('scipy')

# ffmpeg 경로 (pydub 의존성)
ffmpeg_path = '/opt/homebrew/bin/ffmpeg'
ffprobe_path = '/opt/homebrew/bin/ffprobe'

a = Analysis(
    ['qt_scope.py'],
    pathex=[project_path],
    binaries=[
        (ffmpeg_path, '.'),
        (ffprobe_path, '.'),
    ],
    datas=[
        *matplotlib_datas,
    ],
    hiddenimports=[
        'PyQt5',
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
        'matplotlib',
        'matplotlib.backends.backend_qt5agg',
        'matplotlib.figure',
        'matplotlib.patches',
        'numpy',
        'pydub',
        'audioop',
        'pygame',
        'scipy',
        'scipy.signal',
        'PIL',
        'PIL.Image',
        *scipy_hiddenimports,
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'PySide2',
        'PySide6',
        'PyQt6',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ASA-2000',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # GUI 앱이므로 콘솔 비활성화
    disable_windowed_traceback=False,
    argv_emulation=True,  # macOS에서 파일 드래그&드롭 지원
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ASA-2000',
)

# macOS 앱 번들 생성
app = BUNDLE(
    coll,
    name='ASA-2000.app',
    icon='AppIcon.icns',
    bundle_identifier='com.tnwnrrl.asa2000',
    info_plist={
        'CFBundleName': 'ASA-2000',
        'CFBundleDisplayName': 'Audio Spectrum Analyzer ASA-2000',
        'CFBundleGetInfoString': 'Reverse Audio Analysis System',
        'CFBundleIdentifier': 'com.tnwnrrl.asa2000',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'NSHumanReadableCopyright': 'Copyright 2025',
        'NSHighResolutionCapable': True,
        'NSMicrophoneUsageDescription': 'Audio analysis requires microphone access',
        'CFBundleDocumentTypes': [
            {
                'CFBundleTypeName': 'Audio File',
                'CFBundleTypeRole': 'Viewer',
                'LSItemContentTypes': [
                    'public.mp3',
                    'public.mpeg-4-audio',
                    'com.microsoft.waveform-audio',
                ],
                'CFBundleTypeExtensions': ['mp3', 'm4a', 'wav'],
            }
        ],
        'LSMinimumSystemVersion': '10.13',
    },
)
