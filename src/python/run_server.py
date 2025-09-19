#!/usr/bin/env python3
"""Server Startup Script"""
import sys
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

from src.python.app.main import run_server

if __name__ == "__main__":
    run_server()