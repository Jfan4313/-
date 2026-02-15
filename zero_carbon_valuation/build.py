#!/usr/bin/env python3
"""
零碳项目收益评估软件 - 打包脚本

构建并打包前后端为单个可执行文件
"""
import os
import sys
import subprocess
from pathlib import Path


def run_command(cmd, description):
    """运行命令并显示输出"""
    print(f"\n{'=' * 60}")
    print(f"🔄 {description}")
    print(f"{'=' * 60}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print(result.stderr)
    if result.returncode != 0:
        print(f"❌ {description} 失败")
        return False
    print(f"✅ {description} 成功")
    return True


def check_dependencies():
    """检查依赖"""
    print("🔍 检查依赖...")

    # 检查 Python 版本
    if sys.version_info < (3, 8):
        print("❌ 需要 Python 3.8 或更高版本")
        return False

    # 检查 PyInstaller
    try:
        import PyInstaller
        print(f"✅ PyInstaller 版本: {PyInstaller.__version__}")
    except ImportError:
        print("❌ 未安装 PyInstaller，正在安装...")
        if not run_command("pip install pyinstaller", "安装 PyInstaller"):
            return False

    # 检查 npm
    result = subprocess.run("npm --version", shell=True, capture_output=True)
    if result.returncode != 0:
        print("❌ 未安装 npm")
        return False
    print(f"✅ npm 版本: {result.stdout.strip()}")

    return True


def build_frontend():
    """构建前端"""
    return run_command("python build_frontend.py", "构建前端")


def build_executable():
    """构建可执行文件"""
    return run_command(
        "pyinstaller --clean zero_carbon.spec",
        "构建可执行文件"
    )


def main():
    print("=" * 60)
    print("🚀 零碳项目收益评估软件 - 打包工具")
    print("=" * 60)

    ROOT_DIR = Path(__file__).parent

    # 检查依赖
    if not check_dependencies():
        print("\n❌ 依赖检查失败")
        sys.exit(1)

    # 构建前端
    if not build_frontend():
        print("\n❌ 前端构建失败")
        sys.exit(1)

    # 构建可执行文件
    if not build_executable():
        print("\n❌ 可执行文件构建失败")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("✨ 打包完成!")
    print("=" * 60)
    print(f"\n可执行文件位置: {ROOT_DIR / 'dist' / 'ZeroCarbonPro'}")
    print("\n使用方法:")
    print("  cd dist")
    print("  ./ZeroCarbonPro")
    print("\n访问地址: http://localhost:8000/")


if __name__ == "__main__":
    main()
