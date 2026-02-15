#!/usr/bin/env python3
"""
构建前端并复制到后端静态目录
"""
import os
import sys
import shutil
from pathlib import Path

# 配置路径
FRONTEND_DIR = Path("/Users/su/Desktop/code/项目/零碳项目收益评估软件前端")
BACKEND_STATIC_DIR = Path(__file__).parent / "api" / "static"

def build_frontend():
    """构建前端"""
    print("=" * 50)
    print("开始构建前端...")
    print("=" * 50)

    # 进入前端目录
    os.chdir(FRONTEND_DIR)

    # 运行构建
    import subprocess
    result = subprocess.run(
        ["npm", "run", "build"],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print("❌ 前端构建失败:")
        print(result.stderr)
        return False

    print("✅ 前端构建成功")
    return True


def copy_to_static():
    """复制构建产物到后端静态目录"""
    print("\n" + "=" * 50)
    print("复制静态文件...")
    print("=" * 50)

    dist_dir = FRONTEND_DIR / "dist"

    if not dist_dir.exists():
        print(f"❌ 构建目录不存在: {dist_dir}")
        return False

    # 清空目标目录
    if BACKEND_STATIC_DIR.exists():
        shutil.rmtree(BACKEND_STATIC_DIR)
    BACKEND_STATIC_DIR.mkdir(parents=True, exist_ok=True)

    # 复制所有文件
    for item in dist_dir.iterdir():
        if item.is_dir():
            shutil.copytree(item, BACKEND_STATIC_DIR / item.name)
        else:
            shutil.copy2(item, BACKEND_STATIC_DIR / item.name)

    print(f"✅ 静态文件已复制到: {BACKEND_STATIC_DIR}")
    return True


def main():
    print("🚀 零碳项目收益评估软件 - 前端构建脚本\n")

    # 检查前端目录
    if not FRONTEND_DIR.exists():
        print(f"❌ 前端目录不存在: {FRONTEND_DIR}")
        sys.exit(1)

    # 构建前端
    if not build_frontend():
        sys.exit(1)

    # 复制到静态目录
    if not copy_to_static():
        sys.exit(1)

    print("\n" + "=" * 50)
    print("✨ 构建完成!")
    print("=" * 50)
    print(f"\n静态文件位置: {BACKEND_STATIC_DIR}")
    print("现在可以运行: python api/main.py")


if __name__ == "__main__":
    main()
