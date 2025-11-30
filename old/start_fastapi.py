#!/usr/bin/env python
"""
FastAPI 启动脚本
确保使用正确的 Python 环境和路径
"""
import sys
import os
import subprocess
from pathlib import Path

def main():
    # 设置工作目录到 backend
    backend_dir = Path(__file__).parent / "backend"
    os.chdir(backend_dir)

    # 设置 PYTHONPATH
    current_dir = Path.cwd()
    python_path = str(current_dir)

    # 构建 uvicorn 启动命令
    cmd = [
        sys.executable,  # 使用当前 Python 解释器
        "-m", "uvicorn",
        "app.main:app",
        "--reload",
        "--host", "0.0.0.0",
        "--port", "8000"
    ]

    # 设置环境变量
    env = os.environ.copy()
    env["PYTHONPATH"] = python_path

    print(f"工作目录: {current_dir}")
    print(f"Python 路径: {sys.executable}")
    print(f"PYTHONPATH: {python_path}")
    print(f"启动命令: {' '.join(cmd)}")
    print("-" * 50)

    # 启动服务
    try:
        subprocess.run(cmd, env=env, check=True)
    except KeyboardInterrupt:
        print("\n服务已停止")
    except subprocess.CalledProcessError as e:
        print(f"启动失败: {e}")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())