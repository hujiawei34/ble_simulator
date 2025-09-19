"""Common Exception Handlers"""
from flask import jsonify
from fastapi import HTTPException
import sys
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

from src.python.utils.log_util import LogUtil

logger = LogUtil.get_logger('exceptions')

def handle_404(error):
    """处理404错误"""
    logger.warning(f"404错误: {error}")
    return jsonify({
        'error': 'Not Found',
        'message': '请求的资源不存在',
        'status_code': 404
    }), 404

def handle_500(error):
    """处理500错误"""
    logger.error(f"500错误: {error}")
    return jsonify({
        'error': 'Internal Server Error',
        'message': '服务器内部错误',
        'status_code': 500
    }), 500

def setup_flask_error_handlers(app):
    """设置Flask错误处理器"""
    app.register_error_handler(404, handle_404)
    app.register_error_handler(500, handle_500)
    logger.info("Flask错误处理器设置完成")