"""Flask Routes"""
from flask import Blueprint, render_template, jsonify, request
import sys
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

from src.python.utils.log_util import LogUtil

# 创建蓝图
main_bp = Blueprint('main', __name__)
logger = LogUtil.get_logger('flask_routes')

@main_bp.route('/')
def index():
    """首页"""
    logger.info("访问首页")
    return render_template('index.html', title='BLE Simulator')

@main_bp.route('/health')
def health():
    """健康检查"""
    logger.info("健康检查请求")
    return jsonify({
        'status': 'healthy',
        'service': 'Flask BLE Simulator',
        'version': '1.0.0'
    })

@main_bp.route('/devices')
def devices():
    """设备列表页面"""
    logger.info("访问设备列表页面")
    return render_template('devices.html', title='BLE Devices')

@main_bp.route('/about')
def about():
    """关于页面"""
    logger.info("访问关于页面")
    return render_template('about.html', title='About')