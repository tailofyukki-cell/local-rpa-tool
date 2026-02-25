# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files

# --- PyInstaller設定 ---

# ベースディレクトリ
base_dir = Path(__file__).parent
src_dir = base_dir / "src"

# 実行ファイル名
exe_name = "LocalRPA"

# --- データファイルの収集 ---
# PySide6のデータファイルを収集
datas = collect_data_files("PySide6")

# OpenCVのデータファイルを収集（Windows用）
if sys.platform == "win32":
    import cv2
    opencv_dir = Path(cv2.__file__).parent
    datas.append((str(opencv_dir / "data"), "cv2/data"))

# --- EXEビルド設定 ---

a = Analysis(
    [str(src_dir / "main.py")],
    pathex=[str(base_dir)],
    binaries=[],
    datas=datas,
    hiddenimports=[
        "PySide6.QtCore",
        "PySide6.QtGui",
        "PySide6.QtWidgets",
        "PySide6.QtSvg",
        "cv2",
        "numpy",
        "pyautogui",
        "pywin32",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name=exe_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # GUIアプリケーションなのでコンソールは非表示
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # ここにアイコンファイルのパスを指定できます
)
