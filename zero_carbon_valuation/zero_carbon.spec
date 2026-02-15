# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# 项目目录 - 使用当前工作目录
ROOT_DIR = Path.cwd()
API_DIR = ROOT_DIR / "api"
STATIC_DIR = API_DIR / "static"
MODULES_DIR = ROOT_DIR / "modules"

print(f"ROOT_DIR: {ROOT_DIR}")
print(f"API_DIR: {API_DIR}")
print(f"STATIC_DIR: {STATIC_DIR}")
print(f"MODULES_DIR: {MODULES_DIR}")

# 分析导入
a = Analysis(
    [str(API_DIR / "main.py")],
    pathex=[str(ROOT_DIR), str(API_DIR)],
    binaries=[],
    datas=[
        # 静态文件（前端）
        (str(STATIC_DIR), "api/static"),
        # 核心算法模块
        (str(MODULES_DIR), "modules"),
        # API目录完整内容
        (str(API_DIR / "__init__.py"), "api"),
        (str(API_DIR / "config.py"), "api"),
        (str(API_DIR / "models.py"), "api"),
        # 路由目录
        (str(API_DIR / "routers"), "api/routers"),
    ],
    hiddenimports=[
        'fastapi',
        'fastapi.staticfiles',
        'fastapi.responses',
        'starlette',
        'starlette.requests',
        'starlette.responses',
        'uvicorn',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.loops.auto',
        'uvicorn.lifespan.on',
        'uvicorn.logging',
        'pydantic',
        'pydantic.dataclasses',
        'pydantic.main',
        'pydantic.validators',
        'numpy',
        'pandas',
        'pandas._libs',
        'openpyxl',
        'plotly',
        'plotly.graph_objects',
        'plotly.express',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # 排除不需要的模块以减小体积
        'tkinter',
        'matplotlib',
        'IPython',
        'jupyter',
        'notebook',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# 排除不需要的二进制文件
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ZeroCarbonPro',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # 设置为False可隐藏控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # 可以添加自定义图标文件路径
)
