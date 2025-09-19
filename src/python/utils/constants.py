#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目常量定义
"""

from pathlib import Path
import sys

# 项目根目录 - 从当前文件向上4级
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
print(f"PROJECT_ROOT: {PROJECT_ROOT}")

sys.path.append(str(PROJECT_ROOT))
from src.python.utils.log_util import default_logger as logger

logger.info(f"PROJECT_ROOT: {PROJECT_ROOT}")