"""Common Middleware"""
import time
from flask import request, g
import sys
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

from src.python.utils.log_util import LogUtil

logger = LogUtil.get_logger('middleware')

def before_request():
    """请求前处理"""
    g.start_time = time.time()
    logger.info(f"收到请求: {request.method} {request.path}")

def after_request(response):
    """请求后处理"""
    if hasattr(g, 'start_time'):
        duration = time.time() - g.start_time
        logger.info(f"请求完成: {request.method} {request.path} - 状态码: {response.status_code} - 耗时: {duration:.3f}s")
    return response

def setup_flask_middleware(app):
    """设置Flask中间件"""
    app.before_request(before_request)
    app.after_request(after_request)
    logger.info("Flask中间件设置完成")