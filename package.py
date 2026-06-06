#!/usr/bin/env python3
"""
打包脚本 - 使用 PyInstaller 打包 InkScript 为可执行文件
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def check_pyinstaller():
    """检查 PyInstaller 是否已安装"""
    try:
        import PyInstaller
        return True
    except ImportError:
        return False

def install_pyinstaller():
    """安装 PyInstaller"""
    print("正在安装 PyInstaller...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

def clean_build():
    """清理之前的构建文件"""
    print("清理构建文件...")
    dirs_to_clean = ["build", "dist", "__pycache__"]
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
    
    # 删除 .spec 文件
    for spec_file in Path(".").glob("*.spec"):
        spec_file.unlink()

def build_executable():
    """构建可执行文件"""
    print("开始构建可执行文件...")
    
    # 检查图标文件
    icon_path = "assets/icon.ico"
    icon_option = f"--icon={icon_path}" if os.path.exists(icon_path) else ""
    
    # PyInstaller 命令
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=InkScript",
        "--onefile",
        "--windowed",
        "--add-data", "novel2script/web;novel2script/web",
        "--add-data", "novel2script/prompts;novel2script/prompts",
        "--add-data", "novel2script/skills;novel2script/skills",
        "--hidden-import", "fastapi",
        "--hidden-import", "uvicorn",
        "--hidden-import", "pydantic",
        "--hidden-import", "yaml",
        "--hidden-import", "cryptography.fernet",
        "--hidden-import", "sse_starlette",
        "--collect-all", "novel2script",
        "novel2script/cli.py",
    ]
    
    if icon_option:
        cmd.insert(5, icon_option)
    
    subprocess.check_call(cmd)

def create_launcher_script():
    """创建启动脚本（用于开发环境）"""
    print("创建启动脚本...")
    
    # Windows 启动脚本
    with open("run.bat", "w") as f:
        f.write("@echo off\n")
        f.write("python -m novel2script.cli gui\n")
    
    # Unix 启动脚本
    with open("run.sh", "w") as f:
        f.write("#!/bin/bash\n")
        f.write("python -m novel2script.cli gui\n")
    
    os.chmod("run.sh", 0o755)

def main():
    """主函数"""
    print("=" * 50)
    print("InkScript 打包工具")
    print("=" * 50)
    
    # 检查 PyInstaller
    if not check_pyinstaller():
        print("未检测到 PyInstaller，正在安装...")
        install_pyinstaller()
    
    # 清理构建文件
    clean_build()
    
    # 构建可执行文件
    try:
        build_executable()
        print("\n" + "=" * 50)
        print("构建成功！")
        print("可执行文件位于: dist/InkScript.exe")
        print("=" * 50)
    except subprocess.CalledProcessError as e:
        print(f"\n构建失败: {e}")
        return 1
    
    # 创建启动脚本
    create_launcher_script()
    
    print("\n打包完成！")
    print("你可以：")
    print("  1. 运行 dist/InkScript.exe 启动应用")
    print("  2. 运行 run.bat (Windows) 或 run.sh (Unix) 在开发环境中启动")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
