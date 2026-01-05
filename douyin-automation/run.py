#!/usr/bin/env python3
"""
抖音自动化营销工具 - 启动脚本
从项目根目录运行: python run.py
"""

import sys
from pathlib import Path

# 添加 src 目录到 Python 路径
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# 运行主程序
from src.main import main

if __name__ == '__main__':
    exit(main() or 0)
